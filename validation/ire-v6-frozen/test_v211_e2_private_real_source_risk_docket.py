"""V211 private-real-source custody and fail-closed tests (SYNTHETIC CI)."""
from __future__ import annotations

import copy
import hashlib
import json
import unittest

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import parse_srt
from test_v210_e2_private_original_source_inventory import RAW,synthetic
from v211_e2_private_real_source_risk_docket import (
    SCHEMA,audit_private_v211_source_risk_docket,
)


def fixture():
    previous=synthetic()
    raw_v210=json.dumps(previous,ensure_ascii=False,indent=2).encode("utf-8")
    cues=parse_srt(RAW)
    issues=[]
    for idx,code,priority in ((2,"QUESTION_EMBEDDED_FINANCE","HIGH"),
                              (3,"CONDITIONAL_FINANCIAL_SCOPE","MEDIUM")):
        text=cues[idx-1].text
        issues.append({
            "issue_id":f"V211-SOURCE-{len(issues)+1:03d}",
            "source_cue_index":idx,"source_quote":text,
            "source_text_sha256":sha256(text.encode()),
            "risk_code":code,"risk_priority":priority,
            "speaker_source_interpretation_unverified":
                "원본 발화는 아직 참인 금융 사실이라고 승인되지 않은 주장입니다.",
            "chat_reviewer_warning_not_original_speaker":
                "이것은 검토자의 의미 및 조건 해석이며 원본 발언자의 최종 금융 진실 승인과 구별해야 합니다.",
            "risk_reason":"FINANCIAL_SOURCE_PENDING",
            "connected_v210_draft_ids":["E2REAL-001" if idx==2 else "E2REAL-002"],
            "source_audio_or_visual_confirmed":False,
            "financial_truth_certified":False,
            "e2_cleared":False,
        })
    rows=[]
    for idx,cue in enumerate(cues,1):
        rows.append({
            "cue_index":idx,
            "source_text_sha256":sha256(cue.text.encode()),
            "provisional_v210_context_draft_ids":
                ["E2REAL-001"] if idx<=2 else
                ["E2REAL-002"] if idx==3 else [],
            "explicit_v211_risk_issue_ids":
                [x["issue_id"] for x in issues if x["source_cue_index"]==idx],
            "independent_atom_level_semantic_verification_passed":False,
            "v179_prior_exact_disposition_available":False,
        })
    docket={
        "schema":SCHEMA,
        "video_id":previous["video_id"],
        "source_sha256":sha256(RAW),
        "v210_private_inventory_sha256":hashlib.sha256(raw_v210).hexdigest(),
        "original_cues":4,
        "prior_v179_unresolved_total_reported":0,
        "prior_v179_suspicious_noatom_total_reported":0,
        "prior_v179_exact_open_cue_ids_unavailable":True,
        "prior_v179_exact_noatom_cue_ids_unavailable":True,
        "current_explicit_source_risk_cues":2,
        "current_explicit_high_priority":1,
        "current_explicit_medium_priority":1,
        "current_explicit_low_priority":0,
        "all_250_cues_source_hash_accounted":True,
        "issues":issues,
        "cue_census":rows,
        "direct_chat_review_not_independent_gold":True,
        "source_warning_does_not_equal_proven_factual_error":True,
        "v179_24_and_68_individually_resolved":False,
        "independent_gold_certified":False,
        "e2_pass":False,
        "e3_e4_e5_authorized":False,
        "finance_approved":False,
        "knowledge_published":False,
    }
    return raw_v210,docket


