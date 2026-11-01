# Andra Markets

The Andra Markets website: a markets research platform with dashboards, quant
tools, an economic calendar, a daily close note, a research library, interview prep and explainers.

- `assets/`: stylesheet, script, self-hosted font, brand mark.
- `tools/build_site.py`: generates every page from one shell. Edit markup here, except for the section pages added on 1 Nov 2026, which each live in their own module, `tools/page_<name>.py` (`pages(site)` returns their HTML; `site` is build_site itself, for its shell and helpers). It also writes `assets/search-index.js` (the header search index, not committed).
- `tools/check_site.py`: run after the build, at every deploy. It fails the deploy if a close note page came out without a section its note has, or the homepage index lacks a section of the menu, so the live site keeps its last good version.
- `tools/import_notes.py`, `tools/nyse.py`: import the daily close notes (below).
- `tools/dashboard_data.py`: fetches the dashboard figures at deploy time (below).
- `tools/company_data.py`: fetches the figures behind the company pages (the calendar's 600: the 200 largest in the S&P 500, the STOXX Europe 600 and the six Asian markets) at deploy time, into `.cache/companies/`.
- `tools/calendar_data.py`: fetches the calendar at deploy time (below).
- `tools/world_data.py`: fetches the World markets figures at deploy time (below).
- `assets/world.js`: the World markets comparison radar.
- `tools/fx_data.py`: fetches the daily FX analyses and the FX pairs table at deploy time (below).
- `tools/strip_data.py`: fetches the homepage market strip (the tape) every 15 minutes in US hours (below).
- `tools/fedrates_data.py`, `assets/fedrates.js`: the Fed & Rates section (`fed-rates/`): fetches its figures at deploy time and every 15 minutes in US hours (below), and draws its charts.
- `data/path_to_wall_street.json`, `assets/careers.js`: Break into Wall Street (`break-into-wall-street/`), the careers guide.
- `data/recruiting_calendar.json`, `assets/recruiting.js`: the recruiting calendar (`recruiting-calendar/`; it was part of the guide until 1 Nov 2026 and its old address redirects), kept by hand (below).
- `data/technicals/<topic>.json`, `assets/technicals.js`: its nine technical preparation pages (`break-into-wall-street/technicals/<topic>/`): what to know, a worked example, practice cards, common mistakes. Edit the guide's text in the data file and update its `reviewed` date.
- `data/reports/`: the weekly reviews and research in the Research Library (`research/`): `index.json` plus one PDF per report in `pdf/`, published as it is at `research/pdf/`. `tools/import_report.py` copies a report's PDF and adds its line; see `data/reports/README.md`.
- `data/interview_prep.json`: Markets Interview Prep (`interview-prep/`): the weekly block (`week`, rewritten each week) and the question bank.
- `tools/page_central_banks.py`, `tools/centralbanks_data.py`, `assets/centralbanks.js`: Central banks (`central-banks/`): the four policy rates and next meetings, fetched at deploy time (below).
- `tools/page_recession_watch.py`, `tools/recession_data.py`, `assets/recession.js`: Recession watch (`recession-watch/`): five indicators and NBER recessions from FRED, fetched at deploy time (below).
- `tools/page_chart_of_the_day.py`, `assets/chart-of-the-day.js`: Chart of the day (`chart-of-the-day/`), one chart per close note.
- `tools/page_market_history.py`, `assets/market-history.js`, `tools/history_data.py`: Market history (`market-history/`), its S&P 500 history fetched at deploy (below).
- `data/interview_simulator.json`, `assets/interview-sim.js`, `tools/page_interview_simulator.py`: the Interview simulator (`interview-simulator/`): tracks and their topics, lengths, same-question groups and the key points of each model answer, kept by hand. The build drops any key point whose words or figures are not in its answer and prints it, as it does key points for a question whose wording changed.
- `tools/legal_content.py`: the legal notice (`legal/`) and the privacy and cookies policy (`privacy/`).
- `assets/lab.js`: the ten Lab tools (`lab/`), which run entirely in the browser. The inputs that differ from a tool's defaults are kept in the URL fragment (`#yld=5&freq=1`), never sent to the server, so a link shares a setup.
- `tools/lab_data.py`: fetches the daily closes behind the Lab's risk and correlation tool at deploy time (below).
- `assets/sim.js`, `assets/fed-game.js`, `assets/portfolio-game.js`, `tools/sim_data.py`, `tools/sim_content.py`: the four Simulators (`simulators/`), their history fetched at deploy time and the historical episodes they reveal (below).
- `assets/calendar.js`: the calendar's week tabs, filters and today mark.
- `assets/profile.js`, `worker/`: the live company data on the Companies pages (search, live price, news, analysts, other US companies) and the Cloudflare Worker it reads from (below).
- `tools/make_mark.py`: makes the transparent header and footer marks from `andra-horse.png`.
- `assets/hero-horse.js`, `tools/make_horse_particles.py`: the homepage hero's particle horse and the particle map it is drawn from (`assets/horse-particles.png`, made from `andra-horse.png`). A click on a link to another page takes the hero back into the point it formed from before the page opens (DESIGN.md, Page transitions).
- `assets/section-scene.js`, `tools/make_section_horse.py`: the section pages' backdrop (a black sphere of floating particles with the horse lit from behind) and the horse texture it uses (`assets/section-horse.png`, made from `andra-horse.png`). Arriving from the homepage the sphere opens out of that point; from one section to the next it carries on while the page cross-fades.
- `data/notes/<date>.json`: one record per close note: its text and the ten
  closing levels for the tape. No PDF or facts file is ever stored here.
- `DESIGN.md`: the design system. Every page follows it.
- `PRODUCT.md`: product truth and brand commitments.
- `AGENT_FIXES.md`: known problems in the agent repo, to fix next.

The HTML pages (`index.html`, `methodology/`, `reports/`, `research/`, `interview-prep/`, `fed-rates/`, `break-into-wall-street/`, `sources/`, `legal/`, `privacy/`, `dashboards/`, `calendar/`) are generated at
deploy time and are not stored in the repo. Pushes to `main` deploy to GitHub
Pages via `.github/workflows/pages.yml`, which builds the pages and publishes
only `index.html`, `methodology/`, `reports/`, `dashboards/`, `calendar/` and `assets/`. To preview
locally: `python3 tools/build_site.py`.

## Publishing the close note

The agent in `Pabloballesteros1412/andramarkets` builds the note and uploads
its files as an Actions artifact. `.github/workflows/publish-notes.yml` in
this repo checks for new artifacts twice an hour from 20:00 to 02:59 UTC,
with a read-only token, and for each one:

- **publishes it** when it passes every check: it commits the note record
  (text and tape closes) to `main`, then deploys the site;
- **holds it in a pull request** titled "Held close note: <date>" when the
  date was not an NYSE trading day, is in the future, the run finished before
  that day's close, the figure check failed, the run was a demo, an
  instrument's print is from another session (`series_off_session` in the
  facts), or the note is incomplete (a section missing or cut short). Merge
  to publish, close to discard;
