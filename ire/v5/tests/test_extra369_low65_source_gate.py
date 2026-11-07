"""Regression evidence for 65 low-lexical-risk original SRT windows and 19 caution examples."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ire.v5 import extra369_low65_source_gate as gate
from ire.v5.advisory_answer_pipeline import answer

ROOT=Path(__file__).resolve().parents[3]

class Extra369Low65Tests(unittest.TestCase):
    def test_remaining_65_windows_are_scoped_not_atomic_recall(self):
        r=gate.audit(ROOT)
        self.assertEqual(r["source_cues"],3123)
        self.assertEqual(r["source_windows"],175)
        self.assertEqual(r["previous_36_claim_overlapping_windows"],97)
        self.assertEqual(r["previous_13_high_signal_reviews_preserved"],13)
        self.assertEqual(r["additional_low_keyword_windows_semantically_triaged"],65)
        self.assertEqual(r["all_78_previously_unlinked_windows_triaged"],78)
        self.assertEqual(r["untriaged_windows_in_original_78"],0)
        self.assertEqual(r["remaining_atomic_completeness_gaps_in_97_linked_windows"],"UNKNOWN")
        self.assertEqual(r["additional_low_keyword_financial_cautions"],19)
        self.assertFalse(r["source_cue_semantics_independently_blind_recalled"])
        self.assertFalse(r["private_owner_source_reopened_in_this_process"])
        self.assertEqual(r["formal_new_statutory_financial_fact_approvals"],0)
        self.assertEqual(r["strict_master_equivalence_approvals"],0)

    def test_business_owner_financial_asset_diversification(self):
        x=gate.retrieve(ROOT,"사업자는 투자할 필요 없다")
        self.assertEqual(x["items"][0]["caution_id"],"V5-LOWC-01")
        self.assertEqual(x["items"][0]["original_window_id"],"W00010")
        self.assertFalse(x["items"][0]["personal_financial_action_authorized"])

    def test_japan_etf_ticker_1655_not_truncated_165(self):
        x=gate.retrieve(ROOT,"일본 ETF 165 1655 중 어떤 종목인가요?")
        self.assertEqual(x["items"][0]["caution_id"],"V5-LOWC-11")
        self.assertIn("1655",x["items"][0]["scoped_risk"])
        self.assertIn("1557",x["items"][0]["scoped_risk"])
        self.assertTrue(x["items"][0]["official_context_urls"])

    def test_jpx_trading_hour_narrow_context(self):
        x=gate.retrieve(ROOT,"일본 증시 거래시간 언제인가요?")
        self.assertEqual(x["items"][0]["caution_id"],"V5-LOWC-09")
        self.assertIn("15:30",x["items"][0]["scoped_risk"])

    def test_usdjpy_forex_drop_not_quote_percentage(self):
        x=gate.retrieve(ROOT,"달러엔 100 160 반토막인가요?")
        self.assertEqual(x["items"][0]["caution_id"],"V5-LOWC-18")
        self.assertIn("37.5%",x["items"][0]["scoped_risk"])
        self.assertAlmostEqual((1-100/160)*100,37.5)
        self.assertEqual(x["items"][0]["financial_legal_status"],"SOURCE_SCOPED_NOT_FORMAL_B04")

    def test_child_assets_cannot_be_personal_parent_cash_flow(self):
        x=gate.retrieve(ROOT,"자녀 증여 ETF 월배당 용돈")
        self.assertEqual(x["items"][0]["caution_id"],"V5-LOWC-06")
        self.assertIn("실질 소유자",x["items"][0]["scoped_risk"])

    def test_full_p3_presents_new_low_keyword_source_caveat(self):
        r=answer(ROOT,"사업자는 투자할 필요 없다")
        self.assertIn("사업소득",r["answer_text"])
        self.assertEqual(
            r["extra_three_low_keyword_source_cautions"]["items"][0]["caution_id"],
            "V5-LOWC-01")
        self.assertFalse(r["direct_order_or_personal_recommendation_approved"])

    def test_normal_question_no_injection(self):
        self.assertEqual(gate.retrieve(ROOT,"주차장의 출입구 위치")["items"],[])

    def test_without_private_srt_cannot_claim_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"source.zip"
            with self.assertRaisesRegex(gate.LowKeywordSourceError,
                                        "LOW65_OWNER_ORIGINAL_ARCHIVE_MISSING"):
                gate.audit(ROOT,p)
            p.write_bytes(b"not owner archive")
            with self.assertRaisesRegex(gate.LowKeywordSourceError,
                                        "LOW65_OWNER_ORIGINAL_ARCHIVE_CHANGED"):
                gate.audit(ROOT,p)

    def test_forged_independent_blind_review_rejected(self):
        low,caution=gate.load(ROOT)
        low["all_atomic_claims_independently_recalled"]=True
        with patch.object(gate,"pinned_json",side_effect=[low,caution]):
            with self.assertRaisesRegex(gate.LowKeywordSourceError,
                                        "LOW65_UNEARNED_FINANCIAL_RESEARCH_CERTIFICATION"):
                gate.audit(ROOT)

if __name__=="__main__":
    unittest.main()
