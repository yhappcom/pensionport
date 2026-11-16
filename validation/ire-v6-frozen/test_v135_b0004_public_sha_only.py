"""V135 public SHA-only controls. Private SRT/cue table NOT contained here.
Passing this test proves metadata consistency, NOT independent claim recall.
"""
import json,unittest,re
from pathlib import Path
R=json.loads((Path(__file__).parent/'V135_B0004_SOURCE_FIRST_SHA_ONLY.json').read_text('utf-8'))
class V135B0004RealSourcePublicReceipt(unittest.TestCase):
 def test_01_source_and_scope(self):
  self.assertEqual(R['schema'],'IRE_V135_B0004_REAL_SOURCE_FIRST_SHA_ONLY_V1')
  self.assertEqual(R['video_id'],'5NvtBlmt93Y')
  self.assertEqual(R['total_original_cues'],1481)
  self.assertEqual((R['segment_id'],R['first_cue'],R['last_cue'],R['reviewed_cue_count']),('B0004',361,480,120))
  for name in ('source_sha256','segment_manifest_sha256','b0004_packet_sha256','combined_first_480_dispositions_sha256','prior_first_360_dispositions_sha256','seam_358_370_sha256','seam_475_485_sha256'):
   self.assertRegex(R[name],r'^[0-9a-f]{64}$')
 def test_02_ledger_counts_are_occurrences_not_gold(self):
  self.assertEqual(R['new_provisional_occurrence_atoms'],33)
  self.assertEqual(R['first_480_provisional_occurrence_atoms'],77+33)
  self.assertEqual(R['first_480_reviewed_cues'],360+120)
  self.assertTrue(R['provisional_duplicates_crosslinked_not_finally_merged'])
  self.assertFalse(R['all_video_atomic_truth_independently_certified'])
 def test_03_unresolved_asr_not_closed(self):
  self.assertEqual(R['asr_open_indices'],[361,390,399,407,412,417,429,456,459,469])
  self.assertEqual(R['first_480_open_asr_count'],10+len(R['asr_open_indices']))
  self.assertEqual(R['independent_fact_finance_checks_open'],8)
  self.assertEqual(R['remaining_prior_finance_open'],12)
  self.assertEqual(R['b0003_independent_fact_finance_open_unchanged'],8)
 def test_04_hypothetical_revenue_not_profit(self):
  self.assertEqual(R['hypothetical_40k_times_30_won'],40000*30)
  self.assertFalse(R['room_rate_asr_and_time_unit_verified'])
 def test_05_previous_three_packets_are_sha_only_and_fixed(self):
  self.assertEqual(R['prior_b0001_b0002_b0003_packet_sha256'],[
   'e06cf5d0bcb0473b88acef8739890eb21b8e5061cce37eb709ab6ccd45f2847e',
   '47ce100d1be67ff0a37233cd1361e635824ab829362fbf05d5b4e15f6ff36d1c',
   'ef9ecf9166252f946a40c7e0b2d62d244876cb942aff9419cb638988aa72f16a'])
  self.assertEqual(R['prior_first_360_dispositions_sha256'],'5dfedc3a4c28b2e73d00229371243a61983c8ee281030edbbafb1055f02f347f')
 def test_06_book_table_of_contents_not_full_page_approval(self):
  self.assertTrue(R['two_book_chapters_confirmed_by_publisher_toc'])
  self.assertFalse(R['primary_book_chapter_text_independently_verified'])
 def test_07_all_operational_release_gates_fail_closed(self):
  self.assertEqual(R['v123_final_passed_segments'],0)
  self.assertEqual(R['formally_approved_knowledge_atoms'],0)
  for name in ('knowledge_export_allowed','personal_advisory_e2e_passed','owner_operational_db_proven','p0_go'):
   self.assertFalse(R[name])
  self.assertEqual(R['status'],'B0004_120_SOURCE_CUE_DISPOSITIONS_STRUCTURALLY_AUDITED_ASR_OPEN_V123_HOLD')
if __name__=='__main__':unittest.main(verbosity=2)
