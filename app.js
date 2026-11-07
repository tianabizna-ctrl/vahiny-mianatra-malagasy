/* ============================================================
   Router + chrome. Views live in js/views and register themselves
   on Salama.views; this file only decides which one is on screen.
   ============================================================ */
(function (S) {
  'use strict';

  var core = S.core;
  var ui = S.ui;

  function parseHash() {
    var raw = location.hash.replace(/^#\/?/, '');
    if (!raw) return ['today'];
    return raw.split('/').filter(Boolean);
  }

  function pickView(parts) {
    if (parts[0] === 'reference') {
      var sub = parts[1] || 'phrases';
      return S.views[sub] || S.views.phrases;
    }
    return S.views[parts[0]] || S.views.today;
  }

  function markNav(view) {
    var links = document.querySelectorAll('.appnav a');
    Array.prototype.forEach.call(links, function (link) {
      if (view.nav && link.getAttribute('data-nav') === view.nav) {
        link.setAttribute('aria-current', 'page');
      } else {
        link.removeAttribute('aria-current');
      }
    });
  }

  function render() {
    var parts = parseHash();
    var view = pickView(parts);
    var main = document.getElementById('main');
    var html;

    try {
      html = view.render(parts);
    } catch (error) {
      console.error('[Salama] render failed', error);
      html = '<div class="view-narrow"><h1>This screen could not load</h1>' +
        '<p class="lead">Reloading the page usually fixes it.</p>' +
        '<div class="btn-row"><a class="btn" href="#/today">Back to Today</a></div></div>';
    }

    main.innerHTML = html;
    if (typeof view.mount === 'function') view.mount(main, parts);
    markNav(view);
    window.scrollTo(0, 0);
  }

  /* ---------------- versions ---------------- */
  // One number for the service worker cache, the About panel and the state key.
  // It used to be typed into three files and drifted; sw.js reads the same
  // string from here via data/content.js's meta.version.
  var VERSION = '3.1';

  /* ---------------- header chrome ---------------- */
  var SIZE_LABEL = ['normal', 'large', 'larger'];

  function syncChrome() {
    var pref = core.state.prefs;
    var textBtn = document.getElementById('textSizeBtn');
    if (textBtn) textBtn.textContent = 'Text: ' + SIZE_LABEL[pref.textsize || 0];

    var soundBtn = document.getElementById('soundBtn');
    var soundLabel = document.getElementById('soundLabel');
    if (soundBtn) {
      soundBtn.setAttribute('aria-pressed', pref.autoplay ? 'true' : 'false');
      soundBtn.querySelector('use').setAttribute('href', pref.autoplay ? '#i-volume' : '#i-muted');
    }
    if (soundLabel) soundLabel.textContent = pref.autoplay ? 'Auto-play on' : 'Auto-play off';
  }

  function bindChrome() {
    var textBtn = document.getElementById('textSizeBtn');
    if (textBtn) {
      textBtn.addEventListener('click', function () {
        var next = ((core.state.prefs.textsize || 0) + 1) % 3;
        core.setPref('textsize', next);
        syncChrome();
        ui.toast('Text size: ' + SIZE_LABEL[next]);
      });
    }

    var soundBtn = document.getElementById('soundBtn');
    if (soundBtn) {
      soundBtn.addEventListener('click', function () {
        core.setPref('autoplay', !core.state.prefs.autoplay);
        syncChrome();
        if (!S.speech.ttsAvailable()) {
          ui.toast('This browser has no speech voice; session recordings still play.');
        }
      });
    }

    document.addEventListener('salama:prefs', syncChrome);
  }

  /* ---------------- boot ---------------- */
  function boot() {
    core.applyPrefs();
    core.touchStreak();
    bindChrome();
    syncChrome();

    // Say once, plainly, why a phone can be silent even though the app is not:
    // the iOS silent switch mutes speechSynthesis but not audio elements.
    if (!S.speech.ttsAvailable() && !core.state.prefs.noVoiceNotice) {
      core.setPref('noVoiceNotice', true);
      ui.toast('No speech voice found: recorded audio will still play.');
    }
    window.addEventListener('hashchange', render);
    render();

    if ('serviceWorker' in navigator && location.protocol.indexOf('http') === 0) {
      navigator.serviceWorker.register('sw.js').then(function (registration) {
        if (!registration) console.warn('[Salama] Offline cache unavailable in this browser.');
      }).catch(function (error) {
        // The app works without the cache; it just needs a connection.
        console.warn('[Salama] Offline cache not installed:', error && error.message);
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})(window.Salama);
