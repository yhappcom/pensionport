"""Read-only historical V6 official terminal V2 event-log bridge.

Historical 2026-11-08 V2 reducer could set research_report_closed=True on a
model-only claim census. This module replays the historical transition to
CHECK old stored state digests only; every returned projection is NO-GO.
It never migrates, writes, imports private SRT, or re-approves historic facts.
"""
from __future__ import annotations

import json
import sqlite3
from copy import deepcopy
from pathlib import Path

from .codec import ZERO_SHA, canonical, json_digest, require_hash, require_identifier, sha256
from .errors import DomainConflict, InvalidInput, LedgerCorrupted, UnsupportedSchema
from .official_completion import LAW_RULE_ID, LAW_SOURCE_SHA256
from .state_machine import empty_state, reduce_event
from .store import EVENT_SCHEMA, SCHEMA_VERSION


def _legacy_official_transition(state: dict, payload: dict, event_hash: str) -> dict:
    """Reconstruct the exact historical V2 *state transition*, not its trust."""
    if (type(payload) is not dict or
        set(payload) != {"schema", "base_head_sha256", "base_state_sha256",
                         "private_input_sha256", "report"} or
        payload.get("schema") != "IRE_V6_OFFICIAL_TERMINAL_EVENT_V2" or
        type(payload.get("report")) is not dict):
        raise InvalidInput("LEGACY_V2_OFFICIAL_EVENT_SCHEMA")
    require_hash(payload["base_head_sha256"], "LEGACY_V2_BASE_HEAD")
    require_hash(payload["private_input_sha256"], "LEGACY_V2_INPUT_SHA")
    report = payload["report"]
    revisions = json_digest([
        {"window_id": wid, "revision_event_sha256": rev["revision_event_sha256"]}
        for wid, rev in sorted(state["models"].items())])
    if (payload["base_state_sha256"] != json_digest(state)
        or state["research_report_closed"] is not False
        or report.get("schema") != "IRE_V6_OFFICIAL_SCOPE_TERMINAL_REPORT_V2"
        or report.get("source_sha256") != state["source"]["source_sha256"]
        or report.get("manifest_sha256") != state["source"]["manifest_sha256"]
        or report.get("rule_id") != LAW_RULE_ID
        or report.get("official_document_sha256") != LAW_SOURCE_SHA256
        or report.get("model_revision_set_sha256") != revisions
        or report.get("window_count") != len(state["models"])
        or type(report.get("officially_verified_fact_count")) is not int
        or report["officially_verified_fact_count"] < 1
        or report.get("scope_fully_modelled") is not True
        or report.get("all_registered_factual_assertions_verified") is not True
        or report.get("historical_official_source_bytes_verified") is not True
        or report.get("independent_human_review_required") is not False
        or report.get("general_semantic_recall_certified") is not False
        or report.get("legacy116_semantic_merge_approved") is not False
        or report.get("outcome") != "OFFICIAL_SOURCE_SCOPED_COMPLETE"
        or report.get("research_complete") is not True
        or report.get("engine_quality_certified") is not False
        or report.get("p0_go") is not False):
        raise InvalidInput("LEGACY_V2_TERMINAL_HISTORIC_CONTRACT_MISMATCH")
    after = deepcopy(state)
    after["terminal_audits"].append({
        "event_sha256":event_hash,
        "base_head_sha256":payload["base_head_sha256"],
        "base_state_sha256":payload["base_state_sha256"],
        "report_sha256":json_digest(report),
        "outcome":"OFFICIAL_SOURCE_SCOPED_COMPLETE",
    })
    after["research_report_closed"] = True  # Historical bytes ONLY; never output as GO.
    return after


