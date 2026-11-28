#!/usr/bin/env python3
"""Fetch the figures behind Hedge Fund Data: Attention.

Run by .github/workflows/hedgefund-data.yml: Wikipedia once a day, GDELT a
few subjects every run. Writes .cache/hf/attention.json (schema "andra.attention/1",
Actions cache, never committed or published):

    wikipedia  daily views of the English Wikipedia article on each of the
               companies and market subjects in WIKI, for 400 days (Wikimedia
               pageviews API, people only, no bots; no key). A day's views
               against the article's own 90-day average is the attention
               spike the page shows.
    news       for each subject in NEWS, the share of all the world's online
               news coverage in English that mentions it, and that coverage's
               average tone, each day for three months (GDELT DOC 2.0, no key).
               GDELT limits cloud addresses hard, so each run renews only the
               three subjects fetched longest ago, twelve seconds apart.

A failed source keeps its last good copy with its own date.

    python3 tools/attention_data.py [--force]
"""
import argparse
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard_data import get, log  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "hf" / "attention.json"
SCHEMA = "andra.attention/1"
# Wikimedia asks automated clients to name themselves and a way to reach them.
WIKI_UA = {"User-Agent": "AndraMarketsSite/1.0 (https://github.com/Pabloballesteros1412/andramarkets-site)"}
WIKI = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{}/daily/{}/{}"
WIKI_DAYS = 400
# (key, the page's name, Wikipedia article, group)
WIKI_ARTICLES = [
    ("NVDA", "Nvidia", "Nvidia", "Companies"), ("AAPL", "Apple", "Apple_Inc.", "Companies"),
    ("MSFT", "Microsoft", "Microsoft", "Companies"), ("AMZN", "Amazon", "Amazon_(company)", "Companies"),
    ("GOOGL", "Alphabet", "Google", "Companies"), ("META", "Meta", "Meta_Platforms", "Companies"),
    ("TSLA", "Tesla", "Tesla,_Inc.", "Companies"), ("AVGO", "Broadcom", "Broadcom", "Companies"),
    ("PLTR", "Palantir", "Palantir_Technologies", "Companies"), ("AMD", "AMD", "AMD", "Companies"),
    ("INTC", "Intel", "Intel", "Companies"), ("TSM", "TSMC", "TSMC", "Companies"),
    ("NFLX", "Netflix", "Netflix", "Companies"), ("BRK", "Berkshire Hathaway", "Berkshire_Hathaway", "Companies"),
    ("JPM", "JPMorgan Chase", "JPMorgan_Chase", "Companies"), ("LLY", "Eli Lilly", "Eli_Lilly_and_Company", "Companies"),
    ("NVO", "Novo Nordisk", "Novo_Nordisk", "Companies"), ("ASML", "ASML", "ASML_Holding", "Companies"),
    ("COIN", "Coinbase", "Coinbase", "Companies"), ("MSTR", "Strategy", "Strategy_Inc.", "Companies"),
    ("OPENAI", "OpenAI", "OpenAI", "Private"), ("ANTH", "Anthropic", "Anthropic", "Private"),
    ("SPACEX", "SpaceX", "SpaceX", "Private"),
    ("BTC", "Bitcoin", "Bitcoin", "Assets"), ("GOLD", "Gold", "Gold_as_an_investment", "Assets"),
    ("OIL", "Oil price", "Price_of_oil", "Assets"), ("SPX", "S&P 500", "S%26P_500", "Assets"),
    ("REC", "Recession", "Recession", "Macro"), ("INFL", "Inflation", "Inflation", "Macro"),
    ("TARIFF", "Tariff", "Tariff", "Macro"), ("FED", "Federal Reserve", "Federal_Reserve", "Macro"),
    ("BUBBLE", "Stock market bubble", "Stock_market_bubble", "Macro"), ("CRASH", "Stock market crash", "Stock_market_crash", "Macro"),
    ("LAYOFF", "Layoff", "Layoff", "Macro"), ("STAG", "Stagflation", "Stagflation", "Macro"),
]
GDELT = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_GAP = 12.0  # seconds between requests: GDELT asks for at least five, and is stricter with cloud addresses
GDELT_PER_RUN = 3  # subjects asked for in one run, the stalest first; over a day's runs every subject is renewed
# (key, the page's name, GDELT query)
NEWS = [
    ("recession", "Recession", '(recession OR "economic downturn")'),
    ("inflation", "Inflation", "inflation"),
    ("tariffs", "Tariffs", "(tariff OR tariffs)"),
    ("fed", "The Fed", '("Federal Reserve" OR "the Fed")'),
    ("layoffs", "Layoffs", "(layoffs OR \"job cuts\")"),
    ("ai_bubble", "AI bubble", '"AI bubble"'),
    ("oil", "Oil supply", '("oil supply" OR "oil prices")'),
    ("hormuz", "Strait of Hormuz", '"Strait of Hormuz"'),
    ("taiwan", "Taiwan Strait", '("Taiwan Strait" OR "blockade of Taiwan")'),
    ("shipping", "Shipping disruption", '("shipping disruption" OR "supply chain disruption")'),
    ("default", "Default and debt", '("debt ceiling" OR "sovereign default" OR "bond market")'),
    ("bank", "Bank stress", '("bank run" OR "bank failure" OR "banking crisis")'),
]


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def canonical(titles):
    """Each title as Wikipedia files its article today. A page that has been moved leaves a redirect,
    and the pageviews API counts the redirect's own few views, not the article's: Strategy Inc. read
    7 times a day under its old title. Titles that cannot be resolved are kept as they are."""
    out = {t: t for t in titles}
    try:
        q = urllib.parse.urlencode({"action": "query", "format": "json", "redirects": 1, "titles": "|".join(urllib.parse.unquote(t) for t in titles)})
        d = json.loads(get("https://en.wikipedia.org/w/api.php?" + q, headers=WIKI_UA))["query"]
        step = {x["from"].replace(" ", "_"): x["to"].replace(" ", "_") for x in d.get("normalized", []) + d.get("redirects", [])}
        for t in titles:
            cur = urllib.parse.unquote(t)
            for _ in range(3):  # normalised, then redirected
                if cur not in step:
                    break
                cur = step[cur]
            if cur != urllib.parse.unquote(t):
                out[t] = urllib.parse.quote(cur, safe="_(),.")
                log(f"Wikipedia: {t} is now {cur}")
    except Exception as e:  # noqa: BLE001
        log(f"Wikipedia: titles not resolved, using them as written: {type(e).__name__}: {e}", "warning")
    return out


