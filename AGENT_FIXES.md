# Agent repo fixes (next phase)

Problems found while connecting `Pabloballesteros1412/andramarkets` (the
daily close agent) to this site. Nothing here has been changed in the agent
repo yet. The site already works around each one, as noted.

## 1. `--force` dates the note with today's date, even on a weekend

`.github/workflows/daily-close.yml` always runs `python run_daily.py --force`.
In `run_daily.py`, `--force` skips `_session_date()` and uses
`ny.date()`, the current New York date. Two runs on Saturday 3 October 2026
therefore produced notes dated Saturday, holding Friday's data.

- **Fix:** under `--force` without `--date`, use `_session_date(ny)` (the last
  closed session), and keep only the dedup and publish-window gates skipped.
- **Site today:** a note dated on a day NYSE did not trade is held as a pull
  request, never published directly.

## 2. The figure check result is only visible inside the PDF

When the figure audit fails twice, the PDF gets a "Control note." paragraph
and the email subject a `[REVIEW: figure check]` flag. Nothing in the JSON
files records it, and the edition number is not in any JSON either.

- **Fix:** write `manifest_YYYYMMDD.json` next to the other outputs:
  `{"date", "edition", "audit_ok", "unsupported", "mode": "model" | "quantitative", "demo": false}`.
- **Site today:** reads the PDF text, holds the note if it finds "Control
  note", and reads "Edition NNNN" from the PDF. Once the manifest exists the
  importer should read it instead (a small change in `tools/import_notes.py`).

## 3. The daily workflow has no schedule

`daily-close.yml` has only `workflow_dispatch`, although the README and
`run_daily.py` describe two cron windows. Every note is published only when
someone clicks Run workflow.

- **Fix (owner decision):** add the two UTC crons and drop `--force` from the
  scheduled path, so the session and dedup gates apply.
- **Site today:** checks for new notes twice an hour from 20:00 to 02:59 UTC
  every day, so either way works.

## 4. The video step fails silently on every run

`build_video_data.py` sits at
`.github/workflows/andramarkets-agent/video/build_video_data.py`, but the
workflow runs it from `andramarkets-agent/video/`. The step is
`continue-on-error`, so the run still shows green.

- **Fix:** move the file to `andramarkets-agent/video/build_video_data.py`.

## 5. PDFs and fact packs expire after 90 days (priority)

The `andramarkets-<run id>` artifact is deleted after 90 days. The site keeps
only the note text and the tape closes, never the PDF or the full facts file
(this site repo is public). So today the artifact is the only copy of each
PDF and fact pack, and they disappear after 90 days. The paid tier will need
them (full archive, PDF and data downloads).

- **Fix:** keep a permanent private copy in the agent repo, for example a step
  that commits `AndraMarkets_Close_*.pdf` and `facts_*.json` to an
  `archive/YYYY/` folder in the private agent repo after each run (or uploads
  them as assets on a private release). Do this before the oldest notes
  expire: on 12 October 2026 the agent repo held 66 note artifacts, the
  oldest from 20 August 2026, which expires around 18 November 2026.
- **Stopgap:** the agent repo is private, so its artifact retention can be
  raised to 400 days (agent repo Settings → Actions → General → Artifact and
  log retention, plus `retention-days: 400` on the upload step). That only
  affects new artifacts and is not a permanent archive.
