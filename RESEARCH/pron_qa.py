#!/usr/bin/env python3
"""Build a review sheet a native speaker can work through in one sitting.

    python3 RESEARCH/pron_qa.py            # writes RESEARCH/pron_qa.html

The page is self-contained (inline CSS, no network) so it opens from Drive or a
USB stick. Each row speaks the *adapted* string through the reviewer's own
device voice, exactly as the app would, and records a verdict in localStorage.
"Export TSV" gives you the verdicts back; feed the ✔ rows into
CURATED_STRESS and the ✘ rows to render_audio.py or a recording session.

Order of work in the sheet:
  1. Conflicts — the hand table and the printed dictionary disagree.
  2. Rule-only — stress guessed by the default penultimate rule.
  3. Everything else.
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "RESEARCH"))
import pronunciation as pr

DICT_DOCX = os.path.join(BASE, "MALAGASY ASSETS",
                         "malagasy-english-english-malagasy-dictionary-and-phrasebook-078180843x.docx")
OUT = os.path.join(BASE, "RESEARCH", "pron_qa.html")


def load_content():
    path = os.path.join(BASE, "APP", "data", "content.js")
    raw = open(path, encoding="utf-8").read()
    return json.loads(raw[raw.index("{"):raw.rindex("}") + 1])


def build_rows(data):
    conflicts = {word for word, _, _ in pr.stress_conflicts(DICT_DOCX)}
    rows = []
    for kind, items in (("word", data["vocabulary"]), ("phrase", data["phrases"])):
        for item in items:
            mg = item.get("mg", "")
            if not mg:
                continue
            rows.append({
                "id": item.get("id", ""),
                "kind": kind,
                "mg": mg,
                "en": item.get("en", ""),
                "pron": item.get("pron") or "",
                "source": item.get("pron_source") or "none",
                "fr": pr.adapt(mg, "fr"),
                "ro": pr.adapt(mg, "ro"),
                # Word-level only: a phrase containing a conflicting word is
                # not itself a conflict.
                "conflict": kind == "word" and mg.strip().lower() in conflicts,
            })
    order = {"conflict": 0, "rule": 1, "dictionary": 2, "phrase": 3, "teacher": 4, "single": 5}
    rows.sort(key=lambda r: (order.get("conflict" if r["conflict"] else r["source"], 6),
                             0 if r["kind"] == "word" else 1, r["mg"]))
    return rows


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Salama! — pronunciation review</title>
<style>
  :root { --ink:#241f1a; --paper:#faf6ef; --line:#d8ccb8; --green:#14603a;
          --gold:#87550f; --red:#8c2f1e; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--paper); color:var(--ink);
         font:18px/1.5 -apple-system, "Segoe UI", Roboto, sans-serif; }
  header { position:sticky; top:0; background:var(--paper); z-index:5;
           border-bottom:2px solid var(--line); padding:14px 20px; }
  h1 { font-size:22px; margin:0 0 6px; }
  .bar { display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
  button, select, input[type=search] {
    font:inherit; padding:8px 12px; border:2px solid var(--line);
    background:#fff; color:inherit; border-radius:8px; min-height:44px; }
  button { cursor:pointer; }
  button[aria-pressed=true] { border-color:var(--green); background:#e8f2ec; }
  .row { display:grid; grid-template-columns:1fr auto; gap:10px;
         padding:10px 20px; border-bottom:1px solid var(--line); }
  .mg { font-size:22px; font-weight:600; }
  .hint { color:var(--gold); font-variant:small-caps; letter-spacing:.02em; }
  .en { color:#5b5044; font-size:16px; }
  .chip { display:inline-block; font-size:12px; text-transform:uppercase;
          letter-spacing:.06em; border:1px solid var(--line); border-radius:99px;
          padding:2px 8px; color:#5b5044; }
  .chip.conflict { border-color:var(--red); color:var(--red); }
  .tools { display:flex; gap:6px; align-items:center; }
  .verdicts { display:flex; gap:4px; }
  .verdicts button { padding:4px 10px; min-height:40px; }
  .verdicts button.yes[aria-pressed=true] { background:#dff0e4; border-color:var(--green); }
  .verdicts button.no[aria-pressed=true]  { background:#f7e0dc; border-color:var(--red); }
  footer { padding:24px 20px 80px; color:#5b5044; font-size:15px; }
  .count { font-variant-numeric:tabular-nums; }
  @media (max-width:640px) { .row { grid-template-columns:1fr; } }
</style>
</head>
<body>
<header>
  <h1>Pronunciation review — __TOTAL__ entries</h1>
  <p style="margin:0 0 10px;font-size:16px">
    Press ▶ to hear it the way the app will say it. Mark ✔ if it is close enough
    to correct Malagasy, ✘ if it is wrong, ? if you are unsure. Then press
    <strong>Export TSV</strong> and send the file back.
  </p>
  <div class="bar">
    <input type="search" id="q" placeholder="Search Malagasy or English" style="min-width:220px">
    <select id="filter">
      <option value="conflict">Conflicts first (__CONFLICTS__)</option>
      <option value="rule">Rule-only stress</option>
      <option value="todo">Not marked yet</option>
      <option value="bad">Marked wrong</option>
      <option value="all" selected>Everything</option>
    </select>
    <span class="count" id="count"></span>
    <button id="export">Export TSV</button>
    <button id="clear">Clear marks</button>
  </div>
</header>
<main id="list"></main>
<footer>
  <p>Voice: <span id="voice">checking…</span></p>
  <p>The left column is what the learner sees; the buttons speak the rewritten
     string (<code>fr</code> and <code>ro</code> adaptations) because that is
     what the browser voice receives. Nothing here is uploaded anywhere —
     marks live in this browser's localStorage.</p>
</footer>
<script>
var ROWS = __ROWS__;
var STEP = 150, shown = STEP;
var marks = JSON.parse(localStorage.getItem('salama_pron_qa') || '{}');

function esc(v){return String(v==null?'':v).replace(/&/g,'&amp;').replace(/</g,'&lt;')
  .replace(/>/g,'&gt;').replace(/"/g,'&quot;');}

var voices = [];
function loadVoices(){
  voices = window.speechSynthesis ? window.speechSynthesis.getVoices() : [];
  var fr = voices.filter(function(v){return /^fr/i.test(v.lang);})[0];
  var ro = voices.filter(function(v){return /^ro/i.test(v.lang);})[0];
  document.getElementById('voice').textContent =
    'French ' + (fr ? fr.name : 'not installed') +
    ' · Romanian ' + (ro ? ro.name : 'not installed');
}
if (window.speechSynthesis){
  loadVoices();
  if (window.speechSynthesis.addEventListener) {
    window.speechSynthesis.addEventListener('voiceschanged', loadVoices);
  }
}
function speak(text, lang){
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  var u = new SpeechSynthesisUtterance(text);
  var match = voices.filter(function(v){return v.lang.toLowerCase().indexOf(lang)===0;})[0];
  if (match) { u.voice = match; u.lang = match.lang; } else { u.lang = lang + '-FR'; }
  u.rate = 0.8;
  window.speechSynthesis.speak(u);
}

function passes(row){
  var mark = marks[row.id];
  var f = document.getElementById('filter').value;
  if (f === 'conflict') return row.conflict;
  if (f === 'rule') return row.source === 'rule';
  if (f === 'todo') return !mark;
  if (f === 'bad') return mark === 'no';
  return true;
}

function rowHtml(row){
  var mark = marks[row.id] || '';
  var q = document.getElementById('q').value.trim().toLowerCase();
  return '<div class="row" data-id="' + esc(row.id) + '">' +
    '<div>' +
      '<div class="mg" lang="mg">' + esc(row.mg) + '</div>' +
      (row.pron ? '<div class="hint">' + esc(row.pron) + '</div>' : '') +
      '<div class="en">' + esc(row.en) + '</div>' +
      '<span class="chip ' + (row.conflict ? 'conflict' : '') + '">' +
        esc(row.conflict ? 'conflict' : row.source) + '</span>' +
      '<span class="chip">' + esc(row.kind) + '</span>' +
    '</div>' +
    '<div class="tools">' +
      '<button data-play="fr" title="French adaptation">▶ fr</button>' +
      '<button data-play="ro" title="Romanian adaptation">▶ ro</button>' +
      '<div class="verdicts">' +
        '<button class="yes" data-mark="yes" aria-pressed="' + (mark==='yes') + '">✔</button>' +
        '<button data-mark="?"   aria-pressed="' + (mark==='?') + '">?</button>' +
        '<button class="no"  data-mark="no"  aria-pressed="' + (mark==='no') + '">✘</button>' +
      '</div>' +
    '</div>' +
  '</div>';
}

function render(){
  var q = document.getElementById('q').value.trim().toLowerCase();
  var rows = ROWS.filter(function(r){
    if (!passes(r)) return false;
    if (!q) return true;
    return r.mg.toLowerCase().indexOf(q) !== -1 || r.en.toLowerCase().indexOf(q) !== -1;
  });
  document.getElementById('count').textContent =
    rows.length + ' shown · ' + Object.keys(marks).length + ' marked';
  document.getElementById('list').innerHTML =
    rows.slice(0, shown).map(rowHtml).join('') +
    (rows.length > shown ? '<div class="row"><button id="more">Show ' +
      Math.min(STEP, rows.length - shown) + ' more</button></div>' : '');
}

document.addEventListener('click', function(event){
  var target = event.target.closest('button');
  if (!target) return;
  var rowNode = target.closest('.row');

  if (target.id === 'more') { shown += STEP; render(); return; }
  if (target.id === 'clear') {
    if (!confirm('Clear every mark in this browser?')) return;
    marks = {}; localStorage.setItem('salama_pron_qa', '{}'); render(); return;
  }
  if (target.id === 'export') { exportTsv(); return; }

  if (!rowNode) return;
  var id = rowNode.getAttribute('data-id');
  var row = ROWS.filter(function(r){ return r.id === id; })[0];

  if (target.hasAttribute('data-play')) {
    var which = target.getAttribute('data-play');
    speak(row[which], which);
    return;
  }
  if (target.hasAttribute('data-mark')) {
    var value = target.getAttribute('data-mark');
    if (marks[id] === value) delete marks[id]; else marks[id] = value;
    localStorage.setItem('salama_pron_qa', JSON.stringify(marks));
    var buttons = rowNode.querySelectorAll('[data-mark]');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute('aria-pressed',
        String(buttons[i].getAttribute('data-mark') === marks[id]));
    }
    document.getElementById('count').textContent =
      Object.keys(marks).length + ' marked';
  }
});

document.getElementById('q').addEventListener('input', function(){ shown = STEP; render(); });
document.getElementById('filter').addEventListener('change', function(){ shown = STEP; render(); });

function exportTsv(){
  var lines = ['id\\tkind\\tmg\\ten\\tpron\\tsource\\tconflict\\tverdict'];
  ROWS.forEach(function(r){
    lines.push([r.id, r.kind, r.mg, r.en, r.pron, r.source,
                r.conflict ? 'yes' : '', marks[r.id] || ''].join('\\t'));
  });
  var blob = new Blob([lines.join('\\n')], {type:'text/tab-separated-values'});
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'pron_qa_verdicts.tsv';
  document.body.appendChild(a); a.click(); a.remove();
}

render();
</script>
</body>
</html>
"""


def main():
    data = load_content()
    rows = build_rows(data)
    conflicts = sum(1 for r in rows if r["conflict"])
    html = (PAGE.replace("__ROWS__", json.dumps(rows, ensure_ascii=False))
                .replace("__TOTAL__", str(len(rows)))
                .replace("__CONFLICTS__", str(conflicts)))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    size = os.path.getsize(OUT) // 1024
    print("Wrote %s (%d KB)" % (OUT, size))
    print("  %d entries, %d conflicts flagged, %d rule-only"
          % (len(rows), conflicts, sum(1 for r in rows if r["source"] == "rule")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