- **rejects it** when files are missing or broken. Nothing is published and
  the run fails, so GitHub emails you.

One note per date: the newest run that passes is published, and a newer run
that is held gets the pull request; other runs that day are superseded. If the
run behind a live note fails a check when re-checked, that note is taken down.

Each new daily note that is held gets its own pull request. Notes held while
re-checking runs an earlier import already saw (the first backfill, or after
`VERSION` changes in `tools/import_notes.py`) are collected in one "Backfill
review" pull request with a table of date, reason and agent run. To drop a
note there, delete its file in the pull request (**Files changed**, **...**,
**Delete file**), then merge to publish the rest.

Runs before 15 September 2026 saved no note text file. For those, the text is
read back from the report PDF (`tools/pdf_note.py`, checked against all 23
later runs: every field matched exactly) and always held for review.

The figure check result and edition come from the run's
`manifest_YYYYMMDD.json`. Runs from before the agent wrote one (22 October
2026) have them read from the PDF instead (a "Control note." means the check
failed).

The PDF is read only for those older checks and, for old runs, the text; it and the
full facts file are never committed (this repo is public) or offered on the
site. They stay in the agent's artifacts. To publish at once:
**Actions** → **Publish close notes** → **Run workflow**.

To take a note down: open `data/notes/<date>.json` in the web editor, change
`"published": true` to `"published": false`, commit. The site rebuilds without
it. Later runs for that date keep it down until you set it back to `true`.

Each note record keeps, besides the text, only the figures its page shows:
the ten tape closes, the Treasury curve, the risk score and breadth, and the
name, close and change of the instruments in the margin charts (sectors,
credit, FX, commodities, volatility, digital, global indices, the five biggest
gainers and losers). When the charts need new figures, `CHARTS_VERSION` in
`tools/import_notes.py` goes up and the next import run fills every note in
from its own artifact (while that artifact is still kept, 90 days).

Each December, add the next year's NYSE holidays to `tools/nyse.py`.
Until then, notes dated in that year are held for review.

### One-time setup (GitHub web UI)

**1. Create the read-only token**

