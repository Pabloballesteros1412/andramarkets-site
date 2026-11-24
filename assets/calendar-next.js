/* Calendar: what comes next, large (owner, 25 Nov 2026). Over the table: the next event of high importance that
   has a time, in large type, with a countdown to it, its region, its previous figure and both clocks; under it
   the three after it. Read from the table's own rows (their <time datetime>), so it shows only what the page
   lists; a press goes to the event's row. With no timed event ahead it stays hidden. */
(function () {
  "use strict";
  var head = document.querySelector(".cl__head"), rows = [].slice.call(document.querySelectorAll("tr.cl__row")); if (!head || !rows.length) return;
  var EV = []; rows.forEach(function (r, i) { var t = r.querySelector(".cl__ny time[datetime]"), n = r.querySelector(".cl__ev"); if (!t || !n) return; var at = Date.parse(t.getAttribute("datetime")); if (isNaN(at)) return;
    if (!r.id) r.id = "cl-ev-" + i; var md = r.querySelector(".cl__md"), pr = r.querySelector(".cl__prior"), g = r.closest("tbody");
    EV.push({ at: at, row: r, name: n.textContent, region: r.getAttribute("data-region") || "", imp: r.getAttribute("data-imp"), ny: t.textContent, mad: md ? md.textContent : "", prior: pr ? pr.textContent.trim() : "", plabel: pr ? pr.getAttribute("data-label") || "Previous" : "", day: g ? (g.querySelector(".cl__day th") || {}).textContent || "" : "" }); });
  EV.sort(function (a, b) { return a.at - b.at; }); if (!EV.length) return;
  var box = document.createElement("div"); box.className = "cn"; box.hidden = true;
  box.innerHTML = '<p class="cn__k">Next</p><a class="cn__main"><span class="cn__count" role="timer" aria-live="off"></span><b class="cn__name"></b><span class="cn__meta"></span></a><p class="cn__k cn__k--then">Then</p><ol class="cn__then"></ol>';
  head.appendChild(box); var main = box.querySelector(".cn__main"), count = box.querySelector(".cn__count"), then = box.querySelector(".cn__then"), cur = null;
  function two(n) { return (n < 10 ? "0" : "") + n; }
  function left(ms) { var s = Math.max(0, Math.floor(ms / 1000)), d = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600), m = Math.floor(s % 3600 / 60); return (d ? d + "d " : "") + two(h) + "h " + two(m) + "m " + two(s % 60) + "s"; }
  function go(e) { return function (ev) { ev.preventDefault(); var w = e.row.getAttribute("data-week") || (e.row.closest("tbody") || e.row).getAttribute("data-week"), chip = w && document.querySelector('.cl__weeks [data-week="' + w + '"]'); if (chip && chip.getAttribute("aria-pressed") !== "true") chip.click();
    e.row.scrollIntoView({ behavior: "smooth", block: "center" }); e.row.classList.add("is-found"); setTimeout(function () { e.row.classList.remove("is-found"); }, 2400); }; }
  function meta(e) { return [e.day, e.ny + " New York" + (e.mad ? ", " + e.mad + " Madrid" : ""), e.region, e.prior ? e.plabel + " " + e.prior : ""].filter(Boolean).join(" · "); }
  function pick() { var now = Date.now(), ahead = EV.filter(function (e) { return e.at > now; }); if (!ahead.length) { box.hidden = true; document.querySelector("main").classList.remove("has-next"); return null; }
    var lead = ahead.filter(function (e) { return e.imp === "High"; })[0] || ahead[0];
    if (lead !== cur) { cur = lead; main.href = "#" + lead.row.id; main.onclick = go(lead); box.querySelector(".cn__name").textContent = lead.name; box.querySelector(".cn__meta").textContent = meta(lead);
      then.innerHTML = ""; ahead.filter(function (e) { return e !== lead && e.at >= lead.at; }).slice(0, 3).forEach(function (e) { var li = document.createElement("li"), a = document.createElement("a"); a.href = "#" + e.row.id; a.onclick = go(e);
        a.innerHTML = "<span></span><b></b><i></i>"; a.children[0].textContent = e.day.replace(/^(\w{3})\w*/, "$1") + ", " + e.ny; a.children[1].textContent = e.name; a.children[2].textContent = e.region; li.appendChild(a); then.appendChild(li); });
      box.querySelector(".cn__k--then").hidden = !then.children.length; box.hidden = false; document.querySelector("main").classList.add("has-next"); }
    return lead; }
  function tick() { var e = pick(); if (e) count.textContent = left(e.at - Date.now()); }
  tick(); setInterval(tick, 1000);
})();
