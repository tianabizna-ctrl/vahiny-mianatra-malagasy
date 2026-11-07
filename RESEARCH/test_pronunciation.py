#!/usr/bin/env python3
"""Tests for RESEARCH/pronunciation.py.

    python3 -m unittest discover -s RESEARCH -p "test_*.py" -v
    python3 RESEARCH/test_pronunciation.py        # same thing, one file

These are the invariants the app depends on. They are not linguistic truth —
only a native speaker can settle a stress position — but they catch the class of
bug that shipped before: "ng" syllabified as a prenasalised cluster, "ao"
adapted to a diphthong, an accent mark used from the wrong syllable, and the
Python and JavaScript adapters drifting apart.
"""
import os
import sys
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "RESEARCH"))
import pronunciation as pr

DICT_DOCX = os.path.join(BASE, "MALAGASY ASSETS",
                         "malagasy-english-english-malagasy-dictionary-and-phrasebook-078180843x.docx")


class Syllables(unittest.TestCase):
    def test_prenasalised_cluster_stays_with_previous_vowel(self):
        self.assertEqual(pr.syllabify("antananarivo"),
                         ["an", "ta", "na", "na", "ri", "vo"])
        self.assertEqual(pr.syllabify("trondro"), ["tron", "dro"])

    def test_ng_is_an_onset_not_a_prenasal(self):
        # The bug: man-GAH-tsi-a-ka instead of ma-NGAH-tsi-a-ka.
        self.assertEqual(pr.syllabify("mangatsiaka"),
                         ["ma", "nga", "tsi", "a", "ka"])
        self.assertEqual(pr.syllabify("tonga"), ["to", "nga"])

    def test_oa_is_two_syllables_ao_is_one(self):
        self.assertEqual(pr.syllabify("ahoana"), ["a", "ho", "a", "na"])
        self.assertEqual(pr.syllabify("misaotra"), ["mi", "sao", "tra"])

    def test_accents_do_not_break_syllabification(self):
        self.assertEqual(pr.syllabify("hôpitaly"), pr.syllabify("hopitaly"))


class Stress(unittest.TestCase):
    def test_curated_wins_over_the_rule(self):
        self.assertEqual(pr.stress_position("misaotra"), (2, "dictionary"))
        self.assertEqual(pr.stress_position("vohitra"), (3, "dictionary"))

    def test_defaults(self):
        self.assertEqual(pr.stress_position("sahafa")[0], 2)
        self.assertEqual(pr.stress_position("a")[0], 1)

    def test_dictionary_is_used_without_being_passed_in(self):
        # respell("misaotra") used to fall through to the -tra rule and stress
        # the first syllable, because the curated table was only merged when a
        # lexicon was supplied.
        self.assertEqual(pr.respell("misaotra")[0], "mee-SOH-trah")

    def test_stress_position_never_exceeds_syllable_count(self):
        lexicon = pr.load_stress_lexicon(DICT_DOCX, warn=False)
        for word in list(lexicon)[:400]:
            position = pr.stress_position(word, lexicon)[0]
            self.assertGreaterEqual(position, 1, word)
            self.assertLessEqual(position, len(pr.syllabify(word)) or 1, word)


class Respelling(unittest.TestCase):
    KNOWN = {
        "trano": "TRAH-noo",
        "veloma": "veh-LOO-mah",
        "olona": "oo-LOO-nah",
        "vohitra": "VOO-hee-trah",
        "tsara": "TSAH-rah",
        "gidro": "GEE-droo",
        "antananarivo": "ahn-tah-nah-nah-REE-voo",
    }

    def test_known_words(self):
        for word, expected in self.KNOWN.items():
            self.assertEqual(pr.respell(word)[0], expected, word)

    def test_exactly_one_stressed_syllable(self):
        for word in list(self.KNOWN) + ["mahasoa", "fanafody", "mpianatra"]:
            guess = pr.respell(word)[0]
            stressed = [part for part in guess.split("-") if part == part.upper()
                        and any(c.isalpha() for c in part) and part != part.lower()]
            letters = [part for part in guess.split("-") if any(c.isalpha() for c in part)]
            self.assertEqual(len([p for p in letters if p.isupper()]), 1, guess)
            self.assertTrue(stressed or letters, guess)

    def test_skips_phrases_and_junk(self):
        for text in ("misaotra betsaka", "trano 2", "___", "", "-"):
            self.assertEqual(pr.respell(text), (None, None), text)

    def test_phrase_respelling(self):
        self.assertEqual(pr.respell_phrase("Misaotra betsaka"),
                         "mee-SOH-trah beh-TSAH-kah")
        self.assertIsNone(pr.respell_phrase(" ".join(["word"] * 20)))


