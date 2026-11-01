"""V2 entire source -> conversation -> knowledge -> evidence -> advisory contract.

Synthetic originals only. No prior investment claims, authentic human review,
public API model calls, or financial fact approvals are simulated as real.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ire.source import sha256
from ire.chat_bridge import ConversationResearchSession
from ire.knowledge import empty_knowledge,read_private_snapshot
from ire.v2_run import inspect_manifest,finalize_batch
from ire.v2_evidence import (
    empty_evidence_ledger,validate_evidence_ledger,apply_chat_evidence,
    reconcile_ledger_with_updated_knowledge,advisory_evidence_context,
    save_private_evidence)
from ire.evidence import independently_fetch_candidate
from test_engine import VID,annotations,synthetic_srt
from test_semantics import synthetic_reply


VIDEO2="Qq12345AbCd"
DOCUMENT_URL="https://www.bok.or.kr/portal/synthetic-scope-test"
DOCUMENT_TEXT=(
    "이 문서는 실제 정부 공지가 아니며, 새로 만든 합성 시험용 텍스트입니다. "
    "가상의 상품 A는 계약 조건에 따라 매년 비용이 달라질 수 있습니다. "
    "수수료 예시는 실제 금융 사실을 입증하지 않습니다. "
)*4


def fresh_session(raw,video,root,fully=True):
    digest=sha256(raw)
    source=root/(video+".srt")
    source.write_bytes(raw)
    directory=root/(video+"_sessions")
    session=ConversationResearchSession(raw,video,digest,str(directory))
    if fully:
        while (packet:=session.next_packet()) is not None:
            reply=synthetic_reply(annotations(digest))
            session.accept({
                "schema":"IRE_CHAT_WINDOW_ANSWER_V1",
                "session_id":packet["session_id"],
                "window_id":packet["window_id"],
                "packet_sha256":packet["packet_sha256"],
                "claims":reply["claims"],
                "cue_dispositions":reply["cue_dispositions"]
            })
        session.finalize()
    return {
        "video_id":video,
        "original_srt_path":str(source),
        "source_sha256":digest,
        "private_chat_sessions_path":str(directory)
    }


def manifest(*rows):
    return {
        "schema":"IRE_V2_CHAT_BATCH_V1",
        "research_as_of":"2026-11-01",
        "videos":list(rows)
    }


def source_doc():
    def download(url):
        return ("<html><body>"+DOCUMENT_TEXT+"</body></html>").encode(
            "utf-8"),"text/html; charset=utf-8",url
    return independently_fetch_candidate(
        DOCUMENT_URL,read_fn=download,fetched_at="2026-11-01T00:00:00Z")


def judgment(claim_id,doc,quote="가상의 상품 A는 계약 조건에 따라 매년 비용이 달라질 수 있습니다.",
             verdict="SUPPORTS",when="2026-01-01",until=None):
    return {
        "schema":"IRE_CHAT_EVIDENCE_REVIEW_V2",
        "global_claim_id":claim_id,
        "document_url":doc["canonical_url"],
        "document_sha256":doc["raw_sha256"],
        "document_text_sha256":doc["visible_text_sha256"],
        "source_quote":quote,"verdict":verdict,
        "scope":{
            "jurisdiction":"MATCH","effective_date":"MATCH",
            "conditions":"MATCH","exceptions":"MATCH","numbers":"MATCH"},
        "effective_from":when,"effective_until":until,
        "chat_reviewer_mode":"CURRENT_CHATGPT_CONVERSATION"
    }


class IntegratedSystemV2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.raw,self.sha=synthetic_srt()
        self.raw2=self.raw.replace(
            "상품 비용은".encode("utf-8"),"이 상품 비용은".encode("utf-8"))
        self.item1=fresh_session(self.raw,VID,self.root)
        self.item2=fresh_session(self.raw2,VIDEO2,self.root)
        self.batch=manifest(self.item1,self.item2)

    def complete(self, batch=None,prior=None, evidence=None):
        return finalize_batch(
            batch or self.batch,prior,str(self.root/"long_term_knowledge"),
            str(self.root/"batch_audits"),evidence,
            str(self.root/"source_reviews") if evidence is not None else None)

    def test_one_request_both_videos_completes_source_join_not_factual_truth(self):
        plan=inspect_manifest(self.batch)
        self.assertEqual(plan["requested_video_count"],2)
        self.assertEqual(plan["total_cues"],8)
        self.assertEqual(plan["remaining_windows"],0)
        result=self.complete()
        self.assertEqual(result["final_research_status"],
                         "SOURCE_ANALYSIS_COMPLETE_EVIDENCE_PENDING")
        self.assertEqual(result["knowledge_source_count"],2)
        self.assertEqual(result["cumulative_unverified_claims"],4)
        self.assertGreaterEqual(result["relation_candidates_added"],2)
        self.assertTrue(Path(result["audit_path"]).exists())
        self.assertEqual(Path(result["audit_path"]).stat().st_mode & 0o077,0)
        persisted=read_private_snapshot(
            result["private_knowledge_snapshot_path"])
        self.assertEqual(persisted["version"],2)
        self.assertFalse(result["financial_advice_released"])
        self.assertEqual(result["financial_facts_automatically_approved"],0)
        self.assertEqual(result["model_api_calls"],0)
        self.assertEqual(result["windows_accounted_for"],2)

    def test_missing_context_blocks_entire_batch_knowledge_commit(self):
        partial=copy.deepcopy(self.batch)
        row=fresh_session(
            self.raw.replace("상품 비용은".encode("utf-8"),
                             "별도 상품 비용은".encode("utf-8")),"Zz12345AbCd",
            self.root,fully=False)
        partial["videos"].append(row)
        result=self.complete(partial)
        self.assertEqual(result["final_research_status"],
                         "INCOMPLETE_REQUIRES_RESUME")
        self.assertIsNone(result["private_knowledge_snapshot_path"])
        self.assertEqual(list((self.root/"long_term_knowledge").glob(
            "ire_knowledge_v*.json")),[])
        self.assertGreater(result["windows_total"],
                           result["windows_accounted_for"])
        self.assertIn("SOURCE_WINDOWS_NOT_ALL_ASSESSED",result["blockers"])

    def test_failure_on_second_original_does_not_commit_partial_knowledge(self):
        corrupt=copy.deepcopy(self.batch)
        corrupt["videos"][1]["source_sha256"]=sha256(b"tampered")
        with self.assertRaisesRegex(ValueError,
                                    "V2_BATCH_ORIGINAL_SHA_MISMATCH"):
            self.complete(corrupt)
        self.assertEqual(list((self.root/"long_term_knowledge").glob(
            "ire_knowledge_v*.json")),[])

    def test_unchanged_snapshot_not_used_as_new_semantic_gold(self):
        first=self.complete(manifest(self.item1))
        before=read_private_snapshot(first["private_knowledge_snapshot_path"])
        second=self.complete(manifest(self.item2),prior=before)
        after=read_private_snapshot(second["private_knowledge_snapshot_path"])
        self.assertEqual(after["version"],2)
        self.assertEqual(after["parent_sha256"],before["snapshot_sha256"])
        self.assertEqual(after["claims"][:2],before["claims"])
        self.assertEqual(second["financial_facts_automatically_approved"],0)
        self.assertGreaterEqual(second["relation_candidates_added"],2)

    def test_mutated_sealed_chat_report_is_rejected(self):
        session=ConversationResearchSession(
            self.raw,VID,self.sha,self.item1["private_chat_sessions_path"])
        target=session.folder/"final_report.json"
        obj=json.loads(target.read_text())
        obj["annotations"]["claims"][0]["proposition"]="아무 근거 없는 수정"
        target.write_text(json.dumps(obj,ensure_ascii=False))
        with self.assertRaisesRegex(ValueError,"V2_SEALED_CHAT_REPORT_CHANGED"):
            self.complete()
        self.assertEqual(list((self.root/"long_term_knowledge").glob(
            "ire_knowledge_v*.json")),[])

    def test_evidence_quote_checked_and_financial_truth_not_approved(self):
        outcome=self.complete()
        knowledge=read_private_snapshot(
            outcome["private_knowledge_snapshot_path"])
        ledger=empty_evidence_ledger(knowledge)
        document=source_doc()
        identity=knowledge["claims"][0]["global_claim_id"]
        record=apply_chat_evidence(
            ledger,knowledge,document,judgment(identity,document))
        self.assertEqual(record["version"],1)
        validate_evidence_ledger(record,knowledge)
        self.assertEqual(record["assessments"][0]["actual_network_fetch"],False)
        self.assertEqual(record["assessments"][0]["assessment_label"],
                         "CHAT_ASSESSMENT_WITH_SYNTHETIC_SOURCE")
        self.assertFalse(record["assessments"][0]["finance_truth_approved"])
        context=advisory_evidence_context(
            knowledge,record,"상품 비용과 계약 조건을 분석해 주세요",
            "2026-11-01")
        self.assertEqual(context["certified_independent_financial_facts"],0)
        self.assertEqual(context["actionable_recommendations"],[])
        self.assertEqual(context["plausibly_corroborated_official_text_count"],0)
        self.assertEqual(len(context["evidence_assessments_for_hits"]),1)
        self.assertFalse(context["advice_usable_without_latest_official_recheck"])
        store=save_private_evidence(record,knowledge,str(self.root/"evidence"))
        self.assertEqual(Path(store).stat().st_mode & 0o077,0)

    def test_invented_official_quote_and_false_human_review_blocked(self):
        result=self.complete()
        knowledge=read_private_snapshot(
            result["private_knowledge_snapshot_path"])
        document=source_doc()
        identity=knowledge["claims"][0]["global_claim_id"]
        record=empty_evidence_ledger(knowledge)
        bad=judgment(identity,document,quote="국가에서 100% 원금을 보장합니다.")
        with self.assertRaisesRegex(ValueError,
                                    "V2_EVIDENCE_QUOTE_NOT_IN_FETCHED_ORIGINAL"):
            apply_chat_evidence(record,knowledge,document,bad)
        bad=judgment(identity,document)
        bad["chat_reviewer_mode"]="INDEPENDENT_HUMAN"
        with self.assertRaisesRegex(ValueError,
                                    "V2_EVIDENCE_FALSE_REVIEWER_IDENTITY"):
            apply_chat_evidence(record,knowledge,document,bad)

    def test_expired_or_unknown_effective_date_not_current_advisory_evidence(self):
        result=self.complete()
        knowledge=read_private_snapshot(
            result["private_knowledge_snapshot_path"])
        document=source_doc()
        identity=knowledge["claims"][0]["global_claim_id"]
        record=apply_chat_evidence(
            empty_evidence_ledger(knowledge),knowledge,document,
            judgment(identity,document,
                     when="2025-01-01",until="2025-12-31"))
        context=advisory_evidence_context(
            knowledge,record,"상품 비용과 계약 조건을 확인해 주세요",
            "2026-11-01")
        self.assertFalse(context["evidence_assessments_for_hits"][0][
            "effective_on_question_date"])
        self.assertEqual(context["plausibly_corroborated_official_text_count"],0)

    def test_evidence_survives_new_video_version_without_approval(self):
        first=self.complete(manifest(self.item1))
        kb1=read_private_snapshot(first["private_knowledge_snapshot_path"])
        doc=source_doc()
        claim_id=kb1["claims"][0]["global_claim_id"]
        evidence=apply_chat_evidence(
            empty_evidence_ledger(kb1),kb1,doc,judgment(claim_id,doc))
        second=self.complete(manifest(self.item2),prior=kb1,evidence=evidence)
        kb2=read_private_snapshot(second["private_knowledge_snapshot_path"])
        evidence2=reconcile_ledger_with_updated_knowledge(evidence,kb1,kb2)
        self.assertEqual(evidence2["knowledge_snapshot_sha256"],
                         kb2["snapshot_sha256"])
        self.assertEqual(evidence2["assessments"][0]["global_claim_id"],claim_id)
        self.assertEqual(evidence2["finance_truth_auto_approved"],0)
        self.assertEqual(second["evidence_assessment_count"],1)

    def test_private_one_command_plan_and_finalize(self):
        path=self.root/"source_manifest.json"
        path.write_text(json.dumps(self.batch,ensure_ascii=False))
        cmd=[sys.executable,"-m","ire.v2_run"]
        ready=subprocess.run(cmd+["plan","--private-manifest",str(path)],
            capture_output=True,text=True,check=False)
        self.assertEqual(ready.returncode,0,ready.stderr+ready.stdout)
        info=json.loads(ready.stdout)
        self.assertTrue(info["all_source_windows_completed"])
        final=subprocess.run(
            cmd+["finalize","--private-manifest",str(path),
                 "--private-knowledge-dir",str(self.root/"kb"),
                 "--private-audit-dir",str(self.root/"reports")],
            capture_output=True,text=True,check=False)
        self.assertEqual(final.returncode,2,final.stderr+final.stdout)
        brief=json.loads(final.stdout)
        self.assertEqual(brief["requested_sources"],2)
        self.assertEqual(brief["financial_facts_automatically_approved"],0)
        self.assertNotIn("상품 비용은",final.stdout)


    def test_one_user_batch_five_sources_integrates_all_and_preserves_context(self):
        originals=[]
        video_ids=["Aa000000001","Bb000000002","Cc000000003",
                   "Dd000000004","Ee000000005"]
        for i,video in enumerate(video_ids):
            raw=self.raw.replace(
                "상품 비용은".encode("utf-8"),
                (f"새로운 사례 {i} 상품 비용은").encode("utf-8"))
            originals.append(fresh_session(raw,video,self.root))
        five=manifest(*originals)
        plan=inspect_manifest(five)
        self.assertEqual(plan["requested_video_count"],5)
        self.assertEqual(plan["total_cues"],20)
        self.assertEqual(plan["remaining_windows"],0)
        out=self.complete(five)
        self.assertEqual(out["knowledge_source_count"],5)
        self.assertEqual(out["new_atomic_claims"],10)
        self.assertEqual(out["cumulative_unverified_claims"],10)
        self.assertEqual(out["final_research_status"],
                         "SOURCE_ANALYSIS_COMPLETE_EVIDENCE_PENDING")
        self.assertGreater(out["relation_candidates_added"],0)
        self.assertEqual(out["model_api_calls"],0)
        self.assertEqual(out["financial_facts_automatically_approved"],0)
        saved=read_private_snapshot(out["private_knowledge_snapshot_path"])
        self.assertEqual(saved["version"],5)
        self.assertEqual({s["video_id"] for s in saved["source_register"]},
                         set(video_ids))
        self.assertEqual(len(saved["claims"]),10)



    def test_reusing_stale_knowledge_snapshot_fails_before_commit(self):
        first=self.complete(manifest(self.item1))
        prior=read_private_snapshot(first["private_knowledge_snapshot_path"])
        second=self.complete(manifest(self.item2),prior=prior)
        self.assertEqual(second["knowledge_source_count"],2)
        previous_count=len(list((self.root/"long_term_knowledge").glob(
            "ire_knowledge_v*.json")))
        with self.assertRaisesRegex(ValueError,
                                    "V2_BATCH_STALE_PRIOR_KNOWLEDGE_SNAPSHOT"):
            self.complete(manifest(self.item2),prior=prior)
        self.assertEqual(len(list((self.root/"long_term_knowledge").glob(
            "ire_knowledge_v*.json"))),previous_count)

    def test_existing_evidence_ledger_cannot_be_silently_discarded(self):
        first=self.complete(manifest(self.item1))
        kb=read_private_snapshot(first["private_knowledge_snapshot_path"])
        empty=empty_evidence_ledger(kb)
        folder=str(self.root/"source_reviews")
        save_private_evidence(empty,kb,folder)
        with self.assertRaisesRegex(ValueError,
                                    "V2_BATCH_PRIOR_EVIDENCE_SNAPSHOT_REQUIRED"):
            finalize_batch(
                manifest(self.item2),kb,
                str(self.root/"long_term_knowledge"),
                str(self.root/"batch_audits"),
                prior_evidence=None,private_evidence_dir=folder)
        self.assertEqual(len(list((self.root/"long_term_knowledge").glob(
            "ire_knowledge_v*.json"))),1)


if __name__=="__main__":
    unittest.main()
