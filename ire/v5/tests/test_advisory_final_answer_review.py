"""Final-answer content, not mere labels, must be correct to scoped standard."""
import copy
from pathlib import Path
import unittest
from ire.v5 import advisory_final_answer_review as qa

ROOT=Path(__file__).resolve().parents[3]

class FinalAnswerQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=qa.json.loads((ROOT/qa.CASES).read_text("utf-8"))

    def test_real_final_text_fixes_four_material_defects(self):
        r=qa.run(ROOT)
        self.assertEqual(r["baseline_direct_answers_sufficient"],8)
        self.assertEqual(r["tuned_repaired_answer_cases_passed"],12)
        self.assertEqual(r["post_edit_exploratory_cases_total"],8)
        self.assertFalse(r["factual_judgment_independently_expert_validated"])
        self.assertFalse(r["formal_personal_investment_advice_authorized"])

    def test_direct_answer_required_not_just_technical_labels(self):
        d=copy.deepcopy(self.data)
        d["repaired_cases"][4]["lead"]="ETF_PRODUCT"
        with self.assertRaisesRegex(qa.FinalAnswerReviewError,"FINAL_QA_REPAIRED_ANSWER_DEFECT"):
            qa.run(ROOT,d)

    def test_no_fake_baseline_12_of_12(self):
        d=copy.deepcopy(self.data)
        d["baseline_user_question_directness_sufficient"]=12
        with self.assertRaisesRegex(qa.FinalAnswerReviewError,"FINAL_QA_BASELINE_HISTORY"):
            qa.run(ROOT,d)

    def test_source_claim_required_for_rp_risk(self):
        d=copy.deepcopy(self.data)
        q=next(x for x in d["repaired_cases"] if x["id"]=="Q10")
        q["sources"]=["P1-INVENTED-RP-SOURCE"]
        with self.assertRaisesRegex(qa.FinalAnswerReviewError,"FINAL_QA_REPAIRED_ANSWER_DEFECT"):
            qa.run(ROOT,d)

    def test_risk_clauses_not_just_structure(self):
        d=copy.deepcopy(self.data)
        x=next(x for x in d["repaired_cases"] if x["id"]=="Q12")
        x["terms"].append("손실이 없는 것을 보증합니다")
        with self.assertRaisesRegex(qa.FinalAnswerReviewError,"FINAL_QA_REPAIRED_ANSWER_DEFECT"):
            qa.run(ROOT,d)

    def test_user_requested_order_not_approved(self):
        r=qa.run(ROOT)
        x=next(x for x in r["repaired_cases"] if x["id"]=="Q11")
        self.assertTrue(x["checks"]["no_unapproved_investment_action"])
        self.assertTrue(x["first_sentence"].startswith("현재 입력만으로"))

if __name__=="__main__":
    unittest.main()
