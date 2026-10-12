# Agent repo fixes (next phase)

Problems found while connecting `Pabloballesteros1412/andramarkets` (the
daily close agent) to this site. Nothing here has been changed in the agent
repo yet. Item 1 is urgent and has a deadline; items 2 and 3 decide how much
of each day's note can be published. The site works around the rest, as noted.

## 1. Archive every PDF and fact pack permanently (urgent, before 18 November 2026)

The `andramarkets-<run id>` artifact is deleted after 90 days. The site keeps
only the note text and the tape closes, never the PDF or the full facts file
(this site repo is public). So today the artifact is the only copy of each
PDF and fact pack, and they disappear after 90 days. The paid tier will need
them (full archive, PDF and data downloads).

- **Deadline:** on 12 October 2026 the agent repo held 66 note artifacts, the
  oldest from 20 August 2026, which expires around **18 November 2026**. Each
  later note expires 90 days after its run. Retention cannot go above 90 days
  on this plan, so there is no stopgap: only a permanent copy helps.
- **Fix, two parts:**
  1. **Every new run:** a step in `daily-close.yml`, after "Build and
     publish", that commits `out/AndraMarkets_Close_*.pdf` and
     `out/facts_*.json` to `archive/YYYY/` in the private agent repo, next to
     the existing "Save publish state" commit (the workflow already has
     `contents: write`).
  2. **Backfill, once:** a manual workflow in the agent repo that downloads
     every unexpired `andramarkets-*` artifact with its own `GITHUB_TOKEN`
     (`actions: read`) and commits the same two files from each to
     `archive/YYYY/`. Run it well before 18 November.
- Never copy these files to `andramarkets-site`: that repo is public.

## 2. The figure check fails on most days

Between 20 August and 9 October 2026, 38 dates have at least one run. On 24 of
them the run the site would use carries the "Control note." (the figure audit
failed twice). The site holds every one of them as a pull request, so they
reach the site only if you merge them. Each "[REVIEW: figure check]" email names the unsupported figures.

- **Fix:** look at which figures fail most (likely rounding, derived values
  such as ratios and spreads, or figures the fact pack does not carry) and
  either add them to `fact_pack()` or widen the audit's tolerance for them.

## 3. Truncated replies are published as if complete

Several runs printed a note whose text stops mid-sentence and drops every later
section, for example 4 September ("The Nasdaq 100 added 0.", then nothing) and
15 September at 21:20 ("The dollar firmed against"). The model's reply was cut
off, probably by the token limit, and the run went on. The text is missing from
the artifact itself, so nothing can recover it.

- **Fix:** in `narrative.py`, treat `stop_reason == "max_tokens"` or a reply
  missing any section as a failure: retry, then fall back to
  `write_without_model()` rather than printing a partial note.
- **Site today:** a note with a missing or very short section is held as
  "incomplete", never published directly.

## 4. Note text was not saved before 15 September 2026

`note_YYYYMMDD.json` only exists from the run of 15 September 2026, 21:20
UTC. The 43 earlier artifacts carry the text only inside the report PDF.

- **Site today:** recovers it from the PDF (exact on every later run where both
  exist) and holds it for review. No agent change is needed now that the file
  is saved, but keep saving it: the site prefers it to the PDF.

## 5. Several runs per day, some before the close

Some days have up to six runs, including quantitative-mode runs, a run that
finished at 00:24 ET dated that same day (its figures are the previous
session's), and a Saturday-dated run. Fixing item 6 and scheduling (item 8)
removes most of this.

- **Site today:** keeps one note per date, holds runs made before the close.

## 6. `--force` dates the note with today's date, even on a weekend

`.github/workflows/daily-close.yml` always runs `python run_daily.py --force`.
In `run_daily.py`, `--force` skips `_session_date()` and uses
`ny.date()`, the current New York date. Two runs on Saturday 3 October 2026
therefore produced notes dated Saturday, holding Friday's data.

- **Fix:** under `--force` without `--date`, use `_session_date(ny)` (the last
  closed session), and keep only the dedup and publish-window gates skipped.
- **Site today:** a note dated on a day NYSE did not trade is held as a pull
  request, never published directly.

## 7. The figure check result is only visible inside the PDF

When the figure audit fails twice, the PDF gets a "Control note." paragraph
and the email subject a `[REVIEW: figure check]` flag. Nothing in the JSON
files records it, and the edition number is not in any JSON either.

- **Fix:** write `manifest_YYYYMMDD.json` next to the other outputs:
  `{"date", "edition", "audit_ok", "unsupported", "mode": "model" | "quantitative", "demo": false}`.
- **Site today:** reads the PDF text, holds the note if it finds "Control
  note", and reads "Edition NNNN" from the PDF. Once the manifest exists the
  importer should read it instead (a small change in `tools/import_notes.py`).

## 8. The daily workflow has no schedule

`daily-close.yml` has only `workflow_dispatch`, although the README and
`run_daily.py` describe two cron windows. Every note is published only when
someone clicks Run workflow.

- **Fix (owner decision):** add the two UTC crons and drop `--force` from the
  scheduled path, so the session and dedup gates apply.
- **Site today:** checks for new notes twice an hour from 20:00 to 02:59 UTC
  every day, so either way works.

## 9. The video step fails silently on every run

`build_video_data.py` sits at
`.github/workflows/andramarkets-agent/video/build_video_data.py`, but the
workflow runs it from `andramarkets-agent/video/`. The step is
`continue-on-error`, so the run still shows green.

- **Fix:** move the file to `andramarkets-agent/video/build_video_data.py`.
