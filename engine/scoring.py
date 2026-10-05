"""Score posts in batches: is the author a buyer, and can Rayan add something real here?"""
from __future__ import annotations

import json
from typing import Any

from .config import Config, Lane
from .llm import LLM
from .models import Post

BATCH = 10
ANGLES = ["missing_step", "field_detail", "pushback", "make_concrete", "sharp_question"]

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "ref": {"type": "string"},
                    "author_type": {"type": "string", "enum": ["buyer", "peer_vendor", "creator", "other"]},
                    "icp_fit": {"type": "integer"},
                    "value_room": {"type": "integer"},
                    "sensitive": {"type": "boolean"},
                    "why": {"type": "string"},
                    "best_angle": {"type": "string", "enum": ANGLES},
                    "proof_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["ref", "author_type", "icp_fit", "value_room", "sensitive", "why",
                             "best_angle", "proof_ids"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


def _system(cfg: Config) -> str:
    p = cfg.profile
    proofs = "\n".join(f"- {x['id']} ({x['type']}): {x['summary']}" for x in p.get("proofs", []))
    opinions = "\n".join(f"- {o}" for o in p.get("opinions", []))
    return f"""You triage LinkedIn posts for {p['who']['name']}, founder of {p['who']['business']} ({p['who']['base']}).
{p['who']['one_liner']}

He wants to comment on posts where (a) the audience includes his buyers and (b) he can add something
specific from his real experience. His first clients will be SMB owners who feel the pain of missed
calls/WhatsApp, slow lead follow-up and ops chaos, have budget, and buy from a credible specialist:
clinic and med-spa owners, real-estate brokerages, marketing-agency owners, ops leaders in the GCC.

His proof bank (the only experience he can draw on):
{proofs}

His opinions:
{opinions}

For each post return:
- author_type: buyer (owns/runs an SMB or decides on ops/sales tooling), peer_vendor (sells AI,
  automation, marketing or lead-gen services), creator (content creator / influencer with a business
  audience), other.
- icp_fit 0-10: how likely the post's author AND its readers are his buyers. A vendor talking to vendors is 0-2.
- value_room 0-10: how much room there is for a specific, expert comment grounded in the proof bank
  or opinions above. Generic motivation, announcements, celebrations and pure self-promotion score low.
- sensitive: true for layoffs, grief, health struggles, politics, religion, tragedies, legal disputes.
  He should not comment there.
- why: max 20 words, plain English, the reason this post is or isn't worth his time.
- best_angle: missing_step | field_detail | pushback | make_concrete | sharp_question
- proof_ids: 0-2 ids from the proof bank that genuinely fit (empty if none).
Be strict. Most posts should score below 6 on at least one axis."""


def _user(posts: list[tuple[str, Post, Lane]]) -> str:
    blocks = []
    for ref, p, lane in posts:
        blocks.append(json.dumps({
            "ref": ref,
            "lane": lane.name,
            "author": p.author_name,
            "author_headline": p.author_headline,
            "hours_old": round(p.age_hours, 1),
            "reactions": p.likes,
            "comments": p.comments,
            "text": p.text[:2500],
        }, ensure_ascii=False))
    return "Score these posts:\n" + "\n".join(blocks)


def _mock(posts: list[tuple[str, Post, Lane]]) -> dict[str, Any]:
    out = []
    for ref, p, lane in posts:
        h = p.author_headline.lower()
        hit = any(k.lower() in h for k in lane.buyer_headline_hints)
        out.append({
            "ref": ref,
            "author_type": "buyer" if hit else ("creator" if lane.intent == "audience" else "other"),
            "icp_fit": 8 if hit or lane.intent != "buyer" else 3,
            "value_room": 7,
            "sensitive": False,
            "why": "Mock score: headline matches lane buyer hints." if hit else "Mock score.",
            "best_angle": "field_detail",
            "proof_ids": ["lead_waste_math"],
        })
    return {"results": out}


def priority(p: Post, lane: Lane, score: dict[str, Any]) -> float:
    if score["sensitive"]:
        return 0.0
    if lane.intent == "buyer" and score["author_type"] == "peer_vendor":
        return 0.0
    icp = max(0, min(10, score["icp_fit"]))
    room = max(0, min(10, score["value_room"]))
    base = 0.5 * icp + 0.5 * room
    fresh = max(0.0, 1.5 - p.age_hours / 8)          # first hours matter most
    vel = min(1.0, p.velocity / 20)
    crowded = 1.0 if p.comments > 60 else 0.0
    return round(min(10.0, (base + fresh + vel - crowded) * lane.weight), 2)


def score_posts(cfg: Config, llm: LLM, items: list[tuple[Post, Lane]]) -> list[tuple[Post, Lane, dict, float]]:
    scored = []
    for i in range(0, len(items), BATCH):
        chunk = [(f"p{j}", p, lane) for j, (p, lane) in enumerate(items[i:i + BATCH])]
        result = llm.json(
            model=cfg.s("models", "scoring"),
            effort=cfg.s("models", "scoring_effort", default="low"),
            system=_system(cfg),
            user=_user(chunk),
            schema=SCHEMA,
            max_tokens=8000,
            mock=lambda c=chunk: _mock(c),
        )
        by_ref = {r["ref"]: r for r in result.get("results", [])}
        for ref, p, lane in chunk:
            s = by_ref.get(ref)
            if s:
                scored.append((p, lane, s, priority(p, lane, s)))
    return scored
