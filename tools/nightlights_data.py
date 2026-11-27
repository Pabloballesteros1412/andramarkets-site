#!/usr/bin/env python3
"""Fetch the figures behind Hedge Fund Data: From orbit, night lights, once a day.

Run by .github/workflows/hedgefund-data.yml. Writes .cache/hf/nightlights.json
(schema "andra.nightlights/1", Actions cache, never committed or published):

    regions   for each place in REGIONS (factory belts, capitals at war or
              under sanctions, oil fields that flare gas), the month's total
              night-time light seen from orbit: the sum of the radiance of
              every pixel in the box, in nW/cm2/sr, and how many pixels were
              lit, for each month since MONTHS ago. A month in which fewer
              than nine pixels in ten were measured (cloud, or a month not
              yet over) has no figure rather than a low one. A month's total against
              the same month a year earlier is the figure the page shows,
              since light follows the seasons.

Source: NASA Black Marble, VNP46A3 (monthly, the near-nadir snow-free
composite, 15 arc-second pixels, about 500 m), from NASA LAADS, with an
Earthdata Login token. The product's licence has to be accepted once on the
LAADS site by the token's owner; until then every download is refused, and the
run says so. Each run reads at most MAX_TILES new tiles (about 15 to 25 MB
each), newest month first, so the history fills in over the days.

    python3 tools/nightlights_data.py

Environment:
    NASA_EARTHDATA_TOKEN   Earthdata Login token (repository secret).
"""
import datetime as dt
import io
import json
import math
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard_data import UA, log  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "hf" / "nightlights.json"
SCHEMA = "andra.nightlights/2"  # /1 misread the file's encoding: its figures are discarded
LAADS = "https://ladsweb.modaps.eosdis.nasa.gov/api/v2/content/"
PRODUCT = "allData/5200/VNP46A3"
FIELD = "NearNadir_Composite_Snow_Free"
LIT = 1.0        # a pixel brighter than 1 nW/cm2/sr counts as lit
MIN_VALID = 0.9  # share of a box's pixels the month must have measured for its figure to be kept
MONTHS, MAX_TILES = 37, 14
# (key, the page's name, why it matters, west, south, east, north); each box lies inside one 10-degree tile.
REGIONS = [
    ("prd", "Pearl River Delta", "China's export factories", 112.8, 22.2, 114.6, 23.6),
    ("shanghai", "Shanghai", "China's largest port and industry", 120.8, 30.6, 122.0, 31.8),
    ("beijing", "Beijing and Tianjin", "Northern China's industry", 116.0, 38.9, 117.8, 39.95),
    ("pyongyang", "Pyongyang", "North Korea under sanctions", 125.6, 38.9, 125.95, 39.15),
    ("moscow", "Moscow", "Russia's economy at war", 36.8, 55.4, 38.4, 56.1),
    ("kyiv", "Kyiv", "Ukraine's grid under attack", 30.2, 50.2, 30.9, 50.7),
    ("tehran", "Tehran", "Iran under sanctions", 51.1, 35.5, 51.7, 35.85),
    ("gaza", "Gaza", "War and power cuts", 34.2, 31.2, 34.6, 31.6),
    ("dubai", "Dubai", "Gulf trade and finance", 55.1, 24.9, 55.6, 25.4),
    ("mumbai", "Mumbai", "India's commercial capital", 72.75, 18.85, 73.1, 19.3),
    ("lagos", "Lagos", "Africa's largest city", 3.1, 6.4, 3.6, 6.7),
    ("permian", "Permian Basin", "US shale oil, lit by its gas flares", -104.0, 31.0, -101.0, 33.0),
    ("nyc", "New York", "A reference: a rich city at steady light", -74.3, 40.5, -73.7, 41.0),
]
PX = 2400  # pixels per 10-degree tile side


def tile_of(w, s, e, n):
    h, v = int((w + 180) // 10), int((90 - n) // 10)
    if int((e + 180) // 10) != h or int((90 - s) // 10) != v:
        raise ValueError(f"box {w},{s},{e},{n} crosses a tile edge")
    return h, v


class Laads:
    def __init__(self, token):
        self.h = {"User-Agent": UA, "Authorization": f"Bearer {token}"}

    def json(self, path):
        req = urllib.request.Request(LAADS + "details/" + path, headers=self.h)
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())

    def file(self, url):
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None
        opener = urllib.request.build_opener(NoRedirect)
        try:
            with opener.open(urllib.request.Request(url, headers=self.h), timeout=300) as r:
                return r.read(200 * 1024 * 1024)
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307):
                where = e.headers.get("Location", "")
                if "licenses" in where or "login" in where:
                    raise PermissionError("LAADS asks for the Black Marble licence to be accepted, or a login") from None
            raise


def months(laads):
    """(month 'YYYY-MM', year, day-of-year directory) for the months LAADS has, newest first."""
    out = []
    this = dt.date.today().year
    for y in (this, this - 1, this - 2, this - 3):
        try:
            for d in laads.json(f"{PRODUCT}/{y}?pageSize=400").get("content", []):
                doy = d.get("name", "")
                if doy.isdigit():
                    m = dt.date(y, 1, 1) + dt.timedelta(days=int(doy) - 1)
                    out.append((m.strftime("%Y-%m"), y, doy))
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
    return sorted(out, reverse=True)[:MONTHS]


