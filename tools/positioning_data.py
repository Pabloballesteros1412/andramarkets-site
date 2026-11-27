#!/usr/bin/env python3
"""Fetch the figures behind Hedge Fund Data: Positioning, at each run.

Run by .github/workflows/hedgefund-data.yml. Writes .cache/hf/positioning.json
(schema "andra.positioning/1", Actions cache, never committed or published):

    cot     the Commitments of Traders: each Tuesday, how speculators
            (non-commercial traders) are positioned in the futures that move
            markets (equity indices, Treasuries, the dollar's pairs, oil,
            gas, metals, grains, bitcoin, the VIX): long, short, net, and net
            as a share of open interest, for three years (CFTC, no key;
            published each Friday for the Tuesday before).
    short   short sale volume: the share of each day's volume in every US
            listed share that was a short sale, as FINRA's Reg SHO files
            report it, for the last 30 trading days; the market as a whole,
            and each of the 600 most traded shares. Short volume is not
            short interest: most of it is market makers' hedging, so the
            page reads a share's ratio against its own average, never alone.

A failed source keeps its last good copy with its own date.

    python3 tools/positioning_data.py
"""
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nyse  # noqa: E402
from dashboard_data import get, log  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "hf" / "positioning.json"
SCHEMA = "andra.positioning/1"

COT = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"
COT_YEARS = 3
# CFTC contract market codes: (code, the page's name, group).
CONTRACTS = [
    ("13874A", "E-mini S&P 500", "Equities"), ("209742", "E-mini Nasdaq-100", "Equities"),
    ("239742", "E-mini Russell 2000", "Equities"), ("1170E1", "VIX", "Equities"),
    ("042601", "2-year Treasury note", "Rates"), ("044601", "5-year Treasury note", "Rates"),
    ("043602", "10-year Treasury note", "Rates"), ("020601", "Treasury bond", "Rates"),
    ("045601", "Fed funds", "Rates"),
    ("098662", "US dollar index", "Currencies"), ("099741", "Euro", "Currencies"),
    ("097741", "Japanese yen", "Currencies"), ("096742", "British pound", "Currencies"),
    ("092741", "Swiss franc", "Currencies"), ("090741", "Canadian dollar", "Currencies"),
    ("232741", "Australian dollar", "Currencies"), ("095741", "Mexican peso", "Currencies"),
    ("067651", "WTI crude oil", "Commodities"), ("023651", "Natural gas", "Commodities"),
    ("088691", "Gold", "Commodities"), ("084691", "Silver", "Commodities"),
    ("085692", "Copper", "Commodities"), ("002602", "Corn", "Commodities"),
    ("005602", "Soybeans", "Commodities"), ("001602", "Wheat", "Commodities"),
    ("133741", "Bitcoin", "Crypto"), ("146021", "Ether", "Crypto"),
]

FINRA = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{}.txt"
SHORT_DAYS = 30
SHORT_TOP = 600
MIN_VOLUME = 50_000  # shares a day; thinner names are left out of the files kept


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def cot():
    since = (now_utc().date() - dt.timedelta(days=365 * COT_YEARS)).isoformat()
    codes = ",".join(f"'{c}'" for c, _, _ in CONTRACTS)
    q = urllib.parse.urlencode({
        "$select": "report_date_as_yyyy_mm_dd,cftc_contract_market_code,open_interest_all,"
                   "noncomm_positions_long_all,noncomm_positions_short_all,comm_positions_long_all,comm_positions_short_all",
        "$where": f"cftc_contract_market_code in({codes}) AND report_date_as_yyyy_mm_dd >= '{since}'",
        "$order": "report_date_as_yyyy_mm_dd", "$limit": 50000})
    rows = json.loads(get(f"{COT}?{q}", limit=40 * 1024 * 1024))
    if not rows:
        raise ValueError("CFTC returned no rows")
    by = {}
    for r in rows:
        oi, lg, sh = num(r["open_interest_all"]), num(r["noncomm_positions_long_all"]), num(r["noncomm_positions_short_all"])
        if not oi or lg is None or sh is None:
            continue
        by.setdefault(r["cftc_contract_market_code"], []).append(
            [r["report_date_as_yyyy_mm_dd"][:10], int(lg), int(sh), int(lg - sh), round((lg - sh) / oi * 100, 2), int(oi),
             int(num(r["comm_positions_long_all"]) or 0) - int(num(r["comm_positions_short_all"]) or 0)])
    out = []
    for code, name, group in CONTRACTS:
        w = by.get(code)
        if not w:
            log(f"CFTC: no rows for {name} ({code})", "warning")
            continue
        nets = [x[4] for x in w]
        lo, hi = min(nets), max(nets)
        out.append({"code": code, "name": name, "group": group,
                    "fields": ["date", "spec_long", "spec_short", "spec_net", "spec_net_pct_oi", "open_interest", "commercial_net"],
                    "weeks": w,
                    # where this week's net sits in its three-year range, 0 (most short) to 100 (most long)
                    "percentile_3y": round((nets[-1] - lo) / (hi - lo) * 100) if hi > lo else None})
    return {"fetched": iso(now_utc()), "as_of": max(c["weeks"][-1][0] for c in out), "contracts": out,
            "source": "CFTC Commitments of Traders, legacy futures only"}


