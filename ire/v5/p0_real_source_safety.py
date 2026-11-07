"""P0 adaptive source context and durable, fail-closed second-pass review."""
from __future__ import annotations

import json
import os
from pathlib import Path
from .engine import canonical, sha256, require, _private_dir
from .planner import END
from .p0_semantic_coverage import contextual_packet, audit_second_pass


def adaptive_packet(run, window_id: str, *, minimum: int = 2,
                    maximum: int = 8) -> dict:
    """Extend only forced boundaries; refuse to equate punctuation with meaning."""
    require(type(minimum) is int and type(maximum) is int and
            0 <= minimum <= maximum <= 8, "P0_ADAPTIVE_BUDGET_INVALID")
    baseline = contextual_packet(run, window_id, halo_cues=0)
    windows = run.manifest["windows"]
    pos = next(i for i, w in enumerate(windows)
               if w["window_id"] == window_id)
    ids = windows[pos]["primary_cue_ids"]
    forced_before = bool(pos and windows[pos - 1].get(
        "continuation_boundary_review_required"))
    forced_after = bool(windows[pos].get(
        "continuation_boundary_review_required"))
    prev = list(range(ids[0] - 1, max(0, ids[0] - maximum - 1), -1))
    following = list(range(ids[-1] + 1,
                           min(len(run.cues), ids[-1] + maximum) + 1))

    def choose(candidates, forced):
        if not forced:
            return min(minimum, len(candidates)), False
        for count, cue_id in enumerate(candidates, 1):
            if END.search(run.cues[cue_id].text):
                return max(minimum, count), False
        return len(candidates), bool(candidates)

    n_before, u_before = choose(prev, forced_before)
    n_after, u_after = choose(following, forced_after)
    before, after = sorted(prev[:n_before]), following[:n_after]
    require(not (set(before + after) & set(ids)), "P0_CONTEXT_CITATION_OWNERSHIP_LEAK")
    body = {k: v for k, v in baseline.items() if k != "context_sha256"}
    body.update({
        "schema": "IRE_V5_P0_ADAPTIVE_PACKET_V1",
        "before": [{"cue_index": i, "text": run.cues[i].text} for i in before],
        "after": [{"cue_index": i, "text": run.cues[i].text} for i in after],
        "context_only_cue_ids": before + after,
        "forced_before": forced_before, "forced_after": forced_after,
        "unresolved_punctuation_boundary_before": u_before,
        "unresolved_punctuation_boundary_after": u_after,
        "boundary_status_is_only_a_heuristic": True,
        "independent_atomic_recall_certified": False})
    return {**body, "context_sha256": sha256(canonical(body))}


def _write_once(path: Path, raw: bytes) -> None:
    if path.exists():
        require(path.read_bytes() == raw, "P0_PROOF_REPLAY_CONTENT_CHANGED")
        return
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())


class SecondPassRegistry:
    """Immutable per-window reviews; OPEN cannot be silently erased.

    This registry audits *submitted* chat judgments, not the semantic accuracy
    of the language model or full source recall. Review data stays private.
    """
    def __init__(self, runs: dict, private_root: Path):
        self.runs = runs
        self.root = _private_dir(Path(private_root) / "p0_second_pass_proofs")

    def submit(self, video_id: str, window_id: str, review: dict) -> dict:
        require(video_id in self.runs, "P0_PROOF_VIDEO_UNKNOWN")
        run = self.runs[video_id]
        result = audit_second_pass(run, window_id, review)
        payload = {
            "schema": "IRE_V5_P0_SECOND_PASS_PROOF_V1",
            "video_id": video_id, "window_id": window_id,
            "source_sha256": run.manifest["source_sha256"],
            "model_sha256": sha256(canonical(run.model[window_id])),
            "review_sha256": sha256(canonical(review)),
            "result": result,
        }
        raw = canonical(payload)
        folder = _private_dir(_private_dir(self.root / video_id) / window_id)
        _write_once(folder / (sha256(raw) + ".json"), raw)
        return result

    def status(self, video_id: str, window_id: str) -> dict:
        require(video_id in self.runs, "P0_PROOF_VIDEO_UNKNOWN")
        run = self.runs[video_id]
        if window_id not in run.model:
            return {"passed": False, "has_gap": False, "records": 0}
        folder = self.root / video_id / window_id
        if not folder.exists():
            return {"passed": False, "has_gap": False, "records": 0}
        model_sha = sha256(canonical(run.model[window_id]))
        current = []
        for path in sorted(folder.glob("*.json")):
            raw = path.read_bytes()
            require(path.name == sha256(raw) + ".json",
                    "P0_PROOF_FILE_HASH_MISMATCH")
            record = json.loads(raw)
            result = record.get("result", {})
            require(record.get("schema") == "IRE_V5_P0_SECOND_PASS_PROOF_V1"
                    and record.get("video_id") == video_id
                    and record.get("window_id") == window_id
                    and record.get("source_sha256") ==
                        run.manifest["source_sha256"]
                    and result.get("model_packet_sha256") ==
                        run.packet(window_id)["packet_sha256"]
                    and result.get("result_sha256") ==
                        sha256(canonical({k:v for k,v in result.items()
                                         if k != "result_sha256"})),
                    "P0_PROOF_SOURCE_OR_RESULT_DRIFT")
            if record["model_sha256"] == model_sha:
                current.append(record)
        gap = any(not v["result"]["source_review_reconciled"] for v in current)
        passed = bool(current) and not gap and any(
            v["result"]["source_review_reconciled"] for v in current)
        return {"passed": passed, "has_gap": gap, "records": len(current)}
