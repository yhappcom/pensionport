"""Five-video coordinator tests. Synthetic speech never counts as real finance research."""
from __future__ import annotations
import copy
import json
import tempfile
import unittest
from pathlib import Path
from ire.v5.engine import sha256, RunError
from ire.v5.batch import FiveVideoResearchBatch


def fixture_video(n):
    vid=f"V5TEST{n:05d}"
    lines=[]
    for i in range(1,5):
        t=i*3
        lines.append(f"{i}\n00:00:{t:02d},000 --> 00:00:{t+1:02d},000\n"
                     f"Pension scenario {n} condition {i} needs confirmation.\n")
    raw="\n".join(lines).encode()
    win=[]
    for k,start in enumerate((1,3),1):
        ids=[start,start+1]
        content=" ".join(f"Pension scenario {n} condition {i} needs confirmation."
                         for i in ids)
        win.append({"window_id":f"W{k:05d}","primary_cue_ids":ids,
                    "primary_text_sha256":sha256(content.encode())})
    man={"schema":"IRE_V5_SOURCE_PLAN_V1","video_id":vid,
         "source_sha256":sha256(raw),"source_cues":4,
         "planner_version":"IRE_V5_TEST_WINDOWS_1",
         "prior_baseline_git_blob_sha":"a"*40,
         "active_window_ids":[w["window_id"] for w in win],"windows":win}
    return {"source":raw,"manifest":man}


class FiveVideoBatchTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.path=Path(t.name)/"private"
        self.inputs=[fixture_video(i) for i in range(1,6)]
        self.b=FiveVideoResearchBatch("research-20261104-five",self.inputs,self.path)

    def actions(self,vid,k=1):
        run=self.b.runs[vid]
        p=run.packet(f"W{k:05d}")
        refs=[{"cue_index":r["cue_index"],"quote":r["text"]} for r in p["cues"]]
        cid=f"V5C{k:04d}"
        model={"schema":"IRE_V5_MODEL_WINDOW_V1","window_id":f"W{k:05d}",
               "packet_sha256":p["packet_sha256"],
               "claimed_author":"CURRENT_CHATGPT_CONVERSATION",
               "independent_human_verified":False,
               "claims":[{"claim_id":cid,"kind":"PERSONAL_CASE",
                    "proposition":"A hypothetical pension example requires personal confirmation.",
                    "requires_external_verification":True,
                    "fact_verified":False,"advisory_approved":False,
                    "source_refs":refs}],
               "cue_dispositions":[{"cue_index":r["cue_index"],"status":"LINKED",
                    "claim_ids":[cid],"reason":None} for r in p["cues"]]}
        evidence={"schema":"IRE_V5_EVIDENCE_CASE_V1","claim_id":cid,
                  "status":"OPEN_PERSONAL_DATA","search_query":"official personal pension rule",
                  "investigation_summary":"Source eligibility could not be individually verified.",
                  "financial_truth_approved":False,"open_reason":"Person-specific data unavailable."}
        relation={"schema":"IRE_V5_PRIOR_RELATION_V1","claim_id":cid,
                  "prior_baseline_git_blob_sha":"a"*40,"prior_claim_ids":[],
                  "status":"NO_RELEVANT_PRIOR_WITH_SEARCH","search_terms":["pension"],
                  "review_notes":"Synthetic historical baseline search returned no comparable exact claim.",
                  "automerge":False,"financial_truth_approved":False}
        return [{"type":"MODEL_ANALYSIS","payload":model},
                {"type":"EVIDENCE_REVIEW","payload":evidence},
                {"type":"PRIOR_RELATION_REVIEW","payload":relation}]

    def test_five_sources_locked_and_reopened(self):
        status=self.b.status()
        self.assertEqual(status["video_count"],5)
        self.assertEqual(status["windows_total"],10)
        self.assertEqual(status["windows_processed"],0)
        self.assertEqual(status["source_cues"],20)
        self.assertEqual(FiveVideoResearchBatch.open_private(self.path).status(),status)
        self.assertFalse(status["all_videos_research_reports_sealed"])

    def test_four_sources_supported_not_six_or_three(self):
        with tempfile.TemporaryDirectory() as temp:
            b=FiveVideoResearchBatch("four-videos",self.inputs[:4],Path(temp)/"new")
            self.assertEqual(b.status()["video_count"],4)
        with self.assertRaisesRegex(RunError,"FIVE_VIDEO_REQUIRES_FOUR_OR_FIVE_SOURCES"):
            FiveVideoResearchBatch("invalid-three",self.inputs[:3],self.path)

    def test_round_robin_all_five_and_budget(self):
        data=self.b.next_source_bundle(max_windows=5,max_chars=12000)
        self.assertEqual(len(data["windows"]),5)
        self.assertEqual([x["video_id"] for x in data["windows"]],self.b.video_order)
        self.assertTrue(all(x["packet"]["window_id"]=="W00001" for x in data["windows"]))
        self.assertFalse(data["all_video_source_work_complete"])
        self.assertFalse(data["user_continue_requested"])

    def test_five_video_event_batches_single_receipt_each(self):
        req=[{"video_id":vid,"actions":self.actions(vid)} for vid in self.b.video_order]
        result=self.b.submit_multi_video(req)
        self.assertEqual(result["batch_state"]["windows_processed"],5)
        self.assertEqual(sum(x["event_receipts"] for x in result["batch_state"]["videos"]),5)
        self.assertFalse(result["batch_state"]["all_videos_research_reports_sealed"])
        self.assertFalse(result["cross_video_commit_atomic"])
        self.assertEqual(len(self.b.next_review_bundle()["claims"]),0)
        self.assertEqual(FiveVideoResearchBatch.open_private(self.path).status(),self.b.status())
        new_tasks=self.b.next_source_bundle(max_windows=5,max_chars=12000)
        self.assertTrue(all(x["packet"]["window_id"]=="W00002" for x in new_tasks["windows"]))

    def test_replay_bundle_idempotent(self):
        vid=self.b.video_order[0]
        actions=self.actions(vid)
        first=self.b.submit_video_bundle(vid,actions)
        second=self.b.submit_video_bundle(vid,actions)
        self.assertTrue(first["accepted_now"])
        self.assertFalse(second["accepted_now"])
        self.assertTrue(second["previously_committed"])
        self.assertEqual(first["event_sha256"],second["event_sha256"])
        out=self.b.submit_multi_video([{"video_id":vid,"actions":actions}])
        self.assertFalse(out["receipts"][0]["accepted_now"])
        self.assertEqual(self.b.status()["windows_processed"],1)

    def test_invalid_second_video_preflights_nothing_written(self):
        a=self.actions(self.b.video_order[0])
        b=self.actions(self.b.video_order[1])
        b[0]["payload"]["claims"][0]["source_refs"][0]["quote"]="invented speech"
        requests=[{"video_id":self.b.video_order[0],"actions":a},
                  {"video_id":self.b.video_order[1],"actions":b}]
        with self.assertRaisesRegex(RunError,"MODEL_HALO_OR_FABRICATED_QUOTE"):
            self.b.submit_multi_video(requests)
        self.assertEqual(self.b.status()["windows_processed"],0)
        self.assertEqual(sum(x["event_receipts"] for x in self.b.status()["videos"]),0)

    def test_malformed_inner_event_rejected(self):
        vid=self.b.video_order[0]
        actions=self.actions(vid)
        actions.append({"type":"RESEARCH_CLOSURE","payload":{}})
        with self.assertRaisesRegex(RunError,"BATCH_ACTION_TYPE_NOT_ALLOWED"):
            self.b.submit_video_bundle(vid,actions)
        self.assertEqual(self.b.status()["windows_processed"],0)

    def test_evidence_requires_quote_and_prior_after_model(self):
        vid=self.b.video_order[0]
        actions=self.actions(vid)
        with self.assertRaisesRegex(RunError,"EVIDENCE_CLAIM_NOT_ANALYZED"):
            self.b.submit_video_bundle(vid,actions[1:])
        self.assertEqual(self.b.status()["windows_processed"],0)

    def test_claim_review_bundle_after_model_only(self):
        vid=self.b.video_order[0]
        self.b.submit_video_bundle(vid,self.actions(vid)[:1])
        r=self.b.next_review_bundle()
        self.assertEqual(r["outstanding_claims_total"],1)
        self.assertTrue(r["claims"][0]["needs_evidence_review"])
        self.assertTrue(r["claims"][0]["needs_prior_relation_review"])
        self.assertFalse(r["financial_fact_approved"])

    def test_five_full_closures_still_not_advisory_approval(self):
        for k in (1,2):
            req=[{"video_id":vid,"actions":self.actions(vid,k)} for vid in self.b.video_order]
            self.b.submit_multi_video(req)
        for vid in self.b.video_order:
            self.b.runs[vid].close()
        result=self.b.status()
        self.assertTrue(result["all_videos_research_reports_sealed"])
        self.assertEqual(result["videos_full_scope_sealed"],5)
        self.assertFalse(result["one_chat_turn_semantic_execution_proven"])
        self.assertEqual(result["official_financial_facts_approved"],0)
        self.assertIn("NO_GO",result["p0_five_video_one_turn_release"])

    def test_manifest_tampering_and_duplicate_source(self):
        tampered=copy.deepcopy(self.inputs)
        tampered[1]["manifest"]["video_id"]=tampered[0]["manifest"]["video_id"]
        with self.assertRaises(RunError):
            FiveVideoResearchBatch("dup-video",tampered,self.path)
        current=self.path/"videos"/self.b.video_order[0]/"private_source.srt"
        current.write_bytes(b"FAKED SOURCE")
        with self.assertRaisesRegex(RunError,"FIVE_VIDEO_ORIGINAL_SOURCE_MISMATCH"):
            FiveVideoResearchBatch.open_private(self.path)

if __name__=="__main__": unittest.main()
