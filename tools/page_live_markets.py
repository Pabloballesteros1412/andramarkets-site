"""Live Markets (live-markets/): live quotes and charts from TradingView's free
widgets, all on one page of the Markets group (owner, 25 Nov 2026: "a new
section, Live Markets, and everything goes there, as if you had walked into
TradingView"). A tape under the header, the full chart, the market overview in
four tabs beside the index in focus, and the heatmap of the IBEX 35 or the
S&P 500.

The symbols are in assets/markets-config.js; assets/markets.js mounts each
widget when it comes near the screen and builds it again when the theme changes.
The widgets load from TradingView, so this is the one page whose Content
Security Policy admits its scripts and frames (TV_MARK in build_site.py), and
the privacy policy names it (tools/legal_content.py).
"""
CONFIG = "markets-config.js"


def slot(kind, label, extra=""):
    """A widget's place: its frame, the skeleton shown until it loads, the line shown if it
    cannot, and TradingView's own attribution, which the free widgets require."""
    return (f'<div class="tv tv--{kind}" data-tv="{kind}"{extra}>'
            f'<div class="tv__frame" role="group" aria-label="{label}"></div>'
            f'<p class="tv__fail">Live data did not load. It comes from TradingView: a content blocker or a '
            f'lost connection can stop it.</p>'
            f'<p class="tv__by"><a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank">'
            f'Track all markets on TradingView</a></p></div>')


