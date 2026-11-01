"""V3 omission-risk tests, deliberately not a semantic gold benchmark."""
from __future__ import annotations

import copy
import tempfile
from pathlib import Path
import unittest

from ire.v3_semantic_audit import window_semantic_audit, review_clusters
from ire.v3_orchestrator import ChatBatchQueue
from ire.source import sha256
from test_engine import VID, synthetic_srt, annotations
from test_semantics import synthetic_reply
from test_checkpoint import nonclaim_response


class V3SemanticOmissionAuditTests(unittest.TestCase):
    def setUp(self):
        self.raw, self.digest = synthetic_srt()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        original = self.root/"original.srt"
        original.write_bytes(self.raw)
        self.manifest = {
            "schema": "IRE_V2_CHAT_BATCH_V1",
            "research_as_of": "2026-11-02",
            "videos": [{
                "video_id": VID,
                "original_srt_path": str(original),
                "source_sha256": sha256(self.raw),
                "private_chat_sessions_path": str(self.root/"private")
            }]
        }
        self.queue = ChatBatchQueue(self.manifest)
        self.work = self.queue.next_work(max_packets=1, max_chars=30000)
        self.packet = self.work["packets"][0]["packet"]

    def answer(self, data):
        return {
            "schema": "IRE_V3_CHAT_SUBMISSION_V1",
            "batch_sha256": self.work["batch_sha256"],
            "max_packets": self.work["max_packets"],
            "max_chars": self.work["max_chars"],
            "answers": [{
                "video_id": VID,
                "submission": {
                    "schema": "IRE_CHAT_WINDOW_ANSWER_V1",
                    "session_id": self.packet["session_id"],
                    "window_id": self.packet["window_id"],
                    "packet_sha256": self.packet["packet_sha256"],
                    "claims": data["claims"],
                    "cue_dispositions": data["cue_dispositions"]
                }
            }]
        }

    def test_high_signal_financial_numeric_cannot_be_silent_nonclaim(self):
        value = nonclaim_response(self.packet)
        risk = window_semantic_audit(self.packet, value)
        self.assertTrue(any(
            x["code"] == "HIGH_SIGNAL_FINANCIAL_NUMERIC_NONCLAIM"
            for x in risk["critical"]))
        with self.assertRaisesRegex(
                ValueError, "V3_HIGH_SIGNAL_SEMANTIC_OMISSION_BLOCKED"):
            self.queue.accept(self.answer(value))
        self.assertEqual(self.queue.status()["accepted_windows"], 0)

    def test_numeric_claim_missing_measurement_blocked(self):
        value = synthetic_reply(annotations(self.digest))
        value["claims"][1]["frame"]["measurements"] = []
        risk = window_semantic_audit(self.packet, value)
        self.assertIn("NUMERIC_CLAIM_WITHOUT_MEASUREMENT_FRAME",
                      [x["code"] for x in risk["critical"]])
        with self.assertRaisesRegex(
                ValueError, "V3_HIGH_SIGNAL_SEMANTIC_OMISSION_BLOCKED"):
            self.queue.accept(self.answer(value))
        self.assertEqual(self.queue.status()["accepted_windows"], 0)

    def test_valid_cue_census_passes_and_audit_is_not_truth_certification(self):
        value = synthetic_reply(annotations(self.digest))
        result = self.queue.accept(self.answer(value))
        self.assertEqual(result["accepted_windows"], 1)
        report = self.queue.audit_semantic_coverage()
        self.assertEqual(report["critical_count"], 0)
        self.assertEqual(report["checked_windows"], 1)
        self.assertFalse(report["true_semantic_recall_measured"])
        self.assertFalse(report["independent_gold_available"])

    def test_existing_v2_checkpoint_risk_is_blocked_before_knowledge_commit(self):
        value = nonclaim_response(self.packet)
        self.queue.sessions[0].accept(
            self.answer(value)["answers"][0]["submission"])
        report = self.queue.audit_semantic_coverage()
        self.assertGreater(report["critical_count"], 0)
        outcome = self.queue.finalize(
            str(self.root/"knowledge"), str(self.root/"reports"))
        self.assertEqual(outcome["status"], "INCOMPLETE_REQUIRES_RESUME")
        self.assertEqual(outcome["quality_gate"],
                         "V3_HIGH_SIGNAL_SEMANTIC_OMISSION_BLOCKED")
        self.assertIsNone(outcome["knowledge_snapshot_sha256"])
        self.assertEqual(list((self.root/"knowledge").glob("*.json")), [])

    def test_nonfinancial_smalltalk_is_not_forced_into_financial_claim(self):
        packet = {
            "video_id": VID, "window_id": "W00001",
            "primary_cues": [{
                "cue_index": 1, "start_ms": 0, "end_ms": 1000,
                "text": "여러분 안녕하세요 오늘도 반갑습니다."
            }],
            "left_context_cues": [], "right_context_cues": []
        }
        reply = {"claims": [],
                 "cue_dispositions": [{
                     "cue_index": 1, "status": "NONCLAIM_CANDIDATE",
                     "reason": "금융 사실이나 투자 지침을 언급하지 않은 인사입니다."
                 }]}
        self.assertEqual(window_semantic_audit(packet, reply)["critical"], [])
        self.assertEqual(window_semantic_audit(packet, reply)["warnings"], [])

    def test_compound_claim_is_warning_not_automatic_split(self):
        packet = {
            "video_id": VID, "window_id": "W00001",
            "primary_cues": [{"cue_index": 1, "start_ms": 0, "end_ms": 1200,
                              "text": "IRP에는 퇴직금을 넣고 또한 ISA는 비과세라는 예시"}],
            "left_context_cues": [], "right_context_cues": []
        }
        reply = {"claims": [{
            "proposition": "IRP에 퇴직금을 넣고 또한 ISA는 비과세라고 설명한다",
            "claim_types": ["PRODUCT"],
            "frame": {"measurements": []},
            "source_refs": [{"cue_index": 1, "quote": packet[
                "primary_cues"][0]["text"]}]
        }], "cue_dispositions": [{
            "cue_index": 1, "status": "LINKED", "reason": None}]}
        result = window_semantic_audit(packet, reply)
        self.assertEqual(result["critical"], [])
        self.assertIn("POSSIBLE_COMPOUND_FINANCIAL_ATOM",
                      [x["code"] for x in result["warnings"]])

    def test_review_clusters_preserve_individual_window_references(self):
        def packet(vid, win, start, end, text):
            return {"video_id": vid, "packet": {
                "window_id": win, "primary_cues": [{
                    "cue_index": start//1000+1,
                    "start_ms": start, "end_ms": end, "text": text}]
            }}
        batch = [
            packet(VID, "W00001", 0, 900, "IRP 수령 자격"),
            packet(VID, "W00002", 1100, 1800, "개인형 퇴직연금 수령 요건"),
            packet(VID, "W00003", 2200, 3000, "ETF 분배금"),
            packet("BbCcDdEeF34", "W00001", 0, 800, "퇴직급여")
        ]
        clusters = review_clusters(batch)
        self.assertEqual(clusters[0]["window_ids"], ["W00001", "W00002"])
        self.assertEqual(clusters[1]["window_ids"], ["W00003"])
        self.assertEqual(clusters[2]["video_id"], "BbCcDdEeF34")
        self.assertEqual(len(self.work["adaptive_review_clusters"]), 1)


if __name__ == "__main__":
    unittest.main()
