#!/usr/bin/env python3
"""Render real Malagasy audio with the Meta MMS model.

    pip install transformers torch torchaudio soundfile
    python3 RESEARCH/render_audio.py --i-accept-noncommercial --what words --limit 20
    python3 RESEARCH/render_audio.py --i-accept-noncommercial --what all

Writes one clip per vocabulary entry to APP/media/audio/words/<id>.mp3 and one
per dialogue line to APP/media/audio/lines/<dialogue-id>-<index>.mp3. The build
(`build_app_data.py`) picks both up automatically, and the app plays a clip
before it considers any synthetic voice, so this single step is what makes the
pronunciation actually Malagasy instead of an accent of French.

LICENCE — READ THIS
    facebook/mms-tts-mlg is CC-BY-NC 4.0: non-commercial use only, attribution
    to Meta AI required. This script refuses to run without
    --i-accept-noncommercial so that decision is made on purpose. If the course
    is ever sold, the audio has to come from a native speaker instead —
    `--what words --list <file>` prints exactly what a recording session needs.

Everything is resumable: existing files are skipped, so an interrupted run
costs nothing.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import unicodedata

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "RESEARCH"))
from content_quality import audio_slug
MODEL = "facebook/mms-tts-mlg"
WORDS_DIR = os.path.join(BASE, "APP", "media", "audio", "words")
PHRASES_DIR = os.path.join(BASE, "APP", "media", "audio", "phrases")
LINES_DIR = os.path.join(BASE, "APP", "media", "audio", "lines")
DIRS = {"words": WORDS_DIR, "phrases": PHRASES_DIR, "lines": LINES_DIR}
# slug -> sha1 of the text that produced the clip. Lets --force-changed re-render
# exactly the entries whose text a proofreading pass changed, and nothing else.
MANIFEST = os.path.join(BASE, "APP", "media", "audio", "manifest.json")


def text_hash(text):
    return hashlib.sha1(plain(text).encode("utf-8")).hexdigest()


def manifest_key(kind, slug):
    # The same slug can exist in two folders ("azafady" is both a word and a
    # phrase), so the folder is part of the key.
    return "%s/%s" % (kind, slug)


def read_manifest():
    try:
        return json.load(open(MANIFEST, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def plain(text):
    """The MMS text front end does not need stress accents; strip them so the
    model reads the same characters it was trained on ('ianaréo' -> 'ianareo')."""
    decomposed = unicodedata.normalize("NFD", text or "")
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def write_mp3(path, samples, sample_rate, bitrate, encoder):
    """samples: float32 numpy array in [-1, 1]."""
    pcm = (samples * 32767.0).astype("int16").tobytes()
    if encoder == "lameenc":
        import lameenc
        enc = lameenc.Encoder()
        enc.set_bit_rate(bitrate)
        enc.set_in_sample_rate(sample_rate)
        enc.set_channels(1)
        enc.set_quality(5)
        data = enc.encode(pcm) + enc.flush()
        with open(path, "wb") as handle:
            handle.write(data)
        return
    # ffmpeg fallback: write a temporary wav and convert
    import soundfile
    temporary = path + ".wav"
    soundfile.write(temporary, samples, sample_rate)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", temporary,
                    "-codec:a", "libmp3lame", "-b:a", "%dk" % bitrate, path], check=True)
    os.unlink(temporary)


def load_content():
    path = os.path.join(BASE, "APP", "data", "content.js")
    raw = open(path, encoding="utf-8").read()
    return json.loads(raw[raw.index("{"):raw.rindex("}") + 1])


def taught_vocabulary(data):
    """Ids of the vocabulary actually reachable from the 36 sessions."""
    themes = set()
    for session in data["sessions"]:
        themes.update(session.get("themes") or [])
    return {w["id"] for w in data["vocabulary"]
            if set(w.get("themes") or []) & themes}


def collect(data, what, include_phrases, taught_only=False):
    """(relative path stem, text) pairs, in a stable order."""
    jobs = []
    keep = taught_vocabulary(data) if taught_only else None
    if what in ("words", "all"):
        for word in data["vocabulary"]:
            if word.get("isPhrase") and what == "words" and not include_phrases:
                continue
            if keep is not None and word["id"] not in keep:
                continue
            if word.get("mg"):
                jobs.append(("words", word["id"], word["mg"]))
    if what in ("phrases", "all"):
        keep = taught_vocabulary(data) if taught_only else None
        for phrase in data["phrases"]:
            if phrase.get("mg") and phrase.get("id"):
                jobs.append(("phrases", phrase["id"], phrase["mg"]))
    if what in ("lines", "all"):
        for dialogue in data["dialogues"]:
            for index, line in enumerate(dialogue.get("lines", [])):
                if line.get("mg"):
                    jobs.append(("lines", "%s-%d" % (dialogue["id"], index), line["mg"]))
    return jobs


def write_list(jobs, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("kind\tid\ttext\n")
        for kind, stem, text in jobs:
            f.write("%s\t%s\t%s\n" % (kind, stem, text))
    print("Wrote %s — %d lines for a recording session." % (path, len(jobs)))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--what", choices=["words", "phrases", "lines", "all"], default="words")
    parser.add_argument("--limit", type=int, default=0, help="stop after N clips")
    parser.add_argument("--dry-run", action="store_true", help="list the work, write nothing")
    parser.add_argument("--list", dest="list_path", default="",
                        help="write a TSV of what to record instead of synthesising")
    parser.add_argument("--include-phrases", action="store_true",
                        help="also render vocabulary entries that contain a space")
    parser.add_argument("--mp3", action="store_true",
                        help="write mp3 instead of wav (lameenc, or ffmpeg as a fallback)")
    parser.add_argument("--bitrate", type=int, default=32, help="mp3 bitrate in kbps (32 is plenty for speech)")
    parser.add_argument("--force-changed", action="store_true",
                        help="re-render clips whose source text changed since last time")
    parser.add_argument("--taught-only", action="store_true",
                        help="only the words and phrases the 36 sessions actually use")
    parser.add_argument("--i-accept-noncommercial", action="store_true",
                        help="acknowledge the CC-BY-NC 4.0 licence of the model")
    parser.add_argument("--model", default=MODEL)
    args = parser.parse_args()

    data = load_content()
    jobs = collect(data, args.what, args.include_phrases, args.taught_only)
    manifest = read_manifest()

    # Two entries can slugify to the same file name; the build refuses to wire
    # those (they fall back to the synthesiser), so there is exactly one clip to
    # keep and no way to know which text it should match. Leave them alone.
    seen = {}
    for kind, stem, text in jobs:
        seen.setdefault(manifest_key(kind, audio_slug(stem)), set()).add(plain(text))
    ambiguous = {key for key, texts in seen.items() if len(texts) > 1}
    if ambiguous:
        print("  %d clip name(s) shared by two entries: kept as-is (unwired in the app)"
              % len(ambiguous))

    def needs_work(kind, stem, text):
        path = os.path.join(DIRS[kind], audio_slug(stem) + (".mp3" if args.mp3 else ".wav"))
        if not os.path.exists(path):
            return True
        if args.force_changed and manifest_key(kind, audio_slug(stem)) not in ambiguous:
            return manifest.get(manifest_key(kind, audio_slug(stem))) != text_hash(text)
        return False

    pending = [(kind, stem, text) for kind, stem, text in jobs if needs_work(kind, stem, text)]

    print("%d clips to render (%d already present)." % (len(pending), len(jobs) - len(pending)))
    if args.list_path:
        write_list(jobs, args.list_path)
        return 0
    if args.dry_run:
        for kind, stem, text in pending[:20]:
            print("  %-6s %-28s %s" % (kind, stem, text))
        if len(pending) > 20:
            print("  ... and %d more" % (len(pending) - 20))
        return 0

    if not args.i_accept_noncommercial:
        print("Refusing to render: %s is CC-BY-NC 4.0 (non-commercial only).\n"
              "Re-run with --i-accept-noncommercial if that fits this project, or\n"
              "use --list to produce a script for a native-speaker recording." % args.model,
              file=sys.stderr)
        return 2

    try:
        import torch
        from transformers import AutoTokenizer, VitsModel
    except ImportError as error:
        print("Missing dependency: %s\n  pip install transformers torch soundfile" % error,
              file=sys.stderr)
        return 2

    encoder = None
    if args.mp3:
        try:
            import lameenc  # no external binary needed
            encoder = "lameenc"
        except ImportError:
            if shutil.which("ffmpeg"):
                encoder = "ffmpeg"
            else:
                print("No mp3 encoder: pip install lameenc (or install ffmpeg).",
                      file=sys.stderr)
                return 2
    else:
        try:
            import soundfile
        except ImportError:
            print("Missing soundfile. pip install soundfile", file=sys.stderr)
            return 2

    print("Loading %s ..." % args.model)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = VitsModel.from_pretrained(args.model)
    model.eval()
    torch.manual_seed(0)  # the duration predictor is stochastic
    sample_rate = model.config.sampling_rate

    for folder in DIRS.values():
        os.makedirs(folder, exist_ok=True)
    done = 0
    for kind, stem, text in pending:
        target_dir = DIRS[kind]
        target = os.path.join(target_dir, audio_slug(stem) + (".mp3" if args.mp3 else ".wav"))
        try:
            inputs = tokenizer(plain(text), return_tensors="pt")
            with torch.no_grad():
                waveform = model(**inputs).waveform
            samples = waveform.squeeze().numpy()
            if args.mp3:
                write_mp3(target, samples, sample_rate, args.bitrate, encoder)
            else:
                import soundfile
                soundfile.write(target, samples, sample_rate)
        except Exception as error:                      # keep going on one bad row
            print("  FAILED %s (%s): %s" % (stem, text, error), file=sys.stderr)
            continue
        manifest[manifest_key(kind, audio_slug(stem))] = text_hash(text)
        done += 1
        if done % 25 == 0:
            print("  %d/%d" % (done, len(pending)))
        if args.limit and done >= args.limit:
            print("  stopped at --limit %d" % args.limit)
            break

    try:
        os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
        with open(MANIFEST, "w", encoding="utf-8") as handle:
            json.dump(dict(sorted(manifest.items())), handle, indent=0)
    except OSError as error:
        print("Could not write the audio manifest: %s" % error, file=sys.stderr)
    print("Rendered %d clip(s)." % done)
    print("Next: python3 RESEARCH/build_app_data.py   (picks the clips up as wordAudio/lineAudio)")
    print("Note: include the CC-BY-NC attribution in the app's About panel, e.g."
          ' "Word audio is synthesised with Meta\'s MMS Malagasy voice (CC BY-NC 4.0)."')
    return 0


if __name__ == "__main__":
    sys.exit(main())
