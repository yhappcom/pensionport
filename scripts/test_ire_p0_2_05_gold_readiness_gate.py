"""P0-2-05 public regression: never certify synthetic or same-chat gold as independent."""
from __future__ import annotations
import copy,unittest
from scripts.ire_p0_2_05_gold_readiness_gate import (
    ROOT,P205,PLAN,STATE,LEDGER,load,verify,
)

class P205GoldReadinessNegativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline=tuple(load(ROOT,p) for p in (P205,STATE,LEDGER,PLAN))
    def setUp(self):
        self.r,self.s,self.l,self.p=copy.deepcopy(self.baseline)
    def errors(self):
        return verify(ROOT,receipt=self.r,state=self.s,ledger=self.l,plan=self.p)
    def invalid(self,label):
        errors=self.errors()
        self.assertTrue(any(label in x for x in errors),errors)
    def test_01_actual_gold_hold_with_deterministic_source_custody(self):
        self.assertEqual([],verify(ROOT,receipt=self.r,state=self.s,ledger=self.l,plan=self.p,historical_only=True))
    def test_02_cannot_mark_p205_pass_without_independent_gold(self):
        self.s['items'][16]['status']='PASS'
        self.invalid('CHECKLIST')
    def test_03_cannot_unlock_p206_while_p205_hold(self):
        self.s['items'][17]['status']='READY'
        self.invalid('PREVIOUS_16_PASS')
    def test_04_wrong_active_stage_cursor(self):
        self.l['development_gate']['this_item']='P0-2-06'
        self.invalid('LEDGER_CANNOT_ADVANCE')
    def test_05_68_prediction_atoms_tampered(self):
        self.r['frozen_legacy_candidate_atom_count']=67
        self.invalid('SOURCE_ONLY_PACKET')
    def test_06_original_srt_digest_tampered(self):
        self.r['source_srt_sha256']='0'*64
        self.invalid('EVIDENCE_HASH')
    def test_07_250_cue_packet_missing_one(self):
        self.r['source_only_blind_packet_cues']=249
        self.invalid('SOURCE_ONLY_PACKET')
    def test_08_production_plan_version_forged(self):
        self.p['preregistration_revision']='V99'
        self.invalid('PREREGISTERED')
    def test_09_precision_minimum_weakened(self):
        self.p['assessment']['thresholds']['atomic_precision_min_bp']=9400
        self.invalid('TARGETS_95_98')
    def test_10_recall_minimum_weakened(self):
        self.p['assessment']['thresholds']['atomic_recall_min_bp']=9700
        self.invalid('TARGETS_95_98')
    def test_11_high_risk_FN_threshold_weakened(self):
        self.p['assessment']['thresholds']['high_risk_false_negative_max']=1
        self.invalid('TARGETS_95_98')
    def test_12_reviewer_one_falsely_authenticated(self):
        self.r['blinded_reviewer_one_authenticated']=True
        self.invalid('NO_UNATTESTED')
    def test_13_gold_rater_two_falsely_authenticated(self):
        self.r['blinded_reviewer_two_authenticated']=True
        self.invalid('NO_UNATTESTED')
    def test_14_forged_gold_atomic_claim_count(self):
        self.r['independently_adjudicated_gold_atomic_claims']=100
        self.invalid('NO_UNATTESTED')
    def test_15_gold_lock_hash_forged(self):
        self.r['reviewer_gold_sha256_frozen']='0'*64
        self.invalid('NO_UNATTESTED')
    def test_16_gold_alignment_hash_forged(self):
        self.r['prediction_to_gold_alignment_sha256_frozen']='0'*64
        self.invalid('NO_UNATTESTED')
    def test_17_false_perfect_gold_precision(self):
        self.r['precision']=1.0
        self.invalid('INDEPENDENT_MEASUREMENT')
    def test_18_false_perfect_gold_recall(self):
        self.r['recall']=1.0
        self.invalid('INDEPENDENT_MEASUREMENT')
    def test_19_fake_zero_high_risk_FN(self):
        self.r['high_risk_false_negative_count']=0
        self.invalid('INDEPENDENT_MEASUREMENT')
    def test_20_relabel_p201_source_cue_triage_as_atomic_gold(self):
        self.r['prior_p201_is_independent_atomic_gold']=True
        self.invalid('OLD_SOURCE_FIRST')
    def test_21_relabel_p203_internal_meaning_review_as_blind(self):
        self.r['previous_p203_private_meaning_review_is_independently_blind']=True
        self.invalid('OLD_SOURCE_FIRST')
    def test_22_disclose_legacy_predictions_in_gold_packet(self):
        self.r['source_only_blind_packet_original_candidate_atom_text_included']=True
        self.invalid('SOURCE_ONLY_PACKET')
    def test_23_show_p202_labels_to_gold_reviewer(self):
        self.r['source_only_blind_packet_prior_p201_p202_p203_labels_included']=True
        self.invalid('SOURCE_ONLY_PACKET')
    def test_24_falsify_e2_finance_accuracy(self):
        self.r['real_etf_e2_accuracy_final_pass']=True
        self.invalid('FALSE_E2_E3')
    def test_25_falsify_e3_v123_13_approvals(self):
        self.r['real_etf_e3_v123_approved_children']=13
        self.invalid('FALSE_E2_E3')
    def test_26_falsify_e5_actual_published_knowledge(self):
        self.r['real_etf_e5_knowledge_publications']=1
        self.invalid('FALSE_E2_E3')
    def test_27_fake_software_tests_are_financial_gold(self):
        self.r['synthetic_gold_evaluation_cases_are_independent_financial_proof']=True
        self.invalid('SYNTHETIC_UNIT_TESTS')
    def test_28_fake_unblocked_successor(self):
        self.r['next_item_status']='READY'
        self.invalid('NO_SEQUENTIAL')
    def test_29_missing_library_intake_hash(self):
        self.r['gold_candidate_source_only_intake_sha256']='0'*64
        self.invalid('EVIDENCE_HASH')
    def test_30_fake_independent_conversation_without_blinding(self):
        self.p['independence_contract']['chatgpt_same_conversation_reviewer_without_proven_blinding_is_independent']=True
        self.invalid('NO_FAKE_BLINDED')

if __name__=='__main__':
    unittest.main()
