"""V11 end-to-end frontier binding: synthetic source only, no human gold."""
from __future__ import annotations

import copy
import json
import unittest
from unittest.mock import patch

from ire.v6.errors import (IdempotencyConflict, InvalidInput, LedgerCorrupted,
                           QualityNotProven)
from ire.v6.host_batch import MARKER_SCHEMA
from ire.v6.semantic_frontier import source_first_semantic_frontier
from ire.v6.tests import test_host_batch


class HostBatchSemanticFrontierIntegrationTests(unittest.TestCase):
    def setUp(self):
        parent=test_host_batch.HostBatchTests("test_one_command_commits_all_models_and_proofs_atomically")
        parent.setUp()
        self.addCleanup(parent.doCleanups)
        self.fx=parent

    def _expected_frontier(self):
        return source_first_semantic_frontier(self.fx.fx.source,self.fx.fx.exchange)

    def _marker(self):
        con=self.fx.fx.store._connection()
        try:
            r=con.execute("SELECT event_json FROM events WHERE scope_id=? AND command_id=?",
                          ("host_scope","run_0001_seal")).fetchone()
            self.assertIsNotNone(r)
            return json.loads(r["event_json"])["payload"]["review"]
        finally:
            con.close()

    def test_real_batch_path_commits_source_first_review_pin(self):
        f=self._expected_frontier()
        receipt=self.fx.fx.store.submit_host_atomic_batch(**self.fx.args())
        pin=receipt["source_first_semantic_frontier_pin"]
        self.assertEqual(pin["review_case_census_sha256"],f["review_case_census_sha256"])
        self.assertEqual(pin["review_case_count"],f["review_case_count"])
        self.assertEqual(pin["review_cases_by_kind"],f["review_cases_by_kind"])
        self.assertEqual(pin["original_source_sha256"],self.fx.fx.source.source_sha256)
        self.assertGreater(pin["review_case_count"],0)
        self.assertTrue(receipt["human_semantic_review_pending"])
        self.assertFalse(pin["independent_semantic_review_verified"])
        self.assertFalse(receipt["research_complete"])
        self.assertFalse(receipt["p0_go"])
        self.assertTrue(receipt["atomic_batch_committed"])

    def test_marker_is_persisted_under_same_transaction_as_model_and_proof(self):
        receipt=self.fx.fx.store.submit_host_atomic_batch(**self.fx.args())
        marker=self._marker()
        self.assertEqual(marker["schema"],MARKER_SCHEMA)
        self.assertEqual(marker["source_first_semantic_frontier_pin"],
                         receipt["source_first_semantic_frontier_pin"])
        self.assertEqual(marker["bundle_sha256"],receipt["bundle_sha256"])
        self.assertTrue(marker["human_semantic_review_pending"])
        self.assertFalse(marker["engine_quality_certified"])
        snap=self.fx.fx.store.snapshot("host_scope")
        self.assertEqual(snap["ledger_head_sha256"],receipt["event_sha256"])
        self.assertEqual(snap["progress"]["model_windows_recorded"],2)

    def test_idempotent_retry_keeps_same_frontier_and_no_new_events(self):
        first=self.fx.fx.store.submit_host_atomic_batch(**self.fx.args())
        later=self.fx.fx.store.submit_host_atomic_batch(**self.fx.args())
        self.assertTrue(later["idempotent_replay"])
        self.assertEqual(first["bundle_sha256"],later["bundle_sha256"])
        self.assertEqual(first["source_first_semantic_frontier_pin"],
                         later["source_first_semantic_frontier_pin"])
        self.assertEqual(self.fx.fx.store.snapshot("host_scope")["sequence"],
                         self.fx.base["sequence"]+5)

    def test_changed_semantic_frame_same_run_cannot_reuse_previous_receipt(self):
        self.fx.fx.store.submit_host_atomic_batch(**self.fx.args())
        shifted=copy.deepcopy(self.fx.fx.exchange)
        shifted["atoms"][0]["speaker"]="UNKNOWN"
        # Proposed exchange is tied to prior-knowledge proposal checks as well.
        # Any error MUST be fail-closed without adding events to the ledger.
        before=self.fx.fx.store.snapshot("host_scope")
        with self.assertRaises((IdempotencyConflict,InvalidInput,QualityNotProven)):
            self.fx.fx.store.submit_host_atomic_batch(**self.fx.args(exchange=shifted))
        after=self.fx.fx.store.snapshot("host_scope")
        self.assertEqual(before["sequence"],after["sequence"])
        self.assertEqual(before["ledger_head_sha256"],after["ledger_head_sha256"])

    def test_undisposed_qualified_source_does_not_gain_batch_approval(self):
        e=copy.deepcopy(self.fx.fx.exchange)
        # Previous functional guard: explicit financial cue NO_ATOM is blocked
        # before committing any proof event, even if source frontier could mark it.
        e["cue_dispositions"][0].update(disposition="NO_ATOM",claim_ids=[],
                                         note="모델이 주장 없음을 제안")
        e["atoms"].pop(0)
        before=self.fx.fx.store.snapshot("host_scope")
        with self.assertRaises((InvalidInput,QualityNotProven)):
            self.fx.fx.store.submit_host_atomic_batch(**self.fx.args(exchange=e))
        self.assertEqual(before["ledger_head_sha256"],
                         self.fx.fx.store.snapshot("host_scope")["ledger_head_sha256"])

    def test_frontier_invariant_tampering_fails_without_partial_commit(self):
        valid=self._expected_frontier()
        altered=copy.deepcopy(valid)
        altered["review_case_count"]+=1
        with patch("ire.v6.host_batch.source_first_semantic_frontier",
                   return_value=altered):
            with self.assertRaisesRegex(LedgerCorrupted,
                                        "HOST_BATCH_SEMANTIC_FRONTIER_INTEGRITY_DRIFT"):
                self.fx.fx.store.submit_host_atomic_batch(**self.fx.args())
        self.assertEqual(self.fx.base["ledger_head_sha256"],
                         self.fx.fx.store.snapshot("host_scope")["ledger_head_sha256"])

    def test_frontier_output_contains_no_private_source_text(self):
        r=self.fx.fx.store.submit_host_atomic_batch(**self.fx.args())
        data=json.dumps(r,ensure_ascii=False)
        for cue in self.fx.fx.source.cues:
            self.assertNotIn(cue.text,data)
        self.assertNotIn("review_cases",r)
        self.assertFalse(r["independent_gold_recall_measured"])

    def test_source_first_frontier_does_not_authorize_gold_or_knowledge_merge(self):
        result=self.fx.fx.store.submit_host_atomic_batch(**self.fx.args())
        pin=result["source_first_semantic_frontier_pin"]
        self.assertTrue(pin["human_semantic_review_pending"])
        self.assertNotIn("approved",result)
        self.assertFalse(result["semantic_truth_certified"])
        self.assertFalse(result["p0_go"])


if __name__=="__main__":
    unittest.main()
