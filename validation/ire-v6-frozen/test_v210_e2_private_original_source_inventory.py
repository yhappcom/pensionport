"""V210 source-only provenance: synthetic SRT, real 250-cue original is private."""
from __future__ import annotations

import copy
import unittest

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import parse_srt
from v210_e2_private_original_source_inventory import (
    SCHEMA,audit_private_e2_source_first_inventory,
)

RAW=(
    "1\n00:00:01,000 --> 00:00:01,500\nETF는 펀드의 일종입니다.\n\n"
    "2\n00:00:02,000 --> 00:00:02,500\nISA에 연 8% 수익을 보장한다는 질문인가요?\n\n"
    "3\n00:00:03,000 --> 00:00:03,500\n다만 한도를 초과하면 달라질 수 있습니다.\n\n"
    "4\n00:00:04,000 --> 00:00:04,500\n감사합니다.\n"
).encode("utf-8")


def synthetic():
    cues=parse_srt(RAW)
    def link(i):
        txt=cues[i-1].text
        return {"cue_index":i,"quote":txt,
                "source_text_sha256":sha256(txt.encode("utf-8"))}
    claims=[
        {
            "provisional_id":"E2REAL-001",
            "start_cue":1,"end_cue":2,
            "kind":"FACT",
            "proposition_unverified":"ETF가 펀드의 일종이라는 설명을 한 원문 주장입니다.",
            "anchors":[link(1),link(2)],
            "condition_anchor_cues":[],"exception_anchor_cues":[],
            "risks":["EMBEDDED_UNVERIFIED_QUESTION"],
            "financial_fact_approved":False,
            "speaker_verified":False,"native_v6_claim_id":None,
            "e2_pass":False,"e3_e4_e5_authorized":False,
        },
        {
            "provisional_id":"E2REAL-002",
            "start_cue":3,"end_cue":3,
            "kind":"HYPOTHETICAL",
            "proposition_unverified":"소득 한도 초과라는 조건을 붙인 원문 설명입니다.",
            "anchors":[link(3)],
            "condition_anchor_cues":[3],"exception_anchor_cues":[],
            "risks":[],
            "financial_fact_approved":False,
            "speaker_verified":False,"native_v6_claim_id":None,
            "e2_pass":False,"e3_e4_e5_authorized":False,
        },
    ]
    return {
        "schema":SCHEMA,"video_id":"Synth123456",
        "zip_file":"not_original_synthetic_source.zip",
        "source_sha256":sha256(RAW),"cue_count":4,
        "current_turn_source_directly_read":True,
        "original_v179_prior_claims_used_as_source_of_labels":False,
        "review_method":"CHATGPT_DIRECT_ORIGINAL_SRT_FIRST_PASS_NEW_HYPOTHESES_NOT_INDEPENDENT_GOLD",
        "submitted_claims_provisional":2,
        "types":{"FACT":1,"HYPOTHETICAL":1},
        "cues_in_any_hypothesis_span":3,
        "uncovered_original_cues":[4],
        "financial_fact_approved":False,
        "gold_quality_certified":False,
        "e2_pass":False,"e3_e4_e5_authorized":False,
        "knowledge_written":False,
        "claims":claims,
    }