def pages(site):
    def switch(slot_id, items, label, what=""):
        """The chips that choose what a slot shows; assets/markets.js fills them from the config."""
        return (f'<div class="filters lm-switch" role="group" aria-label="{label}" data-tv-switch="{slot_id}" '
                f'data-tv-list="{items}" data-tv-what="{what}" hidden></div>')

    body = f"""<main id="main" class="page lm">
  <div class="lm-tape">{slot("tape", "Quotes tape")}</div>
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Live Markets</h1>
      <p class="lede">Indices, shares, currencies, commodities, bonds and crypto as they trade, on TradingView's charts.</p>
    </header>
    <section class="lm-minis-sec" aria-label="The day so far">
      <div class="lm-minis" data-tv-minis></div>
      <p class="tv__by"><a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank">Track all markets on TradingView</a></p>
    </section>
    <section class="lm-sec reveal" aria-labelledby="lm-chart">
      <div class="lm-sec__head"><h2 id="lm-chart">Chart</h2><p>Choose a symbol or type any ticker, compare two, add indicators, or show two or four charts.</p></div>
      <div class="lm-picks" data-tv-picks="lm-chart-slot" hidden></div>
      <div class="lm-charts" data-tv-charts data-n="1">
        {slot("chart", "Chart", ' id="lm-chart-slot" data-tv-main')}
        {slot("chart", "Second chart", ' data-tv-chart-n="2" hidden')}
        {slot("chart", "Third chart", ' data-tv-chart-n="3" hidden')}
        {slot("chart", "Fourth chart", ' data-tv-chart-n="4" hidden')}
      </div>
    </section>
    <section class="lm-sec reveal" aria-labelledby="lm-about">
      <div class="lm-sec__head"><h2 id="lm-about">In the chart</h2><p data-tv-no-share>Choose a share above to see its figures, its profile and its news here.</p></div>
      {slot("info", "The symbol in the chart", ' data-tv-follow')}
      <div class="lm-pair lm-pair--even" data-tv-share hidden>
        <div class="lm-sub"><h3>Fundamentals</h3>{slot("financials", "Fundamentals of the company in the chart", ' data-tv-follow')}</div>
        <div class="lm-sub"><h3>Profile</h3>{slot("profile", "Profile of the company in the chart", ' data-tv-follow')}</div>
      </div>
    </section>
    <section class="lm-sec reveal" aria-labelledby="lm-quotes">
      <div class="lm-sec__head"><h2 id="lm-quotes">Quotes</h2><p>Last, change, open, high, low and previous close.</p></div>
      {slot("quotes", "Quotes: indices, currencies, commodities, bond futures and crypto")}
    </section>
    <div class="lm-pair">
      <section class="lm-sec reveal" aria-labelledby="lm-overview">
        <div class="lm-sec__head"><h2 id="lm-overview">Market overview</h2></div>
        {slot("overview", "Market overview: indices, FX, commodities and bonds")}
      </section>
      <section class="lm-sec reveal" style="--i:1" aria-labelledby="lm-focus">
        <div class="lm-sec__head"><h2 id="lm-focus">In focus</h2></div>
        {slot("symbol", "Index in focus")}
      </section>
    </div>
    <div class="lm-pair">
      <section class="lm-sec reveal" aria-labelledby="lm-movers">
        <div class="lm-sec__head"><h2 id="lm-movers">Movers</h2>{switch("lm-movers-slot", "movers", "Market whose movers are shown", "movers")}</div>
        {slot("movers", "Most active, gainers and losers", ' id="lm-movers-slot"')}
      </section>
      <section class="lm-sec reveal" style="--i:1" aria-labelledby="lm-news">
        <div class="lm-sec__head"><h2 id="lm-news">News</h2><p>Headlines from TradingView: the market's, or the share's in the chart.</p></div>
        {slot("news", "Headlines from TradingView", ' data-tv-follow')}
      </section>
    </div>
    <section class="lm-sec reveal" aria-labelledby="lm-heat">
      <div class="lm-sec__head"><h2 id="lm-heat">Heatmap</h2><p>In an index's map, choose a company to open its page in Companies.</p>
        {switch("lm-heatmap", "heatmaps", "Market shown in the heatmap", "heatmap")}</div>
      {slot("heatmap", "Heatmap", ' id="lm-heatmap"')}
    </section>
    <section class="lm-sec reveal" aria-labelledby="lm-econ">
      <div class="lm-sec__head"><h2 id="lm-econ">World economy</h2><p>Each country by its GDP, unemployment, government debt, interest rate or inflation.</p></div>
      {slot("econ", "World economy map")}
    </section>
    <section class="lm-sec reveal" aria-labelledby="lm-fx">
      <div class="lm-sec__head"><h2 id="lm-fx">Currencies</h2><p>Each row's currency against each column's.</p>
        {switch("lm-fx-slot", "fx.views", "View of the currencies table")}</div>
      {slot("fx", "Currencies against each other", ' id="lm-fx-slot"')}
    </section>
    <section class="lm-sec reveal" aria-labelledby="lm-screen">
      <div class="lm-sec__head"><h2 id="lm-screen">Screener</h2><p>Every listed share of a market: sort by a column, or filter.</p>
        {switch("lm-screen-slot", "screeners", "Market shown in the screener", "screener")}</div>
      {slot("screener", "Share screener", ' id="lm-screen-slot"')}
    </section>
    <p class="lm-note">Market data provided by <a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank">TradingView</a>. Some markets may be delayed. The widgets load from TradingView, under its own terms and privacy policy; see <a href="../privacy/#hosting">Privacy and cookies</a>. For information only, not investment advice.</p>
    <noscript><p class="lm-note">Live Markets needs JavaScript: its quotes and charts are drawn by TradingView's widgets.</p></noscript>
  </div>
</main>"""
    # Where a company clicked in a heatmap lands: assets/company-go.js sends it on to its page.
    go = site.shell(
        title="Opening the company: Andra Markets", desc="Opening the company's page.",
        body='<main id="main" class="page"><div class="wrap"><header class="page__head">'
             '<h1 class="page__title">Companies</h1><p class="lede">Opening the company. If nothing happens, go to '
             '<a class="link" href="../">Companies</a>.</p></header></div></main>',
        home="../../", base="../../", path="companies/go/", scripts=("search-index.js", "company-go.js"),
        scene=False, index=False)
    return {"companies/go/": go, "live-markets/": site.shell(
        title="Live Markets: Andra Markets",
        desc="Live quotes and charts for indices, shares, currencies, commodities, bonds and crypto, with movers, "
             "heatmaps, a screener and each company's figures. Market data by TradingView.",
        body=body, home="../", base="../", path="live-markets/", scripts=(CONFIG, "markets.js"),
        head=f'\n<link rel="stylesheet" href="../assets/markets.css?v={site.ver("markets.css")}">')}
