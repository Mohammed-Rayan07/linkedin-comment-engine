"""One run: sync Telegram taps -> fetch -> filter -> score -> draft -> deliver."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime

from . import filters
from .config import Config, Lane
from .drafting import draft_comments
from .llm import LLM, LLMRefusal
from .models import Post
from .scoring import score_posts
from .sources import PRICE_PER_POST_USD, BudgetExhausted, fetch_lane, remaining_today
from .store import Store
from .telegram import Telegram, keyboard, process_updates, render_card

log = logging.getLogger(__name__)


class SendFailed(Exception):
    """Telegram rejected a card. Stop drafting more this run (each draft costs LLM tokens)."""


@dataclass
class RunReport:
    fetched: int = 0
    new: int = 0
    filtered: dict[str, int] = field(default_factory=dict)
    scored: int = 0
    carded: int = 0
    skipped_by_writer: int = 0
    taps: int = 0
    notes: list[str] = field(default_factory=list)

    def summary(self) -> str:
        f = ", ".join(f"{k}={v}" for k, v in sorted(self.filtered.items())) or "none"
        out = (f"fetched={self.fetched} new={self.new} filtered[{f}] scored={self.scored} "
               f"cards={self.carded} writer_skips={self.skipped_by_writer} taps_applied={self.taps}")
        return out + "".join(f"\n  - {n}" for n in self.notes)


def _post_from_row(row) -> Post:
    return Post(
        id=row["id"], url=row["url"], text=row["text"], author_name=row["author_name"] or "",
        author_headline=row["author_headline"] or "", author_url=row["author_url"] or "",
        author_type="profile", posted_at=datetime.fromisoformat(row["posted_at"]),
        likes=row["likes"] or 0, comments=row["comments"] or 0, shares=0, lane_id=row["lane_id"],
    )


class Engine:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.store = Store(cfg.db_path)
        self.llm = LLM(cfg, self.store)
        self.tg = Telegram(cfg)

    # ---- delivery ----------------------------------------------------------
    def _deliver(self, p: Post, lane: Lane, score: dict, prio: float, report: RunReport) -> bool:
        try:
            d = draft_comments(self.cfg, self.llm, p, lane, score)
        except LLMRefusal as e:
            self.store.set_post_status(p.id, "skipped", f"refusal:{e}")
            return False
        if not d.options:
            self.store.set_post_status(p.id, "skipped", f"writer:{d.skip_reason}")
            report.skipped_by_writer += 1
            return False
        card_id = self.store.add_card(p.id, d.options, d.connection_note)
        try:
            msg_id = self.tg.send(render_card(card_id, p, lane, score, prio, d), keyboard(card_id, len(d.options)))
        except Exception as e:
            # undo so the post is retried next run instead of being stranded as "carded"
            log.warning("telegram send failed for post %s: %s", p.id, e)
            self.store.delete_card(card_id)
            raise SendFailed(str(e)) from e
        if msg_id:
            self.store.set_card_message(card_id, msg_id)
        self.store.add_card_sent()
        report.carded += 1
        return True

    # ---- Telegram taps -----------------------------------------------------
    def handle_action(self, kind: str, card_id: int, opt: int | None) -> str:
        card = self.store.get_card(card_id)
        if not card:
            return "Unknown card"
        if card["status"] != "sent":
            return f"Already {card['status']}"
        if kind == "p":
            self.store.resolve_card(card_id, "posted", opt)
            return f"✅ Logged: posted option {opt}"
        if kind == "s":
            self.store.resolve_card(card_id, "skipped")
            return "⏭ Skipped"
        # regenerate with fresh angles
        self.store.resolve_card(card_id, "regen")
        row = self.store.get_post_row(card["post_id"])
        lane = self.cfg.lane(row["lane_id"]) if row else None
        if not row or not lane:
            return "Post no longer available"
        score = json.loads(row["score_json"] or "{}")
        old = [o["text"] for o in json.loads(card["options_json"])]
        score = dict(score, why=(score.get("why", "") + " | Rayan wants different angles than: "
                                 + " /// ".join(o[:120] for o in old)))
        try:
            self._deliver(_post_from_row(row), lane, score, row["priority"] or 0, RunReport())
        except SendFailed:
            return "Couldn't send new angles"
        return "🔁 New angles sent"

    def handle_command(self, text: str) -> str:
        if text.startswith("/stats"):
            return stats_text(self.store)
        if text.startswith("/help") or text.startswith("/start"):
            return ("I send you posts worth commenting on, with 3 drafted options each.\n"
                    "Tap ✅ Posted N after you post (edit freely first), ⏭ Skip, or 🔁 New angles.\n"
                    "/stats shows the last 7 days.")
        return ""

    def sync(self, timeout: int = 0) -> int:
        return process_updates(self.tg, self.store, self.handle_action, self.handle_command, timeout)

    # ---- main run ------------------------------------------------------------
    def run(self, lane_ids: list[str] | None = None) -> RunReport:
        cfg, store = self.cfg, self.store
        report = RunReport()
        report.taps = self.sync()

        lanes = [l for l in cfg.enabled_lanes if not lane_ids or l.id in lane_ids]
        candidates: list[tuple[Post, Lane]] = []
        # split this run's scrape budget fairly so the first lane can't eat the whole day
        run_budget = min(remaining_today(cfg, store), int(cfg.s("budgets", "max_posts_per_run", default=8)))
        for i, lane in enumerate(lanes):
            share = max(1, run_budget // len(lanes) + (1 if i < run_budget % len(lanes) else 0))
            try:
                posts = fetch_lane(cfg, store, lane, budget=share)
            except BudgetExhausted as e:
                report.notes.append(str(e))
                break
            except Exception as e:  # one broken lane shouldn't kill the run
                log.exception("lane %s failed", lane.id)
                report.notes.append(f"lane {lane.id} failed: {e}")
                continue
            report.fetched += len(posts)
            known = store.known_ids([p.id for p in posts])
            for p in posts:
                if p.id in known:
                    continue
                known.add(p.id)
                report.new += 1
                reason = filters.reject_reason(p, lane, cfg)
                if reason:
                    report.filtered[reason] = report.filtered.get(reason, 0) + 1
                    store.add_post(p, "filtered", reason)
                else:
                    store.add_post(p, "new")
                    candidates.append((p, lane))

        # freshest first, capped to the per-run scoring budget
        candidates.sort(key=lambda pl: (-pl[1].weight, pl[0].age_hours))
        candidates = candidates[: int(cfg.s("budgets", "max_llm_scored_per_run", default=40))]
        if candidates:
            for p, lane, s, prio in score_posts(cfg, self.llm, candidates):
                store.set_score(p.id, s, prio)
                report.scored += 1

        self._deliver_best(report)
        return report

    def _deliver_best(self, report: RunReport) -> None:
        cfg, store = self.cfg, self.store
        left_today = int(cfg.s("budgets", "max_cards_per_day", default=20)) - store.today()["cards_sent"]
        quota = min(int(cfg.s("budgets", "max_cards_per_run", default=8)), left_today)
        if quota <= 0:
            report.notes.append("daily card limit reached")
            return
        rows = store.db.execute(
            "SELECT * FROM posts WHERE status='scored' AND priority >= ? ORDER BY priority DESC",
            (float(cfg.s("budgets", "min_priority", default=6.0)),),
        ).fetchall()
        max_age = cfg.s("filters", "max_age_hours", default=36)
        for row in rows:
            if report.carded >= quota:
                break
            p = _post_from_row(row)
            lane = cfg.lane(row["lane_id"])
            if not lane or p.age_hours > max_age:
                store.set_post_status(p.id, "skipped", "expired")
                continue
            try:
                self._deliver(p, lane, json.loads(row["score_json"]), row["priority"], report)
            except SendFailed as e:
                report.notes.append(f"telegram send failed, stopping this run: {e}")
                break


def stats_text(store: Store, days: int = 7) -> str:
    s = store.stats(days)
    by_lane: dict[str, dict[str, int]] = {}
    for r in s["cards"]:
        by_lane.setdefault(r["lane_id"], {})[r["status"]] = r["n"]
    lines = [f"📊 Last {days} days"]
    for lane, st in sorted(by_lane.items()):
        total = sum(st.values())
        lines.append(f"• {lane}: {total} cards · {st.get('posted', 0)} posted · "
                     f"{st.get('skipped', 0)} skipped · {st.get('sent', 0)} pending")
    claude = sum(u.get("llm_cost_usd") or 0 for u in s["usage"])
    apify = sum(u["posts_scraped"] for u in s["usage"]) * PRICE_PER_POST_USD
    for u in s["usage"]:
        lines.append(f"  {u['day']}: scraped {u['posts_scraped']} · cards {u['cards_sent']} · "
                     f"Claude ${u.get('llm_cost_usd') or 0:.2f}")
    lines.append(f"💵 Spend: Claude ${claude:.2f} + Apify ~${apify:.2f} (estimate from token/post counts)")
    return "\n".join(lines)
