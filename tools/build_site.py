#!/usr/bin/env python3
"""Build the Andra Markets site.

Light (default) and dark themes, switched by a header toggle and remembered
per visitor. Writes:

    index.html                 the homepage
    methodology/index.html     methodology (placeholder page)
    reports/index.html         every published close note
    reports/<date>/index.html  one page per note, rendered from its text
    dashboards/<slug>/         one page per dashboard (assets/dashboard.js draws the chart)

    python3 tools/build_site.py

Close notes come from data/notes/*.json, written by tools/import_notes.py.
With none published, the home page keeps its placeholders. The tape shows the
latest note's closing levels. No PDF or facts file is ever linked: the site is
free, and those downloads are reserved for paid subscribers later.

Dashboard tiles draw real figures from .cache/dashboards/tiles.json, written
at deploy time by tools/dashboard_data.py, with their source and date; a tile
without a record shows its source and "Data pending". Lab and Learn charts are schematic
shapes, not market data, and labelled "Illustrative". Follow DESIGN.md.
"""
import datetime as dt
import html
import json
import math
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nyse  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT
ICONS = ROOT / "assets" / "icons"

# Andra Markets social channels. Footer links and the Watch section are built
# from these, so a channel appears everywhere once its URL is set.
LINKEDIN_URL = "https://www.linkedin.com/company/andramarkets/"
TIKTOK_URL = "https://www.tiktok.com/@andramarkets"
YOUTUBE_URL = ""  # No channel yet. Set the URL to bring back the footer link and icon.

SOCIALS = [
    ("LinkedIn", LINKEDIN_URL, "linkedin-logo"),
    ("TikTok", TIKTOK_URL, "tiktok-logo"),
    ("YouTube", YOUTUBE_URL, "youtube-logo"),
]

# Watch embeds (placeholders until real videos exist): (platform, shape).
# "wide" is a 16:9 YouTube frame, "tall" a 9:16 TikTok frame. To add YouTube
# back, set YOUTUBE_URL and put ("YouTube", "wide") first; the grid adapts.
VIDEOS = [
    ("TikTok", "tall"),
    ("TikTok", "tall"),
    ("TikTok", "tall"),
    ("TikTok", "tall"),
]

# Absolute site address, no trailing slash, e.g. "https://andramarkets.com".
# Social cards need it for og:image and canonical links. Left empty until the
# site has its own domain, so no account name is baked into the pages.
SITE_URL = ""


# Chart helpers ---------------------------------------------------------------

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


# Dashboard tiles with real data ---------------------------------------------
# Figures from tools/dashboard_data.py (.cache/dashboards/tiles.json). A tile
# without a record shows "Data pending": no dashboard tile is illustrative.

DASH_DATA = ROOT / ".cache" / "dashboards" / "tiles.json"


def load_dash_data():
    try:
        return json.loads(DASH_DATA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def data_svg(w, h, body, label, stretch=True):
    par = ' preserveAspectRatio="none"' if stretch else ""
    return f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}"{par}>{body}</svg>'


d_path = d  # the path helper, renamed here: "d" is each tile's data below

TENOR_NAME = {"ust1m": "1-month", "ust3m": "3-month", "ust6m": "6-month", "ust1y": "1-year",
              "ust2y": "2-year", "ust3y": "3-year", "ust5y": "5-year", "ust7y": "7-year",
              "ust10y": "10-year", "ust20y": "20-year", "ust30y": "30-year"}


def tip(text):
    return f"<title>{esc(text)}</title>"


def chg(v):
    return signed(v, 2, "%")


def pct(v, dec=2):
    return f"{v:.{dec}f}%".replace("-", MINUS)


