(function () {
  "use strict";

  var REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var REVEAL_SELECTOR = [
    ".exam-course-item",
    ".page__content",
    ".sidebar",
    ".archive",
  ].join(", ");

  function initScrollReveal() {
    if (REDUCED_MOTION || !("IntersectionObserver" in window)) return;

    var elements = document.querySelectorAll(REVEAL_SELECTOR);
    if (!elements.length) return;

    elements.forEach(function (element, index) {
      element.classList.add("is-reveal-pending");
      element.style.transitionDelay = Math.min(index * 0.06, 0.36) + "s";
    });

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-revealed");
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.06, rootMargin: "0px 0px -40px 0px" }
    );

    elements.forEach(function (element) {
      observer.observe(element);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initScrollReveal();
  });
})();
