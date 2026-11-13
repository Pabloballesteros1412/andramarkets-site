/* Andra Markets: lenses, the tools' figures drawn as fields of fine lines (owner-approved
   preview, 13 Nov 2026). Thousands of thin white strands on the black ground, laid over one
   another so that density reads as brightness, with small monospaced read-outs. Used by the
   portfolio analyser (assets/portfolio.js) and Your fund (assets/fund.js).

     AndraLens.weave(canvas, { returns, steps, block, unit })  possible paths of a portfolio
     AndraLens.ring(canvas, { names, notes, matrix, onHover }) how holdings move together

   Both draw on a 2D canvas at the device's pixel ratio (2 at most), redraw when their width
   changes, and draw in one pass under reduced motion. Each returns what it measured, so the
   page can say it in words beside the picture: the canvas itself is an image to a screen reader. */
(function () {
  "use strict";
  var TAU = Math.PI * 2, MINUS = "−";
  var INK = "242,243,243", UP = "#1fd27a", DOWN = "#ff4b52";
  var MONO = '"Geist Mono", ui-monospace, "SFMono-Regular", Menlo, monospace';
  var still = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // A small seeded generator: the same portfolio draws the same picture every time.
  function rng(seed) {
    var s = seed >>> 0;
    return function () {
      s = (s + 0x6D2B79F5) >>> 0;
      var t = Math.imul(s ^ (s >>> 15), 1 | s);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function seedOf(a) {
    var h = 2166136261;
    for (var i = 0; i < a.length; i++) h = Math.imul(h ^ Math.round(a[i] * 1e6), 16777619);
    return h >>> 0;
  }
  function pct(v, dec) {
    var r = Number((v * 100).toFixed(dec));
    return (r > 0 ? "+" : r < 0 ? MINUS : "") + Math.abs(r).toFixed(dec) + "%";
  }
  function fit(cv, h) {
    var dpr = Math.min(window.devicePixelRatio || 1, 2), w = cv.clientWidth;
    cv.style.height = h + "px";
    cv.width = Math.round(w * dpr);
    cv.height = Math.round(h * dpr);
    var c = cv.getContext("2d");
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { c: c, w: w, h: h };
  }
  // A read-out on the canvas: small capitals in the monospaced face, letters set apart.
  function label(c, text, x, y, align, color) {
    c.font = "400 10px " + MONO;
    c.textAlign = align || "left";
    c.fillStyle = color || "rgba(163,168,170,.95)";
    if ("letterSpacing" in c) c.letterSpacing = "1.2px";
    c.fillText(String(text).toUpperCase(), x, y);
  }
  // Redraw when the canvas changes width, and once the monospaced face has loaded.
  // A canvas is drawn again and again as the inputs change: it keeps one listener and its latest picture.
  function keep(cv, draw) {
    cv.__lens = draw;
    if (cv.__kept) return;
    cv.__kept = true;
    var last = cv.clientWidth;
    window.addEventListener("resize", function () {
      if (cv.clientWidth !== last) { last = cv.clientWidth; cv.__lens(); }
    });
    if (document.fonts && document.fonts.load) document.fonts.load("10px " + MONO).then(function () { if (cv.isConnected) cv.__lens(); });
  }

  /* Possible paths: the past returns reshuffled in blocks, each path one strand ---------- */

  function weave(cv, o) {
    var ret = o.returns, steps = o.steps, block = o.block, N = o.paths || 1600;
    var R = rng(seedOf(ret)), every = Math.max(1, Math.round(steps / 84)), pts = Math.floor(steps / every);
    var paths = [], ends = [];
    for (var p = 0; p < N; p++) {
      var v = 100, a = new Float32Array(pts + 1), k = 0, s = 0;
      a[0] = 100;
      while (s < steps) {
        var at = Math.floor(R() * (ret.length - block + 1));
        for (var b = 0; b < block && s < steps; b++) {
          v *= 1 + ret[at + b];
          if (v < 0.01) v = 0.01;
          s++;
          if (s % every === 0 && k < pts) a[++k] = v;
        }
      }
      paths.push(a);
      ends.push(a[pts]);
    }
    var order = ends.map(function (_, i) { return i; }).sort(function (x, y) { return ends[x] - ends[y]; });
    function q(f) { return order[Math.min(N - 1, Math.max(0, Math.floor(f * N)))]; }
    var i5 = q(0.05), i50 = q(0.5), i95 = q(0.95);
    var out = { paths: N, p5: ends[i5] / 100 - 1, p50: ends[i50] / 100 - 1, p95: ends[i95] / 100 - 1,
      lower: ends.filter(function (e) { return e < 100; }).length / N };
    function draw() {
      var w = cv.clientWidth;
      if (!w) return;
      var S = fit(cv, Math.round(Math.min(Math.max(w * 0.44, 260), 500))), c = S.c, mine = cv.__run = (cv.__run || 0) + 1;
      var side = w < 560 ? 86 : 132, L = 40, T = 14, B = 26;
      var lo = Math.max(ends[q(0.004)] * 0.96, 1), hi = ends[q(0.996)] * 1.04;
      var X = function (i) { return L + i / pts * (S.w - L - side); };
      var Y = function (val) { return T + (Math.log(hi) - Math.log(val)) / (Math.log(hi) - Math.log(lo)) * (S.h - T - B); };
      function strand(a) {
        c.beginPath();
        c.moveTo(X(0), Y(a[0]));
        for (var i = 1; i < a.length; i++) c.lineTo(X(i), Y(Math.min(Math.max(a[i], lo), hi)));
        c.stroke();
      }
      c.clearRect(0, 0, S.w, S.h);
      [25, 50, 75, 100, 125, 150, 200, 300, 500].forEach(function (g) {
        if (g !== 100 && (g < lo * 1.05 || g > hi * 0.95)) return;
        c.beginPath(); c.moveTo(L, Y(g)); c.lineTo(S.w - side, Y(g));
        c.strokeStyle = "rgba(" + INK + "," + (g === 100 ? 0.24 : 0.07) + ")"; c.lineWidth = 1; c.stroke();
        label(c, g, L - 8, Y(g) + 3, "right", "rgba(116,121,124,.95)");
      });
      (o.ticks || []).forEach(function (t, i, all) {
        label(c, t, X(i / (all.length - 1) * pts), S.h - 6, i === 0 ? "left" : i === all.length - 1 ? "right" : "center", "rgba(116,121,124,.95)");
      });
      var done = 0;
      (function frame() {
        if (mine !== cv.__run) return;
        c.globalCompositeOperation = "lighter";
        c.lineWidth = 0.7;
        c.strokeStyle = "rgba(" + INK + ",.05)";
        for (var n = 0; n < (still ? N : 48) && done < N; n++) strand(paths[done++]);
        c.globalCompositeOperation = "source-over";
        if (done < N) { window.requestAnimationFrame(frame); return; }
        c.lineWidth = 1; c.strokeStyle = "rgba(" + INK + ",.6)"; c.setLineDash([2, 4]);
        strand(paths[i5]); strand(paths[i95]);
        c.setLineDash([]); c.lineWidth = 1.6; c.strokeStyle = "rgb(" + INK + ")";
        strand(paths[i50]);
        [[i95, "1 in 20 above"], [i50, "Middle"], [i5, "1 in 20 below"]].forEach(function (m) {
          var e = ends[m[0]], x = X(pts), y = Y(Math.min(Math.max(e, lo), hi));
          c.beginPath(); c.arc(x, y, 2.5, 0, TAU); c.fillStyle = "rgb(" + INK + ")"; c.fill();
          label(c, m[1], x + 10, y - 3);
          label(c, e.toFixed(0) + " · " + pct(e / 100 - 1, 0), x + 10, y + 10, "left", e >= 100 ? UP : DOWN);
        });
      })();
    }
    draw();
    keep(cv, draw);
    return out;
  }

  /* A ring of holdings: each pair joined by a band of strands as thick as its correlation -- */

  function ring(cv, o) {
    var n = o.names.length, pairs = [], hover = -1, S = null, rad = 0;
    for (var i = 0; i < n; i++) for (var j = i + 1; j < n; j++) pairs.push([i, j, o.matrix[i][j]]);
    pairs.sort(function (a, b) { return b[2] - a[2]; });
    function pos(k, r) {
      var a = -Math.PI / 2 + k / n * TAU;
      return [S.w / 2 + Math.cos(a) * r, S.h / 2 + Math.sin(a) * r, a];
    }
    function draw() {
      var w = cv.clientWidth;
      if (!w) return;
      S = fit(cv, Math.round(Math.min(Math.max(w * 0.62, 320), 560)));
      var c = S.c, R = rng(23 + n);
      rad = Math.min(S.w - 150, S.h - 84) / 2;
      c.clearRect(0, 0, S.w, S.h);
      c.beginPath(); c.arc(S.w / 2, S.h / 2, rad, 0, TAU);
      c.strokeStyle = "rgba(" + INK + ",.14)"; c.lineWidth = 1; c.stroke();
      c.globalCompositeOperation = "lighter";
      c.lineWidth = 0.7;
      c.strokeStyle = "rgba(" + INK + "," + (hover >= 0 ? 0.14 : 0.09) + ")";
      // fewer strands for each pair as the ring fills, so twelve holdings do not turn solid
      var scale = 260 * Math.min(1, 45 / Math.max(pairs.length, 1) + 0.35);
      pairs.forEach(function (p) {
        if (p[2] <= 0.05 || (hover >= 0 && p[0] !== hover && p[1] !== hover)) return;
        var strands = Math.round(Math.pow(p[2], 1.15) * scale), a = pos(p[0], rad)[2], b = pos(p[1], rad)[2];
        var spread = Math.min(0.05 + p[2] * 0.09, Math.PI / n * 0.8);
        for (var k = 0; k < strands; k++) {
          var ja = a + (R() - 0.5) * spread * 2, jb = b + (R() - 0.5) * spread * 2, pull = 0.1 + R() * 0.5;
          c.beginPath();
          c.moveTo(S.w / 2 + Math.cos(ja) * rad, S.h / 2 + Math.sin(ja) * rad);
          c.quadraticCurveTo(S.w / 2 + (Math.cos(ja) + Math.cos(jb)) * rad * pull * 0.5, S.h / 2 + (Math.sin(ja) + Math.sin(jb)) * rad * pull * 0.5,
            S.w / 2 + Math.cos(jb) * rad, S.h / 2 + Math.sin(jb) * rad);
          c.stroke();
        }
      });
      c.globalCompositeOperation = "source-over";
      o.names.forEach(function (name, k) {
        var p = pos(k, rad), t = pos(k, rad + 16), right = Math.cos(p[2]) > 0.2, left = Math.cos(p[2]) < -0.2;
        var align = right ? "left" : left ? "right" : "center", up = Math.sin(p[2]) < -0.7 ? -14 : 0;
        c.beginPath(); c.arc(p[0], p[1], k === hover ? 4 : 2.6, 0, TAU); c.fillStyle = "rgb(" + INK + ")"; c.fill();
        label(c, name, t[0], t[1] + 3 + up, align, k === hover ? "rgb(" + INK + ")" : "rgba(163,168,170,.95)");
        if (o.notes) label(c, o.notes[k], t[0], t[1] + 16 + up, align, "rgba(116,121,124,.95)");
      });
    }
    function point(e) {
      if (!S) return;
      var b = cv.getBoundingClientRect(), x = e.clientX - b.left, y = e.clientY - b.top, best = -1, bd = 36 * 36;
      for (var k = 0; k < n; k++) {
        var p = pos(k, rad + 8), d = (p[0] - x) * (p[0] - x) + (p[1] - y) * (p[1] - y);
        if (d < bd) { bd = d; best = k; }
      }
      if (best !== hover) { hover = best; draw(); if (o.onHover) o.onHover(hover); }
    }
    cv.onpointermove = point;
    cv.onpointerdown = point;
    cv.onpointerleave = function () { if (hover >= 0) { hover = -1; draw(); if (o.onHover) o.onHover(-1); } };
    draw();
    keep(cv, draw);
    return { pairs: pairs };
  }

  window.AndraLens = { weave: weave, ring: ring, pct: pct };
})();