def short_day(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {d:%b}"


def month_name(iso):
    return f"{dt.date.fromisoformat(iso):%b %Y}"


def span(vals, pad_frac=0.12, floor=0.05):
    lo, hi = min(vals), max(vals)
    pad = max((hi - lo) * pad_frac, floor)
    return lo - pad, hi + pad


def r_yield_curve(rec):
    d = rec["data"]
    years = [TENOR_YEARS[k] for k in d["tenors"]]
    lo, hi = span(d["now"] + d["before"])
    X = lambda t: 12 + (W - 24) * math.sqrt(t) / math.sqrt(30)  # noqa: E731
    Y = lambda v: H - 12 - (H - 24) * (v - lo) / (hi - lo)  # noqa: E731
    a = [(X(t), Y(v)) for t, v in zip(years, d["now"])]
    b = [(X(t), Y(v)) for t, v in zip(years, d["before"])]
    now, then = short_day(rec["asof"]), short_day(d["then"])
    names = [TENOR_NAME[k] for k in d["tenors"]]
    dots = "".join(f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="2.5">{tip(f"{n}: {pct(v)} ({then}: {pct(o)})")}</circle>'
                   for (x, y), n, v, o in zip(a, names, d["now"], d["before"]))
    label = (f"US Treasury yield curve on {now} against {then}: "
             + ", ".join(f"{n} {pct(v)}" for n, v in zip(names, d["now"])))
    return (data_svg(W, H, grid_lines(W, H, 4) + f'<path class="dash" d="{d_path(b)}"/><path class="line" d="{d_path(a)}"/>' + dots, label, stretch=False),
            [("line", now), ("dash", then)])


def r_fed_path(rec):
    d = rec["data"]
    months, implied, effr = [m for m, _ in d["months"]], [v for _, v in d["months"]], d.get("effr")
    lo, hi = span(implied + ([effr] if effr is not None else []))
    pa, pb = fit([implied, [effr if effr is not None else implied[0]] * len(implied)], W, H, 14, lo, hi)
    names = [month_name(m + "-01") for m in months]
    dots = "".join(f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="2.5">{tip(f"{n}: {pct(v)}")}</circle>'
                   for (x, y), n, v in zip(pa, names, implied))
    label = "Fed funds rate implied by futures, month by month: " + ", ".join(f"{n} {pct(v)}" for n, v in zip(names, implied))
    ref, leg = "", [("line", "Implied path")]
    if effr is not None:
        label += f"; effective rate {pct(effr)} on {short_day(d['effr_date'])}"
        ref, leg = f'<path class="dash" d="{d_path(pb)}"/>', leg + [("dash", "Effective rate")]
    return (data_svg(W, H, grid_lines(W, H, 4) + ref + f'<path class="line" d="{d_path(pa)}"/>' + dots, label, stretch=False), leg)


def r_sector_heatmap(rec):
    rows = rec["data"]["rows"]
    rows_n, cols, gap = 3, 4, 3
    cw, ch = (W - gap * (cols - 1)) / cols, (H - gap * (rows_n - 1)) / rows_n
    m = max(abs(v) for _, v in rows) or 1
    cells = "".join(
        f'<rect class="{"up" if v >= 0 else "down"}" x="{(i % cols) * (cw + gap):.1f}" y="{(i // cols) * (ch + gap):.1f}" '
        f'width="{cw:.1f}" height="{ch:.1f}" opacity="{0.45 + 0.55 * abs(v) / m:.2f}">{tip(f"{n}: {chg(v)}")}</rect>'
        for i, (n, v) in enumerate(rows))
    label = "S&P 500 sector ETFs ranked by the day's move: " + ", ".join(f"{n} {chg(v)}" for n, v in rows)
    return data_svg(W, H, cells, label, stretch=False), [("up", "Up"), ("down", "Down")]


def r_hbars(rows, label, gap):
    m = max(abs(r[1]) for r in rows) or 1
    rh = (H - gap * (len(rows) - 1)) / len(rows)
    mid = W / 2
    out = [f'<line class="ref" x1="{mid}" x2="{mid}" y1="0" y2="{H}"/>']
    for i, r in enumerate(rows):
        n, v = r[0], r[1]
        bw = max(1.0, abs(v) / m * (mid - 6))
        x = mid if v >= 0 else mid - bw
        out.append(f'<rect class="{"up" if v >= 0 else "down"}" x="{x:.1f}" y="{i * (rh + gap):.1f}" width="{bw:.1f}" height="{rh:.1f}">'
                   f'{tip(f"{n}: {chg(v)}" + (f", {short_day(r[2])}" if len(r) > 2 else ""))}</rect>')
    return data_svg(W, H, "".join(out), label)


def r_global_indices(rec):
    rows = rec["data"]["rows"]
    label = "Equity index moves at each latest local close: " + ", ".join(
        f"{n} {chg(v)}" + ("" if day == rec["asof"] else f" ({short_day(day)})") for n, v, day in rows)
    return r_hbars(rows, label, 4), [("up", "Up"), ("down", "Down")]


def r_fx_majors(rec):
    rows = rec["data"]["rows"]
    label = "The US dollar's move against each major currency: " + ", ".join(f"{n} {chg(v)}" for n, v in rows)
    return r_hbars([[f"Dollar against the {n.lower()}" if n != "Euro" else "Dollar against the euro", v] for n, v in rows], label, 6), \
        [("up", "Dollar stronger"), ("down", "Dollar weaker")]


def r_vol_term(rec):
    d = rec["data"]
    lo, hi = span(d["now"] + d["before"], 0.15, 0.5)
    X = lambda t: 14 + (W - 28) * (math.sqrt(t) - math.sqrt(d["days"][0])) / (math.sqrt(d["days"][-1]) - math.sqrt(d["days"][0]))  # noqa: E731
    Y = lambda v: H - 12 - (H - 24) * (v - lo) / (hi - lo)  # noqa: E731
    a = [(X(t), Y(v)) for t, v in zip(d["days"], d["now"])]
    b = [(X(t), Y(v)) for t, v in zip(d["days"], d["before"])]
    now, then = short_day(rec["asof"]), short_day(d["then"])
    dots = "".join(f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="2.5">{tip(f"{lb}: {v:.2f} ({then}: {o:.2f})")}</circle>'
                   for (x, y), lb, v, o in zip(a, d["labels"], d["now"], d["before"]))
    label = (f"Cboe S&P 500 implied volatility by expiry on {now} against {then}: "
             + ", ".join(f"{lb} {v:.2f}" for lb, v in zip(d["labels"], d["now"])))
    return (data_svg(W, H, grid_lines(W, H, 4) + f'<path class="dash" d="{d_path(b)}"/><path class="line" d="{d_path(a)}"/>' + dots, label, stretch=False),
            [("line", now), ("dash", then)])


def r_commodities(rec):
    d = rec["data"]
    pa, pb = fit([d["oil"], d["gold"]], W, H, 8)
    label = (f"WTI crude and gold front-month futures, rebased to 100 on {short_day(d['start'])}: "
             f"WTI {d['oil'][-1]:.1f}, gold {d['gold'][-1]:.1f} on {short_day(rec['asof'])}")
    return (data_svg(W, H, grid_lines(W, H, 3) + f'<path class="line" d="{d_path(pa)}"/><path class="dash" d="{d_path(pb)}"/>', label),
            [("line", "WTI crude"), ("dash", "Gold")])


def r_credit_spreads(rec):
    d = rec["data"]
    pa, pb = fit([d["hy"], d["ig"]], W, H, 8, 0, max(d["hy"]) * 1.08)
    area = d_path(pb) + f" L{pb[-1][0]:.1f} {H} L{pb[0][0]:.1f} {H} Z"
    label = (f"Option-adjusted spreads over Treasuries since {short_day(d['start'])}: high yield {pct(d['hy'][-1])}, "
             f"investment grade {pct(d['ig'][-1])} on {short_day(rec['asof'])}")
    return (data_svg(W, H, grid_lines(W, H, 3) + f'<path class="area" d="{area}"/><path class="line" d="{d_path(pa)}"/><path class="dash" d="{d_path(pb)}"/>', label),
            [("line", "High yield"), ("dash", "Investment grade")])


def r_inflation_labour(rec):
    d = rec["data"]
    infl = [v for _, v in d["cpi"]]
    pa, = fit([infl], W, H * 0.55, 8)
    jobs = d["jobs"]
    m = max(abs(v) for _, v in jobs) or 1
    bw = W / len(jobs)
    base = H - 4
    bars = "".join(
        f'<rect class="{"up" if v >= 0 else "down"}" x="{i * bw + 1:.1f}" y="{base - abs(v) / m * 36:.1f}" width="{bw - 2:.1f}" height="{max(abs(v) / m * 36, 0.5):.1f}">'
        f'{tip(f"{month_name(day)}: {signed(v, 0)}k jobs")}</rect>'
        for i, (day, v) in enumerate(jobs))
    label = (f"US consumer price inflation, year on year, {pct(infl[-1], 1)} in {month_name(d['cpi_month'])}, "
             f"above monthly payroll changes, {signed(jobs[-1][1], 0)} thousand in {month_name(d['jobs_month'])}")
    return data_svg(W, H, f'<path class="line" d="{d_path(pa)}"/>' + bars, label), [("line", "Inflation, y/y"), ("up", "Jobs added")]


def r_correlation(rec):
    d = rec["data"]
    names, mx = d["names"], d["matrix"]
    n, gap = len(names), 3
    c = (H - gap * (n - 1)) / n
    cells = []
    for r in range(n):
        for col in range(r, n):
            v = mx[r][col]
            cells.append(f'<rect class="{"up" if v >= 0 else "down"}" x="{col * (c + gap):.1f}" y="{r * (c + gap):.1f}" '
                         f'width="{c:.1f}" height="{c:.1f}" opacity="{0.45 + 0.55 * abs(v):.2f}">'
                         f'{tip(f"{names[r]} and {names[col]}: {v:+.2f}".replace("-", MINUS))}</rect>')
    pairs = [f"{names[r]} and {names[col]} {mx[r][col]:+.2f}".replace("-", MINUS) for r in range(n) for col in range(r + 1, n)]
    label = f"Correlation of daily returns over {d['sessions']} sessions to {short_day(rec['asof'])}: " + ", ".join(pairs)
    return data_svg(H, H, "".join(cells), label, stretch=False), [("up", "Positive"), ("down", "Negative")]


def r_breadth(rec):
    d = rec["data"]
    net = [(day, adv - dec, adv, dec) for day, adv, dec, _ in d["sessions"]]
    m = max(abs(v) for _, v, _, _ in net) or 1
    gap = 3
    bw = (W - gap * (len(net) - 1)) / len(net)
    mid = H / 2
    bars = [f'<line class="ref" x1="0" x2="{W}" y1="{mid}" y2="{mid}"/>']
    for i, (day, v, adv, dec) in enumerate(net):
        bh = max(abs(v) / m * (mid - 4), 1.0)
        y = mid - bh if v >= 0 else mid
        bars.append(f'<rect class="{"up" if v >= 0 else "down"}" x="{i * (bw + gap):.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}">'
                    f'{tip(f"{short_day(day)}: {adv} up, {dec} down")}</rect>')
    label = (f"Advancers less decliners across the Andra Markets watchlist of {d['size']} US large caps, "
             f"{len(net)} sessions to {short_day(rec['asof'])}: " + ", ".join(f"{short_day(day)} {signed(v, 0)}" for day, v, _, _ in net))
    return data_svg(W, H, "".join(bars), label), [("up", "More advancers"), ("down", "More decliners")]


REAL = {
    "yield_curve": r_yield_curve, "fed_path": r_fed_path, "sector_heatmap": r_sector_heatmap,
    "vol_term": r_vol_term, "global_indices": r_global_indices, "fx_majors": r_fx_majors,
    "commodities": r_commodities, "credit_spreads": r_credit_spreads,
    "inflation_labour": r_inflation_labour, "breadth": r_breadth, "correlation": r_correlation,
}


def tile_asof(key, rec):
    """The tile's date: the month for monthly data, else the session."""
    if key == "inflation_labour":
        return month_name(rec["asof"])
    return day_med(dt.date.fromisoformat(rec["asof"]))


# Icons -----------------------------------------------------------------------

ICON_NAMES = ["warning-circle", "arrow-right", "arrow-up-right", "list", "x", "play", "sun", "moon"] + [
    icon_name for _, url, icon_name in SOCIALS if url
]


def sprite():
    symbols = []
    for name in ICON_NAMES:
        path = re.search(r'd="([^"]+)"', (ICONS / f"{name}.svg").read_text()).group(1)
        symbols.append(f'<symbol id="i-{name}" viewBox="0 0 256 256"><path d="{path}"/></symbol>')
    return '<svg width="0" height="0" style="position:absolute" aria-hidden="true">' + "".join(symbols) + "</svg>"


def icon(name):
    return f'<svg class="icon" aria-hidden="true"><use href="#i-{name}"/></svg>'


# Content ---------------------------------------------------------------------

# Tape: (label, instrument key, decimals). Levels are the latest note's
# closes (see TAPE in tools/import_notes.py). The 10-year is a yield, its
# change in basis points.
TAPE = [
    ("S&amp;P 500", "spx", 2),
    ("Nasdaq 100", "ndx", 2),
    ("Russell 2000", "rut", 2),
    ("Euro Stoxx 50", "sx5e", 2),
    ("Nikkei 225", "nky", 2),
    ("VIX", "vix", 2),
    ("US 10Y yield", "ust10y", 2),
    ("EUR/USD", "eurusd", 4),
    ("WTI crude", "wti", 2),
    ("Gold", "gold", 1),
]
RATES = {"ust10y"}

CATEGORIES = [
    ("rates", "Rates and credit", "Rates"),
    ("macro", "Macro and the Fed", "Macro"),
    ("equities", "Equities", "Equities"),
    ("cross", "Cross-asset", "Cross-asset"),
]

# (key, category, title, description, source). The key names the tile's record
# from tools/dashboard_data.py. A tile still waiting for its first figures
# shows its source and "Data pending", never a stand-in chart.
DASHBOARDS = [
    ("yield_curve", "rates", "Yield curve", "The Treasury curve today against a month ago.", "FRED, US Treasury"),
    ("fed_path", "macro", "Fed path", "Where futures price the policy rate, month by month.", "CME futures, Yahoo Finance; FRED"),
    ("sector_heatmap", "equities", "Sector heatmap", "Every S&amp;P 500 sector, ranked by the day's move.", "Yahoo Finance, sector ETFs"),
    ("vol_term", "cross", "Volatility term structure", "Implied volatility across expiries, and how its shape is shifting.", "Cboe, Yahoo Finance"),
    ("global_indices", "equities", "Global indices", "Major equity benchmarks across the US, Europe and Asia.", "Yahoo Finance, local closes"),
    ("fx_majors", "cross", "FX majors", "The dollar against the major currencies.", "Yahoo Finance"),
    ("commodities", "cross", "Commodities", "Oil and gold, rebased to the same start.", "Futures, Yahoo Finance"),
    ("credit_spreads", "rates", "Credit spreads", "High yield and investment grade spreads over Treasuries.", "ICE BofA, FRED"),
    ("inflation_labour", "macro", "Inflation and labour", "Inflation prints alongside the monthly jobs report.", "BLS, FRED"),
    ("breadth", "equities", "Watchlist breadth", "Advancers less decliners across the Andra Markets watchlist of US large caps, session by session.", "Andra Markets watchlist, Yahoo Finance"),
    ("correlation", "cross", "Cross-asset correlation", "How stocks, bonds, the dollar and commodities move together.", "Yahoo Finance, daily returns"),
]

# Dashboard pages: key -> (slug, default range, how to read it, source).
DASH_PAGES = {
    "yield_curve": ("yield-curve", "1M",
        "Each dot is the yield on a US Treasury of that maturity; the solid line is the latest close, the dashed one the curve "
        "at the start of the range. Maturities are spaced by the square root of their length, so the short end is not squeezed. "
        "An upward slope is normal: lenders ask more to lend for longer. A curve that falls from left to right (inverted) has "
        "often come before a slowdown. A move in the short end is mostly about Fed policy; a move in the long end about growth, "
        "inflation and the supply of bonds.",
        "Daily Treasury par yields, published by the US Treasury and served by FRED (series DGS1MO to DGS30). FRED posts each "
        "day's curve late in the evening, so the latest curve is usually the previous session's. While FRED is unreachable the "
        "curve comes from the Andra Markets archive of the same FRED figures."),
    "fed_path": ("fed-path", "1M",
        "Each point is one month's 30-day fed funds future: 100 minus its price is the average overnight rate the market expects "
        "for that month. A path that slopes down prices rate cuts; one that rises prices hikes. The dashed line is the same path "
        "as it was priced at the start of the range, so the gap shows how expectations have moved. Futures carry a small risk "
        "premium, so they are a guide to expectations, not a forecast.",
        "CBOT 30-day fed funds futures, daily settlement, from Yahoo Finance. The effective federal funds rate is from the "
        "Federal Reserve Bank of New York, served by FRED (series EFFR), when FRED is reachable."),
    "sector_heatmap": ("sector-heatmap", "1D",
        "Each bar is one of the eleven S&amp;P 500 sectors, through the Select Sector SPDR ETF that tracks it, over the chosen "
        "range. Leaders and laggards show where money is rotating: defensive sectors (staples, utilities, health care) tend to "
        "lead when investors are cautious, cyclical ones (technology, discretionary, financials, energy) when they are confident.",
        "Select Sector SPDR ETFs (XLK, XLF, XLV, XLY, XLP, XLE, XLI, XLB, XLRE, XLU, XLC), price change between daily closes, "
        "from Yahoo Finance. Prices only; dividends are not included."),
    "vol_term": ("volatility-term-structure", "1M",
        "Each dot is a Cboe index of the S&amp;P 500 volatility that options imply over a horizon: 9 days, 1, 3 and 6 months. "
        "Normally the line rises with the horizon (contango): calm now, more uncertainty further out. When near-term volatility "
        "rises above longer-term volatility (backwardation), the market is pricing stress now. The dashed line is the structure "
        "at the start of the range.",
        "Cboe VIX9D, VIX, VIX3M and VIX6M index closes, from Yahoo Finance. Levels are in volatility points (annualised percent)."),
    "global_indices": ("global-indices", "1D",
        "Each bar is a major equity benchmark's price change over the range, measured from each index's own local closes, so "
        "Asian, European and American markets are compared on their own sessions. Changes are in local currency and leave out "
        "dividends.",
        "S&amp;P 500, Euro Stoxx 50, DAX 40, FTSE 100, Nikkei 225, Hang Seng, Bovespa and S&amp;P/TSX closes, from Yahoo Finance."),
    "fx_majors": ("fx-majors", "1D",
        "Each bar is the US dollar's move against one major currency over the range. A bar to the right means the dollar "
        "gained: it buys more of that currency. A broad move in one direction says more about the dollar itself; a single "
        "outlier says more about that currency.",
        "Spot exchange rates (EUR/USD, USD/JPY, GBP/USD, USD/CHF, USD/CAD, AUD/USD), daily closes from Yahoo Finance. For pairs "
        "quoted against the dollar (EUR/USD) the sign is flipped so every bar reads as the dollar's move."),
    "commodities": ("commodities", "3M",
        "Both lines start at 100 on the first day of the range, so the gap between them is the difference in performance, "
        "not in price. Above 100 means a gain since then, below 100 a loss. Oil moves with growth and supply news; gold with "
        "real yields, the dollar and demand for safety, so the two often part ways.",
        "NYMEX WTI crude (CL) and COMEX gold (GC) front-month futures, daily closes, from Yahoo Finance. A session still trading "
        "is left out. The front month rolls to the next contract near expiry, which can add a small jump."),
    "credit_spreads": ("credit-spreads", "6M",
        "Each line is the extra yield companies pay over Treasuries of the same maturity: high yield (below investment grade) "
        "and investment grade. Spreads widen when investors fear defaults and tighten when they are confident, so a sudden "
        "widening in high yield is an early sign of stress.",
        "ICE BofA US High Yield and US Corporate option-adjusted spreads (BAMLH0A0HYM2, BAMLC0A0CM), daily, served by FRED. "
        "FRED carries ICE data with a short delay."),
    "inflation_labour": ("inflation-and-labour", "2Y",
        "The line is consumer price inflation: the change in the CPI over the same month a year earlier. The bars are the jobs "
        "the economy added or lost each month (nonfarm payrolls, in thousands). Together they are the two halves of the Fed's "
        "mandate: stable prices and maximum employment. Both are revised after release; the figures here are the latest vintage.",
        "US Bureau of Labor Statistics: CPI for all urban consumers, seasonally adjusted (CPIAUCSL), and total nonfarm "
        "payrolls (PAYEMS), served by FRED. A month without a release is left blank."),
    "breadth": ("watchlist-breadth", "1M",
        "Each bar is one trading session: the number of stocks on the Andra Markets watchlist that rose, less the number that "
        "fell. Tall green bars mean the gains were broad; an index that rises while most bars are red is being carried by a few "
        "large names. This is the watchlist's breadth, not the whole market's.",
        "The Andra Markets watchlist of US large caps, closes from Yahoo Finance, as recorded in each published close note's "
        "verified figures. History starts with the first archived note."),
    "correlation": ("cross-asset-correlation", "3M",
        "Each cell is the correlation of two assets' daily returns over the window, from +1 (they move together) to &minus;1 "
        "(they move in opposite directions). Stocks and bonds moving apart is the classic hedge; when they start moving "
        "together, a balanced portfolio loses its cushion.",
        "Daily closes from Yahoo Finance: S&amp;P 500, iShares 20+ Year Treasury Bond ETF (TLT), ICE US Dollar Index, WTI "
        "crude and gold front-month futures. Log returns over the sessions all five traded."),
}
SHORT = {"S&P 500": "S&P", "Long Treasuries": "TLT", "Dollar index": "USD", "WTI crude": "WTI", "Gold": "Gold"}


def latest_rows(key, rec):
    """The page's "Latest" table: (name, level, note) rows."""
    det, asof = rec["detail"], rec["asof"]
    if det["kind"] == "curve":
        cmp = det["compare"].get("1M") or next(iter(det["compare"].values()))
        rows = []
        idx = {lb: i for i, lb in enumerate(det["labels"])}
        pick = {"yield_curve": ["3M", "2Y", "10Y", "30Y"], "vol_term": det["labels"]}.get(key)
        if key == "fed_path":
            pick = [det["labels"][i] for i in (0, min(2, len(det["labels"]) - 1), min(5, len(det["labels"]) - 1), len(det["labels"]) - 1)]
        for lb in pick:
            i = idx[lb]
            v, o = det["values"][i], cmp["values"][i]
            if det.get("unit") == "%" or key == "yield_curve":
                rows.append((("Implied, " if key == "fed_path" else "") + lb, pct(v, 2), f"{signed((v - o) * 100, 0, 'bp')} since {short_day(cmp['date'])}"))
            else:
                rows.append((f"VIX {lb}", f"{v:.2f}", f"{signed(v - o, 2)} since {short_day(cmp['date'])}"))
        if key == "yield_curve":
            v = (det["values"][idx["10Y"]] - det["values"][idx["2Y"]]) * 100
            o = (cmp["values"][idx["10Y"]] - cmp["values"][idx["2Y"]]) * 100
            rows.append(("10Y less 2Y", signed(v, 0, "bp"), f"{signed(v - o, 0, 'bp')} since {short_day(cmp['date'])}"))
        if det.get("ref"):
            rows.append((det["ref"]["name"], pct(det["ref"]["value"], 2), short_day(det["ref"]["date"])))
        return rows
    if det["kind"] == "perf":
        r = det["ranges"]["1D"]
        rows = sorted(zip(det["names"], r["values"], r["to"]), key=lambda x: -x[1])
        return [(esc(n), chg(v), "on the day" if t == asof else f"close of {short_day(t)}") for n, v, t in rows]
    if det["kind"] == "lines":
        out = []
        for sr in det["series"]:
            v = sr["values"]
            dec = sr.get("dec", det.get("dec", 2))
            if det.get("rebase"):
                out.append((sr["name"], f"{v[-1]:,.{dec}f}", f"{chg((v[-1] / v[-2] - 1) * 100)} on the day"))
                out.append((f"{sr['name']}, 1 year", chg((v[-1] / v[0] - 1) * 100), f"since {short_day(det['dates'][0])}"))
            else:
                base = det["dates"].index(next(x for x in det["dates"] if x >= months_back_iso(det["dates"][-1], 1)))
                out.append((sr["name"], pct(v[-1], 2), f"{signed((v[-1] - v[base]) * 100, 0, 'bp')} since {short_day(det['dates'][base])}"))
        return out
    if det["kind"] == "macro":
        cpi = [(dte, v) for dte, v in zip(det["dates"], det["cpi"]) if v is not None]
        jobs = [(dte, v) for dte, v in zip(det["dates"], det["jobs"]) if v is not None]
        avg3 = sum(v for _, v in jobs[-3:]) / 3
        return [("Inflation, y/y", pct(cpi[-1][1], 1), month_name(cpi[-1][0])),
                ("Month before", pct(cpi[-2][1], 1), month_name(cpi[-2][0])),
                ("Payrolls", f"{signed(jobs[-1][1], 0)}k", month_name(jobs[-1][0])),
                ("3-month average", f"{signed(avg3, 0)}k", f"to {month_name(jobs[-1][0])}")]
    if det["kind"] == "breadth":
        ss = det["sessions"]
        last = ss[-1]
        avg = sum(a - b for _, a, b, _ in ss[-20:]) / len(ss[-20:])
        return [("Advancers", str(last[1]), short_day(last[0])), ("Decliners", str(last[2]), short_day(last[0])),
                ("Net", signed(last[1] - last[2], 0), short_day(last[0])),
                ("Net, 20-session average", signed(avg, 1), f"of {sum(last[1:])} stocks")]
    if det["kind"] == "matrix":
        win = det["windows"].get("3M") or next(iter(det["windows"].values()))
        m, names = win["matrix"], det["names"]
        return [(f"S&amp;P 500 and {esc(names[j])}", signed(m[0][j], 2), f"{win['sessions']} sessions")
                for j in range(1, len(names))]
    return []


def months_back_iso(iso_day, n):
    d = dt.date.fromisoformat(iso_day)
    y, m = divmod(d.month - 1 - n, 12)
    y, m = d.year + y, m + 1
    for day in range(d.day, 27, -1):
        try:
            return dt.date(y, m, day).isoformat()
        except ValueError:
            continue
    return dt.date(y, m, min(d.day, 28)).isoformat()


def dash_ranges(det):
    if det["kind"] == "curve":
        return list(det["compare"])
    if det["kind"] == "perf":
        return list(det["ranges"])
    if det["kind"] == "matrix":
        return list(det["windows"])
    return det["ranges"]


def dashboard_page(key, cat, name, desc, source, rec):
    slug, default, how, long_source = DASH_PAGES[key]
    cat_label = {k: label for k, label, _ in CATEGORIES}[cat]
    crumbs = f'<p class="dd__crumbs"><a href="../../#dashboards">Dashboards</a> <span aria-hidden="true">/</span> {cat_label}</p>'
    if rec:
        det = dict(rec["detail"])
        if key == "fx_majors":
            det["sign"] = True
        if det["kind"] == "matrix":
            det["short"] = [SHORT.get(n, n) for n in det["names"]]
        ranges = dash_ranges(det)
        cur = default if default in ranges else ranges[-1]
        chips = "".join(f'<button type="button" class="chip" data-range="{r}" aria-pressed="{"true" if r == cur else "false"}">{r}</button>'
                        for r in ranges)
        asof = tile_asof(key, rec)
        meta = f'{esc(rec["source"])}. As of {asof}.'
        payload = json.dumps(det, separators=(",", ":")).replace("</", "<\\/")
        rows = latest_rows(key, rec)
        kpis = "".join(f'<li class="kpi__item"><span class="kpi__name">{n}</span><span class="kpi__level">{lv}</span>'
                       f'<span class="kpi__chg">{note}</span></li>' for n, lv, note in rows)
        figure = (f'<div class="filters dd__ranges" role="group" aria-label="Time range">{chips}</div>'
                  f'<figure class="dd__chart"><div class="dd__plot dd__plot--{det["kind"]}" role="img" tabindex="0" aria-label="{esc(name)}"></div>'
                  f'<figcaption><p class="key dd__key"></p><p class="dd__read" aria-live="polite"></p></figcaption></figure>'
                  f'<noscript><p class="dd__pending">The chart needs JavaScript. The latest values are in the table.</p></noscript>'
                  f'<script type="application/json" id="dd-data">{payload}</script>')
        side = (f'<aside class="report__side dd__side" aria-labelledby="side-title">'
                f'<h2 class="report__side-title" id="side-title">Latest</h2><ul class="kpi">{kpis}</ul>'
                f'<p class="report__src">{esc(rec["source"])}, {asof}.</p></aside>')
        data_attrs = f' data-dash data-range="{cur}" data-title="{esc(name)}" data-asof="{asof}"'
        scripts = ("dashboard.js",)
    else:
        meta = f"{source}. Data pending."
        figure = '<div class="dd__plot dd__plot--pending"><p class="dd__pending">Data pending</p></div>'
        side, data_attrs, scripts = "", "", ()
    body = f"""<main id="main" class="page dd"{data_attrs}>
  <div class="wrap dd__grid">
    <header class="page__head dd__head">
      {crumbs}
      <h1 class="page__title">{name}</h1>
      <p class="lede">{desc}</p>
      <p class="note__meta">{meta}</p>
    </header>
    <section class="dd__main" aria-label="Chart">{figure}</section>
    {side}
    <div class="page__body dd__text">
      <section aria-labelledby="dd-how"><h2 id="dd-how">How to read it</h2><p>{how}</p></section>
      <section aria-labelledby="dd-src"><h2 id="dd-src">Source</h2><p>{long_source}</p><p>For information only. Not investment advice.</p></section>
    </div>
  </div>
</main>"""
    return shell(
        title=f"{name}: Andra Markets dashboard",
        desc=esc(html.unescape(desc)),
        body=body,
        home="../../",
        base="../../",
        path=f"dashboards/{slug}/",
        scripts=scripts,
    )


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


# Close notes -----------------------------------------------------------------

NOTES = ROOT / "data" / "notes"
REPORTS = ROOT / "reports"

# Report page sections, in reading order: (field, heading).
SECTIONS = [
    ("takeaways", "Takeaways"),
    ("desk_view", "Desk view"),
    ("watching", "What we watch"),
    ("equities", "Equities"),
    ("rates", "Rates"),
    ("credit", "Credit"),
    ("fx", "FX"),
    ("commodities", "Commodities"),
    ("volatility", "Volatility"),
    ("digital", "Digital assets"),
    ("international", "International"),
    ("correlation", "Correlation"),
]


def load_notes():
    """Published notes, newest first."""
    notes = []
    for f in NOTES.glob("*.json"):
        rec = json.loads(f.read_text(encoding="utf-8"))
        if rec.get("published") is False:
            continue
        rec["day"] = dt.date.fromisoformat(rec["date"])
        notes.append(rec)
    return sorted(notes, key=lambda r: r["date"], reverse=True)


def esc(text):
    return html.escape(text, quote=True)


def day_long(d):
    return f"{d:%A} {d.day} {d:%B %Y}"


def day_med(d):
    return f"{d.day} {d:%b %Y}"


def read_minutes(rec):
    words = 0
    for v in rec["note"].values():
        for t in v if isinstance(v, list) else [v]:
            words += len(t.split())
    return max(1, math.ceil(words / 230))


def paragraphs(text):
    return "".join(f"<p>{esc(' '.join(p.split()))}</p>" for p in re.split(r"\n\s*\n", text) if p.strip())


MINUS = "\u2212"


def signed(v, decimals, unit=""):
    r = round(v, decimals)
    if r == 0:
        return f"{0:.{decimals}f}{unit}"
    return f"{'+' if r > 0 else MINUS}{abs(r):,.{decimals}f}{unit}"


def tape_items(rec):
    """Closing level and daily change for each tape instrument."""
    items, any_stale = [], False
    for label, key, dec in TAPE:
        row = (rec.get("closes") or {}).get(key) or {}
        last, chg = row.get("last"), row.get("chg")
        if last is None:
            level, change = "n/a", ""
        elif key in RATES:
            level = f"{last:.{dec}f}%"
            change = signed(chg, 0, "bp") if chg is not None else "n/a"
        else:
            level = f"{last:,.{dec}f}"
            change = signed(chg, 2, "%") if chg is not None else "n/a"
        if last is not None and row.get("stale"):
            change, any_stale = "Prior close", True
        items.append((label, level, change))
    return items, any_stale


# Page ------------------------------------------------------------------------

THEME_BOOT = (
    "(function(){var t='light';try{var q=new URLSearchParams(location.search).get('theme');"
    "if(q==='light'||q==='dark'){t=q;localStorage.setItem('andra-theme',q)}"
    "else{var s=localStorage.getItem('andra-theme');if(s==='light'||s==='dark')t=s}}catch(e){}"
    "document.documentElement.setAttribute('data-theme',t);"
    "var m=document.querySelector('meta[name=theme-color]');if(m)m.content=t==='dark'?'#0a0c0d':'#f4f6f6'})();"
)


def page(notes):
    latest = notes[0] if notes else None
    if latest:
        d = latest["day"]
        items, any_stale = tape_items(latest)
        tape = "".join(
            f'<li class="tape__item"><span class="tape__name">{n}</span>'
            f'<span class="tape__level">{level}</span><span class="tape__chg">{change}</span></li>'
            for n, level, change in items
        )
        tape_title = f'Markets {day_med(d)}, {nyse.close_time(d)} ET'
        tape_note = (f'<a class="tape__note" href="reports/{latest["date"]}/"><span>Latest close note, {day_med(d)}: '
                     f'{esc(latest["note"]["headline"])}</span>{icon("arrow-right")}</a>')
        tape_src = "Close and daily change. Sources: Yahoo Finance, FRED for the US 10Y yield."
        if any_stale:
            tape_src += " Prior close: no print yet for the session."
    else:
        tape = "".join(
            f'<li class="tape__item"><span class="tape__name">{n}</span>'
            f'<span class="tape__level ph">[live]</span><span class="tape__chg ph">[live]</span></li>'
            for n, *_ in TAPE
        )
        tape_title = f'Markets {ph("[date]")}, {ph("[time]")} ET'
        tape_note = (f'<a class="tape__note" href="#note"><span>Latest close note, {ph("[date]")}: '
                     f'<span class="ph ph--ink">[headline]</span></span>{icon("arrow-right")}</a>')
        tape_src = f'Last and daily change. Source {ph("[data vendor]")}'
    dash_data = load_dash_data()
    filters = f'<button type="button" class="chip" data-filter="all" data-label="All" aria-pressed="true">All <span class="chip__n">{len(DASHBOARDS)}</span></button>' + "".join(
        f'<button type="button" class="chip" data-filter="{key}" data-label="{label}" aria-pressed="false">{short} '
        f'<span class="chip__n">{sum(1 for x in DASHBOARDS if x[1] == key)}</span></button>'
        for key, label, short in CATEGORIES
    )
    cat_label = {k: label for k, label, _ in CATEGORIES}
    swatch = {"line": "k-solid", "dash": "k-dash", "up": "sw-up", "down": "sw-down"}

    def tile(i, key, cat, name, desc, source):
        rec = dash_data.get(key)
        if rec:
            chart, leg = REAL[key](rec)
            items = "".join(f'<span><i class="{swatch[kind]}"></i>{label}</span>' for kind, label in leg)
            figure = f'<div class="dash-tile__chart draw">{chart}</div><p class="key">{items}</p>'
            src = f'{cat_label[cat]}. {esc(rec["source"])}, {tile_asof(key, rec)}'
        else:
            figure = '<div class="dash-tile__chart dash-tile__chart--pending"><p>Data pending</p></div><p class="key" aria-hidden="true">&nbsp;</p>'
            src = f"{cat_label[cat]}. {source}."
        return (f'<li class="dash-tile reveal" data-cat="{cat}" style="--i:{i % 3}">'
                f'<a href="dashboards/{DASH_PAGES[key][0]}/" class="dash-tile__link">{figure}'
                f'<div class="dash-tile__text">'
                f'<h3>{name}</h3><p class="dash-tile__desc">{desc}</p>'
                f'<p class="dash-tile__src">{src}</p></div>'
                f'<span class="dash-tile__go">{icon("arrow-up-right")}</span></a></li>')

    tiles = "".join(tile(i, *t) for i, t in enumerate(DASHBOARDS))
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
    if latest:
        archive = "".join(
            f'<li><a href="reports/{r["date"]}/"><time datetime="{r["date"]}">{day_med(r["day"])}</time>'
            f'<span class="note-list__title">{esc(r["note"]["headline"])}</span>{icon("arrow-right")}</a></li>'
            for r in notes[1:4]
        )
        note_latest = f"""<article class="reveal" style="--i:1">
          <h3 class="note__title">{esc(latest["note"]["headline"])}</h3>
          <p class="note__summary">{esc(" ".join(latest["note"]["standfirst"].split()))}</p>
          <p class="note__meta"><time datetime="{latest["date"]}">{day_med(latest["day"])}</time><span>{read_minutes(latest)} min read</span></p>
          <a class="btn" href="reports/{latest["date"]}/">Read the note {icon("arrow-right")}</a>
        </article>"""
        all_notes = "reports/"
    else:
        archive = "".join(
            f'<li><a href="#note"><span class="ph">[date]</span><span class="note-list__title"><span class="ph ph--ink">[Close note headline]</span></span>{icon("arrow-right")}</a></li>'
            for _ in range(3)
        )
        note_latest = f"""<article class="reveal" style="--i:1">
          <h3 class="note__title"><span class="ph ph--ink">[Headline of the latest close note]</span></h3>
          <p class="note__summary">{ph("[Two sentences on the session: what moved, and why it mattered.]")}</p>
          <p class="note__meta">{ph("[date]")}<span>{ph("[n]")} min read</span></p>
          <a class="btn" href="#note">Read the note {icon("arrow-right")}</a>
        </article>"""
        all_notes = "#note"
    learn = "".join(
        f'<li class="reveal" style="--i:{i}"><a href="#learn"><span class="learn-list__title">{t}</span>'
        f'<span class="learn-list__desc">{desc}</span><span class="learn-list__time"><span class="ph">[n]</span> min read</span></a></li>'
        for i, (t, desc) in enumerate(LEARN)
    )
    channels = {label: (url, icon_name) for label, url, icon_name in SOCIALS if url}
    videos = [(platform, shape) for platform, shape in VIDEOS if platform in channels]
    video_items = "".join(
        f'<li class="video video--{shape} reveal" style="--i:{i}"><a href="{channels[platform][0]}">'
        f'<span class="video__frame"><span class="video__play">{icon("play")}</span>'
        f'<span class="video__platform">{icon(channels[platform][1])}{platform}</span></span>'
        f'<span class="video__title"><span class="ph ph--ink">[Video title]</span></span>'
        f'<span class="video__meta"><span class="ph">[duration]</span></span></a></li>'
        for i, (platform, shape) in enumerate(videos)
    )
    watch_layout = "watch-grid--mixed" if any(shape == "wide" for _, shape in videos) else "watch-grid--tall"
    watch_platforms = " and ".join(dict.fromkeys(platform for platform, _ in videos))

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
        <h2 id="tape-title">{tape_title}</h2>
        {tape_note}
      </div>
      <ul class="tape__list" tabindex="0" aria-label="Market levels">{tape}</ul>
      <p class="tape__src">{tape_src}</p>
    </div>
  </section>

  <section class="section dash" id="dashboards" aria-labelledby="dash-title">
    <div class="wrap">
      <div class="section-head">
        <h2 class="section-title reveal" id="dash-title">Dashboards</h2>
        <p class="lede reveal">Interactive views across rates, equities, macro and cross-asset. Each preview names its source and date.</p>
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
            <p class="tool__src">{ph("[source]")}, {ph("[date]")}</p>
          </div>
          <span class="link">Open the explorer {icon("arrow-up-right")}</span>
        </a>
        <a class="tool reveal" href="#lab" style="--i:1">
          <div class="draw">{c_payoff()}</div>
          <p class="key"><span><i class="k-solid"></i>Value today</span><span><i class="k-dash"></i>Payoff at expiry</span><span class="key__note">Illustrative</span></p>
          <div class="tool__text">
            <h3>Options pricer</h3>
            <p>Price European options and watch the Greeks respond as strike, volatility and time change.</p>
            <p class="tool__src">Model {ph("[model]")}. {ph("[source]")}, {ph("[date]")}</p>
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
        {note_latest}
      </div>
      <div class="note__archive reveal" style="--i:2">
        <p class="note__label">Every US trading day, after the close.</p>
        <ol class="note-list">{archive}</ol>
        <a class="link" href="{all_notes}">All notes {icon("arrow-right")}</a>
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
          <p class="key"><span><i class="k-solid"></i>Normal curve</span><span><i class="k-dash"></i>Inverted curve</span><span class="key__note">Diagram, not market data</span></p>
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
        <p class="lede reveal">Market recaps and short explainers on {watch_platforms}. Embeds are placeholders.</p>
      </div>
      <ul class="watch-grid {watch_layout}">{video_items}</ul>
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
      <span class="brand__mark"><img class="brand__mark--light" src="{base}assets/andra-mark-light.png" alt="" width="140" height="160"><img class="brand__mark--dark" src="{base}assets/andra-mark-dark.png" alt="" width="140" height="160"></span>
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
    social_links = "\n".join(
        f'      <li><a href="{url}" rel="me">{icon(icon_name)}{label}</a></li>'
        for label, url, icon_name in SOCIALS if url
    )
    return f"""<footer class="site-footer">
  <div class="wrap grid">
    <div class="foot__brand">
      <a class="brand" href="{home or '#top'}" aria-label="Andra Markets, home">
        <span class="brand__mark"><img class="brand__mark--light" src="{base}assets/andra-mark-light.png" alt="" width="140" height="160" loading="lazy"><img class="brand__mark--dark" src="{base}assets/andra-mark-dark.png" alt="" width="140" height="160" loading="lazy"></span>
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
      <a href="{base}reports/">All notes</a>
      <a href="{base}methodology/">Methodology</a>
    </nav>
    <ul class="foot__social" aria-label="Andra Markets on social media">
{social_links}
    </ul>
    <div class="foot__legal">
      <span>&copy; {ph("[year]")} Andra Markets</span>
      <span>For information only. Not investment advice.</span>
    </div>
  </div>
</footer>"""


def shell(title, desc, body, home, base, path="", scripts=()):
    url = f"{SITE_URL}/{path}" if SITE_URL else ""
    og_image = f"{SITE_URL}/assets/og-image.png" if SITE_URL else f"{base}assets/og-image.png"
    canonical = f'<link rel="canonical" href="{url}">\n<meta property="og:url" content="{url}">\n' if url else ""
    return f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#f4f6f6">
<script>{THEME_BOOT}</script>
<link rel="icon" href="{base}assets/favicon-32.png" sizes="32x32" type="image/png">
<link rel="icon" href="{base}assets/favicon-48.png" sizes="48x48" type="image/png">
<link rel="apple-touch-icon" href="{base}assets/apple-touch-icon.png">
{canonical}<meta property="og:type" content="website">
<meta property="og:site_name" content="Andra Markets">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The Andra Markets engraved horse beside the line Markets, on the record.">
<meta name="twitter:card" content="summary_large_image">
<link rel="preload" href="{base}assets/fonts/schibsted-grotesk-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{base}assets/site.css">
</head>
<body>
{sprite()}
<a class="skip" href="#main">Skip to content</a>

{site_header(home, base)}

{body}

{site_footer(home, base)}

<script src="{base}assets/site.js" defer></script>{"".join(f'<script src="{base}assets/{js}" defer></script>' for js in scripts)}
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
        path="methodology/",
    )


