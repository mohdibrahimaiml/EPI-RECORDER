/**
 * EPI theme — light / dark with localStorage + system default.
 * Sets data-theme on <html> and <body>. Exposes window.EPITheme.
 */
(function () {
  var KEY = "epi-theme";

  function systemPrefersDark() {
    try {
      return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    } catch (e) {
      return true;
    }
  }

  function resolve(theme) {
    if (theme === "light" || theme === "dark") return theme;
    return systemPrefersDark() ? "dark" : "light";
  }

  function apply(theme) {
    var t = resolve(theme);
    document.documentElement.setAttribute("data-theme", t);
    if (document.body) document.body.setAttribute("data-theme", t);
    // Keep instrument pages themed; do not force dark class removal
    document.querySelectorAll(".theme-toggle-nav, #themeToggleNav, [data-theme-toggle]").forEach(function (btn) {
      var dark = t === "dark";
      btn.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
      btn.setAttribute("title", dark ? "Light mode" : "Dark mode");
      // Mobile drawer buttons need a label; icon-only on compact nav
      if (btn.classList.contains("mob-theme-btn") || (btn.closest && btn.closest(".mob-menu"))) {
        btn.innerHTML = dark ? "&#9788; Light mode" : "&#9789; Dark mode";
      } else {
        btn.innerHTML = dark ? "&#9788;" : "&#9789;"; // sun / moon
      }
      btn.setAttribute("aria-pressed", dark ? "true" : "false");
    });
    return t;
  }

  function get() {
    try {
      return localStorage.getItem(KEY) || "";
    } catch (e) {
      return "";
    }
  }

  function set(theme) {
    var t = theme === "light" || theme === "dark" ? theme : resolve(theme);
    try {
      localStorage.setItem(KEY, t);
    } catch (e) {}
    return apply(t);
  }

  function toggle() {
    var cur = document.documentElement.getAttribute("data-theme") || resolve(get());
    return set(cur === "dark" ? "light" : "dark");
  }

  function init() {
    var stored = get();
    apply(stored || (systemPrefersDark() ? "dark" : "light"));
    document.addEventListener("click", function (e) {
      var btn = e.target && e.target.closest && e.target.closest("[data-theme-toggle], .theme-toggle-nav, #themeToggleNav");
      if (btn) {
        e.preventDefault();
        toggle();
      }
    });
    try {
      if (window.matchMedia) {
        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function (ev) {
          if (!get()) apply(ev.matches ? "dark" : "light");
        });
      }
    } catch (e) {}
  }

  window.EPITheme = { init: init, set: set, get: get, toggle: toggle, apply: apply };

  // Run ASAP if body exists; else on DOMContentLoaded
  if (document.body) init();
  else document.addEventListener("DOMContentLoaded", init);
})();
