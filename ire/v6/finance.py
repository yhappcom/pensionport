"""V6-4: finance evidence and prior-knowledge *candidate* structural auditing.

This code never decides that an issuer is genuine, a quote semantically supports
an investment proposition, or a prior relation is correct. Source byte hashes,
URL/issuer metadata, effective dates and baseline membership are checked. The
output is explicitly REVIEW_PENDING and cannot approve financial facts.
"""
from __future__ import annotations

import re
from datetime import date
from urllib.parse import urlsplit

from .codec import canonical, json_digest, require_hash, sha256
from .errors import InvalidInput

CANDIDATE_RELATIONS = frozenset({
    "SAME_PENDING", "EXTENDS_PENDING", "CONFLICT_PENDING",
    "SUPERSEDED_PENDING", "DISTINCT_PENDING", "OPEN"
})
CLAIM_ID = re.compile(r"C[0-9]{5,8}\Z")
PRIOR_ID = re.compile(r"[A-Za-z0-9_.:-]{1,96}\Z")


def _as_date(value: str, code: str) -> date:
    if type(value) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise InvalidInput(code)
    try:
        d = date.fromisoformat(value)
    except ValueError as exc:
        raise InvalidInput(code) from exc
    if d.isoformat() != value:
        raise InvalidInput(code)
    return d


def _url(value: str) -> None:
    if type(value) is not str or not 10 <= len(value) <= 2048:
        raise InvalidInput("EVIDENCE_URL_INVALID")
    try:
        parsed = urlsplit(value)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or
            parsed.password or parsed.fragment or parsed.port not in (None, 443) or
            parsed.hostname in ("localhost", "127.0.0.1") or "." not in parsed.hostname):
            raise InvalidInput("EVIDENCE_URL_NOT_SAFE_HTTPS")
    except ValueError as exc:
        raise InvalidInput("EVIDENCE_URL_NOT_SAFE_HTTPS") from exc
    if any(ord(c) < 32 for c in value):
        raise InvalidInput("EVIDENCE_URL_INVALID")


def audit_official_candidate(document_raw: bytes, proposal: dict,
                             *, expected_document_sha256: str,
                             as_of: str) -> dict:
    """Verify a pinned captured document, not independent issuer authenticity."""
    expected = require_hash(expected_document_sha256, "OFFICIAL_DOCUMENT_PIN")
    if (type(document_raw) is not bytes or not document_raw or
        len(document_raw) > 8 * 1024 * 1024):
        raise InvalidInput("OFFICIAL_DOCUMENT_BYTES_REQUIRED")
    if sha256(document_raw) != expected:
        raise InvalidInput("OFFICIAL_DOCUMENT_BYTES_MISMATCH")
    if type(proposal) is not dict or set(proposal) != {
        "schema", "claim_id", "issuer", "url", "quote", "published_on",
        "effective_from", "effective_until", "retrieved_on", "jurisdiction",
        "scope_note", "claim_support_verdict"
    } or proposal["schema"] != "IRE_V6_OFFICIAL_CANDIDATE_V1":
        raise InvalidInput("OFFICIAL_CANDIDATE_SCHEMA_INVALID")
    claim_id = proposal["claim_id"]
    if type(claim_id) is not str or not CLAIM_ID.fullmatch(claim_id):
        raise InvalidInput("OFFICIAL_CLAIM_ID_INVALID")
    if (type(proposal["issuer"]) is not str or not proposal["issuer"].strip() or
        len(proposal["issuer"]) > 150 or type(proposal["jurisdiction"]) is not str or
        not proposal["jurisdiction"].strip()):
        raise InvalidInput("OFFICIAL_ISSUER_OR_JURISDICTION_INVALID")
    _url(proposal["url"])
    observed = _as_date(as_of, "OFFICIAL_AS_OF_INVALID")
    published = _as_date(proposal["published_on"], "OFFICIAL_PUBLICATION_DATE_INVALID")
    retrieved = _as_date(proposal["retrieved_on"], "OFFICIAL_RETRIEVAL_DATE_INVALID")
    effective = _as_date(proposal["effective_from"], "OFFICIAL_EFFECTIVE_DATE_INVALID")
    until_value = proposal["effective_until"]
    until = None if until_value is None else _as_date(until_value,"OFFICIAL_EXPIRY_DATE_INVALID")
    if (published > retrieved or retrieved > observed or
        (until is not None and until < effective)):
        raise InvalidInput("OFFICIAL_DATE_CHRONOLOGY_INVALID")
    if (type(proposal["quote"]) is not str or len(proposal["quote"].strip()) < 2 or
        type(proposal["scope_note"]) is not str or not proposal["scope_note"].strip()):
        raise InvalidInput("OFFICIAL_QUOTE_OR_SCOPE_MISSING")
    if proposal["claim_support_verdict"] != "UNREVIEWED":
        raise InvalidInput("OFFICIAL_CLAIM_SUPPORT_CANNOT_SELF_APPROVE")
    try:
        body = document_raw.decode("utf-8-sig", errors="strict")
    except UnicodeError as exc:
        raise InvalidInput("OFFICIAL_DOCUMENT_UTF8_REQUIRED") from exc
    # Exact textual presence, not semantic entailment.
    if " ".join(proposal["quote"].split()) not in " ".join(body.split()):
        raise InvalidInput("OFFICIAL_QUOTE_NOT_IN_CAPTURED_DOCUMENT")
    applicable = effective <= observed and (until is None or observed <= until)
    return {
        "schema":"IRE_V6_OFFICIAL_CANDIDATE_AUDIT_V1",
        "claim_id":claim_id, "document_sha256":expected,
        "proposal_sha256":json_digest(proposal),
        "issuer_declared":proposal["issuer"],"url_declared":proposal["url"],
        "as_of":as_of,"effective_at_as_of":applicable,
        "captured_document_bytes_verified":True,
        "quoted_text_present":True,
        "issuer_authenticity_independently_verified":False,
        "claim_semantically_supported":False,
        "finance_fact_approved":False,
        "status":"SOURCE_CANDIDATE_REVIEW_PENDING" if applicable else "DATE_NOT_APPLICABLE",
    }


