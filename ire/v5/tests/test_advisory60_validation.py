"""Defensive checks for new-question and source-scoped CHAT evidence benchmark."""
import copy
import unittest
from pathlib import Path
from ire.v5 import advisory60_validation as v
from ire.v5 import advisory60

ROOT=Path(__file__).resolve().parents[3]

class Advisory60NewQuestionValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenario=v.read(ROOT,v.SCENARIOS)
        cls.facts=v.read(ROOT,v.FACTS)
        cls.policy=advisory60.load_policy(ROOT)

    def modified(self,scenarios=None,facts=None):
        return v.verify(ROOT,
                        self.scenario if scenarios is None else scenarios,
                        self.facts if facts is None else facts)

    def test_repaired_not_confused_with_untuned_holdout_accuracy(self):
        r=self.modified()
        self.assertEqual(r["baseline_route_correct"],11)
        self.assertEqual(r["repaired_question_route_correct"],20)
        self.assertEqual(r["untuned_holdout_route_correct"],12)
        self.assertEqual(r["untuned_holdout_route_total"],16)
        self.assertEqual(len(r["untuned_holdout_misses"]),4)
        self.assertFalse(r["generative_model_accurate_advisory_rate_measured"])

    def test_sources_checked_in_chat_not_independent_attestation(self):
        r=self.modified()
        self.assertEqual(r["official_page_entries_reviewed_by_chat"],16)
        self.assertEqual(r["chat_authored_narrow_answers_source_checked"],15)
        self.assertFalse(r["current_law_external_source_reopened_by_ci"])
        self.assertEqual(r["trading_and_personal_portfolio_advice_approved"],0)

    def test_numeric_examples_evaluated_not_just_stored(self):
        r=self.modified()
        self.assertEqual(r["arithmetic_examples_checked"],5)
        b=copy.deepcopy(self.facts)
        b["arithmetic_assertions"][0]["expected"]=9000000
        with self.assertRaisesRegex(v.Advisory60ValidationError,
                                    "ADVISORY60_MATH_MISMATCH_V01"):
            self.modified(facts=b)

    def test_source_url_must_be_trusted_exact_host(self):
        b=copy.deepcopy(self.facts)
        b["sources"][0]["url"]="https://nts.go.kr.attack.invalid/retirement"
        with self.assertRaisesRegex(v.Advisory60ValidationError,
                                    "ADVISORY60_FALSE_SOURCE_OR_DOMAIN_CERTIFICATION"):
            self.modified(facts=b)

    def test_unscoped_fake_official_source_reference_rejected(self):
        b=copy.deepcopy(self.facts)
        b["answers"][0]["source_ids"]=["NTS-FAKE"]
        with self.assertRaisesRegex(v.Advisory60ValidationError,
                                    "ADVISORY60_UNVERIFIED_SOURCE_REFERENCE"):
            self.modified(facts=b)

    def test_unearned_blind_certification_not_allowed(self):
        b=copy.deepcopy(self.facts)
        b["independent_blind_human_validation"]=True
        with self.assertRaisesRegex(v.Advisory60ValidationError,
                                    "ADVISORY60_UNEARNED_FINANCIAL_CERTIFICATION"):
            self.modified(facts=b)

    def test_personal_trade_masquerading_as_education_rejected(self):
        b=copy.deepcopy(self.facts)
        b["answers"][4]["personal_trade_or_allocation_approved"]=True
        with self.assertRaisesRegex(v.Advisory60ValidationError,
                                    "ADVISORY60_UNSUPPORTED_ANSWER_APPROVAL"):
            self.modified(facts=b)

    def test_missing_tax_caveat_and_critical_answer_term_rejected(self):
        b=copy.deepcopy(self.facts)
        b["answers"][0]["narrow_chat_answer"]="이 금액은 언제나 돌려받는 돈입니다. " * 8
        with self.assertRaisesRegex(v.Advisory60ValidationError,
                                    "ADVISORY60_ANSWER_REQUIRED_SCOPE_DROPPED"):
            self.modified(facts=b)

    def test_wrongly_labelled_old_corrected_route_is_detected(self):
        b=copy.deepcopy(self.scenario)
        b["repair_set"][0]["expected_route_id"]="ETF_PRODUCT"
        with self.assertRaisesRegex(v.Advisory60ValidationError,
                                    "ADVISORY60_NEW_QUESTION_ROUTE_REGRESSION"):
            self.modified(scenarios=b)

    def test_unknown_personal_intent_does_not_escape_no_route(self):
        x=advisory60.resolve(self.policy,"내 계좌 애완견 간식을 바로 주문해줘",
                             intent="personal_action")
        self.assertEqual(x["decision"],"PERSONAL_ACTION_NO_RESEARCH_ROUTE")
        self.assertFalse(x["personal_action_approved"])

    def test_unknown_guarantee_not_treated_as_no_risk(self):
        x=advisory60.resolve(self.policy,"미상 기기에서 확정 수익을 약속해도 되나요?",
                             intent="guaranteed_return")
        self.assertEqual(x["decision"],
                         "REFUSE_UNSUPPORTED_GUARANTEE_NO_RESEARCH_ROUTE")
        self.assertFalse(x["current_financial_rule_live_verified"])

    def test_foreign_dividend_and_isa_transfer_remain_separate(self):
        x=advisory60.resolve(self.policy,
            "ISA에 담은 미국 배당 ETF에서 해외 원천세가 빠지는 건 ISA 연금전환 공제와 똑같은 건가요?")
        self.assertEqual(x["route_id"],"ISA_FOREIGN_DIVIDEND")
        self.assertNotIn("EDU-KR-ISA-TO-PENSION-2026-01",
                         [n["knowledge_id"] for n in x["education_nodes"]])

    def test_retirement_shortfall_and_personal_amount_not_recommendations(self):
        x=advisory60.resolve(self.policy,
            "월급 320만원, 고정비 240만원이면 처음 투자에 얼마를 써야 하나요?")
        self.assertEqual(x["decision"],
                         "PERSONAL_ACTION_NOT_AUTHORIZED_SHOW_CHECKS")
        self.assertFalse(x["trade_or_amount_recommended"])
        
if __name__=="__main__":
    unittest.main()
