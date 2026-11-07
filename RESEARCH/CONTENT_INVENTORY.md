# Content Inventory & Source Map — "Vahiny Mianatra Malagasy" Project

**Purpose:** Teaching Malagasy to an elderly American woman (beginner, English speaker).
All content below is already downloaded and extracted inside this project folder, ready to be used in the website and the app.

---

## 1. Folder structure

```
VAHINY MIANATRA MALAGASY/
├── MALAGASY ASSETS/
│   ├── FIANARANA MITENY MALAGASY DOC/        ← Your main documents
│   │   ├── Official Malagasy Peace Corps Madagascar Volunteer Manual.pdf  (175 p, scanned images, no text layer)
│   │   ├── MG_Malagasy_Language_Lessons (1).pdf / MG_Malagasy_Language_Lessons.pdf  (24 p, text OK, 32 topical lessons)
│   │   ├── Malagasy.pdf                      (62 p, text OK — "Creative Relaxation" method + vocabulary)
│   │   ├── ED454700.pdf                      (176 p, scanned — French "Livre du stagiaire")
│   │   ├── FIANARANA MALAGASY.docx           (teaching plan + materials guide, in Malagasy)
│   │   └── MIANATRA MALAGASY.docx / .pdf     (12-week curriculum for the student, in Malagasy)
│   ├── Malagasy-Sakalava/                    ← Yojik.com mirror of the Peace Corps course (public domain)
│   │   ├── MG_Malagasy_Language_Lessons.pdf
│   │   ├── MG_Malagasy_Lesson_1..14.mp3 + MG_Malagasy_Introduction.mp3
│   │   └── ED454700.pdf, Official Manual pdf, page.html (source page)
│   ├── bako-blog-lessons/                    ← NEW: all 58 lesson PDFs downloaded from bako.blog
│   │   ├── introductory-lessons/  (8 files)
│   │   ├── grammar-lessons/      (28 files)
│   │   └── thematic-lessons/     (23 files)
│   └── VOAMBOLANA MALAGASY.jpg
└── extracted/                                ← NEW: everything converted to plain text
    ├── bako-text/
    │   ├── introductory-lessons/  (8 .txt)
    │   ├── grammar-lessons/      (28 .txt)
    │   └── thematic-lessons/     (23 .txt)
    ├── bako_lessons.json          (the site's own lesson catalogue)
    ├── download_bako.py          (rerunnable download script)
    ├── MIANATRA_MALAGASY.txt      (12-week curriculum text)
    ├── FIANARANA_MALAGASY.txt     (lesson-plan + materials text)
    ├── MG_Malagasy_Language_Lessons_1_.txt  (32 Peace Corps topical lessons, full text)
    ├── Malagasy.txt              (Creative Relaxation method + vocabulary appendix)
    ├── Official_Malagasy_Peace_Corps_Madagascar_Volunteer_Manual.txt  (empty — scanned PDF)
    └── ED454700.txt               (empty — scanned PDF)
```

Two PDFs (the Official Peace Corps Volunteer Manual and ED454700) are pure scanned images with no
extractable text. They remain usable as PDFs viewed directly in the app, and their content overlaps
with the text-based Peace Corps Language Lessons PDF.

---

## 2. What each source is good for

### bako.blog — "Learning Malagasy and Tsimihety with Bako" (mandritsara.github.io/bako)
**The backbone of the website's lesson content.** Bako is a real language tutor in Mandritsara (since
2008) who wrote this course exactly for missionaries and visitors — the closest match to your
student's profile. Her "15 lessons" are 15 thematic tracks (23 PDFs with a/b/d/e sub-lessons):

- **Introductory (8 PDFs):** greetings, goodbye, useful expressions, introducing yourself,
  market + numbers/money, review exercises, church (ordinal numbers), village (adjectives).
- **Grammar (28 PDFs):** forming sentences, phrases with verbs, intransitive/transitive verbs,
  adverbs & auxiliaries, *amin'ny*, opposites, demonstratives, comparisons, indirect object,
  conjunctions, indirect pronouns, possessives, adverbials of place and time.
