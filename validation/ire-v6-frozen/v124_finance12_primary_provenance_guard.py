"""V124 official-body relevance negative-control guard for finance OPEN 12.

Additive to V123 ChatGPT gate; never approves semantic entailment, identity,
legal effective-period coverage, taxpayer/product eligibility or P0 GO.
Owner-private transcript, account data, and case notes are never emitted.
"""
from __future__ import annotations
import html
import re
from datetime import date
from pathlib import Path

from verify_pinned_official_snapshot import RECORDS, verify

CASE_IDS = (
    "R001","R004","R005","R007","R008","R009",
    "R010","R011","R012","R014","R015","R018",
)
SOURCE = "decree_40_3"
CONTEXT_ONLY = frozenset({"R004", "R010"})
DIRECT_CLAUSE_ONLY = frozenset({"R011"})
SOURCE_LINKED = CONTEXT_ONLY | DIRECT_CLAUSE_ONLY
SOURCE_ORDER_ANCHORS = (
    "제40조의3(연금계좌의 인출순서 등)", "과세제외금액",
    "이연퇴직소득", "연금계좌세액공제",
)

def _fail(code):
    raise ValueError("V124_" + code)

def _plain(raw):
    text = html.unescape(raw.decode("utf-8-sig", errors="strict"))
    text = re.sub(r"<[^>]*>", " ", text)
    return re.sub(r"\s+", " ", text)

def _case_expected_source(cid):
    return (SOURCE,) if cid in SOURCE_LINKED else ()

def _case_expected_class(cid):
    if cid in DIRECT_CLAUSE_ONLY:
        return "STATUTORY_SOURCE_ORDER_CLAUSE_ONLY_NOT_CASE_ELIGIBILITY"
    if cid in CONTEXT_ONLY:
        return "WITHDRAWAL_SOURCE_CONTEXT_NOT_FULL_CLAIM_SUPPORT"
    return "NO_MATCHING_ARCHIVED_PRIMARY_RESPONSE"

def audit_archived_finance_case_relevance(raw_dir: Path, case_rows: list[dict],
                                          *, review_date: str="2026-11-15") -> dict:
    """Rehash actual public original source bytes, reject unrelated claims.

    This preflight has no approval path: source-to-claim applicability and
    independent ChatGPT final decision remain OPEN.
    """
    try:
        d = date.fromisoformat(review_date)
        if d.isoformat() != review_date:
            _fail("REVIEW_DATE_INVALID")
    except (ValueError, TypeError) as exc:
        raise ValueError("V124_REVIEW_DATE_INVALID") from exc
    evidence = verify(raw_dir)
    if (evidence["government_raw_body_files_reverified"] != 2
            or evidence["all_body_bytes_hash_match"] is not True):
        _fail("ARCHIVED_BODY_REPLAY_FAILED")
    blobs = {key:(raw_dir / rec["filename"]).read_bytes()
             for key,rec in RECORDS.items()}
    law = _plain(blobs[SOURCE])
    if not all(anchor in law for anchor in SOURCE_ORDER_ANCHORS):
        _fail("PINNED_LAW_SOURCE_ORDER_ANCHOR_MISSING")
    nts = _plain(blobs["nts_pension"])
    if "연금소득" not in nts:
        _fail("PINNED_NTS_PENSION_TOPIC_MISSING")
    # This older NTS pension-income page cannot be misused for ISA 60 days.
    if "개인종합자산관리계좌" in nts and "60일" in nts:
        _fail("HISTORICAL_NTS_ISA_TOPIC_CHANGED")
    if type(case_rows) is not list or len(case_rows) != len(CASE_IDS):
        _fail("FINANCE12_CASE_CENSUS")
    seen = set()
    for row in case_rows:
        if type(row) is not dict or set(row) != {
            "reference_id", "linked_archived_body_ids", "original_source_class",
            "private_evidence_note_sha256", "authority_issuer_checked",
            "current_effective_range_verified", "exact_account_and_product_scope_verified",
            "speaker_audio_verified", "primary_claim_body_entailment_adjudicated",
            "finance_fact_status", "finance_fact_approved",
        }:
            _fail("ROW_SCHEMA")
        cid = row["reference_id"]
        if type(cid) is not str or cid not in CASE_IDS or cid in seen:
            _fail("CASE_ID_DUPLICATE_OR_UNKNOWN")
        if (row["linked_archived_body_ids"] != list(_case_expected_source(cid))
                or row["original_source_class"] != _case_expected_class(cid)):
            _fail("ARCHIVED_BODY_IRRELEVANT_OR_MISATTRIBUTED")
        digest = row["private_evidence_note_sha256"]
        if type(digest) is not str or not re.fullmatch("[a-f0-9]{64}", digest):
            _fail("PRIVATE_REVIEW_NOTE_DIGEST_MISSING")
        if any(row[k] is not False for k in (
            "authority_issuer_checked", "current_effective_range_verified",
            "exact_account_and_product_scope_verified", "speaker_audio_verified",
            "primary_claim_body_entailment_adjudicated", "finance_fact_approved",
        )) or row["finance_fact_status"] != "OPEN":
            _fail("FALSE_FINANCE_FACT_AUTHORITY_OR_PREMATURE_CLOSURE")
        seen.add(cid)
    if seen != set(CASE_IDS):
        _fail("CASE_CENSUS_MISMATCH")
    return {
        "schema":"IRE_V124_FINANCE12_PRIMARY_RELEVANCE_HOLD_RECEIPT_V1",
        "as_of":review_date,
        "official_archived_original_bodies_sha_verified":2,
        "archived_2026_11_08_source_order_clause_visible":True,
        "archived_nts_generic_pension_page_has_isa_60_day_proof":False,
        "finance12_cases_accounted":12,
        "cases_with_older_archived_law_source_context":len(SOURCE_LINKED),
        "cases_with_direct_statutory_subclause_present":len(DIRECT_CLAUSE_ONLY),
        "cases_without_claim_specific_archived_body":len(CASE_IDS)-len(SOURCE_LINKED),
        "original_issuer_notice_for_promotion_R015_present":False,
        "claim_substantive_entailment_approved":False,
        "effective_period_and_account_applicability_adjudicated":False,
        "independent_owner_production_db_verified":False,
        "finance_facts_approved":0, "finance_cases_open":12,
        "new_research_candidates_export_allowed":False,"p0_go":False,
        "status":"FINANCE12_PRIMARY_BYTES_PARTIAL_SCOPE_HOLD",
    }
