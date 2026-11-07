#!/usr/bin/env python3
"""Malagasy pronunciation: stress, English respelling, and speech-engine adaptation.

Three separate jobs live here, and they must not be confused with one another:

* `stress_position()` — which syllable carries stress. Dictionary first, then the
  documented default.
* `respell()` — an **English-facing** spelling hint for the learner ("tra-NOU").
  Letters are English, so it must never be fed to a speech engine.
* `adapt()` / `speech_text()` — Malagasy rewritten into the orthography of a
  *foreign* voice (French, Romanian, Italian…). This is what the browser should
  speak. `APP/js/speech.js` implements the same tables; `check_parity.py`
  asserts the two produce identical strings.

Sources and what they actually say
----------------------------------
* Default stress is penultimate. A lexical class of "weak" stems ending in
  -na, -ka, -tra takes antepenultimate stress, but that is a lexical property,
  not a spelling rule: olona is [uˈluna] (penult) while vohitra is [ˈvuhiʈʂa]
  (antepenult). So: dictionary accent first, then a -tra-only heuristic.
* Vowels: a /a/, e /e/, i /i/, y /i/ (final), o /u/. "o" is "oo" and "e" is
  "eh" — the two mistakes English speakers make most often.
* Consonants: j /dz/, ts /ts/, tr /ʈʂ/, dr /ɖʐ/; "ny" is /ni/, not /ɲ/;
  "ng" is /ŋg/ and is a syllable onset, never a prenasalised cluster.
* ao and oa vary between [au̯]/[ua̯] and contracted [o] in Merina speech.
  Merina "ao" is [o], so the adapter writes "ô" (fr) or "o" (ro/it/es).
* Final vowels are often devoiced in speech. They are never dropped here:
  deletion is optional and a missing vowel teaches the wrong word.
* h is *always* pronounced. No adapter may delete it.

Speech engines: no browser or operating system ships an installed Malagasy
voice (checked November 2026). A Malagasy *model* does exist
(`facebook/mms-tts-mlg`, CC-BY-NC 4.0); `render_audio.py` uses it to write
per-word clips, and the app prefers those clips to any fallback voice.
"""
import os
import re
import sys
import unicodedata
import zipfile

VOWELS = "aeiouy"

# Two vowel letters that behave as one syllable nucleus.
DIPHTHONGS = ("ao", "ai", "ay", "ei", "ou", "au", "oi")

# Words where a written "ao" actually spans a syllable boundary. Spelling alone
# cannot decide this ("vao" is also a word of its own), so the dictionary's own
# stress mark is the authority: Rasoloson accents vaovao on the third syllable
# from the end, which is only possible if it is va-o-va-o rather than vao-vao.
HIATUS_AO = frozenset({"vaovao"})


def _is_nucleus_pair(word, pair):
    if pair not in DIPHTHONGS:
        return False
    if pair == "ao" and word in HIATUS_AO:
        return False
    return True

# English-facing respelling for each nucleus (respell(), display only).
NUCLEUS_SOUND = {
    "a": "ah", "e": "eh", "i": "ee", "o": "oo", "y": "ee",
    "ao": "oh", "ai": "eye", "ay": "eye", "ei": "ay-ee",
    "ou": "oh", "au": "ow", "oi": "oy",
}

# Consonants whose English reading is wrong for Malagasy (display only).
CONSONANT_SOUND = {"j": "dz"}


# --------------------------------------------------------------------------
# spelling
# --------------------------------------------------------------------------
def strip_accents(text):
    decomposed = unicodedata.normalize("NFD", text or "")
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def _plain(word):
    """Lower-case ASCII-ish working copy. Accents carry stress, not sound, and
    syllabify() would treat "ô" as a consonant, so they are removed first."""
    return strip_accents((word or "").strip()).lower()


def syllabify(word):
    """Split a Malagasy word into written syllables.

    "oa" stays two syllables (ahoana -> a-ho-a-na); "ao" is one (misaotra ->
    mi-sao-tra). Trailing consonants attach to the preceding syllable.
    """
    word = _plain(word)
    syllables, current, index = [], "", 0
    while index < len(word):
        char = word[index]
        if char in VOWELS:
            nucleus = char
            pair = word[index:index + 2]
            if len(pair) == 2 and _is_nucleus_pair(word, pair):
                nucleus = pair
                index += 1
            current += nucleus
            syllables.append(current)
            current = ""
        else:
            current += char
        index += 1
    if current:
        if syllables:
            syllables[-1] += current
        else:
            syllables.append(current)
    syllables = _split_prenasal(syllables)
    return [s for s in syllables if s]


