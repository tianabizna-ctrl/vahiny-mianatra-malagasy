#!/usr/bin/env python3
"""Validate APP/data/content.js before it ships.

Run after build_app_data.py. Exits non-zero when the pack would teach something
wrong or point at a missing audio file.

    python3 RESEARCH/validate_content.py
"""

import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "RESEARCH"))
import content_quality as cq

APP = os.path.join(BASE, "APP")
raw = open(os.path.join(APP, "data", "content.js"), encoding="utf-8").read()
data = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])

errors, warnings = [], []

# ---- vocabulary -----------------------------------------------------------
for w in data["vocabulary"]:
    if not w.get("mg") or not w.get("en"):
        errors.append(f"vocabulary {w.get('id')}: empty mg/en")
    for pattern in cq.GARBAGE_PATTERNS:
        if pattern.search(w.get("en", "")):
            errors.append(f"vocabulary {w['id']}: mangled gloss {w['en']!r}")
            break
    if w.get("en", "").lower() == w.get("mg", "").lower():
        warnings.append(f"vocabulary {w['id']}: gloss repeats the Malagasy")

# ---- phrases --------------------------------------------------------------
for p in data["phrases"]:
    if cq.looks_english(p.get("mg", "")):
        errors.append(f"phrase {p['id']}: English in the Malagasy column {p['mg']!r}")
    if cq.duplicated_pair(p.get("mg", ""), p.get("en", "")):
        errors.append(f"phrase {p['id']}: English column repeats the Malagasy")
    if p.get("group") not in {g["id"] for g in data["phraseGroups"]}:
        errors.append(f"phrase {p['id']}: unknown group {p['group']!r}")

# ---- dialogues ------------------------------------------------------------
dialogue_ids = {d["id"] for d in data["dialogues"]}
for d in data["dialogues"]:
    if len(d["lines"]) < 2:
        warnings.append(f"dialogue {d['id']}: fewer than two lines")
    for line in d["lines"]:
        if cq.looks_english(line.get("mg", "")):
            errors.append(f"dialogue {d['id']}: English line {line['mg']!r}")

# ---- sessions -------------------------------------------------------------
for s in data["sessions"]:
    if not s.get("dialogue") or s["dialogue"] not in dialogue_ids:
        errors.append(f"session {s['id']}: missing dialogue mapping")
    if not s.get("audio"):
        warnings.append(f"session {s['id']}: no audio")
    for rel in s.get("audio", []):
        if not os.path.exists(os.path.join(APP, rel)):
            errors.append(f"session {s['id']}: audio file missing {rel}")

# ---- curriculum coverage --------------------------------------------------
weeks = {w["week"]: w for w in data["curriculum"]}
if len(weeks) != 12:
    errors.append(f"curriculum: expected 12 weeks, found {len(weeks)}")
if len(data["sessions"]) != 36:
    errors.append(f"curriculum: expected 36 sessions, found {len(data['sessions'])}")

# ---- topics ---------------------------------------------------------------
theme_ids = {t["id"] for t in data["themeMap"]}
if "dictionary" in theme_ids:
    errors.append("themeMap: 'dictionary' is not a topic shelf")
orphans = [w["id"] for w in data["vocabulary"]
           if w.get("themes") and not (set(w["themes"]) & theme_ids)]
if orphans:
    warnings.append(f"{len(orphans)} words tagged only with unknown topics")

# ---- pronunciation --------------------------------------------------------
# These gates exist because a wrong written hint is worse than none: it is what
# the learner imitates out loud. The rules mirror RESEARCH/test_pronunciation.py.
import pronunciation as pr
from pronunciation import syllabify, stress_position

APPROX_SOURCES = {"phrase", "rule", "dictionary", "single"}
words = data["vocabulary"]
phrases = data["phrases"]

# 1. A generated hint for a single word must name exactly one stressed syllable.
#    A phrase names one per word, so only "at least one" is required there.
#    Teacher-written hints are free-form and are not held to either rule.
def _groups(text):
    return [g for g in re.split(r"[\s\-]+", text or "") if g]


bad_stress = []
unstressed_teacher = []
for item in words + phrases:
    guess = item.get("pron")
    if not guess:
        continue
    upper = [g for g in _groups(guess) if g.isupper()]
    source = item.get("pron_source")
    if source not in (APPROX_SOURCES | {"teacher"}):
        errors.append(f"{item['id']}: unknown pron_source {source!r}")
        continue
    if source == "teacher":
        if not upper:
            unstressed_teacher.append(item["id"])
        continue
    if " " in item["mg"]:
        if not upper:
            bad_stress.append((item["id"], guess, 0))
    else:
        # A compound word ("manam-bady") is respelled part by part, so it
        # carries one stress per part; a simple word carries exactly one.
        expected = max(1, len([p for p in item["mg"].split("-") if p]))
        if len(upper) != expected:
            bad_stress.append((item["id"], guess, len(upper)))

# 2. A generated hint for a single word must have one group per written
#    syllable, so hint and word cannot silently disagree about syllable count.
bad_syllables = []
for item in words:
    guess = item.get("pron")
    if not guess or item.get("pron_source") == "teacher" or item.get("isPhrase"):
        continue
    if " " in item["mg"]:
        continue
    parts = [p for p in item["mg"].split("-") if p]
    if len(parts) > 1:
        continue          # respelled part by part; checked by the stress gate
    if len(_groups(guess)) != len(syllabify(item["mg"])):
        bad_syllables.append((item["id"], item["mg"], guess))

# 3. A hint must be readable ASCII: accents belong to the audio adapter, not to
#    the English-facing respelling.
bad_ascii = [i["id"] for i in words + phrases
             if i.get("pron") and i.get("pron_source") != "teacher"
             and any(ord(ch) > 127 for ch in i["pron"])]

