# Vahiny Mianatra Malagasy — Research Summary

**Goal:** Website + app to teach Malagasy to an elderly American woman (absolute beginner, English speaker).

## Voice: Abidi (v3.4)

- `abidi_render.py` — batch renderer for abidi.artifisialy.mg; 3,377 clips in
  `APP/media/audio_abidi/`, manifest in `ABIDI_RENDERED.json`.
- `build_app_data.py` uses Abidi wherever a clip exists; `VOICE_MAP.json` pins entries
  back to MMS; `--voice=mms` reverts the whole app.
- `finish_app.sh` — sweep, rebuild, check chain, regenerate sheets, package.
- `ABIDI.md` (service, licence, permission note), `NARRATIONBOX.md` (the alternative
  and its real cost).

## Native-speaker review (v3.3)

- `proofread.py` → `PROOFREAD.html` — 3,843 rows, ✔/?/✘ buttons, typed corrections,
  localStorage progress, TSV export.
- `apply_corrections.py` — TSV → `CORRECTIONS.json` (merge, `--report`, `--reset`).
- `build_app_data.py` applies `CORRECTIONS.json` **after** the source pack, so a
  correction always wins and every override is logged.
- `render_audio.py --force-changed` re-renders only clips whose Malagasy text changed
  (`APP/media/audio/manifest.json` holds the text hash per clip).
- Workflow and review order: `PROOFREADING.md`.

## What has been done

1. ✅ Inventoried all materials in `MALAGASY ASSETS/` (Peace Corps course PDFs + 15 MP3s from the Yojik
   mirror, plus your own Malagasy teaching documents).
2. ✅ Extracted the text of every text-based document → `extracted/` (see `CONTENT_INVENTORY.md`
   for the map). The only two PDFs without a text layer are pure scans (the 175-page Official
   Volunteer Manual and the 176-page French `ED454700.pdf`) — they still open fine as PDFs.
3. ✅ Researched bako.blog: found that its downloads page loads the lesson list from
   `lessons.json`. Fetched it and **downloaded all 58 lesson PDFs** (8 introductory, 28 grammar,
   23 thematic across 15 themes) → `MALAGASY ASSETS/bako-blog-lessons/`, with plain-text
   extractions in `extracted/bako-text/`.
4. ✅ Built a **starter content pack** (`CONTENT_PACK_STARTER.json`): 71 survival phrases in 6
   units and 111 vocabulary words in 7 groups, all cross-referenced with the matching Peace Corps
   audio files — ready to be loaded by a website or app.
5. ✅ Mapped your 12-week teaching curriculum (from your MIANATRA/FIANARANA docs) to the Bako
   lesson PDFs and Peace Corps audio → `CURRICULUM_MAP.md`.

## Key research findings about the sources

| Source | What it is | Status / rights |
|---|---|---|
| Peace Corps Malagasy Language Lessons (24 p, 32 lessons + 14 MP3s) | Survival course: alphabet, greetings, family, numbers, food, days, colours, furniture | **Public domain** — free to embed in your site/app |
| Peace Corps Madagascar Volunteer Manual (175 p) | 29 competency-based lessons for volunteers; dialogues, cultural notes | **Public domain** |
| ED454700 "Livre du stagiaire" (176 p, French) | FSI-style Peace Corps trainee book | **Public domain** (scanned, no text layer) |
| bako.blog (Mandritsara) | Bako's own course, 58 PDFs, written for missionaries/visitors learning Tsimihety + official Malagasy | Bako's own work — publicly downloadable, but obtain permission before republishing her PDFs on your site; linking to them is safe |
| livelingua.com/project/peace-corps/malagasy | Online mirror of all 3 Peace Corps courses with a browser audio player & pronunciation recorder | Free mirror of public-domain content |
| fsi-language-courses.org/malagasy-sakalava | Another mirror (3 PDFs + 16 audio) | Public domain |
| Malagasy.pdf "Creative Relaxation" (62 p) | Confidence/relaxation-based method + vocabulary, French with some English | Freely shared draft ("rough version for feedback") — fine for personal teaching |
| UW-Madison LCTL resources guide (wisc.pb.unizin.org) | Curated list of Malagasy resources; notes that Peace Corps/church materials are the best free listening sources | Reference only |
| Global Recordings Network (globalrecordings.net/en/language/mlg) | Hundreds of free native-spoken audio recordings in many Malagasy dialects | Free to listen |
| Malagasy Mianatra Anglais (YouTube channel) | Trilingual Malagasy/French/English lessons read by native speakers | Free to watch; can't re-embed content, link out |
| Targumi / 17-minute-languages / uTalk / Memrise | Commercial options for live lessons or flashcards | Paid — optional supplements only |

## Copyright notes for the website & app

- **Safe to embed/copy freely:** Everything from the Peace Corps (all 3 PDFs + 14 MP3s). US
  government works are public domain.
- **Cite-and-link, or get permission:** Bako's lesson PDFs. Her content is on a public GitHub Pages
  site (mandritsara.github.io/bako) with no stated licence; the mandritsara.org project is a
  mission project, so an email asking permission will likely get a warm yes. Meanwhile the lesson
  catalog at `extracted/bako_lessons.json` documents exactly what exists.
