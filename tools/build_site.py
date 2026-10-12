#!/usr/bin/env python3
"""Build the Andra Markets site.

Light (default) and dark themes, switched by a header toggle and remembered
per visitor. Writes:

    index.html               the homepage
    methodology/index.html   methodology (placeholder page)

    python3 tools/build_site.py

Every chart is a schematic shape from a seeded random walk. None of it is
market data, and the page labels it "Illustrative". Follow DESIGN.md.
"""
import math
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT
ICONS = ROOT / "assets" / "icons"

# Andra Markets on LinkedIn. Replace with the company page URL.
LINKEDIN_URL = "#"


# Chart helpers ---------------------------------------------------------------

def walk(n, seed, drift=0.0, vol=1.0, start=0.0):
    rng = random.Random(seed)
    y, out = start, []
    for _ in range(n):
        y += drift + rng.gauss(0, vol)
        out.append(y)
    return out


def fit(series, w, h, pad=8, lo=None, hi=None):
    """Scale one or more series into a shared w x h box."""
    flat = [v for s in series for v in s]
    lo = min(flat) if lo is None else lo
    hi = max(flat) if hi is None else hi
    out = []
    for s in series:
        n = len(s)
        out.append([
            (pad + (w - 2 * pad) * i / (n - 1), pad + (h - 2 * pad) * (1 - (v - lo) / (hi - lo)))
            for i, v in enumerate(s)
        ])
    return out


def d(pts):
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)


def grid_lines(w, h, rows):
    return "".join(
        f'<line class="grid-line" x1="0" x2="{w}" y1="{h * i / rows:.1f}" y2="{h * i / rows:.1f}"/>'
        for i in range(1, rows)
    )


def svg(w, h, body, label, stretch=True):
    par = ' preserveAspectRatio="none"' if stretch else ""
    return f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="{label}, illustrative, not market data"{par}>{body}</svg>'


W, H = 320, 160  # dashboard tile charts


