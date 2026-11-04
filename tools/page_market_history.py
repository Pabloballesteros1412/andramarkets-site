"""Market history (market-history/, market-history/<slug>/): the S&P 500 since 1928,
episode by episode (owner-approved sketch, 1 Nov 2026).

The episodes and their text are the Trading Simulator's US episodes
(tools/sim_content.py), used as written: they cover every month since 1928
without gaps. The index is a timeline: the whole history on one chart with each
episode's fall marked, then every episode in order with its years, name and fall.
Each episode has its own page: the S&P 500 through the episode from its peak to
its low and back to the peak, the figures, the text, a link to play those years
in the Trading Simulator and the site pages the episode links to.

Figures are measured here from S&P 500 daily closes, price only, the series the
text speaks of (Yahoo Finance ^GSPC, the S&P 90 before March 1957), cached at
deploy time by tools/history_data.py in .cache/history/sp500.json. Without that
file every figure and chart reads "Data pending". assets/market-history.js draws
the charts at their pixel width, with a crosshair and a readout.
"""
import datetime as dt
import json
import math
import re

DATA = ("history", "sp500.json")
SIM = "simulators/trading-simulator/"

# Where an episode's text measures its fall from a peak in the episode before, or to
# a low in the episode after, the figures follow the text: (search the peak from,
# search the low to), as months. Everything else stays within the episode's months.
MEASURE = {
    "1929-11": ("1928-01", None),   # "From its 1929 peak to the summer of 1932 the index lost about 86%"
    "1957-01": ("1956-01", None),   # "The index fell about 20% from its 1956 high"
    "1980-01": (None, "1982-08"),   # "The index fell about 27% from late 1980 to August 1982"
}
MEASURED_AS = ("the Great Depression from the 1929 peak, Sputnik and the 1957 recession from the 1956 high, "
               "and the Volcker squeeze to the low of August 1982")
CHART_POINTS = 640      # closes sent to the browser per episode chart (extremes always kept)
OVERVIEW_POINTS = 1400  # for the chart of the whole history


# Episodes ----------------------------------------------------------------------

def _month(iso_month):
    return dt.date(int(iso_month[:4]), int(iso_month[5:7]), 1)


def _next_month(d):
    return dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1)


def episodes():
    from sim_content import EPISODES
    out = []
    for i, (a, b, name, text, links) in enumerate(EPISODES):
        ongoing = b >= "2099"
        first, last = _month(a), _month(b)
        if ongoing:
            years, period = f"Since {first.year}", f"Since {first:%B %Y}"
        elif first.year == last.year:
            years, period = f"{first.year}", f"{first:%B} to {last:%B %Y}"
        else:
            years, period = f"{first.year} to {last.year}", f"{first:%B %Y} to {last:%B %Y}"
        stem = re.sub(r"[^a-z0-9]+", "-", re.sub(r"^the ", "", name.lower())).strip("-")
        out.append({"i": i, "start": a, "end": b, "name": name, "title": name[0].upper() + name[1:],
                    "text": text, "links": links, "slug": f"{a[:4]}-{stem}", "ongoing": ongoing,
                    "years": years, "period": period,
                    "years_in": years[0].lower() + years[1:] if ongoing else years})  # mid-sentence
    return out


# Data -----------------------------------------------------------------------------

def load(site):
    """[(date, close)] oldest first, or None while the history is not cached."""
    path = site.ROOT / ".cache" / DATA[0] / DATA[1]
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        rows = [(dt.date.fromisoformat(d), float(c)) for d, c in raw["rows"]
                if isinstance(c, (int, float)) and math.isfinite(c) and c > 0]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    rows.sort()
    if len(rows) < 1000 or rows[0][0] > dt.date(1928, 1, 31):
        return None
    return rows


def _first_on_or_after(days, d):
    lo, hi = 0, len(days)
    while lo < hi:
        mid = (lo + hi) // 2
        if days[mid] < d:
            lo = mid + 1
        else:
            hi = mid
    return lo


