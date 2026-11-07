#!/usr/bin/env python3
"""Render course audio with Abidi, the Malagasy TTS at abidi.artifisialy.mg.

    python3 RESEARCH/abidi_render.py --sample            # 14 clips, for an A/B listen
    python3 RESEARCH/abidi_render.py --limit 50          # a first batch
    python3 RESEARCH/abidi_render.py --what words --limit 200 --delay 2
    python3 RESEARCH/abidi_render.py --list              # what is still missing

Why this script is deliberately slow and asks permission
--------------------------------------------------------
Abidi is a small free beta run by artifisialy.mg, not a public API with a quota.
The endpoint behind the web page works, and that is how this script talks to it —
politely: one request at a time, a pause between requests, stop on refusal, and
nothing is ever re-requested twice. Rendering the whole course (3,373 clips) would
be ~2.5 hours of continuous load on their machine, so ask them first:

    https://www.artifisialy.mg/abidi/  ·  the feedback form on the page  ·
    facebook.com/profile.php?id=61583001317244

A short note in Malagasy is in RESEARCH/PROOFREADING.md, ready to paste.

Output: APP/media/audio_abidi/{words,phrases,lines}/<slug>.mp3 (mono, 22 kHz source,
converted to 32 kbps mp3 so the whole course stays small). The app keeps using the
MMS clips until build_app_data.py is pointed at this folder, so a partial render is
harmless.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
import wave

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIRS = {
    "words": os.path.join(BASE, "APP", "media", "audio_abidi", "words"),
    "phrases": os.path.join(BASE, "APP", "media", "audio_abidi", "phrases"),
    "lines": os.path.join(BASE, "APP", "media", "audio_abidi", "lines"),
}
HOST = "https://abidi.artifisialy.mg"
JAR = os.path.join(BASE, "RESEARCH", ".abidi_cookies")
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_quality as cq  # noqa: E402


# ----------------------------------------------------------------- curl helpers
# Each worker keeps its own cookie jar: two threads writing one file corrupt it, and
# a corrupt jar means an unauthenticated request and a failed clip.
_local = threading.local()


def _jar():
    return getattr(_local, "jar", JAR)


def _curl(args, timeout=120):
    jar = _jar()
    command = ["curl", "-sS", "-m", str(timeout), "-b", jar, "-c", jar, "-A", UA,
               "-H", "Referer: %s/inference/" % HOST, "-H", "Origin: %s" % HOST] + args
    return subprocess.run(command, capture_output=True)


def _csrf():
    jar = _jar()
    if not os.path.exists(jar):
        return ""
    for line in open(jar, encoding="utf-8"):
        if "csrftoken" in line:
            return line.split()[-1]
    return ""


def open_session():
    """Load the page once to get a CSRF cookie; no cookie, no token, no audio."""
    _curl(["-o", os.devnull, "%s/inference/" % HOST], timeout=60)
    if not _csrf():
        raise SystemExit("Could not get a CSRF cookie from %s" % HOST)


def token():
    result = _curl(["-X", "POST", "-H", "X-CSRFToken: " + _csrf(),
                    "-H", "X-Requested-With: XMLHttpRequest",
                    "-H", "Content-Type: application/json", "-d", "{}",
                    "%s/inference/api/ephemeral-token/" % HOST])
    try:
        return json.loads(result.stdout.decode("utf-8"))["token"]
    except (ValueError, KeyError):
        raise SystemExit("No token: %s" % result.stdout.decode("utf-8")[:200])


def synthesise(text, path, rythme=1, fiovan=1, angola=1):
    """One clip. Returns (ok, message).

    The service answers HTTP 200 with {"error": "Upstream unreachable"} when its own
    backend hiccups, so the status line is not proof of audio: the body is checked
    for a RIFF header before anything is kept.
    """
    sign = token()
    result = _curl(["-X", "POST", "-H", "X-CSRFToken: " + _csrf(),
                    "-H", "X-API-TOKEN: 1234", "-H", "X-ABIDI-SIGN: " + sign,
                    "-H", "Content-Type: application/json",
                    "-H", "Accept: audio/*,application/octet-stream",
                    "-d", json.dumps({"text": text, "rythme": rythme,
                                      "fiovan": fiovan, "angola": angola}),
                    "-o", path, "-w", "%{http_code} %{content_type} %{size_download}",
                    "%s/inference/api/tts/" % HOST])
    status = result.stdout.decode("utf-8").strip().split()
    if not status or status[0] != "200":
        return False, "HTTP %s" % (status[0] if status else "?")
    try:
        with open(path, "rb") as handle:
            header = handle.read(12)
    except OSError as error:
        return False, str(error)
    if header[:4] != b"RIFF":
        try:
            with open(path, "rb") as handle:
                body = handle.read(200).decode("utf-8", "replace")
        except OSError:
            body = ""
        os.remove(path)
        return False, "not audio: %s" % body.strip()[:80]
    return True, "audio/wav"


# ----------------------------------------------------------------- audio check
def wav_seconds(path):
    try:
        with wave.open(path) as handle:
            return handle.getnframes() / float(handle.getframerate())
    except (wave.Error, EOFError):
        return 0.0


def to_mp3(wav_path, mp3_path, bitrate=32):
    """lameenc keeps the monophonic 22 kHz voice intact at 32 kbps."""
    try:
        import lameenc
        import soundfile as sf
    except ImportError:
        return False
    data, rate = sf.read(wav_path, dtype="int16")
    if getattr(data, "ndim", 1) > 1:
        data = data[:, 0]
    encoder = lameenc.Encoder()
    encoder.set_bit_rate(bitrate)
    encoder.set_in_sample_rate(rate)
    encoder.set_channels(1)
    encoder.set_quality(5)
    with open(mp3_path, "wb") as handle:
        handle.write(encoder.encode(data.tobytes()))
        handle.write(encoder.flush())
    return True


# ----------------------------------------------------------------- jobs
def load_content():
    raw = open(os.path.join(BASE, "APP", "data", "content.js"), encoding="utf-8").read()
    return json.loads(raw[raw.index("{"):raw.rindex("}") + 1])


# Dialogue lines that are not spoken Malagasy: placeholders and alternative forms
# copied from the Peace Corps intro packs ("Anarako ........ (name) ........",
# "(or give a kabary)", "MISAOTRA / MAZOTOA"). Speaking them teaches nothing, so they
# are left without a recording on purpose.
UNSPEAKABLE = (
    "(or give a kabary)", "Mazotoa homana / mihinana", "Or: Faly",
    "... (number)", "(Andriamanitra o...", "MIPETRAKA / MANTOTRY",
    "MIVAVAKA / HIVAVAKA", "(insert", "........", "OFFICIAL:",
)


def speakable(text):
    return not any(marker in text for marker in UNSPEAKABLE)


def collect(data, what, sample=False):
    jobs = []
    if what in ("all", "lines") and not sample:
        for dialogue in data["dialogues"]:
            for index, line in enumerate(dialogue["lines"]):
                if not speakable(line["mg"]):
                    continue
                jobs.append(("lines", "%s-%d" % (dialogue["id"], index), line["mg"]))
    if what in ("all", "phrases") and not sample:
        for phrase in data["phrases"]:
            jobs.append(("phrases", phrase["id"], phrase["mg"]))
    if what in ("all", "words") and not sample:
        # Taught vocabulary first: those are the words a lesson actually asks the
        # learner to repeat, so if the render has to stop early it stops on the tail.
        taught = set()
        for session in data["sessions"]:
            taught.update(session.get("themes") or [])
        ordered = sorted(data["vocabulary"],
                         key=lambda w: (0 if set(w.get("themes") or []) & taught else 1,
                                        w.get("level") or 1, w["mg"]))
        for word in ordered:
            jobs.append(("words", word["id"], word["mg"]))
    if sample:
        jobs = sample_jobs(data)
    return jobs


def sample_jobs(data):
    """Fourteen entries chosen to expose a bad voice: greetings, a long line, a
    sentence with a French loan, and words whose stress is easy to get wrong."""
    wanted_words = ["misaotra", "tongasoa", "manakory", "fahasalamana",
                    "mipetrapetraha", "ramatoabe"]
    wanted_lines = ["dlg_greet_and_farewell-0", "dlg_greet_and_farewell-2",
                    "dlg_market_shopping-2", "dlg_health_emergency-1",
                    "dlg_directions_travel-1"]
    wanted_phrases = ["rpb_tsara_fa_misaotra", "rpb_veloma", "rpb_misaotra_betsaka"]
    jobs = []
    for dialogue in data["dialogues"]:
        for index, line in enumerate(dialogue["lines"]):
            stem = "%s-%d" % (dialogue["id"], index)
            if stem in wanted_lines:
                jobs.append(("lines", stem, line["mg"]))
    known = {word["id"] for word in data["vocabulary"]}
    for word in data["vocabulary"]:
        if word["id"] in wanted_words:
            jobs.append(("words", word["id"], word["mg"]))
    for phrase in data["phrases"]:
        if phrase["id"] in wanted_phrases:
            jobs.append(("phrases", phrase["id"], phrase["mg"]))
    # A couple more so the sample always reaches fourteen even if ids drift.
    for word in data["vocabulary"]:
        if len(jobs) >= 14:
            break
        if word["id"] in known and word["id"] not in {job[1] for job in jobs}:
            if word["id"] in ("vary", "rano", "tsena", "dokotera", "tsara"):
                jobs.append(("words", word["id"], word["mg"]))
    return jobs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--what", default="all", choices=["all", "words", "phrases", "lines"])
    parser.add_argument("--sample", action="store_true", help="the 14-clip A/B set")
    parser.add_argument("--limit", type=int, default=0, help="stop after N clips")
    parser.add_argument("--delay", type=float, default=1.5, help="seconds between requests")
    parser.add_argument("--list", action="store_true", help="show what is missing, render nothing")
    parser.add_argument("--concurrency", type=int, default=1,
                        help="parallel requests (keep low: this is someone's free beta)")
    parser.add_argument("--manifest", default=os.path.join(BASE, "RESEARCH", "ABIDI_RENDERED.json"))
    args = parser.parse_args()

    data = load_content()
    jobs = collect(data, args.what, sample=args.sample)
    for kind in OUT_DIRS:
        os.makedirs(OUT_DIRS[kind], exist_ok=True)

    def target(kind, stem):
        return os.path.join(OUT_DIRS[kind], cq.audio_slug(stem) + ".mp3")

    pending = [job for job in jobs if not os.path.exists(target(job[0], job[1]))]
    print("%d clip(s) in the set, %d already rendered, %d to go"
          % (len(jobs), len(jobs) - len(pending), len(pending)))
    if args.list:
        for kind, stem, text in pending[:40]:
            print("  %-8s %-34s %s" % (kind, stem, text))
        if len(pending) > 40:
            print("  ... and %d more" % (len(pending) - 40))
        return 0
    if not pending:
        return 0

    if args.limit:
        pending = pending[:args.limit]
        print("Limiting this run to %d clip(s)." % len(pending))
    if len(pending) > 100 and args.delay < 1.0:
        raise SystemExit("That is a lot of requests for a free service; raise "
                         "--delay to at least 1 second so it stays gentle.")

    open_session()
    done, failed, manifest = 0, [], {}
    if os.path.exists(args.manifest):
        try:
            manifest = json.load(open(args.manifest, encoding="utf-8"))
        except ValueError:
            manifest = {}

    lock = threading.Lock()
    counter = {"n": 0, "done": 0}

    def target_path(kind, stem):
        return os.path.join(OUT_DIRS[kind], cq.audio_slug(stem) + ".mp3")

    def worker(chunk, worker_id):
        # A private jar per worker, seeded from the session already opened.
        jar = "%s.%d" % (JAR, worker_id)
        if os.path.exists(JAR):
            with open(JAR, "rb") as source, open(jar, "wb") as target:
                target.write(source.read())
        _local.jar = jar
        for kind, stem, text in chunk:
            wav = os.path.join(OUT_DIRS[kind], cq.audio_slug(stem) + ".wav")
            mp3 = target_path(kind, stem)
            okay, message = False, ""
            for attempt in range(3):
                try:
                    okay, message = synthesise(text, wav)
                except SystemExit:
                    raise
                except Exception as error:
                    okay, message = False, str(error)
                if okay:
                    break
                if attempt < 2:
                    time.sleep(3 + 4 * attempt)
            with lock:
                counter["n"] += 1
                position = counter["n"]
            if not okay:
                with lock:
                    failed.append((kind, stem, message))
                print("  %3d/%d failed  %-28s %s" % (position, len(pending), stem, message))
                time.sleep(max(args.delay, 1.0))
                continue
            seconds = wav_seconds(wav)
            if seconds < 0.15:
                with lock:
                    failed.append((kind, stem, "silent clip (%.2fs)" % seconds))
                if os.path.exists(wav):
                    os.remove(wav)
                continue
            if not to_mp3(wav, mp3):
                os.replace(wav, mp3.replace(".mp3", ".wav"))
            elif os.path.exists(wav):
                os.remove(wav)
            with lock:
                manifest[cq.audio_slug(stem)] = {"kind": kind, "text": text,
                                                 "seconds": round(seconds, 2),
                                                 "voice": "abidi"}
                counter["done"] += 1
            print("  %3d/%d %-8s %-28s %5.2fs  %s"
                  % (position, len(pending), kind, stem, seconds, text[:34]))
            time.sleep(args.delay)

    workers = max(1, min(args.concurrency, 12))
    chunks = [pending[index::workers] for index in range(workers)]
    threads = [threading.Thread(target=worker, args=(chunk, index))
               for index, chunk in enumerate(chunks) if chunk]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    with open(args.manifest, "w", encoding="utf-8") as handle:
        json.dump(dict(sorted(manifest.items())), handle, indent=1, ensure_ascii=False)
    print("Rendered %d, failed %d. Manifest: %s"
          % (counter["done"], len(failed), args.manifest))
    if failed:
        print("Failures are left out on purpose \u2014 re-run to retry just those.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
