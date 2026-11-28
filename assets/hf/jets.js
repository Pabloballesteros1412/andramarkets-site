/* Hedge Fund Data: Corporate jets. The page's figures are in data.js beside the page (window.HFDATA), which
   tools/page_hedgefund.py writes from .cache/hf/. Nothing here is fetched from anywhere else. */
(function () {
"use strict";
var DATA = window.HFDATA; if (!DATA) { document.documentElement.classList.add("hf-nodata"); return; }
const D = DATA;
// ICAO type code -> [maker index, model, long range]
const MAKERS = ["Gulfstream", "Bombardier", "Dassault", "Embraer", "Cessna Citation", "Other makers"];
const MCOL = ["#ffb048", "#5ce1ff", "#b9a1ff", "#ff8ad1", "#e9ecee", "#aeb6bb"];
const T = {GLF2:[0,"Gulfstream II",0],GLF3:[0,"Gulfstream III",0],GLF4:[0,"Gulfstream G450 / IV",1],GLF5:[0,"Gulfstream G550 / V",1],GLF6:[0,"Gulfstream G650",1],GLF7:[0,"Gulfstream G700",1],GA5C:[0,"Gulfstream G500",1],GA6C:[0,"Gulfstream G600",1],GA7C:[0,"Gulfstream G700",1],GA8C:[0,"Gulfstream G800",1],G150:[0,"Gulfstream G150",0],G280:[0,"Gulfstream G280",0],GALX:[0,"Gulfstream G200",0],ASTR:[0,"Gulfstream G100",0],
GLEX:[1,"Bombardier Global Express",1],GL5T:[1,"Bombardier Global 5000",1],GL7T:[1,"Bombardier Global 7500",1],GL8T:[1,"Bombardier Global 8000",1],CL30:[1,"Bombardier Challenger 300",0],CL35:[1,"Bombardier Challenger 350",0],CL60:[1,"Bombardier Challenger 600 series",0],LJ31:[1,"Learjet 31",0],LJ35:[1,"Learjet 35",0],LJ40:[1,"Learjet 40",0],LJ45:[1,"Learjet 45",0],LJ55:[1,"Learjet 55",0],LJ60:[1,"Learjet 60",0],LJ70:[1,"Learjet 70",0],LJ75:[1,"Learjet 75",0],
F2TH:[2,"Dassault Falcon 2000",0],F900:[2,"Dassault Falcon 900",1],FA10:[2,"Dassault Falcon 10",0],FA20:[2,"Dassault Falcon 20",0],FA50:[2,"Dassault Falcon 50",0],FA6X:[2,"Dassault Falcon 6X",1],FA7X:[2,"Dassault Falcon 7X",1],FA8X:[2,"Dassault Falcon 8X",1],
E35L:[3,"Embraer Legacy 600 / 650",0],E50P:[3,"Embraer Phenom 100",0],E55P:[3,"Embraer Phenom 300",0],E545:[3,"Embraer Praetor 500",0],E550:[3,"Embraer Praetor 600",0],
C25A:[4,"Citation CJ2",0],C25B:[4,"Citation CJ3",0],C25C:[4,"Citation CJ4",0],C25M:[4,"Citation M2",0],C500:[4,"Citation I",0],C501:[4,"Citation I/SP",0],C510:[4,"Citation Mustang",0],C525:[4,"Citation CJ1",0],C526:[4,"Citation Jet",0],C550:[4,"Citation II / Bravo",0],C551:[4,"Citation II/SP",0],C560:[4,"Citation V / Encore",0],C56X:[4,"Citation Excel / XLS",0],C650:[4,"Citation III / VII",0],C680:[4,"Citation Sovereign",0],C68A:[4,"Citation Latitude",0],C700:[4,"Citation Longitude",0],C750:[4,"Citation X",0],
H25A:[5,"Hawker 125",0],H25B:[5,"Hawker 800",0],H25C:[5,"Hawker 1000",0],HA4T:[5,"Hawker 4000",0],BE40:[5,"Beechjet 400",0],PRM1:[5,"Beechcraft Premier I",0],HDJT:[5,"HondaJet",0],PC24:[5,"Pilatus PC-24",0],SF50:[5,"Cirrus Vision Jet",0],EA50:[5,"Eclipse 500",0]};
const J = D.jets.map(j => { const t = T[j[2]] || [5, j[2], 0]; return {lon: j[0], lat: j[1], code: j[2], k: t[0], model: t[1], lr: t[2], alt: j[3], ground: j[4], kn: j[5], trk: j[6]}; });
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const dm = (v, p, n) => { const a = Math.abs(v), d = Math.floor(a), m = (a - d) * 60; return `${d}\u00b0${m.toFixed(2).padStart(5, "0")}\u2032${v >= 0 ? p : n}`; };
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches, phone = () => innerWidth <= 760;
const ft = m => m == null ? null : Math.round(m * 3.28084 / 100) * 100;
const when = new Date(D.time * 1000), hhmm = when.toISOString().slice(11, 16);
const km = (a, b, c, d) => { const p = Math.PI / 180, x = Math.sin((c - a) * p / 2) ** 2 + Math.cos(a * p) * Math.cos(c * p) * Math.sin((d - b) * p / 2) ** 2; return 12742 * Math.asin(Math.sqrt(x)); };
const counts = MAKERS.map((_, k) => J.filter(j => j.k === k).length), on = MAKERS.map(() => true);
document.getElementById("s-age").textContent = hhmm + " UTC";
document.getElementById("s-n").textContent = J.length.toLocaleString("en-US");
document.getElementById("s-air").textContent = J.filter(j => !j.ground).length.toLocaleString("en-US");
document.getElementById("s-lr").textContent = J.filter(j => !j.ground && j.lr).length.toLocaleString("en-US");
document.getElementById("s-all").textContent = D.airborne.toLocaleString("en-US");
const day = Object.keys(D.daily).sort().pop(), dd = D.daily[day];
document.getElementById("foot").textContent = `The OpenSky Network, sampled ${when.toLocaleDateString("en-GB", {day: "numeric", month: "short", year: "numeric", timeZone: "UTC"})} ${hhmm} UTC. Jets are told by their type, from OpenSky's aircraft database. No owner, operator or person is recorded.`;

function plane(size) { const c = document.createElement("canvas"); c.width = c.height = size; const g = c.getContext("2d"), s = size; g.fillStyle = "#fff"; g.beginPath();
  g.moveTo(s * .5, s * .04); g.lineTo(s * .57, s * .36); g.lineTo(s * .96, s * .58); g.lineTo(s * .96, s * .66); g.lineTo(s * .57, s * .58); g.lineTo(s * .55, s * .82); g.lineTo(s * .7, s * .92); g.lineTo(s * .7, s * .97); g.lineTo(s * .5, s * .92);
  g.lineTo(s * .3, s * .97); g.lineTo(s * .3, s * .92); g.lineTo(s * .45, s * .82); g.lineTo(s * .43, s * .58); g.lineTo(s * .04, s * .66); g.lineTo(s * .04, s * .58); g.lineTo(s * .43, s * .36); g.closePath(); g.fill(); return g.getImageData(0, 0, s, s); }
// The basemap is named by the build (<meta name="hf-tiles">): Esri imagery with an ArcGIS key, NASA Blue Marble without one.
const TL = JSON.parse(document.querySelector('meta[name="hf-tiles"]').content);
const STYLE = {version: 8, sources: {
    sat: {type: "raster", tiles: [TL.sat], tileSize: 256, maxzoom: TL.z, attribution: TL.att},
    ref: {type: "raster", tiles: [TL.ref || TL.sat], tileSize: 256, maxzoom: TL.z}},
  layers: [{id: "bg", type: "background", paint: {"background-color": "#000"}}, {id: "sat", type: "raster", source: "sat", paint: {"raster-brightness-max": .7, "raster-saturation": -.25}},
    {id: "ref", type: "raster", source: "ref", paint: {"raster-opacity": .6}}, {id: "dark", type: "raster", source: "sat", layout: {visibility: "none"}, paint: {"raster-saturation": -1, "raster-brightness-max": .3, "raster-contrast": .25}}]};
if (!TL.ref) { delete STYLE.sources.ref; const rl = STYLE.layers.find(l => l.id === "ref"); rl.source = "sat"; rl.paint = {"raster-opacity": 0}; }  // no places layer without a key: the layer stays, empty, so the switches still find it
const map = new maplibregl.Map({container: "map", style: STYLE, center: phone() ? [-90, 38] : [-70, 38], zoom: phone() ? 2.2 : 3.1, minZoom: 1.2, maxZoom: 16, attributionControl: false, dragRotate: false, pitchWithRotate: false});
map.touchZoomRotate.disableRotation();
map.addControl(new maplibregl.NavigationControl({showCompass: false}), "bottom-right"); map.addControl(new maplibregl.ScaleControl({unit: "nautical"}), "bottom-right"); map.addControl(new maplibregl.AttributionControl({compact: true}), "bottom-right");
const pop = new maplibregl.Popup({closeButton: false, closeOnClick: false, offset: 14, className: "pop"});
let selJ = null, selH = null; const marks = new Map();
map.on("load", () => {
  map.addImage("plane", plane(40), {sdf: true});
  map.addSource("jets", {type: "geojson", data: {type: "FeatureCollection", features: J.map((j, i) => ({type: "Feature", geometry: {type: "Point", coordinates: [j.lon, j.lat]}, properties: {i, k: j.k, trk: j.trk ?? 0, lr: j.lr, g: j.ground ? 1 : 0}}))}});
  map.addSource("sel", {type: "geojson", data: {type: "FeatureCollection", features: []}});
  map.addLayer({id: "sel", type: "circle", source: "sel", paint: {"circle-radius": 20, "circle-color": "rgba(255,255,255,.08)", "circle-stroke-color": "#fff", "circle-stroke-width": 2}});
  map.addLayer({id: "jets", type: "symbol", source: "jets", layout: {"icon-image": "plane", "icon-rotate": ["get", "trk"], "icon-rotation-alignment": "map", "icon-allow-overlap": true, "icon-ignore-placement": true, "symbol-sort-key": ["get", "lr"],
      "icon-size": ["interpolate", ["linear"], ["zoom"], 1, ["case", ["==", ["get", "lr"], 1], .42, .32], 5, ["case", ["==", ["get", "lr"], 1], .68, .52], 9, ["case", ["==", ["get", "lr"], 1], .95, .75]]},
    paint: {"icon-color": ["match", ["get", "k"], ...MCOL.flatMap((c, i) => [i, c]), "#888"], "icon-opacity": ["case", ["==", ["get", "g"], 1], .55, 1], "icon-halo-color": "rgba(0,0,0,.9)", "icon-halo-width": 1.4}});
  map.on("mouseenter", "jets", () => map.getCanvas().style.cursor = "pointer"); map.on("mouseleave", "jets", () => { map.getCanvas().style.cursor = ""; pop.remove(); });
  map.on("mousemove", "jets", e => { const j = J[e.features[0].properties.i]; pop.setLngLat([j.lon, j.lat]).setHTML(`<b>${esc(j.model)}</b>${j.ground ? "On the ground" : (ft(j.alt) ?? "?").toLocaleString("en-US") + " ft, " + (j.kn ?? "?") + " kn"}`).addTo(map); });
  map.on("click", "jets", e => { e.originalEvent.stopPropagation(); selectJet(e.features[0].properties.i, false); });
  for (const h of D.hubs) { const el = document.createElement("div"); el.className = "cpm hub show"; el.innerHTML = `<b role="button" tabindex="0" aria-label="${h.name}"></b><span>${h.name}<em>${hubJets(h).length}</em></span>`; el.onclick = e => { e.stopPropagation(); selectHub(h, true); }; new maplibregl.Marker({element: el}).setLngLat([h.lon, h.lat]).addTo(map); marks.set(h.code, el); }
  kinds(); inView();
});
map.on("moveend", inView);
const ro = document.getElementById("ro"); const readout = ll => ro.textContent = `${ll ? dm(ll.lat, "N", "S") + "  " + dm(ll.lng, "E", "W") + "    " : ""}zoom ${map.getZoom().toFixed(1)}`;
map.on("mousemove", e => readout(e.lngLat)); map.on("zoom", () => readout(null)); readout(null);
document.querySelectorAll("[data-base]").forEach(b => b.onclick = () => { const sat = b.dataset.base === "sat"; ["sat", "ref"].forEach(l => map.setLayoutProperty(l, "visibility", sat ? "visible" : "none")); map.setLayoutProperty("dark", "visibility", sat ? "none" : "visible"); document.querySelectorAll("[data-base]").forEach(x => x.setAttribute("aria-pressed", x === b)); });
function kinds() { const el = document.getElementById("kinds"); el.innerHTML = MAKERS.map((k, i) => `<button aria-pressed="${on[i]}" data-k="${i}"><i style="background:${MCOL[i]}"></i>${k} <b>${counts[i]}</b></button>`).join("");
  el.querySelectorAll("button").forEach(b => b.onclick = () => { const i = +b.dataset.k; on[i] = !on[i]; b.setAttribute("aria-pressed", on[i]); map.setFilter("jets", ["in", ["get", "k"], ["literal", on.map((v, j) => v ? j : -1).filter(j => j >= 0)]]); inView(); }); }
// jets within 50 km of an airfield and below 3,000 m, or on the ground: arriving, leaving or parked
function hubJets(h) { return J.map((j, i) => [j, i]).filter(([j]) => km(j.lat, j.lon, h.lat, h.lon) <= 50 && (j.ground || (j.alt ?? 1e9) < 3000)); }
function listHubs() { const rows = D.hubs.map(h => [h, hubJets(h).length, (dd.hubs || {})[h.code]]).sort((a, b) => b[1] - a[1]); const el = document.getElementById("list-cp");
  el.innerHTML = `<p class="note">Business jets within 50 km of each airfield and below 10,000 ft: arriving, leaving or on the ground with the transponder on.</p><div class="lh"><span>Airfield</span><span>Now</span><span>Day's avg, 15 km</span></div>` + rows.map(([h, n, a]) =>
    `<button class="row${selH === h ? " is-on" : ""}" data-c="${h.code}"><span class="n">${h.name}<span class="s">${h.code}</span></span><span class="r">${n}</span><span class="r dim">${a == null ? "[n/a]" : a.toFixed(1)}</span></button>`).join("");
  el.querySelectorAll(".row").forEach(r => r.onclick = () => selectHub(D.hubs.find(h => h.code === r.dataset.c), true)); }
function inView() { if (!map.getLayer("jets")) return; const seen = new Set(), rows = []; for (const f of map.queryRenderedFeatures({layers: ["jets"]})) { const i = f.properties.i; if (!seen.has(i)) { seen.add(i); rows.push(i); } }
  rows.sort((a, b) => J[b].lr - J[a].lr || (J[b].alt ?? 0) - (J[a].alt ?? 0)); const el = document.getElementById("list-vs");
  el.innerHTML = `<div class="lh"><span></span><span>${rows.length} in view, long range first</span><span>Altitude</span></div>` + rows.slice(0, 80).map(i => { const j = J[i];
    return `<button class="row${i === selJ ? " is-on" : ""}" data-i="${i}"><i class="dot" style="background:${MCOL[j.k]}"></i><span class="n">${esc(j.model)}<span class="s">${j.ground ? "On the ground" : (j.kn ?? "?") + " kn, heading " + (j.trk ?? "?") + "\u00b0"}</span></span><span class="r dim">${j.ground ? "" : ((ft(j.alt) ?? 0) / 1000).toFixed(0) + "k ft"}</span></button>`; }).join("");
  el.querySelectorAll(".row").forEach(r => r.onclick = () => selectJet(+r.dataset.i, true)); }
document.querySelectorAll("[data-tab]").forEach(b => b.onclick = () => { document.querySelectorAll("[data-tab]").forEach(x => x.setAttribute("aria-selected", x === b)); document.getElementById("list-cp").hidden = b.dataset.tab !== "cp"; document.getElementById("list-vs").hidden = b.dataset.tab !== "vs"; });
const card = document.getElementById("card");
function marksSel() { for (const [c, el] of marks) el.classList.toggle("is-on", !!selH && c === selH.code); }
function closeCard() { card.classList.remove("show"); selJ = null; selH = null; marksSel(); map.getSource("sel")?.setData({type: "FeatureCollection", features: []}); listHubs(); inView(); }
function show(html) { card.innerHTML = `<button class="x" aria-label="Close">\u00d7</button>` + html; card.classList.remove("show"); void card.offsetWidth; card.classList.add("show"); card.querySelector(".x").onclick = closeCard; }
function selectJet(i, fly) { selJ = i; selH = null; marksSel(); const j = J[i]; map.getSource("sel").setData({type: "Feature", geometry: {type: "Point", coordinates: [j.lon, j.lat]}});
  const near = D.hubs.map(h => [km(j.lat, j.lon, h.lat, h.lon), h]).sort((a, b) => a[0] - b[0])[0];
  show(`<div class="hd"><p class="tag"><i style="background:${MCOL[j.k]}"></i>${MAKERS[j.k]}${j.lr ? ", long range" : ""}</p><h2>${esc(j.model)}</h2><p class="sub">${dm(j.lat, "N", "S")}  ${dm(j.lon, "E", "W")}</p></div>
  <div class="g2" style="border-top:0"><div><span>Altitude</span><b>${j.ground ? "On the ground" : (ft(j.alt) ?? 0).toLocaleString("en-US") + " <small>ft</small>"}</b></div><div><span>Ground speed</span><b>${j.kn ?? "[n/a]"} <small>kn</small></b></div>
  <div><span>Heading</span><b>${j.trk == null ? "[n/a]" : j.trk + "\u00b0"}</b></div><div><span>Type code</span><b>${j.code}</b></div>
  <div style="grid-column:1/-1;border-right:0"><span>Nearest airfield watched</span><b style="font-size:15px">${near[1].name}, ${Math.round(near[0]).toLocaleString("en-US")} km</b></div></div>
  <p class="src">ADS-B from the OpenSky Network. The jet is told by its type alone: no registration, owner, operator or person is recorded or shown. Aircraft whose owners asked not to be tracked are not in the public feed.</p>`);
  if (fly) map.flyTo({center: [j.lon, j.lat], zoom: Math.max(map.getZoom(), 7), duration: reduce ? 0 : 1600, essential: true}); inView(); listHubs(); }
function selectHub(h, fly) { selH = h; selJ = null; marksSel(); map.getSource("sel")?.setData({type: "FeatureCollection", features: []}); const js = hubJets(h); const by = {}; for (const [j] of js) by[j.model] = (by[j.model] || 0) + 1;
  const a = (dd.hubs || {})[h.code];
  show(`<div class="hd"><p class="tag">Airfield, ${h.code}</p><h2>${h.name}</h2><p class="sub">${dm(h.lat, "N", "S")}  ${dm(h.lon, "E", "W")}</p></div>
  <div class="big"><b>${js.length}</b><span>business jets within 50 km<br>and below 10,000 ft, at ${hhmm} UTC</span></div>
  <div class="g2"><div><span>In the air nearby</span><b>${js.filter(([j]) => !j.ground).length}</b></div><div><span>On the ground</span><b>${js.filter(([j]) => j.ground).length}</b></div>
  <div><span>Long range</span><b>${js.filter(([j]) => j.lr).length}</b></div><div><span>Day's average, 15 km</span><b>${a == null ? "[n/a]" : a.toFixed(1)}</b></div></div>
  <div class="sec"><span>By model, now</span></div><div class="types">${Object.entries(by).sort((x, y) => y[1] - x[1]).map(([m, n]) => `<div><span>${esc(m)}</span><b>${n}</b></div>`).join("") || '<div><span>None heard at this sample</span><b></b></div>'}</div>
  <p class="src">A count, not a schedule: a jet parked with its transponder off is not heard. The daily history began on ${day}; a comparison with the same weekday needs a few weeks of samples.</p>`);
  if (fly) map.flyTo({center: [h.lon, h.lat], zoom: 8.5, duration: reduce ? 0 : 2200, curve: 1.5, essential: true, padding: phone() ? {bottom: innerHeight * .5} : {left: 340, right: 350}}); listHubs(); }
map.on("click", e => { if (!map.queryRenderedFeatures(e.point, {layers: ["jets"]}).length && selJ != null) closeCard(); });
listHubs(); window.__api = {selectHub, selectJet, J, D, map};
})();
