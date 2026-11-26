/* Portfolio interactions. Everything degrades gracefully without JS. */
(function () {
  "use strict";
  var doc = document.documentElement;
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Theme toggle ---------- */
  var themeBtn = document.querySelector("[data-theme-toggle]");
  function setThemeLabel() {
    if (!themeBtn) return;
    var next = doc.dataset.theme === "dark" ? "light" : "dark";
    themeBtn.setAttribute("aria-label", "Switch to " + next + " theme");
  }
  if (themeBtn) {
    setThemeLabel();
    themeBtn.addEventListener("click", function () {
      doc.dataset.theme = doc.dataset.theme === "dark" ? "light" : "dark";
      try { localStorage.setItem("theme", doc.dataset.theme); } catch (e) {}
      setThemeLabel();
    });
  }

  /* ---------- Header: scrolled state + mobile nav ---------- */
  var header = document.querySelector("[data-header]");
  var navToggle = document.querySelector("[data-nav-toggle]");
  function onScroll() { if (header) header.classList.toggle("is-scrolled", window.scrollY > 8); }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  function closeNav() {
    doc.classList.remove("nav-open");
    if (navToggle) { navToggle.setAttribute("aria-expanded", "false"); navToggle.setAttribute("aria-label", "Open menu"); }
  }
  if (navToggle) {
    navToggle.addEventListener("click", function () {
      var open = !doc.classList.contains("nav-open");
      doc.classList.toggle("nav-open", open);
      navToggle.setAttribute("aria-expanded", String(open));
      navToggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });
    document.querySelectorAll(".site-nav a").forEach(function (a) { a.addEventListener("click", closeNav); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeNav(); });
  }

  /* ---------- Scroll reveal ---------- */
  var reveals = document.querySelectorAll(".reveal");
  if (!reduceMotion && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("is-visible"); io.unobserve(en.target); }
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.06 });
    reveals.forEach(function (el, i) {
      el.style.transitionDelay = Math.min((i % 6) * 60, 300) + "ms";
      io.observe(el);
    });
  } else {
    reveals.forEach(function (el) { el.classList.add("is-visible"); });
  }

  /* ---------- Active section in nav (home page) ---------- */
  var navLinks = document.querySelectorAll("[data-nav]");
  if (navLinks.length && document.body.classList.contains("page-home") && "IntersectionObserver" in window) {
    var map = {};
    navLinks.forEach(function (a) { map[a.dataset.nav] = a; });
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var link = map[en.target.id];
        if (!link) return;
        if (en.isIntersecting) {
          navLinks.forEach(function (a) { a.classList.remove("is-active"); });
          link.classList.add("is-active");
        }
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    Object.keys(map).forEach(function (id) { var s = document.getElementById(id); if (s) spy.observe(s); });
  }

  /* ---------- Work filter ---------- */
  var filterBar = document.querySelector("[data-filters]");
  var grid = document.querySelector("[data-filter-grid]");
  if (filterBar && grid) {
    var status = document.querySelector("[data-filter-status]");
    var buttons = filterBar.querySelectorAll("[data-filter]");
    function apply(key) {
      var shown = 0;
      grid.querySelectorAll(".project-card").forEach(function (card) {
        var match = key === "all" || card.dataset.functions.split(" ").indexOf(key) !== -1;
        card.classList.toggle("is-hidden", !match);
        if (match) { shown++; card.classList.add("is-visible"); }
      });
      buttons.forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.filter === key)); });
      if (status) status.textContent = shown + " project" + (shown === 1 ? "" : "s") + " shown";
      if (history.replaceState) history.replaceState(null, "", key === "all" ? location.pathname : "#" + key);
    }
    buttons.forEach(function (b) { b.addEventListener("click", function () { apply(b.dataset.filter); }); });
    var initial = location.hash.slice(1);
    if (initial && filterBar.querySelector('[data-filter="' + initial + '"]')) apply(initial);
  }

  /* ---------- Lightbox ---------- */
  var dialog = document.querySelector("[data-lightbox-dialog]");
  if (dialog && typeof dialog.showModal === "function") {
    var imgEl = dialog.querySelector("[data-lb-img]");
    var titleEl = dialog.querySelector("[data-lb-title]");
    var countEl = dialog.querySelector("[data-lb-count]");
    var altEl = dialog.querySelector("[data-lb-alt]");
    var prev = dialog.querySelector("[data-lb-prev]");
    var next = dialog.querySelector("[data-lb-next]");
    var state = { slides: [], alts: [], i: 0, opener: null };

    function show(i) {
      var n = state.slides.length;
      state.i = (i + n) % n;
      imgEl.src = state.slides[state.i];
      imgEl.alt = state.alts[state.i] || "";
      altEl.textContent = state.alts[state.i] || "";
      countEl.textContent = n > 1 ? (state.i + 1) + " / " + n : "";
      prev.hidden = next.hidden = n < 2;
      // warm the next image
      if (n > 1) { var pre = new Image(); pre.src = state.slides[(state.i + 1) % n]; }
    }

    document.querySelectorAll("[data-lightbox]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var base = btn.dataset.base || "";
        state.slides = JSON.parse(btn.dataset.slides).map(function (s) { return base + s; });
        state.alts = JSON.parse(btn.dataset.alts || "[]");
        state.opener = btn;
        titleEl.textContent = btn.dataset.title || "";
        show(0);
        dialog.showModal();
        doc.style.overflow = "hidden";
      });
    });

    prev.addEventListener("click", function () { show(state.i - 1); });
    next.addEventListener("click", function () { show(state.i + 1); });
    dialog.querySelector("[data-lb-close]").addEventListener("click", function () { dialog.close(); });
    dialog.addEventListener("close", function () {
      doc.style.overflow = "";
      if (state.opener) state.opener.focus();
    });
    // click on the dark backdrop area (not the image or controls) closes
    dialog.addEventListener("click", function (e) {
      if (e.target === dialog || e.target.classList.contains("lb-stage")) dialog.close();
    });
    dialog.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { e.preventDefault(); show(state.i + 1); }
      if (e.key === "ArrowLeft") { e.preventDefault(); show(state.i - 1); }
    });
    // swipe on touch screens
    var x0 = null;
    dialog.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    dialog.addEventListener("touchend", function (e) {
      if (x0 === null || state.slides.length < 2) return;
      var dx = e.changedTouches[0].clientX - x0;
      if (Math.abs(dx) > 40) show(state.i + (dx < 0 ? 1 : -1));
      x0 = null;
    });
  }

  /* ---------- Print: expand collapsed sections ---------- */
  window.addEventListener("beforeprint", function () {
    document.querySelectorAll("details").forEach(function (d) { d.dataset.wasOpen = d.open; d.open = true; });
    reveals.forEach(function (el) { el.classList.add("is-visible"); });
  });
  window.addEventListener("afterprint", function () {
    document.querySelectorAll("details").forEach(function (d) { d.open = d.dataset.wasOpen === "true"; });
  });
})();