def short_volume(old):
    """Short sale volume per day, for the last SHORT_DAYS sessions; files already held are not fetched again."""
    days = (old or {}).get("days") or {}
    want, d = [], now_utc().date()
    while len(want) < SHORT_DAYS and d > now_utc().date() - dt.timedelta(days=60):
        if nyse.is_trading_day(d):
            want.append(d)
        d -= dt.timedelta(days=1)
    got = 0
    for day in want:
        key = day.isoformat()
        if key in days:
            continue
        try:
            raw = get(FINRA.format(day.strftime("%Y%m%d")), limit=40 * 1024 * 1024).decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):  # not published yet, or no file for that day
                continue
            raise
        rows = {}
        for line in raw.splitlines()[1:]:
            p = line.split("|")
            if len(p) < 5 or not p[1]:
                continue
            sv, tv = num(p[2]), num(p[4])
            if sv is None or not tv or tv < MIN_VOLUME:
                continue
            rows[p[1]] = [round(sv), round(tv)]
        if rows:
            days[key] = rows
            got += 1
        time.sleep(0.2)
    keep = {d.isoformat() for d in want}
    days = {k: v for k, v in days.items() if k in keep}
    if not days:
        raise ValueError("no FINRA short volume file could be read")
    ordered = sorted(days)
    last = days[ordered[-1]]
    top = sorted(last, key=lambda s: -last[s][1])[:SHORT_TOP]
    # The market's ratio over the shares kept (every name trading 50,000 shares a day or more).
    market = [[k, round(sum(v[0] for v in days[k].values()) / sum(v[1] for v in days[k].values()) * 100, 2)] for k in ordered]
    shares = {}
    for s in top:
        series = [[k, round(days[k][s][0] / days[k][s][1] * 100, 1), days[k][s][1]] for k in ordered if s in days[k]]
        ratios = [x[1] for x in series[:-1]]
        shares[s] = {"series": series, "avg": round(sum(ratios) / len(ratios), 1) if ratios else None}
    log(f"FINRA: {got} new days, {len(ordered)} held, {ordered[0]} to {ordered[-1]}")
    return {"fetched": iso(now_utc()), "days": days, "market": market, "shares": shares,
            "source": "FINRA Reg SHO daily short sale volume (consolidated NMS)"}


def main():
    try:
        old = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = {}
    out = {"schema": SCHEMA, "cot": old.get("cot"), "short": old.get("short")}
    try:
        out["cot"] = cot()
        log(f"CFTC: {len(out['cot']['contracts'])} contracts, as of {out['cot']['as_of']}")
    except Exception as e:  # noqa: BLE001
        log(f"CFTC failed, keeping the last copy: {type(e).__name__}: {e}", "warning")
    try:
        out["short"] = short_volume(old.get("short"))
    except Exception as e:  # noqa: BLE001
        log(f"FINRA failed, keeping the last copy: {type(e).__name__}: {e}", "warning")
    if not out["cot"] and not out["short"]:
        log("Positioning: no source has ever been fetched", "error")
        return 1
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    log(f"Wrote {CACHE.relative_to(ROOT)} ({CACHE.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
