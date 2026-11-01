"""Central banks (central-banks/): the Fed, the ECB, the Bank of England and the
Bank of Japan in one table (policy rate, last move, next meeting with a
countdown) and the four rates since 2019 on one chart. Owner-approved sketch,
1 Nov 2026; built on the Fed & Rates page grid and panels (DESIGN.md).

Figures from .cache/centralbanks/centralbanks.json (tools/centralbanks_data.py);
decision dates from that file, the calendar (.cache/calendar/calendar.json) and
Fed & Rates' FOMC calendar. A bank with no figures yet says "Data pending".
assets/centralbanks.js draws the chart and keeps the countdowns current.
"""
import datetime as dt
import json

CHART_FROM = "2019-01-01"
BANKS = [  # key, short name, full name, what the rate is, calendar title of its decisions
    ("fed", "Fed", "Federal Reserve", "target range", "FOMC rate decision"),
    ("ecb", "ECB", "European Central Bank", "deposit facility rate", "ECB rate decision"),
    ("boe", "BoE", "Bank of England", "Bank Rate", "Bank of England rate decision and minutes"),
    ("boj", "BoJ", "Bank of Japan", "policy rate", "Bank of Japan rate decision"),
]
CHART_NAME = {"fed": "Fed, top of the target range", "ecb": "ECB, deposit facility rate", "boe": "BoE, Bank Rate",
              "boj": "BoJ, policy rate"}


