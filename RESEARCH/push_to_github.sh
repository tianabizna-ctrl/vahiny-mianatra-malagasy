#!/bin/bash
# Push the Salama! project to GitHub.
#
#   GH_TOKEN=github_pat_... bash RESEARCH/push_to_github.sh [owner/repo]
#
# The token is passed in the environment, never written to .git/config, so it does
# not end up in the repository or in the workspace snapshot.
set -euo pipefail
cd "$(dirname "$0")/.."

REPO="${1:-tianabizna-ctrl/vahiny-mianatra-malagasy}"
: "${GH_TOKEN:?set GH_TOKEN to a GitHub personal access token with contents:write}"

echo "== 1. commit whatever changed since the last push =="
git add -A
if ! git diff --cached --quiet; then
  git commit -qm "Salama! — content and audio update ($(date +%Y-%m-%d))"
  echo "   committed"
else
  echo "   nothing new to commit"
fi

echo "== 2. check the remote is reachable and empty-or-existing =="
API="https://api.github.com/repos/$REPO"
code=$(curl -s -o /tmp/repo.json -w '%{http_code}' \
        -H "Authorization: Bearer $GH_TOKEN" "$API")
if [ "$code" != "200" ]; then
  echo "   GitHub says HTTP $code for $REPO"
  python3 - <<'PY'
import json
try:
    print("  ", json.load(open('/tmp/repo.json')).get('message'))
except Exception:
    pass
PY
  echo "   Create the empty repository first (github.com/new, no README), then re-run."
  exit 1
fi
echo "   found $REPO"

echo "== 3. push (this uploads the audio; it can take a few minutes) =="
git remote remove origin 2>/dev/null || true
git remote add origin "https://x-access-token:${GH_TOKEN}@github.com/${REPO}.git"
git branch -M main
git push -u origin main --force

echo "== 4. report =="
python3 - <<'PY'
import json, subprocess, urllib.request
PY
curl -s -H "Authorization: Bearer $GH_TOKEN" "$API" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print('   repository: %s (%s)' % (d['full_name'], 'private' if d['private'] else 'public'))
print('   size: %.1f MB on GitHub' % (d['size']/1024))
print('   url: %s' % d['html_url'])"
git remote remove origin
echo "   (remote removed again so the token is not left behind)"
echo "== done =="
