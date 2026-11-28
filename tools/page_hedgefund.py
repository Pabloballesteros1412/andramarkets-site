"""Hedge Fund Data (hedge-fund-data/): alternative data, one screen a section.

Owner-approved mocks, 27 and 28 Nov 2026, built as approved. Unlike the rest of the site each section is a
full-screen working screen with its own bar, not a page under the site's header (see DESIGN.md, Hedge Fund
Data). A section is three source files: its markup (tools/hf/<slug>.html), its stylesheet and its script
(assets/hf/<slug>.css and .js). This module writes the page and, beside it, data.js: the figures the
script draws, cut down from .cache/hf/ (tools/*_data.py, .github/workflows/hedgefund-data.yml). A section
whose data has not arrived is a plain page saying so.
"""
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
GROUP = "hedge-fund-data"


def cache(site, name):
    try:
        return json.loads((site.ROOT / ".cache" / "hf" / name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def power(site):
    d = cache(site, "power.json") or {}
    p, t = d.get("power") or {}, d.get("passengers") or {}
    if not p.get("grids") or len(p.get("hourly_us48_utc") or []) < 200 or len(t.get("days") or {}) < 400:
        return None  # the screen compares with a year earlier: it needs the grids, the hours and a year of airports
    return {"grids": p["grids"], "hourly": p["hourly_us48_utc"], "pfetched": p["fetched"], "pax": t["days"]}


def attention(site):
    w = (cache(site, "attention.json") or {}).get("wikipedia") or {}
    arts = [{"k": a["key"], "n": a["name"], "a": a["article"], "g": a["group"], "f": a["first"], "v": a["views"]}
            for a in w.get("articles") or []]
    return {"fetched": w["fetched"], "last": w["last"], "arts": arts} if len(arts) >= 30 else None


def predictions(site):
    d = cache(site, "predictions.json") or {}
    ev = [{"v": e["venue"], "id": e["id"], "t": e["title"], "u": e["url"], "g": e["tags"], "end": e["end"], "v24": e["vol24h"], "vol": e["vol"],
           "o": [[o["label"], o["prob"], o["prev"], o["vol24h"], o["vol"]] for o in e["outcomes"]]}
          for v in (d.get("venues") or {}).values() for e in v.get("events") or []]
    # Candidates are named as the venues name them: the owner's exception to the no-names rule, for this screen only.
    return {"fetched": {k: v["fetched"] for k, v in d["venues"].items()}, "ev": ev} if len(ev) >= 20 else None


def positioning(site):
    d = cache(site, "positioning.json") or {}
    cot, sh = d.get("cot") or {}, d.get("short") or {}
    if not cot.get("contracts") or not sh.get("market"):
        return None
    dates = [m[0] for m in sh["market"]]
    shares = {}
    for k, v in sh["shares"].items():
        by = {x[0]: x[1] for x in v["series"]}
        shares[k] = {"r": [by.get(x) for x in dates], "v": v["series"][-1][2], "a": v["avg"]}
    return {"asof": cot["as_of"], "dates": dates, "mkt": [m[1] for m in sh["market"]], "sh": shares,
            "cot": [{"n": c["name"], "g": c["group"], "p": c["percentile_3y"], "w": [x[:6] for x in c["weeks"]]} for c in cot["contracts"]]}


SMALL = {"INC", "CORP", "LTD", "CO", "THE", "AND", "OF", "PLC", "LLC", "LP"}


def title_case(s):
    """SEC and USAspending shout their names: ACME HOLDINGS INC reads better as Acme Holdings Inc; short tickers stay."""
    s = (s or "").strip()
    if not s.isupper():
        return s
    return " ".join(w if (len(w) <= 4 and w not in SMALL) else w.capitalize() for w in s.split())


AGENCY = (("Department of ", ""), ("National Aeronautics and Space Administration", "NASA"), ("General Services Administration", "GSA"))


def insiders(site):
    ins, con = cache(site, "insiders.json") or {}, cache(site, "contracts.json") or {}
    trades = [{"t": t["ticker"], "c": title_case(t["company"]), "d": t["date"], "k": t["code"], "sh": t["shares"], "px": t["price"], "v": t["value"],
               "roles": t.get("roles") or [t["role"]], "o": sorted(t.get("owners") or [])}
              for t in ins.get("trades") or []
              # a filing now and then carries a mistyped date in the future: it cannot have happened yet
              if t.get("value") and t.get("ticker") and t["date"] <= (ins.get("fetched") or "9")[:10]]
    acts = []
    for a in con.get("actions") or []:
        if not a.get("date"):
            continue
        ag = a["agency"]
        for old, new in AGENCY:
            ag = ag.replace(old, new)
        acts.append({"d": a["date"], "v": a["amount"], "r": title_case(a["recipient"]), "t": a["ticker"], "c": a["company"], "a": ag, "w": title_case(a["what"])[:150]})
    return {"fetched": ins["fetched"], "trades": trades, "acts": acts} if len(trades) >= 20 else None


KINDS = ["tanker", "cargo", "passenger", "fishing", "tug", "other", "unknown"]  # the order assets/hf/ships.js draws them in
NEAR_DEG = 1.5  # a chokepoint has live positions if a vessel was heard within this many degrees of it


def ships(site):
    d = cache(site, "ships.json") or {}
    pw, ais = d.get("portwatch") or {}, d.get("ais") or {}
    if not pw.get("chokepoints") or len(ais.get("vessels") or {}) < 500:
        return None
    static = cache(site, "ships_static.json") or {}
    static = static.get("vessels", static)
    when = dt.datetime.strptime(ais["sampled"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp()
    v = []
    for mmsi, x in ais["vessels"].items():
        tr = x["trail"]
        lon, lat, t = tr[-1]
        st = static.get(mmsi) or {}
        v.append([lon, lat, x["cog"] if x["cog"] is not None else x["hdg"], x["sog"], KINDS.index(x["kind"] or "unknown") if (x["kind"] or "unknown") in KINDS else 5,
                  st.get("name") or None, st.get("dest") or None, st.get("len") or None, round(max(0, when - t) / 60, 1),
                  [c for q in tr[:-1] for c in q[:2]]])
    cps = []
    for c in pw["chokepoints"]:
        live = sum(1 for r in v if abs(r[0] - c["lon"]) <= NEAR_DEG and abs(r[1] - c["lat"]) <= NEAR_DEG)
        cps.append({"name": c["name"], "lat": c["lat"], "lon": c["lon"], "t": c["total"], "tk": c["tanker"], "ct": c["container"], "db": c["dry_bulk"], "gc": c["other"], "live": live})
    return {"PW": {"dates": [pw["first"], pw["last"]], "n": len(pw["chokepoints"][0]["total"]), "cp": cps}, "AIS": {"sampled": ais["sampled"], "v": v}}


def jets(site):
    d = cache(site, "jets.json") or {}
    la, hi = d.get("latest") or {}, d.get("history") or {}
    if len(la.get("jets") or []) < 20:
        return None
    return {"time": la["time"], "aircraft": la["aircraft"], "airborne": la["airborne"], "by_region": la["by_region"], "jets": la["jets"],
            "hubs": d["hubs"], "hubnow": la["hubs"], "daily": hi.get("daily") or {}, "samples": [x[:5] for x in hi.get("samples") or []]}


def orbit(site):
    t = (cache(site, "orbit.json") or {}).get("thermal") or {}
    if len(t.get("points") or []) < 100:
        return None
    n = cache(site, "nightlights.json") or {}
    # a month no region was measured in (the month still running) tells the page nothing
    months = {m: v for m, v in (n.get("data") or {}).items() if any(x and x.get("sum") is not None for x in v.values())}
    return {"t": {"fetched": t["fetched"], "total": t["total"], "points": [[p[0], p[1], p[2], p[4], p[5]] for p in t["points"]], "regions": t["regions"], "latest": t["latest"]},
            "n": {"regions": n.get("regions") or [], "data": months}}


# The basemap of the three map screens. With ARCGIS_API_KEY (a key the owner makes at developers.arcgis.com, kept as
# a repository secret and scoped there to this site's address: it is public in the page by nature), Esri's World
# Imagery and its places, as in the approved mocks. Without it, NASA's Blue Marble, which needs no key and no licence.
def tiles():
    key = (os.environ.get("ARCGIS_API_KEY") or "").strip()
    if key:
        base = "https://ibasemaps-api.arcgis.com/arcgis/rest/services/"
        return {"sat": f"{base}World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}?token={key}", "z": 18, "att": "Imagery Esri, Maxar, Earthstar Geographics",
                "ref": f"{base}Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}?token={key}"}
    return {"sat": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/2004-08-01/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg",
            "z": 8, "att": "NASA Blue Marble (GIBS)", "ref": None}


MAP = (("hf/vendor/maplibre-gl.css",), ("hf/vendor/maplibre-gl.js",))

# slug, the name on the screen, the page's description, what builds its figures, extra stylesheets and scripts
SECTIONS = [
    ("ships", "Ships", "Vessels at sea from live AIS, and how many cross each of the world's 28 chokepoints a day.", ships, *MAP),
    ("jets", "Corporate jets", "Business jets in the air now, by maker, and the airfields they use.", jets, *MAP),
    ("orbit", "From orbit", "Fires, gas flares and industrial heat seen by satellite in the last 24 hours, and the night lights of thirteen places.", orbit, *MAP),
    ("attention", "Attention", "What the world is reading on Wikipedia, day by day: 287 companies, assets and subjects against their own normal.", attention, (), ()),
    ("predictions", "Prediction markets", "What Polymarket and Kalshi price for the Fed, inflation, recession, elections and the markets, by money traded.", predictions, (), ()),
    ("positioning", "Positioning", "How speculators are placed in 27 futures markets, and how much of each US share's volume is sold short.", positioning, (), ()),
    ("insiders", "Insiders and contracts", "Open-market purchases and sales by company insiders, and the federal contracts listed companies win.", insiders, (), ()),
    ("power", "Power and passengers", "US electricity demand by grid and airport passengers, against the same days a year earlier.", power, (), ()),
]


def pending(site, slug, name, desc):
    body = (f'<main id="main" class="page"><div class="wrap"><header class="page__head"><h1 class="page__title">{name}</h1>'
            f'<p class="lede">{desc}</p></header><div class="dd__plot dd__plot--pending"><p class="dd__pending">Data pending</p></div></div></main>')
    return site.shell(title=f"{name}: Andra Markets", desc=desc, body=body, home="../../", base="../../", path=f"{GROUP}/{slug}/")


LEDE = "What ships, jets, satellites, filings, bets and readers show, before it reaches the prices."


# What each screen holds, for the group's map: (name, ...) under each section.
PARTS = {
    "ships": ("Live map", "Chokepoints", "Tankers", "Vessels in view"),
    "jets": ("In the air now", "By maker", "Airfields"),
    "orbit": ("Heat detections", "Oil and gas flares", "Night lights"),
    "attention": ("The wall", "By group", "Largest spikes"),
    "predictions": ("The Fed", "Economy", "Elections", "Largest moves"),
    "positioning": ("Futures", "Short selling", "Crowding"),
    "insiders": ("Insiders", "Cluster buys", "Government contracts"),
    "power": ("Every grid", "The year", "Hour by hour", "Air passengers"),
}
MAP_ORDER = ("ships", "orbit", "jets", "attention", "predictions", "positioning", "insiders", "power")  # Ships first (owner)


def index(site):
    """The group's own page, as Markets, Research and Careers have theirs: every section and its parts on one map of
    light, drawn by the Tools map's script (assets/tools-map.js) in the group's own colour. Without the script it is a list."""
    name = {slug: n for slug, n, *_ in SECTIONS}
    groups = "".join(
        f'<li data-key="{k}"><a class="tools-map__name" href="{k}/">{name[k]}</a><ol>'
        + "".join(f'<li><a href="{k}/">{part}</a></li>' for part in PARTS[k]) + "</ol></li>" for k in MAP_ORDER)
    body = f"""<main id="main" class="page">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Hedge Fund Data</h1>
      <p class="lede">{LEDE}<span class="tool-map__hint"> Drag a section where you like.</span><span class="tools-map__touch"> Spread two fingers to enlarge the map.</span></p>
    </header>
    <nav class="tools-map tools-map--teal" data-page="hedge-fund-data" data-tint='["170,245,238","90,225,216","30,190,186"]' aria-label="Hedge Fund Data"><ol>{groups}</ol></nav>
  </div>
</main>"""
    return site.shell(title="Hedge Fund Data: Andra Markets", desc=LEDE, body=body, home="../", base="../", path=f"{GROUP}/", scripts=("tools-map.js",))


def pages(site):
    out = {f"{GROUP}/": index(site)}
    for slug, name, desc, build, styles, scripts in SECTIONS:
        path = f"{GROUP}/{slug}/"
        data = build(site)
        if not data:
            out[path] = pending(site, slug, name, desc)
            continue
        # The figures go out as a script beside the page, not a .json: the site publishes no data files
        # (pages.yml checks), and a script from the site's own address is what its policy already allows.
        raw = ("window.HFDATA=" + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";\n").encode("utf-8")
        folder = site.OUT / GROUP / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "data.js").write_bytes(raw)
        (folder / "data.json").unlink(missing_ok=True)
        head = f'\n<script src="data.js?v={hashlib.sha1(raw).hexdigest()[:10]}" defer></script>'
        if styles:  # a map screen: name its basemap (csp_policy() in build_site.py opens the policy to it)
            head += f'\n<meta name="hf-tiles" content="{html.escape(json.dumps(tiles(), separators=(",", ":")), quote=True)}">'
        out[path] = site.shell(title=f"{name}: Andra Markets", desc=desc, body=(HERE / "hf" / f"{slug}.html").read_text(encoding="utf-8"),
                               home="../../", base="../../", path=path, nav=False, footer=False, scene=False, head=head,
                               bare=(*styles, f"hf/{slug}.css"), scripts=(*scripts, f"hf/{slug}.js"))
    return out
