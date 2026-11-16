import copy,json,unittest
from pathlib import Path
from v142_p0_open_evidence_gate import audit_public_triage,audit_high_risk_context,REQUIRED_FACT_CHECK
META=json.loads((Path(__file__).parent/'V142_SOURCE_FIRST_SHA_ONLY.json').read_text(encoding='utf8'))
class V142PublicP0(unittest.TestCase):
 def test_01_real_custody_receipt_still_hold(self):
  r=audit_public_triage(META)
  self.assertEqual(r['status'],'REAL_SOURCE_AND_88_OPEN_CENSUS_VERIFIED_REMAIN_HOLD')
  self.assertFalse(r['p0_go'])
 def test_02_unreported_audio_open_rejected(self):
  x=copy.deepcopy(META);x['open_source_cues_remain_unverified_audio']=87
  self.assertTrue(audit_public_triage(x)['status'].startswith('REJECT'))
 def test_03_fake_all_88_audio_closed_rejected(self):
  x=copy.deepcopy(META);x['open_source_cues_remain_unverified_audio']=0
  self.assertTrue(audit_public_triage(x)['status'].startswith('REJECT'))
 def test_04_forged_parent_source_rejected(self):
  x=copy.deepcopy(META);x['source_sha256']='0'*64
  self.assertTrue(audit_public_triage(x)['status'].startswith('REJECT'))
 def test_05_forged_approved_v123_rejected(self):
  x=copy.deepcopy(META);x['v123_final_passed_segments']=13
  self.assertTrue(audit_public_triage(x)['status'].startswith('REJECT'))
 def test_06_false_research_publication_rejected(self):
  x=copy.deepcopy(META);x['research_publication_allowed']=True
  self.assertTrue(audit_public_triage(x)['status'].startswith('REJECT'))
 def test_07_zero_remaining_open_cannot_be_passed_as_boolean(self):
  x=copy.deepcopy(META);x['open_source_cues_remain_unverified_audio']=False
  self.assertTrue(audit_public_triage(x)['status'].startswith('REJECT'))
 def test_08_high_risk_claim_missing_required_context(self):
  r=audit_high_risk_context(['B13_FIVE_STOCKS_LIFE_CHANGING_GAIN_ADVOCACY'])
  self.assertEqual(r['status'],'HOLD_MISSING_SOURCE_BOUND_RISK_CONTEXT')
 def test_09_with_required_context_still_no_advice(self):
  r=audit_high_risk_context(['B13_FIVE_STOCKS_LIFE_CHANGING_GAIN_ADVOCACY','B10_NONEXPERT_DIVERSIFY_EXCEPTION'],requested_release=True)
  self.assertEqual(r['status'],'HOLD_SOURCE_ONLY_HIGH_RISK_FACT_OR_ADVICE')
  self.assertFalse(r['release_allowed'])
 def test_10_context_link_completeness(self):
  self.assertEqual(len(REQUIRED_FACT_CHECK),13)
  self.assertTrue(all(v for v in REQUIRED_FACT_CHECK.values()))
 def test_11_no_high_risk_is_not_v123(self):
  r=audit_high_risk_context([],requested_release=True)
  self.assertEqual(r['status'],'HOLD_NO_REAL_V123_SIGNED_PARENT_REPLAY')
 def test_12_private_gold_claim_forgery_rejected(self):
  x=copy.deepcopy(META);x['independent_semantic_precision_verified']=True
  self.assertTrue(audit_public_triage(x)['status'].startswith('REJECT'))
if __name__=='__main__':unittest.main(verbosity=2)
