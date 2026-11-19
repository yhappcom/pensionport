"""V171: no-API, two-call current-chat evidence revisit for V170 KEEP_OPEN.

Prepare reveals original claim+context, *only the evidence excerpt* and exact
source/evidence hashes. A subsequent host invocation supplies the actual
reviewer's verdict, never fabricated by Python. The private raw evidence is
not uploaded and publisher origin is NOT certified by this protocol.

This adapter is an append-only *research proposal* step. It cannot update
V123, sign E4, clear thirteen HOLD segments or publish E5/V128 knowledge.
"""
from __future__ import annotations

import copy
import json
from contextlib import closing
from dataclasses import dataclass

from v166_e4_full_video_readiness import digest
from v167_chat_research_loop import _evidence_summary
from v170_evidence_revisit import EvidenceRevisitJournal

SCHEMA = "IRE_V171_IN_CHAT_REVISIT_CHALLENGE_V1"
RECEIPT = "IRE_V171_IN_CHAT_REVISIT_COMMIT_RECEIPT_V1"


def _need(ok, code):
    if not ok:
        raise ValueError("V171_CHAT_REVISIT_" + code)


@dataclass(frozen=True)
class PreparedRevisit:
    """Entire object is PRIVATE: `challenge` alone may cross chat boundary."""
    challenge: dict
    raw_evidence: list


def _snapshot(revisits, claim_id):
    initial, tasks, base = revisits._base()
    _need(claim_id in base, "ONLY_PREVIOUSLY_RESEARCHED")
    with closing(revisits.journal._connect()) as con:
        effective, revisit_head, event_count = revisits._read(con, tasks, base)
        all_receipts = con.execute(
            "SELECT claim_id, proposal_json FROM revisit_receipts ORDER BY seq"
        ).fetchall()
    proposal = effective[claim_id]
    _need(proposal["proposed_decision"] == "KEEP_OPEN", "NOT_STILL_OPEN")
    seen = {r["body_sha256"] for r in base[claim_id]["source_evidence"]}
    for cid, raw_json in all_receipts:
        if cid == claim_id:
            seen.update(row["body_sha256"] for row in
                        json.loads(raw_json)["source_evidence"])
    status = revisits.journal.status()
    return {
        "docket_sha256": revisits.journal.docket["docket_sha256"],
        "owner_source_sha256": revisits.journal.docket["owner_source_sha256"],
        "first_pass_head": status["journal_head_sha256"],
        "initial_proposal_sha": digest(base[claim_id]),
        "effective_proposal_sha": digest(proposal),
        "revisit_head": revisit_head,
        "revisit_event_count": event_count,
        "seen_body_sha256": sorted(seen),
        "task": tasks[claim_id],
    }


def prepare_revisit_chat_turn(revisits: EvidenceRevisitJournal, claim_id: str,
                              *, evidence_retriever) -> PreparedRevisit:
    """Prepare a genuine, unreviewed new-evidence request without DB writes."""
    _need(isinstance(revisits, EvidenceRevisitJournal), "PRIVATE_REVISIT_JOURNAL")
    _need(type(claim_id) is str and bool(claim_id), "CLAIM_ID")
    _need(callable(evidence_retriever), "EVIDENCE_HOST_CALLBACK")
    snap = _snapshot(revisits, claim_id)
    rows = evidence_retriever(copy.deepcopy(snap["task"]))
    evidence = _evidence_summary(rows)
    _need(any(e["body_sha256"] not in snap["seen_body_sha256"] for e in evidence),
          "NO_PREVIOUSLY_UNSEEN_EVIDENCE_BODY")
    req = {
        "docket_sha256": snap["docket_sha256"],
        "owner_source_sha256": snap["owner_source_sha256"],
        "task": snap["task"],
        "evidence": evidence,
        "source_provenance_and_statutory_scope_not_yet_authenticated": True,
    }
    request = {**req, "request_sha256": digest(req)}
    core = {
        "schema": SCHEMA,
        "claim_id": claim_id,
        "owner_source_sha256": snap["owner_source_sha256"],
        "docket_sha256": snap["docket_sha256"],
        "first_pass_head_sha256": snap["first_pass_head"],
        "original_proposal_sha256": snap["initial_proposal_sha"],
        "effective_proposal_sha256": snap["effective_proposal_sha"],
        "revisit_head_sha256": snap["revisit_head"],
        "revisit_event_count_before": snap["revisit_event_count"],
        "previous_evidence_body_sha256": snap["seen_body_sha256"],
        "request": request,
        "python_called_any_model": False,
        "cryptographic_chat_identity_confirmed": False,
        "evidence_issuer_identity_verified": False,
        "native_v123_approved": False,
        "e4_approved": False,
        "e5_authorized": False,
    }
    return PreparedRevisit({**core, "challenge_sha256": digest(core)},
                           copy.deepcopy(rows))


