"""Pre-registered but NOT independently judged blind evaluation scope."""
from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

PATH = Path(__file__).with_name("BLIND_PREREGISTRATION_V1.json")
PIN = "77280d7f917a7f8a25437157b78081147d17088f0b269a90275bac8bc1cbe296"


class NoFakeBlindGoldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = PATH.read_bytes()
        cls.p = json.loads(cls.raw)

    def test_exact_precommitted_protocol_sha256(self):
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), PIN)
        self.assertEqual(
            json.dumps(self.p,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode(),
            self.raw)

    def test_source_archive_and_baseline_pins(self):
        self.assertEqual(self.p["canonical_dev_head"],
                         "f753ba57a1afabaa849f3eeca88170938c0b51f6")
        self.assertEqual(self.p["legacy_master_116_git_blob_sha"],
                         "ab5af7eea02e65d5e36174546a2a94f4cc642d92")
        self.assertEqual(self.p["source_archive_sha256"],
                         "9ccd094766fc0b896d1b237edcf7ea4ef7b7622007262275f0d9e4c0518fee10")

    def test_cohort_commitment_opaque_but_valid(self):
        h=self.p["source_cohort_hash_commitment"]
        self.assertRegex(h,r"^[0-9a-f]{64}$")
        self.assertTrue(self.p["private_salt_retained_outside_github"])
        self.assertTrue(self.p["source_precommitment_verified_in_chat_against_raw_zip"])

    def test_sample_stratification_and_scope(self):
        self.assertEqual(self.p["selected_video_count"],9)
        self.assertEqual(self.p["selected_cue_count"],6829)
        self.assertEqual({k:x["selected"] for k,x in self.p["strata"].items()},
                         {"SHORT":3,"MEDIUM":3,"LONG":3})
        self.assertEqual(self.p["legacy_master_direct_source_overlap_count"],0)

    def test_predeclared_precision_recall_thresholds(self):
        self.assertEqual(self.p["precision_min_ppm"],950000)
        self.assertEqual(self.p["recall_min_ppm"],900000)
        self.assertEqual(self.p["high_risk_recall_min_ppm"],950000)
        self.assertEqual(set(self.p["high_risk_categories"]),
                         {"TAX","PENSION","LEVERAGE","RETURN"})

    def test_sample_size_guard(self):
        self.assertGreaterEqual(self.p["min_total_gold_atoms_for_conclusive_evaluation"],50)
        self.assertGreaterEqual(self.p["min_high_risk_gold_atoms_for_conclusive_evaluation"],30)

    def test_true_independent_review_separate_from_engine(self):
        self.assertEqual(self.p["required_independent_source_first_reviewers"],2)
        self.assertEqual(self.p["required_separate_dispute_adjudicators"],1)
        self.assertTrue(self.p["reviewers_must_not_see_model_predictions_before_sealing_gold"])

    def test_gold_not_fabricated(self):
        self.assertIsNone(self.p["gold_commitment_sha256"])
        self.assertFalse(self.p["gold_reviewers_identity_independently_verified"])
        self.assertIsNone(self.p["held_out_predictions_sha256"])
        self.assertFalse(self.p["precision_recall_measured"])

    def test_no_claim_about_past_exposure_or_release(self):
        self.assertFalse(self.p["previous_exposure_independently_ruled_out"])
        self.assertFalse(self.p["semantic_accuracy_certified"])
        self.assertFalse(self.p["p0_go"])
        self.assertEqual(self.p["stage"],"COHORT_AND_RUBRIC_COMMITTED_GOLD_PENDING")

    def test_private_cohort_not_published(self):
        self.assertNotIn(b"video_id",self.raw)
        self.assertNotIn(b"raw_srt_sha256",self.raw)
        self.assertNotIn(b"private_salt",self.raw.replace(b"private_salt_retained_outside_github",b""))
        self.assertTrue(self.p["cohort_reveal_before_model_prediction_forbidden"])


if __name__ == "__main__":
    unittest.main()
