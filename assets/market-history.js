/* Market history (market-history/): draws the S&P 500 charts at their pixel width,
   so labels stay 12px on a phone, with a crosshair and a readout that follow the
   pointer or the arrow keys (Home and End jump to the ends), as on the dashboard
   pages. Data comes from the page's own <script type="application/json"> block,
   written by tools/page_market_history.py: daily closes, price only.

   Episode charts mark the peak, the low and the day the index was back at the
   peak, shade the fall in --down-tint and draw the peak's level as a dashed
   reference. The overview runs from 1928 on a log scale with every episode's fall
   shaded; the readout names the episode under the pointer, and a click or Enter
   opens it. Nothing animates, so reduced motion needs nothing more. */
(function () {
  "use strict";
  var NS = "http://www.w3.org/2000/svg";
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var MINUS = "−";

  function el(name, attrs, text) {
    var n = document.createElementNS(NS, name);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (text != null) n.textContent = text;
    return n;
  }
  function parse(iso) {
    return Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +(iso.slice(8, 10) || 1));
  }
  function day(t) {
    var d = new Date(t);
    return d.getUTCDate() + " " + MONTHS[d.getUTCMonth()] + " " + d.getUTCFullYear();
  }
  function num(v) {
    return v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  function tick(v) {
    return v >= 100 ? Math.round(v).toLocaleString("en-US") : v >= 10 ? String(Math.round(v)) : String(+v.toFixed(1));
  }
  function signed(v, dec, unit) {
    var r = +v.toFixed(dec);
    if (r === 0) return (0).toFixed(dec) + unit;
    return (r > 0 ? "+" : MINUS) + Math.abs(r).toFixed(dec) + unit;
  }
  function move(text) {
    var c = text.charAt(0) === "+" ? "mv--up" : text.charAt(0) === MINUS ? "mv--down" : "";
    return c ? '<span class="mv ' + c + '">' + text + "</span>" : text;
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  // Round steps for a linear axis: 1, 2 or 5 times a power of ten.
  function niceStep(span, n) {
    var raw = span / n, p = Math.pow(10, Math.floor(Math.log10(raw))), m = raw / p;
    return (m <= 1 ? 1 : m <= 2 ? 2 : m <= 5 ? 5 : 10) * p;
  }
  // Ticks for a log axis: 1, 2 and 5 times powers of ten inside the range, thinned to fit.
  function logTicks(lo, hi, room) {
    var out = [];
    for (var e = Math.floor(Math.log10(lo)); e <= Math.ceil(Math.log10(hi)); e++) {
      [1, 2, 5].forEach(function (m) {
        var v = m * Math.pow(10, e);
        if (v >= lo && v <= hi) out.push(v);
      });
    }
    while (out.length > room) out = out.filter(function (_, i) { return i % 2 === 0; });
    return out;
  }

  function setup(fig) {
    var plot = fig.querySelector(".mh__plot");
    var read = fig.querySelector(".mh__read");
    var data;
    try {
      data = JSON.parse(fig.querySelector(".mh-data").textContent);
    } catch (e) {
      return;
    }
    var over = data.kind === "overview";
    var ts = data.d.map(function (p) { return parse(p[0]); });
    var vs = data.d.map(function (p) { return p[1]; });
    var eps = (data.eps || []).map(function (e) {
      // [first month, last month, title, slug, years, fall]: from the first day of the
      // first month to the first day of the month after the last.
      var a = parse(e[0]), b = parse(e[1]), bd = new Date(b);
      return { a: a, b: Date.UTC(bd.getUTCFullYear(), bd.getUTCMonth() + 1, 1), title: e[2], slug: e[3], years: e[4], fall: e[5] };
    });
    var cur = over ? ts.length - 1 : data.low;
    var X, Y, w, h, cross, dot, xs;

    function episodeAt(t) {
      for (var i = 0; i < eps.length; i++) if (t >= eps[i].a && t < eps[i].b) return eps[i];
      return null;
    }

    function draw() {
      w = Math.round(plot.clientWidth);
      h = Math.round(plot.clientHeight);
      if (!w || !h) return;
      var L = 46, R = over ? 6 : 10, T = 14, B = 26;
      var t0 = ts[0], t1 = ts[ts.length - 1];
      var lo = Math.min.apply(null, vs), hi = Math.max.apply(null, vs);
      var f, g;
      if (data.log) {
        f = function (v) { return Math.log(v); };
        lo = lo / 1.12;
        hi = hi * 1.12;
      } else {
        f = function (v) { return v; };
        var pad = (hi - lo) * 0.1 || hi * 0.05;
        lo = Math.max(0, lo - pad);
        hi = hi + pad;
      }
      var flo = f(lo), fhi = f(hi);
      X = function (t) { return L + (w - L - R) * (t - t0) / ((t1 - t0) || 1); };
      Y = function (v) { return T + (h - T - B) * (1 - (f(v) - flo) / ((fhi - flo) || 1)); };
      var svg = el("svg", { "class": "chart", viewBox: "0 0 " + w + " " + h, width: w, height: h, "aria-hidden": "true" });

      // The episode's months, where the chart runs beyond them.
      if (data.ep) {
        var e0 = parse(data.ep[0]), e1 = parse(data.ep[1]);
        if (e0 > t0 || e1 < t1) {
          svg.appendChild(el("rect", { "class": "mh-epband", x: X(e0), y: T, width: Math.max(1, X(e1) - X(e0)), height: h - T - B }));
        }
      }
      // Falls, peak to low.
      var bands = data.bands || (data.peak != null ? [[data.d[data.peak][0], data.d[data.low][0]]] : []);
      bands.forEach(function (b) {
        var a = X(parse(b[0])), z = X(parse(b[1]));
        svg.appendChild(el("rect", { "class": "band-down", x: a, y: T, width: Math.max(1, z - a), height: h - T - B }));
      });
      // Grid with round values.
      var ticks = [];
      if (data.log) {
        ticks = logTicks(lo, hi, h < 280 ? 4 : 6);
      } else {
        // At least three lines: a finer round step when the range sits between two.
        for (var n = h < 280 ? 3 : 4; n <= 12 && ticks.length < 3; n++) {
          var step = niceStep(hi - lo, n);
          ticks = [];
          for (var v = Math.ceil(lo / step) * step; v <= hi; v += step) ticks.push(v);
        }
      }
      ticks.forEach(function (v) {
        svg.appendChild(el("line", { "class": "grid-line", x1: L, x2: w - R, y1: Y(v), y2: Y(v) }));
        svg.appendChild(el("text", { "class": "chart__label", x: 0, y: Y(v) + 4 }, tick(v)));
      });
      // Years along the foot: every year, or every 2, 5, 10 or 20 to fit.
      var y0 = new Date(t0).getUTCFullYear(), y1 = new Date(t1).getUTCFullYear();
      var every = [1, 2, 5, 10, 20, 25, 50].find(function (n) { return (w - L - R) / ((y1 - y0 + 1) / n) >= 52; }) || 50;
      var years = [];
      for (var y = Math.ceil((y0 + (Date.UTC(y0, 0, 1) < t0 ? 1 : 0)) / every) * every; y <= y1; y += every) {
        var tx = X(Date.UTC(y, 0, 1));
        if (tx >= L - 1 && tx <= w - R) years.push([y, tx]);
      }
      if (years.length < 2) {
        // A short chart: its first and last day instead, as on the dashboard pages.
        svg.appendChild(el("text", { "class": "chart__label", x: L, y: h - 6 }, day(t0)));
        svg.appendChild(el("text", { "class": "chart__label", x: w - R, y: h - 6, "text-anchor": "end" }, day(t1)));
      } else {
        years.forEach(function (p) {
          svg.appendChild(el("line", { "class": "mh-tick", x1: p[1], x2: p[1], y1: h - B, y2: h - B + 4 }));
          var anchor = p[1] - L < 16 ? "start" : w - R - p[1] < 16 ? "end" : "middle";
          svg.appendChild(el("text", { "class": "chart__label", x: p[1], y: h - 6, "text-anchor": anchor }, String(p[0])));
        });
      }
      svg.appendChild(el("line", { "class": "mh-base", x1: L, x2: w - R, y1: h - B, y2: h - B }));
      // The peak's level, from the peak to the day it was regained (or the end).
      if (data.peak != null) {
        var pv = vs[data.peak];
        var endT = data.back != null ? ts[data.back] : t1;
        svg.appendChild(el("line", { "class": "ref", x1: X(ts[data.peak]), x2: X(endT), y1: Y(pv), y2: Y(pv) }));
      }
      // The line.
      var d = "";
      for (var i = 0; i < ts.length; i++) d += (i ? " L" : "M") + X(ts[i]).toFixed(1) + " " + Y(vs[i]).toFixed(1);
      svg.appendChild(el("path", { "class": "line", d: d }));
      // Peak, low and back at the peak, named beside their dots.
      if (data.peak != null) {
        // The peak above its dot and the low below it, where the line is clear; "Back at
        // the peak" above the dashed level and left of its dot, where the line was still below.
        var marks = [[data.peak, "Peak", -1], [data.low, "Low", 1]];
        if (data.back != null) marks.push([data.back, "Back at the peak", -1, true]);
        marks.forEach(function (m) {
          var mx = X(ts[m[0]]), my = Y(vs[m[0]]);
          svg.appendChild(el("circle", { "class": "dot", cx: mx, cy: my, r: 3 }));
          var anchor = m[3] ? "end" : mx - L < 40 ? "start" : w - R - mx < 60 ? "end" : "middle";
          var lx = m[3] ? mx - 6 : mx;
          // Too close to the peak's own label (a quick recovery on a narrow chart), or to
          // the left edge: below the level line instead, right of the dot where there is room.
          if (m[3] && (mx - 104 < X(ts[data.peak]) + 20 || mx - L < 110)) {
            var right = w - R - mx > 110;
            anchor = right ? "start" : "end";
            lx = right ? mx + 6 : mx - 6;
            m[2] = 1;
          }
          var ly = m[2] < 0 ? my - 9 : my + 18;
          if (ly < 11) ly = my + 18;
          if (ly > h - B - 4) ly = my - 9;
          svg.appendChild(el("text", { "class": "chart__label mh-mark", x: lx, y: ly, "text-anchor": anchor }, m[1]));
        });
      }
      cross = el("line", { "class": "cross", y1: T, y2: h - B });
      dot = el("circle", { "class": "dot", r: 3.5 });
      svg.appendChild(cross);
      svg.appendChild(dot);
      xs = ts.map(X);
      plot.replaceChildren(svg);
      show(cur);
    }

    function show(i) {
      cur = Math.max(0, Math.min(ts.length - 1, i));
      if (!cross) return;
      var x = xs[cur], y = Y(vs[cur]);
      cross.setAttribute("x1", x);
      cross.setAttribute("x2", x);
      dot.setAttribute("cx", x);
      dot.setAttribute("cy", y);
      var text = day(ts[cur]) + ": " + num(vs[cur]);
      if (over) {
        var ep = episodeAt(ts[cur]);
        if (ep) text = esc(ep.title) + ", " + ep.years + (ep.fall ? " (fall " + move(ep.fall) + ")" : "") + ". " + text;
      } else if (data.peak != null && cur > data.peak && (data.back == null || cur < data.back)) {
        text += ", " + move(signed((vs[cur] / vs[data.peak] - 1) * 100, 1, "%")) + " from the peak";
      }
      read.innerHTML = text;
    }

    function nearest(px) {
      var a = 0, b = xs.length - 1;
      while (b - a > 1) {
        var m = (a + b) >> 1;
        if (xs[m] < px) a = m; else b = m;
      }
      return Math.abs(xs[a] - px) <= Math.abs(xs[b] - px) ? a : b;
    }

    function open() {
      var ep = over && episodeAt(ts[cur]);
      if (ep) location.href = ep.slug + "/";
    }

    plot.addEventListener("pointermove", function (e) {
      if (!xs) return;
      var r = plot.getBoundingClientRect();
      show(nearest(e.clientX - r.left));
    });
    plot.addEventListener("pointerleave", function () {
      show(over ? ts.length - 1 : data.low);
    });
    if (over) {
      plot.classList.add("mh__plot--open");
      plot.addEventListener("click", function (e) {
        if (!xs) return;
        var r = plot.getBoundingClientRect();
        show(nearest(e.clientX - r.left));
        open();
      });
    }
    plot.addEventListener("keydown", function (e) {
      var step = e.shiftKey ? Math.max(1, Math.round(ts.length / 20)) : 1;
      if (e.key === "ArrowRight") show(cur + step);
      else if (e.key === "ArrowLeft") show(cur - step);
      else if (e.key === "Home") show(0);
      else if (e.key === "End") show(ts.length - 1);
      else if (e.key === "Enter" && over) open();
      else return;
      e.preventDefault();
    });

    var timer;
    window.addEventListener("resize", function () {
      clearTimeout(timer);
      timer = setTimeout(draw, 120);
    });
    draw();
  }

  document.querySelectorAll("[data-mh]").forEach(setup);
})();
