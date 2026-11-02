"""V3 audited correction overlays; synthetic research only, not semantic gold."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ire.chat_bridge import ConversationResearchSession
from ire.source import sha256
from ire.v3_corrections import SUBMISSION_SCHEMA, _serialized, submit_correction
from ire.v3_orchestrator import ChatBatchQueue
from test_engine import VID, synthetic_srt, annotations
from test_semantics import synthetic_reply


class V3CorrectionOverlayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw, self.digest = synthetic_srt()
        self.original = self.root / "source.srt"
        self.original.write_bytes(self.raw)
        self.manifest = {
            "schema": "IRE_V2_CHAT_BATCH_V1", "research_as_of": "2026-11-02",
            "videos": [{"video_id": VID, "source_sha256": self.digest,
                        "original_srt_path": str(self.original),
                        "private_chat_sessions_path": str(self.root/"sessions"),
                        "window_strategy": "V3_ADAPTIVE"}]
        }
        self.q = ChatBatchQueue(self.manifest)
        self.s = self.q.sessions[0]
        packet = self.s.next_packet()
        reply = synthetic_reply(annotations(self.digest))
        self.s.accept({"schema": "IRE_CHAT_WINDOW_ANSWER_V1",
                       "session_id": packet["session_id"],
                       "window_id": packet["window_id"],
                       "packet_sha256": packet["packet_sha256"],
                       **reply})
        self.base_file = self.s.answers/(packet["window_id"]+".json")
        self.base_sha = sha256(self.base_file.read_bytes())
        self.base = self.s._answer(packet["window_id"])
        self.packet = packet

    def proposal(self, new_text="조건이 있는 가상 금융 상품 비용 설명"):
        revised = copy.deepcopy(self.s._answer(self.packet["window_id"]))
        revised["claims"][0]["proposition"] = new_text
        return {"schema": SUBMISSION_SCHEMA,
                "video_id": VID,
                "session_id": self.s.session_id,
                "window_id": self.packet["window_id"],
                "packet_sha256": self.packet["packet_sha256"],
                "prior_answer_sha256": sha256(_serialized(self.s._answer(
                    self.packet["window_id"]))),
                "reason_codes": ["OTHER_SOURCE_MEANING_CORRECTION"],
                "affected_claim_ordinals": [1],
                "review_note": "Synthetic fixture: revise a first proposition without altering cited source cues.",
                "reviewed_as_of": "2026-11-02",
                "corrected_answer": revised}

    def test_corrected_answer_is_effective_without_changing_base_file(self):
        data = self.proposal()
        result = self.q.correct(data)
        self.assertEqual(result["revision"], 1)
        self.assertEqual(result["status"]["accepted_windows"], 1)
        self.assertTrue(result["base_checkpoint_preserved"])
        self.assertFalse(result["finance_truth_approved"])
        self.assertEqual(self.base_sha, sha256(self.base_file.read_bytes()))
        self.assertEqual(self.s._answer_original("W00001"), self.base)
        self.assertEqual(self.s._answer("W00001"), data["corrected_answer"])
        renewed = ChatBatchQueue(self.manifest)
        self.assertEqual(renewed.sessions[0]._answer("W00001"), data["corrected_answer"])
        self.assertEqual(renewed.status()["remaining_windows"], 0)
        report = renewed.sessions[0].finalize()
        saved = json.loads(Path(report["private_report_path"]).read_text())
        self.assertEqual(saved["annotations"]["claims"][0]["proposition"],
                         data["corrected_answer"]["claims"][0]["proposition"])

    def test_two_revisions_must_follow_parent_hash_chain(self):
        self.q.correct(self.proposal())
        self.q.correct(self.proposal("두 번째 합성 수정 명제입니다."))
        self.assertEqual(len(list((self.s.folder/"corrections").glob("*.json"))), 2)
        resumed = ConversationResearchSession(self.raw, VID, self.digest,
                    str(self.root/"sessions"), window_strategy="V3_ADAPTIVE")
        self.assertEqual(resumed._answer("W00001")["claims"][0]["proposition"],
                         "두 번째 합성 수정 명제입니다.")
        self.assertEqual(self.base_sha, sha256(self.base_file.read_bytes()))

    def test_stale_parent_revision_is_rejected(self):
        proposal = self.proposal()
        self.q.correct(proposal)
        another = self.proposal("세 번째 가상의 분석 설명")
        another["prior_answer_sha256"] = proposal["prior_answer_sha256"]
        with self.assertRaisesRegex(ValueError, "V3_CORRECTION_STALE_PRIOR_ANSWER"):
            self.q.correct(another)
        self.assertEqual(len(list((self.s.folder/"corrections").glob("*.json"))), 1)

    def test_forged_original_quote_rejected_without_side_effect(self):
        proposal = self.proposal()
        proposal["corrected_answer"]["claims"][0]["source_refs"][0]["quote"] = (
            "보장되는 연 99%의 투자 수익률")
        with self.assertRaisesRegex(ValueError, "UNTRACEABLE_QUOTED_SOURCE"):
            self.q.correct(proposal)
        self.assertFalse((self.s.folder/"corrections").exists())

    def test_wrong_session_or_packet_identity_cannot_revise(self):
        proposal = self.proposal()
        proposal["packet_sha256"] = sha256(b"unrelated financial source")
        with self.assertRaisesRegex(ValueError, "V3_CORRECTION_SUBMISSION_IDENTITY_INVALID"):
            self.q.correct(proposal)
        self.assertFalse((self.s.folder/"corrections").exists())

    def test_receipt_mutation_detected_even_if_original_unchanged(self):
        self.q.correct(self.proposal())
        path = next((self.s.folder/"corrections").glob("*.json"))
        doc = json.loads(path.read_text())
        doc["body"]["corrected_answer"]["claims"][0]["proposition"] = (
            "재계산된 해시가 없는 허위 투자 명제")
        path.write_text(json.dumps(doc,ensure_ascii=False))
        with self.assertRaisesRegex(ValueError, "V3_CORRECTION_HASH_OR_NAME_MISMATCH"):
            self.s.status()

    def test_rehashed_original_checkpoint_also_breaks_overlay_chain(self):
        self.q.correct(self.proposal())
        base = json.loads(self.base_file.read_text())
        base["answer"]["claims"][0]["proposition"] = "재해시된 원문과 무관한 허위 명제"
        base["answer_sha256"] = sha256(_serialized(base["answer"]))
        self.base_file.write_text(json.dumps(base,ensure_ascii=False))
        with self.assertRaisesRegex(ValueError, "V3_CORRECTION_IDENTITY_OR_PARENT_MISMATCH"):
            self.s.status()

    def test_forged_human_or_finance_approval_is_not_accepted(self):
        self.q.correct(self.proposal())
        path = next((self.s.folder/"corrections").glob("*.json"))
        doc = json.loads(path.read_text())
        doc["body"]["independent_human_reviewer"] = True
        doc["receipt_sha256"] = sha256(_serialized(doc["body"]))
        renamed = path.with_name("W00001_rev0001_" + doc["receipt_sha256"][:16]+".json")
        path.unlink()
        renamed.write_text(json.dumps(doc,ensure_ascii=False))
        with self.assertRaisesRegex(ValueError, "V3_CORRECTION_IDENTITY_OR_PARENT_MISMATCH"):
            self.s.status()

    def test_cli_correct_and_private_original_persistence(self):
        payload = self.proposal()
        correction = self.root / "correction.json"
        correction.write_text(json.dumps(payload,ensure_ascii=False))
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps(self.manifest,ensure_ascii=False))
        proc = subprocess.run([
            sys.executable,"-m","ire.v3_orchestrator","correct",
            "--private-manifest", str(manifest),
            "--private-correction", str(correction)],
            capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["revision"],1)
        self.assertFalse(result["finance_truth_approved"])
        self.assertEqual(self.base_sha,sha256(self.base_file.read_bytes()))
        self.assertNotIn("Synthetic fixture", proc.stdout)
        again = subprocess.run([
            sys.executable,"-m","ire.v3_orchestrator","correct",
            "--private-manifest", str(manifest),
            "--private-correction", str(correction)],
            capture_output=True,text=True)
        self.assertEqual(again.returncode,3)
        self.assertEqual(json.loads(again.stdout)["status"],"FAILED_CLOSED")


if __name__ == "__main__":
    unittest.main()