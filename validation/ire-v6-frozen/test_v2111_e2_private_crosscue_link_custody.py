"""V211.1 E2 guarded cross-cue source links; publicly synthetic only."""
from __future__ import annotations

import copy
from hashlib import sha256
import json
import unittest

from ire.v6.codec import sha256 as text_sha
from ire.v6.errors import InvalidInput
from ire.v6.source import parse_srt
from test_v210_e2_private_original_source_inventory import RAW
from test_v211_e2_private_real_source_risk_docket import fixture
from v2111_e2_private_crosscue_link_custody import (
    SCHEMA,audit_private_cross_cue_relations,
)


def synthetic_links():
    v210,docket=fixture()
    v211=json.dumps(docket,ensure_ascii=False,indent=2).encode("utf-8")
    cues=parse_srt(RAW)
    def edge(number,i,j,kind):
        explanation="자막 속 질문·단서·조건의 관계는 검토자 해석이며 금융 사실로 승인되지 않습니다."
        return {
            "relation_id":f"V211R-{number:03d}",
            "from_cue":i,"to_cue":j,
            "from_quote":cues[i-1].text,
            "to_quote":cues[j-1].text,
            "from_source_text_sha256":text_sha(cues[i-1].text.encode("utf-8")),
            "to_source_text_sha256":text_sha(cues[j-1].text.encode("utf-8")),
            "relation_type":kind,
            "chat_reviewer_interpretation_not_source_speaker":explanation,
            "semantic_relation_independently_confirmed":False,
            "financial_fact_approved":False,
        }
    return v210,v211,{
        "schema":SCHEMA,
        "video_id":docket["video_id"],
        "original_source_sha256":text_sha(RAW),
        "v210_inventory_sha256":sha256(v210).hexdigest(),
        "v211_docket_sha256":sha256(v211).hexdigest(),
        "total_cues":4,
        "relation_count":2,
        "relations":[edge(1,2,3,"EXCEPTION"),edge(2,1,2,"HYPOTHETICAL_EXAMPLE")],
        "each_relation_has_both_original_quotes":True,
        "chat_review_of_relation_not_external_gold":True,
        "e2_final_pass":False,
        "e3_e4_e5_authorized":False,
        "financial_truth_certified":False,
        "native_v6_claims_issued":False,
    }


class TestV2111CrossCueSourceCustody(unittest.TestCase):
    def setUp(self):
        self.v210,self.v211,self.data=synthetic_links()

    def audit(self,data=None,v211=None,v210=None,source=RAW):
        return audit_private_cross_cue_relations(
            source,self.v210 if v210 is None else v210,
            self.v211 if v211 is None else v211,
            self.data if data is None else data,
            expected_source_sha256=text_sha(RAW))

    def test_01_correct_source_quoted_caveat_not_semantic_gold(self):
        result=self.audit()
        self.assertEqual(result["original_cues_source_verified"],4)
        self.assertEqual(result["source_quoted_cross_cue_relations"],2)
        self.assertEqual(result["relation_type_counts"]["EXCEPTION"],1)
        self.assertEqual(result["relation_type_counts"]["HYPOTHETICAL_EXAMPLE"],1)
        self.assertFalse(result["independent_semantic_gold_verified"])
        self.assertFalse(result["e2_final_pass"])
        self.assertFalse(result["cross_cue_meanings_finally_approved"])
        self.assertFalse(result["knowledge_published"])
        self.assertNotIn("from_quote",str(result))

    def test_02_source_bytes_changed(self):
        with self.assertRaisesRegex(InvalidInput,"ORIGINAL_BYTES_CHANGED"):
            self.audit(source=RAW+b" ")

    def test_03_v211_private_docket_changed(self):
        with self.assertRaisesRegex(InvalidInput,
                                    "SOURCE_RISK_HEAD_OR_FALSE_APPROVAL"):
            self.audit(v211=self.v211+b" ")

    def test_04_condition_cue_quote_forgery_rejected(self):
        bad=copy.deepcopy(self.data)
        bad["relations"][0]["to_quote"]="손실 위험 없음"
        with self.assertRaisesRegex(InvalidInput,
                                    "RELATION_NOT_ORIGINAL_OR_FINANCIALLY_PREAPPROVED"):
            self.audit(bad)

    def test_05_hash_cannot_swap_among_source_cues(self):
        bad=copy.deepcopy(self.data)
        bad["relations"][0]["to_source_text_sha256"]=(
            self.data["relations"][0]["from_source_text_sha256"])
        with self.assertRaisesRegex(InvalidInput,
                                    "RELATION_NOT_ORIGINAL_OR_FINANCIALLY_PREAPPROVED"):
            self.audit(bad)

    def test_06_duplicate_edges_rejected(self):
        bad=copy.deepcopy(self.data)
        bad["relations"][1]=copy.deepcopy(bad["relations"][0])
        bad["relations"][1]["relation_id"]="V211R-002"
        with self.assertRaisesRegex(InvalidInput,
                                    "RELATION_NOT_ORIGINAL_OR_FINANCIALLY_PREAPPROVED"):
            self.audit(bad)

    def test_07_drop_original_rebuttal_source_rejected(self):
        bad=copy.deepcopy(self.data)
        bad["relations"].pop()
        with self.assertRaisesRegex(InvalidInput,"RELATION_COUNT_OR_FORMAT"):
            self.audit(bad)

    def test_08_forge_financial_fact_or_step_advancement_rejected(self):
        for key in ("e2_final_pass","e3_e4_e5_authorized",
                    "financial_truth_certified","native_v6_claims_issued"):
            bad=copy.deepcopy(self.data);bad[key]=True
            with self.assertRaisesRegex(InvalidInput,
                                        "SOURCE_RISK_HEAD_OR_FALSE_APPROVAL"):
                self.audit(bad)

    def test_09_directly_forge_source_truth_in_relation_rejected(self):
        bad=copy.deepcopy(self.data)
        bad["relations"][0]["financial_fact_approved"]=True
        with self.assertRaisesRegex(InvalidInput,
                                    "RELATION_NOT_ORIGINAL_OR_FINANCIALLY_PREAPPROVED"):
            self.audit(bad)

    def test_10_missing_link_field_fails_closed_without_keyerror(self):
        bad=copy.deepcopy(self.data)
        bad["relations"][0].pop("to_source_text_sha256")
        with self.assertRaisesRegex(InvalidInput,"RELATION_FIELDS_DRIFT"):
            self.audit(bad)

    def test_11_bad_link_index_type_fails_closed_without_typeerror(self):
        bad=copy.deepcopy(self.data)
        bad["relations"][0]["to_cue"]=[]
        with self.assertRaisesRegex(InvalidInput,
                                    "RELATION_NOT_ORIGINAL_OR_FINANCIALLY_PREAPPROVED"):
            self.audit(bad)

    def test_12_reported_prior_v179_is_not_pretended_reconciled(self):
        result=self.audit()
        self.assertTrue(result["missing_v179_individual_owner_cases"])
        self.assertFalse(result["cross_cue_meanings_finally_approved"])


if __name__=="__main__":
    unittest.main()