# "ng" is deliberately absent: it is a velar digraph and stays an onset
# (ma-nga-tsia-ka, to-nga). "nk"/"mp" are not prenasalised either.
PRENASAL_ONSET = re.compile(r"^(n|m)(?=[ptkbd]|ts|tr|dr)")


def _split_prenasal(syllables):
    """Keep the nasal of a prenasalised cluster with the previous vowel.

    Antananarivo is an-ta-na-na-ri-vo, not a-nta-na-na-ri-vo; trondro is
    tron-dro. The nasal closes the preceding syllable and the stop opens the
    next one.
    """
    for index in range(1, len(syllables)):
        match = PRENASAL_ONSET.match(syllables[index])
        if match and syllables[index - 1] and syllables[index - 1][-1] in VOWELS:
            syllables[index - 1] += match.group(1)
            syllables[index] = syllables[index][1:]
    return syllables


def vowel_count(text):
    """Number of vowel nuclei in a fragment (consonant-only tails do not count)."""
    plain = _plain(text)
    count, index = 0, 0
    while index < len(plain):
        if plain[index] in VOWELS:
            count += 1
            pair = plain[index:index + 2]
            if len(pair) == 2 and pair in DIPHTHONGS:
                index += 1
        index += 1
    return count


def _key(word):
    plain = strip_accents(unicodedata.normalize("NFC", word or "")).lower()
    plain = plain.replace("\u2019", "'")
    return re.sub(r"\s+", " ", plain).strip()


# --------------------------------------------------------------------------
# stress
# --------------------------------------------------------------------------
# Verified entries. The value is the stressed syllable counted from the end:
# 1 = last, 2 = penultimate, 3 = antepenultimate. Every value here was checked
# by hand against the Rasoloson dictionary or a Peace Corps lesson sound file.
CURATED_STRESS = {
    "salama": 2, "misaotra": 2, "azafady": 2, "veloma": 2, "trano": 2,
    "vody": 2, "manasa": 2, "olona": 2, "vohitra": 3, "tanana": 3,
    "malagasy": 2, "fahasalamana": 2, "antananarivo": 2, "manao": 2,
    "ahoana": 3, "tonga": 2, "soa": 2, "mazotoa": 2,
    "mandrapihaona": 3, "mandrosoa": 2, "mipetraka": 2,
    "fianakaviana": 3, "zanaka": 2, "vady": 2, "reny": 2,
    "sakafo": 2, "vary": 2, "rano": 2, "mofo": 2, "hena": 2,
    "trondro": 2, "akoho": 2, "atody": 2, "tsena": 2, "vola": 2,
    "volana": 2, "andro": 2, "alina": 2, "maraina": 2, "hariva": 2,
    "androany": 2, "omaly": 2, "rahampitso": 2, "herinandro": 3,
    "taona": 2, "firy": 2, "inona": 2, "iza": 2, "aiza": 2,
    "mahafinaritra": 3, "tsara": 2, "ratsy": 2, "kely": 2,
    "lehibe": 3, "vaovao": 3, "tompoko": 2, "ramatoa": 3,
    "rahalahy": 3, "rahavavy": 3, "zanakalahy": 3, "zanakavavy": 3,
    "dadabe": 3, "nenibe": 3, "mpianatra": 3, "mpampianatra": 3,
    "dokotera": 3, "hopitaly": 2, "marary": 2, "fanafody": 3,
    "lalana": 2, "manakory": 2,
}

ACCENTED = "\u00e0\u00e1\u00e2\u00e4\u00e8\u00e9\u00ea\u00eb\u00ec\u00ed\u00ee\u00ef\u00f2\u00f3\u00f4\u00f6\u00f9\u00fa\u00fb"

# The DOCX kept only "é" (mostly) and "â" after the PDF-to-Word conversion, so
# the recoverable set is small and must be filtered hard: an accent that does
# not sit on one of the last three syllables is an artefact, not a stress mark.
MIN_STRESS_LEXICON_ENTRIES = 200


