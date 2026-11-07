"""Checks source integrity, 53 candidate relations and honest approval status."""
import copy
import unittest
from pathlib import Path
from unittest.mock import patch

from ire.v5 import five_study_gate as m

ROOT=Path(__file__).resolve().parents[3]

class FiveSourceStudiesTests(unittest.TestCase):
    def test_5_real_video_reviews_and_53_provisional_claims(self):
        r=m.verify(ROOT)
        self.assertEqual(r["full_transcripts_read_by_chat"],5)
        self.assertEqual(r["total_source_cues"],3313)
        self.assertEqual(r["coverage_sections"],41)
        self.assertEqual(r["provisional_claims"],53)
        self.assertEqual(sum(r["provisional_relations"].values()),53)
        self.assertEqual(r["independently_verified_financial_facts"],0)
        self.assertFalse(r["personalized_advisory_approved"])
        self.assertFalse(r["private_srt_bytes_verified_this_run"])

    def mutate(self,video,change):
        original=m.load
        name=video+".json"
        def fake(path):
            x=original(path)
            if str(path).endswith("/ire/v5/studies/"+name):
                x=copy.deepcopy(x)
                change(x)
            return x
        with patch.object(m,"load",side_effect=fake):
            return m.verify(ROOT)

    def test_unsupported_factual_approval_is_blocked(self):
        with self.assertRaisesRegex(m.StudyGateError,"STUDY_UNAPPROVED_CLAIM_ESCALATED"):
            self.mutate("l0Q-2Ah-ba8",
                        lambda x:x["claims"][0].update(advisory_approved=True))

    def test_wrong_zip_source_fingerprint_is_blocked(self):
        with self.assertRaisesRegex(m.StudyGateError,"STUDY_ORIGINAL_SRT_MISMATCH"):
            self.mutate("7p3p7TKcdqY",
                        lambda x:x.update(source_sha256="0"*64))

    def test_cue_gap_cannot_be_called_complete(self):
        with self.assertRaisesRegex(m.StudyGateError,"STUDY_CUE_SECTION_GAP_OR_OVERLAP"):
            self.mutate("2bLy034D5LA",
                        lambda x:x["source_sections"][1].update(first_cue=33))

    def test_fake_prior_claim_is_blocked(self):
        with self.assertRaisesRegex(m.StudyGateError,"STUDY_UNKNOWN_OR_OUT_OF_SCOPE_LEGACY_CLAIM"):
            self.mutate("z1oZOJ3_uIk",
                        lambda x:x["claims"][0].update(prior_claim_ids=["FAKE"]))

    def test_missing_official_source_catalog_entry_is_blocked(self):
        with self.assertRaisesRegex(m.StudyGateError,"STUDY_UNKNOWN_WEB_EVIDENCE"):
            self.mutate("tDD5GzvDYq8",
                        lambda x:x["claims"][0].update(evidence_ids=["SRC-MADE-UP"]))

    def test_unresolved_cue_cannot_be_mislabeled_atomic_verified(self):
        with self.assertRaisesRegex(m.StudyGateError,"STUDY_FALSIFIED_COMPLETION_OR_APPROVAL"):
            self.mutate("l0Q-2Ah-ba8",
                        lambda x:x.update(each_cue_independently_claim_adjudicated=True))

    def test_three_high_stakes_corrections_are_preserved(self):
        r={vid:m.load(ROOT/"ire/v5/studies"/(vid+".json"))
           for vid in m.STUDIES}
        by={vid:{c["claim_id"]:c for c in doc["claims"]}
            for vid,doc in r.items()}
        self.assertEqual(by["l0Q-2Ah-ba8"]["P217-07"]["review_status"],"OFFICIAL_CORRECTION")
        self.assertEqual(by["2bLy034D5LA"]["R250-06"]["review_status"],
                         "PENDING_REGULATORY_CHANGE")
        self.assertEqual(by["tDD5GzvDYq8"]["A237-05"]["review_status"],
                         "UNSAFE_PROFIT_GUARANTEE")
        self.assertEqual(by["z1oZOJ3_uIk"]["E229-06"]["review_status"],
                         "HISTORICAL_PRODUCT_RANKING")

    def test_dca_arithmetic_counterexample_is_not_approved_earnings(self):
        rec=m.load(ROOT/"ire/v5/studies/tDD5GzvDYq8.json")
        a=rec["counterexample_arithmetic"]
        self.assertEqual(a["total_units"],16)
        self.assertEqual(a["average_cost_krw"],93750)
        self.assertEqual(a["ending_value_krw"],800000)
        self.assertEqual(a["unrealized_loss_krw"],700000)
        self.assertLess(a["return_pct"],-46)

if __name__=="__main__":
    unittest.main()
