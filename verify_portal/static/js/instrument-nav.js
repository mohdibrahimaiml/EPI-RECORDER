/** Shared mobile nav + dark instrument for marketing pages. */
(function () {
  document.documentElement.setAttribute("data-theme", "dark");
  if (document.body) {
    document.body.setAttribute("data-theme", "dark");
    if (!document.body.classList.contains("epi-instrument") && !document.body.classList.contains("v2-home")) {
      document.body.classList.add("epi-instrument");
    }
  }
  var nav = document.getElementById("nav");
  if (nav) {
    window.addEventListener("scroll", function () {
      nav.classList.toggle("scrolled", window.scrollY > 40);
    });
  }
  var mb = document.getElementById("mobBtn");
  var mm = document.getElementById("mobMenu");
  if (!mb || !mm) return;
  mb.addEventListener("click", function () {
    var open = mm.classList.contains("open") || mm.style.display === "block";
    if (open) {
      mm.classList.remove("open");
      mm.style.display = "none";
      mb.classList.remove("open");
      mb.setAttribute("aria-expanded", "false");
      document.body.style.overflow = "";
    } else {
      mm.classList.add("open");
      mm.style.display = "block";
      mb.classList.add("open");
      mb.setAttribute("aria-expanded", "true");
      document.body.style.overflow = "hidden";
    }
  });
  mm.querySelectorAll("a").forEach(function (a) {
    a.addEventListener("click", function () {
      mm.classList.remove("open");
      mm.style.display = "none";
      mb.classList.remove("open");
      mb.setAttribute("aria-expanded", "false");
      document.body.style.overflow = "";
    });
  });
})();
