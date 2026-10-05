"""Core data shapes."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Post:
    id: str
    url: str
    text: str
    author_name: str
    author_headline: str
    author_url: str
    author_type: str  # "profile" | "company"
    posted_at: datetime
    likes: int
    comments: int
    shares: int
    lane_id: str
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def age_hours(self) -> float:
        return max((datetime.now(timezone.utc) - self.posted_at).total_seconds() / 3600, 0.0)

    @property
    def velocity(self) -> float:
        """Reactions + weighted comments per hour since posting."""
        return (self.likes + 2 * self.comments) / max(self.age_hours, 0.5)

    @property
    def first_name(self) -> str:
        parts = [w for w in (self.author_name or "").split() if w.rstrip(".").lower() not in _TITLES]
        return parts[0] if parts else ""


_TITLES = {"dr", "eng", "prof", "mr", "mrs", "ms", "sheikh", "capt"}


def _posted_at(item: dict[str, Any]) -> datetime:
    posted = item.get("postedAt") or {}
    if isinstance(posted, dict):
        ts = posted.get("timestamp")
        if ts:
            return datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc)
        date = posted.get("date")
        if date:
            return datetime.fromisoformat(str(date).replace("Z", "+00:00"))
    if isinstance(posted, (int, float)):
        return datetime.fromtimestamp(posted / 1000, tz=timezone.utc)
    return datetime.now(timezone.utc)


def post_from_apify(item: dict[str, Any], lane_id: str) -> Post | None:
    """Normalize a harvestapi post item. Returns None for reposts/empty items."""
    if item.get("type") not in (None, "post"):
        return None
    text = (item.get("content") or "").strip()
    post_id = str(item.get("id") or "")
    url = item.get("linkedinUrl") or ""
    if not text or not post_id or not url:
        return None
    if item.get("repost") and not text:
        return None
    author = item.get("author") or {}
    eng = item.get("engagement") or {}
    return Post(
        id=post_id,
        url=url,
        text=text,
        author_name=author.get("name") or "",
        author_headline=author.get("info") or author.get("position") or "",
        author_url=author.get("linkedinUrl") or "",
        author_type=author.get("type") or "profile",
        posted_at=_posted_at(item),
        likes=int(eng.get("likes") or 0),
        comments=int(eng.get("comments") or 0),
        shares=int(eng.get("shares") or 0),
        lane_id=lane_id,
        raw=item,
    )
