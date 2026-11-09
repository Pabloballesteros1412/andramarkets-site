# Research Library inbox

Drop a report PDF here, on `main`, and it is published on its own: the
`Publish reports` workflow reads the cover (report number, date, title, the
paragraph under the title and the category line), moves the PDF to
`data/reports/pdf/`, adds it to the library and deploys the site.

On github.com: open this folder, **Add file → Upload files**, drop the PDFs,
**Commit changes**. The library shows them a few minutes later.

To set any field yourself, add a JSON file with the same name next to the
PDF, for example `AndraMarkets_2026-110_Topic.json`:

    {"title": "...", "summary": "...", "tags": ["equities", "rates"]}

Fields: `title`, `summary` (up to 220 characters), `tags` (any of
`equities`, `rates`, `fx`, `commodities`, `macro`, `credit`), `date`
(YYYY-MM-DD), `slug`, `type` (`research` or `weekly`). The slide-style
covers cannot be read and need one with at least `date`, `slug` and `title`.

A PDF identical to a published one is dropped. A new file for a report
already published (same slug) replaces it. A PDF that cannot be read stays
here, and the workflow fails so GitHub emails you.
