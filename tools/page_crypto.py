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
        out = {"crypto/": site.shell(title="Crypto: Andra Markets", desc="Where the coins trade, and what they are worth.",
                                     body=body, home="../", base="../", path="crypto/")}
        for path, title in (("crypto/prices/", "Prices"), ("crypto/bitcoin/", "Bitcoin")):
            out[path] = pending(site, path, title)
        return out
    coins = d["coins"]
    try:
        asof = dt.datetime.fromisoformat(d["asof"].replace("Z", "+00:00"))
        when = f"{asof.day} {asof:%b %Y}, {asof:%H:%M} UTC"
    except ValueError:
        when = ""
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
    {more(site, "crypto/", "../")}
  </div>
</main>"""
    out = {"crypto/": site.shell(
        title="Crypto: Andra Markets",
        desc="Where the day's crypto trading is registered, country by country, on the real Earth.",
        body=body, home="../", base="../", path="crypto/", scripts=("crypto-globe.js",) if places else ())}
    out["crypto/prices/"] = prices_page(site, d, when)
    out["crypto/bitcoin/"] = bitcoin_page(site, d, load_history(site))
    return out


# ---- the other sections ------------------------------------------------------------------------------------------
SECTIONS = (("crypto/", "Where it trades"), ("crypto/prices/", "Prices"), ("crypto/bitcoin/", "Bitcoin"))
HALVINGS = (("2012-11-28", 210000), ("2016-07-09", 420000), ("2020-05-11", 630000), ("2024-04-20", 840000))
MON = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def more(site, here, base):
    """The group's sections, at the foot of each one, the current one unlinked."""
    links = " · ".join(f'<span aria-current="page">{t}</span>' if p == here else f'<a href="{base}{p}">{t}</a>' for p, t in SECTIONS)
    return f'<nav class="cs-more" aria-label="Crypto"><span class="cs-more__k">In Crypto</span> {links}</nav>'


def pending(site, path, title):
    body = f"""<main id="main" class="page dd fr cs-page"><div class="wrap"><header class="page__head"><h1 class="page__title">{title}</h1>
<p class="note__meta"><span>Data pending</span></p></header><div class="dd__plot dd__plot--pending"><p class="dd__pending">Data pending</p></div>
{more(site, path, "../../")}</div></main>"""
    return site.shell(title=f"{title}: Crypto: Andra Markets", desc=f"{title}, in Crypto.", body=body, home="../../", base="../../", path=path)


def load_history(site):
    try:
        h = json.loads((site.ROOT / ".cache" / "crypto" / "btc.json").read_text(encoding="utf-8"))
        return h if len(h.get("p") or []) > 1000 else None
    except (OSError, ValueError):
        return None


def day_name(iso):
    d = dt.date.fromisoformat(iso[:10])
    return f"{d.day} {MON[d.month - 1]} {d.year}"


def kpis(rows):
    return "".join(f'<li class="kpi__item"><span class="kpi__name">{n}</span><span class="kpi__level">{lv}</span><span class="kpi__chg">{note}</span></li>' for n, lv, note in rows)


def signed(v, d=1):
    n = round(v, d)
    return ("+" if n > 0 else MINUS if n < 0 else "") + f"{abs(n):.{d}f}"


