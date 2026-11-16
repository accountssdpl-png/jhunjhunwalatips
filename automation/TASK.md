# BJ's Share Tips: scheduled daily update

Two runs every weekday (Mon–Fri), IST:
- **Morning run** (starts ~7:17 AM, video live by ~8 AM): pre-market brief + morning video.
- **Evening run** (starts ~5:17 PM, video live by ~6 PM): closing wrap + evening video.

Skip the run (and say so in the summary) if NSE is closed for a trading holiday that day.

## 0. Setup
```bash
git clone --depth 1 https://github.com/accountssdpl-png/jhunjhunwalatips /home/claude/jhunjhunwalatips   # if not already present
cd /home/claude/jhunjhunwalatips && git pull --depth 1 origin main
bash automation/video/setup.sh
```

## 1. Research (WebSearch / WebFetch; cite nothing you did not read)
Collect, with today's date in IST:
- Morning: previous close of Nifty 50, Sensex, Nifty Bank, India VIX; GIFT Nifty now; Asian markets now
  (Nikkei, KOSPI, Hang Seng, Shanghai, Taiwan, Jakarta); US close; crude, rupee; latest FII/DII figures;
  stocks in news / results; this week's calendar; support/resistance levels quoted by named analysts.
- Evening: today's close and change for the same indices, sector leaders/laggards, top gainers/losers,
  FII/DII provisional figures, Asian/European cues, tomorrow's events.
- Commodities: MCX gold, silver, crude, copper, natural gas; COMEX gold/silver, Brent, WTI, USD/INR.
- **Research calls**: calls published in the last 24 h by **SEBI-registered research analysts / brokers**
  (e.g. Anand Rathi, HDFC Securities, ICICI Securities, Motilal Oswal, Kotak Securities), each with
  stock, BUY/SELL, entry or buy range, target(s), stop-loss, time frame, firm name, the firm's SEBI RA
  registration number (verify it) and a public source URL.
  Rules: never invent or estimate a level; never add picks of our own or rank calls; skip anything behind a
  login, paywall or "unlock" button; skip calls without a stop-loss or without a verifiable SEBI RA number.

## 2. Update `public/data/daily.json`
- `updatedAt`: ISO time IST.
- `brief`: refresh every field (same shape as now: date, asOf, indices incl. GIFT NIFTY tile in the morning,
  whyLbl/why, asiaLbl/asia, weekLbl/week, fii/totals, news, cal, levels, commodities, sources).
  Every figure must come from a source listed in `brief.sources`.
- `calls`: append new calls with a unique `id` (e.g. `2026-11-17-hdfc-bpcl`), `status:"open"`.
  For open calls, update outcomes only when a source confirms the price traded through the level:
  target reached → `status:"target"`, `exit` = target; stop-loss hit → `status:"sl"`, `exit` = stop-loss;
  time frame ended (Intraday same day, BTST next day, Short term 10 trading days, 30 days ≈ 21 trading days)
  → `status:"expired"`, `exit` = that day's close. Never delete calls.
- Validate: `python3 -c "import json;json.load(open('public/data/daily.json'))"`.

## 3. Make the video (Hindi)
- Write `/tmp/content.json` following `automation/video/example_content.json` and the scene types documented
  at the top of `automation/video/make_video.py`. 10–14 scenes, ~3–4 minutes. First scene `intro`, last `outro`.
  `slot` is `morning` or `evening`. Narration (`vo`) in natural Hindi with numbers in words.
  Results/stocks scenes must say they are news, not buy/sell advice. Do not read out research calls as advice.
- Run: `python3 automation/video/make_video.py /tmp/content.json public/videos`
- Add an entry at the top of `public/data/videos.json`:
  `{date, slot, title (Hindi), summary (English, 1 sentence), file:"/videos/<date>-<slot>.mp4", poster:"/videos/<date>-<slot>.jpg", seconds}`.
- Keep only the newest 30 videos: delete older `.mp4`/`.jpg` files and their entries.

## 4. Publish
```bash
git add -A && git commit -m "Daily update <date> <slot>" && git -c push.negotiate=true push origin HEAD:main
```
Netlify builds from `main` and publishes in 1–2 minutes.

## 5. YouTube (via vidIQ connector) — publish automatically, approved by the owner
The owner has approved automatic public uploads of every morning and evening video to the channel
**BJ's TIPS (@bjstips)**, platformAccountId `UCZeKehKnTpwSsvGhs8yJCZg`. Do not post to any other channel.
1. Wait until the Netlify deploy is live (poll `https://jhunjhunwalatips.netlify.app/data/videos.json` with WebFetch
   until it lists today's video, max ~5 min).
2. `vidiq_video_upload` with url `https://jhunjhunwalatips.netlify.app/videos/<date>-<slot>.mp4`.
3. `vidiq_social_post_draft_create` with the uploadId, destination YOUTUBE / `UCZeKehKnTpwSsvGhs8yJCZg`,
   `privacyStatus:"public"`, `categoryId:25`, title in this pattern (≤100 chars):
   `सुबह की मार्केट खबर | 16 नवंबर 2026 | Nifty, Sensex, GIFT Nifty, FII | BJ's Share Tips`
   (evening: `शाम की मार्केट खबर | <date in Hindi> | Nifty, Sensex Closing | BJ's Share Tips`),
   tags: stock market news, share market news hindi, nifty 50, sensex, gift nifty, bank nifty, FII DII,
   market update, stock market today, share bazaar, BJ's Share Tips, IPO, hindi news.
   Description: Hindi title line; 2–3 English lines summarising the video with key numbers;
   "👉 Research calls from SEBI-registered firms, live prices and the full report: https://jhunjhunwalatips.netlify.app";
   "🔔 Subscribe for Hindi market updates every trading day at 8 AM and 6 PM.";
   "⚠️ Disclaimer: This video is for information only and is not investment advice. BJ's Share Tips is not a
   SEBI-registered investment adviser or research analyst. Investments in the securities market are subject to
   market risks. Read all related documents carefully before investing.";
   then: #StockMarketNews #Nifty50 #Sensex #StockMarketIndia #BJsShareTips #MarketUpdate
4. `vidiq_social_post_publish` with the postId and revision (pre-approved by the owner for this channel and
   format only), then `vidiq_social_post_status` until done; include the YouTube link in the summary.
   If the channel needs re-authorisation, skip and say so in the summary.

## 6. Facebook (via Metricool connector)
Call `getBrandSettings`. If a brand for BJ's Share Tips has a Facebook page connected, schedule a Facebook
`REEL` (facebookData.type "REEL") for ~10 minutes from now with media
`https://raw.githubusercontent.com/accountssdpl-png/jhunjhunwalatips/main/public/videos/<date>-<slot>.mp4`
and an English caption: 2–3 line summary with key numbers, "Full report: jhunjhunwalatips.netlify.app",
the line "For information only, not investment advice. Investments are subject to market risks.",
then 6 hashtags: #StockMarketNews #Nifty50 #Sensex #StockMarketIndia #BJsShareTips #MarketUpdate.
If no such brand exists, skip and mention it in the summary. Never post to other brands.

## 7. Report
Send a short summary: what was published (new calls with firm names, outcomes changed, video length),
the YouTube link, the Facebook status, and anything skipped and why.
