#!/usr/bin/env python3
"""Fetch the figures behind Hedge Fund Data: Ships, every 30 minutes.

Run by .github/workflows/hedgefund-data.yml. Writes, in the Actions cache
(never committed or published as files):

    .cache/hf/ships.json        schema "andra.ships/1"
        portwatch   daily transit calls through the world's 28 chokepoints, by
                    vessel type, about 400 days (IMF PortWatch, no key).
        ais         where each vessel was last seen: one sample of the global
                    AIS stream from aisstream.io, merged with the samples
                    before it. A vessel keeps its last six positions as a trail
                    and drops out six hours after it was last heard. Nothing
                    is ever moved between samples.
    .cache/hf/ships_static.json what each vessel says about itself (type, name,
                    call sign, IMO, size, destination), kept for 30 days, since
                    a vessel sends it only every six minutes.

aisstream.io relays terrestrial AIS receivers: dense along coasts and in the
straits, thin in the open ocean. A failed source keeps its last good copy
(restored by the workflow's cache) with its own date, and never fails the run
on its own; the run fails only if neither source has ever been fetched.

    python3 tools/ships_data.py [--seconds 150] [--no-ais] [--no-portwatch]

Environment:
    AISSTREAM_API_KEY   aisstream.io key (repository secret). Without it the
                        AIS sample is skipped and the last copy is kept.
"""
import argparse
import asyncio
import datetime as dt
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard_data import get, log  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "hf" / "ships.json"
STATIC = ROOT / ".cache" / "hf" / "ships_static.json"
SCHEMA = "andra.ships/1"

PW = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
PW_DAILY = PW + "Daily_Chokepoints_Data/FeatureServer/0/query"
PW_POINTS = PW + "PortWatch_chokepoints_database/FeatureServer/0/query"
PW_DAYS = 400
PW_FIELDS = ["n_total", "n_tanker", "n_container", "n_dry_bulk", "n_general_cargo", "n_roro", "capacity"]

AIS_URL = "wss://stream.aisstream.io/v0/stream"
KEEP_HOURS = 6        # a vessel not heard for this long leaves the map
TRAIL = 6             # positions kept per vessel, newest last
STATIC_DAYS = 30
MAX_MSGS = 2_000_000  # a guard on one sample, far above a normal one


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, separators=(",", ":")), encoding="utf-8")
    tmp.replace(path)


# IMF PortWatch -----------------------------------------------------------------

def arcgis(url, params):
    """Every row of an ArcGIS feature query, page by page."""
    rows, offset = [], 0
    while True:
        q = {**params, "resultOffset": offset, "resultRecordCount": 2000, "f": "json"}
        d = json.loads(get(url + "?" + urllib.parse.urlencode(q), limit=20 * 1024 * 1024))
        if "error" in d:
            raise ValueError(f"PortWatch: {d['error']}")
        feats = d.get("features", [])
        rows += [f["attributes"] for f in feats]
        if not d.get("exceededTransferLimit") and len(feats) < 2000:
            return rows
        offset += len(feats)


def portwatch():
    since = (now_utc().date() - dt.timedelta(days=PW_DAYS)).isoformat()
    points = arcgis(PW_POINTS, {"where": "1=1", "outFields": "portid,portname,lat,lon", "returnGeometry": "false"})
    rows = arcgis(PW_DAILY, {"where": f"date >= DATE '{since}'", "outFields": "date,portid," + ",".join(PW_FIELDS),
                             "orderByFields": "ObjectId"})
    if not points or not rows:
        raise ValueError("PortWatch returned no rows")
    days = sorted({r["date"][:10] for r in rows})
    index = {d: i for i, d in enumerate(days)}
    by = {}
    for r in rows:
        by.setdefault(r["portid"], {})[index[r["date"][:10]]] = r
    out = []
    for p in sorted(points, key=lambda p: p["portid"]):
        got = by.get(p["portid"], {})
        col = lambda f: [got[i][f] if i in got else None for i in range(len(days))]  # noqa: E731
        gc = [(got[i]["n_general_cargo"] or 0) + (got[i]["n_roro"] or 0) if i in got else None for i in range(len(days))]
        out.append({"id": p["portid"], "name": p["portname"], "lat": round(p["lat"], 4), "lon": round(p["lon"], 4),
                    "total": col("n_total"), "tanker": col("n_tanker"), "container": col("n_container"),
                    "dry_bulk": col("n_dry_bulk"), "other": gc, "capacity": col("capacity")})
    return {"fetched": iso(now_utc()), "first": days[0], "last": days[-1], "chokepoints": out,
            "source": "IMF PortWatch (University of Oxford; AIS from Spire)"}


# aisstream.io ------------------------------------------------------------------

def kind(ais_type):
    """The vessel's AIS ship type as the page groups it."""
    if ais_type is None:
        return None
    if 80 <= ais_type <= 89:
        return "tanker"
    if 70 <= ais_type <= 79:
        return "cargo"
    if 60 <= ais_type <= 69:
        return "passenger"
    if ais_type in (30,):
        return "fishing"
    if ais_type in (31, 32, 52):
        return "tug"
    return "other"


def valid(lat, lon):
    return -90 <= lat <= 90 and -180 <= lon <= 180 and not (lat == 0 and lon == 0)


