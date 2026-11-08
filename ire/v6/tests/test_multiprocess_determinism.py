"""Real multiprocessing concurrency, cross-instance replay and deterministic digests."""
from __future__ import annotations

import multiprocessing as mp
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from ire.v6 import ConcurrentHeadChanged, LedgerCorrupted, TransactionStore
from ire.v6.codec import sha256


def _writer(path: str, expected_head: str, key: str,
            ready, go, results):
    try:
        store = TransactionStore(path)
        ready.put(key)
        if not go.wait(10):
            results.put((key, "timeout"))
            return
        r = store.submit(scope_id="research_scope", command_id=key,
                         expected_head=expected_head, kind="MODEL_RECORDED",
                         payload={"window_id":"W00001", "model":{"text":key}})
        results.put((key, "committed", r["event_sha256"]))
    except ConcurrentHeadChanged as exc:
        results.put((key, exc.code))
    except BaseException as exc:
        results.put((key, "UNEXPECTED:" + type(exc).__name__ + ":" + str(exc)))


class MultiprocessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "ledger.db"
        self.store = TransactionStore(self.path)
        self.genesis = self.store.create_scope(
            scope_id="research_scope",video_id="v6TEST00001",
            source_sha256=sha256(b"src"),manifest_sha256=sha256(b"manifest"),
            command_id="create_research_scope")

    def test_two_processes_one_expected_head_only_one_commit(self):
        ctx = mp.get_context("spawn")
        ready, go, results = ctx.Queue(), ctx.Event(), ctx.Queue()
        workers = [ctx.Process(target=_writer,args=(str(self.path),
                    self.genesis["event_sha256"],"writer_"+str(i),ready,go,results))
                   for i in range(2)]
        for p in workers:p.start()
        for _ in workers:ready.get(timeout=10)
        go.set()
        outcome=[results.get(timeout=10) for _ in workers]
        for p in workers:
            p.join(10)
            self.assertEqual(p.exitcode,0)
        self.assertEqual(len([r for r in outcome if r[1]=="committed"]),1, outcome)
        self.assertEqual(len([r for r in outcome if r[1]=="V6_CONCURRENT_HEAD_CHANGED"]),1,outcome)
        self.assertEqual(TransactionStore(self.path).snapshot("research_scope")["sequence"],2)

    def test_three_scopes_independent_replay_and_no_global_state(self):
        for num in range(2,4):
            self.store.create_scope(scope_id=f"scope_video_{num}",
                                    video_id=f"v6TEST0000{num}",
                                    source_sha256=sha256(f"src{num}".encode()),
                                    manifest_sha256=sha256(f"manifest{num}".encode()),
                                    command_id=f"create_video_{num}")
        self.store.submit(scope_id="scope_video_2",command_id="model_only_2",
                          expected_head=self.store.snapshot("scope_video_2")["ledger_head_sha256"],
                          kind="MODEL_RECORDED",payload={"window_id":"W00025",
                                                         "model":{"status":"not approved"}})
        self.assertEqual(self.store.snapshot("research_scope")["sequence"],1)
        self.assertEqual(self.store.snapshot("scope_video_2")["sequence"],2)
        self.assertEqual(self.store.snapshot("scope_video_3")["sequence"],1)
        self.assertEqual(self.store.snapshot("scope_video_2")["state"]["models"]["W00025"]["revision"],1)

    def test_same_commands_independent_databases_yield_equal_hashes(self):
        other = TransactionStore(Path(self.tmp.name)/"clone.db")
        b=other.create_scope(scope_id="research_scope",video_id="v6TEST00001",
                             source_sha256=sha256(b"src"),manifest_sha256=sha256(b"manifest"),
                             command_id="create_research_scope")
        self.assertEqual(self.genesis["event_sha256"],b["event_sha256"])
        sequence=[("model_1","W00001","first"),("model_2","W00025","offset"),
                  ("model_3","W00001","corrected")]
        for key,wid,label in sequence:
            receipts=[]
            for store in [self.store, other]:
                head=store.snapshot("research_scope")["ledger_head_sha256"]
                receipts.append(store.submit(scope_id="research_scope",command_id=key,
                                             expected_head=head,kind="MODEL_RECORDED",
                                             payload={"window_id":wid,"model":{"meaning":label}}))
            self.assertEqual(receipts[0]["event_sha256"],receipts[1]["event_sha256"])
            self.assertEqual(receipts[0]["state_sha256"],receipts[1]["state_sha256"])
        self.assertEqual(self.store.snapshot("research_scope"),other.snapshot("research_scope"))

    def test_corruption_of_recorded_state_digest_fail_closed(self):
        self.store.submit(scope_id="research_scope",command_id="model_1",
                          expected_head=self.genesis["event_sha256"],kind="MODEL_RECORDED",
                          payload={"window_id":"W00001","model":{"meaning":"first"}})
        con = sqlite3.connect(self.path)
        try:
            con.execute("UPDATE events SET state_sha256=? WHERE scope_id=? AND sequence=2",
                        ("e"*64,"research_scope"))
            con.commit()
        finally:
            con.close()
        with self.assertRaises(LedgerCorrupted):
            self.store.snapshot("research_scope")
        with self.assertRaises(LedgerCorrupted):
            self.store.submit(scope_id="research_scope",command_id="future_write",
                              expected_head="e"*64,kind="MODEL_RECORDED",
                              payload={"window_id":"W00002","model":{"meaning":"bad"}})


if __name__=="__main__":unittest.main()
