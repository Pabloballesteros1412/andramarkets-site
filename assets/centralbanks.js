// Central banks (central-banks/): the four policy rates since 2019 as step
// lines in the Fed & Rates look (assets/fedrates.js), a crosshair readout
// (pointer and arrow keys), the days to each bank's next meeting counted in
// New York time, and "Save image" (a PNG of the chart, made in the browser).
(function () {
  "use strict";
  var NS = "http://www.w3.org/2000/svg";
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  function t(iso) {
    return Date.parse(iso + "T00:00:00Z");
  }
  function iso(ms) {
    return new Date(ms).toISOString().slice(0, 10);
  }
  function dmed(s) {
    var p = s.split("-");
    return +p[2] + " " + MON[+p[1] - 1] + " " + p[0];
  }

  // Next meetings: the first decision day not yet past in New York, and the days to it.
  function nyToday() {
    try {
      var parts = {};
      new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit" })
        .formatToParts(new Date()).forEach(function (p) { parts[p.type] = p.value; });
      return parts.year + "-" + parts.month + "-" + parts.day;
    } catch (e) {
      return iso(Date.now());
    }
  }
  function countdowns() {
    var today = nyToday();
    document.querySelectorAll("tr[data-next]").forEach(function (row) {
      var days;
      try { days = JSON.parse(row.getAttribute("data-next")); } catch (e) { return; }
      var d = days.filter(function (x) { return x >= today; })[0];
      var a = row.querySelector("[data-cb-day]"), b = row.querySelector("[data-cb-in]");
      if (!d || !a || !b) return;
      var n = Math.round((t(d) - t(today)) / 864e5);
      a.textContent = dmed(d);
      b.textContent = n === 0 ? "Today" : n === 1 ? "Tomorrow" : "In " + n + " days";
    });
  }
  countdowns();
  setInterval(countdowns, 60000);

  var el = document.getElementById("cb-data");
  if (!el) return;
  var D = JSON.parse(el.textContent);
  if (!D.banks || !D.banks.length || !document.getElementById("cb-chart-plot")) return;

  function mk(tag, attrs, parent, text) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  }
  function ticks(lo, hi, n) {
    if (!((hi - lo) / n > 0) || !isFinite(hi - lo)) return [];
    var step = Math.pow(10, Math.floor(Math.log10((hi - lo) / n)));
    var err = (hi - lo) / n / step;
    step *= err >= 5 ? 10 : err >= 2 ? 5 : err >= 1.4 ? 2 : 1;
    var out = [];
    for (var v = Math.ceil(lo / step) * step; v <= hi + step * 1e-6 && out.length < 50; v += step) out.push(+v.toFixed(6));
    return out;
  }
  function minus(s) {
    return String(s).replace("-", "−");
  }
  function pct(v) {
    return minus(v.toFixed(2)) + "%";
  }

  // One axis for the four: every change day and one point a week, so the
  // crosshair lands on each change.
  var STY = ["s0", "s1", "s3", "s2"];
  var start = t(D.from);
  var end = Math.max.apply(null, D.banks.map(function (b) { return t(b.asof); }));
  var axis = {};
  for (var x = start; x <= end; x += 7 * 864e5) axis[x] = 1;
  axis[end] = 1;
  D.banks.forEach(function (b) {
    b.steps.forEach(function (p) { axis[t(p[0])] = 1; });
    axis[t(b.asof)] = 1;
  });
  var xs = Object.keys(axis).map(Number).sort(function (a, b) { return a - b; });
  function at(steps, x, last) {
    if (x > last || x < t(steps[0][0])) return null;
    var v = null;
    for (var i = 0; i < steps.length && t(steps[i][0]) <= x; i++) v = steps[i][1];
    return v;
  }
  var series = D.banks.map(function (b, k) {
    var last = t(b.asof);
    return { name: b.name, label: b.label, cls: STY[k], steps: b.steps, last: last,
             ys: xs.map(function (x) { return at(b.steps, x, last); }),
             lower: b.lower ? xs.map(function (x) { return at(b.lower, x, last); }) : null };
  });

  function draw() {
    var box = document.getElementById("cb-chart-plot");
    var W = box.clientWidth || 640;
    var H = Math.max(240, Math.min(380, W * 0.42));
    var narrow = W < 520;
    var m = { l: 44, r: narrow ? 8 : 56, t: 12, b: 26 };
    box.innerHTML = "";
    box.style.height = H + "px";
    var svg = mk("svg", { class: "chart", viewBox: "0 0 " + W + " " + H, width: W, height: H, role: "presentation" }, box);
    var all = [0];
    series.forEach(function (s) { s.ys.forEach(function (v) { if (v != null) all.push(v); }); });
    var lo = Math.min.apply(null, all), hi = Math.max.apply(null, all);
    var pad = (hi - lo) * 0.08 || 0.1;
    lo -= pad;
    hi += pad;
    var x0 = xs[0], x1 = xs[xs.length - 1];
    function X(x) { return m.l + ((x - x0) / (x1 - x0 || 1)) * (W - m.l - m.r); }
    function Y(v) { return m.t + (1 - (v - lo) / (hi - lo)) * (H - m.t - m.b); }
    ticks(lo, hi, 4).forEach(function (v) {
      mk("line", { class: "grid-line", x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) }, svg);
      mk("text", { class: "chart__label", x: m.l - 8, y: Y(v) + 4, "text-anchor": "end" }, svg, minus(v.toFixed(Math.abs(hi - lo) < 3 ? 1 : 0)) + "%");
    });
    if (lo < 0 && hi > 0) mk("line", { class: "ref", x1: m.l, x2: W - m.r, y1: Y(0), y2: Y(0) }, svg);
    var y0 = new Date(x0).getUTCFullYear(), y1 = new Date(x1).getUTCFullYear();
    var every = (W - m.l - m.r) / Math.max(1, y1 - y0) < 44 ? 2 : 1;
    for (var yr = y0; yr <= y1; yr++) {
      var tx = Date.UTC(yr, 0, 1);
      if (tx >= x0 && tx <= x1 && (yr - y0) % every === 0) mk("text", { class: "chart__label", x: X(tx), y: H - 6, "text-anchor": "middle" }, svg, String(yr));
    }
    var g = mk("g", { class: "fr-draw" }, svg);
    var ends = [];
    series.forEach(function (s) {
      // A step line: level until the day it changes, then straight to the new level.
      var d = "", prev = null;
      s.steps.forEach(function (p, i) {
        var px = X(Math.max(t(p[0]), x0)), py = Y(p[1]);
        d += i === 0 ? "M" + px.toFixed(1) + " " + py.toFixed(1) : "H" + px.toFixed(1) + "V" + py.toFixed(1);
        prev = p[1];
      });
      d += "H" + X(Math.min(s.last, x1)).toFixed(1);
      mk("path", { class: s.cls, d: d }, g);
      ends.push({ name: s.name, y: Y(prev) });
    });
    if (!narrow) {
      ends.sort(function (a, b) { return a.y - b.y; });
      for (var i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 14) ends[i].y = ends[i - 1].y + 14;
      ends.forEach(function (e) { mk("text", { class: "chart__label chart__end", x: W - m.r + 8, y: e.y + 4 }, svg, e.name); });
    }
    var key = document.getElementById("cb-chart-key");
    key.innerHTML = series.map(function (s) {
      return '<span><svg class="key__line chart" viewBox="0 0 16 6"><line class="' + s.cls + '" x1="0" x2="16" y1="3" y2="3" style="fill:none"/></svg>' + s.label + "</span>";
    }).join("") + (lo < 0 && hi > 0 ? '<span><i class="k-ref"></i>Zero</span>' : "");
    var cross = mk("line", { class: "cross", y1: m.t, y2: H - m.b, x1: -10, x2: -10 }, svg);
    var hot = mk("g", { class: "fr-hot" }, svg);
    var read = document.getElementById("cb-chart-read");
    var cur = xs.length - 1;
    function fig(s, k) {
      return s.lower && s.lower[k] != null ? s.lower[k].toFixed(2) + " to " + pct(s.ys[k]) : pct(s.ys[k]);
    }
    // Each series ends on its own as-of date, so the readout opens on every
    // bank's latest level with its date; a point under the pointer shows that day.
    function latest() {
      cur = xs.length - 1;
      cross.style.display = "none";  // the SVG draws outside its box, so park nothing at -10
      hot.innerHTML = "";
      read.innerHTML = "<b>Latest</b>: " + series.map(function (s) {
        var k = xs.indexOf(s.last);
        var d = dmed(iso(s.last));
        return s.name + " " + fig(s, k) + " (" + (new Date(s.last).getUTCFullYear() === new Date().getUTCFullYear() ? d.replace(/ \d{4}$/, "") : d) + ")";
      }).join(", ");
    }
    function show(i) {
      cur = Math.max(0, Math.min(xs.length - 1, i));
      var x = X(xs[cur]);
      cross.style.display = "";
      cross.setAttribute("x1", x);
      cross.setAttribute("x2", x);
      hot.innerHTML = "";
      var parts = [];
      series.forEach(function (s) {
        var v = s.ys[cur];
        if (v == null) return;
        mk("circle", { class: "dot", cx: x, cy: Y(v), r: 3.5 }, hot);
        parts.push(s.name + " " + fig(s, cur));
      });
      read.innerHTML = "<b>" + dmed(iso(xs[cur])) + "</b>: " + parts.join(", ");
    }
    svg.addEventListener("pointermove", function (e) {
      var r = svg.getBoundingClientRect(), px = ((e.clientX - r.left) / r.width) * W;
      var best = 0, bd = Infinity;
      xs.forEach(function (x, i) { var dd = Math.abs(X(x) - px); if (dd < bd) { bd = dd; best = i; } });
      show(best);
    });
    box.onkeydown = function (e) {
      var k = { ArrowLeft: cur - 1, ArrowRight: cur + 1, Home: 0, End: xs.length - 1 }[e.key];
      if (k != null) { e.preventDefault(); show(k); }
    };
    latest();
  }
  var rt, lastW = window.innerWidth;
  window.addEventListener("resize", function () {
    if (window.innerWidth === lastW) return;  // a phone's toolbar showing or hiding changes only the height
    lastW = window.innerWidth;
    clearTimeout(rt);
    rt = setTimeout(draw, 120);
  });
  draw();

  // Save image: the chart with its title, the mark, source and date.
  function inline(src, dst) {
    var cs = getComputedStyle(src);
    ["fill", "stroke", "stroke-width", "stroke-dasharray", "stroke-linecap", "stroke-linejoin", "opacity",
     "font-size", "font-weight", "font-family"].forEach(function (p) { dst.style.setProperty(p, cs.getPropertyValue(p)); });
    for (var i = 0; i < src.children.length; i++) inline(src.children[i], dst.children[i]);
  }
  document.querySelectorAll("[data-save]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var pid = btn.getAttribute("data-save");
      var sec = document.getElementById(pid);
      var svg = sec.querySelector(".fr__plot svg");
      if (!svg) return;
      btn.disabled = true;
      var root = getComputedStyle(document.documentElement);
      var ground = root.getPropertyValue("--ground").trim(), ink = root.getPropertyValue("--ink").trim(), ink3 = root.getPropertyValue("--ink-3").trim();
      var clone = svg.cloneNode(true);
      inline(svg, clone);
      clone.querySelectorAll(".cross, .fr-hot").forEach(function (n) { n.remove(); });
      clone.setAttribute("xmlns", NS);
      var w = +svg.getAttribute("width"), h = +svg.getAttribute("height");
      var img = new Image();
      img.onload = function () {
        var S = 2, P = 32, top = 96, foot = 72;
        var cv = document.createElement("canvas");
        cv.width = (w + P * 2) * S;
        cv.height = (h + top + foot) * S;
        var ctx = cv.getContext("2d");
        ctx.scale(S, S);
        ctx.fillStyle = ground;
        ctx.fillRect(0, 0, w + P * 2, h + top + foot);
        var mark = document.querySelector(document.documentElement.getAttribute("data-theme") === "dark" ? ".brand__mark--dark" : ".brand__mark--light");
        if (mark && mark.complete) ctx.drawImage(mark, P, 22, 17.5, 20);
        ctx.fillStyle = ink;
        ctx.font = '600 14px "Schibsted Grotesk", Arial, sans-serif';
        ctx.fillText("Andra Markets", P + 26, 38);
        ctx.font = '540 20px "Schibsted Grotesk", Arial, sans-serif';
        ctx.fillText("Central banks: " + sec.querySelector("h2").textContent, P, 74, w);
        ctx.drawImage(img, P, top, w, h);
        ctx.fillStyle = ink3;
        ctx.font = '400 12px "Schibsted Grotesk", Arial, sans-serif';
        ctx.fillText(sec.querySelector(".fr__src").textContent.replace(/\s+/g, " ").trim(), P, top + h + 30, w);
        ctx.fillText("Andra Markets. For information only. Not investment advice.", P, top + h + 48, w);
        cv.toBlob(function (blob) {
          var a = document.createElement("a");
          a.href = URL.createObjectURL(blob);
          a.download = "andra-markets-central-banks-" + new Date().toISOString().slice(0, 10) + ".png";
          document.body.appendChild(a);
          a.click();
          setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
          btn.disabled = false;
        }, "image/png");
      };
      img.onerror = function () { btn.disabled = false; };
      img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(new XMLSerializer().serializeToString(clone));
    });
  });
})();
