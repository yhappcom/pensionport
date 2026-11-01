"""No-API chat integration tests, using exclusively newly made synthetic sources."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from ire.chat_bridge import ConversationResearchSession
from test_engine import VID,synthetic_srt,annotations
from test_semantics import synthetic_reply
from test_checkpoint import source_many,nonclaim_response
from ire.source import sha256


class ChatOnlyResearchIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.raw,self.digest=synthetic_srt()
        self.gold_free_reply=synthetic_reply(annotations(self.digest))
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        self.session=ConversationResearchSession(
            self.raw,VID,self.digest,str(self.root/"chat_sessions"))

    def answer(self,reply=None,session=None):
        owner=session or self.session
        packet=owner.next_packet()
        value=reply if reply is not None else self.gold_free_reply
        return {
            "schema":"IRE_CHAT_WINDOW_ANSWER_V1",
            "session_id":packet["session_id"],
            "window_id":packet["window_id"],
            "packet_sha256":packet["packet_sha256"],
            "claims":copy.deepcopy(value["claims"]),
            "cue_dispositions":copy.deepcopy(value["cue_dispositions"])
        }

    def test_prepare_next_accept_resume_finalize_without_api(self):
        packet=self.session.next_packet()
        self.assertEqual(packet["video_id"],VID)
        self.assertEqual(len(packet["primary_cues"]),4)
        self.assertFalse(packet["model_api_required"])
        with patch.dict(os.environ,{"OPENAI_API_KEY":"EXISTING_KEY_IS_IGNORED"}):
            submitted=self.session.accept(self.answer())
            resumed=ConversationResearchSession(
                self.raw,VID,self.digest,str(self.root/"chat_sessions"))
            report=resumed.finalize()
        self.assertEqual(submitted["remaining_windows"],0)
        self.assertEqual(report["model_api_calls"],0)
        self.assertEqual(report["proposed_atoms"],2)
        stored=json.loads(Path(report["private_report_path"]).read_text())
        self.assertFalse(stored["semantic_completeness_certified"])
        self.assertFalse(stored["financial_fact_verified"])
        self.assertEqual(stored["financial_facts_approved"],0)
        self.assertFalse(stored["independent_human_gold_available"])
        self.assertEqual(len(stored["verification_worklist"]["claims"]),2)
        self.assertEqual(Path(report["private_report_path"]).stat().st_mode & 0o077,0)
        self.assertIsNone(resumed.next_packet())
        with self.assertRaisesRegex(ValueError,"CHAT_FINAL_REPORT_OVERWRITE_FORBIDDEN"):
            resumed.finalize()

    def test_untrusted_model_cannot_hallucinate_source_and_retry_cleanly(self):
        answer=self.answer()
        answer["claims"][0]["source_refs"][0]["quote"]="모든 투자자의 수익률 100% 보장"
        with self.assertRaisesRegex(ValueError,"UNTRACEABLE_QUOTED_SOURCE"):
            self.session.accept(answer)
        self.assertEqual(self.session.status()["accepted_windows"],0)
        self.assertFalse(list(self.session.answers.glob("*.json")))
        valid=self.session.accept(self.answer())
        self.assertEqual(valid["accepted_windows"],1)

    def test_wrong_packet_or_video_identity_refused(self):
        ans=self.answer()
        ans["packet_sha256"]=sha256(b"false packet")
        with self.assertRaisesRegex(ValueError,"CHAT_ANSWER_SESSION_OR_PACKET_MISMATCH"):
            self.session.accept(ans)
        ans=self.answer()
        ans["session_id"]=sha256(b"another original")
        with self.assertRaisesRegex(ValueError,"CHAT_ANSWER_SESSION_OR_PACKET_MISMATCH"):
            self.session.accept(ans)

    def test_cue_omission_and_duplicate_are_blocked(self):
        ans=self.answer()
        ans["cue_dispositions"].pop()
        with self.assertRaisesRegex(ValueError,"SEMANTIC_WINDOW_OUTPUT_CENSUS_INVALID"):
            self.session.accept(ans)
        self.session.accept(self.answer())
        with self.assertRaisesRegex(ValueError,"CHAT_ANSWER_OVERWRITE_FORBIDDEN"):
            self.session.accept(self.answer())

    def test_cached_chat_reply_tampering_blocks_resume(self):
        self.session.accept(self.answer())
        cache=self.session.answers/"W00001.json"
        saved=json.loads(cache.read_text())
        saved["answer"]["claims"][0]["proposition"]="different claim on replay"
        cache.write_text(json.dumps(saved))
        with self.assertRaisesRegex(ValueError,"CHAT_CACHED_ANSWER_TAMPERED"):
            self.session.status()

    def test_incomplete_multiwindow_source_cannot_finalize(self):
        raw=source_many()
        session=ConversationResearchSession(
            raw,VID,sha256(raw),str(self.root/"many"))
        self.assertEqual(session.status()["total_windows"],4)
        self.assertEqual(session.status()["remaining_windows"],4)
        answer=session.next_packet()
        packet=nonclaim_response(answer)
        session.accept({
            "schema":"IRE_CHAT_WINDOW_ANSWER_V1",
            "session_id":answer["session_id"],
            "window_id":answer["window_id"],
            "packet_sha256":answer["packet_sha256"],
            "claims":packet["claims"],
            "cue_dispositions":packet["cue_dispositions"]
        })
        self.assertEqual(session.status()["remaining_windows"],3)
        with self.assertRaisesRegex(ValueError,"CHAT_FINALIZE_BLOCKED_UNANNOTATED_WINDOWS"):
            session.finalize()

    def test_original_hash_and_project_boundary(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_SHA256_MISMATCH"):
            ConversationResearchSession(
                self.raw,VID,sha256(b"tampered"),str(self.root/"bad"))
        from ire.cli import REPOSITORY
        with self.assertRaisesRegex(ValueError,"CHECKPOINT_INSIDE_REPOSITORY_FORBIDDEN"):
            ConversationResearchSession(
                self.raw,VID,self.digest,str(REPOSITORY/"secret"))

    def test_cli_chat_only_full_lifecycle(self):
        original=self.root/"new_source.srt"
        original.write_bytes(self.raw)
        replyfile=self.root/"new_chat_answer.json"
        arguments=[
            "--original-srt",str(original),
            "--video-id",VID,
            "--source-sha256",self.digest,
            "--private-session-dir",str(self.root/"cli_sessions")
        ]
        base=[sys.executable,"-m","ire.chat_bridge"]
        def call(command):
            proc=subprocess.run(base+[command]+arguments,
                                capture_output=True,text=True,check=False)
            self.assertFalse(proc.stderr,proc.stderr)
            return proc,json.loads(proc.stdout)
        prep,stat=call("prepare")
        self.assertEqual(prep.returncode,0)
        self.assertEqual(stat["remaining_windows"],1)
        nxt,packet=call("next")
        self.assertEqual(nxt.returncode,0)
        reply=self.gold_free_reply
        replyfile.write_text(json.dumps({
            "schema":"IRE_CHAT_WINDOW_ANSWER_V1",
            "session_id":packet["session_id"],
            "window_id":packet["window_id"],
            "packet_sha256":packet["packet_sha256"],
            **reply
        },ensure_ascii=False))
        run=subprocess.run(
            base+["accept"]+arguments+["--private-reply-file",str(replyfile)],
            capture_output=True,text=True,check=False)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        finish,summary=call("finalize")
        self.assertEqual(finish.returncode,2)
        self.assertEqual(summary["model_api_calls"],0)
        self.assertEqual(summary["proposed_atoms"],2)
        self.assertNotIn("상품 비용은",finish.stdout)
        self.assertEqual(summary["release"],"BLOCKED")

    def test_chat_model_cannot_claim_human_gold_or_approve(self):
        answer=self.answer()
        answer["claims"][0]["annotation_status"]="APPROVED"
        with self.assertRaisesRegex(ValueError,"SEMANTIC_CLAIM_OUTPUT_SCHEMA_MISMATCH"):
            self.session.accept(answer)
        ans=self.answer()
        ans["cue_dispositions"][0]["status"]="NONCLAIM_CANDIDATE"
        with self.assertRaisesRegex(ValueError,"SEMANTIC_CUE_REVERSE_SOURCE_LINK_MISMATCH"):
            self.session.accept(ans)


if __name__=="__main__":
    unittest.main()
