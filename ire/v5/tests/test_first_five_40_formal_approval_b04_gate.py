"""First-40 precise rule dispositions, B04 partition, and fact-approval safety."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from ire.v5 import first_five_40_formal_approval_b04_gate as gate

DATA=Path(__file__).resolve().parents[1]
OPEN=DATA/'validation/first_five_40_open5_resolution_20261106.json'
B04=DATA/'legacy_consolidation/B04_FIRST40_SCOPED_EDUCATION_EDGES_20261106.json'
OLD=DATA/'validation/first_five_40_scoped_fact_knowledge_review_20261106.json'

class FormalScopeAndB04SafetyTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.base=json.loads(OLD.read_text('utf-8'))
  cls.base_res=json.loads(OPEN.read_text('utf-8'))
  cls.base_b04=json.loads(B04.read_text('utf-8'))
  cls.prev=[{'claim_id':f'GOMHEE-C{i:02d}' if i<100 else f'GOMHEE-C{i}',
             'supporting_videos':['Unrelated1']} for i in range(1,117)]
 def setUp(self):
  self.old=copy.deepcopy(self.base);self.res=copy.deepcopy(self.base_res)
  self.b04=copy.deepcopy(self.base_b04);self.prior=copy.deepcopy(self.prev)
 def check(self):return gate.verify_bundle(self.old,self.res,self.b04,self.prior)
 def test_five_terminal_safety_with_six_B04_links(self):
  x=self.check()
  self.assertEqual(x['five_composite_reviews_terminal'],5)
  self.assertEqual(x['b04_scope_accepted_education_edges'],6)
  self.assertEqual(x['outside_b04_links_unmerged'],9)
  self.assertEqual(x['v5_kernel_official_financial_facts_approved'],0)
  self.assertFalse(x['formal_B04_master_fact_merge_approved'])
 def test_original_claim_cannot_be_promoted(self):
  self.res['open_five_review_outcomes'][0]['full_video_speaker_claim_certified']=True
  with self.assertRaisesRegex(gate.FormalGateError,'UNAUTHORIZED_KERNEL_APPROVAL'):self.check()
 def test_personalized_advice_cannot_be_promoted(self):
  self.res['open_five_review_outcomes'][0]['person_specific_tax_advice_approved']=True
  with self.assertRaisesRegex(gate.FormalGateError,'UNAUTHORIZED_KERNEL_APPROVAL'):self.check()
 def test_fake_official_byte_snapshot_is_blocked(self):
  self.res['authority_text_byte_snapshots_pinned']=True
  with self.assertRaisesRegex(gate.FormalGateError,'FALSE_FINANCIAL_FACT_APPROVAL'):self.check()
 def test_2026_3_percent_change_is_required(self):
  self.res['authorities']['NTS_RATE2026']['evidence']='단순 연금소득은 과거 세율을 적용하여 모두 종신형 세율이 단일한다.'
  self.res['authorities']['NTS_RATE2026']['paraphrase_sha256']=gate.sha256(self.res['authorities']['NTS_RATE2026']['evidence'].encode())
  with self.assertRaisesRegex(gate.FormalGateError,'PENSION_2026_RATE_CHANGE_OMITTED'):self.check()
 def test_nonofficial_financial_domain_disallowed(self):
  self.res['authorities']['LAW_55']['url']='https://some-finance-forum.example/claims'
  with self.assertRaisesRegex(gate.FormalGateError,'NONOFFICIAL_AUTHORITY'):self.check()
 def test_status_five_are_not_implicitly_all_valid_law(self):
  self.res['open_five_review_outcomes'][3]['final_review_disposition']='ALL_TAX_RATE_EXACT_APPROVED'
  with self.assertRaisesRegex(gate.FormalGateError,'OPEN_FIVE_WHOLE_CLAIM_UNSAFELY_APPROVED'):self.check()
 def test_source_claim_sha_drift_blocked(self):
  self.res['open_five_review_outcomes'][2]['original_claim_payload_sha256']='0'*64
  with self.assertRaisesRegex(gate.FormalGateError,'SPEAKER_ORIGINAL_SOURCE_LINK_TAMPERED'):self.check()
 def test_mutated_cue_links_blocked(self):
  self.res['open_five_review_outcomes'][2]['source_cue_indices']=[100]
  with self.assertRaisesRegex(gate.FormalGateError,'SPEAKER_ORIGINAL_SOURCE_LINK_TAMPERED'):self.check()
 def test_B04_not_full_knowledge_master(self):
  self.b04['B04_formal_master_fact_merge_completed']=True
  with self.assertRaisesRegex(gate.FormalGateError,'B04_MASTER_PROMOTED_WITHOUT_FACT_VERIFICATION'):self.check()
 def test_B04_wrong_legacy_target_blocked(self):
  self.b04['B04_scoped_education_edges'][0]['prior_claim_id']='GOMHEE-C21'
  with self.assertRaisesRegex(gate.FormalGateError,'B04_EDGE_FABRICATED|B04_CROSS_BATCH'):self.check()
 def test_cross_batch_misplaced_cannot_be_promoted(self):
  e=self.b04['cross_batch_edges_not_promoted_here'].pop()
  e['link_status']='SCOPED_EDUCATION_EDGE_ACCEPTED_NOT_LEGACY_MASTER_MERGED'
  self.b04['B04_scoped_education_edges'].append(e)
  with self.assertRaisesRegex(gate.FormalGateError,'B04_EDGES_COUNT_OR_PARTITION_INVALID'):self.check()
 def test_prior_video_fraud_blocked(self):
  self.prior[65]['supporting_videos']=['sz5N9WJS310']
  with self.assertRaisesRegex(gate.FormalGateError,'B04_HISTORICAL_VIDEO_PROVENANCE_FABRICATED'):self.check()
 def test_prior_master_anchor_changed_blocked(self):
  self.res['prior_master_git_blob_sha']='a'*40
  with self.assertRaisesRegex(gate.FormalGateError,'RULE_RESOLUTION_IDENTITY_DRIFT'):self.check()
 def test_missing_source_rejected(self):
  self.res['open_five_review_outcomes'][4]['official_authority_ids']=[]
  with self.assertRaisesRegex(gate.FormalGateError,'RULE_MISSING_DIRECT_OFFICIAL_SCOPE'):self.check()
 def test_bogus_attestation_flags_never_approve_financial_fact(self):
  x=gate.authorize_formal_financial_fact({'raw_official_source_bytes_verified':True,'verifier_credential_registry_match':True})
  self.assertFalse(x['authorized'])
  self.assertEqual(x['reason'],'TRUSTED_VERIFIER_REGISTRY_NOT_IMPLEMENTED')
 def test_no_attestation_cannot_approve(self):
  self.assertFalse(gate.authorize_formal_financial_fact(None)['authorized'])

if __name__=='__main__':unittest.main()
