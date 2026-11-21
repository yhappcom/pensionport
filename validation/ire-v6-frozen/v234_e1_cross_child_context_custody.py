"""V234: actual V228 full-source atom graph -> lossless private cross-child context escrow.

The frozen V127 splits 250 source cues into 13 bounded children.  A source
claim can *reference cues outside its child*.  The child V6 audit forbids
outside-scope context/qualifiers/numbers, so naively trimming references would
change meaning.  Transport those references in an exact original-text,
source-SHA-bound private sidecar and explicitly HOLD V123/E4/E5 publication
until semantic cross-scope review and real child evidence are present.

This is a deterministic custody and risk frontier, NOT semantic judgment,
independent accuracy, verified user-turn identity or authority to publish.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.codec import ZERO_SHA, json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from v1271_parent_resume_checkpoint import PrivateFullVideoCheckpoint
from v230_e1_v228_source_native_handoff import SCHEMA as V230_SCHEMA

SCHEMA = "IRE_V234_E1_FULL_SOURCE_CROSS_CHILD_CONTEXT_ESCROW_V1"


def _need(ok: Any, code: str) -> None:
    if not ok:
        raise InvalidInput("V234_E1_" + code)


def _child_map(checkpoint):
    out = {}
    for segment_id, m in zip(checkpoint.child_ids, checkpoint.child_manifests):
        for idx in range(m["scope"]["first_cue"], m["scope"]["last_cue"] + 1):
            _need(idx not in out, "CHILD_CUE_DUPLICATE")
            out[idx] = segment_id
    _need(set(out) == set(range(1, len(checkpoint.parent.cues) + 1)),
          "CHILD_SOURCE_NOT_EXHAUSTIVE")
    return out


def build_lossless_context_escrow(*, origin: dict,
                                   checkpoint: PrivateFullVideoCheckpoint,
                                   externally_pinned_parent_plan_sha256: str,
                                   externally_pinned_checkpoint_head_sha256: str,
                                   externally_pinned_source_sha256: str,
                                   externally_pinned_exchange_digest: str) -> dict:
    """Private raw-source-backed cross-segment graph, NO semantic approvals.

    The expected pins must have been held separately from the supplied mutable
    origin/checkpoint, otherwise hash equality is not an independent attestation.
    """
    _need(type(origin) is dict and origin.get("schema") == V230_SCHEMA
          and isinstance(checkpoint, PrivateFullVideoCheckpoint),
          "VERIFIED_ORIGIN_AND_PARENT_REQUIRED")
    source = origin["source"]
    exchange = origin["exchange"]
    _need(source.source_sha256 == externally_pinned_source_sha256
          and origin["source_sha256"] == externally_pinned_source_sha256
          and checkpoint.parent.source_sha256 == externally_pinned_source_sha256
          and checkpoint.parent.cue_census_sha256 == source.cue_census_sha256
          and checkpoint.owner_pin == origin["inventory_sha256"]
          and checkpoint.raw == origin["source_raw"]
          and checkpoint.parent_manifest == origin["manifest"]
          and checkpoint.parent_inventory == origin["inventory_bytes"]
          and checkpoint.plan_pin == externally_pinned_parent_plan_sha256
          and json_digest(exchange) == externally_pinned_exchange_digest
          and origin["native_exchange_digest"] == externally_pinned_exchange_digest,
          "EXTERNAL_SOURCE_EXCHANGE_OR_PARENT_PIN_DRIFT")
    progress = checkpoint.progress(externally_pinned_checkpoint_head=
                                   externally_pinned_checkpoint_head_sha256)
    _need(progress["expected_child_scopes"] == len(checkpoint.child_ids),
          "CHECKPOINT_CHILD_CENSUS")
    audit = audit_host_atomic_exchange(source, exchange)
    _need(audit["proposed_atomic_claims"] == origin["unapproved_atoms"],
          "NATIVE_FULL_ATOM_CENSUS")
    ownership = _child_map(checkpoint)
    full_claim_ids = {a["claim_id"] for a in exchange["atoms"]}
    _need(len(full_claim_ids) == origin["unapproved_atoms"],
          "DUPLICATE_ATOM_ID")
    local = []
    cross = []
    conditions_cross = 0
    numeric_cross = 0
    external_cue_edges = 0
    for atom in exchange["atoms"]:
        cid = atom["claim_id"]
        primary = atom["source_refs"][0]["cue_index"]
        owner = ownership[primary]
        source_indices = {x["cue_index"] for x in atom["source_refs"]}
        context_indices = set(atom["context_cue_indices"])
        condition_indices = set(atom["condition_cue_indices"])
        exception_indices = set(atom["exception_cue_indices"])
        numbers = atom["numeric_references"]
        number_indices = {x["cue_index"] for x in numbers}
        referenced = sorted(source_indices | context_indices | condition_indices |
                            exception_indices | number_indices)
        _need(all(1 <= i <= len(source.cues) for i in referenced),
              "CROSS_SOURCE_CUE_OUT_OF_RANGE")
        neighbor = sorted({ownership[i] for i in referenced})
        cross_scope = neighbor != [owner]
        if not cross_scope:
            local.append(cid)
            continue
        conditions_cross += int(any(ownership[i] != owner
                                     for i in condition_indices | exception_indices))
        numeric_cross += int(any(ownership[i] != owner for i in number_indices))
        external_cue_edges += sum(ownership[i] != owner for i in referenced)
        context_cues = []
        for i in referenced:
            cue = source.cues[i - 1]
            roles = []
            if i in source_indices: roles.append("PRIMARY_SOURCE")
            if i in context_indices: roles.append("CONTEXT")
            if i in condition_indices: roles.append("CONDITION")
            if i in exception_indices: roles.append("EXCEPTION")
            if i in number_indices: roles.append("NUMERIC_SOURCE")
            context_cues.append({
                "cue_index":i,"segment_id":ownership[i],
                "cue_text":cue.text,
                "cue_text_sha256":sha256(cue.text.encode("utf-8")),
                "reference_roles":roles,
                "numeric_tokens":[r["token"] for r in numbers if r["cue_index"] == i],
            })
        cross.append({
            "claim_id":cid,"original_atom_sha256":json_digest(atom),
            "primary_segment_id":owner,"referenced_segment_ids":neighbor,
            "cross_segment_cues":context_cues,
            "status":"OPEN_REQUIRES_CHATGPT_CROSS_SCOPE_SOURCE_SEMANTIC_REVIEW",
            "meaning_approved":False,
            "finance_approved":False,
        })
    _need(len(local) + len(cross) == origin["unapproved_atoms"],
          "ATOM_FRONTIER_COVERAGE_LOSS")
    return {
        "schema":SCHEMA,
        "source_sha256":externally_pinned_source_sha256,
        "native_exchange_digest":externally_pinned_exchange_digest,
        "owner_inventory_sha256":origin["inventory_sha256"],
        "parent_plan_sha256":externally_pinned_parent_plan_sha256,
        "checkpoint_head_sha256":externally_pinned_checkpoint_head_sha256,
        "child_count":len(checkpoint.child_ids),
        "source_cue_count":len(source.cues),
        "full_atom_count":origin["unapproved_atoms"],
        "all_local_atom_ids":local,
        "cross_segment_atom_rows":cross,
        "cross_segment_atom_count":len(cross),
        "cross_segment_qualifier_atom_count":conditions_cross,
        "cross_segment_numeric_atom_count":numeric_cross,
        "external_cue_reference_edges":external_cue_edges,
        "cross_scope_semantic_review_completed":False,
        "host_user_turn_identity_cryptographically_verified":False,
        "v123_final_approval":False,
        "e4_authorized":False,
        "e5_published":False,
        "status":"CROSS_SEGMENT_FULL_SOURCE_CUSTODY_PASS_REVIEW_HOLD"
    }


def verify_escrow_bytes(*, origin: dict, checkpoint: PrivateFullVideoCheckpoint,
                         escrow: dict, externally_pinned_escrow_sha256: str,
                         externally_pinned_parent_plan_sha256: str,
                         externally_pinned_checkpoint_head_sha256: str,
                         externally_pinned_source_sha256: str,
                         externally_pinned_exchange_digest: str) -> dict:
    """Rebuild and compare *all* context quotes, numeric and qualifier indices."""
    _need(type(escrow) is dict and
          json_digest(escrow) == externally_pinned_escrow_sha256,
          "EXTERNAL_CONTEXT_ESCROW_HASH_MISMATCH")
    expected = build_lossless_context_escrow(
        origin=origin,checkpoint=checkpoint,
        externally_pinned_parent_plan_sha256=externally_pinned_parent_plan_sha256,
        externally_pinned_checkpoint_head_sha256=externally_pinned_checkpoint_head_sha256,
        externally_pinned_source_sha256=externally_pinned_source_sha256,
        externally_pinned_exchange_digest=externally_pinned_exchange_digest)
    _need(escrow == expected, "CROSS_SCOPE_CUE_OR_ATOM_CONTEXT_SUBSTITUTED")
    return {
        "schema":"IRE_V234_E1_CONTEXT_ESCROW_READBACK_V1",
        "status":"ALL_PARENT_CROSS_REFERENCES_BYTE_VERIFIED_APPROVAL_HOLD",
        "cross_segment_atom_count":expected["cross_segment_atom_count"],
        "cross_segment_qualifier_atom_count":expected["cross_segment_qualifier_atom_count"],
        "cross_segment_numeric_atom_count":expected["cross_segment_numeric_atom_count"],
        "external_cue_reference_edges":expected["external_cue_reference_edges"],
        "escrow_sha256":externally_pinned_escrow_sha256,
        "e3_final_approved":False,
        "e4_authorized":False,
        "e5_published":0,
    }


def require_complete_real_child_release(*, escrow: dict,
                                         checkpoint: PrivateFullVideoCheckpoint,
                                         externally_pinned_checkpoint_head_sha256: str) -> None:
    """Real ETF never gains E3/E4/E5 approval from source SHA or manual refs."""
    _need(type(escrow) is dict and escrow.get("schema") == SCHEMA,
          "CROSS_SCOPE_RECEIPT_REQUIRED")
    progress = checkpoint.progress(externally_pinned_checkpoint_head=
                                   externally_pinned_checkpoint_head_sha256)
    if (escrow["cross_segment_atom_count"] or
        progress["passed_child_scopes"] != progress["expected_child_scopes"] or
        escrow["host_user_turn_identity_cryptographically_verified"] is False):
        raise QualityNotProven(
            "V234_E1_OPEN_CROSS_SCOPE_ATOMS_OR_UNVERIFIED_CHILD_REVIEWS_AND_HOST_TURNS")
    # Independent E2 and E3 approvals, true ChatGPT host review and V123/E4
    # evidence must be presented to the ordinary frozen gates. This custody
    # helper does not grant any release, even on a no-cross synthetic fixture.
    raise QualityNotProven("V234_E1_ACTUAL_V123_E4_E5_REQUIRED")