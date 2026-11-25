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
        support_host: "https://www.tradingview.com"
      }];
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
      var source = CFG.heatmaps[+el.getAttribute("data-tv-source") || 0] || CFG.heatmaps[0];
      return ["stock-heatmap", {
        dataSource: source[1], blockSize: "market_cap_basic", blockColor: "change", grouping: "sector",
        colorTheme: th, locale: CFG.locale, width: "100%", height: "100%",
        // A company clicked in the map opens its page in Companies (companies/go/ finds it).
        symbolUrl: new URL((document.body.getAttribute("data-base") || "") + "companies/go/", location.href).href +
          "?x={tvexchange}&s={tvsymbol}",
        hasTopBar: false, isDataSetEnabled: false, isZoomEnabled: false, hasSymbolTooltip: true, isMonoSize: false
      }];
    }
  };

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
  slots = slots.filter(function (el) { return deferred.indexOf(el) < 0; });
  if (deferred.length) {
    var later = function () { setTimeout(function () { deferred.forEach(mount); slots = slots.concat(deferred); }, 1400); };
    if (document.readyState === "complete") later(); else window.addEventListener("load", later);
  }
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        io.unobserve(entry.target);
        mount(entry.target);
      });
    }, { rootMargin: "320px 0px" });
    slots.forEach(function (el) { io.observe(el); });
  } else {
    slots.forEach(mount);
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
  var chart = document.querySelector('[data-tv="chart"]');
  if (chart) {
    var wasWide = chart.clientWidth >= 900, resizeWait;
    window.addEventListener("resize", function () {
      clearTimeout(resizeWait);
      resizeWait = setTimeout(function () {
        var wide = chart.clientWidth >= 900;
        if (wide === wasWide) return;
        wasWide = wide;
        if (chart.classList.contains("is-mounted")) mount(chart);
      }, 250);
    });
  }

  // Chips that choose what a slot shows (the heatmap's index).
  [].forEach.call(document.querySelectorAll("[data-tv-switch]"), function (group) {
    var target = document.getElementById(group.getAttribute("data-tv-switch"));
    var chips = [].slice.call(group.querySelectorAll(".chip"));
    if (!target) return;
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        // (site.js may already have pressed the chip: go by what the slot shows)
        if (target.getAttribute("data-tv-source") === chip.getAttribute("data-tv-source")) return;
        chips.forEach(function (c) { c.setAttribute("aria-pressed", c === chip ? "true" : "false"); });
        target.setAttribute("data-tv-source", chip.getAttribute("data-tv-source"));
        var title = target.querySelector(".tv__frame");
        if (title) title.setAttribute("aria-label", chip.textContent.trim() + " heatmap");
        if (target.classList.contains("is-mounted")) mount(target);
      });
    });
  });

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
      target.setAttribute("data-tv-symbol", symbol);
      [].forEach.call(group.children, function (c) {
        c.setAttribute("aria-pressed", c.getAttribute("data-symbol") === symbol ? "true" : "false");
      });
      mount(target);
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
    box.hidden = false;
  });

  window.AndraMarkets = { mount: mount, unmount: unmount, refresh: refresh, theme: theme };
})();
