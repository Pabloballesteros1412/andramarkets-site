#!/usr/bin/env python3
"""Fetch the daily FX analyses and the FX market table, at deploy time.

Run by .github/workflows/pages.yml before tools/build_site.py. Writes
.cache/fx/fx.json (Actions cache, never committed or published):

    analyses   one record per NYSE session, from the agent's daily FX
               analysis (Pabloballesteros1412/andramarkets, PR 14): the file
               fx_YYYYMMDD_r<run>.json in each archive-YYYY-MM-DD release,
               schema "andra.fx/1". Only files with that exact name, in an
               archive-* release, are read (the agent's rule).
    market     the dollar index, the G10 majors and the main emerging-market
               pairs from Yahoo Finance: last close and the moves over a day,
               a week, a month and the year so far, as each pair is quoted,
               and two years of daily closes for the page's charts.
    rates      each currency's 3-month interbank rate and the US's, from the
               OECD (monthly, one request): the rate differential the page's
               scatter plots each currency's move against. A currency the OECD
               has no figure for is left off the scatter.

An analysis is shown only when every check passes: the schema is
andra.fx/1, the date is an NYSE trading day that is not in the future, the
run was not a demo, the figure check passed (audit.ok), no trade language
was flagged, and the close note for that session is published
(data/notes/<date>.json, "published" not false): a session whose note is
held for review, or taken down, shows no FX analysis either. Where a session has
several runs, the run behind its published close note is used, else the
newest run that passes. Each analysis keeps only the text and the figures
the page shows.

    python3 tools/fx_data.py

Environment:
    AGENT_ARTIFACTS_TOKEN  fine-grained token on the agent repo (Contents: read)
    AGENT_REPO             default Pabloballesteros1412/andramarkets
"""
import datetime as dt
import json
import math
import os
import re
import sys
import time
import urllib.error
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nyse  # noqa: E402
from dashboard_data import API, AGENT_REPO, get, log, yahoo  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NOTES = ROOT / "data" / "notes"
CACHE = ROOT / ".cache" / "fx" / "fx.json"
SCHEMA = "andra.fx/1"
NAME = re.compile(r"fx_(\d{8})_r(\d+)\.json")
SECTIONS = ["dollar", "majors", "em", "drivers", "levels", "ahead"]
MAX_FX = 2 * 1024 * 1024

# The market table: (key, pair, Yahoo symbol, group, what the quote is, decimals).
PAIRS = [
    ("dxy", "Dollar index (DXY)", "DX-Y.NYB", "dollar", "index", 2),
    ("eurusd", "EUR/USD", "EURUSD=X", "major", "USD per EUR", 4),
    ("usdjpy", "USD/JPY", "JPY=X", "major", "JPY per USD", 2),
    ("gbpusd", "GBP/USD", "GBPUSD=X", "major", "USD per GBP", 4),
    ("usdchf", "USD/CHF", "CHF=X", "major", "CHF per USD", 4),
    ("usdcad", "USD/CAD", "CAD=X", "major", "CAD per USD", 4),
    ("audusd", "AUD/USD", "AUDUSD=X", "major", "USD per AUD", 4),
    ("nzdusd", "NZD/USD", "NZDUSD=X", "major", "USD per NZD", 4),
    ("usdcny", "USD/CNY", "CNY=X", "em", "CNY per USD", 4),
    ("usdmxn", "USD/MXN", "MXN=X", "em", "MXN per USD", 4),
    ("usdbrl", "USD/BRL", "BRL=X", "em", "BRL per USD", 4),
    ("usdinr", "USD/INR", "INR=X", "em", "INR per USD", 2),
    ("usdkrw", "USD/KRW", "KRW=X", "em", "KRW per USD", 1),
    ("usdzar", "USD/ZAR", "ZAR=X", "em", "ZAR per USD", 4),
    ("usdtry", "USD/TRY", "TRY=X", "em", "TRY per USD", 4),
]


def num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def text(v, limit=4000):
    return v.strip()[:limit] if isinstance(v, str) else ""


# The agent's archive ------------------------------------------------------------

