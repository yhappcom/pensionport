"""P3 actual text construction, citations and safety checks."""
import unittest
from pathlib import Path
from ire.v5 import advisory_answer_pipeline as p3

ROOT=Path(__file__).resolve().parents[3]

class AnswerP3Tests(unittest.TestCase):
    def test_freeform_answer_generated_with_direct_source(self):
        r=p3.answer(ROOT,"연금계좌 세액공제 900만원은 그대로 환급되나요?")
        self.assertIn("P1-PENSION-CREDIT-LIMIT",r["fact_ids"])
        self.assertIn("g.nts.go.kr",r["answer_text"])
        self.assertIn("공제대상",r["answer_text"])
        self.assertFalse(r["direct_order_or_personal_recommendation_approved"])

    def test_mixed_isa_foreign_and_pension_avoid_conflating(self):
        r=p3.answer(ROOT,
            "미국 배당 ETF가 담긴 ISA의 외국원천세와 ISA 연금전환 공제가 같은 규정인가요?")
        self.assertIn("ISA_FOREIGN_DIVIDEND",r["domain_candidates"])
        self.assertIn("ISA_TRANSFER",r["domain_candidates"])
        self.assertIn("출처:",r["answer_text"])

    def test_money_calculated_but_not_ordered(self):
        r=p3.answer(ROOT,"은퇴 후 월 생활비 부족분이 얼마나 남나요?",{
            "kind":"RETIREMENT_GAP","monthly_pension_krw":1200000,
            "other_monthly_income_krw":200000,
            "options":[{"id":"base","monthly_expense_krw":3000000}]})
        self.assertIn("1,600,000원",r["answer_text"])
        self.assertFalse(r["direct_order_or_personal_recommendation_approved"])

    def test_personal_sell_instruction_never_executed(self):
        r=p3.answer(ROOT,"내 계좌에서 반도체주를 지금 모두 팔아줘")
        self.assertTrue(r["personal_order_detected"])
        self.assertIn("전량 매도",r["answer_text"])
        self.assertFalse(r["direct_order_or_personal_recommendation_approved"])

    def test_sure_profit_claim_not_echoed_as_guarantee(self):
        r=p3.answer(ROOT,"CMA 금리가 예금보다 높으니 손실 없이 수익을 보장받나요?")
        self.assertTrue(r["guarantee_claim_detected"])
        self.assertIn("보장으로 답하지 않습니다",r["answer_text"])

    def test_answers_start_with_direct_distinction_not_only_route_ids(self):
        x=p3.answer(ROOT,
            "미국 배당 ETF가 담긴 ISA의 외국원천세와 ISA 연금전환 공제가 같은 규정인가요?")
        self.assertTrue(x["answer_text"].startswith("ISA 만기자금의 연금계좌 이전 공제와 해외배당"))
        self.assertIn("서로 다른 제도",x["answer_text"])
        self.assertNotIn("ISA_FOREIGN_DIVIDEND, ISA_TRANSFER",x["answer_text"])

    def test_pension_refund_not_equated_with_contribution(self):
        x=p3.answer(ROOT,"연금계좌에 900만원 넣으면 전액 환급받나요?")
        self.assertTrue(x["answer_text"].startswith("연금계좌에 납입한 금액을"))
        self.assertIn("동일한 액수로 환급받는 것은 아닙니다",x["answer_text"])

    def test_direct_personal_order_refusal_precedes_all_claims(self):
        x=p3.answer(ROOT,"내 계좌에서 반도체주를 지금 모두 팔아줘")
        self.assertTrue(x["answer_text"].startswith("현재 입력만으로 개인 계좌"))
        self.assertFalse(x["direct_order_or_personal_recommendation_approved"])

    def test_new_45_and_12_results_report_non_blind(self):
        r=p3.audit(ROOT)
        self.assertEqual(r["fresh_chat_authored_questions"],45)
        self.assertEqual(r["answer_examples_generated"],12)
        self.assertEqual(len(r["answer_probe_results"]),12)
        self.assertFalse(r["human_independent_answer_quality_review_completed"])
        self.assertFalse(r["real_portfolio_advice_authorized"])
        self.assertNotEqual(r["product_release_status"],"APPROVED_PERSONAL_ADVICE")

if __name__=="__main__":
    unittest.main()
