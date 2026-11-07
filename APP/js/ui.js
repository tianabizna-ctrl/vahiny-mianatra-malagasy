/* ============================================================
   UI helpers: escaping, inline icons, toast, small formatting.
   ============================================================ */
window.Salama = window.Salama || {};
(function (S) {
  'use strict';

  function esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  /** Malagasy text is marked up with its own language so screen readers and
   *  browser speech engines do not read it as English. */
  function mg(value) {
    return '<span lang="mg">' + esc(value) + '</span>';
  }

  function icon(name, cls) {
    return '<svg class="icon ' + (cls || '') + '" aria-hidden="true" focusable="false">' +
      '<use href="#i-' + name + '"></use></svg>';
  }

  function norm(value) {
    return String(value == null ? '' : value)
      .toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  var toastTimer = null;
  function toast(message) {
    var node = document.getElementById('toast');
    if (!node) {
      node = document.createElement('div');
      node.id = 'toast';
      node.className = 'toast';
      node.setAttribute('role', 'status');
      document.body.appendChild(node);
    }
    node.textContent = message;
    node.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { node.hidden = true; }, 2800);
  }

  /** Label for a pronunciation: machine guess, or checked by the reviewer. */
  function pronunciationTag(item) {
    if (!item) return '';
    if (item.pron_verified) {
      return ' <span class="checked" title="Approved by a native speaker">' +
        '\u2713 checked</span>';
    }
    return item.pron_approx ? ' <span class="approx">(approx.)</span>' : '';
  }

  /** "sah-LAH-mah" plus an honest label for generated respellings. */
  function pronunciation(word, options) {
    if (!word || !word.pron) return '';
    var label = pronunciationTag(word);
    var opts = options || {};
    return '<p class="say">' + (opts.prefix || '') + esc(word.pron) + label + '</p>';
  }

  function plural(count, one, many) {
    return count === 1 ? one : (many || one + 's');
  }

  var REFERENCE_TABS = [
    { id: 'phrases', title: 'Phrases & dialogues' },
    { id: 'words', title: 'Words' },
    { id: 'grammar', title: 'Grammar' },
    { id: 'culture', title: 'Culture' },
    { id: 'sayit', title: 'How to say it' }
  ];

  function referenceTabs(active) {
    return '<nav class="tabs" aria-label="Reference">' + REFERENCE_TABS.map(function (tab) {
      return '<a href="#/reference/' + tab.id + '"' +
        (tab.id === active ? ' aria-current="page"' : '') + '>' + tab.title + '</a>';
    }).join('') + '</nav>';
  }

  /* ---------------- speech controls ----------------
     One implementation for all six screens. A button carries:
       data-speak="<malagasy text>"   normal reading
       data-slow="<malagasy text>"    one syllable at a time
       data-word-id="<vocabulary id>" prefer a rendered clip for that word
       data-line="<dialogue id>:<index>" prefer a rendered clip for that line
     speech.js decides clip-vs-voice so no view has to know about files. */
  function speakButtons(text, options) {
    var opts = options || {};
    var extra = (opts.wordId ? ' data-word-id="' + esc(opts.wordId) + '"' : '') +
                (opts.line ? ' data-line="' + esc(opts.line) + '"' : '');
    var label = opts.label || 'Listen';
    return '<button class="icon-btn" type="button" data-speak="' + esc(text) + '"' + extra + '>' +
        icon('volume') + '<span class="visually-hidden">' + esc(label) + '</span></button>' +
      '<button class="icon-btn slow" type="button" data-slow="' + esc(text) + '"' + extra + '>' +
        icon('volume') + '<span>Syllables</span></button>';
  }

  /** True when a rendered clip exists, so the toast is not raised needlessly. */
  function hasClip(node) {
    var speech = S.speech;
    if (!speech || !S.core || !S.core.data) return false;
    var data = S.core.data;
    var wordId = node.getAttribute('data-word-id');
    if (wordId && ((data.wordAudio && data.wordAudio[wordId]) ||
                   (data.phraseAudio && data.phraseAudio[wordId]))) return true;
    var line = String(node.getAttribute('data-line') || '').split(':');
    return line.length === 2 && data.lineAudio && data.lineAudio[line[0] + '-' + line[1]] !== undefined;
  }

  /**
   * Speak whatever a pressed control asks for. Returns true when the event was
   * a speech control, so views can `if (ui.speakFrom(event)) return;`.
   */
  function speakFrom(event) {
    var node = event.target.closest('[data-speak],[data-slow]');
    if (!node) return false;
    var speech = S.speech;
    var slow = node.hasAttribute('data-slow');
    var text = node.getAttribute(slow ? 'data-slow' : 'data-speak');
    var options = { node: node };
    if (slow) { options.syllables = true; options.slow = true; }

    if (!speech.ttsAvailable() && !hasClip(node)) {
      toast('No speech voice is available in this browser.');
      return true;
    }
    var wordId = node.getAttribute('data-word-id');
    if (wordId && !slow) {
      if (speech.speakWordId(wordId, options)) return true;
    }
    var line = String(node.getAttribute('data-line') || '').split(':');
    if (line.length === 2 && !slow) {
      if (speech.speakLine(line[0], Number(line[1]), text, options)) return true;
    }
    speech.speak(text, options);
    return true;
  }

  S.ui = {
    esc: esc,
    mg: mg,
    icon: icon,
    norm: norm,
    toast: toast,
    pronunciation: pronunciation,
    pronunciationTag: pronunciationTag,
    plural: plural,
    referenceTabs: referenceTabs,
    speakButtons: speakButtons,
    speakFrom: speakFrom
  };
})(window.Salama);
