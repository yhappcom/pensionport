"""V214: native V6 actual code, synthetic fixture; no personal SRT in CI."""
from __future__ import annotations

import copy
import json
import unittest

from ire.v6.errors import InvalidInput
from ire.v6.codec import sha256
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from v176_chat_engine_loop import make_original_plan
from test_v210_e2_private_original_source_inventory import RAW,synthetic
from v214_e2_real_srt_provisional_native_v6 import (
    SCHEMA,PROVENANCE_SCHEMA,construct_provisional_native_v6,
    summarize_candidate_overlap,
)


class TestV214PrivateRealOriginalV6Staging(unittest.TestCase):
    def setUp(self):
        self.inventory=synthetic()

    def inventory_bytes(self,inventory=None):
        value=self.inventory if inventory is None else inventory
        return json.dumps(value,ensure_ascii=False,indent=2).encode("utf-8")

    def build(self,inventory=None,raw=RAW,window_size=2,
              qualifier_source_review=None,
              private_v210_source_bytes=None,
              expected_v210_source_sha256=None):
        v=self.inventory if inventory is None else inventory
        raw_v210=(self.inventory_bytes(v)
                  if private_v210_source_bytes is None else
                  private_v210_source_bytes)
        return construct_provisional_native_v6(
            raw,v,
            expected_source_sha256=sha256(RAW),
            private_v210_source_bytes=raw_v210,
            expected_v210_source_sha256=(
                sha256(raw_v210) if expected_v210_source_sha256 is None
                else expected_v210_source_sha256),
            window_size=window_size,
            qualifier_source_review=qualifier_source_review)

    def qualifier_review(self,origin="SOURCE_EXPLICIT"):
        from ire.v6.source import parse_srt
        cues=parse_srt(RAW)
        rows=[]
        for c in self.inventory["claims"]:
            for field in ("condition_anchor_cues","exception_anchor_cues"):
                for i in c[field]:
                    quote=cues[i-1].text if origin in {
                        "SOURCE_EXPLICIT","SOURCE_CONTEXT"} else None
                    rows.append({
                        "provisional_id":c["provisional_id"],
                        "qualifier_field":field,"cue_index":i,
                        "source_text_sha256":sha256(cues[i-1].text.encode("utf-8")),
                        "source_quote":quote,
                        "origin":origin,
                        "meaning_rationale":
                           "원문에 조건·예외가 존재하는지 별도 채팅 검토자로 확인하되 사실 승인하지 않습니다.",
                        "speaker_audio_verified":False,
                        "independent_gold_certified":False,
                        "financial_fact_approved":False,
                        "e2_final_pass":False,
                        "e3_e4_e5_authorized":False,
                    })
        return {
            "schema":PROVENANCE_SCHEMA,
            "source_sha256":self.inventory["source_sha256"],
            "v210_review_sha256":sha256(self.inventory_bytes()),
            "review_executor":"CHATGPT_IN_CHAT",
            "responses":rows,
            "independent_gold_certified":False,
            "financial_fact_approved":False,
            "e2_final_pass":False,
            "e3_e4_e5_authorized":False,
        }

    def test_01_actual_native_audit_all_source_cues_and_draft_atoms(self):
        exchange,receipt=self.build()
        src,_=make_original_plan(
            RAW,"Synth123456",expected_source_sha256=sha256(RAW),
            window_size=2)
        native=audit_host_atomic_exchange(src,exchange)
        self.assertEqual(native["proposed_atomic_claims"],2)
        self.assertEqual(receipt["schema"],SCHEMA)
        self.assertEqual(receipt["actual_original_cues_audited"],4)
        self.assertEqual(receipt["owner_windows"],2)
        self.assertEqual(receipt["native_v6_unapproved_proposals_staged"],2)
        self.assertEqual(receipt["cues_left_unresolved"],2)
        self.assertEqual(exchange["atoms"][1]["condition_cue_indices"],[])
        self.assertEqual(receipt["qualifier_source_role_reviews_required_but_missing"],1)
        self.assertEqual(exchange["atoms"][0]["speaker"],"UNKNOWN")
        self.assertEqual(exchange["atoms"][0]["stance"],"UNRESOLVED")
        self.assertFalse(receipt["e2_final_pass"])
        self.assertFalse(receipt["knowledge_written"])

    def test_02_proposition_99pct_never_in_original_blocks_native(self):
        d=copy.deepcopy(self.inventory)
        d["claims"][0]["proposition_unverified"]+=" 추가로 99%가 보장됩니다."
        native,receipt=self.build(d)
        self.assertEqual(receipt["native_v6_unapproved_proposals_staged"],1)
        self.assertEqual(receipt["blocked_proposal_ids"],["E2REAL-001"])
        self.assertEqual(receipt["cues_left_unresolved"],3)
        self.assertFalse(receipt["independent_gold_or_real_recall_verified"])
        self.assertEqual(native["atoms"][0]["claim_id"],"C00002")

    def test_03_unspoken_derived_math_is_not_speaker_fact(self):
        d=copy.deepcopy(self.inventory)
        d["claims"][1]["risks"]=["COMPUTED_NOT_SPOKEN"]
        exchange,receipt=self.build(d)
        self.assertEqual(receipt["blocked_unspoken_derived_proposals"],1)
        self.assertEqual(receipt["blocked_proposal_ids"],["E2REAL-002"])
        self.assertEqual(exchange["atoms"][0]["claim_id"],"C00001")

    def test_04_original_quote_or_cue_sha_forgery_blocked(self):
        d=copy.deepcopy(self.inventory)
        d["claims"][0]["anchors"][0]["quote"]="무조건 연 99% 보장"
        with self.assertRaisesRegex(InvalidInput,
                                    "SOURCE_ANCHOR_QUOTE_OR_SHA_CHANGED"):
            self.build(d)

    def test_05_missing_original_cue_census_does_not_pass(self):
        wrong=RAW+b"\n"
        with self.assertRaisesRegex(InvalidInput,"ORIGINAL_BYTES_CHANGED"):
            self.build(raw=wrong)

    def test_06_no_automatic_noatom_for_cues_outside_provisional_claims(self):
        exchange,receipt=self.build()
        self.assertEqual(
            [r["disposition"] for r in exchange["cue_dispositions"]],
            ["CANDIDATES","UNRESOLVED","CANDIDATES","UNRESOLVED"])
        self.assertTrue(receipt["unresolved_cues_cannot_be_assumed_noatom"])

    def test_07_no_auto_speaker_stance_or_e3_release_on_complete_draft(self):
        exchange,receipt=self.build()
        for x in exchange["atoms"]:
            self.assertEqual(x["speaker"],"UNKNOWN")
            self.assertEqual(x["stance"],"UNRESOLVED")
        self.assertFalse(receipt["speaker_and_stance_source_finalized"])
        self.assertFalse(receipt["old_v179_v181_v176_private_owner_recovered"])
        self.assertFalse(receipt["e3_e4_e5_authorized"])
        self.assertFalse(receipt["independent_gold_or_real_recall_verified"])

    def test_08_pairwise_overlap_never_equated_or_deduplicated(self):
        x=summarize_candidate_overlap(self.inventory)
        self.assertEqual(x["overlapping_cue_candidate_pairs"],0)
        d=copy.deepcopy(self.inventory)
        d["claims"][1]["start_cue"]=2
        x=summarize_candidate_overlap(d)
        self.assertEqual(x["overlapping_cue_candidate_pairs"],1)
        self.assertFalse(x["pairs"][0]["source_semantic_equivalence_verified"])
        self.assertTrue(x["no_atoms_merged_or_deleted"])

    def test_09_forged_gold_pass_cannot_enter_native_preflight(self):
        d=copy.deepcopy(self.inventory)
        d["e2_pass"]=True
        with self.assertRaisesRegex(InvalidInput,
                                    "FALSE_E2_OR_FINANCIAL_TRUTH_APPROVAL"):
            self.build(d)

    def test_10_native_deterministic_hash_and_no_owner_write(self):
        a,r=self.build()
        b,s=self.build()
        self.assertEqual(a,b)
        self.assertEqual(r,s)
        self.assertTrue(r["unresolved_cues_cannot_be_assumed_noatom"])
        self.assertFalse(r["original_v176_owner_journal_mutated"])

    def test_11_window_count_is_derived_only_from_source(self):
        _,receipt=self.build(window_size=1)
        self.assertEqual(receipt["owner_windows"],4)
        self.assertFalse(receipt["e2_final_pass"])

    def test_12_false_source_span_claim_count_fails_closed(self):
        d=copy.deepcopy(self.inventory)
        d["submitted_claims_provisional"]=100
        with self.assertRaisesRegex(InvalidInput,"CLAIM_RECORD_COUNT"):
            self.build(d)


    def test_13_explicit_original_source_qualifier_mapped_after_separate_chat_review(self):
        review=self.qualifier_review()
        exchange,receipt=self.build(qualifier_source_review=review)
        self.assertEqual(exchange["atoms"][1]["condition_cue_indices"],[3])
        self.assertEqual(receipt["source_explicit_provisional_condition_cue_links"],1)
        self.assertEqual(receipt["qualifier_source_role_reviews_required_but_missing"],0)
        self.assertFalse(receipt["speaker_and_stance_source_finalized"])
        self.assertFalse(receipt["e2_final_pass"])

    def test_14_reviewer_added_warning_never_as_native_v6_condition(self):
        exchange,receipt=self.build(
            qualifier_source_review=self.qualifier_review("REVIEWER_ADDED"))
        self.assertEqual(exchange["atoms"][1]["condition_cue_indices"],[])
        self.assertEqual(receipt["non_source_spoken_qualifier_reviews_retained_outside_v6"],1)

    def test_15_source_context_only_does_not_equal_source_spoken_condition(self):
        exchange,receipt=self.build(
            qualifier_source_review=self.qualifier_review("SOURCE_CONTEXT"))
        self.assertEqual(exchange["atoms"][1]["condition_cue_indices"],[])
        self.assertEqual(receipt["non_source_spoken_qualifier_reviews_retained_outside_v6"],1)

    def test_16_invented_source_quote_fails_closed(self):
        review=self.qualifier_review()
        review["responses"][0]["source_quote"]="99% 보장 가짜 수치"
        with self.assertRaisesRegex(InvalidInput,
                                    "QUALIFIER_QUOTE_NOT_IN_ORIGINAL"):
            self.build(qualifier_source_review=review)

    def test_17_missing_source_qualifier_review_row_cannot_silently_pass(self):
        review=self.qualifier_review()
        review["responses"]=[]
        with self.assertRaisesRegex(InvalidInput,
                                    "QUALIFIER_REVIEW_SOURCE_SCHEMA_OR_COUNT"):
            self.build(qualifier_source_review=review)

    def test_18_wrong_private_owner_source_sha_cannot_apply_chat_review(self):
        review=self.qualifier_review()
        review["v210_review_sha256"]="f"*64
        with self.assertRaisesRegex(InvalidInput,
                                    "QUALIFIER_REVIEW_SOURCE_SCHEMA_OR_COUNT"):
            self.build(qualifier_source_review=review)

    def test_19_false_financial_approval_in_qualifier_rejected(self):
        review=self.qualifier_review()
        review["responses"][0]["financial_fact_approved"]=True
        with self.assertRaisesRegex(InvalidInput,"QUALIFIER_REVIEW_ROW_DRIFT"):
            self.build(qualifier_source_review=review)

    def test_20_malformed_unhashable_qualifier_type_no_typeerror(self):
        review=self.qualifier_review()
        review["responses"][0]["origin"]=["SOURCE_EXPLICIT"]
        with self.assertRaisesRegex(InvalidInput,"QUALIFIER_REVIEW_ROW_DRIFT"):
            self.build(qualifier_source_review=review)


    def test_21_realistic_v210_decimal_illustration_with_original_bytes_no_runfail(self):
        d=copy.deepcopy(self.inventory)
        d["computed_illustration"]={"derived_percent":0.4682}
        exchange,receipt=self.build(d)
        self.assertEqual(receipt["native_v6_unapproved_proposals_staged"],2)
        self.assertEqual(receipt["v210_review_sha256"],
                         sha256(self.inventory_bytes(d)))
        self.assertFalse(receipt["e2_final_pass"])

    def test_22_replaced_private_file_bytes_rejected_before_audit(self):
        original_bytes=self.inventory_bytes()
        with self.assertRaisesRegex(InvalidInput,
                                    "V210_PRIVATE_BYTES_OR_EXTERNAL_SHA_CHANGED"):
            self.build(private_v210_source_bytes=original_bytes+b" ",
                       expected_v210_source_sha256=sha256(original_bytes))

    def test_23_no_v210_original_bytes_explicit_input_error_not_typeerror(self):
        with self.assertRaisesRegex(InvalidInput,
                                    "V210_ORIGINAL_BYTES_AND_EXTERNAL_HEAD_REQUIRED"):
            construct_provisional_native_v6(
                RAW,self.inventory,
                expected_source_sha256=sha256(RAW),
                private_v210_source_bytes=None,
                expected_v210_source_sha256="f"*64)

    def test_24_wrong_pin_blocks_even_when_parsed_json_matches(self):
        with self.assertRaisesRegex(InvalidInput,
                                    "V210_PRIVATE_BYTES_OR_EXTERNAL_SHA_CHANGED"):
            self.build(expected_v210_source_sha256="f"*64)


if __name__=="__main__":
    unittest.main()
