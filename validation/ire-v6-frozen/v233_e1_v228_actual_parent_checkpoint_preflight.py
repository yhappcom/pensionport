"""V233: verified V228 real source -> V232 V6 host -> NEW V127.1 parent plan.

A genuine source-native V6 host-only receipt can be handed to the FROZEN
V127.1 full-video coordinator without pretending that the V176 owner exists.
This performs NO V123 review, E4 approval or V128/V126 publication.

The 2-turn caller refs are manual, not host-cryptographic provenance. A real
V123 review and official evidence must be authored independently in ChatGPT.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any

from ire.v6 import TransactionStore
from ire.v6.codec import ZERO_SHA, require_hash
from ire.v6.errors import InvalidInput, QualityNotProven
from v1271_parent_resume_checkpoint import PrivateFullVideoCheckpoint
from v230_e1_v228_source_native_handoff import SCHEMA as V230_SCHEMA
from v231_e1_v228_private_turn2_custody_bridge import (
    verify_real_turn2_private_custody)

SCHEMA = "IRE_V233_REAL_V228_SOURCE_NATIVE_V1271_CHECKPOINT_PREFLIGHT_V1"


def _need(condition: Any, name: str) -> None:
    if not condition:
        raise InvalidInput("V233_E1_" + name)


def verify_v232_source_native_host(*, origin: dict,
                                   native_store: TransactionStore,
                                   scope_id: str,
                                   expected_host_head_sha256: str,
                                   expected_event_count: int,
                                   second_receipt: dict,
                                   private_source_note: dict,
                                   prequarantine: dict,
                                   externally_pinned_receipt_sha256: str,
                                   externally_pinned_source_note_sha256: str,
                                   externally_pinned_prequarantine_sha256: str,
                                   ) -> dict:
    """Read-only proof of a genuine, held V6 host scope bound to V231 bytes."""
    _need(isinstance(origin, dict) and origin.get("schema") == V230_SCHEMA and
          type(native_store) is TransactionStore and
          type(scope_id) is str and scope_id,
          "REAL_NATIVE_SOURCE_AND_STORE_REQUIRED")
    require_hash(expected_host_head_sha256, "V233_E1_EXTERNAL_HOST_HEAD")
    _need(type(expected_event_count) is int and expected_event_count >= 4,
          "HOST_EVENT_COUNT_REQUIRED")
    proof = verify_real_turn2_private_custody(
        origin=origin, second_receipt=second_receipt,
        private_source_note=private_source_note,
        prequarantine=prequarantine,
        externally_pinned_receipt_sha256=externally_pinned_receipt_sha256,
        externally_pinned_source_note_sha256=
            externally_pinned_source_note_sha256,
        externally_pinned_prequarantine_sha256=
            externally_pinned_prequarantine_sha256)
    snap = native_store.snapshot(scope_id)
    state = snap["state"]
    progress = snap["progress"]
    expected_windows = {wid for wid, _, _ in origin["source"].primary_windows}
    _need(snap["ledger_head_sha256"] == expected_host_head_sha256 and
          snap["sequence"] == expected_event_count,
          "EXTERNAL_HOST_HEAD_OR_SEQUENCE_CHANGED")
    _need(state["source"]["source_sha256"] == origin["source_sha256"] and
          state["source"]["manifest_sha256"] ==
              origin["source"].manifest_sha256,
          "HOST_SOURCE_OR_MANIFEST_SUBSTITUTED")
    _need(state["owner_pin"] is not None and
          state["owner_pin"]["inventory_sha256"] ==
              origin["inventory_sha256"],
          "V6_HOST_OWNER_INVENTORY_NOT_PINNED")
    _need(set(state["models"]) == expected_windows and
          set(state["structural_proofs"]) == expected_windows and
          progress["model_windows_recorded"] == len(expected_windows) and
          progress["current_revision_structural_proof_records"] ==
              len(expected_windows),
          "V6_HOST_ALL_ORIGINAL_WINDOWS_NOT_PRESENT")
    _need(progress["financial_facts_approved"] is False and
          progress["verified_proofs"] == 0 and
          progress["research_report_closed"] is False and
          progress["p0_go"] is False and
          proof["e3_final_approved"] is False and
          proof["e4_authorized"] is False and
          proof["e5_published"] == 0,
          "UNAPPROVED_HOST_SCOPE_CANNOT_BE_PROMOTED")
    return {
        "status": "V232_REAL_HOST_SCOPE_VERIFIED_UNAPPROVED",
        "source_sha256": origin["source_sha256"],
        "host_head_sha256": expected_host_head_sha256,
        "host_event_count": expected_event_count,
        "host_window_count": len(expected_windows),
        "cue_count": origin["cue_count"],
        "atom_count": origin["unapproved_atoms"],
        "prequarantine_cue_count": proof["unapproved_source_cues_escrowed"],
        "e3_final_approved": False,
        "e4_authorized": False,
        "e5_published": 0,
    }


def open_new_real_v1271_checkpoint(*, origin: dict,
                                    native_store: TransactionStore,
                                    scope_id: str,
                                    expected_host_head_sha256: str,
                                    expected_event_count: int,
                                    second_receipt: dict,
                                    private_source_note: dict,
                                    prequarantine: dict,
                                    externally_pinned_receipt_sha256: str,
                                    externally_pinned_source_note_sha256: str,
                                    externally_pinned_prequarantine_sha256: str,
                                    checkpoint_path: Path,
                                    max_cues: int = 20,
                                    expected_checkpoint_head_sha256: str = ZERO_SHA,
                                    ) -> dict:
    """Create/resume V127.1 pinned real source plan; NEVER invent child reviews.

    Does not claim history recovery. A newly created file is private (0600)
    from O_EXCL onward; caller must keep the parent directory private (0700).
    Existing checkpoints require an EXTERNAL pinned head and same source plan.
    """
    host = verify_v232_source_native_host(
        origin=origin, native_store=native_store, scope_id=scope_id,
        expected_host_head_sha256=expected_host_head_sha256,
        expected_event_count=expected_event_count,
        second_receipt=second_receipt,
        private_source_note=private_source_note,
        prequarantine=prequarantine,
        externally_pinned_receipt_sha256=externally_pinned_receipt_sha256,
        externally_pinned_source_note_sha256=
            externally_pinned_source_note_sha256,
        externally_pinned_prequarantine_sha256=
            externally_pinned_prequarantine_sha256)
    require_hash(expected_checkpoint_head_sha256,
                 "V233_E1_EXTERNAL_CHECKPOINT_HEAD")
    _need(type(max_cues) is int and 1 <= max_cues <= 120,
          "CHECKPOINT_MAX_CUES")
    target = Path(checkpoint_path)
    _need(target.suffix == ".db" and target.parent.is_dir() and
          not target.parent.is_symlink(), "PRIVATE_CHECKPOINT_LOCATION")
    if os.name == "posix":
        st = target.parent.stat()
        _need(st.st_uid == os.getuid() and not st.st_mode & 0o077,
              "PRIVATE_CHECKPOINT_DIRECTORY_MODE")
    _need(not target.is_symlink(), "CHECKPOINT_SYMLINK_NOT_ALLOWED")
    created = False
    if not target.exists():
        _need(expected_checkpoint_head_sha256 == ZERO_SHA,
              "NEW_CHECKPOINT_REQUIRES_ZERO_HEAD")
        fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        created = True
    elif os.name == "posix":
        _need(stat.S_ISREG(target.stat().st_mode) and
              not target.stat().st_mode & 0o077,
              "PRIVATE_CHECKPOINT_FILE_MODE")
    checkpoint = PrivateFullVideoCheckpoint(
        target, raw=origin["source_raw"],
        parent_manifest=origin["manifest"],
        parent_inventory=origin["inventory_bytes"],
        expected_parent_inventory_sha256=origin["inventory_sha256"],
        max_cues=max_cues)
    progress = checkpoint.progress(
        externally_pinned_checkpoint_head=expected_checkpoint_head_sha256)
    _need(sum((progress["passed_child_scopes"],
               progress["held_child_scopes"],
               progress["missing_child_scopes"])) ==
          progress["expected_child_scopes"], "CHILD_PLAN_CENSUS")
    _need(progress["ready_for_full_parent_replay"] is False and
          progress["passed_child_scopes"] == 0 and
          progress["engine_research_complete"] is False and
          progress["p0_go"] is False,
          "UNAPPROVED_REAL_CHILD_CANNOT_BE_RELEASED")
    _need(checkpoint.parent.source_sha256 == host["source_sha256"] and
          sum(1 for _ in checkpoint.child_manifests) ==
              progress["expected_child_scopes"],
          "CHILD_PARENT_REAL_SOURCE_NOT_BOUND")
    return {
        "schema": SCHEMA,
        "status": "REAL_ETF_V1271_SOURCE_PINNED_CHILD_REVIEW_HOLD",
        "checkpoint_created_now": created,
        "source_sha256": host["source_sha256"],
        "v6_host_head_sha256": host["host_head_sha256"],
        "v6_host_events": host["host_event_count"],
        "v6_host_windows": host["host_window_count"],
        "parent_plan_sha256": progress["parent_plan_sha256"],
        "v1271_checkpoint_head_sha256": progress["checkpoint_head_sha256"],
        "source_cues": host["cue_count"],
        "unapproved_atoms": host["atom_count"],
        "source_cues_quarantined": host["prequarantine_cue_count"],
        "v1271_expected_children": progress["expected_child_scopes"],
        "v1271_children_passed": 0,
        "v1271_children_missing": progress["missing_child_scopes"],
        "e1_real_host_stage_proven": True,
        "v123_chat_final_released": False,
        "v128_parent_assembly_allowed": False,
        "v126_knowledge_published": False,
        "e3_final_approved": False,
        "e4_authorized": False,
        "e5_published": 0,
    }


def require_actual_e1_full_release_ready(*, checkpoint_receipt: dict) -> None:
    """Force an explicit stop for genuine unapproved E2/E3 inputs."""
    _need(type(checkpoint_receipt) is dict and
          checkpoint_receipt.get("schema") == SCHEMA,
          "CHECKPOINT_RECEIPT_REQUIRED")
    raise QualityNotProven(
        "V233_E1_ACTUAL_E2_E3_VERDICTS_AND_V123_E4_E5_APPROVAL_REQUIRED"
    )