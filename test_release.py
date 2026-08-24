"""Release-artifact invariants for the final no-audio deck."""
import collections
import json
import pathlib
import sqlite3
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
APKG = ROOT / "out" / "german-pareto-deck.apkg"


class TestReleaseArtifact(unittest.TestCase):
    def setUp(self):
        self.assertTrue(APKG.exists(), APKG)

    def test_no_audio_and_card_counts(self):
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(APKG) as package:
                self.assertEqual(json.loads(package.read("media")), {})
                package.extract("collection.anki2", td)
            db = sqlite3.connect(pathlib.Path(td) / "collection.anki2")
            notes = db.execute("select mid, guid, flds from notes").fetchall()
            cards = db.execute("select nid from cards").fetchall()
            self.assertEqual(len(notes), 3122)
            self.assertEqual(len(cards), 3122)
            self.assertEqual(len({row[1] for row in notes}), 3122)
            self.assertEqual(collections.Counter(row[0] for row in notes),
                             collections.Counter({1607392319: 2560,
                                                  1607392398: 500,
                                                  1607392399: 62}))
            for mid, _, fields in notes:
                values = fields.split("\x1f")
                if mid == 1607392319:
                    self.assertEqual(len(values), 6)
                    self.assertTrue(values[1].strip())
                    self.assertNotIn("[sound:", fields)
                elif mid == 1607392398:
                    self.assertEqual(len(values), 3)
                    self.assertIn("{{c1::", values[0])
                else:
                    self.assertEqual(mid, 1607392399)
                    self.assertEqual(len(values), 4)
                    self.assertNotIn("[sound:", fields)
            db.close()

    def test_deck_names(self):
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(APKG) as package:
                package.extract("collection.anki2", td)
            db = sqlite3.connect(pathlib.Path(td) / "collection.anki2")
            decks_blob = db.execute("select decks from col").fetchone()[0]
            decks = [value["name"] for value in json.loads(decks_blob).values()]
            self.assertIn("German Pareto::Core", decks)
            self.assertIn("German Pareto::Extension", decks)
            self.assertIn("German Pareto::Patterns", decks)
            db.close()


if __name__ == "__main__":
    unittest.main()
