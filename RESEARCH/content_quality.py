#!/usr/bin/env python3
"""Content-cleaning helpers for the Salama! content pipeline.

The source dictionaries and phrasebooks were compiled from several documents, and
the merge left three classes of defect in the generated content pack:

1. Glosses carrying fragments of a neighbouring dictionary line
   (e.g. "mother (formal/compound form); mother reraka ad), tired").
2. Phrases whose Malagasy and English columns slipped out of alignment, so the
   app taught an English sentence as if it were Malagasy.
3. Pronunciation hints on only ~1% of the vocabulary.

This module fixes (1) and (2) deterministically at build time and generates
clearly-labelled approximate respellings for (3). Every repair it makes is
counted so the build can print what changed.
"""

import re
import unicodedata

# Fragments left behind by the dictionary merge. A gloss segment containing one
# of these is a mangled neighbour line, never a real meaning.
GARBAGE_PATTERNS = [
    re.compile(r"\b[a-z'-]+\s+ad\)", re.I),   # "... reraka ad), tired"
    re.compile(r"\b[a-z'-]+\s+con\]", re.I),  # "... na con], or; either"
    re.compile(r"\bskm\b", re.I),             # "skin; skm"
    re.compile(r"\]\s*,", re.I),
]

# English function words that never occur as Malagasy words. Anything shared
# between the two languages (no, be, fa, dia, izy, aho, ny, sy, ho, te, any,
# koa, bus, ...) is deliberately excluded: "Inona no vaovao?" and "Tsara be"
# are correct Malagasy and must not be filtered.
ENGLISH_WORDS = {
    "the", "you", "your", "yours", "is", "are", "am", "was", "were", "what",
    "where", "when", "which", "how", "why", "who", "this", "that", "these",
    "those", "there", "would", "could", "should", "please", "have", "has",
    "does", "doesn't", "don't", "not", "my", "me", "i", "we", "they", "he",
    "she", "it", "and", "or", "but", "with", "from", "for", "about", "some",
    "want", "know", "speak", "understand", "cost", "much", "many", "here",
    "very", "hello", "thank", "sorry", "excuse", "goodbye", "good",
    "morning", "night", "anyone", "someone", "ask", "asks", "said", "say",
    "get", "off", "station", "stops", "driver", "assistant", "sometimes",
    "if", "then", "banks", "bank", "exchange", "airport", "hotels",
    "bought", "can", "been", "will", "must", "during", "rain", "heavy",
    "sheltered", "trade", "winds", "arid", "metric", "system", "unit",
    "in", "of", "on", "at", "to",
}

# Words that carry Malagasy spelling but are legitimately borrowed into it;
# they must not be mistaken for English lines.
MALAGASY_SAFE = {
    "dite", "kafe", "labiera", "sipa", "hopitaly", "dokotera", "sekretra",
    "restaurant", "karta", "hotely", "bisy", "moto", "taxi", "telefaonina",
}

GARBAGE_COUNT = {"gloss_segments": 0, "gloss_entries": 0, "phrases_dropped": 0,
                 "phrases_repaired": 0, "phrases_regrouped": 0,
                 "pron_generated": 0, "pron_skipped": 0, "themes_stripped": 0}


