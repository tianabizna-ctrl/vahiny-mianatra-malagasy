/* Course: the 12-week outline, and one week's three sessions. */
(function (S) {
  'use strict';
  var core = S.core;
  var ui = S.ui;

  function weekList(selectedWeek) {
    return '<div class="week-list">' + core.data.curriculum.map(function (week) {
      var done = core.weekDoneCount(week.week);
      var state = done === week.sessions.length ? 'Complete'
        : (done ? done + ' of ' + week.sessions.length : '');
      return '<a class="week-row" href="#/course/' + week.week + '"' +
        (week.week === selectedWeek ? ' aria-current="true"' : '') + '>' +
        '<span class="week-no">Week ' + week.week + '</span>' +
        '<span class="week-title">' + ui.esc(week.title) + '</span>' +
        '<span class="week-state">' + state + '</span>' +
        ui.icon('chevron-right', 'icon-sm') +
        '</a>';
    }).join('') + '</div>';
  }

  function weekDetail(week) {
    var sessions = core.data.sessions.filter(function (s) { return s.week === week.week; });
    return '<section class="panel" aria-labelledby="weekTitle">' +
      '<div class="session-meta"><span class="week">Month ' + week.month + '</span> ' +
      '<span>' + core.weekDoneCount(week.week) + ' of ' + sessions.length + ' sessions complete</span></div>' +
      '<h2 id="weekTitle" style="margin-top:0">Week ' + week.week + ' — ' + ui.esc(week.title) + '</h2>' +
      sessions.map(function (session) {
        var done = core.isSessionDone(session.id);
        return '<a class="session-row" href="#/session/' + session.id + '">' +
          '<span><span class="day">' + ui.esc(session.day) + ' · Session ' + session.number + '</span>' +
          '<p class="focus">' + ui.esc(session.focus) + '</p></span>' +
          '<span class="state">' + (done ? ui.icon('check', 'icon-sm') + ' Done' : 'Start') +
          ui.icon('chevron-right', 'icon-sm') + '</span></a>';
      }).join('') +
      '</section>';
  }

  function render(parts) {
    var weekNo = Number(parts[1]);
    var week = core.data.curriculum.filter(function (w) { return w.week === weekNo; })[0] || null;

    return '<div class="view-narrow">' +
      '<h1>Course</h1>' +
      '<p class="lead">Twelve weeks, three sessions a week, from first greetings to a full conversation.</p>' +
      (week ? weekDetail(week) : '') +
      '<h2>' + (week ? 'All weeks' : 'Weeks') + '</h2>' +
      weekList(week ? week.week : 0) +
      '</div>';
  }

  function mount(root) {
    // Selecting a week scrolls the outline into view so the detail is visible.
    if (root && root.querySelector('[aria-current="true"]')) {
      var el = root.querySelector('#weekTitle');
      if (el && window.innerWidth < 760) el.scrollIntoView({ block: 'start' });
    }
  }

  S.views = S.views || {};
  S.views.course = { render: render, mount: mount, nav: 'course' };
})(window.Salama);
