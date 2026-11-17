"""E4 source-kind authority taxonomy — synthetic only; V123 unchanged."""
from __future__ import annotations
import copy
import unittest
from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput
from test_v123_chat_final_gate import ChatFinalGateTests
from v166_e4_typed_authority import (
    SCHEMA, CLASS_TO_KIND, audit_e4_source_type_inventory,
)

NOTE=("ChatGPT 합성 출처 분류: 이 원자에 요구되는 적절한 1차 근거기관과 "
      "기존 발화의 사실·의견·질문 성격을 분리합니다. 고위험 금융 표시만으로 "
      "법령의 적용이 입증되었다고 해석하지 않고 현재의 V123 원자별 "
      "상태를 절대 바꾸지 않으며 개인별 자문을 승인하지 않습니다.")


class V166E4TypedEvidenceRoutes(unittest.TestCase):
    def setUp(self):
        fx=ChatFinalGateTests("test_01_real_native_v6_batch_then_synthetic_chat_final_pass")
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        self.fx=fx
        self.exchange=copy.deepcopy(fx.exchange)
        self.review=copy.deepcopy(fx.review)
        # Reclassify nonfinancial source speech *synthetically*, while
        # retaining original cue and V6 atom/source hashes.
        a=self.exchange["atoms"]
        a[1]["kind"]="OPINION"
        a[2]["kind"]="QUESTION"
        for atom,v in zip(a,self.review["atom_verdicts"]):
            v["atom_sha256"]=json_digest(atom)
        self.review["atom_verdicts"][1]["status"]="OPEN"
        self.categories=[
            "STATUTORY_FINANCIAL_RULE",
            "PERSONAL_SUBJECTIVE_OPINION",
            "HYPOTHETICAL_OR_QUESTION",
        ]
        self.inventory=self._make()

    def _make(self):
        rows=[]
        for a,v,cat in zip(self.exchange["atoms"],self.review["atom_verdicts"],
                           self.categories):
            cue_idx=a["source_refs"][0]["cue_index"]
            quote=a["source_refs"][0]["quote"]
            rows.append({
                "claim_id":a["claim_id"],
                "atom_sha256":json_digest(a),
                "original_cue_index":cue_idx,
                "original_cue_quote":quote,
                "original_cue_quote_sha256":sha256(quote.encode("utf-8")),
                "evidence_class":cat,
                "authority_route":CLASS_TO_KIND[cat][1],
                "source_evidence_scope_note":NOTE,
                "source_evidence_scope_note_sha256":sha256(NOTE.encode("utf-8")),
                "v123_original_status":v["status"],
                "unchanged_v123_review_note_sha256":v["private_review_note_sha256"],
                "financial_claim_flag_only_screening_not_legal_proof":True,
                "reviewer_not_speaker_quote":True,
                "primary_verification_complete":False,
                "independent_gold_certified":False,
                "personal_advice_approved":False,
            })
        return {
            "schema":SCHEMA,
            "source_sha256":self.fx.source.source_sha256,
            "manifest_sha256":self.fx.source.manifest_sha256,
            "chat_review_sha256":json_digest(self.review),
            "review_executor":"CHATGPT_IN_CHAT",
            "rows":rows,
            "private_reviewer_custody_sha256":sha256(b"synthetic taxonomy"),
            "any_v123_status_changed":False,
            "any_fact_autoapproved":False,
            "formal_current_law_certified":False,
            "personal_advice_approved":False,
        }

    def run_audit(self, inventory=None):
        return audit_e4_source_type_inventory(
            self.fx.source,self.exchange,self.review,
            self.inventory if inventory is None else inventory)

    def test_01_factual_legal_opinion_question_distinct_authority_routes(self):
        r=self.run_audit()
        self.assertEqual(r["atom_census"],3)
        self.assertEqual(r["actual_statutory_rule_atom_count"],1)
        self.assertEqual(r["nonstatutory_financial_or_highrisk_screening_count"],2)
        self.assertTrue(r["legacy_highrisk_flag_cannot_prove_statutory_authority"])
        self.assertTrue(r["all_v123_verdicts_unchanged"])
        self.assertFalse(r["research_knowledge_release_authorized"])

    def test_02_open_subjective_opinion_not_promoted(self):
        doc=self._make()
        self.assertEqual(doc["rows"][1]["v123_original_status"],"OPEN")
        self.assertFalse(self.run_audit(doc)["final_chat_approval_granted"])

    def test_03_wrong_opinion_issuer_legal_route_fails(self):
        d=self._make()
        d["rows"][1]["evidence_class"]="STATUTORY_FINANCIAL_RULE"
        d["rows"][1]["authority_route"]="GOVERNMENT_LEGAL_PRIMARY"
        with self.assertRaisesRegex(InvalidInput,"ATOMIC_KIND_OR_PRIMARY_AUTHORITY"):
            self.run_audit(d)

    def test_04_missing_one_atom_does_not_silently_pass(self):
        d=self._make()
        d["rows"].pop()
        with self.assertRaisesRegex(InvalidInput,"ATOMIC_REVIEW_CENSUS"):
            self.run_audit(d)

    def test_05_video_question_cannot_be_bibliographic_assertion(self):
        d=self._make()
        d["rows"][2]["evidence_class"]="PUBLISHER_BOOK_BIBLIOGRAPHY"
        d["rows"][2]["authority_route"]="ORIGINAL_PUBLISHER_PRIMARY"
        with self.assertRaisesRegex(InvalidInput,"ATOMIC_KIND_OR_PRIMARY_AUTHORITY"):
            self.run_audit(d)

    def test_06_wrong_atom_direct_quote_fails(self):
        d=self._make()
        d["rows"][1]["original_cue_index"]=1
        d["rows"][1]["original_cue_quote"]=self.fx.source.cues[0].text
        d["rows"][1]["original_cue_quote_sha256"]=sha256(
            d["rows"][1]["original_cue_quote"].encode("utf-8"))
        with self.assertRaisesRegex(InvalidInput,"SOURCE_FIRST_CUE_OR_VERBATIM_QUOTE"):
            self.run_audit(d)

    def test_07_new_chat_verdict_cannot_be_smuggled_into_old_review(self):
        d=self._make()
        d["rows"][1]["v123_original_status"]="ACCEPT_FOR_RESEARCH"
        with self.assertRaisesRegex(InvalidInput,"V123_VERDICT_OR_ATOM_CHANGED"):
            self.run_audit(d)

    def test_08_false_primary_verification_flag_cannot_produce_approval(self):
        d=self._make()
        d["rows"][1]["primary_verification_complete"]=True
        with self.assertRaisesRegex(InvalidInput,"CLASSIFICATION_NOT_PRIMARY_VERIFICATION"):
            self.run_audit(d)

    def test_09_reviewer_scope_note_not_speaker_quote_and_digest_pin(self):
        d=self._make()
        d["rows"][0]["source_evidence_scope_note"]="변조된 검토자 의견"
        with self.assertRaisesRegex(InvalidInput,"SOURCE_MEANING_OR_REVIEWER_CAUTION"):
            self.run_audit(d)

    def test_10_numeric_highrisk_legacy_flag_not_an_issuer_type(self):
        d=self._make()
        d["rows"][0]["financial_claim_flag_only_screening_not_legal_proof"]=False
        with self.assertRaisesRegex(InvalidInput,"SOURCE_MEANING_OR_REVIEWER_CAUTION"):
            self.run_audit(d)

    def test_11_cross_video_source_replay_is_rejected(self):
        d=self._make()
        d["source_sha256"]="f"*64
        with self.assertRaisesRegex(InvalidInput,"REVIEW_PIN_OR_FALSE_APPROVAL"):
            self.run_audit(d)

if __name__=="__main__":
    unittest.main()
