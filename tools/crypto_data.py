#!/usr/bin/env python3
"""Fetch the figures behind Crypto (crypto/), at deploy time.

Run by .github/workflows/pages.yml before tools/build_site.py. Writes one file,
.cache/crypto/crypto.json: the largest coins by market value (price, value, the
change over a day and over a week), the whole market's value with Bitcoin's
share of it, and where the day's trading is registered: the 500 exchanges
CoinGecko lists, their 24-hour volume added up by the country each declares as
its seat. Also .cache/crypto/btc.json: Bitcoin's closing price every day since
July 2010 (Coin Metrics Community Data, CC BY-NC 4.0, no key) and the current block
height (mempool.space), for the Bitcoin page. And for each of the other coins a
file in .cache/crypto/coins/ (its daily closes, from Coin Metrics where it has
them and otherwise CoinGecko's last year; its network's active addresses,
transactions and supply where Coin Metrics has them; for the 25 largest, the
exchanges where it trades) and its logo in .cache/crypto/logos/, for the coin
pages. And .cache/crypto/markets.json: the daily closes since September 2014 of the
S&P 500, the Nasdaq Composite, gold, the dollar index and long Treasuries (Yahoo
Finance), for Bitcoin vs markets. And .cache/crypto/derivs.json: Bitcoin's derivatives
on Deribit (the DVOL index, the perpetual's funding, futures and options), for
Derivatives. And .cache/crypto/network.json: Bitcoin's network from mempool.space
(hashrate, difficulty, pools, fees, the queue and the Lightning network), for Network.
And .cache/crypto/defi.json: stablecoins and DeFi from DefiLlama, for Stablecoins & DeFi. tools/page_crypto.py reads them all; nothing here
is published as a file.

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
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "crypto" / "crypto.json"
HISTORY = ROOT / ".cache" / "crypto" / "btc.json"
COINS_DIR = ROOT / ".cache" / "crypto" / "coins"
LOGOS = ROOT / ".cache" / "crypto" / "logos"
CM = "https://community-api.coinmetrics.io/v4/"
NET_METRICS = ("AdrActCnt", "TxCnt", "SplyCur")
TICKERS_FOR = 25  # the largest coins get the table of exchanges; CoinGecko's public limits allow no more
COINMETRICS = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?assets=btc&metrics=PriceUSD&frequency=1d&page_size=10000&start_time=2010-07-18"
MEMPOOL = "https://mempool.space/api/blocks/tip/height"
API = "https://api.coingecko.com/api/v3/"
KEEP = 100
# Another coin under a wrapper: by name, or by a symbol the name does not give away.
WRAPPED = re.compile(r"wrapped|staked|staking|bridged|restaked|binance-peg", re.I)
WRAPPED_SYMBOLS = {"wbtc", "weth", "steth", "wsteth", "weeth", "cbbtc", "reth", "wbeth", "lbtc", "jitosol", "msol", "bnsol", "rseth", "solvbtc"}
# Pegged to a currency: shown, and marked, since their value says nothing of their price.
STABLE = {"usdt", "usdc", "dai", "usds", "usde", "fdusd", "pyusd", "usd1", "tusd", "usdd", "frax", "susds", "susde", "usdf", "bfusd", "rlusd", "usdg", "usdtb", "buidl",
          "usdy", "usyc", "ousg", "usdo", "frxusd", "gho", "crvusd", "usd0", "lusd", "eurc", "usdx", "usdb", "usda", "usd0++", "syrupusdc", "jaaa", "jtrsy",
          "xaut", "paxg"}  # the last two are held to gold, not to a currency, and are marked the same way


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
    return get_url(API + path)


def get_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "site-build/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def spark(prices, n=42):
    """The last seven days in about n points (CoinGecko gives them hourly), four significant figures."""
    if len(prices) < 2:
        return []
    step = max(1, len(prices) // n)
    pts = prices[::step] + ([prices[-1]] if (len(prices) - 1) % step else [])
    return [float(f"{p:.4g}") for p in pts if p is not None]


def history():
    """Bitcoin's close every day since 18 July 2010, as one list from the first day, and the block height."""
    rows, url = [], COINMETRICS
    while url and len(rows) < 100000:   # one page holds 10,000 days; later years page on
        page = get_url(url)
        rows += page.get("data") or []
        url = page.get("next_page_url")
    days = [(r["time"][:10], float(r["PriceUSD"])) for r in rows if r.get("PriceUSD")]
    if len(days) < 5000 or days[0][0] != "2010-07-18":
        raise ValueError("unexpected Bitcoin history")
    out, d0 = [], dt.date.fromisoformat(days[0][0])
    for day, price in days:   # one figure a day; a missing day keeps the day before's
        k = (dt.date.fromisoformat(day) - d0).days
        while len(out) < k:
            out.append(out[-1])
        out.append(float(f"{price:.5g}"))
    try:
        height = int(urllib.request.urlopen(urllib.request.Request(MEMPOOL, headers={"User-Agent": "site-build/1.0"}), timeout=20).read().decode().strip())
    except Exception:  # noqa: BLE001
        height = None
    return {"start": days[0][0], "last": days[-1][0], "p": out, "height": height, "source": "Coin Metrics", "fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def cm_catalog(metric):
    """The assets Coin Metrics' free tier carries a metric for."""
    out, url = set(), f"{CM}catalog-v2/asset-metrics?metrics={metric}&page_size=1000"
    for _ in range(20):
        page = get_url(url)
        out |= {x["asset"] for x in page.get("data") or []}
        url = page.get("next_page_url")
        if not url:
            break
    return out


def daily(rows, key):
    """[(date, value)] to one list from the first date, a missing day keeping the day before's."""
    days = [(r["time"][:10], float(r[key])) for r in rows if r.get(key) not in (None, "")]
    if not days:
        return None, []
    out, d0 = [], dt.date.fromisoformat(days[0][0])
    for day, v in days:
        k = (dt.date.fromisoformat(day) - d0).days
        while len(out) < k:
            out.append(out[-1])
        out.append(float(f"{v:.5g}"))
    return days[0][0], out


def coin_detail(c, cats, rank):
    """One coin's history, network and exchanges. Coin Metrics when it has the coin and its last price agrees
    with CoinGecko's within a quarter; otherwise CoinGecko's last 365 days."""
    import time
    sym, rec = c["symbol"].lower(), {"id": c["id"], "fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    if sym in cats["PriceUSD"]:
        mets = ["PriceUSD"] + [m for m in NET_METRICS if sym in cats[m]]
        try:
            rows, url = [], f"{CM}timeseries/asset-metrics?assets={sym}&metrics={','.join(mets)}&frequency=1d&page_size=10000"
            while url and len(rows) < 100000:
                page = get_url(url)
                rows += page.get("data") or []
                url = page.get("next_page_url")
                time.sleep(0.7)
            start, p = daily(rows, "PriceUSD")
            if p and c["price"] and 0.8 < p[-1] / c["price"] < 1.25:
                rec.update({"start": start, "p": p, "source": "Coin Metrics"})
                net = {}
                for m in NET_METRICS:
                    if m in mets:
                        ns, nv = daily(rows, m)
                        if nv and len(nv) > 365:
                            net[m] = {"start": ns, "v": nv}
                if net:
                    rec["net"] = net
        except Exception as e:  # noqa: BLE001
            print(f"crypto: {c['id']} from Coin Metrics: {type(e).__name__}: {e}")
    if "p" not in rec:
        for attempt in (1, 2, 3, 4):
            try:
                rows = get(f"coins/{c['id']}/market_chart?vs_currency=usd&days=365&interval=daily")["prices"]
                by_day = {}
                for t, v in rows:
                    by_day[dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc).date().isoformat()] = v
                days = sorted(by_day)[:-1] if len(by_day) > 2 else sorted(by_day)   # the last point is today, not a close
                start, p = daily([{"time": d, "v": by_day[d]} for d in days], "v")
                if p:
                    rec.update({"start": start, "p": p, "source": "CoinGecko"})
                break
            except Exception as e:  # noqa: BLE001   CoinGecko's public limit: wait it out, longer each time
                if attempt < 4:
                    time.sleep(30 * attempt)
                else:
                    print(f"crypto: {c['id']} from CoinGecko: {type(e).__name__}: {e}")
        time.sleep(2.5)
    if rank <= TICKERS_FOR:
        try:
            try:
                t = get(f"coins/{c['id']}/tickers?order=volume_desc&depth=false").get("tickers") or []
            except urllib.error.HTTPError as e:
                if e.code != 429:
                    raise
                time.sleep(45)   # CoinGecko's public limit: wait it out once
                t = get(f"coins/{c['id']}/tickers?order=volume_desc&depth=false").get("tickers") or []
            rec["tickers"] = [{"ex": x["market"]["name"], "pair": f"{x['base']}/{x['target']}"[:24], "vol": (x.get("converted_volume") or {}).get("usd")}
                              for x in t[:60] if (x.get("converted_volume") or {}).get("usd")]
        except Exception as e:  # noqa: BLE001
            print(f"crypto: {c['id']} tickers: {type(e).__name__}: {e}")
        time.sleep(2.5)
    return rec


def logo(c):
    """The coin's logo from CoinGecko, kept: fetched once."""
    have = list(LOGOS.glob(f"{c['id']}.*")) if LOGOS.exists() else []
    if have or not c.get("image"):
        return
    try:
        req = urllib.request.Request(c["image"], headers={"User-Agent": "site-build/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            body, kind = r.read(), r.headers.get("Content-Type", "")
        ext = ".png" if body[:8] == b"\x89PNG\r\n\x1a\n" else ".jpg" if body[:3] == b"\xff\xd8\xff" else ".webp" if body[8:12] == b"WEBP" else None
        if ext and len(body) < 400000:
            LOGOS.mkdir(parents=True, exist_ok=True)
            (LOGOS / f"{c['id']}{ext}").write_bytes(body)
    except Exception as e:  # noqa: BLE001
        print(f"crypto: {c['id']} logo: {type(e).__name__}: {e}")


def coins_detail(coins):
    try:
        cats = {m: cm_catalog(m) for m in ("PriceUSD",) + NET_METRICS}
    except Exception as e:  # noqa: BLE001
        print(f"crypto: Coin Metrics catalog: {type(e).__name__}: {e}; CoinGecko only")
        cats = {m: set() for m in ("PriceUSD",) + NET_METRICS}
    COINS_DIR.mkdir(parents=True, exist_ok=True)
    done = {"Coin Metrics": 0, "CoinGecko": 0, "kept": 0}
    for rank, c in enumerate(coins, 1):
        if c["id"] == "bitcoin":
            continue
        logo(c)
        rec = coin_detail(c, cats, rank)
        path = COINS_DIR / f"{c['id']}.json"
        if "tickers" not in rec and path.exists() and rank <= TICKERS_FOR:
            try:
                old = json.loads(path.read_text(encoding="utf-8")).get("tickers")
                if old:
                    rec["tickers"] = old
            except ValueError:
                pass
        if "p" not in rec:
            done["kept"] += path.exists()
            continue   # the last good copy stays
        path.write_text(json.dumps(rec, separators=(",", ":")), encoding="utf-8")
        done[rec["source"]] += 1
    print(f"crypto: coin pages from Coin Metrics {done['Coin Metrics']}, CoinGecko {done['CoinGecko']}, last copy {done['kept']}")


DERIVS = ROOT / ".cache" / "crypto" / "derivs.json"
DERIBIT = "https://www.deribit.com/api/v2/public/"
_MONTHS = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}


def _expiry(code):
    """Deribit's expiry code ("25DEC26") as a date."""
    m = re.match(r"(\d+)([A-Z]{3})(\d\d)$", code)
    return dt.date(2000 + int(m[3]), _MONTHS[m[2]], int(m[1])).isoformat()


def derivatives(old):
    """Bitcoin's derivatives on Deribit, no key: the DVOL index day by day, the perpetual's funding day by day,
    every future's mark price and open interest, and every option's open interest and volatility by expiry and
    strike. DVOL and funding come in windows (1,000 days, 30 days): each run adds to what the cache already holds."""
    import time

    def g(path):
        return get_url(DERIBIT + path)["result"]
    now = int(time.time() * 1000)
    spot = g("get_index_price?index_name=btc_usd")["index_price"]
    dvol = dict((old or {}).get("dvol") or [])
    for r in g(f"get_volatility_index_data?currency=BTC&resolution=1D&start_timestamp=1609459200000&end_timestamp={now}")["data"]:
        dvol[dt.datetime.fromtimestamp(r[0] / 1000, dt.timezone.utc).date().isoformat()] = r[4]
    fund = dict((old or {}).get("fund") or [])
    hours = {}
    for k in range(6 if len(fund) < 150 else 1):
        end = now - k * 30 * 86400000
        for f in g(f"get_funding_rate_history?instrument_name=BTC-PERPETUAL&start_timestamp={end - 30 * 86400000}&end_timestamp={end}"):
            hours.setdefault(dt.datetime.fromtimestamp(f["timestamp"] / 1000, dt.timezone.utc).date().isoformat(), []).append(f["interest_1h"])
        time.sleep(0.4)
    for day, v in hours.items():
        if len(v) >= 20 or day not in fund:   # a whole day's hours, as a yearly rate in percent
            fund[day] = round(sum(v) / len(v) * 24 * 365 * 100, 3)
    futures = []
    for x in g("get_book_summary_by_currency?currency=BTC&kind=future"):
        parts = x["instrument_name"].split("-")
        if len(parts) != 2 or parts[0] != "BTC":
            continue
        futures.append({"name": parts[1], "date": None if parts[1] == "PERPETUAL" else _expiry(parts[1]), "mark": x["mark_price"], "oi": x["open_interest"]})
    exps = {}
    for x in g("get_book_summary_by_currency?currency=BTC&kind=option"):
        _, code, strike, kind = x["instrument_name"].split("-")
        e = exps.setdefault(code, {"date": _expiry(code), "und": None, "k": {}})
        e["und"] = x.get("underlying_price") or e["und"]
        row = e["k"].setdefault(int(strike), [0.0, 0.0, None, None])   # calls, puts, the calls' volatility, the puts'
        row[0 if kind == "C" else 1] += x.get("open_interest") or 0
        row[2 if kind == "C" else 3] = x.get("mark_iv")
    if len(dvol) < 300 or len(exps) < 3 or not futures:
        raise ValueError("unexpected derivatives data")
    return {"spot": spot, "dvol": sorted(dvol.items()), "fund": sorted(fund.items()), "futures": futures,
            "expiries": [{"date": e["date"], "und": e["und"], "k": [[k] + [None if v is None else round(v, 2) for v in row] for k, row in sorted(e["k"].items())]}
                         for e in sorted(exps.values(), key=lambda e: e["date"])],
            "source": "Deribit", "fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


NETWORK = ROOT / ".cache" / "crypto" / "network.json"
MEMPOOL_API = "https://mempool.space/api/"


def network():
    """Bitcoin's network from mempool.space, no key: the hashrate day by day, the difficulty's next change, the
    month's blocks by mining pool, fees now and block by block over a year, the queue, and the Lightning network
    (its totals, its nodes by country, and where each node that publishes an address says it is)."""
    import math
    import time

    def g(path):
        time.sleep(0.4)
        return get_url(MEMPOOL_API + path)
    hr = g("v1/mining/hashrate/all")
    rows = [(h["timestamp"], h["avgHashrate"] / 1e18) for h in hr["hashrates"] if h["timestamp"] >= 1262304000 and h["avgHashrate"]]
    if len(rows) < 3000:
        raise ValueError("short hashrate history")
    hashes = []
    for i in range(0, len(rows), 2):   # every second day, each the average of the week to it, in EH/s
        w = [v for _, v in rows[max(0, i - 6):i + 1]]
        hashes.append([dt.datetime.fromtimestamp(rows[i][0], dt.timezone.utc).date().isoformat(), float(f"{sum(w) / len(w):.4g}")])
    pools = g("v1/mining/pools/1m")
    fr = g("v1/mining/blocks/fee-rates/1y")
    world = g("v1/lightning/nodes/world")
    countries = g("v1/lightning/nodes/countries")
    top = math.log(1 + (world.get("maxLiquidity") or 1))
    cells, by_country = {}, {}
    for n in world["nodes"]:
        lon, lat, cap = n[0], n[1], n[4] or 0
        if lon is None or lat is None:
            continue
        key = (round(lon, 1), round(lat, 1))   # nodes in one town are one light, as bright as its largest
        cells[key] = max(cells.get(key, 0), round(math.log(1 + cap) / top, 2))
        name = n[6].get("en") if isinstance(n[6], dict) else None
        if name:
            by_country.setdefault(name, []).append((lon, lat))
    located = sum(1 for n in world["nodes"] if n[0] is not None and n[1] is not None)
    places = []
    for c in countries[:40]:
        name = c["name"]["en"]
        ll = by_country.get(name)
        if not ll:
            continue
        lons, lats = sorted(x for x, _ in ll), sorted(y for _, y in ll)   # the middle node: steady for a wide country
        places.append({"name": name, "lon": lons[len(lons) // 2], "lat": lats[len(lats) // 2], "count": c["count"], "share": c["share"], "btc": int(c["capacity"] or 0) / 1e8})
    if len(places) < 5 or len(cells) < 200:
        raise ValueError("unexpected Lightning data")
    return {"hash": hashes, "now": hr["currentHashrate"] / 1e18, "difficulty": g("v1/difficulty-adjustment"),
            "pools": {"blocks": pools["blockCount"], "list": [[x["name"], x["blockCount"]] for x in pools["pools"][:12]]},
            "fees": g("v1/fees/recommended"), "queue": {k: v for k, v in g("mempool").items() if k in ("count", "vsize", "total_fee")},
            "feerates": [[r["timestamp"], r["avgFee_50"], r["avgFee_90"]] for r in fr][::2],
            "ln": g("v1/lightning/statistics/latest")["latest"], "places": places, "located": located,
            "points": [[k[0], k[1], v] for k, v in cells.items()],
            "source": "mempool.space", "fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


DEFI = ROOT / ".cache" / "crypto" / "defi.json"
LLAMA = "https://api.llama.fi/"
LLAMA_STABLE = "https://stablecoins.llama.fi/"
DEFI_FROM = 1546300800   # 1 Jan 2019


def defi():
    """Stablecoins and DeFi from DefiLlama, no key: every stablecoin's supply day by day in total, the largest
    coins (supply, a month before, price, what backs each), supply by backing and by chain, the value locked in
    DeFi day by day, and its largest chains and protocols (exchanges left out)."""
    import time

    def g(url):
        time.sleep(0.4)
        return get_url(url)
    total = [[int(r["date"]), round(((r.get("totalCirculatingUSD") or {}).get("peggedUSD") or 0) / 1e9, 3)] for r in g(LLAMA_STABLE + "stablecoincharts/all")]
    total = [r for r in total if r[0] >= DEFI_FROM][::2]
    coins = [x for x in g(LLAMA_STABLE + "stablecoins?includePrices=true")["peggedAssets"] if (x.get("circulating") or {}).get("peggedUSD")]
    coins.sort(key=lambda x: -x["circulating"]["peggedUSD"])
    supply = sum(x["circulating"]["peggedUSD"] for x in coins)
    backing = {}
    for x in coins:
        kind = {"fiat-backed": "fiat", "algorithmic": "formula"}.get(x.get("pegMechanism"), "crypto")
        backing[kind] = backing.get(kind, 0) + x["circulating"]["peggedUSD"]
    chains = sorted(([c["name"], (c.get("totalCirculatingUSD") or {}).get("peggedUSD") or 0] for c in g(LLAMA_STABLE + "stablecoinchains")), key=lambda c: -c[1])[:10]
    tvl = [[r["date"], round(r["tvl"] / 1e9, 3)] for r in g(LLAMA + "v2/historicalChainTvl") if r["date"] >= DEFI_FROM][::2]
    dchains = sorted(([c["name"], c.get("tvl") or 0] for c in g(LLAMA + "v2/chains")), key=lambda c: -c[1])[:10]
    prot = [x for x in g(LLAMA + "protocols") if x.get("tvl") and x.get("category") not in ("CEX", "Chain")]
    prot.sort(key=lambda x: -x["tvl"])
    if len(total) < 500 or len(tvl) < 500 or len(coins) < 20:
        raise ValueError("unexpected DefiLlama data")
    return {"total": total, "supply": supply, "count": len(coins), "backing": backing, "chains": chains, "tvl": tvl, "defi_chains": dchains,
            "coins": [{"name": x["name"], "symbol": x["symbol"], "supply": x["circulating"]["peggedUSD"], "month": (x.get("circulatingPrevMonth") or {}).get("peggedUSD"),
                       "price": x.get("price"), "peg": x.get("pegType"), "backing": x.get("pegMechanism")} for x in coins[:12]],
            "protocols": [[x["name"], x.get("category") or "", x["tvl"], x.get("change_7d")] for x in prot[:12]],
            "source": "DefiLlama", "fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


MARKETS = ROOT / ".cache" / "crypto" / "markets.json"
# What Bitcoin is set beside on the Bitcoin vs markets page: Yahoo Finance symbols, daily closes (adjusted, so the
# Treasury fund carries its income; the two share indices are price levels, without dividends).
MARKET_SYMBOLS = (("SPX", "^GSPC"), ("NDX", "^IXIC"), ("GOLD", "GC=F"), ("DXY", "DX-Y.NYB"), ("BOND", "TLT"))
MARKETS_FROM = "2014-09-17"


def markets():
    """Daily closes of each market since September 2014, by date."""
    import urllib.parse
    out = {}
    p1 = int(dt.datetime(2014, 9, 1, tzinfo=dt.timezone.utc).timestamp())
    p2 = int(dt.datetime.now(dt.timezone.utc).timestamp()) + 86400
    for key, sym in MARKET_SYMBOLS:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?period1={p1}&period2={p2}&interval=1d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=40) as r:
            res = json.loads(r.read().decode("utf-8"))["chart"]["result"][0]
        ind = res["indicators"]
        closes = (ind.get("adjclose") or [{}])[0].get("adjclose") or ind["quote"][0]["close"]
        days = {dt.datetime.fromtimestamp(t, dt.timezone.utc).date().isoformat(): float(f"{c:.6g}") for t, c in zip(res["timestamp"], closes) if c}
        days = {d: v for d, v in days.items() if d >= MARKETS_FROM}
        if len(days) < 2500:
            raise ValueError(f"short history for {sym}")
        out[key] = days
    return {"s": out, "source": "Yahoo Finance", "fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def fetch():
    rows = get("coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=true&price_change_percentage=24h,7d,30d,1y")
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
                      "month": r.get("price_change_percentage_30d_in_currency"), "year": r.get("price_change_percentage_1y_in_currency"),
                      "ath": r.get("ath"), "ath_date": (r.get("ath_date") or "")[:10], "atl": r.get("atl"), "atl_date": (r.get("atl_date") or "")[:10],
                      "fdv": r.get("fully_diluted_valuation"), "volume": r.get("total_volume"), "high": r.get("high_24h"), "low": r.get("low_24h"),
                      "change": r.get("price_change_24h"), "circ": r.get("circulating_supply"), "total_supply": r.get("total_supply"), "max_supply": r.get("max_supply"),
                      "image": r.get("image"),
                      "spark": spark((r.get("sparkline_in_7d") or {}).get("price") or []), "stable": sym in STABLE})
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
    try:
        hist = history()
        HISTORY.parent.mkdir(parents=True, exist_ok=True)
        HISTORY.write_text(json.dumps(hist, separators=(",", ":")), encoding="utf-8")
        print(f"crypto: Bitcoin history {hist['start']} to {hist['last']}, {len(hist['p'])} days, block {hist['height']}")
    except Exception as e:  # noqa: BLE001
        warn(f"crypto: Bitcoin history: {type(e).__name__}: {e}; keeping the last copy")
    try:
        mk = markets()
        MARKETS.parent.mkdir(parents=True, exist_ok=True)
        MARKETS.write_text(json.dumps(mk, separators=(",", ":")), encoding="utf-8")
        print(f"crypto: markets {', '.join(f'{k} {len(v)}' for k, v in mk['s'].items())}")
    except Exception as e:  # noqa: BLE001
        warn(f"crypto: markets: {type(e).__name__}: {e}; keeping the last copy")
    try:
        prev = json.loads(DERIVS.read_text(encoding="utf-8")) if DERIVS.exists() else None
        dv = derivatives(prev)
        DERIVS.parent.mkdir(parents=True, exist_ok=True)
        DERIVS.write_text(json.dumps(dv, separators=(",", ":")), encoding="utf-8")
        print(f"crypto: derivatives DVOL {len(dv['dvol'])} days, funding {len(dv['fund'])} days, {len(dv['futures'])} futures, {len(dv['expiries'])} option expiries")
    except Exception as e:  # noqa: BLE001
        warn(f"crypto: derivatives: {type(e).__name__}: {e}; keeping the last copy")
    try:
        nw = network()
        NETWORK.parent.mkdir(parents=True, exist_ok=True)
        NETWORK.write_text(json.dumps(nw, separators=(",", ":")), encoding="utf-8")
        print(f"crypto: network hashrate {len(nw['hash'])} points, {len(nw['pools']['list'])} pools, {len(nw['places'])} Lightning countries, {len(nw['points'])} lights")
    except Exception as e:  # noqa: BLE001
        warn(f"crypto: network: {type(e).__name__}: {e}; keeping the last copy")
    try:
        df = defi()
        DEFI.parent.mkdir(parents=True, exist_ok=True)
        DEFI.write_text(json.dumps(df, separators=(",", ":")), encoding="utf-8")
        print(f"crypto: defi {df['count']} stablecoins, supply {len(df['total'])} points, TVL {len(df['tvl'])} points, {len(df['protocols'])} protocols")
    except Exception as e:  # noqa: BLE001
        warn(f"crypto: defi: {type(e).__name__}: {e}; keeping the last copy")
    if not data:
        return 0
    if data_ex:
        data["exchanges"] = data_ex
    if "--no-coins" not in sys.argv:
        coins_detail(data["coins"])
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    ex = data.get("exchanges") or {}
    print(f"crypto: {len(data['coins'])} coins, {data['source']}, {data['asof']}; {ex.get('count', 0)} exchanges in {len(ex.get('countries', []))} countries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
