"""Contract checks for a real source-reviewed video and the 116-claim baseline."""
import copy
import json
import unittest
from pathlib import Path

from ire.v5.review_gate import legacy_claim_ids, validate_review, ReviewGateError

ROOT=Path(__file__).resolve().parents[3]
REVIEW=ROOT/"ire/v5/reviews/4TFtEQxSM38_20261104.json"
PRIOR=ROOT/"data/claims.jsonl"


class ReviewGateTests(unittest.TestCase):
    def setUp(self):
        self.review=json.loads(REVIEW.read_text("utf-8"))
        self.prior=legacy_claim_ids(PRIOR)

    def test_real_303_cue_public_review_links_to_legacy_without_promotion(self):
        self.assertGreaterEqual(len(self.prior),100)
        result=validate_review(self.review,self.prior)
        self.assertTrue(result["all_cue_sections_accounted_for"])
        self.assertFalse(result["source_rechecked_with_raw_bytes"])
        self.assertEqual(result["claims_provisional"],10)
        self.assertGreater(result["legacy_claim_candidates_validated"],0)
        self.assertFalse(result["knowledge_merge_approved"])
        self.assertFalse(result["investment_advice_eligible"])
        self.assertEqual(result["financial_facts_independently_approved"],0)

    def test_cue_coverage_gap_cannot_be_reported_complete(self):
        r=copy.deepcopy(self.review)
        r["sections"][3]["from"]+=1
        with self.assertRaisesRegex(ReviewGateError,"SOURCE_CUE_CENSUS_GAP_OR_OVERLAP"):
            validate_review(r,self.prior)

    def test_dangling_prior_claim_is_blocked(self):
        r=copy.deepcopy(self.review)
        r["claims"][0]["prior_claim_candidates"]=["GOMHEE-NEVER-EXISTED"]
        with self.assertRaisesRegex(ReviewGateError,"UNRESOLVED_PRIOR_CLAIM_REFERENCE"):
            validate_review(r,self.prior)

    def test_no_fictitious_independent_advice_approval(self):
        r=copy.deepcopy(self.review)
        r["investment_advice_approved"]=True
        with self.assertRaisesRegex(ReviewGateError,"UNAUTHORIZED_ADVISORY_PROMOTION"):
            validate_review(r,self.prior)

    def test_no_automatic_knowledge_merge(self):
        r=copy.deepcopy(self.review)
        r["claims"][0]["relation_status"]="SAME_AND_MERGED"
        with self.assertRaisesRegex(ReviewGateError,"UNAUTHORIZED_CLAIM_OR_KNOWLEDGE_MERGE"):
            validate_review(r,self.prior)

    def test_raw_source_identity_must_match_when_supplied(self):
        with self.assertRaises(ReviewGateError):
            validate_review(self.review,self.prior,b"not the source")

if __name__=="__main__":
    unittest.main()
