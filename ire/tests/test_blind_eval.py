"""All evaluation data in this suite is entirely synthetic, not human gold."""
from __future__ import annotations

import copy
import unittest

from ire.blind_eval import (
    measure_blind_performance,validate_blind_gold,digest_json,
    FRAME_FIELDS)
from ire.source import sha256
from test_engine import VID,synthetic_srt,annotations


def fixture():
    raw,digest=synthetic_srt()
    predicted=annotations(digest)
    def gold_frame(atom):
        return copy.deepcopy(atom["frame"])
    gold={
        "schema":"IRE_BLIND_GOLD_V1",
        "video_id":VID,
        "source_sha256":digest,
        "reviewers":[
            {"reviewer_id":"fake_rev_a",
             "independent_from_model_attestation":True,
             "source_first_review_sha256":sha256(b"synthetic-reviewer-a")},
            {"reviewer_id":"fake_rev_b",
             "independent_from_model_attestation":True,
             "source_first_review_sha256":sha256(b"synthetic-reviewer-b")}],
        "adjudicator_id":"fake_rev_c",
        "source_only_adjudication":True,
        "claims":[
            {"gold_id":"G00001",
             "proposition":"상품의 계약 조건이 달라지면 비용도 달라질 수 있다.",
             "source_refs":[{"cue_index":1,"quote":"상품 비용은"},
                            {"cue_index":2,"quote":"계약 조건에 따라 달라질 수 있습니다."}],
             "financial_frame":gold_frame(predicted["claims"][0]),
             "financial_importance":"CRITICAL"},
            {"gold_id":"G00002",
             "proposition":"연 0.3% 비용은 단지 가정된 예시다.",
             "source_refs":[{"cue_index":3,"quote":"연간 수수료 0.3%는 예시입니다."}],
             "financial_frame":gold_frame(predicted["claims"][1]),
             "financial_importance":"STANDARD"},
        ]
    }
    def pair(c,g,v="EXACT"):
        return {
            "predicted_claim_id":c,"gold_id":g,"semantic_verdict":v,
            "frame_field_verdicts":{k:"CORRECT" for k in FRAME_FIELDS}}
    mapping={
        "schema":"IRE_BLIND_ALIGNMENT_V1",
        "video_id":VID,
        "source_sha256":digest,
        "sealed_gold_sha256":digest_json(gold),
        "prediction_manifest_sha256":digest_json(predicted),
        "alignment_reviewer_id":"fake_match_a",
        "model_results_hidden_during_gold_creation":True,
        "all_predictions_and_gold_compared":True,
        "pairs":[pair("C00001","G00001"),pair("C00002","G00002")]
    }
    return raw,digest,gold,predicted,mapping


class SyntheticBlindEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.raw,self.digest,self.gold,self.pred,self.match=fixture()

    def measure(self):
        return measure_blind_performance(
            self.raw,self.digest,VID,self.gold,self.pred,self.match)

    def test_strict_recall_precision_and_critical_coverage(self):
        result=self.measure()
        self.assertEqual(result["strict_precision"],1.0)
        self.assertEqual(result["strict_recall"],1.0)
        self.assertEqual(result["critical_recall"],1.0)
        self.assertEqual(result["critical_gold_count"],1)
        self.assertEqual(result["strict_exact_matches"],2)
        self.assertEqual(result["exact_match_frame_accuracy"]["modality"]["accuracy"],1.0)
        self.assertFalse(result["external_human_reviewer_identity_verified"])
        self.assertFalse(result["true_blind_independence_proven"])
        self.assertFalse(result["research_complete"])

    def test_partial_is_not_true_positive(self):
        self.match["pairs"][1]["semantic_verdict"]="PARTIAL"
        result=self.measure()
        self.assertEqual(result["strict_exact_matches"],1)
        self.assertEqual(result["partial_related_pairs"],1)
        self.assertEqual(result["strict_precision"],0.5)
        self.assertEqual(result["strict_recall"],0.5)
        self.assertEqual(result["critical_recall"],1.0)

    def test_no_gold_leakage_or_fabricated_source_quote(self):
        self.gold["claims"][0]["source_refs"][0]["quote"]="이 영상은 연 100% 확정"
        self.match["sealed_gold_sha256"]=digest_json(self.gold)
        with self.assertRaisesRegex(ValueError,"GOLD_UNTRACEABLE_OR_INVENTED_ORIGINAL_QUOTE"):
            self.measure()

    def test_blind_gold_digest_tampering_rejected(self):
        self.gold["claims"][0]["proposition"]="새로운 의미로 멋대로 변경"
        with self.assertRaisesRegex(ValueError,"BLIND_ALIGNMENT_HASH_OR_ATTESTATION_MISMATCH"):
            self.measure()

    def test_model_prediction_digest_drift_rejected(self):
        self.pred["claims"][0]["proposition"]="출처 원문과 의미가 달라질 수도 있다"
        with self.assertRaisesRegex(ValueError,"BLIND_ALIGNMENT_HASH_OR_ATTESTATION_MISMATCH"):
            self.measure()

    def test_gold_needs_two_distinct_source_first_reviewers(self):
        self.gold["reviewers"][1]["reviewer_id"]="fake_rev_a"
        with self.assertRaisesRegex(ValueError,"GOLD_ADJUDICATOR_NOT_ROLE_SEPARATED"):
            self.measure()
        self.gold["reviewers"][1]["reviewer_id"]="fake_rev_b"
        self.gold["reviewers"][0]["independent_from_model_attestation"]=False
        with self.assertRaisesRegex(ValueError,"GOLD_REVIEWER_SOURCE_FIRST_ATTESTATION_MISSING"):
            self.measure()

    def test_model_results_must_be_sealed_before_adjudication(self):
        self.match["model_results_hidden_during_gold_creation"]=False
        with self.assertRaisesRegex(ValueError,"BLIND_ALIGNMENT_HASH_OR_ATTESTATION_MISMATCH"):
            self.measure()

    def test_exact_rejects_critical_condition_error(self):
        self.match["pairs"][0]["frame_field_verdicts"]["conditions"]="INCORRECT"
        with self.assertRaisesRegex(ValueError,"BLIND_EXACT_ATOM_WITH_CORE_FRAME_ERROR"):
            self.measure()

    def test_matching_one_to_one_no_duplicate_claim_matching(self):
        self.match["pairs"].append(copy.deepcopy(self.match["pairs"][0]))
        with self.assertRaisesRegex(ValueError,"BLIND_PAIR_INVALID_ID_OR_DOUBLE_MATCH"):
            self.measure()

    def test_missing_gold_atom_is_a_false_negative(self):
        self.match["pairs"].pop()
        result=self.measure()
        self.assertEqual(result["strict_recall"],0.5)
        self.assertEqual(result["strict_precision"],0.5)
        self.assertTrue(result["recall_wilson_95"]["lower"]<=0.5)
        self.assertTrue(result["recall_wilson_95"]["upper"]>=0.5)

    def test_source_video_digest_mismatch_fails(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_SHA256_MISMATCH"):
            measure_blind_performance(
                self.raw,sha256(b"someone-else's-raw"),VID,
                self.gold,self.pred,self.match)


    def test_zero_predicted_atoms_does_not_become_perfect_score(self):
        self.pred["claims"]=[]
        self.pred["cue_dispositions"]=[
            {"cue_index":index,"status":"NONCLAIM_CANDIDATE",
             "claim_ids":[],
             "reason":"합성 예제에서 금융 명제 누락 여부를 독립 검사 중입니다."}
            for index in range(1,5)]
        self.match["pairs"]=[]
        self.match["prediction_manifest_sha256"]=digest_json(self.pred)
        result=self.measure()
        self.assertEqual(result["gold_atom_count"],2)
        self.assertEqual(result["predicted_atom_count"],0)
        self.assertEqual(result["strict_recall"],0.0)
        self.assertIsNone(result["strict_precision"])
        self.assertEqual(result["unmatched_gold_or_nonexact"],2)
        self.assertFalse(result["research_complete"])

    def test_unadjudicated_guess_match_cannot_be_auto_approved(self):
        self.match["pairs"][0]["semantic_verdict"]="INCORRECT"
        result=self.measure()
        self.assertEqual(result["strict_exact_matches"],1)
        self.assertEqual(result["strict_recall"],0.5)
        self.assertEqual(result["strict_precision"],0.5)
        self.assertEqual(result["critical_recall"],0.0)



if __name__=="__main__":
    unittest.main()
