"""Source-cue regression: 636 lexical risk signals and 22 scoped source spans."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ire.v5 import first_five_all5129_risk_gate as gate
from ire.v5.advisory_answer_pipeline import answer

ROOT=Path(__file__).resolve().parents[3]


class Original5129RiskGateTests(unittest.TestCase):
    def test_all_5129_source_cues_screened_and_no_fake_atomic_recall(self):
        result=gate.audit(ROOT)
        self.assertEqual(result["source_cues_screened"],5129)
        self.assertEqual(result["source_windows_screened"],288)
        self.assertEqual(result["risk_flagged_source_cues"],636)
        self.assertEqual(result["reviewed_risk_claim_groups"],22)
        self.assertFalse(result["source_spans_private_reopened_this_process"])
        self.assertEqual(result["formal_financial_claim_approvals"],0)
        self.assertFalse(result["full_atomic_claim_recall_independently_proven"])
        self.assertFalse(result["independent_personal_advice_grade_pass"])

    def test_macro_20pct_gdp_not_approved(self):
        r=gate.retrieve(ROOT,"GDP 대비 경상수지 20%는 확정인가요?")
        self.assertEqual(r["items"][0]["review_id"],"FV5-3PASS-015")
        self.assertEqual(r["items"][0]["status"],"OFFICIAL_MACRO_TABLE_OPEN")
        self.assertFalse(r["items"][0]["new_verified_financial_law_fact"])

    def test_cash_deposit_vs_isa_gold_not_collapsed(self):
        r=gate.retrieve(ROOT,"KRX 금현물 세금과 실물 인출시 VAT는?")
        self.assertEqual(r["items"][0]["review_id"],"FV5-3PASS-002")
        self.assertTrue(r["items"][0]["official_context_urls"])

    def test_reverse_mortgage_prior_sale_error_in_live_advice(self):
        r=answer(ROOT,"주택연금 집 팔아야 가입 가능한가요?")
        self.assertIn("집을 먼저",r["answer_text"])
        self.assertEqual(r["first_five_full5129_risk_screen_cautions"]["items"][0]["review_id"],
                         "FV5-3PASS-012")
        self.assertFalse(r["direct_order_or_personal_recommendation_approved"])

    def test_credit_card_tax_stale_2025_scope_in_live_advice(self):
        r=answer(ROOT,"연말정산 신용카드 의무인가요?")
        self.assertIn("총급여",r["answer_text"])
        self.assertIn("FV5-3PASS-020",
                      [x["review_id"] for x in r["first_five_full5129_risk_screen_cautions"]["items"]])
        self.assertFalse(r["direct_order_or_personal_recommendation_approved"])

    def test_irp_deposit_and_all_in_parking_not_general_rules(self):
        r=gate.retrieve(ROOT,"퇴직 IRP 추가납입 불가가 법적 의무인가요?")
        self.assertEqual(r["items"][0]["review_id"],"FV5-3PASS-008")
        self.assertIn("권고",r["items"][0]["caution"])

    def test_unrelated_question_not_contaminated(self):
        self.assertEqual(gate.retrieve(ROOT,"주차장 운영시간")["items"],[])

    def test_nonexistent_original_bytes_do_not_fake_source_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"original.zip"
            with self.assertRaisesRegex(gate.FullCueRiskError,"PRIVATE_SOURCE_NOT_AVAILABLE"):
                gate.audit(ROOT,source_zip=p)
            p.write_bytes(b"fake archive")
            with self.assertRaisesRegex(gate.FullCueRiskError,"ARCHIVE_HASH_CHANGED"):
                gate.audit(ROOT,source_zip=p)

    def test_forged_certification_rejected(self):
        c,r=gate.read_all(ROOT)
        changed=copy.deepcopy(r)
        changed["independent_blind_recall_proven"]=True
        with patch.object(gate,"pinned_json",side_effect=[c,changed]):
            with self.assertRaisesRegex(gate.FullCueRiskError,
                                        "RISK5129_FALSE_FORMAL_APPROVAL"):
                gate.audit(ROOT)

    def test_lexical_scanner_is_bounded_and_reproducible(self):
        flagged,counts=gate.scan_cues(["연금저축 1500만원 6% 보장",
                                         "내일 영화관 갈까요?","주택연금 금리 3%"])
        self.assertEqual(flagged,2)
        self.assertEqual(counts["PERCENT_NUMERIC"],2)
        self.assertEqual(counts["ACCOUNT_TAX_PENSION"],2)


if __name__=="__main__":unittest.main()
