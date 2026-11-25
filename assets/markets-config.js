// Live Markets (live-markets/): every symbol the TradingView widgets show.
// Add, remove or reorder lines here; nothing else needs to change.
//
// A symbol is "EXCHANGE:TICKER" as TradingView writes it (search for the
// instrument on tradingview.com and copy it from the page). Not every symbol is
// open to the free widgets: the official index feeds TVC:IBEX35, TVC:SX5E,
// TVC:DEU40 and TVC:NI225 answer "only available on TradingView", so those
// indices use a broker's quote of the same index instead. Government bond
// yields (TVC:DE10Y, TVC:US10Y...) are closed to them too: bonds are shown by
// their Eurex futures, which are prices, not yields (a future rises when the
// yield falls).
window.ANDRA_MARKETS = {
  locale: "en",

  // The tape under the header: [symbol, name shown].
  tape: [
    ["FOREXCOM:SPXUSD", "S&P 500"],
    ["FOREXCOM:NSXUSD", "Nasdaq 100"],
    ["OANDA:EU50EUR", "Euro Stoxx 50"],
    ["BME:IBC", "IBEX 35"],
    ["FX_IDC:EURUSD", "EUR/USD"],
    ["TVC:UKOIL", "Brent"],
    ["OANDA:XAUUSD", "Gold"],
    ["EUREX:FGBL1!", "Bund 10Y future"],
    ["BITSTAMP:BTCUSD", "Bitcoin"]
  ],

  // The large chart. It opens on `symbol`; the reader changes it with the chips
  // above the chart (`picks`: [name shown, symbol]), by typing any ticker in the
  // field beside them, or from the chart's own search.
  chart: {
    symbol: "FOREXCOM:SPXUSD",
    interval: "D",
    timezone: "Europe/Madrid",
    picks: [
      ["S&P 500", "FOREXCOM:SPXUSD"],
      ["Nasdaq 100", "FOREXCOM:NSXUSD"],
      ["Euro Stoxx 50", "OANDA:EU50EUR"],
      ["IBEX 35", "CAPITALCOM:SP35"],
      ["Nvidia", "NASDAQ:NVDA"],
      ["Apple", "NASDAQ:AAPL"],
      ["Microsoft", "NASDAQ:MSFT"],
      ["Alphabet", "NASDAQ:GOOGL"],
      ["Amazon", "NASDAQ:AMZN"],
      ["Meta", "NASDAQ:META"],
      ["Tesla", "NASDAQ:TSLA"],
      ["EUR/USD", "FX_IDC:EURUSD"],
      ["Gold", "OANDA:XAUUSD"],
      ["Brent", "TVC:UKOIL"],
      ["Bitcoin", "BITSTAMP:BTCUSD"]
    ],
    // The list at the chart's right on wide screens.
    watchlist: [
      "FOREXCOM:SPXUSD", "FOREXCOM:NSXUSD", "OANDA:EU50EUR", "CAPITALCOM:SP35",
      "NASDAQ:NVDA", "NASDAQ:AAPL", "NASDAQ:MSFT", "NASDAQ:GOOGL", "NASDAQ:AMZN", "NASDAQ:META", "NASDAQ:TSLA",
      "FX_IDC:EURUSD", "TVC:UKOIL", "OANDA:XAUUSD", "EUREX:FGBL1!", "BITSTAMP:BTCUSD"
    ]
  },

  // Market overview: one tab per entry, [symbol, name shown] in each.
  overview: [
    { title: "Indices", symbols: [
      ["FOREXCOM:SPXUSD", "S&P 500"],
      ["FOREXCOM:NSXUSD", "Nasdaq 100"],
      ["OANDA:EU50EUR", "Euro Stoxx 50"],
      ["OANDA:DE30EUR", "DAX"],
      ["BME:IBC", "IBEX 35"],
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
      ["EUREX:FGBL1!", "Germany 10Y, Bund future"],
      ["EUREX:FGBM1!", "Germany 5Y, Bobl future"],
      ["EUREX:FGBS1!", "Germany 2Y, Schatz future"],
      ["EUREX:FBTP1!", "Italy 10Y, BTP future"],
      ["EUREX:FOAT1!", "France 10Y, OAT future"],
      ["NASDAQ:TLT", "US Treasuries 20Y+, ETF"]
    ] }
  ],

  // The index in focus beside the overview: [name shown, symbol].
  featured: ["S&P 500", "FOREXCOM:SPXUSD"],

  // Heatmaps, one chip each: [chip label, TradingView's name for the index].
  // Others TradingView offers: "NASDAQ100", "DAX", "SX5E", "UK100", "CAC40".
  heatmaps: [
    ["S&P 500", "SPX500"],
    ["IBEX 35", "IBEX35"]
  ]
};
