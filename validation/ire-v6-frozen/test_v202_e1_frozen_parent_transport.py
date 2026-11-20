"""E1-only: actual V176 reviewed SRT routed through frozen V123/V128/V126.

Every utterance and financial verdict is SYNTHETIC, pre-authored in fixture.
The test proves connection, not the quality or authenticity of E2–E5.
"""
import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession, COMMIT
from v202_e1_frozen_parent_transport import run_source_pinned_parent
from test_v166_e1_same_typed_review_to_sqlite import V166E1SameTypedReviewToSQLite


class V202FrozenE1Transport(unittest.TestCase):
    def setUp(self):
        fixture = V166E1SameTypedReviewToSQLite(
            "test_01_same_typed_review_native_v123_v127_v128_private_sqlite_commit")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture._prepare()
        self.fx=fixture
        root=tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        self.original=fixture.fx.p.raw
        self.engine=EngineChatSession(
            Path(root.name)/"v176-owner.sqlite",self.original,
            fixture.fx.p.parent.fx.source.video_id,
            owner_source_sha256=sha256(self.original),
            window_size=2,expected_window_count=2)
        atoms=[]
        for case in fixture.fx.packets:
            atoms.extend(case["case"]["exchange"]["atoms"])
        self.atoms=atoms
        self._populate_v176_source()
        self.head=self.engine.progress()["checkpoint_head_sha256"]

    def _populate_v176_source(self):
        grouped={}
        for atom in self.atoms:
            ref=atom["source_refs"][0]
            grouped.setdefault(ref["cue_index"],[]).append(atom)
        while self.engine.progress()["cue_remaining"]:
            task=self.engine.prepare(limit=2,source_first_only=True)
            rows=[]
            for cue in task["target_cues"]:
                idx=cue["cue_index"]
                members=grouped.get(idx,[])
                claims=[]
                for atom in members:
                    quote=atom["source_refs"][0]["quote"]
                    claims.append({
                        "proposition":atom["proposition"],
                        "kind":atom["kind"],
                        "quote":quote,
                        "context_cue_indices":[idx],
                        "conditions":[],"exceptions":[],
                        "numeric_tokens":[],"high_risk":True,
                        "needs_official_source":True})
                rows.append({
                    "cue_index":idx,
                    "source_text_sha256":cue["source_text_sha256"],
                    "disposition":"ASSERTION" if members else "NON_RESEARCH",
                    "analysis":"합성 원본에서 검토한 잠정 발언이며 금융 사실을 승인한 것이 아닙니다.",
                    "speaker_role":"NARRATOR","claims":claims,
                    "limitations_checked":True,
                })
            self.engine.submit(task,{
                "schema":COMMIT,
                "challenge_sha256":task["challenge_sha256"],
                "review_executor":"CHATGPT_IN_CHAT",
                "responses":rows})

    def run(self,**kw):
        params=dict(
            engine=self.engine,
            checkpoint=self.fx.fx.checkpoint,
            knowledge_store=self.fx.fx.knowledge,
            expected_owner_head=self.head,
            expected_knowledge_head="0"*64,
            review_or_load_child=self.fx.fx.child,
            review_seams=self.fx.fx.seams,
            review_parent=self.fx.fx.parent_review)
        params.update(kw)
        return run_source_pinned_parent(**params)

    def test_01_real_frozen_full_transport_writes_only_synthetic_approved_atoms(self):
        result=self.run()
        self.assertEqual(result["native_parent_status"],
                         "WHOLE_VIDEO_RESEARCH_CANDIDATE_PUBLISHED_ATOMICALLY")
        self.assertTrue(result["native_knowledge_published"])
        self.assertEqual(self.fx._counts(),
                         {"events":2,"knowledge":2,"parent_publications":1})
        self.assertFalse(result["e4_real_financial_approval_certified"])
        self.assertFalse(result["e5_real_13_child_knowledge_certified"])

    def test_02_resume_idempotent_does_not_duplicate_native_publication(self):
        first=self.run()
        second=self.run()
        self.assertEqual(second["native_parent_result"]["publication_receipt"]["status"],
                         "IDEMPOTENT_PARENT_KNOWLEDGE_COMMIT")
        self.assertEqual(first["native_parent_result"]["knowledge_head_sha256"],
                         second["native_parent_result"]["knowledge_head_sha256"])
        self.assertEqual(self.fx._counts(),
                         {"events":2,"knowledge":2,"parent_publications":1})

    def test_03_wrong_owner_checkpoint_blocks_before_knowledge_write(self):
        with self.assertRaisesRegex(InvalidInput,"FROZEN_OWNER_HEAD_MISMATCH"):
            self.run(expected_owner_head="f"*64)
        self.fx._assert_zero()

    def test_04_child_atom_injection_blocks_before_parent_publication(self):
        original=self.fx.fx.child
        def altered(segment_id,manifest,stage,raw):
            packet=copy.deepcopy(original(segment_id,manifest,stage,raw))
            packet["case"]["exchange"]["atoms"][0]["proposition"]="Forged 99% guaranteed return"
            return packet
        with self.assertRaisesRegex(InvalidInput,"UNREVIEWED_CHILD_ATOM_INJECTED"):
            self.run(review_or_load_child=altered)
        self.fx._assert_zero()

    def test_05_original_source_differs_blocks_before_all_callbacks(self):
        class BadCheckpoint:
            raw=b"wrong source"
        with self.assertRaisesRegex(InvalidInput,"PARENT_SOURCE_BYTES_DIFFER"):
            self.run(checkpoint=BadCheckpoint())
        self.fx._assert_zero()

    def test_06_unverified_financial_child_holds_and_keeps_knowledge_empty(self):
        second=self.fx.fx.packets[1]["case"]
        second["official_evidence_bodies"]={}
        result=self.run()
        self.assertEqual(result["native_parent_status"],
                         "HOLD_CHILD_CHAT_SEMANTICS_OR_FINANCE")
        self.assertFalse(result["native_knowledge_published"])
        self.fx._assert_zero()

    def test_07_parent_sqlite_abort_rolls_back_all_child_staging(self):
        with sqlite3.connect(self.fx.fx.knowledge.path) as con:
            con.execute("""CREATE TABLE parent_publications(parent_id TEXT PRIMARY KEY,
                proof_json TEXT NOT NULL,proof_sha256 TEXT NOT NULL,
                from_head_sha256 TEXT NOT NULL,to_head_sha256 TEXT NOT NULL,
                entry_count INTEGER NOT NULL)""")
            con.execute("""CREATE TRIGGER reject_parent_insert BEFORE INSERT ON parent_publications
                BEGIN SELECT RAISE(ABORT,'forced E1 parent failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.run()
        self.fx._assert_zero()

    def test_08_missing_chat_callbacks_no_silent_approval(self):
        with self.assertRaisesRegex(InvalidInput,"ACTUAL_HOST_CALLBACKS_REQUIRED"):
            self.run(review_parent=None)
        self.fx._assert_zero()


if __name__=="__main__":
    unittest.main()
