"""No model API: explicit source-proven one-command execution safety tests."""
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
from ire.v3_one_turn import (run_one_turn, prepare_all_source_packets,
    compact_source_plan, reconstruct_full_source_plan, BUNDLE_SCHEMA)
from test_engine import VID, synthetic_srt, annotations
from test_semantics import synthetic_reply
from test_checkpoint import source_many, nonclaim_response

OTHER = "BbCcDdEeF34"


class OneTurnIntegrationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        raw, digest = synthetic_srt()
        self.original_digest = digest
        self.manifest = {
            "schema": "IRE_V2_CHAT_BATCH_V1", "research_as_of": "2026-11-02",
            "videos": []
        }
        for index, (vid, content) in enumerate([(VID, raw), (OTHER, source_many())]):
            path = self.root / (f"source_{index}.srt")
            path.write_bytes(content)
            self.manifest["videos"].append({
                "video_id": vid, "original_srt_path": str(path),
                "source_sha256": sha256(content),
                "private_chat_sessions_path": str(self.root / f"private_{index}"),
                "window_strategy": "V3_ADAPTIVE",
            })
        self.queue = ChatBatchQueue(self.manifest)

    def bundle(self):
        answers=[]
        for session in self.queue.sessions:
            for window in session.windows:
                packet = session.packet(window["window_id"])
                if session.video_id == VID:
                    body = synthetic_reply(annotations(self.original_digest))
                else:
                    body = nonclaim_response(packet)
                answers.append({"video_id":session.video_id,"submission":{
                    "schema":"IRE_CHAT_WINDOW_ANSWER_V1",
                    "session_id":packet["session_id"],
                    "window_id":packet["window_id"],
                    "packet_sha256":packet["packet_sha256"],
                    "claims":copy.deepcopy(body["claims"]),
                    "cue_dispositions":copy.deepcopy(body["cue_dispositions"]),
                }})
        return {"schema":BUNDLE_SCHEMA,
                "batch_fingerprint":self.queue.plan["batch_fingerprint"],
                "answers":answers}

    def test_compact_plan_losslessly_reconstructs_every_packet_and_hash(self):
        full=prepare_all_source_packets(self.queue,max_packets=2,max_chars=30000)
        compact=compact_source_plan(full)
        inflated=reconstruct_full_source_plan(compact)
        self.assertEqual(inflated,full)
        self.assertEqual(compact["original_full_plan_sha256"],full["plan_sha256"])
        self.assertEqual(compact["external_model_api_calls"],0)
        self.assertFalse(compact["previous_model_answers_included"])

    def test_tampered_compact_cue_even_with_recomputed_outer_hash_is_blocked(self):
        from ire.v3_one_turn import _canonical
        compact=compact_source_plan(prepare_all_source_packets(
            self.queue,max_packets=2,max_chars=30000))
        damaged=copy.deepcopy(compact)
        src=damaged["sources"][0]
        first=next(iter(src["cue_ledger"]))
        src["cue_ledger"][first]["text"]="THIS SUBTITLE IS AN ATTACK"
        damaged["plan_sha256"]=sha256(_canonical({k:v for k,v in damaged.items()
                                                   if k != "plan_sha256"}))
        with self.assertRaisesRegex(ValueError,"PACKET_HASH_MISMATCH"):
            reconstruct_full_source_plan(damaged)

    def test_compact_schedule_dropped_window_rejected_even_after_rehash(self):
        from ire.v3_one_turn import _canonical
        compact=compact_source_plan(prepare_all_source_packets(
            self.queue,max_packets=2,max_chars=30000))
        damaged=copy.deepcopy(compact)
        damaged["batch_schedule"][0]["window_keys"].pop()
        damaged["batch_schedule"][0]["packet_count"]-=1
        damaged["plan_sha256"]=sha256(_canonical({k:v for k,v in damaged.items()
                                                   if k != "plan_sha256"}))
        with self.assertRaisesRegex(ValueError,"BATCH_IDENTITY_MISMATCH"):
            reconstruct_full_source_plan(damaged)

    def test_cli_private_compact_plan_does_not_leak_original_cues_to_stdout(self):
        path=self.root/"manifest.json";path.write_text(json.dumps(self.manifest))
        save=self.root/"private_source"/"compact.json"
        proc=subprocess.run([sys.executable,"-m","ire.v3_one_turn","prepare",
            "--private-manifest",str(path),"--private-packets-file",str(save),
            "--compact","--max-packets","2","--max-chars","30000"],
            capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stdout)
        out=json.loads(proc.stdout)
        self.assertTrue(out["source_plan_compact"])
        self.assertEqual(save.stat().st_mode & 0o077,0)
        self.assertNotIn("synthetic",proc.stdout.lower())
        self.assertNotIn("primary_cues",proc.stdout)
        self.assertEqual(reconstruct_full_source_plan(json.loads(save.read_text()))[
            "pending_windows"],out["pending_windows"])

    def test_one_private_source_plan_contains_every_pending_packet_once(self):
        source_plan=prepare_all_source_packets(self.queue,max_packets=2,max_chars=30000)
        identity=[]
        for batch in source_plan["batches"]:
            self.assertLessEqual(batch["packet_count"],2)
            for row in batch["packets"]:
                identity.append((row["video_id"],row["packet"]["window_id"]))
        self.assertEqual(source_plan["pending_windows"],
                         self.queue.status()["total_windows"])
        self.assertEqual(len(identity),len(set(identity)))
        self.assertFalse(source_plan["contains_previous_chat_claims_or_results"])
        self.assertEqual(source_plan["external_model_api_calls"],0)
        initial=self.queue.next_work(max_packets=2,max_chars=30000)
        self.assertEqual(source_plan["batches"][0]["batch_sha256"],
                         initial["batch_sha256"])

    def test_prepare_command_writes_private_plan_not_model_answers(self):
        path=self.root/"manifest.json";path.write_text(json.dumps(self.manifest))
        source_plan_dir=self.root/"private_plan"
        source_plan=source_plan_dir/"source_packets.json"
        proc=subprocess.run([sys.executable,"-m","ire.v3_one_turn","prepare",
             "--private-manifest",str(path),"--private-packets-file",
             str(source_plan),"--max-packets","2","--max-chars","30000"],
             capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stdout)
        output=json.loads(proc.stdout)
        self.assertEqual(output["pending_windows"],self.queue.status()["total_windows"])
        self.assertTrue(source_plan.is_file())
        self.assertEqual(source_plan.stat().st_mode & 0o077,0)
        self.assertEqual(source_plan_dir.stat().st_mode & 0o077,0)
        prepared=json.loads(source_plan.read_text())
        self.assertEqual(prepared["plan_sha256"],output["plan_sha256"])
        self.assertFalse(prepared["contains_previous_chat_claims_or_results"])

    def test_source_plan_rejects_budget_instead_of_skipping_cues(self):
        with self.assertRaisesRegex(ValueError,"OVER_BUDGET"):
            prepare_all_source_packets(self.queue,max_packets=12,max_chars=1000)
        self.assertEqual(self.queue.status()["accepted_windows"],0)

    def test_source_plan_after_partial_resume_only_has_pending_windows(self):
        source=self.bundle()
        run_one_turn(self.queue,source,max_packets=1,max_chars=30000,max_rounds=1)
        plan=prepare_all_source_packets(self.queue,max_packets=2,max_chars=30000)
        self.assertEqual(plan["previously_accepted_windows"],1)
        self.assertEqual(plan["pending_windows"],self.queue.status()["remaining_windows"])
        remaining=[row["packet"]["window_id"] for batch in plan["batches"]
                    for row in batch["packets"] if row["video_id"]==VID]
        self.assertNotIn("W00001",remaining)

    def test_single_command_all_windows_and_cumulative_snapshot(self):
        all_source=self.bundle()
        result=run_one_turn(self.queue,all_source,max_packets=2,
                            max_chars=30000,
                            private_knowledge_dir=str(self.root/"kb"),
                            private_audit_dir=str(self.root/"audits"))
        self.assertEqual(result["remaining_windows"],0)
        self.assertTrue(result["one_turn_full_source_completion_achieved"])
        self.assertEqual(result["newly_accepted_windows"],
                         self.queue.status()["total_windows"])
        self.assertEqual(result["research_status"],
                         "SOURCE_ANALYSIS_COMPLETE_EVIDENCE_PENDING")
        self.assertTrue(result["knowledge_snapshot_sha256"])
        self.assertFalse(result["official_financial_truth_approved"])
        self.assertFalse(result["personalized_advisory_released"])
        self.assertEqual(result["external_model_api_calls"],0)
        self.assertEqual(len(list((self.root/"kb").glob("ire_knowledge_v*.json"))),1)

    def test_empty_bundle_is_not_fake_completion(self):
        r=run_one_turn(self.queue,None)
        self.assertEqual(r["newly_accepted_windows"],0)
        self.assertGreater(r["remaining_windows"],0)
        self.assertEqual(r["stop_reason"],"NEEDS_CHATGPT_SOURCE_MEANING_FOR_NEXT_WINDOW")
        self.assertIsNone(r["knowledge_snapshot_sha256"])
        self.assertFalse(r["one_turn_full_source_completion_achieved"])

    def test_resume_same_full_bundle_after_bounded_rounds(self):
        bundle=self.bundle()
        part=run_one_turn(self.queue,bundle,max_packets=1,max_chars=30000,max_rounds=1)
        self.assertEqual(part["newly_accepted_windows"],1)
        self.assertEqual(part["stop_reason"],"BOUNDED_ROUNDS_EXHAUSTED")
        resumed=ChatBatchQueue(self.manifest)
        remaining=run_one_turn(resumed,bundle,max_packets=2,max_chars=30000,
                               private_knowledge_dir=str(self.root/"kb"),
                               private_audit_dir=str(self.root/"audit"))
        self.assertEqual(remaining["remaining_windows"],0)
        self.assertEqual(remaining["previously_completed_windows"],1)
        self.assertEqual(remaining["newly_accepted_windows"],
                         resumed.status()["total_windows"]-1)

    def test_gap_in_supplied_answers_blocks_without_skipping(self):
        source=self.bundle()
        source["answers"]=source["answers"][1:]
        result=run_one_turn(self.queue,source,max_packets=2,max_chars=30000)
        self.assertEqual(result["newly_accepted_windows"],0)
        self.assertEqual(result["next_window_id"],"W00001")

    def test_missing_middle_answer_keeps_precise_next_position(self):
        source=self.bundle()
        # Sorted by source, consecutive first video then second.
        self.assertGreaterEqual(len(source["answers"]),3)
        missing=source["answers"][1]
        source["answers"].remove(missing)
        result=run_one_turn(self.queue,source,max_packets=3,max_chars=30000)
        self.assertEqual(result["newly_accepted_windows"],1)
        self.assertEqual(result["next_video_id"],missing["video_id"])
        self.assertEqual(result["next_window_id"],missing["submission"]["window_id"])

    def test_wrong_source_fingerprint_fails_before_writes(self):
        bundle=self.bundle();bundle["batch_fingerprint"]=sha256(b"different")
        with self.assertRaisesRegex(ValueError,"SOURCE_CHANGED"):
            run_one_turn(self.queue,bundle)
        self.assertEqual(self.queue.status()["accepted_windows"],0)

    def test_late_invalid_source_quote_preflights_before_any_write(self):
        bundle=self.bundle()
        bundle["answers"][-1]["submission"]["packet_sha256"]=sha256(b"spoof")
        with self.assertRaisesRegex(ValueError,"STALE_PACKET"):
            run_one_turn(self.queue,bundle)
        self.assertEqual(self.queue.status()["accepted_windows"],0)

    def test_duplicate_claim_window_rejected(self):
        bundle=self.bundle()
        bundle["answers"].append(copy.deepcopy(bundle["answers"][0]))
        with self.assertRaisesRegex(ValueError,"DUPLICATE_OR_STALE_PACKET"):
            run_one_turn(self.queue,bundle)
        self.assertEqual(self.queue.status()["accepted_windows"],0)

    def test_attempt_to_overwrite_immutable_prior_answer_rejected(self):
        bundle=self.bundle()
        run_one_turn(self.queue,bundle,max_packets=1,max_chars=30000,max_rounds=1)
        tampered=copy.deepcopy(bundle)
        tampered["answers"][0]["submission"]["claims"]=[]
        with self.assertRaisesRegex(ValueError,"REPLAY_CHANGED_IMMUTABLE_ANSWER"):
            run_one_turn(ChatBatchQueue(self.manifest),tampered)

    def test_after_all_windows_without_dirs_does_not_commit_knowledge(self):
        result=run_one_turn(self.queue,self.bundle(),max_packets=3,max_chars=30000)
        self.assertEqual(result["remaining_windows"],0)
        self.assertEqual(result["research_status"],
                         "SOURCE_SUBMISSION_COMPLETE_FINALIZATION_NOT_REQUESTED")
        self.assertIsNone(result["knowledge_snapshot_sha256"])

    def test_quality_gate_blocks_snapshot_even_with_all_answers(self):
        from unittest.mock import patch
        import ire.v3_claim_quality as qual
        fake=qual.audit_claim_quality(self.queue)
        fake=dict(fake, risk_count=1, material_unresolved_causal_count=1)
        with patch("ire.v3_claim_quality.audit_claim_quality",return_value=fake):
            result=run_one_turn(self.queue,self.bundle(),max_packets=2,
                                max_chars=30000,
                                private_knowledge_dir=str(self.root/"kb"),
                                private_audit_dir=str(self.root/"audit"))
        self.assertEqual(result["remaining_windows"],0)
        self.assertEqual(result["research_status"],
                         "COMPLETE_SOURCE_SUBMISSION_QUALITY_BLOCKED")
        self.assertIn("P0_UNSEPARATED_FINANCIAL_CAUSAL_BASIS",
                      result["p0_p2_release_blockers"])
        self.assertFalse((self.root/"kb").exists())
        self.assertIsNone(result["knowledge_snapshot_sha256"])

    def test_same_answer_count_with_modified_proposition_changes_bundle_digest(self):
        a=self.bundle();b=copy.deepcopy(a)
        # Source-grounded bundle identity is hashed; source-specific preflight
        # may also reject semantic divergence before any writes.
        b["answers"][0]["submission"]["claims"][0]["proposition"] += " "
        from ire.v3_one_turn import _canonical
        self.assertNotEqual(sha256(_canonical(a)),sha256(_canonical(b)))

    def test_cli_can_complete_multiple_windows_in_one_call(self):
        manifest_path=self.root/"manifest.json"
        manifest_path.write_text(json.dumps(self.manifest))
        bundle_path=self.root/"answers.json"
        bundle_path.write_text(json.dumps(self.bundle(),ensure_ascii=False))
        command=[sys.executable,"-m","ire.v3_one_turn","execute",
                 "--private-manifest",str(manifest_path),
                 "--private-answers",str(bundle_path),
                 "--private-knowledge-dir",str(self.root/"kb"),
                 "--private-audit-dir",str(self.root/"audit"),
                 "--max-packets","3","--max-chars","30000"]
        proc=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stdout)
        data=json.loads(proc.stdout)
        self.assertTrue(data["one_turn_research_snapshot_written"])
        self.assertFalse(data["official_financial_truth_approved"])
        self.assertTrue(data["p0_p2_release_blockers"])
        self.assertIsNotNone(data["supplied_bundle_sha256"])

    def test_cli_exit_code_nonzero_if_sources_incomplete(self):
        path=self.root/"manifest.json";path.write_text(json.dumps(self.manifest))
        cmd=[sys.executable,"-m","ire.v3_one_turn","execute",
             "--private-manifest",str(path)]
        r=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(r.returncode,2)
        self.assertFalse(r.stderr)
        self.assertEqual(json.loads(r.stdout)["remaining_windows"],
                         self.queue.status()["total_windows"])


if __name__=="__main__":unittest.main()