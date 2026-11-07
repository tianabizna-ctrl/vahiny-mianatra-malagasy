/* ============================================================
   Speech: recorded clips first, then a Malagasy-aware fallback voice.

   Malagasy has no installed system voice on any current phone or
   desktop. This module therefore does three things, in order:

   1. Plays a rendered Malagasy clip if one exists
      (CONTENT.wordAudio / CONTENT.lineAudio, produced by
      RESEARCH/render_audio.py from the facebook/mms-tts-mlg model).
   2. Otherwise rewrites the word into the spelling of the closest
      installed voice and speaks it syllable by syllable.
   3. Never pretends any of this is a native recording: the UI marks
      generated pronunciations as "approx.".

   The rewrite tables are duplicated in RESEARCH/pronunciation.py
   (ADAPTERS). RESEARCH/check_parity.py fails if the two disagree, so
   change them together.
   ============================================================ */
window.Salama = window.Salama || {};
(function (S) {
  'use strict';

  var synth = 'speechSynthesis' in window ? window.speechSynthesis : null;
  var voices = [];
  var currentAudio = null;
  var currentButton = null;

  /* ---------------- fallback voices, best first ----------------
     Matches VOICE_PRIORITY in pronunciation.py. Romanian is ahead of
     Italian on purpose: it pronounces h, has /ts/ (ț), no nasal vowels,
     and weak final vowels like Malagasy. Spanish is last-but-one because
     its h is silent, which deletes a real Malagasy consonant. */
  var VOICE_PRIORITY = ['mg', 'fr', 'ro', 'it', 'es', 'pt', 'ca', 'en'];

  /* ---------------- adaptation tables (mirror of ADAPTERS) ---------------- */
  var DIPHTHONGS = ['ao', 'ai', 'ay', 'ei', 'ou', 'au', 'oi'];
  var VOWELS = 'aeiouy';
  // Words where a written "ao" spans a syllable boundary (va-o-va-o). Kept in
  // step with HIATUS_AO in pronunciation.py — check_parity.py enforces it.
  var HIATUS_AO = { vaovao: true };

  function isNucleusPair(word, pair) {
    if (DIPHTHONGS.indexOf(pair) === -1) return false;
    if (pair === 'ao' && HIATUS_AO[word]) return false;
    return true;
  }

  var ADAPTERS = {
    fr: { ao: 'ô', oa: 'o-a', ai: 'aï', ay: 'aï', ei: 'é-i', oi: 'o-i',
          ou: 'o-u', au: 'a-ou', j: 'dz', y: 'i', o: 'ou', e: 'é' },
    ro: { ao: 'o', oa: 'o-a', ai: 'ai', ay: 'ai', ei: 'e-i', oi: 'o-i',
          ou: 'o-u', au: 'au', j: 'dz', ts: 'ț', y: 'i', o: 'u', e: 'e' },
    it: { ao: 'ò', oa: 'o-a', ai: 'ai', ay: 'ai', ei: 'e-i', oi: 'o-i',
          ou: 'o-u', au: 'au', j: 'dz', y: 'i', o: 'u', e: 'e' },
    es: { ao: 'o', oa: 'o-a', ai: 'ai', ay: 'ai', ei: 'e-i', oi: 'o-i',
          ou: 'o-u', au: 'au', j: 'dz', y: 'i', o: 'u', e: 'e' },
    ca: { ao: 'o', oa: 'o-a', ai: 'ai', ay: 'ai', ei: 'e-i', oi: 'o-i',
          ou: 'o-u', au: 'au', j: 'tz', ts: 'ts', y: 'i', o: 'u', e: 'e' },
    pt: { ao: 'o', oa: 'o-a', ai: 'ai', ay: 'ai', ei: 'ei', oi: 'oi',
          ou: 'o-u', au: 'au', j: 'dz', ts: 'ts', y: 'i', o: 'u', e: 'ê' },
    en: { ao: 'oh', oa: 'oo-ah', ai: 'eye', ay: 'eye', ei: 'ay-ee', oi: 'oy',
          ou: 'oh', au: 'ow', j: 'dz', y: 'ee', o: 'oo', e: 'eh' }
  };

  /* ---------------- spelling helpers ---------------- */
  function syllabify(word) {
    var syllables = [], current = '', i = 0, w = String(word || '').toLowerCase();
    while (i < w.length) {
      var ch = w[i];
      if (VOWELS.indexOf(ch) !== -1) {
        var nucleus = ch;
        var pair = w.substr(i, 2);
        if (pair.length === 2 && isNucleusPair(w, pair)) {
          nucleus = pair;
          i += 1;
        }
        current += nucleus;
        syllables.push(current);
        current = '';
      } else {
        current += ch;
      }
      i += 1;
    }
    if (current) {
      if (syllables.length) syllables[syllables.length - 1] += current;
      else syllables.push(current);
    }
    // Keep the nasal of a prenasalised cluster with the previous vowel:
    // an-ta-na-na-ri-vo, tron-dro. "ng" is not one of these — it is a velar
    // digraph and stays an onset (ma-nga-tsia-ka, to-nga).
    for (var n = 1; n < syllables.length; n += 1) {
      var m = /^(n|m)(?=[ptkbd]|ts|tr|dr)/.exec(syllables[n]);
      if (m && syllables[n - 1] && VOWELS.indexOf(syllables[n - 1].slice(-1)) !== -1) {
        syllables[n - 1] += m[1];
        syllables[n] = syllables[n].slice(1);
      }
    }
    return syllables.filter(Boolean);
  }

  // Malagasy s is always [s]; French and Italian read one s between vowels as
  // [z] (misaotra -> [miz…]). Double it before adapting.
  function hardenS(word) {
    return word.replace(/([aeiouy])s(?=[aeiouy])/g, '$1ss');
  }

  function applyMap(syllable, table) {
    // Malagasy g is always hard; French/Italian/Portuguese soften it before
    // e, i, y (gidro -> [ʒidʁo]). The silent u has to sit inside the syllable
    // or the hyphenation would split it away.
    if (/^g[eiy]/.test(syllable)) syllable = 'gu' + syllable.slice(1);
    var keys = Object.keys(table).sort(function (a, b) { return b.length - a.length; });
    var out = '', i = 0;
    while (i < syllable.length) {
      var hit = null;
      for (var k = 0; k < keys.length; k += 1) {
        if (syllable.substr(i, keys[k].length) === keys[k]) { hit = keys[k]; break; }
      }
      if (hit) { out += table[hit]; i += hit.length; }
      else { out += syllable[i]; i += 1; }
    }
    return out;
  }

  /**
   * Rewrite Malagasy into the orthography of a fallback voice, one syllable at
   * a time. The hyphens are the point: they stop a French voice turning
   * "an/on/in" into a nasal vowel and swallowing a final -e, which is what
   * made "Antananarivo" unrecognisable. Returns the text unchanged for a real
   * Malagasy voice or an unknown language.
   */
  function adapt(text, lang) {
    if (!text) return text || '';
    var code = String(lang || '').toLowerCase().replace('_', '-').slice(0, 2);
    if (code === 'mg') return text;
    var table = ADAPTERS[code];
    if (!table) return text;
    var pieces = String(text).toLowerCase().split(/([^a-z]+)/);
    return pieces.map(function (piece) {
      if (!piece || !/[a-z]/.test(piece)) return piece;
      var syllables = syllabify(hardenS(piece));
      if (!syllables.length) return piece;
      return syllables.map(function (s) { return applyMap(s, table); }).join('-');
    }).join('');
  }

  /* ---------------- voice selection ---------------- */
  function loadVoices() {
    try { voices = synth ? synth.getVoices() : []; } catch (e) { voices = []; }
  }

  if (synth) {
    loadVoices();
    if (typeof synth.addEventListener === 'function') {
      synth.addEventListener('voiceschanged', loadVoices);
    }
    // Some browsers fill the list late without ever firing the event, which
    // used to make the app claim no voice was installed.
    setTimeout(loadVoices, 400);
    setTimeout(loadVoices, 1500);
  }

  function codeOf(voice) {
    return String((voice && voice.lang) || '').toLowerCase().slice(0, 2);
  }

  function rank(voice) {
    var index = VOICE_PRIORITY.indexOf(codeOf(voice));
    if (index === -1) return 999;
    var name = String(voice.name || '').toLowerCase();
    // Prefer the higher-quality voice when a language has several.
    return index + (/google|natural|neural|premium|enhanced/.test(name) ? -0.5 : 0);
  }

  function prefs() {
    return (S.core && S.core.state && S.core.state.prefs) || {};
  }

  function pickVoice() {
    if (!voices.length) loadVoices();
    var wanted = prefs().voiceURI;
    if (wanted) {
      for (var p = 0; p < voices.length; p += 1) {
        if (voices[p].voiceURI === wanted) return voices[p];
      }
    }
    if (!voices.length) return null;
    var sorted = voices.slice().sort(function (a, b) { return rank(a) - rank(b); });
    return rank(sorted[0]) < 999 ? sorted[0] : null;
  }

  function ttsAvailable() { return Boolean(synth); }

  function stopAll() {
    if (synth) { try { synth.cancel(); } catch (e) { /* ignore */ } }
    if (currentAudio) {
      try { currentAudio.pause(); } catch (e) { /* ignore */ }
      currentAudio = null;
    }
    clearButton();
  }

  /* ---------------- button state ---------------- */
  // Screen readers get told what is happening; sighted users get a pulse.
  function markButton(node) {
    clearButton();
    if (!node || !node.classList) return;
    currentButton = node;
    node.setAttribute('data-speaking', 'true');
  }

  function clearButton() {
    if (currentButton && currentButton.removeAttribute) {
      currentButton.removeAttribute('data-speaking');
    }
    currentButton = null;
  }

  /* ---------------- speaking ---------------- */
  // Chrome stops an utterance after ~15 s and swallows the tail, so long
  // phrases are queued sentence by sentence. No lookbehind in the regex:
  // older iPad Safari (a likely device here) does not support it.
  function chunk(text) {
    var parts = String(text).match(/[^.!?;:]+[.!?;:]*/g) || [String(text)];
    if (parts.length === 1 && String(text).length > 160) {
      parts = String(text).split(/,\s+/);
    }
    return parts.map(function (part) { return part.trim(); }).filter(Boolean);
  }

  function utter(textToSay, voice, rate) {
    var utterance = new SpeechSynthesisUtterance(textToSay);
    if (voice) {
      utterance.voice = voice;
      utterance.lang = voice.lang;
    } else {
      utterance.lang = 'fr-FR';
    }
    utterance.rate = rate;
    utterance.pitch = 1;
    utterance.onend = clearButton;
    utterance.onerror = clearButton;
    synth.speak(utterance);
  }

  /**
   * Speak Malagasy text with the best installed voice.
   * options: { slow, syllables, rate, lang, node, onEnd, onError }
   *   slow      — 0.6 instead of the default rate
   *   syllables — say one syllable at a time with a small gap, so the learner
   *               hears the shape of the word even when the vowels are off
   *   node      — button to mark while speaking
   */
  function speak(text, options) {
    if (!synth || !text) return false;
    var opts = options || {};
    var preference = prefs();
    try {
      if (currentAudio) { currentAudio.pause(); currentAudio = null; }
      synth.cancel();
      var voice = pickVoice();
      var code = opts.lang || (voice ? codeOf(voice) : 'fr');
      var baseRate = Number(opts.rate || preference.rate || 0.82);
      var rate = opts.slow ? Math.max(0.4, baseRate * 0.72) : baseRate;
      var line = adapt(String(text), code);
      var useSyllables = opts.syllables || (preference.syllables && /\s/.test(line) === false);

      markButton(opts.node);
      // Several Android builds drop an utterance queued in the same tick as
      // cancel(); one macrotask of breathing room fixes it.
      setTimeout(function () {
        if (useSyllables) {
          var bits = line.split('-').filter(Boolean);
          bits.forEach(function (bit, index) {
            utter(bit + (index === bits.length - 1 ? '.' : ','), voice, rate * 0.8);
          });
          return;
        }
        var parts = chunk(line);
        parts.forEach(function (part) { utter(part, voice, rate); });
      }, 30);
      return true;
    } catch (e) {
      clearButton();
      if (opts.onError) opts.onError(e);
      return false;
    }
  }

  /* ---------------- recordings ---------------- */
  function recordingsFor() {
    var data = (S.core && S.core.data) || {};
    return {
      words: data.wordAudio || {},
      phrases: data.phraseAudio || {},
      lines: data.lineAudio || {}
    };
  }

  function clipFor(id) {
    if (!id) return null;
    var maps = recordingsFor();
    return maps.words[id] || maps.phrases[id] || null;
  }

  /** Speak one vocabulary entry: rendered clip first, fallback voice second. */
  function speakWord(word, options) {
    if (!word) return false;
    var file = clipFor(word.id);
    if (file) {
      // A real Malagasy recording is better than any synthetic reading, even in
      // syllable mode — so play it, just slower when the learner asked for that.
      var audio = play(file, options);
      if (audio) return true;
    }
    return speak(word.mg, options);
  }

  /** Same, looked up by id — this is what the views pass around. */
  function speakWordId(id, options) {
    var word = S.core && S.core.wordById ? S.core.wordById(id) : null;
    if (word) return speakWord(word, options);
    return false;
  }

  /** One line of a dialogue, by "<dialogueId>#<index>". */
  function speakLine(dialogueId, index, text, options) {
    var maps = recordingsFor();
    var file = maps.lines[dialogueId + '-' + index];
    if (file) {
      var audio = play(file, options);
      if (audio) return true;
    }
    return speak(text, options);
  }

  /** Play a recorded file (mp3). Returns the audio element. */
  function play(url, handlers) {
    var h = handlers || {};
    stopAll();
    var audio = new Audio(url);
    currentAudio = audio;
    markButton(h.node);
    // "Syllables" or the slow rate applied to a recording: keep the authentic
    // pronunciation and stretch the time, instead of switching to a synthetic
    // voice that says the word differently.
    var slow = h.syllables || h.slow;
    if (slow) {
      try { audio.playbackRate = 0.65; } catch (e) { /* older engines */ }
    }
    audio.addEventListener('ended', function () {
      currentAudio = null;
      clearButton();
      if (h.onEnd) h.onEnd();
    });
    audio.addEventListener('error', function () {
      currentAudio = null;
      clearButton();
      if (h.onError) h.onError();
    });
    var attempt = audio.play();
    if (attempt && typeof attempt.catch === 'function') {
      attempt.catch(function () {
        currentAudio = null;
        clearButton();
        if (h.onError) h.onError();
      });
    }
    return audio;
  }

  function isPlaying() { return Boolean(currentAudio) && !currentAudio.paused; }

  /** The voice that will actually be used, for Settings. */
  function voiceReport() {
    var voice = pickVoice();
    if (!voice) {
      return { name: null, lang: null, adapted: true,
               note: 'No speech voice is installed — only recorded clips will play.' };
    }
    var native = codeOf(voice) === 'mg';
    return {
      name: voice.name,
      lang: voice.lang,
      adapted: !native,
      note: native
        ? 'A Malagasy voice is installed, so words are read as written.'
        : 'Words are rewritten for this voice (' + codeOf(voice) + ') and said syllable by syllable.'
    };
  }

  S.speech = {
    speak: speak,
    speakWord: speakWord,
    speakWordId: speakWordId,
    speakLine: speakLine,
    play: play,
    stop: stopAll,
    ttsAvailable: ttsAvailable,
    isPlaying: isPlaying,
    adapt: adapt,
    syllabify: syllabify,
    voiceReport: voiceReport,
    voices: function () { if (!voices.length) loadVoices(); return voices.slice(); },
    voiceName: function () {
      var report = voiceReport();
      return report.name ? report.name + ' (' + report.lang + ')' : null;
    }
  };
})(window.Salama);
