"""IRE V6-1 SQLite event transaction kernel (no research approval authority).

Atomic commit: BEGIN IMMEDIATE -> validate/replay -> insert event -> update
head -> COMMIT. Every reader uses a single SQLite snapshot and verifies the
entire chain before returning a typed, version-bound projection. No in-memory
state is authoritative. A prior successful read is never reused as a cache.

This implements software durability and consistency, not source provenance,
reviewer independence, financial truth, digital signatures, or P0 GO.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Callable

from .codec import (ZERO_SHA, VIDEO, canonical, json_digest, require_hash,
                    require_identifier, sha256)
from .errors import (ConcurrentHeadChanged, DomainConflict,
                     IdempotencyConflict, InvalidInput, LedgerCorrupted,
                     QualityNotProven, UnsupportedSchema)
from .state_machine import empty_state, progress, reduce_event

SCHEMA_VERSION = 4
EVENT_SCHEMA = "IRE_V6_EVENT_V1"
EVENT_RECEIPT_SCHEMA = "IRE_V6_EVENT_COMMIT_V1"
SNAPSHOT_SCHEMA = "IRE_V6_VERIFIED_SNAPSHOT_V1"


class TransactionStore:
    """Single-host, local-disk, multi-process SQLite V6-1 event store.

    WAL must not be placed on a network filesystem or exposed to an untrusted
    local writer. Use an access-controlled private directory for research data.
    The constructor neither imports historical records nor starts V5 execution.
    """

    def __init__(self, database_path: str | Path, *, timeout_seconds: float = 15):
        self.path = Path(database_path)
        if self.path.name in ("", ".", "..") or self.path.suffix != ".db":
            raise InvalidInput("DATABASE_PATH_REQUIRES_DB_FILE")
        if not (0.1 <= timeout_seconds <= 120):
            raise InvalidInput("DATABASE_TIMEOUT_INVALID")
        self.timeout = timeout_seconds
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.path.parent.is_symlink():
            raise InvalidInput("DATABASE_PARENT_SYMLINK_NOT_ALLOWED")
        if self.path.is_symlink():
            raise InvalidInput("DATABASE_SYMLINK_NOT_ALLOWED")
        if os.name == "posix":
            parent_stat = self.path.parent.stat()
            if parent_stat.st_uid != os.getuid() or parent_stat.st_mode & 0o077:
                raise InvalidInput("PRIVATE_DATABASE_DIRECTORY_REQUIRED")
            if self.path.exists():
                st = self.path.stat()
                if st.st_uid != os.getuid() or st.st_mode & 0o077:
                    raise InvalidInput("INSECURE_EXISTING_DATABASE_PERMISSIONS")
        self._init_db()

    def _connection(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path, timeout=self.timeout,
                              isolation_level=None)
        try:
            con.execute("PRAGMA foreign_keys = ON")
            con.execute("PRAGMA synchronous = FULL")
            con.execute(f"PRAGMA busy_timeout = {int(self.timeout * 1000)}")
            con.row_factory = sqlite3.Row
            return con
        except BaseException:
            con.close()
            raise

    def _init_db(self):
        con = self._connection()
        try:
            # journal_mode is set before opening a transaction.
            mode = con.execute("PRAGMA journal_mode = WAL").fetchone()[0]
            if str(mode).lower() != "wal":
                raise UnsupportedSchema("LOCAL_WAL_JOURNAL_NOT_AVAILABLE")
            con.execute("BEGIN IMMEDIATE")
            try:
                version = con.execute("PRAGMA user_version").fetchone()[0]
                # V6-1 state digests cannot be silently reinterpreted by V6-2.
                # Require explicit, future migration for v1 stores.
                if version not in (0, SCHEMA_VERSION):
                    raise UnsupportedSchema("V6_STORE_VERSION_MIGRATION_REQUIRED")
                con.execute("""
                    CREATE TABLE IF NOT EXISTS scopes(
                        scope_id TEXT NOT NULL PRIMARY KEY,
                        video_id TEXT NOT NULL UNIQUE,
                        source_sha256 TEXT NOT NULL UNIQUE,
                        manifest_sha256 TEXT NOT NULL,
                        sequence INTEGER NOT NULL,
                        head_sha256 TEXT NOT NULL
                    )
                """)
                con.execute("""
                    CREATE TABLE IF NOT EXISTS events(
                        scope_id TEXT NOT NULL,
                        sequence INTEGER NOT NULL,
                        command_id TEXT NOT NULL,
                        command_sha256 TEXT NOT NULL,
                        prev_sha256 TEXT NOT NULL,
                        event_sha256 TEXT NOT NULL,
                        event_json TEXT NOT NULL,
                        state_sha256 TEXT NOT NULL,
                        PRIMARY KEY(scope_id, sequence),
                        UNIQUE(scope_id, command_id),
                        FOREIGN KEY(scope_id) REFERENCES scopes(scope_id)
                    )
                """)
                con.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
                con.execute("COMMIT")
            except BaseException:
                con.execute("ROLLBACK")
                raise
        finally:
            con.close()
        # Fail closed rather than treating permission errors as best effort.
        # On POSIX only the owning user may access private research metadata.
        if os.name == "posix":
            os.chmod(self.path, 0o600)

    def _replay(self, con: sqlite3.Connection, scope_id: str):
        scope = con.execute("SELECT * FROM scopes WHERE scope_id=?",
                            (scope_id,)).fetchone()
        if scope is None:
            raise InvalidInput("SCOPE_UNKNOWN")
        if con.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
            raise UnsupportedSchema("SCHEMA_CHANGED")
        state = empty_state()
        prev = ZERO_SHA
        seq = 0
        genesis = None
        rows = con.execute(
            "SELECT * FROM events WHERE scope_id=? ORDER BY sequence",
            (scope_id,)
        ).fetchall()
        for row in rows:
            seq += 1
            raw = row["event_json"]
            try:
                event = json.loads(raw)
                if type(event) is not dict or raw.encode("utf-8") != canonical(event):
                    raise ValueError("JSON_NOT_CANONICAL")
            except (ValueError, TypeError, InvalidInput, UnicodeError) as exc:
                raise LedgerCorrupted("EVENT_JSON_INVALID_OR_NONCANONICAL") from exc
            if set(event) != {"schema", "scope_id", "sequence",
                              "prev_event_sha256", "command_id",
                              "command_sha256", "type", "payload"}:
                raise LedgerCorrupted("EVENT_SHAPE_MISMATCH")
            if (event["schema"] != EVENT_SCHEMA or
                event["scope_id"] != scope_id or
                type(event["sequence"]) is not int or
                event["sequence"] != seq or row["sequence"] != seq or
                event["prev_event_sha256"] != prev or
                row["prev_sha256"] != prev or
                event["command_id"] != row["command_id"] or
                event["command_sha256"] != row["command_sha256"] or
                sha256(raw.encode("utf-8")) != row["event_sha256"]):
                raise LedgerCorrupted("EVENT_CHAIN_OR_ROW_MISMATCH")
            if (event["type"] in ("TERMINAL_AUDIT_RECORDED", "TERMINAL_OFFICIAL_COMPLETION_RECORDED") and
                event["payload"].get("base_head_sha256")!=prev):
                raise LedgerCorrupted("AUDIT_BASE_HEAD_NOT_PREVIOUS_EVENT")
            fingerprint = json_digest({
                "kind": event["type"], "payload": event["payload"],
                "expected_head": prev,
            })
            if fingerprint != row["command_sha256"]:
                raise LedgerCorrupted("COMMAND_FINGERPRINT_MISMATCH")
            try:
                state = reduce_event(state, event["type"],
                                     event["payload"], row["event_sha256"])
            except (DomainConflict, InvalidInput, TypeError, KeyError) as exc:
                raise LedgerCorrupted("EVENT_REDUCER_REJECTED:" + str(exc)) from exc
            if json_digest(state) != row["state_sha256"]:
                raise LedgerCorrupted("DERIVED_STATE_DIGEST_MISMATCH")
            if seq == 1:
                if event["type"] != "SCOPE_DECLARED":
                    raise LedgerCorrupted("GENESIS_MISSING")
                genesis = event["payload"]
            elif event["type"] == "SCOPE_DECLARED":
                raise LedgerCorrupted("DUPLICATE_GENESIS")
            prev = row["event_sha256"]
        if (seq == 0 or seq != scope["sequence"] or prev != scope["head_sha256"]
            or genesis != {"video_id": scope["video_id"],
                           "source_sha256": scope["source_sha256"],
                           "manifest_sha256": scope["manifest_sha256"]}):
            raise LedgerCorrupted("HEAD_OR_GENESIS_MISMATCH")
        return state, seq, prev

    def _write_event(self, con: sqlite3.Connection, *, scope_id: str,
                     seq: int, prev: str, command_id: str,
                     kind: str, payload: dict, state: dict):
        fingerprint = json_digest({"kind": kind, "payload": payload,
                                   "expected_head": prev})
        body = {"schema": EVENT_SCHEMA, "scope_id": scope_id,
                "sequence": seq, "prev_event_sha256": prev,
                "command_id": command_id, "command_sha256": fingerprint,
                "type": kind, "payload": payload}
        raw = canonical(body)
        event_hash = sha256(raw)
        after = reduce_event(state, kind, payload, event_hash)
        after_hash = json_digest(after)
        con.execute("INSERT INTO events(scope_id,sequence,command_id,command_sha256,"
                    "prev_sha256,event_sha256,event_json,state_sha256) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (scope_id, seq, command_id, fingerprint, prev, event_hash,
                     raw.decode("utf-8"), after_hash))
        self._before_commit("after_event_insert")
        count = con.execute("UPDATE scopes SET sequence=?,head_sha256=? "
                            "WHERE scope_id=? AND sequence=? AND head_sha256=?",
                            (seq, event_hash, scope_id, seq-1, prev)).rowcount
        if count != 1:
            raise ConcurrentHeadChanged("ATOMIC_HEAD_COMPARE_AND_SWAP_FAILED")
        self._before_commit("after_head_update")
        return self._receipt(scope_id, seq, event_hash, after_hash,
                             command_id, idempotent=False)

    def _before_commit(self, stage: str) -> None:
        """Test seam for deterministic crash injection; default has no effects."""
        return None

    @staticmethod
    def _receipt(scope_id, seq, head, state_hash, command_id, *, idempotent):
        return {"schema": EVENT_RECEIPT_SCHEMA,
                "scope_id": scope_id, "sequence": seq,
                "event_sha256": head, "state_sha256": state_hash,
                "command_id": command_id, "idempotent_replay": idempotent,
                "source_original_bytes_verified": False,
                "research_complete": False,
                "engine_quality_certified": False,
                "p0_go": False}

    @staticmethod
    def _commit(con: sqlite3.Connection, work: Callable):
        con.execute("BEGIN IMMEDIATE")
        try:
            result = work()
            con.execute("COMMIT")
            return result
        except BaseException:
            if con.in_transaction:
                con.execute("ROLLBACK")
            raise

    def create_scope(self, *, scope_id: str, video_id: str,
                     source_sha256: str, manifest_sha256: str,
                     command_id: str) -> dict:
        scope_id = require_identifier(scope_id, name="SCOPE_ID")
        video_id = require_identifier(video_id, VIDEO, "VIDEO_ID")
        source_sha256 = require_hash(source_sha256, "SOURCE_SHA256")
        manifest_sha256 = require_hash(manifest_sha256, "MANIFEST_SHA256")
        command_id = require_identifier(command_id, name="COMMAND_ID")
        payload = {"video_id": video_id, "source_sha256": source_sha256,
                   "manifest_sha256": manifest_sha256}
        fingerprint = json_digest({"kind": "SCOPE_DECLARED",
                                   "payload": payload, "expected_head": ZERO_SHA})
        con = self._connection()
        try:
            def work():
                previous = con.execute("SELECT * FROM scopes WHERE scope_id=?",
                                       (scope_id,)).fetchone()
                if previous is not None:
                    self._replay(con, scope_id)
                    first = con.execute("SELECT * FROM events WHERE scope_id=? "
                                        "AND sequence=1", (scope_id,)).fetchone()
                    if first and first["command_id"] == command_id and first["command_sha256"] == fingerprint:
                        return self._receipt(scope_id, 1, first["event_sha256"],
                                             first["state_sha256"], command_id,
                                             idempotent=True)
                    raise DomainConflict("SCOPE_ID_ALREADY_USED")
                try:
                    con.execute("INSERT INTO scopes(scope_id,video_id,source_sha256,"
                                "manifest_sha256,sequence,head_sha256) VALUES (?,?,?,?,0,?)",
                                (scope_id, video_id, source_sha256,
                                 manifest_sha256, ZERO_SHA))
                except sqlite3.IntegrityError as exc:
                    raise DomainConflict("VIDEO_ID_OR_SOURCE_DUPLICATE_IN_STORE") from exc
                return self._write_event(con, scope_id=scope_id,seq=1,
                                         prev=ZERO_SHA,command_id=command_id,
                                         kind="SCOPE_DECLARED",payload=payload,
                                         state=empty_state())
            return self._commit(con, work)
        finally:
            con.close()

    def submit(self, *, scope_id: str, command_id: str, expected_head: str,
               kind: str, payload: dict) -> dict:
        scope_id = require_identifier(scope_id, name="SCOPE_ID")
        command_id = require_identifier(command_id, name="COMMAND_ID")
        expected_head = require_hash(expected_head, "EXPECTED_HEAD")
        if kind not in ("MODEL_RECORDED", "REVIEW_PROPOSED"):
            raise DomainConflict("COMMAND_KIND_NOT_ENABLED")
        if type(payload) is not dict:
            raise InvalidInput("COMMAND_PAYLOAD_INVALID")
        fingerprint = json_digest({"kind": kind, "payload": payload,
                                   "expected_head": expected_head})
        con = self._connection()
        try:
            def work():
                state, seq, head = self._replay(con, scope_id)
                prior = con.execute("SELECT * FROM events WHERE scope_id=? AND command_id=?",
                                    (scope_id, command_id)).fetchone()
                if prior is not None:
                    if prior["command_sha256"] != fingerprint:
                        raise IdempotencyConflict("SAME_KEY_DIFFERENT_INPUT")
                    return self._receipt(scope_id, prior["sequence"],
                                         prior["event_sha256"], prior["state_sha256"],
                                         command_id, idempotent=True)
                if head != expected_head:
                    raise ConcurrentHeadChanged("EXPECTED_HEAD_STALE")
                return self._write_event(con, scope_id=scope_id,seq=seq+1,
                                         prev=head,command_id=command_id,
                                         kind=kind,payload=payload,state=state)
            return self._commit(con, work)
        finally:
            con.close()

    def attest_source(self, *, scope_id: str, command_id: str,
                      expected_head: str, raw: bytes, manifest: dict) -> dict:
        """Recompute raw source+census+plan, then commit only derived hashes."""
        from .source import verify_source
        scope_id = require_identifier(scope_id, name="SCOPE_ID")
        command_id = require_identifier(command_id, name="COMMAND_ID")
        expected_head = require_hash(expected_head, "EXPECTED_HEAD")
        source = self.snapshot(scope_id)["state"]["source"]
        audit = verify_source(raw, manifest,
                              expected_source_sha256=source["source_sha256"],
                              expected_manifest_sha256=source["manifest_sha256"])
        payload = source_attestation = audit.attestation()
        fingerprint = json_digest({"kind": "SOURCE_ATTESTED", "payload": payload,
                                   "expected_head": expected_head})
        con = self._connection()
        try:
            def work():
                state, seq, head = self._replay(con, scope_id)
                prior = con.execute("SELECT * FROM events WHERE scope_id=? AND command_id=?",
                                    (scope_id, command_id)).fetchone()
                if prior:
                    if prior["command_sha256"] != fingerprint:
                        raise IdempotencyConflict("SAME_KEY_DIFFERENT_SOURCE_ATTESTATION")
                    return self._receipt(scope_id, prior["sequence"],
                                         prior["event_sha256"],prior["state_sha256"],
                                         command_id,idempotent=True)
                if head != expected_head:
                    raise ConcurrentHeadChanged("EXPECTED_HEAD_STALE")
                if state["source_attestation"] is not None:
                    raise DomainConflict("SOURCE_ALREADY_ATTESTED")
                if source_attestation["video_id"] != state["source"]["video_id"]:
                    raise DomainConflict("VIDEO_ID_SOURCE_MISMATCH")
                return self._write_event(con,scope_id=scope_id,seq=seq+1,
                                         prev=head,command_id=command_id,
                                         kind="SOURCE_ATTESTED",payload=payload,state=state)
            return self._commit(con,work)
        finally:
            con.close()

    def submit_structural_proof(self, *, scope_id: str, command_id: str,
                                expected_head: str, window_id: str,
                                raw: bytes, manifest: dict, review: dict) -> dict:
        """Durably record source-link proof, not semantic or financial approval."""
        from .source import verify_source
        from .proof import audit_model_anchors
        scope_id = require_identifier(scope_id, name="SCOPE_ID")
        command_id = require_identifier(command_id, name="COMMAND_ID")
        expected_head = require_hash(expected_head, "EXPECTED_HEAD")
        window_id = require_identifier(window_id, name="WINDOW_ID")
        con = self._connection()
        try:
            def work():
                state, seq, head = self._replay(con,scope_id)
                prior = con.execute("SELECT * FROM events WHERE scope_id=? AND command_id=?",
                                    (scope_id,command_id)).fetchone()
                if prior is not None:
                    historical = json.loads(prior["event_json"])
                    recorded = historical["payload"]
                    if (historical["type"] != "STRUCTURAL_PROOF_RECORDED" or
                        historical["prev_event_sha256"] != expected_head or
                        recorded["window_id"] != window_id or
                        recorded["review"] != review):
                        raise IdempotencyConflict("SAME_KEY_DIFFERENT_PROOF_INPUT")
                    # An old proof may be retried after A->B->A. Return its
                    # historical receipt only after re-reading the same real
                    # source and reproducing the original structural audit.
                    source = verify_source(raw,manifest,
                             expected_source_sha256=state["source"]["source_sha256"],
                             expected_manifest_sha256=state["source"]["manifest_sha256"])
                    historic_model_row=con.execute(
                        "SELECT event_json FROM events WHERE scope_id=? AND event_sha256=?",
                        (scope_id,recorded["model_revision_event_sha256"])).fetchone()
                    if historic_model_row is None:
                        raise LedgerCorrupted("HISTORICAL_MODEL_REVISION_MISSING")
                    historic_model=json.loads(historic_model_row["event_json"])["payload"]["model"]
                    historic_audit=audit_model_anchors(source,window_id,historic_model,review)
                    if historic_audit != recorded["audit"]:
                        raise IdempotencyConflict("SAME_KEY_HISTORICAL_PROOF_DRIFT")
                    return self._receipt(scope_id,prior["sequence"],
                                         prior["event_sha256"],prior["state_sha256"],
                                         command_id,idempotent=True)
                if head != expected_head:
                    raise ConcurrentHeadChanged("EXPECTED_HEAD_STALE")
                att = state["source_attestation"]
                if att is None:
                    raise DomainConflict("SOURCE_ATTESTATION_REQUIRED")
                source = verify_source(raw,manifest,
                                       expected_source_sha256=state["source"]["source_sha256"],
                                       expected_manifest_sha256=state["source"]["manifest_sha256"])
                if source.attestation() != {k:v for k,v in att.items() if k!="event_sha256"}:
                    raise DomainConflict("SOURCE_REPLAY_ATTESTATION_CHANGED")
                model_state = state["models"].get(window_id)
                if model_state is None:
                    raise DomainConflict("STRUCTURAL_PROOF_REQUIRES_MODEL")
                row = con.execute("SELECT event_json FROM events WHERE scope_id=? AND event_sha256=?",
                                  (scope_id,model_state["revision_event_sha256"])).fetchone()
                if row is None:
                    raise LedgerCorrupted("MODEL_EVENT_NOT_FOUND")
                model = json.loads(row["event_json"])["payload"]["model"]
                audit = audit_model_anchors(source,window_id,model,review)
                payload = {"window_id":window_id,
                           "source_attestation_event_sha256":att["event_sha256"],
                           "model_revision_event_sha256":model_state["revision_event_sha256"],
                           "model_sha256":model_state["model_sha256"],
                           "review":review,"audit":audit}
                fingerprint = json_digest({"kind":"STRUCTURAL_PROOF_RECORDED",
                                           "payload":payload,"expected_head":expected_head})
                return self._write_event(con,scope_id=scope_id,seq=seq+1,
                                         prev=head,command_id=command_id,
                                         kind="STRUCTURAL_PROOF_RECORDED",payload=payload,state=state)
            return self._commit(con,work)
        finally:
            con.close()

    def attest_owner_inventory(self, *, scope_id: str, command_id: str,
                               expected_head: str, raw: bytes, manifest: dict,
                               inventory_bytes: bytes, expected_inventory_sha256: str) -> dict:
        """Persist operator-inventory *pin match*, never owner identity approval."""
        from .trust import verify_owner_inventory
        scope_id = require_identifier(scope_id, name="SCOPE_ID")
        command_id = require_identifier(command_id, name="COMMAND_ID")
        expected_head = require_hash(expected_head, "EXPECTED_HEAD")
        con = self._connection()
        try:
            def work():
                state, seq, head = self._replay(con, scope_id)
                anchor = verify_owner_inventory(raw, manifest, inventory_bytes,
                                     expected_inventory_sha256=expected_inventory_sha256)
                payload = anchor.attestation()
                fingerprint = json_digest({"kind":"OWNER_PIN_RECORDED",
                                           "payload":payload,"expected_head":expected_head})
                prior = con.execute("SELECT * FROM events WHERE scope_id=? AND command_id=?",
                                    (scope_id, command_id)).fetchone()
                if prior:
                    if prior["command_sha256"] != fingerprint:
                        raise IdempotencyConflict("OWNER_PIN_SAME_KEY_CHANGED")
                    return self._receipt(scope_id, prior["sequence"], prior["event_sha256"],
                                         prior["state_sha256"], command_id, idempotent=True)
                if head != expected_head:
                    raise ConcurrentHeadChanged("EXPECTED_HEAD_STALE")
                att = state["source_attestation"]
                if att is None or anchor.source.attestation() != {k:v for k,v in att.items()
                                                                  if k != "event_sha256"}:
                    raise DomainConflict("OWNER_PIN_REQUIRES_MATCHING_SOURCE_ATTESTATION")
                if state["owner_pin"] is not None:
                    raise DomainConflict("OWNER_PIN_ALREADY_RECORDED")
                return self._write_event(con, scope_id=scope_id, seq=seq+1,
                            prev=head, command_id=command_id, kind="OWNER_PIN_RECORDED",
                            payload=payload, state=state)
            return self._commit(con, work)
        finally:
            con.close()

    def submit_finance_candidate(self, *, scope_id: str, command_id: str,
                                 expected_head: str, window_id: str,
                                 raw: bytes, manifest: dict,
                                 inventory_bytes: bytes, expected_inventory_sha256: str,
                                 official_document_raw: bytes, official_proposal: dict,
                                 expected_official_sha256: str, as_of: str,
                                 prior_baseline: dict, prior_relation: dict,
                                 expected_baseline_sha256: str) -> dict:
        """Commit vetted *candidate metadata*. Does not approve facts or relations."""
        from .trust import verify_owner_inventory
        from .finance import audit_official_candidate, audit_prior_relation
        from .proof import audit_model_anchors
        scope_id = require_identifier(scope_id, name="SCOPE_ID")
        command_id = require_identifier(command_id, name="COMMAND_ID")
        expected_head = require_hash(expected_head, "EXPECTED_HEAD")
        window_id = require_identifier(window_id, name="WINDOW_ID")
        con = self._connection()
        try:
            def work():
                state, seq, head = self._replay(con, scope_id)
                owner = state["owner_pin"]
                att = state["source_attestation"]
                if not owner or not att:
                    raise DomainConflict("FINANCE_CANDIDATE_REQUIRES_OWNER_PIN")
                anchored = verify_owner_inventory(raw, manifest, inventory_bytes,
                                    expected_inventory_sha256=expected_inventory_sha256)
                if (anchored.attestation() != {k:v for k,v in owner.items() if k!="event_sha256"} or
                    anchored.source.attestation() != {k:v for k,v in att.items() if k!="event_sha256"}):
                    raise DomainConflict("FINANCE_CANDIDATE_OWNER_PIN_MISMATCH")
                model_state = state["models"].get(window_id)
                proof_state = state["structural_proofs"].get(window_id)
                if (not model_state or not proof_state or
                    proof_state["model_revision_event_sha256"] != model_state["revision_event_sha256"]):
                    raise DomainConflict("FINANCE_CANDIDATE_REQUIRES_CURRENT_PROOF")
                model_row = con.execute(
                    "SELECT event_json FROM events WHERE scope_id=? AND event_sha256=?",
                    (scope_id, model_state["revision_event_sha256"])).fetchone()
                proof_row = con.execute(
                    "SELECT event_json FROM events WHERE scope_id=? AND event_sha256=?",
                    (scope_id, proof_state["proof_event_sha256"])).fetchone()
                if not model_row or not proof_row:
                    raise LedgerCorrupted("FINANCE_CANDIDATE_MODEL_OR_PROOF_MISSING")
                model = json.loads(model_row["event_json"])["payload"]["model"]
                review = json.loads(proof_row["event_json"])["payload"]["review"]
                checked = audit_model_anchors(anchored.source, window_id, model, review)
                if json_digest(checked) != proof_state["audit_sha256"]:
                    raise LedgerCorrupted("FINANCE_CANDIDATE_CURRENT_PROOF_REPLAY_MISMATCH")
                official = audit_official_candidate(official_document_raw, official_proposal,
                                                    expected_document_sha256=expected_official_sha256,
                                                    as_of=as_of)
                relation = audit_prior_relation(prior_baseline, prior_relation,
                                                 expected_baseline_sha256=expected_baseline_sha256)
                claim_id=official["claim_id"]
                if relation["claim_id"] != claim_id or claim_id not in {
                    item["claim_id"] for item in model["claims"]}:
                    raise DomainConflict("FINANCE_CANDIDATE_CLAIM_NOT_IN_CURRENT_MODEL")
                payload={"window_id":window_id,
                         "model_revision_event_sha256":model_state["revision_event_sha256"],
                         "structural_proof_event_sha256":proof_state["proof_event_sha256"],
                         "owner_pin_event_sha256":owner["event_sha256"],
                         "official_audit":official,"relation_audit":relation}
                fingerprint=json_digest({"kind":"FINANCE_CANDIDATE_RECORDED",
                                         "payload":payload,"expected_head":expected_head})
                prior=con.execute("SELECT * FROM events WHERE scope_id=? AND command_id=?",
                                  (scope_id,command_id)).fetchone()
                if prior:
                    if prior["command_sha256"] != fingerprint:
                        raise IdempotencyConflict("FINANCE_CANDIDATE_SAME_KEY_CHANGED")
                    return self._receipt(scope_id,prior["sequence"],prior["event_sha256"],
                                         prior["state_sha256"],command_id,idempotent=True)
                if head != expected_head:
                    raise ConcurrentHeadChanged("EXPECTED_HEAD_STALE")
                return self._write_event(con,scope_id=scope_id,seq=seq+1,prev=head,
                                         command_id=command_id,kind="FINANCE_CANDIDATE_RECORDED",
                                         payload=payload,state=state)
            return self._commit(con,work)
        finally:
            con.close()

    def snapshot_with_finance_candidate(self, *, scope_id: str, window_id: str,
               claim_id: str, raw: bytes, manifest: dict,
               inventory_bytes: bytes, expected_inventory_sha256: str,
               official_document_raw: bytes, official_proposal: dict,
               expected_official_sha256: str, as_of: str,
               prior_baseline: dict, prior_relation: dict,
               expected_baseline_sha256: str) -> dict:
        """Replay a current candidate against all real input bytes in one read tx.

        Historical candidates are not current after any model revision. This
        verifies recorded *candidate structure*; factual entailment stays OPEN.
        """
        from .trust import verify_owner_inventory
        from .finance import audit_official_candidate, audit_prior_relation, CLAIM_ID
        from .proof import audit_model_anchors
        scope_id = require_identifier(scope_id, name="SCOPE_ID")
        window_id = require_identifier(window_id, name="WINDOW_ID")
        if type(claim_id) is not str or not CLAIM_ID.fullmatch(claim_id):
            raise InvalidInput("FINANCE_REPLAY_CLAIM_ID_INVALID")
        con = self._connection()
        try:
            con.execute("BEGIN")
            try:
                state,seq,head = self._replay(con,scope_id)
                owner = state["owner_pin"]
                att = state["source_attestation"]
                if owner is None or att is None:
                    raise DomainConflict("FINANCE_REPLAY_OWNER_PIN_MISSING")
                anchored = verify_owner_inventory(raw,manifest,inventory_bytes,
                                    expected_inventory_sha256=expected_inventory_sha256)
                if (anchored.attestation() != {k:v for k,v in owner.items()
                                               if k != "event_sha256"} or
                    anchored.source.attestation() != {k:v for k,v in att.items()
                                                       if k != "event_sha256"}):
                    raise DomainConflict("FINANCE_REPLAY_OWNER_PIN_DRIFT")
                model_state = state["models"].get(window_id)
                proof_state = state["structural_proofs"].get(window_id)
                finance = state["finance_candidate_reviews"].get(window_id+":"+claim_id)
                if (not model_state or not proof_state or not finance or
                    finance["model_revision_event_sha256"] != model_state["revision_event_sha256"] or
                    proof_state["model_revision_event_sha256"] != model_state["revision_event_sha256"]):
                    raise DomainConflict("FINANCE_REPLAY_CURRENT_CANDIDATE_NOT_AVAILABLE")
                model_row=con.execute("SELECT event_json FROM events WHERE scope_id=? AND event_sha256=?",
                        (scope_id,model_state["revision_event_sha256"])).fetchone()
                proof_row=con.execute("SELECT event_json FROM events WHERE scope_id=? AND event_sha256=?",
                        (scope_id,proof_state["proof_event_sha256"])).fetchone()
                finance_row=con.execute("SELECT event_json FROM events WHERE scope_id=? AND event_sha256=?",
                        (scope_id,finance["finance_event_sha256"])).fetchone()
                if not model_row or not proof_row or not finance_row:
                    raise LedgerCorrupted("FINANCE_REPLAY_DEPENDENCY_MISSING")
                model=json.loads(model_row["event_json"])["payload"]["model"]
                review=json.loads(proof_row["event_json"])["payload"]["review"]
                checked=audit_model_anchors(anchored.source,window_id,model,review)
                if json_digest(checked) != proof_state["audit_sha256"]:
                    raise LedgerCorrupted("FINANCE_REPLAY_SOURCE_PROOF_DRIFT")
                official=audit_official_candidate(official_document_raw,official_proposal,
                                    expected_document_sha256=expected_official_sha256,as_of=as_of)
                relation=audit_prior_relation(prior_baseline,prior_relation,
                                    expected_baseline_sha256=expected_baseline_sha256)
                payload=json.loads(finance_row["event_json"])["payload"]
                if (official != payload["official_audit"] or
                    relation != payload["relation_audit"] or
                    payload["model_revision_event_sha256"] != model_state["revision_event_sha256"] or
                    payload["structural_proof_event_sha256"] != proof_state["proof_event_sha256"] or
                    payload["owner_pin_event_sha256"] != owner["event_sha256"] or
                    json_digest(official) != finance["official_audit_sha256"] or
                    json_digest(relation) != finance["relation_audit_sha256"]):
                    raise LedgerCorrupted("FINANCE_REPLAY_SAVED_CANDIDATE_DRIFT")
                result={"schema":"IRE_V6_PRIVATE_FINANCE_CANDIDATE_REPLAY_V1",
                        "scope_id":scope_id,"sequence":seq,"ledger_head_sha256":head,
                        "state_sha256":json_digest(state),"claim_id":claim_id,
                        "source_original_bytes_replayed_this_call":True,
                        "owner_inventory_pin_matched_this_call":True,
                        "official_document_bytes_replayed_this_call":True,
                        "legacy_baseline_membership_replayed_this_call":True,
                        "official_effective_at_as_of":official["effective_at_as_of"],
                        "issuer_authenticity_independently_verified":False,
                        "financial_claim_semantically_verified":False,
                        "prior_relation_semantically_verified":False,
                        "research_closed":False,"p0_go":False}
                con.execute("COMMIT")
                return result
            except BaseException:
                if con.in_transaction:
                    con.execute("ROLLBACK")
                raise
        finally:
            con.close()

    def snapshot_with_source(self, *, scope_id: str, raw: bytes, manifest: dict) -> dict:
        """Freshly replay every current structural proof against private bytes."""
        from .source import verify_source
        from .proof import audit_model_anchors
        scope_id = require_identifier(scope_id, name="SCOPE_ID")
        con = self._connection()
        try:
            con.execute("BEGIN")
            try:
                state,seq,head = self._replay(con,scope_id)
                source = verify_source(raw,manifest,
                                       expected_source_sha256=state["source"]["source_sha256"],
                                       expected_manifest_sha256=state["source"]["manifest_sha256"])
                att = state["source_attestation"]
                if att is None or source.attestation() != {k:v for k,v in att.items() if k!="event_sha256"}:
                    raise DomainConflict("SOURCE_REPLAY_ATTESTATION_REQUIRED")
                rechecked=[]
                for wid,proof in state["structural_proofs"].items():
                    model_state = state["models"].get(wid)
                    if not model_state or proof["model_revision_event_sha256"] != model_state["revision_event_sha256"]:
                        continue
                    event_row = con.execute("SELECT event_json FROM events WHERE scope_id=? AND event_sha256=?",
                                            (scope_id,proof["proof_event_sha256"])).fetchone()
                    model_row = con.execute("SELECT event_json FROM events WHERE scope_id=? AND event_sha256=?",
                                            (scope_id,model_state["revision_event_sha256"])).fetchone()
                    if event_row is None or model_row is None:
                        raise LedgerCorrupted("PROOF_OR_MODEL_EVENT_MISSING")
                    proof_payload=json.loads(event_row["event_json"])["payload"]
                    model=json.loads(model_row["event_json"])["payload"]["model"]
                    audit = audit_model_anchors(source,wid,model,proof_payload["review"])
                    if audit!=proof_payload["audit"] or json_digest(audit)!=proof["audit_sha256"]:
                        raise LedgerCorrupted("PROOF_FRESH_REPLAY_MISMATCH")
                    rechecked.append(wid)
                result={"schema":"IRE_V6_PRIVATE_SOURCE_REPLAY_SNAPSHOT_V1",
                        "scope_id":scope_id,"sequence":seq,
                        "ledger_head_sha256":head,"state_sha256":json_digest(state),
                        "source_original_bytes_verified_this_call":True,
                        "current_structural_proofs_reverified":len(rechecked),
                        "source_attestation_event_sha256":att["event_sha256"],
                        "semantic_recall_verified":False,"financial_facts_approved":False,
                        "research_closed":False,"engine_quality_certified":False,"p0_go":False}
                con.execute("COMMIT")
                return result
            except BaseException:
                if con.in_transaction:
                    con.execute("ROLLBACK")
                raise
        finally:
            con.close()

    def freeze_blind_plan(self, *, scope_id: str, command_id: str,
                          expected_head: str, raw: bytes, manifest: dict,
                          inventory_bytes: bytes, expected_inventory_sha256: str,
                          plan: dict) -> dict:
        """Pre-register gold hash, scope and thresholds BEFORE any model event."""
        from .trust import verify_owner_inventory
        from .evaluation import validate_plan
        scope_id=require_identifier(scope_id,name="SCOPE_ID")
        command_id=require_identifier(command_id,name="COMMAND_ID")
        expected_head=require_hash(expected_head,"EXPECTED_HEAD")
        con=self._connection()
        try:
            def work():
                state,seq,head=self._replay(con,scope_id)
                owner=state["owner_pin"]
                if not owner or state["models"]:
                    raise DomainConflict("BLIND_PLAN_REQUIRES_PIN_AND_NO_PREDICTIONS")
                anchored=verify_owner_inventory(raw,manifest,inventory_bytes,
                                    expected_inventory_sha256=expected_inventory_sha256)
                if anchored.attestation()!={k:v for k,v in owner.items() if k!="event_sha256"}:
                    raise DomainConflict("BLIND_PLAN_OWNER_REPLAY_MISMATCH")
                digest=validate_plan(anchored.source,plan)
                payload={"plan":plan,"plan_sha256":digest,
                         "owner_pin_event_sha256":owner["event_sha256"]}
                fp=json_digest({"kind":"BLIND_PLAN_FROZEN","payload":payload,
                                "expected_head":expected_head})
                previous=con.execute("SELECT * FROM events WHERE scope_id=? AND command_id=?",
                                     (scope_id,command_id)).fetchone()
                if previous:
                    if previous["command_sha256"]!=fp:
                        raise IdempotencyConflict("BLIND_PLAN_COMMAND_REUSED_DIFFERENT")
                    return self._receipt(scope_id,previous["sequence"],previous["event_sha256"],
                                         previous["state_sha256"],command_id,idempotent=True)
                if head!=expected_head:
                    raise ConcurrentHeadChanged("EXPECTED_HEAD_STALE")
                return self._write_event(con,scope_id=scope_id,seq=seq+1,prev=head,
                       command_id=command_id,kind="BLIND_PLAN_FROZEN",payload=payload,state=state)
            return self._commit(con,work)
        finally:
            con.close()

    def record_blind_measurement(self, *, scope_id: str, command_id: str,
                                 expected_head: str, raw: bytes, manifest: dict,
                                 inventory_bytes: bytes, expected_inventory_sha256: str,
                                 gold: dict, predictions: dict, alignment: dict) -> dict:
        """Record arithmetically audited gold comparisons, NOT independent truth."""
        from .trust import verify_owner_inventory
        from .evaluation import measure_blind
        from .proof import audit_model_anchors
        from .receipt import _payload
        scope_id=require_identifier(scope_id,name="SCOPE_ID")
        command_id=require_identifier(command_id,name="COMMAND_ID")
        expected_head=require_hash(expected_head,"EXPECTED_HEAD")
        con=self._connection()
        try:
            def work():
                state,seq,head=self._replay(con,scope_id)
                plan=state["blind_plan"]
                owner=state["owner_pin"]
                if not plan or not owner:
                    raise DomainConflict("BLIND_MEASUREMENT_REQUIRES_FROZEN_PLAN")
                anchored=verify_owner_inventory(raw,manifest,inventory_bytes,
                                    expected_inventory_sha256=expected_inventory_sha256)
                if anchored.attestation()!={k:v for k,v in owner.items() if k!="event_sha256"}:
                    raise DomainConflict("BLIND_MEASUREMENT_OWNER_REPLAY_MISMATCH")
                expected_predictions=[]
                for wid,_,_ in anchored.source.primary_windows:
                    model=state["models"].get(wid)
                    if not model:
                        raise DomainConflict("BLIND_MEASUREMENT_MISSING_MODEL_WINDOW")
                    payload=self._load_model_event(con,scope_id,model["revision_event_sha256"])
                    proof=state["structural_proofs"].get(wid)
                    if not proof or proof["model_revision_event_sha256"]!=model["revision_event_sha256"]:
                        raise DomainConflict("BLIND_MEASUREMENT_CURRENT_PROOF_REQUIRED")
                    proof_payload=_payload(con,scope_id,proof["proof_event_sha256"],
                                          "STRUCTURAL_PROOF_RECORDED")
                    verified=audit_model_anchors(anchored.source,wid,payload,
                                                  proof_payload["review"])
                    if (verified!=proof_payload["audit"] or
                        json_digest(verified)!=proof["audit_sha256"]):
                        raise LedgerCorrupted("BLIND_MEASUREMENT_PROOF_REPLAY_MISMATCH")
                    for claim in payload["claims"]:
                        expected_predictions.append(claim)
                if type(predictions) is not dict or type(predictions.get("claims")) is not list:
                    raise InvalidInput("BLIND_PREDICTIONS_INVALID")
                # Predictions must be the exact source-grounded MODEL_RECORDED claims.
                actual={c.get("claim_id"):c for c in expected_predictions}
                if len(actual)!=len(expected_predictions) or len(predictions["claims"])!=len(actual):
                    raise DomainConflict("BLIND_MODEL_CLAIM_IDS_NOT_GLOBALLY_UNIQUE")
                for c in predictions["claims"]:
                    if type(c) is not dict:
                        raise InvalidInput("BLIND_PREDICTION_CLAIM_INVALID")
                    model_claim=actual.get(c.get("claim_id"))
                    if (model_claim is None or c.get("proposition")!=model_claim["proposition"] or
                        c.get("source_refs")!=model_claim["source_refs"] or
                        type(c.get("frame")) is not dict or
                        c["frame"].get("modality")!=model_claim["kind"]):
                        raise DomainConflict("BLIND_PREDICTIONS_CHANGED_FROM_MODEL_REVISION")
                metrics=measure_blind(raw,manifest,plan["plan"],gold,predictions,alignment)
                revisions=json_digest([{"window_id":wid,"revision_event_sha256":
                            state["models"][wid]["revision_event_sha256"]}
                            for wid in sorted(state["models"])])
                payload={"plan_event_sha256":plan["event_sha256"],
                         "revision_set_sha256":revisions,"metrics":metrics,
                         "gold":gold,"predictions":predictions,"alignment":alignment}
                fp=json_digest({"kind":"BLIND_MEASUREMENT_RECORDED", "payload":payload,
                                "expected_head":expected_head})
                prev=con.execute("SELECT * FROM events WHERE scope_id=? AND command_id=?",
                                 (scope_id,command_id)).fetchone()
                if prev:
                    if prev["command_sha256"]!=fp:
                        raise IdempotencyConflict("BLIND_MEASUREMENT_COMMAND_REUSED_DIFFERENT")
                    return self._receipt(scope_id,prev["sequence"],prev["event_sha256"],
                                         prev["state_sha256"],command_id,idempotent=True)
                if head!=expected_head:
                    raise ConcurrentHeadChanged("EXPECTED_HEAD_STALE")
                return self._write_event(con,scope_id=scope_id,seq=seq+1,prev=head,
                         command_id=command_id,kind="BLIND_MEASUREMENT_RECORDED",
                         payload=payload,state=state)
            return self._commit(con,work)
        finally:
            con.close()

    @staticmethod
    def _load_model_event(con,scope_id,event_sha256):
        row=con.execute("SELECT event_json FROM events WHERE scope_id=? AND event_sha256=?",
                        (scope_id,event_sha256)).fetchone()
        if row is None:
            raise LedgerCorrupted("BLIND_MODEL_EVENT_NOT_FOUND")
        event=json.loads(row["event_json"])
        if event["type"]!="MODEL_RECORDED":
            raise LedgerCorrupted("BLIND_MODEL_EVENT_TYPE_INVALID")
        return event["payload"]["model"]

    def snapshot_with_blind_measurement(self, *, scope_id: str, raw: bytes,
                                        manifest: dict, inventory_bytes: bytes,
                                        expected_inventory_sha256: str) -> dict:
        """Recompute stored blinded *arithmetic* inside a verified read snapshot.

        No proof that supplied labels were independently generated. All stored
        gold/prediction/alignment bytes remain private in the local database.
        """
        from .trust import verify_owner_inventory
        from .evaluation import measure_blind
        scope_id=require_identifier(scope_id,name="SCOPE_ID")
        con=self._connection()
        try:
            con.execute("BEGIN")
            try:
                state,seq,head=self._replay(con,scope_id)
                owner=state["owner_pin"]
                plan=state["blind_plan"]
                record=state["blind_measurement"]
                if not owner or not plan or not record:
                    raise DomainConflict("BLIND_SNAPSHOT_MEASUREMENT_NOT_PRESENT")
                anchor=verify_owner_inventory(raw,manifest,inventory_bytes,
                    expected_inventory_sha256=expected_inventory_sha256)
                if anchor.attestation()!={k:v for k,v in owner.items() if k!="event_sha256"}:
                    raise DomainConflict("BLIND_SNAPSHOT_OWNER_REPLAY_DRIFT")
                revisions=json_digest([{"window_id":wid,"revision_event_sha256":
                                state["models"][wid]["revision_event_sha256"]}
                                for wid in sorted(state["models"])])
                if revisions!=record["revision_set_sha256"]:
                    raise DomainConflict("BLIND_SNAPSHOT_MODEL_REVISED_SINCE_MEASUREMENT")
                row=con.execute("SELECT event_json FROM events WHERE scope_id=? AND event_sha256=?",
                                 (scope_id,record["event_sha256"])).fetchone()
                if row is None:
                    raise LedgerCorrupted("BLIND_SNAPSHOT_MEASUREMENT_EVENT_MISSING")
                payload=json.loads(row["event_json"])["payload"]
                checked=measure_blind(raw,manifest,plan["plan"],payload["gold"],
                                      payload["predictions"],payload["alignment"])
                if checked!=payload["metrics"] or json_digest(checked)!=record["metrics_sha256"]:
                    raise LedgerCorrupted("BLIND_SNAPSHOT_METRICS_REPLAY_MISMATCH")
                # Confirm the recorded prediction atoms still equal current model
                # source strings and core modality; user-classified frames remain
                # externally unverified semantic assertions.
                current={}
                for wid,_,_ in anchor.source.primary_windows:
                    model=state["models"].get(wid)
                    if not model:raise DomainConflict("BLIND_SNAPSHOT_WINDOW_MODEL_MISSING")
                    for claim in self._load_model_event(con,scope_id,model["revision_event_sha256"])["claims"]:
                        if claim["claim_id"] in current:
                            raise DomainConflict("BLIND_SNAPSHOT_CLAIM_ID_DUPLICATE")
                        current[claim["claim_id"]]=claim
                actual={c["claim_id"]:c for c in payload["predictions"]["claims"]}
                if len(actual)!=len(current):
                    raise LedgerCorrupted("BLIND_SNAPSHOT_PREDICTION_CENSUS_DRIFT")
                for cid,c in actual.items():
                    ref=current.get(cid)
                    if ref is None or c["source_refs"]!=ref["source_refs"] or \
                       c["proposition"]!=ref["proposition"] or \
                       c["frame"]["modality"]!=ref["kind"]:
                        raise LedgerCorrupted("BLIND_SNAPSHOT_PREDICTION_CONTENT_DRIFT")
                result={"schema":"IRE_V6_BLIND_MEASUREMENT_REPLAY_V1",
                        "scope_id":scope_id,"sequence":seq,"ledger_head_sha256":head,
                        "measurement_event_sha256":record["event_sha256"],
                        "counts":checked["counts"],"precision":checked["precision"],
                        "recall":checked["recall"],
                        "high_risk_recall":checked["high_risk_recall"],
                        "arithmetic_replayed_this_call":True,
                        "actual_reviewer_identity_verified":False,
                        "gold_completeness_independently_verified":False,
                        "engine_quality_certified":False,"p0_go":False}
                con.execute("COMMIT")
                return result
            except BaseException:
                if con.in_transaction:con.execute("ROLLBACK")
                raise
        finally:
            con.close()

    def issue_terminal_audit_receipt(self, *, scope_id: str, command_id: str,
                                     expected_head: str, raw: bytes, manifest: dict,
                                     inventory_bytes: bytes, expected_inventory_sha256: str,
                                     finance_inputs: dict) -> dict:
        """Atomically issue a snapshot-bound TERMINAL_BLOCKED audit only.

        This NEVER returns research_complete=True. It does not modify or
        authorize issue_terminal_receipt(), still gated on absent independent
        semantic and factual validation. Source inputs stay in private memory.
        """
        from .receipt import audit_receipt_inputs, audit_input_digest
        scope_id=require_identifier(scope_id,name="SCOPE_ID")
        command_id=require_identifier(command_id,name="COMMAND_ID")
        expected_head=require_hash(expected_head,"EXPECTED_HEAD")
        con=self._connection()
        try:
            def work():
                state,seq,head=self._replay(con,scope_id)
                input_sha=audit_input_digest(raw,manifest,inventory_bytes,
                              expected_inventory_sha256,finance_inputs)
                previous=con.execute("SELECT * FROM events WHERE scope_id=? AND command_id=?",
                                     (scope_id,command_id)).fetchone()
                if previous:
                    historical=json.loads(previous["event_json"])
                    stored=historical["payload"]
                    if (historical["type"]!="TERMINAL_AUDIT_RECORDED" or
                        stored["base_head_sha256"]!=expected_head or
                        stored["private_input_sha256"]!=input_sha):
                        raise IdempotencyConflict("TERMINAL_AUDIT_RETRY_CHANGED")
                    historic=self._receipt(scope_id,previous["sequence"],previous["event_sha256"],
                                           previous["state_sha256"],command_id,idempotent=True)
                    return {**historic,"audit_report":stored["report"],
                            "base_head_sha256":stored["base_head_sha256"],
                            "terminal_outcome":"TERMINAL_BLOCKED",
                            "historical":previous["event_sha256"]!=head,
                            "research_complete":False}
                if head!=expected_head:
                    raise ConcurrentHeadChanged("EXPECTED_HEAD_STALE")
                report=audit_receipt_inputs(con,scope_id,state,raw=raw,manifest=manifest,
                    inventory_bytes=inventory_bytes,
                    expected_inventory_sha256=expected_inventory_sha256,
                    finance_inputs=finance_inputs)
                payload={"schema":"IRE_V6_TERMINAL_AUDIT_EVENT_V1",
                         "base_head_sha256":expected_head,
                         "base_state_sha256":json_digest(state),
                         "private_input_sha256":input_sha,"report":report}
                result=self._write_event(con,scope_id=scope_id,seq=seq+1,prev=head,
                        command_id=command_id,kind="TERMINAL_AUDIT_RECORDED",payload=payload,state=state)
                return {**result,"audit_report":report,"base_head_sha256":expected_head,
                        "terminal_outcome":"TERMINAL_BLOCKED","historical":False,
                        "research_complete":False}
            return self._commit(con,work)
        finally:
            con.close()

    def read_terminal_audit_receipt(self, *, scope_id: str, audit_event_sha256: str) -> dict:
        """Verify a historical audit's provenance; never equate it with current GO."""
        scope_id=require_identifier(scope_id,name="SCOPE_ID")
        audit_event_sha256=require_hash(audit_event_sha256,"AUDIT_EVENT_SHA")
        con=self._connection()
        try:
            con.execute("BEGIN")
            try:
                state,seq,head=self._replay(con,scope_id)
                audit=next((r for r in state["terminal_audits"]
                            if r["event_sha256"]==audit_event_sha256),None)
                if not audit:
                    raise InvalidInput("AUDIT_RECEIPT_NOT_FOUND")
                row=con.execute("SELECT event_json FROM events WHERE scope_id=? AND event_sha256=?",
                                (scope_id,audit_event_sha256)).fetchone()
                if row is None:
                    raise LedgerCorrupted("AUDIT_RECEIPT_EVENT_DISAPPEARED")
                payload=json.loads(row["event_json"])["payload"]
                if json_digest(payload["report"])!=audit["report_sha256"]:
                    raise LedgerCorrupted("AUDIT_REPORT_DIGEST_MISMATCH")
                result={"schema":"IRE_V6_AUDIT_RECEIPT_VIEW_V1","scope_id":scope_id,
                        "audit_event_sha256":audit_event_sha256,
                        "base_head_sha256":audit["base_head_sha256"],
                        "current_ledger_head_sha256":head,
                        "is_latest_event":head==audit_event_sha256,
                        "outcome":"TERMINAL_BLOCKED","report":payload["report"],
                        "research_complete":False,"engine_quality_certified":False,"p0_go":False}
                con.execute("COMMIT")
                return result
            except BaseException:
                if con.in_transaction:
                    con.execute("ROLLBACK")
                raise
        finally:
            con.close()

    def snapshot(self, scope_id: str) -> dict:
        """Verified, one-version read; no reuse of earlier replay status."""
        scope_id = require_identifier(scope_id, name="SCOPE_ID")
        con = self._connection()
        try:
            con.execute("BEGIN")
            try:
                state, seq, head = self._replay(con, scope_id)
                result = {"schema": SNAPSHOT_SCHEMA,
                          "scope_id": scope_id,"sequence": seq,
                          "ledger_head_sha256": head,
                          "state_sha256": json_digest(state),
                          "state": state, "progress": progress(state)}
                con.execute("COMMIT")
                return result
            except BaseException:
                if con.in_transaction:
                    con.execute("ROLLBACK")
                raise
        finally:
            con.close()

    def is_current(self, *, scope_id: str, ledger_head_sha256: str) -> bool:
        """The only supported way to check whether a historical snapshot is current."""
        require_hash(ledger_head_sha256, "LEDGER_HEAD")
        return self.snapshot(scope_id)["ledger_head_sha256"] == ledger_head_sha256

    def progress_receipt(self, scope_id: str) -> dict:
        snap = self.snapshot(scope_id)
        return {"schema": "IRE_V6_PROGRESS_RECEIPT_V1",
                "scope_id": snap["scope_id"],
                "snapshot_sequence": snap["sequence"],
                "snapshot_head_sha256": snap["ledger_head_sha256"],
                "state_sha256": snap["state_sha256"],
                "progress": snap["progress"],
                "terminal": snap["progress"]["research_report_closed"],
                "research_complete": snap["progress"]["research_report_closed"],
                "engine_quality_certified": False,
                "p0_go": False,
                "terminal_outcome": ("OFFICIAL_SOURCE_SCOPED_COMPLETE"
                    if snap["progress"]["research_report_closed"]
                    else "V6_KERNEL_ONLY_VALIDATION_OPEN")}

    def issue_terminal_receipt(self, scope_id: str, *, command_id=None,
                               expected_head=None, raw=None, manifest=None,
                               inventory_bytes=None, expected_inventory_sha256=None,
                               finance_inputs=None, determinations=None,
                               official_document_raw=None, as_of=None) -> dict:
        """V2 narrowed official-rule completion, never general engine P0 GO.

        Historical no-evidence signature still fails; all new inputs must be
        transaction-bound and the official rule is cryptographically pinned.
        """
        if command_id is None:
            self.snapshot(scope_id)
            raise QualityNotProven("V6_1_MANDATORY_PROOF_VERIFIERS_NOT_IMPLEMENTED")
        from .receipt import audit_input_digest
        from .official_completion import audit_official_completion, verify_pinned_law
        scope_id=require_identifier(scope_id,name="SCOPE_ID")
        command_id=require_identifier(command_id,name="COMMAND_ID")
        expected_head=require_hash(expected_head,"EXPECTED_HEAD")
        if type(determinations) is not list or type(official_document_raw) is not bytes:
            raise InvalidInput("OFFICIAL_COMPLETION_INPUTS_REQUIRED")
        verify_pinned_law(official_document_raw,as_of=as_of)
        commitment=json_digest({
            "source_finance":audit_input_digest(raw,manifest,inventory_bytes,
                                expected_inventory_sha256,finance_inputs),
            "decisions":json_digest(determinations),
            "official_raw_sha256":sha256(official_document_raw),
            "as_of":as_of})
        con=self._connection()
        try:
            def work():
                state,seq,head=self._replay(con,scope_id)
                previous=con.execute(
                    "SELECT * FROM events WHERE scope_id=? AND command_id=?",
                    (scope_id,command_id)).fetchone()
                if previous:
                    e=json.loads(previous["event_json"])
                    p=e["payload"]
                    if (e["type"]!="TERMINAL_OFFICIAL_COMPLETION_RECORDED" or
                        p["base_head_sha256"]!=expected_head or
                        p["private_input_sha256"]!=commitment):
                        raise IdempotencyConflict("OFFICIAL_TERMINAL_RETRY_CHANGED")
                    receipt=self._receipt(scope_id,previous["sequence"],
                                previous["event_sha256"],previous["state_sha256"],
                                command_id,idempotent=True)
                    still_current=(previous["event_sha256"]==head and
                                   state["research_report_closed"])
                    return {**receipt,"terminal_outcome":p["report"]["outcome"],
                            "research_complete":still_current,
                            "scoped_official_rule_verified":True,
                            "historical_scope_completed":True,
                            "is_current":still_current}
                if head!=expected_head:
                    raise ConcurrentHeadChanged("EXPECTED_HEAD_STALE")
                if state["research_report_closed"]:
                    raise DomainConflict("OFFICIAL_SCOPE_ALREADY_COMPLETE")
                report=audit_official_completion(
                    con,scope_id,state,raw=raw,manifest=manifest,
                    inventory_bytes=inventory_bytes,
                    expected_inventory_sha256=expected_inventory_sha256,
                    finance_inputs=finance_inputs,determinations=determinations,
                    official_document_raw=official_document_raw,as_of=as_of)
                payload={"schema":"IRE_V6_OFFICIAL_TERMINAL_EVENT_V2",
                         "base_head_sha256":head,
                         "base_state_sha256":json_digest(state),
                         "private_input_sha256":commitment,
                         "report":report}
                result=self._write_event(
                    con,scope_id=scope_id,seq=seq+1,prev=head,
                    command_id=command_id,
                    kind="TERMINAL_OFFICIAL_COMPLETION_RECORDED",
                    payload=payload,state=state)
                return {**result,"terminal_outcome":report["outcome"],
                        "research_complete":True,
                        "scoped_official_rule_verified":True,"is_current":True}
            return self._commit(con,work)
        finally:
            con.close()

    def read_official_terminal_receipt(self, *, scope_id: str,
                                       terminal_event_sha256: str) -> dict:
        """Fresh SQLite audit of current/historical official-scope terminal."""
        scope_id=require_identifier(scope_id,name="SCOPE_ID")
        terminal_event_sha256=require_hash(terminal_event_sha256,"TERMINAL_SHA")
        con=self._connection()
        try:
            con.execute("BEGIN")
            try:
                state,seq,head=self._replay(con,scope_id)
                entry=next((e for e in state["terminal_audits"]
                    if e["event_sha256"]==terminal_event_sha256 and
                    e["outcome"]=="OFFICIAL_SOURCE_SCOPED_COMPLETE"),None)
                if entry is None:
                    raise InvalidInput("OFFICIAL_SCOPE_RECEIPT_NOT_FOUND")
                row=con.execute(
                    "SELECT event_json FROM events WHERE scope_id=? AND event_sha256=?",
                    (scope_id,terminal_event_sha256)).fetchone()
                if row is None:
                    raise LedgerCorrupted("OFFICIAL_SCOPE_EVENT_MISSING")
                event=json.loads(row["event_json"])
                if (event["type"]!="TERMINAL_OFFICIAL_COMPLETION_RECORDED" or
                    json_digest(event["payload"]["report"])!=entry["report_sha256"]):
                    raise LedgerCorrupted("OFFICIAL_SCOPE_REPORT_DRIFT")
                current=head==terminal_event_sha256 and state["research_report_closed"]
                result={"schema":"IRE_V6_OFFICIAL_TERMINAL_READ_V2",
                        "scope_id":scope_id,
                        "terminal_event_sha256":terminal_event_sha256,
                        "base_head_sha256":entry["base_head_sha256"],
                        "current_head_sha256":head,
                        "is_current":current,
                        "historical_scope_completed":True,
                        "research_complete":current,
                        "engine_quality_certified":False,"p0_go":False,
                        "report":event["payload"]["report"]}
                con.execute("COMMIT")
                return result
            except BaseException:
                if con.in_transaction:
                    con.execute("ROLLBACK")
                raise
        finally:
            con.close()
