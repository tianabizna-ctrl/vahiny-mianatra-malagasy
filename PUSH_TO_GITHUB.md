# Push this project to GitHub

Target: `https://github.com/tianabizna-ctrl/vahiny-mianatra-malagasy` (created, empty).

## Why the push failed

The token `github_pat_11CFAL…fU6n3O` can **read** every repo but **write** nothing:

```
PUT /repos/tianabizna-ctrl/vahiny-mianatra-malagasy/contents/.push-test  → 403
PUT /repos/tianabizna-ctrl/MANIFEST-WEBSITE/contents/.push-test          → 403
git push https://github.com/tianabizna-ctrl/vahiny-mianatra-malagasy.git  → 403
```

Message each time: `Resource not accessible by personal access token`. For a
fine-grained token that means one of two things — and both must be right:

1. **Repository access** must include `vahiny-mianatra-malagasy`
   (its permissions are read-only until the token is edited, even if the token's
   account owns the repo);
2. **Permissions → Contents = Read and write** (Repository permissions).

Edit: https://github.com/settings/tokens → pick the token → *Repository access* →
*Permissions* → **Contents: Read and write** → Save. Then the push below works with
the same token string.

## The push

```bash
cd salama
git init
git config user.email you@example.com
git config user.name "Your Name"
git add -A
git commit -m "Salama! v3.4 — 3,377 Abidi Malagasy TTS clips, offline PWA"
git branch -M main
git remote add origin https://github.com/tianabizna-ctrl/vahiny-mianatra-malagasy.git
git push -u origin main
```

`RESEARCH/push_to_github.sh` does exactly this (token from the environment, remote
removed again afterwards so the token is not left in `.git/config`):

```bash
GH_TOKEN=github_pat_... bash RESEARCH/push_to_github.sh tianabizna-ctrl/vahiny-mianatra-malagasy
```

## What gets pushed

- 78 MB, 3,653 files — the app, the 3,377 Abidi clips, the tooling, the review sheet.
  Under GitHub's 1 GB-per-repo soft limit and its 100 MB per-file limit (largest file
  is 6.2 MB).
- **Not** pushed: `*.wav` leftovers, the zip bundle, the 39 MB inlined review sheet,
  cookie jars (see `.gitignore`).
- Audio is committed as files, not LFS: 35 MB of mp3s is comfortably inside a normal
  repo, and LFS would make cloning harder for a non-technical user.

## If you prefer a different shape

- **Smaller repo** — commit only `APP/` (app + audio) and leave `RESEARCH/` and
  `MALAGASY ASSETS/` out: ~36 MB, ~3,500 files.
- **Audio out of git** — keep code in GitHub and host the mp3s as a release asset
  (`gh release create v3.4 salama-audio.zip`); the app's paths are relative, so the
  folder just has to sit beside `index.html`.