def archive(notes):
    months = {}
    for r in notes:
        months.setdefault((r["day"].year, r["day"].month), []).append(r)
    groups = "".join(
        f'<section class="archive__month" aria-labelledby="m-{y}-{m:02d}">'
        f'<h2 id="m-{y}-{m:02d}">{dt.date(y, m, 1):%B %Y}</h2><ol class="note-list">'
        + "".join(
            f'<li><a href="{r["date"]}/"><time datetime="{r["date"]}">{r["day"].day} {r["day"]:%b}</time>'
            f'<span class="note-list__title">{esc(r["note"]["headline"])}</span>{icon("arrow-right")}</a></li>'
            for r in rows
        )
        + "</ol></section>"
        for (y, m), rows in months.items()
    )
    count = f"{len(notes)} note{'' if len(notes) == 1 else 's'}." if notes else "The first note is on its way."
    body = f"""<main id="main" class="page">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Daily close notes</h1>
      <p class="lede">Every US trading day, after the close. {count}</p>
    </header>
    <div class="archive">{groups}</div>
  </div>
</main>"""
    return shell(
        title="Daily close notes: Andra Markets",
        desc="The Andra Markets close note archive: one research note every US trading day, after the close.",
        body=body,
        home="../",
        base="../",
        path="reports/",
    )


