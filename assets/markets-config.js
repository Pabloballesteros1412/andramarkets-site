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
    // Indicators the reader can switch on: [chip label, TradingView's study, true to have it
    // on at first]. The chart opens clean (owner, 27 Nov 2026).
    // A study is TradingView's name for it ("RSI@tv-basicstudies"), or one with its
    // settings ({ id, inputs }).
    indicators: [
      ["MA 50", { id: "MASimple@tv-basicstudies", inputs: { length: 50 } }],
      ["MA 200", { id: "MASimple@tv-basicstudies", inputs: { length: 200 } }],
      ["Bollinger", "BB@tv-basicstudies"],
      ["RSI", "RSI@tv-basicstudies"],
      ["MACD", "MACD@tv-basicstudies"],
      ["Stoch RSI", "StochasticRSI@tv-basicstudies"]
    ],
    // The charts beside the main one when the reader shows two or four: [symbol, name]. The
    // first place is the main chart's. These are plain charts, for a glance across markets;
    // "Analyse" opens one alone with every tool.
    layout: [
      ["FOREXCOM:SPXUSD", "S&P 500"],
      ["FOREXCOM:NSXUSD", "Nasdaq 100"],
      ["OANDA:XAUUSD", "Gold"],
      ["BITSTAMP:BTCUSD", "Bitcoin"]
    ],
    // The list at the chart's right on wide screens.
    watchlist: [
      "FOREXCOM:SPXUSD", "FOREXCOM:NSXUSD", "OANDA:EU50EUR", "CAPITALCOM:SP35",
      "NASDAQ:NVDA", "NASDAQ:AAPL", "NASDAQ:MSFT", "NASDAQ:GOOGL", "NASDAQ:AMZN", "NASDAQ:META", "NASDAQ:TSLA",
      "FX_IDC:EURUSD", "TVC:UKOIL", "OANDA:XAUUSD", "EUREX:FGBL1!", "BITSTAMP:BTCUSD"
    ]
  },

  // The row of mini charts at the top of the page: [symbol, name for screen readers].
  minis: [
    ["FOREXCOM:SPXUSD", "S&P 500"],
    ["FOREXCOM:NSXUSD", "Nasdaq 100"],
    ["OANDA:EU50EUR", "Euro Stoxx 50"],
    ["OANDA:XAUUSD", "Gold"],
    ["TVC:UKOIL", "Brent"],
    ["BITSTAMP:BTCUSD", "Bitcoin"]
  ],

  // The quotes table, one group of rows each: [symbol, name shown].
  quotes: [
    { name: "Indices", symbols: [
      ["FOREXCOM:SPXUSD", "S&P 500"],
      ["FOREXCOM:NSXUSD", "Nasdaq 100"],
      ["FOREXCOM:DJI", "Dow Jones"],
      ["OANDA:EU50EUR", "Euro Stoxx 50"],
      ["OANDA:DE30EUR", "DAX"],
      ["BME:IBC", "IBEX 35"],
      ["OANDA:UK100GBP", "FTSE 100"],
      ["OANDA:JP225USD", "Nikkei 225"]
    ] },
    { name: "Currencies", symbols: [
      ["FX_IDC:EURUSD", "EUR/USD"],
      ["FX_IDC:GBPUSD", "GBP/USD"],
      ["FX_IDC:USDJPY", "USD/JPY"],
      ["FX_IDC:USDCHF", "USD/CHF"],
      ["FX_IDC:EURGBP", "EUR/GBP"]
    ] },
    { name: "Commodities", symbols: [
      ["TVC:UKOIL", "Brent"],
      ["TVC:USOIL", "WTI"],
      ["OANDA:XAUUSD", "Gold"],
      ["OANDA:XAGUSD", "Silver"],
      ["CAPITALCOM:COPPER", "Copper"],
      ["CAPITALCOM:NATURALGAS", "Natural gas"]
    ] },
    { name: "Bond futures", symbols: [
      ["EUREX:FGBL1!", "Bund 10Y"],
      ["EUREX:FGBM1!", "Bobl 5Y"],
      ["EUREX:FGBS1!", "Schatz 2Y"],
      ["EUREX:FBTP1!", "BTP 10Y"],
      ["EUREX:FOAT1!", "OAT 10Y"]
    ] },
    { name: "Crypto", symbols: [
      ["BITSTAMP:BTCUSD", "Bitcoin"],
      ["BITSTAMP:ETHUSD", "Ether"],
      ["BINANCE:SOLUSDT", "Solana"],
      ["BINANCE:XRPUSDT", "XRP"]
    ] }
  ],

  // The world economy map. The reader picks the measure on the map itself (GDP,
  // unemployment, government debt, interest rate, inflation); this is the first.
  economy: { region: "global", metric: "gdp" },

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

  // Heatmaps, one chip each: [chip label, TradingView's name for the set, kind].
  // kind is "stock" (the default: an index's companies), "crypto" or "etf".
  // Other indices TradingView offers: "DAX", "SX5E", "UK100", "CAC40", "NIKKEI225".
  heatmaps: [
    ["S&P 500", "SPX500"],
    ["Nasdaq 100", "NASDAQ100"],
    ["IBEX 35", "IBEX35"],
    ["Crypto", "Crypto", "crypto"],
    ["ETFs", "AllUSEtf", "etf"]
  ],

  // Movers (most active, gainers, losers), one chip each: [chip label, exchange].
  movers: [
    ["United States", "US"],
    ["Spain", "BME"]
  ],

  // Currencies: the table's currencies, and its two views.
  fx: {
    currencies: ["EUR", "USD", "JPY", "GBP", "CHF", "AUD", "CAD", "CNY"],
    views: [
      ["Day's change", "forex-heat-map"],
      ["Rates", "forex-cross-rates"]
    ]
  },

  // The screener, one chip each: [chip label, TradingView's market]. It opens on
  // the Performance columns; the reader can change them from the screener.
  screeners: [
    ["United States", "america"],
    ["Spain", "spain"],
    ["Germany", "germany"],
    ["United Kingdom", "uk"]
  ],
  screenerColumns: "performance"
};
