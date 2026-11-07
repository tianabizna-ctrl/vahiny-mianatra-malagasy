# Ten questions for a Malagasy speaker (Merina)

Print this or paste it into a message. It takes about 15 minutes and it is the
difference between pronunciation the app *claims* and pronunciation it can *stand
behind*. Answer in any mix of Malagasy, French or English — a voice recording is even
better than writing.

How to answer: for each word, just say **which syllable is loudest**, and whether the
word below it looks right. Write the stressed syllable in capitals, e.g. `mi-PE-tra-ka`.

---

## A. The three words where our two sources disagree

The dictionary and our own table point at different syllables. A native ear settles them.

| # | Word | Means | Dictionary says | Our table says | Which is right? |
|---|------|-------|-----------------|----------------|-----------------|
| 1 | **dokotera** | doctor | do-ko-**TE**-ra | **DO**-ko-te-ra | |
| 2 | **lehibe** | big | le-hi-**BE** | **LE**-hi-be | |
| 3 | **mipetraka** | to sit / live | mi-**PE**-tra-ka | mi-**PE**-tra-ka | |

## B. Seven common words we are only guessing at

These are taught in the first weeks and currently get the default "second-to-last
syllable" rule. If any is wrong, the learner is confidently taught the wrong rhythm.

| # | Word | Means | We say | Correct stress? |
|---|------|-------|--------|-----------------|
| 4 | **misaotra** | thank you | mi-**SO**-tra | |
| 5 | **veloma** | goodbye | ve-**LO**-ma | |
| 6 | **ahoana** | how (in *manao ahoana*) | a-**HOO**-a-na | |
| 7 | **fahasalamana** | health | fa-ha-sa-la-**MA**-na | |
| 8 | **mahafinaritra** | pleasant, lovely | ma-ha-fi-na-**RI**-tra | |
| 9 | **mipetraka** | → see #3 | | |
| 10 | **misaotra betsaka** | thank you very much | mi-**SO**-tra be-**TSA**-ka | |

## C. Three sound questions (one line each)

11. **Final vowels.** In ordinary speech, do you hear **trano** as *tra-noo* or more like
    *tra-n*? We keep the vowel, and tell learners it may be whispered — is that fair?
12. **"ao".** In Antananarivo, **misaotra** — does it sound closer to *mee-SOH-tra* or
    *mee-SOW-tra*? We currently say "closer to SOH".
13. **"tr" / "dr".** Is our description fair — "**trano** and **mandry**, with the tongue
    further back than the English *tr* in *train*"? If you have a better comparison for
    an English speaker, what is it?

---

## D. Optional, if there is time

Listen to any 20 entries in `pron_qa.html` (open it in a browser, press ▶ on each row) and
mark ✔ / ✘. That file covers all 3,195 words and phrases and exports a spreadsheet.
That is the single most valuable hour anyone can spend on this project.

## What happens with the answers

* Wrong stress → we correct `CURATED_STRESS` and re-run the tests; the correction is then
  used everywhere, including the audio.
* Right stress but wrong sound → the word goes on the recording list
  (`render_audio.py --list`) or gets a rendered clip.
* Answers get recorded in `RESEARCH/PRONUNCIATION.md`, which currently says plainly that
  **nothing has been checked by a native speaker yet**. Once these ten are answered, that
  sentence changes for the words they cover.
