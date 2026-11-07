#!/usr/bin/env python3
"""Build APP/data/content.js from RESEARCH/CONTENT_PACK_FULL.json.

Usage:  python3 build_app_data.py      (run from the project root)
Output: APP/data/content.js — a single JS file defining `window.CONTENT`.

Keeps the app self-contained: vocabulary, phrases, dialogues, grammar, culture,
pronunciation, the 12-week curriculum, and Peace Corps audio mappings.
"""
import json, os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "RESEARCH"))
import content_quality as cq
import pronunciation as pr

pack = json.load(open(os.path.join(BASE, "RESEARCH", "CONTENT_PACK_FULL.json"), encoding="utf-8"))

# Corrections from a native-speaker proofreading pass (RESEARCH/apply_corrections.py).
# Absent file = nothing corrected yet, which is the normal state.
CORRECTIONS_PATH = os.path.join(BASE, "RESEARCH", "CORRECTIONS.json")
CORRECTIONS = {}
CORRECTION_STATS = {"applied": 0, "verified": 0, "wrong": 0, "missing": 0}
CORRECTION_LOG = []
if os.path.exists(CORRECTIONS_PATH):
    try:
        CORRECTIONS = json.load(open(CORRECTIONS_PATH, encoding="utf-8")).get("entries", {})
    except (ValueError, OSError) as error:
        print("WARNING corrections file unreadable (%s); ignoring it." % error, file=sys.stderr)
        CORRECTIONS = {}


def apply_correction(entry, key):
    """Overwrite text and mark approval for one entry, in place.

    'verdict: ok' is the important one: it means a native speaker listened or read
    and approved, so the UI stops calling the pronunciation approximate.
    """
    fix = CORRECTIONS.get(key)
    if not fix:
        return
    if fix.get("mg"):
        entry["mg_original"] = entry.get("mg", "")
        entry["mg"] = fix["mg"]
    if fix.get("en"):
        entry["en_original"] = entry.get("en", "")
        entry["en"] = fix["en"]
    if fix.get("note"):
        entry["reviewer_note"] = fix["note"]
    verdict = fix.get("verdict")
    if verdict == "ok":
        entry["pron_verified"] = True
        CORRECTION_STATS["verified"] += 1
    elif verdict == "wrong":
        entry["pron_disputed"] = True
        CORRECTION_STATS["wrong"] += 1
    if fix.get("mg") or fix.get("en"):
        CORRECTION_STATS["applied"] += 1
        # Corrections always win over the source pack (including text the teacher
        # wrote). Logged, so a silent overwrite is impossible.
        CORRECTION_LOG.append((key, entry.get("mg_original"), fix.get("mg"),
                               entry.get("en_original"), fix.get("en")))


# Stress marks preserved in the Rasoloson dictionary DOCX (ianaréo, matétika).
DICT_DOCX = os.path.join(BASE, "MALAGASY ASSETS",
                         "malagasy-english-english-malagasy-dictionary-and-phrasebook-078180843x.docx")
STRESS_LEXICON = pr.load_stress_lexicon(DICT_DOCX)
# Words where the hand table and the printed dictionary disagree. Surfaced here
# so a missing or unreadable dictionary can never pass silently again.
STRESS_CONFLICTS = pr.stress_conflicts(DICT_DOCX)

# ---------------- vocabulary ----------------
def slur(p):
    with open(p, encoding="utf-8") as f:
        s = f.read()
    return re.sub(r"\s+", " ", s).strip()

vocabulary = []
for w in pack["vocabulary"]:
    mg = w.get("mg", "").strip()
    en = w.get("en", "").strip()
    if not mg or not en or len(en) > 100:
        continue
    # A gloss like "skin; skm" or "mother (...) ; mother reraka ad), tired"
    # carries fragments of the next dictionary line. Keep the real senses only.
    primary, alternates = cq.clean_gloss(en)
    if not primary:
        continue
    mg, inline_dialect = cq.split_dialect(mg)
    mg = cq.strip_official(mg)
    mg, mg_variants = cq.split_variants(mg)
    en = cq.strip_official(primary)
    entry = {
        "id": w["id"],
        "mg": mg,
        "en": en,
        "themes": [t for t in w.get("themes", []) if t != "dictionary"],
        "level": w.get("level", 1),
    }
    if alternates:
        entry["alt"] = alternates
    if mg_variants:
        entry["mg_alt"] = mg_variants
    if w.get("note"):
        entry["note"] = w["note"]
    if w.get("pos"):
        entry["pos"] = w["pos"]
    if w.get("pron"):
        entry["pron"] = w["pron"]
    if w.get("variants"):
        entry["mg_tsm"] = ", ".join(v["mg"] for v in w["variants"] if v.get("mg"))
    elif inline_dialect and not entry.get("mg_tsm"):
        entry["mg_tsm"] = inline_dialect
    entry["isPhrase"] = " " in mg
    vocabulary.append(entry)

