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

    var cursor = document.querySelector(".site-cursor");
    var dot = document.querySelector(".site-cursor-dot");
    if (!cursor || !dot) return;

    document.body.classList.add("has-custom-cursor");

    var mouseX = window.innerWidth / 2;
    var mouseY = window.innerHeight / 2;
    var ringX = mouseX;
    var ringY = mouseY;
    var dotOffsetX = 0;
    var dotOffsetY = 0;
    var maxDrift = 5;

    document.addEventListener("mousemove", function (e) {
      mouseX = e.clientX;
      mouseY = e.clientY;
    });

    function clampDotOffset(dx, dy) {
      var dist = Math.sqrt(dx * dx + dy * dy);
      if (dist > maxDrift) {
        var ratio = maxDrift / dist;
        return { x: dx * ratio, y: dy * ratio };
      }
      return { x: dx, y: dy };
    }

    function applyCursorPosition() {
      cursor.style.left = ringX + "px";
      cursor.style.top = ringY + "px";

      var scale = document.body.classList.contains("is-cursor-active") ? 0.5 : 1;
      dot.style.transform =
        "translate(calc(-50% + " + dotOffsetX + "px), calc(-50% + " + dotOffsetY + "px)) scale(" + scale + ")";
    }

    function snapCursorToMouse() {
      ringX = mouseX;
      ringY = mouseY;
      dotOffsetX = 0;
      dotOffsetY = 0;
      applyCursorPosition();
    }

    function animateCursor() {
      ringX += (mouseX - ringX) * 0.38;
      ringY += (mouseY - ringY) * 0.38;

      var targetOffsetX = mouseX - ringX;
      var targetOffsetY = mouseY - ringY;
      dotOffsetX += (targetOffsetX - dotOffsetX) * 0.58;
      dotOffsetY += (targetOffsetY - dotOffsetY) * 0.58;

      var offset = clampDotOffset(dotOffsetX, dotOffsetY);
      dotOffsetX = offset.x;
      dotOffsetY = offset.y;

      applyCursorPosition();
      requestAnimationFrame(animateCursor);
    }

    snapCursorToMouse();
    animateCursor();

    if (window.visualViewport) {
      window.visualViewport.addEventListener("resize", snapCursorToMouse);
      window.visualViewport.addEventListener("scroll", snapCursorToMouse);
    }
    window.addEventListener("resize", snapCursorToMouse);

    document.querySelectorAll("a, button, .link-card, .note-card, .social-link").forEach(function (el) {
      el.addEventListener("mouseenter", function () {
        document.body.classList.add("is-cursor-active");
      });
      el.addEventListener("mouseleave", function () {
        document.body.classList.remove("is-cursor-active");
      });
    });

    document.addEventListener("mouseleave", function () {
      cursor.style.opacity = "0";
    });

    document.addEventListener("mouseenter", function () {
      cursor.style.opacity = "1";
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

  function getTheme() {
    return document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
  }

  function particlesConfig(theme) {
    var isLight = theme === "light";
    return {
      particles: {
        number: { value: isLight ? 72 : 64, density: { enable: true, value_area: 900 } },
        color: { value: isLight ? ["#8c959f", "#afb8c1", "#d0d7de"] : ["#00ff88", "#00ccff"] },
        shape: { type: "circle" },
        opacity: { value: isLight ? 0.55 : 0.45, random: true },
        size: { value: isLight ? 2.2 : 2.5, random: true },
        line_linked: {
          enable: true,
          distance: 140,
          color: isLight ? "#afb8c1" : "#00ccff",
          opacity: isLight ? 0.32 : 0.28,
          width: 1
        },
        move: {
          enable: true,
          speed: isLight ? 1.5 : 1.8,
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
          repulse: { distance: isLight ? 90 : 100, duration: 0.35 },
          push: { particles_nb: 3 }
        }
      },
      retina_detect: true
    };
  }

  function ensureParticles(theme) {
    if (reducedMotion || !document.getElementById("particles-js") || !window.particlesJS) return;

    if (!window.pJSDom || !Array.isArray(window.pJSDom) || !window.pJSDom.length || !window.pJSDom[0].pJS) {
      if (!Array.isArray(window.pJSDom)) {
        window.pJSDom = [];
      }
      window.particlesJS("particles-js", particlesConfig(theme));
      return;
    }

    syncParticleTheme(theme);
  }

  function syncParticleTheme(theme) {
    if (!window.pJSDom || !window.pJSDom.length || !window.pJSDom[0].pJS || typeof hexToRgb !== "function") {
      ensureParticles(theme);
      return;
    }

    var pJS = window.pJSDom[0].pJS;
    var config = particlesConfig(theme);
    var colors = config.particles.color.value;

    pJS.particles.color.value = colors;
    pJS.particles.line_linked.color = config.particles.line_linked.color;
    pJS.particles.line_linked.opacity = config.particles.line_linked.opacity;

    for (var i = 0; i < pJS.particles.array.length; i += 1) {
      pJS.particles.array[i].color.rgb = hexToRgb(colors[i % colors.length]);
    }
  }

  function initParticles() {
    if (reducedMotion || !document.getElementById("particles-js")) return;

    function boot() {
      ensureParticles(getTheme());
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

  function initTheme() {
    var root = document.documentElement;
    var toggle = document.querySelector(".theme-toggle");
    var meta = document.getElementById("themeColorMeta");

    function applyTheme(theme, options) {
      var next = theme === "light" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try {
        localStorage.setItem("site-theme", next);
      } catch (error) {
        /* private browsing may block storage */
      }
      if (meta) {
        meta.setAttribute("content", next === "light" ? "#ffffff" : "#0d1117");
      }
      if (toggle) {
        toggle.setAttribute("aria-pressed", next === "light" ? "true" : "false");
      }
      if (options && options.syncParticles) {
        syncParticleTheme(next);
      }
    }

    if (toggle) {
      toggle.addEventListener("click", function () {
        var current = root.getAttribute("data-theme") === "light" ? "light" : "dark";
        applyTheme(current === "light" ? "dark" : "light", { syncParticles: true });
        var links = document.getElementById("navLinks");
        var navToggle = document.querySelector(".nav-toggle");
        if (links) links.classList.remove("is-open");
        if (navToggle) navToggle.setAttribute("aria-expanded", "false");
      });
    }

    applyTheme(root.getAttribute("data-theme") || "dark");
  }

  document.addEventListener("DOMContentLoaded", function () {
    initTheme();
    initNav();
    initCustomCursor();
    initTypeWriter();
    initParticles();
    initScrollReveal();
    loadPoetry();
    loadBusuanzi();
  });
})();
