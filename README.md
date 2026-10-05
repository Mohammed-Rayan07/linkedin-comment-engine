# Raynix LinkedIn Comment Engine

Finds LinkedIn posts worth commenting on, from your buyers and from creators they follow, and drafts
expert comments grounded only in work you've actually done. Drafts arrive in Telegram. You edit and
post them yourself.

**It never touches your LinkedIn account.** Scraping runs on Apify's servers without your login or
cookies, and nothing is posted automatically. Every word goes out under your name, so a human (you)
stays in the loop.

```
 Apify (no login)        rules              Claude                Claude + truth gate        Telegram
 ┌─────────────┐   ┌──────────────┐   ┌───────────────┐   ┌──────────────────────┐   ┌──────────────┐
 │ buyer lanes │   │ vendor auth. │   │ buyer? fit?   │   │ 3 options, 3 angles  │   │ card + tap-  │
 │ creators    │──▶│ non-English  │──▶│ value room?   │──▶│ numbers must be in   │──▶│ to-copy text │
 │ prospects   │   │ old/crowded  │   │ priority 0-10 │   │ your proof bank      │   │ ✅ ⏭ 🔁      │
 └─────────────┘   └──────────────┘   └───────────────┘   └──────────────────────┘   └──────────────┘
```

## Setup (about 15 minutes)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Fill in `.env`:

1. **GEMINI_API_KEY**: free, from aistudio.google.com > Get API key. The engine uses Gemini 3.8 Flash by default; to use Claude instead, set `models.provider: claude` and add `ANTHROPIC_API_KEY`
2. **APIFY_TOKEN**: from console.apify.com > Settings > Integrations. The default 80 posts a day costs about $4.80 a month, which fits inside the free plan's $5 monthly credit.
3. **Telegram**: message @BotFather, send `/newbot`, and paste the token into `TELEGRAM_BOT_TOKEN`. Then open your new bot, send it `hi`, and run:
   ```bash
   python -m engine telegram-setup
   ```
   Paste the printed `TELEGRAM_CHAT_ID` into `.env`.

Try it with no keys first. This uses fixture posts and a fake LLM:

```bash
python -m engine run --mock
```

## Before the first real run (important)

1. **Read `config/expert_profile.yaml` line by line.** This is the truth gate: the writer may only use these facts, and every number in a comment must appear here or in the post being replied to. Fix anything that's wrong. When you land a real client result, add it there.
2. **Run the yield test.** It costs about $0.20 of Apify credit and shows which lanes actually surface buyers rather than other AI agencies:
   ```bash
   python -m engine yield-test
   ```
   Disable lanes in `config/lanes.yaml` that come back mostly vendors.
3. **Do a single-lane first run** and check the cards in Telegram before turning everything on:
   ```bash
   python -m engine run --lanes clinics
   ```
4. **Add creators and dream prospects** to the `creators` and `prospects` lanes in `config/lanes.yaml`, then set `enabled: true`. Pick creators your buyers follow, not AI influencers. After a few days, `python -m engine suggest-creators` lists high-engagement authors the engine keeps running into.

## Daily use

**Start here: [HOW_TO_POST.md](HOW_TO_POST.md)** has the step-by-step for turning a card into a posted comment.

### Dashboard (laptop and phone)

**https://mohammed-rayan07.github.io/comment-crm/** (or `python -m engine dashboard`)

- **▶ Post now**: one card at a time, best first. Open the post, copy a comment (edit it in place
  first if you like), tap **I posted this**. The next card opens.
- **Pipeline**: a CRM board. To post → Commented → Connection sent → They replied → In DMs → Call
  booked → Client. Drag cards between columns or click one to move it and add notes.
- **Stats**: comments per day, the funnel from card to call, which search lanes convert, your
  follower count, and a box for the numbers only you can see (impressions, profile views).

How it works: the page is public code with no data in it. On each device you paste a GitHub key
that can only reach this repo (the page walks you through it). It reads `state/dashboard.json`,
which every run rewrites, and saves your clicks as lines in `state/actions.jsonl`, which every run
applies through the same code as the Telegram buttons. The database itself is only ever written by
the scheduled run. Clicks show up straight away on the dashboard and reach the database and Telegram at the
next run, or right away if you press **Run now**.

Page source: `dashboard/index.html`. To update the live page, copy it to the
`Mohammed-Rayan07/comment-crm` repo (`index.html`) and push.

**Your own LinkedIn stats** (`my_stats` in `config/settings.yaml`, off by default): every 2 days
it reads your public comments (likes and replies on each) and your follower count. It also
marks a card posted when your comment appears on its post, and learns your exact final wording. It costs about
$1 a month, taken from the same daily Apify cap as post scraping. Impressions and profile views
need your login, so the engine never reads them; type them into the Stats tab instead.

```bash
python -m engine run      # one pass: fetch, score, draft, send cards
python -m engine bot      # local mode only: stay online so button taps apply instantly
python -m engine stats    # last 7 days, including $ spent
python -m engine check "your own comment text"   # run the guard on something you wrote
```

In Telegram, each card shows the post, why it was picked, three comment options with different
angles (tap the text to copy), and a connection note for buyer posts. After you post, tap
**✅ Posted N** (it logs which angle you used), or tap **⏭ Skip** or **🔁 New angles**. Send `/stats`
to the bot at any time.

**How it learns your voice.** Every comment you mark ✅ Posted becomes an example for future drafts.
When you edit a draft before posting, **reply to the card with your final version**. That's the
strongest signal, and edited examples are weighted first. After a couple of weeks the drafts should read
like you.

Comment as early as you can. The first 60–90 minutes after a post goes up get most of the reach,
which is why the engine favours fresh posts.

## Run it on a schedule (laptop off)

`.github/workflows/engine.yml` runs the engine three times a day (08:00, 13:00, 18:00 Riyadh).

1. Push this folder to a **private** GitHub repo.
2. Fill in `.env`, then push its values as repo secrets in one command:
   ```bash
   gh secret set -f .env
   ```
3. Run it once from the Actions tab with "Run workflow".

Button taps are applied at the start of the next scheduled run.

**The schedule is the only runner.** The database (`data/engine.db`) lives in this repo and every
scheduled run commits it back, so there's one copy of your cards. Don't run `run`, `fill` or `bot`
locally while the schedule is on. If you ever do, `git pull` first and push right after.

## Costs

| Item | Monthly |
|---|---|
| Apify (80 posts/day cap) | ~$4.80, covered by the free plan's $5/month |
| Gemini 3.8 Flash (free tier) | $0. It's rate-limited, so the engine paces its calls and falls back to Gemini 3.7 Flash if the daily quota runs out. On the free tier, Google may use the prompts (public posts + your proof bank) to improve its products. |
| GitHub Actions (private repo) | free (~300 of 2,000 free minutes) |

If you switch to Claude (`models.provider: claude`), `/stats` tracks real spend. `drafting_effort: medium` is the biggest cost lever.

## Files

| Path | What it is |
|---|---|
| `config/expert_profile.yaml` | Your proof bank: the only facts the writer may use |
| `config/voice.md` | How you sound, banned phrases, example comments |
| `config/lanes.yaml` | Where posts come from: buyer searches, creators, prospects |
| `config/settings.yaml` | Models, budgets, filters, comment length |
| `engine/guard.py` | Truth gate + anti-AI-slop checks |
| `engine/pipeline.py` | The run loop |
