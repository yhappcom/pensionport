"""Single-command, resumable ChatGPT-hosted V3 research execution (no LLM API).

The current ChatGPT conversation writes source-cited financial meanings into a
PRIVATE sealed answer bundle. This deterministic program accepts every available
verified answer in source order, checks the live source and effective revisions,
then performs exactly one finalization when the entire requested batch is ready.
It NEVER calls a model, invents missing responses, bypasses semantic blockers or
asserts investment advice approval. A complete answer bundle can be finished in
one command; an incomplete bundle yields a safe next-work receipt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .source import require, sha256
from .cli import private_file, write_new_private_report
from .semantics import verify_window_before_caching
from .v3_semantic_audit import window_semantic_audit
from .v3_orchestrator import ChatBatchQueue, _canonical
from .v3_release import completion_gate
from .knowledge import read_private_snapshot

BUNDLE_SCHEMA = "IRE_V3_ONE_TURN_ANSWERS_V1"
RECEIPT_SCHEMA = "IRE_V3_ONE_TURN_EXECUTION_V1"
MAX_BUNDLE_BYTES = 32_000_000
MAX_ROUNDS = 1000


def _load_bundle(queue: ChatBatchQueue, bundle: dict | None) -> dict:
    if bundle is None:
        return {}
    require(type(bundle) is dict and set(bundle) == {
        "schema", "batch_fingerprint", "answers"
    } and bundle["schema"] == BUNDLE_SCHEMA and
            bundle["batch_fingerprint"] == queue.plan["batch_fingerprint"] and
            type(bundle["answers"]) is list and
            len(bundle["answers"]) <= 10000,
            "V3_ONE_TURN_BUNDLE_SCHEMA_OR_SOURCE_CHANGED")
    index = {}
    sessions = {s.video_id: s for s in queue.sessions}
    # Preflight the ENTIRE submitted bundle, including later windows, before
    # accepting any new checkpoint. The model response is always untrusted.
    for row in bundle["answers"]:
        require(type(row) is dict and set(row) == {"video_id", "submission"},
                "V3_ONE_TURN_ROW_SCHEMA_INVALID")
        vid, answer = row["video_id"], row["submission"]
        require(type(vid) is str and vid in sessions and
                type(answer) is dict and set(answer) == {
                    "schema", "session_id", "window_id", "packet_sha256",
                    "claims", "cue_dispositions"
                } and answer["schema"] == "IRE_CHAT_WINDOW_ANSWER_V1",
                "V3_ONE_TURN_ANSWER_SCHEMA_INVALID")
        session = sessions[vid]
        wid = answer["window_id"]
        require(type(wid) is str, "V3_ONE_TURN_WINDOW_INVALID")
        packet = session.packet(wid)
        key = (vid, wid)
        require(key not in index and
                answer["session_id"] == packet["session_id"] and
                answer["packet_sha256"] == packet["packet_sha256"],
                "V3_ONE_TURN_DUPLICATE_OR_STALE_PACKET")
        content = {"claims": answer["claims"],
                   "cue_dispositions": answer["cue_dispositions"]}
        # Existing immutable base checkpoints may have later corrections.
        # Replays must be the same base answer (or the exact effective one),
        # never a silent change to a previously stored financial proposition.
        original = session._answer_original(wid)
        effective = session._answer(wid)
        if original is not None:
            require(content == original or content == effective,
                    "V3_ONE_TURN_REPLAY_CHANGED_IMMUTABLE_ANSWER")
        else:
            verify_window_before_caching(
                session.original, session.digest, session._window(wid), content)
            audit = window_semantic_audit(packet, answer)
            require(not audit["critical"],
                    "V3_ONE_TURN_UNSUPPORTED_HIGH_SIGNAL_CLAIM")
        index[key] = answer
    return index


def run_one_turn(queue: ChatBatchQueue, bundle: dict | None = None, *,
                 max_packets: int = 8, max_chars: int = 40000,
                 max_rounds: int = MAX_ROUNDS,
                 private_knowledge_dir: str | None = None,
                 private_audit_dir: str | None = None,
                 prior_knowledge_snapshot: str | None = None,
                 prior_evidence_snapshot: str | None = None,
                 private_evidence_dir: str | None = None) -> dict:
    """Run all source-validated *provided* answers; never synthesize claims.

    The caller may invoke again with the very same complete answer bundle after
    an I/O interruption; already-sealed answers are checked, not overwritten.
    """
    require(type(max_packets) is int and 1 <= max_packets <= 12 and
            type(max_chars) is int and 1000 <= max_chars <= 60000 and
            type(max_rounds) is int and 1 <= max_rounds <= MAX_ROUNDS,
            "V3_ONE_TURN_LIMIT_INVALID")
    require((private_knowledge_dir is None) == (private_audit_dir is None),
            "V3_ONE_TURN_FINALIZE_DIRECTORY_PAIR_REQUIRED")
    if prior_knowledge_snapshot or prior_evidence_snapshot or private_evidence_dir:
        require(private_knowledge_dir is not None,
                "V3_ONE_TURN_PRIOR_LEDGER_REQUIRES_FINALIZE_DIR")
    index = _load_bundle(queue, bundle)
    bundle_digest = sha256(_canonical(bundle)) if bundle is not None else None
    before = queue.status()
    submitted_now = 0
    completed_rounds = 0
    stop_reason = None
    while completed_rounds < max_rounds:
        state = queue.status()
        if not state["remaining_windows"]:
            break
        batch = queue.next_work(max_packets=max_packets, max_chars=max_chars)
        count = 0
        for item in batch["packets"]:
            packet = item["packet"]
            if (item["video_id"], packet["window_id"]) not in index:
                break
            count += 1
        if not count:
            stop_reason = "NEEDS_CHATGPT_SOURCE_MEANING_FOR_NEXT_WINDOW"
            break
        if count < len(batch["packets"]):
            # Reissue the correct hash for the shorter contiguous prefix.
            batch = queue.next_work(max_packets=count, max_chars=max_chars)
        response = {
            "schema": "IRE_V3_CHAT_SUBMISSION_V1",
            "batch_sha256": batch["batch_sha256"],
            "max_packets": batch["max_packets"],
            "max_chars": batch["max_chars"],
            "answers": [{"video_id": item["video_id"], "submission": index[
                (item["video_id"], item["packet"]["window_id"])]}
                        for item in batch["packets"]],
        }
        queue.accept(response)
        submitted_now += len(response["answers"])
        completed_rounds += 1
    after = queue.status()
    if not stop_reason and after["remaining_windows"]:
        stop_reason = "BOUNDED_ROUNDS_EXHAUSTED"
    first_pending = next((x for x in after["per_source"]
                          if x["next_window_id"] is not None), None)
    audit = queue.audit_semantic_coverage()
    quality = audit["cross_window_claim_quality"]
    ready_to_finalize = (after["remaining_windows"] == 0 and
                         audit["critical_count"] == 0 and
                         quality["risk_count"] == 0)
    final = None
    if after["remaining_windows"]:
        research_state = "INCOMPLETE_REQUIRES_CHATGPT_SOURCE_ANALYSIS"
    elif not ready_to_finalize:
        research_state = "COMPLETE_SOURCE_SUBMISSION_QUALITY_BLOCKED"
        stop_reason = "CRITICAL_SEMANTIC_OR_CAUSAL_REVIEW_PENDING"
    elif private_knowledge_dir is None:
        research_state = "SOURCE_SUBMISSION_COMPLETE_FINALIZATION_NOT_REQUESTED"
        stop_reason = "KNOWLEDGE_AND_AUDIT_DIRECTORIES_REQUIRED"
    else:
        final = queue.finalize(private_knowledge_dir, private_audit_dir,
                               prior_knowledge_snapshot,
                               prior_evidence_snapshot,
                               private_evidence_dir)
        research_state = final["status"]
        if research_state == "INCOMPLETE_REQUIRES_RESUME":
            stop_reason = "FINALIZE_FAIL_CLOSED"
    # A single command must also state which parts of the original P0-P2
    # research and advisory lifecycle remain blocked. Even a fully annotated
    # transcript is NOT certified official financial evidence or human gold.
    integrated_knowledge = None
    if final is not None and final["knowledge_snapshot_sha256"] is not None:
        expected = final["knowledge_snapshot_sha256"][:16]
        matches = list(Path(private_knowledge_dir).glob(
            "ire_knowledge_v*_" + expected + ".json"))
        require(len(matches) == 1,
                "V3_ONE_TURN_INTEGRATED_SNAPSHOT_NOT_FOUND")
        integrated_knowledge = read_private_snapshot(str(matches[0]))
        require(integrated_knowledge["snapshot_sha256"] ==
                final["knowledge_snapshot_sha256"],
                "V3_ONE_TURN_SNAPSHOT_IDENTITY_MISMATCH")
    lifecycle_gate = completion_gate(queue, integrated_knowledge)
    # No private source snippets, financial claims, home paths or investor
    # information are ever included in this stdout-friendly report.
    core = {
        "schema": RECEIPT_SCHEMA,
        "source_batch_fingerprint": queue.plan["batch_fingerprint"],
        "original_cues": after["total_cues"],
        "requested_windows": after["total_windows"],
        "previously_completed_windows": before["accepted_windows"],
        "newly_accepted_windows": submitted_now,
        "total_accepted_windows": after["accepted_windows"],
        "remaining_windows": after["remaining_windows"],
        "batch_rounds_executed": completed_rounds,
        "provided_answers_in_bundle": len(index),
        "supplied_bundle_sha256": bundle_digest,
        "next_video_id": first_pending["video_id"] if first_pending else None,
        "next_window_id": first_pending["next_window_id"] if first_pending else None,
        "remaining_semantic_omission_critical": audit["critical_count"],
        "remaining_material_financial_quality_risks": quality["risk_count"],
        "research_status": research_state,
        "stop_reason": stop_reason,
        "p0_p2_next_operation": lifecycle_gate["next_operation"],
        "p0_p2_release_blockers": lifecycle_gate["blockers"],
        "p0_p2_release_blocker_count": len(lifecycle_gate["blockers"]),
        "p0_p2_advisory_release_status":
            lifecycle_gate["investor_advisory_release_status"],
        "knowledge_snapshot_sha256": (final["knowledge_snapshot_sha256"]
                                       if final is not None else None),
        "official_financial_truth_approved": False,
        "independent_human_gold_certified": False,
        "personalized_advisory_released": False,
        "external_model_api_calls": 0,
        "automatic_unlabeled_inference_used": False,
        "one_turn_full_source_completion_achieved": bool(
            after["remaining_windows"] == 0),
    }
    core["one_turn_research_snapshot_written"] = bool(
        core["knowledge_snapshot_sha256"] is not None)
    return {**core, "receipt_sha256": sha256(_canonical(core))}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="One-command no-API chat-supplied financial research batch")
    parser.add_argument("operation", choices=["execute"])
    parser.add_argument("--private-manifest", required=True)
    parser.add_argument("--private-answers")
    parser.add_argument("--private-result")
    parser.add_argument("--private-knowledge-dir")
    parser.add_argument("--private-audit-dir")
    parser.add_argument("--prior-knowledge-snapshot")
    parser.add_argument("--prior-evidence-snapshot")
    parser.add_argument("--private-evidence-dir")
    parser.add_argument("--max-packets", type=int, default=8)
    parser.add_argument("--max-chars", type=int, default=40000)
    parser.add_argument("--max-rounds", type=int, default=MAX_ROUNDS)
    args = parser.parse_args()
    try:
        manifest = json.loads(private_file(
            args.private_manifest).read_text(encoding="utf-8"))
        queue = ChatBatchQueue(manifest)
        bundle = None
        if args.private_answers:
            path = private_file(args.private_answers)
            require(path.stat().st_size <= MAX_BUNDLE_BYTES,
                    "V3_ONE_TURN_BUNDLE_OVERSIZED")
            bundle = json.loads(path.read_text(encoding="utf-8"))
        result = run_one_turn(
            queue, bundle, max_packets=args.max_packets,
            max_chars=args.max_chars, max_rounds=args.max_rounds,
            private_knowledge_dir=args.private_knowledge_dir,
            private_audit_dir=args.private_audit_dir,
            prior_knowledge_snapshot=args.prior_knowledge_snapshot,
            prior_evidence_snapshot=args.prior_evidence_snapshot,
            private_evidence_dir=args.private_evidence_dir)
        if args.private_result:
            write_new_private_report(args.private_result, result)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["one_turn_research_snapshot_written"] else 2
    except (ValueError, KeyError, TypeError, OSError, UnicodeError,
            json.JSONDecodeError):
        print(json.dumps({"schema": "IRE_V3_ONE_TURN_ERROR_V1",
                          "status": "FAILED_CLOSED"}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())