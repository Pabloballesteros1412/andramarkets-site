// Live Markets (live-markets/): every symbol the TradingView widgets show.
// Add, remove or reorder lines here; nothing else needs to change.
//
// A symbol is "EXCHANGE:TICKER" as TradingView writes it (search for the
// instrument on tradingview.com and copy it from the page). Not every symbol is
// open to the free widgets: the official index feeds TVC:IBEX35, TVC:SX5E,
// TVC:DEU40 and TVC:NI225 answer "only available on TradingView", so those
// indices use a broker's quote of the same index instead.
window.ANDRA_MARKETS = {
  locale: "en",

  // The tape under the header: [symbol, name shown].
  tape: [
    ["BME:IBC", "IBEX 35"],
    ["OANDA:EU50EUR", "Euro Stoxx 50"],
    ["FOREXCOM:SPXUSD", "S&P 500"],
    ["FOREXCOM:NSXUSD", "Nasdaq 100"],
    ["FX_IDC:EURUSD", "EUR/USD"],
    ["TVC:UKOIL", "Brent"],
    ["OANDA:XAUUSD", "Gold"],
    ["TVC:DE10Y", "Germany 10Y"],
    ["BITSTAMP:BTCUSD", "Bitcoin"]
  ],

  // The large chart. The reader can change its symbol from the chart itself.
  chart: {
    symbol: "CAPITALCOM:SP35",
    interval: "D",
    timezone: "Europe/Madrid",
    // The list at the chart's right on wide screens.
    watchlist: [
      "CAPITALCOM:SP35", "OANDA:EU50EUR", "FOREXCOM:SPXUSD", "FOREXCOM:NSXUSD",
      "FX_IDC:EURUSD", "TVC:UKOIL", "OANDA:XAUUSD", "TVC:DE10Y", "BITSTAMP:BTCUSD"
    ]
  },

  // Market overview: one tab per entry, [symbol, name shown] in each.
  overview: [
    { title: "Indices", symbols: [
      ["BME:IBC", "IBEX 35"],
      ["OANDA:EU50EUR", "Euro Stoxx 50"],
      ["OANDA:DE30EUR", "DAX"],
      ["FOREXCOM:SPXUSD", "S&P 500"],
      ["FOREXCOM:NSXUSD", "Nasdaq 100"],
      ["OANDA:JP225USD", "Nikkei 225"]
    ] },
    { title: "FX", symbols: [
      ["FX_IDC:EURUSD", "EUR/USD"],
      ["FX_IDC:GBPUSD", "GBP/USD"],
      ["FX_IDC:USDJPY", "USD/JPY"],
      ["FX_IDC:EURGBP", "EUR/GBP"],
      ["FX_IDC:USDCHF", "USD/CHF"],
      ["FX_IDC:USDMXN", "USD/MXN"]
    ] },
    { title: "Commodities", symbols: [
      ["TVC:UKOIL", "Brent"],
      ["TVC:USOIL", "WTI"],
      ["OANDA:XAUUSD", "Gold"],
      ["OANDA:XAGUSD", "Silver"],
      ["CAPITALCOM:COPPER", "Copper"],
      ["CAPITALCOM:NATURALGAS", "Natural gas"]
    ] },
    { title: "Bonds", symbols: [
      ["TVC:DE10Y", "Germany 10Y"],
      ["TVC:ES10Y", "Spain 10Y"],
      ["TVC:IT10Y", "Italy 10Y"],
      ["TVC:US10Y", "US 10Y"],
      ["TVC:US02Y", "US 2Y"],
      ["TVC:GB10Y", "UK 10Y"]
    ] }
  ],

  // The index in focus beside the overview: [name shown, symbol].
  featured: ["IBEX 35", "CAPITALCOM:SP35"],

  // Heatmaps, one chip each: [chip label, TradingView's name for the index].
  // Others TradingView offers: "NASDAQ100", "DAX", "SX5E", "UK100", "CAC40".
  heatmaps: [
    ["IBEX 35", "IBEX35"],
    ["S&P 500", "SPX500"]
  ]
};
