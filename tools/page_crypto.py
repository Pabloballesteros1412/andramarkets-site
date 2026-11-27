"""Crypto (crypto/): Bitcoin as a sun and the other coins as its planets.

Owner-approved sketch, 27 Nov 2026 ("the Bitcoin sun", chosen over three flat looks: the group keeps the site's
sky and takes an amber light of its own). The page is a table of the largest coins by market value, from
.cache/crypto/crypto.json (tools/crypto_data.py, CoinGecko); assets/crypto-sun.js draws that table as a system
over it: the sun is Bitcoin, each planet a coin sized by its market value, the larger the nearer. Every figure on
the picture is the table's own. Without the script, or without WebGL or canvas, the page is the table.
"""
import datetime as dt
import json

MINUS = "−"
PLANETS = 24  # the largest coins after Bitcoin are planets; the rest of the hundred are the belt beyond them


def load(site):
    try:
        d = json.loads((site.ROOT / ".cache" / "crypto" / "crypto.json").read_text(encoding="utf-8"))
        return d if len(d.get("coins") or []) >= 10 else None
    except (OSError, ValueError):
        return None


def money(v):
    if v >= 1000:
        return f"${v:,.0f}"
    if v >= 1:
        return f"${v:,.2f}"
    return f"${v:.4f}" if v >= 0.01 else f"${v:.6f}"


def big(v):
    return f"${v / 1e12:.2f}tn" if v >= 1e12 else f"${v / 1e9:.1f}bn" if v >= 1e9 else f"${v / 1e6:.0f}m"


def move(v):
    """A signed change, coloured (the Rise and Fall Rule); a dash when the source has none."""
    if v is None:
        return '<span class="cs-none">n/a</span>'
    n = round(v, 1)
    cls = "up" if n > 0 else "down" if n < 0 else ""
    return f'<span class="{cls}">{"+" if n > 0 else MINUS if n < 0 else ""}{abs(n):.1f}%</span>'


def pages(site):
    d = load(site)
    if not d:
        body = """<main id="main" class="page cs-page"><div class="wrap"><header class="page__head"><h1 class="page__title">Crypto</h1>
<p class="lede">Bitcoin and everything that turns round it.</p></header>
<div class="dd__plot dd__plot--pending"><p class="dd__pending">Data pending</p></div></div></main>"""
        return {"crypto/": site.shell(title="Crypto: Andra Markets", desc="Bitcoin and the largest coins by market value.",
                                      body=body, home="../", base="../", path="crypto/")}
    coins = d["coins"]
    try:
        asof = dt.datetime.fromisoformat(d["asof"].replace("Z", "+00:00"))
        when = f"{asof.day} {asof:%b %Y}, {asof:%H:%M} UTC"
    except ValueError:
        when = ""
    rows = "".join(
        f'<tr id="c-{site.esc(c["id"])}" data-cap="{c["cap"]}" data-rank="{i + 1}"{" data-stable" if c["stable"] else ""}>'
        f'<td class="cs-rank">{i + 1}</td><th scope="row"><span class="cs-name">{site.esc(c["name"])}</span> <span class="cs-sym">{site.esc(c["symbol"])}</span>'
        f'{"<span class=cs-peg>pegged</span>" if c["stable"] else ""}</th>'
        f'<td class="cs-price">{money(c["price"])}</td><td class="cs-day">{move(c["day"])}</td><td class="cs-week">{move(c["week"])}</td>'
        f'<td class="cs-cap">{big(c["cap"])}</td></tr>' for i, c in enumerate(coins))
    btc = coins[0]
    body = f"""<main id="main" class="page cs-page">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Crypto</h1>
      <p class="lede">Bitcoin and everything that turns round it.</p>
      <p class="note__meta"><span>The whole market {big(d["total"])}</span><span>Bitcoin {d["btc_share"]:.1f}% of it</span><span>Data from CoinGecko, {when}</span></p>
    </header>
    <div class="cs" data-planets="{PLANETS}" hidden>
      <canvas aria-hidden="true"></canvas>
      <div class="cs__names"></div>
      <p class="lens-read cs__read">Size by market value · the larger the coin, the nearer its orbit · the belt is the rest of the hundred · the surfaces and the turning are not data</p>
      <a class="lib-map__down" href="#cs-all">Every coin</a>
    </div>
    <section id="cs-all" aria-labelledby="cs-all-h">
      <h2 id="cs-all-h" class="cs-h">The {len(coins)} largest coins</h2>
      <p class="cs-sub">By market value in US dollars. Coins that are another coin under a wrapper (wrapped, staked or bridged) are left out. "Pegged" marks a coin held to a currency.</p>
      <div class="cs-scroll"><table class="cs-tab"><thead><tr><th scope="col"><span class="visually-hidden">Rank</span></th><th scope="col">Coin</th><th scope="col">Price</th>
        <th scope="col">Day</th><th scope="col">Week</th><th scope="col">Market value</th></tr></thead><tbody>{rows}</tbody></table></div>
      <p class="report__src">CoinGecko, {when}. Prices and changes in US dollars; a day is the last 24 hours, a week the last seven days. For information only. Not investment advice. Surfaces of the Sun and planets: Solar System Scope (CC BY 4.0), from NASA imagery.</p>
    </section>
  </div>
</main>"""
    return {"crypto/": site.shell(
        title="Crypto: Andra Markets",
        desc=f"Bitcoin at {money(btc['price'])} and the {len(coins) - 1} largest coins after it by market value, with their change over a day and a week.",
        body=body, home="../", base="../", path="crypto/", scripts=("crypto-sun.js",))}
