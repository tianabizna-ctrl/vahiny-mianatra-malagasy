# Salama! v3.4 — the app now speaks with a Malagasy voice

v3.2 shipped audio in a machine voice that a Malagasy speaker could hear was wrong.
v3.4 replaces it: **every word, phrase and dialogue line in the course is now spoken by
Abidi**, the Malagasy text-to-speech service from artifisialy.mg.

## The render

| | |
| --- | --- |
| clips rendered | **3,377** — 2,478 words · 717 phrases · 182 dialogue sentences |
| failures | 0 (one phrase needed a retry, then succeeded) |
| size | 28.6 MB at 32 kbps mono, 22 kHz source |
| wired into the app | **3,367 Abidi** clips, 6 still MMS |
| render time | ~2.5 hours at ~30 clips/minute |
| service | Abidi, artifisialy.mg — credited in the app's attribution block |

Twelve dialogue "lines" were deliberately **not** rendered because they are not spoken
Malagasy — they are placeholders copied from the Peace Corps intro packs
(`Anarako ........ (name) ........`, `(or give a kabary)`, `MISAOTRA / MAZOTOA`). They
keep their old MMS clip or no clip, and `validate_content.py` now warns about all 12 so
they can be rewritten.

## Voice choice is per entry, not per project

Your listening pass found Abidi better overall but **MMS correct for "veloma"**. That
correction is permanent:

```json
// RESEARCH/VOICE_MAP.json
{"word:veloma": "mms", "phrase:rpb_veloma": "mms"}
```

- default: Abidi wherever a clip exists, MMS everywhere else;
- `--voice=mms` ignores Abidi completely (the old app, exactly);
- an override is honoured even when the Abidi clip exists, and every build prints
  `1 kept on mms by VOICE_MAP.json`;
- keys are the same as the review sheet's, so any future judgement ("this one sounds
  wrong") is a one-line change, not a re-render.

## Attribution

The app's `attribution` block now names both voices:

- **abidi** — "Word, phrase and dialogue pronunciations are synthesised with Abidi, the
  Malagasy text-to-speech service by artifisialy.mg (abidi.artifisialy.mg)."
- **mms** — "A few pronunciation clips use the Meta MMS Malagasy voice
  (facebook/mms-tts-mlg, CC BY-NC 4.0), kept where it reads an entry better."

## What else changed

- `RESEARCH/abidi_render.py` is now a real batch tool: `--concurrency`, `--delay`,
  `--limit`, `--list`, per-thread cookie jars, three retries on an upstream hiccup, and
  a RIFF check so an HTTP 200 carrying `{"error": "Upstream unreachable"}` can never
  become a silent clip. Taught vocabulary renders first.
- `RESEARCH/finish_app.sh` — one command for the whole switchover (sweep, rebuild,
  check chain, regenerate the review sheet, package). Idempotent.
- `RESEARCH/validate_content.py` warns about the 12 placeholder dialogue lines.
- `ABIDI_SAMPLE.html` stays small (0.33 MB, 13 comparisons) — it is a decision page,
  not a copy of the course.
- `PROOFREAD_AUDIO.html` (39 MB) now carries the Abidi clips inside it, so the review
  sheet plays the voice the learner actually hears, with no folder or server.

## Check chain

```
28 pronunciation tests            OK
adapters agree on 29 words x 8    OK
validate_content.py               content OK (2 advisory warnings)
smoke_app.js                      14 routes rendered, speech layer exercised
zip extract + smoke               OK, 0 dangling audio references
```

## Still open

1. **12 placeholder dialogue lines** need real Malagasy from you.
2. Your review of the 3,843 entries is unaffected and still the highest-value next
   step; the sheet already plays the new voice.
3. **NarrationBox / Google Chirp 3** — recorded in `RESEARCH/NARRATIONBOX.md` as the
   only plausible alternative (~$1.52 for the whole corpus) if you ever want a change.
