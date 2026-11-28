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
        for path, title in ((TRADES, "Where it trades"), ("crypto/prices/", "Prices"), ("crypto/bitcoin/", "Bitcoin"), ("crypto/derivatives/", "Derivatives"), ("crypto/network/", "Network"), ("crypto/stablecoins/", "Stablecoins &amp; DeFi")):
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
      <p class="visually-hidden cg__read">The Earth as lit at {ex_when} · each column, a country where exchanges are registered, as tall as its share of the day's trading</p>
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
      <h1 class="page__title">Where it trades</h1>
      <p class="lede">{LEDE}</p>
      <p class="note__meta"><span>The whole market {big(d["total"])}</span><span>Bitcoin {d["btc_share"]:.1f}% of it</span><span>Data from CoinGecko, {when}</span></p>
    </header>
    {globe}{seats}
    {more(site, TRADES, "../../")}
  </div>
</main>"""
    out = {TRADES: site.shell(
        title="Where crypto trades: Andra Markets",
        desc="Where the day's crypto trading is registered, country by country, on the real Earth.",
        body=body, home="../../", base="../../", path=TRADES, scripts=("crypto-globe.js",) if places else ())}
    nw = load_network(site)
    out["crypto/"] = landing(site, d, when, data if places else None, nw)
    out["crypto/prices/"] = prices_page(site, d, when)
    hist = load_history(site)
    out["crypto/bitcoin/"] = bitcoin_page(site, d, hist, markets_parts(site, d, hist, load_markets(site)))
    out["crypto/markets/"] = moved(site, "crypto/markets/", "../bitcoin/#markets", "Bitcoin vs markets")
    try:
        today = dt.datetime.fromisoformat(d["asof"].replace("Z", "+00:00")).date()
    except ValueError:
        today = dt.date.today()
    out.update(coin_pages(site, d, hist, when, today))
    out["crypto/derivatives/"] = derivs_page(site, d, hist, load_derivs(site))
    out["crypto/network/"] = network_page(site, d, nw)
    out["crypto/stablecoins/"] = defi_page(site, d, load_defi(site))
    return out


def moved(site, path, to, title):
    """A page that has moved into another: it sends the reader on at once, and says where."""
    body = f"""<main id="main" class="page cs-page"><div class="wrap"><header class="page__head"><h1 class="page__title">{title}</h1>
<p class="lede"><a href="{to}">{title} is now part of Bitcoin.</a></p></header></div></main>"""
    return site.shell(title=f"{title}: Crypto: Andra Markets", desc=f"{title} is now part of the Bitcoin page.", body=body, home="../../", base="../../", path=path,
                      head=f'\n<meta http-equiv="refresh" content="0; url={to}">', index=False)


def net_layer(nw):
    """The Network page's lights, as a layer the landing's globe can put on."""
    return {"points": nw["points"], "places": [
        {"name": p["name"], "lon": p["lon"], "lat": p["lat"], "share": p["share"] / 100, "label": f"{p['count']:,} nodes · {p['share']:.0f}%", "more": f"{p['btc']:,.0f} BTC in channels"} for p in nw["places"]]}


def landing(site, d, when, trade, nw):
    """The group's front: the Earth in the middle, the seven sections either side of it, by name alone (owner, 28 Nov 2026)."""
    layers = {}
    if trade:
        layers["trade"] = {"places": trade["places"]}
    if nw:
        layers["net"] = net_layer(nw)
    own = {TRADES: "trade", "crypto/network/": "net"}
    items = "".join(f'<li><a href="../{p}" data-layer="{own.get(p, "") if own.get(p) in layers else ""}">{t}</a></li>' for p, t in SECTIONS)
    data = {"asof": d.get("asof"), "layers": layers}
    body = f"""<main id="main" class="page cs-page chp">
  <div class="wrap">
    <section class="ch">
      <h1 class="page__title">Crypto</h1>
      <p class="visually-hidden">Where the coins trade, what they are worth and how their networks run.</p>
      <div class="cg ch__globe" hidden>
        <canvas class="cg__gl" aria-hidden="true"></canvas>
        <canvas class="cg__ov" aria-hidden="true"></canvas>
        <div class="cg__names" aria-hidden="true"></div>
        <p class="visually-hidden cg__status" role="status" aria-live="polite"></p>
        <script type="application/json">{json.dumps(data, separators=(",", ":")).replace("</", "<\\/")}</script>
      </div>
      <nav aria-label="The sections of Crypto"><ol class="ch__list">{items}</ol></nav>
    </section>
    <p class="report__src ch__src">CoinGecko, Coin Metrics, Deribit, mempool.space and DefiLlama, {when}. The Earth: Solar System Scope (CC BY 4.0), from NASA imagery.</p>
  </div>
</main>"""
    return site.shell(title="Crypto: Andra Markets", desc="Where the coins trade, what they are worth and how their networks run.",
                      body=body, home="../", base="../", path="crypto/", scripts=("crypto-globe.js",))


# ---- the other sections ------------------------------------------------------------------------------------------
TRADES = "crypto/exchanges/"
SECTIONS = ((TRADES, "Where it trades"), ("crypto/prices/", "Prices"), ("crypto/bitcoin/", "Bitcoin"), ("crypto/derivatives/", "Derivatives"), ("crypto/network/", "Network"), ("crypto/stablecoins/", "Stablecoins &amp; DeFi"))
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
            out.append(f'<tr><th scope="row"><a href="../../{coin_path(c)}">{site.esc(c["name"])}</a> <span class="cs-sym">{site.esc(c["symbol"])}</span></th>{"".join(cells)}</tr>')
        return "".join(out)
    heads = "".join(f'<th scope="col">{t}</th>' for _, t in cols)
    heat = (f'<div class="cs-scroll" data-view="free"><table class="mk-heat"><thead><tr><th scope="col">Coin</th>{heads}</tr></thead><tbody>{heat_rows([c for c in coins if not c["stable"]][:30])}</tbody></table></div>'
            f'<div class="cs-scroll" data-view="all" hidden><table class="mk-heat"><thead><tr><th scope="col">Coin</th>{heads}</tr></thead><tbody>{heat_rows(coins[:30])}</tbody></table></div>')
    trs = "".join(
        f'<tr id="c-{site.esc(c["id"])}"><td class="cs-rank">{i + 1}</td><th scope="row"><a class="cs-name" href="../../{coin_path(c)}">{site.esc(c["name"])}</a> <span class="cs-sym">{site.esc(c["symbol"])}</span>'
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


def bitcoin_page(site, d, h, mk=None):
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
                 ("Next halving", next_level, next_note or "block height pending"), ("Block height", f"{height:,}" if height else "n/a", "mempool.space")) + (mk["side"] if mk else ()))
    data = {"start": h["start"], "p": p, "now": [today.isoformat(), btc["price"]], "halvings": [x[0] for x in HALVINGS]}
    hist_when = day_name(h["last"])
    body = f"""<main id="main" class="page dd fr cs-page{" vm" if mk else ""}">
  <div class="wrap dd__grid">
    <header class="page__head dd__head">
      <h1 class="page__title">Bitcoin</h1>
      <p class="lede">{"The price since 2010, its halvings and great falls, and how it has done beside shares, gold, the dollar and bonds." if mk else "The price since 2010, its four halvings and every great fall."}</p>
      <p class="note__meta"><span>Coin Metrics, CoinGecko, mempool.space{", Yahoo Finance" if mk else ""}</span><span>Updated {when}</span><span>Refreshed at every deploy</span></p>
{mk["race"] if mk else ""}    </header>
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
{('<h2 class="cs-h btc-vs" id="markets">Beside the markets</h2>' + chr(10) + mk["panels"] + mk["script"]) if mk else ""}      {more(site, "crypto/bitcoin/", "../../")}
      <script type="application/json" id="btc-data">{json.dumps(data, separators=(",", ":"))}</script>
    </div>
    <aside class="report__side dd__side" aria-labelledby="side-title"><h2 class="report__side-title" id="side-title">Latest</h2><ul class="kpi">{side}</ul><p class="report__src">CoinGecko, {when}; mempool.space for the block height.</p></aside>
  </div>
</main>"""
    return site.shell(title="Bitcoin: Crypto: Andra Markets", desc=f"Bitcoin at {money(btc['price'])}: its price every day since 2010, how far below its record it stands, its four halving cycles and every great fall.",
                      body=body, home="../../", base="../../", path="crypto/bitcoin/", scripts=("crypto-bitcoin.js",) + (("crypto-markets.js",) if mk else ()))


# ---- a page for each coin (owner, 27 Nov 2026: "analyse each coin, as in Companies"; sketch with Ethereum approved) ----
FALL_CUT = 0.5   # a coin's great falls: every fall of more than half from a record close
NET_METRICS = ("AdrActCnt", "TxCnt", "SplyCur")
INVEST = (("A year ago", 365), ("3 years ago", 1095), ("5 years ago", 1826))


def coin_path(c):
    return "crypto/bitcoin/" if c["id"] == "bitcoin" else f"crypto/{c['id']}/"


def load_coin(site, cid):
    try:
        r = json.loads((site.ROOT / ".cache" / "crypto" / "coins" / f"{cid}.json").read_text(encoding="utf-8"))
        return r if len(r.get("p") or []) > 60 else None
    except (OSError, ValueError):
        return None


def coin_logo(site, cid):
    found = sorted((site.ROOT / ".cache" / "crypto" / "logos").glob(f"{cid}.*")) if (site.ROOT / ".cache" / "crypto" / "logos").exists() else []
    return found[0] if found else None


def series_now(rec, price, today):
    """The daily closes, carried to today with CoinGecko's price when today is past the last close."""
    p, start = list(rec["p"]), dt.date.fromisoformat(rec["start"])
    last = start + dt.timedelta(days=len(p) - 1)
    if price and today > last:
        p += [p[-1]] * ((today - last).days - 1) + [price]
    return start, p


def at_date(start, p, d):
    i = (d - start).days
    return p[i] if 0 <= i < len(p) else None


