/* Quiz: multiple choice, no typing. */
(function (S) {
  'use strict';
  var core = S.core;
  var ui = S.ui;
  var speech = S.speech;

  var options = { theme: 'all', length: 10 };
  var quiz = null;    // { pool, index, score, answered, chosen }
  var summary = null; // { score, total } once a quiz is finished

  function shuffle(list) {
    var arr = list.slice();
    for (var i = arr.length - 1; i > 0; i -= 1) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = arr[i]; arr[i] = arr[j]; arr[j] = tmp;
    }
    return arr;
  }

  function themeCounts() {
    return core.data.themeMap.map(function (t) {
      return { id: t.id, title: t.title, n: core.wordsForTheme(t.id).length };
    }).filter(function (t) { return t.n >= 10; });
  }

  function setupView() {
    var themes = themeCounts();
    return '<div class="view-narrow">' +
      '<h1>Quiz</h1>' +
      '<p class="lead">Ten or fifteen questions on one topic. Every answer is marked as you go.</p>' +
      '<div class="panel">' +
        '<div class="filter-row">' +
          '<div class="field"><label for="quizTheme">Topic</label>' +
            '<select id="quizTheme"><option value="all">All topics</option>' +
            themes.map(function (t) {
              return '<option value="' + t.id + '"' + (options.theme === t.id ? ' selected' : '') + '>' +
                ui.esc(t.title) + ' (' + t.n + ')</option>';
            }).join('') +
            '</select></div>' +
          '<div class="field"><label for="quizLength">Questions</label>' +
            '<select id="quizLength">' +
              [5, 10, 15].map(function (n) {
                return '<option value="' + n + '"' + (options.length === n ? ' selected' : '') + '>' + n + ' questions</option>';
              }).join('') +
            '</select></div>' +
        '</div>' +
        '<button class="btn btn-lg" type="button" data-quiz-start="true">Start quiz' + ui.icon('arrow-right') + '</button>' +
      '</div>' +
      '</div>';
  }

  function buildQuiz() {
    var pool = shuffle(core.wordsForTheme(options.theme)).slice(0, options.length);
    if (pool.length < 4) { ui.toast('Not enough words in that topic.'); return; }
    quiz = { pool: pool, index: 0, score: 0, answered: false, chosen: null };
  }

  function distractorsFor(word, promptLang) {
    var sameTheme = core.wordsForTheme((word.themes || [])[0] || 'all');
    var pools = [sameTheme, core.wordsForTheme('all')];
    var need = 3;
    var picked = [];
    var seen = {};
    seen[promptLang === 'mg' ? word.en : word.mg] = true;
    for (var p = 0; p < pools.length && picked.length < need; p += 1) {
      var shuffled = shuffle(pools[p]);
      for (var i = 0; i < shuffled.length && picked.length < need; i += 1) {
        var candidate = shuffled[i];
        if (candidate.id === word.id) continue;
        var text = promptLang === 'mg' ? candidate.en : candidate.mg;
        if (!text || seen[text] || text.length > 60) continue;
        seen[text] = true;
        picked.push(text);
      }
    }
    return picked;
  }

  function questionView() {
    var word = quiz.pool[quiz.index];
    var promptLang = quiz.index % 2 === 0 ? 'mg' : 'en';
    var prompt = promptLang === 'mg' ? word.mg : word.en;
    var correct = promptLang === 'mg' ? word.en : word.mg;
    var all = shuffle([correct].concat(distractorsFor(word, promptLang)));
    quiz.options = all;

    var body = quiz.answered
      ? '<div class="feedback" data-tone="' + (quiz.chosen === correct ? 'good' : 'bad') + '" role="status">' +
          (quiz.chosen === correct
            ? 'Correct. <span lang="mg">' + ui.esc(word.mg) + '</span> — ' + ui.esc(word.en)
            : 'Not quite. <span lang="mg">' + ui.esc(word.mg) + '</span> means “' + ui.esc(word.en) + '”.') +
        '</div>' +
        '<div class="btn-row" style="margin-top:16px">' +
          '<button class="btn" type="button" data-quiz-next="true">' +
            (quiz.index + 1 >= quiz.pool.length ? 'See result' : 'Next question') + ui.icon('arrow-right') + '</button>' +
        '</div>'
      : '<div class="options">' + all.map(function (option, optionIndex) {
          return '<button class="option" type="button" data-option="' + optionIndex + '" lang="' +
            (promptLang === 'mg' ? 'en' : 'mg') + '">' + ui.esc(option) + '</button>';
        }).join('') + '</div>';

    return '<div class="view-narrow">' +
      '<div class="review-head"><h1>Quiz</h1>' +
        '<span class="review-position">Question ' + (quiz.index + 1) + ' of ' + quiz.pool.length + '</span></div>' +
      '<div class="panel">' +
        '<p class="quiz-prompt">' +
          (promptLang === 'mg'
            ? '<span class="word" lang="mg">' + ui.esc(prompt) + '</span>What does it mean?'
            : '<span class="word">' + ui.esc(prompt) + '</span>Which is the Malagasy?') +
        '</p>' +
        (promptLang === 'mg'
          ? '<div style="margin-bottom:16px">' + ui.speakButtons(word.mg, { wordId: word.id }) + '</div>'
          : '') +
        body +
      '</div>' +
      '<div class="btn-row" style="margin-top:16px">' +
        '<button class="btn btn-quiet" type="button" data-quiz-quit="true">End quiz</button>' +
      '</div>' +
      '</div>';
  }

  function finishQuiz() {
    summary = { score: quiz.score, total: quiz.pool.length, theme: options.theme };
    core.state.quizzes.push({
      date: Date.now(),
      theme: options.theme,
      score: quiz.score,
      total: quiz.pool.length
    });
    core.save();
    quiz = null;
  }

  function summaryView() {
    var pct = Math.round((summary.score / summary.total) * 100);
    return '<div class="view-narrow">' +
      '<h1>Quiz finished</h1>' +
      '<p class="lead">' + summary.score + ' of ' + summary.total + ' correct — ' + pct + '%</p>' +
      '<div class="btn-row">' +
        '<button class="btn" type="button" data-quiz-again="true">Another quiz</button>' +
        '<a class="btn btn-secondary" href="#/today">Back to Today</a>' +
        '<a class="btn btn-quiet" href="#/progress">See progress</a>' +
      '</div>' +
      '</div>';
  }

  function render() {
    if (summary) return summaryView();
    if (!quiz) return setupView();
    return questionView();
  }

  function rerender() {
    var main = document.getElementById('main');
    main.innerHTML = render();
    mount(main);
  }

  function mount(root) {
    var scope = root.querySelector('.view-narrow') || root;

    scope.addEventListener('change', function (event) {
      if (event.target.id === 'quizTheme') options.theme = event.target.value;
      if (event.target.id === 'quizLength') options.length = Number(event.target.value);
    });

    scope.addEventListener('click', function (event) {
      if (ui.speakFrom(event)) return;
      var target = event.target.closest('[data-quiz-start],[data-option],[data-quiz-next],[data-quiz-quit],[data-quiz-again]');
      if (!target) return;

      if (target.hasAttribute('data-quiz-start')) { buildQuiz(); rerender(); return; }
      if (target.hasAttribute('data-option')) {
        if (quiz.answered) return;
        var picked = quiz.options[Number(target.getAttribute('data-option'))];
        quiz.chosen = picked;
        quiz.answered = true;
        var word = quiz.pool[quiz.index];
        var correct = quiz.index % 2 === 0 ? word.en : word.mg;
        var right = picked === correct;
        if (right) quiz.score += 1;
        // A quiz answer is practice too, so it feeds the same schedule.
        core.gradeWord(word.id, right ? 2 : 0);
        rerender();
        // The old condition tested `correct`, a non-empty string that was
        // always truthy, so a wrong answer was read out as loudly as a right one.
        if (right && core.state.prefs.autoplay) speech.speakWord(word);
        return;
      }
      if (target.hasAttribute('data-quiz-next')) {
        if (quiz.index + 1 >= quiz.pool.length) finishQuiz();
        else { quiz.index += 1; quiz.answered = false; quiz.chosen = null; }
        rerender();
        window.scrollTo(0, 0);
        return;
      }
      if (target.hasAttribute('data-quiz-quit')) {
        quiz = null;
        summary = null;
        rerender();
        return;
      }
      if (target.hasAttribute('data-quiz-again')) {
        quiz = null;
        summary = null;
        rerender();
        return;
      }
    });
  }

  S.views = S.views || {};
  S.views.quiz = { render: render, mount: mount, nav: null };
})(window.Salama);
