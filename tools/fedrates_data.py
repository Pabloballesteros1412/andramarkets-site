#!/usr/bin/env python3
"""Fetch the figures behind the Fed & Rates section (fed-rates/), at deploy time.

Run by .github/workflows/pages.yml before tools/build_site.py. Writes one
file, .cache/fedrates/fedrates.json, with one block per part of the page,
each with its own source, as-of date and fetch time. build_site.py embeds it
in the page; nothing here is published as a file.

Two modes:

    python3 tools/fedrates_data.py          full: every block (each deploy,
                                            and the daily refreshes)
    python3 tools/fedrates_data.py --fast   only what moves during the session:
                                            fed funds futures (meeting odds and
                                            the expected path) and the Cboe
                                            Treasury yield indices. Run on the
                                            market strip schedule, every 15
                                            minutes while the NYSE is open.

Sources:
    US Treasury     daily par yield curve and real yield curve (CSV), the
                    primary source for the curve, spreads' latest day and the
                    10-year real yield's latest day
    FRED            DGS1MO to DGS30 (curve backup), T10Y2Y and T10Y3M,
                    DFEDTARU and DFEDTARL, EFFR, FEDFUNDS, CPIAUCSL, PCEPILFE,
                    UNRATE, DFII10, T5YIE, T10YIE and T5YIFR, with FRED_API_KEY
    Federal Reserve the FOMC calendar (tools/calendar_data.py parses it)
    Yahoo Finance   CBOT 30-day fed funds futures (ZQ), delayed about 10
                    minutes; Cboe yield indices ^IRX, ^FVX, ^TNX and ^TYX,
                    delayed about 15 minutes

Meeting probabilities follow the method CME Group publishes for FedWatch: each
contract settles on its month's average effective rate, so the rate after a
meeting is the month's implied rate with the days before the decision taken
out; a month with no meeting anchors the rate going into the next one.

A block whose source fails keeps its last good copy (restored by the
workflow's cache) with its own date; a failure never stops the deploy.

Environment:
    FRED_API_KEY  FRED API key (repository secret); never printed
"""
import calendar as cal
import csv
import datetime as dt
import io
import json
import math
import sys
import urllib.parse
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard_data import MONTH_CODES, fred, get, log, yahoo  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "fedrates" / "fedrates.json"
NY = ZoneInfo("America/New_York")
UTC = dt.timezone.utc

TENORS = [("1M", 1 / 12, "DGS1MO"), ("3M", 0.25, "DGS3MO"), ("6M", 0.5, "DGS6MO"), ("1Y", 1, "DGS1"),
          ("2Y", 2, "DGS2"), ("3Y", 3, "DGS3"), ("5Y", 5, "DGS5"), ("7Y", 7, "DGS7"), ("10Y", 10, "DGS10"),
          ("20Y", 20, "DGS20"), ("30Y", 30, "DGS30")]
LABELS = [t for t, *_ in TENORS]
# Cboe yield indices on Yahoo: the 13-week bill stands in for 3M.
INTRADAY = [("3M", "^IRX"), ("5Y", "^FVX"), ("10Y", "^TNX"), ("30Y", "^TYX")]
DAILY_YEARS = 2  # older daily history is thinned to one point a week


def iso(d):
    return d.isoformat()


def now_utc():
    return dt.datetime.now(UTC)


def stamp(block, source, asof):
    block.update(source=source, asof=iso(asof), fetched=now_utc().isoformat(timespec="seconds"))
    return block


# US Treasury ------------------------------------------------------------------

TREASURY = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
            "daily-treasury-rates.csv/{y}/all?type={kind}&field_tdr_date_value={y}&page&_format=csv")


def tenor_label(head):
    """'1 Mo' -> '1M', '10 Yr' -> '10Y', '30 YR' -> '30Y'; None for others (1.5 Month, 4 Mo...)."""
    parts = head.strip().lower().replace("month", "mo").replace("year", "yr").split()
    if len(parts) != 2 or parts[1].rstrip("s") not in ("mo", "yr"):
        return None
    try:
        n = float(parts[0])
    except ValueError:
        return None
    lb = f"{n:g}{'M' if parts[1].startswith('mo') else 'Y'}"
    return lb if lb in LABELS else None


