"""V5 P0C: verify retrieved issuer text and pinned legacy search candidates.
Validation is structural, not independent network attestation or tax advice.
"""
from __future__ import annotations
import base64
from datetime import datetime
from urllib.parse import urlsplit
from .engine import RunError, require, sha256

DOMAINS=("nps.or.kr","nts.go.kr","law.go.kr","krx.co.kr","fsc.go.kr","fss.or.kr","kofia.or.kr")
SOURCE_TYPES={"HOST_RETRIEVED_MARKDOWN","HOST_RETRIEVED_HTML","HOST_RETRIEVED_TEXT"}
FINDINGS={"RULE_CANDIDATE_SCOPE_OPEN","PERSONAL_APPLICABILITY_OPEN",
          "HISTORICAL_RULE_PENDING","CONFLICT_OPEN"}

def _time(value):
    require(type(value) is str and "T" in value,"P0C_OBSERVED_TIME_MISSING")
    try:
        stamp=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc:
        raise RunError("P0C_OBSERVED_TIME_INVALID") from exc
    require(stamp.tzinfo is not None,"P0C_OBSERVED_TIME_NOT_AWARE")

def _host(url):
    try:
        parsed=urlsplit(url)
        host=parsed.hostname or ""
        return (parsed.scheme=="https" and not parsed.username and
            not parsed.password and any(host==d or host.endswith("."+d) for d in DOMAINS))
    except ValueError:
        return False

def validate_official_capture(dossier):
    require(type(dossier) is dict and dossier.get("schema")=="IRE_V5_P0C_OFFICIAL_CAPTURE_V1",
            "P0C_OFFICIAL_CAPTURE_SCHEMA")
    require(type(dossier.get("official_url")) is str and _host(dossier["official_url"]),
            "P0C_OFFICIAL_DOMAIN_NOT_ALLOWED")
    require(type(dossier.get("issuer")) is str and len(dossier["issuer"])>=3,
            "P0C_ISSUER_MISSING")
    require(dossier.get("source_type") in SOURCE_TYPES,"P0C_CAPTURE_TYPE_NOT_DECLARED")
    _time(dossier.get("observed_at"))
    require(dossier.get("independently_attested") is False and
            dossier.get("financial_fact_approved") is False,
            "P0C_UNSUPPORTED_ATTESTATION")
    encoded=dossier.get("capture_base64")
    require(type(encoded) is str and len(encoded)<=2_800_000,
            "P0C_CAPTURE_BYTES_MISSING_OR_TOO_LARGE")
    try:
        raw=base64.b64decode(encoded,validate=True)
        text=raw.decode("utf-8")
    except (ValueError,UnicodeError) as exc:
        raise RunError("P0C_CAPTURE_BAD_ENCODING") from exc
    require(60<=len(raw)<=2_000_000,"P0C_CAPTURE_SIZE_INVALID")
    require(dossier.get("capture_sha256")==sha256(raw),"P0C_CAPTURE_SHA_MISMATCH")
    quote=dossier.get("exact_excerpt")
    require(type(quote) is str and len(quote.strip())>=10 and quote in text,
            "P0C_EXCERPT_NOT_IN_CAPTURED_BYTES")
    require(dossier.get("finding") in FINDINGS and
            type(dossier.get("scope_limitation")) is str and
            len(dossier["scope_limitation"].strip())>=12,
            "P0C_SCOPE_APPLICABILITY_UNREVIEWED")
    require(type(dossier.get("effective_date_review")) is str and
            len(dossier["effective_date_review"].strip())>=12,
            "P0C_EFFECTIVE_DATE_UNREVIEWED")
    return {"candidate_capture_sha256":sha256(raw),
            "verified_scope":False,"network_origin_attested":False}

def validate_strict_evidence(item,claim):
    if not claim["requires_external_verification"]:
        require(item["status"]=="NOT_REQUIRED_WITH_REASON" or
                bool(item.get("search_attempts")),
                "P0C_OPTIONAL_EVIDENCE_NOT_EXPLAINED")
        return
    attempts=item.get("search_attempts")
    require(type(attempts) is list and bool(attempts),
            "P0C_MANDATORY_SEARCH_ATTEMPT_RECEIPT")
    for attempt in attempts:
        require(type(attempt) is dict and type(attempt.get("query")) is str and
                len(attempt["query"].strip())>=8 and
                type(attempt.get("outcome")) is str and
                len(attempt["outcome"].strip())>=8,
                "P0C_SEARCH_ATTEMPT_INVALID")
        _time(attempt.get("observed_at"))
    if item["status"]=="OFFICIAL_CANDIDATE_APPLICABILITY_OPEN":
        validate_official_capture(item.get("official_capture"))
    else:
        require(item["status"] in {"OPEN_SOURCE","OPEN_PERSONAL_DATA","OPEN_ASSUMPTION"},
                "P0C_EVIDENCE_DISPOSITION_INVALID")
        require(item.get("official_capture") is None,
                "P0C_OFFICIAL_CAPTURE_MUST_HAVE_CANDIDATE_STATUS")
        require(type(item.get("not_verified_explanation")) is str and
                len(item["not_verified_explanation"].strip())>=12,
                "P0C_OPEN_SOURCE_REASON_MISSING")

def validate_strict_relation(item,expected_prior_blob):
    p=item.get("prior_lookup")
    require(type(p) is dict and p.get("schema")=="IRE_V5_P0C_PRIOR_LOOKUP_V1",
            "P0C_PRIOR_LOOKUP_SCHEMA_INVALID")
    require(p.get("prior_git_blob_sha")==expected_prior_blob,
            "P0C_PRIOR_LOOKUP_BLOB_MISMATCH")
    require(type(p.get("source_path")) is str and p["source_path"].startswith("data/"),
            "P0C_PRIOR_SOURCE_PATH_UNVERIFIED")
    require(type(p.get("review_excerpt")) is str and
            len(p["review_excerpt"].strip())>=12 and
            type(p.get("relationship_reason")) is str and
            len(p["relationship_reason"].strip())>=14,
            "P0C_PRIOR_RELATION_CONTEXT_MISSING")
    require(p.get("old_claims_autopromoted") is False and
            p.get("financial_fact_approved") is False,
            "P0C_PRIOR_AUTOMERGE_DENIED")
