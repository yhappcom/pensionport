"""V144 metadata-only real-source migration barrier (not V123 final review).

A source-first provisional packet is not a native V6 host atomic exchange.
This guard prevents QA dashboards or runners from silently substituting V141
claim IDs or V142 triage labels for source-bound V123 ChatGPT verdicts.
Only public SHA/count metadata is examined; no owner-private transcript text.
"""
from __future__ import annotations

import re
from typing import Mapping

EXPECTED_SOURCE_SHA = "638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d"
EXPECTED_SCHEMA = "V144_REAL_SOURCE_TO_V143_QUARANTINE_PREPARATION_HOLD_V1"
_SHA = re.compile(r"[0-9a-f]{64}\Z")


class QuarantineEvidenceNotComplete(ValueError):
    """Caller must supply actual canonical V6 and V123 artifacts next."""


def assess_real_source_preflight(receipt: Mapping) -> dict:
    """Check exact source scope and source-review triage; never grant GO."""
    if not isinstance(receipt, dict):
        raise QuarantineEvidenceNotComplete("V144_METADATA_NOT_MAPPING")
    expected = {
        "schema": EXPECTED_SCHEMA,
        "source_sha256": EXPECTED_SOURCE_SHA,
        "video_id": "5NvtBlmt93Y",
        "original_cue_count": 1481,
        "v141_provisional_cues_with_status_census": 1481,
        "v141_provisional_atom_occurrences": 274,
        "v142_original_open_cues": 88,
        "context_classifiable_audio_not_authenticated": 36,
        "candidate_high_impact_cue_quarantines": 52,
        "claims_adjacent_to_quarantined_cues_for_dependency_review": 83,
        "other_claims_not_adjacent_to_high_impact_quarantine": 191,
        "all_open_neighbor_atom_union": 138,
        "original_audio_available_in_user_original_archive": False,
        "provisional_atom_ids_are_not_v6_canonical_claim_ids": True,
        "v123_quarantine_ledger_source_bound": True,
        "v123_canonical_atom_sha256_not_yet_bound": True,
        "v6_owner_host_receipts_verified": 0,
        "v123_final_approved_segments": 0,
        "v128_private_knowledge_entries_published": 0,
        "precision_recall_measured_on_independent_gold": False,
        "personalized_advice_approved": False,
        "p0_go": False,
        "status": "REAL_SOURCE_QUARANTINE_AND_DEPENDENCY_REVIEW_PREPARED_V123_FINAL_HOLD",
    }
    bad = [k for k, v in expected.items() if type(receipt.get(k)) is not type(v) or receipt.get(k) != v]
    if bad:
        raise QuarantineEvidenceNotComplete("V144_TRIAGE_OR_FALSE_APPROVAL:" + ",".join(sorted(bad)))
    for key in ("quarantine_rows_digest_sha256", "atom_preparation_rows_digest_sha256",
                "segment_preflight_digest_sha256"):
        if type(receipt.get(key)) is not str or not _SHA.fullmatch(receipt[key]):
            raise QuarantineEvidenceNotComplete("V144_MISSING_OR_INVALID_OWNER_PREPARATION_DIGEST:" + key)
    return {
        "schema": "V144_SOURCE_FIRST_PREPARATION_PUBLIC_GATE_V1",
        "source_sha256": EXPECTED_SOURCE_SHA,
        "reviewed_source_cues": 1481,
        "source_only_audio_context_cases": 36,
        "proposed_quarantine_cues": 52,
        "provisional_atoms_requiring_dependency_adjudication": 83,
        "canonical_v6_host_replay_required": True,
        "source_bound_v123_all_child_reviews_required": True,
        "v128_signed_parent_release_required": True,
        "status": "SOURCE_FIRST_PREP_ONLY_NATIVE_V6_V123_V128_HOLD",
        "knowledge_export_allowed": False,
        "personalized_advice_approved": False,
        "p0_go": False,
    }


def require_native_v123_release_from_provisional(receipt: Mapping) -> None:
    """A provisional V141 schema can NEVER be treated as a signed V123 gate.

    Call real V6 host + V123/V128 validation with canonical exchange records
    after independently capturing source-bound ChatGPT decisions.
    """
    assess_real_source_preflight(receipt)
    raise QuarantineEvidenceNotComplete("V144_PROVISIONAL_PACKET_IS_NOT_V123_APPROVAL")
