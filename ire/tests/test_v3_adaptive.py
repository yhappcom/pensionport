"""Adaptive V3 discourse planning and explicit V2 checkpoint isolation tests."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from ire.source import Cue, sha256, source_record, parse_srt
from ire.v3_adaptive import adaptive_discourse_windows
from ire.chat_bridge import ConversationResearchSession
from ire.v3_orchestrator import ChatBatchQueue
from test_engine import VID
from test_checkpoint import source_many, nonclaim_response


class AdaptiveV3SourceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.raw = source_many()
        self.digest = sha256(self.raw)

    def test_all_cues_owned_once_bounded_with_original_halo(self):
        cues = parse_srt(self.raw, self.digest)
        older = source_record(self.raw, VID, self.digest)["windows"]
        newer = adaptive_discourse_windows(cues)
        self.assertEqual(len(older), 4)
        self.assertEqual(len(newer), 2)
        self.assertEqual([i for w in newer for i in w["source_cue_ids"]],
                         list(range(1, 32)))
        self.assertTrue(all(len(w["source_cue_ids"]) <= 18
                            for w in newer))
        self.assertEqual(newer[1]["left_context_cue_ids"], [16, 17, 18])
        self.assertEqual(newer[0]["right_context_cue_ids"], [19, 20, 21])
        self.assertTrue(all(
            w["semantic_interpretation"] == "NOT_PERFORMED" for w in newer))

    def test_compound_sentence_can_cross_old_ten_cue_boundary(self):
        texts = ["연금 수령 금액은" for _ in range(11)] + [
            "이전 조건과 함께 계산합니다"]
        cues = tuple(Cue(index=i, start_ms=i*1000,
                         end_ms=i*1000+800, text=text)
                     for i, text in enumerate(texts, 1))
        adaptive = adaptive_discourse_windows(cues)
        self.assertEqual(len(adaptive), 1)
        self.assertEqual(adaptive[0]["source_cue_ids"], list(range(1, 13)))
        self.assertEqual(adaptive[0]["right_context_cue_ids"], [])

    def test_financial_topic_switch_can_cut_after_finished_clause(self):
        texts = ["IRP 수수료 0.3%입니다"] * 5 + ["ETF 매매 비용입니다"] * 5
        cues = tuple(Cue(index=i, start_ms=i*1200,
                         end_ms=i*1200+900, text=t)
                     for i, t in enumerate(texts, 1))
        newer = adaptive_discourse_windows(cues)
        self.assertEqual([len(w["source_cue_ids"]) for w in newer], [5, 5])

    def test_oversize_unbounded_cue_is_not_dropped(self):
        cues = (Cue(index=1, start_ms=0, end_ms=1000,
                    text="임의 문자 " * 700),)
        with self.assertRaisesRegex(
                ValueError, "V3_ADAPTIVE_SINGLE_CUE_EXCEEDS_CONTEXT_BUDGET"):
            adaptive_discourse_windows(cues)

    def test_explicit_version_never_reuses_v2_session_checkpoint(self):
        folder = str(self.root/"private_sessions")
        old = ConversationResearchSession(
            self.raw, VID, self.digest, folder)
        first = old.next_packet()
        a = nonclaim_response(first)
        old.accept({
            "schema": "IRE_CHAT_WINDOW_ANSWER_V1",
            "session_id": first["session_id"],
            "window_id": first["window_id"],
            "packet_sha256": first["packet_sha256"],
            **a,
        })
        self.assertEqual(old.status()["accepted_windows"], 1)
        fresh = ConversationResearchSession(
            self.raw, VID, self.digest, folder,
            window_strategy="V3_ADAPTIVE")
        self.assertEqual(fresh.status()["accepted_windows"], 0)
        self.assertEqual(fresh.status()["total_windows"], 2)
        self.assertNotEqual(old.session_id, fresh.session_id)
        self.assertTrue((old.folder/"answers"/"W00001.json").exists())
        self.assertEqual(json.loads(
            (fresh.folder/"session_manifest.json").read_text())[
                "window_strategy"], "V3_ADAPTIVE")
        resumed = ConversationResearchSession(
            self.raw, VID, self.digest, folder)
        self.assertEqual(resumed.status()["accepted_windows"], 1)

    def test_v3_adaptive_full_multiwindow_queue_and_v2_finalizer(self):
        original = self.root/"original.srt"
        original.write_bytes(self.raw)
        manifest = {
            "schema": "IRE_V2_CHAT_BATCH_V1",
            "research_as_of": "2026-11-02",
            "videos": [{
                "video_id": VID,
                "original_srt_path": str(original),
                "source_sha256": self.digest,
                "private_chat_sessions_path": str(self.root/"checkpoints"),
                "window_strategy": "V3_ADAPTIVE",
            }]
        }
        queue = ChatBatchQueue(manifest)
        self.assertEqual(queue.status()["total_windows"], 2)
        batch = queue.next_work(max_packets=2, max_chars=60000)
        self.assertEqual(batch["packet_count"], 2)
        answers = []
        for entry in batch["packets"]:
            packet = entry["packet"]
            answers.append({
                "video_id": VID,
                "submission": {
                    "schema": "IRE_CHAT_WINDOW_ANSWER_V1",
                    "session_id": packet["session_id"],
                    "window_id": packet["window_id"],
                    "packet_sha256": packet["packet_sha256"],
                    **nonclaim_response(packet),
                }
            })
        receipt = queue.accept({
            "schema": "IRE_V3_CHAT_SUBMISSION_V1",
            "batch_sha256": batch["batch_sha256"],
            "max_packets": batch["max_packets"],
            "max_chars": batch["max_chars"],
            "answers": answers,
        })
        self.assertTrue(receipt["full_semantic_analysis_submitted"])
        restarted = ChatBatchQueue(manifest)
        self.assertEqual(restarted.status()["remaining_windows"], 0)
        final = restarted.finalize(
            str(self.root/"kb"), str(self.root/"audits"))
        self.assertEqual(final["status"],
                         "SOURCE_ANALYSIS_COMPLETE_EVIDENCE_PENDING")
        self.assertIsNotNone(final["knowledge_snapshot_sha256"])
        self.assertTrue(Path(final["audit_path"]).is_file())

    def test_reject_invalid_mode_without_cross_contamination(self):
        original = self.root/"source.srt"
        original.write_bytes(self.raw)
        m = {"schema": "IRE_V2_CHAT_BATCH_V1",
             "research_as_of": "2026-11-02",
             "videos": [{
                 "video_id": VID,
                 "original_srt_path": str(original),
                 "source_sha256": self.digest,
                 "private_chat_sessions_path": str(self.root/"bad"),
                 "window_strategy": "UNVERIFIED",
             }]}
        with self.assertRaisesRegex(ValueError, "V2_BATCH_ITEM_SCHEMA_INVALID"):
            ChatBatchQueue(m)


if __name__ == "__main__":
    unittest.main()
