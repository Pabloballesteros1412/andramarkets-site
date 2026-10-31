# Research Library sources

Weekly market reviews and research reports for the Research Library
(`/research/`). Daily close notes are not part of it: they come from
`data/notes/` and keep their own archive at `/reports/`.

The Research Library publishes each report as its PDF, as it is (owner,
31 Oct 2026). `index.json` lists the reports; `pdf/<slug>.pdf` holds each
PDF. `tools/build_site.py` copies the PDFs to `/research/pdf/` at deploy
time and the library page links to them, newest first. These are the only
PDFs the repo keeps and the deploy publishes: `.gitignore` and the deploy
check in `pages.yml` refuse every other PDF.

## Adding a report

1. Copy the PDF and add its line to the index in one step:

       python3 tools/import_report.py path/to/report.pdf --type research \
         --date 2026-10-30 --slug 2026-77-big-oil \
         --title "Big Oil’s Windfall Quarter" \
         --summary "One or two sentences." --tags equities,commodities

   This writes `data/reports/pdf/<slug>.pdf` and adds the entry, with its
   page count, to `index.json`.

2. Or by hand: put the PDF at `data/reports/pdf/<slug>.pdf` and add one line
   to the `reports` list in `index.json`:

       {"slug": "2026-77-big-oil", "date": "2026-10-30", "type": "research",
        "title": "...", "summary": "...", "tags": ["equities"], "pages": 5}

- `type`: `weekly` (Weekly market review) or `research` (Research).
- `tags`: any of `equities`, `rates`, `fx`, `commodities`, `macro`, `credit`.
- `summary`: about two lines on the page (up to 220 characters).
- `slug`: lower case letters, digits and hyphens; the PDF is published at
  `/research/pdf/<slug>.pdf`. Slugs here start with the report number.
- `pages`: the page count, shown with the file size.
- `"published": false` takes a report down without deleting it.

A report without its PDF is skipped at build time.
