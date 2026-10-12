#!/usr/bin/env python3
"""Build the two homepage prototypes from one template.

Both directions share this exact markup; only `data-theme` differs, so the
structure, copy and typeface stay identical and only the mood changes.

    python3 tools/build_prototypes.py

Charts are schematic shapes from a seeded random walk. They carry no market
data and are labelled "Illustrative" on the page.
"""
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "prototypes"
ICONS = OUT / "assets" / "icons"


# Charts ---------------------------------------------------------------------

def walk(n, seed, drift=0.0, vol=1.0, start=0.0):
    rng = random.Random(seed)
    y, out = start, []
    for _ in range(n):
        y += drift + rng.gauss(0, vol)
        out.append(y)
    return out


def scale(vals, w, h, pad):
    lo, hi = min(vals), max(vals)
    n = len(vals)
    return [
        (pad + (w - 2 * pad) * i / (n - 1), pad + (h - 2 * pad) * (1 - (v - lo) / (hi - lo)))
        for i, v in enumerate(vals)
    ]


def d(pts):
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)


def grid_lines(w, h, rows):
    return "".join(
        f'<line class="grid-line" x1="0" x2="{w}" y1="{h * i / rows:.1f}" y2="{h * i / rows:.1f}"/>'
        for i in range(1, rows)
    )


def svg(w, h, body, label):
    return (
        f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="{label}" '
        f'preserveAspectRatio="none">{body}</svg>'
    )


def chart_intraday():
    w, h = 640, 320
    pts = scale(walk(130, 7, 0.02, 1.0), w, h, 12)
    area = d(pts) + f" L{pts[-1][0]:.1f} {h} L{pts[0][0]:.1f} {h} Z"
    ref = pts[0][1]
    body = (
        grid_lines(w, h, 4)
        + f'<path class="area" d="{area}"/>'
        + f'<line class="ref" x1="0" x2="{w}" y1="{ref:.1f}" y2="{ref:.1f}"/>'
        + f'<path class="line" d="{d(pts)}"/>'
        + f'<circle class="dot" cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="3.5"/>'
    )
    return svg(w, h, body, "Illustrative intraday chart shape, not market data")


def chart_breadth():
    w, h = 640, 240
    rng = random.Random(3)
    vals = [rng.gauss(0.15, 1) for _ in range(40)]
    m = max(abs(v) for v in vals)
    bw = w / len(vals)
    mid = h / 2
    bars = []
    for i, v in enumerate(vals):
        bh = abs(v) / m * (mid - 6)
        y = mid - bh if v >= 0 else mid
        cls = "up" if v >= 0 else "down"
        bars.append(f'<rect class="{cls}" x="{i * bw + 2:.1f}" y="{y:.1f}" width="{bw - 4:.1f}" height="{bh:.1f}"/>')
    body = f'<line class="ref" x1="0" x2="{w}" y1="{mid}" y2="{mid}"/>' + "".join(bars)
    return svg(w, h, body, "Illustrative advance and decline bars, not market data")


def chart_sectors():
    w, h = 440, 240
    rng = random.Random(5)
    vals = sorted((rng.gauss(0, 1) for _ in range(11)), reverse=True)
    m = max(abs(v) for v in vals)
    rh = h / len(vals)
    mid = w / 2
    rows = []
    for i, v in enumerate(vals):
        bw = abs(v) / m * (mid - 8)
        x = mid if v >= 0 else mid - bw
        cls = "up" if v >= 0 else "down"
        rows.append(f'<rect class="{cls}" x="{x:.1f}" y="{i * rh + 3:.1f}" width="{bw:.1f}" height="{rh - 6:.1f}"/>')
    body = f'<line class="ref" x1="{mid}" x2="{mid}" y1="0" y2="{h}"/>' + "".join(rows)
    return svg(w, h, body, "Illustrative sector bars, not market data")


