"""V170: explicit no-API ChatGPT host boundary for V169 research journals.

The current chat model *reads* a prepared challenge and supplies the verdict
records in a separate tool invocation. Python neither invokes an LLM nor
pretends a `CHATGPT_IN_CHAT` label authenticates model identity. The source and
its exact evidence bytes stay in private process memory; public challenges
contain only the source text needed for review and evidence excerpts.

This is an input/output adapter and a durable unreleased-proposal writer. It
cannot authorize V123, E4 or E5 publication. A candidate requires a separately
authored V168 native secondary review, and E4 still re-fetches official bytes.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass

from v166_e4_full_video_readiness import digest
from v167_chat_research_loop import _evidence_summary
from v169_chat_research_journal import ChatReviewJournal

SCHEMA = "IRE_V170_ACTUAL_CHAT_BOUNDARY_CHALLENGE_V1"
RECEIPT = "IRE_V170_CHAT_BOUNDARY_COMMIT_RECEIPT_V1"


def _need(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError("V170_CHAT_BOUNDARY_" + code)


@dataclass(frozen=True)
class PreparedChatTurn:
    """Private in-process transport: keep raw evidence out of shared challenge.

    The entire object is PRIVATE and must not be sent to GitHub. Only
    `.challenge` should be shown to the in-chat reviewer. `raw_evidence` can
    contain authenticating bytes but the bridge does not establish origin.
    """
    challenge: dict
    raw_evidence: dict


def prepare_chat_turn(journal: ChatReviewJournal, *, evidence_retriever,
                      limit: int = 4) -> PreparedChatTurn:
    """Prepare next source-pinned tasks without consuming journal progress.

    A legitimate current-chat reviewer must inspect each request's original
    quoted context, conditions, exceptions and evidence, then provide its OWN
    decision rows. This function never constructs a reviewer response.
    """
    _need(isinstance(journal, ChatReviewJournal), "REAL_PRIVATE_JOURNAL_REQUIRED")
    _need(callable(evidence_retriever), "EVIDENCE_LOOKUP_REQUIRED")
    _need(type(limit) is int and 1 <= limit <= 30, "LIMIT")
    prior = journal.status()
    _need(prior["remaining_count"] > 0, "NO_UNREVIEWED_TASKS")
    tasks = journal.next_tasks(limit)
    _need(len(tasks) == min(limit, prior["remaining_count"]), "CURSOR_GAP")
    requests, raw_evidence = [], {}
    for task in tasks:
        cid = task["claim_id"]
        rows = evidence_retriever(copy.deepcopy(task))
        summaries = _evidence_summary(rows)
        request = {
            "docket_sha256": prior["root_docket_sha256"],
            "owner_source_sha256": prior["owner_source_sha256"],
            "task": task,
            "evidence": summaries,
            "source_provenance_and_statutory_scope_not_yet_authenticated": True,
        }
        requests.append({**request, "request_sha256": digest(request)})
        raw_evidence[cid] = copy.deepcopy(rows)
    core = {
        "schema": SCHEMA,
        "owner_source_sha256": prior["owner_source_sha256"],
        "docket_sha256": prior["root_docket_sha256"],
        "journal_head_sha256_before": prior["journal_head_sha256"],
        "processed_count_before": prior["processed_count"],
        "total_open_in_original_revision": prior["original_open_count"],
        "requests": requests,
        "python_called_any_model": False,
        "chat_model_identity_cryptographically_attested": False,
        "official_origin_authenticated_here": False,
        "v123_or_e4_approved": False,
        "e5_authorized": False,
    }
    public = {**core, "challenge_sha256": digest(core)}
    return PreparedChatTurn(challenge=public, raw_evidence=raw_evidence)


def commit_chat_turn(journal: ChatReviewJournal, prepared: PreparedChatTurn,
                     reviewer_responses: list) -> dict:
    """Consume explicit model-authored decisions, atomically or not at all.

    This is the SECOND tool call of a single ChatGPT turn. It does not infer
    model reasoning from the evidence, fill in absent flags, call any LLM or
    create secondary native V123 verdicts. Misordered/stale/swapped or omitted
    responses fail without any SQLite writes.
    """
    _need(isinstance(journal, ChatReviewJournal)
          and isinstance(prepared, PreparedChatTurn), "PRIVATE_HOST_BOUNDARY_REQUIRED")
    c = prepared.challenge
    _need(type(c) is dict and c.get("schema") == SCHEMA and
          c.get("challenge_sha256") == digest({
              k: v for k, v in c.items() if k != "challenge_sha256"}),
          "CHALLENGE_TAMPERED")
    _need(c.get("python_called_any_model") is False and
          c.get("chat_model_identity_cryptographically_attested") is False and
          c.get("official_origin_authenticated_here") is False and
          c.get("v123_or_e4_approved") is False and c.get("e5_authorized") is False,
          "FALSE_CHAT_OR_RELEASE_AUTHORITY")
    before = journal.status()
    _need((before["root_docket_sha256"],before["owner_source_sha256"],
           before["journal_head_sha256"],before["processed_count"],
           before["original_open_count"]) ==
          (c["docket_sha256"],c["owner_source_sha256"],
           c["journal_head_sha256_before"],c["processed_count_before"],
           c["total_open_in_original_revision"]),
          "STALE_OR_WRONG_OWNER_REVISION")
    reqs = c.get("requests")
    _need(type(reqs) is list and 1 <= len(reqs) <= 30 and
          type(reviewer_responses) is list and len(reviewer_responses) == len(reqs),
          "COMPLETE_CHAT_BATCH_REQUIRED")
    tasks = journal.next_tasks(len(reqs))
    _need([r.get("task") for r in reqs] == tasks,
          "TASK_ORDER_OR_CONTENT_CHANGED")
    _need(set(prepared.raw_evidence) == {t["claim_id"] for t in tasks},
          "PRIVATE_EVIDENCE_CENSUS")
    replies = {}
    for req, row in zip(reqs, reviewer_responses):
        cid = req["task"]["claim_id"]
        raw = prepared.raw_evidence[cid]
        expected = {
            "docket_sha256": c["docket_sha256"],
            "owner_source_sha256": c["owner_source_sha256"],
            "task": req["task"],
            "evidence": _evidence_summary(raw),
            "source_provenance_and_statutory_scope_not_yet_authenticated": True,
        }
        _need(req == {**expected, "request_sha256": digest(expected)},
              "EVIDENCE_BYTES_OR_REQUEST_TAMPERED")
        _need(type(row) is dict and row.get("claim_id") == cid and
              row.get("atom_sha256") == req["task"]["atom_sha256"] and
              row.get("request_sha256") == req["request_sha256"] and
              cid not in replies, "RESPONSE_ORDER_OR_SOURCE_PIN")
        replies[cid] = copy.deepcopy(row)
    # The V167 verifier validates *every* field/semantic-review boolean and
    # the V169 journal makes a complete-batch atomic SQLite commit.
    def retriever(task):
        return copy.deepcopy(prepared.raw_evidence[task["claim_id"]])
    def reviewer(live_request):
        cid = live_request["task"]["claim_id"]
        _need(live_request == reqs[[t["claim_id"] for t in tasks].index(cid)],
              "LIVE_REQUEST_CHANGED_AFTER_CHALLENGE")
        return copy.deepcopy(replies[cid])
    after = journal.run_round(evidence_retriever=retriever,
                              chat_reviewer=reviewer, limit=len(reqs))
    _need(after["processed_count"] == before["processed_count"]+len(reqs),
          "POST_COMMIT_PROGRESS_UNEXPECTED")
    # Merely processing a KEEP_OPEN is NOT semantic resolution. The journal
    # remains a source-pinned *proposal* log, not accepted knowledge.
    decisions = [row["decision"] for row in reviewer_responses]
    report = {
        "schema": RECEIPT,
        "owner_source_sha256": c["owner_source_sha256"],
        "docket_sha256": c["docket_sha256"],
        "challenge_sha256": c["challenge_sha256"],
        "reviewed_request_count": len(reqs),
        "processed_total": after["processed_count"],
        "initial_open_count": after["original_open_count"],
        "never_reviewed_count": after["remaining_count"],
        "still_open_in_this_batch": decisions.count("KEEP_OPEN"),
        "source_only_quarantine_proposals_not_final":
            decisions.count("QUARANTINE_PROPOSAL"),
        "candidates_needing_native_and_e4":
            decisions.count("CANDIDATE_NEEDS_NATIVE_REVIEW"),
        "rejected_proposals_needing_native": decisions.count("REJECT_PROPOSAL"),
        "journal_head_sha256": after["journal_head_sha256"],
        "native_v123_final_approval": False,
        "official_e4_approval": False,
        "knowledge_published": False,
        "e5_authorized": False,
    }
    return {**report, "receipt_sha256": digest(report)}