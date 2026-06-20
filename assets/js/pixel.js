(function () {
  "use strict";

  var REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var REVEAL_SELECTOR = [
    ".exam-course-item",
    ".page__content",
    ".sidebar",
    ".archive",
    ".problem-card",
    ".problems-zone",
  ].join(", ");

  function initCursorGlow() {
    var glow = document.getElementById("cyberCursorGlow");
    if (!glow || REDUCED_MOTION) return;

    var targetX = window.innerWidth / 2;
    var targetY = window.innerHeight / 2;
    var currentX = targetX;
    var currentY = targetY;

    document.addEventListener("mousemove", function (event) {
      targetX = event.clientX;
      targetY = event.clientY;
    });

    function tick() {
      currentX += (targetX - currentX) * 0.12;
      currentY += (targetY - currentY) * 0.12;
      glow.style.transform =
        "translate3d(" + (currentX - 180) + "px," + (currentY - 180) + "px,0)";
      requestAnimationFrame(tick);
    }

    tick();
  }

  function initCardTilt() {
    if (REDUCED_MOTION) return;

    document.addEventListener("mousemove", function (event) {
      var cards = document.querySelectorAll(".cyber-glass-panel, .problem-card");
      cards.forEach(function (card) {
        var rect = card.getBoundingClientRect();
        var cx = rect.left + rect.width / 2;
        var cy = rect.top + rect.height / 2;
        var dx = (event.clientX - cx) / rect.width;
        var dy = (event.clientY - cy) / rect.height;

        if (Math.abs(dx) > 0.8 || Math.abs(dy) > 0.8) {
          card.style.setProperty("--tilt-x", "0deg");
          card.style.setProperty("--tilt-y", "0deg");
          return;
        }

        card.style.setProperty("--tilt-y", dx * 4 + "deg");
        card.style.setProperty("--tilt-x", -dy * 4 + "deg");
      });
    });
  }

  function initScrollReveal() {
    if (REDUCED_MOTION || !("IntersectionObserver" in window)) return;

    var elements = document.querySelectorAll(REVEAL_SELECTOR);
    if (!elements.length) return;

    elements.forEach(function (element, index) {
      element.classList.add("is-reveal-pending");
      element.style.transitionDelay = Math.min(index * 0.05, 0.3) + "s";
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
    initCursorGlow();
    initCardTilt();
    initScrollReveal();
  });
})();
