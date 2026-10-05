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

1. **ANTHROPIC_API_KEY**: from console.anthropic.com
2. **APIFY_TOKEN**: from console.apify.com > Settings > Integrations. The free plan's $5 credit renews monthly; the default 25 posts/day uses about $1.50 of it.
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

**Pick one mode: local or scheduled. Don't run both.** The scheduled runs keep their own database
in the Actions cache. A local `bot` or `run` would use a different database, and it would consume the
same Telegram button taps.

## Costs

| Item | Monthly |
|---|---|
| Apify (25 posts/day cap) | ~$1.50, covered by the free plan's $5/month |
| Claude (scoring + drafting ~15–20 cards/day on Opus 5.5) | **unverified estimate: ~$20–60.** Check `/stats` after day one, since it tracks real spend. |
| GitHub Actions (private repo) | free (~300 of 2,000 free minutes) |

If Claude costs come in high, the levers in `config/settings.yaml` are:
- `drafting_effort: medium` (the biggest lever, since thinking tokens bill as output)
- `scoring: claude-haiku-4-5` (scoring is simple classification)
- a lower `max_cards_per_day`

## Files

| Path | What it is |
|---|---|
| `config/expert_profile.yaml` | Your proof bank: the only facts the writer may use |
| `config/voice.md` | How you sound, banned phrases, example comments |
| `config/lanes.yaml` | Where posts come from: buyer searches, creators, prospects |
| `config/settings.yaml` | Models, budgets, filters, comment length |
| `engine/guard.py` | Truth gate + anti-AI-slop checks |
| `engine/pipeline.py` | The run loop |