def wikipedia(old):
    titles = canonical([a[2] for a in WIKI_ARTICLES])
    end = now_utc().date() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=WIKI_DAYS)
    out = []
    for key, name, art, group in WIKI_ARTICLES:
        art = titles[art]
        url = WIKI.format(art, start.strftime("%Y%m%d00"), end.strftime("%Y%m%d00"))
        for i in range(4):
            try:
                items = json.loads(get(url, headers=WIKI_UA)).get("items", [])
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    items = []
                    break
                if e.code != 429 or i == 3:
                    raise
                time.sleep(5 * (i + 1))
        if not items:
            log(f"Wikipedia: no views for {art}", "warning")
            continue
        first = dt.datetime.strptime(items[0]["timestamp"][:8], "%Y%m%d").date()
        views = {it["timestamp"][:8]: it["views"] for it in items}
        n = (end - first).days + 1
        series = [views.get((first + dt.timedelta(days=i)).strftime("%Y%m%d")) for i in range(n)]
        out.append({"key": key, "name": name, "article": art, "group": group, "first": first.isoformat(), "views": series})
        time.sleep(0.15)
    if not out:
        raise ValueError("Wikipedia returned no views")
    return {"fetched": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"), "last": end.isoformat(), "articles": out,
            "source": "Wikimedia pageviews (English Wikipedia, users only)"}


def gdelt(mode, query):
    q = urllib.parse.urlencode({"query": f"{query} sourcelang:english", "mode": mode, "format": "json", "timespan": "3months"})
    try:
        return json.loads(get(f"{GDELT}?{q}"))
    finally:
        time.sleep(GDELT_GAP)


def news(old):
    """Renews the GDELT_PER_RUN subjects fetched longest ago; the others keep their last copy."""
    kept = {s["key"]: s for s in (old or {}).get("subjects", [])}
    order = sorted(NEWS, key=lambda n: (kept.get(n[0]) or {}).get("fetched", ""))
    renewed = 0
    for key, name, query in order[:GDELT_PER_RUN]:
        try:
            vol = gdelt("timelinevol", query)
            tone = gdelt("timelinetone", query)
        except Exception as e:  # noqa: BLE001
            log(f"GDELT {name}: {type(e).__name__}: {e}", "warning")
            continue
        v = {d["date"][:8]: d["value"] for d in (vol.get("timeline") or [{}])[0].get("data", [])}
        t = {d["date"][:8]: d["value"] for d in (tone.get("timeline") or [{}])[0].get("data", [])}
        days = sorted(v)
        if not days:
            continue
        kept[key] = {"key": key, "name": name, "query": query, "fetched": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "first": f"{days[0][:4]}-{days[0][4:6]}-{days[0][6:]}",
                     # share of all monitored English coverage, in percent; tone runs about -10 (negative) to +10
                     "share": [round(v[d], 4) for d in days], "tone": [None if d not in t else round(t[d], 2) for d in days]}
        renewed += 1
    if not kept:
        raise ValueError("GDELT returned nothing")
    log(f"GDELT: renewed {renewed} of {GDELT_PER_RUN} subjects; {len(kept)} of {len(NEWS)} held")
    return {"fetched": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"), "subjects": [kept[k] for k, _, _ in NEWS if k in kept],
            "source": "The GDELT Project, DOC 2.0 (English-language online news)"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    try:
        old = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = {}
    today = now_utc().date().isoformat()
    out = {"schema": SCHEMA, "wikipedia": old.get("wikipedia"), "news": old.get("news")}
    did = False
    for part, fn in (("wikipedia", lambda: wikipedia(old.get("wikipedia"))), ("news", lambda: news(old.get("news")))):
        if part == "wikipedia" and not a.force and (out[part] or {}).get("fetched", "")[:10] == today:
            continue
        try:
            out[part] = fn()
            did = True
            log(f"Attention, {part}: {len(out[part].get('articles') or out[part].get('subjects'))} series")
        except Exception as e:  # noqa: BLE001
            log(f"Attention, {part} failed, keeping the last copy: {type(e).__name__}: {e}", "warning")
    if not did:
        log("Attention: already fetched today")
        return 0
    if not out["wikipedia"] and not out["news"]:
        return 1
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    log(f"Wrote {CACHE.relative_to(ROOT)} ({CACHE.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
