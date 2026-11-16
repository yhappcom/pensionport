"""Public synthetic SHA-only control; no user private SRT; no semantic gold."""
import json,unittest
from pathlib import Path
R=json.loads((Path(__file__).parent/'V137_B0006_SOURCE_FIRST_SHA_ONLY.json').read_text('utf-8'))
class V137PublicSourceCustodyAndNonPromotion(unittest.TestCase):
 def test_01_identity_and_bound_scope(self):
  self.assertEqual(R['schema'],'IRE_V137_B0006_REAL_SOURCE_FIRST_SHA_ONLY_V1')
  self.assertEqual(R['source_sha256'],'638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d')
  self.assertEqual(R['video_id'],'5NvtBlmt93Y')
  self.assertEqual((R['original_video_cues'],R['segment_id'],R['first_cue'],R['last_cue'],R['reviewed_segment_cues']),(1481,'B0006',601,720,120))
  self.assertEqual(R['segment_manifest_sha256'],'4b9b7d3014b3df4057dad9ca1a7a692dc3b250f6fc8ed30fe859c6ab274c8663')
 def test_02_review_receipts_not_claim_recall(self):
  for key in ('b0006_packet_sha256','b0006_dispositions_sha256','prior_first_600_dispositions_sha256_unchanged','seam_592_605_sha256','seam_714_726_sha256'):
   self.assertRegex(R[key],r'^[0-9a-f]{64}$')
  self.assertEqual(len(R['prior_b0001_b0005_packets_sha256_unchanged']),5)
  self.assertEqual(R['prior_b0001_b0005_packets_sha256_unchanged'][-1], 'e1b6505a6fe2249029d04996e46bfb02fe5e2142d088fd631d5f4435559a851f')
  self.assertEqual(R['first_720_reviewed_cues'],600+120)
  self.assertEqual(R['new_provisional_occurrence_atoms'],28)
  self.assertEqual(R['first_720_provisional_occurrence_atoms'],137+28)
  self.assertEqual(R['provisional_cross_claim_relations'],27)
  self.assertFalse(R['independent_complete_claim_recall_proven'])
 def test_03_uncertainty_explicit_and_old_open_unchanged(self):
  self.assertEqual(R['asr_open_indices'],[622,631,643,665,669,672,682,692,698,700,717])
  self.assertEqual(R['first_720_asr_open_cues'],28+len(R['asr_open_indices']))
  self.assertEqual(R['new_external_fact_applicability_open'],12)
  self.assertEqual(R['prior_b0005_external_fact_open_unchanged'],10)
  self.assertEqual(R['prior_finance_rule_open_unchanged'],12)
  self.assertEqual(R['local_private_negative_controls_blocked'],7)
 def test_04_no_automatic_cyclical_or_semiconductor_promotion(self):
  for key in ('all_chinese_shipyards_failed_supported','three_sole_semiconductor_manufacturers_supported','cyclical_booms_inevitable_supported','distressed_stock_buy_always_safe','sector_recovery_guarantees_shareholder_return'):
   self.assertFalse(R[key],key)
  self.assertTrue(R['external_oecd_shipbuilding_data_observed'])
  self.assertTrue(R['external_2026_dram_market_data_observed'])
  self.assertFalse(R['external_finance_applicability_approved'])
 def test_05_owner_and_audio_release_rejected(self):
  self.assertEqual(R['v123_final_passed_segments'],0)
  self.assertEqual(R['formal_knowledge_published'],0)
  for key in ('original_audio_verified','knowledge_export_allowed','operational_db_owner_attested','personal_advisory_e2e_passed','p0_go'):
   self.assertFalse(R[key],key)
  self.assertEqual(R['status'],'B0006_120_SOURCE_FIRST_CUE_DISPOSITIONS_CROSSCHECKED_ASR_FACT_OPEN_V123_HOLD')
if __name__=='__main__':unittest.main(verbosity=2)
