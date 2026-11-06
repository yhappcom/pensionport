"""Fail-closed source, scope, arithmetic, approval and event-chain checks."""
from pathlib import Path
import copy,json,unittest
from ire.v5.first_five_phase1_cue_gate import Phase1ReviewError
from ire.v5.first_five_phase1_second_ten_gate import verify
ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'ire/v5/validation/first_five_phase1_video1_11_20_cue_review_20261106.json'
class Phase1SecondTenGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=json.loads(SOURCE.read_text('utf-8'))
    def fresh(self):return copy.deepcopy(self.data)
    def test_frozen_progress_is_not_full_release(self):
        x=verify(ROOT)
        self.assertEqual(x['manually_reviewed_windows_video1'],20)
        self.assertEqual(x['source_cues_reviewed_video1'],349)
        self.assertEqual(x['five_video_new_unresolved_cues_remaining'],4578)
        self.assertFalse(x['private_original_zip_replayed_in_this_run'])
        self.assertEqual(x['financial_rule_or_personal_advice_release'],'NO_GO')
    def test_false_financial_promotion_denied(self):
        for k,v in [('all_five_ResearchRun_CLOSURE_issued',True),('official_personal_finance_fact_approved',1),('investment_advice_authorized',True),('full_original_atomic_recall_proven',True)]:
            d=self.fresh();d[k]=v
            with self.subTest(k=k),self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_source_hash_drift_denied(self):
        d=self.fresh();d['source_window_reviews'][1]['window_sha256']='0'*64
        with self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_nonfinancial_conversion_denied(self):
        d=self.fresh();d['source_window_reviews'][0]['cue_dispositions'][0]['status']='NONCLAIM'
        with self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_unreviewed_nonclaim_promotion_denied(self):
        d=self.fresh();row=d['source_window_reviews'][0]
        row['claims'][0]['cue_ids'].remove(170)
        row['cue_dispositions'][0]={'cue_index':170,'status':'NONCLAIM','claim_ids':[],
             'reason':'An unreviewed financial assertion must never be marked NONCLAIM.'}
        with self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_claim_direct_quote_disclosure_denied(self):
        d=self.fresh();d['source_window_reviews'][1]['claims'][0]['quote']='private transcript raw'
        with self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_retired_previous_claim_id_cannot_be_reused(self):
        d=self.fresh();d['source_window_reviews'][0]['claims'][0]['claim_id']='V5C0011'
        with self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_period_conflict_cannot_be_silently_corrected(self):
        d=self.fresh();d['source_period_discrepancy_not_audio_confirmed']='No errors.'
        with self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_math_7_year_incorrect_5100_vs_3200(self):
        d=self.fresh();d['arithmetic_recheck'][0]['future_value_krw']=51925442
        with self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_prior_event_chain_head_change_denied(self):
        d=self.fresh();d['first_ten_prior_event_head_sha256']='0'*64
        with self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_bad_open_status_denied(self):
        d=self.fresh();d['private_actual_replay_status_summary'][0]['unresolved_cues']=0
        with self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_private_replay_needs_both_owner_inputs(self):
        with self.assertRaises(Phase1ReviewError):verify(ROOT,original_zip=Path('/wrong'))
        with self.assertRaises(Phase1ReviewError):verify(ROOT,private_root=Path('/wrong'))
if __name__=='__main__':unittest.main()