def _lexicon_from_dict_text(text):
    """Recover stress positions from a dictionary that marks them.

    The OCR of the Rasoloson dictionary lost its accents, but the DOCX kept
    them (ianaréo, matétika, fahasalamàna). The position of the mark inside the
    word gives the stressed syllable directly.
    """
    found = {}
    for token in re.findall(r"[^\s\d(),.;:!?/\"']{3,}", text or ""):
        low = token.lower()
        accent_at = next((i for i, ch in enumerate(low) if ch in ACCENTED), None)
        if accent_at is None:
            continue
        key = re.sub(r"[^a-z' -]", "", strip_accents(token).lower()).strip(" -'")
        if len(key) < 3 or len(key) > 18 or " " in key:
            continue
        total = vowel_count(key)
        if total < 2:
            continue
        before = vowel_count(low[:accent_at])
        if before < 1:
            continue
        from_end = total - before
        # Rejected: an accent on the vowel of a one-vowel token, or further
        # back than the antepenultimate, is a conversion artefact.
        if from_end < 1 or from_end > 3:
            continue
        # A hyphenated compound is only usable if every part has a vowel;
        # otherwise it is OCR debris ("anomezan-tsky", "famerim-bsl").
        if "-" in key and any(not re.search(r"[aeiou]", part) for part in key.split("-")):
            continue
        found.setdefault(key, from_end)
    return found


def load_stress_lexicon(docx_path=None, warn=True):
    """Curated entries plus every usable stress mark the dictionary kept."""
    lexicon = dict(CURATED_STRESS)
    if not docx_path or not os.path.exists(docx_path):
        if warn:
            print("WARNING pronunciation: stress dictionary not found"
                  + (" (%s)" % docx_path if docx_path else "")
                  + " — falling back to the %d curated entries. Every other word"
                  " gets the default penultimate rule." % len(CURATED_STRESS),
                  file=sys.stderr)
        return lexicon
    try:
        with zipfile.ZipFile(docx_path) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", "ignore")
        text = re.sub(r"<[^>]+>", " ", xml)
        recovered = _lexicon_from_dict_text(text)
        for word, position in recovered.items():
            lexicon.setdefault(word, position)
        if warn and len(recovered) < MIN_STRESS_LEXICON_ENTRIES:
            print("WARNING pronunciation: only %d stress marks recovered from %s"
                  % (len(recovered), os.path.basename(docx_path)), file=sys.stderr)
    except (KeyError, OSError, zipfile.BadZipFile) as error:
        if warn:
            print("WARNING pronunciation: could not read %s (%s)"
                  % (docx_path, error), file=sys.stderr)
    return lexicon


def stress_position(word, lexicon=None):
    """Stressed syllable counted from the end, plus where the answer came from."""
    if lexicon is None:
        lexicon = CURATED_STRESS
    key = _key(word)
    if key in lexicon:
        return lexicon[key], "dictionary"
    syllables = syllabify(word)
    if len(syllables) <= 1:
        return 1, "single"
    # Documented weak-stem pattern: -tra words take antepenultimate stress
    # unless the dictionary says otherwise (misaotra is penultimate).
    if len(syllables) >= 3 and key.endswith("tra"):
        return 3, "rule"
    return 2, "rule"


def stress_conflicts(docx_path=None):
    """Words where the hand-checked table and the printed dictionary disagree.

    These are the entries that most need a native ear, so the build prints the
    count and pron_qa.py lists them first. Nothing resolves them automatically:
    the hand table is unverified and the OCR'd dictionary is not perfect either.
    """
    if not docx_path or not os.path.exists(docx_path):
        return []
    try:
        with zipfile.ZipFile(docx_path) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", "ignore")
    except (KeyError, OSError, zipfile.BadZipFile):
        return []
    recovered = _lexicon_from_dict_text(re.sub(r"<[^>]+>", " ", xml))
    return sorted((word, CURATED_STRESS[word], position)
                  for word, position in recovered.items()
                  if word in CURATED_STRESS and CURATED_STRESS[word] != position)


def stress_report(lexicon):
    """Compare the curated and recovered sources, for the QA pass.

    Returns (disagreements, rejected_noise). Disagreements are words where the
    hand-checked table and the dictionary accent point at different syllables:
    those are the entries that most need a native ear.
    """
    curated = set(CURATED_STRESS)
    disagreements = []
    for word, position in sorted(lexicon.items()):
        if word in curated and CURATED_STRESS[word] != position:
            disagreements.append((word, CURATED_STRESS[word], position))
    noisy = sorted(w for w in lexicon
                   if w not in curated and re.search(r"[^a-z]", w))
    return disagreements, noisy


