/* Andra Markets: the globe on the Companies index (companies/; owner's request, 13 Nov 2026).
   Every company the site follows is a point on a slowly turning sphere, set with its sector;
   a line joins two companies whose weekly returns move together (worked out at build time,
   tools/build_site.py, globe_data). Green and red are the last session's rise or fall.
   Pointing at a company puts a reticle on it, opens its card and leaves only its lines;
   clicking it opens its page. On a touch screen the first tap names the company and the second
   opens it. The table under the globe lists the same companies as links, so nothing here is
   the only way to a page.

   It is dressed as an instrument (owner, 13 Nov 2026: "more larper"): a graduated bezel with
   the heading it is turned to, a sweep that lights the companies it passes, pulses running
   along the ties, a tally for each sector, and a short start-up in which the companies are
   counted in. Every figure on it is real: nothing is written for show.

   Drawn on a 2D canvas. What does not change between frames (bezel, corner blocks) is drawn
   once to a second canvas. It turns only while on screen, stays still under reduced motion,
   and draws fewer lines on a device that cannot keep up. */
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
  var MARKET = { us: "United States", europe: "Europe", asia: "Asia" };

  function pct(bp) { var r = Number((bp / 100).toFixed(2)); return (r > 0 ? "+" : r < 0 ? MINUS : "") + Math.abs(r).toFixed(2) + "%"; }
  function esc(t) { return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function pad(n, w) { n = String(n); while (n.length < w) n = "0" + n; return n; }
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
  for (var q0 = 0; q0 < 14; q0++) cage.push([R0() * Math.PI, R0() * Math.PI]);
  // each link's arc, lifted a little off the surface, as points on the unit sphere
  var ARC = LINKS.map(function (l) {
    var a = P.pts[l[0]], b = P.pts[l[1]], om = Math.acos(Math.max(-1, Math.min(1, a[0] * b[0] + a[1] * b[1] + a[2] * b[2]))), so = Math.sin(om) || 1, out = [], seg = 5 + Math.round(om * 9);
    for (var k = 0; k <= seg; k++) { var t = k / seg, wa = Math.sin((1 - t) * om) / so, wb = Math.sin(t * om) / so, lift = 1 + 0.045 * om * Math.sin(Math.PI * t); out.push([(a[0] * wa + b[0] * wb) * lift, (a[1] * wa + b[1] * wb) * lift, (a[2] * wa + b[2] * wb) * lift]); }
    return out;
  });
  // a speck for each company, hung off the surface: above it on a rise, sunk into it on a fall
  var DUST = CO.map(function (c, i) { var p = P.pts[i], h = 1 + Math.max(-0.05, Math.min(0.09, c[MOVE] / 1e4 * 2.2)); return [p[0] * h, p[1] * h, p[2] * h]; });
  // some ties carry a pulse: the strongest, and never so many that the globe crawls
  var PULSE = LINKS.map(function (l, n) { return n; }).sort(function (a, b) { return LINKS[b][2] - LINKS[a][2]; }).slice(0, Math.min(70, Math.ceil(LINKS.length / 6))).map(function (n) { return [n, R0()]; });
  // each sector's tally of the last session
  var TALLY = SEC.map(function () { return [0, 0]; });
  CO.forEach(function (c) { TALLY[c[SECT]][0]++; if (c[MOVE] > 0) TALLY[c[SECT]][1]++; });
  var UPS = CO.filter(function (c) { return c[MOVE] > 0; }).length, DOWNS = CO.filter(function (c) { return c[MOVE] < 0; }).length;
  var MEAN = CO.reduce(function (t, c) { return t + c[MOVE]; }, 0) / N;

  var S = { w: 0, h: 0, c: null, rad: 0, dpr: 1 }, rotY = 0.6, rotX = -0.28, cosY, sinY, cosX, sinX;
  var hover = -1, held = -1, drag = null, on = false, Q = [], sectorOn = "all", marketOn = "all", layer = null, born = 0;
  function turn() { cosY = Math.cos(rotY); sinY = Math.sin(rotY); cosX = Math.cos(rotX); sinX = Math.sin(rotX); }
  function proj(p) {
    var x = p[0] * cosY + p[2] * sinY, z = -p[0] * sinY + p[2] * cosY, y = p[1] * cosX - z * sinX;
    return [S.cx + x * S.rad, S.cy - y * S.rad, p[1] * sinX + z * cosX];
  }
  function text(c, str, x, y, align, color, size) {
    c.font = "400 " + (size || 10) + "px " + MONO; c.textAlign = align || "left"; c.fillStyle = color;
    if ("letterSpacing" in c) c.letterSpacing = "1px";
    c.fillText(String(str).toUpperCase(), x, y);
  }
  function shown(i) { return (sectorOn === "all" || D.slugs[CO[i][SECT]] === sectorOn) && (marketOn === "all" || CO[i][MKT] === marketOn); }
  var DIM = "rgba(116,121,124,.95)", SOFT = "rgba(163,168,170,.95)", FULL = "rgb(" + INK + ")";

  function size() {
    var dpr = Math.min(window.devicePixelRatio || 1, N > 600 ? 1.5 : 2), w = cv.clientWidth, h = Math.round(Math.min(Math.max(w * 0.6, 380), 760));
    cv.style.height = h + "px"; cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
    S.c = cv.getContext("2d"); S.c.setTransform(dpr, 0, 0, dpr, 0, 0); S.w = w; S.h = h; S.dpr = dpr;
    S.wide = w > 760; S.cx = w / 2; S.cy = h / 2; S.rad = Math.min(w * (S.wide ? 0.3 : 0.4), h * 0.385); S.bez = S.rad * 1.13;
    backdrop();
  }
  /* What never moves: the bezel and the corner blocks, drawn once. */
  function backdrop() {
    layer = document.createElement("canvas"); layer.width = cv.width; layer.height = cv.height;
    var c = layer.getContext("2d"), cx = S.cx, cy = S.cy, k, a, r0;
    c.setTransform(S.dpr, 0, 0, S.dpr, 0, 0);
    // the bezel: a tick a degree and a half, a longer one every fifteen, a figure every thirty
    c.strokeStyle = "rgba(" + INK + ",.16)"; c.lineWidth = 1;
    c.beginPath(); c.arc(cx, cy, S.bez, 0, TAU); c.stroke();
    c.beginPath(); c.arc(cx, cy, S.bez + 14, 0, TAU); c.strokeStyle = "rgba(" + INK + ",.07)"; c.stroke();
    c.beginPath();
    for (k = 0; k < 240; k++) { a = k / 240 * TAU; r0 = S.bez + (k % 10 === 0 ? 9 : k % 5 === 0 ? 6 : 3); c.moveTo(cx + Math.cos(a) * S.bez, cy + Math.sin(a) * S.bez); c.lineTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0); }
    c.strokeStyle = "rgba(" + INK + ",.3)"; c.stroke();
    if (S.wide) for (k = 0; k < 12; k++) { a = k / 12 * TAU - Math.PI / 2; text(c, pad(k * 30, 3), cx + Math.cos(a) * (S.bez + 26), cy + Math.sin(a) * (S.bez + 26) + 3, "center", DIM, 9); }
    // a cross through the middle, broken where the globe is
    c.beginPath(); [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(function (d) { c.moveTo(cx + d[0] * (S.bez + 34), cy + d[1] * (S.bez + 34)); c.lineTo(cx + d[0] * (S.bez + 52), cy + d[1] * (S.bez + 52)); });
    c.strokeStyle = "rgba(" + INK + ",.3)"; c.stroke();
    // brackets in the four corners
    c.beginPath(); [[0, 0, 1, 1], [S.w, 0, -1, 1], [0, S.h, 1, -1], [S.w, S.h, -1, -1]].forEach(function (b) { c.moveTo(b[0] + b[2] * 0.5, b[1] + b[3] * 14); c.lineTo(b[0] + b[2] * 0.5, b[1] + b[3] * 0.5); c.lineTo(b[0] + b[2] * 14, b[1] + b[3] * 0.5); });
    c.strokeStyle = "rgba(" + INK + ",.4)"; c.stroke();
    if (!S.wide) return;
    // top left: what this is
    var x = 18, y = 30;
    text(c, "Andra · company field", x, y, "left", FULL, 10);
    text(c, "Session " + (D.asof || "") + " · close", x, y + 16, "left", SOFT, 9);
    text(c, "Ties: weekly returns · " + D.weeks + " weeks · corr ≥ 0.50", x, y + 30, "left", DIM, 9);
    // top right: the count
    text(c, "Bodies " + pad(N, 4), S.w - 18, y, "right", FULL, 10);
    text(c, "Ties " + pad(LINKS.length, 4) + " · sectors " + pad(SEC.length, 2), S.w - 18, y + 16, "right", SOFT, 9);
    text(c, "Rose " + pad(UPS, 4) + " · fell " + pad(DOWNS, 4) + " · mean " + pct(MEAN), S.w - 18, y + 30, "right", DIM, 9);
    // bottom left: each sector's tally, a bar of how many of its companies rose
    var rows = SEC.map(function (s, g) { return g; }).sort(function (a2, b2) { return TALLY[b2][0] - TALLY[a2][0]; }).slice(0, 11), by = S.h - 22 - rows.length * 13;
    text(c, "Sector · rose / all", x, by - 8, "left", SOFT, 9);
    rows.forEach(function (g, n) {
      var yy = by + 8 + n * 13, t = TALLY[g], bw = 64, share = t[0] ? t[1] / t[0] : 0;
      text(c, SEC[g].slice(0, 13), x, yy, "left", DIM, 9);
      c.fillStyle = "rgba(" + INK + ",.16)"; c.fillRect(x + 118, yy - 6, bw, 3);
      c.fillStyle = "rgb(" + UP + ")"; c.fillRect(x + 118, yy - 6, bw * share, 3);
      text(c, pad(t[1], 3) + "/" + pad(t[0], 3), x + 118 + bw + 8, yy, "left", DIM, 9);
    });
    // bottom right: how to use it
    text(c, "Point · lock on", S.w - 18, S.h - 50, "right", SOFT, 9);
    text(c, "Click · open the company", S.w - 18, S.h - 36, "right", SOFT, 9);
    text(c, "Drag · turn", S.w - 18, S.h - 22, "right", DIM, 9);
  }

  // A slow device draws fewer lines: after a run of long frames, every second one, then every third.
  var dense = LINKS.length > 1200, thin = 1, slow = 0;

  function draw(t) {
    var c = S.c, focus = hover >= 0 ? hover : held, filtered = sectorOn !== "all" || marketOn !== "all", i, k, s;
    turn();
    c.clearRect(0, 0, S.w, S.h);
    if (layer) c.drawImage(layer, 0, 0, S.w, S.h);
    // start-up: the companies are counted in over a second and a half
    var boot = still ? 1 : Math.min(1, (t - born) / 1.5), live = Math.ceil(N * boot);
    // the heading the globe is turned to, as a marker running round the bezel
    var head = ((rotY % TAU) + TAU) % TAU, ha = head - Math.PI / 2;
    c.beginPath(); c.moveTo(S.cx + Math.cos(ha) * (S.bez - 5), S.cy + Math.sin(ha) * (S.bez - 5)); c.lineTo(S.cx + Math.cos(ha) * (S.bez + 14), S.cy + Math.sin(ha) * (S.bez + 14));
    c.strokeStyle = FULL; c.lineWidth = 1.5; c.stroke();
    if (S.wide) text(c, "Hdg " + pad(Math.round(head / TAU * 360) % 360, 3) + "° · tilt " + (rotX < 0 ? MINUS : "+") + pad(Math.abs(Math.round(rotX / Math.PI * 180)), 2) + "°", S.cx, S.cy + S.bez + 44, "center", SOFT, 9);

    c.lineWidth = 1; c.strokeStyle = "rgba(" + INK + ",.07)";
    c.beginPath();
    cage.forEach(function (tl) {
      for (var j = 0; j <= 48; j++) { var a = j / 48 * TAU, x = Math.cos(a), y = Math.sin(a) * Math.cos(tl[0]), z = Math.sin(a) * Math.sin(tl[0]), q = proj([x * Math.cos(tl[1]) + z * Math.sin(tl[1]), y, -x * Math.sin(tl[1]) + z * Math.cos(tl[1])]); if (j) c.lineTo(q[0], q[1]); else c.moveTo(q[0], q[1]); }
    });
    c.stroke();
    c.beginPath(); c.arc(S.cx, S.cy, S.rad, 0, TAU); c.strokeStyle = "rgba(" + INK + ",.45)"; c.stroke();
    Q = P.pts.map(proj);

    // the sweep: a meridian that turns faster than the globe and lights what it passes
    var sw = still ? -9 : (t * 0.55) % TAU;
    function lit(p) { if (sw < 0) return 0; var a = Math.atan2(p[0] * cosY + p[2] * sinY, -p[0] * sinY + p[2] * cosY), d = ((a - sw) % TAU + TAU) % TAU; return d < 0.5 ? 1 - d / 0.5 : 0; }
    if (sw >= 0 && boot >= 1) {
      c.beginPath();
      for (k = 0; k <= 24; k++) { var la = -Math.PI / 2 + k / 24 * Math.PI, x0 = Math.cos(la) * Math.sin(sw), z0 = Math.cos(la) * Math.cos(sw), y0 = Math.sin(la), yy = y0 * cosX - z0 * sinX, zz = y0 * sinX + z0 * cosX; if (zz < 0) continue; c.lineTo(S.cx + x0 * S.rad, S.cy - yy * S.rad); }
      c.strokeStyle = "rgba(" + INK + ",.28)"; c.lineWidth = 1; c.stroke();
    }

    // Lines, stroked a few dozen arcs at a time: one path holding every arc is far slower to fill.
    var groups = { far: [], near: [], own: [] }, counts = { far: 0, near: 0, own: 0 };
    function into(kind, pts) {
      var g = groups[kind];
      if (counts[kind]++ % 28 === 0) g.push(new Path2D());
      var path = g[g.length - 1];
      path.moveTo(pts[0][0], pts[0][1]);
      for (var j = 1; j < pts.length; j++) path.lineTo(pts[j][0], pts[j][1]);
    }
    var seenZ = {};
    for (var n = 0; n < LINKS.length; n++) {
      var l = LINKS[n], isOwn = focus >= 0 && (l[0] === focus || l[1] === focus);
      if (l[0] >= live || l[1] >= live) continue;
      if (!isOwn && (focus >= 0 ? n % 3 : n % thin)) continue;
      if (filtered && !(shown(l[0]) && shown(l[1]))) continue;
      var a = ARC[n], z = 0, pts = [];
      for (k = 0; k < a.length; k++) { s = proj(a[k]); z += s[2]; pts.push(s); }
      var near = z / a.length > 0;
      seenZ[n] = near;
      if (!near && !isOwn && (dense || thin > 1)) continue;  // the far side's lines are the first to go
      into(isOwn ? "own" : near ? "near" : "far", pts);
    }
    function stroke(kind, width, alpha) { c.lineWidth = width; c.strokeStyle = "rgba(" + INK + "," + alpha + ")"; groups[kind].forEach(function (p) { c.stroke(p); }); }
    stroke("far", 0.7, focus >= 0 ? 0.04 : 0.07);
    stroke("near", 0.7, focus >= 0 ? 0.09 : 0.24);
    stroke("own", 1.2, 0.9);
    // pulses along the strongest ties on the near side
    if (!still && boot >= 1) {
      c.fillStyle = FULL;
      PULSE.forEach(function (pl) {
        var n2 = pl[0], l2 = LINKS[n2];
        if (!seenZ[n2] || (focus >= 0 && l2[0] !== focus && l2[1] !== focus)) return;
        var arc = ARC[n2], u = (t * (0.18 + l2[2] / 400) + pl[1]) % 1, f = u * (arc.length - 1), i0 = Math.floor(f), w = f - i0, A = arc[i0], B = arc[Math.min(arc.length - 1, i0 + 1)];
        var q = proj([A[0] + (B[0] - A[0]) * w, A[1] + (B[1] - A[1]) * w, A[2] + (B[2] - A[2]) * w]);
        c.fillRect(q[0] - 1, q[1] - 1, 2, 2);
      });
    }

    // The companies, drawn in a handful of fills: far or near, risen or fallen, bright or dimmed.
    var tied = {};
    if (focus >= 0) mine[focus].forEach(function (n3) { var l3 = LINKS[n3]; tied[l3[0] === focus ? l3[1] : l3[0]] = l3[2]; });
    var bins = {}, halo = { u: new Path2D(), d: new Path2D() }, flare = new Path2D(), stems = { u: new Path2D(), d: new Path2D() };
    for (i = 0; i < live; i++) {
      s = Q[i];
      var front = s[2] > 0, m = CO[i][MOVE], on2 = (!filtered || shown(i)) && (focus < 0 || i === focus || tied[i] != null);
      var r = (i < 60 ? 2.6 : i < 300 ? 2 : 1.5) * (front ? 1 : 0.6) * (i === focus ? 2 : tied[i] != null && focus >= 0 ? 1.4 : 1);
      var key = (front ? "1" : "0") + (m > 0 ? "u" : m < 0 ? "d" : "n") + (on2 ? "1" : "0"), path = bins[key] || (bins[key] = new Path2D());
      path.moveTo(s[0] + r, s[1]); path.arc(s[0], s[1], r, 0, TAU);
      if (front && on2 && m) {
        // a stem to its speck: how far it moved, out of the surface or into it
        var d = proj(DUST[i]), st = stems[m > 0 ? "u" : "d"];
        st.moveTo(s[0], s[1]); st.lineTo(d[0], d[1]);
        if (i < 220 || Math.abs(m) > 250) { var hl = halo[m > 0 ? "u" : "d"]; hl.moveTo(s[0] + r * 3.2, s[1]); hl.arc(s[0], s[1], r * 3.2, 0, TAU); }
        if (lit(P.pts[i]) > 0.55) { flare.moveTo(s[0] + r + 3, s[1]); flare.arc(s[0], s[1], r + 3, 0, TAU); }
      }
    }
    c.lineWidth = 0.8;
    c.strokeStyle = "rgba(" + UP + ",.55)"; c.stroke(stems.u); c.strokeStyle = "rgba(" + DN + ",.55)"; c.stroke(stems.d);
    c.fillStyle = "rgba(" + UP + ",.1)"; c.fill(halo.u); c.fillStyle = "rgba(" + DN + ",.1)"; c.fill(halo.d);
    ["0", "1"].forEach(function (f) { ["n", "d", "u"].forEach(function (dd) { ["0", "1"].forEach(function (lv) {
      var path = bins[f + dd + lv];
      if (!path) return;
      c.fillStyle = "rgba(" + (dd === "u" ? UP : dd === "d" ? DN : INK) + "," + ((f === "1" ? 1 : 0.25) * (lv === "1" ? 1 : filtered ? 0.12 : 0.4)).toFixed(2) + ")"; c.fill(path);
    }); }); });
    c.strokeStyle = "rgba(" + INK + ",.55)"; c.lineWidth = 1; c.stroke(flare);

    // sector names, each with its tally, just off the surface
    if (S.w > 620) P.centre.forEach(function (p, g) {
      s = proj([p[0] * 1.2, p[1] * 1.2, p[2] * 1.2]);
      if (s[2] < -0.15) return;
      var al = s[2] > 0.25 ? 0.95 : 0.45, e = proj([p[0] * 1.03, p[1] * 1.03, p[2] * 1.03]);
      c.beginPath(); c.moveTo(e[0], e[1]); c.lineTo(s[0], s[1]); c.strokeStyle = "rgba(" + INK + "," + (al * 0.3).toFixed(2) + ")"; c.lineWidth = 1; c.stroke();
      text(c, SEC[g], s[0], s[1] - 4, "center", "rgba(163,168,170," + al + ")", 9);
      text(c, pad(TALLY[g][1], 3) + " / " + pad(TALLY[g][0], 3) + " up", s[0], s[1] + 8, "center", "rgba(116,121,124," + al + ")", 8);
    });
    if (boot < 1) { text(c, "Indexing " + pad(live, 4) + " / " + pad(N, 4), S.cx, S.cy + 4, "center", FULL, 11); return; }
    // names: the largest that face us when nothing is in focus; the focus and its companions when one is
    if (focus < 0 && S.w > 620) { for (i = 0; i < Math.min(N, 16); i++) if (Q[i][2] > 0.45 && (!filtered || shown(i))) text(c, CO[i][TICK], Q[i][0] + 7, Q[i][1] + 3, "left", "rgba(163,168,170," + ((Q[i][2] - 0.45) * 1.8).toFixed(2) + ")", 9); }
    if (focus >= 0) reticle(c, focus, tied, t);
  }

  /* Locked on a company: brackets round it, cross-hairs out to the bezel, and its card. */
  function reticle(c, f, tied, t) {
    var p = Q[f], co = CO[f], mv = co[MOVE], breathe = still ? 0 : Math.sin(t * 4) * 1.5, g = 11 + breathe, tk = 5;
    Object.keys(tied).forEach(function (j) { if (Q[j][2] > 0) text(c, CO[j][TICK] + " " + (tied[j] / 100).toFixed(2), Q[j][0] + 8, Q[j][1] + 3, "left", SOFT, 9); });
    c.strokeStyle = FULL; c.lineWidth = 1.2; c.beginPath();
    [[-1, -1], [1, -1], [1, 1], [-1, 1]].forEach(function (d) { c.moveTo(p[0] + d[0] * g, p[1] + d[1] * (g - tk)); c.lineTo(p[0] + d[0] * g, p[1] + d[1] * g); c.lineTo(p[0] + d[0] * (g - tk), p[1] + d[1] * g); });
    c.stroke();
    // cross-hairs from the brackets out to the bezel
    c.beginPath(); c.setLineDash([2, 5]);
    c.moveTo(p[0], p[1] - g - 4); c.lineTo(p[0], S.cy - Math.sqrt(Math.max(0, S.bez * S.bez - (p[0] - S.cx) * (p[0] - S.cx))));
    c.moveTo(p[0] - g - 4, p[1]); c.lineTo(S.cx - Math.sqrt(Math.max(0, S.bez * S.bez - (p[1] - S.cy) * (p[1] - S.cy))), p[1]);
    c.strokeStyle = "rgba(" + INK + ",.4)"; c.lineWidth = 1; c.stroke(); c.setLineDash([]);
    if (!S.wide) { text(c, co[NAME], p[0] + (p[0] > S.w - 170 ? -g - 6 : g + 6), p[1] - 4, p[0] > S.w - 170 ? "right" : "left", FULL, 11); text(c, pct(mv), p[0] + (p[0] > S.w - 170 ? -g - 6 : g + 6), p[1] + 10, p[0] > S.w - 170 ? "right" : "left", "rgb(" + (mv >= 0 ? UP : DN) + ")", 10); return; }
    // the card, on the side with room, joined to the company by a leader
    var right = p[0] < S.cx, cw = 236, x = right ? S.cx + S.bez + 62 : S.cx - S.bez - 62 - cw, ties = mine[f].map(function (n) { var l = LINKS[n]; return [l[0] === f ? l[1] : l[0], l[2]]; }).sort(function (a, b) { return b[1] - a[1]; });
    x = Math.max(18, Math.min(S.w - cw - 18, x));
    var rows = [["Ticker", co[TICK]], ["Sector", SEC[co[SECT]]], ["Market", MARKET[co[MKT]] || co[MKT]], ["Rank", "#" + pad(f + 1, 4) + " of " + N], ["Ties", pad(ties.length, 2)]];
    var ch = 74 + rows.length * 14 + (ties.length ? 22 + Math.min(4, ties.length) * 14 : 0), y = Math.max(86, Math.min(S.h - ch - 70, p[1] - ch / 2));
    c.beginPath(); c.moveTo(p[0] + (right ? g + 4 : -g - 4), p[1]); c.lineTo(right ? x - 14 : x + cw + 14, y + 20); c.lineTo(right ? x : x + cw, y + 20); c.strokeStyle = "rgba(" + INK + ",.55)"; c.stroke();
    c.beginPath(); c.moveTo(x, y + 6); c.lineTo(x, y); c.lineTo(x + cw, y); c.lineTo(x + cw, y + 6); c.moveTo(x, y + ch - 6); c.lineTo(x, y + ch); c.lineTo(x + cw, y + ch); c.lineTo(x + cw, y + ch - 6); c.strokeStyle = "rgba(" + INK + ",.4)"; c.stroke();
    text(c, "Locked · " + pad(f + 1, 4), x + 10, y + 16, "left", DIM, 9);
    c.font = "300 20px Geist, sans-serif"; c.textAlign = "left"; c.fillStyle = FULL; if ("letterSpacing" in c) c.letterSpacing = "-0.4px";
    var nm = co[NAME]; while (c.measureText(nm).width > cw - 20 && nm.length > 4) nm = nm.slice(0, -2); c.fillText(nm === co[NAME] ? nm : nm + "…", x + 10, y + 42);
    text(c, pct(mv), x + 10, y + 60, "left", "rgb(" + (mv >= 0 ? UP : DN) + ")", 12);
    text(c, "last session", x + 10 + 78, y + 60, "left", DIM, 9);
    rows.forEach(function (r, n) { var yy = y + 80 + n * 14; text(c, r[0], x + 10, yy, "left", DIM, 9); text(c, r[1], x + cw - 10, yy, "right", SOFT, 9); });
    if (ties.length) {
      var ty = y + 80 + rows.length * 14 + 10;
      text(c, "Moves with", x + 10, ty, "left", DIM, 9);
      ties.slice(0, 4).forEach(function (tt, n) { var yy = ty + 14 + n * 14; text(c, CO[tt[0]][TICK], x + 10, yy, "left", SOFT, 9); c.fillStyle = "rgba(" + INK + ",.16)"; c.fillRect(x + 74, yy - 5, 96, 2); c.fillStyle = FULL; c.fillRect(x + 74, yy - 5, 96 * tt[1] / 100, 2); text(c, (tt[1] / 100).toFixed(2), x + cw - 10, yy, "right", SOFT, 9); });
    }
    text(c, "Click to open →", x + 10, y + ch + 16, "left", FULL, 9);
  }

  function say() {
    var f = hover >= 0 ? hover : held;
    if (f < 0) { read.innerHTML = "Last session · <b>" + UPS + "</b> rose · <b>" + DOWNS + "</b> fell · point at a company, click to open its page"; return; }
    var c = CO[f], ties = mine[f].map(function (n) { var l = LINKS[n]; return [l[0] === f ? l[1] : l[0], l[2]]; }).sort(function (a, b) { return b[1] - a[1]; });
    read.innerHTML = "<b>" + esc(c[NAME]) + "</b> · " + esc(SEC[c[SECT]]) + ' · <span class="mv ' + (c[MOVE] >= 0 ? "mv--up" : "mv--down") + '">' + pct(c[MOVE]) + "</span>" +
      (ties.length ? " · moves with " + ties.slice(0, 4).map(function (x) { return esc(CO[x[0]][TICK]) + " " + (x[1] / 100).toFixed(2); }).join(", ") : " · no close companion") +
      (held === f && hover < 0 ? ' · <a href="' + encodeURI(c[SLUG]) + '/">Open its page</a>' : "");
  }

  var t0 = performance.now(), clock = 0;
  function frame(now) {
    if (!on) return;
    clock = (now - t0) / 1000;
    if (!drag && hover < 0 && held < 0 && !still) rotY += 0.0014;
    var before = performance.now();
    draw(clock);
    slow = performance.now() - before > 24 ? slow + 1 : 0;
    if (slow > 12 && thin < 4) { thin++; slow = 0; }
    if (!still) window.requestAnimationFrame(frame);
  }
  function once() { if (still || !on) draw(clock); }
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
    if (vis && !on) { on = true; if (!born) born = (performance.now() - t0) / 1000; window.requestAnimationFrame(frame); if (still) draw(0); } else if (!vis) on = false;
  }, { rootMargin: "60px" }).observe(cv);

  box.hidden = false;
  stats.textContent = N.toLocaleString("en-US") + " companies · " + SEC.length + " sectors · " + LINKS.length.toLocaleString("en-US") + " ties · weekly returns, " + D.weeks + " weeks";
  cv.setAttribute("aria-label", "A turning globe of the " + N + " companies below, grouped by sector, with lines between those whose weekly returns move together. " + UPS + " rose and " + DOWNS + " fell in the last session. Every company is also in the table under it.");
  cv.style.cursor = "grab";
  size(); lastW = cv.clientWidth; say();
  if (document.fonts && document.fonts.load) document.fonts.load("10px " + MONO).then(function () { backdrop(); once(); });
})();
