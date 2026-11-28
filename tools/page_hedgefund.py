"""Hedge Fund Data (hedge-fund-data/): alternative data, one screen a section.

Owner-approved mocks, 27 and 28 Nov 2026, built as approved. Unlike the rest of the site each section is a
full-screen working screen with its own bar, not a page under the site's header (see DESIGN.md, Hedge Fund
Data). A section is three source files: its markup (tools/hf/<slug>.html), its stylesheet and its script
(assets/hf/<slug>.css and .js). This module writes the page and, beside it, data.json: the figures the
script draws, cut down from .cache/hf/ (tools/*_data.py, .github/workflows/hedgefund-data.yml). A section
whose data has not arrived is a plain page saying so.
"""
import hashlib
import json
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


# slug, the name on the screen, the page's description, what builds its figures, extra stylesheets and scripts
SECTIONS = [
    ("attention", "Attention", "What the world is reading on Wikipedia, day by day: 287 companies, assets and subjects against their own normal.", attention, (), ()),
    ("power", "Power and passengers", "US electricity demand by grid and airport passengers, against the same days a year earlier.", power, (), ()),
]


def pending(site, slug, name, desc):
    body = (f'<main id="main" class="page"><div class="wrap"><header class="page__head"><h1 class="page__title">{name}</h1>'
            f'<p class="lede">{desc}</p></header><div class="dd__plot dd__plot--pending"><p class="dd__pending">Data pending</p></div></div></main>')
    return site.shell(title=f"{name}: Andra Markets", desc=desc, body=body, home="../../", base="../../", path=f"{GROUP}/{slug}/")


def pages(site):
    out = {}
    for slug, name, desc, build, styles, scripts in SECTIONS:
        path = f"{GROUP}/{slug}/"
        data = build(site)
        if not data:
            out[path] = pending(site, slug, name, desc)
            continue
        raw = json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("<", "\\u003c").encode("utf-8")
        folder = site.OUT / GROUP / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "data.json").write_bytes(raw)
        head = f'\n<meta name="hf-data" content="data.json?v={hashlib.sha1(raw).hexdigest()[:10]}">'
        out[path] = site.shell(title=f"{name}: Andra Markets", desc=desc, body=(HERE / "hf" / f"{slug}.html").read_text(encoding="utf-8"),
                               home="../../", base="../../", path=path, nav=False, footer=False, scene=False, head=head,
                               bare=(*styles, f"hf/{slug}.css"), scripts=(*scripts, f"hf/{slug}.js"))
    return out