def measure(ep, rows, days):
    """The episode's fall, its low and its recovery, from daily closes (indices into rows)."""
    first = _first_on_or_after(days, _month(ep["start"]))
    end = len(rows) - 1 if ep["ongoing"] else _first_on_or_after(days, _next_month(_month(ep["end"]))) - 1
    if first >= len(rows) or end <= first:
        return None
    peak_from, low_to = MEASURE.get(ep["start"], (None, None))
    p0 = _first_on_or_after(days, _month(peak_from)) if peak_from else first
    l1 = min(len(rows) - 1, _first_on_or_after(days, _next_month(_month(low_to))) - 1) if low_to else end
    run, best = p0, None
    for j in range(p0, l1 + 1):
        if rows[j][1] > rows[run][1]:
            run = j
        if j >= first:
            fall = rows[j][1] / rows[run][1] - 1
            if best is None or fall < best[0]:
                best = (fall, run, j)
    fall, peak, low = best
    back = next((k for k in range(low + 1, len(rows)) if rows[k][1] >= rows[peak][1]), None) if fall < 0 else None
    base = first - 1 if first > 0 else first
    return {"first": first, "end": end, "peak": peak, "low": low, "back": back, "fall": fall,
            "over": rows[end][1] / rows[base][1] - 1, "base": base}


def months_between(a, b):
    return round((b - a).days / 30.4375)


def months_text(n):
    if n < 1:
        return "Under a month"
    return f"{n} month{'' if n == 1 else 's'}"


def years_after(a, b):
    y = (b - a).days / 365.25
    return f"{y:.0f} years" if y >= 10 else f"{y:.1f} years"


def text_check(ep, m):
    """Warn in the build log when the measured fall and the text's own figure for it
    disagree by more than 4 points (the text gives rounded 'about' figures)."""
    said = [int(n) for n in re.findall(
        r"\b(?:fell|lost|down)\b[^.%]{0,40}?\b(?:about|roughly|nearly|almost)\s+(\d+)%(?!\s+in a (?:single )?day)",
        ep["text"])]
    said += [int(n) for n in re.findall(r"\b(?:about|roughly|nearly|almost)\s+(\d+)%\s+below its high", ep["text"])]
    said = [n for n in said if n >= 10]
    if said and abs(max(said) + m["fall"] * 100) > 4:
        print(f"market history: {ep['slug']} measures {m['fall'] * 100:.1f}% but its text says about {max(said)}%")


# Formatting --------------------------------------------------------------------

def level(v):
    return f"{v:,.2f}"


def pct(site, v):
    return site.mv(site.signed(v * 100, 1, "%"))


def day(site, d):
    return site.day_med(d)


def span_days(site, a, b):
    if a.year == b.year:
        return f"{a.day} {a:%b} to {b.day} {b:%b %Y}"
    return f"{site.day_med(a)} to {site.day_med(b)}"


def thin(rows, lo, hi, keep, n):
    """Indices from lo to hi, at most about n of them: each stretch keeps its highest
    and lowest close, so falls and peaks survive; the indices in keep always stay."""
    if hi - lo + 1 <= n:
        return list(range(lo, hi + 1))
    out = {lo, hi, *[k for k in keep if k is not None and lo <= k <= hi]}
    step = (hi - lo + 1) / (n / 2)
    b = float(lo)
    while int(b) <= hi:
        s, e = int(b), min(hi, int(b + step))
        seg = range(s, e + 1)
        out.add(min(seg, key=lambda k: rows[k][1]))
        out.add(max(seg, key=lambda k: rows[k][1]))
        b += step
    return sorted(out)


def payload(data):
    return json.dumps(data, separators=(",", ":")).replace("</", "<\\/")


def source_line(first, upto):
    """The chart's source line; first is the chart's first day."""
    s90 = " (the S&amp;P 90 before March 1957)" if first < dt.date(1957, 3, 4) else ""
    return f"S&amp;P 500 daily close, price only{s90}. Yahoo Finance, ^GSPC, to {upto}."


PENDING = '<div class="dd__plot dd__plot--pending"><p class="dd__pending">Data pending</p></div>'
NOSCRIPT = '<noscript><p class="dd__pending">The chart needs JavaScript. The figures are beside it.</p></noscript>'


def figure(fid, label, data, key):
    return (f'<figure class="dd__chart mh__fig" data-mh>'
            f'<div class="dd__plot mh__plot" role="img" tabindex="0" aria-label="{label}"></div>'
            f'<figcaption><p class="key">{key}</p><p class="dd__read mh__read" aria-live="polite"></p></figcaption>'
            f'{NOSCRIPT}<script type="application/json" class="mh-data" id="{fid}">{payload(data)}</script></figure>')


