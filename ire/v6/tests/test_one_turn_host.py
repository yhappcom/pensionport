"""Private no-API one-turn renderer to ACID host-batch bridge: synthetic cues."""
from __future__ import annotations

import copy
import json
import unittest

from ire.v6.errors import (ConcurrentHeadChanged, DomainConflict,
                           InvalidInput, QualityNotProven)
from ire.v6.one_turn_host import (prepare_private_host_turn,
                                  commit_private_host_turn)
from ire.v6.tests import test_host_batch as fixture_module


class HostOneTurnBridgeTests(unittest.TestCase):
    def setUp(self):
        fixture=fixture_module.HostBatchTests(
            "test_one_command_commits_all_models_and_proofs_atomically")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.f=fixture

    def prepare(self,**updates):
        args=dict(raw=self.f.fx.raw,manifest=self.f.fx.manifest,
                  inventory_bytes=self.f.owner,scope_id="host_scope",
                  expected_inventory_sha256=self.f.pin,
                  expected_head=self.f.base["ledger_head_sha256"])
        args.update(updates)
        return prepare_private_host_turn(**args)

    def complete(self,packet,**updates):
        args=dict(raw=self.f.fx.raw,manifest=self.f.fx.manifest,
                  inventory_bytes=self.f.owner,
                  expected_inventory_sha256=self.f.pin,run_id="run_0001",
                  exchange=self.f.fx.exchange,knowledge=self.f.knowledge,
                  window_models=self.f.models,window_reviews=self.f.reviews)
        args.update(updates)
        return commit_private_host_turn(self.f.fx.store,packet,**args)

    def test_renders_source_first_exact_original_cues_and_windows(self):
        x=self.prepare()
        self.assertEqual(x["status"],"HOST_TURN_READY_NOT_EXECUTED")
        self.assertTrue(x["turn_payload_available"])
        self.assertEqual(x["scoped_cue_count"],4)
        self.assertEqual(len(x["turn_payload"]["windows"]),2)
        self.assertEqual(
            [r["cue_index"] for w in x["turn_payload"]["windows"]
                             for r in w["primary_cues"]],
            [1,2,3,4])
        self.assertEqual(x["turn_payload"]["windows"][0]["primary_cues"][0]["text"],
                         self.f.fx.source.cues[0].text)
        self.assertTrue(x["turn_payload"]["independent_gold_must_not_be_shown_to_model"])
        self.assertFalse(x["full_video_research_completed"])

    def test_true_existing_transactional_batch_end_to_end(self):
        r=self.complete(self.prepare())
        self.assertTrue(r["atomic_batch_receipt"]["atomic_batch_committed"])
        self.assertTrue(r["atomic_batch_receipt"]["human_semantic_review_pending"])
        self.assertFalse(r["research_complete"])
        self.assertFalse(r["p0_go"])
        self.assertFalse(r["model_api_called"])
        self.assertEqual(self.f.fx.store.snapshot("host_scope")["progress"]["model_windows_recorded"],2)

    def test_exact_retry_is_idempotent_without_new_events(self):
        t=self.prepare()
        a=self.complete(t)
        b=self.complete(t)
        self.assertEqual(a["atomic_batch_receipt"]["event_sha256"],
                         b["atomic_batch_receipt"]["event_sha256"])
        self.assertTrue(b["atomic_batch_receipt"]["idempotent_replay"])

    def test_private_source_cue_tamper_blocked_before_write(self):
        t=self.prepare()
        t["turn_payload"]["windows"][0]["primary_cues"][0]["text"]="허위 원본"
        with self.assertRaisesRegex(DomainConflict,"PRIVATE_SOURCE_PACKET_DRIFT"):
            self.complete(t)
        self.assertEqual(self.f.base["ledger_head_sha256"],
                         self.f.fx.store.snapshot("host_scope")["ledger_head_sha256"])

    def test_change_expected_cue_model_status_never_promotes(self):
        t=self.prepare()
        t["full_video_research_completed"]=True
        with self.assertRaises(DomainConflict):
            self.complete(t)

    def test_scope_over_source_budget_blocked_without_text(self):
        t=self.prepare(max_cues=2)
        self.assertFalse(t["turn_payload_available"])
        self.assertNotIn("turn_payload",t)
        self.assertEqual(t["scoped_cue_count"],4)
        self.assertFalse(t["full_video_research_completed"])
        self.assertEqual(t["status"],"HOST_TURN_BLOCKED_SCOPE_TOO_MANY_CUES")
        with self.assertRaisesRegex(QualityNotProven,"CANNOT_BE_COMPLETED"):
            self.complete(t,max_cues=2)

    def test_payload_budget_overflow_fails_closed(self):
        t=self.prepare(max_payload_bytes=1024)
        self.assertFalse(t["turn_payload_available"])
        self.assertEqual(t["status"],"HOST_TURN_BLOCKED_PRIVATE_PAYLOAD_TOO_LARGE")
        self.assertNotIn("turn_payload",t)

    def test_source_sha_drift_fails_before_model_generation(self):
        with self.assertRaises(InvalidInput):
            self.prepare(raw=self.f.fx.raw+b" ")

    def test_concurrent_head_changed_blocks_old_turn(self):
        t=self.prepare()
        self.complete(t)
        with self.assertRaises(ConcurrentHeadChanged):
            self.complete(t,run_id="run_0002")

    def test_no_private_text_in_published_receipt(self):
        r=self.complete(self.prepare())
        encoded=json.dumps(r,ensure_ascii=False)
        for cue in self.f.fx.source.cues:
            self.assertNotIn(cue.text,encoded)
        self.assertNotIn("turn_payload",r)

    def test_bad_budget_inputs_rejected(self):
        for val in (0,True,20001):
            with self.assertRaises(InvalidInput):
                self.prepare(max_cues=val)


if __name__=="__main__":
    unittest.main()
