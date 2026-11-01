"""Firms (firms/): a directory of the firms in the Recruiting calendar.

Owner-approved sketch, 1 Nov 2026. Built from data/recruiting_calendar.json through
the calendar's own loader and helpers in tools/build_site.py (load_recruiting,
RC_GROUPS, RC_KINDS, RC_STATUS, rc_attrs): one entry per firm, grouping its
programmes, with its type (the calendar's groups), the divisions and US offices
its programmes name, and each programme's cycle, window and apply link. Every fact
on the page is read from the data file: nothing about a firm is added here (no
descriptions, rankings, pay or headcounts). assets/firms.js runs the type and
division chips and counts down to closing dates; without JavaScript every firm shows.

page_application_tracker.py uses slug(), window() and divisions() from here.
"""
import datetime as dt
import re

# Divisions in the order the page names them; "Other" only when a firm names nothing else.
DIV_ORDER = ["IB", "S&T", "AM", "ER", "Quant", "Risk", "Other"]
# The data's locations that are not a city.
WIDE = ("Multiple US offices", "Select US offices", "US")
# One firm's type, from the calendar's groups (RC_GROUPS names them in the plural).
TYPE_ONE = {"bank": "Bank", "boutique": "Boutique", "am": "Asset manager", "hf": "Hedge fund",
            "quant": "Trading and quant"}


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def divisions(rows):
    """The divisions a firm's programmes name, in DIV_ORDER; "Other" only if alone."""
    seen = {d for r in rows for d in r.get("divisions") or []}
    named = [d for d in DIV_ORDER if d in seen and d != "Other"]
    named += sorted(d for d in seen if d not in DIV_ORDER)
    return named or (["Other"] if "Other" in seen else [])


def offices(rows):
    """The cities a firm's programmes name, then "Multiple US offices" (or "Select US
    offices") when one says so; "US" when no programme names a city."""
    cities, wide = [], set()
    for r in rows:
        for loc in r.get("locations") or []:
            if loc in WIDE:
                wide.add(loc)
            elif loc not in cities:
                cities.append(loc)
    for w in ("Multiple US offices", "Select US offices"):
        if w in wide:
            return cities + [w]
    return cities or (["US"] if wide else [])


def window(site, r, what, today):
    """Opens or closes, in the Recruiting calendar's words (its by-firm view): a date,
    "(closed)" once a closing date has passed, "Expected [window]", "Rolling" or
    "Not announced"."""
    if r.get(what):
        d = dt.date.fromisoformat(r[what])
        closed = what == "closes" and d < today
        return f"{d.day} {site.MON3[d.month - 1]} {d.year}" + (" (closed)" if closed else "")
    w = r.get(f"{what}_window")
    return f"Expected {w}" if w else ("Rolling" if r["status"] == "rolling" else "Not announced")


def tags(site, r):
    """The calendar's status tags (rc_firm): status, low confidence, not yet re-checked."""
    out = f'<span class="tag">{site.RC_STATUS[r["status"]]}</span>'
    if r["status"] == "expected" and r.get("confidence") == "low":
        out += '<span class="tag">Low confidence</span>'
    if r["status"] != "unknown" and not r.get("verified"):
        out += '<span class="tag">Not yet re-checked</span>'
    return out


def checked_line(site, rows):
    """The calendar head's line: where the dates come from, when, and how many were re-checked."""
    dated = [r for r in rows if r["status"] != "unknown"]
    rechecked = sum(bool(r.get("verified")) for r in dated)
    checked = max((r.get("checked") or "" for r in rows), default="")
    if not checked:
        return "Dates from each firm's own site", ""
    day = site.day_med(dt.date.fromisoformat(checked))
    return f"Dates from each firm's own site, {day}; {rechecked} of {len(dated)} re-checked by hand", day


def cycle(site, r):
    """The cycle ("Summer 2027"), led by the kind of programme (the calendar's RC_KINDS)
    unless the cycle already says it: "Early insight, 2026 to 2027"."""
    kind, cyc = dict(site.RC_KINDS).get(r["kind"], ""), r.get("cycle") or ""
    said = {"summer": "summer", "fulltime": "full", "offcycle": "off"}.get(r["kind"])
    if not kind or (said and said in cyc.lower()):
        return cyc
    return f"{kind}, {cyc}" if cyc else kind


def programme(site, r, today):
    esc = site.esc
    locs = ", ".join(r.get("locations") or [])
    meta = esc(cycle(site, r)) + (f". {esc(locs)}" if locs else "")
    basis = (f'<span class="rc-basis">{esc(r["basis"])}</span>'
             if r["status"] == "expected" and r.get("basis") else "")
    closes = esc(window(site, r, "closes", today))
    if r.get("closes") and dt.date.fromisoformat(r["closes"]) >= today:
        closes += f'<span class="rc-soon" data-close="{r["closes"]}"></span>'
    name = esc(r["programme"])
    return (f'<li class="fm-prog" {site.rc_attrs(r)}>'
            f'<div class="fm-prog__main"><h3 class="fm-prog__name">{name}</h3>'
            f'<p class="fm-prog__meta">{meta}</p><span class="rc-tags">{tags(site, r)}</span>{basis}</div>'
            f'<dl class="fm-when"><div><dt>Opens</dt><dd>{esc(window(site, r, "opens", today))}</dd></div>'
            f'<div><dt>Closes</dt><dd>{closes}</dd></div></dl>'
            f'<p class="fm-prog__go"><a class="rc-apply" href="{esc(r["url"])}" rel="noopener">Apply {site.icon("arrow-up-right")}'
            f'<span class="visually-hidden">: {esc(r["firm"])}, {name}</span></a></p></li>')


