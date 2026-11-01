"""Chart of the day (chart-of-the-day/, chart-of-the-day/<date>/): one chart from each
session's close note, with two lines of context and a link to the note, and an
archive by date (owner-approved sketch, 1 Nov 2026). Meant for sharing too.

The chart is one of the note's own margin charts, drawn by the same code and
markup as on the note's page (margin_chart(), bar_chart() and curve_chart() in
tools/build_site.py), from the figures the note carries (data/notes/<date>.json).

Which chart: among six of the note's charts (S&P 500 sectors, global equity
indices, currencies, commodities, volatility indices, digital assets), the one
whose instruments moved most against their usual day: the median absolute move
of its instruments that session, divided by that same figure's median over the
chart's previous 20 sessions. A chart with fewer than three instruments that day
is left out. With no history to compare against (the first session) the S&P 500
sectors lead; when none of the six can be drawn, the day's moves, then the
watchlist's gainers and losers, then the Treasury curve, then credit. Only notes
up to each session count, so a session's chart never changes once published.

The two lines are on the record: the first is built from the chart's own figures
(what rose and fell most, with signs, and how many rose); the second quotes the
note's section beside the chart, as written: its first sentence without figures,
or its first sentence when every one has figures. Notes whose figure check failed
are published here as on their own page, with the same statement.
"""
import datetime as dt
import html
import re
import statistics

# (MARGIN field in build_site, noun for the count in the first line)
CANDIDATES = [("equities", "sectors"), ("international", "indices"), ("fx", ""), ("commodities", ""),
              ("volatility", "indices"), ("digital", "")]
FALLBACK = [("takeaways", ""), ("desk_view", None), ("rates", None), ("credit", "")]
WINDOW = 20
SECTION_NAME = {"takeaways": "Takeaways", "desk_view": "Desk view", "equities": "Equities", "rates": "Rates",
                "credit": "Credit", "fx": "FX", "commodities": "Commodities", "volatility": "Volatility",
                "digital": "Digital assets", "international": "International"}
FAILED = ("This edition did not fully pass the automated figure check against the session's verified fact pack. "
          "It was reviewed before publication.")


# The chart ------------------------------------------------------------------------

def chart_rows(site, field, rec):
    """[(name, change %, close)] as the note's margin chart draws them, or [] (the curve has its own)."""
    _, what, _ = site.MARGIN[field]
    ch = rec.get("charts") or {}
    if what == "curve":
        return []
    if what == "moves":
        return site.moves_rows(rec)
    if what == "movers":
        mv, seen, rows = ch.get("movers") or {}, set(), []
        for name, chg in (mv.get("leaders") or []) + (mv.get("laggards") or []):
            if name not in seen and chg is not None:
                seen.add(name)
                rows.append((name, chg, None))
        return rows
    block = (ch.get("bars") or {}).get(what) or {}
    return [(n, c, last) for n, last, c in block.get("rows") or [] if c is not None]


def reading(site, field, rec):
    rows = chart_rows(site, field, rec)
    if len(rows) < 3:
        return None
    return statistics.median(abs(c) for _, c, _ in rows)


def pick_all(site, notes):
    """{date: MARGIN field} for every note that has a chart to show, oldest first."""
    hist = {f: [] for f, _ in CANDIDATES}
    out = {}
    for rec in sorted(notes, key=lambda r: r["date"]):
        best, best_score = None, None
        for field, _ in CANDIDATES:
            r = reading(site, field, rec)
            if r is None:
                continue
            past = hist[field][-WINDOW:]
            usual = statistics.median(past) if past else 0
            if usual > 0:
                score = r / usual
                if best_score is None or score > best_score:
                    best, best_score = field, score
            hist[field].append(r)
        if best is None:
            for field, _ in CANDIDATES + FALLBACK:
                if site.margin_chart(field, rec):
                    best = field
                    break
        if best:
            out[rec["date"]] = best
    return out


def chart_title(site, field):
    return site.MARGIN[field][0]


def figure(site, field, rec):
    """The note page's own margin chart, its title promoted to this page's h2."""
    fig = site.margin_chart(field, rec)
    fig = fig.replace('<figure class="report__margin">', '<figure class="report__margin cotd__fig">', 1)
    return fig.replace("<h3>", '<h2 class="cotd__ctitle" id="cotd-title">', 1).replace("</h3>", "</h2>", 1)


