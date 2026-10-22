# LinkedIn Brain: Mohammed Rayan / Raynix AI

> One file that holds everything about the LinkedIn effort: who he is, the live profile section by section, every post and its numbers, what we built, what we decided and why, the goals, the rules, and what's pending.
> Built 12 Oct 2026, last updated **16 Oct 2026 (evening)**. **Starting a fresh chat? Read "START HERE (16 Oct)" directly below section 0.** It overrides everything older. The 15 Oct status and sections 1-9 are kept as history, with "superseded" markers where facts changed. Re-check anything marked [verify].
> Companion files: `FIRST_CLIENTS_PLAYBOOK.md` (the offer, current terms, scripts, sprint), `PROFILE_VERSIONS.md` (exact live profile text V3/V3.1 and older versions), `CONTENT_PLAYBOOK.md` (research, calendar, full post texts), `PERSONAL_BRAND.md` (competitor and niche research), `config/expert_profile.yaml` (the truth gate), `config/voice.md`, `HOW_TO_POST.md`. Website code: `..\raynix-website` (separate repo).

---

## 0. Read this first (the 60-second version)

- **Who:** Mohammed Rayan, B.Tech AI student at NITK Surathkal (2025-2029), based in Riyadh, founder of **Raynix AI, an AI consulting & engineering company**. Pre-first-client. Wants **(A)** paying clients (first 3 through the Founding Partner Program) and **(B)** AI/ML internships (secondary).
- **Lane (since 15 Oct):** real estate teams and clinics. Their leads become booked viewings and appointments through one connected system: capture, instant AI reply, AI sales follow-up, booking, CRM, owner alerts, reviews and reactivation. Never pitched as a basic chatbot or receptionist vendor.
- **Voice:** builder / engineer's build log, plain owner language, "I" never "we". Says what it does, what broke, and what it's never allowed to decide. Casual in chat ("bro").
- **Positioning line:** *"The LLM talks, the code decides."* Method: audit first, build second.
- **Strongest proof:**
  - 2nd of 135 teams at the L&T Finance challenge (18.47% MAPE, lowest of all)
  - Advocall (24h hackathon build)
  - MedLog Suite (8 bilingual agents, open code, synthetic data)
  - Ayah Archive, a **faceless digital brand**: 1.1M+ views in 30 days, 5,000+ followers, 500+ purchases, 7,500+ AED (₹2L+) of Meta ads
- **Biggest lever discovered:** the L&T post (835 impressions by 15 Oct) broke out because **a judge he genuinely tagged (Dr. Kamlesh Kumar, L&T Finance) reposted it and NITK clubs shared it**. Genuine tags plus reposts beat his own network. Pitch-style "Comment X" posts went out before the 5 Oct relaunch, on a tiny account. They are **untested since the relaunch, not dead** (see `feedback-timeline-before-verdicts`).
- **The funnel now:** post or comment → profile (headline, banner, Featured) → **raynixai.com/founding** → book a free 20-minute AI Lead Audit (Cal) or WhatsApp.
- **Hard rules:** the consolidated list is in START HERE, item 9.

---

## START HERE (16 Oct 2026): everything live, and the handoff for the content chat

> **Content strategy (17 Oct, v2 final):** `CONTENT_STRATEGY.md` is the master strategy (funnel, MedLog series P3-P8 + outro, image prompt system, IST times, 30-day calendar 18 Oct to 13 Nov). It supersedes `CONTENT_PLAN_30D.md`.
>
> **STANDING RULE (Rayan, 17 Oct): every LinkedIn post Claude writes runs the pipeline in `CONTENT_STRATEGY.md` section 11 automatically, without being asked:** load this brain + `config/linkedin-voice-profile.md` + `config/linkedin-story-bank.md` → `linkedin-skills:linkedin-post-writer` → `linkedin-skills:linkedin-humanizer --mode audit` → `humanizer:humanizer` → truth gate → visual (GPT Image whiteboard prompt / carousel / real screenshot) → show Rayan with the IST time → post only after his yes. Never use the plugin's Publora or Apify features. Owner posts must talk straight to the ICP ("your problem is costing you X, here's how I'd approach it"), not generic education. It overrides item 7 (cadence) below and the content parts of `CONTENT_PLAYBOOK.md`. 16 Oct numbers: 1,789 impressions/28d, 791/7d, 118 followers, 114 connections, 49 profile viewers/90d, 1 search appearance, **0 comments on own posts in 28 days**; founding post 61 impressions, 0 reactions at 9h.

### 1. Where things stand (evening, 16 Oct)
- Profile V3/V3.1, the new banner, the website, the Founding Partner offer (page, PDF, deck), the Featured section and the founding announcement post are **all live**.
- **No client yet, and no calls yet.**
- Website work is paused by Rayan's call ("stop editing the website… focus on the client now"). From here the work is content, comments, conversations and DMs.

### 2. What's live (assets)
| Asset | Where | Notes |
|---|---|---|
| Profile V3 + V3.1 | LinkedIn | Exact text and revert history are in `PROFILE_VERSIONS.md`. Headline: "I build AI systems that turn real estate & clinic leads into booked viewings and appointments \| AI consulting & engineering \| …". |
| Banner | LinkedIn | `assets/linkedin-banner.png` (3168x792) with its HTML source. "AI systems that book your leads / and run your operations." with his photo. |
| Website | https://raynixai.com | Next.js on Vercel, code in `..\raynix-website`. Homepage hero has a peach link to /founding ("Founding Partner Program: pay only when it works · 3 spots"). Lighthouse desktop 100 across the board. Google Search Console domain is verified via GoDaddy TXT. |
| Offer page | https://raynixai.com/founding | Covers the guarantee, system, what's included, pricing, timeline, safety rules, who it's for, the founder, 8 FAQs and repeated Cal + WhatsApp buttons. Has its own OG image ("Your AI lead system. Pay only when it works."). |
| Offer PDF (public) | https://raynixai.com/raynix-ai-founding-partner-program.pdf | 15 slides, 3.7 MB. Use this or /founding in DMs, because the deck artifact below is private. |
| Editable deck | https://claude.ai/artifact/QkxoGowcrstLCPDTU4Sqtp | Slides artifact. Re-export the PDF and replace `public/` in the website if it changes. |
| Booking | https://cal.com/mohammed-rayan-p9qiwg/ai-audit | Free 20-minute audit. **Rayan still has to rename the event to "Free AI Lead Audit"**, so it matches the page and deck. |
| WhatsApp | the `wa.me` link in `raynix-website/lib/site.ts` | Chat only, no calls. **Never write the number as text** in any post, comment or image. |
| Email | rayan@raynixai.com | Microsoft 365. Never touch the MX/SPF/DMARC records. |
| LinkedIn Featured | profile | Order: (1) link card "Founding Partner Program: pay only when it works (3 spots)" → /founding, with the custom OG thumbnail (Post Inspector refreshed); (2) the founding post; (3) L&T 2nd of 135; (4) MedLog launch; (5) Advocall. |
| Contact info | profile | Website field set to raynixai.com/founding. Whether ayaharchive.shop is still listed was not checked [verify]. The custom profile button and the intro website link are Premium-only, so neither was used and nothing was bought. |