# --------------------------------------------------------------------------
# audio file names
# --------------------------------------------------------------------------
def audio_slug(text):
    """A file name that is safe on every filesystem, derived from an entry id.

    Some dictionary entries carry a variant in their id ("fatana_/_fatampera",
    "veloma/mazotoa_+_alarobia_koa"). A "/" in an id silently truncates the path,
    which is how 105 entries ended up with no rendered audio. The id in the data
    is left alone (progress is keyed by it); only the file name is slugged.

    Identity for ids that are already safe, so existing clips keep their names.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return slug or "entry"


# --------------------------------------------------------------------------
# glosses
# --------------------------------------------------------------------------
def _is_garbage(segment: str) -> bool:
    return any(p.search(segment) for p in GARBAGE_PATTERNS)


def _lemma(text: str) -> str:
    text = text.strip().lower()
    for prefix in ("to ", "a ", "an ", "the "):
        if text.startswith(prefix):
            text = text[len(prefix):]
    return re.sub(r"[^a-z' -]", "", text).strip()


# Fragments left over after an annotation is cut away: "seller; merchant na
# con], or; either" leaves "either".
ORPHAN_FRAGMENTS = {
    "either", "or", "and", "but", "when", "if", "also", "tired", "con",
    "see", "etc", "lit", "coll", "fig", "esp", "etc.",
}

# Dictionary tail annotations that leaked into the gloss column: "hospital i
# art. before proper names", "blood raha con], when, when" etc.
ANNOTATION_TAIL = re.compile(
    r"\s(?:[a-z]\s+)?(?:art\.|con\]|ad\))\s*.*$|"
    r"\s+(?:before|after)\s+proper names.*$|"
    r"\s+see\s+[A-Z].*$", re.I)


def trim_annotations(text: str) -> str:
    return ANNOTATION_TAIL.sub("", text or "").strip(" ,;")


def clean_gloss(en: str):
    """Split a contaminated gloss into a primary sense and alternate senses.

    Returns (primary, alternates). Alternate senses are the *other* dictionary
    meanings that survived cleaning, so the UI can show "also: ..." instead of
    a semicolon soup on a flashcard.
    """
    if not en:
        return "", []
    segments = [s.strip() for s in re.split(r";", en) if s.strip()]
    kept, seen = [], set()
    for seg in segments:
        if _is_garbage(seg):
            GARBAGE_COUNT["gloss_segments"] += 1
            continue
        seg = trim_annotations(re.sub(r"\s{2,}", " ", seg))
        if not seg:
            continue
        key = _lemma(seg)
        if key in seen:
            continue
        seen.add(key)
        kept.append(seg)
    if not kept:
        return "", []
    primary = kept[0]
    # The primary sense keeps its slash-pairs ("Hello! / Hi!") but drops a
    # duplicated second half ("see _lemma"), a fragment left behind by a cut
    # annotation ("skm" -> "either"), or a longer restatement of itself.
    alts = []
    for candidate in kept[1:4]:
        lemma = _lemma(candidate)
        if not lemma or lemma == _lemma(primary):
            continue
        if lemma in ORPHAN_FRAGMENTS or len(lemma) < 3:
            continue
        if _lemma(primary) and _lemma(primary) in lemma:
            continue
        alts.append(candidate)
    if segments and alts != segments[1:4]:
        GARBAGE_COUNT["gloss_entries"] += 1
    return primary, alts


# --------------------------------------------------------------------------
# phrases
# --------------------------------------------------------------------------
def looks_english(text: str) -> bool:
    """True when a field reads as an English sentence, not Malagasy."""
    tokens = re.findall(r"[A-Za-z']+", text.lower())
    if not tokens:
        return False
    if any(t in MALAGASY_SAFE for t in tokens) and len(tokens) <= 2:
        return False
    hits = sum(1 for t in tokens if t in ENGLISH_WORDS)
    # Two or more English function words, or one when the text is very short.
    return hits >= 2 or (hits >= 1 and len(tokens) <= 3)


def is_fragment(en: str) -> bool:
    """True for an English field that is only a note, not a meaning.

    "No", "Yes", "Hi" are legitimate meanings, so this only rejects an empty
    field, a bare parenthetical, or punctuation.
    """
    s = en.strip()
    if not s:
        return True
    if s.startswith("(") and s.endswith(")"):
        return True
    if not re.search(r"[A-Za-z0-9]", s):
        return True
    return False


def duplicated_pair(mg: str, en: str) -> bool:
    """True when the 'English' column is just the Malagasy line plus a note.

    e.g. mg "lavitra be eto io, tompoko" / en "Lavitra be eto io. (neutral form)"
    """
    mg_tokens = set(re.findall(r"[a-z']+", mg.lower()))
    en_tokens = set(re.findall(r"[a-z']+", re.sub(r"\([^)]*\)", "", en).lower()))
    if len(en_tokens) < 2:
        return False
    shared = en_tokens & mg_tokens
    return len(shared) >= 2 and len(shared) / len(en_tokens) >= 0.6


JUNK_MG = re.compile(r"^\s*(mr|mrs|ms|dr|miss)\.", re.I)


def rescue_phrase(mg, en, vocab_index):
    """Return a corrected (mg, en) pair, or None if the row is unrecoverable.

    Where the Malagasy column actually holds a real word we already know, the
    dictionary was right and only the English slipped, so we re-pair from it.
    """
    if not looks_english(mg):
        return None
    key = re.sub(r"\s+", " ", mg.strip().lower())
    if key in vocab_index:
        return mg, vocab_index[key]
    return None


# --------------------------------------------------------------------------
# approximate pronunciation
# --------------------------------------------------------------------------
_VOWEL_SOUND = {
    "a": "ah", "e": "ay", "i": "ee", "o": "oo", "y": "ee",
    "ao": "ah-oo", "oa": "oh-ah", "ai": "eye", "ay": "eye", "oi": "oy",
    "au": "ah-oo", "ei": "ay-ee", "ea": "ay-ah",
}
_NUCLEI = ("ao", "oa", "ai", "ay", "oi", "au", "ei", "ea")
_WORD_OK = re.compile(r"^[a-zA-Z' -]+$")


def syllabify(word: str):
    syllables, current, i = [], "", 0
    while i < len(word):
        ch = word[i]
        if ch.lower() in "aeiouy":
            nucleus = ch
            pair = word[i:i + 2].lower()
            if len(pair) == 2 and pair in _NUCLEI:
                nucleus = word[i:i + 2]
                i += 1
            current += nucleus
            syllables.append(current)
            current = ""
        else:
            current += ch
        i += 1
    if current:
        if syllables:
            syllables[-1] += current
        else:
            syllables.append(current)
    return syllables


def _respell_syllable(syl: str) -> str:
    out = syl.lower().replace("j", "dz").replace("ts", "ts")
    for letters in ("ao", "oa", "ai", "ay", "oi", "au", "ei", "ea"):
        if letters in out:
            out = out.replace(letters, _VOWEL_SOUND[letters])
    for letter in ("a", "e", "i", "o", "y"):
        out = out.replace(letter, _VOWEL_SOUND[letter])
    out = re.sub(r"oo-oo|ah-ah|ee-ee", lambda m: m.group(0).split("-")[0], out)
    return out


def approx_pron(mg: str):
    """A labelled approximate respelling, e.g. "sah-LAH-mah".

    Applies the standard rule: stress the penultimate syllable, or the
    antepenultimate in words ending in -ka, -tra, -na. Returns None when the
    spelling is too irregular to respell safely.
    """
    word = mg.strip().strip("!?.,;:").lower()
    if not word or " " in word or not _WORD_OK.match(word):
        return None
    if "-" in word or "'" in word:
        return None
    if len(word) > 13 or len(word) < 3:
        return None
    if re.search(r"[^aeiouy\s'-]{4,}", word):
        return None
    syllables = syllabify(word)
    if not syllables or len(syllables) > 4:
        return None
    parts = [_respell_syllable(s) for s in syllables]
    if any(not p for p in parts):
        return None
    stress = len(parts) - 2
    if len(parts) > 2 and word.endswith(("ka", "tra", "na")):
        stress = len(parts) - 3
    stress = max(0, min(stress, len(parts) - 1))
    parts[stress] = parts[stress].upper()
    return "-".join(parts)


# --------------------------------------------------------------------------
# inline annotations
# --------------------------------------------------------------------------
DIALECT_INLINE = re.compile(r"\s*\(\s*(?:tsm|tsimihety)\s*:?\s*([^)]*)\)", re.I)
OFFICIAL_INLINE = re.compile(r"\s*\(\s*(?:off|official)\s*:?\s*([^)]*)\)", re.I)


def split_dialect(text: str):
    """Pull an inline "(tsm: pia)" out of the Malagasy field.

    Left in place it shows up inside quiz options and dictionary entries, where
    it reads as part of the word.
    """
    if not text:
        return text, ""
    match = DIALECT_INLINE.search(text)
    if not match:
        return text, ""
    cleaned = DIALECT_INLINE.sub("", text).strip()
    return cleaned, match.group(1).strip()


def strip_official(text: str) -> str:
    return OFFICIAL_INLINE.sub("", text or "").strip()


def _ascii_letters(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return re.sub(r"[^a-z]", "", decomposed)


def split_variants(mg: str):
    """'hopitaly / hôpitaly / lôpitaly' -> ('hopitaly', ['hôpitaly', 'lôpitaly']).

    Only splits when the alternatives really are spellings of the same word, so
    phrases that use a slash for other reasons are left alone.
    """
    text = (mg or "").strip()
    if "/" not in text:
        return text, []
    parts = [p.strip() for p in re.split(r"\s*/\s*", text) if p.strip()]
    if len(parts) < 2:
        return text, []
    base = _ascii_letters(parts[0])
    if len(base) < 3:
        return text, []
    for candidate in parts[1:]:
        if not _ascii_letters(candidate).startswith(base[:3]):
            return text, []
    return parts[0], parts[1:3]


SPEAKER_STAGE = re.compile(r"^(.*?)\s*\(([^)]*)\)\s*$")


def split_stage(speaker: str):
    """'Person 1 (walking)' -> ('Person 1', 'walking')."""
    match = SPEAKER_STAGE.match(speaker or "")
    if not match:
        return (speaker or "").strip(), ""
    return match.group(1).strip(), match.group(2).strip()


# --------------------------------------------------------------------------
# phrase groups
# --------------------------------------------------------------------------
# The pack produced 30 overlapping group ids ("greetings_courtesies" and
# "greetings" and "polite_words" were the same shelf). Consolidate to the
# handful of situations a learner actually thinks in.
GROUP_MAP = {
    "greetings_courtesies": "greetings", "greet_and_farewell": "greetings",
    "greetings": "greetings", "polite_words": "greetings",
    "polite_expressions": "greetings", "small_talk": "greetings",
    "introducing_yourself": "introducing", "introductions": "introducing",
    "general": "basics", "basic_needs": "basics",
    "food_drink": "food", "eating_ordering": "food",
    "market": "market", "shopping": "market", "market_shopping": "market",
    "numbers": "money", "money": "money",
    "transport": "transport", "transport_travel": "transport",
    "directions_places": "directions", "directions_travel": "directions",
    "travel_sightseeing": "travel", "traveler": "travel",
    "accommodation": "travel",
    "body_health": "health", "health_emergency": "health",
    "emergencies": "emergencies",
    "weather_nature": "weather", "weather_smalltalk": "weather",
    "time_calendar": "time", "time_appointments": "time",
    "administration": "official", "communications": "official",
    "colors": "colours",
}

GROUP_TITLES = {
    "greetings": "Greetings & politeness",
    "introducing": "Introducing yourself",
    "basics": "Everyday basics",
    "food": "Food & eating",
    "market": "Market & shopping",
    "money": "Money & numbers",
    "transport": "Transport",
    "directions": "Directions & places",
    "travel": "Travel & sightseeing",
    "health": "Health",
    "emergencies": "Emergencies",
    "weather": "Weather",
    "time": "Time & dates",
    "official": "Official business",
    "colours": "Colours",
}


def normalise_group(group: str) -> str:
    return GROUP_MAP.get(group, "basics")


def clean_dialogue_title(title: str) -> str:
    """Strip scrape headings from a dialogue title."""
    t = re.sub(r"\s+", " ", title).strip()
    t = re.sub(r"^Exercise [A-Z]+\s*(ANSWER)?\s*[-–:]?\s*", "", t, flags=re.I)
    # Lesson PDFs set these as headings ("EXCUSE ME / PLEASE / PARDON - walking
    # past someone"), so judge the part before the dash, then trim the aside.
    head, sep, _ = t.partition(" - ")
    head_letters = [c for c in head if c.isalpha()]
    if head_letters and sum(1 for c in head_letters if c.isupper()) / len(head_letters) > 0.7:
        if sep and len(head) > 8:
            t = head
        t = t.lower()
        t = t[0].upper() + t[1:] if t else t
    t = re.sub(r"\s*\((Bako[^)]*|Peace Corps[^)]*|Week \d+[^)]*|every Malagasy table!|[^)]*to be converted[^)]*)\)", "", t, flags=re.I)
    t = re.sub(r"\s*-\s*the guest initiates.*$", "", t, flags=re.I)
    t = re.sub(r"\s*-\s*the reply you might get$", "", t, flags=re.I)
    t = re.sub(r"\s*\(.*?\)\s*$", "", t)
    t = t.strip(" -–:")
    if not t:
        return "Conversation"
    return t[:1].upper() + t[1:]
