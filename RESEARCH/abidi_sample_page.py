#!/usr/bin/env python3
"""Build ABIDI_SAMPLE.html: the same fourteen entries in both voices, side by side.

    python3 RESEARCH/abidi_sample_page.py

MMS clips come from APP/media/audio/, Abidi clips from APP/media/audio_abidi/.
Both are inlined as data URIs, so the page plays from a double-click with no server
and no folder beside it. Nothing in the app changes: this page is only for choosing.
"""
import base64
import json
import os
import wave

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "ABIDI_SAMPLE.html")
MANIFEST = os.path.join(BASE, "RESEARCH", "ABIDI_RENDERED.json")
LANG = {"words": "word", "phrases": "phrase", "lines": "sentence"}


def load_content():
    raw = open(os.path.join(BASE, "APP", "data", "content.js"), encoding="utf-8").read()
    return json.loads(raw[raw.index("{"):raw.rindex("}") + 1])


def english_for(data, kind, stem):
    if kind == "words":
        for word in data["vocabulary"]:
            if word["id"] == stem:
                return word.get("en", "")
    if kind == "phrases":
        for phrase in data["phrases"]:
            if phrase["id"] == stem:
                return phrase.get("en", "")
    dialogue_id, _, index = stem.rpartition("-")
    for dialogue in data["dialogues"]:
        if dialogue["id"] == dialogue_id:
            try:
                return dialogue["lines"][int(index)].get("en", "")
            except (ValueError, IndexError):
                return ""
    return ""


def mms_path(data, kind, stem):
    if kind == "words":
        return data.get("wordAudio", {}).get(stem, "")
    if kind == "phrases":
        return data.get("phraseAudio", {}).get(stem, "")
    return data.get("lineAudio", {}).get(stem, "")


def data_uri(path, mime):
    try:
        with open(path, "rb") as handle:
            return "data:%s;base64,%s" % (mime, base64.b64encode(handle.read()).decode())
    except OSError:
        return ""


def mp3_seconds(path):
    """Cheap estimate: bitrate is fixed at 32 kbps by the renderer."""
    try:
        return os.path.getsize(path) * 8 / 32000.0
    except OSError:
        return 0.0


# The A/B page is for a decision, not for listening to the course: a handful of
# entries is enough, and inlining thousands of clips made a 60 MB file out of it.
CURATED = ["dlg_greet_and_farewell-0", "dlg_greet_and_farewell-2",
           "dlg_directions_travel-1", "dlg_health_emergency-1",
           "rpb_tsara_fa_misaotra", "rpb_veloma", "rpb_misaotra_betsaka",
           "misaotra", "manakory", "tongasoa", "veloma", "mipetrapetraha",
           "ramatoabe", "fahasalamana", "tsara", "vary"]


def build_rows(data, manifest, limit=16):
    rows, seen = [], set()
    stems = {slug: _stem_for(data, meta.get("kind", ""), meta["text"])
             for slug, meta in manifest.items()}
    chosen = [slug for slug in manifest
              if stems.get(slug) in CURATED] or list(manifest)
    ordered = sorted(chosen, key=lambda slug: CURATED.index(stems[slug])
                     if stems.get(slug) in CURATED else 99)
    for slug in ordered[:limit]:
        meta = manifest[slug]
        text = meta["text"]
        if text in seen:                     # two rows with the same words teach nothing
            continue
        seen.add(text)
        kind = meta["kind"]
        stem = stems.get(slug) or _stem_for(data, kind, text)
        mms = mms_path(data, kind, stem)
        folder = os.path.join(BASE, "APP", "media", "audio_abidi",
                              LANG.get(kind, kind) + "s" if kind != "phrases" else kind)
        folder = os.path.join(BASE, "APP", "media", "audio_abidi", kind)
        abidi = os.path.join(folder, slug + ".mp3")
        if not os.path.exists(abidi):
            abidi = os.path.join(folder, slug + ".wav")
        rows.append({
            "text": text,
            "en": english_for(data, kind, stem),
            "kind": LANG.get(kind, kind),
            "stem": stem,
            "mms": data_uri(os.path.join(BASE, "APP", mms), "audio/mpeg") if mms else "",
            "abidi": data_uri(abidi, "audio/mpeg" if abidi.endswith(".mp3") else "audio/wav"),
            "abidi_s": meta.get("seconds", 0),
            "mms_s": mp3_seconds(os.path.join(BASE, "APP", mms)) if mms else 0,
        })
    return rows


def _stem_for(data, kind, text):
    """The manifest stores slugs; the content stores ids. Match them back."""
    import re

    def slug(value):
        return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

    pool = []
    if kind == "words":
        pool = [(word["id"], word["mg"]) for word in data["vocabulary"]]
    elif kind == "phrases":
        pool = [(phrase["id"], phrase["mg"]) for phrase in data["phrases"]]
    else:
        for dialogue in data["dialogues"]:
            for index, line in enumerate(dialogue["lines"]):
                pool.append(("%s-%d" % (dialogue["id"], index), line["mg"]))
    for stem, mg in pool:
        if slug(stem) == slug(text) or mg == text:
            return stem
    return ""


PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Two voices — MMS vs Abidi</title>
<style>
  :root { --ink:#241f1a; --paper:#faf6ef; --card:#fff; --line:#d8ccb8;
          --green:#14603a; --gold:#87550f; --muted:#5b5044; }
  * { box-sizing:border-box; }
  body { margin:0; padding:20px 16px 60px; background:var(--paper); color:var(--ink);
         font:18px/1.55 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  header { max-width:760px; margin:0 auto 18px; }
  h1 { font-size:24px; margin:0 0 6px; }
  p.sub { margin:0; color:var(--muted); font-size:16px; }
  .row { max-width:760px; margin:0 auto 12px; background:var(--card);
         border:2px solid var(--line); border-radius:12px; padding:12px 14px; }
  .mg { font-size:21px; font-weight:600; margin:0 0 2px; }
  .en { margin:0 0 10px; color:var(--muted); font-size:16px; }
  .pair { display:grid; gap:8px; grid-template-columns:1fr 1fr; }
  @media (max-width:560px) { .pair { grid-template-columns:1fr; } }
  .opt { border:2px solid var(--line); border-radius:10px; padding:8px 10px; }
  .opt.new { border-color:var(--green); background:#f2f9f4; }
  .tag { display:block; font-size:13px; letter-spacing:.04em; text-transform:uppercase;
         color:var(--muted); margin-bottom:4px; }
  .opt.new .tag { color:var(--green); font-weight:700; }
  audio { width:100%; height:40px; }
  .missing { font-size:14px; color:var(--gold); }
  .kind { font-size:13px; color:var(--muted); }
  footer { max-width:760px; margin:24px auto 0; font-size:15px; color:var(--muted); }
  code { background:#efe7d8; padding:1px 5px; border-radius:4px; font-size:14px; }
</style>
</head>
<body>
<header>
  <h1>Two voices, same words</h1>
  <p class="sub">Left: the machine voice the app ships today (Meta MMS, 16 kHz).
     Right: Abidi, the Malagasy TTS from artifisialy.mg (22 kHz). Same text, same
     course entries. Listen to both and tell me which one a Malagasy ear trusts.</p>
</header>
<main id="list"></main>
<footer>
  <p><b>What I need from you:</b> a one-line verdict — “Abidi is better”, “MMS is
     better”, or “Abidi is better but…” — plus any row where one of them says the
     wrong word.</p>
  <p>Abidi is a free beta, so the whole course is <i>not</i> rendered yet. Fourteen
     clips exist to make this decision; a full render is ~3,400 requests and needs
     their permission first (there is a ready-to-send note in
     <code>RESEARCH/PROOFREADING.md</code>).</p>
</footer>
<script>
var ROWS = __ROWS__;
function esc(v) {
  return String(v == null ? '' : v).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
document.getElementById('list').innerHTML = ROWS.map(function (row, index) {
  return '<article class="row">' +
    '<p class="mg" lang="mg">' + esc(row.text) + '</p>' +
    (row.en ? '<p class="en">' + esc(row.en) + '</p>' : '') +
    '<div class="pair">' +
      '<div class="opt"><span class="tag">MMS — shipping now</span>' +
        (row.mms ? '<audio controls preload="none" src="' + row.mms + '"></audio>'
                 : '<p class="missing">no MMS clip</p>') + '</div>' +
      '<div class="opt new"><span class="tag">Abidi — candidate</span>' +
        (row.abidi ? '<audio controls preload="none" src="' + row.abidi + '"></audio>'
                   : '<p class="missing">not rendered</p>') + '</div>' +
    '</div>' +
    '<p class="kind">' + esc(row.kind) + ' · ' + esc(row.stem) + '</p>' +
  '</article>';
}).join('');
</script>
</body>
</html>
"""


def main():
    data = load_content()
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    # The manifest is keyed by slug only; recover the kind from the file's folder.
    for slug, meta in manifest.items():
        if "kind" in meta:
            continue
        for kind in ("words", "phrases", "lines"):
            if os.path.exists(os.path.join(BASE, "APP", "media", "audio_abidi", kind,
                                           slug + ".mp3")):
                meta["kind"] = kind
    rows = build_rows(data, manifest)
    payload = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    html = PAGE.replace("__ROWS__", payload)
    with open(OUT, "w", encoding="utf-8") as handle:
        handle.write(html)
    print("Wrote %s (%.2f MB) with %d comparisons"
          % (OUT, os.path.getsize(OUT) / 1048576, len(rows)))
    for row in rows[:40]:
        print("  %-9s %-22s mms %s  abidi %s"
              % (row["kind"], row["stem"],
                 "yes" if row["mms"] else "no ",
                 "%.1fs" % row["abidi_s"] if row["abidi"] else "missing"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
