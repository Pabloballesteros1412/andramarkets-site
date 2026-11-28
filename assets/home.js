/* Andra Markets homepage: the phone menu and the scene of light (WebGL). */
(function(){var b=document.getElementById('menu-btn'),s=document.getElementById('sheet');if(!b||!s)return;function set(o){s.classList.toggle('open',o);b.setAttribute('aria-expanded',o);b.textContent=o?'Close':'Menu';}b.addEventListener('click',function(){set(!s.classList.contains('open'));});s.addEventListener('click',function(e){if(e.target.closest('a'))set(false);});document.addEventListener('keydown',function(e){if(e.key==='Escape')set(false);});})();
(function () {
  var cv = document.getElementById("scene"), gl = cv.getContext("webgl", { antialias: false, alpha: false, premultipliedAlpha: false });
  var OPENING = document.documentElement.classList.contains("opening"), OPEN_S = document.documentElement.classList.contains("opening--quick") ? 1.1 : 2.6;
  try { sessionStorage.setItem("andra-opened", "1"); } catch (e) { /* private mode */ }
  var DATA = JSON.parse(document.getElementById("home-data").textContent), reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!gl) { document.documentElement.classList.add("no-gl", "is-live"); return; }
  var VS = [
    "attribute vec3 a1,a2,a3,a4; attribute vec2 aFa,aFb; attribute vec4 aR;",
    "uniform float uImg,uHV,uFt,uGain,uA,uB,uT,uTime,uAspect,uDpr,uIntro,uObj,uPx,uVis,uOn[7]; uniform vec2 uRot[7]; uniform vec3 uOff[7]; uniform vec2 uPtr,uHc; uniform float uRr,uNight,uHS;",
    "varying float vA;",
    "vec3 rot(vec3 p, vec2 r){ float c=cos(r.x),s=sin(r.x); p=vec3(c*p.x+s*p.z,p.y,-s*p.x+c*p.z); c=cos(r.y); s=sin(r.y); return vec3(p.x,c*p.y-s*p.z,s*p.y+c*p.z); }",
    "vec3 nz(vec3 p){ return vec3(sin(p.y*2.1+p.z*1.3)+sin(p.z*3.7+p.x*1.9), sin(p.z*2.3+p.x*1.7)+sin(p.x*3.1+p.y*2.9), sin(p.x*2.7+p.y*1.1)+sin(p.y*3.3+p.z*2.2)); }",
    "void main(){",
    "  float f=uT;",
    "  float ft=clamp((f-aR.x*0.35)/0.65,0.0,1.0); ft=ft*ft*(3.0-2.0*ft);",
    "  float amb=step(1.5,aR.w);",                                     // ambient dust keeps its place
    "  float fe=0.0; float fw=1.0; float cut=(1.0-smoothstep(0.0,0.35,uFt))*(1.0-amb);",
    "  vec3 h0=vec3(mix(aFa,aFb,fe)/10000.0, mix((aR.y-0.5)*0.02, aR.y*4.6-2.6, amb));",
    "  float shed=0.0; float age=0.0;",
            "  vec3 p=vec3(0.0); float wh=0.0;",
    "  float th=(aR.y*2.0-1.0)*asin(clamp(1.15*uAspect/uRr,0.0,1.0)); float lift=0.0;",
    "  vec3 arcW=vec3((vec2(uHc.x,uHc.y-uRr)+(uRr+lift)*vec2(sin(th),cos(th)))*(3.4/2.75),0.0);",
    "  float hvB=0.75*mix(1.0,0.12,clamp(lift*2.2,0.0,1.0))*(0.1+0.9*exp(-abs(sin(th))*uRr*1.5));",
    "  float nt=clamp((uNight-aR.x*0.3)/0.7,0.0,1.0); nt=nt*nt*(3.0-2.0*nt);",
    // uOn marks the two shapes in play: the other four are not worked out for any particle
    "  float w=0.0,w0=0.0,w1=0.0,bf=1.0,w2=0.0,bf2=1.0;",
    "  if(uOn[0]>0.5){ float sn=sin(3.14159*nt); vec3 hp=h0*uObj*uHS+uOff[0]; if(sn>0.0005) hp+=nz(h0*3.0+aR.y*7.0+uTime*0.2)*0.13*sn;",
    "    w=(1.0-ft)*step(abs(uA-0.0),0.5)+ft*step(abs(uB-0.0),0.5); w0=w; p+=w*mix(mix(arcW,hp,nt),rot(h0,uRot[0]),amb); wh+=w; }",
    "  if(uOn[1]>0.5){ w=(1.0-ft)*step(abs(uA-1.0),0.5)+ft*step(abs(uB-1.0),0.5); vec3 g1=rot(a1,uRot[1]); w1=w*(1.0-amb); bf=mix(0.2,1.0,smoothstep(-0.5,0.3,g1.z)); p+=w*(g1*mix(uObj,1.0,amb)+uOff[1]*(1.0-amb)); }",
    "  if(uOn[2]>0.5){ w=(1.0-ft)*step(abs(uA-2.0),0.5)+ft*step(abs(uB-2.0),0.5); vec3 g2=rot(a2,uRot[2]); w2=w*(1.0-amb); bf2=mix(0.5,1.0,smoothstep(-0.5,0.3,g2.z)); p+=w*(g2*mix(uObj,1.0,amb)+uOff[2]*(1.0-amb)); }",
    "  if(uOn[3]>0.5){ w=(1.0-ft)*step(abs(uA-3.0),0.5)+ft*step(abs(uB-3.0),0.5); p+=w*(rot(a3,uRot[3])*mix(uObj,1.0,amb)+uOff[3]*(1.0-amb)); }",
    "  if(uOn[4]>0.5){ w=(1.0-ft)*step(abs(uA-4.0),0.5)+ft*step(abs(uB-4.0),0.5); p+=w*(rot(a4,uRot[4])*mix(uObj,1.0,amb)+uOff[4]*(1.0-amb)); }",
    "  if(uOn[5]>0.5){ w=(1.0-ft)*step(abs(uA-5.0),0.5)+ft*step(abs(uB-5.0),0.5); p+=w*(rot(a4,uRot[5])*mix(uObj,1.0,amb)+uOff[5]*(1.0-amb)); }",   // Crypto: a picture, its particles unseen
    "  if(uOn[6]>0.5){ w=(1.0-ft)*step(abs(uA-6.0),0.5)+ft*step(abs(uB-6.0),0.5); p+=w*mix(arcW,rot(h0,uRot[6]),amb); wh+=w; }",
    "  float burst=sin(3.14159*ft)*(1.0-amb); p.x=mix(p.x, mod(p.x-uTime*0.2+3.2,6.4)-3.2, amb);",
    "  float drift=0.2*burst+0.05*amb;",                                // the noise costs the most: only where a particle moves by it
    "  if(drift>0.0005) p+=nz(p*1.3+uTime*0.22+aR.y*6.0)*drift;",
    "  p.x-=burst*0.25*aR.y;",                                          // the wind carries the dust back
    "  float un=(1.0-uIntro)*(1.0-uIntro)*(1.0-amb); if(un>0.0005){ p+=nz(p*0.6+aR.x*9.0)*un*1.6; p.x+=un*2.2; }",
    "  p.xy+=uPtr*0.06*(p.z+0.6)*(1.0-wh*(1.0-amb));",
    "  float z=3.4-p.z; vec2 s=p.xy/z*2.75;",
    "  gl_Position=vec4(s.x/uAspect,s.y,0.0,1.0);",
    "  float coc=abs(p.z)*mix(1.0,1.6,amb);",
    "  float size=mix(1.5+aR.z*0.2,aR.z*0.6+0.42,amb)*uPx*(3.4/z); size*=1.0+coc*2.6*amb+burst*aR.x*1.6+amb*0.6;",
    "  float hk=wh*(1.0-amb); size=mix(size,max(1.0,1.15*uDpr/max(1.0,uDpr*0.8)),hk*(1.0-burst));",
    "  float sub=min(1.0,size*size); gl_PointSize=clamp(size,1.0,40.0*uDpr);",
    "  float br=mix(0.62,clamp(aR.w,0.0,1.0),0.0); br=mix(br,0.5,amb);",
    "  float g=br*sub*uIntro/(1.0+coc*coc*18.0*amb)*(1.0-0.78*burst)*mix(uVis*0.34*uGain,0.3,amb)*mix(1.0,bf,w1)*mix(1.0,bf2*0.8,w2)*(1.0-(1.0-amb)*(1.0-wh));",   // the groups' figures are drawn, not made of particles
    "  float hv=step(aR.x,uHV)*uIntro*clamp(pow(aR.w,1.2)*0.96,0.0,1.0)*nt*mix(0.22,1.0,smoothstep(0.72,1.0,nt))*step(0.001,w0);",
    "  vA=mix(g,hv*(1.0-uImg),hk);",
    "}"].join("\n");
  var FS = "precision mediump float; varying float vA; uniform vec3 uCol; void main(){ vec2 d=gl_PointCoord-0.5; float r=dot(d,d)*4.0; float a=(1.0-smoothstep(0.0,1.0,r))*vA; gl_FragColor=vec4(uCol*a,1.0); }";
  function sh(t, s) { var o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o); if (!gl.getShaderParameter(o, gl.COMPILE_STATUS)) console.error(gl.getShaderInfoLog(o)); return o; }
  var pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(pr); gl.useProgram(pr);
  var U = {}; ["uHS", "uNight", "uHc", "uRr", "uImg", "uHV", "uFt", "uGain", "uA", "uB", "uT", "uTime", "uAspect", "uDpr", "uIntro", "uObj", "uPx", "uRot", "uOff", "uPtr", "uVis", "uCol", "uOn"].forEach(function (n) { U[n] = gl.getUniformLocation(pr, n); });

  var BG_FS = ["precision highp float;",
    "uniform vec2 uRes,uC,uH; uniform float uTime,uHor,uGlobe,uGR,uAspect,uR,uOpen;",
    "float hash(vec2 p){ return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453); }",
    "void main(){",
    "  vec2 uv=gl_FragCoord.xy/uRes*2.0-1.0; vec2 p=vec2(uv.x*uAspect,uv.y);",
    "  vec3 col=vec3(0.016)*exp(-length(vec2((uv.x-uC.x)*uAspect*0.6,(uv.y-uC.y)*0.9))*1.9);",
    "  if(uHor>0.001){ vec2 c=vec2(uH.x*uAspect,uH.y-uR); float dist=length(p-c)-uR; float ax=abs(p.x-uH.x*uAspect);",
    "    float reach=uOpen*uOpen*(uAspect*1.25+0.4); float lit=1.0-smoothstep(reach*0.72,reach+0.001,ax); float spark=smoothstep(0.0,0.3,uOpen)*(1.0+1.5*exp(-pow((uOpen-0.3)/0.14,2.0)));",
    "    float fall=exp(-ax*0.85); float line=exp(-abs(dist)*260.0)*(0.16+0.62*fall)+exp(-abs(dist)*60.0)*0.10*fall;",
    "    float atm=dist>0.0?exp(-dist*6.5)*0.17*fall:exp(dist*13.0)*0.085*fall;",
    "    float core=exp(-length(vec2(ax*4.2,(p.y-uH.y)*8.0)))*0.42; float streak=exp(-ax*55.0)*exp(-abs(p.y-uH.y)*2.4)*0.16;",
    "    if(dist<0.0) col*=mix(1.0,0.12,uHor);",
    "    col+=vec3(1.0)*((line+atm)*lit+(core+streak)*spark)*uHor; }",
    "  if(uGlobe>0.001){ vec2 q=(p-vec2(uC.x*uAspect,uC.y))/uGR; float r2=dot(q,q);",
    "    if(r2<1.0){ vec3 n=vec3(q,sqrt(1.0-r2)); vec3 L=normalize(vec3(-0.80,0.38,0.42)); float lam=max(0.0,dot(n,L));",
    "      vec3 body=vec3(0.006)+vec3(0.15)*pow(lam,1.5); float fr=pow(1.0-n.z,3.5); body+=vec3(0.75)*fr*(0.04+lam*lam); col=mix(col,body,uGlobe); }",
    "    else { float a=exp(-(sqrt(r2)-1.0)*16.0); vec2 qn=normalize(q); float l=pow(max(0.0,dot(qn,normalize(vec2(-0.80,0.38)))),2.0); col+=vec3(0.6)*a*l*uGlobe; } }",
    "  col*=1.0-0.28*dot(uv*vec2(0.8,0.92),uv*vec2(0.8,0.92));",
    "  col+=(hash(gl_FragCoord.xy+fract(uTime)*91.7)-0.5)*0.005;",
    "  gl_FragColor=vec4(col,1.0); }"].join("\n");
  var Q_VS = "attribute vec2 aQ; uniform vec4 uBox; varying vec2 vUv; void main(){ vUv=aQ; gl_Position=vec4(uBox.xy+(aQ*2.0-1.0)*uBox.zw,0.0,1.0); }";
  var SIL_FS = "precision mediump float; varying vec2 vUv; uniform sampler2D uTex; uniform float uAlpha,uFlip; void main(){ vec4 t=texture2D(uTex,vec2(vUv.x,1.0-vUv.y)); gl_FragColor=vec4(vec3(t.r)*uAlpha,1.0); }";
  function prog2(v, f) { var p = gl.createProgram(); gl.attachShader(p, sh(gl.VERTEX_SHADER, v)); gl.attachShader(p, sh(gl.FRAGMENT_SHADER, f)); gl.linkProgram(p); return p; }
  var PB = prog2(Q_VS, BG_FS), PS = prog2(Q_VS, SIL_FS), qb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, qb); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([0, 0, 1, 0, 0, 1, 1, 1]), gl.STATIC_DRAW);
  function UL(p, names) { var o = {}; names.forEach(function (n) { o[n] = gl.getUniformLocation(p, n); }); return o; }
  var UB = UL(PB, ["uBox", "uRes", "uC", "uTime", "uHor", "uH", "uR", "uGlobe", "uGR", "uAspect", "uOpen"]), US = UL(PS, ["uBox", "uTex", "uAlpha", "uFlip"]);
  var silTex = null, silH = 0, srcImg = null, IMG_ASP = 0.88, bufs = [], rbuf = null;
  gl.useProgram(pr);
  var small = Math.min(innerWidth, innerHeight) < 700, N = small ? 400000 : 800000, AMB = small ? 1500 : 4800, MINN = small ? 120000 : 200000, drawN = N, capN = N, res = 1, skip = 2, ftAcc = 0, ftN = 0, lastNow = 0;
  var T = [null]; for (var k = 1; k < 5; k++) T.push(new Float32Array(N * 3)); var FB = [], NF = 1, FW = 681, FH = 774, HHW = 1.2, UU = new Float32Array(N), VV = new Float32Array(N);
  var R = new Float32Array(N * 4), rnd = Math.random;
  // ---- shapes -------------------------------------------------------------------------
  // Every point sits at an exact, evenly spaced place on a line (a low-discrepancy sequence, not chance), so lines read clean.
  function q0(n) { var v = n * 0.6180339887498949; return v - Math.floor(v); }
  function q1(n) { var v = n * 0.7548776662466927; return v - Math.floor(v); }
  function q2(n) { var v = n * 0.5698402909980532; return v - Math.floor(v); }
  function q3(n) { var v = n * 0.8191725133961645; return v - Math.floor(v); }
  // the light of each shape: the horse, Markets (violet), Tools (white), Research (gold), Careers (blue), Crypto (amber), the close
  var COLS = [[1, 1, 1], [0.8, 0.7, 1], [1, 1, 1], [1, 0.82, 0.56], [0.5, 0.72, 1], [1, 0.78, 0.45], [1, 1, 1]];
  function q4(n) { var v = n * 0.4142135623730951; return v - Math.floor(v); }
  // Each group's picture has a form of its own, in its map's colour (owner, 20 and 21 Nov 2026): Markets a globe
  // of knots and arcs, Tools the reel's tree on both sides of a bottleneck, Research a burst from one core,
  // Careers the web of its map. The globe, burst and web are drawn in the maps' language, knots joined by ropes.
  // A form is knots [x, y, z, size] and ropes [from, to, bow, width]; on a globe the ropes follow the sphere.
  function webForm(kids) {
    var N0 = [], E = [], k, j2;
    for (k = 0; k < 6; k++) { var an = -Math.PI / 2 + k / 6 * 6.2832; N0.push([Math.cos(an) * 0.5, -Math.sin(an) * 0.5, 0, 1]); }
    for (k = 0; k < 6; k++) E.push([k, (k + 1) % 6, -0.13, 1]);
    for (k = 0; k < 6; k++) for (j2 = 0; j2 < kids[k]; j2++) { var a0 = -Math.PI / 2 + k / 6 * 6.2832, ca = a0 + (j2 - (kids[k] - 1) / 2) * 0.36, dd = 0.4 + (kids[k] > 3 && j2 % 2 ? 0.07 : 0);
      N0.push([N0[k][0] + Math.cos(ca) * dd, N0[k][1] - Math.sin(ca) * dd, 0, 0.5]); E.push([k, N0.length - 1, 0.05, 0.5]); }
    return { n: N0, e: E };
  }
  function globeForm() {
    var N0 = [], E = [], M0 = 30, R = 0.8, i2, j2, seen = {};
    for (i2 = 0; i2 < M0; i2++) { var yy = 1 - (i2 + 0.5) / M0 * 2, rr = Math.sqrt(1 - yy * yy), th = i2 * 2.39996; N0.push([Math.cos(th) * rr * R, yy * R, Math.sin(th) * rr * R, i2 % 5 === 0 ? 0.9 : 0.5]); }
    for (i2 = 0; i2 < M0; i2++) { var near = []; for (j2 = 0; j2 < M0; j2++) if (j2 !== i2) near.push([Math.pow(N0[i2][0] - N0[j2][0], 2) + Math.pow(N0[i2][1] - N0[j2][1], 2) + Math.pow(N0[i2][2] - N0[j2][2], 2), j2]);
      near.sort(function (a, b) { return a[0] - b[0]; }); [0, 1, 4].forEach(function (q) { var o2 = near[q][1], key = Math.min(i2, o2) + "-" + Math.max(i2, o2); if (!seen[key]) { seen[key] = 1; E.push([i2, o2, 0.1, q === 4 ? 0.45 : 0.6]); } }); }
    return { n: N0, e: E, r: R };
  }
  function burstForm() {
    var N0 = [[0, 0, 0, 1.5]], E = [], k, j2;
    for (k = 0; k < 7; k++) { var an = k / 7 * 6.2832 + 0.3, d1 = 0.5 + (k % 2) * 0.1, m = N0.length; N0.push([Math.cos(an) * d1, Math.sin(an) * d1, (k % 3 - 1) * 0.12, 0.8]); E.push([0, m, k % 2 ? 0.08 : -0.08, 0.9]);
      var kids = 2 + k % 2; for (j2 = 0; j2 < kids; j2++) { var ca = an + (j2 - (kids - 1) / 2) * 0.34, d2 = 0.36 + (j2 % 2) * 0.06; N0.push([N0[m][0] + Math.cos(ca) * d2, N0[m][1] + Math.sin(ca) * d2, N0[m][2] * 1.6, 0.45]); E.push([m, N0.length - 1, 0.05, 0.45]); } }
    return { n: N0, e: E };
  }
  // Tools: the tree of the owner's reference reel, made on both sides of a bottleneck (owner, 21 Nov 2026).
  // Hundreds of hair-thin strands gather from a wide wind-blown crown below, squeeze through one narrow neck and
  // fan out into a second crown above; one path through the neck is lit, with a light at each turn.
  var TREE = (function () {
    var seed = 11, NS = 900, NP = 26, S = [], k, j2, mx = 0, my = 0;
    function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
    function sm(a, b, t) { t = Math.max(0, Math.min(1, (t - a) / (b - a))); return t * t * (3 - 2 * t); }
    var boughs = []; for (k = 0; k < 9; k++) boughs.push([-0.5 + Math.pow(k / 8, 0.8) * 1.6 + (rnd() - 0.5) * 0.1, (rnd() - 0.5) * 0.8]); // lean (from upright, towards the wind) and depth
    for (k = 0; k < NS; k++) { var bg = boughs[Math.floor(Math.pow(rnd(), 0.75) * 9)], twig = Math.floor(rnd() * 4), th1 = bg[0] + (twig - 1.5) * 0.11, th2 = th1 + (rnd() - 0.5) * 0.3, L = (0.8 + rnd() * 0.5) * (1 + Math.max(0, bg[0]) * 0.28), dz = bg[1] + (rnd() - 0.5) * 0.3, droop = 0.5 + rnd() * 0.8,
        x = (rnd() - 0.5) * 0.012, y = 0, z = (rnd() - 0.5) * 0.012, pts = [];
      for (j2 = 0; j2 < NP; j2++) { var t = j2 / (NP - 1), th = 0.12 + (bg[0] - 0.12) * sm(0.0, 0.22, t) + (th1 - bg[0]) * sm(0.18, 0.5, t) + (th2 - th1) * sm(0.45, 0.9, t) + droop * t * t * t * (bg[0] > 0.1 ? 1 : -0.4) + Math.sin(t * 9 + k) * 0.04 * t;
        pts.push([x, y, z]); x -= Math.sin(th) * L / NP; y += Math.cos(th) * L / NP; z += dz * sm(0.2, 0.7, t) * L / NP; if (Math.abs(x) > mx) mx = Math.abs(x); if (y > my) my = y; }
      S.push(pts); }
    var sc = Math.min(1.1 / mx, 0.95 / my);
    S.forEach(function (pts) { pts.forEach(function (q) { q[0] *= sc; q[1] *= sc; q[2] *= sc; }); });
    var best = 0, bv = -9; S.forEach(function (pts, n2) { var e2 = pts[NP - 1], v = e2[1] - Math.abs(e2[0] + 0.3) * 0.8; if (v > bv) { bv = v; best = n2; } }); // the lit path ends high in each crown
    return { s: S, np: NP, lit: best };
  })();
  function halfPt(pts, t) { var f = t * (TREE.np - 1), i2 = Math.min(TREE.np - 2, Math.floor(f)), u = f - i2, A = pts[i2], B = pts[i2 + 1]; return [A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u, A[2] + (B[2] - A[2]) * u]; }
  function strandPt(k, t) { // a whole strand: one half below the neck, turned about it, and another above
    var NS = TREE.s.length, P; if (t >= 0.5) return halfPt(TREE.s[k], t * 2 - 1); P = halfPt(TREE.s[k === TREE.lit ? k : (k * 7 + 3) % NS], 1 - t * 2); return [-P[0], -P[1], -P[2]];
  }
  function treeShape(i, o) {
    var n = i / 3, c = q0(n), a = q1(n), b = q2(n), d = q3(n), e = q4(n), P;
    if (c < 0.87) { var t = 0.5 + (b - 0.5) * Math.pow(Math.abs(b * 2 - 1), -0.15); P = strandPt(Math.floor(a * TREE.s.length) % TREE.s.length, Math.max(0, Math.min(1, t))); P[0] += (d - 0.5) * 0.0015; P[1] += (e - 0.5) * 0.0015; }
    else if (c < 0.91) { P = strandPt(TREE.lit, b); P[0] += (d - 0.5) * 0.004; P[1] += (e - 0.5) * 0.004; }                   // the lit path
    else { var m = Math.floor(a * 9) % 9, ang = b * 6.2832, up = d * 2 - 1, fl = Math.sqrt(1 - up * up), r = e * e * e * (m === 0 || m === 8 ? 0.06 : m === 4 ? 0.075 : 0.028); P = strandPt(TREE.lit, m / 8); // a light at each turn; the neck and the two tips brightest
      P = [P[0] + Math.cos(ang) * fl * r, P[1] + up * r, P[2] + Math.sin(ang) * fl * r]; }
    o[i] = P[0]; o[i + 1] = P[1]; o[i + 2] = P[2];
  }
  function ready(F) { // how the particles are shared out: by each rope's length and width, and by each knot's size
    var tot = 0, k; F.el = F.e.map(function (e) { var a = F.n[e[0]], b = F.n[e[1]], l = Math.sqrt(Math.pow(a[0] - b[0], 2) + Math.pow(a[1] - b[1], 2) + Math.pow(a[2] - b[2], 2)); tot += l * (0.4 + e[3]); return tot; });
    for (k = 0; k < F.el.length; k++) F.el[k] /= tot; tot = 0; F.nl = F.n.map(function (n) { tot += n[3] * n[3]; return tot; }); for (k = 0; k < F.nl.length; k++) F.nl[k] /= tot; return F;
  }
  var FORMS = [ready(globeForm()), null, ready(burstForm()), ready(webForm([2, 2, 5, 4, 5, 4]))]; // Tools is the tree, above
  function formShape(i, o, F) {
    var n = i / 3, c = q0(n), a = q1(n), b = q2(n), d = q3(n), e = q4(n), x, y, z, k = 0;
    if (c < 0.6) {                                   // a rope: a bundle of strands, widest at its middle
      while (k < F.el.length - 1 && F.el[k] < a) k++; var E = F.e[k], A = F.n[E[0]], B2 = F.n[E[1]], u = 1 - b, dx = B2[0] - A[0], dy = B2[1] - A[1], dz = B2[2] - A[2], l = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1, wd = Math.sin(3.14159 * b) * 0.05 * E[3];
      if (F.r) { x = A[0] * u + B2[0] * b; y = A[1] * u + B2[1] * b; z = A[2] * u + B2[2] * b; var len = Math.sqrt(x * x + y * y + z * z) || 1, lift = F.r * (1 + E[2] * Math.sin(3.14159 * b) * l) / len; x *= lift; y *= lift; z *= lift; x += (d - 0.5) * wd; y += (e - 0.5) * wd; z += (q0(n * 3.7) - 0.5) * wd; }
      else { var mx = (A[0] + B2[0]) / 2 - dy / l * E[2] * l * 2, my = (A[1] + B2[1]) / 2 + dx / l * E[2] * l * 2; x = u * u * A[0] + 2 * u * b * mx + b * b * B2[0]; y = u * u * A[1] + 2 * u * b * my + b * b * B2[1]; z = A[2] * u + B2[2] * b;
        x += -dy / l * (d - 0.5) * wd; y += dx / l * (d - 0.5) * wd; z += (e - 0.5) * wd; }
    } else {                                         // a knot: a core of light and a flare of rays
      while (k < F.nl.length - 1 && F.nl[k] < a) k++; var P = F.n[k], sz = P[3], ang, r;
      if (d < 0.42) { var rays = sz > 0.6 ? 6 : 4; ang = Math.floor(b * rays) / rays * 6.2832 + 0.3; r = e * e * 0.16 * sz; } else { ang = b * 6.2832; r = e * e * e * 0.075 * sz; }
      x = P[0] + Math.cos(ang) * r; y = P[1] + Math.sin(ang) * r; z = P[2] + (q0(n * 3.7) - 0.5) * r;
    }
    o[i] = x; o[i + 1] = y; o[i + 2] = z;
  }
  // ---- The four groups' figures, drawn in the maps' own stroke (owner, 21 Nov 2026: fixed and clear, in keeping
  // with the site): ropes of fine strands, knots of light with a flare, light travelling along. Markets a globe of
  // knots and arcs, Tools the reel's tree on both sides of a bottleneck, Research a burst, Careers the web.
  var fc = document.createElement("canvas"), fx = fc.getContext("2d"); fc.id = "figs"; fc.setAttribute("aria-hidden", "true"); cv.parentNode.insertBefore(fc, cv.nextSibling);
  var TINT = [null, ["208,190,255", "172,144,255", "132,104,255"], ["226,236,252", "215,230,255", "190,215,255"], ["255,214,150", "255,190,110", "255,160,70"], ["120,185,255", "60,140,255", "30,100,255"]];
  var fseed = 5, FC, FA = 1, FL = 1; function fr() { fseed = (fseed * 16807) % 2147483647; return fseed / 2147483647; }
  function fstr(n) { var a = []; for (var i = 0; i < n; i++) a.push({ r: Math.sqrt(fr()), tw: (fr() - 0.5) * 1.4, ph: fr() * 6.28, sp: 0.5 + fr() }); return a; }
  function fglow(x, y, r, a) { a *= FA; var g = fx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, "rgba(255,255,255," + a.toFixed(3) + ")"); g.addColorStop(0.25, "rgba(" + FC[1] + "," + (a * 0.45).toFixed(3) + ")"); g.addColorStop(1, "rgba(" + FC[2] + ",0)"); fx.fillStyle = g; fx.fillRect(x - r, y - r, r * 2, r * 2); }
  function frope(ax, ay, bx, by, bow, st, wide, base, t, pulses, key) {
    var dx = bx - ax, dy = by - ay, l = Math.sqrt(dx * dx + dy * dy) || 1, nx = -dy / l, ny = dx / l, c0 = bow.length ? bow[0] : (ax + bx) / 2 + nx * bow * l, c1 = bow.length ? bow[1] : (ay + by) / 2 + ny * bow * l; // bow: how far it bends, or the point it bends through
    var p1x = ax + (c0 - ax) * 2 / 3, p1y = ay + (c1 - ay) * 2 / 3, p2x = bx + (c0 - bx) * 2 / 3, p2y = by + (c1 - by) * 2 / 3; fx.lineWidth = 0.55 * FL;
    for (var q = 0; q < st.length; q++) { var z = st[q], th = z.ph + t * z.sp * 0.5, o1 = wide * z.r * Math.sin(th), o2 = wide * z.r * Math.sin(th + 2.6 + z.tw);
      fx.strokeStyle = "rgba(" + FC[0] + "," + (FA * base * (0.3 + 0.7 * (0.5 + 0.5 * Math.cos(th)))).toFixed(3) + ")"; fx.beginPath(); fx.moveTo(ax, ay); fx.bezierCurveTo(p1x + nx * o1, p1y + ny * o1, p2x + nx * o2, p2y + ny * o2, bx, by); fx.stroke(); }
    function at(f) { var u = 1 - f; return [u * u * u * ax + 3 * u * u * f * p1x + 3 * u * f * f * p2x + f * f * f * bx, u * u * u * ay + 3 * u * u * f * p1y + 3 * u * f * f * p2y + f * f * f * by]; }
    fx.lineCap = "round";
    for (var u2 = 0; u2 < pulses; u2++) { var f = (t * (0.1 + u2 * 0.03) + key * 0.37 + u2 * 0.41) % 1, back = u2 % 2;
      for (var k = 0; k < 12; k++) { var f0 = f - k * 0.011, f1 = f - (k + 1) * 0.011; if (f1 < 0) break; var a0 = at(back ? 1 - f0 : f0), a1 = at(back ? 1 - f1 : f1); fx.strokeStyle = "rgba(" + FC[0] + "," + (FA * (1 - k / 12) * 0.8).toFixed(3) + ")"; fx.lineWidth = 1.3 * FL * (1 - k / 14); fx.beginPath(); fx.moveTo(a0[0], a0[1]); fx.lineTo(a1[0], a1[1]); fx.stroke(); }
      var hd = at(back ? 1 - f : f); fglow(hd[0], hd[1], 9 * FL, 0.9); }
  }
  function fknot(X, Y, R, big, t, ph, a) {
    var beat = 0.5 + 0.5 * Math.sin(t * 1.3 + ph * 3); fglow(X, Y, R * (4.2 + 0.6 * beat), (big ? 0.26 : 0.2) * a); fglow(X, Y, R * 1.1, 0.9 * a); fglow(X, Y, R * 0.42, a);
    var rot0 = t * 0.07 + ph, rays = big ? 6 : 4;
    for (var r0 = 0; r0 < rays; r0++) { var ang = rot0 + r0 * 6.2832 / rays, len = R * ((big ? r0 % 3 === 0 : r0 % 2 === 0) ? 4.4 + 1.2 * beat : 2.1 + 0.5 * beat), ex = X + Math.cos(ang) * len, ey = Y + Math.sin(ang) * len, g = fx.createLinearGradient(X, Y, ex, ey);
      g.addColorStop(0, "rgba(255,255,255," + (0.85 * a * FA).toFixed(3) + ")"); g.addColorStop(0.3, "rgba(" + FC[1] + "," + (0.3 * a * FA).toFixed(3) + ")"); g.addColorStop(1, "rgba(" + FC[2] + ",0)"); fx.strokeStyle = g; fx.lineWidth = (big ? 1 : 0.7) * FL; fx.beginPath(); fx.moveTo(X, Y); fx.lineTo(ex, ey); fx.stroke(); }
  }
  // the web and the burst: knots [x, y, big, phase], ropes [from, to, bow, strands, wide, pulses]
  function flat(kn, rp) { return { k: kn, r: rp.map(function (e) { return { a: e[0], b: e[1], bow: e[2], st: fstr(e[3]), wide: e[4], pu: e[5] }; }) }; }
  var BURST = (function () { var kn = [[0, 0, 1, 1]], rp = [], k, j2;
    for (k = 0; k < 7; k++) { var an = k / 7 * 6.2832 + 0.3, d1 = 0.5 + (k % 2) * 0.1, m = kn.length; kn.push([Math.cos(an) * d1, Math.sin(an) * d1, 1, fr() * 6]); rp.push([0, m, k % 2 ? 0.16 : -0.16, 34, 0.04, 2]);
      var kids = 2 + k % 2; for (j2 = 0; j2 < kids; j2++) { var ca = an + (j2 - (kids - 1) / 2) * 0.34, d2 = 0.36 + (j2 % 2) * 0.06; kn.push([kn[m][0] + Math.cos(ca) * d2, kn[m][1] + Math.sin(ca) * d2, 0, fr() * 6]); rp.push([m, kn.length - 1, (j2 % 2 ? 1 : -1) * 0.1, 14, 0.02, 1]); } }
    return flat(kn, rp); })();
  var GLOBE = (function () { var kn = [], ed = [], M0 = 30, i2, j2, seen = {};
    for (i2 = 0; i2 < M0; i2++) { var yy = 1 - (i2 + 0.5) / M0 * 2, rr = Math.sqrt(1 - yy * yy), th = i2 * 2.39996; kn.push([Math.cos(th) * rr, yy, Math.sin(th) * rr, i2 % 5 === 0, fr() * 6]); }
    for (i2 = 0; i2 < M0; i2++) { var near = []; for (j2 = 0; j2 < M0; j2++) if (j2 !== i2) near.push([Math.pow(kn[i2][0] - kn[j2][0], 2) + Math.pow(kn[i2][1] - kn[j2][1], 2) + Math.pow(kn[i2][2] - kn[j2][2], 2), j2]);
      near.sort(function (a, b) { return a[0] - b[0]; }); [0, 1, 4].forEach(function (q) { var o2 = near[q][1], key = Math.min(i2, o2) + "-" + Math.max(i2, o2); if (!seen[key]) { seen[key] = 1; ed.push({ a: i2, b: o2, st: fstr(7), pu: ed.length % 3 === 0 }); } }); }
    return { k: kn, e: ed }; })();
  // Tools: a chart of candles (what the tools work on), with its average drawn as a rope and the last candle live.
  var CANDLES = (function () { var a = [], p = 0.3, k; for (k = 0; k < 20; k++) { var o = p, c = o + (fr() - 0.42) * 0.2; if (k === 7 || k === 13) c = o - 0.14 - fr() * 0.06; var hi = Math.max(o, c) + fr() * 0.07 + 0.015, lo = Math.min(o, c) - fr() * 0.07 - 0.015; a.push({ o: o, c: c, h: hi, l: lo, ph: fr() * 6 }); p = c; }
    var mn = 9, mx = -9; a.forEach(function (z) { mn = Math.min(mn, z.l); mx = Math.max(mx, z.h); }); a.forEach(function (z) { ["o", "c", "h", "l"].forEach(function (f) { z[f] = (z[f] - mn) / (mx - mn) * 1.2 - 0.6; }); }); a.st = fstr(12); return a; })();
  // Careers: the skyline the group is about, towers with their windows lit.
  var TOWERS = (function () { var a = [], x = -0.98, k; while (x < 0.9) { var w = 0.09 + fr() * 0.09, mid = 1 - Math.abs(x + w / 2) * 0.75, h = (0.35 + fr() * 0.5) * (0.55 + mid * 0.75), cols = Math.max(2, Math.round(w / 0.03)), rows = Math.max(3, Math.round(h / 0.045)), win = [];
      for (k = 0; k < cols * rows; k++) win.push(fr() < 0.42 ? fr() * 6.28 : -1); a.push({ x: x, w: w, h: h, cols: cols, rows: rows, win: win, top: fr() < 0.3 ? 1 : fr() < 0.5 ? 2 : 0, back: 0 }); x += w + 0.012 + fr() * 0.02; }
    var tall = 0; a.forEach(function (z, n2) { if (Math.abs(z.x + z.w / 2) < Math.abs(a[tall].x + a[tall].w / 2)) tall = n2; }); a[tall].h = 1.0; a[tall].top = 3; a[tall].rows = 22; a[tall].win = []; for (k = 0; k < a[tall].cols * 22; k++) a[tall].win.push(fr() < 0.5 ? fr() * 6.28 : -1);
    var b = []; for (x = -0.9; x < 0.85; x += 0.13 + fr() * 0.1) b.push({ x: x, w: 0.1 + fr() * 0.07, h: 0.3 + fr() * 0.45 }); a.back = b; a.st = fstr(30); return a; })();
  var SIGN = new Image(); if (DATA.sign) SIGN.src = DATA.sign;
  function figs(t, wts, cxN, cyN, obj, intro) {
    var d = Math.min(2, window.devicePixelRatio || 1), w = Math.round(W * d), h = Math.round(H * d); if (fc.width !== w || fc.height !== h) { fc.width = w; fc.height = h; }
    fx.setTransform(1, 0, 0, 1, 0, 0); fx.clearRect(0, 0, w, h); fx.globalCompositeOperation = "lighter";
    var X0 = (cxN * 0.5 + 0.5) * w, Y0 = (0.5 - cyN * 0.5) * h, R = obj * h * 0.5 * 2.75 / 3.4; FL = d * Math.max(0.8, Math.min(1.5, R / (330 * d)));
    for (var n = 1; n <= 4; n++) { var al = wts[n]; if (al < 0.01) continue; FA = al * al * intro; FC = TINT[n]; var S = R * (0.94 + 0.06 * al);
      if (n === 1) drawGlobe(t, X0, Y0, S * 0.84); else if (n === 2) drawCandles(t, X0, Y0, S); else if (n === 3) drawFlat(BURST, t, X0, Y0, S * 0.98, 0.3); else drawTowers(t, X0, Y0, S); }
    // Crypto: Bitcoin's sign with its walls built of a golden nebula, a picture (tools/make_crypto_sign.py) that breathes (owner, 28 Nov 2026)
    var a5 = wts[5]; if (a5 > 0.01 && SIGN.complete && SIGN.naturalWidth) { var s5 = R * (2.5 + 0.12 * a5) * (1 + 0.012 * Math.sin(t * 0.35)), br = 0.9 + 0.1 * Math.sin(t * 0.6);
      fx.globalAlpha = Math.min(1, a5 * a5 * intro * br); fx.drawImage(SIGN, X0 - s5 / 2, Y0 - s5 / 2, s5, s5); fx.globalAlpha = Math.min(1, a5 * a5 * intro) * (0.1 + 0.08 * Math.sin(t * 0.9 + 1)); fx.drawImage(SIGN, X0 - s5 * 0.52, Y0 - s5 * 0.52, s5 * 1.04, s5 * 1.04); fx.globalAlpha = 1; }
  }
  function drawFlat(F, t, X0, Y0, S, base) {
    var P = F.k.map(function (k, i2) { var fl = k[2] ? 0.012 : 0.02; return [X0 + (k[0] + Math.sin(t * 0.42 + k[3] * 2) * fl) * S, Y0 - (k[1] + Math.cos(t * 0.36 + k[3] * 3) * fl) * S]; });
    F.r.forEach(function (e, i2) { frope(P[e.a][0], P[e.a][1], P[e.b][0], P[e.b][1], e.bow, e.st, e.wide * S, base, t, e.pu, i2); });
    F.k.forEach(function (k, i2) { fknot(P[i2][0], P[i2][1], (k[2] ? 0.024 * k[2] : 0.012) * S, k[2], t, k[3], 1); });
  }
  function drawGlobe(t, X0, Y0, S) {
    var ay = t * 0.14 + ptr[0] * 0.3, ax = 0.3 - ptr[1] * 0.1, ca = Math.cos(ay), sa = Math.sin(ay), cb = Math.cos(ax), sb = Math.sin(ax);
    function pr3(x, y, z) { var x1 = x * ca + z * sa, z1 = -x * sa + z * ca, y1 = y * cb - z1 * sb, z2 = y * sb + z1 * cb, f = 1 / (1 - z2 * 0.14); return [X0 + x1 * S * f, Y0 - y1 * S * f, z2]; }
    var rim = fx.createRadialGradient(X0, Y0, S * 0.9, X0, Y0, S * 1.16); rim.addColorStop(0, "rgba(" + FC[2] + ",0)"); rim.addColorStop(0.42, "rgba(" + FC[1] + "," + (0.16 * FA).toFixed(3) + ")"); rim.addColorStop(1, "rgba(" + FC[2] + ",0)"); fx.fillStyle = rim; fx.fillRect(X0 - S * 1.2, Y0 - S * 1.2, S * 2.4, S * 2.4);
    var P = GLOBE.k.map(function (k) { return pr3(k[0], k[1], k[2]); });
    GLOBE.e.forEach(function (e, i2) { var A = GLOBE.k[e.a], B = GLOBE.k[e.b], pts = [], j2, zm = 0;
      for (j2 = 0; j2 <= 10; j2++) { var u = j2 / 10, x = A[0] * (1 - u) + B[0] * u, y = A[1] * (1 - u) + B[1] * u, z = A[2] * (1 - u) + B[2] * u, l = (1 + 0.05 * Math.sin(3.14159 * u)) / Math.sqrt(x * x + y * y + z * z), q = pr3(x * l, y * l, z * l); pts.push(q); zm += q[2] / 11; }
      var dep = Math.max(0, Math.min(1, (zm + 0.55) / 0.9)), base = 0.07 + 0.38 * dep * dep, dx = pts[10][0] - pts[0][0], dy = pts[10][1] - pts[0][1], l2 = Math.sqrt(dx * dx + dy * dy) || 1, nx = -dy / l2, ny = dx / l2; fx.lineWidth = 0.55 * FL;
      e.st.forEach(function (z2) { var th = z2.ph + t * z2.sp * 0.5, o = 0.02 * S * z2.r * Math.sin(th); fx.strokeStyle = "rgba(" + FC[0] + "," + (FA * base * (0.4 + 0.6 * (0.5 + 0.5 * Math.cos(th)))).toFixed(3) + ")"; fx.beginPath();
        for (j2 = 0; j2 <= 10; j2++) { var en = Math.sin(3.14159 * j2 / 10) * o; if (j2) fx.lineTo(pts[j2][0] + nx * en, pts[j2][1] + ny * en); else fx.moveTo(pts[0][0], pts[0][1]); } fx.stroke(); });
      if (e.pu && dep > 0.5) { var f = (t * 0.13 + i2 * 0.37) % 1, k = Math.min(9, Math.floor(f * 10)), u3 = f * 10 - k, hx2 = pts[k][0] + (pts[k + 1][0] - pts[k][0]) * u3, hy2 = pts[k][1] + (pts[k + 1][1] - pts[k][1]) * u3; fglow(hx2, hy2, 8 * FL, 0.85 * dep); } });
    GLOBE.k.forEach(function (k, i2) { var dep = Math.max(0, Math.min(1, (P[i2][2] + 0.55) / 0.9)); if (dep < 0.5) fglow(P[i2][0], P[i2][1], 0.02 * S, 0.25 + 0.5 * dep); else fknot(P[i2][0], P[i2][1], (k[3] ? 0.02 : 0.011) * S, k[3], t, k[4], dep); });
  }
  function col(a) { return "rgba(" + FC[0] + "," + (FA * a).toFixed(3) + ")"; }
  function drawCandles(t, X0, Y0, S) {
    var n = CANDLES.length, step = 1.64 / n, bw = step * 0.56, ma = [], sum = 0, k, vb = Y0 + 0.74 * S;
    function px(i2) { return X0 + (-0.84 + step * (i2 + 0.5)) * S; } function py(v) { return Y0 - (v * 0.98 + 0.12) * S; }
    fx.lineWidth = 0.5 * FL; for (k = 0; k < 5; k++) { fx.strokeStyle = col(0.07); fx.beginPath(); fx.moveTo(X0 - 0.86 * S, py(-0.6 + k * 0.3)); fx.lineTo(X0 + 0.86 * S, py(-0.6 + k * 0.3)); fx.stroke(); fx.strokeStyle = col(0.4); fx.beginPath(); fx.moveTo(X0 + 0.86 * S, py(-0.6 + k * 0.3)); fx.lineTo(X0 + 0.89 * S, py(-0.6 + k * 0.3)); fx.stroke(); } // the grid of the chart, and the ticks of its scale
    fx.strokeStyle = col(0.3); fx.beginPath(); fx.moveTo(X0 + 0.86 * S, py(0.66)); fx.lineTo(X0 + 0.86 * S, vb); fx.lineTo(X0 - 0.86 * S, vb); fx.stroke();
    CANDLES.forEach(function (z, i2) { var c = z.c + (i2 === n - 1 ? Math.sin(t * 0.9) * 0.05 : 0), up = c >= z.o, x = px(i2), y0 = py(Math.max(z.o, c)), y1 = py(Math.min(z.o, c)), hh = Math.max(2 * FL, y1 - y0), hi = py(Math.max(z.h, c)), lo = py(Math.min(z.l, c));
      sum += c; if (i2 >= 4) { sum -= CANDLES[i2 - 4].c; } ma.push([x, py(sum / Math.min(i2 + 1, 4) + 0.1)]);
      var vh = (0.03 + Math.abs(z.c - z.o) * 0.42 + 0.02 * Math.sin(z.ph)) * S; fx.fillStyle = col(up ? 0.16 : 0.3); fx.fillRect(x - bw * S / 2, vb - vh, bw * S, vh);   // what changed hands that day
      fglow(x, (y0 + y1) / 2, bw * S * (i2 === n - 1 ? 3 : 1.6), i2 === n - 1 ? 0.22 : 0.12); fx.strokeStyle = col(0.75); fx.lineWidth = 0.8 * FL; fx.beginPath(); fx.moveTo(x, hi); fx.lineTo(x, y0); fx.moveTo(x, y1); fx.lineTo(x, lo); fx.stroke();
      if (up) { fx.fillStyle = col(0.1); fx.fillRect(x - bw * S / 2, y0, bw * S, hh); fx.strokeStyle = col(0.95); fx.lineWidth = 1.1 * FL; fx.strokeRect(x - bw * S / 2, y0, bw * S, hh); }  // a rise is hollow, a fall is solid
      else { var g = fx.createLinearGradient(0, y0, 0, y0 + hh); g.addColorStop(0, col(0.85)); g.addColorStop(1, col(0.45)); fx.fillStyle = g; fx.fillRect(x - bw * S / 2, y0, bw * S, hh); }
      if (i2 === n - 1) { var yc = py(c); fx.setLineDash([3 * FL, 5 * FL]); fx.strokeStyle = col(0.45); fx.lineWidth = 0.7 * FL; fx.beginPath(); fx.moveTo(X0 - 0.86 * S, yc); fx.lineTo(X0 + 0.86 * S, yc); fx.stroke(); fx.setLineDash([]); fknot(X0 + 0.86 * S, yc, 0.018 * S, 1, t, 1, 1); } });
    for (k = 0; k < ma.length - 1; k++) frope(ma[k][0], ma[k][1], ma[k + 1][0], ma[k + 1][1], 0, CANDLES.st, 0.014 * S, 0.42, t, k % 4 === 0 ? 1 : 0, k);
  }
  function drawTowers(t, X0, Y0, S) {
    var gy = Y0 + 0.46 * S, sx = Math.sin(t * 0.2) * 0.012 + ptr[0] * 0.03, S0 = S; S = S * 0.96;
    TOWERS.back.forEach(function (z) { var x = X0 + (z.x - sx * 0.4) * S, w = z.w * S, h = z.h * S; fx.fillStyle = col(0.035); fx.fillRect(x, gy - h, w, h); fx.strokeStyle = col(0.2); fx.lineWidth = 0.6 * FL; fx.strokeRect(x, gy - h, w, h); });
    TOWERS.forEach(function (z) { var x = X0 + (z.x - sx) * S, w = z.w * S, rh = z.h * S * 0.3, g = fx.createLinearGradient(0, gy, 0, gy + rh); g.addColorStop(0, "rgba(" + FC[1] + "," + (0.2 * FA).toFixed(3) + ")"); g.addColorStop(1, "rgba(" + FC[2] + ",0)"); fx.fillStyle = g; fx.fillRect(x + w * 0.08, gy, w * 0.84, rh); }); // each tower's light on the water
    TOWERS.forEach(function (z, i2) { var x = X0 + (z.x - sx) * S, w = z.w * S, h = z.h * S, y = gy - h, cw = w / z.cols, ch = h / z.rows, r, c;
      fx.fillStyle = "rgba(0,0,0,0.9)"; fx.globalCompositeOperation = "source-over"; fx.fillRect(x, y, w, h); fx.globalCompositeOperation = "lighter"; fx.fillStyle = col(0.05); fx.fillRect(x, y, w, h);
      fx.strokeStyle = col(0.8); fx.lineWidth = 0.9 * FL; fx.beginPath(); fx.moveTo(x, gy); fx.lineTo(x, y); fx.lineTo(x + w, y); fx.lineTo(x + w, gy); fx.stroke();
      if (z.top === 1) { fx.beginPath(); fx.moveTo(x + w * 0.16, y); fx.lineTo(x + w * 0.16, y - 0.05 * S); fx.lineTo(x + w * 0.84, y - 0.05 * S); fx.lineTo(x + w * 0.84, y); fx.moveTo(x + w * 0.32, y - 0.05 * S); fx.lineTo(x + w * 0.32, y - 0.09 * S); fx.lineTo(x + w * 0.68, y - 0.09 * S); fx.lineTo(x + w * 0.68, y - 0.05 * S); fx.stroke(); } // setbacks
      if (z.top === 2) { fx.beginPath(); fx.moveTo(x + w / 2, y); fx.lineTo(x + w / 2, y - 0.07 * S); fx.stroke(); }
      if (z.top === 3) { fx.beginPath(); fx.moveTo(x, y); fx.lineTo(x + w / 2, y - 0.12 * S); fx.lineTo(x + w, y); fx.moveTo(x + w / 2, y - 0.12 * S); fx.lineTo(x + w / 2, y - 0.24 * S); fx.stroke(); fknot(x + w / 2, y - 0.24 * S, 0.016 * S, 1, t, 2, 1); }
      for (r = 0; r < z.rows; r++) for (c = 0; c < z.cols; c++) { var ph = z.win[r * z.cols + c]; if (ph < 0) continue; fx.fillStyle = "rgba(" + FC[0] + "," + (FA * (0.35 + 0.45 * (0.5 + 0.5 * Math.sin(t * 0.5 + ph)))).toFixed(3) + ")"; fx.fillRect(x + c * cw + cw * 0.3, y + r * ch + ch * 0.28, cw * 0.4, ch * 0.36); } });
    frope(X0 - 1.06 * S, gy, X0 + 1.06 * S, gy, 0, TOWERS.st, 0.008 * S, 0.5, t, 2, 3); S = S0;
  }
  function build(img) {
    var c = document.createElement("canvas"); c.width = img.naturalWidth; c.height = img.naturalHeight; var x = c.getContext("2d"); x.drawImage(img, 0, 0);
    var d = x.getImageData(0, 0, c.width, c.height).data, SW = c.width, i = 0; FW = c.width; FH = c.height; srcImg = img; IMG_ASP = FW / FH;
    for (; i < N - AMB; i++) { var j = i * 3; formShape(j, T[1], FORMS[0]); treeShape(j, T[2]); formShape(j, T[3], FORMS[2]); formShape(j, T[4], FORMS[3]);
      UU[i] = rnd(); VV[i] = rnd(); R[i * 4] = rnd(); R[i * 4 + 1] = rnd(); R[i * 4 + 2] = rnd() * rnd(); R[i * 4 + 3] = 0.55 + 0.45 * rnd(); }
    for (; i < N; i++) { var j3 = i * 3, ax = (rnd() - 0.5) * 6.4, ay = (rnd() - 0.5) * 3.4, az = -2.6 + rnd() * 4.6;
      for (var k = 1; k < 5; k++) { T[k][j3] = ax; T[k][j3 + 1] = ay; T[k][j3 + 2] = az; }
      UU[i] = ax; VV[i] = ay; R[i * 4] = rnd(); R[i * 4 + 1] = (az + 2.6) / 4.6; R[i * 4 + 2] = rnd(); R[i * 4 + 3] = 2; }
    for (var k2 = 1; k2 < 5; k2++) { var b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferData(gl.ARRAY_BUFFER, T[k2], gl.STATIC_DRAW); bufs.push([b, gl.getAttribLocation(pr, "a" + k2)]); T[k2] = null; }
    // each gallop frame: every particle keeps its place in the silhouette's mass (a monotone map), so it flows from pose to pose
    var K = HHW / FH, col = new Float32Array(FW + 1), pre = new Float32Array(FW * (FH + 1)), fi = 0;
    function one() {
      var ox = 0, oy = 0, xx, yy, sum;
      for (xx = 0; xx < FW; xx++) { sum = 0; pre[xx * (FH + 1)] = 0; for (yy = 0; yy < FH; yy++) { var dv = d[((oy + yy) * SW + ox + xx) * 4] / 255; sum += dv > 0.045 ? 0.3 + 0.7 * dv : 0; pre[xx * (FH + 1) + yy + 1] = sum; } col[xx + 1] = col[xx] + sum; }
      var tot = col[FW], out = new Int16Array(N * 2), q;
      for (q = 0; q < N - AMB; q++) {
        var tu = UU[q] * tot, lo = 0, hi = FW - 1, mid; while (lo < hi) { mid = (lo + hi) >> 1; if (col[mid + 1] <= tu) lo = mid + 1; else hi = mid; }
        var cw = col[lo + 1] - col[lo], fx = cw > 0 ? (tu - col[lo]) / cw : 0.5, base = lo * (FH + 1), tv = VV[q] * pre[base + FH], l2 = 0, h2 = FH - 1;
        while (l2 < h2) { mid = (l2 + h2) >> 1; if (pre[base + mid + 1] <= tv) l2 = mid + 1; else h2 = mid; }
        var ch = pre[base + l2 + 1] - pre[base + l2], fy = ch > 0 ? (tv - pre[base + l2]) / ch : 0.5;
        out[q * 2] = (lo + fx - FW / 2) * K * 10000; out[q * 2 + 1] = ((FH - l2 - fy) * K - HHW / 2) * 10000; R[q * 4 + 3] = d[(l2 * SW + lo) * 4] / 255;
      }
      for (; q < N; q++) { out[q * 2] = UU[q] * 10000; out[q * 2 + 1] = VV[q] * 10000; }
      var fb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, fb); gl.bufferData(gl.ARRAY_BUFFER, out, gl.STATIC_DRAW); FB.push(fb);
      if (++fi < NF) setTimeout(one, 0); else { rbuf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, rbuf); gl.bufferData(gl.ARRAY_BUFFER, R, gl.STATIC_DRAW); t0 = performance.now(); document.documentElement.classList.add("is-live"); requestAnimationFrame(frame); }
    }
    one();
  }
  var W = 0, H = 0, DPR = 1, t0 = 0, prog = 0, ptr = [0, 0], pt = [0, 0], secs = [].slice.call(document.querySelectorAll(".sec")), dots = [].slice.call(document.querySelectorAll(".rail a"));
  // The canvas never holds more than MAXPX pixels (a large or dense screen would fill several times that for the same picture).
  var MAXPX = 3200000, M = [], VH = 0, stTop = 0, stH = 0;
  function size() { W = cv.clientWidth; H = cv.clientHeight; DPR = Math.max(1, Math.min(small ? 2 : 1.75, window.devicePixelRatio || 1, Math.sqrt(MAXPX / Math.max(1, W * H)))) * res; cv.width = Math.round(W * DPR); cv.height = Math.round(H * DPR); gl.viewport(0, 0, cv.width, cv.height); measure(); }
  // where each section sits: read when the layout changes, not on every frame
  function measure() { VH = innerHeight; for (var i = 0; i < secs.length; i++) M[i] = [secs[i].offsetTop, secs[i].offsetHeight, +secs[i].getAttribute("data-shape")]; if (st) { stTop = st.offsetTop; stH = st.offsetHeight; } }
  addEventListener("resize", size); addEventListener("load", measure); document.addEventListener("visibilitychange", function () { skip = 3; ftAcc = ftN = 0; });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(measure);
  if (window.ResizeObserver) new ResizeObserver(measure).observe(document.getElementById("main") || document.body);
  addEventListener("pointermove", function (e) { pt[0] = (e.clientX / innerWidth) * 2 - 1; pt[1] = -((e.clientY / innerHeight) * 2 - 1); }, { passive: true });

  var jump = null, night = 0, st = document.querySelector(".statement"), words = [].slice.call(document.querySelectorAll(".statement .w"));
  var onNow = [], litN = -1, actNow = -1, ids = secs.map(function (s) { return "#" + s.id; }), rotA = new Float32Array(14), offA = new Float32Array(21), onA = new Float32Array(7), LOC = null;
  size();
  var TINTS = [[0.05, 0.06, 0.08], [0.04, 0.07, 0.13], [0.03, 0.09, 0.10], [0.11, 0.07, 0.035], [0.13, 0.06, 0.03], [0.12, 0.07, 0.02], [0.06, 0.065, 0.08]], tint = [0.05, 0.06, 0.08];
  function target() {
    var y = window.scrollY || document.documentElement.scrollTop, vh = VH, p = 0, ng = 0;
    for (var i = 0; i < M.length; i++) {
      var top = M[i][0], h = M[i][1]; if (y + 1 < top) break;
      var a = M[i][2], nx = M[i + 1] ? M[i + 1][2] : a;
      var f = Math.min(1, Math.max(0, (y - top - (h - vh)) / vh));   // the last screen of a section hands over to the next
      p = a + (nx - a) * f; ng = i === 0 ? Math.min(1, (y - top) / (vh * 0.8)) : 1;
    }
    return [Math.min(6, p), ng];
  }
  function frame(now) {
    if (window.__clock != null) { now = window.__clock; t0 = 0; }
    var t = (now - t0) / 1000, tg = target(), k = reduce ? 1 : 0.09;
    night += (tg[1] - night) * (reduce ? 1 : 0.12);
    if (!jump && Math.abs(tg[0] - prog) > 1.15 && !reduce) jump = { a: Math.round(prog), b: Math.round(tg[0]), t0: now };
    var A, B, Tm;
    if (jump) { var jt = Math.min(1, (now - jump.t0) / 1500); if (!jump.fixed) jump.b = Math.round(tg[0]); A = jump.a; B = jump.b; Tm = jt; if (jt >= 1) { prog = tg[0]; jump = null; A = Math.min(5, Math.floor(prog)); B = A + 1; Tm = prog - A; } }
    else { prog += (tg[0] - prog) * k; if (Math.abs(tg[0] - prog) < 0.0005) prog = tg[0]; A = Math.min(5, Math.floor(prog)); B = A + 1; Tm = prog - A; }
    if (A === B) Tm = 0;
    function wt(n) { return (A === n ? 1 - Tm : 0) + (B === n ? Tm : 0); }
    ptr[0] += (pt[0] - ptr[0]) * 0.05; ptr[1] += (pt[1] - ptr[1]) * 0.05;
    var asp = W / H, port = asp < 0.85, tt = reduce ? 0 : t, nf = 1;
    var rot = [0, 0,
      tt * 0.14 + ptr[0] * 0.3, 0.3 + ptr[1] * -0.1,                                    // the globe turns
      Math.sin(tt * 0.21 + 1) * 0.2 + ptr[0] * 0.25, 0.1 + ptr[1] * -0.1,                // the tree sways
      Math.sin(tt * 0.19 + 2) * 0.22 + ptr[0] * 0.25, 0.26 + ptr[1] * -0.1,
      Math.sin(tt * 0.2 + 3) * 0.22 + ptr[0] * 0.25, 0.26 + ptr[1] * -0.1,
      0, 0, 0, 0];
    var hs = port ? 2.05 : 1, obj = port ? Math.min(0.42, asp * 0.9) : Math.min(1, asp * 0.62);
    var ox = port ? 0 : Math.min(0.8, asp * 0.43), oy = port ? 0.4 : 0.06, side = [1, 1, 1, 1, 1, 1, 0];
    var off = []; for (var i = 0; i < 7; i++) off.push(ox * side[i] * (i === 0 ? 0.86 : 1), oy, 0);
    // where the object sits on screen (weights between the two shapes in play)
    var es = Tm * Tm * (3 - 2 * Tm), cx = (off[A * 3] * (1 - es) + off[B * 3] * es) * 2.75 / 3.4 / asp, cy = (off[A * 3 + 1] * (1 - es) + off[B * 3 + 1] * es) * 2.75 / 3.4;
    var hh = HHW / 2 * obj * hs * 2.75 / 3.4, hw = hh * IMG_ASP / asp, hx = off[0] * 2.75 / 3.4 / asp, hy = off[1] * 2.75 / 3.4, yh = hy - hh * 0.955;
    var w5 = wt(6), hor = Math.max((1 - night) * wt(0), Math.max(0, (w5 - 0.3) / 0.7)), feet = (port ? -0.12 : -0.3) - (w5 > 0 ? 0 : night * 0.55);
    gl.disable(gl.BLEND);
    for (var d0 = 0; d0 < 7; d0++) gl.disableVertexAttribArray(d0);
    if (!LOC) LOC = { bq: gl.getAttribLocation(PB, "aQ"), sq: gl.getAttribLocation(PS, "aQ"), fa: gl.getAttribLocation(pr, "aFa"), fb: gl.getAttribLocation(pr, "aFb"), r: gl.getAttribLocation(pr, "aR") };
    gl.useProgram(PB); gl.bindBuffer(gl.ARRAY_BUFFER, qb); var la = LOC.bq; gl.enableVertexAttribArray(la); gl.vertexAttribPointer(la, 2, gl.FLOAT, false, 0, 0);
    gl.uniform4f(UB.uBox, 0, 0, 1, 1); gl.uniform2f(UB.uRes, cv.width, cv.height); gl.uniform2f(UB.uC, cx, cy); gl.uniform1f(UB.uTime, tt);
    var op = reduce || !OPENING ? 1 : Math.min(1, Math.max(0, (t - 0.2) / OPEN_S)); gl.uniform1f(UB.uOpen, 1 - Math.pow(1 - op, 2.2)); gl.uniform1f(UB.uHor, hor); gl.uniform2f(UB.uH, 0, feet); gl.uniform1f(UB.uR, port ? 2.2 : 3.4);
    gl.uniform1f(UB.uGlobe, 0); gl.uniform1f(UB.uGR, 0.82 * obj * 2.75 / 3.4); gl.uniform1f(UB.uAspect, asp);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    var wH = wt(0) + wt(6), it0 = reduce ? 1 : Math.min(1, t / 3.4), imgA = Math.max(0, Math.min(1, (wH - 0.86) / 0.14)) * Math.max(0, Math.min(1, (it0 - 0.8) / 0.2));
    imgA = Math.max(0, Math.min(1, (wt(0) - 0.86) / 0.14)) * Math.max(0, Math.min(1, (night - 0.95) / 0.05)); imgA = imgA * imgA * (3 - 2 * imgA);
    if (srcImg) { var ph = Math.max(8, Math.round(hh * H * DPR));                 // the drawing, resampled to exactly the pixels it will cover
      if (Math.abs(ph - silH) > 1) { silH = ph; var tc = document.createElement("canvas"); tc.height = ph; tc.width = Math.max(8, Math.round(ph * IMG_ASP)); var tx = tc.getContext("2d"); tx.imageSmoothingQuality = "high"; tx.drawImage(srcImg, 0, 0, tc.width, tc.height);
        if (!silTex) silTex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, silTex); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, tc);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE); } }
    if (imgA > 0.003 && silTex) {
      gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE); gl.useProgram(PS); gl.bindBuffer(gl.ARRAY_BUFFER, qb); var ls = LOC.sq; gl.enableVertexAttribArray(ls); gl.vertexAttribPointer(ls, 2, gl.FLOAT, false, 0, 0);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, silTex); gl.uniform1i(US.uTex, 0); gl.uniform1f(US.uAlpha, imgA); gl.uniform1f(US.uFlip, 0);
      var qx = cx, qy = cy, qh = silH / (H * DPR), qw = qh * IMG_ASP / asp;
      qx = Math.round((qx * 0.5 + 0.5) * cv.width - qw * cv.width / 2) / cv.width * 2 - 1 + qw; qy = Math.round((qy * 0.5 + 0.5) * cv.height - qh * cv.height / 2) / cv.height * 2 - 1 + qh;
      gl.uniform4f(US.uBox, qx, qy, qw, qh); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    }
    gl.useProgram(pr); for (var bi = 0; bi < bufs.length; bi++) { gl.bindBuffer(gl.ARRAY_BUFFER, bufs[bi][0]); gl.enableVertexAttribArray(bufs[bi][1]); gl.vertexAttribPointer(bufs[bi][1], 3, gl.FLOAT, false, 0, 0); }
    var cyc = 0, f0 = Math.floor(cyc * NF) % NF, f1 = (f0 + 1) % NF, la0 = LOC.fa, la1 = LOC.fb;
    gl.bindBuffer(gl.ARRAY_BUFFER, FB[f0]); gl.enableVertexAttribArray(la0); gl.vertexAttribPointer(la0, 2, gl.SHORT, false, 0, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, FB[f1]); gl.enableVertexAttribArray(la1); gl.vertexAttribPointer(la1, 2, gl.SHORT, false, 0, 0);
    gl.uniform1f(U.uImg, imgA); gl.uniform1f(U.uFt, 0); gl.uniform1f(U.uHV, Math.min(1, Math.max(0.01, (small ? 0.2 : 0.4) * (hh * H * DPR) * (hh * H * DPR * FW / FH) / N))); gl.uniform1f(U.uNight, night); gl.uniform1f(U.uHS, hs); gl.uniform2f(U.uHc, 0, feet); gl.uniform1f(U.uRr, port ? 2.2 : 3.4);
    var rl = LOC.r; gl.bindBuffer(gl.ARRAY_BUFFER, rbuf); gl.enableVertexAttribArray(rl); gl.vertexAttribPointer(rl, 4, gl.FLOAT, false, 0, 0);
    gl.uniform1f(U.uA, A); gl.uniform1f(U.uB, B); gl.uniform1f(U.uT, Tm); gl.uniform1f(U.uTime, tt); gl.uniform1f(U.uAspect, asp); gl.uniform1f(U.uDpr, DPR); var it = reduce ? 1 : Math.min(1, t / 3.4); gl.uniform1f(U.uIntro, 1 - Math.pow(1 - it, 3));
    gl.uniform1f(U.uObj, obj); gl.uniform1f(U.uPx, DPR * H / 900 * (small ? 1.15 : 1)); gl.uniform1f(U.uVis, 1);
    var ca0 = COLS[A], cb0 = COLS[B]; gl.uniform3f(U.uCol, ca0[0] + (cb0[0] - ca0[0]) * es, ca0[1] + (cb0[1] - ca0[1]) * es, ca0[2] + (cb0[2] - ca0[2]) * es); // each group in its map's colour
    rotA.set(rot); offA.set(off); for (var o6 = 0; o6 < 7; o6++) onA[o6] = (A === o6 && Tm < 1) || (B === o6 && Tm > 0) ? 1 : 0;
    gl.uniform2fv(U.uRot, rotA); gl.uniform3fv(U.uOff, offA); gl.uniform1fv(U.uOn, onA); gl.uniform2f(U.uPtr, ptr[0], ptr[1]);
    // the lines of particles: none are drawn while the horizon alone, or the finished drawing of the horse, is the picture
    var hidden = (A === 0 && (Tm === 0 || B === 0) && (night < 0.002 || imgA > 0.998)) || (B === 6 && Tm === 1);
    // keep it smooth: if frames run long, draw fewer of the (randomly ordered) particles, each a little brighter; if that is
    // not enough and they run past 40 ms, a smaller canvas (a browser holding 30 a second to save battery keeps its canvas whole).
    // A level that ran long is not gone back to.
    // Frames are timed only while the particles are drawn, and not across a spell with the tab hidden.
    var dtf = now - lastNow; lastNow = now; skip--; if (hidden) ftAcc = ftN = 0;
    if (!hidden && skip <= 0 && dtf > 0 && window.__clock == null) { ftAcc += Math.min(dtf, 500); ftN++; if (ftN >= 30) { var avg = ftAcc / ftN; ftAcc = ftN = 0;
      if (avg > 21) { if (drawN > MINN) { capN = Math.round(drawN * 0.9); drawN = Math.max(MINN, Math.round(drawN * 0.7)); } else if (avg > 40 && res > 0.62) { res *= 0.85; size(); } }
      else if (avg < 17.4 && drawN < capN) drawN = Math.min(capN, Math.round(drawN * 1.1)); } }
    gl.uniform1f(U.uGain, Math.min(3, 0.3 * 1600000 / drawN) * (small ? 0.2 : 1));
    gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE); if (!hidden) gl.drawArrays(gl.POINTS, 0, drawN);
    if (hidden || drawN < N - AMB) gl.drawArrays(gl.POINTS, N - AMB, AMB);   // the dust in the air is always there
    // text
    // (the page is written to only when a value changes, so a still screen costs no style work)
    var y = window.scrollY || 0, vh = VH, act = 0, bd = 1e9;
    for (var s2 = 0; s2 < M.length; s2++) { var sT = M[s2][0], sH = M[s2][1], mid = sT + sH - vh / 2, dd = Math.abs(y + vh / 2 - mid) / vh; if (sH > vh * 1.2) dd = Math.max(0, (y < sT ? (sT - y) : (y + vh - sT - sH)) / vh);
      var on = Math.max(0, 1 - dd * 2.4).toFixed(3); if (on !== onNow[s2]) { onNow[s2] = on; secs[s2].style.setProperty("--on", on); } if (dd < bd) { bd = dd; act = s2; } }
    if (act !== actNow) { actNow = act; for (var r2 = 0; r2 < dots.length; r2++) dots[r2].classList.toggle("on", dots[r2].getAttribute("href") === ids[act]); }
    if (st) { var sp = (y - stTop + vh * 0.55) / (stH - vh * 0.35), nW = words.length, lit = Math.max(0, Math.min(nW, Math.ceil(sp * (nW + 2) - 1)));
      if (lit !== litN) { litN = lit; for (var w0 = 0; w0 < nW; w0++) words[w0].classList.toggle("lit", w0 < lit); } }
    figs(reduce ? 4 : t, [0, wt(1), wt(2), wt(3), wt(4), wt(5)], cx, cy, obj, 1);
    requestAnimationFrame(frame);
  }
  document.addEventListener("click", function (e) { var a = e.target.closest && e.target.closest('a[href^="#"]'); if (!a || reduce) return; var sec = document.getElementById(a.getAttribute("href").slice(1)); if (!sec || !sec.hasAttribute("data-shape")) return;
    var b = +sec.getAttribute("data-shape"), cur = Math.round(prog); if (jump) cur = jump.b; if (b !== cur) jump = { a: cur, b: b, t0: performance.now(), fixed: true }; });
  var img = new Image(); img.onload = function () { build(img); }; img.src = DATA.horse;
})();

/* leaving for another page: the scene carries the eye in, then the page changes; the next page knows it comes from here */
(function(){
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches, going = false;
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href]"); if (!a || going) return;
    var href = a.getAttribute("href"); if (!href || href.charAt(0) === "#" || a.target || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button) return;
    if (a.origin !== location.origin) return;
    try { sessionStorage.setItem("andra-arrive", String(Date.now())); } catch (err) { /* private mode */ }
    if (reduce) return;
    e.preventDefault(); going = true; document.documentElement.classList.add("is-leaving");
    setTimeout(function () { location.href = a.href; }, 640);
  });
  addEventListener("pageshow", function (e) { if (e.persisted) { going = false; document.documentElement.classList.remove("is-leaving"); } });
})();
