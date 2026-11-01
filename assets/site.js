// Andra Markets: theme, header state, menu, filters, reveals, signup, share,
// rolling figures, search and the methodology questions.
// The rolling figures, gliding chips, theme reveal, search palette, share swap
// and question panels are adapted from beUI (MIT License, Copyright (c) 2026
// Saurabh Chauhan, https://github.com/starc007/ui-components); see assets/LICENSE-beui.txt.
(function () {
  var root = document.documentElement;
  root.classList.add("js");
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  function still() {
    return reduce.matches;
  }

  // Rolling figures: each digit is a column of 0 to 9 that slides to its
  // value. Screen readers get the plain text; the columns are hidden from them.
  // Also used by assets/dashboard.js for the chart readout.
  // A column holds ten lines, so each digit is 10% of its height. Set as a
  // plain transform: Safari can leave a transition on a custom property
  // stuck halfway.
  function shift(d) {
    return "translateY(" + -10 * d + "%)";
  }
  function Roll(el, text) {
    this.el = el;
    this.sr = document.createElement("span");
    this.sr.className = "visually-hidden";
    this.vis = document.createElement("span");
    this.vis.className = "roll";
    this.vis.setAttribute("aria-hidden", "true");
    el.textContent = "";
    el.appendChild(this.sr);
    el.appendChild(this.vis);
    this.shape = null;
    this.cols = [];
    if (text != null) this.set(text);
  }
  // With data-moves on the element, a word that starts with a sign ("+0.42%",
  // "(−12)") is a rise or a fall and takes the up or down colour.
  Roll.prototype.build = function (text) {
    var vis = this.vis, cols = [], moves = this.el.hasAttribute("data-moves");
    vis.textContent = "";
    text.split(" ").forEach(function (word, w) {
      if (w) vis.appendChild(document.createTextNode(" "));
      var box = document.createElement("span");
      var sign = moves && /^\(?([+\u2212])\d/.exec(word);
      box.className = "roll__w" + (sign ? (sign[1] === "+" ? " mv--up" : " mv--down") : "");
      for (var i = 0; i < word.length; i++) {
        var c = word[i];
        var slot = document.createElement("span");
        if (c >= "0" && c <= "9") {
          slot.className = "roll__d";
          var col = document.createElement("span");
          col.className = "roll__col";
          for (var n = 0; n < 10; n++) {
            var line = document.createElement("span");
            line.textContent = n;
            col.appendChild(line);
          }
          col.style.transform = shift(c);
          slot.appendChild(col);
          cols.push(col);
        } else {
          slot.className = "roll__s";
          slot.textContent = c;
        }
        box.appendChild(slot);
      }
      vis.appendChild(box);
    });
    this.cols = cols;
    this.shape = text.replace(/[0-9]/g, "0");
  };
  Roll.prototype.set = function (text) {
    this.sr.textContent = text;
    if (text.replace(/[0-9]/g, "0") !== this.shape) {
      this.build(text);
      return;
    }
    var k = 0;
    for (var i = 0; i < text.length; i++) {
      var c = text[i];
      if (c >= "0" && c <= "9") this.cols[k++].style.transform = shift(c);
    }
  };
  // Builds at zero, then rolls up to the real figure.
  Roll.prototype.rollIn = function (text, delay) {
    var self = this;
    this.build(text.replace(/[0-9]/g, "0"));
    this.sr.textContent = text;
    void this.vis.offsetWidth;
    setTimeout(function () {
      self.set(text);
    }, delay || 0);
  };
  window.AndraRoll = Roll;

  // Tape: the closes roll up once when the tape comes into view. A live feed
  // can call update(text) on each figure's Roll later.
  var tapeFigs = document.querySelectorAll(".tape__level:not(.ph), .tape__chg:not(.ph)");
  if (tapeFigs.length) {
    var rolls = Array.prototype.map.call(tapeFigs, function (el) {
      var text = el.textContent.trim();
      return { roll: new Roll(el, text), text: text };
    });
    var rollTape = function () {
      if (still()) return;
      rolls.forEach(function (r, i) {
        r.roll.rollIn(r.text, 60 + Math.floor(i / 2) * 45);
      });
    };
    var tapeList = document.querySelector(".tape__list");
    if (tapeList && "IntersectionObserver" in window) {
      var tio = new IntersectionObserver(function (entries) {
        if (entries[0].isIntersecting) {
          tio.disconnect();
          rollTape();
        }
      });
      tio.observe(tapeList);
    }
  }

  // Header turns solid once the hero has scrolled under it.
  var header = document.querySelector(".site-header");
  var hero = document.querySelector(".hero__sentinel");
  if (header && hero && "IntersectionObserver" in window) {
    new IntersectionObserver(
      function (entries) {
        header.classList.toggle("is-solid", !entries[0].isIntersecting);
      },
      { threshold: 0 }
    ).observe(hero);
  } else if (header && document.body.classList.contains("has-scene")) {
    // section pages: the header stays clear over the scene until the page scrolls
    var shade = function () { header.classList.toggle("is-solid", window.scrollY > 8); };
    window.addEventListener("scroll", shade, { passive: true });
    shade();
  } else if (header) {
    header.classList.add("is-solid");
  }

  // Theme: dark by default (owner, 31 Oct 2026), the visitor's choice is remembered. The
  // header's mark is the switch (owner, 1 Nov 2026).
  var themeBtn = document.querySelector(".brand__toggle");
  function syncThemeBtn() {
    var dark = root.getAttribute("data-theme") === "dark";
    var label = dark ? "Switch to light theme" : "Switch to dark theme";
    themeBtn.setAttribute("aria-label", label);
    themeBtn.setAttribute("title", label);
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", dark ? "#0a0c0d" : "#ffffff");
  }
  if (themeBtn) {
    syncThemeBtn();
    themeBtn.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      var apply = function () {
        root.setAttribute("data-theme", next);
        syncThemeBtn();
      };
      try {
        localStorage.setItem("andra-theme", next);
      } catch (e) {}
      if (!document.startViewTransition || still()) {
        apply();
        return;
      }
      // The new theme opens as a circle from the mark and covers the page.
      var r = themeBtn.getBoundingClientRect();
      var x = r.left + r.width / 2;
      var y = r.top + r.height / 2;
      var end = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
      root.classList.add("theme-reveal");
      var vt = document.startViewTransition(apply);
      vt.ready
        .then(function () {
          root.animate(
            { clipPath: ["circle(0px at " + x + "px " + y + "px)", "circle(" + end + "px at " + x + "px " + y + "px)"] },
            { duration: 560, easing: "cubic-bezier(0.77, 0, 0.175, 1)", pseudoElement: "::view-transition-new(root)" }
          );
        })
        .catch(function () {});
      vt.finished.finally(function () {
        root.classList.remove("theme-reveal");
      });
    });
  }

  // Homepage groups (owner, 1 Nov 2026: the sections opened too abruptly): a group's list
  // grows to its height as it fades in, its sections following one another 25ms apart, and
  // folds away a little faster. One group is open at a time: the open one folds first, then
  // the next opens, so two lists never share the space (on phones they open in the same
  // place). The details keep their name attribute for when this script does not run; here
  // the script keeps one open itself, as the browser would close the other at once. Reduced
  // motion: the details open and close as they are.
  var groups = Array.prototype.slice.call(document.querySelectorAll(".hero__group"));
  var EASE_OUT = "cubic-bezier(0.23, 1, 0.32, 1)";
  // the list is clipped only while it moves, so a focused section's outline is never cut
  function clip(list, on) { list.style.overflow = on ? "hidden" : ""; }
  function foldGroup(d, done) {
    var list = d.querySelector("ul");
    if (d._anim) d._anim.cancel();
    if (!d.open) { if (done) done(); return; }
    clip(list, true);
    var a = list.animate(
      [{ height: list.offsetHeight + "px", paddingTop: getComputedStyle(list).paddingTop, opacity: 1 },
       { height: "0px", paddingTop: "0px", opacity: 0 }],
      { duration: 180, easing: "ease-in" }
    );
    d._anim = a;
    a.onfinish = function () { d._anim = null; d.open = false; clip(list, false); if (done) done(); };
  }
  function unfoldGroup(d) {
    var list = d.querySelector("ul");
    if (d._anim) d._anim.cancel();
    d.open = true;
    clip(list, true);
    var a = list.animate(
      [{ height: "0px", paddingTop: "0px", opacity: 0 },
       { height: list.offsetHeight + "px", paddingTop: getComputedStyle(list).paddingTop, opacity: 1 }],
      { duration: 280, easing: EASE_OUT }
    );
    d._anim = a;
    a.onfinish = function () { d._anim = null; clip(list, false); };
    Array.prototype.forEach.call(list.querySelectorAll("li"), function (li, i) {
      li.animate(
        [{ opacity: 0, transform: "translateY(-4px)" }, { opacity: 1, transform: "none" }],
        { duration: 240, delay: 40 + i * 25, easing: EASE_OUT, fill: "backwards" }
      );
    });
  }
  if (groups.length && "animate" in Element.prototype) {
    groups.forEach(function (d) { d.removeAttribute("name"); });
    groups.forEach(function (d) {
      d.querySelector("summary").addEventListener("click", function (e) {
        e.preventDefault();
        var opening = !d.open || (d._anim && d._anim.playState === "running" && d._closing);
        var other = groups.filter(function (g) { return g !== d && g.open; });
        if (still()) {
          other.forEach(function (g) { g.open = false; });
          d.open = !d.open;
          return;
        }
        if (!opening) { d._closing = true; foldGroup(d, function () { d._closing = false; }); return; }
        d._closing = false;
        if (!other.length) { unfoldGroup(d); return; }
        var left = other.length;
        other.forEach(function (g) { foldGroup(g, function () { if (--left === 0) unfoldGroup(d); }); });
      });
    });
  }

  // Moving to another page (owner-approved, 1 Nov 2026): section pages cross-fade into one
  // another (VIEW_TRANSITION in tools/build_site.py). The homepage takes no part, so a
  // transition towards it is called off here, before the browser starts it for nothing.
  window.addEventListener("pageswap", function (e) {
    var vt = e.viewTransition, to = e.activation && e.activation.entry && e.activation.entry.url;
    if (!vt || !to) return;
    vt.ready.catch(function () {});
    vt.finished.catch(function () {});
    var home = new URL(document.body.getAttribute("data-base") || "./", location.href).pathname;
    if (new URL(to).pathname === home) vt.skipTransition();
  });

  // Chip groups: the ink fill glides to the pressed chip. Works for any
  // .filters group, including the range chips that dashboard.js presses.
  // Chips pressed while the page sets up (a view or filter from the link's
  // fragment) take their place at once, as if the page had been built so.
  var settled = false;
  document.addEventListener("DOMContentLoaded", function () {
    settled = true;
  });
  document.querySelectorAll(".filters").forEach(function (group) {
    var ind = document.createElement("span");
    ind.className = "filters__glide";
    ind.setAttribute("aria-hidden", "true");
    group.insertBefore(ind, group.firstChild);
    group.classList.add("has-glide");
    function place(animate) {
      var on = group.querySelector('.chip[aria-pressed="true"]');
      // None pressed (a dashboard's comparison date replaces its range): no fill.
      ind.style.opacity = on ? "" : "0";
      if (!on) return;
      if (!animate) ind.style.transition = "none";
      ind.style.width = on.offsetWidth + "px";
      ind.style.height = on.offsetHeight + "px";
      ind.style.transform = "translate(" + on.offsetLeft + "px, " + on.offsetTop + "px)";
      if (!animate) {
        void ind.offsetWidth;
        ind.style.transition = "";
      }
    }
    place(false);
    new MutationObserver(function () {
      if (settled) {
        place(true);
        return;
      }
      var chips = group.querySelectorAll(".chip");
      chips.forEach(function (c) {
        c.style.transition = "none";
      });
      place(false);
      void group.offsetWidth;
      chips.forEach(function (c) {
        c.style.transition = "";
      });
    }).observe(group, { attributes: true, subtree: true, attributeFilter: ["aria-pressed"] });
    window.addEventListener("resize", function () {
      place(false);
    });
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(function () {
        place(false);
      });
    }
  });

  // Dashboard filters. The chosen category lives in the URL's fragment
  // (dashboards/#rates), so a filtered page can be shared; All leaves none.
  var chips = document.querySelectorAll(".chip[data-filter]");
  var tiles = document.querySelectorAll(".dash-tile");
  var filterStatus = document.querySelector(".filters__status");
  // enter: matching tiles fade in and rise; a filter from the link leaves
  // them to reveal on scroll, as on any other visit.
  var filterTo = function (chip, enter) {
    var cat = chip.getAttribute("data-filter");
    var shown = 0;
    chips.forEach(function (c) {
      c.setAttribute("aria-pressed", String(c === chip));
    });
    tiles.forEach(function (tile) {
      var match = cat === "all" || tile.getAttribute("data-cat") === cat;
      tile.hidden = !match;
      tile.classList.remove("is-entering");
      if (match) {
        if (enter) {
          tile.style.setProperty("--e", shown);
          tile.classList.add("is-in");
          void tile.offsetWidth;
          tile.classList.add("is-entering");
        }
        shown++;
      }
    });
    filterStatus.textContent =
      cat === "all"
        ? "Showing all " + tiles.length + " dashboards"
        : "Showing " + shown + " of " + tiles.length + " dashboards: " + chip.getAttribute("data-label");
  };
  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      var cat = chip.getAttribute("data-filter");
      filterTo(chip, true);
      history.replaceState(null, "", location.pathname + location.search + (cat === "all" ? "" : "#" + encodeURIComponent(cat)));
    });
  });
  var startCat = location.hash.slice(1).toLowerCase();
  chips.forEach(function (chip) {
    if (startCat && startCat !== "all" && chip.getAttribute("data-filter") === startCat) filterTo(chip, false);
  });

  // The menu's groups (owner-approved, 31 Oct 2026): above 960px each button opens its
  // panel under the header, one at a time. A click outside, Escape or a link closes it.
  var groupBtns = document.querySelectorAll(".nav__btn");
  function closeGroups(except) {
    var any = false;
    groupBtns.forEach(function (b) {
      var open = b === except;
      b.setAttribute("aria-expanded", String(open));
      b.parentNode.classList.toggle("is-open", open);
      if (open) orbit(b.parentNode);
      any = any || open;
    });
    if (header && !(menuBtnOpen())) header.classList.toggle("is-open", any);
  }

  // The open group's sections orbit its title (owner-approved, 1 Nov 2026; site.css has the
  // panel). Above 960px they sit on an ellipse the size of the panel, the first at the top
  // (with two sections, top left and bottom right), and come out of the title over 1.1s as
  // the group opens; the ellipse then turns once every 120s. It stops while the pointer or
  // the focus is on a section, so it is easy to take, and every opening starts from the same
  // places. It runs only while the group is open. Reduced motion: the sections stand still in
  // their places.
  var wideMenu = window.matchMedia("(min-width: 961px)");
  var ORBIT_TURN = 120;
  function orbit(g) {
    var ul = g.querySelector(".nav__links");
    if (!ul || !wideMenu.matches) return;
    var items = Array.prototype.slice.call(ul.children);
    var start = items.length === 2 ? -0.82 * Math.PI : -Math.PI / 2;
    var t = 0, last = 0, t0 = performance.now();
    if (g._orbit) cancelAnimationFrame(g._orbit);
    if (!g._held) {
      g._held = 0;
      items.forEach(function (li) {
        var on = function () { g._held++; }, off = function () { g._held = Math.max(0, g._held - 1); };
        li.addEventListener("pointerenter", on);
        li.addEventListener("pointerleave", off);
        li.addEventListener("focusin", on);
        li.addEventListener("focusout", off);
      });
    }
    function place(now) {
      if (!g.classList.contains("is-open") || !wideMenu.matches) {
        g._orbit = 0;
        items.forEach(function (li) { li.style.transform = ""; li.style.opacity = ""; });
        return;
      }
      var dt = last ? (now - last) / 1000 : 0;
      last = now;
      if (!g._held && !still()) t += dt;
      var k = still() ? 1 : Math.min(1, (now - t0) / 1100);
      k = 1 - Math.pow(1 - k, 3);
      var W = ul.clientWidth, H = ul.clientHeight;
      items.forEach(function (li, i) {
        var w = li.offsetWidth, h = li.offsetHeight;
        var a = start + i * 2 * Math.PI / items.length + t * 2 * Math.PI / ORBIT_TURN;
        var x = W / 2 - w / 2 + Math.cos(a) * (W - w) / 2 * k;
        var y = H / 2 - h / 2 + Math.sin(a) * (H - h) / 2 * k;
        li.style.transform = "translate(" + x.toFixed(1) + "px, " + y.toFixed(1) + "px)";
        li.style.opacity = Math.min(1, k * 1.4).toFixed(3);
      });
      g._orbit = requestAnimationFrame(place);
    }
    place(t0);
  }
  function menuBtnOpen() {
    var m = document.querySelector(".menu-btn");
    return m && m.getAttribute("aria-expanded") === "true";
  }
  if (groupBtns.length) {
    groupBtns.forEach(function (b) {
      b.addEventListener("click", function () {
        closeGroups(b.getAttribute("aria-expanded") === "true" ? null : b);
      });
    });
    document.addEventListener("click", function (e) {
      if (!e.target.closest(".nav__btn") && !e.target.closest(".nav__panel")) closeGroups(null);
      else if (e.target.closest(".nav__panel a")) closeGroups(null);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") return;
      var open = document.querySelector('.nav__btn[aria-expanded="true"]');
      if (open) { closeGroups(null); open.focus(); }
    });
  }

  // Mobile menu.
  var menuBtn = document.querySelector(".menu-btn");
  var nav = document.getElementById("site-nav");
  function setMenu(open) {
    header.classList.toggle("is-open", open);
    menuBtn.setAttribute("aria-expanded", String(open));
    menuBtn.querySelector("span").textContent = open ? "Close" : "Menu";
    menuBtn.querySelector("use").setAttribute("href", open ? "#i-x" : "#i-list");
    if (open) nav.querySelector("a").focus();
  }
  if (menuBtn && nav) {
    menuBtn.addEventListener("click", function () {
      setMenu(menuBtn.getAttribute("aria-expanded") !== "true");
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) setMenu(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && menuBtn.getAttribute("aria-expanded") === "true") {
        setMenu(false);
        menuBtn.focus();
      }
    });
  }

  // Reveal on enter, once.
  var targets = document.querySelectorAll(".reveal, .draw");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-in");
            io.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -12% 0px", threshold: 0.05 }
    );
    targets.forEach(function (el) {
      io.observe(el);
    });
  } else {
    targets.forEach(function (el) {
      el.classList.add("is-in");
    });
  }

  // Signup: front-end only until an email provider is connected.
  var form = document.querySelector(".signup form");
  if (form) {
    var input = form.querySelector("input");
    var status = form.querySelector(".field__status");
    var msg = form.querySelector(".field__msg");
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var value = input.value.trim();
      var ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
      input.setAttribute("aria-invalid", String(!ok));
      status.classList.toggle("is-error", !ok);
      if (!ok) {
        msg.textContent = value
          ? "That email address looks incomplete. Check it and try again."
          : "Enter your email address to subscribe.";
        input.focus();
        return;
      }
      // No newsletter platform yet: nothing is sent or stored.
      msg.textContent = "The newsletter launches soon. Your address was not saved: sign up here again once it opens.";
      form.closest(".signup").classList.add("is-done");
    });
    input.addEventListener("input", function () {
      if (input.getAttribute("aria-invalid") === "true") {
        input.removeAttribute("aria-invalid");
        msg.textContent = "";
        status.classList.remove("is-error");
      }
    });
  }

  // Share a close note: the system share sheet where there is one, else copy
  // the link and swap the label to "Link copied". Hidden without JS, since it
  // cannot work without it.
  var share = document.querySelector(".report__share");
  if (share) {
    var shareBtn = share.querySelector("[data-share]");
    var swap = shareBtn.querySelector(".swap");
    var shareMsg = share.querySelector(".report__share-status");
    var url = location.origin + location.pathname;
    var title = document.querySelector("h1").textContent;
    var swapTimer;
    var say = function (text, quiet) {
      shareMsg.textContent = text;
      shareMsg.classList.toggle("visually-hidden", !!quiet);
    };
    var copied = function () {
      say("Link copied.", true);
      swap.classList.add("is-on");
      clearTimeout(swapTimer);
      swapTimer = setTimeout(function () {
        swap.classList.remove("is-on");
        say("");
      }, 2400);
    };
    share.hidden = false;
    shareBtn.addEventListener("click", function () {
      say("");
      if (navigator.share) {
        navigator.share({ title: title, url: url }).catch(function () {});
      } else if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(url).then(copied, function () {
          say("Copy this link: " + url);
        });
      } else {
        say("Copy this link: " + url);
      }
    });
  }

  // Companies index: filter the table by market and by sector, both at once,
  // and by the search field (assets/profile.js calls andraCoFilter as you type).
  var coChips = document.querySelectorAll(".chip[data-cofilter], .chip[data-comarket]");
  if (coChips.length) {
    var coRows = document.querySelectorAll(".co-tab tbody tr");
    var coStatus = document.querySelector(".co-index__status");
    var coPick = { sector: "all", market: "all" };
    var coQuery = "";
    var coApply = function () {
      var shown = [];
      coRows.forEach(function (row) {
        var on = (coPick.sector === "all" || row.getAttribute("data-sector") === coPick.sector) &&
          (coPick.market === "all" || row.getAttribute("data-market") === coPick.market) &&
          (!coQuery || (row.getAttribute("data-q") || "").indexOf(coQuery) !== -1);
        row.hidden = !on;
        if (on) shown.push(row);
      });
      var names = [];
      ["comarket", "cofilter"].forEach(function (a) {
        var on = document.querySelector('.chip[data-' + a + '][aria-pressed="true"]');
        if (on && on.getAttribute("data-" + a) !== "all") names.push(on.firstChild.textContent.trim());
      });
      if (coQuery) names.push("\u201c" + coQuery + "\u201d");
      coStatus.textContent = names.length
        ? "Showing " + shown.length + " of " + coRows.length + " companies: " + names.join(", ")
        : "Showing all " + coRows.length + " companies";
      return shown;
    };
    window.andraCoFilter = function (q) {
      coQuery = q;
      return coApply();
    };
    coChips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        var kind = chip.hasAttribute("data-comarket") ? "market" : "sector";
        var attr = kind === "market" ? "data-comarket" : "data-cofilter";
        coPick[kind] = chip.getAttribute(attr);
        document.querySelectorAll(".chip[" + attr + "]").forEach(function (c) {
          c.setAttribute("aria-pressed", String(c === chip));
        });
        coApply();
      });
    });
  }

  // Features that are not live yet say so where they are pressed.
  document.querySelectorAll("[data-soon]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var box = btn.closest(".co-acts, .co-gate, .report__share, .lib-lead__acts");
      var out = box && box.querySelector(".co-acts__status, .co-gate__status, .report__share-status");
      if (out) out.textContent = btn.getAttribute("data-soon");
    });
  });

  // Questions: one open at a time (methodology), or any number (.acc--multi,
  // the Interview Prep question bank). Without JS every answer shows.
  document.querySelectorAll(".acc").forEach(function (acc) {
    var multi = acc.classList.contains("acc--multi");
    var accBtns = acc.querySelectorAll(".acc__btn");
    accBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var open = btn.getAttribute("aria-expanded") !== "true";
        accBtns.forEach(function (b) {
          if (multi && b !== btn) return;
          b.setAttribute("aria-expanded", "false");
          b.closest(".acc__item").classList.remove("is-open");
        });
        if (open) {
          btn.setAttribute("aria-expanded", "true");
          btn.closest(".acc__item").classList.add("is-open");
        }
      });
    });
  });

  // Interview Prep: filter the question bank by subject.
  var ipChips = document.querySelectorAll(".chip[data-ipcat]");
  if (ipChips.length) {
    var ipItems = document.querySelectorAll(".acc--multi .acc__item");
    var ipStatus = document.querySelector(".ip__status");
    ipChips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        var cat = chip.getAttribute("data-ipcat");
        var shown = 0;
        ipChips.forEach(function (c) {
          c.setAttribute("aria-pressed", String(c === chip));
        });
        ipItems.forEach(function (item) {
          var on = cat === "all" || item.getAttribute("data-cat") === cat;
          item.hidden = !on;
          if (on) shown++;
        });
        ipStatus.textContent = cat === "all"
          ? "Showing all " + ipItems.length + " questions"
          : "Showing " + shown + " of " + ipItems.length + " questions: " + chip.firstChild.textContent.trim();
      });
    });
  }

  // Research Library: filter the weekly reviews and research by topic and by
  // the search field, both at once. The choice is kept in the address, so a
  // filtered view can be shared. The latest review always stays on top.
  var libInput = document.getElementById("lib-q");
  if (libInput) {
    var libItems = document.querySelectorAll("[data-lib-item]");
    var libChips = document.querySelectorAll(".chip[data-lib-tag]");
    var libStatus = document.querySelector(".lib__status");
    var libEmpty = document.querySelector(".lib__empty");
    var libTag = "all";
    var libPress = function (value) {
      var hit = Array.prototype.some.call(libChips, function (c) {
        return c.getAttribute("data-lib-tag") === value;
      });
      libTag = hit ? value : "all";
      libChips.forEach(function (c) {
        c.setAttribute("aria-pressed", String(c.getAttribute("data-lib-tag") === libTag));
      });
    };
    var libApply = function () {
      var query = libInput.value.trim();
      var words = query.toLowerCase().split(/\s+/).filter(Boolean);
      var shown = 0;
      libItems.forEach(function (item) {
        var q = item.getAttribute("data-q");
        var on = (libTag === "all" || (" " + item.getAttribute("data-tags") + " ").indexOf(" " + libTag + " ") !== -1) &&
          words.every(function (w) {
            return q.indexOf(w) !== -1;
          });
        item.hidden = !on;
        if (on) shown++;
      });
      var names = [];
      var params = new URLSearchParams();
      if (libTag !== "all") {
        params.set("tag", libTag);
        names.push(document.querySelector('.chip[data-lib-tag="' + libTag + '"]').firstChild.textContent.trim());
      }
      if (query) {
        params.set("q", query);
        names.push("\u201c" + query + "\u201d");
      }
      libStatus.textContent = names.length
        ? "Showing " + shown + " of " + libItems.length + " earlier reviews and research: " + names.join(", ")
        : "";
      libEmpty.hidden = !names.length || shown > 0;
      var qs = params.toString();
      history.replaceState(null, "", location.pathname + (qs ? "?" + qs : "") + location.hash);
    };
    libChips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        libPress(chip.getAttribute("data-lib-tag"));
        libApply();
      });
    });
    libInput.addEventListener("input", libApply);
    libInput.form.addEventListener("submit", function (e) {
      e.preventDefault();
    });
    document.querySelector("[data-lib-reset]").addEventListener("click", function () {
      libPress("all");
      libInput.value = "";
      libApply();
      libInput.focus();
    });
    var libStart = new URLSearchParams(location.search);
    if (libStart.get("tag")) libPress(libStart.get("tag"));
    libInput.value = libStart.get("q") || "";
    libApply();
  }

  // Search: dashboards, close notes and pages, from assets/search-index.js
  // (written by tools/build_site.py), loaded the first time search opens.
  var searchBtn = document.querySelector(".search-btn");
  if (searchBtn) {
    var base = document.body.getAttribute("data-base") || "";
    var mac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);
    var kbd = searchBtn.querySelector("kbd");
    if (kbd && !mac) kbd.textContent = "Ctrl K";
    searchBtn.hidden = false;

    var pal = document.createElement("div");
    pal.className = "pal";
    pal.hidden = true;
    pal.innerHTML =
      '<div class="pal__panel" role="dialog" aria-modal="true" aria-label="Search Andra Markets">' +
      '<div class="pal__field"><svg class="icon" aria-hidden="true"><use href="#i-magnifying-glass"/></svg>' +
      '<input id="pal-q" type="text" placeholder="Search companies, dashboards and notes" autocomplete="off" spellcheck="false"' +
      ' role="combobox" aria-expanded="true" aria-controls="pal-list" aria-autocomplete="list" aria-label="Search">' +
      '<button class="pal__esc" type="button">Esc</button></div>' +
      '<ul class="pal__list" id="pal-list" role="listbox" aria-label="Results"><li class="pal__glide" aria-hidden="true"></li></ul>' +
      '<p class="pal__foot" aria-hidden="true"><span>\u2191 \u2193 to move</span><span>Enter to open</span></p></div>';
    document.body.appendChild(pal);
    var q = pal.querySelector("input");
    var list = pal.querySelector(".pal__list");
    var glide = pal.querySelector(".pal__glide");
    var rows = [];
    var active = 0;
    var lastFocus = null;
    var loading = false;

    var GROUPS = ["Companies", "Dashboards", "Close notes", "Reports", "Pages"];
    var score = function (item, query) {
      if (!query) return item.g === "Close notes" || item.g === "Companies" ? 1 : 2;
      var t = item.t.toLowerCase();
      var at = t.indexOf(query);
      if (at === 0) return 6;
      if (at > 0) return 5 - at / 200;
      if ((item.k || "").toLowerCase().indexOf(query) !== -1) return 3;
      // Loose matching (letters in order) only once the query is long enough
      // to mean something, so "oct" finds October notes, not every title.
      if (query.length < 4) return 0;
      var i = 0;
      for (var c = 0; c < t.length && i < query.length; c++) if (t[c] === query[i]) i++;
      return i === query.length ? 1 : 0;
    };
    var render = function () {
      Array.prototype.slice.call(list.children).forEach(function (c) {
        if (c !== glide) list.removeChild(c);
      });
      rows = [];
      var items = window.ANDRA_SEARCH;
      var query = q.value.trim().toLowerCase();
      if (!items) {
        var wait = document.createElement("li");
        wait.className = "pal__empty";
        wait.textContent = "Loading the index.";
        list.appendChild(wait);
        glide.style.height = "0px";
        return;
      }
      var any = false;
      GROUPS.forEach(function (g) {
        var hits = items
          .filter(function (it) {
            return it.g === g;
          })
          .map(function (it, n) {
            return { it: it, s: score(it, query), n: n };
          })
          .filter(function (h) {
            return h.s > 0;
          })
          .sort(function (a, b) {
            return b.s - a.s || a.n - b.n;
          })
          .slice(0, query ? 6 : 4);
        if (!hits.length) return;
        any = true;
        var head = document.createElement("li");
        head.className = "pal__grp";
        head.setAttribute("role", "presentation");
        head.textContent = g;
        list.appendChild(head);
        hits.forEach(function (h) {
          var li = document.createElement("li");
          var idx = rows.length;
          li.className = "pal__row";
          li.id = "pal-opt-" + idx;
          li.setAttribute("role", "option");
          li.setAttribute("data-href", base + h.it.u);
          var b = document.createElement("span");
          b.className = "pal__t";
          b.textContent = h.it.t;
          var m = document.createElement("span");
          m.className = "pal__m";
          m.textContent = h.it.m;
          li.appendChild(b);
          li.appendChild(m);
          li.addEventListener("pointermove", function () {
            if (active !== idx) setActive(idx, false);
          });
          li.addEventListener("click", function () {
            go(idx);
          });
          list.appendChild(li);
          rows.push(li);
        });
      });
      if (!any) {
        var none = document.createElement("li");
        none.className = "pal__empty";
        none.textContent = "Nothing matches \u201c" + q.value.trim() + "\u201d. Try a dashboard, an asset or a date such as 21 Oct.";
        list.appendChild(none);
        glide.style.height = "0px";
        q.removeAttribute("aria-activedescendant");
        return;
      }
      setActive(0, false, true);
    };
    var setActive = function (i, scroll, instant) {
      if (!rows.length) return;
      active = (i + rows.length) % rows.length;
      var row = rows[active];
      rows.forEach(function (r, j) {
        r.setAttribute("aria-selected", String(j === active));
      });
      q.setAttribute("aria-activedescendant", row.id);
      if (instant) glide.style.transition = "none";
      glide.style.height = row.offsetHeight + "px";
      glide.style.transform = "translateY(" + row.offsetTop + "px)";
      if (instant) {
        void glide.offsetWidth;
        glide.style.transition = "";
      }
      if (scroll) row.scrollIntoView({ block: "nearest" });
    };
    var go = function (i) {
      var row = rows[i];
      if (!row) return;
      var href = row.getAttribute("data-href");
      closePal();
      location.href = href;
    };
    var load = function () {
      if (window.ANDRA_SEARCH || loading) return;
      loading = true;
      var tag = document.createElement("script");
      tag.src = base + "assets/search-index.js";
      tag.onload = function () {
        if (!pal.hidden) render();
      };
      tag.onerror = function () {
        loading = false;
        var err = list.querySelector(".pal__empty");
        if (err) err.textContent = "Search could not load. Check your connection and open it again.";
      };
      document.head.appendChild(tag);
    };
    var openPal = function () {
      if (!pal.hidden) return;
      lastFocus = document.activeElement;
      load();
      pal.hidden = false;
      q.value = "";
      root.classList.add("pal-open");
      render();
      requestAnimationFrame(function () {
        pal.classList.add("is-open");
        q.focus();
        if (rows.length) setActive(0, false, true);
      });
    };
    var closePal = function () {
      if (pal.hidden) return;
      pal.classList.remove("is-open");
      root.classList.remove("pal-open");
      setTimeout(function () {
        pal.hidden = true;
        if (lastFocus && lastFocus.focus) lastFocus.focus();
      }, still() ? 0 : 180);
    };
    searchBtn.addEventListener("click", openPal);
    searchBtn.addEventListener("pointerenter", load);
    pal.querySelector(".pal__esc").addEventListener("click", closePal);
    pal.addEventListener("click", function (e) {
      if (e.target === pal) closePal();
    });
    q.addEventListener("input", render);
    document.addEventListener("keydown", function (e) {
      if ((e.metaKey || e.ctrlKey) && !e.altKey && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (pal.hidden) openPal();
        else closePal();
        return;
      }
      if (e.key === "/" && pal.hidden && !/input|textarea|select/i.test(e.target.tagName) && !e.target.isContentEditable) {
        e.preventDefault();
        openPal();
        return;
      }
      if (pal.hidden) return;
      if (e.key === "Escape") {
        e.preventDefault();
        closePal();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setActive(active + 1, true);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActive(active - 1, true);
      } else if (e.key === "Enter") {
        e.preventDefault();
        go(active);
      } else if (e.key === "Tab") {
        e.preventDefault();
        q.focus();
      }
    });
  }
})();
