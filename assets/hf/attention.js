/* Hedge Fund Data: Attention. The page's figures are in a JSON file beside it, named by <meta name="hf-data">;
   tools/page_hedgefund.py writes both. Nothing here is fetched from anywhere else. */
(function () {
"use strict";
var meta = document.querySelector('meta[name="hf-data"]'); if (!meta) return;
fetch(meta.content).then(function (r) { if (!r.ok) throw new Error("data " + r.status); return r.json(); }).then(function (DATA) {
const D = DATA;
const $ = id => document.getElementById(id), esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const F = "Inter, 'Helvetica Neue', Arial, sans-serif";
const num = v => v >= 1e6 ? (v / 1e6).toFixed(2) + "M" : v >= 1e4 ? (v / 1e3).toFixed(1) + "K" : Math.round(v).toLocaleString("en-US");
const xf = x => x >= 10 ? x.toFixed(0) + "×" : x.toFixed(1) + "×";
const dS = s => new Date(s + "T00:00:00Z").toLocaleDateString("en-GB", {day: "numeric", month: "short", year: "numeric", timeZone: "UTC"}), dW = s => new Date(s + "T00:00:00Z").toLocaleDateString("en-GB", {weekday: "long", timeZone: "UTC"}), dM = s => new Date(s + "T00:00:00Z").toLocaleDateString("en-GB", {day: "2-digit", month: "short", timeZone: "UTC"});
const clamp = (v, a, b) => Math.max(a, Math.min(b, v)), mean = a => a.reduce((s, x) => s + x, 0) / (a.length || 1);
const GROUPS = [...new Set(D.arts.map(a => a.g))], FAM = {Private: [179, 157, 255], Themes: [255, 143, 184], Crypto: [255, 196, 92], Assets: [255, 196, 92], Macro: [226, 230, 233], Geopolitics: [255, 160, 122]}, gcol = (g, a = 1) => `rgba(${(FAM[g] || [92, 225, 255]).join(",")},${a})`;
const dayAt = (first, i) => new Date(Date.parse(first + "T00:00:00Z") + i * 864e5).toISOString().slice(0, 10);
const N = Math.max(...D.arts.map(a => a.v.length)), FIRST = D.arts.find(a => a.v.length === N).f, DAYS = Array.from({length: N}, (_, i) => dayAt(FIRST, i));
// each subject against its own normal: the median of the 90 days before (the whole record, for the first 90)
const med = a => { const s = [...a].sort((x, y) => x - y); return s[s.length >> 1] || 1; };
const S = D.arts.map(a => { const v = new Array(N - a.v.length).fill(0).concat(a.v.map(x => x ?? 0)), all = med(v.filter(x => x > 0)), early = med(v.slice(0, 90).filter(x => x > 0)) || all, base = v.map((_, i) => i >= 90 ? med(v.slice(i - 90, i)) || all : early), x = v.map((y, i) => y / (Math.max(base[i] || 1, 50))); let pk = 0; x.forEach((y, i) => { if (y > x[pk]) pk = i; });
  return {k: a.k, n: a.n, art: a.a, g: a.g, v, x, pk, small: all < 40}; }).filter(s => !s.small);
let order = "group", win = Math.min(400, N), cur = N - 1, ordCur = N - 1, sel = null, flt = {cap: 8, g: null, q: ""};
const V = () => { const q = flt.q.trim().toLowerCase(); return S.filter(s => (!flt.g || s.g === flt.g) && (!q || s.n.toLowerCase().includes(q) || s.k.toLowerCase() === q)); };
const rows = () => { const v = V(); return order === "group" ? GROUPS.flatMap(g => v.filter(s => s.g === g)) : order === "day" ? v.sort((a, b) => b.x[ordCur] - a.x[ordCur]) : v.sort((a, b) => a.pk - b.pk); };

function wall() { const cv = $("wall"), wl = $("wl"), tip = $("t1"), d = Math.min(2, devicePixelRatio || 1), w = wl.clientWidth, h = wl.clientHeight; if (!w || !h) return; cv.style.height = h + "px"; if (cv.width !== w * d || cv.height !== h * d) { cv.width = w * d; cv.height = h * d; } const g = cv.getContext("2d"); g.setTransform(d, 0, 0, d, 0, 0);
  const R = rows(), L = {l: 168, r: 54, t: 46, b: 20}, i0 = N - win, n = win, rh = Math.max(22, (h - L.t - L.b) / Math.max(R.length, 1)), amp = Math.min(rh, 30) * 3.4; $("sp").style.height = Math.max(0, R.length * rh + L.t + L.b - h) + "px"; const sy = wl.scrollTop, X = i => L.l + (i - i0) / (n - 1) * (w - L.l - L.r), yOf = r => L.t + (r + 1) * rh - sy; cv._rh = rh; g.clearRect(0, 0, w, h); const H = x => Math.min(x, flt.cap) / flt.cap * amp * (flt.cap / 4);
  // months
  g.font = "400 10px " + F; g.fillStyle = "#69727a"; g.textAlign = "left"; for (let i = i0; i < N; i++) if (DAYS[i].slice(8) === "01") { g.strokeStyle = "rgba(255,255,255,.045)"; g.beginPath(); g.moveTo(X(i) + .5, L.t - 30); g.lineTo(X(i) + .5, h - L.b); g.stroke(); if (win > 120 || true) g.fillText(new Date(DAYS[i] + "T00:00:00Z").toLocaleDateString("en-GB", {month: "short", year: DAYS[i].slice(5, 7) === "01" ? "2-digit" : undefined, timeZone: "UTC"}), X(i) + 4, h - 5); }
  const hot = cv._hot; g.save(); g.beginPath(); g.rect(0, 34, w, h - L.b - 34); g.clip();
  if (!R.length) { g.fillStyle = "#8a9196"; g.font = "400 13px " + F; g.textAlign = "center"; g.fillText("No subject matches. Clear the search or pick another group.", w / 2, h / 2); }
  R.forEach((s, r) => { const y0 = yOf(r); if (y0 < 30 || y0 - amp > h) return; const on = s === sel || s.k === hot, dim = (sel || hot) && !on;
    g.beginPath(); g.moveTo(X(i0), y0); for (let i = i0; i < N; i++) g.lineTo(X(i), y0 - H(Math.max(0, s.x[i] - .0)) * .25 - 0); g.lineTo(X(N - 1), y0); g.closePath();
    g.fillStyle = "rgba(7,9,11,.94)"; g.fill();
    const gr = g.createLinearGradient(0, y0 - amp, 0, y0); gr.addColorStop(0, gcol(s.g, dim ? .1 : on ? .55 : .34)); gr.addColorStop(1, gcol(s.g, 0)); g.fillStyle = gr; g.fill();
    g.beginPath(); for (let i = i0; i < N; i++) { const yy = y0 - H(s.x[i]) * .25; i === i0 ? g.moveTo(X(i), yy) : g.lineTo(X(i), yy); } g.strokeStyle = gcol(s.g, dim ? .22 : on ? 1 : .8); g.lineWidth = on ? 1.6 : 1; g.lineJoin = "round"; g.stroke();
    g.textAlign = "right"; g.textBaseline = "alphabetic"; g.font = (on ? "600 " : "400 ") + "11px " + F; g.fillStyle = dim ? "#4d555b" : on ? "#fff" : "#c3c9ce"; g.fillText(s.n, L.l - 12, y0 - 2);
    const x = s.x[cur]; g.textAlign = "left"; g.font = "400 10.5px " + F; g.fillStyle = dim ? "#4d555b" : x >= 2 ? "#fff" : "#8a9196"; g.fillText(xf(x), w - L.r + 10, y0 - 2);
    if (order === "group") { g.fillStyle = gcol(s.g, .9); g.fillRect(6, y0 - rh + 3, 2, rh - 2); } });
  // group names down the side when ordered by group

  // the day under the cursor
  const cx = X(clamp(cur, i0, N - 1)); g.strokeStyle = "rgba(255,255,255,.75)"; g.lineWidth = 1; g.beginPath(); g.moveTo(cx + .5, L.t - 30); g.lineTo(cx + .5, h - L.b); g.stroke();
  R.forEach((s, r) => { const yy = yOf(r) - H(s.x[cur]) * .25; if (yy < 30 || yy > h) return; g.fillStyle = (sel && s !== sel) ? "rgba(255,255,255,.35)" : "#fff"; g.beginPath(); g.arc(cx, yy, s === sel ? 3 : 1.8, 0, 7); g.fill(); }); g.restore();
  if (R.length * rh > h - L.t - L.b + 1) { g.font = "400 10px " + F; g.fillStyle = "#69727a"; g.textAlign = "left"; g.fillText(`${R.length} subjects, scroll for more`, 16, L.t - 20); }
  g.font = "600 11px " + F; g.textAlign = cx > w - 160 ? "right" : "left"; g.fillStyle = "#fff"; g.fillText(dS(DAYS[cur]), cx + (cx > w - 160 ? -8 : 8), L.t - 20);
  g.font = "400 10px " + F; g.fillStyle = "#69727a"; g.textAlign = "left"; g.fillText("that day", w - L.r + 10, L.t - 20);
  const at = e => { const b = cv.getBoundingClientRect(), mx = e.clientX - b.left, my = e.clientY - b.top, i = clamp(Math.round(i0 + (mx - L.l) / (w - L.l - L.r) * (n - 1)), i0, N - 1); let best = null, bd = 1e9; R.forEach((s, r) => { const yy = yOf(r) - H(s.x[i]) * .25, dd = my - yy; if (dd >= -6 && my <= yOf(r) + 2 && dd < bd) { bd = dd; best = s; } }); if (!best && R.length) { const r = clamp(Math.floor((my - L.t + sy) / rh), 0, R.length - 1); best = my > L.t - 10 ? R[r] : null; } return {i, s: best, mx, my, inside: mx >= L.l - 4 && mx <= w - L.r + 4}; };
  cv.style.cursor = "crosshair"; wl.onscroll = () => { tip.style.opacity = 0; wall(); };
  cv.onpointermove = e => { const {i, s, mx, my, inside} = at(e); if (!inside && mx > L.l) return; const moved = inside && i !== cur, k = s ? s.k : null; if (inside) cur = i; if (moved || k !== cv._hot) { cv._hot = k; wall(); if (moved) side(); } if (s && inside) tipAt(tip, mx, my, `<b>${esc(s.n)}</b><br>${num(s.v[i])} readers, ${xf(s.x[i])} its normal<br><i>Click for tools</i>`); else tip.style.opacity = 0; };
  cv.onpointerleave = () => { tip.style.opacity = 0; if (cv._hot) { cv._hot = null; wall(); } };
  cv.onclick = e => { e.stopPropagation(); const {s} = at(e); tip.style.opacity = 0; openMenu(menuFor(s), e.clientX, e.clientY); }; }
function tipAt(tip, x, y, html) { const cv = $("wall"); tip.innerHTML = html; tip.style.left = clamp(x + 14, 2, cv.clientWidth - tip.offsetWidth - 2) + "px"; tip.style.top = $("wl").scrollTop + clamp(y + 12, 2, cv.clientHeight - tip.offsetHeight - 2) + "px"; tip.style.opacity = 1; }
function side() { const day = DAYS[cur], vis = V(), rk = vis.sort((a, b) => b.x[cur] - a.x[cur]), top = rk[0] || {x: [], v: [], n: ""}, tot = vis.reduce((t, s) => t + s.v[cur], 0), up = vis.filter(s => s.x[cur] >= 1.5).length, mx = Math.max(top.x[cur] || 0, 2);
  $("day").innerHTML = `<small>${dW(day)}${cur === N - 1 ? ", the latest day" : ""}</small><b>${dS(day)}</b><p>${top.x[cur] >= 2 ? `${esc(top.n)} was read ${num(top.v[cur])} times, ${xf(top.x[cur])} its normal.` : "No subject stood far above its normal."} ${up} of ${vis.length} ${flt.g ? esc(flt.g.toLowerCase()) + " " : ""}subjects were at one and a half times their normal or more. ${num(tot)} readers in all.</p>
    <div class="nav"><button id="pv" ${cur <= N - win ? "disabled" : ""}>← Before</button><button id="nx" ${cur >= N - 1 ? "disabled" : ""}>After →</button><button id="now" ${cur === N - 1 ? "disabled" : ""}>Latest</button><button id="pkb">Peak</button></div>`;
  $("pv").onclick = () => go(cur - 1); $("nx").onclick = () => go(cur + 1); $("now").onclick = () => go(N - 1); $("pkb").onclick = () => { const s = sel || [...S].sort((a, b) => b.x[b.pk] - a.x[a.pk])[0]; go(s.pk); };
  $("rkh").textContent = "Most above normal that day";
  $("rk").innerHTML = rk.map((s, i) => `<button data-k="${s.k}" class="${s === sel ? "on" : ""}"><span class="i">${i + 1}</span><span class="n">${esc(s.n)}</span><span class="r dim">${num(s.v[cur])}</span><span class="r" style="color:${s.x[cur] >= 2 ? "#fff" : "var(--ink-2)"}">${xf(s.x[cur])}</span><u style="width:${clamp(s.x[cur] / mx * 100, 1, 100)}%;background:${gcol(s.g)}"></u></button>`).join("");
  $("rk").querySelectorAll("button").forEach(b => b.onclick = () => { const s = S.find(x => x.k === b.dataset.k); sel = sel === s ? null : s; draw(); reveal(); }); }
function go(i) { cur = ordCur = clamp(i, N - win, N - 1); wall(); side(); }
function reveal() { const R = rows(), i = R.indexOf(sel), wl = $("wl"), rh = $("wall")._rh || 22; if (i < 0) return; const y = i * rh; if (y < wl.scrollTop + 20 || y > wl.scrollTop + wl.clientHeight - 110) wl.scrollTop = Math.max(0, y - wl.clientHeight / 2); }
function draw() { ordCur = cur;
  $("grp").innerHTML = `<button data-g="" aria-pressed="${!flt.g}">All<em>${S.length}</em></button>` + GROUPS.map(g => `<button data-g="${esc(g)}" aria-pressed="${flt.g === g}"><i style="background:${gcol(g)}"></i>${esc(g)}<em>${S.filter(s => s.g === g).length}</em></button>`).join("");
  $("grp").querySelectorAll("button").forEach(b => b.onclick = () => { flt.g = b.dataset.g || null; $("wl").scrollTop = 0; draw(); });
  $("meta").innerHTML = `English Wikipedia, readers a day. ${S.length} subjects, ${dM(DAYS[0])} ${DAYS[0].slice(0, 4)} to <b>${dS(D.last)}</b>.`;
  $("ord").innerHTML = [["group", "Group"], ["day", "That day"], ["peak", "When it peaked"]].map(([k, l]) => `<button data-o="${k}" aria-pressed="${order === k}">${l}</button>`).join(""); $("win").innerHTML = [90, 180, 400].map(v => `<button data-w="${v}" aria-pressed="${win === Math.min(v, N)}">${v} days</button>`).join("");
  document.querySelectorAll("[data-o]").forEach(b => b.onclick = () => { order = b.dataset.o; draw(); }); document.querySelectorAll("[data-w]").forEach(b => b.onclick = () => { win = Math.min(+b.dataset.w, N); cur = Math.max(cur, N - win); draw(); });
  const tp = [...S].sort((a, b) => b.x[N - 1] - a.x[N - 1]).slice(0, 40).map(s => `<span><b>${esc(s.n)}</b>${num(s.v[N - 1])} readers, ${xf(s.x[N - 1])} normal</span>`).join(""); $("tape").innerHTML = tp + tp;
  $("chips").innerHTML = sel ? `<button id="cs" title="Clear">${esc(sel.n)} ×</button>` : ""; if (sel) $("cs").onclick = () => { sel = null; draw(); };
  $("foot").innerHTML = `<span>Source: Wikimedia pageviews, English Wikipedia, people only</span><span>Height: readers that day as a multiple of the subject's median over the 90 days before, capped at ${flt.cap}×</span><span class="keys"><span><kbd>←</kbd><kbd>→</kbd>travel in time</span><span><kbd>↑</kbd><kbd>↓</kbd>subject</span><span><kbd>/</kbd>find</span><span><kbd>P</kbd>its peak</span><span><kbd>Esc</kbd>clear</span></span>`;
  wall(); side(); }
// tools
const download = (name, text) => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([text], {type: "text/csv"})); a.download = name; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500); };
const copy = (text, btn) => { const done = () => { btn.querySelector("i").textContent = "Copied"; }; (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject()).then(done, () => { const ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta); ta.select(); try { document.execCommand("copy"); done(); } catch (e) {} ta.remove(); }); };
function menuFor(s) { const doit = f => () => { f(); closeMenu(); draw(); }, day = DAYS[cur];
  if (s) return {title: s.n, sub: `${dS(day)}: ${num(s.v[cur])} readers, ${xf(s.x[cur])} its normal. Its largest day was ${dS(DAYS[s.pk])}, at ${xf(s.x[s.pk])}.`, items: [
    [sel === s ? "Clear the selection" : "Follow this subject", "", doit(() => { sel = sel === s ? null : s; }), sel === s], ["Go to its largest day", "P", doit(() => { sel = s; cur = clamp(s.pk, N - win, N - 1); if (s.pk < N - win) { win = N; cur = s.pk; } })],
    ["Read the article on Wikipedia", "wikipedia.org ↗", `https://en.wikipedia.org/wiki/${s.art}`],
    ["Copy that day's figures", "", b => copy(`${s.n}: ${num(s.v[cur])} Wikipedia readers on ${dS(day)}, ${xf(s.x[cur])} its normal. Source: Wikimedia pageviews via Andra Markets.`, b)],
    ["Download its daily readers", "CSV", () => { download(`andra-attention-${s.k.toLowerCase()}.csv`, "date,readers,times_normal\n" + s.v.map((x, i) => `${DAYS[i]},${x},${s.x[i].toFixed(2)}`).join("\n")); closeMenu(); }]]};
  return {title: "Wall tools", sub: "Click a line for that subject's own tools.", items: [["opt", "Cap the height at", [4, 8, 16], flt.cap, v => { flt.cap = v; closeMenu(); draw(); }], ["Go to the latest day", "", doit(() => { cur = N - 1; })],
    ["Save the wall as an image", "PNG", () => { $("wall").toBlob(b => { const a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = "andra-attention-wall.png"; a.click(); }); closeMenu(); }],
    ["Download every subject", "CSV", () => { download("andra-attention.csv", "date," + S.map(s => s.k).join(",") + "\n" + DAYS.map((d, i) => d + "," + S.map(s => s.v[i]).join(",")).join("\n")); closeMenu(); }], ["Reset", "", doit(() => { sel = null; order = "group"; win = Math.min(400, N); cur = N - 1; flt.cap = 8; flt.g = null; flt.q = ""; $("q").value = ""; })]]}; }
