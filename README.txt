BJ'S SHARE TIPS — NETLIFY ADMIN TRACKER

IMPORTANT: This project needs a Netlify build so its serverless function and Netlify Blobs backend are deployed. Do not deploy only the public folder using a static-only manual upload.

RECOMMENDED SETUP (KEEP YOUR EXISTING NETLIFY SITE)
1. Extract this ZIP on your computer.
2. Create a new private GitHub repository and upload ALL extracted contents, including:
   - public/index.html
   - public/logo.jpg
   - netlify/functions/api.mjs
   - netlify.toml
   - package.json
3. In Netlify, open your EXISTING site jhunjhunwalatips.netlify.app.
4. Go to Project configuration > Build & deploy > Continuous deployment > Link repository (wording may vary).
5. Connect the GitHub repository you created.
6. Set Build command: leave blank (or use npm install if Netlify requests a build command).
   Set Publish directory: public
   Functions directory: netlify/functions
   netlify.toml already declares these settings.
7. Go to Project configuration > Environment variables and add:
   ADMIN_PASSWORD = a strong, unique password you choose
   SESSION_SECRET = a separate random secret of at least 32 characters
8. Trigger a new production deploy and wait for it to finish.

ADMIN
Open the live site, click Admin, and sign in using ADMIN_PASSWORD.
Calls are stored in Netlify Blobs. Only authenticated admin sessions can add/edit/delete calls. Sessions expire after 8 hours.

SECURITY / OPERATIONS
- Never put secrets in public files, GitHub, screenshots, or chat.
- No broker account-opening, payment, or subscription section.
- Prices/CMP are manual; no live NSE price feed is connected.
- The new tracker starts empty. Add only verified calls.
- Confirm the site deploy is successful before sharing it publicly.


MARKET DATA & NEWS UPGRADE
--------------------------
The public dashboard now includes a TradingView Market Overview widget with India (SENSEX, NIFTY 50, NIFTY BANK) and Global (Dow Jones, Nasdaq, S&P 500, Nikkei 225, Hang Seng, FTSE 100) tabs. TradingView supplies the quotes; whether an instrument is real-time or delayed depends on TradingView and exchange data entitlements. The website does not claim exchange-certified real-time prices. For execution, verify prices with your broker/exchange.

The Latest Market News section fetches India and international headlines from Google News RSS through the Netlify Function at /api/news. The browser refreshes the feeds every five minutes. Headlines link out to publishers; no article text is republished. No news API key is required.

No additional Netlify environment variables are required for the market widget or news feed. Keep the existing ADMIN_PASSWORD and SESSION_SECRET variables configured for the private admin panel. Do not share these secrets.

DEPLOY
------
Upload/commit the contents of this ZIP to the same GitHub repository connected to your existing Netlify site, replacing the prior package files. Keep the same production branch and Netlify site. Trigger a new deploy. After deployment, test /api/calls and /api/news?region=india and /api/news?region=global.


NOVEMBER 2026 REDESIGN: SHARE TIPS + MARKET BRIEF + LIVE PRICES
---------------------------------------------------------------
- Share tips: 11 calls from SEBI-registered firms (Anand Rathi, HDFC Securities,
  ICICI Securities) are built into the function as starting data. They show until
  you save anything in Admin; after your first save, everything lives in Netlify Blobs.
- Admin has new fields: Buy range, SEBI RA reg. no., Note.
- Market brief (index close, why it moved, week board, FII flows, stocks in the news,
  calendar, levels, sources) is in the "EDIT DAILY: market brief" block near the top
  of the script in public/index.html.
- Live stock prices (optional): add environment variable EODHD_API_TOKEN (eodhd.com plan
  covering NSE/BSE live delayed prices, about 15-20 min delay) and redeploy. Each tip card
  then shows last price, a stop-loss-to-target bar and move since call, refreshed every
  minute in market hours. Without the key the site works normally with call-date prices.
- Check symbol codes with EODHD (e.g. TMCV for Tata Motors CV, NSEI.INDX for Nifty).


16 NOV 2026 UPDATE: LIGHT THEME + PAGES
---------------------------------------
- New light design. Tabs: Home, Today's picks, All tips, Commodities, News, Track record (Admin via button).
- Today's picks = calls dated today; if none yet, shows the latest published day with a note.
- Commodities page: MCX and international tiles (edit in BRIEF.commodities), live international
  prices from TradingView (gold, silver, copper, crude, natural gas, USD/INR) and commodity news.
- News page: India, Global, Commodities and IPO tabs (/api/news?region=india|global|commodities|ipo).
- TradingView strip no longer uses NSE/US index symbols that widgets block; Indian indices come
  from the brief (or live via EODHD_API_TOKEN).
