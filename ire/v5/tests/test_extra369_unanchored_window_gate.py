"""V5 #6/#8/#9 unlinked-window source audit regression."""
from pathlib import Path
import unittest
from ire.v5 import extra369_unanchored_window_gate as gate

ROOT=Path(__file__).resolve().parents[3]

class Extra369GapTests(unittest.TestCase):
    def test_window_counts(self):
        d=gate.audit(ROOT)
        self.assertEqual(d["source_windows"],175)
        self.assertEqual(d["windows_directly_anchored_by_prior36"],97)
        self.assertEqual(d["windows_not_directly_anchored_by_prior36"],78)
        self.assertEqual(d["unlinked_high_signal_windows_reviewed"],13)
        self.assertEqual(d["lower_signal_or_context_unlinked_windows_still_open"],65)
        self.assertFalse(d["strict_new_claim_recall_certified"])

    def test_nephew_gift_scope(self):
        d=gate.retrieve(ROOT,"삼촌 조카 1천만원 증여 되나요?")
        self.assertEqual(d["items"][0]["review_id"],"V5-GAP-02")
        self.assertIn("10년",d["items"][0]["scope_caveat"])
        self.assertFalse(d["items"][0]["official_law_fact_finalized"])

if __name__=="__main__":
    unittest.main()
