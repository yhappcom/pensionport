"""Private, offline structural replay of a source-grounded ChatGPT revision.

Caller supplies real source, independently pinned owner inventory, frozen
prediction/reviewer bytes, pending prior relations and reviewed quarantine.
No model generation, automatic quarantine, fabricated review or publication.
Use a new private local database; preserve any previous trial unchanged.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from .atomic_exchange import audit_host_atomic_exchange
from .chat_revision import compile_chat_atom_revision
from .codec import json_digest, require_hash, sha256
from .errors import InvalidInput, LedgerCorrupted
from .host_quarantine_preflight import audit_host_quarantine_preflight
from .prior_knowledge import audit_prior_candidates
from .store import TransactionStore
from .trust import verify_owner_inventory


def _read_pinned_json(raw, pin, label):
    require_hash(pin,label)
    if type(raw) is not bytes or sha256(raw)!=pin:
        raise InvalidInput(label+"_BYTES_DRIFT")
    try:
        obj=json.loads(raw)
    except (ValueError,UnicodeError) as exc:
        raise InvalidInput(label+"_JSON_INVALID") from exc
    if type(obj) is not dict:
        raise InvalidInput(label+"_OBJECT_REQUIRED")
    return obj


def replay_private_revision(*, database_path, scope_id, run_id, raw, manifest,
                            inventory_bytes, expected_inventory_sha256,
                            frozen_native_bytes, expected_native_sha256,
                            reviewer_bytes, expected_reviewer_sha256,
                            knowledge, quarantine_preflight=None):
    """Commit and reopen a new private V6 structural host batch.

    All semantic inputs must be prepared outside the runner by actual review.
    Existing unresolved or suspicious cues remain escrowed. The receipt is
    deliberately SHA/count-only and never asserts research completion.
    """
    before=_read_pinned_json(frozen_native_bytes,expected_native_sha256,"OFFLINE_NATIVE")
    review=_read_pinned_json(reviewer_bytes,expected_reviewer_sha256,"OFFLINE_REVIEW")
    if set(review)!={"edits","cue_reviews"} or type(review["cue_reviews"]) is not list:
        raise InvalidInput("OFFLINE_REVISION_REVIEW_SCHEMA")
    pinned=verify_owner_inventory(raw,manifest,inventory_bytes,
                                   expected_inventory_sha256=expected_inventory_sha256)
    source=pinned.source
    prior=audit_host_atomic_exchange(source,before)
    inputs={"before":before,"edits":review["edits"],"cue_reviews":review["cue_reviews"]}
    compiled=compile_chat_atom_revision(source,before,edits=inputs["edits"],
                                        cue_reviews=inputs["cue_reviews"])
    exchange=compiled["exchange"]
    proposed=audit_host_atomic_exchange(source,exchange)
    if audit_prior_candidates(source,exchange,knowledge)["p0_go"] is not False:
        raise InvalidInput("OFFLINE_PRIOR_UNSAFE_GO")
    quarantine=audit_host_quarantine_preflight(source,exchange,quarantine_preflight)
    path=Path(database_path)
    if path.exists() or path.is_symlink():
        raise InvalidInput("OFFLINE_NEW_DATABASE_REQUIRED")
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    if path.parent.is_symlink() or (os.name=="posix" and (
        path.parent.stat().st_uid!=os.getuid() or path.parent.stat().st_mode & 0o077)):
        raise InvalidInput("OFFLINE_PRIVATE_DIRECTORY_REQUIRED")
    # Exclusive reservation prevents accidental overwrite/race with prior trials.
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    os.close(fd)
    store=TransactionStore(path)
    first=store.create_scope(scope_id=scope_id,video_id=source.video_id,
        source_sha256=source.source_sha256,manifest_sha256=source.manifest_sha256,
        command_id="offline_genesis")
    second=store.attest_source(scope_id=scope_id,command_id="offline_source",
        expected_head=first["event_sha256"],raw=raw,manifest=manifest)
    third=store.attest_owner_inventory(scope_id=scope_id,command_id="offline_owner",
        expected_head=second["event_sha256"],raw=raw,manifest=manifest,
        inventory_bytes=inventory_bytes,expected_inventory_sha256=expected_inventory_sha256)
    read_args=dict(scope_id=scope_id,run_id=run_id,raw=raw,manifest=manifest,
        inventory_bytes=inventory_bytes,expected_inventory_sha256=expected_inventory_sha256)
    args=dict(**read_args,expected_head=third["event_sha256"],exchange=exchange,
        knowledge=knowledge,window_models=compiled["window_models"],
        window_reviews=compiled["window_reviews"],quarantine_preflight=quarantine_preflight,
        chat_revision=inputs)
    committed=store.submit_host_atomic_batch(**args)
    replay=store.submit_host_atomic_batch(**args)
    reopened=TransactionStore(path)
    saved=reopened.read_host_chat_revision(**read_args)
    snap=reopened.snapshot(scope_id)
    if (not committed["atomic_batch_committed"] or not replay["idempotent_replay"]
        or committed["event_sha256"]!=replay["event_sha256"]
        or saved["event_sha256"]!=committed["event_sha256"]
        or saved["record"]["inputs"]!=inputs or saved["record"]["result"]!=compiled
        or saved["private_chat_revision_sha256"]!=committed["private_chat_revision_sha256"]
        or snap["ledger_head_sha256"]!=committed["event_sha256"]
        or snap["progress"]["model_windows_recorded"]!=len(source.primary_windows)
        or snap["progress"]["current_revision_structural_proof_records"]!=len(source.primary_windows)
        or snap["progress"]["engine_quality_certified"] is not False):
        raise LedgerCorrupted("OFFLINE_REVISION_REOPEN_DRIFT")
    with sqlite3.connect(path) as con:
        if con.execute("PRAGMA integrity_check").fetchall()!=[("ok",)]:
            raise LedgerCorrupted("OFFLINE_SQLITE_INTEGRITY_FAILURE")
    return {"schema":"IRE_V6_OFFLINE_PRIVATE_REVISION_REPLAY_V1",
            "source_sha256":source.source_sha256,"manifest_sha256":source.manifest_sha256,
            "inventory_sha256":expected_inventory_sha256,
            "frozen_native_sha256":expected_native_sha256,
            "reviewer_input_sha256":expected_reviewer_sha256,
            "cue_count":len(source.cues),"window_count":len(source.primary_windows),
            "before_atoms":prior["proposed_atomic_claims"],
            "after_atoms":proposed["proposed_atomic_claims"],
            "unresolved_cues":proposed["unresolved_cues"],
            "quarantined_cues":quarantine["unresolved_original_cue_count"] if quarantine else 0,
            "sequence":snap["sequence"],"ledger_head_sha256":snap["ledger_head_sha256"],
            "private_chat_revision_sha256":saved["private_chat_revision_sha256"],
            "sqlite_integrity_ok":True,"reopened_exact_revision":True,
            "idempotent_replay":True,"research_complete":False,
            "independent_gold_verified":False,"p0_go":False}
