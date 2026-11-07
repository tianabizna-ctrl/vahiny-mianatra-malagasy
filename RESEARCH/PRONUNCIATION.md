# Malagasy pronunciation — the evidence behind the app's claims

This is the note `pronunciation.py` cited twice before it existed. It records what
was actually consulted, what was inferred, and what is still unverified. Update it
whenever a rule changes.

**Status:** rules implemented and unit-tested; **2,466 word clips, 711 phrase clips and
196 dialogue-line clips are rendered with Meta's MMS Malagasy model**, so the audio is
Malagasy rather than a foreign voice. **No native speaker has reviewed any of it yet** —
`pron_qa.html` and `SPEAKER_QUESTIONS.md` exist to fix exactly that.

---

## 1. Sources

| Source | What it gave us | Confidence |
|---|---|---|
| Howe, *Central Malagasy*, Journal of the International Phonetic Association (illustration of the IPA) | Vowel qualities (a, e, i, o=[u], final y=[i]); j=[dz], ts=[ts], tr=[ʈʂ], dr=[ɖʐ]; ny=[ni]; penultimate stress with lexical exceptions; final-vowel devoicing; ao/oa realisations | High — peer-reviewed, and the basis for the consonant/vowel tables |
| Rasoloson, *Malagasy–English / English–Malagasy Dictionary and Phrasebook* (the DOCX in `MALAGASY ASSETS/`) | Stress marks the OCR lost but the DOCX kept (`ianaréo`, `izâho`, `Mitsangâna`) → 241 usable entries | Medium — the mark is authoritative where present, but only `é`/`â` survived conversion and there are transcription errors (`lnlan-kely`, `sman-kena`) |
| Peace Corps *Malagasy Language Lessons* + 14 recordings | Stress and rhythm heard, not just written; the reference audio shipped in the app | Medium-high for the words that appear in them |
| Wikivoyage Malagasy phrasebook (CC BY-SA 3.0) | Traveler-oriented approximations; used for cross-checking, never as the primary rule | Low-medium |
| Native-speaker intuitions encoded in `CURATED_STRESS` | 72 hand-checked stress positions | **Unverified** — see §4 |

## 2. Rules that are settled

* **Stress** is penultimate. A lexical class of weak stems (some `-na`, `-ka`, `-tra`
  words) takes antepenultimate stress, but this is a property of the word, not of the
  ending: `olona` [uˈluna] (penult) vs `vohitra` [ˈvuhiʈʂa] (antepenult), while
  `misaotra` ends in `-tra` and is still penultimate [miˈsotʂa]. The app therefore
  uses: dictionary mark → `-tra` heuristic → default penultimate.
  **The `-ka`/`-na` rule in the old README was wrong and has been removed.**
* **Vowels**: `a` [a], `e` [e], `i`/final `y` [i], `o` [u]. `o` is not the English
  "oh" and `e` is not "ee" — the two mistakes English speakers make most.
* **Consonants**: `j` [dz], `ts` [ts], `tr` [ʈʂ], `dr` [ɖʐ]; `ny` [ni]; `ng` is [ŋɡ]
  and is a syllable **onset** (`ma-nga-tsia-ka`, `to-nga`), never a prenasalised
  cluster. This was wrong in the first implementation.
* **`h` is always pronounced.** A Spanish fallback voice silently deletes it, which
  is why Spanish is not the preferred substitute.
* **Final vowels** are often devoiced or dropped in fast speech. The app never drops
  them: a missing vowel teaches the wrong word.
* **Merina `ao`** is [o] (`misaotra` ≈ [miˈsotʂa]), heard as [au̯] further south.
  `oa` is always two syllables (`ahoana` = a-ho-a-na).

## 3. Rules that are heuristics

| Heuristic | Why it is only a heuristic |
|---|---|
| `-tra` → antepenultimate | True for many words, false for others; no published complete list |
| `ao` = one nucleus | Almost always, except where the dictionary's own accent requires a hiatus (`vaovao` = va-o-va-o) |
| Prenasalised `n`/`m` closes the previous syllable | Reliable, but `nk`/`mp` boundaries in compounds are not covered |
| Stress for the ~1,650 words with no dictionary mark | Pure default rule |
| `ai`, `ay`, `oi`, `ou` as diphthongs | Mostly loanwords; never checked against the dictionary |

