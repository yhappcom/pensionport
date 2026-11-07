"""Regression of #1-#5 real-original cue-provenance bridge, not a blind financial exam."""
from __future__ import annotations
import unittest
from pathlib import Path
from ire.v5 import first_five_advisory_bridge as bridge
from ire.v5 import advisory60

ROOT = Path(__file__).resolve().parents[3]

class FirstFiveBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = bridge.load(ROOT)
        cls.policy = advisory60.load_policy(ROOT)

    def test_45_provisional_items_and_b04_links(self):
        self.assertEqual(len(self.index),45)
        self.assertEqual({x['evidence_id'] for x in self.index},
                         {f'F{i:02d}' for i in range(1,26)}|
                         {f'S{i:02d}' for i in range(1,21)})
        self.assertEqual({x['prior_legacy_claim_id'] for x in self.index if x['video_number']==3}, {'GOMHEE-C64'})
        self.assertEqual({x['prior_legacy_claim_id'] for x in self.index if x['video_number']==4}, {'GOMHEE-C63'})
        self.assertEqual({x['prior_legacy_claim_id'] for x in self.index if x['video_number']==5}, {'GOMHEE-C62'})
        self.assertTrue(all(x['prior_legacy_claim_id'] is None for x in self.index if x['video_number']<3))
        self.assertTrue(all(not x['financial_fact_approved'] and not x['personal_action_approved'] for x in self.index))

    def test_semantic_retrieval_has_video_cue_and_constraints(self):
        cases = {
            'CMA 위험과 예금자보호 비교':'F08',
            '퇴직금 IRP 증권사 이전 비용':'F11',
            '재직 업종 ETF 투자 위험':'F23',
            '연금 1500만원 인출상한과 세금':'F03',
            'TDF 2060 사회초년생 연금저축':'S18',
        }
        for q, ref in cases.items():
            with self.subTest(q=q):
                docs=bridge.retrieve(self.index,q)
                row=next(x for x in docs if x['evidence_id']==ref)
                self.assertEqual(len(row['source_span_sha256']),64)
                self.assertTrue(row['critical_limit'])
                self.assertFalse(row['current_law_verified_by_ci'])
                self.assertFalse(row['personal_action_approved'])

    def test_advisory60_output_exposes_original_cue_evidence_without_approval(self):
        for question, expected in [
            ('CMA 위험과 예금자보호 비교','F08'),
            ('퇴직금 IRP 증권사 이전 비용','F11'),
            ('손실 종목 보유','F18'),
            ('재직 업종 ETF 투자 위험','F23'),
            ('추납 1800만원과 연금저축 차이','F01'),
        ]:
            with self.subTest(question=question):
                reply=advisory60.resolve(self.policy,question)
                matched=reply['first_five_original_source_evidence']
                self.assertIn(expected,[x['evidence_id'] for x in matched])
                self.assertFalse(reply['personal_action_approved'])
                self.assertFalse(reply['current_financial_rule_live_verified'])
                self.assertFalse(reply['trade_or_amount_recommended'])
                self.assertTrue(reply['post_60_claim_provisional_links_only'])

    def test_no_relevance_no_fake_reference(self):
        self.assertEqual(bridge.retrieve(self.index,'내일 영화관 상영 스케줄'),[])
        reply=advisory60.resolve(self.policy,'내일 영화관 상영 스케줄')
        self.assertEqual(reply['decision'],'NO_SUPPORTED_RESEARCH_ROUTE')
        self.assertEqual(reply['first_five_original_source_evidence'],[])

    def test_provisional_bridge_audit_not_full_research_release(self):
        a=bridge.audit(ROOT)
        self.assertEqual(a['hand_authored_query_scenarios'],15)
        self.assertEqual(a['source_windows_planned'],288)
        self.assertFalse(a['remaining_windows_semantic_complete'])
        self.assertEqual(a['approved_financial_facts'],0)
        self.assertFalse(a['research_full_go'])

if __name__=='__main__': unittest.main()
