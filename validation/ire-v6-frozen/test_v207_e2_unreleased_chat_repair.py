"""V207 E2 replay tests with original Korean Q/quote synthetic source.

No approved V6 atom or financial/legal factual truth is created.
"""
from __future__ import annotations

import copy
import unittest

from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput
from v206_e2_full_cue_semantic_census import build_e2_source_repair_docket
from v207_e2_unreleased_chat_repair import SCHEMA,audit_e2_chat_repairs
from test_v206_e2_full_cue_semantic_census import (
    TestV206KoreanQuestionQuoteMeaningGap,TestV206UnsupportedAnecdote,
    answered,
)


def authored_plan(owner,challenge,answer,head,*,actions=None):
    docket=build_e2_source_repair_docket(
        owner,challenge,answer,expected_owner_head=head)
    actions=actions or {}
    decisions=[]
    for issue in docket["issues"]:
        isembedded=(issue["reason"]=="EMBEDDED_ASSERTION_EXCLUDED_BY_V176")
        action=actions.get(issue["issue_id"],
                           "DRAFT_UNVERIFIED_EMBEDDED_CLAIM"
                           if isembedded else "KEEP_OPEN")
        cue=issue["cue_index"]
        quote=issue["original_source_quote"]
        kind="FACT"
        act=("REPORTED_CLAIM_IN_QUESTION"
             if issue["original_disposition"]=="QUESTION" else
             "QUOTED_UNVERIFIED_SPEECH"
             if issue["original_disposition"]=="QUOTE" else
             "UNRESOLVED_SOURCE_SPEECH")
        draft=[]
        if action=="DRAFT_UNVERIFIED_EMBEDDED_CLAIM":
            from ire.v6.atomic_exchange import NUMBER
            reviewed_row=next(r for r in answer["rows"] if r["cue_index"]==cue)
            links=reviewed_row["rebuttal_source_links"]
            ctx=sorted({cue}|{r["cue_index"] for r in links})
            draft=[{
                "draft_id":f"E2DRAFT-{cue:05d}-01",
                "kind":kind,
                "proposition":"원문에서 인용하거나 질문한 검증되지 않은 투자 과세 주장입니다.",
                "source_cue_index":cue,
                "verbatim_quote":quote,
                "context_cue_indices":ctx,
                "conditions":[],"exceptions":[],
                "source_discourse_links":copy.deepcopy(links),
                "numeric_references":[{"cue_index":cue,"token":token}
                                      for token in NUMBER.findall(quote)],
                "speaker":"UNKNOWN","stance":"UNRESOLVED","as_of":None,
                "epistemic_status":act,
                "fact_dependency_open":True,
                "not_native_v6_atom":True,
                "financial_fact_approved":False,
            }]
        note=("현재 자막에서 다른 사람의 금융적 사실 주장을 인용하거나 질문한 "
              "경우이며, 사실 여부·예외·개인별 적용을 확인하기 전에는 "
              "정식 V6 금융 사실 원자 또는 투자 조언으로 승인하지 않습니다.")
        decisions.append({
            "issue_id":issue["issue_id"],
            "cue_index":cue,
            "source_cue_sha256":issue["source_cue_sha256"],
            "issue_reason":issue["reason"],
            "review_action":action,
            "source_speech_act":act,
            "quoted_source_excerpt":quote,
            "review_note":note,
            "review_note_sha256":sha256(note.encode("utf-8")),
            "draft_claims":draft,
            "previous_v176_decision_unchanged":True,
        })
    return {
        "schema":SCHEMA,"review_executor":"CHATGPT_IN_CHAT",
        "source_sha256":owner.source.source_sha256,
        "owner_head_sha256":head,
        "e2_challenge_sha256":challenge["challenge_sha256"],
        "e2_answer_sha256":json_digest(answer),
        "source_docket_sha256":json_digest(docket),
        "review_notes_sha256":sha256(b"synthetic unapproved private source notes"),
        "decisions":decisions,
        "financial_fact_approved":False,
        "native_v6_released":False,
        "knowledge_publication_authorized":False,
        "e2_final_pass":False,
        "e3_e4_e5_authorized":False,
    }