# simple pronunciation helper: attach from teacher-doc pronunciations where the mg matches
pron_index = {}
for k in ("key_words_16_throat_exercise", "flashcard_pronunciation_from_teacher_docs",
          "traveler_pronunciations"):
    for p in (pack["pronunciation"].get(k) or []):
        if isinstance(p, dict) and p.get("mg") and p.get("say"):
            pron_index.setdefault(p["mg"].lower().strip(), p["say"])
def mark_stress(text, word):
    """Add the stress mark to a teacher-written hint that has none.

    The teacher docs often write "mee-peh-trah-kah": good letters, no stress. If
    the hint has exactly one group per written syllable we can capitalise the
    stressed one without touching a single letter the teacher chose.
    """
    if not text or re.search(r"[A-Z]", text):
        return text, False
    groups = [g for g in re.split(r"[\s]+", text) if g]
    if len(groups) != 1:
        return text, False
    parts = groups[0].split("-")
    syllables = pr.syllabify(word)
    if len(parts) != len(syllables) or not parts:
        return text, False
    position = pr.stress_position(word, STRESS_LEXICON)[0]
    index = max(0, len(parts) - min(position, len(parts)))
    parts[index] = parts[index].upper()
    return "-".join(parts), True


for w in vocabulary:
    say = pron_index.get(w["mg"].lower().strip())
    if say and "pron" not in w:
        w["pron"], marked = mark_stress(say, w["mg"])
        w["pron_source"] = "teacher"
        if marked:
            w["pron_stress_added"] = True
            cq.GARBAGE_COUNT["pron_stress_added"] = cq.GARBAGE_COUNT.get("pron_stress_added", 0) + 1
        continue
    if "pron" in w:
        marked = False
        if not re.search(r"[A-Z]", w["pron"]):
            w["pron"], marked = mark_stress(w["pron"], w["mg"])
            if marked:
                w["pron_stress_added"] = True
        w["pron_source"] = "teacher"
        continue
    # A written hint for every study word *and* every phrase: dictionary stress
    # where the DOCX preserved a mark, otherwise the documented penultimate
    # default. Phrases are respelled word by word — they used to be skipped
    # entirely, which left the roleplay lines with no hint at all.
    if w["isPhrase"]:
        guess = pr.respell_phrase(w["mg"], STRESS_LEXICON)
        source = "phrase"
    else:
        guess, source = pr.respell(w["mg"], STRESS_LEXICON)
    if guess:
        w["pron"] = guess
        w["pron_source"] = source
        w["pron_approx"] = True
        cq.GARBAGE_COUNT["pron_generated"] += 1
    else:
        cq.GARBAGE_COUNT["pron_skipped"] += 1

# Corrections from the proofreading pass, once every field exists.
for w in vocabulary:
    apply_correction(w, "word:%s" % w["id"])
    if w.get("pron_verified"):
        w.pop("pron_approx", None)          # approved by a person: not approximate any more

# ---------------- phrases ----------------
# 14 rows slipped their columns during compilation and taught English as if it
# were Malagasy. Re-pair from the dictionary when the Malagasy word is known,
# otherwise drop the row rather than ship a wrong pair.
vocab_index = {}
for w in vocabulary:
    vocab_index.setdefault(re.sub(r"\s+", " ", w["mg"].strip().lower()), w["en"])

phrases = []
for p in pack["phrases"]:
    if not p.get("mg") or not p.get("en"):
        continue
    mg, en = p["mg"].strip(), p["en"].strip()
    if cq.JUNK_MG.match(mg) or cq.duplicated_pair(mg, en):
        cq.GARBAGE_COUNT["phrases_dropped"] += 1
        continue
    if cq.looks_english(mg) or cq.is_fragment(en):
        # The row cannot be trusted in either direction; there is no reliable
        # way to recover the intended pair, so it is dropped instead of shipped.
        cq.GARBAGE_COUNT["phrases_dropped"] += 1
        continue
    mg, inline_dialect = cq.split_dialect(mg)
    mg = cq.strip_official(mg)
    mg, mg_variants = cq.split_variants(mg)
    en = cq.strip_official(en)
    group = cq.normalise_group(p.get("group", "general"))
    entry = {"id": p["id"], "mg": mg, "en": en, "group": group}
    if mg_variants:
        entry["mg_alt"] = mg_variants
    if p.get("note"):
        entry["note"] = p["note"]
    if p.get("mg_tsm"):
        entry["mg_tsm"] = p["mg_tsm"]
    elif inline_dialect:
        entry["mg_tsm"] = inline_dialect
    # Phrases used to ship with no pronunciation at all, so the lines used in
    # roleplay — the place a learner actually speaks — had neither a written
    # hint nor adapted audio. Respell them word by word.
    guess = pr.respell_phrase(entry["mg"], STRESS_LEXICON)
    if guess:
        entry["pron"] = guess
        entry["pron_source"] = "phrase"
        entry["pron_approx"] = True
        cq.GARBAGE_COUNT["pron_generated"] += 1
    else:
        cq.GARBAGE_COUNT["pron_skipped"] += 1
    apply_correction(entry, "phrase:%s" % entry["id"])
    if entry.get("pron_verified"):
        entry.pop("pron_approx", None)
    phrases.append(entry)

