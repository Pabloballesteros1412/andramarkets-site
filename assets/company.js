/* Andra Markets company pages: the peer strips, the cash flow model, revenue
   to profit and the share price against the S&P 500, drawn at each chart's
   own pixel width from the figures embedded in the page (#co-data, written by
   tools/build_site.py). Tokens and rules: DESIGN.md, Company page. */
(function () {
  "use strict";
  var src = document.getElementById("co-data");
  if (!src) return;
  var D = JSON.parse(src.textContent);
  var NS = "http://www.w3.org/2000/svg";
  var MINUS = "−";
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  function el(name, attrs, text, parent) {
    var e = document.createElementNS(NS, name);
    for (var k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  }
  function svgIn(box, w, h, label) {
    box.textContent = "";
    var svg = el("svg", { "class": "chart", viewBox: "0 0 " + w + " " + h, width: w, height: h, role: "img", "aria-label": label });
    box.appendChild(svg);
    return svg;
  }
  function signed(v, d, unit) {
    var r = Math.abs(v).toFixed(d);
    if (+r === 0) return (0).toFixed(d) + (unit || "");
    return (v > 0 ? "+" : MINUS) + r + (unit || "");
  }
  function day(iso) {
    var p = iso.split("-");
    return +p[2] + " " + MONTHS[+p[1] - 1] + " " + p[0];
  }
  function usd(v) {
    return "$" + v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  /* Peers: one strip per measure, the company filled, the median a dashed tick. */
  var MEAS = [
    { k: "pe", n: "P/E, last 12 months", f: function (v) { return v.toFixed(1) + "x"; }, note: "lower is cheaper" },
    { k: "g", n: "Revenue growth", f: function (v) { return signed(v, 1, "%"); }, note: "last fiscal year" },
    { k: "om", n: "Operating margin", f: function (v) { return signed(v, 1, "%").replace("+", ""); }, note: "" },
    { k: "de", n: "Debt to equity", f: function (v) { return v.toFixed(0) + "%"; }, note: "lower is safer" },
    { k: "dy", n: "Dividend yield", f: function (v) { return v.toFixed(2) + "%"; }, note: "" }
  ];
  var peersBox = document.getElementById("co-peers");
  var peersRead = document.getElementById("co-peers-read");
  var self = D.peers.filter(function (p) { return p.t === D.t; })[0];
  function drawPeers() {
    var w = peersBox.clientWidth;
    if (!w) return;
    var rowH = 60, R = 8, h = MEAS.length * rowH;
    var svg = svgIn(peersBox, w, h, D.name + " against " + (D.peers.length - 1) + " companies on five measures");
    var marks = [];
    MEAS.forEach(function (m, r) {
      var rows = D.peers.filter(function (p) { return p[m.k] != null; });
      var vals = rows.map(function (p) { return p[m.k]; }).sort(function (a, b) { return a - b; });
      var top = r * rowH;
      el("text", { "class": "chart__value", x: 0, y: top + 16, "font-weight": 550 }, m.n, svg);
      var mine = self[m.k];
      el("text", { "class": "chart__label", x: w, y: top + 16, "text-anchor": "end" },
        w < 520 ? (mine == null ? "n/a" : m.f(mine)) :
          (mine == null ? D.name + ": n/a" : D.name + " " + m.f(mine) + (m.note ? ", " + m.note : "")), svg);
      var y = top + 40;
      el("line", { "class": "grid-line", x1: 0, x2: w - R, y1: y, y2: y }, null, svg);
      if (vals.length < 2) return;
      // Clip the axis to the 5th and 95th percentiles so one outlier does not
      // squash the rest; dots beyond sit on the edge with an arrow.
      var lo = vals[Math.floor((vals.length - 1) * 0.05)], hi = vals[Math.ceil((vals.length - 1) * 0.95)];
      if (hi === lo) { lo -= 1; hi += 1; }
      var X = function (v) { return 8 + (w - R - 16) * (Math.max(lo, Math.min(hi, v)) - lo) / (hi - lo); };
      var med = vals[Math.floor(vals.length / 2)];
      el("line", { x1: X(med), x2: X(med), y1: y - 8, y2: y + 8, stroke: "var(--ink-3)", "stroke-dasharray": "2 2" }, null, svg);
      rows.forEach(function (p) {
        if (p.t === D.t) return;
        var out = p[m.k] < lo || p[m.k] > hi;
        var c = el("circle", { cx: X(p[m.k]), cy: y, r: 5, fill: "var(--ground)", stroke: "var(--ink-3)", "stroke-width": 1.5 }, null, svg);
        if (out) c.setAttribute("stroke-dasharray", "2 1.5");
        var text = m.n + ": " + p.n + " " + m.f(p[m.k]) + ". Median " + m.f(med) + ".";
        el("title", {}, text, c);
        marks.push({ c: c, text: text });
      });
      if (mine != null) {
        var mc = el("circle", { cx: X(mine), cy: y, r: 6.5, fill: "var(--ink)", stroke: "var(--ground)", "stroke-width": 2 }, null, svg);
        var t = m.n + ": " + D.name + " " + m.f(mine) + ". Median " + m.f(med) + ".";
        el("title", {}, t, mc);
        marks.push({ c: mc, text: t });
      }
    });
    marks.forEach(function (mk) {
      mk.c.style.cursor = "pointer";
      mk.c.addEventListener("pointerenter", function () { peersRead.textContent = mk.text; });
      mk.c.addEventListener("click", function () { peersRead.textContent = mk.text; });
    });
    if (!peersRead.textContent) peersRead.textContent = "Dashed tick: the median. A dashed dot sits beyond the axis, which spans the middle 90% of values.";
  }

  /* Cash flow model: ten years, growth fading from year 6 to the terminal rate. */
  var M = D.dcf;
  var valBox = document.getElementById("co-val");
  var gIn = document.getElementById("co-g"), rIn = document.getElementById("co-r"), tIn = document.getElementById("co-tg");
  var DEF = gIn ? { g: gIn.value, r: rIn.value, t: tIn.value } : null;
  function model(g1, rr, tt) {
    var f = M.fcf, pv = 0, flows = [];
    for (var y = 1; y <= 10; y++) {
      var gy = y <= 5 ? g1 : g1 + (tt - g1) * (y - 5) / 5;
      f = f * (1 + gy / 100);
      var p = f / Math.pow(1 + rr / 100, y);
      pv += p;
      flows.push(p);
    }
    var tv = f * (1 + tt / 100) / (rr / 100 - tt / 100) / Math.pow(1 + rr / 100, 10);
    return { ps: (pv + tv - M.net_debt) / M.shares, flows: flows, pv: pv, tv: tv };
  }
  function implied(rr, tt) {
    var lo = -30, hi = 120;
    if (model(hi, rr, tt).ps < D.price) return null;
    if (model(lo, rr, tt).ps > D.price) return null;
    for (var i = 0; i < 60; i++) {
      var mid = (lo + hi) / 2;
      if (model(mid, rr, tt).ps < D.price) lo = mid; else hi = mid;
    }
    return (lo + hi) / 2;
  }
  function drawVal(res) {
    var w = valBox.clientWidth;
    if (!w) return;
    var h = 170, T = 18, B = 22;
    var bars = res.flows.concat([res.tv]);
    var max = Math.max.apply(null, bars.map(function (v) { return Math.max(v, 0); })) || 1;
    var bw = w / bars.length;
    var svg = svgIn(valBox, w, h, "Each year's cash flow and the value after year 10, in today's money");
    el("line", { "class": "grid-line", x1: 0, x2: w, y1: h - B, y2: h - B }, null, svg);
    bars.forEach(function (v, i) {
      var last = i === bars.length - 1;
      var bh = Math.max(1, (h - T - B) * Math.max(v, 0) / max);
      var x = i * bw + 3, cw = Math.max(2, bw - 6);
      var r = el("rect", { x: x, y: h - B - bh, width: cw, height: bh, fill: last ? "var(--chart-line)" : "var(--chart-fill)", stroke: "var(--chart-line)", "stroke-width": 1 }, null, svg);
      el("title", {}, (last ? "Value after year 10" : "Year " + (i + 1) + " cash flow") + ", today's money: $" + v.toFixed(1) + "bn", r);
      el("text", { "class": "chart__label", x: x + cw / 2, y: h - 6, "text-anchor": "middle" }, last ? "After 10" : String(i + 1), svg);
      if (i === 0 || i === 9 || last) el("text", { "class": "chart__value", x: x + cw / 2, y: h - B - bh - 5, "text-anchor": "middle" }, "$" + v.toFixed(0) + "bn", svg);
    });
  }
  function update() {
    var g = +gIn.value, r = +rIn.value, t = +tIn.value;
    if (t > r - 1) { t = r - 1; tIn.value = t; }
    document.getElementById("co-g-o").textContent = signed(g, 1, "%") + " a year";
    document.getElementById("co-r-o").textContent = r.toFixed(2) + "%";
    document.getElementById("co-tg-o").textContent = t.toFixed(2) + "% a year";
    var res = model(g, r, t);
    var gap = (res.ps / D.price - 1) * 100;
    var fv = document.getElementById("co-fv"), fc = document.getElementById("co-fv-c");
    if (res.ps <= 0) {
      fv.textContent = "Below zero";
      fc.textContent = "Debt outweighs the cash flows on these assumptions.";
    } else {
      fv.textContent = usd(res.ps).replace(/\.\d\d$/, "");
      fc.textContent = Math.abs(gap).toFixed(0) + "% " + (gap >= 0 ? "above" : "below") + " the " + usd(D.price) + " close. " +
        Math.round(res.tv / (res.pv + res.tv) * 100) + "% of it comes after year 10.";
    }
    var ig = implied(r, t);
    document.getElementById("co-ig").textContent = ig == null ? "Out of range" : signed(ig, 1, "%") + " a year";
    document.getElementById("co-ig-c").textContent =
      "Cash flow growth in years 1 to 5 that makes the model equal the price, at a " + r.toFixed(2) + "% discount rate." +
      (M.cagr != null ? " Over the last three fiscal years free cash flow grew " + signed(M.cagr, 1, "%") + " a year." : "");
    drawVal(res);
  }
  if (M && gIn) {
    [gIn, rIn, tIn].forEach(function (i) { i.addEventListener("input", update); });
    document.getElementById("co-reset").addEventListener("click", function () {
      gIn.value = DEF.g; rIn.value = DEF.r; tIn.value = DEF.t;
      update();
    });
  }

  /* Revenue to profit: totals from zero, steps from where the last bar ended. */
  var flowBox = document.getElementById("co-flow");
  function drawFlow() {
    var F = D.flow, w = flowBox.clientWidth;
    if (!w || !F) return;
    var rev = F[0][1];
    var narrow = w < 560, rowH = 30, labW = Math.min(150, w * 0.36), R = narrow ? 92 : 180, T = 18, bh = 16;
    var h = F.length * rowH + T;
    var svg = svgIn(flowBox, w, h, "Revenue of $" + rev.toFixed(1) + "bn down to net income in the year to " + D.fy);
    var run = 0, lo = 0, hi = rev;
    F.forEach(function (f) {
      if (f[2] === "total") run = f[1]; else run += f[1];
      lo = Math.min(lo, run); hi = Math.max(hi, run);
    });
    var X = function (v) { return labW + (w - labW - R) * (v - lo) / (hi - lo); };
    var step = Math.pow(10, Math.floor(Math.log10(hi / 2)));
    if (hi / step > 6) step *= 2;
    for (var v = 0; v <= hi; v += step) {
      el("line", { "class": v ? "grid-line" : "zero-line", x1: X(v), x2: X(v), y1: T - 4, y2: h }, null, svg);
      if (!narrow || v === 0 || v + step > hi) el("text", { "class": "chart__label", x: X(v), y: 10, "text-anchor": v ? "middle" : "start" }, "$" + v + "bn", svg);
    }
    run = 0;
    var prevEnd = null, prevY = null;
    F.forEach(function (f, i) {
      var tot = f[2] === "total", a, b, cls;
      var y = T + i * rowH + (rowH - bh) / 2;
      if (tot) { a = 0; b = f[1]; cls = "bar"; }
      else { a = run; b = run + f[1]; cls = f[1] < 0 ? "down" : "up"; }
      run = b;
      var x0 = X(Math.min(a, b)), x1 = X(Math.max(a, b));
      if (prevY !== null) el("line", { x1: X(prevEnd), x2: X(prevEnd), y1: prevY + bh, y2: y, stroke: "var(--ink-3)", "stroke-dasharray": "2 2" }, null, svg);
      prevEnd = b;
      prevY = y;
      el("text", { "class": "chart__value", x: 0, y: y + bh / 2 + 4, "font-weight": tot ? 600 : 400 }, f[0], svg);
      var rect = el("rect", { "class": cls, x: x0, y: y, width: Math.max(1.5, x1 - x0), height: bh }, null, svg);
      var pct = Math.abs(f[1]) / rev * 100;
      el("title", {}, f[0] + ": " + (tot ? "$" : (f[1] < 0 ? MINUS : "+") + "$") + Math.abs(f[1]).toFixed(1) + "bn, " + pct.toFixed(1) + "% of revenue", rect);
      var t = el("text", { "class": "chart__value", x: X(hi) + 10, y: y + bh / 2 + 4, "font-weight": tot ? 600 : 400 },
        (tot ? "" : f[1] < 0 ? MINUS : "+") + Math.abs(f[1]).toFixed(1), svg);
      if (i > 0) el("tspan", { "class": "chart__label", "font-weight": 400 }, "  " + (f[3] && !narrow ? f[3] + " " : "") + pct.toFixed(0) + "%", t);
    });
  }

  /* Against the market: both rebased to 100 on the first shared session. */
  var ctxBox = document.getElementById("co-ctx"), ctxRead = document.getElementById("co-ctx-read");
  var spx = {};
  D.spx.forEach(function (p) { spx[p[0]] = p[1]; });
  var H = D.hist.filter(function (p) { return spx[p[0]] != null; });
  function drawCtx() {
    var w = ctxBox.clientWidth;
    if (!w) return;
    var rows = H.length > 1 ? H : D.hist;
    var both = H.length > 1;
    var h = Math.max(200, Math.min(300, w * 0.4)), R = 42, T = 10, B = 24;
    var a0 = rows[0][1], b0 = both ? spx[rows[0][0]] : null;
    var A = rows.map(function (p) { return p[1] / a0 * 100; });
    var Bv = both ? rows.map(function (p) { return spx[p[0]] / b0 * 100; }) : [];
    var all = A.concat(Bv);
    var lo = Math.floor(Math.min.apply(null, all) / 10) * 10, hi = Math.ceil(Math.max.apply(null, all) / 10) * 10;
    var X = function (i) { return (w - R) * i / (rows.length - 1); };
    var Y = function (v) { return T + (h - T - B) * (1 - (v - lo) / (hi - lo)); };
    var svg = svgIn(ctxBox, w, h, D.name + " " + signed(A[A.length - 1] - 100, 1, "%") +
      (both ? " and the S&P 500 " + signed(Bv[Bv.length - 1] - 100, 1, "%") : "") + " over the year");
    svg.setAttribute("tabindex", "0");
    var stepY = [10, 20, 25, 50, 100, 200].filter(function (k) { return (hi - lo) / k <= 6; })[0] || 500;
    lo = Math.floor(lo / stepY) * stepY;
    hi = Math.ceil(hi / stepY) * stepY;
    for (var v = lo; v <= hi; v += stepY) {
      el("line", { "class": v === 100 ? "ref" : "grid-line", x1: 0, x2: w - R, y1: Y(v), y2: Y(v) }, null, svg);
      el("text", { "class": "chart__label", x: w - R + 6, y: Y(v) + 4 }, String(v), svg);
    }
    el("text", { "class": "chart__label", x: 0, y: h - 6 }, day(rows[0][0]), svg);
    el("text", { "class": "chart__label", x: w - R, y: h - 6, "text-anchor": "end" }, day(rows[rows.length - 1][0]), svg);
    var path = function (arr) { return arr.map(function (v, i) { return (i ? "L" : "M") + X(i).toFixed(1) + " " + Y(v).toFixed(1); }).join(""); };
    if (both) el("path", { d: path(Bv), fill: "none", stroke: "var(--ink-3)", "stroke-width": 1.5, "stroke-dasharray": "4 3" }, null, svg);
    el("path", { "class": "line", d: path(A) }, null, svg);
    var xh = el("line", { "class": "cross", y1: T, y2: h - B }, null, svg);
    var d1 = el("circle", { "class": "dot", r: 3.5 }, null, svg);
    var d2 = both ? el("circle", { r: 3, fill: "var(--ink-3)" }, null, svg) : null;
    var cur = rows.length - 1;
    function show(i) {
      cur = Math.max(0, Math.min(rows.length - 1, i));
      xh.setAttribute("x1", X(cur)); xh.setAttribute("x2", X(cur));
      d1.setAttribute("cx", X(cur)); d1.setAttribute("cy", Y(A[cur]));
      if (d2) { d2.setAttribute("cx", X(cur)); d2.setAttribute("cy", Y(Bv[cur])); }
      ctxRead.textContent = day(rows[cur][0]) + ": " + D.name + " " + usd(rows[cur][1]) + " (" + signed(A[cur] - 100, 1, "%") + ")" +
        (both ? ", S&P 500 " + spx[rows[cur][0]].toLocaleString("en-US", { maximumFractionDigits: 0 }) + " (" + signed(Bv[cur] - 100, 1, "%") + ")" : "");
    }
    function at(e) {
      var b = svg.getBoundingClientRect();
      return Math.round((e.clientX - b.left) / (b.width * (w - R) / w) * (rows.length - 1));
    }
    svg.addEventListener("pointermove", function (e) { show(at(e)); });
    svg.addEventListener("pointerdown", function (e) { show(at(e)); });
    svg.addEventListener("keydown", function (e) {
      var s = { ArrowLeft: -1, ArrowRight: 1 }[e.key];
      if (e.key === "Home") s = -rows.length;
      if (e.key === "End") s = rows.length;
      if (s) { e.preventDefault(); show(cur + s); }
    });
    show(cur);
  }

  function drawAll() {
    drawPeers();
    if (M && gIn) update();
    drawFlow();
    drawCtx();
  }
  drawAll();
  var t;
  var body = document.querySelector(".co__body");
  if ("ResizeObserver" in window && body) {
    new ResizeObserver(function () {
      clearTimeout(t);
      t = setTimeout(drawAll, 80);
    }).observe(body);
  }
})();
