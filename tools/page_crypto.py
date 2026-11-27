"""Crypto (crypto/): where the coins trade, and what they are worth.

Owner-approved sketch and build, 27 Nov 2026 (after the Bitcoin sun and its planets, the eclipse and two flat
maps: "sober, like the maps, and realistic"). Under the head, the real Earth as it was lit at the time of the
data, and a column of amber light from each country where exchanges declare their seat, as tall as that
country's share of the day's trading (assets/crypto-globe.js; the figures are in the page as JSON and in the
table of seats below it). Then the table of the hundred largest coins by market value. All from
.cache/crypto/crypto.json (tools/crypto_data.py, CoinGecko). Without the script or WebGL, the page is the two tables.
"""
import datetime as dt
import json

MINUS = "−"
SEATS_SHOWN = 12  # countries in the table of seats under the globe; the globe draws them all
LEDE = "Where the coins trade, and what they are worth."


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
<p class="lede">""" + LEDE + """</p></header>
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
    globe, seats = "", ""
    ex = d.get("exchanges") or {}
    places = ex.get("countries") or []
    if places:
        def pct(v):
            return f"{v * 100:.1f}%" if v < 0.01 else f"{v * 100:.0f}%"
        try:
            fetched = dt.datetime.fromisoformat(ex["fetched"].replace("Z", "+00:00"))
            ex_when = f"{fetched.day} {fetched:%b %Y}, {fetched:%H:%M} UTC"
        except (KeyError, ValueError):
            ex_when = when
        data = {"asof": ex.get("fetched") or d.get("asof"), "count": ex.get("count"), "places": [
            {k: c[k] for k in ("name", "lat", "lon", "share", "n", "top", "island")} for c in places]}
        isl = ex.get("islands") or 0
        globe = f"""
    <section class="cg" aria-label="Where the day's trading is registered" hidden>
      <canvas class="cg__gl" aria-hidden="true"></canvas>
      <canvas class="cg__ov" aria-hidden="true"></canvas>
      <div class="cg__names" aria-hidden="true"></div>
      <div class="cg__big"><p class="lens-read">Registered on islands</p><p class="cg__fig">{pct(isl)}</p>
        <p class="cg__say">of the day's trading on {ex.get("count")} exchanges goes through exchanges registered on islands.</p></div>
      <p class="visually-hidden cg__status" role="status" aria-live="polite"></p>
      <p class="lens-read cg__read">The Earth as lit at {ex_when} · each column, a country where exchanges are registered, as tall as its share of the day's trading</p>
      <a class="lib-map__down" href="#cg-seats">Every seat</a>
      <script type="application/json">{json.dumps(data, separators=(",", ":")).replace("</", "<\\/")}</script>
    </section>"""
        trs = "".join(
            f'<tr><th scope="row">{site.esc(c["name"])}{" <span class=cs-peg>island</span>" if c["island"] else ""}</th><td class="cs-cap">{pct(c["share"])}</td>'
            f'<td class="cs-price">{c["n"]}</td><td class="cg-top">{site.esc(", ".join(c["top"]))}</td></tr>' for c in places[:SEATS_SHOWN])
        seats = f"""
    <section id="cg-seats" aria-labelledby="cg-seats-h">
      <h2 id="cg-seats-h" class="cs-h">Where the day's trading is registered</h2>
      <p class="cs-sub">Each exchange's volume over the last 24 hours, added up by the country it declares as its seat: where it is registered, not where its customers live. {pct(ex.get("unplaced") or 0)} of the volume names no country.</p>
      <div class="cs-scroll"><table class="cs-tab cg-tab"><thead><tr><th scope="col">Country</th><th scope="col">Share of the day</th><th scope="col">Exchanges</th><th scope="col">Largest there</th></tr></thead><tbody>{trs}</tbody></table></div>
      <p class="report__src">CoinGecko, {ex_when}: the {ex.get("count")} exchanges it lists, volume in bitcoin. {len(places)} countries in all; the {min(SEATS_SHOWN, len(places))} largest here. The Earth: Solar System Scope (CC BY 4.0), from NASA imagery.</p>
    </section>"""
    body = f"""<main id="main" class="page cs-page">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Crypto</h1>
      <p class="lede">{LEDE}</p>
      <p class="note__meta"><span>The whole market {big(d["total"])}</span><span>Bitcoin {d["btc_share"]:.1f}% of it</span><span>Data from CoinGecko, {when}</span></p>
    </header>
    {globe}{seats}
    <section id="cs-all" aria-labelledby="cs-all-h">
      <h2 id="cs-all-h" class="cs-h">The {len(coins)} largest coins</h2>
      <p class="cs-sub">By market value in US dollars. Coins that are another coin under a wrapper (wrapped, staked or bridged) are left out. "Pegged" marks a coin held to a currency.</p>
      <div class="cs-scroll"><table class="cs-tab"><thead><tr><th scope="col"><span class="visually-hidden">Rank</span></th><th scope="col">Coin</th><th scope="col">Price</th>
        <th scope="col">Day</th><th scope="col">Week</th><th scope="col">Market value</th></tr></thead><tbody>{rows}</tbody></table></div>
      <p class="report__src">CoinGecko, {when}. Prices and changes in US dollars; a day is the last 24 hours, a week the last seven days. For information only. Not investment advice.</p>
    </section>
  </div>
</main>"""
    return {"crypto/": site.shell(
        title="Crypto: Andra Markets",
        desc=f"Where the day's crypto trading is registered, country by country, and the {len(coins)} largest coins by market value: Bitcoin at {money(btc['price'])}.",
        body=body, home="../", base="../", path="crypto/", scripts=("crypto-globe.js",) if places else ())}
