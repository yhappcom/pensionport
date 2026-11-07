"""V5 P0: bounded generic SRT cohort for one to twenty different videos.

This is a deterministic host-task scheduler, NOT a background ChatGPT worker,
model caller, internet researcher, or claim fact verifier. State and original
transcripts are held only in a private local folder (not committed to GitHub).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .engine import ResearchRun, RunError, require, canonical, sha256, _private_dir
from .planner import prepare_full_video_manifest
from .p0_real_source_safety import adaptive_packet, SecondPassRegistry

VID = re.compile(r"[A-Za-z0-9_-]{11}\Z")


def _private_write(path: Path, data: bytes) -> None:
    if path.exists():
        require(path.read_bytes() == data, "P0_PRIVATE_SOURCE_OR_PLAN_DRIFT")
        return
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fp:
        fp.write(data)
        fp.flush()
        os.fsync(fp.fileno())


class P0StrictResearchRun(ResearchRun):
    """P0-only run: every closure path, including append/replay, requires proofs.

    Legacy ResearchRun and historical event-body hashes are unaffected.
    Without this hook, callers could bypass GenericResearchCohort.close_video()
    through runs[video_id].close() or append(RESEARCH_CLOSURE,...).
    """
    def __init__(self, source_srt: bytes, manifest: dict, store: Path,
                 cohort_root: Path):
        self._p0_cohort_root = Path(cohort_root)
        super().__init__(source_srt, manifest, store)

    def _apply(self, kind: str, item: dict) -> None:
        if kind == "RESEARCH_CLOSURE":
            proof = SecondPassRegistry(
                {self.manifest["video_id"]: self}, self._p0_cohort_root)
            missing = [wid for wid in self.active
                       if not proof.status(self.manifest["video_id"], wid)["passed"]]
            require(not missing, "P0_SECOND_PASS_COMPLETENESS_NOT_PROVEN")
        return super()._apply(kind, item)


class GenericResearchCohort:
    """Keep existing single-video ResearchRun receipts, do not fork its schema."""

    def __init__(self, items: list[dict], private_root: Path):
        require(type(items) is list and 1 <= len(items) <= 20,
                "P0_GENERIC_COHORT_SIZE_INVALID")
        root = _private_dir(Path(private_root))
        seen = set()
        self.root = root
        self.runs = {}
        self.order = []
        for item in items:
            require(type(item) is dict and set(item) ==
                    {"video_id", "source", "prior_baseline_git_blob_sha"} and
                    type(item["source"]) is bytes,
                    "P0_GENERIC_SOURCE_INPUT_INVALID")
            vid = item["video_id"]
            require(type(vid) is str and VID.fullmatch(vid) and vid not in seen,
                    "P0_GENERIC_VIDEO_ID_DUPLICATE")
            seen.add(vid)
            manifest = prepare_full_video_manifest(
                item["source"], vid, item["prior_baseline_git_blob_sha"])
            store = _private_dir(root / vid)
            _private_write(store / "original.srt", item["source"])
            _private_write(store / "manifest.json", canonical(manifest))
            self.runs[vid] = P0StrictResearchRun(
                item["source"], manifest, store / "ledger", root)
            self.order.append(vid)
        index = {"schema": "IRE_V5_P0_GENERIC_COHORT_V1",
                 "video_ids": self.order,
                 "source_hashes": {vid: self.runs[vid].manifest["source_sha256"]
                                   for vid in self.order},
                 "model_api_execution_proven": False,
                 "source_census_is_not_research_completion": True}
        _private_write(root / "cohort_lock.json", canonical(index))
        self.p0_proofs = SecondPassRegistry(self.runs, root)

    @classmethod
    def reopen(cls, root: Path) -> "GenericResearchCohort":
        root = Path(root)
        lock = json.loads((root / "cohort_lock.json").read_text("utf-8"))
        require(lock.get("schema") == "IRE_V5_P0_GENERIC_COHORT_V1" and
                1 <= len(lock.get("video_ids", [])) <= 20,
                "P0_GENERIC_LOCK_INVALID")
        items = []
        for vid in lock["video_ids"]:
            store = root / vid
            m = json.loads((store / "manifest.json").read_text("utf-8"))
            items.append({"video_id": vid,
                          "source": (store / "original.srt").read_bytes(),
                          "prior_baseline_git_blob_sha":
                              m["prior_baseline_git_blob_sha"]})
        return cls(items, root)

    def next_source_tasks(self, *, max_windows: int = 20,
                          max_chars: int = 50000, halo_cues: int = 2) -> dict:
        require(type(max_windows) is int and 1 <= max_windows <= 100 and
                type(max_chars) is int and 2000 <= max_chars <= 250000,
                "P0_GENERIC_WORK_BUDGET_INVALID")
        queues = {}
        for vid in self.order:
            run = self.runs[vid]
            run.replay()
            queues[vid] = [wid for wid in run.active if wid not in run.model]
        out = []
        used = 0
        while len(out) < max_windows and any(queues.values()):
            made = False
            for vid in self.order:
                if not queues[vid] or len(out) >= max_windows:
                    continue
                pkt = adaptive_packet(self.runs[vid], queues[vid][0],
                                      minimum=halo_cues, maximum=8)
                item = {"video_id": vid, "contextual_packet": pkt}
                size = len(canonical(item))
                if size > max_chars:
                    raise RunError("P0_GENERIC_SINGLE_CONTEXT_PACKET_TOO_LARGE")
                if used + size > max_chars:
                    continue
                used += size
                out.append(item)
                queues[vid].pop(0)
                made = True
            if not made:
                break
        body = {"schema": "IRE_V5_P0_GENERIC_WORK_PACKET_V1",
                "items": out, "total_source_bytes": used,
                "model_executed_by_runner": False,
                "work_remaining": bool(any(queues.values()))}
        return {**body, "work_sha256": sha256(canonical(body))}

    def next_required_task(self) -> dict:
        """Second pass BEFORE evidence and prior review to avoid wasted work."""
        tasks = []
        for vid in self.order:
            run = self.runs[vid]
            t = run.next_task()
            # Every submitted model should be independently challenged for
            # additional atomic units before investing in evidence retrieval.
            for wid in run.active:
                if wid not in run.model:
                    continue
                proof = self.p0_proofs.status(vid, wid)
                if not proof["passed"]:
                    t = {"phase": (
                        "P0_ATOMIC_GAP_REQUIRES_MODEL_CORRECTION"
                        if proof["has_gap"] else "P0_SECOND_PASS_REQUIRED"),
                        "window_id": wid,
                        "review_records": proof["records"],
                        "independent_atomic_recall_certified": False}
                    break
            if t["phase"] != "DONE":
                ctx = adaptive_packet(run, t["window_id"]) if (
                    t["phase"] in {"MODEL_ANALYSIS_REQUIRED",
                                   "P0_SECOND_PASS_REQUIRED",
                                   "P0_ATOMIC_GAP_REQUIRES_MODEL_CORRECTION"}
                    ) else None
                tasks.append({"video_id": vid, "task": t,
                              "contextual_packet": ctx})
        return {"schema": "IRE_V5_P0_GENERIC_NEXT_TASK_V1",
                "tasks": tasks, "user_followup_required": False,
                "all_source_research_closed": not tasks,
                "independent_semantic_recall_certified": False}

    def audit(self, video_id: str, window_id: str, second_pass: dict) -> dict:
        return self.p0_proofs.submit(video_id, window_id, second_pass)

    def close_video(self, video_id: str) -> dict:
        """Strict new P0 closure, without altering legacy receipt formats."""
        require(video_id in self.runs, "P0_GENERIC_UNKNOWN_VIDEO")
        run = self.runs[video_id]
        run.replay()
        missing = [wid for wid in run.active
                   if not self.p0_proofs.status(video_id, wid)["passed"]]
        require(not missing, "P0_SECOND_PASS_COMPLETENESS_NOT_PROVEN")
        return run.close()

    def status(self) -> dict:
        reports = []
        for vid in self.order:
            s = self.runs[vid].replay()
            reviewed = sum(self.p0_proofs.status(vid, wid)["passed"]
                           for wid in self.runs[vid].active)
            reports.append({"video_id": vid,
                            "source_cues": len(self.runs[vid].cues),
                            "p0_second_pass_proof_windows": reviewed,
                            "p0_second_pass_all_windows": reviewed == s["video_windows_total"],
                            "windows_total": s["video_windows_total"],
                            "model_windows": s["submitted_windows"],
                            "evidence_relation_reviewed_windows":
                                s["windows_model_evidence_relation_reviewed"],
                            "research_receipt_sealed": s["sealed"],
                            "atomic_recall_certified": False})
        return {"schema": "IRE_V5_P0_GENERIC_STATUS_V1",
                "videos": reports,
                "video_count": len(reports),
                "source_windows": sum(v["windows_total"] for v in reports),
                "source_windows_with_model": sum(v["model_windows"] for v in reports),
                "p0_source_windows_with_second_pass_proof":
                    sum(v["p0_second_pass_proof_windows"] for v in reports),
                "p0_source_second_pass_ready":
                    all(v["p0_second_pass_all_windows"] for v in reports),
                "independent_atomic_recall_certified": False,
                "llm_or_web_executed_by_this_module": False,
                "personal_advice_approved": False}
