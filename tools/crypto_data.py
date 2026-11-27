#!/usr/bin/env python3
"""Fetch the figures behind Crypto (crypto/), at deploy time.

Run by .github/workflows/pages.yml before tools/build_site.py. Writes one file,
.cache/crypto/crypto.json: the largest coins by market value (price, value, the
change over a day and over a week) and the whole market's value with Bitcoin's
share of it. tools/page_crypto.py reads it; nothing here is published as a file.

Source: CoinGecko's public API, no key (https://www.coingecko.com/en/api). Its
terms ask for attribution, which the page gives beside every figure's date.
Tokens that are another coin under a wrapper (wrapped, staked or bridged) are
left out, so no coin is counted twice. A failed fetch keeps the last good copy
(restored by the workflow's cache) with its own date, and never stops the deploy.

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
KEEP = 30
# Another coin under a wrapper: by name, or by a symbol the name does not give away.
WRAPPED = re.compile(r"wrapped|staked|staking|bridged|restaked|binance-peg", re.I)
WRAPPED_SYMBOLS = {"wbtc", "weth", "steth", "wsteth", "weeth", "cbbtc", "reth", "wbeth", "lbtc", "jitosol", "msol", "bnsol", "rseth", "solvbtc"}
# Pegged to a currency: shown, and marked, since their value says nothing of their price.
STABLE = {"usdt", "usdc", "dai", "usds", "usde", "fdusd", "pyusd", "usd1", "tusd", "usdd", "frax", "susds", "susde", "usdf", "bfusd", "rlusd", "usdg", "usdtb", "buidl"}


def get(path):
    req = urllib.request.Request(API + path, headers={"User-Agent": "site-build/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch():
    rows = get("coins/markets?vs_currency=usd&order=market_cap_desc&per_page=80&page=1&price_change_percentage=24h,7d")
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
    if len(coins) < 10 or coins[0]["id"] != "bitcoin":
        raise ValueError("unexpected list of coins")
    stamp = max(r.get("last_updated") or "" for r in rows)
    return {"coins": coins, "total": world["total_market_cap"]["usd"], "btc_share": world["market_cap_percentage"]["btc"],
            "asof": stamp, "source": "CoinGecko", "fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def main():
    try:
        data = fetch()
    except Exception as e:  # noqa: BLE001  the deploy goes on with the last good copy
        msg = f"crypto: {type(e).__name__}: {e}; keeping the last copy"
        print(f"::warning::{msg}" if "GITHUB_ACTIONS" in __import__("os").environ else msg)
        return 0
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"crypto: {len(data['coins'])} coins, {data['source']}, {data['asof']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
