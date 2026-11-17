"""E4 mixed LAW + OPINION REAL V6/V123/V128 code with synthetic text.

This is different from unit tests that mutate cases after V6 registration:
the actual host atomic transaction is constructed from a four-cue synthetic
SRT with 2 factual financial claims plus 1 attributed subjective opinion.
Every V123/V127.1/E3 approval uses the REAL unchanged native gate, and every
research publication uses the real V128/V126 SQLite components. Official
government source bytes are mocked, so no real legal truth is claimed.
"""
from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from ire.v6.codec import ZERO_SHA
from ire.v6.errors import InvalidInput,QualityNotProven
from ire.v6.tests import test_atomic_exchange as atomic_module
from ire.v6.tests.test_atomic_exchange import HostAtomExchangeTests
from ire.v6.tests.test_source_and_proof import make_srt
from test_v166_e3_chat_decision_delivery import V166E3NativeDecisionDelivery
from test_v166_e4_primary_approval_gate import (
    BODY,make_manifest,make_typed_inventory_for_legal_synthetic_case,
    make_nonlegal_manifest_for_case,replace_synthetic_official_body)
from v166_e4_sealed_knowledge import E4SealedKnowledgeStore
from v166_e4_primary_approval_gate import run_e4_guarded_parent

OPINION=("개인적으로는 장기 투자습관을 꾸준히 유지하는 편이 더 "
         "마음 편하다고 생각합니다.")
NOTE=("이 문장은 정식 법령이나 투자수익의 객관적 진위가 아니라 원문 화자의 "
      "개인적 판단이라는 사실만 보존합니다. 숫자나 매매 명령, 확정 수익률, "
      "원금 보장, 세제적용 조건을 화자의 의견에서 추론하여 새로운 사실로 "
      "만들지 않으며 금융 법령에 관한 법률 적합성도 입증하지 않습니다.")