function openMenu(m, x, y) { const el = $("menu"); el.innerHTML = `<header><b>${esc(m.title)}</b><span>${esc(m.sub)}</span></header>` + m.items.map((it, i) => it[0] === "opt" ? `<div class="opt">${it[1]}<span>${it[2].map(v => `<button data-i="${i}" data-v="${v}" aria-pressed="${v === it[3]}">${v}×</button>`).join("")}</span></div>`
    : typeof it[2] === "string" ? `<a role="menuitem" href="${it[2]}" target="_blank" rel="noopener noreferrer">${esc(it[0])}<i>${it[1]}</i></a>` : `<button role="menuitem" data-i="${i}" class="${it[3] ? "is" : ""}">${esc(it[0])}<i>${it[1]}</i></button>`).join("");
  el.classList.add("show"); const w = el.offsetWidth, h = el.offsetHeight; el.style.left = Math.max(8, Math.min(x + 10, innerWidth - w - 8)) + "px"; el.style.top = Math.max(8, Math.min(y + 10, innerHeight - h - 8)) + "px";
  el.querySelectorAll("[data-i]").forEach(b => b.onclick = e => { e.stopPropagation(); const it = m.items[+b.dataset.i]; it[0] === "opt" ? it[4](+b.dataset.v) : it[2](b); }); const f = el.querySelector("button,a"); if (f) f.focus(); }
