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
    assert "Option 1" in out and "Connection note" in out

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
