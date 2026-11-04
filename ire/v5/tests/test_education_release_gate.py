"""Five source approvals form four education entries, not five advisor approvals."""
import copy
import unittest
from pathlib import Path
from ire.v5.education_release_gate import verify,read,EducationReleaseError

ROOT=Path(__file__).resolve().parents[3]
ITEMS=ROOT/"ire/v5/advisory_knowledge/deduplicated_educational_knowledge_20261104.json"

class EducationReleaseTests(unittest.TestCase):
    def setUp(self):
        self.data=read(ITEMS)

    def test_five_source_cases_merge_to_four_unique_educational_facts(self):
        actual=verify(ROOT)
        self.assertEqual(actual["evidence_supported_source_cases"],5)
        self.assertEqual(actual["deduplicated_education_facts"],4)
        self.assertEqual(actual["excluded_non_education_cases"],5)
        self.assertFalse(actual["formal_financial_advice_go"])
        self.assertFalse(actual["independent_human_blind_grade_present"])

    def test_uncertain_irp_rule_cannot_be_promoted_as_education_approved(self):
        o=copy.deepcopy(self.data)
        o["entries"][0]["source_audit_ids"].append("P06_IRP_70PCT")
        with self.assertRaisesRegex(EducationReleaseError,"EDUCATION_BLOCKED_CLAIM_PROMOTED"):
            verify(ROOT,o)

    def test_missing_video_source_from_dedup_is_rejected(self):
        o=copy.deepcopy(self.data)
        o["entries"][1]["source_audit_ids"]=["P03_ISA_PENSION_TRANSFER"]
        with self.assertRaises(EducationReleaseError):
            verify(ROOT,o)

    def test_fake_personal_advice_approval_rejected(self):
        o=copy.deepcopy(self.data)
        o["entries"][0]["personalized_advice_approved"]=True
        with self.assertRaisesRegex(EducationReleaseError,"EDUCATION_FAKE_BLIND_OR_LEGAL_APPROVAL"):
            verify(ROOT,o)

    def test_unsafe_pension_inflation_rejected(self):
        o=copy.deepcopy(self.data)
        o["entries"][2]["critical_qualification"]="모든 인출금액이 연간 1500만원을 넘으면 예외 없이 계좌 인출이 법적으로 금지된다고 단정한다."
        with self.assertRaisesRegex(EducationReleaseError,"EDUCATION_PENSION_TAX_VS_WITHDRAWAL_CONFUSED"):
            verify(ROOT,o)
