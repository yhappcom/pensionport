"""Generic fail-closed human-annotated source attribution contract.

This module does not infer speakers, correct ASR or claim financial truth.
It validates provenance/uncertainty before a claim can be eligible for a
human-reviewed evidence and prior-knowledge relation stage.
"""
from __future__ import annotations
from dataclasses import dataclass
import re

SPEAKER_KINDS = frozenset({"HOST_CLAIM", "COMMENT_CASE", "UNCERTAIN_SPEAKER"})
CLAIM_KINDS = frozenset({"RULE", "OPINION", "HYPOTHETICAL", "PERSONAL_CASE", "RECOMMENDATION", "MATH"})
UNCERTAINTY_FLAGS = frozenset({
    "ASR_OPEN", "BOUNDARY_OPEN", "SPEAKER_OPEN", "PRODUCT_ID_OPEN",
    "PERSONAL_SUITABILITY_OPEN", "HISTORICAL_EVENT_OPEN", "EVIDENCE_OPEN",
})
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_WID = re.compile(r"W[0-9]{5}\Z")

class AttributionContractError(ValueError):
    pass

@dataclass(frozen=True)
class AttributedClaim:
    video_id: str
    window_id: str
    source_sha256: str
    cue_index: int
    cue_text_sha256: str
    speaker_kind: str
    claim_kind: str
    uncertainty_flags: frozenset[str]
    source_quote_verified: bool
    context_cues_checked: tuple[int, ...]
    personal_advice_approved: bool = False
    fact_approved: bool = False


def validate_attributed_claim(claim: AttributedClaim, *, cue_hashes: dict[int, str],
                              active_window_cues: set[int]) -> None:
    if not claim.video_id or not _WID.fullmatch(claim.window_id):
        raise AttributionContractError("INVALID_WINDOW_OR_VIDEO_ID")
    if not _SHA.fullmatch(claim.source_sha256):
        raise AttributionContractError("SOURCE_SHA256_REQUIRED")
    if claim.cue_index not in active_window_cues or cue_hashes.get(claim.cue_index) != claim.cue_text_sha256:
        raise AttributionContractError("SOURCE_CUE_ANCHOR_MISMATCH")
    if claim.speaker_kind not in SPEAKER_KINDS or claim.claim_kind not in CLAIM_KINDS:
        raise AttributionContractError("UNSUPPORTED_ATTRIBUTION_KIND")
    if not isinstance(claim.uncertainty_flags, frozenset) or not claim.uncertainty_flags <= UNCERTAINTY_FLAGS:
        raise AttributionContractError("UNKNOWN_UNCERTAINTY_FLAG")
    if claim.cue_index not in claim.context_cues_checked or not all(x in cue_hashes for x in claim.context_cues_checked):
        raise AttributionContractError("ADJACENT_CONTEXT_NOT_REVIEWED")
    if claim.speaker_kind == "COMMENT_CASE" and claim.claim_kind != "PERSONAL_CASE":
        raise AttributionContractError("COMMENT_CANNOT_BE_PROMOTED_TO_HOST_RULE")
    if claim.speaker_kind == "UNCERTAIN_SPEAKER" and "SPEAKER_OPEN" not in claim.uncertainty_flags:
        raise AttributionContractError("UNCERTAIN_SPEAKER_REQUIRES_FLAG")
    if not claim.source_quote_verified and "ASR_OPEN" not in claim.uncertainty_flags:
        raise AttributionContractError("ASR_UNVERIFIED_REQUIRES_OPEN_FLAG")
    if claim.personal_advice_approved or claim.fact_approved:
        raise AttributionContractError("NO_AUTOMATIC_FACT_OR_PERSONAL_ADVICE_APPROVAL")


def validate_empty_window(*, window_id: str, cue_ids: list[int], source_cue_hashes: dict[int,str],
                          disposition: str, reviewer_marked: bool,
                          second_pass_marked: bool) -> None:
    if not _WID.fullmatch(window_id) or not cue_ids or len(set(cue_ids)) != len(cue_ids):
        raise AttributionContractError("INVALID_EMPTY_WINDOW_OWNERSHIP")
    if any(x not in source_cue_hashes or not _SHA.fullmatch(source_cue_hashes[x]) for x in cue_ids):
        raise AttributionContractError("EMPTY_WINDOW_SOURCE_CUES_NOT_HASHED")
    if disposition not in {"NO_FINANCIAL_ATOMIC_CLAIMS", "NONFINANCIAL_CLAIMS_ONLY"}:
        raise AttributionContractError("EMPTY_WINDOW_MISSING_EXPLICIT_DISPOSITION")
    if not reviewer_marked or not second_pass_marked:
        raise AttributionContractError("EMPTY_WINDOW_NOT_SECOND_PASS_REVIEWED")
