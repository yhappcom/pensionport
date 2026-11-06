"""Deterministic regressions for source-cue, source identity and tax-safety gates."""
from pathlib import Path
import unittest,json,copy
from ire.v5.first_five_phase1_third_twenty_gate import verify,Phase1ReviewError
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'ire/v5/validation/first_five_phase1_video1_21_40_cue_review_20261106.json'

class Phase1ThirdTwentyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.source=json.loads(DATA.read_text('utf-8'))
    def fresh(self):return copy.deepcopy(self.source)
    def test_baseline_source_scoped_open_verdict(self):
        r=verify(ROOT)
        self.assertEqual(r['source_video1_reviewed_windows'],40)
        self.assertEqual(r['five_video_unresolved_cues_remaining'],4236)
        self.assertEqual(r['private_claims_reviewed'],314)
        self.assertFalse(r['original_source_replayed_in_this_execution'])
        self.assertEqual(r['full_five_video_research_closure'],'BLOCKED')
    def test_financial_promotion_forbidden(self):
        for k,v in [('all_five_ResearchRun_CLOSURE_issued',True),
                    ('official_personal_finance_fact_approved',1),
                    ('investment_advice_authorized',True),
                    ('full_original_atomic_claim_recall_proven',True),
                    ('B04_legacy_merge_approved',True)]:
            data=self.fresh();data[k]=v
            with self.subTest(k=k),self.assertRaises(Phase1ReviewError):verify(ROOT,data)
    def test_provisional_count_cannot_equal_all_completed(self):
        data=self.fresh();data['current_five_video_unresolved_cue_count']=0
        with self.assertRaises(Phase1ReviewError):verify(ROOT,data)
    def test_source_window_hash_mutation_rejected(self):
        data=self.fresh();data['original_window_reviews'][3]['window_sha256']='0'*64
        with self.assertRaises(Phase1ReviewError):verify(ROOT,data)
    def test_source_window_cue_gap_rejected(self):
        data=self.fresh();data['original_window_reviews'][4]['cue_dispositions'].pop()
        with self.assertRaises(Phase1ReviewError):verify(ROOT,data)
    def test_nonclaim_whitelist_not_automatic(self):
        data=self.fresh();data['original_window_reviews'][2]['cue_dispositions'][0]['status']='NONCLAIM'
        with self.assertRaises(Phase1ReviewError):verify(ROOT,data)
    def test_unreviewed_financial_cue_cannot_be_relabelled_nonclaim(self):
        data=self.fresh();w=data['original_window_reviews'][0];cue=350
        w['claims'][0]['cue_ids'].remove(cue)
        w['cue_dispositions'][0]={'cue_index':cue,'status':'NONCLAIM','claim_ids':[],
             'reason':'This financial speech is not an incidental greeting.'}
        with self.assertRaises(Phase1ReviewError):verify(ROOT,data)
    def test_reuse_of_misidentified_prior_claim_id_denied(self):
        data=self.fresh();data['original_window_reviews'][12]['claims'][0]['claim_id']='V5C0027'
        with self.assertRaises(Phase1ReviewError):verify(ROOT,data)
    def test_public_payload_no_private_quotation(self):
        data=self.fresh();data['original_window_reviews'][5]['claims'][0]['source_text']='raw source excerpt'
        with self.assertRaises(Phase1ReviewError):verify(ROOT,data)
    def test_bad_tax_rate_arithmetic_denied(self):
        data=self.fresh();data['financial_numeric_recheck']['gross_10billion_16p5percent_after_tax_krw']=8460000000
        with self.assertRaises(Phase1ReviewError):verify(ROOT,data)
    def test_bad_twenty_year_compound_denied(self):
        data=self.fresh();data['financial_numeric_recheck']['pension_500k_monthly_20y_7pct_krw']=250000000
        with self.assertRaises(Phase1ReviewError):verify(ROOT,data)
    def test_statutory_candidate_not_approved(self):
        data=self.fresh();data['original_window_reviews'][1]['claims'][2]['financial_fact_approved']=True
        with self.assertRaises(Phase1ReviewError):verify(ROOT,data)
    def test_bad_event_chain_prior_head_denied(self):
        data=self.fresh();data['prior_video1_event_head_sha256']='0'*64
        with self.assertRaises(Phase1ReviewError):verify(ROOT,data)
    def test_untrusted_external_source_rejected(self):
        data=self.fresh();data['original_window_reviews'][0]['claims'][1]['official_evidence_url_candidates']=['https://fraud.example/finance']
        with self.assertRaises(Phase1ReviewError):verify(ROOT,data)
    def test_private_mode_requires_original_and_run(self):
        with self.assertRaises(Phase1ReviewError):verify(ROOT,source_zip=Path('/notfound'))
        with self.assertRaises(Phase1ReviewError):verify(ROOT,private_root=Path('/notfound'))
if __name__=='__main__':unittest.main()
