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
    },
    "required": ["can_add_value", "skip_reason", "options"],
    "additionalProperties": False,
}


@dataclass
class Draft:
    options: list[dict[str, Any]]
    skip_reason: str | None = None


def _learned(examples) -> str:
    # Only his own wording teaches his voice. Drafts he posted unchanged are the model's writing, and
    # feeding those back made every comment converge on the same template.
    examples = [ex for ex in examples if ex["source"] == "edited"]
    if not examples:
        return ""
    parts = ["\n# Comments in Rayan's own words (strongest signal for his voice; match how he writes)"]
    for ex in examples:
        parts.append(f"Post: {ex['post_excerpt'][:240]}\nhe wrote: {ex['comment']}")
    return "\n\n".join(parts)


def _system(cfg: Config, examples=()) -> str:
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
  Skipping is the right call often, especially outside his lane. Never write a comment just to have one.

# Expert profile
{profile_yaml}

# Voice guide
{cfg.voice}

# Output
Write {n} options that a reader could tell apart at a glance, each using a DIFFERENT angle
(missing_step, field_detail, pushback, make_concrete, sharp_question):
- Option 1 is short: one or two sentences, under 180 characters. A specific reaction with a reason, or one answerable question.
- Option 2 is the one place his own work may appear, told as a quick story, and only if a proof genuinely fits. Otherwise a concrete test or example.
- Option 3 takes a different stance: a respectful disagreement, or a question about their specific situation.
Each option: {cfg.s('comment', 'min_chars', default=40)}-{cfg.s('comment', 'max_chars', default=450)} characters, ready to paste, English only.
Every option's first sentence must respond to something specific in THIS post. If you could paste it under
a different post on the same topic, rewrite it.
proof_ids lists the profile proofs each option draws on (empty if it uses only opinions or the post).""" + _learned(examples)


def _recently_used(store) -> tuple[list[str], list[str]]:
    """Proofs and opening lines from the last 24h of cards, so twenty comments don't all sound alike."""
    proofs: dict[str, int] = {}
    openers: list[str] = []
    for row in store.db.execute("SELECT options_json FROM cards WHERE created_at >= datetime('now','-1 day')"):
        for o in json.loads(row["options_json"]):
            for pid in o.get("proof_ids", []):
                proofs[pid] = proofs.get(pid, 0) + 1
            openers.append(o["text"].split(".")[0][:90])
    overused = [pid for pid, n in sorted(proofs.items(), key=lambda kv: -kv[1]) if n >= 2]
    return overused, openers[-15:]


def _user(p: Post, lane: Lane, score: dict[str, Any], feedback: str | None, store=None) -> str:
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
        "post_text": p.text[:4000],
    }
    msg = "Draft comments for this post:\n" + json.dumps(payload, ensure_ascii=False, indent=1)
    if store is not None:
        overused, openers = _recently_used(store)
        if overused or openers:
            msg += ("\n\nRayan has already used these proofs in recent comments; prefer different ones or the "
                    f"post's own details: {overused}\nDon't start with or echo these recent opening lines: {openers}")
    if feedback:
        msg += ("\n\nYour previous drafts broke these rules. Rewrite all options so none of these "
                "problems remain, without inventing anything new:\n" + feedback)
    return msg


def _mock(p: Post, lane: Lane, score: dict[str, Any]) -> dict[str, Any]:
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
    }


def _violations(d: dict[str, Any], cfg: Config, p: Post) -> dict[int, list[str]]:
    lo, hi = cfg.s("comment", "min_chars", default=140), cfg.s("comment", "max_chars", default=650)
    return {i: guard.check(o["text"], cfg.profile, p.text, lo, hi) for i, o in enumerate(d.get("options", []))}


def draft_comments(cfg: Config, llm: LLM, p: Post, lane: Lane, score: dict[str, Any]) -> Draft:
    call = dict(
        task="drafting",
        system=_system(cfg, llm.store.recent_examples(10)),
        schema=SCHEMA,
        max_tokens=16000,
        mock=lambda: _mock(p, lane, score),
    )
    result = llm.json(user=_user(p, lane, score, None, llm.store), **call)
    if not result.get("can_add_value"):
        return Draft([], result.get("skip_reason") or "nothing specific to add")

    bad = {i: v for i, v in _violations(result, cfg, p).items() if v}
    if bad:
        feedback = "\n".join(f"- option {i + 1}: " + "; ".join(v) for i, v in bad.items())
        log.info("post %s: regenerating, violations:\n%s", p.id, feedback)
        result = llm.json(user=_user(p, lane, score, feedback, llm.store), **call)
        if not result.get("can_add_value"):
            return Draft([], result.get("skip_reason") or "nothing specific to add")

    clean = [o for i, o in enumerate(result.get("options", []))
             if not guard.check(o["text"], cfg.profile, p.text,
                                cfg.s("comment", "min_chars", default=140),
                                cfg.s("comment", "max_chars", default=650))]
    if not clean:
        return Draft([], "every draft failed the truth/voice checks")
    return Draft(clean)
