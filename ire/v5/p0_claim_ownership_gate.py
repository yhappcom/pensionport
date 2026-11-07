"""Fail-closed, video-agnostic source-cue/window ownership gate for P0 claim artifacts.

Checks structural ownership of source-derived metadata, including provisional
cross-window context. It cannot independently certify semantic coverage, verify
private SRT bytes absent from CI, infer speakers, or approve financial advice.
Only materialized *corrected* candidate records pass; legacy erroneous window
labels remain stored as append-only history and cannot be effective owners.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import re

SCHEMA = "IRE_V5_P0_CLAIM_OWNERSHIP_RECONCILIATION_V1"
REGISTRY_SCHEMA = "IRE_V5_P0_CLAIM_OWNERSHIP_REGISTRY_V1"
REGISTRY = Path("ire/v5/validation/p0_claim_ownership_registry.json")
SHA = re.compile(r"[0-9a-f]{64}\Z")
WINDOW = re.compile(r"W[0-9]{5}\Z")
TIME = re.compile(r"(?:[0-9]{2}:){2}[0-9]{2},[0-9]{3}\Z")


class ClaimOwnershipError(ValueError):
    pass


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ClaimOwnershipError(reason)


def _wid(n: int) -> str:
    return f"W{n:05d}"


def _record_window_plan(data: dict) -> tuple[dict[int, str], dict[str, dict]]:
    windows = data.get("windows")
    require(type(windows) is list and bool(windows), "WINDOW_PLAN_MISSING")
    require(len(windows) <= 100000, "WINDOW_PLAN_TOO_LARGE")
    cue_owner = {}
    by_id = {}
    first_window = windows[0].get("window_id")
    require(type(first_window) is str and WINDOW.fullmatch(first_window) is not None,
            "FIRST_WINDOW_ID_INVALID")
    first_num = int(first_window[1:])
    prev_last = None
    for position, window in enumerate(windows):
        wid = window.get("window_id")
        first = window.get("first_cue")
        last = window.get("last_cue")
        require(wid == _wid(first_num + position), "WINDOW_ID_SEQUENCE_GAP")
        require(type(first) is int and type(last) is int and
                0 < first <= last <= data["source_cues_total"], "WINDOW_CUE_RANGE_INVALID")
        if prev_last is not None:
            require(first == prev_last + 1, "WINDOW_CUE_GAP_OR_OVERLAP")
        require(type(window.get("window_text_sha256")) is str and
                SHA.fullmatch(window["window_text_sha256"]) is not None,
                "WINDOW_SOURCE_HASH_INVALID")
        for cue in range(first, last + 1):
            require(cue not in cue_owner, "DOUBLE_OWNED_SOURCE_CUE")
            cue_owner[cue] = wid
        by_id[wid] = window
        prev_last = last
    require(first_window == data.get("source_window_first") and
            windows[-1]["window_id"] == data.get("source_window_last"),
            "DECLARED_WINDOW_RANGE_DRIFT")
    return cue_owner, by_id


def validate_claim_ownership(data: dict) -> dict:
    require(type(data) is dict and data.get("schema") == SCHEMA, "CLAIM_SCHEMA_INVALID")
    for field in ("archive_sha256", "source_sha256"):
        require(type(data.get(field)) is str and SHA.fullmatch(data[field]) is not None,
                "SOURCE_SHA256_INVALID")
    require(type(data.get("video_id")) is str and
            re.fullmatch(r"[A-Za-z0-9_-]{11}", data["video_id"]) is not None,
            "VIDEO_ID_INVALID")
    require(type(data.get("source_cues_total")) is int and
            data["source_cues_total"] > 0, "SOURCE_CUE_COUNT_INVALID")
    require(data.get("p0_complete") is False and
            data.get("independent_gold_available") is False and
            data.get("formal_second_pass_registry_generated") is False and
            data.get("finance_facts_approved") == 0, "FALSE_P0_OR_FINANCIAL_APPROVAL")
    cue_owner, windows = _record_window_plan(data)
    claims = data.get("claims")
    require(type(claims) is list and bool(claims), "CANDIDATES_MISSING")
    require(len(claims) <= 100000, "CLAIMS_TOO_MANY")
    require(len(claims) == data.get("legacy_claim_count"), "CLAIM_CENSUS_DRIFT")
    seen = set()
    corrections = []
    cross_boundaries = 0
    for c in claims:
        cid = c.get("candidate_id")
        require(type(cid) is str and cid and cid not in seen, "DUPLICATE_CANDIDATE_ID")
        seen.add(cid)
        cue = c.get("anchor_cue")
        require(type(cue) is int and cue in cue_owner, "ANCHOR_CUE_NOT_IN_PLAN")
        wid = c.get("window_id")
        require(wid == cue_owner[cue], "CLAIM_CUE_OUTSIDE_OWNED_WINDOW")
        require(type(c.get("anchor_cue_sha256")) is str and
                SHA.fullmatch(c["anchor_cue_sha256"]) is not None,
                "CLAIM_CUE_HASH_INVALID")
        require(type(c.get("anchor_start_time")) is str and
                TIME.fullmatch(c["anchor_start_time"]) is not None,
                "CLAIM_TIMESTAMP_INVALID")
        require(type(c.get("summary")) is str and len(c["summary"].strip()) >= 10,
                "CLAIM_SEMANTIC_SUMMARY_MISSING")
        require(c.get("fact_approved") is False and
                c.get("evidence_status") == "OPEN" and
                c.get("prior_relation_status") == "OPEN",
                "CLAIM_UNSUPPORTED_FINAL_APPROVAL")
        previous = c.get("original_window_id")
        require(type(previous) is str and WINDOW.fullmatch(previous) is not None,
                "ORIGINAL_CLAIM_OWNER_MISSING")
        corrected = previous != wid
        require(c.get("correction_status") ==
                ("LEGACY_WINDOW_OWNER_CORRECTED" if corrected else "UNCHANGED"),
                "ORIGINAL_OWNER_CORRECTION_UNACKNOWLEDGED")
        if corrected:
            corrections.append((cid, previous, wid, cue))
        start = c.get("context_first_cue")
        end = c.get("context_last_cue")
        require(type(start) is int and type(end) is int and
                start <= cue <= end, "CLAIM_CONTEXT_SPAN_EXCLUDES_ANCHOR")
        require(all(i in cue_owner for i in range(start, end + 1)),
                "CLAIM_CONTEXT_CUE_MISSING")
        positions = [int(cue_owner[i][1:]) for i in (start, end)]
        require(max(abs(v - int(wid[1:])) for v in positions) <= 1,
                "CLAIM_CONTEXT_NOT_ADJACENT")
        crosses = positions[0] != positions[1]
        require(type(c.get("cross_window_context_open")) is bool and
                c["cross_window_context_open"] == crosses,
                "CROSS_WINDOW_CONTEXT_NOT_FLAGGED")
        if crosses:
            cross_boundaries += 1
    require(data.get("legacy_owner_errors_expected") == len(corrections),
            "OWNER_CORRECTION_COUNT_DRIFT")
    require(data.get("first_unread_window") ==
            _wid(int(data["source_window_last"][1:]) + 1),
            "NEXT_UNREAD_WINDOW_DRIFT")
    require(data.get("formal_queue_pointer") == data["source_window_first"],
            "FORMAL_POINTER_CANNOT_ADVANCE_WITHOUT_EVENT")
    return {
        "video_id": data["video_id"], "windows_structurally_checked": len(windows),
        "cues_in_window_plan": len(cue_owner),
        "provisional_claims_structurally_checked": len(claims),
        "corrected_legacy_owner_rows": len(corrections),
        "cross_window_context_open": cross_boundaries,
        "first_unread_window": data["first_unread_window"],
        "formal_queue_pointer": data["formal_queue_pointer"],
        "private_srt_replayed_in_this_ci": False,
        "semantic_gold_recall_certified": False,
        "p0_go": False,
    }


def verify(root: Path, registry_path: Path | None = None) -> dict:
    root = Path(root).resolve()
    registry_path = root / REGISTRY if registry_path is None else Path(registry_path)
    registry = json.loads(registry_path.read_text("utf-8"))
    require(type(registry) is dict and registry.get("schema") == REGISTRY_SCHEMA,
            "OWNERSHIP_REGISTRY_SCHEMA_INVALID")
    require(registry.get("p0_go") is False, "REGISTRY_FALSE_P0_GO")
    entries = registry.get("entries")
    require(type(entries) is list and bool(entries), "OWNERSHIP_REGISTRY_EMPTY")
    seen_paths = set()
    all_result = []
    seen_claims_by_video = {}
    used_cues_by_video = {}
    for entry in entries:
        require(type(entry) is dict and type(entry.get("path")) is str,
                "OWNERSHIP_ENTRY_INVALID")
        rel = Path(entry["path"])
        require(not rel.is_absolute() and ".." not in rel.parts and
                str(rel).startswith("ire/v5/validation/") and
                rel.suffix == ".json" and str(rel) not in seen_paths,
                "OWNERSHIP_REGISTRY_UNSAFE_OR_DUPLICATE_PATH")
        seen_paths.add(str(rel))
        path = (root / rel).resolve()
        require(path.is_relative_to(root / "ire/v5/validation") and path.is_file(),
                "OWNERSHIP_RECORD_MISSING_OR_ESCAPED")
        raw = path.read_bytes()
        require(type(entry.get("record_sha256")) is str and
                hashlib.sha256(raw).hexdigest() == entry["record_sha256"],
                "OWNERSHIP_RECORD_HASH_DRIFT")
        data = json.loads(raw)
        result = validate_claim_ownership(data)
        vid = data["video_id"]
        ids = seen_claims_by_video.setdefault(vid, set())
        new_ids = {c["candidate_id"] for c in data["claims"]}
        require(not (ids & new_ids), "RESEARCH_CLAIM_ID_DUPLICATED_ACROSS_BATCHES")
        ids.update(new_ids)
        cue_ranges = used_cues_by_video.setdefault(vid, set())
        new_cues = {i for w in data["windows"] for i in
                    range(w["first_cue"], w["last_cue"] + 1)}
        require(not (cue_ranges & new_cues), "RESEARCH_CUE_OVERLAP_ACROSS_BATCHES")
        cue_ranges.update(new_cues)
        all_result.append(result)
    return {
        "schema": "IRE_V5_P0_CLAIM_OWNERSHIP_GATE_RESULT_V1",
        "batches": len(all_result),
        "verified_provisional_claim_anchors": sum(
            x["provisional_claims_structurally_checked"] for x in all_result),
        "corrected_legacy_claim_owners": sum(
            x["corrected_legacy_owner_rows"] for x in all_result),
        "cross_window_context_open": sum(x["cross_window_context_open"] for x in all_result),
        "source_structure_checked": True,
        "private_srt_replayed_in_this_ci": False,
        "semantic_gold_recall_certified": False,
        "p0_go": False,
        "per_batch": all_result
    }
