"""Recession watch (recession-watch/): the most watched US recession indicators
on one page, each with its latest reading, a plain reading against its own
published definition (or the note that it has none), and its history since
1970 (or its first observation) with NBER recessions shaded. Owner-approved
sketch, 1 Nov 2026; built on the Fed & Rates page grid and panels (DESIGN.md).
No forecast and no probability of our own.

Figures from .cache/recession/recession.json (tools/recession_data.py); an
indicator with no figures yet says "Data pending". assets/recession.js draws
the charts.
"""
import datetime as dt
import json


def load(site):
    try:
        return json.loads((site.ROOT / ".cache" / "recession" / "recession.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def day(site, iso):
    return site.day_med(dt.date.fromisoformat(iso))


def short(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {d:%b}"


def month(iso):
    return f"{dt.date.fromisoformat(iso):%b %Y}"


def lvl(v, dec=0, unit=""):
    """A level: signed only when negative (true minus), in ink."""
    return f"{v:,.{dec}f}{unit}".replace("-", "−")


def first_year(block):
    """When the chart starts: 1970, or the series' first observation."""
    first = block.get("first") or block["dates"][0]  # the first observation, before thinning to weeks
    return "1970" if first <= "1970-01-31" else month(first)


# Each indicator: (key, name, what it measures, chart title, intro, unit for the chart).
INDICATORS = [
    ("curve", "10Y-3M curve", "10-year less 3-month Treasury yield", "10Y-3M Treasury curve",
     "The 10-year Treasury yield less the 3-month, in basis points. Below zero, the curve is inverted."),
    ("sahm", "Sahm rule", "Rise in unemployment over its 12-month low", "Sahm rule",
     "How far the 3-month average of the unemployment rate stands above its lowest of the past 12 months, "
     "in percentage points, as published at the time. The rule triggers at 0.50."),
    ("claims", "Initial claims", "New claims for unemployment benefits, weekly", "Initial jobless claims",
     "First claims for unemployment benefits each week, seasonally adjusted, in thousands, with their 4-week average."),
    ("hy", "HY credit spread", "High-yield bonds over Treasuries", "High-yield credit spread",
     "The extra yield on US high-yield corporate bonds over Treasuries, option-adjusted, in basis points."),
    ("nfci", "Chicago Fed NFCI", "National Financial Conditions Index", "Chicago Fed National Financial Conditions Index",
     "A weekly index of US money, debt and equity markets and the banking system. Zero is the average since 1971; "
     "above zero, conditions are tighter than average."),
]


def reading(site, key, b):
    """(latest, its change, signal, signal note, date) for the table, from the block."""
    L = b["latest"]
    a = L.get("ago")
    if key == "curve":
        inv = L["value"] < 0
        return (lvl(L["value"], 0, " bp"),
                site.mv(f'{site.signed(L["value"] - a["value"], 0, " bp")} since {short(a["date"])}') if a else "",
                "Inverted" if inv else "Not inverted",
                f'{"Below" if inv else "At or above"} zero since {day(site, L["since"])}', day(site, L["date"]))
    if key == "sahm":
        hit = L["value"] >= b.get("trigger", 0.5) - 1e-9
        last = L.get("last_trigger")
        return (lvl(L["value"], 2, " pp"),
                site.mv(f'{site.signed(L["value"] - a["value"], 2)} since {month(a["date"])}') if a else "",
                "At or above the 0.50 trigger" if hit else "Below the 0.50 trigger",
                f"Last at or above 0.50 in {month(last)}" if last and not hit else "Trigger: 0.50 percentage point",
                month(L["date"]))
    if key == "claims":
        return (lvl(L["value"], 0, "k"),
                site.mv(f'{site.signed(L["value"] - a["value"], 0, "k")} since {short(a["date"])}') if a else "",
                "No official threshold", f'4-week average {lvl(L["avg"]["value"], 0, "k")}',
                f'Week to {day(site, L["date"])}')
    if key == "hy":
        return (lvl(L["value"], 0, " bp"),
                site.mv(f'{site.signed(L["value"] - a["value"], 0, " bp")} since {short(a["date"])}') if a else "",
                "No official threshold", f'Past year: {lvl(L["low"])} to {lvl(L["high"])} bp', day(site, L["date"]))
    # nfci
    v = L["value"]
    sig = "Tighter than average" if v > 0 else "Looser than average" if v < 0 else "At its average"
    return (lvl(v, 2), site.mv(f'{site.signed(v - a["value"], 2)} since {short(a["date"])}') if a else "", sig,
            f'{"Above" if v > 0 else "At or below"} zero since {day(site, L["since"])}', f'Week to {day(site, L["date"])}')


def payload(data):
    out = {}
    for key, *_ in INDICATORS:
        b = data.get(key)
        if not b:
            continue
        if key == "claims":
            out[key] = {"dates": b["dates"], "series": b["series"]}
        else:
            out[key] = {"dates": b["dates"], "values": b["values"]}
        if key == "sahm":
            out[key]["trigger"] = b.get("trigger", 0.5)
    out["rec"] = (data.get("recessions") or {}).get("periods") or []
    return out


def pages(site):
    """{output path: page HTML}. site is tools/build_site.py, for shell(), icon() and the loaders."""
    data = load(site)
    rec = data.get("recessions")
    rec_src = f'Recessions: {site.esc(rec["source"])}.' if rec else "Recessions: NBER via FRED (USREC), data pending."
    rows, panels = "", ""
    for key, name, what, title, intro in INDICATORS:
        b = data.get(key)
        head = (f'<th scope="row"><a class="rw-name" href="#rw-{key}">{name}</a>'
                f'<span class="cb-sub">{what}</span></th>')
        if b:
            latest, change, sig, note, when = reading(site, key, b)
            rows += (f'<tr>{head}<td data-l="Latest"><span class="cb-fig">{latest}</span><span class="cb-sub">{change}</span></td>'
                     f'<td data-l="Signal"><span class="rw-sig">{sig}</span><span class="cb-sub">{note}</span></td>'
                     f'<td data-l="Date"><span class="rw-date">{when}</span></td></tr>')
            start = first_year(b)
            low = when.replace("Week to", "week to")
            asof = f"Latest {low}" if when.startswith("Week") else f"Latest month {when}" if key == "sahm" else f"As of {when}"
            label = f"{title}, from {start}, with NBER recessions shaded. Latest {latest}, {low}."
            ctl = ""
            if key == "claims":
                ctl = ('<div class="dd__ctl"><div class="dd__cgroup"><span class="cl__glabel" id="rw-scale-l">Scale</span>'
                       '<div class="filters" role="group" aria-labelledby="rw-scale-l">'
                       '<button type="button" class="chip" data-scale="lin" aria-pressed="true">Linear</button>'
                       '<button type="button" class="chip" data-scale="log" aria-pressed="false">Log</button></div></div></div>')
            inner = ctl + site.fr_figure(f"rw-{key}-c", site.esc(label))
            src = f'{site.esc(b["source"])}. {asof}. From {start}{"" if start == "1970" else ", where the series starts"}. {rec_src}'
        else:
            rows += f'<tr>{head}<td colspan="3" class="rw-none"><span class="cb-pending">Data pending</span></td></tr>'
            inner, src = site.FR_PENDING, f"FRED. {rec_src}"
        panels += site.fr_panel(f"rw-{key}", title, intro, inner, src, save=bool(b))
    table = ('<div class="cb-wrap"><table class="cb-tab rw-tab"><caption class="visually-hidden">Latest reading, signal and date of each indicator</caption>'
             '<thead><tr><th scope="col">Indicator</th><th scope="col">Latest</th><th scope="col">Signal</th>'
             f'<th scope="col">Date</th></tr></thead><tbody>{rows}</tbody></table></div>')
    now_p = site.fr_panel("rw-now", "Latest readings",
                          "Each indicator against its own published definition, or the note that it has none. "
                          "Changes are on the reading about a month before.",
                          table, "FRED. Each reading with its own date. No forecast of our own.", save=False)
    ranges = "".join(f'<button type="button" class="chip" data-range="{r}" aria-pressed="{"true" if r == "Max" else "false"}">{r}</button>'
                     for r in ("1Y", "2Y", "5Y", "10Y", "20Y", "Max"))
    stamps = [b["fetched"] for k, b in data.items() if isinstance(b, dict) and b.get("fetched")]
    updated = f"Updated {site.et_stamp(max(stamps))}" if stamps else "Data pending"
    blob = json.dumps(payload(data), separators=(",", ":")).replace("</", "<\\/")
    body = f"""<main id="main" class="page dd fr rw">
  <div class="wrap dd__grid">
    <header class="page__head dd__head">
      <h1 class="page__title">Recession watch</h1>
      <p class="lede">The most watched US recession indicators, each with its latest reading, its history with recessions shaded and its source.</p>
      <p class="note__meta"><span>FRED: Federal Reserve, BLS, Department of Labor, ICE BofA, Chicago Fed, NBER</span><span>{updated}</span><span>Refreshed each weekday</span></p>
    </header>
    <div class="dd__main fr__main">
      {now_p}
      <div class="fr__range dd__ctl rw-range"><div class="dd__cgroup"><span class="cl__glabel" id="rw-range-l">Range, for the charts</span>
        <div class="filters dd__ranges" role="group" aria-labelledby="rw-range-l">{ranges}</div></div></div>
      {panels}
    </div>
    <div class="page__body dd__text">
      <section aria-labelledby="rw-how"><h2 id="rw-how">How to read it</h2><p>The curve is inverted when 3-month bills yield more than 10-year notes; it turned negative before most US recessions since the 1970s, with long and variable lags. The Sahm rule marks the start of a recession when the 3-month average of the unemployment rate rises 0.50 percentage point or more above its lowest 3-month average of the previous 12 months; this real-time version uses the unemployment rate as it was published at the time. Initial claims count the people filing a first claim for unemployment benefits each week; the 4-week average smooths the weekly noise. The high-yield spread is the extra yield investors ask to hold the bonds of lower-rated US companies rather than Treasuries. The Chicago Fed's index reads positive when financial conditions are tighter than average and negative when they are looser, by the Chicago Fed's own definition.</p><p>Shaded periods are recessions as the NBER dates them, from the month after a peak to the trough.</p></section>
      <section aria-labelledby="rw-lim"><h2 id="rw-lim">Limits</h2><p>No indicator here is a forecast, and this page makes none: no probability, no call. Indicators like these have signalled recessions that did not come, and turned late on others. Claims and the high-yield spread have no official threshold. The NBER dates a recession only months after it starts, so the latest months are never shaded. Claims are revised; the page shows the figures as last published.</p></section>
      <section aria-labelledby="rw-src"><h2 id="rw-src">Sources and method</h2><p>All series from FRED: T10Y3M (from the Federal Reserve's Treasury yields), SAHMREALTIME (from the BLS unemployment rate), ICSA and IC4WSA (US Department of Labor), BAMLH0A0HYM2 (ICE BofA US High Yield Index), NFCI (Federal Reserve Bank of Chicago) and USREC (NBER). Each chart starts in 1970, or where its series starts. Daily series older than two years are shown one point a week. Fetched each weekday; a series that does not answer keeps its last figures, with their date.</p><p>For information only. Not investment advice.</p></section>
    </div>
  </div>
</main>
<script type="application/json" id="rw-data">{blob}</script>"""
    return {"recession-watch/": site.shell(
        title="Recession watch: Andra Markets",
        desc="The 10Y-3M Treasury curve, the Sahm rule, initial jobless claims, the high-yield credit spread and the "
             "Chicago Fed's financial conditions index, with NBER recessions shaded since 1970. By Andra Markets.",
        body=body, home="../", base="../", path="recession-watch/", scripts=("recession.js",))}
