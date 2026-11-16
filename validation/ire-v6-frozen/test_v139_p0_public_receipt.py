"""Public SHA-only P0 negative controls; no original SRT or final ChatGPT accuracy proof."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).parent
R=json.loads((ROOT/'V139_P0_PERFORMANCE_SHA_ONLY.json').read_text('utf-8'))
class V139MetadataCensusAndNoFalseGo(unittest.TestCase):
 def test_01_full_original_census_metadata(self):
  self.assertEqual(R['parent_video_id'],'5NvtBlmt93Y')
  self.assertEqual(R['parent_raw_srt_sha256'],'638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d')
  self.assertEqual(R['parent_total_original_cues'],1481)
  self.assertEqual(R['total_13_source_scopes_censused'],13)
  self.assertEqual(R['source_cue_sha_checked'],1481)
 def test_02_source_first_targeted_review_is_not_gold(self):
  self.assertEqual(R['p0_1_source_only_blind_targets_frozen'],46)
  self.assertEqual(R['p0_1_same_chat_selected_matched'],41)
  self.assertEqual(R['p0_1_same_chat_selected_partial'],3)
  self.assertEqual(R['p0_1_same_chat_selected_missing_or_unlinked'],2)
  self.assertEqual(41+3+2,46)
  self.assertRegex(R['p0_1_frozen_source_only_label_sha256'],r'^[0-9a-f]{64}$')
  self.assertFalse(R['p0_1_full_720_gold_adjudicated'])
  self.assertFalse(R['p0_1_external_independent_gold'])
  for x in ['p0_1_actual_tp','p0_1_actual_fp','p0_1_actual_fn','p0_1_precision','p0_1_recall','p0_1_high_risk_omission_rate']:
   self.assertIsNone(R[x],x)
  self.assertFalse(R['p0_1_pass'])
 def test_03_source_queue_without_fabricated_full_analysis(self):
  self.assertEqual(R['prev_provisional_cue_research'],720)
  self.assertEqual(R['prior_provisional_atomic_occurrences'],165)
  self.assertEqual(R['p0_2_new_unreviewed_final_semantic_cues'],761)
  self.assertEqual(R['p0_2_source_first_risk_cases'],16)
  self.assertRegex(R['p0_2_source_queue_sha256'],r'^[0-9a-f]{64}$')
  self.assertFalse(R['p0_2_new_full_atom_dispositions_complete'])
  self.assertFalse(R['p0_2_actual_one_invocation_13_segment_v128_replay_passed'])
  self.assertEqual(R['p0_2_all_13_v123_final_passed'],0)
  self.assertEqual(R['p0_2_atomic_knowledge_published'],0)
 def test_04_current_law_excerpt_not_personal_finance_approval(self):
  self.assertEqual(R['p0_3_fact_checked_example_questions'],8)
  self.assertEqual(R['p0_3_official_current_law_web_excerpt_cases'],2)
  self.assertEqual(R['p0_3_issuer_original_bytes_verified_cryptographically'],0)
  self.assertEqual(R['p0_3_real_v5_v23_current_advisory_end_to_end_runs'],0)
  self.assertFalse(R['p0_3_owner_operational_db_connected'])
  self.assertFalse(R['p0_3_personalized_investment_advice_approved'])
 def test_05_quality_gates_are_no_go_by_default(self):
  self.assertEqual(R['private_real_original_integrity_tests_passed'],8)
  self.assertEqual(R['public_synthetic_contract_tests_passed_locally'],10)
  self.assertFalse(R['analysis_model_processing_times_measured'])
  self.assertTrue(R['code_only_stage_timings_measured'])
  self.assertFalse(R['p0_go'])
if __name__=='__main__':unittest.main(verbosity=2)
