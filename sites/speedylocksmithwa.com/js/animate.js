/* Scroll progress bar: CSS scroll-timeline handles it in modern browsers; this is the fallback. */
(function () {
  var bar = document.querySelector(".progress");
  if (!bar || (window.CSS && CSS.supports && CSS.supports("animation-timeline: scroll()"))) return;
  var ticking = false;
  function update() {
    ticking = false;
    var h = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.transform = "scaleX(" + (h > 0 ? Math.min(1, window.scrollY / h) : 0) + ")";
  }
  window.addEventListener("scroll", function () { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
  update();
})();
/* Site animations, driven by Motion (https://motion.dev) — /js/motion.min.js exposes window.Motion {animate, inView}.
   Rules: no animation when the visitor prefers reduced motion; the hero image (LCP) is never faded;
   elements are only hidden right before they animate, so nothing is invisible without JS. */
(function () {
  var M = window.Motion;
  if (!M || !M.animate || !M.inView) return;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (!("IntersectionObserver" in window)) return;

  var EASE = [0.22, 1, 0.36, 1];
  var reveal = { opacity: [0, 1], transform: ["translateY(18px)", "translateY(0)"] };

  var VH = window.innerHeight || document.documentElement.clientHeight;
  function onScreen(el) { var r = el.getBoundingClientRect(); return r.top < VH && r.bottom > 0; }
  function prep(els) {
    for (var i = 0; i < els.length; i++) {
      if (onScreen(els[i]) && !(els[i].closest && els[i].closest(".hero"))) { els[i].__skip = true; continue; } /* visible at load: show now */
      els[i].style.opacity = "0"; els[i].style.willChange = "opacity, transform";
    }
  }
  function done(el) { el.style.willChange = ""; el.style.opacity = ""; el.style.transform = ""; }
  function run(el, delay, dur) {
    if (el.__skip) return;
    M.animate(el, reveal, { duration: dur || 0.6, delay: delay || 0, easing: EASE }).finished.then(function () { done(el); });
  }

  /* 1. Hero: quick stagger on load (short, so LCP/FCP are not delayed) */
  var hero = document.querySelector(".hero");
  if (hero) {
    var parts = hero.querySelectorAll(".wrap > .badge, .wrap > .bignum, .wrap > .cta-row, .wrap > .crumb"); /* h1 + lede stay visible: they are often the LCP element */
    prep(parts);
    for (var i = 0; i < parts.length; i++) run(parts[i], 0.05 + i * 0.09, 0.55);
    var facts = hero.querySelectorAll(".facts li");
    prep(facts);
    for (var j = 0; j < facts.length; j++) run(facts[j], 0.35 + j * 0.07, 0.45);
  }

  /* 2. Sticky call/text bar slides up */
  var sticky = document.querySelector(".sticky");
  if (sticky) {
    M.animate(sticky, { transform: ["translateY(100%)", "translateY(0)"] }, { duration: 0.5, delay: 0.6, easing: EASE })
      .finished.then(function () { sticky.style.transform = ""; });
  }

  /* 3. Everything below the fold reveals as it scrolls into view */
  function onView(el, cb) {
    M.inView(el, function () { cb(el); }, { margin: "0px 0px -10% 0px" });
  }

  // Section headings + stand-alone blocks
  var singles = document.querySelectorAll("main section:not(.hero) h2, main section:not(.hero) h3, .pimg, .map, .aside, .rev-cta, .lead, .offer, .contact > *, .reveal");
  prep(singles);
  for (var s = 0; s < singles.length; s++) onView(singles[s], function (el) { run(el, 0, 0.55); });

  // Groups: stagger the children
  var groups = [
    ".grid",      // service / product cards (.svc)
    ".revs",      // review cards (.rev)
    ".why",       // why-us list
    ".steps",     // how-it-works
    ".gallery",   // photos
    ".towns",     // service-area links
    ".brands",    // brand / car-make chips
    ".links",     // nearby-area links
    ".prose > ul, .prose > ol:not(.steps)"
  ];
  // FAQ <details> reveal one by one
  var faqs = document.querySelectorAll("main details");
  prep(faqs);
  for (var q = 0; q < faqs.length; q++) (function (el, n) { onView(el, function () { run(el, 0, 0.45); }); })(faqs[q], q);
  for (var g = 0; g < groups.length; g++) {
    var containers = document.querySelectorAll(groups[g]);
    for (var c = 0; c < containers.length; c++) (function (box) {
      var kids = box.children;
      if (!kids.length) return;
      prep(kids);
      onView(box, function () {
        var step = kids.length > 12 ? 0.03 : 0.08;
        for (var k = 0; k < kids.length; k++) run(kids[k], Math.min(k * step, 0.9), 0.5);
      });
    })(containers[c]);
  }

  /* 4. Micro-interactions: cards lift on hover, phone buttons pulse once in view */
  var cards = document.querySelectorAll(".svc, .rev, .gallery figure");
  for (var h = 0; h < cards.length; h++) (function (el) {
    el.addEventListener("mouseenter", function () { M.animate(el, { transform: "translateY(-4px)" }, { duration: 0.25, easing: EASE }); });
    el.addEventListener("mouseleave", function () { M.animate(el, { transform: "translateY(0)" }, { duration: 0.3, easing: EASE }); });
  })(cards[h]);

  var big = document.querySelectorAll(".bignum");
  for (var b = 0; b < big.length; b++) onView(big[b], function (el) {
    M.animate(el, { transform: ["scale(1)", "scale(1.03)", "scale(1)"] }, { duration: 0.9, delay: 0.8, easing: "ease-in-out" });
  });
})();