## 4. Known defects and open questions

1. **Three words where the hand table and the printed dictionary disagree:**
   `dokotera` (hand: antepenult, dictionary: penult), `lehibe` (hand 3, dictionary 1),
   `mipetraka` (hand 2, dictionary 3). The build prints these and `pron_qa.html` lists
   them first. A native speaker should settle them; until then the hand table wins.
2. **72 curated entries have never been heard.** They come from the sources above and
   from plausible reading of the dictionary, not from a speaker.
3. **32 teacher-written respellings carry no stress mark at all** (`manao_ahoana`,
   `tompoko`, `ramatoa`). They render without any capitalised syllable, which looks
   inconsistent next to generated hints. Either mark them or regenerate them.
4. **The adapter cannot fix `tr`/`dr`, `h` on some voices, or French final stress.**
   French [tʁ]/[dʁ] vs Malagasy [ʈʂ]/[ɖʐ] is not reachable by respelling. That is what
   `render_audio.py` is for.
5. **No device ships an installed Malagasy voice** (checked November 2026). The app
   therefore ships its own clips, rendered from `facebook/mms-tts-mlg` (VITS, CC-BY-NC
   4.0) — see §5b. The fallback voice remains for the ~5 % of entries with no clip.

## 5b. The rendered audio (what the learner actually hears)

| | |
|---|---|
| Model | `facebook/mms-tts-mlg`, VITS, 16 kHz, CC BY-NC 4.0 (non-commercial; attribution in the app footer and About panel) |
| Coverage | 2,466 of 2,478 vocabulary entries, 711 of 717 phrases, 196 of 196 dialogue lines |
| Not covered | 12 vocabulary and 6 phrase entries whose ids slug to the same filename; they fall back to the adapted device voice rather than risk playing the wrong clip |
| Format | mono mp3, 32 kbps (~6 KB per word, ~19 MB total) |
| Reproduce | `python3 RESEARCH/render_audio.py --i-accept-noncommercial --what all --mp3` (≈45 min on one CPU) |
| Listen | `python3 RESEARCH/audio_sample.py` → `AUDIO_SAMPLE.html` |

What the model fixes that no respelling can: `tr`/`dr` as [ʈʂ]/[ɖʐ], a pronounced `h`,
Malagasy stress placement, and clean final vowels. What it does not fix: it is a
statistical model trained on read speech, so it can still put phrase stress in the wrong
place, and it says abbreviations and loanwords as spelled. Those are the rows a native
speaker should mark first.

## 5. How the pieces fit

```
pronunciation.py        stress_position / respell / adapt  (Python: build + QA)
APP/js/speech.js        adapt / syllabify                   (browser: playback)
RESEARCH/check_parity.py    fails if the two adapters disagree
RESEARCH/test_pronunciation.py   the invariants above
RESEARCH/pron_qa.py     pron_qa.html — native-speaker review sheet
RESEARCH/render_audio.py    MMS clips → APP/media/audio/{words,lines}
```

Two respellings exist on purpose and must not be confused:

* `word.pron` (`mee-SOH-trah`) is for the **learner's eyes**: English letters.
* `adapt()` output (`mi-ssô-tra`) is for the **voice**: French/Romanian letters.

Feeding the first into `speak()` produces nonsense. This is commented in both files.

## 6. Review protocol for the native speaker

1. `python3 RESEARCH/pron_qa.py`, open `pron_qa.html`.
2. Start with the "Conflicts first" filter (3 words), then "Rule-only stress"
   (≈1,640). Judge the *stress* first, the vowels second.
3. Export the TSV. Verdicts then go:
   * ✔ → keep; consider adding the word to `CURATED_STRESS`.
   * ✘ stress wrong → fix `CURATED_STRESS` and re-run the tests.
   * ✘ voice wrong but stress right → the word needs a rendered clip; it belongs on the
     recording list (`render_audio.py --list`).

## 7. What would make this note say "verified"

A single sitting with a native speaker over the ≈600 words the 36 sessions actually
teach, recorded as verdicts in `pron_qa.tsv`, plus stress positions corrected in
`CURATED_STRESS`. Everything else in this document is inference.