def c_yield_curve():
    tenors = [0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]
    now = [0.62, 0.66, 0.7, 0.66, 0.63, 0.62, 0.64, 0.68, 0.78, 0.8]
    ago = [0.7, 0.73, 0.74, 0.7, 0.66, 0.63, 0.63, 0.65, 0.72, 0.74]

    def pts(vals):
        return [(12 + (W - 24) * math.sqrt(t) / math.sqrt(30), H - 12 - (H - 24) * (v - 0.55) / 0.3) for t, v in zip(tenors, vals)]

    a, b = pts(now), pts(ago)
    dots = "".join(f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="2.5"/>' for x, y in a)
    return svg(W, H, grid_lines(W, H, 4) + f'<path class="dash" d="{d(b)}"/><path class="line" d="{d(a)}"/>' + dots, "Yield curve shape, today against one month ago", stretch=False)


def c_fed_path():
    steps = [5, 5, 4.75, 4.75, 4.5, 4.5, 4.25, 4.25, 4.0, 4.0]
    implied = [5, 4.95, 4.82, 4.7, 4.58, 4.46, 4.36, 4.24, 4.15, 4.08]
    pa, pb = fit([steps, implied], W, H, 14)
    stair = []
    for i, (x, y) in enumerate(pa):
        if i:
            stair.append((x, pa[i - 1][1]))
        stair.append((x, y))
    dots = "".join(f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="2.5"/>' for x, y in pb)
    return svg(W, H, grid_lines(W, H, 4) + f'<path class="dash" d="{d(stair)}"/><path class="line" d="{d(pb)}"/>' + dots, "Policy rate path implied by futures against the current rate", stretch=False)


def c_credit():
    ig = [abs(v) + 6 for v in walk(80, 31, 0, 0.4)]
    hy = [v * 2.6 + 2 for v in ig]
    rng = random.Random(32)
    hy = [v + rng.gauss(0, 0.8) for v in hy]
    pa, pb = fit([hy, ig], W, H, 8)
    area = d(pb) + f" L{pb[-1][0]:.1f} {H} L{pb[0][0]:.1f} {H} Z"
    return svg(W, H, grid_lines(W, H, 3) + f'<path class="area" d="{area}"/><path class="line" d="{d(pa)}"/><path class="dash" d="{d(pb)}"/>', "Credit spreads, high yield against investment grade")


def heat_cells(rows, cols, seed, w, h, gap=3, diag=False):
    rng = random.Random(seed)
    cw, ch = (w - gap * (cols - 1)) / cols, (h - gap * (rows - 1)) / rows
    cells = []
    for r in range(rows):
        for c in range(cols):
            v = 1.0 if diag and r == c else max(-1, min(1, rng.gauss(0.1, 0.55)))
            if diag and c < r:
                continue
            cls = "up" if v >= 0 else "down"
            op = 0.45 + 0.55 * abs(v)
            cells.append(f'<rect class="{cls}" x="{c * (cw + gap):.1f}" y="{r * (ch + gap):.1f}" width="{cw:.1f}" height="{ch:.1f}" opacity="{op:.2f}"/>')
    return "".join(cells)


def c_sector_heatmap():
    return svg(W, H, heat_cells(3, 4, 41, W, H), "Sector performance heatmap", stretch=False)


def c_correlation():
    return svg(H, H, heat_cells(5, 5, 42, H, H, diag=True), "Cross-asset correlation matrix", stretch=False)


def hbars(vals, w, h, gap=4):
    m = max(abs(v) for v in vals)
    rh = (h - gap * (len(vals) - 1)) / len(vals)
    mid = w / 2
    out = [f'<line class="ref" x1="{mid}" x2="{mid}" y1="0" y2="{h}"/>']
    for i, v in enumerate(vals):
        bw = abs(v) / m * (mid - 6)
        x = mid if v >= 0 else mid - bw
        out.append(f'<rect class="{"up" if v >= 0 else "down"}" x="{x:.1f}" y="{i * (rh + gap):.1f}" width="{bw:.1f}" height="{rh:.1f}"/>')
    return "".join(out)


def c_global_indices():
    rng = random.Random(51)
    vals = sorted((rng.gauss(0.2, 1) for _ in range(8)), reverse=True)
    return svg(W, H, hbars(vals, W, H), "Global equity index moves")


def c_fx():
    rng = random.Random(61)
    vals = sorted((rng.gauss(0, 1) for _ in range(7)), reverse=True)
    return svg(W, H, hbars(vals, W, H, 6), "Major currency moves against the US dollar")


def vbars(vals, w, h, gap=3):
    m = max(abs(v) for v in vals)
    bw = (w - gap * (len(vals) - 1)) / len(vals)
    mid = h / 2
    out = [f'<line class="ref" x1="0" x2="{w}" y1="{mid}" y2="{mid}"/>']
    for i, v in enumerate(vals):
        bh = abs(v) / m * (mid - 4)
        y = mid - bh if v >= 0 else mid
        out.append(f'<rect class="{"up" if v >= 0 else "down"}" x="{i * (bw + gap):.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}"/>')
    return "".join(out)


def c_breadth():
    rng = random.Random(3)
    return svg(W, H, vbars([rng.gauss(0.15, 1) for _ in range(30)], W, H), "Advancers minus decliners")


def c_earnings():
    rng = random.Random(71)
    n, gap = 12, 4
    bw = (W - gap * (n - 1)) / n
    out = []
    for i in range(n):
        share = rng.uniform(0.6, 0.85)
        reported = (i + 3) / (n + 2) * 0.92
        beat, miss = share * reported, (1 - share) * reported
        hb, hm = beat * (H - 8), miss * (H - 8)
        x = i * (bw + gap)
        out.append(f'<rect class="up" x="{x:.1f}" y="{H - hb:.1f}" width="{bw:.1f}" height="{hb:.1f}"/>')
        out.append(f'<rect class="down" x="{x:.1f}" y="{H - hb - hm - 2:.1f}" width="{bw:.1f}" height="{hm:.1f}"/>')
    return svg(W, H, "".join(out), "Earnings beats and misses as companies report")


def c_vol_term():
    tenors = [1, 2, 3, 4, 6, 9, 12]
    now = [0.42, 0.5, 0.56, 0.6, 0.65, 0.69, 0.72]
    ago = [0.6, 0.62, 0.63, 0.64, 0.66, 0.68, 0.7]

    def pts(vals):
        return [(14 + (W - 28) * (t - 1) / 11, H - 12 - (H - 24) * (v - 0.38) / 0.38) for t, v in zip(tenors, vals)]

    a, b = pts(now), pts(ago)
    dots = "".join(f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="2.5"/>' for x, y in a)
    return svg(W, H, grid_lines(W, H, 4) + f'<path class="dash" d="{d(b)}"/><path class="line" d="{d(a)}"/>' + dots, "Volatility term structure, today against one week ago", stretch=False)


def c_commodities():
    a, b = walk(70, 81, 0.05, 1), walk(70, 82, -0.04, 1)
    pa, pb = fit([a, b], W, H, 8)
    return svg(W, H, grid_lines(W, H, 3) + f'<path class="line" d="{d(pa)}"/><path class="dash" d="{d(pb)}"/>', "Oil and gold, rebased")


def c_inflation_labour():
    infl = [abs(v) * 0.4 + 2 for v in walk(48, 91, 0, 0.5, 3)]
    rng = random.Random(92)
    jobs = [1 + rng.gauss(0, 0.7) for _ in range(48)]
    pa, = fit([infl], W, H * 0.55, 8)
    pb_vals = jobs
    m = max(abs(v) for v in pb_vals)
    bw = W / len(pb_vals)
    base = H - 4
    bars = "".join(
        f'<rect class="{"up" if v >= 0 else "down"}" x="{i * bw + 1:.1f}" y="{base - abs(v) / m * 36:.1f}" width="{bw - 2:.1f}" height="{abs(v) / m * 36:.1f}"/>'
        for i, v in enumerate(pb_vals)
    )
    return svg(W, H, f'<path class="line" d="{d(pa)}"/>' + bars, "Inflation line above monthly payroll changes")


def c_momentum(w=640, h=260):
    rng = random.Random(4)
    y, vals, regimes, i0 = 0.0, [], [], 0
    for length, drift in [(60, 0.32), (35, -0.45), (70, 0.28), (25, -0.6), (55, 0.35), (55, -0.3)]:
        regimes.append((i0, i0 + length, drift))
        i0 += length
        for _ in range(length):
            y += drift + rng.gauss(0, 0.9)
            vals.append(y)
    pts, = fit([vals], w, h, 10)
    bands = "".join(
        f'<rect class="{"band-up" if dr > 0 else "band-down"}" x="{pts[a][0]:.1f}" y="0" width="{pts[min(b, len(pts) - 1)][0] - pts[a][0]:.1f}" height="{h}"/>'
        for a, b, dr in regimes
    )
    return svg(w, h, bands + grid_lines(w, h, 4) + f'<path class="line" d="{d(pts)}"/>', "Momentum strategy across trending and reversal regimes")


def c_payoff(w=640, h=260):
    # Long call: payoff at expiry (dashed) and value before expiry (solid).
    xs = [i / 99 for i in range(100)]
    k = 0.5
    payoff = [max(0, x - k) for x in xs]
    value = [0.09 * math.log1p(math.exp((x - k) / 0.09)) for x in xs]
    pa, pb = fit([payoff, value], w, h, 12, lo=-0.02, hi=0.55)
    zero = h - 12 - (h - 24) * (0.02 / 0.57)
    return svg(w, h, grid_lines(w, h, 4) + f'<line class="ref" x1="0" x2="{w}" y1="{zero:.1f}" y2="{zero:.1f}"/><path class="dash" d="{d(pa)}"/><path class="line" d="{d(pb)}"/>', "Call option value before expiry against its payoff at expiry")


def c_explainer(w=560, h=240):
    # Normal against inverted curve, an explainer diagram.
    tenors = [0.25, 1, 2, 5, 10, 30]

    def curve(vals):
        return [(16 + (w - 32) * math.sqrt(t) / math.sqrt(30), h - 16 - (h - 32) * v) for t, v in zip(tenors, vals)]

    normal = curve([0.2, 0.35, 0.45, 0.6, 0.7, 0.8])
    inverted = curve([0.75, 0.7, 0.6, 0.48, 0.42, 0.45])
    return svg(w, h, grid_lines(w, h, 4) + f'<path class="line" d="{d(normal)}"/><path class="dash" d="{d(inverted)}"/>', "Diagram of a normal and an inverted yield curve", stretch=False)


# Icons -----------------------------------------------------------------------

ICON_NAMES = ["warning-circle", "arrow-right", "arrow-up-right", "linkedin-logo", "tiktok-logo", "youtube-logo", "list", "x", "play", "sun", "moon"]


def sprite():
    symbols = []
    for name in ICON_NAMES:
        path = re.search(r'd="([^"]+)"', (ICONS / f"{name}.svg").read_text()).group(1)
        symbols.append(f'<symbol id="i-{name}" viewBox="0 0 256 256"><path d="{path}"/></symbol>')
    return '<svg width="0" height="0" style="position:absolute" aria-hidden="true">' + "".join(symbols) + "</svg>"


def icon(name):
    return f'<svg class="icon" aria-hidden="true"><use href="#i-{name}"/></svg>'


# Content ---------------------------------------------------------------------

TAPE = ["S&amp;P 500", "Nasdaq 100", "Russell 2000", "Euro Stoxx 50", "Nikkei 225",
        "VIX", "US 10Y yield", "EUR/USD", "WTI crude", "Gold"]

CATEGORIES = [
    ("rates", "Rates and credit", "Rates"),
    ("macro", "Macro and the Fed", "Macro"),
    ("equities", "Equities", "Equities"),
    ("cross", "Cross-asset", "Cross-asset"),
]

DASHBOARDS = [
    ("rates", "Yield curve", "The Treasury curve today against a month ago.", c_yield_curve, [("line", "Today"), ("dash", "1 month ago")]),
    ("macro", "Fed path", "Where futures price the policy rate, meeting by meeting.", c_fed_path, [("line", "Implied path"), ("dash", "Current rate")]),
    ("equities", "Sector heatmap", "Every S&amp;P 500 sector, ranked by the day's move.", c_sector_heatmap, [("up", "Up"), ("down", "Down")]),
    ("cross", "Volatility term structure", "Implied volatility across expiries, and how its shape is shifting.", c_vol_term, [("line", "Today"), ("dash", "1 week ago")]),
    ("equities", "Global indices", "Major equity benchmarks across the US, Europe and Asia.", c_global_indices, [("up", "Up"), ("down", "Down")]),
    ("cross", "FX majors", "The dollar against the major currencies.", c_fx, [("up", "Stronger"), ("down", "Weaker")]),
    ("cross", "Commodities", "Energy, metals and agriculture, rebased to the same start.", c_commodities, [("line", "Oil"), ("dash", "Gold")]),
    ("rates", "Credit spreads", "High yield and investment grade spreads over Treasuries.", c_credit, [("line", "High yield"), ("dash", "Investment grade")]),
    ("macro", "Inflation and labour", "Inflation prints alongside the monthly jobs report.", c_inflation_labour, [("line", "Inflation"), ("up", "Jobs added")]),
    ("equities", "Earnings season tracker", "Beats and misses as companies report, sector by sector.", c_earnings, [("up", "Beats"), ("down", "Misses")]),
    ("equities", "Market breadth", "Advancers, decliners and new highs across the market.", c_breadth, [("up", "Advancers"), ("down", "Decliners")]),
    ("cross", "Cross-asset correlation", "How stocks, bonds, the dollar and commodities move together.", c_correlation, [("up", "Positive"), ("down", "Negative")]),
]

CALENDAR = [
    ("[Day, date]", [
        ("Macro", "Consumer prices (CPI)", "[consensus]", "[prior]"),
        ("Earnings", "[Company] quarterly results", "EPS [consensus]", "EPS [prior]"),
    ]),
    ("[Day, date]", [
        ("Macro", "Retail sales", "[consensus]", "[prior]"),
        ("Fed", "FOMC rate decision", "[consensus]", "[prior]"),
        ("Fed", "Fed Chair press conference", "", ""),
    ]),
    ("[Day, date]", [
        ("Earnings", "[Company] quarterly results", "EPS [consensus]", "EPS [prior]"),
        ("Macro", "Nonfarm payrolls", "[consensus]", "[prior]"),
    ]),
]

LEARN = [
    ("What moves bond yields", "Inflation, growth and the Fed, in plain terms."),
    ("What the VIX actually measures", "Why it is called the fear gauge, and where that breaks down."),
    ("How earnings season works", "Estimates, beats, misses and why guidance matters more."),
    ("Momentum, explained", "Why winners keep winning, until they suddenly do not."),
    ("What the Fed does on decision day", "Rates, the statement, the dots and the press conference."),
]


def ph(text):
    return f'<span class="ph">{text}</span>'


def fill(text):
    """Wrap every [placeholder] in a span."""
    return re.sub(r"(\[[^\]]+\])", r'<span class="ph">\1</span>', text)


# Page ------------------------------------------------------------------------

THEME_BOOT = (
    "(function(){var t='light';try{var q=new URLSearchParams(location.search).get('theme');"
    "if(q==='light'||q==='dark'){t=q;localStorage.setItem('andra-theme',q)}"
    "else{var s=localStorage.getItem('andra-theme');if(s==='light'||s==='dark')t=s}}catch(e){}"
    "document.documentElement.setAttribute('data-theme',t);"
    "var m=document.querySelector('meta[name=theme-color]');if(m)m.content=t==='dark'?'#0a0c0d':'#f4f6f6'})();"
)


def page():
    tape = "".join(
        f'<li class="tape__item"><span class="tape__name">{n}</span>'
        f'<span class="tape__level ph">[live]</span><span class="tape__chg ph">[live]</span></li>'
        for n in TAPE
    )
    filters = f'<button type="button" class="chip" data-filter="all" data-label="All" aria-pressed="true">All <span class="chip__n">{len(DASHBOARDS)}</span></button>' + "".join(
        f'<button type="button" class="chip" data-filter="{key}" data-label="{label}" aria-pressed="false">{short} '
        f'<span class="chip__n">{sum(1 for x in DASHBOARDS if x[0] == key)}</span></button>'
        for key, label, short in CATEGORIES
    )
    cat_label = {k: label for k, label, _ in CATEGORIES}
    swatch = {"line": "k-solid", "dash": "k-dash", "up": "sw-up", "down": "sw-down"}

    def key_html(leg):
        items = "".join(f'<span><i class="{swatch[kind]}"></i>{label}</span>' for kind, label in leg)
        return f'<p class="key">{items}<span class="key__note">Illustrative</span></p>'

    tiles = "".join(
        f'<li class="dash-tile reveal" data-cat="{cat}" style="--i:{i % 3}">'
        f'<a href="#dashboards" class="dash-tile__link">'
        f'<div class="dash-tile__chart draw">{fn()}</div>{key_html(leg)}'
        f'<div class="dash-tile__text">'
        f'<h3>{name}</h3><p class="dash-tile__desc">{desc}</p>'
        f'<p class="dash-tile__src">{cat_label[cat]}. {ph("[source]")}, {ph("[date]")}</p></div>'
        f'<span class="dash-tile__go">{icon("arrow-up-right")}</span></a></li>'
        for i, (cat, name, desc, fn, leg) in enumerate(DASHBOARDS)
    )
    calendar = "".join(
        f'<tbody><tr class="cal__day"><th scope="rowgroup" colspan="5">{fill(day)}</th></tr>'
        + "".join(
            f'<tr><td class="cal__time ph">[time]</td>'
            f'<th scope="row">{fill(event)}</th><td class="cal__type"><span class="tag tag--{kind.lower()}">{kind}</span></td>'
            f'<td class="cal__cons" data-label="Consensus">{fill(cons)}</td><td class="cal__prior" data-label="Prior">{fill(prior)}</td></tr>'
            for kind, event, cons, prior in rows
        )
        + "</tbody>"
        for day, rows in CALENDAR
    )
    archive = "".join(
        f'<li><a href="#note"><span class="ph">[date]</span><span class="note-list__title"><span class="ph ph--ink">[Close note headline]</span></span>{icon("arrow-right")}</a></li>'
        for _ in range(3)
    )
    learn = "".join(
        f'<li class="reveal" style="--i:{i}"><a href="#learn"><span class="learn-list__title">{t}</span>'
        f'<span class="learn-list__desc">{desc}</span><span class="learn-list__time"><span class="ph">[n]</span> min read</span></a></li>'
        for i, (t, desc) in enumerate(LEARN)
    )
    tiktoks = "".join(
        f'<li class="video video--tall reveal" style="--i:{i + 1}"><a href="#watch">'
        f'<span class="video__frame"><span class="video__play">{icon("play")}</span>'
        f'<span class="video__platform">{icon("tiktok-logo")}TikTok</span></span>'
        f'<span class="video__title"><span class="ph ph--ink">[Video title]</span></span>'
        f'<span class="video__meta"><span class="ph">[duration]</span></span></a></li>'
        for i in range(2)
    )

    return shell(
        title="Andra Markets: markets research platform",
        desc="Andra Markets is a markets research platform: dashboards, quant tools, an economic calendar, a daily close note, explainers and videos.",
        body=f"""<main id="main">
  <section class="hero" id="top" aria-labelledby="hero-title">
    <span class="hero__sentinel" aria-hidden="true"></span>
    <div class="hero__art" aria-hidden="true">
      <img class="horse" src="assets/andra-horse.png" alt="" width="1024" height="1024" fetchpriority="high">
    </div>
    <div class="wrap hero__copy">
      <h1 id="hero-title" style="--i:0">Markets, on&nbsp;the&nbsp;record.</h1>
      <p class="hero__sub" style="--i:1">A markets research platform. Live dashboards, quant tools, an economic calendar and a daily close note.</p>
      <div class="hero__actions" style="--i:2">
        <a class="btn" href="#dashboards">Explore dashboards {icon("arrow-right")}</a>
        <a class="btn btn--ghost" href="#subscribe">Subscribe</a>
      </div>
    </div>
  </section>

  <section class="tape" aria-labelledby="tape-title">
    <div class="wrap">
      <div class="tape__head">
        <h2 id="tape-title">Markets {ph("[date]")}, {ph("[time]")} ET</h2>
        <a class="tape__note" href="#note"><span>Latest close note, {ph("[date]")}: <span class="ph ph--ink">[headline]</span></span>{icon("arrow-right")}</a>
      </div>
      <ul class="tape__list" tabindex="0" aria-label="Market levels">{tape}</ul>
      <p class="tape__src">Last and daily change. Source {ph("[data vendor]")}</p>
    </div>
  </section>

  <section class="section dash" id="dashboards" aria-labelledby="dash-title">
    <div class="wrap">
      <div class="section-head">
        <h2 class="section-title reveal" id="dash-title">Dashboards</h2>
        <p class="lede reveal">Interactive views across rates, equities, macro and cross-asset. Previews are illustrative.</p>
      </div>
      <div class="filters" role="group" aria-label="Filter dashboards by category">{filters}</div>
      <p class="filters__status" role="status" aria-live="polite">Showing all {len(DASHBOARDS)} dashboards</p>
      <ul class="dash-grid">{tiles}</ul>
    </div>
  </section>

  <section class="section lab" id="lab" aria-labelledby="lab-title">
    <div class="wrap">
      <div class="section-head">
        <h2 class="section-title reveal" id="lab-title">Lab</h2>
        <p class="lede reveal">Interactive quant tools. Change the inputs, watch the result move.</p>
      </div>
      <div class="lab-grid">
        <a class="tool tool--wide reveal" href="#lab">
          <div class="draw">{c_momentum()}</div>
          <p class="key"><span><i class="sw-up"></i>Trending regime</span><span><i class="sw-down"></i>Reversal regime</span><span class="key__note">Illustrative</span></p>
          <div class="tool__text">
            <h3>Momentum regime backtest</h3>
            <p>Run a momentum rule across trending and reversal regimes, and see where it pays and where it breaks.</p>
            <p class="tool__params">Lookback {ph("[n]")} months. Universe {ph("[universe]")}.</p>
          </div>
          <span class="link">Open the explorer {icon("arrow-up-right")}</span>
        </a>
        <a class="tool reveal" href="#lab" style="--i:1">
          <div class="draw">{c_payoff()}</div>
          <p class="key"><span><i class="k-solid"></i>Value today</span><span><i class="k-dash"></i>Payoff at expiry</span><span class="key__note">Illustrative</span></p>
          <div class="tool__text">
            <h3>Options pricer</h3>
            <p>Price European options and watch the Greeks respond as strike, volatility and time change.</p>
          </div>
          <span class="link">Open the pricer {icon("arrow-up-right")}</span>
        </a>
        <div class="tool tool--next reveal" style="--i:2">
          <h3>Next in the Lab</h3>
          <p>{ph("[Tool name]")} and {ph("[Tool name]")} are in development. New tools are announced in the daily note.</p>
          <a class="link" href="#subscribe">Subscribe {icon("arrow-right")}</a>
        </div>
      </div>
    </div>
  </section>

  <section class="section calendar" id="calendar" aria-labelledby="cal-title">
    <div class="wrap">
      <div class="section-head">
        <div>
          <h2 class="section-title reveal" id="cal-title">Calendar</h2>
          <p class="lede reveal">Macro releases, Fed meetings and earnings for the week of {ph("[date]")}. Times in ET.</p>
        </div>
        <a class="link reveal" href="#calendar">Full calendar {icon("arrow-right")}</a>
      </div>
      <div class="cal-wrap reveal">
        <table class="cal">
          <thead><tr><th scope="col">Time</th><th scope="col">Event</th><th scope="col">Type</th><th scope="col">Consensus</th><th scope="col">Prior</th></tr></thead>
          {calendar}
        </table>
      </div>
    </div>
  </section>

  <section class="section note" id="note" aria-labelledby="note-title">
    <div class="wrap grid">
      <div class="note__latest">
        <h2 class="section-title reveal" id="note-title">Daily close note</h2>
        <article class="reveal" style="--i:1">
          <h3 class="note__title"><span class="ph ph--ink">[Headline of the latest close note]</span></h3>
          <p class="note__summary">{ph("[Two sentences on the session: what moved, and why it mattered.]")}</p>
          <p class="note__meta">{ph("[date]")}<span>{ph("[n]")} min read</span></p>
          <a class="btn" href="#note">Read the note {icon("arrow-right")}</a>
        </article>
      </div>
      <div class="note__archive reveal" style="--i:2">
        <p class="note__label">Every US trading day, after the close.</p>
        <ol class="note-list">{archive}</ol>
        <a class="link" href="#note">All notes {icon("arrow-right")}</a>
      </div>
    </div>
  </section>

  <section class="section learn" id="learn" aria-labelledby="learn-title">
    <div class="wrap">
      <div class="section-head">
        <h2 class="section-title reveal" id="learn-title">Learn</h2>
        <p class="lede reveal">Market explainers for people starting out. No jargon left unexplained.</p>
      </div>
      <div class="grid learn__grid">
        <a class="learn-feature reveal" href="#learn">
          <div class="draw">{c_explainer()}</div>
          <p class="key"><span><i class="k-solid"></i>Normal curve</span><span><i class="k-dash"></i>Inverted curve</span></p>
          <h3>How to read the yield curve</h3>
          <p>What the curve is, why it usually slopes up, and what it means when it turns upside down.</p>
          <span class="learn-list__time">{ph("[n]")} min read</span>
        </a>
        <ol class="learn-list">{learn}</ol>
      </div>
    </div>
  </section>

  <section class="section watch" id="watch" aria-labelledby="watch-title">
    <div class="wrap">
      <div class="section-head">
        <h2 class="section-title reveal" id="watch-title">Watch</h2>
        <p class="lede reveal">Market recaps and short explainers from YouTube and TikTok. Embeds are placeholders.</p>
      </div>
      <ul class="watch-grid">
        <li class="video video--wide reveal"><a href="#watch">
          <span class="video__frame"><span class="video__play">{icon("play")}</span>
          <span class="video__platform">{icon("youtube-logo")}YouTube</span></span>
          <span class="video__title"><span class="ph ph--ink">[Video title]</span></span>
          <span class="video__meta"><span class="ph">[duration]</span></span></a></li>
        {tiktoks}
      </ul>
    </div>
  </section>

  <section class="section about" id="about" aria-labelledby="about-title">
    <div class="wrap grid">
      <h2 class="visually-hidden" id="about-title">About Andra Markets</h2>
      <p class="about__statement reveal">Andra Markets reads the data every trading day and keeps the dashboards, tools, calendar and notes current. Built for professionals, written so anyone can learn from it.</p>
      <dl class="reveal" style="--i:1">
        <div><dt>Covers</dt><dd>US and global markets: rates, equities, macro, FX and commodities</dd></div>
        <div><dt>Publishes</dt><dd>A close note every US trading day</dd></div>
        <div><dt>Data</dt><dd class="ph">[data sources]</dd></div>
      </dl>
    </div>
  </section>

  <section class="section signup" id="subscribe" aria-labelledby="subscribe-title">
    <div class="signup__art" aria-hidden="true"><img class="horse" src="assets/andra-horse.png" alt="" width="1024" height="1024" loading="lazy"></div>
    <div class="wrap grid">
      <h2 class="section-title reveal" id="subscribe-title">The market, in your inbox.</h2>
      <form class="reveal" style="--i:1" novalidate>
        <div class="field">
          <label for="email">Email address</label>
          <div class="field__row">
            <input id="email" name="email" type="email" autocomplete="email" inputmode="email" placeholder="you@company.com" aria-describedby="email-help email-status">
            <button class="btn" type="submit">Subscribe</button>
          </div>
          <p class="field__help" id="email-help">The daily close note and new tools. Unsubscribe in one click.</p>
          <p class="field__status" id="email-status" role="status" aria-live="polite"><span class="field__icon">{icon("warning-circle")}</span><span class="field__msg"></span></p>
        </div>
      </form>
    </div>
  </section>
</main>""",
        home="",
        base="",
    )


def site_header(home, base):
    return f"""<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{home or '#top'}" aria-label="Andra Markets, home">
      <span class="brand__mark"><img src="{base}assets/andra-horse.png" alt="" width="64" height="64"></span>
      <span class="brand__name">Andra Markets</span>
    </a>
    <nav class="nav" id="site-nav" aria-label="Primary">
      <a href="{home}#dashboards">Dashboards</a>
      <a href="{home}#lab">Lab</a>
      <a href="{home}#calendar">Calendar</a>
      <a href="{home}#note">Daily note</a>
      <a href="{home}#learn">Learn</a>
      <a href="{home}#watch">Watch</a>
      <a class="nav__subscribe" href="{home}#subscribe">Subscribe</a>
    </nav>
    <button class="theme-btn" type="button" aria-label="Switch to dark theme">
      <svg class="icon icon--sun" aria-hidden="true"><use href="#i-sun"/></svg>
      <svg class="icon icon--moon" aria-hidden="true"><use href="#i-moon"/></svg>
    </button>
    <a class="btn btn--sm" href="{home}#subscribe">Subscribe</a>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="site-nav">
      <svg class="icon" aria-hidden="true"><use href="#i-list"/></svg><span>Menu</span>
    </button>
  </div>
</header>"""


def site_footer(home, base):
    return f"""<footer class="site-footer">
  <div class="wrap grid">
    <div class="foot__brand">
      <a class="brand" href="{home or '#top'}" aria-label="Andra Markets, home">
        <span class="brand__mark"><img src="{base}assets/andra-horse.png" alt="" width="64" height="64" loading="lazy"></span>
        <span class="brand__name">Andra Markets</span>
      </a>
      <p>Research on US and global markets.</p>
    </div>
    <nav class="foot__nav" aria-label="Footer">
      <a href="{home}#dashboards">Dashboards</a>
      <a href="{home}#lab">Lab</a>
      <a href="{home}#calendar">Calendar</a>
      <a href="{home}#note">Daily note</a>
      <a href="{home}#learn">Learn</a>
      <a href="{home}#watch">Watch</a>
      <a href="{home}#about">About</a>
      <a href="{base}methodology/">Methodology</a>
    </nav>
    <ul class="foot__social" aria-label="Andra Markets on social media">
      <li><a href="{LINKEDIN_URL}" rel="me">{icon("linkedin-logo")}LinkedIn</a></li>
      <li><a href="#" rel="me">{icon("tiktok-logo")}TikTok {ph("[handle]")}</a></li>
      <li><a href="#" rel="me">{icon("youtube-logo")}YouTube {ph("[handle]")}</a></li>
    </ul>
    <div class="foot__legal">
      <span>&copy; {ph("[year]")} Andra Markets</span>
      <span>For information only. Not investment advice.</span>
    </div>
  </div>
</footer>"""


def shell(title, desc, body, home, base):
    return f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#f4f6f6">
<script>{THEME_BOOT}</script>
<link rel="icon" href="{base}assets/andra-horse.png">
<link rel="preload" href="{base}assets/fonts/schibsted-grotesk-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{base}assets/site.css">
</head>
<body>
{sprite()}
<a class="skip" href="#main">Skip to content</a>

{site_header(home, base)}

{body}

{site_footer(home, base)}

<script src="{base}assets/site.js" defer></script>
</body>
</html>
"""


def methodology():
    body = f"""<main id="main" class="page">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Methodology</h1>
      <p class="lede">How Andra Markets sources, processes and presents market data. This page is a placeholder until the methodology is published.</p>
    </header>
    <div class="page__body">
      <section aria-labelledby="m-data">
        <h2 id="m-data">Data sources</h2>
        <p>{ph("[Data vendors, coverage and update times]")}</p>
      </section>
      <section aria-labelledby="m-pipeline">
        <h2 id="m-pipeline">Pipeline</h2>
        <p>{ph("[How the daily pipeline collects, checks and publishes data and notes]")}</p>
      </section>
      <section aria-labelledby="m-charts">
        <h2 id="m-charts">Charts</h2>
        <p>Every chart states its source and date. Green marks a rise and red a fall; colour appears only inside charts. Previews marked Illustrative are not market data.</p>
      </section>
      <section aria-labelledby="m-corrections">
        <h2 id="m-corrections">Corrections</h2>
        <p>{ph("[How errors are reported, corrected and logged]")}</p>
      </section>
    </div>
  </div>
</main>"""
    return shell(
        title="Methodology: Andra Markets",
        desc="How Andra Markets sources, processes and presents market data.",
        body=body,
        home="../",
        base="../",
    )


def main():
    (OUT / "index.html").write_text(page())
    (OUT / "methodology").mkdir(exist_ok=True)
    (OUT / "methodology" / "index.html").write_text(methodology())
    print("wrote index.html and methodology/index.html")


if __name__ == "__main__":
    main()
