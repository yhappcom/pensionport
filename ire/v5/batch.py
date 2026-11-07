"""IRE V5: four/five-video research transaction coordinator.

This is a bounded ChatGPT-host work scheduler and receipt verifier. It does NOT
call a language model or search the web, and it does not claim that planning
five videos means five videos have been researched.

Private source and claim text never enter GitHub control-plane status. A bundle
reduces hundreds of per-claim file writes to a single validated, hash-chained
receipt PER VIDEO; multi-video writes are recoverable, not globally atomic.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any
from .engine import (
    ResearchRun, RunError, require, canonical, sha256, _private_dir,
    _exclusive_json, _read_json, cues_from_srt,
)

BATCH_SCHEMA = "IRE_V5_4_5_VIDEO_BATCH_V1"
ACTION_SCHEMA = "IRE_V5_ACTION_BUNDLE_V1"
VIDEO_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
BATCH_RE = re.compile(r"^[a-zA-Z0-9][A-Za-z0-9_-]{3,63}$")


def _write_exclusive_bytes(path: Path, value: bytes) -> None:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(value)
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise


class FiveVideoResearchBatch:
    """Exact 4-5 unique full-video source manifests, locked for one request.

    inputs: iterable of {"source": raw_srt_bytes, "manifest": full V5 manifest}
    New private folder persists source bytes and each manifest for cold restart.
    Existing: `open_private` validates every stored raw source and the lock.
    """
    def __init__(self, batch_id: str, inputs: list[dict], root: str | Path):
        require(isinstance(batch_id, str) and BATCH_RE.fullmatch(batch_id) is not None,
                "FIVE_VIDEO_BATCH_ID_INVALID")
        require(type(inputs) is list and 4 <= len(inputs) <= 5,
                "FIVE_VIDEO_REQUIRES_FOUR_OR_FIVE_SOURCES")
        seen = set()
        entries = []
        for x in inputs:
            require(type(x) is dict and set(x) == {"source", "manifest"} and
                    type(x["source"]) is bytes and type(x["manifest"]) is dict,
                    "FIVE_VIDEO_INPUT_INVALID")
            m, raw = x["manifest"], x["source"]
            vid = m.get("video_id")
            require(type(vid) is str and VIDEO_RE.fullmatch(vid) and vid not in seen,
                    "FIVE_VIDEO_DUPLICATE_OR_INVALID_ID")
            seen.add(vid)
            require(m.get("source_sha256") == sha256(raw) and
                    m.get("source_cues") == len(cues_from_srt(raw)),
                    "FIVE_VIDEO_ORIGINAL_SOURCE_MISMATCH")
            require(m.get("active_window_ids") == [w.get("window_id") for w in m.get("windows", [])],
                    "FIVE_VIDEO_MUST_PLAN_FULL_VIDEO")
            entries.append({"video_id": vid, "source_sha256": sha256(raw),
                            "plan_sha256": sha256(canonical(m)),
                            "source_cues": m["source_cues"],
                            "total_windows": len(m["windows"])})
        self.root = _private_dir(Path(root))
        self.source_root = _private_dir(self.root / "videos")
        lock = {"schema": BATCH_SCHEMA, "batch_id": batch_id,
                "video_count": len(inputs), "videos": entries,
                "financial_facts_approved": 0,
                "host_model_execution_independently_proven": False}
        lock_path = self.root / "batch_lock.json"
        if lock_path.exists():
            require(_read_json(lock_path) == lock,
                    "FIVE_VIDEO_BATCH_LOCK_OR_SOURCE_CHANGED")
        self.batch_id = batch_id
        self.runs: dict[str, ResearchRun] = {}
        for x in inputs:
            vid, raw, m = x["manifest"]["video_id"], x["source"], x["manifest"]
            directory = _private_dir(self.source_root / vid)
            source_path = directory / "private_source.srt"
            plan_path = directory / "source_manifest.json"
            if source_path.exists():
                require(source_path.read_bytes() == raw, "FIVE_VIDEO_PRIVATE_SOURCE_DRIFT")
            else:
                _write_exclusive_bytes(source_path, raw)
            if plan_path.exists():
                require(_read_json(plan_path) == m, "FIVE_VIDEO_PRIVATE_PLAN_DRIFT")
            else:
                _exclusive_json(plan_path, m)
            self.runs[vid] = ResearchRun(raw, m, directory)
        if not lock_path.exists():
            _exclusive_json(lock_path, lock)
        self.lock = lock
        self.video_order = [e["video_id"] for e in entries]

    @classmethod
    def open_private(cls, root: str | Path) -> "FiveVideoResearchBatch":
        root = Path(root).expanduser().resolve()
        lock = _read_json(root / "batch_lock.json")
        require(lock.get("schema") == BATCH_SCHEMA and
                type(lock.get("videos")) is list and 4 <= len(lock["videos"]) <= 5,
                "FIVE_VIDEO_ARCHIVED_LOCK_INVALID")
        inputs = []
        for entry in lock["videos"]:
            vid = entry["video_id"]
            require(VIDEO_RE.fullmatch(vid) is not None, "FIVE_VIDEO_ARCHIVE_PATH_INVALID")
            directory = root / "videos" / vid
            inputs.append({"source": (directory / "private_source.srt").read_bytes(),
                           "manifest": _read_json(directory / "source_manifest.json")})
        return cls(lock["batch_id"], inputs, root)

    def status(self) -> dict:
        states = []
        for vid in self.video_order:
            s = self.runs[vid].replay()
            states.append({"video_id": vid, "source_sha256": s["source_sha256"],
                           "source_cues": self.runs[vid].manifest["source_cues"],
                           "windows_total": s["video_windows_total"],
                           "windows_processed": s["submitted_windows"],
                           "windows_model_evidence_relation_reviewed":
                               s["windows_model_evidence_relation_reviewed"],
                           "windows_model_pending_review":
                               s["windows_model_pending_review"],
                           "windows_remaining": s["video_windows_total"] - s["submitted_windows"],
                           "claims": s["claims"], "evidence_cases": s["evidence_cases_reviewed"],
                           "relation_cases": s["relation_cases_reviewed"],
                           "event_receipts": s["receipt_count"],
                           "event_chain_sha256": s["event_chain_head_sha256"],
                           "full_video_source_scope_sealed": s["full_video_source_scope_sealed"]})
        total = sum(x["windows_total"] for x in states)
        processed = sum(x["windows_processed"] for x in states)
        completed = sum(x["full_video_source_scope_sealed"] for x in states)
        return {"schema": "IRE_V5_4_5_BATCH_STATUS_V1", "batch_id": self.batch_id,
                "video_count": len(states), "source_cues": sum(x["source_cues"] for x in states),
                "windows_total": total, "windows_processed": processed,
                "windows_model_evidence_relation_reviewed":
                    sum(x["windows_model_evidence_relation_reviewed"] for x in states),
                "windows_model_pending_review":
                    sum(x["windows_model_pending_review"] for x in states),
                "windows_remaining": total - processed,
                "videos_full_scope_sealed": completed,
                "all_videos_research_reports_sealed": completed == len(states),
                "one_chat_turn_semantic_execution_proven": False,
                "official_financial_facts_approved": 0,
                "p0_five_video_one_turn_release": "NO_GO_NOT_INDEPENDENTLY_ATTESTED",
                "videos": states}

    def next_source_bundle(self, *, max_windows: int = 15,
                           max_chars: int = 30000) -> dict:
        """Round-robin primary source packets; no inherited prior answers in prompts."""
        require(type(max_windows) is int and 4 <= max_windows <= 100 and
                type(max_chars) is int and 4000 <= max_chars <= 250000,
                "FIVE_VIDEO_BATCH_BUDGET_INVALID")
        pending = {vid: [wid for wid in self.runs[vid].active
                         if wid not in self.runs[vid].model]
                   for vid in self.video_order}
        packets = []
        used = 0
        while len(packets) < max_windows and any(pending.values()):
            made = False
            for vid in self.video_order:
                if not pending[vid] or len(packets) >= max_windows:
                    continue
                wid = pending[vid][0]
                packet = self.runs[vid].packet(wid)
                # Side-car context is source-only. Keep the original signed
                # primary packet intact for legacy MODEL_ANALYSIS compatibility.
                from .p0_real_source_safety import adaptive_packet
                context = adaptive_packet(self.runs[vid], wid)
                item = {"video_id": vid, "packet": packet, "context": context}
                count = len(canonical(item))
                if count > max_chars:
                    raise RunError("FIVE_VIDEO_SINGLE_PACKET_EXCEEDS_BUDGET")
                if used + count > max_chars:
                    continue
                pending[vid].pop(0)
                packets.append(item)
                used += count
                made = True
            if not made:
                break
        result = {"schema": "IRE_V5_MULTI_SOURCE_WORK_PACKET_V1",
                  "batch_id": self.batch_id, "windows": packets,
                  "total_source_bytes": used, "max_source_bytes": max_chars,
                  "model_api_calls": 0,
                  "user_continue_requested": False,
                  "all_video_source_work_complete": self.status()["windows_remaining"] == 0}
        return {**result, "work_sha256": sha256(canonical(result))}

    def next_review_bundle(self, *, max_claims: int = 80) -> dict:
        """Batch official and prior obligations. Query groups are discovery-only."""
        require(type(max_claims) is int and 1 <= max_claims <= 500,
                "FIVE_VIDEO_REVIEW_LIMIT_INVALID")
        pending = []
        for vid in self.video_order:
            run = self.runs[vid]
            run.replay()
            for wid in run.active:
                if wid not in run.model:
                    continue
                for c in run.model[wid]["claims"]:
                    cid = c["claim_id"]
                    if cid not in run.evidence or cid not in run.relations:
                        pending.append({"video_id": vid, "window_id": wid,
                                        "claim_id": cid,
                                        "proposition": c["proposition"],
                                        "official_verification_required": c["requires_external_verification"],
                                        "needs_evidence_review": cid not in run.evidence,
                                        "needs_prior_relation_review": cid not in run.relations,
                                        "prior_baseline_git_blob_sha":
                                            run.manifest["prior_baseline_git_blob_sha"]})
        body = {"schema": "IRE_V5_MULTI_VIDEO_REVIEW_WORK_V1",
                "batch_id": self.batch_id, "outstanding_claims_total": len(pending),
                "claims": pending[:max_claims],
                "search_reuse_allowed": True,
                "same_search_is_not_same_applicability": True,
                "financial_fact_approved": False}
        return {**body, "work_sha256": sha256(canonical(body))}

    def submit_video_bundle(self, video_id: str, actions: list[dict]) -> dict:
        """One immutable hashed event per video, idempotent replay by content.

        A call covering several videos can be resumed after a crash; individual
        video appends are atomic, but a cross-video set is NOT an atomic commit.
        """
        require(video_id in self.runs, "FIVE_VIDEO_UNKNOWN_VIDEO")
        require(type(actions) is list and 1 <= len(actions) <= 500,
                "FIVE_VIDEO_ACTIONS_INVALID")
        bundle = {"schema": ACTION_SCHEMA, "actions": actions}
        digest = sha256(canonical(bundle))
        run = self.runs[video_id]
        run.replay()
        for f in sorted(run.events.glob("*.json")):
            event = _read_json(f)
            if event["type"] == "BATCH_ACCEPT" and sha256(canonical(event["payload"])) == digest:
                require(event["payload"] == bundle, "FIVE_VIDEO_REPLAY_CONTENT_CONFLICT")
                return {"video_id": video_id, "accepted_now": False,
                        "previously_committed": True,
                        "event_sha256": event["event_sha256"],
                        "video_status": run.status()}
        r = run.append("BATCH_ACCEPT", bundle)
        return {"video_id": video_id, "accepted_now": True,
                "previously_committed": False, "event_sha256": r["event_sha256"],
                "video_status": r["status"]}

    def submit_multi_video(self, requests: list[dict]) -> dict:
        """Preflight all videos; recoverable per-video sequential commits.

        Not all-or-nothing across video directories if power fails during writes.
        Retrying a previously committed identical bundle is idempotent.
        """
        require(type(requests) is list and 1 <= len(requests) <= len(self.video_order),
                "FIVE_VIDEO_MULTI_SUBMISSION_CENSUS_INVALID")
        vids = set()
        for entry in requests:
            require(type(entry) is dict and set(entry) == {"video_id", "actions"},
                    "FIVE_VIDEO_MULTI_SUBMISSION_SCHEMA_INVALID")
            vid = entry["video_id"]
            require(vid in self.runs and vid not in vids,
                    "FIVE_VIDEO_DUPLICATE_SUBMISSION")
            vids.add(vid)
            run = self.runs[vid]
            run.replay()
            bundle = {"schema": ACTION_SCHEMA, "actions": entry["actions"]}
            # Exact replays are safe and should not be revalidated against an
            # already advanced state (where IDs now intentionally exist).
            if any(_read_json(f).get("type") == "BATCH_ACCEPT" and
                   _read_json(f).get("payload") == bundle
                   for f in sorted(run.events.glob("*.json"))):
                continue
            before = (run.model.copy(), run.evidence.copy(),
                      run.relations.copy(), run.closure)
            try:
                run._apply("BATCH_ACCEPT", bundle)
            finally:
                run.model, run.evidence, run.relations, run.closure = before
        receipts = [self.submit_video_bundle(row["video_id"], row["actions"])
                    for row in requests]
        return {"schema": "IRE_V5_MULTI_VIDEO_BATCH_SUBMIT_V1",
                "receipts": receipts,
                "batch_state": self.status(),
                "cross_video_commit_atomic": False,
                "partial_crash_replay_supported": True}
