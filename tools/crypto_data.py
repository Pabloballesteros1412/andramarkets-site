#!/usr/bin/env python3
"""Fetch the figures behind Crypto (crypto/), at deploy time.

Run by .github/workflows/pages.yml before tools/build_site.py. Writes one file,
.cache/crypto/crypto.json: the largest coins by market value (price, value, the
change over a day and over a week), the whole market's value with Bitcoin's
share of it, and where the day's trading is registered: the 500 exchanges
CoinGecko lists, their 24-hour volume added up by the country each declares as
its seat. tools/page_crypto.py reads it; nothing here is published as a file.

Source: CoinGecko's public API, no key (https://www.coingecko.com/en/api). Its
terms ask for attribution, which the page gives beside every figure's date.
Tokens that are another coin under a wrapper (wrapped, staked or bridged) are
left out, so no coin is counted twice. A failed fetch keeps the last good copy
(restored by the workflow's cache) with its own date, and never stops the deploy;
the coins and the exchanges are fetched apart, so one can fail and the other stay new.
A country with no place in SEATS below is counted with the volume that names no
country, and the run says so, so the table can be extended.

    python3 tools/crypto_data.py
"""
import datetime as dt
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "crypto" / "crypto.json"
API = "https://api.coingecko.com/api/v3/"
KEEP = 100
# Another coin under a wrapper: by name, or by a symbol the name does not give away.
WRAPPED = re.compile(r"wrapped|staked|staking|bridged|restaked|binance-peg", re.I)
WRAPPED_SYMBOLS = {"wbtc", "weth", "steth", "wsteth", "weeth", "cbbtc", "reth", "wbeth", "lbtc", "jitosol", "msol", "bnsol", "rseth", "solvbtc"}
# Pegged to a currency: shown, and marked, since their value says nothing of their price.
STABLE = {"usdt", "usdc", "dai", "usds", "usde", "fdusd", "pyusd", "usd1", "tusd", "usdd", "frax", "susds", "susde", "usdf", "bfusd", "rlusd", "usdg", "usdtb", "buidl"}


# Where each declared seat is drawn on the globe: the capital or the financial centre, (lat, lon).
SEATS = {
    "Australia": (-33.87, 151.21), "Austria": (48.21, 16.37), "Bahamas": (25.05, -77.35), "Brazil": (-23.55, -46.63),
    "British Virgin Islands": (18.43, -64.62), "Canada": (43.65, -79.38), "Cayman Islands": (19.29, -81.37), "Chad": (12.13, 15.06),
    "Chile": (-33.45, -70.67), "China": (31.23, 121.47), "Costa Rica": (9.93, -84.08), "Cyprus": (35.17, 33.36),
    "El Salvador": (13.69, -89.19), "Estonia": (59.44, 24.75), "France": (48.86, 2.35), "Georgia": (41.72, 44.79),
    "Germany": (50.11, 8.68), "Gibraltar": (36.14, -5.35), "Hong Kong": (22.32, 114.17), "India": (19.08, 72.88),
    "Indonesia": (-6.2, 106.85), "Isle of Man": (54.15, -4.48), "Israel": (32.09, 34.78), "Italy": (45.46, 9.19),
    "Jamaica": (18.0, -76.79), "Japan": (35.68, 139.69), "Lithuania": (54.69, 25.28), "Luxembourg": (49.61, 6.13),
    "Malaysia": (3.14, 101.69), "Malta": (35.9, 14.51), "Marshall Islands": (7.09, 171.38), "Netherlands": (52.37, 4.9),
    "Norway": (59.91, 10.75), "Panama": (8.98, -79.52), "Philippines": (14.6, 120.98), "Poland": (52.23, 21.01),
    "Saint Vincent and the Grenadines": (13.16, -61.23), "Samoa": (-13.83, -171.76), "Seychelles": (-4.62, 55.45),
    "Singapore": (1.29, 103.85), "South Africa": (-26.2, 28.05), "South Korea": (37.57, 126.98), "Spain": (40.42, -3.7),
    "Switzerland": (47.37, 8.54), "Taiwan": (25.03, 121.57), "Thailand": (13.75, 100.5), "Turkey": (41.01, 28.98),
    "United Arab Emirates": (25.2, 55.27), "United Kingdom": (51.51, -0.13), "United States": (37.77, -122.42),
    "Vanuatu": (-17.73, 168.32), "Vietnam": (10.82, 106.63), "Bermuda": (32.29, -64.78), "Curacao": (12.12, -68.93),
    "Mauritius": (-20.16, 57.5), "Belize": (17.25, -88.77), "Saint Kitts and Nevis": (17.3, -62.72), "Mexico": (19.43, -99.13),
    "Argentina": (-34.6, -58.38), "Nigeria": (6.52, 3.38), "Ireland": (53.35, -6.26), "Bulgaria": (42.7, 23.32),
    "Czech Republic": (50.08, 14.44), "Ukraine": (50.45, 30.52), "Kazakhstan": (43.24, 76.89), "Russia": (55.76, 37.62),
}
SAME = {"Panama Canal Zone": "Panama"}
ISLANDS = {"Seychelles", "British Virgin Islands", "Cayman Islands", "Marshall Islands", "Vanuatu", "Samoa", "Bahamas", "Jamaica",
           "Saint Vincent and the Grenadines", "Isle of Man", "Malta", "Cyprus", "Bermuda", "Curacao", "Mauritius", "Saint Kitts and Nevis"}


