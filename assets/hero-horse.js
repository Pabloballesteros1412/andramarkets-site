// Andra Markets homepage hero: the horse drawn by particles (owner-approved, 31 Oct 2026).
//
// Every dot starts at one point at the centre of the hero and flies out from it to its place
// in the horse (owner, 31 Oct 2026), outline first, as the header's mark shows it (owner-
// approved, 1 Nov 2026; until then the pencil look): one particle per inked pixel of
// assets/horse-particles.png (loaded as its lossless WebP copy where the browser decodes it),
// made from andra-horse.png by tools/make_horse_particles.py.
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
// The headline, the index (the four group names) and the header (the mark, which is also the theme
// switch, the name and the legal line; owner, 31 Oct and 1 Nov 2026) fly out of the same point
// (owner-approved, 31 Oct 2026): each character and the mark are drawn where the page sets them
// and sampled into particles; once they settle, the real page (crisp, selectable, the links and
// the switch working) takes over. The page marks html.hero-forming in its head, before the
// header is parsed (HERO_BOOT in tools/build_site.py); this script removes it whenever it
// cannot run, so nothing is left hidden.
//
// A click on a link to another page takes the whole hero back into that point before the
// page opens (owner-approved, 1 Nov 2026); the section page opens out of it
// (assets/section-scene.js).
(function () {
  "use strict";
  var hero = document.querySelector(".hero");
  var stage = hero && hero.querySelector(".hero__stage");
  var canvas = hero && hero.querySelector(".hero__canvas");
  var art = hero && hero.querySelector(".hero__art");
  var copy = hero && hero.querySelector(".hero__copy");
  var stamp = hero && hero.querySelector(".hero__stamp");
  var horseImg = art && art.querySelector(".horse");
  var bar = document.querySelector(".site-header--home");
  var root = document.documentElement;
  function giveUp() { root.classList.remove("hero-forming"); }
  // the particles cannot draw the horse: show the text and fetch the still engraving
  // (the page fetches it only when it may show: __heroStill in HERO_BOOT)
  function fail() { giveUp(); if (window.__heroStill) window.__heroStill(); }
  if (!stage || !canvas || !art || !copy || !horseImg || !window.WebGLRenderingContext) { fail(); return; }
  var headline = copy.querySelector("h1");
  // the index's four group names (owner-approved, 1 Nov 2026): their sections are folded away
  var links = Array.prototype.slice.call(copy.querySelectorAll(".hero__index summary"));
  var mq = window.matchMedia("(prefers-reduced-motion: reduce)");
  var reduce = mq.matches;
  var TAU = Math.PI * 2;
  var SRC = { x: 278, y: 258, w: 454, h: 516, side: 1024 }; // the horse inside the 1024px engraving
  // The hero's clock runs 1.4x real time (owner, 1 Nov 2026: "a little faster"), so every
  // timing below, in hero seconds, is 1/1.4 of it in real time: the horse settles at about
  // 4.3s, the phrase, the groups and the header turn crisp from about 2.1s. The band of
  // light over the settled horse keeps its real-time pace.
  var SPEED = 1.4;
  var DONE = 6; // hero seconds until every particle has settled

  // Colours as the canvas draws them. In the light theme the canvas is inverted, so each
  // value is the complement of the ink on screen: soft black dust and horse (about #333 with
  // the canvas at 0.8 opacity). In the dark theme the horse settles in the ink, as the
  // header's mark shows it (owner-approved, 1 Nov 2026; it was dark grey).
  var COLOURS = {
    light: { dust: [0.92, 0.905, 0.89], horse: [0.9, 0.886, 0.873], text: [0.99, 0.985, 0.98] },
    dark: { dust: [0.914, 0.925, 0.922], horse: [0.914, 0.925, 0.922], text: [0.914, 0.925, 0.922] }
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
    "uniform float t, m, dpr, pitch, sm, am, prad, sheen, xt, xo;",
    "varying float va; varying vec3 vc;",
    "const float PI = 3.14159265;",
    "float eio(float x){ return x < 0.5 ? 4.0*x*x*x : 1.0 - pow(-2.0*x + 2.0, 3.0) * 0.5; }",
    HASH,
    SEED,
    "void main(){",
    // Most of the time the horse stands settled: every particle at home, nothing flying,
    // nothing leaving, no pointer. Each stage below is then skipped as a whole (the test is on
    // uniforms, so every particle takes the same way and nothing is lost to branching), and
    // what is left is the place, the ink and the band of light. Skipped, each stage would
    // have changed nothing: past DONE every particle has landed (f and e are 1), m is 0 but
    // for a chart, xt is 0 but when leaving and ptr.z 0 once the pointer has gone.
    "  vec2 home = hb.xy + (aH.xy - 0.5) * hb.zw;",
    "  vec2 pos = home, s = cc;",
    "  float a = aH.z, sz = 2.0*pitch, f = 1.0, e = 1.0, eg = 0.0, xe = 0.0, dust = 0.0;",
    // each particle's random numbers, from its own pixel: nothing to build or upload, and only
    // made while something moves (the pointer needs two)
    "  vec2 cell = aH.xy * dim;",
    "  vec4 aR = vec4(0.0), aR2 = vec4(0.0);",
    "  bool moving = t < " + DONE.toFixed(1) + " || m > 0.0 || xt > 0.0;",
    "  if (moving || ptr.z > 0.0) aR.xy = vec2(hash(cell), hash(cell + 17.31));",
    "  if (moving) {",
    "    aR.zw = vec2(hash(cell + 41.97), hash(cell + 73.13));",
    "    aR2 = vec4(0.0, hash(cell + 101.7), hash(cell + 131.9), hash(cell + 163.3));",
    "    s = seed(cc, vec2(aR.x, aR2.y), t);",
    "    dust = 0.035 + 0.55*pow(aR2.w, 4.0);",
    "  }",
    // outline first, then the shading from the head down
    "  if (t < " + DONE.toFixed(1) + ") {",
    "    float d = aH.w > 0.5 ? 0.5 + 1.2*aR.w : 1.6 + 1.1*aH.y + 0.6*aR.w;",
    "    f = clamp((t - d) / 2.3, 0.0, 1.0);",
    "    e = fly(f);",
    "    vec2 dd = home - s;",
    "    float k = sin(PI*e) * (aR.z - 0.5) * 0.44;",
    "    pos = s + dd*e + vec2(-dd.y, dd.x)*k;",
    "    a = mix(dust, aH.z, smoothstep(0.6, 1.0, e));",
    "    sz = mix(2.2, 2.0*pitch, e);",
    "  }",
    "  float band = (aH.x + aH.y*0.6) - mod(t*" + (0.12 / SPEED).toFixed(4) + ", 2.6) + 0.5;",
    "  a *= 1.0 + sheen * 0.5 * f * exp(-band*band*80.0);",
    // scroll: the horse comes apart into dust and settles as the chart
    "  if (m > 0.0) {",
    "    eg = eio(clamp(m*1.75 - aH.x*0.75, 0.0, 1.0));",
    "    float sc = sin(PI*eg) * (24.0 + 70.0*aR2.y);",
    "    float ang = aR2.z*2.0*PI;",
    "    pos = mix(pos, aC.xy, eg) + vec2(cos(ang), sin(ang))*sc;",
    "    a = mix(mix(a, dust, sin(PI*eg)), aC.z, smoothstep(0.6, 1.0, eg));",
    "    sz = mix(sz, 2.0, eg);",
    "  }",
    // leaving for a section: back into the point, the shading first and the outline last,
    // slow away from its place and fast into the point (the way in, reversed)
    "  if (xt > 0.0) {",
    "    float xf = clamp((xt - (aH.w > 0.5 ? 0.1 : 0.0) - 0.1*aR.w) / 0.42, 0.0, 1.0);",
    "    xe = xf*xf*xf;",
    "    vec2 xd = pos - s;",
    "    pos = s + xd*(1.0 - xe) + vec2(-xd.y, xd.x) * sin(PI*xe) * (aR.z - 0.5) * 0.44;",
    "    a = mix(a, dust, smoothstep(0.0, 0.4, xe));",
    "    sz = mix(sz, 2.2, xe);",
    "  }",
    "  a *= xo;",
    // pointer: the dots part around it and close again behind it
    "  if (ptr.z > 0.0) {",
    "    vec2 dp = pos - ptr.xy; float dist = length(dp);",
    "    float q = 1.0 - smoothstep(0.0, prad, dist);",
    "    vec2 dir = dp / max(dist, 0.001);",
    "    pos += (dir * q * q * prad * 0.3 * (0.35 + 1.3*aR.x) + vec2(-dir.y, dir.x) * q * prad * 0.16 * (aR.y - 0.5)) * ptr.z;",
    "    a *= 1.0 + 0.6 * q * ptr.z;",
    "  }",
    "  gl_Position = vec4(pos.x / res.x * 2.0 - 1.0, 1.0 - pos.y / res.y * 2.0, 0.0, 1.0);",
    // a point is never drawn under one device pixel, so in a small slot on a low-density
    // screen (phones give the horse a smaller slot) the dots would overlap and brighten:
    // dim them by the area they gain instead
    "  float ps = sz * dpr * sm;",
    "  gl_PointSize = max(1.0, ps);",
    "  va = a * am * min(1.0, ps * ps);",
    "  vc = mix(dcol, hcol, smoothstep(0.6, 1.0, e) * (1.0 - smoothstep(0.0, 0.5, eg)) * (1.0 - smoothstep(0.0, 0.4, xe)));",
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
    "uniform float t, dpr, sm, am, prad, pitch, visP, visI, visH, xt, xo;",
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
    "  a *= mix(1.0, aP.w < 1.5 ? visP : aP.w < 2.5 ? visI : visH, step(0.999, f));",
    // leaving for a section: the text goes back into the point a moment before the horse
    "  float xf = clamp((xt - 0.1*rq.y) / 0.42, 0.0, 1.0);",
    "  float xe = xf*xf*xf;",
    "  vec2 xd = pos - s;",
    "  pos = s + xd*(1.0 - xe) + vec2(-xd.y, xd.x) * sin(PI*xe) * (rq.y - 0.5) * 0.44;",
    "  a = mix(a, dust, smoothstep(0.0, 0.4, xe)) * xo;",
    "  e *= 1.0 - xe;",
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
  if (!gl) { fail(); return; }
  function shader(type, src) { var o = gl.createShader(type); gl.shaderSource(o, src); gl.compileShader(o); return o; }
  // first: the attribute always fed from a buffer takes slot 0, which some drivers need
  // enabled (the horse's aC is fed only if a chart is built)
  function program(vs, first) {
    var p = gl.createProgram();
    gl.attachShader(p, shader(gl.VERTEX_SHADER, vs));
    gl.attachShader(p, shader(gl.FRAGMENT_SHADER, FS));
    gl.bindAttribLocation(p, 0, first);
    gl.linkProgram(p);
    return gl.getProgramParameter(p, gl.LINK_STATUS) ? p : null;
  }
  function uniforms(p, names) { var u = {}; names.forEach(function (n) { u[n] = gl.getUniformLocation(p, n); }); return u; }
  var prog = program(VS, "aH");
  if (!prog) { fail(); return; }
  var progT = program(VS_TEXT, "aP");
  var U = uniforms(prog, ["res", "cc", "hb", "ptr", "hcol", "dcol", "dim", "t", "m", "dpr", "pitch", "sm", "am", "prad", "sheen", "kk", "xt", "xo"]);
  var UT = progT ? uniforms(progT, ["res", "cc", "ptr", "tcol", "dcol", "t", "dpr", "sm", "am", "prad", "pitch", "visP", "visI", "visH", "kk", "xt", "xo"]) : null;
  var MAX_ATTRIBS = Math.min(8, gl.getParameter(gl.MAX_VERTEX_ATTRIBS));
  // both programs share the attribute slots: each draw switches them to its own buffers
  // (each attribute's slot is looked up once, not on every frame)
  var slots = {};
  function slot(p, name) {
    var k = (p === prog ? "h:" : "t:") + name;
    if (!(k in slots)) slots[k] = gl.getAttribLocation(p, name);
    return slots[k];
  }
  function attribs(list) {
    for (var i = 0; i < MAX_ATTRIBS; i++) gl.disableVertexAttribArray(i);
    list.forEach(function (a) {
      var l = slot(a[0], a[1]);
      if (l < 0) return;
      gl.bindBuffer(gl.ARRAY_BUFFER, a[2]);
      gl.enableVertexAttribArray(l);
      gl.vertexAttribPointer(l, a[3], gl.FLOAT, false, a[4], a[5]);
    });
  }

  var N = 0, PW = 0, PH = 0, px = null, sBuf = null, cBuf = null, chartAttr = null, chartReady = false, order = null;
  var TS = 1.25;            // the text is sampled at 1.25 particles per CSS pixel
  var tBuf = null, TN = 0, textOn = false, T_P = 3, T_I = 4, T_H = 3, crispP = false, crispI = false, crispH = false;
  var W = 0, H = 0, DPR = 1, box = null, cbox = null;
  var t0 = 0, running = false, visible = true, lastP = -1, frameNo = 0;
  var ptr = { x: -1e4, y: -1e4, sx: -1e4, sy: -1e4, s: 0, last: -1e9 };
  // leaving for a section (owner-approved, 1 Nov 2026): xMode 1 on the way into the point,
  // 2 on the way back out (the page shown again from the back/forward cache), 3 while the
  // real text takes over again; xT is how far into the way in, in seconds
  var EXIT = 0.64, BACK = 0.5, xMode = 0, xT = 0, xO = 1, xVis = 1, xS = 0, xLast = 0, xGo = null;

  /* ---------- the particles, from the map ---------- */
  function build(image) {
    PW = image.naturalWidth; PH = image.naturalHeight;
    var c = document.createElement("canvas"); c.width = PW; c.height = PH;
    var x = c.getContext("2d", { willReadFrequently: true });
    x.drawImage(image, 0, 0);
    var d = x.getImageData(0, 0, PW, PH).data;
    // the inked pixels, counted first so they go straight into a typed array (a plain array
    // grown pixel by pixel took most of this function's time on a phone)
    var n = PW * PH, i, k = 0;
    for (i = 0; i < n; i++) if (d[i * 4] > 10) k++;
    var idx = new Uint32Array(k);
    for (i = 0, k = 0; i < n; i++) if (d[i * 4] > 10) idx[k++] = i;
    // shuffled, so the first third (the halo pass) is a fair sample of the whole drawing
    var r = rng(1412);
    for (var j = idx.length - 1; j > 0; j--) { var w = Math.floor(r() * (j + 1)), tmp = idx[j]; idx[j] = idx[w]; idx[w] = tmp; }
    N = idx.length;
    px = idx;
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
    // the chart's places (cBuf) are made only if a chart is ever built (buildChart)
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

  /* ---------- the headline, the index and the header, character by character ---------- */
  // Paints one thing where the page sets it (paint(x) draws in page pixels) and returns its
  // inked pixels as [x, y, ink, group, delay, duration] records (six floats each), in stage
  // pixels. ink scales the tone it settles at (the legal line is lighter than the headline);
  // the delay is given u, 0 to 1 across ref (the thing itself unless another box is given).
  function sample(b, paint, group, delay, dur, r, ink, ref) {
    var s = stage.getBoundingClientRect(), pad = 4;
    var w = Math.ceil((b.width + pad * 2) * TS), h = Math.ceil((b.height + pad * 2) * TS);
    if (w < 2 || h < 2) return new Float32Array(0);
    var c = document.createElement("canvas"); c.width = w; c.height = h;
    var x = c.getContext("2d", { willReadFrequently: true }), d;
    x.setTransform(TS, 0, 0, TS, (pad - b.left) * TS, (pad - b.top) * TS);
    x.fillStyle = "#fff";
    try { paint(x); d = x.getImageData(0, 0, w, h).data; } catch (e) { return new Float32Array(0); }
    var n = 0, k;
    for (k = 3; k < d.length; k += 4) if (d[k] >= 16) n++;
    ref = ref || b;
    var out = new Float32Array(n * 6), o = 0, x0 = b.left - pad - s.left, y0 = b.top - pad - s.top;
    var u0 = ref.left - s.left, rw = Math.max(1, ref.width), xx, yy, px;
    for (yy = 0, k = 3; yy < h; yy++) for (xx = 0; xx < w; xx++, k += 4) {
      if (d[k] < 16) continue;
      px = x0 + (xx + 0.5) / TS;
      out[o] = px; out[o + 1] = y0 + (yy + 0.5) / TS; out[o + 2] = Math.min(1, d[k] / 255 * 1.05) * ink;
      out[o + 3] = group; out[o + 4] = delay((px - u0) / rw, r); out[o + 5] = dur;
      o += 6;
    }
    return out;
  }

  // the characters of el, each in its own font, size and weight
  function sampleText(el, group, delay, dur, r, ink, ref) {
    return sample(el.getBoundingClientRect(), function (x) {
      var cs = getComputedStyle(el), size = parseFloat(cs.fontSize);
      x.font = cs.fontWeight + " " + size + "px " + cs.fontFamily;
      x.textBaseline = "alphabetic";
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
    }, group, delay, dur, r, ink, ref);
  }

  // the header's mark (its transparent PNG, by its alpha), where the page shows it
  function sampleImage(img, group, delay, dur, r, ink, ref) {
    if (!img.complete || !img.naturalWidth) return new Float32Array(0);
    var b = img.getBoundingClientRect();
    return sample(b, function (x) { x.drawImage(img, b.left, b.top, b.width, b.height); }, group, delay, dur, r, ink, ref);
  }
  function shown(el) { var b = el.getBoundingClientRect(); return b.width > 0 && b.height > 0; }

  // how far a colour token stands from the ground, against the ink's (for the legal line)
  function tone(name) {
    var v = getComputedStyle(root).getPropertyValue(name).trim(), m = /^#([0-9a-f]{6})$/i.exec(v);
    if (!m) return -1;
    var n = parseInt(m[1], 16);
    return (((n >> 16) & 255) + ((n >> 8) & 255) + (n & 255)) / 765;
  }
  function weight(name) {
    var g = tone("--ground"), c = tone(name), k = tone("--ink");
    if (g < 0 || c < 0 || k < 0 || Math.abs(k - g) < 0.05) return 1;
    return Math.max(0.2, Math.min(1, Math.abs(c - g) / Math.abs(k - g)));
  }

  function buildText() {
    var r = rng(5150), parts = [], total = 0;
    // the headline first, left to right as it reads; then the index, item by item
    parts.push(sampleText(headline, 1, function (u, rr) { return 0.15 + u * 0.9 + rr() * 0.3; }, 1.6, r, 1));
    T_P = 0.15 + 0.9 + 0.3 + 1.6;
    links.forEach(function (el, k) {
      parts.push(sampleText(el, 2, function (u, rr) { return 0.95 + k * 0.09 + u * 0.3 + rr() * 0.2; }, 1.3, r, 1));
    });
    T_I = 0.95 + Math.max(0, links.length - 1) * 0.09 + 0.3 + 0.2 + 1.3;
    // the header with the headline, left to right across the bar: the mark, the name, then
    // the legal line in its lighter tone
    if (bar) {
      var row = bar.querySelector(".wrap") || bar, ref = row.getBoundingClientRect();
      var hd = function (u, rr) { return 0.3 + Math.max(0, Math.min(1, u)) * 0.8 + rr() * 0.3; };
      Array.prototype.forEach.call(bar.querySelectorAll(".brand__mark img"), function (el) {
        if (shown(el)) parts.push(sampleImage(el, 3, hd, 1.6, r, 1, ref));
      });
      Array.prototype.forEach.call(bar.querySelectorAll(".brand__name"), function (el) {
        parts.push(sampleText(el, 3, hd, 1.6, r, 1, ref));
      });
      var legal = weight("--ink-3");
      Array.prototype.forEach.call(bar.querySelectorAll(".site-header__legal a"), function (el) {
        parts.push(sampleText(el, 3, hd, 1.6, r, legal, ref));
      });
    }
    T_H = 0.3 + 0.8 + 0.3 + 1.6;
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
    textAt = textKey();
  }

  // Sampling the text takes a moment (about 10ms on a laptop, 30 to 45ms on a phone), too
  // long to spend as the hero starts to leave: the particles from the last time are kept and
  // sampled again only if something they came from has moved or the theme has changed.
  // textKey is where each piece stands, its size and the theme; freshText samples again only
  // if it differs.
  var textAt = null;
  function textKey() {
    var s = stage.getBoundingClientRect(), k = [theme()], els = [headline].concat(links);
    if (bar) els = els.concat(Array.prototype.slice.call(bar.querySelectorAll(".wrap, .brand__mark img, .brand__name, .site-header__legal a")));
    els.forEach(function (el) {
      var b = el.getBoundingClientRect();
      k.push(Math.round((b.left - s.left) * 8), Math.round((b.top - s.top) * 8), Math.round(b.width * 8), Math.round(b.height * 8),
        el.tagName === "IMG" ? (el.complete && el.naturalWidth ? 1 : 0) : 1);
    });
    return k.join(",");
  }
  function freshText() { if (!tBuf || textKey() !== textAt) buildText(); }

  // the real text takes over for good; the page no longer needs the forming state
  function finishText() {
    textOn = false;
    hero.classList.add("crisp-h1", "crisp-ix");
    if (bar) bar.classList.add("crisp-hd");
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
    if (!cBuf) { cBuf = gl.createBuffer(); chartAttr = new Float32Array(N * 3); }
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
  // The homepage keeps the horse (owner, 31 Oct 2026): it never turns into the chart, even
  // where the hero is taller than the screen. The engine keeps the chart for a hero that
  // should have one; set MORPH to bring it back.
  var MORPH = false;
  function hasTrack() { return MORPH && hero.getBoundingClientRect().height - H > 1; }

  function progress() {
    if (reduce || !MORPH) return 0;
    var r = hero.getBoundingClientRect(), span = r.height - H;
    return span > 0 ? clamp01(-r.top / span) : 0;
  }

  function draw(t, p) {
    var m = reduce ? 0 : smooth(0.15, 0.75, p);
    if (m > 0 && t < DONE) { t0 -= (DONE - t) / SPEED * 1000; t = DONE; } // scrolling finishes the drawing
    if (m > 0 && !chartReady) buildChart();
    var col = COLOURS[theme()];
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(prog);
    attribs(cBuf ? [[prog, "aH", sBuf, 4, 16, 0], [prog, "aC", cBuf, 3, 12, 0]] : [[prog, "aH", sBuf, 4, 16, 0]]);
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
    gl.uniform1f(U.xt, xT); gl.uniform1f(U.xo, xO);
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
    if (!xMode) {
      var cp = t >= T_P, ci = t >= T_I, ch = t >= T_H;
      if (cp !== crispP) { crispP = cp; hero.classList.toggle("crisp-h1", cp); }
      if (ci !== crispI) { crispI = ci; hero.classList.toggle("crisp-ix", ci); }
      if (ch !== crispH) { crispH = ch; if (bar) bar.classList.toggle("crisp-hd", ch); }
      if (t >= Math.max(T_P, T_I, T_H) + 0.6) { finishText(); return; }
    }
    if (!TN) return;
    gl.useProgram(progT);
    attribs([[progT, "aP", tBuf, 4, 24, 0], [progT, "aQ", tBuf, 2, 24, 16]]);
    gl.uniform2f(UT.res, W, H); gl.uniform1f(UT.dpr, DPR);
    gl.uniform2f(UT.cc, W / 2, H / 2);
    gl.uniform3f(UT.ptr, ptr.sx, ptr.sy, ptr.s); gl.uniform1f(UT.prad, W > 860 ? 95 : 70);
    gl.uniform1f(UT.t, t); gl.uniform1f(UT.pitch, 1 / TS);
    if (xMode) {
      gl.uniform1f(UT.visP, xVis); gl.uniform1f(UT.visI, xVis); gl.uniform1f(UT.visH, xVis);
    } else {
      gl.uniform1f(UT.visP, 1 - smooth(T_P, T_P + 0.45, t)); gl.uniform1f(UT.visI, 1 - smooth(T_I, T_I + 0.45, t));
      gl.uniform1f(UT.visH, 1 - smooth(T_H, T_H + 0.45, t));
    }
    gl.uniform1f(UT.xt, xT); gl.uniform1f(UT.xo, xO);
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
    var held = now - ptr.last < 1200;
    ptr.s += ((held ? 1 : 0) - ptr.s) * 0.08;
    // the pointer's hold fades to nothing rather than ever closer to it, so a settled horse
    // goes back to its cheapest drawing (at a thousandth the dots stir by under 0.05px)
    if (!held && ptr.s < 0.001) ptr.s = 0;
    ptr.sx += (ptr.x - ptr.sx) * 0.22; ptr.sy += (ptr.y - ptr.sy) * 0.22;
    var t = (now - t0) / 1000 * SPEED, p = progress();
    if (xMode) exitClock(now);
    // once settled and untouched, half the frame rate is plenty for the band of light
    else if (t > DONE + 0.5 && ptr.s < 0.01 && p === lastP && (frameNo++ & 1)) return;
    draw(t, p);
    if (xMode === 1 && xT >= EXIT) go();
  }

  /* ---------- leaving for a section: everything goes back into the point ---------- */
  // Clicking a link to another page (a section in an open group, the legal line)
  // takes the horse, the headline, the index and the header back into the point at the
  // centre they came out of, the way in reversed (0.64s), then opens the page, which opens
  // out of the same point (assets/section-scene.js, html.arrive). Not under reduced motion,
  // nor before the particles are drawing; a link opened in a new tab or window goes as usual.
  // Its clock moves at most 1/20s a frame, so a frame held up pauses it rather than skipping it.
  function exitClock(now) {
    var dt = xLast ? Math.max(0, Math.min(now - xLast, 50)) / 1000 : 0;
    xLast = now;
    if (xMode === 1) xT = Math.min(EXIT, xT + dt);
    else if (xMode === 2) {
      xT = Math.max(0, xT - dt * EXIT / BACK);
      if (xT <= 0) {
        // back in place: the real page takes over again as the text particles fade (as when
        // it first formed)
        xMode = 3; xS = 0;
        hero.classList.add("crisp-h1", "crisp-ix");
        if (bar) bar.classList.add("crisp-hd");
        root.classList.add("hero-returning", "hero-formed");
        root.classList.remove("hero-leaving", "hero-forming");
      }
    } else if (xMode === 3) {
      xS += dt; xVis = 1 - smooth(0, 0.45, xS);
      if (xS >= 0.5) { xMode = 0; xVis = 1; textOn = false; root.classList.remove("hero-returning"); }
    }
    xO = 1 - smooth(EXIT - 0.12, EXIT, xT);
  }

  function go() {
    if (xMode !== 1 || !xGo) return;
    var href = xGo;
    xGo = null;
    location.href = href;
  }

  function leave(href) {
    if (xMode === 1) { xGo = href; return; }
    // the text as it stands, so it can go back into the point with the horse (sampled again
    // only if it moved since: usually done already as the pointer went down on the link)
    if (progT && !textOn) { freshText(); textOn = true; }
    if (xMode !== 2) xT = 0;
    xMode = 1; xLast = 0; xGo = href; xVis = 1;
    root.classList.add("hero-leaving");
    root.classList.remove("hero-returning");
    ptr.last = -1e9;
    try { sessionStorage.setItem("andra-arrive", String(Date.now())); } catch (e) { /* private mode */ }
    // fetch the page while the hero leaves (the speculation rules may have already)
    var l = document.createElement("link");
    l.rel = "prefetch"; l.href = href;
    document.head.appendChild(l);
    // and the section's sphere texture, so it is in the cache when that page asks for it
    var next = canvas.getAttribute("data-next");
    if (next && !leave.next) { leave.next = new Image(); leave.next.src = next; }
    exitClock(performance.now());
    start();
    // if frames stall (a hidden tab), go anyway
    setTimeout(go, (EXIT - xT) * 1000 + 600);
  }

  // the link a click or press would leave by, if the hero takes it back into the point
  function exitLink(e) {
    if (reduce || e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return null;
    var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
    if (!a || a.target || a.hasAttribute("download") || a.origin !== location.origin) return null;
    if (a.pathname === location.pathname || /\.pdf$/i.test(a.pathname)) return null;
    if (!hero.classList.contains("is-live")) return null;
    return a;
  }
  function onClick(e) {
    var a = exitLink(e);
    if (!a) return;
    e.preventDefault();
    leave(a.href);
  }
  // the pointer going down on such a link: the text is made ready then, before the click, so
  // the way back into the point starts without stopping to sample it
  function onPress(e) { if (progT && !textOn && !xMode && exitLink(e)) freshText(); }
  function start() { if (!running && !reduce && visible && !document.hidden) { running = true; requestAnimationFrame(loop); } }
  function stop() { running = false; }
  function still() { draw((performance.now() - t0) / 1000 * SPEED, progress()); }

  // everything the text particles are sampled from is in: the headline's font (the header
  // and the index use the same) and the header's mark as the page shows it
  function textIn() {
    if (!document.fonts || !document.fonts.check) return false;
    var marks = bar ? Array.prototype.filter.call(bar.querySelectorAll(".brand__mark img"), shown) : [];
    if (marks.some(function (img) { return !img.complete || !img.naturalWidth; })) return false;
    var cs = getComputedStyle(headline);
    try { return document.fonts.check(cs.fontWeight + " 32px " + cs.fontFamily); } catch (e) { return false; }
  }

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
    if (!N) { fail(); return; }
    // the headline and index form too, unless the page already gave up waiting (HERO_BOOT)
    var withText = !!(progT && headline && root.classList.contains("hero-forming") && !reduce);
    if (!withText) giveUp();
    hero.classList.add("is-live");
    measure();
    // the text, sampled before the clock starts when its font and the mark are already in
    // (the usual case), so the flight never stops a moment to sample it once under way
    var early = withText && textIn();
    if (early) { buildText(); textOn = true; }
    t0 = performance.now();
    if (withText && !early) {
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
    document.addEventListener("click", onClick);
    document.addEventListener("pointerdown", onPress, { passive: true });
    // shown again from the back/forward cache after leaving: everything comes back out of
    // the point (the way in, reversed again, 0.5s)
    window.addEventListener("pageshow", function (e) {
      if (!e.persisted || xMode !== 1) return;
      xGo = null; xMode = 2; xLast = 0;
      start();
    });
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (es) { visible = es[0].isIntersecting; if (visible) start(); else stop(); }).observe(hero);
    }
    document.addEventListener("visibilitychange", function () { if (document.hidden) stop(); else start(); });
    // a new theme mid-forming: the header's mark and the legal line's tone follow it
    new MutationObserver(function () { if (textOn) buildText(); if (!running) still(); }).observe(root, { attributes: true, attributeFilter: ["data-theme"] });
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
    if (image.naturalWidth) begin(image); else fail();
  } else {
    if (!image) { image = new Image(); image.decoding = "async"; image.src = canvas.getAttribute("data-src"); }
    image.addEventListener("load", function () { begin(image); });
    // HERO_BOOT retries the PNG when the WebP copy does not decode: give up only when
    // nothing is left loading
    image.addEventListener("error", function () { if (image.complete && !image.naturalWidth) fail(); });
  }
})();
