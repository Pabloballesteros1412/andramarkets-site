# Research Library sources

Weekly market reviews and research reports for the Research Library
(`/reports/`). Daily close notes are not listed here: they come from
`data/notes/` and join the library on their own.

This folder is read by `tools/build_site.py` at deploy time and is never
published as it is: the deploy refuses JSON and PDF files, and the repo is
public, so a report's PDF never goes in here (`*.pdf` is ignored by git).

## Adding a report

1. Convert the PDF to text and add its line to the index in one step:

       python3 tools/import_report.py path/to/report.pdf --type weekly \
         --date 2026-10-30 --title "The week the 10-year reached 5%" \
         --summary "One or two sentences." --tags equities,rates,fx

   This writes `data/reports/<slug>.md` and adds the entry to `index.json`.
   Read the Markdown once: PDF tables and charts do not survive the
   conversion, so tidy or drop them.

2. Or by hand: write `data/reports/<slug>.md` and add one line to the
   `reports` list in `index.json`:

       {"slug": "weekly-2026-10-30", "date": "2026-10-30", "type": "weekly",
        "title": "...", "summary": "...", "tags": ["equities", "rates"]}

- `type`: `weekly` (Weekly market review) or `research` (Research).
- `tags`: any of `equities`, `rates`, `fx`, `commodities`, `macro`, `credit`.
- `summary`: about two lines on the page (up to 220 characters).
- `slug`: lower case letters, digits and hyphens; it becomes
  `/reports/<slug>/`. It must not be a bare date (those are close notes).
- `"published": false` takes a report down without deleting it.

## The Markdown the site reads

`## Heading` starts a section, a blank line separates paragraphs, lines
starting `- ` make a ruled list, `**bold**` is bold. A line starting
`Source:` is set as a source line. Nothing else is interpreted.