# ---------------- dialogues ----------------
dialogues = []
for d in pack["dialogues"]:
    lines = []
    for line_index, line in enumerate(d.get("lines", [])):
        if not line.get("mg") or not line.get("en"):
            continue
        if cq.looks_english(line["mg"]):
            continue
        mg_line, dialect = cq.split_dialect(line["mg"])
        speaker, stage = cq.split_stage(line.get("speaker", ""))
        clean = {"speaker": speaker, "mg": mg_line, "en": cq.strip_official(line["en"])}
        if stage:
            clean["stage"] = stage
        if dialect:
            clean["mg_tsm"] = dialect
        # A hint per dialogue line: the roleplay is where the learner speaks, and
        # it was the one place with no written pronunciation at all.
        hint = pr.respell_phrase(clean["mg"], STRESS_LEXICON)
        if hint:
            clean["pron"] = hint
        apply_correction(clean, "dlg:%s:%d" % (d["id"], line_index))
        if clean.get("pron_verified"):
            clean.pop("pron_approx", None)
        lines.append(clean)
    if len(lines) >= 2:
        dialogues.append({"id": d["id"], "title": cq.clean_dialogue_title(d.get("title", "")),
                          "group": cq.normalise_group(d.get("group", "")), "lines": lines})

# ---------------- grammar (rules distilled, plain English) ----------------
grammar = []
for g in pack["grammar"]:
    rules = []
    for r in g.get("rules", []):
        if not isinstance(r, dict) or not r.get("rule"):
            continue
        rule = {"rule": re.sub(r"^W[••\-]?\s*", "", r["rule"]).strip(),
                "explanation": r.get("explanation", ""),
                "examples": [{"mg": e.get("mg", ""), "en": e.get("en", "")}
                             for e in r.get("examples", []) if e.get("mg")]}
        for example_index, example in enumerate(rule["examples"]):
            apply_correction(example, "gram:%s:%d:%d"
                             % (g.get("id", ""), len(rules), example_index))
        rules.append(rule)
    if rules:
        grammar.append({"id": g.get("id", ""), "title": g.get("title", ""), "rules": rules})

# ---------------- culture ----------------
culture = []
seen_notes = set()
for c in pack["culture"]:
    note = re.sub(r"\s+", " ", c.get("note", "")).strip()
    key = note.lower()
    if note and key not in seen_notes and len(note) > 10:
        seen_notes.add(key)
        note_entry = {"lesson": c.get("lesson", ""), "note": note}
        apply_correction(note_entry, "culture:%d" % len(culture))
        culture.append(note_entry)

# ---------------- pronunciation guide ----------------
# Notes distilled from the JIPA illustration of Central Malagasy (Howe) — the
# mistakes English speakers actually make, stated once each.
GUIDE_NOTES = [
    "o is “oo” as in food, never the “o” in go: trano is TRAH-noo.",
    "e is “eh” as in bed, not “ee”: veloma is veh-LOO-mah.",
    "j is “dz” as in adze, not the j in job: jiro (lamp) is DZEE-roo.",
    "ts is one sound, as at the end of cats: tsara is TSAH-rah.",
    "tr and dr are said further back than in English: trano, mandry.",
    "ng is two sounds, n then a hard g: mangatsiaka is mah-NGAH-tsee-ah-kah.",
    "y at the end of a word is “ee”: Malagasy is mah-lah-GAH-see.",
    "Stress usually falls on the second-to-last syllable. Many -tra words "
    "stress the third-to-last (vohitra → VOO-hee-trah), but not all "
    "(misaotra → mee-SOH-trah).",
    "Final vowels are often whispered or dropped in fast speech — olona can "
    "sound like “oo-loon” — but say them while learning.",
    "ny is “nee”, not the ny in canyon: ny olona is nee oo-LOO-nah.",
    "ao is close to “oh” in the capital: misaotra is mee-SOH-trah (heard as "
    "mee-SOW-trah further south).",
]

pron = {
    "vowels": pack["pronunciation"].get("vowels", []),
    "notes": list(pack["pronunciation"].get("notes", [])) +
             [{"note": text} for text in GUIDE_NOTES],
    "key_words": pack["pronunciation"].get("key_words_16_throat_exercise", []),
    "teacher_flashcards": pack["pronunciation"].get("flashcard_pronunciation_from_teacher_docs", []),
    "traveler": pack["pronunciation"].get("traveler_pronunciations", []),
    "voice_note": "No browser or phone ships an installed Malagasy voice (checked November 2026), "
                  "so the app rewrites each word into the spelling of the closest installed "
                  "voice (French, Romanian, Italian, Spanish, Catalan) and says each syllable "
                  "separately. Where a recorded clip exists it is played instead, and a real "
                  "Malagasy voice, if one ever gets installed, is used before anything else.",
}

# Rendered recordings. `render_audio.py` writes one clip per word and per
# dialogue line; anything found here wins over a synthetic voice.
#   media/audio/words/<vocabulary-id>.mp3
#   media/audio/lines/<dialogue-id>-<line-index>.mp3
AUDIO_EXTENSIONS = (".mp3", ".m4a", ".ogg", ".opus", ".wav")