def prices_page(site, d, when):
    """Prices (crypto/prices/; owner-approved sketch, 27 Nov 2026): the Fed & Rates page grid. The market's shares,
    the moves of the thirty largest as a heatmap, every coin with its last seven days, and the Latest panel."""
    coins, total = d["coins"], d["total"]
    btc, eth = coins[0], next((c for c in coins if c["id"] == "ethereum"), coins[1])
    stables = [c for c in coins if c["stable"]]
    others = [c for c in coins if not c["stable"] and c is not btc and c is not eth]
    share = lambda v: v / total * 100 if total else 0
    bars = "".join(f'<div class="mk-row"><span>{n}</span><i><b style="width:{min(100, share(v)):.2f}%"></b></i><span>{share(v):.1f}%</span></div>'
                   for n, v in (("Bitcoin", btc["cap"]), ("Ethereum", eth["cap"]), ("Stablecoins", sum(c["cap"] for c in stables)),
                                (f"The other {len(others)} of the hundred", sum(c["cap"] for c in others))))
    cols = (("day", "Day"), ("week", "Week"), ("month", "Month"), ("year", "Year"))

    def heat_rows(rows):
        big = {k: max([abs(c.get(k) or 0) for c in rows] or [1]) or 1 for k, _ in cols}
        out = []
        for c in rows:
            cells = []
            for k, _ in cols:
                v = c.get(k)
                if v is None:
                    cells.append('<td class="mk-na">n/a</td>')
                    continue
                n, a = round(v, 1), 0.12 + 0.45 * abs(v) / big[k]
                bg = f"rgba(31,210,122,{a:.3f})" if n > 0 else f"rgba(255,75,82,{a:.3f})" if n < 0 else "transparent"
                cells.append(f'<td style="background:{bg}">{signed(v)}%</td>')
            out.append(f'<tr><th scope="row">{site.esc(c["name"])} <span class="cs-sym">{site.esc(c["symbol"])}</span></th>{"".join(cells)}</tr>')
        return "".join(out)
    heads = "".join(f'<th scope="col">{t}</th>' for _, t in cols)
    heat = (f'<div class="cs-scroll" data-view="free"><table class="mk-heat"><thead><tr><th scope="col">Coin</th>{heads}</tr></thead><tbody>{heat_rows([c for c in coins if not c["stable"]][:30])}</tbody></table></div>'
            f'<div class="cs-scroll" data-view="all" hidden><table class="mk-heat"><thead><tr><th scope="col">Coin</th>{heads}</tr></thead><tbody>{heat_rows(coins[:30])}</tbody></table></div>')
    trs = "".join(
        f'<tr id="c-{site.esc(c["id"])}"><td class="cs-rank">{i + 1}</td><th scope="row"><span class="cs-name">{site.esc(c["name"])}</span> <span class="cs-sym">{site.esc(c["symbol"])}</span>'
        f'{"<span class=cs-peg>pegged</span>" if c["stable"] else ""}</th><td class="cs-price">{money(c["price"])}</td><td class="cs-day">{move(c["day"])}</td><td class="cs-week">{move(c["week"])}</td>'
        f'<td class="mk-sp"><canvas data-sp="{",".join(str(x) for x in c.get("spark") or [])}" aria-hidden="true"></canvas></td><td class="cs-cap">{big(c["cap"])}</td></tr>'
        for i, c in enumerate(coins))
    free = [c for c in coins if not c["stable"] and c.get("day") is not None]
    up, down = sum(1 for c in free if round(c["day"], 1) > 0), sum(1 for c in free if round(c["day"], 1) < 0)
    hi, lo = max(free, key=lambda c: c["day"]), min(free, key=lambda c: c["day"])
    side = kpis((("Whole market", big(total), "every listed coin"), ("Bitcoin's share", f"{share(btc['cap']):.1f}%", big(btc["cap"])),
                 ("Ethereum's share", f"{share(eth['cap']):.1f}%", big(eth["cap"])), ("Stablecoins", f"{share(sum(c['cap'] for c in stables)):.1f}%", big(sum(c["cap"] for c in stables))),
                 ("Rose today", f"{up} of {len(free)}", "not counting stablecoins"), ("Fell today", f"{down} of {len(free)}", "not counting stablecoins"),
                 ("Largest rise", site.esc(hi["name"]), move(hi["day"])), ("Largest fall", site.esc(lo["name"]), move(lo["day"]))))
    body = f"""<main id="main" class="page dd fr cs-page">
  <div class="wrap dd__grid">
    <header class="page__head dd__head">
      <h1 class="page__title">Prices</h1>
      <p class="lede">The hundred largest coins: what they are worth and how they moved.</p>
      <p class="note__meta"><span>CoinGecko</span><span>Updated {when}</span><span>Refreshed at every deploy</span></p>
    </header>
    <div class="dd__main fr__main">
      <section class="fr__panel" aria-labelledby="mk-market-h"><div class="fr__ph"><h2 id="mk-market-h">The market</h2></div><p class="fr__intro">The whole crypto market, {big(total)}, and who holds what share of it.</p>
        <div class="mk-bars">{bars}</div><p class="fr__src">CoinGecko, {when}: the market value of every coin it lists. Stablecoins are coins held to a currency (or to gold).</p></section>
      <section class="fr__panel mk-moves" aria-labelledby="mk-moves-h"><div class="fr__ph"><h2 id="mk-moves-h">Moves</h2></div><p class="fr__intro">The thirty largest coins over a day, a week, a month and a year. The deeper the tint, the larger the move against the others in its column.</p>
        <div class="dd__ctl" hidden><div class="dd__cgroup"><span class="cl__glabel" id="mk-show-l">Show</span><div class="filters dd__ranges" role="group" aria-labelledby="mk-show-l"><button type="button" class="chip" data-show="free" aria-pressed="true">Without stablecoins</button><button type="button" class="chip" data-show="all" aria-pressed="false">All</button></div></div></div>
        {heat}<p class="fr__src">CoinGecko, {when}. A day is the last 24 hours; a month 30 days; a year 365.</p></section>
      <section class="fr__panel" id="every-coin" aria-labelledby="mk-all-h"><div class="fr__ph"><h2 id="mk-all-h">Every coin</h2></div><p class="fr__intro">The hundred largest by market value. Wrapped, staked and bridged tokens are left out: each is another coin under a wrapper. "Pegged" marks a coin held to a currency or to gold.</p>
        <div class="cs-scroll"><table class="cs-tab"><thead><tr><th scope="col"><span class="visually-hidden">Rank</span></th><th scope="col">Coin</th><th scope="col">Price</th><th scope="col">Day</th><th scope="col">Week</th><th scope="col" class="mk-sp">Last seven days</th><th scope="col">Market value</th></tr></thead><tbody>{trs}</tbody></table></div>
        <p class="fr__src">CoinGecko, {when}. Prices and changes in US dollars. The seven-day line is drawn on each coin's own scale. For information only. Not investment advice.</p></section>
      {more(site, "crypto/prices/", "../../")}
    </div>
    <aside class="report__side dd__side" aria-labelledby="side-title"><h2 class="report__side-title" id="side-title">Latest</h2><ul class="kpi">{side}</ul><p class="report__src">CoinGecko, {when}.</p></aside>
  </div>
</main>"""
    return site.shell(title="Prices: Crypto: Andra Markets", desc=f"The hundred largest coins by market value, with their moves over a day, a week, a month and a year. Bitcoin at {money(btc['price'])}.",
                      body=body, home="../../", base="../../", path="crypto/prices/", scripts=("crypto-prices.js",))


