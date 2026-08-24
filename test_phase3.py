"""Tests for deterministic phase-3 source handling."""
import csv
import pathlib
import unittest

from src.lemma_overrides import canonical_ref
from src.translations import shortest_translation

ROOT = pathlib.Path(__file__).resolve().parent
DERIVED = ROOT / "derived"


class TestDeterministicChoices(unittest.TestCase):
    def test_german_spelling_wins_casefold_collision(self):
        self.assertEqual(canonical_ref({"gross", "groß"}), "groß")
        self.assertEqual(canonical_ref({"heissen", "heißen"}), "heißen")

    def test_translation_tie_breaks_by_text(self):
        self.assertEqual(shortest_translation({"B", "A"}), "A")
        self.assertEqual(shortest_translation({"long", "short"}), "long")

    def test_override_artifact_rejects_known_bad_link(self):
        with open(DERIVED / "lemma_overrides.csv", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        by_form = {row["form"]: row["lemma"] for row in rows}
        self.assertNotEqual(by_form.get("trinkst"), "triften")
        self.assertEqual(by_form.get("verhält"), "verhalten")
        self.assertNotIn(" ", by_form.get("verhält", ""))
        with open(DERIVED / "lemma_override_exclusions.csv", encoding="utf-8", newline="") as fh:
            rejected = list(csv.DictReader(fh))
        self.assertTrue(any(row["form"] == "trinkst" for row in rejected))

    def test_final_word_rows_have_glosses(self):
        with open(DERIVED / "glosses_lemma.csv", encoding="utf-8", newline="") as fh:
            glosses = {row["lemma"] for row in csv.DictReader(fh) if row["gloss"].strip()}
        with open(DERIVED / "wordlist.csv", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 2560)
        self.assertTrue(all(row["lemma"] in glosses for row in rows))
        with open(DERIVED / "vocab_exclusions.csv", encoding="utf-8", newline="") as fh:
            excluded = list(csv.DictReader(fh))
        self.assertEqual(len(excluded), 28)


if __name__ == "__main__":
    unittest.main()
