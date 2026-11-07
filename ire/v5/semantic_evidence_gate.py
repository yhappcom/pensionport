"""Audit fine-grained semantic/evidence recheck without legal/advisory self-approval.

This gate verifies cue-to-existing-source anchoring, evidence type, temporal
effectivity and preservation of earlier knowledge. It cannot independently
recreate model semantics or attest legal-source document bytes. The private
SRT is *not* in GitHub CI; existing new_video_followup_gate verifies it in
the active private host with --private-zip.
"""
from __future__ import annotations
import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

OVERLAY = Path("ire/v5/new_video_studies/WIXWPJjhF50_SEMANTIC_EVIDENCE_RECHECK_20261105.json")
PARENT = Path("ire/v5/new_video_studies/WIXWPJjhF50_20261105.json")


class SemanticEvidenceGateError(ValueError):
    pass


def require(ok: bool, code: str) -> None:
    if not ok:
        raise SemanticEvidenceGateError(code)


def read(p: Path) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def verify(root: Path, overlay: dict | None = None) -> dict:
    root = Path(root)
    o = overlay if overlay is not None else read(root / OVERLAY)
    parent = read(root / PARENT)
    v = parent["video"]
    review_date = date.fromisoformat(o["review_date"])
    require(o.get("schema") == "IRE_V5_SOURCE_SEMANTIC_EVIDENCE_RECHECK_V1"
            and review_date == date(2026, 11, 5)
            and o.get("video_id") == v["video_id"] == "WIXWPJjhF50"
            and o.get("roster_no") == v["roster_no"] == 232
            and o.get("source_cues") == v["original_cue_count"] == 185
            and o.get("original_srt_sha256") == v["original_srt_sha256"]
            and o.get("previous_study_path") == str(PARENT)
            and o.get("full_source_parent_windows_rechecked_from_private_srt") is True,
            "SEMANTIC_SOURCE_BASELINE_MISMATCH")
    require(o.get("prior_canonical_education_13_unchanged") is True
            and o.get("legacy_claims_116_unchanged") is True
            and o.get("previous_12_source_claims_unchanged") is True
            and o.get("new_provisional_concepts_approved") == 0
            and o.get("individual_investment_advice_approved") is False
            and o.get("financial_fact_independently_certified") is False
            and o.get("semantic_recall_against_blind_human_gold") is None
            and o.get("unverified_screen_prices_status") ==
                "OPEN_PENDING_ORIGINAL_VIDEO_SCREEN_AND_KRX_POINT_IN_TIME_PRICES",
            "SEMANTIC_PRETENDS_APPROVED_OR_SCREEN_VERIFIED")
    auth = {}
    for ref in o.get("external_references", []):
        k = ref["id"]
        url = urlparse(ref.get("url", ""))
        require(k not in auth and url.scheme == "https"
                and bool(url.hostname) and len(ref.get("description", "")) > 12
                and ref.get("original_document_bytes_sealed") is False
                and ref.get("external_blind_review") is False,
                "SEMANTIC_AUTHORITY_PROVENANCE_FALSE")
        auth[k] = ref
    require(len(auth) >= 10
            and sum(x["kind"].startswith("OFFICIAL")
                    or x["issuer"] in {"금융위원회", "한국거래소 KIND"}
                    for x in auth.values()) >= 6,
            "SEMANTIC_OFFICIAL_CROSS_REFERENCES_INSUFFICIENT")
    original = {r["claim_id"]: r for r in parent["research_claims"]}
    records = o.get("semantic_assertions", [])
    require(len(records) == 22, "SEMANTIC_FINE_CLAIMS_COUNT_INCOMPLETE")
    for n, item in enumerate(records, 1):
        claim_id = item.get("parent_claim_id")
        require(item.get("analysis_id") == f"S232-{n:02d}"
                and claim_id in original,
                "SEMANTIC_ID_OR_PARENT_MISSING")
        ref = original[claim_id]
        start, end = item.get("cue_start"), item.get("cue_end")
        require(type(start) is int and type(end) is int
                and ref["cue_start"] <= start <= end <= ref["cue_end"]
                and len(item.get("source_paraphrase", "")) >= 26
                and len(item.get("independent_evidence_analysis", "")) >= 45,
                "SEMANTIC_ATOMIC_ANCHOR_OR_REVIEW_MISSING")
        refs = item.get("source_ids", [])
        require(type(refs) is list and len(refs) > 0
                and len(set(refs)) == len(refs)
                and set(refs) <= set(auth),
                "SEMANTIC_EVIDENCE_IDS_FABRICATED")
        require(item.get("source_audio_verified") is False
                and item.get("blind_human_verified") is False
                and item.get("individual_advice_approved") is False
                and "CERTIFIED" not in item.get("adjudication", ""),
                "SEMANTIC_UNREVIEWED_FACT_PROMOTED")
    by_id = {r["analysis_id"]: r for r in records}
    def has(rid: str, *words: str) -> bool:
        return all(word in by_id[rid]["independent_evidence_analysis"]
                   for word in words)
    require(by_id["S232-03"]["adjudication"] ==
                "SOURCE_NUMERIC_DISCREPANCY_CONFIRMED_AUDIO_OPEN"
            and has("S232-03", "+160%", "+130%", "ASR")
            and by_id["S232-06"]["adjudication"] ==
                "HISTORICAL_FUTURE_NOW_EFFECTIVE_WITH_LEGAL_FORM_CORRECTION"
            and has("S232-06", "2023-06-26", "400%", "+300%"),
            "SEMANTIC_OLD_ARITHMETIC_OR_EFFECTIVE_DATE_LOST")
    require(by_id["S232-14"]["adjudication"] ==
                "OVERGENERALIZATION_CONTRADICTED_BY_CONTEMPORANEOUS_DATA"
            and has("S232-14", "6개", "3개", "제이오")
            and by_id["S232-20"]["adjudication"] ==
                "INVALID_VALUATION_INFERENCE"
            and has("S232-20", "발행주식수", "시가총액")
            and by_id["S232-10"]["adjudication"] ==
                "PARTIAL_EXAMPLE_CONFIRMED_SNAPSHOT_OPEN",
            "SEMANTIC_MISSING_CRITICAL_ERRORS_AND_PARTIAL_EVIDENCE")
    rules = {r["id"]: r for r in o.get("temporal_rule_updates", [])}
    ipo = rules.get("IPO-2023-FIRST-DAY", {})
    future = rules.get("IPO-2026-PREDEMAND-CORNERSTONE", {})
    require(ipo.get("status") == "EFFECTIVE_CURRENT"
            and ipo.get("effective_from") == "2023-06-26"
            and ipo.get("range_pct_of_offer") == [60, 400]
            and set(ipo.get("sources", [])) <= set(auth)
            and future.get("status") ==
                "APPROVED_NOT_YET_EFFECTIVE_AS_OF_2026-11-05"
            and future.get("approved_decree_on") == "2026-11-03"
            and date.fromisoformat(future.get("effective_on")) >
                review_date
            and future.get("effective_on") == "2026-11-13"
            and "별도 규정" in future.get("scope_note", "")
            and set(future.get("sources", [])) <= set(auth),
            "SEMANTIC_2026_FUTURE_RULE_FALSELY_EFFECTIVE")
    return {
        "schema": "IRE_V5_FINE_SEMANTIC_EVIDENCE_GATE_V1",
        "video_id": v["video_id"],
        "rechecked_semantic_units": len(records),
        "parent_original_claims_preserved": len(original),
        "original_source_cues_parent_covered": v["original_cue_count"],
        "external_evidence_sources": len(auth),
        "separate_future_2026_ipo_rule_not_prematurely_effective": True,
        "historical_arithmetic_error_flagged": True,
        "feb_2023_all_ttasang_overgeneralization_blocked": True,
        "share_price_company_size_inference_blocked": True,
        "independent_human_blind_recall_measured": False,
        "financial_fact_certified": False,
        "individual_financial_advice_released": False,
        "outcome": "SEMANTICS_AND_OFFICIAL_CONTEXT_RECHECKED_WITH_EXPLICIT_OPEN_ITEMS",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    args = p.parse_args()
    print(json.dumps(verify(args.root), sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
