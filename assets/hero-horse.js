// Andra Markets homepage hero: the horse drawn by particles (owner-approved, 31 Oct 2026).
//
// Every dot starts at one point at the centre of the hero and flies out from it to its place
// in the horse (owner, 31 Oct 2026), outline first, as the light theme prints it (the pencil
// look): one particle per inked pixel of
// assets/horse-particles.png, made from andra-horse.png by tools/make_horse_particles.py.
// The pointer parts the dots; a slow band of light passes over the drawing. Where the hero
// has scroll room, scrolling through it turns the horse into an illustrative price chart
// drawn like an engraving. The homepage is one screen (owner, 31 Oct 2026), so there it
// stays the horse and the chart is never built.
//
// Light theme: soft black dots on white (the canvas is drawn light on dark and inverted in
// CSS). Dark theme: white dots, and the horse settles in dark grey. Reduced motion: the
// drawing stands still and nothing morphs. Without WebGL or JavaScript the hero keeps the
// still engraving (.horse).
//
// The headline and the index of sections fly out of the same point (owner-approved, 31 Oct
// 2026): each character is drawn where the page sets it and sampled into particles; once
// they settle, the real text (crisp, selectable, the links working) takes over. The page
// marks html.hero-forming before the hero is parsed (HERO_BOOT in tools/build_site.py); this
// script removes it whenever it cannot run, so the text is never left hidden.
(function () {
  "use strict";
  var hero = document.querySelector(".hero");
  var stage = hero && hero.querySelector(".hero__stage");
  var canvas = hero && hero.querySelector(".hero__canvas");
  var art = hero && hero.querySelector(".hero__art");
  var copy = hero && hero.querySelector(".hero__copy");
  var stamp = hero && hero.querySelector(".hero__stamp");
  var horseImg = art && art.querySelector(".horse");
  var root = document.documentElement;
  function giveUp() { root.classList.remove("hero-forming"); }
  if (!stage || !canvas || !art || !copy || !horseImg || !window.WebGLRenderingContext) { giveUp(); return; }
  var headline = copy.querySelector("h1");
  var links = Array.prototype.slice.call(copy.querySelectorAll(".hero__index a"));
  var mq = window.matchMedia("(prefers-reduced-motion: reduce)");
  var reduce = mq.matches;
  var TAU = Math.PI * 2;
  var SRC = { x: 278, y: 258, w: 454, h: 516, side: 1024 }; // the horse inside the 1024px engraving
  var DONE = 6; // seconds until every particle has settled

  // Colours as the canvas draws them. In the light theme the canvas is inverted, so each
  // value is the complement of the ink on screen: soft black dust and horse (about #333 with
  // the canvas at 0.8 opacity). In the dark theme: ink dust and chart, a dark grey horse.
  var COLOURS = {
    light: { dust: [0.92, 0.905, 0.89], horse: [0.9, 0.886, 0.873], text: [0.99, 0.985, 0.98] },
    dark: { dust: [0.914, 0.925, 0.922], horse: [0.36, 0.374, 0.389], text: [0.914, 0.925, 0.922] }
  };

  function rng(seed) {
    return function () {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      var t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  function clamp01(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }
  function smooth(a, b, v) { var t = clamp01((v - a) / (b - a)); return t * t * (3 - 2 * t); }
  function theme() { return root.getAttribute("data-theme") === "dark" ? "dark" : "light"; }

  // a sine-free hash (Dave Hoskins), stable on mobile GPUs: one random number in [0, 1) per input
  var HASH = "float hash(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }";
  // the point at the centre of the hero that every particle leaves from: a few pixels across,
  // its particles turning in place until their turn to fly. They leave it at speed and slow
  // into place (ease-out cubic), so nothing piles up around the point.
  var SEED = "vec2 seed(vec2 c, vec2 r, float t){ float a = r.x*6.2832 + t*(1.5 + 2.0*r.y); return c + vec2(cos(a), sin(a)) * 3.0 * sqrt(r.y); }" +
    "float fly(float x){ float y = 1.0 - x; return 1.0 - y*y*y; }";
  var VS = [
    "attribute vec4 aH; attribute vec3 aC;",
    "uniform vec2 res; uniform vec2 cc; uniform vec4 hb; uniform vec3 ptr; uniform vec3 hcol; uniform vec3 dcol; uniform vec2 dim;",
    "uniform float t, m, dpr, pitch, sm, am, prad, sheen;",
    "varying float va; varying vec3 vc;",
    "const float PI = 3.14159265;",
    "float eio(float x){ return x < 0.5 ? 4.0*x*x*x : 1.0 - pow(-2.0*x + 2.0, 3.0) * 0.5; }",
    HASH,
    SEED,
    "void main(){",
    // each particle's random numbers, from its own pixel: nothing to build or upload
    "  vec2 cell = aH.xy * dim;",
    "  vec4 aR = vec4(hash(cell), hash(cell + 17.31), hash(cell + 41.97), hash(cell + 73.13));",
    "  vec4 aR2 = vec4(0.0, hash(cell + 101.7), hash(cell + 131.9), hash(cell + 163.3));",
    "  vec2 home = hb.xy + (aH.xy - 0.5) * hb.zw;",
    // outline first, then the shading from the head down
    "  float d = aH.w > 0.5 ? 0.5 + 1.2*aR.w : 1.6 + 1.1*aH.y + 0.6*aR.w;",
    "  float f = clamp((t - d) / 2.3, 0.0, 1.0);",
    "  vec2 s = seed(cc, vec2(aR.x, aR2.y), t);",
    "  float e = fly(f);",
    "  vec2 dd = home - s;",
    "  float k = sin(PI*e) * (aR.z - 0.5) * 0.44;",
    "  vec2 pos = s + dd*e + vec2(-dd.y, dd.x)*k;",
    "  float dust = 0.035 + 0.55*pow(aR2.w, 4.0);",
    "  float a = mix(dust, aH.z, smoothstep(0.6, 1.0, e));",
    "  float sz = mix(2.2, 2.0*pitch, e);",
    "  float band = (aH.x + aH.y*0.6) - mod(t*0.12, 2.6) + 0.5;",
    "  a *= 1.0 + sheen * 0.5 * f * exp(-band*band*80.0);",
    // scroll: the horse comes apart into dust and settles as the chart
    "  float eg = eio(clamp(m*1.75 - aH.x*0.75, 0.0, 1.0));",
    "  float sc = sin(PI*eg) * (24.0 + 70.0*aR2.y);",
    "  float ang = aR2.z*2.0*PI;",
    "  pos = mix(pos, aC.xy, eg) + vec2(cos(ang), sin(ang))*sc;",
    "  a = mix(mix(a, dust, sin(PI*eg)), aC.z, smoothstep(0.6, 1.0, eg));",
    "  sz = mix(sz, 2.0, eg);",
    // pointer: the dots part around it and close again behind it
    "  vec2 dp = pos - ptr.xy; float dist = length(dp);",
    "  float q = 1.0 - smoothstep(0.0, prad, dist);",
    "  vec2 dir = dp / max(dist, 0.001);",
    "  pos += (dir * q * q * prad * 0.3 * (0.35 + 1.3*aR.x) + vec2(-dir.y, dir.x) * q * prad * 0.16 * (aR.y - 0.5)) * ptr.z;",
    "  a *= 1.0 + 0.6 * q * ptr.z;",
    "  gl_Position = vec4(pos.x / res.x * 2.0 - 1.0, 1.0 - pos.y / res.y * 2.0, 0.0, 1.0);",
    "  gl_PointSize = max(1.0, sz * dpr * sm);",
    "  va = a * am;",
    "  vc = mix(dcol, hcol, smoothstep(0.6, 1.0, e) * (1.0 - smoothstep(0.0, 0.5, eg)));",
    "}"
  ].join("\n");
  var FS = [
    "precision mediump float; varying float va; varying vec3 vc; uniform float kk;",
    "void main(){ vec2 d = gl_PointCoord - 0.5; float k = exp(-dot(d, d) * 4.0 * kk);",
    "  gl_FragColor = vec4(vc * va * k, va * k); }"
  ].join("\n");
  // the headline and the index: targets in stage pixels, each group with its own timing
  var VS_TEXT = [
    "attribute vec4 aP; attribute vec2 aQ;",
    "uniform vec2 res; uniform vec2 cc; uniform vec3 ptr; uniform vec3 tcol; uniform vec3 dcol;",
    "uniform float t, dpr, sm, am, prad, pitch, visP, visI;",
    "varying float va; varying vec3 vc;",
    "const float PI = 3.14159265;",
    HASH,
    SEED,
    "void main(){",
    "  vec2 cell = aP.xy * 1.25 + 7.0;",
    "  vec4 rq = vec4(hash(cell), hash(cell + 23.7), hash(cell + 57.1), hash(cell + 89.3));",
    "  vec2 aS = rq.zw;",
    "  float f = clamp((t - aQ.x) / aQ.y, 0.0, 1.0);",
    "  vec2 s = seed(cc, rq.xz, t);",
    "  float e = fly(f);",
    "  vec2 dd = aP.xy - s;",
    "  float k = sin(PI*e) * (rq.y - 0.5) * 0.44;",
    "  vec2 pos = s + dd*e + vec2(-dd.y, dd.x)*k;",
    "  float dust = 0.035 + 0.55*pow(aS.y, 4.0);",
    "  float a = mix(dust, aP.z, smoothstep(0.6, 1.0, e));",
    "  a *= mix(1.0, aP.w < 1.5 ? visP : visI, step(0.999, f));",
    "  vec2 dp = pos - ptr.xy; float dist = length(dp);",
    "  float q = 1.0 - smoothstep(0.0, prad, dist);",
    "  vec2 dir = dp / max(dist, 0.001);",
    "  pos += (dir * q * q * prad * 0.3 * (0.35 + 1.3*aS.x) + vec2(-dir.y, dir.x) * q * prad * 0.16 * (aS.y - 0.5)) * ptr.z;",
    "  gl_Position = vec4(pos.x / res.x * 2.0 - 1.0, 1.0 - pos.y / res.y * 2.0, 0.0, 1.0);",
    "  gl_PointSize = max(1.0, mix(2.2, 2.0*pitch, e) * dpr * sm);",
    "  va = a * am;",
    "  vc = mix(dcol, tcol, smoothstep(0.6, 1.0, e));",
    "}"
  ].join("\n");

  var gl = null;
  try { gl = canvas.getContext("webgl", { antialias: false, alpha: true, premultipliedAlpha: true }); } catch (e) { gl = null; }
  if (!gl) { giveUp(); return; }
  function shader(type, src) { var o = gl.createShader(type); gl.shaderSource(o, src); gl.compileShader(o); return o; }
  function program(vs) {
    var p = gl.createProgram();
    gl.attachShader(p, shader(gl.VERTEX_SHADER, vs));
    gl.attachShader(p, shader(gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(p);
    return gl.getProgramParameter(p, gl.LINK_STATUS) ? p : null;
  }
  function uniforms(p, names) { var u = {}; names.forEach(function (n) { u[n] = gl.getUniformLocation(p, n); }); return u; }
  var prog = program(VS);
  if (!prog) { giveUp(); return; }
  var progT = program(VS_TEXT);
  var U = uniforms(prog, ["res", "cc", "hb", "ptr", "hcol", "dcol", "dim", "t", "m", "dpr", "pitch", "sm", "am", "prad", "sheen", "kk"]);
  var UT = progT ? uniforms(progT, ["res", "cc", "ptr", "tcol", "dcol", "t", "dpr", "sm", "am", "prad", "pitch", "visP", "visI", "kk"]) : null;
  var MAX_ATTRIBS = Math.min(8, gl.getParameter(gl.MAX_VERTEX_ATTRIBS));
  // both programs share the attribute slots: each draw switches them to its own buffers
  function attribs(list) {
    for (var i = 0; i < MAX_ATTRIBS; i++) gl.disableVertexAttribArray(i);
    list.forEach(function (a) {
      var l = gl.getAttribLocation(a[0], a[1]);
      if (l < 0) return;
      gl.bindBuffer(gl.ARRAY_BUFFER, a[2]);
      gl.enableVertexAttribArray(l);
      gl.vertexAttribPointer(l, a[3], gl.FLOAT, false, a[4], a[5]);
    });
  }

  var N = 0, PW = 0, PH = 0, px = null, sBuf = null, cBuf = null, chartAttr = null, chartReady = false, order = null;
  var TS = 1.25;            // the text is sampled at 1.25 particles per CSS pixel
  var tBuf = null, TN = 0, textOn = false, T_P = 3, T_I = 4, crispP = false, crispI = false;
  var W = 0, H = 0, DPR = 1, box = null, cbox = null;
  var t0 = 0, running = false, visible = true, lastP = -1, frameNo = 0;
  var ptr = { x: -1e4, y: -1e4, sx: -1e4, sy: -1e4, s: 0, last: -1e9 };

  /* ---------- the particles, from the map ---------- */
  function build(image) {
    PW = image.naturalWidth; PH = image.naturalHeight;
    var c = document.createElement("canvas"); c.width = PW; c.height = PH;
    var x = c.getContext("2d", { willReadFrequently: true });
    x.drawImage(image, 0, 0);
    var d = x.getImageData(0, 0, PW, PH).data;
    var idx = [];
    for (var i = 0, n = PW * PH; i < n; i++) if (d[i * 4] > 10) idx.push(i);
    // shuffled, so the first third (the halo pass) is a fair sample of the whole drawing
    var r = rng(1412);
    for (var j = idx.length - 1; j > 0; j--) { var k = Math.floor(r() * (j + 1)), tmp = idx[j]; idx[j] = idx[k]; idx[k] = tmp; }
    N = idx.length;
    px = new Uint32Array(idx);
    // position, ink and outline only: the shader makes each particle's random numbers
    var st = new Float32Array(N * 4);
    for (var q = 0, o = 0; q < N; q++, o += 4) {
      var p = idx[q], xx = p % PW, yy = (p - xx) / PW;
      st[o] = (xx + 0.5) / PW; st[o + 1] = (yy + 0.5) / PH;
      st[o + 2] = d[p * 4] / 255; st[o + 3] = d[p * 4 + 1] > 127 ? 1 : 0;
    }
    sBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, sBuf);
    gl.bufferData(gl.ARRAY_BUFFER, st, gl.STATIC_DRAW);
    cBuf = gl.createBuffer();
    chartAttr = new Float32Array(N * 3);
    gl.bindBuffer(gl.ARRAY_BUFFER, cBuf);
    gl.bufferData(gl.ARRAY_BUFFER, chartAttr, gl.DYNAMIC_DRAW);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.ONE, gl.ONE);
    gl.clearColor(0, 0, 0, 0);
  }

  /* ---------- layout: the horse sits exactly where the still engraving sits ---------- */
  function measure() {
    var s = stage.getBoundingClientRect(), a = horseImg.getBoundingClientRect(), slot = art.getBoundingClientRect();
    W = Math.max(1, Math.round(s.width)); H = Math.max(1, Math.round(s.height));
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(W * DPR); canvas.height = Math.round(H * DPR);
    gl.viewport(0, 0, canvas.width, canvas.height);
    var k = a.height / SRC.side; // the engraving is square; its height is what the layout sets
    box = { cx: a.left - s.left + (SRC.x + SRC.w / 2) * k, cy: a.top - s.top + (SRC.y + SRC.h / 2) * k, w: SRC.w * k, h: SRC.h * k };
    // the chart takes the horse's place: the right half on wide screens (the headline is top
    // left, the index bottom left), the horse's slot between them on phones
    var gutter = Math.min(56, Math.max(16, W * 0.04)), side = Math.max(0, (W - 1440) / 2);
    var L = side + gutter, Rt = W - side - gutter, y0, y1;
    if (W > 860) {
      y0 = Math.max(64 + 40, H * 0.2); y1 = Math.min(H * 0.7, H - 150);
      if (y1 - y0 < 160) y1 = y0 + 160;
      cbox = { x: Math.round(L + (Rt - L) * 0.52), y: Math.round(y0), w: Math.round((Rt - L) * 0.48), h: Math.round(y1 - y0) };
    } else {
      y0 = slot.top - s.top + 8; y1 = slot.bottom - s.top - 28;
      if (y1 - y0 < 100) y1 = y0 + 100;
      cbox = { x: Math.round(L), y: Math.round(y0), w: Math.round(Rt - L), h: Math.round(y1 - y0) };
    }
    if (stamp) { stamp.style.left = cbox.x + "px"; stamp.style.top = (cbox.y + cbox.h + 12) + "px"; }
    chartReady = false;
  }

  /* ---------- the headline and the index, character by character ---------- */
  // Draws el's characters where the page sets them and returns its inked pixels as
  // [x, y, ink, group, delay, duration] records (six floats each), in stage pixels.
  function sampleText(el, group, delay, dur, r) {
    var s = stage.getBoundingClientRect(), cs = getComputedStyle(el), b = el.getBoundingClientRect();
    var size = parseFloat(cs.fontSize), pad = 4;
    var w = Math.ceil((b.width + pad * 2) * TS), h = Math.ceil((b.height + pad * 2) * TS);
    if (w < 2 || h < 2) return new Float32Array(0);
    var c = document.createElement("canvas"); c.width = w; c.height = h;
    var x = c.getContext("2d", { willReadFrequently: true });
    x.setTransform(TS, 0, 0, TS, (pad - b.left) * TS, (pad - b.top) * TS);
    x.font = cs.fontWeight + " " + size + "px " + cs.fontFamily;
    x.fillStyle = "#fff"; x.textBaseline = "alphabetic";
    var m = x.measureText("Mg"), asc = m.fontBoundingBoxAscent || size * 0.8;
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT), range = document.createRange(), node, i, rc;
    while ((node = walker.nextNode())) {
      for (i = 0; i < node.textContent.length; i++) {
        if (!node.textContent[i].trim()) continue;
        range.setStart(node, i); range.setEnd(node, i + 1);
        rc = range.getClientRects()[0];
        if (rc) x.fillText(node.textContent[i], rc.left, rc.top + asc);
      }
    }
    var d = x.getImageData(0, 0, w, h).data, n = 0, k;
    for (k = 3; k < d.length; k += 4) if (d[k] >= 16) n++;
    var out = new Float32Array(n * 6), o = 0, x0 = b.left - pad - s.left, y0 = b.top - pad - s.top, bw = Math.max(1, b.width), xx, yy, px;
    for (yy = 0, k = 3; yy < h; yy++) for (xx = 0; xx < w; xx++, k += 4) {
      if (d[k] < 16) continue;
      px = x0 + (xx + 0.5) / TS;
      out[o] = px; out[o + 1] = y0 + (yy + 0.5) / TS; out[o + 2] = Math.min(1, d[k] / 255 * 1.05);
      out[o + 3] = group; out[o + 4] = delay((px - x0 - pad) / bw, r); out[o + 5] = dur;
      o += 6;
    }
    return out;
  }

  function buildText() {
    var r = rng(5150), parts = [], total = 0;
    // the headline first, left to right as it reads; then the index, item by item
    parts.push(sampleText(headline, 1, function (u, rr) { return 0.15 + u * 0.9 + rr() * 0.3; }, 1.6, r));
    T_P = 0.15 + 0.9 + 0.3 + 1.6;
    links.forEach(function (el, k) {
      parts.push(sampleText(el, 2, function (u, rr) { return 0.95 + k * 0.09 + u * 0.3 + rr() * 0.2; }, 1.3, r));
    });
    T_I = 0.95 + Math.max(0, links.length - 1) * 0.09 + 0.3 + 0.2 + 1.3;
    parts.forEach(function (a) { total += a.length; });
    var A = new Float32Array(total), o = 0;
    parts.forEach(function (a) { A.set(a, o); o += a.length; });
    TN = total / 6;
    // shuffled, so the halo pass (the first third) covers every word
    var q, j, k2, tmp;
    for (q = TN - 1; q > 0; q--) {
      j = Math.floor(r() * (q + 1));
      for (k2 = 0; k2 < 6; k2++) { tmp = A[q * 6 + k2]; A[q * 6 + k2] = A[j * 6 + k2]; A[j * 6 + k2] = tmp; }
    }
    if (!tBuf) tBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, tBuf);
    gl.bufferData(gl.ARRAY_BUFFER, A, gl.STATIC_DRAW);
  }

  // the real text takes over for good; the page no longer needs the forming state
  function finishText() {
    textOn = false;
    hero.classList.add("crisp-h1", "crisp-ix");
    root.classList.add("hero-formed");
    root.classList.remove("hero-forming");
  }

  /* ---------- the chart, drawn like an engraving and shared out among the particles ---------- */
  var SERIES = (function () {
    var S = 180, ys = [], y = 0, r = rng(1412), i, k;
    for (i = 0; i < S; i++) { y += (r() - 0.46) * 1.0 + 0.35 * Math.sin(i / 17); ys.push(y); }
    var sm = ys.map(function (_, i) { var a = 0, c = 0; for (k = -4; k <= 4; k++) { var j = i + k; if (j >= 0 && j < S) { a += ys[j]; c++; } } return a / c; });
    var lo = Math.min.apply(null, sm), hi = Math.max.apply(null, sm);
    return sm.map(function (v) { return 1 - (0.06 + 0.82 * (v - lo) / (hi - lo)); });
  })();

  function ctx2d(w, h) {
    var c = document.createElement("canvas"); c.width = w; c.height = h;
    return c.getContext("2d", { willReadFrequently: true });
  }
  function drawChart(w, h) {
    var x = ctx2d(w, h), r = rng(77), S = SERIES.length, i, k, s;
    x.fillStyle = "#000"; x.fillRect(0, 0, w, h);
    var padL = 1, padR = 12, top = Math.round(h * 0.05), bot = h - 16;
    var P = SERIES.map(function (v, i) { return [padL + i / (S - 1) * (w - padL - padR), top + v * (bot - top) + (r() - 0.5) * 0.7]; });
    var line = new Path2D(), area = new Path2D();
    P.forEach(function (p, i) { if (i) line.lineTo(p[0], p[1]); else line.moveTo(p[0], p[1]); });
    area.moveTo(P[0][0], bot); P.forEach(function (p) { area.lineTo(p[0], p[1]); }); area.lineTo(P[S - 1][0], bot); area.closePath();
    var depth = Math.max(26, (bot - top) * 0.22);

    // dotted grid, as in the site's charts
    x.fillStyle = "rgba(255,255,255,0.55)";
    [0.25, 0.5, 0.75].forEach(function (lv) { var gy = Math.round(top + lv * (bot - top)); for (var gx = 0; gx < w - padR; gx += 4) x.fillRect(gx, gy, 1, 1); });

    // hatching under the line, slightly wavy, fading with depth
    function hatch(c, dir) {
      c.beginPath();
      for (k = -h; k < w + h; k += 7.5 + (r() - 0.5) * 1.2) {
        var ph = r() * TAU;
        for (s = 0; s <= h; s += 6) {
          var hx = k + dir * s + Math.sin(s * 0.05 + ph) * 0.6, hy = h - s;
          if (s) c.lineTo(hx, hy); else c.moveTo(hx, hy);
        }
      }
      c.stroke();
    }
    var hc = ctx2d(w, h);
    hc.lineWidth = 1; hc.strokeStyle = "rgba(255,255,255,0.9)";
    hc.save(); hc.clip(area); hatch(hc, 1); hc.restore();
    hc.globalCompositeOperation = "destination-in";
    var gr = hc.createLinearGradient(0, top, 0, bot);
    gr.addColorStop(0, "rgba(0,0,0,0.85)"); gr.addColorStop(1, "rgba(0,0,0,0.07)");
    hc.fillStyle = gr; hc.fillRect(0, 0, w, h);
    x.drawImage(hc.canvas, 0, 0);
    // crosshatch close under the line only, fading out with distance from it
    var xc = ctx2d(w, h);
    xc.lineWidth = 1; xc.strokeStyle = "rgba(255,255,255,0.8)";
    xc.save(); xc.clip(area); hatch(xc, -1); xc.restore();
    var mc = ctx2d(w, h);
    mc.lineJoin = "round"; mc.strokeStyle = "rgba(255,255,255,0.12)";
    for (var lw = 6; lw <= Math.max(60, depth * 2); lw += 6) { mc.lineWidth = lw; mc.stroke(line); }
    xc.globalCompositeOperation = "destination-in"; xc.drawImage(mc.canvas, 0, 0);
    x.drawImage(xc.canvas, 0, 0);

    // baseline with ticks
    x.strokeStyle = "rgba(255,255,255,0.75)"; x.lineWidth = 1; x.beginPath();
    x.moveTo(0, bot + 0.5); x.lineTo(w - padR, bot + 0.5);
    for (i = 0; i <= 12; i++) { var tx = Math.round(padL + i / 12 * (w - padL - padR)) + 0.5; x.moveTo(tx, bot); x.lineTo(tx, bot + 5); }
    x.stroke();
    // the line: an engraver's double stroke, and a ring on the last point
    x.lineJoin = "round"; x.lineCap = "round";
    x.save(); x.translate(0, 3.2); x.strokeStyle = "rgba(255,255,255,0.5)"; x.lineWidth = 0.9; x.stroke(line); x.restore();
    x.strokeStyle = "#fff"; x.lineWidth = 2.3; x.stroke(line);
    var ex = P[S - 1][0], ey = P[S - 1][1];
    x.beginPath(); x.arc(ex, ey, 5.5, 0, TAU); x.lineWidth = 1.1; x.stroke();
    x.beginPath(); x.arc(ex, ey, 2.2, 0, TAU); x.fillStyle = "#fff"; x.fill();
    return x.getImageData(0, 0, w, h).data;
  }

  function buildChart() {
    if (!order) {
      // the left of the horse becomes the left of the chart
      order = Array.prototype.slice.call(new Uint32Array(N).map(function (_, i) { return i; }));
      order.sort(function (a, b) { return (px[a] % PW) - (px[b] % PW) || px[a] - px[b]; });
    }
    var w = Math.max(40, cbox.w), h = Math.max(40, cbox.h), d = drawChart(w, h), r = rng(5);
    var xs = [], ys = [], is = [], sum = 0, cx, cy;
    for (cx = 0; cx < w; cx++) for (cy = 0; cy < h; cy++) {
      var v = d[(cy * w + cx) * 4] / 255;
      if (v > 0.03) { xs.push(cx); ys.push(cy); is.push(v); sum += v; }
    }
    // each lit pixel gets particles in proportion to its brightness
    var per = N / sum, alpha = Math.min(1, 0.92 * sum / N), k = 0, carry = 0;
    for (var j = 0; j < xs.length && k < N; j++) {
      var want = is[j] * per + carry, c = Math.floor(want);
      carry = want - c;
      if (j === xs.length - 1) c = N - k;
      for (var q = 0; q < c && k < N; q++, k++) {
        var i = order[k] * 3;
        chartAttr[i] = cbox.x + xs[j] + 0.5 + (r() - 0.5) * 0.7;
        chartAttr[i + 1] = cbox.y + ys[j] + 0.5 + (r() - 0.5) * 0.7;
        chartAttr[i + 2] = alpha;
      }
    }
    for (; k < N; k++) { var z = order[k] * 3; chartAttr[z] = cbox.x + w; chartAttr[z + 1] = cbox.y + h; chartAttr[z + 2] = 0; }
    gl.bindBuffer(gl.ARRAY_BUFFER, cBuf);
    gl.bufferData(gl.ARRAY_BUFFER, chartAttr, gl.DYNAMIC_DRAW);
    chartReady = true;
  }

  /* ---------- drawing ---------- */
  function hasTrack() { return hero.getBoundingClientRect().height - H > 1; }

  function progress() {
    if (reduce) return 0;
    var r = hero.getBoundingClientRect(), span = r.height - H;
    return span > 0 ? clamp01(-r.top / span) : 0;
  }

  function draw(t, p) {
    var m = reduce ? 0 : smooth(0.15, 0.75, p);
    if (m > 0 && t < DONE) { t0 -= (DONE - t) * 1000; t = DONE; } // scrolling finishes the drawing
    if (m > 0 && !chartReady) buildChart();
    var col = COLOURS[theme()];
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(prog);
    attribs([[prog, "aH", sBuf, 4, 16, 0], [prog, "aC", cBuf, 3, 12, 0]]);
    gl.uniform2f(U.dim, PW, PH);
    gl.uniform2f(U.res, W, H);
    gl.uniform1f(U.dpr, DPR);
    gl.uniform4f(U.hb, box.cx, box.cy, box.w, box.h);
    gl.uniform1f(U.pitch, box.h / PH);
    gl.uniform3f(U.ptr, ptr.sx, ptr.sy, reduce ? 0 : ptr.s);
    gl.uniform1f(U.prad, W > 860 ? 95 : 70);
    gl.uniform1f(U.t, reduce ? 1000 : t);
    gl.uniform1f(U.m, m);
    gl.uniform2f(U.cc, W / 2, H / 2);
    gl.uniform1f(U.sheen, reduce ? 0 : 1);
    gl.uniform3f(U.hcol, col.horse[0], col.horse[1], col.horse[2]);
    gl.uniform3f(U.dcol, col.dust[0], col.dust[1], col.dust[2]);
    // a faint halo from a third of the particles (light theme only: the dark homepage is
    // matte black, owner 31 Oct 2026), then every particle sharp
    var halo = theme() === "light";
    if (halo) {
      gl.uniform1f(U.sm, 4.5); gl.uniform1f(U.am, 0.05); gl.uniform1f(U.kk, 2.0);
      gl.drawArrays(gl.POINTS, 0, Math.floor(N / 3));
    }
    gl.uniform1f(U.sm, 1); gl.uniform1f(U.am, 0.86); gl.uniform1f(U.kk, 2.8);
    gl.drawArrays(gl.POINTS, 0, N);
    if (textOn) drawText(t, col, halo);
    if (stamp) stamp.style.opacity = smooth(0.7, 1, m).toFixed(3);
    lastP = p;
  }

  function drawText(t, col, halo) {
    var cp = t >= T_P, ci = t >= T_I;
    if (cp !== crispP) { crispP = cp; hero.classList.toggle("crisp-h1", cp); }
    if (ci !== crispI) { crispI = ci; hero.classList.toggle("crisp-ix", ci); }
    if (t >= T_I + 0.6) { finishText(); return; }
    if (!TN) return;
    gl.useProgram(progT);
    attribs([[progT, "aP", tBuf, 4, 24, 0], [progT, "aQ", tBuf, 2, 24, 16]]);
    gl.uniform2f(UT.res, W, H); gl.uniform1f(UT.dpr, DPR);
    gl.uniform2f(UT.cc, W / 2, H / 2);
    gl.uniform3f(UT.ptr, ptr.sx, ptr.sy, ptr.s); gl.uniform1f(UT.prad, W > 860 ? 95 : 70);
    gl.uniform1f(UT.t, t); gl.uniform1f(UT.pitch, 1 / TS);
    gl.uniform1f(UT.visP, 1 - smooth(T_P, T_P + 0.45, t)); gl.uniform1f(UT.visI, 1 - smooth(T_I, T_I + 0.45, t));
    gl.uniform3f(UT.tcol, col.text[0], col.text[1], col.text[2]); gl.uniform3f(UT.dcol, col.dust[0], col.dust[1], col.dust[2]);
    if (halo) {
      gl.uniform1f(UT.sm, 4.5); gl.uniform1f(UT.am, 0.05); gl.uniform1f(UT.kk, 2.0);
      gl.drawArrays(gl.POINTS, 0, Math.floor(TN / 3));
    }
    gl.uniform1f(UT.sm, 1); gl.uniform1f(UT.am, 0.86); gl.uniform1f(UT.kk, 2.8);
    gl.drawArrays(gl.POINTS, 0, TN);
  }

  function loop(now) {
    if (!running) return;
    requestAnimationFrame(loop);
    ptr.s += ((now - ptr.last < 1200 ? 1 : 0) - ptr.s) * 0.08;
    ptr.sx += (ptr.x - ptr.sx) * 0.22; ptr.sy += (ptr.y - ptr.sy) * 0.22;
    var t = (now - t0) / 1000, p = progress();
    // once settled and untouched, half the frame rate is plenty for the band of light
    if (t > DONE + 0.5 && ptr.s < 0.01 && p === lastP && (frameNo++ & 1)) return;
    draw(t, p);
  }
  function start() { if (!running && !reduce && visible && !document.hidden) { running = true; requestAnimationFrame(loop); } }
  function stop() { running = false; }
  function still() { draw((performance.now() - t0) / 1000, progress()); }

  // resolves true once the page's font is ready, false if it takes longer than ms
  function fontReady(ms) {
    if (!document.fonts || !document.fonts.load) return Promise.resolve(true);
    var font = getComputedStyle(headline).fontWeight + " 32px " + getComputedStyle(headline).fontFamily;
    return Promise.race([
      document.fonts.load(font).then(function () { return document.fonts.ready; }).then(function () { return true; }, function () { return false; }),
      new Promise(function (res) { setTimeout(function () { res(false); }, ms); })
    ]);
  }

  function begin(image) {
    build(image);
    if (!N) { giveUp(); return; }
    // the headline and index form too, unless the page already gave up waiting (HERO_BOOT)
    var withText = !!(progT && headline && root.classList.contains("hero-forming") && !reduce);
    if (!withText) giveUp();
    hero.classList.add("is-live");
    measure();
    t0 = performance.now();
    if (withText) {
      fontReady(1500).then(function (ok) {
        if (!ok) { finishText(); return; }
        requestAnimationFrame(function () {
          setTimeout(function () { buildText(); textOn = true; if (!running) still(); }, 0);
        });
      });
    }
    if (reduce) still(); else start();
    // the chart is only needed if the hero can scroll; then build it when the page is quiet
    setTimeout(function () { if (!chartReady && hasTrack()) buildChart(); }, (DONE + 1) * 1000);

    stage.addEventListener("pointermove", function (e) {
      var r = stage.getBoundingClientRect();
      ptr.x = e.clientX - r.left; ptr.y = e.clientY - r.top;
      if (ptr.s < 0.01) { ptr.sx = ptr.x; ptr.sy = ptr.y; }
      ptr.last = performance.now();
    }, { passive: true });
    stage.addEventListener("pointerleave", function () { ptr.last = -1e9; });
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (es) { visible = es[0].isIntersecting; if (visible) start(); else stop(); }).observe(hero);
    }
    document.addEventListener("visibilitychange", function () { if (document.hidden) stop(); else start(); });
    new MutationObserver(function () { if (!running) still(); }).observe(root, { attributes: true, attributeFilter: ["data-theme"] });
    var rt;
    window.addEventListener("resize", function () {
      clearTimeout(rt);
      rt = setTimeout(function () { measure(); if (textOn) buildText(); if (!running) still(); }, 120);
    });
    var onMotion = function (e) { reduce = e.matches; measure(); if (reduce) { stop(); still(); } else start(); };
    if (mq.addEventListener) mq.addEventListener("change", onMotion);
  }

  var image = window.__heroMap;
  if (image && image.complete) {
    if (image.naturalWidth) begin(image); else giveUp();
  } else {
    if (!image) { image = new Image(); image.decoding = "async"; image.src = canvas.getAttribute("data-src"); }
    image.addEventListener("load", function () { begin(image); });
    image.addEventListener("error", giveUp);
  }
})();
