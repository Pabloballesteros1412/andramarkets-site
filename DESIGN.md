---
name: Andra Markets
description: A markets research platform on the record. Black ground, light Geist type, words and hairlines instead of boxes, a horizon of light and the engraved horse, red and green only for rises and falls.
colors:
  ground: "#000000"
  ground-2: "#0c0d0e"
  ink: "#f2f3f3"
  ink-2: "#a3a8aa"
  ink-3: "#74797c"
  rule: "rgba(242, 243, 243, 0.10)"
  rule-strong: "rgba(242, 243, 243, 0.26)"
  btn-bg: "#f2f3f3"
  btn-fg: "#000000"
  btn-hover: "#ffffff"
  plate: "#0b0c0d"
  plate-2: "#121415"
  plate-hover: "#1a1c1e"
  plate-ink: "#f2f3f3"
  plate-ink-2: "#a3a8aa"
  plate-rule: "rgba(242, 243, 243, 0.12)"
  chart-line: "#f2f3f3"
  chart-grid: "rgba(242, 243, 243, 0.08)"
  chart-fill: "rgba(242, 243, 243, 0.07)"
  up: "#1fd27a"
  down: "#ff4b52"
  up-text: "#1fd27a"
  down-text: "#ff4b52"
  up-tint: "rgba(31, 210, 122, 0.2)"
  down-tint: "rgba(255, 75, 82, 0.2)"
  select: "rgba(242, 243, 243, 0.22)"
  focus: "#f2f3f3"
  scrim: "rgba(0, 0, 0, 0.7)"
typography:
  display:
    fontFamily: "Geist, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(2.5rem, 5.8vw, 5.5rem)"
    fontWeight: 300
    lineHeight: 1.02
    letterSpacing: "-0.035em"
  page-title:
    fontFamily: "Geist, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(2.5rem, 6vw, 4.5rem)"
    fontWeight: 300
    lineHeight: 1
    letterSpacing: "-0.038em"
  section-title:
    fontFamily: "Geist, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(2rem, 4.2vw, 3.5rem)"
    fontWeight: 300
    lineHeight: 1.02
    letterSpacing: "-0.038em"
  page-section-title:
    fontFamily: "Geist, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "-0.02em"
  list-title:
    fontFamily: "Geist, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.1875rem"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "-0.012em"
  lede:
    fontFamily: "Geist, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(1rem, 1.25vw, 1.125rem)"
    fontWeight: 300
    lineHeight: 1.55
    letterSpacing: "normal"
  body:
    fontFamily: "Geist, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 350
    lineHeight: 1.55
    letterSpacing: "0.003em"
  body-mobile:
    fontFamily: "Geist, Helvetica Neue, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 350
    lineHeight: 1.55
    letterSpacing: "0.003em"
  brand:
    fontFamily: "Geist, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "0.3em"
    textTransform: "uppercase"
  action:
    fontFamily: "Geist, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "0.14em"
    textTransform: "uppercase"
  small:
    fontFamily: "Geist, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 350
    lineHeight: 1.55
    letterSpacing: "normal"
  meta:
    fontFamily: "Geist, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 350
    lineHeight: 1.55
    letterSpacing: "normal"
  figure:
    fontFamily: "Geist, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.1875rem"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "normal"
    fontFeature: "tnum"
rounded:
  none: "0px"
spacing:
  gutter: "clamp(16px, 4vw, 56px)"
  max-width: "1440px"
  nav-height: "64px"
  section: "clamp(88px, 12vh, 152px)"
  section-mobile: "72px"
  grid-gap: "clamp(16px, 2vw, 32px)"
  section-head-gap: "clamp(32px, 5vw, 56px)"
  tile-padding: "clamp(18px, 2vw, 28px)"
  card-padding: "clamp(20px, 2.4vw, 32px)"
components:
  action:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.action}"
    rounded: "{rounded.none}"
    padding: "0"
    height: "44px"
  header:
    textColor: "{colors.ink}"
    height: "{spacing.nav-height}"
  chip:
    backgroundColor: "transparent"
    textColor: "{colors.ink-3}"
    rounded: "{rounded.none}"
    padding: "0"
    height: "44px"
  chip-pressed:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
  input:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
  dash-tile:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    padding: "{spacing.tile-padding}"
    rounded: "{rounded.none}"
  tag:
    backgroundColor: "transparent"
    textColor: "{colors.ink-3}"
    typography: "{typography.meta}"
    padding: "0"
    rounded: "{rounded.none}"
---

# Design System: Andra Markets

Source of truth: `assets/site.css` with `assets/theme.css` loaded after it (every inner page), `assets/home.css` and `assets/home.js` (the homepage), `assets/site.js` and `tools/build_site.py`. The owner approved this look on 11 Nov 2026. Where a value is set in both stylesheets, `theme.css` wins and is the one recorded here. The front matter holds the tokens.

## Overview

**Creative North Star: "Light on the Record"**

A black page, white light and one typeface in light weights. The homepage is a horizon of light with the engraved horse forming out of its dust; every other page is type on black with a faint light at its head. Nothing is boxed: actions are words with a long arrow, filters are words, fields are a line, lists and tiles are separated by hairlines.

Colour is withheld on purpose. The site is ink on black; vivid red and green carry one meaning only, a rise or a fall, in charts and on every figure that shows a move (see The Rise and Fall Rule). Seriousness comes from restraint, dated and sourced numbers, and bracketed placeholders wherever a real number does not yet exist.

**Key Characteristics:**
- One theme: dark. There is no light theme and no theme switch.
- One family: Geist, variable, in light weights, every stack ending in `sans-serif`.
- No boxes: words, lines to write on and 1px hairlines. No shadows, square corners.
- The horse is the only image: the brand mark in the header and footer, and the engraving on the homepage. Each group of the menu also has a picture drawn in fine lines (a globe, a mesh, a chart, buildings).
- Red and green only for rises and falls (charts, and figures with a sign); errors are ink only.
- Motion belongs to the homepage and to moving between pages; inner pages are still. Reduced motion is respected everywhere.

## Colors

Ink on black, one slightly raised tone, and a red and green pair for rises and falls.

**Theme mechanics.** Every page ships `data-theme="dark"` and `theme-color` `#000000`. `assets/site.css` still defines its tokens for `:root` and for `[data-theme="dark"]`; `assets/theme.css` sets the values below for all of them, so nothing depends on the attribute. The homepage defines its own tokens in `assets/home.css` with the same values.

| Token | Value | Role |
|---|---|---|
| `--ground` | `#000000` | The page. |
| `--ground-2` | `#0c0d0e` | A raised tone, used sparingly (the practice progress track). |
| `--ink` | `#f2f3f3` | Headings, body copy, the chosen filter, focus rings, chart lines and dots. The only emphasis the UI has. |
| `--ink-2` | `#a3a8aa` | Secondary text: ledes, descriptions, menu names at rest, meta. |
| `--ink-3` | `#74797c` | Tertiary text: placeholders (`.ph`), source lines, legal line, filters at rest, tags, the dashed comparison line in charts. |
| `--rule` | `rgba(242, 243, 243, 0.10)` | Hairlines: section and list dividers, the line above a tile. |
| `--rule-strong` | `rgba(242, 243, 243, 0.26)` | Stronger rules: list heads, the page head rule, the line of a field, chart reference lines, link underlines. |
| `--select` | `rgba(242, 243, 243, 0.22)` | Text selection. |
| `--focus` | `#f2f3f3` | 2px focus outline. |
| `--scrim` | `rgba(0, 0, 0, 0.7)` | Behind the search palette. |

**The plate.** The Lab and the simulators keep their own tokens (`--plate` `#0b0c0d`, `--plate-2` `#121415`, `--plate-hover` `#1a1c1e`, `--plate-ink`, `--plate-ink-2`, `--plate-rule`), now almost the page's own, so a tool no longer reads as a separate dark slab.

### Chart colours
| Token | Value | Role |
|---|---|---|
| `--chart-line` | `#f2f3f3` | Primary series (solid) and dots. |
| `--chart-grid` | `rgba(242, 243, 243, 0.08)` | Horizontal grid lines. |
| `--chart-fill` | `rgba(242, 243, 243, 0.07)` | Area fill under a series. |
| `--up` / `--up-text` | `#1fd27a` | Rise, positive, beats, advancers, stronger; and a rise as text. |
| `--down` / `--down-text` | `#ff4b52` | Fall, negative, misses, decliners, weaker; and a fall as text. |
| `--up-tint` | `rgba(31, 210, 122, 0.2)` | Positive regime bands. |
| `--down-tint` | `rgba(255, 75, 82, 0.2)` | Negative regime bands. |

On black, `#1fd27a` and `#ff4b52` pass WCAG AA as text, so the figure and chart pairs are the same.

