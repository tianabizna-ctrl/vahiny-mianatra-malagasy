#!/usr/bin/env python3
"""Turn a proofreading export into corrections the build applies.

    python3 RESEARCH/apply_corrections.py salama_corrections.tsv

Reads the TSV written by PROOFREAD.html ("Export corrections") and merges it into
RESEARCH/CORRECTIONS.json. Then:

    python3 RESEARCH/build_app_data.py      # corrections are applied, verified entries marked
    python3 RESEARCH/validate_content.py
    python3 RESEARCH/render_audio.py --i-accept-noncommercial --what all --mp3 --force-changed

What the export can say, per row:

    verdict = ok        the entry is right; it is marked "checked by a native speaker"
                        and loses the "(approx.)" label in the app
    verdict = wrong     the recording (or the text) does not sound right; kept and
                        reported as outstanding work. With no rewrite it means
                        "this clip must be replaced", not "this text must change".
    verdict = (empty)   no opinion
    corrected_mg/en     replaces the text; the audio for that entry is re-rendered

Re-running is safe: the file is merged by key, so a second export only updates
what changed. `--report` prints what is currently outstanding without writing.
"""
import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(BASE, "RESEARCH", "CORRECTIONS.json")
COLUMNS = ["key", "section", "original_mg", "original_en", "verdict",
           "corrected_mg", "corrected_en", "note"]


def load_content():
    path = os.path.join(BASE, "APP", "data", "content.js")
    raw = open(path, encoding="utf-8-sig").read()
    return json.loads(raw[raw.index("{"):raw.rindex("}") + 1])


def known_keys(data):
    keys = set()
    for dialogue in data["dialogues"]:
        for index in range(len(dialogue["lines"])):
            keys.add("dlg:%s:%d" % (dialogue["id"], index))
    for phrase in data["phrases"]:
        keys.add("phrase:%s" % phrase["id"])
    for word in data["vocabulary"]:
        keys.add("word:%s" % word["id"])
    for topic in data["grammar"]:
        for rule_index, rule in enumerate(topic.get("rules", [])):
            for example_index, _ in enumerate(rule.get("examples", [])):
                keys.add("gram:%s:%d:%d" % (topic["id"], rule_index, example_index))
    for index in range(len(data["culture"])):
        keys.add("culture:%d" % index)
    return keys


def read_tsv(path):
    # utf-8-sig: the sheet writes a BOM so Excel keeps Malagasy diacritics, and a
    # re-saved file may carry one too.
    with open(path, encoding="utf-8-sig") as handle:
        lines = [line.rstrip("\n").rstrip("\r") for line in handle if line.strip()]
    if not lines:
        raise SystemExit("The file is empty.")
    header = lines[0].split("\t")
    if header[:1] != ["key"]:
        raise SystemExit("That does not look like a PROOFREAD.html export "
                         "(first column should be 'key').")
    index = {name: position for position, name in enumerate(header)}
    rows = []
    for line in lines[1:]:
        cells = line.split("\t")
        cells += [""] * (len(header) - len(cells))
        rows.append({name: cells[position] for name, position in index.items()})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tsv", nargs="?", help="exported TSV from PROOFREAD.html")
    parser.add_argument("--report", action="store_true", help="print current state, write nothing")
    parser.add_argument("--reset", action="store_true", help="delete CORRECTIONS.json first")
    args = parser.parse_args()

    if args.reset and os.path.exists(TARGET):
        os.unlink(TARGET)
        print("Removed %s" % TARGET)

    data = load_content()
    valid = known_keys(data)
    existing = {}
    if os.path.exists(TARGET):
        existing = json.load(open(TARGET, encoding="utf-8")).get("entries", {})

    if args.report or not args.tsv:
        counts = {"ok": 0, "wrong": 0, "unsure": 0, "corrected": 0, "clips": 0}
        for key, entry in existing.items():
            verdict = entry.get("verdict") or ""
            if verdict in counts:
                counts[verdict] += 1
            if entry.get("mg") or entry.get("en"):
                counts["corrected"] += 1
            elif verdict == "wrong":
                counts["clips"] += 1      # wrong sound, text untouched
        print("CORRECTIONS.json: %d entries" % len(existing))
        print("  checked by a native speaker (ok): %d" % counts["ok"])
        print("  marked wrong (outstanding):       %d" % counts["wrong"])
        print("  unsure:                           %d" % counts["unsure"])
        print("  with rewritten text:              %d" % counts["corrected"])
        print("  clips to replace (wrong, no rewrite): %d" % counts["clips"])
        if not args.tsv:
            print("\nPass the exported TSV to apply new corrections.")
        return 0

    rows = read_tsv(args.tsv)
    added = updated = skipped = 0
    corrections = []
    for row in rows:
        key = row.get("key", "").strip()
        if not key:
            continue
        if key not in valid:
            skipped += 1
            print("  skip %-34s no such entry in this build" % key, file=sys.stderr)
            continue
        entry = existing.get(key, {})
        before = json.dumps(entry, sort_keys=True)
        verdict = (row.get("verdict") or "").strip()
        if verdict:
            entry["verdict"] = verdict
        # A field that repeats the *other* language's original is almost always a
        # shifted column, not a correction: the stakes are high (an English
        # sentence replacing the Malagasy), so it is refused and reported.
        def slipped(field, value):
            other = "original_en" if field == "mg" else "original_mg"
            return bool(value) and value == (row.get(other) or "").strip() != ""

        for field, column in (("mg", "corrected_mg"), ("en", "corrected_en")):
            value = (row.get(column) or "").strip()
            original = (row.get("original_" + field) or "").strip()
            # Only store a real change: the UI prefills nothing, but a re-export
            # of an unchanged row must not look like an edit.
            if value and slipped(field, value):
                print("  refuse %-30s %s column repeats the other language (%r)"
                      % (key, field, value), file=sys.stderr)
                continue
            if value and value != original:
                entry[field] = value
                corrections.append((key, field, original, value))
                if (row.get("original_" + field) or "") and entry.get("orig_" + field) is None:
                    entry["orig_" + field] = original
            elif "orig_" + field in entry and not value:
                entry.pop(field, None)
        note = (row.get("note") or "").strip()
        if note:
            entry["note"] = note
        entry["section"] = row.get("section", entry.get("section", ""))
        after = json.dumps(entry, sort_keys=True)
        if before == after:
            continue
        if key in existing:
            updated += 1
        else:
            added += 1
        existing[key] = entry

    payload = {
        "source": os.path.basename(args.tsv),
        "note": "Produced by RESEARCH/apply_corrections.py from a PROOFREAD.html export. "
                "Applied by RESEARCH/build_app_data.py. 'verdict: ok' means a native "
                "speaker approved the entry; its '(approx.)' label is removed.",
        "entries": dict(sorted(existing.items())),
    }
    with open(TARGET, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=1)
        handle.write("\n")

    print("Merged %d row(s): %d new, %d updated, %d skipped" % (len(rows), added, updated, skipped))
    print("Wrote %s (%d entries)" % (TARGET, len(existing)))
    if corrections:
        print("\nText changes — the audio for these will be re-rendered:")
        for key, field, before, after in corrections[:40]:
            print("  %-32s %s: %r -> %r" % (key, field, before, after))
        if len(corrections) > 40:
            print("  ... and %d more" % (len(corrections) - 40))
    print("\nNext: python3 RESEARCH/build_app_data.py && python3 RESEARCH/validate_content.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
