"""Small tests for Kaikki gloss extraction rules."""
import unittest

from src.lemma_glosses import useful_gloss


class TestUsefulGloss(unittest.TestCase):
    def test_uses_translation_after_grammar_label(self):
        got = useful_gloss({"glosses": ["genitive masculine of der", "whose"],
                            "tags": ["relative"]})
        self.assertEqual(got[0], "whose")

    def test_extracts_quoted_form_translation(self):
        got = useful_gloss({"glosses": ["nominative plural of diejenige (“those”)"],
                            "tags": ["form-of"]})
        self.assertEqual(got[0], "those")

    def test_extracts_comparative_translation(self):
        got = useful_gloss({"glosses": ["comparative degree of gut; better"],
                            "tags": ["form-of", "comparative"]})
        self.assertEqual(got[0], "better")

    def test_rejects_inflection_only(self):
        self.assertIsNone(useful_gloss({"glosses": ["inflection of sagen:"],
                                         "tags": ["form-of"]}))


if __name__ == "__main__":
    unittest.main()
