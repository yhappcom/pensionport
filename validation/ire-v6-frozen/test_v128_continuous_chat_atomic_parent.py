"""V128 synthetic continuous ChatGPT-hosted scope loop and all-child ACID publication.

The V6 child native stores, V123 final review and V126 private SQLite are REAL
implementations; all SRT, official HTML and ChatGPT verdicts are SYNTHETIC.
No model/API execution or legal accuracy/financial fact is certified here.
"""
from __future__ import annotations

import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ire.v6 import TransactionStore
from ire.v6.codec import ZERO_SHA, sha256
from ire.v6.errors import InvalidInput, QualityNotProven, ConcurrentHeadChanged
from test_v127_full_video_chat_completion import V127FullVideoChatReviewAggregationTests
from test_v126_chat_approved_knowledge_store import explicit_relation_decisions
from v126_chat_approved_knowledge_store import PrivateKnowledgeStore
from v1271_parent_resume_checkpoint import PrivateFullVideoCheckpoint
from v128_host_continuous_video import run_all_video_scopes_in_chat
from v128_atomic_parent_knowledge import (
    publish_parent_once, construct_parent_release_review,
)


class V128HostRunAndAtomicParentTests(unittest.TestCase):
    def setUp(self):
        self.p=V127FullVideoChatReviewAggregationTests(
            "test_every_parent_cue_and_multiwindow_child_replayed_in_one_call")
        self.addCleanup(self.p.doCleanups)
        original=TransactionStore.submit_host_atomic_batch
        submitted=[]

        def capture(store, **kwargs):
            result=original(store, **kwargs)
            if kwargs.get("scope_id", "").startswith("subscope_"):
                submitted.append(copy.deepcopy(kwargs))
            return result

        with patch.object(TransactionStore,"submit_host_atomic_batch",capture):
            self.p.setUp()
        self.assertEqual(len(submitted),2)
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.temp=Path(temp.name)
        self.checkpoint_kw={"raw":self.p.raw,"parent_manifest":self.p.manifest,
              "parent_inventory":self.p.inventory,
              "expected_parent_inventory_sha256":self.p.inventory_sha,
              "max_cues":2}
        self.checkpoint=PrivateFullVideoCheckpoint(self.temp/"checkpoint.sqlite",**self.checkpoint_kw)
        self.knowledge=PrivateKnowledgeStore(self.temp/"private_knowledge.sqlite")
        self.packets=[]
        for i,case in enumerate(self.p.cases):
            self.packets.append({
               "case":case,
               "relation_decisions":explicit_relation_decisions(case["exchange"],case["prior_knowledge"]),
               "original_host_batch_replay_args":submitted[i],
               "explicit_hold_revision":False,
            })
        self.trace=[]

    def child(self, segment_id, manifest, stage, original_raw):
        self.assertEqual(original_raw,self.p.raw)
        index=self.checkpoint.child_ids.index(segment_id)
        self.assertEqual(manifest,self.checkpoint.child_manifests[index])
        self.trace.append((segment_id,stage))
        return self.packets[index]

    def seams(self,checkpoint,cases):
        self.assertIs(checkpoint,self.checkpoint)
        self.assertEqual(len(cases),2)
        return self.p.seams

    def parent_review(self,checkpoint,assembly,seams,packets):
        template=construct_parent_release_review(
            assembly["checkpoint_head_sha256"],assembly,seams,packets,
            private_chat_parent_review_sha256=sha256(b"SYNTHETIC only: source-first parent verdict"))
        # Only the synthetic host test explicitly supplies affirmative judgments;
        # production code never fills these fields automatically.
        template.update(whole_parent_source_first_reviewed=True,
            condition_exception_rebuttal_seams_reviewed=True,
            prior_knowledge_conflicts_resolved=True,
            unresolved_high_risk_semantic_omissions=0,
            unresolved_cross_segment_cases=0)
        return template

    def run_engine(self,**kw):
        args={"checkpoint":self.checkpoint,"knowledge_store":self.knowledge,
              "review_or_load_child":self.child,"review_seams":self.seams,
              "review_parent":self.parent_review,
              "expected_knowledge_head":ZERO_SHA}
        args.update(kw)
        return run_all_video_scopes_in_chat(**args)

    def _counts(self):
        with sqlite3.connect(self.knowledge.path) as con:
            return {t:con.execute("SELECT COUNT(*) FROM "+t).fetchone()[0] for t in
                    ("events","knowledge", "parent_publications") if
                    con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?",(t,)).fetchone()}

    def test_01_two_native_v6_children_seam_and_atomic_private_parent_publication(self):
        result=self.run_engine()
        self.assertEqual(self.trace,[("B0001","REVIEW_REQUIRED"),("B0002","REVIEW_REQUIRED")])
        self.assertEqual(result["status"],"WHOLE_VIDEO_RESEARCH_CANDIDATE_PUBLISHED_ATOMICALLY")
        self.assertEqual(result["child_scopes_supplied"],2)
        self.assertEqual(result["child_checkpoints_written"],2)
        self.assertEqual(result["publication_receipt"]["entry_count"],3)
        self.assertEqual(self._counts(),{"events":3,"knowledge":3,"parent_publications":1})
        self.assertEqual(self.knowledge.audit()["head_sha256"],result["knowledge_head_sha256"])
        self.assertTrue(result["all_video_knowledge_published"])
        self.assertFalse(result["p0_go"])
        self.assertEqual(result["financial_fact_formally_approved"],0)

    def test_02_idempotent_same_chat_host_replay_and_no_second_publication(self):
        first=self.run_engine()
        second=self.run_engine()
        self.assertEqual(second["publication_receipt"]["status"],"IDEMPOTENT_PARENT_KNOWLEDGE_COMMIT")
        self.assertEqual(second["child_checkpoints_reused"],2)
        self.assertEqual(second["knowledge_head_sha256"],first["knowledge_head_sha256"])
        self.assertEqual(self._counts(),{"events":3,"knowledge":3,"parent_publications":1})
        self.assertEqual(self.trace[-2:],[("B0001","LOAD_EXISTING_PINNED_PASS"),
                                          ("B0002","LOAD_EXISTING_PINNED_PASS")])

    def test_03_second_child_finance_open_holds_and_knowledge_never_partially_inserts(self):
        packet=dict(self.packets[1]);case=dict(packet["case"])
        case["official_evidence_bodies"]={}
        packet["case"]=case
        self.packets[1]=packet
        r=self.run_engine()
        self.assertEqual(r["status"],"HOLD_CHILD_CHAT_SEMANTICS_OR_FINANCE")
        self.assertEqual(self.checkpoint.progress()["passed_child_scopes"],1)
        self.assertEqual(self.checkpoint.progress()["held_child_scopes"],1)
        self.assertEqual(self._counts().get("events",0),0)
        self.assertEqual(self._counts().get("knowledge",0),0)
        self.assertFalse(r["all_video_knowledge_published"])

    def test_04_recovery_from_open_requires_chat_explicit_revision(self):
        packet=dict(self.packets[1]);case=dict(packet["case"])
        case["official_evidence_bodies"]={}
        packet["case"]=case
        self.packets[1]=packet
        self.assertIn("HOLD",self.run_engine()["status"])
        self.packets[1]={**self.packets[1],"case":self.p.cases[1]}
        with self.assertRaisesRegex(QualityNotProven,"REVIEW_REVISION_NOT_EXPLICIT"):
            self.run_engine()
        self.packets[1]["explicit_hold_revision"]=True
        result=self.run_engine()
        self.assertEqual(result["publication_receipt"]["entry_count"],3)
        self.assertEqual(self.checkpoint.progress()["passed_child_scopes"],2)

    def test_05_missing_parent_chat_release_cannot_commit_after_all_children_pass(self):
        def missing(*args):return None
        with self.assertRaisesRegex(QualityNotProven,"PARENT_CHAT_RELEASE_SCHEMA"):
            self.run_engine(review_parent=missing)
        self.assertEqual(self._counts().get("events",0),0)
        self.assertEqual(self._counts().get("knowledge",0),0)
        self.assertEqual(self.checkpoint.progress()["passed_child_scopes"],2)

    def test_06_forged_parent_review_cannot_commit(self):
        def forge(checkpoint,assembly,seams,packets):
            result=self.parent_review(checkpoint,assembly,seams,packets)
            result["whole_parent_source_first_reviewed"]=False
            return result
        with self.assertRaisesRegex(QualityNotProven,"PARENT_CHAT_RELEASE_NOT_SOURCE_BOUND"):
            self.run_engine(review_parent=forge)
        self.assertEqual(self._counts().get("events",0),0)
        self.assertEqual(self._counts().get("knowledge",0),0)

    def test_07_missing_parent_seam_cannot_commit(self):
        with self.assertRaisesRegex(QualityNotProven,"MISSING_CROSS_SEGMENT"):
            self.run_engine(review_seams=lambda *_:[])
        self.assertEqual(self._counts().get("events",0),0)
        self.assertEqual(self._counts().get("knowledge",0),0)

    def test_08_bad_second_child_chat_relation_rolls_back_first_staged_success(self):
        modified=copy.deepcopy(self.packets[1]["relation_decisions"])
        modified[0]["private_chat_relation_review_sha256"]="BAD"
        self.packets[1]["relation_decisions"]=modified
        with self.assertRaises(QualityNotProven):
            self.run_engine()
        self.assertEqual(self._counts().get("events",0),0)
        self.assertEqual(self._counts().get("knowledge",0),0)

    def test_09_forged_second_host_replay_args_prevents_any_private_write(self):
        replay=copy.deepcopy(self.packets[1]["original_host_batch_replay_args"])
        replay["run_id"]="new-run-forgery"
        self.packets[1]["original_host_batch_replay_args"]=replay
        with self.assertRaises((QualityNotProven,ConcurrentHeadChanged)):
            self.run_engine()
        self.assertEqual(self._counts().get("events",0),0)
        self.assertEqual(self._counts().get("knowledge",0),0)

    def test_10_fail_at_last_parent_receipt_sqlite_insert_rolls_back_all_child_entries(self):
        with sqlite3.connect(self.knowledge.path) as con:
            con.execute("""CREATE TABLE parent_publications(parent_id TEXT PRIMARY KEY,
                      proof_json TEXT NOT NULL, proof_sha256 TEXT NOT NULL,
                      from_head_sha256 TEXT NOT NULL,to_head_sha256 TEXT NOT NULL,
                      entry_count INTEGER NOT NULL)""")
            con.execute("""CREATE TRIGGER abort_parent_proof BEFORE INSERT ON parent_publications
                      BEGIN SELECT RAISE(ABORT, 'synthetic parent receipt failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.run_engine()
        self.assertEqual(self._counts(),{"events":0,"knowledge":0,"parent_publications":0})
        self.assertEqual(self.knowledge.audit()["head_sha256"],ZERO_SHA)

    def test_11_same_parent_different_chat_signature_cannot_replace_publication(self):
        first=self.run_engine()
        def changed(checkpoint,assembly,seams,packets):
            out=self.parent_review(checkpoint,assembly,seams,packets)
            out["private_chat_parent_review_sha256"]=sha256(b"different synthetic verdict")
            return out
        with self.assertRaisesRegex(QualityNotProven,"PARENT_ALREADY_PUBLISHED_WITH_DIFFERENT_PROOF"):
            self.run_engine(review_parent=changed)
        self.assertEqual(self._counts(),{"events":3,"knowledge":3,"parent_publications":1})

    def test_12_mismatched_start_head_prevents_all_writes(self):
        with self.assertRaisesRegex(QualityNotProven,"KNOWLEDGE_EXPECTED_HEAD_CHANGED"):
            self.run_engine(expected_knowledge_head="1"*64)
        self.assertEqual(self._counts().get("events",0),0)
        self.assertEqual(self._counts().get("knowledge",0),0)

    def test_13_host_needs_real_callbacks_no_silent_fake_chat(self):
        with self.assertRaisesRegex(InvalidInput,"SYNC_CHAT_CALLBACKS_REQUIRED"):
            self.run_engine(review_or_load_child=None)
        self.assertEqual(self.checkpoint.progress()["passed_child_scopes"],0)

    def test_14_existing_parent_publication_proof_tamper_detected(self):
        self.run_engine()
        with sqlite3.connect(self.knowledge.path) as con:
            con.execute("UPDATE parent_publications SET proof_sha256=?",("1"*64,))
        with self.assertRaisesRegex(QualityNotProven,"PARENT_PROOF_HASH_OR_SCHEMA_DRIFT"):
            self.run_engine()

    def test_15_unresolved_contradiction_in_parent_relation_blocks_full_video(self):
        row=copy.deepcopy(self.packets[1]["relation_decisions"])
        row[0]["relation"]="CONFLICT"
        self.packets[1]["relation_decisions"]=row
        with self.assertRaisesRegex(QualityNotProven,"UNRESOLVED_PARENT_KNOWLEDGE_CONFLICT"):
            self.run_engine()
        self.assertEqual(self._counts().get("events",0),0)
        self.assertEqual(self._counts().get("knowledge",0),0)

    def test_16_old_direct_child_knowledge_writer_cannot_bypass_parent_gate(self):
        child=self.packets[0]
        c=child["case"]
        with self.assertRaisesRegex(QualityNotProven,
                                    "PARTIAL_SOURCE_REQUIRES_FULL_PARENT_ATOMIC_PUBLICATION"):
            self.knowledge.add_chat_final_batch(
                c["source"],c["exchange"],c["prior_knowledge"],
                host_receipt=c["host_receipt"],chat_review=c["chat_review"],
                source_store=c["source_store"],
                official_evidence_bodies=c["official_evidence_bodies"],
                relation_decisions=child["relation_decisions"],
                expected_knowledge_head=ZERO_SHA,
                original_host_batch_replay_args=child["original_host_batch_replay_args"])
        self.assertEqual(self._counts().get("events",0),0)
        self.assertEqual(self._counts().get("knowledge",0),0)

    def test_17_temporary_parent_staging_db_cannot_be_used_for_qa(self):
        stage_dir=self.temp/"v128_staging_synthetic"
        stage_dir.mkdir()
        stage=PrivateKnowledgeStore(stage_dir/"staging.db",parent_staging_only=True)
        with self.assertRaisesRegex(QualityNotProven,"UNPUBLISHED_PARENT_STAGING_NOT_QUERYABLE"):
            stage.evidence_for_question("투자 분산")
        with self.assertRaisesRegex(QualityNotProven,"UNPUBLISHED_PARENT_STAGING_CANNOT_REVOKE"):
            stage.revoke("0"*64,chat_review_sha256="1"*64,expected_knowledge_head=ZERO_SHA)


    def test_18_damaged_parent_approval_receipt_cannot_support_knowledge_query(self):
        # The V128 publisher already detects this on publication replay.
        # V130 extends fail-closed enforcement to the real V126 Q&A path.
        self.run_engine()
        with sqlite3.connect(self.knowledge.path) as con:
            con.execute("UPDATE parent_publications SET proof_sha256=?",("1"*64,))
        with self.assertRaisesRegex(QualityNotProven,"PARENT_PROOF_HASH_OR_SCHEMA_DRIFT"):
            self.knowledge.evidence_for_question("투자 연구 기반 분산 및 집중")
        with self.assertRaisesRegex(QualityNotProven,"PARENT_PROOF_HASH_OR_SCHEMA_DRIFT"):
            self.knowledge.audit()

    def test_19_modified_parent_event_head_cannot_support_answer_packet(self):
        self.run_engine()
        with sqlite3.connect(self.knowledge.path) as con:
            con.execute("UPDATE parent_publications SET to_head_sha256=?",("1"*64,))
        with self.assertRaisesRegex(QualityNotProven,"PARENT_PROOF_HASH_OR_SCHEMA_DRIFT"):
            self.knowledge.evidence_for_question("투자 연구 자문")

    def test_20_valid_parent_receipt_query_is_only_a_context_packet(self):
        self.run_engine()
        ev=self.knowledge.evidence_for_question("투자 연구 자문")
        self.assertFalse(ev["p0_go"])
        self.assertTrue(ev["research_candidate_not_formal_financial_fact"])
        self.assertTrue(ev["chatgpt_final_answer_review_required"])
        self.assertNotIn("answer_text",ev)

if __name__ == "__main__":
    unittest.main()
