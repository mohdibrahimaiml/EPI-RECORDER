// EPI site nav — single owner of burger + scroll + mobile theme
(function () {
  function ready(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }

  ready(function () {
    var nav = document.getElementById("nav");
    var btn = document.getElementById("mobBtn");
    var menu = document.getElementById("mobMenu");

    if (nav) {
      var onScroll = function () {
        nav.classList.toggle("scrolled", window.scrollY > 24);
      };
      onScroll();
      window.addEventListener("scroll", onScroll, { passive: true });
    }

    // Theme toggle in drawer (desktop toggle lives in hidden .nav-links)
    if (menu && !menu.querySelector("[data-theme-toggle], .mob-theme-btn")) {
      var themeBtn = document.createElement("button");
      themeBtn.type = "button";
      themeBtn.className = "mob-theme-btn theme-toggle-nav";
      themeBtn.setAttribute("data-theme-toggle", "1");
      themeBtn.setAttribute("aria-label", "Toggle color theme");
      themeBtn.innerHTML = "&#9788; Theme";
      menu.appendChild(themeBtn);
      if (window.EPITheme && typeof window.EPITheme.apply === "function") {
        try {
          var cur = document.documentElement.getAttribute("data-theme") || "dark";
          window.EPITheme.apply(cur);
        } catch (e) {}
      }
    }

    if (!btn || !menu) return;

    // Prevent duplicate listeners (nav.js or instrument-nav)
    if (btn.dataset.epiNavBound === "1") return;
    btn.dataset.epiNavBound = "1";

    function isOpen() {
      return menu.classList.contains("is-open") || menu.classList.contains("open");
    }

    function setOpen(open) {
      menu.classList.toggle("is-open", open);
      menu.classList.toggle("open", open);
      if (open) {
        menu.removeAttribute("hidden");
        menu.style.display = "flex";
        menu.style.pointerEvents = "auto";
      } else {
        menu.style.display = "none";
        menu.style.pointerEvents = "none";
        menu.setAttribute("hidden", "");
      }
      btn.classList.toggle("is-open", open);
      btn.classList.toggle("open", open);
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      btn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      document.body.style.overflow = open ? "hidden" : "";
      document.documentElement.style.overflow = open ? "hidden" : "";
      document.body.classList.toggle("mob-nav-open", open);
    }

    setOpen(false);

    function toggle(e) {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
        if (typeof e.stopImmediatePropagation === "function") e.stopImmediatePropagation();
      }
      setOpen(!isOpen());
    }

    // Capture phase so we win over any leftover instrument-nav handlers
    btn.addEventListener("click", toggle, true);

    menu.addEventListener("click", function (e) {
      var a = e.target && e.target.closest && e.target.closest("a");
      if (a) setOpen(false);
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && isOpen()) setOpen(false);
    });

    window.addEventListener(
      "resize",
      function () {
        if (window.innerWidth > 1100 && isOpen()) setOpen(false);
      },
      { passive: true }
    );

    // Expose for debugging / secondary scripts
    window.EPINav = { setOpen: setOpen, isOpen: isOpen };
  });
})();
