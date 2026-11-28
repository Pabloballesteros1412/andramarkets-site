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


# slug, the name on the screen, the page's description, what builds its figures, extra stylesheets and scripts
SECTIONS = [
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