def scan_audio(relative_dir):
    folder = os.path.join(BASE, "APP", relative_dir)
    found = {}
    if os.path.isdir(folder):
        for name in sorted(os.listdir(folder)):
            stem, extension = os.path.splitext(name)
            if extension.lower() in AUDIO_EXTENSIONS:
                found[stem] = relative_dir.replace(os.sep, "/") + "/" + name
    return found


_word_files = scan_audio(os.path.join("media", "audio", "words"))
_line_files = scan_audio(os.path.join("media", "audio", "lines"))


def index_by_id(items, files, kind):
    """{entry id: relative path} using the slugged file name.

    Two entry ids can slug to the same file name ("mba_" and "mba", "Misy ___ ve?"
    and "Misy … ve?"). Whichever entry the renderer touched last would otherwise
    be played for both, i.e. one of them would hear the wrong sentence. A slug
    shared by more than one entry is therefore left un-wired: no clip is better
    than the wrong clip, and the fallback voice still speaks it.
    """
    ids_by_slug = {}
    for item in items:
        ids_by_slug.setdefault(cq.audio_slug(item.get("id", "")), []).append(item["id"])
    ambiguous = {slug: ids for slug, ids in ids_by_slug.items() if len(ids) > 1}
    found = {}
    for item in items:
        slug = cq.audio_slug(item.get("id", ""))
        if slug in ambiguous:
            continue
        path = files.get(slug)
        if path:
            found[item["id"]] = path
    if ambiguous:
        print("  %s audio skipped for %d ambiguous slug(s): %s"
              % (kind, len(ambiguous),
                 ", ".join(sorted(ambiguous)[:4])), file=sys.stderr)
    missing = [i["id"] for i in items if i["id"] not in found]
    if missing:
        print("  %s audio missing for %d entr%s (e.g. %s)"
              % (kind, len(missing), "y" if len(missing) == 1 else "ies",
                 ", ".join(missing[:3])), file=sys.stderr)
    return found


# --voice abidi: use the Abidi renders where they exist and keep MMS for the rest.
# Off by default, so an experiment can never quietly change what the learner hears.
# auto  (default): Abidi wherever a clip exists, MMS everywhere else
# abidi           : same, but say so loudly
# mms             : ignore the Abidi renders entirely
_selected = "auto"
for _arg in sys.argv:
    if _arg in ("--voice=mms", "--mms"):
        _selected = "mms"
    elif _arg in ("--voice=abidi", "--abidi", "--voice=auto"):
        _selected = "abidi" if _arg != "--voice=auto" else "auto"
VOICE = _selected

# Per-entry voice choice, because no voice wins everywhere: the reviewer reported
# that MMS reads "veloma" correctly while Abidi is better in general.
VOICE_MAP_PATH = os.path.join(BASE, "RESEARCH", "VOICE_MAP.json")
VOICE_MAP = {}
if os.path.exists(VOICE_MAP_PATH):
    try:
        VOICE_MAP = json.load(open(VOICE_MAP_PATH, encoding="utf-8")).get("entries", {})
    except (ValueError, OSError) as error:
        print("WARNING voice map unreadable (%s)" % error, file=sys.stderr)


def overlay_voice(found, items, kind, prefix):
    """Abidi where a clip exists, then honour explicit per-entry overrides.

    `found` is the MMS map and is never mutated: an override back to MMS needs the
    original path, and a mis-typed key must not silently keep an Abidi clip.
    """
    mms = dict(found)
    if VOICE == "mms":
        if VOICE_MAP:
            print("  voice: forced to mms; %d override(s) in VOICE_MAP.json ignored"
                  % len(VOICE_MAP))
        return mms
    folder = os.path.join("media", "audio_abidi", kind)
    merged = dict(mms)
    added = 0
    if os.path.isdir(os.path.join(BASE, "APP", folder)):
        abidi = index_by_id(items, scan_audio(folder), kind + " (abidi)")
        for entry_id, path in abidi.items():
            merged[entry_id] = path
        added = len(abidi)
    # Overrides
    back_to_mms = unknown = 0
    for key, choice in VOICE_MAP.items():
        wanted, _, entry_id = key.partition(":")
        if wanted != prefix:
            continue
        if entry_id not in {item["id"] for item in items}:
            print("  voice map: unknown entry %r ignored" % key, file=sys.stderr)
            unknown += 1
            continue
        if choice == "mms":
            if entry_id in mms:
                merged[entry_id] = mms[entry_id]
            else:
                merged.pop(entry_id, None)
            back_to_mms += 1
        elif choice == "abidi":
            pass                      # already applied above when a clip exists
    print("  voice: %d %s clip(s) from abidi%s%s"
          % (added, kind,
             ", %d kept on mms by VOICE_MAP.json" % back_to_mms if back_to_mms else "",
             ", %d unknown key(s)" % unknown if unknown else ""))
    return merged


