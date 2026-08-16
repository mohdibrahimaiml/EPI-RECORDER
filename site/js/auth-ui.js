// EPI Auth UI — single nav auth slot + API wake
(function () {
  var API_BASE = (function () {
    var h = (location && location.hostname) || "";
    if (h === "epilabs.org" || h === "www.epilabs.org" || h.endsWith(".pages.dev")) return "";
    return "https://epi-verify-portal.onrender.com";
  })();
  var TOKEN_KEY = "epi_token";
  var USER_KEY = "epi_user";

  function wakeApi() {
    try {
      fetch(API_BASE + "/api/ping", { mode: "cors", credentials: "omit", cache: "no-store" }).catch(function () {});
      fetch(API_BASE + "/api/auth/status", { mode: "cors", credentials: "omit", cache: "no-store" }).catch(function () {});
    } catch (e) {}
  }
  wakeApi();

  // Account page owns its own full auth UI
  var path = (window.location.pathname || "").replace(/\/$/, "") || "/";
  if (path === "/account" || path.endsWith("/account.html")) return;

  function ensureSlot() {
    var slot = document.getElementById("nav-auth-slot");
    if (slot) return slot;
    var navLinks = document.getElementById("navLinks") || document.querySelector(".nav-links");
    if (!navLinks) return null;
    // Remove stray hard-coded Sign in CTAs (keep only our slot)
    navLinks.querySelectorAll("a.nav-link-cta").forEach(function (a) {
      var t = (a.textContent || "").toLowerCase();
      if (t.indexOf("sign") >= 0 && a.getAttribute("href") === "/account") {
        var li = a.closest("li");
        if (li && !li.id) li.remove();
      }
    });
    var li = document.createElement("li");
    li.id = "nav-auth-slot";
    navLinks.appendChild(li);
    return li;
  }

  function injectNav(label, isLoggedIn) {
    var slot = ensureSlot();
    if (!slot) return;
    slot.innerHTML = "";
    var a = document.createElement("a");
    a.href = "/account";
    a.id = "nav-auth";
    a.textContent = label;
    a.className = isLoggedIn ? "nav-auth-link" : "nav-link-cta";
    a.setAttribute("data-auth-link", "1");
    slot.appendChild(a);

    // Mobile menu: update or append one auth link
    var mm = document.getElementById("mobMenu");
    if (mm) {
      var existing = mm.querySelector("[data-auth-link]");
      if (existing) {
        existing.textContent = label;
        existing.href = "/account";
      } else {
        var m = document.createElement("a");
        m.href = "/account";
        m.setAttribute("data-auth-link", "1");
        m.textContent = label;
        if (!isLoggedIn) m.className = "nav-link-cta";
        mm.appendChild(m);
      }
    }
  }

  var cached = localStorage.getItem(USER_KEY);
  var token = localStorage.getItem(TOKEN_KEY) || "";
  if (cached) {
    try {
      var user = JSON.parse(cached);
      injectNav(user.login || "Account", true);
    } catch (e) {
      injectNav("Sign in", false);
    }
  } else {
    injectNav("Sign in", false);
  }

  if (!token && !cached) return;

  fetch(API_BASE + "/api/auth/me", {
    credentials: "include",
    headers: token ? { Authorization: "Bearer " + token } : {},
    cache: "no-store",
  })
    .then(function (r) {
      if (r.ok) return r.json();
      throw new Error("not logged in");
    })
    .then(function (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      injectNav(user.login || "Account", true);
    })
    .catch(function () {
      localStorage.removeItem(USER_KEY);
      if (!token) injectNav("Sign in", false);
      else injectNav("Account", true);
    });
})();
