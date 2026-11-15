"""Public metadata-only CI: never claim this independently replays private SRT."""
import json,re,unittest
from pathlib import Path

DATA=Path(__file__).with_name('V133_B0002_SOURCE_FIRST_SHA_ONLY.json')
class V133RealB0002HashOnlyReceiptTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=json.loads(DATA.read_text(encoding='utf-8'))
 def test_01_full_original_cue_scope_not_auto_pass(self):
  r=self.r
  self.assertEqual(r['schema'],'IRE_V133_B0002_REAL_SOURCE_FIRST_CUE_AUDIT_SHA_ONLY_V1')
  self.assertEqual((r['scope_first_cue'],r['scope_last_cue'],r['cue_count_source_confirmed']),(121,240,120))
  self.assertEqual(r['explicit_chat_cue_dispositions_submitted'],120)
  self.assertFalse(r['b0002_semantic_completeness_independently_certified'])
 def test_02_composite_240_source_cue_census_pinned(self):
  r=self.r
  self.assertEqual(r['combined_1_to_240_explicit_cue_dispositions'],240)
  self.assertEqual(r['combined_1_to_240_provisional_atom_count'],43)
  self.assertEqual(r['combined_1_to_240_unresolved_cue_count'],7)
  self.assertEqual(r['b0001_audio_speaker_open'],111)
 def test_03_b0002_six_asr_open(self):
  r=self.r
  self.assertEqual(r['unresolved_asr_semantics_cue_indices'],[145,172,202,207,223,233])
  self.assertEqual(r['unresolved_asr_semantics_cues_count'],6)
  self.assertEqual(r['b0002_structural_cue_disposition_result'],'HOLD_OPEN_CUE_DISPOSITIONS')
 def test_04_book_historical_vs_current_scope_not_mixed(self):
  r=self.r
  for k in ('book_2007_vs_present_day_populations_not_equated',
      'patel_motel_vs_aahoa_hotel_ownership_not_equated',
      'family_unpaid_labor_vs_economic_cost_not_equated',
      'debt_maximum_loss_guarantee_rejected'):
   self.assertIs(r[k],True)
  self.assertEqual(r['independent_fact_and_financial_checks_open'],7)
 def test_05_privacy_and_sha_only_provenance(self):
  r=self.r
  self.assertEqual(r['video_id'],'5NvtBlmt93Y')
  self.assertEqual(r['source_sha256'],'638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d')
  for k in ('source_sha256','child_manifest_sha256','b0002_source_cue_disposition_sha256','b0002_review_packet_sha256','combined_1_to_240_cue_disposition_sha256','private_b0002_sha256'):
   self.assertRegex(r[k],r'^[0-9a-f]{64}$')
  self.assertEqual(len(r['b0002_to_b0003_237_245_cue_sha256']),9)
  self.assertTrue(all(re.fullmatch(r'[0-9a-f]{64}',s) for s in r['b0002_to_b0003_237_245_cue_sha256']))
  self.assertNotIn('original_text',r)
 def test_06_no_promotion_finance12_independent_db(self):
  r=self.r
  self.assertEqual(r['whole_video_v123_final_passed_segments'],0)
  self.assertEqual(r['all_video_research_knowledge_promoted'],0)
  self.assertEqual(r['finance_open_claims_other_video'],12)
  self.assertIs(r['actual_personal_advice_passed'],False)
  self.assertIs(r['owner_operational_db_independently_attested'],False)
  self.assertIs(r['b0002_to_b0003_investment_recommendation_approved'],False)
  self.assertIs(r['p0_go'],False)

if __name__=='__main__':unittest.main()
