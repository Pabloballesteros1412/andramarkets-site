#!/usr/bin/env python3
"""Fetch the figures behind Hedge Fund Data: Jets, every 30 minutes.

Run by .github/workflows/hedgefund-data.yml. Writes .cache/hf/jets.json
(schema "andra.jets/1", Actions cache, never committed or published):

    sky        every aircraft OpenSky's receivers hear at the moment of the
               sample: how many are airborne, worldwide and by region.
    bizjets    the business jets among them (by ICAO type code, from
               OpenSky's aircraft database): where each is, and how many are
               at or over the airfields where business aviation gathers
               (Teterboro, Van Nuys, Le Bourget, Geneva and others).
    history    the counts above at every sample for 14 days, and a daily
               figure (the day's average) for 400 days.

Only types and counts are kept: no owner, operator or registrant, and no
person is named (DESIGN.md: no personal names). Aircraft whose owners asked
for them not to be shown (FAA LADD, PIA) are not in OpenSky's public feed.

    python3 tools/jets_data.py

Environment:
    OPENSKY_CLIENT_ID, OPENSKY_CLIENT_SECRET   OpenSky API client (repository
        secrets). Without them the run asks anonymously, with a lower quota.
"""
import csv
import datetime as dt
import io
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard_data import UA, get, log  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "hf" / "jets.json"
TYPES = ROOT / ".cache" / "hf" / "jets_types.json"  # icao24 -> type code, business jets only
SCHEMA = "andra.jets/1"

TOKEN = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
STATES = "https://opensky-network.org/api/states/all?extended=1"
DB_BUCKET = "https://s3.opensky-network.org/data-samples"
DB_FALLBACK = ["https://s3.opensky-network.org/data-samples/metadata/aircraftDatabase.csv",
               "https://opensky-network.org/datasets/metadata/aircraftDatabase.csv"]
DB_DAYS = 30  # the type table is rebuilt once a month

# ICAO type designators of business jets (Gulfstream, Bombardier, Dassault,
# Embraer, Cessna Citation, Learjet, Hawker, Pilatus PC-24, HondaJet, Cirrus Vision).
BIZ = set("""GLF2 GLF3 GLF4 GLF5 GLF6 GLF7 GA5C GA6C GA7C GA8C G150 G280 GALX ASTR
GLEX GL5T GL7T GL8T CL30 CL35 CL60 E35L E50P E55P E545 E550 LJ31 LJ35 LJ40 LJ45 LJ55 LJ60 LJ70 LJ75
F2TH F900 FA10 FA20 FA50 FA6X FA7X FA8X C25A C25B C25C C25M C500 C501 C510 C525 C526 C550 C551 C560
C56X C650 C680 C68A C700 C750 H25A H25B H25C HA4T BE40 PRM1 HDJT PC24 SF50 EA50""".split())

# Airfields where business aviation gathers: (code, name, lat, lon). Counted within 15 km, on the ground or below 3,000 m.
HUBS = [("KTEB", "Teterboro", 40.850, -74.061), ("KHPN", "White Plains", 41.067, -73.708),
        ("KVNY", "Van Nuys", 34.210, -118.490), ("KPBI", "Palm Beach", 26.683, -80.096),
        ("KOMA", "Omaha", 41.303, -95.894), ("KIAD", "Washington Dulles", 38.944, -77.456),
        ("KSJC", "San Jose", 37.363, -121.929), ("KASE", "Aspen", 39.223, -106.869),
        ("EGLF", "Farnborough", 51.275, -0.776), ("LFPB", "Paris Le Bourget", 48.969, 2.441),
        ("LSGG", "Geneva", 46.238, 6.109), ("LSZH", "Zurich", 47.458, 8.548),
        ("OMDW", "Dubai World Central", 24.896, 55.161), ("VHHH", "Hong Kong", 22.308, 113.918),
        ("WSSL", "Singapore Seletar", 1.417, 103.868)]
HUB_KM, HUB_ALT = 15, 3000

REGIONS = [("North America", 15, 72, -170, -50), ("Europe", 34, 72, -25, 45), ("China", 18, 54, 73, 135),
           ("Rest of Asia and Oceania", -50, 55, 60, 180), ("Middle East", 12, 42, 34, 63),
           ("Latin America", -56, 15, -120, -30), ("Africa", -36, 37, -20, 52)]
KEEP_SAMPLES_DAYS, KEEP_DAILY_DAYS = 14, 400


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def load(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def save(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, separators=(",", ":")), encoding="utf-8")
    tmp.replace(p)