# 4. The adapter must be able to speak every entry in at least French.
bad_adapt = []
for item in (words + phrases)[:4000]:
    try:
        out = pr.adapt(item["mg"], "fr")
    except Exception as error:                        # pragma: no cover
        bad_adapt.append((item["id"], str(error)))
        continue
    if not out:
        bad_adapt.append((item["id"], "empty"))

# 5. Audio maps must point at files that exist, and at ids that exist.
if data.get("wordAudio"):
    ids = {w["id"] for w in words} | {p["id"] for p in phrases}
    for key, rel in data["wordAudio"].items():
        if not os.path.exists(os.path.join(APP, rel)):
            errors.append(f"wordAudio {key}: file missing {rel}")
        if key not in ids:
            warnings.append(f"wordAudio {key}: no entry with that id")
if data.get("phraseAudio"):
    ids = {p["id"] for p in phrases}
    for key, rel in data["phraseAudio"].items():
        if not os.path.exists(os.path.join(APP, rel)):
            errors.append(f"phraseAudio {key}: file missing {rel}")
        if key not in ids:
            warnings.append(f"phraseAudio {key}: no phrase with that id")
if data.get("lineAudio"):
    valid = set()
    for dialogue in data["dialogues"]:
        for index in range(len(dialogue["lines"])):
            valid.add(f"{dialogue['id']}-{index}")
    for key, rel in data["lineAudio"].items():
        if not os.path.exists(os.path.join(APP, rel)):
            errors.append(f"lineAudio {key}: file missing {rel}")
        if key not in valid:
            warnings.append(f"lineAudio {key}: no dialogue line with that id")

for item_id, guess, count in bad_stress[:8]:
    errors.append(f"{item_id}: {count} stressed syllables in {guess!r}")
for item_id, mg, guess in bad_syllables[:8]:
    errors.append(f"{item_id}: hint {guess!r} does not match {mg!r} syllable by syllable")
for item_id in bad_ascii[:8]:
    errors.append(f"{item_id}: pronunciation hint is not ASCII")
for item_id, reason in bad_adapt[:8]:
    errors.append(f"{item_id}: adapter failed ({reason})")
if unstressed_teacher:
    warnings.append(f"{len(unstressed_teacher)} teacher-written hints carry no stress mark "
                    f"(e.g. {', '.join(unstressed_teacher[:3])})")

approx = sum(1 for w in words if w.get("pron_approx"))
covered = sum(1 for item in words + phrases if item.get("pron"))
total = len(words) + len(phrases)
coverage = (covered / total) * 100 if total else 0
print(f"pronunciation coverage: {coverage:.0f}% ({approx} generated, labelled approximate)")
if data.get("wordAudio"):
    print(f"rendered clips: {len(data['wordAudio'])} words, "
          f"{len(data.get('phraseAudio') or {})} phrases, {len(data.get('lineAudio') or {})} lines")
# The floor is what the current pipeline guarantees; raise it, never lower it,
# when a generator improves. Entries without a hint are the ones respell()
# refuses on purpose (too long, >7 syllables, digits, punctuation).
COVERAGE_FLOOR = 98.0
if coverage < COVERAGE_FLOOR:
    errors.append(f"pronunciation coverage {coverage:.0f}% is below the "
                  f"{COVERAGE_FLOOR:.0f}% floor")

# 6. The hand table and the printed dictionary must not disagree silently.
conflicts = data["meta"].get("counts", {}).get("stress_conflicts", 0)
if conflicts:
    warnings.append(f"{conflicts} words where the hand stress table and the printed "
                    "dictionary disagree — see RESEARCH/pron_qa.html")


# 6b. Dialogue lines that are placeholders, not Malagasy to say aloud. They are left
#     without audio on purpose; they still need rewriting before the course is final.
PLACEHOLDERS = ("........", "(insert", "(or give a kabary)", "Or: Faly", "... (number)",
                "OFFICIAL:", "MIPETRAKA / MANTOTRY", "MIVAVAKA / HIVAVAKA")
placeholder_lines = []
for dialogue in data["dialogues"]:
    for index, line in enumerate(dialogue.get("lines", [])):
        if any(marker in line.get("mg", "") for marker in PLACEHOLDERS):
            placeholder_lines.append("%s[%d]" % (dialogue["id"], index))
if placeholder_lines:
    warnings.append(f"{len(placeholder_lines)} dialogue line(s) are placeholders copied "
                    f"from the source packs, not spoken Malagasy (e.g. "
                    f"{', '.join(placeholder_lines[:3])}) — they have no recording")

# 7. Native-speaker review: an approved entry must not still be labelled
#    approximate (the badge in the UI would contradict itself).
reviewed = disputed = 0
for item in data["vocabulary"] + data["phrases"]:
    if item.get("pron_verified"):
        reviewed += 1
        if item.get("pron_approx"):
            errors.append(f"{item.get('id')!r} is approved by the reviewer but "
                          "still flagged approximate")
    if item.get("pron_disputed"):
        disputed += 1
if reviewed or disputed:
    print(f"review: {reviewed} approved by a native speaker, {disputed} disputed")

print(f"vocabulary {len(data['vocabulary'])} | phrases {len(data['phrases'])} | "
      f"dialogues {len(data['dialogues'])} | sessions {len(data['sessions'])}")
for warning in warnings[:10]:
    print("WARN ", warning)
if len(warnings) > 10:
    print(f"WARN  ... {len(warnings) - 10} more")
for error in errors:
    print("FAIL ", error)
print("content OK" if not errors else f"{len(errors)} errors")
sys.exit(1 if errors else 0)
