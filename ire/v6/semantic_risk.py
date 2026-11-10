"""V6 P0-2 conservative semantic-risk triage on pinned original cues.

This is an independent *challenge list*, not an entailment model. A source
phrase may belong to a different speaker or topic; every flag requires human
judgment. Invalid calendar dates are structural failures. The docket only
contains original-bound indices, SHA identifiers and reason codes.
"""
from __future__ import annotations

import hashlib
import re
from datetime import date

from .atomic_exchange import audit_host_atomic_exchange
from .codec import canonical, sha256
from .errors import InvalidInput

NEGATION = re.compile(r"아닙니다|아니라|아니다|안\s*됩니다|불가능|잘못|틀렸|정정|반대|"
                      r"그러나|하지만|그렇지\s*않|not\s+true|instead|incorrect", re.I)
CONDITION = re.compile(r"만약|경우|때에만|한다면|라면|조건|해당되는\s*경우|"
                       r"제한적|if\s+|only\s+if|provided\s+that", re.I)
EXCEPTION = re.compile(r"다만|제외|예외|별도로|그럼에도|단,\s*|"
                       r"except|unless|exception", re.I)
QUOTATION = re.compile(r"질문|댓글|인용|누가\s*말|어떤\s*분|"
                       r"asked|quote|questioner", re.I)
CORRECTION = re.compile(r"정정|틀렸|잘못|취소|아니다|아닙니다|반대로|"
                        r"correction|incorrect", re.I)
ANNUAL = re.compile(r"연간|매년|연\s*[0-9]|연\s*[0-9]+%|annual|per\s+year", re.I)
MONTHLY = re.compile(r"월간|매월|월\s*[0-9]|월\s*[0-9]+%|monthly|per\s+month", re.I)

REASONS = (
    "SOURCE_NEGATION_POLARITY_REVIEW",
    "UNMAPPED_CONDITION_IN_MODEL_CONTEXT",
    "UNMAPPED_EXCEPTION_IN_MODEL_CONTEXT",
    "NEARBY_CORRECTION_NOT_IN_CONTEXT",
    "QUESTION_OR_QUOTATION_SPEAKER_REVIEW",
    "NUMERIC_ANNUAL_MONTHLY_SCOPE_REVIEW",
    "CONFLICTING_STANCES_ON_SAME_SOURCE_CUE",
)


def _digest_rows(rows):
    digest = hashlib.sha256(b"[")
    for index, row in enumerate(rows):
        if index:
            digest.update(b",")
        digest.update(canonical(row))
    digest.update(b"]")
    return digest.hexdigest()


def audit_semantic_risks(source, exchange):
    """Check source-first semantic hazards; never certify an answer.

    Raises for *impossible* date frames, not subjective lexical disagreement.
    All other cases are non-blocking review duties, not verified mistakes.
    """
    validated = audit_host_atomic_exchange(source, exchange)
    first, last = source.scope_first_cue, source.scope_last_cue
    claims = exchange["atoms"]
    cases, seen = [], set()

    def add(reason, cue_index, claim_id=None):
        identity = (reason, cue_index, claim_id)
        if identity in seen:
            return
        if len(cases) >= 100000:
            raise InvalidInput("SEMANTIC_RISK_CASE_LIMIT")
        seen.add(identity)
        record = {"reason": reason, "cue_index": cue_index, "claim_id": claim_id}
        cases.append({"case_sha256": sha256(canonical({
            "source_sha256": source.source_sha256,
            "manifest_sha256": source.manifest_sha256, **record
        })), **record})

    def cue(i):
        return source.cues[i - 1].text

    by_ref = {}
    for atom in claims:
        cid = atom["claim_id"]
        if atom["as_of"] is not None:
            try:
                date.fromisoformat(atom["as_of"])
            except (ValueError, TypeError) as exc:
                raise InvalidInput("SEMANTIC_RISK_INVALID_REAL_CALENDAR_DATE") from exc
        anchors = [x["cue_index"] for x in atom["source_refs"]]
        context = set(atom["context_cue_indices"])
        cond = set(atom["condition_cue_indices"])
        exceptions = set(atom["exception_cue_indices"])
        for i in anchors:
            by_ref.setdefault(i, []).append((cid, atom["stance"]))
        for i in sorted(context):
            text = cue(i)
            if CONDITION.search(text) and i not in cond:
                add("UNMAPPED_CONDITION_IN_MODEL_CONTEXT", i, cid)
            if EXCEPTION.search(text) and i not in exceptions:
                add("UNMAPPED_EXCEPTION_IN_MODEL_CONTEXT", i, cid)
        for i in anchors:
            text = cue(i)
            if NEGATION.search(text) and atom["stance"] not in {
                "NEGATED", "CORRECTED", "QUOTED", "UNRESOLVED"
            }:
                add("SOURCE_NEGATION_POLARITY_REVIEW", i, cid)
            if QUOTATION.search(text) and atom["speaker"] == "NARRATOR":
                add("QUESTION_OR_QUOTATION_SPEAKER_REVIEW", i, cid)
            # These are hints, not semantic conclusions: "연" inside "연금"
            # cannot count as an annual return reference.
            source_annual, source_monthly = bool(ANNUAL.search(text)), bool(MONTHLY.search(text))
            predicted_annual = bool(ANNUAL.search(atom["proposition"]))
            predicted_monthly = bool(MONTHLY.search(atom["proposition"]))
            if ((source_annual and predicted_monthly and not source_monthly)
                    or (source_monthly and predicted_annual and not source_annual)):
                add("NUMERIC_ANNUAL_MONTHLY_SCOPE_REVIEW", i, cid)
            for neighbor in (i - 2, i - 1, i + 1, i + 2):
                if (first <= neighbor <= last and neighbor not in context
                        and CORRECTION.search(cue(neighbor))):
                    add("NEARBY_CORRECTION_NOT_IN_CONTEXT", neighbor, cid)

    for i, overlaps in by_ref.items():
        stances = {stance for _, stance in overlaps}
        if len(overlaps) >= 2 and "AFFIRMED" in stances and (
            "NEGATED" in stances or "CORRECTED" in stances):
            add("CONFLICTING_STANCES_ON_SAME_SOURCE_CUE", i)

    cases.sort(key=lambda c: (c["cue_index"], c["reason"], c["claim_id"] or ""))
    counts = {reason: 0 for reason in REASONS}
    for item in cases:
        counts[item["reason"]] += 1
    if len(cases) != len({c["case_sha256"] for c in cases}):
        raise InvalidInput("SEMANTIC_RISK_DUPLICATE_CASE")
    return {
        "schema": "IRE_V6_SOURCE_SEMANTIC_RISK_REVIEW_V1",
        "source_sha256": source.source_sha256,
        "manifest_sha256": source.manifest_sha256,
        "atom_candidate_digest": validated["atom_candidate_digest"],
        "cue_disposition_digest": validated["cue_disposition_digest"],
        "scoped_cue_count": validated["original_scoped_cues_enumerated"],
        "model_claim_count": validated["proposed_atomic_claims"],
        "review_cases": cases,
        "review_case_count": len(cases),
        "cases_by_reason": counts,
        "case_census_sha256": _digest_rows(cases),
        "semantic_entailment_independently_verified": False,
        "independent_human_review_complete": False,
        "financial_law_as_of_verified": False,
        "missed_claim_recall_measured": False,
        "research_complete": False,
        "p0_go": False,
        "status": "SOURCE_FIRST_SEMANTIC_RISKS_PENDING_HUMAN_REVIEW",
    }
