/* Andra Markets company pages: the peer strips, the cash flow model, revenue
   to profit and the share price against the S&P 500, drawn at each chart's
   own pixel width from the figures embedded in the page (#co-data, written by
   tools/build_site.py). Tokens and rules: DESIGN.md, Company page. */
(function () {
  "use strict";
  // A logo drawn in white or pale colours (made for dark backgrounds) gets the
  // dark plate instead of the white one.
  var logo = document.querySelector(".co-logo img");
  function plate() {
    try {
      var c = document.createElement("canvas"), n = 48;
      c.width = c.height = n;
      var x = c.getContext("2d");
      x.drawImage(logo, 0, 0, n, n);
      var px = x.getImageData(0, 0, n, n).data, sum = 0, count = 0;
      for (var i = 0; i < px.length; i += 4) {
        if (px[i + 3] < 128) continue;
        sum += 0.2126 * px[i] + 0.7152 * px[i + 1] + 0.0722 * px[i + 2];
        count++;
      }
      // Mostly light ink, and enough transparency that the plate shows through.
      if (count && count < n * n * 0.9 && sum / count > 205) logo.parentNode.classList.add("co-logo--light");
    } catch (e) { /* a logo the canvas cannot read keeps the white plate */ }
  }
  if (logo) {
    if (logo.complete && logo.naturalWidth) plate();
    else logo.addEventListener("load", plate);
  }

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
      var lab = el("text", { "class": "chart__label", x: w, y: top + 16, "text-anchor": "end" }, null, svg);
      if (mine == null) lab.textContent = w < 520 ? "n/a" : D.name + ": n/a";
      else {
        if (w >= 520) el("tspan", {}, D.name + " ", lab);
        var fig = m.f(mine);
        // Revenue growth is a rise or a fall: its figure takes the colour.
        el("tspan", { "class": m.k === "g" && /^[+\u2212]/.test(fig) ? (fig[0] === "+" ? "mv--up" : "mv--down") : null, fill: m.k === "g" && /^[+\u2212]/.test(fig) ? (fig[0] === "+" ? "var(--up-text)" : "var(--down-text)") : null }, fig, lab);
        if (w >= 520 && m.note) el("tspan", {}, ", " + m.note, lab);
      }
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
      mk.c.addEventListener("pointerenter", function () { setRead(peersRead, mk.text); });
      mk.c.addEventListener("click", function () { setRead(peersRead, mk.text); });
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

  /* Where revenue goes: one bar split into what each $100 of revenue paid for,
     red for costs and tax, green for what was kept; rows below give each line. */
  var flowBox = document.getElementById("co-flow");
  function drawFlow() {
    var C = D.comp, w = flowBox ? flowBox.clientWidth : 0;
    if (!w || !C) return;
    var parts = C.parts.map(function (p, i) { return { n: p[0], v: p[1], cls: "down", op: Math.max(0.35, 1 - i * 0.16) }; });
    if (C.ni > 0) parts.push({ n: "Net income", v: C.ni, cls: "up", op: 1 });
    var total = parts.reduce(function (a, p) { return a + p.v; }, 0);
    var rowH = 26, barH = 40, T = 4, gap = 22;
    var h = T + barH + gap + parts.length * rowH + (C.ni < 0 ? rowH : 0);
    var svg = svgIn(flowBox, w, h, "Of revenue of $" + C.rev.toFixed(1) + "bn in the year to " + D.fy + ": " +
      parts.map(function (p) { return p.n + " $" + p.v.toFixed(1) + "bn"; }).join(", "));
    var x = 0;
    parts.forEach(function (p) {
      var pw = w * p.v / total;
      var r = el("rect", { "class": p.cls, x: x, y: T, width: Math.max(1, pw - 1), height: barH, opacity: p.op }, null, svg);
      el("title", {}, p.n + ": $" + p.v.toFixed(1) + "bn, " + (p.v / C.rev * 100).toFixed(1) + "% of revenue", r);
      if (pw > 44) el("text", { "class": "co-seg", x: x + 8, y: T + barH / 2 + 4 }, (p.v / C.rev * 100).toFixed(0) + "%", svg);
      x += pw;
    });
    if (C.extra > 0 || C.ni < 0) {
      var rx = w * C.rev / total;
      el("line", { x1: rx, x2: rx, y1: T - 4, y2: T + barH + 6, stroke: "var(--ink)", "stroke-width": 1.5 }, null, svg);
      el("text", { "class": "chart__label", x: Math.min(rx, w - 4), y: T + barH + 18, "text-anchor": rx > w - 80 ? "end" : "middle" }, "Revenue", svg);
    }
    var y0 = T + barH + gap;
    var narrow = w < 520, colV = narrow ? w : w - 130, colP = w;
    parts.forEach(function (p, i) {
      var y = y0 + i * rowH;
      el("rect", { "class": p.cls, x: 0, y: y + 5, width: 12, height: 12, opacity: p.op }, null, svg);
      el("text", { "class": "chart__value", x: 22, y: y + 15, "font-weight": p.cls === "up" ? 600 : 400 }, p.n, svg);
      var pctTxt = (p.v / C.rev * 100).toFixed(0) + "%";
      if (narrow) {
        var tv = el("text", { "class": "chart__value", x: colV, y: y + 15, "text-anchor": "end" }, "$" + p.v.toFixed(1) + "bn", svg);
        el("tspan", { "class": "chart__label" }, "  " + pctTxt, tv);
      } else {
        el("text", { "class": "chart__value", x: colV, y: y + 15, "text-anchor": "end" }, "$" + p.v.toFixed(1) + "bn", svg);
        el("text", { "class": "chart__label", x: colP, y: y + 15, "text-anchor": "end" }, pctTxt + " of revenue", svg);
      }
      el("line", { "class": "grid-line", x1: 0, x2: w, y1: y + rowH - 2, y2: y + rowH - 2 }, null, svg);
    });
    if (C.ni < 0) {
      var yl = y0 + parts.length * rowH;
      el("text", { "class": "chart__value", x: 22, y: yl + 15, "font-weight": 600 }, "Net loss", svg);
      el("text", { "class": "chart__value mv--down", x: colV, y: yl + 15, "text-anchor": "end" }, MINUS + "$" + Math.abs(C.ni).toFixed(1) + "bn", svg);
    }
  }

  /* Colour signed percentages in a readout (DESIGN.md, The Rise and Fall Rule). */
  function setRead(node, text) {
    node.textContent = "";
    text.split(/([+−]\d[\d,.]*%)/).forEach(function (part) {
      if (!part) return;
      if (/^[+−]\d/.test(part) && /%$/.test(part)) {
        var sp = document.createElement("span");
        sp.className = part[0] === "+" ? "mv--up" : "mv--down";
        sp.textContent = part;
        node.appendChild(sp);
      } else node.appendChild(document.createTextNode(part));
    });
  }

  /* Column charts over fiscal years or quarters: grouped series around a zero
     line, an optional line series, a readout for the column under the pointer. */
  function nice(max) {
    var p = Math.pow(10, Math.floor(Math.log10(max || 1))), m = max / p;
    return (m <= 1 ? 1 : m <= 2 ? 2 : m <= 2.5 ? 2.5 : m <= 5 ? 5 : 10) * p;
  }
  function columns(box, read, cats, series, opt) {
    var w = box ? box.clientWidth : 0;
    if (!w) return;
    opt = opt || {};
    var h = opt.h || Math.max(180, Math.min(260, w * 0.42)), T = 16, B = 24, R = 46;
    var vals = [];
    series.forEach(function (s) { s.vals.forEach(function (v) { if (v != null) vals.push(v); }); });
    if (!vals.length) { box.textContent = ""; return; }
    var hi = Math.max(0, Math.max.apply(null, vals)), lo = Math.min(0, Math.min.apply(null, vals));
    var step = nice((hi - lo) / 4);
    hi = Math.ceil(hi / step) * step; lo = Math.floor(lo / step) * step;
    if (hi === lo) hi = lo + step;
    var Y = function (v) { return T + (h - T - B) * (hi - v) / (hi - lo); };
    var svg = svgIn(box, w, h, opt.label || "");
    for (var v = lo; v <= hi + step / 2; v += step) {
      el("line", { "class": Math.abs(v) < step / 1e6 ? "zero-line" : "grid-line", x1: 0, x2: w - R, y1: Y(v), y2: Y(v) }, null, svg);
      el("text", { "class": "chart__label", x: w - R + 6, y: Y(v) + 4 }, (opt.fmt || String)(v), svg);
    }
    var bars = series.filter(function (s) { return s.type !== "line"; });
    var cw = (w - R) / cats.length, inner = cw * 0.72, bw = inner / bars.length;
    var band = el("rect", { "class": "hover-band", x: 0, y: T, width: cw, height: h - T - B, opacity: 0 }, null, svg);
    svg.insertBefore(band, svg.firstChild);
    cats.forEach(function (c, i) {
      var x0 = i * cw + (cw - inner) / 2;
      bars.forEach(function (s, k) {
        var v = s.vals[i];
        if (v == null) return;
        var y = Math.min(Y(v), Y(0)), bh = Math.max(1, Math.abs(Y(v) - Y(0)));
        var r = el("rect", { "class": s.cls, x: x0 + k * bw + 1, y: y, width: Math.max(2, bw - 2), height: bh }, null, svg);
        if (s.cls === "fill") { r.setAttribute("fill", "var(--chart-fill)"); r.setAttribute("stroke", "var(--chart-line)"); }
        if (s.cls === "hollow") { r.setAttribute("fill", "none"); r.setAttribute("stroke", "var(--chart-line)"); r.setAttribute("stroke-dasharray", "3 2"); }
      });
      el("text", { "class": "chart__label", x: i * cw + cw / 2, y: h - 6, "text-anchor": "middle" }, w < 480 && cats.length > 5 ? c.replace(/^(\w{3}) \d\d(\d\d)$/, "$1 $2") : c, svg);
    });
    series.filter(function (s) { return s.type === "line"; }).forEach(function (s) {
      var pts = [];
      s.vals.forEach(function (v, i) { if (v != null) pts.push([i * cw + cw / 2, Y(v)]); });
      if (pts.length > 1) el("path", { "class": "line", d: "M" + pts.map(function (p) { return p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" L") }, null, svg);
      pts.forEach(function (p) { el("circle", { "class": "dot", cx: p[0], cy: p[1], r: 3.5 }, null, svg); });
    });
    function show(i) {
      i = Math.max(0, Math.min(cats.length - 1, i));
      band.setAttribute("x", i * cw);
      band.setAttribute("opacity", 1);
      if (read) setRead(read, cats[i] + ": " + series.map(function (s) {
        return s.name + " " + (s.vals[i] == null ? "n/a" : (opt.fmtRead || opt.fmt || String)(s.vals[i], s));
      }).join(", ") + (opt.extra ? opt.extra(i) : ""));
    }
    svg.setAttribute("tabindex", "0");
    svg.addEventListener("pointermove", function (e) {
      var b = svg.getBoundingClientRect();
      show(Math.floor((e.clientX - b.left) / (b.width * (w - R) / w) * cats.length));
    });
    svg.addEventListener("keydown", function (e) {
      var cur = +(band.getAttribute("x")) / cw;
      var st = { ArrowLeft: -1, ArrowRight: 1 }[e.key];
      if (st) { e.preventDefault(); show(Math.round(cur) + st); }
    });
    show(cats.length - 1);
  }
  var bn = function (v) { return (v < 0 ? MINUS : "") + "$" + Math.abs(v).toLocaleString("en-US", { maximumFractionDigits: Math.abs(v) < 10 ? 1 : 0 }) + "bn"; };
  var axisBn = function (v) { return (v < 0 ? MINUS : "") + "$" + Math.abs(v).toLocaleString("en-US", { maximumFractionDigits: 1 }); };
  function yoy(arr, i, back) {
    var a = arr[i], b = arr[i - back];
    if (a == null || b == null || b <= 0) return null;
    return (a / b - 1) * 100;
  }

  function drawYears() {
    var Y = D.years;
    if (!Y) return;
    columns(document.getElementById("co-years"), document.getElementById("co-years-read"), Y.years, [
      { name: "Revenue", vals: Y.rev, cls: "fill" },
      { name: "Net income", vals: Y.ni, cls: "bar" }
    ], { fmt: axisBn, fmtRead: bn, label: D.name + " revenue and net income by fiscal year",
      extra: function (i) {
        var g = yoy(Y.rev, i, 1), m = Y.rev[i] && Y.ni[i] != null ? Y.ni[i] / Y.rev[i] * 100 : null;
        return (m != null ? ", net margin " + m.toFixed(1) + "%" : "") + (g != null ? ". Revenue " + signed(g, 1, "%") + " on the year before" : "");
      } });
  }
  function drawQuarters() {
    var Q = D.quarters;
    if (!Q) return;
    var read = document.getElementById("co-q-read");
    var extra = function (i) {
      var g = yoy(Q.rev, i, 4);
      return g != null ? ". Revenue " + signed(g, 1, "%") + " on a year earlier" : "";
    };
    var both = [{ name: "Revenue", vals: Q.rev, cls: "fill" }];
    columns(document.getElementById("co-qrev"), read, Q.labels, both, { fmt: axisBn, fmtRead: bn, h: 190, label: "Quarterly revenue", extra: extra });
    columns(document.getElementById("co-qeps"), read, Q.labels, [{ name: "EPS", vals: Q.eps, cls: "bar" }],
      { fmt: function (v) { return (v < 0 ? MINUS : "") + "$" + Math.abs(v).toFixed(v % 1 ? 2 : 0); }, h: 190, label: "Quarterly diluted EPS",
        fmtRead: function (v) { return (v < 0 ? MINUS : "") + "$" + Math.abs(v).toFixed(2); } });
    // Start the shared readout on the latest quarter with revenue growth.
    setRead(read, Q.labels[Q.labels.length - 1] + ": Revenue " + (Q.rev[Q.rev.length - 1] == null ? "n/a" : bn(Q.rev[Q.rev.length - 1])) +
      ", EPS " + (Q.eps[Q.eps.length - 1] == null ? "n/a" : "$" + Q.eps[Q.eps.length - 1].toFixed(2)) + extra(Q.labels.length - 1));
  }
  function drawCash() {
    var Y = D.years;
    if (!Y) return;
    columns(document.getElementById("co-cash"), document.getElementById("co-cash-read"), Y.years, [
      { name: "Cash from operations", vals: Y.ocf, cls: "fill" },
      { name: "Capital spending", vals: Y.capex, cls: "down" },
      { name: "Free cash flow", vals: Y.fcf, cls: "bar" }
    ], { fmt: axisBn, fmtRead: bn, label: D.name + " cash flow by fiscal year" });
  }
  function drawBalance() {
    var Y = D.years;
    if (!Y) return;
    var ser = [];
    if (Y.cash.some(function (v) { return v != null; })) ser.push({ name: "Cash and investments", vals: Y.cash, cls: "fill" });
    ser.push({ name: "Debt", vals: Y.debt, cls: "bar" });
    ser.push({ name: "Equity", vals: Y.equity, cls: "hollow" });
    columns(document.getElementById("co-bs"), document.getElementById("co-bs-read"), Y.years, ser,
      { fmt: axisBn, fmtRead: bn, label: D.name + " cash, debt and equity by fiscal year" });
  }
  function drawShareholders() {
    var Y = D.years;
    if (!Y) return;
    columns(document.getElementById("co-sh"), document.getElementById("co-sh-read"), Y.years, [
      { name: "Dividends", vals: Y.div.map(function (v) { return v == null ? 0 : v; }), cls: "bar" },
      { name: "Buybacks", vals: Y.buy.map(function (v) { return v == null ? 0 : v; }), cls: "fill" },
      { name: "Net income", vals: Y.ni, type: "line" }
    ], { fmt: axisBn, fmtRead: bn, label: D.name + " dividends and buybacks against net income",
      extra: function (i) {
        var paid = (Y.div[i] || 0) + (Y.buy[i] || 0);
        return Y.ni[i] > 0 ? ". Paid out " + (paid / Y.ni[i] * 100).toFixed(0) + "% of net income" : "";
      } });
  }

  /* One line over dates, with a dashed reference: P/E over time, drawdown. */
  function lineChart(box, read, pts, opt) {
    var w = box ? box.clientWidth : 0;
    if (!w || !pts || pts.length < 2) return;
    var h = opt.h || Math.max(180, Math.min(260, w * 0.38)), T = 10, B = 24, R = 46;
    var vs = pts.map(function (p) { return p[1]; });
    var lo = Math.min.apply(null, vs.concat(opt.ref != null ? [opt.ref] : [])), hi = Math.max.apply(null, vs.concat(opt.ref != null ? [opt.ref] : []));
    if (opt.floor0) hi = Math.max(hi, 0);
    var step = nice((hi - lo) / 4 || 1);
    lo = Math.floor(lo / step) * step; hi = Math.ceil(hi / step) * step;
    var X = function (i) { return (w - R) * i / (pts.length - 1); };
    var Yf = function (v) { return T + (h - T - B) * (hi - v) / (hi - lo); };
    var svg = svgIn(box, w, h, opt.label);
    for (var v = lo; v <= hi + step / 2; v += step) {
      el("line", { "class": "grid-line", x1: 0, x2: w - R, y1: Yf(v), y2: Yf(v) }, null, svg);
      el("text", { "class": "chart__label", x: w - R + 6, y: Yf(v) + 4 }, opt.fmt(v), svg);
    }
    var lab = opt.monthly ? function (d) { return day(d).replace(/^\d+ /, ""); } : day;
    el("text", { "class": "chart__label", x: 0, y: h - 6 }, lab(pts[0][0]), svg);
    el("text", { "class": "chart__label", x: w - R, y: h - 6, "text-anchor": "end" }, lab(pts[pts.length - 1][0]), svg);
    var d = "M" + pts.map(function (p, i) { return X(i).toFixed(1) + " " + Yf(p[1]).toFixed(1); }).join(" L");
    if (opt.area) el("path", { d: d + " L" + X(pts.length - 1).toFixed(1) + " " + Yf(0) + " L0 " + Yf(0) + " Z", "class": "band-down" }, null, svg);
    if (opt.ref != null) el("line", { "class": "ref", x1: 0, x2: w - R, y1: Yf(opt.ref), y2: Yf(opt.ref) }, null, svg);
    el("path", { "class": "line", d: d }, null, svg);
    var xh = el("line", { "class": "cross", y1: T, y2: h - B }, null, svg);
    var dot = el("circle", { "class": "dot", r: 3.5 }, null, svg);
    var cur = pts.length - 1;
    function show(i) {
      cur = Math.max(0, Math.min(pts.length - 1, i));
      xh.setAttribute("x1", X(cur)); xh.setAttribute("x2", X(cur));
      dot.setAttribute("cx", X(cur)); dot.setAttribute("cy", Yf(pts[cur][1]));
      if (read) setRead(read, opt.read(pts[cur]));
    }
    svg.setAttribute("tabindex", "0");
    svg.addEventListener("pointermove", function (e) {
      var b = svg.getBoundingClientRect();
      show(Math.round((e.clientX - b.left) / (b.width * (w - R) / w) * (pts.length - 1)));
    });
    svg.addEventListener("keydown", function (e) {
      var st = { ArrowLeft: -1, ArrowRight: 1 }[e.key];
      if (st) { e.preventDefault(); show(cur + st); }
    });
    show(cur);
  }
  function drawPE() {
    var P = D.pe;
    if (!P) return;
    var avg = P.reduce(function (a, p) { return a + p[1]; }, 0) / P.length;
    lineChart(document.getElementById("co-pe"), document.getElementById("co-pe-read"), P, {
      ref: avg, monthly: true, label: D.name + " P/E over time against its average of " + avg.toFixed(1) + "x",
      fmt: function (v) { return v.toFixed(0) + "x"; },
      read: function (p) { return day(p[0]).replace(/^\d+ /, "") + ": P/E " + p[1].toFixed(1) + "x, average " + avg.toFixed(1) + "x"; }
    });
  }
  function drawDD() {
    if (!D.risk) return;
    lineChart(document.getElementById("co-dd"), document.getElementById("co-dd-read"), D.risk.dd, {
      area: true, floor0: true, label: D.name + " below its highest close so far, over the past year",
      fmt: function (v) { return (v < 0 ? MINUS : "") + Math.abs(v).toFixed(0) + "%"; },
      read: function (p) { return day(p[0]) + ": " + (p[1] < -0.05 ? signed(p[1], 1, "%") + " below the high so far" : "at its high so far"); }
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
      setRead(ctxRead, day(rows[cur][0]) + ": " + D.name + " " + usd(rows[cur][1]) + " (" + signed(A[cur] - 100, 1, "%") + ")" +
        (both ? ", S&P 500 " + spx[rows[cur][0]].toLocaleString("en-US", { maximumFractionDigits: 0 }) + " (" + signed(Bv[cur] - 100, 1, "%") + ")" : ""));
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
    drawYears();
    drawQuarters();
    drawCash();
    drawBalance();
    drawShareholders();
    drawPE();
    drawDD();
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
