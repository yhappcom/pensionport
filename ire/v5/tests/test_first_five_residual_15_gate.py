"""Regression: original #2~#5 research gaps remain quarantined and queryable."""
import copy
from pathlib import Path
import tempfile
import unittest

from ire.v5 import first_five_residual_15_gate as gate
from ire.v5.advisory_answer_pipeline import answer

ROOT=Path(__file__).resolve().parents[3]


class FirstFiveResidual15Tests(unittest.TestCase):
    def test_real_source_span_and_prior_ledger_relationships(self):
        x=gate.audit(ROOT)
        self.assertEqual(x["reviewed_original_srt_spans"],15)
        self.assertEqual(x["previous_68_and_237_ledger_related_source_spans"],13)
        self.assertEqual(x["new_direct_source_anchor_gaps_for_adjudication"],2)
        self.assertEqual(x["source_audio_number_discrepancies_open"],1)
        self.assertEqual(x["live_scoped_question_probes_passed"],5)
        self.assertFalse(x["private_owner_source_zip_replayed_in_this_process"])
        self.assertFalse(x["full_first_five_atomic_recall_independently_verified"])
        self.assertEqual(x["formal_financial_fact_promotions"],0)

    def test_ambiguous_asr_yield_not_released_as_89_percent(self):
        r=gate.retrieve(ROOT,"89% 배당률이 맞나요?")
        self.assertEqual(r["items"][0]["review_id"],"FV5-RES-011")
        self.assertIn("원음",r["items"][0]["scope_caveat"])
        self.assertFalse(r["items"][0]["formal_financial_fact_approved"])

    def test_fee_overgeneralization_appears_in_actual_advice(self):
        r=answer(ROOT,"증권사 IRP 수수료 0원인가요?")
        x=r["first_five_residual_15_scoped_cautions"]
        self.assertIn("FV5-RES-006",[row["review_id"] for row in x["items"]])
        self.assertIn("수수료",r["answer_text"])
        self.assertIn("원본 자막의 고위험 발언 대조",r["answer_text"])
        self.assertFalse(r["direct_order_or_personal_recommendation_approved"])

    def test_irp_1man_is_not_approved_as_universal_legal_rule(self):
        r=answer(ROOT,"IRP 1만원 연금개시가 의무인가요?")
        x=r["first_five_residual_15_scoped_cautions"]["items"]
        self.assertTrue(any(v["review_id"]=="FV5-RES-007" for v in x))
        self.assertIn("법적 근거는 확보하지 못했다",r["answer_text"])

    def test_employer_stock_correlation_caution(self):
        r=answer(ROOT,"재직 회사 주식 매수 괜찮을까요?")
        self.assertIn("동반위험",r["answer_text"])
        self.assertIn("FV5-RES-014",[
            v["review_id"] for v in r["first_five_residual_15_scoped_cautions"]["items"]])

    def test_unrelated_question_not_contaminated(self):
        r=gate.retrieve(ROOT,"오늘의 기상정보 안내")
        self.assertEqual(r["items"],[])

    def test_falsely_promoting_irp_minimum_fails(self):
        d=gate.from_json(ROOT,gate.LEDGER)
        d["items"][6]["legal_fact_or_product_terms_formally_approved"]=True
        with self.assertRaisesRegex(gate.ResidualReviewError,
                                    "RES15_BAD_CUE_BOUNDARY_OR_FORGED_APPROVAL"):
            gate.verify(ROOT,replacement=d)

    def test_manipulated_prior_anchor_is_rejected(self):
        d=gate.from_json(ROOT,gate.LEDGER)
        d["items"][0]["prior_candidate_ids"]=["FV5-A001"]
        with self.assertRaisesRegex(gate.ResidualReviewError,
                                    "RES15_PRIOR_68_PROPOSITION_NOT_QUALIFIED"):
            gate.verify(ROOT,replacement=d)

    def test_unavailable_private_archive_is_not_falsely_replayed(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"source.zip"
            with self.assertRaisesRegex(gate.ResidualReviewError,
                                        "RES15_ORIGINAL_ZIP_MISSING"):
                gate.verify(ROOT,source_zip=p)
            p.write_bytes(b"fake")
            with self.assertRaisesRegex(gate.ResidualReviewError,
                                        "RES15_ORIGINAL_ARCHIVE_HASH_DIFFERENT"):
                gate.verify(ROOT,source_zip=p)


if __name__=="__main__": unittest.main()