def token():
    cid = (os.environ.get("OPENSKY_CLIENT_ID") or "").strip()
    sec = (os.environ.get("OPENSKY_CLIENT_SECRET") or "").strip()
    if not cid or not sec:
        log("OpenSky: no API client set, asking anonymously", "warning")
        return None
    body = urllib.parse.urlencode({"grant_type": "client_credentials", "client_id": cid, "client_secret": sec}).encode()
    req = urllib.request.Request(TOKEN, data=body, headers={"User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read())["access_token"]


def type_table(old):
    """icao24 -> ICAO type code for the business jets in OpenSky's aircraft database, rebuilt monthly."""
    if old and old.get("built", "") >= (now_utc() - dt.timedelta(days=DB_DAYS)).strftime("%Y-%m-%d"):
        return old
    urls = []
    try:  # the newest complete database in OpenSky's public bucket
        xml = get(f"{DB_BUCKET}?prefix=metadata/", limit=5 * 1024 * 1024).decode("utf-8", "replace")
        keys = sorted(re.findall(r"<Key>(metadata/aircraft-database-complete-\d{4}-\d{2}\.csv)</Key>", xml))
        urls += [f"{DB_BUCKET}/{k}" for k in reversed(keys[-2:])]
    except Exception as e:  # noqa: BLE001
        log(f"OpenSky bucket listing failed: {type(e).__name__}: {e}", "warning")
    for url in urls + DB_FALLBACK:
        try:
            raw = get(url, limit=400 * 1024 * 1024).decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            log(f"Aircraft database {url}: {type(e).__name__}: {e}", "warning")
            continue
        rows = csv.reader(io.StringIO(raw), quotechar="'" if raw[:200].count("'") > raw[:200].count('"') else '"')
        head = [h.strip().strip("'\"").lower() for h in next(rows)]
        try:
            i_icao, i_type = head.index("icao24"), head.index("typecode")
        except ValueError:
            log(f"Aircraft database {url}: columns {head[:12]}", "warning")
            continue
        table = {}
        for r in rows:
            if len(r) > max(i_icao, i_type):
                t = r[i_type].strip().upper()
                if t in BIZ:
                    table[r[i_icao].strip().lower()] = t
        if len(table) > 1000:
            log(f"Aircraft database {url.rsplit('/', 1)[-1]}: {len(table)} business jets")
            return {"built": now_utc().strftime("%Y-%m-%d"), "source": url, "types": table}
    if old:
        log("Aircraft database: no new copy, keeping the last", "warning")
        return old
    raise ValueError("no aircraft database could be read")


def km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


def region(lat, lon):
    for name, la0, la1, lo0, lo1 in REGIONS:
        if la0 <= lat <= la1 and lo0 <= lon <= lo1:
            return name
    return "Elsewhere"


def snapshot(tok, types):
    headers = {"Authorization": f"Bearer {tok}"} if tok else {}
    d = json.loads(get(STATES, headers=headers, limit=60 * 1024 * 1024))
    states = d.get("states") or []
    if not states:
        raise ValueError("OpenSky returned no aircraft")
    airborne, by_region, jets, hubs = 0, {}, [], {h[0]: 0 for h in HUBS}
    for s in states:
        icao, lon, lat, baro, ground, vel, track, geo = s[0], s[5], s[6], s[7], s[8], s[9], s[10], s[13]
        if lat is None or lon is None:
            continue
        if not ground:
            airborne += 1
            r = region(lat, lon)
            by_region[r] = by_region.get(r, 0) + 1
        t = types.get((icao or "").lower())
        if not t:
            continue
        alt = geo if geo is not None else baro
        jets.append([round(lon, 3), round(lat, 3), t, None if alt is None else round(alt), bool(ground),
                     None if vel is None else round(vel * 1.94384), None if track is None else round(track)])
        for code, _, hlat, hlon in HUBS:
            if (ground or (alt is not None and alt < HUB_ALT)) and km(lat, lon, hlat, hlon) <= HUB_KM:
                hubs[code] += 1
    return {"time": d.get("time"), "aircraft": len(states), "airborne": airborne, "by_region": by_region,
            "bizjets": len(jets), "bizjets_airborne": sum(1 for j in jets if not j[4]), "hubs": hubs, "jets": jets}


def main():
    old = load(CACHE) or {}
    try:
        types = type_table(load(TYPES))
        save(TYPES, types)
        snap = snapshot(token(), types["types"])
    except Exception as e:  # noqa: BLE001
        log(f"Jets failed, keeping the last copy: {type(e).__name__}: {e}", "warning")
        return 0 if old else 1

    t = int(snap["time"] or time.time())
    hist = old.get("history") or {"samples": [], "daily": {}}
    hist["samples"].append([t, snap["aircraft"], snap["airborne"], snap["bizjets"], snap["bizjets_airborne"], snap["hubs"]])
    hist["samples"] = [s for s in hist["samples"] if s[0] >= t - KEEP_SAMPLES_DAYS * 86400]
    day = dt.datetime.fromtimestamp(t, dt.timezone.utc).date().isoformat()
    today = [s for s in hist["samples"] if dt.datetime.fromtimestamp(s[0], dt.timezone.utc).date().isoformat() == day]
    mean = lambda i: round(sum(s[i] for s in today) / len(today))  # noqa: E731
    hist["daily"][day] = {"samples": len(today), "airborne": mean(2), "bizjets": mean(3), "bizjets_airborne": mean(4),
                          "hubs": {h[0]: round(sum(s[5].get(h[0], 0) for s in today) / len(today), 1) for h in HUBS}}
    cut = (dt.date.fromisoformat(day) - dt.timedelta(days=KEEP_DAILY_DAYS)).isoformat()
    hist["daily"] = {k: v for k, v in hist["daily"].items() if k >= cut}

    out = {"schema": SCHEMA, "fetched": iso(now_utc()), "source": "The OpenSky Network (opensky-network.org)",
           "hubs": [{"code": c, "name": n, "lat": la, "lon": lo} for c, n, la, lo in HUBS], "latest": snap, "history": hist}
    save(CACHE, out)
    log(f"Jets: {snap['aircraft']} aircraft, {snap['airborne']} airborne, {snap['bizjets']} business jets "
        f"({snap['bizjets_airborne']} airborne); hubs {snap['hubs']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
