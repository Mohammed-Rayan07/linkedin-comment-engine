"""Dashboard clicks -> engine.

The dashboard never touches data/engine.db (the scheduled GitHub run is its only writer). Each click is
appended as one JSON line to state/actions.jsonl in the repo; every run applies the lines it hasn't seen
yet, through the same code paths as a Telegram tap, so the learning loop and stats behave identically.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from .config import Config
from .models import Post

if TYPE_CHECKING:
    from .pipeline import Engine

log = logging.getLogger(__name__)

ACTIONS_NAME = "actions.jsonl"
KINDS = {"posted", "skip", "regen", "reopen", "stage", "note", "metric", "autopilot", "manual"}
# CRM stages after a comment is posted. None = just commented.
STAGES = {"commented": None, "connected": "connected", "replied": "replied", "dm": "dm", "call": "call",
          "client": "client"}
METRICS = {"followers", "impressions_7d", "profile_viewers_90d", "search_appearances_7d"}
MAX_TEXT = 3000


def validate(a: dict[str, Any]) -> str | None:
    """Return an error message, or None if the action is well-formed."""
    kind = a.get("kind")
    if kind not in KINDS:
        return f"unknown action {kind!r}"
    if kind == "autopilot":
        return None if isinstance(a.get("on"), bool) else "autopilot needs on: true/false"
    if kind == "metric":
        if a.get("key") not in METRICS:
            return "unknown metric"
        try:
            float(a.get("value"))
        except (TypeError, ValueError):
            return "metric value must be a number"
        if not isinstance(a.get("day"), str) or len(a["day"]) != 10:
            return "metric day must be YYYY-MM-DD"
        return None
    if kind == "manual":
        # Work done by hand in the browser (no engine card): the CRM gets a card for it.
        for f in ("post_url", "author_name"):
            if not isinstance(a.get(f), str) or not a[f].strip():
                return f"manual needs {f}"
        for f in ("author_headline", "author_url", "text", "note"):
            if a.get(f) is not None and (not isinstance(a[f], str) or len(a[f]) > MAX_TEXT):
                return f"{f} must be text under {MAX_TEXT} chars"
        if a.get("stage") not in STAGES:
            return "unknown stage"
        return None
    if not isinstance(a.get("card"), int):
        return "card must be a number"
    if kind == "stage" and a.get("stage") not in STAGES:
        return "unknown stage"
    for f in ("text", "note"):
        if a.get(f) is not None and (not isinstance(a[f], str) or len(a[f]) > MAX_TEXT):
            return f"{f} must be text under {MAX_TEXT} chars"
    if a.get("opt") is not None and not isinstance(a["opt"], int):
        return "opt must be a number"
    return None


def read_lines(cfg: Config) -> list[str]:
    path = cfg.state_dir / ACTIONS_NAME
    if not path.exists():
        return []
    return [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def apply_actions(engine: "Engine") -> int:
    """Apply dashboard actions not applied yet. Idempotent: replaying the same file applies nothing."""
    store = engine.store
    lines = read_lines(engine.cfg)
    done = int(store.get("actions_applied", "0") or 0)
    applied = 0
    for i in range(done, len(lines)):
        try:
            a = json.loads(lines[i])
            err = validate(a)
            if err:
                log.warning("dashboard action %d ignored: %s", i, err)
            else:
                _apply(engine, a)
                applied += 1
        except Exception as e:  # one bad line must never block the rest
            log.warning("dashboard action %d failed: %s", i, e)
        store.put("actions_applied", str(i + 1))
    return applied


def _apply_manual(engine: "Engine", a: dict[str, Any]) -> None:
    """Log work done by hand in the browser. A comment gives a 'posted' card; no comment gives a
    'skipped' card (connection request only) so the Pipeline shows the person without inflating stats."""
    store = engine.store
    url = a["post_url"].strip()
    post_id = "manual-" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    if not store.get_post_row(post_id):
        store.add_post(Post(
            id=post_id, url=url, text=(a.get("post_text") or "").strip(), author_name=a["author_name"].strip(),
            author_headline=(a.get("author_headline") or "").strip(), author_url=(a.get("author_url") or "").strip(),
            author_type="profile", posted_at=datetime.now(timezone.utc), likes=0, comments=0, shares=0,
            lane_id="manual"), status="scored")
    row = store.db.execute("SELECT id FROM cards WHERE post_id=?", (post_id,)).fetchone()
    text = (a.get("text") or "").strip()
    if row:
        card_id = int(row["id"])
    else:
        card_id = store.add_card(post_id, [{"angle": "manual", "text": text}] if text else [], None)
        if text:
            store.resolve_card(card_id, "posted", 1)
        else:
            store.resolve_card(card_id, "skipped", None)
    store.set_stage(card_id, STAGES[a["stage"]])
    if a.get("note"):
        store.set_note(card_id, a["note"].strip())


def _apply(engine: "Engine", a: dict[str, Any]) -> None:
    store, tg = engine.store, engine.tg
    kind = a["kind"]
    if kind == "autopilot":
        store.put("paused", "0" if a["on"] else "1")
        return
    if kind == "metric":
        store.put_metric(a["day"], a["key"], float(a["value"]))
        return
    if kind == "manual":
        _apply_manual(engine, a)
        return
    card_id = a["card"]
    card = store.get_card(card_id)
    if not card:
        log.warning("dashboard action for unknown card #%s", card_id)
        return
    options = json.loads(card["options_json"])
    label = None

    if kind == "posted":
        opt = a.get("opt")
        text = (a.get("text") or "").strip()
        if card["status"] == "sent":
            if opt and 1 <= opt <= len(options):
                label = engine.handle_action("p", card_id, opt)
            else:
                store.resolve_card(card_id, "posted", 0)
                label = "✅ Logged: posted"
        # his final wording, if he changed the draft, is the best training signal there is
        picked = options[opt - 1]["text"].strip() if opt and 1 <= opt <= len(options) else ""
        if len(text) >= 20 and text != picked:
            engine._learn(store.get_card(card_id), text, "edited")
    elif kind == "skip":
        label = engine.handle_action("s", card_id, None) if card["status"] == "sent" else None
    elif kind == "regen":
        label = engine.handle_action("r", card_id, None) if card["status"] == "sent" else None
    elif kind == "reopen":
        store.reopen_card(card_id)
        tg.restore(card["tg_message_id"], card_id, len(options))
    elif kind == "stage":
        if card["status"] in ("sent", "skipped", "regen"):
            store.resolve_card(card_id, "posted", card["chosen_option"] or 0)
            label = "✅ Logged: posted"
        store.set_stage(card_id, STAGES[a["stage"]])
    elif kind == "note":
        store.set_note(card_id, (a.get("note") or "").strip())

    if label:
        tg.mark(card["tg_message_id"], label)
