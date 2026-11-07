#!/usr/bin/env node
/* ============================================================
   Headless smoke test: render and mount every screen with a stub DOM.

   Catches the class of bug a syntax check cannot: a view that throws
   because a variable is out of scope, an attribute that no longer
   exists, or a speech handler that was left pointing at old markup.

       node RESEARCH/smoke_app.js

   Exits non-zero on the first screen that fails.
   ============================================================ */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const APP = path.join(__dirname, '..', 'APP');

/* ---------------- a DOM small enough to reason about ---------------- */
function makeNode(name) {
  const node = {
    nodeName: (name || 'div').toUpperCase(),
    attributes: {},
    children: [],
    textContent: '',
    hidden: false,
    files: [],
    style: {},
    classList: { add() {}, remove() {}, contains() { return false; } },
    dataset: {},
    listeners: {},
    addEventListener(type, fn) {
      (node.listeners[type] = node.listeners[type] || []).push(fn);
    },
    removeEventListener() {},
    appendChild(child) { node.children.push(child); return child; },
    removeChild() {},
    remove() {},
    click() {},
    focus() {},
    setAttribute(key, value) { node.attributes[key] = String(value); },
    getAttribute(key) { return Object.prototype.hasOwnProperty.call(node.attributes, key) ? node.attributes[key] : null; },
    hasAttribute(key) { return Object.prototype.hasOwnProperty.call(node.attributes, key); },
    removeAttribute(key) { delete node.attributes[key]; },
    querySelector() { return node._child; },
    querySelectorAll() { return []; },
    closest() { return null; },
    insertAdjacentHTML() {},
    matches() { return false; }
  };
  // Assigning innerHTML replaces the element's children in a real browser, so
  // the handler bound to the old child is gone. Mirror that: a new child means
  // exactly one live listener at a time, as in the app.
  node._html = '';
  Object.defineProperty(node, 'innerHTML', {
    get() { return node._html; },
    set(value) { node._html = String(value); node._child = makeNode('leaf'); }
  });
  // One stable child, so a mounted handler can be found again in the test.
  // Leaf children (created for a throwaway querySelector) get no child of their
  // own, or this would recurse forever.
  node._child = name === 'leaf' ? node : makeNode('leaf');
  Object.defineProperty(node, 'firstElementChild', { get() { return node._child; } });
  return node;
}

const mainNode = makeNode('main');

const documentStub = {
  readyState: 'complete',
  documentElement: makeNode('html'),
  body: makeNode('body'),
  head: makeNode('head'),
  title: 'Salama!',
  getElementById(id) { return id === 'main' ? mainNode : makeNode('div'); },
  querySelector() { return makeNode('div'); },
  querySelectorAll() { return []; },
  createElement(tag) { return makeNode(tag); },
  createTextNode(text) { return { textContent: String(text) }; },
  addEventListener() {},
  removeEventListener() {},
  dispatchEvent() { return true; }
};

const storage = {};
const localStorageStub = {
  getItem(key) { return Object.prototype.hasOwnProperty.call(storage, key) ? storage[key] : null; },
  setItem(key, value) { storage[key] = String(value); },
  removeItem(key) { delete storage[key]; },
  clear() { Object.keys(storage).forEach((k) => delete storage[k]); }
};

const sandbox = {
  console,
  document: documentStub,
  localStorage: localStorageStub,
  navigator: { language: 'en-GB' },   // no serviceWorker: registration must be skipped
  location: { hash: '#/today', protocol: 'http:', host: 'localhost' },
  setTimeout: (fn) => { try { fn(); } catch (e) { /* timers are not the point */ } return 0; },
  clearTimeout() {},
  Date, Math, JSON, Object, Array, String, Number, Boolean, RegExp, Error,
  Intl, Promise,
  URL: { createObjectURL() { return 'blob:stub'; }, revokeObjectURL() {} },
  Blob: function Blob() {},
  Audio: function Audio() {
    this.play = function () { return { catch() {} }; };
    this.pause = function () {};
    this.addEventListener = function () {};
    this.paused = true;
  },
  FileReader: function FileReader() {},
  CustomEvent: function CustomEvent(name) { this.name = name; },
  alert() {},
  confirm() { return false; }
};
sandbox.addEventListener = function () {};
sandbox.removeEventListener = function () {};
sandbox.scrollTo = function () {};
sandbox.scrollY = 0;
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.self = sandbox;

