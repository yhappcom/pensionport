"""V129 live-owner case outcome: software regression over SHA-only public receipt.

This file contains no owner transcript, private ChatGPT memo, portfolio account
information, or copied official HTML. Failure to pass a genuine source review
must not be promoted to production finance knowledge.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from ire.v6.codec import ZERO_SHA
from ire.v6.errors import QualityNotProven
from v126_chat_approved_knowledge_store import PrivateKnowledgeStore
from v126_chat_research_answer_bridge import prepare_question_packet

class V129RealFourTrackNonpromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads((ROOT / "V129_REAL_ACCEPTANCE_SHA_ONLY.json").read_text(encoding="utf-8"))
        cls.policy = json.loads((ROOT / "V125_ENGINE_FIRST_PORTFOLIO_DEFERRED_POLICY.json").read_text(encoding="utf-8"))

    def test_all_1481_original_cues_reviewed_only_at_discourse_level(self):
        r=self.receipt
        self.assertEqual(r['original_cues'],1481)
        self.assertEqual(r['cue_source_first_discourse_reviewed'],1481)
        self.assertEqual(r['segment_count'],13)
        self.assertEqual(r['seam_source_context_checked'],12)
        self.assertEqual(r['chatgpt_meaning_clusters_diagnostic_not_atoms'],52)
        self.assertEqual(r['v123_formal_final_pass_segment_count'],0)
        self.assertFalse(r['engine_phase_completed'])
        self.assertEqual(r['acceptance_results']['single_turn_chatgpt_v123_13scope_actual_acceptance'],
                         'HOLD_0_OF_13_FINAL_PASSED')

    def test_real_V128_host_demands_actual_child_cases_and_did_not_publish(self):
        r=self.receipt
        self.assertTrue(r['v128_real_source_host_fail_closed'])
        self.assertEqual(r['v128_real_source_callback_runs'],1)
        self.assertIn('V128_HOST_REVIEW_CHILD_PACKET_MISSING_OR_SCHEMA',r['v128_real_source_error_code'])
        self.assertEqual(r['v128_real_source_published_knowledge_count'],0)

    def test_isolated_db_is_not_owner_operational_ledger(self):
        r=self.receipt
        self.assertFalse(r['real_owner_operational_db_found'])
        self.assertEqual(r['isolated_v1237_staging_head_sha256'],
                         'a24352d7068d1ab8e0e2a915f60ae8578d0bef8c2d10900f6840d6bd35ddb6a9')
        self.assertEqual(r['private_v1237_sha_manifest_members_rechecked'],15)
        self.assertEqual(r['acceptance_results']['owner_operational_db_vs_original'],
                         'HOLD_OWNER_OPERATING_DB_NOT_FOUND')

    def test_current_law_text_not_misrepresented_as_exact_issuer_response_bytes(self):
        r=self.receipt
        self.assertTrue(r['official_text_researched_asof_20261116'])
        self.assertFalse(r['official_exact_new_issuer_body_authentication_complete'])
        self.assertEqual(r['finance_open_count'],12)
        self.assertEqual(r['acceptance_results']['current_official_finance_text'],
                         'CONTEXT_CHECKED_12_CLAIM_SPECIFIC_OPEN')

    def test_empty_real_candidate_store_stops_qa_before_any_advice(self):
        with tempfile.TemporaryDirectory(prefix='v129_synthetic_private_db_') as d:
            db=PrivateKnowledgeStore(Path(d)/'private.db')
            self.assertEqual(db.audit()['head_sha256'],ZERO_SHA)
            self.assertEqual(db.audit()['active_claims'],0)
            q='ISA 만기 연금 전환 300만원 환급인가요? 현재 연구 지식으로 투자 조언을 해주세요.'
            with self.assertRaisesRegex(QualityNotProven,'NO_APPROVED_RESEARCH_CANDIDATES'):
                prepare_question_packet(db,q,selected_knowledge_ids=[],as_of='2026-11-16')
            self.assertEqual(db.audit()['head_sha256'],ZERO_SHA)

    def test_negative_hold_cannot_be_promoted_by_previously_green_synthetic_ci(self):
        r=self.receipt
        self.assertTrue(r['investment_qa_synthetic_engine_positive_previous_ci'])
        self.assertEqual(r['real_knowledge_qa_accepted_count'],0)
        self.assertFalse(r['real_advisory_end_to_end_pass'])
        self.assertFalse(r['p0_go'])
        self.assertFalse(self.policy['completed_engine'])

    def test_all_private_source_proof_identifiers_are_only_sha_pins(self):
        r=self.receipt
        self.assertRegex(r['source_sha256'],r'^[a-f0-9]{64}$')
        for k,v in r['private_reviews_sha256'].items():
            with self.subTest(source=k):
                self.assertRegex(v,r'^[a-f0-9]{64}$')
        self.assertEqual(len(r['private_reviews_sha256']),5)

    def test_phase_R_and_P_remain_blocked(self):
        r=self.receipt
        self.assertFalse(r['new_video_research_expanded'])
        self.assertFalse(r['portfolio_drive_integration_executed'])
        self.assertFalse(self.policy['further_video_research_authorized'])
        self.assertFalse(self.policy['portfolio_integration_implementation_authorized'])
        self.assertFalse(self.policy['p0_go'])

if __name__=='__main__':
    unittest.main()
