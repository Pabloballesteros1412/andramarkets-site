# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Static site (`index.html`, `methodology/`, `reports/`, `dashboards/`, `assets/`), generated
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
an economic calendar; a daily US market close note; Learn (explainers for people
starting out); and Watch (TikTok videos; YouTube to follow once Andra has a channel). Success: visitors explore
a dashboard or tool, come back for the calendar and note, and subscribe by email.

## Positioning

One platform that serves professionals (dashboards, tools, calendar) and
newcomers (Learn, Watch) from the same automated pipeline, dated and on the
record. The daily note is one module among others, not the centrepiece.

## Operating Context

- The close note is tied to the US market close and published per trading day.
- Visitors arrive from LinkedIn and TikTok as well as direct links.
- Channels: LinkedIn https://www.linkedin.com/company/andramarkets/ and TikTok
  https://www.tiktok.com/@andramarkets. No YouTube channel yet.

## Capabilities and Constraints

- Modules: dashboards (11, each on real data: yield curve, Fed path, sector
  heatmap, volatility term structure, global indices, FX majors, commodities,
  credit spreads, inflation and labour, watchlist breadth, cross-asset
  correlation; an earnings season tracker returns once it has a real source;
  no illustrative dashboard tiles; a tile waiting for data says "Data pending"), Lab tools, economic calendar, daily close note,
  Learn, Watch.
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
- Published only as Andra Markets: no personal names anywhere on the site.
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
the economic calendar; Learn; Lab tools; Watch.

The site never offers downloads: no note PDF, no verified facts file, no data
behind the dashboards. This repo is public, so PDFs and full fact packs are
never committed here; they stay in the agent repo and its artifacts.

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
