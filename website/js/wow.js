/**
 * Visible Magic UI / Aceternity-style interactions (vanilla).
 * Spotlight follows pointer on hero. No React required.
 */
(function () {
  'use strict';
  if (!document.body || !document.body.classList.contains('v2-home')) return;

  var reduce =
    window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var hero = document.querySelector('body.v2-home .hero');
  var spot = document.querySelector('.hero-fx .spotlight');
  if (hero && spot && !reduce) {
    var setSpot = function (clientX, clientY) {
      var r = hero.getBoundingClientRect();
      var x = ((clientX - r.left) / r.width) * 100;
      var y = ((clientY - r.top) / r.height) * 100;
      hero.style.setProperty('--spot-x', x + '%');
      hero.style.setProperty('--spot-y', y + '%');
    };
    hero.addEventListener(
      'pointermove',
      function (e) {
        setSpot(e.clientX, e.clientY);
      },
      { passive: true }
    );
    // default center-top glow
    hero.style.setProperty('--spot-x', '55%');
    hero.style.setProperty('--spot-y', '35%');
  }

  // Mark page as wow-ready (optional debug / future hooks)
  document.documentElement.setAttribute('data-epi-wow', '1');
})();
