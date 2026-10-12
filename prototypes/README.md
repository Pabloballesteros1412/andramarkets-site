# Homepage prototype

One page, two themes. Light is the default; the header toggle switches to dark
and the choice is remembered in the visitor's browser (`?theme=light|dark` also
sets it). Nothing here is the real site: no real data, no working sub-pages.

- `index.html`: the homepage.
- `cream/`, `dark/`: redirects from the first round's preview links to the
  matching theme.

Edit `tools/build_prototypes.py` (markup and chart shapes) and
`assets/site.css` / `assets/site.js`, then run
`python3 tools/build_prototypes.py` to regenerate.

## Sections

Hero, market tape (with a one-tap link to the latest close note), dashboards
(12, filterable by category), Lab (quant tools), economic calendar, daily close
note, Learn, Watch, about, subscribe, footer with LinkedIn, TikTok, YouTube.

## Placeholders to replace

Everything in square brackets is a placeholder, never invented data: market
levels `[live]`, dates and times, data vendor and sources, note headlines and
summaries, read times, calendar consensus/prior values and company names, Lab
tool parameters and upcoming tool names, video titles and durations, social
handles and URLs (links point to `#`), copyright year. Dashboard, explainer and
tool names and descriptions are proposals. All charts are illustrative shapes
from seeded random walks and are labelled as such. The video frames are embed
placeholders. The signup form is a front-end mock and sends nothing.

## Brand mark

`assets/andra-horse.png` is an unmodified copy of the repo's mark. In the light
theme it is shown with a CSS invert + grayscale + multiply treatment
(owner-approved for the prototype); the file itself is never recoloured or
cropped. A proper favicon crop still needs owner approval; the prototype uses
the full image.

## Licenses

- Schibsted Grotesk: SIL Open Font License 1.1 (`assets/fonts/OFL.txt`).
- Icons: Phosphor Icons (MIT), inlined as an SVG sprite.
