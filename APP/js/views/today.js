/* Today: the next session and what is due for review. */
(function (S) {
  'use strict';
  var core = S.core;
  var ui = S.ui;

  function previewTurns(session) {
    var dialogue = session && session.dialogue ? core.dialogue(session.dialogue) : null;
    if (!dialogue) return '';
    return dialogue.lines.slice(0, 2).map(function (line) {
      return '<div class="turn"><span class="who">' + ui.esc(line.speaker || 'A') +
        (line.stage ? ' <span class="stage">(' + ui.esc(line.stage) + ')</span>' : '') + '</span>' +
        ui.mg(line.mg) +
        '<p class="trans">' + ui.esc(line.en) + '</p></div>';
    }).join('');
  }

  function steps(session, done) {
    var names = ['Warm-up dialogue', 'New words', 'Roleplay'];
    return '<ol class="steps">' + names.map(function (name) {
      return '<li data-done="' + (done ? 'true' : 'false') + '">' +
        '<span class="tick">' + (done ? ui.icon('check', 'icon-sm') : '') + '</span>' +
        '<span>' + name + '</span></li>';
    }).join('') + '</ol>';
  }

  function render() {
    var session = core.nextSession();
    var doneCount = core.sessionDoneCount();
    var total = core.data.sessions.length;
    var everything = doneCount === total;
    var due = core.dueCount();
    var round = Math.min(10, due);

    var statusLine = doneCount + ' of ' + total + ' sessions complete';
    if (core.state.streak.days > 1) statusLine += ' · ' + core.state.streak.days + '-day streak';

    return '' +
      '<div class="view-narrow">' +
        '<header class="today-head">' +
          '<p class="date">' + ui.esc(core.longDate()) + '</p>' +
          '<h1>' + (everything ? 'Course complete' : 'Today') + '</h1>' +
        '</header>' +

        (everything
          ? '<section class="panel session-panel">' +
              '<h2 class="session-title">All ' + total + ' sessions are marked complete</h2>' +
              '<p class="muted">Any session can be replayed from the course outline. Words you rate below “known” keep returning in review.</p>' +
              '<div class="btn-row"><a class="btn btn-lg" href="#/review">Review words</a>' +
              '<a class="btn btn-secondary" href="#/course">Course outline</a></div>' +
            '</section>'
          : '<section class="panel session-panel" aria-labelledby="sessionTitle">' +
              '<div class="session-meta">' +
                '<span class="week">Week ' + session.week + '</span>' +
                ' <span>Session ' + session.number + ' of ' + session.total_sessions + '</span>' +
                ' <span>Month ' + session.month + '</span>' +
              '</div>' +
              '<h2 class="session-title" id="sessionTitle">' + ui.esc(session.focus) + '</h2>' +
              '<div class="preview">' + previewTurns(session) + '</div>' +
              steps(session, false) +
              '<div class="btn-row">' +
                '<a class="btn btn-lg" href="#/session/' + session.id + '">Start session' +
                  ui.icon('arrow-right') + '</a>' +
                '<a class="btn btn-quiet" href="#/course/' + session.week + '">Week ' + session.week + ' outline</a>' +
              '</div>' +
            '</section>') +

        '<div class="review-strip">' +
          '<div>' +
            (due
              ? '<p class="count"><strong>' + due + '</strong> ' + ui.plural(due, 'word') + ' due</p>' +
                '<p class="detail">A ' + round + '-card round</p>'
              : '<p class="count"><strong>0</strong> words due</p>' +
                '<p class="detail">Words join the deck as you open sessions.</p>') +
          '</div>' +
          (due
            ? '<a class="btn btn-secondary" href="#/review">Review words</a>'
            : '<a class="btn btn-quiet" href="#/quiz">Practise a quiz instead</a>') +
        '</div>' +

        '<div class="today-foot">' +
          '<p class="meta">' + ui.esc(statusLine) + '</p>' +
          '<a class="cta-link" href="#/course">Course outline' + ui.icon('chevron-right', 'icon-sm') + '</a>' +
        '</div>' +
      '</div>';
  }

  function mount() { /* no local listeners: navigation is by link */ }

  S.views = S.views || {};
  S.views.today = { render: render, mount: mount, nav: 'today' };
})(window.Salama);
