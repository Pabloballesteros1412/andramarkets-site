#!/usr/bin/env python3
"""Build the Andra Markets site.

Light (default) and dark themes, switched by a header toggle and remembered
per visitor. Writes:

    index.html                 the homepage
    methodology/index.html     methodology (placeholder page)
    reports/index.html         every published close note
    reports/<date>/index.html  one page per close note, rendered from its text
    research/                  the Research Library: weekly reviews and research (data/reports)
    research/pdf/<slug>.pdf    each report's PDF, copied from data/reports/pdf
    interview-prep/            Markets Interview Prep (data/interview_prep.json)
    sources/, legal/, privacy/ data sources, legal notice, privacy and cookies
    dashboards/<slug>/         one page per dashboard (assets/dashboard.js draws the chart)
    calendar/                  the calendar, five weeks (assets/calendar.js: tabs and filters)
    calendar/week/<monday>/    one page per week since the calendar started

    python3 tools/build_site.py

Close notes come from data/notes/*.json, written by tools/import_notes.py.
With none published, the home page keeps its placeholders. The tape shows the
latest note's closing levels. No note PDF or facts file is ever linked: the
site is free, and those downloads are reserved for paid subscribers later. The
Research Library is the exception: its reports are published as their PDFs.

Dashboard tiles draw real figures from .cache/dashboards/tiles.json, written
at deploy time by tools/dashboard_data.py, with their source and date; a tile
without a record shows its source and "Data pending". Lab charts are schematic
shapes, not market data, and labelled "Illustrative". The calendar reads
.cache/calendar/calendar.json, written by tools/calendar_data.py. Follow DESIGN.md.
"""
import datetime as dt
import html
import json
import math
import os
import random
import re
import shutil
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nyse  # noqa: E402
from calendar_data import MOVES as CAL_MOVES, SOURCES as CAL_SOURCES  # noqa: E402
from legal_content import LEGAL, LEGAL_UPDATED, PRIVACY, PRIVACY_UPDATED  # noqa: E402
from world_data import AXES as WORLD_AXES, MARKETS as WORLD_MARKETS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT
ICONS = ROOT / "assets" / "icons"

# Andra Markets social channels: the footer links to each one with a URL.
# Plain links only: no player or feed is embedded (owner, 30 Oct 2026: the
# Watch section and its TikTok embeds were removed so no third-party cookies
# are set).
LINKEDIN_URL = "https://www.linkedin.com/company/andramarkets/"
TIKTOK_URL = "https://www.tiktok.com/@andramarkets"
YOUTUBE_URL = ""  # No channel yet. Set the URL to bring back the footer link and icon.

SOCIALS = [
    ("LinkedIn", LINKEDIN_URL, "linkedin-logo"),
    ("TikTok", TIKTOK_URL, "tiktok-logo"),
    ("YouTube", YOUTUBE_URL, "youtube-logo"),
]

# Absolute site address, no trailing slash, e.g. "https://andramarkets.com".
# Social cards need it for og:image and canonical links. Left empty until the
# site has its own domain, so no account name is baked into the pages.
SITE_URL = ""

# The profile API (worker/, a Cloudflare Worker) that the company pages call for live
# prices, fundamentals and news, with no trailing slash. The address is public
# (every visitor's browser calls it); the vendors' keys live in the Worker,
# never here. The repository variable PROFILE_API overrides it at deploy time.
PROFILE_API = (os.environ.get("PROFILE_API", "").strip()
               or "https://andra-profile-api.pabloballesteros141.workers.dev").rstrip("/")


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


def c_bond(w=640, h=260):
    # Price of a 10-year 4% annual bond against its yield (solid) and the
    # straight line duration predicts (dashed): convexity in one picture.
    def price(y):
        return sum(4 / (1 + y) ** t for t in range(1, 11)) + 100 / (1 + y) ** 10
    ys = [i / 99 * 0.10 for i in range(100)]
    p0, mod = price(0.04), 8.11 / 1.04
    curve = [price(y) for y in ys]
    line = [p0 * (1 - mod * (y - 0.04)) for y in ys]
    pa, pb = fit([curve, line], w, h, 12, lo=55, hi=145)
    return svg(w, h, grid_lines(w, h, 4) + f'<path class="dash" d="{d(pb)}"/><path class="line" d="{d(pa)}"/>', "Bond price against yield, with the duration line")


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
    "sector_heatmap": r_sector_heatmap,
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

