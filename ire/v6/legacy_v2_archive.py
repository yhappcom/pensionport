"""Read-only, full-chain legacy V2 official completion archive verification.

Old scope-completion flags are retained only as *historical events*. Nothing
here migrates records to the current reducer, approves finance, or publishes
private model/SRT content. Even a valid old hash chain may be semantically wrong.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from urllib.parse import quote

from .codec import ZERO_SHA, canonical, json_digest, require_identifier, sha256
from .errors import DomainConflict, InvalidInput, LedgerCorrupted, UnsupportedSchema
from .legacy_v2_state_machine import empty_state, reduce_event

EVENT_SCHEMA = "IRE_V6_EVENT_V1"
LEGACY_USER_VERSION = 4
MAX_EVENTS = 100000


def read_legacy_v2_archive(database_path: str | Path, scope_id: str) -> dict:
    """Verify every legacy V2 event with its *original* reducer, never rewrite.

    A historical V2 report marked research_complete=True is not accepted as
    current semantic completion or independent recall.
    """
    scope_id = require_identifier(scope_id, name="LEGACY_SCOPE")
    path = Path(database_path)
    if not path.is_file() or path.is_symlink() or path.suffix != ".db":
        raise InvalidInput("LEGACY_DB_READONLY_FILE_REQUIRED")
    uri = "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True, isolation_level=None)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA query_only=ON")
        con.execute("BEGIN")
        try:
            if con.execute("PRAGMA user_version").fetchone()[0] != LEGACY_USER_VERSION:
                raise UnsupportedSchema("LEGACY_V2_DB_SCHEMA_UNSUPPORTED")
            row = con.execute("SELECT * FROM scopes WHERE scope_id=?", (scope_id,)).fetchone()
            if row is None:
                raise InvalidInput("LEGACY_SCOPE_NOT_FOUND")
            events = con.execute(
                "SELECT * FROM events WHERE scope_id=? ORDER BY sequence",
                (scope_id,)).fetchall()
            if not 1 <= len(events) <= MAX_EVENTS:
                raise UnsupportedSchema("LEGACY_V2_EVENT_CENSUS_UNSUPPORTED")
            state, head, genesis = empty_state(), ZERO_SHA, None
            old_terminals = 0
            for sequence, record in enumerate(events, 1):
                raw = record["event_json"]
                try:
                    event = json.loads(raw)
                    if type(event) is not dict or raw.encode("utf-8") != canonical(event):
                        raise ValueError("NONCANONICAL_LEGACY_EVENT")
                except (InvalidInput, ValueError, UnicodeError, TypeError) as exc:
                    raise LedgerCorrupted("LEGACY_V2_EVENT_NONCANONICAL") from exc
                if set(event) != {
                    "schema", "scope_id", "sequence", "prev_event_sha256",
                    "command_id", "command_sha256", "type", "payload"
                }:
                    raise LedgerCorrupted("LEGACY_V2_EVENT_SHAPE")
                if (event["schema"] != EVENT_SCHEMA or
                    event["scope_id"] != scope_id or
                    type(event["sequence"]) is not int or
                    event["sequence"] != sequence or
                    record["sequence"] != sequence or
                    event["prev_event_sha256"] != head or
                    record["prev_sha256"] != head or
                    event["command_id"] != record["command_id"] or
                    event["command_sha256"] != record["command_sha256"] or
                    sha256(raw.encode("utf-8")) != record["event_sha256"]):
                    raise LedgerCorrupted("LEGACY_V2_EVENT_CHAIN_INVALID")
                kind, payload = event["type"], event["payload"]
                if kind in ("TERMINAL_AUDIT_RECORDED", "TERMINAL_OFFICIAL_COMPLETION_RECORDED"):
                    if payload.get("base_head_sha256") != head:
                        raise LedgerCorrupted("LEGACY_V2_TERMINAL_BASE_DRIFT")
                fingerprint = json_digest({
                    "kind":kind,"payload":payload,"expected_head":head
                })
                if fingerprint != record["command_sha256"]:
                    raise LedgerCorrupted("LEGACY_V2_COMMAND_DIGEST_DRIFT")
                try:
                    after = reduce_event(state, kind, payload, record["event_sha256"])
                except (DomainConflict, InvalidInput, TypeError, KeyError) as exc:
                    raise LedgerCorrupted("LEGACY_V2_REDUCER_REJECTED") from exc
                if json_digest(after) != record["state_sha256"]:
                    raise LedgerCorrupted("LEGACY_V2_DERIVED_STATE_DIGEST_DRIFT")
                if sequence == 1:
                    if kind != "SCOPE_DECLARED":
                        raise LedgerCorrupted("LEGACY_V2_GENESIS_REQUIRED")
                    genesis = payload
                elif kind == "SCOPE_DECLARED":
                    raise LedgerCorrupted("LEGACY_V2_DUPLICATE_GENESIS")
                if kind == "TERMINAL_OFFICIAL_COMPLETION_RECORDED":
                    if payload["report"].get("outcome") != "OFFICIAL_SOURCE_SCOPED_COMPLETE":
                        raise LedgerCorrupted("LEGACY_V2_UNEXPECTED_TERMINAL_OUTCOME")
                    old_terminals += 1
                state, head = after, record["event_sha256"]
            if (head != row["head_sha256"] or len(events) != row["sequence"] or
                genesis != {"video_id":row["video_id"],
                           "source_sha256":row["source_sha256"],
                           "manifest_sha256":row["manifest_sha256"]}):
                raise LedgerCorrupted("LEGACY_V2_HEAD_OR_GENESIS_DRIFT")
            if old_terminals == 0:
                raise UnsupportedSchema("NOT_A_V2_OFFICIAL_TERMINAL_ARCHIVE")
            result = {
                "schema":"IRE_V6_LEGACY_V2_READONLY_ARCHIVE_VERIFIED_V1",
                "scope_id":scope_id,"legacy_user_version":LEGACY_USER_VERSION,
                "event_count":len(events),"historical_head_sha256":head,
                "old_official_terminal_event_count":old_terminals,
                "legacy_hash_chain_and_reducer_verified":True,
                "old_complete_flags_present_but_not_trusted":True,
                "historical_source_bytes_reverified_this_call":False,
                "historical_semantic_truth_verified":False,
                "current_research_complete":False,
                "current_scoped_rule_approved":False,
                "direct_resume_or_live_write_allowed":False,
                "lossless_migration_completed":False,
                "requires_separate_versioned_migration":True,
                "p0_go":False,
            }
            con.execute("COMMIT")
            return result
        except BaseException:
            if con.in_transaction:
                con.execute("ROLLBACK")
            raise
    finally:
        con.close()
