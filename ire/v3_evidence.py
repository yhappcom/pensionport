"""IRE V3: fail-closed official-document scope evidence audit.

A current-chat model supplies proposed support/contradiction AND exact primary
document anchors for every claimed scope match. Deterministic guards verify
each quote against independently captured official-domain page text and check
declared effective dates and numerical tokens. This is not external legal
validation, human independent assessment, or financial truth certification.
Legacy V2 evidence entries remain intact but do not gain V3 anchor status.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import re

from .source import require, sha256, text_norm, DIGEST
from .checkpoint import safe_private_directory
from .cli import private_file
from .evidence import independently_fetch_candidate, issuer_for
from .knowledge import read_private_snapshot, validate_knowledge
from .v2_evidence import (
    REQUIRED_REVIEW, SCOPE_FIELDS, SCOPE_VALUES,
    apply_chat_evidence, save_private_evidence, validate_evidence_ledger,
)

SCHEMA = "IRE_CHAT_EVIDENCE_REVIEW_V3"
REQUIRED = REQUIRED_REVIEW | {"scope_anchors"}
MAX_ANCHORS_PER_SCOPE = 8
MAX_ANCHOR_CHARS = 1000
NUMERIC = re.compile(r"(?<![A-Za-z0-9])\d[\d,.]*\s*(?:%|퍼센트|원|억|만|bp|bps)", re.I)


def _canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _date_in_anchor(day: str, anchor: str) -> bool:
    year, month, number = (int(x) for x in day.split("-"))
    forms = (
        rf"(?<!\d){year}\s*[-./]\s*{month:02d}\s*[-./]\s*{number:02d}(?!\d)",
        rf"(?<!\d){year}\s*[-./]\s*{month}\s*[-./]\s*{number}(?!\d)",
        rf"(?<!\d){year}\s*년\s*0?{month}\s*월\s*0?{number}\s*일",
    )
    return any(re.search(pattern, anchor) for pattern in forms)


def _claim_with_id(knowledge: dict, claim_id: str) -> dict:
    for claim in knowledge["claims"]:
        if claim["global_claim_id"] == claim_id:
            return claim
    raise ValueError("V3_SCOPE_UNREGISTERED_CLAIM")


def audit_v3_scope(knowledge: dict, document: dict, review: dict) -> dict:
    """Check proposed scope anchors without asserting semantic/legal truth."""
    validate_knowledge(knowledge)
    require(type(review) is dict and set(review) == REQUIRED and
            review.get("schema") == SCHEMA and
            review.get("chat_reviewer_mode") == "CURRENT_CHATGPT_CONVERSATION",
            "V3_SCOPE_REVIEW_CONTRACT_INVALID")
    require(type(document) is dict and
            document.get("schema") == "IRE_INDEPENDENT_DOCUMENT_V1" and
            type(document.get("visible_text")) is str and
            type(document.get("visible_text_sha256")) is str and
            document["visible_text_sha256"] ==
                sha256(document["visible_text"].encode("utf-8")) and
            type(document.get("raw_sha256")) is str and
            DIGEST.fullmatch(document["raw_sha256"]) is not None and
            issuer_for(document.get("canonical_url")) is not None and
            document.get("issuer_domain_category") ==
                issuer_for(document["canonical_url"]) and
            document.get("source_read_mode") in (
                "LIVE_NETWORK_FETCH", "INJECTED_SYNTHETIC_READER"),
            "V3_SCOPE_DOCUMENT_PROVENANCE_INVALID")
    require(document.get("canonical_url") == review["document_url"] and
            document["raw_sha256"] == review["document_sha256"] and
            document["visible_text_sha256"] == review["document_text_sha256"],
            "V3_SCOPE_DOCUMENT_IDENTITY_MISMATCH")
    claim = _claim_with_id(knowledge, review["global_claim_id"])
    scope = review.get("scope")
    require(document.get("extracted_text_truncated") is not True,
            "V3_SCOPE_TRUNCATED_OFFICIAL_TEXT_CANNOT_JUDGE_FULL_SCOPE")
    anchors = review.get("scope_anchors")
    require(type(scope) is dict and set(scope) == set(SCOPE_FIELDS) and
            all(x in SCOPE_VALUES for x in scope.values()) and
            type(anchors) is dict and set(anchors) == set(SCOPE_FIELDS),
            "V3_SCOPE_FIELDS_INVALID")

    full_text = text_norm(document["visible_text"])
    hashes = {}
    for field in SCOPE_FIELDS:
        values = anchors[field]
        require(type(values) is list and
                len(values) <= MAX_ANCHORS_PER_SCOPE and
                all(type(v) is str and
                    8 <= len(v.strip()) <= MAX_ANCHOR_CHARS
                    for v in values) and
                len(set(values)) == len(values),
                "V3_SCOPE_ANCHOR_LIST_INVALID")
        if scope[field] in ("MATCH", "CONFLICT"):
            require(bool(values), "V3_SCOPE_POSITIVE_WITHOUT_ANCHOR")
        else:
            require(not values, "V3_SCOPE_UNRESOLVED_HAS_UNJUSTIFIED_ANCHOR")
        for value in values:
            require(text_norm(value) in full_text,
                    "V3_SCOPE_ANCHOR_NOT_IN_DOCUMENT")
        hashes[field] = [sha256(v.encode("utf-8")) for v in values]

    frame = claim["frame"]
    if scope["jurisdiction"] == "MATCH":
        require(frame.get("jurisdiction") is not None,
                "V3_SCOPE_NO_CLAIM_JURISDICTION")
    if scope["conditions"] == "MATCH":
        require(bool(frame.get("conditions")),
                "V3_SCOPE_NO_CLAIM_CONDITIONS")
    if scope["exceptions"] == "MATCH":
        require(bool(frame.get("exceptions")),
                "V3_SCOPE_NO_CLAIM_EXCEPTIONS")
    if scope["numbers"] == "MATCH":
        measurements = frame.get("measurements") or []
        require(bool(measurements), "V3_SCOPE_NO_CLAIM_MEASUREMENTS")
        number_text = text_norm(" ".join(anchors["numbers"]))
        for measurement in measurements:
            value = text_norm(measurement["value_text"])
            require(value in number_text,
                    "V3_SCOPE_NUMBER_NOT_IN_EXACT_DOCUMENT_ANCHOR")
    elif scope["numbers"] == "CONFLICT":
        require(any(NUMERIC.search(x) for x in anchors["numbers"]),
                "V3_SCOPE_NUMERIC_CONFLICT_WITHOUT_NUMBER")

    start, end = review["effective_from"], review["effective_until"]
    require(start is None or
            (type(start) is str and date.fromisoformat(start).isoformat() == start),
            "V3_SCOPE_START_DATE_INVALID")
    require(end is None or
            (type(end) is str and date.fromisoformat(end).isoformat() == end),
            "V3_SCOPE_END_DATE_INVALID")
    require(start is None or end is None or start <= end,
            "V3_SCOPE_DATE_RANGE_INVALID")
    if start is not None or end is not None:
        require(scope["effective_date"] == "MATCH",
                "V3_SCOPE_UNANCHORED_EFFECTIVE_RANGE")
        date_text = " ".join(anchors["effective_date"])
        for boundary in (start, end):
            if boundary is not None:
                require(_date_in_anchor(boundary, date_text),
                        "V3_SCOPE_EFFECTIVE_BOUNDARY_NOT_IN_DOCUMENT")
    if scope["effective_date"] == "MATCH":
        require(start is not None,
                "V3_SCOPE_MATCHED_DATE_WITHOUT_BEGINNING")
    quote = review.get("source_quote")
    require(type(quote) is str and
            8 <= len(quote) <= 1500 and
            text_norm(quote) in full_text,
            "V3_SCOPE_MAIN_QUOTE_NOT_IN_DOCUMENT")
    return {
        "schema": "IRE_V3_SCOPED_DOCUMENT_AUDIT_V1",
        "global_claim_id": review["global_claim_id"],
        "document_sha256": document["raw_sha256"],
        "document_text_sha256": document["visible_text_sha256"],
        "issuer_candidate_only": issuer_for(document["canonical_url"]),
        "anchor_sha256_by_scope": hashes,
        "scope_proposals": scope,
        "effective_from_proposal": start,
        "effective_until_proposal": end,
        "source_document_truncated": document.get("extracted_text_truncated") is True,
        "actual_network_fetch": document["source_read_mode"] == "LIVE_NETWORK_FETCH",
        "citation_text_and_scope_anchors_matched": True,
        "scope_semantic_truth_verified": False,
        "statutory_effect_verified": False,
        "independent_human_review": False,
        "approved_financial_facts": 0,
    }


def apply_v3_scope_evidence(ledger: dict, knowledge: dict,
                            document: dict, review: dict) -> tuple[dict, dict]:
    """Reuse V2 immutable evidence event, add a separately sealed V3 receipt."""
    validate_evidence_ledger(ledger, knowledge)
    audit = audit_v3_scope(knowledge, document, review)
    older = {k: v for k, v in review.items() if k != "scope_anchors"}
    older["schema"] = "IRE_CHAT_EVIDENCE_REVIEW_V2"
    newer = apply_chat_evidence(ledger, knowledge, document, older)
    event = newer["assessments"][-1]
    core = {
        **audit,
        "schema": "IRE_V3_SCOPED_EVIDENCE_RECEIPT_V1",
        "assessment_id": event["assessment_id"],
        "previous_evidence_sha256": ledger["snapshot_sha256"],
        "next_evidence_sha256": newer["snapshot_sha256"],
        "knowledge_snapshot_sha256": knowledge["snapshot_sha256"],
        "review_sha256": sha256(_canonical(review)),
        "financial_advice_approved": False,
    }
    receipt = {**core, "receipt_sha256": sha256(_canonical(core))}
    return newer, receipt


def save_v3_scope_receipt(receipt: dict, directory: str) -> str:
    require(type(receipt) is dict and
            receipt.get("schema") == "IRE_V3_SCOPED_EVIDENCE_RECEIPT_V1" and
            type(receipt.get("receipt_sha256")) is str and
            DIGEST.fullmatch(receipt["receipt_sha256"]) and
            sha256(_canonical({k: v for k, v in receipt.items()
                               if k != "receipt_sha256"})) ==
                receipt["receipt_sha256"] and
            receipt["approved_financial_facts"] == 0 and
            receipt["financial_advice_approved"] is False,
            "V3_SCOPE_RECEIPT_INVALID")
    root = safe_private_directory(directory)
    target = root / ("ire_v3_scope_" + receipt["receipt_sha256"] + ".json")
    raw = _canonical(receipt)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return str(target)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="No-API, original-document-anchored V3 finance evidence")
    parser.add_argument("operation", choices=["review"])
    parser.add_argument("--private-knowledge-snapshot", required=True)
    parser.add_argument("--private-ledger", required=True)
    parser.add_argument("--private-chat-review", required=True)
    parser.add_argument("--private-evidence-dir", required=True)
    parser.add_argument("--private-original-document-dir", required=True)
    args = parser.parse_args()
    try:
        knowledge = read_private_snapshot(args.private_knowledge_snapshot)
        ledger = json.loads(private_file(
            args.private_ledger).read_text(encoding="utf-8"))
        review = json.loads(private_file(
            args.private_chat_review).read_text(encoding="utf-8"))
        require(type(review) is dict and
                type(review.get("document_url")) is str,
                "V3_SCOPE_OFFICIAL_URL_REQUIRED")
        doc = independently_fetch_candidate(
            review["document_url"],
            private_evidence_dir=args.private_original_document_dir)
        updated, receipt = apply_v3_scope_evidence(
            ledger, knowledge, doc, review)
        result_path = save_private_evidence(
            updated, knowledge, args.private_evidence_dir)
        receipt_path = save_v3_scope_receipt(
            receipt, args.private_evidence_dir)
        result = {
            "schema": "IRE_V3_SCOPE_EVIDENCE_REVIEW_RESULT",
            "status": "DOCUMENT_QUOTES_MATCHED_FINANCIAL_TRUTH_UNATTESTED",
            "receipt_sha256": receipt["receipt_sha256"],
            "evidence_snapshot_sha256": updated["snapshot_sha256"],
            "knowledge_snapshot_sha256": knowledge["snapshot_sha256"],
            "private_evidence_path": result_path,
            "private_receipt_path": receipt_path,
            "issuer_candidate_only": receipt["issuer_candidate_only"],
            "financial_facts_approved": 0,
            "model_api_calls": 0,
        }
        # Never echo personal source claims/quotes or review material.
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 2
    except (ValueError, KeyError, TypeError, OSError, UnicodeError):
        print(json.dumps({"schema": "IRE_V3_SCOPE_EVIDENCE_ERROR",
                          "status": "FAILED_CLOSED"}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())