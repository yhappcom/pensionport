"""Synthetic mutation tests for public 11-pair SHA-only HOLD gate."""
from __future__ import annotations
import copy
import unittest
from scripts.ire_p0_2_05_kind_triage_gate import ROOT,RECEIPT,STATE,LEDGER,load,verify


class P205KindTriagePublicGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=(load(ROOT,RECEIPT),load(ROOT,STATE),load(ROOT,LEDGER))
    def setUp(self):
        self.r,self.s,self.l=copy.deepcopy(self.base)
    def err(self):return verify(ROOT,receipt=self.r,state=self.s,ledger=self.l)
    def bad(self,expected):
        failures=self.err()
        self.assertTrue(any(expected in x for x in failures),failures)
    def test_01_healthy_sha_and_explicit_gold_hold(self):self.assertEqual([],verify(ROOT,receipt=self.r,state=self.s,ledger=self.l,historical_only=True))
    def test_02_wrong_original_source_hash(self):
        self.r['source_sha256']='0'*64;self.bad('FROZEN_HASH')
    def test_03_wrong_original_native_hash(self):
        self.r['frozen_native_sha256']='0'*64;self.bad('FROZEN_HASH')
    def test_04_wrong_frozen_first_pass_hash(self):
        self.r['source_first_71_sha256']='0'*64;self.bad('FROZEN_HASH')
    def test_05_wrong_frozen_topic_crosswalk_hash(self):
        self.r['crosswalk_71_68_sha256']='0'*64;self.bad('FROZEN_HASH')
    def test_06_wrong_private_11_pair_json_hash(self):
        self.r['kind_triage_private_json_sha256']='0'*64;self.bad('FROZEN_HASH')
    def test_07_wrong_private_zip_hash(self):
        self.r['kind_triage_private_zip_sha256']='0'*64;self.bad('FROZEN_HASH')
    def test_08_fake_library_file(self):
        self.r['kind_triage_private_library_file_id']='libfile_fake';self.bad('PRIVATE_ORIGINAL_CUSTODY')
    def test_09_missing_one_group(self):
        self.r['triaged_groups']['DISTINCT_PROPOSITION_TOPIC_ONLY']=3;self.bad('FOUR_CATEGORY_COUNT')
    def test_10_fake_11_misclassifications_already_proven(self):
        self.r['confirmed_engine_misclassification_count']=11;self.bad('CANNOT_CLAIM')
    def test_11_independent_categories_falsely_approved(self):
        self.r['triaged_groups_are_independently_approved']=True;self.bad('CANNOT_CLAIM')
    def test_12_forge_semantic_truth(self):
        self.r['semantic_truth_of_group_resolution_proven']=True;self.bad('CANNOT_CLAIM')
    def test_13_highrisk_10_closed(self):
        self.r['all_10_high_risk_review_queues_open']=False;self.bad('CANNOT_CLAIM')
    def test_14_highrisk_queue_count_forged(self):
        self.r['high_risk_review_queue_count']=0;self.bad('CANNOT_CLAIM')
    def test_15_cue_census_falsified(self):
        self.r['source_original_cues_checked']=249;self.bad('FOUR_CATEGORY_COUNT')
    def test_16_provisional_count_falsified(self):
        self.r['source_provisional_claims']=68;self.bad('FOUR_CATEGORY_COUNT')
    def test_17_frozen_native_count_falsified(self):
        self.r['frozen_native_unapproved_claims']=70;self.bad('FOUR_CATEGORY_COUNT')
    def test_18_claims_no_omitted_atoms(self):
        self.r['source_cues_outside_claim_context_confirmed_absent']=True;self.bad('NO_FALSE_ATOMIC')
    def test_19_forge_precise_gold_one_to_one_alignment(self):
        self.r['strict_one_to_one_atomic_gold_proven']=True;self.bad('NO_FALSE_ATOMIC')
    def test_20_forge_independent_reviewer_identity(self):
        self.r['independent_reviewer_sessions']=2;self.bad('NO_FORGED')
    def test_21_forge_gold_atoms(self):
        self.r['independent_gold_atoms']=71;self.bad('NO_FORGED')
    def test_22_forge_precision_success(self):
        self.r['independent_precision']=1;self.bad('NO_FORGED')
    def test_23_forge_recall_success(self):
        self.r['independent_recall']=1;self.bad('NO_FORGED')
    def test_24_forge_highrisk_FN_zero(self):
        self.r['independent_high_risk_false_negative_count']=0;self.bad('NO_FORGED')
    def test_25_lower_precision_target_afterseeing_predictions(self):
        self.r['minimum_precision_basis_points']=9000;self.bad('ASSESSMENT_TARGETS')
    def test_26_lower_recall_target(self):
        self.r['minimum_recall_basis_points']=9300;self.bad('ASSESSMENT_TARGETS')
    def test_27_claim_topic_link_true_positive(self):
        self.r['topic_only_relation_cannot_become_gold_match']=False;self.bad('FALSE_SOURCE')
    def test_28_claim_gold_from_prior_same_chat(self):
        self.r['source_first_diagnostic_remains_same_chat_nonindependent']=False;self.bad('FALSE_SOURCE')
    def test_29_forge_crosswalk_as_truth(self):
        self.r['source_quote_cryptographic_check_not_semantic_entailment']=False;self.bad('FALSE_SOURCE')
    def test_30_claim_E2_E3_E4_E5_APPROVED(self):
        self.r['no_new_e2_e3_e4_e5_approvals']=False;self.bad('FALSE_SOURCE')
    def test_31_claim_P205_PASS_without_independent_gold(self):
        self.s['items'][16]['status']='PASS';self.bad('PREVIOUS_16_PASS')
    def test_32_unlock_P206(self):
        self.s['items'][17]['status']='READY';self.bad('PREVIOUS_16_PASS')
    def test_33_advance_canonical_cursor(self):
        self.l['development_gate']['pending_next_item']='P0-2-06';self.bad('CURRENT_CURSOR')
    def test_34_hide_prior_16_pass(self):
        self.s['items'][15]['status']='HOLD';self.bad('PREVIOUS_16_PASS')
    def test_35_fake_actual_accuracy_stage(self):
        self.r['financial_research_stage']='PASS_GOLD';self.bad('SEQUENTIAL_GATE')
    def test_36_wrong_SRT_video_id(self):
        self.r['video_id']='fictitious';self.bad('FOUR_CATEGORY_COUNT')
    def test_37_drop_label_pairs(self):
        self.r['topic_related_crosswalk_label_discrepancy_pairs']=10;self.bad('FOUR_CATEGORY_COUNT')
    def test_38_wrong_release_flag(self):
        self.r['item_state']='PASS';self.bad('SEQUENTIAL_GATE')
    def test_39_incorrect_schema(self):
        self.r['schema']='IRE_P205_SUCCESS';self.bad('SCHEMA_ID_DATE')
    def test_40_wrong_source_only_module(self):
        self.r['technical_module']='ire/v6/missing.py';self.bad('CODE_AND_TEST_PATHS')

if __name__=='__main__':unittest.main()
