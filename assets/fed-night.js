/* Fed & Rates: the United States at night, seen from orbit over the Gulf. A fragment shader casts each
   pixel's ray at the sphere and reads the night lights there; a 2D canvas on top draws the Board in
   Washington and the twelve Reserve Banks, the arcs between them and the light travelling along the arcs.
   Banks that vote on the FOMC this year burn brighter: New York always, four others by the committee's
   yearly rotation. Pointing at a city names its Bank; a click goes to the policy panel. */
(function () {
  var stage = document.querySelector(".fr-night"); if (!stage) return;
  var glc = stage.querySelector(".fr-night__gl"), top = stage.querySelector(".fr-night__top"), read = stage.querySelector(".fr-night__read"), TEX;
  try { TEX = JSON.parse(stage.querySelector('script[type="application/json"]').textContent); } catch (e) { return; }
  var gl = glc.getContext("webgl", { antialias: false, alpha: true, premultipliedAlpha: true }), cx = top.getContext("2d"); if (!gl || !cx) return;
  stage.hidden = false; // the room is taken at once, so nothing below jumps when the view arrives
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], nextDay = "";
  if (TEX.next) { var nd = new Date(TEX.next); if (!isNaN(nd) && nd > new Date()) { var pt = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", month: "numeric", day: "numeric" }).formatToParts(nd), mo = 0, dy = 0; pt.forEach(function (x) { if (x.type === "month") mo = +x.value; if (x.type === "day") dy = +x.value; }); nextDay = dy + " " + MON[mo - 1].toUpperCase(); } }
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var RAD = Math.PI / 180, YEAR = new Date().getFullYear();
  // The twelve Reserve Banks and the Board. Votes rotate by the FOMC's own rule: New York always, four others by year.
  var A = ["Richmond", "Boston", "Philadelphia"], B = ["Cleveland", "Chicago"], C = ["Atlanta", "St. Louis", "Dallas"], Dg = ["San Francisco", "Kansas City", "Minneapolis"];
  function voters(y) { var k = ((y - 2024) % 3 + 3) % 3; return [A[k], B[((y - 2024) % 2 + 2) % 2], C[k], Dg[k]]; }
  function nextVote(n) { for (var y = YEAR; y < YEAR + 4; y++) if (voters(y).indexOf(n) >= 0) return y; return null; }
  var P = [["Washington", 0, 38.893, -77.045], ["Boston", 1, 42.352, -71.054], ["New York", 2, 40.708, -74.009], ["Philadelphia", 3, 39.953, -75.149], ["Cleveland", 4, 41.501, -81.69],
    ["Richmond", 5, 37.535, -77.44], ["Atlanta", 6, 33.789, -84.384], ["Chicago", 7, 41.878, -87.632], ["St. Louis", 8, 38.628, -90.189], ["Minneapolis", 9, 44.983, -93.268],
    ["Kansas City", 10, 39.076, -94.585], ["Dallas", 11, 32.789, -96.801], ["San Francisco", 12, 37.793, -122.396]].map(function (c) {
    var v = c[0] === "New York" ? YEAR : c[1] ? nextVote(c[0]) : YEAR;
    return { name: c[0], d: c[1], p: ll(c[2], c[3]), votes: v === YEAR, when: v, always: c[0] === "New York" || !c[1] };
  });
  function ll(lat, lon) { var a = lat * RAD, o = lon * RAD; return [Math.cos(a) * Math.sin(o), Math.sin(a), Math.cos(a) * Math.cos(o)]; }
  function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
  function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
  function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
  function norm(a) { var l = Math.sqrt(dot(a, a)); return [a[0] / l, a[1] / l, a[2] / l]; }
  function mul(a, k) { return [a[0] * k, a[1] * k, a[2] * k]; }
  // arcs from the Board to each Bank, lifted off the ground
  var ARC = P.slice(1).map(function (c) {
    var a = P[0].p, b = c.p, w = Math.acos(Math.max(-1, Math.min(1, dot(a, b)))), pts = [], n = 40;
    for (var i = 0; i <= n; i++) { var t = i / n, s0 = Math.sin((1 - t) * w) / Math.sin(w), s1 = Math.sin(t * w) / Math.sin(w), q = [a[0] * s0 + b[0] * s1, a[1] * s0 + b[1] * s1, a[2] * s0 + b[2] * s1]; pts.push(mul(norm(q), 1 + (0.008 + w * 0.085) * Math.sin(Math.PI * t))); }
    return { to: c, pts: pts, ph: (c.d * 0.37) % 1, sp: 0.16 + 0.05 * ((c.d * 7) % 5) / 5 };
  });

  function sh(t, s) { var o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o); return o; }
  var pr = gl.createProgram();
  gl.attachShader(pr, sh(gl.VERTEX_SHADER, "attribute vec2 p;varying vec2 v;void main(){v=p;gl_Position=vec4(p,0.,1.);}"));
  gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, "precision highp float;varying vec2 v;uniform vec3 eye,fw,rt,up;uniform vec2 tf;uniform vec4 box;uniform sampler2D night,day;uniform float lit;" +
        "void main(){vec3 d=normalize(fw+rt*v.x*tf.x+up*v.y*tf.y);float b=dot(eye,d);float c=dot(eye,eye)-1.;float h=b*b-c;vec3 col=vec3(0.);float al=1.;" +
    "float near=length(eye+d*max(-b,0.));" +
    "if(h>0.&&b<0.){float t=-b-sqrt(h);vec3 n=eye+d*t;float lat=asin(clamp(n.y,-1.,1.));float lon=atan(n.x,n.z);" +
    "vec2 uv=vec2((degrees(lon)-box.x)/(box.y-box.x),(box.w-degrees(lat))/(box.w-box.z));float inb=step(0.,uv.x)*step(uv.x,1.)*step(0.,uv.y)*step(uv.y,1.);" +
    "float nl=texture2D(night,uv).r*inb;float dl=texture2D(day,vec2(lon/6.2831853+.5,.5-lat/3.14159265)).r;" +
    "float mu=max(dot(n,-d),0.);float rim=pow(1.-mu,3.2);" +
    "nl=pow(nl,1.7);col=vec3(1.,.985,.96)*nl*(1.05+.35*lit)*mix(.5,1.,mu);" +     // the lights, a little dimmer through more air
    "col+=vec3(.42,.5,.62)*dl*.085*(.4+.6*mu);" +                                   // the ground, by moonlight
    "col+=vec3(.16,.3,.62)*rim*.9+vec3(.5,.7,1.)*pow(1.-mu,9.)*.9;" +               // air near the horizon
    "}else{float a=exp(-(near-1.)*46.);col=vec3(.22,.42,.9)*a*1.25+vec3(.7,.85,1.)*exp(-(near-1.)*260.)*.8;al=clamp(a*1.6,0.,1.);}" + // the limb, over the page's own sky
    "float fade=smoothstep(-1.,-.72,v.y);gl_FragColor=vec4(col*fade,al*fade);}"));
  gl.linkProgram(pr); if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) return; gl.useProgram(pr);
  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer()); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  var lp = gl.getAttribLocation(pr, "p"); gl.enableVertexAttribArray(lp); gl.vertexAttribPointer(lp, 2, gl.FLOAT, false, 0, 0);
  function U(n) { return gl.getUniformLocation(pr, n); }
  gl.clearColor(0, 0, 0, 0); var uEye = U("eye"), uFw = U("fw"), uRt = U("rt"), uUp = U("up"), uTf = U("tf"), uLit = U("lit");
  gl.uniform4f(U("box"), TEX.box[0], TEX.box[1], TEX.box[2], TEX.box[3]);
  var ready = 0;
  function tex(unit, name, src) {
    var t = gl.createTexture(), im = new Image();
    function up() { gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t); gl.texImage2D(gl.TEXTURE_2D, 0, gl.LUMINANCE, gl.LUMINANCE, gl.UNSIGNED_BYTE, im);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.uniform1i(U(name), unit); ready++; if (ready === 2) { t0 = 0; size(); stage.classList.add("is-on"); } once(); }
    im.src = src; // decoded off the main thread where the browser can
    if (im.decode) im.decode().then(up, function () { if (im.complete && im.naturalWidth) up(); }); else im.onload = up;
  }
  // The pictures load, and the view starts, once the page's own transition has finished: starting during it made the arrival stutter.
  var begun = false; function begin() { if (begun) return; begun = true; tex(0, "night", TEX.night); tex(1, "day", TEX.day); }
  window.addEventListener("pagereveal", function (e) { if (e.viewTransition && e.viewTransition.finished) e.viewTransition.finished.then(begin, begin); else begin(); });
  window.setTimeout(begin, "onpagereveal" in window ? 1400 : 120);

  var W = 0, H = 0, dpr = 1, phone = false, eye, fw, rt, up, tanF, asp, t0 = 0, drift = 0, driftT = 0, hover = -1, px = 0, py = 0, drag = false, fly = still ? 1 : 0, q = 1, slow = 0, nfr = 0, last = 0;
  function size() { W = glc.clientWidth; H = glc.clientHeight; dpr = Math.min(window.devicePixelRatio || 1, 2); phone = W < 640; var g = Math.min(dpr, 1.5) * q; if (W * H * g * g > 1.7e6) g = Math.sqrt(1.7e6 / (W * H));
    glc.width = Math.round(W * g); glc.height = Math.round(H * g); top.width = Math.round(W * dpr); top.height = Math.round(H * dpr); gl.viewport(0, 0, glc.width, glc.height); asp = W / H; }
  function cam(time) {
    var k = still ? 1 : Math.min(1, (time - t0) / 7000); k = 1 - Math.pow(1 - k, 3); fly = k;
    drift += (driftT - drift) * 0.08;
    var sway = still ? 0 : Math.sin(time / 11000) * 2.2, lon = (phone ? -91 : -95) + drift + sway + (1 - k) * 16;
    var alt = (phone ? 2.3 : 1.5) + (1 - k) * 1.5, lat0 = (phone ? 24 : 19) - (1 - k) * 8;
    eye = mul(ll(lat0, lon), alt);
    var tg = ll((phone ? 39 : 40) + (1 - k) * -6, (phone ? -92 : -96) + drift * 0.6 + sway * 0.5);
    fw = norm(sub(tg, eye)); rt = norm(cross(fw, norm(eye))); up = cross(rt, fw);
    tanF = Math.tan((phone ? 24 : 19.5) * RAD);
  }
  function proj(p) { var v = sub(p, eye), z = dot(v, fw); if (z <= 0) return null; return [(0.5 + 0.5 * dot(v, rt) / (z * tanF * asp)) * W, (0.5 - 0.5 * dot(v, up) / (z * tanF)) * H, z]; }
  function seen(p) { return dot(p, eye) > 1; }
  var MONO = "Geist Mono, ui-monospace, monospace", SANS = "Geist, system-ui, sans-serif";
  var glow = document.createElement("canvas"); glow.width = glow.height = 128;
  (function () { var g = glow.getContext("2d"), r = g.createRadialGradient(64, 64, 0, 64, 64, 64); r.addColorStop(0, "rgba(255,255,255,1)"); r.addColorStop(0.12, "rgba(225,238,255,.8)"); r.addColorStop(0.35, "rgba(150,190,255,.22)"); r.addColorStop(1, "rgba(120,170,255,0)"); g.fillStyle = r; g.fillRect(0, 0, 128, 128); })();
  function spot(q, s, a) { cx.globalAlpha = a; cx.drawImage(glow, q[0] - s / 2, q[1] - s / 2, s, s); }
  function over(time) {
    cx.setTransform(dpr, 0, 0, dpr, 0, 0); cx.clearRect(0, 0, W, H);
    var t = still ? 0.5 : (time - t0) / 1000, show = Math.max(0, (fly - 0.55) / 0.45), sc = phone ? 0.7 : 1;
    cx.globalCompositeOperation = "lighter"; cx.lineCap = "round";
    ARC.forEach(function (a, i) {
      var on = hover < 0 || hover === 0 || P[hover] === a.to, pts = a.pts.map(proj), strong = a.to.votes;
      cx.globalAlpha = show * (on ? (strong ? 0.5 : 0.24) : 0.07); cx.strokeStyle = "rgb(170,205,255)"; cx.lineWidth = strong ? 1.1 : 0.8;
      cx.beginPath(); pts.forEach(function (q, j) { if (!q) return; if (j) cx.lineTo(q[0], q[1]); else cx.moveTo(q[0], q[1]); }); cx.stroke();
      if (still || !on) return;
      // light travelling out from the Board and back in from the Bank
      for (var d = 0; d < 2; d++) {
        var ph = (t * a.sp + a.ph + d * 0.5) % 1, f = d ? 1 - ph : ph, n = a.pts.length - 1;
        for (var s = 0; s < 9; s++) { var ff = f - (d ? -1 : 1) * s * 0.012; if (ff < 0 || ff > 1) continue; var x = ff * n, j0 = Math.min(n - 1, Math.floor(x)), u = x - j0, q0 = pts[j0], q1 = pts[j0 + 1]; if (!q0 || !q1) continue;
          spot([q0[0] + (q1[0] - q0[0]) * u, q0[1] + (q1[1] - q0[1]) * u], (s ? 12 : 26) * sc * (strong ? 1.15 : 0.9), show * (1 - s / 9) * (s ? 0.5 : 1) * (strong ? 1 : 0.7)); }
      }
    });
    P.forEach(function (c, i) {
      var q = proj(c.p); if (!q || !seen(c.p)) { c.q = null; return; } c.q = q;
      var beat = still ? 0.5 : 0.5 + 0.5 * Math.sin(t * 1.7 + c.d * 1.3), big = !c.d ? 1.9 : c.votes ? 1.35 : 0.95, hot = hover === i ? 1.5 : 1;
      spot(q, (58 + 16 * beat) * big * hot * sc, show * (c.votes || !c.d ? 0.95 : 0.6)); spot(q, 16 * big * sc, show);
      if (c.votes || !c.d) { cx.globalAlpha = show * 0.55 * (1 - beat); cx.strokeStyle = "rgb(190,215,255)"; cx.lineWidth = 1; cx.beginPath(); cx.arc(q[0], q[1], (9 + 15 * beat) * big * sc, 0, 7); cx.stroke(); }
    });
    cx.globalCompositeOperation = "source-over"; cx.globalAlpha = 1;
    if (hover >= 0 && P[hover].q) card(P[hover]);
  }
  function lines(c) {
    if (!c.d) return ["Board of Governors", "SEVEN GOVERNORS, ALWAYS VOTE", nextDay ? "NEXT DECISION " + nextDay : "THE FOMC MEETS HERE"];
    return ["Federal Reserve Bank of " + c.name, "DISTRICT " + c.d, c.name === "New York" ? "ALWAYS VOTES" : c.votes ? "VOTES IN " + YEAR : "NEXT VOTES IN " + c.when];
  }
  function card(c) {
    var l = lines(c), x = c.q[0] + 22, y = c.q[1] - 30; cx.font = "300 " + (phone ? 17 : 21) + "px " + SANS; var w = cx.measureText(l[0]).width; if (x + w > W - 12) x = c.q[0] - w - 22; if (x < 12) x = 12;
    var gr = Math.max(w, 170) * 0.85, gx = x + Math.max(w, 170) / 2, gy = y + 30, g = cx.createRadialGradient(gx, gy, 8, gx, gy, gr); g.addColorStop(0, "rgba(0,0,0,.8)"); g.addColorStop(0.55, "rgba(0,0,0,.5)"); g.addColorStop(1, "rgba(0,0,0,0)"); cx.fillStyle = g; cx.fillRect(gx - gr, gy - gr, gr * 2, gr * 2);
    cx.textAlign = "left"; cx.textBaseline = "top"; cx.shadowColor = "#000"; cx.shadowBlur = 14; cx.fillStyle = "#f2f3f3"; cx.fillText(l[0], x, y); cx.fillText(l[0], x, y);
    cx.font = "400 11px " + MONO; cx.fillStyle = "rgba(200,205,210,.95)"; cx.fillText(l[1], x, y + (phone ? 25 : 30)); cx.fillStyle = "#f2f3f3"; cx.fillText(l[2], x, y + (phone ? 41 : 46)); cx.shadowBlur = 0;
  }
  var run = 0, visible = true;
  function frame(time) {
    run = 0; if (!t0) t0 = time; cam(time);
    // a machine that cannot keep up gets a coarser picture, not a slower one
    if (ready === 2 && last) { slow += time - last; if (++nfr === 30) { if (slow / 30 > 26 && q > 0.5) { q *= 0.78; size(); } slow = 0; nfr = 0; } } last = time;
    if (ready === 2) { gl.uniform3fv(uEye, eye); gl.uniform3fv(uFw, fw); gl.uniform3fv(uRt, rt); gl.uniform3fv(uUp, up); gl.uniform2f(uTf, tanF * asp, tanF); gl.uniform1f(uLit, fly); gl.clear(gl.COLOR_BUFFER_BIT); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4); over(time); }
    if (visible && !still) run = requestAnimationFrame(frame);
  }
  function once() { if (!run) { last = 0; run = requestAnimationFrame(frame); } }
  function near(x, y) { var best = -1, bd = (phone ? 30 : 24); P.forEach(function (c, i) { if (!c.q) return; var d = Math.hypot(c.q[0] - x, c.q[1] - y); if (d < bd) { bd = d; best = i; } }); return best; }
  function say() { read.textContent = hover >= 0 ? lines(P[hover]).join(". ") + "." : ""; top.style.cursor = hover >= 0 ? "pointer" : "grab"; }
  var sx = 0, sd = 0, moved = 0, held = -1;
  top.addEventListener("pointerdown", function (e) { drag = true; moved = 0; sx = e.clientX; sd = driftT; });
  top.addEventListener("pointermove", function (e) { var b = top.getBoundingClientRect(); px = e.clientX - b.left; py = e.clientY - b.top;
    if (drag && e.pointerType === "mouse") { var m = e.clientX - sx; moved = Math.max(moved, Math.abs(m)); if (moved > 6) driftT = Math.max(-16, Math.min(16, sd - m * 0.03)); }
    var h = near(px, py); if (h !== hover) { hover = h; say(); } once(); });
  top.addEventListener("pointerup", function (e) { drag = false; var b = top.getBoundingClientRect(), h = near(e.clientX - b.left, e.clientY - b.top);
    if (moved <= 6 && h >= 0 && (e.pointerType === "mouse" || held === h)) { var s = document.getElementById(TEX.goto); if (s) s.scrollIntoView({ behavior: still ? "auto" : "smooth", block: "start" }); }
    held = e.pointerType === "mouse" ? -1 : h; hover = h; say(); once(); });
  top.addEventListener("pointerleave", function () { drag = false; if (hover >= 0) { hover = -1; say(); once(); } });
  window.addEventListener("resize", function () { size(); once(); });
  if ("IntersectionObserver" in window) new IntersectionObserver(function (en) { visible = en[0].isIntersecting; if (visible) once(); }).observe(stage);
  size(); once();
})();