word_audio = index_by_id(vocabulary, _word_files, "word")
phrase_audio = index_by_id(phrases, scan_audio(os.path.join("media", "audio", "phrases")),
                           "phrase")
dialogue_lines = [{"id": "%s-%d" % (d["id"], index)}
                  for d in dialogues for index, _ in enumerate(d.get("lines", []))]
line_audio = index_by_id(dialogue_lines, _line_files, "line")
word_audio = overlay_voice(word_audio, vocabulary, "words", "word")
phrase_audio = overlay_voice(phrase_audio, phrases, "phrases", "phrase")
line_audio = overlay_voice(line_audio, dialogue_lines, "lines", "dlg")

# ---------------- 12-week curriculum ----------------
AUDIO_PATH = "../MALAGASY ASSETS/Malagasy-Sakalava/"
curriculum = [
    {"week": 1, "month": 1, "title": "Pronunciation & Greetings", "sessions": [
        {"day": "Monday", "focus": "Greetings dialogue: Salama! Manao ahoana? Tsara fa misaotra",
         "audio": ["MG_Malagasy_Introduction.mp3", "MG_Malagasy_Lesson_2.mp3"], "themes": ["greetings_courtesies"]},
        {"day": "Wednesday", "focus": "Vowels a, e, i, o; Misaotra / Azafady",
         "audio": ["MG_Malagasy_Lesson_1.mp3"], "themes": ["greetings_courtesies"]},
        {"day": "Friday", "focus": "Review: full greeting + goodbye; 12-week goal-setting",
         "audio": ["MG_Malagasy_Lesson_2.mp3"], "themes": ["greetings_courtesies"]},
    ]},
    {"week": 2, "month": 1, "title": "Pronouns & Introducing Yourself", "sessions": [
        {"day": "Monday", "focus": "Izaho, ianao, izy; 'Miteny malagasy ve ianao?' — 'Kely fotsiny'",
         "audio": [], "themes": ["people_family", "verbs_grammar"]},
        {"day": "Wednesday", "focus": "Izahay (we-not-you) vs isika (we-with-you)",
         "audio": [], "themes": ["verbs_grammar"]},
        {"day": "Friday", "focus": "Dialogue: name, origin, family basics — Manambady aho. Manana zanaka aho.",
         "audio": ["MG_Malagasy_Lesson_3.mp3"], "themes": ["people_family"]},
    ]},
    {"week": 3, "month": 1, "title": "Numbers & Money", "sessions": [
        {"day": "Monday", "focus": "Numbers 1–10; 'Firy?'",
         "audio": ["MG_Malagasy_Lesson_9.mp3"], "themes": ["numbers"]},
        {"day": "Wednesday", "focus": "Numbers 11–100, read right-to-left; ariary money",
         "audio": ["MG_Malagasy_Lesson_9.mp3"], "themes": ["numbers"]},
        {"day": "Friday", "focus": "Market dialogue: Ohatrinona ity? Lafo be! Mora ve?",
         "audio": [], "themes": ["numbers", "food_drink"]},
    ]},
    {"week": 4, "month": 1, "title": "Making Sentences (VOS Order)", "sessions": [
        {"day": "Monday", "focus": "Mihinana vary aho — Verb + Object + Subject",
         "audio": ["MG_Malagasy_Lesson_5.mp3"], "themes": ["food_drink", "verbs_grammar"]},
        {"day": "Wednesday", "focus": "Saying 'not': tsy mihinana hena aho",
         "audio": [], "themes": ["verbs_grammar"]},
        {"day": "Friday", "focus": "Month 1 review — market roleplay game",
         "audio": [], "themes": ["numbers", "food_drink", "greetings_courtesies"]},
    ]},
    {"week": 5, "month": 2, "title": "Food & Ordering", "sessions": [
        {"day": "Monday", "focus": "Food and drink vocabulary",
         "audio": ["MG_Malagasy_Lesson_10.mp3"], "themes": ["food_drink"]},
        {"day": "Wednesday", "focus": "Mila … (I need) / Te hi… (I want to)",
         "audio": [], "themes": ["verbs_grammar", "food_drink"]},
        {"day": "Friday", "focus": "Restaurant dialogue + ordering",
         "audio": [], "themes": ["food_drink"]},
    ]},
    {"week": 6, "month": 2, "title": "Directions & Places", "sessions": [
        {"day": "Monday", "focus": "Aiza ny …? (Where is the toilet / market / bank?)",
         "audio": ["MG_Malagasy_Lesson_6.mp3"], "themes": ["directions_places"]},
        {"day": "Wednesday", "focus": "Ankavanana (right), ankavia (left), mahitsy (straight)",
         "audio": [], "themes": ["directions_places"]},
        {"day": "Friday", "focus": "Map roleplay: get from home to the market",
         "audio": [], "themes": ["directions_places"]},
    ]},
    {"week": 7, "month": 2, "title": "Family & Possessives", "sessions": [
        {"day": "Monday", "focus": "Family members — bring your family photos!",
         "audio": ["MG_Malagasy_Lesson_4.mp3"], "themes": ["people_family"]},
        {"day": "Wednesday", "focus": "Possessive suffixes -ko, -nao, -ny: tranoko, vadinao, zanany",
         "audio": [], "themes": ["people_family"]},
        {"day": "Friday", "focus": "Your family tree in Malagasy — show & tell",
         "audio": [], "themes": ["people_family"]},
    ]},
    {"week": 8, "month": 2, "title": "Time & Calendar", "sessions": [
        {"day": "Monday", "focus": "Days of the week; omaly, androany, rahampitso",
         "audio": ["MG_Malagasy_Lesson_11.mp3"], "themes": ["time_calendar"]},
        {"day": "Wednesday", "focus": "Clock: Amin'ny firy izao?",
         "audio": [], "themes": ["time_calendar"]},
        {"day": "Friday", "focus": "Making appointments: Hihaona amin'ny Zoma amin'ny efatra isika",
         "audio": [], "themes": ["time_calendar"]},
    ]},
    {"week": 9, "month": 3, "title": "Past & Future Tenses", "sessions": [
        {"day": "Monday", "focus": "Present→past: mihinana → nihinana",
         "audio": [], "themes": ["verbs_grammar"]},
        {"day": "Wednesday", "focus": "Present→future: mihinana → hihinana",
         "audio": [], "themes": ["verbs_grammar"]},
        {"day": "Friday", "focus": "Inona no nataonao omaly? / Inona no hataonao rahampitso?",
         "audio": [], "themes": ["verbs_grammar", "time_calendar"]},
    ]},
    {"week": 10, "month": 3, "title": "Health & Emergencies", "sessions": [
        {"day": "Monday", "focus": "Body parts: lohako, kiboko, tongotro",
         "audio": [], "themes": ["body_health"]},
        {"day": "Wednesday", "focus": "Marary aho! Vonjeo! Mila dokotera aho!",
         "audio": ["MG_Malagasy_Lesson_6.mp3"], "themes": ["body_health"]},
        {"day": "Friday", "focus": "Emergency roleplay",
         "audio": [], "themes": ["body_health"]},
    ]},
    {"week": 11, "month": 3, "title": "Small Talk & Weather", "sessions": [
        {"day": "Monday", "focus": "Weather: mafana, mangatsiaka, avy ny orana",
         "audio": [], "themes": ["weather_nature"]},
        {"day": "Wednesday", "focus": "Reactions & opinions: Tsara kely! Mahafinaritra!",
         "audio": ["MG_Malagasy_Lesson_12.mp3"], "themes": ["weather_nature", "greetings_courtesies"]},
        {"day": "Friday", "focus": "Free conversation about hobbies and likes",
         "audio": [], "themes": ["daily_routine", "clothing", "colors"]},
    ]},
    {"week": 12, "month": 3, "title": "Grand Finale", "sessions": [
        {"day": "Monday", "focus": "Market simulation — buy a week of groceries entirely in Malagasy",
         "audio": [], "themes": ["numbers", "food_drink"]},
        {"day": "Wednesday", "focus": "Transport roleplay: taxi-brousse",
         "audio": [], "themes": ["transport"]},
        {"day": "Friday", "focus": "45 minutes of conversation ONLY in Malagasy + celebration 🎉",
         "audio": [], "themes": ["greetings_courtesies", "food_drink", "people_family"]},
    ]},
]
# The build used to delete every audio mapping because the paths pointed outside
# the served folder. The 14 Peace Corps recordings now ship with the app.
AUDIO_DIR = "media/audio/"
DEFAULT_AUDIO = {
    1: ["MG_Malagasy_Introduction.mp3", "MG_Malagasy_Lesson_2.mp3"],
    2: ["MG_Malagasy_Lesson_3.mp3"], 3: ["MG_Malagasy_Lesson_9.mp3"],
    4: ["MG_Malagasy_Lesson_5.mp3"], 5: ["MG_Malagasy_Lesson_10.mp3"],
    6: ["MG_Malagasy_Lesson_6.mp3"], 7: ["MG_Malagasy_Lesson_4.mp3"],
    8: ["MG_Malagasy_Lesson_11.mp3"], 9: ["MG_Malagasy_Lesson_13.mp3"],
    10: ["MG_Malagasy_Lesson_6.mp3"], 11: ["MG_Malagasy_Lesson_12.mp3"],
    12: ["MG_Malagasy_Lesson_14.mp3"],
}