class V166E4MixedOriginalSourceParent(unittest.TestCase):
    def setUp(self):
        raw=make_srt([
            "연금저축의 예상 수익은 10%입니다.",
            "하지만 실제로는 8%일 수 있습니다.",
            OPINION,
            "일반 교육 안내입니다.",
        ])
        original=HostAtomExchangeTests.sample

        def typed_sample(testcase):
            e=original(testcase)
            third=e["atoms"][2]
            third["kind"]="OPINION"
            third["stance"]="AFFIRMED"
            third["proposition"]="화자는 개인적으로 장기 투자습관이 편하다고 생각한다"
            third["context_cue_indices"]=[3]
            third["condition_cue_indices"]=[]
            third["exception_cue_indices"]=[]
            third["numeric_references"]=[]
            return e

        self.h=V166E3NativeDecisionDelivery(
            "test_01_all_chat_approved_children_preserve_research_only_pass")
        with patch.object(atomic_module,"make_srt",return_value=raw),patch.object(
                 HostAtomExchangeTests,"sample",typed_sample):
            self.h.setUp()
        self.addCleanup(self.h.doCleanups)
        self.fx=self.h.fx
        self.fx.knowledge=E4SealedKnowledgeStore(
            self.fx.knowledge.path,
            external_signing_key=b"SYNTHETIC_MIXED_NATIVE_SOURCE_TEST_KEY_"*2)
        self.legal_manifests={}
        self.typed_inventories={}
        self.nonlegal_manifests={}
        self.segments=list(self.fx.checkpoint.child_ids)
        self.assertEqual(len(self.segments),2)
        for idx,(sid,packet) in enumerate(zip(self.segments,self.fx.packets)):
            case=packet["case"]
            replace_synthetic_official_body(case)
            primary=make_manifest(case)
            classes={}
            if idx==1:
                self.assertEqual(len(case["exchange"]["atoms"]),1)
                self.assertEqual(case["exchange"]["atoms"][0]["kind"],"OPINION")
                classes[case["exchange"]["atoms"][0]["claim_id"]]=(
                    "PERSONAL_SUBJECTIVE_OPINION")
                primary["rows"]=[]
            typed=make_typed_inventory_for_legal_synthetic_case(
                case,evidence_classes=classes)
            nonlegal_rows=[]
            if idx==1:
                atom=case["exchange"]["atoms"][0]
                src=atom["source_refs"][0]["quote"]
                from ire.v6.codec import sha256
                nonlegal_rows.append({
                    "claim_id":atom["claim_id"],
                    "evidence_class":"PERSONAL_SUBJECTIVE_OPINION",
                    "authority_route":"SOURCE_ONLY_NO_OBJECTIVE_TRUTH",
                    "source_quote_sha256":sha256(src.encode("utf-8")),
                    "chat_meaning_note":NOTE,
                    "chat_meaning_note_sha256":sha256(NOTE.encode("utf-8")),
                    "primary_url":None,"primary_body_sha256":None,
                    "verification_mode":"SOURCE_ONLY_SPEAKER_ATTRIBUTION",
                    "original_speaker_audio_verified":False,
                    "formal_financial_fact_certified":False,
                    "personal_advice_approved":False,
                })
            self.legal_manifests[sid]=primary
            self.typed_inventories[sid]=typed
            self.nonlegal_manifests[sid]=make_nonlegal_manifest_for_case(
                case,typed,rows=nonlegal_rows)

    def run_e4(self):
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=BODY):
            return run_e4_guarded_parent(
                self.fx.checkpoint,self.fx.knowledge,
                review_or_load_child=self.fx.child,
                review_seams=self.fx.seams,
                review_parent=self.fx.parent_review,
                primary_manifest_for_child=lambda sid,case:self.legal_manifests.get(sid),
                typed_inventory_for_child=lambda sid,case:self.typed_inventories.get(sid),
                typed_manifest_for_child=lambda sid,case:self.nonlegal_manifests.get(sid),
                expected_knowledge_head=ZERO_SHA,
                now_as_of="2026-11-17")

    def test_01_native_real_e1_e3_e4_mixed_law_opinion_parent_atomic_publish(self):
        result=self.run_e4()
        self.assertEqual(result["status"],"E4_PARENT_RESEARCH_CANDIDATES_PUBLISHED")
        self.assertTrue(result["e4_durable_certification_verified"])
        self.assertEqual(len(result["child_preflights"]),2)
        self.assertEqual(self.fx._counts(),
                         {"events":3,"knowledge":3,"parent_publications":1})
        verified=self.fx.knowledge.verify_e4_certificate(
            externally_pinned_seal_sha256=result["e4_external_owner_pin_sha256"])
        self.assertEqual(verified["approved_child_receipts_count"],2)
        self.assertFalse(verified["source_finance_fact_legally_certified"])
        self.assertFalse(result["personal_advice_approved"])

    def test_02_no_evidence_row_for_opinion_blocks_entire_parent(self):
        self.nonlegal_manifests[self.segments[1]]["rows"]=[]
        with self.assertRaisesRegex(InvalidInput,"ALL_ACCEPTED_NONLEGAL"):
            self.run_e4()
        self.assertEqual(self.fx._counts().get("knowledge",0),0)

    def test_03_opinion_rebranded_as_statute_cannot_borrow_legal_manifest(self):
        item=self.typed_inventories[self.segments[1]]["rows"][0]
        item["evidence_class"]="STATUTORY_FINANCIAL_RULE"
        item["authority_route"]="GOVERNMENT_LEGAL_PRIMARY"
        with self.assertRaisesRegex(InvalidInput,"SOURCE_TYPE_ATOMIC_KIND"):
            self.run_e4()
        self.assertEqual(self.fx._counts().get("knowledge",0),0)

    def test_04_typing_missing_in_second_child_holds_knowledge(self):
        self.typed_inventories.pop(self.segments[1])
        with self.assertRaises(InvalidInput):
            self.run_e4()
        self.assertEqual(self.fx._counts().get("knowledge",0),0)

    def test_05_source_only_unverified_numeric_claim_must_be_blocked(self):
        c=self.nonlegal_manifests[self.segments[1]]["rows"][0]
        c["verification_mode"]="PUBLISHER_ORIGINAL_ENGLISH_TITLE"
        with self.assertRaisesRegex(InvalidInput,"OPINION_OR_QUESTION_MUST_NOT_BORROW"):
            self.run_e4()
        self.assertEqual(self.fx._counts().get("knowledge",0),0)


if __name__=="__main__":
    unittest.main()
