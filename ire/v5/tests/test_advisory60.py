"""Adversarial policy/coverage checks; not independent human answer scoring."""
from __future__ import annotations
import copy
import unittest
from pathlib import Path
from ire.v5 import advisory60 as a

ROOT=Path(__file__).resolve().parents[3]

class Advisory60Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=a.load_policy(ROOT)

    def test_60_legacy_claims_are_integrated_without_fact_approval(self):
        got=a.audit(ROOT)
        self.assertEqual(got["legacy_claims_traced"],60)
        self.assertEqual(got["decision_domains"],15)
        self.assertEqual(got["question_scenarios_routed"],20)
        self.assertEqual(got["legacy_claims_promoted_to_new_financial_fact"],0)
        self.assertFalse(got["actual_model_advisory_answer_accuracy_test"])
        self.assertFalse(got["personalized_financial_trade_authorized"])

    def test_dynamic_question_recovers_source_and_decision_structure(self):
        x=a.resolve(self.policy,"연금저축 세액공제와 비공제원금 차이가 무엇인가요")
        self.assertEqual(x["route_id"],"PENSION_TAX")
        self.assertIn("GOMHEE-C42",x["source_claim_ids"])
        self.assertEqual(len(x["questions_to_resolve"]),3)
        self.assertIn("EDU-KR-PENSION-CREDIT-600-900",
                      [x["knowledge_id"] for x in x["education_nodes"]])
        self.assertFalse(x["current_financial_rule_live_verified"])
        self.assertFalse(x["personal_action_approved"])

    def test_isa_foreign_tax_is_not_same_as_isa_transfer(self):
        x=a.resolve(self.policy,"ISA 미국배당 외국납부세액 처리는 어떻게 되나요")
        self.assertEqual(x["route_id"],"ISA_FOREIGN_DIVIDEND")
        self.assertIn("GOMHEE-C33",x["source_claim_ids"])
        self.assertNotIn("EDU-KR-ISA-TO-PENSION-2026-01",
                         [x["knowledge_id"] for x in x["education_nodes"]])

    def test_asset_allocation_is_not_dca_arithmetic_proof(self):
        x=a.resolve(self.policy,"자산배분 목표비중과 리밸런싱 방법")
        self.assertIn("GOMHEE-C52",x["source_claim_ids"])
        self.assertNotIn("EDU-GENERAL-DCA-ARITH-01",
                         [x["knowledge_id"] for x in x["education_nodes"]])

    def test_8pct_withdrawal_cannot_be_called_safe(self):
        x=a.resolve(self.policy,"커버드콜 8% 인출률은 안전한가요")
        self.assertEqual(x["route_id"],"RETIREMENT_WITHDRAWAL")
        self.assertIn("8%",x["critical_limit"])
        self.assertIn("안전인출률",x["critical_limit"])
        self.assertFalse(x["personal_action_approved"])

    def test_personal_portfolio_instruction_fails_closed(self):
        x=a.resolve(self.policy,"내 포트폴리오 목표비중 추천해줘")
        self.assertEqual(x["decision"],"PERSONAL_ACTION_NOT_AUTHORIZED_SHOW_CHECKS")
        self.assertFalse(x["trade_or_amount_recommended"])

    def test_guaranteed_profits_refused(self):
        x=a.resolve(self.policy,"CMA 비상자금 원금 보장 무조건 수익")
        self.assertEqual(x["decision"],"REFUSE_GUARANTEED_RETURN_AND_SHOW_FRAMEWORK")

    def test_new_first_five_atomic_source_evidence_is_provisional(self):
        x=a.resolve(self.policy,"연금 1500 인출상한 세금")
        self.assertTrue(any(z["id"]=="FV5-A007" for z in x["first_five_atomic_source_evidence"]))
        self.assertTrue(all(z["personalized_trade_action_approved"] is False
                            for z in x["first_five_atomic_source_evidence"]))
        self.assertFalse(x["personal_action_approved"])
        y=a.resolve(self.policy,"내일 영화관 상영 일정")
        self.assertEqual(y["first_five_atomic_source_evidence"],[])

    def test_unknown_topic_no_unsupported_advice(self):
        x=a.resolve(self.policy,"이번 주말 영화 추천")
        self.assertEqual(x["decision"],"NO_SUPPORTED_RESEARCH_ROUTE")
        self.assertEqual(x["source_claim_ids"],[])

    def test_nonbaseline_date_fails_as_current_law(self):
        with self.assertRaisesRegex(a.Advisory60Error,"HISTORICAL_BASELINE"):
            a.resolve(self.policy,"IRP 중도인출 설명",as_of="2027-05-05")

    def test_changed_catalog_cannot_promote_personal_advice(self):
        catalog=a.read(ROOT,a.CATALOG)
        d=copy.deepcopy(catalog)
        d["approved_personal_advice_items"]=1
        with self.assertRaisesRegex(a.Advisory60Error,"NO_UNEARNED"):
            a.load_policy(ROOT,d)

    def test_changed_catalog_cannot_omit_claim(self):
        catalog=a.read(ROOT,a.CATALOG)
        d=copy.deepcopy(catalog)
        for x in d["routes"]:
            x["claim_ids"]=[z for z in x["claim_ids"] if z!="GOMHEE-C60"]
        with self.assertRaisesRegex(a.Advisory60Error,"COVERAGE_GAP"):
            a.load_policy(ROOT,d)

    def test_catalog_cannot_link_fabricated_education_node(self):
        catalog=a.read(ROOT,a.CATALOG)
        d=copy.deepcopy(catalog)
        d["routes"][0]["education_node_ids"].append("EDU-FAKE-999")
        with self.assertRaisesRegex(a.Advisory60Error,"ROUTE_OR_LIMIT"):
            a.load_policy(ROOT,d)

    def test_per_claim_source_statuses_not_falsified(self):
        got=a.resolve(self.policy,"CMA 발행어음 RP 중 비상자금에 적합한지")
        for src in got["sources"]:
            self.assertFalse(src["new_financial_fact_approved"])
            self.assertTrue(src["unverified_original_full_transcript_this_batch"])

    def test_scenarios_are_not_independent_validation(self):
        suite=a.read(ROOT,a.CASES)
        self.assertEqual(suite["authorship"],"CHATGPT_AUTHORED_NOT_INDEPENDENT_BLIND_GOLD")
        self.assertFalse(suite["claims_about_model_answer_accuracy"])

if __name__=="__main__":
    unittest.main()
