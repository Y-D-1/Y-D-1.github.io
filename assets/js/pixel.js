(function () {
  "use strict";

  var CLOUD_COUNT = 8;
  var REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var REVEAL_SELECTOR = [
    ".exam-course-item",
    ".page__content",
    ".sidebar",
    ".archive",
  ].join(", ");

  function initClouds() {
    var layer = document.getElementById("terraCloudLayer");
    if (!layer) return;

    var fragment = document.createDocumentFragment();

    for (var i = 0; i < CLOUD_COUNT; i++) {
      var cloud = document.createElement("span");
      var width = 48 + Math.floor(Math.random() * 80);
      var height = 16 + Math.floor(Math.random() * 20);
      var top = 5 + Math.random() * 45;

      cloud.className = "terra-cloud";
      cloud.style.width = width + "px";
      cloud.style.height = height + "px";
      cloud.style.top = top + "%";
      cloud.style.left = Math.random() * 100 + "%";
      cloud.style.opacity = String(0.35 + Math.random() * 0.35);

      if (!REDUCED_MOTION) {
        cloud.style.animationDuration = 45 + Math.random() * 55 + "s";
        cloud.style.animationDelay = Math.random() * -60 + "s";
      }

      fragment.appendChild(cloud);
    }

    layer.appendChild(fragment);
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
    initClouds();
    initScrollReveal();
  });
})();
