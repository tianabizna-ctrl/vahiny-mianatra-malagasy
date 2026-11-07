/* Settings: reading comfort, how words are spoken, and the learner's own data. */
(function (S) {
  'use strict';
  var core = S.core;
  var ui = S.ui;
  var speech = S.speech;

  var RATES = [['0.62', 'Slow'], ['0.82', 'Normal'], ['1', 'Brisk']];

  function textSizes() {
    var current = core.state.prefs.textsize || 0;
    return [['0', 'Normal'], ['1', 'Large'], ['2', 'Larger']].map(function (pair) {
      return '<button class="chip" type="button" data-textsize="' + pair[0] + '" aria-pressed="' +
        (String(current) === pair[0] ? 'true' : 'false') + '">' + pair[1] + '</button>';
    }).join('');
  }

  function rateChips() {
    var current = String(core.state.prefs.rate || 0.82);
    return RATES.map(function (pair) {
      return '<button class="chip" type="button" data-rate="' + pair[0] + '" aria-pressed="' +
        (current === pair[0] ? 'true' : 'false') + '">' + pair[1] + '</button>';
    }).join('');
  }

  // Every voice the device offers, closest language first, with the ones the
  // app can actually use at the top. A Malagasy voice, if it ever appears, is
  // listed as such and used automatically.
  function voiceChooser() {
    var voices = speech.voices();
    var report = speech.voiceReport();
    if (!voices.length) {
      return '<p class="setting-note">No speech voices are installed on this device. ' +
        'Recorded audio still plays.</p>';
    }
    var preferred = ['mg', 'fr', 'ro', 'it', 'es', 'pt', 'ca', 'en'];
    var sorted = voices.slice().sort(function (a, b) {
      var ai = preferred.indexOf(String(a.lang).slice(0, 2).toLowerCase());
      var bi = preferred.indexOf(String(b.lang).slice(0, 2).toLowerCase());
      return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
    });
    var current = core.state.prefs.voiceURI || '';
    return '<select id="voiceURI" aria-label="Voice">' +
      '<option value=""' + (current ? '' : ' selected') + '>Automatic — ' +
        ui.esc(report.name || 'none available') + '</option>' +
      sorted.map(function (voice) {
        return '<option value="' + ui.esc(voice.voiceURI) + '"' +
          (current === voice.voiceURI ? ' selected' : '') + '>' +
          ui.esc(voice.name + ' (' + voice.lang + ')') + '</option>';
      }).join('') +
      '</select>';
  }

  function render() {
    var prefs = core.state.prefs;
    var report = speech.voiceReport();
    var counts = core.data.meta && core.data.meta.counts ? core.data.meta.counts : {};
    var clips = (counts.rendered_word_clips || 0) + (counts.rendered_line_clips || 0);
    var version = (core.data.meta && core.data.meta.version) || '';

    return '<div class="view-narrow">' +
      '<h1>Settings</h1>' +

      '<div class="panel">' +
        '<div class="setting">' +
          '<div><div class="k">Text size</div>' +
          '<div class="h">Affects every screen, including flashcards.</div></div>' +
          '<div class="chips" style="margin:0">' + textSizes() + '</div>' +
        '</div>' +
        '<div class="setting">' +
          '<div><div class="k">Speaking speed</div>' +
          '<div class="h">How fast a word or phrase is read aloud.</div></div>' +
          '<div class="chips" style="margin:0">' + rateChips() + '</div>' +
        '</div>' +
        '<div class="setting">' +
          '<div><div class="k">Auto-play pronunciation</div>' +
          '<div class="h">Speaks a word when it appears in a review or a session.</div></div>' +
          '<button class="btn ' + (prefs.autoplay ? '' : 'btn-quiet') + '" type="button" data-autoplay="true" aria-pressed="' +
            (prefs.autoplay ? 'true' : 'false') + '">' + (prefs.autoplay ? 'On' : 'Off') + '</button>' +
        '</div>' +
        '<div class="setting">' +
          '<div><div class="k">Syllable mode for every word</div>' +
          '<div class="h">Says each word one syllable at a time. Easier to imitate, slower to hear.</div></div>' +
          '<button class="btn ' + (prefs.syllables ? '' : 'btn-quiet') + '" type="button" data-syllables="true" aria-pressed="' +
            (prefs.syllables ? 'true' : 'false') + '">' + (prefs.syllables ? 'On' : 'Off') + '</button>' +
        '</div>' +
      '</div>' +

      '<h2>Voice</h2>' +
      '<div class="panel">' +
        '<div class="setting">' +
          '<div><div class="k">Voice used for words</div>' +
          '<div class="h">' + ui.esc(report.note) + '</div></div>' +
          '<div class="setting select">' + voiceChooser() + '</div>' +
        '</div>' +
        '<p class="setting-note">' +
          (clips
            ? clips + ' word and line recordings ship with the app and are played before any voice.'
            : 'No recorded word clips ship with this build yet, so words use the device voice.') +
          ' Session audio is the Peace Corps Malagasy recordings.' +
        '</p>' +
        '<p class="setting-note">On an iPhone or iPad the side switch silences the device voice ' +
          'but not recorded audio. If a word is silent and a lesson recording is not, check that switch.</p>' +
        '<div class="btn-row" style="margin-top:12px">' +
          '<button class="btn btn-secondary" type="button" data-test-voice="true">' +
            ui.icon('volume') + 'Hear a sample</button>' +
        '</div>' +
      '</div>' +

      '<h2>Your data</h2>' +
      '<div class="panel">' +
        '<p>Progress is stored in this browser only — ' +
          ui.plural(core.sessionDoneCount(), 'session') + ', ' +
          ui.plural(Object.keys(core.state.cards).length, 'word') + ' and ' +
          ui.plural(core.state.quizzes.length, 'quiz', 'quizzes') + '.</p>' +
        '<div class="btn-row">' +
          '<button class="btn btn-secondary" type="button" data-export="true">' +
            ui.icon('download') + 'Export progress</button>' +
          '<label class="btn btn-secondary" for="importFile">' +
            ui.icon('download') + 'Restore from file</label>' +
          '<input type="file" id="importFile" accept="application/json,.json" hidden>' +
          '<button class="btn btn-danger" type="button" data-reset="true">' +
            ui.icon('trash') + 'Reset everything</button>' +
        '</div>' +
        '<p class="meta" id="resetNote" hidden>Tap reset once more to erase all progress on this device.</p>' +
      '</div>' +

      '<h2>About</h2>' +
      '<div class="panel">' +
        '<p><strong>Salama!</strong> — part of the Vahiny Mianatra Malagasy project. 12 weeks, 36 sessions, ' +
          core.data.vocabulary.length + ' dictionary entries, ' + core.data.phrases.length + ' phrases and ' +
          core.data.dialogues.length + ' dialogues. Version ' + ui.esc(version) + '.</p>' +
        (clips ? '<p class="meta">Word audio is synthesised with Meta\'s MMS Malagasy voice ' +
          '(facebook/mms-tts-mlg, CC BY-NC 4.0).</p>' : '') +
        '<p class="meta">' + ui.esc(core.data.attribution.note) + '</p>' +
      '</div>' +
      '</div>';
  }

  function mount(root) {
    var scope = root.querySelector('.view-narrow') || root;
    var resetArmed = false;

    scope.addEventListener('change', function (event) {
      if (event.target.id === 'voiceURI') {
        core.setPref('voiceURI', event.target.value);
        ui.toast(event.target.value ? 'Voice changed.' : 'Using the automatic voice.');
        rerender();
      }
      if (event.target.id === 'importFile') {
        var file = event.target.files && event.target.files[0];
        if (!file) return;
        var reader = new FileReader();
        reader.onload = function () {
          try {
            var summary = core.importData(String(reader.result));
            ui.toast('Restored ' + ui.plural(summary.words, 'word') + ' and ' +
              ui.plural(summary.sessions, 'session') + '.');
            rerender();
          } catch (error) {
            ui.toast(error.message || 'That file could not be read.');
          }
        };
        reader.readAsText(file);
      }
    });

    scope.addEventListener('click', function (event) {
      var size = event.target.closest('[data-textsize]');
      if (size) {
        core.setPref('textsize', Number(size.getAttribute('data-textsize')));
        rerender();
        return;
      }
      var rate = event.target.closest('[data-rate]');
      if (rate) {
        core.setPref('rate', Number(rate.getAttribute('data-rate')));
        rerender();
        return;
      }
      if (event.target.closest('[data-autoplay]')) {
        core.setPref('autoplay', !core.state.prefs.autoplay);
        rerender();
        return;
      }
      if (event.target.closest('[data-syllables]')) {
        core.setPref('syllables', !core.state.prefs.syllables);
        rerender();
        return;
      }
      var test = event.target.closest('[data-test-voice]');
      if (test) {
        // A sentence rather than a word: it shows what a roleplay line sounds like.
        speech.speak('Misaotra betsaka, tompoko.', { node: test });
        return;
      }
      if (event.target.closest('[data-export]')) {
        core.exportData();
        ui.toast('Progress file downloaded.');
        return;
      }
      var reset = event.target.closest('[data-reset]');
      if (reset) {
        if (!resetArmed) {
          resetArmed = true;
          var note = scope.querySelector('#resetNote');
          if (note) note.hidden = false;
          reset.textContent = 'Confirm reset';
          return;
        }
        core.resetData();
        ui.toast('Progress reset.');
        rerender();
      }
    });
  }

  function rerender() {
    var main = document.getElementById('main');
    main.innerHTML = render();
    mount(main);
    document.dispatchEvent(new CustomEvent('salama:prefs'));
  }

  S.views = S.views || {};
  S.views.settings = { render: render, mount: mount, nav: 'settings' };
})(window.Salama);