def treasury(kind, years):
    """{date: {tenor: yield}} from the Treasury's daily CSV for the given years."""
    out = {}
    for y in years:
        raw = get(TREASURY.format(y=y, kind=kind), headers={"Accept": "text/csv,*/*"}).decode("utf-8-sig", "replace")
        rows = list(csv.reader(io.StringIO(raw)))
        if not rows or "date" not in rows[0][0].lower():
            raise ValueError(f"Treasury {kind} {y}: unexpected CSV")
        cols = [(i, tenor_label(h)) for i, h in enumerate(rows[0])]
        for r in rows[1:]:
            try:
                d = dt.datetime.strptime(r[0].strip(), "%m/%d/%Y").date()
            except (ValueError, IndexError):
                continue
            vals = {}
            for i, lb in cols:
                if lb and i < len(r):
                    try:
                        v = float(r[i])
                    except ValueError:
                        continue
                    if math.isfinite(v):
                        vals[lb] = v
            if vals:
                out[d] = vals
    if not out:
        raise ValueError(f"Treasury {kind}: no rows")
    return out


# Helpers ------------------------------------------------------------------------

def at_or_before(days, d):
    best = None
    for x in days:
        if x > d:
            break
        best = x
    return best


def aligned(series, start=None, daily_from=None):
    """One date axis for several [(date, value)] series: daily from daily_from,
    one point a week (the week's last observation) before it. None where a
    series has no value."""
    daily_from = daily_from or (dt.date.today() - dt.timedelta(days=365 * DAILY_YEARS))
    by = [dict(s) for s in series]
    weekly = []
    for s in series:
        w = {}
        for d, v in s:
            if d < daily_from:
                w[d.isocalendar()[:2]] = v
        weekly.append(w)
    days = sorted(set().union(*(set(b) for b in by)))
    if start:
        days = [d for d in days if d >= start]
    keep, seen = [], {}
    for d in days:
        if d >= daily_from:
            keep.append(d)
        else:
            seen[d.isocalendar()[:2]] = d  # the week's last date
    keep = sorted(set(seen.values())) + keep
    vals = []
    for b, w in zip(by, weekly):
        vals.append([round(b[d], 3) if d >= daily_from and d in b else
                     (round(w[d.isocalendar()[:2]], 3) if d < daily_from and d.isocalendar()[:2] in w else None)
                     for d in keep])
    return [iso(d) for d in keep], vals


def yoy(rows):
    """Year-on-year change (%) of a monthly index."""
    by = dict(rows)
    out = []
    for d, v in rows:
        prev = by.get(d.replace(year=d.year - 1))
        if prev:
            out.append((d, round((v / prev - 1) * 100, 2)))
    return out


# Blocks -------------------------------------------------------------------------

def b_curve():
    """Today's curve against the day before, a week, a month and a year ago."""
    today = dt.date.today()
    curves, source = {}, []
    try:
        fr = fred([f for *_, f in TENORS], today - dt.timedelta(days=400))
        for lb, _, f in TENORS:
            for d, v in fr[f]:
                curves.setdefault(d, {})[lb] = v
        source.append("FRED (DGS1MO to DGS30)")
    except (OSError, ValueError) as e:
        log(f"curve: FRED: {e}", "warning")
    try:
        for d, c in treasury("daily_treasury_yield_curve", [today.year - 1, today.year]).items():
            curves.setdefault(d, {}).update(c)  # the Treasury's own figures take precedence
        source.insert(0, "US Treasury, daily par yield curve")
    except (OSError, ValueError) as e:
        log(f"curve: Treasury: {e}", "warning")
    days = sorted(d for d, c in curves.items() if all(lb in c for lb in LABELS))
    if len(days) < 30:
        raise LookupError("too few complete curves")
    last = days[-1]
    picks = {"now": last, "1D": days[-2]}
    for k, back in (("1W", dt.timedelta(days=7)), ("1M", dt.timedelta(days=30)), ("1Y", dt.timedelta(days=365))):
        d = at_or_before(days, last - back)
        if d:
            picks[k] = d
    block = {"tenors": LABELS, "years": [round(y, 4) for _, y, _ in TENORS],
             "curves": {k: [curves[d][lb] for lb in LABELS] for k, d in picks.items()},
             "dates": {k: iso(d) for k, d in picks.items()}}
    return stamp(block, "; ".join(source), last), curves


