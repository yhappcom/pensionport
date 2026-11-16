"""Synthetic tests for actual V154 owner-source integration HOLD."""
import copy
import json
import unittest
from pathlib import Path
from v154_actual_source_integration_hold import (
    V154GateError, audit_v154_sha_only, require_actual_native_host_for_v123,
)

FILE=Path(__file__).with_name("V154_SOURCE_CORRECTION_AND_DISPOSITION_SHA_ONLY.json")


class V154SourceIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.r=json.loads(FILE.read_text(encoding="utf-8"))

    def test_01_actual_one_atom_six_cue_changes_under_hold(self):
        status=audit_v154_sha_only(self.r)
        self.assertEqual(status["remaining_original_unresolved_cues"],102)
        self.assertEqual(status["source_first_no_atom_dispositions"],6)
        self.assertEqual(status["actual_source_bound_atom_corrections"],1)
        self.assertEqual(status["new_native_v6_host_receipts"],0)
        self.assertFalse(status["p0e_go"])

    def test_02_wrong_source_sha_fails(self):
        r=copy.deepcopy(self.r);r["original_sha256"]="0"*64
        with self.assertRaisesRegex(V154GateError,"SOURCE_DRIFT"):
            audit_v154_sha_only(r)

    def test_03_faked_all_108_resolved_fails(self):
        r=copy.deepcopy(self.r);r["remaining_unresolved_cue_count"]=0
        with self.assertRaisesRegex(V154GateError,"FALSE_COUNT"):
            audit_v154_sha_only(r)

    def test_04_faked_host_receipt_fails(self):
        r=copy.deepcopy(self.r);r["post_revision_host_native_receipt_count"]=13
        with self.assertRaisesRegex(V154GateError,"FALSE_COUNT"):
            audit_v154_sha_only(r)

    def test_05_faked_v123_final_approval_fails(self):
        r=copy.deepcopy(self.r);r["v123_final_approved_segments"]=13
        with self.assertRaisesRegex(V154GateError,"FALSE_COUNT"):
            audit_v154_sha_only(r)

    def test_06_faked_v128_publication_fails(self):
        r=copy.deepcopy(self.r);r["v128_parent_publications"]=276
        with self.assertRaisesRegex(V154GateError,"FALSE_COUNT"):
            audit_v154_sha_only(r)

    def test_07_faked_gold_recall_fails(self):
        r=copy.deepcopy(self.r);r["gold_recall_measured"]=True
        with self.assertRaisesRegex(V154GateError,"FALSE_GO"):
            audit_v154_sha_only(r)

    def test_08_faked_no_high_risk_fns_fails(self):
        r=copy.deepcopy(self.r);r["high_risk_fn_zero_proven"]=True
        with self.assertRaisesRegex(V154GateError,"FALSE_GO"):
            audit_v154_sha_only(r)

    def test_09_tampered_private_exchange_pin_fails(self):
        r=copy.deepcopy(self.r);r["V154_B0013_CORRECTED_V6_EXCHANGE_DRAFT_sha256"]="BAD"
        with self.assertRaisesRegex(V154GateError,"PRIVATE_SEGMENT_EXCHANGE_PIN"):
            audit_v154_sha_only(r)

    def test_10_no_actual_native_host_13_replay_not_ready(self):
        with self.assertRaisesRegex(V154GateError,"THIRTEEN_NATIVE_RECEIPTS_MISSING"):
            require_actual_native_host_for_v123(self.r,[])

    def test_11_no_private_ledger_replay_rejected_even_with_13_fake_receipts(self):
        receipts=[{"scope_id":str(i)} for i in range(13)]
        with self.assertRaisesRegex(V154GateError,"PRIVATE_LEDGER_REPLAY_REQUIRED"):
            require_actual_native_host_for_v123(self.r,receipts)

    def test_12_13_fake_receipts_with_fake_snapshots_fail(self):
        receipts=[{"scope_id":str(i),"schema":"IRE_V6_HOST_BATCH_RECEIPT_V1",
                   "is_current":True,"atomic_batch_committed":True,
                   "human_semantic_review_pending":True,
                   "semantic_truth_certified":False,"p0_go":False,
                   "event_sha256":"1"*64,"source_and_proof_model_windows":2}
                  for i in range(13)]
        with self.assertRaisesRegex(V154GateError,"REAL_LEDGER_HEAD_OR_PROOF_MISSING"):
            require_actual_native_host_for_v123(
                self.r,receipts,{"0":{"ledger_head_sha256":"1"*64,"progress":{}}})


if __name__=="__main__":
    unittest.main()
