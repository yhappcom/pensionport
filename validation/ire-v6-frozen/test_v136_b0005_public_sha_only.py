"""V136 public metadata-only nonpromotion test: DOES NOT validate private SRT."""
import json, unittest
from pathlib import Path
R=json.loads((Path(__file__).parent/'V136_B0005_SOURCE_FIRST_SHA_ONLY.json').read_text('utf8'))
class V136B0005MetadataOnly(unittest.TestCase):
 def test_01_original_identity_and_bound_scope(self):
  self.assertEqual(R['schema'],'IRE_V136_B0005_REAL_SOURCE_FIRST_SHA_ONLY_V1')
  self.assertEqual((R['video_id'],R['original_video_cues']),('5NvtBlmt93Y',1481))
  self.assertEqual((R['segment_id'],R['first_cue'],R['last_cue'],R['reviewed_segment_cues']),('B0005',481,600,120))
  for k in ('source_sha256','segment_manifest_sha256','prior_b0004_packet_sha256_unchanged','prior_first_480_dispositions_sha256_unchanged','b0005_packet_sha256','b0005_120_dispositions_sha256','seam_475_485_sha256','seam_592_605_sha256'):
   self.assertRegex(R[k],r'^[a-f0-9]{64}$')
 def test_02_prior_records_same_sha(self):
  self.assertEqual(R['source_sha256'],'638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d')
  self.assertEqual(R['prior_b0004_packet_sha256_unchanged'],'ddc63afd4314bfe36a29d70f8a3aa436f63571dea94689bf991a602c4ecda5d9')
  self.assertEqual(R['prior_first_480_dispositions_sha256_unchanged'],'7892b0df7a8b6f6f3559194ae0ad3cf13710c1d1167ee94fdf580b61e3167ab3')
 def test_03_provisional_not_final_counts(self):
  self.assertEqual(R['combined_first_600_cues'],480+120)
  self.assertEqual(R['new_provisional_occurrence_atoms'],27)
  self.assertEqual(R['combined_first_600_provisional_occurrence_atoms'],110+27)
  self.assertEqual(R['cross_claim_provisional_relations'],21)
  self.assertFalse(R['independent_claim_recall_proven'])
 def test_04_asr_and_fact_open(self):
  self.assertEqual(R['asr_open_indices'],[489,515,517,522,532,534,556,593])
  self.assertEqual(R['combined_first_600_asr_open_cues'],20+len(R['asr_open_indices']))
  self.assertEqual(R['independent_external_fact_and_applicability_open'],10)
  self.assertEqual(R['prior_b0004_fact_checks_open_unchanged'],8)
  self.assertEqual(R['prior_finance_rule_open_unchanged'],12)
 def test_05_misleading_financial_claims_not_promoted(self):
  self.assertEqual(R['samsung_2026_q3_operating_profit_trillion_won'],107.4)
  self.assertEqual(R['samsung_2026_q3_reported_net_profit_trillion_won'],75.13)
  self.assertFalse(R['speaker_300trillion_net_profit_realized_period_verified'])
  self.assertFalse(R['one_to_three_year_high_success_probability_verified'])
  self.assertFalse(R['food_exports_linear_earnings_verified'])
  self.assertTrue(R['book_third_principle_toc_verified'])
  self.assertFalse(R['book_full_chapter_verified'])
 def test_06_chat_approval_and_owner_release_blocked(self):
  self.assertEqual(R['v123_final_passed_segments'],0)
  self.assertEqual(R['formally_approved_knowledge_atoms'],0)
  for k in ('knowledge_export_allowed','owner_operational_db_verified','personal_advisory_e2e_passed','p0_go'):
   self.assertFalse(R[k])
  self.assertEqual(R['status'],'B0005_120_CUE_SOURCE_REVIEW_CROSSCHECKED_ASR_FACT_OPEN_V123_HOLD')
if __name__=='__main__': unittest.main(verbosity=2)
