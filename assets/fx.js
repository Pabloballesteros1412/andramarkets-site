/* Andra Markets FX page charts: the dollar index, one pair or several rebased
   to 100, a heatmap of each pair's moves, and each currency's move against
   its rate differential with the US. Drawn from the figures embedded in the
   page at each chart's own pixel width, with a readout that follows the
   pointer or the arrow keys, in the dashboards' chart style. Red and green
   only for rises and falls (DESIGN.md, The Rise and Fall Rule). */
(function () {
  "use strict";
  var root = document.querySelector("[data-fxcharts]");
  var src = document.getElementById("fx-data");
  if (!root || !src) return;
  var D = JSON.parse(src.textContent);
  var NS = "http://www.w3.org/2000/svg";
  var MINUS = "−";
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var SPAN = { "1M": 1, "3M": 3, "6M": 6, "1Y": 12 };
  var MAX_LINES = 6;
  var byKey = {};
  D.pairs.forEach(function (p) { byKey[p.key] = p; });
  var roll = window.AndraRoll;
  // Every readout here prints signed moves: they take green or red from their sign.
  root.querySelectorAll(".dd__read").forEach(function (r) { r.setAttribute("data-moves", ""); });

  function el(name, attrs, text) {
    var e = document.createElementNS(NS, name);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  }
  function num(v, dec) {
    var s = v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec });
    // a value that rounds to zero carries no sign ("0.00", never "−0.00")
    if (/^-[0.,]+$/.test(s)) s = s.slice(1);
    return s.replace("-", MINUS);
  }
  function signed(v, dec, unit) {
    var r = Number(v.toFixed(dec));
    return (r > 0 ? "+" : r < 0 ? MINUS : "") + num(Math.abs(r), dec) + (unit || "");
  }
  function moveClass(t) {
    return t.charAt(0) === "+" ? " mv--up" : t.charAt(0) === MINUS ? " mv--down" : "";
  }
  function parse(iso) {
    var p = iso.split("-");
    return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2]));
  }
  function day(iso) {
    var d = parse(iso);
    return d.getUTCDate() + " " + MONTHS[d.getUTCMonth()] + " " + d.getUTCFullYear();
  }
  function monthsBack(iso, n) {
    var d = parse(iso), t = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() - n, 1));
    var last = new Date(Date.UTC(t.getUTCFullYear(), t.getUTCMonth() + 1, 0)).getUTCDate();
    t.setUTCDate(Math.min(d.getUTCDate(), last));
    return t.toISOString().slice(0, 10);
  }
  function svgFor(w, h) {
    return el("svg", { "class": "chart", width: w, height: h, viewBox: "0 0 " + w + " " + h, "aria-hidden": "true" });
  }
  // Round tick values: steps of 1, 2, 2.5 or 5 times a power of ten.
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
  function decOf(step) {
    return step >= 1 ? 0 : Math.min(4, Math.ceil(-Math.log(step) / Math.LN10));
  }
  function keyItems(key, items) {
    key.replaceChildren();
    items.forEach(function (it) {
      var s = document.createElement("span");
      if (/^s\d$/.test(it[0])) {
        var sv = el("svg", { width: 16, height: 6, viewBox: "0 0 16 6", "class": "chart key__line", "aria-hidden": "true" });
        sv.appendChild(el("line", { "class": it[0], x1: 0, x2: 16, y1: 3, y2: 3 }));
        s.appendChild(sv);
      } else {
        var i = document.createElement("i");
        i.className = it[0];
        s.appendChild(i);
      }
      s.appendChild(document.createTextNode(it[1]));
      key.appendChild(s);
    });
  }
  // The currency's own move against the dollar, from a move in the pair as quoted.
  function ccyMove(p, m) {
    if (m == null) return null;
    return p.inv ? (1 / (1 + m / 100) - 1) * 100 : m;
  }

  /* One chart block: its plot, key, readout and pointer and key handling. */
  function Chart(box, drawFn) {
    var plot = box.querySelector(".dd__plot"), out = box.querySelector(".dd__read");
    var self = { box: box, plot: plot, key: box.querySelector(".dd__key"), hover: null, index: -1 };
    var r = roll ? new roll(out) : null;
    self.say = function (t) { if (r) r.set(t); else out.textContent = t; };
    self.draw = function () {
      var w = plot.clientWidth;
      if (!w) return;
      var c = drawFn(w, self);
      if (!c) return;
      plot.replaceChildren(c.svg);
      plot.style.height = c.h ? c.h + "px" : "";
      plot.setAttribute("aria-label", c.label);
      self.hover = c;
      c.svg.addEventListener("pointermove", function (e) {
        var b = c.svg.getBoundingClientRect(), k = c.pick(e.clientX - b.left, e.clientY - b.top);
        if (k >= 0) self.show(k);
      });
      self.show(self.index >= 0 && self.index < c.count ? self.index : c.start != null ? c.start : c.count - 1);
    };
    self.show = function (k) {
      self.index = k;
      self.say(self.hover.show(k));
    };
    plot.addEventListener("keydown", function (e) {
      if (!self.hover) return;
      var step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
      if (e.key === "Home") step = -self.hover.count;
      if (e.key === "End") step = self.hover.count;
      if (!step) return;
      e.preventDefault();
      self.show(Math.max(0, Math.min(self.hover.count - 1, self.index + step)));
    });
    var lastW = 0;
    if ("ResizeObserver" in window) {
      new ResizeObserver(function () {
        if (plot.clientWidth !== lastW) { lastW = plot.clientWidth; self.draw(); }
      }).observe(plot);
    } else window.addEventListener("resize", self.draw);
    return self;
  }
  // Chip groups: one pressed (a choice) or several (toggles).
  function choice(group, onPick) {
    group.addEventListener("click", function (e) {
      var b = e.target.closest(".chip");
      if (!b) return;
      group.querySelectorAll(".chip").forEach(function (c) { c.setAttribute("aria-pressed", String(c === b)); });
      onPick(b.getAttribute("data-v"));
    });
    var on = group.querySelector('.chip[aria-pressed="true"]');
    return on ? on.getAttribute("data-v") : null;
  }

  /* Lines over time: one series as a level, or several rebased to 100. */
  function lines(w, h, o) {
    var dates = D.hist.dates, start = monthsBack(dates[dates.length - 1], SPAN[o.range]);
    var i0 = 0;
    while (i0 < dates.length - 1 && dates[i0] < start) i0++;
    var ds = dates.slice(i0);
    var ls = o.keys.map(function (k, j) {
      var raw = D.hist.series[k].slice(i0), v = [], last = null, base = null;
      raw.forEach(function (x) {
        if (x != null) last = x;
        if (base == null && last != null) base = last;
        v.push(last);
      });
      var p = byKey[k];
      return { p: p, raw: v, base: base, cls: "s" + (j % 6),
               v: v.map(function (x) { return x == null ? null : o.rebase ? x / base * 100 : x; }) };
    });
    var all = [];
    ls.forEach(function (l) { l.v.forEach(function (x) { if (x != null) all.push(x); }); });
    if (o.rebase) all.push(100);
    var lo = Math.min.apply(null, all), hi = Math.max.apply(null, all), pad = (hi - lo) * 0.08 || 1;
    lo -= pad; hi += pad;
    var multi = ls.length > 1, endW = multi && w >= 520 ? 92 : 0;
    var L = 56, R = 8 + endW, T = 8, B = 24;
    var X = function (i) { return L + (w - L - R) * i / Math.max(ds.length - 1, 1); };
    var Y = function (v) { return T + (h - T - B) * (1 - (v - lo) / (hi - lo)); };
    var svg = svgFor(w, h);
    var ticks = nice(lo, hi, 4), dec = o.rebase ? 0 : decOf(ticks.length > 1 ? ticks[1] - ticks[0] : 1);
    ticks.forEach(function (t) {
      svg.appendChild(el("line", { "class": "grid-line", x1: L, x2: w - R, y1: Y(t), y2: Y(t) }));
      svg.appendChild(el("text", { "class": "chart__label", x: L - 8, y: Y(t) + 4, "text-anchor": "end" }, num(t, dec)));
    });
    if (o.rebase) svg.appendChild(el("line", { "class": "ref", x1: L, x2: w - R, y1: Y(100), y2: Y(100) }));
    svg.appendChild(el("text", { "class": "chart__label", x: L, y: h - 6 }, day(ds[0])));
    svg.appendChild(el("text", { "class": "chart__label", x: w - R, y: h - 6, "text-anchor": "end" }, day(ds[ds.length - 1])));
    ls.forEach(function (l) {
      var d = "", pen = false;
      l.v.forEach(function (v, i) {
        if (v == null) { pen = false; return; }
        d += (pen ? " L" : (d ? " M" : "M")) + X(i).toFixed(1) + " " + Y(v).toFixed(1);
        pen = true;
      });
      svg.appendChild(el("path", { "class": l.cls, d: d }));
    });
    if (endW) {
      var tags = ls.map(function (l) { return { l: l, y: Y(l.v[l.v.length - 1]) }; }).sort(function (a, b) { return a.y - b.y; });
      for (var k = 1; k < tags.length; k++) if (tags[k].y - tags[k - 1].y < 14) tags[k].y = tags[k - 1].y + 14;
      tags.forEach(function (t) { svg.appendChild(el("text", { "class": "chart__label chart__end", x: w - R + 8, y: t.y + 4 }, t.l.p.name)); });
    }
    var cross = el("line", { "class": "cross", y1: T, y2: h - B });
    var dots = ls.map(function () { return el("circle", { "class": "dot", r: 3 }); });
    svg.appendChild(cross);
    dots.forEach(function (d) { svg.appendChild(d); });
    var xs = ds.map(function (_, i) { return X(i); });
    function fig(l, i) {
      if (l.v[i] == null) return l.p.name + " n/a";
      if (o.rebase) return l.p.name + " " + num(l.v[i], 1) + " (" + signed(l.v[i] - 100, 2, "%") + ")";
      return l.p.name + " " + num(l.raw[i], l.p.dec) + " (" + signed((l.raw[i] / l.base - 1) * 100, 2, "%") + " since " + day(ds[0]) + ")";
    }
    return {
      svg: svg, count: ds.length,
      label: (o.rebase ? "Rebased to 100 on " + day(ds[0]) + ". " : "") + ls.map(function (l) { return fig(l, ds.length - 1); }).join(", ") +
        " on " + day(ds[ds.length - 1]) + ". Use the arrow keys to read each day.",
      key: ls.map(function (l) { return [l.cls, l.p.name + (o.rebase || l.p.key === "dxy" ? "" : ", " + l.p.quote)]; }).concat(o.rebase ? [["k-ref", "100 on " + day(ds[0])]] : []),
      pick: function (x) {
        var best = 0;
        for (var i = 1; i < xs.length; i++) if (Math.abs(xs[i] - x) < Math.abs(xs[best] - x)) best = i;
        return best;
      },
      show: function (i) {
        cross.setAttribute("x1", xs[i]); cross.setAttribute("x2", xs[i]);
        ls.forEach(function (l, j) {
          dots[j].setAttribute("cx", xs[i]);
          dots[j].setAttribute("cy", l.v[i] == null ? -10 : Y(l.v[i]));
        });
        return day(ds[i]) + ": " + ls.map(function (l) { return fig(l, i); }).join(", ");
      }
    };
  }

  function heightOf(w) { return Math.round(Math.max(240, Math.min(380, w * 0.42))); }
  function bindKey(chart, c) { if (c && chart.key) keyItems(chart.key, c.key); return c; }

  /* 1. The dollar index on its own. */
  var dxyBox = root.querySelector('[data-chart="dxy"]');
  if (dxyBox && D.hist.series.dxy) {
    var dxyRange = "6M";
    var dxy = Chart(dxyBox, function (w, self) {
      return bindKey(self, lines(w, heightOf(w), { keys: ["dxy"], range: dxyRange }));
    });
    dxyRange = choice(dxyBox.querySelector(".dd__ranges"), function (v) { dxyRange = v; dxy.index = -1; dxy.draw(); }) || dxyRange;
    dxy.draw();
  }

  /* 2. One pair, or several rebased to 100. */
  var pairBox = root.querySelector('[data-chart="pairs"]');
  if (pairBox) {
    var st = { view: "one", pair: "eurusd", range: "6M", picked: ["eurusd", "usdjpy", "gbpusd"] };
    var status = pairBox.querySelector(".dd__status");
    var oneG = pairBox.querySelector(".fx-one"), cmpG = pairBox.querySelector(".fx-cmp");
    var pc = Chart(pairBox, function (w, self) {
      var keys = st.view === "one" ? [st.pair] : st.picked.filter(function (k) { return D.hist.series[k]; });
      if (!keys.length) return null;
      return bindKey(self, lines(w, heightOf(w), { keys: keys, range: st.range, rebase: st.view === "cmp" }));
    });
    st.view = choice(pairBox.querySelector(".fx-views"), function (v) {
      st.view = v;
      oneG.hidden = v !== "one";
      cmpG.hidden = v !== "cmp";
      status.textContent = "";
      window.dispatchEvent(new Event("resize")); // the chip glides measure the group now on screen
      pc.index = -1;
      pc.draw();
    }) || st.view;
    st.pair = choice(oneG.querySelector(".filters"), function (v) { st.pair = v; pc.index = -1; pc.draw(); }) || st.pair;
    st.range = choice(pairBox.querySelector(".dd__ranges"), function (v) { st.range = v; pc.index = -1; pc.draw(); }) || st.range;
    cmpG.querySelector(".dd__toggles").addEventListener("click", function (e) {
      var b = e.target.closest(".chip");
      if (!b) return;
      var k = b.getAttribute("data-v"), i = st.picked.indexOf(k);
      status.textContent = "";
      if (i >= 0) {
        if (st.picked.length === 1) { status.textContent = "At least one pair stays on the chart."; return; }
        st.picked.splice(i, 1);
      } else {
        if (st.picked.length >= MAX_LINES) { status.textContent = "Up to six lines at once. Turn one off first."; return; }
        st.picked.push(k);
      }
      b.setAttribute("aria-pressed", String(i < 0));
      pc.index = -1;
      pc.draw();
    });
    pc.draw();
  }

  /* 3. Every pair's moves over a day, a week, a month and the year so far. */
  var COLS = [["d1", "Day"], ["w1", "Week"], ["m1", "Month"], ["ytd", "Year to date"]];
  var heatBox = root.querySelector('[data-chart="heat"]');
  if (heatBox) {
    var mode = "quoted";
    var heat = Chart(heatBox, function (w, self) {
      var rows = D.pairs.filter(function (p) { return D.moves[p.key] && (mode === "quoted" || p.ccy); });
      var labW = Math.min(150, w * 0.34), top = 24, rowH = 30, cw = (w - labW) / COLS.length, h = top + rowH * rows.length;
      var svg = svgFor(w, h);
      var val = function (p, c) {
        var m = D.moves[p.key][c];
        return mode === "quoted" ? m : ccyMove(p, m);
      };
      var maxC = COLS.map(function (c) {
        var m = 0.01;
        rows.forEach(function (p) { var v = val(p, c[0]); if (v != null) m = Math.max(m, Math.abs(v)); });
        return m;
      });
      COLS.forEach(function (c, j) {
        svg.appendChild(el("text", { "class": "chart__label", x: labW + cw * (j + 0.5), y: 15, "text-anchor": "middle" },
                           cw < 90 ? ["1D", "1W", "1M", "YTD"][j] : c[1]));
      });
      var cells = [];
      rows.forEach(function (p, i) {
        var y = top + rowH * i;
        svg.appendChild(el("text", { "class": "chart__label", x: 0, y: y + rowH / 2 + 4 }, mode === "quoted" ? p.name : p.ccy));
        COLS.forEach(function (c, j) {
          var v = val(p, c[0]), x = labW + cw * j;
          if (v != null) {
            // Opacity grows with the move's size within its column, as on the correlation matrix.
            svg.appendChild(el("rect", { "class": v >= 0 ? "up" : "down", x: x + 1, y: y + 1, width: cw - 2, height: rowH - 2,
                                         opacity: (0.12 + 0.45 * Math.abs(v) / maxC[j]).toFixed(2) }));
          }
          svg.appendChild(el("text", { "class": "chart__value", x: x + cw / 2, y: y + rowH / 2 + 4, "text-anchor": "middle" },
                             v == null ? "n/a" : signed(v, 2, "%")));
          cells.push([p, c, v, x, y]);
        });
      });
      var ring = el("rect", { "class": "cell-ring", width: cw, height: rowH, x: -100, y: -100 });
      svg.appendChild(ring);
      return {
        svg: svg, h: h, count: cells.length, start: 0,
        key: [["sw-up", mode === "quoted" ? "Pair rose" : "Currency stronger"], ["sw-down", mode === "quoted" ? "Pair fell" : "Currency weaker"]],
        label: (mode === "quoted" ? "Moves of each pair as quoted" : "Each currency's move against the dollar") +
          " over a day, a week, a month and the year to date. Use the arrow keys to read each cell.",
        pick: function (x, y) {
          var i = Math.floor((y - top) / rowH), j = Math.floor((x - labW) / cw);
          return i < 0 || j < 0 || i >= rows.length || j >= COLS.length ? -1 : i * COLS.length + j;
        },
        show: function (k) {
          var c = cells[k];
          ring.setAttribute("x", c[3]); ring.setAttribute("y", c[4]);
          var who = mode === "quoted" ? c[0].name + " (" + c[0].quote + ")" : c[0].ccy + " against the dollar";
          return who + ", " + c[1][1].toLowerCase() + ": " + (c[2] == null ? "n/a" : signed(c[2], 2, "%"));
        }
      };
    });
    heatBox.querySelector(".fx-mode") && (mode = choice(heatBox.querySelector(".fx-mode"), function (v) {
      mode = v; heat.index = -1; heat.draw();
    }) || mode);
    heat.draw();
  }

  /* 4. Each currency's move against its rate differential with the US. */
  var scBox = root.querySelector('[data-chart="scatter"]');
  if (scBox && D.rates && D.rates.USD) {
    var per = "m1";
    var sc = Chart(scBox, function (w, self) {
      var us = D.rates.USD.rate, pts = [];
      D.pairs.forEach(function (p) {
        if (!p.ccy || !D.rates[p.ccy] || !D.moves[p.key]) return;
        var m = ccyMove(p, D.moves[p.key][per]);
        if (m == null) return;
        pts.push({ p: p, x: D.rates[p.ccy].rate - us, y: m, month: D.rates[p.ccy].month });
      });
      if (!pts.length) return null;
      var h = heightOf(w) + 20, L = 52, R = 16, T = 26, B = 40;
      var xs = pts.map(function (q) { return q.x; }).concat([0]), ys = pts.map(function (q) { return q.y; }).concat([0]);
      var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs), y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
      var px = (x1 - x0) * 0.1 || 1, py = (y1 - y0) * 0.12 || 1;
      x0 -= px; x1 += px; y0 -= py; y1 += py;
      var X = function (v) { return L + (w - L - R) * (v - x0) / (x1 - x0); };
      var Y = function (v) { return T + (h - T - B) * (1 - (v - y0) / (y1 - y0)); };
      var svg = svgFor(w, h);
      var yt = nice(y0, y1, 4), xt = nice(x0, x1, w < 480 ? 4 : 6);
      var yd = decOf(yt.length > 1 ? yt[1] - yt[0] : 1), xd = decOf(xt.length > 1 ? xt[1] - xt[0] : 1);
      yt.forEach(function (t) {
        svg.appendChild(el("line", { "class": "grid-line", x1: L, x2: w - R, y1: Y(t), y2: Y(t) }));
        svg.appendChild(el("text", { "class": "chart__label", x: L - 8, y: Y(t) + 4, "text-anchor": "end" }, signed(t, yd, "%")));
      });
      xt.forEach(function (t) {
        svg.appendChild(el("text", { "class": "chart__label", x: X(t), y: h - B + 16, "text-anchor": "middle" }, signed(t, xd)));
      });
      svg.appendChild(el("line", { "class": "ref", x1: L, x2: w - R, y1: Y(0), y2: Y(0) }));
      svg.appendChild(el("line", { "class": "ref", x1: X(0), x2: X(0), y1: T, y2: h - B }));
      svg.appendChild(el("text", { "class": "chart__label", x: (L + w - R) / 2, y: h - 4, "text-anchor": "middle" },
                         "Rate differential with the US, percentage points"));
      svg.appendChild(el("text", { "class": "chart__label", x: 0, y: 12 }, "Currency against the dollar"));
      pts.forEach(function (q) {
        var t = signed(q.y, 2, "%");
        svg.appendChild(el("circle", { "class": t.charAt(0) === "+" ? "up" : t.charAt(0) === MINUS ? "down" : "dot", cx: X(q.x), cy: Y(q.y), r: 4.5 }));
        svg.appendChild(el("text", { "class": "chart__label", x: X(q.x) + 8, y: Y(q.y) + 4 }, q.p.ccy));
      });
      var ring = el("circle", { "class": "cell-ring", r: 8, cx: -20, cy: -20 });
      svg.appendChild(ring);
      var spanW = { d1: "the day", w1: "the week", m1: "the month", ytd: "the year to date" }[per];
      return {
        svg: svg, count: pts.length, start: 0,
        key: [["sw-up", "Currency stronger against the dollar"], ["sw-down", "Weaker"], ["k-ref", "Zero"]],
        label: "Each currency's move against the dollar over " + spanW + " against its 3-month rate less the US's: " +
          pts.map(function (q) { return q.p.ccy + " " + signed(q.x, 2) + " points, " + signed(q.y, 2, "%"); }).join("; ") +
          ". Use the arrow keys to read each currency.",
        pick: function (x, y) {
          var best = -1, bd = 900;
          pts.forEach(function (q, i) {
            var d = Math.pow(X(q.x) - x, 2) + Math.pow(Y(q.y) - y, 2);
            if (d < bd) { bd = d; best = i; }
          });
          return best;
        },
        show: function (i) {
          var q = pts[i];
          ring.setAttribute("cx", X(q.x)); ring.setAttribute("cy", Y(q.y));
          return q.p.ccy + ": " + signed(q.y, 2, "%") + " against the dollar over " + spanW + "; 3-month rate " +
            num(D.rates[q.p.ccy].rate, 2) + "% against the US's " + num(us, 2) + "%, " +
            // A differential is a level, not a move: worded without a sign so it stays in ink.
            (Math.abs(q.x) < 0.005 ? "level with the US" : num(Math.abs(q.x), 2) + " points " + (q.x > 0 ? "above" : "below") + " the US") +
            " (" + q.month + ")";
        }
      };
    });
    per = choice(scBox.querySelector(".fx-per"), function (v) { per = v; sc.index = -1; sc.draw(); }) || per;
    sc.draw();
  }
  root.hidden = false;
})();
