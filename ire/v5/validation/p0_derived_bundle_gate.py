"""Verify redacted, content-addressed P0 real-SRT derived research bundles.

The archived payloads contain only paraphrased candidate propositions, cue
indices/hashes and risk flags. They do NOT include original SRT text, nor
assert an independently proven atomic recall rate or financial fact approval.

No external API/network access and no changes to active knowledge are needed.
"""
from __future__ import annotations

import base64
import hashlib
import json
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "private_source_derived_20261107"
ARCHIVE_SHA = "00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd"
RAW_SHA = {
    "short5": "9f305af6c5acdf11fb3af312e0483229f68b13a04a0e4e7f5d19caefdb9422fd",
    "long5": "853e3e37692ded8e0cdcc20e0c365e473eacbe8d98af5b659487811b31382221",
    "evidence19": "8877a86bf69a84b0043abf36b8b6dca69e4cd143eea82c503cbf0e48c44cfc99",
    "long5risk": "8ebe14dfb16edda1cf1fe8e840f70ab38d1b6a5136d1778b6b4b8dd9720ff34d",
}
FORBIDDEN_KEYS = {"original_srt", "source_quote", "source_text", "cue_text",
                  "transcript_full", "private_transcript"}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_bundle(name: str) -> dict:
    if name not in RAW_SHA:
        raise ValueError("P0_DERIVED_UNKNOWN_BUNDLE")
    encoded = (ROOT / (name + ".json.zlib.b64")).read_text("ascii").strip()
    compressed = base64.b64decode(encoded, validate=True)
    obj = zlib.decompressobj()
    # Fail closed if compressed file is replaced with an unexpectedly large
    # payload or trailing unchecked data.
    raw = obj.decompress(compressed, 2_000_000)
    if obj.unconsumed_tail or obj.unused_data or not obj.eof:
        raise ValueError("P0_DERIVED_COMPRESSED_PAYLOAD_INVALID")
    if _sha(raw) != RAW_SHA[name]:
        raise ValueError("P0_DERIVED_PAYLOAD_SHA_DRIFT")
    out = json.loads(raw)
    check_no_original_source_leak(out)
    return out


def check_no_original_source_leak(node) -> None:
    if isinstance(node, dict):
        if set(node) & FORBIDDEN_KEYS:
            raise ValueError("P0_DERIVED_ORIGINAL_SOURCE_LEAK")
        for value in node.values():
            check_no_original_source_leak(value)
    elif isinstance(node, list):
        for value in node:
            check_no_original_source_leak(value)


def research_state() -> dict:
    short, long, evidence, risks = (
        read_bundle("short5"), read_bundle("long5"),
        read_bundle("evidence19"), read_bundle("long5risk"))
    if (short["source_zip_sha256"] != ARCHIVE_SHA or
        long["source_archive_sha256"] != ARCHIVE_SHA or
        risks["source_archive_hash"] != ARCHIVE_SHA):
        raise ValueError("P0_DERIVED_SRT_SOURCE_SHA_MISMATCH")
    if not (short["candidate_count"] == 49 and
            short["source_cues_read"] == 179 and
            long["reviewed_claim_candidates"] == 29 and
            long["reviewed_source_windows"] == 18 and
            risks["source_cues_checked"] == 6295 and
            risks["windows_checked"] == 354 and
            risks["windows_with_model_semantics"] == 0 and
            evidence["evidence_review_count"] == 19):
        raise ValueError("P0_DERIVED_FROZEN_CENSUS_DRIFT")
    short_vid = {x["video_id"] for x in short["videos"]}
    long_vid = {x["video_id"] for x in long["videos"]}
    if len(short_vid) != 5 or len(long_vid) != 5 or short_vid & long_vid:
        raise ValueError("P0_DERIVED_VIDEO_COHORT_INVALID")
    if {x["video_id"] for x in risks["videos"]} != long_vid:
        raise ValueError("P0_DERIVED_LONG_RISK_VIDEO_MISMATCH")
    claims = {c["candidate_id"] for v in short["videos"] for c in v["candidates"]}
    claims |= {c["atom_id"] for v in long["videos"] for c in v["claims"]}
    if len(claims) != 78:
        raise ValueError("P0_DERIVED_CLAIM_ID_CONFLICT")
    if any(item["claim_id"] not in claims for item in evidence["evidence_reviews"]):
        raise ValueError("P0_DERIVED_EVIDENCE_WITHOUT_SOURCE_CLAIM")
    if (short["full_atomic_recall_certified"] or short["complete_v5_event_chain"] or
        long["complete_atomic_recall_certified"] or
        evidence["financial_truth_formally_approved"] or
        risks["independent_semantic_recall_measured"]):
        raise ValueError("P0_DERIVED_UNSUPPORTED_FINANCIAL_APPROVAL")
    if any(c["financial_truth_approved"] for v in short["videos"]
           for c in v["candidates"]):
        raise ValueError("P0_DERIVED_UNAPPROVED_CLAIM_PROMOTED")
    if any(c["approved_financial_fact"] for v in long["videos"]
           for c in v["claims"]):
        raise ValueError("P0_DERIVED_UNAPPROVED_LONG_CLAIM_PROMOTED")
    return {
        "schema": "IRE_V5_P0_REAL10_DERIVED_RESEARCH_RECEIPT_V1",
        "real_source_video_count": 10,
        "real_source_cue_count": 6474,
        "source_windows_total": 366,
        "model_atomic_claim_candidates_provisional": 78,
        "long_video_source_windows_scoped_reviewed": 18,
        "narrow_official_source_reviews": 19,
        "full_v5_private_source_model_analysis_receipts": 0,
        "independent_atomic_recall_measured": False,
        "p0_financial_research_release": "NO_GO",
        "p1_formal_knowledge_merge": "BLOCKED",
        "personal_advice_approved": False,
    }


if __name__ == "__main__":
    print(json.dumps(research_state(), ensure_ascii=False, sort_keys=True))
