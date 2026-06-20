(function () {
  "use strict";

  var STAR_COUNT = 50;
  var REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var REVEAL_SELECTOR = [
    ".exam-course-item",
    ".page__content",
    ".sidebar",
    ".archive",
  ].join(", ");

  function initStarField() {
    var field = document.getElementById("pixelStarField");
    if (!field) return;

    var fragment = document.createDocumentFragment();

    for (var i = 0; i < STAR_COUNT; i++) {
      var star = document.createElement("span");
      var size = Math.random() > 0.5 ? 4 : 2;

      star.className = "pixel-bg-star";
      star.style.left = Math.random() * 100 + "%";
      star.style.top = Math.random() * 100 + "%";
      star.style.width = size + "px";
      star.style.height = size + "px";

      if (!REDUCED_MOTION) {
        star.style.animationDelay = Math.random() * 3 + "s";
        star.style.animationDuration = 1.5 + Math.random() * 2 + "s";
      }

      fragment.appendChild(star);
    }

    field.appendChild(fragment);
  }

  function initScrollReveal() {
    if (REDUCED_MOTION || !("IntersectionObserver" in window)) return;

    var elements = document.querySelectorAll(REVEAL_SELECTOR);
    if (!elements.length) return;

    elements.forEach(function (element) {
      element.classList.add("is-reveal-pending");
    });

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-revealed");
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.08 }
    );

    elements.forEach(function (element) {
      observer.observe(element);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initStarField();
    initScrollReveal();
  });
})();
