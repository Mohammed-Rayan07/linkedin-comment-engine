"""Loads config/*.yaml + .env into one object."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"


@dataclass
class Lane:
    id: str
    name: str
    kind: str  # "search" | "profiles"
    intent: str  # "buyer" | "audience" | "prospect"
    enabled: bool = True
    weight: float = 1.0
    posted_limit: str = "24h"
    max_posts_per_query: int = 10
    max_posts_per_profile: int = 2
    queries: list[str] = field(default_factory=list)
    profiles: list[str] = field(default_factory=list)
    buyer_headline_hints: list[str] = field(default_factory=list)
    author_keywords: str | None = None
    sort_by: str = "relevance"  # relevance | date
    max_age_hours: float | None = None  # overrides filters.max_age_hours for this lane
    min_likes: int = 0
    budget_weight: float = 1.0


@dataclass
class Config:
    settings: dict[str, Any]
    lanes: list[Lane]
    vendor_patterns: list[str]
    profile: dict[str, Any]
    voice: str
    mock: bool
    apify_token: str | None
    telegram_token: str | None
    telegram_chat_id: str | None
    db_path: Path

    def s(self, *keys: str, default: Any = None) -> Any:
        node: Any = self.settings
        for k in keys:
            if not isinstance(node, dict) or k not in node:
                return default
            node = node[k]
        return node

    @property
    def state_dir(self) -> Path:
        """Where the dashboard files live: state/ in the repo for the real database, next to any other one
        (tests, --mock) so those never overwrite the real dashboard data."""
        if self.db_path.resolve() == (DATA_DIR / "engine.db").resolve():
            return ROOT / "state"
        return self.db_path.parent

    @property
    def enabled_lanes(self) -> list[Lane]:
        return [lane for lane in self.lanes if lane.enabled]

    def lane(self, lane_id: str) -> Lane | None:
        return next((lane for lane in self.lanes if lane.id == lane_id), None)


def _read_yaml(name: str) -> Any:
    with open(CONFIG_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _env(name: str) -> str | None:
    """Unset, empty and unfilled placeholders all count as missing."""
    value = (os.getenv(name) or "").strip()
    return None if not value or "REPLACE_ME" in value else value


def load_config(mock: bool | None = None) -> Config:
    load_dotenv(ROOT / ".env")
    lanes_doc = _read_yaml("lanes.yaml")
    lanes = [Lane(**lane) for lane in lanes_doc.get("lanes", [])]
    if mock is None:
        mock = os.getenv("ENGINE_MODE", "live").lower() == "mock"
    db_path = Path(os.getenv("ENGINE_DB", str(DATA_DIR / ("engine.mock.db" if mock else "engine.db"))))
    return Config(
        settings=_read_yaml("settings.yaml"),
        lanes=lanes,
        vendor_patterns=[p.lower() for p in lanes_doc.get("vendor_headline_patterns", [])],
        profile=_read_yaml("expert_profile.yaml"),
        voice=(CONFIG_DIR / "voice.md").read_text(encoding="utf-8"),
        mock=mock,
        apify_token=_env("APIFY_TOKEN"),
        telegram_token=_env("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=_env("TELEGRAM_CHAT_ID"),
        db_path=db_path,
    )
