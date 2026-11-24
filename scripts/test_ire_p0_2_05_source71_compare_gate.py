"""Public regression attacks on P205 SHA-only non-independent source-first review."""
from __future__ import annotations
import copy
import unittest
from scripts.ire_p0_2_05_source71_compare_gate import (
    ROOT,FIRST,COMPARE,GOLD,STATE,LEDGER,load,verify,
)


class P205Source71Native68PublicGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline=tuple(load(ROOT,p) for p in (FIRST,COMPARE,GOLD,STATE,LEDGER))
    def setUp(self):
        self.f,self.c,self.g,self.s,self.l=copy.deepcopy(self.baseline)
    def errs(self):
        return verify(ROOT,first=self.f,compare=self.c,gold=self.g,state=self.s,ledger=self.l)
    def bad(self,word):
        issues=self.errs()
        self.assertTrue(any(word in q for q in issues),issues)
    def test_01_real_sha_only_positive_hold(self):self.assertEqual([],verify(ROOT,first=self.f,compare=self.c,gold=self.g,state=self.s,ledger=self.l,historical_only=True))
    def test_02_forged_private_first_pass_sha(self):
        self.f['frozen_provisional_json_sha256']='0'*64;self.bad('FIRST_SOURCE_PACKAGE')
    def test_03_forged_private_first_zip(self):
        self.f['frozen_provisional_zip_sha256']='0'*64;self.bad('FIRST_SOURCE_PACKAGE')
    def test_04_fake_prior_prediction_read_is_false(self):
        self.f['used_original_v228_prediction_content_to_draft_this_round']=True;self.bad('SOURCE_ONLY_CANNOT')
    def test_05_fake_independent_source_chat(self):
        self.f['genuine_blindness_independently_attested']=True;self.bad('SOURCE_ONLY_CANNOT')
    def test_06_fake_71_source_atom_truth(self):
        self.f['source_first_candidate_is_financial_truth']=True;self.bad('SOURCE_ONLY_CANNOT')
    def test_07_zero_source_cues(self):
        self.f['source_only_cues_checked']=0;self.bad('SOURCE250_FIRSTPASS')
    def test_08_hidden_source_candidates(self):
        self.f['provisional_atomic_candidate_count']=70;self.bad('SOURCE250_FIRSTPASS')
    def test_09_high_risk_36_silenced(self):
        self.f['high_risk_provisional_candidate_count']=0;self.bad('SOURCE250_FIRSTPASS')
    def test_10_missing_cue_and_fake_coverage(self):
        self.f['source_coverage_missing_indices']=[15];self.bad('SOURCE250_FIRSTPASS')
    def test_11_pretend_gold_covers_250(self):
        self.f['gold_independent_atom_count']=71;self.bad('PROVISIONAL_GOLD')
    def test_12_pretend_precision_95(self):
        self.f['independent_precision']=0.95;self.bad('PROVISIONAL_GOLD')
    def test_13_false_recall_100(self):
        self.f['independent_recall']=1;self.bad('PROVISIONAL_GOLD')
    def test_14_fake_high_risk_fn_zero(self):
        self.f['high_risk_FN']=0;self.bad('PROVISIONAL_GOLD')
    def test_15_crosswalk_without_precomparison_freeze(self):
        self.f['pre_crosswalk_freeze']=False;self.bad('PROVISIONAL_GOLD')
    def test_16_crosswalk_different_native_sha(self):
        self.c['frozen_prediction_sha256']='0'*64;self.bad('POST_COMPARE_SCOPE')
    def test_17_crosswalk_different_source_candidate_sha(self):
        self.c['pre_comparison_frozen_source_first_sha256']='0'*64;self.bad('DIAGNOSTIC_AFTER_FREEZE')
    def test_18_wrong_crosswalk_zip(self):
        self.c['post_comparison_crosswalk_zip_sha256']='0'*64;self.bad('DIAGNOSTIC_AFTER_FREEZE')
    def test_19_68_original_preds_falsified(self):
        self.c['original_native_prediction_count']=67;self.bad('POST_COMPARE_SOURCE_COUNTS')
    def test_20_two_source_only_candidates_silenced(self):
        self.c['source_candidates_without_separate_native_topic_link']=0;self.bad('SPLIT_MERGE_KIND')
    def test_21_index_scope_atom_14_disappears(self):
        self.c['source_only_standalone_candidate_ids']=['P205-SRC-003'];self.bad('SPLIT_MERGE_KIND')
    def test_22_kind_disagreements_silenced(self):
        self.c['kind_label_disagreement_related_pairs']=0;self.bad('SPLIT_MERGE_KIND')
    def test_23_many_to_one_unresolved_ignored(self):
        self.c['native_atoms_related_to_multiple_source_candidates']=0;self.bad('SPLIT_MERGE_KIND')
    def test_24_link_assumed_exact_TP(self):
        self.c['lexical_or_topic_relation_as_TP']=True;self.bad('TOPIC_RELATION')
    def test_25_unlinked_topic_assumed_true_FN(self):
        self.c['unmatched_topic_relation_as_FN']=True;self.bad('TOPIC_RELATION')
    def test_26_same_chat_labelled_independent(self):
        self.c['manually_reviewed_same_chat_is_independent']=True;self.bad('TOPIC_RELATION')
    def test_27_fake_p205_accuracy_pass(self):
        self.c['no_e2_final_approval']=False;self.bad('NO_ACCURACY')
    def test_28_fake_p205_highrisk_zero(self):
        self.c['high_risk_FN']=0;self.bad('NO_ACCURACY')
    def test_29_fake_existing_gold_reviewer_count(self):
        self.g['independently_adjudicated_gold_atomic_claims']=71;self.bad('PRIOR_HOLD')
    def test_30_skip_to_p206(self):
        self.s['items'][17]['status']='READY';self.bad('P205_HOLD')
    def test_31_skip_cursor_to_p206(self):
        self.l['development_gate']['this_item']='P0-2-06';self.bad('UNAUTHORIZED_P206')
    def test_32_falsely_mark_p205_pass(self):
        self.s['items'][16]['status']='PASS';self.bad('P205_HOLD')

if __name__=='__main__':
    unittest.main()
