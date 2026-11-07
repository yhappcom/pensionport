"""Check that private-source-derived P0 data cannot masquerade as research GO."""
import unittest
from ire.v5.validation.p0_derived_bundle_gate import (
    read_bundle, research_state, check_no_original_source_leak)


class P0Real10DerivedIntegrityTests(unittest.TestCase):
    def test_full_cohort_source_and_provisional_claim_counts(self):
        r = research_state()
        self.assertEqual(r["real_source_video_count"], 10)
        self.assertEqual(r["real_source_cue_count"], 6474)
        self.assertEqual(r["source_windows_total"], 366)
        self.assertEqual(r["model_atomic_claim_candidates_provisional"], 78)
        self.assertEqual(r["narrow_official_source_reviews"], 19)
        self.assertEqual(r["long_video_source_windows_scoped_reviewed"], 18)

    def test_claim_candidates_have_source_refs_but_no_final_approval(self):
        s, l = read_bundle("short5"), read_bundle("long5")
        self.assertTrue(all(len(c["anchor_cue_sha256"]) == 64
                            and len(c["span_sha256"]) == 64
                            and not c["financial_truth_approved"]
                            for v in s["videos"] for c in v["candidates"]))
        self.assertTrue(all(len(c["source_window_primary_sha256"]) == 64
                            and not c["approved_financial_fact"]
                            for v in l["videos"] for c in v["claims"]))
        self.assertFalse(s["independent_gold"])
        self.assertFalse(l["complete_atomic_recall_certified"])

    def test_all_risk_windows_flagged_as_not_semantically_completed(self):
        x = read_bundle("long5risk")
        self.assertEqual(sum(len(v["window_inventory"]) for v in x["videos"]), 354)
        for v in x["videos"]:
            for w in v["window_inventory"]:
                self.assertTrue(w["must_review_all_semantics"])
                self.assertFalse(w["human_verification_complete"])

    def test_evidence_sources_do_not_authorize_financial_truth(self):
        x = read_bundle("evidence19")
        self.assertEqual(x["evidence_review_count"], 19)
        self.assertTrue(all(r["official_url"].startswith("https://")
                            and not r["automatically_approved_as_financial_truth"]
                            for r in x["evidence_reviews"]))
        self.assertEqual(x["financial_truth_formally_approved"], 0)

    def test_no_false_go_or_private_srt_bytes(self):
        r = research_state()
        self.assertEqual(r["p0_financial_research_release"], "NO_GO")
        self.assertEqual(r["p1_formal_knowledge_merge"], "BLOCKED")
        self.assertFalse(r["personal_advice_approved"])
        with self.assertRaisesRegex(ValueError, "P0_DERIVED_ORIGINAL_SOURCE_LEAK"):
            check_no_original_source_leak({"original_srt": "not allowed"})


if __name__ == "__main__":
    unittest.main()
