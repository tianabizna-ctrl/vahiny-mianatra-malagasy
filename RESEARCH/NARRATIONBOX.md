# NarrationBox — what it is, and whether it can voice this course

Checked 6 November 2026: `https://app.narrationbox.com/` (login), marketing page
`https://narrationbox.com/text-to-speech/malagasy`.

## What it offers

- A **web app** (account required) with 1,500+ voices in 80+ languages; the Malagasy
  page claims "Malagasy AI text to speech with natural voices", and its copy is
  unusually well informed about Malagasy (o read as u, final y as i, units-first
  numbers, Ar 5 000 → *dimy arivo ariary*, French loans kept in French spelling).
- 21 "multilingual" narrators. Their portraits are served from
  `narratorfaces.s3.amazonaws.com/narrator_faces/en-US-Chirp3-HD-*.png`, i.e. a
  **Google Chirp 3: HD** voice family. That means the Malagasy is produced by a
  multilingual model told to speak Malagasy — not a model trained on Malagasy, which
  is what Abidi is and what the ear picked out.
- **Free plan: 1,000 words**, no card. Paid plans from about **$9.99/month**.
- **No public API.** Rendering is manual: type or upload, generate, export MP3/WAV.
  (Their Studio accepts EPUB/PDF/DOCX and splits blocks, which is the only bulk path.)

## Can it voice this course?

The course is **3,682 clips / 7,985 words / 50,589 characters**. So:

| Route | Feasible? |
| --- | --- |
| Free plan (1,000 words) | Covers about **⅛** of the course. Enough for a listening test, not for the app. |
| Paid plan, manual export | Possible in principle, but 3,682 clips means 3,682 generate-and-download cycles, or one giant DOCX re-split by hand afterwards. |
| API / automation | **Not available.** Nothing to script, so I cannot do it for you. |

## The cheap automatable alternative nobody mentions

Their narrators look like Google's, so the same voice can be had directly from
**Google Cloud Text-to-Speech**: **Chirp 3: HD at $30 per 1M characters**, with the
**first 1M characters free every month**.

Our whole corpus is 50,589 characters — i.e. **$1.52** if paid, **$0** inside the free
monthly allowance, generated through a real API that a script can drive.

The catch: Google Cloud TTS does **not** list Malagasy (mg-MG) among its supported
locales. A multilingual voice can be asked to read Malagasy, and the result is the same
gamble NarrationBox is making. So this is worth one test, not a commitment: if it works
it is by far the cheapest route; if not, Abidi stays the answer.

## What I would do, in order

1. **Abidi stays the voice** (your ear already decided that, and all 196 dialogue
   sentences are now rendered in it).
2. **Test NarrationBox on the free plan** — paste these five lines, download the MP3s,
   and put them in the workspace:
   `Misaotra betsaka tompoko.` · `Firy ny vidin'ny vary?` · `Manakory ianao?` ·
   `Tsy lavitra. Mianatsimo, avy eo miankavanana.` · `Mipetrapetraha, mazotoa homana.`
   I will run them through the same A/B page against Abidi and MMS.
3. **Only then** consider Google Chirp 3 for the ~2,470 vocabulary words: one script,
   one afternoon, ~$1.50 of billing at worst, if and only if a test clip sounds right.
4. **Check the terms before shipping.** NarrationBox is a commercial service and its
   plan terms govern whether generated audio may be embedded in a distributed app.
   Google's terms allow it; Abidi's position is still unanswered (see `ABIDI.md`).

## Why not just scrape NarrationBox?

It is a paid, logged-in service. Scripting it would need your credentials, would break
their terms, and would cost more in account risk than the $1.52 it takes to do this
properly through an API that permits automation.
