"""Provisional claim ownership regressions; no private transcript embedded."""
import copy
import json
from pathlib import Path
import unittest
from ire.v5.p0_claim_ownership_gate import validate_claim_ownership, ClaimOwnershipError

ROOT = Path(__file__).resolve().parents[1]

class ClaimOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads((ROOT / "ire/v5/validation/p0_claim_ownership_index.json").read_text("utf-8"))

    def test_corrected_real_26_anchor_index(self):
        result = validate_claim_ownership(self.base)
        self.assertEqual(result["checked_claims"], 26)
        self.assertEqual(result["checked_cues"], 144)
        self.assertFalse(result["p0_go"])

    def assert_rejected(self, mutate, code):
        obj = copy.deepcopy(self.base)
        mutate(obj)
        with self.assertRaisesRegex(ClaimOwnershipError, code):
            validate_claim_ownership(obj)

    def test_pr38_cue729_misowned(self):
        self.assert_rejected(lambda d: next(c for c in d["claims"] if c["anchor_cue"] == 729).__setitem__("window_id", "W00042"), "CLAIM_WINDOW_MISMATCH")

    def test_pr38_cue772_misowned(self):
        self.assert_rejected(lambda d: next(c for c in d["claims"] if c["anchor_cue"] == 772).__setitem__("window_id", "W00044"), "CLAIM_WINDOW_MISMATCH")

    def test_source_drift(self):
        self.assert_rejected(lambda d: d["claims"][0].__setitem__("source_sha256", "0" * 64), "CLAIM_SOURCE_MISMATCH")

    def test_missing_support(self):
        self.assert_rejected(lambda d: d["claims"][0].__setitem__("support_cues", []), "CLAIM_SUPPORT_MISSING")

    def test_cross_window_requires_review(self):
        self.assert_rejected(lambda d: d["claims"][0].__setitem__("support_cues", [659, 666]), "CROSS_WINDOW_REVIEW_REQUIRED")

    def test_outside_batch_support_rejected(self):
        self.assert_rejected(lambda d: d["claims"][0].__setitem__("support_cues", [659, 647]), "CLAIM_SUPPORT_OUTSIDE_BATCH")

    def test_duplicate_claim_id(self):
        self.assert_rejected(lambda d: d["claims"][1].__setitem__("claim_id", d["claims"][0]["claim_id"]), "OWNERSHIP_CLAIM_ID")

    def test_overlap(self):
        self.assert_rejected(lambda d: d["windows"][1].__setitem__("first_cue", 665), "OWNERSHIP_WINDOW_GAP_OR_OVERLAP")

    def test_resume_pointer(self):
        self.assert_rejected(lambda d: d.__setitem__("next_cue", 791), "OWNERSHIP_RESUME_POINTER")

    def test_multiple_atomic_claims_same_cue_allowed(self):
        obj = copy.deepcopy(self.base)
        extra = copy.deepcopy(obj["claims"][0])
        extra["claim_id"] = "SECOND_AT_SAME_CUE"
        obj["claims"].append(extra)
        self.assertEqual(validate_claim_ownership(obj)["multi_claim_anchor_cues"], 1)

if __name__ == "__main__":
    unittest.main()
