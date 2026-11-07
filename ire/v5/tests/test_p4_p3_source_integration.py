"""Newly reviewed #1 source facts are live education, not a 116 master merge."""
from pathlib import Path
import unittest
from ire.v5 import p4_p3_source_integration as p4
from ire.v5.advisory_answer_pipeline import answer

ROOT=Path(__file__).resolve().parents[3]


class P3P4IntegratedTests(unittest.TestCase):
    def test_29_nodes_and_live_seven_retrievals(self):
        d=p4.audit(ROOT)
        self.assertEqual(d["active_education_nodes"],29)
        self.assertEqual(d["previous_education_nodes"],22)
        self.assertEqual(d["new_education_nodes"],7)
        self.assertEqual(d["source_claim_candidates"],89)
        self.assertEqual(d["new_question_probes_passed"],7)
        self.assertEqual(d["formal_master_merges"],0)

    def test_pension_overgeneralization_has_official_scope_caveats(self):
        a=p4.retrieve(ROOT,"연금 1500 종합과세 강제인가요",limit=29)
        x=next(x for x in a["items"]
               if x["knowledge_id"]=="P3-001-PRIVATE-PENSION-1500-CHOICE")
        self.assertIn("15%",x["statement"])
        self.assertIn("1,500만원",x["statement"])
        self.assertIn("www.nts.go.kr",str(x["official_context_urls"]))
        self.assertFalse(x["formal_financial_fact_approved"])

    def test_unverified_old_insurance_guarantee_is_not_certified(self):
        a=p4.retrieve(ROOT,"옛날 연금저축보험 이전과 최저보증이율 비교",limit=29)
        x=next(x for x in a["items"]
               if x["knowledge_id"]=="P3-001-OLD-PENSION-INSURANCE-TRANSFER-CHECKLIST")
        self.assertIn("증명 전까지",x["statement"])
        self.assertEqual(x["official_context_urls"],[])

    def test_unsafe_new_knowledge_promotion_is_denied(self):
        d=p4.read(ROOT,p4.MANIFEST)
        d["items"][0]["personalized_action_approved"]=True
        with self.assertRaisesRegex(p4.P4IncrementalError,
                                    "P4_UNAPPROVED_OR_INVALID_KNOWLEDGE"):
            p4.load(ROOT,replacement=d)

    def test_new_knowledge_without_real_original_claims_is_denied(self):
        d=p4.read(ROOT,p4.MANIFEST)
        d["items"][0]["source_claim_ids"]=["FV5-P3-9999"]
        with self.assertRaisesRegex(p4.P4IncrementalError,"P4_SOURCE_OR_GRAPH_RELATION"):
            p4.load(ROOT,replacement=d)

    def test_live_p3_answer_retrieves_2026_finance_scope(self):
        a=answer(ROOT,"ISA 50년 손실 이월은 무기한 비과세인가요?")
        r=a["p4_p3_source_education_retrieval"]
        self.assertIn("P3-001-ISA-NETTING-SCOPE-NO-50YEAR-GUARANTEE",
                      [x["knowledge_id"] for x in r["items"]])
        self.assertIn("원본 SRT",a["answer_text"])
        self.assertFalse(a["direct_order_or_personal_recommendation_approved"])

    def test_personal_order_is_still_not_approved(self):
        a=answer(ROOT,"내 계좌에서 주식 전량 매도해줘")
        self.assertEqual(a["p4_p3_source_education_retrieval"]["items"],[])
        self.assertFalse(a["direct_order_or_personal_recommendation_approved"])


if __name__=="__main__": unittest.main()
