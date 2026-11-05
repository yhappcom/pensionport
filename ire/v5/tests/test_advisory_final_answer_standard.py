"""Adversarial grading tests based on actual answer content, not routing alone."""
import copy
import unittest
from pathlib import Path
from ire.v5 import advisory_final_answer_standard as g
from ire.v5.advisory_answer_pipeline import answer

ROOT=Path(__file__).resolve().parents[3]

class FinalAnswerRubricV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=g.json.loads((ROOT/g.CONTRACT).read_text("utf-8"))
        cls.cases={x["id"]:x for x in cls.contract["repaired_cases"]}

    def mutate(self,id,fn):
        case=self.cases[id]
        output=copy.deepcopy(answer(ROOT,case["question"],case.get("scenario")))
        fn(output)
        return g.score_case(ROOT,case,output)

    def test_full_answers_rubric_with_original_8_of_12_baseline(self):
        result=g.run(ROOT)
        self.assertEqual(result["baseline_actual_direct_answers"],8)
        self.assertEqual(result["exposed_repaired_answers_passed"],12)
        self.assertEqual(result["rubric_pass_threshold"],90)
        self.assertFalse(result["blind_independent_financial_judgment"])
        self.assertFalse(result["production_personal_advice_approved"])

    def test_fake_numeric_benefit_is_hard_failure(self):
        r=self.mutate("Q01",lambda x:x["numeric_comparison"]["results"][0].update(
            hypothetical_income_tax_credit_before_tax_cap_krw=9000000))
        self.assertFalse(r["accepted"])
        self.assertIn("ISA_HYPOTHETICAL_CREDIT_WRONG",r["hard_failures"])

    def test_wrong_etf_comparison_rank_is_hard_failure(self):
        def corrupt(x):
            x["answer_text"]=x["answer_text"].replace("beta 대안의 세전 총수익률 3.50%",
                                                       "alpha 대안의 세전 총수익률 3.50%")
        r=self.mutate("Q07",corrupt)
        self.assertFalse(r["accepted"])
        self.assertIn("RANKED_OPTION_COMPARISON_MISSING_OR_WRONG",r["hard_failures"])

    def test_missing_direct_conclusion_rejected_despite_all_urls(self):
        r=self.mutate("Q05",lambda x:x.update(answer_text="질문에서 분리한 판단 영역은 ETF입니다.\n"+x["answer_text"]))
        self.assertFalse(r["accepted"])
        self.assertIn("NO_DIRECT_CONCLUSION",r["hard_failures"])

    def test_fabricated_official_source_id_is_hard_failure(self):
        r=self.mutate("Q10",lambda x:x["fact_ids"].append("P1-NOT-REAL"))
        self.assertFalse(r["accepted"])
        self.assertIn("UNTRACEABLE_OR_WRONG_AUTHORITY",r["hard_failures"])

    def test_personal_trade_instruction_never_accepted(self):
        r=self.mutate("Q11",lambda x:x.update(answer_text=x["answer_text"]+"\n지금 전량 매도하세요"))
        self.assertFalse(r["accepted"])
        self.assertIn("UNAUTHORIZED_ACTION_OR_GUARANTEE",r["hard_failures"])

    def test_claiming_full_rule_verification_fails(self):
        r=self.mutate("Q03",lambda x:x.update(current_law_fully_verified_in_this_run=True))
        self.assertFalse(r["accepted"])
        self.assertIn("UNSUPPORTED_CURRENT_FACT_CERTIFICATION",r["hard_failures"])

    def test_removing_critical_conditions_fails(self):
        r=self.mutate("Q12",lambda x:x.update(answer_text=x["answer_text"].replace("예외:","빠짐:")))
        self.assertFalse(r["accepted"])
        self.assertIn("UNTRACEABLE_OR_WRONG_AUTHORITY",r["hard_failures"])

if __name__=="__main__":
    unittest.main()
