# Salama! 3.2 — finished build

**Date:** 6 November 2026 · **Version:** 3.1 → 3.2
**All checks green:** 28 unit tests · Python↔JS adapter parity · content validation ·
headless smoke test (14 routes, 6 interaction flows) · every JS file parses.

---

## What changed since 3.1

### 1. The audio is now actually Malagasy

The last blocker was that words were still spoken by a French (or other) voice doing its
best with Malagasy spelling. That is gone: **3,373 clips are rendered with Meta's MMS
Malagasy model** (`facebook/mms-tts-mlg`) and shipped inside the app.

| Clip set | Count | Where | Size |
|---|---|---|---|
| Words | 2,466 of 2,478 | `APP/media/audio/words/` | 18 MB |
| Phrases | 711 of 717 | `APP/media/audio/phrases/` | 2 MB |
| Dialogue lines | 196 of 196 | `APP/media/audio/lines/` | 2 MB |

* 16 kHz mono, 32 kbps mp3 (~6 KB per word). Service worker caches each clip on first
  play, so a session's audio is offline after it has been heard once.
* Reproduce with `python3 RESEARCH/render_audio.py --i-accept-noncommercial --what all --mp3`
  (≈45 min on one CPU; resumable). `--list` writes a recording script instead, for a
  native speaker.
* Licence: CC BY-NC 4.0, non-commercial — attribution now sits in the app footer, the
  Settings → About panel and both READMEs. You confirmed personal/free use.
* What this fixes that no respelling could: `tr`/`dr` as [ʈʂ]/[ɖʐ], a pronounced `h`,
  Malagasy stress, clean final vowels.
* What it does not fix: it is a statistical model reading text, so long-phrase stress and
  abbreviations can still be wrong, and nobody has reviewed it.

**18 entries deliberately have no clip.** Twelve vocabulary and six phrase ids slug to the
same filename (`mba` vs `mba_`, `Misy … ve?` vs `Misy ___ ve?`). Rather than let one
entry play another's audio, they fall back to the adapted device voice. The build reports
this and `audio_slug()` in `content_quality.py` keeps every filename filesystem-safe.

### 2. Installable as a real app

* PNG icons at 180/192/512 generated from the SVG, plus a **maskable** 512 icon, so the
  icon is not letterboxed on Android.
* `apple-touch-icon` and `apple-mobile-web-app-*` meta for an iOS home-screen install.
* Service worker pre-caches the icons; cache name bumped to `salama-v3.2.0`.

### 3. Three more app fixes

* **Spaced repetition was too generous.** Rating a brand-new card "I knew it" promoted it
  a box in the same breath as introducing it — and a correct quiz answer did the same — so
  a word seen once could read as "known" without ever being recalled. A card's first
  rating now only establishes it (`reps` counter); promotion starts on the second.
* **Review spoke the answer twice** (reveal handler + autoplay after re-render). Now
  voice plays once per card: on arrival when the prompt is Malagasy, on reveal when the
  prompt was the English meaning.
* **"Syllables" now stretches the real recording** (0.65× playback) instead of switching
  to a synthetic reading, so slow mode no longer changes the pronunciation.
* Dialogue lines carry their own written hint, shown under each line in the session runner
  and the dialogue view — the roleplay was the one place with no pronunciation at all.
* 26 teacher-written hints that carried no stress mark now get one, without a single
  letter the teacher chose being changed (only capitalisation). 6 multi-word hints remain
  unstressed and are listed as warnings.

### 4. New files

| File | Purpose |
|---|---|
| `README.md` | package-level guide: what this is, how to run, the checks, honest audio notes |
| `AUDIO_SAMPLE.html` | 16 clips embedded as data URIs — plays in any sandbox, sendable as one file to a Malagasy speaker |
| `RESEARCH/audio_sample.py` | regenerates that page |
| `RESEARCH/SPEAKER_QUESTIONS.md` | the ten questions worth asking a native speaker first |
| `RESEARCH/PRONUNCIATION.md` §5b | what the rendered audio covers, and what it still cannot fix |

---

## Verification output

```
28 tests OK
adapters agree on 29 words x 8 languages
pronunciation coverage: 100% (2441 generated, labelled approximate)
rendered clips: 2466 words, 711 phrases, 196 lines
content OK
smoke OK: 14 routes rendered and mounted, speech layer and six interaction flows exercised
all js ok
```

## How to try it

```bash
cd APP && python3 -m http.server 8788     # open http://127.0.0.1:8788
```

Or open `AUDIO_SAMPLE.html` first and just listen to the words.

## What a native speaker should still decide

Nothing here has been heard by a Malagasy speaker. The three stress conflicts
(`dokotera 3/2`, `lehibe 3/1`, `mipetraka 2/3`) are unresolved, and the model's phrase
stress is unverified. `RESEARCH/SPEAKER_QUESTIONS.md` covers those in fifteen minutes;
`RESEARCH/pron_qa.html` covers all 3,195 entries and exports a spreadsheet. When those
verdicts arrive, wrong stress goes into `CURATED_STRESS` (and the tests catch anything
that breaks), and words the model mangles go on the recording list.

That is the only remaining work, and it needs a person, not code.
