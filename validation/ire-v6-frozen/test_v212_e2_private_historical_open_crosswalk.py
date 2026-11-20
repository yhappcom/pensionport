"""V212 source-bound V182 OPEN audit: synthetic public fixture only.

The real private 250-cue / 17-case packet is NEVER sent to Github CI.
"""
from __future__ import annotations

from collections import Counter
import copy
from hashlib import sha256 as sha
import json
import unittest

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import parse_srt
from test_v210_e2_private_original_source_inventory import RAW
from test_v2111_e2_private_crosscue_link_custody import synthetic_links
from v212_e2_private_historical_open_crosswalk import (
    SCHEMA, HISTORICAL_REFERENCE, PRIVATE_BASENAMES,
    EVIDENCE_REQUIRED, audit_private_open_crosswalk,
    audit_real_v182_etf_source_open,
)

GOLD_SIMULATED_OPEN_MAP={
    1:"FACT_SCOPE_OVERGENERALIZATION",
    2:"ASR_AUDIO",
    3:"VIDEO_SCREEN",
}
REVIEWER="원음과 직접 원본 화면을 확인하기 전에 문맥상의 주장을 검토자 추론으로 다루고 정식 금융 사실로 승인해서는 안 됩니다."


def make_fixture():
    v210,v211,rel=synthetic_links()
    v2111=json.dumps(rel,ensure_ascii=False,indent=2).encode("utf-8")
    original=parse_srt(RAW)
    inv=json.loads(v210)
    risk=json.loads(v211)
    issues={r["source_cue_index"]:r for r in risk["issues"]}
    rows=[]
    for i,kind in GOLD_SIMULATED_OPEN_MAP.items():
        context=[{
            "cue_index":n,
            "source_quote":original[n-1].text,
            "source_text_sha256":sha256(original[n-1].text.encode("utf-8")),
        } for n in range(max(1,i-2),min(len(original),i+2)+1)]
        issue=issues.get(i)
        rows.append({
            "cue_index":i,
            "historical_v182_open_type":kind,
            "historical_v182_effective_open":True,
            "source_quote":original[i-1].text,
            "source_text_sha256":sha256(original[i-1].text.encode("utf-8")),
            "original_neighborhood":context,
            "linked_v210_unapproved_candidate_ids":[
                c["provisional_id"] for c in inv["claims"]
                if c["start_cue"]<=i<=c["end_cue"]],
            "v211_prior_risk_issue_id":(
                issue["issue_id"] if issue else None),
            "v211_newly_identified_gap":issue is None,
            "v2111_related_original_source_edge_ids":[
                edge["relation_id"] for edge in rel["relations"]
                if i in (edge["from_cue"],edge["to_cue"])],
            "chat_source_interpretation_not_speaker":REVIEWER,
            "must_resolve_via":EVIDENCE_REQUIRED[kind],
            "can_be_marked_resolved_from_current_srt_only":False,
            "external_gold_certified":False,
            "financial_fact_approved":False,
            "original_owner_v176_event_changed":False,
        })
    packet={
        "schema":SCHEMA,"video_id":inv["video_id"],
        "original_source_sha256":sha256(RAW),
        "total_original_cues":len(original),
        "historical_reference":HISTORICAL_REFERENCE,
        "historical_v182_owner_sqlite_recovered":False,
        "v179_24_open_individual_cases_available":False,
        "v179_68_noatom_individual_cases_available":False,
        "historical_v182_open_count":len(rows),
        "v211_existing_risk_covered_count":2,
        "v211_missing_cue_risk_count":1,
        "v211_missing_original_cue_ids":[1],
        "historical_open_types":dict(Counter(GOLD_SIMULATED_OPEN_MAP.values())),
        "private_input_hashes":dict(zip(PRIVATE_BASENAMES,(
            sha(v210).hexdigest(),sha(v211).hexdigest(),sha(v2111).hexdigest()
        ))),
        "rows":rows,
        "chat_review_is_not_external_gold":True,
        "all_historical_v182_open_still_needs_resolution":True,
        "independent_gold_certified":False,
        "e2_pass":False,"e3_e4_e5_authorized":False,
        "financial_facts_approved":False,"knowledge_published":False,
    }
    return v210,v211,v2111,packet


