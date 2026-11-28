/* Hedge Fund Data: From orbit. The page's figures are in data.js beside the page (window.HFDATA), which
   tools/page_hedgefund.py writes from .cache/hf/. Nothing here is fetched from anywhere else. */
(function () {
"use strict";
var DATA = window.HFDATA; if (!DATA) { document.documentElement.classList.add("hf-nodata"); return; }
const D = DATA;
const T = D.t, NL = D.n;
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const n0 = v => Math.round(v).toLocaleString("en-US");
const sign = v => { const r = Math.round(v * 10) / 10; return r === 0 ? "0.0%" : (r > 0 ? "+" : "\u2212") + Math.abs(r).toFixed(1) + "%"; };
const mv = v => Math.round(v * 10) > 0 ? "mv--up" : Math.round(v * 10) < 0 ? "mv--down" : "";
const dm = (v, p, n) => { const a = Math.abs(v), d = Math.floor(a), m = (a - d) * 60; return `${d}\u00b0${m.toFixed(2).padStart(5, "0")}\u2032${v >= 0 ? p : n}`; };
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches, phone = () => innerWidth <= 760;
const fetched = new Date(T.fetched), hhmm = fetched.toISOString().slice(11, 16);
const MONTHS = Object.keys(NL.data).sort(); const mName = m => new Date(m + "-15T00:00:00Z").toLocaleDateString("en-GB", {month: "short", year: "numeric", timeZone: "UTC"});
for (const r of NL.regions) { const s = MONTHS.map(m => (NL.data[m][r.key] || {}).sum ?? null); r.series = s; const have = s.map((v, i) => [v, i]).filter(x => x[0] != null);
  r.last = have.length ? have[have.length - 1][0] : null; r.lastM = have.length ? MONTHS[have[have.length - 1][1]] : null; r.prev = have.length > 1 ? have[have.length - 2][0] : null; r.chg = r.prev ? (r.last / r.prev - 1) * 100 : null;
  r.lit = have.length ? NL.data[r.lastM][r.key].lit : null; }
for (const r of T.regions) { r.count = T.latest[r.key].count; r.frp = T.latest[r.key].frp; }
let mode = "heat", sel = null;

const gibs = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_Black_Marble/default/2016-01-01/GoogleMapsCompatible_Level8/{z}/{y}/{x}.png";
// The basemap is named by the build (<meta name="hf-tiles">): Esri imagery with an ArcGIS key, NASA Blue Marble without one.
const TL = JSON.parse(document.querySelector('meta[name="hf-tiles"]').content);
const STYLE = {version: 8, sources: {
    night: {type: "raster", tiles: [gibs], tileSize: 256, maxzoom: 8, attribution: "NASA Black Marble (GIBS)"},
    sat: {type: "raster", tiles: [TL.sat], tileSize: 256, maxzoom: TL.z, attribution: TL.att},
    ref: {type: "raster", tiles: [TL.ref || TL.sat], tileSize: 256, maxzoom: TL.z}},
  layers: [{id: "bg", type: "background", paint: {"background-color": "#000"}},
    {id: "night", type: "raster", source: "night", paint: {"raster-brightness-max": 1, "raster-contrast": .15}},
    {id: "sat", type: "raster", source: "sat", layout: {visibility: "none"}, paint: {"raster-brightness-max": .6, "raster-saturation": -.3}}, {id: "dark", type: "raster", source: "sat", layout: {visibility: "none"}, paint: {"raster-saturation": -1, "raster-brightness-max": .3, "raster-contrast": .25}},
    {id: "ref", type: "raster", source: "ref", paint: {"raster-opacity": .5}}]};
if (!TL.ref) { delete STYLE.sources.ref; const rl = STYLE.layers.find(l => l.id === "ref"); rl.source = "sat"; rl.paint = {"raster-opacity": 0}; }  // no places layer without a key: the layer stays, empty, so the switches still find it
const map = new maplibregl.Map({container: "map", style: STYLE, center: phone() ? [20, 10] : [15, 12], zoom: phone() ? 1.3 : 2.2, minZoom: 1.2, maxZoom: 12, attributionControl: false, dragRotate: false, pitchWithRotate: false});
map.touchZoomRotate.disableRotation();
map.addControl(new maplibregl.NavigationControl({showCompass: false}), "bottom-right"); map.addControl(new maplibregl.ScaleControl({unit: "metric"}), "bottom-right"); map.addControl(new maplibregl.AttributionControl({compact: true}), "bottom-right");
const pop = new maplibregl.Popup({closeButton: false, closeOnClick: false, offset: 10, className: "pop"});
const box = b => [[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]], [b[0], b[1]]];
const marks = [];
map.on("load", () => {
  map.addSource("heat", {type: "geojson", data: {type: "FeatureCollection", features: T.points.map((p, i) => ({type: "Feature", geometry: {type: "Point", coordinates: [p[0], p[1]]}, properties: {i, frp: p[2]}}))}});
  map.addSource("boxes", {type: "geojson", data: {type: "FeatureCollection", features: []}});
  map.addLayer({id: "glow", type: "heatmap", source: "heat", maxzoom: 7, paint: {"heatmap-weight": ["interpolate", ["linear"], ["get", "frp"], 20, .25, 300, 1], "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 1, .7, 6, 1.6],
      "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 1, 5, 6, 22], "heatmap-opacity": ["interpolate", ["linear"], ["zoom"], 4, .85, 7, 0],
      "heatmap-color": ["interpolate", ["linear"], ["heatmap-density"], 0, "rgba(255,120,20,0)", .2, "rgba(255,120,20,.55)", .5, "rgba(255,176,72,.85)", .8, "rgba(255,226,150,.95)", 1, "#fff8e0"]}});
  map.addLayer({id: "pts", type: "circle", source: "heat", minzoom: 3.5, paint: {"circle-radius": ["interpolate", ["linear"], ["get", "frp"], 20, 2.5, 100, 4.5, 500, 9],
      "circle-color": ["interpolate", ["linear"], ["get", "frp"], 20, "#ff8a2a", 100, "#ffc45c", 400, "#fff3c4"], "circle-opacity": ["interpolate", ["linear"], ["zoom"], 3.5, 0, 5, .95], "circle-stroke-color": "rgba(0,0,0,.6)", "circle-stroke-width": .6}});
  map.addLayer({id: "boxes", type: "line", source: "boxes", paint: {"line-color": ["case", ["==", ["get", "on"], 1], "#ffb048", "rgba(242,243,243,.55)"], "line-width": ["case", ["==", ["get", "on"], 1], 2, 1], "line-dasharray": [3, 2]}});
  map.on("mousemove", "pts", e => { const p = T.points[e.features[0].properties.i]; map.getCanvas().style.cursor = "crosshair"; pop.setLngLat([p[0], p[1]]).setHTML(`<b>${p[2].toFixed(0)} MW</b>Seen ${String(p[3]).padStart(4, "0").replace(/(..)(..)/, "$1:$2")} UTC, ${p[4] === "N" ? "at night" : "by day"}`).addTo(map); });
  map.on("mouseleave", "pts", () => { map.getCanvas().style.cursor = ""; pop.remove(); });
  render();
});
const ro = document.getElementById("ro"); const readout = ll => ro.textContent = `${ll ? dm(ll.lat, "N", "S") + "  " + dm(ll.lng, "E", "W") + "    " : ""}zoom ${map.getZoom().toFixed(1)}`;
map.on("mousemove", e => readout(e.lngLat)); map.on("zoom", () => readout(null)); readout(null);
document.querySelectorAll("[data-base]").forEach(b => b.onclick = () => { for (const l of ["night", "sat", "dark"]) map.setLayoutProperty(l, "visibility", l === b.dataset.base ? "visible" : "none"); document.querySelectorAll("[data-base]").forEach(x => x.setAttribute("aria-pressed", x === b)); });
document.querySelectorAll("[data-mode]").forEach(b => b.onclick = () => { mode = b.dataset.mode; sel = null; card.classList.remove("show"); document.querySelectorAll("[data-mode]").forEach(x => x.setAttribute("aria-pressed", x === b)); render(); });

function render() {
  const heat = mode === "heat", regs = heat ? T.regions : NL.regions;
  for (const l of ["glow", "pts"]) if (map.getLayer(l)) map.setLayoutProperty(l, "visibility", heat ? "visible" : "none");
  map.getSource("boxes")?.setData({type: "FeatureCollection", features: regs.map(r => ({type: "Feature", geometry: {type: "LineString", coordinates: box(r.bbox)}, properties: {on: sel === r ? 1 : 0}}))});
  marks.splice(0).forEach(m => m.remove());
  for (const r of regs) { const el = document.createElement("div"); el.className = "rg" + (sel === r ? " is-on" : "");
    el.innerHTML = `<span>${esc(r.name)}<em${heat ? "" : ` class="${r.chg == null ? "" : mv(r.chg)}" style="${r.chg == null ? "color:var(--ink-3)" : ""}"`}>${heat ? n0(r.count) : r.chg == null ? "1 month" : sign(r.chg)}</em></span>`;
    el.onclick = e => { e.stopPropagation(); select(r, true); }; marks.push(new maplibregl.Marker({element: el}).setLngLat([(r.bbox[0] + r.bbox[2]) / 2, r.bbox[3]]).addTo(map)); }
  const S = (i, l, v) => { document.getElementById("s" + i + "l").textContent = l; document.getElementById("s" + i).innerHTML = v; };
  if (heat) { const top = [...T.regions].sort((a, b) => b.frp - a.frp)[0];
    S(1, "Detections, 24 h", n0(T.total)); S(2, "Hottest region watched", `${top.name}, ${n0(top.frp)} MW`); S(3, "Fetched", hhmm + " UTC");
    document.getElementById("note").textContent = "Heat seen from orbit in the last 24 hours: fires, gas flares at oil fields, burning industry. Sixteen regions that matter to markets are counted.";
    document.getElementById("foot").textContent = `NASA FIRMS, VIIRS 375 m, near real time (NOAA-20, NOAA-21, Suomi NPP). The map draws the ${n0(T.points.length)} most intense detections; every detection is counted. The daily history began on ${T.fetched.slice(0, 10)}.`;
  } else { const have = NL.regions.filter(r => r.last != null);
    S(1, "Places measured", `${have.length} of ${NL.regions.length}`); S(2, "Latest month", have.length ? mName(MONTHS[MONTHS.length - 1]) : "[pending]"); S(3, "Months held", MONTHS.length + " of 37");
    document.getElementById("note").textContent = "The month's night-time light over thirteen places: factory belts, capitals at war or under sanctions, an oil field lit by its flares. Light is activity you cannot fake.";
    document.getElementById("foot").textContent = "NASA Black Marble VNP46A3, monthly, snow-free composite: the sum of radiance over each box. The page will compare each month with the same month a year earlier once the three-year history is in; for now, the month before. The picture underneath is NASA's 2016 composite."; }
  const el = document.getElementById("list"), rows = heat ? [...regs].sort((a, b) => b.frp - a.frp) : [...regs].sort((a, b) => (b.last ?? -1) - (a.last ?? -1));
  el.innerHTML = (heat ? `<div class="lh"><span>Region</span><span>Detections</span><span>Power, MW</span></div>` : `<div class="lh"><span>Place</span><span>vs month before</span><span>Light</span></div>`) + rows.map(r =>
    `<button class="row${sel === r ? " is-on" : ""}" data-k="${r.key}"><span class="n">${esc(r.name)}<span class="s">${esc(r.why)}</span></span>` + (heat ? `<span class="r">${n0(r.count)}</span><span class="r dim">${n0(r.frp)}</span>`
      : `<span class="r ${r.chg == null ? "dim" : mv(r.chg)}">${r.chg == null ? "[n/a]" : sign(r.chg)}</span><span class="r dim">${r.last == null ? "[pending]" : (r.last / 1000).toFixed(1) + "k"}</span>`) + `</button>`).join("");
  el.querySelectorAll(".row").forEach(b => b.onclick = () => select(regs.find(r => r.key === b.dataset.k), true));
}
const card = document.getElementById("card");
function select(r, fly) { sel = r; const heat = mode === "heat", b = r.bbox, mid = `${dm((b[1] + b[3]) / 2, "N", "S")}  ${dm((b[0] + b[2]) / 2, "E", "W")}`;
  let html;
  if (heat) { const inside = T.points.filter(p => p[0] >= b[0] && p[0] <= b[2] && p[1] >= b[1] && p[1] <= b[3]).sort((x, y) => y[2] - x[2]).slice(0, 6);
    html = `<div class="hd"><p class="tag">Heat, last 24 hours</p><h2>${esc(r.name)}</h2><p class="sub">${mid}</p></div>
    <div class="big"><b>${n0(r.count)}</b><span>detections<br>${esc(r.why.toLowerCase())}</span></div>
    <div class="g2"><div><span>Radiative power</span><b>${n0(r.frp)} <small>MW</small></b></div><div><span>Share of the world's detections</span><b>${(r.count / T.total * 100).toFixed(1)}%</b></div></div>
    <div class="sec"><span>Most intense, where and how hot</span></div><div class="hot">${inside.map(p => `<div><span>${dm(p[1], "N", "S")} ${dm(p[0], "E", "W")}</span><b>${p[2].toFixed(0)} MW</b></div>`).join("") || '<div><span>None among the most intense on the map</span><b></b></div>'}</div>
    <p class="src">A count rises with fires and with flaring, and falls under cloud, which hides the ground from the satellite. One day says little: the page will set each day against the same region's own average once a few weeks are held.</p>`; }
  else { const mx = Math.max(...r.series.filter(v => v != null), 1);
    html = `<div class="hd"><p class="tag">Night lights</p><h2>${esc(r.name)}</h2><p class="sub">${mid}</p></div>
    <div class="big"><b class="${r.chg == null ? "" : mv(r.chg)}">${r.chg == null ? "[n/a]" : sign(r.chg)}</b><span>light in ${r.lastM ? mName(r.lastM) : "[pending]"}<br>against the month before</span></div>
    <div class="g2"><div><span>Sum of radiance</span><b>${r.last == null ? "[pending]" : n0(r.last)}</b></div><div><span>Lit pixels, about 500 m each</span><b>${r.lit == null ? "[pending]" : n0(r.lit)}</b></div></div>
    <div class="sec"><span>Month by month</span></div><div class="months">${MONTHS.map((m, i) => `<div><b>${r.series[i] == null ? "" : (r.series[i] / 1000).toFixed(1) + "k"}</b><i style="height:${r.series[i] == null ? 0 : Math.max(2, r.series[i] / mx * 70)}px"></i>${mName(m)}</div>`).join("")}</div>
    <p class="src">${esc(r.why)}. Light follows the seasons and the moon-free nights each month has, so the honest comparison is with the same month a year earlier; that needs the history, which is being read a few tiles a run.</p>`; }
  card.innerHTML = `<button class="x" aria-label="Close">\u00d7</button>` + html; card.classList.remove("show"); void card.offsetWidth; card.classList.add("show");
  card.querySelector(".x").onclick = () => { sel = null; card.classList.remove("show"); render(); };
  if (fly) map.fitBounds([[b[0], b[1]], [b[2], b[3]]], {padding: phone() ? {top: 70, bottom: innerHeight * .5, left: 30, right: 30} : {top: 110, bottom: 60, left: 380, right: 390}, maxZoom: mode === "heat" ? 8 : 8, duration: reduce ? 0 : 2000, essential: true});
  render(); }
window.__api = {select, T, NL, setMode: m => document.querySelector(`[data-mode=${m}]`).click()};
})();