# Report side panel: the session in numbers -----------------------------------

KPIS = [("S&amp;P 500", "spx", 2), ("Nasdaq 100", "ndx", 2), ("US 10Y yield", "ust10y", 2),
        ("VIX", "vix", 2)]
TENOR_YEARS = {"ust1m": 1 / 12, "ust3m": 0.25, "ust6m": 0.5, "ust1y": 1, "ust2y": 2, "ust3y": 3,
               "ust5y": 5, "ust7y": 7, "ust10y": 10, "ust20y": 20, "ust30y": 30}
TENOR_LABEL = {"ust3m": "3M", "ust1y": "1Y", "ust2y": "2Y", "ust5y": "5Y", "ust10y": "10Y", "ust30y": "30Y"}


def prev_session(day):
    d = day - dt.timedelta(days=1)
    for _ in range(10):
        if nyse.is_trading_day(d) is not False:
            return d
        d -= dt.timedelta(days=1)
    return d


def real_svg(w, h, body, label):
    return f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">{body}</svg>'


def bar_chart(rows, label):
    """Diverging horizontal bars for (name, change %, close) rows, largest gain first."""
    rows = sorted(rows, key=lambda r: r[1], reverse=True)
    W, row, top = 300, 19, 2
    H = top + row * len(rows) + 2
    x0, half = 186, 64
    span = max(abs(r[1]) for r in rows) or 1
    body = f'<line class="ref" x1="{x0}" x2="{x0}" y1="0" y2="{H}"/>'
    for i, (name, chg, last) in enumerate(rows):
        y = top + i * row
        wbar = max(1.0, half * abs(chg) / span)
        x = x0 if chg >= 0 else x0 - wbar
        tip = f"{name}: {signed(chg, 2, '%')}" + (f", close {last:,.2f}" if last is not None else "")
        body += (f'<g><title>{esc(tip)}</title>'
                 f'<text class="chart__label" x="0" y="{y + 13}">{esc(name)}</text>'
                 f'<rect class="{"up" if chg >= 0 else "down"}" x="{x:.1f}" y="{y + 4.5}" width="{wbar:.1f}" height="10"/>'
                 f'<text class="chart__value" x="{W}" y="{y + 13}" text-anchor="end">{signed(chg, 2, "%")}</text></g>')
    aria = f"{label}, change at the close: " + ", ".join(f"{n} {signed(c, 2, '%')}" for n, c, _ in rows)
    return real_svg(W, H, body, aria)