# The two lines ----------------------------------------------------------------------

def first_line(site, field, rec, noun):
    """What the chart shows, from its own figures."""
    if site.MARGIN[field][1] == "curve":
        curve = {c.get("key"): c for c in (rec.get("charts") or {}).get("curve") or []}
        parts = [(lbl, curve[k]) for k, lbl in (("ust2y", "2-year"), ("ust10y", "10-year"), ("ust30y", "30-year"))
                 if k in curve and curve[k].get("last") is not None and curve[k].get("chg") is not None]
        if not parts:
            return ""
        said = ", ".join(f"the {lbl} at {c['last']:.2f}%, {site.mv(site.signed(c['chg'], 0, 'bp'))} on the session before"
                         for lbl, c in parts)
        return f"Treasury yields at the close: {said}."
    rows = [(n, round(c, 2)) for n, c, _ in chart_rows(site, field, rec)]
    if len(rows) < 3:
        return ""
    s = lambda v: site.mv(site.signed(v, 2, "%"))
    hi = max(rows, key=lambda r: r[1])
    lo = min(rows, key=lambda r: r[1])
    up = sum(1 for _, c in rows if c > 0)
    down = sum(1 for _, c in rows if c < 0)
    flat = len(rows) - up - down
    esc = site.esc
    if noun is None:  # the watchlist's biggest gainers and losers: a count would mean nothing
        return (f"On the Andra Markets watchlist, {esc(hi[0])} rose the most, {s(hi[1])}, "
                f"and {esc(lo[0])} fell the most, {s(lo[1])}.")
    of = f"{len(rows)} {noun}".strip()
    if up and down:
        line = f"{esc(hi[0])} rose the most, {s(hi[1])}, and {esc(lo[0])} fell the most, {s(lo[1])}. {up} of {of} rose"
    elif down:
        line = f"{esc(lo[0])} fell the most, {s(lo[1])}, and {esc(hi[0])} the least, {s(hi[1])}. None of the {of} rose"
    elif up:
        line = f"{esc(hi[0])} rose the most, {s(hi[1])}, and {esc(lo[0])} the least, {s(lo[1])}. All {of} rose"
    else:
        return f"None of the {of} moved at the close."
    if flat:
        line += f" and {flat} {'was' if flat == 1 else 'were'} unchanged"
    return line + "."


SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z“\"])")
# Index names carry numbers that are not figures.
NAMES = re.compile(r"\b(?:S&P(?:/TSX)?|Nasdaq|Stoxx|STOXX|DAX|FTSE|Nikkei|Russell|MidCap|ASX|CSI|SmallCap)\s*\d+")


def second_line(rec, field):
    """(the quoted sentence, the section's name) or None: the note's section beside the
    chart, its first sentence without figures, else its first sentence."""
    v = (rec.get("note") or {}).get(field)
    if not v:
        return None
    parts = v if isinstance(v, list) else [p for para in re.split(r"\n\s*\n", v) for p in SENTENCE.split(" ".join(para.split()))]
    parts = [" ".join(p.split()) for p in parts if p and p.strip()]
    if not parts:
        return None
    plain = next((p for p in parts if not re.search(r"\d", NAMES.sub("", p))), None)
    return (plain or parts[0]), SECTION_NAME.get(field, field)


# Pages -------------------------------------------------------------------------------

def share(site, url, title):
    """The close note's share row (system share sheet, else copy the link), sharing
    this session's own page even from chart-of-the-day/; assets/chart-of-the-day.js."""
    return (f'<div class="cotd__share" hidden data-url="{url}" data-title="{site.esc(title)}">'
            f'<button class="btn" type="button" data-cotd-share><span class="swap"><span class="swap__a">'
            f'{site.icon("link")}Share this chart</span><span class="swap__b" aria-hidden="true">{site.icon("check")}'
            f'Link copied</span></span></button>'
            f'<p class="report__share-status" role="status" aria-live="polite"></p></div>')


