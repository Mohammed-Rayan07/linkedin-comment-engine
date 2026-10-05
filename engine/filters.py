"""Cheap rule filters that run before any LLM call."""
from __future__ import annotations

import re

from .config import Config, Lane
from .models import Post

_ARABIC = re.compile(r"[؀-ۿ]")
_LATIN = re.compile(r"[A-Za-z]")
_HIRING = re.compile(r"\b(we('| a)re hiring|job opening|apply now|vacancy|#hiring)\b", re.I)


def is_mostly_non_english(text: str) -> bool:
    arabic = len(_ARABIC.findall(text))
    latin = len(_LATIN.findall(text))
    return arabic > latin


def is_vendor(headline: str, vendor_patterns: list[str]) -> bool:
    h = headline.lower()
    return any(p in h for p in vendor_patterns)


def reject_reason(post: Post, lane: Lane, cfg: Config) -> str | None:
    """Return why a post should be skipped, or None if it passes."""
    f = cfg.settings.get("filters", {})
    if len(post.text) < f.get("min_post_chars", 180):
        return "too_short"
    if post.age_hours > f.get("max_age_hours", 36):
        return "too_old"
    if post.comments > f.get("max_comments", 150):
        return "comments_saturated"
    if f.get("skip_non_english", True) and is_mostly_non_english(post.text):
        return "non_english"
    if _HIRING.search(post.text):
        return "job_post"
    if lane.intent == "buyer":
        if post.author_type == "company":
            return "company_page"
        if is_vendor(post.author_headline, cfg.vendor_patterns):
            return "vendor_author"
    return None
