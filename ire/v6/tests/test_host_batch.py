"""All-or-nothing host model/proof persistence; no model API or fake GO."""
from __future__ import annotations
import copy
import unittest

from ire.v6.errors import ConcurrentHeadChanged, InvalidInput, QualityNotProven


class HostBatchTests(unittest.TestCase):
    def setUp(self):
        from ire.v6.tests.test_prior_knowledge import PriorKnowledgeTests
        parent=PriorKnowledgeTests(methodName="test_116_and_p4_29_are_replayed_without_approval")
        parent.setUp()
        self.addCleanup(parent.doCleanups)
        self.fx=parent.fx
        self.knowledge=parent.inputs
        self.owner,self.pin=self.fx.attest()
        self.base=self.fx.store.snapshot("host_scope")
        self.models={}
        self.reviews={}
        for wid,_,_ in self.fx.source.primary_windows:
            claims=[]
            for atom in self.fx.exchange["atoms"]:
                if atom["owner_window_id"] != wid:
                    continue
                indices=[r["cue_index"] for r in atom["source_refs"]]
                claims.append({"claim_id":atom["claim_id"],
                               "proposition":atom["proposition"],
                               "kind":atom["kind"],
                               "owner_window_id":wid,
                               "source_refs":atom["source_refs"],
                               "context_first_cue":indices[0],
                               "context_last_cue":indices[-1]})
            self.models[wid]={"schema":"IRE_V6_ATOMIC_MODEL_V1","claims":claims}
            self.reviews[wid]={"schema":"IRE_V6_STRUCTURAL_REVIEW_V1",
                               "review_scope":"SOURCE_ANCHORS_ONLY",
                               "reviewed_claim_ids":sorted(c["claim_id"] for c in claims),
                               "independent_gold_verified":False}

    def args(self, **updates):
        d=dict(scope_id="host_scope",run_id="run_0001",
               expected_head=self.base["ledger_head_sha256"],
               raw=self.fx.raw,manifest=self.fx.manifest,
               inventory_bytes=self.owner,expected_inventory_sha256=self.pin,
               exchange=self.fx.exchange,knowledge=self.knowledge,
               window_models=self.models,window_reviews=self.reviews)
        d.update(updates)
        return d

    def test_one_command_commits_all_models_and_proofs_atomically(self):
        receipt=self.fx.store.submit_host_atomic_batch(**self.args())
        self.assertTrue(receipt["atomic_batch_committed"])
        self.assertFalse(receipt["research_complete"])
        self.assertEqual(receipt["source_and_proof_model_windows"],2)
        snap=self.fx.store.snapshot("host_scope")
        self.assertEqual(snap["progress"]["model_windows_recorded"],2)
        self.assertEqual(snap["progress"]["current_revision_structural_proof_records"],2)
        self.assertFalse(snap["progress"]["engine_quality_certified"])
        self.assertEqual(snap["ledger_head_sha256"],receipt["event_sha256"])

    def test_exact_request_is_idempotent_and_no_extra_events(self):
        first=self.fx.store.submit_host_atomic_batch(**self.args())
        second=self.fx.store.submit_host_atomic_batch(**self.args())
        self.assertTrue(second["idempotent_replay"])
        self.assertTrue(second["is_current"])
        self.assertEqual(first["event_sha256"],second["event_sha256"])
        self.assertEqual(self.fx.store.snapshot("host_scope")["sequence"],
                         self.base["sequence"]+5)

    def test_changed_request_same_run_id_rejected(self):
        self.fx.store.submit_host_atomic_batch(**self.args())
        changed=copy.deepcopy(self.models)
        changed["W00001"]["claims"][0]["proposition"]="완전히 다른 30% 신규 주장"
        with self.assertRaises(InvalidInput):
            self.fx.store.submit_host_atomic_batch(**self.args(window_models=changed))

    def test_missing_window_and_forged_quote_block_before_any_write(self):
        for mutation in ("missing","quote"):
            models=copy.deepcopy(self.models)
            if mutation=="missing":models.pop("W00002")
            else:models["W00001"]["claims"][0]["source_refs"][0]["quote"]="가짜 자료"
            with self.subTest(mutation=mutation),self.assertRaises((InvalidInput,QualityNotProven)):
                self.fx.store.submit_host_atomic_batch(**self.args(window_models=models))
            self.assertEqual(self.fx.store.snapshot("host_scope")["ledger_head_sha256"],
                             self.base["ledger_head_sha256"])

    def test_failure_after_first_insert_rolls_back_entire_batch(self):
        def inject_failure(stage):
            if stage=="after_event_insert":
                raise RuntimeError("INJECTED_HOST_BATCH_FAILURE")
        original=self.fx.store._before_commit
        self.fx.store._before_commit=inject_failure
        try:
            with self.assertRaisesRegex(RuntimeError,"INJECTED_HOST_BATCH_FAILURE"):
                self.fx.store.submit_host_atomic_batch(**self.args())
        finally:
            self.fx.store._before_commit=original
        snap=self.fx.store.snapshot("host_scope")
        self.assertEqual(snap["sequence"],self.base["sequence"])
        self.assertEqual(snap["ledger_head_sha256"],self.base["ledger_head_sha256"])
        finished=self.fx.store.submit_host_atomic_batch(**self.args())
        self.assertFalse(finished["idempotent_replay"])

    def test_concurrent_stale_head_is_rejected(self):
        valid=self.fx.store.submit_host_atomic_batch(**self.args())
        with self.assertRaises(ConcurrentHeadChanged):
            self.fx.store.submit_host_atomic_batch(**self.args(
                run_id="run_0002",expected_head=self.base["ledger_head_sha256"]))
        self.assertEqual(self.fx.store.snapshot("host_scope")["ledger_head_sha256"],
                         valid["event_sha256"])


if __name__=="__main__":
    unittest.main()