class E2V207RepairTests(unittest.TestCase):
    def setUp(self):
        self.fx=TestV206KoreanQuestionQuoteMeaningGap(
            "test_15_embedded_question_and_quoted_claim_do_not_disappear_as_noatom")
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.owner=self.fx.owner
        self.challenge=self.fx.packet
        self.head=self.fx.head
        self.answer=answered(self.challenge,source_risks={
            1:("QUESTION_WITH_EMBEDDED_ASSERTION","8%가 무조건 비과세"),
            2:("QUOTE_WITH_FACT_DEPENDENCY","모든 소득이 비과세"),
        })
        self.plan=authored_plan(self.owner,self.challenge,self.answer,self.head)

    def run_audit(self,plan=None,answer=None):
        return audit_e2_chat_repairs(
            self.owner,self.challenge,answer if answer is not None else self.answer,
            plan if plan is not None else self.plan,
            expected_owner_head=self.head)

    def test_01_two_embedded_claims_become_unreleased_original_pinned_drafts(self):
        before=self.owner.progress()["checkpoint_head_sha256"]
        result=self.run_audit()
        self.assertEqual(result["issues_reviewed"],2)
        self.assertEqual(result["unreleased_draft_claims"],2)
        self.assertFalse(result["original_v176_changed"])
        self.assertFalse(result["e2_final_pass"])
        self.assertFalse(result["e3_e4_e5_authorized"])
        self.assertFalse(result["knowledge_written"])
        self.assertEqual(before,self.owner.progress()["checkpoint_head_sha256"])
        self.assertTrue(all(d["native_v6_claim_id"] is None
                            for d in result["unreleased_drafts"]))

    def test_02_question_and_quote_have_distinct_speech_attribution(self):
        out=self.run_audit()["unreleased_drafts"]
        self.assertEqual(out[0]["source_speech_act"],
                         "REPORTED_CLAIM_IN_QUESTION")
        self.assertEqual(out[1]["source_speech_act"],
                         "QUOTED_UNVERIFIED_SPEECH")
        self.assertEqual(out[0]["numeric_references"],
                         [{"cue_index":1,"token":"8%"}])
        self.assertEqual(out[1]["numeric_references"],[])

    def test_03_missing_issue_rejected(self):
        p=copy.deepcopy(self.plan)
        p["decisions"].pop()
        with self.assertRaisesRegex(InvalidInput,"PIN_OR_FALSE_RELEASE"):
            self.run_audit(p)

    def test_04_forged_source_digest_rejected(self):
        p=copy.deepcopy(self.plan)
        p["source_docket_sha256"]="f"*64
        with self.assertRaisesRegex(InvalidInput,"PIN_OR_FALSE_RELEASE"):
            self.run_audit(p)

    def test_05_question_disguised_as_direct_financial_fact_rejected(self):
        p=copy.deepcopy(self.plan)
        p["decisions"][0]["source_speech_act"]="FINANCIAL_FACT_ASSERTION"
        with self.assertRaisesRegex(InvalidInput,"QUESTION_QUOTE_ATTRIBUTION_LOSS"):
            self.run_audit(p)

    def test_06_quote_original_noatom_must_not_turn_into_native_id(self):
        p=copy.deepcopy(self.plan)
        p["decisions"][1]["draft_claims"][0]["draft_id"]="C00001"
        with self.assertRaisesRegex(InvalidInput,"DRAFT_MEANING_OR_SOURCE_DRIFT"):
            self.run_audit(p)

    def test_07_forged_cue_quote_rejected(self):
        p=copy.deepcopy(self.plan)
        p["decisions"][0]["draft_claims"][0]["verbatim_quote"]="연 80% 비과세 보장"
        with self.assertRaisesRegex(InvalidInput,"DRAFT_MEANING_OR_SOURCE_DRIFT"):
            self.run_audit(p)

    def test_08_forged_numeric_quote_or_missing_number_rejected(self):
        p=copy.deepcopy(self.plan)
        p["decisions"][0]["draft_claims"][0]["numeric_references"]=[]
        with self.assertRaisesRegex(InvalidInput,"REPORTED_NUMERIC_TOKEN_REMOVED_OR_INVENTED"):
            self.run_audit(p)

    def test_09_unquoted_financial_exception_cannot_be_added(self):
        p=copy.deepcopy(self.plan)
        p["decisions"][0]["draft_claims"][0]["exceptions"]=[{
            "cue_index":1,"verbatim_quote":"현행법상 누구나 절세 보장",
            "source_cue_sha256":p["decisions"][0]["source_cue_sha256"]}]
        with self.assertRaisesRegex(InvalidInput,"QUALIFIER_SOURCE_NOT_ORIGINAL"):
            self.run_audit(p)

    def test_10_unapproved_fact_cannot_be_advice_or_e3_release(self):
        for key in ["financial_fact_approved","native_v6_released",
                    "knowledge_publication_authorized","e2_final_pass",
                    "e3_e4_e5_authorized"]:
            p=copy.deepcopy(self.plan);p[key]=True
            with self.assertRaisesRegex(InvalidInput,"PIN_OR_FALSE_RELEASE"):
                self.run_audit(p)

    def test_11_original_source_head_mutation_blocks_existing_review(self):
        with self.assertRaisesRegex(InvalidInput,"EXTERNAL_OWNER_HEAD_STALE"):
            audit_e2_chat_repairs(self.owner,self.challenge,self.answer,self.plan,
                                   expected_owner_head="f"*64)

    def test_12_keep_open_does_not_auto_generate_candidate(self):
        docket=build_e2_source_repair_docket(
            self.owner,self.challenge,self.answer,expected_owner_head=self.head)
        p=authored_plan(self.owner,self.challenge,self.answer,self.head,
                       actions={docket["issues"][0]["issue_id"]:"KEEP_OPEN"})
        result=self.run_audit(p)
        self.assertEqual(result["unreleased_draft_claims"],1)
        self.assertEqual(result["still_open_issues"],1)

    def test_16_explicit_neighboring_exception_survives_draft_projection(self):
        from ire.v6.codec import sha256
        answer=copy.deepcopy(self.answer)
        quote=self.owner.source.cues[3].text
        answer["rows"][0]["rebuttal_source_links"]=[{
            "cue_index":4,
            "source_quote":quote,
            "source_text_sha256":sha256(quote.encode("utf-8")),
            "relation_type":"EXCEPTION",
        }]
        plan=authored_plan(
            self.owner,self.challenge,answer,self.head)
        out=self.run_audit(plan,answer)
        first=out["unreleased_drafts"][0]
        self.assertEqual(first["source_discourse_links"][0]["cue_index"],4)
        self.assertEqual(first["source_discourse_links"][0]["relation_type"],"EXCEPTION")
        bad=copy.deepcopy(plan)
        bad["decisions"][0]["draft_claims"][0]["source_discourse_links"]=[]
        with self.assertRaisesRegex(InvalidInput,
                                    "CROSS_CUE_DISCOURSE_LOST_OR_DUPLICATED"):
            self.run_audit(bad,answer)

    def test_17_cross_cue_rebuttal_must_remain_in_context(self):
        answer=copy.deepcopy(self.answer)
        quote=self.owner.source.cues[3].text
        answer["rows"][0]["rebuttal_source_links"]=[{
            "cue_index":4,
            "source_quote":quote,
            "source_text_sha256":sha256(quote.encode("utf-8")),
            "relation_type":"REBUTTAL",
        }]
        plan=authored_plan(self.owner,self.challenge,answer,self.head)
        bad=copy.deepcopy(plan)
        bad["decisions"][0]["draft_claims"][0]["context_cue_indices"]=[1]
        with self.assertRaisesRegex(InvalidInput,
                                    "CROSS_CUE_DISCOURSE_NOT_ORIGINAL"):
            self.run_audit(bad,answer)

    def test_13_quarantine_requires_no_proposed_atom(self):
        p=copy.deepcopy(self.plan)
        p["decisions"][1]["review_action"]="SOURCE_ONLY_QUARANTINE"
        with self.assertRaisesRegex(InvalidInput,"QUARANTINE_OR_OPEN_CANNOT_ISSUE_ATOM"):
            self.run_audit(p)
        p["decisions"][1]["draft_claims"]=[]
        out=self.run_audit(p)
        self.assertEqual(out["source_only_quarantined_issues"],1)
        self.assertEqual(out["unreleased_draft_claims"],1)