def moves_rows(rec):
    rows = []
    for label, key, _ in TAPE:
        c = (rec.get("closes") or {}).get(key) or {}
        if key in RATES or c.get("chg") is None or c.get("last") is None or c.get("stale"):
            continue
        rows.append((html.unescape(label), c["chg"], c["last"]))
    return rows


def curve_chart(rec, d):
    """Treasury curve at its latest close against the session before."""
    curve = [c for c in ((rec.get("charts") or {}).get("curve") or [])
             if c.get("key") in TENOR_YEARS and c.get("last") is not None and c.get("chg") is not None]
    if len(curve) < 4:
        return "", ""
    stale = any(c.get("stale") for c in curve)
    close = prev_session(d) if stale else d
    before = prev_session(close)
    now = [(TENOR_YEARS[c["key"]], c["last"], c["key"]) for c in curve]
    then = [(t, last - c["chg"] / 100) for (t, last, _), c in zip(now, curve)]
    W, H, left, right, top, bottom = 300, 128, 40, 8, 6, 18
    ys = [v for _, v, _ in now] + [v for _, v in then]
    lo, hi = min(ys), max(ys)
    pad = max((hi - lo) * 0.12, 0.05)
    lo, hi = lo - pad, hi + pad
    X = lambda t: left + (W - left - right) * math.sqrt(t) / math.sqrt(30)
    Y = lambda v: top + (H - top - bottom) * (1 - (v - lo) / (hi - lo))
    body = ""
    for k in range(3):
        v = lo + (hi - lo) * (k + 0.5) / 3
        body += (f'<line class="grid-line" x1="{left}" x2="{W - right}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>'
                 f'<text class="chart__label" x="0" y="{Y(v) + 4:.1f}">{v:.2f}%</text>')
    for t, _, key in now:
        if key in TENOR_LABEL:
            body += f'<text class="chart__label" x="{X(t):.1f}" y="{H - 3}" text-anchor="middle">{TENOR_LABEL[key]}</text>'
    path = lambda pts: "M" + " L".join(f"{X(t):.1f} {Y(v):.1f}" for t, v in pts)
    body += f'<path class="dash" d="{path(then)}"/><path class="line" d="{path([(t, v) for t, v, _ in now])}"/>'
    body += "".join(f'<circle class="dot" cx="{X(t):.1f}" cy="{Y(v):.1f}" r="2.5"><title>{c["tenor"]}: {v:.2f}%, {signed(c["chg"], 0, "bp")}</title></circle>'
                    for (t, v, _), c in zip(now, curve))
    two, ten = next((c for c in curve if c["key"] == "ust2y"), None), next((c for c in curve if c["key"] == "ust10y"), None)
    label = f"US Treasury yield curve at the close of {day_med(close)}, against {day_med(before)}"
    if two and ten:
        label += f": 2-year {two['last']:.2f}% ({signed(two['chg'], 0, 'bp')}), 10-year {ten['last']:.2f}% ({signed(ten['chg'], 0, 'bp')})"
    key = (f'<p class="key"><span><i class="k-solid"></i>{close.day} {close:%b}</span>'
           f'<span><i class="k-dash"></i>{before.day} {before:%b}</span></p>')
    src = f"FRED, close of {day_med(close)}"
    if stale:
        src += ", the latest published curve"
    return real_svg(W, H, body, label) + key, src + "."


