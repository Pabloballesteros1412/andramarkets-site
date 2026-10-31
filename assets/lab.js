/* Andra Markets Lab tools: bond price and duration, options payoff, compound
   growth, Black-Scholes pricer, yield to maturity, two-asset frontier,
   discounted cash flow, position sizing and value at risk, real return, and
   risk and correlation. Everything is calculated in the browser from the
   inputs on the page: nothing is sent or stored. The inputs that differ from
   the defaults are kept in the URL fragment, which the browser never sends, so
   a link shares a setup. The risk tool loads the daily
   returns baked into assets/lab-risk-<market>.js at deploy time. Charts are drawn at the
   plot's own pixel width, with a readout that follows the pointer or the arrow
   keys (as on the dashboard pages). Tokens and rules: DESIGN.md. */
(function () {
  "use strict";
  var page = document.querySelector("[data-tool]");
  if (!page) return;
  var tool = page.getAttribute("data-tool");
  var NS = "http://www.w3.org/2000/svg";
  var MINUS = "−";
  var plot = page.querySelector(".dd__plot");
  var readout = page.querySelector(".dd__read");
  var result = page.querySelector(".lt-result");
  var status = page.querySelector(".lt-status");
  var hover = null;
  var index = -1;

  function el(name, attrs, text) {
    var e = document.createElementNS(NS, name);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  }
  function num(v, dec) {
    var s = v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec });
    // a value that rounds to zero carries no sign ("0.000", never "−0.000")
    if (/^-[0.,]+$/.test(s)) s = s.slice(1);
    return s.replace("-", MINUS);
  }
  function signed(v, dec, unit) {
    var r = Number(v.toFixed(dec));
    return (r > 0 ? "+" : r < 0 ? MINUS : "") + num(Math.abs(r), dec) + (unit || "");
  }
  // A rise or a fall in green or red, its sign kept (The Rise and Fall Rule).
  function mv(text) {
    var c = text.charAt(0) === "+" ? "mv mv--up" : text.charAt(0) === MINUS ? "mv mv--down" : "";
    return c ? '<span class="' + c + '">' + text + "</span>" : text;
  }
  function val(id) {
    var input = document.getElementById(id);
    var v = parseFloat(input.value);
    var lo = parseFloat(input.min), hi = parseFloat(input.max);
    var bad = !isFinite(v) || v < lo || v > hi;
    input.setAttribute("aria-invalid", bad ? "true" : "false");
    return bad ? null : v;
  }
  function pressed(group) {
    var on = page.querySelector('[data-group="' + group + '"] .chip[aria-pressed="true"]');
    return on ? on.getAttribute("data-value") : null;
  }
  function kpis(rows) {
    result.innerHTML = rows.map(function (r) {
      return '<li class="kpi__item"><span class="kpi__name">' + r[0] + '</span><span class="kpi__level">' + r[1] +
        '</span><span class="kpi__chg">' + (r[2] || "") + "</span></li>";
    }).join("");
  }
  function invalid() {
    var bad = page.querySelectorAll('input[aria-invalid="true"]');
    if (!bad.length) {
      status.textContent = "";
      return false;
    }
    var names = Array.prototype.map.call(bad, function (b) {
      var l = page.querySelector('label[for="' + b.id + '"]');
      return l ? l.firstChild.textContent.trim() : b.id;
    });
    status.textContent = "Check " + names.join(", ") + ": each must be within its range.";
    return true;
  }

  // Round tick values inside [lo, hi]: steps of 1, 2, 2.5 or 5 times a power of ten.
  function nice(lo, hi, n) {
    var raw = (hi - lo) / n;
    if (!(raw > 0) || !isFinite(raw)) return [];
    var p = Math.pow(10, Math.floor(Math.log(raw) / Math.LN10)), step = p;
    [1, 2, 2.5, 5, 10].some(function (m) { step = m * p; return m * p >= raw; });
    // tolerances scale with the step: a fixed one (1e-9) made a range of near-zero values
    // (a deep out-of-the-money option) loop for seconds and freeze the page
    var out = [], eps = step * 1e-6;
    for (var v = Math.ceil(lo / step) * step; v <= hi + eps && out.length < 50; v += step) out.push(Math.abs(v) < eps ? 0 : v);
    return out;
  }

  /* One line chart: xs, series [{values, cls, area}], x and y formatters, a
     readout function, optional reference y (zero line) and a marked point. */
  function draw(o) {
    plot.innerHTML = "";
    var w = plot.clientWidth, h = plot.clientHeight;
    if (!w || !h) return;
    var L = 56, R = 12, T = 12, B = 28;
    var all = [];
    o.series.forEach(function (s) { all = all.concat(s.values.filter(isFinite)); });
    if (o.ref != null) all.push(o.ref);
    var lo = Math.min.apply(null, all), hi = Math.max.apply(null, all);
    if (o.floor0) lo = Math.min(0, lo);
    // a series that is flat to within rounding (all values about zero) draws as a flat line
    var pad = hi - lo > 1e-9 * Math.max(1, Math.abs(hi), Math.abs(lo)) ? (hi - lo) * 0.08 : 1;
    lo -= o.floor0 && lo === 0 ? 0 : pad;
    hi += pad;
    var x0 = o.xs[0], x1 = o.xs[o.xs.length - 1];
    var X = function (x) { return L + (w - L - R) * (x - x0) / (x1 - x0); };
    var Y = function (y) { return T + (h - T - B) * (1 - (y - lo) / (hi - lo)); };
    var svg = el("svg", { "class": "chart", width: w, height: h, viewBox: "0 0 " + w + " " + h, "aria-hidden": "true" });
    nice(lo, hi, 4).forEach(function (gy) {
      svg.appendChild(el("line", { "class": "grid-line", x1: L, x2: w - R, y1: Y(gy), y2: Y(gy) }));
      svg.appendChild(el("text", { "class": "chart__label", x: L - 8, y: Y(gy) + 4, "text-anchor": "end" }, o.fy(gy)));
    });
    var xt = nice(x0, x1, w < 480 ? 3 : 5);
    xt.forEach(function (tx) {
      svg.appendChild(el("text", { "class": "chart__label", x: X(tx), y: h - 8, "text-anchor": X(tx) < L + 20 ? "start" : X(tx) > w - R - 20 ? "end" : "middle" }, o.fx(tx)));
    });
    if (o.ref != null) svg.appendChild(el("line", { "class": "ref", x1: L, x2: w - R, y1: Y(o.ref), y2: Y(o.ref) }));
    o.series.forEach(function (s) {
      var d = "";
      s.values.forEach(function (v, i) { d += (i ? " L" : "M") + X(o.xs[i]).toFixed(1) + " " + Y(v).toFixed(1); });
      if (s.bands) {
        // Gain above the reference line, loss below: regime tints.
        var up = d + " L" + X(x1).toFixed(1) + " " + Y(o.ref).toFixed(1) + " L" + X(x0).toFixed(1) + " " + Y(o.ref).toFixed(1) + " Z";
        var clipU = "lt-cu", clipD = "lt-cd";
        var defs = el("defs", {});
        var cu = el("clipPath", { id: clipU }), cd = el("clipPath", { id: clipD });
        cu.appendChild(el("rect", { x: 0, y: 0, width: w, height: Y(o.ref) }));
        cd.appendChild(el("rect", { x: 0, y: Y(o.ref), width: w, height: h }));
        defs.appendChild(cu); defs.appendChild(cd);
        svg.appendChild(defs);
        svg.appendChild(el("path", { "class": "band-up", d: up, "clip-path": "url(#" + clipU + ")" }));
        svg.appendChild(el("path", { "class": "band-down", d: up, "clip-path": "url(#" + clipD + ")" }));
      }
      if (s.area) {
        svg.appendChild(el("path", { "class": "area", d: d + " L" + X(x1).toFixed(1) + " " + Y(Math.max(lo, 0)).toFixed(1) + " L" + X(x0).toFixed(1) + " " + Y(Math.max(lo, 0)).toFixed(1) + " Z" }));
      }
      svg.appendChild(el("path", { "class": s.cls, d: d }));
    });
    (o.marks || []).forEach(function (m) {
      svg.appendChild(el("circle", { "class": "dot", cx: X(m[0]), cy: Y(m[1]), r: 3 }));
    });
    var cross = el("line", { "class": "cross", y1: T, y2: h - B, x1: -10, x2: -10 });
    var dot = el("circle", { "class": "dot", r: 3.5, cx: -10, cy: -10 });
    svg.appendChild(cross);
    svg.appendChild(dot);
    plot.appendChild(svg);
    var n = o.xs.length;
    hover = {
      count: n,
      show: function (i) {
        index = i;
        var x = X(o.xs[i]);
        cross.setAttribute("x1", x);
        cross.setAttribute("x2", x);
        dot.setAttribute("cx", x);
        dot.setAttribute("cy", Y(o.series[0].values[i]));
        readout.innerHTML = o.read(i);
      },
      at: function (px) {
        var x = x0 + (x1 - x0) * (px - L) / (w - L - R);
        var best = 0;
        for (var i = 1; i < n; i++) if (Math.abs(o.xs[i] - x) < Math.abs(o.xs[best] - x)) best = i;
        return best;
      },
    };
    hover.show(o.start != null ? o.start : n - 1);
  }

  plot.addEventListener("pointermove", function (e) {
    if (!hover) return;
    var r = plot.getBoundingClientRect();
    var k = hover.at(e.clientX - r.left, e.clientY - r.top);
    if (k >= 0) hover.show(k);
  });
  plot.addEventListener("keydown", function (e) {
    if (!hover) return;
    var i = index;
    if (e.key === "ArrowRight") i = Math.min(hover.count - 1, i + 1);
    else if (e.key === "ArrowLeft") i = Math.max(0, i - 1);
    else if (e.key === "Home") i = 0;
    else if (e.key === "End") i = hover.count - 1;
    else return;
    e.preventDefault();
    hover.show(i);
  });

  /* Bond price and duration ----------------------------------------------- */

  function bondPrice(face, cpn, y, years, f) {
    var n = Math.max(1, Math.round(years * f)), c = face * cpn / 100 / f, r = y / 100 / f;
    var p = 0, mac = 0, conv = 0;
    for (var t = 1; t <= n; t++) {
      var cf = c + (t === n ? face : 0);
      var v = Math.pow(1 + r, -t);
      p += cf * v;
      mac += t * cf * v;
      conv += t * (t + 1) * cf * v / Math.pow(1 + r, 2);
    }
    mac = mac / p / f;
    return { price: p, mac: mac, mod: mac / (1 + r), conv: conv / p / (f * f), n: n, c: c };
  }

  function bond() {
    var face = val("b-face"), cpn = val("b-cpn"), y = val("b-yld"), years = val("b-yrs");
    var f = parseInt(pressed("freq"), 10);
    if (invalid()) return;
    var b = bondPrice(face, cpn, y, years, f);
    var dv01 = b.mod * b.price * 0.0001;
    var up = bondPrice(face, cpn, y + 1, years, f).price, dn = bondPrice(face, cpn, Math.max(0, y - 1), years, f).price;
    kpis([
      ["Price", num(b.price, 2), num(b.price / face * 100, 3) + " per 100 face"],
      ["Yield to maturity", num(y, 2) + "%", (f === 2 ? "Semi-annual" : "Annual") + " compounding"],
      ["Macaulay duration", num(b.mac, 2) + " years", "Weighted time to the cash flows"],
      ["Modified duration", num(b.mod, 2), "Price change per 1 point of yield, %"],
      ["Convexity", num(b.conv, 1), "Curvature of price against yield"],
      ["DV01", num(dv01, 4), "Price change per basis point"],
      ["Yield +1 point", num(up, 2), mv(signed((up / b.price - 1) * 100, 2, "%"))],
      ["Yield " + MINUS + "1 point", num(dn, 2), mv(signed((dn / b.price - 1) * 100, 2, "%"))],
    ]);
    var xs = [], ps = [], approx = [];
    var top = Math.max(2 * y, y + 4);
    for (var i = 0; i <= 80; i++) {
      var yy = top * i / 80;
      xs.push(yy);
      ps.push(bondPrice(face, cpn, yy, years, f).price);
      var dy = (yy - y) / 100;
      approx.push(b.price * (1 - b.mod * dy));
    }
    var start = Math.round(y / top * 80);
    draw({
      xs: xs,
      series: [{ values: ps, cls: "line" }, { values: approx, cls: "dash" }],
      marks: [[y, b.price]],
      start: start,
      fx: function (v) { return num(v, v % 1 ? 1 : 0) + "%"; },
      fy: function (v) { return num(v, 0); },
      read: function (i) {
        var chg = signed((ps[i] / b.price - 1) * 100, 2, "%");
        return "Yield " + num(xs[i], 2) + "%: price " + num(ps[i], 2) + ", " + mv(chg) +
          " against today; the duration line says " + num(approx[i], 2) + ".";
      },
    });
  }

  /* Options payoff ---------------------------------------------------------- */

  function ncdf(x) {
    // Abramowitz and Stegun 26.2.17, accurate to about 1e-7.
    var t = 1 / (1 + 0.2316419 * Math.abs(x));
    var d = 0.3989422804014327 * Math.exp(-x * x / 2);
    var p = d * t * (0.31938153 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))));
    return x > 0 ? 1 - p : p;
  }
  function bs(type, S, K, T, r, s) {
    if (type === "stock") return S;
    if (T <= 0 || s <= 0) return Math.max(0, type === "call" ? S - K : K - S);
    var d1 = (Math.log(S / K) + (r + s * s / 2) * T) / (s * Math.sqrt(T)), d2 = d1 - s * Math.sqrt(T);
    return type === "call" ? S * ncdf(d1) - K * Math.exp(-r * T) * ncdf(d2)
      : K * Math.exp(-r * T) * ncdf(-d2) - S * ncdf(-d1);
  }
  var STRATS = {
    "long-call": { name: "Long call", legs: function (k1) { return [["call", k1, 1]]; } },
    "long-put": { name: "Long put", legs: function (k1) { return [["put", k1, 1]]; } },
    "short-call": { name: "Short call", legs: function (k1) { return [["call", k1, -1]]; } },
    "short-put": { name: "Short put", legs: function (k1) { return [["put", k1, -1]]; } },
    "bull-call": { name: "Bull call spread", two: true, legs: function (k1, k2) { return [["call", k1, 1], ["call", k2, -1]]; } },
    "bear-put": { name: "Bear put spread", two: true, legs: function (k1, k2) { return [["put", k2, 1], ["put", k1, -1]]; } },
    "straddle": { name: "Long straddle", legs: function (k1) { return [["call", k1, 1], ["put", k1, 1]]; } },
    "strangle": { name: "Long strangle", two: true, legs: function (k1, k2) { return [["put", k1, 1], ["call", k2, 1]]; } },
    "covered-call": { name: "Covered call", legs: function (k1) { return [["stock", 0, 1], ["call", k1, -1]]; } },
    "protective-put": { name: "Protective put", legs: function (k1) { return [["stock", 0, 1], ["put", k1, 1]]; } },
  };

  function options() {
    var key = pressed("strategy");
    var st = STRATS[key];
    var k2wrap = document.getElementById("o-k2").closest(".lt-field");
    k2wrap.hidden = !st.two;
    var S = val("o-spot"), k1 = val("o-k1"), k2 = st.two ? val("o-k2") : k1;
    var vol = val("o-vol"), days = val("o-days"), rate = val("o-rate");
    if (invalid()) return;
    if (st.two && k2 <= k1) {
      document.getElementById("o-k2").setAttribute("aria-invalid", "true");
      status.textContent = "The higher strike must be above the lower strike.";
      return;
    }
    var T = days / 365, r = rate / 100, s = vol / 100;
    var legs = st.legs(k1, k2);
    var cost = 0;
    legs.forEach(function (l) { cost += l[2] * bs(l[0], S, l[1], T, r, s); });
    function atExpiry(x) {
      var v = 0;
      legs.forEach(function (l) {
        v += l[2] * (l[0] === "stock" ? x : l[0] === "call" ? Math.max(0, x - l[1]) : Math.max(0, l[1] - x));
      });
      return v - cost;
    }
    function today(x) {
      var v = 0;
      legs.forEach(function (l) { v += l[2] * bs(l[0], x, l[1], T, r, s); });
      return v - cost;
    }
    var lo = S * 0.5, hi = S * 1.5, n = 120, xs = [], pe = [], pt = [];
    for (var i = 0; i <= n; i++) {
      var x = lo + (hi - lo) * i / n;
      xs.push(x);
      pe.push(atExpiry(x));
      pt.push(today(x));
    }
    var bes = [];
    for (var j = 1; j <= n; j++) {
      if ((pe[j - 1] < 0) !== (pe[j] < 0) && pe[j] !== pe[j - 1]) {
        bes.push(xs[j - 1] + (xs[j] - xs[j - 1]) * (0 - pe[j - 1]) / (pe[j] - pe[j - 1]));
      }
    }
    // Beyond the chart: a slope still rising at the right edge is unlimited.
    var slopeR = atExpiry(hi * 10) - atExpiry(hi * 9);
    var maxP = Math.max.apply(null, pe), minP = Math.min.apply(null, pe.concat([atExpiry(0)]));
    kpis([
      ["Strategy", st.name, legs.filter(function (l) { return l[0] !== "stock"; }).length + " option leg" + (legs.length > 1 ? "s" : "")],
      [legs[0][0] === "stock" ? "Net cost, share included" : cost >= 0 ? "Net premium paid" : "Net premium received",
        num(Math.abs(cost), 2), "Per share, Black-Scholes"],
      ["Maximum profit", slopeR > 1e-9 ? "Unlimited" : num(maxP, 2), "At expiry, per share"],
      ["Maximum loss", num(Math.abs(Math.min(0, minP)), 2), slopeR < -1e-9 ? "Unlimited above the chart" : "At expiry, per share"],
      ["Break-even", bes.length ? bes.map(function (b) { return num(b, 2); }).join(" and ") : "None in range", "Underlying at expiry"],
      ["Contract of 100", num(Math.abs(cost) * 100, 0), (cost >= 0 ? "Paid" : "Received") + " for one contract"],
    ]);
    var start = Math.round((S - lo) / (hi - lo) * n);
    draw({
      xs: xs,
      series: [{ values: pt, cls: "line" }, { values: pe, cls: "dash", bands: true }],
      ref: 0,
      marks: bes.map(function (b) { return [b, 0]; }),
      start: start,
      fx: function (v) { return num(v, 0); },
      fy: function (v) { return signed(v, v % 1 ? 1 : 0); },
      read: function (i) {
        return "Underlying at " + num(xs[i], 2) + ": at expiry " + mv(signed(pe[i], 2)) +
          ", if it moved there today " + mv(signed(pt[i], 2)) + " per share.";
      },
    });
  }

  /* Compound growth --------------------------------------------------------- */

  function growth() {
    var p0 = val("g-start"), add = val("g-add"), rate = val("g-rate"), years = val("g-yrs");
    if (invalid()) return;
    years = Math.round(years);
    var m = Math.pow(1 + rate / 100, 1 / 12) - 1;
    var xs = [0], total = [p0], paid = [p0];
    var v = p0, c = p0;
    for (var mo = 1; mo <= years * 12; mo++) {
      v = v * (1 + m) + add;
      c += add;
      if (mo % 12 === 0) {
        xs.push(mo / 12);
        total.push(v);
        paid.push(c);
      }
    }
    var gain = v - c;
    var rule = rate > 0 ? Math.log(2) / Math.log(1 + rate / 100) : null;
    kpis([
      ["Final value", num(v, 0), "After " + years + " year" + (years === 1 ? "" : "s")],
      ["Paid in", num(c, 0), num(p0, 0) + " at the start, " + num(add, 0) + " a month"],
      ["Growth", num(gain, 0), c > 0 ? num(gain / c * 100, 0) + "% of what was paid in" : ""],
      ["Growth share of the end value", v > 0 ? num(gain / v * 100, 0) + "%" : "n/a", "The rest is what was paid in"],
      ["Doubling time", rule ? num(rule, 1) + " years" : "n/a", "At " + num(rate, 1) + "% a year, with no additions"],
    ]);
    draw({
      xs: xs,
      series: [{ values: total, cls: "line" }, { values: paid, cls: "dash", area: true }],
      floor0: true,
      fx: function (yv) { return "Year " + num(yv, 0); },
      fy: function (yv) { return yv >= 1e6 ? num(yv / 1e6, yv % 1e6 ? 1 : 0) + "m" : yv >= 1e3 ? num(yv / 1e3, yv % 1e3 ? 1 : 0) + "k" : num(yv, 0); },
      read: function (i) {
        return "Year " + xs[i] + ": value " + num(total[i], 0) + ", of which paid in " + num(paid[i], 0) +
          " and growth " + num(total[i] - paid[i], 0) + ".";
      },
    });
  }

  /* Shared: a curve drawn through (x, y) points in any order (the frontier). */
  function drawXY(o) {
    plot.innerHTML = "";
    var w = plot.clientWidth, h = plot.clientHeight;
    if (!w || !h) return;
    var L = 56, R = 12, T = 12, B = 28;
    var ax = [], ay = [];
    o.series.forEach(function (s) { ax = ax.concat(s.xs); ay = ay.concat(s.ys); });
    var x0 = Math.min(0, Math.min.apply(null, ax)), x1 = Math.max.apply(null, ax) * 1.06;
    var lo = Math.min.apply(null, ay), hi = Math.max.apply(null, ay);
    var pad = hi - lo > 1e-9 * Math.max(1, Math.abs(hi), Math.abs(lo)) ? (hi - lo) * 0.1 : 1;
    lo -= pad; hi += pad;
    var X = function (x) { return L + (w - L - R) * (x - x0) / (x1 - x0); };
    var Y = function (y) { return T + (h - T - B) * (1 - (y - lo) / (hi - lo)); };
    var svg = el("svg", { "class": "chart", width: w, height: h, viewBox: "0 0 " + w + " " + h, "aria-hidden": "true" });
    nice(lo, hi, 4).forEach(function (gy) {
      svg.appendChild(el("line", { "class": "grid-line", x1: L, x2: w - R, y1: Y(gy), y2: Y(gy) }));
      svg.appendChild(el("text", { "class": "chart__label", x: L - 8, y: Y(gy) + 4, "text-anchor": "end" }, o.fy(gy)));
    });
    nice(x0, x1, w < 480 ? 3 : 5).forEach(function (tx) {
      svg.appendChild(el("text", { "class": "chart__label", x: X(tx), y: h - 8, "text-anchor": X(tx) < L + 20 ? "start" : X(tx) > w - R - 20 ? "end" : "middle" }, o.fx(tx)));
    });
    o.series.forEach(function (s) {
      var d = "";
      s.xs.forEach(function (x, i) { d += (i ? " L" : "M") + X(x).toFixed(1) + " " + Y(s.ys[i]).toFixed(1); });
      svg.appendChild(el("path", { "class": s.cls, d: d }));
    });
    (o.marks || []).forEach(function (m) {
      svg.appendChild(el("circle", { "class": "dot", cx: X(m[0]), cy: Y(m[1]), r: 3 }));
      if (m[2]) svg.appendChild(el("text", { "class": "chart__label", x: X(m[0]) + 8, y: Y(m[1]) - 6 }, m[2]));
    });
    var dot = el("circle", { "class": "dot", r: 4.5, cx: -10, cy: -10 });
    svg.appendChild(dot);
    plot.appendChild(svg);
    var main = o.series[0], n = main.xs.length;
    hover = {
      count: n,
      show: function (i) {
        index = i;
        dot.setAttribute("cx", X(main.xs[i]));
        dot.setAttribute("cy", Y(main.ys[i]));
        readout.innerHTML = o.read(i);
      },
      at: function (px, py) {
        var best = 0, bd = Infinity;
        for (var i = 0; i < n; i++) {
          var dx = X(main.xs[i]) - px, dy = py == null ? 0 : Y(main.ys[i]) - py, dd = dx * dx + dy * dy;
          if (dd < bd) { bd = dd; best = i; }
        }
        return best;
      },
    };
    hover.show(o.start != null ? o.start : 0);
  }

  /* Black-Scholes pricer --------------------------------------------------- */

  function npdf(x) { return 0.3989422804014327 * Math.exp(-x * x / 2); }
  function greeks(type, S, K, T, r, q, s) {
    var sq = Math.sqrt(T), d1 = (Math.log(S / K) + (r - q + s * s / 2) * T) / (s * sq), d2 = d1 - s * sq;
    var dq = Math.exp(-q * T), dr = Math.exp(-r * T), call = type === "call";
    var price = call ? S * dq * ncdf(d1) - K * dr * ncdf(d2) : K * dr * ncdf(-d2) - S * dq * ncdf(-d1);
    var delta = call ? dq * ncdf(d1) : dq * (ncdf(d1) - 1);
    var gamma = dq * npdf(d1) / (S * s * sq);
    var vega = S * dq * npdf(d1) * sq / 100;
    var theta = (-S * dq * npdf(d1) * s / (2 * sq) + (call ? q * S * dq * ncdf(d1) - r * K * dr * ncdf(d2)
      : -q * S * dq * ncdf(-d1) + r * K * dr * ncdf(-d2))) / 365;
    var rho = (call ? K * T * dr * ncdf(d2) : -K * T * dr * ncdf(-d2)) / 100;
    return { price: price, delta: delta, gamma: gamma, vega: vega, theta: theta, rho: rho, d1: d1, d2: d2 };
  }

  function pricer() {
    var type = pressed("type"), view = pressed("view");
    var S = val("p-spot"), K = val("p-k"), vol = val("p-vol"), days = val("p-days"), rate = val("p-rate"), div = val("p-div");
    if (invalid()) return;
    var T = days / 365, r = rate / 100, q = div / 100, s = vol / 100;
    var g = greeks(type, S, K, T, r, q, s);
    var field = view === "value" ? "price" : view;
    var intrinsic = Math.max(0, type === "call" ? S - K : K - S);
    kpis([
      [type === "call" ? "Call value" : "Put value", num(g.price, 2), "Per share; " + num(g.price * 100, 0) + " for a contract of 100"],
      ["Intrinsic and time value", num(intrinsic, 2) + " + " + num(g.price - intrinsic, 2), "Exercise value now, and the rest"],
      ["Delta", num(g.delta, 3), "Value change for a 1 move in the price"],
      ["Gamma", num(g.gamma, 4), "Delta change for a 1 move in the price"],
      ["Vega", num(g.vega, 3), "Value change for 1 point of volatility"],
      ["Theta", num(g.theta, 3), "Value change as one day passes"],
      ["Rho", num(g.rho, 3), "Value change for 1 point of interest rate"],
      ["Probability of expiring in the money", num((type === "call" ? ncdf(g.d2) : ncdf(-g.d2)) * 100, 1) + "%", "Under the model, N(d2)"],
    ]);
    var lo = S * 0.5, hi = S * 1.5, n = 120, xs = [], now = [], exp = [];
    for (var i = 0; i <= n; i++) {
      var x = lo + (hi - lo) * i / n, gx = greeks(type, x, K, T, r, q, s);
      xs.push(x);
      now.push(gx[field]);
      exp.push(Math.max(0, type === "call" ? x - K : K - x));
    }
    var names = { value: "value", delta: "delta", gamma: "gamma", vega: "vega", theta: "theta" };
    var dec = { value: 2, delta: 3, gamma: 4, vega: 3, theta: 3 }[view];
    var series = [{ values: now, cls: "line" }];
    if (view === "value") series.push({ values: exp, cls: "dash" });
    page.querySelector(".key").hidden = view !== "value";
    draw({
      xs: xs,
      series: series,
      ref: view === "value" ? null : 0,
      marks: [[S, g[field]]],
      start: Math.round((S - lo) / (hi - lo) * n),
      fx: function (v) { return num(v, 0); },
      fy: function (v) { return num(v, view === "value" ? (v % 1 ? 1 : 0) : dec - 1); },
      read: function (i) {
        return "Underlying at " + num(xs[i], 2) + ": " + names[view] + " " + num(now[i], dec) +
          (view === "value" ? " today, " + num(exp[i], 2) + " at expiry." : ".");
      },
    });
  }

  /* Yield to maturity -------------------------------------------------------- */

  function ytm() {
    var price = val("y-price"), cpn = val("y-cpn"), years = val("y-yrs");
    var f = parseInt(pressed("freq"), 10);
    if (invalid()) return;
    var lo = -5, hi = 60;
    if (bondPrice(100, cpn, hi, years, f).price > price || bondPrice(100, cpn, lo, years, f).price < price) {
      status.textContent = "No yield between −5% and 60% gives that price. Check the price.";
      return;
    }
    for (var k = 0; k < 100; k++) {
      var mid = (lo + hi) / 2;
      if (bondPrice(100, cpn, mid, years, f).price > price) lo = mid; else hi = mid;
      if (hi - lo < 1e-6) break;
    }
    var y = (lo + hi) / 2, b = bondPrice(100, cpn, y, years, f);
    var eff = (Math.pow(1 + y / 100 / f, f) - 1) * 100;
    var pull = 100 - price;
    kpis([
      ["Yield to maturity", num(y, 3) + "%", (f === 2 ? "Semi-annual" : "Annual") + " compounding"],
      ["Effective annual yield", num(eff, 3) + "%", "Per-period rate compounded over a year"],
      ["Current yield", num(cpn / price * 100, 3) + "%", "Annual coupon over the price"],
      [price < 100 ? "Discount to par" : price > 100 ? "Premium over par" : "At par", num(Math.abs(pull), 2), price < 100 ? "Earned as the price pulls to 100" : price > 100 ? "Lost as the price pulls to 100" : "Yield equals the coupon"],
      ["Modified duration", num(b.mod, 2), "Price change per 1 point of yield, %"],
      ["Coupon payments left", String(b.n), num(b.c, 3) + " each per 100 face"],
    ]);
    var xs = [], ps = [], top = Math.max(2 * Math.max(y, 0.5), y + 4), bottom = Math.max(-2, Math.min(0, y - 2));
    for (var i = 0; i <= 80; i++) {
      var yy = bottom + (top - bottom) * i / 80;
      xs.push(yy);
      ps.push(bondPrice(100, cpn, yy, years, f).price);
    }
    draw({
      xs: xs,
      series: [{ values: ps, cls: "line" }],
      marks: [[y, price]],
      start: Math.round((y - bottom) / (top - bottom) * 80),
      fx: function (v) { return num(v, v % 1 ? 1 : 0) + "%"; },
      fy: function (v) { return num(v, 0); },
      read: function (i) {
        return "Yield " + num(xs[i], 2) + "%: price " + num(ps[i], 2) + " per 100 face.";
      },
    });
  }

  /* Two-asset efficient frontier ------------------------------------------- */

  function frontier() {
    var ra = val("f-ra"), va = val("f-va"), rb = val("f-rb"), vb = val("f-vb"), rho = val("f-rho"), rf = val("f-rf");
    if (invalid()) return;
    function mix(w) {
      var v = Math.sqrt(w * w * va * va + (1 - w) * (1 - w) * vb * vb + 2 * w * (1 - w) * rho * va * vb);
      return [v, w * ra + (1 - w) * rb];
    }
    var ws = [], vx = [], ry = [];
    for (var i = 0; i <= 100; i++) {
      var p = mix(i / 100);
      ws.push(i); vx.push(p[0]); ry.push(p[1]);
    }
    // Minimum variance and the highest Sharpe ratio, both within 0% to 100%.
    var den = va * va + vb * vb - 2 * rho * va * vb;
    var wmin = den > 0 ? Math.round(Math.min(1, Math.max(0, (vb * vb - rho * va * vb) / den)) * 100) / 100 : 0.5;
    var best = 0, bs_ = -Infinity;
    for (var j = 0; j <= 100; j++) {
      var m = mix(j / 100), sh = m[0] > 0 ? (m[1] - rf) / m[0] : -Infinity;
      if (sh > bs_) { bs_ = sh; best = j / 100; }
    }
    var mv0 = mix(wmin), tg = mix(best);
    kpis([
      ["Minimum-risk mix", num(wmin * 100, 0) + "% A, " + num((1 - wmin) * 100, 0) + "% B", "Volatility " + num(mv0[0], 2) + "%, return " + num(mv0[1], 2) + "%"],
      ["Highest Sharpe mix", num(best * 100, 0) + "% A, " + num((1 - best) * 100, 0) + "% B", "Volatility " + num(tg[0], 2) + "%, return " + num(tg[1], 2) + "%"],
      ["Its Sharpe ratio", num(bs_, 2), "Return above " + num(rf, 1) + "% per point of volatility"],
      ["Sharpe ratio of A alone", num((ra - rf) / va, 2), ""],
      ["Sharpe ratio of B alone", num((rb - rf) / vb, 2), ""],
      ["Risk cut at the minimum", num(Math.min(va, vb) - mv0[0], 2) + " points", "Below the less volatile asset"],
    ]);
    var cmlX = [0, Math.max.apply(null, vx)], cmlY = [rf, rf + bs_ * cmlX[1]];
    drawXY({
      series: [{ xs: vx, ys: ry, cls: "line" }, { xs: cmlX, ys: cmlY, cls: "dash" }],
      marks: [[va, ra, "A"], [vb, rb, "B"], [mv0[0], mv0[1]], [tg[0], tg[1]]],
      start: Math.round(best * 100),
      fx: function (v) { return num(v, v % 1 ? 1 : 0) + "%"; },
      fy: function (v) { return num(v, v % 1 ? 1 : 0) + "%"; },
      read: function (i) {
        return num(ws[i], 0) + "% in A, " + num(100 - ws[i], 0) + "% in B: volatility " + num(vx[i], 2) +
          "%, expected return " + num(ry[i], 2) + "%, Sharpe ratio " + num((ry[i] - rf) / vx[i], 2) + ".";
      },
    });
  }

  /* Discounted cash flow ----------------------------------------------------- */

  function dcf() {
    var fcf = val("d-fcf"), g1 = val("d-g1"), g2 = val("d-g2"), gt = val("d-gt"), r = val("d-r"), debt = val("d-debt"), sh = val("d-sh");
    if (invalid()) return;
    if (gt >= r) {
      document.getElementById("d-gt").setAttribute("aria-invalid", "true");
      status.textContent = "Growth after year 10 must be below the discount rate, or the value is infinite.";
      return;
    }
    var xs = [], flows = [], pvs = [], c = fcf, pv = 0;
    for (var t = 1; t <= 10; t++) {
      c *= 1 + (t <= 5 ? g1 : g2) / 100;
      var d = c / Math.pow(1 + r / 100, t);
      xs.push(t); flows.push(c); pvs.push(d); pv += d;
    }
    var tv = c * (1 + gt / 100) / ((r - gt) / 100), tvpv = tv / Math.pow(1 + r / 100, 10);
    var ev = pv + tvpv, eq = ev - debt;
    kpis([
      ["Enterprise value", num(ev, 0), "Millions, flows and terminal value today"],
      ["Equity value", num(eq, 0), "Enterprise value less net debt"],
      ["Value per share", eq > 0 ? num(eq / sh, 2) : "n/a", eq > 0 ? "Equity value over " + num(sh, 1) + "m shares" : "Net debt exceeds the enterprise value"],
      ["Years 1 to 10", num(pv, 0), num(pv / ev * 100, 0) + "% of the enterprise value"],
      ["After year 10", num(tvpv, 0), num(tvpv / ev * 100, 0) + "% of the enterprise value"],
      ["Implied multiple", num(ev / fcf, 1) + "x", "Enterprise value over last year's free cash flow"],
    ]);
    draw({
      xs: xs,
      series: [{ values: flows, cls: "line" }, { values: pvs, cls: "dash", area: true }],
      floor0: true,
      fx: function (v) { return "Year " + num(v, 0); },
      fy: function (v) { return num(v, v % 1 ? 1 : 0); },
      read: function (i) {
        return "Year " + xs[i] + ": free cash flow " + num(flows[i], 1) + ", worth " + num(pvs[i], 1) + " today.";
      },
    });
  }

  /* Position size and value at risk ---------------------------------------- */

  function sizing() {
    var acct = val("v-acct"), risk = val("v-risk"), entry = val("v-entry"), stop = val("v-stop"), vol = val("v-vol"), days = val("v-days");
    var conf = parseInt(pressed("conf"), 10);
    if (invalid()) return;
    days = Math.round(days); // whole trading days: the chart reads one point per day
    if (stop >= entry) {
      document.getElementById("v-stop").setAttribute("aria-invalid", "true");
      status.textContent = "The stop must be below the entry price (a long position).";
      return;
    }
    var atRisk = acct * risk / 100, shares = Math.floor(atRisk / (entry - stop));
    var value = shares * entry, z = conf === 99 ? 2.326348 : 1.644854;
    var es = npdf(z) / (1 - conf / 100);
    var sd = function (d) { return vol / 100 * Math.sqrt(d / 252); };
    var vr = value * z * sd(days), sf = value * es * sd(days), stopLoss = shares * (entry - stop);
    kpis([
      ["Shares", num(shares, 0), "Money at risk over the distance to the stop"],
      ["Position value", num(value, 0), num(value / acct * 100, 1) + "% of the account"],
      ["Loss at the stop", num(stopLoss, 0), num(stopLoss / acct * 100, 2) + "% of the account"],
      ["Value at risk, " + conf + "%", num(vr, 0), "Over " + num(days, 0) + " trading day" + (days === 1 ? "" : "s")],
      ["Expected shortfall", num(sf, 0), "Average loss on the worst " + (100 - conf) + "% of days"],
      ["Daily move, one standard deviation", num(sd(1) * 100, 2) + "%", num(sd(1) * entry, 2) + " a share"],
    ]);
    if (!shares) status.textContent = "The money at risk does not cover one share at this stop.";
    var xs = [], vs = [], ss = [], top = Math.max(20, days * 2);
    for (var d = 1; d <= top; d++) {
      xs.push(d); vs.push(value * z * sd(d)); ss.push(value * es * sd(d));
    }
    draw({
      xs: xs,
      series: [{ values: vs, cls: "line" }, { values: ss, cls: "dash" }],
      ref: stopLoss,
      floor0: true,
      start: days - 1,
      fx: function (v) { return num(v, 0) + "d"; },
      fy: function (v) { return v >= 1e6 ? num(v / 1e6, 1) + "m" : v >= 1e3 ? num(v / 1e3, v % 1e3 ? 1 : 0) + "k" : num(v, 0); },
      read: function (i) {
        return "Held " + xs[i] + " day" + (xs[i] === 1 ? "" : "s") + ": value at risk " + num(vs[i], 0) + ", expected shortfall " +
          num(ss[i], 0) + "; the stop caps the planned loss at " + num(stopLoss, 0) + ".";
      },
    });
  }

  /* Real return after inflation -------------------------------------------- */

  function real() {
    var p0 = val("r-start"), nom = val("r-nom"), inf = val("r-inf"), tax = val("r-tax"), years = val("r-yrs");
    if (invalid()) return;
    years = Math.round(years);
    var net = nom * (nom > 0 ? 1 - tax / 100 : 1);
    var realRate = ((1 + net / 100) / (1 + inf / 100) - 1) * 100;
    var xs = [0], nv = [p0], rv = [p0];
    for (var t = 1; t <= years; t++) {
      xs.push(t);
      nv.push(p0 * Math.pow(1 + net / 100, t));
      rv.push(nv[t] / Math.pow(1 + inf / 100, t));
    }
    var end = nv[years], endReal = rv[years];
    kpis([
      ["Real return", mv(signed(realRate, 2, "%")), "A year, after " + (tax ? "tax and " : "") + "inflation"],
      ["Simple difference", mv(signed(net - inf, 2, "%")), "Return less inflation, which overstates it"],
      ["Value, money of the day", num(end, 0), "After " + years + " year" + (years === 1 ? "" : "s")],
      ["Value, today's money", num(endReal, 0), "What it can buy at today's prices"],
      ["Purchasing power lost", num(end - endReal, 0), end > 0 ? num((1 - endReal / end) * 100, 0) + "% of the end value" : ""],
      ["Prices after " + years + " years", "×" + num(Math.pow(1 + inf / 100, years), 2), "At " + num(inf, 1) + "% a year"],
    ]);
    draw({
      xs: xs,
      series: [{ values: nv, cls: "line" }, { values: rv, cls: "dash" }],
      floor0: true,
      fx: function (v) { return "Year " + num(v, 0); },
      fy: function (v) { return v >= 1e6 ? num(v / 1e6, v % 1e6 ? 1 : 0) + "m" : v >= 1e3 ? num(v / 1e3, v % 1e3 ? 1 : 0) + "k" : num(v, 0); },
      read: function (i) {
        return "Year " + xs[i] + ": " + num(nv[i], 0) + " in money of the day, " + num(rv[i], 0) + " in today's money.";
      },
    });
  }

  /* Risk and correlation ----------------------------------------------------- */

  var R = null; // {companies, files, asof, picked: [symbols], weights: {sym: %}, data: {market: {start, series}}}

  function riskSetup() {
    var src = document.getElementById("lt-data");
    if (!src) return;
    R = JSON.parse(src.textContent);
    R.data = {};
    R.loading = {};
    R.parsed = {};
    R.by = {};
    R.companies.forEach(function (c) { R.by[c.s] = c; });
    R.picked = R.companies.filter(function (c) { return c.m === "us"; }).slice(0, 4).map(function (c) { return c.s; });
    R.defaults = R.picked.slice();
    R.weights = {};
    var find = document.getElementById("r-find"), opts = document.getElementById("r-opts");
    var active = -1, matches = [];
    function close() {
      opts.hidden = true;
      find.setAttribute("aria-expanded", "false");
      find.removeAttribute("aria-activedescendant");
      active = -1;
    }
    function render() {
      var q = find.value.trim().toLowerCase();
      if (!q) { close(); return; }
      matches = R.companies.filter(function (c) {
        return R.picked.indexOf(c.s) < 0 && (c.n.toLowerCase().indexOf(q) >= 0 || c.s.toLowerCase().indexOf(q) === 0);
      }).slice(0, 8);
      opts.innerHTML = matches.length ? matches.map(function (c, i) {
        return '<li role="option" id="r-opt-' + i + '" aria-selected="' + (i === active) + '" data-s="' + c.s + '">' +
          '<span class="lt-opts__name">' + esc(c.n) + '</span><span class="lt-opts__meta">' + esc(c.s) + ", " + esc(c.c) + "</span></li>";
      }).join("") : '<li class="lt-opts__none">No company in the calendar matches.</li>';
      opts.hidden = false;
      find.setAttribute("aria-expanded", "true");
      if (active >= 0) find.setAttribute("aria-activedescendant", "r-opt-" + active);
    }
    function add(sym) {
      if (R.picked.length >= 10) {
        status.textContent = "Up to ten companies. Remove one to add another.";
        return;
      }
      R.picked.push(sym);
      find.value = "";
      close();
      risk();
      share();
    }
    find.addEventListener("input", function () { active = -1; render(); });
    find.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        if (!matches.length) return;
        e.preventDefault();
        active = (active + (e.key === "ArrowDown" ? 1 : -1) + matches.length) % matches.length;
        render();
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (matches.length && !opts.hidden) add(matches[Math.max(active, 0)].s);
      } else if (e.key === "Escape") {
        close();
      }
    });
    find.addEventListener("blur", function () { setTimeout(close, 150); });
    opts.addEventListener("mousedown", function (e) {
      var li = e.target.closest("[data-s]");
      if (li) { e.preventDefault(); add(li.getAttribute("data-s")); }
    });
    page.querySelector(".lt-picked").addEventListener("click", function (e) {
      var b = e.target.closest("[data-remove]");
      if (!b) return;
      var sym = b.getAttribute("data-remove");
      R.picked = R.picked.filter(function (x) { return x !== sym; });
      delete R.weights[sym];
      risk();
      share();
      find.focus();
    });
    page.querySelector(".lt-picked").addEventListener("input", function (e) {
      var inp = e.target.closest("[data-weight]");
      if (!inp) return;
      R.weights[inp.getAttribute("data-weight")] = parseFloat(inp.value);
      riskCalc();
      share();
    });
  }
  function esc(t) {
    return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function load(market, done) {
    if (R.data[market]) { done(); return; }
    if (R.loading[market]) { R.loading[market].push(done); return; }
    R.loading[market] = [done];
    var sc = document.createElement("script");
    sc.src = (document.body.getAttribute("data-base") || "") + "assets/" + R.files[market];
    sc.onload = function () {
      R.data[market] = (window.ANDRA_RISK || {})[market];
      var q = R.loading[market];
      R.loading[market] = null;
      q.forEach(function (f) { f(); });
    };
    sc.onerror = function () {
      R.loading[market] = null;
      status.textContent = "The returns for " + market + " did not load. Check your connection and try again.";
    };
    document.head.appendChild(sc);
  }
  // Cumulative log price (basis points) on the weekday axis; NaN where the market was shut.
  // The series' first close carries no return, so its first session reads as shut.
  function cum(market, sym) {
    var k = market + ":" + sym;
    if (!R.parsed[k]) {
      var raw = R.data[market].series[sym].split(","), out = [], acc = 0;
      for (var i = 0; i < raw.length; i++) {
        if (raw[i] === "") out.push(NaN);
        else out.push(acc += +raw[i]);
      }
      R.parsed[k] = out;
    }
    return R.parsed[k];
  }
  function axisDate(start, i) {
    var d = parse(start), wk = Math.floor(i / 5), r = i % 5;
    d.setUTCDate(d.getUTCDate() + wk * 7 + r);
    return d.toISOString().slice(0, 10);
  }
  function parse(iso) {
    var p = iso.split("-");
    return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2]));
  }
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  function dayLabel(iso) {
    var d = parse(iso);
    return d.getUTCDate() + " " + MONTHS[d.getUTCMonth()] + " " + d.getUTCFullYear();
  }
  function monthsBack(iso, n) {
    var d = parse(iso), t = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() - n, 1));
    var last = new Date(Date.UTC(t.getUTCFullYear(), t.getUTCMonth() + 1, 0)).getUTCDate();
    t.setUTCDate(Math.min(d.getUTCDate(), last));
    return t.toISOString().slice(0, 10);
  }
  // Returns between consecutive days on which every series printed, from index i0.
  function joint(series, i0) {
    var n = Infinity;
    series.forEach(function (s) { n = Math.min(n, s.length); });
    var prev = -1, out = series.map(function () { return []; }), days = 0;
    for (var i = i0; i < n; i++) {
      var ok = true;
      for (var j = 0; j < series.length; j++) if (isNaN(series[j][i])) { ok = false; break; }
      if (!ok) continue;
      if (prev >= 0) {
        for (var k = 0; k < series.length; k++) out[k].push((series[k][i] - series[k][prev]) / 1e4);
        days++;
      }
      prev = i;
    }
    return { rets: out, n: days, last: prev };
  }
  function mean(a) { var t = 0; a.forEach(function (x) { t += x; }); return t / a.length; }
  function cov(a, b) {
    var ma = mean(a), mb = mean(b), t = 0;
    for (var i = 0; i < a.length; i++) t += (a[i] - ma) * (b[i] - mb);
    return t / (a.length - 1);
  }

  function risk() {
    if (!R) riskSetup();
    var markets = {};
    R.picked.forEach(function (s) { markets[R.by[s].m] = 1; });
    var need = Object.keys(markets).filter(function (m) { return !R.data[m]; });
    renderPicked();
    if (need.length) {
      readout.textContent = "Loading the daily returns.";
      var left = need.length;
      need.forEach(function (m) { load(m, function () { if (--left === 0) riskCalc(); }); });
      return;
    }
    riskCalc();
  }
  function renderPicked() {
    var custom = pressed("weights") === "custom";
    var eq = R.picked.length ? 100 / R.picked.length : 0;
    page.querySelector(".lt-picked").innerHTML = R.picked.map(function (s) {
      var c = R.by[s], w = R.weights[s] != null && isFinite(R.weights[s]) ? R.weights[s] : Math.round(eq * 10) / 10;
      return '<li><span class="lt-picked__name">' + esc(c.n) + ' <span class="lt-unit">' + esc(s) + "</span></span>" +
        (custom ? '<label class="lt-picked__w"><span class="visually-hidden">Weight of ' + esc(c.n) + ' in %</span><input type="number" inputmode="decimal" min="0" max="100" step="1" value="' + w + '" data-weight="' + esc(s) + '"><span aria-hidden="true">%</span></label>' : "") +
        '<button type="button" class="lt-picked__x" data-remove="' + esc(s) + '" aria-label="Remove ' + esc(c.n) + '">' +
        '<svg class="icon" aria-hidden="true"><use href="#i-x"></use></svg></button></li>';
    }).join("");
  }
  function riskCalc() {
    var table = page.querySelector(".lt-risk tbody");
    status.textContent = "";
    if (R.picked.length < 2) {
      plot.innerHTML = "";
      plot.style.height = "";
      hover = null;
      table.innerHTML = "";
      result.innerHTML = "";
      readout.textContent = "Pick at least two companies.";
      return;
    }
    var span = { "3M": 3, "6M": 6, "1Y": 12, "3Y": 36 }[pressed("win")];
    var cs = R.picked.map(function (s) { return R.by[s]; });
    var start = R.data[cs[0].m].start;
    var series = cs.map(function (c) { return cum(c.m, c.s); });
    // The window ends on the last day every company printed.
    var all = joint(series, 0);
    var endIso = axisDate(start, all.last), from = monthsBack(endIso, span);
    var i0 = 0;
    while (axisDate(start, i0) < from) i0++;
    var J = joint(series, i0);
    if (J.n < 20) {
      readout.textContent = "Too few sessions in common over this window.";
      return;
    }
    var n = cs.length, C = [], M = [];
    for (var i = 0; i < n; i++) {
      C.push([]);
      for (var j = 0; j < n; j++) C[i].push(cov(J.rets[i], J.rets[j]));
    }
    for (i = 0; i < n; i++) {
      M.push([]);
      for (j = 0; j < n; j++) M[i].push(C[i][j] / Math.sqrt(C[i][i] * C[j][j]));
    }
    // Each company on its own sessions: volatility, and beta on the sessions it shares with its benchmark.
    var stats = cs.map(function (c, k) {
      var own = joint([series[k]], i0), vol = Math.sqrt(cov(own.rets[0], own.rets[0]) * 252) * 100;
      var pair = joint([series[k], cum(c.m, c.b)], i0);
      var beta = cov(pair.rets[0], pair.rets[1]) / cov(pair.rets[1], pair.rets[1]);
      return { vol: vol, beta: beta };
    });
    var custom = pressed("weights") === "custom", w = [], tot = 0;
    cs.forEach(function (c) {
      var x = custom ? R.weights[c.s] : 1;
      if (x == null || !isFinite(x)) x = 100 / n;
      x = Math.max(0, x);
      w.push(x); tot += x;
    });
    if (!tot) {
      status.textContent = "Give at least one company a weight above zero.";
      return;
    }
    if (custom && Math.abs(tot - 100) > 0.05) status.textContent = "Weights add to " + num(tot, 1) + "%: scaled to 100%.";
    w = w.map(function (x) { return x / tot; });
    var pv = 0, avgVol = 0;
    for (i = 0; i < n; i++) {
      avgVol += w[i] * Math.sqrt(C[i][i] * 252) * 100;
      for (j = 0; j < n; j++) pv += w[i] * w[j] * C[i][j];
    }
    pv = Math.sqrt(pv * 252) * 100;
    var pairs = [];
    for (i = 0; i < n; i++) for (j = i + 1; j < n; j++) pairs.push([M[i][j], i, j]);
    pairs.sort(function (a, b) { return b[0] - a[0]; });
    var avgR = mean(pairs.map(function (p) { return p[0]; }));
    var fromIso = axisDate(start, i0);
    kpis([
      ["Portfolio volatility", num(pv, 1) + "%", "A year, " + (custom ? "your" : "equal") + " weights"],
      ["Weighted average volatility", num(avgVol, 1) + "%", "On the same sessions, before diversification"],
      ["Diversification benefit", num(avgVol - pv, 1) + " points", "Volatility removed by combining them"],
      ["Average correlation", num(avgR, 2), pairs.length + " pair" + (pairs.length === 1 ? "" : "s")],
      ["Most alike", esc(cs[pairs[0][1]].s) + " and " + esc(cs[pairs[0][2]].s), num(pairs[0][0], 2)],
      ["Least alike", esc(cs[pairs[pairs.length - 1][1]].s) + " and " + esc(cs[pairs[pairs.length - 1][2]].s), num(pairs[pairs.length - 1][0], 2)],
      ["Sessions in common", num(J.n, 0), dayLabel(fromIso) + " to " + dayLabel(endIso)],
    ]);
    table.innerHTML = cs.map(function (c, k) {
      return '<tr><td class="co-tab__name">' + esc(c.n) + "<span>" + esc(c.s) + "</span></td><td class=\"co-tab__sec\">" + esc(c.bn) +
        '</td><td class="num" data-label="Volatility">' + num(stats[k].vol, 1) + '%</td><td class="num" data-label="Beta">' + num(stats[k].beta, 2) +
        '</td><td class="num" data-label="Weight">' + num(w[k] * 100, 1) + "%</td></tr>";
    }).join("");
    matrixChart(cs, M, J.n, fromIso, endIso);
  }
  function matrixChart(cs, M, sessions, fromIso, endIso) {
    var w = plot.clientWidth, n = cs.length;
    if (!w) return;
    var labW = Math.min(150, w * 0.34), top = 22;
    var c = Math.min((w - labW) / n, 72), h = top + c * n;
    var svg = el("svg", { "class": "chart", width: w, height: h, viewBox: "0 0 " + w + " " + h, "aria-hidden": "true" });
    var cells = [];
    cs.forEach(function (co, j) {
      svg.appendChild(el("text", { "class": "chart__label", x: labW + c * (j + 0.5), y: 14, "text-anchor": "middle" }, c < 46 ? co.s.split(".")[0].slice(0, 4) : co.s.split(".")[0].slice(0, 6)));
    });
    var maxChars = Math.floor(labW / 7);
    cs.forEach(function (co, i) {
      var nm = co.n.length > maxChars ? co.n.slice(0, maxChars - 1) + "…" : co.n;
      svg.appendChild(el("text", { "class": "chart__label", x: 0, y: top + c * (i + 0.5) + 4 }, nm));
      for (var j = 0; j < n; j++) {
        var v = M[i][j];
        svg.appendChild(el("rect", { "class": v >= 0 ? "up" : "down", x: labW + c * j + 1, y: top + c * i + 1, width: c - 2, height: c - 2, opacity: (0.12 + 0.45 * Math.abs(v)).toFixed(2) }));
        if (c >= 34) svg.appendChild(el("text", { "class": "chart__value", x: labW + c * (j + 0.5), y: top + c * (i + 0.5) + 4, "text-anchor": "middle" }, signed(v, 2).replace(/^\+/, "")));
        if (i !== j) cells.push([i, j]);
      }
    });
    var ring = el("rect", { "class": "cell-ring", width: c, height: c, x: -100, y: -100 });
    svg.appendChild(ring);
    plot.replaceChildren(svg);
    plot.style.height = h + "px";
    plot.setAttribute("aria-label", "Correlation of daily returns over " + sessions + " sessions from " + dayLabel(fromIso) + " to " +
      dayLabel(endIso) + ": " + cells.filter(function (p) { return p[0] < p[1]; }).map(function (p) {
        return cs[p[0]].n + " and " + cs[p[1]].n + " " + signed(M[p[0]][p[1]], 2);
      }).join(", ") + ". Use the arrow keys to read each pair.");
    hover = {
      count: cells.length,
      show: function (k) {
        index = k;
        var p = cells[k];
        ring.setAttribute("x", labW + c * p[1]);
        ring.setAttribute("y", top + c * p[0]);
        readout.textContent = cs[p[0]].n + " and " + cs[p[1]].n + ": correlation " + signed(M[p[0]][p[1]], 2).replace(/^\+/, "") +
          " over " + sessions + " sessions, " + dayLabel(fromIso) + " to " + dayLabel(endIso) + ".";
      },
      at: function (px, py) {
        var i = Math.floor((py - top) / c), j = Math.floor((px - labW) / c);
        if (i < 0 || j < 0 || i >= n || j >= n || i === j) return index;
        for (var k = 0; k < cells.length; k++) if (cells[k][0] === i && cells[k][1] === j) return k;
        return index;
      },
    };
    hover.show(index >= 0 && index < cells.length ? index : 0);
  }

  /* Shareable link ------------------------------------------------------------ */

  // The inputs that differ from the page's defaults live in the URL fragment
  // (#yld=5&freq=1), which the browser never sends to the server: a link
  // carries a setup and the page still sends and stores nothing. A number
  // input's key is its id without the tool's prefix, a chip group's is the
  // group; the risk tool adds its companies in order (co) and, with custom
  // weights, each one's weight in the same order (w). Read back, a value out of
  // range, unknown or malformed is ignored and the default stays.
  var NUMBER = /^-?(\d+\.?\d*|\.\d+)(e[+-]?\d+)?$/i;
  var saving = null;
  function keyOf(id) { return id.slice(id.indexOf("-") + 1); }
  // The number written in s if it is one within [lo, hi], else null.
  function within(s, lo, hi) {
    var v = NUMBER.test(s) ? parseFloat(s) : NaN;
    return isFinite(v) && !(v < lo) && !(v > hi) ? v : null;
  }
  function save() {
    var pairs = [];
    page.querySelectorAll(".lt-chips").forEach(function (g) {
      var on = g.querySelector('.chip[aria-pressed="true"]');
      if (on && !on.hasAttribute("data-default")) pairs.push([g.getAttribute("data-group"), on.getAttribute("data-value")]);
    });
    page.querySelectorAll(".lt-field input").forEach(function (input) {
      var v = within(input.value, parseFloat(input.min), parseFloat(input.max));
      if (v != null && v !== parseFloat(input.defaultValue)) pairs.push([keyOf(input.id), String(v)]);
    });
    if (R) {
      if (R.picked.join(",") !== R.defaults.join(",")) pairs.push(["co", R.picked.join(",")]);
      var w = pressed("weights") !== "custom" ? "" : R.picked.map(function (s) {
        var x = R.weights[s];
        return isFinite(x) && x >= 0 && x <= 100 ? String(x) : "";
      }).join(",").replace(/,+$/, "");
      if (w) pairs.push(["w", w]);
    }
    var frag = pairs.map(function (p) {
      return encodeURIComponent(p[0]) + "=" + encodeURIComponent(p[1]).replace(/%2C/g, ",");
    }).join("&");
    if ((frag ? "#" + frag : "") === location.hash) return;
    try {
      history.replaceState(null, "", location.pathname + location.search + (frag ? "#" + frag : ""));
    } catch (e) {
      // a browser that rate-limits history updates refuses this one; the next change writes the fragment
    }
  }
  // After each change, held briefly so a burst of keystrokes makes one history update.
  function share() {
    clearTimeout(saving);
    saving = setTimeout(save, 150);
  }
  function restore() {
    var got = Object.create(null);
    location.hash.slice(1).split("&").forEach(function (pair) {
      var i = pair.indexOf("=");
      if (i < 1) return;
      try {
        got[decodeURIComponent(pair.slice(0, i))] = decodeURIComponent(pair.slice(i + 1));
      } catch (e) {
        // a malformed escape: ignored
      }
    });
    page.querySelectorAll(".lt-chips").forEach(function (g) {
      var want = got[g.getAttribute("data-group")], chips = g.querySelectorAll(".chip");
      var hit = Array.prototype.filter.call(chips, function (c) { return c.getAttribute("data-value") === want; })[0];
      if (!hit) return;
      chips.forEach(function (c) { c.setAttribute("aria-pressed", c === hit ? "true" : "false"); });
    });
    page.querySelectorAll(".lt-field input").forEach(function (input) {
      var k = keyOf(input.id), v = k in got ? within(got[k], parseFloat(input.min), parseFloat(input.max)) : null;
      if (v != null) input.value = String(v);
    });
    if (tool !== "risk") return;
    if (!R) riskSetup();
    if (!R) return;
    // A company not in the tool's list (it holds only those with returns) is dropped, as are repeats and any past the tenth.
    var syms = "co" in got ? got.co.split(",") : R.defaults, ws = "w" in got ? got.w.split(",") : [];
    var picked = [], weights = {};
    syms.forEach(function (s, i) {
      if (!Object.prototype.hasOwnProperty.call(R.by, s) || picked.indexOf(s) >= 0 || picked.length >= 10) return;
      picked.push(s);
      var x = i < ws.length ? within(ws[i], 0, 100) : null;
      if (x != null) weights[s] = x;
    });
    // An empty pick ("co=") is kept as it was shared; a list of only unknown companies is ignored.
    if (picked.length || !got.co) {
      R.picked = picked;
      R.weights = weights;
    }
  }

  var run = { bond: bond, options: options, growth: growth, bs: pricer, ytm: ytm, frontier: frontier, dcf: dcf,
    "var": sizing, real: real, risk: risk }[tool];
  page.querySelectorAll(".lt-chips .chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      chip.parentNode.querySelectorAll(".chip").forEach(function (c) {
        c.setAttribute("aria-pressed", c === chip ? "true" : "false");
      });
      run();
      share();
    });
  });
  page.querySelectorAll(".lt-field input").forEach(function (input) {
    input.addEventListener("input", function () {
      run();
      share();
    });
  });
  // Every input back to its default: the reset button, and a fragment opened in this tab.
  function clear() {
    page.querySelectorAll(".lt-field input").forEach(function (input) {
      input.value = input.defaultValue;
    });
    page.querySelectorAll(".lt-chips").forEach(function (g) {
      g.querySelectorAll(".chip").forEach(function (c) {
        c.setAttribute("aria-pressed", c.hasAttribute("data-default") ? "true" : "false");
      });
    });
    if (R) {
      R.picked = R.defaults.slice();
      R.weights = {};
    }
  }
  // The risk tool redraws only its chart on resize; its inputs live outside .lt-field.
  var reset = page.querySelector(".lt-reset");
  if (reset) {
    reset.addEventListener("click", function () {
      clear();
      run();
      share();
    });
  }
  // A link to another setup opened in this tab changes only the fragment, and the
  // page does not reload. A fragment with no value in it is an in-page link (the
  // skip link's #main) and leaves the inputs as they are.
  window.addEventListener("hashchange", function () {
    if (location.hash.length > 1 && location.hash.indexOf("=") < 0) return;
    clearTimeout(saving);
    clear();
    restore();
    run();
  });
  page.querySelector(".lt-tool").hidden = false;
  restore();
  run();
  var last = plot.clientWidth;
  window.addEventListener("resize", function () {
    if (plot.clientWidth !== last) {
      last = plot.clientWidth;
      run();
    }
  });
})();
