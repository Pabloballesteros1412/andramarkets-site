/* Andra Markets: the globe on the Companies index (companies/; owner's request, 13 Nov 2026).
   Every company the site follows is a point on a slowly turning sphere, set with its sector;
   a line joins two companies whose weekly returns move together (worked out at build time,
   tools/build_site.py, globe_data). Green and red are the last session's rise or fall.
   Pointing at a company names it and leaves only its lines; clicking it opens its page.
   On a touch screen the first tap names the company and the second opens it. The table under
   the globe lists the same companies as links, so nothing here is the only way to a page.
   Drawn on a 2D canvas at up to twice the device's pixels; it turns only while on screen and
   stays still under reduced motion. */
(function () {
  "use strict";
  var box = document.querySelector(".co-globe"), src = document.getElementById("globe-data");
  if (!box || !src) return;
  var D = JSON.parse(src.textContent), CO = D.co, N = CO.length, SEC = D.sectors;
  var cv = box.querySelector("canvas"), read = box.querySelector(".lens-read"), stats = box.querySelector(".lens-stats");
  var TAU = Math.PI * 2, MINUS = "−", INK = "242,243,243", UP = "31,210,122", DN = "255,75,82";
  var MONO = '"Geist Mono", ui-monospace, "SFMono-Regular", Menlo, monospace';
  var still = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  // a company: [folder, name, ticker, sector, market, last move in basis points]
  var SLUG = 0, NAME = 1, TICK = 2, SECT = 3, MKT = 4, MOVE = 5;

  function pct(bp) { var r = Number((bp / 100).toFixed(2)); return (r > 0 ? "+" : r < 0 ? MINUS : "") + Math.abs(r).toFixed(2) + "%"; }
  function esc(t) { return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function norm(a) { var l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; }
  function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
  function rng(seed) { var s = seed >>> 0; return function () { s = (s + 0x6D2B79F5) >>> 0; var t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

  /* Where each company sits: sectors spread over the sphere, their companies spiralling
     out from the middle of each, the largest first; then a few rounds of pushing apart. */
  var P = (function () {
    var G = SEC.length, centre = [], seen = {}, pts;
    for (var g = 0; g < G; g++) { var y = 1 - (g + 0.5) / G * 2, r = Math.sqrt(1 - y * y), a = g * 2.399963; centre.push([Math.cos(a) * r, y, Math.sin(a) * r]); }
    var gap = Math.min(0.1, 2.05 / Math.sqrt(N));
    pts = CO.map(function (c) {
      var k = seen[c[SECT]] = (seen[c[SECT]] || 0) + 1, c0 = centre[c[SECT]], rad = gap * 0.62 * Math.sqrt(k), ang = k * 2.399963;
      var u = norm(cross(c0, Math.abs(c0[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0])), v = cross(c0, u);
      return norm([c0[0] + (u[0] * Math.cos(ang) + v[0] * Math.sin(ang)) * rad, c0[1] + (u[1] * Math.cos(ang) + v[1] * Math.sin(ang)) * rad, c0[2] + (u[2] * Math.cos(ang) + v[2] * Math.sin(ang)) * rad]);
    });
    for (var it = 0; it < 6; it++) {
      for (var i = 0; i < N; i++) for (var j = i + 1; j < N; j++) {
        var p = pts[i], q = pts[j], dx = q[0] - p[0], dy = q[1] - p[1], dz = q[2] - p[2], d2 = dx * dx + dy * dy + dz * dz;
        if (d2 > gap * gap * 0.49 || d2 === 0) continue;
        var d = Math.sqrt(d2), push = (gap * 0.7 - d) / d * 0.5;
        p[0] -= dx * push; p[1] -= dy * push; p[2] -= dz * push; q[0] += dx * push; q[1] += dy * push; q[2] += dz * push;
      }
      pts = pts.map(norm);
    }
    return { pts: pts, centre: centre };
  })();
  var LINKS = D.links, mine = CO.map(function () { return []; });
  LINKS.forEach(function (l, n) { mine[l[0]].push(n); mine[l[1]].push(n); });
  var R0 = rng(7), cage = [];
  for (var q0 = 0; q0 < 16; q0++) cage.push([R0() * Math.PI, R0() * Math.PI]);
  // each link's arc, lifted a little off the surface, as points on the unit sphere
  var ARC = LINKS.map(function (l) {
    var a = P.pts[l[0]], b = P.pts[l[1]], om = Math.acos(Math.max(-1, Math.min(1, a[0] * b[0] + a[1] * b[1] + a[2] * b[2]))), so = Math.sin(om) || 1, out = [], seg = 5 + Math.round(om * 9);
    for (var k = 0; k <= seg; k++) { var t = k / seg, wa = Math.sin((1 - t) * om) / so, wb = Math.sin(t * om) / so, lift = 1 + 0.045 * om * Math.sin(Math.PI * t); out.push([(a[0] * wa + b[0] * wb) * lift, (a[1] * wa + b[1] * wb) * lift, (a[2] * wa + b[2] * wb) * lift]); }
    return out;
  });

  var S = { w: 0, h: 0, c: null, rad: 0 }, rotY = 0.6, rotX = -0.28, cosY, sinY, cosX, sinX;
  var hover = -1, held = -1, drag = null, on = false, Q = [], sectorOn = "all", marketOn = "all";
  function turn() { cosY = Math.cos(rotY); sinY = Math.sin(rotY); cosX = Math.cos(rotX); sinX = Math.sin(rotX); }
  function proj(p) {
    var x = p[0] * cosY + p[2] * sinY, z = -p[0] * sinY + p[2] * cosY, y = p[1] * cosX - z * sinX;
    return [S.w / 2 + x * S.rad, S.h / 2 - y * S.rad, p[1] * sinX + z * cosX];
  }
  function label(text, x, y, align, color, size) {
    var c = S.c;
    c.font = "400 " + (size || 10) + "px " + MONO; c.textAlign = align || "left"; c.fillStyle = color;
    if ("letterSpacing" in c) c.letterSpacing = "1px";
    c.fillText(String(text).toUpperCase(), x, y);
  }
  function shown(i) { return (sectorOn === "all" || D.slugs[CO[i][SECT]] === sectorOn) && (marketOn === "all" || CO[i][MKT] === marketOn); }
  function size() {
    var dpr = Math.min(window.devicePixelRatio || 1, N > 600 ? 1.5 : 2), w = cv.clientWidth, h = Math.round(Math.min(Math.max(w * 0.52, 340), 660));
    cv.style.height = h + "px"; cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
    S.c = cv.getContext("2d"); S.c.setTransform(dpr, 0, 0, dpr, 0, 0); S.w = w; S.h = h; S.rad = Math.min(w, h) * 0.445;
  }

  function draw(t) {
    var c = S.c, focus = hover >= 0 ? hover : held, filtered = sectorOn !== "all" || marketOn !== "all";
    turn();
    c.clearRect(0, 0, S.w, S.h);
    c.lineWidth = 1; c.strokeStyle = "rgba(" + INK + ",.07)";
    c.beginPath();
    cage.forEach(function (tl) {
      for (var k = 0; k <= 48; k++) { var a = k / 48 * TAU, x = Math.cos(a), y = Math.sin(a) * Math.cos(tl[0]), z = Math.sin(a) * Math.sin(tl[0]), s = proj([x * Math.cos(tl[1]) + z * Math.sin(tl[1]), y, -x * Math.sin(tl[1]) + z * Math.cos(tl[1])]); if (k) c.lineTo(s[0], s[1]); else c.moveTo(s[0], s[1]); }
    });
    c.stroke();
    c.beginPath(); c.arc(S.w / 2, S.h / 2, S.rad, 0, TAU); c.strokeStyle = "rgba(" + INK + ",.4)"; c.stroke();
    Q = P.pts.map(proj);
    // the lines, in three strokes: the far side, the near side, and the focus company's own
    // Stroked a few dozen arcs at a time: one path holding every arc is far slower to fill,
    // because the browser must work out where all its lines cross.
    var groups = { far: [], near: [], own: [] }, counts = { far: 0, near: 0, own: 0 };
    function into(kind, pts) {
      var g = groups[kind];
      if (counts[kind]++ % 28 === 0) g.push(new Path2D());
      var path = g[g.length - 1];
      path.moveTo(pts[0][0], pts[0][1]);
      for (var k = 1; k < pts.length; k++) path.lineTo(pts[k][0], pts[k][1]);
    }
    for (var n = 0; n < LINKS.length; n++) {
      var l = LINKS[n], isOwn = focus >= 0 && (l[0] === focus || l[1] === focus);
      if (!isOwn && (focus >= 0 ? n % 3 : n % thin)) continue;
      if (filtered && !(shown(l[0]) && shown(l[1]))) continue;
      var a = ARC[n], z = 0, pts = [];
      for (var k = 0; k < a.length; k++) { var s = proj(a[k]); z += s[2]; pts.push(s); }
      var near = z / a.length > 0;
      if (!near && !isOwn && (dense || thin > 1)) continue;  // the far side's lines are the first to go
      into(isOwn ? "own" : near ? "near" : "far", pts);
    }
    function stroke(kind, width, alpha) { c.lineWidth = width; c.strokeStyle = "rgba(" + INK + "," + alpha + ")"; groups[kind].forEach(function (p) { c.stroke(p); }); }
    stroke("far", 0.7, focus >= 0 ? 0.04 : 0.07);
    stroke("near", 0.7, focus >= 0 ? 0.09 : 0.26);
    stroke("own", 1.1, 0.85);
    // the companies: the far side first and dimmer
    var tied = {};
    if (focus >= 0) mine[focus].forEach(function (n) { var l = LINKS[n]; tied[l[0] === focus ? l[1] : l[0]] = l[2]; });
    // drawn in a handful of fills, not one a company: far or near, risen or fallen, bright or dimmed
    var bins = {}, i;
    for (i = 0; i < N; i++) {
      var s = Q[i], front = s[2] > 0, m = CO[i][MOVE], lit = (!filtered || shown(i)) && (focus < 0 || i === focus || tied[i] != null);
      var r = (i < 60 ? 2.6 : i < 300 ? 2 : 1.5) * (front ? 1 : 0.6) * (i === focus ? 2 : tied[i] != null && focus >= 0 ? 1.4 : 1);
      var key = (front ? "1" : "0") + (m > 0 ? "u" : m < 0 ? "d" : "n") + (lit ? "1" : "0"), path = bins[key] || (bins[key] = new Path2D());
      path.moveTo(s[0] + r, s[1]); path.arc(s[0], s[1], r, 0, TAU);
    }
    ["0", "1"].forEach(function (f) { ["n", "d", "u"].forEach(function (d) { ["0", "1"].forEach(function (l) {
      var path = bins[f + d + l];
      if (!path) return;
      c.fillStyle = "rgba(" + (d === "u" ? UP : d === "d" ? DN : INK) + "," + ((f === "1" ? 1 : 0.25) * (l === "1" ? 1 : filtered ? 0.12 : 0.45)).toFixed(2) + ")"; c.fill(path);
    }); }); });
    if (S.w > 620) P.centre.forEach(function (p, g) {
      var s = proj([p[0] * 1.13, p[1] * 1.13, p[2] * 1.13]);
      if (s[2] > -0.15) label(SEC[g], s[0], s[1], "center", "rgba(116,121,124," + (s[2] > 0.25 ? 0.95 : 0.5) + ")", 9);
    });
    // names: the largest that face us when nothing is in focus; the focus and its companions when one is
    if (focus < 0 && S.w > 620) { for (i = 0; i < Math.min(N, 14); i++) if (Q[i][2] > 0.45 && (!filtered || shown(i))) label(CO[i][TICK], Q[i][0] + 7, Q[i][1] + 3, "left", "rgba(163,168,170," + ((Q[i][2] - 0.45) * 1.8).toFixed(2) + ")", 9); }
    if (focus >= 0) {
      Object.keys(tied).forEach(function (j) { if (Q[j][2] > 0) label(CO[j][TICK], Q[j][0] + 7, Q[j][1] + 3, "left", "rgba(163,168,170,.9)", 9); });
      var f = Q[focus], mv = CO[focus][MOVE], right = f[0] > S.w - 220;
      c.beginPath(); c.arc(f[0], f[1], 9 + (still ? 0 : Math.sin(t * 3) * 1.5), 0, TAU); c.strokeStyle = "rgba(" + INK + ",.8)"; c.lineWidth = 1; c.stroke();
      label(CO[focus][NAME], f[0] + (right ? -14 : 14), f[1] - 4, right ? "right" : "left", "rgb(" + INK + ")", 11);
      label(pct(mv), f[0] + (right ? -14 : 14), f[1] + 10, right ? "right" : "left", "rgb(" + (mv >= 0 ? UP : DN) + ")", 10);
    }
  }
  function say() {
    var f = hover >= 0 ? hover : held;
    if (f < 0) {
      var ups = CO.filter(function (c) { return c[MOVE] > 0; }).length, downs = CO.filter(function (c) { return c[MOVE] < 0; }).length;
      read.innerHTML = "Last session · <b>" + ups + "</b> rose · <b>" + downs + "</b> fell · point at a company, click to open its page";
      return;
    }
    var c = CO[f], ties = mine[f].map(function (n) { var l = LINKS[n]; return [l[0] === f ? l[1] : l[0], l[2]]; }).sort(function (a, b) { return b[1] - a[1]; });
    read.innerHTML = "<b>" + esc(c[NAME]) + "</b> · " + esc(SEC[c[SECT]]) + ' · <span class="mv ' + (c[MOVE] >= 0 ? "mv--up" : "mv--down") + '">' + pct(c[MOVE]) + "</span>" +
      (ties.length ? " · moves with " + ties.slice(0, 4).map(function (x) { return esc(CO[x[0]][TICK]) + " " + (x[1] / 100).toFixed(2); }).join(", ") : " · no close companion") +
      (held === f && hover < 0 ? ' · <a href="' + encodeURI(c[SLUG]) + '/">Open its page</a>' : "");
  }

  // A slow device draws fewer lines: after a run of long frames, every second one, then every third.
  var dense = LINKS.length > 1200, thin = 1, slow = 0;
  var t0 = performance.now();
  function frame(now) {
    if (!on) return;
    if (!drag && hover < 0 && held < 0 && !still) rotY += 0.0014;
    var before = performance.now();
    draw((now - t0) / 1000);
    slow = performance.now() - before > 24 ? slow + 1 : 0;
    if (slow > 12 && thin < 4) { thin++; slow = 0; }
    if (!still) window.requestAnimationFrame(frame);
  }
  function once() { if (still || !on) draw(0); }
  function pick(e) {
    var b = cv.getBoundingClientRect(), x = e.clientX - b.left, y = e.clientY - b.top, best = -1, reach = e.pointerType === "mouse" ? 12 : 22, bd = reach * reach;
    for (var i = 0; i < N; i++) { var s = Q[i]; if (!s || s[2] <= 0 || !shown(i)) continue; var d = (s[0] - x) * (s[0] - x) + (s[1] - y) * (s[1] - y); if (d < bd) { bd = d; best = i; } }
    return best;
  }
  cv.addEventListener("pointerdown", function (e) { drag = { x: e.clientX, y: e.clientY, ry: rotY, rx: rotX, moved: false }; cv.setPointerCapture(e.pointerId); });
  cv.addEventListener("pointermove", function (e) {
    if (drag) {
      if (Math.abs(e.clientX - drag.x) + Math.abs(e.clientY - drag.y) > 5) drag.moved = true;
      if (drag.moved) { rotY = drag.ry + (e.clientX - drag.x) * 0.006; rotX = Math.max(-1.2, Math.min(1.2, drag.rx + (e.clientY - drag.y) * 0.006)); once(); }
      return;
    }
    if (e.pointerType !== "mouse") return;
    var h = pick(e);
    if (h !== hover) { hover = h; cv.style.cursor = h >= 0 ? "pointer" : "grab"; say(); once(); }
  });
  cv.addEventListener("pointerup", function (e) {
    var moved = drag && drag.moved; drag = null;
    if (moved) return;
    var h = pick(e);
    if (h < 0) { if (held >= 0) { held = -1; say(); once(); } return; }
    // a mouse opens the page at once; a finger names the company first, and opens it on the second tap
    if (e.pointerType === "mouse" || held === h) { window.location.href = encodeURI(CO[h][SLUG]) + "/"; return; }
    held = h; say(); once();
  });
  cv.addEventListener("pointerleave", function () { if (hover >= 0) { hover = -1; cv.style.cursor = "grab"; say(); once(); } });
  // the page's own filters dim the companies they leave out
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-cofilter],[data-comarket]");
    if (!b) return;
    if (b.hasAttribute("data-cofilter")) sectorOn = b.getAttribute("data-cofilter"); else marketOn = b.getAttribute("data-comarket");
    once();
  });
  var lastW = 0;
  window.addEventListener("resize", function () { if (cv.clientWidth !== lastW) { lastW = cv.clientWidth; size(); once(); } });
  new IntersectionObserver(function (en) {
    var vis = en[0].isIntersecting;
    if (vis && !on) { on = true; window.requestAnimationFrame(frame); if (still) draw(0); } else if (!vis) on = false;
  }, { rootMargin: "120px" }).observe(cv);

  box.hidden = false;
  stats.textContent = N.toLocaleString("en-US") + " companies · " + SEC.length + " sectors · " + LINKS.length.toLocaleString("en-US") + " ties · weekly returns, " + D.weeks + " weeks";
  cv.setAttribute("aria-label", "A turning globe of the " + N + " companies below, grouped by sector, with lines between those whose weekly returns move together. Every company is also in the table under it.");
  cv.style.cursor = "grab";
  size(); lastW = cv.clientWidth; say();
  if (document.fonts && document.fonts.load) document.fonts.load("10px " + MONO).then(once);
})();
