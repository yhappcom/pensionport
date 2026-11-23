"""Issue #50 synthetic historic V2 SQLite replay; no actual private DB material."""
from __future__ import annotations
import copy
import sqlite3
import unittest

from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.errors import LedgerCorrupted
from ire.v6.legacy_v2_readonly import inspect_historical_v2_store
from ire.v6.tests.test_official_completion import OfficialTerminalV2Tests, SCOPE
from ire.v6.store import TransactionStore

HISTORIC_FIELDS = (
    "schema", "source_sha256", "manifest_sha256", "owner_inventory_sha256",
    "rule_id", "official_document_sha256", "verified_as_of", "window_count",
    "model_revision_set_sha256", "reviewed_atom_count",
    "officially_verified_fact_count", "replayed_proof_set_sha256",
    "replayed_finance_set_sha256", "determination_sha256",
    "scope_fully_modelled", "independent_human_review_required",
    "historical_official_source_bytes_verified",
    "general_semantic_recall_certified", "legacy116_semantic_merge_approved",
    "outcome", "research_complete", "engine_quality_certified", "p0_go",
)


class Issue50V2HistoricalReplayTests(unittest.TestCase):
    setUp = OfficialTerminalV2Tests.setUp
    head = OfficialTerminalV2Tests.head
    setup_recorded = OfficialTerminalV2Tests.setup_recorded
    decision = OfficialTerminalV2Tests.decision
    args = OfficialTerminalV2Tests.args

    def make_historic_v2_log(self):
        """Build a V2-shaped *synthetic* row with exact historical state hash."""
        self.setup_recorded()
        latest=self.store.issue_terminal_receipt(**self.args())
        state=self.store.snapshot(SCOPE)["state"]
        with sqlite3.connect(self.store.path) as con:
            con.row_factory=sqlite3.Row
            row=con.execute(
                "SELECT * FROM events WHERE scope_id=? AND event_sha256=?",
                (SCOPE,latest["event_sha256"])).fetchone()
            event=__import__("json").loads(row["event_json"])
            report=event["payload"]["report"]
            old={key:report[key] for key in HISTORIC_FIELDS}
            old["correctly_classified_nonfact_count"]=report["model_labelled_nonfact_count"]
            old.update({
                "all_registered_factual_assertions_verified":True,
                "outcome":"OFFICIAL_SOURCE_SCOPED_COMPLETE",
                "research_complete":True,
            })
            event["payload"]["report"]=old
            event["command_sha256"]=json_digest({
                "kind":event["type"],
                "payload":event["payload"],
                "expected_head":event["prev_event_sha256"],
            })
            raw=canonical(event)
            digest=sha256(raw)
            historic_state=copy.deepcopy(state)
            historic_state["terminal_audits"][-1].update({
                "event_sha256":digest,
                "report_sha256":json_digest(old),
                "outcome":"OFFICIAL_SOURCE_SCOPED_COMPLETE",
            })
            historic_state["research_report_closed"]=True
            con.execute("UPDATE events SET event_json=?,command_sha256=?,"
                        "event_sha256=?,state_sha256=? WHERE scope_id=? AND sequence=?",
                        (raw.decode("utf8"),event["command_sha256"],digest,
                         json_digest(historic_state),SCOPE,row["sequence"]))
            con.execute("UPDATE scopes SET head_sha256=? WHERE scope_id=?",
                        (digest,SCOPE))
            con.commit()

    def test_01_old_v2_snapshot_fails_closed_under_v3_live_reducer(self):
        self.make_historic_v2_log()
        with self.assertRaisesRegex(LedgerCorrupted,"EVENT_REDUCER_REJECTED"):
            TransactionStore(self.store.path).snapshot(SCOPE)

    def test_02_historic_v2_state_digest_readonly_replay_and_no_go(self):
        self.make_historic_v2_log()
        before=self.store.path.read_bytes()
        view=inspect_historical_v2_store(self.store.path,scope_id=SCOPE)
        self.assertEqual(view["historical_v2_official_terminal_count"],1)
        self.assertTrue(view["historical_event_chain_and_state_digest_verified"])
        self.assertTrue(view["historical_model_only_completion_is_not_trusted"])
        self.assertFalse(view["current_research_complete"])
        self.assertFalse(view["current_official_rule_verified"])
        self.assertFalse(view["current_source_speaker_meaning_verified"])
        self.assertFalse(view["current_engine_quality_certified"])
        self.assertFalse(view["current_p0_go"])
        self.assertFalse(view["write_performed"])
        self.assertFalse(view["migration_performed"])
        self.assertEqual(self.store.path.read_bytes(),before)

    def test_03_old_terminal_tamper_rejected(self):
        self.make_historic_v2_log()
        with sqlite3.connect(self.store.path) as con:
            con.execute("UPDATE events SET event_json=replace(event_json, ?, ?) "
                        "WHERE scope_id=? AND sequence=(SELECT MAX(sequence) "
                        "FROM events WHERE scope_id=?)",
                        ("OFFICIAL_SOURCE_SCOPED_COMPLETE",
                         "OFFICIAL_FALSE_REPLAY",SCOPE,SCOPE))
            con.commit()
        with self.assertRaisesRegex(LedgerCorrupted,"LEGACY_V2_EVENT_CHAIN_MISMATCH"):
            inspect_historical_v2_store(self.store.path,scope_id=SCOPE)

    def test_04_new_v3_history_must_not_be_mislabelled_v2(self):
        self.setup_recorded()
        self.store.issue_terminal_receipt(**self.args())
        with self.assertRaisesRegex(LedgerCorrupted,"LEGACY_V2_TERMINAL_OR_FINAL_HEAD_MISMATCH"):
            inspect_historical_v2_store(self.store.path,scope_id=SCOPE)

    def test_05_historic_v2_wrong_scope_rejected(self):
        self.make_historic_v2_log()
        from ire.v6.errors import InvalidInput
        with self.assertRaisesRegex(InvalidInput,"LEGACY_V2_SCOPE_NOT_FOUND"):
            inspect_historical_v2_store(self.store.path,scope_id="not_this_scope")


if __name__=="__main__":
    unittest.main()
