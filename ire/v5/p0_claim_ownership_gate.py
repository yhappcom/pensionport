"""Generic, fail-closed audit of provisional claim-to-window ownership.

A source-derived *index* only. No semantic completeness or source-byte attestation.
The index must be reviewed separately from the original private transcript.
"""
from __future__ import annotations
import json
from pathlib import Path

class ClaimOwnershipError(ValueError):
    pass

def validate_claim_ownership(index: dict) -> dict:
    if type(index) is not dict or index.get("schema") != "IRE_V5_P0_CLAIM_OWNERSHIP_V1":
        raise ClaimOwnershipError("OWNERSHIP_SCHEMA")
    windows = index.get("windows")
    claims = index.get("claims")
    if not isinstance(windows, list) or not windows or not isinstance(claims, list):
        raise ClaimOwnershipError("OWNERSHIP_CENSUS")
    source = index.get("source_sha256")
    video = index.get("video_id")
    if not isinstance(source, str) or len(source) != 64 or not isinstance(video, str) or not video:
        raise ClaimOwnershipError("OWNERSHIP_SOURCE_IDENTITY")
    owners = {}
    prev_end = None
    prev_window = None
    for w in windows:
        wid, start, end = w.get("window_id"), w.get("first_cue"), w.get("last_cue")
        if not isinstance(wid, str) or len(wid) != 6 or not wid.startswith("W") or not wid[1:].isdigit():
            raise ClaimOwnershipError("OWNERSHIP_WINDOW_ID")
        if type(start) is not int or type(end) is not int or start > end:
            raise ClaimOwnershipError("OWNERSHIP_WINDOW_BOUNDS")
        if prev_end is not None and (start != prev_end + 1 or int(wid[1:]) != prev_window + 1):
            raise ClaimOwnershipError("OWNERSHIP_WINDOW_GAP_OR_OVERLAP")
        for cue in range(start, end + 1):
            owners[cue] = wid
        prev_end, prev_window = end, int(wid[1:])
    seen = set()
    multi_anchor = {}
    for c in claims:
        cid, cue, wid = c.get("claim_id"), c.get("anchor_cue"), c.get("window_id")
        if not isinstance(cid, str) or not cid or cid in seen:
            raise ClaimOwnershipError("OWNERSHIP_CLAIM_ID")
        seen.add(cid)
        if type(cue) is not int or cue not in owners or wid != owners[cue]:
            raise ClaimOwnershipError("CLAIM_WINDOW_MISMATCH:" + cid)
        if c.get("video_id") != video or c.get("source_sha256") != source:
            raise ClaimOwnershipError("CLAIM_SOURCE_MISMATCH:" + cid)
        multi_anchor.setdefault(cue, []).append(cid)
        refs = c.get("support_cues")
        if not isinstance(refs, list) or not refs or cue not in refs or any(type(x) is not int for x in refs):
            raise ClaimOwnershipError("CLAIM_SUPPORT_MISSING:" + cid)
        # Boundary-spanning claims must explicitly identify support outside this batch.
        if any(x not in owners for x in refs):
            raise ClaimOwnershipError("CLAIM_SUPPORT_OUTSIDE_BATCH:" + cid)
        if any(owners[x] != wid for x in refs) and c.get("cross_window_review") is not True:
            raise ClaimOwnershipError("CROSS_WINDOW_REVIEW_REQUIRED:" + cid)
    if index.get("next_cue") != prev_end + 1 or index.get("next_window") != f"W{prev_window+1:05d}":
        raise ClaimOwnershipError("OWNERSHIP_RESUME_POINTER")
    return {"schema": "IRE_V5_P0_CLAIM_OWNERSHIP_RESULT_V1",
            "checked_claims": len(claims), "checked_cues": len(owners),
            "multi_claim_anchor_cues": sum(len(v) > 1 for v in multi_anchor.values()),
            "source_bytes_replayed": False, "semantic_recall_certified": False, "p0_go": False}

def verify(root: Path) -> dict:
    path = Path(root) / "ire/v5/validation/p0_claim_ownership_index.json"
    return validate_claim_ownership(json.loads(path.read_text("utf-8")))
