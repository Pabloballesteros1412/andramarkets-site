// Live Markets (live-markets/): mounts TradingView's free widgets in the page's
// own frames. Symbols come from assets/markets-config.js.
//
// Every element with data-tv="tape|chart|overview|symbol|heatmap" is a slot. A
// slot is mounted when it comes near the screen, shows a skeleton until its
// frame has loaded, and is unmounted and mounted again when the page's theme
// changes, so each widget always matches the ground it stands on.
//
//   AndraMarkets.mount(el)    build the widget in a slot
//   AndraMarkets.unmount(el)  take it out again
//   AndraMarkets.refresh()    remount every mounted slot (theme or tokens changed)
//   AndraMarkets.theme()      "dark" or "light", read from the page
(function () {
  "use strict";
  var CFG = window.ANDRA_MARKETS;
  if (!CFG) return;
  var root = document.documentElement;
  var SRC = "https://s3.tradingview.com/external-embedding/embed-widget-";
  var WEB = "https://widgets.tradingview-widget.com/w/" + (CFG.locale || "en") + "/tv-";

  // The row of mini charts: one slot for each of the config's minis, made here so the list
  // lives in the config alone.
  [].forEach.call(document.querySelectorAll("[data-tv-minis]"), function (row) {
    (CFG.minis || []).forEach(function (m) {
      var el = document.createElement("div");
      el.className = "tv tv--mini";
      el.setAttribute("data-tv", "mini");
      el.setAttribute("data-tv-symbol", m[0]);
      el.innerHTML = '<div class="tv__frame" role="group"></div><p class="tv__fail">Not loaded.</p>';
      el.firstChild.setAttribute("aria-label", m[1]);
      row.appendChild(el);
    });
  });
  // The charts beside the main one, each on its own symbol until the reader changes it.
  [].forEach.call(document.querySelectorAll("[data-tv-chart-n]"), function (el) {
    var n = +el.getAttribute("data-tv-chart-n"), list = (CFG.chart && CFG.chart.layout) || [];
    if (!el.getAttribute("data-tv-symbol") && list[n - 1]) el.setAttribute("data-tv-symbol", list[n - 1]);
  });
  var slots = [].slice.call(document.querySelectorAll("[data-tv]"));
  if (!slots.length) return;

  // The theme the page is drawn in: its used colour scheme, so the widgets
  // follow the stylesheet and not a guess about data-theme.
  function theme() {
    var scheme = getComputedStyle(root).colorScheme || "";
    if (/dark/.test(scheme)) return "dark";
    if (/light/.test(scheme)) return "light";
    return root.getAttribute("data-theme") === "light" ? "light" : "dark";
  }

  function token(name, fallback) {
    return getComputedStyle(root).getPropertyValue(name).trim() || fallback;
  }

  // "#rrggbb" at an opacity, for the fills under a line.
  function alpha(hex, a) {
    var m = /^#([0-9a-f]{6})$/i.exec(hex);
    if (!m) return hex;
    var n = parseInt(m[1], 16);
    return "rgba(" + (n >> 16) + "," + ((n >> 8) & 255) + "," + (n & 255) + "," + a + ")";
  }

  function tokens() {
    var up = token("--up", "#1fd27a"), down = token("--down", "#ff4b52");
    return {
      up: up, down: down, ink: token("--ink", "#f2f3f3"), ink2: token("--ink-2", "#a3a8aa"),
      grid: token("--chart-grid", "rgba(242,243,243,.08)"), font: token("--font", "sans-serif").replace(/"/g, ""),
      upFill: alpha(up, 0.16), downFill: alpha(down, 0.16), upNone: alpha(up, 0), downNone: alpha(down, 0),
      inkFill: alpha(token("--ink", "#f2f3f3"), 0.1), inkNone: alpha(token("--ink", "#f2f3f3"), 0)
    };
  }

  // One widget: [TradingView's script name, its settings].
  var BUILD = {
    tape: function (el, th) {
      return ["ticker-tape", {
        symbols: CFG.tape.map(function (s) { return { proName: s[0], title: s[1] }; }),
        showSymbolLogo: false, isTransparent: true, displayMode: "regular", colorTheme: th, locale: CFG.locale
      }];
    },
    chart: function (el, th, t) {
      var c = CFG.chart, wide = el.clientWidth >= 900;
      return ["advanced-chart", {
        autosize: true, symbol: el.getAttribute("data-tv-symbol") || c.symbol, interval: c.interval || "D", timezone: c.timezone || "Etc/UTC",
        theme: th, style: "1", locale: CFG.locale, allow_symbol_change: true, withdateranges: true,
        hide_side_toolbar: !wide, details: false, hotlist: false, calendar: false, save_image: false,
        watchlist: wide && c.watchlist ? c.watchlist : [],
        backgroundColor: th === "dark" ? "rgba(0, 0, 0, 1)" : "rgba(255, 255, 255, 1)", gridColor: t.grid,
        studies: studies(),
        compareSymbols: el.getAttribute("data-tv-compare") ? [{ symbol: el.getAttribute("data-tv-compare"), position: "SameScale" }] : [],
        support_host: "https://www.tradingview.com"
      }];
    },
    mini: function (el, th, t) {
      return ["mini-symbol-overview", plain(th, {
        symbol: el.getAttribute("data-tv-symbol"), dateRange: "1D", chartOnly: false, noTimeScale: true,
        // the line in ink: TradingView colours the change itself, as a rise or a fall
        trendLineColor: t.ink, underLineColor: t.inkFill, underLineBottomColor: t.inkNone
      })];
    },
    quotes: function (el, th) {
      return ["market-quotes", plain(th, {
        showSymbolLogo: false,
        symbolsGroups: CFG.quotes.map(function (g) {
          return { name: g.name, symbols: g.symbols.map(function (s) { return { name: s[0], displayName: s[1] }; }) };
        })
      })];
    },
    // TradingView's newer kind of widget: an element of its own, not a frame from a script.
    econ: function (el, th) {
      return ["@economic-map", { region: CFG.economy.region || "global", metric: CFG.economy.metric || "gdp", theme: th, transparent: "" }];
    },
    overview: function (el, th, t) {
      return ["market-overview", {
        colorTheme: th, isTransparent: true, locale: CFG.locale, width: "100%", height: "100%",
        // The chart above the list draws its dates in TradingView's own serif face, which no
        // setting changes: kept as it is at the owner's word (25 Nov 2026).
        dateRange: "12M", showChart: true, showSymbolLogo: false, showFloatingTooltip: false,
        plotLineColorGrowing: t.up, plotLineColorFalling: t.down, gridLineColor: t.grid, scaleFontColor: t.ink2,
        belowLineFillColorGrowing: t.upFill, belowLineFillColorFalling: t.downFill,
        belowLineFillColorGrowingBottom: t.upNone, belowLineFillColorFallingBottom: t.downNone,
        symbolActiveColor: t.inkFill,
        tabs: CFG.overview.map(function (tab) {
          return { title: tab.title, symbols: tab.symbols.map(function (s) { return { s: s[0], d: s[1] }; }) };
        })
      }];
    },
    symbol: function (el, th, t) {
      return ["symbol-overview", {
        symbols: [[CFG.featured[0], CFG.featured[1] + "|12M"]],
        colorTheme: th, isTransparent: true, locale: CFG.locale, width: "100%", height: "100%", autosize: true,
        chartOnly: false, showVolume: false, hideDateRanges: false, hideMarketStatus: false, hideSymbolLogo: true,
        scalePosition: "right", scaleMode: "Normal", fontFamily: t.font, fontSize: "10", fontColor: t.ink2,
        noTimeScale: false, valuesTracking: "1", changeMode: "price-and-percent", chartType: "area",
        lineColor: t.ink, topColor: t.inkFill, bottomColor: t.inkNone, lineWidth: 1, gridLineColor: t.grid,
        upColor: t.up, downColor: t.down, borderUpColor: t.up, borderDownColor: t.down,
        wickUpColor: t.up, wickDownColor: t.down,
        dateRanges: ["1d|1", "1m|30", "3m|60", "12m|1D", "60m|1W", "all|1M"]
      }];
    },
    heatmap: function (el, th) {
      var source = chosen(el, CFG.heatmaps), kind = source[2] || "stock";
      var map = {
        dataSource: source[1], blockColor: "change", colorTheme: th, locale: CFG.locale, width: "100%", height: "100%",
        hasTopBar: false, isDataSetEnabled: false, isZoomEnabled: false, hasSymbolTooltip: true, isMonoSize: false
      };
      if (kind === "crypto") {
        map.blockSize = "market_cap_calc"; map.blockColor = "24h_close_change|5";
        return ["crypto-coins-heatmap", map];
      }
      if (kind === "etf") {
        map.blockSize = "volume"; map.grouping = "asset_class";
        return ["etf-heatmap", map];
      }
      map.blockSize = "market_cap_basic"; map.grouping = "sector";
      // A company clicked in the map opens its page in Companies (companies/go/ finds it).
      map.symbolUrl = new URL((document.body.getAttribute("data-base") || "") + "companies/go/", location.href).href +
        "?x={tvexchange}&s={tvsymbol}";
      return ["stock-heatmap", map];
    },
    // The symbol the chart shows: its quote line, and for a share its figures and profile.
    info: function (el, th) { return ["symbol-info", plain(th, { symbol: symbolOf(el) })]; },
    financials: function (el, th) { return ["financials", plain(th, { symbol: symbolOf(el), displayMode: "regular", largeChartUrl: "" })]; },
    profile: function (el, th) { return ["symbol-profile", plain(th, { symbol: symbolOf(el) })]; },
    // TradingView's headlines: the symbol's when it is a share, the market's otherwise.
    news: function (el, th) {
      var s = symbolOf(el);
      return ["timeline", plain(th, isShare(s) ? { feedMode: "symbol", symbol: s, displayMode: "regular" }
                                              : { feedMode: "all_symbols", displayMode: "regular" })];
    },
    movers: function (el, th, t) {
      return ["hotlists", plain(th, {
        exchange: chosen(el, CFG.movers)[1], dateRange: "12M", showChart: false, showSymbolLogo: false,
        showFloatingTooltip: false, plotLineColorGrowing: t.up, plotLineColorFalling: t.down, symbolActiveColor: t.inkFill
      })];
    },
    fx: function (el, th) {
      return [chosen(el, CFG.fx.views)[1], plain(th, { currencies: CFG.fx.currencies })];
    },
    screener: function (el, th) {
      return ["screener", plain(th, {
        market: chosen(el, CFG.screeners)[1], defaultColumn: CFG.screenerColumns || "performance",
        defaultScreen: "most_capitalized", showToolbar: true
      })];
    }
  };

  // The entry of a config list that a slot's chips have chosen (the first until one is).
  function chosen(el, list) { return list[+el.getAttribute("data-tv-source") || 0] || list[0]; }
  function plain(th, more) {
    var cfg = { colorTheme: th, isTransparent: true, locale: CFG.locale, width: "100%", height: "100%" };
    for (var k in more) cfg[k] = more[k];
    return cfg;
  }
  function symbolOf(el) { return el.getAttribute("data-tv-symbol") || CFG.chart.symbol; }
  // A share has figures, a profile and news of its own: a listing on a stock exchange, or a
  // bare ticker ("AAPL"). Indices, currencies, futures and crypto here come from other sources.
  var SHARES = /^(NASDAQ|NYSE|AMEX|BATS|BME|XETR|FWB|LSE|MIL|EURONEXT|SIX|OMXSTO|OMXCOP|OMXHEX|TSX|TSE|HKEX|ASX|NSE|BSE|KRX|TWSE|BMFBOVESPA|BMV):/;
  function isShare(symbol) { return SHARES.test(symbol) || /^[A-Z][A-Z.]{0,4}$/.test(symbol); }

  function unmount(el) {
    if (el._tvWatch) { el._tvWatch.disconnect(); el._tvWatch = null; }
    clearTimeout(el._tvWait);
    var frame = el.querySelector(".tv__frame");
    if (frame) frame.textContent = "";
    el.classList.remove("is-mounted", "is-ready", "is-failed");
  }

  function mount(el) {
    var build = BUILD[el.getAttribute("data-tv")];
    var frame = el.querySelector(".tv__frame");
    if (!build || !frame) return;
    unmount(el);
    var made = build(el, theme(), tokens());
    if (made[0].charAt(0) === "@") return mountElement(el, frame, made[0].slice(1), made[1]);
    var box = document.createElement("div");
    box.className = "tradingview-widget-container";
    var inner = document.createElement("div");
    inner.className = "tradingview-widget-container__widget";
    var script = document.createElement("script");
    script.src = SRC + made[0] + ".js";
    script.async = true;
    script.text = JSON.stringify(made[1]);
    script.onerror = function () { fail(el); };
    box.appendChild(inner);
    box.appendChild(script);
    el.classList.add("is-mounted");

    // The skeleton stays until the widget's frame has loaded and drawn.
    function ready(iframe) {
      if (el._tvWatch) { el._tvWatch.disconnect(); el._tvWatch = null; }
      iframe.addEventListener("load", function () {
        clearTimeout(el._tvWait);
        el._tvWait = setTimeout(function () { el.classList.add("is-ready"); }, 500);
      });
    }
    el._tvWatch = new MutationObserver(function () {
      var iframe = box.querySelector("iframe");
      if (iframe) ready(iframe);
    });
    el._tvWatch.observe(box, { childList: true, subtree: true });
    el._tvWait = setTimeout(function () { if (!el.classList.contains("is-ready")) fail(el); }, 15000);
    frame.appendChild(box);
  }

  // A widget that is an element (<tv-economic-map>): its module is loaded once, the element is
  // made with its settings as attributes, and it draws itself inside its own closed shadow.
  var modules = {};
  function mountElement(el, frame, name, attrs) {
    if (!modules[name]) {
      var s = document.createElement("script");
      s.type = "module";
      s.src = WEB + name + ".js";
      s.onerror = function () { fail(el); };
      document.head.appendChild(s);
      modules[name] = true;
    }
    var w = document.createElement("tv-" + name);
    for (var k in attrs) w.setAttribute(k, attrs[k]);
    w.style.display = "block";
    w.style.height = "100%";
    frame.appendChild(w);
    el.classList.add("is-mounted");
    var waited = 0;
    (function check() {
      if (!el.contains(w)) return;
      if (window.customElements && customElements.get("tv-" + name)) {
        el._tvWait = setTimeout(function () { el.classList.add("is-ready"); }, 1200);
        return;
      }
      if ((waited += 250) > 15000) { el.classList.add("is-failed"); return; }
      el._tvWait = setTimeout(check, 250);
    })();
  }

  // No frame came (offline, or a blocker stopped TradingView): say so in ink.
  function fail(el) {
    if (el.querySelector("iframe")) { el.classList.add("is-ready"); return; }
    el.classList.add("is-failed");
  }

  function refresh() {
    slots.forEach(function (el) { if (el.classList.contains("is-mounted")) mount(el); });
  }

  // Mount each slot as it comes near the screen. A slot marked data-tv-defer (the homepage's
  // tape) waits until the page has loaded and its opening has had the frame to itself.
  var deferred = slots.filter(function (el) { return el.hasAttribute("data-tv-defer"); });
  // The extra charts are mounted when the reader asks for them (the layout chips), not on scroll.
  var watched = slots.filter(function (el) { return deferred.indexOf(el) < 0 && !el.hasAttribute("data-tv-chart-n"); });
  if (deferred.length) {
    var later = function () { setTimeout(function () { deferred.forEach(mount); }, 1400); };
    if (document.readyState === "complete") later(); else window.addEventListener("load", later);
  }
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        // the mini charts are one row that scrolls sideways on phones: they come in together
        var group = entry.target.getAttribute("data-tv") === "mini"
          ? [].slice.call(entry.target.parentNode.children) : [entry.target];
        group.forEach(function (el) {
          io.unobserve(el);
          if (!el.classList.contains("is-mounted")) mount(el);
        });
      });
    }, { rootMargin: "320px 0px" });
    watched.forEach(function (el) { io.observe(el); });
  } else {
    watched.forEach(mount);
  }

  // The page's theme changed: every mounted widget is built again in it.
  var current = theme();
  function themeMayHaveChanged() {
    var now = theme();
    if (now === current) return;
    current = now;
    refresh();
  }
  new MutationObserver(themeMayHaveChanged).observe(root, { attributes: true, attributeFilter: ["data-theme", "class", "style"] });
  if (window.matchMedia) {
    var mq = window.matchMedia("(prefers-color-scheme: dark)");
    if (mq.addEventListener) mq.addEventListener("change", themeMayHaveChanged);
  }

  // The chart shows its tools and watchlist only on wide screens: build it again
  // when the page crosses that width.
  var resizeWait;
  function wideCharts() {
    [].forEach.call(document.querySelectorAll('[data-tv="chart"]'), function (c) { c._wide = c.clientWidth >= 900; });
  }
  wideCharts();
  window.addEventListener("resize", function () {
    clearTimeout(resizeWait);
    resizeWait = setTimeout(function () {
      [].forEach.call(document.querySelectorAll('[data-tv="chart"]'), function (c) {
        var wide = c.clientWidth >= 900;
        if (wide === c._wide) return;
        c._wide = wide;
        if (c.classList.contains("is-mounted")) mount(c);
      });
    }, 250);
  });

  // The indicators drawn on every chart: those the reader has switched on, the config's
  // defaults until then.
  var INDICATORS = (CFG.chart && CFG.chart.indicators) || [];
  var on = INDICATORS.map(function (d) { return !!d[2]; });
  function studies() {
    // all in one form: the chart drops names given beside studies given with settings
    return INDICATORS.filter(function (d, i) { return on[i]; })
      .map(function (d) { return typeof d[1] === "string" ? { id: d[1] } : d[1]; });
  }
  function eachChart(fn) {
    [].forEach.call(document.querySelectorAll('[data-tv="chart"]'), function (c) {
      if (c.classList.contains("is-mounted")) fn(c);
    });
  }

  // Chips that choose what a slot shows (which heatmap, which market's movers...): one chip
  // for each entry of the config list the group names, the first chosen.
  [].forEach.call(document.querySelectorAll("[data-tv-switch]"), function (group) {
    var target = document.getElementById(group.getAttribute("data-tv-switch"));
    var list = group.getAttribute("data-tv-list").split(".").reduce(function (o, k) { return o && o[k]; }, CFG);
    if (!target || !list || list.length < 2) return;
    var what = group.getAttribute("data-tv-what") || "";
    list.forEach(function (entry, i) {
      var chip = document.createElement("button");
      chip.type = "button";
      chip.className = "chip";
      chip.textContent = entry[0];
      chip.setAttribute("aria-pressed", i === 0 ? "true" : "false");
      chip.addEventListener("click", function () {
        if ((+target.getAttribute("data-tv-source") || 0) === i) return;
        [].forEach.call(group.children, function (c) { c.setAttribute("aria-pressed", c === chip ? "true" : "false"); });
        target.setAttribute("data-tv-source", i);
        var frame = target.querySelector(".tv__frame");
        if (frame) frame.setAttribute("aria-label", (entry[0] + " " + what).trim());
        if (target.classList.contains("is-mounted")) mount(target);
      });
      group.appendChild(chip);
    });
    group.hidden = false;
  });

  // The symbol the reader chose: the chart and every slot that follows it (data-tv-follow) are
  // built again on it. What only a share has is shown for a share and put away otherwise.
  function setSymbol(symbol, remount) {
    [].forEach.call(document.querySelectorAll("[data-tv-main], [data-tv-follow]"), function (el) {
      el.setAttribute("data-tv-symbol", symbol);
      if (remount && el.classList.contains("is-mounted")) mount(el);
    });
    var share = isShare(symbol);
    [].forEach.call(document.querySelectorAll("[data-tv-share]"), function (el) { el.hidden = !share; });
    [].forEach.call(document.querySelectorAll("[data-tv-no-share]"), function (el) { el.hidden = share; });
  }
  setSymbol(CFG.chart.symbol, false);

  // What the chart shows: a chip for each of the config's picks, and a field for any other
  // ticker ("AAPL", "BME:SAN"). Either builds the chart again on that symbol.
  [].forEach.call(document.querySelectorAll("[data-tv-picks]"), function (box) {
    var target = document.getElementById(box.getAttribute("data-tv-picks"));
    var picks = (CFG.chart && CFG.chart.picks) || [];
    if (!target || !picks.length) return;
    var group = document.createElement("div");
    group.className = "filters lm-switch";
    group.setAttribute("role", "group");
    group.setAttribute("aria-label", "Symbol shown in the chart");
    function show(symbol) {
      [].forEach.call(group.children, function (c) {
        c.setAttribute("aria-pressed", c.getAttribute("data-symbol") === symbol ? "true" : "false");
      });
      setSymbol(symbol, true);
      if (!target.classList.contains("is-mounted")) mount(target);
    }
    var start = target.getAttribute("data-tv-symbol") || CFG.chart.symbol;
    picks.forEach(function (pick) {
      var chip = document.createElement("button");
      chip.type = "button";
      chip.className = "chip";
      chip.textContent = pick[0];
      chip.setAttribute("data-symbol", pick[1]);
      chip.setAttribute("aria-pressed", pick[1] === start ? "true" : "false");
      chip.addEventListener("click", function () {
        if (target.getAttribute("data-tv-symbol") !== pick[1]) show(pick[1]);
      });
      group.appendChild(chip);
    });
    var form = document.createElement("form");
    form.className = "lm-find";
    var id = "lm-find-q";
    form.innerHTML = '<label for="' + id + '">Any other ticker</label>' +
      '<input id="' + id + '" type="text" inputmode="latin" autocomplete="off" autocapitalize="characters" ' +
      'spellcheck="false" maxlength="24" placeholder="AAPL, BME:SAN, BTCUSD">' +
      '<button type="submit" class="chip">Show</button>';
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var q = form.querySelector("input"), v = q.value.trim().toUpperCase();
      if (!/^[A-Z0-9][A-Z0-9:._!&-]{0,23}$/.test(v)) { q.focus(); return; }
      show(v);
    });
    box.appendChild(group);
    box.appendChild(form);

    // Compare: a second symbol drawn over the main chart, on the same scale in percent.
    var cmp = document.createElement("form");
    cmp.className = "lm-find lm-find--cmp";
    cmp.innerHTML = '<label for="lm-cmp-q">Compare with</label>' +
      '<input id="lm-cmp-q" type="text" inputmode="latin" autocomplete="off" autocapitalize="characters" ' +
      'spellcheck="false" maxlength="24" placeholder="NASDAQ:NVDA, OANDA:XAUUSD">' +
      '<button type="submit" class="chip">Add</button><button type="button" class="chip lm-clear" hidden>Clear</button>';
    var clear = cmp.querySelector(".lm-clear");
    cmp.addEventListener("submit", function (e) {
      e.preventDefault();
      var q = cmp.querySelector("input"), v = q.value.trim().toUpperCase();
      if (!/^[A-Z0-9][A-Z0-9:._!&-]{0,23}$/.test(v)) { q.focus(); return; }
      target.setAttribute("data-tv-compare", v);
      clear.hidden = false;
      mount(target);
    });
    clear.addEventListener("click", function () {
      target.removeAttribute("data-tv-compare");
      cmp.querySelector("input").value = "";
      clear.hidden = true;
      mount(target);
    });

    var tools = document.createElement("div");
    tools.className = "lm-tools";
    // Indicators: chips that each switch one on or off, on every chart shown.
    if (INDICATORS.length) {
      var ind = document.createElement("div");
      ind.className = "filters lm-switch";
      ind.setAttribute("role", "group");
      ind.setAttribute("aria-label", "Indicators drawn on the charts");
      ind.innerHTML = '<span class="lm-tools__k">Indicators</span>';
      INDICATORS.forEach(function (d, i) {
        var chip = document.createElement("button");
        chip.type = "button";
        chip.className = "chip";
        chip.textContent = d[0];
        chip.setAttribute("aria-pressed", on[i] ? "true" : "false");
        chip.addEventListener("click", function () {
          on[i] = !on[i];
          chip.setAttribute("aria-pressed", on[i] ? "true" : "false");
          eachChart(mount);
        });
        ind.appendChild(chip);
      });
      tools.appendChild(ind);
    }
    // Layout: one chart, two side by side, or four in a square.
    var grid = target.parentNode;
    if (grid && grid.hasAttribute("data-tv-charts")) {
      var lay = document.createElement("div");
      lay.className = "filters lm-switch lm-layout";
      lay.setAttribute("role", "group");
      lay.setAttribute("aria-label", "How many charts");
      lay.innerHTML = '<span class="lm-tools__k">Charts</span>';
      [1, 2, 4].forEach(function (n) {
        var chip = document.createElement("button");
        chip.type = "button";
        chip.className = "chip";
        chip.textContent = n;
        chip.setAttribute("aria-label", n === 1 ? "One chart" : n + " charts");
        chip.setAttribute("aria-pressed", n === 1 ? "true" : "false");
        chip.addEventListener("click", function () {
          if (+grid.getAttribute("data-n") === n) return;
          [].forEach.call(lay.querySelectorAll(".chip"), function (c) { c.setAttribute("aria-pressed", c === chip ? "true" : "false"); });
          grid.setAttribute("data-n", n);
          [].forEach.call(grid.querySelectorAll("[data-tv-chart-n]"), function (c) {
            var show = +c.getAttribute("data-tv-chart-n") <= n;
            if (show === !c.hidden) return;
            c.hidden = !show;
            if (!show) unmount(c);
          });
          // every chart shown is drawn again at its new width
          requestAnimationFrame(function () {
            [].forEach.call(grid.querySelectorAll('[data-tv="chart"]'), function (c) {
              if (!c.hidden) { c._wide = c.clientWidth >= 900; mount(c); }
            });
          });
        });
        lay.appendChild(chip);
      });
      tools.appendChild(lay);
    }
    box.appendChild(cmp);
    box.appendChild(tools);
    box.hidden = false;
  });

  window.AndraMarkets = { mount: mount, unmount: unmount, refresh: refresh, theme: theme };
})();
