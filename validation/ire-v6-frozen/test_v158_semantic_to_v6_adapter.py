"""V157 ChatGPT-to-V6 adapter tests using invented source only."""
from __future__ import annotations
import copy
import unittest

from ire.v6.tests.test_source_and_proof import make_srt, make_manifest, VIDEO
from ire.v6.source import verify_source
from ire.v6.codec import sha256, json_digest
from ire.v6.atomic_exchange import NUMBER, audit_host_atomic_exchange
from ire.v6.errors import InvalidInput
from v158_semantic_to_v6_adapter import apply_chat_review_to_v6_exchange


class V158AdapterTests(unittest.TestCase):
    def setUp(self):
        raw = make_srt([
            "개인 투자 의견입니다.",
            "투자를 한다면 손실 가능성을 봅니다.",
            "언제 매도해야 할까요?",
            "그게 질문입니다?",
        ])
        m = make_manifest(raw, cut=2)
        src = verify_source(raw, m, expected_source_sha256=sha256(raw),
                            expected_manifest_sha256=json_digest(m))
        self.source = src
        a = [
            {"claim_id":"C00001","owner_window_id":"W00001",
             "proposition":"주관적 투자 평가를 말한다.",
             "kind":"FACT","stance":"UNRESOLVED","speaker":"UNKNOWN",
             "source_refs":[{"cue_index":1,"quote":src.cues[0].text}],
             "context_cue_indices":[1,2],"condition_cue_indices":[],
             "exception_cue_indices":[],"numeric_references":[],"as_of":None},
            {"claim_id":"C00002","owner_window_id":"W00002",
             "proposition":"화자가 투자 매도 시점을 질문한다.",
             "kind":"OPINION","stance":"UNRESOLVED","speaker":"UNKNOWN",
             "source_refs":[{"cue_index":3,"quote":src.cues[2].text}],
             "context_cue_indices":[3],"condition_cue_indices":[],
             "exception_cue_indices":[],"numeric_references":[],"as_of":None}
        ]
        rows=[]
        for i in range(1,5):
            selected=i in (1,3)
            rows.append({
                "cue_index":i,"cue_text_sha256":sha256(src.cues[i-1].text.encode()),
                "disposition":"CANDIDATES" if selected else "NO_ATOM",
                "claim_ids":[f"C0000{1 if i==1 else 2}"] if selected else [],
                "numeric_tokens":NUMBER.findall(src.cues[i-1].text),
                "note":"" if selected else "문장 또는 조건부 배경 문맥"
            })
        self.exchange={
            "schema":"IRE_V6_HOST_ATOMIC_EXCHANGE_V1",
            "video_id":VIDEO,"source_sha256":sha256(raw),
            "manifest_sha256":json_digest(m),
            "atoms":a,"cue_dispositions":rows
        }
        audit_host_atomic_exchange(src,self.exchange)
        self.decisions=[
            self.make("C00001","SET_KIND",{"kind":"OPINION"}),
            self.make("C00001","SET_CONDITIONAL",{"condition_cue_indices":[2]}),
            self.make("C00002","SET_KIND",{"kind":"QUESTION"}),
            self.make("C00002","EXTEND_QUESTION",
                      {"cue_indices":[4],"speaker":"QUESTIONER"})
        ]

    def make(self,cid,action,payload):
        atom=next(x for x in self.exchange["atoms"] if x["claim_id"]==cid)
        return {"claim_id":cid,"action":action,
                "before_sha256":json_digest(atom),
                "review_sha256":"a"*64,"payload":payload}

    def test_actual_v6_source_audit_4_changes_no_approval(self):
        fixed,report=apply_chat_review_to_v6_exchange(
            self.source,self.exchange,self.decisions)
        self.assertEqual(report["change_count"],4)
        self.assertFalse(report["native_host_committed"])
        self.assertFalse(report["chat_v123_final_approved"])
        self.assertEqual(fixed["atoms"][0]["kind"],"OPINION")
        self.assertEqual(fixed["atoms"][0]["stance"],"CONDITIONAL")
        self.assertEqual(fixed["atoms"][1]["speaker"],"QUESTIONER")
        self.assertEqual([x["cue_index"] for x in fixed["atoms"][1]["source_refs"]],[3,4])
        self.assertEqual(self.exchange["cue_dispositions"][3]["disposition"],"NO_ATOM")
        audit_host_atomic_exchange(self.source,fixed)

    def test_stale_atom_hash_rejected(self):
        x=copy.deepcopy(self.decisions);x[0]["before_sha256"]="0"*64
        with self.assertRaises(InvalidInput):
            apply_chat_review_to_v6_exchange(self.source,self.exchange,x)

    def test_duplicate_action_rejected(self):
        with self.assertRaises(InvalidInput):
            apply_chat_review_to_v6_exchange(self.source,self.exchange,
                                            self.decisions+[self.decisions[0]])

    def test_question_wrong_source_ref_rejected(self):
        x=copy.deepcopy(self.decisions);x[3]["payload"]["cue_indices"]=[2]
        with self.assertRaises(InvalidInput):
            apply_chat_review_to_v6_exchange(self.source,self.exchange,x)

    def test_condition_outside_context_rejected(self):
        x=copy.deepcopy(self.decisions)
        x[1]["payload"]["condition_cue_indices"]=[4]
        with self.assertRaises(InvalidInput):
            apply_chat_review_to_v6_exchange(self.source,self.exchange,x)

    def test_forged_review_digest_rejected(self):
        x=copy.deepcopy(self.decisions);x[2]["review_sha256"]="fake"
        with self.assertRaises(InvalidInput):
            apply_chat_review_to_v6_exchange(self.source,self.exchange,x)



    def test_v158_explicit_affirmed_video_speech_act_not_financial_truth(self):
        self.exchange["atoms"][0]["context_cue_indices"]=[1]
        decision=self.make("C00001","SET_STANCE_AFFIRMED",{"stance":"AFFIRMED"})
        fixed,receipt=apply_chat_review_to_v6_exchange(self.source,self.exchange,[decision])
        self.assertEqual(fixed["atoms"][0]["stance"],"AFFIRMED")
        self.assertEqual(receipt["changes"][0]["financial_fact_truth_approved"],False)
        self.assertFalse(receipt["native_host_committed"])
        self.assertFalse(receipt["chat_v123_final_approved"])

    def test_v158_question_cannot_be_affirmed(self):
        self.exchange["atoms"][1]["kind"]="QUESTION"
        decision=self.make("C00002","SET_STANCE_AFFIRMED",{"stance":"AFFIRMED"})
        with self.assertRaises(InvalidInput):
            apply_chat_review_to_v6_exchange(self.source,self.exchange,[decision])

    def test_v158_affirmed_cannot_be_fabricated_quote(self):
        self.exchange["atoms"][0]["context_cue_indices"]=[1]
        decision=self.make("C00001","SET_STANCE_AFFIRMED",{"stance":"QUOTED"})
        with self.assertRaises(InvalidInput):
            apply_chat_review_to_v6_exchange(self.source,self.exchange,[decision])

    def test_v158_stale_affirmed_before_hash_fails(self):
        self.exchange["atoms"][0]["context_cue_indices"]=[1]
        decision=self.make("C00001","SET_STANCE_AFFIRMED",{"stance":"AFFIRMED"})
        decision["before_sha256"]="0"*64
        with self.assertRaises(InvalidInput):
            apply_chat_review_to_v6_exchange(self.source,self.exchange,[decision])

    def test_v158_duplicated_stance_action_fails(self):
        self.exchange["atoms"][0]["context_cue_indices"]=[1]
        decision=self.make("C00001","SET_STANCE_AFFIRMED",{"stance":"AFFIRMED"})
        with self.assertRaises(InvalidInput):
            apply_chat_review_to_v6_exchange(self.source,self.exchange,[decision,decision])

if __name__=="__main__":
    unittest.main()
