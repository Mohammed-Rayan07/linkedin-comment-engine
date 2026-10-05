"""Draft comment options for one post, then run them through the truth gate."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import yaml

from . import guard
from .config import Config, Lane
from .llm import LLM
from .models import Post
from .scoring import ANGLES

log = logging.getLogger(__name__)

NOTE_MAX = 280  # LinkedIn connection notes cap at 300 chars

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "can_add_value": {"type": "boolean"},
        "skip_reason": {"type": "string"},
        "options": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "angle": {"type": "string", "enum": ANGLES},
                    "text": {"type": "string"},
                    "proof_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["angle", "text", "proof_ids"],
                "additionalProperties": False,
            },
        },
        "connection_note": {"type": "string"},
    },
    "required": ["can_add_value", "skip_reason", "options", "connection_note"],
    "additionalProperties": False,
}


@dataclass
class Draft:
    options: list[dict[str, Any]]
    connection_note: str | None
    skip_reason: str | None = None


def _system(cfg: Config) -> str:
    profile_yaml = yaml.safe_dump(cfg.profile, sort_keys=False, allow_unicode=True, width=120)
    n = cfg.s("comment", "options_per_post", default=3)
    return f"""You ghost-draft LinkedIn comments for Rayan. He reads every draft, edits it, and posts it himself.
His reputation is on the line with every word, so accuracy beats cleverness.

# Truth rules (non-negotiable)
- Use ONLY facts from the expert profile below, or facts stated in the post itself. Nothing else exists.
- Every number you write must appear in the profile or the post. If you need a number you don't have, write without one.
- Respect each proof's `type` and `how_to_phrase`. Audit findings are things he observed, never results he delivered.
  Builds are demos/prototypes/own tooling, never "for a client". There are no verified client results.
- Never break anything in `never_claim`.
- If he has nothing specific to add, set can_add_value=false and explain in skip_reason. A skipped post costs nothing; a hollow comment costs credibility.

# Expert profile
{profile_yaml}

# Voice guide
{cfg.voice}

# Output
Write {n} options, each using a DIFFERENT angle (missing_step, field_detail, pushback, make_concrete, sharp_question).
Each option: {cfg.s('comment', 'min_chars', default=140)}-{cfg.s('comment', 'max_chars', default=650)} characters, ready to paste, English only.
proof_ids lists the profile proofs each option draws on (empty if it uses only opinions or the post).
connection_note: only when asked for one in the request, otherwise "". When asked: a connection request note under {NOTE_MAX} characters
that references this specific post, makes no pitch, and gives the person a reason to accept."""


def _user(p: Post, lane: Lane, score: dict[str, Any], feedback: str | None) -> str:
    want_note = lane.intent in ("buyer", "prospect") and score.get("author_type") == "buyer"
    payload = {
        "lane": lane.name,
        "lane_intent": lane.intent,
        "author": p.author_name,
        "author_headline": p.author_headline,
        "hours_old": round(p.age_hours, 1),
        "reactions": p.likes,
        "comments": p.comments,
        "triage_note": score.get("why"),
        "suggested_angle": score.get("best_angle"),
        "suggested_proofs": score.get("proof_ids"),
        "write_connection_note": want_note,
        "post_text": p.text[:4000],
    }
    msg = "Draft comments for this post:\n" + json.dumps(payload, ensure_ascii=False, indent=1)
    if feedback:
        msg += ("\n\nYour previous drafts broke these rules. Rewrite all options so none of these "
                "problems remain, without inventing anything new:\n" + feedback)
    return msg


def _mock(p: Post, lane: Lane, score: dict[str, Any]) -> dict[str, Any]:
    note = (f"Hi {p.first_name}, your post on missed enquiries matched what I keep seeing when I map "
            "how calls and WhatsApp actually flow. Would be good to stay connected.")
    return {
        "can_add_value": True,
        "skip_reason": "",
        "options": [
            {"angle": "make_concrete", "proof_ids": ["lead_waste_math"],
             "text": ("Easy way to put a number on this: missed calls per day x booking rate if answered x "
                      "average value x 30. Most owners only track ad spend, so the leak never shows up in a report. "
                      "You only see the patients you captured, not the ones who called the next clinic.")},
            {"angle": "field_detail", "proof_ids": ["dentist_story"],
             "text": ("I lived the other side of this. At 11 PM with tooth pain I called 5 clinics. Three didn't answer, "
                      "one read me its opening hours, one was an Arabic-only voicemail. The 6th answered and got me as a patient. "
                      "Nobody at the first five ever knew I called.")},
            {"angle": "sharp_question", "proof_ids": ["seven_pm_test"],
             "text": ("Have you tried calling your own front desk at 7 PM, or on a Friday? Whatever happens on that call "
                      "is what every new lead gets. Curious what you'd find, because that's usually where the gap is, "
                      "not in the ads.")},
        ],
        "connection_note": note if lane.intent in ("buyer", "prospect") else "",
    }


def _violations(d: dict[str, Any], cfg: Config, p: Post) -> dict[int, list[str]]:
    lo, hi = cfg.s("comment", "min_chars", default=140), cfg.s("comment", "max_chars", default=650)
    return {i: guard.check(o["text"], cfg.profile, p.text, lo, hi) for i, o in enumerate(d.get("options", []))}


def draft_comments(cfg: Config, llm: LLM, p: Post, lane: Lane, score: dict[str, Any]) -> Draft:
    call = dict(
        model=cfg.s("models", "drafting"),
        effort=cfg.s("models", "drafting_effort", default="high"),
        system=_system(cfg),
        schema=SCHEMA,
        max_tokens=16000,
        mock=lambda: _mock(p, lane, score),
    )
    result = llm.json(user=_user(p, lane, score, None), **call)
    if not result.get("can_add_value"):
        return Draft([], None, result.get("skip_reason") or "nothing specific to add")

    bad = {i: v for i, v in _violations(result, cfg, p).items() if v}
    if bad:
        feedback = "\n".join(f"- option {i + 1}: " + "; ".join(v) for i, v in bad.items())
        log.info("post %s: regenerating, violations:\n%s", p.id, feedback)
        result = llm.json(user=_user(p, lane, score, feedback), **call)
        if not result.get("can_add_value"):
            return Draft([], None, result.get("skip_reason") or "nothing specific to add")

    clean = [o for i, o in enumerate(result.get("options", []))
             if not guard.check(o["text"], cfg.profile, p.text,
                                cfg.s("comment", "min_chars", default=140),
                                cfg.s("comment", "max_chars", default=650))]
    note = (result.get("connection_note") or "").strip() or None
    if note and guard.check(note, cfg.profile, p.text, 0, NOTE_MAX):
        note = None
    if not clean:
        return Draft([], None, "every draft failed the truth/voice checks")
    return Draft(clean, note)
