# Accessibility audit — Salama! (v3.0)

**Date:** 6 November 2026
**Engine:** axe-core 4.11.1
**Pages tested:** Today (390 × 844 and 1280 × 900), session runner, review, words, settings.
**Result:** 0 violations after the fixes below.

## Violations found in the first pass

| Rule | Impact | Element | Cause | Fix |
|---|---|---|---|---|
| `button-name` | critical | `#soundBtn` in the header | The label span was `display: none` under 760px to save space, which also removed the accessible name | Replaced the visual hiding with an off-screen clip so the label stays in the accessibility tree (`styles.css`) |
| `link-name` | serious | Settings link in the header | Same cause | Same fix |
| `color-contrast` | serious | Dialogue speaker labels (`You`, `Host`) | Gold `#b9791f` on cream `#faf6ef` is 3.35:1; the minimum is 4.5:1 for text under 24px | Added `--gold-ink: #87550f` (5.8:1) and used it for all gold text; gold stays for borders and fills |
| `color-contrast` | serious | `.approx`, culture sources, quiet metadata | `--ink-faint` at `#8a7a68` was borderline | Darkened to `#6f6051` |

## What already passed

Skip link and focusable target, one `main` landmark, landmark uniqueness, `html lang`, document title, viewport zoom (no `user-scalable=no`), heading order, list structure, nested-interactive, `tabindex` values, ARIA attribute validity.

## Deliberate accessibility decisions

* Every Malagasy string is wrapped in `lang="mg"` so screen readers and browser speech engines do not read it as English: `ui.mg()` in `js/ui.js` and explicit `lang="mg"` attributes in the views.
* All interactive controls are real `<button>` or `<a>` elements with at least 44 × 44 px targets; primary actions are 52–60 px tall.
* Keyboard focus is always visible (`:focus-visible`, 3px gold outline with offset).
* Body text is 21px, the smallest label is 18px, and the Text control offers 21 / 23 / 26px body sizes.
* `prefers-reduced-motion` disables the only transitions used.
* Quiz feedback and toasts are announced through `role="status"`.
* The mobile navigation is fixed to the bottom with 64px targets; the header keeps only three utility controls.

## Addendum — v3.1 (6 November 2026)

New controls, all reviewed by hand against the same rules:

* Every Listen button is paired with a **Syllables** button. Both are 44 px minimum,
  both are real `<button>`s with a text label, and the slow one is visually quieter but
  not lower-contrast than the audit's threshold.
* A speaking button gets `data-speaking` while audio runs. The pulse animation is
  suppressed by the existing `prefers-reduced-motion` rule, so the state is conveyed by
  the border and background colour as well, never by motion alone.
* Settings gained: speaking speed (3 chips), a voice `<select>` with an explicit
  `aria-label`, syllable mode, "Hear a sample", and "Restore from file" (a `<label for>`
  driving a hidden `<input type=file>`, so it is keyboard reachable).
* Restore failures are announced through the existing `role="status"` toast rather than
  an `alert()`.
* `utterance.lang` is deliberately the **voice's** language, not `mg`, while the visible
  text keeps `lang="mg"`. Changing it to `mg-MG` silences engines that have no Malagasy
  voice. Do not "fix" this.

## Re-running the audit

```bash
cd APP && python3 -m http.server 8788
```

Then run an accessibility audit against `http://127.0.0.1:8788/index.html#/today` and check the session runner at `#/session/w1s1`, which contains the audio player and the most interactive controls.