def commit_revisit_chat_turn(revisits: EvidenceRevisitJournal,
                             prepared: PreparedRevisit, reviewer_response: dict):
    """Consume ONE current-chat verdict, preserving an append-only proposal log.

    Missing, swapped, stale, altered evidence/first-pass journal, or unverified
    semantic fields fail before the V170 atomic commit. V170/V167 validates all
    mandated fields/booleans; no defaults are generated for the chat reviewer.
    """
    _need(isinstance(revisits, EvidenceRevisitJournal)
          and isinstance(prepared, PreparedRevisit), "PRIVATE_REVIEW_INPUT")
    c = prepared.challenge
    _need(type(c) is dict and c.get("schema") == SCHEMA and
          c.get("challenge_sha256") == digest({k: v for k, v in c.items()
                                                 if k != "challenge_sha256"}),
          "CHALLENGE_TAMPERED")
    _need(all(c.get(k) is False for k in (
        "python_called_any_model", "cryptographic_chat_identity_confirmed",
        "evidence_issuer_identity_verified", "native_v123_approved",
        "e4_approved", "e5_authorized")), "FALSE_AUTHORITY")
    claim_id = c["claim_id"]
    snap = _snapshot(revisits, claim_id)
    _need((snap["docket_sha256"], snap["owner_source_sha256"],
           snap["first_pass_head"], snap["initial_proposal_sha"],
           snap["effective_proposal_sha"], snap["revisit_head"],
           snap["revisit_event_count"], snap["seen_body_sha256"]) ==
          (c["docket_sha256"], c["owner_source_sha256"],
           c["first_pass_head_sha256"], c["original_proposal_sha256"],
           c["effective_proposal_sha256"], c["revisit_head_sha256"],
           c["revisit_event_count_before"], c["previous_evidence_body_sha256"]),
          "STALE_SOURCE_OR_REVISIT_STATE")
    evidence = _evidence_summary(prepared.raw_evidence)
    req = {"docket_sha256": c["docket_sha256"],
           "owner_source_sha256": c["owner_source_sha256"],
           "task": snap["task"], "evidence": evidence,
           "source_provenance_and_statutory_scope_not_yet_authenticated": True}
    expected = {**req, "request_sha256": digest(req)}
    _need(c["request"] == expected, "REQUEST_OR_RAW_EVIDENCE_MUTATED")
    _need(type(reviewer_response) is dict and
          reviewer_response.get("claim_id") == claim_id and
          reviewer_response.get("atom_sha256") == snap["task"]["atom_sha256"] and
          reviewer_response.get("request_sha256") == expected["request_sha256"],
          "REVIEW_RESPONSE_WRONG_CLAIM_OR_REQUEST")
    # A normal callback would invoke a model, which is deliberately forbidden.
    # This callback only passes through an explicitly supplied chat-authored row.
    def retriever(live_task):
        _need(live_task == snap["task"], "SOURCE_TASK_CHANGED")
        return copy.deepcopy(prepared.raw_evidence)
    def passthrough(live_request):
        _need(live_request == expected, "EVIDENCE_REQUEST_CHANGED")
        return copy.deepcopy(reviewer_response)
    after = revisits.run_revisit(claim_id, evidence_retriever=retriever,
                                 chat_reviewer=passthrough)
    _need(after["revisit_events"] == snap["revisit_event_count"] + 1,
          "POST_COMMIT_EVENT_COUNT_DRIFT")
    core = {"schema": RECEIPT,
            "claim_id": claim_id,
            "owner_source_sha256": snap["owner_source_sha256"],
            "docket_sha256": snap["docket_sha256"],
            "request_sha256": expected["request_sha256"],
            "chat_verdict_sha256": digest(reviewer_response),
            "revisit_events_total": after["revisit_events"],
            "revisit_head_sha256": after["revisit_head_sha256"],
            "still_open_research_proposals": after["latest_still_open_count"],
            "candidates_needing_native_review": after["candidate_not_native_approved"],
            "never_researched_count": after["never_researched_count"],
            "native_v123_approved": False,
            "e4_approved": False,
            "e5_authorized": False,
            "knowledge_published": False}
    return {**core, "receipt_sha256": digest(core)}