"""Cross-video knowledge and advisory regression; all fixtures are synthetic."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ire.chat_bridge import ConversationResearchSession
from ire.knowledge import (
    SCHEMA,advisory_research_context,empty_knowledge,fingerprint,
    ingest_new_video,read_private_snapshot,save_private_snapshot,
    validate_knowledge)
from ire.source import sha256
from test_engine import VID,annotations,synthetic_srt
from test_semantics import synthetic_reply

OTHER_ID="Yy012345678"


def make_report(raw:bytes, video_id:str, work:Path) -> dict:
    digest=sha256(raw)
    session=ConversationResearchSession(raw,video_id,digest,str(work))
    while (packet:=session.next_packet()) is not None:
        annotation=annotations(digest)
        answer=synthetic_reply(annotation)
        result=session.accept({
            "schema":"IRE_CHAT_WINDOW_ANSWER_V1",
            "session_id":packet["session_id"],
            "window_id":packet["window_id"],
            "packet_sha256":packet["packet_sha256"],
            "claims":answer["claims"],
            "cue_dispositions":answer["cue_dispositions"]})
        assert result["accepted_windows"]>0
    detail=session.finalize()
    return json.loads(Path(detail["private_report_path"]).read_text())


class NewIreKnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.original,self.sha=synthetic_srt()
        self.new_original=self.original.replace(
            "상품 비용은".encode("utf-8"),
            "이 상품 비용은".encode("utf-8"))
        self.report1=make_report(self.original,VID,self.root/"video1")
        self.report2=make_report(self.new_original,OTHER_ID,
                                 self.root/"video2")

    def test_new_source_registry_then_cross_video_links_are_only_candidates(self):
        first=ingest_new_video(empty_knowledge(),self.original,self.report1)
        self.assertEqual(first["version"],1)
        self.assertEqual(len(first["claims"]),2)
        self.assertEqual(first["relation_candidates"],[])
        self.assertEqual(first["source_register"][0]["claim_count"],2)
        second=ingest_new_video(first,self.new_original,self.report2)
        self.assertEqual(second["version"],2)
        self.assertEqual(len(second["claims"]),4)
        self.assertEqual(len(second["source_register"]),2)
        self.assertGreaterEqual(len(second["relation_candidates"]),2)
        self.assertEqual(second["parent_sha256"],first["snapshot_sha256"])
        self.assertEqual(second["claims"][:2],first["claims"])
        self.assertTrue(all(
            x["review_status"]=="PENDING_SEPARATE_ADJUDICATION"
            for x in second["relation_candidates"]))
        self.assertTrue(all(
            x["knowledge_status"]=="UNVERIFIED_REVIEW_REQUIRED"
            for x in second["claims"]))
        self.assertEqual(second["automatic_financial_approvals"],0)
        validate_knowledge(second)

    def test_no_automatic_research_or_advisory_certification(self):
        first=ingest_new_video(empty_knowledge(),self.original,self.report1)
        second=ingest_new_video(first,self.new_original,self.report2)
        context=advisory_research_context(
            second,"상품 비용에 따른 투자 판단을 검토해주세요","2026-11-01",
            investor_profile={"investment_horizon_years":10,
                              "risk_tolerance":"moderate"})
        self.assertGreater(context["knowledge_claim_count"],0)
        self.assertGreater(len(context["unverified_relevant_claims"]),0)
        self.assertGreater(len(context["possible_cross_video_conflicts_or_updates"]),0)
        self.assertEqual(context["actionable_recommendations"],[])
        self.assertEqual(context["independent_verified_citable_claim_count"],0)
        self.assertEqual(context["advisory_output_status"],
                         "RESEARCH_CONTEXT_ONLY_NOT_ACTIONABLE_ADVICE")
        self.assertTrue(context["fresh_official_source_reverification_required"])
        self.assertTrue(context["investor_suitability_reconfirmation_required"])
        self.assertEqual(context["unverified_relevant_claims"][0][
            "claim_not_independently_factual_verified"],True)

    def test_same_source_is_never_double_counted(self):
        state=ingest_new_video(empty_knowledge(),self.original,self.report1)
        with self.assertRaisesRegex(ValueError,
                                    "KNOWLEDGE_REUSED_ORIGINAL_BYTES_NO_DOUBLECOUNT"):
            ingest_new_video(state,self.original,self.report1)
        with self.assertRaisesRegex(ValueError,
                                    "KNOWLEDGE_SOURCE_VIDEO_ID_ALREADY_REGISTERED"):
            ingest_new_video(state,self.new_original,self.report2 | {
                "video_id":VID,
                "annotations":self.report2["annotations"] | {"video_id":VID}
            })

    def test_different_timestamps_same_content_cannot_fake_new_knowledge(self):
        altered=self.original.replace(b"00:00:00,000",b"00:00:00,100")
        self.assertNotEqual(sha256(altered),self.sha)
        new_report=make_report(altered,OTHER_ID,self.root/"different_timing")
        state=ingest_new_video(empty_knowledge(),self.original,self.report1)
        with self.assertRaisesRegex(ValueError,
                                    "KNOWLEDGE_DUPLICATE_TRANSCRIPT_BODY"):
            ingest_new_video(state,altered,new_report)

    def test_old_report_or_partial_chat_cannot_enter_knowledge(self):
        state=empty_knowledge()
        corrupt=copy.deepcopy(self.report1)
        corrupt["all_primary_windows_submitted"]=False
        with self.assertRaisesRegex(ValueError,
                                    "KNOWLEDGE_REQUIRES_COMPLETE_NEW_CHAT_SOURCE_REPORT"):
            ingest_new_video(state,self.original,corrupt)
        corrupt=copy.deepcopy(self.report1)
        corrupt["schema"]="HISTORICAL_OLD_STUDY_REPORT"
        with self.assertRaisesRegex(ValueError,
                                    "KNOWLEDGE_REQUIRES_COMPLETE_NEW_CHAT_SOURCE_REPORT"):
            ingest_new_video(state,self.original,corrupt)
        corrupt=copy.deepcopy(self.report1)
        corrupt["financial_facts_approved"]=2
        with self.assertRaisesRegex(ValueError,
                                    "KNOWLEDGE_REQUIRES_COMPLETE_NEW_CHAT_SOURCE_REPORT"):
            ingest_new_video(state,self.original,corrupt)

    def test_old_study_import_flags_and_fake_verified_status_rejected(self):
        state=ingest_new_video(empty_knowledge(),self.original,self.report1)
        tampered=copy.deepcopy(state)
        tampered["old_research_knowledge_imported"]=True
        with self.assertRaisesRegex(ValueError,"KNOWLEDGE_SNAPSHOT_TAMPERED"):
            validate_knowledge(tampered)
        body=copy.deepcopy(state)
        body["claims"][0]["knowledge_status"]="CONFIRMED"
        base={k:v for k,v in body.items() if k!="snapshot_sha256"}
        body["snapshot_sha256"]=fingerprint(base)
        with self.assertRaisesRegex(ValueError,"KNOWLEDGE_SILENT_FACT_APPROVAL_DENIED"):
            validate_knowledge(body)

    def test_private_snapshots_are_immutable_versioned_and_verified(self):
        state=empty_knowledge()
        folder=str(self.root/"private_snapshots")
        first=save_private_snapshot(state,folder)
        self.assertTrue(Path(first).is_file())
        self.assertEqual(Path(first).stat().st_mode & 0o077,0)
        with self.assertRaisesRegex(ValueError,"KNOWLEDGE_SNAPSHOT_OVERWRITE_FORBIDDEN"):
            save_private_snapshot(state,folder)
        again=read_private_snapshot(first)
        self.assertEqual(again["snapshot_sha256"],state["snapshot_sha256"])
        second=ingest_new_video(again,self.original,self.report1)
        next_path=save_private_snapshot(second,folder)
        self.assertNotEqual(first,next_path)
        self.assertTrue(Path(first).exists())
        Path(next_path).write_text(Path(next_path).read_text().replace(
            "UNVERIFIED_REVIEW_REQUIRED","CONFIRMED"))
        with self.assertRaisesRegex(ValueError,"KNOWLEDGE_SNAPSHOT_TAMPERED"):
            read_private_snapshot(next_path)

    def test_one_command_knowledge_and_advisory_cli_without_api(self):
        folder=str(self.root/"kb")
        cmds=[sys.executable,"-m","ire.knowledge"]
        init=subprocess.run(cmds+["init","--private-directory",folder],
                            capture_output=True,text=True,check=False)
        self.assertEqual(init.returncode,0,init.stderr)
        prior=json.loads(init.stdout)["snapshot_path"]
        original=self.root/"source.srt"
        original.write_bytes(self.original)
        report=self.root/"chat_report.json"
        report.write_text(json.dumps(self.report1,ensure_ascii=False))
        with_source=subprocess.run(
            cmds+["ingest","--private-directory",folder,
                  "--prior-snapshot",prior,
                  "--original-srt",str(original),
                  "--chat-final-report",str(report)],
            capture_output=True,text=True,check=False)
        self.assertEqual(with_source.returncode,2,with_source.stderr+with_source.stdout)
        result=json.loads(with_source.stdout)
        self.assertEqual(result["claim_count"],2)
        self.assertEqual(result["automatically_approved_financial_facts"],0)
        advisory=subprocess.run(cmds+[
            "advisory","--private-directory",folder,
            "--prior-snapshot",result["snapshot_path"],
            "--question","상품 비용과 계약 조건은 어떻게 고려하나요?",
            "--as-of","2026-11-01"],
            capture_output=True,text=True,check=False)
        self.assertEqual(advisory.returncode,2,advisory.stderr+advisory.stdout)
        response=json.loads(advisory.stdout)
        self.assertEqual(response["actionable_recommendations"],[])
        self.assertTrue(response["no_previous_research_gold_imported"])

    def test_wrong_source_digest_and_provenance_rejected(self):
        state=empty_knowledge()
        corrupt=copy.deepcopy(self.report1)
        corrupt["source_sha256"]=sha256(b"falsified")
        with self.assertRaisesRegex(ValueError,"KNOWLEDGE_ORIGINAL_SHA_MISMATCH"):
            ingest_new_video(state,self.original,corrupt)
        corrupt=copy.deepcopy(self.report1)
        corrupt["annotations"]["claims"][0]["source_refs"][0]["quote"]="일 년에 무조건 100% 상승"
        with self.assertRaisesRegex(ValueError,"UNTRACEABLE_QUOTED_SOURCE"):
            ingest_new_video(state,self.original,corrupt)

    def test_advisory_time_and_profile_conditions_are_strict(self):
        state=empty_knowledge()
        with self.assertRaises(ValueError):
            advisory_research_context(state,"투자 자문 질문입니다.","2026-02-30")
        with self.assertRaisesRegex(ValueError,"ADVISORY_PROFILE_SCHEMA_INVALID"):
            advisory_research_context(state,"투자 자문 질문입니다.","2026-11-01",
                                      investor_profile={"account_password":"secret"})


    def test_chat_finalize_also_incrementally_integrates_knowledge(self):
        first_session=ConversationResearchSession(
            self.original,VID,self.sha,str(self.root/"video1"))
        folder=str(self.root/"long_lived_knowledge")
        first=first_session.finalize_and_integrate(
            empty_knowledge(),folder)
        self.assertEqual(first["knowledge_version"],1)
        self.assertEqual(first["cumulative_source_videos"],1)
        self.assertEqual(first["cumulative_unverified_atoms"],2)
        self.assertEqual(first["knowledge_approved_facts"],0)
        saved=read_private_snapshot(first["private_knowledge_snapshot_path"])
        second_session=ConversationResearchSession(
            self.new_original,OTHER_ID,sha256(self.new_original),
            str(self.root/"video2"))
        second=second_session.finalize_and_integrate(saved,folder)
        self.assertEqual(second["knowledge_version"],2)
        self.assertEqual(second["cumulative_source_videos"],2)
        self.assertEqual(second["cumulative_unverified_atoms"],4)
        self.assertGreaterEqual(second["cross_video_relation_candidates"],2)
        self.assertGreaterEqual(second["unverified_concept_clusters"],1)
        self.assertEqual(second["advisory_recommendations_automatically_approved"],0)
        self.assertTrue(Path(first["private_knowledge_snapshot_path"]).exists())
        self.assertTrue(Path(second["private_knowledge_snapshot_path"]).exists())
        self.assertNotEqual(first["private_knowledge_snapshot_path"],
                            second["private_knowledge_snapshot_path"])
        # This session is already registered in knowledge snapshot v1.
        with self.assertRaisesRegex(ValueError,
                                    "KNOWLEDGE_REUSED_ORIGINAL_BYTES_NO_DOUBLECOUNT"):
            first_session.finalize_and_integrate(saved,folder)

    def test_concept_topic_cluster_retains_scope_and_numeric_disagreement(self):
        from ire.knowledge import provisional_concept_index
        first=ingest_new_video(empty_knowledge(),self.original,self.report1)
        second=ingest_new_video(first,self.new_original,self.report2)
        topics=provisional_concept_index(second)
        shared=[t for t in topics if t["cross_video_topic"]]
        self.assertTrue(shared)
        self.assertTrue(all(
            t["status"]=="UNVERIFIED_TOPIC_CLUSTER_FOR_REVIEW"
            and t["canonical_verified_financial_conclusion"] is None
            and t["automatic_merge"] is False for t in shared))
        self.assertTrue(all(t["source_video_count"]==2 for t in shared))
        ctx=advisory_research_context(
            second,"상품의 계약 조건과 수수료는 어떻게 되나요?",
            "2026-11-01")
        self.assertTrue(ctx["provisional_integrated_topic_clusters"])
        self.assertEqual(ctx["actionable_recommendations"],[])

    def test_one_command_chat_finalize_integrates_or_fail_closes_on_prior_gap(self):
        # Prepare already-completed private chat reports from synthetic SRT.
        session=ConversationResearchSession(
            self.original,VID,self.sha,str(self.root/"video1"))
        original=self.root/"original.srt"
        original.write_bytes(self.original)
        folder=self.root/"chat_knowledge"
        cmd=[sys.executable,"-m","ire.chat_bridge","finalize",
             "--original-srt",str(original),
             "--video-id",VID,"--source-sha256",self.sha,
             "--private-session-dir",str(self.root/"video1"),
             "--private-knowledge-dir",str(folder)]
        first=subprocess.run(cmd,capture_output=True,text=True,check=False)
        self.assertEqual(first.returncode,2,first.stderr+first.stdout)
        response=json.loads(first.stdout)
        self.assertEqual(response["knowledge_version"],1)
        self.assertEqual(response["cumulative_source_videos"],1)
        no_prior=subprocess.run(cmd,capture_output=True,text=True,check=False)
        self.assertEqual(no_prior.returncode,3)
        self.assertEqual(json.loads(no_prior.stdout)["status"],"FAILED_CLOSED")



    def test_policy_scope_time_changes_are_review_flags_not_automatic_facts(self):
        old_report=copy.deepcopy(self.report1)
        new_report=copy.deepcopy(self.report2)
        old_report["annotations"]["claims"][0]["frame"]["effective_date"]="2026-01-01"
        new_report["annotations"]["claims"][0]["frame"]["effective_date"]="2027-01-01"
        first=ingest_new_video(empty_knowledge(),self.original,old_report)
        second=ingest_new_video(first,self.new_original,new_report)
        self.assertIn("POSSIBLE_TEMPORAL_RULE_CHANGE",
                      {x["candidate_type"] for x in second["relation_candidates"]})
        self.assertTrue(all(x["review_status"]=="PENDING_SEPARATE_ADJUDICATION"
                            for x in second["relation_candidates"]))
        self.assertEqual(second["automatic_financial_approvals"],0)

    def test_unreviewed_polarity_difference_never_becomes_verified_conflict(self):
        old_report=copy.deepcopy(self.report1)
        new_report=copy.deepcopy(self.report2)
        new_report["annotations"]["claims"][0]["frame"]["modality"]="NEGATION"
        first=ingest_new_video(empty_knowledge(),self.original,old_report)
        second=ingest_new_video(first,self.new_original,new_report)
        links=[x for x in second["relation_candidates"]
               if x["candidate_type"]=="POSSIBLE_NEGATION_CONFLICT"]
        self.assertTrue(links)
        self.assertTrue(all(not x.get("verified",False) for x in links))
        self.assertEqual(second["claims"][2]["knowledge_status"],
                         "UNVERIFIED_REVIEW_REQUIRED")



    def test_tampered_final_chat_report_cannot_enter_knowledge(self):
        session=ConversationResearchSession(
            self.original,VID,self.sha,str(self.root/"video1"))
        report_file=session.folder/"final_report.json"
        report=json.loads(report_file.read_text())
        report["annotations"]["claims"][0]["proposition"]="완전히 변경된 금융 명제"
        report_file.write_text(json.dumps(report,ensure_ascii=False))
        with self.assertRaisesRegex(ValueError,"CHAT_FINAL_REPORT_CONTENT_CHANGED"):
            session.finalize_and_integrate(
                empty_knowledge(),str(self.root/"private_kb_after_tamper"))


if __name__=="__main__":
    unittest.main()
