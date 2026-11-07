"""Generic non-overlapping source-window accounting for human-reviewed P0 receipts.

No model inference, source SRT text or financial fact approval is performed here.
"""
from __future__ import annotations
from dataclasses import dataclass

class WindowCoverageError(ValueError):
    pass

@dataclass(frozen=True)
class ReviewedWindow:
    window_id: str
    first_cue: int
    last_cue: int
    claim_count: int
    source_sha256: str
    reviewer_status: str

def validate_new_window_batch(
    windows: list[ReviewedWindow],
    *,
    previously_reviewed: set[str],
    expected_source_sha256: str,
    expected_window_ids: set[str],
    next_window_id: str,
) -> dict:
    """Fail closed on duplicate windows, source drift, false claimless completion.

    Adjacent context from already reviewed windows may be read but is never
    counted as newly completed. This protects hour-to-hour accounting.
    """
    if not windows or not expected_window_ids or not next_window_id:
        raise WindowCoverageError("EMPTY_OR_UNBOUNDED_RESEARCH_BATCH")
    if len(expected_source_sha256) != 64:
        raise WindowCoverageError("SOURCE_HASH_MISSING")
    ids = [w.window_id for w in windows]
    if len(set(ids)) != len(ids) or set(ids) != expected_window_ids:
        raise WindowCoverageError("WINDOW_OWNERSHIP_DRIFT")
    if set(ids) & previously_reviewed:
        raise WindowCoverageError("PREVIOUSLY_REVIEWED_WINDOW_RECOUNT")
    owned = set()
    for w in windows:
        if w.source_sha256 != expected_source_sha256:
            raise WindowCoverageError("SOURCE_HASH_DRIFT")
        if not (w.window_id.startswith("W") and len(w.window_id)==6
                and w.window_id[1:].isdigit()):
            raise WindowCoverageError("INVALID_WINDOW_ID")
        if not (0 < w.first_cue <= w.last_cue and w.claim_count >= 0):
            raise WindowCoverageError("INVALID_CUE_OR_CLAIM_COUNT")
        if w.reviewer_status not in ("MODEL_SEMANTIC_PROVISIONAL",
                                      "REVIEWED_NO_FINANCIAL_CLAIMS"):
            raise WindowCoverageError("UNREVIEWED_WINDOW_CANNOT_COUNT")
        if w.claim_count == 0 and w.reviewer_status != "REVIEWED_NO_FINANCIAL_CLAIMS":
            raise WindowCoverageError("UNEXPLAINED_EMPTY_WINDOW")
        if w.claim_count > 0 and w.reviewer_status != "MODEL_SEMANTIC_PROVISIONAL":
            raise WindowCoverageError("CLAIMS_MISCLASSIFIED_AS_EMPTY")
        cues = set(range(w.first_cue, w.last_cue+1))
        if cues & owned:
            raise WindowCoverageError("CUE_OWNERSHIP_OVERLAP")
        owned.update(cues)
    if next_window_id in set(ids):
        raise WindowCoverageError("RESUME_POINTER_POINTS_TO_COMPLETED_WINDOW")
    return {"new_windows":len(windows),"new_cues":len(owned),
            "provisional_claims":sum(w.claim_count for w in windows),
            "next_window":next_window_id,
            "fact_approval":False,"independent_recall_certified":False}
