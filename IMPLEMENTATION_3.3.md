# Salama! v3.3 — the native-speaker review loop

v3.2 shipped the audio. v3.3 makes the course **correctable by a Malagasy speaker**
without touching code.

## What you do

0. **Judge by ear.** Open `PROOFREAD_AUDIO.html` and press **▶ Hevero** on any row:
   it plays the real clip, not a phonetic respelling. Switch on **Listen mode** and the
   job becomes: hear it, press ✔ or ✘, next one plays by itself. Space plays, 1 = ✔,
   2 = ?, 3 = ✘, j/k step. 3,373 of the 3,843 rows have a recording; the 470 that do
   not (grammar examples, culture notes, a handful of unwireable duplicates) are read
   as text and say so on the row.
1. Or start from `PROOFREAD.html` (0.8 MB) with `APP/` beside it.
2. Mark rows: **✔ marina** / **? tsy fantatro** / **✘ diso**, and type corrected
   Malagasy or English where the text is wrong.
3. Press **Export corrections** → `salama_corrections.tsv`.
4. Send that file back.

Start with **Sentences** (196 dialogue lines — one evening). Those are the only
lines the learner says out loud to a real person, so they carry the most risk.

## What happens to your marks

```bash
python3 RESEARCH/apply_corrections.py salama_corrections.tsv   # merge, keeps earlier batches
python3 RESEARCH/build_app_data.py                             # rebuild the app
python3 RESEARCH/validate_content.py                           # gate
python3 RESEARCH/render_audio.py --mp3 --force-changed          # only the clips whose text changed
```

- **✔** → the entry gets `pron_verified: true` and loses `pron_approx`. In the app
  the *(approx.)* label is replaced by **✓ checked**, so the learner can see which
  hints a Malagasy speaker vouched for.
- **Typed text** → replaces the course text; the original is kept as `mg_original` /
  `en_original`, and the build prints `correction wins …` for every override.
  Your text always beats the source pack, the dictionary and the rules.
- **✘ with no rewrite** → recorded as `pron_disputed` and reported by the validator:
  *the clip must be replaced*, the text is left alone. Nothing is guessed on your behalf.
- **?** → stored, app unchanged.

## Guard rails

- A TSV whose `corrected_en` repeats `original_en` etc. is treated as a shifted
  spreadsheet column and refused, not applied. An English sentence silently
  replacing a Malagasy one is the one failure worth being paranoid about.
- Keys that no longer exist in the build are skipped and reported, never guessed.
- `CORRECTIONS.json` is the only record of what you decided and why — keep it.
- Exports carry a UTF-8 BOM so Excel and Google Sheets keep `à ô ñ` intact; the
  loader reads BOM and non-BOM alike.
- In the sandboxed in-app preview, browser storage is unavailable; the page says so
  and works in memory. Download the file and open it locally for real use.

## Re-rendering audio

`APP/media/audio/manifest.json` stores a hash of the text behind each clip.
`--force-changed` therefore re-renders exactly the entries you rewrote — verified on
a one-word edit: 1 clip queued, 3,390 untouched. Nine clip names are shared by two
entries; the app does not wire those (they use the fallback voice), so the renderer
leaves them alone.

## Numbers

| | |
| --- | --- |
| review rows | 3,843 (sentences 196 · phrases 717 · words 2,478 · grammar 291 · notes 161) |
| rows with a playable recording | 3,373 (all sentences, phrases and wired words) |
| audio clips | 3,373 (words 2,466 · phrases 711 · lines 196) |
| check chain | 28 pronunciation tests · parity 29×8 · content OK · smoke 14 routes |