class TestV211PrivateDocket(unittest.TestCase):
    def setUp(self):
        self.v210,self.docket=fixture()

    def audit(self,docket=None,v210=None,original=RAW):
        return audit_private_v211_source_risk_docket(
            original,self.v210 if v210 is None else v210,
            self.docket if docket is None else docket,
            expected_source_sha256=sha256(RAW))

    def test_01_positive_private_cue_census_is_not_semantic_truth(self):
        receipt=self.audit()
        self.assertEqual(receipt["original_cues_sha_verified"],4)
        self.assertEqual(receipt["v210_provisional_claims_source_verified"],2)
        self.assertEqual(receipt["v211_explicit_high_source_review_cases"],1)
        self.assertEqual(receipt["v211_explicit_medium_source_review_cases"],1)
        self.assertEqual(receipt["v211_explicit_total_source_review_cases"],2)
        self.assertFalse(receipt["independent_semantic_gold_verified"])
        self.assertFalse(receipt["e2_final_pass"])
        self.assertFalse(receipt["actual_v176_owner_repair_committed"])
        self.assertFalse(receipt["e3_e4_e5_authorized"])
        self.assertNotIn("source_quote",str(receipt))
        self.assertNotIn("원본",str(receipt))

    def test_02_source_bytes_changed(self):
        with self.assertRaisesRegex(InvalidInput,"ORIGINAL_BYTES_CHANGED"):
            self.audit(original=RAW+b" ")

    def test_03_previous_private_review_bytes_changed(self):
        changed=self.v210+b" "
        with self.assertRaisesRegex(InvalidInput,
                                   "SOURCE_PRIOR_V210_OR_APPROVAL_GUARD"):
            self.audit(v210=changed)

    def test_04_cue_quote_cannot_be_rewritten(self):
        d=copy.deepcopy(self.docket)
        d["issues"][0]["source_quote"]="장기 투자면 모든 손실이 보장됩니다"
        with self.assertRaisesRegex(InvalidInput,
                                   "PRIVATE_RISK_SOURCE_QUOTE_OR_ROLE_DRIFT"):
            self.audit(d)

    def test_05_risk_index_cannot_be_reassigned_to_prior_cue(self):
        d=copy.deepcopy(self.docket)
        d["issues"][0]["source_cue_index"]=1
        with self.assertRaisesRegex(InvalidInput,
                                   "PRIVATE_RISK_SOURCE_QUOTE_OR_ROLE_DRIFT"):
            self.audit(d)

    def test_06_wrong_provisional_claim_mapping_fail_closed(self):
        d=copy.deepcopy(self.docket)
        d["cue_census"][1]["provisional_v210_context_draft_ids"]=[]
        with self.assertRaisesRegex(InvalidInput,
                                   "WHOLE_ORIGINAL_CUE_CENSUS_OR_RISK_DRIFT"):
            self.audit(d)

    def test_07_missing_source_cue_in_census_fails(self):
        d=copy.deepcopy(self.docket)
        d["cue_census"].pop()
        with self.assertRaisesRegex(InvalidInput,"ORIGINAL_CUE_OR_RISK_COUNT"):
            self.audit(d)

    def test_08_duplicate_risk_index_fails(self):
        d=copy.deepcopy(self.docket)
        d["issues"][1]["source_cue_index"]=2
        with self.assertRaisesRegex(InvalidInput,
                                   "PRIVATE_RISK_SOURCE_QUOTE_OR_ROLE_DRIFT"):
            self.audit(d)

    def test_09_gold_and_e3_cannot_be_forged(self):
        for field in ("independent_gold_certified","e2_pass",
                      "e3_e4_e5_authorized","finance_approved",
                      "knowledge_published","v179_24_and_68_individually_resolved"):
            d=copy.deepcopy(self.docket);d[field]=True
            with self.assertRaisesRegex(InvalidInput,
                                       "SOURCE_PRIOR_V210_OR_APPROVAL_GUARD"):
                self.audit(d)

    def test_10_reported_v179_noatom_count_is_not_current_issue_count(self):
        d=copy.deepcopy(self.docket)
        d["prior_v179_unresolved_total_reported"]=24
        d["prior_v179_suspicious_noatom_total_reported"]=68
        receipt=self.audit(d)
        self.assertEqual(receipt["v211_explicit_total_source_review_cases"],2)
        self.assertEqual(receipt["previous_v179_suspicious_noatom_reported"],68)
        self.assertFalse(receipt["prior_v179_individual_cue_id_mapping_available"])

    def test_11_private_reviewer_warning_cannot_be_erased(self):
        d=copy.deepcopy(self.docket)
        d["issues"][1]["chat_reviewer_warning_not_original_speaker"]=""
        with self.assertRaisesRegex(InvalidInput,
                                   "PRIVATE_RISK_SOURCE_QUOTE_OR_ROLE_DRIFT"):
            self.audit(d)

    def test_12_original_cue_sha_cannot_be_replaced(self):
        d=copy.deepcopy(self.docket)
        d["cue_census"][3]["source_text_sha256"]="0"*64
        with self.assertRaisesRegex(InvalidInput,
                                   "WHOLE_ORIGINAL_CUE_CENSUS_OR_RISK_DRIFT"):
            self.audit(d)


if __name__=="__main__":
    unittest.main()
