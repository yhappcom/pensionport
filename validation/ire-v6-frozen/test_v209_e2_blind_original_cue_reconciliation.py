"""V209 blind-to-V176 source reading: fake Korean text, no independent gold."""
from __future__ import annotations

import copy
import unittest

from ire.v6.atomic_exchange import NUMBER
from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput
from v209_e2_blind_original_cue_reconciliation import (
    PLAN,ANSWER,blind_challenge,
    review_blind_and_reconcile,reconcile_full_blind_video,
)
from test_v206_e2_full_cue_semantic_census import TestV206KoreanQuestionQuoteMeaningGap

ANALYSIS="기존 V176 원자 분류를 보지 않고 원문 질문·인용과 주장·조건·예외를 개별적으로 분해합니다."

SPEECH={
    1:"QUESTION_WITH_EMBEDDED_ASSERTION",
    2:"QUOTE_WITH_FACT_DEPENDENCY",
    3:"OPINION_ASSERTION",
    4:"FACT_ASSERTION",
}
CLAIMS={
    1:("FACT","8%가 무조건 비과세",
       "질문에 포함된 연 8% 비과세라는 사실 여부 미검증 주장입니다.",
       "QUESTIONED_NOT_ASSERTED"),
    2:("FACT","모든 소득이 비과세",
       "타인 발언으로 인용된 모든 소득 비과세 가능성의 미검증 주장입니다.",
       "QUOTED_NOT_ENDORSED"),
    3:("OPINION","ISA가 유리하지만 조건에 따라 과세될 수 있습니다.",
       "ISA가 유리하다는 발언자의 의견에 조건부 과세 설명이 붙어 있습니다.",
       "OPINION_ONLY"),
    4:("FACT","한도 초과분은 과세될 수 있다는 설명입니다.",
       "한도를 넘는 금액의 과세 가능성에 대해 설명하는 검증 전 주장입니다.",
       "ASSERTED_UNVERIFIED"),
}


def blind_answer(challenge,*,remove_cues=None):
    remove_cues=set(remove_cues or ())
    responses=[]
    for original in challenge["target_cues"]:
        i=original["cue_index"]
        if i in remove_cues:
            speech="NON_RESEARCH_ONLY"
            claims=[]
        else:
            speech=SPEECH[i]
            kind,quote,prop,role=CLAIMS[i]
            conditions=[]
            exceptions=[]
            if i==3:
                conditions=[{"cue_index":i,"source_quote":"조건에 따라",
                             "source_text_sha256":original["source_text_sha256"]}]
            if i==4:
                exceptions=[{"cue_index":i,"source_quote":"한도 초과분",
                             "source_text_sha256":original["source_text_sha256"]}]
            claims=[{
                "kind":kind,"proposition":prop,
                "source_quote":quote,"epistemic_role":role,
                "context_cue_indices":[i],
                "condition_links":conditions,"exception_links":exceptions,
                "rebuttal_links":[],
                "numeric_references":[{
                    "cue_index":i,"token":t}
                    for t in NUMBER.findall(prop)],
            }]
        responses.append({
            "cue_index":i,
            "source_text_sha256":original["source_text_sha256"],
            "speech_act":speech,
            "original_quote":original["original_text"],
            "analysis":ANALYSIS,
            "analysis_sha256":sha256(ANALYSIS.encode("utf-8")),
            "atoms":claims,
            "cue_numeric_tokens":original["original_numeric_tokens"],
            "audio_speaker_verified":False,
            "financial_fact_approved":False,
        })
    return {
        "schema":ANSWER,"challenge_sha256":challenge["challenge_sha256"],
        "review_executor":"CHATGPT_IN_CHAT",
        "responses":responses,
        "independent_external_gold_certified":False,
        "financial_fact_truth_certified":False,"e2_final_pass":False,
    }