def firm_entry(site, firm, rows, today):
    esc = site.esc
    key = slug(firm)
    group = site.RC_GROUP_OF.get(rows[0]["group"], rows[0]["group"])
    divs = " ".join(sorted({d for r in rows for d in r.get("divisions") or [] if d in site.RC_DIVS})) or "Other"
    progs = "".join(programme(site, r, today) for r in rows)
    return (f'<article class="fm-firm" id="f-{key}" data-group="{group}" data-div="{esc(divs)}" aria-labelledby="f-{key}-h">'
            f'<div class="fm-firm__head"><h2 class="fm-firm__name" id="f-{key}-h">{esc(firm)}</h2>'
            f'<p class="fm-firm__type"><span class="visually-hidden">Type: </span>{TYPE_ONE.get(group, "")}</p>'
            f'<p class="fm-firm__divs"><span class="visually-hidden">Divisions: </span>{esc(" · ".join(divisions(rows)))}</p>'
            f'<p class="fm-firm__locs"><span class="visually-hidden">US offices: </span>{esc(", ".join(offices(rows)))}</p></div>'
            f'<ul class="fm-progs" aria-label="{esc(firm)} programmes">{progs}</ul>'
            f'<p class="fm-firm__more"><a class="rc-apply" href="../recruiting-calendar/#f-{key}">See in the Recruiting calendar '
            f'{site.icon("arrow-right")}<span class="visually-hidden">: {esc(firm)}</span></a></p></article>')


def by_firm(site, rows):
    """{firm: [rows]} in the calendar's by-firm order: type, then firm, then programme."""
    order = {g: i for i, (g, _) in enumerate(site.RC_GROUPS)}
    firms = {}
    for r in sorted(rows, key=lambda r: (order.get(site.RC_GROUP_OF.get(r["group"], r["group"]), 9),
                                         r["firm"].lower(), r["programme"].lower())):
        firms.setdefault(r["firm"], []).append(r)
    return firms


def pages(site):
    """{output path: page HTML}. site is tools/build_site.py, for shell(), icon() and the loaders."""
    rows = site.load_recruiting()
    today = dt.datetime.now(site.NY).date()
    firms = by_firm(site, rows)
    checked, _ = checked_line(site, rows)

    per_group = {}
    for rs in firms.values():
        g = site.RC_GROUP_OF.get(rs[0]["group"], rs[0]["group"])
        per_group[g] = per_group.get(g, 0) + 1

    def chips(name, opts, counts=None):
        return "".join(
            f'<button type="button" class="chip" data-{name}="{site.esc(v)}" data-label="{site.esc(lb)}" '
            f'aria-pressed="{"true" if i == 0 else "false"}">{site.esc(lb)}'
            + (f' <span class="chip__n">{counts[v]}</span>' if counts and v in counts else "") + "</button>"
            for i, (v, lb) in enumerate([("all", "All")] + opts))
    groups = [(g, lb) for g, lb in site.RC_GROUPS if per_group.get(g)]
    counts = dict(per_group, all=len(firms))

    if firms:
        listing = (f'<div class="fm-list">{"".join(firm_entry(site, f, rs, today) for f, rs in firms.items())}</div>'
                   f'<p class="cl__empty fm-empty" hidden>No firm of this type has a programme in that division.</p>')
        controls = f"""<div class="cl__controls fm-ctl" hidden>
      <div class="cl__groups">
        <div class="cl__group"><span class="cl__glabel" id="fm-g-l">Type</span><div class="filters" role="group" aria-labelledby="fm-g-l">{chips("group", groups, counts)}</div></div>
        <div class="cl__group"><span class="cl__glabel" id="fm-d-l">Division</span><div class="filters" role="group" aria-labelledby="fm-d-l">{chips("div", [(x, x) for x in site.RC_DIVS])}</div></div>
      </div>
      <p class="filters__status cl__status fm-status" role="status" aria-live="polite"></p>
    </div>"""
        meta = f'<span>{len(firms)} firms, {len(rows)} programmes</span><span>{checked}</span>'
    else:
        listing = '<p class="cl__none">The list of firms is not available right now. Every date is in the <a href="../recruiting-calendar/">Recruiting calendar</a>.</p>'
        controls, meta = "", "<span>Data pending</span>"

    body = f"""<main id="main" class="page cl rc fm">
  <div class="wrap">
    <header class="page__head cl__head">
      <h1 class="page__title">Firms</h1>
      <p class="lede">The banks, boutiques, asset managers, hedge funds and trading firms in the <a href="../recruiting-calendar/">Recruiting calendar</a>: the divisions each hires for, its US offices, and when its programmes open and close.</p>
      <p class="note__meta">{meta}</p>
    </header>
    {controls}
    {listing}
    <div class="page__body">
      <section aria-labelledby="fm-how"><h2 id="fm-how">Where the dates come from</h2><p>Every firm, programme and date here is the Recruiting calendar's: read from the firm's own careers site or the posting itself, on the day shown at the top. A firm's divisions and offices are the ones its programmes name. A row tagged "Not yet re-checked" has not yet been opened again by hand, so confirm it on the firm's site before you rely on it. An expected window comes from when the same programme opened last cycle, and says what it rests on.</p><p>For information only: always confirm the dates on the firm's site.</p></section>
    </div>
  </div>
</main>"""
    return {"firms/": site.shell(
        title="Firms: Andra Markets",
        desc="The banks, boutiques, asset managers, hedge funds and trading firms in the Recruiting calendar: their divisions, US offices and application windows, from each firm's own site.",
        body=body, home="../", base="../", path="firms/", scripts=("firms.js",))}
