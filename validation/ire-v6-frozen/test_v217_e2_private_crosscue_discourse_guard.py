"""V217 private source discourse guard: synthetic inputs only in public CI."""
from __future__ import annotations
import copy
import json
import unittest
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.atomic_exchange import NUMBER, audit_host_atomic_exchange
from v176_chat_engine_loop import make_original_plan
from v217_e2_private_crosscue_discourse_guard import (
    audit_private_crosscue_discourse,require_no_unresolved_discourse_for_approval,
)

RAW=(
    "1\n00:00:01,000 --> 00:00:01,500\nETF는 펀드의 일종입니다.\n\n"
    "2\n00:00:02,000 --> 00:00:02,500\nISA에 연 8% 보장 여부를 묻습니다.\n\n"
    "3\n00:00:03,000 --> 00:00:03,500\n다만 한도를 초과하면 달라질 수 있습니다.\n\n"
    "4\n00:00:04,000 --> 00:00:04,500\n감사합니다.\n"
).encode("utf-8")


class TestV217CrossCueDiscourseGuard(unittest.TestCase):
    @staticmethod
    def dumps(x):
        return (json.dumps(x,ensure_ascii=False,indent=2)+"\n").encode("utf-8")

    def setUp(self):
        self.source,_=make_original_plan(RAW,"Synth123456",
            expected_source_sha256=sha256(RAW),window_size=2)
        cues=self.source.cues
        self.exchange={
            "schema":"IRE_V6_HOST_ATOMIC_EXCHANGE_V1",
            "video_id":self.source.video_id,
            "source_sha256":self.source.source_sha256,
            "manifest_sha256":self.source.manifest_sha256,
            "cue_dispositions":[],
            "atoms":[{
                "claim_id":"C00001","owner_window_id":self.source.owner(1),
                "proposition":"ETF는 펀드의 일종입니다.","kind":"FACT",
                "stance":"UNRESOLVED","speaker":"UNKNOWN",
                "source_refs":[{"cue_index":1,"quote":cues[0].text}],
                "context_cue_indices":[1,2],
                "condition_cue_indices":[],"exception_cue_indices":[],
                "numeric_references":[],"as_of":None,
            },{
                "claim_id":"C00002","owner_window_id":self.source.owner(3),
                "proposition":"한도를 초과하면 적용이 달라질 수 있습니다.",
                "kind":"HYPOTHETICAL","stance":"UNRESOLVED","speaker":"UNKNOWN",
                "source_refs":[{"cue_index":3,"quote":cues[2].text}],
                "context_cue_indices":[3],"condition_cue_indices":[3],
                "exception_cue_indices":[],"numeric_references":[],"as_of":None,
            }],
        }
        for i,c in enumerate(cues,1):
            ids={1:["C00001"],3:["C00002"]}.get(i,[])
            self.exchange["cue_dispositions"].append({
                "cue_index":i,"cue_text_sha256":sha256(c.text.encode("utf-8")),
                "disposition":"CANDIDATES" if ids else "UNRESOLVED",
                "claim_ids":ids,"numeric_tokens":NUMBER.findall(c.text),
                "note":"원문에 근거한 미승인 의미 점검 필요",
            })
        audit_host_atomic_exchange(self.source,self.exchange)
        def edge(n,i,j,rtype):
            a,b=cues[i-1].text,cues[j-1].text
            return {"relation_id":f"V217R-{n:03}",
                "from_cue":i,"to_cue":j,"from_quote":a,"to_quote":b,
                "from_source_text_sha256":sha256(a.encode("utf-8")),
                "to_source_text_sha256":sha256(b.encode("utf-8")),
                "relation_type":rtype,
                "chat_reviewer_interpretation_not_source_speaker":
                    "원문을 근거로 검토자가 판단한 미승인 관계입니다.",
                "semantic_relation_independently_confirmed":False,
                "financial_fact_approved":False}
        self.ledger={
            "schema":"IRE_V211_1_PRIVATE_ETF_CROSS_CUE_CONTEXT_RELATIONS_V1",
            "video_id":self.source.video_id,
            "original_source_sha256":sha256(RAW),"total_cues":4,
            "relation_count":3,
            "relations":[edge(1,1,3,"REBUTTAL_SCOPE"),
                         edge(2,1,2,"QUESTION_CONTEXT"),
                         edge(3,3,4,"EXCEPTION")],
            "each_relation_has_both_original_quotes":True,
            "chat_review_of_relation_not_external_gold":True,
            "e2_final_pass":False,"e3_e4_e5_authorized":False,
            "financial_truth_certified":False,"native_v6_claims_issued":False,
        }

    def audit(self,exchange=None,ledger=None,raw=RAW,
              native_bytes=None,ledger_bytes=None,
              expected_native=None,expected_ledger=None):
        ex=self.exchange if exchange is None else exchange
        le=self.ledger if ledger is None else ledger
        nb=self.dumps(ex) if native_bytes is None else native_bytes
        lb=self.dumps(le) if ledger_bytes is None else ledger_bytes
        return audit_private_crosscue_discourse(raw,ex,nb,le,lb,
            expected_source_sha256=sha256(RAW),
            expected_exchange_sha256=(sha256(nb) if expected_native is None
                                      else expected_native),
            expected_ledger_sha256=(sha256(lb) if expected_ledger is None
                                      else expected_ledger),window_size=2)

    def test_01_cross_atom_rebuttal_not_silently_merged(self):
        r=self.audit()
        self.assertEqual((r["source_relations_checked"],
                          r["same_atom_context_relations"],
                          r["cross_atom_unresolved_relations"],
                          r["unmapped_cue_relations"]),(3,1,1,1))
        self.assertFalse(r["e2_final_pass"])
        self.assertFalse(r["independent_semantic_gold_certified"])
        self.assertNotIn("ETF는 펀드",str(r))

    def test_02_unresolved_cross_atom_release_blocked(self):
        with self.assertRaisesRegex(InvalidInput,"UNRESOLVED_RELATIONS_BLOCK_APPROVAL"):
            require_no_unresolved_discourse_for_approval(self.audit())

    def test_03_even_no_edges_cannot_forge_gold(self):
        d=self.audit()
        d["cross_atom_unresolved_relations"]=0
        d["unmapped_cue_relations"]=0
        with self.assertRaisesRegex(InvalidInput,"INDEPENDENT_MEANING_GOLD_NOT_ATTESTED"):
            require_no_unresolved_discourse_for_approval(d)

    def test_04_source_sha_changed_fails(self):
        with self.assertRaisesRegex(InvalidInput,"ORIGINAL_SOURCE_BYTES_CHANGED"):
            self.audit(raw=RAW+b" ")

    def test_05_native_original_bytes_changed_fails(self):
        with self.assertRaisesRegex(InvalidInput,"NATIVE_BYTE_TAMPER"):
            self.audit(native_bytes=self.dumps(self.exchange)+b" ",
                       expected_native=sha256(self.dumps(self.exchange)))

    def test_06_ledger_original_bytes_changed_fails(self):
        with self.assertRaisesRegex(InvalidInput,"LEDGER_BYTE_TAMPER"):
            self.audit(ledger_bytes=self.dumps(self.ledger)+b" ",
                       expected_ledger=sha256(self.dumps(self.ledger)))

    def test_07_unspoken_quote_rejected(self):
        d=copy.deepcopy(self.ledger)
        d["relations"][0]["from_quote"]="원금 보장을 약속"
        with self.assertRaisesRegex(InvalidInput,"RELATION_QUOTE_OR_SOURCE_SHA_CHANGED"):
            self.audit(ledger=d)

    def test_08_fake_external_gold_rejected(self):
        d=copy.deepcopy(self.ledger)
        d["relations"][0]["semantic_relation_independently_confirmed"]=True
        with self.assertRaisesRegex(InvalidInput,"RELATION_ID_SCOPE_OR_FALSE_GOLD"):
            self.audit(ledger=d)

    def test_09_duplicate_relation_ids_rejected(self):
        d=copy.deepcopy(self.ledger)
        d["relations"][1]["relation_id"]=d["relations"][0]["relation_id"]
        with self.assertRaisesRegex(InvalidInput,"RELATION_ID_SCOPE_OR_FALSE_GOLD"):
            self.audit(ledger=d)

    def test_10_bad_relation_index_not_typeerror(self):
        d=copy.deepcopy(self.ledger)
        d["relations"][0]["from_cue"]=[]
        with self.assertRaisesRegex(InvalidInput,"RELATION_ID_SCOPE_OR_FALSE_GOLD"):
            self.audit(ledger=d)

    def test_11_wrong_relation_cue_hash_rejected(self):
        d=copy.deepcopy(self.ledger)
        d["relations"][1]["to_source_text_sha256"]="f"*64
        with self.assertRaisesRegex(InvalidInput,"RELATION_QUOTE_OR_SOURCE_SHA_CHANGED"):
            self.audit(ledger=d)

    def test_12_no_fake_e2_approval(self):
        d=copy.deepcopy(self.ledger)
        d["e2_final_pass"]=True
        with self.assertRaisesRegex(InvalidInput,"LEDGER_CUSTODY_OR_FALSE_APPROVAL"):
            self.audit(ledger=d)

    def test_13_incomplete_relation_census_blocked(self):
        d=copy.deepcopy(self.ledger)
        d["relation_count"]=5
        with self.assertRaisesRegex(InvalidInput,"BOUNDED_RELATION_CENSUS"):
            self.audit(ledger=d)

    def test_14_no_unverified_speaker_promotion(self):
        d=copy.deepcopy(self.exchange)
        d["atoms"][0]["speaker"]="NARRATOR"
        with self.assertRaisesRegex(InvalidInput,"UNAPPROVED_ATOM_REQUIRED"):
            self.audit(exchange=d)

    def test_15_restart_deterministic_and_unpublished(self):
        a=self.audit();b=self.audit()
        self.assertEqual(a,b)
        self.assertFalse(a["automatic_merge"])
        self.assertFalse(a["knowledge_published"])


if __name__=="__main__":
    unittest.main()
