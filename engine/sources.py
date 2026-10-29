"""Post sources: Apify (live, never touches your LinkedIn account) and fixtures (mock)."""
from __future__ import annotations

import json
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from .config import ROOT, Config, Lane
from .models import Post, post_from_apify
from .store import Store

log = logging.getLogger(__name__)

APIFY_BASE = "https://api.apify.com/v2"
SEARCH_ACTOR = "harvestapi~linkedin-post-search"
PROFILE_ACTOR = "harvestapi~linkedin-profile-posts"
PRICE_PER_POST_USD = 0.002  # free-plan rate; also charged ~$0.001 per zero-result query
WATERMARK_OVERLAP = timedelta(minutes=15)
POSTED_LIMIT_HOURS = {"1h": 1, "24h": 24, "week": 168, "month": 720}


class BudgetExhausted(Exception):
    pass


class ApifyUnavailable(Exception):
    """Apify refused the whole account (bad token, no plan, or monthly usage limit hit).

    Every lane would fail the same way, so the run stops scraping instead of trying each one."""


# 401 bad token, 402 payment required, 403 usage limit / permission. None of these are per-lane problems.
_ACCOUNT_LEVEL_STATUSES = {401, 402, 403}


def _watermark_key(lane: Lane, item: str | None = None) -> str:
    if item is None:
        return f"watermark:{lane.id}"
    token = hashlib.sha1(item.encode("utf-8")).hexdigest()[:12]
    return f"watermark:{lane.id}:{token}"


def _since(lane: Lane, store: Store, items: list[str] | None = None) -> datetime:
    """Use the oldest selected item watermark so none of a lane's queries are skipped."""
    window = timedelta(hours=POSTED_LIMIT_HOURS.get(lane.posted_limit, 24))
    floor = datetime.now(timezone.utc) - window
    marks = [store.get(_watermark_key(lane, item)) for item in (items or [])]
    if marks and all(marks):
        oldest = min(datetime.fromisoformat(mark) for mark in marks if mark)
        return max(floor, oldest - WATERMARK_OVERLAP)
    return floor


def _rotate(store: Store, lane: Lane, items: list[str], n: int) -> list[str]:
    """Rotate smaller manual budgets while each selected item keeps its own watermark."""
    if n >= len(items):
        return list(items)
    key = f"rotation:{lane.id}"
    start = int(store.get(key, "0") or 0) % len(items)
    picked = [items[(start + i) % len(items)] for i in range(n)]
    store.put(key, str((start + n) % len(items)))
    return picked


def _apify_error(resp: httpx.Response) -> str:
    """Apify's own explanation (e.g. monthly usage limit) when the body has one."""
    try:
        err = resp.json().get("error") or {}
        return str(err.get("message") or err.get("type") or resp.text)[:200]
    except Exception:
        return resp.text[:200]


def _run_actor(cfg: Config, actor: str, payload: dict[str, Any], max_items: int) -> list[dict[str, Any]]:
    max_charge = round(max_items * PRICE_PER_POST_USD + 0.02, 3)
    params = {"maxItems": max_items, "maxTotalChargeUsd": max_charge, "timeout": 280}
    headers = {"Authorization": f"Bearer {cfg.apify_token}"}
    url = f"{APIFY_BASE}/acts/{actor}/run-sync-get-dataset-items"
    resp = httpx.post(url, params=params, headers=headers, json=payload, timeout=300)
    if resp.status_code in _ACCOUNT_LEVEL_STATUSES:
        raise ApifyUnavailable(f"Apify returned {resp.status_code}: {_apify_error(resp)}")
    resp.raise_for_status()
    items = resp.json()
    return items if isinstance(items, list) else []


def remaining_today(cfg: Config, store: Store) -> int:
    return int(cfg.s("budgets", "max_posts_scraped_per_day", default=750)) - store.today()["posts_scraped"]


def fetch_lane(cfg: Config, store: Store, lane: Lane, budget: int | None = None, probe: bool = False,
               since_override: datetime | None = None) -> list[Post]:
    """Fetch new posts for a lane, spending at most `budget` posts of Apify credit.

    probe=True (yield-test) looks back a week with the lane's own limits and leaves the daily budget
    and the lane watermark untouched, so it never starves the real runs."""
    if not probe:
        left = remaining_today(cfg, store)
        if left <= 0:
            raise BudgetExhausted(f"daily scrape budget used ({cfg.s('budgets', 'max_posts_scraped_per_day')} posts)")
        budget = min(left, budget if budget is not None else left)
    if cfg.mock:
        posts = _mock_fetch(lane)
    else:
        if not cfg.apify_token:
            raise RuntimeError("APIFY_TOKEN missing (set it in .env, or run with --mock)")
        if probe:
            since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        else:
            since = (since_override or _since(lane, store)).isoformat()
        if lane.kind == "search":
            if not lane.queries:
                return []
            if probe:
                queries, per_query = lane.queries, lane.max_posts_per_query
            else:
                queries = _rotate(store, lane, lane.queries, max(1, min(len(lane.queries), budget)))
                since = (since_override or _since(lane, store, queries)).isoformat()
                per_query = max(1, min(lane.max_posts_per_query,
                                       (budget + len(queries) - 1) // len(queries)))
            payload: dict[str, Any] = {
                "searchQueries": queries,
                "maxPosts": per_query,
                "postedLimitDate": since,
                "sortBy": lane.sort_by,  # the watermark already limits results to fresh posts
            }
            if lane.author_keywords:
                payload["authorKeywords"] = lane.author_keywords
            cap = per_query * len(queries) if probe else min(budget, per_query * len(queries))
            items = _run_actor(cfg, SEARCH_ACTOR, payload, cap)
        else:
            if not lane.profiles:
                return []
            per_profile = lane.max_posts_per_profile
            profiles = lane.profiles if probe else _rotate(
                store, lane, lane.profiles, max(1, min(len(lane.profiles), budget // max(per_profile, 1))))
            if not probe:
                since = (since_override or _since(lane, store, profiles)).isoformat()
            payload = {
                "targetUrls": profiles,          # one run for the whole watchlist
                "maxPosts": per_profile,
                "postedLimitDate": since,
                "includeReposts": False,
            }
            cap = per_profile * len(profiles) if probe else min(budget, per_profile * len(profiles))
            items = _run_actor(cfg, PROFILE_ACTOR, payload, cap)
        posts = [p for p in (post_from_apify(i, lane.id) for i in items) if p]
        if not probe:
            store.add_scraped(len(items))
            checked = queries if lane.kind == "search" else profiles
            checked_at = datetime.now(timezone.utc).isoformat()
            for item in checked:
                store.put(_watermark_key(lane, item), checked_at)
    log.info("lane %s: %d posts", lane.id, len(posts))
    return posts


def _mock_fetch(lane: Lane) -> list[Post]:
    data = json.loads((ROOT / "fixtures" / "sample_posts.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    posts = []
    for item in data:
        if item.get("_lane") != lane.id:
            continue
        item = dict(item)
        # fixtures store age in hours so they always look fresh
        item["postedAt"] = {"timestamp": int((now - timedelta(hours=item.pop("_age_hours", 2))).timestamp() * 1000)}
        p = post_from_apify(item, lane.id)
        if p:
            posts.append(p)
    return posts
