"""V151: source-bound P0-E remediation gate, never a semantic accuracy oracle.

Private SRT, propositions and candidate exchanges stay outside GitHub. The
public receipt is a SHA-only *HOLD* commitment. Tests are synthetic. This gate
rejects attempts to relabel structural lineage checks as final meaning, gold,
V123 authorization, V128 publication, or personal-advice approval.
"""
from __future__ import annotations

import hashlib
import json
import re

HEX = re.compile(r"[0-9a-f]{64}\Z")
SCHEMA = "V151_PRIVATE_SOURCE_REMEDIATION_SUMMARY_V1"
HOLD = "PRIVATE_SOURCE_FIRST_DRAFT_CORRECTIONS_REPLAY_HOLD_NO_APPROVAL"


class V151RemediationError(ValueError):
    pass


def _require(ok, name):
    if not ok:
        raise V151RemediationError("V151_" + name)


def digest(value):
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def audit_public_hold_receipt(r: dict) -> dict:
    """Count/hash/invariant audit only. A self-attested receipt is NOT quality proof."""
    _require(type(r) is dict and r.get("schema") == SCHEMA, "SCHEMA")
    sha_keys = (
        "source_sha256", "change_sha256", "237_cue_triage_sha256",
        "202_claim_lineage_sha256", "seam_sha256",
        "new_b0012_exchange_sha256", "new_b0013_exchange_sha256",
    )
    for key in sha_keys:
        _require(type(r.get(key)) is str and bool(HEX.fullmatch(r[key])),
                 "SHA_" + key.upper())
    numbers = {
        "original_cue_count": 1481,
        "old_v145_atoms": 274,
        "prior_unreferenced_count": 254,
        "v150_reviewed_cues": 17,
        "v151_remaining_screened": 237,
        "v151_pending_semantic_gold_cues": 237,
        "prior_pending_claims": 202,
        "v151_pending_claims_structurally_verified": 202,
        "v151_pending_claims_semantically_approved": 0,
        "existing_v123_final_approved_scopes": 0,
        "v128_new_publication_count": 0,
        "draft_correction_count": 7,
    }
    for key, expected in numbers.items():
        _require(type(r.get(key)) is int and r[key] == expected,
                 "COUNT_" + key.upper())
    _require(r.get("v150_reviewed_cues", 0) +
             r.get("v151_remaining_screened", 0) ==
             r["prior_unreferenced_count"], "UNREFERENCED_PARTITION")
    _require(r.get("revised_segment_atoms") == {"B0012": 17, "B0013": 6}
             and r.get("new_claim_ids") == ["C00275", "C00276"],
             "ATOMIC_SPLITS_NOT_PINNED")
    _require(r.get("video_id") == "5NvtBlmt93Y", "VIDEO")
    _require(r.get("status") == HOLD, "HOLD_STATUS_REQUIRED")
    must_be_false = (
        "host_v6_exchange_reissued",
        "chat_final_semantic_review_all_13_completed",
        "current_law_individual_application_approved",
        "full_video_precision_measured", "full_video_recall_measured",
        "externally_independent_gold", "p0e_go", "p0_go",
    )
    for key in must_be_false:
        _require(r.get(key) is False, "FALSE_COMPLETION_" + key.upper())
    return {
        "schema": "V151_PUBLIC_NO_FALSE_APPROVAL_RESULT_V1",
        "source_sha256": r["source_sha256"],
        "source_cues_partition_screened": 254,
        "prior_pending_claims_structurally_reconciled": 202,
        "meaning_approved_claims_added": 0,
        "v123_approved_scopes": 0,
        "v128_published": 0,
        "p0e_go": False, "p0_go": False,
        "status": "REMEDIATION_DRAFT_PINNED_SEMANTIC_AND_HOST_REPLAY_OPEN",
        "source_text_present_in_public_receipt": False,
        "gold_precision_or_recall_certified": False,
    }


def verify_private_cue_partition(v149_queue, v150_reviewed, v151_triage,
                                 source_text_by_cue: dict):
    """Owner-private audit: all 254 source gap cues are pinned and partitioned."""
    _require(type(v149_queue) is list and len(v149_queue) == 254,
             "SOURCE_254_QUEUE")
    _require(type(v150_reviewed) is list and len(v150_reviewed) == 17,
             "SOURCE_17_REVIEWED")
    _require(type(v151_triage) is list and len(v151_triage) == 237,
             "SOURCE_237_TRIAGE")
    _require(type(source_text_by_cue) is dict and len(source_text_by_cue) == 1481,
             "OWNER_1481_SOURCE_REQUIRED")
    expected = set(range(1, 1482))
    _require(set(source_text_by_cue) == expected, "OWNER_CUE_RANGE")
    baseline = [x["cue_index"] for x in v149_queue]
    first = [x["cue_index"] for x in v150_reviewed]
    last = [x["cue_index"] for x in v151_triage]
    _require(len(set(baseline)) == 254 and len(set(first)) == 17 and
             len(set(last)) == 237 and not (set(first) & set(last))
             and set(first) | set(last) == set(baseline),
             "SOURCE_PARTITION_NOT_EXHAUSTIVE")
    for row in v149_queue:
        i = row["cue_index"]
        _require(row["original_text"] == source_text_by_cue[i] and
                 row["source_text_sha256"] == hashlib.sha256(
                     source_text_by_cue[i].encode("utf-8")
                 ).hexdigest(), "V149_SOURCE_DRIFT")
    for row in v151_triage:
        i = row["cue_index"]
        _require(row.get("source_text_sha256") == hashlib.sha256(
                     source_text_by_cue[i].encode("utf-8")
                 ).hexdigest() and
                 row.get("semantic_gold_finalized") is False and
                 row.get("pending_v123") is True and
                 row.get("possible_false_negative_not_certified") is True,
                 "TRIAGE_MASQUERADES_AS_GOLD")
    return {"source_only_triage": 237, "pending_gold": 237,
            "source_sha_checks": 254, "final_semantic_certified": False}


