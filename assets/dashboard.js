/* Andra Markets dashboard pages: one chart drawn at the plot's own pixel size
   from the figures embedded in the page, a range selector, and a readout that
   follows the pointer or the arrow keys. Tokens and rules: DESIGN.md. */
(function () {
  "use strict";
  var page = document.querySelector("[data-dash]");
  var src = document.getElementById("dd-data");
  if (!page || !src) return;
  var D = JSON.parse(src.textContent);
  var plot = page.querySelector(".dd__plot");
  var key = page.querySelector(".dd__key");
  var out = page.querySelector(".dd__read");
  var chips = page.querySelectorAll(".dd .chip");
  var NS = "http://www.w3.org/2000/svg";
  var MINUS = "−";
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var cur = page.getAttribute("data-range");
  var hover = null; // {count, show(i)} for the chart on screen
  var index = -1;

  function el(name, attrs, text) {
    var e = document.createElementNS(NS, name);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  }
  function num(v, dec) {
    return v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec }).replace("-", MINUS);
  }
  function signed(v, dec, unit) {
    var r = Number(v.toFixed(dec));
    return (r > 0 ? "+" : r < 0 ? MINUS : "") + num(Math.abs(r), dec) + (unit || "");
  }
  function parse(iso) {
    var p = iso.split("-");
    return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2]));
  }
  function day(iso) {
    var d = parse(iso);
    return d.getUTCDate() + " " + MONTHS[d.getUTCMonth()] + " " + d.getUTCFullYear();
  }
  function month(iso) {
    var d = parse(iso);
    return MONTHS[d.getUTCMonth()] + " " + d.getUTCFullYear();
  }
  function monthsBack(iso, n) {
    var d = parse(iso);
    var t = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() - n, 1));
    var last = new Date(Date.UTC(t.getUTCFullYear(), t.getUTCMonth() + 1, 0)).getUTCDate();
    t.setUTCDate(Math.min(d.getUTCDate(), last));
    return t.toISOString().slice(0, 10);
  }
  var SPAN = { "1M": 1, "3M": 3, "6M": 6, "1Y": 12, "2Y": 24, "5Y": 60 };

  /* Indices of dates inside the range: the range's start, or everything when
     the range is the last offered and the history is shorter. */
  function window_(dates) {
    var start = monthsBack(dates[dates.length - 1], SPAN[cur]);
    var i0 = 0;
    while (i0 < dates.length - 1 && dates[i0] < start) i0++;
    return i0;
  }
  function extent(vals, padFrac, floor) {
    var lo = Infinity, hi = -Infinity;
    vals.forEach(function (v) { if (v != null) { lo = Math.min(lo, v); hi = Math.max(hi, v); } });
    var pad = Math.max((hi - lo) * padFrac, floor || 0);
    return [lo - pad, hi + pad];
  }
  function gridY(svg, lo, hi, Y, x0, x1, fmt) {
    for (var k = 0; k < 4; k++) {
      var v = lo + (hi - lo) * (k + 0.5) / 4;
      svg.appendChild(el("line", { "class": "grid-line", x1: x0, x2: x1, y1: Y(v), y2: Y(v) }));
      svg.appendChild(el("text", { "class": "chart__label", x: 0, y: Y(v) + 4 }, fmt(v)));
    }
  }
  function dates2(svg, a, b, x0, x1, y) {
    svg.appendChild(el("text", { "class": "chart__label", x: x0, y: y }, a));
    svg.appendChild(el("text", { "class": "chart__label", x: x1, y: y, "text-anchor": "end" }, b));
  }
  function path(pts) {
    return "M" + pts.map(function (p) { return p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" L");
  }
  function keyItems(items) {
    key.replaceChildren();
    items.forEach(function (it) {
      var s = document.createElement("span");
      var i = document.createElement("i");
      i.className = it[0];
      s.appendChild(i);
      s.appendChild(document.createTextNode(it[1]));
      key.appendChild(s);
    });
  }
  function svgFor(w, h) {
    return el("svg", { "class": "chart", viewBox: "0 0 " + w + " " + h, width: w, height: h, "aria-hidden": "true" });
  }
  function nearest(xs, x) {
    var best = 0;
    for (var i = 1; i < xs.length; i++) if (Math.abs(xs[i] - x) < Math.abs(xs[best] - x)) best = i;
    return best;
  }

  /* Time series: commodities (rebased to the range's first day), credit spreads. */
  function lines(w, h) {
    var i0 = window_(D.dates), dates = D.dates.slice(i0);
    var series = D.series.map(function (s) {
      var v = s.values.slice(i0);
      return { s: s, raw: v, v: D.rebase ? v.map(function (x) { return x / v[0] * 100; }) : v };
    });
    var all = [];
    series.forEach(function (s) { all = all.concat(s.v); });
    var L = 40, R = 4, T = 6, B = 22;
    var e = extent(D.rebase ? all.concat([100]) : all.concat(series.some(function (s) { return s.s.area; }) ? [0] : []), 0.08);
    var lo = e[0], hi = e[1];
    var X = function (i) { return L + (w - L - R) * i / Math.max(dates.length - 1, 1); };
    var Y = function (v) { return T + (h - T - B) * (1 - (v - lo) / (hi - lo)); };
    var svg = svgFor(w, h);
    gridY(svg, lo, hi, Y, L, w - R, function (v) { return D.rebase ? num(v, 0) : num(v, 1) + (D.unit || ""); });
    if (D.rebase) svg.appendChild(el("line", { "class": "ref", x1: L, x2: w - R, y1: Y(100), y2: Y(100) }));
    dates2(svg, day(dates[0]), day(dates[dates.length - 1]), L, w - R, h - 4);
    series.forEach(function (s) {
      var pts = s.v.map(function (v, i) { return [X(i), Y(v)]; });
      if (s.s.area) svg.appendChild(el("path", { "class": "area", d: path(pts) + " L" + X(pts.length - 1) + " " + Y(Math.max(lo, 0)) + " L" + L + " " + Y(Math.max(lo, 0)) + " Z" }));
      svg.appendChild(el("path", { "class": s.s.style, d: path(pts) }));
    });
    var cross = el("line", { "class": "cross", y1: T, y2: h - B });
    var dots = series.map(function () { return el("circle", { "class": "dot", r: 3 }); });
    svg.appendChild(cross);
    dots.forEach(function (d) { svg.appendChild(d); });
    keyItems(series.map(function (s) { return [s.s.style === "line" ? "k-solid" : "k-dash", s.s.name]; }));
    var xs = dates.map(function (_, i) { return X(i); });
    return {
      svg: svg, xs: xs,
      label: (D.rebase ? "Rebased to 100 on " + day(dates[0]) + ". " : "") + series.map(function (s) {
        return s.s.name + " " + num(s.raw[s.raw.length - 1], s.s.dec != null ? s.s.dec : D.dec) + (D.unit || "");
      }).join(", ") + " on " + day(dates[dates.length - 1]),
      show: function (i) {
        cross.setAttribute("x1", xs[i]); cross.setAttribute("x2", xs[i]);
        series.forEach(function (s, j) { dots[j].setAttribute("cx", xs[i]); dots[j].setAttribute("cy", Y(s.v[i])); });
        return day(dates[i]) + ": " + series.map(function (s) {
          var dec = s.s.dec != null ? s.s.dec : D.dec;
          return s.s.name + " " + num(s.raw[i], dec) + (D.unit || "") + (D.rebase ? " (" + num(s.v[i], 1) + ")" : "");
        }).join(", ");
      }
    };
  }

  /* Monthly inflation line above monthly payroll bars. */
  function macro(w, h) {
    var n = SPAN[cur], dates = D.dates.slice(-n), cpi = D.cpi.slice(-n), jobs = D.jobs.slice(-n);
    var L = 40, R = 4, T = 6, B = 22, split = (h - B) * 0.58;
    var e = extent(cpi, 0.1, 0.2), lo = e[0], hi = e[1];
    var X = function (i) { return L + (w - L - R) * (i + 0.5) / dates.length; };
    var Y = function (v) { return T + (split - T - 10) * (1 - (v - lo) / (hi - lo)); };
    var m = 1;
    jobs.forEach(function (v) { if (v != null) m = Math.max(m, Math.abs(v)); });
    var zero = split + (h - B - split) / 2, half = (h - B - split) / 2 - 4;
    var svg = svgFor(w, h);
    gridY(svg, lo, hi, Y, L, w - R, function (v) { return num(v, 1) + "%"; });
    svg.appendChild(el("line", { "class": "ref", x1: L, x2: w - R, y1: zero, y2: zero }));
    svg.appendChild(el("text", { "class": "chart__label", x: 0, y: zero + 4 }, "0"));
    var bw = Math.max((w - L - R) / dates.length - 2, 1);
    jobs.forEach(function (v, i) {
      if (v == null) return;
      var bh = Math.max(Math.abs(v) / m * half, 1);
      svg.appendChild(el("rect", { "class": v >= 0 ? "up" : "down", x: X(i) - bw / 2, y: v >= 0 ? zero - bh : zero, width: bw, height: bh }));
    });
    var pts = [];
    cpi.forEach(function (v, i) { if (v != null) pts.push([X(i), Y(v)]); });
    svg.appendChild(el("path", { "class": "line", d: path(pts) }));
    dates2(svg, month(dates[0]), month(dates[dates.length - 1]), L, w - R, h - 4);
    var cross = el("line", { "class": "cross", y1: T, y2: h - B }), dot = el("circle", { "class": "dot", r: 3 });
    svg.appendChild(cross); svg.appendChild(dot);
    keyItems([["k-solid", "Inflation, year on year"], ["sw-up", "Jobs added"], ["sw-down", "Jobs lost"]]);
    var xs = dates.map(function (_, i) { return X(i); });
    var lastC = cpi.length - 1; while (lastC > 0 && cpi[lastC] == null) lastC--;
    var lastJ = jobs.length - 1; while (lastJ > 0 && jobs[lastJ] == null) lastJ--;
    return {
      svg: svg, xs: xs,
      label: "Consumer price inflation " + num(cpi[lastC], 1) + "% in " + month(dates[lastC]) + "; payrolls " + signed(jobs[lastJ], 0) + " thousand in " + month(dates[lastJ]),
      show: function (i) {
        cross.setAttribute("x1", xs[i]); cross.setAttribute("x2", xs[i]);
        dot.setAttribute("cx", xs[i]); dot.setAttribute("cy", cpi[i] == null ? -10 : Y(cpi[i]));
        return month(dates[i]) + ": inflation " + (cpi[i] == null ? "not published" : num(cpi[i], 1) + "%") +
          ", payrolls " + (jobs[i] == null ? "not published" : signed(jobs[i], 0) + " thousand");
      }
    };
  }

  /* Watchlist breadth: advancers less decliners, one bar per session. */
  function breadth(w, h) {
    var dates = D.sessions.map(function (s) { return s[0]; });
    var i0 = window_(dates), rows = D.sessions.slice(i0);
    var L = 28, R = 4, T = 6, B = 22;
    var m = 1;
    rows.forEach(function (r) { m = Math.max(m, Math.abs(r[1] - r[2])); });
    var zero = T + (h - T - B) / 2, half = (h - T - B) / 2;
    var X = function (i) { return L + (w - L - R) * (i + 0.5) / rows.length; };
    var bw = Math.max((w - L - R) / rows.length - 3, 1);
    var svg = svgFor(w, h);
    [m, -m].forEach(function (v) {
      var y = zero - v / m * half;
      svg.appendChild(el("line", { "class": "grid-line", x1: L, x2: w - R, y1: y, y2: y }));
      svg.appendChild(el("text", { "class": "chart__label", x: 0, y: y + 4 }, signed(v, 0)));
    });
    svg.appendChild(el("line", { "class": "ref", x1: L, x2: w - R, y1: zero, y2: zero }));
    rows.forEach(function (r, i) {
      var v = r[1] - r[2], bh = Math.max(Math.abs(v) / m * half, 1);
      svg.appendChild(el("rect", { "class": v >= 0 ? "up" : "down", x: X(i) - bw / 2, y: v >= 0 ? zero - bh : zero, width: bw, height: bh }));
    });
    dates2(svg, day(rows[0][0]), day(rows[rows.length - 1][0]), L, w - R, h - 4);
    var cross = el("line", { "class": "cross", y1: T, y2: h - B });
    svg.appendChild(cross);
    keyItems([["sw-up", "More advancers"], ["sw-down", "More decliners"]]);
    var xs = rows.map(function (_, i) { return X(i); });
    return {
      svg: svg, xs: xs,
      label: rows.length + " sessions from " + day(rows[0][0]) + " to " + day(rows[rows.length - 1][0]),
      show: function (i) {
        cross.setAttribute("x1", xs[i]); cross.setAttribute("x2", xs[i]);
        var r = rows[i];
        return day(r[0]) + ": " + r[1] + " up, " + r[2] + " down, " + r[3] + " unchanged (" + signed(r[1] - r[2], 0) + ")";
      }
    };
  }

  /* A term structure today against the same curve at the range's start. */
  function curve(w, h) {
    var cmp = D.compare[cur];
    var L = 44, R = 10, T = 8, B = 22;
    var vals = D.values.concat(cmp.values).concat(D.ref ? [D.ref.value] : []);
    var e = extent(vals, 0.12, D.unit === "%" ? 0.05 : 0.5), lo = e[0], hi = e[1];
    var x0 = D.x[0], x1 = D.x[D.x.length - 1];
    var X = function (i) { return L + (w - L - R) * (D.x[i] - x0) / (x1 - x0); };
    var Y = function (v) { return T + (h - T - B) * (1 - (v - lo) / (hi - lo)); };
    var dec = D.dec != null ? D.dec : 2;
    var svg = svgFor(w, h);
    gridY(svg, lo, hi, Y, L, w - R, function (v) { return num(v, D.unit === "%" ? 2 : 1) + (D.unit || ""); });
    if (D.ref) svg.appendChild(el("line", { "class": "ref", x1: L, x2: w - R, y1: Y(D.ref.value), y2: Y(D.ref.value) }));
    // Label every tenor that fits: about 7px a character at 12px, 8px apart.
    var lastRight = -Infinity, lastLeft = X(D.labels.length - 1) - D.labels[D.labels.length - 1].length * 7;
    D.labels.forEach(function (lb, i) {
      var anchor = i === 0 ? "start" : i === D.labels.length - 1 ? "end" : "middle";
      var x = X(i), wid = lb.length * 7;
      var left = anchor === "start" ? x : anchor === "end" ? x - wid : x - wid / 2;
      if (anchor === "middle" && (left < lastRight + 8 || left + wid > lastLeft - 8)) return;
      svg.appendChild(el("text", { "class": "chart__label", x: x, y: h - 4, "text-anchor": anchor }, lb));
      lastRight = left + wid;
    });
    var a = D.values.map(function (v, i) { return [X(i), Y(v)]; });
    var b = cmp.values.map(function (v, i) { return [X(i), Y(v)]; });
    svg.appendChild(el("path", { "class": "dash", d: path(b) }));
    svg.appendChild(el("path", { "class": "line", d: path(a) }));
    a.forEach(function (p) { svg.appendChild(el("circle", { "class": "dot", cx: p[0], cy: p[1], r: 2.5 })); });
    var cross = el("line", { "class": "cross", y1: T, y2: h - B }), ring = el("circle", { "class": "dot", r: 4 });
    svg.appendChild(cross); svg.appendChild(ring);
    var items = [["k-solid", day(D.date)], ["k-dash", day(cmp.date)]];
    if (D.ref) items.push(["k-ref", D.ref.name + " " + num(D.ref.value, 2) + "%, " + day(D.ref.date)]);
    keyItems(items);
    var change = function (i) {
      var dlt = D.values[i] - cmp.values[i];
      return D.unit === "%" ? signed(dlt * 100, 0, "bp") : signed(dlt, 2, " points");
    };
    var xs = D.x.map(function (_, i) { return X(i); });
    return {
      svg: svg, xs: xs,
      label: "On " + day(D.date) + " against " + day(cmp.date) + ": " + D.labels.map(function (lb, i) {
        return lb + " " + num(D.values[i], dec) + (D.unit || "");
      }).join(", "),
      show: function (i) {
        cross.setAttribute("x1", xs[i]); cross.setAttribute("x2", xs[i]);
        ring.setAttribute("cx", xs[i]); ring.setAttribute("cy", a[i][1]);
        return D.labels[i] + ": " + num(D.values[i], dec) + (D.unit || "") + " on " + day(D.date) + ", " +
          num(cmp.values[i], dec) + (D.unit || "") + " on " + day(cmp.date) + " (" + change(i) + ")";
      }
    };
  }

  /* Changes over the range, one labelled bar each, largest gain first. */
  function perf(w) {
    var r = D.ranges[cur];
    var rows = D.names.map(function (n, i) { return [n, r.values[i], r.from[i], r.to[i]]; })
      .sort(function (p, q) { return q[1] - p[1]; });
    var row = 26, T = 2, h = T + row * rows.length;
    var nameW = Math.min(150, w * 0.4), valW = 64;
    var x0 = nameW + (w - nameW - valW) / 2, half = (w - nameW - valW) / 2 - 4;
    var m = 0.01;
    rows.forEach(function (p) { m = Math.max(m, Math.abs(p[1])); });
    var svg = svgFor(w, h);
    svg.appendChild(el("line", { "class": "ref", x1: x0, x2: x0, y1: 0, y2: h }));
    var bands = rows.map(function (p, i) {
      var y = T + i * row, bwid = Math.max(Math.abs(p[1]) / m * half, 1);
      svg.appendChild(el("text", { "class": "chart__label", x: 0, y: y + 17 }, p[0]));
      svg.appendChild(el("rect", { "class": p[1] >= 0 ? "up" : "down", x: p[1] >= 0 ? x0 : x0 - bwid, y: y + 6, width: bwid, height: 14 }));
      svg.appendChild(el("text", { "class": "chart__value", x: w, y: y + 17, "text-anchor": "end" }, signed(p[1], 2, "%")));
      return y;
    });
    var band = el("rect", { "class": "hover-band", x: 0, y: 0, width: w, height: row });
    svg.insertBefore(band, svg.firstChild);
    keyItems(D.sign ? [["sw-up", "Dollar stronger"], ["sw-down", "Dollar weaker"]] : [["sw-up", "Up"], ["sw-down", "Down"]]);
    var span = cur === "1D" ? "the day" : cur;
    return {
      svg: svg, ys: bands, h: h,
      label: "Change over " + span + ": " + rows.map(function (p) { return p[0] + " " + signed(p[1], 2, "%"); }).join(", "),
      show: function (i) {
        band.setAttribute("y", bands[i]);
        var p = rows[i];
        return p[0] + ": " + signed(p[1], 2, "%") + ", close of " + day(p[2]) + " to close of " + day(p[3]);
      }
    };
  }

  /* Correlation of daily returns over the window, every pair. */
  function matrix(w) {
    var win = D.windows[cur], n = D.names.length;
    var labW = Math.min(118, w * 0.32), top = 22;
    var c = Math.min((w - labW) / n, 72), h = top + c * n;
    var svg = svgFor(w, h);
    var cells = [];
    D.names.forEach(function (name, j) {
      svg.appendChild(el("text", { "class": "chart__label", x: labW + c * (j + 0.5), y: 14, "text-anchor": "middle" }, D.short[j]));
    });
    D.names.forEach(function (name, i) {
      svg.appendChild(el("text", { "class": "chart__label", x: 0, y: top + c * (i + 0.5) + 4 }, name));
      for (var j = 0; j < n; j++) {
        var v = win.matrix[i][j];
        svg.appendChild(el("rect", { "class": v >= 0 ? "up" : "down", x: labW + c * j + 1, y: top + c * i + 1, width: c - 2, height: c - 2, opacity: (0.12 + 0.45 * Math.abs(v)).toFixed(2) }));
        svg.appendChild(el("text", { "class": "chart__value", x: labW + c * (j + 0.5), y: top + c * (i + 0.5) + 4, "text-anchor": "middle" }, signed(v, 2).replace(/^\+/, "")));
        cells.push([i, j]);
      }
    });
    var ring = el("rect", { "class": "cell-ring", width: c, height: c });
    svg.appendChild(ring);
    keyItems([["sw-up", "Move together"], ["sw-down", "Move apart"]]);
    return {
      svg: svg, cells: cells, labW: labW, top: top, c: c, n: n, h: h,
      label: "Correlation of daily returns over " + win.sessions + " sessions from " + day(win.from) + ": " +
        cells.filter(function (p) { return p[0] < p[1]; }).map(function (p) {
          return D.names[p[0]] + " and " + D.names[p[1]] + " " + signed(win.matrix[p[0]][p[1]], 2);
        }).join(", "),
      show: function (k) {
        var p = cells[k];
        ring.setAttribute("x", labW + c * p[1]); ring.setAttribute("y", top + c * p[0]);
        return D.names[p[0]] + " and " + D.names[p[1]] + ": " + signed(win.matrix[p[0]][p[1]], 2) +
          " over " + win.sessions + " sessions, " + day(win.from) + " to " + page.getAttribute("data-asof");
      }
    };
  }

  var KINDS = { lines: lines, macro: macro, breadth: breadth, curve: curve, perf: perf, matrix: matrix };

  function draw() {
    var w = plot.clientWidth, h = plot.clientHeight;
    if (!w) return;
    var chart = KINDS[D.kind](w, h);
    plot.replaceChildren(chart.svg);
    if (chart.h) plot.style.height = chart.h + "px";
    plot.setAttribute("aria-label", page.getAttribute("data-title") + ". " + chart.label);
    var count = chart.xs ? chart.xs.length : chart.ys ? chart.ys.length : chart.cells.length;
    hover = { count: count, show: chart.show };
    function pick(e) {
      var r = chart.svg.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
      if (chart.xs) return nearest(chart.xs, x);
      if (chart.ys) return Math.max(0, Math.min(chart.ys.length - 1, Math.floor((y - 2) / 26)));
      var i = Math.floor((y - chart.top) / chart.c), j = Math.floor((x - chart.labW) / chart.c);
      if (i < 0 || j < 0 || i >= chart.n || j >= chart.n || i === j) return -1;
      return i * chart.n + j;
    }
    chart.svg.addEventListener("pointermove", function (e) {
      var k = pick(e);
      if (k >= 0) show(k);
    });
    // Start on the latest point, the top bar, or the first pair off the diagonal.
    show(index >= 0 && index < count ? index : chart.xs ? count - 1 : chart.cells ? 1 : 0);
  }
  function show(k) {
    index = k;
    out.textContent = hover.show(k);
  }
  plot.addEventListener("keydown", function (e) {
    if (!hover) return;
    var step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
    if (e.key === "Home") step = -hover.count;
    if (e.key === "End") step = hover.count;
    if (!step) return;
    e.preventDefault();
    show(Math.max(0, Math.min(hover.count - 1, index + step)));
  });
  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      cur = chip.getAttribute("data-range");
      chips.forEach(function (c) { c.setAttribute("aria-pressed", String(c === chip)); });
      index = -1;
      draw();
    });
  });
  if ("ResizeObserver" in window) new ResizeObserver(function () { draw(); }).observe(plot);
  else window.addEventListener("resize", draw);
  draw();
})();
