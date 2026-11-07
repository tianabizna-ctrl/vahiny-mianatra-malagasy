# Salama! — Learn Malagasy

A static, installable web app for absolute beginners learning Malagasy. No build
step, no dependencies, no server logic.

<!-- counts:start -->
**Current build:** 2478 dictionary entries, 717 phrases, 33 dialogues, 27 grammar topics, 161 culture notes, 36 sessions over 12 weeks. Pronunciation is written for 100% of words and phrases.
<!-- counts:end -->

The block above is written by `RESEARCH/build_app_data.py`; do not edit it by hand.

## Run it

```bash
cd APP
python3 -m http.server 8788
# open http://127.0.0.1:8788
```

Opening `index.html` directly also works; only the offline cache needs `http(s)`.

## Screens

| Route | What it does |
|---|---|
| `#/today` | The next session (with its dialogue preview) and the due review count |
| `#/course`, `#/course/3` | The 12-week outline and one week's three sessions |
| `#/session/w1s2` | Runner: warm-up dialogue → new words → roleplay → finish |
| `#/review`, `#/review/round` | A bounded 10 or 15 card round: reveal the meaning, then rate it |
| `#/quiz` | Multiple choice practice (5, 10 or 15 questions) |
| `#/reference/phrases` etc. | Phrases, words, grammar, culture, pronunciation |
| `#/dialogue/:id` | One dialogue transcript, line by line audio |
| `#/progress` | Sessions, weeks, word counts, quiz history |
| `#/settings` | Text size, speaking speed, voice, syllable mode, export/restore and reset |

## Files

```
index.html              shell, inline SVG icon sprite, script order
styles.css              design tokens + all styling (no framework)
app.js                  router and header controls
js/core.js              stored state, spaced repetition, progress selectors
js/speech.js            recorded clips, Malagasy→fallback-voice adapter, syllable shaping
js/ui.js                escaping, icons, toast, reference tabs
js/views/*.js            one file per screen
data/content.js         generated — do not edit by hand
media/audio/            the 14 Peace Corps Malagasy recordings
manifest.webmanifest    install metadata
sw.js                   offline cache (shell on install, audio on first play)
```

## Content pipeline

`data/content.js` is generated. Edit the generator, not the output. From the repository root:

```bash
python3 RESEARCH/build_app_data.py     # rebuilds APP/data/content.js
python3 RESEARCH/validate_content.py   # fails on bad pairs, missing audio, etc.
```

* `RESEARCH/build_app_data.py` — assembles vocabulary, phrases, dialogues, grammar, culture, the 12-week curriculum, session → dialogue/audio mappings and topic shelves.
* `RESEARCH/content_quality.py` — the repair rules: stripping contaminated glosses, detecting English in the Malagasy column, splitting dialect annotations, consolidating 30 phrase groups into 15, and generating labelled approximate pronunciations.

Repairs are reported on every build (gloss segments fixed, phrases dropped, pronunciations generated).

## Audio

Three layers, tried in this order:

1. **A rendered Malagasy clip** — `media/audio/words/`, `phrases/` and `lines/`, written
   by `RESEARCH/render_audio.py` from Meta's MMS Malagasy model. This build ships
   **2,466 word clips, 711 phrase clips and 196 dialogue-line clips** (~19 MB, mono
   mp3, cached on first play by the service worker). This is the only layer that is real
   Malagasy rather than an approximation, and it covers everything a session uses.
2. **The best installed voice**, rewritten for that language: Malagasy `o` becomes
   French `ou`, `j` becomes `dz`, `ao` becomes `ô`, and the word is handed over one
   syllable at a time so a French voice neither nasalises `an/on/in` nor swallows a
   final vowel. Voice order is `mg, fr, ro, it, es, pt, ca, en`; Romanian is ahead of
   Italian because it pronounces `h` and has `ț` = [ts].
3. **Session recordings** — the public-domain Peace Corps Malagasy Language Lessons in
   `media/audio/` — are the reference for listening, and are always played as recorded.

Every generated pronunciation is labelled *approx.* in the UI. Nothing has been checked
by a native speaker yet: `RESEARCH/pron_qa.py` builds a review sheet for that, and
`RESEARCH/PRONUNCIATION.md` records what is settled and what is still inference.

Settings offers a slower rate, a per-word **Syllables** button, and a voice picker.

## Known limits

* No phone, tablet or desktop ships an *installed* Malagasy voice (checked November
  2026). 18 entries have no clip (their ids collide on a filename) and use the fallback.
* The clips come from a statistical model, not a person: stress on long phrases and the
  reading of abbreviations can still be wrong, and none of it has been checked by a
  native speaker yet.
* The adapter cannot reproduce `tr` [ʈʂ] / `dr` [ɖʐ] with a French voice, or French
  final-syllable stress. Rendered clips solve this; nothing else does.
* Stress is penultimate by default. Words where the hand table and the printed
  dictionary disagree (currently 3) are listed in `RESEARCH/pron_qa.html`.
* Progress lives in `localStorage`. Settings → Export progress writes a backup file and
  Restore from file reads it back.

## Checks

```bash
python3 RESEARCH/build_app_data.py        # regenerate data/content.js
python3 RESEARCH/validate_content.py      # content + pronunciation gates, fails loudly
python3 RESEARCH/test_pronunciation.py    # 28 unit tests on the rules
python3 RESEARCH/check_parity.py          # Python and JS adapters must agree
node RESEARCH/smoke_app.js                # every screen renders and every handler runs
```