class E2V207AnecdoteCannotBecomeApprovedFact(unittest.TestCase):
    def setUp(self):
        self.fx=TestV206UnsupportedAnecdote(
            "test_20_unmappable_anecdote_still_has_its_source_claim_in_e2")
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.owner=self.fx.owner
        self.head=self.fx.head
        from v206_e2_full_cue_semantic_census import prepare_e2_cue_challenge
        self.challenge=prepare_e2_cue_challenge(
            self.owner,expected_owner_head=self.head,start_cue=2,limit=1)
        self.answer=answered(self.challenge)
        self.plan=authored_plan(self.owner,self.challenge,self.answer,self.head)

    def test_14_anecdote_keep_open_remains_unreleased(self):
        out=audit_e2_chat_repairs(
            self.owner,self.challenge,self.answer,self.plan,
            expected_owner_head=self.head)
        self.assertEqual(out["unreleased_draft_claims"],0)
        self.assertEqual(out["still_open_issues"],1)

    def test_15_anecdote_cannot_be_wrapped_in_new_approved_v6_atom(self):
        p=copy.deepcopy(self.plan)
        p["decisions"][0]["review_action"]="DRAFT_UNVERIFIED_EMBEDDED_CLAIM"
        p["decisions"][0]["draft_claims"]=[{}]
        with self.assertRaisesRegex(InvalidInput,"DRAFT_MUST_BE_SOURCE_EMBEDDED"):
            audit_e2_chat_repairs(
                self.owner,self.challenge,self.answer,p,
                expected_owner_head=self.head)


if __name__=="__main__":
    unittest.main()
