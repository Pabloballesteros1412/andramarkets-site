# Plan: publish the daily close note on the site

Status: **approved and built.** Owner decisions: pull approach; held notes
open a pull request; a newer note replaces an older one for the same date;
page sketches approved; facts JSON offered as a download; live data Stage 1
now, Stage 2 later; backfill the last 90 days, with anything that fails a
check held for review. Setup steps live in README, Publishing the close note.
Agent repo problems are tracked in AGENT_FIXES.md.

---

## 1. What the agent produces today

I read `Pabloballesteros1412/andramarkets` (`andramarkets-agent/` and
`.github/workflows/`). Findings that shape the plan:

- **Trigger.** `daily-close.yml` runs on **Run workflow only** (no schedule).
  Every run passes `--force`. Recent runs land around 20:45 to 21:45 UTC.
- **Output.** Every successful run uploads one Actions artifact named
  `andramarkets-<run id>` (about 3 MB, kept 90 days) holding `out/`:

  | File | Use on the site |
  |---|---|
  | `AndraMarkets_Close_YYYYMMDD.pdf` | the note, published as a download |
  | `note_YYYYMMDD.json` | headline, standfirst, takeaways, desk view, watching, section text |
  | `facts_YYYYMMDD.json` | verified fact pack: session date, levels and changes for the tape |
  | `series_YYYYMMDD.json` | S&P 500 intraday closes (optional chart later) |
  | LinkedIn PDF, TikTok PNGs, captions | **not published on the site** |

- **Figure check.** If the audit fails twice, the PDF still ships, with a
  "Control note." paragraph in the disclaimer. Nothing in the JSON says so.
- **Date risk.** With `--force` the note is dated with today's New York date.
  Two runs on Saturday 3 October produced notes dated a Saturday. The site
  must not publish a note dated on a day NYSE did not trade.
- **Unrelated, for your information.** `build_video_data.py` sits in
  `.github/workflows/andramarkets-agent/video/` instead of
  `andramarkets-agent/video/`, so the video step fails silently every run
  (it is `continue-on-error`).

---

## 2. How to connect the two repos

### Option A: the agent pushes to this repo

The agent workflow gets a token that can **write** to `andramarkets-site` and
commits the PDF and JSON after each run.

- Instant publication.
- Needs a change to the agent workflow now.
- The write token lives in the agent's runner, which also runs `pip install`,
  Playwright and `npm install` (a large third-party tree). If any of that is
  ever compromised, the token can rewrite the public site.

### Option B (recommended): this repo pulls from the agent

A new workflow in `andramarkets-site` checks the agent's latest artifacts on a
schedule, takes only the files it needs, validates them, commits them here and
deploys.

- **Least privilege.** The only cross-repo secret is **read-only** access to
  the agent's Actions artifacts. Write access never leaves this repo (it uses
  this repo's own built-in `GITHUB_TOKEN`).
- **The public site decides what goes public.** Validation runs on the site
  side, in code with no third-party dependencies beyond `pypdf`.
- **No agent change needed.** Works with the agent exactly as it is.
- **Cost:** up to about 30 minutes of delay after a run (schedule), or
  immediate if you click **Run workflow** on the site's Actions tab.
- Artifacts expire after 90 days, so every note is copied into this repo
  permanently. That also lets us **backfill** the notes from roughly the last
  90 days on the first run (you choose which).

Option C, a GitHub App, is the most "correct" but needs a private key and an
installation flow that is awkward without a terminal. Not worth it here.

### Recommended flow (Option B)

```
agent run (you click Run workflow in andramarkets)
  └─ uploads artifact andramarkets-<run id>
site workflow "Publish close notes" (every 30 min, 20:00 to 02:00 UTC, Mon to Sat; or Run workflow)
  1. list agent artifacts newer than the last one imported   (read-only token)
  2. download the zip, extract only the 3 named files (no other paths)
  3. validate, else hold:
       - PDF starts with %PDF and is under 20 MB
       - JSON parses; headline and session date present
       - session date is an NYSE trading day, not in the future
       - PDF text has no "Control note." (figure check passed)
  4. passed  → commit to main: reports/<date>/note.pdf + data/notes/<date>.json
     held    → open a pull request instead, so you review and click Merge
  5. run tools/build_site.py and deploy GitHub Pages (same job, see note)
```

Notes on the details:

- **Pushes made by a workflow do not trigger other workflows.** So the publish
  workflow deploys Pages itself (it calls the existing `pages.yml` as a
  reusable workflow) instead of relying on the push.
- **Same date twice** (a re-run or a correction): the newer run replaces the
  older one and the report page shows its edition number. Tell me if you would
  rather keep the first and hold the second for review.
- **Removing a note:** in the web editor open `data/notes/<date>.json`, change
  `"published": true` to `false`, commit. The site rebuilds without it.
- **Text safety:** all model-written text is HTML-escaped before it reaches a
  page. Captions and the LinkedIn/TikTok copy never enter this repo.
- Two runs can never race: the workflow uses a concurrency group.

### Later, small agent change (separate approval)

Not needed for launch, but worth doing next:

1. Write `manifest_YYYYMMDD.json` with session date, edition, `audit_ok` and
   model or quantitative mode, so the site stops reading the PDF text for the
   "Control note" check.
2. Under `--force`, date the note with the last closed session instead of
   today (fixes the Saturday notes).
3. Move `build_video_data.py` to where the workflow expects it.

---

## 3. Secrets and exactly what to click

Everything below is in the GitHub web UI. About five minutes.

**Step 1. Create the read-only token**

1. Top right avatar → **Settings** → left sidebar, bottom → **Developer
   settings** → **Personal access tokens** → **Fine-grained tokens** →
   **Generate new token**.
2. Token name: `andramarkets-site: read agent artifacts`.
3. Expiration: **Custom**, one year from today. Put a reminder in your
   calendar a week before. (If it expires, the workflow fails and GitHub emails
   you; nothing breaks on the live site.)
4. Resource owner: **Pabloballesteros1412**.
5. Repository access: **Only select repositories** → `andramarkets` (the
   agent repo, *not* the site).
6. Permissions → **Repository permissions** → **Actions: Read-only**.
   Leave everything else at **No access**. (Metadata: Read-only is added
   automatically.)
7. **Generate token**, then copy it (shown once).

**Step 2. Store it in the site repo**

1. Open `andramarkets-site` → **Settings** → **Secrets and variables** →
   **Actions** → **New repository secret**.
2. Name: `AGENT_ARTIFACTS_TOKEN`. Secret: paste the token. **Add secret**.

**Step 3. Allow the workflow to open review pull requests** (for held notes)

1. `andramarkets-site` → **Settings** → **Actions** → **General**.
2. Under **Workflow permissions**, tick **Allow GitHub Actions to create and
   approve pull requests**. Leave the radio on **Read repository contents and
   packages permissions**: the workflow asks for write access in its own file,
   only for its own job.
3. **Save**.

**Step 4. Check two settings that should already be right**

- **Settings** → **Pages** → Source: **GitHub Actions**.
- Avatar → **Settings** → **Notifications** → **Actions**: on, so a failed
  publish reaches your inbox.

Nothing to click in the agent repo. If you later protect `main` with a rule
that requires pull requests, add **GitHub Actions** to the bypass list or
every note will become a pull request.

**Daily use:** run the agent as you do now. The note appears on the site within
30 minutes. To publish at once: site repo → **Actions** → **Publish close
notes** → **Run workflow**.

---

## 4. What gets built (design proposal, needs your approval)

Everything uses existing DESIGN.md components and tokens only: no new colours,
type sizes, components or motion. Proposed for your yes or no.

### Home page

- **Daily close note module:** the latest note's headline (`note__title`), its
  standfirst as the summary, date and read time (computed from the word
  count), "Read the note" → the report page. Archive column: the three
  previous notes as ruled rows (date | headline | arrow). "All notes" →
  `/reports/`.
- **Tape link** "Latest close note, [date]: [headline]" → the latest report.
- Before the first note exists, the current placeholders stay.

### Archive page `/reports/`

Inner page (`.page`), same header and footer.

```
Daily close notes                                  ← page title
Every US trading day, after the close. [n] notes.  ← lede (ink-2)
════════════════════════════════════════════════   ← rule-strong
October 2026                                       ← month row, like a calendar day row
 9 Oct   Headline of the note ................  →  ← note-list row, same as home
 8 Oct   Headline of the note ................  →
 6 Oct   ...
September 2026
 ...
```

One page holds every note (about 250 a year, a light list). Mobile stacks date
over headline, exactly as the home archive does.

### Report page `/reports/2026-10-09/`

