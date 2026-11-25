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
import json
import re

CONFIG = "markets-config.js"


def heatmaps(site):
    """The heatmap chips' labels, read from the config so the page and the script agree."""
    text = (site.ROOT / "assets" / CONFIG).read_text(encoding="utf-8")
    m = re.search(r"heatmaps:\s*(\[.*?\])\s*\n\s*\}", text, re.S)
    try:
        rows = json.loads(re.sub(r"//[^\n]*", "", m.group(1))) if m else []
    except ValueError:
        rows = []
    return [r[0] for r in rows if r] or ["IBEX 35", "S&P 500"]


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
    labels = heatmaps(site)
    chips = "".join(
        f'<button type="button" class="chip" data-tv-source="{i}" aria-pressed="{"true" if i == 0 else "false"}">{site.esc(name)}</button>'
        for i, name in enumerate(labels))
    body = f"""<main id="main" class="page lm">
  <div class="lm-tape">{slot("tape", "Quotes tape")}</div>
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Live Markets</h1>
      <p class="lede">Indices, currencies, commodities, bonds and bitcoin as they trade, on TradingView's charts.</p>
    </header>
    <section class="lm-sec reveal" aria-labelledby="lm-chart">
      <div class="lm-sec__head"><h2 id="lm-chart">Chart</h2><p>Change the symbol, the interval or the range from the chart itself.</p></div>
      {slot("chart", "Chart")}
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
    <section class="lm-sec reveal" aria-labelledby="lm-heat">
      <div class="lm-sec__head"><h2 id="lm-heat">Heatmap</h2>
        <div class="filters lm-switch" role="group" aria-label="Index shown in the heatmap" data-tv-switch="lm-heatmap">{chips}</div></div>
      {slot("heatmap", f"{site.esc(labels[0])} heatmap", ' id="lm-heatmap" data-tv-source="0"')}
    </section>
    <p class="lm-note">Market data provided by <a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank">TradingView</a>. Some markets may be delayed. The widgets load from TradingView, under its own terms and privacy policy; see <a href="../privacy/#hosting">Privacy and cookies</a>. For information only, not investment advice.</p>
    <noscript><p class="lm-note">Live Markets needs JavaScript: its quotes and charts are drawn by TradingView's widgets.</p></noscript>
  </div>
</main>"""
    return {"live-markets/": site.shell(
        title="Live Markets: Andra Markets",
        desc="Live quotes and charts for indices, currencies, commodities, bonds and bitcoin, with heatmaps of the "
             "IBEX 35 and the S&P 500. Market data by TradingView.",
        body=body, home="../", base="../", path="live-markets/", scripts=(CONFIG, "markets.js"),
        head=f'\n<link rel="stylesheet" href="../assets/markets.css?v={site.ver("markets.css")}">')}