# Section -> margin chart: (title, rows key in charts.bars or a special, source).
MARGIN = {
    "takeaways": ("The day's moves", "moves", "Yahoo Finance, change at the close"),
    "desk_view": ("Biggest gainers and losers", "movers",
                  "Andra Markets watchlist of US large caps; Yahoo Finance, change at the close"),
    "equities": ("S&amp;P 500 sectors", "sectors", "Sector ETFs, Yahoo Finance, change at the close"),
    "rates": ("Treasury yield curve", "curve", ""),
    "credit": ("Credit proxies", "credit", "Listed ETFs as proxies for each segment; Yahoo Finance, change at the close"),
    "fx": ("Currencies", "fx", "Yahoo Finance, change at the New York close. A rise in USD/xxx is a stronger dollar"),
    "commodities": ("Commodities", "commodities", "Front-month futures, Yahoo Finance, change at the close"),
    "volatility": ("Volatility indices", "volatility", "Yahoo Finance, change at the close"),
    "digital": ("Digital assets", "digital", "Yahoo Finance, change to the New York close"),
    "international": ("Global equity indices", "international", "Yahoo Finance, change at each local close"),
}


def margin_chart(field, rec):
    """The chart beside a section, or "" when the note has no data for it."""
    if field not in MARGIN:
        return ""
    title, what, src = MARGIN[field]
    d, ch = rec["day"], rec.get("charts") or {}
    left_out = 0
    if what == "curve":
        svg, src = curve_chart(rec, d)
        if not svg:
            return ""
        return f'<figure class="report__margin"><h3>{title}</h3>{svg}<figcaption class="report__src">{src}</figcaption></figure>'
    if what == "moves":
        rows = moves_rows(rec)
    elif what == "movers":
        mv = ch.get("movers") or {}
        seen, rows = set(), []
        for name, chg in (mv.get("leaders") or []) + (mv.get("laggards") or []):
            if name not in seen and chg is not None:
                seen.add(name)
                rows.append((name, chg, None))
    else:
        block = (ch.get("bars") or {}).get(what) or {}
        rows = [(n, c, last) for n, last, c in block.get("rows") or []]
        left_out = block.get("left_out") or 0
    if len(rows) < 3:
        return ""
    note = f" {left_out} without a print that day left out." if left_out else ""
    return (f'<figure class="report__margin"><h3>{title}</h3>{bar_chart(rows, html.unescape(title))}'
            f'<figcaption class="report__src">{src}, {day_med(d)}.{note}</figcaption></figure>')