### Named Rules
**The Rise and Fall Rule** (owner's change, 22 Oct 2026; it replaces the charts-only rule). Red and green mean a rise or a fall, and nothing else. They colour chart marks and keys, and every figure on the site that shows a rise or a fall: price moves and percentage changes, the tape, the close-note panel, chart value labels, dashboard "Latest" panels and readouts, calendar changes (m/m, q/q, monthly changes) and earnings first-session moves. The figure always keeps its + or − sign, so colour is never the only cue; a figure that rounds to zero has no sign and stays in ink. Labels, prose, headings, units and words beside the figure ("on the day", "since 3 Oct", "q/q") stay in ink. Levels stay in ink even when signed: yields, rates, inflation rates, spreads, correlations, scores, EPS. Never in buttons, links, tags, status messages, errors, success messages or decoration. As text the figure uses `--up-text` / `--down-text` (`.mv--up`, `.mv--down`; SVG labels take the same classes), except on a dashboard heat cell, where it is white on the cell's own red or green (see Dashboard tile); `build_site.py` reads the class from the printed sign (`mv()`, `move_class()`), and the rolling figures colour a signed word when their element carries `data-moves`.

## Typography

**Font:** Geist (with Helvetica Neue, Arial, sans-serif), for everything.

**Character:** One face in light weights. Hierarchy comes from size and tight negative tracking at display sizes; weight changes little (300 to 400, 500 for the rare bold).

Self-hosted variable font: `assets/fonts/geist-latin.woff2` (SIL OFL 1.1, `assets/fonts/OFL-Geist.txt`), `font-weight: 100 900`, `font-display: swap`, preloaded in every page head. The single stack is `--font: "Geist", "Helvetica Neue", Arial, sans-serif`. No serif face exists anywhere, including fallbacks. Schibsted Grotesk, the previous face, is kept only because the share images (`tools/og_note.py`, `assets/og-image.png`) are still set in it.

### Hierarchy
- **Homepage phrase and closing line** (300, `clamp(2.5rem, 5.8vw, 5.5rem)`, 1.02, -0.035em), centred. **Homepage group title** (300, `clamp(2.5rem, 5.2vw, 4.75rem)`). **Homepage statement** (300, `clamp(1.75rem, 3.1vw, 2.875rem)`, 1.1).
- **Page title** (300, `clamp(2.5rem, 6vw, 4.5rem)`, 1, -0.038em): inner page h1. A close note's headline uses the section title scale (300, `clamp(2rem, 4.2vw, 3.5rem)`, 1.02).
- **Section heading on an inner page** (400, 1.375rem, -0.02em).
- **Titles in lists and tiles** (400): note list, tool and report titles, dashboard tile, calendar event, accordion questions. Sizes as recorded in each page's section.
- **Lede** (300, `clamp(1rem, 1.25vw, 1.125rem)`, 1.55): ink-2, max 52ch.
- **Body** (350, 1.0625rem, 1.55; 1rem at 640px and below): long text max 65ch.
- **Brand** (400, 0.8125rem, uppercase, 0.3em): the "Andra Markets" wordmark next to the mark.
- **Actions** (400, 0.8125rem, uppercase, 0.14em): every button, followed by its arrow.
- **Menu and filters** (400, 0.8125rem to 0.875rem): menu group names, filters, range switches, labels of fields.
- **Small** (0.875rem) and **meta** (0.8125rem), 350: help text, statuses, note meta, chart keys, source lines, tags, legal line.
- **Figures** (400, tabular): levels and changes in panels and tables.
- **Bold** inside text is 500.

Uppercase with letter-spacing is used for the brand and for actions, nowhere else. No italics.

### Named Rules
**The Tabular Numbers Rule.** `font-variant-numeric: tabular-nums` is applied only to elements that hold numbers: tape levels and changes and chip counts. Never on prose or punctuation-bearing text: the calendar's times and figures stay proportional, because tabular colons and points open wide gaps in this face ("10 : 00").

**The One Family Rule.** Every `font-family` resolves to the single `--font` stack ending in `sans-serif`. Form controls use `font: inherit`.

## Layout

**The homepage** is a fixed scene with full-screen sections scrolling over it (see Homepage). It has its own header and no site footer.

**Container.** `.wrap`: full width, max `1440px`, centred, side padding `--gutter` = `clamp(16px, 4vw, 56px)`. Full-bleed sections (hero, tape, Lab plate, signup) paint edge to edge and put a `.wrap` inside.

**Inner pages on wide screens (owner, 11 Nov 2026; 961px and up).** No page leaves the right half empty. The page head runs the full width with its title, lede and meta line centred. Each section of a text or list page is a two-column row, 3fr and 9fr with a gap of clamp(32px, 5vw, 96px): its heading at the left, its content across the rest (archives put the month at the left, in 1.375rem). Data pages with no side panel (Fed & Rates, Central banks, Recession watch, World) run their tables and charts across all twelve columns. Chart of the day puts the chart at the left (7fr) and what it shows at the right (5fr). The Interview simulator's controls and card sit in the middle, 52rem wide. The two long Careers guides (Break into Wall Street, Markets Interview Prep) sit wholly on the page's axis instead: a 54rem column in the middle, section headings centred at 1.75rem with their one-line intro centred under them, the page index a centred row of links, the sample CV centred. A close note keeps its own grid and its title at the left; pages with a side panel (Lab tools, dashboards, company pages, history episodes) keep their columns. Below 961px every page keeps the single column, unchanged. Where the per-page sections below give a 44rem body, this rule wins on wide screens.

**Grid.** `.grid`: 12 columns `repeat(12, minmax(0, 1fr))`, column gap `clamp(16px, 2vw, 32px)`. Row gaps per section: note 48px, About 40px, signup 40px, footer 32px. The Lab uses its own 12 columns with gap `clamp(12px, 1.6vw, 20px)` (wide tool spans 7, tool spans 5, "next" spans all). Dashboards use a 3-column lattice.

**Vertical rhythm.** Section padding `--section` = `clamp(88px, 12vh, 152px)` top and bottom; `72px` at 640px and below. Section head bottom margin `clamp(32px, 5vw, 56px)`. Hero copy top padding `nav-h + 48px`, bottom `clamp(56px, 11vh, 120px)`. Inner page top padding `nav-h + clamp(48px, 9vh, 112px)`. Footer padding 48px top, 40px bottom.

**Nav height.** `--nav-h` = `64px`. `scroll-padding-top` is `nav-h + 16px` so anchors land clear of the fixed header.

**Breakpoints (max-width) and what each collapses:**
- **1100px:** dashboard grid 3 to 2 columns; the calendar drops its Type column.
- **1100px:** the search button turns into its 44px icon (it was 1799px with twelve nav links; the four menu groups leave room for its label above 1100px, owner-approved 31 Oct 2026).
- **960px:** the menu becomes the sheet (it was 1300px with twelve links; four groups fit the bar down to 961px, owner-approved 31 Oct 2026; the sheet shows one group at a time in the panel's cards since 2 Nov 2026); the menu button appears; header gap tightens 24px to 8px. The same width also takes the note, About, signup columns and the footer brand to full width; footer nav and social split 6/6; Lab tools go full width.
- **860px:** the homepage puts each group's picture above its text, hides its header links behind "Menu" and its section marks.
- **640px:** section padding 72px; body 1rem; section heads stack; tape columns become `40vw` each; dashboard tiles go to one column (18px 16px padding, reading figure 1.25rem); calendar becomes stacked rows and its filter labels sit above their chips (see Components); note archive stacks date over title; signup input and button stack; hero buttons stretch; footer links grow to 44px.
- **520px:** every header button hidden (the Subscribe, paused, and Contact us, which sits at the foot instead: see Contact us); menu button shows its icon only.

Tap targets are at least 44px (actions, filters, links, the menu button, footer links on phones).

## Elevation & Depth

The system is flat. There are no drop shadows and no cards. A surface is set apart by a hairline, never by height, and a hover changes colour, not tone or position.

Light is the one exception to flatness, and it is drawn, not cast: the homepage's horizon and its flare (`assets/home.js`), and on inner pages a faint wash at the head of the page (`body::before`, a radial gradient of ink at 7% fading out by 46vh). The fixed header on inner pages has a black fade behind it once the page scrolls, so text does not run under the menu.

### Named Rules
**The Flat Record Rule.** Nothing casts a shadow or sits in a box. A surface is distinguished by a hairline, and a hover changes colour, not height.

## Shapes

Square corners everywhere (`border-radius: 0` resets UA rounding on inputs). The only curves are data marks (2.5px chart dots), the icons, the horizon and the pictures of the groups.

Borders are 1px hairlines in `--rule` or `--rule-strong`, and they are lines, not frames: a rule above a tile or a card, a rule under each row of a list, a rule under a field. The one framed thing is the search palette, because it floats over the page; the sample CV in Break into Wall Street keeps a faint outline because it is a picture of a document.

Icons are Phosphor-style 256-unit SVG paths in an inline sprite (`warning-circle`, `arrow-right`, `arrow-up-right`, `list`, `x`, `envelope-simple` (Contact us), plus the logo of each social channel that has a URL: `linkedin-logo`, `tiktok-logo`, and `youtube-logo` once YouTube is live), drawn at `1em` in `currentColor`.

## Components

### Homepage
`page()` in `tools/build_site.py`, `assets/home.css`, `assets/home.js`. The page does not load `site.css` or `site.js`. A fixed WebGL canvas fills the screen and full-screen sections scroll over it.

1. **Top.** "Markets, on the record." centred above a curved horizon: a thin line of white light with a soft flare at its centre. Nothing else.
2. **Statement.** "What moved, and why. Every trading day, after the New York close.", lit word by word as it scrolls, on the left. Particles lift off the horizon, swarm (dim until they have nearly settled) and form the horse on the right; once formed it is shown as the engraving itself (`assets/horse-particles.webp`, from `andra-horse.png`), not as particles. On phones the horse is above the statement.
3. **One screen per group of the menu.** Title, one line and the group's six sections as plain links on the left; its picture on the right, in fine lines of particles: Markets a globe with a ring and its financial centres; Tools a curved mesh; Research the S&P 500 at the close of every published note, with a column under each close; Careers a row of buildings rising. On phones the picture is above the text.
4. **Closing.** The horizon again, "On the record, every trading day." and Contact us, with the copyright, the legal line and Privacy and cookies at the foot.

- **Header:** the mark and name on the left; Markets, Tools, Research, Careers and Contact on the right, which scroll to their screens. At 860px and below, "Menu" opens a full-screen black list of the same. A column of short marks at the right edge shows the current screen (wide screens).
- **Particles:** up to 1.6 million on wide screens and 500,000 on small ones; the count drops by itself when frames run long, and the rest brighten to compensate. Scrolling takes them from one picture to the next; a jump between screens that are not neighbours (from the header) takes them straight from one picture to the other. Particles in transit are dimmed, and on phones every particle is less than half as bright, so the cloud never covers the text.
- **Opening the site.** The page starts dark. A point of light comes up at the centre, the horizon spreads from it to both sides (about 2.6s), the phrase rises out of a blur at 1.35s and the header fades in at 2.3s. Once per visit; after that a short version (about 1.1s). If the scene never starts the phrase and header are shown after four seconds, and at once without WebGL.
- **Fallbacks:** reduced motion draws still frames, with no opening and no leaving move. Without WebGL the text stands on black.

### Actions (buttons)
Words, not slabs. Every `.btn` (primary, ghost and small alike) is its label in small uppercase (0.8125rem, 400, 0.14em) in ink, with no border and no fill, min height 44px, followed by a thin arrow 44px long that moves 8px on hover. Icons inside buttons are not shown. Small controls inside tools (reset, previous and next) are plain ink-2 words that turn to ink on hover.

### Links
- **Text link (`.link`):** 0.9375rem at 400, underlined (1px, offset 0.22em) in `--rule-strong`, min height 44px, trailing arrow. On hover the icon moves `translate(2px, -2px)`.
- **Inline links** inherit colour with a 1px underline at 0.22em offset.
- **Focus:** every focusable element gets a 2px `--focus` outline at 3px offset (chips at -4px offset; inputs at 0).

### Header and nav
- **Structure:** fixed, 64px. Left to right: the mark and the wordmark (the link home), the four menu groups, search, Contact us, and the menu button at 960px and below. The mark is a plain element; it was the theme switch until 11 Nov 2026.
- **Over the page:** clear at the top; once the page scrolls a black fade sits behind the bar.
- **Menu groups** (owner-approved, 31 Oct 2026; they replace the twelve flat links; six sections in every group, owner-approved 1 Nov 2026): Markets (Dashboards, Fed & Rates, Calendar, World, FX, Companies), Tools (Options, Bonds, Risk & portfolio, Valuation & growth, Market replays, Strategy games: the fourteen Lab tools and Simulators in six themes, each a page of its own, `lab/options/`, `lab/bonds/`, `lab/risk-and-portfolio/`, `lab/valuation-and-growth/`, `simulators/market-replays/` and `simulators/strategy-games/` (owner, 4 Nov 2026: until then each opened its group halfway down the Lab or Simulators page, `lab/#options` to `simulators/#games`, unlike the sections of the other groups; see Tools theme pages)), Research (Daily note, Research Library, Chart of the day, Central banks, Recession watch, Market history), Careers (Interview prep, Interview simulator, Break into Wall Street, Recruiting calendar, Firms, Application tracker), from `NAV_GROUPS` in `tools/build_site.py`. Each group is a button (0.9375rem/550, ink-2, ink on hover) with a caret-down icon at 0.75em; open, it reads in ink with a 1px ink underline at 0.5em and the caret turns over (200ms). A click opens its panel and closes any other; a second click, a click outside, Escape (focus back on the button) or a link closes it, except a plain click on a section where the browser moves between pages with a view transition: there the panel stays open until the next page shows, as the section's name flies into its title (see Page transitions). Without JavaScript a panel opens on hover and focus.
- **Menu panel (above 960px):** fixed under the header to the foot of the screen, on black. The group's picture, a still line drawing of the homepage's scene for that group (`nav_art()` in `tools/build_site.py`; the Research one is drawn from the published notes' closes), sits alone in the middle with the six sections around it, each with its small chart, name, line and arrow. No title or line of text in the middle. Switching groups, the closing group's links are hidden at once so they never pile up while its panel fades.
- **Menu sheet (960px and below):** the group names in a row, the open one underlined, and its six sections in a list under them. No picture and no title.
- **Open group button:** ink and underlined; no outline or box round it.
- **Search:** a magnifying glass, "Search" and the shortcut, with no border; an icon at 1100px and below.
- **Contact us:** an action (words and arrow); see Contact us.

### Filters and range switches
- **Chip:** a word, min height 44px, no border, no fill, ink-3 at 400; its count in ink-3.
- **Chosen (`aria-pressed="true"`):** ink, with a 1px ink underline. Exactly one is chosen. The sliding fill of the previous look is not used.
- **Hover (fine pointers):** ink.
- **Row:** 26px between chips; horizontal scroll with hidden scrollbar, bleeding to the gutter.
- **Status:** a polite live region below the chips at 0.875rem ink-2: "Showing all 9 dashboards" or "Showing n of 9 dashboards: [category]". Matching tiles fade in and rise 6px over 320ms on filter, staggered 35ms.

### Fields
Text, search, number and email inputs, selects and text areas are a single line to write on: no border but a 1px `--rule-strong` line underneath, no fill, square. On focus the line turns to ink; there is no outline. Labels are 400.

### Tiles, cards and tags
Dashboard tiles, question cards and the chart of the day's figure carry one `--rule` hairline above and nothing around; they do not change tone on hover. Tags are plain small text in ink-3 with no border.

### Footer
`--rule` top border, 64px above and 40px below. On the left the mark and wordmark, a one-line description, Contact us and the social links. On the right five columns of links, each under its name in ink: Markets (Dashboards, Fed & Rates, Calendar, World markets, FX, Companies), Tools (Lab, Simulators), Research (Daily note, Research Library, Chart of the day, Central banks, Recession watch, Market history), Careers (Interview prep, Interview simulator, Break into Wall Street, Recruiting calendar, Firms, Application tracker) and Andra Markets (Methodology, Data sources, Legal notice, Privacy and cookies). Links 0.875rem in ink-3, ink on hover. Then the copyright and the legal line. At 960px and below the columns become two and the brand block sits above them. The homepage has no site footer; its closing screen carries the legal line.

### Moving between pages
- **Leaving the homepage:** a click on a link to another page fades the text and scales the scene up into the dark (about 0.6s), then the page changes (`assets/home.js`). It leaves `andra-arrive` in `sessionStorage`.
- **Arriving in a section:** the page's head reads that note before the first paint (`ARRIVE_BOOT` in `tools/build_site.py`, ignored after 8s) and marks `html.arrive`: the page rises out of the dark and the header and footer fade in.
- **Back to the homepage:** it opens again with the short opening.
- **From one section to another:** a view transition across pages (`VIEW_TRANSITION`, type `section`; Chrome, Edge and Safari, others change page as before). The header keeps its place, the page going fades and the next one rises into place; from the open menu, the section's name flies into the new page's title. `assets/site.js` leaves `andra-move` in `sessionStorage` for it.
- **Fallbacks:** reduced motion, a link opened in a new tab or window, and a PDF all go straight to the page.

### The horse
- **Brand mark:** the transparent mark (`assets/andra-mark-dark.png`) beside the wordmark in the header and the footer, and on the homepage's header. Height one line of the wordmark, width auto.
- **Homepage:** the engraving, formed from particles and then shown as itself, beside the statement (see Homepage). It is the only place the horse is shown large.
- **Favicon and touch icon:** the owner-approved head-and-neck crop; see Brand assets.

The page sections that follow were written for the previous look and are kept as the record of each page's structure, content, measures and behaviour, which have not changed. Where they give a border, a fill, a font weight above 400 or a boxed button, chip or tile, the rules above apply instead.

### Tape
Not on the homepage since 31 Oct 2026 (the homepage is one screen); kept here as built.
A full-width band below the hero, ground fill, `--rule` top and bottom.
- **Head:** h2 "Markets [date], [time] ET" at 0.9375rem/600 ink, and a right-aligned link to the latest close note (550, ink, arrow nudges 3px on hover). Head text otherwise 0.875rem ink-2.
- **List:** 10 instruments in a grid of `minmax(124px, 1fr)` columns that scrolls horizontally with snap; at 640px and below each column is `40vw`. Items separated by vertical `--rule` hairlines, 16px padding. Name 0.8125rem ink-2; level 1.1875rem/500 tabular; change 0.875rem.
- **Rolling figures (owner-approved, 22 Oct 2026):** levels and changes roll up from zero, digit by digit, once the tape enters view (640ms ease-out, staggered 45ms per instrument). Each digit is a column of 0 to 9 in tabular figures; separators and letters stay still. Screen readers get the plain figure. A live feed can update a figure through the same roll (`AndraRoll` in `assets/site.js`), which moves only the digits that change. No roll under reduced motion; the figures are plain text without JS.
- **Source line:** "Last and daily change. Source [data vendor]" at 0.8125rem ink-3.
- **Market strip (between notes):** refreshed every 15 minutes in US hours and after the European and Asian closes (`tools/strip_data.py`, see README, Market strip). The head reads "Markets 22 Oct 2026, as of 2:45 pm ET"; each item adds a fourth line, `.tape__when` (0.8125rem ink-3): its own time ("2:45 pm ET") while its market trades, "Close, 22 Oct" once it has shut. Changes are on the previous session's close, coloured as rises and falls. The link still goes to the newest published note. Source line: "Last price and change on the previous close, each with its time or close date. Sources: Yahoo Finance, FRED for the US 10Y yield. Futures and FX may be delayed." Shown only when newer than the latest note's close.
- **With a published note:** the head reads "Markets 9 Oct 2026, 4:00 pm ET" (1:00 pm on NYSE early closes) and links to that note's page. Levels are the note's official closes (stored in its note record), with thousands separators and each instrument's decimals; changes carry a sign and a true minus (U+2212), percent to two decimals, the 10-year yield in whole basis points. Changes are coloured as rises and falls (The Rise and Fall Rule); levels and names stay in ink. A series with no print for the session shows its level and "Prior close" as the change; a missing value reads "n/a". Source line: "Close and daily change. Sources: Yahoo Finance, FRED for the US 10Y yield.", plus "Prior close: no print yet for the session." when it applies.

### Dashboards page (`dashboards/`, 31 Oct 2026)
The dashboards section that was on the homepage, as an inner page: the page head ("Dashboards", the lede "Interactive views across rates, equities, macro and cross-asset. Open any one for its full history." and, under it, "Figures to the close of [Friday 30 Oct 2026]. Each tile names its own source and date." at 0.875rem ink-2, the newest session among the daily tiles, left out while no tile has figures), then the filter chips, the status line and the tile lattice: three columns, two at 1100px and below, one at 640px and below. The head's rule sits `clamp(32px, 5vw, 56px)` above the chips. Each dashboard page's crumbs ("Dashboards / [Category]") link back here.

### Dashboard tile
A cell in the hairline lattice; no card chrome. Owner-approved from mock A, 1 Nov 2026 ("tiles that read"): every tile can be read without a pointer, on a phone too.
- **Order, top to bottom:** title row (h3, with the `arrow-up-right` at 1.125rem on the right, at 0.5 opacity), the reading, the chart, then the source line pinned to the tile's foot.
- **Reading:** one figure and one line, built from the figures the tile draws (`tile_reading()` in `tools/build_site.py`), never typed by hand. The figure is 1.375rem/500 (1.25rem at 640px and below), the line 0.875rem ink-2, max 46ch. Sectors and global indices lead with the weakest on a down day (the median is negative) and the strongest otherwise, then how many rose or fell and the other end; FX majors lead with the dollar's largest move and count the majors it gained and lost against; the volatility curve leads with the VIX 1-month level, its change since the comparison date and the curve's shape (inverted at the front, upward sloping or flat); commodities lead with the larger day move of WTI and gold, then both rebased levels; credit leads with the high-yield spread and its change over a month in bp; inflation and labour with CPI year on year and the month's payrolls; breadth with the net figure and the advancers and decliners; correlation with S&P 500 and long Treasuries and how closely they move. Changes take red or green from their sign (The Rise and Fall Rule); levels (VIX, spreads, CPI, correlations) stay in ink. A record that lacks what the line needs shows the tile's description instead.
- **Chart:** a 320 x 176 box drawn at the tile's width (`.chart--tile`), names and values written on it at 11.5 units (about 14px on a laptop, 12px on a phone) in proportional figures, so points and commas stay narrow. Sectors: a 4 x 3 heat grid, each cell naming its sector and change. Global indices and FX majors: diverging bars with the name on the left and the signed change on the right (an index whose latest close is older than the tile's date adds that date to its name). Volatility: the curve with each expiry's level above its dot, the expiries evenly spaced and named below, and the comparison curve dashed with its date at its end. Commodities and credit: lines with each one's name and last value at its right end (pushed apart so they never overlap), commodities with the dashed 100 line. Inflation: the CPI line with its last value, the payroll bars below with the month's figure. Breadth: net bars around a zero line, the last session's figure on the right and the first and last dates below. Correlation: the lower triangle of pairs, rows and columns named (S&amp;P, TLT, USD, WTI, Gold), each cell with its value. No key row: the chart names its own marks. Every mark keeps its native tooltip and the SVG its full aria-label.
- **Heat cells** (sectors and correlation): deep green or red fills, the same in both themes, deeper for a larger move (green `#0e4a2b` to `#11803f`, red `#5a171c` to `#b3212a`; correlation runs from grey `#2a3035` at zero), with white type. A move that rounds to zero is grey and unsigned. On a heat cell the figure keeps its sign and the cell's own colour carries the rise or fall, so the figure is white rather than `--up-text` or `--down-text`.
- **Deeper rises and falls (owner, 1 Nov 2026):** inside `.dash-grid` the chart pair and the text pair are a shade darker than the site's: light `--up` `#0a7a3d`, `--down` `#c01d26`, `--down-text` `#b81c24`; dark `--up` `#12964f`, `--down` `#cf2a32`, `--up-text` `#19b866`, `--down-text` `#ee3f47`. Text figures still pass WCAG AA on the ground.
- **Source line:** "[Category]. [source], [date]" at 0.8125rem ink-3, e.g. "Rates and credit. FRED, US Treasury, 19 Oct 2026". The date is the data's own as-of date (the month for monthly data), never the build date.
- **Data:** fetched at deploy time by `tools/dashboard_data.py` (the agent's archived facts of published notes, FRED, Yahoo Finance). A source that fails keeps the tile's last good figures and their date; a tile that has no figures yet keeps its place: its description stands in for the reading and its chart box (320:176) holds one line, "Data pending" (0.8125rem ink-3, centred), with no chart, and its source line names the real source without a date. **No illustrative tiles:** the earnings season tracker is out until it has a real source; market breadth is shown as "Watchlist breadth" (advancers less decliners across the Andra Markets watchlist, from the agent's archive), never as market-wide breadth.
- **No kicker:** the title opens the tile. The category lives in the source line.
- **Hover (fine pointers):** tile fills to `--ground-2` over 200ms; the arrow goes to full opacity and nudges 2px up and right.
- **Padding:** `clamp(18px, 2vw, 28px)`; 18px 16px at 640px and below, where the lattice is one column so every chart runs the full width.
- **Link:** every tile opens its dashboard page, `dashboards/<slug>/`.

### Dashboard page
Owner-approved from the Commodities mock. One page per dashboard, `dashboards/<slug>/`, built from the same record as its tile; no downloads (the chart's figures are embedded in the page, which the owner approved).
- **Grid:** 12 columns, row gap `clamp(32px, 5vw, 48px)`. Head full width; the chart in columns 1 to 8; the "Latest" panel in 10 to 12, sticky (`top: nav-h + 24px`); "How to read it" and "Source" in 1 to 8 under the chart. At 960px and below one column in that order: head, chart, Latest, notes.
- **Head:** crumbs ("Dashboards / [Category]", 0.8125rem ink-3, the link ink-2), the page title, the tile's description as the lede, then "[source]. As of [date]." in the note meta style; `--rule-strong` under it, as on every page.
- **Range selector:** the existing chips (`aria-pressed`), 1M, 3M, 6M and 1Y where the history covers them; a range the history does not fully cover is offered once and shows all there is. Changes over a range add 1D (sector heatmap, global indices, FX majors); the volatility curve adds 1W (its tile's comparison); inflation and labour uses 1Y, 2Y and 5Y; commodities and credit add 2Y. Defaults: the tile's own view (1D, 1M or 1W comparisons), 3M for commodities and correlation, 6M for credit, 2Y for inflation.
- **Chart:** drawn by `assets/dashboard.js` at the plot's pixel width (height `clamp(240px, 42vw, 380px)`; bar lists and the matrix size to their rows), so labels stay 12px on a phone. Series, grid, reference lines, dots and bars follow Charts; a vertical crosshair in `--rule-strong`, a `--ground-2` band behind the hovered bar, a 1.5px ink ring on the hovered matrix cell. Changes over a range are labelled diverging bars (name left, signed value right, largest gain first), never colour alone. The correlation matrix shows every pair with its value; cell opacity `0.12 + 0.45 x |r|` keeps the ink figures readable in both themes.
- **Key and readout:** the key below the chart (dates for curve comparisons); under it a live readout (0.875rem ink, `aria-live="polite"`) for the point under the pointer, or under the arrow keys once the chart has focus (Home and End jump to the ends). It starts on the latest point.
- **Latest:** the close-note panel style (`.kpi`): four to eleven rows of name, level and what the change is measured against, then a source line.
- **Views, comparison date and toggles (owner-approved, 26 Oct 2026):** above the chart, in order: "View" chips when the page has more than one view (Ranked and Rebased for sectors, indices and FX; Curve, Change, Over time for the volatility curve; Rebased and Ranked for commodities; Levels and Change for credit; Inflation and jobs, and Unemployment; Net and Cumulative for breadth; Matrix and Rolling for correlation), each group with its 0.8125rem ink-3 label above. "Range" holds the range chips and, beside them, a date field (44px, `--rule-strong` border, label 0.875rem/550: "From", "Compare with" on curves, "Window ending" on the matrix) bounded by the history; picking a date unpresses the range chips and the glide fades out. 1D shows only on the ranked view. "Show" holds one toggle per series: a hairline chip (44px) whose 10px square fills with ink when the series is on, never the single pressed fill of a choice. At least one stays on; line views take up to six at once and say so in a 650 status line under the controls. Series added beyond the tile start off; the Latest panel lists the tile's series only.
- **Link to a view (31 Oct 2026; no visible change):** the view, range or comparison date and the series switched on live in the URL's fragment, never the query string, so nothing reaches a server: `#view=rebased&range=6M&on=technology,energy`, with `from=2026-03-16` in place of `range` for a date. `assets/dashboard.js` writes it with `replaceState` on every change, only what differs from the page's defaults (the plain page keeps a clean URL); a series' key is its name in lower case joined by hyphens (`sp-500-spy`). Opening a link applies it before the first draw, the chips already in place (no glide); a view, range or series the page does not offer, a date outside the field's bounds, more series than the view takes and unknown keys are ignored. The dashboards page keeps its filter the same way (`dashboards/#rates`; All leaves none). Shared links depend on these keys.
- **Several lines on one chart (owner-approved, 26 Oct 2026):** six monochrome styles in order: solid ink 1.6 (`s0`), dashed ink-3 4 4 (`s1`), dotted ink-2 1 3 round caps (`s2`), long dash ink-2 9 4 (`s3`), dash-dot ink-3 7 3 1 3 (`s4`), thin solid ink-3 1px (`s5`). Each line is named at its right end (12px ink-2, pushed apart 14px so names never overlap; on phones under 520px the key alone names them), and the key shows each style as a 16px SVG line. Rebased lines share a dashed 100 reference; changes a dashed zero line. No colour: red and green stay for rises and falls (bars and signed figures).
- **Pending:** a page whose dashboard has no figures yet keeps its head, notes and source, and its chart area holds "Data pending" (0.875rem ink-3, centred) above a `--rule` hairline; no chips, no Latest panel.

### Fed & Rates (`fed-rates/`, owner-approved preview, 30 Oct 2026)
A section of its own in the menu, built on the dashboard page grid (head, main column 1 to 8, sticky Latest in 10 to 12, notes), from `.cache/fedrates/fedrates.json` (`tools/fedrates_data.py`); `assets/fedrates.js` draws it.
- **Head:** title, lede, then the meta row: sources, "Updated [date], [time] ET" and "Refreshed every 15 minutes while the NYSE is open". No crumbs.
- **Range:** one chip group above the panels, 1M to Max (default 5Y), for the charts over time (spreads, the Fed against inflation and jobs, real rates).
- **Panels:** a stack separated by `--rule-strong` rules, each with its h2 (1.375rem/540), a one-line intro in ink-2, its controls, chart, key and readout, and a source line (0.8125rem ink-3) with its own as-of date. In order: Policy rate and the FOMC; What markets price; Treasury yield curve; Curve spreads; The Fed against inflation and jobs; Real rates and breakevens.
- **Policy:** two columns split by a `--rule` hairline (one column at 640px and below): target range ("4.00 to 4.25%", 1.5 to 2rem/540) with the effective rate and the last change (signed, red or green), and the next decision ("9 Dec 2026, 2:00 pm ET") over a countdown (days, hours, min, sec: 1.5rem/500 tabular over 0.75rem ink-3 units). Under them a ruled list of meetings: the last one past in ink-3 with its decision, the next in 600 ("Next, with projections" where the Summary of Economic Projections comes), then the following five.
- **Probabilities:** ruled rows of outcome (Hold, Cut 25 bp, Hike 25 bp, and any wider move priced), a 12px bar (ink fill on `--ground-2`) and the percentage in ink: a probability is not a move, so no red or green. Above it "Next meeting, [date]. Implied change [signed bp]", the change in red or green. Under it the expected rate after each meeting: solid now, dashed as priced a month ago, the effective rate as a dashed reference line.
- **Curve:** maturities spaced by the square root of their length; "Compare with" toggles (the dashboard hairline toggles) for 1 week, 1 month (on) and 1 year ago, in styles s1, s3, s2 against the solid s0 curve with dots. Intraday points from the Cboe yield indices are hollow 4px rings (ground fill, 1.5px ink), keyed "Intraday, [time] ET, delayed", shown only while newer than the official curve. Under the chart a table of changes in basis points by maturity (0.8125rem tabular, each figure signed and in red or green).
- **Spreads:** chips 2s10s, 3m10y, Both. Periods when a spread shown is below zero are shaded in `--chart-fill` and keyed "Inverted": inversion is not a fall, so never red. A dashed zero line.
- **Save image:** a small ghost button (download icon, "Save image"; icon only under 520px) at the right of each chart panel's heading. It makes a 2x PNG in the browser: the theme's ground, the transparent header mark and "Andra Markets" (600 14px), "Fed & Rates: [panel]" (540 20px), the chart as drawn (crosshair and hover dots left out), the source line and "Andra Markets. For information only. Not investment advice." in ink-3. Named `andra-markets-fed-rates-[panel]-[date].png`. The one download on the site (PRODUCT.md): an image, never the figures.
- **Latest:** the `.kpi` panel: target range, effective rate, next FOMC with its most likely outcome, 2Y and 10Y yields, 2s10s and 3m10y (levels in ink, signed), 10Y real yield, 10Y breakeven, core PCE. Day changes in red or green with their sign.
- **Pending:** a block not fetched yet keeps its panel and source with "Data pending" in its chart box; its Save image button is left out.

### Central banks (`central-banks/`, owner-approved sketch, 1 Nov 2026)
The Fed & Rates page grid and panels (head, main column 1 to 8, notes; no Latest panel: the table is the summary), from `.cache/centralbanks/centralbanks.json` (`tools/centralbanks_data.py`); `assets/centralbanks.js` draws it (`tools/page_central_banks.py`).
- **Head:** title, lede, meta row: sources, "Updated [date], [time] ET", "Refreshed each weekday".
- **Policy rates now:** the first panel, without a rule of its own under the head's. A ruled table (`.cb-tab`: `--rule-strong` top, `--rule` rows, column heads 0.8125rem/500 ink-2): Bank, Policy rate, Last move, Next meeting. The short name 1.0625rem/540 over the full name and measure (0.8125rem ink-2); "Fed" is an underlined link to Fed & Rates whose arrow nudges 3px on hover. Figures 1.1875rem/500, proportional, over a 0.8125rem ink-3 line: "As of [date]"; the last move signed in bp, red or green, over the day it took effect; the next decision over "In n days" ("Today", "Tomorrow"), recounted in the browser in New York time. At 640px and below each row stacks: the bank, then the cells two to a row, each with its column name above (0.75rem ink-3).
- **The four rates since 2019:** step lines, Fed s0 (top of the target range), ECB s1, BoE s3, BoJ s2, each named at its right end; a dashed zero line while a rate is below zero. Each line ends on its own as-of date; the readout opens on "Latest: [bank level (date)]…" and shows a day's levels under the pointer or arrow keys (the Fed as its range). No Save image (PRODUCT.md allows it on Fed & Rates only; `SAVE_IMAGE` in the module turns it on).
- **Pending:** a bank with no figures says "Data pending" (0.875rem ink-3) in its cells and is left off the chart; with none, the chart box says "Data pending".

### Recession watch (`recession-watch/`, owner-approved sketch, 1 Nov 2026)
The Fed & Rates grid and panels, from `.cache/recession/recession.json` (`tools/recession_data.py`); `assets/recession.js` draws it (`tools/page_recession_watch.py`). No forecast and no probability.
- **Latest readings:** the Central banks table: Indicator (linked to its chart, what it measures under it), Latest (the level in ink, over its change on the reading about a month before, signed, red or green by direction, never by good or bad), Signal (a plain reading at 500 over a 0.8125rem ink-3 note, against the indicator's own published definition, or "No official threshold"), Date ("30 Oct 2026", "Week to 24 Oct 2026", "Oct 2026"). Signals are ink: no traffic-light colours.
- **Range:** chips 1Y, 2Y, 5Y, 10Y, 20Y, Max (default) between the table and the charts.
- **Charts:** one Fed & Rates panel per indicator; NBER recessions in `--chart-fill`, keyed "NBER recession"; dashed reference lines at zero (curve, NFCI) and 0.50 (Sahm); claims weekly (s5) and 4-week average (s0) with a Scale group (Linear, Log), as the 2020 spike flattens the rest. A single line drops the room for line names. The readout adds "In an NBER recession" in a shaded period. The source line says where the series starts. No Save image, as on Central banks.
- **Pending:** as Central banks; an indicator with no figures spans its row with "Data pending".

### Break into Wall Street (`break-into-wall-street/`, owner-approved preview, 30 Oct 2026)
An inner page from `data/path_to_wall_street.json`; "Break into Wall Street" in the menu, the footer and as the title (renamed from Careers and Path to Wall Street, owner, 30 Oct 2026; `careers/` redirects). `assets/careers.js` runs the templates.
- **Head:** title, lede, meta row (the five roles, "Last reviewed [date]"). Then "On this page": a numbered two-column list of links (one column on phones), closed by a `--rule` hairline.
- **Sections** in the 44rem body, as on Interview Prep: the roles in the multi-open accordion (short name above in the Interview Prep subject style; inside: what, "A typical day" as a ruled numbered list, "Suits you if", "Where it leads", labels 0.8125rem/600 ink); the CV rules as a ruled list; networking steps; the technicals as ruled link rows (name, description, arrow that nudges 3px on hover); certifications as ruled rows with a When / Worth it definition grid; resources in groups.
- **Recruiting calendar** (owner-approved preview, 30 Oct 2026; replaced the timeline by academic year; its own section of the Careers menu since 1 Nov 2026, owner: the guide no longer carries it, and `break-into-wall-street/recruiting-calendar/` redirects to `recruiting-calendar/`; `assets/recruiting.js`). The page uses the calendar's shape: title, lede, meta (firms and programmes, counts by status, "Checked by hand against each firm's careers site, last checked [date]"); a View group (By date, By firm), month tabs ("Open now" for rolling programmes, then each month from this one), and Programme, Firms, Division and Dates ("Confirmed only") chip groups with a status line; the `.cl__table` by date, grouped by month, with columns Date, Firm and programme, Window (Opens, Closes, Rolling), Division (tags), Cycle and Apply; By firm, a ruled table of every programme grouped by firm type with Opens and Closes as dates, "Expected [window]", "Rolling" or "Not announced", past closes marked "(closed)", and the basis of each expected window under it in ink-3. Status is text in tags (Confirmed date, Expected window, Rolling, Not announced, Low confidence, Not yet re-checked), never red or green. Without JavaScript the controls stay hidden and both views show.
- **Technical preparation:** ruled rows (topic, one-line description, arrow) linking to nine training pages, `break-into-wall-street/technicals/<topic>/` (owner-approved preview, 30 Oct 2026), from `data/technicals/<topic>.json` (`assets/technicals.js`): crumbs, title, lede, meta (question counts, "Your progress stays in this browser"); a row of topic tabs (0.875rem/500 ink-2, the current one ink 600 with a 2px ink underline, scrolling on phones); "What you must know" as a numbered ruled list (number 0.875rem/600 ink-3, title 1.0625rem/540, text ink-2); an optional worked example table (statement or step in 600, figures right-aligned and tabular in ink with their sign: worked examples are not market moves, so no red or green); on Brainteasers the mental maths drill; "Practice"; "Common mistakes" as a ruled list; a pager (next topic, all topics, Interview Prep).
- **Practice card:** Level (All, Core, Advanced) and Order (To review first, Shuffle) chips; a progress line ("n of m marked Got it, k to review") with a 4px ink bar on `--ground-2` and "Reset progress"; a card with a 1px `--rule-strong` border: "Question i of n", a level tag, the question (1.25 to 1.5rem/540, balanced), "Show answer" (primary) revealing the model answer in ink-2 and "Likely follow-up", then "Got it" (primary) and "Review again" (ghost), with Previous and Next on the right. Marks are kept in `localStorage` per topic, so cards to review come first next time. Without JavaScript every question shows with its answer.
- **Mental maths drill:** Time (60 seconds, 2 minutes) and Questions (Mixed, Multiplication, Percentages, Fractions) chips; a bordered panel with the clock, score and best score (tabular), the question at `clamp(2rem, 5vw, 3.5rem)`/540, a 48px input and "Start" / "Answer" button, and a line under it naming the last answer ("Correct" or "Not quite", in ink: right and wrong are not rises and falls). Best scores stay in `localStorage`.
- **Sample CV:** a sheet with a 1px `--rule-strong` border on the ground (no shadow, no radius), 0.8125rem, centred name (1.375rem/600) and contact, section heads in 0.75rem/650 capitals over a `--rule-strong` rule, rows with dates right-aligned. Captioned "Sample CV. Every name, firm and figure is an example."
- **Templates:** chips per template; one shown at a time: "Subject" line, then the body as pre-wrapped text in ink-2; a ghost "Copy template" button with a polite status ("Copied. Replace every [bracket] before sending.").
- **Visas:** three columns (US, UK, EU) split by `--rule` hairlines, one column at 960px and below; each route a link to the official page with one line in ink-2. A note that rules change.
- **Content rules:** a date only when the firm has published it and someone has checked it on the firm's page (read from the firm's own site; a row not yet re-checked by hand carries a "Not yet re-checked" tag and the head counts the re-checked rows); an expected window says what it rests on; no salaries; no personal names (books by title and publisher); every visa and certification links to its official source.

### Firms (`firms/`, owner-approved sketch, 1 Nov 2026)
A directory of the firms in the Recruiting calendar, from `data/recruiting_calendar.json` only (`tools/page_firms.py`, `assets/firms.js`). Calendar page head (title, lede linking the calendar, meta: firm and programme counts and the calendar's checked line). Type chips (the calendar's groups, firm counts in tabular figures) and Division chips (IB, S&T, AM, Quant) with a status line, hidden without JavaScript. The list is max 64rem. Each firm sits under a `--rule-strong` rule: its name (1.375rem/540) and type (0.875rem/550 ink) on one line; its divisions (" · ", 0.9375rem ink-2) and US offices (0.875rem ink-2) under them. The right column lines up with the programmes' dates. Programmes are `--rule` rows in three columns (main, 17rem dates, 6.5rem apply): name (1rem/540), cycle and locations (0.875rem ink-2), the calendar's tags and expected-window basis; Opens and Closes as a definition list in the calendar's words, with "Closes in n days"; the calendar's Apply link with a 44px target. Each firm ends with "See in the Recruiting calendar" to `recruiting-calendar/#f-<slug>`, which opens the calendar's By firm view at that firm's first row. Rows stack at 640px. No description, ranking, pay or headcount.

### Application tracker (`application-tracker/`, owner-approved sketch, 1 Nov 2026)
The reader's applications, in `localStorage` (`andra-tracker`) only, never sent (`tools/page_application_tracker.py`, `assets/tracker.js`; the calendar's programmes are a JSON data block in the page). A primary "Add from the Recruiting calendar" button (a CSS plus sign) opens a dialog: a type-to-narrow combobox over a ruled list (the Lab picker's rows, `--ground-2` on the active row), then "Or add your own" (firm, role, optional deadline). The board has four columns (To apply, Applied, Interview, Offer), each headed 0.9375rem/600 with its count in ink-3 over a `--rule-strong` rule; two columns at 1100px, one at 640px. Cards have a 1px `--rule` border: firm (1.0625rem/540), role (ink-2), a date list (Closes with "Closes in n days" and "From the Recruiting calendar" in ink-3; Applied; Next with "In n days"), a contacts and notes count, then a Status select (44px, square, caret icon) and a Details button. Nearest date first. Dialogs follow the search palette: the dialog is the scrim, the panel `--ground` with a `--rule-strong` border, opening with opacity and `translateY(-8px) scale(0.985)` (instant under reduced motion). Fields follow the Lab's (52px, `--rule-strong`, invalid as the signup error). Under the board: "Saved only in this browser. Nothing you enter is sent." with Export a copy, Import a copy and Delete all (each confirmed in a small dialog, focus on the safe choice). A `--rule-strong` notice with the warning icon appears when storage is blocked. Without JavaScript a sentence links the calendar.

### World markets (`world/`)
Twenty-five markets on eight measures, from `tools/world_data.py` (see README, World markets data); `assets/world.js` draws the comparison. The dashboard page grid.
- **Head:** page title "World markets", lede, "Yahoo Finance, OECD, World Bank, IMF. Updated [date, time] ET." in the note meta style. No crumbs.
- **Picker:** "Compare up to three" (0.8125rem ink-3) over one toggle chip per market (the dashboard toggles: hairline 44px chips, a 10px square filled ink when on); United States, Germany and Japan to start. At least one stays on; a fourth says so in a 650 status line. On phones the chips are one horizontal scrolling row.
- **Radar:** eight spokes (1M return, YTD return, Volatility, Currency, 10Y yield, GDP growth, Inflation, Unemployment, clockwise from the top), four `--chart-grid` rings, labels 12px ink-2 outside the rim. Every axis runs from the lowest figure among the 25 markets (at 12% of the radius, so the lowest is still visible) to the highest (the rim). Markets in the first three of the six line styles (solid ink, dashed ink-3, dotted ink-2) with 2.6px dots; the first market also gets a `--chart-fill` area when it has all eight figures. A missing figure leaves a gap in the outline: the edges to that spoke are not drawn. A crosshair line from the centre follows the spoke under the pointer or the arrow keys; the readout names the measure and each market's figure with its date. Outward means higher, not better.
- **Comparison table:** under the key, measures as rows and the markets as columns (the column head carries the market's line swatch); each cell holds the figure (1rem/500 tabular) over its date and source (0.8125rem ink-3), or "No figure" in ink-3.
- **The scale (side panel, `.kpi` style):** each axis's lowest and highest figure with the markets that hold them; a source line explains the scale. It sits beside the radar only and is not sticky: the sections under it run full width, so it must never slide over them.
- **Labels on every point:** the large radar names its spokes at the rim, and each point carries a tooltip with the market, the measure, the figure and its date. Each small radar's points carry the measure and figure as a tooltip, and a 0.8125rem line under the market's index reads out the measure nearest the pointer ("Volatility: 14.80%"), holding its height when empty.
- **Each market:** a lattice of 25 small static radars (120px, the same scale, one solid outline) with the market and its index under each; pressing one adds or removes it from the comparison (pressed: `--ground-2` fill and "· compared").
- **Every figure:** a full-width table of the 25 markets by eight measures, scrolling sideways when narrow; returns and the currency move are moves (signed, red or green), every other figure is a level in ink.
- **How to read it** and **Sources** (one row per axis: what it measures, each source with its dates, and which markets have no figure and why). No figure is ever estimated.

### FX (`fx/`, `fx/<date>/`)
- **Index (`fx/`):** inner page head ("FX", lede). With an analysis: the latest as the daily note module's article (note-title headline linked to its page, standfirst in ink-2, meta row with date, edition and read time, a primary "Read the analysis" button), closed by a `--rule` hairline. Then "Majors and emerging markets" (inner page h2): the pairs table, a 0.8125rem ink-3 source line saying how the pairs are quoted, and a text link to the FX dashboard. Then "Every analysis": the note archive pattern (month headings, `7rem | title | arrow` rows). Before the first analysis only the pairs table and the dashboard link show; no placeholder for the analysis.
- **Pairs table (`.fx-tab`):** `--rule-strong` top rule; group rows "The dollar", "G10 majors", "Emerging markets" (0.875rem/600 over a `--rule-strong` rule); each pair's name (540) over its quote convention (0.8125rem ink-3, "USD per EUR"), then last (tabular), day, week, month and year to date, right-aligned. Every move is signed and coloured as a rise or a fall as the pair is quoted; a move that rounds to zero stays in ink; levels in ink. The analysis page adds the policy rate with the bank and its gap to the Fed in bp (ink: rates are levels). On phones each pair is a row: name and quote on the left, last over the day's move on the right, then week, month and year (and policy rate) as labelled lines.
- **Analysis (`fx/<date>/`):** the report page layout: crumbs "FX / Daily analysis", the headline in the report title scale, standfirst, meta row, "Share this analysis"; the side panel "The session in numbers" (the dollar index and nine pairs, level and day's move); sections Takeaways (ruled list), The dollar, G10 majors, Emerging markets, Rate differentials and central banks, Levels that matter (ruled list, one line per pair), Ahead (each only when it has text), "Every pair" (the table with policy rates) and Sources. Pager: previous and next analysis, all FX analyses, the FX dashboard, the close note for the session.
- **Charts (`fx/`, under the pairs table, `assets/fx.js`):** "Charts" (inner page h2), then one block per chart under a hairline, each with the dashboard page's controls (labelled chip groups), plot, key and live readout (pointer or arrow keys):
  - *The dollar index:* one solid line, range chips 1M, 3M, 6M, 1Y (6M to start), crosshair and dot; the readout gives the level and the move since the range's start.
  - *Pairs:* "View" chips, One pair (a pair chip group, one pressed) or Compare, rebased to 100 (toggle chips, up to six, in the six line styles with names at the right ends and a dashed 100 reference); range chips as above.
  - *Moves:* a heatmap of every pair over a day, a week, a month and the year to date, in the correlation matrix style (cell `--up`/`--down` at opacity `0.12 + 0.45 x |move| / largest in its column`, signed figures in ink, a ring on the cell under the pointer); "Read as" chips switch between each pair as quoted and each currency against the dollar. Column heads shorten to 1D, 1W, 1M, YTD when narrow.
  - *Moves and rate differentials:* a scatter of each currency's move against the dollar (vertical, chips for the period) against its 3-month interbank rate less the US's (horizontal, percentage points), dashed zero lines, each point a 4.5px dot in `--up` or `--down` by the move's sign (ink when it rounds to zero) with its currency code in ink-2; the readout words the differential without a sign ("1.31 points below the US"), since it is a level. A source line names the OECD rates and the currencies without one.
- **Nav:** "FX" between Calendar and Daily note in the header (and in the footer). With World markets as well the header holds nine links: the gap tightens to 12px from 1021px to 1080px.

### Lab tool card and the plate
- **Plate:** the `.lab` section, `--plate` fill, all ink tokens re-mapped (see Colors).
- **Tool card:** `--plate-2` fill, padding `clamp(20px, 2.4vw, 32px)`, chart on top (640x260 viewBox), key with Illustrative stamp, then title, description (plate-ink-2, max 48ch), optional parameters line (0.875rem, with placeholders), a source line (`.tool__src`, 0.875rem plate-ink-2: `[source], [date]`, or the model and source for a calculator), and an "Open" text link pinned to the bottom. The wide card spans 7 columns, the other 5.
- **Hover:** card fills to `--plate-hover` over 200ms.
- **"Next in the Lab":** full-width row, transparent with a `--plate-rule` outline, title at 1.25rem, text and a Subscribe link in a wrapping row.
- **Homepage cards (Lab tools live):** the wide card opens the options payoff diagram, the other the bond calculator (its Illustrative chart is a 10-year 4% bond's price against yield with the duration line), and the full-width row reads "Also in the Lab": a sentence naming the eight other tools, then links to risk and correlation, the Black-Scholes pricer and all tools.

### Tools theme pages (`lab/options/`, `lab/bonds/`, `lab/risk-and-portfolio/`, `lab/valuation-and-growth/`, `simulators/market-replays/`, `simulators/strategy-games/`)
The six sections of the Tools menu, each a page of its own since 4 Nov 2026 (owner: the menu took you into the Lab page, not to the section, unlike the other groups), from `TOOL_THEMES` in `tools/build_site.py`. The Lab index layout with nothing new: the page head (title, the theme's name, so the menu's name flies into it as for every section; a lede of one sentence on what its tools do, then "Every tool runs in your browser: nothing you enter is sent or stored." or, for the simulators, "Every simulator runs in your browser; your results stay on your device."), then its tools as the index's ruled list (`.learn-list.lab-index`, max 44rem, `--rule-strong` top rule), each row exactly as on the Lab or Simulators index. No crumbs, as on the other section pages; the tools' crumbs lead back here. The Lab and Simulators indexes stay, with every tool in its themes, and are still in the footer.

### Simulators (`simulators/`; owner-approved, 30 Oct 2026, leaner layout approved the same day)
Market games, separate from the Lab: the Trading Simulator, the Panic Test, Guess the Fed and the Portfolio Builder. They run in the browser (`assets/sim.js` for the two chart games, `assets/fed-game.js`, `assets/portfolio-game.js`); their data is `assets/simdata-*.js` (see README, Simulators data). Results stay in localStorage.
- **Nav and footer:** "Simulators" after Lab. **Homepage:** its own section between Dashboards and the Lab, on the ground (not a plate), `--rule` top border: title, lede, "Play today's challenge" (primary) and "All simulators" (ghost), a 0.875rem ink-3 line naming the other three; the game chart with the horse in columns 6 to 12, an illustrative seeded path stamped "Illustrative". Stacks at 960px.
- **Index page:** the Lab index layout (ruled list), one row per simulator with its data in the meta line, in the two themes of the Tools menu (Market replays: the Trading Simulator and the Panic Test; Strategy games: Guess the Fed and the Portfolio Builder), as on the Lab index. Each theme is also a page of its own (see Tools theme pages).
- **Crumbs:** the simulator's theme, linked to its page, then its name ("Market replays / Panic Test").
- **Page head (every simulator):** crumbs, title (560, `clamp(1.5rem, 2.4vw, 2rem)`), a 0.875rem ink-2 tag on the right (mode and market, or round and score), over a `--rule-strong` rule.
- **Chart games (Trading Simulator, Panic Test):** only four things while playing. (1) One figure: you against the rival in signed points (`clamp(2rem, 4vw, 3rem)`/540, Rise and Fall Rule) over "ahead of / behind the Index" (Panic Test: "holding on"); the month and "In cash since month 13" on the right. (2) The chart, `clamp(300px, 50vh, 500px)` (320px on phones), the whole horse still behind it (175% of its height, `--horse-filter`, blend on its layer, opacity 0.13 light and 0.3 dark). (3) A 10px strip under it, ink while in the market and a 2px `--ink-3` line while out, then the key. (4) One row: the primary button (72px, "Go to cash" / "Back in the market"; Panic Test "Sell" / "Buy back", with a `Space` hint) and two 72px square ghost buttons, the speed (cycles 0.5x, 1x, 2x, 4x) and pause (pause and play icons). "How it works" is a closed disclosure under them.
- **Reading the position from the chart alone:** your line is heavy (2.6) in the market and light (1.2) out of it; stretches out of the market are `--chart-fill` bands labelled "Cash" (Panic Test "Sold") at their top; the head of your line carries an 8px dot, solid in the market and hollow out of it, and a label "You, in cash $9,616"; the rival's head carries "Index $10,151" in ink-3. The labels sit right of the day's dashed line, or left of it in the last quarter, and push apart when they would touch. The rival is dashed `--ink-3`.
- **Before the start:** a panel centred over the empty chart (ground at 92%): title ("Two hidden years of the S&P 500"; Panic Test "A crash is coming"), three sentences, chips for the game (Today's challenge, Random period; Trading Simulator only) and the market (S&P 500, Nasdaq, Euro Stoxx 50, Nikkei 225), Start, and a note on dividends.
- **End screens:** the word (Skill or Luck; Panic Test Steady, Well timed, Even or Panic; Guess the Fed "7 of 10") at `clamp(4rem, 11vw, 8.5rem)`/560 in ink (long words smaller), one sentence, Play again and Share; the full chart and strip on the right (Guess the Fed: the ten months as a ruled table). Share opens a panel below: the black 1200x630 image (owner's choice; chart games only), the text, LinkedIn, X, WhatsApp, Copy link, Save image. The image (owner-approved, 1 Nov 2026) is drawn in the browser by `drawCard()` in `assets/sim.js` on `#0a0c0d`: across the top, the dark transparent mark (30x34) and "Andra Markets" (28px/650) at 64px from the left, the word with a full stop (124px/560, smaller to fit 430px) and, from 520px, the sentence (30px, `#a8b0b4`, the points signed in `#1fd27a` / `#ff4b52`, zero in ink); below, the game's chart the full width (64 to 1136px, 254px tall) as on the end screen: bands out of the market (`rgba(233,236,235,0.08)`, labelled "Cash" or "Sold" at their top when they fit), the grid with dollar labels (18px, `#899196`), the rival dashed `#899196`, your line `#e9eceb` at 3.4 in the market and 1.6 out, then the 12px strip; at the foot, the key on the left (You, In cash or Sold only when you left the market, The Index or Holding on; 20px) and "Trading Simulator, on Andra Markets" (Panic Test) on the right. No large horse on this card. Then the reveal ("You traded March 1973 to February 1975: the oil shock bear market." with context and links; the Panic Test adds the fall and recovery in bold), one ruled line of figures, and "Your games and record" closed.
- **Guess the Fed:** an intro panel (`--ground-2`), then four figures in a ruled grid (CPI over 12 months, unemployment, the target, the 2-year yield; levels in ink with a note and a 24-month sparkline), "What does the Fed do this month?", three 72px ghost buttons Cut, Hold, Hike (the pick fills with ink), and the answer in a `--ground-2` panel: "Correct" or "Not this time", the month and the decision, the figures and the period, Next.
- **Portfolio Builder:** sliders for stocks and bonds (cash takes the rest) in ruled rows with the share at 1.375rem, Rebalance chips (Never, Every year), Run ten years (then Run again and New hidden years); the chart (your mix solid, the 60/40 dashed) drawing in over 2.4s (instant under reduced motion), three figures (final value, worst fall, against 60/40) and the reveal panel.

### Lab tool pages (`lab/`, `lab/<slug>/`)
Eleven tools drawn entirely in the browser (ten by `assets/lab.js`, the portfolio analyser by `assets/portfolio.js`): nothing entered is sent or stored. The index lists them in the four Lab themes of the Tools menu (owner-approved, 1 Nov 2026), each a heading in the archive month style (0.875rem/600 over a `--rule-strong` rule, its id the theme's id: `#options`, `#bonds`, `#risk`, `#valuation`) over its ruled list: Options (payoff diagram, Black-Scholes pricer), Bonds (price and duration, yield to maturity), Risk & portfolio (portfolio analyser, risk and correlation, two-asset frontier, position size and value at risk), Valuation & growth (discounted cash flow, compound growth, real return). Nine are calculators; the risk and correlation tool also loads the daily returns baked in at deploy (see README, Lab data). The dashboard page grid: head (crumbs: the tool's theme, linked to its page, then "Calculator", as "Options / Calculator", title, lede, "Runs in your browser. Nothing you enter is sent or stored." in the note meta style); inputs in columns 1 to 8: chip groups (strategy, coupon frequency) with a 0.8125rem ink-3 label above, then number fields in an auto-fill grid (label 0.875rem/550 with its unit in ink-3, input 52px, `--rule-strong` border, invalid as the signup error: ink border and inset ring, plus a 650 status line naming the field), a "Reset inputs" button; then the chart (dashboard plot: grid with round tick values, crosshair, dot, readout under pointer or arrow keys) and its key. "Result" panel in columns 10 to 12, the `.kpi` style, notes proportional. "How it works" and "Assumptions" below. Options payoff: today's profit or loss solid, at expiry dashed, gain and loss as `band-up` / `band-down` tints around the zero line, break-evens as dots. Bond: price against yield solid, the duration estimate dashed. Compound growth: value solid, paid in dashed over a `--chart-fill` area. Black-Scholes pricer: call or put chips and a "Chart" chip group (value, delta, gamma, vega, theta); value today solid, at expiry dashed (key hidden for the Greeks, which draw one line over a zero reference). Yield to maturity: price against yield solid with the solved yield as a dot. Two-asset frontier: the mixes as a solid curve in volatility (x) and return (y), the capital market line dashed, dots for A and B (labelled) and for the minimum-risk and highest-Sharpe mixes; the readout follows the nearest mix. Discounted cash flow: each year's cash flow solid, its present value dashed over a `--chart-fill` area. Position size and value at risk: VaR solid and expected shortfall dashed across holding periods, the loss at the stop as the `--rule-strong` reference line. Real return: value in money of the day solid, in today's money dashed; the real return and the simple difference are moves (signed, coloured). Every tool page has "How it works" and "Assumptions".
- **Portfolio analyser (`lab/portfolio-analyser/`; owner-approved mock, 11 Nov 2026, built with weights and amounts and in US dollars at the owner's word):** its own layout, not the calculator grid. Under the page head a `--rule-strong` rule, then two columns (5fr and 7fr, gap clamp(32px, 5vw, 88px); one column at 960px and below). Left, "Holdings" (section heads 1.375rem/400 with a 0.8125rem ink-3 line under them): two chip rows with their label to the left (Enter: Weights, Amounts in $; Period: 1 year, 3 years), the "Add a holding" combobox of the risk tool, then the holdings as a ruled list (56px rows): name over ticker, sector and country in 0.8125rem ink-3, a number field that is only a `--rule-strong` line under right-aligned tabular figures ("%" after it, or "$" before; ink line on focus) and a 44px remove button. With amounts, each row also shows its weight in ink-3 (hidden at 560px and below). A Total row over a `--rule-strong` rule, a polite status line (0.8125rem ink-2), and two plain actions, Equal weights and Reset. Up to fifteen holdings. Right, six sections parted by `--rule` hairlines: The portfolio (four figures at clamp(1.625rem, 2.6vw, 2.375rem)/300 with the S&P 500's beside each in 0.8125rem ink-3; two by two at 960px and below), Growth of 100 (portfolio a solid 1.6px ink line, S&P 500 a dashed 1.3px ink-3 line, gridlines `--chart-grid`, a readout under it that follows the pointer or the arrow keys), Where the risk comes from (per holding two 5px bars, weight in ink-3 over share of risk in ink, the share as a figure at the right), What it is exposed to (three ruled lists: sector, country, currency; stacked at 560px and below), How the holdings move together (a grid of correlations tinted in white by strength, never red or green, scrolling sideways when it does not fit) and In past falls (a ruled table). Red and green appear only on the signed return, the deepest fall and the falls of the past episodes. The standard How it works, Assumptions and pager follow, 46rem wide.
- **Risk and correlation (`lab/risk-correlation/`):** window chips (3M, 6M, 1Y, 3Y, default 1Y), weight chips (Equal, Custom), then "Add a company": a 52px search input (combobox) whose matches drop below it as a ruled list (44px rows, name 0.9375rem/500, ticker and country 0.8125rem ink-3, `--ground-2` on the active row; arrows, Enter and Escape work). Picked companies are a ruled list (52px rows, name 540 with the ticker in ink-3, a 44px remove button with the x icon; with Custom weights a 40px number field in %). Two to ten companies; the four largest US companies to start. The chart area is the correlation matrix in the dashboard matrix style (cell opacity `0.12 + 0.45 x |r|`, values in ink, a 1.5px ring on the pair under the pointer or arrow keys, the readout naming the pair, the sessions and the dates); under it a `.co-tab` table of company, benchmark, volatility, beta and weight (on phones name and benchmark over the three figures, each with its label in ink-3). The side panel is titled "Portfolio": portfolio volatility, weighted average volatility, diversification benefit, average correlation, most and least alike pairs, sessions in common. Correlations, volatilities and betas are levels: ink.

### Calendar (owner-approved mock, 22 Oct 2026)
One component, `.cl__table`, on three surfaces: the calendar page (`calendar/`), one archive page per week (`calendar/week/<monday>/`) and the homepage section. Built from `.cache/calendar/calendar.json` (see README, Calendar data).
- **Page head:** page title "Calendar", lede, then "Official schedules. Updated [date, time] ET." in the note meta style; `--rule-strong` under it.
- **Week tabs:** the existing chips (`aria-pressed`, gliding fill), one per week, Monday to Sunday: "This week, 19 to 25 Oct", "Next week, 26 Oct to 1 Nov", then three more by range. Five weeks, so at least four lie ahead. The tab holding today's New York date is pressed on load; a `#d-YYYY-MM-DD` link opens that day's week.
- **Filters:** four chip groups, each with a 0.8125rem ink-3 label (Type, Region, Earnings, Importance) to its left; at 640px and below the label sits above its own scrolling row. Type: All, Macro, Market structure, Earnings. Region: All, US, Euro area, UK, Japan, China; an earnings row also answers to its company's home economy (euro-area countries under Euro area, Hong Kong under China). Earnings (owner-approved mock, 22 Oct 2026): All, US, Europe, Asia, showing the markets together or apart; only earnings rows answer to it. Importance: All, High. A polite status line under them: "Showing all n events this week" or "Showing n of m events this week". With no JS the controls stay hidden and every week shows.
- **Table, desktop:** `--rule-strong` top rule; columns New York, Madrid, Event, Region, Type, Importance, Previous, Actual (head cells 0.8125rem/500 ink-2). Each day is its own `<tbody>` with a day row (0.875rem/600 ink, 28px top padding, 16px for the first day, `--rule-strong` bottom rule), grouped by the New York date. Rows: 14px vertical padding, `--rule` bottom borders. Event cell 1.0625rem/540, 34% wide, linked (no underline until hover) to the publisher's page, with its source under it (0.8125rem ink-3). Times are each city's local clock ("8:30 am", "2:30 pm"), converted per date, so the weeks when only one city has changed its clocks read right. At 1100px and below the Type column hides.
- **Order within a day:** all-day items (market structure), then by time; earnings before the open sit just before 9:30 am ET, after the close at 4:00 pm, and "Time not given" last.
- **Importance:** text, no colour, no marker: "High" in ink at 600, "Medium" in ink-2 at 0.875rem.
- **Previous and Actual:** Previous in ink-2; a change (m/m, q/q, a monthly change) is coloured as a rise or a fall, a level stays in ink. Actual, once released, is the figure as first printed, underlined in `--rule-strong` with an `arrow-up-right` icon, linked to the official release. A released event still waiting for its figure reads "Figures pending" (0.875rem ink-3). No consensus column.
- **Earnings rows** (US, Europe, Asia; owner-approved mock, 22 Oct 2026): Region shows the company's country. The two time cells merge into "Before open", "After close" or "Time not given", judged against the company's own market hours; a known time outside New York shows its New York and Madrid clocks instead, and the source line adds "Before the local open" or "After the local close". Under the company a row of square tags (`.cl__tags`, 6px gap): "Confirmed date" or "Estimated date", then the report type when it is clear (Quarterly results, Half-year results, Full-year results, Trading update). Previous is "EPS x.xx [currency], quarter to [Mon YYYY]" (diluted EPS a year earlier; the currency code on non-US rows); Actual the reported diluted EPS, linked to the company's financials on Yahoo Finance.
- **First session:** once results are out, a second line in the Actual cell (`.cl__react`, 0.8125rem): "First session" in ink-3, the stock's move at 600 coloured as a rise or a fall, then its benchmark and the benchmark's move that session ("S&P 500 +0.28%"), also coloured. Until that session closes it reads "First session not closed yet" (ink-3), for three days at most.
- **Rows without a time:** "All day" (market structure) or "Time not given" (a release the publisher dates but does not time, such as Bank of Japan decisions), across both time cells.
- **Today:** the day row reads "Today, Thursday 22 Oct" and that day's rows sit on `--ground-2` (full bleed on mobile). Checked again in the browser against the New York date, since the page is built ahead.
- **Mobile (640px and below):** head row hidden; each row is a grid of `4.75rem | 1fr | auto`: New York time over the Madrid time (with a 0.75rem ink-3 "Madrid" under it) on the left, the event with "[Region]. [source]" under it in the middle, importance on the right; Previous and Actual below the event at 0.875rem with their label from `data-label`. Region and Type cells hide; empty cells disappear.
- **Sources:** an inner page section (h2 1.375rem/540) after the table: how the figures are read, then a ruled list of every source with the day of its copy (0.875rem; date ink-3, right-aligned; stacked on mobile). A failing source reads "Last good copy [date]", a figures source "Last good figures [date]", one never read yet "Not available yet". Ends "For information only. Not investment advice."
- **Week archive page:** crumbs "Calendar / Week of [date]", title "Week of 19 Oct", the filters without tabs, the week's table, a pager (previous and next week, "The calendar, five weeks ahead"), then Sources.
- **Homepage section:** the section head links "Full calendar" to `calendar/`; the table shows today's and the rest of the week's high-importance rows (carrying into next week late in the week), up to ten.
- **Close notes:** from the calendar's first week on, each note's pager carries "The calendar for this session", linking to `calendar/week/<monday>/#d-<date>`.

### Daily note module
Not on the homepage since 31 Oct 2026. "Daily note" in the nav, the footer and the homepage index opens the note archive (`reports/`: every close note, newest first, grouped by month); the footer's "All notes" link went, as it led to the same page, and the search lists the archive as "Daily close notes".
- **Latest (columns 1 to 6):** section title, then an article: note title (note-title style, 28px above), summary (max 46ch), meta row (date and read time, 0.875rem ink-2, 20px gap), and a primary "Read the note" button.
- **Archive (columns 8 to 12, bottom-aligned):** a label line ("Every US trading day, after the close.", 0.875rem ink-2) over a `--rule-strong` rule, then a ruled list of rows `7rem | title | 20px arrow`, 18px vertical padding. Hover underlines the title and nudges the arrow 4px. Mobile stacks date above title. An "All notes" link follows.
- **Real notes:** the latest note fills the article (headline in ink, standfirst as summary, read time from the word count at 230 words a minute) and the archive lists the three before it. Dates are `<time>` in ink-2 with tabular figures ("9 Oct 2026"; 0.8125rem on mobile). Until a note is published the placeholders stay.

### Note archive (`/reports/`)
An inner page. Head: page title "Daily close notes", lede "Every US trading day, after the close. [n] notes. Weekly reviews and research are in the Research Library." Body (max 44rem): notes grouped by month, newest first. Each month opens with a heading styled like a calendar day row (0.875rem/600 ink, 28px top padding, 16px for the first, 12px bottom, `--rule-strong` bottom rule), followed by the note list rows with the date as "9 Oct".

### Research Library (`/research/`, owner-approved mock, 30 Oct 2026)
Only the reports that are not the daily note: weekly market reviews and research (owner: the library must not read as "daily note 2.0"). An inner page; the owner rejected a dark plate band, so everything sits on the ground.
- **Head:** title "Research Library", lede "Weekly market reviews and research from Andra Markets: longer than the daily note, written to be kept." Under it a count row (0.875rem ink-2): "[n] weekly reviews", "[n] research reports", "Looking for the daily note? All close notes" linking `/reports/`.
- **Lead:** the latest weekly review on the 12-column grid. Columns 1 to 7: a kicker row over a `--rule-strong` rule ("Latest weekly market review" left, "Week [ISO week] · [Mon–Fri]" right, 0.875rem ink-2), the title at `clamp(2.25rem, 4.6vw, 4rem)`/540, line height 1, -0.04em, balanced; the summary as lede; meta (long date, read time, topics); then "Read the review" (primary) and the locked PDF button. Columns 9 to 12, bottom-aligned: "In this issue" (0.875rem/600 over `--rule-strong`), the review's section headings numbered 01, 02… (0.9375rem ink-2, numbers ink-3 tabular, `--rule` hairlines). Stacks at 960px. With no weekly review: the kicker and "The first weekly market review is on its way."
- **Tools (JS only, when there are reports):** one row: the search field (48px, max 420px) and topic chips with counts (All topics, Equities, Rates, FX, Commodities, Macro, Credit; a topic with nothing has no chip). Both combine and filter the earlier reviews and research (the lead stays); the choice is kept in the address (`?tag=&q=`); status "Showing n of N earlier reviews and research: [choices]"; no match shows "Clear the search".
- **Weekly market reviews:** section head (h2 `clamp(1.5rem, 2.4vw, 2rem)`/540 left, "Every Friday after the close…" 0.875rem ink-2 right, `--rule-strong` under). Earlier issues in a hairline lattice, 3 columns (2 at 960px, 1 at 640px): "Week [n]" at 2.5rem/540 tabular, the Mon–Fri dates (0.8125rem ink-3), title (1.125rem/540), summary (ink-2, two lines), and a foot row of topics and read time (0.8125rem ink-3). Hover fills `--ground-2` and shows the `arrow-up-right`.
- **Research:** a ruled list: topic (0.875rem/550 ink-2) in a 9rem column, then title (`clamp(1.25rem, 2vw, 1.625rem)`/540), summary (ink-2), date and read time (0.8125rem ink-3), arrow right. On phones the topic sits above the title. Empty: "The first research report is on its way."
- **Report page (`/research/<slug>/`):** the report page head with crumbs ("Research Library / [type]"), title, summary as lede, meta (long date, type, read time), then the share row. Body: the Markdown's sections (h2, paragraphs, ruled lists, a "Source:" line at 0.8125rem ink-3), then "About this report" with the disclaimer and a link to the legal notice. Pager: previous and next report, Research Library, Get reports by email.
- **Locked PDF (paused, owner 31 Oct 2026):** removed from the close notes with every subscribe entry point (see Signup form); the spec is kept for when the paid tier opens. A ghost button with the lock icon, "Download PDF" and, after a `--rule` hairline, "Subscribers only" (0.8125rem/450 ink-3); `aria-disabled`, ink-2 label, not-allowed cursor, no press scale. Pressing it writes "PDF downloads open to subscribers with the paid tier. The full text is free to read here." in the status line beside it. No file sits behind it.
- **Sources:** `data/reports/index.json` plus one Markdown file each; `tools/import_report.py` converts a PDF. The PDF is never committed or published.

### Markets Interview Prep (`/interview-prep/`)
An inner page from one data file, `data/interview_prep.json`, rewritten weekly. Head: title "Markets Interview Prep" and lede. Body (44rem):
- **What you need to know this week:** meta row ("Week of [Monday]", "Updated [date]"), intro, then five to seven numbered topics under a `--rule-strong` rule, rows split by `--rule`: the number (0.875rem/600 ink-3, tabular) in a 2.5rem column, title (1.125rem/540, balanced), then "What happened", "Why it matters", "Say it in an interview" as labels (0.8125rem/600 ink) over ink-2 text, and "From the close notes of [dates]" (0.8125rem ink-3) linking each session's note. Every figure comes from a published close note; prose stays in ink.
- **Question bank:** subject chips with counts (wrapping in the column above 640px, scrolling on phones) and a status line; then the methodology accordion in its multi-open variant (`.acc--multi`): any number of answers open, all closed at first. Each question shows its subject above it (0.75rem/550 ink-3). Answers are ink-2 paragraphs or a ruled numbered list, closed by "Likely follow-up:" (label in ink, 600).
- **How to use it:** a short note and the disclaimer.

### Chart of the day (`chart-of-the-day/`, `chart-of-the-day/<date>/`, owner-approved sketch, 1 Nov 2026)
One chart per session from its close note; `chart-of-the-day/` shows the latest (`tools/page_chart_of_the_day.py`, `assets/chart-of-the-day.js`). Inner page head, then the session: its long date (1.1875rem/540) with previous and next session buttons on the right (44px squares, `--rule-strong` border, the caret turned; ink fill on hover; the missing one at half opacity in `--rule`). The chart is the note's own margin chart (Report page, Bar charts and Curve chart), same markup, in a card with a 1px `--rule-strong` border and `clamp(20px, 3vw, 28px)` padding, its title promoted to an h2 at 1.375rem/540 and its source and date under it. The column is 30rem wide, so the chart's 12-unit labels read at about 16px on a laptop and 13px on a phone. Under the card two lines: the reading (1.0625rem ink), built from the chart's figures (what rose and fell most, signed and coloured, and how many rose), and a quote from the note's section beside the chart (ink-2, a 1px `--rule-strong` rule on its left, "The close note, [section]" under it in 0.8125rem ink-3). Then "Read the close note" (text link) and "Share this chart" (the note's Share button; it always shares the session's own page), and a source line (0.8125rem ink-3) naming the note and its edition, with the figure-check statement when the note failed it. The chart is chosen by rule: of six charts (sectors, global indices, currencies, commodities, volatility, digital assets), the one whose median absolute move is largest against its median over its previous 20 sessions; sectors on the first session. "Every chart" is the FX archive pattern, each row adding the chart's largest move in 0.875rem ink-2.

### Market history (`market-history/`, `market-history/<slug>/`, owner-approved sketch, 1 Nov 2026)
The Trading Simulator's 36 US episodes, text as written (`tools/page_market_history.py`, `assets/market-history.js`). Index: inner page head with the meta row, "The S&P 500 since 1928" (inner page h2): daily closes on a log scale, each episode's fall from peak to low in `--down-tint`, years along the foot, crosshair and readout naming the episode under the pointer (a click or Enter opens it); then "Every episode", a ruled timeline: years (0.875rem ink-2, tabular), name (1.0625rem/540), the fall as an 8px `--down` bar scaled to the deepest and the signed figure in `--down-text`, arrow; a 0.8125rem ink-3 head row over a `--rule-strong` rule. The bar goes at 960px; at 640px years sit over the name. Episode pages use the dashboard page grid: crumbs, the episode's name as title, meta (period, "Episode n of 36", the fall). The chart (columns 1 to 8, drawn at pixel width) runs from the peak to the day it was regained: line `--chart-line`, the fall in `--down-tint`, the peak's level as a `ref` line from the peak to its recovery, dots and labels (550 ink with a ground halo) for Peak, Low and Back at the peak, the episode's months in `--chart-fill` when the chart runs past them; the readout adds the change from the peak in red or green. "The fall in numbers" (`.kpi`, columns 10 to 12): fall, peak to low; to the low (months and sessions); peak; low; back at the peak; over the episode. Then What happened, Play it (a primary button to the Trading Simulator at the episode's two years), On Andra Markets (the episode's links) and How the figures are measured. Without data: "Data pending" in the chart box and the panel.

### Interview simulator (`interview-simulator/`, owner-approved sketch, 1 Nov 2026)
A timed mock interview, answered aloud, from `data/interview_simulator.json` and the questions of the technicals and Interview Prep (`assets/interview-sim.js`, `tools/page_interview_simulator.py`). Head: title, lede, meta ("[n] questions in [n] topics", "Your progress stays in this browser"). Track (IB, S&T, AM/ER) and Length (10, 20, 30 min) chip groups side by side, each with its 0.8125rem ink-3 label; during an interview they are disabled at 0.5 opacity. One card in the practice card style (1px `--rule-strong`, max 52rem): meta row ("Question i of n", topic) with the clock on the right in the mental maths drill's look (0.875rem/600 ink, tabular, `role=timer`, announced only at 30 seconds left and at time up through a polite live region; "Time is up" in ink at 550 beside it; it never moves on); the question at 1.25 to 1.5rem/540; "Answer aloud; notes are optional." (0.875rem ink-2) over a notes field (96px, `--rule-strong` border, square); "End the interview" (text button) left and "Show the model answer" (primary) right. The answer opens under a `--rule-strong` rule across the card (fade and 6px rise over 260ms, none under reduced motion): labels at 0.8125rem/600 ink ("Model answer", "Key points", "How did you do?"), the answer in ink-2 with "Likely follow-up:", key points in ink each after a check icon, three ghost buttons Nailed it, Partly, Missed (the pick fills with ink; three equal columns on phones), then "Next question" (primary, disabled until a rating). Results: counts as the heading, the score and best in ink-2, a ruled table by topic (name linked to its page, a "To review" tag, source in ink-3; ratings right-aligned, tabular) and the ruled list of questions asked. Ratings, scores and the clock are not rises or falls: ink only. Focus moves to the question, then the "Model answer" label, then Next, then the results heading. Without JavaScript a note and the topic table, whose rows link every page.

### Contact us (`contact/`, owner-approved mock, 8 Nov 2026)
- **Button:** "Contact us", a small ghost button (40px, 0.875rem, square, `--rule-strong` border, ink label; fills with ink on hover), linking to `contact/`. Above 520px it sits at the right end of the header on every page: after the search on inner pages (16px to the legal line on the homepage at 960px and below, 24px above). At 520px and below the header hides it with its other buttons and it sits at the foot instead (owner: "en el movil ponlo abajo"): on inner pages in the footer, under the brand line, where it shows at every width; on the homepage, which has no footer, centred under the four groups at the foot of the screen (24px from the bottom, or the safe area), where the horse and the names keep sitting as one block between the phrase and it, so the screen still does not scroll (checked at 360x740, 375x667 and 390x844). While a group is open its sections show over that room, so the button gives way (hidden) until it closes. On the homepage both forms follow the header and the index: clear while the particles form the text, in at 450ms once it settles, gone at once when the hero leaves; without WebGL the foot button rises in with the hero copy (`--i:3`).
- **Page:** an inner page. Title "Contact us", lede "Questions, corrections or ideas for Andra Markets: write to us, or follow the research on LinkedIn and TikTok." The body is a ruled list under a `--rule-strong` top rule, one row per way in, `--rule` between them, at least 92px tall: the icon (1.5rem; `envelope-simple`, then each channel's logo from `SOCIALS`), the name (1.375rem/540, -0.02em; 1.1875rem at 640px and below) and the address under it (0.9375rem ink-2; 0.875rem on phones): andramarkets@gmail.com (`CONTACT_EMAIL`), linkedin.com/company/andramarkets, @andramarkets. The email row opens the visitor's mail app (`mailto:`) and ends with a "Copy address" small ghost button ("Copy" at 640px and below); it swaps to a tick and "Copied" for 2.4s as the share button does, and says "Email address copied." to screen readers. Without the clipboard it shows "Select the address and copy it: ..." under it; without JavaScript the button is hidden. Each channel row ends with the arrow up and to the right (1.25rem) and carries `rel="me"`. On hover the name underlines (1px `--rule-strong`) and the arrow moves `translate(2px, -2px)`. Under the list, in ink-3 at 0.875rem: "Andra Markets does not give personal investment advice: see the legal notice."

### Data sources, legal notice, privacy (`/sources/`, `/legal/`, `/privacy/`)
Inner pages. **Data sources:** a ruled list, one row per provider: name as a link (1.0625rem/540), what it supplies (ink-2), then a two-column definition grid (0.875rem; labels "Used in", "Updated" in ink-3 at 5.5rem). **Legal notice and Privacy and cookies:** text from `tools/legal_content.py`; "On this page" contents (0.875rem/600 heading, a numbered two-column list at 0.9375rem, one column on phones, ink-2 links), then one section per heading, closed by "Last updated [date]" in ink-3. Bracketed placeholders mark details the owner must supply.

### Report page (`/reports/<date>/`)
An inner page, one per note.
- **Head:** the headline in the section title scale (540, `clamp(2rem, 4.2vw, 3.5rem)`, 1.02, -0.035em, balanced): a model headline runs 8 to 13 words, too long for the page title scale. Then the standfirst as the lede, the meta row (long date, edition, read time; 0.875rem ink-2, 20px gaps, 20px above), then the share row 28px below: a primary "Share this note" button and a polite status line beside it (0.875rem ink-2, 20px gap). The button (link icon) opens the system share sheet where the browser has one, else copies the page link: its label swaps to "Link copied" with a tick that draws in (220ms blur cross-fade, 2.4s, then back), and the status line says "Link copied." to screen readers only. If copying fails it shows the link to copy by hand. The row is hidden without JS. On mobile the button goes full width. No meta or label above the headline (no eyebrows).
- **Body:** inner page sections in reading order, each only when it has text: Takeaways, Desk view, What we watch, Equities, Rates, Credit, FX, Commodities, Volatility, Digital assets, International, Correlation, then Sources (with the figure check statement and "For information only. Not investment advice."). Takeaways and What we watch are ruled lists: `--rule` top border, rows padded 12px with `--rule` separators, ink-2 text. Consecutive paragraphs are 12px apart.
- **Layout and side panel.** The report is a 12-column grid. At 1280px and up: text (head and sections) in columns 1 to 6, margin charts in 7 to 9, and the panel "The session in numbers" in 10 to 12, sticky (`top: nav-h + 24px`) for the whole article. From 961px to 1279px: text 1 to 7; the panel (not sticky) and the margin charts share columns 9 to 12. At 960px and below: one column, the panel after the head (summary and Share), each margin chart right after its section, closed by a `--rule` hairline.
- **Panel contents:** title at 0.9375rem/600 over a `--rule-strong` rule (the tape head style); a 2-column ruled grid in the tape item style (name 0.8125rem ink-2, level 1.1875rem/500 tabular, change 0.875rem tabular and coloured as a rise or a fall, `--rule` hairlines, no boxes): S&P 500, Nasdaq 100, US 10Y yield, VIX, risk score with its label, breadth as "up / down"; then a source line (0.8125rem ink-3). It is short enough to fit any desktop viewport.
- **Margin charts:** one per section that has data in that note, aligned with the section's heading (28px top padding), title at 0.9375rem/600, source and date under it (0.8125rem ink-3), with a count of instruments left out when they had no print that day. Takeaways: the day's moves (tape instruments in percent). Desk view: biggest gainers and losers from the watchlist. Equities: S&P 500 sector ETFs. Rates: the Treasury curve. Credit: listed proxies (LQD, HYG, EMB, BKLN, IEF, TLT). FX: dollar index and five pairs. Commodities: WTI, Brent, natural gas, gold, silver, copper. Volatility: VIX, VIX 9-day, VIX 3-month, VVIX, MOVE. Digital assets: bitcoin, ether, solana, XRP. International: Euro Stoxx 50, DAX, FTSE 100, Nikkei 225, Hang Seng, KOSPI, Bovespa, S&P/TSX. A chart with fewer than 3 instruments is not drawn.
- **Bar charts** (all margin charts but the curve): diverging horizontal bars from a dashed zero line, sorted by change, `--up` / `--down` fills, signed value at the right in `--up-text` / `--down-text`. Direction and the signed label carry the polarity too, so colour is never the only cue (the red and green pair falls below the colour-blind separation target in the light theme, so this redundancy is required). No key: one series.
- **Curve chart:** the latest published curve (solid `--chart-line`, dots) against the session before (dashed `--ink-3`), tenors spaced by square root of maturity, 3 gridlines with yield labels, key with the two dates, source line naming the close it shows. FRED usually publishes after the note is written, so the curve is normally the previous session's and the source line says so.
- **All report charts** are real data: no "Illustrative" stamp. 300-unit-wide inline SVG; text 12px (labels ink-2, values ink and tabular). Each SVG has an aria-label listing its values and a native tooltip per mark.
- **Pager:** text links below the body, 32px above, 24px apart: "Previous note, [date]", "Next note, [date]", "All notes", "Get the note by email" (to the signup plate).
- **No downloads.** The site is the free tier: no PDF, facts file or data download is linked or published anywhere (see PRODUCT.md, Business Model). The deploy fails if a PDF, JSON, CSV or XLSX file reaches the published site.

### Inner page (`.page`)
For methodology and future sub-pages, sharing the same header and footer. Top padding `nav-h + clamp(48px, 9vh, 112px)`, bottom `--section`. The head is max 44rem: page title and lede (16px gap) over a `--rule-strong` bottom rule, with `clamp(32px, 5vw, 56px)` padding. The body is max 44rem: sections padded 28px with `--rule` bottom borders, h2 at 1.375rem/540, paragraphs ink-2 max 65ch. The header is solid from the first paint.

### Methodology questions (owner-approved, 22 Oct 2026)
A "Questions" section closes the methodology body: an accordion under a `--rule-strong` top rule, rows separated by `--rule` hairlines. Each question is an h3 button (1.0625rem/540 ink, 16px vertical padding, plus sign that turns to a minus); the answer is ink-2 body text. One answer is open at a time, the first by default (the Interview Prep question bank uses the multi-open variant). Panels open to their own height (grid rows, 380ms ease-out) and the text fades in 80ms later. Without JS every answer shows.

### Search
- **Button:** in the header after the nav, hidden without JS. Above 1200px a 40px outline button (`--rule` border, magnifying glass, "Search", and the shortcut "⌘K" or "Ctrl K" after a hairline in ink-3); at 1200px and below a 44px icon button like the menu button.
- **Palette:** ⌘K or Ctrl K (or "/") opens it from any page. A scrim (`--scrim`) over the page and a 560px panel at 12vh: ground fill, `--rule-strong` border, square, no shadow. A 56px input row, then results grouped as Companies, Dashboards, Close notes, Reports (weekly reviews and research) and Pages (group labels 0.8125rem ink-3), each row a title (0.9375rem/500) and meta (type or date, 0.8125rem ink-3). A `--ground-2` band glides to the active row (220ms); arrows move it, Enter opens, Esc or a click outside closes and returns focus. Opens with a fade and `translateY(-8px) scale(0.985)` to rest over 240ms.
- **Index:** `assets/search-index.js`, written by `tools/build_site.py` from the dashboards, the published notes and the main pages, loaded the first time search opens (a .js file because the deploy refuses JSON). Matches the title first, then keywords (descriptions, sources, dates); letters-in-order matching only from four characters.

### Company pages (owner-approved, 22 Oct 2026)
The 1,200 companies of the earnings calendar's universe (owner's request, 11 Nov 2026; it was 600 since 28 Oct 2026): the 400 largest in the S&P 500, in the STOXX Europe 600 and across the six Asian markets, one listing each, read from the calendar cache by `tools/company_data.py` at deploy time; `assets/company.js` draws the charts at each chart's pixel width. Prices are in the currency the shares trade in (pence shown as pounds), report figures in the currency the company reports in, each with its own symbol (`CUR_SYMBOL` in `build_site.py`); ratios that mix them (P/E, price to book, the cash flow model) convert at today's rate.
- **Index (`/companies/`):** inner page head, two rows of filter chips (filter chip component, with its glide): markets (All, US, Europe, Asia), then sectors; both apply at once, and a status line names them, then a table under a `--rule-strong` top rule: rank by market value in dollars across the three markets (ink-3), company (540, ink, links to its page) with the ticker in ink-3, sector, close in its own currency, day change, market value in dollars and P/E, numbers right-aligned in tabular figures, `--rule` row borders, `--ground-2` on row hover. At 640px and below each row is a grid: rank, name over sector, close over day change; market value and P/E are hidden. Source line names the membership sources (State Street, iShares, Yahoo Finance's screener) and Yahoo Finance with the close date.
- **Company page (`/companies/<ticker>/`, dots as hyphens: `/companies/asml-as/`):** the dashboard page grid. Head: crumbs (Companies / sector), the common company name as page title (`CO_NAMES` in `build_site.py`), then the close (540, `clamp(1.75rem, 3vw, 2.25rem)`, tabular), the day's change in ink-2 and the ticker, exchange and close date; a one-sentence lede built from the figures (sector, revenue, growth, operating margin); then "Add to portfolio monitor" (primary) and "Alert me on results" (ghost), which say in a status line that the feature is coming soon. Right: "Key figures", the report panel style: market value, P/E on the last four quarters' diluted EPS, revenue growth, operating margin, free cash flow and net debt (net income and shareholders' equity with price to book for banks, insurers and asset managers), dividend yield, 52-week range; source line with the fiscal year, balance sheet and close dates.
- **Sections (left, 8 columns):** "Against its peers": five strips (P/E, revenue growth, operating margin, debt to equity, dividend yield), peers as hollow `--ink-3` dots, the company filled ink, the median a dashed tick; the axis spans the 5th to 95th percentile and a dot beyond it sits on the edge, dashed. Peers are the company's sector among the 200 of its own market (US, Europe or Asia), or all 200 when the sector has fewer than four. A readout names the dot under the pointer. "Valuation": a ten-year discounted cash flow model on the last fiscal year's free cash flow with three range inputs (growth years 1 to 5, discount rate, growth after year 10; square 4px ink thumb on a `--rule-strong` track), the value per share and the growth the price implies (solved for), and a bar chart of discounted flows (`--chart-fill` with ink outline; the value after year 10 solid ink). Not drawn for banks, insurers and asset managers, or when free cash flow is not positive: a sentence says why. "Valuation over time": month-end P/E on the last fiscal year's diluted EPS known at the time (solid line) against its average (dashed `ref` line), crosshair and readout. "Where revenue goes" (replaces the waterfall, owner's request): a sentence in ink ("Of every $100 of revenue ... kept $40 as net income"), one full-width 40px bar split into costs and tax (`--down`, each line a step lighter) and net income (`--up`), the share of revenue printed inside segments wide enough, a "Revenue" tick when other income takes the bar past revenue, then one row per line: swatch, name, $bn and share of revenue (on phones $bn and share on one line). "Revenue and profit, N years" (revenue `--chart-fill` outlined, net income ink), "Last N quarters" (revenue and diluted EPS side by side, one shared readout with revenue growth on a year earlier), "Cash flow and investment" (cash from operations outlined, capital spending `--down` below zero, free cash flow ink), "Balance sheet" (cash outlined, debt ink, equity dashed outline) and "Returns to shareholders" (dividends ink, buybacks outlined, net income as a line with dots): column charts with a zero line, gridlines labelled on the right in $bn, a `--ground-2` band on the column under the pointer and a readout for it (arrow keys too), starting on the latest. "Share price returns": a table of 1 month, 3 months, year to date and 1 year for the company (600), its sector average among the 200 of its market and its benchmark (the S&P 500 for the US, the STOXX Europe 600 for Europe, each Asian market's main index). "Against the market": the company (solid) and its benchmark (dashed `--ink-3`) rebased to 100 over a year, crosshair and readout as on dashboard pages. "Investment memo": a `--rule-strong` bordered notice that the memo comes with the subscription, with what it will hold and a button that says subscriptions open soon. "Risk" (after "Against the market"): four figures in the key figures style (volatility over a year, annualised, with the benchmark's; beta to the benchmark from daily returns; the deepest fall of the year with its dates; how far below the year's high it closed), then the drawdown chart: the fall from the highest close so far as a line over a `band-down` area, 0% at the top. "Ahead": the next results date from the calendar (linked to its week), or a sentence that none is posted yet.
- **Logo (owner's requests, 22 Oct 2026):** the company's official logo (SVG from Wikimedia Commons, else a PNG) large in the empty right side of the head, beside all of its text, cut out on the page ground: no plate or border. `company.js` measures the drawn outline on a canvas and shows only that, as large as a `clamp(160px, 24vw, 320px)` by `clamp(110px, 13vw, 190px)` area allows, right-aligned and vertically centred (at 760px and below, up to 112 by 64px beside the crumbs and title). One-colour logos take the theme's ink (a black logo turns light on the dark theme, a white one turns ink on the light theme); on the dark theme a colour logo with black, grey or navy lettering flips its lightness and keeps its hues (`invert(1) hue-rotate(180deg)`). Logos with a background of their own, and deep reds, are left as they are.
- **Colour:** The Rise and Fall Rule: the day's change in the head (both the dollar and the percentage), revenue growth in key figures and the peer strip label, period returns, the deepest fall and distance below the high, signed percentages in every readout, and the day column on the index. Levels (prices, margins, P/E, EPS, yields) and prose stay in ink.

### Live company data (owner-approved mock, 29 Oct 2026; merged into Companies, 30 Oct 2026)
The Company profile section was merged into Companies (owner's request, 30 Oct 2026): one section, no second nav entry. `assets/profile.js` fills it in the browser from the profile API (`worker/`); `/profile/` only forwards old links.
- **Search on the index (`/companies/`):** under the head, above the market chips: the palette's field set on the page (56px, `--rule-strong` border, magnifying glass in ink-3, "Enter" hint), max 640px, focus outline in `--focus`. Typing filters the table at once (ticker or name, together with the chips; the status line adds the query). Below the field, "Other US-listed companies" (0.8125rem/550 ink-3) lists matches outside the 1,200 in the same bordered list as the palette (ticker 600 tabular in a 5.5rem column, name beside it, the active row `--ground-2`, arrows move). Enter opens the exact ticker, else the first match in the table, else the first other company. A status line (0.875rem ink-2) says when nothing matches, or that a ticker given in a link does not trade and what matches its name.
- **US company pages of the 1,200:** the head's close becomes the live price, its day change (Rise and Fall Rule) and "Live, 3:42 pm ET" with a 6px ink dot that fades slowly (still under reduced motion) when the quote is under 15 minutes old, else "Last price" with its date; it refreshes every minute and falls back to the close. After "Risk", before "Investment memo": News (ruled list: headline 0.9375rem/500, publisher and age in ink-3 with an out arrow) and What analysts say (one 28px bar split in ink steps, strong buy darkest; never red or green, as it is not a rise or a fall). European and Asian pages are unchanged: the free price feed covers US listings only.
- **Other US companies (`/companies/live/?t=TICK`):** the company page grid filled live. Head: crumbs ("Companies / sector") with a compact search field (40px, max 280px) on the right; the name; the live price as above; a lede from the figures; the two "coming soon" buttons; a sticky section index under the header (0.875rem/500 ink-2, the section in view in ink with a 2px underline, sideways on phones). Right: "Key figures" (market value, P/E, EV/EBITDA, price to sales, free cash flow yield, net debt or net cash, dividend yield, 52-week range with beta). Sections: Overview (description, facts as a ruled grid of label over value); Revenue and profit, N years (the company page's column chart); Margins (gross solid, operating dashed `--ink-3`, net dotted ink; levels, in ink); Financial statements (three chips as tabs, a table with a sticky first column scrolled to the latest year on phones); Multiples (P/E at each fiscal year end against its dashed median, then now, 5-year average and peer median); Peers (table, the company's row in 600, peers linking to their pages); News; What analysts say; Investment memo (`co-gate` with the memo's outline greyed). A ticker among the 1,200 goes to its own page; one that does not trade goes to the index search with its name.
- **Loading and errors:** each part loads on its own. Loading: blocks in `--ground-2` with the shape of the content, fading between full and half opacity over 1.6s (still under reduced motion). Error: a `--rule-strong` box with the warning icon, a sentence in ink saying what did not load, a note in ink-2 on why and what happens next, and a ghost "Try again" button; when the source is busy it retries on its own. Errors are never red. A saved copy served during an outage carries its date in the source line.

### Asset versions
Every page links its stylesheets (`site.css` and `theme.css`, or `home.css` on the homepage), its scripts and the particle map with `?v=` and a short hash of the file (`ver()` in `build_site.py`), so a browser fetches them again whenever they change instead of showing a new page with an old stylesheet.

### Motion components and licence
The rolling figures, chip glide, theme reveal, search palette, share swap and questions accordion were adapted from beUI (owner-approved proposal, 22 Oct 2026), rewritten in plain JS and CSS with these tokens: square, flat, ink only, no bounce. beUI is MIT licensed; its notice is kept in `assets/LICENSE-beui.txt` and cited at the top of `assets/site.js` and the components block of `assets/site.css`.
The theme reveal and the chip glide are no longer in use.

### Placeholder tokens
Every unknown value is a bracketed placeholder (`[date]`, `[live]`, `[source]`, `[n]`, `[handle]`, `[Company]`...). The generator wraps every `[...]` in `.ph`, which renders in `--ink-3` (plate-ink-2 on the plate). `.ph--ink` renders in full ink and is used where the placeholder stands in for a headline or title (note headlines, video titles, the tape's headline).

### Charts
- **Series:** primary series solid, `--chart-line`, 1.6 stroke, round joins. Comparison series dashed, `--ink-3`, 1.3 stroke, `4 4` dash. Strokes are `non-scaling-stroke`.
- **Grid:** 3 or 4 horizontal lines in `--chart-grid`, 1px. Reference or zero lines use `--rule-strong`, 1px, dash `3 4`.
- **Marks:** 2.5px radius dots in chart-line on key points; areas in `--chart-fill`; bars and heatmap cells in `--up`/`--down`; regime bands in `--up-tint`/`--down-tint`.
- **Heatmap:** cell opacity `0.45 + 0.55 x |value|`, so the floor is 0.45 and no cell fades into the ground. Cells have a 3px gap.
- **Boxes:** tiles use a 320x160 viewBox in a 2:1 box; Lab charts 640x260; explainer 560x240. Time series stretch (`preserveAspectRatio="none"`); shaped charts (curves, heatmaps, matrices) keep their aspect.
- **Key:** below every chart, 0.8125rem ink-2: a 16px solid or dashed line swatch for series, a 12px square for up/down, then the "Illustrative" stamp.
- **Accessibility:** each SVG is `role="img"`. An illustrative chart's aria-label ends ", illustrative, not market data"; a real one lists its values and dates.
- **Data:** real figures with a source and date, or a schematic seeded random walk stamped Illustrative. Never invented figures.

### Brand assets
- **Favicon and touch icon** (`assets/favicon-32.png`, `assets/favicon-48.png`, `assets/apple-touch-icon.png` at 180px): a head-and-neck crop of `andra-horse.png` (source box x462 to 646, y252 to 436) on its own black ground, pixels otherwise unaltered, resized with Lanczos. The owner asked for "a favicon (head and neck crop of the horse)" and approved the proposal as shown. This is the only approved crop of the mark.
- **Header and footer marks** (`assets/andra-mark-dark.png`, 140x160; `assets/andra-mark-light.png` is still made and shipped but no longer shown): made by `tools/make_mark.py` from `andra-horse.png`. The black ground is removed (alpha from luminance: 6 and below is transparent, 160 and above opaque, so the engraving's grey shading stays as partial transparency), the empty margin is trimmed to a 6px pad, and the horse is set in each theme's ink (`#0e1215` light, `#e9eceb` dark). The whole horse is kept, shapes untouched. Owner-requested to remove the box the old blend technique showed on mobile. Regenerate with `python3 tools/make_mark.py`; never edit by hand.
- **Homepage particle map** (`assets/horse-particles.webp`, 681x774, lossless): made by `tools/make_horse_particles.py` from `andra-horse.png`. The horse's box (source x278 to 732, y258 to 774) is upsampled 1.5x with Lanczos; each pixel's red channel is its ink in the header mark's look, with the faintest shading dropped and a gentle curve; the green channel marks the outline. The homepage places its particles by this map and then shows the red channel as the finished engraving. Nothing is redrawn: every value comes from the original engraving.
- **Social share image** (`assets/og-image.png`, 1200x630): the full, uncropped horse screen-blended on `#0a0c0d` at 0.62 opacity with a radial vignette, the wordmark (1.625rem/650) and the hero line set in Schibsted Grotesk (84px/560, -0.04em), sub in `#a8b0b4`. Owner-approved as shown. Every page's head carries icon links, Open Graph and Twitter card tags; canonical and `og:url` are emitted only once `SITE_URL` is set in `tools/build_site.py`. Close notes say `og:type` article with their publication time; redirects carry `noindex`. Structured data, the sitemap and the feed are invisible: see README, Search engines, link previews and the feed.
- **Close note share image** (`reports/<date>/og.jpg`, 1200x630, owner-approved 31 Oct 2026): drawn at build time by `tools/og_note.py` (Pillow; the deploy installs it) on the social share image's ground: `andra-horse.png` whole, untouched, screen-blended at 0.62 on `#0a0c0d` at the right with the radial vignette; the dark transparent mark (34px) and "Andra Markets" (26px/650) at 72px from the left and 64px from the top; "Close note, Friday 30 Oct 2026" (22px/400, `#a8b0b4`); the note's headline (54px/560, -0.035em, 1.04, balanced over at most three lines within 700px; 48, 42 or 38px when it needs more); and, on a hairline rule, four daily changes (S&P 500, Nasdaq 100, VIX, Gold; a stale one gives way to Euro Stoxx 50, then WTI) with their names (19px, `#a8b0b4`) over the change (30px/520 tabular, signed, `#1fd27a` up, `#ff4b52` down), separated by hairlines. JPEG at quality 90 without chroma subsampling. The note page's `og:image` and its Article structured data's `image` point to it, with the alt "The Andra Markets close note for [date]: [headline]"; every other page, and a note whose image could not be drawn, shares `assets/og-image.png`.
- New derivatives (other sizes, a manifest icon, alternative share cards) need owner approval before they ship.

## Do's and Don'ts

### Do:
- **Do** keep the site one dark theme: black ground, `theme-color` `#000000`, no switch.
- **Do** set every colour through the custom properties, and new values in `assets/theme.css` (inner pages) or `assets/home.css` (homepage).
- **Do** use the one `--font` stack ending in `sans-serif`, in light weights: 300 for titles and ledes, 350 for text, 400 for headings in lists, labels and figures, 500 for the rare bold.
- **Do** make actions words with an arrow, filters words with an underline for the chosen one, and fields a line to write on.
- **Do** apply tabular figures only to elements that hold numbers.
- **Do** give every chart a key and a source and date line. Lab charts carry an "Illustrative" stamp until real data exists; dashboard tiles never do.
- **Do** write unknown values as bracketed placeholders in `.ph`.
- **Do** separate with 1px hairlines (`--rule`, `--rule-strong`), as lines above or below, never as frames.
- **Do** gate every hover effect behind `@media (hover: hover) and (pointer: fine)`.
- **Do** keep content visible by default: hide for an entrance only when a script has marked the page (`html.js`, `html.opening`), and show it anyway if that script never finishes.
- **Do** use the shared eases: `cubic-bezier(0.23, 1, 0.32, 1)` (`--ease-out`) on inner pages and `cubic-bezier(.2, .8, .2, 1)` on the homepage for entrances and arrows.
- **Do** under `prefers-reduced-motion: reduce` drop the opening, the leaving move, the particles' flight and every rise; draw the homepage's scene as still frames.
- **Do** test the homepage on a phone: particles pile up on a small screen, so anything in transit must stay dim enough to read text over.
- **Do** show the horse whole, from `andra-horse.png` and its approved derivatives only.
- **Do** publish only as "Andra Markets".

### Don't:
- **Don't** round any corner; everything is square (0px).
- **Don't** add shadows, cards or boxes. The search palette is the one framed panel.
- **Don't** add a light theme or a second theme.
- **Don't** use gradients except for light: the homepage's horizon and flare, the wash at the head of inner pages and the fade behind the fixed header.
- **Don't** use red or green for anything but a rise or a fall: not for errors, success, tags, links, labels or prose, and never on a figure without its sign.
- **Don't** put an eyebrow, kicker or category label above a heading.
- **Don't** use em dashes or en dashes in copy; use commas, colons or full stops.
- **Don't** put a personal name anywhere on the site. The one exception is the privacy policy, which names the owner as the data controller (GDPR art. 13; owner, 2 Nov 2026).
- **Don't** crop, redraw, recolour (in the file), replace or regenerate `andra-horse.png`. The approved derivatives are the favicon set, the transparent marks and the homepage particle map (Brand assets); any other derivative needs owner approval first.
- **Don't** add a second illustration style. The pictures of the four groups are line drawings made of the same light as the rest; anything new needs owner approval.
- **Don't** use a serif face or a fallback stack that ends in `serif`, and don't add a second family.
- **Don't** set text heavier than 500, or in uppercase except the brand and actions.
- **Don't** invent numbers, prices, counts or dates; use a bracketed placeholder.
- **Don't** introduce an accent colour in the UI; ink is the only emphasis.
