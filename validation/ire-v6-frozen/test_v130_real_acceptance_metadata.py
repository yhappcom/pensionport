"""V130 public-only acceptance nonpromotion guards (owner raw SRT not in repo)."""
import json
import re
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent

class V130SourceAndFinanceNonPromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=json.loads((HERE/'V130_ORIGINAL_SOURCE_SHA_ONLY.json').read_text(encoding='utf-8'))
        cls.v129=json.loads((HERE/'V129_REAL_ACCEPTANCE_SHA_ONLY.json').read_text(encoding='utf-8'))
        cls.policy=json.loads((HERE/'V125_ENGINE_FIRST_PORTFOLIO_DEFERRED_POLICY.json').read_text(encoding='utf-8'))

    def test_verified_13_source_and_12_context_boundaries_not_atom_recall(self):
        r=self.r
        self.assertEqual(r['real_original_cues'],1481)
        self.assertEqual(r['independently_rechecked_source_scope_sha_count'],13)
        self.assertTrue(r['all_13_private_V129_scope_text_shas_match_actual_original'])
        self.assertTrue(r['all_12_boundary_cue_shas_match_actual_original'])
        self.assertTrue(r['full_original_cue_index_census_no_missing_or_overlap'])
        self.assertEqual(r['actual_original_sha256'],self.v129['source_sha256'])
        self.assertEqual(r['chatgpt_v123_final_pass_segments'],0)
        self.assertEqual(r['chatgpt_v123_final_pass_claims'],0)

    def test_new_private_source_finding_not_silently_approved(self):
        r=self.r
        self.assertEqual(r['new_high_risk_original_cues'],[1151,1154])
        self.assertRegex(r['new_high_risk_cue_span_sha256'],r'^[a-f0-9]{64}$')
        self.assertTrue(r['new_high_risk_not_formally_adjudicated'])
        self.assertEqual(r['research_knowledge_published'],0)

    def test_unattested_operational_db_and_claim_specific_finance_held(self):
        r=self.r
        self.assertFalse(r['operator_inventory_owner_signed'])
        self.assertFalse(r['real_operational_v6_db_owner_identity_verified'])
        self.assertFalse(r['real_operational_knowledge_head_verified'])
        self.assertEqual(r['finance_open_claim_count'],12)
        self.assertFalse(r['claim_specific_20261116_original_issuer_bytes_authenticated'])

    def test_final_chat_and_qa_nonpromotion_phase_order(self):
        r=self.r
        self.assertFalse(r['real_verified_advisory_end_to_end'])
        self.assertFalse(r['p0_go'])
        self.assertFalse(r['new_video_research_staged'])
        self.assertFalse(r['portfolio_drive_visited'])
        self.assertFalse(self.policy['completed_engine'])
        self.assertFalse(self.policy['further_video_research_authorized'])
        self.assertFalse(self.policy['portfolio_integration_implementation_authorized'])

if __name__=='__main__':
    unittest.main()