# Pages ---------------------------------------------------------------------------

def method_section(sim_href, sid="mh-how"):
    return (f'<section aria-labelledby="{sid}"><h2 id="{sid}">How the figures are measured</h2>'
            f"<p>From the S&amp;P 500's daily closes, price only: dividends are not included. An episode's fall is "
            f"the largest drop from a close to a later close within its months, from the highest close before the "
            f"low. Where an episode's text measures from a peak in the episode before or to a low in the episode "
            f"after, the figures do too: {MEASURED_AS}. Months are calendar months, rounded. Back at the peak is "
            f"the first close at or above the peak's close.</p>"
            f"<p>The text of each episode is the one the "
            f'<a href="{sim_href}">Trading Simulator</a> shows at the end of a game. '
            f"For information only. Not investment advice.</p></section>")


def index_page(site, eps, rows, ms):
    n = len(eps)
    if rows:
        upto = day(site, rows[-1][0])
        meta = f"<span>S&amp;P 500 daily closes, price only</span><span>Yahoo Finance, to {upto}</span>"
        keep = [k for m in ms if m for k in (m["peak"], m["low"])]
        idx = thin(rows, 0, len(rows) - 1, keep, OVERVIEW_POINTS)
        data = {"kind": "overview", "log": True,
                "d": [[rows[k][0].isoformat(), round(rows[k][1], 2)] for k in idx],
                "eps": [[e["start"], e["end"], e["title"], e["slug"], e["years_in"],
                         site.signed(m["fall"] * 100, 1, "%") if m else ""] for e, m in zip(eps, ms)],
                "bands": [[rows[m["peak"]][0].isoformat(), rows[m["low"]][0].isoformat()] for m in ms if m and m["fall"] < 0]}
        deepest = min((m["fall"] for m in ms if m), default=-1)
        label = (f"The S&amp;P 500 daily close from {day(site, rows[0][0])} to {upto} on a log scale, with each "
                 f"episode's fall from peak to low shaded. Deepest: {site.signed(deepest * 100, 1, '%')}.")
        key = ('<span><i class="k-solid"></i>S&amp;P 500, daily close (log scale)</span>'
               '<span><i class="sw-down mh-sw"></i>Each episode\'s fall, peak to low</span>')
        chart = figure("mh-overview", label, data, key) + f'<p class="report__src">{source_line(rows[0][0], upto)}</p>'
    else:
        meta = "<span>S&amp;P 500 daily closes, price only</span><span>Yahoo Finance. Data pending</span>"
        chart, deepest = PENDING + '<p class="report__src">S&amp;P 500 daily close, price only. Yahoo Finance, ^GSPC.</p>', -1
    items = ""
    for e, m in zip(eps, ms):
        if m:
            w = max(1.5, 100 * m["fall"] / deepest) if deepest < 0 else 0
            fig = (f'<span class="mh-tl__bar" aria-hidden="true"><i style="width:{w:.1f}%"></i></span>'
                   f'<span class="mh-tl__fall">{pct(site, m["fall"])}</span>')
        else:
            fig = '<span class="mh-tl__bar" aria-hidden="true"></span><span class="mh-tl__fall mh-tl__fall--pending">Data pending</span>'
        items += (f'<li><a href="{e["slug"]}/"><span class="mh-tl__years">{e["years"]}</span>'
                  f'<span class="mh-tl__name">{site.esc(e["title"])}</span>{fig}{site.icon("arrow-right")}</a></li>')
    body = f"""<main id="main" class="page mh">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Market history</h1>
      <p class="lede">What happened in each stage of the S&amp;P 500 since 1928: {n} episodes, each with its fall from peak to low, the months to the low and back to the peak, and what happened.</p>
      <p class="note__meta">{meta}</p>
    </header>
    <section class="mh-over" aria-labelledby="mh-over-t">
      <h2 class="mh__h2" id="mh-over-t">The S&amp;P 500 since 1928</h2>
      {chart}
    </section>
    <section class="mh-tl" aria-labelledby="mh-tl-t">
      <h2 class="mh__h2" id="mh-tl-t">Every episode</h2>
      <p class="mh-tl__head" aria-hidden="true"><span>Years</span><span>Episode</span><span>Fall, peak to low</span></p>
      <ol class="mh-tl__list">{items}</ol>
    </section>
    <div class="page__body mh__text">
      {method_section("../" + SIM)}
    </div>
  </div>
</main>"""
    return site.shell(title="Market history: Andra Markets",
                      desc=f"What happened in each stage of the S&amp;P 500 since 1928: {n} episodes from the great crash "
                           "to today, each with its fall from peak to low and the time it took to recover.",
                      body=body, home="../", base="../", path="market-history/",
                      scripts=("market-history.js",) if rows else ())


