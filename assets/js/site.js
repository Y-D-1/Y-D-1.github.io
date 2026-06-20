(function () {
  "use strict";

  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var finePointer = window.matchMedia("(pointer: fine)").matches;

  function initNav() {
    var toggle = document.querySelector(".nav-toggle");
    var links = document.getElementById("navLinks");
    var navbar = document.querySelector(".navbar");
    if (!links) return;

    if (toggle) {
      toggle.addEventListener("click", function () {
        var open = links.classList.toggle("is-open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });

      links.querySelectorAll("a").forEach(function (link) {
        link.addEventListener("click", function () {
          links.classList.remove("is-open");
          toggle.setAttribute("aria-expanded", "false");
        });
      });
    }

    if (!navbar) return;
    var lastScroll = 0;
    window.addEventListener("scroll", function () {
      var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      if (scrollTop > lastScroll && scrollTop > 80) {
        navbar.classList.add("is-hidden");
      } else {
        navbar.classList.remove("is-hidden");
      }
      lastScroll = scrollTop <= 0 ? 0 : scrollTop;
    }, { passive: true });
  }

  function initCustomCursor() {
    if (reducedMotion || !finePointer) return;

    var ring = document.querySelector(".site-cursor");
    var dot = document.querySelector(".site-cursor-dot");
    if (!ring || !dot) return;

    document.body.classList.add("has-custom-cursor");

    document.addEventListener("mousemove", function (e) {
      ring.style.left = e.clientX + "px";
      ring.style.top = e.clientY + "px";
      dot.style.left = e.clientX + "px";
      dot.style.top = e.clientY + "px";
    });

    document.addEventListener("mouseleave", function () {
      ring.style.opacity = "0";
      dot.style.opacity = "0";
    });

    document.addEventListener("mouseenter", function () {
      ring.style.opacity = "1";
      dot.style.opacity = "1";
    });
  }

  function initTypeWriter() {
    var el = document.getElementById("typedText");
    if (!el || reducedMotion) {
      if (el) el.textContent = "数学之美，在于简洁";
      return;
    }

    var texts = (el.getAttribute("data-texts") || "鱼栋一").split("||");
    var textIndex = 0;
    var charIndex = 0;
    var deleting = false;

    function tick() {
      var current = texts[textIndex] || "";
      if (deleting) {
        charIndex -= 1;
        el.textContent = current.substring(0, charIndex);
        if (charIndex === 0) {
          deleting = false;
          textIndex = (textIndex + 1) % texts.length;
          setTimeout(tick, 400);
          return;
        }
        setTimeout(tick, 35);
        return;
      }

      charIndex += 1;
      el.textContent = current.substring(0, charIndex);
      if (charIndex === current.length) {
        setTimeout(function () {
          deleting = true;
          tick();
        }, 2000);
        return;
      }
      setTimeout(tick, 75);
    }

    tick();
  }

  function initParticles() {
    if (reducedMotion || !document.getElementById("particles-js")) return;

    function boot() {
      if (!window.particlesJS) return;
      window.particlesJS("particles-js", {
        particles: {
          number: { value: 64, density: { enable: true, value_area: 900 } },
          color: { value: ["#00ff88", "#00ccff"] },
          shape: { type: "circle" },
          opacity: { value: 0.45, random: true },
          size: { value: 2.5, random: true },
          line_linked: {
            enable: true,
            distance: 140,
            color: "#00ccff",
            opacity: 0.28,
            width: 1
          },
          move: {
            enable: true,
            speed: 1.8,
            direction: "none",
            out_mode: "out"
          }
        },
        interactivity: {
          detect_on: "window",
          events: {
            onhover: { enable: true, mode: "repulse" },
            onclick: { enable: true, mode: "push" },
            resize: true
          },
          modes: {
            repulse: { distance: 100, duration: 0.35 },
            push: { particles_nb: 3 }
          }
        },
        retina_detect: true
      });
    }

    if (window.particlesJS) {
      boot();
    } else {
      window.addEventListener("load", boot);
    }
  }

  function initScrollReveal() {
    var sections = document.querySelectorAll(".section");
    if (!sections.length || !("IntersectionObserver" in window)) {
      sections.forEach(function (s) { s.classList.add("visible"); });
      return;
    }

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );

    sections.forEach(function (section) {
      observer.observe(section);
    });
  }

  function loadPoetry() {
    var el = document.getElementById("poetry");
    if (!el) return;

    var script = document.createElement("script");
    script.src = "https://sdk.jinrishici.com/v2/browser/jinrishici.js";
    script.onload = function () {
      if (window.jinrishici) {
        window.jinrishici.load(function (result) {
          el.textContent = result.data.content;
        });
      }
    };
    script.onerror = function () {
      el.textContent = "书山有路勤为径，学海无涯苦作舟。";
    };
    document.body.appendChild(script);
  }

  function loadBusuanzi() {
    if (!document.getElementById("busuanzi_value_site_uv")) return;
    var script = document.createElement("script");
    script.src = "//busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js";
    script.async = true;
    document.body.appendChild(script);
  }

  document.addEventListener("DOMContentLoaded", function () {
    initNav();
    initCustomCursor();
    initTypeWriter();
    initParticles();
    initScrollReveal();
    loadPoetry();
    loadBusuanzi();
  });
})();
