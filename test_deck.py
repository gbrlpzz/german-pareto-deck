"""Unit tests for the cloze matcher (v0.2 token-span matching).

Run: .venv/bin/python -m unittest test_deck -v
"""
import unittest

from src.deck import make_cloze, clean_gloss


class TestMakeCloze(unittest.TestCase):
    def test_simple(self):
        out = make_cloze("Ich weiß es.", "weiß")
        self.assertEqual(out, "Ich {{c1::weiß}} es.")

    def test_multiword_keeps_punctuation(self):
        out = make_cloze("Ich weiß nicht, was du meinst.", "ich weiß nicht")
        self.assertEqual(out, "{{c1::Ich}} {{c1::weiß}} {{c1::nicht}}, was du meinst.")

    def test_frame_two_spans(self):
        out = make_cloze("Er hat kein Wort gesagt.", "hat … gesagt")
        self.assertEqual(out, "Er {{c1::hat}} kein Wort {{c1::gesagt}}.")

    def test_apostrophe_form(self):
        out = make_cloze("Das geht's nicht.", "gehts")
        self.assertEqual(out, "Das {{c1::geht's}} nicht.")

    def test_case_insensitive(self):
        out = make_cloze("Kann ich helfen?", "kann … helfen")
        self.assertEqual(out, "{{c1::Kann}} ich {{c1::helfen}}?")

    def test_miss_returns_none(self):
        self.assertIsNone(make_cloze("Hallo Welt.", "ich weiß nicht"))
        self.assertIsNone(make_cloze("Er hat es nie.", "hat … gesagt"))


class TestCleanGloss(unittest.TestCase):
    def test_keeps_real_gloss(self):
        self.assertEqual(clean_gloss("to go; to walk"), "to go; to walk")

    def test_drops_grammar_descriptors(self):
        self.assertEqual(clean_gloss("nominative/accusative singular feminine of der"), "")
        self.assertEqual(clean_gloss("third-person singular present of sein"), "")
        self.assertEqual(clean_gloss(""), "")


if __name__ == "__main__":
    unittest.main()
