#!/usr/bin/env python3
"""Build a self-contained page of rendered Malagasy clips, for listening checks.

    python3 RESEARCH/audio_sample.py

Writes AUDIO_SAMPLE.html with the mp3s embedded as data URIs, so it plays in any
sandbox (including a preview pane with no network and no file access) and can be
sent to a Malagasy speaker as one file.
"""
import base64
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "RESEARCH"))
from content_quality import audio_slug
WORDS = os.path.join(BASE, "APP", "media", "audio", "words")
PHRASES = os.path.join(BASE, "APP", "media", "audio", "phrases")
LINES = os.path.join(BASE, "APP", "media", "audio", "lines")
OUT = os.path.join(BASE, "AUDIO_SAMPLE.html")

# Ids chosen to exercise every rule the adapter cares about: penultimate stress,
# -tra antepenultimate, prenasalised clusters, ng as an onset, j = dz, ts,
# o = oo, ao = [o], a compound, and a whole sentence.
WANTED = [
    ("salama", "hello"),
    ("misaotra", "thank you"),
    ("trano", "house"),
    ("veloma", "goodbye"),
    ("ahoana", "how? (part of manao ahoana)"),
    ("tsara", "good"),
    ("mangatsiaka", "cold (ng as an onset)"),
    ("gidro", "lemur (j/g before i)"),
    ("vohitra", "hill (-tra, antepenultimate)"),
    ("trondro", "fish (prenasalised tr)"),
    ("manam-bady", "married (compound)"),
    ("vaovao", "news (hiatus ao)"),
    ("fahasalamana", "health"),
    ("manao_ahoana", "how are you"),
    ("salama_tompoko", "hello, sir/madam"),
    ("misaotra_betsaka", "thank you very much"),
]


def load_content():
    path = os.path.join(BASE, "APP", "data", "content.js")
    raw = open(path, encoding="utf-8").read()
    return json.loads(raw[raw.index("{"):raw.rindex("}") + 1])


def b64(path):
    with open(path, "rb") as handle:
        return base64.b64encode(handle.read()).decode("ascii")


def main():
    data = load_content()
    by_id = {w["id"]: w for w in data["vocabulary"]}
    by_id.update({p["id"]: p for p in data["phrases"]})

    cards = []
    for word_id, note in WANTED:
        slug = audio_slug(word_id)
        path = os.path.join(WORDS, slug + ".mp3")
        if not os.path.exists(path):
            path = os.path.join(PHRASES, slug + ".mp3")
        if not os.path.exists(path):
            continue
        entry = by_id.get(word_id, {})
        cards.append({
            "mp3": b64(path),
            "mg": entry.get("mg", word_id),
            "en": entry.get("en", note),
            "pron": entry.get("pron", ""),
            "note": note,
        })

    # Two whole dialogue lines, to hear connected speech rather than one word.
    line_cards = []
    for dialogue in data["dialogues"]:
        for index, line in enumerate(dialogue["lines"]):
            path = os.path.join(LINES, "%s-%d.mp3" % (dialogue["id"], index))
            if not os.path.exists(path):
                continue
            line_cards.append({
                "mp3": b64(path),
                "mg": line["mg"],
                "en": line["en"],
                "pron": line.get("pron", ""),
                "note": "from “" + dialogue["title"] + "”",
            })
            break
        if len(line_cards) >= 2:
            break

    def section(title, intro, items):
        if not items:
            return ""
        rows = "".join(
            '<article class="card">'
            '<div><p class="mg" lang="mg">%s</p>'
            '<p class="say">%s</p>'
            '<p class="en">%s <span class="note">— %s</span></p></div>'
            '<audio controls preload="none" src="data:audio/mpeg;base64,%s"></audio>'
            '</article>' % (
                item["mg"].replace("&", "&amp;").replace("<", "&lt;"),
                item["pron"].replace("&", "&amp;"),
                item["en"].replace("&", "&amp;").replace("<", "&lt;"),
                item["note"].replace("&", "&amp;"),
                item["mp3"])
            for item in items)
        return ('<h2>%s</h2><p class="intro">%s</p><div class="list">%s</div>'
                % (title, intro, rows))

    total = len(cards) + len(line_cards)
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Salama! — rendered Malagasy audio</title>
<style>
  :root { --ink:#241f1a; --paper:#faf6ef; --line:#d8ccb8; --green:#14603a; --gold:#87550f; }
  * { box-sizing: border-box; }
  body { margin:0 auto; max-width:820px; padding:32px 20px 64px; background:var(--paper);
         color:var(--ink); font:19px/1.55 -apple-system,"Segoe UI",Roboto,sans-serif; }
  h1 { font-size:30px; margin:0 0 6px; }
  h2 { font-size:22px; margin:34px 0 6px; color:var(--green); }
  .sub, .intro { color:#5b5044; font-size:16px; margin:0 0 18px; }
  .list { display:grid; gap:12px; }
  .card { display:grid; grid-template-columns:1fr auto; gap:14px; align-items:center;
          background:#fff; border:1px solid var(--line); border-radius:12px; padding:14px 16px; }
  .mg { font-size:24px; font-weight:600; margin:0; }
  .say { margin:2px 0; color:var(--gold); font-variant:small-caps; letter-spacing:.02em; }
  .en { margin:2px 0; color:#5b5044; font-size:16px; }
  .note { opacity:.75; }
  audio { width:200px; }
  footer { margin-top:36px; color:#5b5044; font-size:15px; border-top:1px solid var(--line); padding-top:16px; }
  @media (max-width:600px) { .card { grid-template-columns:1fr; } audio { width:100%; } }
</style>
</head>
<body>
<h1>Salama! — rendered Malagasy audio</h1>
<p class="sub">__COUNT__ clips spoken by Meta's MMS Malagasy voice model (facebook/mms-tts-mlg,
CC BY-NC 4.0), not by a fallback voice with a foreign accent. These are the clips the app
now plays before it reaches for any device voice. Judge the stress and the vowels, not the
recording quality: the model is 16 kHz mono and 32 kbps.</p>
__SECTIONS__
<footer>Any word that sounds wrong is a candidate for the recorded list, not for a code fix:
<code>python3 RESEARCH/render_audio.py --list recording_script.tsv</code>.
Full review sheet: <code>RESEARCH/pron_qa.html</code>.</footer>
</body>
</html>
"""
    sections = section("Single words",
                       "Chosen to exercise each rule the pronunciation code encodes.",
                       cards) + section(
        "Whole lines", "Connected speech, as it plays in a session or a dialogue.", line_cards)
    html = html.replace("__COUNT__", str(total)).replace("__SECTIONS__", sections)
    with open(OUT, "w", encoding="utf-8") as handle:
        handle.write(html)
    print("Wrote %s (%d KB, %d clips)" % (OUT, os.path.getsize(OUT) // 1024, total))
    if total < len(WANTED):
        print("  note: %d of the requested ids had no clip yet"
              % (len(WANTED) + 2 - total), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