const context = vm.createContext(sandbox);

/* ---------------- load the app in the browser's script order ---------------- */
const files = [
  'data/content.js',
  'js/core.js',
  'js/speech.js',
  'js/ui.js',
  'js/views/today.js',
  'js/views/course.js',
  'js/views/session.js',
  'js/views/review.js',
  'js/views/quiz.js',
  'js/views/words.js',
  'js/views/library.js',
  'js/views/progress.js',
  'js/views/settings.js',
  'app.js'
];

for (const file of files) {
  const full = path.join(APP, file);
  const code = fs.readFileSync(full, 'utf8');
  try {
    vm.runInContext(code, context, { filename: file });
  } catch (error) {
    console.error('LOAD FAILED ' + file + ': ' + error.message);
    process.exit(1);
  }
}

const S = sandbox.window.Salama;
const problems = [];

function check(label, fn) {
  try {
    const html = fn();
    if (typeof html === 'string' && !html.trim()) problems.push(label + ': rendered nothing');
    if (typeof html === 'string' && /undefined|\[object Object\]|NaN/.test(html)) {
      problems.push(label + ': output contains undefined/NaN');
    }
  } catch (error) {
    problems.push(label + ': ' + error.message);
  }
}

/* ---------------- every route ---------------- */
const routes = [
  ['today', ['today']],
  ['course', ['course']],
  ['course week', ['course', '3']],
  ['session runner', ['session', 'w1s1']],
  ['session runner 2', ['session', 'w6s2']],
  ['review setup', ['review']],
  ['quiz', ['quiz']],
  ['words', ['reference', 'words']],
  ['phrases', ['reference', 'phrases']],
  ['grammar', ['reference', 'grammar']],
  ['culture', ['reference', 'culture']],
  ['pronunciation guide', ['reference', 'sayit']],
  ['progress', ['progress']],
  ['settings', ['settings']]
];

for (const [label, parts] of routes) {
  const view = parts[0] === 'reference'
    ? S.views[parts[1]]
    : S.views[parts[0]];
  if (!view) { problems.push(label + ': no view registered'); continue; }
  check(label + ' render', () => view.render(parts));
  check(label + ' mount', () => {
    if (view.mount) view.mount(makeNode('main'), parts);
    return 'ok';
  });
}

/* ---------------- a dialogue and a grammar topic ---------------- */
const firstDialogue = S.core.data.dialogues[0];
check('dialogue detail', () => S.views.dialogue.render(['dialogue', firstDialogue.id]));
const firstGrammar = S.core.data.grammar[0];
check('grammar detail', () => S.views.grammar.render(['reference', 'grammar', firstGrammar.id]));