def chart_curve():
    w, h = 440, 240
    tenors = [0, 1, 2, 3, 5, 7, 10, 20, 30]
    a = [0.62, 0.74, 0.8, 0.79, 0.73, 0.71, 0.74, 0.85, 0.9]
    b = [0.78, 0.8, 0.77, 0.72, 0.66, 0.65, 0.69, 0.79, 0.84]

    def pts(vals):
        return [(16 + (w - 32) * (t ** 0.5) / (30 ** 0.5), h - 16 - (h - 32) * (v - 0.55) / 0.4) for t, v in zip(tenors, vals)]

    pa, pb = pts(a), pts(b)
    dots = "".join(f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="3"/>' for x, y in pa)
    body = grid_lines(w, h, 4) + f'<path class="curve-b" d="{d(pb)}"/><path class="curve-a" d="{d(pa)}"/>' + dots
    return svg(w, h, body, "Illustrative yield curve shape, not market data")


def chart_vol():
    w, h = 640, 240
    realised = [abs(x) for x in walk(90, 11, 0, 0.9, 8)]
    rng = random.Random(12)
    implied = [v + 2.2 + rng.gauss(0, 0.35) for v in realised]
    lo, hi = min(realised + implied), max(realised + implied)
    def pts(vals):
        return [(10 + (w - 20) * i / 89, 10 + (h - 20) * (1 - (v - lo) / (hi - lo))) for i, v in enumerate(vals)]
    pr, pi = pts(realised), pts(implied)
    gap = d(pi) + " L" + " L".join(f"{x:.1f} {y:.1f}" for x, y in reversed(pr)) + " Z"
    body = (grid_lines(w, h, 3) + f'<path class="area" d="{gap}"/>'
            + f'<path class="curve-b" d="{d(pr)}"/><path class="line" d="{d(pi)}"/>')
    return svg(w, h, body, "Illustrative implied and realised volatility shapes, not market data")


def chart_momentum():
    w, h = 1200, 420
    # Seed chosen so every band's net move agrees with its label.
    rng = random.Random(4)
    y, vals, regimes, i0 = 0.0, [], [], 0
    for length, drift in [(60, 0.32), (35, -0.45), (70, 0.28), (25, -0.6), (55, 0.35), (55, -0.3)]:
        regimes.append((i0, i0 + length, drift))
        i0 += length
        for _ in range(length):
            y += drift + rng.gauss(0, 0.9)
            vals.append(y)
    pts = scale(vals, w, h, 16)
    bands = []
    for a, b, drift in regimes:
        x0, x1 = pts[a][0], pts[min(b, len(pts) - 1)][0]
        cls = "band-up" if drift > 0 else "band-down"
        bands.append(f'<rect class="{cls}" x="{x0:.1f}" y="0" width="{x1 - x0:.1f}" height="{h}"/>')
    body = "".join(bands) + grid_lines(w, h, 4) + f'<path class="line" d="{d(pts)}"/>'
    return svg(w, h, body, "Illustrative momentum regime chart, not market data")


# Icons ----------------------------------------------------------------------

def sprite():
    symbols = []
    for name in ["arrow-right", "arrow-up-right", "linkedin-logo", "tiktok-logo", "youtube-logo", "list", "x"]:
        path = re.search(r'd="([^"]+)"', (ICONS / f"{name}.svg").read_text()).group(1)
        symbols.append(f'<symbol id="i-{name}" viewBox="0 0 256 256"><path d="{path}"/></symbol>')
    return '<svg width="0" height="0" style="position:absolute" aria-hidden="true">' + "".join(symbols) + "</svg>"


def icon(name):
    return f'<svg class="icon" aria-hidden="true"><use href="#i-{name}"/></svg>'


# Page -----------------------------------------------------------------------

TAPE = [
    "S&amp;P 500", "Nasdaq 100", "Dow Jones", "Russell 2000", "VIX",
    "US 10Y yield", "US dollar (DXY)", "WTI crude", "Gold",
]

ARCHIVE = [
    ("Close note", "[Close note headline]"),
    ("Close note", "[Close note headline]"),
    ("Study", "[Study title]"),
    ("Close note", "[Close note headline]"),
]

DASHBOARDS = [
    ("Market breadth", "Advancers, decliners and new highs across the US market.", chart_breadth, "", None),
    ("Sector rotation", "Which sectors led and lagged, and how that is shifting.", chart_sectors, "", None),
    ("Rates and the curve", "The Treasury curve today against where it stood a month ago.", chart_curve, "", ("Today", "1 month ago")),
    ("Volatility", "Implied and realised volatility, and the gap between them.", chart_vol, " tile--inverse", ("Implied", "Realised")),
]

TITLES = {
    "cream": "Andra Markets: Cream direction (prototype)",
    "dark": "Andra Markets: Dark direction (prototype)",
}


def page(theme):
    tape = "".join(
        f'<li class="tape__item"><span class="tape__name">{n}</span>'
        f'<span class="tape__level ph">[live]</span><span class="tape__chg ph">[live]</span></li>'
        for n in TAPE
    )
    archive = "".join(
        f'<li class="archive__row"><a href="#archive">'
        f'<span class="archive__date ph">[date]</span>'
        f'<span class="archive__title"><span class="ph">{title}</span></span>'
        f'<span class="archive__type">{kind}</span>{icon("arrow-right")}</a></li>'
        for kind, title in ARCHIVE
    )
    tiles = "".join(
        f'<a class="tile reveal{extra}" href="#dashboards" style="--i:{i}">'
        f'<div class="tile__chart draw">{fn()}</div>'
        + (f'<p class="key"><span><i class="k-solid"></i>{leg[0]}</span><span><i class="k-dash"></i>{leg[1]}</span></p>' if leg else "")
        + f'<div><h3>{name}</h3><p>{desc}</p>'
        f'<span class="link">Open dashboard {icon("arrow-up-right")}</span></div></a>'
        for i, (name, desc, fn, extra, leg) in enumerate(DASHBOARDS)
    )
    return f"""<!doctype html>
<html lang="en" data-theme="{theme}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLES[theme]}</title>
<meta name="description" content="Andra Markets is an automated research desk: a daily US market close note, interactive dashboards and quantitative studies.">
<meta name="theme-color" content="{'#edefee' if theme == 'cream' else '#0a0c0d'}">
<meta name="robots" content="noindex">
<link rel="icon" href="../assets/andra-horse.png">
<link rel="preload" href="../assets/fonts/schibsted-grotesk-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="../assets/site.css">
</head>
<body>
{sprite()}
<a class="skip" href="#main">Skip to content</a>

<header class="site-header">
  <div class="wrap">
    <a class="brand" href="#top" aria-label="Andra Markets, home">
      <span class="brand__mark"><img src="../assets/andra-horse.png" alt="" width="64" height="64"></span>
      <span class="brand__name">Andra Markets</span>
    </a>
    <nav class="nav" id="site-nav" aria-label="Primary">
      <a href="#latest">Close note</a>
      <a href="#archive">Archive</a>
      <a href="#dashboards">Dashboards</a>
      <a href="#research">Research</a>
      <a href="#about">About</a>
    </nav>
    <a class="btn" href="#subscribe">Subscribe</a>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="site-nav">
      <svg class="icon" aria-hidden="true"><use href="#i-list"/></svg><span>Menu</span>
    </button>
  </div>
</header>

<main id="main">
  <section class="hero" id="top" aria-labelledby="hero-title">
    <span class="hero__sentinel" aria-hidden="true"></span>
    <div class="hero__art" aria-hidden="true">
      <img class="horse" src="../assets/andra-horse.png" alt="" width="1024" height="1024" fetchpriority="high">
    </div>
    <div class="wrap hero__copy">
      <h1 id="hero-title" style="--i:0">Every close, on&nbsp;the record.</h1>
      <p class="hero__sub" style="--i:1">An automated research desk. A daily note on the US market close, live dashboards and quantitative studies.</p>
      <div class="hero__actions" style="--i:2">
        <a class="btn" href="#latest">Read the latest note {icon("arrow-right")}</a>
        <a class="btn btn--ghost" href="#subscribe">Subscribe</a>
      </div>
    </div>
  </section>

  <section class="tape" aria-labelledby="tape-title">
    <div class="wrap">
      <div class="tape__head">
        <h2 id="tape-title">US close <span class="ph">[date]</span>, 4:00 PM ET</h2>
        <span>Levels and daily change. Note published <span class="ph">[time]</span> ET. Source <span class="ph">[data vendor]</span></span>
      </div>
      <ul class="tape__list" tabindex="0" aria-label="Market close levels">{tape}</ul>
    </div>
  </section>

  <section class="section latest" id="latest" aria-labelledby="latest-title">
    <div class="wrap grid">
      <div class="latest__text">
        <h2 class="section-title reveal" id="latest-title">The latest close note</h2>
        <article class="reveal" style="--i:1">
          <p class="latest__meta"><span class="ph">[date]</span><span><span class="ph">[n]</span> min read</span></p>
          <h3 class="latest__title"><span class="ph ph--ink">[Headline of the latest close note]</span></h3>
          <p class="latest__summary"><span class="ph">[Two sentences on the session: what moved, and why it mattered.]</span></p>
          <a class="btn" href="#latest">Read the note {icon("arrow-right")}</a>
        </article>
      </div>
      <figure class="latest__figure draw reveal" style="--i:2">
        {chart_intraday()}
        <figcaption><span>S&amp;P 500, session of <span class="ph">[date]</span></span><span>Illustrative</span></figcaption>
      </figure>
    </div>
  </section>

  <section class="section archive" id="archive" aria-labelledby="archive-title">
    <div class="wrap">
      <div class="section-head">
        <h2 class="section-title reveal" id="archive-title">Archive</h2>
        <a class="link reveal" href="#archive">All notes and studies {icon("arrow-right")}</a>
      </div>
      <ol class="archive__list reveal">{archive}</ol>
    </div>
  </section>

  <section class="section dash" id="dashboards" aria-labelledby="dash-title">
    <div class="wrap">
      <div class="section-head">
        <h2 class="section-title reveal" id="dash-title">Dashboards</h2>
        <p class="lede reveal">Interactive views of the US market. Charts below are illustrative.</p>
      </div>
      <div class="dash__grid">{tiles}</div>
    </div>
  </section>

  <section class="section feature" id="research" aria-labelledby="research-title">
    <div class="wrap">
      <div class="grid">
        <h2 class="feature__title reveal" id="research-title">Momentum regimes</h2>
        <p class="feature__abstract reveal" style="--i:1">When does trend-following pay, and when does it break? A regime-by-regime study of momentum in US equities.</p>
      </div>
      <figure class="feature__figure draw reveal">
        {chart_momentum()}
        <figcaption>
          <span class="legend"><span><i class="sw-up"></i>Trending regime</span><span><i class="sw-down"></i>Reversal regime</span></span>
          <span>Illustrative</span>
        </figcaption>
      </figure>
      <div class="feature__foot">
        <dl class="facts reveal">
          <div><dt>Sample</dt><dd class="ph">[period]</dd></div>
          <div><dt>Universe</dt><dd class="ph">[universe]</dd></div>
          <div><dt>Method</dt><dd class="ph">[method]</dd></div>
        </dl>
        <a class="btn reveal" href="#research">Read the study {icon("arrow-right")}</a>
      </div>
    </div>
  </section>

  <section class="section about" id="about" aria-labelledby="about-title">
    <div class="wrap grid">
      <h2 class="visually-hidden" id="about-title">About Andra Markets</h2>
      <p class="about__statement reveal">Andra Markets is an automated research desk. Every US trading day it reads the close, writes the note and updates the dashboards.</p>
      <dl class="reveal" style="--i:1">
        <div><dt>Publishes</dt><dd>A close note every US trading day</dd></div>
        <div><dt>Builds</dt><dd>Interactive dashboards and quantitative studies</dd></div>
        <div><dt>Data</dt><dd class="ph">[data sources]</dd></div>
      </dl>
    </div>
  </section>

  <section class="section signup" id="subscribe" aria-labelledby="subscribe-title">
    <div class="signup__art" aria-hidden="true"><img class="horse" src="../assets/andra-horse.png" alt="" width="1024" height="1024" loading="lazy"></div>
    <div class="wrap grid">
      <h2 class="section-title reveal" id="subscribe-title">The close, in your inbox.</h2>
      <form class="reveal" style="--i:1" novalidate>
        <div class="field">
          <label for="email">Email address</label>
          <div class="field__row">
            <input id="email" name="email" type="email" autocomplete="email" inputmode="email" placeholder="you@company.com" aria-describedby="email-help email-status">
            <button class="btn" type="submit">Subscribe</button>
          </div>
          <p class="field__help" id="email-help">One note per US trading day. Unsubscribe in one click.</p>
          <p class="field__status" id="email-status" role="status" aria-live="polite"></p>
        </div>
      </form>
    </div>
  </section>
</main>

<footer class="site-footer">
  <div class="wrap grid">
    <div class="foot__brand">
      <a class="brand" href="#top" aria-label="Andra Markets, home">
        <span class="brand__mark"><img src="../assets/andra-horse.png" alt="" width="64" height="64" loading="lazy"></span>
        <span class="brand__name">Andra Markets</span>
      </a>
      <p>An automated research desk on the US market close.</p>
    </div>
    <nav class="foot__nav" aria-label="Footer">
      <a href="#latest">Close note</a>
      <a href="#archive">Archive</a>
      <a href="#dashboards">Dashboards</a>
      <a href="#research">Research</a>
      <a href="#about">About</a>
    </nav>
    <ul class="foot__social" aria-label="Andra Markets on social media">
      <li><a href="#" rel="me">{icon("linkedin-logo")}LinkedIn <span class="ph">[handle]</span></a></li>
      <li><a href="#" rel="me">{icon("tiktok-logo")}TikTok <span class="ph">[handle]</span></a></li>
      <li><a href="#" rel="me">{icon("youtube-logo")}YouTube <span class="ph">[handle]</span></a></li>
    </ul>
    <div class="foot__legal">
      <span>&copy; <span class="ph">[year]</span> Andra Markets</span>
      <span>For information only. Not investment advice.</span>
    </div>
  </div>
</footer>

<script src="../assets/site.js" defer></script>
</body>
</html>
"""


def main():
    for theme in ("cream", "dark"):
        target = OUT / theme / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page(theme))
        print("wrote", target.relative_to(ROOT))


if __name__ == "__main__":
    main()