```
Thursday 9 October 2026   Edition 0031   6 min read      ← meta row (ink-2, 20px gaps)
Headline of the note                                     ← page title
Standfirst, two sentences.                               ← lede
[ Download the PDF  ↓ ]   Previous note  ·  Next note    ← primary button, text links
════════════════════════════════════════════════
Takeaways        ruled list of four
Desk view        two paragraphs
What we watch    ruled list of four
Equities · Rates · Credit · FX · Commodities · Volatility · Digital · International · Correlation
                 one section each, h2 + paragraphs, as the inner page body
────────────────────────────────────────────────
Sources: Yahoo Finance, FRED. Every figure checked against the session's
verified fact pack. For information only. Not investment advice.
```

- The PDF is linked, not embedded: embedded PDFs are poor on phones and slow
  everywhere, and the HTML text reads well on a phone.
- Tables and exhibits stay in the PDF.
- Each report page gets its own title and description for link previews,
  reusing the approved share image.
- **Question:** also offer the verified facts JSON as a download, as a signal
  of rigour for recruiters? It is small and already public data.

### Nav

No new top-level nav item now. "All notes" on the home page and a footer link
reach the archive. Tell me if you want "Notes" in the header.

---

## 5. Live market data on the home page (free sources)

The tape shows 10 instruments: S&P 500, Nasdaq 100, Russell 2000, Euro Stoxx
50, Nikkei 225, VIX, US 10Y yield, EUR/USD, WTI crude, Gold.

One honest constraint first: **real-time and intraday index data is licensed**
(S&P, Nasdaq, Stoxx, Nikkei). Free intraday APIs (Twelve Data, Finnhub, Alpha
Vantage, Yahoo) forbid or don't grant public redistribution on their free
tiers, and putting a key in the browser exposes it to anyone. So for a free
site that stays on the record, the right unit is **the official close**,
clearly dated.

### Stage 1 (recommended, ships with the archive): the closing tape

Fill the tape from the latest note's `facts` file: the closing level and daily
change for all 10 instruments, already pulled by the agent from Yahoo and FRED
and already checked. The head reads "Markets [date], 4:00 pm ET" with the
source line "Close and daily change. Source: Yahoo Finance, FRED". Zero new
dependencies, zero new secrets, and every number is dated and sourced.

### Stage 2 (optional, separate approval): refresh between notes

A small scheduled workflow in this repo, three times per trading day, that
updates a `tape.json` from **official, public-domain or openly licensed daily
sources**, so the tape stays current on days without a note:

| Instrument | Free source | Terms |
|---|---|---|
| US 10Y yield | US Treasury daily par yield curve | public domain |
| EUR/USD | ECB euro reference rates | free reuse with attribution |
| WTI crude | EIA spot price API | public domain, free key |
| VIX | Cboe historical VIX CSV | free download |
| S&P 500 | FRED `SP500` (daily close) | free key, S&P notice required |
| Nasdaq 100, Russell 2000, Euro Stoxx 50, Nikkei 225, Gold | no clean free source | stay on the agent's close |

Each item shows its own date, so a mixed tape never pretends to be one
snapshot.

### Not recommended: embedded widgets

TradingView's free ticker tape widget is truly live and licensed for display,
but it loads third-party scripts and trackers, carries their branding, uses
red and green in UI text and cannot take our font or tokens. It breaks
DESIGN.md in several places.

---

## 6. Build order once approved

1. `tools/build_site.py`: read `data/notes/*.json`; render home module,
   archive page, report pages; fill the tape from the latest facts.
2. `tools/import_notes.py`: download, validate, hold or accept (stdlib plus
   `pypdf`).
3. `.github/workflows/publish-notes.yml`, and `pages.yml` made reusable and
   extended to publish `reports/`.
4. Backfill the existing notes from the last 90 days (you pick which).
5. Screenshots of both themes, desktop and phone, for your sign-off before
   merging.

## 7. Decisions I need from you

1. Option B (site pulls, read-only token)? **Recommended.**
2. Held notes (failed figure check, non-trading date) open a pull request for
   you to merge. OK?
3. Same session date twice: newer replaces older? (Recommended.)
4. The archive and report page layouts in section 4, as sketched.
5. Publish the facts JSON next to the PDF: yes or no?
6. Live data: Stage 1 now; Stage 2 later or never?
7. Backfill: all notes in the last 90 days, or start from the next run?
