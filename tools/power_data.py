#!/usr/bin/env python3
"""Fetch the figures behind Hedge Fund Data: Power and passengers, a few times a day.

Run by .github/workflows/hedgefund-data.yml; a part fetched in the last six
hours is not fetched again. Writes .cache/hf/power.json (schema
"andra.power/1", Actions cache, never committed or published):

    power       electricity demand, each day for three years, in megawatt
                hours, for the lower 48 states and the grids where data
                centres gather (PJM with northern Virginia, ERCOT in Texas)
                and the other large ones; and each hour of the last 14 days
                for the lower 48 (EIA Hourly Electric Grid Monitor, EIA_API_KEY).
                A day is compared with the same weekday a year earlier, since
                demand follows the week and the weather.
    passengers  people screened at US airport checkpoints each day (TSA). The
                TSA page refuses some automated clients; when it does, the
                part keeps its last copy and the run says so.

A failed part keeps its last good copy with its own date.

    python3 tools/power_data.py [--force]

Environment:
    EIA_API_KEY   EIA open data key (repository secret).
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard_data import get, log  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "hf" / "power.json"
SCHEMA = "andra.power/1"
EIA = "https://api.eia.gov/v2/electricity/rto/"
# (EIA respondent, the page's name)
GRIDS = [("US48", "Lower 48 states"), ("PJM", "PJM (Mid-Atlantic, incl. northern Virginia)"), ("ERCO", "ERCOT (Texas)"),
         ("MISO", "MISO (Midwest)"), ("CISO", "California ISO"), ("SWPP", "Southwest Power Pool"),
         ("NYIS", "New York ISO"), ("ISNE", "ISO New England"), ("SOCO", "Southern Company"), ("TVA", "Tennessee Valley Authority")]
DAILY_DAYS, HOURLY_DAYS = 3 * 366, 14
TSA = "https://www.tsa.gov/travel/passenger-volumes"
TSA_UA = {"User-Agent": "AndraMarketsSite/1.0 (https://github.com/Pabloballesteros1412/andramarkets-site)"}
REFRESH_HOURS = 6


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def eia(path, params, key):
    rows, offset = [], 0
    while True:
        q = [("api_key", key), ("data[0]", "value"), ("offset", offset), ("length", 5000)] + params
        d = json.loads(get(EIA + path + "?" + urllib.parse.urlencode(q), limit=40 * 1024 * 1024))
        part = (d.get("response") or {}).get("data") or []
        rows += part
        if len(part) < 5000:
            return rows
        offset += len(part)


def power():
    key = (os.environ.get("EIA_API_KEY") or "").strip()
    if not key:
        raise ValueError("EIA_API_KEY is not set")
    start = (now_utc().date() - dt.timedelta(days=DAILY_DAYS)).isoformat()
    params = [("frequency", "daily"), ("facets[type][]", "D"), ("facets[timezone][]", "Eastern"), ("start", start),
              ("sort[0][column]", "period"), ("sort[0][direction]", "asc")] + [("facets[respondent][]", g) for g, _ in GRIDS]
    rows = eia("daily-region-data/data/", params, key)
    by = {}
    for r in rows:
        if r.get("value") not in (None, ""):
            by.setdefault(r["respondent"], {})[r["period"]] = round(float(r["value"]))
    grids = []
    for code, name in GRIDS:
        d = by.get(code)
        if not d:
            log(f"EIA: no daily demand for {code}", "warning")
            continue
        days = sorted(d)
        first = dt.date.fromisoformat(days[0])
        n = (dt.date.fromisoformat(days[-1]) - first).days + 1
        grids.append({"code": code, "name": name, "first": days[0], "mwh": [d.get((first + dt.timedelta(days=i)).isoformat()) for i in range(n)]})
    if not grids:
        raise ValueError("EIA returned no daily demand")
    hstart = (now_utc() - dt.timedelta(days=HOURLY_DAYS)).strftime("%Y-%m-%dT%H")
    hrows = eia("region-data/data/", [("frequency", "hourly"), ("facets[type][]", "D"), ("facets[respondent][]", "US48"),
                                      ("start", hstart), ("sort[0][column]", "period"), ("sort[0][direction]", "asc")], key)
    hourly = [[r["period"], round(float(r["value"]))] for r in hrows if r.get("value") not in (None, "")]
    return {"fetched": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"), "unit": "MWh", "grids": grids,
            "hourly_us48_utc": hourly, "source": "U.S. Energy Information Administration, Hourly Electric Grid Monitor"}


def passengers():
    html = get(TSA, headers=TSA_UA, limit=10 * 1024 * 1024).decode("utf-8", "replace")
    rows = re.findall(r"<td[^>]*>\s*(\d{1,2}/\d{1,2}/\d{4})\s*</td>\s*<td[^>]*>\s*([\d,]+)\s*</td>", html)
    days = {}
    for d, n in rows:
        m, dd, y = (int(x) for x in d.split("/"))
        days[dt.date(y, m, dd).isoformat()] = int(n.replace(",", ""))
    if len(days) < 30:
        raise ValueError(f"TSA page held {len(days)} days")
    return {"fetched": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"), "days": dict(sorted(days.items())),
            "source": "Transportation Security Administration, checkpoint travel numbers"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    try:
        old = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = {}
    out = {"schema": SCHEMA, "power": old.get("power"), "passengers": old.get("passengers")}
    fresh = (now_utc() - dt.timedelta(hours=REFRESH_HOURS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    did = False
    for part, fn in (("power", power), ("passengers", passengers)):
        if not a.force and (out[part] or {}).get("fetched", "") >= fresh:
            continue
        try:
            out[part] = fn()
            did = True
            log(f"{part}: fetched")
        except Exception as e:  # noqa: BLE001
            log(f"{part} failed, keeping the last copy: {type(e).__name__}: {e}", "warning")
    if not did:
        return 0 if (out["power"] or out["passengers"]) else 1
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    log(f"Wrote {CACHE.relative_to(ROOT)} ({CACHE.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
