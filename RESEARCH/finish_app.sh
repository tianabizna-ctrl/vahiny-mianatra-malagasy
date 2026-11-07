#!/bin/bash
# Finish the Abidi switchover once the render is complete.
#   bash RESEARCH/finish_app.sh
# Safe to re-run: every step is idempotent, and the audio sweep only touches
# leftover .wav files that never got converted.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== 1. sweep leftover wav -> mp3 =="
python3 - <<'PY'
import glob, os, sys
sys.path.insert(0, 'RESEARCH')
import abidi_render as ar
converted = discarded = failed = 0
for wav in sorted(glob.glob('APP/media/audio_abidi/*/*.wav')):
    with open(wav, 'rb') as handle:
        if handle.read(4) != b'RIFF':
            os.remove(wav); discarded += 1; continue
    if ar.to_mp3(wav, wav[:-4] + '.mp3'):
        os.remove(wav); converted += 1
    else:
        failed += 1
print("converted %d, discarded %d, left %d" % (converted, discarded, failed))
if failed:
    sys.exit("codec missing: pip install lameenc soundfile")
PY

echo "== 2. rebuild content with Abidi =="
python3 RESEARCH/build_app_data.py

echo "== 3. check chain =="
python3 RESEARCH/test_pronunciation.py | tail -1
python3 RESEARCH/check_parity.py | tail -1
python3 RESEARCH/validate_content.py | tail -3
node RESEARCH/smoke_app.js | tail -1

echo "== 4. regenerate the review sheet and the A/B page =="
python3 RESEARCH/proofread.py --inline-audio
python3 RESEARCH/abidi_sample_page.py | head -1

echo "== 5. coverage report =="
python3 - <<'PY'
import glob, json, os
raw = open('APP/data/content.js', encoding='utf-8').read()
data = json.loads(raw[raw.index('{'):raw.rindex('}') + 1])
for name, key in (("words", "wordAudio"), ("phrases", "phraseAudio"), ("lines", "lineAudio")):
    audio = data.get(key, {})
    abidi = [k for k, v in audio.items() if 'audio_abidi' in v]
    print("  %-8s wired %4d  of which abidi %4d  mms %4d"
          % (name, len(audio), len(abidi), len(audio) - len(abidi)))
print("  clips on disk: words %d phrases %d lines %d"
      % tuple(len(glob.glob('APP/media/audio_abidi/%s/*.mp3' % k))
              for k in ('words', 'phrases', 'lines')))
total = sum(os.path.getsize(p) for p in glob.glob('APP/media/audio_abidi/*/*.mp3'))
print("  abidi audio: %.1f MB" % (total / 1048576))
PY

echo "== 6. package =="
rm -f salama-3.4-complete.zip
zip -qr salama-3.4-complete.zip . -x "salama-3.*-complete.zip" -x "*/__pycache__/*" \
    -x "*.pyc" -x "PROOFREAD_AUDIO.html" -x "RESEARCH/.abidi_cookies*" -x "*.wav"
ls -lh salama-3.4-complete.zip
echo "== done =="
