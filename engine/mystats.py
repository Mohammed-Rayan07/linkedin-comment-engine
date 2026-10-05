"""Your own LinkedIn numbers, read from your PUBLIC activity via Apify (no login, never your cookie).

What this can see: the comments you posted (likes + replies on each), and your follower count.
What it can't: impressions, profile views, search appearances. LinkedIn only shows those to you when
you're logged in, so the dashboard has a small form where you type them in once a week.

Bonus: when one of your comments lands on a card's post, the card is marked posted automatically and
your exact final wording becomes a learning example, even if you never tapped anything.

Costs Apify credit (~$0.002 per comment read), counted against the same daily cap as post scraping, so
the monthly total never goes over budget. Off unless my_stats.enabled is true in settings.yaml.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from .sources import _run_actor, remaining_today

if TYPE_CHECKING:
    from .pipeline import Engine

log = logging.getLogger(__name__)

COMMENTS_ACTOR = "harvestapi~linkedin-profile-comments"
PROFILE_ACTOR = "harvestapi~linkedin-profile-scraper"
LONG_ID = re.compile(r"\d{16,20}")


def due(engine: "Engine") -> bool:
    cfg, store = engine.cfg, engine.store
    if not cfg.s("my_stats", "enabled", default=False) or cfg.mock or not cfg.apify_token:
        return False
    last = store.get("mystats_checked_at")
    if not last:
        return True
    every = float(cfg.s("my_stats", "every_days", default=2))
    return datetime.now(timezone.utc) - datetime.fromisoformat(last) >= timedelta(days=every) - timedelta(hours=2)


def _post_ids(item: dict[str, Any]) -> set[str]:
    post = item.get("post") or {}
    ids = {str(item.get("postId") or ""), str(post.get("id") or ""), str(post.get("entityId") or "")}
    for f in (post.get("linkedinUrl"), post.get("shareUrn"), post.get("shareLinkedinUrl"), item.get("linkedinUrl")):
        ids |= set(LONG_ID.findall(str(f or "")))
    return {i for i in ids if i}


def match_card(store, item: dict[str, Any]):
    """Find the card whose post this comment is on. Activity ids and ugcPost ids differ for the same post,
    so match on any id in either URL, then fall back to author + opening words."""
    ids = _post_ids(item)
    rows = store.db.execute(
        "SELECT c.id, c.post_id, p.url, p.author_url, p.text FROM cards c JOIN posts p ON p.id=c.post_id "
        "WHERE c.status != 'regen' AND c.created_at >= datetime('now','-30 days')").fetchall()
    for r in rows:
        if r["post_id"] in ids or ids & set(LONG_ID.findall(r["url"] or "")):
            return store.get_card(r["id"])
    post = item.get("post") or {}
    handle = ((post.get("author") or {}).get("publicIdentifier") or "").lower()
    opening = " ".join((post.get("content") or "").split())[:60].lower()
    if handle and opening:
        for r in rows:
            if handle in (r["author_url"] or "").lower() and " ".join((r["text"] or "").split())[:60].lower() == opening:
                return store.get_card(r["id"])
    return None


def check(engine: "Engine", force: bool = False) -> str:
    cfg, store = engine.cfg, engine.store
    if not force and not due(engine):
        return ""
    profile = cfg.s("my_stats", "profile_url")
    max_comments = int(cfg.s("my_stats", "max_comments", default=30))
    if not profile:
        return "my_stats.profile_url is not set"
    if remaining_today(cfg, store) < max_comments + 2:
        return "skipped your stats check: today's Apify cap is used up (tries again next run)"

    items = _run_actor(cfg, COMMENTS_ACTOR, {"profiles": [profile], "maxItems": max_comments,
                                             "postedLimit": "month"}, max_comments)
    store.add_scraped(len(items))
    now = datetime.now(timezone.utc).isoformat()
    matched = auto_posted = 0
    for it in items:
        if not it.get("id"):
            continue
        card = match_card(store, it)
        eng = it.get("engagement") or {}
        post = it.get("post") or {}
        text = (it.get("commentary") or "").strip()
        store.upsert_my_comment({
            "id": str(it["id"]), "post_id": str(it.get("postId") or post.get("id") or ""),
            "card_id": card["id"] if card else None, "url": it.get("linkedinUrl"),
            "post_url": post.get("linkedinUrl"), "post_author": (post.get("author") or {}).get("name"),
            "text": text, "created_at": it.get("createdAt"), "likes": int(eng.get("likes") or 0),
            "replies": int(eng.get("comments") or 0), "checked_at": now})
        if not card:
            continue
        matched += 1
        if card["status"] in ("sent", "skipped"):
            store.resolve_card(card["id"], "posted", 0)
            engine.tg.mark(card["tg_message_id"], "✅ Seen on LinkedIn")
            auto_posted += 1
        if len(text) >= 20:
            engine._learn(store.get_card(card["id"]), text, "edited")  # what you actually posted

    followers = None
    try:
        prof = _run_actor(cfg, PROFILE_ACTOR, {"profileScraperMode": "Profile details no email ($4 per 1k)",
                                               "queries": [profile]}, 1)
        store.add_scraped(2)  # $0.004 = two posts' worth of credit
        if prof:
            p = prof[0]
            followers = p.get("followerCount") or p.get("followersCount") or p.get("followers")
            if followers is not None:
                store.put_metric(date.today().isoformat(), "followers", float(followers))
            conns = p.get("connectionsCount") or p.get("connections")
            if conns is not None:
                store.put_metric(date.today().isoformat(), "connections", float(conns))
    except Exception as e:  # followers are a nice-to-have
        log.warning("follower check failed: %s", e)

    store.put("mystats_checked_at", now)
    return (f"your stats: {len(items)} comments read, {matched} on engine cards "
            f"({auto_posted} auto-marked posted), followers={followers}")