# Every session points at a real dialogue from the pack, so the warm-up is
# stored lesson content rather than a generated example.
SESSION_DIALOGUES = {
    (1, 1): "dlg_greet_and_farewell", (1, 2): "dlg_intro_2_15", (1, 3): "dlg_intro_1b_13",
    (2, 1): "dlg_introducing_yourself", (2, 2): "dlg_intro_3_21", (2, 3): "dlg_intro_3_22",
    (3, 1): "dlg_intro_4_24", (3, 2): "dlg_intro_4_23", (3, 3): "dlg_market_shopping",
    (4, 1): "dlg_basic_needs", (4, 2): "dlg_polite_words", (4, 3): "dlg_intro_4_24",
    (5, 1): "dlg_eating_ordering", (5, 2): "dlg_basic_needs", (5, 3): "dlg_eating_ordering",
    (6, 1): "dlg_directions_travel", (6, 2): "dlg_directions_travel", (6, 3): "dlg_directions_travel",
    (7, 1): "dlg_intro_3_22", (7, 2): "dlg_intro_3_22", (7, 3): "dlg_introducing_yourself",
    (8, 1): "dlg_time_appointments", (8, 2): "dlg_time_appointments", (8, 3): "dlg_time_appointments",
    (9, 1): "dlg_basic_needs", (9, 2): "dlg_basic_needs", (9, 3): "dlg_time_appointments",
    (10, 1): "dlg_health_emergency", (10, 2): "dlg_health_emergency", (10, 3): "dlg_health_emergency",
    (11, 1): "dlg_weather_smalltalk", (11, 2): "dlg_weather_smalltalk", (11, 3): "dlg_weather_smalltalk",
    (12, 1): "dlg_market_shopping", (12, 2): "dlg_transport_travel", (12, 3): "dlg_greet_and_farewell",
}
WEEK_GRAMMAR = {
    1: "core_grammar_for_beginners", 2: "core_grammar_for_beginners", 3: "gram_1",
    4: "gram_1", 5: "gram_2", 6: "gram_3", 7: "gram_13a", 8: "gram_15a",
    9: "gram_2", 10: "gram_10", 11: "gram_7", 12: "gram_1",
}