### 3. The offer (current terms; the full version is in `FIRST_CLIENTS_PLAYBOOK.md` → "CURRENT TERMS")
> **v2.1, live 22 Oct 2026.** Rayan approved it ("do it all"). It replaces the 16 Oct v1 terms (4,500 + 1,500 a month, a 12-month lock, "free until").

- **"Live in 5 days. Proven on your real leads in 14. Pay only after the proof."** 3 founding spots, onboarded one at a time.
- **Free:** the audit, the Leak Map (theirs to keep), the build, and the 14-day live proof.
- **Setup is 1,500 AED/SAR, split in two:**
  - **750** when the speed and follow-up targets pass (around day 12)
  - **750** when the booking target passes (around day 19)
- **Care plan:** 750 a month from payment 2. Month-to-month, 7 days' notice to cancel, price locked while they stay.
- **Outside the GCC:** about USD 400 + USD 200 a month.
- **After the founding spots:** 6,000 setup (50% upfront) + 1,500 a month. Rayan must actually charge this, or it gets removed from the page.
- **Targets:**
  - **T1:** 95% of first replies in under 60 seconds, measured over the first 7 days.
  - **T2:** follow-up within WhatsApp's rules, plus every lead logged.
  - **T3:** a booking number set on the call from their own baseline.
- **If a target is missed:**
  - T1 or T2: fixed free, nothing due.
  - T3: one free 14-day extension, then the client continues or walks away and keeps the system.
  - **Payment 1 isn't refunded.** This is stated on the page.
- **Software** is on the client's accounts, usually under USD 100 a month, confirmed before the build.
- **In return:** case-study permission. A testimonial and intros only if they're happy. **Never a Google review.**
- **Full mechanics and the agreement outline:** `FIRST_CLIENTS_PLAYBOOK.md` → CURRENT TERMS v2.1 and section 8.
- **Not updated yet:**
  - The 15-slide deck/PDF still shows v1. It's unlinked from the page, so don't send it.
  - **Fixed 22 Oct:**
    - The founding post text now matches v2.1 ("You pay nothing until it proves itself on your real leads…", "Miss a target, and I fix it free.") and points to /founding for the current pricing.
    - The Featured link card is now "Founding Partner Program: live in 5 days, pay after proof (3 spots)".
    - Post Inspector was re-run on /founding.
  - **Still v1:** the post's 15-page carousel PDF, which can't be swapped without reposting.
- **The "after the founding spots" prices are indicative.** Rayan's real quote depends on the client type, the services and the volume, and the page says so under the price.
- In content, never quote a number that isn't on /founding, and never invent "was X, now Y" anchor prices.
- **Scarcity has to stay true.** "3 spots" only drops when a spot is actually signed.
- The free-build wording in the playbook's older sections (including its draft "build your AI lead system free" post) is **superseded. Don't reuse it.**

### 4. Posts live (8)
| # | Post | Impressions (last pull 15 Oct) | Notes |
|---|---|---|---|
| 1 | L&T Finance 2nd of 135 | 835 | Breakout, driven by the judge's repost and NITK clubs. Its audience is Mumbai / L&T, not the ICP. |
| 2 | Re-introduction ("everything I've shipped, and what broke") | 151 | |
| 3 | Advocall | 128 | |
| 4 | MedLog complaint desk (agent P1) | 118 | |
| 5 | "If an AI agent has never said I don't know" | 115 | |
| 6 | MedLog launch ("four hours with a logistics leader") | 85 | Publicly promised a post on every agent. |
| 7 | MedLog three-way match (agent P2) | 20 at about 12h | |
| 8 | **Founding Partner Program announcement** (16 Oct, about 10:30 AM Riyadh, Friday) | not pulled yet | Document post with the 15-page deck as a carousel. https://www.linkedin.com/feed/update/urn:li:activity:7516764913470537729/ |

**The founding post's first comment:** "Full offer, pricing and the free 20-minute AI Lead Audit booking: https://raynixai.com/founding"

**Founding post text (as published, verified exact):**
```
I'm opening 3 Founding Partner spots at Raynix AI.

The offer, plainly:

I build your AI lead system. Every enquiry from your ads, portals, website or WhatsApp gets a reply in seconds, in Arabic or English. It qualifies the lead, follows up for days, and books the viewing or appointment straight into your calendar. You get an alert the moment a serious lead shows up.

On day one we agree your targets in writing: reply speed, follow-up coverage and booked appointments, measured against your current numbers.

You pay nothing until the system hits them.
If it doesn't, I keep working for free until it does.

It runs on your own accounts, so it stays yours either way.

Why this deal? I'm choosing three businesses to build my flagship case studies with. I'd rather earn proof than fake it.

Who it's for: real estate brokerages and teams, and clinics, in the UAE, KSA or the UK that already pay for leads and get 50+ enquiries a month.

The full offer is in the 15 pages below: the system, the guarantee, pricing and the timeline.

The link to book a free 20-minute AI Lead Audit is in the first comment.
```
The 15 Oct analytics baseline is in the STATUS UPDATE 15 OCT section below: 1,571 impressions over 28 days, 103 connections, 107 followers, 1 search appearance a week. Pull fresh numbers before judging anything, and only compare posts from after the 5 Oct relaunch.

### 5. Content queue (unposted; full paste-ready texts in `CONTENT_PLAYBOOK.md` section 11)
- **MedLog series: an open public promise** (the launch said every agent would get a post). Done: P1 complaint desk and P2 three-way match. Still owed: P3 reports, P4 driver check-in ("a driver replied 👍, my agent refused to guess"; text is CONTENT_PLAYBOOK Post 2), P5 days-of-cover / stock-out, P6 live status, P7 and P8. Check exact agent names and screenshots in `..\raynix-medlog-suite` (`docs/images/`).
- **"3 of my 8 AI agents don't use AI"** (CONTENT_PLAYBOOK Post 5; P5/P7/P8 use no LLM).
- **Carousel: "5 ML lessons no lecture taught me"** (Post 3). Needs his real loss-divergence plot and the `[fill in]` learning rate.
- **Ayah Archive: faceless brand, 1.1M views in 30 days** (Post 4). Needs a real Instagram insights screenshot with buyer names blurred. Ad spend is **7,500+ AED (₹2L+)**. Never "9,000+ AED at 3x", and never "₹100K".
- **The truth-gate / comment-engine post** (Post 6). Never mention scraping, Apify or the private repo.
- **Advocall "4 things that broke in 24 hours"** carousel, and a "timely take" within 48h of the next big AI release.
- **Buyer-facing lead-leak posts** for the real estate / clinic lane (reply speed, after-hours enquiries, follow-up gaps). These are **untested since the relaunch**, so test them. They are the posts that most naturally lead to /founding.

### 6. How content should feed the offer
- **Featured does the selling.** Most posts (build logs, lessons) need no link and no pitch. Profile visitors land on the /founding card first.
- Put **/founding in the first comment only on offer- or lead-leak-related posts**, never in the post body.
- A soft offer reminder about once a week at most, and only with something true and new (for example a spot taken, or what the audit found, with permission). Never fake urgency.
- Every post is still 1 idea, a hook under about 12 words, 900-1,300 characters, a real screenshot or photo over AI art, 0-3 hashtags, and a specific closing question (no "Thoughts?", no "Comment X" bait).
- Tag only people genuinely in the story (2-5). **Never tag the MedLog interviewee or his employer.**
- DMs send **raynixai.com/founding** (not the PDF, and not the private artifact).