def b_intraday():
    """Cboe yield indices: last price and time, while it is newer than the official curve."""
    pts = []
    for lb, sym in INTRADAY:
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?"
               + urllib.parse.urlencode({"range": "5d", "interval": "1d"}))
        meta = json.loads(get(url))["chart"]["result"][0]["meta"]
        v, t = meta.get("regularMarketPrice"), meta.get("regularMarketTime")
        if not isinstance(v, (int, float)) or not t:
            continue
        v = v / 10 if v > 20 else v  # older quotes were the yield times ten
        pts.append({"tenor": lb, "value": round(v, 3),
                    "time": dt.datetime.fromtimestamp(t, UTC).isoformat(timespec="seconds")})
    if not pts:
        raise LookupError("no Cboe yield index answered")
    latest = max(p["time"] for p in pts)
    return {"points": pts, "time": latest, "source": "Cboe yield indices, Yahoo Finance, delayed",
            "fetched": now_utc().isoformat(timespec="seconds")}


def b_spreads(curves):
    start = dt.date(1976, 1, 1)
    s = fred(["T10Y2Y", "T10Y3M"], start)
    rows = {k: list(v) for k, v in s.items()}
    # The Treasury's curve is out the same evening; FRED's spreads a day later.
    for sid, a, b in (("T10Y2Y", "10Y", "2Y"), ("T10Y3M", "10Y", "3M")):
        last = rows[sid][-1][0]
        for d in sorted(curves):
            c = curves[d]
            if d > last and a in c and b in c:
                rows[sid].append((d, round(c[a] - c[b], 2)))
    dates, vals = aligned([rows["T10Y2Y"], rows["T10Y3M"]])
    asof = max(rows["T10Y2Y"][-1][0], rows["T10Y3M"][-1][0])
    block = {"dates": dates, "unit": "bp",
             "series": [{"name": "2s10s", "values": vals[0]}, {"name": "3m10y", "values": vals[1]}]}
    return stamp(block, "FRED (T10Y2Y, T10Y3M); US Treasury for the latest day", asof)


def b_macro():
    start = dt.date(1959, 1, 1)
    s = fred(["FEDFUNDS", "CPIAUCSL", "PCEPILFE", "UNRATE"], start)
    series = [s["FEDFUNDS"], yoy(s["CPIAUCSL"]), yoy(s["PCEPILFE"]), s["UNRATE"]]
    series = [[(d, v) for d, v in x if d >= dt.date(1960, 1, 1)] for x in series]
    days = sorted(set().union(*(set(d for d, _ in x) for x in series)))
    vals = [[round(dict(x)[d], 2) if d in dict(x) else None for d in days] for x in series]
    names = ["Fed funds", "CPI", "Core PCE", "Unemployment"]
    latest = {n: {"value": x[-1][1], "month": iso(x[-1][0]), "prev": x[-2][1]} for n, x in zip(names, series)}
    block = {"dates": [iso(d) for d in days], "unit": "%", "monthly": True, "latest": latest,
             "series": [{"name": n, "values": v} for n, v in zip(names, vals)]}
    return stamp(block, "FRED (FEDFUNDS, CPIAUCSL, PCEPILFE, UNRATE); BLS, BEA, Federal Reserve", max(x[-1][0] for x in series))


def b_real():
    today = dt.date.today()
    s = fred(["DFII10", "T5YIE", "T10YIE", "T5YIFR"], dt.date(2003, 1, 1))
    rows = {k: list(v) for k, v in s.items()}
    source = "FRED (DFII10, T5YIE, T10YIE, T5YIFR)"
    try:
        real = treasury("daily_treasury_real_yield_curve", [today.year])
        last = rows["DFII10"][-1][0]
        extra = [(d, c["10Y"]) for d, c in sorted(real.items()) if d > last and "10Y" in c]
        rows["DFII10"] += extra
        source = "US Treasury, real yield curve; " + source
    except (OSError, ValueError) as e:
        log(f"real: Treasury: {e}", "warning")
    order = ["DFII10", "T5YIE", "T10YIE", "T5YIFR"]
    dates, vals = aligned([rows[k] for k in order])
    names = ["10Y real", "5Y breakeven", "10Y breakeven", "5y5y"]
    latest = {n: {"value": rows[k][-1][1], "date": iso(rows[k][-1][0]), "prev": rows[k][-2][1]} for n, k in zip(names, order)}
    block = {"dates": dates, "unit": "%", "latest": latest,
             "series": [{"name": n, "values": v} for n, v in zip(names, vals)]}
    return stamp(block, source, max(rows[k][-1][0] for k in order))


