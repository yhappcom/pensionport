"""Private E2 checkpoint: SHA chain, owner pins, conflicts, idempotence and resume."""
from __future__ import annotations

import copy
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from ire.v6.codec import ZERO_SHA
from ire.v6.errors import InvalidInput
from v206_e2_private_cue_checkpoint import PrivateE2CensusCheckpoint
from v206_e2_full_cue_semantic_census import prepare_e2_cue_challenge
from test_v206_e2_full_cue_semantic_census import answered
import test_v202_e1_v176_native_positive_path as e1_fixture


class TestV206PrivateE2Checkpoint(unittest.TestCase):
    def setUp(self):
        self.fx=e1_fixture.TestV202SameInputE1Route(
            "test_01_preseeded_native_v166_cannot_impersonate_v176_verdict")
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.owner=self.fx.owner
        self.head=self.owner.progress()["checkpoint_head_sha256"]
        self.dir=tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path=Path(self.dir.name)/"e2_private.db"
        self.store=PrivateE2CensusCheckpoint(
            self.path,self.owner,expected_owner_head=self.head)

    def batch(self,start,limit):
        c=prepare_e2_cue_challenge(self.owner,
            expected_owner_head=self.head,start_cue=start,limit=limit)
        return c,answered(c)

    def test_01_first_batch_then_resume_preserves_head_and_next_cue(self):
        original=self.store.progress()
        self.assertEqual(original["private_e2_head_sha256"],ZERO_SHA)
        self.assertEqual(original["original_cues_remaining"],4)
        c,a=self.batch(1,2)
        result=self.store.record(c,a,expected_private_head=ZERO_SHA)
        self.assertEqual(result["original_cues_committed"],2)
        self.assertEqual(self.store.progress()["next_cue_index"],3)
        resumed=PrivateE2CensusCheckpoint(
            self.path,self.owner,expected_owner_head=self.head)
        self.assertEqual(resumed.progress(externally_pinned_private_head=
                         result["private_head_sha256"])["original_cues_checkpointed"],2)
        self.assertFalse(resumed.progress()["e2_pass"])

    def test_02_all_cues_checkpointed_does_not_certify_semantic_gold(self):
        c1,a1=self.batch(1,2)
        first=self.store.record(c1,a1,expected_private_head=ZERO_SHA)
        c2,a2=self.batch(3,2)
        self.store.record(c2,a2,expected_private_head=first["private_head_sha256"])
        result=self.store.progress()
        self.assertEqual(result["original_cues_remaining"],0)
        self.assertTrue(result["source_cue_census_recorded"])
        self.assertFalse(result["independent_gold_semantics_verified"])
        self.assertFalse(result["e2_pass"])
        self.assertFalse(result["e3_e4_e5_authorized"])

    def test_03_retry_same_batch_is_idempotent_no_new_event(self):
        c,a=self.batch(1,2)
        first=self.store.record(c,a,expected_private_head=ZERO_SHA)
        duplicate=self.store.record(c,a,expected_private_head=ZERO_SHA)
        self.assertEqual(duplicate["status"],
                         "IDEMPOTENT_E2_CUE_REVIEW_REPLAY")
        self.assertEqual(duplicate["private_head_sha256"],
                         first["private_head_sha256"])
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM e2_events").fetchone()[0],1)

    def test_04_changed_same_cue_cannot_overwrite_private_verdict(self):
        c,a=self.batch(1,2)
        first=self.store.record(c,a,expected_private_head=ZERO_SHA)
        modified=copy.deepcopy(a)
        modified["rows"][0]["reviewer_caution"]="정식 예금자보호 여부가 검증되지 않았으므로 원문 발화를 사실로 확인하면 안 됩니다."
        from ire.v6.codec import sha256
        modified["rows"][0]["reviewer_caution_sha256"]=sha256(
            modified["rows"][0]["reviewer_caution"].encode())
        with self.assertRaisesRegex(InvalidInput,
                                    "PRIVATE_CUE_ALREADY_REVIEWED_NO_SILENT_REVISION"):
            self.store.record(c,modified,
                expected_private_head=first["private_head_sha256"])
        self.assertEqual(self.store.progress()["original_cues_checkpointed"],2)

    def test_05_interleaved_stale_expected_head_rejected(self):
        c,a=self.batch(1,2)
        self.store.record(c,a,expected_private_head=ZERO_SHA)
        c2,a2=self.batch(3,2)
        with self.assertRaisesRegex(InvalidInput,
                                   "PRIVATE_EXPECTED_HEAD_STALE"):
            self.store.record(c2,a2,expected_private_head=ZERO_SHA)
        self.assertEqual(self.store.progress()["original_cues_remaining"],2)

    def test_06_corrupted_private_event_hash_is_detected(self):
        c,a=self.batch(1,2)
        self.store.record(c,a,expected_private_head=ZERO_SHA)
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE e2_events SET event_sha256=? WHERE seq=1",
                       ("f"*64,))
        with self.assertRaisesRegex(InvalidInput,"PRIVATE_EVENT_HASH_OR_SCHEMA_DRIFT"):
            self.store.progress()

    def test_07_private_payload_modification_rejected(self):
        c,a=self.batch(1,2)
        self.store.record(c,a,expected_private_head=ZERO_SHA)
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE e2_events SET event_json=? WHERE seq=1",
                       ('{"unsafe":"false review"}',))
        with self.assertRaisesRegex(InvalidInput,"PRIVATE_EVENT_HASH_OR_SCHEMA_DRIFT"):
            self.store.progress()

    def test_08_external_pin_mismatch_rejected(self):
        c,a=self.batch(1,2)
        self.store.record(c,a,expected_private_head=ZERO_SHA)
        with self.assertRaisesRegex(InvalidInput,
                                    "EXTERNAL_PRIVATE_CHECKPOINT_HEAD_CHANGED"):
            self.store.progress(externally_pinned_private_head="f"*64)

    def test_09_private_file_mode_enforced(self):
        self.assertEqual(self.path.stat().st_mode & 0o077,0)
        os.chmod(self.path,0o644)
        with self.assertRaisesRegex(InvalidInput,
                                    "PRIVATE_FILE_PERMISSIONS_REQUIRED"):
            PrivateE2CensusCheckpoint(
                self.path,self.owner,expected_owner_head=self.head)

    def test_10_wrong_owner_head_on_resume_fails_closed(self):
        with self.assertRaisesRegex(InvalidInput,
                                   "ORIGINAL_OWNER_JOURNAL_CHANGED"):
            PrivateE2CensusCheckpoint(
                self.path,self.owner,expected_owner_head="f"*64)


if __name__=="__main__":
    unittest.main()
