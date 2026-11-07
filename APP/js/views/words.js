/* Reference: words, phrases, dialogues. */
(function (S) {
  'use strict';
  var core = S.core;
  var ui = S.ui;
  var speech = S.speech;

  var PAGE = 40;
  var CHIP_LIMIT = 8;
  var words = { q: '', theme: 'all', limit: PAGE };
  var phrases = { q: '', group: 'all', limit: PAGE };
  var topicsExpanded = false;
  var groupsExpanded = false;

  /* ---------------- words ---------------- */
  function wordEntry(w) {
    return '<article class="entry">' +
      '<div>' +
        '<p class="mg-line" lang="mg">' + ui.esc(w.mg) + '</p>' +
        (w.pron ? '<p class="say">' + ui.esc(w.pron) + ui.pronunciationTag(w) + '</p>' : '') +
        '<p class="en">' + ui.esc(w.en) + (w.pos ? ' <span class="meta">(' + ui.esc(w.pos) + ')</span>' : '') + '</p>' +
        (w.mg_alt && w.mg_alt.length ? '<p class="alt">Also written: <span lang="mg">' + ui.esc(w.mg_alt.join(', ')) + '</span></p>' : '') +
        (w.alt && w.alt.length ? '<p class="alt">Also: ' + ui.esc(w.alt.join('; ')) + '</p>' : '') +
        (w.mg_tsm ? '<p class="alt">Tsimihety: <span lang="mg">' + ui.esc(w.mg_tsm) + '</span></p>' : '') +
        (w.note ? '<p class="note">' + ui.esc(w.note) + '</p>' : '') +
      '</div>' +
      '<div class="entry-tools">' + ui.speakButtons(w.mg, { wordId: w.id }) + '</div>' +
      '</article>';
  }

  function filteredWords() {
    var q = ui.norm(words.q);
    return core.wordsForTheme(words.theme).filter(function (w) {
      if (!q) return true;
      if (ui.norm(w.mg).indexOf(q) !== -1) return true;
      if (ui.norm(w.en).indexOf(q) !== -1) return true;
      return (w.alt || []).some(function (a) { return ui.norm(a).indexOf(q) !== -1; });
    });
  }

  function paintWords() {
    var list = filteredWords();
    var shown = list.slice(0, words.limit);
    var listNode = document.getElementById('wordList');
    var countNode = document.getElementById('wordCount');
    var moreBtn = document.getElementById('wordMore');
    if (!listNode) return;
    listNode.innerHTML = list.length
      ? shown.map(wordEntry).join('')
      : '<p class="empty">No words match. Malagasy words are short — try fewer letters.</p>';
    countNode.textContent = list.length + ' ' + ui.plural(list.length, 'word') +
      (list.length > shown.length ? ', showing ' + shown.length : '');
    moreBtn.hidden = list.length <= shown.length;
  }

  // Topics and phrase groups run to 16 and 15 shelves. Showing all of them cost
  // four rows above the results on a phone, so the long tail starts collapsed.
  function topicChips() {
    var topics = core.data.themeMap;
    var visible = topicsExpanded ? topics : topics.slice(0, CHIP_LIMIT);
    var more = topics.length > CHIP_LIMIT
      ? '<button class="chip" type="button" data-expand-topics="true">' +
        (topicsExpanded ? 'Fewer topics' : 'More topics (' + (topics.length - CHIP_LIMIT) + ')') + '</button>'
      : '';
    return '<button class="chip" type="button" data-word-theme="all" aria-pressed="' +
      (words.theme === 'all' ? 'true' : 'false') + '">All topics</button>' +
      visible.map(function (t) {
        return '<button class="chip" type="button" data-word-theme="' + t.id + '" aria-pressed="' +
          (words.theme === t.id ? 'true' : 'false') + '">' + ui.esc(t.title) + '</button>';
      }).join('') + more;
  }

  function phraseChips() {
    var groups = core.data.phraseGroups;
    var visible = groupsExpanded ? groups : groups.slice(0, CHIP_LIMIT);
    var more = groups.length > CHIP_LIMIT
      ? '<button class="chip" type="button" data-expand-groups="true">' +
        (groupsExpanded ? 'Fewer situations' : 'More situations (' + (groups.length - CHIP_LIMIT) + ')') + '</button>'
      : '';
    return '<button class="chip" type="button" data-phrase-group="all" aria-pressed="' +
      (phrases.group === 'all' ? 'true' : 'false') + '">All situations (' + core.data.phrases.length + ')</button>' +
      visible.map(function (g) {
        return '<button class="chip" type="button" data-phrase-group="' + g.id + '" aria-pressed="' +
          (phrases.group === g.id ? 'true' : 'false') + '">' + ui.esc(g.title) + ' (' + g.count + ')</button>';
      }).join('') + more;
  }

  function wordsView() {
    return '<div>' +
      ui.referenceTabs('words') +
      '<h1>Words</h1>' +
      '<p class="lead">' + core.data.vocabulary.length + ' dictionary entries, with pronunciation where it is known. Search in Malagasy or English.</p>' +
      '<div class="filter-row">' +
        '<div class="search-wrap">' + ui.icon('search') +
          '<input type="search" id="wordSearch" placeholder="Search words" aria-label="Search words" value="' + ui.esc(words.q) + '">' +
        '</div>' +
      '</div>' +
      '<div class="chips" id="wordTopics">' + topicChips() + '</div>' +
      '<p class="result-count" id="wordCount"></p>' +
      '<div class="entry-list" id="wordList"></div>' +
      '<div style="margin-top:24px"><button class="btn btn-quiet" type="button" id="wordMore" hidden>Show more words</button></div>' +
      '</div>';
  }

  /* ---------------- phrases ---------------- */
  function phraseEntry(p) {
    return '<article class="entry">' +
      '<div>' +
        '<p class="mg-line" lang="mg">' + ui.esc(p.mg) + '</p>' +
        (p.pron ? '<p class="say">' + ui.esc(p.pron) + ui.pronunciationTag(p) + '</p>' : '') +
        '<p class="en">' + ui.esc(p.en) + '</p>' +
        (p.note ? '<p class="note">' + ui.esc(p.note) + '</p>' : '') +
        (p.mg_tsm ? '<p class="alt">Tsimihety: <span lang="mg">' + ui.esc(p.mg_tsm) + '</span></p>' : '') +
      '</div>' +
      '<div class="entry-tools">' + ui.speakButtons(p.mg) + '</div>' +
      '</article>';
  }

  function filteredPhrases() {
    var q = ui.norm(phrases.q);
    return core.data.phrases.filter(function (p) {
      if (phrases.group !== 'all' && p.group !== phrases.group) return false;
      if (!q) return true;
      return ui.norm(p.mg).indexOf(q) !== -1 || ui.norm(p.en).indexOf(q) !== -1;
    });
  }

  function paintPhrases() {
    var list = filteredPhrases();
    var shown = list.slice(0, phrases.limit);
    var listNode = document.getElementById('phraseList');
    var countNode = document.getElementById('phraseCount');
    var moreBtn = document.getElementById('phraseMore');
    if (!listNode) return;
    listNode.innerHTML = list.length
      ? shown.map(phraseEntry).join('')
      : '<p class="empty">No phrases match that search.</p>';
    countNode.textContent = list.length + ' ' + ui.plural(list.length, 'phrase') +
      (list.length > shown.length ? ', showing ' + shown.length : '');
    moreBtn.hidden = list.length <= shown.length;
  }

  function dialogueList() {
    var q = ui.norm(phrases.q);
    var list = core.data.dialogues.filter(function (d) {
      if (!q) return true;
      if (ui.norm(d.title).indexOf(q) !== -1) return true;
      return d.lines.some(function (l) { return ui.norm(l.mg).indexOf(q) !== -1 || ui.norm(l.en).indexOf(q) !== -1; });
    });
    if (!list.length) return '';
    return '<h2>Dialogues</h2><div class="entry-list">' + list.slice(0, 12).map(function (d) {
      return '<a class="grammar-item" href="#/dialogue/' + d.id + '">' +
        '<span class="t">' + ui.esc(d.title) + '</span>' +
        '<span class="m">' + d.lines.length + ' lines · ' + ui.esc(core.themeTitle(d.group)) + '</span></a>';
    }).join('') + '</div>';
  }

  function phrasesView() {
    return '<div>' +
      ui.referenceTabs('phrases') +
      '<h1>Phrases &amp; dialogues</h1>' +
      '<p class="lead">' + core.data.phrases.length + ' phrases and ' + core.data.dialogues.length +
        ' recorded conversations, grouped by situation.</p>' +
      '<div class="filter-row">' +
        '<div class="search-wrap">' + ui.icon('search') +
          '<input type="search" id="phraseSearch" placeholder="Search phrases" aria-label="Search phrases" value="' + ui.esc(phrases.q) + '">' +
        '</div>' +
      '</div>' +
      '<div class="chips" id="phraseChips">' + phraseChips() + '</div>' +
      '<p class="result-count" id="phraseCount"></p>' +
      '<div class="entry-list" id="phraseList"></div>' +
      '<div style="margin-top:24px"><button class="btn btn-quiet" type="button" id="phraseMore" hidden>Show more phrases</button></div>' +
      '<div id="dialogueSection">' + dialogueList() + '</div>' +
      '</div>';
  }

  /* ---------------- one dialogue ---------------- */
  function dialogueView(id) {
    var dialogue = core.dialogue(id);
    if (!dialogue) return '<p class="empty">That dialogue was not found.</p>';
    return '<div class="view-narrow">' +
      '<p class="meta"><a class="cta-link" href="#/reference/phrases">Phrases &amp; dialogues</a></p>' +
      '<h1>' + ui.esc(dialogue.title) + '</h1>' +
      '<p class="meta">' + ui.esc(core.themeTitle(dialogue.group)) + ' · ' + dialogue.lines.length + ' lines</p>' +
      '<div class="dialogue panel">' + dialogue.lines.map(function (line, index) {
        return '<div class="turn">' +
          '<span class="who">' + ui.esc(line.speaker || 'A') +
            (line.stage ? ' <span class="stage">(' + ui.esc(line.stage) + ')</span>' : '') + '</span>' +
          '<p class="line" lang="mg">' + ui.esc(line.mg) + '</p>' +
          (line.pron ? '<p class="say">' + ui.esc(line.pron) + ui.pronunciationTag(line) + '</p>' : '') +
          '<p class="trans">' + ui.esc(line.en) + '</p>' +
          '<div class="turn-tools">' +
            ui.speakButtons(line.mg, { line: id + ':' + index }) +
          '</div>' +
          '</div>';
      }).join('') + '</div>' +
      '</div>';
  }

  /* ---------------- mount ---------------- */
  function mount(root, which) {
    var scope = root.querySelector('.view-narrow') || root.firstElementChild || root;
    if (!scope || !scope.addEventListener) scope = root;

    scope.addEventListener('click', function (event) {
      if (ui.speakFrom(event)) return;
      var chip = event.target.closest('[data-word-theme]');
      if (chip) {
        words.theme = chip.getAttribute('data-word-theme');
        words.limit = PAGE;
        var topics = scope.querySelector('#wordTopics');
        if (topics) topics.innerHTML = topicChips();
        paintWords();
        return;
      }
      if (event.target.closest('[data-expand-topics]')) {
        topicsExpanded = !topicsExpanded;
        var topicBox = scope.querySelector('#wordTopics');
        if (topicBox) topicBox.innerHTML = topicChips();
        return;
      }
      var group = event.target.closest('[data-phrase-group]');
      if (group) {
        phrases.group = group.getAttribute('data-phrase-group');
        phrases.limit = PAGE;
        var chipBox = scope.querySelector('#phraseChips');
        if (chipBox) chipBox.innerHTML = phraseChips();
        paintPhrases();
        var section = scope.querySelector('#dialogueSection');
        if (section) section.innerHTML = dialogueList();
        return;
      }
      if (event.target.closest('[data-expand-groups]')) {
        groupsExpanded = !groupsExpanded;
        var groupBox = scope.querySelector('#phraseChips');
        if (groupBox) groupBox.innerHTML = phraseChips();
        return;
      }
      if (event.target.closest('#wordMore')) { words.limit += PAGE; paintWords(); return; }
      if (event.target.closest('#phraseMore')) { phrases.limit += PAGE; paintPhrases(); return; }
    });

    scope.addEventListener('input', function (event) {
      if (event.target.id === 'wordSearch') { words.q = event.target.value; words.limit = PAGE; paintWords(); }
      if (event.target.id === 'phraseSearch') {
        phrases.q = event.target.value;
        phrases.limit = PAGE;
        paintPhrases();
        var section = scope.querySelector('#dialogueSection');
        if (section) section.innerHTML = dialogueList();
      }
    });

    if (which === 'words') paintWords();
    if (which === 'phrases') paintPhrases();
  }

  S.views = S.views || {};
  S.views.words = {
    render: wordsView,
    mount: function (root) { mount(root, 'words'); },
    nav: 'reference'
  };
  S.views.phrases = {
    render: phrasesView,
    mount: function (root) { mount(root, 'phrases'); },
    nav: 'reference'
  };
  S.views.dialogue = {
    render: function (parts) { return dialogueView(parts[1]); },
    mount: function (root) { mount(root, 'dialogue'); },
    nav: 'reference'
  };
})(window.Salama);
