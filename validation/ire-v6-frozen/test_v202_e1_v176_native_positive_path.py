"""V202 E1-only same-input native V176→V123→V127→V128→V126 tests.

Synthetic authored ChatGPT packets only. No actual E2/E3/E4 financial quality
or real user-video 13-segment knowledge approval is implied.
"""
from __future__ import annotations
import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ire.v6 import TransactionStore
from ire.v6.codec import ZERO_SHA, sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession, COMMIT
from v202_e1_v176_native_positive_path import run_connected_e1_route
import test_v166_e1_same_typed_review_to_sqlite as v166_fixture


class TestV202SameInputE1Route(unittest.TestCase):
    def setUp(self):
        self.fx=v166_fixture.V166E1SameTypedReviewToSQLite(
            "test_01_same_typed_review_native_v123_v127_v128_private_sqlite_commit")
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.fx._prepare()  # Explicit synthetic V166 source-only ChatGPT attestation.
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.owner=EngineChatSession(
            self.root/"owner.sqlite",self.fx.fx.p.raw,"AbCdEf12345",
            owner_source_sha256=sha256(self.fx.fx.p.raw),window_size=2,
            expected_window_count=2)
        self.native=TransactionStore(self.root/"parent_native.db")
        self.assertEqual(self.owner.manifest,self.fx.fx.p.manifest)
        self._commit_same_chat_candidates()

    def _native_atoms(self):
        return {atom["source_refs"][0]["cue_index"]:atom
                for p in self.fx.fx.packets
                for atom in p["case"]["exchange"]["atoms"]}

    def _commit_same_chat_candidates(self):
        atoms=self._native_atoms()
        while True:
            task=self.owner.prepare(limit=2,source_first_only=True)
            if task["type"]!="CLASSIFY_SOURCE_CUES":
                break
            rows=[]
            for item in task["target_cues"]:
                i=item["cue_index"]
                atom=atoms.get(i)
                claim=[]
                if atom:
                    claim=[{
                        "proposition": atom["proposition"],
                        "kind":atom["kind"],
                        "quote":atom["source_refs"][0]["quote"],
                        "context_cue_indices":atom["context_cue_indices"],
                        "conditions":["소득에 따라"] if i==3 else [],
                        "exceptions":[],
                        "numeric_tokens":[x["token"] for x in
                                          atom["numeric_references"]],
                        "high_risk":True,
                        "needs_official_source":True,
                    }]
                rows.append({
                    "cue_index":i,"source_text_sha256":item["source_text_sha256"],
                    "disposition":"ASSERTION" if atom else "NON_RESEARCH",
                    "analysis":"합성 영상 원문만 읽고 출처와 발화 문맥을 검토한 미승인 후보입니다.",
                    "speaker_role":"HOST",
                    "limitations_checked":True,
                    "claims":claim,
                })
            self.owner.submit(task,{
                "schema":COMMIT,"challenge_sha256":task["challenge_sha256"],
                "review_executor":"CHATGPT_IN_CHAT","responses":rows})
        self.assertTrue(self.owner.progress()["source_first_review_complete"])

    def args(self,**extra):
        d=dict(
            owner=self.owner,
            parent_native_store=self.native,
            checkpoint=self.fx.fx.checkpoint,
            knowledge_store=self.fx.fx.knowledge,
            scope_id="e1_v202_same_source",
            inventory_bytes=self.fx.fx.p.inventory,
            expected_inventory_sha256=self.fx.fx.p.inventory_sha,
            expected_owner_head=self.owner.progress()["checkpoint_head_sha256"],
            new_parent_scope=True,
            review_or_load_child=self.fx.fx.child,
            review_seams=self.fx.fx.seams,
            review_parent=self.fx.fx.parent_review,
            expected_knowledge_head=ZERO_SHA,
        )
        d.update(extra)
        return d

    def _counts(self):
        with sqlite3.connect(self.fx.fx.knowledge.path) as con:
            existing={x[0] for x in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            return {name:(con.execute("SELECT COUNT(*) FROM "+name).fetchone()[0]
                          if name in existing else 0)
                    for name in ("events","knowledge","parent_publications")}

    def test_01_same_original_review_reaches_frozen_gate_and_atomic_sqlite(self):
        r=run_connected_e1_route(**self.args())
        self.assertEqual(r["e1_structural_route"],"PASS_SYNTHETIC_ROUTE")
        self.assertEqual(r["checked_cues"],4)
        self.assertEqual(r["checked_atoms"],3)
        self.assertEqual(r["knowledge_sqlite_counts"],{
            "events":2,"knowledge":2,"parent_publications":1})
        self.assertTrue(r["legacy_v123_v127_v128_v126_invoked"])
        self.assertEqual(r["native_v128_status"],
                         "WHOLE_VIDEO_RESEARCH_CANDIDATE_PUBLISHED_ATOMICALLY")
        self.assertEqual(self._counts(),r["knowledge_sqlite_counts"])
        self.assertFalse(r["e3_independent_gold_verified"])
        self.assertFalse(r["e5_real_13_segment_pub_verified"])

    def test_02_missing_child_official_bytes_hold_zero_publication(self):
        self.fx.fx.packets[1]["case"]["official_evidence_bodies"]={}
        r=run_connected_e1_route(**self.args())
        self.assertEqual(r["e1_structural_route"],"SAFE_HOLD_NO_PUBLICATION")
        self.assertEqual(r["native_v128_status"],
                         "HOLD_CHILD_CHAT_SEMANTICS_OR_FINANCE")
        self.assertEqual(r["knowledge_sqlite_counts"],{
            "events":0,"knowledge":0,"parent_publications":0})

    def test_03_native_child_claim_substitution_fails_closed_before_release(self):
        self.fx.fx.packets[0]["case"]["exchange"]["atoms"][0]["proposition"]+=" 가짜"
        with self.assertRaisesRegex(InvalidInput,
                                    "CANDIDATE_MEANING_OR_PROVENANCE_SUBSTITUTED"):
            run_connected_e1_route(**self.args())
        self.assertEqual(self._counts(),{
            "events":0,"knowledge":0,"parent_publications":0})

    def test_04_owner_head_tamper_rejected_without_publication(self):
        with self.assertRaisesRegex(InvalidInput,"EXTERNAL_OWNER_HEAD_CHANGED"):
            run_connected_e1_route(**self.args(expected_owner_head="f"*64))
        self.assertEqual(self._counts(),{
            "events":0,"knowledge":0,"parent_publications":0})

    def test_05_parent_original_plan_mismatch_fails_before_store(self):
        self.fx.fx.checkpoint.parent_manifest=dict(self.fx.fx.checkpoint.parent_manifest)
        self.fx.fx.checkpoint.parent_manifest["cue_count"]=888
        with self.assertRaisesRegex(InvalidInput,
                                    "V128_PARENT_SOURCE_OR_PLAN_SUBSTITUTED"):
            run_connected_e1_route(**self.args())
        self.assertEqual(self._counts(),{
            "events":0,"knowledge":0,"parent_publications":0})

    def test_06_separate_private_reopen_keeps_source_and_owner_digest(self):
        r=run_connected_e1_route(**self.args())
        reopened=EngineChatSession(self.root/"owner.sqlite",self.fx.fx.p.raw,
            "AbCdEf12345",owner_source_sha256=sha256(self.fx.fx.p.raw),
            window_size=2,expected_window_count=2)
        self.assertEqual(r["owner_head_sha256"],
                         reopened.progress()["checkpoint_head_sha256"])
        native_reopen=TransactionStore(self.root/"parent_native.db")
        self.assertEqual(r["native_source_ledger_head_sha256"],
                         native_reopen.snapshot("e1_v202_same_source")["ledger_head_sha256"])
        self.assertEqual(r["knowledge_sqlite_counts"],self._counts())

    def test_08_unattested_speaker_and_stance_cannot_become_native_approval(self):
        """V202 formerly ignored speaker/stance drift from V176 source review."""
        owner_exchange,_=self.owner.compile_native_v6_stage()
        native_atoms=[a for p in self.fx.fx.packets
                      for a in p["case"]["exchange"]["atoms"]]
        self.assertEqual(len(owner_exchange["atoms"]),len(native_atoms))
        self.assertTrue(all(a["speaker"]=="UNKNOWN" and
                            a["stance"]=="UNRESOLVED"
                            for a in owner_exchange["atoms"]))
        self.assertTrue(any(a["speaker"]!="UNKNOWN" and
                            a["stance"]!="UNRESOLVED"
                            for a in native_atoms))
        # The original V176 ChatGPT journal never authorized these changes.
        # No native approval or knowledge write is allowed.
        with self.assertRaisesRegex(InvalidInput,
                                    "SEMANTIC_FRAME_UNATTESTED"):
            run_connected_e1_route(**self.args())
        self.assertEqual(self._counts(),{
            "events":0,"knowledge":0,"parent_publications":0})

    def test_07_cannot_restart_approval_by_resetting_private_native(self):
        run_connected_e1_route(**self.args())
        with self.assertRaisesRegex(InvalidInput,"NEW_SCOPE_ALREADY_EXISTS"):
            run_connected_e1_route(**self.args())


if __name__=="__main__":
    unittest.main()
