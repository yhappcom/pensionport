"""V145 source-only pending-cue escrow for host batch, NOT claim approval.

The native V6 host may write *structural* model/proof evidence even if some
source cues remain explicitly unresolved, but ONLY when every unresolved or
lexically suspicious unclaimed cue is present in a source-SHA-bound private
ChatGPT preflight ledger. V123 must subsequently exclude these exact source
cues and all dependent atoms before allowing any approved research candidate.
No official financial fact, audio fidelity, gold recall or P0 GO is certified.
"""
from __future__ import annotations
from .claim_census import FINANCIAL, QUALIFIER, MULTI_CLAIM
from .codec import require_hash, json_digest, sha256
from .errors import InvalidInput, QualityNotProven

_REASONS = frozenset({"ASR_ORIGINAL_UNVERIFIED", "FINANCIAL_CONTEXT_UNRESOLVED",
                      "SPEAKER_OR_QUESTION_AMBIGUOUS", "NUMERIC_OR_UNIT_AMBIGUOUS",
                      "OTHER_SOURCE_FIRST_RISK"})


def audit_host_quarantine_preflight(source, exchange, ledger):
    rows = exchange["cue_dispositions"]
    mandatory = []
    for row in rows:
        idx = row["cue_index"]
        body = source.cues[idx - 1].text
        risky = bool(FINANCIAL.search(body) or QUALIFIER.search(body) or
                     MULTI_CLAIM.search(body))
        if row["disposition"] == "UNRESOLVED" or (
                row["disposition"] == "NO_ATOM" and risky):
            mandatory.append(idx)
    if not mandatory:
        if ledger is not None:
            raise InvalidInput("HOST_PREQUARANTINE_UNEXPECTED_WHEN_NO_RESIDUAL")
        return None
    if ledger is None:
        raise QualityNotProven("HOST_BATCH_UNRESOLVED_SOURCE_RESIDUALS")
    required = {"schema", "source_sha256", "manifest_sha256", "review_executor",
                "private_review_sha256", "cue_rows", "audio_authenticity_verified",
                "semantic_claims_independently_verified", "p0_go"}
    if (type(ledger) is not dict or set(ledger) != required or
        ledger["schema"] != "IRE_V6_HOST_SOURCE_PREQUARANTINE_V145" or
        ledger["source_sha256"] != source.source_sha256 or
        ledger["manifest_sha256"] != source.manifest_sha256 or
        ledger["review_executor"] != "CHATGPT_IN_CHAT" or
        ledger["audio_authenticity_verified"] is not False or
        ledger["semantic_claims_independently_verified"] is not False or
        ledger["p0_go"] is not False or
        type(ledger["cue_rows"]) is not list):
        raise InvalidInput("HOST_PREQUARANTINE_SOURCE_OR_AUTHORITY_INVALID")
    require_hash(ledger["private_review_sha256"],"HOST_PREQUARANTINE_CHAT_NOTE")
    checks = []
    for row in ledger["cue_rows"]:
        if (type(row) is not dict or set(row) != {
            "cue_index", "cue_text_sha256", "reason_code",
            "private_chat_cue_review_sha256", "source_first_context_reviewed"}):
            raise InvalidInput("HOST_PREQUARANTINE_ROW_SCHEMA")
        idx = row["cue_index"]
        if (type(idx) is not int or idx not in mandatory or
            row["cue_text_sha256"] != sha256(source.cues[idx-1].text.encode("utf-8")) or
            row["reason_code"] not in _REASONS or
            row["source_first_context_reviewed"] is not True):
            raise InvalidInput("HOST_PREQUARANTINE_CUE_MISSING_OR_DRIFT")
        require_hash(row["private_chat_cue_review_sha256"],"HOST_PREQUARANTINE_CUE_NOTE")
        checks.append(idx)
    if checks != mandatory or len(checks) != len(set(checks)):
        raise QualityNotProven("HOST_PREQUARANTINE_CUE_CENSUS_NOT_EXACT")
    return {
        "schema":"IRE_V6_HOST_SOURCE_PREQUARANTINE_RECEIPT_V145",
        "source_sha256":source.source_sha256,
        "manifest_sha256":source.manifest_sha256,
        "preflight_ledger_sha256":json_digest(ledger),
        "unresolved_original_cue_count":len(checks),
        "unresolved_original_cue_indices":checks,
        "host_structural_staging_only":True,
        "original_audio_authenticated":False,
        "all_claim_semantics_approved":False,
        "p0_go":False,
    }
