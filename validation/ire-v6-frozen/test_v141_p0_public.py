"""CI metadata and red-team regression: never claims owner-original replay in CI."""
import json, unittest
from pathlib import Path
from v141_p0_completion_gate import audit_candidate_readonly,audit_census_not_final,EXPECTED_PARENT_SHA
ROOT=Path(__file__).parent
META=json.loads((ROOT/'V141_SOURCE_FIRST_SHA_ONLY.json').read_text('utf8'))
class V141PublicNonPromotion(unittest.TestCase):
 def test_01_source_and_scope_census(self):
  self.assertEqual(META['parent_source_sha256'],EXPECTED_PARENT_SHA)
  self.assertEqual((META['reviewed_cue_count'],META['segments_count'],META['new_cue_dispositions']),(1481,13,761))
  self.assertEqual(META['new_provisional_atom_occurrences'],109)
  self.assertEqual(META['provisional_atom_occurrences_total'],274)
 def test_02_all_seven_private_receipts_sha_only(self):
  self.assertEqual(len(META['new_segment_receipts']),7)
  self.assertEqual([x['segment_id'] for x in META['new_segment_receipts']],[f'B{i:04d}' for i in range(7,14)])
  self.assertEqual(sum(x['cue_count'] for x in META['new_segment_receipts']),761)
  self.assertEqual(sum(x['new_asr_open'] for x in META['new_segment_receipts']),49)
  for x in META['new_segment_receipts']:
   self.assertRegex(x['cue_rows_sha256'],r'^[0-9a-f]{64}$')
   self.assertRegex(x['packet_sha256'],r'^[0-9a-f]{64}$')
 def test_03_no_precision_fooled_by_frozen_scope(self):
  self.assertFalse(META['independent_semantic_gold_passed'])
  self.assertIsNone(META['precision'])
  self.assertIsNone(META['recall'])
  self.assertFalse(META['p0_go'])
 def test_04_source_census_never_approves(self):
  x=audit_census_not_final(META)
  self.assertEqual(x['status'],'SOURCE_CENSUS_COMPLETE_FINAL_SEMANTIC_QUALITY_UNPROVEN')
  self.assertFalse(x['knowledge_export_allowed'])
 def test_05_forged_metadata_flags_not_acceptance(self):
  d=dict(META);d['v123_passed_scopes']=13;d['p0_go']=True;d['independent_semantic_gold_passed']=True
  self.assertFalse(audit_census_not_final(d)['p0_go'])
 def test_06_missing_scope_prevents_census(self):
  d=dict(META);d['reviewed_cue_count']=1480
  self.assertEqual(audit_census_not_final(d)['status'],'HOLD_CENSUS_INCONSISTENT')
 def test_07_missing_diversification_exception_blocks(self):
  q=audit_candidate_readonly(parent_source_sha256=EXPECTED_PARENT_SHA,candidate_claim_ids=['B13_FIVE_STOCKS_LIFE_CHANGING_GAIN_ADVOCACY'])
  self.assertEqual(q['status'],'HOLD_MISSING_MANDATORY_SEMANTIC_CONTEXT')
 def test_08_context_complete_still_unapproved(self):
  ids=['B13_FIVE_STOCKS_LIFE_CHANGING_GAIN_ADVOCACY','B10_NONEXPERT_DIVERSIFY_EXCEPTION','B10_DRAWDOWN_ALWAYS_LEADS_BIG_GAIN_FALSE']
  q=audit_candidate_readonly(parent_source_sha256=EXPECTED_PARENT_SHA,candidate_claim_ids=ids)
  self.assertEqual(q['status'],'HOLD_HIGH_RISK_SOURCE_FACT_OR_ADVICE_UNAPPROVED')
 def test_09_dividend_yield_not_margin_of_safety(self):
  q=audit_candidate_readonly(parent_source_sha256=EXPECTED_PARENT_SHA,candidate_claim_ids=['B11_DIVIDEND_YIELD_EQUALS_MARGIN_FALSE'])
  self.assertEqual(q['status'],'HOLD_MISSING_MANDATORY_SEMANTIC_CONTEXT')
 def test_10_company_hbm_missing_context_blocks(self):
  q=audit_candidate_readonly(parent_source_sha256=EXPECTED_PARENT_SHA,candidate_claim_ids=['B7_SAMSUNG_DID_NOT_MAKE_HBM_FALSE'])
  self.assertFalse(q['answer_release_allowed'])
 def test_11_forged_v123_counts_cannot_promote(self):
  q=audit_candidate_readonly(parent_source_sha256=EXPECTED_PARENT_SHA,candidate_claim_ids=[],approved_v123_receipts=13,formal_knowledge_entries=274)
  self.assertEqual(q['status'],'HOLD_UNVERIFIED_SELF_ATTESTED_APPROVAL_COUNTS')
 def test_12_no_private_srt_in_public_metadata(self):
  self.assertNotIn('source_cues',META)
  self.assertNotIn('raw_srt',META)
  self.assertEqual(META['v123_passed_scopes'],0)
  self.assertEqual(META['published_research_knowledge_atoms'],0)
if __name__=='__main__':unittest.main(verbosity=2)