dialogue_ids = {d["id"] for d in dialogues}
grammar_ids = {g["id"] for g in grammar}
sessions = []
for wk in curriculum:
    for index, session in enumerate(wk["sessions"], start=1):
        session["id"] = f"w{wk['week']}s{index}"
        session["number"] = index
        session["week"] = wk["week"]
        session["week_title"] = wk["title"]
        session["month"] = wk["month"]
        session["total_sessions"] = len(wk["sessions"])
        session["audio"] = [AUDIO_DIR + a for a in (session.get("audio") or DEFAULT_AUDIO[wk["week"]])]
        dialogue_id = SESSION_DIALOGUES[(wk["week"], index)]
        session["dialogue"] = dialogue_id if dialogue_id in dialogue_ids else None
        grammar_id = WEEK_GRAMMAR[wk["week"]]
        session["grammar"] = grammar_id if grammar_id in grammar_ids else None
        sessions.append(session)

# topic shelves for the dictionary and review filters
theme_map = [
    {"id": "greetings_courtesies", "title": "Greetings & Courtesies", "icon": "hand"},
    {"id": "people_family", "title": "People & Family", "icon": "users"},
    {"id": "food_drink", "title": "Food & Drink", "icon": "bowl"},
    {"id": "numbers", "title": "Numbers & Money", "icon": "hash"},
    {"id": "colors", "title": "Colours", "icon": "palette"},
    {"id": "time_calendar", "title": "Time & Calendar", "icon": "clock"},
    {"id": "weather_nature", "title": "Weather & Nature", "icon": "cloud"},
    {"id": "animals", "title": "Animals", "icon": "paw"},
    {"id": "body_health", "title": "Body & Health", "icon": "heart"},
    {"id": "house_objects", "title": "Home & Objects", "icon": "home"},
    {"id": "directions_places", "title": "Directions & Places", "icon": "compass"},
    {"id": "daily_routine", "title": "Daily Routine", "icon": "list"},
    {"id": "verbs_grammar", "title": "Verbs & Grammar Words", "icon": "pencil"},
    {"id": "transport", "title": "Transport", "icon": "bus"},
    {"id": "school", "title": "School", "icon": "book"},
    {"id": "clothing", "title": "Clothing", "icon": "shirt"},
]

phrase_groups = []
_seen_groups = set()
for p in phrases:
    if p["group"] not in _seen_groups:
        _seen_groups.add(p["group"])
        phrase_groups.append({
            "id": p["group"],
            "title": cq.GROUP_TITLES.get(p["group"], p["group"].replace("_", " ").title()),
            "count": sum(1 for q in phrases if q["group"] == p["group"]),
        })
phrase_groups.sort(key=lambda g: (-g["count"], g["title"]))

