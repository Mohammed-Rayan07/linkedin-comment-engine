from pathlib import Path

import pytest

from engine import guard
from engine.config import load_config
from engine.pipeline import Engine


@pytest.fixture()
def cfg(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ENGINE_DB", str(tmp_path / "test.db"))
    cfg = load_config(mock=True)
    # tests run against the three fixture lanes with global limits, whatever the live lanes.yaml says
    for lane in cfg.lanes:
        lane.enabled = lane.id in ("clinics", "realestate", "agencies")
        lane.max_age_hours, lane.min_likes = None, 0
    return cfg


def check(cfg, text, post=""):
    return guard.check(text, cfg.profile, post, 0, 2000)


# --- truth gate -------------------------------------------------------------
def test_invented_number_is_blocked(cfg):
    v = check(cfg, "We cut no-shows by 37% in the first month with a voice agent.")
    assert any("37" in x for x in v)


def test_client_claim_is_blocked(cfg):
    assert any("client" in x for x in check(cfg, "For one client the agent booked every after-hours call."))
    assert any("client" in x for x in check(cfg, "We helped a clinic answer every call."))


def test_proof_bank_numbers_are_allowed(cfg):
    text = "When I mapped a distributor's workflow, 3,000 invoices a month were matched by hand, 10-15 minutes each."
    assert check(cfg, text) == []


def test_numbers_quoted_from_post_are_allowed(cfg):
    post = "We bought 600 leads from portals last month."
    assert check(cfg, "600 leads and half waited past the first hour. That gap is the whole game.", post) == []


def test_trivial_numbers_and_times_pass(cfg):
    assert check(cfg, "Call your own front desk at 7 PM on a Friday. Do it 3 times. Being reachable 24/7 matters.") == []


def test_style_bans(cfg):
    assert any("opener" in x for x in check(cfg, "Great post! Speed matters a lot here."))
    assert any("em dash" in x for x in check(cfg, "Speed matters — always."))
    assert any("pitchy" in x for x in check(cfg, "Speed matters. DM me for a demo."))
    assert any("it's not X" in x for x in check(cfg, "It's not a lead problem, it's a follow-up problem."))
    assert any("leverage" in x for x in check(cfg, "You can leverage agents for this."))


def test_ai_templates_blocked_but_natural_contrast_passes(cfg):
    # real drafts that read as AI under other people's posts
    assert check(cfg, "The hard part isn't that they lack dedication. It is that nobody has a fixed role.")
    assert check(cfg, "The step most brokerages miss isn't getting more enquiries, but ensuring a fast reply.")
    assert check(cfg, "The hidden cost of wearing every hat isn't just fatigue, it's response latency.")
    assert check(cfg, "Lead loss usually comes down to who owns the follow-up.")
    # the same words, said the way people actually talk
    assert check(cfg, "Honestly I'd push back on the hiring part. It isn't cheap, but it's the only fix for walk-ins.") == []
    assert check(cfg, "Ha, my WhatsApp is not a CRM, but I treat it like one.") == []


def test_family_never_mentioned(cfg):
    assert any("forbidden" in x for x in check(cfg, "My dad runs a logistics operation like this."))


# --- end to end (mock) ------------------------------------------------------
def test_mock_run_end_to_end(cfg, capsys):
    engine = Engine(cfg)
    report = engine.run()
    assert report.new == 7
    assert report.filtered.get("vendor_author") == 1
    assert report.filtered.get("non_english") == 1
    assert report.filtered.get("too_old") == 1
    assert report.filtered.get("job_post") == 1
    assert report.carded == 3
    out = capsys.readouterr().out
    assert "Option 1" in out and "Connection note" not in out

    # second run: everything already seen, nothing re-sent
    report2 = engine.run()
    assert report2.new == 0 and report2.carded == 0

    # taps are applied
    assert engine.handle_action("p", 1, 2).startswith("✅")
    assert engine.store.get_card(1)["status"] == "posted"
    assert engine.handle_action("p", 1, 2).startswith("Already")


def test_percentage_must_match_a_percentage(cfg):
    # "40" exists in the proof bank as "30-40 items", but not as a percentage
    assert any("40%" in x for x in check(cfg, "That alone usually cuts missed bookings by 40% in a month."))
    assert check(cfg, "43% of the farmers had no credit bureau record.") == []


def test_small_invented_outcomes_are_blocked(cfg):
    assert any("3x" in x for x in check(cfg, "Answering after hours gets you 3x more bookings."))
    assert any("'7'" in x for x in check(cfg, "That change saved 7 hours a week of front-desk time."))
    assert any("in half" in x for x in check(cfg, "Instant replies cut no-shows in half."))
    # small numbers that are in the proof bank, or not outcomes, still pass
    assert check(cfg, "At 11 PM I called 5 clinics. The 6th answered. Two lessons from that night.") == []


def test_live_budget_split_and_query_rotation(cfg, monkeypatch):
    """Live path with a fake Apify: 8 posts/run split across 3 lanes, queries rotate, daily cap holds."""
    from engine import sources
    calls = []

    def fake_actor(_cfg, actor, payload, max_items):
        calls.append((payload.get("searchQueries"), payload["maxPosts"], max_items))
        return [{"type": "post", "id": f"{len(calls)}-{i}", "linkedinUrl": "u", "content": "x" * 300,
                 "author": {"name": "A B", "info": "Clinic owner"}, "postedAt": {"timestamp": 0}}
                for i in range(max_items)]

    monkeypatch.setattr(sources, "_run_actor", fake_actor)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    cfg.settings["budgets"].update(max_posts_scraped_per_day=25, max_posts_per_run=8)
    cfg.mock = False
    cfg.apify_token = "test"
    engine = Engine(cfg)
    engine.llm.cfg = cfg
    monkeypatch.setattr("engine.pipeline.score_posts", lambda *a, **k: [])

    engine.run()
    assert [c[2] for c in calls] == [3, 3, 2]                 # 8 split across 3 lanes
    first_clinic_queries = calls[0][0]
    engine.run()
    assert calls[3][0] != first_clinic_queries                # next run uses the next queries
    for _ in range(3):
        engine.run()
    assert engine.store.today()["posts_scraped"] == 25        # daily cap respected exactly


def test_learning_from_posted_and_edited_comments(cfg):
    engine = Engine(cfg)
    engine.run()
    engine.store.set_card_message(1, 111)
    engine.store.set_card_message(2, 222)
    engine.handle_action("p", 1, 1)                       # picked option 1 as-is
    assert engine.handle_reply(222, "My own rewritten comment about missed calls after 7 PM.").startswith("🧠")
    ex = engine.store.recent_examples()
    assert [e["source"] for e in ex] == ["edited", "picked"]
    assert engine.store.get_card(2)["status"] == "posted"
    from engine.drafting import _system
    assert "My own rewritten comment" in _system(cfg, ex)


def test_spelled_out_numbers_are_checked(cfg):
    assert any("40%" in x for x in check(cfg, "That cuts missed bookings by forty percent in a month."))
    assert any("'8'" in x for x in check(cfg, "It saved eight hours a week of admin."))
    # spelled-out numbers that ARE in the proof bank still pass
    assert check(cfg, "Three missed calls a day at a thirty percent booking rate adds up fast.") == []


def _write_actions(cfg, actions):
    import json as _json
    path = cfg.state_dir / "actions.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        for a in actions:
            f.write(_json.dumps(a) + "\n")


def test_dashboard_actions_apply_once_and_feed_learning(cfg):
    import json as _json
    from engine import inbox
    engine = Engine(cfg)
    engine.run()
    opt1 = _json.loads(engine.store.get_card(1)["options_json"])[0]["text"]
    _write_actions(cfg, [
        {"kind": "posted", "card": 1, "opt": 1},                                   # as-is, like a Telegram tap
        {"kind": "posted", "card": 2, "opt": 2, "text": "My own final wording about after-hours calls."},
        {"kind": "stage", "card": 2, "stage": "replied"},
        {"kind": "note", "card": 2, "note": "asked about pricing"},
        {"kind": "skip", "card": 3},
        {"kind": "bogus", "card": 3},                                              # ignored, never blocks the rest
        {"kind": "metric", "key": "impressions_7d", "value": 1234, "day": "2026-10-06"},
    ])
    assert inbox.apply_actions(engine) == 6
    assert inbox.apply_actions(engine) == 0                                        # replaying applies nothing
    c1, c2, c3 = (engine.store.get_card(i) for i in (1, 2, 3))
    assert (c1["status"], c1["chosen_option"]) == ("posted", 1)
    assert (c2["status"], c2["stage"], c2["note"]) == ("posted", "replied", "asked about pricing")
    assert c3["status"] == "skipped"
    ex = {e["card_id"]: e for e in engine.store.recent_examples()}
    assert (ex[1]["source"], ex[1]["comment"]) == ("picked", opt1)                 # same row a Telegram tap makes
    assert (ex[2]["source"], ex[2]["comment"]) == ("edited", "My own final wording about after-hours calls.")
    # the snapshot the dashboard reads reflects all of it
    from engine.export import snapshot
    snap = snapshot(cfg, engine.store)
    assert snap["actions_applied"] == 7
    card2 = next(c for c in snap["cards"] if c["id"] == 2)
    assert card2["stage"] == "replied" and card2["options"]
    assert snap["metrics"]["impressions_7d"][0]["value"] == 1234


def test_reopen_and_stage_from_queue(cfg):
    from engine import inbox
    engine = Engine(cfg)
    engine.run()
    _write_actions(cfg, [{"kind": "skip", "card": 1}, {"kind": "reopen", "card": 1},
                         {"kind": "stage", "card": 2, "stage": "connected"}])       # dragged straight from To post
    inbox.apply_actions(engine)
    assert engine.store.get_card(1)["status"] == "sent"
    c2 = engine.store.get_card(2)
    assert (c2["status"], c2["stage"]) == ("posted", "connected")


def test_my_comment_matches_card_by_ugc_or_activity_id(cfg):
    from engine import mystats
    engine = Engine(cfg)
    engine.run()
    card = engine.store.get_card(1)
    engine.store.db.execute("UPDATE posts SET url=? WHERE id=?",
                            ("https://www.linkedin.com/posts/x_y-activity-7512630430219616256-M30A", card["post_id"]))
    # LinkedIn gives the same post an activity id and a ugcPost id; either one in either URL must match
    item = {"id": "c1", "postId": "7511860364372774912", "post": {"id": "7511860364372774912",
            "shareUrn": "urn:li:activity:7512630430219616256",
            "linkedinUrl": "https://www.linkedin.com/posts/x_y-ugcPost-7511860364372774912-Mk6R"}}
    assert mystats.match_card(engine.store, item)["id"] == 1
    assert mystats.match_card(engine.store, {"id": "c3", "postId": card["post_id"]})["id"] == 1
    assert mystats.match_card(engine.store, {"id": "c2", "postId": "123", "post": {"id": "123"}}) is None


def test_pause_switch_stops_drafting_but_keeps_syncing(cfg):
    from engine import inbox
    engine = Engine(cfg)
    _write_actions(cfg, [{"kind": "autopilot", "on": False}])
    report = engine.run()
    assert report.carded == 0 and engine.store.get("paused") == "1"
    _write_actions(cfg, [{"kind": "autopilot", "on": True}])
    assert engine.run().carded > 0                       # back to normal
    assert "Paused" in engine.handle_command("/pause") and engine.store.get("paused") == "1"
    assert "Resumed" in engine.handle_command("/resume") and engine.store.get("paused") == "0"


def test_manual_action_logs_hand_done_work(cfg):
    from engine import inbox
    from engine.export import snapshot
    engine = Engine(cfg)
    engine.run()
    commented = {"kind": "manual", "post_url": "https://www.linkedin.com/in/x-y/recent-activity/all/",
                 "author_name": "Pat Example", "author_headline": "Founder", "text": "A real comment I posted by hand.",
                 "stage": "connected", "note": "request sent"}
    connect_only = {"kind": "manual", "post_url": "https://www.linkedin.com/in/z-w/", "author_name": "Sam Example",
                    "stage": "connected", "note": "connect only"}
    _write_actions(cfg, [commented, connect_only, commented, {"kind": "manual", "author_name": "no url"}])
    assert inbox.apply_actions(engine) == 3                                        # the malformed one is ignored
    rows = engine.store.db.execute(
        "SELECT c.status, c.stage, c.note, p.lane_id FROM cards c JOIN posts p ON p.id=c.post_id "
        "WHERE p.lane_id='manual' ORDER BY c.id").fetchall()
    assert [(r["status"], r["stage"]) for r in rows] == [("posted", "connected"), ("skipped", "connected")]
    assert len(rows) == 2                                                          # the replayed duplicate made no 3rd card
    snap = snapshot(cfg, engine.store)
    assert any(c["lane"] == "manual" and c["stage"] == "connected" for c in snap["cards"])


def test_nothing_lived_to_add_never_becomes_a_card(cfg):
    # a fresh, busy post from a perfect-fit buyer still isn't a card if he has nothing he has lived to add
    from datetime import datetime, timedelta, timezone
    from engine.models import Post
    from engine.scoring import priority
    p = Post(id="1", url="u", text="t", author_name="A B", author_headline="Clinic owner", author_url="a",
             author_type="profile", posted_at=datetime.now(timezone.utc) - timedelta(hours=1),
             likes=80, comments=5, shares=0, lane_id=cfg.lanes[0].id)
    score = {"sensitive": False, "icp_fit": 9, "author_type": "buyer"}
    assert priority(p, cfg.lanes[0], dict(score, value_room=3)) == 0.0
    assert priority(p, cfg.lanes[0], dict(score, value_room=7)) > 6