def load(site):
    try:
        return json.loads((site.ROOT / ".cache" / "centralbanks" / "centralbanks.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def next_days(key, title, data, cal, fed, today):
    """Upcoming decision days (ISO, the bank's own date), from every source that has them."""
    days = {m["day"] for m in ((data.get("meetings") or {}).get(key) or {}).get("dates") or []}
    days |= {e["date"] for e in (cal.get("events") or {}).values()
             if e.get("src") == key and e.get("title") == title and e.get("date")}
    if key == "fed":
        days |= {m["last"] for m in ((fed.get("fomc") or {}).get("meetings") or [])}
    return sorted(d for d in days if d >= today.isoformat())[:4]


def in_days(n):
    return "Today" if n == 0 else "Tomorrow" if n == 1 else f"In {n} days"


def level_text(site, key, r):
    if key == "fed" and r.get("lower") is not None:
        return f'{r["lower"]:.2f} to {r["level"]:.2f}%'
    return site.pct(r["level"])


def move_text(site, bp):
    dec = 0 if abs(bp - round(bp)) < 0.05 else 1
    return site.mv(site.signed(bp, dec, " bp"))


def from_chart(st):
    """Steps from CHART_FROM: the level in force that day, then each change."""
    if st[0][0] > CHART_FROM:  # a series that starts later starts where it starts
        return st
    at = [p for p in st if p[0] <= CHART_FROM][-1][1]
    return [[CHART_FROM, at]] + [p for p in st if p[0] > CHART_FROM]


def chart_payload(rates):
    banks = []
    for key, short, *_ in BANKS:
        r = rates.get(key)
        if not r or not r.get("steps"):
            continue
        b = {"key": key, "name": short, "label": CHART_NAME[key], "asof": r["asof"], "steps": from_chart(r["steps"])}
        if key == "fed" and r.get("lower_steps"):
            b["lower"] = from_chart(r["lower_steps"])
        banks.append(b)
    return {"from": CHART_FROM, "banks": banks}


def pages(site):
    """{output path: page HTML}. site is tools/build_site.py, for shell(), icon() and the loaders."""
    data, cal, fed = load(site), site.load_calendar(), site.load_fedrates()
    rates = data.get("rates") or {}
    today = dt.datetime.now(site.NY).date()
    pending = '<span class="cb-pending">Data pending</span>'
    rows, latest = "", []
    for key, short, full, what, title in BANKS:
        r = rates.get(key)
        name = (f'<a class="cb-bank" href="../fed-rates/">{short}{site.icon("arrow-right")}</a>' if key == "fed"
                else f'<span class="cb-bank">{short}</span>')
        sub = f"{full}, {what}" + (". More in Fed &amp; Rates" if key == "fed" else "")
        if r:
            lv = (f'<span class="cb-fig">{level_text(site, key, r)}</span>'
                  f'<span class="cb-sub">As of {site.day_med(dt.date.fromisoformat(r["asof"]))}</span>')
            lm = r.get("last_move")
            mv_ = (f'<span class="cb-fig">{move_text(site, lm["bp"])}</span>'
                   f'<span class="cb-sub">{site.day_med(dt.date.fromisoformat(lm["date"]))}</span>') if lm else pending
            latest.append(f'{short} {level_text(site, key, r)}')
        else:
            lv, mv_ = pending, pending
        nxt = next_days(key, title, data, cal, fed, today)
        if nxt:
            d0 = dt.date.fromisoformat(nxt[0])
            nx = (f'<span class="cb-fig" data-cb-day>{site.day_med(d0)}</span>'
                  f'<span class="cb-sub" data-cb-in>{in_days((d0 - today).days)}</span>')
        else:
            nx = pending
        attr = f' data-next="{site.esc(json.dumps(nxt))}"' if nxt else ""
        rows += (f'<tr{attr}>'
                 f'<th scope="row">{name}<span class="cb-sub">{sub}</span></th>'
                 f'<td data-l="Policy rate">{lv}</td><td data-l="Last move">{mv_}</td><td data-l="Next meeting">{nx}</td></tr>')
    table = ('<div class="cb-wrap"><table class="cb-tab"><caption class="visually-hidden">Policy rate, last move and next meeting of each bank</caption>'
             '<thead><tr><th scope="col">Bank</th><th scope="col">Policy rate</th><th scope="col">Last move</th>'
             f'<th scope="col">Next meeting</th></tr></thead><tbody>{rows}</tbody></table></div>')
    srcs = [rates[k]["source"] for k, *_ in BANKS if rates.get(k)]
    now_src = (("; ".join(site.esc(s) for s in srcs) + ". ") if srcs else "Each central bank, FRED and the BIS. ")
    now_src += "Next meetings from each bank's own calendar, as read for the Calendar. Days counted in New York time."
    now_p = site.fr_panel("cb-now", "Policy rates now",
                          "Each bank's policy rate, its last change and the day of its next decision.",
                          table, now_src, save=False)
    payload = chart_payload(rates)
    if payload["banks"]:
        asof = max(b["asof"] for b in payload["banks"])
        label = (f"Policy rates since {site.day_med(dt.date.fromisoformat(CHART_FROM))}: "
                 + ", ".join(CHART_NAME[b["key"]] for b in payload["banks"]) + ". Latest: " + ", ".join(latest) + ".")
        inner = site.fr_figure("cb-chart", site.esc(label))
        chart_src = f'{"; ".join(site.esc(s) for s in srcs)}. As of {site.day_med(dt.date.fromisoformat(asof))}.'
    else:
        inner, chart_src = site.FR_PENDING, "Each central bank, FRED and the BIS."
    chart_p = site.fr_panel("cb-rates", "The four rates since 2019",
                            "Each rate as it stood every day. The Fed's line is the top of its target range.",
                            inner, chart_src, save=bool(payload["banks"]))
    stamps = [x["fetched"] for grp in ("rates", "meetings") for x in (data.get(grp) or {}).values() if x.get("fetched")]
    updated = f"Updated {site.et_stamp(max(stamps))}" if stamps else "Data pending"
    blob = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    body = f"""<main id="main" class="page dd fr cb">
  <div class="wrap dd__grid">
    <header class="page__head dd__head">
      <h1 class="page__title">Central banks</h1>
      <p class="lede">The Fed, the ECB, the Bank of England and the Bank of Japan: each policy rate, its last move and the next decision, and the four rates since 2019.</p>
      <p class="note__meta"><span>Federal Reserve, ECB, Bank of England, BIS, FRED</span><span>{updated}</span><span>Refreshed each weekday</span></p>
    </header>
    <div class="dd__main fr__main">
      {now_p}{chart_p}
    </div>
    <div class="page__body dd__text">
      <section aria-labelledby="cb-how"><h2 id="cb-how">How to read it</h2><p>Each bank sets one rate that steers what banks pay to borrow overnight. The Fed sets a target range for the federal funds rate. The ECB steers through its deposit facility rate, the rate it pays on banks' overnight deposits. The Bank of England sets Bank Rate. The Bank of Japan has targeted the overnight call rate since March 2024; from 2016 until then it charged −0.1% on part of the balances banks hold with it.</p><p>A move is the change from the level before, in basis points: one basis point is 0.01 percentage point. Its date is the day the new rate took effect, as each series records it: the day after the decision for the Fed, usually the following Wednesday for the ECB, the day of the decision for the Bank of England.</p></section>
      <section aria-labelledby="cb-src"><h2 id="cb-src">Sources and method</h2><p>The Fed's target range from the Federal Reserve via FRED (DFEDTARU and DFEDTARL). The ECB's deposit facility rate from the ECB Data Portal, which lists the days it changed, or FRED (ECBDFR) when the portal does not answer. Bank Rate from the Bank of England's database (IUDBEDR), with the BIS as backup. The Bank of Japan's rate from the BIS central bank policy rate series (WS_CBPOL). Meeting dates from each bank's own calendar, the same pages the economic calendar reads. Fetched each weekday; a source that does not answer keeps its last figures, with their date.</p><p>For information only. Not investment advice.</p></section>
    </div>
  </div>
</main>
<script type="application/json" id="cb-data">{blob}</script>"""
    return {"central-banks/": site.shell(
        title="Central banks: Andra Markets",
        desc="The policy rates of the Fed, the ECB, the Bank of England and the Bank of Japan: the latest level, the last "
             "move, the next meeting and the four rates since 2019. By Andra Markets.",
        body=body, home="../", base="../", path="central-banks/", scripts=("centralbanks.js",))}
