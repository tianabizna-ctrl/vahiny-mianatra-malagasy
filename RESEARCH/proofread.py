#!/usr/bin/env python3
"""Build PROOFREAD.html — a review sheet for a native Malagasy speaker.

    python3 RESEARCH/proofread.py

One self-contained page (no network) that lists every Malagasy sentence, phrase and
word in the course, biggest risk first:

  1. Sentences   — the 196 dialogue lines (what the learner actually says out loud)
  2. Phrases     — the 717 phrasebook entries
  3. Words       — the ~683 single words the 36 sessions teach, then the rest
  4. Grammar     — example sentences from the 27 grammar topics
  5. Notes       — the 161 culture notes

For each row the reviewer marks ✔ (marina), ? (tsy fantatro) or ✘ (diso) and can
type the correct Malagasy and/or English. Marks and corrections live in the
browser's localStorage and export as TSV + JSON. Feed the TSV to

    python3 RESEARCH/apply_corrections.py corrections.tsv

which writes RESEARCH/CORRECTIONS.json; the build then applies every correction and
marks the approved entries as checked by a native speaker.
"""
import base64
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "PROOFREAD.html")


def load_content():
    path = os.path.join(BASE, "APP", "data", "content.js")
    raw = open(path, encoding="utf-8").read()
    return json.loads(raw[raw.index("{"):raw.rindex("}") + 1])


def taught_themes(data):
    themes = set()
    for session in data["sessions"]:
        themes.update(session.get("themes") or [])
    return themes


def build_rows(data):
    taught = taught_themes(data)
    rows = []

    # 1. Dialogue sentences — natural speech, used in the roleplay step.
    for dialogue in data["dialogues"]:
        for index, line in enumerate(dialogue["lines"]):
            rows.append({
                "key": "dlg:%s:%d" % (dialogue["id"], index),
                "section": "sentences",
                "mg": line.get("mg", ""),
                "en": line.get("en", ""),
                "audio": data.get("lineAudio", {}).get("%s-%d" % (dialogue["id"], index), ""),
                "pron": line.get("pron", ""),
                "where": dialogue.get("title", ""),
                "who": line.get("speaker", ""),
            })

    # 2. Phrasebook phrases.
    for phrase in data["phrases"]:
        rows.append({
            "key": "phrase:%s" % phrase["id"],
            "section": "phrases",
            "mg": phrase.get("mg", ""),
            "en": phrase.get("en", ""),
            "audio": data.get("phraseAudio", {}).get(phrase["id"], ""),
            "pron": phrase.get("pron", ""),
            "where": phrase.get("group", ""),
            "who": "",
        })

    # 3. Words: everything the sessions teach first, then the long tail.
    for word in sorted(data["vocabulary"],
                       key=lambda w: (0 if set(w.get("themes") or []) & taught else 1,
                                      w.get("level") or 1, w["mg"])):
        rows.append({
            "key": "word:%s" % word["id"],
            "section": "words",
            "mg": word.get("mg", ""),
            "en": word.get("en", ""),
            "audio": data.get("wordAudio", {}).get(word["id"], ""),
            "pron": word.get("pron", ""),
            "where": ", ".join((word.get("themes") or [])[:2]) if word.get("themes") else "",
            "who": "taught" if set(word.get("themes") or []) & taught else "",
        })

    # 4. Grammar example sentences.
    for topic in data["grammar"]:
        for rule_index, rule in enumerate(topic.get("rules", [])):
            for example_index, example in enumerate(rule.get("examples", [])):
                if not example.get("mg"):
                    continue
                rows.append({
                    "key": "gram:%s:%d:%d" % (topic["id"], rule_index, example_index),
                    "section": "grammar",
                    "mg": example["mg"],
                    "en": example.get("en", ""),
                    "audio": "",
                    "pron": "",
                    "where": topic.get("title", ""),
                    "who": rule.get("rule", "")[:70],
                })

    # 5. Culture notes (English prose that quotes Malagasy).
    for index, note in enumerate(data["culture"]):
        rows.append({
            "key": "culture:%d" % index,
            "section": "notes",
            "mg": note.get("note", ""),
            "en": "",
            "audio": "",
            "pron": "",
            "where": note.get("lesson", "").replace("_", " "),
            "who": "",
        })
    return rows


