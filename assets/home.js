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
    "uniform float uImg,uHV,uFt,uGain,uA,uB,uT,uTime,uAspect,uDpr,uIntro,uObj,uPx,uVis,uOn[6]; uniform vec2 uRot[6]; uniform vec3 uOff[6]; uniform vec2 uPtr,uHc; uniform float uRr,uNight,uHS;",
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
    "  float w=0.0,w0=0.0,w1=0.0,bf=1.0;",
    "  if(uOn[0]>0.5){ float sn=sin(3.14159*nt); vec3 hp=h0*uObj*uHS+uOff[0]; if(sn>0.0005) hp+=nz(h0*3.0+aR.y*7.0+uTime*0.2)*0.13*sn;",
    "    w=(1.0-ft)*step(abs(uA-0.0),0.5)+ft*step(abs(uB-0.0),0.5); w0=w; p+=w*mix(mix(arcW,hp,nt),rot(h0,uRot[0]),amb); wh+=w; }",
    "  if(uOn[1]>0.5){ w=(1.0-ft)*step(abs(uA-1.0),0.5)+ft*step(abs(uB-1.0),0.5); vec3 g1=rot(a1,uRot[1]); w1=w*(1.0-amb); bf=mix(1.0,mix(0.07,1.0,smoothstep(-0.06,0.06,g1.z)),step(dot(a1,a1),0.9)); p+=w*(g1*mix(uObj,1.0,amb)+uOff[1]*(1.0-amb)); }",
    "  if(uOn[2]>0.5){ w=(1.0-ft)*step(abs(uA-2.0),0.5)+ft*step(abs(uB-2.0),0.5); p+=w*(rot(a2+vec3(0.0,0.05*sin(a2.x*3.0+a2.z*2.0+uTime*0.9),0.0)*(1.0-amb),uRot[2])*mix(uObj,1.0,amb)+uOff[2]*(1.0-amb)); }",
    "  if(uOn[3]>0.5){ w=(1.0-ft)*step(abs(uA-3.0),0.5)+ft*step(abs(uB-3.0),0.5); p+=w*(rot(a3,uRot[3])*mix(uObj,1.0,amb)+uOff[3]*(1.0-amb)); }",
    "  if(uOn[4]>0.5){ w=(1.0-ft)*step(abs(uA-4.0),0.5)+ft*step(abs(uB-4.0),0.5); p+=w*(rot(a4,uRot[4])*mix(uObj,1.0,amb)+uOff[4]*(1.0-amb)); }",
    "  if(uOn[5]>0.5){ w=(1.0-ft)*step(abs(uA-5.0),0.5)+ft*step(abs(uB-5.0),0.5); p+=w*mix(arcW,rot(h0,uRot[5]),amb); wh+=w; }",
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
    "  float g=br*sub*uIntro/(1.0+coc*coc*18.0*amb)*(1.0-0.78*burst)*mix(uVis*0.34*uGain,0.3,amb)*mix(1.0,bf,w1);",
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
  var LATS = [], LATC = [0]; (function () { for (var k = -5; k <= 5; k++) { LATS.push(k * 0.2618); LATC.push(LATC[LATC.length - 1] + Math.cos(k * 0.2618)); } })();
  // Minimal scenes: a few exact lines each.
  function globe(i, o) {
    var n = i / 3, c = q0(n), a = q1(n), b = q2(n), x, y, z, r = 0.82, lat, lon;
    if (c < 0.1) { var an = b * 6.2832, rr = 1.14; x = Math.cos(an) * rr; z = Math.sin(an) * rr; y = z * 0.32; z = z * 0.95; }
    else {
      if (c < 0.4) { var LK = [-1.05, -0.7, -0.35, 0, 0.35, 0.7, 1.05], LW = [0.07, 0.19, 0.33, 0.5, 0.67, 0.81, 0.93], k = 0; while (k < 6 && a > LW[k]) k++; lat = LK[k]; lon = b * 6.2832; }
      else { lon = Math.floor(a * 12) / 12 * 6.2832; lat = (b * 2 - 1) * 1.5; }
      x = r * Math.cos(lat) * Math.cos(lon); y = r * Math.sin(lat); z = r * Math.cos(lat) * Math.sin(lon);
    }
    o[i] = x; o[i + 1] = y; o[i + 2] = z;
  }
  function surface(i, o) {
    var n = i / 3, x, z;
    if (q0(n) < 0.55) { x = (Math.floor(q1(n) * 13) - 6) / 6; z = q2(n) * 2 - 1; } else { z = (Math.floor(q1(n) * 11) - 5) / 5; x = q2(n) * 2 - 1; }
    var tm = (z + 1) / 2, y = -0.42 + 0.62 * x * x * (1.25 - 0.75 * tm) + 0.2 * Math.exp(-2.2 * tm) - 0.1 * x * (1 - tm);
    o[i] = x * 0.98; o[i + 1] = y * 0.9; o[i + 2] = z * 0.8;
  }
  var S = DATA.spx, smin = Math.min.apply(0, S), smax = Math.max.apply(0, S);
  function sy(v) { return -0.5 + (v - smin) / (smax - smin) * 1.05; }
  function chart(i, o) {
    var n = i / 3, c = q0(n), a = q1(n), b = q2(n), m = S.length, x, y;
    if (c < 0.46) { var f = b * (m - 1), j = Math.floor(f), t = f - j; x = f; y = sy(S[j] + (S[Math.min(m - 1, j + 1)] - S[j]) * t); }
    else { var j2 = Math.floor(a * m); x = j2; y = -0.62 + (sy(S[j2]) + 0.62) * q3(n); }
    o[i] = -0.92 + x / (m - 1) * 1.84; o[i + 1] = y * 0.85; o[i + 2] = 0;
  }
  var TW = [], TWH = [0.24, 0.38, 0.3, 0.52, 0.44, 0.68, 0.6, 0.86, 0.76, 1.04, 0.94, 1.26], TWA = [0];
  (function () { var x = 0; for (var j = 0; j < TWH.length; j++) { TW.push([x, 0.13, TWH[j], 0.13, (j % 3 - 1) * 0.07]); x += 0.165; TWA.push(TWA[j] + TWH[j] + 0.5); } })();
  var TWC = (TW[TW.length - 1][0] + 0.13) / 2;
  function skyline(i, o) {
    var n = i / 3, c = q0(n), a = q1(n), b = q2(n), d = q3(n), tt = a * TWA[TWA.length - 1], k = 0; while (k < TW.length - 1 && TWA[k + 1] <= tt) k++;
    var t = TW[k], x, y, z, base = -0.62;
    if (c < 0.4) { var e = Math.floor(d * 12);
      if (e < 4) { x = (e & 1); z = (e >> 1); y = b; } else if (e < 8) { x = b; z = (e & 1); y = (e >> 2 === 1 ? (e >> 1) & 1 : 0); y = (e >> 1) & 1; } else { x = (e & 1); z = b; y = (e >> 1) & 1; } }
    else { var rows = Math.max(3, Math.round(t[2] / 0.052)); y = (Math.floor(d * rows) + 0.5) / rows; if (c < 0.8) { x = b; z = 1; } else { x = 1; z = b; } }
    o[i] = (t[0] + x * t[1] - TWC) * 0.78; o[i + 1] = (base + y * t[2]) * 0.92 + 0.02; o[i + 2] = (t[4] + (z - 0.5) * t[3]) * 0.9;
  }
  function build(img) {
    var c = document.createElement("canvas"); c.width = img.naturalWidth; c.height = img.naturalHeight; var x = c.getContext("2d"); x.drawImage(img, 0, 0);
    var d = x.getImageData(0, 0, c.width, c.height).data, SW = c.width, i = 0; FW = c.width; FH = c.height; srcImg = img; IMG_ASP = FW / FH;
    for (; i < N - AMB; i++) { var j = i * 3; globe(j, T[1]); surface(j, T[2]); chart(j, T[3]); skyline(j, T[4]);
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
  var onNow = [], litN = -1, actNow = -1, ids = secs.map(function (s) { return "#" + s.id; }), rotA = new Float32Array(12), offA = new Float32Array(18), onA = new Float32Array(6), LOC = null;
  size();
  var TINTS = [[0.05, 0.06, 0.08], [0.04, 0.07, 0.13], [0.03, 0.09, 0.10], [0.11, 0.07, 0.035], [0.13, 0.06, 0.03], [0.06, 0.065, 0.08]], tint = [0.05, 0.06, 0.08];
  function target() {
    var y = window.scrollY || document.documentElement.scrollTop, vh = VH, p = 0, ng = 0;
    for (var i = 0; i < M.length; i++) {
      var top = M[i][0], h = M[i][1]; if (y + 1 < top) break;
      var a = M[i][2], nx = M[i + 1] ? M[i + 1][2] : a;
      var f = Math.min(1, Math.max(0, (y - top - (h - vh)) / vh));   // the last screen of a section hands over to the next
      p = a + (nx - a) * f; ng = i === 0 ? Math.min(1, (y - top) / (vh * 0.8)) : 1;
    }
    return [Math.min(5, p), ng];
  }
  function frame(now) {
    if (window.__clock != null) { now = window.__clock; t0 = 0; }
    var t = (now - t0) / 1000, tg = target(), k = reduce ? 1 : 0.09;
    night += (tg[1] - night) * (reduce ? 1 : 0.12);
    if (!jump && Math.abs(tg[0] - prog) > 1.15 && !reduce) jump = { a: Math.round(prog), b: Math.round(tg[0]), t0: now };
    var A, B, Tm;
    if (jump) { var jt = Math.min(1, (now - jump.t0) / 1500); if (!jump.fixed) jump.b = Math.round(tg[0]); A = jump.a; B = jump.b; Tm = jt; if (jt >= 1) { prog = tg[0]; jump = null; A = Math.min(4, Math.floor(prog)); B = A + 1; Tm = prog - A; } }
    else { prog += (tg[0] - prog) * k; if (Math.abs(tg[0] - prog) < 0.0005) prog = tg[0]; A = Math.min(4, Math.floor(prog)); B = A + 1; Tm = prog - A; }
    if (A === B) Tm = 0;
    function wt(n) { return (A === n ? 1 - Tm : 0) + (B === n ? Tm : 0); }
    ptr[0] += (pt[0] - ptr[0]) * 0.05; ptr[1] += (pt[1] - ptr[1]) * 0.05;
    var asp = W / H, port = asp < 0.85, tt = reduce ? 0 : t, nf = 1;
    var rot = [0, 0,
      tt * 0.16 + ptr[0] * 0.3, 0.28 + ptr[1] * -0.1,
      -0.5 + Math.sin(tt * 0.2) * 0.18 + ptr[0] * 0.25, 0.42 + ptr[1] * -0.1,
      Math.sin(tt * 0.22) * 0.14 + ptr[0] * 0.2, 0.05 + ptr[1] * -0.08,
      -0.45 + Math.sin(tt * 0.18) * 0.2 + ptr[0] * 0.25, 0.16 + ptr[1] * -0.08,
      0, 0];
    var hs = port ? 2.05 : 1, obj = port ? Math.min(0.42, asp * 0.9) : Math.min(1, asp * 0.62);
    var ox = port ? 0 : Math.min(0.8, asp * 0.43), oy = port ? 0.4 : 0.06, side = [1, 1, 1, 1, 1, 0];
    var off = []; for (var i = 0; i < 6; i++) off.push(ox * side[i] * (i === 0 ? 0.86 : 1), oy, 0);
    // where the object sits on screen (weights between the two shapes in play)
    var es = Tm * Tm * (3 - 2 * Tm), cx = (off[A * 3] * (1 - es) + off[B * 3] * es) * 2.75 / 3.4 / asp, cy = (off[A * 3 + 1] * (1 - es) + off[B * 3 + 1] * es) * 2.75 / 3.4;
    var hh = HHW / 2 * obj * hs * 2.75 / 3.4, hw = hh * IMG_ASP / asp, hx = off[0] * 2.75 / 3.4 / asp, hy = off[1] * 2.75 / 3.4, yh = hy - hh * 0.955;
    var w5 = wt(5), hor = Math.max((1 - night) * wt(0), Math.max(0, (w5 - 0.3) / 0.7)), feet = (port ? -0.12 : -0.3) - (w5 > 0 ? 0 : night * 0.55);
    gl.disable(gl.BLEND);
    for (var d0 = 0; d0 < 7; d0++) gl.disableVertexAttribArray(d0);
    if (!LOC) LOC = { bq: gl.getAttribLocation(PB, "aQ"), sq: gl.getAttribLocation(PS, "aQ"), fa: gl.getAttribLocation(pr, "aFa"), fb: gl.getAttribLocation(pr, "aFb"), r: gl.getAttribLocation(pr, "aR") };
    gl.useProgram(PB); gl.bindBuffer(gl.ARRAY_BUFFER, qb); var la = LOC.bq; gl.enableVertexAttribArray(la); gl.vertexAttribPointer(la, 2, gl.FLOAT, false, 0, 0);
    gl.uniform4f(UB.uBox, 0, 0, 1, 1); gl.uniform2f(UB.uRes, cv.width, cv.height); gl.uniform2f(UB.uC, cx, cy); gl.uniform1f(UB.uTime, tt);
    var op = reduce || !OPENING ? 1 : Math.min(1, Math.max(0, (t - 0.2) / OPEN_S)); gl.uniform1f(UB.uOpen, 1 - Math.pow(1 - op, 2.2)); gl.uniform1f(UB.uHor, hor); gl.uniform2f(UB.uH, 0, feet); gl.uniform1f(UB.uR, port ? 2.2 : 3.4);
    gl.uniform1f(UB.uGlobe, Math.max(0, wt(1) * 1.6 - 0.6)); gl.uniform1f(UB.uGR, 0.82 * obj * 2.75 / 3.4); gl.uniform1f(UB.uAspect, asp);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    var wH = wt(0) + wt(5), it0 = reduce ? 1 : Math.min(1, t / 3.4), imgA = Math.max(0, Math.min(1, (wH - 0.86) / 0.14)) * Math.max(0, Math.min(1, (it0 - 0.8) / 0.2));
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
    gl.uniform3f(U.uCol, 1, 1, 1);
    rotA.set(rot); offA.set(off); for (var o6 = 0; o6 < 6; o6++) onA[o6] = (A === o6 && Tm < 1) || (B === o6 && Tm > 0) ? 1 : 0;
    gl.uniform2fv(U.uRot, rotA); gl.uniform3fv(U.uOff, offA); gl.uniform1fv(U.uOn, onA); gl.uniform2f(U.uPtr, ptr[0], ptr[1]);
    // the lines of particles: none are drawn while the horizon alone, or the finished drawing of the horse, is the picture
    var hidden = (A === 0 && (Tm === 0 || B === 0) && (night < 0.002 || imgA > 0.998)) || (B === 5 && Tm === 1);
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
