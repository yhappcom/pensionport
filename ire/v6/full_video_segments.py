"""Private full-video bounded workplan with *no* self-pinned child approval.

The current ChatGPT host has a per-turn cue budget. This deterministic planner
covers the *entire* verified owner-pinned original by grouping existing frozen
primary windows without gaps, overlaps or altered window ownership. Child
plans are proposals only: a distinct externally pinned owner inventory and
ledger scope are required before any child is submitted to the V6 host.
No model call, no private cue text, no research-complete inference.
"""
from __future__ import annotations

from copy import deepcopy

from .codec import json_digest, require_hash
from .errors import InvalidInput, QualityNotProven
from .source import verify_source
from .trust import verify_owner_inventory

MAX_CUES_PER_HOST=120
MAX_SEGMENTS=512


def propose_full_video_segments(raw, manifest, inventory_bytes, *,
                                expected_inventory_sha256,
                                max_cues=MAX_CUES_PER_HOST):
    """Produce source-verified child-scope *proposals*, not trusted child pins.

    No source-derived manifest digest is an independently authorized pin.
    Before executing a segment, an external owner must separately attest its
    child manifest and inventory in a new scope/ledger. The planner cannot
    submit host tasks and cannot combine independently unreviewed results.
    """
    require_hash(expected_inventory_sha256, "FULL_VIDEO_OWNER_INVENTORY_PIN")
    if type(max_cues) is not int or not 1 <= max_cues <= MAX_CUES_PER_HOST:
        raise InvalidInput("PRIVATE_SEGMENT_CUE_BUDGET_INVALID")
    pinned=verify_owner_inventory(
        raw,manifest,inventory_bytes,
        expected_inventory_sha256=expected_inventory_sha256)
    src=pinned.source
    if (src.scope_first_cue != 1 or
        src.scope_last_cue != len(src.cues) or
        manifest["scope"]["mode"]!="FULL_VIDEO"):
        raise QualityNotProven("PRIVATE_SEGMENT_FULL_VIDEO_PARENT_REQUIRED")
    expected_source_sha=src.source_sha256
    expected_manifest_sha=src.manifest_sha256
    base={
        "schema":"IRE_V6_PRIVATE_FULL_VIDEO_WORKPLAN_V1",
        "video_id":src.video_id,
        "parent_source_sha256":expected_source_sha,
        "parent_manifest_sha256":expected_manifest_sha,
        "owner_inventory_sha256":pinned.inventory_sha256,
        "original_full_video_cues":len(src.cues),
        "max_cues_per_host_turn":max_cues,
        "owner_attestation_must_be_independent_for_each_child":True,
        "child_manifest_digests_are_not_owner_attestations":True,
        "model_api_called":False,
        "human_semantic_review_pending":True,
        "whole_video_research_complete":False,
        "independent_gold_recall_measured":False,
        "p0_go":False,
    }
    if len(src.cues)<=max_cues:
        return dict(base,status="FULL_SOURCE_FITS_EXISTING_HOST_TURN",
                    segment_count=0,segments=[],
                    segmentation_needed=False,
                    full_cue_partition_structurally_verified=True)
    windows=deepcopy(manifest["windows"])
    groups=[]
    current=[]
    count=0
    for window in windows:
        size=window["last_cue"]-window["first_cue"]+1
        if size>max_cues:
            raise QualityNotProven(
                "PRIVATE_SEGMENT_ORIGINAL_OWNER_WINDOW_EXCEEDS_HOST_BUDGET")
        if current and count+size>max_cues:
            groups.append(current)
            current=[]
            count=0
        current.append(window)
        count+=size
    if current:
        groups.append(current)
    if not groups or len(groups)>MAX_SEGMENTS:
        raise QualityNotProven("PRIVATE_SEGMENT_BOUND_TOO_MANY_SEGMENTS")
    segments=[]
    next_cue=1
    for index,group in enumerate(groups,1):
        first,last=group[0]["first_cue"],group[-1]["last_cue"]
        if first!=next_cue or last-first+1>max_cues:
            raise InvalidInput("PRIVATE_SEGMENT_GAP_OR_EXCESS")
        next_cue=last+1
        child={
            "schema":"IRE_V6_SOURCE_PLAN_V1",
            "video_id":src.video_id,
            "source_sha256":expected_source_sha,
            "cue_count":len(src.cues),
            "scope":{"mode":"PARTIAL","first_cue":first,"last_cue":last},
            "windows":group,
        }
        child_sha=json_digest(child)
        # This self-hash validates only deterministic structural derivation,
        # not independent owner trust; all execution gates remain separate.
        check=verify_source(raw,child,
                            expected_source_sha256=expected_source_sha,
                            expected_manifest_sha256=child_sha)
        if (check.scope_first_cue!=first or
            check.scope_last_cue!=last or
            tuple(w for w,_,_ in check.primary_windows)!=
                tuple(w["window_id"] for w in group)):
            raise InvalidInput("PRIVATE_SEGMENT_CHILD_SOURCE_REPLAY_DRIFT")
        segments.append({
            "segment_id":f"B{index:04d}",
            "first_cue":first,
            "last_cue":last,
            "scoped_cue_count":last-first+1,
            "source_window_ids":[w["window_id"] for w in group],
            "child_manifest_sha256":child_sha,
            "child_manifest":child,
            "child_owner_inventory_pinned":False,
            "child_host_batch_committed":False,
            "independent_semantic_review_completed":False,
        })
    if next_cue!=len(src.cues)+1:
        raise InvalidInput("PRIVATE_SEGMENT_PARENT_CUE_TAIL_MISSING")
    return dict(base,status="PRIVATE_CHILD_OWNER_PINS_REQUIRED_BEFORE_EXECUTION",
                segment_count=len(segments),segments=segments,
                segmentation_needed=True,
                full_cue_partition_structurally_verified=True,
                child_plan_census_sha256=json_digest([
                    {"segment_id":s["segment_id"],
                     "first_cue":s["first_cue"],
                     "last_cue":s["last_cue"],
                     "child_manifest_sha256":s["child_manifest_sha256"]}
                    for s in segments]))
