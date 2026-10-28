"""One run: sync Telegram taps -> fetch -> filter -> score -> draft -> deliver."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from . import filters, inbox, mystats
from .config import Config, Lane
from .drafting import draft_comments
from .export import write_snapshot
from .llm import LLM, LLMRefusal, LLMUnavailable
from .models import Post
from .scoring import score_posts
from .sources import PRICE_PER_POST_USD, ApifyUnavailable, BudgetExhausted, fetch_lane, remaining_today
from .store import Store
from .telegram import Telegram, keyboard, process_updates, render_card

log = logging.getLogger(__name__)


class SendFailed(Exception):
    """Telegram rejected a card. Stop drafting more this run (each draft costs LLM tokens)."""


def _allocate_scrape_budget(lanes: list[Lane], budget: int) -> list[int]:
    """Allocate discovery by ICP lane share without changing comment quality scores."""
    if not lanes or budget <= 0:
        return [0] * len(lanes)
    # Keep tiny one-off runs spread across lanes; apply ICP weights once there is room to do so.
    if budget <= len(lanes) * 10:
        shares = [budget // len(lanes)] * len(lanes)
        for i in range(budget % len(lanes)):
            shares[i] += 1
        return shares
    weights = [max(0.0, lane.budget_weight) for lane in lanes]
    total = sum(weights)
    if total <= 0:
        weights = [1.0] * len(lanes)
        total = float(len(lanes))
    exact = [budget * weight / total for weight in weights]
    shares = [int(value) for value in exact]
    remainder = budget - sum(shares)
    order = sorted(range(len(lanes)), key=lambda i: (exact[i] - shares[i], weights[i]), reverse=True)
    for i in order[:remainder]:
        shares[i] += 1
    return shares


@dataclass
class RunReport:
    fetched: int = 0
    new: int = 0
    filtered: dict[str, int] = field(default_factory=dict)
    scored: int = 0
    carded: int = 0
    skipped_by_writer: int = 0
    taps: int = 0
    failed: bool = False  # scraping produced nothing because every lane errored; the CLI exits non-zero
    notes: list[str] = field(default_factory=list)

    def summary(self) -> str:
        f = ", ".join(f"{k}={v}" for k, v in sorted(self.filtered.items())) or "none"
        out = (f"fetched={self.fetched} new={self.new} filtered[{f}] scored={self.scored} "
               f"cards={self.carded} writer_skips={self.skipped_by_writer} taps_applied={self.taps}")
        if self.failed:
            out = "FAILED: no lane could be scraped\n" + out
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
        card_id = self.store.add_card(p.id, d.options)
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
            options = json.loads(card["options_json"])
            if opt and 1 <= opt <= len(options):
                self._learn(card, options[opt - 1]["text"], "picked")
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

    def _learn(self, card, comment: str, source: str) -> None:
        row = self.store.get_post_row(card["post_id"])
        excerpt = (row["text"] if row else "")[:400]
        self.store.add_example(card["id"], excerpt, comment.strip(), source)

    def handle_reply(self, message_id: int, text: str) -> str:
        """Rayan replied to a card with the comment he actually posted: the best training signal there is."""
        card = self.store.card_by_message(message_id)
        if not card or len(text) < 20:
            return ""
        self._learn(card, text, "edited")
        if card["status"] == "sent":
            self.store.resolve_card(card["id"], "posted", 0)
        return "🧠 Saved. Future drafts will learn from how you wrote this one."

    def handle_command(self, text: str) -> str:
        if text.startswith("/stats"):
            return stats_text(self.store)
        if text.startswith("/pause"):
            self.store.put("paused", "1")
            return "⏸ Paused. No new posts or drafts until you send /resume (your taps still sync)."
        if text.startswith("/resume"):
            self.store.put("paused", "0")
            return "▶️ Resumed. New cards come with the next run (08:00, 13:00, 18:00 Riyadh)."
        if text.startswith("/queue"):
            return queue_text(self.store)
        if text.startswith("/help") or text.startswith("/start"):
            return ("I send you posts worth commenting on, with 3 drafted options each.\n"
                    "Tap ✅ Posted N after you post (edit freely first), ⏭ Skip, or 🔁 New angles.\n"
                    "/queue lists every card still waiting, with links.\n"
                    "/stats shows the last 7 days.\n"
                    "/pause stops new posts and drafts; /resume turns them back on.\n"
                    "Taps are applied at the next scheduled run (08:00, 13:00, 18:00 Riyadh), "
                    "so a spinning button is normal.")
        return ""

    def sync(self, timeout: int = 0) -> int:
        """Apply dashboard clicks first, then Telegram taps."""
        applied = inbox.apply_actions(self)
        return applied + process_updates(self.tg, self.store, self.handle_action, self.handle_command,
                               self.handle_reply, timeout)

    # ---- main run ------------------------------------------------------------
    def run(self, lane_ids: list[str] | None = None, since_days: float | None = None,
            run_budget: int | None = None, card_quota: int | None = None,
            skip_fetch: bool = False) -> RunReport:
        cfg, store = self.cfg, self.store
        report = RunReport()
        report.taps = self.sync()
        if self.store.get("paused") == "1":
            # switched off from the dashboard or /pause: keep syncing clicks, find and draft nothing
            report.notes.append("paused: skipped finding posts and drafting")
            self.update_board()
            return report
        daily_cards_left = (int(cfg.s("budgets", "max_cards_per_day", default=30))
                            - store.today()["cards_sent"])
        if daily_cards_left <= 0:
            report.notes.append("daily card limit reached: skipped scraping and drafting")
            self.update_board()
            return report
        if not skip_fetch:
            try:
                if note := mystats.check(self):
                    report.notes.append(note)
            except Exception as e:  # your stats are a nice-to-have; never block finding posts
                report.notes.append(f"your stats check failed: {e}")

        lanes = [l for l in cfg.enabled_lanes if not lane_ids or l.id in lane_ids]
        if skip_fetch:
            lanes = []  # only score/draft posts already saved by earlier runs
        candidates: list[tuple[Post, Lane]] = []
        # Weight discovery toward real-estate and clinic buyers. Quality scoring stays separate.
        # Scale the scrape ceiling down when this run has fewer card slots left, avoiding spend
        # on candidates the daily delivery cap could not send.
        per_run_cards = int(cfg.s("budgets", "max_cards_per_run", default=15))
        requested_cards = min(per_run_cards, daily_cards_left,
                              card_quota if card_quota is not None else per_run_cards)
        per_run_posts = int(cfg.s("budgets", "max_posts_per_run", default=250))
        requested_posts = min(per_run_posts, run_budget if run_budget else per_run_posts)
        scaled_posts = max(1, (requested_posts * requested_cards + per_run_cards - 1) // per_run_cards)
        run_budget = min(remaining_today(cfg, store), scaled_posts)
        since = datetime.now(timezone.utc) - timedelta(days=since_days) if since_days else None
        shares = _allocate_scrape_budget(lanes, run_budget)
        lanes_tried = lanes_failed = 0
        for lane, share in zip(lanes, shares):
            if share <= 0:
                continue
            lanes_tried += 1
            try:
                posts = fetch_lane(cfg, store, lane, budget=share, since_override=since)
            except BudgetExhausted as e:
                report.notes.append(str(e))
                lanes_tried -= 1
                break
            except ApifyUnavailable as e:
                # the account itself is blocked: trying the other lanes would just repeat the same refusal
                log.error("Apify unavailable, stopping scrape: %s", e)
                report.notes.append(f"Apify unavailable, scraping stopped: {e}")
                report.failed = True
                self._alert_apify(str(e))
                break
            except Exception as e:  # one broken lane shouldn't kill the run
                log.exception("lane %s failed", lane.id)
                report.notes.append(f"lane {lane.id} failed: {e}")
                lanes_failed += 1
                continue
            report.fetched += len(posts)
            lane_new = 0
            lane_filtered: dict[str, int] = {}
            known = store.known_ids([p.id for p in posts])
            for p in posts:
                if p.id in known:
                    continue
                known.add(p.id)
                report.new += 1
                reason = filters.reject_reason(p, lane, cfg)
                if reason:
                    report.filtered[reason] = report.filtered.get(reason, 0) + 1
                    lane_filtered[reason] = lane_filtered.get(reason, 0) + 1
                    store.add_post(p, "filtered", reason)
                else:
                    store.add_post(p, "new")
                    candidates.append((p, lane))
                    lane_new += 1
            log.info("lane %s: %d fetched, %d new candidates, filtered=%s",
                     lane.id, len(posts), lane_new, lane_filtered or "none")

        if lanes_tried and lanes_failed == lanes_tried:
            report.failed = True  # every lane errored: a green run here would hide a dead scraper

        # posts left unscored by an earlier run (e.g. the model was overloaded) get another chance
        seen = {p.id for p, _ in candidates}
        for row in store.db.execute("SELECT * FROM posts WHERE status='new'").fetchall():
            lane = cfg.lane(row["lane_id"])
            if lane and lane.enabled and row["id"] not in seen:
                candidates.append((_post_from_row(row), lane))

        # freshest first, capped to the per-run scoring budget
        candidates.sort(key=lambda pl: (-pl[1].budget_weight, pl[0].age_hours))
        candidates = candidates[: int(cfg.s("budgets", "max_llm_scored_per_run", default=250))]
        if candidates:
            try:
                for p, lane, s, prio in score_posts(cfg, self.llm, candidates):
                    store.set_score(p.id, s, prio)
                    report.scored += 1
            except LLMUnavailable as e:
                report.notes.append(f"{e}; unscored posts will be retried next run")
        try:
            self._deliver_best(report, card_quota)
        except LLMUnavailable as e:
            report.notes.append(f"{e}; remaining drafts will be retried next run")
        self.update_board()
        return report

    def _alert_apify(self, reason: str) -> None:
        """Tell Rayan once a day on Telegram. The GitHub run itself also turns red (non-zero exit)."""
        key = f"alert:apify:{datetime.now(timezone.utc).date().isoformat()}"
        if self.store.get(key):
            return
        try:
            self.tg.send("⚠️ Apify is refusing requests, so no new posts are being found.\n"
                         f"{reason}\n"
                         "Check console.apify.com > Settings > Usage (monthly limit) and the APIFY_TOKEN secret. "
                         "Nothing is being spent while this lasts.")
        except Exception as e:  # the alert is a courtesy; the failed run is the real signal
            log.warning("apify alert not sent: %s", e)
        self.store.put(key, "1")

    def update_board(self) -> None:
        try:
            write_snapshot(self.cfg, self.store)
        except Exception as e:
            log.warning("dashboard snapshot failed: %s", e)
        try:
            self.tg.pin_status(self.store, status_text(self.store))
        except Exception as e:  # the board is a nice-to-have; never fail a run over it
            log.warning("status board update failed: %s", e)

    def _deliver_best(self, report: RunReport, card_quota: int | None = None) -> None:
        cfg, store = self.cfg, self.store
        left_today = max(0, int(cfg.s("budgets", "max_cards_per_day", default=30))
                         - store.today()["cards_sent"])
        per_run = int(cfg.s("budgets", "max_cards_per_run", default=15))
        quota = min(per_run, left_today, card_quota) if card_quota is not None else min(per_run, left_today)
        if quota <= 0:
            report.notes.append("daily card limit reached")
            return
        # best first; posts between floor_priority and min_priority only fill a quota the strong ones can't
        floor = float(cfg.s("budgets", "floor_priority", default=cfg.s("budgets", "min_priority", default=6.0)))
        rows = store.db.execute(
            "SELECT * FROM posts WHERE status='scored' AND priority >= ? ORDER BY priority DESC",
            (floor,),
        ).fetchall()
        for row in rows:
            if report.carded >= quota:
                break
            p = _post_from_row(row)
            lane = cfg.lane(row["lane_id"])
            if not lane or p.age_hours > (lane.max_age_hours or cfg.s("filters", "max_age_hours", default=36)):
                store.set_post_status(p.id, "skipped", "expired")
                continue
            try:
                self._deliver(p, lane, json.loads(row["score_json"]), row["priority"], report)
            except SendFailed as e:
                report.notes.append(f"telegram send failed, stopping this run: {e}")
                break


def queue_text(store: Store, limit: int = 40) -> str:
    rows = store.db.execute(
        """SELECT c.id, p.lane_id, p.author_name, p.url, p.priority FROM cards c JOIN posts p ON p.id=c.post_id
           WHERE c.status='sent' ORDER BY p.priority DESC LIMIT ?""", (limit,)).fetchall()
    if not rows:
        return "Queue is empty. New cards arrive at 08:00, 13:00 and 18:00 Riyadh."
    lines = [f"📥 {len(rows)} cards waiting (best first). Scroll up to the card number to copy a comment."]
    for r in rows:
        lines.append(f"#{r['id']} · {r['lane_id']} · {r['priority']:.1f} · {r['author_name']}\n{r['url']}")
    return "\n".join(lines)[:4000]


def status_text(store: Store) -> str:
    """The pinned board: what's waiting, what you've done, what it cost."""
    by = {(r["lane_id"], r["status"]): r["n"] for r in store.db.execute(
        "SELECT p.lane_id, c.status, COUNT(*) n FROM cards c JOIN posts p ON p.id=c.post_id GROUP BY 1, 2")}
    lanes = sorted({lane for lane, _ in by})
    waiting = sum(n for (_, s), n in by.items() if s == "sent")
    posted = sum(n for (_, s), n in by.items() if s == "posted")
    week = store.db.execute(
        "SELECT COUNT(*) FROM cards WHERE status='posted' AND acted_at >= datetime('now','-7 days')").fetchone()[0]
    learned = store.db.execute("SELECT COUNT(*) FROM examples").fetchone()[0]
    scraped = store.db.execute(
        "SELECT COALESCE(SUM(posts_scraped),0) FROM usage WHERE day >= date('now','start of month')").fetchone()[0]
    lines = ["📊 <b>Comment engine</b>" + ("  ⏸ <b>PAUSED</b> (send /resume)" if store.get("paused") == "1" else ""),
             f"📥 Waiting: <b>{waiting}</b>   ✅ Posted: <b>{posted}</b> ({week} this week)",
             ""]
    for lane in lanes:
        lines.append(f"• {lane}: {by.get((lane, 'sent'), 0)} waiting · {by.get((lane, 'posted'), 0)} posted · "
                     f"{by.get((lane, 'skipped'), 0)} skipped")
    lines += ["",
              f"🧠 Comments learned from: {learned}",
              f"💵 Apify this month: ~${scraped * PRICE_PER_POST_USD:.2f} of $5",
              f"🕒 Updated {datetime.now(timezone.utc).strftime('%d %b %H:%M')} UTC · "
              "next runs 08:00 / 13:00 / 18:00 Riyadh",
              "/queue = waiting cards with links"]
    return "\n".join(lines)


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