def side_panel(rec):
    d = rec["day"]
    closes, ch = rec.get("closes") or {}, rec.get("charts") or {}
    items = []
    for label, key, dec in KPIS:
        c = closes.get(key) or {}
        if c.get("last") is None:
            continue
        if key in RATES:
            level = f"{c['last']:.{dec}f}%"
            change = "Prior close" if c.get("stale") else (signed(c["chg"], 0, "bp") if c.get("chg") is not None else "n/a")
        else:
            level = f"{c['last']:,.{dec}f}"
            change = signed(c["chg"], 2, "%") if c.get("chg") is not None else "n/a"
        items.append((label, level, change))
    risk, br = ch.get("risk") or {}, ch.get("breadth") or {}
    if risk.get("score") is not None:
        items.append(("Risk score", f"{risk['score']:+.2f}".replace("-", MINUS), esc(risk.get("label") or "")))
    if br.get("advancers") is not None and br.get("decliners") is not None:
        items.append(("Breadth", f"{br['advancers']} / {br['decliners']}", "up / down"))
    if not items:
        return ""
    kpis = "".join(f'<li class="kpi__item"><span class="kpi__name">{n}</span>'
                   f'<span class="kpi__level">{lv}</span><span class="kpi__chg">{chg}</span></li>' for n, lv, chg in items)
    return (f'<aside class="report__side" aria-labelledby="side-title">'
            f'<h2 class="report__side-title" id="side-title">The session in numbers</h2>'
            f'<ul class="kpi">{kpis}</ul>'
            f'<p class="report__src">Close and daily change, {day_med(d)}. Yahoo Finance, FRED; '
            f'risk score and breadth by Andra Markets.</p></aside>')


