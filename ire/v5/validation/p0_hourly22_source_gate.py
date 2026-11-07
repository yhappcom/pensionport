"""Strict audit of source-hash-derived #22 W01-W12 real conversational research.

No raw private SRT is in this repo, and this 12-window model output cannot
attest independent financial recall or research closure.
"""
from __future__ import annotations
import base64
import hashlib
import json
import zlib
from pathlib import Path

ARCHIVE_SHA256 = "00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd"
SRT_SHA256 = "cd99dbf5576b74f2b256f2e08d6b869fdfbed7b08e8fcb5bb1f1296e50deea06"
DATA_SHA256 = "2729703bdb90bdb261d93db5e59bba8db44fe76d6014e2f8dbe88e80bbc3aa3a"
DATA_PATH = Path(__file__).resolve().parent / "private_source_derived_20261107" / "hourly22_w01_w12.json.zlib.b64"
FORBIDDEN = {"raw_srt", "original_srt", "source_quote", "source_text", "full_transcript"}


def _scan_no_raw_source(obj):
    if isinstance(obj, dict):
        if set(obj) & FORBIDDEN:
            raise ValueError("P0_HOURLY_PRIVATE_SRT_IN_GITHUB")
        for v in obj.values():
            _scan_no_raw_source(v)
    elif isinstance(obj, list):
        for v in obj:
            _scan_no_raw_source(v)


def load_hourly22() -> dict:
    encoded = DATA_PATH.read_text("ascii").strip()
    compressed = base64.b64decode(encoded, validate=True)
    decomp = zlib.decompressobj()
    raw = decomp.decompress(compressed, 1_000_000)
    if not decomp.eof or decomp.unused_data or decomp.unconsumed_tail:
        raise ValueError("P0_HOURLY_BAD_COMPRESSED_BODY")
    if hashlib.sha256(raw).hexdigest() != DATA_SHA256:
        raise ValueError("P0_HOURLY_DATA_HASH_CHANGED")
    obj = json.loads(raw)
    _scan_no_raw_source(obj)
    return obj


def audited_status() -> dict:
    d = load_hourly22()
    if not (d["schema"] == "IRE_V5_P0_SINGLE_HOURLY_HOST_SEMANTIC_PILOT_V1"
            and d["source_archive_sha256"] == ARCHIVE_SHA256
            and d["source_srt_sha256"] == SRT_SHA256
            and d["video_id"] == "WGFPHeM6-6I"
            and d["source_cues_total"] == 1065
            and d["source_windows_total"] == 60):
        raise ValueError("P0_HOURLY_SOURCE_IDENTITY_CHANGED")
    windows = d["source_windows"]
    claims = d["claims"]
    reviews = d["evidence_reviews"]
    if not (len(windows)==12 and len(claims)==44
            and d["cues_reviewed_in_this_turn"] == 216
            and d["candidate_first_pass_count"] == 40
            and d["compound_first_pass_replaced"] == 1
            and d["second_pass_date_subclaims_added"] == 4
            and d["second_pass_other_new_subclaims_added"] == 1
            and d["provisional_final_atomic_candidates"] == 44
            and d["official_source_reviewed_candidate_count"] == 23
            and len(reviews) == 23):
        raise ValueError("P0_HOURLY_CENSUS_DRIFT")
    valid_ids = {f"W{i:05d}" for i in range(1,13)}
    by_id = {w["window_id"]:w for w in windows}
    if set(by_id)!=valid_ids:
        raise ValueError("P0_HOURLY_MISSING_OR_DUPLICATED_WINDOW")
    cues = []
    for i in range(1,13):
        w = by_id[f"W{i:05d}"]
        inv = w["cue_inventory"]
        if len(inv)!=w["primary_cue_count"]:
            raise ValueError("P0_HOURLY_CUE_COUNT_MISMATCH")
        ids=[x["cue_index"] for x in inv]
        if ids!=list(range(w["source_first_cue"],w["source_last_cue"]+1)):
            raise ValueError("P0_HOURLY_SOURCE_CUE_GAP")
        if any(len(x["text_sha256"]) != 64 for x in inv):
            raise ValueError("P0_HOURLY_ORIGINAL_CUE_HASH_MISSING")
        if w["independent_blind_gold_recall_certified"]:
            raise ValueError("P0_HOURLY_INDEPENDENCE_OVERCLAIM")
        cues+=ids
    if cues!=list(range(1,217)):
        raise ValueError("P0_HOURLY_CUE_OWNERSHIP_COLLISION")
    ids=[c["candidate_id"] for c in claims]
    if len(set(ids))!=44:
        raise ValueError("P0_HOURLY_CLAIM_ID_COLLISION")
    source_cue_map={w["window_id"]:{x["cue_index"]:x["text_sha256"]
                           for x in w["cue_inventory"]} for w in windows}
    for c in claims:
        if (c["candidate_maturity"] != "SOURCE_GROUNDED_PROVISIONAL"
            or c["prior_knowledge_relation"] != "OPEN_REQUIRES_EXISTING_116_REVIEW"
            or c["financial_truth_approved"]
            or c["source_sha256"]!=SRT_SHA256
            or c["window_id"] not in valid_ids
            or source_cue_map[c["window_id"]].get(c["anchor"])!=c["cue_text_sha256"]):
            raise ValueError("P0_HOURLY_UNSUPPORTED_SOURCE_CLAIM")
    if sorted(d["prior_scoped_windows"])!=["W00041","W00046","W00055","W00056"] \
            or d["prior_scoped_window_overlap_count"]!=0:
        raise ValueError("P0_HOURLY_PRIOR_WINDOW_DUPLICATION")
    if len({r["candidate_id"] for r in reviews})!=23 \
            or not {r["candidate_id"] for r in reviews}<=set(ids):
        raise ValueError("P0_HOURLY_EVIDENCE_NO_CLAIM")
    docs={x["source_id"]:x["url"] for x in d["official_sources"]}
    if len(docs)!=9 or any(not u.startswith("https://") for u in docs.values()):
        raise ValueError("P0_HOURLY_OFFICIAL_URL_INVALID")
    for r in reviews:
        if (not r["official_source_checked"] or r["person_specific_approval"]
            or not r["source_ids"] or not set(r["source_ids"])<=set(docs)):
            raise ValueError("P0_HOURLY_EVIDENCE_UNTRUSTED")
    if (d["full_ledger_event_chain_submitted"]
        or d["p0_research_completeness_certified"]
        or d["independent_gold_atomic_recall_certified"]
        or d["financial_truth_automatically_approved"]
        or d["personal_advice_approved"]):
        raise ValueError("P0_HOURLY_FALSE_RESEARCH_GO")
    if d["next_source_window_id"]!="W00013" or d["unreviewed_remaining_windows_in_this_video"]!=48:
        raise ValueError("P0_HOURLY_RESUME_POINTER_CHANGED")
    return {"schema":"IRE_V5_P0_HOURLY22_AUDIT_V1",
            "video":"#22","windows_read":12,"original_cues_read":216,
            "first_pass_propositions":40,"second_pass_provisional_final":44,
            "official_source_claim_reviews":23,"next_window":"W00013",
            "no_prior_window_overlap":True,"p0_final_release":"NO_GO",
            "independent_gold_recall":False,"p1_auto_merge":False}

if __name__=="__main__":
    print(json.dumps(audited_status(),ensure_ascii=False,sort_keys=True))
