"""Check mandatory original V5 file survival alongside new validation additions."""
import unittest
from pathlib import Path
from ire.v5 import repository_tree_gate as g

ROOT=Path(__file__).resolve().parents[3]

class RepositoryTreeTests(unittest.TestCase):
    def test_previous_20_questions_and_60_study_files_still_exist(self):
        r=g.check(ROOT)
        self.assertEqual(r["essential_original_and_new_files"],23)
        self.assertTrue(r["original_20_scenarios_preserved"])
        self.assertTrue(r["old_13_education_graph_preserved"])
        self.assertFalse(r["full_git_tree_diff_checked_inside_ci"])

    def test_missing_previous_scenario_file_is_fatal(self):
        names=set(g.ESSENTIAL)
        names.remove("ire/v5/advisory_integration/question_scenarios_20261105.json")
        with self.assertRaisesRegex(g.RepositoryTreeError,
                                    "REQUIRED_RESEARCH_FILES_MISSING"):
            g.check(ROOT,names)

    def test_missing_previous_original_unit_test_is_fatal(self):
        names=set(g.ESSENTIAL)
        names.remove("ire/v5/tests/test_advisory60.py")
        with self.assertRaisesRegex(g.RepositoryTreeError,
                                    "REQUIRED_RESEARCH_FILES_MISSING"):
            g.check(ROOT,names)

if __name__=="__main__":
    unittest.main()
