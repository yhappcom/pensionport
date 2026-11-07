"""Cue-level source coverage audit for 97 already claim-linked #6/#8/#9 windows."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ire.v5 import extra369_linked97_cue_gap_gate as gate
from ire.v5.advisory_answer_pipeline import answer

ROOT=Path(__file__).resolve().parents[3]

class Linked97PartialCuesTests(unittest.TestCase):
    def test_506_residual_cues_not_called_missing_atomic_claims(self):
        d=gate.audit(ROOT)
        self.assertEqual(d["claim_linked_windows"],97)
        self.assertEqual(d["unanchored_cues_within_linked_windows"],506)
        self.assertEqual(d["linked_windows_containing_unanchored_cues"],53)
        self.assertEqual(d["linked_windows_with_no_cue_gap"],44)
        self.assertEqual(d["lexical_risk_high_windows_within_partial53"],9)
        self.assertEqual(d["selected_source_claim_candidates"],36)
        self.assertFalse(d["independently_blind_atom_recall_certified"])
        self.assertFalse(d["all_506_residual_cue_positions_are_missing_atomic_claims"])
        self.assertEqual(d["new_strict_formal_financial_claim_approvals"],0)

    def test_periodic_gift_3pct_discount_not_automatic_tax_exemption(self):
        r=gate.retrieve(ROOT,"적립식 증여 3% 할인 신고하면 세금은 없나요?")
        self.assertEqual(r["items"][0]["review_id"],"V5-PART-02")
        self.assertIn("연 3%",r["items"][0]["scope_caveat"])
        self.assertIn("신고기간",r["items"][0]["scope_caveat"])
        self.assertFalse(r["items"][0]["personal_financial_order_authorized"])

    def test_usdjpy_cash_vs_stock_risk(self):
        r=gate.retrieve(ROOT,"달러 현금 미국 주식 차이")
        self.assertEqual(r["items"][0]["review_id"],"V5-PART-03")
        self.assertIn("주가",r["items"][0]["scope_caveat"])

    def test_travel_currency_cash_can_have_fx_gain(self):
        r=gate.retrieve(ROOT,"엔화 현금 환차익")
        self.assertEqual(r["items"][0]["review_id"],"V5-PART-05")
        self.assertIn("환차손익",r["items"][0]["scope_caveat"])

    def test_model_30year_not_guaranteed(self):
        r=gate.retrieve(ROOT,"30년 투자 수익 원금 초과")
        self.assertEqual(r["items"][0]["review_id"],"V5-PART-01")
        self.assertIn("보장",r["items"][0]["scope_caveat"])

    def test_live_p3_answer_reflects_unanchored_cue_context(self):
        r=answer(ROOT,"적립식 증여 3% 할인 신고하면 세금은 없나요?")
        self.assertEqual(
            r["extra_three_linked97_cue_residual_cautions"]["items"][0]["review_id"],
            "V5-PART-02")
        self.assertIn("신고기간",r["answer_text"])
        self.assertFalse(r["direct_order_or_personal_recommendation_approved"])

    def test_unrelated_question_no_caution(self):
        self.assertEqual(gate.retrieve(ROOT,"문화예술 공연 관람")["items"],[])

    def test_missing_original_cannot_claim_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"source.zip"
            with self.assertRaisesRegex(gate.LinkedPartialCueError,
                                        "LINKED97_PRIVATE_ZIP_MISSING"):
                gate.audit(ROOT,p)
            p.write_bytes(b"not source")
            with self.assertRaisesRegex(gate.LinkedPartialCueError,
                                        "LINKED97_PRIVATE_ARCHIVE_CHANGED"):
                gate.audit(ROOT,p)

    def test_forged_atomic_perfection_rejected(self):
        d=gate.read(ROOT)
        d["independent_complete_claim_recall_proven"]=True
        with patch.object(gate,"read",return_value=d):
            with self.assertRaisesRegex(gate.LinkedPartialCueError,
                                        "LINKED97_UNEARNED_ATOMIC_CLAIM_COMPLETENESS"):
                gate.audit(ROOT)

if __name__=="__main__":
    unittest.main()
