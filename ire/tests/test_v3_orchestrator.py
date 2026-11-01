"""V3 queue integration tests using only fresh synthetic subtitle sources."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ire.source import sha256
from ire.v3_orchestrator import ChatBatchQueue
from test_engine import VID, synthetic_srt, annotations
from test_semantics import synthetic_reply
from test_checkpoint import source_many, nonclaim_response

OTHER = "BbCcDdEeF34"


class V3ChatQueueTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name)
        raw1, self.sha1 = synthetic_srt()
        raw2 = source_many()
        self.files = []
        for idx, (video, raw) in enumerate([(VID, raw1), (OTHER, raw2)], 1):
            original = self.home / f"original_{idx}.srt"
            original.write_bytes(raw)
            self.files.append({
                "video_id": video,
                "original_srt_path": str(original),
                "source_sha256": sha256(raw),
                "private_chat_sessions_path": str(self.home / f"session_{idx}"),
            })
        self.manifest = {
            "schema": "IRE_V2_CHAT_BATCH_V1",
            "research_as_of": "2026-11-02",
            "videos": self.files,
        }
        self.queue = ChatBatchQueue(self.manifest)

    def answers(self, batch):
        rows = []
        for item in batch["packets"]:
            packet = item["packet"]
            if item["video_id"] == VID:
                content = synthetic_reply(annotations(self.sha1))
            else:
                content = nonclaim_response(packet)
            rows.append({
                "video_id": item["video_id"],
                "submission": {
                    "schema": "IRE_CHAT_WINDOW_ANSWER_V1",
                    "session_id": packet["session_id"],
                    "window_id": packet["window_id"],
                    "packet_sha256": packet["packet_sha256"],
                    "claims": copy.deepcopy(content["claims"]),
                    "cue_dispositions": copy.deepcopy(
                        content["cue_dispositions"]),
                },
            })
        return {
            "schema": "IRE_V3_CHAT_SUBMISSION_V1",
            "batch_sha256": batch["batch_sha256"],
            "max_packets": batch["max_packets"],
            "max_chars": batch["max_chars"],
            "answers": rows,
        }

    def test_multi_video_queue_and_interrupt_resume(self):
        status = self.queue.status()
        self.assertEqual(status["total_cues"], 35)
        self.assertEqual(status["total_windows"], 5)
        work = self.queue.next_work(max_packets=2, max_chars=30000)
        self.assertEqual(len(work["packets"]), 2)
        self.assertEqual([x["video_id"] for x in work["packets"]],
                         [VID, OTHER])
        first = self.queue.accept(self.answers(work))
        self.assertEqual(first["accepted_windows"], 2)
        self.assertEqual(first["remaining_windows"], 3)
        restarted = ChatBatchQueue(self.manifest)
        self.assertEqual(restarted.status()["accepted_windows"], 2)
        pending = restarted.next_work(max_packets=3, max_chars=60000)
        self.assertEqual(len(pending["packets"]), 3)
        self.assertTrue(all(x["video_id"] == OTHER
                            for x in pending["packets"]))
        resumed = restarted.accept(self.answers(pending))
        self.assertEqual(resumed["remaining_windows"], 0)
        self.assertTrue(resumed["full_semantic_analysis_submitted"])
        self.assertFalse(resumed["advisory_ready"])
        self.assertEqual(resumed["official_facts_approved"], 0)
        result = restarted.finalize(str(self.home / "kb"),
                                    str(self.home / "audit"))
        self.assertEqual(result["status"],
                         "SOURCE_ANALYSIS_COMPLETE_EVIDENCE_PENDING")
        self.assertIsNotNone(result["knowledge_snapshot_sha256"])
        self.assertTrue(Path(result["audit_path"]).exists())

    def test_invalid_second_answer_rejects_all_without_cache(self):
        work = self.queue.next_work(max_packets=2, max_chars=30000)
        response = self.answers(work)
        response["answers"][1]["submission"]["cue_dispositions"][0][
            "reason"] = None
        with self.assertRaisesRegex(ValueError,
                                    "SEMANTIC_NONCLAIM_REASON_REQUIRED"):
            self.queue.accept(response)
        self.assertEqual(self.queue.status()["accepted_windows"], 0)
        self.assertEqual(sum(len(list(x.answers.glob("*.json")))
                             for x in self.queue.sessions), 0)

    def test_stale_batch_or_cross_video_source_spoof_is_blocked(self):
        work = self.queue.next_work(max_packets=2, max_chars=30000)
        spoof = self.answers(work)
        spoof["answers"][1]["video_id"] = VID
        with self.assertRaisesRegex(ValueError,
                                    "V3_RESPONSE_VIDEO_ORDER_MISMATCH"):
            self.queue.accept(spoof)
        wrong = self.answers(work)
        wrong["batch_sha256"] = sha256(b"substituted")
        with self.assertRaisesRegex(ValueError,
                                    "V3_BATCH_CHECKPOINT_OR_IDENTITY_MISMATCH"):
            self.queue.accept(wrong)
        self.queue.accept(self.answers(work))
        with self.assertRaisesRegex(ValueError,
                                    "V3_BATCH_CHECKPOINT_OR_IDENTITY_MISMATCH"):
            self.queue.accept(self.answers(work))

    def test_incomplete_batch_blocks_knowledge_commit(self):
        result = self.queue.finalize(str(self.home / "kb"),
                                     str(self.home / "audit"))
        self.assertEqual(result["status"], "INCOMPLETE_REQUIRES_RESUME")
        self.assertIsNone(result["knowledge_snapshot_sha256"])
        self.assertEqual(list((self.home / "kb").glob("ire_knowledge_v*.json")),
                         [])

    def test_original_bytes_replaced_between_calls_fails_closed(self):
        work = self.queue.next_work(max_packets=1, max_chars=30000)
        source = Path(self.files[0]["original_srt_path"])
        source.write_bytes(b"changed source")
        with self.assertRaisesRegex(ValueError, "SOURCE_SHA256_MISMATCH"):
            ChatBatchQueue(self.manifest)
        self.assertEqual(work["packet_count"], 1)

    def test_tiny_packet_budget_refuses_silent_skip(self):
        with self.assertRaisesRegex(ValueError,
                                    "V3_PACKET_BUDGET_TOO_SMALL_FOR_SOURCE"):
            self.queue.next_work(max_packets=2, max_chars=1000)
        self.assertEqual(self.queue.status()["remaining_windows"], 5)

    def test_no_api_cli_workflow(self):
        path = self.home / "manifest.json"
        path.write_text(json.dumps(self.manifest))
        base = [sys.executable, "-m", "ire.v3_orchestrator",
                "--private-manifest", str(path)]
        def call(op, *args):
            command = [sys.executable, "-m", "ire.v3_orchestrator",
                       op, "--private-manifest", str(path), *args]
            proc = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(proc.stderr, "")
            return proc, json.loads(proc.stdout)
        proc, data = call("status")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(data["remaining_windows"], 5)
        proc, batch = call("next", "--max-packets", "2",
                           "--max-chars", "30000")
        self.assertEqual(proc.returncode, 0)
        submission = self.home / "submission.json"
        submission.write_text(json.dumps(self.answers(batch),
                                         ensure_ascii=False))
        proc, receipt = call("accept", "--private-submission",
                             str(submission))
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(receipt["accepted_windows"], 2)
        self.assertEqual(receipt["external_model_api_calls"], 0)


if __name__ == "__main__":
    unittest.main()
