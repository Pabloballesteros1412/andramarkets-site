/* Andra Markets: the Earth on the World markets page (world/; owner-approved preview, 13 Nov 2026).
   The real Earth, turning slowly: its surface from NASA's Blue Marble and night lights (in grey,
   shaded by relief, lit where it is day right now, with a thin atmosphere at the edge), drawn in
   WebGL. Over it, painted on a flat map and wrapped round the globe, every border as a hairline
   and the markets' countries filled green or red for their last session. A ring goes out from
   an exchange that is trading now (regular hours; holidays are not known). Arcs join the markets
   whose weekly returns move together (tools/build_site.py, world_globe). Pointing at a country
   lights it and shows its index and its day, month and year; clicking it adds it to the
   comparison below, as its button does. A 2D canvas over the WebGL one carries arcs, rings and
   words. With no WebGL the section stays hidden and the page is as it was. It turns only while
   on screen and not at all under reduced motion. */
(function () {
  "use strict";
  var box = document.querySelector(".wm-globe"), src = document.getElementById("wg-data"), GEO = window.ANDRA_GEO;
  if (!box || !src || !GEO) return;
  var D = JSON.parse(src.textContent), MK = D.markets, N = MK.length, LINKS = D.links;
  var base = (document.body.getAttribute("data-base") || "") + "assets/";
  var TEX = { day: base + D.tex.day, night: base + D.tex.night, topo: base + D.tex.topo };
  var cv = box.querySelector(".wm-globe__top"), read = box.querySelector(".wm-globe__read"), stats = box.querySelector(".wm-globe__stats");
  var TAU = Math.PI * 2, RAD = Math.PI / 180, MINUS = "−", INK = "242,243,243", UP = "31,210,122", DN = "255,75,82";
  var MONO = '"Geist Mono", ui-monospace, Menlo, monospace';
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  // regular trading hours in UTC, [open, close] in minutes; a lunch break is ignored
  var HOURS = { USA: [870, 1260], CAN: [870, 1260], MEX: [870, 1260], BRA: [780, 1200], ARG: [840, 1200], GBR: [480, 990], DEU: [480, 990], FRA: [480, 990], ITA: [480, 990], ESP: [480, 990], NLD: [480, 990], CHE: [480, 990], SWE: [480, 990], TUR: [420, 900], ISR: [479, 925], ZAF: [420, 900], IND: [225, 600], CHN: [90, 420], HKG: [90, 480], JPN: [0, 390], KOR: [0, 390], TWN: [60, 330], IDN: [120, 540], SGP: [60, 540], AUS: [1380, 1800],
    NOR: [480, 925], DNK: [480, 960], FIN: [480, 990], BEL: [480, 990], AUT: [480, 990], IRL: [480, 990], PRT: [480, 990], GRC: [510, 920], EST: [480, 840], LVA: [480, 840], LTU: [480, 840], MYS: [60, 540], NZL: [1260, 1665], POL: [480, 965], ROU: [465, 885], COL: [870, 1260], THA: [180, 570], VNM: [120, 465], SAU: [420, 720], ARE: [360, 660], QAT: [390, 615], KWT: [360, 580], PHL: [90, 420], CHL: [750, 1200], PER: [870, 1260] };
  // Sunday to Thursday in Israel and the Gulf
  var SUNDAY = { ISR: 1, SAU: 1, QAT: 1, KWT: 1 };
  function pct(v, d) { if (v == null) return "n/a"; var r = Number(v.toFixed(d)); return (r > 0 ? "+" : r < 0 ? MINUS : "") + Math.abs(r).toFixed(d) + "%"; }
  function cls(v) { return v > 0 ? "up" : v < 0 ? "dn" : ""; }
  function vec(lon, lat, h) { var c = Math.cos(lat * RAD) * (h || 1); return [c * Math.sin(lon * RAD), Math.sin(lat * RAD) * (h || 1), c * Math.cos(lon * RAD)]; }
  function isOpen(iso, now) {
    var h = HOURS[iso]; if (!h) return false;
    var m = now.getUTCHours() * 60 + now.getUTCMinutes(), day = now.getUTCDay();
    // Sydney and Wellington open on the UTC evening before their own day
    if (h[1] > 1440) { var late = m >= h[0], early = m < h[1] - 1440, d = late ? (day + 1) % 7 : day; return (late || early) && d >= 1 && d <= 5; }
    if (SUNDAY[iso]) return day >= 0 && day <= 4 && m >= h[0] && m < h[1];
    return day >= 1 && day <= 5 && m >= h[0] && m < h[1];
  }
  var P = MK.map(function (m) { return vec(m.lon, m.lat); });
  var ARC = LINKS.map(function (l) {
    var a = P[l[0]], b = P[l[1]], om = Math.acos(Math.max(-1, Math.min(1, a[0] * b[0] + a[1] * b[1] + a[2] * b[2]))), so = Math.sin(om) || 1, out = [], seg = 8 + Math.round(om * 16);
    for (var k = 0; k <= seg; k++) { var t = k / seg, wa = Math.sin((1 - t) * om) / so, wb = Math.sin(t * om) / so, lift = 1 + Math.min(0.22, 0.03 + 0.16 * om) * Math.sin(Math.PI * t); out.push([(a[0] * wa + b[0] * wb) * lift, (a[1] * wa + b[1] * wb) * lift, (a[2] * wa + b[2] * wb) * lift]); }
    return out;
  });
  var mine = MK.map(function () { return []; }); LINKS.forEach(function (l, n) { mine[l[0]].push(n); mine[l[1]].push(n); });

  var S = {}, rotY = 20 * RAD, rotX = 0.42, cosY, sinY, cosX, sinX, PERSP = 0, hover = -1, held = -1, drag = null, Q = [], sprites, shell, now = new Date(), SUN, OPEN = [];
  function clockwork() {
    now = new Date();
    var doy = Math.floor((now - Date.UTC(now.getUTCFullYear(), 0, 0)) / 864e5), decl = -23.44 * Math.cos(TAU * (doy + 10) / 365), lon = -((now.getUTCHours() + now.getUTCMinutes() / 60) - 12) * 15;
    SUN = vec(lon, decl); OPEN = MK.map(function (m) { return isOpen(m.iso, now); });
    stats.textContent = N + " markets · " + OPEN.filter(Boolean).length + " trading now · " + ("0" + now.getUTCHours()).slice(-2) + ":" + ("0" + now.getUTCMinutes()).slice(-2) + " UTC · closes to " + D.asof;
  }
  function proj(p) { var x = p[0] * cosY + p[2] * sinY, z = -p[0] * sinY + p[2] * cosY, y = p[1] * cosX - z * sinX, zz = p[1] * sinX + z * cosX, f = 1 / (1 + PERSP - zz * PERSP); return [S.cx + x * S.rad * f, S.cy - y * S.rad * f, zz, f]; }
  function label(text, x, y, align, color, size) { var c = S.c; c.font = "400 " + (size || 10) + "px " + MONO; c.textAlign = align || "left"; c.fillStyle = color; if ("letterSpacing" in c) c.letterSpacing = "1px"; c.fillText(String(text).toUpperCase(), x, y); }
  function sprite(rgb) { var el = document.createElement("canvas"), n = 64; el.width = el.height = n; var c = el.getContext("2d"), g = c.createRadialGradient(n / 2, n / 2, 0, n / 2, n / 2, n / 2); g.addColorStop(0, "rgba(" + rgb + ",.95)"); g.addColorStop(0.12, "rgba(" + rgb + ",.5)"); g.addColorStop(0.4, "rgba(" + rgb + ",.12)"); g.addColorStop(1, "rgba(" + rgb + ",0)"); c.fillStyle = g; c.fillRect(0, 0, n, n); return el; }
  /* The surface: the real Earth in WebGL under the 2D canvas. Day side from NASA's Blue Marble,
     night side from its city lights, shaded by relief, with a thin atmosphere at the edge. */
  var GLc = box.querySelector(".wm-globe__gl"), gl = GLc.getContext("webgl", { alpha: true, antialias: true, premultipliedAlpha: true }), U = {}, overTex = null;
  var VS = "attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}";
  var FS = "precision highp float;uniform vec2 ctr;uniform float rad,cy,sy,cx,sx;uniform vec3 sun;uniform sampler2D day,night,topo,over;" +
    "const float PI=3.14159265;" +
    "vec3 obj(vec3 v){float p1=v.y*cx+v.z*sx;float z1=-v.y*sx+v.z*cx;return vec3(v.x*cy-z1*sy,p1,v.x*sy+z1*cy);}" +
    "void main(){vec2 q=(gl_FragCoord.xy-ctr)/rad;float r2=dot(q,q);" +
    " if(r2>1.){float d=sqrt(r2)-1.;float g=exp(-d*9.)*.3+exp(-d*40.)*.55;vec3 n=obj(normalize(vec3(q,0.)));float lit=.3+.7*smoothstep(-.3,.5,dot(n,sun));g*=lit;gl_FragColor=vec4(vec3(.82,.9,1.)*g,g);return;}" +
    " float z=sqrt(1.-r2);vec3 p=obj(vec3(q,z));vec2 uv=vec2(atan(p.x,p.z)/(2.*PI)+.5,.5-asin(clamp(p.y,-1.,1.))/PI);" +
    " float e=1./1024.;float h=texture2D(topo,uv).r;float hx=texture2D(topo,uv+vec2(e,0.)).r-texture2D(topo,uv-vec2(e,0.)).r;float hy=texture2D(topo,uv+vec2(0.,e)).r-texture2D(topo,uv-vec2(0.,e)).r;" +
    " float sd=dot(p,sun);float dayf=smoothstep(-.14,.24,sd);" +
    " float relief=1.+clamp(hx*-7.+hy*6.,-.6,.8);" +
    " float d=pow(texture2D(day,uv).r,.8)*1.55*relief;" +
    " float n=pow(texture2D(night,uv).r,1.3)*2.6;" +
    " float base=mix(.03+d*.16,d*(.34+.8*max(sd,0.)),dayf);" +
    " vec3 col=vec3(base)*vec3(.93,.97,1.)+vec3(1.,.94,.84)*n*(1.-dayf);" +
    " vec4 ov=texture2D(over,uv);col=mix(col,ov.rgb*(.42+base*1.5),ov.a);" +
    " float rim=pow(1.-z,3.);col+=vec3(.75,.86,1.)*rim*(.14+.5*dayf);" +
    " gl_FragColor=vec4(col,1.);}";
  function tex(unit, src) {
    var t = gl.createTexture(), im = new Image();
    gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.LUMINANCE, 1, 1, 0, gl.LUMINANCE, gl.UNSIGNED_BYTE, new Uint8Array([0]));
    im.onload = function () {
      gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.LUMINANCE, gl.LUMINANCE, gl.UNSIGNED_BYTE, im);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.generateMipmap(gl.TEXTURE_2D); once();
    };
    im.src = src;
  }
  if (gl) (function () {
    function sh(type, src) { var o = gl.createShader(type); gl.shaderSource(o, src); gl.compileShader(o); if (!gl.getShaderParameter(o, gl.COMPILE_STATUS)) console.log("SHADER", gl.getShaderInfoLog(o)); return o; }
    var prog = gl.createProgram(); gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(prog); gl.useProgram(prog);
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer()); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(prog, "a"); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    ["ctr", "rad", "cy", "sy", "cx", "sx", "sun", "day", "night", "topo", "over"].forEach(function (n) { U[n] = gl.getUniformLocation(prog, n); });
    gl.uniform1i(U.day, 0); gl.uniform1i(U.night, 1); gl.uniform1i(U.topo, 2); gl.uniform1i(U.over, 3); overTex = gl.createTexture();
    tex(0, TEX.day); tex(1, TEX.night); tex(2, TEX.topo);
  })();
  /* The countries, painted on a flat map and laid over the surface: every border as a hairline,
     the markets' countries filled green or red for their last session, the one in focus brighter. */
  var map = document.createElement("canvas"); map.width = 4096; map.height = 2048;
  function trace(c, r) { var W = map.width, H = map.height, px = null; for (var i = 0; i < r.length; i += 2) { var x = (r[i] + 180) / 360 * W, y = (90 - r[i + 1]) / 180 * H; if (px === null || Math.abs(x - px) > W / 2) c.moveTo(x, y); else c.lineTo(x, y); px = x; } }
  function paint() {
    if (!gl || !overTex) return;
    var c = map.getContext("2d"), f = hover >= 0 ? hover : held;
    c.clearRect(0, 0, map.width, map.height);
    c.beginPath(); GEO.b.forEach(function (r) { trace(c, r); }); c.strokeStyle = "rgba(242,243,243,.22)"; c.lineWidth = 1.4; c.stroke();
    MK.forEach(function (m, i) {
      var rings = GEO.c[m.iso]; if (!rings) return;
      var v = m.d1 || 0, a = (0.42 + Math.min(0.4, Math.abs(v) * 0.28)) * (f >= 0 && f !== i ? 0.55 : 1) + (f === i ? 0.18 : 0);
      c.beginPath(); rings.forEach(function (r) { trace(c, r); c.closePath(); });
      var tone = m.d1 == null ? INK : v >= 0 ? UP : DN;  // no figure yet: no colour
      c.fillStyle = "rgba(" + tone + "," + Math.min(0.95, m.d1 == null ? a * 0.5 : a).toFixed(2) + ")"; c.fill("evenodd");
      c.strokeStyle = f === i ? "rgba(242,243,243,.95)" : "rgba(" + tone + ",.9)"; c.lineWidth = f === i ? 3 : 1.6; c.stroke();
    });
    gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, overTex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, map);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE); gl.generateMipmap(gl.TEXTURE_2D);
  }
  // Which market's country is under a point of the screen: back from the screen to longitude and latitude.
  function countryAt(x, y) {
    var qx = (x - S.cx) / S.rad, qy = -(y - S.cy) / S.rad, r2 = qx * qx + qy * qy; if (r2 > 1) return -1;
    var z = Math.sqrt(1 - r2), p1 = qy * cosX + z * sinX, z1 = -qy * sinX + z * cosX, p0 = qx * cosY - z1 * sinY, p2 = qx * sinY + z1 * cosY;
    var lon = Math.atan2(p0, p2) / RAD, lat = Math.asin(Math.max(-1, Math.min(1, p1))) / RAD;
    for (var i = 0; i < N; i++) { var rings = GEO.c[MK[i].iso] || [], inside = false; for (var k = 0; k < rings.length; k++) { var r = rings[k]; for (var a = 0, b = r.length - 2; a < r.length; b = a, a += 2) { if ((r[a + 1] > lat) !== (r[b + 1] > lat) && lon < (r[b] - r[a]) * (lat - r[a + 1]) / (r[b + 1] - r[a + 1]) + r[a]) inside = !inside; } } if (inside) return i; }
    return -1;
  }
  function surface() {
    if (!gl) return;
    var d = S.dpr;
    gl.viewport(0, 0, GLc.width, GLc.height); gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.uniform2f(U.ctr, S.cx * d, (S.h - S.cy) * d); gl.uniform1f(U.rad, S.rad * d);
    gl.uniform1f(U.cy, cosY); gl.uniform1f(U.sy, sinY); gl.uniform1f(U.cx, cosX); gl.uniform1f(U.sx, sinX); gl.uniform3f(U.sun, SUN[0], SUN[1], SUN[2]);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }
  function size() {
    var dpr = Math.min(window.devicePixelRatio || 1, 2), w = cv.clientWidth, h = Math.round(Math.min(Math.max(w * 0.6, 380), 760));
    cv.style.height = h + "px"; cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); S.c = cv.getContext("2d"); S.c.setTransform(dpr, 0, 0, dpr, 0, 0); S.w = w; S.h = h;
    S.cx = w / 2; S.cy = h / 2 + 4; S.rad = Math.min(w * 0.44, h * 0.43); S.limb = S.rad / Math.sqrt((1 + PERSP) * (1 + PERSP) - PERSP * PERSP);
    if (!sprites) sprites = { u: sprite(UP), d: sprite(DN), n: sprite(INK) };
    S.dpr = dpr; GLc.width = cv.width; GLc.height = cv.height;
  }
  function draw(t) {
    var c = S.c, focus = hover >= 0 ? hover : held, i, k, s;
    cosY = Math.cos(rotY); sinY = Math.sin(rotY); cosX = Math.cos(rotX); sinX = Math.sin(rotX);
    c.clearRect(0, 0, S.w, S.h);
    surface();
    Q = P.map(proj);
    c.globalCompositeOperation = "lighter";
    LINKS.forEach(function (l, n) {
      var own = focus >= 0 && (l[0] === focus || l[1] === focus), a = ARC[n], prev = null;
      c.beginPath();
      for (k = 0; k < a.length; k++) { s = proj(a[k]); if (s[2] < -0.04) { prev = null; continue; } if (prev) c.lineTo(s[0], s[1]); else c.moveTo(s[0], s[1]); prev = s; }
      c.lineWidth = own ? 1.2 : 0.7; c.strokeStyle = "rgba(" + INK + "," + (own ? 0.95 : focus >= 0 ? 0.1 : 0.16 + (l[2] - 45) / 55 * 0.4) + ")"; c.stroke();
      if (!still && (focus < 0 || own)) { var u = (t * (0.12 + l[2] / 500) + n * 0.37) % 1, f = u * (a.length - 1), i0 = Math.floor(f), w = f - i0, A = a[i0], B = a[Math.min(a.length - 1, i0 + 1)], q = proj([A[0] + (B[0] - A[0]) * w, A[1] + (B[1] - A[1]) * w, A[2] + (B[2] - A[2]) * w]); if (q[2] > -0.04) c.drawImage(sprites.n, q[0] - 5, q[1] - 5, 10, 10); }
    });
    c.globalAlpha = 1; c.globalCompositeOperation = "source-over";
    for (i = 0; i < N; i++) {
      s = Q[i]; if (s[2] <= 0.05 || !OPEN[i]) continue;
      // trading now: a ring that goes out from the exchange and fades
      var ph = still ? 0.4 : (t * 0.6 + i * 0.13) % 1; c.beginPath(); c.arc(s[0], s[1], 2 + ph * 13, 0, TAU); c.strokeStyle = "rgba(" + INK + "," + (0.85 * (1 - ph)).toFixed(2) + ")"; c.lineWidth = 1; c.stroke();
    }
    // names: the ones that face us, kept apart; all of them when one is in focus
    var placed = [];
    for (i = 0; i < N; i++) {
      s = Q[i]; if (s[2] <= 0.3 || i === focus) continue;
      var tiedTo = focus >= 0 && mine[focus].some(function (n) { return LINKS[n][0] === i || LINKS[n][1] === i; });
      if (focus >= 0 && !tiedTo) continue;
      if (placed.some(function (q) { return Math.abs(q[0] - s[0]) < 44 && Math.abs(q[1] - s[1]) < 12; })) continue;
      placed.push(s); label(MK[i].iso, s[0], s[1] + 3, "center", "rgba(242,243,243," + Math.min(0.95, (s[2] - 0.3) * 2).toFixed(2) + ")", 9);
    }
    if (focus >= 0 && Q[focus][2] > 0) {
      var f2 = Q[focus], mk = MK[focus], right = f2[0] > S.w - 260;
      c.font = "300 20px Geist, sans-serif"; c.textAlign = right ? "right" : "left"; c.fillStyle = "rgb(" + INK + ")"; if ("letterSpacing" in c) c.letterSpacing = "-0.3px";
      c.shadowColor = "#000"; c.shadowBlur = 8; c.fillText(mk.name, f2[0] + (right ? -20 : 20), f2[1] - 2);
var ax = f2[0] + (right ? -20 : 20), al = right ? "right" : "left";
      label(mk.index + (OPEN[focus] ? " \u00b7 trading now" : ""), ax, f2[1] + 15, al, "rgba(200,204,206,.95)", 10);
      label("Day " + pct(mk.d1, 2), ax, f2[1] + 30, al, "rgb(" + (mk.d1 >= 0 ? UP : DN) + ")", 10);
      label("Month " + pct(mk.m1, 1), ax, f2[1] + 44, al, "rgb(" + (mk.m1 >= 0 ? UP : DN) + ")", 10);
      label("Year " + pct(mk.ytd, 1), ax, f2[1] + 58, al, "rgb(" + (mk.ytd >= 0 ? UP : DN) + ")", 10); c.shadowBlur = 0;
    }
  }
  function say() {
    var f = hover >= 0 ? hover : held;
    if (f < 0) { var ups = MK.filter(function (m) { return m.d1 > 0; }).length; read.innerHTML = "Last session · <b>" + ups + "</b> rose · <b>" + (N - ups) + "</b> fell · point at a country, click to compare it"; return; }
    var m = MK[f], ties = mine[f].map(function (n) { var l = LINKS[n]; return [l[0] === f ? l[1] : l[0], l[2]]; }).sort(function (a, b) { return b[1] - a[1]; });
    read.innerHTML = "<b>" + m.name + "</b> · " + m.index + ' · <span class="' + cls(m.d1) + '">' + pct(m.d1, 2) + '</span> · 1 month <span class="' + cls(m.m1) + '">' + pct(m.m1, 1) + '</span> · this year <span class="' + cls(m.ytd) + '">' + pct(m.ytd, 1) + "</span>" + (ties.length ? " · moves with " + ties.slice(0, 3).map(function (x) { return MK[x[0]].iso + " " + (x[1] / 100).toFixed(2); }).join(", ") : "");
  }
  var t0 = performance.now(), clock = 0, on = false, tick = 0;
  function frame(nowMs) { if (!on) return; clock = (nowMs - t0) / 1000; if (!drag && hover < 0 && held < 0 && !still) rotY -= 0.0011; if (++tick % 600 === 0) clockwork(); draw(clock); if (!still) requestAnimationFrame(frame); }
  function once() { if (still || !on) draw(clock); }
  function pick(e) { var b = cv.getBoundingClientRect(), x = e.clientX - b.left, y = e.clientY - b.top, hit = countryAt(x, y); if (hit >= 0) return hit; var best = -1, reach = e.pointerType === "mouse" ? 14 : 24, bd = reach * reach; for (var i = 0; i < N; i++) { var s = Q[i]; if (!s || s[2] <= 0.02) continue; var d = (s[0] - x) * (s[0] - x) + (s[1] - y) * (s[1] - y); if (d < bd) { bd = d; best = i; } } return best; }
  cv.addEventListener("pointerdown", function (e) { drag = { x: e.clientX, y: e.clientY, ry: rotY, rx: rotX, moved: false }; cv.setPointerCapture(e.pointerId); });
  cv.addEventListener("pointermove", function (e) {
    if (drag) { if (Math.abs(e.clientX - drag.x) + Math.abs(e.clientY - drag.y) > 5) drag.moved = true; if (drag.moved) { rotY = drag.ry + (e.clientX - drag.x) * 0.006; rotX = Math.max(-1.2, Math.min(1.2, drag.rx + (e.clientY - drag.y) * 0.006)); once(); } return; }
    if (e.pointerType !== "mouse") return; var h = pick(e); if (h !== hover) { hover = h; cv.style.cursor = h >= 0 ? "pointer" : "grab"; paint(); say(); once(); }
  });
  cv.addEventListener("pointerup", function (e) { var moved = drag && drag.moved; drag = null; if (moved) return;
    var h = pick(e);
    // a finger names the market first; the second tap, or any click, puts it in the comparison below
    if (h >= 0 && (e.pointerType === "mouse" || held === h)) { var chip = document.querySelector('.wm-pick [data-m="' + MK[h].iso + '"]'); if (chip) chip.click(); }
    held = e.pointerType === "mouse" ? -1 : h; paint(); say(); once(); });
  cv.addEventListener("pointerleave", function () { if (hover >= 0) { hover = -1; paint(); say(); once(); } });
  var lw = 0; window.addEventListener("resize", function () { if (cv.clientWidth !== lw) { lw = cv.clientWidth; size(); once(); } });
  new IntersectionObserver(function (en) { var v = en[0].isIntersecting; if (v && !on) { on = true; requestAnimationFrame(frame); if (still) draw(0); } else if (!v) on = false; }, { rootMargin: "60px" }).observe(cv);
  if (!gl) return;  // no WebGL: the page is as it was, without the globe
  box.hidden = false;
  clockwork(); size(); lw = cv.clientWidth; paint(); say();
  if (document.fonts && document.fonts.load) document.fonts.load("10px " + MONO).then(once);
})();
