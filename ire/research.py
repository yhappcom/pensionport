"""Evidence validation and independent-review queue.

Document content matching does not establish issuing authority, applicability,
authenticity, factual truth, statutory effectiveness or independent review.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
import re
from urllib.parse import urlparse
from .claims import obligations
from .source import require, sha256, text_norm, DIGEST

def inspect_document_bytes(document: bytes, expected_sha256: str,
                           locator: str, quotation: str) -> dict:
    require(type(document) is bytes and 0 < len(document)<=20_000_000,
            "INVALID_EVIDENCE_DOCUMENT_BYTES")
    require(type(expected_sha256) is str
            and DIGEST.fullmatch(expected_sha256) is not None
            and sha256(document)==expected_sha256,
            "EVIDENCE_SHA256_MISMATCH")
    address=urlparse(locator)
    require(address.scheme=="https" and address.netloc and
            not address.username and not address.password,
            "EVIDENCE_CANONICAL_HTTPS_LOCATOR_REQUIRED")
    require(type(quotation) is str and len(quotation)>=8 and
            len(quotation)<=3000, "EVIDENCE_QUOTE_REQUIRED")
    try:
        text=document.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("OFFLINE_DOCUMENT_TEXT_UTF8_REQUIRED") from exc
    require(text_norm(quotation) in text_norm(text),
            "EVIDENCE_QUOTE_NOT_IN_DOCUMENT")
    return {
        "schema":"IRE_DOCUMENT_BYTE_MATCH_V1",
        "document_sha256":expected_sha256,
        "canonical_https_locator":locator,
        "quotation_text_sha256":sha256(quotation.encode("utf-8")),
        "source_bytes_match":True,
        "publisher_identity_verified":False,
        "current_legal_effect_verified":False,
        "scope_and_exceptions_verified":False,
        "independently_reviewed":False,
        "claim_truth_approved":False,
        "evidence_status":"PROVISIONAL_SOURCE_TEXT_MATCH_ONLY"
    }


def decimal_input(value: str) -> Decimal:
    require(type(value) is str and len(value)<=80,
            "DECIMAL_INPUT_MUST_BE_EXACT_STRING")
    try:
        x=Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("INVALID_EXACT_DECIMAL") from exc
    require(x.is_finite(), "NONFINITE_CALCULATION")
    return x


def compound_lump_sum(principal: str, annual_rate: str, years: int) -> dict:
    """Independent algebraic sanity check, not a product forecast.

    annual_rate is an *effective* annual decimal (e.g. "0.04"), before fees.
    """
    require(type(years) is int and 0<=years<=100,
            "CALCULATION_YEARS_INVALID")
    p=decimal_input(principal)
    r=decimal_input(annual_rate)
    require(p>=0 and Decimal("-1")<r<=Decimal("2"),
            "CALCULATION_INPUTS_UNBOUNDED")
    result=p*(Decimal(1)+r)**years
    return {
        "schema":"IRE_EXACT_ARITHMETIC_V1",
        "principal":str(p),"effective_annual_rate":str(r),
        "year_count":years,
        "gross_future_value":str(result),
        "taxes_included":False,"fees_included":False,
        "financial_fact_verified":False,"investment_result_guaranteed":False
    }


def pending_research(proposed: dict) -> dict:
    require(type(proposed) is dict and proposed.get("schema")=="IRE_PROPOSALS_V1"
            and type(proposed.get("claims")) is list,
            "RESEARCH_REQUIRES_TYPED_ATOMIC_LEDGER")
    records=[]
    for claim in proposed["claims"]:
        records.append({
            "claim_id":claim["claim_id"],
            "obligations":obligations(claim),
            "official_evidence":"NOT_INDEPENDENTLY_VERIFIED",
            "numeric_and_empirical":"NOT_INDEPENDENTLY_VERIFIED",
            "source_meaning":"NOT_INDEPENDENTLY_VERIFIED",
            "reviewer_identity":"NOT_ATTESTED",
            "decision":"BLOCKED"
        })
    return {
        "schema":"IRE_INDEPENDENT_RESEARCH_WORKLIST_V1",
        "claims":records,
        "fully_verified_claims":0,
        "independent_research_complete_certificates":0,
        "knowledge_merge_approvals":0,
        "release":"BLOCKED_UNTIL_AUTHENTIC_EVIDENCE_AND_INDEPENDENT_REVIEW"
    }