PAGE = r"""<!DOCTYPE html>
<html lang="mg">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Salama! — fanitsiana ny votoaty</title>
<style>
  :root {
    --ink:#241f1a; --paper:#faf6ef; --card:#fff; --line:#d8ccb8; --line-soft:#e9e0d0;
    --green:#14603a; --green-soft:#e8f2ec; --gold:#87550f; --red:#8c2f1e; --red-soft:#f7e0dc;
    --muted:#5b5044; --blue-soft:#eaf1f6; --blue:#1f4e6b;
  }
  * { box-sizing:border-box; }
  html { -webkit-text-size-adjust:100%; }
  body {
    margin:0; background:var(--paper); color:var(--ink);
    font:19px/1.55 -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }
  a { color:var(--green); }

  /* ---------- header ---------- */
  header { position:sticky; top:0; z-index:20; background:var(--paper);
           border-bottom:2px solid var(--line); padding:10px 16px 8px; }
  .head-top { display:flex; flex-wrap:wrap; gap:10px; align-items:baseline; }
  h1 { font-size:21px; margin:0; }
  .sub { font-size:15px; color:var(--muted); margin:0; }
  .progress { margin:8px 0 6px; height:9px; background:var(--line-soft); border-radius:99px; overflow:hidden; }
  .progress > i { display:block; height:100%; width:0; background:var(--green); transition:width .2s; }
  .bar { display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
  button, select, input, textarea { font:inherit; color:inherit; }
  .btn { background:var(--card); border:2px solid var(--line); border-radius:9px;
         padding:9px 13px; min-height:44px; cursor:pointer; }
  .btn:hover { border-color:var(--green); }
  .btn-primary { background:var(--green); border-color:var(--green); color:#fff; font-weight:600; }
  .btn-small { padding:6px 10px; min-height:38px; font-size:16px; }
  select, input[type=search] { background:var(--card); border:2px solid var(--line);
        border-radius:9px; padding:9px 11px; min-height:44px; }
  input[type=search] { min-width:190px; flex:1 1 190px; }
  .tabs { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
  .tab { border:2px solid var(--line); background:var(--card); border-radius:99px;
         padding:7px 13px; cursor:pointer; font-size:16px; display:flex; gap:6px; align-items:center; }
  .tab[aria-pressed=true] { background:var(--green-soft); border-color:var(--green); font-weight:600; }
  .tab .n { font-size:13px; color:var(--muted); font-variant-numeric:tabular-nums; }
  .tab[aria-pressed=true] .n { color:var(--green); }
  .counter { font-size:15px; color:var(--muted); margin-left:auto; font-variant-numeric:tabular-nums; }

  /* ---------- guidance ---------- */
  .persist-warn { margin: 8px 0 0; padding: 8px 10px; border-radius: 6px;
    background: #fff4e0; color: #6b4a10; font-size: var(--fs-meta); line-height: 1.5; }
  .switch { display:flex; gap:8px; align-items:center; font-size:16px;
    border:2px solid var(--line); background:var(--card); border-radius:9px;
    padding:7px 11px; min-height:44px; cursor:pointer; }
  .switch input { width:20px; height:20px; }
  .listen { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin:2px 0 6px; }
  .play { background:var(--green); color:#fff; border:2px solid var(--green); border-radius:11px;
    padding:12px 22px; font-size:20px; font-weight:700; min-height:56px; min-width:132px;
    cursor:pointer; }
  .play:hover { filter:brightness(1.08); }
  .play:disabled { background:var(--line); border-color:var(--line); color:var(--muted);
    cursor:not-allowed; }
  .noclip { font-size:15px; color:var(--muted); font-style:italic; }
  .row[data-active="true"] { border-color:var(--green); box-shadow:0 0 0 3px var(--green-soft); }
  .audio-tip { margin:8px 0 0; padding:9px 11px; border-radius:6px; background:var(--blue-soft);
    color:var(--blue); font-size:15px; line-height:1.5; }
  .listen audio { width:100%; max-width:360px; height:44px; margin:2px 0; }
  .audio-warn { margin:8px 0 0; padding:9px 11px; border-radius:6px; background:var(--red-soft);
    color:#6b2b1c; font-size:15px; line-height:1.5; }
  .order { margin: 0 0 10px; font-size: var(--fs-meta); line-height: 1.55; }
  details.guide { margin:10px 16px 0; background:var(--blue-soft); border:1px solid #cfe0ea;
                  border-radius:12px; padding:10px 14px; }
  details.guide summary { cursor:pointer; font-weight:600; color:var(--blue); }
  details.guide ul { margin:8px 0 0 18px; padding:0; font-size:16px; }
  details.guide li { margin:4px 0; }
  .mg-word { font-weight:600; }

  /* ---------- rows ---------- */
  main { padding:12px 16px 120px; max-width:900px; margin:0 auto; }
  .row { background:var(--card); border:1px solid var(--line); border-radius:14px;
         padding:14px 16px; margin-bottom:10px; }
  .row[data-verdict=ok] { border-color:#b6d8c4; background:linear-gradient(0deg,#f4faf6,#fff); }
  .row[data-verdict=wrong] { border-color:#e3b3a9; background:linear-gradient(0deg,#fdf5f3,#fff); }
  .row[data-verdict=unsure] { border-color:#e2d3ae; background:linear-gradient(0deg,#fdfaf1,#fff); }
  .mg-line { font-size:25px; font-weight:600; margin:0 0 2px; line-height:1.3; }
  .row[data-section=notes] .mg-line { font-size:18px; font-weight:400; }
  .en-line { margin:0; color:var(--muted); font-size:17px; }
  .pron { margin:2px 0 0; color:var(--gold); font-size:16px;
          font-variant:small-caps; letter-spacing:.02em; }
  .meta { margin:6px 0 0; display:flex; flex-wrap:wrap; gap:6px; align-items:center; }
  .chip { font-size:12.5px; text-transform:uppercase; letter-spacing:.05em;
          border:1px solid var(--line); border-radius:99px; padding:2px 8px; color:var(--muted); }
  .chip.taught { border-color:var(--green); color:var(--green); }

  .tools { display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; align-items:center; }
  .verdict { display:flex; gap:5px; }
  .verdict button { border:2px solid var(--line); background:var(--card); border-radius:9px;
                    min-width:46px; min-height:42px; cursor:pointer; font-size:17px; }
  .verdict button[aria-pressed=true].y { background:var(--green-soft); border-color:var(--green); }
  .verdict button[aria-pressed=true].n { background:var(--red-soft); border-color:var(--red); }
  .verdict button[aria-pressed=true].q { background:#fdf3d9; border-color:var(--gold); }

  .fix { display:none; margin-top:10px; border-top:1px dashed var(--line); padding-top:10px; }
  .fix[data-open=true] { display:block; }
  .fix label { display:block; font-size:14.5px; color:var(--muted); margin:8px 0 3px; }
  .fix input, .fix textarea { width:100%; background:#fffdf8; border:1.5px solid var(--line);
        border-radius:8px; padding:9px 11px; font-size:17px; }
  .fix textarea { min-height:56px; resize:vertical; }
  .fix .hint { font-size:14px; color:var(--muted); margin-top:8px; }
  .saved { font-size:14.5px; color:var(--green); }

  .onaat { position:fixed; inset:0; background:rgba(36,31,26,.55); display:none;
           align-items:center; justify-content:center; padding:16px; z-index:50; }
  .onaat[data-open=true] { display:flex; }
  .card-oa { background:var(--card); border-radius:16px; max-width:560px; width:100%;
             padding:20px; max-height:90vh; overflow:auto; }
  .card-oa h2 { margin:0 0 8px; font-size:22px; }
  .card-oa p { margin:8px 0; font-size:16.5px; }
  footer { padding:0 16px 40px; max-width:900px; margin:0 auto; color:var(--muted); font-size:15px; }
  @media (max-width:600px) {
    .mg-line { font-size:22px; }
    header { padding:8px 12px 6px; }
    main { padding:10px 12px 120px; }
  }
  @media print { header, .tools, .fix, footer { display:none; } .row { break-inside:avoid; } }
</style>
</head>
<body>

<header>
  <div class="head-top">
    <h1>Fanitsiana ny votoaty — Salama!</h1>
    <p class="sub">__TOTAL__ entries · peruse, mark, correct. Everything is saved in this browser.</p>
  </div>
  <div class="progress" aria-hidden="true"><i id="bar"></i></div>
  <div class="bar">
    <input type="search" id="q" placeholder="Search Malagasy or English…" aria-label="Search">
    <select id="filter" aria-label="Filter">
      <option value="todo">Not judged yet</option>
      <option value="heard">Played, not judged</option>
      <option value="all">Everything</option>
      <option value="ok">Marked ✔ marina</option>
      <option value="wrong">Marked ✘ diso</option>
      <option value="unsure">Marked ?</option>
      <option value="fixed">Has a correction</option>
    </select>
    <label class="switch"><input type="checkbox" id="auto">
      <span>Listen mode: play it, press a mark, next one comes up</span></label>
    <button class="btn btn-small" id="testSound" type="button">Can I hear it?</button>
    <button class="btn btn-small" id="export" type="button">Export corrections</button>
    <button class="btn btn-small" id="resume" type="button">Resume</button>
    <span class="counter" id="counter"></span>
  </div>
  <div class="tabs" id="tabs"></div>
</header>

<details class="guide" open>
  <summary>Start here — and what to check (tap to close)</summary>
  <p class="order"><b>How to work:</b> switch on <b>Listen mode</b>, then just press
     <b>▶</b> and mark ✔ or ✘. Space plays, 1 = ✔, 3 = ✘, 2 = ?, and it moves on by itself.
     3,391 of the 3,843 entries have a recording; grammar examples and culture notes are
     text only (no clip), so those you read.</p>
  <p class="order"><b>Order that pays off fastest:</b>
     1) <b>Sentences</b> (196 lines — about one evening, and these are the only lines the learner
        will say to a real person) →
     2) <b>Phrases</b> (717) →
     3) <b>Words</b> (the taught ones come first) →
     4) <b>Grammar examples</b> and <b>Notes</b>.
     You do not have to finish. Anything you mark is saved the moment you press it.</p>
  <p class="order">Lamina tsara indrindra: <b>fehezanteny</b> aloha (196), dia <b>fomba fiteny</b>,
     dia <b>teny</b>, dia ohatra fitsipika sy fanamarihana. Tsy voatery vita daholo — ny voamarina
     dia voatahiry avy hatrany.</p>
  <ul>
    <li><b>Malagasy spelling</b> — official (Merina) orthography. The app teaches official Malagasy,
        with Tsimihety variants shown separately and labelled.</li>
    <li><b>The English meaning</b> — does it match what the Malagasy actually says? Watch for a
        gloss that drifted onto the wrong line.</li>
    <li><b>Would a Malagasy say it this way?</b> Especially in <i>sentences</i> and <i>phrases</i>.
        Unnatural but grammatical counts as ✘ — the learner will repeat it to a real person.</li>
    <li><b>Politeness</b> — <i>ianao</i> vs <i>ianareo</i>, <i>tompoko</i>, and whether a form is
        too familiar for an elderly visitor to use.</li>
    <li><b>Just press ▶ and listen.</b> Mark <b>✘</b> when the recording does not sound like the
        word — even if the written Malagasy is fine. That tells me the clip must be replaced.</li>
    <li><b>Just press ▶ and listen.</b> The phonetics are hidden on purpose — you are judging
        the sound, not a respelling. Ask: would a Malagasy say it like that? Is the stress on
        the right syllable? Does it sound like the real word at all?</li>
    <li><b>Notes</b> are English text quoting Malagasy — check the quotes and the cultural claims.</li>
    <li>Not sure? Mark <b>?</b> — that is a useful answer, and nothing gets changed silently.</li>
    <li>Only the ✔ mark changes the app: an entry you approve stops being labelled
        <i>(approx.)</i> and starts showing <b>✓ checked</b>.</li>
  </ul>
</details>

<main id="list" aria-live="polite"></main>

<footer>
  <p>Corrections never leave this browser until you press <b>Export corrections</b> and send the
     file back. Nothing here is uploaded anywhere.</p>
</footer>

<div class="onaat" id="onaat" role="dialog" aria-modal="true" aria-labelledby="oaTitle">
  <div class="card-oa">
    <h2 id="oaTitle">Exported</h2>
    <p id="oaBody"></p>
    <div class="bar" style="margin-top:14px">
      <button class="btn btn-primary" id="oaClose" type="button">Close</button>
    </div>
  </div>
</div>

<script>
var ROWS = __ROWS__;
var SECTION_NAMES = {
  sentences: 'Sentences',
  phrases: 'Phrases',
  words: 'Words',
  grammar: 'Grammar examples',
  notes: 'Culture notes'
};
var STORE = 'salama_proofread_v1';
var POS = 'salama_proofread_pos_v1';

// A sandboxed preview frame (and private mode in some browsers) refuses storage
// entirely. The sheet must still work there: marks live in memory and you are told
// to reopen the file in a real browser before doing serious work.
var persistOK = (function () {
  try { localStorage.setItem('salama_probe', '1'); localStorage.removeItem('salama_probe'); return true; }
  catch (e) { return false; }
})();

function load() {
  try { return JSON.parse(localStorage.getItem(STORE) || '{}'); } catch (e) { return {}; }
}
var marks = load();
var activeKey = null;

function save() {
  try { localStorage.setItem(STORE, JSON.stringify(marks)); } catch (e) {}
  paintCounter();
}

function esc(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ---------------- audio ---------------- */
// One reusable element: overlapping clips would be worse than none.
var audioBase = '__AUDIO_BASE__';
var player = new Audio();
var playerReady = false;
var nativeMode = false;     // programmatic play() was refused: use real <audio controls>
var audioNote = null;

function noteToUser(html, bad) {
  if (!audioNote) {
    audioNote = document.createElement('p');
    audioNote.className = bad ? 'audio-warn' : 'audio-tip';
    document.querySelector('header').appendChild(audioNote);
  }
  audioNote.className = bad ? 'audio-warn' : 'audio-tip';
  audioNote.innerHTML = html;
}

function srcFor(row) { return row && row.audio ? audioBase + row.audio : ''; }

function rowNode(key) {
  return document.querySelector('.row[data-key="' + key.replace(/"/g, '\\"') + '"]');
}

function markActive(key) {
  activeKey = key;
  var previous = document.querySelector('.row[data-active="true"]');
  if (previous && previous.getAttribute('data-key') !== key) {
    previous.setAttribute('data-active', 'false');
  }
  var article = rowNode(key);
  if (article) article.setAttribute('data-active', 'true');
  return article;
}

// The reliable path: a real audio element with the browser's own controls. Used
// when the page is not allowed to start audio by itself (sandboxed frames,
// stricter autoplay policies) — the learner then presses the browser's play button.
function embedPlayer(row, article) {
  if (!article) return;
  var holder = article.querySelector('.listen');
  if (!holder) return;
  var existing = holder.querySelector('audio');
  if (existing) { existing.play().catch(function () {}); return; }
  var el = document.createElement('audio');
  el.controls = true;
  el.autoplay = true;
  el.preload = 'auto';
  el.src = srcFor(row);
  el.setAttribute('aria-label', 'Recording of ' + row.mg);
  el.addEventListener('error', function () {
    noteToUser('The browser cannot decode this clip. Try the copy at ' +
      '<b>http://localhost:8788/PROOFREAD.html</b> (see RESEARCH/PROOFREADING.md).', true);
  });
  holder.insertBefore(el, holder.firstChild);
  var attempt = el.play();
  if (attempt && attempt.catch) {
    attempt.catch(function () { noteToUser('Press the \u25B6 on the player below the phrase.', false); });
  }
}

var timer = null;

function playRow(row, slow) {
  if (!row) return;
  if (!row.audio) {
    noteToUser('That entry has no recording \u2014 it is text only. Judge it by reading.', false);
    return;
  }
  var article = markActive(row.key);
  if (timer) clearTimeout(timer);
  var mark = marks[row.key] || (marks[row.key] = {});
  if (!mark.heard) { mark.heard = true; save(); }

  if (nativeMode) {
    embedPlayer(row, article);
    if (autoMode()) scheduleNext(row.key);
    return;
  }

  player.pause();
  player.onended = null;
  player.src = srcFor(row);
  player.playbackRate = slow ? 0.7 : 1;
  var attempt = player.play();
  if (attempt && attempt.then) {
    attempt.then(function () {
      playerReady = true;
      if (autoMode()) player.onended = function () { timer = setTimeout(nextRow, 350); };
    }).catch(function (error) {
      // NotAllowedError = the page may not start audio on its own. Not a dead end:
      // hand the row a normal player and say so once.
      nativeMode = true;
      embedPlayer(row, article);
      noteToUser('This page is not allowed to start playback by itself, so the ' +
        'recording is in the player under the phrase \u2014 press its \u25B6. ' +
        '(' + (error && error.name ? error.name : 'blocked') + ')', false);
    });
  }
}

function autoMode() { return document.getElementById('auto').checked; }

function scheduleNext(key) {
  if (timer) clearTimeout(timer);
  timer = setTimeout(function () {
    var rows = rowsForView();
    var position = -1;
    for (var i = 0; i < rows.length; i++) { if (rows[i].key === key) { position = i; break; } }
    var following = rows[position + 1];
    if (!following) return;
    if (!rowNode(following.key)) { view.shown += view.step; render(); }
    playRow(following, false);
  }, 300);
}

function nextRow() {
  var rows = rowsForView();
  var position = -1;
  for (var i = 0; i < rows.length; i++) { if (rows[i].key === activeKey) { position = i; break; } }
  var following = rows[position + 1];
  if (!following) return null;
  if (!rowNode(following.key)) { view.shown += view.step; render(); }
  playRow(following, false);
  return following;
}

function stepActive(direction) {
  var rows = rowsForView();
  if (!rows.length) return null;
  var index = rows.indexOf ? rows.indexOf(null) : -1;
  index = -1;
  for (var i = 0; i < rows.length; i++) { if (rows[i].key === activeKey) { index = i; break; } }
  var next = rows[index + direction];
  if (!next) return null;
  if (!rowNode(next.key)) { view.shown += view.step; render(); }
  playRow(next, false);
  return next;
}

// Diagnostics the reviewer can actually act on.
function testSound() {
  var row = ROWS.filter(function (r) { return r.audio; })[0];
  if (!row) { noteToUser('No recordings in this file.', true); return; }
  noteToUser('Testing: ' + row.mg + ' \u2014 if you hear nothing, the browser is ' +
    'blocking sound for this page.', false);
  playRow(row, false);
}

/* ---------------- keyboard ---------------- */
document.addEventListener('keydown', function (event) {
  var tag = (event.target.tagName || '').toLowerCase();
  if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
  if (event.metaKey || event.ctrlKey || event.altKey) return;
  var rows = visibleRows();
  var current = null;
  for (var i = 0; i < rows.length; i++) { if (rows[i].key === activeKey) { current = rows[i]; break; } }
  if (event.key === ' ' || event.key === 'Enter') {
    event.preventDefault();
    if (current) { playRow(current, false); }
    else if (rows.length) { playRow(rows[0], false); }
    return;
  }
  if (event.key === 'j' || event.key === 'ArrowDown') { event.preventDefault(); stepActive(1); return; }
  if (event.key === 'k' || event.key === 'ArrowUp') { event.preventDefault(); stepActive(-1); return; }
  var map = { '1': 'ok', '2': 'unsure', '3': 'wrong' };
  var verdict = map[event.key];
  if (!verdict) return;
  if (!current && rows.length) current = rows[0];
  if (!current) return;
  event.preventDefault();
  var mark = marks[current.key] || (marks[current.key] = {});
  mark.verdict = verdict;
  save();
  if (autoMode()) {
    var position = rows.indexOf(current);
    var following = rows[position + 1];
    if (following) {
      if (!document.querySelector('[data-key="' + following.key.replace(/"/g, '\\"') + '"]')) {
        view.shown += view.step;
        render();
      }
      playRow(following, false);
    }
  } else {
    var node = document.querySelector('[data-key="' + current.key.replace(/"/g, '\\"') + '"]');
    if (node) {
      node.setAttribute('data-verdict', verdict);
      var buttons = node.querySelectorAll('[data-verdict]');
      for (var b = 0; b < buttons.length; b++) {
        buttons[b].setAttribute('aria-pressed',
          String(buttons[b].getAttribute('data-verdict') === verdict));
      }
    }
  }
});

document.getElementById('auto').addEventListener('change', function () {
  if (!autoMode()) { if (timer) clearTimeout(timer); player.onended = null; return; }
  var rows = visibleRows();
  var current = null;
  for (var i = 0; i < rows.length; i++) { if (rows[i].key === activeKey) { current = rows[i]; break; } }
  playRow(current || rows[0], false);
});

/* ---------------- export ---------------- */
function exportAll() {
  var byKey = {};
  ROWS.forEach(function (row) { byKey[row.key] = row; });
  var keys = Object.keys(marks).filter(function (k) {
    var m = marks[k];
    return m && (m.verdict || m.mg || m.en || m.note);
  });
  if (!keys.length) {
    document.getElementById('oaTitle').textContent = 'Nothing to export yet';
    document.getElementById('oaBody').textContent =
      'Mark a few entries first — ✔, ?, ✘ or a correction.';
    document.getElementById('onaat').setAttribute('data-open', 'true');
    return;
  }
  var header = ['key', 'section', 'original_mg', 'original_en', 'verdict',
                'corrected_mg', 'corrected_en', 'note'];
  var lines = [header.join('\t')];
  keys.sort().forEach(function (key) {
    var row = byKey[key] || { section: '', mg: '', en: '' };
    var m = marks[key];
    lines.push([key, row.section,
                (row.mg || '').replace(/\t/g, ' '),
                (row.en || '').replace(/\t/g, ' '),
                m.verdict || '',
                (m.mg || '').replace(/\t/g, ' '),
                (m.en || '').replace(/\t/g, ' '),
                (m.note || '').replace(/\n/g, ' ').replace(/\t/g, ' ')].join('\t'));
  });
  // Leading BOM: without it Excel/Sheets mangle Malagasy diacritics (à, ô, ñ).
  var blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/tab-separated-values' });
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'salama_corrections.tsv';
  document.body.appendChild(a);
  a.click();
  a.remove();

  var okCount = keys.filter(function (k) { return marks[k].verdict === 'ok'; }).length;
  var wrongCount = keys.filter(function (k) { return marks[k].verdict === 'wrong'; }).length;
  var fixCount = keys.filter(function (k) {
    var m = marks[k];
    return (m.mg && m.mg !== (byKey[k] || {}).mg) || (m.en && m.en !== (byKey[k] || {}).en);
  }).length;
  document.getElementById('oaTitle').textContent = 'Exported ' + keys.length + ' entries';
  document.getElementById('oaBody').innerHTML =
    '<b>salama_corrections.tsv</b> has been downloaded.<br>' +
    '✔ ' + okCount + ' correct · ✘ ' + wrongCount + ' wrong · ' +
    fixCount + ' with a rewritten text.<br><br>' +
    'Send that file back and every correction is applied to the course, then the ' +
    'audio is re-rendered for the entries whose text changed.';
  document.getElementById('onaat').setAttribute('data-open', 'true');
}

/* ---------------- boot ---------------- */
try {
  var saved = localStorage.getItem(POS);
  if (saved) view.section = saved;
} catch (e) {}
if (!persistOK) {
  var warn = document.createElement('p');
  warn.className = 'persist-warn';
  warn.innerHTML = '<b>This preview cannot save.</b> Marks work, but they live only in this ' +
    'tab and vanish on reload. Download <i>PROOFREAD.html</i> and open it in your browser ' +
    '(double-click it) for saving, Resume and Export to work.';
  document.querySelector('header').appendChild(warn);
}
render();
</script>
</body>
</html>
"""


