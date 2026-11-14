"""Synthetic and actual public-receipt-only V113 regressions; no private subtitles."""
import copy
import unittest
from v113_public_window_evidence_debt_guard import load_receipts, audit

class V113PublicWindowEvidenceDebtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = load_receipts()

    def check_bad(self, edit):
        d = copy.deepcopy(self.baseline)
        edit(d)
        with self.assertRaises(ValueError):
            audit(d)

    def test_public_receipts_reconcile(self):
        r = audit(self.baseline)
        self.assertEqual((r["distinct_window_cues_in_named_three_cohorts"],
                          r["not_in_these_12_windows"]), (480,15377))
        self.assertEqual(r["still_open"],12)
        self.assertIsNone(r["certified_recall"])
        self.assertFalse(r["prior_v92_v75_overlap_fully_reconciled"])

    def test_duplicate_window_rejected(self):
        self.check_bad(lambda d: d["v102"]["new_windows"].__setitem__(
            0, ["sz5N9WJS310","W00020"]))

    def test_duplicate_v101_window_rejected(self):
        self.check_bad(lambda d: d["v101"]["selected_window_summaries"][0].__setitem__(
            "window_id","W00020"))

    def test_out_of_video_window_rejected(self):
        self.check_bad(lambda d: d["v102"]["new_windows"][0].__setitem__(1,"W09999"))

    def test_cross_cohort_mismatch_rejected(self):
        self.check_bad(lambda d: d["v102"].__setitem__("cumulative_shadow_reviewed_cues",319))

    def test_route_accounting_rejected(self):
        self.check_bad(lambda d: d["v102"]["reviewed_route_counts"].__setitem__(
            "BASELINE_PARENT_PENDING",146))

    def test_fake_v98_coverage_rejected(self):
        self.check_bad(lambda d: d["v98"].__setitem__(
            "source_first_full_semantic_review_completed",True))

    def test_fake_independent_gold_rejected(self):
        self.check_bad(lambda d: d["v109"].__setitem__("independent_gold",True))

    def test_fake_go_rejected(self):
        self.check_bad(lambda d: d["v112"].__setitem__("p0_go",True))

    def test_fake_precision_rejected(self):
        self.check_bad(lambda d: d["v112"].__setitem__("certified_precision",1.0))

    def test_source_pin_drift_rejected(self):
        self.check_bad(lambda d: d["v110"].__setitem__("source_zip_sha256","f"*64))

    def test_v110_coverage_misread_rejected(self):
        self.check_bad(lambda d: d["v110"].__setitem__("v110_speech_act_units",84))

    def test_v111_unearned_audio_closure_rejected(self):
        self.check_bad(lambda d: d["v111"].__setitem__("open_audio",6))

    def test_v112_unearned_account_closure_rejected(self):
        self.check_bad(lambda d: d["v112"].__setitem__("open_account_scope",0))

    def test_v112_tax_promotion_rejected(self):
        self.check_bad(lambda d: d["v112"].__setitem__(
            "current_tax_personal_application_resolved",True))

    def test_v98_baseline_mutation_rejected(self):
        self.check_bad(lambda d: d["v102"].__setitem__("v98_baseline_mutated",True))

    def test_v110_v111_mutation_rejected(self):
        self.check_bad(lambda d: d["v112"].__setitem__("v110_v111_sources_untouched",False))

    def test_unknown_source_footprint_rejected(self):
        self.check_bad(lambda d: d["v101"]["selected_window_summaries"][1].__setitem__(
            "video_id","not-a-video"))

if __name__ == "__main__":
    unittest.main()
