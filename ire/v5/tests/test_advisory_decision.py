"""P2 checks real alternatives and prohibits automatic recommendations."""
import unittest
from pathlib import Path
from ire.v5 import advisory_decision as p2

ROOT=Path(__file__).resolve().parents[3]

class DecisionP2(unittest.TestCase):
    def test_all_five_comparisons_are_reproducible(self):
        got=p2.audit(ROOT)
        self.assertEqual(got["conditional_scenario_templates"],4)
        self.assertEqual(got["synthetic_comparison_cases_passed"],5)
        self.assertEqual(got["personal_trade_recommendations_authorized"],0)

    def test_benefit_at_day_70_zero_and_day_35_limited_to_300(self):
        s={"kind":"ISA_TRANSFER","assumed_income_tax_credit_rate":0.15,
           "options":[{"id":"late","transfer_krw":30000000,"days_after_isa_expiry":70},
                      {"id":"early","transfer_krw":30000000,"days_after_isa_expiry":35}]}
        x=p2.compare(ROOT,"ISA 만기 연금 전환 세액공제 조건은?",s)
        self.assertEqual(x["results"][0]["additional_credit_eligible_contribution_krw"],0)
        self.assertEqual(x["results"][1]["additional_credit_eligible_contribution_krw"],3000000)
        self.assertIsNone(x["results"][1]["hypothetical_credit_after_supplied_remaining_tax_cap_krw"])
        self.assertFalse(x["personalized_trade_authorized"])

    def test_wrong_scope_isa_tax_credit_refused(self):
        with self.assertRaisesRegex(p2.DecisionP2Error,"P2_ISA_LAW_NOT_ACTUALLY_RETRIEVED"):
            p2.compare(ROOT,"오늘 보유주식 반도체를 팔까요?",{
                "kind":"ISA_TRANSFER","assumed_income_tax_credit_rate":0.15,
                "options":[{"id":"transfer","transfer_krw":30000000,"days_after_isa_expiry":30}]
            })

    def test_etf_high_distribution_not_equivalent_high_total_return(self):
        s={"kind":"ETF_TOTAL_RETURN","options":[
            {"id":"a","initial_value_krw":1000000,"ending_market_value_krw":950000,
             "cash_distributions_krw":80000,"separately_paid_fees_krw":10000}]}
        x=p2.compare(ROOT,"ETF 배당분배와 총수익 차이?",s)
        self.assertEqual(x["results"][0]["net_total_return_pct_pre_tax"],2.0)
        self.assertFalse(x["future_returns_guaranteed"])

    def test_bad_tax_rate_is_not_accepted(self):
        with self.assertRaisesRegex(p2.DecisionP2Error,"P2_UNVERIFIED_TAX_RATE"):
            p2.compare(ROOT,"ISA 만기 세액공제를 받으려면?",{
                "kind":"ISA_TRANSFER","assumed_income_tax_credit_rate":0.50,
                "options":[{"id":"bad","transfer_krw":30000000,"days_after_isa_expiry":20}]
            })

    def test_negative_portfolio_percent_rejected(self):
        with self.assertRaisesRegex(p2.DecisionP2Error,"P2_INVALID_FINANCIAL_INPUT"):
            p2.compare(ROOT,"주식 목표비중 조정",{
                "kind":"ALLOCATION_DRIFT","target_equity_pct":60,
                "options":[{"id":"bad","current_equity_pct":-10}]
            })

if __name__=="__main__":
    unittest.main()
