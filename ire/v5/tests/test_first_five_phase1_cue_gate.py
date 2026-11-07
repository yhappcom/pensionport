"""Adversarial tests for original cue adjudication / no false formal release."""
import copy,json,unittest
from pathlib import Path
from ire.v5.first_five_phase1_cue_gate import verify,Phase1ReviewError

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'ire/v5/validation/first_five_phase1_video1_10_windows_cue_review_20261106.json'

class FirstFivePhase1CueGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical=json.loads(DATA.read_text('utf-8'))
    def row(self):return copy.deepcopy(self.canonical)
    def test_current_public_gate_no_fake_private_replay(self):
        v=verify(ROOT)
        self.assertEqual(v['previously_unresolved_cues_newly_dispositioned'],159)
        self.assertEqual(v['actual_v5_private_model_evidence_relation_windows'],10)
        self.assertEqual(v['all_five_video_unresolved_cues_remaining'],4749)
        self.assertFalse(v['actual_v5_original_source_private_replayed_this_run'])
        self.assertEqual(v['financial_advisory_release'],'NO_GO')
    def test_false_full_research_or_advice_approval_denied(self):
        for key,value in [('finance_education_full_release_go',True),
                          ('formal_five_video_research_closures_issued',5),
                          ('independently_verified_financial_facts_approved',3),
                          ('no_universal_recall_proven',False)]:
            d=self.row();d[key]=value
            with self.subTest(key=key),self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_original_window_digest_change_denied(self):
        d=self.row();d['source_window_reviews'][2]['window_sha256']='0'*64
        with self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_automatically_relabeling_financial_cue_as_nonclaim_denied(self):
        d=self.row();d['source_window_reviews'][0]['cue_dispositions'][1]['status']='NONCLAIM'
        with self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_wiping_original_claim_id_or_inverse_links_denied(self):
        d=self.row();d['source_window_reviews'][2]['claims'][0]['cue_ids']=[]
        with self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_old_claim_id_cannot_be_reused_for_new_meaning(self):
        d=self.row();d['source_window_reviews'][1]['claims'][0]['claim_id']='V5C0003'
        with self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_forged_nonclaim_new_cue_denied(self):
        d=self.row();d['source_window_reviews'][3]['claims'][0]['cue_ids'].remove(44)
        d['source_window_reviews'][3]['cue_dispositions'][0]['claim_ids']=[]
        d['source_window_reviews'][3]['cue_dispositions'][0]['status']='NONCLAIM'
        d['source_window_reviews'][3]['cue_dispositions'][0]['reason']='Marking an unexamined cue as a greeting for artificial completion.'
        with self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_missing_cue_rejected(self):
        d=self.row();d['source_window_reviews'][4]['cue_dispositions'].pop()
        with self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_math_mistake_or_guaranteed_yield_denied(self):
        for key,value in [('amount_krw',40000000),('not_guaranteed',False)]:
            d=self.row();d['arithmetic_rechecked'][0][key]=value
            with self.subTest(key=key),self.assertRaises(Phase1ReviewError):verify(ROOT,d)
    def test_private_replay_requires_both_original_and_events(self):
        with self.assertRaises(Phase1ReviewError):verify(ROOT,private_root=Path('/wrong'))
        with self.assertRaises(Phase1ReviewError):verify(ROOT,original_zip=Path('/wrong'))
    def test_original_quote_not_admitted_to_public_ledger(self):
        d=self.row();d['source_window_reviews'][0]['claims'][0]['quote']='raw private speech'
        with self.assertRaises(Phase1ReviewError):verify(ROOT,d)

if __name__=='__main__':unittest.main()
