# Homepage prototypes

Two directions for owner approval. Same markup, copy and typeface; only the
mood differs. Nothing here is the real site.

- `cream/`: A. Cool off-white ground, the horse printed large as an engraving.
- `dark/`: B. Near-black ground, the horse large, dim and cinematic.
- `index.html`: chooser linking both.

Edit `tools/build_prototypes.py` (markup) and `assets/site.css` / `assets/site.js`,
then run `python3 tools/build_prototypes.py` to regenerate both pages.

## Placeholders to replace

Everything in square brackets is a placeholder, never invented data: market
levels and changes `[live]`, dates `[date]`, data vendor, note headline and
summary, read time, study sample/universe/method, data sources, social
handles and URLs (links point to `#`), copyright year. The four dashboard
names and descriptions are proposals. All charts are illustrative shapes from
a seeded random walk and are labelled as such. The signup form is a
front-end mock and sends nothing.

## Brand mark

`assets/andra-horse.png` is an unmodified copy of the repo's mark. On the cream
direction it is shown with a CSS `invert` + `multiply` blend (owner-approved for
the prototype); the file itself is never recoloured or cropped. A proper
favicon crop still needs owner approval; the prototypes use the full image.

## Licenses

- Schibsted Grotesk: SIL Open Font License 1.1 (`assets/fonts/OFL.txt`).
- Icons: Phosphor Icons (MIT), inlined as an SVG sprite.
