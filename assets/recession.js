// Recession watch (recession-watch/): one chart per indicator, drawn at the
// plot's pixel width in the Fed & Rates look (assets/fedrates.js): monochrome
// line styles, NBER recessions shaded in the chart fill, a dashed reference
// line, a crosshair readout (pointer and arrow keys), the range chips, a log
// scale for claims and "Save image" (a PNG of one chart, made in the browser).
(function () {
  "use strict";
  var el = document.getElementById("rw-data");
  if (!el) return;
  var D = JSON.parse(el.textContent);
  var NS = "http://www.w3.org/2000/svg";
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var state = { range: "Max", scale: "lin" };

  function mk(tag, attrs, parent, text) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  }
  function ticks(lo, hi, n) {
    if (!((hi - lo) / n > 0) || !isFinite(hi - lo)) return [];
    var step = Math.pow(10, Math.floor(Math.log10((hi - lo) / n)));
    var err = (hi - lo) / n / step;
    step *= err >= 5 ? 10 : err >= 2 ? 5 : err >= 1.4 ? 2 : 1;
    var out = [];
    for (var v = Math.ceil(lo / step) * step; v <= hi + step * 1e-6 && out.length < 50; v += step) out.push(+v.toFixed(6));
    return out;
  }
  function minus(s) {
    return String(s).replace("-", "−");
  }
  function signed(v, dec, unit) {
    var r = +v.toFixed(dec);
    return (r > 0 ? "+" : r < 0 ? "−" : "") + Math.abs(r).toFixed(dec) + (unit || "");
  }
  function level(v, dec, unit) {
    return minus(v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec })) + (unit || "");
  }
  function t(iso) {
    return Date.parse(iso + "T00:00:00Z");
  }
  function dlabel(iso, kind) {
    var p = iso.split("-");
    var d = +p[2] + " " + MON[+p[1] - 1] + " " + p[0];
    return kind === "month" ? MON[+p[1] - 1] + " " + p[0] : kind === "week" ? "Week to " + d : d;
  }

  // One chart. o: {id, series:[{name, xs, ys, cls}], bands:[[t0,t1]], refs:[{y, key}],
  // log:bool, fmt(v), xlabels(w), read(i)}
  function chart(o) {
    var box = document.getElementById(o.id + "-plot");
    var W = box.clientWidth || 640;
    var H = Math.max(240, Math.min(380, W * 0.42));
    var narrow = W < 520;
    // room on the right for the lines' names, when there is more than one
    var m = { l: 48, r: narrow || o.series.length < 2 ? 8 : 104, t: 12, b: 26 };
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
    (o.refs || []).forEach(function (r) { all.push(r.y); });
    var f = o.log ? function (v) { return Math.log10(Math.max(v, 1e-9)); } : function (v) { return v; };
    var lo = Math.min.apply(null, all.map(f)), hi = Math.max.apply(null, all.map(f));
    var pad = (hi - lo) * 0.1 || 0.1;
    lo -= pad;
    hi += pad;
    var x0 = Math.min.apply(null, xsAll), x1 = Math.max.apply(null, xsAll);
    function X(x) {
      return m.l + ((x - x0) / (x1 - x0 || 1)) * (W - m.l - m.r);
    }
    function Y(v) {
      return m.t + (1 - (f(v) - lo) / (hi - lo)) * (H - m.t - m.b);
    }
    var tv = o.log ? [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000].filter(function (v) {
      return f(v) >= lo && f(v) <= hi;
    }) : ticks(lo, hi, 4);
    // the axis takes the room its longest label needs (claims run to "5,000k")
    m.l = Math.max(40, Math.max.apply(null, tv.map(function (v) { return minus(o.fmt(v)).length; }).concat([0])) * 7 + 14);
    var shown = (o.bands || []).filter(function (b) { return b[1] > x0 && b[0] < x1; });
    shown.forEach(function (b) {
      var a = X(Math.max(b[0], x0)), z = X(Math.min(b[1], x1));
      mk("rect", { class: "fr-band", x: a, y: m.t, width: Math.max(1, z - a), height: H - m.t - m.b }, svg);
    });
    tv.forEach(function (v) {
      mk("line", { class: "grid-line", x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) }, svg);
      mk("text", { class: "chart__label", x: m.l - 8, y: Y(v) + 4, "text-anchor": "end" }, svg, minus(o.fmt(v)));
    });
    (o.refs || []).forEach(function (r) {
      mk("line", { class: "ref", x1: m.l, x2: W - m.r, y1: Y(r.y), y2: Y(r.y) }, svg);
    });
    o.xlabels(W - m.l - m.r).forEach(function (p) {
      if (p[0] >= x0 && p[0] <= x1) mk("text", { class: "chart__label", x: X(p[0]), y: H - 6, "text-anchor": "middle" }, svg, p[1]);
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
      for (var i = s.ys.length - 1; i >= 0; i--) if (s.ys[i] != null) {
        ends.push({ name: s.name, y: Y(s.ys[i]) });
        break;
      }
    });
    if (!narrow && o.series.length > 1) {
      ends.sort(function (a, b) { return a.y - b.y; });
      for (var i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 14) ends[i].y = ends[i - 1].y + 14;
      ends.forEach(function (e) {
        mk("text", { class: "chart__label chart__end", x: W - m.r + 8, y: e.y + 4 }, svg, e.name);
      });
    }
    var key = document.getElementById(o.id + "-key");
    key.innerHTML = o.series.map(function (s) {
      return '<span><svg class="key__line" viewBox="0 0 16 6"><line class="' + s.cls + '" x1="0" x2="16" y1="3" y2="3" style="fill:none"/></svg>' + s.name + "</span>";
    }).join("") + (shown.length || (o.bands || []).length ? '<span><i class="fr-sw-band"></i>NBER recession</span>' : "")
      + (o.refs || []).filter(function (r) { return r.key; }).map(function (r) { return '<span><i class="k-ref"></i>' + r.key + "</span>"; }).join("");
    key.querySelectorAll("svg").forEach(function (s) { s.classList.add("chart"); });
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
      var inRec = (o.bands || []).some(function (b) { return base.xs[cur] >= b[0] && base.xs[cur] < b[1]; });
      read.innerHTML = o.read(cur) + (inRec ? ". In an NBER recession" : "");
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

  // The range: the last 1 to 20 years, or everything (from 1970 or the series' start).
  function cut(dates) {
    if (state.range === "Max") return 0;
    var last = t(dates[dates.length - 1]);
    var from = last - { "1Y": 1, "2Y": 2, "5Y": 5, "10Y": 10, "20Y": 20 }[state.range] * 365.25 * 864e5;
    var i0 = dates.findIndex(function (d) { return t(d) >= from; });
    if (i0 < 0 || dates.length - i0 < 3) i0 = Math.max(0, dates.length - 3);
    return i0;
  }
  // Axis labels spaced by time, not by point (older history is weekly).
  function timeLabels(dates, i0) {
    return function (w) {
      var t0 = t(dates[i0]), t1 = t(dates[dates.length - 1]);
      var n = Math.max(2, Math.floor(w / 90)), out = [];
      var days = (t1 - t0) / 864e5;
      var a = new Date(t0), y = a.getUTCFullYear(), mo = a.getUTCMonth();
      if (days > 2.5 * 365) {
        var step = [1, 2, 5, 10, 20].filter(function (k) { return days / 365.25 / k <= n; })[0] || 20;
        for (var yr = Math.ceil((y + 1) / step) * step; Date.UTC(yr, 0, 1) <= t1; yr += step) out.push([Date.UTC(yr, 0, 1), String(yr)]);
      } else {
        var sm = [1, 2, 3, 6, 12].filter(function (k) { return days / 30.4 / k <= n; })[0] || 12;
        for (var k = 1; Date.UTC(y, mo + k, 1) <= t1; k++) {
          var d = new Date(Date.UTC(y, mo + k, 1));
          if (d.getUTCMonth() % sm === 0) out.push([d.getTime(), MON[d.getUTCMonth()] + " " + String(d.getUTCFullYear()).slice(2)]);
        }
      }
      return out;
    };
  }
  var BANDS = (D.rec || []).map(function (p) { return [t(p[0]), t(p[1])]; });

  function draw(key, opts) {
    var b = D[key];
    if (!b || !document.getElementById("rw-" + key + "-c-plot")) return;
    var i0 = cut(b.dates);
    var dates = b.dates.slice(i0), xs = dates.map(t);
    var list = b.series || [{ name: opts.name, values: b.values }];
    var series = list.map(function (s, k) {
      return { name: s.name, xs: xs, ys: s.values.slice(i0), cls: (opts.styles || ["s0"])[k] };
    });
    chart({
      id: "rw-" + key + "-c", series: series, bands: BANDS, refs: opts.refs, log: opts.log, fmt: opts.fmt,
      xlabels: timeLabels(b.dates, i0),
      read: function (i) {
        var kind = opts.kind === "daily" ? (t(dates[dates.length - 1]) - xs[i] > 2 * 365.25 * 864e5 ? "week" : "day") : opts.kind;
        return "<b>" + dlabel(dates[i], kind) + "</b>: " + series.map(function (s) {
          return (series.length > 1 ? s.name + " " : "") + (s.ys[i] == null ? "n/a" : opts.rfmt(s.ys[i]));
        }).join(", ");
      },
    });
  }
  var DRAW = {
    curve: function () {
      draw("curve", { name: "10Y-3M", kind: "daily", refs: [{ y: 0, key: "Zero: inverted below" }],
        fmt: function (v) { return v.toFixed(0); }, rfmt: function (v) { return level(v, 0, " bp"); } });
    },
    sahm: function () {
      draw("sahm", { name: "Sahm rule", kind: "month", refs: [{ y: D.sahm ? D.sahm.trigger : 0.5, key: "0.50 trigger" }],
        fmt: function (v) { return v.toFixed(1); }, rfmt: function (v) { return level(v, 2, " pp"); } });
    },
    claims: function () {
      draw("claims", { kind: "week", styles: ["s5", "s0"], log: state.scale === "log",
        fmt: function (v) { return v.toLocaleString("en-US", { maximumFractionDigits: 0 }) + "k"; },
        rfmt: function (v) { return level(v, 0, "k"); } });
    },
    hy: function () {
      draw("hy", { name: "High-yield spread", kind: "daily",
        fmt: function (v) { return v.toFixed(0); }, rfmt: function (v) { return level(v, 0, " bp"); } });
    },
    nfci: function () {
      draw("nfci", { name: "NFCI", kind: "week", refs: [{ y: 0, key: "Zero: the average" }],
        fmt: function (v) { return v.toFixed(1); }, rfmt: function (v) { return level(v, 2); } });
    },
  };
  function drawAll() {
    for (var k in DRAW) DRAW[k]();
  }

  document.querySelectorAll("[data-range]").forEach(function (b) {
    b.addEventListener("click", function () {
      document.querySelectorAll("[data-range]").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      state.range = b.getAttribute("data-range");
      drawAll();
    });
  });
  document.querySelectorAll("[data-scale]").forEach(function (b) {
    b.addEventListener("click", function () {
      document.querySelectorAll("[data-scale]").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      state.scale = b.getAttribute("data-scale");
      DRAW.claims();
    });
  });
  var rt, lastW = window.innerWidth;
  window.addEventListener("resize", function () {
    if (window.innerWidth === lastW) return;  // a phone's toolbar showing or hiding changes only the height
    lastW = window.innerWidth;
    clearTimeout(rt);
    rt = setTimeout(drawAll, 120);
  });
  drawAll();

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
        ctx.fillText("Recession watch: " + sec.querySelector("h2").textContent, P, 74, w);
        ctx.drawImage(img, P, top, w, h);
        ctx.fillStyle = ink3;
        ctx.font = '400 12px "Schibsted Grotesk", Arial, sans-serif';
        ctx.fillText(sec.querySelector(".fr__src").textContent.replace(/\s+/g, " ").trim(), P, top + h + 30, w);
        ctx.fillText("Andra Markets. For information only. Not investment advice.", P, top + h + 48, w);
        cv.toBlob(function (blob) {
          var a = document.createElement("a");
          a.href = URL.createObjectURL(blob);
          a.download = "andra-markets-" + pid.replace("rw-", "recession-watch-") + "-" + new Date().toISOString().slice(0, 10) + ".png";
          document.body.appendChild(a);
          a.click();
          setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
          btn.disabled = false;
        }, "image/png");
      };
      img.onerror = function () { btn.disabled = false; };
      img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(new XMLSerializer().serializeToString(clone));
    });
  });
})();
