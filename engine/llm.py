"""Thin Claude wrapper: structured JSON output, effort control, refusal fallback, token accounting."""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Callable

import anthropic

from .config import Config
from .store import Store

log = logging.getLogger(__name__)

FALLBACK_BETA = "server-side-fallback-2026-07-01"

# $ per million tokens: input, output, cache read, cache write (5-min)
PRICES = {
    "claude-opus-5-5": (4.0, 20.0, 0.20, 5.0),
    "claude-sonnet-5-5": (2.0, 10.0, 0.20, 2.5),
    "claude-haiku-4-5": (1.0, 5.0, 0.10, 1.25),
}


def cost_usd(model: str, usage) -> float:
    pin, pout, pread, pwrite = PRICES.get(model, PRICES["claude-opus-5-5"])
    return (
        (usage.input_tokens or 0) * pin
        + (usage.output_tokens or 0) * pout  # includes thinking tokens
        + (getattr(usage, "cache_read_input_tokens", 0) or 0) * pread
        + (getattr(usage, "cache_creation_input_tokens", 0) or 0) * pwrite
    ) / 1_000_000


class LLMRefusal(Exception):
    pass


class LLM:
    def __init__(self, cfg: Config, store: Store):
        self.cfg = cfg
        self.store = store
        if not cfg.mock and "REPLACE_ME" in os.getenv("ANTHROPIC_API_KEY", ""):
            raise RuntimeError("ANTHROPIC_API_KEY in .env is still the placeholder; paste your real key")
        self.client = None if cfg.mock else anthropic.Anthropic()
        self.use_fallbacks = bool(cfg.s("models", "server_fallbacks", default=True))

    def json(
        self,
        *,
        model: str,
        effort: str,
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

        kwargs: dict[str, Any] = dict(
            model=model,
            max_tokens=max_tokens,
            # stable system prompt first so the big expert-profile prefix gets cached across calls
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
            output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
        )
        try:
            resp = self._create(kwargs)
        except anthropic.BadRequestError as e:
            if self.use_fallbacks and "fallback" in str(e).lower():
                log.warning("server-side fallbacks rejected; retrying without them")
                self.use_fallbacks = False
                resp = self._create(kwargs)
            else:
                raise

        u = resp.usage
        self.store.add_tokens(
            (u.input_tokens or 0) + (getattr(u, "cache_read_input_tokens", 0) or 0)
            + (getattr(u, "cache_creation_input_tokens", 0) or 0),
            u.output_tokens or 0,
            cost_usd(model, u),
        )
        if resp.stop_reason == "refusal":
            raise LLMRefusal(getattr(resp.stop_details, "category", None) or "refusal")
        if resp.stop_reason == "max_tokens":
            raise RuntimeError("model output hit max_tokens; raise max_tokens")
        text = next((b.text for b in resp.content if b.type == "text"), "")
        return json.loads(text)

    def _create(self, kwargs: dict[str, Any]):
        assert self.client is not None
        if self.use_fallbacks:
            return self.client.beta.messages.create(betas=[FALLBACK_BETA], fallbacks="default", **kwargs)
        return self.client.messages.create(**kwargs)