def day_block(site, rec, field, noun, newer, older, here):
    """here: the path from this page to chart-of-the-day/ ("" on the index, "../" on a dated page)."""
    d = rec["day"]
    esc = site.esc
    prev_ = (f'<a class="cotd__step cotd__step--prev" href="{here}{older["date"]}/" '
             f'aria-label="Previous session, {site.day_long(older["day"])}" title="Previous session, {site.day_med(older["day"])}">'
             f'{site.icon("caret-down")}</a>') if older else '<span class="cotd__step cotd__step--prev" aria-hidden="true">' + site.icon("caret-down") + "</span>"
    next_ = (f'<a class="cotd__step cotd__step--next" href="{here}{newer["date"]}/" '
             f'aria-label="Next session, {site.day_long(newer["day"])}" title="Next session, {site.day_med(newer["day"])}">'
             f'{site.icon("caret-down")}</a>') if newer else '<span class="cotd__step cotd__step--next" aria-hidden="true">' + site.icon("caret-down") + "</span>"
    line1 = first_line(site, field, rec, noun)
    quote = second_line(rec, field)
    quote_html = (f'<blockquote class="cotd__quote"><p>“{esc(quote[0])}”</p>'
                  f'<footer>The close note, {quote[1]}</footer></blockquote>') if quote else ""
    title = html.unescape(chart_title(site, field))
    url = f"{here}{rec['date']}/"
    edition = f", edition {esc(rec['edition'])}" if rec.get("edition") else ""
    failed = f" {FAILED}" if rec.get("figure_check") == "failed" else ""
    return f"""<article class="cotd__day" aria-labelledby="cotd-title">
      <div class="cotd__bar">
        <p class="cotd__date"><time datetime="{rec['date']}">{site.day_long(d)}</time></p>
        <nav class="cotd__nav" aria-label="Other sessions">{prev_}{next_}</nav>
      </div>
      {figure(site, field, rec)}
      {f'<p class="cotd__read">{line1}</p>' if line1 else ""}
      {quote_html}
      <div class="cotd__acts">
        <a class="link" href="{here}../reports/{rec['date']}/">Read the close note {site.icon("arrow-right")}</a>
        {share(site, url, f"Chart of the day, {site.day_med(d)}: {title}")}
      </div>
      <p class="cotd__src">Source: the Andra Markets close note for {site.day_long(d)}{edition}, its chart and its text.{failed}</p>
    </article>"""


CANDIDATE_NAMES = ("the S&amp;P 500 sectors, global equity indices, currencies, commodities, volatility indices "
                   "and digital assets")


def how_section(site):
    return (f'<section aria-labelledby="cotd-how"><h2 id="cotd-how">How the chart is chosen</h2>'
            f"<p>Each session's chart comes from its close note: of six of its charts ({CANDIDATE_NAMES}), the one whose "
            f"instruments moved most against their usual day. For each chart, the median move of its instruments that "
            f"session is set against the same figure over the chart's previous {WINDOW} sessions, and the largest "
            f"ratio wins. A chart with fewer than three instruments that day is left out. With nothing to compare "
            f"against, as on the first session, the S&amp;P 500 sectors lead; when none of the six can be drawn, the "
            f"day's moves, then the watchlist's biggest gainers and losers, the Treasury curve and credit. Only the "
            f"notes up to each session count, so a session's chart never changes once it is published.</p>"
            f"<p>The first line under the chart is built from the chart's own figures. The second quotes the note's "
            f"section beside the chart, as written: its first sentence without figures, or its first sentence when "
            f"every one has figures. For information only. Not investment advice.</p></section>")


def lead_figure(site, field, rec):
    """The chart's largest move, for its row in the archive: "VIX 9-day +21.30%"."""
    if site.MARGIN[field][1] == "curve":
        c = next((c for c in (rec.get("charts") or {}).get("curve") or [] if c.get("key") == "ust10y"), None)
        if not c or c.get("chg") is None:
            return ""
        return f' <span class="cotd__lead">10-year {site.mv(site.signed(c["chg"], 0, "bp"))}</span>'
    rows = chart_rows(site, field, rec)
    if not rows:
        return ""
    n, c, _ = max(rows, key=lambda r: abs(r[1]))
    return f' <span class="cotd__lead">{site.esc(n)} {site.mv(site.signed(c, 2, "%"))}</span>'


