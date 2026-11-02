"""V3 one-turn output token compression must never silently classify a cue."""
from __future__ import annotations

import copy
import unittest

from ire.source import sha256
from ire.v3_compact_answers import (
    COMPACT_SCHEMA, compact_full_bundle, expand_compact_bundle,
    compact_answer_metrics)
from ire.v3_one_turn import (run_one_turn, prepare_all_source_packets,
    compact_source_plan, render_private_batch_for_chat,
    verify_compact_plan_against_current_original, _canonical)
import test_v3_one_turn as fixtures


class CompactAnswerExchangeTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.OneTurnIntegrationTests("test_empty_bundle_is_not_fake_completion")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.queue=self.fixture.queue
        self.full=self.fixture.bundle()
        self.compact=compact_full_bundle(self.queue,self.full)

    def test_source_exact_roundtrip(self):
        self.assertEqual(self.compact["schema"], COMPACT_SCHEMA)
        self.assertEqual(expand_compact_bundle(self.queue,self.compact),self.full)
        self.assertFalse(compact_answer_metrics(self.full,self.compact)["certifies_financial_meaning"])

    def test_one_turn_full_v1_and_compact_save_identical_contents(self):
        cp=copy.deepcopy(self.full)
        out=run_one_turn(self.queue,self.compact,max_packets=2,max_chars=30000,
                         private_knowledge_dir=str(self.fixture.root/"kb"),
                         private_audit_dir=str(self.fixture.root/"audit"))
        self.assertTrue(out["compact_answer_exchange_used"])
        self.assertEqual(out["remaining_windows"],0)
        self.assertEqual(out["provided_answers_in_bundle"],len(cp["answers"]))
        for row in cp["answers"]:
            v=next(s for s in self.queue.sessions if s.video_id==row["video_id"])
            self.assertEqual(v._answer(row["submission"]["window_id"]),{
                "claims":row["submission"]["claims"],
                "cue_dispositions":row["submission"]["cue_dispositions"]})

    def test_v1_legacy_answer_interface_still_accepted(self):
        out=run_one_turn(self.queue,self.full,max_packets=1,max_chars=30000,max_rounds=1)
        self.assertFalse(out["compact_answer_exchange_used"])
        self.assertEqual(out["newly_accepted_windows"],1)

    def test_hard_error_on_gap_before_any_file_saved(self):
        forged=copy.deepcopy(self.compact)
        forged["answers"][-1]["cue_runs"].pop()
        with self.assertRaisesRegex(ValueError,"RUNS_OR_CLAIMS_INVALID|PRIMARY_CUE_NOT_ALL_CLASSIFIED"):
            run_one_turn(self.queue,forged,max_packets=2,max_chars=30000)
        self.assertEqual(self.queue.status()["accepted_windows"],0)

    def test_hard_error_on_overlap(self):
        forged=copy.deepcopy(self.compact)
        first=forged["answers"][0]["cue_runs"]
        if len(first)>1:
            first[1][0]=first[0][0]
        else:
            first[0][0]=first[0][1]+1
        with self.assertRaisesRegex(ValueError,"CUE_RUN"):
            expand_compact_bundle(self.queue,forged)

    def test_hard_error_on_unsupported_extra_field(self):
        forged=copy.deepcopy(self.compact)
        forged["answers"][0]["claims"].append({"proposition":"fake"})
        with self.assertRaisesRegex(ValueError,"CLAIM_SCHEMA"):
            expand_compact_bundle(self.queue,forged)

    def test_source_packet_hash_mismatch(self):
        forged=copy.deepcopy(self.compact)
        forged["answers"][-1]["packet_sha256"]=sha256(b"forged")
        with self.assertRaisesRegex(ValueError,"STALE_ORIGINAL_PACKET"):
            run_one_turn(self.queue,forged)
        self.assertEqual(self.queue.status()["accepted_windows"],0)

    def test_unsupported_cue_quote_outside_primary(self):
        forged=copy.deepcopy(self.compact)
        first=forged["answers"][0]
        first["claims"][0]["source_refs"][0]=999
        with self.assertRaisesRegex(ValueError,"QUOTE_OUTSIDE_PRIMARY"):
            run_one_turn(self.queue,forged)
        self.assertEqual(self.queue.status()["accepted_windows"],0)

    def test_quote_slice_outside_text_rejected(self):
        forged=copy.deepcopy(self.compact)
        first=forged["answers"][0]
        ref=first["claims"][0]["source_refs"][0]
        idx=ref if type(ref) is int else ref[0]
        first["claims"][0]["source_refs"][0]=[idx,0,99999999]
        with self.assertRaisesRegex(ValueError,"QUOTE_OFFSET_INVALID"):
            run_one_turn(self.queue,forged)

    def test_nonclaim_without_reason_rejected(self):
        forged=copy.deepcopy(self.compact)
        spans=[s for a in forged["answers"] for s in a["cue_runs"] if s[2]=="N"]
        self.assertTrue(spans)
        spans[0][3]=-1
        with self.assertRaisesRegex(ValueError,"CUE_RUN_REASON_INVALID"):
            run_one_turn(self.queue,forged)

    def test_fake_implicit_default_status_rejected(self):
        forged=copy.deepcopy(self.compact)
        forged["status_for_all_unmentioned_cues"]="NONCLAIM_CANDIDATE"
        with self.assertRaisesRegex(ValueError,"BUNDLE_OR_ORIGINAL_MISMATCH"):
            run_one_turn(self.queue,forged)

    def test_all_claims_removed_cannot_keep_linked_status(self):
        forged=copy.deepcopy(self.compact)
        forged["answers"][0]["claims"]=[]
        with self.assertRaisesRegex(ValueError,"REVERSE_SOURCE_LINK_MISMATCH"):
            run_one_turn(self.queue,forged)
        self.assertEqual(self.queue.status()["accepted_windows"],0)

    def test_partial_bundles_produce_explicit_pause(self):
        partial=copy.deepcopy(self.compact)
        partial["answers"]=partial["answers"][:1]
        out=run_one_turn(self.queue,partial,max_packets=2,max_chars=30000)
        self.assertEqual(out["newly_accepted_windows"],1)
        self.assertGreater(out["remaining_windows"],0)
        self.assertFalse(out["one_turn_research_snapshot_written"])

    def test_duplicate_window_refused_before_side_effect(self):
        forged=copy.deepcopy(self.compact)
        forged["answers"].append(copy.deepcopy(forged["answers"][0]))
        with self.assertRaisesRegex(ValueError,"ANSWER_DUPLICATE"):
            run_one_turn(self.queue,forged)
        self.assertEqual(self.queue.status()["accepted_windows"],0)

    def test_same_compact_submission_resume_preserves_original(self):
        out=run_one_turn(self.queue,self.compact,max_packets=1,max_chars=30000,max_rounds=1)
        self.assertEqual(out["newly_accepted_windows"],1)
        original_session=self.queue.sessions[0]
        b=original_session._answer_original("W00001")
        again=run_one_turn(self.queue,self.compact,max_packets=2,max_chars=30000)
        self.assertTrue(again["compact_answer_exchange_used"])
        self.assertEqual(original_session._answer_original("W00001"),b)

    def test_render_model_input_has_unique_quoted_cues_and_provenance(self):
        original=prepare_all_source_packets(self.queue,max_packets=2,max_chars=30000)
        cp=compact_source_plan(original)
        batch=render_private_batch_for_chat(self.queue,cp,1)
        self.assertEqual(batch["window_count"],2)
        self.assertIn("UNTRUSTED_SRT_DATA_ONLY",batch["text"])
        self.assertIn("PACKET_SHA256=",batch["text"])
        self.assertIn("PRIMARY=",batch["text"])
        self.assertEqual(batch["batch_number"],1)
        self.assertNotIn("full approved financial truth",batch["text"])

    def test_render_rejects_fully_rehashed_fake_original(self):
        full=prepare_all_source_packets(self.queue,max_packets=2,max_chars=30000)
        fake=copy.deepcopy(full)
        victim=fake["batches"][0]["packets"][0]["packet"]
        victim["primary_cues"][0]["text"]="FALSE SOURCE THAT DID NOT EXIST"
        victim["packet_sha256"]=sha256(_canonical({k:v for k,v in victim.items()
                                                   if k!="packet_sha256"}))
        target=fake["batches"][0]
        identity={"schema":target["schema"],
                  "batch_fingerprint":fake["source_batch_fingerprint"],
                  "window_identity":[[r["video_id"],r["packet"]["packet_sha256"]]
                                     for r in target["packets"]]}
        target["batch_sha256"]=sha256(_canonical(identity))
        fake["plan_sha256"]=sha256(_canonical({k:v for k,v in fake.items()
                                               if k!="plan_sha256"}))
        cp=compact_source_plan(fake)
        with self.assertRaisesRegex(ValueError,"NOT_CURRENT_ORIGINAL"):
            render_private_batch_for_chat(self.queue,cp,1)

    def test_render_rejects_stale_plan_after_new_checkpoint(self):
        full=prepare_all_source_packets(self.queue,max_packets=2,max_chars=30000)
        cp=compact_source_plan(full)
        run_one_turn(self.queue,self.full,max_packets=1,max_chars=30000,max_rounds=1)
        with self.assertRaisesRegex(ValueError,"NOT_CURRENT_ORIGINAL"):
            verify_compact_plan_against_current_original(self.queue,cp)

    def test_render_no_source_text_leaked_by_cli(self):
        import subprocess,sys,json
        manifest=self.fixture.root/"manifest.json"
        manifest.write_text(json.dumps(self.fixture.manifest))
        plan=self.fixture.root/"source_plan"/"compact.json"
        rendered=self.fixture.root/"rendered"/"batch1.json"
        a=subprocess.run([sys.executable,"-m","ire.v3_one_turn","prepare",
                          "--private-manifest",str(manifest),
                          "--private-packets-file",str(plan),"--compact",
                          "--max-packets","2","--max-chars","30000"],
                          capture_output=True,text=True)
        self.assertEqual(a.returncode,0,a.stdout+a.stderr)
        b=subprocess.run([sys.executable,"-m","ire.v3_one_turn","render",
                          "--private-manifest",str(manifest),
                          "--private-packets-file",str(plan),
                          "--private-rendered-file",str(rendered),
                          "--batch-number","1"],capture_output=True,text=True)
        self.assertEqual(b.returncode,0,b.stdout+b.stderr)
        self.assertNotIn("primary_cues",b.stdout)
        self.assertNotIn("채권",b.stdout)
        self.assertNotIn("synthetic",b.stdout.lower())
        payload=json.loads(rendered.read_text())
        self.assertTrue(payload["source_text_untrusted"].startswith(
            "IRE_SOURCE_CUE_LEDGER_FOR_CURRENT_CHAT_V1"))
        self.assertEqual(rendered.stat().st_mode & 0o077,0)

    def test_reason_dictionary_mismatch(self):
        forged=copy.deepcopy(self.compact)
        forged["reasons"].append(forged["reasons"][0])
        with self.assertRaisesRegex(ValueError,"REASONS_OR_COUNT"):
            expand_compact_bundle(self.queue,forged)


if __name__=="__main__":
    unittest.main()