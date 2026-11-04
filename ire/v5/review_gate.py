"""Fail-closed source review and cumulative-knowledge candidate gate.

Runs entirely with Python stdlib. A prior legacy claim, a video transcript review,
or a web URL is not by itself verified financial knowledge or approved advice.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

SHA = re.compile(r"[0-9a-f]{64}\Z")
VID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
REVIEW_SCHEMA = "IRE_V5_CHATGPT_SOURCE_STUDY_V1"


class ReviewGateError(ValueError):
    pass


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ReviewGateError(code)


def legacy_claim_ids(path: str | Path) -> set[str]:
    ids: set[str] = set()
    for number, line in enumerate(Path(path).read_text("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        require(type(obj) is dict and type(obj.get("claim_id")) is str,
                "LEGACY_CLAIM_ID_MISSING")
        cid = obj["claim_id"]
        require(cid not in ids, "DUPLICATE_LEGACY_CLAIM_ID")
        require(type(obj.get("claim")) is str and obj["claim"].strip() != "",
                "LEGACY_CLAIM_EMPTY")
        require(type(obj.get("supporting_videos")) is list and
                len(obj["supporting_videos"]) > 0,
                "LEGACY_CLAIM_WITHOUT_SOURCE_ID")
        ids.add(cid)
    require(bool(ids), "EMPTY_LEGACY_LEDGER")
    return ids


def validate_review(review: dict, prior_ids: set[str],
                    original_srt: bytes | None = None) -> dict:
    require(type(review) is dict and review.get("schema") == REVIEW_SCHEMA,
            "REVIEW_SCHEMA_INVALID")
    require(type(review.get("video_id")) is str and
            VID.fullmatch(review["video_id"]) is not None,
            "REVIEW_VIDEO_ID_INVALID")
    require(type(review.get("source_sha256")) is str and
            SHA.fullmatch(review["source_sha256"]) is not None,
            "REVIEW_SOURCE_HASH_INVALID")
    n = review.get("cues")
    require(type(n) is int and n > 0, "REVIEW_CUE_COUNT_INVALID")
    if original_srt is not None:
        require(hashlib.sha256(original_srt).hexdigest() ==
                review["source_sha256"], "REVIEW_LIVE_SOURCE_MISMATCH")
        from .corpus_catalog import inspect_srt
        cues, duration = inspect_srt(original_srt)
        require(cues == n, "REVIEW_LIVE_SOURCE_MISMATCH")
        require(duration == review["source_total_ms"],
                "REVIEW_LIVE_SOURCE_DURATION_MISMATCH")
    require(review.get("investment_advice_approved") is False and
            review.get("financial_facts_independently_approved") == 0 and
            review.get("no_auto_advisory") is True,
            "UNAUTHORIZED_ADVISORY_PROMOTION")
    sections = review.get("sections")
    claims = review.get("claims")
    require(type(sections) is list and type(claims) is list and
            len(sections) > 0 and len(claims) > 0,
            "REVIEW_SECTIONS_OR_CLAIMS_MISSING")
    ids: set[str] = set()
    for claim in claims:
        require(type(claim) is dict and type(claim.get("claim_id")) is str and
                claim["claim_id"].startswith("V5-" + review["video_id"] + "-") and
                claim["claim_id"] not in ids,
                "REVIEW_CLAIM_ID_DUPLICATE_OR_WRONG_SOURCE")
        ids.add(claim["claim_id"])
        a,b=claim.get("cue_start"),claim.get("cue_end")
        require(type(a) is int and type(b) is int and 1<=a<=b<=n,
                "REVIEW_CLAIM_OUTSIDE_SOURCE")
        require(type(claim.get("proposition")) is str and
                len(claim["proposition"].strip())>=8,
                "REVIEW_EMPTY_PROPOSITION")
        require(claim.get("finance_fact_independently_approved") is False and
                claim.get("advisory_eligible") is False and
                claim.get("relation_status")=="CANDIDATE_NOT_MERGED",
                "UNAUTHORIZED_CLAIM_OR_KNOWLEDGE_MERGE")
        prior=claim.get("prior_claim_candidates")
        require(type(prior) is list and len(prior)==len(set(prior)) and
                all(cid in prior_ids for cid in prior),
                "UNRESOLVED_PRIOR_CLAIM_REFERENCE")
        require(type(claim.get("open_reason")) is str and
                len(claim["open_reason"].strip())>=10,
                "CLAIM_APPLICABILITY_UNDOCUMENTED")
        urls=claim.get("official_sources")
        require(type(urls) is list and
                all(type(url) is str and url.startswith("https://") for url in urls),
                "OFFICIAL_SOURCE_URL_INVALID")
        # URL presence is a citation candidate, NOT proof of official source bytes.
    cursor=1
    refs=set()
    for sec in sections:
        require(type(sec) is dict and type(sec.get("from")) is int and
                type(sec.get("to")) is int and sec["from"]==cursor and
                sec["from"]<=sec["to"]<=n,
                "SOURCE_CUE_CENSUS_GAP_OR_OVERLAP")
        cursor=sec["to"]+1
        require(type(sec.get("claim_ids")) is list and
                all("V5-"+review["video_id"]+"-"+short in ids for short in sec["claim_ids"]),
                "SOURCE_SECTION_UNKNOWN_CLAIM")
        for short in sec["claim_ids"]:
            refs.add("V5-"+review["video_id"]+"-"+short)
    require(cursor==n+1,"SOURCE_CUE_CENSUS_INCOMPLETE")
    require(refs==ids,"REVIEW_CLAIM_WITHOUT_CUE_SECTION")
    require(type(review.get("open_items")) is list and
            len(review["open_items"])>0,"MISSING_OPEN_QUALITY_ITEMS")
    return {
        "schema":"IRE_V5_REVIEW_GATE_RESULT_V1",
        "video_id":review["video_id"],
        "source_sha256":review["source_sha256"],
        "all_cue_sections_accounted_for":True,
        "source_rechecked_with_raw_bytes":original_srt is not None,
        "claims_provisional":len(ids),
        "legacy_claim_candidates_validated":sum(
            len(c["prior_claim_candidates"]) for c in claims),
        "open_quality_items":len(review["open_items"]),
        "knowledge_merge_approved":False,
        "financial_facts_independently_approved":0,
        "investment_advice_eligible":False,
        "release":"SOURCE_REVIEW_ONLY_NO_ADVISORY"
    }


def main() -> int:
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review",type=Path,required=True)
    parser.add_argument("--prior",type=Path,required=True)
    parser.add_argument("--original-srt",type=Path)
    args=parser.parse_args()
    report=json.loads(args.review.read_text("utf-8"))
    original=args.original_srt.read_bytes() if args.original_srt else None
    result=validate_review(report,legacy_claim_ids(args.prior),original)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
