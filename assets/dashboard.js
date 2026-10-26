/* Andra Markets dashboard pages: one chart drawn at the plot's own pixel size
   from the figures embedded in the page, with a view selector, a range
   selector, a comparison date, series toggles, and a readout that follows the
   pointer or the arrow keys. Tokens and rules: DESIGN.md (Dashboard page). */
(function () {
  "use strict";
  var page = document.querySelector("[data-dash]");
  var src = document.getElementById("dd-data");
  if (!page || !src) return;
  var D = JSON.parse(src.textContent);
  var plot = page.querySelector(".dd__plot");
  var key = page.querySelector(".dd__key");
  var out = page.querySelector(".dd__read");
  var status = page.querySelector(".dd__status");
  var rangeChips = page.querySelectorAll(".dd__ranges .chip");
  var viewChips = page.querySelectorAll(".dd__views .chip");
  var toggles = page.querySelector(".dd__toggles");
  var dateIn = page.querySelector(".dd__date input");
  var NS = "http://www.w3.org/2000/svg";
  var MINUS = "−";
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var MAX_LINES = 6; // line views: six monochrome styles (owner-approved, 26 Oct 2026)
  var cur = page.getAttribute("data-range"); // a range label, or "date" when a comparison date is set
  var from = null; // the comparison date, ISO
  var view = page.getAttribute("data-view") || "main";
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
  // Rises in green, falls in red, read from the printed sign (DESIGN.md,
  // The Rise and Fall Rule); a figure that rounds to zero stays in ink.
  function moveClass(text) {
    return text.charAt(0) === "+" ? " mv--up" : text.charAt(0) === MINUS ? " mv--down" : "";
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
  var SPAN = { "1W": 0.25, "1M": 1, "3M": 3, "6M": 6, "1Y": 12, "2Y": 24, "5Y": 60 };

  /* The start of the range: the comparison date, or the range before the latest date. */
  function startIso(last) {
    if (cur === "date" && from) return from;
    if (cur === "1W") {
      var d = parse(last);
      d.setUTCDate(d.getUTCDate() - 7);
      return d.toISOString().slice(0, 10);
    }
    return monthsBack(last, SPAN[cur] || 1);
  }
  /* Index of the first date on or after the range's start. */
  function window_(dates) {
    var start = startIso(dates[dates.length - 1]);
    var i0 = 0;
    while (i0 < dates.length - 1 && dates[i0] < start) i0++;
    return i0;
  }
  /* Index of the last date on or before iso, or -1. */
  function atOrBefore(dates, iso) {
    var i = -1;
    for (var k = 0; k < dates.length && dates[k] <= iso; k++) i = k;
    return i;
  }
  function extent(vals, padFrac, floor) {
    var lo = Infinity, hi = -Infinity;
    vals.forEach(function (v) { if (v != null && isFinite(v)) { lo = Math.min(lo, v); hi = Math.max(hi, v); } });
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
    var d = "", pen = false;
    pts.forEach(function (p) {
      if (p == null) { pen = false; return; }
      d += (pen ? " L" : (d ? " M" : "M")) + p[0].toFixed(1) + " " + p[1].toFixed(1);
      pen = true;
    });
    return d;
  }
  // Key items: [class, label]. The six line styles draw as a short SVG line.
  function keyItems(items) {
    key.replaceChildren();
    items.forEach(function (it) {
      var s = document.createElement("span");
      if (/^s\d$/.test(it[0])) {
        var sv = el("svg", { width: 16, height: 6, viewBox: "0 0 16 6", "aria-hidden": "true", "class": "chart key__line" });
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
  function svgFor(w, h) {
    return el("svg", { "class": "chart", viewBox: "0 0 " + w + " " + h, width: w, height: h, "aria-hidden": "true" });
  }
  function nearest(xs, x) {
    var best = 0;
    for (var i = 1; i < xs.length; i++) if (Math.abs(xs[i] - x) < Math.abs(xs[best] - x)) best = i;
    return best;
  }
  function say(text) {
    if (status) status.textContent = text || "";
  }

  /* Series toggles ----------------------------------------------------------- */

  // The series a view can toggle, and which are on, kept per view.
  var ON = {};
  function list() {
    var v = VIEWS[view];
    return v && v.series ? v.series() : null;
  }
  function onFor(series) {
    if (!ON[view]) {
      var cap = VIEWS[view].lines ? MAX_LINES : Infinity, n = 0;
      var all = VIEWS[view].allOn;
      ON[view] = series.map(function (s) {
        var on = (all || s.on !== false) && n < (VIEWS[view].firstOn || cap);
        if (on) n++;
        return on;
      });
      if (!n && series.length) ON[view][0] = true;
    }
    return ON[view];
  }
  function renderToggles() {
    if (!toggles) return;
    var series = list();
    toggles.parentNode.hidden = !series || series.length < 2;
    if (!series || series.length < 2) return;
    var on = onFor(series);
    toggles.innerHTML = series.map(function (s, i) {
      return '<button type="button" class="chip" data-i="' + i + '" aria-pressed="' + on[i] + '">' + s.name.replace(/&/g, "&amp;").replace(/</g, "&lt;") + "</button>";
    }).join("");
  }
  if (toggles) {
    toggles.addEventListener("click", function (e) {
      var b = e.target.closest(".chip");
      if (!b) return;
      var on = ON[view], i = +b.getAttribute("data-i");
      var count = on.filter(Boolean).length;
      if (on[i] && count === 1) { say("At least one series stays on."); return; }
      if (!on[i] && VIEWS[view].lines && count >= MAX_LINES) {
        say("Up to six lines at once. Turn one off first.");
        return;
      }
      if (!on[i] && VIEWS[view].maxOn && count >= VIEWS[view].maxOn) {
        say("Up to " + VIEWS[view].maxOn + " at once. Turn one off first.");
        return;
      }
      on[i] = !on[i];
      b.setAttribute("aria-pressed", String(on[i]));
      say("");
      index = -1;
      draw();
    });
  }
  function picked(series) {
    var on = onFor(series);
    var out = [];
    series.forEach(function (s, i) { if (on[i]) out.push({ s: s, i: i }); });
    return out;
  }

  /* Several lines on one axis, in the six monochrome styles, each named at its
     right end. mode: level, rebase (to 100 at the range's start) or change
     (since the range's start, in the series' unit; bp for percent levels). */
  function multi(w, h, o) {
    var dates = o.dates, i0 = window_(dates), ds = dates.slice(i0);
    var chosen = o.chosen;
    var lines = chosen.map(function (c, k) {
      var raw = c.s.values.slice(i0), v = raw.slice(), base = null, last = null;
      // Carry the last value over days a series did not trade.
      for (var j = 0; j < v.length; j++) {
        if (v[j] == null) v[j] = last; else last = v[j];
        if (base == null && v[j] != null) base = v[j];
      }
      var sign = o.sign ? o.sign[c.i] : 1;
      var shown = v.map(function (x) {
        if (x == null) return null;
        if (o.mode === "rebase") return Math.pow(x / base, sign) * 100;
        if (o.mode === "change") return (x - base) * (o.unit === "%" ? 100 : 1);
        return x;
      });
      return { name: c.s.name, raw: v, v: shown, base: base, cls: "s" + (k % 6), dec: c.s.dec != null ? c.s.dec : o.dec };
    });
    var all = [];
    lines.forEach(function (l) { all = all.concat(l.v); });
    if (o.mode === "rebase") all.push(100);
    if (o.mode === "change" || o.zero) all.push(0);
    var labW = w < 520 ? 0 : 112, L = 44, R = 4 + labW, T = 8, B = 22;
    var e = extent(all, 0.08, 0.01), lo = e[0], hi = e[1];
    var X = function (i) { return L + (w - L - R) * i / Math.max(ds.length - 1, 1); };
    var Y = function (v) { return T + (h - T - B) * (1 - (v - lo) / (hi - lo)); };
    var unitY = o.mode === "change" ? (o.unit === "%" ? "bp" : o.unit || "") : (o.mode === "rebase" ? "" : o.unit || "");
    var svg = svgFor(w, h);
    gridY(svg, lo, hi, Y, L, w - R, function (v) {
      return o.mode === "rebase" ? num(v, 0) : num(v, Math.abs(hi - lo) < 5 && unitY !== "bp" ? 1 : 0) + (unitY === "%" ? "%" : "");
    });
    if (o.mode === "rebase") svg.appendChild(el("line", { "class": "ref", x1: L, x2: w - R, y1: Y(100), y2: Y(100) }));
    if (o.mode === "change" || o.zero) svg.appendChild(el("line", { "class": "ref", x1: L, x2: w - R, y1: Y(0), y2: Y(0) }));
    dates2(svg, day(ds[0]), day(ds[ds.length - 1]), L, w - R, h - 4);
    lines.forEach(function (l) {
      var pts = l.v.map(function (v, i) { return v == null ? null : [X(i), Y(v)]; });
      if (o.area && l === lines[1]) {
        var a = pts.filter(Boolean);
        if (a.length) svg.appendChild(el("path", { "class": "area", d: path(a) + " L" + a[a.length - 1][0] + " " + Y(Math.max(lo, 0)) + " L" + a[0][0] + " " + Y(Math.max(lo, 0)) + " Z" }));
      }
      svg.appendChild(el("path", { "class": l.cls, d: path(pts) }));
    });
    // Names at the right end, pushed apart so they never overlap.
    if (labW) {
      var tags = lines.map(function (l) {
        var lv = l.v[l.v.length - 1];
        return { l: l, y: lv == null ? null : Y(lv) };
      }).filter(function (t) { return t.y != null; }).sort(function (a, b) { return a.y - b.y; });
      for (var k = 1; k < tags.length; k++) if (tags[k].y - tags[k - 1].y < 14) tags[k].y = tags[k - 1].y + 14;
      var over = tags.length ? tags[tags.length - 1].y - (h - B) : 0;
      if (over > 0) tags.forEach(function (t) { t.y -= over; });
      tags.forEach(function (t) {
        var nm = t.l.name.length > 16 ? t.l.name.slice(0, 15) + "…" : t.l.name;
        svg.appendChild(el("text", { "class": "chart__label chart__end", x: w - R + 8, y: t.y + 4 }, nm));
      });
    }
    var cross = el("line", { "class": "cross", y1: T, y2: h - B });
    var dots = lines.map(function () { return el("circle", { "class": "dot", r: 3 }); });
    svg.appendChild(cross);
    dots.forEach(function (d) { svg.appendChild(d); });
    keyItems(lines.map(function (l) { return [l.cls, l.name]; }).concat(o.keyExtra || []));
    var xs = ds.map(function (_, i) { return X(i); });
    function fig(l, i) {
      var x = l.v[i];
      if (x == null) return l.name + " n/a";
      if (o.mode === "rebase") return l.name + " " + num(x, 1) + " (" + signed(x - 100, 2, "%") + ")";
      if (o.mode === "change") return l.name + " " + signed(x, unitY === "bp" ? 0 : (o.dec != null ? o.dec : 2), unitY === "bp" ? "bp" : unitY);
      return l.name + " " + num(x, l.dec != null ? l.dec : 2) + (o.unit === "%" ? "%" : o.unit === "bp" ? "bp" : "");
    }
    return {
      svg: svg, xs: xs,
      label: (o.mode === "rebase" ? "Rebased to 100 on " + day(ds[0]) + ". " : o.mode === "change" ? "Change since " + day(ds[0]) + ". " : "") +
        lines.map(function (l) { return fig(l, l.v.length - 1); }).join(", ") + " on " + day(ds[ds.length - 1]),
      show: function (i) {
        cross.setAttribute("x1", xs[i]); cross.setAttribute("x2", xs[i]);
        lines.forEach(function (l, j) {
          dots[j].setAttribute("cx", xs[i]);
          dots[j].setAttribute("cy", l.v[i] == null ? -10 : Y(l.v[i]));
        });
        return day(ds[i]) + ": " + lines.map(function (l) { return fig(l, i); }).join(", ");
      }
    };
  }

  /* Labelled diverging bars, largest first: rows [name, value, readout]. */
  function bars(w, rows, o) {
    if (!o.keepOrder) rows = rows.slice().sort(function (p, q) { return q[1] - p[1]; });
    var row = 26, T = 2, h = T + row * rows.length;
    var nameW = Math.min(170, w * 0.42), valW = 72;
    var x0 = nameW + (w - nameW - valW) / 2, half = (w - nameW - valW) / 2 - 4;
    var m = 0.01;
    rows.forEach(function (p) { m = Math.max(m, Math.abs(p[1])); });
    var svg = svgFor(w, h);
    svg.appendChild(el("line", { "class": "ref", x1: x0, x2: x0, y1: 0, y2: h }));
    var ys = rows.map(function (p, i) {
      var y = T + i * row, bwid = Math.max(Math.abs(p[1]) / m * half, 1);
      svg.appendChild(el("text", { "class": "chart__label", x: 0, y: y + 17 }, p[0].length > 26 ? p[0].slice(0, 25) + "…" : p[0]));
      svg.appendChild(el("rect", { "class": p[1] >= 0 ? "up" : "down", x: p[1] >= 0 ? x0 : x0 - bwid, y: y + 6, width: bwid, height: 14 }));
      var lab = signed(p[1], o.dec, o.unit);
      svg.appendChild(el("text", { "class": "chart__value" + moveClass(lab), x: w, y: y + 17, "text-anchor": "end" }, lab));
      return y;
    });
    var band = el("rect", { "class": "hover-band", x: 0, y: 0, width: w, height: row });
    svg.insertBefore(band, svg.firstChild);
    keyItems(o.key);
    return {
      svg: svg, ys: ys, h: h,
      label: o.label + rows.map(function (p) { return p[0] + " " + signed(p[1], o.dec, o.unit); }).join(", "),
      show: function (i) {
        band.setAttribute("y", ys[i]);
        return rows[i][2];
      }
    };
  }

  /* Changes over the range for every instrument switched on, each from its own
     latest close back to its last close on or before the range's start. */
  function ranked(w) {
    var H = D.hist, sign = H.sign;
    var last = H.dates[H.dates.length - 1];
    var start = startIso(last);
    var rows = [];
    picked(H.series).forEach(function (c) {
      var v = c.s.values, li = v.length - 1;
      while (li >= 0 && v[li] == null) li--;
      if (li < 1) return;
      var bi;
      if (cur === "1D") {
        bi = li - 1;
        while (bi >= 0 && v[bi] == null) bi--;
      } else {
        bi = atOrBefore(H.dates, start);
        while (bi >= 0 && v[bi] == null) bi--;
      }
      if (bi < 0) return;
      var k = sign ? sign[c.i] : 1, chg = k * (v[li] / v[bi] - 1) * 100;
      rows.push([c.s.name, chg, c.s.name + ": " + signed(chg, 2, "%") + ", close of " + day(H.dates[bi]) + " to close of " + day(H.dates[li])]);
    });
    var span = cur === "1D" ? "the day" : cur === "date" ? "since " + day(start) : cur;
    return bars(w, rows, {
      dec: 2, unit: "%",
      key: sign ? [["sw-up", "Dollar stronger"], ["sw-down", "Dollar weaker"]] : [["sw-up", "Up"], ["sw-down", "Down"]],
      label: "Change over " + span + ": "
    });
  }

  /* A term structure today against the same curve on the comparison date. */
  function compareCurve() {
    if (cur !== "date" && D.compare[cur]) return D.compare[cur];
    var H = D.hist, n = D.labels.length;
    var i = atOrBefore(H.dates, startIso(D.date));
    if (i < 0) i = 0;
    return { date: H.dates[i], values: H.series.slice(0, n).map(function (s) { return s.values[i]; }) };
  }
  function curve(w, h) {
    var cmp = compareCurve();
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
    var b = cmp.values.map(function (v, i) { return v == null ? null : [X(i), Y(v)]; });
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
          (cmp.values[i] == null ? "n/a" : num(cmp.values[i], dec) + (D.unit || "")) + " on " + day(cmp.date) +
          (cmp.values[i] == null ? "" : " (" + change(i) + ")");
      }
    };
  }
  /* How far each point on the curve has moved since the comparison date. */
  function curveChange(w) {
    var cmp = compareCurve(), bp = D.unit === "%";
    var rows = [];
    D.labels.forEach(function (lb, i) {
      if (cmp.values[i] == null) return;
      var dlt = (D.values[i] - cmp.values[i]) * (bp ? 100 : 1);
      rows.push([lb, dlt, lb + ": " + signed(dlt, bp ? 0 : 2, bp ? "bp" : " points") + ", " + num(cmp.values[i], D.dec) +
        (D.unit || "") + " on " + day(cmp.date) + " to " + num(D.values[i], D.dec) + (D.unit || "") + " on " + day(D.date)]);
    });
    var c = bars(w, rows, {
      dec: bp ? 0 : 2, unit: bp ? "bp" : "",
      key: [["sw-up", "Higher"], ["sw-down", "Lower"]],
      // In tenor order, not ranked: the curve's shape reads from top to bottom.
      keepOrder: true,
      label: "Change from " + day(cmp.date) + " to " + day(D.date) + ": "
    });
    return c;
  }

  /* Monthly inflation lines above monthly payroll bars. */
  function macro(w, h) {
    var i0 = window_(D.dates), dates = D.dates.slice(i0), jobs = D.jobs.slice(i0);
    var measures = picked(D.measures || [{ name: "CPI", values: D.cpi }]);
    var ls = measures.map(function (c, k) { return { name: c.s.name, v: c.s.values.slice(i0), cls: "s" + (k % 6) }; });
    var L = 40, R = 4, T = 6, B = 22, split = (h - B) * 0.58;
    var all = [];
    ls.forEach(function (l) { all = all.concat(l.v); });
    var e = extent(all, 0.1, 0.2), lo = e[0], hi = e[1];
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
    ls.forEach(function (l) {
      svg.appendChild(el("path", { "class": l.cls, d: path(l.v.map(function (v, i) { return v == null ? null : [X(i), Y(v)]; })) }));
    });
    dates2(svg, month(dates[0]), month(dates[dates.length - 1]), L, w - R, h - 4);
    var cross = el("line", { "class": "cross", y1: T, y2: h - B }), dot = el("circle", { "class": "dot", r: 3 });
    svg.appendChild(cross); svg.appendChild(dot);
    keyItems(ls.map(function (l) { return [l.cls, l.name + ", year on year"]; }).concat([["sw-up", "Jobs added"], ["sw-down", "Jobs lost"]]));
    var xs = dates.map(function (_, i) { return X(i); });
    var head = ls[0].v, lastC = head.length - 1; while (lastC > 0 && head[lastC] == null) lastC--;
    var lastJ = jobs.length - 1; while (lastJ > 0 && jobs[lastJ] == null) lastJ--;
    return {
      svg: svg, xs: xs,
      label: ls[0].name + " inflation " + num(head[lastC], 1) + "% in " + month(dates[lastC]) + "; payrolls " + signed(jobs[lastJ], 0) + " thousand in " + month(dates[lastJ]),
      show: function (i) {
        cross.setAttribute("x1", xs[i]); cross.setAttribute("x2", xs[i]);
        dot.setAttribute("cx", xs[i]); dot.setAttribute("cy", head[i] == null ? -10 : Y(head[i]));
        return month(dates[i]) + ": " + ls.map(function (l) {
          return l.name + " " + (l.v[i] == null ? "not published" : num(l.v[i], 1) + "%");
        }).join(", ") + "; payrolls " + (jobs[i] == null ? "not published" : signed(jobs[i], 0) + " thousand");
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
  /* The running total of advancers less decliners from the range's start. */
  function breadthLine(w, h) {
    var dates = D.sessions.map(function (s) { return s[0]; }), t = 0;
    var vals = D.sessions.map(function (s) { t += s[1] - s[2]; return t; });
    return multi(w, h, {
      dates: dates, mode: "change", unit: "", dec: 0, zero: true,
      chosen: [{ s: { name: "Advance-decline line", values: vals, dec: 0 }, i: 0 }]
    });
  }

  /* Correlation of daily log returns, on the sessions every chosen asset traded. */
  function returnsOf(idx, i0, i1) {
    var S = D.hist.series, prev = -1, out = idx.map(function () { return []; });
    for (var i = i0; i <= i1; i++) {
      var ok = idx.every(function (k) { return S[k].values[i] != null; });
      if (!ok) continue;
      if (prev >= 0) idx.forEach(function (k, j) { out[j].push(Math.log(S[k].values[i] / S[k].values[prev])); });
      prev = i;
    }
    return out;
  }
  function corr(x, y) {
    var n = x.length, mx = 0, my = 0, sxy = 0, sxx = 0, syy = 0;
    for (var i = 0; i < n; i++) { mx += x[i]; my += y[i]; }
    mx /= n; my /= n;
    for (i = 0; i < n; i++) { sxy += (x[i] - mx) * (y[i] - my); sxx += (x[i] - mx) * (x[i] - mx); syy += (y[i] - my) * (y[i] - my); }
    return sxy / Math.sqrt(sxx * syy);
  }
  var SESSIONS = { "1M": 21, "3M": 63, "6M": 126, "1Y": 250 };
  function matrix(w) {
    var H = D.hist, ch = picked(H.series), n = ch.length, idx = ch.map(function (c) { return c.i; });
    var endIso = cur === "date" && from ? from : H.dates[H.dates.length - 1];
    var span = SESSIONS[cur] || 63;
    var i1 = atOrBefore(H.dates, endIso);
    // Walk back until the window holds its sessions in common.
    var i0 = i1, got = 0;
    while (i0 > 0 && got < span) {
      i0--;
      if (idx.every(function (k) { return H.series[k].values[i0] != null; })) got++;
    }
    var rets = returnsOf(idx, i0, i1), sessions = rets[0].length;
    var M = idx.map(function (_, a) { return idx.map(function (_, b) { return a === b ? 1 : corr(rets[a], rets[b]); }); });
    var labW = Math.min(130, w * 0.32), top = 22;
    var c = Math.min((w - labW) / Math.max(n, 1), 72), h = top + c * n;
    var svg = svgFor(w, h);
    var cells = [];
    ch.forEach(function (x, j) {
      svg.appendChild(el("text", { "class": "chart__label", x: labW + c * (j + 0.5), y: 14, "text-anchor": "middle" }, x.s.short || x.s.name));
    });
    ch.forEach(function (x, i) {
      svg.appendChild(el("text", { "class": "chart__label", x: 0, y: top + c * (i + 0.5) + 4 }, x.s.name));
      for (var j = 0; j < n; j++) {
        var v = M[i][j];
        svg.appendChild(el("rect", { "class": v >= 0 ? "up" : "down", x: labW + c * j + 1, y: top + c * i + 1, width: c - 2, height: c - 2, opacity: (0.12 + 0.45 * Math.abs(v)).toFixed(2) }));
        if (c >= 34) svg.appendChild(el("text", { "class": "chart__value", x: labW + c * (j + 0.5), y: top + c * (i + 0.5) + 4, "text-anchor": "middle" }, signed(v, 2).replace(/^\+/, "")));
        if (i !== j) cells.push([i, j]);
      }
    });
    var ring = el("rect", { "class": "cell-ring", width: c, height: c, x: -100 });
    svg.appendChild(ring);
    keyItems([["sw-up", "Move together"], ["sw-down", "Move apart"]]);
    var fromIso = H.dates[i0], toIso = H.dates[i1];
    var names = ch.map(function (x) { return x.s.name; });
    return {
      svg: svg, cells: cells, labW: labW, top: top, c: c, n: n, h: h,
      label: "Correlation of daily returns over " + sessions + " sessions from " + day(fromIso) + " to " + day(toIso) + ": " +
        cells.filter(function (p) { return p[0] < p[1]; }).map(function (p) {
          return names[p[0]] + " and " + names[p[1]] + " " + signed(M[p[0]][p[1]], 2);
        }).join(", "),
      show: function (k) {
        var p = cells[k];
        ring.setAttribute("x", labW + c * p[1]); ring.setAttribute("y", top + c * p[0]);
        return names[p[0]] + " and " + names[p[1]] + ": " + signed(M[p[0]][p[1]], 2).replace(/^\+/, "") +
          " over " + sessions + " sessions, " + day(fromIso) + " to " + day(toIso);
      }
    };
  }
  /* Rolling correlation of the first asset switched on with each of the others. */
  function rolling(w, h) {
    var H = D.hist, ch = picked(H.series);
    if (ch.length < 2) { say("Switch on at least two assets."); ch = picked(H.series); }
    var base = ch[0], span = SESSIONS[cur === "date" ? "3M" : cur] || 63;
    var others = ch.slice(1);
    var outSeries = others.map(function (o) {
      var vals = H.dates.map(function () { return null; });
      // Returns on the days both traded, then a trailing window.
      var days = [], ra = [], rb = [], prev = -1;
      for (var i = 0; i < H.dates.length; i++) {
        var a = base.s.values[i], b = o.s.values[i];
        if (a == null || b == null) continue;
        if (prev >= 0) {
          ra.push(Math.log(a / base.s.values[prev]));
          rb.push(Math.log(b / o.s.values[prev]));
          days.push(i);
        }
        prev = i;
      }
      for (var k = span; k <= ra.length; k++) vals[days[k - 1]] = corr(ra.slice(k - span, k), rb.slice(k - span, k));
      return { name: "With " + o.s.name, values: vals, dec: 2 };
    });
    var r = multi(w, h, {
      dates: H.dates, mode: "level", unit: "", dec: 2, zero: true,
      chosen: outSeries.map(function (s, i) { return { s: s, i: i }; })
    });
    r.label = "Correlation of " + base.s.name + " with each asset over trailing " + span + "-session windows. " + r.label;
    return r;
  }

  /* Views ---------------------------------------------------------------------- */

  var VIEWS = {};
  function lineView(get, opts) {
    return {
      lines: true,
      series: function () { return get().series; },
      draw: function (w, h) {
        var b = get();
        return multi(w, h, {
          dates: b.dates, chosen: picked(b.series), mode: opts.mode, unit: opts.unit != null ? opts.unit : b.unit,
          dec: opts.dec != null ? opts.dec : 2, sign: opts.sign ? D.hist.sign : null, area: opts.area
        });
      }
    };
  }
  if (D.kind === "perf") {
    VIEWS.main = { series: function () { return D.hist.series; }, draw: function (w) { return ranked(w); } };
    VIEWS.rebased = lineView(function () { return D.hist; }, { mode: "rebase", sign: true });
    VIEWS.rebased.firstOn = 4;
  } else if (D.kind === "curve") {
    VIEWS.main = { draw: curve };
    VIEWS.change = { draw: function (w) { return curveChange(w); } };
    VIEWS.time = lineView(function () { return D.hist; }, { mode: "level", dec: D.dec });
    if (D.spreads) VIEWS.spreads = lineView(function () { return D.spreads; }, { mode: "level", unit: "bp", dec: 0 });
  } else if (D.kind === "lines") {
    var lv = { series: function () { return D.series; }, lines: true };
    lv.draw = function (w, h) {
      return multi(w, h, { dates: D.dates, chosen: picked(D.series), mode: D.rebase ? "rebase" : "level", unit: D.unit, dec: D.dec, area: !D.rebase });
    };
    VIEWS.main = lv;
    if (D.rebase) {
      VIEWS.ranked = {
        allOn: true,
        series: function () { return D.series; },
        draw: function (w) {
          D.hist = D.hist || { dates: D.dates, series: D.series };
          return ranked(w);
        }
      };
    } else {
      VIEWS.change = lineView(function () { return { dates: D.dates, series: D.series, unit: D.unit }; }, { mode: "change" });
    }
  } else if (D.kind === "macro") {
    VIEWS.main = { series: function () { return D.measures || []; }, lines: true, draw: macro };
    if (D.unrate) VIEWS.unrate = { draw: function (w, h) {
      return multi(w, h, { dates: D.dates, mode: "level", unit: "%", dec: 1, chosen: [{ s: { name: "Unemployment rate", values: D.unrate, dec: 1 }, i: 0 }] });
    } };
  } else if (D.kind === "breadth") {
    VIEWS.main = { draw: breadth };
    VIEWS.cum = { draw: breadthLine };
  } else if (D.kind === "matrix") {
    VIEWS.main = { series: function () { return D.hist.series; }, draw: function (w) { return matrix(w); } };
    VIEWS.rolling = { series: function () { return D.hist.series; }, lines: true, draw: rolling };
  }
  // Toggles on the ranked and rolling views share the main view's choice where sensible.
  if (D.kind === "matrix") ON.rolling = null;

  // The readout colours its signed figures as moves; correlations are not moves.
  function movesFor() {
    if (D.kind === "matrix" || view === "time" || view === "spreads" || view === "unrate") out.removeAttribute("data-moves");
    else out.setAttribute("data-moves", "");
  }

  function draw() {
    var w = plot.clientWidth, h = plot.clientHeight;
    if (!w) return;
    var v = VIEWS[view] || VIEWS.main;
    plot.style.height = "";
    var tall = v === VIEWS.main && (D.kind === "perf" || D.kind === "matrix") || view === "change" || view === "ranked";
    plot.classList.toggle("dd__plot--auto", !!tall);
    h = plot.clientHeight;
    var chart = v.draw(w, h);
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
      var k = 0;
      for (var a = 0; a < chart.n; a++) for (var b = 0; b < chart.n; b++) {
        if (a === b) continue;
        if (a === i && b === j) return k;
        k++;
      }
      return -1;
    }
    chart.svg.addEventListener("pointermove", function (e) {
      var k = pick(e);
      if (k >= 0) show(k);
    });
    if (!count) { out.textContent = ""; return; }
    // Start on the latest point, the top bar, or the first pair off the diagonal.
    show(index >= 0 && index < count ? index : chart.xs ? count - 1 : 0);
  }
  // The readout's figures roll to each new point (AndraRoll, assets/site.js).
  var roll = window.AndraRoll ? new window.AndraRoll(out) : null;
  function show(k) {
    index = k;
    var text = hover.show(k);
    if (roll) roll.set(text);
    else out.textContent = text;
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
  rangeChips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      cur = chip.getAttribute("data-range");
      from = null;
      if (dateIn) dateIn.value = "";
      rangeChips.forEach(function (c) { c.setAttribute("aria-pressed", String(c === chip)); });
      index = -1;
      say("");
      draw();
    });
  });
  if (dateIn) {
    dateIn.addEventListener("change", function () {
      var v = dateIn.value;
      if (!v) return;
      if ((dateIn.min && v < dateIn.min) || (dateIn.max && v > dateIn.max)) {
        say("Pick a date between " + day(dateIn.min) + " and " + day(dateIn.max) + ".");
        return;
      }
      from = v;
      cur = "date";
      rangeChips.forEach(function (c) { c.setAttribute("aria-pressed", "false"); });
      index = -1;
      say("");
      draw();
    });
  }
  viewChips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      view = chip.getAttribute("data-view");
      viewChips.forEach(function (c) { c.setAttribute("aria-pressed", String(c === chip)); });
      // The 1D range belongs to the ranked bars; elsewhere it falls back to 1M.
      var oneDay = page.querySelector('.dd__ranges .chip[data-range="1D"]');
      if (oneDay) {
        oneDay.hidden = view !== "main";
        if (oneDay.hidden && cur === "1D") {
          var m = page.querySelector('.dd__ranges .chip[data-range="1M"]');
          if (m) m.click();
        }
      }
      var dateWrap = page.querySelector(".dd__date");
      if (dateWrap) dateWrap.hidden = view === "rolling";
      index = -1;
      say("");
      renderToggles();
      movesFor();
      draw();
    });
  });
  renderToggles();
  movesFor();
  if ("ResizeObserver" in window) new ResizeObserver(function () { draw(); }).observe(plot);
  else window.addEventListener("resize", draw);
  draw();
})();
