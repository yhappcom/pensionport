"""Original #10 short-video 34-cue complete source disposition safety gates."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ire.v5 import video10_all34_cue_gate as gate
from ire.v5.advisory_answer_pipeline import answer

ROOT=Path(__file__).resolve().parents[3]

class Video10Source34Tests(unittest.TestCase):
    def test_exact_34_cues_8_dispositions_no_formal_fact_approval(self):
        x=gate.audit(ROOT)
        self.assertEqual(x["source_cues_dispositioned"],34)
        self.assertEqual(x["source_cue_groups_researched"],8)
        self.assertEqual(x["prior_risk_cases_consistency_checked"],4)
        self.assertEqual(x["private_original_cues_replayed_this_process"],0)
        self.assertEqual(x["new_final_financial_fact_approvals"],0)
        self.assertFalse(x["full_five_video_atomic_recall_certified"])
        self.assertFalse(x["personal_account_withdrawal_action_approved"])

    def test_midwithdrawal_different_by_account(self):
        r=gate.retrieve(ROOT,"IRP 비공제 원금 언제든 꺼낼 수 있나요?")
        self.assertEqual(r["items"][0]["review_id"],"V10-C07")
        self.assertIn("일부인출이 제한",r["items"][0]["scope_caveat"])

    def test_tax_deferral_qualified(self):
        r=gate.retrieve(ROOT,"연금계좌 과세이연 조건은?")
        self.assertEqual(r["items"][0]["review_id"],"V10-C04")
        self.assertEqual(r["items"][0]["disposition"],"CONDITIONAL_TAX_DEFERRAL")

    def test_1500_pension_tax_not_unconditional_low_rate(self):
        r=gate.retrieve(ROOT,"연금저축 1500만원 넘으면 무조건 3.3%인가요?")
        self.assertEqual(r["items"][0]["review_id"],"V10-C06")
        self.assertIn("연간 1500만원",r["items"][0]["scope_caveat"])

    def test_full_short_video_source_p3_answer_connected(self):
        r=answer(ROOT,"연금계좌 과세이연 조건은?")
        self.assertIn("원본 #10",r["answer_text"])
        self.assertEqual(r["video10_all34_original_scope"]["items"][0]["review_id"],"V10-C04")
        self.assertFalse(r["direct_order_or_personal_recommendation_approved"])

    def test_unrelated_topic_not_polluted(self):
        self.assertEqual(gate.retrieve(ROOT,"오늘 맛있는 점심 식당")["items"],[])

    def test_incorrect_private_source_not_misreported(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"source.zip"
            with self.assertRaisesRegex(gate.ShortVideoSourceError,"PRIVATE_SOURCE_ZIP_MISSING"):
                gate.audit(ROOT,p)
            p.write_bytes(b"fake")
            with self.assertRaisesRegex(gate.ShortVideoSourceError,"SOURCE_ARCHIVE_CHANGED"):
                gate.audit(ROOT,p)

    def test_forged_financial_certification_fails(self):
        data=gate.load(ROOT)
        data["current_legal_rules_for_every_taxpayer_approved"]=True
        with patch.object(gate,"load",return_value=data):
            with self.assertRaisesRegex(gate.ShortVideoSourceError,
                                        "SHORT10_UNEARNED_FINANCIAL_APPROVAL"):
                gate.audit(ROOT)

if __name__=="__main__":unittest.main()