def archive(site, items, here):
    months = {}
    for rec, field in items:
        months.setdefault((rec["day"].year, rec["day"].month), []).append((rec, field))
    return ('<section class="fx-archive cotd__archive" id="every" aria-labelledby="cotd-arch-t">'
            '<h2 id="cotd-arch-t">Every chart</h2><div class="archive">'
            + "".join(
                f'<section class="archive__month" aria-labelledby="cotd-m-{y}-{m:02d}"><h3 id="cotd-m-{y}-{m:02d}">{dt.date(y, m, 1):%B %Y}</h3>'
                f'<ol class="note-list">' + "".join(
                    f'<li><a href="{here}{r["date"]}/"><time datetime="{r["date"]}">{r["day"].day} {r["day"]:%b}</time>'
                    f'<span class="note-list__title">{chart_title(site, f)}{lead_figure(site, f, r)}</span>'
                    f'{site.icon("arrow-right")}</a></li>'
                    for r, f in rs)
                + "</ol></section>" for (y, m), rs in months.items())
            + "</div></section>")


LEDE = ("One chart from each session's close note, with two lines: what it shows, from its own figures, "
        "and what the note said.")


def pages(site):
    """{output path: page HTML}. site is tools/build_site.py, for shell(), icon() and the loaders."""
    notes = site.load_notes()  # newest first
    picks = pick_all(site, notes)
    items = [(r, picks[r["date"]]) for r in notes if r["date"] in picks]
    noun = dict(CANDIDATES + FALLBACK)
    out = {}
    for i, (rec, field) in enumerate(items):
        newer = items[i - 1][0] if i > 0 else None
        older = items[i + 1][0] if i + 1 < len(items) else None
        d = rec["day"]
        title = chart_title(site, field)
        pager = ""
        if older:
            pager += f'<a class="link" href="../{older["date"]}/">Previous chart, {site.day_med(older["day"])} {site.icon("arrow-right")}</a>'
        if newer:
            pager += f'<a class="link" href="../{newer["date"]}/">Next chart, {site.day_med(newer["day"])} {site.icon("arrow-right")}</a>'
        pager += f'<a class="link" href="../#every">Every chart {site.icon("arrow-right")}</a>'
        pager += f'<a class="link" href="../../reports/">All close notes {site.icon("arrow-right")}</a>'
        body = f"""<main id="main" class="page cotd">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Chart of the day</h1>
      <p class="lede">{LEDE}</p>
    </header>
    {day_block(site, rec, field, noun[field], newer, older, "../")}
    <div class="page__body cotd__text">{how_section(site)}</div>
    <nav class="report__pager" aria-label="More charts">{pager}</nav>
  </div>
</main>"""
        out[f"chart-of-the-day/{rec['date']}/"] = site.shell(
            title=f"{title}, {site.day_med(d)}: Andra Markets chart of the day",
            desc=site.esc(f"{html.unescape(title)} at the close of {site.day_long(d)}, from the Andra Markets close note: "
                          f"the chart, two lines on what it shows, and a link to the note."),
            body=body, home="../../", base="../../", path=f"chart-of-the-day/{rec['date']}/",
            scripts=("chart-of-the-day.js",))
    if items:
        rec, field = items[0]
        latest = day_block(site, rec, field, noun[field], None, items[1][0] if len(items) > 1 else None, "")
        rest = archive(site, items, "")
    else:
        latest = '<p class="cotd__empty">The first chart comes with the first published close note.</p>'
        rest = ""
    body = f"""<main id="main" class="page cotd">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Chart of the day</h1>
      <p class="lede">{LEDE}</p>
    </header>
    {latest}
    {rest}
    <div class="page__body cotd__text">{how_section(site)}</div>
  </div>
</main>"""
    out["chart-of-the-day/"] = site.shell(
        title="Chart of the day: Andra Markets",
        desc=site.esc("One chart from each session's Andra Markets close note, with two lines on what it shows "
                      "and a link to the note. Every chart, by date."),
        body=body, home="../", base="../", path="chart-of-the-day/",
        scripts=("chart-of-the-day.js",) if items else ())
    return out
