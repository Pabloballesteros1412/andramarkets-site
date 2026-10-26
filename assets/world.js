/* Andra Markets World markets page: up to three markets on one radar, every
   axis on the same scale (the lowest figure among the 25 markets near the
   centre, the highest at the edge), a table of the figures compared with their
   dates and sources, and a readout for the axis under the pointer or the arrow
   keys. Tokens and rules: DESIGN.md (World markets). */
(function () {
  "use strict";
  var page = document.querySelector("[data-world]");
  var src = document.getElementById("wm-data");
  if (!page || !src) return;
  var D = JSON.parse(src.textContent);
  var plot = page.querySelector(".wm-plot");
  var key = page.querySelector(".dd__key");
  var out = page.querySelector(".dd__read");
  var status = page.querySelector(".dd__status");
  var table = page.querySelector(".wm-cmp");
  var NS = "http://www.w3.org/2000/svg";
  var MINUS = "−";
  var MAX = 3;
  var STYLES = ["s0", "s1", "s2"];
  var picked = D.start.slice();
  var axis = 0;
  var names = {};
  D.markets.forEach(function (m) { names[m.iso] = m; });

  function el(name, attrs, text) {
    var e = document.createElementNS(NS, name);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  }
  function num(v, dec) {
    return v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec }).replace("-", MINUS);
  }
  function signed(v, dec) {
    var r = Number(v.toFixed(dec));
    return (r > 0 ? "+" : r < 0 ? MINUS : "") + num(Math.abs(r), dec);
  }
  // A move keeps its sign and takes green or red (The Rise and Fall Rule); a level stays in ink.
  function fig(a, rec, html) {
    if (!rec) return html ? '<span class="wm-na">No figure</span>' : "no figure";
    var t = (a.move ? signed(rec.v, 2) : num(rec.v, 2)) + a.unit;
    if (!html || !a.move) return t;
    var c = t.charAt(0) === "+" ? "mv mv--up" : t.charAt(0) === MINUS ? "mv mv--down" : "";
    return c ? '<span class="' + c + '">' + t + "</span>" : t;
  }
  function esc(t) {
    return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  }
  function frac(a, v) {
    var s = D.scale[a.k];
    if (!s) return null;
    var t = s.hi === s.lo ? 0.5 : (v - s.lo) / (s.hi - s.lo);
    return 0.12 + 0.88 * t;
  }

  function draw() {
    var w = plot.clientWidth;
    if (!w) return;
    var h = Math.min(w, 520);
    plot.style.height = h + "px";
    var n = D.axes.length, cx = w / 2, cy = h / 2;
    var R = Math.max(60, Math.min(w / 2 - (w < 480 ? 58 : 92), h / 2 - 26));
    var svg = el("svg", { "class": "chart", width: w, height: h, viewBox: "0 0 " + w + " " + h, "aria-hidden": "true" });
    var ang = D.axes.map(function (_, i) { return -Math.PI / 2 + 2 * Math.PI * i / n; });
    [0.25, 0.5, 0.75, 1].forEach(function (k) {
      svg.appendChild(el("circle", { "class": "grid-line wm-ring", cx: cx, cy: cy, r: R * k }));
    });
    var hi = el("line", { "class": "cross", x1: cx, y1: cy, x2: cx, y2: cy });
    svg.appendChild(hi);
    D.axes.forEach(function (a, i) {
      var x = cx + R * Math.cos(ang[i]), y = cy + R * Math.sin(ang[i]);
      svg.appendChild(el("line", { "class": "grid-line", x1: cx, y1: cy, x2: x, y2: y }));
      var lx = cx + (R + 12) * Math.cos(ang[i]), ly = cy + (R + 12) * Math.sin(ang[i]);
      var c = Math.cos(ang[i]);
      svg.appendChild(el("text", {
        "class": "chart__label wm-axis", x: lx, y: ly + (Math.sin(ang[i]) > 0.5 ? 12 : Math.sin(ang[i]) < -0.5 ? -4 : 4),
        "text-anchor": c > 0.3 ? "start" : c < -0.3 ? "end" : "middle"
      }, a.short));
    });
    picked.forEach(function (iso, k) {
      var pts = D.axes.map(function (a, i) {
        var rec = (D.figures[iso] || {})[a.k];
        var f = rec ? frac(a, rec.v) : null;
        return f == null ? null : [cx + R * f * Math.cos(ang[i]), cy + R * f * Math.sin(ang[i])];
      });
      // Only between neighbouring axes that both have a figure: a gap is a missing one.
      var d = "";
      for (var i = 0; i < n; i++) {
        var p = pts[i], q = pts[(i + 1) % n];
        if (p && q) d += "M" + p[0].toFixed(1) + " " + p[1].toFixed(1) + " L" + q[0].toFixed(1) + " " + q[1].toFixed(1) + " ";
      }
      if (k === 0 && pts.every(Boolean)) {
        svg.appendChild(el("path", { "class": "area", d: "M" + pts.map(function (p) { return p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" L") + " Z" }));
      }
      svg.appendChild(el("path", { "class": STYLES[k], d: d }));
      pts.forEach(function (p) { if (p) svg.appendChild(el("circle", { "class": "dot", cx: p[0], cy: p[1], r: 2.6 })); });
    });
    plot.replaceChildren(svg);
    key.replaceChildren();
    picked.forEach(function (iso, k) {
      var s = document.createElement("span");
      var sv = el("svg", { width: 16, height: 6, viewBox: "0 0 16 6", "class": "chart key__line", "aria-hidden": "true" });
      sv.appendChild(el("line", { "class": STYLES[k], x1: 0, x2: 16, y1: 3, y2: 3 }));
      s.appendChild(sv);
      s.appendChild(document.createTextNode(names[iso].name));
      key.appendChild(s);
    });
    plot.setAttribute("aria-label", "Radar of " + picked.map(function (iso) { return names[iso].name; }).join(", ") +
      " on eight measures. " + D.axes.map(function (a) {
        return a.label + ": " + picked.map(function (iso) { return names[iso].name + " " + fig(a, (D.figures[iso] || {})[a.k]); }).join(", ");
      }).join(". ") + ". Use the arrow keys to read each measure.");
    function show(i) {
      axis = i;
      hi.setAttribute("x2", cx + R * Math.cos(ang[i]));
      hi.setAttribute("y2", cy + R * Math.sin(ang[i]));
      var a = D.axes[i];
      out.innerHTML = esc(a.label) + ": " + picked.map(function (iso) {
        var rec = (D.figures[iso] || {})[a.k];
        return esc(names[iso].name) + " " + fig(a, rec, true) + (rec ? " (" + esc(rec.when) + ")" : "");
      }).join(", ");
    }
    svg.addEventListener("pointermove", function (e) {
      var r = svg.getBoundingClientRect(), x = e.clientX - r.left - cx, y = e.clientY - r.top - cy;
      var t = Math.atan2(y, x) + Math.PI / 2;
      if (t < 0) t += 2 * Math.PI;
      show(Math.round(t / (2 * Math.PI / n)) % n);
    });
    draw.show = show;
    show(axis);
  }

  function renderTable() {
    var head = "<tr><th scope=\"col\">Measure</th>" + picked.map(function (iso, k) {
      return '<th scope="col"><span class="wm-cmp__key"><svg width="16" height="6" viewBox="0 0 16 6" class="chart key__line" aria-hidden="true"><line class="' + STYLES[k] +
        '" x1="0" x2="16" y1="3" y2="3"></line></svg>' + esc(names[iso].name) + "</span></th>";
    }).join("") + "</tr>";
    var rows = D.axes.map(function (a) {
      return '<tr><th scope="row">' + esc(a.label) + "</th>" + picked.map(function (iso) {
        var rec = (D.figures[iso] || {})[a.k];
        return '<td><span class="wm-cmp__v">' + fig(a, rec, true) + "</span>" +
          (rec ? '<span class="wm-cmp__src">' + esc(rec.when) + ", " + esc(rec.src) + "</span>" : "") + "</td>";
      }).join("") + "</tr>";
    }).join("");
    table.tHead.innerHTML = head;
    table.tBodies[0].innerHTML = rows;
    table.hidden = false;
  }

  function sync() {
    page.querySelectorAll("[data-m]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(picked.indexOf(b.getAttribute("data-m")) >= 0));
    });
    draw();
    renderTable();
  }
  page.addEventListener("click", function (e) {
    var b = e.target.closest("[data-m]");
    if (!b) return;
    var iso = b.getAttribute("data-m"), i = picked.indexOf(iso);
    status.textContent = "";
    if (i >= 0) {
      if (picked.length === 1) { status.textContent = "At least one market stays on the chart."; return; }
      picked.splice(i, 1);
    } else {
      if (picked.length >= MAX) { status.textContent = "Up to three markets at once. Remove one first."; return; }
      picked.push(iso);
    }
    sync();
    if (b.classList.contains("wm-mini")) plot.scrollIntoView({ block: "center", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  });
  plot.addEventListener("keydown", function (e) {
    var step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
    if (!step || !draw.show) return;
    e.preventDefault();
    draw.show((axis + step + D.axes.length) % D.axes.length);
  });
  if ("ResizeObserver" in window) {
    var lastW = 0;
    new ResizeObserver(function () {
      if (plot.clientWidth !== lastW) { lastW = plot.clientWidth; draw(); }
    }).observe(plot);
  } else window.addEventListener("resize", draw);
  sync();
})();