def sim_start(ep):
    """The month the Trading Simulator starts its two years from (?g=): the episode's
    first month, or, for an episode shorter than two years, the month that centres the
    two years on it. Either way the game's two years overlap this episode more than any
    other, so its end screen names this episode."""
    a = _month(ep["start"])
    if ep["ongoing"]:
        return a
    b = _month(ep["end"])
    n = (b.year - a.year) * 12 + b.month - a.month + 1
    if n >= 24:
        return a
    m = a.year * 12 + a.month - 1 - (24 - n) // 2
    return dt.date(m // 12, m % 12 + 1, 1)


def episode_page(site, eps, i, rows, m):
    e = eps[i]
    esc = site.esc
    if rows and m:
        P, L, B = m["peak"], m["low"], m["back"]
        pd_, pl = rows[P]
        ld, ll = rows[L]
        upto = day(site, rows[-1][0])
        lo = min(m["first"], P)
        hi = max(m["end"], B if B is not None else m["end"])
        if B is None and not e["ongoing"]:
            hi = len(rows) - 1
        idx = thin(rows, lo, hi, [P, L, B, m["first"], m["end"]], CHART_POINTS)
        pos = {k: j for j, k in enumerate(idx)}
        data = {"kind": "episode", "log": False,
                "d": [[rows[k][0].isoformat(), round(rows[k][1], 2)] for k in idx],
                "peak": pos[P], "low": pos[L], "back": pos.get(B) if B is not None else None,
                "ep": [rows[m["first"]][0].isoformat(), rows[m["end"]][0].isoformat()]}
        fall = site.signed(m["fall"] * 100, 1, "%")
        back_txt = (f", back at the peak on {day(site, rows[B][0])}" if B is not None
                    else ", not yet back at the peak")
        label = (f"S&amp;P 500 daily close from {day(site, rows[lo][0])} to {day(site, rows[hi][0])}: peak {level(pl)} "
                 f"on {day(site, pd_)}, low {level(ll)} on {day(site, ld)}, {fall}{back_txt}.")
        key = ('<span><i class="k-solid"></i>S&amp;P 500, daily close</span>'
               '<span><i class="sw-down mh-sw"></i>Fall, peak to low</span>'
               '<span><i class="k-ref"></i>The peak\'s level</span>'
               + ('<span><i class="mh-k-ep"></i>The episode\'s months</span>' if (lo < m["first"] or hi > m["end"]) else ""))
        chart = figure("mh-episode", label, data, key) + f'<p class="report__src">{source_line(rows[lo][0], upto)}</p>'
        to_low = months_between(pd_, ld)
        if B is not None:
            bd = rows[B][0]
            nb = months_between(ld, bd)
            back_note = f"{day(site, bd)}, after {years_after(ld, bd)}" if nb >= 24 else day(site, bd)
            back = site.kpi("Back at the peak", months_text(nb), back_note)
        else:
            below = rows[-1][1] / pl - 1
            back = site.kpi("Back at the peak", "Not yet", f"{pct(site, below)} from the peak on {upto}")
        base_d, end_d = rows[m["base"]][0], rows[m["end"]][0]
        kpis = (site.kpi("Fall, peak to low", pct(site, m["fall"]), span_days(site, pd_, ld))
                + site.kpi("To the low", months_text(to_low), f"{L - P:,} sessions")
                + site.kpi("Peak", level(pl), day(site, pd_))
                + site.kpi("Low", level(ll), day(site, ld))
                + back
                + site.kpi("Over the episode", pct(site, m["over"]), span_days(site, base_d, end_d)))
        asof = f" As of {upto}." if e["ongoing"] else ""
        side = (f'<aside class="report__side dd__side" aria-labelledby="side-title">'
                f'<h2 class="report__side-title" id="side-title">The fall in numbers</h2><ul class="kpi">{kpis}</ul>'
                f'<p class="report__src">S&amp;P 500 daily close, price only. Yahoo Finance, ^GSPC.{asof} '
                f'Over the episode: from the last close before it to its last close.</p></aside>')
        meta = (f"<span>{e['period']}</span><span>Episode {i + 1} of {len(eps)}</span>"
                f"<span>Fall {site.mv(fall)}</span>")
        scripts = ("market-history.js",)
    else:
        chart = PENDING + '<p class="report__src">S&amp;P 500 daily close, price only. Yahoo Finance, ^GSPC.</p>'
        side = (f'<aside class="report__side dd__side" aria-labelledby="side-title">'
                f'<h2 class="report__side-title" id="side-title">The fall in numbers</h2>'
                f'<p class="dd__pending mh__pending">Data pending</p></aside>')
        meta = f"<span>{e['period']}</span><span>Episode {i + 1} of {len(eps)}</span>"
        scripts = ()
    start = sim_start(e)
    play = (f'<section aria-labelledby="mh-play"><h2 id="mh-play">Play it</h2>'
            f"<p>The Trading Simulator replays two years of the S&amp;P 500 from {start:%B %Y}, day by day: stay "
            f"invested or move to cash, and finish ahead of the index if you can. The game counts dividends, so its "
            f"figures differ from the price figures here.</p>"
            f'<p class="mh__acts"><a class="btn" href="../../{SIM}?m=sp500&amp;g={start.isoformat()}">'
            f'Play these years in the Trading Simulator {site.icon("arrow-right")}</a></p></section>')
    related = ""
    if e["links"]:
        related = (f'<section aria-labelledby="mh-rel"><h2 id="mh-rel">On Andra Markets</h2><ul class="mh-rel">'
                   + "".join(f'<li><a class="link" href="../../{u}">{esc(t)} {site.icon("arrow-right")}</a></li>'
                             for t, u in e["links"])
                   + "</ul></section>")
    pager = ""
    if i > 0:
        pager += f'<a class="link" href="../{eps[i - 1]["slug"]}/">Previous: {esc(eps[i - 1]["title"])}, {eps[i - 1]["years_in"]} {site.icon("arrow-right")}</a>'
    if i + 1 < len(eps):
        pager += f'<a class="link" href="../{eps[i + 1]["slug"]}/">Next: {esc(eps[i + 1]["title"])}, {eps[i + 1]["years_in"]} {site.icon("arrow-right")}</a>'
    pager += f'<a class="link" href="../">Every episode {site.icon("arrow-right")}</a>'
    body = f"""<main id="main" class="page dd mh mh-ep">
  <div class="wrap dd__grid">
    <header class="page__head dd__head">
      <p class="dd__crumbs"><a href="../">Market history</a> <span aria-hidden="true">/</span> {e["years"]}</p>
      <h1 class="page__title">{esc(e["title"])}</h1>
      <p class="lede">The S&amp;P 500 through the episode, from its peak to its low and back to the peak, and what happened.</p>
      <p class="note__meta">{meta}</p>
    </header>
    <section class="dd__main" aria-label="Chart">{chart}</section>
    {side}
    <div class="page__body dd__text">
      <section aria-labelledby="mh-what"><h2 id="mh-what">What happened</h2><p>{esc(e["text"])}</p></section>
      {play}
      {related}
      {method_section("../../" + SIM)}
    </div>
    <nav class="report__pager mh__pager" aria-label="More episodes">{pager}</nav>
  </div>
</main>"""
    desc = (f"{esc(e['title'])} ({e['period']}): the S&amp;P 500's fall from peak to low, "
            f"the months to the low and back to the peak, and what happened.")
    return site.shell(title=f"{esc(e['title'])}, {e['years']}: Andra Markets market history",
                      desc=desc, body=body, home="../../", base="../../",
                      path=f"market-history/{e['slug']}/", scripts=scripts)


def pages(site):
    """{output path: page HTML}. site is tools/build_site.py, for shell(), icon() and the loaders."""
    eps = episodes()
    rows = load(site)
    ms = [None] * len(eps)
    if rows:
        days = [r[0] for r in rows]
        ms = [measure(e, rows, days) for e in eps]
        for e, m in zip(eps, ms):
            if m:
                text_check(e, m)
    out = {"market-history/": index_page(site, eps, rows, ms)}
    for i, e in enumerate(eps):
        out[f"market-history/{e['slug']}/"] = episode_page(site, eps, i, rows, ms[i])
    return out