async def sample(key, seconds):
    """Latest position per vessel and the static reports heard in `seconds` of the global stream."""
    import websockets  # installed by the workflow; only this source needs it

    pos, static, n = {}, {}, 0
    sub = {"APIKey": key, "BoundingBoxes": [[[-90, -180], [90, 180]]],
           "FilterMessageTypes": ["PositionReport", "ShipStaticData"]}
    async with websockets.connect(AIS_URL, max_size=None, open_timeout=30, ping_interval=20) as ws:
        await ws.send(json.dumps(sub))
        end = time.monotonic() + seconds
        while time.monotonic() < end and n < MAX_MSGS:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=max(1.0, min(30.0, end - time.monotonic())))
            except asyncio.TimeoutError:
                if n == 0:
                    raise ValueError("aisstream sent nothing in 30 seconds") from None
                continue
            m = json.loads(raw)
            if "error" in m:  # a bad key or subscription is answered once, then closed
                raise ValueError(f"aisstream: {m['error']}")
            n += 1
            meta, t = m.get("MetaData", {}), m.get("MessageType")
            mmsi = meta.get("MMSI")
            if not isinstance(mmsi, int) or not 100_000_000 <= mmsi <= 999_999_999:
                continue
            body = m.get("Message", {}).get(t, {})
            if t == "ShipStaticData":
                d = body.get("Dimension") or {}
                static[str(mmsi)] = {
                    "type": body.get("Type"), "name": (body.get("Name") or "").strip() or None,
                    "call": (body.get("CallSign") or "").strip() or None, "imo": body.get("ImoNumber") or None,
                    "dest": (body.get("Destination") or "").strip() or None,
                    "len": (d.get("A") or 0) + (d.get("B") or 0) or None, "beam": (d.get("C") or 0) + (d.get("D") or 0) or None,
                    "seen": int(time.time())}
            elif t == "PositionReport":
                lat, lon = body.get("Latitude"), body.get("Longitude")
                if lat is None or lon is None or not valid(lat, lon):
                    continue
                sog, cog, hdg = body.get("Sog"), body.get("Cog"), body.get("TrueHeading")
                pos[str(mmsi)] = [round(lon, 4), round(lat, 4),
                                  None if cog is None or cog >= 360 else round(cog, 1),
                                  None if sog is None or sog >= 102.3 else round(sog, 1),
                                  None if hdg is None or hdg >= 360 else hdg,
                                  int(time.time())]
    return pos, static, n


def merge(prev_vessels, pos, static, now):
    """The vessels map after one sample: new positions appended to trails, the stale dropped."""
    cut = now - KEEP_HOURS * 3600
    out = {}
    for mmsi, v in (prev_vessels or {}).items():
        if v["trail"][-1][2] >= cut:
            out[mmsi] = v
    for mmsi, (lon, lat, cog, sog, hdg, t) in pos.items():
        v = out.get(mmsi) or {"trail": []}
        last = v["trail"][-1] if v["trail"] else None
        if not last or (last[0], last[1]) != (lon, lat):
            v["trail"] = (v["trail"] + [[lon, lat, t]])[-TRAIL:]
        else:
            v["trail"][-1][2] = t
        v.update({"cog": cog, "sog": sog, "hdg": hdg})
        out[mmsi] = v
    for mmsi, v in out.items():
        s = static.get(mmsi) or {}
        v["kind"] = kind(s.get("type"))
    return out


def ais(prev, static_db, seconds):
    key = (os.environ.get("AISSTREAM_API_KEY") or "").strip()
    if not key:
        raise ValueError("AISSTREAM_API_KEY is not set")
    started = now_utc()
    pos, static, n = asyncio.run(sample(key, seconds))
    if not pos:
        raise ValueError(f"aisstream: {n} messages and no positions")
    now = int(time.time())
    static_db.update(static)
    for mmsi in [m for m, s in static_db.items() if s.get("seen", 0) < now - STATIC_DAYS * 86400]:
        del static_db[mmsi]
    vessels = merge((prev or {}).get("vessels"), pos, static_db, now)
    kinds = {}
    for v in vessels.values():
        kinds[v["kind"] or "unknown"] = kinds.get(v["kind"] or "unknown", 0) + 1
    return {"sampled": iso(started), "seconds": seconds, "messages": n, "heard": len(pos),
            "static_heard": len(static), "vessels": vessels, "by_kind": kinds,
            "source": "aisstream.io (terrestrial AIS)"}


# -------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=150)
    ap.add_argument("--no-ais", action="store_true")
    ap.add_argument("--no-portwatch", action="store_true")
    a = ap.parse_args()

    old = load(CACHE) or {}
    out = {"schema": SCHEMA, "portwatch": old.get("portwatch"), "ais": old.get("ais")}
    static_db = load(STATIC) or {}

    if not a.no_portwatch:
        try:
            out["portwatch"] = portwatch()
            pw = out["portwatch"]
            log(f"PortWatch: {len(pw['chokepoints'])} chokepoints, {pw['first']} to {pw['last']}")
        except Exception as e:  # noqa: BLE001
            log(f"PortWatch failed, keeping the last copy: {type(e).__name__}: {e}", "warning")
    if not a.no_ais:
        try:
            out["ais"] = ais(old.get("ais"), static_db, a.seconds)
            s = out["ais"]
            log(f"AIS: {s['messages']} messages, {s['heard']} vessels heard, {len(s['vessels'])} on the map, "
                f"{len(static_db)} known; by kind {s['by_kind']}")
            save(STATIC, static_db)
        except Exception as e:  # noqa: BLE001
            log(f"AIS failed, keeping the last copy: {type(e).__name__}: {e}", "warning")

    if not out["portwatch"] and not out["ais"]:
        log("Ships: no source has ever been fetched", "error")
        return 1
    save(CACHE, out)
    log(f"Wrote {CACHE.relative_to(ROOT)} ({CACHE.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
