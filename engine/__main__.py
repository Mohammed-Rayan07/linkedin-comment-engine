"""CLI.  python -m engine <command> [--mock]

  run               one full pass (sync taps, fetch, score, draft, send cards)
  dashboard         open the CRM dashboard (hosted on GitHub Pages, works on your phone too)
  bot               stay online: apply button taps instantly and handle /stats
  yield-test        measure which lanes actually surface buyers (spends a little Apify credit)
  suggest-creators  authors who keep showing up with high engagement (watchlist candidates)
  stats             last 7 days
  telegram-setup    print your chat id after you message the bot
  check "text"      run the truth/voice guard on any comment you wrote yourself
"""
from __future__ import annotations

import argparse
import logging
import sys
from collections import Counter

import httpx

from . import filters, guard
from .config import load_config
from .pipeline import Engine, stats_text
from .sources import PRICE_PER_POST_USD, fetch_lane

DASHBOARD_URL = "https://mohammed-rayan07.github.io/comment-crm/"


def main() -> int:
    ap = argparse.ArgumentParser(prog="engine", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["run", "fill", "dashboard", "bot", "yield-test", "suggest-creators", "stats",
                                        "telegram-setup", "check"])
    ap.add_argument("text", nargs="?", help="comment text for `check`")
    ap.add_argument("--mock", action="store_true", help="use fixtures + fake LLM, no API keys needed")
    ap.add_argument("--lanes", help="comma-separated lane ids to run (default: all enabled)")
    ap.add_argument("--yes", action="store_true", help="skip the cost confirmation for yield-test")
    ap.add_argument("--target", type=int, default=20, help="fill: cards you want waiting in Telegram")
    ap.add_argument("--days", type=float, default=5, help="fill: how far back to look")
    ap.add_argument("--max-posts", type=int, default=200, help="fill: Apify post budget (~$0.002 each)")
    ap.add_argument("--no-fetch", action="store_true", help="fill: don't scrape, just score/draft saved posts")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    for noisy in ("httpx", "httpcore", "anthropic"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    cfg = load_config(mock=True if args.mock else None)

    if args.command == "check":
        if not args.text:
            ap.error("check needs the comment text in quotes")
        problems = guard.check(args.text, cfg.profile, "", cfg.s("comment", "min_chars", default=140),
                               cfg.s("comment", "max_chars", default=650))
        print("✅ clean" if not problems else "\n".join(f"❌ {p}" for p in problems))
        return 0

    if args.command == "telegram-setup":
        if not cfg.telegram_token:
            print("Set TELEGRAM_BOT_TOKEN in .env first (create a bot with @BotFather).")
            return 1
        r = httpx.get(f"https://api.telegram.org/bot{cfg.telegram_token}/getUpdates", timeout=30).json()
        chats = {(u.get("message") or {}).get("chat", {}).get("id") for u in r.get("result", [])} - {None}
        if not chats:
            print("No messages yet. Open your bot in Telegram, send it 'hi', then run this again.")
            return 1
        for c in chats:
            print(f"TELEGRAM_CHAT_ID={c}")
        return 0

    if args.command == "dashboard":
        import webbrowser
        print(f"Dashboard: {DASHBOARD_URL}")
        webbrowser.open(DASHBOARD_URL)
        return 0

    engine = Engine(cfg)

    if args.command == "run":
        report = engine.run(args.lanes.split(",") if args.lanes else None)
        print(report.summary())
        return 0

    if args.command == "fill":
        return fill(cfg, engine, args)

    if args.command == "bot":
        if not engine.tg.enabled:
            print("Telegram isn't configured (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID), nothing to listen to.")
            return 1
        print("Listening for button taps and /stats. Ctrl+C to stop.")
        while True:
            try:
                engine.sync(timeout=50)
            except KeyboardInterrupt:
                return 0
            except Exception as e:  # network blips shouldn't kill the bot
                logging.warning("sync error: %s", e)

    if args.command == "stats":
        print(stats_text(engine.store))
        return 0

    if args.command == "suggest-creators":
        rows = engine.store.frequent_authors()
        if not rows:
            print("Not enough data yet. Let the engine run for a few days.")
        for r in rows:
            print(f"{r['n']:>3} posts · avg eng {r['eng']:.0f} · {r['author_name']} · {r['author_headline'][:70]}\n"
                  f"      {r['author_url']}")
        return 0

    if args.command == "yield-test":
        return yield_test(cfg, engine, args)
    return 0


def fill(cfg, engine: Engine, args) -> int:
    """One-off backfill: look back N days and keep going until `target` cards are waiting in Telegram."""
    pending = engine.store.db.execute("SELECT COUNT(*) FROM cards WHERE status='sent'").fetchone()[0]
    need = args.target - pending
    print(f"{pending} cards already waiting; need {max(need, 0)} more. "
          f"Budget: up to {args.max_posts} posts ≈ ${args.max_posts * PRICE_PER_POST_USD:.2f} of Apify credit.")
    if need <= 0:
        return 0
    b = cfg.settings.setdefault("budgets", {})
    b["max_posts_scraped_per_day"] = engine.store.today()["posts_scraped"] + args.max_posts
    b["max_llm_scored_per_run"] = args.max_posts
    b.setdefault("floor_priority", 5.0)
    report = engine.run(args.lanes.split(",") if args.lanes else None,
                        since_days=args.days, run_budget=args.max_posts, card_quota=need,
                        skip_fetch=args.no_fetch)
    print(report.summary())
    print(f"shared seen-ids file now has {engine.store.export_seen()} posts")
    return 0


def yield_test(cfg, engine: Engine, args) -> int:
    """Per search lane: what share of authors look like buyers vs vendors? Decide lanes on data."""
    lanes = [l for l in cfg.lanes if l.kind == "search" and (not args.lanes or l.id in args.lanes.split(","))]
    est_posts = sum(min(len(l.queries), 3) * 10 for l in lanes)  # matches the probe below exactly
    print(f"Yield test on {len(lanes)} lanes, up to ~{est_posts} posts from the past week "
          f"≈ ${est_posts * PRICE_PER_POST_USD:.2f} of Apify credit.")
    if not cfg.mock and not args.yes:
        if input("Proceed? [y/N] ").strip().lower() != "y":
            return 1
    print(f"\n{'lane':<12}{'posts':>6}{'buyer-ish':>11}{'vendor':>8}{'company':>9}{'non-EN':>8}{'med.eng':>9}")
    for lane in lanes:
        probe = type(lane)(**{**lane.__dict__, "queries": lane.queries[:3], "max_posts_per_query": 10})
        try:
            posts = fetch_lane(cfg, engine.store, probe, probe=True)
        except Exception as e:
            print(f"{lane.id:<12}  failed: {e}")
            continue
        n = len(posts) or 1
        hints = [h.lower() for h in lane.buyer_headline_hints]
        buyer = sum(1 for p in posts if any(h in p.author_headline.lower() for h in hints)
                    and not filters.is_vendor(p.author_headline, cfg.vendor_patterns))
        vendor = sum(1 for p in posts if filters.is_vendor(p.author_headline, cfg.vendor_patterns))
        company = sum(1 for p in posts if p.author_type == "company")
        non_en = sum(1 for p in posts if filters.is_mostly_non_english(p.text))
        engs = sorted(p.likes + 2 * p.comments for p in posts) or [0]
        print(f"{lane.id:<12}{len(posts):>6}{buyer / n:>10.0%}{vendor / n:>8.0%}{company / n:>9.0%}"
              f"{non_en / n:>8.0%}{engs[len(engs) // 2]:>9}")
        top = Counter(p.author_headline[:60] for p in posts).most_common(3)
        for h, c in top:
            print(f"{'':<12}  e.g. {h}")
    print("\nKeep lanes with a high buyer-ish share. A lane that's mostly vendors is a waste of credit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
