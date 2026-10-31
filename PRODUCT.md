# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Static site (`index.html`, `methodology/`, `reports/`, `research/`, `interview-prep/`, `fed-rates/`, `break-into-wall-street/`, `sources/`, `legal/`, `privacy/`, `dashboards/`, `assets/`), generated
by `tools/build_site.py` at deploy time and deployed to GitHub Pages from `main` by
`.github/workflows/pages.yml`. No framework, no build step beyond the generator.

## Users

Two audiences in equal measure:

- Finance recruiters and professionals judging the quality and seriousness of
  the research, usually on a laptop and often from a link on a CV or LinkedIn.
- Social media followers (LinkedIn, TikTok) arriving on a phone after
  a post or a clip, who want today's note and a reason to subscribe.

## Product Purpose

Andra Markets is a markets research platform. Its modules: interactive
dashboards across rates, equities, macro and cross-asset; a Lab of interactive
quant tools (momentum regime backtest explorer, options pricer, more to come);
an economic calendar; a daily US market close note; a Research Library; Fed & Rates; Markets Interview Prep; and
Break into Wall Street, a careers guide. Videos stay on
TikTok and LinkedIn: the site links to them and embeds nothing (owner, 30 Oct
2026: the Watch section was removed so the site sets no third-party cookies). Success: visitors explore
a dashboard or tool, come back for the calendar and note, and subscribe by email.

## Positioning

One platform that serves professionals (dashboards, tools, calendar) and
newcomers (Interview Prep, Break into Wall Street) from the same automated pipeline, dated and on the
record. The daily note is one module among others, not the centrepiece.

## Operating Context

- The close note is tied to the US market close and published per trading day.
- Visitors arrive from LinkedIn and TikTok as well as direct links.
- Channels: LinkedIn https://www.linkedin.com/company/andramarkets/ and TikTok
  https://www.tiktok.com/@andramarkets. No YouTube channel yet.

## Capabilities and Constraints

- Modules: dashboards (9, each on real data: sector
  heatmap, volatility term structure, global indices, FX majors, commodities,
  credit spreads, inflation and labour, watchlist breadth, cross-asset
  correlation; an earnings season tracker returns once it has a real source;
  no illustrative dashboard tiles; a tile waiting for data says "Data pending"), Lab tools, economic calendar, daily close note,
  Research Library, Fed & Rates, Interview Prep, Break into Wall Street. Learn
  was removed (owner, 30 Oct 2026); its addresses redirect.