def bitcoin_page(site, d, h):
    """Bitcoin (crypto/bitcoin/; owner-approved sketch, 27 Nov 2026, in dollars by default after the owner's note that
    a ratio scale hid its course): the price since 2010, how far below its record, the four cycles from each halving,
    every great fall, and the Latest panel. The figures are in the page as JSON; assets/crypto-bitcoin.js draws them."""
    if not h:
        return pending(site, "crypto/bitcoin/", "Bitcoin")
    p, start = h["p"], dt.date.fromisoformat(h["start"])
    date = lambda i: (start + dt.timedelta(days=i)).isoformat()
    falls, pk, tr, in_fall = [], 0, 0, False
    for i in range(1, len(p)):
        if p[i] >= p[pk]:
            if in_fall and p[tr] / p[pk] - 1 < -0.7:
                falls.append((pk, tr, p[tr] / p[pk] - 1, i))
            in_fall, pk, tr = False, i, i
        else:
            in_fall = True
            if p[i] < p[tr]:
                tr = i
    open_fall = (pk, tr, p[tr] / p[pk] - 1, None) if in_fall and p[tr] / p[pk] - 1 < -0.3 else None
    rows = "".join(
        f'<tr><th scope="row">{day_name(date(a))}</th><td>{money(p[a])}</td><td>{day_name(date(b))}</td><td>{money(p[b])}</td>'
        f'<td><span class="down">{MINUS}{abs(f) * 100:.0f}%</span></td><td>{b - a:,}</td><td>{f"{back - a:,}" if back else "Not yet"}</td></tr>'
        for a, b, f, back in falls + ([open_fall] if open_fall else []))
    btc = d["coins"][0]
    rec_i = max(range(len(p)), key=lambda i: p[i])
    try:
        fetched = dt.datetime.fromisoformat(d["asof"].replace("Z", "+00:00"))
        when, today = f"{fetched.day} {fetched:%b %Y}, {fetched:%H:%M} UTC", fetched.date()
    except ValueError:
        when, today = "", dt.date.today()
    height = h.get("height")
    last_h = max((x for x in HALVINGS if x[0] <= today.isoformat()), default=HALVINGS[-1])
    nxt = (last_h[1] + 210000) if height else None
    next_note, next_level = "", "n/a"
    if height and nxt:
        left = nxt - height
        eta = today + dt.timedelta(minutes=10 * left)
        next_level, next_note = f"{MON[eta.month - 1]} {eta.year}", f"in about {left:,} blocks, at ten minutes a block"
    from_rec = btc["price"] / p[rec_i] - 1
    side = kpis((("Price", money(btc["price"]), f"{move(btc['day'])} in 24 hours"), ("Week", move(btc["week"]), f"Year {move(btc.get('year'))}"),
                 ("Record close", money(p[rec_i]), day_name(date(rec_i))), ("From the record", move(from_rec * 100), "today"),
                 ("Market value", big(btc["cap"]), f"{d['btc_share']:.1f}% of all crypto"), ("Last halving", day_name(last_h[0]), f"{(today - dt.date.fromisoformat(last_h[0])).days:,} days ago"),
                 ("Next halving", next_level, next_note or "block height pending"), ("Block height", f"{height:,}" if height else "n/a", "mempool.space")))
    data = {"start": h["start"], "p": p, "now": [today.isoformat(), btc["price"]], "halvings": [x[0] for x in HALVINGS]}
    hist_when = day_name(h["last"])
    body = f"""<main id="main" class="page dd fr cs-page">
  <div class="wrap dd__grid">
    <header class="page__head dd__head">
      <h1 class="page__title">Bitcoin</h1>
      <p class="lede">The price since 2010, its four halvings and every great fall.</p>
      <p class="note__meta"><span>Coin Metrics, CoinGecko, mempool.space</span><span>Updated {when}</span><span>Refreshed at every deploy</span></p>
    </header>
    <div class="dd__main fr__main btc">
      <div class="fr__range dd__ctl" hidden><div class="dd__cgroup"><span class="cl__glabel" id="btc-range-l">Range</span>
        <div class="filters dd__ranges" role="group" aria-labelledby="btc-range-l">{"".join(f'<button type="button" class="chip" data-range="{r}" aria-pressed="{"true" if r == "Max" else "false"}">{r}</button>' for r in ("1M", "3M", "1Y", "4Y", "Max"))}</div></div>
        <div class="dd__cgroup"><span class="cl__glabel" id="btc-scale-l">Scale</span><div class="filters dd__ranges" role="group" aria-labelledby="btc-scale-l"><button type="button" class="chip" data-scale="lin" aria-pressed="true">Dollars</button><button type="button" class="chip" data-scale="log" aria-pressed="false">Log</button></div></div></div>
      <section class="fr__panel" aria-labelledby="btc-price-h"><div class="fr__ph"><h2 id="btc-price-h">Price</h2></div><p class="fr__intro">Bitcoin in US dollars, every day since July 2010. Dashed lines: the four halvings, when the reward for mining a block was cut in half. Log shows each step up as ten times the last, so the early years can be read.</p>
        <div class="btc__plot" data-chart="price"><noscript><p class="dd__pending">The chart needs JavaScript. The great falls are in the table below.</p></noscript></div><p class="lens-read btc__read" aria-live="polite"></p>
        <p class="fr__src">Coin Metrics Community Data (PriceUSD, CC BY-NC 4.0), daily closes to {hist_when}; CoinGecko for today. Halvings at blocks 210,000, 420,000, 630,000 and 840,000.</p></section>
      <section class="fr__panel" aria-labelledby="btc-dd-h"><div class="fr__ph"><h2 id="btc-dd-h">Below the record</h2></div><p class="fr__intro">How far the price stood under its highest close so far, each day. Every fall of more than 70% is named.</p>
        <div class="btc__plot" data-chart="dd"></div><p class="lens-read btc__read" aria-live="polite"></p><p class="fr__src">Andra Markets calculation from Coin Metrics.</p></section>
      <section class="fr__panel" aria-labelledby="btc-cy-h"><div class="fr__ph"><h2 id="btc-cy-h">The four cycles</h2></div><p class="fr__intro">The price from each halving, as a multiple of where it stood that day, over the four years that followed.</p>
        <div class="btc__plot" data-chart="cycles"></div><p class="lens-read btc__read" aria-live="polite"></p><p class="fr__src">Andra Markets calculation from Coin Metrics.</p></section>
      <section class="fr__panel" aria-labelledby="btc-falls-h"><div class="fr__ph"><h2 id="btc-falls-h">Every great fall</h2></div><p class="fr__intro">From a record close to the lowest close before the next record: every fall of more than 70%, and the one under way.</p>
        <div class="cs-scroll"><table class="cs-tab btc-falls"><thead><tr><th scope="col">Record</th><th scope="col">Its close</th><th scope="col">Low</th><th scope="col">Its close</th><th scope="col">Fall</th><th scope="col">Days to the low</th><th scope="col">Days back to the record</th></tr></thead><tbody>{rows}</tbody></table></div>
        <p class="fr__src">Andra Markets calculation from Coin Metrics, daily closes. The record here is a closing price; CoinGecko's record, {money(btc.get("ath") or 0)} on {day_name(btc["ath_date"]) if btc.get("ath_date") else "n/a"}, is the highest trade within a day.</p></section>
      {more(site, "crypto/bitcoin/", "../../")}
      <script type="application/json" id="btc-data">{json.dumps(data, separators=(",", ":"))}</script>
    </div>
    <aside class="report__side dd__side" aria-labelledby="side-title"><h2 class="report__side-title" id="side-title">Latest</h2><ul class="kpi">{side}</ul><p class="report__src">CoinGecko, {when}; mempool.space for the block height.</p></aside>
  </div>
</main>"""
    return site.shell(title="Bitcoin: Crypto: Andra Markets", desc=f"Bitcoin at {money(btc['price'])}: its price every day since 2010, how far below its record it stands, its four halving cycles and every great fall.",
                      body=body, home="../../", base="../../", path="crypto/bitcoin/", scripts=("crypto-bitcoin.js",))
