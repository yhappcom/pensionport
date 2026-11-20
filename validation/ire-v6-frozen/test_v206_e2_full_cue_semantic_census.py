"""E2 semantic census stress tests: synthetic Korean data, no financial approvals."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from ire.v6.codec import sha256
from ire.v6.atomic_exchange import NUMBER
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession,COMMIT
from v206_e2_full_cue_semantic_census import (
    prepare_e2_cue_challenge,audit_e2_cue_answer,audit_full_e2_video,
    ANSWER,
)
import test_v202_e1_v176_native_positive_path as original_e1


NOTES="원문의 발언 유형과 금융 주장 여부는 별도로 확인하며 출처의 의미를 자동 승인하지 않습니다."
CAUTION="검토자는 금융 법령과 예외를 독립적으로 검증하기 전 원문 표현을 사실이나 개인 자문으로 승인하지 않습니다."


def answered(packet, *, source_risks=None, missing_terms=None):
    source_risks=source_risks or {}
    missing_terms=missing_terms or set()
    rows=[]
    type_for_kind={
        "FACT":"FINANCIAL_FACT_ASSERTION",
        "OPINION":"OPINION_ASSERTION",
        "HYPOTHETICAL":"HYPOTHESIS_ASSERTION",
        "RECOMMENDATION":"RECOMMENDATION_ASSERTION",
        "MATH":"OTHER_FACT_ASSERTION",
        "QUESTION":"QUESTION_ONLY",
        "ANECDOTE":"OPINION_ASSERTION",
    }
    context={c["cue_index"]:c for c in packet["surrounding_context"]}
    for target in packet["target_cues"]:
        index=target["cue_index"]
        disposition=target["v176_disposition"]
        if disposition=="ASSERTION":
            speech=type_for_kind[target["v176_claims"][0]["kind"]]
        elif disposition=="QUESTION":speech="QUESTION_ONLY"
        elif disposition=="QUOTE":speech="QUOTE_ONLY"
        elif disposition=="NON_RESEARCH":speech="NON_RESEARCH_ONLY"
        else:speech="UNRESOLVED_MEANING"
        embedded=None
        if index in source_risks:
            speech,embedded=source_risks[index]
        judgments=[]
        for claim in target["v176_claims"]:
            def terms(field):
                out=[]
                for ordinal,term in enumerate(claim[field],1):
                    # The reviewer must explicitly anchor original language;
                    # tests search finite source text only to make fixtures.
                    options=[(j,r) for j,r in context.items() if term in r["text"]]
                    missed=(index,field,ordinal) in missing_terms
                    if not options or missed:
                        out.append({"term_ordinal":ordinal,"original_term":term,
                                    "cue_index":None,"source_quote":None,
                                    "source_text_sha256":None,
                                    "status":"UNMAPPED_KEEP_OPEN"})
                    else:
                        j,r=options[0]
                        out.append({"term_ordinal":ordinal,"original_term":term,
                                    "cue_index":j,"source_quote":term,
                                    "source_text_sha256":r["source_text_sha256"],
                                    "status":"SOURCE_EXPLICIT"})
                return out
            judgments.append({
                "claim_id":claim["claim_id"],
                "claim_ordinal":claim["claim_ordinal"],
                "original_claim_sha256":claim["claim_sha256"],
                "source_kind":claim["kind"],
                "speech_act":type_for_kind[claim["kind"]],
                "condition_terms":terms("conditions"),
                "exception_terms":terms("exceptions"),
                "meaning_dependent_fact_open":claim["kind"]=="FACT",
            })
        rows.append({
            "cue_index":index,
            "source_text_sha256":target["source_text_sha256"],
            "v176_event_sha256":target["v176_event_sha256"],
            "source_speaker_role":target["v176_speaker_role"],
            "speech_act":speech,
            "source_quote":target["original_text"],
            "source_meaning_note":NOTES,
            "source_meaning_note_sha256":sha256(NOTES.encode()),
            "reviewer_caution":CAUTION,
            "reviewer_caution_sha256":sha256(CAUTION.encode()),
            "claim_judgments":judgments,
            "cue_numeric_roles":[{
                "ordinal":j+1,"token":token,
                "role":"QUANTITY_SPOKEN_UNVERIFIED"}
                for j,token in enumerate(target["original_numeric_tokens"])],
            "embedded_assertion_quote":embedded,
            "rebuttal_source_links":[],
            "not_original_speaker_quote":True,
            "audio_speaker_verified":False,
            "context_and_counterexamples_checked":True,
            "finance_approved":False,
        })
    return {
        "schema":ANSWER,"challenge_sha256":packet["challenge_sha256"],
        "review_executor":"CHATGPT_IN_CHAT","rows":rows,
        "independent_gold_certified":False,
        "financial_fact_truth_certified":False,
        "e3_e4_e5_authorized":False,
    }


class TestV206LiveSourceCensusFromCurrentE1(unittest.TestCase):
    def setUp(self):
        self.fx=original_e1.TestV202SameInputE1Route(
            "test_01_preseeded_native_v166_cannot_impersonate_v176_verdict")
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.owner=self.fx.owner
        self.head=self.owner.progress()["checkpoint_head_sha256"]
        self.packet=prepare_e2_cue_challenge(
            self.owner,expected_owner_head=self.head,limit=4)
        self.answer=answered(self.packet)

    def audit(self,answer=None,packet=None):
        return audit_e2_cue_answer(
            self.owner,packet or self.packet,answer or self.answer,
            expected_owner_head=self.head)

    def test_01_all_four_cues_three_claims_condition_census_not_quality_go(self):
        result=self.audit()
        self.assertEqual(result["counts"]["cues_checked"],4)
        self.assertEqual(result["counts"]["original_claims_checked"],3)
        self.assertEqual(result["status"],
            "SOURCE_CENSUS_MECHANICALLY_ATTESTED_PENDING_INDEPENDENT_GOLD")
        self.assertFalse(result["e2_real_video_quality_pass"])
        self.assertFalse(result["e3_e4_e5_authorized"])

    def test_02_full_video_batch_split_covers_each_original_cue(self):
        one=prepare_e2_cue_challenge(self.owner,expected_owner_head=self.head,
                                      start_cue=1,limit=2)
        two=prepare_e2_cue_challenge(self.owner,expected_owner_head=self.head,
                                      start_cue=3,limit=2)
        result=audit_full_e2_video(self.owner,[
            {"challenge":one,"answer":answered(one)},
            {"challenge":two,"answer":answered(two)}],
            expected_owner_head=self.head)
        self.assertEqual(result["original_cues_checked"],4)
        self.assertEqual(result["native_atom_reviews"],3)
        self.assertFalse(result["e2_final_pass"])

    def test_03_missing_original_cue_blocked(self):
        one=prepare_e2_cue_challenge(self.owner,expected_owner_head=self.head,
                                      start_cue=1,limit=2)
        with self.assertRaisesRegex(InvalidInput,"FULL_VIDEO_CUE_COVERAGE_MISSING"):
            audit_full_e2_video(self.owner,[
                {"challenge":one,"answer":answered(one)}],
                expected_owner_head=self.head)

    def test_04_duplicate_original_cue_blocked(self):
        with self.assertRaisesRegex(InvalidInput,"FULL_VIDEO_CUE_DOUBLE_COUNT"):
            audit_full_e2_video(self.owner,[
                {"challenge":self.packet,"answer":self.answer},
                {"challenge":self.packet,"answer":self.answer}],
                expected_owner_head=self.head)

    def test_05_qualifier_declared_missing_becomes_hold(self):
        missing=answered(self.packet,missing_terms={(3,"conditions",1)})
        r=self.audit(answer=missing)
        self.assertEqual(r["status"],"HOLD_SEMANTIC_OR_EXTRACTION_LOSS")
        self.assertIn({"cue_index":3,"reason":"UNMAPPED_CONDITIONS"},r["hold_reasons"])

    def test_06_qualifier_erasure_rejected(self):
        bad=copy.deepcopy(self.answer)
        bad["rows"][2]["claim_judgments"][0]["condition_terms"]=[]
        with self.assertRaisesRegex(InvalidInput,"SOURCE_QUALIFIER_CENSUS"):
            self.audit(answer=bad)

    def test_07_qualifier_reforged_as_exception_rejected(self):
        bad=copy.deepcopy(self.answer)
        link=bad["rows"][2]["claim_judgments"][0]
        link["condition_terms"]=[]
        link["exception_terms"]=[{"term_ordinal":1,"original_term":"소득에 따라",
            "cue_index":3,"source_quote":"소득에 따라",
            "source_text_sha256":self.packet["target_cues"][2]["source_text_sha256"],
            "status":"SOURCE_EXPLICIT"}]
        with self.assertRaisesRegex(InvalidInput,"SOURCE_QUALIFIER_CENSUS"):
            self.audit(answer=bad)

    def test_08_original_numeric_role_omission_rejected_even_nonresearch(self):
        i=next(n for n,r in enumerate(self.answer["rows"])
               if r["cue_numeric_roles"])
        bad=copy.deepcopy(self.answer)
        bad["rows"][i]["cue_numeric_roles"]=[]
        with self.assertRaisesRegex(InvalidInput,"WHOLE_CUE_NUMBER_CENSUS"):
            self.audit(answer=bad)

    def test_09_fake_review_as_source_quote_rejected(self):
        bad=copy.deepcopy(self.answer)
        bad["rows"][0]["source_quote"]="상장 ETF 200% 절대 보장"
        with self.assertRaisesRegex(InvalidInput,"QUOTE_SPEAKER_OR_REVIEWER_BOUNDARY"):
            self.audit(answer=bad)

    def test_10_source_kind_or_digest_cannot_be_changed(self):
        bad=copy.deepcopy(self.answer)
        bad["rows"][0]["claim_judgments"][0]["source_kind"]="OPINION"
        with self.assertRaisesRegex(InvalidInput,"CLAIM_KIND_OR_ORIGINAL_SHA_DRIFT"):
            self.audit(answer=bad)

    def test_11_unauthenticated_speaker_becomes_verified_rejected(self):
        bad=copy.deepcopy(self.answer)
        bad["rows"][0]["audio_speaker_verified"]=True
        with self.assertRaisesRegex(InvalidInput,"QUOTE_SPEAKER_OR_REVIEWER_BOUNDARY"):
            self.audit(answer=bad)

    def test_12_gold_or_finance_or_final_step_forgery_rejected(self):
        for key in ("independent_gold_certified","financial_fact_truth_certified",
                    "e3_e4_e5_authorized"):
            bad=copy.deepcopy(self.answer);bad[key]=True
            with self.assertRaisesRegex(InvalidInput,
                                        "REVIEW_DOCUMENT_OR_CUE_CENSUS"):
                self.audit(answer=bad)

    def test_13_fake_challenge_with_self_hash_still_rejected(self):
        from ire.v6.codec import json_digest
        pkt=copy.deepcopy(self.packet)
        pkt["target_cues"][0]["original_text"]="금융 관련 사실을 완전히 지워 버렸습니다"
        pkt["challenge_sha256"]=json_digest({
            k:v for k,v in pkt.items() if k!="challenge_sha256"})
        with self.assertRaisesRegex(InvalidInput,
                                    "CHALLENGE_NOT_CURRENT_OWNER_ISSUED"):
            self.audit(packet=pkt)

    def test_14_forged_rebuttal_link_rejected(self):
        bad=copy.deepcopy(self.answer)
        bad["rows"][0]["rebuttal_source_links"]=[{
            "cue_index":3,"source_quote":"원문에 없는 반박 조건입니다",
            "source_text_sha256":"f"*64,"relation_type":"REBUTTAL"}]
        with self.assertRaisesRegex(InvalidInput,
                                    "REBUTTAL_OR_CONTEXT_QUOTE_FORGED"):
            self.audit(answer=bad)


class TestV206KoreanQuestionQuoteMeaningGap(unittest.TestCase):
    def setUp(self):
        rawtext=[
            "ISA는 8%가, 또 8%가 무조건 비과세라는 주장이 사실인가요?",
            "모든 소득이 비과세된다고 누군가 말했습니다.",
            "제 생각에는 ISA가 유리하지만 조건에 따라 과세될 수 있습니다.",
            "다만 한도 초과분은 과세될 수 있다는 설명입니다.",
        ]
        pieces=[]
        for j,t in enumerate(rawtext,1):
            pieces.append(f"{j}\n00:00:{j:02d},000 --> 00:00:{j:02d},900\n{t}\n")
        self.original=("\n".join(pieces)).encode("utf-8")
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.owner=EngineChatSession(Path(self.t.name)/"owner.sqlite",
            self.original,"E2AbCd12345",owner_source_sha256=sha256(self.original),
            window_size=4,expected_window_count=1)
        task=self.owner.prepare(limit=4,source_first_only=True)
        rows=[]
        for target in task["target_cues"]:
            i=target["cue_index"]
            kind={3:"OPINION",4:"FACT"}
            claims=[]
            if i in kind:
                quote="조건에 따라 과세될 수 있습니다" if i==3 else "한도 초과분은 과세될 수 있다는 설명입니다"
                claims=[{
                    "proposition":"ISA 과세 여부는 조건에 따라 달라질 수 있다는 의견입니다." if i==3
                                  else "한도 초과분에 대해 과세 가능성을 말하는 사실 주장입니다.",
                    "kind":kind[i],"quote":quote,
                    "context_cue_indices":[i],
                    "conditions":["조건에 따라"] if i==3 else [],
                    "exceptions":["한도 초과분"] if i==4 else [],
                    "numeric_tokens":[],"high_risk":True,"needs_official_source":True}]
            rows.append({
                "cue_index":i,"source_text_sha256":target["source_text_sha256"],
                "disposition":{1:"QUESTION",2:"QUOTE"}.get(i,"ASSERTION"),
                "analysis":"자막 원문에서 질문과 인용 및 조건과 예외를 각각 구별하여 연구 관문에 전달합니다.",
                "speaker_role":"HOST","claims":claims,
                "limitations_checked":True,
            })
        self.owner.submit(task,{"schema":COMMIT,
            "challenge_sha256":task["challenge_sha256"],
            "review_executor":"CHATGPT_IN_CHAT","responses":rows})
        self.head=self.owner.progress()["checkpoint_head_sha256"]
        self.packet=prepare_e2_cue_challenge(
            self.owner,expected_owner_head=self.head,limit=4)
        self.assertEqual([x["v176_disposition"] for x in self.packet["target_cues"]],
                         ["QUESTION","QUOTE","ASSERTION","ASSERTION"])

    def test_15_embedded_question_and_quoted_claim_do_not_disappear_as_noatom(self):
        answer=answered(self.packet,source_risks={
            1:("QUESTION_WITH_EMBEDDED_ASSERTION","8%가 무조건 비과세"),
            2:("QUOTE_WITH_FACT_DEPENDENCY","모든 소득이 비과세"),
        })
        r=audit_e2_cue_answer(self.owner,self.packet,answer,
                              expected_owner_head=self.head)
        self.assertEqual(r["status"],"HOLD_SEMANTIC_OR_EXTRACTION_LOSS")
        reasons={(x["cue_index"],x["reason"]) for x in r["hold_reasons"]}
        self.assertIn((1,"EMBEDDED_ASSERTION_EXCLUDED_BY_V176"),reasons)
        self.assertIn((2,"EMBEDDED_ASSERTION_EXCLUDED_BY_V176"),reasons)
        self.assertEqual(r["counts"]["numerical_tokens"],2)
        self.assertEqual(r["counts"]["original_claims_checked"],2)
        self.assertFalse(r["e2_real_video_quality_pass"])

    def test_16_conditions_and_exceptions_separate_source_quote_and_roles(self):
        r=audit_e2_cue_answer(self.owner,self.packet,answered(self.packet),
                              expected_owner_head=self.head)
        self.assertEqual(r["counts"]["original_claims_checked"],2)
        self.assertEqual(r["status"],
            "SOURCE_CENSUS_MECHANICALLY_ATTESTED_PENDING_INDEPENDENT_GOLD")
        bad=answered(self.packet)
        bad["rows"][3]["claim_judgments"][0]["exception_terms"][0][
            "source_quote"]="고정 절세 보장"
        with self.assertRaisesRegex(InvalidInput,"QUALIFIER_SOURCE_QUOTE_UNVERIFIED"):
            audit_e2_cue_answer(self.owner,self.packet,bad,expected_owner_head=self.head)

    def test_17_missing_quote_proof_cannot_be_called_embedded_assertion_review(self):
        a=answered(self.packet,source_risks={
            1:("QUESTION_WITH_EMBEDDED_ASSERTION",None)})
        with self.assertRaisesRegex(InvalidInput,"EMBEDDED_ASSERTION_QUOTE_REQUIRED"):
            audit_e2_cue_answer(self.owner,self.packet,a,expected_owner_head=self.head)

    def test_18_noauto_fact_promote_for_question_or_quote(self):
        bad=answered(self.packet)
        bad["rows"][0]["speech_act"]="FINANCIAL_FACT_ASSERTION"
        with self.assertRaisesRegex(InvalidInput,
                                   "NONASSERTION_MISLABELLED_AS_APPROVED_FACT"):
            audit_e2_cue_answer(self.owner,self.packet,bad,
                                expected_owner_head=self.head)

    def test_19_repeated_numeric_token_cannot_lose_one_occurrence(self):
        original=answered(self.packet)
        self.assertEqual([x["token"] for x in original["rows"][0]["cue_numeric_roles"]],
                         ["8%","8%"])
        original["rows"][0]["cue_numeric_roles"].pop()
        with self.assertRaisesRegex(InvalidInput,"WHOLE_CUE_NUMBER_CENSUS"):
            audit_e2_cue_answer(self.owner,self.packet,original,
                                expected_owner_head=self.head)


class TestV206UnsupportedAnecdote(unittest.TestCase):
    def setUp(self):
        from test_v176_chat_engine_loop import (
            TestCollaborativeEngine,respond)
        self.fixture=TestCollaborativeEngine(
            "test_12_unmappable_anecdote_remains_unresolved")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.owner=self.fixture.session
        task=self.owner.prepare(limit=3)
        result=respond(task,add_claim=True)
        result["responses"][1]["claims"][0]["kind"]="ANECDOTE"
        self.owner.submit(task,result)
        self.head=self.owner.progress()["checkpoint_head_sha256"]

    def test_20_unmappable_anecdote_still_has_its_source_claim_in_e2(self):
        packet=prepare_e2_cue_challenge(self.owner,
            expected_owner_head=self.head,start_cue=2,limit=1)
        original=packet["target_cues"][0]
        self.assertEqual(original["native_projection_status"],"UNSUPPORTED_ANECDOTE")
        self.assertEqual(len(original["v176_claims"]),1)
        self.assertIsNone(original["v176_claims"][0]["claim_id"])
        reviewed=answered(packet)
        result=audit_e2_cue_answer(self.owner,packet,reviewed,
                                  expected_owner_head=self.head)
        self.assertEqual(result["status"],"HOLD_SEMANTIC_OR_EXTRACTION_LOSS")
        self.assertEqual(result["counts"]["original_claims_checked"],1)
        self.assertEqual(result["counts"]["native_atom_reviews"],0)
        self.assertIn({"cue_index":2,"reason":"UNSUPPORTED_SOURCE_ANECDOTE_NOT_IN_V6"},
                      result["hold_reasons"])

    def test_21_unsupported_source_claim_must_not_gain_a_fake_v6_id(self):
        packet=prepare_e2_cue_challenge(self.owner,
            expected_owner_head=self.head,start_cue=2,limit=1)
        reply=answered(packet)
        reply["rows"][0]["claim_judgments"][0]["claim_id"]="C00001"
        with self.assertRaisesRegex(InvalidInput,"CLAIM_KIND_OR_ORIGINAL_SHA_DRIFT"):
            audit_e2_cue_answer(self.owner,packet,reply,
                                expected_owner_head=self.head)


if __name__=="__main__":
    unittest.main()
