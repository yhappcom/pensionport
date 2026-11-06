"""V5 #6/#8/#9 unlinked-window source audit regression."""
from pathlib import Path
import unittest
from ire.v5 import extra369_unanchored_window_gate as gate
from ire.v5.advisory_answer_pipeline import answer

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

    def test_live_answer_for_uncovered_nephew_gift(self):
        result=answer(ROOT,"조카 증여 천만원 증여재산공제 적용되나요?")
        cautions=result["extra_three_unanchored_source_cautions"]["items"]
        self.assertIn("V5-GAP-02",[row["review_id"] for row in cautions])
        self.assertIn("1,000만원",result["answer_text"])
        self.assertFalse(result["direct_order_or_personal_recommendation_approved"])

    def test_fx_spread_and_unrelated_queries(self):
        fx=gate.retrieve(ROOT,"환전 우대 100% 기준환율 맞나요?")
        self.assertEqual(fx["items"][0]["review_id"],"V5-GAP-11")
        self.assertIn("수수료",fx["items"][0]["scope_caveat"])
        self.assertEqual(gate.retrieve(ROOT,"영화관 주차요금")["match_count"],0)

if __name__=="__main__":
    unittest.main()
