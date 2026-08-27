// EPI Auth UI — universal nav auth slot + API wake
(function () {
  'use strict';

  var API_BASE = (function () {
    var h = (location && location.hostname) || '';
    if (h === 'epilabs.org' || h === 'www.epilabs.org' || h.endsWith('.pages.dev')) return '';
    return 'https://epi-verify-portal.onrender.com';
  })();
  var TOKEN_KEY = 'epi_token';
  var USER_KEY = 'epi_user';

  function wakeApi() {
    try {
      fetch(API_BASE + '/api/ping', { mode: 'cors', credentials: 'omit', cache: 'no-store' }).catch(function () {});
      fetch(API_BASE + '/api/auth/status', { mode: 'cors', credentials: 'omit', cache: 'no-store' }).catch(function () {});
    } catch (e) {}
  }
  wakeApi();

  // Account page manages its own dedicated state
  var path = (window.location.pathname || '').replace(/\/$/, '') || '/';
  if (path === '/account' || path.endsWith('/account.html')) return;

  function findNavContainer() {
    return document.getElementById('nav-auth-slot') ||
           document.getElementById('navLinks') ||
           document.querySelector('.nlinks') ||
           document.querySelector('.nav-links') ||
           document.querySelector('nav ul');
  }

  function injectNav(label, isLoggedIn) {
    var slot = document.getElementById('nav-auth-slot');
    if (!slot) {
      var nav = findNavContainer();
      if (nav) {
        // If an existing auth button exists, update it
        var existing = document.getElementById('nav-auth') || nav.querySelector('[data-auth-link]');
        if (existing) {
          existing.textContent = label;
          existing.href = '/account';
          existing.className = isLoggedIn ? 'nav-auth-link' : 'nav-cta';
          existing.setAttribute('data-auth-link', '1');
        } else {
          var li = document.createElement('li');
          li.id = 'nav-auth-slot';
          var a = document.createElement('a');
          a.href = '/account';
          a.id = 'nav-auth';
          a.textContent = label;
          a.className = isLoggedIn ? 'nav-auth-link' : 'nav-cta';
          a.setAttribute('data-auth-link', '1');
          li.appendChild(a);

          // Insert before theme toggle if present, else append
          var tgl = nav.querySelector('.tgl, .theme-toggle-nav');
          if (tgl && tgl.closest('li')) {
            nav.insertBefore(li, tgl.closest('li'));
          } else {
            nav.appendChild(li);
          }
        }
      }
    } else {
      slot.innerHTML = '';
      var a = document.createElement('a');
      a.href = '/account';
      a.id = 'nav-auth';
      a.textContent = label;
      a.className = isLoggedIn ? 'nav-auth-link' : 'nav-cta';
      a.setAttribute('data-auth-link', '1');
      slot.appendChild(a);
    }

    // Mobile menu update
    var mm = document.getElementById('mobMenu') || document.getElementById('mmenu') || document.querySelector('.mmenu');
    if (mm) {
      var mExisting = mm.querySelector('[data-auth-link]') || mm.querySelector('#mob-nav-auth');
      if (mExisting) {
        mExisting.textContent = label;
        mExisting.href = '/account';
        mExisting.className = isLoggedIn ? 'nav-auth-link' : 'nav-cta';
        mExisting.setAttribute('data-auth-link', '1');
      } else {
        var ma = document.createElement('a');
        ma.href = '/account';
        ma.id = 'mob-nav-auth';
        ma.setAttribute('data-auth-link', '1');
        ma.textContent = label;
        ma.className = isLoggedIn ? 'nav-auth-link' : 'nav-cta';
        // Insert before theme toggle if present
        var mtgl = mm.querySelector('.tgl, button');
        if (mtgl) mm.insertBefore(ma, mtgl);
        else mm.appendChild(ma);
      }
    }
  }

  function init() {
    var cached = localStorage.getItem(USER_KEY);
    var token = localStorage.getItem(TOKEN_KEY) || '';
    if (cached) {
      try {
        var user = JSON.parse(cached);
        injectNav(user.login || 'Account', true);
      } catch (e) {
        injectNav('Sign In', false);
      }
    } else {
      injectNav('Sign In', false);
    }

    if (!token && !cached) return;

    fetch(API_BASE + '/api/auth/me', {
      credentials: 'include',
      headers: token ? { Authorization: 'Bearer ' + token } : {},
      cache: 'no-store',
    })
      .then(function (r) {
        if (r.ok) return r.json();
        throw new Error('not logged in');
      })
      .then(function (user) {
        localStorage.setItem(USER_KEY, JSON.stringify(user));
        injectNav(user.login || 'Account', true);
      })
      .catch(function () {
        localStorage.removeItem(USER_KEY);
        if (!token) injectNav('Sign In', false);
        else injectNav('Account', true);
      });
  }

  if (document.readyState !== 'loading') init();
  else document.addEventListener('DOMContentLoaded', init);
})();
