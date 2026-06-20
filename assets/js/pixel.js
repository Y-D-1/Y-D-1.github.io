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
    var maxPoints = 28;
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

    resize();
    window.addEventListener("resize", resize);

    document.addEventListener("mousemove", function (event) {
      mouseX = event.clientX;
      mouseY = event.clientY;
      lastMove = performance.now();
      points.push({ x: mouseX, y: mouseY });
      if (points.length > maxPoints) {
        points.shift();
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

      if (performance.now() - lastMove > 80 && points.length > 0) {
        points.shift();
      }

      if (points.length >= 2) {
        for (var i = 1; i < points.length; i += 1) {
          var t = i / points.length;
          var p0 = points[i - 1];
          var p1 = points[i];

          ctx.beginPath();
          ctx.moveTo(p0.x, p0.y);
          ctx.lineTo(p1.x, p1.y);
          ctx.strokeStyle = "rgba(77, 232, 255, " + t * 0.55 + ")";
          ctx.lineWidth = t * 3.5 + 0.5;
          ctx.lineCap = "round";
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(p1.x, p1.y, t * 2.2 + 0.4, 0, Math.PI * 2);
          ctx.fillStyle = "rgba(139, 200, 255, " + t * 0.35 + ")";
          ctx.fill();
        }
      }

      if (mouseX >= 0 && mouseY >= 0) {
        var glow = ctx.createRadialGradient(mouseX, mouseY, 0, mouseX, mouseY, 52);
        glow.addColorStop(0, "rgba(77, 232, 255, 0.42)");
        glow.addColorStop(0.35, "rgba(61, 139, 255, 0.16)");
        glow.addColorStop(1, "rgba(61, 139, 255, 0)");
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(mouseX, mouseY, 52, 0, Math.PI * 2);
        ctx.fill();

        ctx.beginPath();
        ctx.arc(mouseX, mouseY, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
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
