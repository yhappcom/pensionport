"""P3 must consume the P4 integrated graph without citing pending W41..W67."""
from pathlib import Path
import unittest

from ire.v5.advisory_answer_pipeline import answer

ROOT = Path(__file__).resolve().parents[3]


class P4LiveAdvisoryTests(unittest.TestCase):
    def test_prior13_and_first40_are_both_available_in_actual_answer(self):
        out = answer(ROOT, "ISA 만기자금 연금전환 60일 안에 가능한가요?")
        p4 = out["p4_integrated_knowledge_retrieval"]
        ids = {n["knowledge_id"] for n in p4["items"]}
        self.assertIn("EDU-KR-ISA-TO-PENSION-2026-01", ids)
        self.assertIn("V5-001-40-ISA_MATURITY_TO_PENSION", ids)
        self.assertIn("통합 P4 지식 색인", out["answer_text"])
        self.assertEqual(p4["P3_promoted_fact_count"], 0)
        self.assertFalse(p4["master_modified"])

    def test_direct_trade_request_does_not_get_scoped_knowledge(self):
        out = answer(ROOT, "내 ISA 계좌에서 ETF를 지금 모두 매도해줘")
        self.assertTrue(out["personal_order_detected"])
        self.assertEqual(out["p4_integrated_knowledge_retrieval"]["match_count"], 0)
        self.assertFalse(out["direct_order_or_personal_recommendation_approved"])

    def test_analysis_personal_question_is_not_execution(self):
        out = answer(ROOT, "내 ISA 만기자금을 연금저축으로 옮기는 게 유리한가요?")
        self.assertFalse(out["personal_order_detected"])
        self.assertEqual(out["question_intent"]["kind"], "PERSONAL_DECISION_SUPPORT")
        self.assertGreater(out["p4_integrated_knowledge_retrieval"]["match_count"], 0)
        self.assertFalse(out["current_law_fully_verified_in_this_run"])

    def test_unrelated_question_has_no_verified_finance_knowledge(self):
        out = answer(ROOT, "영화관 상영시간과 주차권 안내는 어디인가요?")
        self.assertEqual(out["p4_integrated_knowledge_retrieval"]["match_count"], 0)


if __name__ == "__main__":
    unittest.main()