def report(rec, newer, older):
    n = rec["note"]
    d = rec["day"]
    meta = f'<time datetime="{rec["date"]}">{day_long(d)}</time>'
    if rec.get("edition"):
        meta += f'<span>Edition {esc(rec["edition"])}</span>'
    meta += f"<span>{read_minutes(rec)} min read</span>"
    sections = ""
    for field, heading in SECTIONS:
        v = n.get(field)
        chart = margin_chart(field, rec)
        if not v and not chart:
            continue
        sid = f"s-{field.replace('_', '-')}"
        if not v:
            # The chart has data but the note has no text here (quantitative mode).
            content = "<p>No commentary for this section in this edition.</p>"
        elif isinstance(v, list):
            content = '<ol class="ruled">' + "".join(f"<li>{esc(t)}</li>" for t in v) + "</ol>"
        else:
            content = paragraphs(v)
        sections += f'\n      <section aria-labelledby="{sid}"><h2 id="{sid}">{heading}</h2>{content}</section>'
        sections += chart
    checked = "Every figure in this note was checked against the session's verified fact pack."
    if rec.get("figure_check") == "failed":
        checked = ("This edition did not fully pass the automated figure check against the "
                   "session's verified fact pack. It was reviewed before publication.")
    sources = (f'<section aria-labelledby="s-sources"><h2 id="s-sources">Sources</h2>'
               f"<p>Levels at the official close from Yahoo Finance; the Treasury curve, breakevens and real "
               f"yields from FRED. {checked}</p><p>For information only. Not investment advice.</p></section>")
    pager = ""
    if older:
        pager += f'<a class="link" href="../{older["date"]}/">Previous note, {day_med(older["day"])} {icon("arrow-right")}</a>'
    if newer:
        pager += f'<a class="link" href="../{newer["date"]}/">Next note, {day_med(newer["day"])} {icon("arrow-right")}</a>'
    pager += f'<a class="link" href="../">All notes {icon("arrow-right")}</a>'
    pager += f'<a class="link" href="../../#subscribe">Get the note by email {icon("arrow-right")}</a>'
    standfirst = " ".join(n.get("standfirst", "").split())
    body = f"""<main id="main" class="page report">
  <div class="wrap">
    <article class="report__grid">
      <header class="page__head">
        <h1 class="page__title report__title">{esc(n["headline"])}</h1>
        {f'<p class="lede">{esc(standfirst)}</p>' if standfirst else ""}
        <p class="note__meta">{meta}</p>
        <div class="report__share" hidden>
          <button class="btn" type="button" data-share>Share this note</button>
          <p class="report__share-status" role="status" aria-live="polite"></p>
        </div>
      </header>
      {side_panel(rec)}
      <div class="page__body">{sections}
      {sources}
      </div>
    </article>
    <nav class="report__pager" aria-label="More close notes">{pager}</nav>
  </div>
</main>"""
    return shell(
        title=f"{esc(n['headline'])}: Andra Markets close note, {day_med(d)}",
        desc=esc(standfirst or f"The Andra Markets close note for {day_long(d)}."),
        body=body,
        home="../../",
        base="../../",
        path=f"reports/{rec['date']}/",
    )


def main():
    notes = load_notes()
    (OUT / "index.html").write_text(page(notes))
    (OUT / "methodology").mkdir(exist_ok=True)
    (OUT / "methodology" / "index.html").write_text(methodology())
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "index.html").write_text(archive(notes))
    for i, rec in enumerate(notes):
        newer = notes[i - 1] if i > 0 else None
        older = notes[i + 1] if i + 1 < len(notes) else None
        (REPORTS / rec["date"]).mkdir(exist_ok=True)
        (REPORTS / rec["date"] / "index.html").write_text(report(rec, newer, older))
    dash_data = load_dash_data()
    for key, cat, name, desc, source in DASHBOARDS:
        folder = OUT / "dashboards" / DASH_PAGES[key][0]
        folder.mkdir(parents=True, exist_ok=True)
        rec = dash_data.get(key)
        # A record cached before the pages existed has no history yet: pending until refetched.
        (folder / "index.html").write_text(dashboard_page(key, cat, name, desc, source, rec if rec and rec.get("detail") else None))
    print(f"wrote index.html, methodology/index.html, reports/index.html, {len(DASHBOARDS)} dashboard pages "
          f"and {len(notes)} report page(s)")


if __name__ == "__main__":
    main()
