"""Public synthetic/metadata controls: no user SRT and NO independent semantic approval."""
import json, unittest
from pathlib import Path
ROOT=Path(__file__).parent
R=json.loads((ROOT/'V134_B0003_SOURCE_FIRST_SHA_ONLY.json').read_text())
class V134B0003PublicCensusNonpromotion(unittest.TestCase):
 def test_01_only_owner_bound_hash_metadata(self):
  self.assertEqual(R['schema'],'IRE_V134_B0003_REAL_SOURCE_FIRST_SHA_ONLY_V1')
  self.assertRegex(R['source_sha256'],r'^[0-9a-f]{64}$')
  self.assertEqual(R['total_original_cues'],1481)
  self.assertEqual(R['video_id'],'5NvtBlmt93Y')
 def test_02_scope_and_atom_counts_not_certification(self):
  self.assertEqual((R['first_cue'],R['last_cue'],R['reviewed_cue_count']),(241,360,120))
  self.assertEqual(R['provisional_atoms_in_segment'],34)
  self.assertEqual(R['combined_first_360_cues'],360)
  self.assertEqual(R['combined_first_360_provisional_atoms'],77)
  self.assertFalse(R['all_video_atomic_truth_independently_certified'])
 def test_03_asr_uncertainties_are_explicit(self):
  self.assertEqual(R['asr_unresolved_indices'],[262,289,307])
  self.assertEqual(R['combined_first_360_open_cues'],10)
  self.assertEqual(R['status'],'B0003_120_SOURCE_CUE_DISPOSITIONS_AUDITED_ASR_OPEN_V123_HOLD')
 def test_04_finance_number_contradiction_detected(self):
  self.assertEqual(R['monthly_salary_300man_annualized_won'],3_000_000*12)
  self.assertEqual(R['source_says_annual_won'],40_000_000)
  self.assertEqual(R['difference_won'],4_000_000)
  self.assertEqual(R['math_800m_times_5_percent_won'],800_000_000*5//100)
  self.assertEqual(R['simple_inverse_annual_36m_at_5_percent_won'],720_000_000)
  self.assertTrue(R['finance_math_contradiction_not_silently_closed'])
 def test_05_no_hypothetical_yield_or_salary_valuation_promotion(self):
  self.assertFalse(R['five_percent_dividend_or_total_return_guaranteed'])
  self.assertFalse(R['salary_as_invested_800m_personal_decision_approved'])
  self.assertTrue(R['do_not_auto_recommend_youtube_or_resignation'])
 def test_06_source_and_old_review_digests_are_only_sha_pins(self):
  for x in ('b0001_review_packet_sha256_unchanged','b0002_review_packet_sha256_unchanged',
            'b0003_review_packet_sha256','b0003_cue_dispositions_sha256',
            'private_b0003_review_sha256','combined_first_360_dispositions_sha256',
            'cross_seam_237_245_sha256','cross_seam_358_370_sha256'):
   self.assertRegex(R[x],r'^[0-9a-f]{64}$')
 def test_07_independent_finance_and_book_remain_open(self):
  self.assertEqual(R['independent_fact_and_finance_cases_open'],8)
  self.assertFalse(R['independent_primary_book_page_verified'])
  self.assertEqual(R['remaining_prior_finance_open'],12)
  self.assertFalse(R['direct_owner_operational_db_proven'])
 def test_08_v123_atomic_publish_and_advisory_still_blocked(self):
  self.assertEqual(R['v123_final_passed_segments'],0)
  self.assertEqual(R['formally_approved_knowledge_atoms'],0)
  self.assertFalse(R['knowledge_export_allowed'])
  self.assertFalse(R['personal_advisory_e2e_passed'])
  self.assertFalse(R['p0_go'])

if __name__=='__main__':unittest.main(verbosity=2)
