"""An analysis request remains answerable without authorizing trades."""
import unittest
from pathlib import Path

from ire.v5.advisory_intent import classify
from ire.v5.advisory_answer_pipeline import answer

ROOT = Path(__file__).resolve().parents[3]


class DecisionVsOrderTests(unittest.TestCase):
    def test_personal_isa_comparison_not_banned_as_trade_order(self):
        query = "내 ISA 만기자금을 연금저축으로 옮기는 게 유리한가요?"
        intent = classify(query)
        self.assertEqual(intent["kind"], "PERSONAL_DECISION_SUPPORT")
        self.assertFalse(intent["order_execution_requested"])
        a = answer(ROOT, query)
        self.assertFalse(a["personal_order_detected"])
        self.assertEqual(a["question_intent"]["kind"], "PERSONAL_DECISION_SUPPORT")
        self.assertIn("대안을 비교", a["answer_text"])
        self.assertFalse(a["direct_order_or_personal_recommendation_approved"])
        self.assertTrue(a["first40_education_retrieval"]["items"])

    def test_asked_to_trade_remains_blocked(self):
        for query in (
            "내 계좌에서 반도체주를 지금 모두 팔아줘",
            "내 ISA 돈을 지금 전량 매도해줘",
            "내 IRP 자금을 즉시 주문 실행해줘",
        ):
            with self.subTest(query=query):
                self.assertEqual(classify(query)["kind"], "ORDER_EXECUTION_REQUEST")
        out = answer(ROOT, "내 계좌에서 반도체주를 지금 모두 팔아줘")
        self.assertTrue(out["personal_order_detected"])
        self.assertIn("전량 매도", out["answer_text"])
        self.assertEqual(out["first40_education_retrieval"]["items"], [])

    def test_guaranteed_return_not_rebranded_analysis(self):
        x = classify("내 IRP 수익은 무조건 보장되나요?")
        self.assertEqual(x["kind"], "GUARANTEED_RETURN_REQUEST")
        self.assertFalse(x["order_execution_authorized"])

    def test_order_and_suitability_approval_always_false(self):
        for q in (
            "내 IRP에서 1000만원 인출할까요?",
            "내 포트폴리오 리밸런싱을 비교해주세요",
            "원금 손실 없이 투자할 수 있나요?",
        ):
            with self.subTest(q=q):
                self.assertFalse(classify(q)["order_execution_authorized"])
                self.assertFalse(classify(q)["personal_investment_suitability_verified"])


if __name__ == "__main__":
    unittest.main()
