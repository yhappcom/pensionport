"""V6-1 adversarial contracts. Tests intentionally require no V5 imports/data."""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ire.v6 import (TransactionStore, ConcurrentHeadChanged, DomainConflict,
                    IdempotencyConflict, InvalidInput, LedgerCorrupted,
                    QualityNotProven, UnsupportedSchema)
from ire.v6.codec import sha256

SRC = sha256(b"original-private-bytes-not-stored-in-public-tests")
MAN = sha256(b"fixture window plan")
VID = "A1b2C3d4E5F"


class KernelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "private" / "v6.db"
        self.store = TransactionStore(self.path)
        self.created = self.store.create_scope(
            scope_id="study_scope_A", video_id=VID,
            source_sha256=SRC, manifest_sha256=MAN,
            command_id="create_scope_A")

    def model(self, *, key="submit_A", expected=None, value="A"):
        return self.store.submit(
            scope_id="study_scope_A", command_id=key,
            expected_head=expected or self.store.snapshot("study_scope_A")["ledger_head_sha256"],
            kind="MODEL_RECORDED",
            payload={"window_id":"W00001", "model":{"meaning":value}})

    def test_insecure_database_directory_or_file_is_rejected(self):
        if os.name != "posix":
            self.skipTest("POSIX permission model only")
        exposed = Path(self.tmp.name) / "exposed"
        exposed.mkdir(mode=0o755)
        os.chmod(exposed, 0o755)
        with self.assertRaises(InvalidInput):
            TransactionStore(exposed / "bad.db")
        os.chmod(self.path, 0o644)
        with self.assertRaises(InvalidInput):
            TransactionStore(self.path)
        os.chmod(self.path, 0o600)
        self.assertEqual(TransactionStore(self.path).snapshot("study_scope_A")["sequence"],1)

    def test_genesis_is_canonical_and_no_false_approval(self):
        snap = self.store.snapshot("study_scope_A")
        self.assertEqual(snap["sequence"], 1)
        self.assertEqual(snap["ledger_head_sha256"], self.created["event_sha256"])
        self.assertEqual(snap["state"]["source"]["source_sha256"], SRC)
        self.assertFalse(snap["progress"]["source_original_bytes_verified"])
        progress = self.store.progress_receipt("study_scope_A")
        self.assertFalse(progress["terminal"])
        self.assertFalse(progress["engine_quality_certified"])
        self.assertFalse(progress["research_complete"])
        with self.assertRaises(QualityNotProven):
            self.store.issue_terminal_receipt("study_scope_A")
        self.assertEqual(self.store.snapshot("study_scope_A")["sequence"], 1)

    def test_no_unsafe_state_transition_or_hardcoded_approvals(self):
        for name in ["RESEARCH_CLOSURE", "ENGINE_QUALITY_GO", "SOURCE_VERIFIED",
                     "REVIEW_VERIFIED", "EVIDENCE_APPROVED"]:
            with self.subTest(name=name), self.assertRaises(DomainConflict):
                self.store.submit(scope_id="study_scope_A",command_id="attack_command",
                                  expected_head=self.created["event_sha256"],
                                  kind=name,payload={"approved":True})
        self.assertEqual(self.store.snapshot("study_scope_A")["sequence"], 1)

    def test_idempotent_retry_is_same_event_and_no_new_write(self):
        head = self.created["event_sha256"]
        first = self.model(expected=head)
        again = self.model(expected=head)
        self.assertTrue(again["idempotent_replay"])
        self.assertFalse(first["idempotent_replay"])
        self.assertEqual(first["event_sha256"], again["event_sha256"])
        self.assertEqual(self.store.snapshot("study_scope_A")["sequence"], 2)
        with self.assertRaises(IdempotencyConflict):
            self.model(expected=head, value="B")
        self.assertEqual(self.store.snapshot("study_scope_A")["sequence"], 2)

    def test_conflicting_writers_must_not_both_succeed(self):
        stale = self.created["event_sha256"]
        first = self.model(expected=stale)
        other = TransactionStore(self.path)
        with self.assertRaises(ConcurrentHeadChanged):
            other.submit(scope_id="study_scope_A",command_id="second_writer",
                         expected_head=stale,kind="MODEL_RECORDED",
                         payload={"window_id":"W00002", "model":{"meaning":"B"}})
        self.assertTrue(other.is_current(scope_id="study_scope_A",
                                         ledger_head_sha256=first["event_sha256"]))
        self.assertFalse(other.is_current(scope_id="study_scope_A",
                                          ledger_head_sha256=stale))

    def test_cross_cohort_id_and_source_duplicate_fail_closed(self):
        for vid, digest in [(VID, sha256(b"different")),
                            ("F5E4D3C2B1A", SRC)]:
            with self.subTest(video=vid), self.assertRaises(DomainConflict):
                self.store.create_scope(scope_id="other_scope",video_id=vid,
                                        source_sha256=digest,manifest_sha256=MAN,
                                        command_id="create_other")
        self.assertEqual(self.store.snapshot("study_scope_A")["sequence"], 1)

    def test_scope_rebinding_rejected_and_exact_creation_retry(self):
        second = self.store.create_scope(
            scope_id="study_scope_A", video_id=VID, source_sha256=SRC,
            manifest_sha256=MAN, command_id="create_scope_A")
        self.assertTrue(second["idempotent_replay"])
        self.assertEqual(second["event_sha256"], self.created["event_sha256"])
        with self.assertRaises(DomainConflict):
            self.store.create_scope(scope_id="study_scope_A", video_id=VID,
                                    source_sha256=sha256(b"attacker"),
                                    manifest_sha256=MAN, command_id="create_scope_A")

    def test_refuse_floats_bool_as_index_and_uncanonical_models(self):
        for bad in [float("nan"), 1.5, {2:"not string key"}, {"x":2**80}]:
            with self.subTest(bad=repr(bad)), self.assertRaises(InvalidInput):
                self.store.submit(scope_id="study_scope_A",command_id="bad_model",
                                  expected_head=self.created["event_sha256"],
                                  kind="MODEL_RECORDED",
                                  payload={"window_id":"W00001", "model":{"data":bad}})
        self.assertEqual(self.store.snapshot("study_scope_A")["sequence"], 1)

    def test_aba_revision_invalidates_previous_reviews(self):
        first = self.model(key="model_A1")
        r1 = self.store.submit(scope_id="study_scope_A",command_id="review_A1",
                               expected_head=first["event_sha256"],
                               kind="REVIEW_PROPOSED",
                               payload={"window_id":"W00001",
                                        "model_revision_event_sha256":first["event_sha256"],
                                        "review":{"analysis":"provisional review"}})
        self.assertEqual(self.store.snapshot("study_scope_A")["progress"]
                         ["unverified_current_revision_review_proposals"], 1)
        second = self.model(key="model_B",value="B")
        self.assertEqual(self.store.snapshot("study_scope_A")["progress"]
                         ["unverified_current_revision_review_proposals"],0)
        third = self.model(key="model_A2",value="A")
        with self.assertRaises(DomainConflict):
            self.store.submit(scope_id="study_scope_A",command_id="stale_review",
                              expected_head=third["event_sha256"],
                              kind="REVIEW_PROPOSED",
                              payload={"window_id":"W00001",
                                       "model_revision_event_sha256":first["event_sha256"],
                                       "review":{"analysis":"stale proof"}})
        snap = self.store.snapshot("study_scope_A")
        self.assertEqual(snap["state"]["models"]["W00001"]["revision"],3)
        self.assertEqual(snap["progress"]["unverified_current_revision_review_proposals"],0)
        self.assertEqual(snap["progress"]["verified_proofs"],0)
        self.assertEqual(r1["sequence"],3)
        new = self.store.submit(scope_id="study_scope_A",command_id="review_A2",
                                expected_head=third["event_sha256"],
                                kind="REVIEW_PROPOSED",
                                payload={"window_id":"W00001",
                                         "model_revision_event_sha256":third["event_sha256"],
                                         "review":{"analysis":"new review"}})
        self.assertEqual(new["sequence"],6)
        self.assertEqual(self.store.snapshot("study_scope_A")["progress"]
                         ["unverified_current_revision_review_proposals"],1)
        self.assertFalse(self.store.progress_receipt("study_scope_A")["engine_quality_certified"])

    def test_append_rollback_when_failure_after_insert_or_head_update(self):
        old = self.store.snapshot("study_scope_A")
        for stage in ("after_event_insert", "after_head_update"):
            with self.subTest(stage=stage):
                def fault(actual):
                    if actual == stage:
                        raise OSError("injected disk-like error")
                self.store._before_commit = fault
                with self.assertRaises(OSError):
                    self.model(key="failed_model", expected=old["ledger_head_sha256"])
                self.store._before_commit = lambda actual: None
                self.assertEqual(TransactionStore(self.path).snapshot("study_scope_A"), old)
        committed = self.model(key="finally_committed",expected=old["ledger_head_sha256"])
        self.assertEqual(committed["sequence"],2)

    def test_hard_exit_before_commit_rolls_back_and_reopens(self):
        root = Path(__file__).resolve().parents[3]
        script = """
import os,sys
from ire.v6 import TransactionStore
s=TransactionStore(sys.argv[1])
s._before_commit=lambda stage: os._exit(87) if stage==sys.argv[2] else None
s.submit(scope_id='study_scope_A',command_id='crashed_process',
         expected_head=sys.argv[3],kind='MODEL_RECORDED',
         payload={'window_id':'W00001','model':{'meaning':'crash'}})
"""
        for stage in ("after_event_insert", "after_head_update"):
            result = subprocess.run(
                [sys.executable,"-c",script,str(self.path),stage,self.created["event_sha256"]],
                cwd=root, capture_output=True,timeout=15)
            self.assertEqual(result.returncode,87,repr(result.stderr))
            self.assertEqual(TransactionStore(self.path).snapshot("study_scope_A")["sequence"],1)
        self.assertEqual(self.model(key="recovery")["sequence"],2)

    def test_exit_after_commit_is_recoverable(self):
        root = Path(__file__).resolve().parents[3]
        script = """
import os,sys
from ire.v6 import TransactionStore
s=TransactionStore(sys.argv[1]);s.submit(scope_id='study_scope_A',
command_id='committed_before_client_exit',expected_head=sys.argv[2],
kind='MODEL_RECORDED',payload={'window_id':'W00001','model':{'meaning':'durable'}})
os._exit(86)
"""
        result = subprocess.run([sys.executable,"-c",script,str(self.path),
                                 self.created["event_sha256"]],cwd=root,
                                capture_output=True,timeout=15)
        self.assertEqual(result.returncode,86,repr(result.stderr))
        s = TransactionStore(self.path).snapshot("study_scope_A")
        self.assertEqual(s["sequence"],2)
        self.assertEqual(s["state"]["models"]["W00001"]["revision"],1)

    def test_external_chain_tamper_aborts_reads_writes_and_receipt(self):
        self.model()
        con=sqlite3.connect(self.path)
        con.execute("UPDATE events SET event_json=? WHERE scope_id=? AND sequence=?",
                    ('{"type":"RESEARCH_CLOSURE"}',"study_scope_A",2))
        con.commit();con.close()
        other=TransactionStore(self.path)
        with self.assertRaises(LedgerCorrupted):other.snapshot("study_scope_A")
        with self.assertRaises(LedgerCorrupted):other.progress_receipt("study_scope_A")
        with self.assertRaises(LedgerCorrupted):other.issue_terminal_receipt("study_scope_A")
        with self.assertRaises(LedgerCorrupted):
            other.submit(scope_id="study_scope_A",command_id="new_write",
                         expected_head=self.created["event_sha256"],
                         kind="MODEL_RECORDED",
                         payload={"window_id":"W00002","model":{"meaning":"x"}})

    def test_missing_event_or_head_corruption_aborts(self):
        self.model()
        conn=sqlite3.connect(self.path)
        conn.execute("DELETE FROM events WHERE scope_id=? AND sequence=2",("study_scope_A",))
        conn.commit();conn.close()
        with self.assertRaises(LedgerCorrupted):
            TransactionStore(self.path).snapshot("study_scope_A")

    def test_schema_version_change_is_not_silently_migrated(self):
        conn=sqlite3.connect(self.path)
        conn.execute("PRAGMA user_version=999")
        conn.close()
        with self.assertRaises(UnsupportedSchema):
            TransactionStore(self.path)

    def test_snapshot_version_is_historical_not_current_approval(self):
        original=self.store.snapshot("study_scope_A")
        second=TransactionStore(self.path)
        self.model()
        self.assertFalse(second.is_current(scope_id="study_scope_A",
                                           ledger_head_sha256=original["ledger_head_sha256"]))
        self.assertTrue(second.is_current(scope_id="study_scope_A",
                                          ledger_head_sha256=self.store.snapshot("study_scope_A")
                                          ["ledger_head_sha256"]))
        # The original historical snapshot's contents remain self-consistent,
        # but its old head cannot certify current status.
        self.assertEqual(original["sequence"],1)

    def test_threaded_readers_do_not_reuse_memory_state(self):
        reader=TransactionStore(self.path)
        def worker(_):
            return reader.snapshot("study_scope_A")
        for i in range(7):
            self.model(key="model_iter_"+str(i),value=str(i))
            with ThreadPoolExecutor(max_workers=6) as pool:
                snaps=list(pool.map(worker,range(30)))
            self.assertTrue(all(x["sequence"]==i+2 for x in snaps))
        self.assertEqual(len(snaps),30)


if __name__=="__main__":
    unittest.main()
