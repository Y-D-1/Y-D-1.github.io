(function () {
  "use strict";

  var REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var REVEAL_SELECTOR = [
    ".exam-course-item",
    ".page__content",
    ".sidebar",
    ".archive",
  ].join(", ");

  function initMouseTrail() {
    var canvas = document.getElementById("cyberTrailCanvas");
    if (!canvas || REDUCED_MOTION) return;

    var ctx = canvas.getContext("2d");
    if (!ctx) return;

    var points = [];
    var maxPoints = 9;
    var minStep = 14;
    var mouseX = -100;
    var mouseY = -100;
    var lastMove = 0;

    function resize() {
      var dpr = window.devicePixelRatio || 1;
      canvas.width = Math.floor(window.innerWidth * dpr);
      canvas.height = Math.floor(window.innerHeight * dpr);
      canvas.style.width = window.innerWidth + "px";
      canvas.style.height = window.innerHeight + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function dist(a, b) {
      var dx = a.x - b.x;
      var dy = a.y - b.y;
      return Math.sqrt(dx * dx + dy * dy);
    }

    resize();
    window.addEventListener("resize", resize);

    document.addEventListener("mousemove", function (event) {
      mouseX = event.clientX;
      mouseY = event.clientY;
      lastMove = performance.now();

      var next = { x: mouseX, y: mouseY };
      if (!points.length || dist(points[points.length - 1], next) >= minStep) {
        points.push(next);
        if (points.length > maxPoints) {
          points.shift();
        }
      } else {
        points[points.length - 1] = next;
      }
    });

    document.addEventListener("mouseleave", function () {
      mouseX = -100;
      mouseY = -100;
    });

    function draw() {
      var w = window.innerWidth;
      var h = window.innerHeight;
      ctx.clearRect(0, 0, w, h);

      if (performance.now() - lastMove > 120 && points.length > 0) {
        points.shift();
      }

      if (points.length >= 2) {
        var n = points.length;
        for (var i = 1; i < n; i += 1) {
          var t = i / (n - 1);
          var p0 = points[i - 1];
          var p1 = points[i];

          ctx.beginPath();
          ctx.moveTo(p0.x, p0.y);
          ctx.lineTo(p1.x, p1.y);
          ctx.strokeStyle = "rgba(77, 232, 255, " + (0.08 + t * 0.62) + ")";
          ctx.lineWidth = 1 + t * 13;
          ctx.lineCap = "round";
          ctx.lineJoin = "round";
          ctx.stroke();
        }
      }

      if (mouseX >= 0 && mouseY >= 0) {
        var headGlow = ctx.createRadialGradient(mouseX, mouseY, 0, mouseX, mouseY, 36);
        headGlow.addColorStop(0, "rgba(200, 245, 255, 0.75)");
        headGlow.addColorStop(0.35, "rgba(77, 232, 255, 0.45)");
        headGlow.addColorStop(0.7, "rgba(61, 139, 255, 0.12)");
        headGlow.addColorStop(1, "rgba(61, 139, 255, 0)");
        ctx.fillStyle = headGlow;
        ctx.beginPath();
        ctx.arc(mouseX, mouseY, 36, 0, Math.PI * 2);
        ctx.fill();

        var headCore = ctx.createRadialGradient(mouseX, mouseY, 0, mouseX, mouseY, 10);
        headCore.addColorStop(0, "rgba(255, 255, 255, 0.95)");
        headCore.addColorStop(0.5, "rgba(180, 240, 255, 0.7)");
        headCore.addColorStop(1, "rgba(77, 232, 255, 0)");
        ctx.fillStyle = headCore;
        ctx.beginPath();
        ctx.arc(mouseX, mouseY, 10, 0, Math.PI * 2);
        ctx.fill();
      }

      requestAnimationFrame(draw);
    }

    draw();
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
    initMouseTrail();
    initScrollReveal();
  });
})();
