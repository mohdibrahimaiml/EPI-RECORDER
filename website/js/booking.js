/**
 * Apply EPI_BOOKING URLs to any [data-book="sprint"] anchors.
 * Requires booking-config.js first.
 */
(function () {
  function apply() {
    var cfg = window.EPI_BOOKING || {};
    var sprint = (cfg.sprint || "").trim();
    var mailto = cfg.sprintMailto || "mailto:mohdibrahim@epilabs.org?subject=Agent%20Evidence%20Sprint";
    document.querySelectorAll('[data-book="sprint"]').forEach(function (a) {
      if (sprint) {
        a.setAttribute("href", sprint);
        a.setAttribute("target", "_blank");
        a.setAttribute("rel", "noopener noreferrer");
        if (!a.getAttribute("data-book-label-set")) {
          // Keep visible label; only ensure title hints calendar
          a.setAttribute("title", "Schedule on Cal.com");
        }
      } else {
        a.setAttribute("href", mailto);
        a.removeAttribute("target");
      }
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", apply);
  } else {
    apply();
  }
})();
