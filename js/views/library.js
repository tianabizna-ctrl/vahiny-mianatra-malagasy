/* Reference: grammar, culture notes, pronunciation. */
(function (S) {
  'use strict';
  var core = S.core;
  var ui = S.ui;
  var speech = S.speech;

  var culture = { q: '', limit: 30 };

  /* ---------------- grammar ---------------- */
  function grammarWeeks(id) {
    var weeks = [];
    core.data.sessions.forEach(function (s) {
      if (s.grammar === id && weeks.indexOf(s.week) === -1) weeks.push(s.week);
    });
    return weeks.sort(function (a, b) { return a - b; });
  }

  function grammarIndex(topicId) {
    if (topicId) {
      var topic = core.grammar(topicId);
      if (!topic) return '<p class="empty">That grammar topic was not found.</p>';
      return '<p class="meta"><a class="cta-link" href="#/reference/grammar">All grammar topics</a></p>' +
        '<h1>' + ui.esc(topic.title) + '</h1>' +
        '<div class="panel">' + topic.rules.map(function (rule) {
          return '<div class="rule-block">' +
            '<h2 class="rule-name">' + ui.esc(rule.rule) + '</h2>' +
            (rule.explanation ? '<p>' + ui.esc(rule.explanation) + '</p>' : '') +
            (rule.examples || []).map(function (ex) {
              return '<div class="example"><strong lang="mg">' + ui.esc(ex.mg) + '</strong>' +
                '<span class="arrow">→</span>' + ui.esc(ex.en) + '</div>';
            }).join('') +
            '</div>';
        }).join('') + '</div>';
    }

    return '<div class="grammar-index">' + core.data.grammar.map(function (topic) {
      var weeks = grammarWeeks(topic.id);
      return '<a class="grammar-item" href="#/reference/grammar/' + topic.id + '">' +
        '<span class="t">' + ui.esc(topic.title) + '</span>' +
        '<span class="m">' + (weeks.length ? 'Taught in week ' + weeks.join(', ') : 'Reference topic') + '</span></a>';
    }).join('') + '</div>';
  }

  function grammarView(parts) {
    return '<div class="view-narrow">' +
      ui.referenceTabs('grammar') +
      (parts[2] ? '' : '<h1>Grammar</h1><p class="lead">Twenty-seven topics, in the order the course introduces them.</p>') +
      grammarIndex(parts[2]) +
      '</div>';
  }

  /* ---------------- culture ---------------- */
  function filteredCulture() {
    var q = ui.norm(culture.q);
    if (!q) return core.data.culture;
    return core.data.culture.filter(function (c) { return ui.norm(c.note).indexOf(q) !== -1; });
  }

  function paintCulture() {
    var list = filteredCulture();
    var node = document.getElementById('cultureList');
    var count = document.getElementById('cultureCount');
    if (!node) return;
    node.innerHTML = list.slice(0, culture.limit).map(function (c) {
      return '<article class="culture-note">' +
        '<p>' + ui.esc(c.note) + '</p>' +
        '<span class="src">' + ui.esc(c.lesson.replace(/_/g, ' ')) + '</span>' +
        '</article>';
    }).join('') || '<p class="empty">No notes match that search.</p>';
    count.textContent = list.length + ' ' + ui.plural(list.length, 'note') +
      (list.length > culture.limit ? ', showing ' + culture.limit : '');
    var more = document.getElementById('cultureMore');
    if (more) more.hidden = list.length <= culture.limit;
  }

  function cultureView() {
    return '<div class="view-narrow">' +
      ui.referenceTabs('culture') +
      '<h1>Culture</h1>' +
      '<p class="lead">Greetings by region, hospitality, family customs and sayings, taken from the lesson materials.</p>' +
      '<div class="filter-row">' +
        '<div class="search-wrap">' + ui.icon('search') +
          '<input type="search" id="cultureSearch" placeholder="Search notes" aria-label="Search culture notes" value="' + ui.esc(culture.q) + '">' +
        '</div>' +
      '</div>' +
      '<p class="result-count" id="cultureCount"></p>' +
      '<div id="cultureList"></div>' +
      '<div style="margin-top:24px"><button class="btn btn-quiet" type="button" id="cultureMore" hidden>Show more notes</button></div>' +
      '</div>';
  }

  /* ---------------- pronunciation ---------------- */
  function sayItView() {
    var guide = core.data.pronunciation;
    var vowels = (guide.vowels || []).map(function (v) {
      return '<tr>' +
        '<td class="vowel"><span class="letter" lang="mg">' + ui.esc(v.letter || '') + '</span></td>' +
        '<td>' + ui.esc(v.sound || v.say || '') +
        ((v.examples || []).length ? '<br><span class="meta">' + ui.esc((v.examples || []).join(' · ')) + '</span>' : '') +
        '</td>' +
        '</tr>';
    }).join('');

    var notes = (guide.notes || []).map(function (n) {
      return '<p>' + ui.esc(typeof n === 'string' ? n : (n.note || n.text || '')) + '</p>';
    }).join('');

    var keyWords = [].concat(guide.key_words || [], guide.teacher_flashcards || [], guide.traveler || [])
      .filter(function (w) { return w && w.mg; })
      .slice(0, 40)
      .map(function (w) {
        return '<article class="entry">' +
          '<div><p class="mg-line" lang="mg">' + ui.esc(w.mg) + '</p>' +
          (w.say ? '<p class="say">' + ui.esc(w.say) + '</p>' : '') +
          '<p class="en">' + ui.esc(w.en || '') + '</p></div>' +
          '<div class="entry-tools">' + ui.speakButtons(w.mg) + '</div>' +
          '</article>';
      }).join('');

    return '<div class="view-narrow">' +
      ui.referenceTabs('sayit') +
      '<h1>How to say it</h1>' +
      '<p class="lead">Malagasy spelling is consistent: every letter is pronounced, and stress usually falls on the second-to-last syllable.</p>' +
      '<div class="panel">' +
        '<h2 style="margin-top:0">Letters and sounds</h2>' +
        '<table class="sound-table"><thead><tr><th>Written</th><th>Sounds like</th></tr></thead>' +
        '<tbody>' + vowels + '</tbody></table>' +
      '</div>' +
      (notes ? '<div class="panel"><h2 style="margin-top:0">Good to know</h2>' + notes + '</div>' : '') +
      (keyWords ? '<h2>Words to practise</h2><div class="entry-list">' + keyWords + '</div>' : '') +
      '<p class="meta" style="margin-top:24px">Word pronunciation here is the best available for each word: teacher-written for some, ' +
      'generated and marked “approx.” for the rest. Recorded lesson audio in a session is the reference for listening.</p>' +
      '</div>';
  }

  function mount(root, which) {
    var scope = root.querySelector('.view-narrow') || root.firstElementChild || root;
    if (!scope || !scope.addEventListener) scope = root;

    scope.addEventListener('click', function (event) {
      if (ui.speakFrom(event)) return;
      if (event.target.closest('#cultureMore')) { culture.limit += 30; paintCulture(); }
    });

    scope.addEventListener('input', function (event) {
      if (event.target.id === 'cultureSearch') {
        culture.q = event.target.value;
        culture.limit = 30;
        paintCulture();
      }
    });

    if (which === 'culture') paintCulture();
  }

  S.views = S.views || {};
  S.views.grammar = {
    render: grammarView,
    mount: function (root) { mount(root, 'grammar'); },
    nav: 'reference'
  };
  S.views.culture = {
    render: cultureView,
    mount: function (root) { mount(root, 'culture'); },
    nav: 'reference'
  };
  S.views.sayit = {
    render: sayItView,
    mount: function (root) { mount(root, 'sayit'); },
    nav: 'reference'
  };
})(window.Salama);