1. Click your avatar (top right) → **Settings**.
2. Left sidebar, at the bottom: **Developer settings**.
3. **Personal access tokens** → **Fine-grained tokens** → **Generate new token**.
4. **Token name:** `andramarkets-site: read agent artifacts`.
5. **Resource owner:** `Pabloballesteros1412`.
6. **Expiration:** **Custom**, one year from today. Add a calendar reminder a
   week before it expires.
7. **Repository access:** **Only select repositories** → pick `andramarkets`
   (the agent repo, not the site).
8. **Permissions** → **Repository permissions** → **Actions** → **Read-only**,
   and **Contents** → **Read-only** (for the dashboards' archive). Leave
   everything else on **No access** (Metadata: Read-only is added
   automatically and is required).
9. **Generate token**, then **copy** it. GitHub shows it only once.

**2. Save it as a secret in this repo**

1. Open `andramarkets-site` → **Settings** (tab at the top of the repo).
2. Left sidebar: **Secrets and variables** → **Actions**.
3. **New repository secret**.
4. **Name:** `AGENT_ARTIFACTS_TOKEN`. **Secret:** paste the token.
5. **Add secret**.

**3. Let the workflow open pull requests for held notes**

1. `andramarkets-site` → **Settings** → left sidebar **Actions** → **General**.
2. Scroll to **Workflow permissions**.
3. Leave **Read repository contents and packages permissions** selected (the
   publish workflow asks for write access in its own file).
4. Tick **Allow GitHub Actions to create and approve pull requests**.
5. **Save**.

**4. Run it once**

**Actions** tab → **Publish close notes** (left list) → **Run workflow** →
**Run workflow**. The first run imports every note from the last 90 days.
Held ones appear under **Pull requests**.

When the token expires the run fails and GitHub emails you: repeat step 1,
then in step 2 open the existing secret and **Update** it.

## Dashboard data

`.github/workflows/pages.yml` runs `tools/dashboard_data.py` before each
build, and at 11:17 UTC on weekdays so the tiles refresh without a new note.
It writes `.cache/dashboards/tiles.json`: for each dashboard the figures its
tile draws, the history its page (`dashboards/<slug>/`) draws, its source and
its as-of date. The file is kept between runs in the
Actions cache, never committed or published.

| Dashboard | Source | As of |
|---|---|---|
| Sector heatmap, FX majors | Yahoo Finance: sector ETFs, spot FX; changes over 1D to 1Y | Latest close |
| Volatility term structure | Cboe VIX9D, VIX, VIX3M, VIX6M via Yahoo Finance, against 5 sessions before | Latest close |
| Global indices | Yahoo Finance, each at its own latest local close | Newest of those closes |
| Commodities | WTI and gold front-month futures via Yahoo Finance, rebased to 100 | Latest settled session |
| Credit spreads | ICE BofA US high yield and corporate OAS via FRED | Latest observation |
| Inflation and labour | BLS CPI (year on year) and payrolls via FRED | Latest month |
| Cross-asset correlation | 60 sessions of daily returns: S&P 500, TLT, dollar index, WTI, gold, Yahoo Finance | Last session |
| Watchlist breadth | Agent archive: advancers less decliners across the Andra Markets watchlist of US large caps, every published session | Newest published session |

Each dashboard page carries more than its tile: two years of history (five
for inflation), so it can compare with any date in that span, and series
that start switched off: SPY beside the sectors; twelve more indices; ten
more currencies and the dollar index; VIX 1-day, VVIX and the 1M less 3M
slope; Brent, natural gas, silver, copper, platinum, corn and wheat; BBB,
BB, CCC, euro high yield and EM corporate spreads (FRED); core CPI, PCE and
core PCE, and the unemployment rate (FRED); Nasdaq 100, Euro Stoxx 50, HYG,
the euro, copper and bitcoin in the correlation matrix. An extra series that
fails is left off its page; the tile keeps working.

The earnings season tracker is not on the site: there is no reliable free
source of beats and misses. Market-wide breadth has no free source either, so
the breadth tile is labelled as the watchlist's.

From the archive, only the facts of the run behind each published note on an
NYSE trading day are read, never a series the facts flag as not yet published
or from another session, and the full facts file is never written to disk.
Reading the archive releases needs **Contents: Read-only** on the agent repo
in `AGENT_ARTIFACTS_TOKEN` (step 1 below, in addition to Actions). When a
source fails, the tile keeps its last figures and their date; a tile that
has no figures yet shows its source and "Data pending", never a stand-in chart. Neither stops the deploy.

The Treasury curve and the fed funds futures path are in Fed & Rates
(below); the old Yield curve and Fed path addresses redirect there.

## Fed & Rates data

`tools/fedrates_data.py` writes `.cache/fedrates/fedrates.json`, one block
per panel of `fed-rates/`, each with its own source, as-of date and fetch
time. Like every cache, it is kept between runs in the Actions cache and
never committed or published: the page carries its figures inline.

| Block | Source | Refreshed |
|---|---|---|
| Treasury curve, 1M to 30Y (now, the day before, 1W, 1M, 1Y) | US Treasury daily par yield curve CSV; FRED DGS1MO to DGS30 as backup | Every full deploy, including 23:37 UTC on weekdays, after the Treasury posts the day's curve |
| Intraday yields (3M, 5Y, 10Y, 30Y) | Cboe yield indices `^IRX`, `^FVX`, `^TNX`, `^TYX` via Yahoo Finance, delayed; shown only while newer than the official curve | Every 15 minutes while the NYSE is open |
| 2s10s, 3m10y since 1976 and 1982 | FRED `T10Y2Y`, `T10Y3M`; the latest day from the Treasury curve | Full deploys |
| Target range, effective rate | FRED `DFEDTARU`, `DFEDTARL`, `EFFR` | Full deploys |
| FOMC calendar | federalreserve.gov (`fomc_meetings` in `tools/calendar_data.py`); projections at the March, June, September and December meetings | Full deploys |
| Meeting probabilities and expected path | CBOT 30-day fed funds futures (`ZQ`) via Yahoo Finance, delayed about 10 minutes; the path as priced a month ago from settlements | Every 15 minutes while the NYSE is open |
| Fed funds, CPI and core PCE (year on year), unemployment since 1960 | FRED `FEDFUNDS`, `CPIAUCSL`, `PCEPILFE`, `UNRATE` | Full deploys |
| 10Y real yield, 5Y and 10Y breakevens, 5y5y | FRED `DFII10`, `T5YIE`, `T10YIE`, `T5YIFR`; the latest 10Y real yield from the Treasury real yield curve | Full deploys |

The market strip refresh (`strip_only`) runs `tools/fedrates_data.py --fast`:
only the futures, the probabilities and the intraday yields. Meeting
probabilities follow the method CME Group publishes for FedWatch (each
contract settles on its month's average effective rate; the days before a
decision are taken out; a month with no meeting anchors the next). Daily
series older than two years are kept one point a week. A block whose source
fails keeps its last copy and date; one never fetched shows "Data pending".
SOFR futures are not used: there is no free source.

## Recruiting calendar

`data/recruiting_calendar.json` holds one row per US programme: firm, firm
type, programme, kind, cycle, divisions, locations, status, dates or
windows, the URL where students apply, the source of the dates, the day
they were checked and `verified`. There is no free feed of firms' recruiting
dates and the trackers' terms forbid reuse, so it is kept by hand:

- **confirmed:** `opens` and `closes` as the firm states them on its careers
  site or in the posting.
- **expected:** `opens_window` and `closes_window` ("Jan 2027 to Mar 2027")
  from the previous cycle, with `basis` saying what that rests on and
  `confidence`.
- **rolling:** the firm reviews applications as they arrive.
- **unknown:** nothing reliable yet; the row keeps its URL.

Every date is read from the firm's own site (`source`) on the `checked`
day. `verified: true` means someone has since opened `source` by hand and
seen the date; until then the row carries a "Not yet re-checked" tag and the
page head counts how many dated rows have been re-checked (owner, 30 Oct
2026: show the calendar now, re-check as the firms' sites become reachable). Re-check the open rows each month and move
expected windows to confirmed dates as firms post them. The page counts
down to closing dates in the browser, so it stays right between deploys.

## Central banks and Recession watch data

`tools/centralbanks_data.py` writes `.cache/centralbanks/centralbanks.json`
(Actions cache, full deploys only). Rates: the Fed from FRED `DFEDTARU` and
`DFEDTARL`; the ECB deposit facility rate from the ECB Data Portal
(`FM.B.U2.EUR.4F.KR.DFR.LEV`, which lists changes only, so its as-of date is
the day it was read), FRED `ECBDFR` as backup; Bank Rate from the Bank of
England's database (`IUDBEDR`), the BIS as backup; the Bank of Japan from the
BIS (`WS_CBPOL`: the API, then the bulk file). Decision dates for 400 days
ahead come from each bank's own calendar, read with `calendar_data.py`'s
parsers. `tools/recession_data.py` writes `.cache/recession/recession.json`
from FRED `T10Y3M`, `SAHMREALTIME`, `ICSA`, `IC4WSA`, `BAMLH0A0HYM2`, `NFCI`
and `USREC`. Each source is fetched on its own and keeps its last good copy;
with none the pages show "Data pending". Neither endpoint could be reached
from the session that built them, so the first deploy is their first live
test: check its log.

## Market history data

`tools/history_data.py` runs at deploy before the build and writes
`.cache/history/sp500.json` (Actions cache): every S&P 500 daily close since
the end of 1927 from Yahoo Finance `^GSPC` (the S&P 90 before March 1957),
price only. It fetches at most once a day and keeps its last good copy. The
build measures each episode from it and prints a warning when a measured fall
differs from its text's "about N%" by more than 4 points. With no copy the
pages show "Data pending".

## Lab data

Nine of the ten Lab tools are calculators with no data. The tenth, risk and
correlation (`lab/risk-correlation/`), offers every company in the calendar's
earnings universe (`universe` in `.cache/calendar/calendar.json`, written by
`tools/calendar_data.py`) with its benchmark. `tools/lab_data.py` runs after
the calendar fetch and keeps about three years of dividend-adjusted daily
closes for each company and benchmark from Yahoo Finance's chart endpoint in
`.cache/lab/closes.json` (Actions cache, never committed or published). Each
run fetches only the symbols not fetched that day, oldest first, 0.35 seconds
apart, within a time budget (`LAB_BUDGET`, 240 seconds by default); the rest
keep their last closes and go first next run. `tools/build_site.py` turns the
closes into daily log returns in basis points, one `assets/lab-risk-<market>.js`
per market (US, Europe, Asia), which the page loads only when a company from
that market is picked. Mainland Chinese companies use the Shanghai Composite
for beta: Yahoo keeps no CSI 300 history. With no universe or closes yet the
page says "Data pending".

## World markets data

`tools/world_data.py` runs before each build and writes
`.cache/world/world.json` (Actions cache, never committed or published): 25
markets, eight figures each, every one with its own source and date. Each
figure keeps its last good value when a source fails.

| Axis | Source |
|---|---|
| 1M and YTD index return, 3M volatility | Yahoo Finance, each market's main index (local currency) |
| Currency against the dollar | Yahoo Finance, change since the end of last year in the dollar value of the local currency |
| 10Y government bond yield | OECD long-term interest rates (monthly), one SDMX request for all countries |
| GDP growth | World Bank real GDP growth, latest year; IMF World Economic Outlook for Taiwan (last completed year only, never a projection) |
| Inflation, unemployment | OECD monthly figures when under six months old; otherwise World Bank, latest year; IMF for Taiwan |

No figure is estimated: where no free official source publishes one (10-year
yields for Argentina, Turkey, Hong Kong, Taiwan, Indonesia and Singapore;
unemployment for South Africa, China and Indonesia; the dollar against itself)
the axis stays empty and the page names the gap. The OECD answers three
requests per run, three seconds apart (it limits bursts).

## FX section

`fx/` shows the agent's daily FX analysis (agent repo, PR 14) and a table of
the dollar index, the G10 majors and the main emerging-market pairs.
`tools/fx_data.py` runs before each build and writes `.cache/fx/fx.json`
(Actions cache, never committed or published):

- **Analyses:** every `fx_YYYYMMDD_r<run>.json` in an `archive-*` release of
  the agent repo (no other name or place is read), schema `andra.fx/1`, read
  with `AGENT_ARTIFACTS_TOKEN` (Contents: read, as for the dashboards). One is
  shown only when the date is an NYSE trading day that is not in the future,
  the run was not a demo, the figure check passed (`audit.ok`), no trade
  language was flagged, and that session's close note is published: a session
  whose note is held for review or taken down shows no FX analysis. The run
  behind the published close note is preferred, else the newest that passes.
  Only the text and the pair figures are kept. What was not shown, and why, is
  logged and kept under `held` in the cache.
- **Pairs table and charts:** last close and the moves over a day, a week, a
  month and the year so far, as each pair is quoted, and two years of daily
  closes for the charts, from Yahoo Finance.
- **Rate differentials:** each currency's 3-month interbank rate and the
  US's, from the OECD (monthly, one request), for the scatter of each
  currency's move against its differential. A figure older than six months,
  or none (the pound, real and lira today), leaves that currency off the
  scatter, and the page names it.

Until the first analysis passes, `fx/` shows only the pairs table and the link
to the FX dashboard. Each analysis gets `fx/<date>/`, linked from the archive
on `fx/`, with its close note.

## Market strip

`.github/workflows/market-strip.yml` refreshes the homepage tape every 15
minutes while the NYSE is open (to 45 minutes after the close, for the
closing prints; holidays and 1:00 pm early closes from `tools/nyse.py`), once
after the Euro Stoxx 50 close (16:52 UTC) and once after the Tokyo close
(06:52 UTC), on weekdays. Each run calls the deploy with `strip_only`: it runs
`tools/strip_data.py` and rebuilds from the cached dashboard, calendar and
company figures without fetching them again. Every deploy fetches the strip
too. The head reads "Markets 22 Oct 2026, as of 2:45 pm ET"; each figure
carries its own time, or "Close, 22 Oct" once its market has shut.

| Instrument | Source |
|---|---|
| S&P 500, Nasdaq 100, Russell 2000, Euro Stoxx 50, Nikkei 225, VIX, EUR/USD, WTI, gold | Yahoo Finance chart metadata: `regularMarketPrice` at `regularMarketTime` (the close once the session has ended, so Europe and Japan never read "Prior close"), change on the last daily close before that session |
| US 10Y yield | FRED `DGS10` with `FRED_API_KEY` (daily: the latest FRED close, usually the previous session's); Yahoo `^TNX` when FRED is unavailable |

The strip shows only when it is newer than the latest published note's
close; otherwise the tape shows that note's closes as before. The "Latest
close note" link always points to the newest published note. An instrument
that fails keeps its last figure and time (Actions cache, never committed or
published). Deploys queue rather than cancel each other.

## Live company data

The Companies section reads live data in the browser from the **profile
API**, a Cloudflare Worker in `worker/` that holds the vendors' keys and
caches every answer (fundamentals, peers, analysts and search 24 hours, news
15 minutes, the price 60 seconds). `assets/profile.js` uses it in three
places:

- `/companies/`: the search field filters the 600 and lists any other
  US-listed company that matches.
- `/companies/<ticker>/` for US companies: the live price, news and analyst
  recommendations on top of the static page.
- `/companies/live/?t=TICK`: the full profile of a US company outside the 600
  (results, margins, statements, multiples, peers, news, analysts).

`/profile/` (the section's first home) forwards old links there.

| Data | Source (free plans) |
|---|---|
| Price, day change, peers, news, analyst recommendations, last-twelve-month multiples | Finnhub |
| Profile, income statement, balance sheet, cash flow, yearly multiples | Financial Modeling Prep |

The free plans cover US listings only, Finnhub's news sentiment is a paid
feature (the page shows analyst recommendations instead), and FMP allows
about 250 calls a day (about 5 per new ticker; repeat visits come from the
cache). A section the plan leaves out says so on the page.

**The keys never enter the repo or the page.** They live as Worker secrets.
Locally they sit in `.env` (ignored by git). `worker/.dev.vars.example`
shows the variables for `npx wrangler dev`.

### One-time setup (GitHub and Cloudflare web UI)

1. Create a free Cloudflare account at dash.cloudflare.com.
2. In Cloudflare, **My Profile → API Tokens → Create Token**, template
   **Edit Cloudflare Workers**, then copy the token. Copy your **Account ID**
   from the Workers & Pages overview page.
3. In GitHub, **Settings → Secrets and variables → Actions → New repository
   secret**, add four secrets: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`,
   `FINNHUB_API_KEY`, `FMP_API_KEY`.
4. **Actions → Deploy profile API → Run workflow.** It runs the Worker's
   tests, deploys it and passes the two vendor keys to it as Worker secrets.
   Its summary shows the Worker's address
   (`https://andra-profile-api.<your-subdomain>.workers.dev`).
5. The site calls `PROFILE_API` in `tools/build_site.py`
   (`https://andra-profile-api.pabloballesteros141.workers.dev`). If the
   Worker moves, change it there, or set a repository variable `PROFILE_API`
   (Settings → Secrets and variables → Actions → Variables), which wins.

The Worker answers only pages from `ALLOWED_ORIGINS` in
`worker/wrangler.toml` (the site's GitHub Pages origin; add the custom
domain there if the site gets one). Optional: bind a KV namespace `STALE`
(see `wrangler.toml`) so a vendor outage or a spent quota serves the last
good answer, marked with its date. To change a key, update the repository
secret and run **Deploy profile API** again. Tests: `cd worker && npm test`.

## FRED API key

The dashboards, the calendar, Central banks and Recession watch read FRED through its official API
(`api.stlouisfed.org`), which needs a key; the keyless download they used
before kept timing out from GitHub's runners. Add it once as a repository
secret: **Settings → Secrets and variables → Actions → New repository
secret**, name `FRED_API_KEY`, value the key the agent repo uses. The deploy
and the Calendar check pass it to the fetchers only. It is never printed: any
FRED error is logged with the key replaced by `***`, and GitHub masks it in
the logs too. Without it, FRED counts as down and the tiles and calendar keep
their last good figures.

## Calendar data

`.github/workflows/pages.yml` runs `tools/calendar_data.py` before each build,
at 11:17 UTC on weekdays and again at 15:47 UTC, after the US morning
releases. It writes `.cache/calendar/calendar.json`, kept in the Actions cache
(never committed or published): every event since the calendar's first week,
the last good copy of each source with the day it was read, and the series
behind Previous and Actual. `tools/build_site.py` turns it into `calendar/`
(this week and the next four), `calendar/week/<monday>/` (one page per week,
the close notes link there) and the homepage section.

| Rows | Schedule from | Previous and Actual from |
|---|---|---|
| Payrolls, CPI, PPI, JOLTS, ECI | BLS calendar file (schedule pages as fallback) | FRED |
| GDP, PCE, trade balance | BEA release schedule | FRED |
| Retail sales, housing starts, new home sales, durable goods | Census economic indicators calendar | FRED |
| Jobless claims | Department of Labor: Thursdays 8:30 am ET, a day earlier on a federal holiday | FRED |
| Industrial production | Federal Reserve G.17 release dates | FRED |
| FOMC decision, press conference, minutes; blackout | Federal Reserve FOMC calendar; the blackout from its communications policy | FRED target range |
| Fed Chair and Vice Chair speeches | Federal Reserve monthly calendar | |
| Treasury note and bond auctions | TreasuryDirect upcoming auctions | TreasuryDirect high yields |
| ISM PMIs, S&P Global flash PMIs, RatingDog China PMIs | ISM and S&P Global release calendars | |
| Consumer confidence, consumer sentiment | The Conference Board, University of Michigan | FRED (sentiment) |
| ECB decision, press conference, account; Lagarde speeches | ECB Governing Council and weekly calendars | ECB deposit rate |
| Euro area HICP, GDP, unemployment, production, retail, sentiment | Eurostat euro indicators calendar | Eurostat |
| Bank of England decision | BoE MPC dates | BoE Bank Rate |
| UK CPI, labour market, GDP, retail sales | ONS release calendar | ONS time series |
| Bank of Japan decision | BoJ meeting schedule (date only) | |
| China activity, prices, PMIs | NBS release calendar | |
| Loan prime rates | PBoC: the 20th, 9:00 am Beijing, next working day | |
| NYSE holidays and early closes, options expiry, quad witching, S&P 500 rebalance | `tools/nyse.py` and the exchanges' published rules | |
| One-off events | `ONE_OFF` in `tools/calendar_data.py`, each with its official source | |
| Earnings, US: top 200 of the S&P 500 | SPY holdings (State Street) for membership; Yahoo Finance for market cap, dates and diluted EPS | Yahoo Finance |
| Earnings, Europe: top 200 of the STOXX Europe 600 | iShares STOXX Europe 600 ETF holdings for membership, each mapped to the company's main listing on Yahoo (`MAIN_LISTING`; the most traded class where the file holds two); Yahoo Finance for market cap (in dollars), dates and EPS | Yahoo Finance |
| Earnings, Asia: top 200 across Japan, Taiwan, South Korea, Hong Kong, mainland China, India | Yahoo Finance screener, one listing per company (mainland A-share for dual listings; Hong Kong for New York-primary Chinese companies; NSE in India; London-primary companies quoted in Hong Kong left out) | Yahoo Finance |
| First-session move, every earnings row | Yahoo Finance daily closes: the stock and its benchmark (S&P 500, STOXX Europe 600, Nikkei 225, TAIEX, KOSPI, Hang Seng, CSI 300, Nifty 50) | |

When a source fails, its events stay as last read and the Sources list on the
page shows the day of that copy; FRED being down keeps the last good figures,
dated the same way. A source that should always have rows in five weeks and
returns none counts as failed, so a changed page never empties the calendar.
Actual is the first print, taken within a week of the release, so a revision
or a later estimate never stands in for it. Add one-off events (OPEC+
meetings, Jackson Hole, debt-ceiling deadlines, elections) to `ONE_OFF` as
they are announced, with their source.

Each market follows its 200 largest companies (`UNIVERSE` in
`tools/calendar_data.py`); the rows marked High stay the largest 25 (US), 12
(Europe) and 5 (Asia), as before. Membership and market caps take a few batched
calls per market (50 symbols a call; Asia screens 220 listings per market).
The per-company calls, year-ago and reported EPS and the first-session moves,
are paced 0.3 seconds apart and share a time budget (`CAL_YAHOO_BUDGET`, 180
seconds by default): reports already out come first, a report still ahead is
not asked again once it has its year-ago figure, and whatever the budget does
not reach is fetched on the next run. With the Lab's 240-second budget for its
closes, the Yahoo work of a deploy stays under ten minutes even on the first
run with the larger lists, and falls to a minute or two once the caches are
warm.

The **Calendar check** workflow runs the fetcher against the live sources on
every pull request that touches it and prints what each source returned, with
an excerpt of any page that failed to parse.

## Placeholders still to fill

Everything in square brackets on the site is a placeholder, never invented
data (none is left: the copyright year is the build's year). The legal notice and privacy policy give the brand
contact, andramarkets@gmail.com (`tools/legal_content.py`), and no personal data: before
the site earns anything, the company (SL) that will run it replaces this with
its name, CIF and registered address (LSSI art. 10).
The Methodology page (`methodology()` in `tools/build_site.py`) describes the
note pipeline, sources and limits: update it when a source or check changes. The tape and the daily note module fill themselves
once the first close note is published.

Social channels live in `SOCIALS` at the top of `tools/build_site.py`: the
footer links to each channel with a URL. Nothing from them is embedded (the
Watch section was removed on 30 Oct 2026 so the site sets no third-party
cookies); `watch/` only sends old links to the home page; `learn/` (removed the same day) sends
each explainer to the section that covers it. Lab charts
are illustrative shapes until real data is wired in, and say so. The signup form is a
placeholder until the free newsletter launches on a newsletter platform
(Substack, Beehiiv or Ghost); it will then link there. See PRODUCT.md,
Business Model.

## Search engines, link previews and the feed

Link previews (LinkedIn, X, WhatsApp), canonical links, the sitemap, robots.txt
and the RSS feed all need the site's absolute address, so they turn on only
when the repository variable `SITE_URL` is set (**Settings → Secrets and
variables → Actions → Variables**, e.g. `https://andramarkets.com`, no
trailing slash). It is left empty until the site has its own domain, so the
GitHub account name is never written into the pages. Once it is set, every
deploy also writes, at the site root:

- `sitemap.xml`: every page except redirects (which carry `noindex`), close
  notes and FX analyses with their date as `lastmod`;
- `robots.txt`: allows everything and points to the sitemap;
- `feed.xml`: RSS 2.0 with the newest 40 close notes and Research Library
  reports (a report links to its PDF, as the library does); every page links
  to it in its head.

Whatever `SITE_URL` says, the homepage carries schema.org structured data for
the organisation and the site, and each close note an `Article` with its
publication time (the agent run's, from the note record); the absolute
fields (url, logo, image) are added only with `SITE_URL`.
`tools/check_site.py` fails the deploy if the three files are missing or
broken with `SITE_URL` set, or present without it.

To move to a domain: point its DNS at GitHub Pages, add it in **Settings →
Pages → Custom domain**, set `SITE_URL`, and add the domain to
`ALLOWED_ORIGINS` in `worker/wrangler.toml` (the company pages' live data),
then run **Deploy profile API** once. Submit `https://<domain>/sitemap.xml`
in Google Search Console and Bing Webmaster Tools.

## Licenses

- Schibsted Grotesk: SIL Open Font License 1.1 (`assets/fonts/OFL.txt`).
- Icons: Phosphor Icons (MIT), inlined as an SVG sprite.

## Simulators data

`tools/sim_data.py` runs at deploy, before the build, and writes one file per
data set to `.cache/sim/` (kept between runs by the workflow cache; each set
is fetched at most once a day and keeps its last good copy when a fetch
fails):

- `sp500.json`: every trading day since the end of 1927 with its total return.
  Daily closes from Yahoo Finance `^GSPC`; to the end of 1987 each month's
  dividend from Robert Shiller's data (via the `datasets/s-and-p-500`
  repository on GitHub) is added day by day as a yield; from 1988 the return
  is the S&P 500 Total Return index, `^SP500TR`.
- `nasdaq.json`, `stoxx50.json`, `nikkei.json`: daily price returns from Yahoo
  (`^IXIC` from 1971, `^STOXX50E` from 2007, `^N225` from 1965). Prices only.
- `fed.json`: monthly CPI, unemployment, the Fed's target and the 2-year
  yield from FRED (needs `FRED_API_KEY`), for Guess the Fed.
- `bonds.json`: the monthly 10-year Treasury yield (Shiller, then FRED GS10
  from 1953), turned into bond returns for the Portfolio Builder.

`build_site.py` packs them into `assets/simdata-<set>.js` (scripts, since the
deploy refuses JSON files); a page whose data is missing shows "Data
pending". Cash earns a flat 2% a year in every simulator. The episodes revealed
at the end of a game are in `tools/sim_content.py`, one list per region (US,
Japan, Europe), each covering every month of its history without gaps.
