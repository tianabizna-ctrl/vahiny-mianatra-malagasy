/* Review: a bounded round of due words, reveal first, then rate. */
(function (S) {
  'use strict';
  var core = S.core;
  var ui = S.ui;
  var speech = S.speech;

  var setup = { theme: 'all', size: 10, direction: 'mg' };
  var round = { queue: [], index: 0, revealed: false, results: { 0: 0, 1: 0, 2: 0 }, started: false };

  function dueFor(theme) { return core.dueWords(theme); }

  function themeOptions() {
    var counts = {};
    dueFor('all').forEach(function (w) {
      (w.themes || []).forEach(function (t) { counts[t] = (counts[t] || 0) + 1; });
    });
    return core.data.themeMap.filter(function (t) { return counts[t.id]; })
      .sort(function (a, b) { return counts[b.id] - counts[a.id]; })
      .map(function (t) {
        return '<button class="chip" type="button" data-theme="' + t.id + '" aria-pressed="' +
          (setup.theme === t.id ? 'true' : 'false') + '">' + ui.esc(t.title) + ' (' + counts[t.id] + ')</button>';
      }).join('');
  }

  function setupView() {
    var due = dueFor(setup.theme);
    var size = Math.min(setup.size, due.length);
    if (!due.length) {
      return '<div class="view-narrow">' +
        '<h1>Review</h1>' +
        '<p class="lead">No words are due yet.</p>' +
        '<div class="panel"><p style="margin:0">Words you meet in a session come back here after a day, then after three days, then a week. ' +
        'Open a session to add words.</p>' +
        '<div class="btn-row" style="margin-top:16px"><a class="btn" href="#/course">Course outline</a>' +
        '<a class="btn btn-secondary" href="#/quiz">Practise a quiz</a></div></div>' +
        '</div>';
    }

    var roundCopy;
    if (due.length > size) roundCopy = 'This round covers ' + size + ' of them.';
    else if (due.length === 1) roundCopy = 'One card.';
    else roundCopy = 'All of them fit in one round.';

    return '<div class="view-narrow">' +
      '<h1>Review</h1>' +
      '<p class="lead">' + due.length + ' ' + ui.plural(due.length, 'word') + ' due today. ' +
        roundCopy + '</p>' +

      '<div class="panel">' +
        '<div class="field" style="margin-bottom:16px">' +
          '<label for="reviewDirection">Show first</label>' +
          '<select id="reviewDirection">' +
            '<option value="mg"' + (setup.direction === 'mg' ? ' selected' : '') + '>Malagasy word</option>' +
            '<option value="en"' + (setup.direction === 'en' ? ' selected' : '') + '>English meaning</option>' +
          '</select>' +
        '</div>' +

        '<fieldset style="border:0;padding:0;margin:0 0 16px">' +
          '<legend class="meta" style="margin-bottom:8px">Cards in this round</legend>' +
          '<div class="btn-row">' +
            '<button class="chip" type="button" data-size="10" aria-pressed="' + (setup.size === 10 ? 'true' : 'false') + '">10 cards</button>' +
            '<button class="chip" type="button" data-size="15" aria-pressed="' + (setup.size === 15 ? 'true' : 'false') + '"' +
              (due.length < 15 ? ' disabled' : '') + '>15 cards</button>' +
          '</div>' +
        '</fieldset>' +

        (themeOptions() ? '<p class="meta" style="margin-bottom:8px">Topic</p><div class="chips">' +
          '<button class="chip" type="button" data-theme="all" aria-pressed="' + (setup.theme === 'all' ? 'true' : 'false') + '">All topics</button>' +
          themeOptions() + '</div>' : '') +

        '<div class="btn-row">' +
          '<a class="btn btn-lg" href="#/review/round" data-start="true">Start review' + ui.icon('arrow-right') + '</a>' +
          '<button class="btn btn-quiet" type="button" data-print="true">' + ui.icon('print') + 'Print these cards</button>' +
        '</div>' +
      '</div>' +

      '<div class="print-deck" id="printDeck"></div>' +
      '</div>';
  }

  function startRound() {
    round.queue = dueFor(setup.theme).slice(0, setup.size);
    round.index = 0;
    round.revealed = false;
    round.results = { 0: 0, 1: 0, 2: 0 };
    round.started = true;
    if (!round.queue.length) { location.hash = '#/review'; }
  }

  function roundBar() {
    return '<div class="round-bar" aria-hidden="true">' + round.queue.map(function (_, i) {
      var state = i < round.index ? 'done' : (i === round.index ? 'current' : '');
      return '<span data-state="' + state + '"></span>';
    }).join('') + '</div>';
  }

  function cardView() {
    var word = round.queue[round.index];
    if (!word) return summaryView();
    var prompt = setup.direction === 'mg' ? word.mg : word.en;
    var answer = setup.direction === 'mg' ? word.en : word.mg;
    var alt = (word.alt || []).filter(function (a) { return a; });

    return '<div class="view-narrow">' +
      '<div class="review-head">' +
        '<h1>Review</h1>' +
        '<span class="review-position">Card ' + (round.index + 1) + ' of ' + round.queue.length + '</span>' +
      '</div>' +
      roundBar() +

      '<div class="review-card" style="margin-top:24px">' +
        '<p class="prompt"' + (setup.direction === 'mg' ? ' lang="mg"' : '') + '>' + ui.esc(prompt) + '</p>' +
        (setup.direction === 'mg' && word.pron
          ? '<p class="say">' + ui.esc(word.pron) + ui.pronunciationTag(word) + '</p>'
          : '') +
        ui.speakButtons(word.mg, { wordId: word.id }) +

        (round.revealed
          ? '<div class="answer">' +
              (setup.direction === 'mg'
                ? ui.esc(word.en)
                : '<span lang="mg">' + ui.esc(word.mg) + '</span>' +
                  (word.pron ? '<span class="alt">' + ui.esc(word.pron) + '</span>' : '')) +
              (setup.direction === 'mg' && alt.length ? '<span class="alt">Also: ' + ui.esc(alt.join('; ')) + '</span>' : '') +
            '</div>' +
            (word.note ? '<p class="note">' + ui.esc(word.note) + '</p>' : '')
          : '<button class="btn btn-secondary btn-lg" type="button" data-reveal="true">Show meaning</button>') +
      '</div>' +

      (round.revealed
        ? '<div class="grades">' +
            '<button class="btn btn-quiet" type="button" data-grade="0">Try again soon</button>' +
            '<button class="btn btn-secondary" type="button" data-grade="1">Getting there</button>' +
            '<button class="btn" type="button" data-grade="2">I knew it</button>' +
          '</div>'
        : '') +

      '<div class="btn-row" style="margin-top:20px">' +
        '<button class="btn btn-quiet" type="button" data-end="true">' + ui.icon('close') + 'End review</button>' +
      '</div>' +
      '</div>';
  }

  function summaryView() {
    var total = round.results[0] + round.results[1] + round.results[2];
    var due = core.dueCount();
    return '<div class="view-narrow">' +
      '<h1>Review finished</h1>' +
      '<p class="lead">' + total + ' ' + ui.plural(total, 'card') + ' rated.</p>' +
      '<div class="summary-grid">' +
        '<div><span class="n">' + round.results[2] + '</span><span class="k">Knew it</span></div>' +
        '<div><span class="n">' + round.results[1] + '</span><span class="k">Getting there</span></div>' +
        '<div><span class="n">' + round.results[0] + '</span><span class="k">Try again soon</span></div>' +
      '</div>' +
      '<p class="meta">' + (due ? due + ' ' + ui.plural(due, 'word') + ' still due.' : 'Nothing else is due today.') + '</p>' +
      '<div class="btn-row" style="margin-top:16px">' +
        (due ? '<a class="btn" href="#/review">Start another round</a>' : '') +
        '<a class="btn btn-secondary" href="#/today">Back to Today</a>' +
        '<a class="btn btn-quiet" href="#/progress">See progress</a>' +
      '</div>' +
      '</div>';
  }

  function render(parts) {
    var isRound = parts[1] === 'round';
    if (!isRound) { round.started = false; return setupView(); }
    if (!round.started) startRound();
    if (round.index >= round.queue.length) return summaryView();
    return cardView();
  }

  function rerender() {
    var main = document.getElementById('main');
    main.innerHTML = render(['review', 'round']);
    mount(main);
  }

  function printDeck() {
    var words = dueFor(setup.theme).slice(0, setup.size);
    var deck = document.getElementById('printDeck');
    if (!deck) return;
    deck.innerHTML = words.map(function (w) {
      return '<div class="card-print">' +
        '<div class="side">Front</div>' +
        '<div class="word" lang="mg">' + ui.esc(w.mg) + '</div>' +
        (w.pron ? '<div>' + ui.esc(w.pron) + '</div>' : '') +
        '<div class="side" style="margin-top:6mm">Back</div>' +
        '<div class="gloss">' + ui.esc(w.en) + '</div>' +
        '</div>';
    }).join('');
    window.print();
  }

  function mount(root) {
    var scope = root.querySelector('.view-narrow') || root;

    scope.addEventListener('change', function (event) {
      if (event.target.id === 'reviewDirection') {
        setup.direction = event.target.value;
      }
    });

    scope.addEventListener('click', function (event) {
      if (ui.speakFrom(event)) return;
      var target = event.target.closest('[data-size],[data-theme],[data-print],[data-reveal],[data-grade],[data-end],[data-start]');
      if (!target) return;

      if (target.hasAttribute('data-start')) {
        startRound();
        return; // the link navigates to #/review/round
      }
      if (target.hasAttribute('data-size')) {
        setup.size = Number(target.getAttribute('data-size'));
        rerenderSetup();
        return;
      }
      if (target.hasAttribute('data-theme')) {
        setup.theme = target.getAttribute('data-theme');
        rerenderSetup();
        return;
      }
      if (target.hasAttribute('data-print')) { printDeck(); return; }
      if (target.hasAttribute('data-reveal')) {
        // Speak the answer exactly once. When the prompt was the English
        // meaning, the Malagasy being revealed is the thing worth hearing;
        // when the prompt was already Malagasy, mount() has spoken it on
        // arrival, so revealing must stay silent. Saying it in both places is
        // what made every answer play twice.
        round.revealed = true;
        var answerWord = round.queue[round.index];
        if (setup.direction === 'en' && answerWord) speech.speakWord(answerWord);
        rerender();
        return;
      }
      if (target.hasAttribute('data-grade')) {
        // Reaching #/review/round directly leaves the queue empty; grading
        // nothing must not throw.
        if (!round.revealed || !round.queue[round.index]) return;
        core.gradeWord(round.queue[round.index].id, Number(target.getAttribute('data-grade')));
        round.results[Number(target.getAttribute('data-grade'))] += 1;
        round.index += 1;
        round.revealed = false;
        rerender();
        window.scrollTo(0, 0);
        return;
      }
      if (target.hasAttribute('data-end')) {
        round.started = false;
        round.index = round.queue.length;
        location.hash = '#/review';
      }
    });

    // On arrival only, and only while the card is still face-down.
    if (round.started && !round.revealed && setup.direction === 'mg' && core.state.prefs.autoplay) {
      var word = round.queue[round.index];
      if (word) speech.speakWord(word);
    }
  }

  function rerenderSetup() {
    var main = document.getElementById('main');
    main.innerHTML = render(['review']);
    mount(main);
  }

  S.views = S.views || {};
  S.views.review = { render: render, mount: mount, nav: 'today' };
})(window.Salama);