def measure(raw, boxes):
    import h5py  # installed by the workflow; only this source needs it
    import numpy as np
    with h5py.File(io.BytesIO(raw), "r") as f:
        found = []
        f.visititems(lambda n, o: found.append(n) if n.endswith(FIELD) else None)
        if not found:
            raise ValueError(f"no {FIELD} in the tile")
        ds = f[found[0]]
        # The field is float32 radiance with its own fill value (-999.9) and scale (1.0): read them from the file.
        fill = float(ds.attrs["_FillValue"][0])
        scale = float(ds.attrs["scale_factor"][0]) if "scale_factor" in ds.attrs else 1.0
        offset = float(ds.attrs["offset"][0]) if "offset" in ds.attrs else 0.0
        data = ds[()]
    out = {}
    for key, (h, v, w, s, e, n) in boxes.items():
        top, left = 90 - v * 10, -180 + h * 10
        r0, r1 = int(math.floor((top - n) * PX / 10)), int(math.ceil((top - s) * PX / 10))
        c0, c1 = int(math.floor((w - left) * PX / 10)), int(math.ceil((e - left) * PX / 10))
        box = data[r0:r1, c0:c1].astype("float64")
        good = ~np.isclose(box, fill) & (box * scale + offset >= 0)
        rad = np.where(good, box * scale + offset, 0.0)
        valid = int(good.sum())
        # A month with too few clear, moonless nights leaves holes: its sum would read as a fall in light.
        # "mean" (radiance per measured pixel) is the figure to compare between months: the pixels measured differ a little.
        out[key] = ({"sum": round(float(rad.sum())), "mean": round(float(rad.sum()) / valid, 3), "lit": int((rad > LIT).sum()),
                     "valid": valid, "pixels": int(box.size)}
                    if valid >= MIN_VALID * box.size else {"sum": None, "mean": None, "lit": None, "valid": valid, "pixels": int(box.size)})
    return out


def main():
    token = (os.environ.get("NASA_EARTHDATA_TOKEN") or "").strip()
    try:
        old = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = {}
    if not token:
        log("Night lights: NASA_EARTHDATA_TOKEN is not set", "warning")
        return 0
    laads = Laads(token)
    data = (old.get("data") or {}) if old.get("schema") == SCHEMA else {}  # month -> region key -> figures
    tiles = {}
    for key, name, why, w, s, e, n in REGIONS:
        h, v = tile_of(w, s, e, n)
        tiles.setdefault((h, v), {})[key] = (h, v, w, s, e, n)
    try:
        avail = months(laads)
    except Exception as e:  # noqa: BLE001
        log(f"Night lights: LAADS listing failed: {type(e).__name__}: {e}", "warning")
        return 0
    read = 0
    for month, year, doy in avail:
        todo = [t for t, boxes in tiles.items() if any(k not in data.get(month, {}) for k in boxes)]
        if not todo:
            continue
        try:
            listing = laads.json(f"{PRODUCT}/{year}/{doy}?pageSize=1000").get("content", [])
        except Exception as e:  # noqa: BLE001
            log(f"Night lights {month}: listing failed: {type(e).__name__}: {e}", "warning")
            continue
        for h, v in todo:
            if read >= MAX_TILES:
                break
            tag = f".h{h:02d}v{v:02d}."
            f = next((x for x in listing if tag in x.get("name", "")), None)
            if not f:
                data.setdefault(month, {}).update({k: None for k in tiles[(h, v)]})  # no tile that month
                continue
            try:
                raw = laads.file(f["downloadsLink"])
                data.setdefault(month, {}).update(measure(raw, tiles[(h, v)]))
                read += 1
            except PermissionError as e:
                log(f"Night lights: {e}. Open a VNP46A3 file on ladsweb.modaps.eosdis.nasa.gov while logged in and accept it.", "warning")
                return 0
            except Exception as e:  # noqa: BLE001
                log(f"Night lights {month} h{h:02d}v{v:02d}: {type(e).__name__}: {e}", "warning")
        if read >= MAX_TILES:
            break
    keep = {m for m, _, _ in avail}
    data = {m: v for m, v in sorted(data.items()) if m in keep}
    out = {"schema": SCHEMA, "fetched": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "unit": "nW/cm2/sr: sum over the box, and mean per measured pixel", "regions": [{"key": k, "name": n, "why": y, "bbox": [w, s, e, nn]}
                                                            for k, n, y, w, s, e, nn in REGIONS],
           "data": data, "source": "NASA Black Marble VNP46A3 (LAADS DAAC)"}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    done = sum(1 for m in data.values() for x in m.values() if x and x.get("sum") is not None)
    log(f"Night lights: read {read} tiles; {len(data)} months held, {done} region-months measured")
    return 0


if __name__ == "__main__":
    sys.exit(main())