def inspect_historical_v2_store(database_path: str | Path, *, scope_id: str) -> dict:
    """Verify old event/state digests against a frozen V2 terminal reducer.

    Opens SQLITE mode=ro, PRAGMA query_only, and a consistent BEGIN snapshot.
    Historical user_version=4 is checked explicitly; no schema migration.
    NEVER expose historical research_complete=true as a current decision.
    """
    scope_id = require_identifier(scope_id, name="LEGACY_V2_SCOPE_ID")
    path = Path(database_path)
    if path.suffix != ".db" or not path.is_file():
        raise InvalidInput("LEGACY_V2_DB_FILE_REQUIRED")
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro",
                                 uri=True, isolation_level=None)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        try:
            if connection.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
                raise UnsupportedSchema("LEGACY_V2_SCHEMA_MIGRATION_FORBIDDEN")
            meta=connection.execute("SELECT * FROM scopes WHERE scope_id=?",
                                     (scope_id,)).fetchone()
            if meta is None:
                raise InvalidInput("LEGACY_V2_SCOPE_NOT_FOUND")
            rows=connection.execute(
                "SELECT * FROM events WHERE scope_id=? ORDER BY sequence",
                (scope_id,)).fetchall()
            prior = ZERO_SHA
            state = empty_state()
            old_terminals = 0
            for index,row in enumerate(rows,1):
                raw=row["event_json"]
                try:
                    event=json.loads(raw)
                except (TypeError,ValueError) as err:
                    raise LedgerCorrupted("LEGACY_V2_JSON_PARSE_FAILURE") from err
                if (type(event) is not dict or
                    raw.encode("utf8") != canonical(event) or
                    set(event) != {"schema","scope_id","sequence",
                                   "prev_event_sha256","command_id",
                                   "command_sha256","type","payload"} or
                    event["schema"] != EVENT_SCHEMA or
                    event["scope_id"] != scope_id or
                    type(event["sequence"]) is not int or
                    event["sequence"] != index or row["sequence"] != index or
                    event["prev_event_sha256"] != prior or
                    row["prev_sha256"] != prior or
                    event["command_id"] != row["command_id"] or
                    event["command_sha256"] != row["command_sha256"] or
                    sha256(raw.encode("utf8")) != row["event_sha256"] or
                    event["command_sha256"] != json_digest({
                        "kind":event["type"],"payload":event["payload"],
                        "expected_head":prior,
                    })):
                    raise LedgerCorrupted("LEGACY_V2_EVENT_CHAIN_MISMATCH")
                try:
                    if (event["type"] == "TERMINAL_OFFICIAL_COMPLETION_RECORDED" and
                        event["payload"].get("report",{}).get("outcome") ==
                        "OFFICIAL_SOURCE_SCOPED_COMPLETE"):
                        if event["payload"]["base_head_sha256"] != prior:
                            raise LedgerCorrupted("LEGACY_V2_TERMINAL_BASE_HEAD_MISMATCH")
                        state=_legacy_official_transition(
                            state,event["payload"],row["event_sha256"])
                        old_terminals += 1
                    else:
                        if (event["type"] in
                            ("TERMINAL_AUDIT_RECORDED",
                             "TERMINAL_OFFICIAL_COMPLETION_RECORDED") and
                            event["payload"].get("base_head_sha256") != prior):
                            raise LedgerCorrupted("LEGACY_V2_BASE_HEAD_DRIFT")
                        state=reduce_event(state,event["type"],
                                           event["payload"],row["event_sha256"])
                except (InvalidInput,DomainConflict,TypeError,KeyError,IndexError) as err:
                    raise LedgerCorrupted("LEGACY_V2_REDUCER_REPLAY_FAILED") from err
                if json_digest(state) != row["state_sha256"]:
                    raise LedgerCorrupted("LEGACY_V2_STATE_DIGEST_MISMATCH")
                if index == 1 and event["type"] != "SCOPE_DECLARED":
                    raise LedgerCorrupted("LEGACY_V2_GENESIS_MISSING")
                prior=row["event_sha256"]
            if (not rows or old_terminals == 0 or prior != meta["head_sha256"]
                or len(rows) != meta["sequence"]):
                raise LedgerCorrupted("LEGACY_V2_TERMINAL_OR_FINAL_HEAD_MISMATCH")
            result={
                "schema":"IRE_V6_HISTORIC_V2_READONLY_REPLAY_V1",
                "scope_id":scope_id,
                "source_sha256":meta["source_sha256"],
                "manifest_sha256":meta["manifest_sha256"],
                "legacy_database_version":SCHEMA_VERSION,
                "historical_event_count":len(rows),
                "historical_v2_official_terminal_count":old_terminals,
                "historical_event_chain_and_state_digest_verified":True,
                "historical_policy_version":"2026-11-08 V2, vulnerable research closure",
                "historical_model_only_completion_is_not_trusted":True,
                "historic_research_complete_may_be_true":True,
                "current_research_complete":False,
                "current_official_rule_verified":False,
                "current_source_speaker_meaning_verified":False,
                "current_independent_semantic_recall_certified":False,
                "current_engine_quality_certified":False,
                "current_p0_go":False,
                "write_performed":False,
                "migration_performed":False,
                "requires_owner_source_first_revalidation":True,
            }
            connection.execute("COMMIT")
            return result
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
    finally:
        connection.close()
