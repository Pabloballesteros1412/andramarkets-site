/* Hedge Fund Data: Ships. The page's figures are in data.js beside the page (window.HFDATA), which
   tools/page_hedgefund.py writes from .cache/hf/. Nothing here is fetched from anywhere else. */
(function () {
"use strict";
var DATA = window.HFDATA; if (!DATA) { document.documentElement.classList.add("hf-nodata"); return; }
const PW = DATA.PW;
const AIS = DATA.AIS;   // {sampled, v: [[lon,lat,dir,sog,kind,name,dest,len,ageMin,trail[]]...]}
const KINDS = [["tanker", "Tanker"], ["cargo", "Cargo"], ["passenger", "Passenger"], ["fishing", "Fishing"], ["tug", "Tug"], ["other", "Other"], ["unknown", "Type not sent yet"]];
const KCOL = ["#ffb048", "#5ce1ff", "#b9a1ff", "#ff8ad1", "#e9ecee", "#aeb6bb", "#6f777c"];
const N = PW.n, day0 = new Date(PW.dates[0] + "T00:00:00Z"), dateAt = i => new Date(day0.getTime() + i * 864e5);
const fmtD = d => d.toLocaleDateString("en-GB", {day: "numeric", month: "short", year: "numeric", timeZone: "UTC"});
const fmtDs = d => d.toLocaleDateString("en-GB", {day: "numeric", month: "short", timeZone: "UTC"});
const avg = a => { const v = a.filter(x => x != null); return v.length ? v.reduce((s, x) => s + x, 0) / v.length : null; };
const lastIdx = (() => { let i = N - 1; while (i > 0 && PW.cp.every(c => c.t[i] == null)) i--; return i; })();
const sign = v => { const r = Math.round(v); return r === 0 ? "0%" : (r > 0 ? "+" : "−") + Math.abs(r) + "%"; };
const mv = v => Math.round(v) > 0 ? "mv--up" : Math.round(v) < 0 ? "mv--down" : "";
const n0 = v => v == null ? "[n/a]" : Math.round(v).toLocaleString("en-US");
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const dm = (v, p, n) => { const a = Math.abs(v), d = Math.floor(a), m = (a - d) * 60; return `${d}°${m.toFixed(2).padStart(5, "0")}′${v >= 0 ? p : n}`; };
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const phone = () => innerWidth <= 760;
const short = n => n.replace(" Strait", "").replace("Strait of ", "");

const ON_WATER = {"Malacca Strait": [101.2, 2.55]};
for (const c of PW.cp) {
  if (ON_WATER[c.name]) [c.lon, c.lat] = ON_WATER[c.name];
  c.last = c.t[lastIdx]; c.w = avg(c.t.slice(lastIdx - 6, lastIdx + 1)); c.y = avg(c.t.slice(Math.max(0, lastIdx - 364), lastIdx + 1));
  c.chg = c.y ? (c.w / c.y - 1) * 100 : null;
  const tw = avg(c.tk.slice(lastIdx - 6, lastIdx + 1)), ty = avg(c.tk.slice(Math.max(0, lastIdx - 364), lastIdx + 1));
  c.tchg = ty ? (tw / ty - 1) * 100 : null;
  c.mix = ["tk", "ct", "db", "gc"].map(k => avg(c[k].slice(lastIdx - 6, lastIdx + 1)) || 0);
}

// ---- vessels as GeoJSON ----
const V = AIS.v;
const feats = V.map((v, i) => ({type: "Feature", id: i, geometry: {type: "Point", coordinates: [v[0], v[1]]},
  properties: {i, k: v[4], dir: v[2] ?? 0, moving: (v[3] ?? 0) >= 0.5 ? 1 : 0, big: (v[7] ?? 0) >= 150 ? 1 : 0}}));
const counts = KINDS.map((_, k) => V.filter(v => v[4] === k).length);
const on = KINDS.map(() => true);

// ---- top bar ----
const sampled = new Date(AIS.sampled);
document.getElementById("s-age").textContent = sampled.toISOString().slice(11, 16) + " UTC";
document.getElementById("s-n").textContent = V.length.toLocaleString("en-US");
document.getElementById("s-tk").textContent = counts[0].toLocaleString("en-US");
document.getElementById("s-uw").textContent = V.filter(v => (v[3] ?? 0) >= 0.5).length.toLocaleString("en-US");
const fall = PW.cp.filter(c => c.y >= 5).sort((a, b) => a.chg - b.chg)[0];
document.getElementById("s-fall").innerHTML = `${short(fall.name)} <span class="${mv(fall.chg)}">${sign(fall.chg)}</span>`;
document.getElementById("foot").textContent = `Positions: aisstream.io, sampled ${fmtD(sampled)} ${sampled.toISOString().slice(11, 16)} UTC, each vessel where it was last heard. Transits: IMF PortWatch, to ${fmtD(dateAt(lastIdx))}.`;

// ---- map ----
function icon(size, moving) {
  const c = document.createElement("canvas"); c.width = c.height = size; const g = c.getContext("2d"); g.fillStyle = "#fff"; g.beginPath();
  if (moving) { g.moveTo(size / 2, 1); g.lineTo(size * .8, size * .5); g.lineTo(size * .72, size - 2); g.lineTo(size * .28, size - 2); g.lineTo(size * .2, size * .5); }
  else { g.arc(size / 2, size / 2, size * .26, 0, 7); }
  g.closePath(); g.fill(); return g.getImageData(0, 0, size, size);
}
// The basemap is named by the build (<meta name="hf-tiles">): Esri imagery with an ArcGIS key, NASA Blue Marble without one.
const TL = JSON.parse(document.querySelector('meta[name="hf-tiles"]').content);
const STYLE = {version: 8, sources: {
    sat: {type: "raster", tiles: [TL.sat], tileSize: 256, maxzoom: TL.z, attribution: TL.att},
    ref: {type: "raster", tiles: [TL.ref || TL.sat], tileSize: 256, maxzoom: TL.z}},
  layers: [{id: "bg", type: "background", paint: {"background-color": "#000"}},
    {id: "sat", type: "raster", source: "sat", paint: {"raster-brightness-max": .78, "raster-saturation": -.15}},
    {id: "ref", type: "raster", source: "ref", paint: {"raster-opacity": .6}}, {id: "dark", type: "raster", source: "sat", layout: {visibility: "none"}, paint: {"raster-saturation": -1, "raster-brightness-max": .3, "raster-contrast": .25}}]};
const HOME = () => phone() ? {center: [10, 45], zoom: 2.6} : {center: [8, 47], zoom: 3.6};
if (!TL.ref) { delete STYLE.sources.ref; const rl = STYLE.layers.find(l => l.id === "ref"); rl.source = "sat"; rl.paint = {"raster-opacity": 0}; }  // no places layer without a key: the layer stays, empty, so the switches still find it
const map = new maplibregl.Map({container: "map", style: STYLE, ...HOME(), minZoom: 1.2, maxZoom: 17, attributionControl: false, dragRotate: false, pitchWithRotate: false});
map.touchZoomRotate.disableRotation();
map.addControl(new maplibregl.NavigationControl({showCompass: false}), "bottom-right");
map.addControl(new maplibregl.ScaleControl({unit: "nautical"}), "bottom-right");
map.addControl(new maplibregl.AttributionControl({compact: true}), "bottom-right");
const colorExpr = ["match", ["get", "k"], ...KCOL.flatMap((c, i) => [i, c]), "#888"];
const pop = new maplibregl.Popup({closeButton: false, closeOnClick: false, offset: 12, className: "pop"});
let selV = null, selC = null;

map.on("load", () => {
  map.addImage("ship", icon(28, true), {sdf: true}); map.addImage("still", icon(28, false), {sdf: true});
  map.addSource("ships", {type: "geojson", data: {type: "FeatureCollection", features: feats}});
  map.addSource("trail", {type: "geojson", data: {type: "FeatureCollection", features: []}});
  map.addSource("sel", {type: "geojson", data: {type: "FeatureCollection", features: []}});
  map.addLayer({id: "trail", type: "line", source: "trail", paint: {"line-color": "#fff", "line-width": 2, "line-dasharray": [1, 1.5], "line-opacity": .9}});
  map.addLayer({id: "sel", type: "circle", source: "sel", paint: {"circle-radius": 16, "circle-color": "rgba(255,255,255,.08)", "circle-stroke-color": "#fff", "circle-stroke-width": 2}});
  map.addLayer({id: "ships", type: "symbol", source: "ships", layout: {
      "icon-image": ["case", ["==", ["get", "moving"], 1], "ship", "still"], "icon-rotate": ["get", "dir"], "icon-rotation-alignment": "map",
      "icon-allow-overlap": true, "icon-ignore-placement": true, "symbol-sort-key": ["-", 10, ["get", "k"]],
      "icon-size": ["interpolate", ["linear"], ["zoom"], 1, ["case", ["==", ["get", "big"], 1], .34, .26], 5, ["case", ["==", ["get", "big"], 1], .6, .46], 9, ["case", ["==", ["get", "big"], 1], 1.0, .78], 13, 1.3]},
    paint: {"icon-color": colorExpr, "icon-halo-color": "rgba(0,0,0,.9)", "icon-halo-width": 1.3}});
  map.on("mouseenter", "ships", () => map.getCanvas().style.cursor = "pointer");
  map.on("mouseleave", "ships", () => { map.getCanvas().style.cursor = ""; pop.remove(); });
  map.on("mousemove", "ships", e => { const v = V[e.features[0].properties.i]; pop.setLngLat([v[0], v[1]]).setHTML(`<b>${esc(v[5] || "Name not sent yet")}</b>${KINDS[v[4]][1]}${v[3] != null ? ", " + v[3].toFixed(1) + " kn" : ""}`).addTo(map); });
  map.on("click", "ships", e => { e.originalEvent.stopPropagation(); selectVessel(e.features[0].properties.i, false); });
  addChokepoints(); inView(); kinds();
});
map.on("moveend", inView);
const ro = document.getElementById("ro");
const readout = ll => ro.textContent = `${ll ? dm(ll.lat, "N", "S") + "  " + dm(ll.lng, "E", "W") + "    " : ""}zoom ${map.getZoom().toFixed(1)}`;
map.on("mousemove", e => readout(e.lngLat)); map.on("zoom", () => readout(null)); readout(null);

document.querySelectorAll("[data-base]").forEach(b => b.onclick = () => {
  const sat = b.dataset.base === "sat"; ["sat", "ref"].forEach(l => map.setLayoutProperty(l, "visibility", sat ? "visible" : "none"));
  map.setLayoutProperty("dark", "visibility", sat ? "none" : "visible");
  document.querySelectorAll("[data-base]").forEach(x => x.setAttribute("aria-pressed", x === b));
});

// ---- vessel type filters ----
function kinds() {
  const el = document.getElementById("kinds");
  el.innerHTML = KINDS.map((k, i) => `<button aria-pressed="${on[i]}" data-k="${i}"><i style="background:${KCOL[i]}"></i>${k[1]} <b>${counts[i].toLocaleString("en-US")}</b></button>`).join("");
  el.querySelectorAll("button").forEach(b => b.onclick = () => { const i = +b.dataset.k; on[i] = !on[i]; b.setAttribute("aria-pressed", on[i]);
    map.setFilter("ships", ["in", ["get", "k"], ["literal", on.map((v, j) => v ? j : -1).filter(j => j >= 0)]]); inView(); });
}

// ---- chokepoints ----
const marks = new Map(), BUSY = new Set([...PW.cp].sort((a, b) => b.y - a.y).slice(0, 9).map(c => c.name).concat(["Strait of Hormuz", "Suez Canal", "Panama Canal", "Bab el-Mandeb Strait"]));
function addChokepoints() {
  for (const c of PW.cp) {
    const el = document.createElement("div"); el.className = "cpm";
    el.innerHTML = `<b role="button" tabindex="0" aria-label="${c.name}"></b><span>${short(c.name)}<em class="${mv(c.chg)}">${sign(c.chg)}</em></span>`;
    el.onclick = e => { e.stopPropagation(); selectCp(c, true); };
    new maplibregl.Marker({element: el}).setLngLat([c.lon, c.lat]).addTo(map); marks.set(c.name, el);
  }
  const lab = () => { const z = map.getZoom(); for (const [n, el] of marks) el.classList.toggle("show", z > 4.2 || (z > 2 && BUSY.has(n))); };
  map.on("zoomend", lab); lab();
}
function spark(cv, c) {
  const w = 60, h = 22, d = 2; cv.width = w * d; cv.height = h * d; const g = cv.getContext("2d"); g.scale(d, d);
  const v = c.t.slice(lastIdx - 89, lastIdx + 1), mx = Math.max(...v.filter(x => x != null), 1);
  g.strokeStyle = "#f2f3f3"; g.lineWidth = 1.1; g.beginPath(); v.forEach((y, i) => { const X = 1 + i / 89 * (w - 3), Y = 2 + (1 - (y ?? 0) / mx) * (h - 4); i ? g.lineTo(X, Y) : g.moveTo(X, Y); }); g.stroke();
}
let sortK = "chg";
function listCp() {
  const rows = [...PW.cp].sort((a, b) => a.chg - b.chg), el = document.getElementById("list-cp");
  el.innerHTML = `<div class="lh"><span>Chokepoint</span><span>Day</span><span>7d vs 1y</span><span>90 days</span></div>` + rows.map(c =>
    `<button class="row${c === selC ? " is-on" : ""}" data-n="${c.name}"><span class="n">${short(c.name)}</span><span class="r dim">${n0(c.last)}</span><span class="r ${mv(c.chg)}">${sign(c.chg)}</span><canvas></canvas></button>`).join("");
  el.querySelectorAll(".row").forEach(r => { const c = PW.cp.find(x => x.name === r.dataset.n); r.onclick = () => selectCp(c, true); spark(r.querySelector("canvas"), c); });
}

// ---- vessels in view ----
function inView() {
  if (!map.getLayer("ships")) return;
  const seen = new Set(), rows = [];
  for (const f of map.queryRenderedFeatures({layers: ["ships"]})) { const i = f.properties.i; if (!seen.has(i)) { seen.add(i); rows.push(i); } }
  rows.sort((a, b) => (V[b][7] ?? 0) - (V[a][7] ?? 0) || (V[b][5] ? 1 : 0) - (V[a][5] ? 1 : 0));
  const el = document.getElementById("list-vs");
  el.innerHTML = `<div class="lh"><span></span><span>${rows.length.toLocaleString("en-US")} in view, largest first</span><span>Speed</span></div>` + rows.slice(0, 80).map(i => { const v = V[i];
    return `<button class="row${i === selV ? " is-on" : ""}" data-i="${i}"><i class="dot" style="background:${KCOL[v[4]]}"></i><span class="n">${esc(v[5] || "Name not sent yet")}<span class="s">${KINDS[v[4]][1]}${v[7] ? ", " + v[7] + " m" : ""}${v[6] ? " → " + esc(v[6]) : ""}</span></span><span class="r dim">${v[3] != null ? v[3].toFixed(1) + " kn" : ""}</span></button>`; }).join("");
  el.querySelectorAll(".row").forEach(r => r.onclick = () => selectVessel(+r.dataset.i, true));
}
document.querySelectorAll("[data-tab]").forEach(b => b.onclick = () => {
  document.querySelectorAll("[data-tab]").forEach(x => x.setAttribute("aria-selected", x === b));
  document.getElementById("list-cp").hidden = b.dataset.tab !== "cp"; document.getElementById("list-vs").hidden = b.dataset.tab !== "vs";
});

// ---- cards ----
const card = document.getElementById("card");
function closeCard() { card.classList.remove("show"); selV = null; selC = null; marksSel(); map.getSource("sel")?.setData({type: "FeatureCollection", features: []}); map.getSource("trail")?.setData({type: "FeatureCollection", features: []}); listCp(); inView(); }
function marksSel() { for (const [n, el] of marks) el.classList.toggle("is-on", !!selC && n === selC.name); }
function show(html) { card.innerHTML = `<button class="x" aria-label="Close">×</button>` + html; card.classList.remove("show"); void card.offsetWidth; card.classList.add("show"); card.querySelector(".x").onclick = closeCard; }

function selectVessel(i, fly) {
  selV = i; selC = null; marksSel(); const v = V[i];
  map.getSource("sel").setData({type: "Feature", geometry: {type: "Point", coordinates: [v[0], v[1]]}});
  const tr = []; for (let j = 0; j < v[9].length; j += 2) tr.push([v[9][j], v[9][j + 1]]); tr.push([v[0], v[1]]);
  map.getSource("trail").setData(tr.length > 1 ? {type: "Feature", geometry: {type: "LineString", coordinates: tr}} : {type: "FeatureCollection", features: []});
  const age = v[8] < 1 ? "under a minute ago" : v[8] < 60 ? `${Math.round(v[8])} min before the sample` : `${(v[8] / 60).toFixed(1)} h before the sample`;
  show(`<div class="hd"><p class="tag"><i style="background:${KCOL[v[4]]}"></i>${KINDS[v[4]][1]}</p><h2>${esc(v[5] || "Name not sent yet")}</h2><p class="sub">${dm(v[1], "N", "S")}  ${dm(v[0], "E", "W")}</p></div>
    <div class="g2" style="border-top:0"><div><span>Speed</span><b>${v[3] != null ? v[3].toFixed(1) + " <small>kn</small>" : "[n/a]"}</b></div><div><span>Course</span><b>${v[2] != null ? Math.round(v[2]) + "°" : "[n/a]"}</b></div>
    <div><span>Destination, as sent</span><b style="font-size:15px">${esc(v[6] || "[not sent]")}</b></div><div><span>Length</span><b>${v[7] ? v[7] + " <small>m</small>" : "[n/a]"}</b></div>
    <div><span>Last heard</span><b style="font-size:14px">${age}</b></div><div><span>Track held</span><b>${tr.length} <small>position${tr.length === 1 ? "" : "s"}</small></b></div></div>
    <p class="src">AIS from aisstream.io. A vessel is drawn where it was last heard and is never moved between samples; its dashed track joins the positions held, up to six over six hours. Name and destination are what the crew typed into the transponder.</p>`);
  if (fly) map.flyTo({center: [v[0], v[1]], zoom: Math.max(map.getZoom(), 9), duration: reduce ? 0 : 1600, essential: true});
  inView(); listCp();
}

let range = 90;
function selectCp(c, fly) {
  selC = c; selV = null; marksSel(); map.getSource("sel")?.setData({type: "FeatureCollection", features: []}); map.getSource("trail")?.setData({type: "FeatureCollection", features: []});
  const tt = c.mix.reduce((s, x) => s + x, 0) || 1, names = ["Tankers", "Container", "Dry bulk", "Other cargo"], cols = ["#ffb048", "#5ce1ff", "#f2f3f3", "#aeb6bb"];
  show(`<div class="hd"><p class="tag">Chokepoint</p><h2>${c.name}</h2><p class="sub">${dm(c.lat, "N", "S")}  ${dm(c.lon, "E", "W")}</p></div>
    <div class="big"><b class="${mv(c.chg)}">${sign(c.chg)}</b><span>vessels a day, last 7 days<br>against the 1-year pace</span></div>
    ${c.live === 0 ? `<p class="src" style="margin-top:0">No live positions here: the receivers behind this map are on land and do not reach this water. The transit counts are complete: ${n0(c.last)} ${c.last === 1 ? "vessel" : "vessels"} crossed on the last day.</p>` : ""}
    <div class="g2"><div><span>Last day, ${fmtDs(dateAt(lastIdx))}</span><b>${n0(c.last)}</b></div><div><span>7-day average</span><b>${c.w.toFixed(1)}</b></div>
    <div><span>1-year average</span><b>${c.y.toFixed(1)}</b></div><div><span>Tankers vs 1 year</span><b class="${mv(c.tchg)}">${c.tchg == null ? "[n/a]" : sign(c.tchg)}</b></div></div>
    <div class="sec"><span>Vessels a day, <span style="color:#ffb048">tankers</span>, 1-year average dashed</span><span class="seg">${[[30, "1M"], [90, "3M"], [387, "1Y"]].map(([r, l]) => `<button data-r="${r}" aria-pressed="${r === range}">${l}</button>`).join("")}</span></div>
    <div class="chart"><canvas id="ch"></canvas><div class="tip" id="tip"></div></div>
    <div class="sec"><span>By type, last 7 days</span></div>
    <div class="mix">${c.mix.map((v, i) => `<div class="r"><span>${names[i]}</span><span class="bar"><i style="width:${v / tt * 100}%;background:${cols[i]}"></i></span><b>${Math.round(v / tt * 100)}%</b></div>`).join("")}</div>
    <p class="src">IMF PortWatch (University of Oxford; AIS from Spire). Each vessel is counted once as it crosses, by type; published about five days later.</p>`);
  card.querySelectorAll("[data-r]").forEach(b => b.onclick = () => { range = +b.dataset.r; card.querySelectorAll("[data-r]").forEach(x => x.setAttribute("aria-pressed", x === b)); chart(c); });
  chart(c);
  if (fly) map.flyTo({center: [c.lon, c.lat], zoom: 7, duration: reduce ? 0 : 2200, curve: 1.5, essential: true, padding: phone() ? {bottom: innerHeight * .5} : {left: 340, right: 350}});
  listCp();
}
function chart(c, hov) {
  const cv = document.getElementById("ch"); if (!cv) return; const tip = document.getElementById("tip");
  const w = cv.clientWidth, h = cv.clientHeight, d = 2; cv.width = w * d; cv.height = h * d; const g = cv.getContext("2d"); g.scale(d, d);
  const i0 = Math.max(0, lastIdx - range + 1), v = c.t.slice(i0, lastIdx + 1), k = c.tk.slice(i0, lastIdx + 1);
  const L = {l: 34, r: 8, t: 20, b: 18}, mx = Math.max(...v.filter(x => x != null), c.y) * 1.1 || 1;
  const X = i => L.l + i / Math.max(1, v.length - 1) * (w - L.l - L.r), Y = y => L.t + (1 - y / mx) * (h - L.t - L.b);
  g.font = "400 11px Inter, Arial, sans-serif"; g.fillStyle = "#868c90"; g.strokeStyle = "rgba(242,243,243,.1)";
  for (const f of [0, 1]) { const y = Math.round(mx * f / 1.1); g.beginPath(); g.moveTo(L.l, Y(y) + .5); g.lineTo(w - L.r, Y(y) + .5); g.stroke(); g.fillText(y, 8, Y(y) + 4); }
  g.fillText(fmtDs(dateAt(i0)), L.l, h - 3); const e = fmtDs(dateAt(lastIdx)); g.fillText(e, w - L.r - g.measureText(e).width, h - 3);
  g.setLineDash([3, 4]); g.strokeStyle = "#868c90"; g.beginPath(); g.moveTo(L.l, Y(c.y)); g.lineTo(w - L.r, Y(c.y)); g.stroke(); g.setLineDash([]);
  const line = (a, col, lw, fill) => { g.beginPath(); a.forEach((y, i) => i ? g.lineTo(X(i), Y(y ?? 0)) : g.moveTo(X(i), Y(y ?? 0))); g.strokeStyle = col; g.lineWidth = lw; g.stroke();
    if (fill) { g.lineTo(X(a.length - 1), Y(0)); g.lineTo(X(0), Y(0)); g.closePath(); g.fillStyle = fill; g.fill(); } };
  line(v, "#f2f3f3", 1.5, "rgba(242,243,243,.07)"); line(k, "#ffb048", 1.2);
  if (hov != null) { g.strokeStyle = "rgba(242,243,243,.4)"; g.beginPath(); g.moveTo(X(hov) + .5, L.t); g.lineTo(X(hov) + .5, h - L.b); g.stroke();
    tip.textContent = `${fmtDs(dateAt(i0 + hov))}: ${n0(v[hov])} vessels, ${n0(k[hov])} tankers`; tip.style.left = Math.min(Math.max(X(hov) - 60, 4), w - 190) + "px"; tip.style.opacity = 1; } else tip.style.opacity = 0;
  cv.onpointermove = ev => { const r = cv.getBoundingClientRect(); chart(c, Math.max(0, Math.min(v.length - 1, Math.round((ev.clientX - r.left - L.l) / (w - L.l - L.r) * (v.length - 1))))); };
  cv.onpointerleave = () => chart(c);
}

// ---- search ----
document.getElementById("q").addEventListener("keydown", e => {
  if (e.key !== "Enter") return; const q = e.target.value.trim().toUpperCase(); if (!q) return;
  const i = V.findIndex(v => v[5] && v[5].toUpperCase() === q); const j = i >= 0 ? i : V.findIndex(v => v[5] && v[5].toUpperCase().includes(q));
  if (j >= 0) selectVessel(j, true); else { e.target.value = ""; e.target.placeholder = "No vessel with that name in this sample"; }
});
map.on("click", e => { if (!map.queryRenderedFeatures(e.point, {layers: ["ships"]}).length && (selV != null)) closeCard(); });
listCp();
window.__api = {selectCp, selectVessel, V, PW, map};
})();
