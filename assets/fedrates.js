// Fed & Rates (fed-rates/): charts drawn at the plot's pixel width in the
// monochrome line styles (s0 to s5), a crosshair readout (pointer and arrow
// keys), the range chips, curve comparisons, inversion bands, the FOMC
// countdown and "Save image" (a PNG of one chart, made in the browser).
(function () {
  "use strict";
  var D = JSON.parse(document.getElementById("fr-data").textContent);
  var NS = "http://www.w3.org/2000/svg";
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var state = { range: "5Y", cmp: { "1W": false, "1M": true, "1Y": false }, sp: "0" };

  function mk(tag, attrs, parent, text) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  }
  function ticks(lo, hi, n) {
    var step = Math.pow(10, Math.floor(Math.log10((hi - lo) / n)));
    var err = (hi - lo) / n / step;
    step *= err >= 5 ? 10 : err >= 2 ? 5 : err >= 1.4 ? 2 : 1;
    var out = [];
    for (var v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(6));
    return out;
  }
  function minus(s) {
    return String(s).replace("-", "−");
  }
  function signed(v, dec, unit) {
    var s = (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(dec) + (unit || "");
    return s;
  }
  function dlabel(iso, monthly) {
    var p = iso.split("-");
    return monthly ? MON[+p[1] - 1] + " " + p[0] : +p[2] + " " + MON[+p[1] - 1] + " " + p[0];
  }
  function t(iso) {
    return Date.parse(iso + "T00:00:00Z");
  }

  // One chart. o: {id, series:[{name, xs, ys, cls}], x:"time"|"cat"|"sqrt", cats,
  // bands:[[x0,x1]], refs:[{y,label}], dots:bool, fmt(v), xfmt(x), read(i)}
  function chart(o) {
    var box = document.getElementById(o.id + "-plot");
    var W = box.clientWidth || 640;
    var H = Math.max(240, Math.min(380, W * 0.42));
    var narrow = W < 520;
    var m = { l: 44, r: narrow ? 8 : 104, t: 12, b: 26 };
    box.innerHTML = "";
    box.style.height = H + "px";
    var svg = mk("svg", { class: "chart", viewBox: "0 0 " + W + " " + H, width: W, height: H, role: "presentation" }, box);
    var all = [], xsAll = [];
    o.series.forEach(function (s) {
      s.ys.forEach(function (v, i) {
        if (v != null) {
          all.push(v);
          xsAll.push(s.xs[i]);
        }
      });
    });
    (o.refs || []).forEach(function (r) {
      all.push(r.y);
    });
    (o.points || []).forEach(function (p) {
      all.push(p[1]);
    });
    var lo = Math.min.apply(null, all), hi = Math.max.apply(null, all);
    var pad = (hi - lo) * 0.1 || 0.1;
    lo -= pad;
    hi += pad;
    var x0 = Math.min.apply(null, xsAll), x1 = Math.max.apply(null, xsAll);
    function X(x) {
      return m.l + ((x - x0) / (x1 - x0 || 1)) * (W - m.l - m.r);
    }
    function Y(v) {
      return m.t + (1 - (v - lo) / (hi - lo)) * (H - m.t - m.b);
    }
    (o.bands || []).forEach(function (b) {
      mk("rect", { class: "fr-band", x: X(b[0]), y: m.t, width: Math.max(1, X(b[1]) - X(b[0])), height: H - m.t - m.b }, svg);
    });
    ticks(lo, hi, 4).forEach(function (v) {
      mk("line", { class: "grid-line", x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) }, svg);
      mk("text", { class: "chart__label", x: m.l - 8, y: Y(v) + 4, "text-anchor": "end" }, svg, minus(o.fmt(v)));
    });
    (o.refs || []).forEach(function (r) {
      mk("line", { class: "ref", x1: m.l, x2: W - m.r, y1: Y(r.y), y2: Y(r.y) }, svg);
      if (r.label && !narrow) mk("text", { class: "chart__label", x: W - m.r + 6, y: Y(r.y) + 4 }, svg, r.label);
    });
    // x labels
    var xl = o.xlabels(W - m.l - m.r);
    xl.forEach(function (p) {
      mk("text", { class: "chart__label", x: X(p[0]), y: H - 6, "text-anchor": "middle" }, svg, p[1]);
    });
    var g = mk("g", { class: "fr-draw" }, svg);
    var ends = [];
    o.series.forEach(function (s) {
      var d = "", pen = false;
      s.ys.forEach(function (v, i) {
        if (v == null) {
          pen = false;
          return;
        }
        d += (pen ? "L" : "M") + X(s.xs[i]).toFixed(1) + " " + Y(v).toFixed(1);
        pen = true;
      });
      mk("path", { class: s.cls, d: d }, g);
      if (o.dots && s.cls === "s0") s.ys.forEach(function (v, i) {
        if (v != null) mk("circle", { class: "dot", cx: X(s.xs[i]), cy: Y(v), r: 2.5 }, g);
      });
      for (var i = s.ys.length - 1; i >= 0; i--) if (s.ys[i] != null) {
        if (o.noEnds) break;
        ends.push({ name: s.name, y: Y(s.ys[i]) });
        break;
      }
    });
    (o.points || []).forEach(function (p) {
      mk("circle", { class: "fr-intra", cx: X(p[0]), cy: Y(p[1]), r: 4 }, g);
    });
    if (!narrow && o.series.length > 1) {
      ends.sort(function (a, b) { return a.y - b.y; });
      for (var i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 14) ends[i].y = ends[i - 1].y + 14;
      ends.forEach(function (e) {
        mk("text", { class: "chart__label chart__end", x: W - m.r + 8, y: e.y + 4 }, svg, e.name);
      });
    }
    // key
    var key = document.getElementById(o.id + "-key");
    key.innerHTML = o.series.map(function (s) {
      return '<span><svg class="key__line" viewBox="0 0 16 6"><line class="' + s.cls + '" x1="0" x2="16" y1="3" y2="3" style="fill:none"/></svg>' + s.name + "</span>";
    }).join("") + (o.bands && o.bands.length ? '<span><i class="fr-sw-band"></i>Inverted</span>' : "")
      + (o.refs || []).filter(function (r) { return r.key; }).map(function (r) { return '<span><i class="k-ref"></i>' + r.key + "</span>"; }).join("")
      + (o.pointsKey ? '<span><i class="fr-sw-intra"></i>' + o.pointsKey + "</span>" : "");
    key.querySelectorAll("svg").forEach(function (s) { s.classList.add("chart"); });
    // crosshair and readout
    var base = o.series[0];
    var cross = mk("line", { class: "cross", y1: m.t, y2: H - m.b, x1: -10, x2: -10 }, svg);
    var hot = mk("g", { class: "fr-hot" }, svg);
    var read = document.getElementById(o.id + "-read");
    var cur = base.xs.length - 1;
    function show(i) {
      cur = Math.max(0, Math.min(base.xs.length - 1, i));
      var x = X(base.xs[cur]);
      cross.setAttribute("x1", x);
      cross.setAttribute("x2", x);
      hot.innerHTML = "";
      o.series.forEach(function (s) {
        var v = s.ys[cur];
        if (v != null) mk("circle", { class: "dot", cx: X(s.xs[cur]), cy: Y(v), r: 3.5 }, hot);
      });
      read.innerHTML = o.read(cur);
    }
    function nearest(px) {
      var best = 0, bd = Infinity;
      base.xs.forEach(function (x, i) {
        var dd = Math.abs(X(x) - px);
        if (dd < bd) { bd = dd; best = i; }
      });
      return best;
    }
    svg.addEventListener("pointermove", function (e) {
      var r = svg.getBoundingClientRect();
      show(nearest(((e.clientX - r.left) / r.width) * W));
    });
    box.onkeydown = function (e) {
      var k = { ArrowLeft: cur - 1, ArrowRight: cur + 1, Home: 0, End: base.xs.length - 1 }[e.key];
      if (k != null) { e.preventDefault(); show(k); }
    };
    show(cur);
  }

  // Range filter for time series
  function cut(block) {
    var last = t(block.dates[block.dates.length - 1]);
    var yrs = { "1M": 1 / 12, "3M": 0.25, "6M": 0.5, "1Y": 1, "2Y": 2, "5Y": 5, "10Y": 10, Max: 999 }[state.range];
    var from = last - yrs * 365.25 * 864e5;
    var i0 = block.dates.findIndex(function (d) { return t(d) >= from; });
    if (block.dates.length - i0 < 3) i0 = block.dates.length - 3;
    return Math.max(0, i0);
  }
  // Axis labels spaced by time, not by point: older history is weekly and
  // the last two years daily, so equal steps in points would bunch up.
  function timeLabels(dates, i0) {
    return function (w) {
      var t0 = t(dates[i0]), t1 = t(dates[dates.length - 1]);
      var n = Math.max(2, Math.floor(w / 90)), out = [];
      var days = (t1 - t0) / 864e5;
      var a = new Date(t0), y = a.getUTCFullYear(), m = a.getUTCMonth();
      if (days > 2.5 * 365) {
        var step = [1, 2, 5, 10, 20].filter(function (k) { return days / 365.25 / k <= n; })[0] || 20;
        for (var yr = Math.ceil((y + 1) / step) * step; Date.UTC(yr, 0, 1) <= t1; yr += step) out.push([Date.UTC(yr, 0, 1), String(yr)]);
      } else if (days > 62) {
        var sm = [1, 2, 3, 6, 12].filter(function (k) { return days / 30.4 / k <= n; })[0] || 12;
        for (var k = 1; Date.UTC(y, m + k, 1) <= t1; k++) {
          var d = new Date(Date.UTC(y, m + k, 1));
          if (d.getUTCMonth() % sm === 0) out.push([d.getTime(), MON[d.getUTCMonth()] + " " + String(d.getUTCFullYear()).slice(2)]);
        }
      } else {
        var sd = Math.max(7, Math.ceil(days / n / 7) * 7);
        for (var x = t1; x >= t0; x -= sd * 864e5) {
          var e = new Date(x);
          out.unshift([x, e.getUTCDate() + " " + MON[e.getUTCMonth()]]);
        }
      }
      return out;
    };
  }
  var STY = ["s0", "s1", "s3", "s2"];

  function drawSeriesBlock(id, block, pick, opts) {
    var i0 = cut(block);
    var dates = block.dates.slice(i0);
    var xs = dates.map(t);
    var monthly = opts.monthly;
    var series = pick.map(function (si, k) {
      var s = block.series[si];
      return { name: s.name, xs: xs, ys: s.values.slice(i0).map(opts.map || function (v) { return v; }), cls: STY[k] };
    });
    chart({
      id: id, series: series, bands: opts.bands ? opts.bands(series, xs) : null, refs: opts.refs,
      fmt: opts.fmt, xlabels: timeLabels(block.dates, i0),
      read: function (i) {
        return "<b>" + dlabel(dates[i], monthly) + "</b>: " + series.map(function (s) {
          return s.name + " " + (s.ys[i] == null ? "n/a" : opts.rfmt(s.ys[i]));
        }).join(", ");
      },
    });
  }

  function inversions(series, xs) {
    var bands = [], start = null;
    for (var i = 0; i < xs.length; i++) {
      var inv = series.some(function (s) { return s.ys[i] != null && s.ys[i] < 0; });
      if (inv && start == null) start = xs[i];
      if (!inv && start != null) { bands.push([start, xs[i]]); start = null; }
    }
    if (start != null) bands.push([start, xs[xs.length - 1]]);
    return bands;
  }

  function drawSpreads() {
    if (!D.spreads) return;
    var pick = state.sp === "2" ? [0, 1] : [+state.sp];
    drawSeriesBlock("fr-sp", D.spreads, pick, {
      monthly: true, map: function (v) { return v == null ? null : Math.round(v * 100); },
      bands: inversions, refs: [{ y: 0, key: "Zero" }],
      fmt: function (v) { return v.toFixed(0); }, rfmt: function (v) { return signed(v, 0, "bp"); },
    });
  }
  function drawMacro() {
    if (!D.macro) return;
    drawSeriesBlock("fr-mac", D.macro, [0, 1, 2, 3], {
      monthly: true, refs: [{ y: 2, key: "Fed 2% target" }],
      fmt: function (v) { return v.toFixed(0) + "%"; }, rfmt: function (v) { return v.toFixed(2) + "%"; },
    });
  }
  function drawReal() {
    if (!D.real) return;
    drawSeriesBlock("fr-re", D.real, [0, 1, 2, 3], {
      monthly: false, refs: [{ y: 0, key: "Zero" }],
      fmt: function (v) { return v.toFixed(1) + "%"; }, rfmt: function (v) { return v.toFixed(2) + "%"; },
    });
  }

  function drawCurve() {
    if (!D.curve) return;
    var c = D.curve, xs = c.years.map(Math.sqrt);
    var series = [{ name: c.dates.now, xs: xs, ys: c.curves.now, cls: "s0" }];
    var sty = { "1W": "s1", "1M": "s3", "1Y": "s2" };
    ["1W", "1M", "1Y"].forEach(function (k) {
      if (state.cmp[k] && c.curves[k]) series.push({ name: c.dates[k], xs: xs, ys: c.curves[k], cls: sty[k] });
    });
    var intra = {};
    (c.intra ? c.intra.points : []).forEach(function (p) { intra[p.tenor] = p.value; });
    chart({
      id: "fr-curve", series: series, dots: true,
      points: c.intra ? c.intra.points.map(function (p) { return [xs[c.tenors.indexOf(p.tenor)], p.value]; }) : null,
      pointsKey: c.intra ? c.intra.label + ", delayed" : null,
      fmt: function (v) { return v.toFixed(1) + "%"; },
      xlabels: function (w) {
        var keep = w < 480 ? ["1M", "1Y", "2Y", "5Y", "10Y", "30Y"] : w < 900 ? ["1M", "6M", "1Y", "2Y", "3Y", "5Y", "10Y", "20Y", "30Y"] : ["1M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"];
        return c.tenors.map(function (n, i) { return [xs[i], n]; }).filter(function (p) { return keep.indexOf(p[1]) > -1; });
      },
      read: function (i) {
        return "<b>" + c.tenors[i] + "</b>: " + series.map(function (s) { return s.name + " " + s.ys[i].toFixed(2) + "%"; }).join(", ")
          + (intra[c.tenors[i]] != null ? "; " + c.intra.label + ": " + intra[c.tenors[i]].toFixed(2) + "%" : "");
      },
    });
    // change table against the earliest comparison switched on
    var vs = ["1W", "1M", "1Y"].filter(function (k) { return state.cmp[k] && c.curves[k]; });
    var el = document.getElementById("fr-chg");
    if (!vs.length) { el.innerHTML = ""; return; }
    var rows = vs.map(function (k) {
      return "<tr><th scope=\"row\">Since " + c.dates[k] + "</th>" + c.tenors.map(function (_, i) {
        var bp = Math.round((c.curves.now[i] - c.curves[k][i]) * 100);
        return '<td class="' + (bp > 0 ? "mv--up" : bp < 0 ? "mv--down" : "") + '">' + signed(bp, 0) + "</td>";
      }).join("") + "</tr>";
    }).join("");
    el.innerHTML = '<table class="fr-tab"><caption>Change in basis points</caption><thead><tr><th scope="col">Maturity</th>'
      + c.tenors.map(function (n) { return '<th scope="col">' + n + "</th>"; }).join("") + "</tr></thead><tbody>" + rows + "</tbody></table>";
  }

  function drawPath() {
    if (!D.path) return;
    var p = D.path, xs = p.meetings.map(function (_, i) { return i; });
    var s = [{ name: "Now", xs: xs, ys: p.now, cls: "s0" }];
    if (p.ago && p.ago.some(function (v) { return v != null; })) s.push({ name: p.ago_label, xs: xs, ys: p.ago, cls: "s1" });
    chart({
      id: "fr-path", series: s, dots: true, refs: p.ref != null ? [{ y: p.ref, key: "Effective rate today" }] : [],
      fmt: function (v) { return v.toFixed(2) + "%"; },
      xlabels: function (w) {
        return p.meetings.map(function (n, i) { return [i, n]; }).filter(function (_, i) { return w > 480 || i % 2 === 0; });
      },
      read: function (i) {
        var out = "<b>After the " + p.meetings[i] + " meeting</b>: expected " + p.now[i].toFixed(2) + "%";
        if (s[1] && p.ago[i] != null) out += ", " + p.ago_label.toLowerCase() + " " + p.ago[i].toFixed(2) + "%";
        if (p.ref != null) {
          var bp = Math.round((p.now[i] - p.ref) * 100);
          out += ', <span class="' + (bp > 0 ? "mv--up" : bp < 0 ? "mv--down" : "") + '">' + signed(bp, 0, "bp") + "</span> from today";
        }
        return out;
      },
    });
  }

  function drawAll() {
    drawPath();
    drawCurve();
    drawSpreads();
    drawMacro();
    drawReal();
  }

  // Controls
  document.querySelectorAll("[data-range]").forEach(function (b) {
    b.addEventListener("click", function () {
      document.querySelectorAll("[data-range]").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      state.range = b.getAttribute("data-range");
      drawSpreads(); drawMacro(); drawReal();
    });
  });
  document.querySelectorAll("[data-cmp]").forEach(function (b) {
    b.addEventListener("click", function () {
      var k = b.getAttribute("data-cmp");
      state.cmp[k] = !state.cmp[k];
      b.setAttribute("aria-pressed", state.cmp[k] ? "true" : "false");
      drawCurve();
    });
  });
  document.querySelectorAll("[data-sp]").forEach(function (b) {
    b.addEventListener("click", function () {
      document.querySelectorAll("[data-sp]").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      state.sp = b.getAttribute("data-sp");
      drawSpreads();
    });
  });
  var rt;
  window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(drawAll, 120); });
  drawAll();

  // Countdown to the next decision (2:00 pm ET). Screen readers get the
  // label only; the ticking figures are hidden from them.
  var cdBox = document.getElementById("fr-cd");
  if (cdBox) {
    var target = Date.parse(cdBox.getAttribute("data-target"));
    var cd = {};
    cdBox.querySelectorAll("[data-cd]").forEach(function (e) { cd[e.getAttribute("data-cd")] = e; });
    var tick = function () {
      var s = Math.max(0, Math.floor((target - Date.now()) / 1000));
      var v = { d: Math.floor(s / 86400), h: Math.floor(s / 3600) % 24, m: Math.floor(s / 60) % 60, s: s % 60 };
      for (var k in v) cd[k].textContent = String(v[k]).padStart(2, "0");
      cdBox.setAttribute("aria-label", s ? "Time to the decision: " + v.d + " days, " + v.h + " hours, " + v.m + " minutes" : "Decision day");
    };
    tick();
    setInterval(tick, 1000);
  }

  // Save image: the panel's chart with its title, the mark, source and date.
  function inline(src, dst) {
    var cs = getComputedStyle(src);
    ["fill", "stroke", "stroke-width", "stroke-dasharray", "stroke-linecap", "stroke-linejoin", "opacity",
     "font-size", "font-weight", "font-family"].forEach(function (p) { dst.style.setProperty(p, cs.getPropertyValue(p)); });
    for (var i = 0; i < src.children.length; i++) inline(src.children[i], dst.children[i]);
  }
  document.querySelectorAll("[data-save]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var pid = btn.getAttribute("data-save");
      var sec = document.getElementById(pid);
      var svg = sec.querySelector(".fr__plot svg");
      if (!svg) return;
      btn.disabled = true;
      var root = getComputedStyle(document.documentElement);
      var ground = root.getPropertyValue("--ground").trim(), ink = root.getPropertyValue("--ink").trim(), ink3 = root.getPropertyValue("--ink-3").trim();
      var clone = svg.cloneNode(true);
      inline(svg, clone);
      clone.querySelectorAll(".cross, .fr-hot").forEach(function (n) { n.remove(); });
      clone.setAttribute("xmlns", NS);
      var w = +svg.getAttribute("width"), h = +svg.getAttribute("height");
      var img = new Image();
      img.onload = function () {
        var S = 2, P = 32, top = 96, foot = 72;
        var cv = document.createElement("canvas");
        cv.width = (w + P * 2) * S;
        cv.height = (h + top + foot) * S;
        var ctx = cv.getContext("2d");
        ctx.scale(S, S);
        ctx.fillStyle = ground;
        ctx.fillRect(0, 0, w + P * 2, h + top + foot);
        var mark = document.querySelector(document.documentElement.getAttribute("data-theme") === "dark" ? ".brand__mark--dark" : ".brand__mark--light");
        if (mark && mark.complete) ctx.drawImage(mark, P, 22, 17.5, 20);
        ctx.fillStyle = ink;
        ctx.font = '600 14px "Schibsted Grotesk", Arial, sans-serif';
        ctx.fillText("Andra Markets", P + 26, 38);
        ctx.font = '540 20px "Schibsted Grotesk", Arial, sans-serif';
        ctx.fillText("Fed & Rates: " + sec.querySelector("h2").textContent, P, 74);
        ctx.drawImage(img, P, top, w, h);
        ctx.fillStyle = ink3;
        ctx.font = '400 12px "Schibsted Grotesk", Arial, sans-serif';
        ctx.fillText(sec.querySelector(".fr__src").textContent.replace(/\s+/g, " ").trim(), P, top + h + 30, w);
        ctx.fillText("Andra Markets. For information only. Not investment advice.", P, top + h + 48, w);
        cv.toBlob(function (blob) {
          var a = document.createElement("a");
          a.href = URL.createObjectURL(blob);
          a.download = "andra-markets-" + pid.replace("fr-", "fed-rates-") + "-" + new Date().toISOString().slice(0, 10) + ".png";
          document.body.appendChild(a);
          a.click();
          setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
          btn.disabled = false;
        }, "image/png");
      };
      img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(new XMLSerializer().serializeToString(clone));
    });
  });
})();
