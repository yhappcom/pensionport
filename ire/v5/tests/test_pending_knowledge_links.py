"""Fail-closed validation for proposed links between new and old research."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
MERGE=ROOT/"ire/v5/merge_candidates/4TFtEQxSM38.json"
REVIEW=ROOT/"ire/v5/reviews/4TFtEQxSM38_20261104.json"
PRIOR=ROOT/"data/claims.jsonl"

class PendingKnowledgeLinkTests(unittest.TestCase):
    def test_full_claim_coverage_with_existing_claim_ids(self):
        merge=json.loads(MERGE.read_text("utf-8"))
        review=json.loads(REVIEW.read_text("utf-8"))
        known={json.loads(line)["claim_id"] for line in PRIOR.read_text("utf-8").splitlines()
               if line.strip()}
        original={c["claim_id"] for c in review["claims"]}
        rows=merge["candidates"]
        self.assertEqual(len(rows),10)
        self.assertEqual(merge["candidate_count"],len(rows))
        self.assertEqual({c["claim_id"] for c in rows},original)
        for c in rows:
            self.assertTrue(c["prior_claim_ids"])
            self.assertTrue(set(c["prior_claim_ids"])<=known)
            self.assertEqual(c["decision"],"OPEN")
            self.assertEqual(c["evidence_for_merge"],"NOT_INDEPENDENTLY_APPROVED")
            self.assertFalse(c["advisory_eligible"])
        self.assertFalse(merge["integrated_into_approved_knowledge"])
        self.assertEqual(merge["independently_approved_financial_facts"],0)
        self.assertFalse(merge["investment_advice_approved"])

    def test_time_scope_and_audio_risks_explicit(self):
        merge=json.loads(MERGE.read_text("utf-8"))
        types={x["claim_id"].split("-")[-1]:x["relationship_proposal"]
               for x in merge["candidates"]}
        self.assertEqual(types["C07"],"OPEN_TIME_DEPENDENT")
        self.assertEqual(types["C10"],"OPEN_ASR")

if __name__=="__main__":
    unittest.main()
