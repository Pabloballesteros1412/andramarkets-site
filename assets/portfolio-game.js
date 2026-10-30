// Andra Markets Simulators: the Portfolio Builder. Split $10,000 between US
// stocks, bonds and cash and run it through ten hidden years since 1928,
// against the classic 60/40. Monthly returns from assets/simdata-portfolio.js
// (written by tools/build_site.py). Runs in the browser.
(function () {
  "use strict";
  var main = document.querySelector(".sim-page");
  var cfgEl = document.getElementById("pb-config");
  if (!main || !cfgEl) return;
  var CFG = JSON.parse(cfgEl.textContent);
  var BASE = main.getAttribute("data-base") || "../../";
  var M = 120; // ten years of months
  var START = 10000;
  var CASH = Math.pow(1.02, 1 / 12) - 1;
  var MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  var W = 640, H = 300, PAD = 10;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function $(name) {
    return main.querySelector('[data-pb="' + name + '"]');
  }
  function money(v) {
    return "$" + Math.round(v).toLocaleString("en-US");
  }
  function signed(v, dec, unit) {
    var s = Math.abs(v).toFixed(dec);
    if (+s === 0) return { text: (0).toFixed(dec) + unit, cls: "" };
    return { text: (v > 0 ? "+" : "−") + s + unit, cls: v > 0 ? "mv--up" : "mv--down" };
  }
  function moveHtml(v, dec, unit) {
    var m = signed(v, dec, unit);
    return '<span class="' + m.cls + '">' + m.text + "</span>";
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  var months = [], stocks = [], bonds = [];
  function load(done) {
    if (months.length) return done();
    function unpack(d) {
      var y = +d.first.slice(0, 4), m = +d.first.slice(5, 7) - 1;
      stocks = d.s.split(",").map(function (v) {
        return +v / 1e5;
      });
      bonds = d.b.split(",").map(function (v) {
        return +v / 1e5;
      });
      for (var i = 0; i < stocks.length; i++) {
        months.push(y + "-" + ("0" + (m + 1)).slice(-2));
        if (++m === 12) {
          m = 0;
          y++;
        }
      }
      done();
    }
    if (window.ANDRA_SIMDATA && window.ANDRA_SIMDATA.portfolio) return unpack(window.ANDRA_SIMDATA.portfolio);
    var s = document.createElement("script");
    s.src = BASE + "assets/" + CFG.file;
    s.onload = function () {
      unpack(window.ANDRA_SIMDATA.portfolio);
    };
    document.head.appendChild(s);
  }

  var start = -1, revealed = false, reb = true, anim = 0;

  function mix() {
    var s = +$("s").value, b = +$("b").value;
    return { s: s, b: b, c: 100 - s - b };
  }
  function syncSliders(moved) {
    var s = $("s"), b = $("b");
    if (+s.value + +b.value > 100) (moved === s ? b : s).value = 100 - +moved.value;
    var m = mix();
    $("s-v").textContent = m.s + "%";
    $("b-v").textContent = m.b + "%";
    $("c-v").textContent = m.c + "%";
    $("mixname").textContent = "Your mix, " + m.s + "/" + m.b + "/" + m.c;
  }

  // Monthly values of a mix over the ten years; with rebalancing, back to the
  // target weights every twelve months.
  function run(w, rebalance) {
    var h = [w.s / 100 * START, w.b / 100 * START, w.c / 100 * START], out = [START];
    for (var i = 0; i < M; i++) {
      h[0] *= 1 + stocks[start + i];
      h[1] *= 1 + bonds[start + i];
      h[2] *= 1 + CASH;
      var v = h[0] + h[1] + h[2];
      out.push(v);
      if (rebalance && (i + 1) % 12 === 0) h = [w.s / 100 * v, w.b / 100 * v, w.c / 100 * v];
    }
    return out;
  }
  function worstFall(vals) {
    var peak = vals[0], worst = 0;
    vals.forEach(function (v) {
      peak = Math.max(peak, v);
      worst = Math.min(worst, v / peak - 1);
    });
    return worst;
  }

  function draw(you, bench, upto) {
    var all = you.concat(bench), lo = Math.min.apply(null, all), hi = Math.max.apply(null, all);
    var pad = (hi - lo) * 0.06;
    lo -= pad;
    hi += pad;
    var x = function (i) {
      return (i / M) * W;
    };
    var y = function (v) {
      return PAD + ((hi - v) / (hi - lo)) * (H - 2 * PAD);
    };
    var raw = (hi - lo) / 4, p = Math.pow(10, Math.floor(Math.log10(raw))), k = raw / p;
    var st = (k < 1.5 ? 1 : k < 3 ? 2 : k < 7 ? 5 : 10) * p, out = [], lab = [];
    for (var v = Math.ceil(lo / st) * st; v < hi; v += st) {
      out.push('<line class="sim-grid" x1="0" x2="' + W + '" y1="' + y(v).toFixed(1) + '" y2="' + y(v).toFixed(1) + '"/>');
      lab.push('<span style="top:' + ((y(v) / H) * 100).toFixed(1) + '%">' + money(v) + "</span>");
    }
    function path(s) {
      var d = "";
      for (var i = 0; i <= upto; i++) d += (i ? "L" : "M") + x(i).toFixed(1) + "," + y(s[i]).toFixed(1);
      return d;
    }
    out.push('<path class="sim-idx" d="' + path(bench) + '"/><path class="sim-you" d="' + path(you) + '"/>');
    $("chart").innerHTML = out.join("");
    $("ylabs").innerHTML = lab.join("");
  }

  // The episodes the ten years run through, in order, with the months of each.
  function overlapTitles() {
    var a = months[start], b = months[start + M - 1], hits = [];
    CFG.episodes.forEach(function (e) {
      var from = a > e.from ? a : e.from, to = b < e.to ? b : e.to;
      if (from <= to) hits.push({ e: e, o: monthsBetween(from, to) });
    });
    return hits;
  }
  function monthsBetween(a, b) {
    return (+b.slice(0, 4) - +a.slice(0, 4)) * 12 + (+b.slice(5, 7) - +a.slice(5, 7));
  }
  function monthName(m) {
    return MONTHS[+m.slice(5, 7) - 1] + " " + m.slice(0, 4);
  }

  function results(you, bench) {
    var final = you[M], worst = worstFall(you), vs = (final - bench[M]) / 100;
    $("figs").innerHTML =
      "<div><span>Final value</span><b>" + money(final) + "</b> " + moveHtml((final / START - 1) * 100, 1, "%") + "</div>" +
      "<div><span>Worst fall</span><b>" + moveHtml(worst * 100, 1, "%") + "</b></div>" +
      "<div><span>Against 60/40</span><b>" + moveHtml(vs, 1, " pts") + "</b></div>";
    $("figs").hidden = false;
    var hits = overlapTitles(), main_ = hits.slice().sort(function (p, q) {
      return q.o - p.o;
    })[0];
    var titles = hits.map(function (h) {
      return h.e.title;
    });
    var along = titles.join("; ");
    var links = main_ ? main_.e.links.map(function (l) {
      return '<a class="link" href="' + BASE + l[1] + '">' + esc(l[0]) + ' <svg class="icon" aria-hidden="true"><use href="#i-arrow-right"/></svg></a>';
    }).join("") : "";
    $("reveal").innerHTML = "<h2>These were " + monthName(months[start]) + " to " + monthName(months[start + M - 1]) + ".</h2>" +
      "<p>Along the way: " + esc(along) + ".</p>" + '<div class="sim-links">' + links + "</div>" + '<p class="sim-src">' + esc(CFG.src) + ". Calculated in your browser. Not investment advice.</p>";
    $("reveal").hidden = false;
    $("tag").textContent = monthName(months[start]) + " to " + monthName(months[start + M - 1]) + " · US stocks, bonds and cash";
    revealed = true;
    $("run").firstChild.textContent = "Run again ";
    $("new").hidden = false;
  }

  function go() {
    load(function () {
      if (start < 0) start = Math.floor(Math.random() * (months.length - M));
      var you = run(mix(), reb), bench = run({ s: 60, b: 40, c: 0 }, true);
      $("empty").hidden = true;
      cancelAnimationFrame(anim);
      if (reduce) {
        draw(you, bench, M);
        results(you, bench);
        return;
      }
      var t0 = performance.now(), dur = revealed ? 900 : 2400;
      (function frame(t) {
        var upto = Math.min(M, Math.round(((t - t0) / dur) * M));
        draw(you, bench, upto);
        if (upto < M) anim = requestAnimationFrame(frame);
        else results(you, bench);
      })(t0);
    });
  }

  $("form").addEventListener("submit", function (e) {
    e.preventDefault();
    go();
  });
  $("new").addEventListener("click", function () {
    start = -1;
    revealed = false;
    $("figs").hidden = true;
    $("reveal").hidden = true;
    $("new").hidden = true;
    $("run").firstChild.textContent = "Run ten years ";
    $("tag").textContent = "Ten hidden years · US stocks, bonds and cash";
    go();
  });
  ["s", "b"].forEach(function (k) {
    $(k).addEventListener("input", function () {
      syncSliders($(k));
    });
  });
  main.querySelectorAll("[data-reb]").forEach(function (b) {
    b.addEventListener("click", function () {
      reb = b.getAttribute("data-reb") === "1";
      main.querySelectorAll("[data-reb]").forEach(function (x) {
        x.setAttribute("aria-pressed", x === b ? "true" : "false");
      });
    });
  });
  $("tag").textContent = "Ten hidden years · US stocks, bonds and cash";
  syncSliders($("s"));
})();