def get(path):
    req = urllib.request.Request(API + path, headers={"User-Agent": "site-build/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch():
    rows = get("coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&price_change_percentage=24h,7d")
    world = get("global")["data"]
    coins = []
    for r in rows:
        sym = (r.get("symbol") or "").lower()
        if WRAPPED.search(r.get("name") or "") or WRAPPED.search(r.get("id") or "") or sym in WRAPPED_SYMBOLS:
            continue
        if not r.get("market_cap") or r.get("current_price") is None:
            continue
        coins.append({"id": r["id"], "symbol": sym.upper(), "name": r["name"], "price": r["current_price"], "cap": r["market_cap"],
                      "day": r.get("price_change_percentage_24h_in_currency"), "week": r.get("price_change_percentage_7d_in_currency"),
                      "stable": sym in STABLE})
        if len(coins) == KEEP:
            break
    if len(coins) < 40 or coins[0]["id"] != "bitcoin":
        raise ValueError("unexpected list of coins")
    stamp = max(r.get("last_updated") or "" for r in rows)
    return {"coins": coins, "total": world["total_market_cap"]["usd"], "btc_share": world["market_cap_percentage"]["btc"],
            "asof": stamp, "source": "CoinGecko", "fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def exchanges():
    """The day's trading by the country each exchange declares as its seat (an island is flagged)."""
    rows = []
    for page in (1, 2):
        rows += get(f"exchanges?per_page=250&page={page}")
    if len(rows) < 100:
        raise ValueError("unexpected list of exchanges")
    total, seats, lost = 0.0, {}, set()
    for r in rows:
        vol = r.get("trade_volume_24h_btc") or 0
        total += vol
        name = SAME.get(r.get("country") or "", r.get("country") or "")
        if name not in SEATS:
            if name and name != "Unknown or Invalid Region":
                lost.add(name)
            continue
        s = seats.setdefault(name, {"name": name, "vol": 0.0, "list": []})
        s["vol"] += vol
        s["list"].append((vol, r.get("name") or ""))
    if total <= 0:
        raise ValueError("no volume")
    if lost:
        print("crypto: seats with no place in SEATS, counted with no country: " + ", ".join(sorted(lost)))
    out = []
    for s in sorted(seats.values(), key=lambda s: -s["vol"]):
        lat, lon = SEATS[s["name"]]
        out.append({"name": s["name"], "lat": lat, "lon": lon, "share": round(s["vol"] / total, 5), "n": len(s["list"]),
                    "top": [n for v, n in sorted(s["list"], reverse=True)[:3]], "island": s["name"] in ISLANDS})
    placed = sum(c["share"] for c in out)
    return {"countries": out, "unplaced": round(max(0.0, 1 - placed), 5), "islands": round(sum(c["share"] for c in out if c["island"]), 5),
            "count": len(rows), "fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def main():
    old = {}
    if CACHE.exists():
        try:
            old = json.loads(CACHE.read_text(encoding="utf-8"))
        except ValueError:
            old = {}
    warn = lambda m: print(f"::warning::{m}" if "GITHUB_ACTIONS" in __import__("os").environ else m)
    try:
        data = fetch()
    except Exception as e:  # noqa: BLE001  the deploy goes on with the last good copy
        warn(f"crypto: {type(e).__name__}: {e}; keeping the last copy of the coins")
        data = {k: v for k, v in old.items() if k != "exchanges"} if old.get("coins") else None
    try:
        data_ex = exchanges()
    except Exception as e:  # noqa: BLE001
        warn(f"crypto: exchanges: {type(e).__name__}: {e}; keeping the last copy")
        data_ex = old.get("exchanges")
    if not data:
        return 0
    if data_ex:
        data["exchanges"] = data_ex
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    ex = data.get("exchanges") or {}
    print(f"crypto: {len(data['coins'])} coins, {data['source']}, {data['asof']}; {ex.get('count', 0)} exchanges in {len(ex.get('countries', []))} countries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
