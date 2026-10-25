"""Engine -> dashboard: a JSON snapshot of every card and the numbers behind them.

Written to state/dashboard.json at the end of each run and committed with the database, so the dashboard
can read it straight from the private repo.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .config import Config
from .sources import PRICE_PER_POST_USD
from .store import Store

SNAPSHOT_NAME = "dashboard.json"
KEEP_DAYS = 30  # older cards drop off the board unless they're somewhere in the sales pipeline


def snapshot(cfg: Config, store: Store) -> dict[str, Any]:
    rows = store.db.execute(
        """SELECT c.*, p.lane_id, p.url, p.author_name, p.author_headline, p.author_url, p.text, p.posted_at,
                  p.likes, p.comments, p.priority, p.score_json
           FROM cards c JOIN posts p ON p.id = c.post_id
           WHERE c.status != 'regen'
             AND (c.created_at >= datetime('now', ?) OR c.stage IS NOT NULL)
           ORDER BY c.id DESC""", (f"-{KEEP_DAYS} days",)).fetchall()
    mine = {r["card_id"]: dict(r) for r in store.db.execute(
        "SELECT * FROM my_comments WHERE card_id IS NOT NULL ORDER BY created_at")}
    cards = []
    for r in rows:
        lane = cfg.lane(r["lane_id"])
        score = json.loads(r["score_json"] or "{}")
        m = mine.get(r["id"])
        cards.append({
            "id": r["id"], "created_at": r["created_at"], "acted_at": r["acted_at"],
            "status": r["status"], "stage": r["stage"], "chosen_option": r["chosen_option"], "note": r["note"],
            "lane": r["lane_id"], "lane_name": lane.name if lane else r["lane_id"],
            "intent": lane.intent if lane else "", "priority": round(r["priority"] or 0, 1),
            "author_name": r["author_name"], "author_headline": r["author_headline"], "author_url": r["author_url"],
            "post_url": r["url"], "post_text": (r["text"] or "")[:1500], "posted_at": r["posted_at"],
            "likes": r["likes"], "comments": r["comments"],
            "why": score.get("why", ""), "best_angle": score.get("best_angle", ""),
            "options": [{"angle": o.get("angle", ""), "text": o.get("text", "")}
                        for o in json.loads(r["options_json"])],
            "my_comment": ({"text": m["text"], "url": m["url"], "likes": m["likes"], "replies": m["replies"],
                            "checked_at": m["checked_at"]} if m else None),
        })

    usage = [dict(u) for u in store.db.execute("SELECT * FROM usage ORDER BY day DESC LIMIT 30")]
    scraped_month = store.db.execute(
        "SELECT COALESCE(SUM(posts_scraped),0) FROM usage WHERE day >= date('now','start of month')").fetchone()[0]
    metrics: dict[str, list[dict[str, Any]]] = {}
    for m in store.db.execute("SELECT * FROM metrics ORDER BY day"):
        metrics.setdefault(m["key"], []).append({"day": m["day"], "value": m["value"]})
    my_comments = [dict(r) for r in store.db.execute(
        "SELECT id, card_id, url, post_url, post_author, created_at, likes, replies FROM my_comments "
        "WHERE created_at >= datetime('now', '-30 days') ORDER BY created_at DESC")]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "actions_applied": int(store.get("actions_applied", "0") or 0),
        "cards": cards,
        "usage": usage,
        "apify_month_usd": round(scraped_month * PRICE_PER_POST_USD, 2),
        "apify_month_cap_usd": 5.0,
        "learned": store.db.execute("SELECT COUNT(*) FROM examples").fetchone()[0],
        "metrics": metrics,
        "my_comments": my_comments,
        "stats_last_checked": store.get("mystats_checked_at"),
        "paused": store.get("paused") == "1",
        "settings": {
            "cards_per_day": cfg.s("budgets", "max_cards_per_day", default=30),
            "stats_enabled": bool(cfg.s("my_stats", "enabled", default=False)),
            "runs": "08:00 / 13:00 / 18:00 Riyadh",
        },
    }


def write_snapshot(cfg: Config, store: Store) -> None:
    path = cfg.state_dir / SNAPSHOT_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot(cfg, store), ensure_ascii=False, indent=0), encoding="utf-8")
