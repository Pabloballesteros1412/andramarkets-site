#!/usr/bin/env python3
"""Fetch the figures behind Recession watch (recession-watch/), at deploy time.

Run by .github/workflows/pages.yml before tools/build_site.py. Writes one
file, .cache/recession/recession.json: one block per indicator (its history
from 1970 or from its first observation, its latest reading and the readings
the page compares it with, its source and as-of date) and the NBER recession
periods the charts shade. tools/page_recession_watch.py embeds what the page
draws; nothing here is published as a file.

Sources, all from FRED (FRED_API_KEY), each indicator fetched on its own:
    T10Y3M         10-year less 3-month Treasury constant maturity, daily
    SAHMREALTIME   the Sahm rule recession indicator, real-time, monthly
    ICSA, IC4WSA   initial jobless claims and their 4-week average, weekly
                   (US Department of Labor)
    BAMLH0A0HYM2   ICE BofA US High Yield Index option-adjusted spread, daily
    NFCI           Chicago Fed National Financial Conditions Index, weekly
    USREC          NBER based recession indicator, monthly

Daily history older than two years is kept one point a week (the week's last
observation), as on Fed & Rates. A block whose source fails keeps its last
good copy (restored by the workflow's cache) with its own date; a failure
never stops the deploy. Nothing here forecasts: the page shows each reading
against its own published definition, or says there is none.

    python3 tools/recession_data.py

Environment:
    FRED_API_KEY  FRED API key (repository secret); never printed
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard_data import at_or_before, fred, log, months_back  # noqa: E402
from fedrates_data import aligned  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "recession" / "recession.json"
UTC = dt.timezone.utc
SINCE = dt.date(1970, 1, 1)  # the charts start here, or where a series starts
SAHM_TRIGGER = 0.50  # percentage points, the rule's own threshold


def iso(d):
    return d.isoformat()


def now_utc():
    return dt.datetime.now(UTC)


def stamp(block, source, asof):
    block.update(source=source, asof=iso(asof), fetched=now_utc().isoformat(timespec="seconds"))
    return block


def thin(rows, scale=1.0, dec=2):
    """Dates and values from SINCE: daily for the last two years, weekly before."""
    rows = [(d, v) for d, v in rows if d >= SINCE]
    if not rows:
        raise ValueError("no observations since 1970")
    dates, (vals,) = aligned([rows])
    return dates, [None if v is None else round(v * scale, dec) for v in vals]


def ago(rows, back):
    """The observation on or before the latest date less `back` (a timedelta, or
    a number of months)."""
    days = [d for d, _ in rows]
    last = days[-1]
    target = months_back(last, back) if isinstance(back, int) else last - back
    d = at_or_before(days, target)
    if d is None:
        return None
    return {"date": iso(d), "value": dict(rows)[d]}


def run_start(rows, test):
    """The first date of the latest unbroken run of observations for which test holds as it does now."""
    now = test(rows[-1][1])
    start = rows[-1][0]
    for d, v in reversed(rows):
        if test(v) != now:
            break
        start = d
    return iso(start)


# Indicators ---------------------------------------------------------------------

def b_curve():
    rows = fred(["T10Y3M"], dt.date(1982, 1, 1))["T10Y3M"]
    dates, values = thin(rows, 100, 0)
    last = rows[-1]
    block = {"dates": dates, "values": values, "unit": "bp", "first": iso(rows[0][0]),
             "latest": {"date": iso(last[0]), "value": round(last[1] * 100),
                        "since": run_start(rows, lambda v: v < 0)}}
    a = ago(rows, 1)
    if a:
        block["latest"]["ago"] = {"date": a["date"], "value": round(a["value"] * 100)}
    return stamp(block, "FRED (T10Y3M)", last[0])


def b_sahm():
    rows = fred(["SAHMREALTIME"], dt.date(1959, 1, 1))["SAHMREALTIME"]
    shown = [(d, v) for d, v in rows if d >= SINCE]
    last = rows[-1]
    hits = [d for d, v in rows if v >= SAHM_TRIGGER - 1e-9]
    block = {"dates": [iso(d) for d, _ in shown], "values": [round(v, 2) for _, v in shown], "unit": "pp",
             "monthly": True, "first": iso(rows[0][0]), "trigger": SAHM_TRIGGER,
             "latest": {"date": iso(last[0]), "value": round(last[1], 2),
                        "ago": {"date": iso(rows[-2][0]), "value": round(rows[-2][1], 2)},
                        "last_trigger": iso(hits[-1]) if hits else None}}
    return stamp(block, "FRED (SAHMREALTIME), from the BLS unemployment rate", last[0])


def b_claims():
    s = fred(["ICSA", "IC4WSA"], dt.date(1967, 1, 1))
    ic, avg = s["ICSA"], s["IC4WSA"]
    by = dict(avg)
    shown = [(d, v) for d, v in ic if d >= SINCE]
    a, b = ago(ic, dt.timedelta(days=28)), ago(avg, dt.timedelta(days=28))
    block = {"dates": [iso(d) for d, _ in shown], "unit": "k", "first": iso(ic[0][0]),
             "series": [{"name": "Weekly", "values": [round(v / 1000, 1) for _, v in shown]},
                        {"name": "4-week average", "values": [round(by[d] / 1000, 2) if d in by else None for d, _ in shown]}],
             "latest": {"date": iso(ic[-1][0]), "value": round(ic[-1][1] / 1000, 1),
                        "avg": {"date": iso(avg[-1][0]), "value": round(avg[-1][1] / 1000, 2)}}}
    if a:
        block["latest"]["ago"] = {"date": a["date"], "value": round(a["value"] / 1000, 1)}
    if b:
        block["latest"]["avg"]["ago"] = {"date": b["date"], "value": round(b["value"] / 1000, 2)}
    return stamp(block, "US Department of Labor via FRED (ICSA, IC4WSA)", max(ic[-1][0], avg[-1][0]))


def b_hy():
    rows = fred(["BAMLH0A0HYM2"], dt.date(1996, 12, 1))["BAMLH0A0HYM2"]
    dates, values = thin(rows, 100, 0)
    last = rows[-1]
    year = [v for d, v in rows if d > last[0] - dt.timedelta(days=365)]
    block = {"dates": dates, "values": values, "unit": "bp", "first": iso(rows[0][0]),
             "latest": {"date": iso(last[0]), "value": round(last[1] * 100),
                        "low": round(min(year) * 100), "high": round(max(year) * 100)}}
    a = ago(rows, 1)
    if a:
        block["latest"]["ago"] = {"date": a["date"], "value": round(a["value"] * 100)}
    return stamp(block, "ICE BofA via FRED (BAMLH0A0HYM2)", last[0])


def b_nfci():
    rows = fred(["NFCI"], dt.date(1971, 1, 1))["NFCI"]
    shown = [(d, v) for d, v in rows if d >= SINCE]
    last = rows[-1]
    block = {"dates": [iso(d) for d, _ in shown], "values": [round(v, 3) for _, v in shown], "unit": "index",
             "first": iso(rows[0][0]),
             "latest": {"date": iso(last[0]), "value": round(last[1], 3),
                        "since": run_start(rows, lambda v: v > 0)}}
    a = ago(rows, dt.timedelta(days=28))
    if a:
        block["latest"]["ago"] = {"date": a["date"], "value": round(a["value"], 3)}
    return stamp(block, "Federal Reserve Bank of Chicago via FRED (NFCI)", last[0])


def recession_periods(rows):
    """[[first day, day after the last month]] for each run of months marked 1."""
    out, start, prev = [], None, None
    for d, v in rows:
        if v >= 0.5 and start is None:
            start = d
        if v < 0.5 and start is not None:
            out.append([iso(start), iso(d)])
            start = None
        prev = d
    if start is not None and prev is not None:
        nxt = dt.date(prev.year + (prev.month == 12), prev.month % 12 + 1, 1)
        out.append([iso(start), iso(nxt)])
    return out


def b_recessions():
    rows = fred(["USREC"], dt.date(1960, 1, 1))["USREC"]
    periods = [p for p in recession_periods(rows) if p[1] >= iso(SINCE)]
    if not periods:
        raise ValueError("USREC: no recession since 1970")
    return stamp({"periods": periods}, "NBER via FRED (USREC)", rows[-1][0])


BLOCKS = {"curve": b_curve, "sahm": b_sahm, "claims": b_claims, "hy": b_hy, "nfci": b_nfci, "recessions": b_recessions}


def main():
    try:
        data = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    for key, fn in BLOCKS.items():
        try:
            data[key] = fn()
            print(f"{key}: {data[key]['source']}, {data[key]['asof']}")
        except Exception as e:  # noqa: BLE001  one source failing never stops the deploy
            kept = (data.get(key) or {}).get("asof") or "none"
            log(f"recession {key}: {type(e).__name__}: {e}; keeping the last copy ({kept})", "warning")
    data["updated"] = now_utc().isoformat(timespec="seconds")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    main()