def vol_year(p, n=365):
    """Annualised volatility of the last n daily moves, in percent."""
    import math
    r = [math.log(p[i] / p[i - 1]) for i in range(max(1, len(p) - n), len(p)) if p[i] > 0 and p[i - 1] > 0]
    if len(r) < 30:
        return None
    m = sum(r) / len(r)
    return (sum((x - m) ** 2 for x in r) / (len(r) - 1)) ** 0.5 * math.sqrt(365) * 100


def great_falls(p, cut):
    falls, pk, tr, in_fall = [], 0, 0, False
    for i in range(1, len(p)):
        if p[i] >= p[pk]:
            if in_fall and p[tr] / p[pk] - 1 < -cut:
                falls.append((pk, tr, p[tr] / p[pk] - 1, i))
            in_fall, pk, tr = False, i, i
        else:
            in_fall = True
            if p[i] < p[tr]:
                tr = i
    if in_fall and p[tr] / p[pk] - 1 < -0.3:
        falls.append((pk, tr, p[tr] / p[pk] - 1, None))
    return falls


def mult_or_pct(v):
    """A change in percent, or as a multiple once it passes ten times."""
    if v is None:
        return '<span class="cs-none">n/a</span>'
    if v >= 900:
        return f'<span class="up">&times;{v / 100 + 1:,.0f}</span>'
    return move(v)


