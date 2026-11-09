"""Historical V2 ledger digest compatibility, synthetic SRT and pinned law."""
from __future__ import annotations

import copy
import json
import sqlite3
import unittest
from contextlib import closing

from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.errors import LedgerCorrupted, UnsupportedSchema
from ire.v6.legacy_v2_state_machine import empty_state, reduce_event
from ire.v6.legacy_v2_archive import read_legacy_v2_archive
from ire.v6.tests.test_official_completion import OfficialTerminalV2Tests


class LegacyV2ArchiveTests(unittest.TestCase):
    def make_legacy(self):
        fixture = OfficialTerminalV2Tests(
            methodName="test_true_official_scoped_complete_and_reopened_sqlite")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.setup_recorded()
        current=fixture.store.issue_terminal_receipt(**fixture.args())
        db=fixture.store.path
        with closing(sqlite3.connect(db)) as con:
            con.row_factory=sqlite3.Row
            events=con.execute(
                "SELECT * FROM events WHERE scope_id=? ORDER BY sequence",
                ("official_v2_scope",)
            ).fetchall()
            # Simulate a real-format legacy V2 completion event, preserving
            # all preceding legitimate source/proof/finance event bytes.
            prev=empty_state()
            for row in events[:-1]:
                ev=json.loads(row["event_json"])
                prev=reduce_event(prev,ev["type"],ev["payload"],row["event_sha256"])
                self.assertEqual(json_digest(prev),row["state_sha256"])
            last=events[-1]
            event=json.loads(last["event_json"])
            self.assertEqual(event["type"],"TERMINAL_OFFICIAL_COMPLETION_RECORDED")
            report=copy.deepcopy(event["payload"]["report"])
            report["correctly_classified_nonfact_count"]=report.pop(
                "model_labelled_nonfact_count")
            for key in list(report):
                if (key.startswith("source_first_") or
                    key in {"source_claim_census_independently_verified",
                            "nonfact_roles_independently_verified",
                            "source_speaker_meaning_verified",
                            "official_statute_rule_text_verified"}):
                    report.pop(key)
            report["all_registered_factual_assertions_verified"]=True
            report["outcome"]="OFFICIAL_SOURCE_SCOPED_COMPLETE"
            report["research_complete"]=True
            event["payload"]["report"]=report
            fp=json_digest({"kind":event["type"],
                             "payload":event["payload"],
                             "expected_head":event["prev_event_sha256"]})
            event["command_sha256"]=fp
            encoded=canonical(event)
            new_sha=sha256(encoded)
            after=reduce_event(prev,event["type"],event["payload"],new_sha)
            self.assertTrue(after["research_report_closed"])
            con.execute(
                "UPDATE events SET event_json=?, event_sha256=?, command_sha256=?,"
                " state_sha256=? WHERE scope_id=? AND sequence=?",
                (encoded.decode(),new_sha,fp,json_digest(after),
                 "official_v2_scope",last["sequence"]))
            con.execute("UPDATE scopes SET head_sha256=? WHERE scope_id=?",
                        (new_sha,"official_v2_scope"))
            con.commit()
        return db,fixture

    def test_old_event_chain_digest_read_only_and_never_reapproved(self):
        db,fixture=self.make_legacy()
        result=read_legacy_v2_archive(db,"official_v2_scope")
        self.assertTrue(result["legacy_hash_chain_and_reducer_verified"])
        self.assertEqual(result["old_official_terminal_event_count"],1)
        self.assertFalse(result["current_research_complete"])
        self.assertFalse(result["current_scoped_rule_approved"])
        self.assertFalse(result["direct_resume_or_live_write_allowed"])
        self.assertFalse(result["lossless_migration_completed"])
        self.assertNotIn("연금계좌에서",json.dumps(result,ensure_ascii=False))
        with self.assertRaises(LedgerCorrupted):
            fixture.store.snapshot("official_v2_scope")

    def test_wrong_digest_in_historical_archive_rejected(self):
        db,_=self.make_legacy()
        with closing(sqlite3.connect(db)) as con:
            con.execute("UPDATE events SET state_sha256=? WHERE scope_id=? AND sequence=2",
                        ("0"*64,"official_v2_scope"))
            con.commit()
        with self.assertRaisesRegex(LedgerCorrupted,"STATE_DIGEST"):
            read_legacy_v2_archive(db,"official_v2_scope")

    def test_modern_ledger_without_old_terminal_is_not_legacy_archive(self):
        fixture=OfficialTerminalV2Tests(methodName="test_true_official_scoped_complete_and_reopened_sqlite")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.setup_recorded()
        fixture.store.issue_terminal_receipt(**fixture.args())
        with self.assertRaises(LedgerCorrupted):
            read_legacy_v2_archive(fixture.store.path,"official_v2_scope")


if __name__=="__main__":
    unittest.main()
