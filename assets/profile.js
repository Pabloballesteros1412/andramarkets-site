/* Andra Markets companies, live: the search on /companies/, the profile of
   any US company outside the 600 (/companies/live/?t=) and the live price,
   news and analysts on the US pages of the 600, filled from the profile API (worker/, a Cloudflare Worker
   that holds the vendors' keys; its address is in data-api on <main>). Each
   part of the page loads on its own: a skeleton of its shape, then the
   content, or an error that says what failed with a way to try again. Vendor
   text (names, headlines) is only ever set as text, never as HTML.
   Tokens and rules: DESIGN.md, Company pages. */
(function () {
  "use strict";
  var main = document.querySelector("main[data-mode]");
  if (!main) return;
  var API = main.getAttribute("data-api") || "";
  var NS = "http://www.w3.org/2000/svg";
  var MINUS = "−";
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  var TICKER = /^[A-Z][A-Z0-9.-]{0,9}$/;
  var $ = function (id) { return document.getElementById(id); };

  /* ---- Small helpers ---- */
  function h(tag, attrs, kids) {
    var e = document.createElement(tag);
    for (var k in attrs || {}) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    [].concat(kids == null ? [] : kids).forEach(function (c) { if (c != null) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }
  function el(name, attrs, text, parent) {
    var e = document.createElementNS(NS, name);
    for (var k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  }
  function icon(name) {
    var s = el("svg", { "class": "icon", "aria-hidden": "true" });
    el("use", { href: "#i-" + name }, null, s);
    return s;
  }
  function fin(v) { return v != null && isFinite(v); }
  function signed(v, d, unit) {
    var r = Math.abs(v).toFixed(d);
    if (+r === 0) return (0).toFixed(d) + (unit || "");
    return (v > 0 ? "+" : MINUS) + r + (unit || "");
  }
  // A figure that shows a rise or a fall, coloured by its sign (The Rise and Fall Rule).
  function mv(text) {
    var c = text.charAt(0) === "+" ? "mv--up" : text.charAt(0) === MINUS ? "mv--down" : null;
    return h("span", { "class": c }, text);
  }
  function setRead(node, text) {
    node.textContent = "";
    text.split(/([+−]\d[\d,.]*%)/).forEach(function (p) {
      if (!p) return;
      node.appendChild(/^[+−]\d/.test(p) && /%$/.test(p) ? mv(p) : document.createTextNode(p));
    });
  }
  function median(a) {
    var v = a.filter(fin).sort(function (x, y) { return x - y; });
    if (!v.length) return null;
    var m = Math.floor(v.length / 2);
    return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
  }
  function mean(a) {
    var v = a.filter(fin);
    return v.length ? v.reduce(function (s, x) { return s + x; }, 0) / v.length : null;
  }
  var SYM = "$";
  function money(v) {
    if (!fin(v)) return "n/a";
    var a = Math.abs(v), s = v < 0 ? MINUS : "";
    if (a >= 1e12) return s + SYM + (a / 1e12).toFixed(2) + "tn";
    if (a >= 1e9) return s + SYM + (a / 1e9).toFixed(a >= 1e11 ? 0 : 1) + "bn";
    if (a >= 1e6) return s + SYM + (a / 1e6).toFixed(0) + "m";
    return s + SYM + a.toLocaleString("en-US", { maximumFractionDigits: 0 });
  }
  function px(v) { return SYM + v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function x1(v) { return fin(v) ? v.toFixed(1) + "x" : "n/a"; }
  function pct(v, d) { return fin(v) ? v.toFixed(d == null ? 1 : d) + "%" : "n/a"; }
  function day(iso) {
    var p = String(iso).split("-");
    return +p[2] + " " + MONTHS[+p[1] - 1] + " " + p[0];
  }
  function etTime(sec) {
    return new Date(sec * 1000).toLocaleTimeString("en-US", { timeZone: "America/New_York", hour: "numeric", minute: "2-digit" }).replace("AM", "am").replace("PM", "pm");
  }
  function etDay(sec) {
    var d = new Date(sec * 1000).toLocaleDateString("en-GB", { timeZone: "America/New_York", day: "numeric", month: "short" });
    return d.replace("Sept", "Sep");
  }
  function ago(sec) {
    var s = Date.now() / 1000 - sec;
    if (s < 3600) return Math.max(1, Math.round(s / 60)) + " min ago";
    if (s < 86400) return Math.round(s / 3600) + " h ago";
    if (s < 172800) return "Yesterday";
    return etDay(sec);
  }

  /* ---- The API ---- */
  function get(path) {
    return fetch(API + path, { headers: { Accept: "application/json" } }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (d) {
        if (!r.ok || d.error) {
          var e = new Error((d.error && d.error.message) || "The data did not load.");
          e.code = (d.error && d.error.code) || "upstream";
          e.retryAfter = d.error && d.error.retryAfter;
          throw e;
        }
        return d;
      });
    }, function () {
      var e = new Error("The connection failed.");
      e.code = "network";
      throw e;
    });
  }

  /* ---- Parts: loading, content, error ---- */
  var retryTimers = {};
  function state(part, st) { if (part) part.setAttribute("data-st", st); }
  function fail(part, what, err, retry) {
    state(part, "error");
    var box = part.querySelector(".pf-err");
    var head = {
      busy: what + " did not load: the data source is busy.",
      plan: what + " are not in the current data plan.",
      network: what + " did not load: the connection failed.",
      config: "The data service is not set up yet."
    }[err.code] || what + " did not load.";
    var wait = err.code === "busy" ? Math.min(err.retryAfter || 60, 300) : 0;
    var note = err.code === "busy" ? (wait >= 300 ? "The free data allowance is used up for now. Try again later." : "It will try again on its own in " + wait + " seconds.")
      : err.code === "network" ? "Check your connection, then try again."
      : err.code === "plan" ? "Andra Markets uses the free plans of its data sources, which leave this out."
      : "The data source did not answer. Try again in a moment.";
    var btn = err.code === "plan" || err.code === "config" ? null : h("button", { "class": "btn btn--ghost btn--sm", type: "button" }, wait ? "Try again now" : "Try again");
    box.textContent = "";
    box.appendChild(h("div", { "class": "pf-errbox", role: "alert" }, [icon("warning-circle"), h("p", {}, head), h("small", {}, note), btn]));
    var key = part.id;
    clearTimeout(retryTimers[key]);
    if (btn) btn.addEventListener("click", function () { clearTimeout(retryTimers[key]); retry(); });
    if (wait && wait < 300) retryTimers[key] = setTimeout(retry, wait * 1000);
  }
  function hideSection(id) {
    var s = $(id);
    if (s) s.hidden = true;
    var a = document.querySelector('.pf-subnav a[href="#' + id + '"]');
    if (a) a.parentNode.hidden = true;
  }
  function staleNote(part, d) {
    if (!d.stale || !part) return;
    var src = part.querySelector(".co-src") || $("pf-side-src");
    if (src && !src.querySelector(".pf-stale")) src.appendChild(h("span", { "class": "pf-stale" }, " Saved copy from " + day(d.asOf.slice(0, 10)) + ": the data source did not answer just now."));
  }

  /* ---- Modes ----
     index:   /companies/, the search over the 600 and any other US ticker
     live:    /companies/live/?t=TICK, the profile of a company outside the 600
     company: /companies/<ticker>/, a US company of the 600: the live price,
              news and analysts on top of its static page */
  var MODE = main.getAttribute("data-mode");
  var params = new URLSearchParams(location.search);
  var LIVE = MODE === "index" ? "live/" : MODE === "live" ? "./" : "../live/";
  function go(t) { location.href = LIVE + "?t=" + encodeURIComponent(t.toUpperCase()); }

  /* ---- Search (the Companies index) ---- */
  function indexSearch() {
    var form = $("pf-form"), q = $("pf-q"), res = $("pf-res"), more = $("pf-more"), status = $("pf-status");
    var filter = window.andraCoFilter || function () { return []; };
    var known = {};
    [].forEach.call(document.querySelectorAll(".co-tab tbody tr[data-t]"), function (r) { known[r.getAttribute("data-t")] = 1; });
    form.hidden = false;
    var items = [], active = -1, timer, seq = 0, nf = "";
    function render(list) {
      items = list;
      active = -1;
      res.textContent = "";
      list.forEach(function (r, i) {
        var a = h("a", { href: LIVE + "?t=" + encodeURIComponent(r.t), tabindex: "-1" }, [h("b", {}, r.t), h("span", {}, r.name)]);
        res.appendChild(h("li", { role: "option", id: "pf-opt-" + i, "aria-selected": "false" }, a));
      });
      more.hidden = !list.length;
      q.setAttribute("aria-expanded", list.length ? "true" : "false");
      q.removeAttribute("aria-activedescendant");
    }
    function move(i) {
      if (!items.length) return;
      active = (i + items.length) % items.length;
      [].forEach.call(res.children, function (li, k) { li.setAttribute("aria-selected", k === active ? "true" : "false"); });
      q.setAttribute("aria-activedescendant", "pf-opt-" + active);
      res.children[active].scrollIntoView({ block: "nearest" });
    }
    q.addEventListener("input", function () {
      clearTimeout(timer);
      var v = q.value.trim();
      var local = filter(v.toLowerCase());
      if (!v) { render([]); status.textContent = ""; return; }
      if (!API) return;
      timer = setTimeout(function () {
        var my = ++seq;
        get("/search?q=" + encodeURIComponent(v)).then(function (d) {
          if (my !== seq) return;
          var others = (d.results || []).filter(function (r) { return !known[r.t]; });
          render(others);
          status.textContent = local.length || others.length
            ? (nf ? "No US-listed company trades as " + nf + ". These match the name." : "")
            : (nf ? "No US-listed company trades as " + nf + ", and none matches that name." : "No US-listed company matches \u201c" + v + "\u201d. Check the ticker, or try the company\u2019s name.");
          nf = "";
        }, function (e) {
          if (my !== seq) return;
          render([]);
          if (!local.length) status.textContent = e.code === "busy" ? "Search is busy. Press Enter to open " + v.toUpperCase() + " directly, or try again in a minute." : "Search did not answer. Press Enter to open a ticker directly.";
        });
      }, 220);
    });
    q.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); move(active + 1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); move(active - 1); }
      else if (e.key === "Escape") { q.value = ""; q.dispatchEvent(new Event("input")); }
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (active >= 0 && items[active]) return go(items[active].t);
      var v = q.value.trim();
      var row = filter(v.toLowerCase())[0];
      // An exact ticker among the 600 opens its page; else the first match, then the first other company.
      var exact = document.querySelector('.co-tab tbody tr[data-t="' + v.toUpperCase().replace(/[^A-Z0-9.-]/g, "") + '"] a');
      if (exact) return (location.href = exact.getAttribute("href"));
      if (row) return (location.href = row.querySelector("a").getAttribute("href"));
      if (items[0]) return go(items[0].t);
      if (TICKER.test(v.toUpperCase())) go(v);
    });
    var pre = params.get("q");
    if (pre) {
      var t = (params.get("nf") || "").toUpperCase();
      if (TICKER.test(t)) nf = t;
      q.value = pre;
      q.dispatchEvent(new Event("input"));
      q.focus();
    }
  }
  if (MODE === "index") return indexSearch();

  var form2 = $("pf-form2");
  if (form2) form2.addEventListener("submit", function (e) {
    e.preventDefault();
    var v = $("pf-q2").value.trim();
    if (TICKER.test(v.toUpperCase())) go(v);
    else if (v) location.href = "../?q=" + encodeURIComponent(v);
  });

  /* ---- The profile ---- */
  var T, F = null, PEERS = null, QUOTE = null, NAME;
  if (MODE === "company") {
    T = main.getAttribute("data-t");
    NAME = main.getAttribute("data-name");
  } else {
    T = (params.get("t") || "").trim().toUpperCase();
    if (!TICKER.test(T)) { location.replace("../" + (T ? "?q=" + encodeURIComponent(T.toLowerCase()) : "")); return; }
    // One of the 600 has its own page.
    var KNOWN = {};
    try { KNOWN = JSON.parse(main.getAttribute("data-known") || "{}"); } catch (e) { /* none */ }
    if (KNOWN[T]) { location.replace("../" + KNOWN[T] + "/"); return; }
    if (!API) { $("pf-lede").textContent = "The live company profiles are not connected to their data yet."; return; }
    NAME = T;
    [].forEach.call(document.querySelectorAll("[data-part]"), function (p) { state(p, "loading"); });
    $("pf-title").textContent = T;
    document.title = T + ": Companies: Andra Markets";
  }

  function setName(n) {
    NAME = n;
    $("pf-title").textContent = n;
    document.title = n + " (" + T + "): Andra Markets";
    [].forEach.call(document.querySelectorAll(".pf-name"), function (s) { s.textContent = n; });
  }

  // Quote: shown first, refreshed every minute while the page is visible.
  var quotePart = $("pf-quote"), quoteTimer;
  function loadQuote(first) {
    return get("/quote?t=" + T).then(function (d) {
      QUOTE = d;
      showQuote();
    }, function (e) {
      if (e.code === "not_found" && first && MODE === "live") return notFound();
      if (MODE === "company") return; // the static close stays
      if (QUOTE) return; // keep the last price on screen; the next refresh tries again
      fail(quotePart, "The price", e, function () { state(quotePart, "loading"); loadQuote(); });
    });
  }
  function showQuote() {
    var d = QUOTE;
    if (!d) return;
    $("pf-px").textContent = px(d.price);
    var chg = $("pf-chg");
    chg.textContent = "";
    if (fin(d.change) && fin(d.changePct)) {
      chg.appendChild(mv((d.change > 0 ? "+" : d.change < 0 ? MINUS : "") + Math.abs(d.change).toFixed(2)));
      chg.appendChild(document.createTextNode(" ("));
      chg.appendChild(mv(signed(d.changePct, 2, "%")));
      chg.appendChild(document.createTextNode(") on the day"));
    }
    var meta = $("pf-qmeta"), fresh = Date.now() / 1000 - d.time < 15 * 60;
    meta.textContent = "";
    var exch = F && F.profile.exchange ? F.profile.exchange : main.getAttribute("data-exchange");
    var when = (fresh ? "Live, " : "Last price " + etDay(d.time) + ", ") + etTime(d.time) + " ET. " + T + (exch ? ", " + exch : "") + ". Finnhub.";
    // One text run: the meta line is a flex row with gaps between its children.
    meta.appendChild(fresh ? h("span", { "class": "pf-live" }, when) : document.createTextNode(when));
    state(quotePart, "ok");
    peerDay();
    keyFigures();
  }
  function pollQuote() {
    clearInterval(quoteTimer);
    quoteTimer = setInterval(function () { if (!document.hidden) loadQuote(); }, 60000);
  }
  document.addEventListener("visibilitychange", function () { if (!document.hidden && QUOTE) loadQuote(); });

  // "?t=nvidia": no such ticker, so search the name on the Companies index.
  function notFound() {
    clearInterval(quoteTimer);
    location.replace("../?q=" + encodeURIComponent(T.toLowerCase()) + "&nf=" + encodeURIComponent(T));
  }

  // Fundamentals: the head, key figures and every chart and table but peers and news.
  var side = $("pf-side");
  var FUND_PARTS = ["pf-about", "pf-years", "pf-margins", "pf-st", "pf-mult"];
  function loadFund() {
    FUND_PARTS.concat("pf-side").forEach(function (id) { state($(id), "loading"); });
    return get("/fundamentals?t=" + T).then(function (d) {
      F = d;
      SYM = !d.profile.currency || d.profile.currency === "USD" ? "$" : d.profile.currency + " ";
      setName(d.profile.name);
      showQuote();
      $("pf-crumb").textContent = d.profile.sector || "US-listed company";
      drawFund();
      staleNote(side, d);
    }, function (e) {
      if (e.code === "not_found") {
        // The price exists but the fundamentals source has no record (a fund, a new listing).
        FUND_PARTS.forEach(hideSection);
        state(side, "ok");
        $("pf-crumb").textContent = "US-listed";
        $("pf-lede").textContent = "No company profile or financial statements are available for " + T + ": it may be a fund or a recent listing.";
        return;
      }
      fail($("pf-about"), "The company\u2019s figures", e, retryFund);
      state(side, "error");
      var box = side.querySelector(".pf-err");
      box.textContent = "";
      box.appendChild(h("p", { "class": "pf-side-err" }, "Not loaded yet."));
      FUND_PARTS.slice(1).forEach(function (id) { $(id).hidden = true; });
    });
  }
  function retryFund() {
    FUND_PARTS.slice(1).forEach(function (id) { $(id).hidden = false; });
    loadFund();
  }

  function keyFigures() {
    if (!F) return;
    var m = F.metrics || {}, Y = F.years, last = Y[Y.length - 1] || {};
    var price = QUOTE ? QUOTE.price : null;
    var mcap = fin(m.marketCap) ? m.marketCap : F.profile.marketCap;
    function k(id, level, note) {
      $("pf-k-" + id).textContent = level;
      $("pf-k-" + id + "-n").textContent = note || " ";
    }
    k("mcap", money(mcap), fin(mcap) && price ? (mcap / price / 1e9).toFixed(2) + "bn shares" : "");
    k("pe", x1(m.pe), fin(m.eps) ? "EPS " + (m.eps < 0 ? MINUS : "") + SYM + Math.abs(m.eps).toFixed(2) : "Last 12 months");
    k("ev", x1(fin(m.evEbitda) ? m.evEbitda : last.evEbitda), fin(m.evEbitda) ? "Last 12 months" : last.fy ? "Fiscal year " + last.fy : "");
    k("ps", x1(m.ps), "Last 12 months");
    var fcfY = fin(last.freeCashFlow) && fin(mcap) && mcap > 0 ? last.freeCashFlow / mcap * 100 : null;
    k("fcf", pct(fcfY), fin(last.freeCashFlow) ? money(last.freeCashFlow) + " in " + last.fy : "");
    var nd = last.netDebt;
    $("pf-k-nd").parentNode.querySelector(".kpi__name").textContent = fin(nd) && nd < 0 ? "Net cash" : "Net debt";
    k("nd", fin(nd) ? money(Math.abs(nd)) : "n/a", fin(nd) && fin(last.ebitda) && last.ebitda > 0 && nd > 0 ? (nd / last.ebitda).toFixed(1) + "x EBITDA" : last.fy ? "Fiscal year " + last.fy : "");
    var dy = m.dividendYield;
    k("dy", fin(dy) && dy > 0 ? dy.toFixed(2) + "%" : "None", fin(m.dividendPerShare) && m.dividendPerShare > 0 ? SYM + m.dividendPerShare.toFixed(2) + " a share" : "No dividend in the last year");
    k("range", fin(m.low52) && fin(m.high52) ? SYM + Math.round(m.low52).toLocaleString("en-US") + "–" + Math.round(m.high52).toLocaleString("en-US") : "n/a",
      fin(m.beta) || fin(F.profile.beta) ? "Beta " + (fin(m.beta) ? m.beta : F.profile.beta).toFixed(2) : "");
    $("pf-side-src").textContent = "Price: Finnhub, live. Figures: Financial Modeling Prep" + (last.end ? ", annual report for the year to " + day(last.end) : "") + "; Finnhub for the last twelve months. Refreshed daily.";
    staleNote(side, F);
    state(side, "ok");
  }

  function drawFund() {
    var p = F.profile, Y = F.years, last = Y[Y.length - 1], prev = Y[Y.length - 2];
    // Lede, built from the figures.
    var lede = $("pf-lede");
    lede.textContent = "";
    var bits = [p.sector, p.industry].filter(Boolean).join(", ");
    lede.appendChild(document.createTextNode((bits ? bits + ". " : "") + (last ? "Revenue of " + money(last.revenue) + " in the fiscal year to " + day(last.end) : "")));
    if (last && prev && prev.revenue > 0) {
      lede.appendChild(document.createTextNode(", "));
      lede.appendChild(mv(signed((last.revenue / prev.revenue - 1) * 100, 1, "%")));
    }
    if (last && fin(last.operatingIncome) && last.revenue) lede.appendChild(document.createTextNode(", with an operating margin of " + pct(last.operatingIncome / last.revenue * 100) + "."));
    else if (last) lede.appendChild(document.createTextNode("."));

    // Overview.
    $("pf-desc").textContent = p.description || "No description is available for " + p.name + ".";
    var facts = $("pf-facts");
    facts.textContent = "";
    [["Sector", p.sector], ["Industry", p.industry], ["Chief executive", p.ceo],
     ["Employees", fin(p.employees) ? p.employees.toLocaleString("en-US") : ""], ["Headquarters", p.city],
     ["Listed since", p.ipoDate ? p.ipoDate.slice(0, 4) : ""]].forEach(function (f) {
      if (f[1]) facts.appendChild(h("div", {}, [h("dt", {}, f[0]), h("dd", {}, f[1])]));
    });
    if (p.website) {
      var host = p.website.replace(/^https?:\/\/(www\.)?/, "").replace(/\/.*$/, "");
      facts.appendChild(h("div", {}, [h("dt", {}, "Website"), h("dd", {}, h("a", { "class": "link", href: p.website, rel: "noopener nofollow" }, host))]));
    }
    state($("pf-about"), "ok");

    keyFigures();
    if (!Y.length) {
      ["pf-years", "pf-margins", "pf-st"].forEach(hideSection);
    } else {
      $("pf-years-h").textContent = "Revenue and profit, " + Y.length + (Y.length === 1 ? " year" : " years");
      ["pf-years", "pf-margins", "pf-st"].forEach(function (id) { state($(id), "ok"); });
      UNIT = Math.max.apply(null, Y.map(function (y) { return Math.abs(y.revenue || 0); })) >= 2e9 ? 1e9 : 1e6;
      var unitName = (UNIT === 1e9 ? "billions" : "millions") + " of " + (SYM === "$" ? "US dollars" : SYM.trim());
      [].forEach.call(document.querySelectorAll(".pf-unit"), function (s) { s.textContent = "in " + unitName; });
      [].forEach.call(document.querySelectorAll(".pf-unit-cap"), function (s) { s.textContent = "In " + unitName; });
      stmt("is");
    }
    multiples();
    state($("pf-mult"), "ok");
    draw();
    var src = $("pf-st").querySelector(".co-src");
    if (F.missing && F.missing.length) {
      var gone = F.missing.filter(function (m) { return m !== "metrics"; }).map(function (m) { return { income: "income statement", balance: "balance sheet", cash: "cash flow", ratios: "historical multiples" }[m]; });
      if (gone.length && !src.querySelector(".pf-gap")) src.appendChild(h("span", { "class": "pf-gap" }, " Not available on the current data plan: " + gone.join(", ") + "."));
    }
    [].forEach.call(document.querySelectorAll("#pf-years, #pf-margins, #pf-st, #pf-mult"), function (s) { staleNote(s, F); });
  }

  /* ---- Charts (DESIGN.md, Charts) ---- */
  var UNIT = 1e9;
  function nice(m) { var p = Math.pow(10, Math.floor(Math.log10(m || 1))), x = m / p; return (x <= 1 ? 1 : x <= 2 ? 2 : x <= 2.5 ? 2.5 : x <= 5 ? 5 : 10) * p; }
  function svgIn(box, w, hh, label) {
    box.textContent = "";
    var s = el("svg", { "class": "chart", viewBox: "0 0 " + w + " " + hh, width: w, height: hh, role: "img", "aria-label": label });
    box.appendChild(s);
    return s;
  }
  function ticks(lo, hi) {
    var step = nice((hi - lo) / 4 || 1);
    return { lo: Math.floor(lo / step) * step, hi: Math.ceil(hi / step) * step || step, step: step };
  }
  function interact(svg, n, xOf, show, w) {
    svg.setAttribute("tabindex", "0");
    var cur = n - 1;
    function at(e) {
      var b = svg.getBoundingClientRect(), x = (e.clientX - b.left) * w / b.width, best = 0;
      for (var i = 1; i < n; i++) if (Math.abs(xOf(i) - x) < Math.abs(xOf(best) - x)) best = i;
      cur = best;
      show(cur);
    }
    svg.addEventListener("pointermove", at);
    svg.addEventListener("pointerdown", at);
    svg.addEventListener("keydown", function (e) {
      var s = { ArrowLeft: -1, ArrowRight: 1 }[e.key];
      if (!s) return;
      e.preventDefault();
      cur = Math.max(0, Math.min(n - 1, cur + s));
      show(cur);
    });
    show(cur);
  }
  function columns(box, read, cats, series, opt) {
    var w = box.clientWidth;
    if (!w) return;
    var hh = Math.max(180, Math.min(260, w * 0.42)), T0 = 16, B = 24, R = 46, vals = [];
    series.forEach(function (s) { s.vals.forEach(function (v) { if (fin(v)) vals.push(v); }); });
    if (!vals.length) return;
    var t = ticks(Math.min(0, Math.min.apply(null, vals)), Math.max(0, Math.max.apply(null, vals)));
    var Y = function (v) { return T0 + (hh - T0 - B) * (t.hi - v) / (t.hi - t.lo); };
    var svg = svgIn(box, w, hh, opt.label);
    for (var v = t.lo; v <= t.hi + t.step / 2; v += t.step) {
      el("line", { "class": Math.abs(v) < t.step / 1e6 ? "zero-line" : "grid-line", x1: 0, x2: w - R, y1: Y(v), y2: Y(v) }, null, svg);
      el("text", { "class": "chart__label", x: w - R + 6, y: Y(v) + 4 }, opt.axis(v), svg);
    }
    var cw = (w - R) / cats.length, inner = cw * 0.72, bw = inner / series.length;
    var band = el("rect", { "class": "hover-band", x: 0, y: T0, width: cw, height: hh - T0 - B, opacity: 0 }, null, svg);
    cats.forEach(function (c, i) {
      var x0 = i * cw + (cw - inner) / 2;
      series.forEach(function (s, k) {
        var v = s.vals[i];
        if (!fin(v)) return;
        var r = el("rect", { "class": s.cls, x: x0 + k * bw + 1, y: Math.min(Y(v), Y(0)), width: Math.max(2, bw - 2), height: Math.max(1, Math.abs(Y(v) - Y(0))) }, null, svg);
        if (s.cls === "fill") { r.setAttribute("fill", "var(--chart-fill)"); r.setAttribute("stroke", "var(--chart-line)"); }
      });
      if (w >= 420 || (cats.length - 1 - i) % 2 === 0) el("text", { "class": "chart__label", x: i * cw + cw / 2, y: hh - 6, "text-anchor": "middle" }, c, svg);
    });
    interact(svg, cats.length, function (i) { return i * cw + cw / 2; }, function (i) {
      band.setAttribute("x", i * cw);
      band.setAttribute("opacity", 1);
      setRead(read, opt.read(i));
    }, w);
  }
  function lines(box, read, cats, series, opt) {
    var w = box.clientWidth;
    if (!w || cats.length < 2) return;
    var hh = Math.max(180, Math.min(240, w * 0.38)), T0 = 12, B = 24, R = 46, L = 6, vals = [];
    series.forEach(function (s) { s.vals.forEach(function (v) { if (fin(v)) vals.push(v); }); });
    if (!vals.length) return;
    var t = ticks(Math.min.apply(null, vals), Math.max.apply(null, vals));
    var Y = function (v) { return T0 + (hh - T0 - B) * (t.hi - v) / (t.hi - t.lo); };
    var X = function (i) { return L + (w - R - L * 2) * i / (cats.length - 1); };
    var svg = svgIn(box, w, hh, opt.label);
    for (var v = t.lo; v <= t.hi + t.step / 2; v += t.step) {
      el("line", { "class": "grid-line", x1: 0, x2: w - R, y1: Y(v), y2: Y(v) }, null, svg);
      el("text", { "class": "chart__label", x: w - R + 6, y: Y(v) + 4 }, opt.axis(v), svg);
    }
    cats.forEach(function (c, i) {
      if (w >= 480 || (cats.length - 1 - i) % 2 === 0) el("text", { "class": "chart__label", x: X(i), y: hh - 6, "text-anchor": i === 0 ? "start" : i === cats.length - 1 ? "end" : "middle" }, c, svg);
    });
    var cross = el("line", { "class": "ref", x1: 0, x2: 0, y1: T0, y2: hh - B, opacity: 0 }, null, svg);
    series.forEach(function (s) {
      var d = "", pen = false;
      s.vals.forEach(function (v, i) {
        if (!fin(v)) { pen = false; return; }
        d += (pen ? " L" : " M") + X(i).toFixed(1) + " " + Y(v).toFixed(1);
        pen = true;
      });
      var p = el("path", { "class": s.cls, d: d.trim() }, null, svg);
      if (s.dot) { p.setAttribute("stroke-dasharray", "1.5 3"); p.setAttribute("stroke-linecap", "round"); p.setAttribute("stroke-width", "2"); }
    });
    var dots = series.map(function (s) { return s.noDot ? null : el("circle", { "class": "dot", r: 3.5, opacity: 0 }, null, svg); });
    interact(svg, cats.length, X, function (i) {
      cross.setAttribute("x1", X(i));
      cross.setAttribute("x2", X(i));
      cross.setAttribute("opacity", 1);
      series.forEach(function (s, k) {
        if (!dots[k]) return;
        var v = s.vals[i];
        dots[k].setAttribute("opacity", fin(v) ? 1 : 0);
        if (fin(v)) { dots[k].setAttribute("cx", X(i)); dots[k].setAttribute("cy", Y(v)); }
      });
      setRead(read, opt.read(i));
    }, w);
  }
  function u(v) { return v == null ? null : v / UNIT; }
  function un(v) { return fin(v) ? (v < 0 ? MINUS : "") + SYM + Math.abs(v / UNIT).toLocaleString("en-US", { maximumFractionDigits: Math.abs(v / UNIT) < 10 ? 1 : 0 }) + (UNIT === 1e9 ? "bn" : "m") : "n/a"; }
  function axisU(v) { return (v < 0 ? MINUS : "") + SYM + Math.abs(v).toLocaleString("en-US", { maximumFractionDigits: 1 }); }
  function fyLabel(y) { return "FY" + String(y.fy).slice(2); }
  function margin(y, k) { return fin(y[k]) && y.revenue ? y[k] / y.revenue * 100 : null; }

  function draw() {
    if (!F || !F.years.length) return;
    var Y = F.years, cats = Y.map(fyLabel);
    columns($("pf-c-years"), $("pf-r-years"), cats,
      [{ vals: Y.map(function (y) { return u(y.revenue); }), cls: "fill" }, { vals: Y.map(function (y) { return u(y.netIncome); }), cls: "bar" }],
      { axis: axisU, label: NAME + " revenue and net income by fiscal year: " + Y.map(function (y) { return y.fy + " revenue " + un(y.revenue) + ", net income " + un(y.netIncome); }).join("; "),
        read: function (i) {
          var y = Y[i], p = Y[i - 1], nm = margin(y, "netIncome");
          return "FY" + y.fy + ": Revenue " + un(y.revenue) + ", net income " + un(y.netIncome) + (fin(nm) ? ", net margin " + nm.toFixed(1) + "%" : "") +
            (p && p.revenue > 0 ? ". Revenue " + signed((y.revenue / p.revenue - 1) * 100, 1, "%") + " on the year before" : "");
        } });
    var gm = Y.map(function (y) { return margin(y, "grossProfit"); }), om = Y.map(function (y) { return margin(y, "operatingIncome"); }), nm = Y.map(function (y) { return margin(y, "netIncome"); });
    lines($("pf-c-margins"), $("pf-r-margins"), cats,
      [{ vals: gm, cls: "line" }, { vals: om, cls: "dash" }, { vals: nm, cls: "line", dot: true }],
      { axis: function (v) { return v + "%"; }, label: NAME + " gross, operating and net margin by fiscal year",
        read: function (i) { return "FY" + Y[i].fy + ": gross " + pct(gm[i]) + ", operating " + pct(om[i]) + ", net " + pct(nm[i]); } });
    var pe = Y.map(function (y) { return fin(y.pe) && y.pe > 0 && y.pe < 300 ? y.pe : null; });
    var med = median(pe), peBox = document.querySelector(".pf-pe");
    peBox.hidden = pe.filter(fin).length < 2;
    if (!peBox.hidden) lines($("pf-c-pe"), $("pf-r-pe"), cats,
      [{ vals: pe, cls: "line" }, { vals: pe.map(function () { return med; }), cls: "dash", noDot: true }],
      { axis: function (v) { return v + "x"; }, label: NAME + " price to earnings at each fiscal year end, median " + x1(med),
        read: function (i) { return "FY" + Y[i].fy + ": P/E " + x1(pe[i]) + " against a median of " + x1(med); } });
  }

  /* ---- Statements ---- */
  var STMTS = {
    is: [["Revenue", "revenue"], ["Revenue growth", "g", "sub"], ["Gross profit", "grossProfit"], ["Operating income", "operatingIncome"],
         ["EBITDA", "ebitda"], ["Net income", "netIncome"], ["Diluted EPS", "eps", "eps"]],
    bs: [["Cash and investments", "cash"], ["Total debt", "debt"], ["Net debt", "netDebt"], ["Shareholders’ equity", "equity"], ["Total assets", "assets"]],
    cf: [["Cash from operations", "operatingCashFlow"], ["Capital spending", "capex"], ["Free cash flow", "freeCashFlow"], ["Dividends paid", "dividends"], ["Shares bought back", "buybacks"]]
  };
  function stmt(which) {
    var Y = F.years, box = $("pf-stmt");
    var head = h("tr", {}, [h("th", { scope: "col" }, "Fiscal year")].concat(Y.map(function (y) { return h("th", { scope: "col" }, fyLabel(y)); })));
    var body = h("tbody");
    STMTS[which].forEach(function (r) {
      var cells = Y.map(function (y, i) {
        if (r[1] === "g") {
          var p = Y[i - 1];
          return h("td", {}, p && p.revenue > 0 && fin(y.revenue) ? mv(signed((y.revenue / p.revenue - 1) * 100, 1, "%")) : "n/a");
        }
        var v = y[r[1]];
        if (!fin(v)) return h("td", {}, "n/a");
        if (r[2] === "eps") return h("td", {}, (v < 0 ? MINUS : "") + SYM + Math.abs(v).toFixed(2));
        var a = Math.abs(v / UNIT);
        return h("td", {}, (v < 0 ? MINUS : "") + a.toLocaleString("en-US", { minimumFractionDigits: 1, maximumFractionDigits: 1 }));
      });
      if (Y.every(function (y) { return r[1] !== "g" && !fin(y[r[1]]); })) return;
      body.appendChild(h("tr", { "class": r[2] === "sub" ? "pf-sub" : null }, [h("th", { scope: "row" }, r[0])].concat(cells)));
    });
    box.textContent = "";
    box.appendChild(h("table", { "class": "pf-tab" }, [h("thead", {}, head), body]));
    box.setAttribute("aria-labelledby", "pf-tab-" + which);
    // Start at the latest year on a narrow screen.
    box.scrollLeft = box.scrollWidth;
  }
  var tabs = [].slice.call(document.querySelectorAll("[data-stmt]"));
  tabs.forEach(function (b, i) {
    function pick() {
      tabs.forEach(function (o) {
        var on = o === b;
        o.setAttribute("aria-selected", on ? "true" : "false");
        o.setAttribute("aria-pressed", on ? "true" : "false");
        o.tabIndex = on ? 0 : -1;
      });
      if (F && F.years.length) stmt(b.getAttribute("data-stmt"));
    }
    b.addEventListener("click", pick);
    b.addEventListener("keydown", function (e) {
      var s = { ArrowLeft: -1, ArrowRight: 1 }[e.key];
      if (!s) return;
      e.preventDefault();
      var n = tabs[(i + s + tabs.length) % tabs.length];
      n.focus();
      n.click();
    });
  });

  /* ---- Multiples ---- */
  function multiples() {
    if (!F) return;
    var m = F.metrics || {}, Y = F.years.slice(-5), others = (PEERS || []).filter(function (p) { return p.t !== T; });
    var rows = [
      ["P/E", m.pe, mean(Y.map(function (y) { return y.pe > 0 && y.pe < 300 ? y.pe : null; })), "pe", x1],
      ["EV / EBITDA", m.evEbitda, mean(Y.map(function (y) { return y.evEbitda > 0 ? y.evEbitda : null; })), "evEbitda", x1],
      ["Price to sales", m.ps, mean(Y.map(function (y) { return y.ps; })), "ps", x1],
      ["Price to book", m.pb, mean(Y.map(function (y) { return y.pb > 0 ? y.pb : null; })), "pb", x1],
      ["Free cash flow yield", m.fcfYield, mean(Y.map(function (y) { return y.pfcf > 0 ? 100 / y.pfcf : null; })), "fcfYield", pct]
    ];
    var tb = $("pf-mult-rows");
    tb.textContent = "";
    rows.forEach(function (r) {
      var pm = PEERS ? median(others.map(function (p) { return p[r[3]]; })) : null;
      tb.appendChild(h("tr", {}, [h("th", { scope: "row" }, r[0]), h("td", {}, r[4](r[1])), h("td", {}, r[4](r[2])), h("td", {}, PEERS ? r[4](pm) : "…")]));
    });
  }

  /* ---- Peers ---- */
  var peerPart = $("pf-peers"), peerQuotes = {};
  function loadPeers() {
    state(peerPart, "loading");
    return get("/peers?t=" + T).then(function (d) {
      PEERS = d.peers || [];
      if (PEERS.length < 2) { hideSection("pf-peers"); multiples(); return; }
      peerTable();
      state(peerPart, "ok");
      staleNote(peerPart, d);
      multiples();
      PEERS.forEach(function (p) {
        if (p.t === T) return;
        get("/quote?t=" + p.t).then(function (q) { peerQuotes[p.t] = q; peerDay(); }, function () {});
      });
    }, function (e) { fail(peerPart, "The peers", e, loadPeers); });
  }
  function peerTable() {
    var tb = $("pf-peer-rows");
    tb.textContent = "";
    PEERS.forEach(function (p) {
      var self = p.t === T;
      var name = self ? h("span", {}, p.name) : h("a", { href: "?t=" + encodeURIComponent(p.t) }, p.name);
      tb.appendChild(h("tr", { "class": self ? "pf-self" : null }, [
        h("th", { scope: "row" }, [name, h("span", { "class": "pf-tk" }, p.t)]),
        h("td", {}, money(p.marketCap)),
        h("td", { "data-day": p.t }, "…"),
        h("td", {}, fin(p.revenueGrowth) ? mv(signed(p.revenueGrowth, 1, "%")) : "n/a"),
        h("td", {}, pct(p.operatingMargin)),
        h("td", {}, x1(p.pe > 0 ? p.pe : null)),
        h("td", {}, x1(p.evEbitda > 0 ? p.evEbitda : null))
      ]));
    });
    peerDay();
  }
  function peerDay() {
    [].forEach.call(document.querySelectorAll("[data-day]"), function (td) {
      var t = td.getAttribute("data-day"), q = t === T ? QUOTE : peerQuotes[t];
      if (!q || !fin(q.changePct)) return;
      td.textContent = "";
      td.appendChild(mv(signed(q.changePct, 2, "%")));
    });
  }

  /* ---- News ---- */
  var newsPart = $("pf-news");
  function loadNews() {
    state(newsPart, "loading");
    return get("/news?t=" + T).then(function (d) {
      var ul = $("pf-news-list");
      ul.textContent = "";
      if (!d.items.length) ul.appendChild(h("li", { "class": "pf-news__none" }, h("p", {}, "No headlines on " + NAME + " in the past week.")));
      d.items.forEach(function (n) {
        ul.appendChild(h("li", {}, h("a", { href: n.url, rel: "noopener nofollow", target: "_blank" }, [
          h("span", { "class": "pf-news__t" }, n.title),
          h("span", { "class": "pf-news__m" }, [n.source + " · " + ago(n.time) + " ", icon("arrow-up-right")])
        ])));
      });
      state(newsPart, "ok");
      staleNote(newsPart, d);
    }, function (e) { fail(newsPart, "The news", e, loadNews); });
  }

  /* ---- Analysts ---- */
  var anPart = $("pf-analysts");
  function loadAnalysts() {
    state(anPart, "loading");
    return get("/analysts?t=" + T).then(function (d) {
      var r = d.months && d.months[0];
      var parts = r ? [["Strong buy", r.strongBuy], ["Buy", r.buy], ["Hold", r.hold], ["Sell", r.sell], ["Strong sell", r.strongSell]] : [];
      var n = parts.reduce(function (s, p) { return s + p[1]; }, 0);
      if (!n) { hideSection("pf-analysts"); return; }
      var ym = r.period.split("-");
      $("pf-an-lede").textContent = "The recommendations of the " + n + " analyst" + (n === 1 ? "" : "s") + " who cover " + NAME + ", " + MONTHS_LONG[+ym[1] - 1] + " " + ym[0] + ".";
      var bar = $("pf-an-bar"), key = $("pf-an-key");
      bar.textContent = "";
      key.textContent = "";
      bar.setAttribute("aria-label", parts.map(function (p) { return p[0] + " " + p[1]; }).join(", "));
      parts.forEach(function (p, i) {
        if (p[1]) bar.appendChild(h("i", { "class": "pf-an-" + (i + 1), style: "flex:" + p[1] }));
        key.appendChild(h("span", {}, [h("i", { "class": "pf-an-" + (i + 1) }), p[0] + " ", h("b", {}, String(p[1]))]));
      });
      state(anPart, "ok");
    }, function (e) { fail(anPart, "The analyst figures", e, loadAnalysts); });
  }

  /* ---- Section index: the section in view is marked ---- */
  var links = [].slice.call(document.querySelectorAll(".pf-subnav a"));
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        links.forEach(function (a) { a.setAttribute("aria-current", a.getAttribute("href") === "#" + e.target.id ? "true" : "false"); });
      });
    }, { rootMargin: "-30% 0px -60% 0px" });
    links.forEach(function (a) { var s = $(a.getAttribute("href").slice(1)); if (s) io.observe(s); });
  }

  // The price first, then the rest at once; peers and news never wait on fundamentals.
  loadQuote(true).then(pollQuote);
  loadNews();
  loadAnalysts();
  if (MODE === "company") return;
  loadFund();
  loadPeers();
  var rt;
  window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(draw, 150); });
})();