def b_policy():
    today = dt.date.today()
    s = fred(["DFEDTARU", "DFEDTARL", "EFFR"], dt.date(2008, 12, 16))
    up, lo, effr = s["DFEDTARU"], dict(s["DFEDTARL"]), s["EFFR"]
    last_change = None
    for i in range(len(up) - 1, 0, -1):
        if up[i][1] != up[i - 1][1]:
            last_change = {"date": iso(up[i][0]), "bp": round((up[i][1] - up[i - 1][1]) * 100)}
            break
    # Target upper bound by day, for the decision at each past meeting.
    hist = {iso(d): v for d, v in up if d >= today - dt.timedelta(days=400)}
    block = {"upper": up[-1][1], "lower": lo.get(up[-1][0], up[-1][1] - 0.25), "effr": effr[-1][1],
             "effr_date": iso(effr[-1][0]), "effr_prev": effr[-2][1], "last_change": last_change,
             "effr_hist": {iso(d): v for d, v in effr if d >= today - dt.timedelta(days=120)}, "upper_hist": hist}
    return stamp(block, "Federal Reserve via FRED (DFEDTARU, DFEDTARL); Federal Reserve Bank of New York via FRED (EFFR)",
                 max(up[-1][0], effr[-1][0]))


def b_fomc():
    from calendar_data import fomc_meetings
    meetings = sorted({(a, b) for a, b, _ in fomc_meetings()})
    rows = [{"first": iso(a), "last": iso(b), "sep": b.month in (3, 6, 9, 12),
             "decision": dt.datetime(b.year, b.month, b.day, 14, 0, tzinfo=NY).astimezone(UTC).isoformat()}
            for a, b in meetings]
    return stamp({"meetings": rows}, "Federal Reserve, FOMC calendar", dt.date.today())


# Fed funds futures ---------------------------------------------------------------

def contract_months(today, n=15):
    out = []
    for i in range(n):
        y, m = divmod(today.month - 1 + i, 12)
        out.append((today.year + y, m + 1))
    return out


def symbol(y, m):
    return f"ZQ{MONTH_CODES[m - 1]}{y % 100:02d}.CBT"


def last_price(sym):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?"
           + urllib.parse.urlencode({"range": "5d", "interval": "1d"}))
    meta = json.loads(get(url))["chart"]["result"][0]["meta"]
    v, t = meta.get("regularMarketPrice"), meta.get("regularMarketTime")
    if not isinstance(v, (int, float)) or not 80 < v <= 100 or not t:
        raise ValueError(f"{sym}: no price")
    return v, dt.datetime.fromtimestamp(t, UTC)


def b_futures(full, old):
    """Current price of each contract; in full mode also the settlement about a
    month ago, for the path as it was priced then."""
    today = dt.date.today()
    prices, times, ago = {}, [], (old or {}).get("ago") if not full else None
    hist = {}
    for y, m in contract_months(today):
        key, sym = f"{y}-{m:02d}", symbol(y, m)
        try:
            v, t = last_price(sym)
        except Exception as e:  # noqa: BLE001  a contract Yahoo does not list ends the path
            log(f"{sym}: {type(e).__name__}: {e}", "warning")
            break
        prices[key] = v
        times.append(t)
        if full:
            try:
                hist[key] = dict(yahoo(sym, "3mo"))
            except Exception as e:  # noqa: BLE001
                log(f"{sym} history: {type(e).__name__}: {e}", "warning")
    if len(prices) < 4:
        raise LookupError("too few fed funds futures")
    if full and hist:
        days = sorted(set.intersection(*(set(h) for h in hist.values())))
        d = at_or_before(days, today - dt.timedelta(days=30))
        if d:
            ago = {"date": iso(d), "prices": {k: h[d] for k, h in hist.items()}}
    ago = ago or (old or {}).get("ago")
    latest = max(times)
    return {"prices": prices, "time": latest.isoformat(timespec="seconds"), "ago": ago,
            "source": "CBOT 30-day fed funds futures, Yahoo Finance, delayed about 10 minutes",
            "asof": iso(latest.astimezone(NY).date()), "fetched": now_utc().isoformat(timespec="seconds")}


