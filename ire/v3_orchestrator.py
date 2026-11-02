"""IRE V3 chat-hosted cross-video work queue (no external model API).

This module never generates financial interpretations. The current ChatGPT
conversation must examine each original-only packet, author the structured
answer, and invoke accept. A deterministic queue and V2 sealed checkpoints
make interrupted requests resumable without importing historical answers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .source import require, sha256
from .cli import private_file
from .chat_bridge import ConversationResearchSession
from .semantics import verify_window_before_caching
from .v2_run import inspect_manifest, finalize_batch
from .knowledge import read_private_snapshot
from .v2_evidence import validate_evidence_ledger
from .v3_semantic_audit import window_semantic_audit, review_clusters

SCHEMA = "IRE_V3_CHAT_QUEUE_V1"
DEFAULT_MAX_PACKETS = 4
DEFAULT_MAX_CHARS = 18000


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


class ChatBatchQueue:
    """Read-only planning, primary-cue packet export and checked submissions.

    The queue has no separate progress database. Existing V2 source-tied,
    immutable per-window checkpoints are its sole source of truth. A process
    restart reconstructs missing work from those checkpoints.
    """

    def __init__(self, manifest: dict):
        self.manifest = manifest
        self.plan = inspect_manifest(manifest)
        self.sessions = []
        for source in manifest["videos"]:
            raw = private_file(source["original_srt_path"]).read_bytes()
            session = ConversationResearchSession(
                raw, source["video_id"], source["source_sha256"],
                source["private_chat_sessions_path"],
                window_strategy=source.get("window_strategy","V2_COMPAT"))
            self.sessions.append(session)

    def status(self) -> dict:
        states = [session.status() for session in self.sessions]
        return {
            "schema": "IRE_V3_CHAT_QUEUE_STATUS_V1",
            "batch_fingerprint": self.plan["batch_fingerprint"],
            "source_count": len(states),
            "total_cues": sum(s["original_cues"] for s in states),
            "total_windows": sum(s["total_windows"] for s in states),
            "accepted_windows": sum(s["accepted_windows"] for s in states),
            "remaining_windows": sum(s["remaining_windows"] for s in states),
            "per_source": [{
                "video_id": s["video_id"],
                "accepted_windows": s["accepted_windows"],
                "remaining_windows": s["remaining_windows"],
                "next_window_id": s["next_window_id"],
            } for s in states],
            "full_semantic_analysis_submitted": all(
                s["all_windows_accounted_for"] for s in states),
            "official_facts_approved": 0,
            "external_model_api_calls": 0,
            "independent_human_review": False,
            "advisory_ready": False,
        }

    def next_work(self, max_packets: int = DEFAULT_MAX_PACKETS,
                  max_chars: int = DEFAULT_MAX_CHARS) -> dict:
        require(type(max_packets) is int and 1 <= max_packets <= 12,
                "V3_PACKET_COUNT_OUT_OF_RANGE")
        require(type(max_chars) is int and 1000 <= max_chars <= 60000,
                "V3_PACKET_BUDGET_OUT_OF_RANGE")
        selected = []
        used_chars = 0
        exhausted_budget = False
        for session in self.sessions:
            for window in session.windows:
                if session._answer(window["window_id"]) is not None:
                    continue
                packet = session.packet(window["window_id"])
                size = len(_canonical(packet).decode("utf-8"))
                require(size <= 60000, "V3_SINGLE_PACKET_OVERSIZE")
                if size > max_chars and not selected:
                    raise ValueError("V3_PACKET_BUDGET_TOO_SMALL_FOR_SOURCE")
                if used_chars + size > max_chars:
                    exhausted_budget = True
                    break
                selected.append({"video_id": session.video_id,
                                 "packet": packet})
                used_chars += size
                if len(selected) == max_packets:
                    break
            if len(selected) == max_packets or exhausted_budget:
                break
        # The budget must not silently skip an oversized earlier source.
        if not selected and self.status()["remaining_windows"]:
            raise ValueError("V3_NO_PACKET_WITHIN_BUDGET")
        identity = {
            "schema": SCHEMA,
            "batch_fingerprint": self.plan["batch_fingerprint"],
            "window_identity": [[p["video_id"],
                                 p["packet"]["packet_sha256"]]
                                for p in selected]
        }
        return {
            "schema": SCHEMA,
            "batch_fingerprint": self.plan["batch_fingerprint"],
            "batch_sha256": sha256(_canonical(identity)),
            "max_packets": max_packets,
            "max_chars": max_chars,
            "packets": selected,
            "packet_count": len(selected),
            "adaptive_review_clusters": review_clusters(selected),
            "remaining_before_batch": self.status()["remaining_windows"],
            "model_execution": "CURRENT_CHATGPT_CONVERSATION_ONLY",
            "contains_untrusted_source_text": True,
            "not_a_financial_truth_certification": True
        }

    def accept(self, response: dict) -> dict:
        require(type(response) is dict and set(response) == {
            "schema", "batch_sha256", "max_packets", "max_chars", "answers"
        }, "V3_BATCH_SUBMISSION_SCHEMA_INVALID")
        require(response["schema"] == "IRE_V3_CHAT_SUBMISSION_V1",
                "V3_BATCH_SUBMISSION_VERSION_INVALID")
        request = self.next_work(response["max_packets"],
                                 response["max_chars"])
        answers = response["answers"]
        require(type(answers) is list and
                len(answers) == len(request["packets"]) and
                len(answers) > 0 and
                response["batch_sha256"] == request["batch_sha256"],
                "V3_BATCH_CHECKPOINT_OR_IDENTITY_MISMATCH")
        sessions = {s.video_id: s for s in self.sessions}
        warnings = []
        # Complete preflight before any checkpoint is written: one corrupt
        # cue quote or wrong video ID must not partially accept the batch.
        for row, expected in zip(answers, request["packets"]):
            require(type(row) is dict and set(row) == {
                "video_id", "submission"
            } and row["video_id"] == expected["video_id"],
                    "V3_RESPONSE_VIDEO_ORDER_MISMATCH")
            submission = row["submission"]
            packet = expected["packet"]
            require(type(submission) is dict and set(submission) == {
                "schema", "session_id", "window_id", "packet_sha256",
                "claims", "cue_dispositions"
            } and submission["schema"] == "IRE_CHAT_WINDOW_ANSWER_V1"
                    and submission["session_id"] == packet["session_id"]
                    and submission["window_id"] == packet["window_id"]
                    and submission["packet_sha256"] == packet["packet_sha256"],
                    "V3_RESPONSE_PACKET_PROVENANCE_INVALID")
            session = sessions[row["video_id"]]
            verify_window_before_caching(
                session.original, session.digest,
                session._window(packet["window_id"]),
                {"claims": submission["claims"],
                 "cue_dispositions": submission["cue_dispositions"]})
            source_audit = window_semantic_audit(packet, submission)
            require(not source_audit["critical"],
                    "V3_HIGH_SIGNAL_SEMANTIC_OMISSION_BLOCKED")
            warnings.extend(source_audit["warnings"])
        # Each write is O_EXCL and source tied; unexpected IO interruption
        # leaves an honest partial checkpoint, not a false batch commit.
        accepted = []
        for row in answers:
            session = sessions[row["video_id"]]
            session.accept(row["submission"])
            accepted.append([row["video_id"],
                             row["submission"]["window_id"]])
        return {
            **self.status(),
            "accepted_in_submission": accepted,
            "semantic_review_warnings": warnings,
            "status": "V3_SOURCE_LINKED_CHECKPOINTS_ACCEPTED_NOT_FACT_CERTIFIED"
        }

    def correct(self, response: dict) -> dict:
        """Append a source-tied corrected answer without altering base checkpoint."""
        from .v3_corrections import submit_correction
        require(type(response) is dict and type(response.get("video_id")) is str,
                "V3_CORRECTION_VIDEO_REQUIRED")
        matching = [s for s in self.sessions if s.video_id == response["video_id"]]
        require(len(matching) == 1, "V3_CORRECTION_UNKNOWN_VIDEO")
        receipt = submit_correction(matching[0], response)
        return {**receipt, "status": self.status()}

    def audit_semantic_coverage(self) -> dict:
        """Recheck all stored V2/V3 responses without changing their bytes.

        Important for V2 legacy checkpoints accepted before V3's strict
        high-signal omission preflight existed.
        """
        critical = []
        warnings = []
        checked = 0
        for session in self.sessions:
            for window in session.windows:
                answer = session._answer(window["window_id"])
                if answer is None:
                    continue
                checked += 1
                packet = session.packet(window["window_id"])
                result = window_semantic_audit(packet, answer)
                for item in result["critical"]:
                    critical.append({"video_id": session.video_id,
                                     "window_id": window["window_id"],
                                     **item})
                for item in result["warnings"]:
                    warnings.append({"video_id": session.video_id,
                                     "window_id": window["window_id"],
                                     **item})
        from .v3_claim_quality import audit_claim_quality
        quality = audit_claim_quality(self)
        return {
            "schema": "IRE_V3_SEMANTIC_COVERAGE_AUDIT_V1",
            "checked_windows": checked,
            "cross_window_claim_quality": quality,
            "critical_omission_suspicions": critical,
            "review_warnings": warnings,
            "critical_count": len(critical),
            "warning_count": len(warnings),
            "true_semantic_recall_measured": False,
            "independent_gold_available": False,
        }

    def finalize(self, private_knowledge_dir: str, private_audit_dir: str,
                 prior_knowledge_snapshot: str | None = None,
                 prior_evidence_snapshot: str | None = None,
                 private_evidence_dir: str | None = None) -> dict:
        audit = self.audit_semantic_coverage()
        quality = audit["cross_window_claim_quality"]
        if audit["critical_count"] or quality["risk_count"]:
            return {
                "schema": "IRE_V3_CHAT_FINALIZATION_V1",
                "status": "INCOMPLETE_REQUIRES_RESUME",
                "quality_gate": ("V3_CROSS_WINDOW_CAUSAL_AND_REGULATORY_REVIEW_BLOCKED"
                                 if quality["risk_count"] else
                                 "V3_HIGH_SIGNAL_SEMANTIC_OMISSION_BLOCKED"),
                "semantic_critical_count": audit["critical_count"],
                "material_claim_quality_risks": quality["risk_count"],
                "completed_source_windows": self.status()["accepted_windows"],
                "requested_source_windows": self.status()["total_windows"],
                "knowledge_snapshot_sha256": None,
                "approved_financial_facts": 0,
                "advisory_ready": False,
                "audit_path": None,
            }
        prior = (read_private_snapshot(prior_knowledge_snapshot)
                 if prior_knowledge_snapshot else None)
        evidence = None
        if prior_evidence_snapshot:
            require(prior is not None, "V3_EVIDENCE_REQUIRES_PRIOR_KNOWLEDGE")
            evidence = json.loads(private_file(
                prior_evidence_snapshot).read_text(encoding="utf-8"))
            validate_evidence_ledger(evidence, prior)
        result = finalize_batch(
            self.manifest, prior, private_knowledge_dir,
            private_audit_dir, evidence, private_evidence_dir)
        return {
            "schema": "IRE_V3_CHAT_FINALIZATION_V1",
            "status": result["final_research_status"],
            "completed_source_windows": result["windows_accounted_for"],
            "requested_source_windows": result["windows_total"],
            "knowledge_snapshot_sha256": result[
                "knowledge_next_snapshot_sha256"],
            "approved_financial_facts": 0,
            "advisory_ready": False,
            "audit_path": result["audit_path"],
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chat-hosted, no-model-API financial research queue")
    parser.add_argument("operation",
                        choices=["status", "next", "accept", "correct", "audit", "gate", "finalize"])
    parser.add_argument("--private-manifest", required=True)
    parser.add_argument("--private-submission")
    parser.add_argument("--private-correction")
    parser.add_argument("--max-packets", type=int, default=DEFAULT_MAX_PACKETS)
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    parser.add_argument("--private-knowledge-dir")
    parser.add_argument("--private-audit-dir")
    parser.add_argument("--prior-knowledge-snapshot")
    parser.add_argument("--prior-evidence-snapshot")
    parser.add_argument("--prior-relation-snapshot")
    parser.add_argument("--private-evidence-dir")
    args = parser.parse_args()
    try:
        manifest = json.loads(private_file(
            args.private_manifest).read_text(encoding="utf-8"))
        queue = ChatBatchQueue(manifest)
        if args.operation == "status":
            result = queue.status()
        elif args.operation == "next":
            result = queue.next_work(args.max_packets, args.max_chars)
        elif args.operation == "audit":
            result = queue.audit_semantic_coverage()
        elif args.operation == "correct":
            require(bool(args.private_correction),
                    "V3_CORRECTION_FILE_REQUIRED")
            payload = json.loads(private_file(
                args.private_correction).read_text(encoding="utf-8"))
            result = queue.correct(payload)
        elif args.operation == "gate":
            from .v3_release import completion_gate
            prior=(read_private_snapshot(args.prior_knowledge_snapshot)
                   if args.prior_knowledge_snapshot else None)
            evidence=(json.loads(private_file(args.prior_evidence_snapshot).read_text(encoding="utf-8"))
                      if args.prior_evidence_snapshot else None)
            relations=(json.loads(private_file(args.prior_relation_snapshot).read_text(encoding="utf-8"))
                       if args.prior_relation_snapshot else None)
            result=completion_gate(queue,prior,evidence,relations)
        elif args.operation == "accept":
            require(bool(args.private_submission),
                    "V3_SUBMISSION_FILE_REQUIRED")
            payload = json.loads(private_file(
                args.private_submission).read_text(encoding="utf-8"))
            result = queue.accept(payload)
        else:
            require(bool(args.private_knowledge_dir and args.private_audit_dir),
                    "V3_FINALIZE_PRIVATE_DIRECTORIES_REQUIRED")
            result = queue.finalize(
                args.private_knowledge_dir, args.private_audit_dir,
                args.prior_knowledge_snapshot, args.prior_evidence_snapshot,
                args.private_evidence_dir)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 2 if args.operation == "finalize" else 0
    except (ValueError, KeyError, TypeError, OSError, UnicodeError,
            json.JSONDecodeError):
        # Never print private source, answer or local path on failures.
        print(json.dumps({"schema": "IRE_V3_CHAT_QUEUE_ERROR_V1",
                          "status": "FAILED_CLOSED"}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())