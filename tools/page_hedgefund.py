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


def med(a):
    a = sorted(a)
    return a[len(a) // 2] if a else 0


def tile_ships(d):
    cp = d["PW"]["cp"]
    tot = [sum(c["t"][i] or 0 for c in cp) for i in range(len(cp[0]["t"]))]
    return f'{len(d["AIS"]["v"]):,}', "vessels at sea", "line", tot[-60:], "Transits a day through 28 chokepoints, 60 days"


def tile_orbit(d):
    return (f'{d["t"]["total"]:,}', "heat detections, 24 h", "bars",
            sorted((v["count"] for v in d["t"]["latest"].values()), reverse=True)[:14], "Detections by region, 24 hours")


def tile_jets(d):
    return f'{len(d["jets"]):,}', "business jets tracked", "bars", sorted(d["by_region"].values(), reverse=True), "Aircraft by region, now"


def tile_attention(d):
    def x(a):
        v = [n or 0 for n in a["v"]]
        return v[-1] / (med(v[-91:-1]) or 1)
    top = max(d["arts"], key=x)
    return f"{x(top):.0f}\u00d7", f'{top["n"]}, against normal', "line", [n for n in top["v"] if n is not None][-60:], f'{top["n"]}: readers a day, 60 days'


def tile_predictions(d):
    ev = max(d["ev"], key=lambda e: e["v24"])
    out = sorted(ev["o"], key=lambda o: -o[1])
    return f"{out[0][1] * 100:.0f}%", out[0][0], "bars", [round(o[1] * 100, 1) for o in out], ev["t"]


def tile_positioning(d):
    c = min(d["cot"], key=lambda c: min(c["p"], 100 - c["p"]))
    p = round(c["p"])
    th = "th" if 10 <= p % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(p % 10, "th")
    return f"{p}{th}", f'percentile, {c["n"]}', "line", [w[4] for w in c["w"][-52:]], f'{c["n"]}: speculators\' net position, 52 weeks'


def tile_insiders(d):
    flow = {}
    for t in sorted(d["trades"], key=lambda t: t["d"]):
        flow[t["d"]] = flow.get(t["d"], 0) + (t["v"] if t["k"] == "P" else -t["v"])
    net = sum(flow.values())
    return f"${abs(net) / 1e9:.1f}bn", ("bought" if net > 0 else "sold") + " net, 45 days", "pm", list(flow.values())[-30:], "Insiders' net flow a day, 30 days"


def tile_power(d):
    return f'{d["hourly"][-1][1] / 1e3:.1f} GW', "lower 48, now", "line", [x for x in d["grids"][0]["mwh"] if x is not None][-60:], "Lower 48 demand a day, 60 days"


# The eight sections in the order of the group's page (Ships first, owner), with the name on its tile.
LANDING = (("ships", "Ships", ships, tile_ships), ("orbit", "From orbit", orbit, tile_orbit), ("jets", "Jets", jets, tile_jets),
           ("attention", "Attention", attention, tile_attention), ("predictions", "Predictions", predictions, tile_predictions),
           ("positioning", "Positioning", positioning, tile_positioning), ("insiders", "Insiders", insiders, tile_insiders),
           ("power", "Power", power, tile_power))


def index(site):
    """The group's page (owner-approved mock, 28 Nov 2026): a map of the world, six agents travelling over it, the light
    falling from them and the eight sections on a line, drawn by assets/hf/landing.js over landing-world.js. The sections and their figures are in the
    page as links, so it reads without the script; a section whose data has not arrived says so."""
    full = {slug: n for slug, n, *_ in SECTIONS}
    tiles, series = "", []
    for slug, name, build, tile in LANDING:
        data = build(site)
        try:
            fig, sub, kind, vals, cap = tile(data) if data else ("", "Data pending", "", [], "")
        except (KeyError, IndexError, ValueError, TypeError, ZeroDivisionError):
            fig, sub, kind, vals, cap = "", "Data pending", "", [], ""
        series.append([kind, vals])
        tiles += (f'<a class="ls__t" href="{slug}/" title="{html.escape(cap, quote=True)}" aria-label="{html.escape(full[slug], quote=True)}">'
                  f'<small>{name}</small><b>{html.escape(fig) or "&nbsp;"}</b><span>{html.escape(sub)}</span></a>')
    payload = json.dumps(series, separators=(",", ":")).replace("<", "\\u003c")
    body = f"""<main id="main" class="ls">
  <canvas id="cv" aria-hidden="true"></canvas>
  <header class="ls__head"><h1>Hedge Fund Data</h1><p>{LEDE}</p></header>
  <div id="srcs" aria-hidden="true"></div>
  <nav class="ls__row" id="row" aria-label="Hedge Fund Data">{tiles}</nav>
  <script type="application/json" id="hf-landing">{payload}</script>
</main>"""
    return site.shell(title="Hedge Fund Data: Andra Markets", desc=LEDE, body=body, home="../", base="../", path=f"{GROUP}/", footer=False,
                      head=f'\n<link rel="stylesheet" href="../assets/hf/landing.css?v={site.ver("hf/landing.css")}">', scripts=("hf/landing-world.js", "hf/landing.js"))


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