out = {
    "meta": {
        "app": "Salama! — Learn Malagasy Gently",
        "project": "Vahiny Mianatra Malagasy",
        "audience": "Elderly American absolute beginner",
        "version": "3.3",
        "dialect_note": "Official Malagasy with regional (Tsimihety) dialect variants shown where available.",
        "counts": {
            "vocabulary": len(vocabulary), "phrases": len(phrases),
            "dialogues": len(dialogues), "grammar_lessons": len(grammar),
            "culture_notes": len(culture), "sessions": len(sessions),
            "words_with_pronunciation": sum(1 for w in vocabulary if w.get("pron")),
            "phrases_with_pronunciation": sum(1 for p in phrases if p.get("pron")),
            "rendered_word_clips": len(word_audio),
            "rendered_phrase_clips": len(phrase_audio),
            "rendered_line_clips": len(line_audio),
            "stress_lexicon": len(STRESS_LEXICON),
            "stress_conflicts": len(STRESS_CONFLICTS),
        },
    },
    "vocabulary": vocabulary,
    "phrases": phrases,
    "phraseGroups": phrase_groups,
    "dialogues": dialogues,
    "grammar": grammar,
    "culture": culture,
    "pronunciation": pron,
    "wordAudio": word_audio,
    "phraseAudio": phrase_audio,
    "lineAudio": line_audio,
    "curriculum": curriculum,
    "sessions": sessions,
    "themeMap": theme_map,
    "attribution": {
        "wikivoyage": "Some traveler phrases and the pronunciation guide are adapted from "
                      "Wikivoyage's 'Malagasy phrasebook' (en.wikivoyage.org), used under "
                      "Creative Commons Attribution-ShareAlike 3.0.",
        "peace_corps": "Lesson audio recordings are the public-domain Peace Corps Malagasy "
                       "Language Lessons (mirrored by fsi-language-courses.org and livelingua.com).",
        "abidi": "Word, phrase and dialogue pronunciations are synthesised with Abidi, the "
                 "Malagasy text-to-speech service by artifisialy.mg (abidi.artifisialy.mg).",
        "mms": "A few pronunciation clips use the Meta MMS Malagasy voice "
               "(facebook/mms-tts-mlg, CC BY-NC 4.0), kept where it reads an entry better.",
        "note": "Salama! is an independent learning product. Its lessons, structure and design "
                "are original; source works (Peace Corps Malagasy materials, lesson archives, "
                "dictionaries and phrasebooks) are used as compiled reference material only.",
    },
}

js = "window.CONTENT = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n"
path = os.path.join(BASE, "APP", "data", "content.js")
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    f.write(js)
print("Wrote", path, f"({os.path.getsize(path)//1024} KB)")
print("  vocabulary:", len(vocabulary), "| phrases:", len(phrases),
      "| dialogues:", len(dialogues), "| grammar:", len(grammar),
      "| culture:", len(culture), "| weeks:", len(curriculum),
      "| sessions:", len(sessions))
pron_counts = {}
for item in vocabulary + phrases:
    source = item.get("pron_source")
    if source:
        pron_counts[source] = pron_counts.get(source, 0) + 1
covered = sum(1 for item in vocabulary + phrases if item.get("pron"))
total = len(vocabulary) + len(phrases)
print("  pronunciation:", json.dumps(pron_counts),
      "| covered: %d/%d (%.0f%%)" % (covered, total, 100.0 * covered / total))
print("  audio: word clips", len(word_audio), "| phrase clips", len(phrase_audio),
      "| line clips", len(line_audio),
      "| stress lexicon", len(STRESS_LEXICON))
if STRESS_CONFLICTS:
    print("  stress conflicts (hand table vs printed dictionary):",
          ", ".join("%s %d/%d" % row for row in STRESS_CONFLICTS),
          "— see RESEARCH/pron_qa.html")
print("  repairs:", json.dumps(cq.GARBAGE_COUNT))
if CORRECTIONS:
    print("  native-speaker corrections: %d applied, %d approved, %d disputed"
          % (CORRECTION_STATS["applied"], CORRECTION_STATS["verified"],
             CORRECTION_STATS["wrong"]))
for key, old_mg, new_mg, old_en, new_en in CORRECTION_LOG:
    if new_mg:
        print("  correction wins %-28s mg %r -> %r" % (key, old_mg, new_mg))
    if new_en:
        print("  correction wins %-28s en %r -> %r" % (key, old_en, new_en))

counts = {}
for item in out["vocabulary"] + out["phrases"]:
    if item.get("pron_verified"):
        counts["verified"] = counts.get("verified", 0) + 1
print("  approved pronunciation entries:", counts.get("verified", 0))

# ---------------- keep the README counts honest ----------------
# The numbers used to be typed by hand in two READMEs and drifted from the
# build. The block between the markers is now generated.
COUNTS_BLOCK = (
    "<!-- counts:start -->\n"
    "**Current build:** {vocabulary} dictionary entries, {phrases} phrases, "
    "{dialogues} dialogues, {grammar} grammar topics, {culture} culture notes, "
    "{sessions} sessions over {weeks} weeks. Pronunciation is written for "
    "{pron:.0f}% of words and phrases.\n"
    "<!-- counts:end -->"
).format(
    vocabulary=len(vocabulary), phrases=len(phrases), dialogues=len(dialogues),
    grammar=len(grammar), culture=len(culture), sessions=len(sessions),
    weeks=len(curriculum), pron=100.0 * covered / total)

readme = os.path.join(BASE, "APP", "README.md")
if os.path.exists(readme):
    text = open(readme, encoding="utf-8").read()
    if "<!-- counts:start -->" in text:
        text = re.sub(r"<!-- counts:start -->.*?<!-- counts:end -->",
                      COUNTS_BLOCK.replace("\\", "\\\\"), text, flags=re.S)
        open(readme, "w", encoding="utf-8").write(text)
        print("  synced counts block in APP/README.md")