def audit_prior_relation(baseline: dict, relation: dict, *,
                         expected_baseline_sha256: str) -> dict:
    expected = require_hash(expected_baseline_sha256, "PRIOR_BASELINE_PIN")
    if json_digest(baseline) != expected:
        raise InvalidInput("PRIOR_BASELINE_PIN_MISMATCH")
    if type(baseline) is not dict or set(baseline) != {"schema","entries"} or \
       baseline["schema"] != "IRE_V6_LEGACY_BASELINE_V1":
        raise InvalidInput("PRIOR_BASELINE_SCHEMA_INVALID")
    entries = baseline["entries"]
    if type(entries) is not list or not 1 <= len(entries) <= 100000:
        raise InvalidInput("PRIOR_BASELINE_ENTRIES_INVALID")
    ids = set()
    for record in entries:
        if type(record) is not dict or set(record) != {"id","content_sha256"}:
            raise InvalidInput("PRIOR_BASELINE_ENTRY_INVALID")
        rid = record["id"]
        if type(rid) is not str or not PRIOR_ID.fullmatch(rid) or rid in ids:
            raise InvalidInput("PRIOR_BASELINE_ID_DUPLICATE_OR_INVALID")
        require_hash(record["content_sha256"],"PRIOR_CONTENT_SHA256")
        ids.add(rid)
    if type(relation) is not dict or set(relation) != {
        "schema", "claim_id", "prior_id", "relationship", "rationale",
        "semantic_relation_verified"
    } or relation["schema"] != "IRE_V6_PRIOR_RELATION_CANDIDATE_V1":
        raise InvalidInput("PRIOR_RELATION_SCHEMA_INVALID")
    cid, prior_id = relation["claim_id"], relation["prior_id"]
    if type(cid) is not str or not CLAIM_ID.fullmatch(cid):
        raise InvalidInput("PRIOR_RELATION_CLAIM_INVALID")
    if type(prior_id) is not str or prior_id not in ids:
        raise InvalidInput("PRIOR_RELATION_TARGET_UNKNOWN")
    if (type(relation["relationship"]) is not str or
        relation["relationship"] not in CANDIDATE_RELATIONS or
        type(relation["rationale"]) is not str or not relation["rationale"].strip() or
        relation["semantic_relation_verified"] is not False):
        raise InvalidInput("PRIOR_RELATION_SELF_APPROVAL_OR_REASON_INVALID")
    return {
        "schema":"IRE_V6_PRIOR_RELATION_AUDIT_V1",
        "claim_id":cid,"prior_id":prior_id,"baseline_sha256":expected,
        "legacy_records_in_pinned_snapshot":len(ids),
        "candidate_relation":relation["relationship"],
        "relation_sha256":json_digest(relation),
        "baseline_entry_membership_verified":True,
        "prior_fact_contents_replayed":False,
        "semantic_relation_verified":False,
        "finance_fact_approved":False,
        "status":"RELATION_CANDIDATE_REVIEW_PENDING",
    }
