# Andra Markets

The Andra Markets website: a markets research platform with dashboards, quant
tools, an economic calendar, a daily close note, explainers and videos.

- `assets/`: stylesheet, script, self-hosted font, brand mark.
- `tools/build_site.py`: generates every page from one shell. Edit markup here. It also writes `assets/search-index.js` (the header search index, not committed).
- `tools/import_notes.py`, `tools/nyse.py`: import the daily close notes (below).
- `tools/dashboard_data.py`: fetches the dashboard figures at deploy time (below).
- `tools/company_data.py`: fetches the figures behind the company pages (the 50 largest S&P 500 companies) at deploy time, into `.cache/companies/`.
- `tools/calendar_data.py`: fetches the calendar at deploy time (below).
- `assets/calendar.js`: the calendar's week tabs, filters and today mark.
- `tools/make_mark.py`: makes the transparent header and footer marks from `andra-horse.png`.
- `data/notes/<date>.json`: one record per close note: its text and the ten
  closing levels for the tape. No PDF or facts file is ever stored here.
- `DESIGN.md`: the design system. Every page follows it.
- `PRODUCT.md`: product truth and brand commitments.
- `AGENT_FIXES.md`: known problems in the agent repo, to fix next.

The HTML pages (`index.html`, `methodology/`, `reports/`, `dashboards/`, `calendar/`) are generated at
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
| Yield curve | FRED Treasury yields (DGS1MO to DGS30), latest against 1M to 1Y before; the agent archive's copy while FRED is down | The curve's own session |
| Fed path | CME 30-day fed funds futures via Yahoo Finance (100 minus price), effective rate from FRED | Latest settled session |
| Sector heatmap, FX majors | Yahoo Finance: sector ETFs, spot FX; changes over 1D to 1Y | Latest close |
| Volatility term structure | Cboe VIX9D, VIX, VIX3M, VIX6M via Yahoo Finance, against 5 sessions before | Latest close |
| Global indices | Yahoo Finance, each at its own latest local close | Newest of those closes |
| Commodities | WTI and gold front-month futures via Yahoo Finance, rebased to 100 | Latest settled session |
| Credit spreads | ICE BofA US high yield and corporate OAS via FRED | Latest observation |
| Inflation and labour | BLS CPI (year on year) and payrolls via FRED | Latest month |
| Cross-asset correlation | 60 sessions of daily returns: S&P 500, TLT, dollar index, WTI, gold, Yahoo Finance | Last session |
| Watchlist breadth | Agent archive: advancers less decliners across the Andra Markets watchlist of US large caps, every published session | Newest published session |

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

## FRED API key

The dashboards and the calendar read FRED through its official API
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
| Earnings, US: top 100 of the S&P 500 | SPY holdings (State Street) for membership; Yahoo Finance for market cap, dates and diluted EPS | Yahoo Finance |
| Earnings, Europe: top 50 of the STOXX Europe 600 | iShares STOXX Europe 600 ETF holdings for membership, each mapped to the company's main listing on Yahoo (`MAIN_LISTING`; the most traded class where the file holds two); Yahoo Finance for market cap (in dollars), dates and EPS | Yahoo Finance |
| Earnings, Asia: top 20 across Japan, Taiwan, South Korea, Hong Kong, mainland China, India | Yahoo Finance screener, one listing per company (mainland A-share for dual listings; Hong Kong for New York-primary Chinese companies; NSE in India; London-primary companies quoted in Hong Kong left out) | Yahoo Finance |
| First-session move, every earnings row | Yahoo Finance daily closes: the stock and its benchmark (S&P 500, STOXX Europe 600, Nikkei 225, TAIEX, KOSPI, Hang Seng, CSI 300, Nifty 50) | |

When a source fails, its events stay as last read and the Sources list on the
page shows the day of that copy; FRED being down keeps the last good figures,
dated the same way. A source that should always have rows in five weeks and
returns none counts as failed, so a changed page never empties the calendar.
Actual is the first print, taken within a week of the release, so a revision
or a later estimate never stands in for it. Add one-off events (OPEC+
meetings, Jackson Hole, debt-ceiling deadlines, elections) to `ONE_OFF` as
they are announced, with their source.

The **Calendar check** workflow runs the fetcher against the live sources on
every pull request that touches it and prints what each source returned, with
an excerpt of any page that failed to parse.

## Placeholders still to fill

Everything in square brackets on the site is a placeholder, never invented
data: Lab
parameters and upcoming tools, video titles and durations, copyright year, and
the Methodology sections. The tape and the daily note module fill themselves
once the first close note is published.

Social channels live in `SOCIALS` and the Watch frames in `VIDEOS`, both at the
top of `tools/build_site.py`. The Watch page (`watch/`) shows TikTok's official
creator embed (the account's videos, newest first) until `TIKTOK_VIDEOS` lists
videos by id, title and date; then each plays in TikTok's official embed player. Andra has no YouTube channel yet: set
`YOUTUBE_URL` and add `("YouTube", "wide")` to the front of `VIDEOS` to bring
back the footer link and the 16:9 frame; the Watch grid adapts by itself. Lab and Learn charts
are illustrative shapes until real data is wired in, and say so. The signup form is a
placeholder until the free newsletter launches on a newsletter platform
(Substack, Beehiiv or Ghost); it will then link there. See PRODUCT.md,
Business Model.

## Licenses

- Schibsted Grotesk: SIL Open Font License 1.1 (`assets/fonts/OFL.txt`).
- Icons: Phosphor Icons (MIT), inlined as an SVG sprite.
