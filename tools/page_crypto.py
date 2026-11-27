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
    hist = load_history(site)
    out["crypto/bitcoin/"] = bitcoin_page(site, d, hist)
    try:
        today = dt.datetime.fromisoformat(d["asof"].replace("Z", "+00:00")).date()
    except ValueError:
        today = dt.date.today()
    out.update(coin_pages(site, d, hist, when, today))
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
