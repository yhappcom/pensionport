"""Prevent losing the 2026 Art. 118-3 + NTS R009 exception in future research."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class R009PriorYearExceptionNotAutoCredit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((ROOT/"V124_1_R009_PRIOR_TAX_YEAR_CREDIT_EXCEPTION_SHA_ONLY.json").read_text(encoding="utf-8"))
        cls.v124=json.loads((ROOT/"V124_REAL_FINANCE12_PRIMARY_BYTE_RELEVANCE_SHA_ONLY.json").read_text(encoding="utf-8"))
        cls.policy=(ROOT/"V6_CURRENT_CHATGPT_FINAL_APPROVAL_PROTOCOL.md").read_text(encoding="utf-8")
    def test_original_and_prior_docket_consistency(self):
        p=self.p
        self.assertEqual(p["original_source_sha256"],self.v124["source_sha256"])
        self.assertEqual(p["prior_v124_private_zip_sha256"],self.v124["private_archive_sha256"])
        self.assertEqual(p["critical_case_id"],"R009")
        self.assertEqual(p["finance_open"],12)
        self.assertEqual(p["new_p1_knowledge_released"],0)
    def test_exception_requires_request_and_is_not_automatic_isa_credit(self):
        p=self.p
        self.assertTrue(p["exception_current_law_2026_found"])
        self.assertTrue(p["nts_2024_authoritative_written_ruling_found"])
        self.assertTrue(p["uncredited_prior_year_pension_contribution_article118_3_exception_requires_case_review"])
        self.assertFalse(p["rollover_bonus_automatically_repeated"])
    def test_rendered_law_does_not_fake_approved_original_body_or_audio(self):
        p=self.p
        self.assertFalse(p["original_http_bodies_for_new_exception_obtained"])
        self.assertFalse(p["original_speaker_audio_verified"])
        self.assertFalse(p["all_12_finance_claims_formally_approved"])
        self.assertFalse(p["p0_go"])
        for k in ("private_case_correction_sha256","private_v1241_bundle_sha256"):
            self.assertEqual(len(p[k]),64)
            int(p[k],16)
        self.assertIn("V124.1",self.policy)
if __name__=="__main__":
    unittest.main()