# --------------------------------------------------------------------------
# English respelling (display only — never speak this)
# --------------------------------------------------------------------------
def _respell_syllable(syllable):
    out, index = "", 0
    while index < len(syllable):
        pair = syllable[index:index + 2].lower()
        if len(pair) == 2 and pair in NUCLEUS_SOUND:
            out += NUCLEUS_SOUND[pair]
            index += 2
            continue
        char = syllable[index]
        lower = char.lower()
        if lower in NUCLEUS_SOUND:
            out += NUCLEUS_SOUND[lower]
        elif lower in CONSONANT_SOUND:
            out += CONSONANT_SOUND[lower]
        else:
            out += lower
        index += 1
    # "ng" stays two letters. English readers say /ŋ/ for it, so the guide
    # includes an explicit note; writing "n-g" here would break the
    # one-group-per-syllable invariant that validate_content.py checks.
    return out


def respell(word, lexicon=None):
    """Return ("tra-NOO", "rule"|"dictionary") or (None, None).

    A hyphen inside a Malagasy entry ("rahalahin-dray", "manam-bady") marks a
    compound boundary, not a syllable break, and the nasal before it belongs to
    the previous syllable. Each part is therefore respelled on its own and the
    parts are joined with a space — otherwise the hint grew a stray "-n-" group.

    The stressed syllable is upper case; hyphens separate syllables. Words with
    spaces, digits or punctuation are skipped because they are phrases or
    placeholders, and a wrong stress hint is worse than none.
    """
    text = strip_accents((word or "").strip()).strip("!?.,;:")
    if not text or " " in text or not re.search(r"[A-Za-z]", text):
        return None, None
    if not re.match(r"^[A-Za-z'’-]+$", text):
        return None, None
    if "-" in text.strip("-"):
        parts, sources = [], []
        for piece in re.split(r"-+", text):
            if not piece:
                continue
            guess, source = respell(piece, lexicon)
            if not guess:
                return None, None
            parts.append(guess)
            sources.append(source)
        if not parts:
            return None, None
        return " ".join(parts), ("dictionary" if all(s == "dictionary" for s in sources) else "rule")
    if len(text) > 18:
        return None, None
    syllables = syllabify(text)
    if not syllables or len(syllables) > 7:
        return None, None
    position, source = stress_position(text, lexicon)
    position = max(1, min(position, len(syllables)))
    stressed_index = len(syllables) - position
    parts = []
    for index, syllable in enumerate(syllables):
        sound = _respell_syllable(syllable)
        if not sound:
            return None, None
        if index == stressed_index:
            sound = sound.upper()
        parts.append(sound)
    return "-".join(parts), source


def respell_phrase(text, lexicon=None, limit=8):
    """Word-by-word respelling for a phrase: "mee-SOH-trah beh-TSAH-kah"."""
    if not text:
        return None
    words = re.findall(r"[A-Za-z'’-]+", strip_accents(text))
    if not words or len(words) > limit:
        return None
    parts = []
    for word in words:
        guess, _ = respell(word, lexicon)
        parts.append(guess or word.lower())
    return " ".join(parts)


