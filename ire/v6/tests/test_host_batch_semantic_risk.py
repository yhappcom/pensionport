"""V14 source-bound P0-2 semantic-risk triage and transactional host tests."""
from __future__ import annotations

import copy
import json
import unittest
from unittest.mock import patch

from ire.v6.errors import IdempotencyConflict, InvalidInput, LedgerCorrupted
from ire.v6.host_batch import MARKER_SCHEMA
from ire.v6.semantic_risk import audit_semantic_risks
from ire.v6.tests import test_host_batch


class HostSemanticRiskBridgeTests(unittest.TestCase):
    def setUp(self):
        base=test_host_batch.HostBatchTests(
            "test_one_command_commits_all_models_and_proofs_atomically")
        base.setUp()
        self.addCleanup(base.doCleanups)
        self.fx=base

    def _commit(self,**extra):
        return self.fx.fx.store.submit_host_atomic_batch(**self.fx.args(**extra))

    def _seal(self):
        con=self.fx.fx.store._connection()
        try:
            row=con.execute("SELECT event_json FROM events WHERE scope_id=? AND command_id=?",
                ("host_scope","run_0001_seal")).fetchone()
            self.assertIsNotNone(row)
            return json.loads(row["event_json"])["payload"]["review"]
        finally:
            con.close()

    def test_semantic_risk_cases_are_pinned_into_real_batch(self):
        scan=audit_semantic_risks(self.fx.fx.source,self.fx.fx.exchange)
        receipt=self._commit()
        pin=receipt["source_semantic_risk_pin"]
        self.assertEqual(pin["case_census_sha256"],scan["case_census_sha256"])
        self.assertEqual(pin["review_case_count"],scan["review_case_count"])
        self.assertEqual(pin["cases_by_reason"],scan["cases_by_reason"])
        self.assertEqual(pin["original_source_sha256"],self.fx.fx.source.source_sha256)
        self.assertFalse(pin["semantic_entailment_independently_verified"])
        self.assertFalse(receipt["p0_go"])

    def test_original_frontier_remains_bound_and_marker_schema_new(self):
        r=self._commit()
        seal=self._seal()
        self.assertEqual(MARKER_SCHEMA,"IRE_V6_HOST_BATCH_COMMIT_MARKER_V3")
        self.assertEqual(seal["schema"],MARKER_SCHEMA)
        self.assertEqual(seal["source_semantic_risk_pin"],r["source_semantic_risk_pin"])
        self.assertEqual(seal["source_first_semantic_frontier_pin"],
                         r["source_first_semantic_frontier_pin"])
        self.assertTrue(seal["human_semantic_review_pending"])
        self.assertFalse(seal["engine_quality_certified"])

    def test_retry_preserves_same_risk_digest_with_no_more_events(self):
        a=self._commit()
        b=self._commit()
        self.assertTrue(b["idempotent_replay"])
        self.assertEqual(a["source_semantic_risk_pin"],b["source_semantic_risk_pin"])
        self.assertEqual(a["event_sha256"],b["event_sha256"])
        self.assertEqual(self.fx.fx.store.snapshot("host_scope")["sequence"],
                         self.fx.base["sequence"]+5)

    def test_valid_calendar_only_and_invalid_date_rolls_back(self):
        e=copy.deepcopy(self.fx.fx.exchange)
        e["atoms"][0]["as_of"]="2026-02-30"
        with self.assertRaisesRegex(InvalidInput,"INVALID_REAL_CALENDAR_DATE"):
            self._commit(exchange=e)
        self.assertEqual(self.fx.fx.store.snapshot("host_scope")["ledger_head_sha256"],
                         self.fx.base["ledger_head_sha256"])

    def test_tampered_risk_census_never_partially_writes(self):
        report=audit_semantic_risks(self.fx.fx.source,self.fx.fx.exchange)
        bad=copy.deepcopy(report)
        bad["review_case_count"]+=1
        with patch("ire.v6.host_batch.audit_semantic_risks",return_value=bad):
            with self.assertRaisesRegex(LedgerCorrupted,"SEMANTIC_RISK_AUDIT_DRIFT"):
                self._commit()
        self.assertEqual(self.fx.fx.store.snapshot("host_scope")["sequence"],
                         self.fx.base["sequence"])

    def test_model_stance_change_same_command_rejected_without_new_write(self):
        first=self._commit()
        e=copy.deepcopy(self.fx.fx.exchange)
        e["atoms"][0]["speaker"]="UNKNOWN"
        with self.assertRaises((IdempotencyConflict,InvalidInput)):
            self._commit(exchange=e)
        self.assertEqual(self.fx.fx.store.snapshot("host_scope")["ledger_head_sha256"],
                         first["event_sha256"])

    def test_no_source_text_in_risk_receipt_or_ledger_event(self):
        r=self._commit()
        encoded=json.dumps(r,ensure_ascii=False)
        sealed=json.dumps(self._seal(),ensure_ascii=False)
        for cue in self.fx.fx.source.cues:
            self.assertNotIn(cue.text,encoded)
            self.assertNotIn(cue.text,sealed)
        self.assertNotIn("review_cases",r)
        self.assertNotIn("proposition",sealed)

    def test_zero_reported_risks_cannot_claim_independent_review(self):
        r=self._commit()
        self.assertTrue(r["human_semantic_review_pending"])
        self.assertFalse(r["source_semantic_risk_pin"][
            "semantic_entailment_independently_verified"])
        self.assertFalse(r["source_semantic_risk_pin"][
            "financial_law_as_of_verified"])
        self.assertFalse(r["independent_gold_recall_measured"])

    def test_seal_is_source_and_model_scoped_not_standalone_approval(self):
        r=self._commit()
        self.assertEqual(r["atomic_batch_committed"],True)
        self.assertEqual(r["source_semantic_risk_pin"]["original_source_sha256"],
                         self.fx.fx.source.source_sha256)
        self.assertNotEqual(r["source_first_semantic_frontier_pin"][
            "review_case_census_sha256"],
            r["source_semantic_risk_pin"]["case_census_sha256"])
        self.assertFalse(r["research_complete"])


if __name__=="__main__":
    unittest.main()
