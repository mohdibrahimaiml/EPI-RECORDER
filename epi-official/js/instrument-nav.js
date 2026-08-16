/** Shared body class for instrument marketing pages. Burger is owned by nav.js only. */
(function () {
  if (document.body) {
    if (
      !document.body.classList.contains("epi-instrument") &&
      !document.body.classList.contains("v2-home")
    ) {
      document.body.classList.add("epi-instrument");
    }
  }
  // Intentionally no burger handler — see js/nav.js (prevents double-toggle).
})();
