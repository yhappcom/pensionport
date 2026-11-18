"""V167: source-pinned research orchestration for an in-chat ChatGPT reviewer.

This module prepares a full original-video OPEN docket, passes its cases to
explicit search and ChatGPT callbacks, and validates proposed dispositions.
Neither callback is supplied by Python: without a model API, the chat host
MUST perform those operations. Proposals do NOT modify V123, release E4, or
write V126/V128. Authenticated legal/issuer checking remains E4's duty.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from urllib.parse import urlsplit

from v166_e4_full_video_readiness import audit_video_readiness, digest, h

SCHEMA = "IRE_V167_SOURCE_PINNED_OPEN_RESEARCH_DOCKET_V1"
PROPOSAL_SCHEMA = "IRE_V167_UNRELEASED_CHAT_RESEARCH_PROPOSALS_V1"
DECISIONS = {"CANDIDATE_NEEDS_NATIVE_REVIEW", "KEEP_OPEN", "QUARANTINE_PROPOSAL", "REJECT_PROPOSAL"}


def _need(value, reason):
    if not value:
        raise ValueError("V167_RESEARCH_" + reason)


def _date(x):
    _need(type(x) is str and len(x) == 10, "AS_OF_REQUIRED")
    try:
        _need(date.fromisoformat(x).isoformat() == x, "AS_OF_INVALID")
    except ValueError as exc:
        raise ValueError("V167_RESEARCH_AS_OF_INVALID") from exc


def prepare_open_docket(raw, cues, segments, *, expected_source_sha256, as_of):
    """Inspect every actual source cue and atom without revising verdicts.

    The underlying E4 census checks all original SRT bytes, segment coverage,
    host/review digests, per-atom hashes, original quotes, and no cross-scope
    duplicates. Only the existing OPENs become review tasks.
    """
    _date(as_of)
    audit = audit_video_readiness(raw, cues, segments,
                                  expected_source_sha256=expected_source_sha256)
    items = []
    for segment in segments:
        scope = segment["segment_id"]
        original = segment["review"]
        atoms = {a["claim_id"]: a for a in segment["exchange"]["atoms"]}
        review_sha = digest(original)
        for verdict in original["atom_verdicts"]:
            if verdict["status"] != "OPEN":
                continue
            atom = atoms[verdict["claim_id"]]
            context = atom["context_cue_indices"]
            item = {
                "segment_id": scope,
                "claim_id": verdict["claim_id"],
                "atom_sha256": digest(atom),
                "prior_review_sha256": review_sha,
                "prior_verdict": "OPEN",
                "high_risk": verdict["high_risk"],
                "kind": atom.get("kind"),
                "source_refs": atom["source_refs"],
                "source_context": [{"cue_index": idx, "text": cues[idx]}
                                   for idx in context],
                "condition_cue_indices": atom.get("condition_cue_indices", []),
                "exception_cue_indices": atom.get("exception_cue_indices", []),
                "numeric_references": atom.get("numeric_references", []),
                "original_proposition": atom.get("proposition"),
                "as_of": as_of,
                "candidate_is_not_approved_knowledge": True,
            }
            _need(type(item["high_risk"]) is bool, "HIGH_RISK_BOOL")
            items.append(item)
    items.sort(key=lambda x: (not x["high_risk"], x["segment_id"], x["claim_id"]))
    _need(len(items) == audit["totals"]["open_atom_count"], "OPEN_CENSUS_DRIFT")
    _need(len({x["claim_id"] for x in items}) == len(items), "DUPLICATE_CLAIM")
    core = {
        "schema": SCHEMA,
        "owner_source_sha256": audit["owner_source_sha256"],
        "as_of": as_of,
        "original_segment_count": audit["segment_count"],
        "original_atom_count": audit["distinct_claim_count"],
        "original_open_count": len(items),
        "original_high_risk_open_count": sum(x["high_risk"] for x in items),
        "items": items,
        "v123_status_changed": False,
        "e4_approved": False,
        "e5_authorized": False,
    }
    return {**core, "docket_sha256": digest(core)}


def _evidence_summary(rows):
    """Check callback-provided content, but NEVER attest the provider/origin.

    E4 must re-fetch allowlisted HTTPS origins and check actual legal scope.
    """
    _need(type(rows) is list and len(rows) <= 12, "EVIDENCE_ROWS")
    out = []
    for row in rows:
        _need(type(row) is dict and set(row) == {
            "url", "body", "excerpt", "source_label", "retrieved_as_of"},
            "EVIDENCE_SCHEMA")
        url = row["url"]
        _need(type(url) is str and len(url) <= 1500, "EVIDENCE_URL")
        p = urlsplit(url)
        _need(p.scheme == "https" and bool(p.hostname)
              and p.username is None and p.password is None
              and p.port in (None, 443) and not p.fragment,
              "EVIDENCE_UNTRUSTED_SCHEME")
        body = row["body"]
        excerpt = row["excerpt"]
        _need(type(body) is bytes and 20 <= len(body) <= 4 * 1024 * 1024,
              "EVIDENCE_BODY")
        _need(type(excerpt) is str and len(excerpt.strip()) >= 10
              and excerpt.encode("utf-8") in body,
              "EVIDENCE_QUOTE_NOT_IN_BYTES")
        _need(type(row["source_label"]) is str and bool(row["source_label"].strip()),
              "EVIDENCE_SOURCE_LABEL")
        _date(row["retrieved_as_of"])
        out.append({
            "url": url,
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "excerpt": excerpt,
            "excerpt_sha256": hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
            "source_label": row["source_label"],
            "retrieved_as_of": row["retrieved_as_of"],
            "provenance_authenticated": False,
            "finance_rule_applicability_verified": False,
        })
    return out


def execute_chat_review_round(docket, *, evidence_retriever, chat_reviewer,
                              limit=None, start_after=None):
    """Synchronous host-adapter call: retrieve -> ChatGPT -> validate -> HOLD.

    The callbacks MUST be supplied by the live chat host. Test doubles prove
    only protocol integrity. No LLM API is hidden here, no web origin is
    authenticated here, and a proposal cannot be used as an E4 release token.
    """
    _need(type(docket) is dict and docket.get("schema") == SCHEMA,
          "DOCKET_SCHEMA")
    core = {k: v for k, v in docket.items() if k != "docket_sha256"}
    _need(docket.get("docket_sha256") == digest(core), "DOCKET_DRIFT")
    _need(core.get("v123_status_changed") is False
          and core.get("e4_approved") is False
          and core.get("e5_authorized") is False, "RELEASE_BYPASS")
    items = docket["items"]
    _need(type(items) is list and len(items) == docket["original_open_count"]
          and sum(type(x.get("high_risk")) is bool and x["high_risk"]
                  for x in items) == docket["original_high_risk_open_count"],
          "WORK_QUEUE_CENSUS")
    _need(len({x["claim_id"] for x in items}) == len(items), "WORK_QUEUE_DUPLICATE")
    _need(callable(evidence_retriever) and callable(chat_reviewer),
          "CHAT_HOST_CALLBACK_REQUIRED")
    _need(limit is None or (type(limit) is int and limit >= 1), "LIMIT")
    if start_after is None:
        offset = 0
    else:
        _need(type(start_after) is str and
              start_after in {x["claim_id"] for x in items},
              "START_AFTER_NOT_IN_DOCKET")
        offset = next(i for i, x in enumerate(items)
                      if x["claim_id"] == start_after) + 1
    selected = items[offset:] if limit is None else items[offset:offset+limit]
    proposed = []
    for task in selected:
        evidence = _evidence_summary(evidence_retriever(task))
        request = {
            "docket_sha256": docket["docket_sha256"],
            "owner_source_sha256": docket["owner_source_sha256"],
            "task": task,
            "evidence": evidence,
            "source_provenance_and_statutory_scope_not_yet_authenticated": True,
        }
        request_hash = digest(request)
        verdict = chat_reviewer({**request, "request_sha256": request_hash})
        _need(type(verdict) is dict and set(verdict) == {
            "claim_id", "atom_sha256", "request_sha256", "decision",
            "reason", "conditions_checked", "exceptions_checked",
            "numbers_and_period_checked", "counterarguments_checked",
            "chat_reviewer_identity_attested", "financial_fact_certified",
            "personal_advice_approved"}, "CHAT_DECISION_SCHEMA")
        _need(verdict["claim_id"] == task["claim_id"]
              and verdict["atom_sha256"] == task["atom_sha256"]
              and verdict["request_sha256"] == request_hash,
              "CHAT_DECISION_PIN_MISMATCH")
        _need(verdict["decision"] in DECISIONS and type(verdict["reason"]) is str
              and len(verdict["reason"].strip()) >= 30,
              "DECISION_OR_EXPLANATION_REQUIRED")
        _need(all(verdict[k] is True for k in (
            "conditions_checked", "exceptions_checked", "numbers_and_period_checked",
            "counterarguments_checked")) and
              verdict["chat_reviewer_identity_attested"] is False and
              verdict["financial_fact_certified"] is False and
              verdict["personal_advice_approved"] is False,
              "CHAT_SEMANTIC_OR_AUTHORITY_NOT_SAFE")
        _need(verdict["decision"] != "CANDIDATE_NEEDS_NATIVE_REVIEW" or evidence,
              "CANDIDATE_WITHOUT_SOURCE")
        proposed.append({
            "segment_id": task["segment_id"],
            "claim_id": task["claim_id"],
            "prior_status": "OPEN",
            "proposed_decision": verdict["decision"],
            "atom_sha256": task["atom_sha256"],
            "prior_review_sha256": task["prior_review_sha256"],
            "request_sha256": request_hash,
            "chat_decision_sha256": digest(verdict),
            "chat_reason": verdict["reason"],
            "source_evidence": evidence,
            "applied_to_native_v123": False,
            "approved_by_e4": False,
            "knowledge_released": False,
        })
    result = {
        "schema": PROPOSAL_SCHEMA,
        "owner_source_sha256": docket["owner_source_sha256"],
        "docket_sha256": docket["docket_sha256"],
        "original_open_count": docket["original_open_count"],
        "proposals_created": len(proposed),
        "unprocessed_open_count": len(items) - len(proposed),
        "candidate_proposals": sum(x["proposed_decision"] == "CANDIDATE_NEEDS_NATIVE_REVIEW" for x in proposed),
        "proposed_quarantines": sum(x["proposed_decision"] == "QUARANTINE_PROPOSAL" for x in proposed),
        "proposals": proposed,
        "review_executor_claimed_not_cryptographically_authenticated": True,
        "evidence_origin_not_authenticated_by_this_module": True,
        "native_v123_replay_required": True,
        "formal_e4_primary_and_scope_review_required": True,
        "native_v123_status_changed": False,
        "knowledge_publication_authorized": False,
        "e5_authorized": False,
    }
    return {**result, "proposal_receipt_sha256": digest(result)}