class TestV210ExactPrivateOriginalEvidence(unittest.TestCase):
    def setUp(self):
        self.source=synthetic()

    def audit(self,data=None,raw=RAW):
        return audit_private_e2_source_first_inventory(
            raw,data if data is not None else self.source,
            expected_source_sha256=sha256(RAW))

    def test_01_original_cues_and_provisional_facts_not_approved(self):
        receipt=self.audit()
        self.assertEqual(receipt["original_cues_checked"],4)
        self.assertEqual(receipt["source_anchored_provisional_claims"],2)
        self.assertEqual(receipt["nonclaim_or_connective_cues"],1)
        self.assertEqual(receipt["candidates_with_explicit_caution_flags"],1)
        self.assertFalse(receipt["e2_final_pass"])
        self.assertFalse(receipt["financial_fact_truth_certified"])
        self.assertFalse(receipt["native_v6_claims_created"])
        self.assertFalse(receipt["research_knowledge_published"])
        self.assertNotIn("proposition",str(receipt))
        self.assertNotIn("원문",str(receipt))

    def test_02_replaced_srt_original_bytes_fail(self):
        with self.assertRaisesRegex(InvalidInput,"ORIGINAL_BYTES_CHANGED"):
            self.audit(raw=RAW+b" ")

    def test_03_changed_original_quote_fails(self):
        data=copy.deepcopy(self.source)
        data["claims"][0]["anchors"][0]["quote"]="ETF는 원금이 보장됩니다"
        with self.assertRaisesRegex(InvalidInput,
                                    "SOURCE_ANCHOR_QUOTE_OR_SHA_CHANGED"):
            self.audit(data)

    def test_04_changed_original_cue_sha_fails(self):
        data=copy.deepcopy(self.source)
        data["claims"][1]["anchors"][0]["source_text_sha256"]="f"*64
        with self.assertRaisesRegex(InvalidInput,
                                    "SOURCE_ANCHOR_QUOTE_OR_SHA_CHANGED"):
            self.audit(data)

    def test_05_missing_original_cue_coverage_fails(self):
        data=copy.deepcopy(self.source)
        data["uncovered_original_cues"]=[]
        with self.assertRaisesRegex(InvalidInput,
                                    "ORIGINAL_250_CUE_COVERAGE_OR_CLAIM_TYPES_DRIFT"):
            self.audit(data)

    def test_06_false_financial_approval_never_passes(self):
        for key in ("financial_fact_approved","gold_quality_certified",
                    "e2_pass","e3_e4_e5_authorized","knowledge_written"):
            data=copy.deepcopy(self.source);data[key]=True
            with self.assertRaisesRegex(InvalidInput,
                                        "FALSE_E2_OR_FINANCIAL_TRUTH_APPROVAL"):
                self.audit(data)

    def test_07_unanchored_condition_cue_not_permitted(self):
        data=copy.deepcopy(self.source)
        data["claims"][1]["condition_anchor_cues"]=[2]
        with self.assertRaisesRegex(InvalidInput,
                                    "QUALIFIER_OR_EXCEPTION_SOURCE_ANCHOR_MISSING"):
            self.audit(data)

    def test_08_auto_promote_native_claim_id_blocked(self):
        data=copy.deepcopy(self.source)
        data["claims"][0]["native_v6_claim_id"]="C00001"
        with self.assertRaisesRegex(InvalidInput,
                                    "PROVISIONAL_CLAIM_NOT_SOURCE_ONLY"):
            self.audit(data)

    def test_09_speaker_verified_claim_blocked(self):
        data=copy.deepcopy(self.source)
        data["claims"][0]["speaker_verified"]=True
        with self.assertRaisesRegex(InvalidInput,
                                    "PROVISIONAL_CLAIM_NOT_SOURCE_ONLY"):
            self.audit(data)

    def test_10_fake_type_count_blocked(self):
        data=copy.deepcopy(self.source)
        data["types"]["FACT"]=2
        with self.assertRaisesRegex(InvalidInput,
                                    "ORIGINAL_250_CUE_COVERAGE_OR_CLAIM_TYPES_DRIFT"):
            self.audit(data)

    def test_11_duplicated_source_anchor_rejected(self):
        data=copy.deepcopy(self.source)
        data["claims"][0]["anchors"].append(copy.deepcopy(
            data["claims"][0]["anchors"][-1]))
        with self.assertRaisesRegex(InvalidInput,
                                    "DUPLICATE_OR_UNORDERED_ANCHOR_CUES"):
            self.audit(data)

    def test_12_source_provenance_but_no_actual_independent_human_gold(self):
        receipt=self.audit()
        self.assertNotIn("independent_gold_certified",receipt)
        self.assertFalse(receipt["e2_semantic_gold_verified"])


if __name__=="__main__":
    unittest.main()