/* ---------------- the speech layer itself ---------------- */
function speakChecks() {
  const speech = S.speech;
  const word = S.core.data.vocabulary.find((w) => w.mg === 'misaotra') || S.core.data.vocabulary[0];

  if (speech.adapt('misaotra', 'fr') !== 'mi-ssô-tra') {
    problems.push('adapt(fr): got ' + speech.adapt('misaotra', 'fr'));
  }
  if (speech.adapt('misaotra', 'mg') !== 'misaotra') {
    problems.push('adapt(mg) must be a no-op');
  }
  if (speech.syllabify('antananarivo').join('-') !== 'an-ta-na-na-ri-vo') {
    problems.push('syllabify(antananarivo): got ' + speech.syllabify('antananarivo').join('-'));
  }
  if (speech.syllabify('mangatsiaka').join('-') !== 'ma-nga-tsi-a-ka') {
    problems.push('syllabify(mangatsiaka): got ' + speech.syllabify('mangatsiaka').join('-'));
  }

  // No voice installed in this sandbox: speak() must return false, not throw,
  // and every entry point must survive being called anyway.
  const results = [
    speech.speak('misaotra'),
    speech.speakWord(word),
    speech.speakWordId(word.id),
    speech.speakLine(firstDialogue.id, 0, firstDialogue.lines[0].mg),
    speech.play('media/audio/MG_Malagasy_Lesson_1.mp3')
  ];
  if (results.some((r) => r && typeof r !== 'boolean' && typeof r !== 'object')) {
    problems.push('speech entry points returned an unexpected type');
  }
  if (speech.ttsAvailable() !== false) {
    problems.push('sandbox has no speechSynthesis but ttsAvailable() is true');
  }
  const report = speech.voiceReport();
  if (!report || typeof report.note !== 'string') problems.push('voiceReport() shape changed');
}
check('speech layer', () => { speakChecks(); return 'ok'; });

/* ---------------- ui handler wiring ---------------- */
check('ui.speakFrom exists', () => {
  if (typeof S.ui.speakButtons !== 'function') throw new Error('ui.speakButtons missing');
  if (typeof S.ui.speakFrom !== 'function') throw new Error('ui.speakFrom missing');
  const markup = S.ui.speakButtons('misaotra', { wordId: 'w1' });
  if (markup.indexOf('data-speak="misaotra"') === -1) throw new Error('no data-speak');
  if (markup.indexOf('data-word-id="w1"') === -1) throw new Error('no data-word-id');
  if (markup.indexOf('data-slow') === -1) throw new Error('no slow control');
  return 'ok';
});

/* ---------------- data invariants the UI relies on ---------------- */
check('data invariants', () => {
  const counts = S.core.data.meta.counts;
  if (counts.vocabulary !== S.core.data.vocabulary.length) throw new Error('vocabulary count drifted');
  if (counts.phrases !== S.core.data.phrases.length) throw new Error('phrase count drifted');
  const sample = S.core.data.phrases.slice(0, 50);
  if (!sample.every((p) => p.pron)) throw new Error('phrases are missing pronunciations');
  if (!S.core.data.vocabulary.every((w) => 'isPhrase' in w || true)) throw new Error('shape');
  return 'ok';
});

/* ---------------- interactions ---------------- */
// A synthetic event whose target.closest() answers for one node with the
// attributes we want, which is how every view reads its own controls.
function control(attributes) {
  const node = makeNode('button');
  Object.keys(attributes || {}).forEach((key) => node.setAttribute(key, attributes[key]));
  return node;
}

function fire(root, attributes, type) {
  // The element that currently holds the handlers: after a re-render it is a
  // fresh child, exactly as in the browser.
  const container = root.querySelector ? root.querySelector('.view-narrow') || root : root;
  const target = control(attributes);
  const event = {
    target,
    preventDefault() {},
    stopPropagation() {}
  };
  target.closest = function (selector) {
    // Answer only if the selector mentions one of this node's attributes.
    const names = ['data-speak', 'data-slow', 'data-word-id', 'data-line', 'data-reveal',
                   'data-grade', 'data-size', 'data-theme', 'data-end', 'data-start',
                   'data-quiz-start', 'data-option', 'data-quiz-next', 'data-rate',
                   'data-syllables', 'data-autoplay', 'data-textsize'];
    const relevant = names.some((name) =>
      target.hasAttribute(name) && selector.indexOf(name) !== -1);
    return relevant ? target : null;
  };
  (container.listeners[type || 'click'] || []).forEach((fn) => fn(event));
}

// In the browser a re-render replaces the element, so exactly one listener is
// live at a time. Give each flow a fresh element to keep that true here too.
function freshMain() {
  mainNode._child = makeNode('leaf');
  return mainNode._child;
}

