"""V214: native V6 actual code, synthetic fixture; no personal SRT in CI."""
from __future__ import annotations

import copy
import unittest

from ire.v6.errors import InvalidInput
from ire.v6.codec import sha256
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from v176_chat_engine_loop import make_original_plan
from test_v210_e2_private_original_source_inventory import RAW,synthetic
from v214_e2_real_srt_provisional_native_v6 import (
    SCHEMA,construct_provisional_native_v6,summarize_candidate_overlap,
)


class TestV214PrivateRealOriginalV6Staging(unittest.TestCase):
    def setUp(self):
        self.inventory=synthetic()

    def build(self,inventory=None,raw=RAW,window_size=2):
        return construct_provisional_native_v6(
            raw,self.inventory if inventory is None else inventory,
            expected_source_sha256=sha256(RAW),
            window_size=window_size)

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
        self.assertEqual(exchange["atoms"][1]["condition_cue_indices"],[3])
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


if __name__=="__main__":
    unittest.main()
