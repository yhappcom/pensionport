"""Previously committed source cohort remains pinned; old human-review contract is historical.

The owner superseded human-gold requirements with first-party source verification
on 2026-11-08. This test DOES NOT certify unseen exposure or true model accuracy.
"""
from __future__ import annotations
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent

class V2SourceScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=json.loads((ROOT/"BLIND_PREREGISTRATION_V1.json").read_text(encoding="utf-8"))
        cls.new=json.loads((ROOT/"OFFICIAL_SOURCE_VERIFICATION_POLICY_V2.json").read_text(encoding="utf-8"))

    def test_source_commitment_persists_without_revealing_private_video_ids(self):
        self.assertEqual(self.old["selected_video_count"],9)
        self.assertEqual(self.old["selected_cue_count"],6829)
        self.assertEqual(self.old["source_cohort_hash_commitment"],
                         "53fc99cef5353fe2b8834461110b190b2d6b893777ce017a4fa2d344edcc530e")
        self.assertEqual(self.old["legacy_master_direct_source_overlap_count"],0)
        self.assertFalse(self.old["previous_exposure_independently_ruled_out"])

    def test_v2_supersedes_old_human_requirements_without_erasing_history(self):
        self.assertTrue(self.new["legacy_v1_preserved_unchanged"])
        self.assertFalse(self.new["independent_human_review_required"])
        self.assertFalse(self.new["independent_human_gold_required"])
        self.assertFalse(self.new["independent_adjudicator_required"])
        self.assertIn("ACCEPTANCE_ONLY",self.new["supersedes"])

    def test_avoid_fabricated_statistical_precision(self):
        self.assertFalse(self.new["statistical_precision_recall_claims_allowed_without_independent_gold"])
        self.assertIn("CONTRADICTED",self.new["allowed_verdicts"])
        self.assertIn("UNVERIFIED",self.new["allowed_verdicts"])
        self.assertFalse(self.new["p0_go"])

    def test_no_private_secret_in_current_policy(self):
        text=(ROOT/"OFFICIAL_SOURCE_VERIFICATION_POLICY_V2.json").read_text(encoding="utf-8")
        self.assertNotIn("source_cohort_salt",text)
        self.assertNotIn("hidden_video_ids",text)
        self.assertTrue(re.fullmatch("[0-9a-f]{64}",self.old["source_cohort_hash_commitment"]))

if __name__=="__main__":
    unittest.main()
