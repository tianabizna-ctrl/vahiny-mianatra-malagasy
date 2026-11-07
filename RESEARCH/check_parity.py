#!/usr/bin/env python3
"""Fail if RESEARCH/pronunciation.py and APP/js/speech.js disagree.

The same Malagasy→foreign-voice tables live in two languages: Python for the
build and the QA sheet, JavaScript for the browser. They drifted once already
(the browser had no adapter at all), so this script compares the two on a
representative word list and exits non-zero on any difference.

    python3 RESEARCH/check_parity.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "RESEARCH"))
import pronunciation as pr

WORDS = [
    "trano", "misaotra", "misaotra betsaka", "antananarivo", "ahoana", "veloma",
    "vahiny", "olona", "fahasalamana", "tsara", "mangatsiaka", "gidro", "hena",
    "vohitra", "trondro", "izaho", "soa", "rano", "sakafo", "vorona", "tonga",
    "mpianatra", "hazo", "asa", "misaotra tompoko", "ny olona", "jiro",
    "vaovao", "ahoana ianao",
]
LANGS = ["fr", "ro", "it", "es", "ca", "pt", "en", "mg"]

NODE_HARNESS = """
global.window = {};
require(%s);
var S = global.window.Salama;
var words = %s;
var langs = %s;
var out = {};
langs.forEach(function (lang) {
  out[lang] = words.map(function (w) { return S.speech.adapt(w, lang); });
});
process.stdout.write(JSON.stringify(out));
"""


def main():
    node = shutil.which("node")
    if not node:
        print("SKIP node is not installed; cannot compare the JS adapter.")
        return 0

    harness = NODE_HARNESS % (
        json.dumps(os.path.join(BASE, "APP", "js", "speech.js")),
        json.dumps(WORDS),
        json.dumps(LANGS),
    )
    handle, path = tempfile.mkstemp(suffix=".js")
    with os.fdopen(handle, "w", encoding="utf-8") as f:
        f.write(harness)
    try:
        result = subprocess.run([node, path], capture_output=True, text=True, timeout=60)
    finally:
        os.unlink(path)
    if result.returncode != 0:
        print("FAIL the JS adapter threw:\n" + (result.stderr or "").strip())
        return 1

    js = json.loads(result.stdout)
    failures = []
    for lang in LANGS:
        for index, word in enumerate(WORDS):
            want = pr.adapt(word, lang)
            got = js[lang][index]
            if want != got:
                failures.append((lang, word, want, got))

    for lang, word, want, got in failures:
        print("FAIL %-2s %-22s python=%-28s js=%s" % (lang, word, want, got))
    if failures:
        print("%d disagreement(s) between pronunciation.py and speech.js" % len(failures))
        return 1
    print("adapters agree on %d words x %d languages" % (len(WORDS), len(LANGS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