def api(path, token, accept="application/vnd.github+json", limit=None):
    headers = {"Accept": accept, "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return get(API + path, headers, **({"limit": limit} if limit else {}))


def archived_files(token):
    """{(date, run id): asset id} for every fx_YYYYMMDD_r<run>.json in an archive-* release."""
    out, page = {}, 1
    while True:
        rel = json.loads(api(f"/repos/{AGENT_REPO}/releases?per_page=100&page={page}", token))
        for r in rel:
            if not str(r.get("tag_name", "")).startswith("archive-"):
                continue
            for a in r.get("assets") or []:
                m = NAME.fullmatch(a.get("name", ""))
                if m:
                    d = m.group(1)
                    out[(f"{d[:4]}-{d[4:6]}-{d[6:]}", int(m.group(2)))] = a["id"]
        if len(rel) < 100:
            break
        page += 1
    return out


def note_runs():
    """{date: (published, run id)} from the close note records."""
    out = {}
    for f in NOTES.glob("*.json"):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        out[rec.get("date")] = (rec.get("published") is not False, (rec.get("source") or {}).get("run_id"))
    return out


def check(rec, day, today):
    """Why an analysis may not be shown, or None when it passes."""
    if rec.get("schema") != SCHEMA:
        return f"schema {rec.get('schema')!r}"
    if rec.get("date") != day:
        return f"dated {rec.get('date')} in the file named for {day}"
    d = dt.date.fromisoformat(day)
    if d > today:
        return "dated in the future"
    if nyse.is_trading_day(d) is not True:
        return "not an NYSE trading day"
    if rec.get("mode") not in ("model", "quantitative"):
        return f"mode {rec.get('mode')!r}"
    if not (rec.get("audit") or {}).get("ok"):
        return "the figure check failed"
    if rec.get("trade_language_flags"):
        return "trade language flagged"
    if not text(rec.get("headline")):
        return "no headline"
    return None


def keep(rec):
    """Only what the page shows: the text and the pair figures."""
    secs = {s.get("id"): s for s in rec.get("sections") or [] if isinstance(s, dict)}
    pairs = []
    for p in (rec.get("facts") or {}).get("pairs") or []:
        if not isinstance(p, dict) or not text(p.get("key"), 20):
            continue
        cv = p.get("ccy_vs_usd") if isinstance(p.get("ccy_vs_usd"), dict) else {}
        pol = p.get("policy") if isinstance(p.get("policy"), dict) else None
        pairs.append({
            "key": text(p["key"], 20), "name": text(p.get("name"), 40), "group": text(p.get("group"), 10),
            "quote": text(p.get("quote"), 30), "dec": int(p["dec"]) if num(p.get("dec")) is not None else 4,
            "last": num(p.get("last")), "d1": num(p.get("d1")), "w1": num(p.get("w1")), "m1": num(p.get("m1")),
            "ytd": num(p.get("ytd")), "ccy_d1": num(cv.get("d1")), "off_session": bool(p.get("off_session")),
            "policy": {"short": text(pol.get("short"), 20), "rate": num(pol.get("rate")),
                       "vs_fed_bp": num(pol.get("vs_fed_bp"))} if pol and num(pol.get("rate")) is not None else None})
    return {
        "date": rec["date"], "edition": rec.get("edition") if isinstance(rec.get("edition"), (int, str)) else None,
        "mode": rec["mode"], "headline": text(rec.get("headline"), 300), "standfirst": text(rec.get("standfirst"), 800),
        "takeaways": [text(t, 600) for t in rec.get("takeaways") or [] if text(t)][:8],
        "sections": [{"id": sid, "title": text((secs.get(sid) or {}).get("title"), 80),
                      "paragraphs": [text(x) for x in (secs.get(sid) or {}).get("paragraphs") or [] if text(x)][:24]}
                     for sid in SECTIONS],
        "word_count": num(rec.get("word_count")),
        "pairs": pairs,
    }


def analyses(cache, token, today):
    files = archived_files(token)
    notes = note_runs()
    by_day = {}
    for (day, run), aid in files.items():
        by_day.setdefault(day, []).append((run, aid))
    held = cache.setdefault("held", {})
    out = cache.setdefault("analyses", {})
    for day, runs in sorted(by_day.items()):
        published, note_run = notes.get(day, (False, None))
        if not published:
            out.pop(day, None)
            held[day] = ("the close note for this session is taken down" if day in notes
                         else "the close note for this session is not published (held or not yet imported)")
            continue
        # The run behind the published close note first, then the newest.
        runs.sort(key=lambda r: (r[0] == note_run, r[0]), reverse=True)
        if day in out and out[day].get("run") == runs[0][0]:
            continue  # already read
        why = None
        for run, aid in runs:
            try:
                rec = json.loads(api(f"/repos/{AGENT_REPO}/releases/assets/{aid}", token,
                                     "application/octet-stream", MAX_FX))
            except (OSError, ValueError) as e:
                why = f"{type(e).__name__}: {e}"[:200]
                continue
            why = check(rec, day, today)
            if why is None:
                out[day] = {**keep(rec), "run": run}
                held.pop(day, None)
                break
        if why:
            held[day] = why
            log(f"fx: {day} not shown: {why}", "warning")


# The market table -------------------------------------------------------------------

def moves(closes):
    """Last close and the moves over 1D, 1W, 1M and YTD, as the pair is quoted."""
    days = [d for d, _ in closes]
    by = dict(closes)
    last_d, last = closes[-1]

    def base(d):
        best = None
        for x in days:
            if x > d:
                break
            best = x
        return best
    out = {"last": last, "date": last_d.isoformat()}
    for k, d in (("d1", days[-2] if len(days) > 1 else None), ("w1", base(last_d - dt.timedelta(days=7))),
                 ("m1", base(last_d - dt.timedelta(days=30))), ("ytd", base(dt.date(last_d.year - 1, 12, 31)))):
        out[k] = round((last / by[d] - 1) * 100, 3) if d else None
    return out


def market(cache):
    rows, bad, hist = {}, [], {}
    for key, name, sym, group, quote, dec in PAIRS:
        try:
            closes = yahoo(sym, "2y")
            rows[key] = {"name": name, "group": group, "quote": quote, "dec": dec, **moves(closes)}
            hist[key] = closes
        except Exception as e:  # noqa: BLE001  a pair keeps its last row and history
            bad.append(f"{sym}: {type(e).__name__}: {e}"[:120])
            if key in (cache.get("market") or {}):
                rows[key] = cache["market"][key]
        time.sleep(0.3)
    cache["market"] = rows
    # The charts' history: every pair on one date axis, None where it did not trade.
    old = cache.get("hist") or {}
    days = sorted(set().union(*(set(d for d, _ in c) for c in hist.values()))) if hist else []
    series = {}
    for key, *_ in PAIRS:
        if key in hist:
            by, dec = dict(hist[key]), rows[key]["dec"] + 2
            series[key] = [round(by[d], dec) if d in by else None for d in days]
        elif key in (old.get("series") or {}) and old.get("dates"):
            # A pair that failed keeps its last history, re-aligned to today's axis.
            by = dict(zip(old["dates"], old["series"][key]))
            series[key] = [by.get(d.isoformat()) for d in days]
    if series:
        cache["hist"] = {"dates": [d.isoformat() for d in days], "series": series}
    for b in bad:
        log(f"fx: {b}; keeping the last row", "warning")


# The rate differential --------------------------------------------------------------

OECD_IR3 = ("https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_FINMARK,/.M.IR3TIB.PA....."
            "?startPeriod={start}&dimensionAtObservation=AllDimensions")
# The OECD area behind each currency (the euro area for the euro).
RATE_AREA = {"EUR": "EA20", "JPY": "JPN", "GBP": "GBR", "CHF": "CHE", "CAD": "CAN", "AUD": "AUS", "NZD": "NZL",
             "CNY": "CHN", "MXN": "MEX", "BRL": "BRA", "INR": "IND", "KRW": "KOR", "ZAR": "ZAF", "TRY": "TUR",
             "USD": "USA"}
FRESH_RATE = 183  # days: an older monthly figure is left off rather than plotted as current


def rates(cache):
    import csv
    import io
    start = f"{dt.date.today().year - 1}-01"
    raw = get(OECD_IR3.format(start=start), {"Accept": "application/vnd.sdmx.data+csv; charset=utf-8"}).decode("utf-8")
    best = {}
    for r in csv.DictReader(io.StringIO(raw)):
        v = num(float(r["OBS_VALUE"])) if r.get("OBS_VALUE") else None
        if v is not None and r["TIME_PERIOD"] > best.get(r["REF_AREA"], ("",))[0]:
            best[r["REF_AREA"]] = (r["TIME_PERIOD"], round(v, 3))
    today = dt.date.today()
    out = {}
    for ccy, area in RATE_AREA.items():
        got = best.get(area)
        if got and (today - dt.date.fromisoformat(got[0] + "-01")).days <= FRESH_RATE:
            out[ccy] = {"rate": got[1], "month": got[0]}
    if "USD" not in out:
        raise ValueError("OECD 3-month rates: no recent US figure")
    cache["rates"] = out


def main():
    try:
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    today = dt.datetime.now(ZoneInfo("America/New_York")).date()
    market(cache)
    try:
        rates(cache)
    except Exception as e:  # noqa: BLE001  the scatter keeps the last rates
        log(f"fx: OECD 3-month rates: {type(e).__name__}: {e}; keeping the last ones", "warning")
    try:
        analyses(cache, os.environ.get("AGENT_ARTIFACTS_TOKEN"), today)
        cache["archive_ok"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    except Exception as e:  # noqa: BLE001  the page keeps the analyses it has
        why = f"{type(e).__name__}: {e}"
        if isinstance(e, urllib.error.HTTPError):
            try:
                why += f" ({json.loads(e.read(4096)).get('message')})"
            except Exception:  # noqa: BLE001
                pass
        log(f"fx: agent archive unavailable, {why}; keeping the analyses already read", "warning")
    cache["updated"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    print(f"fx: {len(cache.get('market') or {})} pairs, {len(cache.get('analyses') or {})} analyses, "
          f"{len(cache.get('held') or {})} not shown")


if __name__ == "__main__":
    main()
