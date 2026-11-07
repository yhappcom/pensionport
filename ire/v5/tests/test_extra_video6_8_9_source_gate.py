"""#6/#8/#9 3,123 owner SRT cues and 36 original-source caution claims."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ire.v5 import extra_video6_8_9_source_gate as gate
from ire.v5.advisory_answer_pipeline import answer

ROOT=Path(__file__).resolve().parents[3]

class ExtraThreeFinanceOriginalTests(unittest.TestCase):
    def test_original_source_window_count_and_careful_approval_levels(self):
        x=gate.audit(ROOT)
        self.assertEqual(x["source_video_numbers"],[6,8,9])
        self.assertEqual(x["original_source_cues"],3123)
        self.assertEqual(x["original_planner_windows"],175)
        self.assertEqual(x["scoped_source_claim_candidates"],36)
        self.assertEqual(x["previous_crossvideo_risk_cases_checked"],9)
        self.assertEqual(x["provisional_crossvideo_concept_relations_checked"],8)
        self.assertFalse(x["private_owner_archive_replayed_this_process"])
        self.assertFalse(x["independent_complete_atomic_recall_certified"])
        self.assertEqual(x["new_formally_approved_financial_law_facts"],0)
        self.assertEqual(x["formal_knowledge_master_edges_approved"],0)

    def test_gift_tax_due_date_is_not_literal_3_months_from_gift_date(self):
        r=gate.retrieve(ROOT,"증여세 증여일부터 3개월로 계산하면 되나요?")
        self.assertEqual(r["items"][0]["claim_id"],"V5X-6-06")
        self.assertIn("달의 말일",r["items"][0]["caveat"])
        self.assertEqual(r["items"][0]["status"],"CURRENT_2026_FILING_STATUTE_CORRECTED")
        self.assertFalse(r["items"][0]["approved_regulatory_fact"])

    def test_child_gift_240million_not_unconditionally_tax_free(self):
        r=gate.retrieve(ROOT,"30년 증여 2억4천은 무조건 비과세인가요?")
        self.assertEqual(r["items"][0]["claim_id"],"V5X-6-11")
        self.assertIn("혼인",r["items"][0]["caveat"])
        self.assertFalse(r["items"][0]["approved_regulatory_fact"])

    def test_770_950_fx_return_calculation(self):
        r=gate.retrieve(ROOT,"엔화 870에서 950 오르면 몇 퍼센트인가요?")
        self.assertEqual(r["items"][0]["claim_id"],"V5X-9-03")
        self.assertIn("9.1954%",r["items"][0]["caveat"])
        self.assertAlmostEqual((950/870-1)*100,9.19540229885,places=5)

    def test_yen_etf_futures_vs_isa_tax(self):
        r=gate.retrieve(ROOT,"엔화 ETF 세금은 일반계좌와 ISA가 같나요?")
        self.assertEqual(r["items"][0]["claim_id"],"V5X-8-01")
        self.assertIn("ISA",r["items"][0]["caveat"])

    def test_late_recorded_yen_fixed_spread_not_global(self):
        r=gate.retrieve(ROOT,"엔화 환전 수수료 1.75%가 고정인가요?")
        self.assertEqual(r["items"][0]["claim_id"],"V5X-9-12")
        self.assertIn("모든 엔화 거래",r["items"][0]["caveat"])

    def test_real_p3_reproduces_new_unmatched_gift_filing_caution(self):
        r=answer(ROOT,"증여세 증여일부터 3개월인가요?")
        self.assertIn("달의 말일",r["answer_text"])
        self.assertIn("V5X-6-06",[
            x["claim_id"] for x in r["extra_three_source_scoped_claims"]["items"]])
        self.assertFalse(r["direct_order_or_personal_recommendation_approved"])

    def test_unrelated_question_not_polluted(self):
        self.assertEqual(gate.retrieve(ROOT,"자동차 타이어 공기압")["items"],[])

    def test_private_original_absence_never_faked(self):
        with tempfile.TemporaryDirectory() as folder:
            src=Path(folder)/"source.zip"
            with self.assertRaisesRegex(gate.ThreeVideoSourceError,
                                        "EXTRA369_ORIGINAL_ZIP_MISSING"):
                gate.audit(ROOT,src)
            src.write_bytes(b"forged private zip")
            with self.assertRaisesRegex(gate.ThreeVideoSourceError,
                                        "EXTRA369_ORIGINAL_ARCHIVE_SHA_CHANGED"):
                gate.audit(ROOT,src)

    def test_tampered_finished_research_flag_rejected(self):
        d=gate.load(ROOT)
        d["fully_independent_blind_atomic_recall_proven"]=True
        with patch.object(gate,"load",return_value=d):
            with self.assertRaisesRegex(gate.ThreeVideoSourceError,
                                        "EXTRA369_FORGED_ATOMIC_OR_LEGAL_APPROVAL"):
                gate.audit(ROOT)

if __name__=="__main__":unittest.main()
