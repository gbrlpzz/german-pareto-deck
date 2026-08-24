"""Smoke tests for the german-pareto-deck pipeline.

Run: .venv/bin/python -m unittest test_pipeline -v
Validates artifact schemas and the D8 selection invariants; heavy stages
(fetch, patterns) are not re-run here - their outputs are committed.
"""
import csv, json, pathlib, unittest

ROOT = pathlib.Path(__file__).resolve().parent
DERIVED = ROOT / "derived"


def rows(name):
    return list(csv.DictReader(open(DERIVED / name)))


class TestFrequencyArtifacts(unittest.TestCase):
    def test_top_forms_monotone(self):
        rows_ = rows("top_forms.csv")[:5000]
        shares = [float(r["cum_share_pct"]) for r in rows_]
        self.assertEqual(shares, sorted(shares))
        self.assertEqual([int(r["rank"]) for r in rows_], list(range(1, 5001)))

    def test_subtitles_anchor_matches_report(self):
        rows_ = {int(r["rank"]): float(r["cum_share_pct"])
                 for r in rows("subtitles_curve.csv")}
        self.assertAlmostEqual(rows_[2000], 85.3, places=1)
        self.assertAlmostEqual(rows_[10000], 94.8, places=1)


class TestPatternSelection(unittest.TestCase):
    def setUp(self):
        self.sel = rows("patterns_selected.csv")
        self.summary = json.load(open(DERIVED / "selection_summary.json"))

    def test_total_is_literature_anchor(self):
        self.assertEqual(len(self.sel), 500)  # D3: PHRASE-List scale

    def test_every_pattern_has_exemplar(self):
        for r in self.sel:
            self.assertTrue(r["examples"], r["pattern"])

    def test_bundles_are_multiword(self):
        for r in self.sel:
            if r["class"] == "lexical_bundle":
                self.assertGreaterEqual(int(r["n"]), 3)  # D8 registry

    def test_no_blocklist_names(self):
        stats = json.load(open(DERIVED / "pattern_stats.json"))
        banned = set(stats["criteria"]["name_blocklist"])
        for r in self.sel:
            if r["kind"] == "bundle":
                toks = set(r["pattern"].split())
                self.assertFalse(toks & banned, r["pattern"])


class TestWordList(unittest.TestCase):
    def test_tiers(self):
        wl = rows("wordlist.csv")
        self.assertTrue(wl)
        for r in wl:
            self.assertIn(r["tier"], ("core", "ext"))
            self.assertGreaterEqual(int(r["rank"]), 1)


if __name__ == "__main__":
    unittest.main()
