/* Hedge Fund Data: Positioning. The page's figures are in a JSON file beside it, named by <meta name="hf-data">;
   tools/page_hedgefund.py writes both. Nothing here is fetched from anywhere else. */
(function () {
"use strict";
var meta = document.querySelector('meta[name="hf-data"]'); if (!meta) return;
fetch(meta.content).then(function (r) { if (!r.ok) throw new Error("data " + r.status); return r.json(); }).then(function (DATA) {
const D = DATA;
const $ = id => document.getElementById(id), esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const F = "Inter, 'Helvetica Neue', Arial, sans-serif";
const sg = (v, dp = 1) => v == null ? '<span class="dim">–</span>' : Math.abs(v) < Math.pow(10, -dp) / 2 ? `<span class="dim">${(0).toFixed(dp)}</span>` : `<span class="${v > 0 ? "up" : "dn"}">${v > 0 ? "+" : "−"}${Math.abs(v).toFixed(dp)}</span>`;
const lv = (v, dp = 1) => v == null ? "–" : (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(dp);
const kk = v => v == null ? "–" : (v < 0 ? "−" : "") + (Math.abs(v) >= 1e6 ? (Math.abs(v) / 1e6).toFixed(2) + "m" : Math.abs(v) >= 1e3 ? (Math.abs(v) / 1e3).toFixed(1) + "k" : Math.abs(v));
const dS = s => new Date(s + "T00:00:00Z").toLocaleDateString("en-GB", {day: "numeric", month: "short", year: "numeric", timeZone: "UTC"}), dM = s => new Date(s + "T00:00:00Z").toLocaleDateString("en-GB", {day: "numeric", month: "short", timeZone: "UTC"});
const mean = a => a.reduce((s, x) => s + x, 0) / a.length, sd = a => { const m = mean(a); return Math.sqrt(mean(a.map(x => (x - m) ** 2))); };
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
// 0 (short end, violet) to 100 (long end, cyan), dark in the middle
const col = (p, a = 1) => { if (p == null) return "rgba(255,255,255,.03)"; const t = (p - 50) / 50, k = Math.pow(Math.abs(t), .8); const c = t >= 0 ? [92, 225, 255] : [179, 157, 255], b = [16, 20, 22]; return `rgba(${c.map((x, i) => Math.round(b[i] + (x - b[i]) * k)).join(",")},${a})`; };
const SHORTN = n => n.replace("E-mini ", "").replace(" Treasury note", " note").replace("US dollar index", "Dollar index").replace("Treasury bond", "T-bond").replace("Japanese ", "").replace("British ", "").replace("Australian dollar", "Aussie").replace("Canadian dollar", "Loonie").replace("Mexican ", "").replace("Swiss ", "").replace(" crude oil", "");

// ---- items, the same shape for both views ----
const GROUPS = ["Equities", "Rates", "Currencies", "Commodities", "Crypto"];
const HN = 52;
const COT = D.cot.map(c => { const w = c.w, n = w.length, s = w.map(x => x[4]), srt = [...s].sort((a, b) => a - b), rank = v => { let lo = 0; while (lo < n && srt[lo] < v) lo++; let hi = lo; while (hi < n && srt[hi] <= v) hi++; return n > 1 ? ((lo + hi - 1) / 2) / (n - 1) * 100 : 50; };
  const L = w[n - 1], z = sd(s) ? (L[4] - mean(s)) / sd(s) : 0;
  return {id: c.n, name: c.n, sn: SHORTN(c.n), g: c.g, val: L[4], d1: n > 1 ? L[4] - w[n - 2][4] : 0, d4: n > 4 ? L[4] - w[n - 5][4] : 0, p: c.p, z, s, dates: w.map(x => x[0]), heat: s.slice(-HN).map(rank), hdates: w.slice(-HN).map(x => x[0]), w, raw: L}; });
const nS = D.dates.length;
const SH = Object.entries(D.sh).map(([t, s]) => { const r = s.r, last = r[nS - 1], prev = r.slice(0, -1).filter(x => x != null); if (last == null || prev.length < 12) return null; const m = mean(prev), sv = sd(prev) || 1;
  return {id: t, name: t, sn: t, g: "", val: last, d1: r[nS - 2] == null ? 0 : last - r[nS - 2], d4: last - m, p: clamp(50 + (last - m) / sv * 16.7, 0, 100), z: (last - m) / sv, s: r, dates: D.dates, heat: r.map(v => v == null ? null : clamp(50 + (v - m) / sv * 16.7, 0, 100)), hdates: D.dates, vol: s.v, avg: m}; }).filter(Boolean).sort((a, b) => b.vol - a.vol);
let mode = "cot", sel = {cot: COT.find(c => c.name === "Euro"), short: SH.find(s => s.id === "NVDA") || SH[0]};
const items = () => mode === "cot" ? COT : SH.slice(0, 40);

function setup(cv) { const w = cv.clientWidth, h = cv.clientHeight, d = Math.min(2, devicePixelRatio || 1); cv.width = w * d; cv.height = h * d; const g = cv.getContext("2d"); g.setTransform(d, 0, 0, d, 0, 0); return {g, w, h}; }
function tipAt(tip, cv, x, y, html) { tip.innerHTML = html; tip.style.left = clamp(x + 14, 2, cv.clientWidth - tip.offsetWidth - 2) + "px"; tip.style.top = clamp(y + 14, 2, cv.clientHeight - tip.offsetHeight - 2) + "px"; tip.style.opacity = 1; }
function area(g, pts, base, stroke, fillTop, glow) { if (pts.length < 2) return; g.beginPath(); pts.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.save(); if (glow) { g.shadowColor = glow; g.shadowBlur = 10; } g.strokeStyle = stroke; g.lineWidth = 1.5; g.lineJoin = "round"; g.stroke(); g.restore();
  g.lineTo(pts[pts.length - 1][0], base); g.lineTo(pts[0][0], base); g.closePath(); const ys = pts.map(p => p[1]), gr = g.createLinearGradient(0, Math.min(...ys, base), 0, Math.max(...ys, base)); const up = Math.min(...ys) < base;
  gr.addColorStop(up ? 0 : 1, fillTop); gr.addColorStop(up ? 1 : 0, "rgba(0,0,0,0)"); g.fillStyle = gr; g.fill(); }

// ---- heatmap: one row per instrument, one column per period ----
function heat() { const cv = $("heat"), tip = $("t1"), {g, w, h} = setup(cv), IT = items(), cols = IT[0].heat.length, cot = mode === "cot";
  const L = {l: cot ? 104 : 54, r: 46, t: 2, b: 18}, rows = [], gaps = cot ? GROUPS.length - 1 : 0; let y = L.t; const rh = (h - L.t - L.b - gaps * 5) / IT.length, cw = (w - L.l - L.r) / cols;
  let lastG = null; for (const it of IT) { if (cot && lastG !== null && it.g !== lastG) y += 5; lastG = it.g; rows.push({it, y}); y += rh; }
  g.textBaseline = "middle";
  for (const {it, y} of rows) { const on = it === sel[mode];
    for (let c = 0; c < cols; c++) { g.fillStyle = col(it.heat[c]); g.fillRect(L.l + c * cw, y, Math.ceil(cw) - (cw > 5 ? 1 : 0), rh - 1); }
    g.font = (on ? "600 " : "400 ") + "10.5px " + F; g.textAlign = "right"; g.fillStyle = on ? "#fff" : "#a7aeb3"; g.fillText(it.sn, L.l - 8, y + rh / 2);
    g.textAlign = "left"; g.fillStyle = "#f2f4f5"; g.font = "500 10.5px " + F; g.fillText(cot ? Math.round(it.p) : it.val.toFixed(0) + "%", w - L.r + 8, y + rh / 2);
    if (on) { g.strokeStyle = "#fff"; g.lineWidth = 1; g.strokeRect(L.l - .5, y - .5, cols * cw, rh); } }
  g.textBaseline = "alphabetic"; g.font = "400 10px " + F; g.fillStyle = "#6c757b"; const nt = 6; for (let j = 0; j <= nt; j++) { const c = Math.round(j / nt * (cols - 1)); g.textAlign = j === 0 ? "left" : j === nt ? "right" : "center"; g.fillText(cot ? new Date(IT[0].hdates[c] + "T00:00:00Z").toLocaleDateString("en-GB", {month: "short", year: "2-digit", timeZone: "UTC"}) : dM(IT[0].hdates[c]), L.l + (c + .5) * cw, h - 4); }
  cv.onpointermove = e => { const r = cv.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top, row = rows.find(q => my >= q.y && my < q.y + rh), c = Math.floor((mx - L.l) / cw); cv._row = row; cv.style.cursor = row ? "pointer" : "";
    if (row && c >= 0 && c < cols) { const it = row.it, i = it.s.length - cols + c; tipAt(tip, cv, mx, my, cot ? `<b>${esc(it.name)}</b><br><i>${dS(it.hdates[c])}</i><br>Net ${lv(it.s[i])}% of open interest<br>${Math.round(it.heat[c])} of 100 in its 3-year range` : `<b>${it.name}</b><br><i>${dS(it.hdates[c])}</i><br>${it.s[c] == null ? "No figure" : it.s[c].toFixed(1) + "% of volume sold short"}<br>Its average ${it.avg.toFixed(1)}%`); } else tip.style.opacity = 0; };
  cv.onpointerleave = () => tip.style.opacity = 0; cv.onclick = () => { if (cv._row) pick(cv._row.it); }; }

// ---- small multiples ----
function mini(cv, it) { const {g, w, h} = setup(cv), v = it.s, a = v.filter(x => x != null), zero = mode === "cot", mn = Math.min(...a, zero ? 0 : Infinity), mx = Math.max(...a, zero ? 0 : -Infinity), Y = y => 3 + (1 - (y - mn) / ((mx - mn) || 1)) * (h - 6), base = zero ? Y(0) : Y(it.avg);
  g.strokeStyle = "rgba(255,255,255,.16)"; g.setLineDash(zero ? [] : [2, 3]); g.beginPath(); g.moveTo(0, base + .5); g.lineTo(w, base + .5); g.stroke(); g.setLineDash([]);
  const pts = []; v.forEach((y, i) => { if (y != null) pts.push([i / (v.length - 1) * w, Y(y)]); }); const c = col(it.p).replace(/rgba\((\d+),(\d+),(\d+),[\d.]+\)/, (m, r, gg, b) => `${Math.max(120, +r)},${Math.max(130, +gg)},${Math.max(140, +b)}`);
  area(g, pts, base, `rgb(${c})`, `rgba(${c},.34)`, null); const lp = pts[pts.length - 1]; g.fillStyle = "#fff"; g.beginPath(); g.arc(lp[0] - 1.5, lp[1], 1.8, 0, 7); g.fill(); }
function multiples() { const IT = mode === "cot" ? COT : SH.slice(0, 32), el = $("sm");
  el.innerHTML = IT.map(it => `<button class="m${it === sel[mode] ? " on" : ""}" data-id="${esc(it.id)}"><span><em>${esc(it.sn)}</em><b>${mode === "cot" ? lv(it.val, 0) : it.val.toFixed(0)}%</b></span><canvas></canvas></button>`).join("");
  el.querySelectorAll(".m").forEach(b => { const it = IT.find(x => x.id === b.dataset.id); mini(b.querySelector("canvas"), it); b.onclick = () => pick(it); }); }

// ---- crowding against momentum ----
function scatter() { const cv = $("sc"), tip = $("t3"), {g, w, h} = setup(cv), IT = items(), cot = mode === "cot", L = {l: 34, r: 10, t: 6, b: 22};
  const ymax = Math.max(...IT.map(i => Math.abs(i.d4)), 1) * 1.15, X = p => L.l + p / 100 * (w - L.l - L.r), Y = v => L.t + (1 - (v + ymax) / (2 * ymax)) * (h - L.t - L.b);
  const q = (x0, x1, y0, y1, c) => { g.fillStyle = c; g.fillRect(X(x0), Y(y1), X(x1) - X(x0), Y(y0) - Y(y1)); }; q(50, 100, 0, ymax, "rgba(92,225,255,.05)"); q(0, 50, -ymax, 0, "rgba(179,157,255,.05)");
  g.strokeStyle = "rgba(255,255,255,.16)"; g.beginPath(); g.moveTo(X(50) + .5, L.t); g.lineTo(X(50) + .5, h - L.b); g.moveTo(L.l, Y(0) + .5); g.lineTo(w - L.r, Y(0) + .5); g.stroke();
  g.font = "400 10px " + F; g.fillStyle = "#6c757b"; g.textAlign = "left"; g.fillText(cot ? "Most short" : "Below its average", L.l, h - 5); g.textAlign = "right"; g.fillText(cot ? "Most long" : "Above its average", w - L.r, h - 5); g.textAlign = "center"; g.fillText(cot ? "3-year percentile" : "against its own average", X(50), h - 5);
  g.textAlign = "right"; g.fillText(lv(ymax, 0), L.l - 5, Y(ymax) + 9); g.fillText(lv(-ymax, 0), L.l - 5, Y(-ymax) - 2); g.fillText("0", L.l - 5, Y(0) + 3);
  g.fillStyle = "rgba(255,255,255,.34)"; g.font = "500 10px " + F; g.textAlign = "right"; g.fillText(cot ? "Crowded long, still adding" : "High and rising", w - L.r - 6, L.t + 12); g.textAlign = "left"; g.fillText(cot ? "Crowded short, still selling" : "Low and falling", L.l + 6, h - L.b - 6);
  const pts = IT.map(it => ({it, x: X(it.p), y: Y(cot ? it.d4 : it.d1)}));
  for (const p of pts) { const on = p.it === sel[mode], ext = p.it.p <= 10 || p.it.p >= 90, r = on ? 6 : ext ? 4.5 : 3.2, c = col(p.it.p).replace(/rgba\((\d+),(\d+),(\d+),[\d.]+\)/, (m, a, b, cc) => `${Math.max(140, +a)},${Math.max(150, +b)},${Math.max(165, +cc)}`);
    if (ext || on) { const gl = g.createRadialGradient(p.x, p.y, 0, p.x, p.y, 18); gl.addColorStop(0, `rgba(${c},.5)`); gl.addColorStop(1, `rgba(${c},0)`); g.fillStyle = gl; g.beginPath(); g.arc(p.x, p.y, 18, 0, 7); g.fill(); }
    g.fillStyle = `rgb(${c})`; g.beginPath(); g.arc(p.x, p.y, r, 0, 7); g.fill(); if (on) { g.strokeStyle = "#fff"; g.lineWidth = 1.5; g.stroke(); }
    if (ext || on) { g.font = (on ? "600 " : "500 ") + "10.5px " + F; g.fillStyle = "#f2f4f5"; g.textAlign = p.x > w - 90 ? "right" : "left"; g.fillText(p.it.sn, p.x + (p.x > w - 90 ? -9 : 9), p.y + 3.5); } }
  cv.onpointermove = e => { const r = cv.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top; let b = null, bd = 16; for (const p of pts) { const d = Math.hypot(p.x - mx, p.y - my); if (d < bd) { bd = d; b = p; } } cv._p = b; cv.style.cursor = b ? "pointer" : "";
    if (b) tipAt(tip, cv, mx, my, cot ? `<b>${esc(b.it.name)}</b><br>${Math.round(b.it.p)} of 100 in 3 years<br>4 weeks: ${sg(b.it.d4)} pts of OI` : `<b>${b.it.name}</b><br>${b.it.val.toFixed(1)}% sold short, z ${lv(b.it.z, 2)}<br>1 day: ${sg(b.it.d1)} pts`); else tip.style.opacity = 0; };
  cv.onpointerleave = () => tip.style.opacity = 0; cv.onclick = () => { if (cv._p) pick(cv._p.it); }; }

// ---- flows: the period's change, ranked ----
function flows() { const cv = $("fl"), tip = $("t4"), {g, w, h} = setup(cv), IT = [...items()].sort((a, b) => b.d1 - a.d1), n = IT.length, L = {l: 8, r: 8, t: 16, b: 46}, bw = (w - L.l - L.r) / n, mx = Math.max(...IT.map(i => Math.abs(i.d1)), .1) * 1.1, Y = v => L.t + (1 - (v + mx) / (2 * mx)) * (h - L.t - L.b);
  g.strokeStyle = "rgba(255,255,255,.18)"; g.beginPath(); g.moveTo(L.l, Y(0) + .5); g.lineTo(w - L.r, Y(0) + .5); g.stroke();
  IT.forEach((it, i) => { const x = L.l + i * bw, on = it === sel[mode], up = it.d1 >= 0, y0 = Y(0), y1 = Y(it.d1), gr = g.createLinearGradient(0, Math.min(y0, y1), 0, Math.max(y0, y1));
    const c = up ? "31,210,122" : "255,75,82"; gr.addColorStop(up ? 0 : 1, `rgba(${c},1)`); gr.addColorStop(up ? 1 : 0, `rgba(${c},.25)`); g.fillStyle = gr; g.fillRect(x + 1.5, Math.min(y0, y1), Math.max(2, bw - 3), Math.abs(y1 - y0) || 1);
    if (on) { g.strokeStyle = "#fff"; g.lineWidth = 1; g.strokeRect(x + 1, Math.min(y0, y1) - .5, Math.max(2, bw - 2), Math.abs(y1 - y0) + 1); }
    g.save(); g.translate(x + bw / 2 + 3, h - L.b + 6); g.rotate(Math.PI / 2.6); g.font = (on ? "600 " : "400 ") + "9.5px " + F; g.fillStyle = on ? "#fff" : "#8b9399"; g.textAlign = "left"; g.fillText(it.sn, 0, 0); g.restore(); });
  g.font = "500 10px " + F; g.textAlign = "left"; g.fillStyle = "#1fd27a"; g.fillText(lv(IT[0].d1) + " " + IT[0].sn, L.l + 2, 10); g.textAlign = "right"; g.fillStyle = "#ff4b52"; g.fillText(IT[n - 1].sn + " " + lv(IT[n - 1].d1), w - L.r - 2, 10);
  cv.onpointermove = e => { const r = cv.getBoundingClientRect(), i = Math.floor((e.clientX - r.left - L.l) / bw), it = IT[i]; cv._it = it; cv.style.cursor = it ? "pointer" : ""; if (it) tipAt(tip, cv, e.clientX - r.left, e.clientY - r.top, `<b>${esc(it.name)}</b><br>${mode === "cot" ? "Week" : "Day"}: ${sg(it.d1)} points${mode === "cot" ? " of open interest" : ""}`); else tip.style.opacity = 0; };
  cv.onpointerleave = () => tip.style.opacity = 0; cv.onclick = () => { if (cv._it) pick(cv._it); }; }

// ---- the selected instrument ----
function detail() { const it = sel[mode], cot = mode === "cot", cv = $("dt"), tip = $("t5");
  $("det").innerHTML = cot ? `<div><h2>${esc(it.name)}</h2><p><span>Long <b>${kk(it.raw[1])}</b></span><span>Short <b>${kk(it.raw[2])}</b></span><span>Net <b>${kk(it.raw[3])}</b></span><span>OI <b>${kk(it.raw[5])}</b></span></p></div><div class="f"><b>${lv(it.val)}%</b><span>of OI · z ${lv(it.z, 2)} · ${Math.round(it.p)} of 100</span></div>`
    : `<div><h2>${it.name}</h2><p><span>Average <b>${it.avg.toFixed(1)}%</b></span><span>Volume <b>${kk(it.vol)}</b></span></p></div><div class="f"><b>${it.val.toFixed(1)}%</b><span>sold short · ${sg(it.d4)} pts vs avg · z ${lv(it.z, 2)}</span></div>`;
  const render = hv => { const {g, w, h} = setup(cv), L = {l: 34, r: 8, t: 6, b: 18}, n = it.s.length, ser = cot ? [it.w.map(x => x[1] / x[5] * 100), it.w.map(x => -x[2] / x[5] * 100), it.s] : [it.s, D.mkt];
    const all = ser.flat().filter(x => x != null), mn0 = Math.min(...all, cot ? 0 : Infinity), mx0 = Math.max(...all), pad = (mx0 - mn0) * .07 || 1, mn = mn0 - pad, mx = mx0 + pad, X = i => L.l + i / (n - 1) * (w - L.l - L.r), Y = v => L.t + (1 - (v - mn) / (mx - mn)) * (h - L.t - L.b);
    g.font = "400 10px " + F; g.fillStyle = "#6c757b"; g.textAlign = "right"; for (let j = 0; j <= 3; j++) { const v = mn0 + (mx0 - mn0) * j / 3; g.strokeStyle = "rgba(255,255,255,.055)"; g.beginPath(); g.moveTo(L.l, Y(v) + .5); g.lineTo(w - L.r, Y(v) + .5); g.stroke(); g.fillText(cot ? lv(v, 0) : v.toFixed(0), L.l - 5, Y(v) + 3); }
    for (let j = 0; j <= 4; j++) { const i = Math.round(j / 4 * (n - 1)); g.textAlign = j === 0 ? "left" : j === 4 ? "right" : "center"; g.fillText(cot ? new Date(it.dates[i] + "T00:00:00Z").toLocaleDateString("en-GB", {month: "short", year: "2-digit", timeZone: "UTC"}) : dM(it.dates[i]), X(i), h - 4); }
    const P = v => v.map((y, i) => y == null ? null : [X(i), Y(y)]).filter(Boolean), base = cot ? Y(0) : Y(it.avg);
    if (cot) { g.strokeStyle = "rgba(255,255,255,.3)"; g.beginPath(); g.moveTo(L.l, base + .5); g.lineTo(w - L.r, base + .5); g.stroke(); area(g, P(ser[0]), base, "rgba(92,225,255,.75)", "rgba(92,225,255,.16)"); area(g, P(ser[1]), base, "rgba(179,157,255,.75)", "rgba(179,157,255,.16)"); area(g, P(ser[2]), base, "#fff", "rgba(255,255,255,0)", "rgba(255,255,255,.7)"); }
    else { g.setLineDash([3, 4]); g.strokeStyle = "#8b9399"; g.beginPath(); g.moveTo(L.l, base); g.lineTo(w - L.r, base); g.stroke(); g.setLineDash([]); const m = P(ser[1]); g.beginPath(); m.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.strokeStyle = "rgba(255,255,255,.3)"; g.lineWidth = 1; g.stroke(); area(g, P(ser[0]), Y(mn0), "#5ce1ff", "rgba(92,225,255,.22)", "rgba(92,225,255,.8)"); }
    if (hv != null) { g.strokeStyle = "rgba(255,255,255,.4)"; g.lineWidth = 1; g.beginPath(); g.moveTo(X(hv) + .5, L.t); g.lineTo(X(hv) + .5, h - L.b); g.stroke(); tipAt(tip, cv, X(hv), 0, cot ? `<b>${dS(it.dates[hv])}</b><br>Long ${kk(it.w[hv][1])} · short ${kk(it.w[hv][2])}<br>Net ${lv(it.s[hv])}% of OI` : `<b>${dS(it.dates[hv])}</b><br>${it.name} ${it.s[hv] == null ? "–" : it.s[hv].toFixed(1) + "%"} · market ${D.mkt[hv].toFixed(1)}%`); } else tip.style.opacity = 0;
    cv.onpointermove = e => { const r = cv.getBoundingClientRect(); render(clamp(Math.round((e.clientX - r.left - L.l) / (w - L.l - L.r) * (n - 1)), 0, n - 1)); }; cv.onpointerleave = () => render(null); }; render(null); }

function kpis() { const cot = mode === "cot", pickN = cot ? ["E-mini S&P 500", "10-year Treasury note", "US dollar index", "WTI crude oil", "Gold", "Bitcoin"].map(n => COT.find(c => c.name === n)).filter(Boolean) : (() => { const want = ["SPY", "QQQ", "NVDA", "TSLA", "AAPL", "IWM"].map(t => SH.find(s => s.id === t)).filter(Boolean); for (const s of SH) { if (want.length >= 6) break; if (!want.includes(s)) want.push(s); } return want.slice(0, 6); })();
  $("kpis").innerHTML = pickN.map(it => `<button class="p k${it === sel[mode] ? " on" : ""}" data-id="${esc(it.id)}"><canvas></canvas><span>${esc(cot ? it.sn : it.name)}</span><div class="v"><b>${cot ? lv(it.val) : it.val.toFixed(1)}</b><i>${sg(it.d1)} ${cot ? "wk" : "d"}</i></div><div class="g"><i style="left:${it.p}%"></i></div><small><span>${cot ? "Short" : "Low"}</span><span>${cot ? Math.round(it.p) + " of 100" : "z " + lv(it.z, 2)}</span><span>${cot ? "Long" : "High"}</span></small></button>`).join("");
  $("kpis").querySelectorAll(".k").forEach(b => { const it = pickN.find(x => x.id === b.dataset.id); b.onclick = () => pick(it); const cv = b.querySelector("canvas"), {g, w, h} = setup(cv), v = it.s.slice(-52).filter(x => x != null), mn = Math.min(...v), mx = Math.max(...v), pts = v.map((y, i) => [i / (v.length - 1) * w, 6 + (1 - (y - mn) / ((mx - mn) || 1)) * (h - 12)]);
    const gr = g.createLinearGradient(0, 0, w, 0); gr.addColorStop(0, "rgba(255,255,255,0)"); gr.addColorStop(1, "rgba(255,255,255,.75)"); g.strokeStyle = gr; g.lineWidth = 1.3; g.beginPath(); pts.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.stroke(); }); }

function draw() { const cot = mode === "cot"; document.querySelectorAll("[data-m]").forEach(b => b.setAttribute("aria-pressed", b.dataset.m === mode));
  $("asof").innerHTML = cot ? `CFTC Commitments of Traders, positions as of <b>${dS(D.asof)}</b> &nbsp;·&nbsp; ${COT.length} futures &nbsp;·&nbsp; speculators' net, % of open interest` : `FINRA short sale volume, session <b>${dS(D.dates[nS - 1])}</b> &nbsp;·&nbsp; market ${D.mkt[nS - 1].toFixed(1)}% sold short &nbsp;·&nbsp; ${SH.length} shares`;
  $("h1").textContent = cot ? "Positioning heatmap, 52 weeks" : "Short selling heatmap, 30 sessions"; $("h1s").innerHTML = cot ? `<span>Most short in 3 yrs</span><i></i><span>Most long</span>` : `<span>Below its average</span><i></i><span>Above</span>`;
  $("h2").textContent = cot ? "Every contract, three years" : "Most traded shares"; $("h2s").textContent = cot ? "net % of OI, zero line" : "short % of volume, own average dashed";
  $("h3").textContent = cot ? "Crowding against momentum" : "Level against the day's change"; $("h3s").textContent = cot ? "across: 3-year percentile · up: 4-week change" : "across: vs own average · up: 1-day change";
  $("h4").textContent = cot ? "The week's flows" : "The day's changes"; $("h4s").textContent = cot ? "change in net, points of OI" : "points, 40 most traded";
  $("h5").textContent = cot ? "Contract" : "Share"; $("h5s").textContent = cot ? "net, longs and shorts, % of OI" : "against the market and its average";
  kpis(); heat(); multiples(); scatter(); flows(); detail(); }
function pick(it) { sel[mode] = it; draw(); }
document.querySelectorAll("[data-m]").forEach(b => b.onclick = () => { mode = b.dataset.m; draw(); });
addEventListener("resize", draw); (document.fonts ? document.fonts.ready : Promise.resolve()).then(draw); requestAnimationFrame(draw);
window.__api = {setMode: m => { mode = m; draw(); }};
}).catch(function (e) { document.documentElement.classList.add("hf-nodata"); console.error(e); });
})();
