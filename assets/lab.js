/* Andra Markets Lab tools: bond price and duration, options payoff, compound
   growth. Everything is calculated in the browser from the inputs on the page:
   no request is made and nothing is sent or stored. Charts are drawn at the
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
    return v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec }).replace("-", MINUS);
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
    var raw = (hi - lo) / n, p = Math.pow(10, Math.floor(Math.log(raw) / Math.LN10)), step = p;
    [1, 2, 2.5, 5, 10].some(function (m) { step = m * p; return m * p >= raw; });
    var out = [];
    for (var v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(Math.abs(v) < 1e-9 ? 0 : v);
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
    var pad = (hi - lo) * 0.08 || 1;
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
    hover.show(hover.at(e.clientX - r.left));
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

  var run = { bond: bond, options: options, growth: growth }[tool];
  page.querySelectorAll(".lt-chips .chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      chip.parentNode.querySelectorAll(".chip").forEach(function (c) {
        c.setAttribute("aria-pressed", c === chip ? "true" : "false");
      });
      run();
    });
  });
  page.querySelectorAll(".lt-field input").forEach(function (input) {
    input.addEventListener("input", run);
  });
  var reset = page.querySelector(".lt-reset");
  if (reset) {
    reset.addEventListener("click", function () {
      page.querySelectorAll(".lt-field input").forEach(function (input) {
        input.value = input.defaultValue;
      });
      page.querySelectorAll(".lt-chips").forEach(function (g) {
        g.querySelectorAll(".chip").forEach(function (c) {
          c.setAttribute("aria-pressed", c.hasAttribute("data-default") ? "true" : "false");
        });
      });
      run();
    });
  }
  page.querySelector(".lt-tool").hidden = false;
  run();
  var last = plot.clientWidth;
  window.addEventListener("resize", function () {
    if (plot.clientWidth !== last) {
      last = plot.clientWidth;
      run();
    }
  });
})();
