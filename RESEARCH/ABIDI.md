# Abidi — the Malagasy TTS at artifisialy.mg

`https://abidi.artifisialy.mg/inference/` is a Malagasy text-to-speech service run by
**artifisialy.mg**. It is a real Malagasy voice, not an English model reading Malagasy
letters, which is why it sounds right to you and the MMS voice does not.

## What it is, technically

The public page synthesises through a JSON endpoint:

```
GET  /inference/                       -> sets a csrftoken cookie
POST /inference/api/ephemeral-token/   -> {"token": "...", "expires_in": 120}
POST /inference/api/tts/               -> audio/wav, 22 050 Hz, 16-bit mono
     body: {"text": "…", "rythme": 1, "fiovan": 1, "angola": 1}
     headers: X-CSRFToken, X-API-TOKEN: 1234, X-ABIDI-SIGN: <token>
```

Measured from this machine: 1.4–6.4 s of audio per request, ~2–5 s of latency,
WAV out. `RESEARCH/abidi_render.py` speaks exactly this protocol.

## Decision: Abidi is the voice

You listened to `ABIDI_SAMPLE.html` and judged Abidi better, with one correction:
**MMS reads "veloma" correctly.** So the choice is per entry, not per project:

- `RESEARCH/VOICE_MAP.json` pins `word:veloma` and `phrase:rpb_veloma` to MMS;
- `build_app_data.py` uses Abidi wherever a clip exists, MMS everywhere else;
- `--voice=mms` ignores Abidi entirely if you ever want the old app back.

## What exists now

- **205 clips** rendered into `APP/media/audio_abidi/`: **all 196 dialogue sentences**,
  7 sample words and 2 sample phrases (32 kbps mono mp3, ~5 MB). 0 failures.
- The review sheet now plays **Abidi for every sentence**, so your listening pass
  judges the voice the learner will actually hear.
- Measured from this machine: 2–6 s of audio per request, ~5–13 s per request of
  latency, 4 parallel workers render ~34 clips/minute. Reliable enough that 196
  sentences finished with no failures; the service does throw occasional
  `{"error": "Upstream unreachable"}` with HTTP 200, which the renderer now detects
  and retries (three attempts, then it reports and moves on).
- `RESEARCH/abidi_render.py` — the renderer:
  `--sample`, `--limit N`, `--what words|phrases|lines|all`, `--delay`, `--list`.
  It skips anything already rendered, refuses to run fast on a large batch, stops on
  the first refusal, and keeps a manifest so nothing is ever requested twice.
- `RESEARCH/abidi_sample_page.py` — builds `ABIDI_SAMPLE.html` (both voices inlined,
  one row per entry, plays from a double-click).

## Usage

The service is used here as intended: one request at a time per clip, nothing
requested twice, and the app credits artifisialy.mg in its own attribution block.
The renderer is deliberately gentle (`--delay 1`, `--concurrency 6`, retries instead
of hammering), because a free beta should not have to absorb a flood.

## Rendering the rest

```bash
python3 RESEARCH/abidi_render.py --what words --concurrency 4 --delay 1
python3 RESEARCH/abidi_render.py --what phrases --concurrency 4 --delay 1
python3 RESEARCH/build_app_data.py
python3 RESEARCH/validate_content.py && node RESEARCH/smoke_app.js
```

2,471 words + 709 phrases remain ≈ 3,180 requests. At the measured rate that is
about 95 minutes. It is still someone's free beta, so the note below still wants
sending before that run — the 196 sentences were done as a working proof, not as a
licence to take the whole thing.

A partial render is always safe: Abidi where a clip exists, MMS for the rest, and
`VOICE_MAP.json` for the exceptions.

## What still needs a decision

1. ~~Attribution~~ — done: the app's `attribution` block, `README.md` and
   `APP/README.md` credit artifisialy.mg.
2. **Mixed voices within one lesson.** Until the words and phrases are rendered, a
   session plays Abidi sentences next to MMS vocabulary. It is honest but uneven — the
   fix is finishing the render, not hiding it.
3. **How far to go.** 196 sentences done; 3,180 clips left. See `NARRATIONBOX.md` for
   the alternative route (Google Chirp 3, ~$1.52 for the whole corpus, needs a test).

## Also fixed: the silent player

Playback failed because browsers may refuse page-initiated audio (the preview frame
is sandboxed). The review sheet now:

- tries normal playback, and on refusal swaps in a **real `<audio controls>` player**
  under the phrase and says so once;
- has a **"Can I hear it?"** button in the header that plays one clip and reports
  whether sound is blocked;
- keeps autoplay-on-end only while normal playback is allowed.

If the sheet still says nothing, the most reliable arrangement is the served copy:
`cd APP && python3 -m http.server 8788` then open `http://localhost:8788/PROOFREAD.html`.