class TestV209BlindSemanticConfrontation(unittest.TestCase):
    def setUp(self):
        self.fx=TestV206KoreanQuestionQuoteMeaningGap(
            "test_15_embedded_question_and_quoted_claim_do_not_disappear_as_noatom")
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.owner=self.fx.owner
        self.head=self.fx.head
        self.task=blind_challenge(
            self.owner,expected_owner_head=self.head,limit=4)
        self.answer=blind_answer(self.task)

    def audit(self,answer=None,task=None):
        return review_blind_and_reconcile(
            self.owner,task if task is not None else self.task,
            answer if answer is not None else self.answer,
            expected_owner_head=self.head)

    def test_01_blind_challenge_hides_v176_predictions_entirely(self):
        self.assertEqual(self.task["schema"],PLAN)
        self.assertFalse(self.task["v176_labels_present"])
        self.assertFalse(self.task["preexisting_candidate_claims_present"])
        self.assertTrue(all(set(c)=={
            "cue_index","original_text","source_text_sha256",
            "original_numeric_tokens"} for c in self.task["target_cues"]))
        self.assertNotIn("disposition",str(self.task).lower())
        self.assertNotIn("v176_claims",str(self.task).lower())
        self.assertEqual(self.task["target_cues"][0]["original_numeric_tokens"],
                         ["8%","8%"])

    def test_02_blind_recheck_detects_two_embedded_fact_omissions(self):
        prior=self.owner.progress()["checkpoint_head_sha256"]
        r=self.audit()
        self.assertEqual(r["blind_original_cues_checked"],4)
        self.assertEqual(r["blind_original_claims_proposed"],4)
        self.assertEqual(r["disagreement_count"],2)
        self.assertEqual({x["cue_index"] for x in r["disagreements"]},{1,2})
        self.assertEqual({x["reason"] for x in r["disagreements"]},
                         {"ATOM_HIDDEN_BY_V176_NONASSERTION"})
        self.assertEqual(r["status"],
                         "HOLD_FOR_CHAT_DISAGREEMENT_ADJUDICATION")
        self.assertFalse(r["independent_external_gold_certified"])
        self.assertFalse(r["e2_final_pass"])
        self.assertEqual(prior,self.owner.progress()["checkpoint_head_sha256"])

    def test_03_qualifier_erasure_is_cross_checked_with_original_v176(self):
        a=copy.deepcopy(self.answer)
        a["responses"][2]["atoms"][0]["condition_links"]=[]
        a["responses"][3]["atoms"][0]["exception_links"]=[]
        r=self.audit(a)
        issues={(x["cue_index"],x["reason"]) for x in r["disagreements"]}
        self.assertIn((3,"CONDITION_EXCEPTION_SOURCE_DISAGREEMENT"),issues)
        self.assertIn((4,"CONDITION_EXCEPTION_SOURCE_DISAGREEMENT"),issues)

    def test_04_original_fact_mislabelled_as_opinion_stays_hold(self):
        a=copy.deepcopy(self.answer)
        a["responses"][3]["atoms"][0]["kind"]="OPINION"
        r=self.audit(a)
        self.assertIn({"cue_index":4,"reason":"CLAIM_KIND_DISAGREEMENT",
                       "details":{"ordinal":1,"previous_kind":"FACT",
                                  "blind_kind":"OPINION"}},
                      r["disagreements"])

    def test_05_reported_claim_cannot_become_narrator_verified_fact(self):
        a=copy.deepcopy(self.answer)
        a["responses"][0]["atoms"][0]["epistemic_role"]="ASSERTED_UNVERIFIED"
        with self.assertRaisesRegex(InvalidInput,
                              "BLIND_REPORTED_CLAIM_PROMOTED_TO_DIRECT_FACT"):
            self.audit(a)

    def test_06_source_quote_and_number_forgery_rejected(self):
        a=copy.deepcopy(self.answer)
        a["responses"][0]["atoms"][0]["source_quote"]="ETF 연 99% 보장"
        with self.assertRaisesRegex(InvalidInput,"BLIND_ATOM_SOURCE_CONTEXT"):
            self.audit(a)
        a=copy.deepcopy(self.answer)
        a["responses"][0]["atoms"][0]["numeric_references"]=[]
        with self.assertRaisesRegex(InvalidInput,
                                    "BLIND_NUMERIC_OMITTED_OR_INVENTED"):
            self.audit(a)

    def test_07_every_original_numeric_token_kept_for_quote_and_question(self):
        a=copy.deepcopy(self.answer)
        a["responses"][0]["cue_numeric_tokens"].pop()
        with self.assertRaisesRegex(InvalidInput,
                "BLIND_ORIGINAL_QUOTE_NUMERIC_OR_REVIEWER_DRIFT"):
            self.audit(a)

    def test_08_blind_task_self_hash_tamper_rejected_even_when_rehashed(self):
        task=copy.deepcopy(self.task)
        task["target_cues"][0]["original_text"]="기존 원문을 다른 글자로 대체합니다."
        task["challenge_sha256"]=json_digest(
            {k:v for k,v in task.items() if k!="challenge_sha256"})
        with self.assertRaisesRegex(InvalidInput,
                                    "BLIND_CHALLENGE_NOT_ORIGINAL"):
            self.audit(task=task)

    def test_09_blind_reading_does_not_claim_external_gold_or_E2_pass(self):
        for key in ("independent_external_gold_certified",
                    "financial_fact_truth_certified","e2_final_pass"):
            a=copy.deepcopy(self.answer)
            a[key]=True
            with self.assertRaisesRegex(InvalidInput,
                                        "BLIND_ANSWER_SCHEMA_OR_CUE_CENSUS"):
                self.audit(a)

    def test_10_nonresearch_false_label_in_blind_causes_speech_disagreement(self):
        a=copy.deepcopy(self.answer)
        a["responses"][0]["speech_act"]="NON_RESEARCH_ONLY"
        a["responses"][0]["atoms"]=[]
        r=self.audit(a)
        self.assertIn("SOURCE_SPEECH_ACT_DISAGREEMENT",
                      {x["reason"] for x in r["disagreements"]})

    def test_11_unresolved_blind_label_is_never_concordant_gold(self):
        a=copy.deepcopy(self.answer)
        a["responses"][2]["speech_act"]="UNRESOLVED_MEANING"
        a["responses"][2]["atoms"]=[]
        r=self.audit(a)
        self.assertIn("BLIND_SOURCE_MEANING_STILL_UNRESOLVED",
                      {x["reason"] for x in r["disagreements"]})

    def test_12_valid_source_rebuttal_new_to_question_stays_disagreement(self):
        a=copy.deepcopy(self.answer)
        quote=self.task["surrounding_cues"][3]["original_text"]
        a["responses"][0]["atoms"][0]["context_cue_indices"]=[1,4]
        a["responses"][0]["atoms"][0]["rebuttal_links"]=[{
            "cue_index":4,"source_quote":quote,
            "source_text_sha256":sha256(quote.encode("utf-8"))}]
        r=self.audit(a)
        reasons={(x["cue_index"],x["reason"]) for x in r["disagreements"]}
        self.assertIn((1,"NEW_BLIND_DISCOURSE_NEEDS_V176_RECHECK"),reasons)

    def test_13_no_previous_meaning_original_can_be_open_not_green(self):
        a=copy.deepcopy(self.answer)
        a["responses"][0]["speech_act"]="UNRESOLVED_MEANING"
        a["responses"][0]["atoms"]=[]
        r=self.audit(a)
        self.assertTrue(r["disagreement_count"]>=1)
        self.assertFalse(r["e2_final_pass"])

    def test_14_full_video_blind_cue_census_exact_once(self):
        c1=blind_challenge(self.owner,expected_owner_head=self.head,
                            start_cue=1,limit=2)
        c2=blind_challenge(self.owner,expected_owner_head=self.head,
                            start_cue=3,limit=2)
        result=reconcile_full_blind_video(self.owner,[
            {"challenge":c1,"answer":blind_answer(c1)},
            {"challenge":c2,"answer":blind_answer(c2)}],
            expected_owner_head=self.head)
        self.assertEqual(result["original_cues_covered"],4)
        self.assertEqual(result["blind_claims_proposed"],4)
        self.assertEqual(result["semantic_disagreements"],2)
        self.assertFalse(result["e2_final_pass"])

    def test_15_full_blind_requires_all_original_cues(self):
        c1=blind_challenge(self.owner,expected_owner_head=self.head,
                            start_cue=1,limit=2)
        with self.assertRaisesRegex(InvalidInput,
                                    "FULL_BLIND_SOURCE_CUE_MISSING"):
            reconcile_full_blind_video(self.owner,[
                {"challenge":c1,"answer":blind_answer(c1)}],
                expected_owner_head=self.head)

    def test_16_full_blind_prevents_double_counting(self):
        with self.assertRaisesRegex(InvalidInput,
                                    "FULL_BLIND_CUE_DOUBLE_COUNT"):
            reconcile_full_blind_video(self.owner,[
                {"challenge":self.task,"answer":self.answer},
                {"challenge":self.task,"answer":self.answer}],
                expected_owner_head=self.head)

    def test_17_wrong_owner_head_for_blind_source_fails_closed(self):
        with self.assertRaisesRegex(InvalidInput,
                                    "OWNER_CHECKPOINT_CHANGED"):
            blind_challenge(self.owner,expected_owner_head="f"*64)

    def test_18_unhashable_speech_act_list_returns_invalidinput(self):
        a=copy.deepcopy(self.answer)
        a["responses"][0]["speech_act"]=["QUESTION_WITH_EMBEDDED_ASSERTION"]
        with self.assertRaisesRegex(InvalidInput,
                             "BLIND_ORIGINAL_QUOTE_NUMERIC_OR_REVIEWER_DRIFT"):
            self.audit(a)


if __name__=="__main__":
    unittest.main()