ICON_NAMES = ["warning-circle", "arrow-right", "arrow-up-right", "list", "x", "sun", "moon",
              "magnifying-glass", "check", "link", "lock-simple", "pause", "play"] + [
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
        for lb, v, o in zip(det["labels"], det["values"], cmp["values"]):
            rows.append((f"VIX {lb}", f"{v:.2f}", mv(f"{signed(v - o, 2)} since {short_day(cmp['date'])}")))
        return rows
    if det["kind"] == "perf":
        r = det["ranges"]["1D"]
        rows = sorted(zip(det["names"], r["values"], r["to"]), key=lambda x: -x[1])
        return [(esc(n), mv(chg(v)), "on the day" if t == asof else f"close of {short_day(t)}") for n, v, t in rows]
    if det["kind"] == "lines":
        out = []
        # The series shown when the page opens; the others are toggles.
        for sr in [x for x in det["series"] if x.get("on", True)]:
            v = sr["values"]
            dec = sr.get("dec", det.get("dec", 2))
            if det.get("rebase"):
                out.append((sr["name"], f"{v[-1]:,.{dec}f}", mv(f"{chg((v[-1] / v[-2] - 1) * 100)} on the day")))
                yr = det["dates"].index(next(x for x in det["dates"] if x >= months_back_iso(det["dates"][-1], 12)))
                out.append((f"{sr['name']}, 1 year", mv(chg((v[-1] / v[yr] - 1) * 100)), f"since {short_day(det['dates'][yr])}"))
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


# Each dashboard page's views: (id, label), the first is the tile's own. A view
# is offered only when the record carries its figures (see view_ok).
PERF_VIEWS = [("main", "Ranked"), ("rebased", "Rebased")]
CURVE_VIEWS = [("main", "Curve"), ("change", "Change"), ("time", "Over time")]
DASH_VIEWS = {
    "sector_heatmap": PERF_VIEWS, "global_indices": PERF_VIEWS, "fx_majors": PERF_VIEWS,
    "vol_term": CURVE_VIEWS,
    "commodities": [("main", "Rebased"), ("ranked", "Ranked")],
    "credit_spreads": [("main", "Levels"), ("change", "Change")],
    "inflation_labour": [("main", "Inflation and jobs"), ("unrate", "Unemployment")],
    "breadth": [("main", "Net"), ("cum", "Cumulative")],
    "correlation": [("main", "Matrix"), ("rolling", "Rolling")],
}
# What the comparison date does on each kind of chart.
DATE_LABEL = {"curve": "Compare with", "matrix": "Window ending"}


def view_ok(det, v):
    if v in ("rebased", "time"):
        return bool(det.get("hist"))
    if v == "spreads":
        return bool(det.get("spreads"))
    if v == "unrate":
        return any(x is not None for x in det.get("unrate") or [])
    return True


def dash_dates(det):
    """First and last date the comparison date can take."""
    if det.get("hist"):
        ds = det["hist"]["dates"]
    elif det["kind"] == "breadth":
        ds = [x[0] for x in det["sessions"]]
    else:
        ds = det.get("dates") or []
    return (ds[0], ds[-1]) if ds else (None, None)


# What each page adds beyond its tile: (how to read the extra views, extra sources).
DASH_MORE = {
    "sector_heatmap": ("Pick a date to measure every sector from that close, and switch sectors on or off; the S&amp;P 500 "
                       "itself (SPY) is there to compare. Rebased draws up to six sectors from 100 on the range's first "
                       "day, so the paths can be compared, not only the end points.", " SPDR S&amp;P 500 ETF (SPY) for comparison."),
    "vol_term": ("Pick a date to compare the curve with any session in the last two years. Change shows how far each "
                 "expiry has moved since then, in volatility points. Over time follows chosen expiries, and adds the "
                 "one-day VIX, the VVIX (the volatility of the VIX itself) and the VIX less the 3-month VIX: above zero, "
                 "the curve is in backwardation.", " Cboe VIX1D and VVIX from Yahoo Finance in the Over time view."),
    "global_indices": ("Twelve more benchmarks can be switched on: Nasdaq 100, Russell 2000, CAC 40, IBEX 35, FTSE MIB, SMI, "
                       "KOSPI, TAIEX, Nifty 50, S&amp;P/ASX 200, Shanghai Composite and IPC Mexico. Pick a date to measure "
                       "from that close; Rebased draws up to six from 100.", " The added indices from Yahoo Finance, in local currency."),
    "fx_majors": ("Ten more can be switched on: the New Zealand dollar, Swedish krona, Norwegian krone, Chinese yuan, "
                  "Mexican peso, Indian rupee, Brazilian real, Korean won, South African rand and the dollar index (DXY). "
                  "Pick a date to measure from that close; Rebased draws the dollar against up to six currencies from 100, "
                  "so a rising line is a stronger dollar.", " The added pairs and the ICE US Dollar Index from Yahoo Finance."),
    "commodities": ("Seven more futures can be switched on: Brent crude, natural gas, silver, copper, platinum, corn and "
                    "wheat, up to six lines at once. Pick a date to rebase from that day. Ranked shows every future's "
                    "change over the range, largest gain first.",
                    " Brent (BZ), natural gas (NG), silver (SI), copper (HG), platinum (PL), corn (ZC) and wheat (ZW) "
                    "front-month futures from Yahoo Finance; a session one of them skipped carries its last close."),
    "credit_spreads": ("Five more spreads can be switched on: BBB and BB, CCC and lower, euro high yield and emerging-market "
                       "corporates. Change shows how far each has moved since the range's start or a date you pick, in "
                       "basis points.", " ICE BofA BBB (BAMLC0A4CBBB), BB (BAMLH0A1HYBB), CCC and lower (BAMLH0A3HYC), "
                       "euro high yield (BAMLHE00EHYIOAS) and emerging markets corporate (BAMLEMCBPIOAS) spreads, served by FRED."),
    "inflation_labour": ("Core CPI, PCE prices and core PCE prices (the Fed's preferred gauge) can be drawn beside headline "
                         "CPI. Pick a month to start from. The Unemployment view draws the unemployment rate, the other half "
                         "of the labour picture.", " Core CPI (CPILFESL), PCE and core PCE price indexes from the Bureau of "
                         "Economic Analysis (PCEPI, PCEPILFE) and the unemployment rate (UNRATE), served by FRED."),
    "breadth": ("Cumulative adds up advancers less decliners from the range's start or a date you pick: the "
                "advance-decline line. A line that falls while the index rises means fewer stocks carry the gains.", ""),
    "correlation": ("Six more assets can be switched on: Nasdaq 100, Euro Stoxx 50, high yield bonds (HYG), the euro, copper "
                    "and bitcoin. Pick a date to see the window that ended then. Rolling follows the first asset switched on "
                    "against each of the others, over a trailing window the length of the range.",
                    " Nasdaq 100, Euro Stoxx 50, iShares iBoxx High Yield (HYG), EUR/USD, copper futures and bitcoin from "
                    "Yahoo Finance; returns on the sessions every chosen asset traded."),
}


def dashboard_page(key, cat, name, desc, source, rec):
    slug, default, how, long_source = DASH_PAGES[key]
    cat_label = {k: label for k, label, _ in CATEGORIES}[cat]
    crumbs = f'<p class="dd__crumbs"><a href="../../#dashboards">Dashboards</a> <span aria-hidden="true">/</span> {cat_label}</p>'
    # A record cached before the pages carried histories draws as pending until refetched.
    if rec and rec["detail"]["kind"] in ("perf", "matrix", "curve") and not rec["detail"].get("hist"):
        rec = None
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
        views = [v for v in DASH_VIEWS.get(key, [("main", "")]) if view_ok(det, v[0])]
        view_chips = "".join(f'<button type="button" class="chip" data-view="{v}" aria-pressed="{"true" if i == 0 else "false"}">{lb}</button>'
                             for i, (v, lb) in enumerate(views))
        lo, hi = dash_dates(det)
        date_label = DATE_LABEL.get(det["kind"], "From")
        controls = (f'<div class="dd__ctl">'
                    + (f'<div class="dd__cgroup"><span class="cl__glabel" id="dd-view-l">View</span>'
                       f'<div class="filters dd__views" role="group" aria-labelledby="dd-view-l">{view_chips}</div></div>' if len(views) > 1 else "")
                    + f'<div class="dd__cgroup"><span class="cl__glabel" id="dd-range-l">Range</span>'
                      f'<div class="dd__rangerow"><div class="filters dd__ranges" role="group" aria-labelledby="dd-range-l">{chips}</div>'
                    + (f'<div class="dd__date"><label for="dd-from">{date_label}</label>'
                       f'<input id="dd-from" type="date" min="{lo}" max="{hi}"></div>' if lo else "")
                    + '</div></div>'
                    + '<div class="dd__cgroup dd__show" hidden><span class="cl__glabel" id="dd-show-l">Show</span>'
                      '<div class="dd__toggles" role="group" aria-labelledby="dd-show-l"></div></div>'
                    + '<p class="dd__status" role="status" aria-live="polite"></p></div>')
        figure = (controls
                  + f'<figure class="dd__chart"><div class="dd__plot" role="img" tabindex="0" aria-label="{esc(name)}"></div>'
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
    extra_how, more_src = DASH_MORE.get(key, ("", ""))
    more_how = f"<p>{extra_how}</p>" if rec and extra_how else ""
    if not rec:
        more_src = ""
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
      <section aria-labelledby="dd-how"><h2 id="dd-how">How to read it</h2><p>{how}</p>{more_how}</section>
      <section aria-labelledby="dd-src"><h2 id="dd-src">Source</h2><p>{long_source}{more_src}</p><p>For information only. Not investment advice.</p></section>
    </div>
  </div>
</main>"""
    return shell(
        title=f"{name}: Andra Markets dashboard",
        # The tile line alone runs 40 to 60 characters: too short for a search or share snippet.
        desc=esc(f"{html.unescape(desc)} Interactive chart with time ranges and the latest figures, "
                 f"from {html.unescape(source)}. By Andra Markets."),
        body=body,
        home="../../",
        base="../../",
        path=f"dashboards/{slug}/",
        scripts=scripts,
    )


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


# Market strip ------------------------------------------------------------------
# The tape between deploys: .cache/strip/strip.json, written by
# tools/strip_data.py every 15 minutes while the NYSE is open and once after
# the European and Asian closes. Shown in place of the latest note's closes
# when it is newer than that note's close; each figure carries its own time.

STRIP_DATA = ROOT / ".cache" / "strip" / "strip.json"


def strip_when(it):
    """"2:45 pm ET" for a market still trading, "Close, 22 Oct" once it has shut."""
    if it.get("state") == "open" and it.get("time"):
        return f'{clock(dt.datetime.fromisoformat(it["time"]).astimezone(NY))} ET'
    return f'Close, {short_day(it["day"])}'


def load_strip(latest):
    """(tape items, title, source line) from the strip, or None to use the note."""
    try:
        strip = json.loads(STRIP_DATA.read_text(encoding="utf-8"))
        updated = dt.datetime.fromisoformat(strip["updated"]).astimezone(NY)
        items = strip["items"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if latest:
        close_h = 13 if nyse.close_time(latest["day"]) == "1:00 pm" else 16
        if updated <= dt.datetime.combine(latest["day"], dt.time(close_h), NY):
            return None  # the note's closes are newer
    closes = (latest or {}).get("closes") or {}
    rows, srcs = [], set()
    for label, key, dec in TAPE:
        it = items.get(key)
        if it and finite(it.get("last")) and finite(it.get("chg")):
            last, chg = it["last"], it["chg"]
            when = strip_when(it)
            srcs.add(it.get("src", "Yahoo Finance"))
        elif latest and finite((closes.get(key) or {}).get("last")):
            # Never fetched yet: the note's close, dated.
            last, chg = closes[key]["last"], (closes[key].get("chg") if finite(closes[key].get("chg")) else None)
            when = f'Close, {short_day(latest["date"])}'
        else:
            rows.append((label, "n/a", "", ""))
            continue
        if key in RATES:
            level = f"{last:.{dec}f}%"
            change = signed(chg, 0, "bp") if chg is not None else "n/a"
        else:
            level = f"{last:,.{dec}f}"
            change = signed(chg, 2, "%") if chg is not None else "n/a"
        rows.append((label, level, change, when))
    tape = "".join(
        f'<li class="tape__item"><span class="tape__name">{n}</span>'
        f'<span class="tape__level">{level}</span><span class="tape__chg {move_class(change)}">{change}</span>'
        f'<span class="tape__when">{when}</span></li>'
        for n, level, change, when in rows)
    title = f'Markets {day_med(updated.date())}, as of {clock(updated)} ET'
    ten = items.get("ust10y") or {}
    ten_src = ("FRED for the US 10Y yield" if ten.get("src") == "FRED"
               else "the CBOE 10-year yield index for the US 10Y yield" if ten else "")
    src = ("Last price and change on the previous close, each with its time or close date. Sources: Yahoo Finance"
           + (f", {ten_src}" if ten_src else "") + ". Futures and FX may be delayed.")
    return tape, title, src


def finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


# Page ------------------------------------------------------------------------

THEME_BOOT = (
    "(function(){var t='light';try{var q=new URLSearchParams(location.search).get('theme');"
    "if(q==='light'||q==='dark'){t=q;localStorage.setItem('andra-theme',q)}"
    "else{var s=localStorage.getItem('andra-theme');if(s==='light'||s==='dark')t=s}}catch(e){}"
    "document.documentElement.setAttribute('data-theme',t);"
    "var m=document.querySelector('meta[name=theme-color]');if(m)m.content=t==='dark'?'#0a0c0d':'#ffffff'})();"
)


def page(notes, cal):
    latest = notes[0] if notes else None
    strip = load_strip(latest)
    if strip:
        tape, tape_title, tape_src = strip
    elif latest:
        d = latest["day"]
        items, any_stale = tape_items(latest)
        tape = "".join(
            f'<li class="tape__item"><span class="tape__name">{n}</span>'
            f'<span class="tape__level">{level}</span><span class="tape__chg {move_class(change)}">{change}</span></li>'
            for n, level, change in items
        )
        tape_title = f'Markets {day_med(d)}, {nyse.close_time(d)} ET'
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
        tape_src = f'Last and daily change. Source {ph("[data vendor]")}'
    if latest:
        # Always the newest published note, whatever the strip shows.
        tape_note = (f'<a class="tape__note" href="reports/{latest["date"]}/"><span>Latest close note, {day_med(latest["day"])}: '
                     f'{esc(latest["note"]["headline"])}</span>{icon("arrow-right")}</a>')
    else:
        tape_note = (f'<a class="tape__note" href="#note"><span>Latest close note, {ph("[date]")}: '
                     f'<span class="ph ph--ink">[headline]</span></span>{icon("arrow-right")}</a>')
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
    return shell(
        title="Andra Markets: markets research platform",
        desc="Andra Markets is a markets research platform: dashboards, quant tools, an economic calendar, a daily close note, research and a guide to breaking into Wall Street.",
        body=f"""<main id="main">
  <section class="hero" id="top" aria-labelledby="hero-title">
    <div class="hero__stage">
      <span class="hero__sentinel" aria-hidden="true"></span>
      <div class="hero__art" aria-hidden="true">
        <img class="horse" src="assets/andra-horse.png" alt="" width="1024" height="1024" fetchpriority="high">
      </div>
      <canvas class="hero__canvas" data-src="assets/horse-particles.png?v={ver("horse-particles.png")}" aria-hidden="true"></canvas>
      <p class="hero__stamp" aria-hidden="true">Illustrative, not market data</p>
      <div class="wrap hero__copy">
        <h1 id="hero-title" style="--i:0">Markets, on&nbsp;the&nbsp;record.</h1>
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

{sim_home()}
  <section class="section lab" id="lab" aria-labelledby="lab-title">
    <div class="wrap">
      <div class="section-head">
        <h2 class="section-title reveal" id="lab-title">Lab</h2>
        <p class="lede reveal">Interactive quant tools. Change the inputs, watch the result move.</p>
      </div>
      <div class="lab-grid">
        <a class="tool tool--wide reveal" href="lab/options-payoff/">
          <div class="draw">{c_payoff()}</div>
          <p class="key"><span><i class="k-solid"></i>Value today</span><span><i class="k-dash"></i>Payoff at expiry</span><span class="key__note">Illustrative</span></p>
          <div class="tool__text">
            <h3>Options payoff diagram</h3>
            <p>Pick a strategy, from a single call to a straddle, and see its profit or loss at expiry and today across prices of the underlying.</p>
            <p class="tool__params">Ten strategies. Strikes, volatility, days to expiry and rate are yours to set.</p>
            <p class="tool__src">Black-Scholes model, calculated in your browser</p>
          </div>
          <span class="link">Open the diagram {icon("arrow-up-right")}</span>
        </a>
        <a class="tool reveal" href="lab/bond-calculator/" style="--i:1">
          <div class="draw">{c_bond()}</div>
          <p class="key"><span><i class="k-solid"></i>Price</span><span><i class="k-dash"></i>Duration estimate</span><span class="key__note">Illustrative</span></p>
          <div class="tool__text">
            <h3>Bond price and duration</h3>
            <p>Price a bond from its yield and see how far the price moves when the yield does.</p>
            <p class="tool__src">Discounted cash flows, calculated in your browser</p>
          </div>
          <span class="link">Open the calculator {icon("arrow-up-right")}</span>
        </a>
        <div class="tool tool--next reveal" style="--i:2">
          <h3>Also in the Lab</h3>
          <p>Eight more tools: risk and correlation across the companies in the earnings calendar, a Black-Scholes pricer with the Greeks, yield to maturity, a two-asset efficient frontier, discounted cash flow, position sizing and value at risk, real return after inflation, and compound growth.</p>
          <a class="link" href="lab/risk-correlation/">Risk and correlation {icon("arrow-right")}</a>
          <a class="link" href="lab/black-scholes/">Black-Scholes pricer {icon("arrow-right")}</a>
          <a class="link" href="lab/">All Lab tools {icon("arrow-right")}</a>
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
</main>""",
        home="",
        base="",
        scripts=("hero-horse.js",),
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
      <a href="{base}fed-rates/">Fed &amp; Rates</a>
      <a href="{base}companies/">Companies</a>
      <a href="{base}lab/">Lab</a>
      <a href="{base}simulators/">Simulators</a>
      <a href="{base}calendar/">Calendar</a>
      <a href="{base}world/">World</a>
      <a href="{base}fx/">FX</a>
      <a href="{base}research/">Research</a>
      <a href="{home}#note">Daily note</a>
      <a href="{base}interview-prep/">Interview prep</a>
      <a href="{base}break-into-wall-street/">Break into Wall Street</a>
    </nav>
    <button class="search-btn" type="button" aria-haspopup="dialog" aria-label="Search Andra Markets" hidden>
      <svg class="icon" aria-hidden="true"><use href="#i-magnifying-glass"/></svg><span>Search</span><kbd>⌘K</kbd>
    </button>
    <button class="theme-btn" type="button" aria-label="Switch to dark theme">
      <svg class="icon icon--sun" aria-hidden="true"><use href="#i-sun"/></svg>
      <svg class="icon icon--moon" aria-hidden="true"><use href="#i-moon"/></svg>
    </button>
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
      <a href="{base}fed-rates/">Fed &amp; Rates</a>
      <a href="{base}companies/">Companies</a>
      <a href="{base}lab/">Lab</a>
      <a href="{base}simulators/">Simulators</a>
      <a href="{base}calendar/">Calendar</a>
      <a href="{base}world/">World markets</a>
      <a href="{base}fx/">FX</a>
      <a href="{base}research/">Research Library</a>
      <a href="{base}reports/">All notes</a>
      <a href="{home}#note">Daily note</a>
      <a href="{base}interview-prep/">Interview prep</a>
      <a href="{base}break-into-wall-street/">Break into Wall Street</a>
      <a href="{home}#about">About</a>
      <a href="{base}methodology/">Methodology</a>
      <a href="{base}sources/">Data sources</a>
      <a href="{base}legal/">Legal notice</a>
      <a href="{base}privacy/">Privacy and cookies</a>
    </nav>
    <ul class="foot__social" aria-label="Andra Markets on social media">
{social_links}
    </ul>
    <div class="foot__legal">
      <span>&copy; {ph("[year]")} Andra Markets</span>
      <span><a href="{base}legal/">For information only. Not investment advice.</a></span>
    </div>
  </div>
</footer>"""


def ver(name):
    """A short hash of an asset, so browsers fetch it again whenever it changes."""
    import hashlib
    return hashlib.sha1((ROOT / "assets" / name).read_bytes()).hexdigest()[:10]


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
<meta name="theme-color" content="#ffffff">
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
<link rel="stylesheet" href="{base}assets/site.css?v={ver("site.css")}">
</head>
<body data-base="{base}">
{sprite()}
<a class="skip" href="#main">Skip to content</a>

{site_header(home, base)}

{body}

{site_footer(home, base)}

<script src="{base}assets/site.js?v={ver("site.js")}" defer></script>{"".join(f'<script src="{base}assets/{js}?v={ver(js)}" defer></script>' for js in scripts)}
</body>
</html>
"""


def watch_redirect():
    """/watch/ was removed (owner, 30 Oct 2026): send old links to the home page."""
    body = (f'<main id="main" class="page"><div class="wrap"><header class="page__head"><h1 class="page__title">Andra Markets</h1>'
            f'<p class="lede">Videos are no longer on this site. Go to the <a class="link" href="../">home page</a>.</p></header></div></main>'
            f'<script>location.replace("../");</script>')
    return shell(title="Andra Markets", desc="Videos are no longer on this site.",
                 body=body, home="../", base="../", path="watch/")


# Lab tools: (slug, data-tool, title, description, how it works, assumptions).
# Calculated by assets/lab.js in the browser: nothing leaves it.
LAB_TOOLS = [
    ("options-payoff", "options", "Options payoff diagram",
     "Pick a strategy and see its profit or loss at expiry, and today, across prices of the underlying.",
     "Each option is priced with the Black-Scholes model from the spot price, strike, volatility, days to expiry and "
     "interest rate you set. The dashed line is the profit or loss per share at expiry: the payoff of every leg less the "
     "net premium. The solid line is the profit or loss if the underlying moved to that price today, valued with the same "
     "model. Where the dashed line sits above zero the strategy gains (green tint); below, it loses (red tint). Dots mark "
     "the break-even prices.",
     "European options on a stock that pays no dividend, one share per leg, no fees or taxes, constant volatility and "
     "interest rate. Real premiums differ: market prices carry each strike's own implied volatility. For learning, not "
     "for pricing trades."),
    ("bond-calculator", "bond", "Bond price and duration",
     "Price a fixed-coupon bond from its yield, and see how much the price moves when the yield does.",
     "The price is the value of every coupon and the final repayment, each discounted at the yield to maturity. Macaulay "
     "duration is the average time to those cash flows, weighted by their value; modified duration turns it into the "
     "percentage change in price for a one-point change in yield; convexity measures how that sensitivity itself changes. "
     "DV01 is the price change for one basis point. The solid line is the price at each yield, the dashed line what "
     "duration alone predicts: the gap between them is convexity.",
     "A plain bullet bond priced on a coupon date (no accrued interest), coupons paid annually or semi-annually, the same "
     "yield for every cash flow, no default. Maturity is rounded to whole coupon periods."),
    ("compound-growth", "growth", "Compound growth",
     "See how a starting sum and a monthly addition grow at a steady annual return.",
     "The annual return is converted to its monthly equivalent and applied every month, with the monthly addition made at "
     "the end of each month. The solid line is the value at the end of each year; the dashed line and the shaded area are "
     "what was paid in, so the gap between them is growth on growth. Doubling time is how long the starting sum alone "
     "takes to double at that return.",
     "A constant return every year, which no real investment delivers; no fees, taxes or inflation. Figures are in "
     "whatever currency you think in. An illustration of compounding, not a forecast."),
    ("risk-correlation", "risk", "Risk and correlation",
     "Pick companies from the calendar's earnings universe and see how they move together, how volatile each is, and how "
     "risky they are as one portfolio.",
     "Daily returns are the change in each company's dividend-adjusted close, as log returns, over the window you choose. "
     "Correlation measures how closely two companies' daily returns move together, from +1 (in step) to \u22121 (opposite "
     "ways); it is measured on the sessions every company you picked traded. Volatility is the standard deviation of a "
     "company's daily returns over its own sessions, annualised by the square root of 252 trading days. Beta is the "
     "company's return sensitivity to its benchmark (the S&amp;P 500 for the US, the STOXX Europe 600 for Europe, each Asian "
     "market's main index): a beta of 1.2 means it has moved 1.2% for each 1% of the index, on average. The portfolio's "
     "volatility combines each company's volatility, its weight and every correlation: it sits below the weighted average "
     "of the volatilities unless every pair moves in perfect step, and the gap is the diversification benefit.",
     "Past returns over the window, which say nothing certain about the next one. Correlations between markets in different "
     "time zones are understated, because their sessions close hours apart: Tokyo's close cannot react to New York's "
     "afternoon until the next day. Prices in each company's own currency, so currency moves are not included. Weights are "
     "held constant (rebalanced daily). Mainland Chinese companies are measured against the Shanghai Composite, because "
     "Yahoo Finance keeps no history for the CSI 300."),
    ("black-scholes", "bs", "Black-Scholes pricer",
     "Price a European call or put and read its Greeks: how its value moves with the price, time, volatility and rates.",
     "The Black-Scholes model values the option as the expected payoff at expiry under a lognormal price, discounted at the "
     "interest rate, with the dividend yield taken off the drift. Delta is the change in the option's value for a 1 move in "
     "the underlying; gamma the change in delta for that move; vega the change in value for 1 point of volatility; theta the "
     "change in value as one calendar day passes; rho the change for 1 point of interest rate. The chart shows the chosen "
     "measure across prices of the underlying, today (solid) and, for the value, at expiry (dashed).",
     "European exercise only, a constant volatility and interest rate, a continuous dividend yield, no fees or taxes, and "
     "prices that move without jumps. Listed options trade on each strike's own implied volatility, so market prices differ. "
     "For learning, not for pricing trades."),
    ("yield-to-maturity", "ytm", "Yield to maturity",
     "Solve for the yield a bond pays from its price, coupon and maturity.",
     "The yield to maturity is the single discount rate that makes the value of every remaining coupon and the final "
     "repayment equal to the price you enter. There is no formula for it, so the tool solves for it numerically (bisection to "
     "a millionth of a percent). Current yield is the annual coupon over the price, ignoring the pull to par. The effective "
     "annual yield compounds the per-period rate over a year. The chart shows the price at each yield, with your price "
     "marked on the curve.",
     "Priced on a coupon date (no accrued interest), coupons paid on schedule and the face value repaid in full, every cash "
     "flow discounted at the same rate. Maturity is rounded to whole coupon periods. A yield assumes coupons can be "
     "reinvested at that same yield, which rarely holds exactly."),
    ("efficient-frontier", "frontier", "Two-asset efficient frontier",
     "Mix two assets and see every combination of risk and return, the lowest-risk mix and the best mix for each unit of "
     "risk.",
     "Each point on the curve is one mix of the two assets, from all in the first to all in the second. The mix's expected "
     "return is the weighted average of the two returns; its volatility depends on both volatilities and the correlation "
     "between them, so with a correlation below 1 some mixes carry less risk than either asset alone. The minimum-variance "
     "mix is the lowest point of risk. The tangency mix has the highest Sharpe ratio: the most return above the risk-free "
     "rate for each point of volatility. The dashed line from the risk-free rate through it is the capital market line.",
     "Expected returns, volatilities and the correlation are your inputs and are held constant, which real markets do not "
     "do. No borrowing or short selling: weights run from 0% to 100%. Returns are treated as normally distributed. A "
     "teaching model of diversification, not an allocation."),
    ("dcf", "dcf", "Discounted cash flow",
     "Value a business from the cash it is expected to generate, and see how much of the value lies beyond ten years.",
     "Free cash flow grows at your first rate for years 1 to 5 and at your second rate for years 6 to 10. Each year's flow "
     "is discounted to today at the discount rate. After year 10 the flows are assumed to grow forever at the terminal "
     "rate, valued with the Gordon growth formula and discounted from year 10. The sum is the enterprise value; taking off "
     "net debt gives the equity value, and dividing by the shares gives a value per share. The solid line is each year's "
     "cash flow, the dashed line and the shaded area its value today.",
     "The terminal growth rate must be below the discount rate, and small changes in either move the value a lot: try "
     "them. Cash flows arrive at each year end. No dilution, tax changes or reinvestment needs beyond what the free cash flow "
     "already nets out. A sketch of the method, not a valuation of any company."),
    ("position-sizing", "var", "Position size and value at risk",
     "Size a position from the amount you are willing to lose, and see how much it could lose on a bad day.",
     "The position is sized so that a fall from the entry to the stop loses the share of the account you set: shares are "
     "the money at risk divided by the distance to the stop. Value at risk (VaR) is the loss the position should exceed only "
     "on the worst days at the confidence you choose (5% of days at 95%), from its annual volatility scaled to the holding "
     "period by the square root of time. Expected shortfall is the average loss on those worst days. The chart shows both "
     "across holding periods, with the loss at the stop as the reference line.",
     "Parametric VaR assumes normally distributed returns with no drift; real returns have fatter tails, so large losses "
     "are more frequent than the model says. A stop is not guaranteed: prices can gap through it. Whole shares only, no "
     "fees or slippage. For learning, not for managing a portfolio."),
    ("real-return", "real", "Real return after inflation",
     "See what a return is worth once inflation, and tax if you set one, have taken their share.",
     "The real return is the nominal return deflated by inflation: (1 + nominal) / (1 + inflation) \u2212 1, which is "
     "slightly less than the simple difference. Tax, if set, is taken from each year's gain before inflation. The solid line "
     "is the value in money of the day; the dashed line the same value in today's money, which is what it can buy. "
     "Purchasing power lost is how much of the nominal end value inflation has eaten.",
     "Constant return, inflation and tax rate every year, tax paid yearly on the gain, no fees. Figures are in whatever "
     "currency you think in. An illustration, not a forecast."),
]


def lab_field(fid, label, value, lo, hi, step, unit):
    return (f'<div class="lt-field"><label for="{fid}">{label}<span class="lt-unit">{unit}</span></label>'
            f'<input id="{fid}" type="number" inputmode="decimal" value="{value}" min="{lo}" max="{hi}" step="{step}"></div>')


def lab_chips(group, label, options, default):
    chips = "".join(f'<button type="button" class="chip" data-value="{v}" aria-pressed="{"true" if v == default else "false"}"'
                    f'{" data-default" if v == default else ""}>{t}</button>' for v, t in options)
    return (f'<div class="lt-group"><span class="cl__glabel" id="lt-g-{group}">{label}</span>'
            f'<div class="filters lt-chips" role="group" data-group="{group}" aria-labelledby="lt-g-{group}">{chips}</div></div>')


def lab_inputs(kind):
    if kind == "bond":
        return (lab_chips("freq", "Coupons", [("2", "Semi-annual"), ("1", "Annual")], "2")
                + '<div class="lt-fields">'
                + lab_field("b-face", "Face value", 100, 1, 1000000, 1, "")
                + lab_field("b-cpn", "Coupon rate", 4, 0, 20, 0.125, "% a year")
                + lab_field("b-yld", "Yield to maturity", 4.5, 0, 25, 0.05, "% a year")
                + lab_field("b-yrs", "Years to maturity", 10, 0.5, 50, 0.5, "years")
                + "</div>")
    if kind == "options":
        strategies = [("long-call", "Long call"), ("long-put", "Long put"), ("short-call", "Short call"),
                      ("short-put", "Short put"), ("bull-call", "Bull call spread"), ("bear-put", "Bear put spread"),
                      ("straddle", "Straddle"), ("strangle", "Strangle"), ("covered-call", "Covered call"),
                      ("protective-put", "Protective put")]
        return (lab_chips("strategy", "Strategy", strategies, "long-call")
                + '<div class="lt-fields">'
                + lab_field("o-spot", "Underlying price", 100, 1, 100000, 1, "")
                + lab_field("o-k1", "Strike", 100, 1, 100000, 1, "lower for spreads")
                + lab_field("o-k2", "Higher strike", 110, 1, 100000, 1, "")
                + lab_field("o-vol", "Volatility", 20, 1, 200, 1, "% a year")
                + lab_field("o-days", "Days to expiry", 30, 1, 1095, 1, "days")
                + lab_field("o-rate", "Interest rate", 4, 0, 20, 0.25, "% a year")
                + "</div>")
    if kind == "bs":
        return (lab_chips("type", "Option", [("call", "Call"), ("put", "Put")], "call")
                + lab_chips("view", "Chart", [("value", "Value"), ("delta", "Delta"), ("gamma", "Gamma"), ("vega", "Vega"),
                                              ("theta", "Theta")], "value")
                + '<div class="lt-fields">'
                + lab_field("p-spot", "Underlying price", 100, 0.01, 1000000, 1, "")
                + lab_field("p-k", "Strike", 100, 0.01, 1000000, 1, "")
                + lab_field("p-vol", "Volatility", 20, 1, 300, 1, "% a year")
                + lab_field("p-days", "Days to expiry", 90, 1, 3650, 1, "days")
                + lab_field("p-rate", "Interest rate", 4, -2, 25, 0.25, "% a year")
                + lab_field("p-div", "Dividend yield", 0, 0, 20, 0.25, "% a year")
                + "</div>")
    if kind == "ytm":
        return (lab_chips("freq", "Coupons", [("2", "Semi-annual"), ("1", "Annual")], "2")
                + '<div class="lt-fields">'
                + lab_field("y-price", "Price", 96, 1, 300, 0.01, "per 100 face")
                + lab_field("y-cpn", "Coupon rate", 4, 0, 20, 0.125, "% a year")
                + lab_field("y-yrs", "Years to maturity", 10, 0.5, 50, 0.5, "years")
                + "</div>")
    if kind == "frontier":
        return ('<div class="lt-fields">'
                + lab_field("f-ra", "Asset A return", 8, -20, 40, 0.1, "% a year")
                + lab_field("f-va", "Asset A volatility", 18, 0.1, 100, 0.1, "% a year")
                + lab_field("f-rb", "Asset B return", 4, -20, 40, 0.1, "% a year")
                + lab_field("f-vb", "Asset B volatility", 6, 0.1, 100, 0.1, "% a year")
                + lab_field("f-rho", "Correlation", -0.2, -1, 1, 0.05, "\u22121 to +1")
                + lab_field("f-rf", "Risk-free rate", 3, -2, 20, 0.1, "% a year")
                + "</div>")
    if kind == "dcf":
        return ('<div class="lt-fields">'
                + lab_field("d-fcf", "Free cash flow, last year", 100, 0.01, 1e9, 1, "millions")
                + lab_field("d-g1", "Growth, years 1 to 5", 8, -30, 60, 0.5, "% a year")
                + lab_field("d-g2", "Growth, years 6 to 10", 4, -30, 40, 0.5, "% a year")
                + lab_field("d-gt", "Growth after year 10", 2.5, -5, 6, 0.1, "% a year")
                + lab_field("d-r", "Discount rate", 9, 1, 30, 0.1, "% a year")
                + lab_field("d-debt", "Net debt", 200, -1e9, 1e9, 1, "millions, cash negative")
                + lab_field("d-sh", "Shares outstanding", 50, 0.001, 1e6, 0.1, "millions")
                + "</div>")
    if kind == "var":
        return (lab_chips("conf", "Confidence", [("95", "95%"), ("99", "99%")], "95")
                + '<div class="lt-fields">'
                + lab_field("v-acct", "Account size", 100000, 100, 1e10, 100, "")
                + lab_field("v-risk", "Risk per trade", 1, 0.05, 25, 0.05, "% of the account")
                + lab_field("v-entry", "Entry price", 50, 0.01, 1e6, 0.01, "")
                + lab_field("v-stop", "Stop price", 46, 0.01, 1e6, 0.01, "below the entry")
                + lab_field("v-vol", "Volatility", 30, 1, 300, 1, "% a year")
                + lab_field("v-days", "Holding period", 1, 1, 250, 1, "trading days")
                + "</div>")
    if kind == "real":
        return ('<div class="lt-fields">'
                + lab_field("r-start", "Starting sum", 10000, 0, 1e10, 100, "")
                + lab_field("r-nom", "Nominal return", 6, -20, 40, 0.1, "% a year")
                + lab_field("r-inf", "Inflation", 3, -5, 50, 0.1, "% a year")
                + lab_field("r-tax", "Tax on gains", 0, 0, 60, 1, "% of each year's gain")
                + lab_field("r-yrs", "Years", 20, 1, 60, 1, "years")
                + "</div>")
    return ('<div class="lt-fields">'
            + lab_field("g-start", "Starting sum", 10000, 0, 100000000, 100, "")
            + lab_field("g-add", "Added each month", 200, 0, 1000000, 10, "")
            + lab_field("g-rate", "Annual return", 5, -20, 30, 0.1, "% a year")
            + lab_field("g-yrs", "Years", 30, 1, 60, 1, "years")
            + "</div>")


LAB_CLOSES = ROOT / ".cache" / "lab" / "closes.json"
RISK_MARKETS = [("us", "US"), ("europe", "Europe"), ("asia", "Asia")]


def risk_data():
    """The risk tool's company list, and its daily returns written to one
    assets/lab-risk-<market>.js per market (loaded only when a company from that
    market is picked; a .js file because the deploy refuses JSON). Returns are
    log returns in basis points on a shared weekday axis, empty where a market
    did not trade. None until the calendar universe and the closes exist."""
    from lab_data import bench_of
    try:
        universe = json.loads(CAL_DATA.read_text(encoding="utf-8")).get("universe") or {}
        closes = json.loads(LAB_CLOSES.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    usable = {s for s, v in closes.items() if len(v.get("closes") or []) >= 60}
    last = max((v["closes"][-1][0] for s, v in closes.items() if s in usable), default=None)
    if not last:
        return None
    end = dt.date.fromisoformat(last)
    start = end - dt.timedelta(days=365 * 3 + 21)
    start -= dt.timedelta(days=start.weekday())
    axis, d = [], start
    while d <= end:
        if d.weekday() < 5:
            axis.append(d.isoformat())
        d += dt.timedelta(days=1)

    def encode(sym):
        by, prev, out = dict(closes[sym]["closes"]), None, []
        for day in axis:
            c = by.get(day)
            if c is None:
                out.append("")
                continue
            out.append("" if prev is None else str(round(math.log(c / prev) * 1e4)))
            prev = c
        return ",".join(out).rstrip(",")

    companies, files = [], {}
    for market, label in RISK_MARKETS:
        series = {}
        for c in universe.get(market) or []:
            b, bname = bench_of(c)
            if c["symbol"] not in usable or b not in usable:
                continue
            for sym in (c["symbol"], b):
                if sym not in series:
                    series[sym] = encode(sym)
            companies.append({"s": c["symbol"], "n": c["name"], "c": c["country"], "m": market, "b": b, "bn": bname})
        if series:
            name = f"lab-risk-{market}.js"
            payload = json.dumps({"start": axis[0], "series": series}, separators=(",", ":"))
            (OUT / "assets" / name).write_text(
                f"// Generated by tools/build_site.py. Do not edit.\n(window.ANDRA_RISK=window.ANDRA_RISK||{{}})"
                f"[{json.dumps(market)}]={payload};\n", encoding="utf-8")
            files[market] = f"{name}?v={ver(name)}"
    if len(companies) < 2:
        return None
    return {"companies": companies, "files": files, "asof": last}


def risk_inputs(data):
    wins = [("3M", "3M"), ("6M", "6M"), ("1Y", "1Y"), ("3Y", "3Y")]
    return (lab_chips("win", "Window", wins, "1Y")
            + lab_chips("weights", "Weights", [("equal", "Equal"), ("custom", "Custom")], "equal")
            + '<div class="lt-pick"><label for="r-find">Add a company<span class="lt-unit">two to ten, from '
            f'{len(data["companies"])} in the earnings calendar</span></label>'
            '<input id="r-find" type="search" autocomplete="off" spellcheck="false" placeholder="Name or ticker" '
            'role="combobox" aria-expanded="false" aria-controls="r-opts" aria-autocomplete="list">'
            '<ul class="lt-opts" id="r-opts" role="listbox" aria-label="Matching companies" hidden></ul></div>'
            '<ul class="lt-picked" aria-label="Companies picked"></ul>')


LAB_KEYS = {"options": [("k-solid", "Profit or loss today"), ("k-dash", "At expiry"), ("sw-up", "Gain"), ("sw-down", "Loss")],
            "bond": [("k-solid", "Price"), ("k-dash", "Duration estimate")],
            "growth": [("k-solid", "Value"), ("k-dash", "Paid in")],
            "risk": [("sw-up", "Move together"), ("sw-down", "Move apart")],
            "bs": [("k-solid", "Today"), ("k-dash", "At expiry")],
            "ytm": [("k-solid", "Price at each yield")],
            "frontier": [("k-solid", "Mixes of A and B"), ("k-dash", "Capital market line")],
            "dcf": [("k-solid", "Free cash flow"), ("k-dash", "Value today")],
            "var": [("k-solid", "Value at risk"), ("k-dash", "Expected shortfall"), ("k-ref", "Loss at the stop")],
            "real": [("k-solid", "Value, money of the day"), ("k-dash", "Value, today's money")]}


def lab_page(i, risk=None):
    slug, kind, title, desc, how, limits = LAB_TOOLS[i]
    key = "".join(f'<span><i class="{c}"></i>{t}</span>' for c, t in LAB_KEYS[kind])
    if kind == "risk":
        return risk_page(i, risk, key)
    others = "".join(f'<a class="link" href="../{t[0]}/">{t[2]} {icon("arrow-right")}</a>' for j, t in enumerate(LAB_TOOLS) if j != i)
    body = f"""<main id="main" class="page dd lt" data-tool="{kind}">
  <div class="wrap dd__grid">
    <header class="page__head dd__head">
      <p class="dd__crumbs"><a href="../">Lab</a> <span aria-hidden="true">/</span> Calculator</p>
      <h1 class="page__title">{title}</h1>
      <p class="lede">{desc}</p>
      <p class="note__meta">Runs in your browser. Nothing you enter is sent or stored.</p>
    </header>
    <section class="dd__main lt-tool" aria-label="Calculator" hidden>
      <div class="lt-inputs">{lab_inputs(kind)}<button class="co-reset lt-reset" type="button">Reset inputs</button>
        <p class="lt-status" role="status" aria-live="polite"></p></div>
      <figure class="dd__chart"><div class="dd__plot" role="img" tabindex="0" aria-label="{title} chart. Use the arrow keys to read values."></div>
        <figcaption><p class="key">{key}</p><p class="dd__read" aria-live="polite"></p></figcaption></figure>
    </section>
    <noscript><p class="dd__pending">This calculator runs in your browser and needs JavaScript.</p></noscript>
    <aside class="report__side dd__side" aria-labelledby="side-title">
      <h2 class="report__side-title" id="side-title">Result</h2>
      <ul class="kpi lt-result" aria-live="polite"></ul>
      <p class="report__src">Calculated in your browser from the inputs. An Andra Markets tool, not a recommendation.</p>
    </aside>
    <div class="page__body dd__text">
      <section aria-labelledby="lt-how"><h2 id="lt-how">How it works</h2><p>{how}</p></section>
      <section aria-labelledby="lt-lim"><h2 id="lt-lim">Assumptions</h2><p>{limits}</p><p>For information and education only. Not investment advice.</p></section>
      <nav class="report__pager" aria-label="More Lab tools">{others}<a class="link" href="../">All Lab tools {icon("arrow-right")}</a></nav>
    </div>
  </div>
</main>"""
    return shell(title=f"{title}: Andra Markets Lab", desc=desc, body=body, home="../../", base="../../",
                 path=f"lab/{slug}/", scripts=("lab.js",))


def risk_page(i, data, key):
    slug, kind, title, desc, how, limits = LAB_TOOLS[i]
    others = "".join(f'<a class="link" href="../{t[0]}/">{t[2]} {icon("arrow-right")}</a>' for j, t in enumerate(LAB_TOOLS) if j != i)
    if data:
        payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
        tool = f"""<section class="dd__main lt-tool" aria-label="Calculator" hidden>
      <div class="lt-inputs">{risk_inputs(data)}<button class="co-reset lt-reset" type="button">Reset</button>
        <p class="lt-status" role="status" aria-live="polite"></p></div>
      <figure class="dd__chart"><div class="dd__plot dd__plot--matrix" role="img" tabindex="0" aria-label="Correlation matrix. Use the arrow keys to read each pair."></div>
        <figcaption><p class="key">{key}</p><p class="dd__read" aria-live="polite"></p></figcaption></figure>
      <div class="co-tab__wrap"><table class="co-tab lt-risk">
        <caption class="visually-hidden">Volatility and beta of each company picked</caption>
        <thead><tr><th scope="col">Company</th><th scope="col">Benchmark</th><th scope="col" class="num">Volatility</th>
        <th scope="col" class="num">Beta</th><th scope="col" class="num">Weight</th></tr></thead><tbody></tbody></table></div>
      <script type="application/json" id="lt-data">{payload}</script>
    </section>
    <noscript><p class="dd__pending">This tool runs in your browser and needs JavaScript.</p></noscript>"""
        meta = (f"Daily closes from Yahoo Finance to {day_med(dt.date.fromisoformat(data['asof']))}, refreshed at each deploy. "
                "Calculated in your browser: nothing you pick is sent or stored.")
        src = f"Yahoo Finance daily closes to {day_med(dt.date.fromisoformat(data['asof']))}, calculated in your browser."
    else:
        tool = '<section class="dd__main" aria-label="Calculator"><div class="dd__plot dd__plot--pending"><p class="dd__pending">Data pending</p></div></section>'
        meta = "Daily closes from Yahoo Finance. Data pending."
        src = "Yahoo Finance daily closes. Data pending."
    body = f"""<main id="main" class="page dd lt" data-tool="{kind}">
  <div class="wrap dd__grid">
    <header class="page__head dd__head">
      <p class="dd__crumbs"><a href="../">Lab</a> <span aria-hidden="true">/</span> Calculator</p>
      <h1 class="page__title">{title}</h1>
      <p class="lede">{desc}</p>
      <p class="note__meta">{meta}</p>
    </header>
    {tool}
    <aside class="report__side dd__side" aria-labelledby="side-title">
      <h2 class="report__side-title" id="side-title">Portfolio</h2>
      <ul class="kpi lt-result" aria-live="polite"></ul>
      <p class="report__src">{src} An Andra Markets tool, not a recommendation.</p>
    </aside>
    <div class="page__body dd__text">
      <section aria-labelledby="lt-how"><h2 id="lt-how">How it works</h2><p>{how}</p></section>
      <section aria-labelledby="lt-lim"><h2 id="lt-lim">Assumptions</h2><p>{limits}</p><p>For information and education only. Not investment advice.</p></section>
      <nav class="report__pager" aria-label="More Lab tools">{others}<a class="link" href="../">All Lab tools {icon("arrow-right")}</a></nav>
    </div>
  </div>
</main>"""
    return shell(title=f"{title}: Andra Markets Lab", desc=desc, body=body, home="../../", base="../../",
                 path=f"lab/{slug}/", scripts=("lab.js",) if data else ())


def lab_index():
    rows = "".join(
        f'<li><a href="{slug}/"><span class="learn-list__title">{title}</span>'
        f'<span class="learn-list__desc">{desc}</span><span class="learn-list__time">{"Yahoo Finance closes, calculated in your browser" if kind == "risk" else "Calculator, runs in your browser"}</span></a></li>'
        for slug, kind, title, desc, _, _ in LAB_TOOLS)
    body = f"""<main id="main" class="page">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Lab</h1>
      <p class="lede">Interactive quant tools. Change the inputs, watch the result move. Every tool runs in your browser: nothing you enter is sent or stored.</p>
    </header>
    <ol class="learn-list lab-index">{rows}</ol>
    <p class="lab-index__next">A momentum regime backtest is in development. New tools are announced in the daily note.</p>
  </div>
</main>"""
    return shell(title="Lab: Andra Markets", desc="Ten interactive quant tools that run in your browser: risk and correlation, options payoff and Black-Scholes Greeks, bond price, yield to maturity, efficient frontier, DCF, value at risk, real return, compound growth.",
                 body=body, home="../", base="../", path="lab/")


SIM_CACHE = ROOT / ".cache" / "sim"
SIM_DAYS = 504  # two years of trading days
SIM_DESC = ("Two hidden years of the S&amp;P 500, played day by day. Stay in or move to cash, and see if you can "
            "beat the Index.")
# (key, name, what the returns include)
SIM_MARKETS = [("sp500", "S&amp;P 500", "with dividends"), ("nasdaq", "Nasdaq Composite", "price only"),
               ("stoxx50", "Euro Stoxx 50", "price only"), ("nikkei", "Nikkei 225", "price only")]
SIMULATORS = [
    ("trading-simulator", "Trading Simulator", SIM_DESC.replace("S&amp;P 500", "S&amp;P 500, Nasdaq, Euro Stoxx 50 or Nikkei")
     + " A daily challenge, the same for everyone, or any two years on record."),
    ("panic-test", "Panic Test", "Start at the last high before one of the great crashes, without knowing which. Sell "
     "when you can't take any more, buy back when you are ready, and see what panic costs."),
    ("guess-the-fed", "Guess the Fed", "Ten hidden months from the Fed's history since 1983. With the figures it had, "
     "will it cut, hold or hike?"),
    ("portfolio-builder", "Portfolio Builder", "Split $10,000 between US stocks, bonds and cash and run it through ten "
     "hidden years, against the classic 60/40."),
]
SIMDATA_HEAD = "// Generated by tools/build_site.py. Do not edit.\n(window.ANDRA_SIMDATA=window.ANDRA_SIMDATA||{})"


def sim_load(name):
    try:
        return json.loads((SIM_CACHE / f"{name}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def sim_write(name, payload):
    """One assets/simdata-<name>.js per data set (a script: the deploy refuses
    JSON). Returns its versioned file name."""
    file = f"simdata-{name}.js"
    (OUT / "assets" / file).write_text(
        f"{SIMDATA_HEAD}[{json.dumps(name)}]=" + json.dumps(payload, separators=(",", ":")) + ";\n", encoding="utf-8")
    return f"{file}?v={ver(file)}"


def sim_market(key):
    """A market's daily history packed small: the first session, each next
    session's gap in days as one base-36 character, and each day's return in
    units of 0.001%. None until tools/sim_data.py has fetched it."""
    rec = sim_load(key)
    rows = (rec or {}).get("rows") or []
    if len(rows) < SIM_DAYS * 3:
        return None
    days = [dt.date.fromisoformat(d) for d, _ in rows]
    gaps = [(b - a).days for a, b in zip([dt.date.fromisoformat(rec["first"])] + days, days)]
    if max(gaps) > 35:
        return None
    file = sim_write(key, {"first": rec["first"], "gaps": "".join("0123456789abcdefghijklmnopqrstuvwxyz"[g] for g in gaps),
                           "r": ",".join(str(round(r * 1e5)) for _, r in rows)})
    return {"file": file, "first": days[0], "last": days[-1]}


def sim_bond_returns(yields):
    """Monthly total returns of a 10-year Treasury bought at par each month: the
    month's coupon plus the price change when the yield moves (semiannual
    coupons). {month: return}."""
    out = {}
    for (m0, y0), (m1, y1) in zip(yields, yields[1:]):
        c, y = y0 / 100, y1 / 100
        v = (1 + y / 2) ** -20
        price = c / y * (1 - v) + v if y > 0 else 1 + 10 * c
        out[m1] = price - 1 + c / 12
    return out


def sim_portfolio():
    """Monthly returns of US stocks (the S&P 500 with dividends, from the daily
    history) and of 10-year Treasuries, packed for the Portfolio Builder."""
    sp, bonds = sim_load("sp500"), sim_load("bonds")
    if not sp or not bonds:
        return None
    stock = {}
    for d, r in sp["rows"]:
        stock[d[:7]] = stock.get(d[:7], 1.0) * (1 + r)
    bond = sim_bond_returns(bonds["rows"])
    last = max(sp["rows"][-1][0][:7], "0")
    months = [m for m in sorted(stock) if m in bond and m < last]  # whole months only
    if len(months) < 240:
        return None
    s = [round((stock[m] - 1) * 1e5) for m in months]
    b = [round(bond[m] * 1e5) for m in months]
    return {"file": sim_write("portfolio", {"first": months[0], "s": ",".join(map(str, s)), "b": ",".join(map(str, b))}),
            "first": months[0], "last": months[-1]}


def sim_fed():
    rec = sim_load("fed")
    rows = (rec or {}).get("rows") or []
    if len(rows) < 300:
        return None
    return {"file": sim_write("fed", {"rows": rows}), "first": rows[0][0], "last": rows[-1][0]}


def sim_data():
    markets = {k: sim_market(k) for k, _, _ in SIM_MARKETS}
    return {"markets": {k: v for k, v in markets.items() if v}, "portfolio": sim_portfolio(), "fed": sim_fed()}


def sim_walk(seed=11, n=SIM_DAYS):
    """An illustrative path for the homepage block: an index and a player who
    sat out two stretches in cash. Not market data."""
    rnd = random.Random(seed)
    cash = ((120, 200), (300, 430))
    idx, you = [10000.0], [10000.0]
    for d in range(1, n):
        r = (0.0002 if d < 60 else (-0.0019 if d < 440 else 0.0026)) + rnd.gauss(0, 0.0105)
        idx.append(idx[-1] * (1 + r))
        out = any(a <= d < b for a, b in cash)
        you.append(you[-1] * (1.02 ** (1 / 252) if out else 1 + r))
    return idx, you, cash


def sim_chart_svg(idx, you, cash, label):
    """The game chart, drawn the way assets/sim.js draws it: your line heavy in
    the market and light in cash, cash stretches as labelled bands."""
    w, h, pad, n = 640, 300, 10, len(idx)
    lo, hi = min(idx + you) * 0.96, max(idx + you) * 1.03
    x = lambda i: i / (n - 1) * w
    y = lambda v: pad + (hi - v) / (hi - lo) * (h - 2 * pad)
    pts = lambda s, a, b: "M" + " L".join(f"{x(i):.1f},{y(s[i]):.1f}" for i in range(a, b))
    steps = [v for v in range(2000, 40000, 2000) if lo < v < hi]
    bands = "".join(f'<rect class="sim-cash" x="{x(a):.1f}" y="0" width="{x(b) - x(a):.1f}" height="{h}"/>' for a, b in cash)
    grid = "".join(f'<line class="sim-grid" x1="0" x2="{w}" y1="{y(v):.1f}" y2="{y(v):.1f}"/>' for v in steps)
    edges = sorted({0, n} | {e for a, b in cash for e in (a, b)})
    runs = "".join(f'<path class="{"sim-out" if any(a <= s < b for a, b in cash) else "sim-in"}" d="{pts(you, max(s - 1, 0), e)}"/>'
                   for s, e in zip(edges, edges[1:]))
    labs = "".join(f'<span style="top:{y(v) / h * 100:.1f}%">${v:,}</span>' for v in steps)
    tags = "".join(f'<span class="sim-bandlab" style="left:{x(a) / w * 100:.1f}%">Cash</span>' for a, b in cash)
    return (f'<svg class="sim-svg" viewBox="0 0 {w} {h}" preserveAspectRatio="none" role="img" aria-label="{label}">'
            f'{bands}{grid}<path class="sim-idx" d="{pts(idx, 0, n)}"/>{runs}</svg>'
            f'<div class="sim-ylabs" aria-hidden="true">{labs}</div>{tags}')


def sim_horse(base):
    return f'<div class="sim-horse" aria-hidden="true"><img src="{base}assets/andra-horse.png" alt="" width="1024" height="1024" loading="lazy" decoding="async"></div>'


SIM_KEY = ('<p class="key sim-key"><span><i class="sim-k-in"></i>You, in the market</span>'
           '<span><i class="sim-k-out"></i>You, in cash</span><span><i class="k-dash"></i>{rival}</span>{extra}</p>')


def sim_home():
    idx, you, cash = sim_walk()
    chart = sim_chart_svg(idx, you, cash, "A player against the Index over two years, illustrative, not market data")
    key = SIM_KEY.format(rival="The Index", extra='<span class="key__note">Illustrative</span>')
    return f"""  <section class="section sim-home" id="simulators" aria-labelledby="sim-title">
    <div class="wrap">
      <div class="sim-home__grid">
        <div class="reveal">
          <h2 class="section-title" id="sim-title">Simulators</h2>
          <p class="lede">{SIM_DESC}</p>
          <div class="sim-home__btns"><a class="btn" href="simulators/trading-simulator/">Play today's challenge {icon("arrow-right")}</a><a class="btn btn--ghost" href="simulators/">All simulators</a></div>
          <p class="sim-home__meta">Also: the Panic Test, Guess the Fed and the Portfolio Builder. Real market history, played in your browser.</p>
        </div>
        <a class="sim-home__art reveal" href="simulators/trading-simulator/" style="--i:1" aria-label="Open the Trading Simulator">
          <div class="sim-stage">{sim_horse("")}{chart}</div>
          {key}
        </a>
      </div>
    </div>
  </section>
"""


def sim_index(sim):
    src = {"trading-simulator": "S&amp;P 500 with dividends since 1928; Nasdaq, Euro Stoxx 50 and Nikkei prices",
           "panic-test": "Every fall of 25% or more on record, in the same four markets",
           "guess-the-fed": "FRED: CPI, unemployment, the Fed's target and the 2-year yield",
           "portfolio-builder": "S&amp;P 500 with dividends and 10-year Treasuries since 1928"}
    rows = "".join(f'<li><a href="{slug}/"><span class="learn-list__title">{name}</span>'
                   f'<span class="learn-list__desc">{desc}</span><span class="learn-list__time">{src[slug]}</span></a></li>'
                   for slug, name, desc in SIMULATORS)
    body = f"""<main id="main" class="page">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Simulators</h1>
      <p class="lede">Play through real market history and test your decisions. Every simulator runs in your browser; your results stay on your device.</p>
    </header>
    <ol class="learn-list lab-index">{rows}</ol>
  </div>
</main>"""
    return shell(title="Simulators: Andra Markets", desc="Four market simulators that run in your browser: the Trading Simulator, the Panic Test, Guess the Fed and the Portfolio Builder.",
                 body=body, home="../", base="../", path="simulators/")


def sim_head(name, tag_attr):
    return (f'<div class="sim-head"><div><p class="dd__crumbs"><a href="../">Simulators</a> <span aria-hidden="true">/</span> {name}</p>'
            f'<h1 class="sim-title">{name}</h1></div><p class="sim-tag" {tag_attr}></p></div>')


def sim_more(title, paras):
    return (f'<details class="sim-more"><summary>{title}</summary><div>'
            + "".join(f"<p>{p}</p>" for p in paras) + "</div></details>")


def sim_shell_page(slug, name, desc, body_inner, scripts, data_ok):
    if not data_ok:
        body_inner = (f'{sim_head(name, "")}<div class="dd__plot dd__plot--pending sim-pending"><p class="dd__pending">Data pending</p></div>')
        scripts = ()
    body = f"""<main id="main" class="sim-page" data-base="../../">
  <div class="wrap">
    {body_inner}
    <noscript><p class="dd__pending">This simulator runs in your browser and needs JavaScript.</p></noscript>
  </div>
</main>"""
    return shell(title=f"{name}: Andra Markets Simulators", desc=html.unescape(re.sub("<[^>]+>", "", desc)), body=body,
                 home="../../", base="../../", path=f"simulators/{slug}/", scripts=scripts)


def sim_game_page(kind, sim):
    """The Trading Simulator and the Panic Test: one chart game (assets/sim.js)."""
    slug, name, desc = next(s for s in SIMULATORS if s[0] == ("trading-simulator" if kind == "trading" else "panic-test"))
    from sim_content import MARKET_EPISODES
    markets = [{"key": k, "name": html.unescape(n), "note": note, "file": sim["markets"][k]["file"]}
               for k, n, note in SIM_MARKETS if k in sim["markets"]]
    episodes = {k: [{"from": a, "to": b, "title": t, "text": x, "links": [[l, u] for l, u in links]}
                    for a, b, t, x, links in MARKET_EPISODES[k]] for k in sim["markets"]}
    src = "; ".join(f"{html.unescape(n)}: Yahoo Finance, {sim['markets'][k]['first'].year} to {day_med(sim['markets'][k]['last'])}"
                    for k, n, _ in SIM_MARKETS if k in sim["markets"])
    config = json.dumps({"game": kind, "markets": markets, "episodes": episodes, "src": src},
                        separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    rival = "The Index" if kind == "trading" else "Holding on"
    if kind == "trading":
        how = [("You start with $10,000 in the market on the first day of a two-year stretch picked from its history, "
                "without being told which. The chart moves forward one trading day at a time. Press the button, or the "
                "space bar, to go to cash or back into the market, as often as you like. Your rival, the Index, buys "
                "on the first day and never sells."),
               ("Your line is heavy while you are in the market and light while you are in cash; cash stretches are "
                "shaded, and the strip under the chart shows your whole game at a glance."),
               ("The S&amp;P 500 includes dividends: the S&amp;P 500 Total Return index from 1988 and Robert Shiller's "
                "monthly dividends before that. The Nasdaq, the Euro Stoxx 50 and the Nikkei are prices only. Cash earns "
                "a flat 2% a year. A switch takes effect from the next day's close. No fees, no taxes."),
               ("At the end, 1,000 random players who were invested for the same number of days and traded as often as "
                "you show whether your result was skill or luck: beat 90% of them and it was skill."),
               "Keys: space to switch, P to pause, 1 to 4 for the speed. For information and education only. Not investment advice."]
    else:
        how = [("You hold $10,000 at the last high before one of the great falls of the market you pick: every fall of "
                "25% or more on record. You are not told which. The chart moves forward one trading day at a time, for "
                "three years. Sell when you can't take any more and buy back when you are ready, as often as you like."),
               ("Your rival is holding on: the same $10,000, never sold. At the end you see what your decisions cost or "
                "earned, how deep the fall went and how long the market took to regain its high."),
               ("Returns follow the same rules as the Trading Simulator: the S&amp;P 500 with dividends, the other "
                "markets prices only; money out of the market earns a flat 2% a year."),
               "Keys: space to sell or buy back, P to pause, 1 to 4 for the speed. For information and education only. Not investment advice."]
    pause_icon = '<svg class="icon" aria-hidden="true"><use href="#i-pause"/></svg>'
    market_chips = "".join(f'<button type="button" class="chip" data-market="{m["key"]}" aria-pressed="{"true" if i == 0 else "false"}">'
                           f'{html.escape(m["name"].replace(" Composite", ""))}</button>' for i, m in enumerate(markets))
    inner = f"""<div class="sim-play">
    {sim_head(name, 'data-sim="tag"')}
    <div class="sim-top"><p class="sim-gap"><span data-sim="gap">0.0 pts</span><small data-sim="gap-sub"></small></p>
      <p class="sim-month"><span data-sim="month"></span><small data-sim="since"></small></p></div>
    <div class="sim-stage sim-stage--game">{sim_horse("../../")}<svg class="sim-svg" viewBox="0 0 640 300" preserveAspectRatio="none" role="img" aria-label="Your money against {rival.lower()}" data-sim="chart"></svg><div class="sim-ylabs" aria-hidden="true" data-sim="ylabs"></div><div data-sim="marks"></div>
      <div class="sim-intro" data-sim="intro"><div><h2 data-sim="intro-title"></h2><p data-sim="intro-text"></p>
        <div class="filters sim-intro__modes" role="group" aria-label="Game" data-sim="modes" hidden><button type="button" class="chip" data-mode="daily" aria-pressed="true">Today's challenge</button><button type="button" class="chip" data-mode="random" aria-pressed="false">Random period</button></div>
        <div class="filters sim-intro__markets" role="group" aria-label="Market" data-sim="markets">{market_chips}</div>
        <button class="btn sim-start" type="button" data-sim="start">Start {icon("arrow-right")}</button>
        <p class="sim-intro__note" data-sim="intro-note"></p></div></div>
    </div>
    <div class="sim-ribbon" aria-hidden="true" data-sim="ribbon"></div>
    {SIM_KEY.format(rival=rival, extra="").replace('<p class="key sim-key">', '<p class="key sim-key" data-sim="key">').replace("You, in cash", "You, in cash" if kind == "trading" else "You, sold")}
    <div class="sim-row" data-sim="row" hidden><button class="btn sim-go" type="button" data-sim="go"><span></span><kbd>Space</kbd></button><button class="btn btn--ghost sim-sq" type="button" data-sim="speed" aria-label="Speed, 1x">1x</button><button class="btn btn--ghost sim-sq" type="button" data-sim="pause" aria-label="Pause">{pause_icon}</button></div>
    <p class="visually-hidden" aria-live="polite" data-sim="live"></p>
    {sim_more("How it works", how)}
  </div>
  <section class="sim-final" aria-labelledby="sim-final-title" hidden></section>
  <script type="application/json" id="sim-config">{config}</script>"""
    return sim_shell_page(slug, name, desc, inner, ("sim.js",), bool(markets))


def sim_fed_page(sim):
    slug, name, desc = SIMULATORS[2]
    fed = sim["fed"]
    from sim_content import EPISODES
    eps = [{"from": a, "to": b, "title": t} for a, b, t, _, _ in EPISODES]
    config = json.dumps({"file": fed["file"] if fed else "", "episodes": eps,
                         "src": f"FRED: CPI, unemployment, the Fed's target and the 2-year Treasury yield, to {fed['last']}" if fed else ""},
                        separators=(",", ":")).replace("</", "<\\/")
    cards = "".join(f'<div><span>{t}</span><b data-fed="{k}"></b><em data-fed="{k}-note"></em><svg viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true"><path data-fed="{k}-spark"/></svg></div>'
                    for k, t in (("cpi", "Inflation, CPI over 12 months"), ("un", "Unemployment"),
                                 ("target", "Fed funds target"), ("gs2", "2-year Treasury yield")))
    how = [("Ten months are picked from the Fed's history since 1983, without their dates. For each one you see the "
            "latest figures before it: inflation, unemployment, the Fed's target and the 2-year Treasury yield, with "
            "their last two years. Will the Fed cut its target that month, hold it or raise it?"),
           ("A month counts as a cut or a hike when the Fed's target at its end differs from the month before, "
            "including moves between meetings. Each game mixes cuts, holds and hikes. The figures are each month's "
            "own, as revised since, so they can differ a little from what the Fed saw at the time."),
           "Data: FRED, the Federal Reserve Bank of St. Louis. For information and education only. Not investment advice."]
    inner = f"""<div class="fed-game">
    {sim_head(name, 'data-fed="tag"')}
    <div class="sim-panel fed-intro" data-fed="intro"><h2>Can you think like the Fed?</h2>
      <p>Ten hidden months from the Fed's history since 1983. You see what the Fed saw. Will it cut, hold or hike?</p>
      <div class="filters" role="group" aria-label="Game" data-fed="modes"><button type="button" class="chip" data-mode="daily" aria-pressed="true">Today's challenge</button><button type="button" class="chip" data-mode="random" aria-pressed="false">Random months</button></div>
      <button class="btn" type="button" data-fed="start">Start {icon("arrow-right")}</button></div>
    <div class="fed-round" data-fed="round" hidden>
      <div class="fed-grid">{cards}</div>
      <p class="fed-q">What does the Fed do this month?</p>
      <div class="fed-btns" role="group" aria-label="Your answer"><button class="btn btn--ghost" type="button" data-pick="cut">Cut</button><button class="btn btn--ghost" type="button" data-pick="hold">Hold</button><button class="btn btn--ghost" type="button" data-pick="hike">Hike</button></div>
      <div class="sim-panel fed-ans" data-fed="answer" aria-live="polite" hidden></div>
    </div>
    {sim_more("How it works", how)}
  </div>
  <section class="sim-final" aria-labelledby="sim-final-title" hidden></section>
  <script type="application/json" id="fed-config">{config}</script>"""
    return sim_shell_page(slug, name, desc, inner, ("fed-game.js",), bool(fed))


def sim_portfolio_page(sim):
    slug, name, desc = SIMULATORS[3]
    pf = sim["portfolio"]
    from sim_content import EPISODES
    eps = [{"from": a, "to": b, "title": t, "links": [[l, u] for l, u in links]} for a, b, t, _, links in EPISODES]
    config = json.dumps({"file": pf["file"] if pf else "", "episodes": eps,
                         "src": (f"S&P 500 with dividends (Yahoo Finance, Robert Shiller) and 10-year Treasuries (Robert Shiller, FRED), "
                                 f"{pf['first'][:4]} to {pf['last']}") if pf else ""},
                        separators=(",", ":")).replace("</", "<\\/")
    sliders = "".join(f'<div class="pb-row"><label for="pb-{k}">{t}<b data-pb="{k}-v">{v}%</b></label>'
                      f'<input id="pb-{k}" type="range" min="0" max="100" step="5" value="{v}" data-pb="{k}"></div>'
                      for k, t, v in (("s", "Stocks", 60), ("b", "Bonds", 30)))
    how = [("Ten years are picked at random from US history since 1928, without their dates. Your $10,000 is split "
            "between stocks, bonds and cash as you choose; cash takes whatever stocks and bonds leave. Without "
            "rebalancing the mix drifts with the markets; rebalancing resets it every twelve months. The dashed line is "
            "the classic 60/40, 60% stocks and 40% bonds rebalanced every year."),
           ("Stocks are the S&amp;P 500 with dividends. Bonds are a 10-year US Treasury bought each month at par, its "
            "return the coupon plus the price change as yields move, from Robert Shiller's long rate and FRED. Cash "
            "earns a flat 2% a year. Monthly returns; no fees, no taxes."),
           "Press Run again to try another mix on the same years. For information and education only. Not investment advice."]
    inner = f"""<div class="pb-game">
    {sim_head(name, 'data-pb="tag"')}
    <div class="pb">
      <form class="pb-form" data-pb="form">
        {sliders}
        <div class="pb-row pb-row--cash"><span>Cash</span><b data-pb="c-v">10%</b></div>
        <p class="pb-lab" id="pb-reb">Rebalance</p>
        <div class="filters" role="group" aria-labelledby="pb-reb"><button type="button" class="chip" data-reb="0" aria-pressed="false">Never</button><button type="button" class="chip" data-reb="1" aria-pressed="true">Every year</button></div>
        <button class="btn pb-run" type="submit" data-pb="run">Run ten years {icon("arrow-right")}</button>
        <button class="btn btn--ghost pb-new" type="button" data-pb="new" hidden>New hidden years</button>
      </form>
      <div class="pb-out">
        <div class="pb-chart"><svg class="sim-svg" viewBox="0 0 640 300" preserveAspectRatio="none" role="img" aria-label="Your mix against the 60/40" data-pb="chart"></svg><div class="sim-ylabs" aria-hidden="true" data-pb="ylabs"></div><p class="pb-empty" data-pb="empty">Pick a mix and press Run.</p></div>
        <p class="key sim-key"><span><i class="k-solid"></i><span data-pb="mixname">Your mix</span></span><span><i class="k-dash"></i>The classic 60/40</span></p>
        <div class="pb-figs" data-pb="figs" hidden></div>
        <div class="sim-panel pb-reveal" data-pb="reveal" hidden></div>
      </div>
    </div>
    {sim_more("How it works", how)}
  </div>
  <script type="application/json" id="pb-config">{config}</script>"""
    return sim_shell_page(slug, name, desc, inner, ("portfolio-game.js",), bool(pf))

METHOD_QA = [
    ("Where do the figures come from?",
     "Every chart and table names its source and date under it. Prices come from Yahoo Finance; Treasury yields, "
     "credit spreads, inflation and payrolls from FRED, the Federal Reserve Bank of St. Louis database that carries "
     "the US Treasury, BLS and ICE BofA series; release dates from each publisher's own calendar."),
    ("When is the close note published?",
     "Every US trading day after the close. The site looks for a new note every half hour from 20:00 to 02:59 UTC "
     "and publishes it once it passes every check. A note dated on a day the NYSE did not trade is held back, "
     "never published."),
    ("What happens when a source fails?",
     "The dashboard, calendar or company page keeps its last good figures and shows their own date, so you can "
     "always see how old a number is. A dashboard with no figures yet says Data pending instead of showing a "
     "made-up chart."),
    ("Is any of this investment advice?",
     "No. Andra Markets publishes research for information only. It never publishes model portfolios or buy and "
     "sell lists."),
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
    def sec(sid, title, inner):
        return f'<section aria-labelledby="m-{sid}"><h2 id="m-{sid}">{title}</h2>{inner}</section>'

    def ruled(items):
        return '<ul class="ruled">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"

    dash_src = [f"<b>{html.unescape(name).replace('&', '&amp;')}</b>: {DASH_PAGES[key][3]}"
                for key, _, name, _, _ in DASHBOARDS]
    body = f"""<main id="main" class="page">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Methodology</h1>
      <p class="lede">How the daily close note is produced and checked, where the dashboards and the calendar get their figures, and what they cannot tell you.</p>
    </header>
    <div class="page__body method">
      {sec("note", "The daily close note",
           "<p>One note for every US trading day, written after the 4:00 pm New York close (1:00 pm on early closes). "
           "An automated research pipeline collects the session's figures into a fact pack: the closing level and "
           "daily change of each instrument, the Treasury curve, a risk score and breadth across the Andra Markets "
           "watchlist of US large caps. A language model then drafts the note's text from that fact pack only. "
           "When the model fails, the pipeline publishes a quantitative edition with the figures and no commentary.</p>")}
      {sec("reports", "How reports are produced",
           "<p>Andra Markets publishes three kinds of report, on this site: the close notes in the <a href=\"../reports/\">archive</a>, the others in the <a href=\"../research/\">Research Library</a>:</p>"
           + ruled([
               "<b>Daily close note</b>: every US trading day, after the close, as described above.",
               "<b>Weekly market review</b>: once a week, after the last session of the trading week, on what moved "
               "across asset classes and what the week ahead holds.",
               "<b>Research</b>: deeper work on a theme, an asset class or a company, published when it is ready, "
               "with no fixed schedule.",
           ])
           + "<p>Each report goes through the same steps. An automated pipeline collects the figures from the "
             "sources below into a verified data set, dated and sourced. The text is drafted from that data set "
             "only, with the help of a language model, and every figure in it is checked against the data set "
             "before publication. A report whose figures do not all match is held, reviewed and corrected before "
             "it is published, and its sources section says so. Opinions are marked as such and are Andra "
             "Markets' reading on the day of publication.</p>")}
      {sec("data", "Data sources",
           ruled([
               "<b>Prices and closes</b>: Yahoo Finance, for US and international equity indices, sector ETFs, "
               "volatility indices, currencies, commodity futures, credit ETFs, digital assets and the watchlist stocks.",
               "<b>Treasury yields, breakevens and real yields</b>: FRED, which serves the US Treasury's daily "
               "par yield curve.",
               "<b>Risk score and breadth</b>: calculated by Andra Markets from the fact pack.",
           ])
           + "<p>Each instrument is taken at its own official close, so an Asian or European index is that market's "
             "close, not a New York price. Every source the site uses, with what it feeds and how often it is "
             "read, is on the <a href=\"../sources/\">data sources</a> page.</p>")}
      {sec("timing", "Timing",
           "<p>The pipeline runs after the US close. This site looks for a new note every half hour from 20:00 to "
           "02:59 UTC, every day, and publishes each note as soon as it passes the checks below. FRED usually posts "
           "a day's Treasury curve late in the evening, so the curve in a note is often the previous session's; the "
           "note's chart says which close it shows.</p>")}
      {sec("check", "Figure check",
           "<p>Before publication every figure in the text is compared with the session's fact pack. A figure the "
           "fact pack does not support fails the check. A note that fails is never published automatically: it is "
           "held for review, and if it is published after review its Sources section says that it did not fully "
           "pass the automated check.</p>")}
      {sec("held", "What is held and why",
           "<p>A note is published straight away only when nothing below applies. Otherwise it is held for review, "
           "and published only once it has been read and approved:</p>"
           + ruled([
               "The date was not an NYSE trading day, or lies in a year whose holidays are not yet in the calendar: "
               "the session cannot be confirmed.",
               "The note is dated in the future, or the run finished before that day's close: its figures cannot be "
               "that session's.",
               "The figure check failed.",
               "The run was a test run, so its figures are not market data.",
               "A figure is from another session, for example a market that was closed that day: the note would mix dates.",
               "A section is missing or stops mid-sentence: the text was cut off.",
               "The text had to be read back from the report rather than from the pipeline's own text file.",
           ])
           + "<p>A run whose files are missing or unreadable is rejected outright. There is one note per session: "
             "the newest run that passes is published and earlier runs that day are set aside. A published note "
             "that later fails a re-check is taken down.</p>")}
      {sec("dashboards", "Dashboards",
           "<p>The dashboards are refreshed at every deploy, before the US open and after the 8:30 and 10:00 am "
           "New York releases. Each shows the date of its own figures, never the date of the build.</p>"
           + ruled(dash_src))}
      {sec("calendar", "Calendar",
           "<p>Every date and time comes from the publisher's own schedule: the BLS, BEA, Census Bureau, Department "
           "of Labor, Federal Reserve, TreasuryDirect, ISM and S&amp;P Global, The Conference Board, the University "
           "of Michigan, the ECB, Eurostat, the Bank of England, the ONS, the Bank of Japan, China's National Bureau "
           "of Statistics and the People's Bank of China. Previous and Actual come from FRED, Eurostat, the ECB, the "
           "ONS, the Bank of England and TreasuryDirect; Actual is the figure as first printed, linked to its "
           "release. Earnings dates and EPS come from Yahoo Finance, with membership from State Street's SPY "
           "holdings and iShares' STOXX Europe 600 ETF holdings. The full list, with the date each was last read, "
           "is on the <a href=\"../calendar/#cl-src\">calendar page</a>.</p>")}
      {sec("limits", "Limits",
           ruled([
               "No consensus forecasts: there is no reliable free source, so the calendar shows Previous and Actual only.",
               "Breadth covers the Andra Markets watchlist of US large caps, not the whole market.",
               "Price changes leave out dividends. Futures roll to the next contract near expiry, which can add a small jump.",
               "Economic figures are revised after release. Dashboards show the latest vintage; the calendar's Actual is the first print.",
               "FRED carries ICE credit spreads with a short delay, and the Treasury curve usually a day late.",
               "An earnings date marked Estimated may move, and a report time Yahoo Finance does not give is never guessed.",
               "When a source fails, its last good figures stay up with their own date until the next good read.",
               "The text of each note is machine-drafted. Its figures are checked against the fact pack; its reading of the session is commentary, not fact.",
           ]))}
      {sec("charts", "Charts and colour",
           "<p>Every chart states its source and date. Green marks a rise and red a fall, on charts and on every "
           "figure that shows a move, always with its + or &minus; sign so colour is never the only cue. Lab "
           "diagrams marked Illustrative are not market data.</p>")}
      {sec("corrections", "Corrections",
           "<p>A published note found to be wrong is taken down and the site rebuilds without it; it stays down, "
           "whatever later runs for that date bring, until it has been corrected and restored. Dashboards and the calendar correct themselves at the "
           "next good read of their source.</p>")}
      <section aria-labelledby="m-questions">
        <h2 id="m-questions">Questions</h2>
        <div class="acc">{questions()}</div>
      </section>
    </div>
  </div>
</main>"""
    return shell(
        title="Methodology: Andra Markets",
        desc="How the Andra Markets close note is produced and checked, the sources behind the dashboards and the calendar, and their limits.",
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
      <p class="lede">Every US trading day, after the close. {count} Weekly reviews and research are in the <a href="../research/">Research Library</a>.</p>
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


# Research Library (/research/) ----------------------------------------------
#
# The reports that are not the daily note, published as their PDFs: weekly
# market reviews and research, from data/reports (index.json plus one PDF each
# in data/reports/pdf; see data/reports/README.md). Each entry links straight
# to its PDF, which the browser opens as it is. The latest weekly review leads
# the page; earlier reviews sit in a lattice of issues and research in a ruled
# list. The weekly blocks stay hidden until the first review is published.
# site.js filters both by topic and by the search field.

LIB = ROOT / "data" / "reports"
LIB_PDF = LIB / "pdf"
LIB_TYPE_NAME = {"weekly": "Weekly market review", "research": "Research"}
LIB_TAGS = [("equities", "Equities"), ("rates", "Rates"), ("fx", "FX"), ("commodities", "Commodities"),
            ("macro", "Macro"), ("credit", "Credit")]
LIB_TAG_NAME = dict(LIB_TAGS)
PDF_SOON = "PDF downloads open to subscribers with the paid tier. The full text is free to read here."


def load_library():
    """Published weekly reviews and research reports with their PDF, newest first."""
    f = LIB / "index.json"
    if not f.exists():
        return []
    out = []
    for r in json.loads(f.read_text(encoding="utf-8")).get("reports", []):
        if r.get("published") is False:
            continue
        pdf = LIB_PDF / f"{r['slug']}.pdf"
        if not pdf.exists():
            print(f"skipped report {r['slug']}: data/reports/pdf/{r['slug']}.pdf is missing")
            continue
        out.append(dict(r, day=dt.date.fromisoformat(r["date"]), pdf=pdf, size=pdf.stat().st_size,
                        tags=[t for t in r.get("tags", []) if t in LIB_TAG_NAME]))
    return sorted(out, key=lambda r: (r["date"], r["slug"]), reverse=True)


def lib_chips(attr, options, counts=None):
    """Chips for one filter group, the first pressed; with counts, a value with
    nothing in it has no chip (a Research chip appears with the first report)."""
    if counts is not None:
        options = [(v, label) for v, label in options if v == "all" or counts.get(v)]
    return "".join(
        f'<button type="button" class="chip" data-{attr}="{v}" aria-pressed="{"true" if i == 0 else "false"}">'
        f'{label}{f" <span class=chip__n>{counts[v]}</span>" if counts is not None and v in counts else ""}</button>'
        for i, (v, label) in enumerate(options))


def lib_week(day):
    """ "Week 44 · 26–30 Oct 2026": the ISO week of a weekly review and its Monday to Friday."""
    mon = day - dt.timedelta(days=day.weekday())
    fri = mon + dt.timedelta(days=4)
    if mon.month == fri.month:
        span = f"{mon.day}–{fri.day} {fri:%b %Y}"
    else:
        span = f"{mon.day} {mon:%b} – {fri.day} {fri:%b %Y}"
    return day.isocalendar()[1], span


def lib_attrs(r):
    q = " ".join([r["title"], r["summary"], LIB_TYPE_NAME[r["type"]]] + [LIB_TAG_NAME[t] for t in r["tags"]]).lower()
    return f'data-lib-item data-tags="{" ".join(r["tags"])}" data-q="{esc(q)}"'


def lib_href(r):
    return f'pdf/{r["slug"]}.pdf'


def lib_link(r):
    """The attributes of a link that opens a report's PDF in a new tab."""
    return f'href="{lib_href(r)}" target="_blank" rel="noopener" type="application/pdf"'


def lib_file(r):
    """ "PDF · 5 pages · 0.5 MB" """
    pages = r.get("pages")
    mb = r["size"] / 1e6
    size = f"{mb:.1f} MB" if mb >= 0.1 else f"{max(1, round(r['size'] / 1e3))} KB"
    return " · ".join(["PDF"] + ([f"{pages} page{'' if pages == 1 else 's'}"] if pages else []) + [size])


def library_page(library):
    weekly = [r for r in library if r["type"] == "weekly"]
    research = [r for r in library if r["type"] == "research"]
    lead = weekly[0] if weekly else None
    tags = lambda r: " · ".join(LIB_TAG_NAME[t] for t in r["tags"])

    lead_html = ""
    if lead:
        wk, span = lib_week(lead["day"])
        lead_html = f"""<section class="grid lib-lead" aria-labelledby="lib-lead-t">
      <div class="lib-lead__main">
        <p class="lib-lead__kicker"><span>Latest weekly market review</span><span>Week {wk} · {span}</span></p>
        <h2 class="lib-lead__title" id="lib-lead-t"><a {lib_link(lead)}>{esc(lead["title"])}</a></h2>
        <p class="lede">{esc(lead["summary"])}</p>
        <p class="note__meta"><time datetime="{lead["date"]}">{day_long(lead["day"])}</time><span>{lib_file(lead)}</span>{f"<span>{tags(lead)}</span>" if lead["tags"] else ""}</p>
        <div class="lib-lead__acts">
          <a class="btn" {lib_link(lead)}>Open the PDF {icon("arrow-up-right")}</a>
        </div>
      </div>
    </section>"""

    def issue(r):
        wk, span = lib_week(r["day"])
        return (f'<li class="lib-issue" {lib_attrs(r)}><a {lib_link(r)}>'
                f'<span class="lib-issue__n">Week {wk}</span><span class="lib-issue__d">{span}</span>'
                f'<span class="lib-issue__t">{esc(r["title"])}</span><span class="lib-issue__s">{esc(r["summary"])}</span>'
                f'<span class="lib-issue__f"><span>{tags(r)}</span><span>{lib_file(r)}</span></span>'
                f'{icon("arrow-up-right")}</a></li>')

    def study(r):
        topic = LIB_TAG_NAME[r["tags"][0]] if r["tags"] else "Research"
        return (f'<li {lib_attrs(r)}><a {lib_link(r)}><span class="lib-res__topic">{topic}</span>'
                f'<span class="lib-res__body"><span class="lib-res__t">{esc(r["title"])}</span>'
                f'<span class="lib-res__s">{esc(r["summary"])}</span>'
                f'<span class="lib-res__m"><time datetime="{r["date"]}">{day_med(r["day"])}</time> · {lib_file(r)}</span></span>'
                f'{icon("arrow-up-right")}</a></li>')

    earlier = weekly[1:]
    if earlier:
        weekly_html = f'<ol class="lib-issues">{"".join(issue(r) for r in earlier)}</ol>'
    else:
        weekly_html = '<p class="lib__none">Earlier reviews are listed here as each new one is published.</p>'
    weekly_sec = f"""<section class="lib-sec" aria-labelledby="lib-weekly">
      <div class="lib-sec__head"><h2 id="lib-weekly">Weekly market reviews</h2><p>Every Friday after the close: what moved across asset classes, and the week ahead.</p></div>
      {weekly_html}
    </section>""" if weekly else ""
    research_html = (f'<ol class="lib-res">{"".join(study(r) for r in research)}</ol>' if research
                     else '<p class="lib__none">The first research report is on its way.</p>')
    tag_n = {k: sum(k in r["tags"] for r in library) for k, _ in LIB_TAGS}
    nw, nr = len(weekly), len(research)
    counts = ([f'{nw} weekly review{"" if nw == 1 else "s"}'] if nw else []) + [f'{nr} research report{"" if nr == 1 else "s"}']
    tools = ""
    if library:
        tools = f"""<div class="lib-tools">
      <form class="pf-field lib__search" role="search" action="">
        {icon("magnifying-glass")}
        <input type="search" id="lib-q" name="q" aria-label="Search reports" placeholder="Search reports" autocomplete="off" spellcheck="false">
      </form>
      <div class="filters" role="group" aria-label="Filter by topic">{lib_chips("lib-tag", [("all", "All topics")] + LIB_TAGS, dict(tag_n, all=len(library)))}</div>
    </div>
    <p class="filters__status lib__status" role="status" aria-live="polite"></p>"""
    body = f"""<main id="main" class="page lib">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Research Library</h1>
      <p class="lede">Weekly market reviews and research from Andra Markets: longer than the daily note, written to be kept. Each report opens as its PDF.</p>
    </header>
    <p class="lib-count">{"".join(f"<span>{c}</span>" for c in counts) if library else ""}<span>Looking for the daily note? <a href="../reports/">All close notes</a></span></p>
    {lead_html}
    {tools}
    {weekly_sec}
    <section class="lib-sec" aria-labelledby="lib-research">
      <div class="lib-sec__head"><h2 id="lib-research">Research</h2><p>Deeper work on a theme, an asset class or a company, published when it is ready.</p></div>
      {research_html}
    </section>
    <p class="lib__empty" hidden>No report matches. <button type="button" class="link" data-lib-reset>Clear the search {icon("arrow-right")}</button></p>
  </div>
</main>"""
    return shell(
        title="Research Library: Andra Markets",
        desc="Weekly market reviews and research from Andra Markets, as PDFs: longer than the daily note, written to be kept.",
        body=body,
        home="../",
        base="../",
        path="research/",
    )



def share_row(what):
    """The report share row: Share (system sheet or copy link) and the PDF
    download, shown locked until the paid tier opens."""
    return f"""<div class="report__share" hidden>
          <button class="btn" type="button" data-share><span class="swap"><span class="swap__a">{icon("link")}Share this {what}</span><span class="swap__b" aria-hidden="true">{icon("check")}Link copied</span></span></button>
          <button class="btn btn--ghost lib-pdf" type="button" aria-disabled="true" data-soon="{PDF_SOON}">{icon("lock-simple")}Download PDF<span class="lib-pdf__tag">Subscribers only</span></button>
          <p class="report__share-status" role="status" aria-live="polite"></p>
        </div>"""


# Markets Interview Prep (/interview-prep/) -----------------------------------
#
# One data file, data/interview_prep.json: the weekly block ("week") is
# rewritten every week; the question bank changes when a question is added.
# Weekly figures come from the close notes the topic cites, never from memory.

IPREP = ROOT / "data" / "interview_prep.json"
IP_PARTS = [("what", "What happened"), ("why", "Why it matters"), ("say", "Say it in an interview")]


def ip_blocks(text):
    """Answer text: paragraphs split by a blank line; a block of "1. " lines is a numbered list."""
    out = ""
    for block in text.strip().split("\n\n"):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if lines and all(re.match(r"\d+\. ", ln) for ln in lines):
            items = (esc(re.sub(r"^\d+\. ", "", ln)) for ln in lines)
            out += '<ol class="ruled">' + "".join(f"<li>{t}</li>" for t in items) + "</ol>"
        else:
            out += f"<p>{esc(' '.join(lines))}</p>"
    return out


def interview_page(notes):
    d = json.loads(IPREP.read_text(encoding="utf-8"))
    week = d["week"]
    published = {rec["date"] for rec in notes}
    monday = dt.date.fromisoformat(week["of"])

    def src(day):
        dd = dt.date.fromisoformat(day)
        label = f"{dd.day} {dd:%b}"
        return f'<a href="../reports/{day}/">{label}</a>' if day in published else label

    topics = "".join(
        f'<li class="ip-topic"><span class="ip-topic__n" aria-hidden="true">{i + 1:02d}</span><div>'
        f'<h3>{esc(t["title"])}</h3><dl class="ip-topic__parts">'
        + "".join(f"<dt>{label}</dt><dd>{esc(t[key])}</dd>" for key, label in IP_PARTS)
        + f'</dl><p class="ip-topic__src">From the close notes of {", ".join(src(x) for x in t["sources"])}.</p></div></li>'
        for i, t in enumerate(week["topics"]))
    cats = d["categories"]
    counts = {c["id"]: sum(q["cat"] == c["id"] for q in d["questions"]) for c in cats}
    chips = lib_chips("ipcat", [("all", "All")] + [(c["id"], c["name"]) for c in cats],
                      dict(counts, all=len(d["questions"])))
    cat_name = {c["id"]: c["name"] for c in cats}
    items = ""
    order = {c["id"]: i for i, c in enumerate(cats)}
    for i, q in enumerate(sorted(d["questions"], key=lambda q: order[q["cat"]])):
        follow = f'<p class="ip-follow"><b>Likely follow-up:</b> {esc(q["follow"])}</p>' if q.get("follow") else ""
        items += (f'<div class="acc__item" data-cat="{q["cat"]}">'
                  f'<h3><button type="button" class="acc__btn" id="ip-b{i}" aria-expanded="false" aria-controls="ip-p{i}">'
                  f'<span><span class="ip-q__cat">{cat_name[q["cat"]]}</span>{esc(q["q"])}</span>'
                  f'<span class="acc__plus" aria-hidden="true"></span></button></h3>'
                  f'<div class="acc__panel" id="ip-p{i}" role="region" aria-labelledby="ip-b{i}"><div>'
                  f'{ip_blocks(q["a"])}{follow}</div></div></div>')
    updated = dt.date.fromisoformat(week["updated"])
    body = f"""<main id="main" class="page ip">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Markets Interview Prep</h1>
      <p class="lede">For students preparing for investment banking, sales and trading and asset management interviews: what moved markets this week, and the questions interviewers ask, with model answers.</p>
    </header>
    <div class="page__body">
      <section aria-labelledby="ip-week">
        <h2 id="ip-week">What you need to know this week</h2>
        <p class="note__meta"><span>Week of {day_long(monday)}</span><span>Updated <time datetime="{week["updated"]}">{day_med(updated)}</time></span></p>
        <p>{esc(week["intro"])}</p>
        <ol class="ip-week">{topics}</ol>
      </section>
      <section aria-labelledby="ip-bank">
        <h2 id="ip-bank">Question bank</h2>
        <p>Typical markets questions from IB, S&amp;T and asset management interviews, grouped by subject. Open a question for a model answer and the follow-up to expect.</p>
        <div class="ip-filters">
          <div class="filters" role="group" aria-label="Filter questions by subject">{chips}</div>
          <p class="filters__status ip__status" role="status" aria-live="polite">Showing all {len(d["questions"])} questions</p>
        </div>
        <div class="acc acc--multi">{items}</div>
      </section>
      <section aria-labelledby="ip-use">
        <h2 id="ip-use">How to use it</h2>
        <p>Model answers are a starting point: say them in your own words, and check the latest levels on the morning of your interview. Figures in the weekly block are from the Andra Markets <a href="../reports/">close notes</a>, each linked to its session.</p>
        <p>Educational material. Not investment advice, and no question here is a recommendation to buy or sell anything.</p>
      </section>
    </div>
  </div>
</main>"""
    return shell(
        title="Markets Interview Prep: Andra Markets",
        desc="What moved markets this week and the markets questions IB, S&T and asset management interviewers ask, with model answers.",
        body=body,
        home="../",
        base="../",
        path="interview-prep/",
    )


# Data sources (/sources/), legal notice (/legal/), privacy (/privacy/) ---------

# (provider, url, what it supplies, where it is used, how often it is read)
DATA_SOURCES = [
    ("Yahoo Finance", "https://finance.yahoo.com/",
     "Closing prices of equity indices, sector ETFs, volatility indices, currencies, commodity futures, credit ETFs, "
     "digital assets and the watchlist stocks; CBOT fed funds futures and the Cboe Treasury yield indices; earnings "
     "dates, diluted EPS and market caps.",
     "Close notes, dashboards, Fed &amp; Rates, World, FX, calendar earnings, company pages, Simulators",
     "After each US close for the notes; at every deploy for the dashboards; every 15 minutes while the NYSE is "
     "open for the fed funds futures and intraday yields"),
    ("FRED, Federal Reserve Bank of St. Louis", "https://fred.stlouisfed.org/",
     "The US Treasury's daily par yield curve, breakevens and real yields, the 2s10s and 3m10y spreads, the Fed's "
     "target range, the effective and monthly federal funds rates, ICE BofA credit spreads, inflation, unemployment "
     "and payrolls; the 10-year Treasury yield since 1953 for the Portfolio Builder.",
     "Close notes, dashboards, Fed &amp; Rates, calendar actuals, Guess the Fed, Portfolio Builder",
     "Daily; FRED posts the Treasury curve late in the evening and credit spreads with a short delay"),
    ("US Treasury and TreasuryDirect", "https://home.treasury.gov/resource-center/data-chart-center/interest-rates",
     "Note and bond auction schedules and results; the daily par yield curve and real yield curve.",
     "Fed &amp; Rates, calendar, close notes", "At every deploy, and each weekday evening after the curve is posted"),
    ("Cboe", "https://www.cboe.com/",
     "VIX and the volatility term structure; the options expiration calendar; the 13-week, 5-, 10- and 30-year "
     "Treasury yield indices.",
     "Dashboards, Fed &amp; Rates, close notes, calendar", "At every deploy; every 15 minutes while the NYSE is open for the yield indices"),
    ("Official statistics and central banks", "../calendar/#cl-src",
     "Release dates and times from the BLS, BEA, Census Bureau, Department of Labor, Federal Reserve, ISM, S&amp;P "
     "Global, The Conference Board, the University of Michigan, the ECB, Eurostat, the Bank of England, the ONS, "
     "the Bank of Japan, China's National Bureau of Statistics and the People's Bank of China; actual figures from "
     "Eurostat, the ECB, the ONS and the Bank of England.",
     "Calendar, Fed &amp; Rates (FOMC dates)", "At every deploy; each source's last read is on the calendar page"),
    ("State Street and iShares", "https://www.ssga.com/",
     "Index membership from the SPY holdings (S&amp;P 500) and the iShares STOXX Europe 600 ETF holdings.",
     "Calendar earnings, company pages", "At every deploy"),
    ("OECD, World Bank and IMF", "https://data.oecd.org/",
     "Ten-year government bond yields, inflation, unemployment and real GDP growth by country; OECD three-month "
     "interbank rates.",
     "World markets, FX", "At every deploy; each figure shows its own date"),
    ("Financial Modeling Prep", "https://site.financialmodelingprep.com/",
     "Company profiles, financial statements and ratios, up to ten years.",
     "Company pages", "When a page is opened, cached for 24 hours"),
    ("Finnhub", "https://finnhub.io/",
     "Quotes, company news, peers, analyst recommendation trends and company metrics.",
     "Company pages", "When a page is opened: the price cached for 60 seconds, news for 15 minutes"),
    ("Robert Shiller, Yale University", "https://shillerdata.com/",
     "Monthly S&amp;P 500 dividends and the long-term US interest rate since 1871: dividends added to the S&amp;P 500's "
     "daily returns before 1988 (from 1988 the S&amp;P 500 Total Return index from Yahoo Finance), and 10-year "
     "Treasury returns before 1953.",
     "Simulators", "At most once a day, at deploy"),
    ("Andra Markets", "../methodology/",
     "The risk score, watchlist breadth and dispersion, and the FOMC meeting probabilities, calculated from the figures above.",
     "Close notes, dashboards", "With each close note"),
]


def sources_page():
    rows = "".join(
        f'<li><h3><a href="{url}">{name}</a></h3><p>{what}</p>'
        f'<dl class="src-meta"><dt>Used in</dt><dd>{used}</dd><dt>Updated</dt><dd>{when}</dd></dl></li>'
        for name, url, what, used, when in DATA_SOURCES)
    body = f"""<main id="main" class="page">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Data sources</h1>
      <p class="lede">Where every figure on Andra Markets comes from, where it is used and how often it is read. Every chart and table also names its source and date.</p>
    </header>
    <div class="page__body">
      <section aria-labelledby="src-list"><h2 id="src-list">Sources</h2><ul class="src-list">{rows}</ul></section>
      <section aria-labelledby="src-rules"><h2 id="src-rules">Rules we follow</h2>
        <ul class="ruled">
          <li>Every figure is dated and sourced, or it is a placeholder. Nothing is estimated to fill a gap.</li>
          <li>Each instrument is taken at its own official close.</li>
          <li>When a source fails, its last good figures stay up with their own date until the next good read.</li>
          <li>No consensus forecasts: there is no reliable free source.</li>
        </ul>
        <p>How the figures become reports is in the <a href="../methodology/">methodology</a>. Data may be delayed or wrong: see the <a href="../legal/#data">legal notice</a>.</p>
      </section>
    </div>
  </div>
</main>"""
    return shell(title="Data sources: Andra Markets",
                 desc="Every data source behind Andra Markets: what it supplies, where it is used and how often it is read.",
                 body=body, home="../", base="../", path="sources/")


def legal_doc(slug, title, lede, sections, updated, desc):
    toc = "".join(f'<li><a href="#{sid}">{heading}</a></li>' for sid, heading, _ in sections)
    secs = "".join(f'<section aria-labelledby="{sid}"><h2 id="{sid}">{heading}</h2>{fill(text)}</section>'
                   for sid, heading, text in sections)
    up = dt.date.fromisoformat(updated)
    body = f"""<main id="main" class="page legal">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">{title}</h1>
      <p class="lede">{lede}</p>
    </header>
    <div class="page__body">
      <nav class="legal__toc" aria-labelledby="legal-toc-h"><h2 id="legal-toc-h">On this page</h2><ol>{toc}</ol></nav>
      {secs}
      <p class="legal__updated">Last updated <time datetime="{updated}">{day_long(up)}</time>.</p>
    </div>
  </div>
</main>"""
    return shell(title=f"{title}: Andra Markets", desc=desc, body=body, home="../", base="../", path=f"{slug}/")


def legal_page():
    return legal_doc("legal", "Legal notice",
                     "Andra Markets publishes research for information and education. It is not investment advice. "
                     "This notice applies to every visitor, including in the United States, the United Kingdom and the European Union.",
                     LEGAL, LEGAL_UPDATED,
                     "The Andra Markets legal notice: not investment advice, past performance, data accuracy, intellectual property, and users in the US, UK and EU.")


def privacy_page():
    return legal_doc("privacy", "Privacy and cookies",
                     "Andra Markets collects almost nothing: no accounts, no analytics, no advertising and no cookies of its own.",
                     PRIVACY, PRIVACY_UPDATED,
                     "How Andra Markets handles personal data and cookies: what is stored, which providers serve the site, and your rights.")


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
    pager += f'<a class="link" href="../../research/">Research Library {icon("arrow-right")}</a>'
    standfirst = " ".join(n.get("standfirst", "").split())
    body = f"""<main id="main" class="page report">
  <div class="wrap">
    <article class="report__grid">
      <header class="page__head">
        <h1 class="page__title report__title">{esc(n["headline"])}</h1>
        {f'<p class="lede">{esc(standfirst)}</p>' if standfirst else ""}
        <p class="note__meta">{meta}</p>
        {share_row("note")}
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


# FX -----------------------------------------------------------------------------
#
# Read from .cache/fx/fx.json, written at deploy time by tools/fx_data.py: the
# agent's daily FX analyses that pass every check, and the market table.

FX_DATA = ROOT / ".cache" / "fx" / "fx.json"
FX_GROUPS = [("dollar", "The dollar"), ("major", "G10 majors"), ("em", "Emerging markets")]


def load_fx():
    try:
        fx = json.loads(FX_DATA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for a in (fx.get("analyses") or {}).values():
        a["day"] = dt.date.fromisoformat(a["date"])
    return fx


def fx_level(v, dec):
    return f"{v:,.{dec}f}" if v is not None else "n/a"


def fx_move(v):
    return mv(signed(v, 2, "%")) if v is not None else '<span class="wm-na">n/a</span>'


def fx_table(rows, caption, policy=False):
    """Pairs grouped as the dollar, G10 majors and emerging markets: level and
    moves as each pair is quoted, signed and coloured as rises and falls."""
    body = ""
    for g, title in FX_GROUPS:
        part = [r for r in rows if r.get("group") == g]
        if not part:
            continue
        body += f'<tbody><tr class="fx-tab__group"><th scope="rowgroup" colspan="{7 if policy else 6}">{title}</th></tr>'
        for r in part:
            pol = r.get("policy")
            pol_cell = ""
            if policy:
                pol_cell = (f'<td class="num" data-label="Policy rate">{pol["rate"]:.2f}%'
                            f'<span>{esc(pol["short"])}, {signed(pol["vs_fed_bp"], 0, "bp")} vs Fed</span></td>'
                            if pol and pol.get("vs_fed_bp") is not None else '<td class="num" data-label="Policy rate"><span class="wm-na">n/a</span></td>')
            body += (f'<tr><th scope="row">{esc(r["name"])}<span>{esc(r.get("quote") or "")}</span></th>'
                     f'<td class="num" data-label="Last">{fx_level(r.get("last"), r.get("dec", 4))}</td>'
                     f'<td class="num" data-label="Day">{fx_move(r.get("d1"))}</td>'
                     f'<td class="num" data-label="Week">{fx_move(r.get("w1"))}</td>'
                     f'<td class="num" data-label="Month">{fx_move(r.get("m1"))}</td>'
                     f'<td class="num" data-label="Year to date">{fx_move(r.get("ytd"))}</td>{pol_cell}</tr>')
        body += "</tbody>"
    head = ('<thead><tr><th scope="col">Pair</th><th scope="col" class="num">Last</th><th scope="col" class="num">Day</th>'
            '<th scope="col" class="num">Week</th><th scope="col" class="num">Month</th><th scope="col" class="num">Year to date</th>'
            + ('<th scope="col" class="num">Policy rate</th>' if policy else "") + "</tr></thead>")
    return (f'<div class="fx-tab__wrap"><table class="fx-tab"><caption class="visually-hidden">{caption}</caption>'
            f"{head}{body}</table></div>")


def fx_minutes(a):
    words = a.get("word_count") or sum(len(p.split()) for s_ in a["sections"] for p in s_["paragraphs"])
    return max(1, math.ceil(words / 230))


def fx_meta(a):
    meta = f'<time datetime="{a["date"]}">{day_long(a["day"])}</time>'
    if isinstance(a.get("edition"), int):
        meta += f'<span>Edition {a["edition"]}</span>'
    return meta + f"<span>{fx_minutes(a)} min read</span>"


def fx_page(a, newer, older):
    sections = ""
    if a["takeaways"]:
        sections += ('<section aria-labelledby="fx-take"><h2 id="fx-take">Takeaways</h2><ol class="ruled">'
                     + "".join(f"<li>{esc(t)}</li>" for t in a["takeaways"]) + "</ol></section>")
    for sec in a["sections"]:
        if not sec["paragraphs"]:
            continue
        sid = f'fx-{sec["id"]}'
        title = esc(sec["title"] or sec["id"].title())
        if sec["id"] == "levels":
            content = '<ul class="ruled">' + "".join(f"<li>{esc(p)}</li>" for p in sec["paragraphs"]) + "</ul>"
        else:
            content = "".join(f"<p>{esc(p)}</p>" for p in sec["paragraphs"])
        sections += f'<section aria-labelledby="{sid}"><h2 id="{sid}">{title}</h2>{content}</section>'
    sections += (f'<section aria-labelledby="fx-pairs"><h2 id="fx-pairs">Every pair</h2>'
                 f'{fx_table(a["pairs"], "Every pair on " + day_med(a["day"]), policy=True)}'
                 f'<p class="fx-src">Moves as each pair is quoted: a rise in USD/JPY is a stronger dollar, a rise in EUR/USD a '
                 f'stronger euro. Policy rates as the analysis had them on file, against the top of the Fed\'s range.</p></section>')
    quant = (" This edition was published in quantitative mode: figures without commentary."
             if a["mode"] == "quantitative" else "")
    sections += (f'<section aria-labelledby="fx-src"><h2 id="fx-src">Sources</h2><p>Exchange rates and the dollar index '
                 f'at the session close from Yahoo Finance; the Fed and ECB rates and Treasury yields from FRED. Every '
                 f'figure in this analysis was checked against the session\'s verified fact pack.{quant}</p>'
                 f'<p>For information only. Not investment advice.</p></section>')
    dxy = next((p for p in a["pairs"] if p["key"] == "dxy"), None)
    side_rows = [p for p in a["pairs"] if p["key"] in ("dxy", "eurusd", "usdjpy", "gbpusd", "usdchf", "audusd",
                                                       "usdcny", "usdmxn", "usdbrl", "usdinr")]
    kpis = "".join(f'<li class="kpi__item"><span class="kpi__name">{esc(p["name"])}</span>'
                   f'<span class="kpi__level">{fx_level(p["last"], p["dec"])}</span>'
                   f'<span class="kpi__chg">{fx_move(p["d1"])}</span></li>' for p in side_rows)
    side = (f'<aside class="report__side" aria-labelledby="side-title"><h2 class="report__side-title" id="side-title">'
            f'The session in numbers</h2><ul class="kpi">{kpis}</ul><p class="report__src">Close and daily change, '
            f'{day_med(a["day"])}, as each pair is quoted. Yahoo Finance.</p></aside>') if side_rows else ""
    pager = ""
    if older:
        pager += f'<a class="link" href="../{older["date"]}/">Previous analysis, {day_med(older["day"])} {icon("arrow-right")}</a>'
    if newer:
        pager += f'<a class="link" href="../{newer["date"]}/">Next analysis, {day_med(newer["day"])} {icon("arrow-right")}</a>'
    pager += f'<a class="link" href="../">All FX analyses {icon("arrow-right")}</a>'
    pager += f'<a class="link" href="../../dashboards/fx-majors/">FX dashboard {icon("arrow-right")}</a>'
    pager += f'<a class="link" href="../../reports/{a["date"]}/">The close note for this session {icon("arrow-right")}</a>'
    body = f"""<main id="main" class="page report fx">
  <div class="wrap">
    <article class="report__grid">
      <header class="page__head">
        <p class="dd__crumbs"><a href="../">FX</a> <span aria-hidden="true">/</span> Daily analysis</p>
        <h1 class="page__title report__title">{esc(a["headline"])}</h1>
        {f'<p class="lede">{esc(a["standfirst"])}</p>' if a["standfirst"] else ""}
        <p class="note__meta">{fx_meta(a)}</p>
        <div class="report__share" hidden>
          <button class="btn" type="button" data-share><span class="swap"><span class="swap__a">{icon("link")}Share this analysis</span><span class="swap__b" aria-hidden="true">{icon("check")}Link copied</span></span></button>
          <p class="report__share-status" role="status" aria-live="polite"></p>
        </div>
      </header>
      {side}
      <div class="page__body">{sections}</div>
    </article>
    <nav class="report__pager" aria-label="More FX analyses">{pager}</nav>
  </div>
</main>"""
    return shell(title=f"{esc(a['headline'])}: Andra Markets FX analysis, {day_med(a['day'])}",
                 desc=esc(a["standfirst"] or f"The Andra Markets FX analysis for {day_long(a['day'])}."),
                 body=body, home="../../", base="../../", path=f"fx/{a['date']}/")


FX_RANGES = ["1M", "3M", "6M", "1Y"]


def fx_chips(cls, label, options, default, toggles=False):
    """A labelled chip group: one pressed (a choice, with the glide) or several (toggles)."""
    chips = "".join(f'<button type="button" class="chip" data-v="{v}" aria-pressed="{"true" if (v in default if toggles else v == default) else "false"}">{t}</button>'
                    for v, t in options)
    gid = f"fx-{cls}-l"
    group = (f'<div class="dd__toggles {cls}" role="group" aria-labelledby="{gid}">{chips}</div>' if toggles else
             f'<div class="filters {cls}" role="group" aria-labelledby="{gid}">{chips}</div>')
    return f'<div class="dd__cgroup"><span class="cl__glabel" id="{gid}">{label}</span>{group}</div>'


def fx_charts(fx):
    """The charts under the pairs table: the dollar index, the pairs, the
    moves heatmap and the rate-differential scatter (assets/fx.js)."""
    hist, rows = fx.get("hist"), fx.get("market") or {}
    if not hist or not hist.get("dates"):
        return ""
    pairs = []
    for key, r in rows.items():
        if key not in hist["series"]:
            continue
        name = r["name"]
        ccy = None if key == "dxy" else (name[:3] if name.endswith("/USD") else name[4:7])
        pairs.append({"key": key, "name": name if key != "dxy" else "Dollar index", "quote": r["quote"], "dec": r["dec"],
                      "group": r["group"], "ccy": ccy, "inv": bool(ccy) and name.startswith("USD/")})
    moves = {k: {m: r.get(m) for m in ("d1", "w1", "m1", "ytd")} for k, r in rows.items()}
    payload = json.dumps({"pairs": pairs, "hist": hist, "moves": moves, "rates": fx.get("rates") or {}},
                         separators=(",", ":")).replace("</", "<\\/")
    ranges = lambda d: fx_chips("dd__ranges", "Range", [(r, r) for r in FX_RANGES], d)  # noqa: E731
    others = [(p["key"], p["name"]) for p in pairs if p["key"] != "dxy"]
    rates = fx.get("rates") or {}
    on_file = [p["ccy"] for p in pairs if p["ccy"] and p["ccy"] in rates]
    missing = [p["ccy"] for p in pairs if p["ccy"] and p["ccy"] not in rates]
    us = rates.get("USD")
    scatter = ""
    if us and on_file:
        scatter = f"""<div class="fx-chart" data-chart="scatter">
        <h3 class="fx-chart__title">Moves and rate differentials</h3>
        <p class="fx-chart__lede">Each currency's move against the dollar (up is a stronger currency) against its 3-month interbank rate less the US's. A currency that pays more than the dollar sits to the right.</p>
        <div class="dd__ctl">{fx_chips("fx-per", "Move over", [("d1", "Day"), ("w1", "Week"), ("m1", "Month"), ("ytd", "Year to date")], "m1")}</div>
        <figure class="dd__chart"><div class="dd__plot" role="img" tabindex="0" aria-label="Scatter of each currency's move against its rate differential with the US"></div>
          <figcaption><p class="key dd__key"></p><p class="dd__read" aria-live="polite"></p></figcaption></figure>
        <p class="fx-src">Rates: OECD, 3-month interbank rates, monthly; the US at {us["rate"]:.2f}% ({dt.date.fromisoformat(us["month"] + "-01"):%b %Y}), each currency at its own latest month.{(" No OECD figure for " + ", ".join(missing) + ": left off.") if missing else ""} Moves: Yahoo Finance closes.</p>
      </div>"""
    return f"""<section class="fx-charts" data-fxcharts aria-labelledby="fx-ch-t" hidden>
      <h2 id="fx-ch-t">Charts</h2>
      <div class="fx-chart" data-chart="dxy">
        <h3 class="fx-chart__title">The dollar index</h3>
        <div class="dd__ctl">{ranges("6M")}</div>
        <figure class="dd__chart"><div class="dd__plot" role="img" tabindex="0" aria-label="The dollar index"></div>
          <figcaption><p class="key dd__key"></p><p class="dd__read" aria-live="polite"></p></figcaption></figure>
      </div>
      <div class="fx-chart" data-chart="pairs">
        <h3 class="fx-chart__title">Pairs</h3>
        <div class="dd__ctl">
          {fx_chips("fx-views", "View", [("one", "One pair"), ("cmp", "Compare, rebased to 100")], "one")}
          <div class="fx-one">{fx_chips("fx-pick", "Pair", others, "eurusd")}</div>
          <div class="fx-cmp" hidden>{fx_chips("fx-picks", "Show, up to six", others, ["eurusd", "usdjpy", "gbpusd"], toggles=True)}</div>
          {ranges("6M")}
          <p class="dd__status" role="status" aria-live="polite"></p>
        </div>
        <figure class="dd__chart"><div class="dd__plot" role="img" tabindex="0" aria-label="Pair chart"></div>
          <figcaption><p class="key dd__key"></p><p class="dd__read" aria-live="polite"></p></figcaption></figure>
      </div>
      <div class="fx-chart" data-chart="heat">
        <h3 class="fx-chart__title">Moves</h3>
        <div class="dd__ctl">{fx_chips("fx-mode", "Read as", [("quoted", "Each pair as quoted"), ("ccy", "Each currency against the dollar")], "quoted")}</div>
        <figure class="dd__chart"><div class="dd__plot dd__plot--auto" role="img" tabindex="0" aria-label="Heatmap of moves"></div>
          <figcaption><p class="key dd__key"></p><p class="dd__read" aria-live="polite"></p></figcaption></figure>
      </div>
      {scatter}
      <script type="application/json" id="fx-data">{payload}</script>
    </section>"""


def fx_index(fx):
    rows = list(((fx or {}).get("market") or {}).values())
    items = sorted(((fx or {}).get("analyses") or {}).values(), key=lambda a: a["date"], reverse=True)
    latest = ""
    if items:
        a = items[0]
        latest = (f'<section class="fx-latest" aria-labelledby="fx-latest-t"><h2 class="visually-hidden" id="fx-latest-t">Latest analysis</h2>'
                  f'<article><h3 class="note__title fx-latest__title"><a href="{a["date"]}/">{esc(a["headline"])}</a></h3>'
                  + (f'<p class="fx-latest__sum">{esc(a["standfirst"])}</p>' if a["standfirst"] else "")
                  + f'<p class="note__meta">{fx_meta(a)}</p>'
                  f'<a class="btn" href="{a["date"]}/">Read the analysis {icon("arrow-right")}</a></article></section>')
    market = ""
    if rows:
        dates = sorted({r["date"] for r in rows})
        when = day_med(dt.date.fromisoformat(dates[-1]))
        market = (f'<section class="fx-market" aria-labelledby="fx-market-t"><h2 id="fx-market-t">Majors and emerging markets</h2>'
                  f'{fx_table(rows, "The dollar index, the G10 majors and the main emerging-market pairs")}'
                  f'<p class="fx-src">Last close and moves as each pair is quoted (a rise in USD/JPY is a stronger dollar, a rise '
                  f'in EUR/USD a stronger euro), latest close {when}; a pair whose market was shut shows its own last close. '
                  f'Yahoo Finance, refreshed at each deploy.</p>'
                  f'<a class="link" href="../dashboards/fx-majors/">The FX dashboard: ranges, comparisons and more currencies {icon("arrow-right")}</a></section>')
    archive_html = ""
    if items:
        months = {}
        for a in items:
            months.setdefault((a["day"].year, a["day"].month), []).append(a)
        archive_html = ('<section class="fx-archive" aria-labelledby="fx-arch-t"><h2 id="fx-arch-t">Every analysis</h2><div class="archive">'
                        + "".join(
                            f'<section class="archive__month" aria-labelledby="fx-m-{y}-{m:02d}"><h3 id="fx-m-{y}-{m:02d}">{dt.date(y, m, 1):%B %Y}</h3>'
                            f'<ol class="note-list">' + "".join(
                                f'<li><a href="{a["date"]}/"><time datetime="{a["date"]}">{a["day"].day} {a["day"]:%b}</time>'
                                f'<span class="note-list__title">{esc(a["headline"])}</span>{icon("arrow-right")}</a></li>' for a in rs)
                            + "</ol></section>" for (y, m), rs in months.items())
                        + "</div></section>")
    lede = ("The dollar, the G10 majors and the main emerging-market currencies: a daily analysis after the US close, "
            "with every figure checked, and the latest moves." if items else
            "The dollar, the G10 majors and the main emerging-market currencies, with their latest moves.")
    body = f"""<main id="main" class="page fx-index">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">FX</h1>
      <p class="lede">{lede}</p>
    </header>
    {latest}
    {market or '<p class="dd__pending">Data pending</p>'}
    {fx_charts(fx) if fx else ""}
    {archive_html}
  </div>
</main>"""
    return shell(title="FX: Andra Markets", desc=lede, body=body, home="../", base="../", path="fx/",
                 scripts=("fx.js",) if fx and fx.get("hist") else ())


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
            f"<p>Earnings are the next report of the 200 largest S&amp;P 500 companies (members from State Street's SPY "
            f"holdings), the 200 largest in the STOXX Europe 600 (members from iShares' holdings of its STOXX Europe 600 "
            f"ETF) and the 200 largest listed in Japan, Taiwan, South Korea, Hong Kong, mainland China and India, one "
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
# One page per company in the calendar's earnings universe (the 200 largest in
# the S&P 500, the STOXX Europe 600 and the six Asian markets), from
# .cache/companies/companies.json (tools/company_data.py). Owner-approved
# design, 22 Oct 2026; 600 companies since 28 Oct 2026. assets/company.js draws the charts from the figures
# embedded in each page.

CO_DATA = ROOT / ".cache" / "companies" / "companies.json"
SHORT_SECTOR = {
    "Information Technology": "Technology", "Communication Services": "Communication",
    "Consumer Discretionary": "Consumer discretionary", "Consumer Staples": "Consumer staples",
    "Health Care": "Health care", "Real Estate": "Real estate",
}


# Each market: (chip label, the list it is drawn from, as a phrase).
CO_MARKETS = {"us": ("US", "the S&amp;P 500"), "europe": ("Europe", "the STOXX Europe 600"),
              "asia": ("Asia", "the six Asian markets")}
CUR_SYMBOL = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CNY": "CN¥", "HKD": "HK$", "TWD": "NT$", "KRW": "₩",
              "INR": "₹", "CHF": "CHF ", "DKK": "DKK ", "SEK": "SEK ", "NOK": "NOK ", "PLN": "PLN "}
CUR_NAME = {"USD": "dollars", "EUR": "euros", "GBP": "pounds", "JPY": "yen", "CNY": "yuan", "HKD": "Hong Kong dollars",
            "TWD": "Taiwan dollars", "KRW": "won", "INR": "rupees", "CHF": "Swiss francs", "DKK": "Danish kroner",
            "SEK": "Swedish kronor", "NOK": "Norwegian kroner", "PLN": "zloty"}


def cur_sym(cur):
    return CUR_SYMBOL.get(cur or "USD", f"{cur} ")


def load_companies():
    try:
        data = json.loads(CO_DATA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    co = data.get("companies") or {}
    order = [t for t in data.get("order") or [] if t in co and len(co[t].get("closes") or []) >= 2]
    if not order:
        return None
    usd = data.get("usd") or {"USD": 1.0}
    bench = data.get("bench") or {}
    if "^GSPC" not in bench and data.get("spx"):
        bench["^GSPC"] = data["spx"]  # a cache written before the 600
    for t in order:
        rec = co[t]
        rec.setdefault("market", "us")
        rec.setdefault("bench", "^GSPC")
        rec.setdefault("bench_name", "S&P 500")
        px, fin = rec.get("currency") or "USD", rec.get("fin_currency") or rec.get("currency") or "USD"
        # Reporting currency to the price's: Shell reports in dollars and trades in pounds.
        rec["_fx"] = 1.0 if px == fin else (usd[fin] / usd[px] if usd.get(fin) and usd.get(px) else None)
        rec["_usd"] = usd.get(px)
    return {"order": order, "co": co, "bench": bench}


def co_logo(t):
    """The company's logo file: the official SVG where there is one, else the PNG."""
    for ext in (".svg", ".png"):
        f = CO_DATA.parent / "logos" / f"{t}{ext}"
        if f.exists():
            return f
    return None


def co_slug(t):
    """URL folder: 'nvda', 'asml-as', '7203-t'."""
    return t.lower().replace(".", "-")


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
    # Legal forms off the end, one at a time: 'Samsung Electronics Co., Ltd.', 'Novo Nordisk A/S'.
    form = (r",?\s+(Inc\.?|Incorporated|Corporation|Corp\.?|Company|Co\.?|plc|PLC|N\.V\.|NV|S\.A\.?|SA|S\.p\.A\.|SpA|SE|AG|"
            r"A/S|ASA|AB|\(publ\)|Oyj|Ltd\.?|Limited|LIMITED|Holdings?|Platforms|Technologies|K\.K\.|Tbk)$")
    while True:
        m = re.sub(form, "", n).strip().rstrip(",")
        if m == n or not m:
            break
        n = m
    return {"Alphabet": "Alphabet", "Berkshire Hathaway": "Berkshire Hathaway"}.get(n, n).strip()


def money(v, cur="USD"):
    """$3.96tn, €331.8bn, ¥867m."""
    if v is None:
        return "n/a"
    a = abs(v)
    sign, c = MINUS if v < 0 else "", cur_sym(cur)
    if a >= 1e12:
        return f"{sign}{c}{a / 1e12:,.2f}tn"
    if a >= 1e9:
        return f"{sign}{c}{a / 1e9:,.1f}bn"
    return f"{sign}{c}{a / 1e6:,.0f}m"


def price_txt(v, cur="USD"):
    """$212.40, ₩55,300: won without decimals."""
    return f"{cur_sym(cur)}{v:,.{0 if cur == 'KRW' else 2}f}"


def pct1(v):
    """12.3%, -0.04 as 0.0%, negatives with a true minus."""
    r = round(v, 1)
    if r == 0:
        return "0.0%"
    return f"{MINUS if r < 0 else ''}{abs(r):.1f}%"


def cur_signed(v, cur="USD"):
    return f"{MINUS if v < 0 else ''}{price_txt(abs(v), cur)}"


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
    fx = rec.get("_fx")  # price currency per unit of the reporting currency
    mcap = price * shares if shares else None
    usd = mcap * rec["_usd"] if mcap and rec.get("_usd") else None
    if usd is not None and usd < 1e10:  # a share count in another class (Berkshire)
        mcap = usd = None
    eps = rec.get("ttm_eps")
    debt, cash, eq = rec.get("debt"), rec.get("cash"), rec.get("equity")
    return {
        "price": price, "prev": prev, "date": closes[-1][0],
        "chg": price - prev, "chg_pct": (price / prev - 1) * 100,
        "mcap": mcap, "mcap_usd": usd, "fx": fx,
        "pe": price / (eps * fx) if eps and eps > 0 and fx else None,
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
    """Revenue down to net income for the last fiscal year, in billions of the
    reporting currency: steps that reconcile."""
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


def co_hist(rec):
    """The last fiscal years side by side, in billions of the reporting currency (EPS in units)."""
    ha = rec.get("hist_a") or {}
    years = sorted({d for v in ha.values() for d, _ in v})[-4:]
    if not years:
        return None
    def col(key, scale=1e9, sign=1, dec=2):
        vals = dict(ha.get(key) or [])
        return [None if vals.get(y) is None else round(sign * vals[y] / scale, dec) for y in years]
    return {
        "years": [fy_label(y) for y in years],
        "rev": col("TotalRevenue"), "ni": col("NetIncomeCommonStockholders"),
        "ocf": col("OperatingCashFlow"), "capex": col("CapitalExpenditure"), "fcf": col("FreeCashFlow"),
        "cash": col("CashCashEquivalentsAndShortTermInvestments"), "debt": col("TotalDebt"),
        "equity": col("StockholdersEquity"),
        "div": col("CashDividendsPaid", sign=-1), "buy": col("RepurchaseOfCapitalStock", sign=-1),
        "eps": col("DilutedEPS", scale=1),
    }


def co_quarters(rec):
    hq = rec.get("hist_q") or {}
    rev, eps = dict(hq.get("TotalRevenue") or []), dict(hq.get("DilutedEPS") or [])
    # The quarters with revenue; EPS that Yahoo has not posted yet shows as n/a.
    qs = sorted(rev)[-8:] if len(rev) >= 2 else sorted(eps)[-8:]
    if len(qs) < 2:
        return None
    return {"labels": [fy_label(q) for q in qs],
            "rev": [None if rev.get(q) is None else round(rev[q] / 1e9, 2) for q in qs],
            "eps": [eps.get(q) for q in qs]}


def co_pe_hist(rec):
    """Month-end P/E on the last fiscal year's diluted EPS known at the time."""
    eps = sorted((d, v) for d, v in (rec.get("hist_a") or {}).get("DilutedEPS") or [])
    out = []
    for d, close in rec.get("monthly") or []:
        known = [v for fy, v in eps if fy <= d]
        if known and known[-1] > 0:
            out.append([d, round(close / known[-1], 1)])
    return out if len(out) >= 6 else None


def period_returns(closes):
    """1M, 3M, year to date and 1Y returns (%) from [(date, close)]."""
    if len(closes) < 30:
        return [None] * 4
    last_d, last = closes[-1]
    def back(n):
        return (last / closes[-1 - n][1] - 1) * 100 if len(closes) > n else None
    year = last_d[:4]
    prior = [c for d, c in closes if d < f"{year}-01-01"]
    ytd = (last / prior[-1] - 1) * 100 if prior else None
    return [back(21), back(63), ytd, (last / closes[0][1] - 1) * 100]


def co_mates(t, data):
    """The company's sector in its own market (US, Europe or Asia)."""
    rec = data["co"][t]
    return [x for x in data["order"] if data["co"][x]["sector"] == rec["sector"] and data["co"][x]["market"] == rec["market"]]


def co_bench(rec, data):
    return [tuple(p) for p in data["bench"].get(rec["bench"]) or []]


def co_returns(t, data):
    rec = data["co"][t]
    sector = rec["sector"]
    mates = co_mates(t, data)
    rows = [(co_name(rec), period_returns(rec["closes"]))]
    if len(mates) >= 3:
        rs = [period_returns(data["co"][x]["closes"]) for x in mates]
        avg = [None if any(r[i] is None for r in rs) else sum(r[i] for r in rs) / len(rs) for i in range(4)]
        rows.append((f"{SHORT_SECTOR.get(sector, sector)} average ({len(mates)})", avg))
    bench = co_bench(rec, data)
    if bench:
        rows.append((esc(rec["bench_name"]), period_returns(bench)))
    return rows


def co_risk(rec, spx):
    """Annualised volatility, beta to the benchmark, the year's deepest fall and its path."""
    closes = rec["closes"]
    if len(closes) < 60:
        return None
    sp = {d: c for d, c in spx}
    rows = [(d, c, sp.get(d)) for d, c in closes]
    r, m = [], []
    for (d0, c0, s0), (d1, c1, s1) in zip(rows, rows[1:]):
        r.append(c1 / c0 - 1)
        if s0 and s1:
            m.append((c1 / c0 - 1, s1 / s0 - 1))
    mean = sum(r) / len(r)
    vol = math.sqrt(sum((x - mean) ** 2 for x in r) / (len(r) - 1)) * math.sqrt(252) * 100
    beta = None
    if len(m) > 60:
        ma = sum(b for _, b in m) / len(m)
        sa = sum(a for a, _ in m) / len(m)
        cov = sum((a - sa) * (b - ma) for a, b in m) / (len(m) - 1)
        var = sum((b - ma) ** 2 for _, b in m) / (len(m) - 1)
        beta = cov / var if var else None
    peak, peak_d, mdd, mdd_peak, mdd_d, dd = closes[0][1], closes[0][0], 0.0, closes[0][0], closes[0][0], []
    for d, c in closes:
        if c > peak:
            peak, peak_d = c, d
        x = (c / peak - 1) * 100
        dd.append([d, round(x, 2)])
        if x < mdd:
            mdd, mdd_peak, mdd_d = x, peak_d, d
    spx_vol = None
    if len(spx) > 60:
        sr = [spx[i + 1][1] / spx[i][1] - 1 for i in range(len(spx) - 1)]
        sm = sum(sr) / len(sr)
        spx_vol = math.sqrt(sum((x - sm) ** 2 for x in sr) / (len(sr) - 1)) * math.sqrt(252) * 100
    return {"vol": vol, "spx_vol": spx_vol, "beta": beta, "mdd": mdd, "mdd_from": mdd_peak, "mdd_to": mdd_d,
            "now": dd[-1][1], "dd": dd}


def co_comp(flow):
    """Where revenue goes: costs, tax and other deductions, and what is left as net income."""
    if not flow or flow[-1][0] != "Net income":
        return None
    rev = flow[0][1]
    parts, extra = [], 0.0
    for f in flow[1:-1]:
        if len(f) > 2 and f[2] == "total":
            continue
        if f[1] < 0:
            parts.append([f[0], round(-f[1], 2)])
        else:
            extra += f[1]
    return {"rev": rev, "parts": parts, "extra": round(extra, 2), "ni": flow[-1][1]}


def returns_table(rows):
    head = "".join(f'<th scope="col" class="num">{h}</th>' for h in ("1 month", "3 months", "Year to date", "1 year"))
    body = []
    for i, (label, vals) in enumerate(rows):
        cells = "".join(f'<td class="num">{mv(signed(v, 1, "%")) if v is not None else "n/a"}</td>' for v in vals)
        cls = ' class="co-ret__self"' if i == 0 else ""
        body.append(f'<tr{cls}><th scope="row">{label}</th>{cells}</tr>')
    return (f'<div class="co-tab__wrap"><table class="co-ret"><thead><tr><th scope="col"><span class="visually-hidden">Series</span></th>'
            f'{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>')


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
    market = rec["market"]
    where = CO_MARKETS.get(market, CO_MARKETS["us"])[1]
    cur, fcur, fx = rec.get("currency") or "USD", rec.get("fin_currency") or rec.get("currency") or "USD", m["fx"]
    fmoney = lambda v: money(v, fcur)  # noqa: E731  a figure from the reports
    in_bn = f"in billions of {CUR_NAME.get(fcur, fcur)}"
    bench_name = esc(rec["bench_name"])
    peers_all = co_mates(t, data)
    if len(peers_all) >= 4:
        peers = peers_all
        peers_lede = (f"{name} (filled) against the other {len(peers) - 1} {SHORT_SECTOR.get(sector, sector).lower()} "
                      f"companies among the 200 largest in {where}. Tap or hover a dot to read it.")
    else:
        peers = [x for x in data["order"] if data["co"][x]["market"] == market]
        peers_lede = (f"{name} (filled) against the 200 largest companies in {where}; too few in its sector "
                      f"to compare on their own. Tap or hover a dot to read it.")
    flow = co_flow(rec)
    cagr, _ = co_cagr(rec)
    bench = co_bench(rec, data)
    risk = co_risk(rec, bench)
    can_dcf = rec.get("dcf") and m["fcf"] and m["fcf"] > 0 and rec.get("shares") and m["mcap"] and fx
    payload = {
        "t": t, "name": name, "price": m["price"], "date": m["date"],
        "cur": cur_sym(cur), "pd": 0 if cur == "KRW" else 2, "fcur": cur_sym(fcur), "bn": rec["bench_name"],
        "peers": [co_peer_row(x, data["co"][x]) for x in peers],
        "comp": co_comp(flow), "fy": fy,
        "years": co_hist(rec), "quarters": co_quarters(rec), "pe": co_pe_hist(rec),
        "risk": None,
        # The model runs in the price's currency, so its value per share sits beside the close.
        "dcf": {"fcf": round(m["fcf"] * fx / 1e9, 3), "net_debt": round((m["net_debt"] or 0) * fx / 1e9, 3),
                "shares": round(rec["shares"] / 1e9, 4), "cagr": None if cagr is None else round(cagr, 1)} if can_dcf else None,
        "hist": [[dd, c] for dd, c in rec["closes"]],
        "bench": [[dd, c] for dd, c in bench],
    }
    if risk:
        payload["risk"] = {"dd": risk["dd"]}
    json_payload = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")

    chg = f'{mv(("+" if m["chg"] >= 0 else MINUS) + price_txt(abs(m["chg"]), cur))} ({mv(signed(m["chg_pct"], 2, "%"))})'
    lede = f"{SHORT_SECTOR.get(sector, sector)}{(', ' + esc(rec['industry'])) if rec.get('industry') else ''}. Revenue of {fmoney(m['rev'])} in the year to {fy}"
    if m["revg"] is not None:
        lede += f", {'up' if m['revg'] >= 0 else 'down'} {abs(m['revg']):.1f}%"
    if m["om"] is not None:
        lede += f", with an operating margin of {pct1(m['om'])}"
    lede += "."

    kp = [
        kpi("Market value", money(m["mcap"], cur), (f'{rec["shares"] / 1e9:.2f}bn shares' + (f', {money(m["mcap_usd"])}' if cur != "USD" else ""))
            if m["mcap"] else "Not shown: share classes"),
        kpi("P/E, last 12 months", f'{m["pe"]:.1f}x' if m["pe"] else "n/a",
            f'EPS {cur_signed(rec["ttm_eps"], fcur)}' if rec.get("ttm_eps") is not None else "No EPS yet"),
        kpi("Revenue growth", mv(signed(m["revg"], 1, "%")) if m["revg"] is not None else "n/a", f"Year to {fy}"),
        kpi("Operating margin", pct1(m["om"]) if m["om"] is not None else "n/a", f"Year to {fy}" if m["om"] is not None else "Not reported for banks"),
    ]
    if rec.get("dcf"):
        kp += [
            kpi("Free cash flow", fmoney(m["fcf"]), f"After {fmoney(abs(m['capex']))} capex" if m["capex"] else f"Year to {fy}"),
            kpi("Net debt" if (m["net_debt"] or 0) >= 0 else "Net cash", fmoney(abs(m["net_debt"])) if m["net_debt"] is not None else "n/a",
                f"{fmoney(m['debt'])} debt, {fmoney(m['cash'])} cash" if m["debt"] is not None else ""),
        ]
    else:
        # A lender's cash flow and debt are its customers' money: show earnings and book value instead.
        eq = rec.get("equity")
        kp += [
            kpi("Net income", fmoney(m["ni"]), f"Year to {fy}"),
            kpi("Shareholders' equity", fmoney(eq), f"Price to book {m['mcap'] / (eq * fx):.1f}x" if m["mcap"] and eq and eq > 0 and fx else "Book value"),
        ]
    kp += [
        kpi("Dividend yield", f'{m["dy"]:.2f}%' if m["dy"] else "None", f'{price_txt(rec["div_ttm"], cur)} a share, last 12 months' if m["dy"] else "No dividend in the last year"),
        kpi("52-week range", f'{cur_sym(cur)}{rec["low52"]:,.0f}&ndash;{rec["high52"]:,.0f}' if rec.get("low52") else "n/a", f"Close {price_txt(m['price'], cur)}"),
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
        <p class="co-src">Base: free cash flow of {fmoney(m["fcf"])} in the year to {fy}, {"net debt" if (m["net_debt"] or 0) >= 0 else "net cash"} of {fmoney(abs(m["net_debt"] or 0))}, {rec["shares"] / 1e9:.2f}bn shares.{f" Converted to {CUR_NAME.get(cur, cur)} at today&rsquo;s rate, the currency the shares trade in." if fcur != cur else ""} Growth fades in a straight line from year 6 to year 10. An Andra Markets model, not a recommendation.</p>"""
    elif not rec.get("dcf"):
        val = ("<p>Not modelled on cash flow. A bank's, insurer's or asset manager's cash flows are mostly its customers' "
               "money, so a free cash flow model says little about its value. Its P/E and dividend sit in the peer "
               "comparison above.</p>")
    else:
        val = (f"<p>Not modelled yet: free cash flow was {fmoney(m['fcf'])} in the year to {fy}, and a cash flow model "
               "needs a positive starting point to mean anything.</p>")

    comp = co_comp(flow)
    if comp and comp["rev"] > 0:
        keep = comp["ni"] / comp["rev"] * 100
        c = cur_sym(fcur)
        if comp["ni"] >= 0:
            comp_line = f"Of every {c}100 of revenue in the year to {fy}, {esc(name)} kept {c}{keep:.0f} as net income."
        else:
            comp_line = f"In the year to {fy} costs exceeded revenue: {esc(name)} lost {c}{-keep:.0f} for every {c}100 of revenue."
        if comp["extra"] > 0:
            comp_line += f" That includes {fmoney(comp['extra'] * 1e9)} of income on top of revenue, such as interest and investment gains."
        flow_sec = (f'<p class="co-lead">{comp_line}</p><div class="co-chart" id="co-flow"></div>'
                    f'<p class="co-src">Annual report for the year to {fy}, via Yahoo Finance. Items under 0.5% of revenue are folded into the next line.</p>')
    else:
        flow_sec = "<p>Data pending.</p>"
    logo_html = ""
    logo_file = co_logo(t)
    if logo_file:
        logo_html = f'<span class="co-logo"><img src="logo{logo_file.suffix}" alt="{esc(name)} logo" width="200" height="200"></span>'
    hist = co_hist(rec)
    quarters = co_quarters(rec)
    pe_hist = co_pe_hist(rec)
    rets = co_returns(t, data)
    nyears = len(hist["years"]) if hist else 0

    def sec(key, title, inner):
        return f'<section aria-labelledby="co-{key}-t"><h2 id="co-{key}-t">{title}</h2>{inner}</section>'

    src_ar = "Annual reports, via Yahoo Finance."
    s_years = sec("years", f"Revenue and profit, {nyears} years",
                  f'<p>Revenue and net income each fiscal year, {in_bn}. Tap or hover a year to read it.</p>'
                  f'<div class="co-chart" id="co-years"></div>'
                  f'<p class="key"><span><i class="sw-fill"></i>Revenue</span><span><i class="sw-ink"></i>Net income</span></p>'
                  f'<p class="co-read" id="co-years-read" aria-live="polite"></p><p class="co-src">{src_ar}</p>') if hist else ""
    s_q = ""
    if quarters:
        s_q = sec("q", f"Last {len(quarters['labels'])} quarters",
                  f'<p>Revenue {in_bn} and diluted earnings per share, quarter by quarter.</p>'
                  '<div class="co-pair"><div><h3 class="co-h3">Revenue</h3><div class="co-chart" id="co-qrev"></div></div>'
                  '<div><h3 class="co-h3">Earnings per share</h3><div class="co-chart" id="co-qeps"></div></div></div>'
                  '<p class="co-read" id="co-q-read" aria-live="polite"></p>'
                  '<p class="co-src">Quarterly reports, via Yahoo Finance. Quarters are named by the month they end.</p>')
    s_cash = sec("cash", "Cash flow and investment",
                 f'<p>Cash from operations, what went into capital spending, and the free cash flow left, {in_bn}.</p>'
                 '<div class="co-chart" id="co-cash"></div>'
                 '<p class="key"><span><i class="sw-fill"></i>Cash from operations</span><span><i class="sw-down"></i>Capital spending</span><span><i class="sw-ink"></i>Free cash flow</span></p>'
                 f'<p class="co-read" id="co-cash-read" aria-live="polite"></p><p class="co-src">{src_ar}</p>') if hist else ""
    s_bs = sec("bs", "Balance sheet",
               f'<p>Cash and short-term investments, debt and shareholders&rsquo; equity at each fiscal year end, {in_bn}.</p>'
               '<div class="co-chart" id="co-bs"></div>'
               '<p class="key"><span><i class="sw-fill"></i>Cash and investments</span><span><i class="sw-ink"></i>Debt</span><span><i class="sw-hollow"></i>Equity</span></p>'
               f'<p class="co-read" id="co-bs-read" aria-live="polite"></p><p class="co-src">{src_ar} Debt excludes leases.</p>') if hist else ""
    s_sh = sec("sh", "Returns to shareholders",
               f'<p>Dividends paid and shares bought back each fiscal year, against net income, {in_bn}.</p>'
               '<div class="co-chart" id="co-sh"></div>'
               '<p class="key"><span><i class="sw-ink"></i>Dividends</span><span><i class="sw-fill"></i>Buybacks</span><span><i class="k-solid"></i>Net income</span></p>'
               f'<p class="co-read" id="co-sh-read" aria-live="polite"></p><p class="co-src">{src_ar}</p>') if hist else ""
    s_pe = sec("pe", "Valuation over time",
               '<p>The price to earnings ratio at each month end, on the last fiscal year&rsquo;s diluted earnings per share known at the time, against its average over the period.</p>'
               '<div class="co-chart" id="co-pe"></div>'
               '<p class="key"><span><i class="k-solid"></i>P/E</span><span><i class="k-dash"></i>Average</span></p>'
               '<p class="co-read" id="co-pe-read" aria-live="polite"></p>'
               '<p class="co-src">Month-end closes and annual reports, via Yahoo Finance.</p>') if pe_hist else ""
    s_ret = sec("ret", "Share price returns",
                f'<p>Price change over each period to the close of {day_med(d)}, without dividends.</p>{returns_table(rets)}'
                f'<p class="co-src">Yahoo Finance daily closes, in {CUR_NAME.get(cur, cur)}. The sector average is the simple average of its companies among the 200 largest in {where}.</p>')
    s_risk = ""
    if risk:
        beta = f'{risk["beta"]:.2f}' if risk["beta"] is not None else "n/a"
        spx_vol = f'; the {bench_name} moved {risk["spx_vol"]:.0f}%' if risk.get("spx_vol") else ""
        vol_txt = f'{risk["vol"]:.0f}%'
        fall_dates = f'{day_med(dt.date.fromisoformat(risk["mdd_from"]))} to {day_med(dt.date.fromisoformat(risk["mdd_to"]))}'
        below = mv(signed(risk["now"], 1, "%")) if risk["now"] < -0.05 else "At its high"
        figs = ('<ul class="kpi co-risk">'
                + kpi("Volatility, 1 year", vol_txt, "Annualised daily moves" + spx_vol)
                + kpi(f"Beta to the {bench_name}", beta, "1.0 moves with the market")
                + kpi("Deepest fall, 1 year", mv(signed(risk["mdd"], 1, "%")), fall_dates)
                + kpi("Below its high", below, "Against the year&rsquo;s highest close")
                + '</ul>')
        s_risk = sec("risk", "Risk",
                     f'<p>How much the shares move, and how far they have fallen from their high over the past year.</p>{figs}'
                     '<div class="co-chart" id="co-dd"></div><p class="co-read" id="co-dd-read" aria-live="polite"></p>'
                     f'<p class="co-src">Yahoo Finance daily closes. Beta from daily returns against the {bench_name}.</p>')

    spx_note = "" if bench else f" The {bench_name} series is pending."
    # US companies: the live price, news and analysts from the profile API.
    live = market == "us" and bool(PROFILE_API)
    live_attrs = (f' data-mode="company" data-api="{esc(PROFILE_API)}" data-t="{fin_ticker(t)}" data-name="{esc(name)}"'
                  f' data-exchange="{esc(rec.get("exchange") or "")}"') if live else ""
    ids = (lambda k: f' id="pf-{k}"') if live else (lambda k: "")
    s_live = pf_news_analysts(esc(name)) if live else ""
    body = f"""<main id="main" class="page dd co" data-co{live_attrs}>
  <div class="wrap dd__grid">
    <header class="page__head dd__head{" co-head--logo" if logo_html else ""}">
      <p class="dd__crumbs"><a href="../">Companies</a> <span aria-hidden="true">/</span> {SHORT_SECTOR.get(sector, sector)}</p>
      <h1 class="page__title">{esc(name)}</h1>
      {logo_html}
      <p class="co-quote"><span class="co-px"{ids("px")}>{price_txt(m["price"], cur)}</span><span class="co-chg"{ids("chg")}>{chg} on the day</span><span class="note__meta"{ids("qmeta")}>{t}, {esc(rec.get("exchange") or "")}. Close {day_med(d)}.</span></p>
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
      {s_pe}
      <section aria-labelledby="co-flow-t">
        <h2 id="co-flow-t">Where revenue goes</h2>
        {flow_sec}
      </section>
      {s_years}
      {s_q}
      {s_cash}
      {s_bs}
      {s_sh}
      {s_ret}
      <section aria-labelledby="co-ctx-t">
        <h2 id="co-ctx-t">Against the market</h2>
        <p>{esc(name)} and the {bench_name} over the past year, both rebased to 100, each in its own currency.{spx_note}</p>
        <div class="co-chart" id="co-ctx"></div>
        <p class="key"><span><i class="k-solid"></i>{esc(name)}</span><span><i class="k-dash"></i>{bench_name}</span></p>
        <p class="co-read" id="co-ctx-read" aria-live="polite"></p>
        <p class="co-src">Yahoo Finance, daily closes to {day_med(d)}.</p>
      </section>
      {s_risk}
      {s_live}
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
        body=body, home=base, base=base, path=f"companies/{co_slug(t)}/", scripts=("company.js", "profile.js") if live else ("company.js",),
    )


def companies_index(data):
    sectors, markets = {}, {}
    for t in data["order"]:
        sectors.setdefault(data["co"][t]["sector"], []).append(t)
        markets.setdefault(data["co"][t]["market"], []).append(t)
    order = sorted(sectors, key=lambda s: (-len(sectors[s]), s))
    n = len(data["order"])
    chips = (f'<button type="button" class="chip" data-cofilter="all" aria-pressed="true">All sectors <span class="chip__n">{n}</span></button>'
             + "".join(f'<button type="button" class="chip" data-cofilter="{slug_s(s)}" aria-pressed="false">{SHORT_SECTOR.get(s, s)} '
                       f'<span class="chip__n">{len(sectors[s])}</span></button>' for s in order))
    mchips = (f'<button type="button" class="chip" data-comarket="all" aria-pressed="true">All markets <span class="chip__n">{n}</span></button>'
              + "".join(f'<button type="button" class="chip" data-comarket="{k}" aria-pressed="false">{label} '
                        f'<span class="chip__n">{len(markets[k])}</span></button>' for k, (label, _) in CO_MARKETS.items() if k in markets))
    # One ranking across the three markets: market value in dollars.
    ms = {t: co_metrics(data["co"][t]) for t in data["order"]}
    ranked = sorted(data["order"], key=lambda t: -(ms[t]["mcap_usd"] or data["co"][t].get("cap") or 0))
    rows = []
    last = None
    for i, t in enumerate(ranked, 1):
        rec, m = data["co"][t], ms[t]
        last = max(last or m["date"], m["date"])
        pe_txt = f'{m["pe"]:.1f}x' if m["pe"] else "n/a"
        usd = m["mcap_usd"] or rec.get("cap")
        rows.append(
            f'<tr data-sector="{slug_s(rec["sector"])}" data-market="{rec["market"]}" data-t="{fin_ticker(t) if rec["market"] == "us" else t}" '
            f'data-q="{esc(" ".join(sorted({t.lower(), fin_ticker(t).lower()})) + " " + html.unescape(co_name(rec)).lower())}"><td class="co-tab__rank">{i}</td>'
            f'<td class="co-tab__name"><a href="{co_slug(t)}/">{esc(co_name(rec))}</a><span>{t}</span></td>'
            f'<td class="co-tab__sec" data-label="Sector">{SHORT_SECTOR.get(rec["sector"], rec["sector"])}</td>'
            f'<td class="num" data-label="Close">{price_txt(m["price"], rec.get("currency") or "USD")}</td>'
            f'<td class="num" data-label="Day">{mv(signed(m["chg_pct"], 2, "%"))}</td>'
            f'<td class="num" data-label="Value">{money(usd)}</td>'
            f'<td class="num" data-label="P/E">{pe_txt}</td></tr>')
    body = f"""<main id="main" class="page co-index" data-mode="index" data-api="{esc(PROFILE_API)}">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Companies</h1>
      <p class="lede">The 200 largest companies in the S&amp;P 500, in the STOXX Europe 600 and across the six Asian markets, the companies the earnings calendar follows, ranked by market value in dollars. Each has a page with its valuation, its peers, where its revenue goes and how the shares have done against the market. Search finds any other US-listed company too.</p>
    </header>
    <form class="pf-field co-index__search" role="search" id="pf-form" hidden>
      {icon("magnifying-glass")}
      <input type="search" id="pf-q" name="q" aria-label="Search companies by ticker or name" placeholder="Search by ticker or name, any US-listed company" role="combobox" aria-expanded="false" aria-controls="pf-res" aria-autocomplete="list" autocomplete="off" spellcheck="false">
      <kbd>Enter</kbd>
    </form>
    <p class="pf-status" id="pf-status" role="status" aria-live="polite"></p>
    <div class="pf-more" id="pf-more" hidden>
      <h2 class="pf-more__h" id="pf-more-h">Other US-listed companies</h2>
      <ul class="pf-list" id="pf-res" role="listbox" aria-labelledby="pf-more-h"></ul>
    </div>
    <div class="filters" role="group" aria-label="Filter companies by market">{mchips}</div>
    <div class="filters" role="group" aria-label="Filter companies by sector">{chips}</div>
    <p class="filters__status co-index__status" role="status" aria-live="polite">Showing all {n} companies</p>
    <div class="co-tab__wrap">
      <table class="co-tab">
        <thead><tr><th scope="col"><span class="visually-hidden">Rank</span></th><th scope="col">Company</th><th scope="col">Sector</th><th scope="col" class="num">Close</th><th scope="col" class="num">Day</th><th scope="col" class="num">Market value</th><th scope="col" class="num">P/E</th></tr></thead>
        <tbody>{"".join(rows)}</tbody>
      </table>
    </div>
    <p class="co-src">Members: State Street SPY holdings (US), iShares STOXX Europe 600 holdings (Europe) and Yahoo Finance's screener for Japan, Taiwan, South Korea, Hong Kong, mainland China and India (Asia). Prices and figures: Yahoo Finance, latest close to {day_med(dt.date.fromisoformat(last))}. Closes in each company's own currency; market value in dollars at today's rates. P/E on the last four quarters' diluted EPS, or the last fiscal year's where a company reports half-yearly.</p>
  </div>
</main>"""
    return shell(title="Companies: Andra Markets",
                 desc="The 200 largest companies in the US, Europe and Asia, each with valuation, peers and results.",
                 body=body, home="../", base="../", path="companies/", scripts=("profile.js",))


# World markets ------------------------------------------------------------------

WORLD_DATA = ROOT / ".cache" / "world" / "world.json"
# Axis key -> (label, short label for the radar, unit, is a move (red/green), note).
WORLD_AXIS = {
    "ret1m": ("Index return, 1 month", "1M return", "%", True, "The main index's price change over the last month, in local currency."),
    "ytd": ("Index return, year to date", "YTD return", "%", True, "The main index's price change since the last close of last year, in local currency."),
    "vol3m": ("Volatility, 3 months", "Volatility", "%", False, "Annualised standard deviation of the index's daily returns over three months."),
    "fx": ("Currency against the dollar", "Currency", "%", True, "Change in the dollar value of the local currency since the end of last year: above zero, the currency gained."),
    "y10": ("10-year government bond yield", "10Y yield", "%", False, "Long-term government bond yield, monthly average."),
    "gdp": ("GDP growth", "GDP growth", "%", False, "Real GDP growth in the latest year the source has published."),
    "cpi": ("Inflation", "Inflation", "%", False, "Consumer prices, year on year: the latest month where it is recent, else the latest year."),
    "unemp": ("Unemployment", "Unemployment", "%", False, "Unemployment rate: the latest month where it is recent, else the latest year."),
}
WORLD_DEFAULT = ["USA", "DEU", "JPN"]


def load_world():
    try:
        w = json.loads(WORLD_DATA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return w if w.get("figures") else None


def world_when(rec):
    """A figure's date as printed: a day, a month or a year."""
    d = rec["date"]
    if len(d) == 10:
        return day_med(dt.date.fromisoformat(d))
    if len(d) == 7:
        return f"{dt.date.fromisoformat(d + '-01'):%b %Y}"
    return d


def world_fig(axis, rec):
    """A figure in its table cell: moves signed and coloured, levels in ink."""
    if not rec:
        return '<span class="wm-na">No figure</span>'
    label, _, unit, move, _ = WORLD_AXIS[axis]
    txt = signed(rec["v"], 2, unit) if move else f'{rec["v"]:.2f}{unit}'.replace("-", MINUS)
    return mv(txt) if move else txt


def world_scale(figs):
    """Each axis's lowest and highest figure across the markets: the radar's shared scale."""
    out = {}
    for a in WORLD_AXES:
        vals = [(f[a]["v"], iso) for iso, f in figs.items() if a in f]
        if vals:
            out[a] = {"lo": min(vals)[0], "hi": max(vals)[0], "lo_m": min(vals)[1], "hi_m": max(vals)[1]}
    return out


def world_mini(iso, figs, scale):
    """A small static radar of one market, on the shared scale."""
    size, c, R = 120, 60, 46
    n = len(WORLD_AXES)
    rings = "".join(f'<circle class="grid-line wm-ring" cx="{c}" cy="{c}" r="{R * k / 4:.1f}"/>' for k in (1, 2, 3, 4))
    spokes, pts = "", []
    for i, a in enumerate(WORLD_AXES):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        spokes += f'<line class="grid-line" x1="{c}" y1="{c}" x2="{c + R * math.cos(ang):.1f}" y2="{c + R * math.sin(ang):.1f}"/>'
        rec, sc = figs.get(iso, {}).get(a), scale.get(a)
        if rec and sc:
            t = 0.5 if sc["hi"] == sc["lo"] else (rec["v"] - sc["lo"]) / (sc["hi"] - sc["lo"])
            r = R * (0.12 + 0.88 * t)
            pts.append((c + r * math.cos(ang), c + r * math.sin(ang)))
        else:
            pts.append(None)
    # Draw only between neighbouring axes that both have a figure.
    segs = ""
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        if a and b:
            segs += f'<line class="wm-edge" x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>'
    # Each point names what it measures (a native tooltip; world.js adds a readout).
    dots = "".join(
        f'<circle class="dot" cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="2.2"><title>{WORLD_AXIS[a][1]}: '
        f'{html.unescape(re.sub(r"<[^>]+>", "", world_fig(a, figs[iso][a])))}, {world_when(figs[iso][a])}</title></circle>'
        for a, p in zip(WORLD_AXES, pts) if p)
    return (f'<svg class="chart wm-mini__svg" viewBox="0 0 {size} {size}" aria-hidden="true">'
            f'{rings}{spokes}{segs}{dots}</svg>')


def world_page(w):
    names = {m[0]: m[1] for m in WORLD_MARKETS}
    index = {m[0]: m[3] for m in WORLD_MARKETS}
    figs = w["figures"] if w else {}
    if not w:
        body = """<main id="main" class="page dd">
  <div class="wrap dd__grid">
    <header class="page__head dd__head"><h1 class="page__title">World markets</h1>
      <p class="lede">Twenty-five markets compared on the same scale.</p><p class="note__meta">Data pending.</p></header>
    <section class="dd__main"><div class="dd__plot dd__plot--pending"><p class="dd__pending">Data pending</p></div></section>
  </div>
</main>"""
        return shell(title="World markets: Andra Markets", desc="Twenty-five markets compared on the same scale.",
                     body=body, home="../", base="../", path="world/")
    scale = world_scale(figs)
    updated = dt.datetime.fromisoformat(w["updated"]).astimezone(NY)
    chips = "".join(
        f'<button type="button" class="chip" data-m="{iso}" aria-pressed="{"true" if iso in WORLD_DEFAULT else "false"}">{esc(nm)}</button>'
        for iso, nm, *_ in WORLD_MARKETS)
    payload = json.dumps({
        "axes": [{"k": a, "label": WORLD_AXIS[a][0], "short": WORLD_AXIS[a][1], "unit": WORLD_AXIS[a][2], "move": WORLD_AXIS[a][3]}
                 for a in WORLD_AXES],
        "markets": [{"iso": iso, "name": nm, "index": idx} for iso, nm, _, idx, *_ in WORLD_MARKETS],
        "figures": {iso: {a: {"v": r["v"], "when": world_when(r), "src": r["src"]} for a, r in f.items() if a in WORLD_AXIS}
                    for iso, f in figs.items()},
        "scale": scale, "start": WORLD_DEFAULT}, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    ranges = "".join(
        f'<li class="kpi__item"><span class="kpi__name">{WORLD_AXIS[a][1]}</span>'
        f'<span class="kpi__level">{world_fig(a, {"v": sc["lo"]})} to {world_fig(a, {"v": sc["hi"]})}</span>'
        f'<span class="kpi__chg">{esc(names[sc["lo_m"]])} to {esc(names[sc["hi_m"]])}</span></li>'
        for a, sc in scale.items())
    minis = "".join(
        f'<li><button type="button" class="wm-mini" data-m="{iso}" aria-pressed="{"true" if iso in WORLD_DEFAULT else "false"}">'
        f'{world_mini(iso, figs, scale)}<span class="wm-mini__name">{esc(names[iso])}</span>'
        f'<span class="wm-mini__idx">{esc(index[iso])}</span>'
        f'<span class="wm-mini__read" aria-hidden="true"></span></button></li>'
        for iso in names)
    head = "".join(f'<th scope="col" class="num">{WORLD_AXIS[a][1]}</th>' for a in WORLD_AXES)
    rows = "".join(
        f'<tr><th scope="row">{esc(names[iso])}<span>{esc(index[iso])}</span></th>'
        + "".join(f'<td class="num">{world_fig(a, figs.get(iso, {}).get(a))}</td>' for a in WORLD_AXES) + "</tr>"
        for iso in names)
    # Each axis's sources, with the dates its figures carry.
    src_rows = []
    for a in WORLD_AXES:
        by = {}
        for iso, f in figs.items():
            if a in f:
                by.setdefault(f[a]["src"], []).append(world_when(f[a]))
        missing = [names[iso] for iso in names if a not in figs.get(iso, {})]
        parts = "; ".join(f"{esc(src)}, {', '.join(sorted(set(ds), key=ds.index)[:3])}{' and others' if len(set(ds)) > 3 else ''}"
                          for src, ds in by.items())
        gap = f" No figure for {', '.join(missing)}: no free official source publishes one." if missing else ""
        if a == "fx" and "United States" in missing:
            gap = gap.replace("United States", "the United States (its currency is the dollar)")
        src_rows.append(f'<li><span>{WORLD_AXIS[a][0]}. {WORLD_AXIS[a][4]} {parts}.{gap}</span></li>')
    body = f"""<main id="main" class="page dd wm" data-world>
  <div class="wrap dd__grid">
    <header class="page__head dd__head">
      <h1 class="page__title">World markets</h1>
      <p class="lede">Twenty-five markets on the same eight measures: how their stock markets and currencies have done, how volatile they are, what their governments pay to borrow, and how their economies are growing, pricing and hiring.</p>
      <p class="note__meta">Yahoo Finance, OECD, World Bank, IMF. Updated {updated.day} {updated:%b %Y}, {updated:%-I:%M} {updated.strftime('%p').lower()} ET.</p>
    </header>
    <section class="dd__main wm-main" aria-label="Compare markets">
      <div class="dd__cgroup"><span class="cl__glabel" id="wm-pick-l">Compare up to three</span>
        <div class="dd__toggles wm-pick" role="group" aria-labelledby="wm-pick-l">{chips}</div></div>
      <p class="dd__status" role="status" aria-live="polite"></p>
      <figure class="dd__chart"><div class="dd__plot wm-plot" role="img" tabindex="0" aria-label="Radar chart of the markets compared"></div>
        <figcaption><p class="key dd__key"></p><p class="dd__read" aria-live="polite"></p></figcaption></figure>
      <noscript><p class="dd__pending">The radar needs JavaScript. Every figure is in the table below.</p></noscript>
      <div class="wm-cmp__wrap"><table class="wm-cmp" hidden><caption class="visually-hidden">The markets compared, each figure with its date and source</caption>
        <thead></thead><tbody></tbody></table></div>
      <script type="application/json" id="wm-data">{payload}</script>
    </section>
    <aside class="report__side dd__side" aria-labelledby="side-title">
      <h2 class="report__side-title" id="side-title">The scale</h2>
      <ul class="kpi wm-scale">{ranges}</ul>
      <p class="report__src">Each axis runs from the lowest figure among the 25 markets, near the centre, to the highest, at the edge.</p>
    </aside>
    <div class="page__body dd__text wm-text">
      <section aria-labelledby="wm-each"><h2 id="wm-each">Each market</h2>
        <ul class="wm-minis">{minis}</ul></section>
      <section aria-labelledby="wm-all"><h2 id="wm-all">Every figure</h2>
        <div class="wm-tab__wrap" tabindex="0"><table class="wm-tab"><caption class="visually-hidden">Eight measures for 25 markets</caption>
          <thead><tr><th scope="col">Market</th>{head}</tr></thead><tbody>{rows}</tbody></table></div></section>
      <section aria-labelledby="wm-how"><h2 id="wm-how">How to read it</h2>
        <p>Each spoke is one measure, scaled from the lowest figure among the 25 markets (near the centre) to the highest (at the edge), so every market is placed against the same range. Outward means a higher figure, not a better one: higher volatility, inflation or unemployment points outward too. A gap in a market's outline is a measure with no figure: none is estimated.</p>
        <p>Stock market and currency figures are daily. The economic figures come out monthly or yearly and are published with a lag, so each one carries its own date in the comparison table, and markets can be compared on different months or years.</p></section>
      <section aria-labelledby="wm-src"><h2 id="wm-src">Sources</h2><ul class="ruled wm-src">{"".join(src_rows)}</ul>
        <p>For information only. Not investment advice.</p></section>
    </div>
  </div>
</main>"""
    return shell(title="World markets: Andra Markets",
                 desc="Twenty-five markets compared on one radar: index returns, volatility, bond yields, currency, growth, inflation and unemployment, each with its official source and date.",
                 body=body, home="../", base="../", path="world/", scripts=("world.js",))


# Fed & Rates (fed-rates/) ---------------------------------------------------------
# Figures from tools/fedrates_data.py (.cache/fedrates/fedrates.json), one block
# per panel, each with its own source and date. A block not fetched yet keeps
# its panel with "Data pending".

FEDRATES_DATA = ROOT / ".cache" / "fedrates" / "fedrates.json"
DOWNLOAD_ICON = ('<svg class="icon" aria-hidden="true" viewBox="0 0 256 256"><path fill="currentColor" d="M224,144v64a8,8,0,0,1-8,8H40a8,'
                 '8,0,0,1-8-8V144a8,8,0,0,1,16,0v56H208V144a8,8,0,0,1,16,0Zm-101.66,5.66a8,8,0,0,0,11.32,0l40-40a8,8,0,0,0-11.32-11.32L136,'
                 '124.69V32a8,8,0,0,0-16,0v92.69L93.66,98.34a8,8,0,0,0-11.32,11.32Z"/></svg>')


def load_fedrates():
    try:
        return json.loads(FEDRATES_DATA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def et_stamp(iso_time):
    """"30 Oct 2026, 2:45 pm ET" from an ISO time."""
    t = dt.datetime.fromisoformat(iso_time).astimezone(NY)
    return f"{day_med(t.date())}, {clock(t)} ET"


def meeting_short(iso_day):
    d = dt.date.fromisoformat(iso_day)
    return f"{d:%b} {d:%y}"


def meeting_days(m):
    a, b = dt.date.fromisoformat(m["first"]), dt.date.fromisoformat(m["last"])
    if a == b:
        return day_med(b)
    if a.month == b.month:
        return f"{a.day} and {b.day} {b:%b %Y}"
    return f"{a.day} {a:%b} and {b.day} {b:%b %Y}"


def bp_name(bp):
    return "Hold" if bp == 0 else f"Cut {abs(bp)} bp" if bp < 0 else f"Hike {bp} bp"


def fr_decision(m, policy):
    """The change in the target range at a past meeting, from the upper bound's history."""
    hist = (policy or {}).get("upper_hist") or {}
    days = sorted(hist)
    before = [d for d in days if d <= m["first"]]
    after = [d for d in days if d > m["last"]]
    if not before or not after:
        return None
    return round((hist[after[0]] - hist[before[-1]]) * 100)


def fr_panel(pid, title, intro, inner, source, save=True):
    btn = (f'<button type="button" class="btn btn--sm btn--ghost fr__save" data-save="{pid}">{DOWNLOAD_ICON}'
           f'<span>Save image</span></button>' if save else "")
    return (f'<section class="fr__panel" id="{pid}" aria-labelledby="{pid}-h">'
            f'<div class="fr__ph"><h2 id="{pid}-h">{title}</h2>{btn}</div>'
            f'<p class="fr__intro">{intro}</p>{inner}<p class="fr__src">{source}</p></section>')


def fr_figure(pid, label):
    return (f'<figure class="dd__chart fr__fig"><div class="dd__plot fr__plot" id="{pid}-plot" role="img" tabindex="0" '
            f'aria-label="{label}"></div><figcaption><p class="key fr__key" id="{pid}-key"></p>'
            f'<p class="dd__read" id="{pid}-read" aria-live="polite"></p></figcaption></figure>')


FR_PENDING = '<div class="dd__plot dd__plot--pending"><p class="dd__pending">Data pending</p></div>'


def fr_payload(d):
    """What assets/fedrates.js draws: the panels' series, dates already formatted."""
    out = {}
    c = d.get("curve")
    if c:
        out["curve"] = {"tenors": c["tenors"], "years": c["years"], "curves": {k: c["curves"][k] for k in ("now", "1W", "1M", "1Y") if k in c["curves"]},
                        "dates": {k: day_med(dt.date.fromisoformat(v)) for k, v in c["dates"].items()}}
        it = d.get("intraday")
        if it and dt.datetime.fromisoformat(it["time"]).astimezone(NY).date() > dt.date.fromisoformat(c["asof"]) \
                and dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(it["time"]) < dt.timedelta(hours=20):
            t = dt.datetime.fromisoformat(it["time"]).astimezone(NY)
            out["curve"]["intra"] = {"label": f"Intraday, {clock(t)} ET", "points": it["points"]}
    o = d.get("odds")
    if o:
        out["path"] = {"meetings": [meeting_short(p["meeting"]) for p in o["path"]], "now": [p["rate"] for p in o["path"]],
                       "ago": (o.get("ago") or {}).get("path"),
                       "ago_label": f'Priced {day_med(dt.date.fromisoformat(o["ago"]["date"]))}' if o.get("ago") else None,
                       "ref": (d.get("policy") or {}).get("effr")}
    for k in ("spreads", "macro", "real"):
        if d.get(k):
            out[k] = {"dates": d[k]["dates"], "series": d[k]["series"]}
    return out


def fr_latest(d):
    """The Latest panel: (name, level, note) rows; levels in ink, moves in red or green."""
    rows = []
    p, c, o, re_, mac = (d.get(k) for k in ("policy", "curve", "odds", "real", "macro"))
    if p:
        lc = p.get("last_change")
        rows.append(("Target range", f'{p["lower"]:.2f} to {p["upper"]:.2f}%',
                     mv(f'{signed(lc["bp"], 0, "bp")} on {short_day(lc["date"])}') if lc else ""))
        rows.append(("Effective rate", pct(p["effr"]), mv(f'{signed((p["effr"] - p["effr_prev"]) * 100, 0, "bp")} on {short_day(p["effr_date"])}')))
    if o:
        top = max(o["probs"], key=lambda x: x["p"])
        rows.append(("Next FOMC", short_day(o["meeting"]), f'{bp_name(top["bp"])} {round(top["p"] * 100)}%'))
    if c:
        i = {lb: n for n, lb in enumerate(c["tenors"])}
        now, prev = c["curves"]["now"], c["curves"]["1D"]
        on = f'on {short_day(c["dates"]["now"])}'
        for lb in ("2Y", "10Y"):
            rows.append((f"{lb} yield", pct(now[i[lb]]), mv(f"{signed((now[i[lb]] - prev[i[lb]]) * 100, 0, 'bp')} {on}")))
        for name, a, b in (("2s10s", "10Y", "2Y"), ("3m10y", "10Y", "3M")):
            v, w = (now[i[a]] - now[i[b]]) * 100, (prev[i[a]] - prev[i[b]]) * 100
            # The spread is a level (ink); its change on the day is a move.
            rows.append((name, signed(v, 0, "bp"), mv(f"{signed(v - w, 0, 'bp')} {on}")))
    if re_:
        for name in ("10Y real", "10Y breakeven"):
            x = re_["latest"][name]
            rows.append((name, pct(x["value"]), mv(f'{signed((x["value"] - x["prev"]) * 100, 0, "bp")} on {short_day(x["date"])}')))
    if mac:
        x = mac["latest"]["Core PCE"]
        rows.append(("Core PCE", pct(x["value"], 1), f'y/y, {month_name(x["month"])}'))
    return rows


def fedrates_page(d):
    p, fomc, o, c = d.get("policy"), d.get("fomc"), d.get("odds"), d.get("curve")
    now = dt.datetime.now(dt.timezone.utc)
    meetings = (fomc or {}).get("meetings") or []
    past = [m for m in meetings if dt.datetime.fromisoformat(m["decision"]) <= now]
    upcoming = [m for m in meetings if dt.datetime.fromisoformat(m["decision"]) > now]
    # Policy and the FOMC
    if p:
        lc = p.get("last_change")
        rate = (f'<div class="fr__rate"><span class="fr__label">Target range</span>'
                f'<span class="fr__big">{p["lower"]:.2f} to {p["upper"]:.2f}%</span>'
                f'<span class="fr__sub">Effective rate {pct(p["effr"])}, {short_day(p["effr_date"])}.'
                + (f' Last change {mv(signed(lc["bp"], 0, "bp"))} on {day_med(dt.date.fromisoformat(lc["date"]))}.' if lc else "")
                + '</span></div>')
    else:
        rate = '<div class="fr__rate"><span class="fr__label">Target range</span><span class="fr__big fr__pending">Data pending</span></div>'
    if upcoming:
        nxt = upcoming[0]
        t = dt.datetime.fromisoformat(nxt["decision"]).astimezone(NY)
        units = "".join(f'<span><b data-cd="{u}">00</b><i>{n}</i></span>' for u, n in (("d", "days"), ("h", "hours"), ("m", "min"), ("s", "sec")))
        nxt_html = (f'<div class="fr__next"><span class="fr__label">Next FOMC decision</span>'
                    f'<span class="fr__big">{day_med(t.date())}, {clock(t)} ET</span>'
                    f'<div class="fr__cd" id="fr-cd" data-target="{nxt["decision"]}" role="timer" aria-label="Time to the decision">{units}</div></div>')
    else:
        nxt_html = '<div class="fr__next"><span class="fr__label">Next FOMC decision</span><span class="fr__big fr__pending">Data pending</span></div>'
    rows = ""
    if past:
        m = past[-1]
        bp = fr_decision(m, p)
        what = "Decided" if bp is None else "Held" if bp == 0 else f"Decided {mv(signed(bp, 0, 'bp'))}"
        rows += f'<li class="is-past"><span>{meeting_days(m)}</span><span>{what}</span></li>'
    for i, m in enumerate(upcoming[:6]):
        note = ("Next" + (", with projections" if m["sep"] else "")) if i == 0 else ("With projections" if m["sep"] else "")
        rows += f'<li{" class=is-next" if i == 0 else ""}><span>{meeting_days(m)}</span><span>{note}</span></li>'
    meet = f'<ol class="fr__meet" aria-label="FOMC meetings">{rows}</ol>' if rows else ""
    pol_src = "; ".join(x for x in ((p or {}).get("source"), (fomc or {}).get("source")) if x) or "Federal Reserve, FRED"
    upd = f' Updated {et_stamp(p["fetched"])}.' if p else ""
    policy = fr_panel("fr-policy", "Policy rate and the FOMC",
                      "The Fed's target range, the rate banks actually lend at overnight, and the next decision.",
                      f'<div class="fr__now">{rate}{nxt_html}</div>{meet}', f"{esc(pol_src)}.{upd}", save=False)
    # What markets price
    if o:
        probs = "".join(f'<li><span class="fr-p__n">{bp_name(x["bp"])}</span><span class="fr-p__bar"><i style="width:{round(x["p"] * 100)}%"></i></span>'
                        f'<span class="fr-p__v">{round(x["p"] * 100)}%</span></li>' for x in o["probs"])
        odds_inner = (f'<div class="fr__probs"><p class="fr__label">Next meeting, {day_med(dt.date.fromisoformat(o["meeting"]))}. '
                      f'Implied change {mv(signed(o["change_bp"], 0, "bp"))}</p><ul>{probs}</ul></div>'
                      + fr_figure("fr-path", "Expected effective rate after each FOMC meeting, implied by fed funds futures"))
        odds_src = f'{o["source"]}, priced {et_stamp(o["time"])} (Yahoo Finance, delayed about 10 minutes); the effective rate from FRED.'
    else:
        odds_inner, odds_src = FR_PENDING, "Andra Markets calculation from CBOT 30-day fed funds futures (Yahoo Finance)."
    odds_p = fr_panel("fr-odds", "What markets price",
                      "Probabilities for the next meeting and the expected rate after each meeting, from fed funds futures.",
                      odds_inner, odds_src, save=bool(o))
    # Curve
    if c:
        toggles = "".join(f'<button type="button" class="chip" data-cmp="{k}" aria-pressed="{"true" if k == "1M" else "false"}">{lb}</button>'
                          for k, lb in (("1W", "1 week ago"), ("1M", "1 month ago"), ("1Y", "1 year ago")) if k in c["curves"])
        curve_inner = (f'<div class="dd__ctl"><div class="dd__cgroup"><span class="cl__glabel" id="cmp-l">Compare with</span>'
                       f'<div class="dd__toggles" role="group" aria-labelledby="cmp-l">{toggles}</div></div></div>'
                       + fr_figure("fr-curve", "US Treasury par yield curve, 1 month to 30 years") + '<div class="fr__chg" id="fr-chg"></div>')
        curve_src = f'{esc(c["source"])}. As of {day_med(dt.date.fromisoformat(c["asof"]))}.'
        if d.get("intraday"):
            curve_src += " Intraday points: Cboe yield indices (13-week bill for 3M) on Yahoo Finance, delayed about 15 minutes."
    else:
        curve_inner, curve_src = FR_PENDING, "US Treasury, daily par yield curve; FRED."
    curve_p = fr_panel("fr-curve", "Treasury yield curve",
                       "Yields from 1 month to 30 years. Compare today's curve with a week, a month and a year ago.",
                       curve_inner, curve_src, save=bool(c))

    def series_panel(key, pid, fig, title, intro, label, extra=""):
        b = d.get(key)
        inner = (extra + fr_figure(fig, label)) if b else FR_PENDING
        asof = dt.date.fromisoformat(b["asof"]) if b else None
        when = (f"Latest month {asof:%b %Y}." if key == "macro" else f"As of {day_med(asof)}.") if b else ""
        return fr_panel(pid, title, intro, inner, f'{esc(b["source"]) if b else "FRED"}. {when}'.strip(), save=bool(b))
    sp_ctl = ('<div class="dd__ctl"><div class="dd__cgroup"><span class="cl__glabel" id="sp-l">Spread</span>'
              '<div class="filters" role="group" aria-labelledby="sp-l">'
              '<button type="button" class="chip" data-sp="0" aria-pressed="true">2s10s</button>'
              '<button type="button" class="chip" data-sp="1" aria-pressed="false">3m10y</button>'
              '<button type="button" class="chip" data-sp="2" aria-pressed="false">Both</button></div></div></div>')
    spreads = series_panel("spreads", "fr-spreads", "fr-sp", "Curve spreads",
                           "10-year less 2-year (2s10s) and 10-year less 3-month (3m10y). Shaded periods: the curve was inverted.",
                           "2s10s and 3m10y Treasury spreads in basis points", sp_ctl)
    macro = series_panel("macro", "fr-macro", "fr-mac", "The Fed against inflation and jobs",
                         "The fed funds rate beside CPI and core PCE inflation (year on year) and the unemployment rate.",
                         "Fed funds rate, CPI and core PCE inflation, and unemployment, monthly")
    real = series_panel("real", "fr-real", "fr-re", "Real rates and breakevens",
                        "The 10-year TIPS yield (the real rate) and the inflation investors price over 5 and 10 years, and 5 years starting 5 years ahead.",
                        "10-year real yield and inflation breakevens")
    ranges = "".join(f'<button type="button" class="chip" data-range="{r}" aria-pressed="{"true" if r == "5Y" else "false"}">{r}</button>'
                     for r in ("1M", "3M", "6M", "1Y", "2Y", "5Y", "10Y", "Max"))
    latest = fr_latest(d)
    kpis = "".join(f'<li class="kpi__item"><span class="kpi__name">{n}</span><span class="kpi__level">{lv}</span>'
                   f'<span class="kpi__chg">{note}</span></li>' for n, lv, note in latest)
    side = (f'<aside class="report__side dd__side fr__side" aria-labelledby="side-title">'
            f'<h2 class="report__side-title" id="side-title">Latest</h2><ul class="kpi">{kpis}</ul>'
            f'<p class="report__src">Each figure with its own date. Sources in each panel.</p></aside>') if latest else ""
    updated = f'Updated {et_stamp(d["updated"])}' if d.get("updated") else "Data pending"
    payload = json.dumps(fr_payload(d), separators=(",", ":")).replace("</", "<\\/")
    body = f"""<main id="main" class="page dd fr">
  <div class="wrap dd__grid">
    <header class="page__head dd__head">
      <h1 class="page__title">Fed &amp; Rates</h1>
      <p class="lede">The policy rate, the Treasury curve and what markets price for the next meetings.</p>
      <p class="note__meta"><span>Federal Reserve, US Treasury, FRED, CBOT futures</span><span>{updated}</span><span>Refreshed every 15 minutes while the NYSE is open</span></p>
    </header>
    <div class="dd__main fr__main">
      <div class="fr__range dd__ctl"><div class="dd__cgroup"><span class="cl__glabel" id="fr-range-l">Range, for the charts over time</span>
        <div class="filters dd__ranges" role="group" aria-labelledby="fr-range-l">{ranges}</div></div></div>
      {policy}{odds_p}{curve_p}{spreads}{macro}{real}
    </div>
    {side}
    <div class="page__body dd__text">
      <section aria-labelledby="fr-how"><h2 id="fr-how">How to read it</h2><p>The FOMC sets a target range for the overnight rate eight times a year. Fed funds futures settle on the average effective rate in their month, so the change from one month to the next shows what the market expects each meeting to do. A curve whose short end sits above its long end is inverted: both spreads above turned negative before most US recessions since the 1970s, with long and variable lags. The real yield is what a Treasury pays after inflation; the breakeven is the inflation rate at which inflation-protected and ordinary Treasuries pay the same.</p></section>
      <section aria-labelledby="fr-src"><h2 id="fr-src">Sources and method</h2><p>Treasury par yields and real yields from the US Treasury, with FRED as backup; FRED posts the curve a day later, so the Treasury's figures come first. Spreads, the fed funds rate, inflation, unemployment and breakevens from FRED. The target range from the Federal Reserve via FRED and the FOMC calendar from the Federal Reserve. Meeting probabilities are an Andra Markets calculation from CBOT 30-day fed funds futures, following the method CME Group publishes: each contract settles on its month's average effective rate, so the rate after a meeting is the month's implied rate with the days before the decision taken out. Futures carry a risk premium, so they are a guide to expectations, not a forecast. The futures and the intraday yield points refresh every 15 minutes while the NYSE is open; the rest once a day. Series older than two years are shown one point a week.</p><p>For information only. Not investment advice.</p></section>
    </div>
  </div>
</main>
<script type="application/json" id="fr-data">{payload}</script>"""
    return shell(title="Fed &amp; Rates: Andra Markets",
                 desc="The Fed's policy rate and FOMC dates, meeting probabilities from fed funds futures, the Treasury curve, "
                      "2s10s and 3m10y spreads, inflation, unemployment and real rates. By Andra Markets.",
                 body=body, home="../", base="../", path="fed-rates/", scripts=("fedrates.js",))


def moved_redirect(path, to, title, text):
    """An old address that moved: say where, and go there."""
    up = "../" * path.count("/")
    body = (f'<main id="main" class="page"><div class="wrap"><header class="page__head"><h1 class="page__title">{title[0].upper() + title[1:]}</h1>'
            f'<p class="lede">{text} <a class="link" href="{up}{to}">{title}</a>.</p></header></div></main>'
            f'<script>location.replace("{up}{to}");</script>')
    name = title[0].upper() + title[1:]
    return shell(title=f"{name}: Andra Markets" if name != "Andra Markets" else name, desc=f"{text} {title}.",
                 body=body, home=up, base=up, path=path)


# Old addresses: path -> (where it went, its title, what the page says).
# Learn was removed (owner, 30 Oct 2026): each explainer sends readers to the
# section that shows its subject live. The careers guide was renamed.
_LEARNT = "Learn was removed. This subject is now covered in"
MOVED = {
    "learn/": ("", "Andra Markets", "Learn was removed. Go to the home page of"),
    "learn/yield-curve/": ("fed-rates/", "Fed &amp; Rates", _LEARNT),
    "learn/fed-rates/": ("fed-rates/", "Fed &amp; Rates", _LEARNT),
    "learn/vix/": ("dashboards/volatility-term-structure/", "Volatility term structure", _LEARNT),
    "learn/earnings-season/": ("calendar/", "the economic calendar", _LEARNT),
    "learn/cpi-vs-pce/": ("dashboards/inflation-and-labour/", "Inflation and labour", _LEARNT),
    "learn/credit-spreads/": ("dashboards/credit-spreads/", "Credit spreads", _LEARNT),
    "careers/": ("break-into-wall-street/", "Break into Wall Street", "This guide is now"),
}


# Technical preparation (break-into-wall-street/technicals/<topic>/) ---------------
# One data file per topic in data/technicals/, in TECH_ORDER. Practice progress
# and the drill's best scores stay in the viewer's browser (assets/technicals.js).

TECH_DIR = ROOT / "data" / "technicals"
TECH_ORDER = ["accounting", "valuation", "lbo", "mergers-and-acquisitions", "markets", "rates-and-the-fed",
              "stock-pitch", "brainteasers-and-mental-maths", "behavioural-and-fit"]


def load_technicals():
    out = []
    for slug in TECH_ORDER:
        f = TECH_DIR / f"{slug}.json"
        if f.exists():
            out.append(json.loads(f.read_text(encoding="utf-8")))
    return out


def tq_paras(a):
    return "".join(f"<p>{esc(x)}</p>" for x in a)


MD_DRILL = """<section id="tq-drill" class="tq-drill" aria-labelledby="tq-drill-h">
      <h2 id="tq-drill-h">Mental maths drill</h2>
      <p class="tq-sub">As many as you can before the clock runs out. Type the answer and press Enter; a wrong answer moves on. Percentages and fractions to two decimals.</p>
      <div class="dd__ctl tq-drill__ctl tq-js">
        <div class="dd__cgroup"><span class="cl__glabel" id="md-t-l">Time</span><div class="filters" role="group" aria-labelledby="md-t-l"><button type="button" class="chip" data-mdtime="60" aria-pressed="true">60 seconds</button><button type="button" class="chip" data-mdtime="120" aria-pressed="false">2 minutes</button></div></div>
        <div class="dd__cgroup"><span class="cl__glabel" id="md-k-l">Questions</span><div class="filters" role="group" aria-labelledby="md-k-l"><button type="button" class="chip" data-mdkind="all" aria-pressed="true">Mixed</button><button type="button" class="chip" data-mdkind="mul" aria-pressed="false">Multiplication</button><button type="button" class="chip" data-mdkind="pct" aria-pressed="false">Percentages</button><button type="button" class="chip" data-mdkind="frac" aria-pressed="false">Fractions</button></div></div>
      </div>
      <div class="tq-md tq-js" id="tq-md">
        <div class="tq-md__bar"><span class="tq-md__time" id="md-time" role="timer">1:00</span><span class="tq-md__score">Score <b id="md-score">0</b></span><span class="tq-md__best">Best <b id="md-best">0</b></span></div>
        <p class="tq-md__q" id="md-q" aria-live="polite">Press Start</p>
        <form class="tq-md__form" id="md-form" autocomplete="off"><label class="visually-hidden" for="md-in">Your answer</label><input id="md-in" inputmode="decimal" disabled><button type="submit" class="btn" id="md-go">Start</button></form>
        <p class="tq-md__log" id="md-log" aria-live="polite"></p>
      </div>
      <p class="tq-nojs">The drill needs JavaScript.</p>
    </section>"""


def technical_page(t, topics):
    slug = t["slug"]
    i = [x["slug"] for x in topics].index(slug)
    up = "../../"
    nav = "".join(f'<li><a href="../{x["slug"]}/"{" aria-current=page" if x["slug"] == slug else ""}>{esc(x["name"])}</a></li>' for x in topics)
    know = "".join(f'<li><b>{esc(e["title"])}</b><p>{esc(e["text"])}</p></li>' for e in t["essentials"])
    ex = ""
    if t.get("example"):
        e = t["example"]
        head = "".join(f'<th scope="col">{esc(c)}</th>' for c in e["columns"])
        rows, last = "", None
        grouped = len({r[0] for r in e["rows"]}) < len(e["rows"])  # a first column that groups rows
        for r in e["rows"]:
            first = grouped and r[0] != last
            last = r[0]
            cells = "".join(f'<td{" class=tq-ex__n" if k == len(r) - 1 else ""}>{esc(v)}</td>' for k, v in enumerate(r[1:], 1))
            rows += f'<tr{" class=tq-ex__first" if first else ""}><th scope="row">{esc(r[0]) if first or not grouped else ""}</th>{cells}</tr>'
        ex = (f'<section id="tq-example" aria-labelledby="tq-ex-h"><h2 id="tq-ex-h">Worked example</h2>'
              f'<p class="tq-ex__title">{esc(e["title"])}</p><p>{esc(e["intro"])}</p>'
              f'<div class="tq-ex__wrap"><table class="tq-ex"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
              f'<p class="tq-ex__note">{esc(e["note"])}</p></section>')
    q = t["questions"]
    core = sum(x["level"] == "core" for x in q)
    payload = json.dumps(q, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    noscript = "".join(f'<li><p class="tq-nq">{esc(x["q"])}</p>{tq_paras(x["a"])}'
                       + (f'<p class="ip-follow"><b>Likely follow-up:</b> {esc(x["follow"])}</p>' if x.get("follow") else "") + "</li>"
                       for x in q)
    nxt = topics[(i + 1) % len(topics)]
    mistakes = "".join(f"<li>{esc(m)}</li>" for m in t["mistakes"])
    body = f"""<main id="main" class="page tq" data-topic="{slug}">
  <div class="wrap">
    <header class="page__head">
      <p class="dd__crumbs"><a href="{up}">Break into Wall Street</a> <span aria-hidden="true">/</span> Technical preparation</p>
      <h1 class="page__title">{esc(t["name"])}</h1>
      <p class="lede">{esc(t["lede"])}</p>
      <p class="note__meta"><span>{len(q)} questions, {core} core and {len(q) - core} advanced</span><span>Your progress stays in this browser</span></p>
    </header>
    <nav class="tq-topics" aria-label="Technical preparation topics"><ol>{nav}</ol></nav>
    <div class="page__body">
      <section id="tq-know" aria-labelledby="tq-know-h"><h2 id="tq-know-h">What you must know</h2><ol class="tq-know">{know}</ol></section>
      {ex}
    </div>
    {MD_DRILL if t.get("drill") else ""}
    <section id="tq-practice" class="tq-practice" aria-labelledby="tq-pr-h">
      <h2 id="tq-pr-h">Practice</h2>
      <p class="tq-sub">Answer out loud first, then check. Mark each card; the ones to review come back first next time.</p>
      <div class="tq-js">
        <div class="dd__ctl">
          <div class="dd__cgroup"><span class="cl__glabel" id="tq-lv-l">Level</span><div class="filters" role="group" aria-labelledby="tq-lv-l"><button type="button" class="chip" data-lv="all" aria-pressed="true">All</button><button type="button" class="chip" data-lv="core" aria-pressed="false">Core</button><button type="button" class="chip" data-lv="advanced" aria-pressed="false">Advanced</button></div></div>
          <div class="dd__cgroup"><span class="cl__glabel" id="tq-or-l">Order</span><div class="filters" role="group" aria-labelledby="tq-or-l"><button type="button" class="chip" data-or="review" aria-pressed="true">To review first</button><button type="button" class="chip" data-or="shuffle" aria-pressed="false">Shuffle</button></div></div>
        </div>
        <div class="tq-prog"><p class="tq-prog__txt" id="tq-prog" aria-live="polite"></p><span class="tq-prog__bar"><i id="tq-prog-bar"></i></span><button type="button" class="tq-reset" id="tq-reset">Reset progress</button></div>
        <article class="tq-card" id="tq-card" aria-live="polite"></article>
      </div>
      <ol class="tq-nojs tq-list">{noscript}</ol>
      <script type="application/json" id="tq-data">{payload}</script>
    </section>
    <div class="page__body">
      <section id="tq-mistakes" aria-labelledby="tq-mi-h"><h2 id="tq-mi-h">Common mistakes</h2><ul class="ruled">{mistakes}</ul></section>
      <nav class="report__pager tq-pager" aria-label="More topics"><a class="link" href="../{nxt["slug"]}/">Next: {esc(nxt["name"])} {icon("arrow-right")}</a><a class="link" href="{up}#pw-tech">All topics {icon("arrow-right")}</a><a class="link" href="{up}../interview-prep/">This week's markets in Interview Prep {icon("arrow-right")}</a></nav>
    </div>
  </div>
</main>"""
    return shell(title=f"{esc(t['name'])}: interview preparation, Andra Markets", desc=esc(t["lede"]), body=body,
                 home="../../../", base="../../../", path=f"break-into-wall-street/technicals/{slug}/", scripts=("technicals.js",))


# Recruiting calendar (break-into-wall-street/recruiting-calendar/) ----------------
# data/recruiting_calendar.json, kept by hand: one row per programme, each
# date taken from the firm's own site. A row not yet re-checked by hand on
# that site (verified false) says so on the page. Never an invented date.

RC_DATA = ROOT / "data" / "recruiting_calendar.json"
RC_KINDS = [("summer", "Summer internship"), ("insight", "Early insight"), ("fulltime", "Full-time"), ("offcycle", "Off-cycle")]
RC_GROUPS = [("bank", "Banks"), ("boutique", "Boutiques"), ("am", "Asset managers"), ("hf", "Hedge funds"), ("quant", "Trading and quant")]
RC_GROUP_OF = {"bulge": "bank", "bank": "bank", "boutique": "boutique", "am": "am", "hf": "hf", "quant": "quant"}
RC_DIVS = ["IB", "S&T", "AM", "Quant"]
RC_STATUS = {"confirmed": "Confirmed date", "expected": "Expected window", "rolling": "Rolling", "unknown": "Not announced"}
MON3 = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_recruiting():
    try:
        rows = json.loads(RC_DATA.read_text(encoding="utf-8"))["rows"]
    except (OSError, ValueError, KeyError):
        return []
    return [dict(r) for r in rows]


def rc_month(window):
    """'Jan 2027 to Mar 2027' -> date(2027, 1, 1)."""
    m, y = window.split(" to ")[0].split()[:2]
    return dt.date(int(y), MON3.index(m[:3]) + 1, 1)


def rc_events(rows):
    """(date or None, what, row): dated opens and closes, expected windows by
    their first month, and rolling programmes (None: open now)."""
    out = []
    for r in rows:
        for what in ("opens", "closes"):
            if r.get(what):
                out.append((dt.date.fromisoformat(r[what]), what, r))
            elif r["status"] == "expected" and r.get(f"{what}_window"):
                try:
                    out.append((rc_month(r[f"{what}_window"]), f"{what}_ex", r))
                except (ValueError, IndexError):
                    pass
        if r["status"] == "rolling" and not r.get("closes"):
            out.append((None, "rolling", r))
    return out


def rc_attrs(r):
    divs = " ".join(d for d in r.get("divisions", []) if d in RC_DIVS) or "Other"
    return (f'data-kind="{r["kind"]}" data-group="{RC_GROUP_OF.get(r["group"], r["group"])}" data-div="{esc(divs)}" '
            f'data-status="{r["status"]}"')


def rc_firm(r, basis=False):
    tags = f'<span class="tag">{RC_STATUS[r["status"]]}</span>'
    if r["status"] == "expected" and r.get("confidence") == "low":
        tags += '<span class="tag">Low confidence</span>'
    if r["status"] != "unknown" and not r.get("verified"):
        tags += '<span class="tag">Not yet re-checked</span>'
    locs = ", ".join(r.get("locations") or [])
    why = (f'<span class="rc-basis">{esc(r["basis"])}</span>' if basis and r["status"] == "expected" and r.get("basis") else "")
    return (f'<th scope="row"><span class="cl__ev">{esc(r["firm"])}</span>'
            f'<span class="rc-sub">{esc(r["programme"])}{". " + esc(locs) if locs else ""}</span>'
            f'<span class="rc-tags">{tags}</span>{why}</th>')


def rc_apply(r, base=""):
    return f'<a class="rc-apply" href="{esc(r["url"])}" rel="noopener">Apply {icon("arrow-up-right")}<span class="visually-hidden"> at {esc(r["firm"])}</span></a>'


def rc_when(d, what, r, today):
    if what in ("opens", "closes"):
        out = f'<span class="rc-when">{d:%a} {d.day} {MON3[d.month - 1]}</span>'
        if what == "closes":
            out += f'<span class="rc-soon" data-close="{d.isoformat()}"></span>'
        return out
    if what == "rolling":
        return '<span class="rc-when rc-when--ex">Open, rolling</span>'
    w = r["opens_window" if what == "opens_ex" else "closes_window"]
    return f'<span class="rc-when rc-when--ex">Expected {esc(w)}</span>'


def rc_upcoming(rows, today, n=6):
    """The next dated opens and closes, then the nearest expected windows."""
    ev = [x for x in rc_events(rows) if x[0] and x[0] >= today.replace(day=1)]
    dated = sorted([x for x in ev if x[1] in ("opens", "closes") and x[0] >= today], key=lambda x: (x[0], x[2]["firm"]))
    loose = sorted([x for x in ev if x[1] in ("opens_ex", "closes_ex")], key=lambda x: (x[0], x[2]["firm"]))
    return (dated + loose)[:n]


def recruiting_page(rows):
    today = dt.datetime.now(NY).date()
    ev = rc_events(rows)
    months = {}
    for d, what, r in ev:
        if d is None:
            months.setdefault("now", []).append((d, what, r))
        elif d >= today.replace(day=1):
            months.setdefault((d.year, d.month), []).append((d, what, r))
    keys = (["now"] if "now" in months else []) + sorted(k for k in months if k != "now")
    mkey = lambda k: k if k == "now" else f"{k[0]}-{k[1]:02d}"  # noqa: E731
    tabs = "".join(f'<button type="button" class="chip" data-month="{mkey(k)}" aria-pressed="{"true" if i == 0 else "false"}">'
                   f'{"Open now" if k == "now" else f"{MON3[k[1] - 1]} {k[0]}"}</button>' for i, k in enumerate(keys))
    bodies = ""
    for k in keys:
        items = months[k]
        exact = sorted([x for x in items if x[1] in ("opens", "closes")], key=lambda x: (x[0], x[2]["firm"]))
        loose = sorted([x for x in items if x[1] not in ("opens", "closes")], key=lambda x: x[2]["firm"])
        trs = ""
        for d, what, r in exact + loose:
            act = {"opens": "Opens", "closes": "Closes", "opens_ex": "Opens", "closes_ex": "Closes", "rolling": "Rolling"}[what]
            divs = "".join(f'<span class="tag">{esc(x)}</span>' for x in r.get("divisions", []))
            trs += (f'<tr class="cl__row rc-row" {rc_attrs(r)}><td class="rc-date">{rc_when(d, what, r, today)}</td>{rc_firm(r)}'
                    f'<td class="rc-act"><span class="rc-what">{act}</span></td><td class="rc-divs"><span class="rc-tags">{divs}</span></td>'
                    f'<td class="rc-cycle">{esc(r.get("cycle", ""))}</td><td class="rc-go">{rc_apply(r)}</td></tr>')
        head = "Open now, rolling review" if k == "now" else f"{dt.date(k[0], k[1], 1):%B %Y}"
        bodies += f'<tbody class="cl__day-group" data-month="{mkey(k)}"><tr class="cl__day"><th scope="rowgroup" colspan="6">{head}</th></tr>{trs}</tbody>'
    bydate = (f'<div class="cl-wrap rc-bydate"><table class="cl__table rc-table" aria-label="Recruiting calendar by date"><thead><tr>'
              f'<th scope="col">Date</th><th scope="col">Firm and programme</th><th scope="col">Window</th><th scope="col">Division</th>'
              f'<th scope="col">Cycle</th><th scope="col"><span class="visually-hidden">Apply</span></th></tr></thead>{bodies}</table>'
              f'<p class="cl__empty" hidden>Nothing matches these filters this month.</p></div>') if keys else \
        '<p class="cl__none">No dated windows yet.</p>'
    order = {g: i for i, (g, _) in enumerate(RC_GROUPS)}

    def when(r, what):
        if r.get(what):
            d = dt.date.fromisoformat(r[what])
            closed = what == "closes" and d < today
            return f"{d.day} {MON3[d.month - 1]} {d.year}" + (" (closed)" if closed else "")
        w = r.get(f"{what}_window")
        return f"Expected {esc(w)}" if w else ("Rolling" if r["status"] == "rolling" else "Not announced")
    firm_rows = "".join(
        f'<tr class="rc-row" {rc_attrs(r)}>{rc_firm(r, basis=True)}<td data-label="Cycle">{esc(r.get("cycle", ""))}</td>'
        f'<td data-label="Opens">{when(r, "opens")}</td><td data-label="Closes">{when(r, "closes")}</td><td>{rc_apply(r)}</td></tr>'
        for r in sorted(rows, key=lambda r: (order.get(RC_GROUP_OF.get(r["group"], r["group"]), 9), r["firm"], r["programme"])))
    byfirm = (f'<div class="rc-byfirm"><table class="rc-firmtab" aria-label="Recruiting calendar by firm"><thead><tr>'
              f'<th scope="col">Firm and programme</th><th scope="col">Cycle</th><th scope="col">Opens</th><th scope="col">Closes</th>'
              f'<th scope="col"><span class="visually-hidden">Apply</span></th></tr></thead><tbody>{firm_rows}</tbody></table></div>')

    def chips(name, opts):
        return "".join(f'<button type="button" class="chip" data-{name}="{v}" aria-pressed="{"true" if i == 0 else "false"}">{lb}</button>'
                       for i, (v, lb) in enumerate([("all", "All")] + opts))
    counts = {s: sum(r["status"] == s for r in rows) for s in RC_STATUS}
    dated = [r for r in rows if r["status"] != "unknown"]
    rechecked = sum(bool(r.get("verified")) for r in dated)
    checked = max((r.get("checked") or "" for r in rows), default="")
    checked_txt = (f"Dates from each firm's own site, {day_med(dt.date.fromisoformat(checked))}; "
                   f"{rechecked} of {len(dated)} re-checked by hand" if checked else "Dates from each firm's own site")
    body = f"""<main id="main" class="page cl rc">
  <div class="wrap">
    <header class="page__head cl__head">
      <p class="dd__crumbs"><a href="../">Break into Wall Street</a> <span aria-hidden="true">/</span> Recruiting calendar</p>
      <h1 class="page__title">Recruiting calendar</h1>
      <p class="lede">When US banks, boutiques, asset managers, hedge funds and trading firms open and close applications for internships and analyst programmes.</p>
      <p class="note__meta"><span>{len({r["firm"] for r in rows})} firms, {len(rows)} programmes</span><span>{counts["confirmed"]} confirmed, {counts["expected"]} expected, {counts["rolling"]} rolling</span><span>{checked_txt}</span></p>
    </header>
    <div class="cl__controls rc-ctl" hidden>
      <div class="cl__groups">
        <div class="cl__group"><span class="cl__glabel" id="rc-v-l">View</span><div class="filters" role="group" aria-labelledby="rc-v-l"><button type="button" class="chip" data-view="date" aria-pressed="true">By date</button><button type="button" class="chip" data-view="firm" aria-pressed="false">By firm</button></div></div>
      </div>
      <div class="filters cl__weeks rc-months" role="group" aria-label="Month">{tabs}</div>
      <div class="cl__groups">
        <div class="cl__group"><span class="cl__glabel" id="rc-k-l">Programme</span><div class="filters" role="group" aria-labelledby="rc-k-l">{chips("kind", RC_KINDS)}</div></div>
        <div class="cl__group"><span class="cl__glabel" id="rc-g-l">Firms</span><div class="filters" role="group" aria-labelledby="rc-g-l">{chips("group", RC_GROUPS)}</div></div>
        <div class="cl__group"><span class="cl__glabel" id="rc-d-l">Division</span><div class="filters" role="group" aria-labelledby="rc-d-l">{chips("div", [(x, x) for x in RC_DIVS])}</div></div>
        <div class="cl__group"><span class="cl__glabel" id="rc-s-l">Dates</span><div class="filters" role="group" aria-labelledby="rc-s-l">{chips("status", [("confirmed", "Confirmed only")])}</div></div>
      </div>
      <p class="filters__status cl__status rc-status" role="status" aria-live="polite"></p>
    </div>
    {bydate}{byfirm}
    <div class="page__body">
      <section aria-labelledby="rc-how"><h2 id="rc-how">How the dates are read</h2><p>Every date comes from the firm's own careers site or the posting itself, read on the day shown. A row tagged "Not yet re-checked" has not yet been opened again by hand to confirm it, so check it on the firm's site before you rely on it. A confirmed date is one the firm states. Where a firm has not published this cycle's dates, the expected window comes from when the same programme opened last cycle, and the row says what that rests on; it becomes a confirmed date once the firm posts it. Rolling means the firm reviews applications as they arrive and states no deadline. Many programmes fill before their deadline, so apply in the first weeks a programme opens. Each row links to where you apply.</p><p>For information only: always confirm the dates on the firm's site.</p></section>
    </div>
  </div>
</main>"""
    return shell(title="Recruiting calendar: Break into Wall Street, Andra Markets",
                 desc="When US banks, boutiques, asset managers, hedge funds and trading firms open and close applications for internships and analyst programmes, checked against each firm's careers site.",
                 body=body, home="../../", base="../../", path="break-into-wall-street/recruiting-calendar/", scripts=("recruiting.js",))


# Break into Wall Street (break-into-wall-street/) ---------------------------------------------------
# One data file, data/path_to_wall_street.json, edited by hand.

CAREERS_DATA = ROOT / "data" / "path_to_wall_street.json"


def careers_page():
    c = json.loads(CAREERS_DATA.read_text(encoding="utf-8"))
    base = "../"
    toc = [("pw-roles", "The roles"), ("pw-time", "Recruiting calendar"), ("pw-cv", "A one-page CV"),
           ("pw-net", "Networking and cold emails"), ("pw-tech", "Technical preparation"),
           ("pw-visa", "Visas for international students"), ("pw-cert", "Certifications"), ("pw-res", "Resources")]
    toc_html = "".join(f'<li><a class="link" href="#{i}">{t}</a></li>' for i, t in toc)
    roles = ""
    for i, r in enumerate(c["roles"]):
        day = "".join(f"<li>{esc(x)}</li>" for x in r["day"])
        roles += (f'<div class="acc__item"><h3><button type="button" class="acc__btn" id="pw-b{i}" aria-expanded="false" aria-controls="pw-p{i}">'
                  f'<span><span class="ip-q__cat">{esc(r["short"])}</span>{esc(r["name"])}</span><span class="acc__plus" aria-hidden="true"></span></button></h3>'
                  f'<div class="acc__panel" id="pw-p{i}" role="region" aria-labelledby="pw-b{i}"><div>'
                  f'<p>{esc(r["what"])}</p><p class="pw-lab">A typical day</p><ol class="ruled pw-day">{day}</ol>'
                  f'<p class="pw-lab">Suits you if</p><p>{esc(r["fit"])}</p>'
                  f'<p class="pw-lab">Where it leads</p><p>{esc(r["exits"])}</p></div></div></div>')
    today = dt.datetime.now(NY).date()
    rc_rows = load_recruiting()
    nxt = "".join(
        f'<tr class="rc-row"><td class="rc-date">{rc_when(d, what, r, today)}</td>{rc_firm(r)}'
        f'<td class="rc-act"><span class="rc-what">{"Opens" if what.startswith("opens") else "Closes"}</span></td>'
        f'<td class="rc-go">{rc_apply(r)}</td></tr>'
        for d, what, r in rc_upcoming(rc_rows, today))
    upcoming = (f'<table class="rc-next" aria-label="Next application dates"><tbody>{nxt}</tbody></table>'
                if nxt else '<p class="rc-none">No dated windows yet.</p>')
    cv, s = c["cv"], c["cv"]["sample"]
    cv_rows = ""
    for sec in s["sections"]:
        rows = ""
        for r in sec["rows"]:
            right = f'<span>{esc(r["right"])}</span>' if r.get("right") else ""
            sub = (f'<div class="cv__row cv__sub"><span>{esc(r["sub"])}</span><span>{esc(r.get("subright", ""))}</span></div>'
                   if r.get("sub") else "")
            bl = "".join(f"<li>{esc(b)}</li>" for b in r.get("bullets", []))
            rows += f'<div class="cv__row"><b>{esc(r["left"])}</b>{right}</div>{sub}<ul>{bl}</ul>'
        cv_rows += f'<div class="cv__sec"><h4>{esc(sec["title"])}</h4>{rows}</div>'
    cv_rules = "".join(f"<li>{esc(x)}</li>" for x in cv["rules"])
    n = c["networking"]
    steps = "".join(f"<li>{esc(x)}</li>" for x in n["steps"])
    tpl_chips = "".join(f'<button type="button" class="chip" data-tpl="{x["id"]}" aria-pressed="{"true" if i == 0 else "false"}">{esc(x["name"])}</button>'
                        for i, x in enumerate(n["templates"]))
    tpls = "".join(f'<div class="pw-tpl" data-tpl-body="{x["id"]}">'
                   f'<p class="pw-tpl__subj"><span>Subject</span> {esc(x["subject"])}</p><pre>{esc(x["body"])}</pre></div>'
                   for x in n["templates"])
    tech = c["technicals"]
    tech_rows = "".join(f'<li><a href="technicals/{x["slug"]}/"><span class="pw-row__t">{esc(x["name"])}</span>'
                        f'<span class="pw-row__d">{esc(x["short"])}</span>{icon("arrow-right")}</a></li>' for x in load_technicals())
    v = c["visas"]
    visa = "".join(f'<div class="pw-visa__col"><h3>{esc(reg["name"])}</h3><ul>' + "".join(
        f'<li><a class="pw-ext" href="{x["src"]}" rel="noopener">{esc(x["name"])}</a><p>{esc(x["what"])}</p></li>' for x in reg["routes"])
        + "</ul></div>" for reg in v["regions"])
    certs = "".join(f'<li><a class="pw-ext" href="{x["src"]}" rel="noopener">{esc(x["name"])}</a><span class="pw-cert__by">{esc(x["by"])}</span>'
                    f'<dl><dt>When</dt><dd>{esc(x["when"])}</dd><dt>Worth it</dt><dd>{esc(x["worth"])}</dd></dl></li>'
                    for x in c["certifications"])
    res = ""
    for g in c["resources"]:
        items = ""
        for x in g["items"]:
            href = x.get("href")
            if href and not href.startswith("http"):
                href = base + href
            name = (f'<a class="pw-ext" href="{href}"{" rel=noopener" if href.startswith("http") else ""}>{esc(x["name"])}</a>'
                    if href else f'<b>{esc(x["name"])}</b>')
            items += f"<li>{name}<p>{esc(x['what'])}</p></li>"
        res += f'<div class="pw-res__g"><h3>{esc(g["group"])}</h3><ul>{items}</ul></div>'
    reviewed = dt.date.fromisoformat(c["reviewed"])
    body = f"""<main id="main" class="page pw">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Break into Wall Street</h1>
      <p class="lede">{esc(c["lede"])}</p>
      <p class="note__meta"><span>Investment banking, sales and trading, asset management, equity research, hedge funds</span><span>Last reviewed <time datetime="{c["reviewed"]}">{day_med(reviewed)}</time></span></p>
    </header>
    <nav class="pw-toc" aria-labelledby="pw-toc-h"><h2 id="pw-toc-h">On this page</h2><ol>{toc_html}</ol></nav>
    <div class="page__body pw__body">
      <section id="pw-roles" aria-labelledby="pw-roles-h">
        <h2 id="pw-roles-h">The roles</h2>
        <p>Five ways into markets: what the job is and what a day looks like for a first-year analyst.</p>
        <div class="acc acc--multi">{roles}</div>
      </section>
    </div>
    <section id="pw-time" class="pw-time" aria-labelledby="pw-time-h">
      <h2 id="pw-time-h">Recruiting calendar</h2>
      <p class="pw-time__lede">When US banks, boutiques, asset managers, hedge funds and trading firms open and close applications. The next dates:</p>
      {upcoming}
      <p class="rc-more"><a class="link" href="recruiting-calendar/">Full recruiting calendar, by date and by firm {icon("arrow-right")}</a></p>
    </section>
    <div class="page__body pw__body">
      <section id="pw-cv" aria-labelledby="pw-cv-h">
        <h2 id="pw-cv-h">A one-page CV</h2>
        <ol class="ruled">{cv_rules}</ol>
      </section>
    </div>
    <figure class="pw-cv">
      <div class="cv" role="img" aria-label="Sample one-page CV with education, experience, leadership and skills sections">
        <p class="cv__name">{esc(s["name"])}</p><p class="cv__contact">{esc(s["contact"])}</p>{cv_rows}
      </div>
      <figcaption class="fr__src">Sample CV. Every name, firm and figure is an example.</figcaption>
    </figure>
    <div class="page__body pw__body">
      <section id="pw-net" aria-labelledby="pw-net-h">
        <h2 id="pw-net-h">Networking and cold emails</h2>
        <ol class="ruled">{steps}</ol>
        <div class="dd__ctl pw-tpl__ctl pw-js"><div class="dd__cgroup"><span class="cl__glabel" id="pw-tpl-l">Template</span>
          <div class="filters" role="group" aria-labelledby="pw-tpl-l">{tpl_chips}</div></div></div>
        <div class="pw-tpls">{tpls}<div class="pw-js"><button type="button" class="btn btn--sm btn--ghost pw-copy">Copy template</button><span class="pw-copy__st" role="status" aria-live="polite"></span></div></div>
      </section>
      <section id="pw-tech" aria-labelledby="pw-tech-h">
        <h2 id="pw-tech-h">Technical preparation</h2>
        <p>{esc(tech["intro"])} Practise with <a class="link" href="{base}interview-prep/">Markets Interview Prep</a>.</p>
        <ul class="pw-rows">{tech_rows}</ul>
      </section>
    </div>
    <section id="pw-visa" class="pw-visa" aria-labelledby="pw-visa-h">
      <h2 id="pw-visa-h">Visas for international students</h2>
      <p class="pw-time__lede">{esc(v["note"])}</p>
      <div class="pw-visa__grid">{visa}</div>
    </section>
    <div class="page__body pw__body">
      <section id="pw-cert" aria-labelledby="pw-cert-h">
        <h2 id="pw-cert-h">Certifications</h2>
        <p>Useful, never a replacement for experience: recruiters value a finished internship over any certificate.</p>
        <ul class="pw-cert">{certs}</ul>
      </section>
      <section id="pw-res" aria-labelledby="pw-res-h">
        <h2 id="pw-res-h">Resources</h2>
        <div class="pw-res">{res}</div>
      </section>
      <section aria-labelledby="pw-about"><h2 id="pw-about">About this guide</h2><p>General guidance for students, reviewed on the date above. Recruiting dates, visa rules and certification requirements change: always check with the firm or the official source. Not career, legal or immigration advice.</p></section>
    </div>
  </div>
</main>"""
    return shell(title="Break into Wall Street: Andra Markets",
                 desc="A guide for students breaking into investment banking, sales and trading, asset management, equity research "
                      "and hedge funds, from non-target universities and from outside the US: roles, recruiting timelines, CV, "
                      "networking, visas and certifications.",
                 body=body, home="../", base="../", path="break-into-wall-street/", scripts=("careers.js", "recruiting.js"))


def slug_s(s):
    return re.sub(r"[^a-z]+", "-", s.lower()).strip("-")


# Search index for the header palette (site.js loads it on first open). A .js
# file, not .json: the deploy refuses JSON files on the published site.
SEARCH_TERMS = {
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

# Words a page is found by beyond its title.
SEARCH_PAGE_TERMS = {
    "fed-rates/": "Fed FOMC policy rate fed funds futures meeting probabilities yield curve Treasury 2s10s 3m10y "
                  "inversion spreads TIPS real yield breakeven inflation CPI PCE unemployment",
    "break-into-wall-street/recruiting-calendar/": "application deadlines internship summer analyst opens closes banks "
                                                   "hedge funds asset managers recruiting dates",
    "break-into-wall-street/": "careers jobs internships spring week summer analyst off-cycle graduate programme recruiting CV resume "
                "networking cold email visa OPT H-1B CFA investment banking sales trading asset management hedge funds",
}

# Live company data (the profile API) -------------------------------------------

def pf_sk(*shapes):
    """A loading skeleton: blocks with the shape of what comes."""
    return '<div class="pf-sk" aria-hidden="true">' + "".join(f'<span class="sk sk--{x}"></span>' for x in shapes) + "</div>"


def pf_sec(key, title, inner, skel):
    """A section assets/profile.js fills: content, skeleton and error slot."""
    return (f'<section id="pf-{key}" aria-labelledby="pf-{key}-t" data-part>'
            f'<h2 id="pf-{key}-t">{title}</h2><div class="pf-ok">{inner}</div>{skel}'
            f'<div class="pf-err"></div></section>')


def pf_news_analysts(name_html):
    """News and analyst recommendations, live from Finnhub."""
    return (pf_sec("news", "News",
                   f'<p>The latest headlines on {name_html} from the past week. Each opens on its publisher&rsquo;s site.</p>'
                   '<ul class="pf-news" id="pf-news-list"></ul>'
                   '<p class="co-src">Finnhub company news, refreshed every 15 minutes. Andra Markets does not write or check these headlines.</p>',
                   pf_sk("line", "line-long", "line", "line-long"))
            + pf_sec("analysts", "What analysts say",
                     '<p id="pf-an-lede"></p><div class="pf-bar" id="pf-an-bar" role="img"></div><p class="pf-legend" id="pf-an-key"></p>'
                     '<p class="co-src">Finnhub recommendation trends, monthly. Not a recommendation from Andra Markets.</p>',
                     pf_sk("bar", "line-short")))


def live_page(companies):
    """/companies/live/?t=TICK: the profile of a US company outside the 600.

    One static page. assets/profile.js reads ?t= and fills it from the profile
    API (PROFILE_API, the Cloudflare Worker in worker/), section by section:
    each starts as a skeleton of its final shape and ends as content, or as an
    error that says what failed and offers to try again. A ticker among the 600
    goes to its own page (data-known); one that does not trade goes to the
    search on the Companies index."""
    sk, sec = pf_sk, pf_sec

    mag = icon("magnifying-glass")
    sections = "".join([
        sec("about", "Overview",
            '<p id="pf-desc"></p><dl class="pf-facts" id="pf-facts"></dl>',
            sk("line", "line", "line-short", "block")),
        sec("years", '<span id="pf-years-h">Revenue and profit</span>',
            '<p>Revenue and net income each fiscal year, <span class="pf-unit">in billions of US dollars</span>. Tap or hover a year to read it.</p>'
            '<div class="co-chart" id="pf-c-years"></div>'
            '<p class="key"><span><i class="sw-fill"></i>Revenue</span><span><i class="sw-ink"></i>Net income</span></p>'
            '<p class="co-read" id="pf-r-years" aria-live="polite"></p>'
            '<p class="co-src">Annual reports, via Financial Modeling Prep.</p>',
            sk("line-long", "chart")),
        sec("margins", "Margins",
            '<p>Gross, operating and net margin each fiscal year, as a share of revenue.</p>'
            '<div class="co-chart" id="pf-c-margins"></div>'
            '<p class="key"><span><i class="k-solid"></i>Gross</span><span><i class="k-dash"></i>Operating</span><span><i class="k-dot"></i>Net</span></p>'
            '<p class="co-read" id="pf-r-margins" aria-live="polite"></p>'
            '<p class="co-src">Annual reports, via Financial Modeling Prep.</p>',
            sk("line-long", "chart")),
        sec("st", "Financial statements",
            '<div class="pf-tabs" role="tablist" aria-label="Statement">'
            '<button type="button" class="chip" role="tab" id="pf-tab-is" aria-controls="pf-stmt" data-stmt="is" aria-selected="true" aria-pressed="true">Income statement</button>'
            '<button type="button" class="chip" role="tab" id="pf-tab-bs" aria-controls="pf-stmt" data-stmt="bs" aria-selected="false" aria-pressed="false" tabindex="-1">Balance sheet</button>'
            '<button type="button" class="chip" role="tab" id="pf-tab-cf" aria-controls="pf-stmt" data-stmt="cf" aria-selected="false" aria-pressed="false" tabindex="-1">Cash flow</button></div>'
            '<div class="pf-scroll pf-scroll--sticky" id="pf-stmt" role="tabpanel" aria-labelledby="pf-tab-is" tabindex="0"></div>'
            '<p class="co-src"><span class="pf-unit-cap">In billions of US dollars</span>, except per share. Annual reports, via Financial Modeling Prep. On a phone, swipe the table sideways.</p>',
            sk("row", "row", "row", "row", "row")),
        sec("mult", "Multiples",
            '<p>The price to earnings ratio at each fiscal year end, against its median over the period, then today&rsquo;s multiples against the company&rsquo;s own history and its peers.</p>'
            '<div class="pf-pe"><div class="co-chart" id="pf-c-pe"></div>'
            '<p class="key"><span><i class="k-solid"></i>P/E</span><span><i class="k-dash"></i>Median</span></p>'
            '<p class="co-read" id="pf-r-pe" aria-live="polite"></p></div>'
            '<div class="pf-scroll"><table class="pf-tab"><thead><tr><th scope="col">Multiple</th><th scope="col">Now</th>'
            '<th scope="col">5-year average</th><th scope="col">Peer median</th></tr></thead><tbody id="pf-mult-rows"></tbody></table></div>'
            '<p class="co-src">Now: Finnhub, last twelve months. Average: Financial Modeling Prep, fiscal year ends. Peers as in the table below.</p>',
            sk("chart", "row", "row", "row")),
        sec("peers", "Peers",
            '<p><span class="pf-name"></span> against the companies Finnhub lists as its peers, on the last twelve months.</p>'
            '<div class="pf-scroll pf-scroll--sticky"><table class="pf-tab"><thead><tr><th scope="col">Company</th><th scope="col">Market value</th>'
            '<th scope="col">Day</th><th scope="col">Revenue growth</th><th scope="col">Operating margin</th><th scope="col">P/E</th>'
            '<th scope="col">EV / EBITDA</th></tr></thead><tbody id="pf-peer-rows"></tbody></table></div>'
            '<p class="co-src">Peers and figures from Finnhub; the day&rsquo;s change from live prices. Each name opens its own profile.</p>',
            sk("row", "row", "row", "row")),
    ]) + pf_news_analysts('<span class="pf-name"></span>')
    memo = ('<section id="pf-memo" aria-labelledby="pf-memo-t"><h2 id="pf-memo-t">Investment memo</h2><div class="co-gate">'
            '<p>For subscribers: a full memo on <span class="pf-name">each company</span>, written for professionals.</p>'
            '<ul class="pf-outline"><li><span>The thesis and what would change it</span></li>'
            '<li><span>Segment by segment, with the model&rsquo;s workings</span></li>'
            '<li><span>Three scenarios and their assumptions</span></li>'
            '<li><span>What to watch at the next results</span></li></ul>'
            '</div></section>')
    kpis = "".join(f'<li class="kpi__item"><span class="kpi__name">{n}</span><span class="kpi__level" id="pf-k-{k}">&nbsp;</span>'
                   f'<span class="kpi__chg" id="pf-k-{k}-n">&nbsp;</span></li>'
                   for k, n in (("mcap", "Market value"), ("pe", "P/E, last 12 months"), ("ev", "EV / EBITDA"), ("ps", "Price to sales"),
                                ("fcf", "Free cash flow yield"), ("nd", "Net debt"), ("dy", "Dividend yield"), ("range", "52-week range")))
    known = {}
    for t in (companies or {}).get("order", []):
        if companies["co"][t]["market"] == "us":
            known[fin_ticker(t)] = co_slug(t)
    known_attr = esc(json.dumps(known, separators=(",", ":")))
    body = f"""<main id="main" class="page dd co pf" data-mode="live" data-api="{esc(PROFILE_API)}" data-known="{known_attr}">
  <div class="wrap dd__grid">
      <header class="page__head dd__head">
        <div class="pf-headrow">
          <p class="dd__crumbs"><a href="../">Companies</a> <span aria-hidden="true">/</span> <span id="pf-crumb">&nbsp;</span></p>
          <form class="pf-field pf-field--sm" role="search" id="pf-form2">
            {mag}
            <input type="search" id="pf-q2" name="t" aria-label="Another ticker" placeholder="Another ticker" autocomplete="off" autocapitalize="characters" spellcheck="false">
          </form>
        </div>
        <h1 class="page__title" id="pf-title">&nbsp;</h1>
        <div class="co-quote" id="pf-quote" data-part>
          <p class="pf-ok"><span class="co-px" id="pf-px"></span><span class="co-chg" id="pf-chg"></span><span class="note__meta" id="pf-qmeta"></span></p>
          <div class="pf-sk" aria-hidden="true"><span class="sk sk--price"></span><span class="sk sk--line-short"></span></div>
          <div class="pf-err"></div>
        </div>
        <p class="lede" id="pf-lede"></p>
        <div class="co-acts">
          <button class="btn" type="button" data-soon="The portfolio monitor is coming soon: you will be able to follow this company and your other holdings here.">Add to portfolio monitor</button>
          <button class="btn btn--ghost" type="button" data-soon="Alerts are coming soon: you will get an email before and after this company's results.">Alert me on results</button>
          <p class="co-acts__status" role="status" aria-live="polite"></p>
        </div>
        <nav class="pf-subnav" aria-label="On this page">
          <ul>
            <li><a href="#pf-about">Overview</a></li>
            <li><a href="#pf-years">Revenue and profit</a></li>
            <li><a href="#pf-margins">Margins</a></li>
            <li><a href="#pf-st">Statements</a></li>
            <li><a href="#pf-mult">Multiples</a></li>
            <li><a href="#pf-peers">Peers</a></li>
            <li><a href="#pf-news">News</a></li>
            <li><a href="#pf-memo">Investment memo</a></li>
          </ul>
        </nav>
      </header>
      <aside class="report__side dd__side" aria-labelledby="side-title" id="pf-side" data-part>
        <h2 class="report__side-title" id="side-title">Key figures</h2>
        <div class="pf-ok"><ul class="kpi">{kpis}</ul></div>
        <div class="pf-sk" aria-hidden="true"><span class="sk sk--row"></span><span class="sk sk--row"></span><span class="sk sk--row"></span><span class="sk sk--row"></span></div>
        <div class="pf-err"></div>
        <p class="report__src" id="pf-side-src">Price: Finnhub. Figures: Financial Modeling Prep and Finnhub.</p>
      </aside>
      <div class="page__body co__body dd__main">
        {sections}
        {memo}
        <p class="co-legal">For information only. Not investment advice.</p>
      </div>
  </div>
</main>"""
    return shell(
        title="Companies: Andra Markets",
        desc="Any US-listed company: the live price, up to ten years of results, margins, multiples, peers and news.",
        body=body, home="../../", base="../../", path="companies/live/", scripts=("profile.js",))


def profile_redirect():
    """/profile/ moved into Companies: send old links on."""
    js = ("var t=new URLSearchParams(location.search).get('t');"
          "location.replace('../companies/'+(t?'live/?t='+encodeURIComponent(t):''));")
    body = (f'<main id="main" class="page"><div class="wrap"><header class="page__head"><h1 class="page__title">Companies</h1>'
            f'<p class="lede">The company profile is now part of <a class="link" href="../companies/">Companies</a>.</p></header></div></main>'
            f'<script>{js}</script>')
    return shell(title="Companies: Andra Markets", desc="The company profile is now part of Companies.",
                 body=body, home="../", base="../", path="profile/")


def fin_ticker(t):
    """Finnhub's form of a US ticker of the 600: BRK-B is BRK.B."""
    return t.replace("-", ".")


SEARCH_PAGES = [
    ("Dashboards", "#dashboards", "Home"),
    ("Fed & Rates", "fed-rates/", "Page"),
    ("Break into Wall Street", "break-into-wall-street/", "Page"),
    ("Recruiting calendar", "break-into-wall-street/recruiting-calendar/", "Break into Wall Street"),
    ("The Lab", "lab/", "Page"),
    ("Simulators", "simulators/", "Page"),
    ("Trading Simulator", "simulators/trading-simulator/", "Simulators"),
    ("Panic Test", "simulators/panic-test/", "Simulators"),
    ("Guess the Fed", "simulators/guess-the-fed/", "Simulators"),
    ("Portfolio Builder", "simulators/portfolio-builder/", "Simulators"),
    ("Companies", "companies/", "Page"),
    ("Economic calendar", "calendar/", "Page"),
    ("World markets", "world/", "Page"),
    ("FX", "fx/", "Page"),
    ("Daily close note", "#note", "Home"),
    ("About", "#about", "Home"),
    ("Research Library", "research/", "Page"),
    ("All close notes", "reports/", "Archive"),
    ("Markets Interview Prep", "interview-prep/", "Page"),
    ("Methodology", "methodology/", "Page"),
    ("Data sources", "sources/", "Page"),
    ("Legal notice", "legal/", "Page"),
    ("Privacy and cookies", "privacy/", "Page"),
]


def search_index(notes, companies=None, library=()):
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
    for r in library:
        items.append({"g": "Reports", "t": r["title"], "m": f"{LIB_TYPE_NAME[r['type']]}, {day_med(r['day'])}",
                      "u": f"research/pdf/{r['slug']}.pdf", "k": r["summary"] + " " + " ".join(r["tags"])})
    for slug, _, title, desc, _, _ in LAB_TOOLS:
        items.append({"g": "Pages", "t": title, "m": "Lab", "u": f"lab/{slug}/", "k": desc + " calculator"})
    for t in load_technicals():
        items.append({"g": "Pages", "t": html.unescape(t["name"]), "m": "Technical preparation",
                      "u": f"break-into-wall-street/technicals/{t['slug']}/",
                      "k": t["short"] + " interview questions " + " ".join(e["title"] for e in t["essentials"])})
    for title, url, meta in SEARCH_PAGES:
        items.append({"g": "Pages", "t": title, "m": meta, "u": url, "k": SEARCH_PAGE_TERMS.get(url, "")})
    payload = json.dumps(items, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return "// Generated by tools/build_site.py. Do not edit.\nwindow.ANDRA_SEARCH=" + payload + ";\n"


def main():
    notes = load_notes()
    cal = load_calendar()
    now = dt.datetime.now(dt.timezone.utc)
    companies = load_companies()
    (OUT / "assets" / "search-index.js").write_text(search_index(notes, companies, load_library()), encoding="utf-8")
    (OUT / "index.html").write_text(page(notes, cal))
    (OUT / "watch").mkdir(exist_ok=True)
    (OUT / "watch" / "index.html").write_text(watch_redirect())
    (OUT / "fed-rates").mkdir(exist_ok=True)
    (OUT / "fed-rates" / "index.html").write_text(fedrates_page(load_fedrates()))
    (OUT / "break-into-wall-street").mkdir(exist_ok=True)
    (OUT / "break-into-wall-street" / "index.html").write_text(careers_page())
    (OUT / "break-into-wall-street" / "recruiting-calendar").mkdir(exist_ok=True)
    (OUT / "break-into-wall-street" / "recruiting-calendar" / "index.html").write_text(recruiting_page(load_recruiting()))
    topics = load_technicals()
    for t in topics:
        folder = OUT / "break-into-wall-street" / "technicals" / t["slug"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(technical_page(t, topics))
    # Yield curve and Fed path are part of Fed & Rates (owner, 30 Oct 2026).
    for old in ("yield-curve", "fed-path"):
        (OUT / "dashboards" / old).mkdir(parents=True, exist_ok=True)
        (OUT / "dashboards" / old / "index.html").write_text(moved_redirect(
            f"dashboards/{old}/", "fed-rates/", "Fed &amp; Rates", "This dashboard is now part of"))
    for path, (to, title, text) in MOVED.items():
        (OUT / path).mkdir(parents=True, exist_ok=True)
        (OUT / path / "index.html").write_text(moved_redirect(path, to, title, text))
    (OUT / "lab").mkdir(exist_ok=True)
    (OUT / "lab" / "index.html").write_text(lab_index())
    risk = risk_data()
    for i, t in enumerate(LAB_TOOLS):
        (OUT / "lab" / t[0]).mkdir(exist_ok=True)
        (OUT / "lab" / t[0] / "index.html").write_text(lab_page(i, risk))
    sim = sim_data()
    (OUT / "simulators").mkdir(exist_ok=True)
    (OUT / "simulators" / "index.html").write_text(sim_index(sim))
    for slug, make in (("trading-simulator", lambda: sim_game_page("trading", sim)),
                       ("panic-test", lambda: sim_game_page("panic", sim)),
                       ("guess-the-fed", lambda: sim_fed_page(sim)),
                       ("portfolio-builder", lambda: sim_portfolio_page(sim))):
        (OUT / "simulators" / slug).mkdir(exist_ok=True)
        (OUT / "simulators" / slug / "index.html").write_text(make())
    (OUT / "world").mkdir(exist_ok=True)
    (OUT / "world" / "index.html").write_text(world_page(load_world()))
    fx = load_fx()
    (OUT / "fx").mkdir(exist_ok=True)
    (OUT / "fx" / "index.html").write_text(fx_index(fx))
    fx_items = sorted(((fx or {}).get("analyses") or {}).values(), key=lambda a: a["date"], reverse=True)
    for i, a in enumerate(fx_items):
        (OUT / "fx" / a["date"]).mkdir(exist_ok=True)
        (OUT / "fx" / a["date"] / "index.html").write_text(
            fx_page(a, fx_items[i - 1] if i > 0 else None, fx_items[i + 1] if i + 1 < len(fx_items) else None))
    (OUT / "profile").mkdir(exist_ok=True)
    (OUT / "profile" / "index.html").write_text(profile_redirect())
    (OUT / "companies" / "live").mkdir(parents=True, exist_ok=True)
    (OUT / "companies" / "live" / "index.html").write_text(live_page(companies))
    (OUT / "methodology").mkdir(exist_ok=True)
    (OUT / "methodology" / "index.html").write_text(methodology())
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "index.html").write_text(archive(notes))
    library = load_library()
    research_dir = OUT / "research"
    shutil.rmtree(research_dir, ignore_errors=True)
    (research_dir / "pdf").mkdir(parents=True)
    (research_dir / "index.html").write_text(library_page(library))
    for r in library:
        shutil.copyfile(r["pdf"], research_dir / "pdf" / f"{r['slug']}.pdf")
    for slug, make in (("interview-prep", lambda: interview_page(notes)), ("sources", sources_page),
                       ("legal", legal_page), ("privacy", privacy_page)):
        (OUT / slug).mkdir(exist_ok=True)
        (OUT / slug / "index.html").write_text(make())
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
            if co_slug(t) == "live":
                continue  # /companies/live/ is the page for every other US company
            folder = OUT / "companies" / co_slug(t)
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "index.html").write_text(company_page(t, companies, cal))
            logo = co_logo(t)
            if logo:
                shutil.copyfile(logo, folder / f"logo{logo.suffix}")
        print(f"wrote {len(companies['order'])} company pages")
    print(f"wrote index.html, methodology/index.html, reports/index.html, {len(DASHBOARDS)} dashboard pages, "
          f"{len(notes)} report page(s) and the calendar with {len(weeks)} week page(s)")


if __name__ == "__main__":
    main()
