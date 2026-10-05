"""LLM wrapper with two backends: Gemini (free tier, default) and Claude.

Both return validated JSON for a given schema. Callers pass a task ("scoring" or "drafting") and the
model/effort for that task comes from config/settings.yaml.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Callable

from .config import Config
from .store import Store

log = logging.getLogger(__name__)

CLAUDE_FALLBACK_BETA = "server-side-fallback-2026-07-01"

# Claude $ per million tokens: input, output, cache read, cache write (5-min). Gemini free tier = $0.
CLAUDE_PRICES = {
    "claude-opus-5-5": (4.0, 20.0, 0.20, 5.0),
    "claude-sonnet-5-5": (2.0, 10.0, 0.20, 2.5),
    "claude-haiku-4-5": (1.0, 5.0, 0.10, 1.25),
}


class LLMRefusal(Exception):
    pass


class LLMUnavailable(Exception):
    """Every configured model is overloaded or out of quota. The run stops; unscored posts carry over."""


def _placeholder(var: str) -> bool:
    value = os.getenv(var, "")
    return not value.strip() or "REPLACE_ME" in value


class LLM:
    def __init__(self, cfg: Config, store: Store):
        self.cfg = cfg
        self.store = store
        self.provider = cfg.s("models", "provider", default="gemini")
        self._last_call = 0.0
        self._exhausted: set[str] = set()  # gemini models whose daily free quota ran out this run
        self.client: Any = None
        if cfg.mock:
            return
        if self.provider == "gemini":
            if _placeholder("GEMINI_API_KEY"):
                raise RuntimeError("GEMINI_API_KEY is missing in .env (get one free at aistudio.google.com)")
            from google import genai
            from google.genai import types
            # fail fast (no SDK-internal retry loops) so our own fallback chain kicks in
            self.client = genai.Client(
                api_key=os.environ["GEMINI_API_KEY"],
                http_options=types.HttpOptions(timeout=180_000, retry_options=types.HttpRetryOptions(attempts=1)),
            )
        elif self.provider == "claude":
            if _placeholder("ANTHROPIC_API_KEY"):
                raise RuntimeError("ANTHROPIC_API_KEY is missing in .env")
            import anthropic
            self.client = anthropic.Anthropic()
            self.use_fallbacks = bool(cfg.s("models", "claude", "server_fallbacks", default=True))
        else:
            raise RuntimeError(f"unknown models.provider '{self.provider}' (use gemini or claude)")

    def json(
        self,
        *,
        task: str,
        system: str,
        user: str,
        schema: dict[str, Any],
        max_tokens: int = 16000,
        mock: Callable[[], dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if self.cfg.mock:
            if mock is None:
                raise RuntimeError("mock mode needs a mock response")
            return mock()
        if self.provider == "gemini":
            return self._gemini(task, system, user, schema, max_tokens)
        return self._claude(task, system, user, schema, max_tokens)

    # ---- Gemini ---------------------------------------------------------------
    def _gemini(self, task: str, system: str, user: str, schema: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        from google.genai import errors, types

        g = self.cfg.s("models", "gemini", default={}) or {}
        fallbacks = g.get("fallbacks") or [g.get("fallback", "gemini-3.7-flash")]
        candidates = [g.get(task, "gemini-3.8-flash"), *fallbacks]
        level = str(g.get(f"{task}_thinking", "high")).upper()
        gap = float(g.get("min_seconds_between_calls", 7))

        for model in [m for m in candidates if m and m not in self._exhausted]:
            config = types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                response_json_schema=schema,
                max_output_tokens=max_tokens,
                thinking_config=types.ThinkingConfig(thinking_level=level),
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            )
            for attempt in range(3):
                wait = self._last_call + gap - time.monotonic()
                if wait > 0:
                    time.sleep(wait)  # free tier has a per-minute cap; pace ourselves
                self._last_call = time.monotonic()
                try:
                    resp = self.client.models.generate_content(model=model, contents=user, config=config)
                except errors.ClientError as e:
                    if e.code == 429:
                        msg = str(e)
                        if "PerDay" in msg or "per day" in msg.lower():
                            log.warning("%s: free daily quota used up, switching model", model)
                            self._exhausted.add(model)
                            break
                        delay = _retry_delay(msg, default=30 * (attempt + 1))
                        log.info("%s rate-limited, retrying in %ss", model, delay)
                        time.sleep(delay)
                        continue
                    if e.code == 404:
                        log.warning("model %s not available, trying fallback", model)
                        break
                    raise
                except errors.ServerError as e:
                    log.info("%s server error (%s), retrying", model, e.code)
                    time.sleep(5 * 2 ** attempt)
                    continue
                except Exception as e:  # timeouts / connection drops
                    log.info("%s request failed (%s), retrying", model, type(e).__name__)
                    time.sleep(5 * 2 ** attempt)
                    continue

                um = resp.usage_metadata
                if um:
                    self.store.add_tokens(um.prompt_token_count or 0,
                                          (um.candidates_token_count or 0) + (um.thoughts_token_count or 0), 0.0)
                cand = (resp.candidates or [None])[0]
                reason = str(getattr(cand, "finish_reason", "") or "")
                if "SAFETY" in reason or "PROHIBITED" in reason or "BLOCKLIST" in reason:
                    raise LLMRefusal(reason)
                if "MAX_TOKENS" in reason:
                    raise RuntimeError("Gemini output hit max_output_tokens; raise max_tokens")
                text = resp.text or ""
                return json.loads(text)
        raise LLMUnavailable("all Gemini models are overloaded or out of free quota right now")

    # ---- Claude ---------------------------------------------------------------
    def _claude(self, task: str, system: str, user: str, schema: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        import anthropic

        c = self.cfg.s("models", "claude", default={}) or {}
        model = c.get(task, "claude-opus-5-5")
        kwargs: dict[str, Any] = dict(
            model=model,
            max_tokens=max_tokens,
            # stable system prompt first so the big expert-profile prefix gets cached across calls
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
            output_config={"effort": c.get(f"{task}_effort", "high"),
                           "format": {"type": "json_schema", "schema": schema}},
        )
        try:
            resp = self._claude_create(kwargs)
        except anthropic.BadRequestError as e:
            if self.use_fallbacks and "fallback" in str(e).lower():
                log.warning("server-side fallbacks rejected; retrying without them")
                self.use_fallbacks = False
                resp = self._claude_create(kwargs)
            else:
                raise
        u = resp.usage
        pin, pout, pread, pwrite = CLAUDE_PRICES.get(model, CLAUDE_PRICES["claude-opus-5-5"])
        cread = getattr(u, "cache_read_input_tokens", 0) or 0
        cwrite = getattr(u, "cache_creation_input_tokens", 0) or 0
        cost = ((u.input_tokens or 0) * pin + (u.output_tokens or 0) * pout + cread * pread + cwrite * pwrite) / 1e6
        self.store.add_tokens((u.input_tokens or 0) + cread + cwrite, u.output_tokens or 0, cost)
        if resp.stop_reason == "refusal":
            raise LLMRefusal(getattr(resp.stop_details, "category", None) or "refusal")
        if resp.stop_reason == "max_tokens":
            raise RuntimeError("model output hit max_tokens; raise max_tokens")
        return json.loads(next((b.text for b in resp.content if b.type == "text"), ""))

    def _claude_create(self, kwargs: dict[str, Any]):
        if self.use_fallbacks:
            return self.client.beta.messages.create(betas=[CLAUDE_FALLBACK_BETA], fallbacks="default", **kwargs)
        return self.client.messages.create(**kwargs)


def _retry_delay(message: str, default: int) -> int:
    m = re.search(r"retry in ([\d.]+)s|retryDelay['\": ]+(\d+)s", message, re.I)
    if m:
        return int(float(m.group(1) or m.group(2))) + 2
    return default
