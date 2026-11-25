/* Break into Wall Street: the guide as a path (owner, 25 Nov 2026). In place of the "On this page" list, the guide's
   sections stand along one line of light that climbs from the lower left to a skyline at the upper right: a rope of
   fine strands with a heavy line through it, a ring at each section with its number and name. Each ring is that
   section's link. Pointing at one, or reaching it with the keyboard, lights the path up to it and leaves the rest
   dim. The order is the page's own; the path says where the guide leads, not that every step must be taken in turn.
   On a phone the path stands upright: it winds down the left of the screen from the first section to the skyline
   at its foot, each section's number and name to the right of its ring. Without this script the page keeps its list. */
(function () {
  "use strict";
  var toc = document.querySelector(".pw-toc"), main = document.querySelector("main"); if (!toc || !main) return;
  var links = [].map.call(toc.querySelectorAll("a"), function (a) { return { href: a.getAttribute("href"), name: a.textContent }; });
  if (links.length < 3) return;
  var NS = "http://www.w3.org/2000/svg", still = window.matchMedia("(prefers-reduced-motion: reduce)").matches, n = links.length;
  function num(i) { return (i < 9 ? "0" : "") + (i + 1); }
  function rng(s) { return function () { s = (s * 16807) % 2147483647; return s / 2147483647; }; }

  var nav = document.createElement("nav"); nav.className = "wp"; nav.setAttribute("aria-label", "On this page");
  var plot = document.createElement("div"); plot.className = "wp__plot"; nav.appendChild(plot);
  toc.parentNode.insertBefore(nav, toc); main.classList.add("has-path");

  function el(name, at, p) { var e = document.createElementNS(NS, name); for (var k in at) e.setAttribute(k, at[k]); if (p) p.appendChild(e); return e; }
  function draw() {
    var W = plot.clientWidth; if (!W) return;
    var up = window.matchMedia("(max-width: 899px)").matches, STEP = 78, pts = [], i, k, t;   // up: the upright path of a phone
    var SW = up ? W - 96 : Math.min(330, W * 0.26), SH = up ? 104 : Math.min(150, plot.clientHeight * 0.42);
    var H = up ? 34 + (n - 1) * STEP + 64 + SH : plot.clientHeight, G = up ? H - 1 : SH + 16;   // G: the ground the skyline stands on
    plot.textContent = "";
    var svg = el("svg", { width: W, height: H, viewBox: "0 0 " + W + " " + H }, plot);
    if (up) { for (i = 0; i < n; i++) pts.push([46 + Math.sin(i * 1.9) * 22, 34 + i * STEP]); pts.push([40, G]); }
    else {
      var x0 = 24, xe = W - SW - 36, yb = H - 74;
      for (i = 0; i < n; i++) { t = i / (n - 1); pts.push([x0 + t * (xe - x0), yb - t * (yb - G) - Math.sin(t * 6.9) * (yb - G) * 0.07]); }
      pts[n - 1][1] = G; pts.push([W - SW, G]);
    }
    function seg(a, b, off) {   // one step of the line, leaving and arriving level (or, upright, plumb), moved off to the side for a strand
      var ox = up ? off : 0, oy = up ? 0 : off, mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, c1 = up ? [a[0], my] : [mx, a[1]], c2 = up ? [b[0], my] : [mx, b[1]];
      return "M" + (a[0] + ox).toFixed(1) + " " + (a[1] + oy).toFixed(1) + " C" + (c1[0] + ox).toFixed(1) + " " + (c1[1] + oy).toFixed(1) + " " + (c2[0] + ox).toFixed(1) + " " + (c2[1] + oy).toFixed(1) + " " + (b[0] + ox).toFixed(1) + " " + (b[1] + oy).toFixed(1);
    }
    function whole(off) { var d = ""; for (var j = 1; j < pts.length; j++) d += (j > 1 ? seg(pts[j - 1], pts[j], off).replace(/^M[^C]+/, " ") : seg(pts[0], pts[1], off)); return d; }

    // The skyline the path leads to: towers of fine lines, some windows lit, on the line the path arrives by.
    var sky = el("g", { "class": "wp-sky", "aria-hidden": "true" }, svg), r = rng(7), cx = W - SW + 10, yt = G;
    el("line", { x1: up ? 0 : W - SW, x2: W, y1: yt, y2: yt, "class": "wp-ground" }, sky);
    while (cx < W - 12) {
      var bw = Math.min(14 + r() * 30, W - cx), bh = SH * (0.28 + r() * 0.72);
      for (k = 0; k <= bw; k += 3.2) el("line", { x1: cx + k, x2: cx + k, y1: yt, y2: yt - bh, "class": "wp-wall", opacity: (0.3 + r() * 0.4).toFixed(2) }, sky);
      for (var q = 0; q < bh / 9 - 1; q++) if (r() > 0.55) { var win = el("rect", { x: cx + 2 + Math.floor(r() * (bw - 4) / 3.2) * 3.2 - 0.8, y: yt - 8 - q * 9, width: 1.6, height: 3, "class": "wp-win" }, sky); if (r() > 0.8) win.style.setProperty("--d", (r() * 6).toFixed(1) + "s"), win.setAttribute("class", "wp-win wp-win--live"); }
      cx += bw + 3 + r() * 5;
    }
    // The rope: strands either side of the line, then the line itself, a stretch for each step so it can light up to a point.
    var rope = el("g", { "aria-hidden": "true" }, svg);
    for (k = (up ? -5 : -8); k <= (up ? 5 : 8); k++) if (k) el("path", { d: whole(k * 2.6), "class": "wp-strand" }, rope);
    var segs = []; for (i = 1; i < pts.length; i++) segs.push(el("path", { d: seg(pts[i - 1], pts[i], 0), "class": "wp-line", pathLength: 1, style: "--i:" + (i - 1) }, rope));
    if (!still) { var spark = el("circle", { r: 2.2, "class": "wp-spark" }, rope); el("animateMotion", { dur: "11s", repeatCount: "indefinite", path: whole(0) }, spark); }
    // The sections: a ring, its number and its name, clear of the line (under and right of it, or over and left).
    var stops = links.map(function (l, j) {
      var p = pts[j], a = el("a", { href: l.href, "class": "wp-stop", style: "--i:" + j }, svg), no, name;
      if (up) {   // a phone: the whole row is the link, the words to the right of the path
        el("rect", { x: 0, y: p[1] - STEP / 2, width: W, height: STEP, fill: "transparent" }, a);
        el("circle", { cx: p[0], cy: p[1], r: 4.2, "class": "wp-ring" }, a);
        no = el("text", { x: 98, y: p[1] - 12, "class": "wp-no" }, a); name = el("text", { x: 98, y: p[1] + 12, "class": "wp-name" }, a);
      } else {
        var under = j % 2 === 0 && j < n - 1;
        el("circle", { cx: p[0], cy: p[1], r: 16, fill: "transparent" }, a);
        el("circle", { cx: p[0], cy: p[1], r: 4.2, "class": "wp-ring" }, a);
        no = el("text", { x: p[0] + (under ? 2 : -2), y: p[1] + (under ? 34 : -44), "class": "wp-no", "text-anchor": under ? "start" : "end" }, a);
        name = el("text", { x: p[0] + (under ? 2 : -2), y: p[1] + (under ? 56 : -22), "class": "wp-name", "text-anchor": under ? "start" : "end" }, a);
      }
      no.textContent = num(j); name.textContent = l.name;
      if (up && name.getComputedTextLength && name.getComputedTextLength() > W - 98) {   // too long for a phone: on two lines
        var words = l.name.split(" "), cut = Math.ceil(words.length / 2); name.textContent = "";
        [words.slice(0, cut), words.slice(cut)].forEach(function (part, q) { var ts = el("tspan", { x: 98, dy: q ? 22 : 0 }, name); ts.textContent = part.join(" "); });
        name.setAttribute("y", p[1] + 6); no.setAttribute("y", p[1] - 18);
      }
      return a;
    });
    function light(j) {   // j: the stop pointed at, or -1 for none
      svg.classList.toggle("is-lit", j >= 0);
      segs.forEach(function (s, q) { s.classList.toggle("is-on", q < j); });
      stops.forEach(function (s, q) { s.classList.toggle("is-on", q <= j); s.classList.toggle("is-at", q === j); });
    }
    stops.forEach(function (s, j) {
      s.addEventListener("pointerenter", function () { light(j); }); s.addEventListener("pointerleave", function () { light(-1); });
      s.addEventListener("focus", function () { light(j); }); s.addEventListener("blur", function () { light(-1); });
    });
  }
  draw();
  var w0 = plot.clientWidth;
  function again() { if (plot.clientWidth !== w0) { w0 = plot.clientWidth; nav.classList.add("is-drawn"); draw(); } }   // drawn again without the opening
  if ("ResizeObserver" in window) new ResizeObserver(again).observe(plot); else window.addEventListener("resize", again);
})();
