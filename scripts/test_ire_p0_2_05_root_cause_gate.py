"""Synthetic mutants proving no fake P205 production go on current owner evidence."""
from __future__ import annotations
import copy,unittest
from unittest.mock import patch
from scripts.ire_p0_2_05_root_cause_gate import ROOT,RECEIPT,STATE,LEDGER,load,verify

class P205RootCausePublicGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=(load(ROOT,RECEIPT),load(ROOT,STATE),load(ROOT,LEDGER))
    def setUp(self):self.r,self.s,self.l=copy.deepcopy(self.base)
    def err(self):return verify(ROOT,receipt=self.r,state=self.s,ledger=self.l)
    def bad(self,label):
        e=self.err();self.assertTrue(any(label in x for x in e),e)
    def test_01_full_current_hold_gate_is_valid(self):self.assertEqual([],verify(ROOT,receipt=self.r,state=self.s,ledger=self.l,historical_only=True))
    def test_02_wrong_srt_bytes_hash(self):self.r['protected_original_source_srt_sha256']='0'*64;self.bad('HASHES')
    def test_03_wrong_native_prediction_hash(self):self.r['protected_original_frozen_native_sha256']='0'*64;self.bad('HASHES')
    def test_04_wrong_source_only_packet_hash(self):self.r['protected_source_only_intake_zip_sha256']='0'*64;self.bad('HASHES')
    def test_05_missing_original_cue(self):self.r['original_source_cues']=249;self.bad('CENSUS')
    def test_06_fake_blind_pred_not_exposed(self):self.r['source_only_intake_prediction_text_absent']=False;self.bad('CENSUS')
    def test_07_fake_atomic_gold_locked(self):self.r['current_gold_atoms_frozen']=250;self.bad('ABSENT')
    def test_08_fake_two_independent_host_sessions(self):self.r['actual_authenticated_blind_review_records']=2;self.bad('ABSENT')
    def test_09_fake_host_trust_registry(self):self.r['actual_host_pinned_public_key_sets']=1;self.bad('ABSENT')
    def test_10_fake_perfect_precision(self):self.r['current_atomic_precision']=1;self.bad('MEASUREMENTS')
    def test_11_fake_perfect_recall(self):self.r['current_atomic_recall']=1;self.bad('MEASUREMENTS')
    def test_12_fake_zero_highrisk_FN(self):self.r['current_high_risk_false_negative_count']=0;self.bad('MEASUREMENTS')
    def test_13_inflate_redgreen_baseline(self):self.r['red_proof_v6_failures']=6;self.bad('EVIDENCE')
    def test_14_hide_real_root_cause(self):self.r['original_gold_eval_defects'].pop();self.bad('BLOCKERS')
    def test_15_auto_production_pin_self_signed(self):
        with patch('scripts.ire_p0_2_05_root_cause_gate._production_pin',return_value='e'*64):self.bad('TRUST_ROOT_MUST_REMAIN')
    def test_16_synthetic_test_laundered_as_financial_gold(self):
        self.r['all_synthetic_tests_are_real_financial_accuracy_measurements']=True;self.bad('PRODUCTION_RELEASE')
    def test_17_preregistered_threshold_weakened(self):self.r['required_atomic_precision_basis_points']=9000;self.bad('THRESHOLDS')
    def test_18_fake_e3_authorization(self):self.r['e3_approvals']=13;self.bad('FAKE_RELEASE')
    def test_19_fake_e5_publication(self):self.r['e5_publications']=13;self.bad('FAKE_RELEASE')
    def test_20_attempt_p205_PASS(self):self.s['items'][16]['status']='PASS';self.bad('LIVE_CHECKLIST_CURSOR')
    def test_21_attempt_unlock_p206(self):self.s['items'][17]['status']='READY';self.bad('LIVE_CHECKLIST_CURSOR')
    def test_22_attempt_advance_canonical_cursor(self):self.l['development_gate']['this_item']='P0-2-06';self.bad('CHECKLIST_CURSOR')
    def test_23_fake_24_actual_reviewers(self):self.r['eligible_independently_adjudicated_gold_atoms']=24;self.bad('ABSENT')
    def test_history_receipt_validation_is_independent_of_live_cursor(self):
        self.s['items'][16]['status']='PASS'
        self.l['development_gate']['this_item']='P0-2-06'
        with patch('scripts.ire_p0_2_05_root_cause_gate._production_pin',return_value='e'*64):
            self.assertEqual([],verify(ROOT,receipt=self.r,state=self.s,ledger=self.l,historical_only=True))
            self.bad('LIVE_CHECKLIST_CURSOR')

    def test_historical_false_metrics_still_rejected(self):
        self.r['current_atomic_precision']=1
        self.assertTrue(any('MEASUREMENTS' in e for e in verify(
            ROOT,receipt=self.r,state=self.s,ledger=self.l,historical_only=True)))

    def test_pinned_historical_receipts(self):
        from scripts.ire_p205_history import verify_history
        self.assertEqual([],verify_history(ROOT))

    def test_24_forge_four_test_cases(self):self.r['positive_production_review_contract_synthetic_tests']=3;self.bad('PRODUCTION_RELEASE')

if __name__=='__main__':unittest.main()
