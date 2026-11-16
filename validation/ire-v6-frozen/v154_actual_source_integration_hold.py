"""V154 public SHA-only integration hold for real private owner corrections.

It verifies private-packet identity commitments and fail-closed control status.
It does NOT issue new native host V6 receipts or assert semantic certainty.
"""
from __future__ import annotations

import re

SOURCE_SHA = "638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d"
SCHEMA = "V154_PRIVATE_SOURCE_CORRECTION_AND_DISPOSITION_REAL_HOLD_V1"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class V154GateError(ValueError):
    pass


def _need(ok, code):
    if not ok:
        raise V154GateError("V154_" + code)


def audit_v154_sha_only(receipt: dict):
    _need(type(receipt) is dict and receipt.get("schema") == SCHEMA, "SCHEMA")
    _need(receipt.get("original_sha256") == SOURCE_SHA, "SOURCE_DRIFT")
    checks = {
        "original_cues": 1481,
        "segments": 13,
        "atom_count_after_correction": 276,
        "confirmed_new_atom_structure_corrections": 1,
        "confirmed_new_cue_disposition_resolutions": 6,
        "original_unresolved_cue_count": 108,
        "remaining_unresolved_cue_count": 102,
        "post_revision_host_native_receipt_count": 0,
        "v123_final_approved_segments": 0,
        "v128_parent_publications": 0,
    }
    for key, expected in checks.items():
        _need(type(receipt.get(key)) is int and receipt[key] == expected,
              "FALSE_COUNT_" + key.upper())
    _need(receipt["original_unresolved_cue_count"] -
          receipt["confirmed_new_cue_disposition_resolutions"] ==
          receipt["remaining_unresolved_cue_count"], "DISPOSITION_ARITHMETIC")
    for segment in range(1, 14):
        name = f"V154_B{segment:04d}_CORRECTED_V6_EXCHANGE_DRAFT_sha256"
        value = receipt.get(name)
        _need(type(value) is str and HEX64.fullmatch(value) is not None,
              "PRIVATE_SEGMENT_EXCHANGE_PIN_" + str(segment))
    _need(type(receipt.get("private_status_sha256")) is str and
          HEX64.fullmatch(receipt["private_status_sha256"]) is not None,
          "PRIVATE_STATUS_PIN")
    for field in (
        "gold_precision_measured", "gold_recall_measured",
        "high_risk_fn_zero_proven",
        "approved_video_knowledge_advice_available", "P0E_GO",
    ):
        _need(receipt.get(field) is False, "FALSE_GO_" + field.upper())
    return {
        "owner_srt_verified_cues": 1481,
        "source_plan_segments_verified_locally": 13,
        "draft_atom_count": 276,
        "actual_source_bound_atom_corrections": 1,
        "source_first_no_atom_dispositions": 6,
        "remaining_original_unresolved_cues": 102,
        "new_native_v6_host_receipts": 0,
        "formal_v123_approved": 0,
        "v128_published": 0,
        "real_approved_knowledge_advice_tested": False,
        "precision_recall_or_high_risk_FN_certified": False,
        "p0e_go": False,
        "status": "V154_REAL_SOURCE_CORRECTION_PARTIAL_INTEGRATION_HOST_AND_GOLD_HOLD",
    }


def require_actual_native_host_for_v123(v154_public_receipt: dict,
                                       actual_host_receipts: list,
                                       ledger_snapshots_by_scope: dict | None = None):
    """Require 13 verifiable native V6 receipt heads before V123 review.

    The caller must supply actual private ledger replay snapshots, not user-
    supplied unverified SHA-only claims. Passing this gate permits V123 REVIEW
    only; it does not approve any ChatGPT meaning or V128 knowledge.
    """
    status = audit_v154_sha_only(v154_public_receipt)
    _need(type(actual_host_receipts) is list, "HOST_RECEIPTS_REQUIRED")
    _need(len(actual_host_receipts) == 13, "THIRTEEN_NATIVE_RECEIPTS_MISSING")
    _need(type(ledger_snapshots_by_scope) is dict, "PRIVATE_LEDGER_REPLAY_REQUIRED")
    scopes = set()
    for receipt in actual_host_receipts:
        _need(type(receipt) is dict and
              receipt.get("schema") == "IRE_V6_HOST_BATCH_RECEIPT_V1" and
              receipt.get("atomic_batch_committed") is True and
              receipt.get("is_current") is True and
              receipt.get("human_semantic_review_pending") is True and
              receipt.get("semantic_truth_certified") is False and
              receipt.get("p0_go") is False, "NATIVE_RECEIPT_SCHEMA_OR_STATUS")
        scope = receipt.get("scope_id")
        _need(type(scope) is str and scope not in scopes, "HOST_SCOPE_DUPLICATE")
        scopes.add(scope)
        event = receipt.get("event_sha256")
        _need(type(event) is str and HEX64.fullmatch(event) is not None,
              "HOST_EVENT_SHA")
        snap = ledger_snapshots_by_scope.get(scope)
        _need(type(snap) is dict and
              snap.get("ledger_head_sha256") == event and
              type(snap.get("progress")) is dict and
              snap["progress"].get("model_windows_recorded") ==
              receipt.get("source_and_proof_model_windows") and
              snap["progress"].get("current_revision_structural_proof_records") ==
              receipt.get("source_and_proof_model_windows"),
              "REAL_LEDGER_HEAD_OR_PROOF_MISSING")
    return {
        **status,
        "new_native_v6_host_receipts": 13,
        "native_receipt_heads_replayed": True,
        "v123_review_permitted": True,
        "v123_review_completed": False,
        "v128_published": 0,
        "p0e_go": False,
    }