- Fed & Rates (`fed-rates/`, owner-approved preview, 30 Oct 2026): its own
  section in the menu, not a dashboard; the Yield curve and Fed path dashboards
  were folded into it and their addresses redirect there. The target range and
  effective rate, the FOMC calendar with a countdown, next-meeting
  probabilities and the expected path (an Andra Markets calculation from CBOT
  fed funds futures, CME's FedWatch method), the Treasury curve 1M to 30Y
  against 1 week, 1 month and 1 year ago, 2s10s and 3m10y with inversion
  periods, the fed funds rate against CPI, core PCE and unemployment, and the
  10Y real yield with breakevens. Sources: the US Treasury and FRED (curve and
  history), the Federal Reserve, Yahoo Finance (futures and Cboe yield indices,
  delayed). Futures and four intraday yields refresh every 15 minutes while the
  NYSE is open; the rest daily. Owner accepted: no SOFR futures (no free
  source) and only four intraday points between official curves.
- Break into Wall Street (`break-into-wall-street/`, owner-approved preview,
  30 Oct 2026; renamed from Path to Wall Street, `careers/` redirects): a
  guide for students entering IB, S&T, asset management, equity research and
  hedge funds, especially from non-target universities and outside the US:
  the roles, a recruiting calendar, a one-page CV, networking with email
  templates, technical preparation, visas, certifications and resources. Its
  text lives in `data/path_to_wall_street.json`; it shows its "Last reviewed"
  date and is reviewed each quarter. The owner approved publishing after
  Claude's review.
  - Recruiting calendar (`break-into-wall-street/recruiting-calendar/`,
    owner-approved preview, 30 Oct 2026; replaced the timeline by academic
    year): US only (owner's choice), about 40 banks, boutiques, asset managers,
    hedge funds and trading firms, by date and by firm, from
    `data/recruiting_calendar.json`. No free source lists firms' dates and the
    aggregators' terms forbid reuse, so the file is kept by hand from each
    firm's own careers site. Each date comes from the firm's own site; a row
    not yet re-checked by hand says so (owner, 30 Oct 2026: publish now,
    re-check later); an expected window comes from the last cycle and says
    what it rests on; never an invented date.
  - Technical preparation (`break-into-wall-street/technicals/<topic>/`,
    owner-approved preview, 30 Oct 2026): nine training pages (accounting,
    valuation, LBO, M&A, markets, rates and the Fed, a stock pitch,
    brainteasers and mental maths, behavioural and fit), each with what to
    know, a worked example, practice cards whose progress stays in the
    browser, and common mistakes; Brainteasers adds a timed mental maths drill.
    Content in `data/technicals/`, reviewed before publishing.
- Calendar (real data, owner-approved 22 Oct 2026): five weeks of market-moving
  releases and events for the US, euro area, UK, Japan and China, central bank
  decisions, minutes and key speeches, Treasury note and bond auctions, NYSE
  holidays and early closes, options expiry, the S&P 500 rebalance, the Fed
  blackout and one-off events, plus the next report of the 200 largest S&P 500
  companies. Dates from each publisher's own schedule; times in New York and
  Madrid; Previous and Actual from FRED, Eurostat, the ECB, the ONS, the Bank
  of England and TreasuryDirect, each Actual linked to its release. No
  consensus forecasts (no reliable free source). Earnings: SPY holdings for
  membership, Yahoo Finance for market cap, dates and diluted EPS; an estimated
  date is never shown as confirmed and a report time Yahoo does not give is
  never guessed. A failing source keeps its last good copy with its date.
  Close notes link to their session's events from the calendar's first week.
  Earnings also cover the 200 largest STOXX Europe 600 companies (iShares
  holdings for membership) and the 200 largest listed in Japan, Taiwan, South
  Korea, Hong Kong, mainland China and India (Yahoo Finance, one listing each:
  the mainland A-share for dual listings, the Hong Kong listing for Chinese
  companies whose primary listing is in New York), ranked by market cap in
  dollars, with the report type when the EPS history makes it clear, EPS in the
  reporting currency, and every row's move on its first full session after the
  report against its benchmark.
- World markets (`world/`): 25 markets on one radar and eight measures (1M and
  YTD index return, 3M volatility, currency against the dollar, 10-year yield,
  GDP growth, inflation, unemployment), up to three compared, each figure with
  its official source and date (Yahoo Finance, OECD, World Bank, IMF); an axis
  with no free official figure stays empty.
- FX (`fx/`): the agent's daily FX analysis after the US close (the dollar,
  G10 majors, emerging markets, rate differentials, levels, what is ahead),
  latest on top with an archive by date, shown only when its figure check
  passed and its session's close note is published; and a table of the dollar
  index, majors and key EM pairs with their moves, linked to the FX dashboard.
- Research Library (`research/`, owner-approved 30 Oct 2026): the reports
  that are not the daily note, weekly market reviews and research, never the
  close notes (which keep their archive at `reports/`). Searchable and
  filtered by topic, newest first. Each report is published as its PDF, as it
  is, free to open and download (owner, 31 Oct 2026): the list links straight
  to the PDF, with its title, summary, date, page count and size; there is no
  web version of the text. Reports live in `data/reports/` (index.json plus
  one PDF each in `pdf/`, added by `tools/import_report.py`).
- Markets Interview Prep (`interview-prep/`, 30 Oct 2026): for students
  preparing for IB, S&T and asset management interviews. A weekly "What you
  need to know this week" block (five to seven topics, figures only from the
  week's close notes) and a question bank with model answers in six subjects,
  all from one file, `data/interview_prep.json`, updated weekly.
- Data sources, legal notice and privacy and cookies (`sources/`, `legal/`,
  `privacy/`), linked from the footer. The legal notice covers US, UK and EU
  readers. The operator's legal name, tax number, address and contact email
  are bracketed placeholders until the owner supplies them (Spanish law asks a
  site's publisher to identify itself).
- One site with a light (default) and dark theme, toggle remembered per visitor.
- Undecided: dashboard names and count, study list, data sources, publication
  time, newsletter platform (Substack, Beehiiv or Ghost), a YouTube channel.
  The site uses labelled placeholders until each is decided.

## Brand Commitments

- Name: Andra Markets. All copy in English.
- `andra-horse.png` is the brand mark (engraved rearing horse on black). Do not
  redraw, recolor, crop or replace it without owner approval. The owner
  approved showing it on light grounds via a CSS invert + grayscale + multiply
  treatment that leaves the file untouched.
- Published only as Andra Markets: no personal names anywhere on the site,
  the legal notice included (owner, 30 Oct 2026). While the site has no
  economic activity (no income, sales, ads, sponsorship or affiliate links)
  the legal notice and privacy policy name only Andra Markets and a brand
  contact email. Before any monetisation (newsletter sponsorship, paid tier)
  the owner will form a company (SL), and the legal notice will then carry
  its name, CIF and registered address as LSSI article 10 requires. Never
  publish the owner's own name, DNI or home address.
- Owner-approved derivatives of the mark: the favicon and touch icon are a
  head-and-neck crop (the owner asked for "a favicon (head and neck crop of the
  horse)" and approved it as shown); the social share image uses the full horse.
  No other crop is approved.
- Sans-serif only, everywhere, including fallbacks (CLAUDE.md rule 2).
- Owner approves visual decisions before real pages are built (CLAUDE.md rule 1).
  The homepage direction was approved as final; DESIGN.md is the system.
- Tone: premium and serious, never playful. References the owner likes for
  their principles (not their look): spacex.com, canyon.com, quartr.com.
- Red and green mean a rise or a fall, and nothing else: inside charts and on every figure that shows a move, always with its + or − sign; labels, prose and headings stay in ink (owner's rule, 22 Oct 2026).

## Evidence on Hand

- `andra-horse.png` (brand mark).
- The daily close notes, imported from the agent repo (`data/notes/`): the
  note text and the ten closing levels the tape shows, from Yahoo Finance and
  FRED. The note PDFs and full fact packs stay in the agent repo.
- No other market data, subscriber counts, testimonials or press exist yet.
  Never invent numbers: use placeholders such as `[live]` and `[date]`.

## Business Model

Recorded for direction only. **No paid feature is built yet.**

### Free tier (open to everyone, on this site)

The daily close note, readable on the web and shareable by link; dashboards;
the economic calendar; Lab tools; the Research Library; Fed & Rates;
Interview Prep; Break into Wall Street.

The site never offers downloads: no note PDF, no verified facts file, no data
behind the dashboards. Two exceptions: the Research Library publishes its
reports as PDFs (owner, 31 Oct 2026), and (owner, 30 Oct 2026) Fed & Rates
charts can be saved as a PNG image, made in the browser, carrying the mark,
the title, the source and the date; never the figures behind them. This repo is public, so PDFs and full fact packs are
never committed here, apart from the Research Library's report PDFs; they stay in the agent repo and its artifacts.

### Paid subscription (future, not built)

- An exclusive weekly report.
- A company deep dive every two weeks, produced with the research agent and
  reviewed by the owner, with a downloadable Excel valuation model.
- Earnings previews and reviews for major companies during earnings season.
- Subscriber polls to choose the next company to analyse.
- Extras: the full report archive, PDF downloads, the data downloads behind
  the dashboards (including the verified facts file), early access to Lab tools.
- **Never:** model portfolios or buy and sell lists (regulatory risk).

Delivery and payments run on a newsletter platform (Substack, Beehiiv or
Ghost, not chosen yet), linked from the site. No custom accounts, logins or
payments on this site.

An on-demand equity research agent is a possible later tier. Not planned now.

### Rollout

1. Launch a free newsletter carrying the daily note, to build an audience.
   The site's email signup links to the newsletter platform once it exists;
   until then it is a placeholder.
2. Open the paid tier later, only after legal advice on the rules for
   publishing investment research.

## Product Principles

1. On the record: every number is dated and sourced, or it is a placeholder.
2. Cadence is the product: the daily note is always one click away.
3. Serve both readers: a recruiter judges rigor in seconds; a follower finds
   today's note in one tap.
4. Restraint signals seriousness: little text per screen, no hype.

## Accessibility & Inclusion

WCAG 2.2 AA contrast; full keyboard support; motion honors
`prefers-reduced-motion`; must work well on phones.