# --------------------------------------------------------------------------
# speech-engine adaptation (this is what a foreign voice should be given)
# --------------------------------------------------------------------------
# Malagasy letter -> the letters that make the same sound in the target
# language. Longest keys win. Notes:
#   * "ao" is Merina [o] -> "ô" (fr) / "o" (ro, it, es, ca). "aou" read [au]
#     and "a-ou" read as two syllables were both wrong.
#   * "oa" is two syllables -> "o-a", never French "oua" ([wa]).
#   * "o" is [u] -> "ou" (fr) / "u" (everywhere else).
#   * "j" is /dz/, "ts" is /ts/ (ro has "ț", ca "tz").
#   * h is never deleted. Spanish is the worst fallback precisely because its
#     h is silent; Romanian is the best because its h, ț, and final vowels
#     all match.
ADAPTERS = {
    "fr": {"ao": "ô", "oa": "o-a", "ai": "aï", "ay": "aï", "ei": "é-i",
           "oi": "o-i", "ou": "o-u", "au": "a-ou", "j": "dz", "y": "i",
           "o": "ou", "e": "é"},
    "ro": {"ao": "o", "oa": "o-a", "ai": "ai", "ay": "ai", "ei": "e-i",
           "oi": "o-i", "ou": "o-u", "au": "au", "j": "dz", "ts": "ț",
           "y": "i", "o": "u", "e": "e"},
    "it": {"ao": "ò", "oa": "o-a", "ai": "ai", "ay": "ai", "ei": "e-i",
           "oi": "o-i", "ou": "o-u", "au": "au", "j": "dz", "y": "i",
           "o": "u", "e": "e"},
    "es": {"ao": "o", "oa": "o-a", "ai": "ai", "ay": "ai", "ei": "e-i",
           "oi": "o-i", "ou": "o-u", "au": "au", "j": "dz", "y": "i",
           "o": "u", "e": "e"},
    "ca": {"ao": "o", "oa": "o-a", "ai": "ai", "ay": "ai", "ei": "e-i",
           "oi": "o-i", "ou": "o-u", "au": "au", "j": "tz", "ts": "ts",
           "y": "i", "o": "u", "e": "e"},
    "pt": {"ao": "o", "oa": "o-a", "ai": "ai", "ay": "ai", "ei": "ei",
           "oi": "oi", "ou": "o-u", "au": "au", "j": "dz", "ts": "ts",
           "y": "i", "o": "u", "e": "ê"},
    "en": {"ao": "oh", "oa": "oo-ah", "ai": "eye", "ay": "eye", "ei": "ay-ee",
           "oi": "oy", "ou": "oh", "au": "ow", "j": "dz", "y": "ee",
           "o": "oo", "e": "eh"},
}

# Voices close enough to Malagasy to be worth using, best first. Every source
# checked says no device ships an installed mg voice (see PRONUNCIATION.md).
VOICE_PRIORITY = ["mg", "fr", "ro", "it", "es", "pt", "ca", "en"]


def _apply_map(syllable, table):
    # Malagasy "g" is always hard; French/Italian/Portuguese soften it before
    # e, i, y (gidro -> [ʒidʁo]). The silent "u" must sit inside the syllable,
    # or the hyphenation would split it away.
    if re.match(r"^g[eiy]", syllable):
        syllable = "gu" + syllable[1:]
    keys = sorted(table, key=len, reverse=True)
    out, index = [], 0
    while index < len(syllable):
        for key in keys:
            if syllable.startswith(key, index):
                out.append(table[key])
                index += len(key)
                break
        else:
            out.append(syllable[index])
            index += 1
    return "".join(out)


def _harden_s(word):
    """Malagasy s is always [s]; French and Italian read one s between vowels
    as [z] (misaotra -> [miz…]). Double it first."""
    return re.sub(r"([aeiouy])s(?=[aeiouy])", r"\1ss", word)


def adapt(text, lang):
    """Rewrite Malagasy for a voice of another language, syllable by syllable.

    Hyphenating the syllables is the point, not a decoration: it stops a
    French voice turning "an/on/in" into a nasal vowel and swallowing a final
    -e, which is what made "Antananarivo" unrecognisable.

    Returns the text unchanged for an "mg" voice or an unknown language.
    """
    if not text:
        return text or ""
    code = (lang or "").lower().replace("_", "-")[:2]
    if code == "mg":
        return text
    table = ADAPTERS.get(code)
    if not table:
        return text

    pieces = re.split(r"([^a-z]+)", text.lower())
    out = []
    for piece in pieces:
        if not piece or not re.search(r"[a-z]", piece):
            out.append(piece)
            continue
        for word in re.split(r"(['’])", piece):
            if not word or word in ("'", "\u2019"):
                out.append(word)
                continue
            syllables = syllabify(_harden_s(word))
            if not syllables:
                out.append(word)
                continue
            out.append("-".join(_apply_map(syllable, table)
                                for syllable in syllables))
    return "".join(out)


def speech_text(text, lang):
    """Backwards-compatible alias for adapt()."""
    return adapt(text, lang)


def voice_score(lang):
    """Higher is better. 100 means a real Malagasy voice."""
    code = (lang or "").lower().replace("_", "-")[:2]
    if code in ("mg", "ml"):
        return 100
    if code in VOICE_PRIORITY:
        return 70 - VOICE_PRIORITY.index(code) * 5
    return 10
