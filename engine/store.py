"""SQLite state: seen posts, cards sent, daily usage, watermarks, Telegram offset."""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .models import Post

# Post ids already handled elsewhere (e.g. a local backfill), committed to git so the scheduled
# GitHub runs, which keep their own database, never send the same post twice.
SEEN_FILE = Path(__file__).resolve().parent.parent / "state" / "seen_post_ids.txt"

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    lane_id TEXT NOT NULL,
    url TEXT NOT NULL,
    author_name TEXT,
    author_headline TEXT,
    author_url TEXT,
    text TEXT,
    posted_at TEXT,
    likes INTEGER,
    comments INTEGER,
    first_seen TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',   -- new | filtered | scored | carded | posted | skipped
    filter_reason TEXT,
    score_json TEXT,
    priority REAL
);
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id TEXT NOT NULL REFERENCES posts(id),
    created_at TEXT NOT NULL,
    tg_message_id INTEGER,
    options_json TEXT NOT NULL,
    connection_note TEXT,
    status TEXT NOT NULL DEFAULT 'sent',  -- sent | posted | skipped | regen
    chosen_option INTEGER,
    acted_at TEXT
);
CREATE TABLE IF NOT EXISTS usage (
    day TEXT PRIMARY KEY,
    posts_scraped INTEGER NOT NULL DEFAULT 0,
    cards_sent INTEGER NOT NULL DEFAULT 0,
    llm_input_tokens INTEGER NOT NULL DEFAULT 0,
    llm_output_tokens INTEGER NOT NULL DEFAULT 0,
    llm_cost_usd REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS metrics (            -- daily numbers: followers (scraped) or impressions (you type them in)
    day TEXT NOT NULL,
    key TEXT NOT NULL,
    value REAL NOT NULL,
    PRIMARY KEY (day, key)
);
CREATE TABLE IF NOT EXISTS my_comments (        -- your own LinkedIn comments, read back from your public activity
    id TEXT PRIMARY KEY,
    post_id TEXT,
    card_id INTEGER,
    url TEXT,
    post_url TEXT,
    post_author TEXT,
    text TEXT,
    created_at TEXT,
    likes INTEGER NOT NULL DEFAULT 0,
    replies INTEGER NOT NULL DEFAULT 0,
    checked_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS examples (           -- comments Rayan actually posted: the writer learns from these
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER,
    post_excerpt TEXT NOT NULL,
    comment TEXT NOT NULL,
    source TEXT NOT NULL,                        -- edited (his own final words) | picked (an option as-is)
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        # columns added after the first release
        for table, column in [("usage", "llm_cost_usd REAL NOT NULL DEFAULT 0"),
                              ("cards", "stage TEXT"),   # CRM stage after posting: connected | replied | dm | call | client
                              ("cards", "note TEXT")]:
            try:
                self.db.execute(f"ALTER TABLE {table} ADD COLUMN {column}")
            except sqlite3.OperationalError:
                pass

    # --- posts -------------------------------------------------------------
    def known_ids(self, ids: list[str]) -> set[str]:
        if not ids:
            return set()
        q = f"SELECT id FROM posts WHERE id IN ({','.join('?' * len(ids))})"
        known = {r["id"] for r in self.db.execute(q, ids)}
        if SEEN_FILE.exists():
            shared = set(SEEN_FILE.read_text(encoding="utf-8").split())
            known |= {i for i in ids if i in shared}
        return known

    def export_seen(self) -> int:
        SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        old = set(SEEN_FILE.read_text(encoding="utf-8").split()) if SEEN_FILE.exists() else set()
        ids = old | {r["id"] for r in self.db.execute("SELECT id FROM posts")}
        SEEN_FILE.write_text("\n".join(sorted(ids)) + "\n", encoding="utf-8")
        return len(ids)

    def add_post(self, p: Post, status: str = "new", reason: str | None = None) -> None:
        self.db.execute(
            """INSERT OR IGNORE INTO posts
               (id, lane_id, url, author_name, author_headline, author_url, text, posted_at,
                likes, comments, first_seen, status, filter_reason)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (p.id, p.lane_id, p.url, p.author_name, p.author_headline, p.author_url, p.text,
             p.posted_at.isoformat(), p.likes, p.comments, _now(), status, reason),
        )
        self.db.commit()

    def set_score(self, post_id: str, score: dict[str, Any], priority: float) -> None:
        self.db.execute(
            "UPDATE posts SET status='scored', score_json=?, priority=? WHERE id=?",
            (json.dumps(score), priority, post_id),
        )
        self.db.commit()

    def set_post_status(self, post_id: str, status: str, reason: str | None = None) -> None:
        self.db.execute("UPDATE posts SET status=?, filter_reason=COALESCE(?, filter_reason) WHERE id=?",
                        (status, reason, post_id))
        self.db.commit()

    def get_post_row(self, post_id: str) -> sqlite3.Row | None:
        return self.db.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()

    # --- cards -------------------------------------------------------------
    def add_card(self, post_id: str, options: list[dict[str, Any]], connection_note: str | None) -> int:
        cur = self.db.execute(
            "INSERT INTO cards (post_id, created_at, options_json, connection_note) VALUES (?,?,?,?)",
            (post_id, _now(), json.dumps(options), connection_note),
        )
        self.db.execute("UPDATE posts SET status='carded' WHERE id=?", (post_id,))
        self.db.commit()
        return int(cur.lastrowid)

    def delete_card(self, card_id: int) -> None:
        card = self.get_card(card_id)
        self.db.execute("DELETE FROM cards WHERE id=?", (card_id,))
        if card:
            self.db.execute("UPDATE posts SET status='scored' WHERE id=?", (card["post_id"],))
        self.db.commit()

    def set_card_message(self, card_id: int, message_id: int) -> None:
        self.db.execute("UPDATE cards SET tg_message_id=? WHERE id=?", (message_id, card_id))
        self.db.commit()

    def get_card(self, card_id: int) -> sqlite3.Row | None:
        return self.db.execute("SELECT * FROM cards WHERE id=?", (card_id,)).fetchone()

    def resolve_card(self, card_id: int, status: str, chosen: int | None = None) -> None:
        self.db.execute("UPDATE cards SET status=?, chosen_option=?, acted_at=? WHERE id=?",
                        (status, chosen, _now(), card_id))
        card = self.get_card(card_id)
        if card and status in ("posted", "skipped"):
            self.db.execute("UPDATE posts SET status=? WHERE id=?", (status, card["post_id"]))
        self.db.commit()

    def reopen_card(self, card_id: int) -> None:
        """Undo a skip (or a wrong Posted tap): the card goes back to the queue."""
        self.db.execute("UPDATE cards SET status='sent', chosen_option=NULL, stage=NULL, acted_at=? WHERE id=?",
                        (_now(), card_id))
        card = self.get_card(card_id)
        if card:
            self.db.execute("UPDATE posts SET status='carded' WHERE id=?", (card["post_id"],))
        self.db.commit()

    def set_stage(self, card_id: int, stage: str | None) -> None:
        self.db.execute("UPDATE cards SET stage=? WHERE id=?", (stage, card_id))
        self.db.commit()

    def set_note(self, card_id: int, note: str) -> None:
        self.db.execute("UPDATE cards SET note=? WHERE id=?", (note, card_id))
        self.db.commit()

    def card_by_message(self, message_id: int) -> sqlite3.Row | None:
        return self.db.execute("SELECT * FROM cards WHERE tg_message_id=?", (message_id,)).fetchone()

    # --- learning examples -------------------------------------------------
    def add_example(self, card_id: int, post_excerpt: str, comment: str, source: str) -> None:
        # one example per card: an edit replaces an earlier "picked" option
        self.db.execute("DELETE FROM examples WHERE card_id=?", (card_id,))
        self.db.execute(
            "INSERT INTO examples (card_id, post_excerpt, comment, source, created_at) VALUES (?,?,?,?,?)",
            (card_id, post_excerpt, comment, source, _now()))
        self.db.commit()

    def recent_examples(self, limit: int = 10) -> list[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM examples ORDER BY (source='edited') DESC, created_at DESC LIMIT ?", (limit,)).fetchall()

    # --- usage / budgets ---------------------------------------------------
    def _bump(self, column: str, n: int) -> None:
        day = date.today().isoformat()
        self.db.execute("INSERT OR IGNORE INTO usage (day) VALUES (?)", (day,))
        self.db.execute(f"UPDATE usage SET {column} = {column} + ? WHERE day=?", (n, day))
        self.db.commit()

    def add_scraped(self, n: int) -> None:
        self._bump("posts_scraped", n)

    def add_card_sent(self) -> None:
        self._bump("cards_sent", 1)

    def add_tokens(self, input_tokens: int, output_tokens: int, cost_usd: float = 0.0) -> None:
        self._bump("llm_input_tokens", input_tokens)
        self._bump("llm_output_tokens", output_tokens)
        day = date.today().isoformat()
        self.db.execute("UPDATE usage SET llm_cost_usd = llm_cost_usd + ? WHERE day=?", (cost_usd, day))
        self.db.commit()

    def today(self) -> dict[str, int]:
        row = self.db.execute("SELECT * FROM usage WHERE day=?", (date.today().isoformat(),)).fetchone()
        return dict(row) if row else {"posts_scraped": 0, "cards_sent": 0,
                                       "llm_input_tokens": 0, "llm_output_tokens": 0}

    # --- kv ----------------------------------------------------------------
    def get(self, key: str, default: str | None = None) -> str | None:
        row = self.db.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def put(self, key: str, value: str) -> None:
        self.db.execute("INSERT INTO kv (key, value) VALUES (?, ?) "
                        "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
        self.db.commit()

    # --- metrics -------------------------------------------------------------
    def put_metric(self, day: str, key: str, value: float) -> None:
        self.db.execute("INSERT INTO metrics (day, key, value) VALUES (?,?,?) "
                        "ON CONFLICT(day, key) DO UPDATE SET value=excluded.value", (day, key, value))
        self.db.commit()

    def upsert_my_comment(self, row: dict[str, Any]) -> None:
        self.db.execute(
            """INSERT INTO my_comments (id, post_id, card_id, url, post_url, post_author, text, created_at,
                                        likes, replies, checked_at)
               VALUES (:id, :post_id, :card_id, :url, :post_url, :post_author, :text, :created_at,
                       :likes, :replies, :checked_at)
               ON CONFLICT(id) DO UPDATE SET likes=excluded.likes, replies=excluded.replies,
                   text=excluded.text, checked_at=excluded.checked_at,
                   card_id=COALESCE(excluded.card_id, my_comments.card_id)""", row)
        self.db.commit()

    # --- reporting ---------------------------------------------------------
    def stats(self, days: int = 7) -> dict[str, Any]:
        q = """SELECT p.lane_id, c.status, COUNT(*) n FROM cards c JOIN posts p ON p.id=c.post_id
               WHERE c.created_at >= datetime('now', ?) GROUP BY p.lane_id, c.status"""
        rows = self.db.execute(q, (f"-{days} days",)).fetchall()
        usage = self.db.execute("SELECT * FROM usage ORDER BY day DESC LIMIT ?", (days,)).fetchall()
        return {"cards": [dict(r) for r in rows], "usage": [dict(r) for r in usage]}

    def frequent_authors(self, min_posts: int = 2, limit: int = 20) -> list[sqlite3.Row]:
        q = """SELECT author_name, author_headline, author_url, COUNT(*) n,
                      AVG(likes + 2*comments) eng
               FROM posts WHERE author_url != '' GROUP BY author_url
               HAVING n >= ? ORDER BY eng DESC LIMIT ?"""
        return self.db.execute(q, (min_posts, limit)).fetchall()