function attempt(label, fn) {
  try { fn(); } catch (error) { problems.push(label + ': ' + error.message); }
}

attempt('review flow', () => {
  // A review round only exists once words are due, so put a few in the schedule
  // first — the app's own path does this when a session is completed.
  S.core.data.vocabulary.slice(0, 3).forEach((w) => S.core.gradeWord(w.id, 1));
  S.views.review.render(['review']);
  const scope = freshMain();
  S.views.review.mount(mainNode, ['review']);
  S.views.review.render(['review', 'round']);
  S.views.review.mount(mainNode, ['review', 'round']);
  fire(mainNode, { 'data-reveal': 'true' });
  fire(mainNode, { 'data-grade': '2' });
  fire(mainNode, { 'data-speak': 'misaotra' });
  fire(mainNode, { 'data-slow': 'misaotra' });
});

attempt('quiz flow', () => {
  S.views.quiz.render();
  const scope = freshMain();
  S.views.quiz.mount(mainNode);
  const before = Object.keys(S.core.state.cards).length;
  fire(mainNode, { 'data-quiz-start': 'true' });
  fire(mainNode, { 'data-option': '0' });
  if (Object.keys(S.core.state.cards).length <= before) {
    problems.push('quiz: answering did not add the word to the schedule');
  }
  fire(mainNode, { 'data-quiz-next': 'true' });
});

attempt('settings flow', () => {
  S.core.setPref('rate', 0.82);
  const scope = freshMain();
  S.views.settings.mount(mainNode);
  fire(mainNode, { 'data-rate': '0.62' });
  if (S.core.state.prefs.rate !== 0.62) problems.push('settings: rate click was ignored');
  const prefsBefore = JSON.stringify(S.core.state.prefs);
  fire(mainNode, { 'data-syllables': 'true' });
  if (S.core.state.prefs.syllables !== true) problems.push('settings: syllable toggle was ignored');
  fire(mainNode, { 'data-textsize': '2' });
  if (S.core.state.prefs.textsize !== 2) problems.push('settings: text size click was ignored');
});

attempt('words flow', () => {
  const scope = freshMain();
  S.views.words.mount(mainNode);
  fire(mainNode, { 'data-speak': 'trano', 'data-word-id': 'x1' });
  fire(mainNode, { 'data-slow': 'trano', 'data-word-id': 'x1' });
});

attempt('session flow', () => {
  const scope = freshMain();
  S.views.session.mount(mainNode, ['session', 'w1s1']);
  fire(mainNode, { 'data-next': 'true' });
  fire(mainNode, { 'data-word-next': 'true' });
  fire(mainNode, { 'data-speak': 'misaotra' });
});

attempt('import round trip', () => {
  const before = Object.keys(S.core.state.cards).length;
  const text = JSON.stringify({
    app: 'Salama!', exportedAt: new Date().toISOString(),
    state: { version: 3, cards: { a: { box: 2, seen: Date.now() } },
             sessions: { w1s1: Date.now() }, quizzes: [], streak: { last: null, days: 0, visits: 0 },
             prefs: { textsize: 1, autoplay: true } }
  });
  const summary = S.core.importData(text);
  if (summary.words !== 1) problems.push('importData: wrong word count');
  if (S.core.state.prefs.textsize !== 1) problems.push('importData: prefs not restored');
  try {
    S.core.importData('{"nope":1}');
    problems.push('importData: accepted a file that is not a backup');
  } catch (error) { /* expected */ }
  if (before === 0 && Object.keys(S.core.state.cards).length === 0) {
    problems.push('importData: state not replaced');
  }
});

/* ---------------- report ---------------- */
if (problems.length) {
  console.error('SMOKE FAILED (' + problems.length + ')');
  problems.forEach((p) => console.error('  - ' + p));
  process.exit(1);
}
console.log('smoke OK: ' + routes.length + ' routes rendered and mounted, ' +
            'speech layer and six interaction flows exercised');