def verify_provisional_seam(b12: dict, b13: dict,
                            source_text_by_cue: dict):
    """Private syntactic/seam guard; ChatGPT must still review speaker and meaning."""
    _require(b12.get("schema") == "IRE_V6_HOST_ATOMIC_EXCHANGE_V1" and
             b13.get("schema") == "IRE_V6_HOST_ATOMIC_EXCHANGE_V1",
             "HOST_SCHEMA")
    _require(b12.get("source_sha256") == b13.get("source_sha256") and
             b12.get("video_id") == b13.get("video_id"),
             "SOURCE_IDENTITY")
    atoms = {}
    for packet in (b12, b13):
        for atom in packet.get("atoms", []):
            cid = atom.get("claim_id")
            _require(cid not in atoms and type(cid) is str,
                     "DUPLICATE_CLAIM_ID")
            atoms[cid] = atom
            refs = atom.get("source_refs")
            _require(type(refs) is list and len(refs) > 0,
                     "MISSING_REF")
            positions = [ref["cue_index"] for ref in refs]
            _require(positions == sorted(set(positions)), "BAD_REF_ORDER")
            for ref in refs:
                i = ref["cue_index"]
                _require(i in source_text_by_cue and
                         type(ref.get("quote")) is str and
                         ref["quote"] in source_text_by_cue[i],
                         "QUOTE_NOT_FROM_OWNER_SOURCE")
    for cid in ("C00261", "C00262", "C00268", "C00269",
                "C00270", "C00271", "C00275", "C00276"):
        _require(cid in atoms, "MANDATORY_ATOM_MISSING_" + cid)
    def refs(cid):
        return [x["cue_index"] for x in atoms[cid]["source_refs"]]
    _require(refs("C00261") == list(range(1377, 1384)) and
             refs("C00276") == list(range(1384, 1388)),
             "BOOK_PRINCIPLE_AND_GUEST_PREFERENCE_MERGED")
    _require(refs("C00262") == list(range(1388, 1391)),
             "PERSONAL_REFLECTION_SOURCE_POLLUTED")
    _require(refs("C00269") == [1437, 1438] and
             atoms["C00269"]["stance"] == "QUOTED",
             "MISATTRIBUTED_RECOMMENDATION_OR_SEAM")
    _require(refs("C00270") == [1441, 1442] and
             refs("C00275") == [1443, 1444, 1445, 1446],
             "TWO_RISKS_COMBINED")
    _require(atoms["C00275"]["kind"] == "OPINION" and
             atoms["C00275"]["stance"] == "CONDITIONAL" and
             set([1444, 1445]).issubset(
                 set(atoms["C00275"]["condition_cue_indices"])),
             "CONCENTRATION_RISK_CONDITION_LOST")
    b12_rows = {x["cue_index"]: x for x in b12["cue_dispositions"]}
    _require(b12_rows[1439]["disposition"] == "UNRESOLVED" and
             b12_rows[1440]["disposition"] == "UNRESOLVED" and
             not b12_rows[1440]["claim_ids"], "CROSS_PARENT_SEAM_FALSE_CLOSED")
    _require(len(b12["atoms"]) == 17 and len(b13["atoms"]) == 6,
             "SPLIT_COUNT")
    for packet in (b12, b13):
        mapping = {}
        for atom in packet["atoms"]:
            for ref in atom["source_refs"]:
                mapping.setdefault(ref["cue_index"], set()).add(atom["claim_id"])
        for row in packet["cue_dispositions"]:
            i = row["cue_index"]
            _require(set(row["claim_ids"]) == mapping.get(i, set()),
                     "CUE_TO_ATOM_MAPPING_NOT_CURRENT")
    return {"candidate_atoms_in_two_segments": 23,
            "source_bound_corrections_staged": True,
            "cross_segment_cue_1439_1440_semantics_open": True,
            "v123_approved": False,
            "v128_published": False,
            "p0e_go": False}
