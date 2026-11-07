/* ============================================================
   Core: stored state, spaced repetition, progress selectors.
   No DOM here — keeps the learning logic testable and separate.
   ============================================================ */
window.Salama = window.Salama || {};
(function (S) {
  'use strict';

  var C = window.CONTENT;
  var KEY = 'salama_state_v3';
  var LEGACY_KEY = 'salama_progress_v1';

  /* ---------------- state ---------------- */
  function blank() {
    return {
      version: 3,
      cards: {},          // wordId -> { box, seen, lastGrade }
      sessions: {},       // sessionId -> timestamp completed
      quizzes: [],        // [{ date, theme, score, total }]
      streak: { last: null, days: 0, visits: 0 },
      prefs: { textsize: 0, autoplay: true, rate: 0.82, syllables: false, voiceURI: '' }
    };
  }

  function readJSON(key) {
    try { return JSON.parse(localStorage.getItem(key) || 'null'); }
    catch (e) { return null; }
  }

  function migrate() {
    var fresh = blank();
    var old = readJSON(LEGACY_KEY);
    if (!old) return fresh;
    // v1 kept words -> { box, seen }, quizzes, weeks and a streak.
    if (old.words) {
      Object.keys(old.words).forEach(function (id) {
        var w = old.words[id] || {};
        fresh.cards[id] = { box: w.box || 0, seen: w.seen || Date.now(), lastGrade: 2 };
      });
    }
    if (Array.isArray(old.quizzes)) fresh.quizzes = old.quizzes.slice(-40);
    if (old.weeks) {
      Object.keys(old.weeks).forEach(function (week) {
        C.sessions.forEach(function (s) {
          if (s.week === Number(week)) fresh.sessions[s.id] = Date.now();
        });
      });
    }
    if (old.streak) {
      fresh.streak = { last: old.streak.last, days: old.streak.days || 0, visits: old.streak.count || 0 };
    }
    try { localStorage.removeItem(LEGACY_KEY); } catch (e) { /* ignore */ }
    return fresh;
  }

  var state = readJSON(KEY) || migrate();
  state.cards = state.cards || {};
  state.sessions = state.sessions || {};
  state.quizzes = state.quizzes || [];
  state.streak = state.streak || { last: null, days: 0, visits: 0 };
  state.prefs = Object.assign(blank().prefs, state.prefs || {});

  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); }
    catch (e) { /* private mode: the session still works, it just won't persist */ }
  }

  /* ---------------- dates ---------------- */
  function dayKey(date) {
    var d = date || new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }

  var WEEKDAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
    'August', 'September', 'October', 'November', 'December'];

  function longDate(date) {
    var d = date || new Date();
    return WEEKDAYS[d.getDay()] + ' ' + d.getDate() + ' ' + MONTHS[d.getMonth()];
  }

  function shortDate(ts) {
    var d = new Date(ts);
    return d.getDate() + ' ' + MONTHS[d.getMonth()].slice(0, 3) + ' ' + d.getFullYear();
  }

  function touchStreak() {
    var today = dayKey();
    if (state.streak.last === today) return;
    var yesterday = dayKey(new Date(Date.now() - 864e5));
    state.streak.days = state.streak.last === yesterday ? (state.streak.days || 0) + 1 : 1;
    state.streak.last = today;
    state.streak.visits = (state.streak.visits || 0) + 1;
    save();
  }

  /* ---------------- spaced repetition ---------------- */
  var INTERVALS = [0, 0, 1, 3, 7, 16, 35]; // days, indexed by box
  var MAX_BOX = 6;

  function dueAt(card) {
    var box = Math.min(Math.max(card.box || 0, 0), 6);
    return (card.seen || 0) + INTERVALS[box] * 864e5;
  }

  function gradeWord(id, grade) {
    var card = state.cards[id] || { box: 0, seen: 0, reps: 0 };
    var box = card.box || 0;
    card.reps = (card.reps || 0) + 1;
    if (grade === 0) {
      box = 0;                                                 // try again soon
    } else if (grade === 1) {
      box = Math.max(box, 1);                                  // getting there: hold
    } else if (card.reps === 1) {
      // First sighting, rated "I knew it": establish the card, do not promote.
      // Rating a brand-new card as known used to jump it a box in the same
      // breath as introducing it, and again from a correct quiz answer, so a
      // word seen once could read as "known" without ever being recalled.
      box = Math.max(box, 1);
    } else {
      box = Math.min(box + 1, MAX_BOX);                        // knew it: promote
    }
    card.box = box;
    card.seen = Date.now();
    card.lastGrade = grade;
    state.cards[id] = card;
    save();
    return card;
  }

  /* ---------------- content selectors ---------------- */
  var byId = {};
  C.vocabulary.forEach(function (w) { byId[w.id] = w; });

  var themeById = {};
  C.themeMap.forEach(function (t) { themeById[t.id] = t; });

  var sessionById = {};
  C.sessions.forEach(function (s) { sessionById[s.id] = s; });

  var dialogueById = {};
  C.dialogues.forEach(function (d) { dialogueById[d.id] = d; });

  var grammarById = {};
  C.grammar.forEach(function (g) { grammarById[g.id] = g; });

  function themeTitle(id) {
    return themeById[id] ? themeById[id].title : String(id || '').replace(/_/g, ' ');
  }

  // Words that make sense as a single review card: no blanks, no essays.
  var studyWords = C.vocabulary.filter(function (w) {
    if (!w.en || !w.mg) return false;
    if (w.en.length > 58) return false;
    if (w.en.indexOf('...') !== -1 || w.mg.indexOf('...') !== -1 || w.mg.indexOf('___') !== -1) return false;
    return true;
  });

  function wordsForTheme(theme) {
    if (!theme || theme === 'all') return studyWords;
    return studyWords.filter(function (w) { return (w.themes || []).indexOf(theme) !== -1; });
  }

  function isDue(card) { return dueAt(card) <= Date.now(); }

  function dueWords(theme) {
    return wordsForTheme(theme).filter(function (w) {
      var card = state.cards[w.id];
      return card && isDue(card);
    }).sort(function (a, b) {
      var ca = state.cards[a.id], cb = state.cards[b.id];
      return (ca.box - cb.box) || (ca.seen - cb.seen);
    });
  }

  function newWords(theme) {
    return wordsForTheme(theme).filter(function (w) { return !state.cards[w.id]; });
  }

  function dueCount() { return dueWords('all').length; }

  function knownCount() {
    return Object.keys(state.cards).filter(function (id) {
      return byId[id] && state.cards[id].box >= 3;
    }).length;
  }

  function learningCount() {
    return Object.keys(state.cards).filter(function (id) {
      return byId[id] && state.cards[id].box < 3;
    }).length;
  }

  function totalCards() { return studyWords.length; }

  function quizAverage() {
    if (!state.quizzes.length) return null;
    var sum = state.quizzes.reduce(function (acc, q) { return acc + q.score / q.total; }, 0);
    return Math.round((sum / state.quizzes.length) * 100);
  }

  /* ---------------- curriculum ---------------- */
  function isSessionDone(id) { return Boolean(state.sessions[id]); }

  function markSession(id) {
    state.sessions[id] = Date.now();
    save();
  }

  function unmarkSession(id) {
    delete state.sessions[id];
    save();
  }

  function nextSession() {
    var pending = C.sessions.filter(function (s) { return !isSessionDone(s.id); });
    return pending.length ? pending[0] : C.sessions[C.sessions.length - 1];
  }

  function sessionDoneCount() {
    return C.sessions.filter(function (s) { return isSessionDone(s.id); }).length;
  }

  function weekDoneCount(week) {
    var list = C.sessions.filter(function (s) { return s.week === week; });
    return list.filter(function (s) { return isSessionDone(s.id); }).length;
  }

  function completedWeeks() {
    return C.curriculum.filter(function (w) {
      return weekDoneCount(w.week) === w.sessions.length;
    }).length;
  }

  /* ---------------- preferences + data ---------------- */
  function setPref(key, value) {
    state.prefs[key] = value;
    save();
    applyPrefs();
  }

  function applyPrefs() {
    document.documentElement.setAttribute('data-textsize', String(state.prefs.textsize || 0));
  }

  function exportData() {
    var payload = {
      app: 'Salama! — Learn Malagasy',
      exportedAt: new Date().toISOString(),
      state: state
    };
    var blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'salama-progress-' + dayKey() + '.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
  }

  /**
   * Restore a file written by exportData(). Accepts both shapes: the wrapped
   * {app, exportedAt, state} and a bare state object. Returns a short summary
   * or throws with a readable reason, so Settings can tell the learner what
   * happened instead of a silent no-op.
   */
  function importData(text) {
    var payload;
    try { payload = JSON.parse(text); }
    catch (e) { throw new Error('That file is not JSON.'); }
    var incoming = payload && payload.state ? payload.state : payload;
    if (!incoming || typeof incoming !== 'object' || !incoming.cards) {
      throw new Error('That file does not look like a Salama! backup.');
    }
    var fresh = blank();
    fresh.cards = incoming.cards || {};
    fresh.sessions = incoming.sessions || {};
    fresh.quizzes = Array.isArray(incoming.quizzes) ? incoming.quizzes.slice(-40) : [];
    fresh.streak = incoming.streak || fresh.streak;
    fresh.prefs = Object.assign(fresh.prefs, incoming.prefs || {});
    Object.keys(state).forEach(function (k) { delete state[k]; });
    Object.keys(fresh).forEach(function (k) { state[k] = fresh[k]; });
    save();
    applyPrefs();
    return {
      sessions: Object.keys(state.sessions).length,
      words: Object.keys(state.cards).length
    };
  }

  function resetData() {
    // Mutate in place so every view holding S.core.state sees the reset.
    var fresh = blank();
    Object.keys(state).forEach(function (k) { delete state[k]; });
    Object.keys(fresh).forEach(function (k) { state[k] = fresh[k]; });
    save();
    applyPrefs();
  }

  S.core = {
    data: C,
    state: state,
    save: save,
    gradeWord: gradeWord,
    dueAt: dueAt,
    dueWords: dueWords,
    newWords: newWords,
    dueCount: dueCount,
    knownCount: knownCount,
    learningCount: learningCount,
    totalCards: totalCards,
    quizAverage: quizAverage,
    wordsForTheme: wordsForTheme,
    themeTitle: themeTitle,
    themeById: themeById,
    wordById: function (id) { return byId[id]; },
    session: function (id) { return sessionById[id]; },
    sessionById: sessionById,
    dialogue: function (id) { return dialogueById[id]; },
    grammar: function (id) { return grammarById[id]; },
    isSessionDone: isSessionDone,
    markSession: markSession,
    unmarkSession: unmarkSession,
    nextSession: nextSession,
    sessionDoneCount: sessionDoneCount,
    weekDoneCount: weekDoneCount,
    completedWeeks: completedWeeks,
    touchStreak: touchStreak,
    longDate: longDate,
    shortDate: shortDate,
    dayKey: dayKey,
    setPref: setPref,
    applyPrefs: applyPrefs,
    exportData: exportData,
    importData: importData,
    resetData: resetData,
    reload: function (nextState) { state = nextState; }
  };
})(window.Salama);
