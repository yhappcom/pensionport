"""V127.1 native V6+V123 synthetic child replay through private durable checkpoint.

No real official HTTP provenance, owner-signed inventory or real chat semantics.
"""
import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ire.v6.codec import ZERO_SHA
from ire.v6.errors import InvalidInput, QualityNotProven
from test_v127_full_video_chat_completion import V127FullVideoChatReviewAggregationTests
from v1271_parent_resume_checkpoint import PrivateFullVideoCheckpoint


class V1271PrivateFullVideoResumeTests(unittest.TestCase):
    def setUp(self):
        parent=V127FullVideoChatReviewAggregationTests("test_every_parent_cue_and_multiwindow_child_replayed_in_one_call")
        parent.setUp()
        self.addCleanup(parent.doCleanups)
        self.p=parent
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db=Path(tmp.name)/"v1271_private.db"
        self.kw={"raw":parent.raw,"parent_manifest":parent.manifest,
                 "parent_inventory":parent.inventory,
                 "expected_parent_inventory_sha256":parent.inventory_sha,
                 "max_cues":2}
        self.ck=PrivateFullVideoCheckpoint(self.db,**self.kw)

    def test_restart_replays_two_child_scopes_and_preserves_no_publication(self):
        initial=self.ck.progress()
        self.assertEqual(initial["next_segment_id"],"B0001")
        self.assertEqual(initial["expected_child_scopes"],2)
        first=self.ck.record("B0001",self.p.cases[0],expected_checkpoint_head=ZERO_SHA)
        self.assertEqual(first["status"],"CHILD_CHAT_CHECKPOINT_PASS")
        self.assertEqual(first["checkpoint_head_sha256"],self.ck.progress()["checkpoint_head_sha256"])
        restart=PrivateFullVideoCheckpoint(self.db,**self.kw)
        self.assertEqual(restart.progress()["next_segment_id"],"B0002")
        same=restart.record("B0001",self.p.cases[0],expected_checkpoint_head=ZERO_SHA)
        self.assertTrue(same["idempotent"])
        second=restart.record("B0002",self.p.cases[1],expected_checkpoint_head=first["checkpoint_head_sha256"])
        r=restart.assemble(self.p.cases,self.p.seams,
                           expected_checkpoint_head=second["checkpoint_head_sha256"])
        self.assertEqual(r["child_segments_replayed"],2)
        self.assertEqual(r["original_parent_cues"],4)
        self.assertFalse(r["new_knowledge_export_allowed"])
        self.assertFalse(r["whole_video_research_complete"])
        self.assertTrue(restart.progress()["ready_for_full_parent_replay"])

    def test_open_child_is_durable_but_cannot_finish_parent(self):
        hold=copy.copy(self.p.cases[0])
        hold["official_evidence_bodies"]={}
        row=self.ck.record("B0001",hold,expected_checkpoint_head=ZERO_SHA)
        self.assertEqual(row["status"],"CHILD_CHAT_CHECKPOINT_HOLD")
        self.assertEqual(self.ck.progress()["held_child_scopes"],1)
        with self.assertRaisesRegex(QualityNotProven,"ASSEMBLY_CHILD_REVIEW_STILL_OPEN"):
            self.ck.assemble(self.p.cases,self.p.seams,
                             expected_checkpoint_head=row["checkpoint_head_sha256"])

    def test_open_evidence_requires_explicit_review_revision(self):
        hold=copy.copy(self.p.cases[0]);hold["official_evidence_bodies"]={}
        first=self.ck.record("B0001",hold,expected_checkpoint_head=ZERO_SHA)
        with self.assertRaisesRegex(QualityNotProven,"REVIEW_REVISION_NOT_EXPLICIT"):
            self.ck.record("B0001",self.p.cases[0],
                expected_checkpoint_head=first["checkpoint_head_sha256"])
        second=self.ck.record("B0001",self.p.cases[0],
            expected_checkpoint_head=first["checkpoint_head_sha256"],allow_hold_revision=True)
        self.assertEqual(second["status"],"CHILD_CHAT_CHECKPOINT_PASS")
        self.assertEqual(self.ck.progress()["passed_child_scopes"],1)
        self.assertNotEqual(second["checkpoint_head_sha256"],first["checkpoint_head_sha256"])

    def test_stale_head_rejected_and_old_approval_unchanged(self):
        first=self.ck.record("B0001",self.p.cases[0],expected_checkpoint_head=ZERO_SHA)
        with self.assertRaisesRegex(QualityNotProven,"CHECKPOINT_EXPECTED_HEAD_CHANGED"):
            self.ck.record("B0002",self.p.cases[1],expected_checkpoint_head=ZERO_SHA)
        self.assertEqual(self.ck.progress()["checkpoint_head_sha256"],first["checkpoint_head_sha256"])
        self.assertEqual(self.ck.progress()["passed_child_scopes"],1)

    def test_owner_or_plan_drift_refused_at_resume(self):
        with self.assertRaisesRegex(QualityNotProven,"PARENT_PLAN_OR_SOURCE_PIN_CHANGED"):
            PrivateFullVideoCheckpoint(self.db,**{**self.kw,"max_cues":4})
        with self.assertRaises(InvalidInput):
            PrivateFullVideoCheckpoint(self.db,**{**self.kw,"raw":self.p.raw+b" "})

    def test_child_manifest_tamper_cannot_write_checkpoint(self):
        child=dict(self.p.cases[0]);child["manifest"]=self.p.manifest
        with self.assertRaisesRegex(QualityNotProven,"CHILD_MANIFEST_NOT_IN_PARENT_PLAN"):
            self.ck.record("B0001",child,expected_checkpoint_head=ZERO_SHA)
        self.assertEqual(self.ck.progress()["checkpoint_head_sha256"],ZERO_SHA)

    def test_sqlite_checkpoint_tamper_detected_after_restart(self):
        self.ck.record("B0001",self.p.cases[0],expected_checkpoint_head=ZERO_SHA)
        with sqlite3.connect(self.db) as con:
            con.execute("UPDATE checkpoint_events SET event_sha256=? WHERE seq=1",("0"*64,))
        with self.assertRaisesRegex(QualityNotProven,"CHECKPOINT_PROOF_CHAIN_OR_SHA_DRIFT"):
            PrivateFullVideoCheckpoint(self.db,**self.kw)

    def test_missing_cross_boundary_review_blocks_parent_assembly(self):
        first=self.ck.record("B0001",self.p.cases[0],expected_checkpoint_head=ZERO_SHA)
        second=self.ck.record("B0002",self.p.cases[1],
                              expected_checkpoint_head=first["checkpoint_head_sha256"])
        with self.assertRaisesRegex(QualityNotProven,"MISSING_CROSS_SEGMENT"):
            self.ck.assemble(self.p.cases,[],expected_checkpoint_head=second["checkpoint_head_sha256"])

    def test_private_subtitle_text_not_written_into_checkpoint(self):
        self.ck.record("B0001",self.p.cases[0],expected_checkpoint_head=ZERO_SHA)
        raw=self.db.read_bytes()
        for cue in self.p.parent.fx.source.cues:
            self.assertNotIn(cue.text.encode("utf-8"),raw)

    def test_checkpoint_external_head_comparison_does_not_self_certify_owner(self):
        row=self.ck.record("B0001",self.p.cases[0],expected_checkpoint_head=ZERO_SHA)
        self.assertEqual(self.ck.progress(externally_pinned_checkpoint_head=row["checkpoint_head_sha256"])["passed_child_scopes"],1)
        with self.assertRaisesRegex(QualityNotProven,"EXTERNAL_CHECKPOINT_HEAD_DRIFT"):
            self.ck.progress(externally_pinned_checkpoint_head="2"*64)

if __name__=="__main__":
    unittest.main()