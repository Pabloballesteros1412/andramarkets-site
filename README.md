# Andra Markets

The Andra Markets website: a markets research platform with dashboards, quant
tools, an economic calendar, a daily close note, explainers and videos.

- `assets/`: stylesheet, script, self-hosted font, brand mark.
- `tools/build_site.py`: generates every page from one shell. Edit markup here.
- `tools/import_notes.py`, `tools/nyse.py`: import the daily close notes (below).
- `data/notes/<date>.json`: one record per close note: its text and the ten
  closing levels for the tape. No PDF or facts file is ever stored here.
- `DESIGN.md`: the design system. Every page follows it.
- `PRODUCT.md`: product truth and brand commitments.
- `AGENT_FIXES.md`: known problems in the agent repo, to fix next.

The HTML pages (`index.html`, `methodology/`, `reports/`) are generated at
deploy time and are not stored in the repo. Pushes to `main` deploy to GitHub
Pages via `.github/workflows/pages.yml`, which builds the pages and publishes
only `index.html`, `methodology/`, `reports/` and `assets/`. To preview
locally: `python3 tools/build_site.py`.

## Publishing the close note

The agent in `Pabloballesteros1412/andramarkets` builds the note and uploads
its files as an Actions artifact. `.github/workflows/publish-notes.yml` in
this repo checks for new artifacts twice an hour from 20:00 to 02:59 UTC,
with a read-only token, and for each one:

- **publishes it** when it passes every check: it commits the note record
  (text and tape closes) to `main`, then deploys the site;
- **holds it in a pull request** titled "Held close note: <date>" when the
  date was not an NYSE trading day, is in the future, or the figure check
  failed. Merge to publish, close to discard;
- **rejects it** when files are missing or broken. Nothing is published and
  the run fails, so GitHub emails you.

A newer note for the same date replaces the older one. The PDF is read only to
run the figure check; it and the full facts file are never committed (this
repo is public) or offered on the site. They stay in the agent's artifacts. To publish at once:
**Actions** → **Publish close notes** → **Run workflow**.

To take a note down: open `data/notes/<date>.json` in the web editor, change
`"published": true` to `"published": false`, commit. The site rebuilds without
it. Later runs for that date keep it down until you set it back to `true`.

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
8. **Permissions** → **Repository permissions** → **Actions** → **Read-only**.
   Leave everything else on **No access** (Metadata: Read-only is added
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

## Placeholders still to fill

Everything in square brackets on the site is a placeholder, never invented
data: dashboard sources and dates, calendar values and company names, Lab
parameters and upcoming tools, video titles and durations, copyright year, and
the Methodology sections. The tape and the daily note module fill themselves
once the first close note is published.

Social channels live in `SOCIALS` and the Watch videos in `VIDEOS`, both at the
top of `tools/build_site.py`. Andra has no YouTube channel yet: set
`YOUTUBE_URL` and add `("YouTube", "wide")` to the front of `VIDEOS` to bring
back the footer link and the 16:9 frame; the Watch grid adapts by itself. All charts are illustrative
shapes until real data is wired in, and say so. The signup form is a
placeholder until the free newsletter launches on a newsletter platform
(Substack, Beehiiv or Ghost); it will then link there. See PRODUCT.md,
Business Model.

## Licenses

- Schibsted Grotesk: SIL Open Font License 1.1 (`assets/fonts/OFL.txt`).
- Icons: Phosphor Icons (MIT), inlined as an SVG sprite.