def coin_pages(site, d, btc_hist, when, today):
    coins, total = d["coins"], d["total"]
    b_start, bp = (series_now(btc_hist, coins[0]["price"], today) if btc_hist else (None, None))
    recs = {c["id"]: load_coin(site, c["id"]) for c in coins if c["id"] != "bitcoin"}
    # the measures every page compares its coin with, over the hundred
    def vol_of(c):
        if c["id"] == "bitcoin":
            return vol_year(bp) if bp else None
        r = recs.get(c["id"])
        return vol_year(r["p"]) if r else None
    meas = (("year", "Change over a year", True, lambda c: c.get("year")),
            ("fromAth", "Below its record", True, lambda c: (c["price"] / c["ath"] - 1) * 100 if c.get("ath") else None),
            ("vol", "Volatility, a year", False, vol_of),
            ("turn", "Turnover, a day", False, lambda c: c["volume"] / c["cap"] * 100 if c.get("volume") and c.get("cap") else None),
            ("issued", "Supply issued", False, lambda c: c["circ"] / c["max_supply"] * 100 if c.get("circ") and c.get("max_supply") else None))
    vals = {k: [f(c) for c in coins] for k, _, _, f in meas}
    btc = coins[0]
    out = {}
    for rank, c in enumerate(coins, 1):
        if c["id"] == "bitcoin":
            continue
        rec = recs.get(c["id"])
        path = coin_path(c)
        name, sym = site.esc(c["name"]), site.esc(c["symbol"])
        share = c["cap"] / total * 100 if total else 0
        if not rec:
            body = f"""<main id="main" class="page dd co cs-page"><div class="wrap"><header class="page__head"><p class="dd__crumbs"><a href="../">Crypto</a> <span aria-hidden="true">/</span> <a href="../prices/">Prices</a></p>
<h1 class="page__title">{name}</h1><p class="note__meta"><span>{sym}</span><span>{money(c["price"])}</span><span>History pending</span></p></header>{more(site, path, "../../")}</div></main>"""
            out[path] = site.shell(title=f"{c['name']}: Crypto: Andra Markets", desc=f"{c['name']} ({c['symbol']}), number {rank} by market value.", body=body, home="../../", base="../../", path=path)
            continue
        start, p = series_now(rec, c["price"], today)
        n = len(p)
        date = lambda i: (start + dt.timedelta(days=i))
        rec_i = max(range(n), key=lambda i: p[i])
        falls = great_falls(p, FALL_CUT)
        since = f"{MON[start.month - 1]} {start.year}"
        full = rec["source"] == "Coin Metrics"
        # head and key figures
        chg = c.get("change")
        quote = (f'<span class="co-px">{money(c["price"])}</span><span class="co-chg">'
                 + (f'<span class="{"up" if round(c["day"], 1) > 0 else "down" if round(c["day"], 1) < 0 else ""}">{"+" if chg > 0 else MINUS if chg < 0 else ""}{money(abs(chg))}</span> ({move(c["day"])})' if chg is not None and c.get("day") is not None else move(c.get("day")))
                 + f' in 24 hours</span><span class="note__meta">{sym}. Number {rank} by market value. {when}.</span>')
        below = (c["price"] / p[rec_i] - 1) * 100
        ordinal = {2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth"}.get(rank)
        lede = (f"The {ordinal + ' largest coin' if ordinal else f'number {rank} coin by market value'}, {share:.1f}% of all crypto."
                + (" Held to a currency or to gold, so its price is meant not to move." if c["stable"] else
                   f" Its record close was {money(p[rec_i])} on {day_name(date(rec_i).isoformat())}" + (f", and it now stands {abs(below):.0f}% below it." if below < -1 else ", and it is near it now.")
                   + (f" Over a year it is {'down' if c['year'] < 0 else 'up'} {abs(c['year']):.0f}%." if c.get("year") is not None else "")))
        fdv = c.get("fdv") or c["cap"]
        side = kpis((("Market value", big(c["cap"]), f"{share:.1f}% of all crypto"),
                     ("If every coin existed", big(fdv), "at the maximum supply" if c.get("max_supply") else "no maximum: the coins there are"),
                     ("Traded in 24 hours", big(c["volume"]) if c.get("volume") else "n/a", f"{c['volume'] / c['cap'] * 100:.1f}% of its value" if c.get("volume") else ""),
                     ("In circulation", f"{c['circ'] / 1e9:,.2f}bn" if (c.get("circ") or 0) >= 1e9 else f"{(c.get('circ') or 0) / 1e6:,.1f}m", (f"of {c['max_supply'] / 1e9:,.2f}bn at most" if c["max_supply"] >= 1e9 else f"of {c['max_supply'] / 1e6:,.1f}m at most") if c.get("max_supply") else "no maximum set"),
                     ("Week", move(c.get("week")), f"Month {move(c.get('month'))}"), ("Year", move(c.get("year")), f"24 hours {move(c.get('day'))}"),
                     ("Record", money(c["ath"]) if c.get("ath") else "n/a", f"{day_name(c['ath_date'])}, within a day" if c.get("ath_date") else ""),
                     ("Lowest ever", money(c["atl"]) if c.get("atl") else "n/a", day_name(c["atl_date"]) if c.get("atl_date") else "")))
        logo = coin_logo(site, c["id"])
        logo_html = f'<span class="co-logo"><img src="logo{logo.suffix}" alt="{name} logo" width="200" height="200"></span>' if logo else ""
        # returns
        def ret_from(d0, series, s0):
            a = at_date(s0, series, d0)
            return (series[-1] / a - 1) * 100 if a else None
        periods = [("24 hours", today - dt.timedelta(days=1)), ("Week", today - dt.timedelta(days=7)), ("Month", today - dt.timedelta(days=30)), ("3 months", today - dt.timedelta(days=91)),
                   ("This year", dt.date(today.year, 1, 1) - dt.timedelta(days=1)), ("Year", today - dt.timedelta(days=365)), ("3 years", today - dt.timedelta(days=1095)), ("5 years", today - dt.timedelta(days=1826)), (f"Since {since}", start)]
        ret_rows = "".join(f'<tr><th scope="row">{lab}</th><td>{mult_or_pct(ret_from(d0, p, start))}</td><td>{mult_or_pct(ret_from(d0, bp, b_start)) if bp else "n/a"}</td></tr>'
                           for lab, d0 in periods if d0 >= start)
        # months and years
        month_end = {}
        for i in range(n):
            dd = date(i)
            month_end[(dd.year, dd.month)] = p[i]
        keys = sorted(month_end)
        mret = {k: (month_end[k] / month_end[keys[j - 1]] - 1) * 100 for j, k in enumerate(keys) if j}
        bigm = max([min(100, abs(v)) for v in mret.values()] or [1]) or 1
        cal = "<thead><tr><th></th>" + "".join(f'<th scope="col">{m}</th>' for m in MON) + '<th scope="col">Year</th></tr></thead><tbody>'
        for y in range(keys[-1][0], keys[0][0] - 1, -1):
            cells = []
            for m in range(1, 13):
                v = mret.get((y, m))
                if v is None:
                    cells.append("<td></td>")
                    continue
                r1, a = round(v), 0.12 + 0.5 * min(1, abs(v) / bigm)
                bg = f"rgba(31,210,122,{a:.3f})" if r1 > 0 else f"rgba(255,75,82,{a:.3f})" if r1 < 0 else "transparent"
                cells.append(f'<td style="background:{bg}">{signed(v, 0)}%</td>')
            ys = month_end.get((y - 1, 12)) or month_end[keys[0]]
            ye = month_end.get((y, 12)) or month_end[keys[-1]]
            yv = (ye / ys - 1) * 100
            cal += f'<tr><th scope="row">{y}</th>{"".join(cells)}<td class="yr">{mult_or_pct(yv) if yv >= 900 else move(yv)}</td></tr>'
        cal += "</tbody>"
        # falls, biggest days, daily moves, $1,000
        fall_rows = "".join(f'<tr><th scope="row">{day_name(date(a).isoformat())}</th><td>{money(p[a])}</td><td>{day_name(date(b).isoformat())}</td><td>{money(p[b])}</td>'
                            f'<td><span class="down">{MINUS}{abs(f) * 100:.0f}%</span></td><td>{b - a:,}</td><td>{f"{back - a:,}" if back else "Not yet"}</td></tr>' for a, b, f, back in falls)
        dm = [((date(i)), (p[i] / p[i - 1] - 1) * 100) for i in range(1, n) if p[i - 1] > 0]
        srt = sorted(dm, key=lambda x: x[1])
        best = "".join(f'<li><span>{day_name(x[0].isoformat())}</span>{move(x[1])}</li>' for x in reversed(srt[-5:]))
        worst = "".join(f'<li><span>{day_name(x[0].isoformat())}</span>{move(x[1])}</li>' for x in srt[:5])
        bins = [0] * 31
        for _, v in dm:
            bins[max(-15, min(15, int(v // 1))) + 15] += 1
        ups = sum(1 for _, v in dm if round(v, 1) > 0)
        tens = sum(1 for _, v in dm if abs(v) >= 10)
        inv_rows = ""
        for lab, days in INVEST + ((f"The start, {since}", n - 1),):
            if days > n - 1:
                continue
            i0 = n - 1 - days
            lump = 1000 * p[-1] / p[i0]
            months = max(1, round(days / 30.44))
            coins_n = sum((1000 / months) / p[min(n - 1, i0 + round(m * 30.44))] for m in range(months))
            drip = coins_n * p[-1]
            inv_rows += f'<tr><th scope="row">{lab}</th><td>${lump:,.0f}</td><td>{mult_or_pct((lump / 1000 - 1) * 100)}</td><td>${drip:,.0f}</td><td>{mult_or_pct((drip / 1000 - 1) * 100)}</td></tr>'
        # where it trades
        tick_html = ""
        if rec.get("tickers"):
            by = {}
            for t in rec["tickers"]:
                e = by.setdefault(t["ex"], {"vol": 0.0, "pair": t["pair"], "top": 0.0})
                e["vol"] += t["vol"]
                if t["vol"] > e["top"]:
                    e["top"], e["pair"] = t["vol"], t["pair"]
            exs = sorted(by.items(), key=lambda kv: -kv[1]["vol"])
            tot = sum(e["vol"] for _, e in exs) or 1
            rows = "".join(f'<tr><th scope="row">{site.esc(k)}</th><td>{site.esc(e["pair"])}</td><td>{big(e["vol"])}</td><td>{e["vol"] / tot * 100:.1f}%</td></tr>' for k, e in exs[:10])
            tick_html = f"""
      <section aria-labelledby="ct-h"><h2 id="ct-h">Where it trades</h2><p>The exchanges where the most {name} changed hands in the last 24 hours, as each reports it.</p>
        <div class="cs-scroll"><table class="cs-tab"><thead><tr><th scope="col">Exchange</th><th scope="col">Main pair</th><th scope="col">Traded</th><th scope="col">Share</th></tr></thead><tbody>{rows}</tbody></table></div>
        <p class="co-src">CoinGecko, {when}. Volumes as the exchanges report them; some are known to count generously.</p></section>"""
        # charts drawn in the browser
        step = 3 if n > 900 else 1
        def ser(vs):
            return [None if v is None else float(f"{v:.4g}") for v in vs[::step]]
        charts = {}
        if bp:
            ratio = [p[i] / at_date(b_start, bp, date(i)) if at_date(b_start, bp, date(i)) else None for i in range(n)]
            charts["vsbtc"] = {"t0": start.isoformat(), "step": step, "fmt": "btc", "y0": 0, "s": [{"v": ser(ratio), "label": "now"}]}
            import math
            re_ = [math.log(p[i] / p[i - 1]) if p[i - 1] > 0 and p[i] > 0 else 0 for i in range(1, n)]
            rb_ = []
            for i in range(1, n):
                b1, b0 = at_date(b_start, bp, date(i)), at_date(b_start, bp, date(i - 1))
                rb_.append(math.log(b1 / b0) if b1 and b0 else 0)
            def corr(a, b):
                k = len(a); ma, mb = sum(a) / k, sum(b) / k
                sab = sum((x - ma) * (y - mb) for x, y in zip(a, b)); sa = sum((x - ma) ** 2 for x in a); sb = sum((y - mb) ** 2 for y in b)
                return sab / (sa * sb) ** 0.5 if sa > 0 and sb > 0 else None
            def vol30(r, i):
                s = r[i - 30:i]; m = sum(s) / 30
                return (sum((x - m) ** 2 for x in s) / 29) ** 0.5 * math.sqrt(365) * 100
            cs, ve, vb = [None] * n, [None] * n, [None] * n
            for i in range(31 + (-31) % step, n, step):   # on the same days the chart keeps
                if i >= 91:
                    cs[i] = corr(re_[i - 91:i - 1], rb_[i - 91:i - 1])
                ve[i], vb[i] = vol30(re_, i - 1), vol30(rb_, i - 1)
            pick = lambda arr: [None if v is None else float(f"{v:.3g}") for v in arr[::step]]
            charts["corr"] = {"t0": start.isoformat(), "step": step, "fmt": "ratio", "y0": -0.5, "y1": 1, "hl": [0], "s": [{"v": pick(cs), "label": "now"}]}
            charts["vol"] = {"t0": start.isoformat(), "step": step, "fmt": "pct", "y0": 0, "s": [{"v": pick(vb), "label": "Bitcoin", "style": "dash", "alpha": 0.6}, {"v": pick(ve), "label": c["name"]}]}
        net_html = ""
        if rec.get("net"):
            parts = []
            labels = {"AdrActCnt": ("Active addresses", "addresses that sent or received it each day, 30-day average", "k"), "TxCnt": ("Transactions", "a day, 30-day average", "k"), "SplyCur": ("Supply", "coins in existence", "k")}
            for m in NET_METRICS:
                if m not in rec["net"]:
                    continue
                s0, v = rec["net"][m]["start"], rec["net"][m]["v"]
                st = 3 if len(v) > 900 else 1
                if m != "SplyCur":
                    avg, acc = [], 0.0
                    for i, x in enumerate(v):
                        acc += x
                        if i >= 30:
                            acc -= v[i - 30]
                        avg.append(acc / 30 if i >= 29 else None)
                    v = avg
                charts[m] = {"t0": s0, "step": st, "fmt": "k", "y0": 0 if m != "SplyCur" else None, "s": [{"v": [None if x is None else float(f"{x:.4g}") for x in v[::st]], "label": "now"}]}
                parts.append(f'<div class="cc-plot" data-chart="{m}" data-name="{labels[m][0]}"></div><p class="co-read" data-read="{m}"></p>')
            net_html = f"""
      <section aria-labelledby="cn-h"><h2 id="cn-h">Network activity</h2><p>How much the {name} network itself is used: {", ".join(labels[m][0].lower() for m in NET_METRICS if m in rec["net"])}.</p>
        {"".join(parts)}<p class="co-src">Coin Metrics Community Data ({", ".join(m for m in NET_METRICS if m in rec["net"])}), daily.</p></section>"""
        peers = {"me": rank - 1, "m": [{"k": k, "label": lab, "move": mv_, "v": [None if x is None else round(x, 2) for x in vals[k]]} for k, lab, mv_, _ in meas], "names": [x["name"] for x in coins]}
        data = {"name": c["name"], "start": start.isoformat(), "p": p, "now": [today.isoformat(), c["price"]], "halvings": [], "fallCut": FALL_CUT, "charts": charts, "peers": peers, "bins": bins}
        supply = (f'<div class="su"><i><b style="width:{min(100, c["circ"] / c["max_supply"] * 100):.2f}%"></b></i><p>{c["circ"] / c["max_supply"] * 100:.0f}% issued: {c["circ"]:,.0f} of {c["max_supply"]:,.0f} at most. {c["max_supply"] - c["circ"]:,.0f} are still to come.</p></div>'
                  if c.get("circ") and c.get("max_supply") else
                  f'<div class="su"><p>{c.get("circ") or 0:,.0f} {sym} in circulation, with no maximum set: more can be issued. For comparison, Bitcoin has issued {btc["circ"] / 21e6 * 100:.1f}% of its 21 million.</p></div>' if btc.get("circ") else "")
        body = f"""<main id="main" class="page dd co cs-page">
  <div class="wrap dd__grid">
    <header class="page__head dd__head{' co-head--logo' if logo else ''}">
      <p class="dd__crumbs"><a href="../">Crypto</a> <span aria-hidden="true">/</span> <a href="../prices/">Prices</a></p>
      <h1 class="page__title">{name}</h1>{logo_html}
      <p class="co-quote">{quote}</p>
      <p class="lede">{site.esc(lede)}</p>
    </header>
    <aside class="report__side dd__side" aria-labelledby="side-title"><h2 class="report__side-title" id="side-title">Key figures</h2><ul class="kpi">{side}</ul><p class="report__src">CoinGecko, {when}.</p></aside>
    <div class="page__body co__body dd__main btc">
      <section aria-labelledby="cp-h"><h2 id="cp-h">Price</h2><p>{name} in US dollars, every day since {since}{"" if full else ", as far back as CoinGecko gives without a key"}.</p>
        <div class="fr__range dd__ctl" hidden><div class="dd__cgroup"><span class="cl__glabel" id="cr-l">Range</span><div class="filters dd__ranges" role="group" aria-labelledby="cr-l">{"".join(f'<button type="button" class="chip" data-range="{r}" aria-pressed="{"true" if r == "Max" else "false"}">{r}</button>' for r in ("1M", "3M", "1Y", "4Y", "Max"))}</div></div>
        <div class="dd__cgroup"><span class="cl__glabel" id="cs-l">Scale</span><div class="filters dd__ranges" role="group" aria-labelledby="cs-l"><button type="button" class="chip" data-scale="lin" aria-pressed="true">Dollars</button><button type="button" class="chip" data-scale="log" aria-pressed="false">Log</button></div></div></div>
        <div class="btc__plot" data-chart="price"></div><p class="co-read btc__read" aria-live="polite"></p>
        <p class="co-src">{"Coin Metrics Community Data (PriceUSD), daily closes" if full else "CoinGecko, daily prices for the last year"}; CoinGecko for today.</p></section>
      <section aria-labelledby="cr-h"><h2 id="cr-h">Returns</h2><p>What {name} gained or lost over each period, and Bitcoin over the same one.</p>
        <div class="cs-scroll"><table class="cs-tab cc-ret"><thead><tr><th scope="col">Period</th><th scope="col">{name}</th><th scope="col">Bitcoin</th></tr></thead><tbody>{ret_rows}</tbody></table></div><p class="co-src">Daily closes; CoinGecko for today.</p></section>
      <section aria-labelledby="cm-h"><h2 id="cm-h">Months and years</h2><p>Every month since {since}, and each year in full. Green a rise, red a fall, deeper for a larger move.</p>
        <div class="cs-scroll"><table class="cc-cal">{cal}</table></div><p class="co-src">Andra Markets calculation from month-end closes.</p></section>
      <section aria-labelledby="co-h"><h2 id="co-h">Against the others</h2><p>{name} (filled) against the other 99 of the hundred largest coins. The dashed tick is the middle coin. Point at a dot to read it.</p>
        <div class="cc-peers"></div><p class="co-read cc-peers-read" aria-live="polite"></p><p class="co-src">CoinGecko, {when}; volatility from a year of daily closes; turnover is a day's trading as a share of market value.</p></section>
      {"" if not bp else f'''<section aria-labelledby="cb-h"><h2 id="cb-h">Against Bitcoin</h2><p>{name} priced in bitcoin: when the line rises, it is gaining on Bitcoin. Then how closely their daily moves have followed each other over the last 90 days (1 in step, 0 unrelated).</p>
        <div class="cc-plot" data-chart="vsbtc" data-name="Priced in bitcoin"></div><p class="co-read" data-read="vsbtc"></p><div class="cc-plot" data-chart="corr" data-name="Moving with Bitcoin"></div><p class="co-read" data-read="corr"></p><p class="co-src">Andra Markets calculation from daily closes.</p></section>
      <section aria-labelledby="cv-h"><h2 id="cv-h">Volatility</h2><p>How much the price swings: the spread of daily moves over the last 30 days, scaled to a year. Bitcoin dashed for comparison.</p>
        <div class="cc-plot" data-chart="vol" data-name="Volatility"></div><p class="co-read" data-read="vol"></p><p class="co-src">Andra Markets calculation from daily closes.</p></section>'''}
      {net_html}
      <section aria-labelledby="cs-h"><h2 id="cs-h">Supply</h2><p>Coins in circulation against the most there can ever be.</p>{supply}<p class="co-src">CoinGecko, {when}.</p></section>
      {tick_html}
      <section aria-labelledby="cd-h"><h2 id="cd-h">The biggest days</h2><p>The five largest one-day rises and falls since {since}.</p><div class="cc-days"><div><h3>Rises</h3><ol>{best}</ol></div><div><h3>Falls</h3><ol>{worst}</ol></div></div><p class="co-src">Daily closes.</p></section>
      <section aria-labelledby="ch-h"><h2 id="ch-h">Daily moves</h2><p>How often each size of daily move has happened since {since}, in steps of one percent.</p>
        <div class="cc-plot" data-chart="hist" data-name="Daily moves"></div><p class="co-read">{name} rose on {ups / max(1, len(dm)) * 100:.0f}% of days{f"; one day in {round(len(dm) / tens)} it moved 10% or more either way" if tens else "; it never moved 10% in a day"}.</p><p class="co-src">Andra Markets calculation from daily closes.</p></section>
      <section aria-labelledby="ci-h"><h2 id="ci-h">If you had put in $1,000</h2><p>All at once at the start of each period, or the same $1,000 spread over its months in equal parts.</p>
        <div class="cs-scroll"><table class="cs-tab cc-inv"><thead><tr><th scope="col">From</th><th scope="col">At once</th><th scope="col">Change</th><th scope="col">Monthly</th><th scope="col">Change</th></tr></thead><tbody>{inv_rows}</tbody></table></div><p class="co-src">Andra Markets calculation from daily closes, before fees and taxes. Not investment advice.</p></section>
      <section aria-labelledby="cdd-h"><h2 id="cdd-h">Below the record</h2><p>How far the price stood under its highest close so far, each day.</p><div class="btc__plot" data-chart="dd"></div><p class="co-read btc__read" aria-live="polite"></p><p class="co-src">Andra Markets calculation from daily closes.</p></section>
      <section aria-labelledby="cf-h"><h2 id="cf-h">Every great fall</h2><p>From a record close to the lowest close before the next record: every fall of more than half, and one under way.</p>
        <div class="cs-scroll"><table class="cs-tab cc-falls"><thead><tr><th scope="col">Record</th><th scope="col">Close</th><th scope="col">Low</th><th scope="col">Close</th><th scope="col">Fall</th><th scope="col">Days down</th><th scope="col">Days back</th></tr></thead><tbody>{fall_rows or '<tr><td colspan="7">No fall of more than half since ' + since + '.</td></tr>'}</tbody></table></div><p class="co-src">Andra Markets calculation from daily closes.</p></section>
      {more(site, path, "../../")}
      <script type="application/json" id="btc-data">{json.dumps(data, separators=(",", ":"))}</script>
    </div>
  </div>
</main>"""
        out[path] = site.shell(title=f"{c['name']} ({c['symbol']}): Crypto: Andra Markets",
                               desc=f"{c['name']} at {money(c['price'])}, number {rank} by market value: its price since {since}, its returns month by month, against Bitcoin and the other coins, its supply and every great fall.",
                               body=body, home="../../", base="../../", path=path, scripts=("crypto-bitcoin.js", "crypto-coin.js"))
        if logo:
            folder = site.OUT / path
            folder.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copyfile(logo, folder / f"logo{logo.suffix}")
    return out


def search_items(site):
    d = load(site)
    if not d:
        return []
    return [{"g": "Pages", "t": c["name"], "m": f"Crypto, {c['symbol']}", "u": coin_path(c), "k": f"{c['symbol']} {c['name']} crypto coin"} for c in d["coins"]]


# ---- Bitcoin vs markets (crypto/markets/; owner-approved sketches, 27 Nov 2026: the race and the portfolio's control) ----
MK_NAMES = (("BTC", "Bitcoin"), ("SPX", "S&amp;P 500"), ("NDX", "Nasdaq"), ("GOLD", "Gold"), ("DXY", "Dollar index"), ("BOND", "Long Treasuries"))
MK_PERIODS = (("Month", 21), ("Year", 252), ("3 years", 756), ("5 years", 1260), ("10 years", 2520))
MK_SHARES = (0, 0.01, 0.05, 0.10)


def load_markets(site):
    try:
        m = json.loads((site.ROOT / ".cache" / "crypto" / "markets.json").read_text(encoding="utf-8"))
        return m if len((m.get("s") or {}).get("SPX") or {}) > 1000 else None
    except (OSError, ValueError):
        return None


def mk_portfolio(rets, days, w):
    """100 put into 60% shares and 40% bonds, with w of it in Bitcoin, set back to its weights each month."""
    hold = {"SPX": 0.6 * (1 - w), "BOND": 0.4 * (1 - w), "BTC": w}
    cur = {k: v * 100 for k, v in hold.items()}
    out = [100.0]
    for i in range(1, len(days)):
        for k in cur:
            cur[k] *= 1 + rets[k][i]
        tot = sum(cur.values())
        out.append(tot)
        if days[i][5:7] != days[i - 1][5:7]:
            cur = {k: tot * v for k, v in hold.items()}
    return out


def markets_parts(site, d, hist, mk):
    """Bitcoin beside the markets, as the pieces the Bitcoin page takes in (owner, 28 Nov 2026: "merge Bitcoin and
    Bitcoin vs markets"): the race for under the head, the panels, four figures for Latest, and the data."""
    import math
    if not hist or not mk:
        return None
    b0 = dt.date.fromisoformat(hist["start"])
    btc = {(b0 + dt.timedelta(days=i)).isoformat(): v for i, v in enumerate(hist["p"])}
    src = dict(mk["s"], BTC=btc)
    days = [x for x in sorted(src["SPX"]) if x in btc or x > hist["last"]]   # the S&P 500's trading days
    days = [x for x in days if x <= hist["last"]]
    keys = [k for k, _ in MK_NAMES]
    ser = {k: [] for k in keys}
    for x in days:
        for k in keys:
            v = src[k].get(x)
            ser[k].append(v if v else (ser[k][-1] if ser[k] else None))
    first = max(next(i for i, v in enumerate(ser[k]) if v) for k in keys)
    days, ser = days[first:], {k: v[first:] for k, v in ser.items()}
    n = len(days)
    rets = {k: [0.0] + [ser[k][i] / ser[k][i - 1] - 1 for i in range(1, n)] for k in keys}
    since = f"{MON[int(days[0][5:7]) - 1]} {days[0][:4]}"
    last_day = day_name(days[-1])

    def vol(r):
        m = sum(r) / len(r)
        return (sum((x - m) ** 2 for x in r) / (len(r) - 1)) ** 0.5 * math.sqrt(252) * 100

    def deepest(p):
        pk, w = p[0], 0.0
        for v in p:
            pk = max(pk, v)
            w = min(w, v / pk - 1)
        return w * 100

    def a_year(p):
        return ((p[-1] / p[0]) ** (252 / (len(p) - 1)) - 1) * 100

    def corr(a, b):
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        sab = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        sa, sb = sum((x - ma) ** 2 for x in a), sum((y - mb) ** 2 for y in b)
        return sab / (sa * sb) ** 0.5 if sa > 0 and sb > 0 else 0.0

    periods = [p for p in MK_PERIODS if p[1] < n] + [(f"Since {since}", n - 1)]
    ret_rows = "".join(
        f'<tr{" class=me" if k == "BTC" else ""}><th scope="row">{name}</th>'
        + "".join(f"<td>{mult_or_pct((ser[k][-1] / ser[k][n - 1 - back] - 1) * 100)}</td>" for _, back in periods) + "</tr>" for k, name in MK_NAMES)
    risk_rows = "".join(
        f'<tr{" class=me" if k == "BTC" else ""}><th scope="row">{name}</th><td>{move(a_year(ser[k]))}</td><td>{vol(rets[k][1:]):.0f}%</td>'
        f'<td>{move(deepest(ser[k]))}</td><td>{move(min(rets[k]) * 100)}</td><td>{move(max(rets[k]) * 100)}</td></tr>' for k, name in MK_NAMES)
    worst = sorted(range(1, n), key=lambda i: rets["SPX"][i])[:10]
    worst_rows = "".join(f'<tr><th scope="row">{day_name(days[i])}</th>' + "".join(f"<td>{move(rets[k][i] * 100)}</td>" for k in ("SPX", "BTC", "GOLD", "BOND")) + "</tr>" for i in worst)
    fell = {k: sum(1 for i in worst if round(rets[k][i] * 100, 1) < 0) for k in ("BTC", "GOLD", "BOND")}
    ports = {w: mk_portfolio(rets, days, w) for w in MK_SHARES}
    port_rows = ""
    for w, p in ports.items():
        years, prev, worst_year = {}, None, None
        for x, v in zip(days, p):
            years.setdefault(x[:4], [v, v])[1] = v
        for y in sorted(years):
            start = years[y][0] if prev is None else prev
            chg = (years[y][1] / start - 1) * 100
            worst_year = chg if worst_year is None else min(worst_year, chg)
            prev = years[y][1]
        pr = [p[i] / p[i - 1] - 1 for i in range(1, n)]
        port_rows += (f'<tr><th scope="row">{"None: 60/40" if not w else f"{w * 100:.0f}% Bitcoin"}</th><td>${p[-1] * 100:,.0f}</td><td>{move(a_year(p))}</td>'
                      f'<td>{vol(pr):.1f}%</td><td>{move(deepest(p))}</td><td>{move(worst_year)}</td></tr>')
    c90 = {k: corr(rets["BTC"][-90:], rets[k][-90:]) for k in ("SPX", "NDX", "GOLD", "DXY")}
    yr = lambda k: (ser[k][-1] / ser[k][max(0, n - 253)] - 1) * 100
    cfmt = lambda v: f"{MINUS if v < 0 else ''}{abs(v):.2f}"
    side = (("With the S&amp;P 500", cfmt(c90["SPX"]), "90-day correlation"), ("With gold", cfmt(c90["GOLD"]), "90-day correlation"),
            ("Bitcoin's volatility", f"{vol(rets['BTC'][-252:]):.0f}%", "last year"), ("The S&amp;P 500's", f"{vol(rets['SPX'][-252:]):.0f}%", "last year"))
    d0 = dt.date.fromisoformat(days[0])
    data = {"start": days[0], "d": [(dt.date.fromisoformat(x) - d0).days for x in days],
            "s": {k: [float(f"{v:.5g}") for v in ser[k]] for k in keys}}
    chips = "".join(f'<button type="button" class="chip" data-back="{b}" aria-pressed="{"true" if lab == "5Y" else "false"}">{lab}</button>'
                    for lab, b in (("1Y", 252), ("3Y", 756), ("5Y", 1260), ("10Y", 2520), (days[0][:4], n - 1)) if b < n)
    race = f"""      <section class="vr" aria-label="Bitcoin and the markets, from the same start" hidden>
        <canvas class="vr__c" role="img" aria-label="Bitcoin, gold, the S&amp;P 500, the Nasdaq, the dollar index and long Treasuries, each starting at 100 on the same day and drawn to today. The figures are in the Returns table below."></canvas>
        <p class="vr__date" aria-hidden="true"></p>
        <div class="vr__ctl"><div class="filters dd__ranges" role="group" aria-label="Start">{chips}</div><button class="btn btn--ghost vr__replay" type="button">Replay</button></div>
        <p class="lens-read vr__read" aria-live="polite"></p>
      </section>
"""
    panels = f"""      <section class="fr__panel" aria-labelledby="vm-ret-h"><div class="fr__ph"><h2 id="vm-ret-h">Returns</h2></div><p class="fr__intro">What each gained or lost over each period, to {last_day}.</p>
        <div class="cs-scroll"><table class="cs-tab vm-t"><thead><tr><th></th>{"".join(f'<th scope="col">{lab}</th>' for lab, _ in periods)}</tr></thead><tbody>{ret_rows}</tbody></table></div>
        <p class="fr__src">Coin Metrics for Bitcoin; Yahoo Finance for the S&amp;P 500, the Nasdaq Composite, gold futures, the dollar index and long Treasuries (the TLT fund, with its income). The share indices are price levels, without dividends. Periods in trading days.</p></section>
      <section class="fr__panel" aria-labelledby="vm-co-h"><div class="fr__ph"><h2 id="vm-co-h">Moving together</h2></div><p class="fr__intro">How closely Bitcoin's daily moves have followed each market's over the last 90 trading days: 1 is in step, 0 unrelated, below 0 opposite.</p>
        <div class="vm-plot" data-chart="corr"></div><p class="lens-read vm-read" data-read="corr" aria-live="polite"></p><p class="fr__src">Andra Markets calculation from daily closes.</p></section>
      <section class="fr__panel" aria-labelledby="vm-ri-h"><div class="fr__ph"><h2 id="vm-ri-h">Risk</h2></div><p class="fr__intro">What each made in a year on average, how much it swings, and its deepest fall from a record, since {since}.</p>
        <div class="cs-scroll"><table class="cs-tab vm-t"><thead><tr><th></th><th scope="col">A year, on average</th><th scope="col">Volatility</th><th scope="col">Deepest fall</th><th scope="col">Worst day</th><th scope="col">Best day</th></tr></thead><tbody>{risk_rows}</tbody></table></div>
        <p class="fr__src">Volatility: the spread of daily moves, scaled to a year. Andra Markets calculation.</p></section>
      <section class="fr__panel" aria-labelledby="vm-wd-h"><div class="fr__ph"><h2 id="vm-wd-h">On the market's worst days</h2></div><p class="fr__intro">The ten largest one-day falls of the S&amp;P 500 since {since}, and what Bitcoin, gold and long Treasuries did the same day.</p>
        <div class="cs-scroll"><table class="cs-tab vm-t"><thead><tr><th scope="col">Day</th><th scope="col">S&amp;P 500</th><th scope="col">Bitcoin</th><th scope="col">Gold</th><th scope="col">Long Treasuries</th></tr></thead><tbody>{worst_rows}</tbody></table></div>
        <p class="lens-read vm-read">Bitcoin fell on {fell["BTC"]} of the ten, gold on {fell["GOLD"]}, long Treasuries on {fell["BOND"]}</p><p class="fr__src">Andra Markets calculation from daily closes.</p></section>
      <section class="fr__panel" aria-labelledby="vm-pf-h"><div class="fr__ph"><h2 id="vm-pf-h">A little Bitcoin in a portfolio</h2></div><p class="fr__intro">A classic portfolio, 60% shares and 40% bonds, with a share of it moved into Bitcoin and put back to its weights every month. Move the share and see what it would have done since {since}.</p>
        <div class="pm" hidden><label class="pm__l" for="pm-w">Bitcoin's share <output id="pm-o" for="pm-w">5%</output></label><input id="pm-w" type="range" min="0" max="20" step="1" value="5">
          <div class="pm__figs" aria-live="polite"><div><span class="lens-read">$10,000 became</span><b id="pm-v"></b><i id="pm-v2"></i></div><div><span class="lens-read">Volatility</span><b id="pm-s"></b><i id="pm-s2"></i></div><div><span class="lens-read">Deepest fall</span><b id="pm-d"></b><i id="pm-d2"></i></div></div>
          <canvas class="pm__c" role="img" aria-label="The portfolio with the chosen share of Bitcoin, in amber, against the plain 60/40 portfolio, both starting at 100."></canvas></div>
        <div class="cs-scroll"><table class="cs-tab vm-t"><thead><tr><th scope="col">Bitcoin's share</th><th scope="col">$10,000 became</th><th scope="col">A year, on average</th><th scope="col">Volatility</th><th scope="col">Deepest fall</th><th scope="col">Worst year</th></tr></thead><tbody>{port_rows}</tbody></table></div>
        <p class="fr__src">The S&amp;P 500 (price level) and long Treasuries (TLT), rebalanced monthly, before fees and taxes. What happened says nothing certain of what will. For information only. Not investment advice.</p></section>
"""
    script = f"""      <script type="application/json" id="vm-data">{json.dumps(data, separators=(",", ":"))}</script>
"""
    return {"race": race, "panels": panels, "script": script, "side": side, "last": last_day}


# ---- Derivatives (crypto/derivatives/; owner-approved sketch, 27 Nov 2026: "the pulse", after two charts of the
# options by strike were turned down) ----
def load_derivs(site):
    try:
        m = json.loads((site.ROOT / ".cache" / "crypto" / "derivs.json").read_text(encoding="utf-8"))
        return m if len(m.get("dvol") or []) > 200 and m.get("expiries") else None
    except (OSError, ValueError):
        return None


def derivs_page(site, d, hist, dv):
    import math
    path = "crypto/derivatives/"
    if not hist or not dv:
        return pending(site, path, "Derivatives")
    spot = dv["spot"]
    try:
        fetched = dt.datetime.fromisoformat(dv["fetched"])
        when, today = f"{fetched.day} {fetched:%b %Y}, {fetched:%H:%M} UTC", fetched.date()
    except (KeyError, ValueError):
        when, today = "", dt.date.today()
    usd = lambda v: f"${v / 1e9:.1f}bn" if v >= 1e9 else f"${v / 1e6:,.0f}m"
    rate = lambda v, dgt=1: f'<span class="{"up" if round(v, dgt) > 0 else "down" if round(v, dgt) < 0 else ""}">{signed(v, dgt)}%</span>'
    # the pulse: DVOL, and what the price actually did over the 30 days before each day
    b0, bp = dt.date.fromisoformat(hist["start"]), hist["p"]
    dvol = [(x, v) for x, v in dv["dvol"] if v]
    d0 = dt.date.fromisoformat(dvol[0][0])
    real = []
    for x, _ in dvol:
        i = (dt.date.fromisoformat(x) - b0).days
        if 31 <= i < len(bp):
            r = [math.log(bp[j] / bp[j - 1]) for j in range(i - 29, i + 1)]
            m = sum(r) / 30
            real.append(round((sum((y - m) ** 2 for y in r) / 29) ** 0.5 * math.sqrt(365) * 100, 1))
        else:
            real.append(None)
    last_dvol = dvol[-1][1]
    last_real = next((v for v in reversed(real) if v is not None), None)
    rank = sum(1 for _, v in dvol if v <= last_dvol) / len(dvol) * 100
    per_day = last_dvol / math.sqrt(365)
    # funding
    fund = dv.get("fund") or []
    f_pos = sum(1 for _, v in fund if v > 0)
    f_avg = sum(v for _, v in fund[-30:]) / max(1, len(fund[-30:]))
    # futures
    futs, perp = [], None
    for f in dv["futures"]:
        if not f["date"]:
            perp = f
            continue
        days = max(1, (dt.date.fromisoformat(f["date"]) - today).days)
        futs.append({"date": f["date"], "days": days, "mark": f["mark"], "oi": f["oi"], "prem": (f["mark"] / spot - 1) * 100, "ann": (f["mark"] / spot - 1) * 365 / days * 100})
    futs.sort(key=lambda f: f["days"])
    curve = [f for f in futs if f["days"] >= 7]
    fut_rows = (f'<tr><th scope="row">Perpetual</th><td>{money(perp["mark"])}</td><td>{rate((perp["mark"] / spot - 1) * 100, 2)}</td><td>see Funding</td><td>{usd(perp["oi"])}</td></tr>' if perp else "") + "".join(
        f'<tr><th scope="row">{day_name(f["date"])}</th><td>{money(f["mark"])}</td><td>{rate(f["prem"], 2)}</td><td>{rate(f["ann"]) if f["days"] >= 7 else "n/a"}</td><td>{usd(f["oi"])}</td></tr>' for f in futs)
    near3 = min(curve, key=lambda f: abs(f["days"] - 91)) if curve else None
    # options
    exps = []
    for e in dv["expiries"]:
        ks = e["k"]
        calls, puts = sum(r[1] for r in ks), sum(r[2] for r in ks)
        if calls + puts <= 0:
            continue
        pain = min((sum(max(0, s[0] - r[0]) * r[1] + max(0, r[0] - s[0]) * r[2] for r in ks), s[0]) for s in ks)[1]
        exps.append({"date": e["date"], "days": max(0, (dt.date.fromisoformat(e["date"]) - today).days), "c": calls, "p": puts, "pain": pain, "und": e["und"] or spot, "k": ks})
    exp_rows = "".join(
        f'<tr><th scope="row">{day_name(e["date"])}</th><td>{"today" if not e["days"] else f"""{e["days"]} day{"s" if e["days"] != 1 else ""}"""}</td><td>{e["c"]:,.0f}</td><td>{e["p"]:,.0f}</td>'
        f'<td>{e["p"] / e["c"]:.2f}</td><td>{usd((e["c"] + e["p"]) * spot)}</td><td>${e["pain"]:,.0f}</td></tr>' if e["c"] else "" for e in exps)
    tc, tp = sum(e["c"] for e in exps), sum(e["p"] for e in exps)
    big_e = max((e for e in exps if e["days"] >= 7), key=lambda e: e["c"] + e["p"], default=exps[-1])
    und = big_e["und"]
    smile = [[r[0], r[4] if r[0] < und else r[3]] for r in big_e["k"] if und * 0.5 < r[0] < und * 1.8 and (r[4] if r[0] < und else r[3])]
    near = lambda t: min(smile, key=lambda q: abs(q[0] - t))[1] if smile else None
    s_atm, s_dn, s_up = near(und), near(und * 0.8), near(und * 1.2)
    fut_oi = sum(f["oi"] for f in dv["futures"])
    side = kpis((("DVOL", f"{last_dvol:.1f}%", "expected, next 30 days"), ("Actual", f"{last_real:.1f}%" if last_real is not None else "n/a", "last 30 days"),
                 ("Funding", rate(fund[-1][1]) if fund else "n/a", "a year, latest day"), ("3-month future", rate(near3["ann"]) if near3 else "n/a", "a year over Bitcoin"),
                 ("Options open", usd((tc + tp) * spot), f"{tc + tp:,.0f} bitcoin"), ("Futures open", usd(fut_oi), f"perpetual {usd(perp['oi'])}" if perp else ""),
                 ("Puts per call", f"{tp / tc:.2f}" if tc else "n/a", "all expiries"), ("Largest expiry", day_name(big_e["date"]), f"max pain ${big_e['pain']:,.0f}")))
    data = {"start": dvol[0][0], "d": [(dt.date.fromisoformat(x) - d0).days for x, _ in dvol], "dvol": [v for _, v in dvol], "real": real,
            "fund": {"start": fund[0][0], "d": [(dt.date.fromisoformat(x) - dt.date.fromisoformat(fund[0][0])).days for x, _ in fund], "v": [v for _, v in fund]} if fund else None,
            "curve": [[f["days"], round(f["ann"], 2), f["date"]] for f in curve], "smile": smile, "und": und}
    body = f"""<main id="main" class="page dd fr cs-page vm dvp">
  <div class="wrap dd__grid">
    <header class="page__head dd__head">
      <h1 class="page__title">Derivatives</h1>
      <p class="lede">How much the market expects Bitcoin to move, what it costs to bet with borrowed money and where the options sit.</p>
      <p class="note__meta"><span>Deribit</span><span>Updated {when}</span><span>Refreshed at every deploy</span></p>
      <section class="vr dvh" aria-label="DVOL, the swing the market expects" hidden>
        <canvas class="vr__c" role="img" aria-label="DVOL, the yearly swing Bitcoin options price in for the next 30 days, each day since {day_name(dvol[0][0])}, with the swing that actually happened behind it. Today {last_dvol:.1f}%."></canvas>
        <p class="vr__date dvh__fig" aria-hidden="true"><b>{last_dvol:.1f}%</b><span>The market expects Bitcoin to move about {per_day:.1f}% a day over the next month</span></p>
        <div class="vr__ctl"><button class="btn btn--ghost vr__replay" type="button">Replay</button></div>
        <p class="lens-read vr__read" aria-live="polite"></p>
      </section>
    </header>
    <div class="dd__main fr__main">
      <section class="fr__panel" aria-labelledby="dv-pulse-h"><div class="fr__ph"><h2 id="dv-pulse-h">Expected and actual swings</h2></div><p class="fr__intro">DVOL is what options price in for the next 30 days, as a yearly figure: Bitcoin's VIX. Today it stands at {last_dvol:.1f}%, higher than on {rank:.0f}% of days since {day_name(dvol[0][0])}; over the last 30 days the price actually swung at {f"{last_real:.1f}%" if last_real is not None else "n/a"}. Divide a yearly figure by 19 for a day's move.</p>
        <p class="fr__src">Deribit (the DVOL index, daily closes); realised volatility from Coin Metrics daily closes, over the 30 days before each day.</p></section>
      <section class="fr__panel" aria-labelledby="dv-fund-h"><div class="fr__ph"><h2 id="dv-fund-h">Funding</h2></div><p class="fr__intro">What holders of the perpetual future pay each other to keep it at Bitcoin's price, as a yearly rate. Above zero, those betting on a rise pay those betting on a fall: the market leans long.</p>
        <div class="vm-plot" data-chart="fund"></div><p class="lens-read vm-read" data-read="fund" aria-live="polite">Longs paid on {f_pos} of the last {len(fund)} days · 30-day average {rate(f_avg)} a year</p><p class="fr__src">Deribit, BTC-PERPETUAL: each day's average of its hourly rates.</p></section>
      <section class="fr__panel" aria-labelledby="dv-curve-h"><div class="fr__ph"><h2 id="dv-curve-h">The futures curve</h2></div><p class="fr__intro">Each future's price over Bitcoin's now, as a yearly rate. Above zero the market pays up to hold Bitcoin later; below, it sells it at a discount. Futures that expire within a week are left off the chart: a few dollars make a wild yearly rate.</p>
        <div class="vm-plot" data-chart="curve"></div>
        <div class="cs-scroll"><table class="cs-tab vm-t"><thead><tr><th scope="col">Future</th><th scope="col">Price</th><th scope="col">Over Bitcoin now</th><th scope="col">As a yearly rate</th><th scope="col">Open</th></tr></thead><tbody>{fut_rows}</tbody></table></div>
        <p class="fr__src">Deribit, mark prices against its Bitcoin index of {money(spot)}, {when}.</p></section>
      <section class="fr__panel" aria-labelledby="dv-smile-h"><div class="fr__ph"><h2 id="dv-smile-h">The smile</h2></div><p class="fr__intro">The volatility options price in at each strike, for the largest expiry, {day_name(big_e["date"])}. A left side higher than the right means protection against a fall costs more than a bet on a rise.</p>
        <div class="vm-plot" data-chart="smile"></div><p class="lens-read vm-read">{f"At the price {s_atm:.0f}% · 20% below, {s_dn:.0f}% · 20% above, {s_up:.0f}% · protection against a fall costs {'more' if s_dn > s_up else 'less'} than a bet on a rise" if s_atm else ""}</p>
        <p class="fr__src">Deribit, mark volatility: puts below the price, calls above.</p></section>
      <section class="fr__panel" aria-labelledby="dv-exp-h"><div class="fr__ph"><h2 id="dv-exp-h">Every expiry</h2></div><p class="fr__intro">Open option contracts at each expiry, in bitcoin: one contract is one bitcoin. Max pain is the price at which the most options would expire worthless.</p>
        <div class="cs-scroll"><table class="cs-tab vm-t"><thead><tr><th scope="col">Expiry</th><th scope="col">In</th><th scope="col">Calls</th><th scope="col">Puts</th><th scope="col">Puts per call</th><th scope="col">Worth</th><th scope="col">Max pain</th></tr></thead><tbody>{exp_rows}</tbody></table></div>
        <p class="fr__src">Deribit, {when}. Deribit holds most of the world's Bitcoin options, but not the futures of CME or other exchanges: these are its figures alone. For information only. Not investment advice.</p></section>
      {more(site, path, "../../")}
      <script type="application/json" id="dv-data">{json.dumps(data, separators=(",", ":"))}</script>
    </div>
    <aside class="report__side dd__side" aria-labelledby="side-title"><h2 class="report__side-title" id="side-title">Latest</h2><ul class="kpi">{side}</ul><p class="report__src">Deribit, {when}.</p></aside>
  </div>
</main>"""
    return site.shell(title="Derivatives: Crypto: Andra Markets", desc=f"Bitcoin's derivatives on Deribit: DVOL at {last_dvol:.0f}%, the perpetual's funding, the futures curve, the volatility smile and every option expiry with its max pain.",
                      body=body, home="../../", base="../../", path=path, scripts=("crypto-derivs.js",))


# ---- Network (crypto/network/; owner-approved sketch, 28 Nov 2026: both pieces, the Lightning nodes on the whole
# Earth and the hashrate as a line of light; the line of text under the globe taken away) ----
def load_network(site):
    try:
        m = json.loads((site.ROOT / ".cache" / "crypto" / "network.json").read_text(encoding="utf-8"))
        return m if len(m.get("hash") or []) > 1000 and m.get("places") else None
    except (OSError, ValueError):
        return None


def network_page(site, d, nw):
    path = "crypto/network/"
    if not nw:
        return pending(site, path, "Network")
    try:
        fetched = dt.datetime.fromisoformat(nw["fetched"])
        when = f"{fetched.day} {fetched:%b %Y}, {fetched:%H:%M} UTC"
    except (KeyError, ValueError):
        when = ""
    btc_price = d["coins"][0]["price"]
    rate = lambda v, dgt=1: f'<span class="{"up" if round(v, dgt) > 0 else "down" if round(v, dgt) < 0 else ""}">{signed(v, dgt)}%</span>'
    ln, places = nw["ln"], nw["places"]
    globe = {"asof": nw["fetched"], "points": nw["points"], "places": [
        {"name": p["name"], "lon": p["lon"], "lat": p["lat"], "share": p["share"] / 100, "label": f"{p['count']:,} nodes · {p['share']:.0f}%", "more": f"{p['btc']:,.0f} BTC in channels"} for p in places]}
    hs = nw["hash"]
    last = hs[-1][1]
    idx = lambda day: next((i for i, h in enumerate(hs) if h[0] >= day), len(hs) - 1)
    year_ago = hs[idx((dt.date.fromisoformat(hs[-1][0]) - dt.timedelta(days=365)).isoformat())][1]
    marks = []
    a, b = idx("2021-04-15"), idx("2021-08-01")
    if b > a:
        hi = max(range(a, b), key=lambda i: hs[i][1])
        lo = min(range(hi, b + 1), key=lambda i: hs[i][1])
        marks.append({"i": lo, "fall": round((hs[lo][1] / hs[hi][1] - 1) * 100), "text": "China bans mining, 2021"})
    top_i = max(range(len(hs)), key=lambda i: hs[i][1])
    big = lambda v: f"{v / 1000:.2f} ZH/s" if v >= 1000 else f"{v:,.0f} EH/s"
    df = nw["difficulty"]
    retarget = dt.datetime.fromtimestamp(df["estimatedRetargetDate"] / 1000, dt.timezone.utc)
    pools, blocks = nw["pools"]["list"], nw["pools"]["blocks"]
    shown = pools[:8]
    rest = blocks - sum(n for _, n in shown)
    pool_rows = "".join(f'<div class="mk-row"><span>{site.esc(name)}</span><i><b style="width:{min(100, n / blocks * 200):.1f}%"></b></i><span>{n / blocks * 100:.1f}%</span></div>'
                        for name, n in shown + [["Every other pool", rest]])
    fees, queue = nw["fees"], nw["queue"]
    pay = fees["fastestFee"] * 140 / 1e8 * btc_price
    ln_rows = "".join(f'<tr><th scope="row">{site.esc(p["name"])}</th><td>{p["count"]:,}</td><td>{p["share"]:.1f}%</td><td>{p["btc"]:,.0f} BTC</td></tr>' for p in places[:12])
    side = kpis((("Hashrate", big(nw["now"]), "now"), ("Next difficulty", rate(df["difficultyChange"]), f"in {df['remainingBlocks']:,} blocks"),
                 ("Next block", f"{fees['fastestFee']} sat/vB", "fee to get in"), ("Waiting", f"{queue['count']:,}", "transactions"),
                 ("Largest pool", site.esc(pools[0][0]), f"{pools[0][1] / blocks * 100:.1f}% of blocks"), ("Top three pools", f"{sum(n for _, n in pools[:3]) / blocks * 100:.0f}%", "of the last month's blocks"),
                 ("Lightning nodes", f"{ln['node_count']:,}", f"{ln['channel_count']:,} channels"), ("In Lightning", f"{ln['total_capacity'] / 1e8:,.0f} BTC", big_usd(ln["total_capacity"] / 1e8 * btc_price))))
    data = {"hash": {"start": hs[0][0], "step": 2, "v": [h[1] for h in hs], "marks": marks, "halvings": [x[0] for x in HALVINGS]},
            "fees": {"t": [r[0] for r in nw["feerates"]], "mid": [r[1] for r in nw["feerates"]], "top": [r[2] for r in nw["feerates"]]}}
    body = f"""<main id="main" class="page dd fr cs-page vm nwp">
  <div class="wrap dd__grid">
    <header class="page__head dd__head">
      <h1 class="page__title">Network</h1>
      <p class="lede">Where Bitcoin's network lives, how much power guards it and what it costs to use.</p>
      <p class="note__meta"><span>mempool.space</span><span>Updated {when}</span><span>Refreshed at every deploy</span></p>
      <section class="cg cg--points" aria-label="Lightning nodes on the Earth" hidden>
        <canvas class="cg__gl" aria-hidden="true"></canvas>
        <canvas class="cg__ov" aria-hidden="true"></canvas>
        <div class="cg__names" aria-hidden="true"></div>
        <div class="cg__big"><p class="lens-read">Lightning nodes</p><p class="cg__fig">{ln["node_count"]:,}</p>
          <p class="cg__say">computers that move bitcoin in an instant. Each light is a town with some of the {nw["located"]:,} that say where they are; the rest keep it to themselves.</p></div>
        <p class="visually-hidden cg__status" role="status" aria-live="polite"></p>
        <p class="visually-hidden">The Earth as lit at {when}, with a light at each town where Lightning nodes publish an address, brighter with more bitcoin in their channels. The countries are in the table below.</p>
        <script type="application/json">{json.dumps(globe, separators=(",", ":")).replace("</", "<\\/")}</script>
      </section>
      <section class="vr dvh nwh" aria-label="The power that guards the network" hidden>
        <canvas class="vr__c" role="img" aria-label="Bitcoin's hashrate, weekly average, since 2010, with the four halvings. Now {big(last)}."></canvas>
        <p class="vr__date dvh__fig" aria-hidden="true"><b>{big(last)}</b><span>The computing power guarding Bitcoin: a billion billion guesses, {last:,.0f} times over, every second</span></p>
        <div class="vr__ctl"><button class="btn btn--ghost vr__replay" type="button">Replay</button></div>
        <p class="lens-read vr__read" aria-live="polite"></p>
      </section>
    </header>
    <div class="dd__main fr__main">
      <section class="fr__panel" aria-labelledby="nw-hash-h"><div class="fr__ph"><h2 id="nw-hash-h">Hashrate</h2></div><p class="fr__intro">Miners guess numbers until one seals a block; the hashrate is how many guesses the whole network makes each second. It stands at {big(last)}, {rate((last / year_ago - 1) * 100, 0)} on a year ago; its highest week was {big(hs[top_i][1])}, in {MON[int(hs[top_i][0][5:7]) - 1]} {hs[top_i][0][:4]}. One EH/s is a billion billion guesses a second.</p>
        <p class="fr__src">mempool.space, daily estimates averaged over the week to each day.</p></section>
      <section class="fr__panel" aria-labelledby="nw-diff-h"><div class="fr__ph"><h2 id="nw-diff-h">Difficulty</h2></div><p class="fr__intro">Every 2,016 blocks, about two weeks, the network makes mining harder or easier so that a block still takes ten minutes.</p>
        <div class="mk-bars"><div class="mk-row"><span>This period</span><i><b style="width:{df["progressPercent"]:.1f}%"></b></i><span>{df["progressPercent"]:.0f}%</span></div></div>
        <p class="lens-read vm-read">{df["remainingBlocks"]:,} blocks to the next change, about {retarget.day} {MON[retarget.month - 1]} {retarget.year} · expected {rate(df["difficultyChange"])} · the last one {rate(df["previousRetarget"])} · blocks are taking {df["timeAvg"] / 60000:.1f} minutes</p>
        <p class="fr__src">mempool.space, {when}.</p></section>
      <section class="fr__panel" aria-labelledby="nw-pool-h"><div class="fr__ph"><h2 id="nw-pool-h">Who mines</h2></div><p class="fr__intro">The share of the last month's {blocks:,} blocks found by each mining pool. No pool should come near half: the bars run to 50%.</p>
        <div class="mk-bars">{pool_rows}</div><p class="fr__src">mempool.space: blocks by the pool that signed them.</p></section>
      <section class="fr__panel" aria-labelledby="nw-fee-h"><div class="fr__ph"><h2 id="nw-fee-h">Fees and the queue</h2></div><p class="fr__intro">What a transaction pays to get into a block, in satoshis for each unit of space (sat/vB): the middle transaction and the dearest tenth, over a year.</p>
        <div class="vm-plot" data-chart="fees"></div>
        <p class="lens-read vm-read" data-read="fees" aria-live="polite">Now: {fees["fastestFee"]} sat/vB gets into the next block, about ${pay:,.2f} for a plain payment · {queue["count"]:,} transactions wait, {queue["vsize"] / 1e6:.0f} blocks' worth</p>
        <p class="fr__src">mempool.space, {when}. A plain payment is taken as 140 units of space, at Bitcoin's price of {money(btc_price)}.</p></section>
      <section class="fr__panel" aria-labelledby="nw-ln-h"><div class="fr__ph"><h2 id="nw-ln-h">Lightning by country</h2></div><p class="fr__intro">Lightning moves bitcoin at once through channels opened between nodes. Where the nodes that publish an address are, and the bitcoin in their channels.</p>
        <div class="cs-scroll"><table class="cs-tab vm-t"><thead><tr><th scope="col">Country</th><th scope="col">Nodes</th><th scope="col">Share</th><th scope="col">In channels</th></tr></thead><tbody>{ln_rows}</tbody></table></div>
        <p class="fr__src">mempool.space. Of {ln["node_count"]:,} nodes, {ln.get("tor_nodes", 0):,} are reached only through Tor and have no place; a node's place is where its address says it is. The Earth: Solar System Scope (CC BY 4.0), from NASA imagery. For information only. Not investment advice.</p></section>
      {more(site, path, "../../")}
      <script type="application/json" id="nw-data">{json.dumps(data, separators=(",", ":"))}</script>
    </div>
    <aside class="report__side dd__side" aria-labelledby="side-title"><h2 class="report__side-title" id="side-title">Latest</h2><ul class="kpi">{side}</ul><p class="report__src">mempool.space, {when}.</p></aside>
  </div>
</main>"""
    return site.shell(title="Network: Crypto: Andra Markets", desc=f"Bitcoin's network: {ln['node_count']:,} Lightning nodes on the Earth, a hashrate of {big(last)}, the next difficulty change, who mines, fees and the queue.",
                      body=body, home="../../", base="../../", path=path, scripts=("crypto-globe.js", "crypto-network.js"))


def big_usd(v):
    return f"${v / 1e9:.1f}bn" if v >= 1e9 else f"${v / 1e6:,.0f}m"


# ---- Stablecoins & DeFi (crypto/stablecoins/; owner, 28 Nov 2026: a line of light "the same as all the others" and a
# river of strands were turned down; the plain data page was accepted: "that will do") ----
BACKING = {"fiat-backed": "Dollars and bills", "algorithmic": "A formula"}


def load_defi(site):
    try:
        m = json.loads((site.ROOT / ".cache" / "crypto" / "defi.json").read_text(encoding="utf-8"))
        return m if len(m.get("total") or []) > 300 and m.get("coins") else None
    except (OSError, ValueError):
        return None


def defi_page(site, d, df):
    path = "crypto/stablecoins/"
    if not df:
        return pending(site, path, "Stablecoins &amp; DeFi")
    try:
        fetched = dt.datetime.fromisoformat(df["fetched"])
        when = f"{fetched.day} {fetched:%b %Y}, {fetched:%H:%M} UTC"
    except (KeyError, ValueError):
        when = ""
    supply, coins = df["supply"], df["coins"]
    share = lambda v, tot: f"{v / tot * 100:.1f}%" if v / tot < 0.01 else f"{v / tot * 100:.0f}%"

    def bars(rows, tot):
        return "".join(f'<div class="mk-row"><span>{site.esc(n)}</span><i><b style="width:{min(100, v / tot * 100):.1f}%"></b></i><span>{share(v, tot)}</span></div>' for n, v in rows)
    coin_rows = ""
    for c in coins:
        month = (c["supply"] / c["month"] - 1) * 100 if c.get("month") else None
        # a change of more than two fifths in a month is a coin moved from one contract to another, not a market move
        month_cell = move(month) if month is not None and abs(month) <= 40 else '<span class="cs-none">n/a</span>'
        off = (c["price"] - 1) * 100 if c.get("price") and c.get("peg") == "peggedUSD" else None
        off_cell = f'<span class="{"up" if round(off, 2) > 0 else "down" if round(off, 2) < 0 else ""}">{signed(off, 2)}%</span>' if off is not None else '<span class="cs-none">n/a</span>'
        coin_rows += (f'<tr><th scope="row">{site.esc(c["name"])} <span class="cs-sym">{site.esc(c["symbol"])}</span></th><td>{big(c["supply"])}</td><td>{c["supply"] / supply * 100:.1f}%</td>'
                      f'<td>{month_cell}</td><td class="sd-l">{BACKING.get(c.get("backing"), "Other coins")}</td><td>{off_cell}</td></tr>')
    back = df["backing"]
    tot, tvl = df["total"], df["tvl"]
    rec_i = max(range(len(tot)), key=lambda i: tot[i][1])
    tvl_i = max(range(len(tvl)), key=lambda i: tvl[i][1])
    mon = lambda ts: (lambda x: f"{MON[x.month - 1]} {x.year}")(dt.datetime.fromtimestamp(ts, dt.timezone.utc))
    tvl_now = tvl[-1][1] * 1e9
    year_ago = next((v for t, v in tot if t >= tot[-1][0] - 365 * 86400), tot[0][1])
    prot_rows = "".join(f'<tr><th scope="row">{site.esc(n)}</th><td class="sd-l">{site.esc(cat)}</td><td>{big(v)}</td><td>{move(ch) if ch is not None else "<span class=cs-none>n/a</span>"}</td></tr>' for n, cat, v, ch in df["protocols"])
    side = kpis((("Stablecoins", big(supply), f"{df['count']} coins"), (f"{site.esc(coins[0]['name'])}'s share", f"{coins[0]['supply'] / supply * 100:.0f}%", big(coins[0]["supply"])),
                 (f"{site.esc(coins[1]['symbol'])}'s share", f"{coins[1]['supply'] / supply * 100:.0f}%", big(coins[1]["supply"])), ("Backed by dollars", f"{back.get('fiat', 0) / supply * 100:.0f}%", "of all stablecoins"),
                 (f"On {site.esc(df['chains'][0][0])}", share(df["chains"][0][1], supply), "of stablecoins"), (f"On {site.esc(df['chains'][1][0])}", share(df["chains"][1][1], supply), "of stablecoins"),
                 ("Locked in DeFi", big(tvl_now), "every chain"), ("Largest protocol", site.esc(df["protocols"][0][0]), big(df["protocols"][0][2]))))
    data = {"total": {"t": [r[0] for r in tot], "v": [r[1] for r in tot]}, "tvl": {"t": [r[0] for r in tvl], "v": [r[1] for r in tvl]}}
    body = f"""<main id="main" class="page dd fr cs-page vm sdp">
  <div class="wrap dd__grid">
    <header class="page__head dd__head">
      <h1 class="page__title">Stablecoins &amp; DeFi</h1>
      <p class="lede">The dollars that live on blockchains, who issues them, and the money put to work there.</p>
      <p class="note__meta"><span>DefiLlama</span><span>Updated {when}</span><span>Refreshed at every deploy</span></p>
    </header>
    <div class="dd__main fr__main">
      <section class="fr__panel" aria-labelledby="sd-tot-h"><div class="fr__ph"><h2 id="sd-tot-h">How many there are</h2></div><p class="fr__intro">A stablecoin promises to be worth one unit of a currency, nearly always the dollar. Every one in circulation, in dollars, since 2019.</p>
        <div class="vm-plot" data-chart="total" data-unit="in circulation"></div>
        <p class="lens-read vm-read" data-read="total" aria-live="polite">${tot[-1][1]:,.0f}bn at the last daily count, {move((tot[-1][1] / year_ago - 1) * 100)} in a year · its record ${tot[rec_i][1]:,.0f}bn in {mon(tot[rec_i][0])} · it fell by a third after Terra collapsed in May 2022</p>
        <p class="fr__src">DefiLlama, {df["count"]} stablecoins.</p></section>
      <section class="fr__panel" aria-labelledby="sd-who-h"><div class="fr__ph"><h2 id="sd-who-h">Who issues them</h2></div><p class="fr__intro">The twelve largest: how many are in circulation, their share, how the month went and how close each trades to the dollar it promises.</p>
        <div class="cs-scroll"><table class="cs-tab vm-t"><thead><tr><th scope="col">Coin</th><th scope="col">In circulation</th><th scope="col">Share</th><th scope="col">Month</th><th scope="col" class="sd-l">Backed by</th><th scope="col">Off its peg</th></tr></thead><tbody>{coin_rows}</tbody></table></div>
        <p class="fr__src">DefiLlama, {when}. Month: the change in coins in circulation, left out where a coin moved to a new contract. Off its peg: the price against one dollar.</p></section>
      <section class="fr__panel" aria-labelledby="sd-back-h"><div class="fr__ph"><h2 id="sd-back-h">What backs them</h2></div><p class="fr__intro">Some issuers hold dollars and Treasury bills in a bank; some hold other coins as collateral; a few hold only a formula.</p>
        <div class="mk-bars">{bars((("Dollars and Treasury bills", back.get("fiat", 0)), ("Other coins as collateral", back.get("crypto", 0)), ("A formula", back.get("formula", 0))), supply)}</div>
        <p class="fr__src">DefiLlama, by the mechanism each coin declares.</p></section>
      <section class="fr__panel" aria-labelledby="sd-where-h"><div class="fr__ph"><h2 id="sd-where-h">Where they live</h2></div><p class="fr__intro">The blockchains that carry the most stablecoins.</p>
        <div class="mk-bars">{bars(df["chains"][:7], supply)}</div><p class="fr__src">DefiLlama.</p></section>
      <section class="fr__panel" aria-labelledby="sd-tvl-h"><div class="fr__ph"><h2 id="sd-tvl-h">Money at work in DeFi</h2></div><p class="fr__intro">The value locked in decentralised finance: coins lent, staked or pooled in programs that run without a bank.</p>
        <div class="vm-plot" data-chart="tvl" data-unit="locked"></div>
        <p class="lens-read vm-read" data-read="tvl" aria-live="polite">{big(tvl_now)} locked today · its record ${tvl[tvl_i][1]:,.0f}bn in {mon(tvl[tvl_i][0])}, {move((tvl[-1][1] / tvl[tvl_i][1] - 1) * 100)} from it</p>
        <p class="fr__src">DefiLlama, total value locked across every chain, in US dollars.</p></section>
      <section class="fr__panel" aria-labelledby="sd-big-h"><div class="fr__ph"><h2 id="sd-big-h">The largest chains and protocols</h2></div><p class="fr__intro">Where that money sits: by blockchain, then by program.</p>
        <div class="mk-bars sd-gap">{bars(df["defi_chains"][:7], tvl_now)}</div>
        <div class="cs-scroll"><table class="cs-tab vm-t"><thead><tr><th scope="col">Protocol</th><th scope="col" class="sd-l">What it does</th><th scope="col">Locked</th><th scope="col">Week</th></tr></thead><tbody>{prot_rows}</tbody></table></div>
        <p class="fr__src">DefiLlama, {when}. Exchanges are left out. For information only. Not investment advice.</p></section>
      {more(site, path, "../../")}
      <script type="application/json" id="sd-data">{json.dumps(data, separators=(",", ":"))}</script>
    </div>
    <aside class="report__side dd__side" aria-labelledby="side-title"><h2 class="report__side-title" id="side-title">Latest</h2><ul class="kpi">{side}</ul><p class="report__src">DefiLlama, {when}.</p></aside>
  </div>
</main>"""
    return site.shell(title="Stablecoins & DeFi: Crypto: Andra Markets", desc=f"{big(supply)} of stablecoins: who issues them, what backs them and which blockchains carry them, and the {big(tvl_now)} locked in DeFi by chain and protocol.",
                      body=body, home="../../", base="../../", path=path, scripts=("crypto-defi.js",))