def implied_path(prices, effr, meetings, after):
    """Expected effective rate after each meeting decided after `after` (a UTC
    datetime), from contract prices {YYYY-MM: price}. Returns [(meeting, start, end)]."""
    rate = {k: 100 - v for k, v in prices.items()}
    upcoming = [m for m in meetings if dt.datetime.fromisoformat(m["decision"]) > after]
    months_with = {m["last"][:7] for m in upcoming}
    out, start = [], effr
    for mt in upcoming:
        d = dt.date.fromisoformat(mt["last"])
        key = mt["last"][:7]
        y, mo = d.year, d.month
        prev_key = f"{y - (mo == 1)}-{(mo - 2) % 12 + 1:02d}"
        nxt_key = f"{y + (mo == 12)}-{mo % 12 + 1:02d}"
        if out and prev_key in rate and prev_key not in months_with:
            start = rate[prev_key]  # a month without a meeting anchors the rate going in
        n = cal.monthrange(y, mo)[1]
        if n - d.day < 7 and nxt_key in rate and nxt_key not in months_with:
            end = rate[nxt_key]  # late in the month: the next month is cleaner
        elif key in rate:
            end = (rate[key] * n - start * d.day) / (n - d.day)
        else:
            break
        out.append((mt, start, end))
        start = end
    return out


def odds(start, end):
    """Probabilities of 25 bp outcomes from an expected change, as [(bp, p)]."""
    steps = (end - start) * 100 / 25
    lo = math.floor(steps)
    frac = steps - lo
    out = {lo * 25: 1 - frac, (lo + 1) * 25: frac}
    for bp in (-25, 0, 25):
        out.setdefault(bp, 0.0)
    return sorted(((bp, round(max(0.0, p), 4)) for bp, p in out.items() if p > 0.0005 or bp in (-25, 0, 25)),
                  key=lambda x: x[0])


def b_odds(fut, policy, fomc):
    meetings = fomc["meetings"]
    now = dt.datetime.fromisoformat(fut["time"])
    path = implied_path(fut["prices"], policy["effr"], meetings, now)
    if not path:
        raise LookupError("no meeting the futures cover")
    first, start, end = path[0]
    block = {"meeting": first["last"], "start": round(start, 4), "change_bp": round((end - start) * 100, 1),
             "probs": [{"bp": bp, "p": p} for bp, p in odds(start, end)],
             "path": [{"meeting": m["last"], "rate": round(e, 4)} for m, _, e in path],
             "time": fut["time"], "source": "Andra Markets calculation from CBOT 30-day fed funds futures",
             "fetched": now_utc().isoformat(timespec="seconds")}
    ago = fut.get("ago")
    if ago:
        d = dt.date.fromisoformat(ago["date"])
        eh = policy.get("effr_hist") or {}
        prior = [k for k in eh if k <= ago["date"]]
        effr_then = eh[max(prior)] if prior else policy["effr"]
        then = dt.datetime(d.year, d.month, d.day, 21, 0, tzinfo=UTC)
        past = {m["last"]: e for m, _, e in implied_path(ago["prices"], effr_then, meetings, then)}
        block["ago"] = {"date": ago["date"], "path": [round(past[p["meeting"]], 4) if p["meeting"] in past else None
                                                       for p in block["path"]]}
    return block


# Main ---------------------------------------------------------------------------------

def main():
    fast = "--fast" in sys.argv
    try:
        data = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}

    def run(key, fn):
        try:
            data[key] = fn()
            print(f"{key}: {data[key].get('asof') or data[key].get('time')}")
            return True
        except Exception as e:  # noqa: BLE001  one source failing never stops the deploy
            kept = (data.get(key) or {}).get("asof") or (data.get(key) or {}).get("time") or "none"
            log(f"fedrates {key}: {type(e).__name__}: {e}; keeping the last copy ({kept})", "warning")
            return False

    if not fast:
        curves = {}

        def curve():
            nonlocal curves
            block, curves = b_curve()
            return block
        run("curve", curve)
        run("spreads", lambda: b_spreads(curves))
        run("macro", b_macro)
        run("real", b_real)
        run("policy", b_policy)
        run("fomc", b_fomc)
    run("intraday", b_intraday)
    if run("futures", lambda: b_futures(not fast, data.get("futures"))) or not fast:
        if data.get("futures") and data.get("policy") and data.get("fomc"):
            run("odds", lambda: b_odds(data["futures"], data["policy"], data["fomc"]))
    data["updated"] = now_utc().isoformat(timespec="seconds")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    main()
