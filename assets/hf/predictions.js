/* Hedge Fund Data: Prediction markets. The page's figures are in data.js beside the page (window.HFDATA), which
   tools/page_hedgefund.py writes from .cache/hf/. Nothing here is fetched from anywhere else. */
(function () {
"use strict";
var DATA = window.HFDATA; if (!DATA) { document.documentElement.classList.add("hf-nodata"); return; }
const D = DATA;
const LONG = ["Fed and rates", "Economy", "Markets", "AI and tech", "Crypto", "Geopolitics", "Elections"];
const CATS = [["FED", /\bfed\b|fomc|interest rate/i], ["ECON", /econom|inflation|\bcpi\b|\bgdp\b|unemploy|recession|jobless|payroll|productivity|tariff/i], ["MKTS", /financ|stock|s&p|nasdaq|oil|gold|commodit|ipo|earnings/i],
  ["AI", /\bai\b|nvidia|compute|gpu|tech|openai|anthropic/i], ["CRYPTO", /crypto|bitcoin|ethereum|solana/i], ["GEO", /geopolit|iran|middle east|ceasefire|war|peace|china|russia|ukraine|israel/i], ["POL", /./]];
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const code = e => e.v === "Kalshi" ? e.id.replace("kalshi:", "") : (e.u.split("/").pop() || "").replace(/-\d{10,}$/, "").split("-").filter(w => !/^(in|the|of|will|what|a|an|to|by|on|be)$/.test(w)).slice(0, 3).map(w => w.slice(0, 5)).join(".").toUpperCase();
const E = D.ev.map(e => { const hay = e.t + " " + e.g.join(" "); const c = /elections?|nominee|primar|mayor|president|prime minister/i.test(hay) && !/fed/i.test(e.t) ? 6 : CATS.findIndex(c => c[1].test(hay));
  const o = e.o.map(x => ({l: x[0], p: x[1], prev: x[2], d: x[2] == null ? null : (x[1] - x[2]) * 100, v24: x[3], vol: x[4]})); return {...e, c, o, lead: o[0], tk: code(e)}; });
const px = p => (p * 100).toFixed(p < .1 || p > .9 ? 1 : 0);
const chg = (d, unit = "") => d == null ? '<span class="dim">n/a</span>' : Math.abs(d) < .05 ? '<span class="dim">0.0</span>' : `<span class="${d > 0 ? "up" : "dn"}">${d > 0 ? "+" : "−"}${Math.abs(d).toFixed(1)}${unit}</span>`;
const usd = v => v >= 1e9 ? (v / 1e9).toFixed(2) + "B" : v >= 1e6 ? (v / 1e6).toFixed(1) + "M" : v >= 1e3 ? (v / 1e3).toFixed(0) + "K" : String(Math.round(v));
const date = s => s ? new Date(s).toLocaleDateString("en-GB", {day: "2-digit", month: "short", year: "2-digit", timeZone: "UTC"}) : "n/a";
let cat = -1, venue = "", q = "", sel = E.find(e => /fed decision in dec/i.test(e.t)) || E[0];
const view = () => E.filter(e => (cat < 0 || e.c === cat) && (!venue || e.v === venue) && (!q || (e.tk + " " + e.t + " " + e.o.map(o => o.l).join(" ")).toLowerCase().includes(q))).sort((a, b) => b.v24 - a.v24);

const f0 = new Date(Object.values(D.fetched).sort()[0]);
document.getElementById("s-age").textContent = f0.toISOString().slice(11, 16) + "Z";
document.getElementById("s-n").textContent = E.reduce((s, e) => s + e.o.length, 0).toLocaleString("en-US");
document.getElementById("s-vol").textContent = "$" + usd(E.reduce((s, e) => s + e.v24, 0));
const adv = E.filter(e => (e.lead.d ?? 0) > .05).length, dec = E.filter(e => (e.lead.d ?? 0) < -.05).length;
document.getElementById("s-ad").innerHTML = `<span class="up">${adv}</span> / <span class="dn">${dec}</span>`;
document.getElementById("status").innerHTML = `<span>Polymarket and Kalshi, public market data</span><span>Last: the price of a Yes share, read as a probability in percent</span><span>Day: points</span><span>Daily history since ${f0.toISOString().slice(0, 10)}</span><span>Not a forecast by Andra Markets</span>`;

const movers = E.flatMap(e => e.o.filter(o => o.d != null && o.v24 >= 2000 && o.p > .02 && o.p < .98).map(o => ({e, o}))).sort((a, b) => Math.abs(b.o.d) - Math.abs(a.o.d)).slice(0, 40);
const tape = [...E].sort((a, b) => b.v24 - a.v24).slice(0, 40).map(e => `<span>${esc(e.t.length > 34 ? e.t.slice(0, 33) + "\u2026" : e.t)} <b>${px(e.lead.p)}</b> ${chg(e.lead.d)}</span>`).join("");
document.getElementById("tape").innerHTML = tape + tape;
document.getElementById("movers").innerHTML = movers.map((m, i) => `<button class="mv" data-i="${i}"><span class="n">${esc(m.o.l)}<small>${esc(m.e.t)}</small></span><span class="r">${px(m.o.p)}</span><span class="r">${chg(m.o.d)}</span></button>`).join("");
document.querySelectorAll(".mv").forEach(b => b.onclick = () => pick(movers[+b.dataset.i].e));

// the macro read: one line each, from the most traded matching contract
const K = [["Fed hikes in Dec", /^fed decision in dec/i, /hike 25|25 bps increase/i], ["Fed holds in Jan", /^fed decision in jan/i, /maintain|no change/i], ["US recession this year", /recession this year/i, null], ["US recession in 2027", /recession in 2027/i, null],
  ["Unemployment, Nov, lead", /unemployment in november/i, null], ["CPI, Nov, lead", /^cpi in november/i, null], ["S&P at year end, lead", /s&p close price end of 2026/i, null], ["GDP, Q4, lead", /gdp growth in q4/i, null]];
document.getElementById("kpis").innerHTML = K.map(([name, re, ore], i) => { const e = E.filter(e => re.test(e.t)).sort((a, b) => b.v24 - a.v24)[0]; if (!e) return ""; const o = (ore && e.o.find(o => ore.test(o.l))) || e.lead;
  return `<button class="kpi" data-id="${e.id}"><span>${name}${ore ? "" : e.o.length > 1 ? ": " + esc(o.l) : ""}</span><b>${px(o.p)}</b><i>${chg(o.d)}</i></button>`; }).join("");
document.querySelectorAll(".kpi").forEach(b => b.onclick = () => pick(E.find(e => e.id === b.dataset.id)));

function cats() { const el = document.getElementById("cats"); el.innerHTML = `<button aria-pressed="${cat < 0}" data-c="-1">All</button>` + CATS.map((c, i) => `<button aria-pressed="${cat === i}" data-c="${i}">${LONG[i]}</button>`).join("");
  el.querySelectorAll("button").forEach(b => b.onclick = () => { cat = +b.dataset.c; cats(); blot(); map(); }); }
function blot() { const rows = view(); document.getElementById("b-n").textContent = rows.length + " questions, most traded first";
  document.getElementById("blot").innerHTML = `<div class="bl h"><span>Question</span><span>Leads</span><span class="r">Last</span><span class="r">Day</span><span class="r">Traded</span></div>` + rows.map(e =>
    `<button class="bl${e === sel ? " on" : ""}" data-id="${e.id}" title="${esc(e.t)}"><span class="tk">${esc(e.t)}</span><span class="nm">${esc(e.lead.l)}</span><span class="r">${px(e.lead.p)}</span><span class="r">${chg(e.lead.d)}</span><span class="r dim">${usd(e.v24)}</span></button>`).join("");
  document.querySelectorAll("#blot .bl:not(.h)").forEach(b => b.onclick = () => pick(E.find(e => e.id === b.dataset.id))); }

// squarified treemap
function squarify(items, x, y, w, h) { const out = []; let rest = items.slice(), total = rest.reduce((s, i) => s + i.v, 0);
  while (rest.length) { const side = Math.min(w, h), scale = (w * h) / total; let row = [], best = Infinity, sum = 0;
    for (const it of rest) { const s2 = sum + it.v, mn = Math.min(...row.map(r => r.v), it.v) * scale, mx = Math.max(...row.map(r => r.v), it.v) * scale, a = s2 * scale;
      const worst = Math.max(side * side * mx / (a * a), a * a / (side * side * mn)); if (worst > best) break; best = worst; row.push(it); sum = s2; }
    const a = sum * scale, thick = a / side; let off = 0;
    for (const it of row) { const len = it.v * scale / thick; out.push(w >= h ? {it, x, y: y + off, w: thick, h: len} : {it, x: x + off, y, w: len, h: thick}); off += len; }
    if (w >= h) { x += thick; w -= thick; } else { y += thick; h -= thick; } rest = rest.slice(row.length); total -= sum; }
  return out; }
function map() { const el = document.getElementById("map"), W = el.clientWidth, H = el.clientHeight; const items = view().slice(0, 42).map(e => ({e, v: Math.max(Math.sqrt(e.v24), 30)}));
  if (!items.length) { el.innerHTML = ""; return; }
  el.innerHTML = squarify(items, 0, 0, W, H).map(({it, x, y, w, h}) => { const e = it.e, d = e.lead.d ?? 0, k = Math.min(1, Math.abs(d) / 6);
    const bg = Math.abs(d) < .05 ? "linear-gradient(160deg,#181c1f,#111416)" : d > 0 ? `linear-gradient(160deg,rgb(${Math.round(12 + 6 * k)},${Math.round(58 + 78 * k)},${Math.round(42 + 44 * k)}),rgb(8,${Math.round(36 + 46 * k)},${Math.round(27 + 26 * k)}))` : `linear-gradient(160deg,rgb(${Math.round(78 + 104 * k)},${Math.round(26 + 14 * k)},${Math.round(31 + 16 * k)}),rgb(${Math.round(48 + 66 * k)},17,${Math.round(21 + 8 * k)}))`;
    const big = w > 150 && h > 80, small = w < 62 || h < 34;
    return `<button class="tile${big ? " big" : ""}${e === sel ? " on" : ""}" data-id="${e.id}" title="${esc(e.t)}" style="left:${x}px;top:${y}px;width:${w}px;height:${h}px;background:${bg}"><b>${esc(e.tk)}</b>${small ? "" : `<em>${esc(h > 62 ? e.t : e.lead.l)}</em>`}${h < 30 ? "" : `<i>${px(e.lead.p)} ${d ? (d > 0 ? "+" : "−") + Math.abs(d).toFixed(1) : ""}</i>`}</button>`; }).join("");
  el.querySelectorAll(".tile").forEach(b => b.onclick = () => pick(E.find(e => e.id === b.dataset.id))); }
function fed() { const rows = E.filter(e => e.v === "Kalshi" && /^fed decision in/i.test(e.t)).sort((a, b) => (a.end || "").localeCompare(b.end || "")).slice(0, 8); if (!rows.length) return "";
  const cols = ["Cut >25bps", "Cut 25bps", "Fed maintains rate", "Hike 25bps", "Hike >25bps"], names = ["Cut, over 25", "Cut 25", "Hold", "Raise 25", "Raise, over 25"];
  return `<div class="ph">The Fed, meeting by meeting <span>Kalshi, probability, %</span></div><div class="fed"><div class="hh"><span>Meeting</span>${names.map(n => `<span>${n}</span>`).join("")}</div>` + rows.map(e => `<div><span>${esc(e.t.replace(/^Fed decision in /i, "").replace("?", ""))}</span>` +
    cols.map(c => { const o = e.o.find(x => x.l === c), p = o ? o.p : null; return `<span style="background:rgba(92,225,255,${p == null ? 0 : (p * .5).toFixed(3)});color:${p != null && p >= .1 ? "#fff" : "var(--ink-3)"}">${p == null ? "n/a" : px(p)}</span>`; }).join("") + `</div>`).join("") + `</div>`; }
function ticket() { const e = sel, o = e.lead;
  document.getElementById("ticket").innerHTML = `<div class="tk-h"><div><p class="code">${e.v} &nbsp;&middot;&nbsp; ${LONG[e.c]}</p><h1>${esc(e.t)}</h1>
      <p class="meta"><span>Resolves <b>${date(e.end)}</b></span><span>Traded in 24 h <b>$${usd(e.v24)}</b></span><span>In all <b>$${usd(e.vol)}</b></span><span>Outcomes <b>${e.o.length}</b></span></p></div>
      <div class="px"><b>${px(o.p)}<span>%</span></b><span>${chg(o.d, " pts")}</span><small>${esc(o.l)}</small></div></div>
    <div class="ld h"><span>Outcome</span><span>Implied probability</span><span class="r">Last</span><span class="r">Day</span><span class="r x">24 h, $</span><span class="r x">Total, $</span></div>` +
    e.o.slice(0, 30).map((x, i) => `<div class="ld${i ? "" : " first"}"><span class="l">${esc(x.l)}</span><span class="dp"><i style="width:${x.p * 100}%"></i></span><span class="r">${px(x.p)}</span><span class="r">${chg(x.d)}</span><span class="r dim x">${usd(x.v24)}</span><span class="r dim x">${usd(x.vol)}</span></div>`).join("") + (e.c === 0 ? fed() : ""); }
function pick(e) { sel = e; blot(); map(); ticket(); document.getElementById("ticket").scrollTop = 0; const r = document.querySelector("#blot .on"); if (r) r.scrollIntoView({block: "nearest"}); }
document.querySelectorAll("[data-v]").forEach(b => b.onclick = () => { venue = b.dataset.v; document.querySelectorAll("[data-v]").forEach(x => x.setAttribute("aria-pressed", x === b)); cats(); blot(); map(); });
document.getElementById("q").addEventListener("input", e => { q = e.target.value.trim().toLowerCase(); blot(); map(); });
addEventListener("resize", map);
cats(); blot(); ticket(); requestAnimationFrame(map);
window.__api = {E, pick};
})();
