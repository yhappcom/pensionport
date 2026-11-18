"""V170: explicit two-phase in-chat review transport with no model/API calls.

A live ChatGPT conversation reads a source-pinned batch request, adjudicates
its atom/source/evidence content, and supplies literal decision rows.  Python
validates and atomically persists *unreleased* proposals using V169's durable
journal.  No callback to a model is hidden in this module; the `chat_reviewer`
closure in V169 is only a transport for supplied (not generated) decisions.

Caution: the "ChatGPT" authorship of the returned JSON is a host claim, not
cryptographically verifiable. Search hits are untrusted text and are NEVER
proof of legal authority. Frozen V123 and E4 must be run separately.
"""
from __future__ import annotations

import copy
from v166_e4_full_video_readiness import digest
from v167_chat_research_loop import _evidence_summary
from v169_chat_research_journal import ChatReviewJournal

SCHEMA = "IRE_V170_SOURCE_PINNED_LIVE_CHAT_REVIEW_BATCH_V1"
REQUEST_SCHEMA = "IRE_V170_LIVE_CHAT_MEANING_REQUEST_V1"


def _need(ok, code):
    if not ok:
        raise ValueError("V170_CHAT_BRIDGE_" + code)


def _receipt_head(journal):
    _need(isinstance(journal, ChatReviewJournal), "PRIVATE_JOURNAL_REQUIRED")
    return journal.status()


def prepare_chat_batch(journal, *, evidence_by_claim, limit=8):
    """Return prompts/verified byte-excerpts ready for THIS chat to evaluate.

    Evidence input is mapping claim_id -> list of V167 evidence rows containing
    HTTPS URL, original response bytes, verbatim excerpt, source name, as-of.
    This transport checks only byte-consistency; it never attests TLS origin.

    The output carries sensitive source speech; never place it in public Git.
    """
    _need(type(limit) is int and 1 <= limit <= 100, "INVALID_LIMIT")
    _need(type(evidence_by_claim) is dict, "EVIDENCE_MAP_REQUIRED")
    snap = _receipt_head(journal)
    tasks = journal.next_tasks(limit)
    expected_ids = {item["claim_id"] for item in tasks}
    _need(set(evidence_by_claim) == expected_ids, "EVIDENCE_EXACT_TASK_CENSUS")
    prompts = []
    for task in tasks:
        source_rows = evidence_by_claim[task["claim_id"]]
        evidence = _evidence_summary(source_rows)
        # Identical to V167.execute_chat_review_round's reviewer request.
        request = {
            "docket_sha256": journal.docket["docket_sha256"],
            "owner_source_sha256": journal.docket["owner_source_sha256"],
            "task": task,
            "evidence": evidence,
            "source_provenance_and_statutory_scope_not_yet_authenticated": True,
        }
        prompts.append({**request, "request_sha256": digest(request)})
    core = {
        "schema": SCHEMA,
        "request_schema": REQUEST_SCHEMA,
        "root_docket_sha256": journal.docket["docket_sha256"],
        "owner_source_sha256": journal.docket["owner_source_sha256"],
        "previous_journal_head_sha256": snap["journal_head_sha256"],
        "previous_processed_count": snap["processed_count"],
        "total_open_count": snap["original_open_count"],
        "requests": prompts,
        "evidence_origin_and_chat_identity_not_attested": True,
        "frozen_v123_native_review_not_yet_run": True,
        "e4_approved": False,
        "e5_authorized": False,
    }
    return {**core, "batch_sha256": digest(core)}


def ingest_chat_responses(journal, *, prepared_batch, evidence_by_claim,
                          chat_responses):
    """Ingest literal ChatGPT-written answers with an atomic V169 journal write.

    Must happen within the live ChatGPT tool-mediated turn (or its authorised
    resume turn) after the model actually reviews every original source/context
    and counterexample. An in-memory Python predicate is NOT a ChatGPT review.
    Rejects stale batches before calling journal.run_round, and rechecks each
    actual request hash inside the V167 native proposal validator.
    """
    _need(type(prepared_batch) is dict and
          prepared_batch.get("schema") == SCHEMA and
          prepared_batch.get("batch_sha256") == digest({
              k: v for k, v in prepared_batch.items() if k != "batch_sha256"}),
          "REVIEW_BATCH_TAMPERED")
    _need(prepared_batch.get("e4_approved") is False and
          prepared_batch.get("e5_authorized") is False and
          prepared_batch.get("evidence_origin_and_chat_identity_not_attested") is True,
          "RELEASE_FLAG_TAMPERED")
    _need(type(chat_responses) is list, "CHAT_RESPONSE_LIST_REQUIRED")
    requests = prepared_batch.get("requests")
    _need(type(requests) is list and requests, "NO_REVIEW_TASKS_TO_INGEST")
    ids = [r.get("task", {}).get("claim_id") for r in requests]
    _need(len(ids) == len(set(ids)) and
          len(ids) == len(chat_responses) and
          all(type(item) is dict for item in chat_responses) and
          [r.get("claim_id") for r in chat_responses] == ids,
          "ANSWER_ORDER_OR_CENSUS_MISMATCH")
    # The durable cursor is checked *before* consulting evidence. A stale
    # response must be rejected as a replay, not misreported as missing
    # evidence for a now-different next task.
    current = _receipt_head(journal)
    _need(prepared_batch.get("root_docket_sha256") ==
          journal.docket["docket_sha256"] and
          prepared_batch.get("owner_source_sha256") ==
          journal.docket["owner_source_sha256"] and
          prepared_batch.get("previous_journal_head_sha256") ==
          current["journal_head_sha256"] and
          prepared_batch.get("previous_processed_count") ==
          current["processed_count"],
          "STALE_OR_CHANGED_REVIEW_CONTEXT")
    # Restore exact batch using unchanged original bytes and the live cursor.
    # Any source/evidence/journal/head drift is a failure, not a silent replay.
    reconstructed = prepare_chat_batch(journal, evidence_by_claim=evidence_by_claim,
                                       limit=len(requests))
    _need(reconstructed == prepared_batch, "STALE_OR_CHANGED_REVIEW_CONTEXT")
    responses = {r["claim_id"]: copy.deepcopy(r) for r in chat_responses}
    expected = {r["task"]["claim_id"]: r for r in requests}

    def evidence_for_task(task):
        return evidence_by_claim[task["claim_id"]]

    def literal_chat_answer(actual_request):
        cid = actual_request["task"]["claim_id"]
        _need(actual_request == expected[cid], "EVIDENCE_OR_REQUEST_DRIFT")
        return copy.deepcopy(responses[cid])

    written = journal.run_round(evidence_retriever=evidence_for_task,
                               chat_reviewer=literal_chat_answer,
                               limit=len(requests))
    _need(written["processed_count"] ==
          prepared_batch["previous_processed_count"] + len(requests),
          "DURABLE_WRITE_COUNT_DRIFT")
    return {
        "schema": "IRE_V170_LIVE_CHAT_DURABLE_UNRELEASED_RECEIPT_V1",
        "root_docket_sha256": journal.docket["docket_sha256"],
        "owner_source_sha256": journal.docket["owner_source_sha256"],
        "ingested_batch_sha256": prepared_batch["batch_sha256"],
        "journal_head_sha256": written["journal_head_sha256"],
        "processed_count": written["processed_count"],
        "remaining_count": written["remaining_count"],
        "ingested_count": len(requests),
        "chat_authorship_not_cryptographically_proven": True,
        "native_v123_replay_required": True,
        "e4_approved": False,
        "e5_authorized": False,
        "knowledge_publication_authorized": False,
    }