- **Your own content:** The MIANATRA/FIANARANA docs and this content pack are yours — no limits.
- **Audio licensing caution for the app:** if you plan studio audio (e.g., speech synthesis or
  native recordings you commission), you own those rights outright.

## Recommendations for the website & app (from the research)

1. **Elderly learners need:** large text (18px minimum), high contrast, simple navigation, one
   thing per screen, audio everywhere (they can lean on listening over reading), printable
   flashcards, and no timers or pressure. Your own teaching docs already embody this.
2. **Structure the site on your 12-week curriculum** (see `CURRICULUM_MAP.md`) — three 90-minute
   sessions per week, each with dialogue → phonetics → roleplay.
3. **Audio layer:** the 14 Peace Corps MP3s match perfectly with lessons 1–14 of the 32-lesson
   text course; assign them as daily 10-minute "homework listening".
4. **Dialect choice:** teach official Malagasy as the base (all materials support it) but include
   Bako's Tsimihety variants as "as spoken in Mandritsara" notes — exactly the bilingual approach
   her lessons use.
5. **Flashcards:** vocabulary from `CONTENT_PACK_STARTER.json` is image-first (no English on the
   card face, per your teaching docs' TPR method). The VOAMBOLANA MALAGASY.jpg you already have
   could be the homepage hero image.
6. **Next content step (optional):** digitise the remaining Peace Corps lessons 15–32 from the
   24-page PDF — the vocabulary lists there (body, weather, transport, shopping) would triple the
   current starter pack.

## Pronunciation and audio tooling

| Script | What it does |
|---|---|
| `pronunciation.py` | stress, English respelling, and the Malagasy→foreign-voice adapter |
| `PRONUNCIATION.md` | the research note: what is settled, what is a heuristic, what is unverified |
| `pron_qa.py` → `pron_qa.html` | self-contained review sheet for a native speaker (marks in localStorage, TSV export) |
| `render_audio.py` | renders real Malagasy clips with `facebook/mms-tts-mlg` (CC BY-NC 4.0; refuses to run without an explicit flag) into `APP/media/audio/{words,lines}` |
| `test_pronunciation.py` | 28 unit tests on syllabification, stress, respelling and adaptation |
| `check_parity.py` | fails if `pronunciation.py` and `APP/js/speech.js` disagree |
| `smoke_app.js` | renders and mounts every screen with a stub DOM, then fires the main handlers |

Run order after changing any rule:

```bash
python3 RESEARCH/test_pronunciation.py
python3 RESEARCH/check_parity.py
python3 RESEARCH/build_app_data.py
python3 RESEARCH/validate_content.py
node RESEARCH/smoke_app.js
```

## Folder guide

```
RESEARCH/
├── README.md                  ← this file
├── CONTENT_INVENTORY.md       ← full inventory of every source & file
├── CURRICULUM_MAP.md          ← 12-week plan mapped to lessons & audio
└── CONTENT_PACK_STARTER.json  ← phrases + vocab data for the website/app
extracted/                     ← all text extracted from PDFs & DOCX, + bako lesson texts
MALAGASY ASSETS/bako-blog-lessons/  ← the 58 downloaded bako.blog lesson PDFs
```

## Content Pack v2.1 — Dictionary Expansion (Nov 2026)

The master pack now also incorporates:

- **Rasoloson dictionary & phrasebook** (the local PDF/DOCX pair — same book, extracted from the
  PDF's cleaner text layer): 1,180 English->Malagasy entries, 835 Malagasy->English entries,
  and 301 phrasebook sentence pairs cleaned with a Malagasy-language scoring filter.
  Files: `extracted/RASOLOSON/DICTIONARY_EN_MG.json`, `DICTIONARY_MG_EN.json`,
  `RASOLOSON_PHRASEBOOK.json` (rebuilt by `extracted/extract_rasoloson.py`).
- **Wikivoyage Malagasy phrasebook** (`RESEARCH/WIKIVOYAGE_PHRASEBOOK.json`, CC BY-SA 3.0):
  205 traveler phrases with English-approximation pronunciations, the full number table with
  pronunciations, months, days, clock/duration expressions, colors, Ariary denominations,
  regional greetings (Toamasina 'Manakory e!', Northern 'Mbola tsara!', Southern 'Akory koahy!'),
  cultural tips, and its vowel/consonant pronunciation guide.

### Totals (built app, `APP/data/content.js` — the authoritative numbers)
- Vocabulary: **2478** entries (after the cleaning rules drop mangled glosses and
  column-slipped rows)
- Phrases: **717** | Dialogues: 33 | Grammar topics: 27 | Culture notes: 161
- Sessions: 36 over 12 weeks
- Pronunciation: written hint for **100%** of words and phrases; stress from the
  dictionary for 172, from the hand table / teacher docs for 107, from the documented
  default rule for the rest; 3 words have a hand-table/dictionary conflict.
- Stress lexicon: 309 entries (72 curated + 241 recovered from the dictionary DOCX).

`RESEARCH/README.md` used to state pack totals (2,489 / 736 / 35) that no longer
matched the build. The build now writes its own counts into `APP/README.md`.

### Licensing / independence note
The website and app are an **original, unaffiliated product**. Facts (word–meaning pairs, phrases)
from these works are compiled as teaching material; the app carries its own name and branding,
no source logos or content presentation, and gives attribution where a license requires it
(Wikivoyage, CC BY-SA 3.0). Products to be published under a new original brand.
