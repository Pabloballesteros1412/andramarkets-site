#!/usr/bin/env python3
"""Build the Andra Markets site.

Light (default) and dark themes, switched by a header toggle and remembered
per visitor. Writes:

    index.html                 the homepage
    methodology/index.html     methodology (placeholder page)
    reports/index.html         every published close note
    reports/<date>/index.html  one page per note, rendered from its text
    dashboards/<slug>/         one page per dashboard (assets/dashboard.js draws the chart)
    calendar/                  the calendar, five weeks (assets/calendar.js: tabs and filters)
    calendar/week/<monday>/    one page per week since the calendar started

    python3 tools/build_site.py

Close notes come from data/notes/*.json, written by tools/import_notes.py.
With none published, the home page keeps its placeholders. The tape shows the
latest note's closing levels. No PDF or facts file is ever linked: the site is
free, and those downloads are reserved for paid subscribers later.

Dashboard tiles draw real figures from .cache/dashboards/tiles.json, written
at deploy time by tools/dashboard_data.py, with their source and date; a tile
without a record shows its source and "Data pending". Lab and Learn charts are schematic
shapes, not market data, and labelled "Illustrative". The calendar reads
.cache/calendar/calendar.json, written by tools/calendar_data.py. Follow DESIGN.md.
"""
import datetime as dt
import html
import json
import math
import random
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nyse  # noqa: E402
from calendar_data import MOVES as CAL_MOVES, SOURCES as CAL_SOURCES  # noqa: E402

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