function closeMenu() { $("menu").classList.remove("show"); }
addEventListener("click", e => { if (!$("menu").contains(e.target)) closeMenu(); });
const tick = () => $("clk").textContent = new Date().toISOString().slice(11, 19) + " UTC"; tick(); setInterval(tick, 1000);
addEventListener("keydown", e => { if ($("menu").classList.contains("show")) { if (e.key === "Escape") closeMenu(); else if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); const fs = [...$("menu").querySelectorAll("a,button")], i = fs.indexOf(document.activeElement); fs[(i + (e.key === "ArrowDown" ? 1 : fs.length - 1)) % fs.length].focus(); } return; }
  if (e.target === $("q")) { if (e.key === "Escape") { $("q").value = ""; flt.q = ""; $("q").blur(); draw(); } return; }
  if (e.key === "/") { e.preventDefault(); $("q").focus(); return; }
  const R = rows(); if (!R.length) return; if (e.key === "ArrowLeft") { e.preventDefault(); go(cur - (e.shiftKey ? 7 : 1)); } else if (e.key === "ArrowRight") { e.preventDefault(); go(cur + (e.shiftKey ? 7 : 1)); }
  else if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); const i = sel ? R.indexOf(sel) : -1; sel = R[clamp(i + (e.key === "ArrowDown" ? 1 : -1), 0, R.length - 1)]; draw(); reveal(); }
  else if (e.key === "p" || e.key === "P") { const s = sel || V().sort((a, b) => b.x[b.pk] - a.x[a.pk])[0]; if (s.pk < N - win) win = N; cur = s.pk; sel = s; draw(); reveal(); } else if (e.key === "Escape") { sel = null; draw(); } });
$("q").oninput = () => { flt.q = $("q").value; $("wl").scrollTop = 0; draw(); };
addEventListener("resize", draw); (document.fonts ? document.fonts.ready : Promise.resolve()).then(draw); requestAnimationFrame(draw);
window.__api = {go, S, N};
}).catch(function (e) { document.documentElement.classList.add("hf-nodata"); console.error(e); });
})();
