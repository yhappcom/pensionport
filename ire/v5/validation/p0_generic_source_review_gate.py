"""Fail-closed generic provenance gate for P0 source-window research summaries.

Pure validation; does not perform model inference, claim truth approval, or
assert independent recall. Never accepts original SRT text as repository data.
"""
from __future__ import annotations
import hashlib
import re

_SHA = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN = {"raw_srt", "source_text", "transcript", "full_transcript", "raw_cue_text"}
_ALLOWED = {"SOURCE_READ_CANDIDATES_PROVISIONAL", "SOURCE_READ_NO_FINANCIAL_ATOMIC_CLAIM"}

class ResearchCoverageError(ValueError):
    pass

def _check(ok, reason):
    if not ok:
        raise ResearchCoverageError(reason)

def _no_raw(obj):
    if isinstance(obj, dict):
        _check(not (_FORBIDDEN & set(obj)), "PRIVATE_SOURCE_TEXT_KEY")
        for value in obj.values():
            _no_raw(value)
    elif isinstance(obj, list):
        for value in obj:
            _no_raw(value)

def validate_source_review(record: dict) -> dict:
    """Validate window ownership, per-cue hashes and candidate anchor identity.

    This is a *structural* gate, not a financial or semantic truth test.
    """
    _check(type(record) is dict, "RECORD_NOT_OBJECT")
    _no_raw(record)
    for field in ("archive_sha256", "source_sha256"):
        _check(bool(_SHA.fullmatch(record.get(field, ""))), "INVALID_SOURCE_HASH")
    windows=record.get("windows")
    candidates=record.get("candidates")
    _check(type(windows) is list and len(windows)>0, "WINDOWS_MISSING")
    _check(type(candidates) is list, "CLAIMS_MISSING")
    _check(record.get("research_complete") is False
           and record.get("p0_go") is False
           and record.get("p1_merge") is False, "FALSE_GO")
    _check(record.get("reviewed_windows")==len(windows), "WINDOW_COUNT")
    _check(record.get("reviewed_cues")==sum(w["cue_count"] for w in windows), "CUE_COUNT")
    first_id=windows[0].get("window_id")
    _check(type(first_id) is str and bool(re.fullmatch(r"W[0-9]{5}", first_id)),
           "FIRST_WINDOW_ID")
    first_window_number=int(first_id[1:])
    _check(first_window_number>=1 and first_window_number+len(windows)<=100000,
           "WINDOW_RANGE")
    _check(record.get("first_cue")==windows[0].get("first_cue"),
           "FIRST_CUE_MISMATCH")
    prev=record["first_cue"]-1
    owners={}
    for offset,w in enumerate(windows):
        _check(w["window_id"]==f"W{first_window_number+offset:05d}", "WINDOW_ORDER")
        _check(w["disposition"] in _ALLOWED, "DISPOSITION_INVALID")
        _check(w["first_cue"]==prev+1 and w["last_cue"]>=w["first_cue"], "CUE_GAP_OR_COLLISION")
        _check(w["cue_count"]==w["last_cue"]-w["first_cue"]+1, "CUE_OWNERSHIP")
        _check(bool(_SHA.fullmatch(w["primary_text_sha256"])), "WINDOW_HASH")
        hashes=w["cue_sha256"]
        _check(len(hashes)==w["cue_count"], "CUE_HASH_COUNT")
        for idx, item in enumerate(hashes, w["first_cue"]):
            _check(item["cue"]==idx and bool(_SHA.fullmatch(item["sha256"])), "CUE_HASH_MISMATCH")
            owners[(w["window_id"],idx)]=item["sha256"]
        prev=w["last_cue"]
    _check(record["last_cue"]==prev and
           record["next_window"]==f"W{first_window_number+len(windows):05d}",
           "RESUME_POINTER")
    if "total_cues" in record:
        _check(type(record["total_cues"]) is int and prev<=record["total_cues"], "CUE_TOTAL_RANGE")
    if "total_windows" in record:
        _check(type(record["total_windows"]) is int and
               first_window_number+len(windows)-1<=record["total_windows"],
               "WINDOW_TOTAL_RANGE")
    seen=set()
    count={w["window_id"]:0 for w in windows}
    for c in candidates:
        cid=c["candidate_id"]
        _check(cid not in seen, "DUPLICATE_CLAIM_ID")
        seen.add(cid)
        _check(owners.get((c["window_id"],c["cue"]))==c["cue_sha256"], "UNOWNED_CLAIM")
        _check(c["truth_approved"] is False and c["prior_relation"].startswith("OPEN"), "UNSUPPORTED_APPROVAL")
        count[c["window_id"]]+=1
    for w in windows:
        _check((count[w["window_id"]]==0)==(w["disposition"]=="SOURCE_READ_NO_FINANCIAL_ATOMIC_CLAIM"),
               "EMPTY_WINDOW_MISMATCH")
    return {"window_count":len(windows),"cue_count":record["reviewed_cues"],
            "provisional_claims":len(candidates),"next_window":record["next_window"],
            "truth_approved":False,"independent_recall_certified":False}
