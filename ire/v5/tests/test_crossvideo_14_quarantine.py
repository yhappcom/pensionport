"""Cross-video risk warnings can be used; new verified financial facts cannot."""
from pathlib import Path
import unittest
from ire.v5.crossvideo_14_quarantine import audit, retrieve, verify
from ire.v5.advisory_answer_pipeline import answer

ROOT=Path(__file__).resolve().parents[3]

class CrossvideoGuardTests(unittest.TestCase):
    def test_five_actual_new_videos_supply_14_quarantined_source_challenges(self):
        out=audit(ROOT)
        self.assertEqual(out["scoped_risk_cases"],14)
        self.assertEqual(out["live_risk_questions_checked"],5)
        self.assertEqual(out["formal_financial_facts_approved"],0)
        self.assertEqual(out["new_education_nodes_from_unverified_videos"],0)

    def test_short_video_overgeneralization_in_actual_answer(self):
        out=answer(ROOT,"세액공제 안받아도 무조건 연금저축이 유리한가요?")
        x=out["crossvideo_unverified_risk_retrieval"]
        self.assertIn("CV-010-PENSION-ALL-BETTER",
                      [r["case_id"] for r in x["items"]])
        self.assertIn("정식 금융사실 승인 전",out["answer_text"])
        self.assertFalse(out["direct_order_or_personal_recommendation_approved"])

    def test_birth_gift_tax_not_unconditionally_applied(self):
        out=answer(ROOT,"자녀에게 2천만원 증여하면 자동으로 비과세인가요?")
        self.assertIn("과거 10년",out["answer_text"])
        self.assertFalse(out["direct_order_or_personal_recommendation_approved"])

    def test_yen_ten_percent_is_not_guaranteed(self):
        out=retrieve(ROOT,"엔화 10% 수익 확정인가요?")
        self.assertEqual(out["match_count"],1)
        self.assertEqual(out["items"][0]["status"],"HYPOTHESIS_ONLY")
        self.assertFalse(out["positive_legal_or_product_approval"])

    def test_compilation_requires_deduplication(self):
        out=retrieve(ROOT,"구독자사연 몰아보기 독립 검증?")
        self.assertIn("CV-007-COMPILATION",[x["case_id"] for x in out["items"]])

    def test_unrelated_topic_not_contaminated(self):
        self.assertEqual(retrieve(ROOT,"세탁소 영업시간")["match_count"],0)

if __name__=="__main__":unittest.main()
