/* Andra Markets: the portfolio analyser (lab/portfolio-analyser/).
   Holdings are entered as weights or as dollar amounts. Everything is worked out
   in the browser from the daily returns baked into assets/lab-risk-<market>.js
   and the dollar rates in assets/lab-risk-fx.js at deploy time: each holding is
   put in US dollars and sampled every Friday, so markets that close hours apart
   are compared over the same week. Nothing entered is sent or stored; a setup
   that differs from the opening one is kept in the URL fragment so a link
   shares it. Layout and colour follow DESIGN.md (Portfolio analyser). */
(function () {
  "use strict";
  var page = document.querySelector('[data-tool="pf"]');
  var src = document.getElementById("pa-data");
  if (!page || !src) return;
  var P = JSON.parse(src.textContent);
  var MINUS = "−", MAX = 15, MIN_WEEKS = 26;
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var by = {};
  P.companies.forEach(function (c) { by[c.s] = c; });
  var data = {}, loading = {}, parsed = {};
  var picked = [];            // [{s: symbol, v: the number entered}]
  var mode = "w", win = "3Y";
  var view = null;            // what the chart last drew, for its readout

  function q(sel) { return page.querySelector(sel); }
  var holds = q(".pa-holds"), status = q(".pa-status"), plot = q(".pa-plot"), readout = q(".pa-read");
  var find = document.getElementById("pa-find"), opts = document.getElementById("pa-opts");

  function esc(t) {
    return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function num(v, dec) {
    var s = v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec });
    if (/^-[0.,]+$/.test(s)) s = s.slice(1);
    return s.replace("-", MINUS);
  }
  function pct(v, dec, sign) {
    var r = Number((v * 100).toFixed(dec));
    return (r > 0 && sign ? "+" : r < 0 ? MINUS : "") + num(Math.abs(r), dec) + "%";
  }
  // A rise or a fall in green or red, its sign kept (The Rise and Fall Rule).
  function mv(text) {
    var c = text.charAt(0) === "+" ? "mv mv--up" : text.charAt(0) === MINUS ? "mv mv--down" : "";
    return c ? '<span class="' + c + '">' + text + "</span>" : text;
  }
  function parse(iso) {
    var p = iso.split("-");
    return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2]));
  }
  // The weekday axis starts on a Monday: index 4, 9, 14... are Fridays.
  function axisDate(i) {
    var d = parse(data.us.start);
    d.setUTCDate(d.getUTCDate() + Math.floor(i / 5) * 7 + i % 5);
    return d;
  }
  function dayLabel(d) { return d.getUTCDate() + " " + MONTHS[d.getUTCMonth()] + " " + d.getUTCFullYear(); }
  function mean(a) { var t = 0; for (var i = 0; i < a.length; i++) t += a[i]; return t / a.length; }
  function cov(a, b) {
    var ma = mean(a), mb = mean(b), t = 0;
    for (var i = 0; i < a.length; i++) t += (a[i] - ma) * (b[i] - mb);
    return t / (a.length - 1);
  }

  /* The returns ------------------------------------------------------------- */

  function load(key, done) {
    if (data[key]) { done(); return; }
    if (loading[key]) { loading[key].push(done); return; }
    loading[key] = [done];
    var sc = document.createElement("script");
    sc.src = (document.body.getAttribute("data-base") || "") + "assets/" + P.files[key];
    sc.onload = function () {
      data[key] = (window.ANDRA_RISK || {})[key];
      var waiting = loading[key];
      loading[key] = null;
      if (!data[key]) { status.textContent = "The returns did not load. Reload the page to try again."; return; }
      waiting.forEach(function (f) { f(); });
    };
    sc.onerror = function () {
      loading[key] = null;
      status.textContent = "The returns did not load. Check your connection and try again.";
    };
    document.head.appendChild(sc);
  }
  // Log level in basis points on the weekday axis, carried over the days a market
  // was shut; NaN until the series' first return.
  function level(key, sym, n) {
    var k = key + ":" + sym;
    if (!parsed[k]) {
      var raw = (data[key].series[sym] || "").split(","), out = [], acc = NaN;
      for (var i = 0; i < n; i++) {
        var r = i < raw.length ? raw[i] : "";
        if (r !== "") acc = (isNaN(acc) ? 0 : acc) + +r;
        out.push(acc);
      }
      parsed[k] = out;
    }
    return parsed[k];
  }
  // A holding in US dollars: its own level less the level of its currency's units per dollar.
  function dollars(c, n) {
    var loc = level(c.m, c.s, n);
    if (c.u === "USD") return loc;
    var fx = level("fx", c.u, n);
    return loc.map(function (v, i) { return v - fx[i]; });
  }

  /* The holdings ------------------------------------------------------------ */

  function entered(h) { return isFinite(h.v) && h.v > 0 ? h.v : 0; }
  function total() { return picked.reduce(function (t, h) { return t + entered(h); }, 0); }
  function field(v) { return mode === "w" ? Math.round(v * 10) / 10 : Math.round(v); }

  function renderHolds() {
    var tot = total();
    holds.innerHTML = picked.map(function (h) {
      var c = by[h.s], meta = [c.s, c.k, c.c].filter(Boolean).join(" · ");
      return '<li><div class="pa-hold__n"><b>' + esc(c.n) + "</b><span>" + esc(meta) + "</span></div>" +
        '<label class="pa-hold__f"><span class="visually-hidden">' + (mode === "w" ? "Weight of " + esc(c.n) + ", percent" : "Amount in " + esc(c.n) + ", US dollars") + "</span>" +
        (mode === "a" ? '<span aria-hidden="true">$</span>' : "") +
        '<input type="number" inputmode="decimal" min="0" step="' + (mode === "w" ? 1 : 100) + '" value="' + (isFinite(h.v) ? h.v : "") + '" data-s="' + esc(h.s) + '">' +
        (mode === "w" ? '<span aria-hidden="true">%</span>' : "") + "</label>" +
        (mode === "a" ? '<span class="pa-hold__w" data-w="' + esc(h.s) + '">' + (tot ? pct(entered(h) / tot, 1) : "") + "</span>" : "") +
        '<button type="button" class="pa-hold__x" data-remove="' + esc(h.s) + '" aria-label="Remove ' + esc(c.n) + '">' +
        '<svg class="icon" aria-hidden="true"><use href="#i-x"></use></svg></button></li>';
    }).join("");
    holds.classList.toggle("pa-holds--a", mode === "a");
  }
  function renderTotal() {
    var tot = total();
    q(".pa-total b").textContent = mode === "w" ? num(tot, tot % 1 ? 1 : 0) + "%" : "$" + num(tot, 0);
    if (mode === "a") {
      picked.forEach(function (h) {
        var cell = holds.querySelector('[data-w="' + h.s.replace(/"/g, "") + '"]');
        if (cell) cell.textContent = tot ? pct(entered(h) / tot, 1) : "";
      });
    }
  }
  function setMode(m) {
    if (m === mode) return;
    var tot = total();
    // 100% reads as $10,000 and back, so the split is kept.
    picked.forEach(function (h) {
      h.v = !tot ? NaN : m === "a" ? Math.round(entered(h) / tot * 10000) : Math.round(entered(h) / tot * 1000) / 10;
    });
    mode = m;
  }
  function press(group, value) {
    Array.prototype.forEach.call(page.querySelectorAll('[data-group="' + group + '"] .chip'), function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-value") === value ? "true" : "false");
    });
  }
  function start() {
    mode = "w"; win = "3Y";
    picked = P.start.map(function (p) { return { s: p[0], v: p[1] }; });
  }

  /* A link to a setup: #p=AAPL~18,MSFT~16&m=a&win=1Y ------------------------ */

  function share() {
    var same = mode === "w" && win === "3Y" && picked.length === P.start.length &&
      picked.every(function (h, i) { return h.s === P.start[i][0] && h.v === P.start[i][1]; });
    var hash = same || !picked.length ? "" : "#p=" + picked.map(function (h) { return encodeURIComponent(h.s) + "~" + (isFinite(h.v) ? h.v : 0); }).join(",") +
      (mode === "a" ? "&m=a" : "") + (win !== "3Y" ? "&win=" + win : "");
    try { history.replaceState(null, "", hash || location.pathname + location.search); } catch (e) { /* a file: page */ }
  }
  function restore() {
    start();
    var m = /[#&]p=([^&]*)/.exec(location.hash);
    if (!m) return;
    var list = [];
    m[1].split(",").forEach(function (part) {
      var kv = part.split("~"), s = decodeURIComponent(kv[0] || ""), v = parseFloat(kv[1]);
      if (by[s] && list.length < MAX && !list.some(function (h) { return h.s === s; })) list.push({ s: s, v: isFinite(v) && v >= 0 ? v : 0 });
    });
    if (!list.length) return;
    picked = list;
    if (/[#&]m=a/.test(location.hash)) mode = "a";
    if (/[#&]win=1Y/.test(location.hash)) win = "1Y";
  }

  /* The reading ------------------------------------------------------------- */

  function clearOut(msg) {
    status.textContent = msg;
    page.querySelector(".pa__out").classList.add("is-empty");
  }
  function run() {
    renderTotal();
    var need = { us: 1 };
    picked.forEach(function (h) {
      need[by[h.s].m] = 1;
      if (by[h.s].u !== "USD") need.fx = 1;
    });
    var missing = Object.keys(need).filter(function (k) { return !data[k]; });
    if (missing.length) {
      status.textContent = "Loading the returns.";
      var left = missing.length;
      missing.forEach(function (k) { load(k, function () { if (--left === 0) run(); }); });
      return;
    }
    calc();
  }
  function calc() {
    var tot = total();
    if (!picked.length) { clearOut("Add a holding to begin."); return; }
    if (!tot) { clearOut(mode === "w" ? "Give at least one holding a weight above zero." : "Give at least one holding an amount above zero."); return; }
    var n = data.us.series[P.bench].split(",").length;
    var cs = picked.map(function (h) { return by[h.s]; });
    var w = picked.map(function (h) { return entered(h) / tot; });
    var L = cs.map(function (c) { return dollars(c, n); }), B = level("us", P.bench, n);
    // The period: Fridays from the first on which every holding has a level, to the last.
    var first = 0, latest = -1;
    L.concat([B]).forEach(function (s, k) {
      var i = 0;
      while (i < n && isNaN(s[i])) i++;
      if (i > first) { first = i; latest = k; }
    });
    var lastFri = n - 1 - ((n - 1) % 5 + 1) % 5;
    var from = win === "1Y" ? Math.max(first, lastFri - 52 * 5) : first;
    var idx = [];
    for (var i = from + (4 - from % 5 + 5) % 5; i <= lastFri; i += 5) idx.push(i);
    var weeks = idx.length - 1;
    if (weeks < MIN_WEEKS) {
      clearOut("Too little history in common: " + (latest >= 0 && latest < cs.length ? cs[latest].n + " has traded for too short a time." : "the holdings share fewer than " + MIN_WEEKS + " weeks."));
      return;
    }
    function weekly(s) {
      var out = [];
      for (var k = 1; k < idx.length; k++) out.push(Math.exp((s[idx[k]] - s[idx[k - 1]]) / 1e4) - 1);
      return out;
    }
    var R = L.map(weekly), rb = weekly(B), rp = [];
    for (var t = 0; t < weeks; t++) {
      var sum = 0;
      for (var j = 0; j < cs.length; j++) sum += w[j] * R[j][t];
      rp.push(sum);
    }
    function stats(r) {
      var g = 1, peak = 1, dd = 0, path = [100];
      for (var k = 0; k < r.length; k++) {
        g *= 1 + r[k];
        path.push(g * 100);
        if (g > peak) peak = g;
        if (g / peak - 1 < dd) dd = g / peak - 1;
      }
      return { ann: Math.pow(g, 52 / r.length) - 1, vol: Math.sqrt(cov(r, r) * 52), dd: dd, path: path };
    }
    var S = stats(rp), SB = stats(rb), vp = cov(rp, rp), beta = cov(rp, rb) / cov(rb, rb);
    var d0 = axisDate(idx[0]), d1 = axisDate(idx[weeks]);
    page.querySelector(".pa__out").classList.remove("is-empty");
    var msg = "";
    if (mode === "w" && Math.abs(tot - 100) > 0.05) msg = "The weights add up to " + num(tot, tot % 1 ? 1 : 0) + "%. The figures treat them as shares of the whole, scaled to 100%.";
    if (win === "3Y" && latest >= 0 && latest < cs.length && first > 30) msg += (msg ? " " : "") + cs[latest].n + " has prices only from " + dayLabel(axisDate(first)) + ", so the period starts there.";
    status.textContent = msg;

    q(".pa-period").textContent = dayLabel(d0) + " to " + dayLabel(d1) + ": " + weeks + " weeks in US dollars, weights held constant.";
    function kpi(name, value, sub) { return "<li><span>" + name + "</span><b>" + value + "</b><i>" + sub + "</i></li>"; }
    q(".pa-kpis").innerHTML =
      kpi("Return a year", mv(pct(S.ann, 1, true)), "S&amp;P 500 " + pct(SB.ann, 1, true)) +
      kpi("Volatility a year", pct(S.vol, 1), "S&amp;P 500 " + pct(SB.vol, 1)) +
      kpi("Deepest fall", mv(pct(S.dd, 1)), "S&amp;P 500 " + pct(SB.dd, 1)) +
      kpi("Beta to the S&amp;P 500", num(beta, 2), beta > 1.05 ? "Moves more than the index" : beta < 0.95 ? "Moves less than the index" : "Moves about as much");

    // Each holding's share of the portfolio's variance.
    var rc = R.map(function (r, k) { return vp > 0 ? w[k] * cov(r, rp) / vp : 0; });
    var order = cs.map(function (_, k) { return k; }).filter(function (k) { return w[k] > 0; }).sort(function (a, b) { return rc[b] - rc[a]; });
    var top = Math.max.apply(null, order.map(function (k) { return Math.max(w[k], rc[k]); }));
    q(".pa-risk").innerHTML = order.map(function (k) {
      return '<div class="pa-row pa-row--bar"><em>' + esc(cs[k].n) + '</em><span class="pa-bar" aria-hidden="true"><i class="pa-bar__w" style="width:' + (w[k] / top * 100).toFixed(1) +
        '%"></i><i style="width:' + (Math.max(0, rc[k]) / top * 100).toFixed(1) + '%"></i></span><b><span class="visually-hidden">weight ' + pct(w[k], 0) + ", share of risk </span>" + pct(rc[k], 0) + "</b></div>";
    }).join("");

    function expo(key, sel, other) {
      var m = {};
      cs.forEach(function (c, k) { var name = c[key] || other; m[name] = (m[name] || 0) + w[k]; });
      // With no sector known for any holding the list would be one empty line: leave it out.
      q(sel).parentNode.hidden = Object.keys(m).length === 1 && m[other] != null;
      q(sel).innerHTML = Object.keys(m).filter(function (x) { return m[x] > 0; }).sort(function (a, b) { return m[b] - m[a]; }).map(function (x) {
        return '<div class="pa-row"><em>' + esc(x) + "</em><b>" + pct(m[x], 0) + "</b></div>";
      }).join("");
    }
    expo("k", ".pa-sector", "Not classified");
    expo("c", ".pa-country", "Other");
    expo("u", ".pa-cur", "Other");

    var mx = q(".pa-mx");
    if (cs.length < 2) {
      mx.innerHTML = '<p class="pa-none">Add a second holding to see how they move together.</p>';
    } else {
      var sd = R.map(function (r) { return Math.sqrt(cov(r, r)); });
      var short = function (c) { return esc(c.s.split(".")[0]); };
      mx.innerHTML = '<table><caption class="visually-hidden">Correlation of weekly returns between each pair of holdings</caption><thead><tr><td></td>' +
        cs.map(function (c) { return '<th scope="col"><abbr title="' + esc(c.n) + '">' + short(c) + "</abbr></th>"; }).join("") + "</tr></thead><tbody>" +
        cs.map(function (c, a) {
          return '<tr><th scope="row"><abbr title="' + esc(c.n) + '">' + short(c) + "</abbr></th>" + cs.map(function (_, b) {
            if (a === b) return '<td class="pa-mx__self">1.00</td>';
            var r = cov(R[a], R[b]) / (sd[a] * sd[b]);
            return '<td style="--v:' + Math.max(0, r).toFixed(2) + '">' + (r < -0.004 ? MINUS : "") + num(Math.abs(r), 2) + "</td>";
          }).join("") + "</tr>";
        }).join("") + "</tbody></table>";
    }

    q(".pa-stress tbody").innerHTML = P.falls.map(function (f) {
      return '<tr><th scope="row">' + esc(f[0]) + "<span>" + esc(f[1]) + "</span></th><td>" + mv(pct(f[2], 1)) + "</td><td>" + mv(pct(Math.max(-1, f[2] * beta), 1)) + "</td></tr>";
    }).join("");

    view = { port: S.path, bench: SB.path, dates: idx.map(axisDate), at: -1 };
    chart();
    lenses(cs, w, R, rp);
  }

  /* The ring of holdings (assets/lens.js) ------- */

  function lenses(cs, w, R, rp) {
    var Lens = window.AndraLens;
    if (!Lens) return;
    var on = cs.map(function (_, k) { return k; }).filter(function (k) { return w[k] > 0; });
    var cv = q(".pa-ring"), read = q(".pa-ring-read"), stats = q(".pa-ring-stats");
    cv.hidden = on.length < 2;
    if (on.length < 2) { stats.textContent = ""; read.textContent = "Add a second holding to see how they move together."; return; }
    var sd = R.map(function (r) { return Math.sqrt(cov(r, r)); });
    var M = on.map(function (a) { return on.map(function (b) { return a === b ? 1 : cov(R[a], R[b]) / (sd[a] * sd[b]); }); });
    var names = on.map(function (k) { return cs[k].s.split(".")[0]; });
    function r2(v) { return (v < -0.004 ? MINUS : "") + num(Math.abs(v), 2); }
    var ring = Lens.ring(cv, { names: names, notes: on.map(function (k) { return pct(w[k], 0); }), matrix: M, onHover: say });
    var pairs = ring.pairs, avg = mean(pairs.map(function (p) { return p[2]; }));
    stats.textContent = on.length + " holdings \u00b7 " + pairs.length + (pairs.length === 1 ? " pair" : " pairs") + " \u00b7 mean correlation " + r2(avg);
    function say(k) {
      if (k < 0) {
        var a = pairs[0], z = pairs[pairs.length - 1];
        read.innerHTML = "Closest <b>" + esc(names[a[0]]) + " \u00b7 " + esc(names[a[1]]) + "</b> " + r2(a[2]) +
          (pairs.length > 1 ? " \u00b7 furthest <b>" + esc(names[z[0]]) + " \u00b7 " + esc(names[z[1]]) + "</b> " + r2(z[2]) : "");
        return;
      }
      var mine = pairs.filter(function (p) { return p[0] === k || p[1] === k; });
      read.innerHTML = "<b>" + esc(cs[on[k]].n) + "</b> \u00b7 " + mine.map(function (p) { return esc(names[p[0] === k ? p[1] : p[0]]) + " " + r2(p[2]); }).join(" \u00b7 ");
    }
    say(-1);
    cv.setAttribute("aria-label", "A ring of " + on.length + " holdings joined by bands of strands as thick as each pair's correlation. The closest pair is " +
      cs[on[pairs[0][0]]].n + " and " + cs[on[pairs[0][1]]].n + ", " + r2(pairs[0][2]) + ". Every figure is in the table under it.");
  }

  /* Growth of 100 ----------------------------------------------------------- */

  function chart() {
    if (!view) return;
    var W = plot.clientWidth;
    if (!W) return;
    var H = W < 480 ? 220 : 300, L = 36, R = 6, T = 8, B = 24, n = view.port.length - 1;
    var all = view.port.concat(view.bench), lo = Math.min.apply(null, all), hi = Math.max.apply(null, all);
    var step = [5, 10, 20, 25, 50, 100, 200, 500].filter(function (s) { return (hi - lo) / s <= 5; })[0] || 1000;
    lo = Math.floor(lo / step) * step; hi = Math.ceil(hi / step) * step;
    var X = function (i) { return L + i / n * (W - L - R); }, Y = function (v) { return T + (hi - v) / (hi - lo) * (H - T - B); };
    var line = function (a) { return a.map(function (v, i) { return (i ? "L" : "M") + X(i).toFixed(1) + " " + Y(v).toFixed(1); }).join(""); };
    var s = '<svg width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + " " + H + '" aria-hidden="true">';
    for (var v = lo; v <= hi + 1e-9; v += step) {
      s += '<line class="g" x1="' + L + '" x2="' + (W - R) + '" y1="' + Y(v).toFixed(1) + '" y2="' + Y(v).toFixed(1) + '"/><text class="t" x="' + (L - 8) + '" y="' + (Y(v) + 4).toFixed(1) + '" text-anchor="end">' + v + "</text>";
    }
    var seen = {};
    view.dates.forEach(function (d, i) {
      var y = d.getUTCFullYear();
      if (n > 80) {
        if (i && d.getUTCMonth() === 0 && !seen[y]) { seen[y] = 1; s += '<text class="t" x="' + X(i).toFixed(1) + '" y="' + (H - 6) + '" text-anchor="middle">' + y + "</text>"; }
      } else if (i && d.getUTCMonth() % 3 === 0 && !seen[y + "-" + d.getUTCMonth()] && d.getUTCDate() <= 7) {
        seen[y + "-" + d.getUTCMonth()] = 1;
        s += '<text class="t" x="' + X(i).toFixed(1) + '" y="' + (H - 6) + '" text-anchor="middle">' + MONTHS[d.getUTCMonth()] + " " + String(y).slice(2) + "</text>";
      }
    });
    s += '<path class="b" d="' + line(view.bench) + '"/><path class="p" d="' + line(view.port) + '"/>';
    var at = view.at >= 0 ? view.at : n;
    if (view.at >= 0) s += '<line class="h" x1="' + X(at).toFixed(1) + '" x2="' + X(at).toFixed(1) + '" y1="' + T + '" y2="' + (H - B) + '"/>';
    s += '<circle class="d" cx="' + X(at).toFixed(1) + '" cy="' + Y(view.port[at]).toFixed(1) + '" r="2.5"/></svg>';
    plot.innerHTML = s;
    view.x0 = L; view.x1 = W - R;
    var text = (at === 0 ? "Start, " : "Week to ") + dayLabel(view.dates[at]) + ": portfolio " + num(view.port[at], 1) + ", S&P 500 " + num(view.bench[at], 1) + ".";
    readout.textContent = text;
    plot.setAttribute("aria-label", "Growth of 100 from " + dayLabel(view.dates[0]) + " to " + dayLabel(view.dates[n]) + ": the portfolio ends at " +
      num(view.port[n], 0) + ", the S&P 500 at " + num(view.bench[n], 0) + ". Use the arrow keys to read each week.");
  }
  plot.addEventListener("pointermove", function (e) {
    if (!view) return;
    var r = plot.getBoundingClientRect(), n = view.port.length - 1;
    var i = Math.round((e.clientX - r.left - view.x0) / (view.x1 - view.x0) * n);
    i = Math.max(0, Math.min(n, i));
    if (i !== view.at) { view.at = i; chart(); }
  });
  plot.addEventListener("pointerleave", function () { if (view && view.at >= 0) { view.at = -1; chart(); } });
  plot.addEventListener("keydown", function (e) {
    if (!view) return;
    var n = view.port.length - 1, i = view.at < 0 ? n : view.at;
    if (e.key === "ArrowLeft") i--; else if (e.key === "ArrowRight") i++; else if (e.key === "Home") i = 0; else if (e.key === "End") i = n; else return;
    e.preventDefault();
    view.at = Math.max(0, Math.min(n, i));
    chart();
  });

  /* The inputs -------------------------------------------------------------- */

  var active = -1, matches = [];
  function closeOpts() {
    opts.hidden = true;
    find.setAttribute("aria-expanded", "false");
    find.removeAttribute("aria-activedescendant");
    active = -1;
  }
  function renderOpts() {
    var term = find.value.trim().toLowerCase();
    if (!term) { closeOpts(); return; }
    matches = P.companies.filter(function (c) {
      return !picked.some(function (h) { return h.s === c.s; }) && (c.n.toLowerCase().indexOf(term) >= 0 || c.s.toLowerCase().indexOf(term) === 0);
    }).slice(0, 8);
    opts.innerHTML = matches.length ? matches.map(function (c, i) {
      return '<li role="option" id="pa-opt-' + i + '" aria-selected="' + (i === active) + '" data-s="' + esc(c.s) + '">' +
        '<span class="lt-opts__name">' + esc(c.n) + '</span><span class="lt-opts__meta">' + esc(c.s) + ", " + esc(c.c) + "</span></li>";
    }).join("") : '<li class="lt-opts__none">No company the site covers matches.</li>';
    opts.hidden = false;
    find.setAttribute("aria-expanded", "true");
    if (active >= 0) find.setAttribute("aria-activedescendant", "pa-opt-" + active);
  }
  function add(sym) {
    find.value = "";
    closeOpts();
    if (picked.length >= MAX) { status.textContent = "Up to " + MAX + " holdings. Remove one to add another."; return; }
    // A new holding takes an average share: the mean of what is already entered.
    var tot = total(), v = picked.length && tot ? field(tot / picked.length) : mode === "w" ? 100 : 10000;
    picked.push({ s: sym, v: v });
    renderHolds(); run(); share();
  }
  find.addEventListener("input", function () { active = -1; renderOpts(); });
  find.addEventListener("keydown", function (e) {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      if (!matches.length || opts.hidden) return;
      e.preventDefault();
      active = (active + (e.key === "ArrowDown" ? 1 : -1) + matches.length) % matches.length;
      renderOpts();
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (matches.length && !opts.hidden) add(matches[Math.max(active, 0)].s);
    } else if (e.key === "Escape") {
      closeOpts();
    }
  });
  find.addEventListener("blur", function () { setTimeout(closeOpts, 150); });
  opts.addEventListener("mousedown", function (e) {
    var li = e.target.closest("[data-s]");
    if (li) { e.preventDefault(); add(li.getAttribute("data-s")); }
  });
  holds.addEventListener("input", function (e) {
    var inp = e.target.closest("input[data-s]");
    if (!inp) return;
    var h = picked.filter(function (x) { return x.s === inp.getAttribute("data-s"); })[0];
    if (!h) return;
    h.v = parseFloat(inp.value);
    run(); share();
  });
  holds.addEventListener("click", function (e) {
    var b = e.target.closest("[data-remove]");
    if (!b) return;
    picked = picked.filter(function (h) { return h.s !== b.getAttribute("data-remove"); });
    renderHolds(); run(); share();
    find.focus();
  });
  page.addEventListener("click", function (e) {
    var chip = e.target.closest(".lt-chips .chip"), act = e.target.closest("[data-pa]");
    if (chip) {
      var group = chip.parentNode.getAttribute("data-group"), value = chip.getAttribute("data-value");
      if (group === "mode") setMode(value); else win = value;
      press(group, value);
      renderHolds(); run(); share();
    } else if (act) {
      if (act.getAttribute("data-pa") === "equal") {
        var tot = total() || (mode === "w" ? 100 : 10000);
        picked.forEach(function (h) { h.v = field(tot / picked.length); });
      } else {
        start();
        press("mode", mode); press("win", win);
      }
      renderHolds(); run(); share();
    }
  });
  window.addEventListener("hashchange", function () {
    if (location.hash.length > 1 && location.hash.indexOf("=") < 0) return;
    restore();
    press("mode", mode); press("win", win);
    renderHolds(); run();
  });
  var lastW = 0;
  window.addEventListener("resize", function () {
    if (plot.clientWidth !== lastW) { lastW = plot.clientWidth; chart(); }
  });

  q(".pa__grid").hidden = false;
  restore();
  press("mode", mode); press("win", win);
  renderHolds();
  run();
})();