### 7. Cadence
- **1 post a day, never 2.** The founding post went out Fri 16 Oct at about 10:30, so nothing else posts on 16 Oct.
- Give the founding post runway. The earliest next slot is Sat 17 Oct at 9:00 AM Riyadh. **Sun 18 Oct at 9:00, the first day of the GCC work week, is the stronger slot.** The content chat decides with Rayan.
- Default slot 9:00 AM Riyadh (11:30 IST). Still to test: a 5 PM Riyadh slot.
- Reply to every comment within the first hour. Comment partners are the first-hour audience.

### 8. How Claude publishes a post (only after Rayan's explicit go for THAT post)
**Approval:** the 16 Oct green light covered the Featured section and the founding post only. **Every new post, comment or DM needs Rayan's explicit yes in chat.** Draft first, show it, then publish.

**Browser setup**
- Use Claude in Chrome in **its own tab group**, logged in as him.
- Never touch another session's tabs (one Claude session works on x.com). Close your own tabs when done.
- If screenshots time out or the viewport is 0x0 (the window is minimized), close the group's tabs and recreate the group with `tabs_context_mcp` createIfEmpty.

**Writing the text**
- LinkedIn text boxes **drop typed characters**. Set text with `form_input` and nudge it (End, space, Backspace).
- Then **verify the saved text character by character** before posting.

**Attaching an image or PDF**
- "Choose file" has no static input. Patch `HTMLInputElement.prototype.click` to capture the dynamic input, append it visibly, find its ref, then use `file_upload`.
- **Document posts:** upload the PDF and give it a title.

**Links**
- Put the link in the **first comment**, straight after publishing.
- Before adding any link card (Featured), run https://www.linkedin.com/post-inspector/inspect/<url> so the preview image is fresh.

**Safety**
- Decline Premium / boost upsells.
- If LinkedIn asks for a password or re-login, **stop and tell Rayan**. Never enter credentials.

**After posting**
- Log the post here (section 4 table).
- Add a `manual` line to the CRM if useful.
- Commit and push (`git pull` first, because CI commits constantly).

### 9. Hard rules (consolidated, all still in force)
**Posting and accounts**
- Never auto-post with the engine, and never use his LinkedIn cookie for automation.
- Never enter passwords or tokens. Never print .env secrets.
- The engine repo stays private.
- Don't sign into Cal.com or Lovable for him. Don't buy anything.

**Truth gate**
- No client results, testimonials or revenue (none exist).
- "Built", never "deployed for".
- MedLog is always "open code, synthetic data". Never name, tag or identify the operator, the interviewee, his employer or his family.
- Ayah Archive is a **faceless digital brand**, never a "product".
- Arabic: the *agents* are bilingual. He is not fluent.
- No scraping or Apify talk in public.

**Voice and wording**
- Use "I" or "Raynix AI", never "we".
- No review-gating language, and never ask for Google reviews as payment.
- Label illustrative visuals "Example".
- No em dashes in comments.
- Calls are in English only.

**Outreach**
- DMs are drafts until Rayan says yes, every time.