ICON_NAMES = ["warning-circle", "arrow-right", "arrow-up-right", "list", "x", "play", "sun", "moon",
              "magnifying-glass", "check", "link"] + [
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
                rows.append((("Implied, " if key == "fed_path" else "") + lb, pct(v, 2), mv(f"{signed((v - o) * 100, 0, 'bp')} since {short_day(cmp['date'])}")))
            else:
                rows.append((f"VIX {lb}", f"{v:.2f}", mv(f"{signed(v - o, 2)} since {short_day(cmp['date'])}")))
        if key == "yield_curve":
            v = (det["values"][idx["10Y"]] - det["values"][idx["2Y"]]) * 100
            o = (cmp["values"][idx["10Y"]] - cmp["values"][idx["2Y"]]) * 100
            # The spread is a level (ink); its change since then is a move.
            rows.append(("10Y less 2Y", signed(v, 0, "bp"), mv(f"{signed(v - o, 0, 'bp')} since {short_day(cmp['date'])}")))
        if det.get("ref"):
            rows.append((det["ref"]["name"], pct(det["ref"]["value"], 2), short_day(det["ref"]["date"])))
        return rows
    if det["kind"] == "perf":
        r = det["ranges"]["1D"]
        rows = sorted(zip(det["names"], r["values"], r["to"]), key=lambda x: -x[1])
        return [(esc(n), mv(chg(v)), "on the day" if t == asof else f"close of {short_day(t)}") for n, v, t in rows]
    if det["kind"] == "lines":
        out = []
        for sr in det["series"]:
            v = sr["values"]
            dec = sr.get("dec", det.get("dec", 2))
            if det.get("rebase"):
                out.append((sr["name"], f"{v[-1]:,.{dec}f}", mv(f"{chg((v[-1] / v[-2] - 1) * 100)} on the day")))
                out.append((f"{sr['name']}, 1 year", mv(chg((v[-1] / v[0] - 1) * 100)), f"since {short_day(det['dates'][0])}"))
            else:
                base = det["dates"].index(next(x for x in det["dates"] if x >= months_back_iso(det["dates"][-1], 1)))
                out.append((sr["name"], pct(v[-1], 2), mv(f"{signed((v[-1] - v[base]) * 100, 0, 'bp')} since {short_day(det['dates'][base])}")))
        return out
    if det["kind"] == "macro":
        cpi = [(dte, v) for dte, v in zip(det["dates"], det["cpi"]) if v is not None]
        jobs = [(dte, v) for dte, v in zip(det["dates"], det["jobs"]) if v is not None]
        avg3 = sum(v for _, v in jobs[-3:]) / 3
        return [("Inflation, y/y", pct(cpi[-1][1], 1), month_name(cpi[-1][0])),
                ("Month before", pct(cpi[-2][1], 1), month_name(cpi[-2][0])),
                ("Payrolls", mv(f"{signed(jobs[-1][1], 0)}k"), month_name(jobs[-1][0])),
                ("3-month average", mv(f"{signed(avg3, 0)}k"), f"to {month_name(jobs[-1][0])}")]
    if det["kind"] == "breadth":
        ss = det["sessions"]
        last = ss[-1]
        avg = sum(a - b for _, a, b, _ in ss[-20:]) / len(ss[-20:])
        return [("Advancers", str(last[1]), short_day(last[0])), ("Decliners", str(last[2]), short_day(last[0])),
                ("Net", mv(signed(last[1] - last[2], 0)), short_day(last[0])),
                ("Net, 20-session average", mv(signed(avg, 1)), f"of {sum(last[1:])} stocks")]
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


def move_class(text):
    """"mv--up" or "mv--down" for a figure that shows a rise or a fall, read from
    its sign as printed (a figure that rounds to zero has none and stays in ink)."""
    t = re.sub(r"<[^>]+>", "", str(text)).lstrip("(")
    return "mv--up" if t.startswith("+") else "mv--down" if t.startswith(MINUS) else ""


def mv(text):
    """A rise or a fall in red or green, its sign kept (DESIGN.md, The Rise and Fall
    Rule). Colours the leading signed figure only: "+5bp since 3 Oct" keeps its
    words in ink."""
    m = re.match(r"([+\u2212][^\s,]*)(.*)", str(text), re.S)
    if not m:
        return text
    return f'<span class="mv {move_class(m.group(1))}">{m.group(1)}</span>{m.group(2)}'


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


def page(notes, cal):
    latest = notes[0] if notes else None
    if latest:
        d = latest["day"]
        items, any_stale = tape_items(latest)
        tape = "".join(
            f'<li class="tape__item"><span class="tape__name">{n}</span>'
            f'<span class="tape__level">{level}</span><span class="tape__chg {move_class(change)}">{change}</span></li>'
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
    calendar = calendar_home(cal, dt.datetime.now(dt.timezone.utc)) or '<p class="cl__none reveal">The calendar fills at the next deploy.</p>'
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
          <p class="lede reveal">This week's high-importance releases, central bank meetings and earnings. Times in New York and Madrid.</p>
        </div>
        <a class="link reveal" href="calendar/">Full calendar {icon("arrow-right")}</a>
      </div>
      <div class="reveal">{calendar}</div>
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
      <a href="{base}companies/">Companies</a>
      <a href="{home}#lab">Lab</a>
      <a href="{base}calendar/">Calendar</a>
      <a href="{home}#note">Daily note</a>
      <a href="{home}#learn">Learn</a>
      <a href="{home}#watch">Watch</a>
      <a class="nav__subscribe" href="{home}#subscribe">Subscribe</a>
    </nav>
    <button class="search-btn" type="button" aria-haspopup="dialog" aria-label="Search Andra Markets" hidden>
      <svg class="icon" aria-hidden="true"><use href="#i-magnifying-glass"/></svg><span>Search</span><kbd>⌘K</kbd>
    </button>
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
      <a href="{base}companies/">Companies</a>
      <a href="{home}#lab">Lab</a>
      <a href="{base}calendar/">Calendar</a>
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
<body data-base="{base}">
{sprite()}
<a class="skip" href="#main">Skip to content</a>

{site_header(home, base)}

{body}

{site_footer(home, base)}

<script src="{base}assets/site.js" defer></script>{"".join(f'<script src="{base}assets/{js}" defer></script>' for js in scripts)}
</body>
</html>
"""


METHOD_QA = [
    ("Where do the figures come from?",
     "Every chart names its source and date under it: FRED and the US Treasury for rates, Yahoo Finance for prices, "
     "Cboe for volatility, CME futures for the Fed path, ICE BofA for credit spreads, the BLS for jobs and inflation, "
     "and the archive of published Andra Markets close notes."),
    ("When is the close note published?",
     "Every US trading day after the close. The site looks for a new note every half hour through the European evening "
     "and night, and publishes it once it passes every check. A note dated on a day the NYSE did not trade is held back, "
     "never published."),
    ("What happens when a source fails?",
     "The dashboard keeps its last good figures and shows their own date, so you can always see how old a number is. "
     "A dashboard with no figures yet says Data pending instead of showing a made-up chart."),
]


def questions():
    """Methodology questions: the first open; site.js keeps one open at a time."""
    out = []
    for i, (q, a) in enumerate(METHOD_QA):
        first = i == 0
        out.append(
            f'<div class="acc__item{" is-open" if first else ""}">'
            f'<h3><button type="button" class="acc__btn" id="qa-b{i}" aria-expanded="{"true" if first else "false"}" aria-controls="qa-p{i}">'
            f'<span>{q}</span><span class="acc__plus" aria-hidden="true"></span></button></h3>'
            f'<div class="acc__panel" id="qa-p{i}" role="region" aria-labelledby="qa-b{i}"><div><p>{a}</p></div></div></div>')
    return "".join(out)


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
      <section aria-labelledby="m-questions">
        <h2 id="m-questions">Questions</h2>
        <div class="acc">{questions()}</div>
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
                 f'<text class="chart__value {move_class(signed(chg, 2, "%"))}" x="{W}" y="{y + 13}" text-anchor="end">{signed(chg, 2, "%")}</text></g>')
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
                   f'<span class="kpi__level">{lv}</span><span class="kpi__chg">{mv(chg)}</span></li>' for n, lv, chg in items)
    return (f'<aside class="report__side" aria-labelledby="side-title">'
            f'<h2 class="report__side-title" id="side-title">The session in numbers</h2>'
            f'<ul class="kpi">{kpis}</ul>'
            f'<p class="report__src">Close and daily change, {day_med(d)}. Yahoo Finance, FRED; '
            f'risk score and breadth by Andra Markets.</p></aside>')


def report(rec, newer, older, cal):
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
    session = calendar_link(cal, d)
    if session:
        pager += f'<a class="link" href="../../{session}">The calendar for this session {icon("arrow-right")}</a>'
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
          <button class="btn" type="button" data-share><span class="swap"><span class="swap__a">{icon("link")}Share this note</span><span class="swap__b" aria-hidden="true">{icon("check")}Link copied</span></span></button>
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


# Calendar ---------------------------------------------------------------------
#
# Read from .cache/calendar/calendar.json, written at deploy time by
# tools/calendar_data.py. calendar/ holds this week and the next four behind
# week tabs; calendar/week/<monday>/ keeps every week since the calendar
# started, so each close note links to the events of its session.

CAL_DATA = ROOT / ".cache" / "calendar" / "calendar.json"
CAL_WEEKS = 5
NY = ZoneInfo("America/New_York")
MADRID = ZoneInfo("Europe/Madrid")
CAL_TYPES = [("macro", "Macro"), ("market", "Market structure"), ("earnings", "Earnings")]
CAL_REGIONS = ["US", "Euro area", "UK", "Japan", "China"]
TIMING = {"before": "Before open", "after": "After close", "none": "Time not given"}
CAL_MARKETS = [("us", "US"), ("europe", "Europe"), ("asia", "Asia")]
EURO_AREA = {"Germany", "France", "Netherlands", "Italy", "Spain", "Belgium", "Ireland", "Finland", "Austria",
             "Portugal", "Luxembourg", "Greece", "Slovakia", "Slovenia", "Croatia", "Bulgaria"}


def region_chip(country):
    """The Region chip an earnings row also answers to: its home economy."""
    return ("Euro area" if country in EURO_AREA else "China" if country in ("China", "Hong Kong") else country)
CAL_CITED = {"cboe": "market", "spdji": "market"}  # read by the market rules, not fetched


def load_calendar():
    try:
        return json.loads(CAL_DATA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def cal_today():
    return dt.datetime.now(NY).date()


def week_of(d):
    return d - dt.timedelta(days=d.weekday())


def clock(t):
    return f"{t.hour % 12 or 12}:{t.minute:02d} {'am' if t.hour < 12 else 'pm'}"


def cal_day_label(d):
    return f"{d:%A} {d.day} {d:%b}"


def week_label(monday):
    sunday = monday + dt.timedelta(days=6)
    if monday.month == sunday.month:
        return f"{monday.day} to {sunday.day} {sunday:%b}"
    return f"{monday.day} {monday:%b} to {sunday.day} {sunday:%b}"


def cal_sort(e):
    """All-day items first, then by time; before the open sits just before 9:30 am ET,
    after the close at 4:00 pm, and a time not given last."""
    if e.get("kind") == "earnings":
        return {"before": (1, 9 * 60 + 29), "after": (1, 16 * 60), "none": (2, 0)}[e.get("timing") or "none"], e["title"]
    if e.get("utc"):
        t = dt.datetime.fromisoformat(e["utc"]).astimezone(NY)
        return (1, t.hour * 60 + t.minute), e["title"]
    return ((2, 0) if e.get("no_time") else (0, 0)), e["title"]


def cal_reaction(e, now):
    """The stock's move on its first full session after the report, coloured as a
    rise or a fall, and its benchmark's move that session (DESIGN.md, Calendar)."""
    r = e.get("reaction")
    if r:
        bench = (f", {esc(r['bench'])} {mv(signed(r['bench_move'], 2, '%'))}" if r.get("bench_move") is not None else "")
        return (f'<span class="cl__react"><span class="cl__rlabel">First session</span> '
                f'{mv(signed(r["move"], 2, "%"))}<span class="cl__bench">{bench}</span></span>')
    day = dt.date.fromisoformat(e.get("local_day") or e["date"])
    if 0 <= (now.date() - day).days <= 3 and now.date() >= day:
        return '<span class="cl__react"><span class="cl__rlabel">First session</span> <span class="cl__pending">not closed yet</span></span>'
    return ""


def cal_row(e, sources, now):
    """One table row, in the approved mock's shape (DESIGN.md, Calendar)."""
    kind = e.get("kind", "macro")
    market = e.get("market", "us")
    if kind == "earnings" and market != "us" and e.get("timing") in ("before", "after") and e.get("stamp"):
        # A known time outside New York: the clocks, and the session it falls in.
        t = dt.datetime.fromisoformat(e["stamp"])
        times = (f'<td class="cl__ny"><time datetime="{e["stamp"]}">{clock(t.astimezone(NY))}</time></td>'
                 f'<td class="cl__md">{clock(t.astimezone(MADRID))}</td>')
    elif kind == "earnings":
        times = f'<td class="cl__ny" colspan="2">{TIMING[e.get("timing") or "none"]}</td>'
    elif e.get("utc"):
        t = dt.datetime.fromisoformat(e["utc"])
        ny, md = t.astimezone(NY), t.astimezone(MADRID)
        times = (f'<td class="cl__ny"><time datetime="{e["utc"]}">{clock(ny)}</time></td>'
                 f'<td class="cl__md">{clock(md)}</td>')
    else:
        times = f'<td class="cl__ny" colspan="2">{"Time not given" if e.get("no_time") else "All day"}</td>'
    src = sources.get(e["src"], {}).get("name", "")
    if kind == "earnings":
        status = "Estimated date" if e.get("status") != "confirmed" else "Confirmed date"
        tags = f'<span class="tag">{status}</span>'
        if e.get("report_type"):
            tags += f'<span class="tag">{esc(e["report_type"])}</span>'
        local = ""
        if market != "us" and e.get("timing") in ("before", "after") and e.get("stamp"):
            local = f'. {"Before" if e["timing"] == "before" else "After"} the local {"open" if e["timing"] == "before" else "close"}'
        meta = (f'<span class="cl__meta"><span class="cl__mregion">{e["country"]}. </span>Yahoo Finance{local}</span>'
                f'<span class="cl__tags">{tags}</span>')
    else:
        meta = f'<span class="cl__meta"><span class="cl__mregion">{e["country"]}. </span>{esc(src)}</span>'
    figure = mv if e.get("ind") in CAL_MOVES else (lambda x: x)
    prev = figure(esc(e.get("previous") or ""))
    if prev and e.get("prev_period") and kind == "earnings":
        prev += f", {esc(e['prev_period'])}"
    released = now >= (dt.datetime.fromisoformat(e["utc"]) if e.get("utc")
                       else dt.datetime.combine(dt.date.fromisoformat(e["date"]), dt.time(23, 59), NY))
    if e.get("actual"):
        href = esc(e.get("actual_url") or e["url"])
        actual = f'<a class="cl__act" href="{href}">{figure(esc(e["actual"]))} {icon("arrow-up-right")}</a>'
    elif released and (e.get("ind") or kind == "earnings") and (e.get("previous") or kind == "earnings"):
        actual = '<span class="cl__pending">Figures pending</span>'
    else:
        actual = ""
    if kind == "earnings":
        actual += cal_reaction(e, now)
    label = "Year ago" if kind == "earnings" else "Previous"
    type_label = dict(CAL_TYPES)[kind]
    title = esc(e["title"])
    if e.get("url") and kind != "earnings":
        title = f'<a class="cl__src" href="{esc(e["url"])}">{title}</a>'
    er = f' data-er="{market}"' if kind == "earnings" else ""
    return (f'<tr class="cl__row" data-type="{kind}" data-region="{esc(region_chip(e["country"]))}"{er} data-imp="{e["imp"]}">{times}'
            f'<th scope="row"><span class="cl__ev">{title}</span>{meta}</th>'
            f'<td class="cl__region">{esc(e["country"])}</td><td class="cl__type"><span class="tag">{type_label}</span></td>'
            f'<td class="cl__imp" data-imp="{e["imp"]}">{e["imp"]}</td>'
            f'<td class="cl__prior" data-label="{label}">{prev}</td>'
            f'<td class="cl__actual" data-label="Actual">{actual}</td></tr>')


def cal_table(days, sources, now, today, label="Calendar"):
    """Day groups (NY date -> events) as the calendar table."""
    bodies = ""
    for d in sorted(days):
        rows = "".join(cal_row(e, sources, now) for e in sorted(days[d], key=cal_sort))
        today_cls = " is-today" if d == today else ""
        head = f"Today, {cal_day_label(d)}" if d == today else cal_day_label(d)
        bodies += (f'<tbody class="cl__day-group{today_cls}" id="d-{d}" data-day="{d}" data-week="{week_of(d)}">'
                   f'<tr class="cl__day"><th scope="rowgroup" colspan="8" data-label="{cal_day_label(d)}">{head}</th></tr>{rows}</tbody>')
    return (f'<div class="cl-wrap"><table class="cl__table" aria-label="{label}"><thead><tr><th scope="col">New York</th>'
            f'<th scope="col">Madrid</th><th scope="col">Event</th><th scope="col">Region</th><th scope="col">Type</th>'
            f'<th scope="col">Importance</th><th scope="col">Previous</th><th scope="col">Actual</th></tr></thead>'
            f'{bodies}</table><p class="cl__empty" hidden>Nothing matches these filters this week.</p></div>')


def cal_days(events, start, end):
    days = {}
    for e in events:
        d = dt.date.fromisoformat(e["date"])
        if start <= d <= end:
            days.setdefault(d, []).append(e)
    return days


def cal_sources_section(cal):
    """Each source with the day of its copy; a failing source shows its last good copy."""
    status = cal.get("sources", {})
    used = {e["src"] for e in cal.get("events", {}).values()} | set(status)
    rows = []
    for key, meta in CAL_SOURCES.items():
        if key not in used:
            continue
        st = status.get(CAL_CITED.get(key, key), {})
        ok = st.get("ok")
        when = day_med(dt.date.fromisoformat(ok[:10])) if ok else None
        if st.get("error"):
            note = f"Last good copy {when}" if when else "Not available yet"
        else:
            note = when or "Not available yet"
        rows.append(f'<li><a href="{esc(meta["url"])}">{esc(meta["name"])}</a><span>{note}</span></li>')
    for ind_src in sorted({v.get("source", "FRED") for v in cal.get("values", {}).values()}):
        vals = [v for v in cal["values"].values() if v.get("source", "FRED") == ind_src]
        oks = [v["ok"] for v in vals if v.get("ok")]
        failing = any(v.get("error") for v in vals)
        when = day_med(dt.date.fromisoformat(max(oks)[:10])) if oks else None
        note = (f"Last good figures {when}" if failing and when else "Not available yet" if not when else when)
        rows.append(f'<li><span class="cl__srcname">{esc(ind_src)}, figures</span><span>{note}</span></li>')
    for key in ("spy", "stoxx600"):  # the membership lists
        lst = cal.get(key) or {}
        when = day_med(dt.date.fromisoformat(lst["ok"][:10])) if lst.get("ok") else None
        note = ("Last good copy " + when if lst.get("error") and when else when or "Not available yet")
        rows.append(f'<li><a href="{esc(CAL_SOURCES[key]["url"])}">{esc(CAL_SOURCES[key]["name"])}</a><span>{note}</span></li>')
    return (f'<section class="cl__sources" aria-labelledby="cl-src"><h2 id="cl-src">Sources</h2>'
            f"<p>Every date and time comes from the publisher's own schedule, and every actual figure links to its "
            f"release. Previous is the last published figure; Actual is the first print, taken within a week of the "
            f"release. No consensus forecasts: no free source is reliable enough. When a source fails, its last good "
            f"copy stays, with its date.</p>"
            f"<p>Earnings are the next report of the 100 largest S&amp;P 500 companies (members from State Street's SPY "
            f"holdings), the 50 largest in the STOXX Europe 600 (members from iShares' holdings of its STOXX Europe 600 "
            f"ETF) and the 20 largest listed in Japan, Taiwan, South Korea, Hong Kong, mainland China and India, one "
            f"listing each, ranked by market cap in dollars. Market caps, dates and diluted EPS from Yahoo Finance; EPS "
            f"in the company's reporting currency, only when Yahoo has it. An estimated date is always marked as "
            f"estimated, and a report time Yahoo does not give, or gives exactly on the market close, is never guessed. "
            f"The report type is read from the periods the company publishes EPS for, and left out when unclear. First "
            f"session is the stock's close-to-close move on the first full session after the report (the next session "
            f"when the time is not given), with its benchmark's move that session: S&amp;P 500, STOXX Europe 600, "
            f"Nikkei 225, TAIEX, KOSPI, Hang Seng, CSI 300 or Nifty 50.</p>"
            f'<ul class="cl__srclist">{"".join(rows)}</ul>'
            f"<p>For information only. Not investment advice.</p></section>")


def cal_chips(group, values):
    return "".join(
        f'<button type="button" class="chip" data-{group}="{v}" aria-pressed="{"true" if i == 0 else "false"}">{label}</button>'
        for i, (v, label) in enumerate(values))


def cal_filters():
    return (f'<div class="cl__groups">'
            f'<div class="cl__group"><span class="cl__glabel" id="cl-g-type">Type</span>'
            f'<div class="filters" role="group" aria-labelledby="cl-g-type">{cal_chips("type", [("all", "All")] + CAL_TYPES)}</div></div>'
            f'<div class="cl__group"><span class="cl__glabel" id="cl-g-region">Region</span>'
            f'<div class="filters" role="group" aria-labelledby="cl-g-region">{cal_chips("region", [("all", "All")] + [(r, r) for r in CAL_REGIONS])}</div></div>'
            f'<div class="cl__group"><span class="cl__glabel" id="cl-g-er">Earnings</span>'
            f'<div class="filters" role="group" aria-labelledby="cl-g-er">{cal_chips("er", [("all", "All")] + CAL_MARKETS)}</div></div>'
            f'<div class="cl__group"><span class="cl__glabel" id="cl-g-imp">Importance</span>'
            f'<div class="filters" role="group" aria-labelledby="cl-g-imp">{cal_chips("imp", [("all", "All"), ("High", "High")])}</div></div>'
            f'</div><p class="filters__status cl__status" role="status" aria-live="polite"></p>')


def cal_updated(cal):
    if not cal.get("updated"):
        return "Official schedules. Not fetched yet."
    t = dt.datetime.fromisoformat(cal["updated"]).astimezone(NY)
    return f"Official schedules. Updated {day_med(t.date())}, {clock(t)} ET."


def calendar_page(cal, now):
    today = cal_today()
    first = week_of(today)
    weeks = [first + dt.timedelta(weeks=i) for i in range(CAL_WEEKS)]
    end = weeks[-1] + dt.timedelta(days=6)
    events = list(cal.get("events", {}).values())
    days = cal_days(events, first, end)
    tabs = "".join(
        f'<button type="button" class="chip" data-week="{w}" aria-pressed="{"true" if i == 0 else "false"}">'
        f'{"This week, " if i == 0 else "Next week, " if i == 1 else ""}{week_label(w)}</button>'
        for i, w in enumerate(weeks))
    body = f"""<main id="main" class="page cl">
  <div class="wrap">
    <header class="page__head cl__head">
      <h1 class="page__title">Calendar</h1>
      <p class="lede">Releases, central banks, market structure and the earnings of the largest companies in the US, Europe and Asia, five weeks ahead. Times in New York and Madrid.</p>
      <p class="note__meta">{cal_updated(cal)}</p>
    </header>
    <div class="cl__controls" hidden>
      <div class="filters cl__weeks" role="group" aria-label="Week">{tabs}</div>
      {cal_filters()}
    </div>
    {cal_table(days, CAL_SOURCES, now, today) if days else '<p class="cl__none">The calendar fills at the next deploy.</p>'}
    {cal_sources_section(cal)}
  </div>
</main>"""
    return shell(
        title="Calendar: Andra Markets",
        desc="Market-moving releases, central bank meetings, market structure and the earnings of the largest companies in the US, Europe and Asia, five weeks ahead, in New York and Madrid time.",
        body=body, home="../", base="../", path="calendar/", scripts=("calendar.js",))


def calendar_week(cal, monday, now, weeks):
    today = cal_today()
    events = list(cal.get("events", {}).values())
    days = cal_days(events, monday, monday + dt.timedelta(days=6))
    i = weeks.index(monday)
    pager = ""
    if i > 0:
        pager += f'<a class="link" href="../{weeks[i - 1]}/">Week of {day_med(weeks[i - 1])} {icon("arrow-right")}</a>'
    if i + 1 < len(weeks):
        pager += f'<a class="link" href="../{weeks[i + 1]}/">Week of {day_med(weeks[i + 1])} {icon("arrow-right")}</a>'
    pager += f'<a class="link" href="../../">The calendar, five weeks ahead {icon("arrow-right")}</a>'
    body = f"""<main id="main" class="page cl">
  <div class="wrap">
    <header class="page__head cl__head">
      <p class="dd__crumbs"><a href="../../">Calendar</a> <span aria-hidden="true">/</span> Week of {day_med(monday)}</p>
      <h1 class="page__title">Week of {monday.day} {monday:%b}</h1>
      <p class="lede">Every release and event of the week, with the figures as first published. Times in New York and Madrid.</p>
      <p class="note__meta">{cal_updated(cal)}</p>
    </header>
    <div class="cl__controls" hidden>{cal_filters()}</div>
    {cal_table(days, CAL_SOURCES, now, today, f"Week of {day_med(monday)}") if days else '<p class="cl__none">Nothing was recorded this week.</p>'}
    <nav class="report__pager" aria-label="More weeks">{pager}</nav>
    {cal_sources_section(cal)}
  </div>
</main>"""
    return shell(
        title=f"Calendar, week of {day_med(monday)}: Andra Markets",
        desc=f"Economic releases, central banks, market structure and earnings for the week of {day_long(monday)}, with the figures as first published.",
        body=body, home="../../../", base="../../../", path=f"calendar/week/{monday}/", scripts=("calendar.js",))


def calendar_weeks(cal):
    """Mondays from the calendar's first week to the last week the tabs show."""
    if not cal.get("first_week"):
        return []
    first = dt.date.fromisoformat(cal["first_week"])
    last = week_of(cal_today()) + dt.timedelta(weeks=CAL_WEEKS - 1)
    return [first + dt.timedelta(weeks=i) for i in range((last - first).days // 7 + 1)]


def calendar_home(cal, now):
    """This week's high-importance rows, from today on, for the homepage."""
    today = cal_today()
    events = [e for e in cal.get("events", {}).values() if e.get("imp") == "High"]
    start, end = today, week_of(today) + dt.timedelta(days=6)
    days = cal_days(events, start, end)
    if sum(len(v) for v in days.values()) < 3:  # late in the week: carry on into the next
        days = cal_days(events, start, end + dt.timedelta(days=7))
    keep, n = {}, 0
    for d in sorted(days):
        for e in sorted(days[d], key=cal_sort):
            if n < 10:
                keep.setdefault(d, []).append(e)
                n += 1
    return cal_table(keep, CAL_SOURCES, now, today, "This week's high-importance events") if keep else ""


def calendar_link(cal, d):
    """The archive page anchor for a session, from the calendar's first week on."""
    if not cal.get("first_week") or d < dt.date.fromisoformat(cal["first_week"]):
        return None
    return f"calendar/week/{week_of(d)}/#d-{d}"


# Company pages ----------------------------------------------------------------
# One page per company among the 50 largest in the S&P 500, from
# .cache/companies/companies.json (tools/company_data.py). Owner-approved
# design, 22 Oct 2026. assets/company.js draws the charts from the figures
# embedded in each page.

CO_DATA = ROOT / ".cache" / "companies" / "companies.json"
SHORT_SECTOR = {
    "Information Technology": "Technology", "Communication Services": "Communication",
    "Consumer Discretionary": "Consumer discretionary", "Consumer Staples": "Consumer staples",
    "Health Care": "Health care", "Real Estate": "Real estate",
}


def load_companies():
    try:
        data = json.loads(CO_DATA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    order = [t for t in data.get("order") or [] if t in (data.get("companies") or {})]
    if not order:
        return None
    return {"order": order, "co": data["companies"], "spx": data.get("spx") or []}


def co_slug(t):
    return t.lower()


# The names people use, for the companies in the list today; a company that
# joins later gets its Yahoo name with the legal suffix taken off.
CO_NAMES = {
    "NVDA": "Nvidia", "AAPL": "Apple", "MSFT": "Microsoft", "AMZN": "Amazon", "GOOGL": "Alphabet", "GOOG": "Alphabet",
    "AVGO": "Broadcom", "META": "Meta", "TSLA": "Tesla", "MU": "Micron", "LLY": "Eli Lilly", "BRK-B": "Berkshire Hathaway",
    "AMD": "AMD", "JPM": "JPMorgan Chase", "XOM": "Exxon Mobil", "V": "Visa", "JNJ": "Johnson & Johnson", "WMT": "Walmart",
    "MA": "Mastercard", "ABBV": "AbbVie", "PLTR": "Palantir", "INTC": "Intel", "CVX": "Chevron", "COST": "Costco",
    "CSCO": "Cisco", "UNH": "UnitedHealth", "MRK": "Merck", "PG": "Procter & Gamble", "KO": "Coca-Cola",
    "CAT": "Caterpillar", "BAC": "Bank of America", "LRCX": "Lam Research", "AMAT": "Applied Materials",
    "HD": "Home Depot", "PM": "Philip Morris", "GE": "GE Aerospace", "PANW": "Palo Alto Networks", "NFLX": "Netflix",
    "GS": "Goldman Sachs", "TXN": "Texas Instruments", "RTX": "RTX", "TMO": "Thermo Fisher", "WFC": "Wells Fargo",
    "GEV": "GE Vernova", "CRWD": "CrowdStrike", "AMGN": "Amgen", "IBM": "IBM", "LIN": "Linde", "MS": "Morgan Stanley",
    "ORCL": "Oracle", "MRVL": "Marvell", "KLAC": "KLA", "SNDK": "SanDisk", "CRM": "Salesforce", "ADI": "Analog Devices",
    "APH": "Amphenol", "DIS": "Disney", "ANET": "Arista Networks", "GILD": "Gilead", "QCOM": "Qualcomm", "PEP": "PepsiCo",
    "VZ": "Verizon", "COP": "ConocoPhillips", "MCD": "McDonald's", "ABT": "Abbott", "UNP": "Union Pacific",
    "AXP": "American Express", "PFE": "Pfizer", "WELL": "Welltower", "BLK": "BlackRock", "NEE": "NextEra Energy",
    "TJX": "TJX", "DE": "Deere", "NOW": "ServiceNow",
}


def co_name(rec):
    """Plain company name: 'Microsoft' for 'Microsoft Corporation'."""
    if rec.get("ticker") in CO_NAMES:
        return CO_NAMES[rec["ticker"]]
    n = html.unescape(rec["name"]).replace("&amp;", "&")
    n = re.sub(r"^The\s+", "", n)
    n = re.sub(r"\s*(&|and)\s*(Co\.?|Company)$", "", n)
    n = re.sub(r",?\s+(Inc\.?|Incorporated|Corporation|Corp\.?|Company|Co\.?|plc|N\.V\.|Ltd\.?|Holdings?|Platforms|Technologies)$", "", n)
    n = re.sub(r",?\s+(Inc\.?|Corporation|Corp\.?)$", "", n)
    return {"Alphabet": "Alphabet", "Berkshire Hathaway": "Berkshire Hathaway"}.get(n, n).strip()


def money(v, short=True):
    """$3.96tn, $331.8bn, $867m."""
    if v is None:
        return "n/a"
    a = abs(v)
    sign = MINUS if v < 0 else ""
    if a >= 1e12:
        return f"{sign}${a / 1e12:.2f}tn"
    if a >= 1e9:
        return f"{sign}${a / 1e9:,.1f}bn"
    return f"{sign}${a / 1e6:,.0f}m"


def pct1(v):
    """12.3%, -0.04 as 0.0%, negatives with a true minus."""
    r = round(v, 1)
    if r == 0:
        return "0.0%"
    return f"{MINUS if r < 0 else ''}{abs(r):.1f}%"


def usd_signed(v):
    return f"{MINUS if v < 0 else ''}${abs(v):,.2f}"


def fy_label(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d:%b} {d.year}"


def co_metrics(rec):
    a = rec["annual"]
    closes = rec["closes"]
    price, prev = closes[-1][1], closes[-2][1]
    rev, rev0 = a["TotalRevenue"]["fy"], a["TotalRevenue"]["prev"]
    op = a["OperatingIncome"]["fy"]
    shares = rec.get("shares")
    mcap = price * shares if shares else None
    if mcap is not None and mcap < 1e10:  # a share count in another class (Berkshire)
        mcap = None
    eps = rec.get("ttm_eps")
    debt, cash, eq = rec.get("debt"), rec.get("cash"), rec.get("equity")
    return {
        "price": price, "prev": prev, "date": closes[-1][0],
        "chg": price - prev, "chg_pct": (price / prev - 1) * 100,
        "mcap": mcap,
        "pe": price / eps if eps and eps > 0 else None,
        "rev": rev, "revg": (rev / rev0 - 1) * 100 if rev and rev0 else None,
        "om": op / rev * 100 if op is not None and rev else None,
        "fcf": a["FreeCashFlow"]["fy"], "capex": a["CapitalExpenditure"]["fy"],
        "net_debt": (debt or 0) - (cash or 0) if debt is not None or cash is not None else None,
        "debt": debt, "cash": cash,
        "de": debt / eq * 100 if debt is not None and eq and eq > 0 else None,
        "dy": rec["div_ttm"] / price * 100 if rec.get("div_ttm") else 0.0,
        "ni": a["NetIncomeCommonStockholders"]["fy"], "ni0": a["NetIncomeCommonStockholders"]["prev"],
    }


def co_flow(rec):
    """Revenue down to net income for the last fiscal year, in $bn: steps that reconcile."""
    a = {k: v["fy"] for k, v in rec["annual"].items()}
    rev = a["TotalRevenue"]
    if not rev:
        return None
    bn = lambda v: round(v / 1e9, 2)  # noqa: E731
    small = abs(rev) * 0.005
    steps = [["Revenue", bn(rev), "total"]]
    base = rev
    cogs, gross = a["CostOfRevenue"], a["GrossProfit"]
    if cogs and gross:
        steps += [["Cost of revenue", -bn(cogs)], ["Gross profit", bn(gross), "total", "Gross margin"]]
        base = gross
    op = a["OperatingIncome"]
    pre, tax, ni = a["PretaxIncome"], a["TaxProvision"], a["NetIncomeCommonStockholders"]
    if op is not None:
        rd, sga = a["ResearchAndDevelopment"] or 0, a["SellingGeneralAndAdministration"] or 0
        if rd:
            steps.append(["Research", -bn(rd)])
        if sga:
            steps.append(["Sales and admin", -bn(sga)])
        other = base - rd - sga - op
        if abs(other) > small:
            steps.append(["Other operating costs" if other > 0 else "Other operating income", bn(-other)])
        steps.append(["Operating profit", bn(op), "total", "Operating margin"])
        base = op
    if pre is None:
        return steps if len(steps) > 1 else None
    if op is None:
        steps.append(["Costs and provisions" if base > pre else "Other income", bn(pre - base)])
    elif abs(pre - base) > small:
        steps.append(["Other income" if pre > base else "Other expense", bn(pre - base)])
    steps.append(["Pre-tax profit", bn(pre), "total"])
    if ni is None:
        return steps
    if tax:
        steps.append(["Tax", -bn(tax)])
    rest = pre - (tax or 0) - ni
    if abs(rest) > small:
        steps.append(["Minorities and other", bn(-rest)])
    steps.append(["Net income", bn(ni), "total", "Net margin"])
    return steps


def co_peer_row(t, rec):
    m = co_metrics(rec)
    r = lambda v, d=2: None if v is None else round(v, d)  # noqa: E731
    return {"t": t, "n": co_name(rec), "pe": r(m["pe"], 1), "g": r(m["revg"], 1), "om": r(m["om"], 1),
            "de": r(m["de"], 0), "dy": r(m["dy"], 2)}


def co_cagr(rec):
    """Free cash flow growth a year over the last three fiscal years, when all are positive."""
    h = [v for _, v in rec.get("fcf_hist") or []]
    if len(h) >= 4 and h[-4] > 0 and h[-1] > 0:
        return ((h[-1] / h[-4]) ** (1 / 3) - 1) * 100, len(h)
    return None, None


def co_earnings(cal, t):
    out = []
    for e in (cal.get("events") or {}).values():
        if e.get("kind") == "earnings" and e.get("ticker") == t and e["date"] >= cal_today().isoformat():
            out.append(e)
    return sorted(out, key=lambda e: e["date"])[:1]


def co_ahead(cal, t, base):
    rows = []
    for e in co_earnings(cal, t):
        d = dt.date.fromisoformat(e["date"])
        when = {"before": "before the open", "after": "after the close"}.get(e.get("timing"), "")
        bits = []
        if e.get("status") == "estimated":
            bits.append("Date estimated, not yet confirmed by the company")
        elif when:
            bits.append(f"Reports {when}")
        if e.get("previous"):
            bits.append(f"a year earlier: {esc(e['previous'])}" + (f", {esc(e['prev_period'])}" if e.get("prev_period") else ""))
        link = calendar_link(cal, d)
        title = "Quarterly results"
        if link:
            title = f'<a class="link" href="{base}{link}">Quarterly results</a>'
        rows.append(f'<li><time datetime="{d}">{day_med(d)}</time><div><b>{title}</b>'
                    f'<span>{"; ".join(bits).capitalize() if bits else ""}</span></div></li>')
    if not rows:
        return '<p>No results date in the calendar yet. It appears here once the company or Yahoo Finance posts one.</p>'
    return f'<ul class="co-cal">{"".join(rows)}</ul><p class="co-src">From the Andra Markets calendar, Yahoo Finance.</p>'


def kpi(name, level, note):
    return (f'<li class="kpi__item"><span class="kpi__name">{name}</span><span class="kpi__level">{level}</span>'
            f'<span class="kpi__chg">{note}</span></li>')


def company_page(t, data, cal):
    rec = data["co"][t]
    m = co_metrics(rec)
    name = co_name(rec)
    sector = rec["sector"]
    d = dt.date.fromisoformat(m["date"])
    fy = fy_label(rec["fy"])
    base = "../../"
    peers_all = [x for x in data["order"] if data["co"][x]["sector"] == sector]
    if len(peers_all) >= 4:
        peers = peers_all
        peers_lede = (f"{name} (filled) against the other {len(peers) - 1} {SHORT_SECTOR.get(sector, sector).lower()} "
                      f"companies among the 50 largest in the S&amp;P 500. Tap or hover a dot to read it.")
    else:
        peers = data["order"]
        peers_lede = (f"{name} (filled) against the 50 largest companies in the S&amp;P 500; too few in its sector "
                      f"to compare on their own. Tap or hover a dot to read it.")
    flow = co_flow(rec)
    cagr, _ = co_cagr(rec)
    can_dcf = rec.get("dcf") and m["fcf"] and m["fcf"] > 0 and rec.get("shares") and m["mcap"]
    payload = {
        "t": t, "name": name, "price": m["price"], "date": m["date"],
        "peers": [co_peer_row(x, data["co"][x]) for x in peers],
        "flow": flow, "fy": fy,
        "dcf": {"fcf": round(m["fcf"] / 1e9, 3), "net_debt": round((m["net_debt"] or 0) / 1e9, 3),
                "shares": round(rec["shares"] / 1e9, 4), "cagr": None if cagr is None else round(cagr, 1)} if can_dcf else None,
        "hist": [[dd, c] for dd, c in rec["closes"]],
        "spx": [[dd, c] for dd, c in data["spx"]],
    }
    json_payload = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")

    chg = f'{"+" if m["chg"] >= 0 else MINUS}${abs(m["chg"]):,.2f} ({signed(m["chg_pct"], 2, "%")})'
    lede = f"{SHORT_SECTOR.get(sector, sector)}{(', ' + esc(rec['industry'])) if rec.get('industry') else ''}. Revenue of {money(m['rev'])} in the year to {fy}"
    if m["revg"] is not None:
        lede += f", {'up' if m['revg'] >= 0 else 'down'} {abs(m['revg']):.1f}%"
    if m["om"] is not None:
        lede += f", with an operating margin of {pct1(m['om'])}"
    lede += "."

    kp = [
        kpi("Market value", money(m["mcap"]), f'{rec["shares"] / 1e9:.2f}bn shares' if m["mcap"] else "Not shown: share classes"),
        kpi("P/E, last 12 months", f'{m["pe"]:.1f}x' if m["pe"] else "n/a",
            f'EPS {usd_signed(rec["ttm_eps"])}' if rec.get("ttm_eps") is not None else "No EPS yet"),
        kpi("Revenue growth", signed(m["revg"], 1, "%") if m["revg"] is not None else "n/a", f"Year to {fy}"),
        kpi("Operating margin", pct1(m["om"]) if m["om"] is not None else "n/a", f"Year to {fy}" if m["om"] is not None else "Not reported for banks"),
    ]
    if rec.get("dcf"):
        kp += [
            kpi("Free cash flow", money(m["fcf"]), f"After {money(abs(m['capex']))} capex" if m["capex"] else f"Year to {fy}"),
            kpi("Net debt" if (m["net_debt"] or 0) >= 0 else "Net cash", money(abs(m["net_debt"])) if m["net_debt"] is not None else "n/a",
                f"{money(m['debt'])} debt, {money(m['cash'])} cash" if m["debt"] is not None else ""),
        ]
    else:
        # A lender's cash flow and debt are its customers' money: show earnings and book value instead.
        eq = rec.get("equity")
        kp += [
            kpi("Net income", money(m["ni"]), f"Year to {fy}"),
            kpi("Shareholders' equity", money(eq), f"Price to book {m['mcap'] / eq:.1f}x" if m["mcap"] and eq and eq > 0 else "Book value"),
        ]
    kp += [
        kpi("Dividend yield", f'{m["dy"]:.2f}%' if m["dy"] else "None", f'${rec["div_ttm"]:.2f} a share, last 12 months' if m["dy"] else "No dividend in the last year"),
        kpi("52-week range", f'${rec["low52"]:,.0f}&ndash;{rec["high52"]:,.0f}' if rec.get("low52") else "n/a", f"Close ${m['price']:,.2f}"),
    ]

    if can_dcf:
        val = f"""<p>A ten-year discounted cash flow model on the last reported free cash flow. Every assumption is on the page: move it and the value follows.</p>
        <div class="co-model">
          <div class="co-ctls">
            <div class="co-ctl"><label for="co-g">Cash flow growth, years 1 to 5 <output id="co-g-o"></output></label><input id="co-g" type="range" min="-5" max="35" step="0.5" value="10"></div>
            <div class="co-ctl"><label for="co-r">Discount rate <output id="co-r-o"></output></label><input id="co-r" type="range" min="6" max="13" step="0.25" value="9"></div>
            <div class="co-ctl"><label for="co-tg">Growth after year 10 <output id="co-tg-o"></output></label><input id="co-tg" type="range" min="0" max="4.5" step="0.25" value="3"></div>
            <button class="co-reset" type="button" id="co-reset">Reset assumptions</button>
          </div>
          <div class="co-verdict">
            <div class="co-v"><span class="co-v__n">Value per share on these assumptions</span><span class="co-v__v" id="co-fv"></span><span class="co-v__c" id="co-fv-c"></span></div>
            <div class="co-v"><span class="co-v__n">Growth the price implies</span><span class="co-v__v" id="co-ig"></span><span class="co-v__c" id="co-ig-c"></span></div>
          </div>
        </div>
        <div class="co-chart" id="co-val"></div>
        <p class="co-src">Base: free cash flow of {money(m["fcf"])} in the year to {fy}, {"net debt" if (m["net_debt"] or 0) >= 0 else "net cash"} of {money(abs(m["net_debt"] or 0))}, {rec["shares"] / 1e9:.2f}bn shares. Growth fades in a straight line from year 6 to year 10. An Andra Markets model, not a recommendation.</p>"""
    elif not rec.get("dcf"):
        val = ("<p>Not modelled on cash flow. A bank's, insurer's or asset manager's cash flows are mostly its customers' "
               "money, so a free cash flow model says little about its value. Its P/E and dividend sit in the peer "
               "comparison above.</p>")
    else:
        val = (f"<p>Not modelled yet: free cash flow was {money(m['fcf'])} in the year to {fy}, and a cash flow model "
               "needs a positive starting point to mean anything.</p>")

    flow_sec = ('<div class="co-chart" id="co-flow"></div>'
                '<p class="key"><span><i class="sw-down"></i>Costs and tax</span>'
                '<span><i class="sw-up"></i>Income</span>'
                '<span><i class="sw-ink"></i>Totals</span></p>'
                f'<p class="co-src">Annual report for the year to {fy}, via Yahoo Finance. Steps under 0.5% of revenue are folded into the next total.</p>'
                if flow else "<p>Data pending.</p>")

    spx_note = "" if data["spx"] else " The S&amp;P 500 series is pending."
    body = f"""<main id="main" class="page dd co" data-co>
  <div class="wrap dd__grid">
    <header class="page__head dd__head">
      <p class="dd__crumbs"><a href="../">Companies</a> <span aria-hidden="true">/</span> {SHORT_SECTOR.get(sector, sector)}</p>
      <h1 class="page__title">{esc(name)}</h1>
      <p class="co-quote"><span class="co-px">${m["price"]:,.2f}</span><span class="co-chg">{chg} on the day</span><span class="note__meta">{t}, {esc(rec.get("exchange") or "")}. Close {day_med(d)}.</span></p>
      <p class="lede">{lede}</p>
      <div class="co-acts">
        <button class="btn" type="button" data-soon="The portfolio monitor is coming soon: you will be able to follow {esc(name)} and your other holdings here.">Add to portfolio monitor</button>
        <button class="btn btn--ghost" type="button" data-soon="Alerts are coming soon: you will get an email before and after {esc(name)}'s results.">Alert me on results</button>
        <p class="co-acts__status" role="status" aria-live="polite"></p>
      </div>
    </header>
    <aside class="report__side dd__side" aria-labelledby="side-title">
      <h2 class="report__side-title" id="side-title">Key figures</h2>
      <ul class="kpi">{"".join(kp)}</ul>
      <p class="report__src">Yahoo Finance: annual report for the year to {fy}, balance sheet at {fy_label(rec["bs_date"]) if rec.get("bs_date") else fy}, close of {day_med(d)}.</p>
    </aside>
    <div class="page__body co__body dd__main">
      <section aria-labelledby="co-peers-t">
        <h2 id="co-peers-t">Against its peers</h2>
        <p>{peers_lede}</p>
        <div class="co-chart" id="co-peers"></div>
        <p class="co-read" id="co-peers-read" aria-live="polite"></p>
        <p class="co-src">Yahoo Finance, {day_med(d)}. P/E on the last four quarters' diluted EPS; revenue growth and operating margin for each company's last fiscal year; debt to equity at the last balance sheet; dividend yield on the last 12 months' dividends.</p>
      </section>
      <section aria-labelledby="co-val-t">
        <h2 id="co-val-t">Valuation</h2>
        {val}
      </section>
      <section aria-labelledby="co-flow-t">
        <h2 id="co-flow-t">From revenue to profit</h2>
        <p>Where revenue went in the year to {fy}, in billions of dollars and as a share of revenue.</p>
        {flow_sec}
      </section>
      <section aria-labelledby="co-ctx-t">
        <h2 id="co-ctx-t">Against the market</h2>
        <p>{esc(name)} and the S&amp;P 500 over the past year, both rebased to 100.{spx_note}</p>
        <div class="co-chart" id="co-ctx"></div>
        <p class="key"><span><i class="k-solid"></i>{esc(name)}</span><span><i class="k-dash"></i>S&amp;P 500</span></p>
        <p class="co-read" id="co-ctx-read" aria-live="polite"></p>
        <p class="co-src">Yahoo Finance, daily closes to {day_med(d)}.</p>
      </section>
      <section aria-labelledby="co-memo-t">
        <h2 id="co-memo-t">Investment memo</h2>
        <div class="co-gate">
          <p>Coming with the Andra Markets subscription: a full memo on {esc(name)}, written for professionals.</p>
          <ul>
            <li>The thesis and what would change it</li>
            <li>Segment by segment, with the model's full workings</li>
            <li>Three scenarios with their assumptions</li>
            <li>What to watch at the next results</li>
          </ul>
          <button class="btn" type="button" data-soon="Subscriptions open soon. Get the free close note by email in the meantime, from the home page.">Subscribe for the memo</button>
          <p class="co-gate__status" role="status" aria-live="polite"></p>
        </div>
      </section>
      <section aria-labelledby="co-ahead-t">
        <h2 id="co-ahead-t">Ahead</h2>
        {co_ahead(cal, t, base)}
      </section>
      <p class="co-legal">For information only. Not investment advice.</p>
    </div>
  </div>
  <script type="application/json" id="co-data">{json_payload}</script>
</main>"""
    return shell(
        title=f"{esc(name)} ({t}): Andra Markets",
        desc=esc(f"{name}: valuation, peers, revenue to profit and the share price against the market. {html.unescape(lede)}"),
        body=body, home=base, base=base, path=f"companies/{co_slug(t)}/", scripts=("company.js",),
    )


def companies_index(data):
    sectors = {}
    for t in data["order"]:
        sectors.setdefault(data["co"][t]["sector"], []).append(t)
    order = sorted(sectors, key=lambda s: (-len(sectors[s]), s))
    chips = (f'<button type="button" class="chip" data-cofilter="all" aria-pressed="true">All <span class="chip__n">{len(data["order"])}</span></button>'
             + "".join(f'<button type="button" class="chip" data-cofilter="{slug_s(s)}" aria-pressed="false">{SHORT_SECTOR.get(s, s)} '
                       f'<span class="chip__n">{len(sectors[s])}</span></button>' for s in order))
    rows = []
    last = None
    for i, t in enumerate(data["order"], 1):
        rec = data["co"][t]
        m = co_metrics(rec)
        last = max(last or m["date"], m["date"])
        pe_txt = f'{m["pe"]:.1f}x' if m["pe"] else "n/a"
        rows.append(
            f'<tr data-sector="{slug_s(rec["sector"])}"><td class="co-tab__rank">{i}</td>'
            f'<td class="co-tab__name"><a href="{co_slug(t)}/">{esc(co_name(rec))}</a><span>{t}</span></td>'
            f'<td class="co-tab__sec" data-label="Sector">{SHORT_SECTOR.get(rec["sector"], rec["sector"])}</td>'
            f'<td class="num" data-label="Close">${m["price"]:,.2f}</td>'
            f'<td class="num" data-label="Day">{signed(m["chg_pct"], 2, "%")}</td>'
            f'<td class="num" data-label="Value">{money(m["mcap"])}</td>'
            f'<td class="num" data-label="P/E">{pe_txt}</td></tr>')
    body = f"""<main id="main" class="page co-index">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Companies</h1>
      <p class="lede">The 50 largest companies in the S&amp;P 500, by their weight in the index. Each has a page with its valuation, its peers, where its revenue goes and how the shares have done against the market.</p>
    </header>
    <div class="filters" role="group" aria-label="Filter companies by sector">{chips}</div>
    <p class="filters__status co-index__status" role="status" aria-live="polite">Showing all {len(data["order"])} companies</p>
    <div class="co-tab__wrap">
      <table class="co-tab">
        <thead><tr><th scope="col"><span class="visually-hidden">Rank</span></th><th scope="col">Company</th><th scope="col">Sector</th><th scope="col" class="num">Close</th><th scope="col" class="num">Day</th><th scope="col" class="num">Market value</th><th scope="col" class="num">P/E</th></tr></thead>
        <tbody>{"".join(rows)}</tbody>
      </table>
    </div>
    <p class="co-src">Members and ranking: State Street SPY holdings. Prices and figures: Yahoo Finance, close of {day_med(dt.date.fromisoformat(last))}. P/E on the last four quarters' diluted EPS.</p>
  </div>
</main>"""
    return shell(title="Companies: Andra Markets",
                 desc="The 50 largest companies in the S&amp;P 500, each with valuation, peers and results.",
                 body=body, home="../", base="../", path="companies/")


def slug_s(s):
    return re.sub(r"[^a-z]+", "-", s.lower()).strip("-")


# Search index for the header palette (site.js loads it on first open). A .js
# file, not .json: the deploy refuses JSON files on the published site.
SEARCH_TERMS = {
    "yield_curve": "Treasury yields 2Y 10Y 30Y inversion",
    "fed_path": "FOMC policy rate cuts hikes",
    "sector_heatmap": "S&P 500 sectors ETFs",
    "vol_term": "VIX implied volatility",
    "global_indices": "Europe Asia Euro Stoxx DAX Nikkei",
    "fx_majors": "dollar DXY EUR/USD USD/JPY currencies",
    "commodities": "oil gold WTI Brent",
    "credit_spreads": "high yield investment grade",
    "inflation_labour": "CPI payrolls jobs inflation",
    "breadth": "advancers decliners",
    "correlation": "stocks bonds dollar",
}

SEARCH_PAGES = [
    ("Dashboards", "#dashboards", "Home"),
    ("The Lab", "#lab", "Home"),
    ("Companies", "companies/", "Page"),
    ("Economic calendar", "calendar/", "Page"),
    ("Daily close note", "#note", "Home"),
    ("Learn", "#learn", "Home"),
    ("Watch", "#watch", "Home"),
    ("Subscribe", "#subscribe", "Home"),
    ("About", "#about", "Home"),
    ("All close notes", "reports/", "Archive"),
    ("Methodology", "methodology/", "Page"),
]


def search_index(notes, companies=None):
    items = []
    for t in (companies or {}).get("order", []):
        rec = companies["co"][t]
        items.append({"g": "Companies", "t": co_name(rec), "m": t, "u": f"companies/{co_slug(t)}/",
                      "k": f"{t} {html.unescape(rec['name'])} {rec['sector']} {rec.get('industry') or ''}"})
    for key, cat, name, desc, source in DASHBOARDS:
        items.append({"g": "Dashboards", "t": html.unescape(name), "m": "Dashboard",
                      "u": f"dashboards/{DASH_PAGES[key][0]}/",
                      "k": " ".join([html.unescape(desc), source, SEARCH_TERMS.get(key, "")])})
    for rec in notes:
        d = rec["day"]
        items.append({"g": "Close notes", "t": rec["note"]["headline"], "m": day_med(d),
                      "u": f"reports/{rec['date']}/", "k": f"{day_long(d)} {day_med(d)} {d.day} {d:%b}"})
    for title, url, meta in SEARCH_PAGES:
        items.append({"g": "Pages", "t": title, "m": meta, "u": url, "k": ""})
    payload = json.dumps(items, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return "// Generated by tools/build_site.py. Do not edit.\nwindow.ANDRA_SEARCH=" + payload + ";\n"


def main():
    notes = load_notes()
    cal = load_calendar()
    now = dt.datetime.now(dt.timezone.utc)
    companies = load_companies()
    (OUT / "assets" / "search-index.js").write_text(search_index(notes, companies), encoding="utf-8")
    (OUT / "index.html").write_text(page(notes, cal))
    (OUT / "methodology").mkdir(exist_ok=True)
    (OUT / "methodology" / "index.html").write_text(methodology())
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "index.html").write_text(archive(notes))
    for i, rec in enumerate(notes):
        newer = notes[i - 1] if i > 0 else None
        older = notes[i + 1] if i + 1 < len(notes) else None
        (REPORTS / rec["date"]).mkdir(exist_ok=True)
        (REPORTS / rec["date"] / "index.html").write_text(report(rec, newer, older, cal))
    (OUT / "calendar").mkdir(exist_ok=True)
    (OUT / "calendar" / "index.html").write_text(calendar_page(cal, now))
    weeks = calendar_weeks(cal)
    for monday in weeks:
        folder = OUT / "calendar" / "week" / monday.isoformat()
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(calendar_week(cal, monday, now, weeks))
    dash_data = load_dash_data()
    for key, cat, name, desc, source in DASHBOARDS:
        folder = OUT / "dashboards" / DASH_PAGES[key][0]
        folder.mkdir(parents=True, exist_ok=True)
        rec = dash_data.get(key)
        # A record cached before the pages existed has no history yet: pending until refetched.
        (folder / "index.html").write_text(dashboard_page(key, cat, name, desc, source, rec if rec and rec.get("detail") else None))
    if companies:
        (OUT / "companies").mkdir(exist_ok=True)
        (OUT / "companies" / "index.html").write_text(companies_index(companies))
        for t in companies["order"]:
            folder = OUT / "companies" / co_slug(t)
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "index.html").write_text(company_page(t, companies, cal))
        print(f"wrote {len(companies['order'])} company pages")
    print(f"wrote index.html, methodology/index.html, reports/index.html, {len(DASHBOARDS)} dashboard pages, "
          f"{len(notes)} report page(s) and the calendar with {len(weeks)} week page(s)")


if __name__ == "__main__":
    main()