def inline_audio(rows):
    """Swap every clip path for a data URI: one file that plays anywhere.

    Big (about 35 MB), so it is a separate opt-in page. It exists for the case
    where the sheet and the APP folder cannot be kept together — an emailed file,
    a sandboxed preview frame, a phone.
    """
    cache = {}
    for row in rows:
        path = row.get("audio")
        if not path:
            continue
        if path not in cache:
            full = os.path.join(BASE, "APP", path)   # paths are APP-relative
            try:
                with open(full, "rb") as handle:
                    cache[path] = "data:audio/mpeg;base64," + base64.b64encode(
                        handle.read()).decode("ascii")
            except OSError:
                cache[path] = ""
        row["audio"] = cache[path]
    return len([row for row in rows if row.get("audio")])


def main():
    data = load_content()
    rows = build_rows(data)
    payload = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    # Two copies of one page: the standalone one expects APP/ beside it; the copy
    # inside APP/ resolves the recordings relative to itself. Both are generated —
    # never hand-edit either.
    targets = [(OUT, "APP/"), (os.path.join(BASE, "APP", "PROOFREAD.html"), "")]
    for path, base in targets:
        html = (PAGE.replace("__ROWS__", payload)
                    .replace("__TOTAL__", str(len(rows)))
                    .replace("__AUDIO_BASE__", base))
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(html)

    counts = {}
    for row in rows:
        counts[row["section"]] = counts.get(row["section"], 0) + 1
    print("Wrote %s (%.1f MB) and APP/PROOFREAD.html"
          % (OUT, os.path.getsize(OUT) / 1048576))
    print("  with a recording: %d of %d rows"
          % (len([r for r in rows if r.get("audio")]), len(rows)))
    print("  " + " | ".join("%s: %d" % (name, counts.get(name, 0)) for name in
                            ("sentences", "phrases", "words", "grammar", "notes")))
    print("  total: %d entries" % len(rows))

    if "--inline-audio" in sys.argv:
        inlined = inline_audio(rows)
        payload = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
        path = os.path.join(BASE, "PROOFREAD_AUDIO.html")
        html = (PAGE.replace("__ROWS__", payload)
                    .replace("__TOTAL__", str(len(rows)))
                    .replace("__AUDIO_BASE__", ""))
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(html)
        print("  wrote %s (%.0f MB) with %d clips inside"
              % (path, os.path.getsize(path) / 1048576, inlined))
    return 0


if __name__ == "__main__":
    sys.exit(main())