class TestV212PriorOpenCrosswalk(unittest.TestCase):
    def setUp(self):
        self.v210,self.v211,self.v2111,self.packet=make_fixture()

    def audit(self,packet=None,raw=RAW, v210=None, v211=None, v2111=None):
        return audit_private_open_crosswalk(
            raw,
            self.v210 if v210 is None else v210,
            self.v211 if v211 is None else v211,
            self.v2111 if v2111 is None else v2111,
            self.packet if packet is None else packet,
            expected_source_sha256=sha256(RAW),
            expected_open_map=GOLD_SIMULATED_OPEN_MAP,
            expected_video_id="Synth123456",
        )

    def test_01_prior_case_census_catches_current_uncovered_open(self):
        r=self.audit()
        self.assertEqual(r["original_source_cues_verified"],4)
        self.assertEqual(r["historical_v182_explicit_open_cases_source_checked"],3)
        self.assertEqual(r["v211_previous_risk_items_covering_open"],2)
        self.assertEqual(r["new_e2_gap_cue_indices"],[1])
        self.assertEqual(r["new_e2_gap_count"],1)
        self.assertFalse(r["previous_v179_open_24_resolved"])
        self.assertFalse(r["e2_final_pass"])
        self.assertFalse(r["e3_e4_e5_authorized"])
        self.assertNotIn("source_quote",str(r))

    def test_02_source_bytes_changed_fails(self):
        with self.assertRaisesRegex(InvalidInput,"SOURCE_OR_HISTORICAL_MAP_INVALID"):
            self.audit(raw=RAW+b" ")

    def test_03_previous_private_docket_bytes_changed_fails(self):
        with self.assertRaisesRegex(InvalidInput,"SOURCE_RISK_HEAD_OR_FALSE_APPROVAL"):
            self.audit(v2111=self.v2111+b" ")

    def test_04_forged_historical_cue_index_fails(self):
        p=copy.deepcopy(self.packet)
        p["rows"][0]["cue_index"]=4
        with self.assertRaisesRegex(InvalidInput,
                                    "SOURCE_OPEN_REVIEW_OR_REFERENCED_EVIDENCE_DRIFT"):
            self.audit(p)

    def test_05_wrong_historical_evidence_type_fails(self):
        p=copy.deepcopy(self.packet)
        p["rows"][1]["historical_v182_open_type"]="VIDEO_SCREEN"
        with self.assertRaisesRegex(InvalidInput,
                                    "SOURCE_OPEN_REVIEW_OR_REFERENCED_EVIDENCE_DRIFT"):
            self.audit(p)

    def test_06_original_quote_and_hash_cannot_be_rewritten(self):
        for field,value in (
            ("source_quote","ETF는 원금을 무조건 보장합니다"),
            ("source_text_sha256","f"*64)):
            p=copy.deepcopy(self.packet)
            p["rows"][0][field]=value
            with self.assertRaisesRegex(InvalidInput,
                                        "SOURCE_OPEN_REVIEW_OR_REFERENCED_EVIDENCE_DRIFT"):
                self.audit(p)

    def test_07_parent_context_cue_sha_cannot_be_lost(self):
        p=copy.deepcopy(self.packet)
        p["rows"][0]["original_neighborhood"][0]["source_text_sha256"]="f"*64
        with self.assertRaisesRegex(InvalidInput,
                                    "SOURCE_OPEN_REVIEW_OR_REFERENCED_EVIDENCE_DRIFT"):
            self.audit(p)

    def test_08_open_case_not_in_prior_risk_cannot_be_called_covered(self):
        p=copy.deepcopy(self.packet)
        p["rows"][0]["v211_newly_identified_gap"]=False
        p["rows"][0]["v211_prior_risk_issue_id"]="V211-SOURCE-999"
        with self.assertRaisesRegex(InvalidInput,
                                    "SOURCE_OPEN_REVIEW_OR_REFERENCED_EVIDENCE_DRIFT"):
            self.audit(p)

    def test_09_new_gap_count_cannot_be_silently_lowered(self):
        p=copy.deepcopy(self.packet)
        p["v211_missing_cue_risk_count"]=0
        with self.assertRaisesRegex(InvalidInput,
                                    "HISTORICAL_OPEN_CASES_OR_RISK_GAP_COUNTS_WRONG"):
            self.audit(p)

    def test_10_no_audio_video_missing_can_be_marked_resolved(self):
        p=copy.deepcopy(self.packet)
        p["rows"][1]["can_be_marked_resolved_from_current_srt_only"]=True
        with self.assertRaisesRegex(InvalidInput,
                                    "SOURCE_OPEN_REVIEW_OR_REFERENCED_EVIDENCE_DRIFT"):
            self.audit(p)

    def test_11_false_approval_or_gold_never_passes(self):
        for k in ("independent_gold_certified","e2_pass",
                  "e3_e4_e5_authorized","financial_facts_approved",
                  "knowledge_published","all_historical_v182_open_still_needs_resolution"):
            p=copy.deepcopy(self.packet)
            p[k]=not p[k]
            with self.assertRaisesRegex(InvalidInput,
                                        "PRIVATE_INPUT_SHA_OR_HISTORICAL_CUSTODY_MISMATCH"):
                self.audit(p)

    def test_12_cannot_invent_v2111_link_to_failed_screen(self):
        p=copy.deepcopy(self.packet)
        p["rows"][0]["v2111_related_original_source_edge_ids"].append("FAKE")
        with self.assertRaisesRegex(InvalidInput,
                                    "SOURCE_OPEN_REVIEW_OR_REFERENCED_EVIDENCE_DRIFT"):
            self.audit(p)

    def test_13_missing_one_previous_open_never_looks_complete(self):
        p=copy.deepcopy(self.packet)
        p["rows"].pop()
        with self.assertRaisesRegex(InvalidInput,"OPEN_CUE_17_CENSUS_MISMATCH"):
            self.audit(p)

    def test_14_wrong_video_or_source_rejected_by_production_entrypoint(self):
        with self.assertRaisesRegex(InvalidInput,
                                    "SOURCE_OR_HISTORICAL_MAP_INVALID"):
            audit_real_v182_etf_source_open(
                RAW,self.v210,self.v211,self.v2111,self.packet)

    def test_15_original_125_v176_owner_not_claimed_restored(self):
        p=copy.deepcopy(self.packet)
        p["historical_v182_owner_sqlite_recovered"]=True
        with self.assertRaisesRegex(InvalidInput,
                                    "PRIVATE_INPUT_SHA_OR_HISTORICAL_CUSTODY_MISMATCH"):
            self.audit(p)


if __name__=="__main__":
    unittest.main()
