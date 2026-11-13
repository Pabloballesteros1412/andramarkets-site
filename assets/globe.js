/* Andra Markets: the globe on the Companies index (companies/; owner's request, 13 Nov 2026).
   Every company the site follows is a point of light on a slowly turning globe, set with its
   sector; an arc joins two companies whose weekly returns move together (worked out at build
   time, tools/build_site.py, globe_data). Green and red are the last session's rise or fall.
   Pointing at a company names it and leaves only its arcs; clicking it opens its page. On a
   touch screen the first tap names the company and the second opens it. The table under the
   globe lists the same companies as links, so nothing here is the only way to a page.

   It is drawn as a solid body, not a wire ball: the far side is hidden, the surface carries a
   fine grid of meridians and parallels that fades towards the limb, the limb has a thin bright
   edge and a soft halo, each company is a small core inside a glow, and the arcs rise off the
   surface the further they have to go. No text on it but the sector names and what the pointer
   is on (owner, 13 Nov 2026: the globe itself must carry it, not decoration round it).

   A 2D canvas. The glows are small sprites drawn once; lines are stroked in small groups. It
   turns only while on screen, stays still under reduced motion, and draws fewer arcs on a
   device that cannot keep up. */
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
  var R0 = rng(7);
  // Each tie as an arc that rises off the surface, higher the further apart its two ends are.
  var ARC = LINKS.map(function (l) {
    var a = P.pts[l[0]], b = P.pts[l[1]], om = Math.acos(Math.max(-1, Math.min(1, a[0] * b[0] + a[1] * b[1] + a[2] * b[2]))), so = Math.sin(om) || 1, out = [], seg = 8 + Math.round(om * 14);
    for (var k = 0; k <= seg; k++) { var t = k / seg, wa = Math.sin((1 - t) * om) / so, wb = Math.sin(t * om) / so, lift = 1 + Math.min(0.17, 0.02 + 0.13 * om) * Math.sin(Math.PI * t); out.push([(a[0] * wa + b[0] * wb) * lift, (a[1] * wa + b[1] * wb) * lift, (a[2] * wa + b[2] * wb) * lift]); }
    return out;
  });
  // The grid: a meridian and a parallel every fifteen degrees, as short runs of points.
  var GRID = [];
  (function () {
    var k, a, b;
    for (k = 0; k < 24; k++) { a = k / 24 * TAU; var m = []; for (b = -84; b <= 84; b += 4) { var la = b / 180 * Math.PI; m.push([Math.cos(la) * Math.cos(a), Math.sin(la), Math.cos(la) * Math.sin(a)]); } GRID.push(m); }
    for (k = -5; k <= 5; k++) { var lat = k * 15 / 180 * Math.PI, p = []; for (b = 0; b <= 360; b += 4) { var lo = b / 180 * Math.PI; p.push([Math.cos(lat) * Math.cos(lo), Math.sin(lat), Math.cos(lat) * Math.sin(lo)]); } GRID.push(p); }
  })();
  // A scatter of faint motes just above the surface, thicker where a sector's companies moved most.
  var MOTES = [];
  CO.forEach(function (c, i) {
    var p = P.pts[i], m = Math.min(1, Math.abs(c[MOVE]) / 400), count = 1 + Math.round(m * 5);
    for (var k = 0; k < count; k++) { var u = norm(cross(p, [R0() - 0.5, R0() - 0.5, R0() - 0.5])), sp = (0.015 + R0() * 0.055) * (0.6 + m), h = 1.005 + R0() * 0.05 * (0.4 + m); MOTES.push([(p[0] + u[0] * sp) * h, (p[1] + u[1] * sp) * h, (p[2] + u[2] * sp) * h]); }
  });
  var PULSE = LINKS.map(function (l, n) { return n; }).sort(function (a, b) { return LINKS[b][2] - LINKS[a][2]; }).slice(0, Math.min(50, Math.ceil(LINKS.length / 10))).map(function (n) { return [n, R0()]; });
  var UPS = CO.filter(function (c) { return c[MOVE] > 0; }).length, DOWNS = CO.filter(function (c) { return c[MOVE] < 0; }).length;

  var S = { w: 0, h: 0, c: null, rad: 0 }, rotY = 0.6, rotX = -0.3, cosY, sinY, cosX, sinX, PERSP = 0.2;
  var hover = -1, held = -1, drag = null, on = false, Q = [], sectorOn = "all", marketOn = "all", sprites = null, shell = null, born = -1;
  function turn() { cosY = Math.cos(rotY); sinY = Math.sin(rotY); cosX = Math.cos(rotX); sinX = Math.sin(rotX); }
  // To the screen, with a little perspective: what faces us is slightly larger. [x, y, depth, scale]
  function proj(p) {
    var x = p[0] * cosY + p[2] * sinY, z = -p[0] * sinY + p[2] * cosY, y = p[1] * cosX - z * sinX, zz = p[1] * sinX + z * cosX, f = 1 / (1 + PERSP - zz * PERSP);
    return [S.cx + x * S.rad * f, S.cy - y * S.rad * f, zz, f];
  }
  // What is on the far side is not drawn: an arc that goes over the edge ends at the edge.
  function hidden(s) { return s[2] < -0.04; }
  function label(text, x, y, align, color, size) {
    var c = S.c;
    c.font = "400 " + (size || 10) + "px " + MONO; c.textAlign = align || "left"; c.fillStyle = color;
    if ("letterSpacing" in c) c.letterSpacing = "1px";
    c.fillText(String(text).toUpperCase(), x, y);
  }
  function shown(i) { return (sectorOn === "all" || D.slugs[CO[i][SECT]] === sectorOn) && (marketOn === "all" || CO[i][MKT] === marketOn); }

  function sprite(rgb) {
    var el = document.createElement("canvas"), n = 64; el.width = el.height = n;
    var c = el.getContext("2d"), g = c.createRadialGradient(n / 2, n / 2, 0, n / 2, n / 2, n / 2);
    g.addColorStop(0, "rgba(" + rgb + ",.95)"); g.addColorStop(0.12, "rgba(" + rgb + ",.5)"); g.addColorStop(0.4, "rgba(" + rgb + ",.12)"); g.addColorStop(1, "rgba(" + rgb + ",0)");
    c.fillStyle = g; c.fillRect(0, 0, n, n);
    return el;
  }
  function size() {
    var dpr = Math.min(window.devicePixelRatio || 1, N > 600 ? 1.5 : 2), w = cv.clientWidth, h = Math.round(Math.min(Math.max(w * 0.6, 380), 760));
    cv.style.height = h + "px"; cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
    S.c = cv.getContext("2d"); S.c.setTransform(dpr, 0, 0, dpr, 0, 0); S.w = w; S.h = h; S.dpr = dpr;
    S.cx = w / 2; S.cy = h / 2 + 4; S.rad = Math.min(w * 0.46, h * 0.44) * (1 + PERSP) * 0.9;
    // where the globe's edge falls on the screen, given the perspective
    S.limb = S.rad / Math.sqrt((1 + PERSP) * (1 + PERSP) - PERSP * PERSP);
    if (!sprites) sprites = { u: sprite(UP), d: sprite(DN), n: sprite(INK) };
    // The body of the globe, drawn once: a halo, a dark disc lit from the upper left, a bright edge.
    shell = document.createElement("canvas"); shell.width = cv.width; shell.height = cv.height;
    var c = shell.getContext("2d"), R = S.limb, g;
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    g = c.createRadialGradient(S.cx, S.cy, R * 0.92, S.cx, S.cy, R * 1.42);
    g.addColorStop(0, "rgba(" + INK + ",.2)"); g.addColorStop(0.2, "rgba(" + INK + ",.07)"); g.addColorStop(1, "rgba(" + INK + ",0)");
    c.fillStyle = g; c.beginPath(); c.arc(S.cx, S.cy, R * 1.42, 0, TAU); c.fill();
    c.fillStyle = "#000"; c.beginPath(); c.arc(S.cx, S.cy, R, 0, TAU); c.fill();
    g = c.createRadialGradient(S.cx - R * 0.42, S.cy - R * 0.46, R * 0.05, S.cx - R * 0.1, S.cy - R * 0.1, R * 1.05);
    g.addColorStop(0, "rgba(" + INK + ",.11)"); g.addColorStop(0.55, "rgba(" + INK + ",.03)"); g.addColorStop(1, "rgba(" + INK + ",0)");
    c.fillStyle = g; c.beginPath(); c.arc(S.cx, S.cy, R, 0, TAU); c.fill();
    // the inside of the edge glows a little, as an atmosphere seen edge-on
    g = c.createRadialGradient(S.cx, S.cy, R * 0.8, S.cx, S.cy, R);
    g.addColorStop(0, "rgba(" + INK + ",0)"); g.addColorStop(1, "rgba(" + INK + ",.13)");
    c.fillStyle = g; c.beginPath(); c.arc(S.cx, S.cy, R, 0, TAU); c.fill();
    g = c.createLinearGradient(S.cx - R, S.cy - R, S.cx + R, S.cy + R);
    g.addColorStop(0, "rgba(" + INK + ",.95)"); g.addColorStop(0.5, "rgba(" + INK + ",.4)"); g.addColorStop(1, "rgba(" + INK + ",.14)");
    c.strokeStyle = g; c.lineWidth = 1; c.beginPath(); c.arc(S.cx, S.cy, R, 0, TAU); c.stroke();
  }

  // A slow device draws fewer arcs: after a run of long frames, every second one, then every third.
  var thin = 1, slow = 0;

  function draw(t) {
    var c = S.c, focus = hover >= 0 ? hover : held, filtered = sectorOn !== "all" || marketOn !== "all", i, k, s;
    var rise = still || born < 0 ? 1 : Math.min(1, (t - born) / 1.4), ease = 1 - Math.pow(1 - rise, 3);
    turn();
    c.clearRect(0, 0, S.w, S.h);
    c.globalAlpha = ease;
    c.drawImage(shell, 0, 0, S.w, S.h);

    // the grid, in three strokes by depth: it thins out towards the limb as a real sphere's does
    var gp = [new Path2D(), new Path2D(), new Path2D()];
    GRID.forEach(function (line) {
      var prev = null;
      for (var j = 0; j < line.length; j++) { var q = proj(line[j]); if (q[2] > 0.02 && prev && prev[2] > 0.02) { var b = gp[q[2] > 0.66 ? 2 : q[2] > 0.33 ? 1 : 0]; b.moveTo(prev[0], prev[1]); b.lineTo(q[0], q[1]); } prev = q; }
    });
    c.lineWidth = 0.6;
    [0.07, 0.12, 0.17].forEach(function (a, n) { c.strokeStyle = "rgba(" + INK + "," + a + ")"; c.stroke(gp[n]); });

    Q = P.pts.map(proj);
    var mNear = new Path2D(), mEdge = new Path2D();
    for (i = 0; i < MOTES.length; i++) { s = proj(MOTES[i]); if (hidden(s)) continue; (s[2] > 0.3 ? mNear : mEdge).rect(s[0], s[1], 1.1, 1.1); }
    c.fillStyle = "rgba(" + INK + ",.28)"; c.fill(mEdge);
    c.fillStyle = "rgba(" + INK + "," + (focus >= 0 ? 0.3 : 0.6) + ")"; c.fill(mNear);

    // The arcs. Only what is not behind the globe; added to what is under them, so crossings glow.
    var groups = { soft: [], firm: [], own: [] }, counts = { soft: 0, firm: 0, own: 0 };
    function into(kind) { var g = groups[kind]; if (counts[kind]++ % 24 === 0) g.push(new Path2D()); return g[g.length - 1]; }
    var grown = Math.max(0, (rise - 0.25) / 0.75);
    for (var n = 0; n < LINKS.length; n++) {
      var l = LINKS[n], isOwn = focus >= 0 && (l[0] === focus || l[1] === focus);
      if (!isOwn && (focus >= 0 ? n % 3 : n % thin)) continue;
      if (filtered && !(shown(l[0]) && shown(l[1]))) continue;
      var a = ARC[n], upto = Math.max(1, Math.round((a.length - 1) * grown)), path = null, prev = null;
      for (k = 0; k <= upto; k++) {
        s = proj(a[k]);
        if (hidden(s)) { prev = null; continue; }
        if (!path) path = into(isOwn ? "own" : l[2] >= 65 ? "firm" : "soft");
        if (prev) path.lineTo(s[0], s[1]); else path.moveTo(s[0], s[1]);
        prev = s;
      }
    }
    c.globalCompositeOperation = "lighter";
    function stroke(kind, width, alpha) { c.lineWidth = width; c.strokeStyle = "rgba(" + INK + "," + alpha + ")"; groups[kind].forEach(function (p) { c.stroke(p); }); }
    stroke("soft", 0.6, focus >= 0 ? 0.05 : 0.16);
    stroke("firm", 0.7, focus >= 0 ? 0.08 : 0.34);
    stroke("own", 3, 0.16); stroke("own", 1.1, 0.95);
    if (!still && rise >= 1) {
      PULSE.forEach(function (pl) {
        var l2 = LINKS[pl[0]];
        if (focus >= 0 && l2[0] !== focus && l2[1] !== focus) return;
        var arc = ARC[pl[0]], u = (t * (0.14 + l2[2] / 600) + pl[1]) % 1, f = u * (arc.length - 1), i0 = Math.floor(f), w = f - i0, A = arc[i0], B = arc[Math.min(arc.length - 1, i0 + 1)];
        var q = proj([A[0] + (B[0] - A[0]) * w, A[1] + (B[1] - A[1]) * w, A[2] + (B[2] - A[2]) * w]);
        if (!hidden(q)) c.drawImage(sprites.n, q[0] - 5, q[1] - 5, 10, 10);
      });
    }

    // The companies on the near side: a glow, then a core. Largest and nearest are brightest.
    var tied = {};
    if (focus >= 0) mine[focus].forEach(function (n3) { var l3 = LINKS[n3]; tied[l3[0] === focus ? l3[1] : l3[0]] = l3[2]; });
    var cores = { u: [new Path2D(), new Path2D()], d: [new Path2D(), new Path2D()], n: [new Path2D(), new Path2D()] };
    for (i = 0; i < N; i++) {
      s = Q[i];
      if (s[2] <= 0.02) continue;
      var m = CO[i][MOVE], kind = m > 0 ? "u" : m < 0 ? "d" : "n", lit = (!filtered || shown(i)) && (focus < 0 || i === focus || tied[i] != null);
      var depth = 0.45 + 0.55 * s[2], base = (i < 40 ? 2.5 : i < 250 ? 1.9 : 1.4) * s[3] * (1 + PERSP), r = base * (i === focus ? 1.9 : tied[i] != null && focus >= 0 ? 1.35 : 1);
      if (lit && (thin < 3 || i < 250)) { var gr = r * (i < 40 ? 7 : 5.2) * depth; c.globalAlpha = ease * depth * (focus >= 0 && i !== focus ? 0.8 : 0.7); c.drawImage(sprites[kind], s[0] - gr, s[1] - gr, gr * 2, gr * 2); }
      var core = cores[kind][lit ? 1 : 0]; core.moveTo(s[0] + r, s[1]); core.arc(s[0], s[1], r, 0, TAU);
    }
    c.globalAlpha = ease;
    c.globalCompositeOperation = "source-over";
    [["n", INK], ["d", DN], ["u", UP]].forEach(function (kc) {
      c.fillStyle = "rgba(" + kc[1] + "," + (filtered ? 0.12 : 0.5) + ")"; c.fill(cores[kc[0]][0]);
      c.fillStyle = "rgb(" + kc[1] + ")"; c.fill(cores[kc[0]][1]);
    });

    // sector names, just off the surface, where they face us
    if (S.w > 620) P.centre.forEach(function (p, g) {
      s = proj([p[0] * 1.02, p[1] * 1.02, p[2] * 1.02]);
      if (s[2] < 0.12) return;
      var out = proj([p[0] * 1.22, p[1] * 1.22, p[2] * 1.22]), al = Math.min(1, (s[2] - 0.12) * 2.2);
      c.beginPath(); c.moveTo(s[0], s[1]); c.lineTo(out[0], out[1]); c.strokeStyle = "rgba(" + INK + "," + (al * 0.28).toFixed(2) + ")"; c.lineWidth = 1; c.stroke();
      label(SEC[g], out[0], out[1] - 5, "center", "rgba(163,168,170," + (al * 0.95).toFixed(2) + ")", 9);
    });
    if (focus >= 0 && Q[focus][2] > 0) {
      Object.keys(tied).forEach(function (j) { if (Q[j][2] > 0.05) label(CO[j][TICK], Q[j][0] + 8, Q[j][1] + 3, "left", "rgba(163,168,170,.95)", 9); });
      var f = Q[focus], mv = CO[focus][MOVE], right = f[0] > S.w - 240;
      c.beginPath(); c.arc(f[0], f[1], 11 + (still ? 0 : Math.sin(t * 3) * 1.5), 0, TAU); c.strokeStyle = "rgba(" + INK + ",.9)"; c.lineWidth = 1; c.stroke();
      c.font = "300 20px Geist, sans-serif"; c.textAlign = right ? "right" : "left"; c.fillStyle = "rgb(" + INK + ")"; if ("letterSpacing" in c) c.letterSpacing = "-0.3px";
      c.fillText(CO[focus][NAME], f[0] + (right ? -20 : 20), f[1] - 2);
      label(pct(mv) + " · " + SEC[CO[focus][SECT]], f[0] + (right ? -20 : 20), f[1] + 15, right ? "right" : "left", "rgb(" + (mv >= 0 ? UP : DN) + ")", 10);
    }
    c.globalAlpha = 1;
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
    if (born < 0) born = clock;
    if (!drag && hover < 0 && held < 0 && !still) rotY += 0.0013;
    var before = performance.now();
    draw(clock);
    slow = performance.now() - before > 24 ? slow + 1 : 0;
    if (slow > 12 && thin < 4) { thin++; slow = 0; }
    if (!still) window.requestAnimationFrame(frame);
  }
  function once() { if (still || !on) draw(clock); }
  function pick(e) {
    var b = cv.getBoundingClientRect(), x = e.clientX - b.left, y = e.clientY - b.top, best = -1, reach = e.pointerType === "mouse" ? 12 : 22, bd = reach * reach;
    for (var i = 0; i < N; i++) { var s = Q[i]; if (!s || s[2] <= 0.02 || !shown(i)) continue; var d = (s[0] - x) * (s[0] - x) + (s[1] - y) * (s[1] - y); if (d < bd) { bd = d; best = i; } }
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
  }, { rootMargin: "60px" }).observe(cv);

  box.hidden = false;
  stats.textContent = N.toLocaleString("en-US") + " companies · " + SEC.length + " sectors · " + LINKS.length.toLocaleString("en-US") + " ties · weekly returns, " + D.weeks + " weeks";
  cv.setAttribute("aria-label", "A turning globe of the " + N + " companies below, grouped by sector, with arcs between those whose weekly returns move together. " + UPS + " rose and " + DOWNS + " fell in the last session. Every company is also in the table under it.");
  cv.style.cursor = "grab";
  size(); lastW = cv.clientWidth; say();
  if (document.fonts && document.fonts.load) document.fonts.load("10px " + MONO).then(once);
})();
