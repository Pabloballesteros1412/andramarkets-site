# Andra Markets

The Andra Markets website: a markets research platform with dashboards, quant
tools, an economic calendar, a daily close note, explainers and videos.

- `index.html`, `methodology/`: the published pages (generated, do not edit by hand).
- `assets/`: stylesheet, script, self-hosted font, brand mark.
- `tools/build_site.py`: generates every page from one shell. Edit markup here,
  then run `python3 tools/build_site.py`.
- `DESIGN.md`: the design system. Every page follows it.
- `PRODUCT.md`: product truth and brand commitments.

Pushes to `main` deploy to GitHub Pages via `.github/workflows/pages.yml`,
which publishes only `index.html`, `methodology/` and `assets/`.

## Placeholders still to fill

Everything in square brackets on the site is a placeholder, never invented
data: market levels `[live]`, dates and times, data vendor and sources, note
headlines and summaries, read times, calendar values and company names, Lab
parameters and upcoming tools, video titles and durations, TikTok and YouTube
handles, copyright year, and the Methodology sections. Set `LINKEDIN_URL` in
`tools/build_site.py` to Andra's LinkedIn page. All charts are illustrative
shapes until real data is wired in, and say so. The signup form is front-end
only until an email provider is connected.

## Licenses

- Schibsted Grotesk: SIL Open Font License 1.1 (`assets/fonts/OFL.txt`).
- Icons: Phosphor Icons (MIT), inlined as an SVG sprite.