- **Thematic (23 PDFs / 15 themes):** Family, House, Weather, Kitchen, Jobs, Clothing & Colours,
  Body (parts & diseases), Food (fruits, vegetables, spices), Animals, Telling the time,
  Directions, School, Chores, Daily routine, Transport.

### Peace Corps — Malagasy Language Lessons (32 lessons, 24-page PDF + 14 MP3s)
**Best for pronunciation drills and audio.** 32 topical lessons: alphabet, greetings, introductions,
family, basic sentence structures, basic needs, question words, commands/requests, numbers, food,
days of the week, and more. The 14 MP3s in `Malagasy-Sakalava/` match lessons 1–14 — embed them in
the app as the audio layer. Mirrors: livelingua.com/project/peace-corps/malagasy,
fsi-language-courses.org/malagasy-sakalava. All public domain.

### Peace Corps — Madagascar Volunteer Manual (175 pages)
**Deeper reference + culture notes** (29 competency-based topical lessons with dialogues, vocab,
exercises, and cultural notes). Scanned images, so use it as an in-app downloadable PDF reference.

### Malagasy.pdf — "Creative Relaxation" (French/English-based method)
**Confidence-building techniques for elderly learners:** relaxation before the lesson, positive
reinforcement, "theatre of one", short sentences, never apologise for your accent. Also contains a
large vocabulary appendix useful for flashcards.

### MIANATRA MALAGASY.docx + FIANARANA MALAGASY.docx (Malagasy-language teaching docs)
**Your personalised 12-week (3-month) curriculum**, written specifically for this student:

- 3 sessions per week (Mon/Wed/Fri), 1h30 each — deliberately chosen as optimal for an older learner
  (long enough to progress, short enough to avoid fatigue).
- Every lesson: ~20–25 min dialogue → ~35 min phonetics/vocabulary → ~30 min roleplay games.
- 12 weeks: W1 pronunciation & greetings → W2 pronouns → W3 numbers & money → W4 VOS sentence
  structure → W5 food → W6 directions → W7 family & possessives → W8 time/calendar → W9 tenses
  (M- present / N- past / H- future) → W10 health & emergencies → W11 small talk & weather →
  W12 full immersion roleplays + a 45-minute conversation entirely in Malagasy.
- Teaching methods baked in: TPR (Total Physical Response), picture flashcards (never English text),
  spaced repetition (same-day → 3 days → 1 week), large print, active voice before passive.

---

## 3. Licensing note

- Peace Corps, FSI and DLI materials are **public domain** (stated by the Yojik mirror and
  fsi-language-courses.org).
- bako.blog material is **Bako's own work** (© mandritsara project, hosted on GitHub Pages under
  the mandritsara.org mission site). It is publicly downloadable; before republishing her lessons
  inside your own website/app, get permission from the site owner (contact page exists on the
  site). A safe approach: link to her PDFs for reading, and write your own lesson text inspired by
  the same progression.
- The "Creative Relaxation" Malagasy.pdf is clearly marked "FIRST ROUGH VERSION ... WITH SOME
  ERRORS FOR CORRECTION AND FEEDBACK" — a freely-shared draft; treat as fair use for tutoring one
  student, ask before republishing.

## 4. Recommended content architecture for the website & app

1. **Backbone:** your 12-week curriculum (from MIANATRA/FIANARANA docs) — one lesson page per week
   and per session, in large print, with the 1h30 structure visible to the student.
2. **Lesson content:** follow Bako's Introductory → Grammar → Thematic progression, mapped onto the
   12 weeks (mapping is in `CURRICULUM_MAP.md`).
3. **Audio:** Peace Corps MP3s embedded per topic (greetings, numbers, food...).
4. **Exercises:** self-check quizzes + printable flashcards derived from the vocabulary in these
   lessons (starter vocabulary data is in `VOCABULARY_STARTER.json`).
5. **Reference shelf:** the three Peace Corps PDFs + Bako PDFs as downloads/viewers.
