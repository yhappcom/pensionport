"""P0 decomposition regression: multiple conceptual routes and no advice."""
import unittest
from pathlib import Path
from ire.v5 import advisory_semantic as p0

ROOT=Path(__file__).resolve().parents[3]

class SemanticP0(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=p0.load_policy(ROOT)

    def test_holdout_has_coverage_without_claiming_new_blind(self):
        out=p0.audit(ROOT)
        self.assertEqual(out["known_prior_holdout_cases"],16)
        self.assertGreaterEqual(out["domain_recall_at_up_to_five"],12)
        self.assertFalse(out["production_financial_advice_validated"])

    def test_combined_isa_tax_and_transfer_does_not_merge_rules(self):
        out=p0.parse("ISA 만기자금을 연금저축으로 옮길 때 미국 배당 외국원천세도 면제되나요?",self.policy)
        self.assertIn("ISA_TRANSFER",out["related_domains"])
        self.assertIn("ISA_FOREIGN_DIVIDEND",out["related_domains"])
        self.assertTrue(out["multi_domain_or_ambiguous"])
        self.assertFalse(out["facts_verified"])

    def test_retirement_pension_shortfall_and_claim_lineage(self):
        out=p0.parse("퇴직 후 생활비 부족분에서 국민연금은 어떻게 반영하나요?",self.policy)
        self.assertIn("RETIREMENT_WITHDRAWAL",out["related_domains"])
        self.assertTrue(out["candidate_claim_ids"])
        self.assertFalse(out["domain_confidence_calibrated"])

    def test_dollar_cash_and_rp_shows_multiple_risks(self):
        out=p0.parse("USD 달러예금과 달러 RP를 안전자산으로 봐도 되나요?",self.policy)
        self.assertIn("FOREIGN_CURRENCY",out["related_domains"])
        self.assertIn("CASH_CMA",out["related_domains"])

    def test_market_breaker_and_rebalancing_retains_both(self):
        out=p0.parse("서킷브레이커가 발생하면 목표비중 매도를 해야 하나요?",self.policy)
        self.assertIn("MARKET_STRESS",out["related_domains"])
        self.assertIn("ALLOCATION",out["related_domains"])

    def test_numbers_are_context_only(self):
        out=p0.parse("ISA 3000만원과 연금저축 500만원을 60일 안에 옮길까요?",self.policy)
        self.assertIn("3000만원",out["numeric_tokens"])
        self.assertIn("500만원",out["numeric_tokens"])
        self.assertIn("60일",out["numeric_tokens"])
        self.assertFalse(out["personal_action_approved"])

    def test_unknown_question_no_fabricated_source(self):
        out=p0.parse("내 계좌 고양이 사료를 사줘요",self.policy)
        self.assertIsNone(out["primary_domain"])
        self.assertEqual(out["candidate_claim_ids"],[])

if __name__=="__main__":
    unittest.main()