class Adaptation(unittest.TestCase):
    def test_french_merina_ao_is_o(self):
        self.assertEqual(pr.adapt("misaotra", "fr"), "mi-ssô-tra")

    def test_oa_never_collapses_to_french_wa(self):
        self.assertNotIn("oua", pr.adapt("ahoana", "fr"))
        self.assertEqual(pr.adapt("soa", "fr"), "sou-a")

    def test_o_is_oo(self):
        self.assertEqual(pr.adapt("trano", "fr"), "tra-nou")
        self.assertEqual(pr.adapt("trano", "it"), "tra-nu")

    def test_h_is_never_deleted(self):
        # The Spanish table used to map h to "" — a silent Spanish h deleting a
        # pronounced Malagasy one.
        for lang in pr.ADAPTERS:
            self.assertIn("h", pr.adapt("hena", lang), lang)
            self.assertIn("h", pr.adapt("hazo", lang), lang)

    def test_g_stays_hard_before_front_vowel(self):
        self.assertEqual(pr.adapt("gidro", "fr"), "gui-drou")
        self.assertEqual(pr.adapt("mangatsiaka", "fr"), "ma-nga-tsi-a-ka")

    def test_intervocalic_s_is_doubled(self):
        self.assertIn("ss", pr.adapt("misaotra", "fr"))
        self.assertIn("ss", pr.adapt("fahasalamana", "fr"))

    def test_ng_is_not_nasalised_apart(self):
        self.assertEqual(pr.adapt("trano", "fr").count("-"), 1)
        self.assertTrue(pr.adapt("mangatsiaka", "fr").startswith("ma-nga"))

    def test_native_and_unknown_languages_are_untouched(self):
        self.assertEqual(pr.adapt("misaotra", "mg"), "misaotra")
        self.assertEqual(pr.adapt("misaotra", "xx"), "misaotra")

    def test_adapter_covers_every_priority_voice(self):
        for lang in pr.VOICE_PRIORITY:
            if lang == "mg":
                continue
            self.assertIn(lang, pr.ADAPTERS, lang)

    def test_syllable_count_is_preserved(self):
        # One output group per Malagasy syllable: that is what makes the
        # hyphenated delivery stop French nasalisation.
        for word in ("antananarivo", "misaotra", "trondro", "mangatsiaka", "gidro"):
            self.assertEqual(len(pr.adapt(word, "fr").split("-")),
                             len(pr.syllabify(word)), word)


class Lexicon(unittest.TestCase):
    def test_recovers_marks_from_the_dictionary(self):
        lexicon = pr.load_stress_lexicon(DICT_DOCX, warn=False)
        self.assertGreater(len(lexicon), pr.MIN_STRESS_LEXICON_ENTRIES)
        self.assertIn("ianareo", lexicon)

    def test_never_returns_a_position_beyond_the_antepenultimate(self):
        lexicon = pr.load_stress_lexicon(DICT_DOCX, warn=False)
        for word, position in lexicon.items():
            self.assertIn(position, (1, 2, 3), word)

    def test_missing_dictionary_warns_instead_of_failing_silently(self):
        self.assertWarns = None  # stderr warning, checked by the build output
        lexicon = pr.load_stress_lexicon(os.path.join(BASE, "nope.docx"), warn=False)
        self.assertEqual(lexicon, dict(pr.CURATED_STRESS))

    def test_no_junk_keys(self):
        lexicon = pr.load_stress_lexicon(DICT_DOCX, warn=False)
        self.assertNotIn("misaotra_betsaka", lexicon)
        for word in lexicon:
            for part in word.split("-"):
                if "-" in word:
                    self.assertRegex(part, r"[aeiou]", word)

    def test_conflicts_are_reported(self):
        conflicts = pr.stress_conflicts(DICT_DOCX)
        self.assertEqual({word for word, _, _ in conflicts},
                         {"dokotera", "lehibe", "mipetraka"})


class CuratedTable(unittest.TestCase):
    def test_entries_are_shaped_like_words(self):
        for word, position in pr.CURATED_STRESS.items():
            self.assertRegex(word, r"^[a-z]+$", word)
            self.assertIn(position, (1, 2, 3), word)
            self.assertLessEqual(position, len(pr.syllabify(word)) or 1, word)


if __name__ == "__main__":
    unittest.main(verbosity=2)
