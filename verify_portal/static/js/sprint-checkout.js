/* Sprint checkout trigger: any [data-sprint-checkout] button opens the Paddle
   overlay for the one-time $1,500 sprint, using the shared paddle config. */
(function () {
  "use strict";
  var CFG = window.EPI_PADDLE_CONFIG;
  if (!CFG || !CFG.clientToken || !CFG.sprintPriceId) return; // fail silently; buttons remain links

  var paddle = null;

  function openSprint() {
    if (!paddle) return;
    var opts = {
      items: [{ priceId: CFG.sprintPriceId, quantity: 1 }],
      settings: {
        displayMode: "overlay",
        variant: "one-page",
        theme: document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light",
        successUrl: location.origin + (CFG.successUrl || "/welcome/")
      }
    };
    try {
      var email = localStorage.getItem(CFG.emailStorageKey || "epi-user-email");
      if (email) opts.customer = { email: email };
    } catch (e) {}
    paddle.Checkout.open(opts);
  }

  function boot() {
    // window.Paddle may not exist yet (CDN script async / Rocket Loader).
    // Poll briefly; if it never appears, fall back to the contact form.
    if (!window.Paddle || !window.Paddle.Initialize) {
      if (boot.attempts === undefined) boot.attempts = 0;
      boot.attempts++;
      if (boot.attempts > 40) {
        console.error('[sprint] Paddle.js never loaded - check ad-blocker/shields');
        document.querySelectorAll("[data-sprint-checkout]").forEach(function(el){
          el.disabled = false;
          el.title = "Payment script blocked - using contact form instead";
          el.addEventListener("click", function(e){
            e.preventDefault();
            var c = document.getElementById("contact");
            if (c) c.scrollIntoView({ behavior: "smooth" });
          });
        });
        return;
      }
      setTimeout(boot, 250);
      return;
    }
    // CDN paddle.js: Initialize() is synchronous (returns undefined) — no .then()
    try {
      window.Paddle.Initialize({
        token: CFG.clientToken,
        eventCallback: function (ev) {
          if (ev.name === "checkout.completed") {
            setTimeout(function () { location.href = location.origin + (CFG.successUrl || "/welcome/"); }, 800);
          }
        }
      });
    } catch (err) {
      console.error("Paddle init failed:", err.message);
      return;
    }
    paddle = window.Paddle;
    // Convert buttons into checkout triggers
    document.querySelectorAll("[data-sprint-checkout]").forEach(function (el) {
      if (el.dataset.sprintBound) return;
      el.dataset.sprintBound = "1";
      el.addEventListener("click", function (e) {
        e.preventDefault();
        openSprint();
      });
    });
  }

  if (document.readyState !== "loading") boot();
  else document.addEventListener("DOMContentLoaded", boot);
})();
