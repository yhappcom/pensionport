"""V3 P0-D/P1/P2 end-to-end synthetic and adversarial tests only.

These checks never substitute self-authored gold for genuine external judges,
and never certify investment advice as real-world accurate.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from ire.source import sha256
from ire.knowledge import empty_knowledge, ingest_new_video, fingerprint
from ire.v2_evidence import empty_evidence_ledger
from ire.v3_relation_review import (
    empty_relation_reviews, submit_relation_review,
    validate_relation_reviews, rebase_relation_reviews,
    relation_review_context, save_private_relation_reviews, discover_relation_candidate)
from ire.v3_relation_eval import (
    validate_relation_gold, evaluate_relation_retrieval)
from ire.v3_advisory import build_advisory_dossier
from ire.v3_advisory_eval import evaluate_advisory_cases
from ire.v3_orchestrator import ChatBatchQueue
from ire.v3_release import completion_gate
from test_knowledge import make_report, OTHER_ID
from test_engine import VID, synthetic_srt


class V3FullLifecycleTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.raw,self.digest=synthetic_srt()
        self.raw2=self.raw.replace("상품 비용은".encode(),"이 상품 비용은".encode())
        first=make_report(self.raw,VID,self.root/"one")
        second=make_report(self.raw2,OTHER_ID,self.root/"two")
        self.k1=ingest_new_video(empty_knowledge(),self.raw,first)
        self.k2=ingest_new_video(self.k1,self.raw2,second)
        self.relations=empty_relation_reviews(self.k2)
        self.evidence=empty_evidence_ledger(self.k2)
        self.pair=self.k2["relation_candidates"][0]
        self.claims={r["global_claim_id"]:r for r in self.k2["claims"]}
        self.report=lambda k: k["source_refs"][0]["quote"]
        self.manifest={
            "schema":"IRE_V2_CHAT_BATCH_V1","research_as_of":"2026-11-02",
            "videos":[{"video_id":VID,
                       "original_srt_path":str(self.root/"src.srt"),
                       "source_sha256":self.digest,
                       "private_chat_sessions_path":str(self.root/"sessions")}]}
        (self.root/"src.srt").write_bytes(self.raw)
        self.queue=ChatBatchQueue(self.manifest)

    def review(self):
        left=self.claims[self.pair["old_claim_id"]]
        right=self.claims[self.pair["new_claim_id"]]
        return {"schema":"IRE_V3_RELATION_REVIEW_SUBMISSION_V1",
                "relation_id":self.pair["relation_id"],
                "old_claim_id":left["global_claim_id"],
                "new_claim_id":right["global_claim_id"],
                "old_quote":self.report(left),
                "new_quote":self.report(right),
                "relation_label":"RELATED_DISTINCT",
                "source_first_explanation":"두 영상의 표현 차이를 확인했으나 금융 사실은 독립 검증되지 않았습니다.",
                "reviewed_as_of":"2026-11-02"}

    def gold(self):
        pair=self.pair
        return {
            "schema":"IRE_V3_RELATION_BLIND_GOLD_V1",
            "knowledge_snapshot_sha256":self.k2["snapshot_sha256"],
            "source_first_only":True,
            "predictions_unseen_during_gold":True,
            "reviewers":[
                {"reviewer_id":"syntheticR1",
                 "source_only_review_sha256":sha256(b"synthetic-1"),
                 "independent_from_model_attestation":True},
                {"reviewer_id":"syntheticR2",
                 "source_only_review_sha256":sha256(b"synthetic-2"),
                 "independent_from_model_attestation":True}],
            "adjudicator_id":"syntheticR3",
            "gold_sealed_at_utc":"2026-11-01T12:00:00Z",
            "complete_candidate_universe_attested":True,
            "queries":[{
                "new_claim_id":pair["new_claim_id"],
                "new_source_quote":self.report(self.claims[pair["new_claim_id"]]),
                "relevant_old_claims":[{
                    "old_claim_id":pair["old_claim_id"],
                    "old_source_quote":self.report(self.claims[pair["old_claim_id"]]),
                    "relation_type":"COMPLEMENT"}]
            }]}

    def test_relation_review_append_only_and_no_factual_promotion(self):
        pending=validate_relation_reviews(self.relations,self.k2)
        self.assertGreater(pending["pending_count"],0)
        changed=submit_relation_review(self.relations,self.k2,self.review())
        self.assertEqual(changed["version"],1)
        self.assertEqual(changed["parent_sha256"],self.relations["snapshot_sha256"])
        self.assertEqual(changed["reviews"][0]["financial_truth_approved"],False)
        self.assertEqual(changed["auto_merged_claims"],0)
        self.assertEqual(validate_relation_reviews(self.relations,self.k2)["reviewed_count"],0)
        self.assertEqual(validate_relation_reviews(changed,self.k2)["reviewed_count"],1)
        output=relation_review_context(changed,self.k2,[self.pair["new_claim_id"]])
        self.assertFalse(output["semantic_adjudication_independent"])
        saved=save_private_relation_reviews(changed,self.k2,str(self.root/"relations"))
        self.assertEqual(Path(saved).stat().st_mode&0o077,0)
        with self.assertRaises(FileExistsError):
            save_private_relation_reviews(changed,self.k2,str(self.root/"relations"))

    def test_duplicate_relation_review_blocked(self):
        updated=submit_relation_review(self.relations,self.k2,self.review())
        with self.assertRaisesRegex(ValueError,"V3_RELATION_REVIEW_UNSAFE_OR_UNREGISTERED"):
            submit_relation_review(updated,self.k2,self.review())

    def test_forged_quote_rejected_even_if_review_id_recomputed(self):
        new=self.review()
        new["new_quote"]="이 원본에는 없는 투자 수익률 500퍼센트 보장"
        with self.assertRaisesRegex(ValueError,"V3_RELATION_QUOTE_NOT_IN_CITED_ORIGINAL"):
            submit_relation_review(self.relations,self.k2,new)

    def test_forged_relation_label_rejected(self):
        new=self.review();new["relation_label"]="CONFIRMED_FINANCIAL_TRUTH"
        with self.assertRaisesRegex(ValueError,"V3_RELATION_REVIEW_UNSAFE_OR_UNREGISTERED"):
            submit_relation_review(self.relations,self.k2,new)

    def test_modified_claim_ids_blocked(self):
        new=self.review();new["new_claim_id"]="K"+"f"*24
        with self.assertRaisesRegex(ValueError,"V3_RELATION_REVIEW_UNSAFE_OR_UNREGISTERED"):
            submit_relation_review(self.relations,self.k2,new)

    def test_relation_ledger_cannot_rebase_unrelated_knowledge(self):
        updated=submit_relation_review(self.relations,self.k2,self.review())
        with self.assertRaisesRegex(ValueError,"V3_RELATION_REBASE_MISSING_SOURCE_CLAIM"):
            rebase_relation_reviews(updated,self.k2,self.k1)
        updated2=rebase_relation_reviews(updated,self.k2,self.k2)
        self.assertEqual(updated2["version"],1)
        self.assertEqual(updated2["reviews"],updated["reviews"])

    def test_blind_retrieval_report_metrics_not_human_certification(self):
        result=evaluate_relation_retrieval(self.k2,self.gold())
        self.assertEqual(result["query_count"],1)
        self.assertEqual(result["positive_pair_count"],1)
        self.assertIn("10",result["results"]["financial_alias"])
        self.assertEqual(result["results"]["financial_alias"]["10"]["recall_at_k"],1.0)
        self.assertFalse(result["certified_real_world_recall"])
        self.assertFalse(result["human_reviewer_identity_independently_verified"])
        self.assertFalse(result["release_gate_approved"])

    def test_false_blind_reviewers_prohibited(self):
        fake=self.gold()
        fake["reviewers"][1]["reviewer_id"]="syntheticR1"
        with self.assertRaisesRegex(ValueError,"V3_RELATION_GOLD_ADJUDICATOR_NOT_SEPARATE"):
            validate_relation_gold(self.k2,fake)

    def test_wrong_gold_quote_prohibited(self):
        fake=self.gold()
        fake["queries"][0]["relevant_old_claims"][0]["old_source_quote"]="해당 자막에 없는 100% 확정 수익"
        with self.assertRaisesRegex(ValueError,"V3_RELATION_GOLD_UNCITED_QUOTE"):
            evaluate_relation_retrieval(self.k2,fake)

    def test_relation_gold_cannot_reuse_prior_video_as_new(self):
        fake=self.gold()
        fake["queries"][0]["new_claim_id"]=self.pair["old_claim_id"]
        fake["queries"][0]["new_source_quote"]=self.report(self.claims[self.pair["old_claim_id"]])
        with self.assertRaisesRegex(ValueError,"V3_RELATION_GOLD_PAIR_NOT_PRIOR_VIDEO"):
            validate_relation_gold(self.k2,fake)

    def test_advisory_without_live_evidence_fails_closed(self):
        result=build_advisory_dossier(
            self.k2,self.evidence,"상품 비용과 계약 조건은 어떻게 다른가요?",
            "2026-11-02","KR",relations=self.relations)
        self.assertGreater(result["relevant_provisional_claim_count"],0)
        self.assertEqual(result["actionable_recommendations"],[])
        self.assertIn("INVESTOR_SUITABILITY_PROFILE_INCOMPLETE",
                      result["unresolved_advisory_requirements"])
        self.assertIn("CROSS_VIDEO_RELATIONS_UNREVIEWED",
                      result["unresolved_advisory_requirements"])
        self.assertTrue(all(not x["can_support_individual_investment_recommendation"]
                            for x in result["claim_dossiers"]))

    def test_complete_user_profile_still_not_auto_investment_advice(self):
        profile={"investment_horizon_years":10,"risk_tolerance":"moderate",
                 "tax_residency":"KR","account_type":"IRP",
                 "liquidity_needs":"5년 이내 인출 계획 없음"}
        result=build_advisory_dossier(
            self.k2,self.evidence,"상품 비용과 계약 조건은 어떻게 다른가요?",
            "2026-11-02","KR",investor_profile=profile)
        self.assertEqual(result["profile_missing_fields"],[])
        self.assertFalse(result["individualized_advice_released"])
        self.assertEqual(result["automatic_financial_fact_approvals"],0)

    def test_advisory_rejects_unsafe_profile_fields(self):
        with self.assertRaisesRegex(ValueError,"V3_ADVISORY_PROFILE_SCHEMA_INVALID"):
            build_advisory_dossier(
                self.k2,self.evidence,"상품 비용과 계약 조건이 다른가요?",
                "2026-11-02",investor_profile={"password":"private"})

    def test_completion_gate_blocks_partial_and_synthetic_gold_even_if_scored(self):
        result=completion_gate(
            self.queue,self.k2,self.evidence,self.relations,
            evaluate_relation_retrieval(self.k2,self.gold()))
        self.assertFalse(result["source_semantic_census_complete"])
        self.assertEqual(result["next_operation"],"FINISH_SOURCE_WINDOWS")
        self.assertEqual(result["financial_facts_independently_approved"],0)
        self.assertFalse(result["financial_advice_released"])
        self.assertIn("P0D_INDEPENDENT_REVIEWER_IDENTITIES_AND_GOLD_UNVERIFIED",
                      result["blockers"])

    def test_completion_rejects_knowledge_evidence_crossing(self):
        with self.assertRaisesRegex(ValueError,"V2_EVIDENCE_LEDGER_KNOWLEDGE_SNAPSHOT_MISMATCH"):
            completion_gate(self.queue,self.k1,self.evidence)

    def test_independent_evaluation_cannot_be_repointed_to_other_snapshot(self):
        gold=evaluate_relation_retrieval(self.k2,self.gold())
        with self.assertRaisesRegex(ValueError,"V3_COMPLETION_RELATION_EVAL_INVALID"):
            completion_gate(self.queue,self.k1,relation_evaluation=gold)


    def test_completed_source_census_still_not_advice_approved(self):
        manifest={
            "schema":"IRE_V2_CHAT_BATCH_V1","research_as_of":"2026-11-02",
            "videos":[
                {"video_id":VID,"original_srt_path":str(self.root/"src.srt"),
                 "source_sha256":self.digest,
                 "private_chat_sessions_path":str(self.root/"one")},
                {"video_id":OTHER_ID,"original_srt_path":str(self.root/"src2.srt"),
                 "source_sha256":sha256(self.raw2),
                 "private_chat_sessions_path":str(self.root/"two")}]}
        (self.root/"src2.srt").write_bytes(self.raw2)
        actual=ChatBatchQueue(manifest)
        self.assertEqual(actual.status()["remaining_windows"],0)
        gated=completion_gate(actual,self.k2,self.evidence,self.relations)
        self.assertTrue(gated["source_semantic_census_complete"])
        self.assertTrue(gated["current_batch_in_cumulative_knowledge"])
        self.assertFalse(gated["financial_advice_released"])
        self.assertEqual(gated["research_release_status"],
                         "STRUCTURAL_SOURCE_COMPLETE_EVIDENCE_PENDING")
        self.assertIn("P0C_NO_INDEPENDENTLY_FETCHED_OFFICIAL_DOCUMENT_EVENTS",
                      gated["blockers"])

    def test_completed_source_with_unrelated_knowledge_cannot_claim_integration(self):
        manifest={"schema":"IRE_V2_CHAT_BATCH_V1",
                  "research_as_of":"2026-11-02",
                  "videos":[{"video_id":VID,
                            "original_srt_path":str(self.root/"src.srt"),
                            "source_sha256":self.digest,
                            "private_chat_sessions_path":str(self.root/"one")}]}
        completed=ChatBatchQueue(manifest)
        gated=completion_gate(completed,self.k1)
        self.assertTrue(gated["current_batch_in_cumulative_knowledge"])
        self.assertFalse(gated["financial_advice_released"])
        unrelated=copy.deepcopy(self.k2)
        for row in unrelated["source_register"]:
            if row["video_id"]==VID:
                row["video_id"]="ABCDEFGHIJK"
        # An internally inconsistent snapshot must fail BEFORE its counts can
        # be treated as proof of integration.
        with self.assertRaisesRegex(ValueError,"KNOWLEDGE_SNAPSHOT_TAMPERED"):
            completion_gate(completed,unrelated)

    def test_unresolved_cue_count_blocks_source_semantic_gate(self):
        from ire.chat_bridge import ConversationResearchSession
        original=self.raw
        session=ConversationResearchSession(
            original,VID,self.digest,str(self.root/"unresolved_sessions"))
        packet=session.next_packet()
        session.accept({
            "schema":"IRE_CHAT_WINDOW_ANSWER_V1",
            "session_id":packet["session_id"],
            "window_id":packet["window_id"],
            "packet_sha256":packet["packet_sha256"],
            "claims":[],
            "cue_dispositions":[{"cue_index":x["cue_index"],
                "status":"UNRESOLVED","reason":"합성 원문 추가 해석 필요"}
                for x in packet["primary_cues"]]})
        manifest={"schema":"IRE_V2_CHAT_BATCH_V1",
                  "research_as_of":"2026-11-02",
                  "videos":[{"video_id":VID,
                            "original_srt_path":str(self.root/"src.srt"),
                            "source_sha256":self.digest,
                            "private_chat_sessions_path":str(self.root/"unresolved_sessions")}]}
        gated=completion_gate(ChatBatchQueue(manifest))
        self.assertEqual(gated["remaining_windows"],0)
        self.assertGreater(gated["unresolved_source_cues"],0)
        self.assertFalse(gated["source_semantic_census_complete"])
        self.assertEqual(gated["next_operation"],"RESOLVE_UNRESOLVED_SOURCE_CUES")


    def test_one_orchestrator_gate_command_reports_real_coverage_without_api(self):
        import subprocess,sys
        path=self.root/"manifest.json"
        path.write_text(json.dumps(self.manifest,ensure_ascii=False))
        result=subprocess.run([sys.executable,"-m","ire.v3_orchestrator",
                               "gate","--private-manifest",str(path)],
                              capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        parsed=json.loads(result.stdout)
        self.assertEqual(parsed["schema"],"IRE_V3_P0_P2_COMPLETION_GATE_V1")
        self.assertEqual(parsed["remaining_windows"],1)
        self.assertFalse(parsed["financial_advice_released"])
        self.assertEqual(parsed["model_api_calls"],0)


    def test_blindly_missed_relation_can_be_added_without_rewriting_knowledge(self):
        # Simulate a pair missed by the initial top-K candidate generator.
        omitted=self.pair
        snapshot=copy.deepcopy(self.k2)
        snapshot["relation_candidates"]=[x for x in snapshot["relation_candidates"]
                                         if x["relation_id"]!=omitted["relation_id"]]
        snapshot["snapshot_sha256"]=fingerprint(
            {k:v for k,v in snapshot.items() if k!="snapshot_sha256"})
        original=copy.deepcopy(snapshot)
        pending=empty_relation_reviews(snapshot)
        proposal={"schema":"IRE_V3_RELATION_DISCOVERY_SUBMISSION_V1",
            "old_claim_id":omitted["old_claim_id"],
            "new_claim_id":omitted["new_claim_id"],
            "old_quote":self.report(self.claims[omitted["old_claim_id"]]),
            "new_quote":self.report(self.claims[omitted["new_claim_id"]]),
            "discovery_explanation":"기존 후보 순위에서 누락된 영상 간 조건 연결을 원본 인용으로 새로 제안합니다."}
        expanded=discover_relation_candidate(pending,snapshot,proposal)
        self.assertEqual(expanded["version"],1)
        self.assertEqual(validate_relation_reviews(expanded,snapshot)["discovered_candidate_count"],1)
        self.assertEqual(snapshot,original)
        self.assertFalse(expanded["discovered_candidates"][0]["independent_human_gold"])
        review=self.review()
        reviewed=submit_relation_review(expanded,snapshot,review)
        self.assertEqual(reviewed["version"],2)
        context=relation_review_context(reviewed,snapshot,[omitted["new_claim_id"]])
        self.assertTrue(any(x["relation_id"]==omitted["relation_id"]
                            for x in context["relevant_reviews"]))
        self.assertEqual(reviewed["auto_merged_claims"],0)

    def test_duplicate_discovery_of_original_candidate_is_rejected(self):
        proposal={"schema":"IRE_V3_RELATION_DISCOVERY_SUBMISSION_V1",
            "old_claim_id":self.pair["old_claim_id"],
            "new_claim_id":self.pair["new_claim_id"],
            "old_quote":self.report(self.claims[self.pair["old_claim_id"]]),
            "new_quote":self.report(self.claims[self.pair["new_claim_id"]]),
            "discovery_explanation":"이미 자동 후보에 들어 있는 동일 관계를 실수로 중복 제출하는 시험입니다."}
        with self.assertRaisesRegex(ValueError,"V3_RELATION_DISCOVERY_EVENT_INVALID"):
            discover_relation_candidate(self.relations,self.k2,proposal)

    def test_discovery_fabricated_quote_never_creates_candidate(self):
        pair=self.pair
        removed=copy.deepcopy(self.k2)
        removed["relation_candidates"]=[x for x in removed["relation_candidates"]
                                         if x["relation_id"]!=pair["relation_id"]]
        removed["snapshot_sha256"]=fingerprint(
            {k:v for k,v in removed.items() if k!="snapshot_sha256"})
        proposal={"schema":"IRE_V3_RELATION_DISCOVERY_SUBMISSION_V1",
            "old_claim_id":pair["old_claim_id"],
            "new_claim_id":pair["new_claim_id"],
            "old_quote":"원문에 없는 배당수익률 45% 확정 보장",
            "new_quote":self.report(self.claims[pair["new_claim_id"]]),
            "discovery_explanation":"가짜 인용을 사용한 후보 누락 복구를 거부해야 한다는 회귀 시험입니다."}
        with self.assertRaisesRegex(ValueError,"V3_RELATION_QUOTE_NOT_IN_CITED_ORIGINAL"):
            discover_relation_candidate(empty_relation_reviews(removed),removed,proposal)


    def advisory_gold(self):
        item=self.k2["claims"][0]
        return {
            "schema":"IRE_V3_ADVISORY_BLIND_CASES_V1",
            "knowledge_snapshot_sha256":self.k2["snapshot_sha256"],
            "evidence_snapshot_sha256":self.evidence["snapshot_sha256"],
            "relation_snapshot_sha256":self.relations["snapshot_sha256"],
            "source_first_manual_scenarios":True,
            "model_outputs_hidden_during_adjudication":True,
            "reviewers":[
                {"reviewer_id":"syntheticA1","source_first_sha256":sha256(b"a1")},
                {"reviewer_id":"syntheticA2","source_first_sha256":sha256(b"a2")}],
            "adjudicator_id":"syntheticA3",
            "cases":[{
                "case_id":"A0001",
                "question":"상품 비용과 계약 조건은 어떻게 다른가요?",
                "as_of":"2026-11-02","jurisdiction":"KR",
                "investor_profile":None,
                "expected_blockers":[
                    "INVESTOR_SUITABILITY_PROFILE_INCOMPLETE",
                    "CROSS_VIDEO_RELATIONS_UNREVIEWED",
                    "INDEPENDENT_CURRENT_REGULATORY_AND_HUMAN_ADJUDICATION_REQUIRED"],
                "expected_relevant_source_quotes":[{
                    "global_claim_id":item["global_claim_id"],
                    "original_source_quote":item["source_refs"][0]["quote"]}],
                "must_not_release_advice":True}]}

    def test_advisory_blind_scenarios_measure_gates_without_truth_approval(self):
        result=evaluate_advisory_cases(self.k2,self.evidence,
                                       self.advisory_gold(),self.relations)
        self.assertEqual(result["scenario_count"],1)
        self.assertEqual(result["unsafe_recommendation_releases"],0)
        self.assertEqual(result["required_blocker_misses"],0)
        self.assertFalse(result["actual_investment_advice_quality_certified"])
        self.assertFalse(result["release_approved"])
        self.assertEqual(result["micro_source_quote_recall"],1.0)

    def test_advisory_blind_scenario_catches_missing_required_gate(self):
        gold=self.advisory_gold()
        gold["cases"][0]["expected_blockers"].append(
            "EXTERNAL_HUMAN_ADJUDICATED_INVESTMENT_FACTS")
        result=evaluate_advisory_cases(self.k2,self.evidence,gold,self.relations)
        self.assertEqual(result["required_blocker_misses"],1)
        self.assertFalse(result["release_approved"])

    def test_advisory_blind_gold_cannot_use_invented_source_quote(self):
        gold=self.advisory_gold()
        gold["cases"][0]["expected_relevant_source_quotes"][0][
            "original_source_quote"]="실제 원문에 없는 99퍼센트 연 수익 보장"
        with self.assertRaisesRegex(ValueError,"V3_ADVISORY_GOLD_QUOTE_OR_CLAIM_INVALID"):
            evaluate_advisory_cases(self.k2,self.evidence,gold,self.relations)

    def test_advisory_blind_gold_cannot_invent_reviewer_independence(self):
        gold=self.advisory_gold()
        gold["reviewers"][1]["reviewer_id"]="syntheticA1"
        with self.assertRaisesRegex(ValueError,"V3_ADVISORY_GOLD_REVIEWERS_NOT_INDEPENDENT"):
            evaluate_advisory_cases(self.k2,self.evidence,gold,self.relations)

    def test_advisory_blind_gold_snapshot_mismatch_rejected(self):
        gold=self.advisory_gold()
        gold["evidence_snapshot_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"V3_ADVISORY_GOLD_SCHEMA_OR_SOURCE_MISMATCH"):
            evaluate_advisory_cases(self.k2,self.evidence,gold,self.relations)


if __name__=="__main__":
    unittest.main()