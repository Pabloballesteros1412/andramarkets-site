#!/usr/bin/env python3
"""Fetch the figures behind Hedge Fund Data: From orbit, every three hours.

Run by .github/workflows/hedgefund-data.yml; a run within three hours of the
last fetch does nothing. Writes .cache/hf/orbit.json (schema "andra.orbit/1",
Actions cache, never committed or published):

    thermal   every heat anomaly the VIIRS instruments on NASA and NOAA
              satellites detected on Earth in the last 24 hours (NASA FIRMS,
              near real time, NASA_FIRMS_MAP_KEY): fires, gas flares and
              industrial heat. Kept: the 4,000 most intense detections for
              the map, and for each region in REGIONS (oil fields that flare
              gas, refining and conflict zones, the forests behind farm and
              insurance losses) the day's count and radiative power, with a
              daily history for 400 days built from the samples.
    lights    night lights are drawn by the page straight from NASA GIBS
              (the VIIRS Black Marble composite), which needs no key; this
              script records only the layer and its tile address. Measured
              night light (NASA Black Marble VNP46, NASA_EARTHDATA_TOKEN) is a
              later step.

A failed source keeps its last good copy with its own date.

    python3 tools/orbit_data.py [--force]

Environment:
    NASA_FIRMS_MAP_KEY   FIRMS map key (repository secret).
"""
import argparse
import csv
import datetime as dt
import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard_data import get, log  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "hf" / "orbit.json"
SCHEMA = "andra.orbit/1"
FIRMS = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/{source}/world/1"
SOURCES = ["VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT", "VIIRS_SNPP_NRT"]
TOP_POINTS, KEEP_DAYS, REFRESH_HOURS = 4000, 400, 3
# (key, the page's name, why it matters, west, south, east, north)
REGIONS = [
    ("permian", "Permian Basin", "Gas flaring at US oil wells", -104.5, 30.5, -100.5, 33.5),
    ("bakken", "Bakken", "Gas flaring at US oil wells", -104.5, 46.5, -102.0, 48.9),
    ("alberta", "Alberta oil sands", "Canadian oil output, and the wildfires that stop it", -120.0, 54.0, -110.0, 60.0),
    ("gulf_states", "Persian Gulf", "Gulf oil and gas", 48.0, 24.0, 57.0, 30.5),
    ("iraq", "Iraq", "Iraqi oil fields", 43.0, 29.5, 48.5, 36.5),
    ("libya", "Libya", "Libyan oil output", 9.0, 25.0, 25.0, 33.0),
    ("niger_delta", "Niger Delta", "Nigerian oil and flaring", 5.0, 4.0, 8.0, 6.5),
    ("w_siberia", "Western Siberia", "Russian oil fields", 65.0, 58.0, 80.0, 64.0),
    ("w_russia", "European Russia", "Russian refineries", 35.0, 43.0, 52.0, 57.0),
    ("ukraine", "Ukraine", "War damage to energy and industry", 22.0, 44.0, 40.5, 52.5),
    ("levant", "Israel, Gaza and Lebanon", "Conflict", 34.0, 29.5, 36.7, 34.7),
    ("venezuela", "Venezuela", "Venezuelan oil", -73.0, 0.5, -59.5, 12.5),
    ("california", "California", "Wildfires and utility and insurance losses", -124.5, 32.5, -114.0, 42.0),
    ("amazon", "Amazon basin", "Forest clearing for soy and cattle", -75.0, -15.0, -45.0, 5.0),
    ("se_asia", "Indonesia and Malaysia", "Palm oil land clearing and haze", 95.0, -8.0, 141.0, 6.0),
    ("australia", "Australia", "Bushfires", 113.0, -44.0, 154.0, -10.0),
]
# Checked on 27 Nov 2026: the Black Marble composite serves tiles at GoogleMapsCompatible_Level8 for date
# 2016-01-01. The daily day/night band layers did not answer for a recent date; they need checking when the page is built.
GIBS = {"Black Marble (2016 composite)": "VIIRS_Black_Marble"}


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def thermal(key, old):
    pts = {}
    for src in SOURCES:
        try:
            raw = get(FIRMS.format(key=key, source=src), limit=200 * 1024 * 1024).decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            log(f"FIRMS {src}: {type(e).__name__}: {e}", "warning")
            continue
        if raw.lstrip().lower().startswith(("invalid", "error", "<")):
            raise ValueError(f"FIRMS {src}: {raw[:120].strip()}")
        for r in csv.DictReader(io.StringIO(raw)):
            try:
                lat, lon, frp = float(r["latitude"]), float(r["longitude"]), float(r.get("frp") or 0)
            except (KeyError, ValueError):
                continue
            if (r.get("confidence") or "").lower() in ("l", "low"):
                continue
            # The satellites overlap: one place seen twice in the same hour is one detection.
            k = (round(lat, 2), round(lon, 2), r.get("acq_date"), (r.get("acq_time") or "")[:2])
            if k not in pts or frp > pts[k][2]:
                pts[k] = [round(lon, 4), round(lat, 4), round(frp, 1), r.get("acq_date"), r.get("acq_time"), r.get("daynight")]
    if not pts:
        raise ValueError("FIRMS returned no detections")
    points = list(pts.values())
    regions = {}
    for key_, name, why, w, s, e, n in REGIONS:
        inside = [p for p in points if w <= p[0] <= e and s <= p[1] <= n]
        regions[key_] = {"count": len(inside), "frp": round(sum(p[2] for p in inside))}
    day = now_utc().date().isoformat()
    hist = dict((old or {}).get("history") or {})
    hist[day] = {"total": len(points), "regions": regions}  # the day's latest 24-hour window
    cut = (now_utc().date() - dt.timedelta(days=KEEP_DAYS)).isoformat()
    hist = {k: v for k, v in sorted(hist.items()) if k >= cut}
    return {"fetched": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"), "window_hours": 24, "total": len(points),
            "points_fields": ["lon", "lat", "frp_mw", "date", "time_utc", "day_night"],
            "points": sorted(points, key=lambda p: -p[2])[:TOP_POINTS],
            "regions": [{"key": k, "name": n, "why": y, "bbox": [w, s, e, nn]} for k, n, y, w, s, e, nn in REGIONS],
            "latest": regions, "history": hist,
            "source": "NASA FIRMS, VIIRS 375 m near real time (NOAA-20, NOAA-21, Suomi NPP)"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    try:
        old = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = {}
    fresh = (now_utc() - dt.timedelta(hours=REFRESH_HOURS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not a.force and (old.get("thermal") or {}).get("fetched", "") >= fresh:
        return 0
    key = (os.environ.get("NASA_FIRMS_MAP_KEY") or "").strip()
    if not key:
        log("From orbit: NASA_FIRMS_MAP_KEY is not set", "warning")
        return 0
    out = {"schema": SCHEMA, "thermal": old.get("thermal"),
           "lights": {"gibs_layers": GIBS, "tiles": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{layer}/default/{date}/GoogleMapsCompatible_Level8/{z}/{y}/{x}.png",
                      "source": "NASA GIBS (VIIRS), no key"}}
    try:
        out["thermal"] = thermal(key, old.get("thermal"))
        t = out["thermal"]
        log(f"FIRMS: {t['total']} detections in 24 hours; " + ", ".join(f"{k} {v['count']}" for k, v in t["latest"].items()))
    except Exception as e:  # noqa: BLE001
        log(f"FIRMS failed, keeping the last copy: {type(e).__name__}: {e}", "warning")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