### 10. Open items for Rayan (he does these himself)
1. Reply to every comment on the founding post (it's Friday, the GCC weekend, so growth may be slower).
2. Rename the Cal event to "Free AI Lead Audit" and add booking questions.
3. Confirm or change the prices. If they change, update the page, the deck and the PDF together.
4. Say yes to the warm-list DMs with the /founding link (Bilal and Apoorv first; drafts in `FIRST_CLIENTS_PLAYBOOK.md` section 7, swapping in the current terms).
5. Search Console: finish the remaining steps in the property (status unconfirmed) [verify].
6. Get ID-verified ("Verify in 2 minutes") and ask for 2-3 recommendations.
7. Fix the CRM stages (sweep connections and replies) before choosing DM targets.
8. The 14-day client sprint runs 17-30 Oct (`FIRST_CLIENTS_PLAYBOOK.md` section 9). The target by 31 Oct is 5 real ICP conversations and 1 audit call.

## STATUS UPDATE 15 OCT 2026 (history: the analytics baseline, CRM state and warm list are still valid; anything that conflicts with START HERE is superseded)

### Where things stand
- **Connections 103** (67 on 10 Oct; 40 ten days ago), **followers 107** (71 on 10 Oct). Mostly real ICP people, not students: follower audience is 34% founders, 20% CXO, 30% at 2-10 person firms, 10% Dubai.
- **Comments:** LinkedIn counts 85 this week (9-15 Oct); the CRM has **111 posted comments** in total.
- **Still no conversations that have become calls, and no client.** The bottleneck is now replies and DMs, not reach.

### LinkedIn analytics, pulled live 15 Oct (baseline for the next check)
| Metric | 15 Oct | Note |
|---|---|---|
| Impressions, 28 days | 1,571 | +2,809% vs a tiny prior 28 days; 60% out-of-network, 508 members reached |
| Impressions, 7 days | 635 | +29% vs prior 7 days |
| Engagement, 28 days | 28 | 25 reactions, 2 comments, 1 save, 0 reposts, 0 sends |
| Profile viewers, 90 days | 44 | low for 111 comments; 6 from IET NITK, 4 from the NITK debating society, 2 from L&T Finance; recent viewers include a Dubai real-estate executive director, a Dubai marketing founder and a Dubai advertising founder |
| Search appearances, 7 days | 1 | was 9 on 10 Oct; profile is almost invisible in search |

### Posts live (7), impressions on 15 Oct
| Post | Impressions | Reactions |
|---|---|---|
| L&T Finance 2nd of 135 | **835** | 15 (carried by the judge's repost and NITK clubs; its viewers are 25% Mumbai, 20% L&T Finance, so a different audience from the ICP) |
| Re-introduction ("everything I've shipped, and what broke") | 151 | 2 |
| Advocall | 128 | 5 |
| MedLog complaint desk (agent 1) | 118 | 2 |
| "If an AI agent has never said I don't know" | 115 | 3 |
| MedLog launch ("four hours with a logistics leader") | 85 | 1 |
| MedLog three-way match (about 12h old) | 20 so far | 1 |

Read: the build posts sit at about 85-150 each with 1-3 reactions. The L&T post is the only breakout and it came from distribution, not content alone. The Week 1 calendar was replaced by the MedLog series; the Tue carousel, Wed Ayah insights post, Thu P5 post and Fri truth-gate post are still unposted. Post 1 (re-intro) is live.

### What was done 12-15 Oct
- **12 Oct: hand-done outreach in Chrome** (own tab group, never touching the other Claude session on x.com): 10 comments and 12 connection requests on ICP-lane people, logged in the CRM through a new `manual` action (`engine/inbox.py`, tested, commits ac35069 and ea4e4bd). 13 entries.
- **Replied to all 4 comment replies found in notifications** (notifications only reach back about 4 hours, so older replies could not be found): Fawad Hashmi, Muhammad Bilal, Apoorv Agarwal, Albin M Jose. Each reply ends with a question.
- **Engine run failure fixed (run 38622563671, 14 Oct 19:18 UTC):** the final "Save state" git push lost a race with the rapid dashboard "posted" commits. Fix: retry loop with rebase abort and backoff in `.github/workflows/engine.yml` (commit 9adf9a0). Verification run 38623119677 succeeded (16 taps applied). Nothing was lost.
- **15 Oct: full analytics review** (the numbers above).

### CRM state (state/dashboard.json, 15 Oct 14:50 UTC)
129 cards: **111 posted** (99 still stage "commented", 11 "connected", 1 "replied"), 14 sent and not yet posted, 4 skipped (3 of them connection-only). Stages are badly out of date: 103 connections and at least 4 real replies exist, but only 12 are marked connected and 1 replied. Fix this before using the Pipeline to choose DM targets. Apify use is $1.54 of the $5 cap.

### Warm lead list (DM priority order; all got a comment and a connection request on 12 Oct unless noted)
| Person | Who | Lane | Status and DM angle |
|---|---|---|---|
| **Punya Mehra** | Founder, Aurah Real Estate, Dubai | BUYER | Highest priority once accepted. Ask: goal question first or listings first in the first WhatsApp message? |
| **Muhammad Bilal** | Meta Ads and lead gen for Dubai real estate | Channel partner (many brokerage clients) | **Replied.** He corrected me: the 186 were WhatsApp conversations started, not all answered in minutes. I owned it and asked what share got a reply within 5 minutes and whether that matches viewings. Best partner target. |
| **Fawad Hashmi** | Aeon & Trisl (Dubai / Abu Dhabi) | BUYER-adjacent | **Replied.** Said expansion is about relationships and developer access. I conceded and asked whether Abu Dhabi enquiries run through the same team as Dubai. |
| **Apoorv Agarwal** | Founder, AVmedia (Dubai), patient acquisition for aesthetic clinics | Channel (clinics) | **Replied** briefly. I asked for the slowest after-hours reply he has seen from a clinic running ads, and invited results from the 11 PM test. |
| **Albin M Jose** | Data scientist / AI automation engineer (Dubai) | Builder peer | **Replied.** I said Meta's test number lets him try WhatsApp before approval and asked whether his 35 test cases are split by intent. |
| Anton Neugebauer | Private-practice consultant (Miami) | Channel | Commented. Angle: time from enquiry to first human reply, split by business hours. |
| Pankaj Kumar | Founder, CoBroker (broker CRM, Dubai) | Peer / integration partner | Commented. Ask: does a new WhatsApp enquiry create the lead automatically? |
| Athar Ammar | Agency for health and real estate (4.9k followers) | Channel | Commented. Ask: do clients assign the owner of the first 4 minutes by rota? |
| Muhammad Faiyaz Uddin Ahmed | LocalVisi Digital, local SEO for US dentists (Doha) | Channel | Commented. Angle: how many of the 521 Google calls were answered. |
| Elena Herre | Founder, PrimeVision Automation (Dubai real-estate follow-up) | Peer, not a buyer | Commented. Same-space builder. |
| Shivam Luthra | Founder, Reva AI | Peer (already 1st-degree) | Commented, no request needed. |
| Hassan Ahmed | MD, Dar Al Safwah Real Estate (Sharjah) | BUYER | Connection request only. Comment on his next post. |
| Mohammed Faisal | Founder, AssetzVault (real estate advisory) | BUYER | Connection request only; mutual connection Raghav. |
| Himanshu Malik | Co-founder and COO, Wytewall (NITK) | NITK network | Connection request only; possible warm intro or mentor. |

### Profile repositioned (15 Oct, evening): V3 is live
Headline, About, Raynix AI Experience, Services and the Ayah Archive project were rewritten. Raynix AI is now an **AI consulting & engineering company**, and the headline lane is **real estate & clinics** (leads into booked viewings and appointments). About and Experience sell the full connected system (capture, instant reply, AI sales follow-up, booking, CRM/Drive/owner alerts, reviews and reactivation) with an audit-first method. Exact live text and the full V1/V2 history for reverting are in `PROFILE_VERSIONS.md`. The headline/About/Experience text in section 2 below is V1 (historical). **All three follow-ups are done:** the V3.1 banner went live 15 Oct; ad spend was confirmed at 7,500+ AED (₹2L+), so "9,000+ AED at 3x" is never used; the Featured section was done 16 Oct.

### Profile health findings (15 Oct)
- **Search visibility is the biggest gap** (1 appearance a week): headline and About lack buyer search words ("WhatsApp", "AI receptionist", "real estate", "clinics", "lead response"). Headline changes are Rayan's call.
- ~~About "1.1M+ monthly views", Projects #4 "digital product"~~ Fixed in V3: About and the project now say "faceless digital brand" and "1.1M+ views in 30 days".
- **"Verify in 2 minutes" is unclaimed** (only Rayan can do it).
- ~~Featured has 3 posts~~ Done 16 Oct: /founding link card, founding post, L&T, MedLog, Advocall.
- Open to Work is on, recruiters only (fine).
- The banner pitches a free ops audit while the headline is internship-friendly: a deliberate dual message, keep an eye on it.

### Next steps (priority order) and the plan for the outreach chat
1. **Sweep recent connections and sync the CRM:** mark who accepted the 12 Oct requests, who replied, who is ICP.
2. **DM the warm list**, starting with Punya Mehra, Muhammad Bilal, Fawad Hashmi, Apoorv Agarwal. A DM is a question about THEM, never a pitch, sent within 24h of acceptance. Draft each from the table above and **ask Rayan for an explicit yes before sending any DM** (sending messages for him needs approval each time).
3. **Fix search visibility and the profile items above.**
4. **Use comment partners as the first-hour audience** for posts; tag only people genuinely in the story; reply to every comment within the hour.
5. **Measure conversations, not impressions.** Target by 31 Oct: 5 real two-way conversations with ICP people and 1 call. Re-pull analytics weekly and compare with the 15 Oct table.

### Rules for any outreach session (carry over)
- Use Claude in Chrome in its own tab group; never touch another session's tabs (a different Claude session works on x.com). Close tabs when done. The built-in browser may be logged out.
- Before commenting on a post, check for an existing "Mohammed Rayan • You" comment (he also posts engine cards from the dashboard, so duplicates are a real risk).
- Comment voice: no "Great post", no em dashes, no pitch, no "Thoughts?"; end with one specific question. Never state a prospect's claim as a fact about a bigger set than they said (this caused the Bilal correction).
- Truth gate stays: no client results, MedLog = synthetic data and never identify the operator, Ayah Archive = faceless digital brand, no scraping or Apify talk, engine repo private, never auto-post, never use his cookie, never enter passwords or tokens.
- Log hand-done work in the CRM with a `manual` line in `state/actions.jsonl` (needs `post_url`, `author_name`, `stage`, optional `text`, `note`, `author_headline`, `author_url`); it applies on the next engine run (08:00, 13:00, 18:00 Riyadh). Always `git pull` before editing and push after.

---

## 1. Identity and goals

| | |
|---|---|
| Name | Mohammed Rayan (he/him) |
| Location | Riyadh, Saudi Arabia (studies at NITK Surathkal, India) |
| Company | Raynix AI (founder), solo, early stage, **no verified paying-client results** |
| Education | NITK Surathkal, B.Tech Artificial Intelligence, 2025-2029; school: NMEIS Riyadh (94.2%) [not on profile]; JEE Advanced 2025 qualified, top ~2% of ~1.5M |
| Languages | English; **not fluent in Arabic** (the *agents* are bilingual, he is not) |
| Stack | Python, TypeScript/Next.js, C, NumPy/Pandas/Matplotlib, LLM APIs (Claude, Gemini), n8n, Vapi, custom code where no-code breaks |
| GitHub | github.com/Mohammed-Rayan07 |
| LinkedIn | linkedin.com/in/mohammed-rayan-ai (custom URL set 10 Oct; old URL `mohammed-rayan-835118389` may stop working) |
| Website/brand | ayaharchive.shop (Ayah Archive) |

### Goals (in priority order)
1. **First paying client** (fastest path: every engager gets a real conversation within 24h; some become "can you look at ours?"). Lanes: real estate teams (UAE/UK/US/AU), marketing agencies that could resell him, GCC clinics, law firms (test lane).
2. **AI/ML internship** (audience B: AI/ML engineers, founders, recruiters at NITK-adjacent and global teams).
3. Build a recognisable builder brand with one voice that serves both.

### 30-day targets (baseline 10 Oct)
| Metric | 10 Oct | Week 1 (to 17 Oct) | Day 30 |
|---|---|---|---|
| Followers | 71 | 110 | 300 |
| Impressions / week | ~850 | 3,000 | 8,000 |
| Profile viewers / week | 31 | 60 | 150 |
| Conversations (DMs with a reply) | ~3 | 10 | 40 |
| Calls / in-person meetings | 0 | 1 | 5 |
| Paid pilot or internship interview | 0 | 0 | 1 |

---

## 2. The profile, section by section (V1, as verified 10 Oct 2026; HISTORY)
> **Superseded.** Headline, About, Experience, Services, the Ayah Archive project, banner, Featured and contact info changed on 15-16 Oct. The live text is V3/V3.1 in `PROFILE_VERSIONS.md`; Featured and contact info are in START HERE section 2. Education, Honors, Skills and the other Projects are unchanged.

### Headline
`Building AI agents, ML models & software | Multi-agent workflows, voice AI receptionists, CRM automation | NITK | Founder, Raynix AI | Documenting every build`
(Note: LinkedIn overwrote it once when an Experience entry was added; restored. Re-check after any Experience edit.)

### Top card
Riyadh, Saudi Arabia · Raynix AI · 67 connections (71 followers) · not yet ID-verified · Open to Work set to **recruiters only** (no public banner): ML Engineer, AI Engineer, Software Engineer; internship/part-time/full-time; remote/hybrid/on-site; Riyadh and India. "Open to volunteer" box removed.

### Contact info
GitHub (portfolio) `github.com/Mohammed-Rayan07`, website `ayaharchive.shop`.

### About (live text)
```
I like building things that work outside a demo.

I'm a B.Tech Artificial Intelligence student at NITK Surathkal (JEE Advanced, top ~2% of ~1.5M candidates) and the founder of Raynix AI. I build AI agents, machine learning models and the software around them: multi-agent workflows, bilingual (Arabic/English) voice receptionists, CRM automation, and the backends, dashboards and tooling that hold it all together.

RECENT BUILDS

→ MedLog Suite: I spent 4 hours with a logistics leader who has 30 years in Saudi healthcare and mapped where his operation loses time: 23 trucks generating 50-60 supervisor calls a day, 3,000 invoices matched by hand every month, 16 days from purchase request to approved PO. Then I built 8 bilingual AI agents in TypeScript, one per gap, with an operations cockpit, execution traces and human-handoff paths. Open code, synthetic data.

→ Advocall: an AI that waits on hold with customer care and argues your case, citing the exact RBI rules. Built in 24 hours at Build for Billions 2026.

→ Farmer income prediction (ML): 2nd of 135 teams at the L&T Finance challenge, with the lowest MAPE of all teams. I chose the loss function from the metric, found an accounting identity hidden in 47,970 rows, and used geography to score farmers with no credit history.

→ Linear regression from scratch: closed-form, normal-equation and gradient-descent solvers in NumPy, with deliberately induced divergence to study how and why optimization fails.

→ Ayah Archive: a digital product I built, launched and automated end to end (payments, delivery, conversion flow). 1.1M+ monthly views and 500+ purchases.

HOW I THINK ABOUT IT

The LLM talks, the code decides. Anything with real consequences, like a booking, a price or a rule, runs in tested code, not in a prompt. I care about systems that fail predictably rather than silently.

Stack: Python, TypeScript, C · NumPy, Pandas, Matplotlib · LLM APIs (Claude, Gemini) · n8n, Vapi · custom code wherever no-code breaks.

I document every build here.

OPEN TO

AI / ML engineering and software development internships and roles · building systems for businesses that lose time or leads between their tools · collaborating with fellow builders and the NITK community.
```
> **FIX NEEDED:** the Ayah Archive bullet says "a digital product" and "1.1M+ monthly views". Rayan's correction (12 Oct): it is a **faceless digital brand**, never a "product". Change to: "Ayah Archive: a faceless digital brand around Qur'an memorisation. 1.1M+ views in 30 days, 5,000+ followers, 500+ purchases." (Also use "in 30 days", not "monthly".)

### Top skills shown under About
Machine Learning · Python · Agentic AI Development · Large Language Models · Software Development

### Featured (live, 10 Oct)
1. L&T Finance post (2nd of 135) · 2. Advocall post · 3. MedLog post.
**To do:** pin the Sunday re-introduction post at the top; order = re-intro, L&T, MedLog, Advocall.

### Experience
**Raynix AI, Founder (Jan 2026-present).** Live text:
```
I run operational discovery audits, then build the AI systems that close the gaps I find.

Selected work:

→ MedLog Suite: a multi-agent system for medical logistics, built from a four-hour structured discovery audit of a large Saudi healthcare group's supply-chain operation (50-60 outlets, 24/6, SFDA-regulated). 8 bilingual agents cover driver coordination, complaint intake, stock-out escalation, invoice/PO matching and compliance tracking, with rule-based escalation to humans. Open code, synthetic data.

→ AI receptionist systems: bilingual Arabic/English voice agents built for clinics, spas, rental companies and a call centre. I engineered the reliability layer: DB/allowlist matching, phonetic retry on failed name capture, SMS fallback when voice drops.

→ Speed-to-lead & CRM automation: inbound enquiry to qualified response in under 10 seconds, routed by availability and language, booking written straight to the calendar.

Stack: Python, TypeScript, Claude, n8n, Vapi, custom integrations.
```
(Wording was changed on 10 Oct from "deployed for" to "**built for**" so nothing overclaims. Gap: no separate Experience entry for Ayah Archive yet; recommended as its own founder entry.)

### Education
NITK Surathkal, B.Tech Artificial Intelligence, 2025-2029. Coursework: Computer Systems, Programming in C, Calculus, Linear Algebra, Optimization, Python & Data Analysis. 2nd of 135 teams at the L&T Finance Farmer Income Prediction Challenge (IET NITK x Incub8 NITK x L&T Finance). (Duplicate/old NITK entry deleted.)

### Projects (4)
1. **MedLog Suite: medical-logistics AI agent suite** (Oct 2026-present, linked to Founder role). 8-agent bilingual system built from a 4-hour discovery audit; agents for complaint triage, invoice-PO-GRN matching, reporting, driver check-ins, delay detection, stock-out warnings, live delivery status, SFDA pre-audit prep and recall tracking; operations cockpit with traces and KPI events; mock/live adapters and synthetic data; human-handoff paths. TypeScript, open code, synthetic data, not a client deployment.
2. **Advocall: AI agent that waits on hold and argues your case** (2026). Built in 24 hours at Build for Billions 2026, first hackathon. English, Hindi, Kannada and more. Calls the user, calls the company citing RBI T+1, calls back with the outcome; live dashboard. Rights engine = tested TypeScript, not a prompt. Guardrails: never asks for OTP/PIN/CVV, says it's an AI, pushes back twice then escalates, nothing filed without the customer's yes.
3. **Linear Regression from Scratch: optimization dynamics and failure modes.** Closed-form, normal-equation and gradient-descent solutions in NumPy; learning-rate sensitivity, initialisation, convergence and divergence; deliberately induced instability; loss tracking and visualisation. Repo: github.com/Mohammed-Rayan07/linear-regression-from-scratch (public; the link card could not be attached earlier).
4. **Ayah Archive: digital product and automated distribution system.** Qur'an memorisation brand; 1.1M+ views in 30 days (organic Instagram), 5,000+ followers, 500+ purchases, ₹100K+ Meta ad spend, automated payment (Cosmofeed) and delivery; ayaharchive.shop.
> **FIX NEEDED:** project 4's title and first line say "digital product". Retitle to "Ayah Archive: faceless digital brand and automated distribution system" and reword "A digital product focused on..." to "A faceless digital brand around Qur'an memorisation...".

### Honors and awards
- 2nd place of 135 teams, Farmer Income Prediction Challenge (L&T Finance x IET NITK x Incub8 NITK, 2026): lowest MAPE of all teams (18.47%); top 8 presented live to the L&T Finance panel; 43% of farmers had no bureau record; loss chosen from the metric (~4 MAPE points); accounting identity in all 47,970 rows; geography carried over half the predictive power.
- JEE Advanced 2025: qualified, top ~2% of ~1.5M candidates (IIT/JEE).

### Skills
Machine Learning, Python, Large Language Models, TypeScript, NumPy, Pandas, n8n, plus earlier ones (Software Development, Agentic AI, etc.). Removed: LinkedIn Sales Navigator, GoHighLevel (they didn't fit the builder voice).

### Services (page)
Appointment Scheduling · Custom Software Development · Lead Generation · Web Development.

### Profile score and gaps (end of 10 Oct)
Content ~9.5/10. Remaining gaps are not wording: **get ID-verified, collect recommendations** (hackathon teammate, NITK professor/senior; the logistics leader only if he's comfortable, and never named publicly), **grow connections** (67), add links to Projects, consider a school entry and NITK clubs.

---

## 3. Posts: every one we know, with numbers

### Existing posts (as of 10 Oct)
| Post | Type | Impressions | Reactions | Takeaway |
|---|---|---|---|---|
| **2nd of 135 at the L&T Finance challenge** | Achievement + 3 specific technical insights + NITK network + tagged judge | **716** | 15 reactions, 2 comments | Reach came from the **judge's repost and NITK clubs sharing it**, not his own network. Content was specific enough to repost. |
| **Advocall** ("So I BUILT an AI AGENT that waits on hold…") | Build story: what it does, design call, 3 things that broke | 118 | 5 | Right format, needs a sharper first line |
| **MedLog launch** ("I sat down and spent four hours with one of the most experienced logistics leaders…") | Ops-audit story, 8 agents, synthetic data, promises to post each agent over 2 weeks | 39 (day 1) | 1 | Public promise: post each agent. |
| "Hot take: agents vs employees" (2 mo ago) | Opinion | 83 | 1 | |
| Instagram funnel automation, "OMG... $2,000+ funnel", "Comment AUTOMATION" (3 mo) | Hype + keyword CTA | 82 | 4 | Hype openers don't work |
| Clinic missed-call calculator, "Comment CALC" | Pitch | 101 | 2 | |
| 11 PM dentist story, "Comment DEMO" | Story + pitch | 69 | 2 | |
| "7PM test", "Comment 7PM/FLOW/LOSS" | Pitch + keyword CTA | 20-50 | 0-1 | Posted months before the 5 Oct relaunch on a ~30-40 connection account, so **untested since the relaunch, not dead**. Keyword-bait CTAs ("Comment X") are suppressed since Mar 2026, so test buyer posts without them. |

**Account stats, 10 Oct:** 71 followers, 67 connections, 851 impressions Oct 2-8 (+1,926% on the prior week), 31 profile views, 9 search appearances. Most of the impressions came from the L&T post.

### Week 1 calendar (Sun 11 - Sat 17 Oct, all 9:00 AM Riyadh = 11:30 AM IST)
Full paste-ready texts, visuals, AI-image fallback prompts and first comments are in `CONTENT_PLAYBOOK.md` section 11.

| Day | Post | Format |
|---|---|---|
| Sun 11 | **Re-introduction: "Everything I've shipped so far, and what broke"** (pin to Featured) | Text + image |
| Mon 12 | MedLog P4: "A driver replied 👍. My agent refused to guess." | Text + cockpit screenshot |
| Tue 13 | "5 ML lessons no lecture taught me" (L&T + breaking gradient descent) | 7-slide PDF carousel |
| Wed 14 | Ayah Archive: faceless brand, 1.1M views in 30 days | Text + real Instagram insights screenshot |
| Thu 15 | "3 of my 8 AI agents don't use AI" | Text + P5 days-of-cover screenshot |
| Fri 16 | The truth gate: "my AI isn't allowed to say anything I haven't done" (no mention of scraping) | Text + blurred screenshot |
| Sat 17 | MedLog P2: "3,000 invoices a month. 10-15 minutes each." | Text + three-way-match screenshot |

### Post 1 status (RESOLVED 15 Oct: the re-introduction is live, 151 impressions; the text below is the 12 Oct history)
Drafted in the LinkedIn composer (Ayah line corrected to "faceless digital brand"). Image `post1-reintro.png` (1080x1350, brand style) is on the Desktop; the user was asked to attach it manually (the browser can't drive the native file picker). Scheduling for Sun 11 Oct 9:00 AM Riyadh was planned, but **today is Mon 12 Oct, so the Sunday slot has passed unless it was scheduled or posted**. Check LinkedIn to see whether Post 1 is live. If not, post it now (or tomorrow) and shift the calendar by a day. After posting: first comment with links (Advocall demo/repo, MedLog repo, GitHub), @-tag Advocall teammates and Build for Billions in the Advocall bullet, add to Featured, reply to every comment in the first hour.

---

## 4. What we have been doing (timeline)

| Date | What |
|---|---|
| 5 Oct | Goal set: personal brand on LinkedIn -> 10-20 qualified sales calls/month. Built the **comment engine** (GitHub Actions 3x/day, Gemini drafts, Telegram cards, truth gate). |
| 6 Oct | Built the **dashboard** (static page on GitHub Pages, per-device GitHub token, Post-now / Pipeline / Stats tabs). |
| ~7-9 Oct | Engine running; on/off switch added (dashboard + /pause /resume); 59 cards generated, 35 posted. |
| 10 Oct | **Personal brand research** (Guillaume Moubeche, Justin Welsh, Liam Ottley, Nick Saraev; Saudi competitors like Nuvxor) -> `PERSONAL_BRAND.md` v1/v2 (niche + geography decision). |
| 10 Oct | **Full profile optimisation** from the CV: headline, About, Featured, Education, Experience, Projects, Honors, Skills, Services, contact info, Open to Work, custom URL. Fixed mistakes (headline overwrite, duplicate entries). |
| 10 Oct | **Content playbook v3**: 2026 algorithm research, creator teardown (Lara Acosta, Charlie Hills, Ruben Hassid, Shubham Saboo), own-post analysis, 7-day calendar, funnel + DM templates. User correction: L&T reach = judge repost -> Amplification section added. |
| 11-12 Oct | Designed Post 1 image + text in the composer. User correction: Ayah Archive = **faceless digital brand**, not a product (fixed in playbook, memory, image, draft). Wrote this brain file. |
| 12 Oct | Hand-done outreach in Chrome: 10 comments and 12 connection requests on ICP people, logged via the new CRM `manual` action. Replied to Bilal, Fawad, Apoorv and Albin. |
| 12-15 Oct | Posts: re-introduction, "never said I don't know", MedLog P1 complaint desk, MedLog P2 three-way match. The engine kept running (111 comments posted by 15 Oct). CI state-push race fixed (commit 9adf9a0). |
| 15 Oct | Full analytics review (baseline table above). **Profile V3**: repositioned as an AI consulting & engineering company with a real estate & clinics lane (V2 "answer every enquiry" rejected as too basic). **V3.1**: new banner, ad spend confirmed at 7,500+ AED. `PROFILE_VERSIONS.md` created. |
| 15-16 Oct | **Website raynixai.com built and launched** (Next.js on Vercel, separate repo `..\raynix-website`): globe hero, leaks, services, ROI calculator, process, FAQ, Cal + WhatsApp + email. Domain moved from Lovable to Vercel (GoDaddy DNS, email records untouched). New logo (notched-ring "R", peach #F2B896). Search Console domain verified. |
| 16 Oct | **Client focus.** `FIRST_CLIENTS_PLAYBOOK.md` written (offer, scripts, leak map, 20-minute audit call, pilot agreement, 14-day sprint 17-30 Oct). Offer changed from a free build to the **Founding Partner Program** (pay after targets are hit). Built the 15-slide deck (Slides artifact + public PDF) and the **/founding page** with OG image and a homepage link. LinkedIn: contact-info website, **Featured section**, and the **founding announcement document post** (about 10:30 AM Riyadh, link in the first comment). |

### The comment engine (what it is, state on 9 Oct)
- Private repo `Mohammed-Rayan07/linkedin-comment-engine`; runs 08:00 / 13:00 / 18:00 Riyadh; Telegram bot @Client_Hunter7_bot; dashboard `https://mohammed-rayan07.github.io/comment-crm/`.
- Finds posts via Apify (free plan, $5/month cap, $0.97 used on 9 Oct, cap 80 posts/day), scores them, drafts 3 expert comments through the **truth gate**, delivers cards. **Rayan posts every comment himself.** Never auto-posting, never using his LinkedIn cookie.
- Totals on 9 Oct: 328 posts seen, 59 cards (35 posted, 23 sent, 1 skipped), 34 learned examples (his edits become few-shot examples). Lanes: real estate 33 cards, clinics 13, SMB owners 13. Max 25 cards/day, 15-20 comments/day target.
- LLM: free Gemini with a fallback chain (503 "high demand" is common). `my_stats` is off (it costs Apify credit).
- Live finding: pain-keyword searches return ~90% vendors; filter by author title with `OR` syntax; GCC buyer posts are scarce, so volume comes from creator/prospect watchlists.

---

## 5. Strategy digest (the why)

### 2026 algorithm, what to trust
- Interest graph drives ~50% of first distribution (connection graph ~10%), so topic consistency and genuinely useful posts beat network size.
- Comments > likes; saves > comments; threaded replies ~2.4x reach; momentum runs 3-8 hours.
- Two posts the same day each lose ~40% reach, so **1 post/day, never 2**; put volume into comments and DMs.
- 900-1,300 characters; carousels (PDF) highest engagement; real photos/screenshots beat generic graphics; hashtags 0-3 (no reach benefit); links in the **first comment**; "Comment KEYWORD" bait suppressed since Mar 2026.

### Creator patterns to copy
Hook under ~12 words with a number/contradiction/confession; one idea per post; short lines; real numbers; story -> lesson -> specifics -> specific question (SLAY: Story, Lesson, Actionable, You); vulnerable personal story + real photo wins (Lara: 6.7k reactions); timely tool news with a number + free resource (Charlie: 3.1k). Size alone doesn't buy engagement (Ruben: 943k followers, ~1k reactions).

### Positioning
- **Since 15 Oct:** Raynix AI is an **AI consulting & engineering company**. The lane is real estate & clinics (leads into booked viewings and appointments). It sells one full connected system (capture, instant AI reply, AI sales follow-up, booking, CRM/Drive, owner alerts, reviews and reactivation), audit first. Plain owner language beats jargon (Rayan rejected "map operations leaks" as too complex). Dubai/GCC buyers have seen many "automation kids", so copy must signal depth.
- Not "another WhatsApp-bot vendor": the Saudi niche is crowded and everyone sounds the same (closest twin Nuvxor: "8 weeks, ~200 conversations, zero clients").
- Distinct angle: **operator's audit first, then build**, plus **engineering judgement** ("the LLM talks, the code decides"; honest about synthetic data).
- The first client comes from a person, a referral or showing up, and from making "yes" cheap (free leak map, then paid pilot), not from cold DMs. Riyadh in-person meetings are an edge.
- Niche scoring: easiest first clients via LinkedIn = real estate teams (UAE/UK/US/AU) or marketing agencies that resell; clinics = GCC priority; law firms = test; home services = wrong channel.

### The funnel
Post / comment -> profile (headline + Featured sell) -> follow/connect -> **DM within 24h, a question about THEM, never a pitch** -> conversation (log in dashboard Pipeline) -> "want me to look at how it works today? 20 min, no pitch" -> call / in-person -> free one-page leak map -> paid pilot. **Since 16 Oct** the profile step routes to raynixai.com/founding (Featured card, first) → the Cal audit booking or WhatsApp, and the paid pilot is the Founding Partner Program. DM templates (builder, owner, agency, recruiter) are in `CONTENT_PLAYBOOK.md` section 8.

### Amplification (biggest lever)
Tag only people genuinely part of the story (judges, organisers, teammates, mentors, clubs), 2-5 max, in a natural thank-you line; make the post make *them* look good; DM after posting without asking for a repost; share wins in NITK club chats. Never tag strangers for reach. **Never tag the MedLog interviewee or his employer.**

### Content pillars
Build breakdowns 45% · ML/engineering lessons 20% · personal journey 20% · buyer-facing opinion 15% (only when backed by a build).

### Daily routine (~75 min)
08:30 post 10 comments from dashboard cards (rewrite first line) · 09:00 publish + first comment · 09:00-10:00 reply to every comment · midday 10 more comments + 15 connection requests · evening DM every new engager + log in Pipeline · Sunday night: Stats tab review.

### Improvement loop
Keep any format that beats median impressions 2x (sequel within 7 days); kill any under 50% of median twice; repurpose winners as carousels 3-4 weeks later; log learnings under "Week log" in `CONTENT_PLAYBOOK.md`. Test next week: move 2 posts to 5 PM Riyadh.

---

## 6. The truth gate (what he may and may not say)

**Allowed facts:** NITK B.Tech AI (2025-); JEE Advanced 2025 top ~2%; L&T Finance 2nd of 135 (60 final submissions, top 8 presented, 18.47% MAPE, 47,970 rows, 43% no bureau record, loss-from-metric worth ~4 points, accounting identity, geography >50% of signal); Advocall (24h, Build for Billions 2026, first hackathon, Next.js/TypeScript/Vapi/Deepgram/GPT-4o/SSE/Render, English/Hindi/Kannada, Twilio->WebRTC switch, Vercel->Render move); MedLog (8 agents, bilingual, synthetic data, open code; audit facts: 23 trucks / 50-60 supervisor calls a day, 3,000 invoices a month at 10-15 min, 16 days PR->PO, 30-40 stock-outs a day triggering 20-30 calls, a week of document gathering before audits; P4 👍 not guessed + 15-minute grace; P5 days-of-cover = on hand / daily use, red <=3 (<=5 critical), amber <=7 (<=10); P5/P7/P8 use no LLM; P2 three-way match, test batch 6 docs -> 1 cleared, 5 to humans, 6,880 SAR at risk, run aborts when the ERP is down); linear regression from scratch; Ayah Archive (faceless digital brand: 1.1M+ views in 30 days, 5,000+ followers, 500+ purchases, **7,500+ AED (₹2L+) of Meta ads** (confirmed by Rayan 15 Oct; the old "₹100K+" figure and the "9,000+ AED at 3x ROI" line are NOT to be used), automated payment/delivery via Cosmofeed); the Founding Partner Program terms exactly as on raynixai.com/founding; voice reliability layer (transcript-to-record match, confirm, phonetic retry, spell, SMS fallback; ~20 ms lookups; ~$1-1.30 per 5-minute call); StockPilot (AI read/propose only); speed-to-lead under 10 seconds; the comment engine (human posts everything); the account numbers above.

**Never:** client results or revenue (none verified); testimonials; review-gating wording or asking for Google reviews as payment; "we" for a solo company; the WhatsApp number as visible text; fake scarcity or invented anchor prices; "deployed for X businesses"; Arabic fluency; the MedLog operator/interviewee/employer or any identifying detail or family; prospect names; invented "what broke" stories; scraping/Apify talk; years of experience not listed. Where a post needs a private detail, write `[fill in]`.

**Voice bans (comments):** "Great post", "Love this", "Thanks for sharing"; game-changer, unlock, leverage, delve, landscape, seamless, robust; "It's not X, it's Y"; em dashes; hashtags/links/emojis in comments; any pitch ("DM me", "book a call"); "Thoughts?".

---

## 7. Image system
Priority: real photo of him > real screenshot of the thing running > real chart from his code > text-on-colour slide > AI image (concept only, never fake dashboards/metrics/people). Size 1080x1350 (4:5) for posts, 1200x630 for link previews. Any illustrative visual is labelled "Example".

**Brand system (since 15-16 Oct; use it for new post images, carousels and PDFs).** It matches the banner, website and deck.
- **Fonts:** Instrument Serif (headlines, often italic for the emphasis phrase) + Manrope (body).
- **Dark colours:** background `#231b16`, surfaces `#2d231d`/`#322720`, border `#4a3a2f`.
- **Accent:** brand peach `#F2B896`.
- **Text:** `#f6ece3` (muted `#c9b8a8`).
- **Light variant:** cream `#f4ebe1`/`#fbf6f0` with copper `#9a5631` and body `#5e4a3d`.
- **Logo:** the notched-ring "R". The kit is in `..\raynix-website\public\brand\` (SVG peach/light/dark, PNG 512/1024).
- **Rendering:** write the image as HTML, then screenshot it with headless Chrome (`chrome.exe --headless=new --window-size=W,H --screenshot`) at 2x. The banner source is `assets/linkedin-banner.html`, a good template.

**History:** the old Post 1 style (light `#F7F7F5`, ink `#111827`, blue `#2563EB`, "building in public" footer, generated by `post1.py` and saved to `Desktop\post1-reintro.png`) is retired for new posts.

---

## 8. Open items and risks
> **Current open items are in START HERE sections 5 (content queue) and 10 (Rayan's items).** The list below is the 12 Oct version, kept for history; items 1-2 and the Featured update are done.

**Do now (12 Oct)**
1. ~~Check whether Post 1 is live~~ Done: live (see STATUS UPDATE 15 OCT).
2. About now says "digital brand" (fixed). Still open: "monthly views" -> "views in 30 days" in About, and check **Projects #4** wording.
3. Mon 12 post (MedLog P4 👍): screenshot the cockpit P4 tab.
4. Tag/DM: Advocall teammates, Build for Billions, Dr. Kamlesh Kumar (only with a genuinely new line), IET NITK, Incub8 NITK.

**This week**
- Build the Tue carousel PDF (7 slides; needs his real loss-divergence plot and the `[fill in]` learning rate).
- Real Instagram insights screenshot for Wed (blur buyer names).
- Fri post: update comment/profile-view counts that day.
- Get ID-verified; request 2-3 recommendations.
- Update Featured; add links to Projects.

**Next week**
- MedLog P1 desk, P6 live status, P3 reports; Advocall "4 things that broke" carousel; build the real "7 PM test" PDF before mentioning it again; first "timely take" within 48h of the next big AI release.

**Risks**
- Automation signals: keep 5-8 comments per session, never auto-post.
- Overclaiming: Experience says "built for", never "deployed for"; MedLog always "synthetic data".
- Reach depends on amplifiers (judge, clubs); keep creating things worth amplifying and thank people genuinely.
- Comment-engine free tiers (Gemini 503s, Apify $5/month); GitHub Pages token is per device.

---

## 9. Quick reference: links and handles
- LinkedIn: linkedin.com/in/mohammed-rayan-ai
- Founding post: https://www.linkedin.com/feed/update/urn:li:activity:7516764913470537729/
- Website: https://raynixai.com · offer page https://raynixai.com/founding · public PDF https://raynixai.com/raynix-ai-founding-partner-program.pdf
- Deck (editable, private): https://claude.ai/artifact/QkxoGowcrstLCPDTU4Sqtp
- Booking (Cal): https://cal.com/mohammed-rayan-p9qiwg/ai-audit · email rayan@raynixai.com · WhatsApp: wa.me link in `raynix-website/lib/site.ts` (never show the number as text)
- Website deploy: Vercel team `raynix1`, project `raynix-ai`, `vercel deploy --prod --yes` from `..\raynix-website`
- Post Inspector (refresh link previews): https://www.linkedin.com/post-inspector/
- GitHub: github.com/Mohammed-Rayan07 (MedLog: `raynix-medlog-suite`; also `linear-regression-from-scratch`; the engine repo is private)
- Dashboard: https://mohammed-rayan07.github.io/comment-crm/
- Ayah Archive: ayaharchive.shop
- Telegram bot: @Client_Hunter7_bot
- Local paths: repo `C:\Users\Lenovo\Desktop\Claude Code\Linkedin - AI Agent`, MedLog `...\Claude Code\raynix-medlog-suite`, website `...\Claude Code\raynix-website`, banner `assets\linkedin-banner.png` (+ `.html` source), memory `...\.claude\projects\...\memory\`
