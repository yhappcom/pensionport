"""Integration of pinned 40-window official extracts into live V5 advisory responses."""
from __future__ import annotations
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ire.v5 import first_five_40_retrieval_bridge as bridge
from ire.v5 import advisory_answer_pipeline as p3
from ire.v5.first_five_40_official_replay_approval_gate import ApprovalGateError

ROOT=Path(__file__).resolve().parents[3]


class First40RetrievalTests(unittest.TestCase):
    def test_catalog_nine_pinned_educational_context_nodes(self):
        nodes=bridge.load_catalog(ROOT)
        self.assertEqual(len(nodes),9)
        self.assertEqual({x['knowledge_id'] for x in nodes},set(bridge.REVIEWED_SOURCE_BINDINGS))
        for node in nodes:
            self.assertTrue(node['source_content_replayed'])
            self.assertFalse(node['independent_knowledge_approved'])
            self.assertFalse(node['speaker_whole_claim_fact_approved'])
            self.assertFalse(node['personal_advice_approved'])
            self.assertFalse(node['formal_master_merged'])
            self.assertTrue(node['official_extraction_evidence'])
            for src in node['official_extraction_evidence']:
                self.assertRegex(src['pinned_sha256'],r'^[0-9a-f]{64}$')
                self.assertTrue(src['official_url'].startswith('https://'))
                self.assertIn('NOT_GOVERNMENT_SIGNED',src['source_kind'])

    def test_nine_distinct_real_korean_questions_reach_appropriate_nodes(self):
        receipt=bridge.audit(ROOT)
        self.assertEqual(receipt['education_candidates_connected'],9)
        self.assertEqual(receipt['sample_queries_verified'],9)
        self.assertEqual(receipt['official_source_snapshots_replayed'],15)
        self.assertTrue(receipt['personal_action_blocked'])
        self.assertFalse(receipt['master_116_modified'])
        self.assertEqual(receipt['externally_signed_narrow_facts_approved'],0)

    def test_personal_action_refused_even_when_matching_prior_pension_terms(self):
        a=bridge.retrieve(ROOT,'내 IRP 계좌 돈을 전량 매도해 줘')
        b=bridge.retrieve(ROOT,'연금 수익이 무조건 보장되나요',intent='guaranteed_return')
        self.assertEqual(a['decision'],'BLOCKED_PERSONAL_ACTION_OR_GUARANTEED_RETURN')
        self.assertEqual(b['decision'],'BLOCKED_PERSONAL_ACTION_OR_GUARANTEED_RETURN')
        self.assertEqual(a['items'],[])
        self.assertEqual(b['items'],[])

    def test_unrelated_question_does_not_hallucinate_official_knowledge(self):
        self.assertEqual(bridge.retrieve(ROOT,'오늘 영화관 주차장 티켓 판매')['match_count'],0)

    def test_pin_failure_is_not_silently_treated_as_no_match(self):
        with patch.object(bridge,'verify_official',side_effect=ApprovalGateError('OFFICIAL_EXTRACT_CONTENT_TAMPERED')):
            with self.assertRaisesRegex(ApprovalGateError,'OFFICIAL_EXTRACT_CONTENT_TAMPERED'):
                bridge.retrieve(ROOT,'ISA 만기 연금계좌 전환')

    def test_unexpected_official_source_connection_rejected(self):
        from ire.v5.first_five_40_official_replay_approval_gate import SCOPE
        real=bridge._json(ROOT/SCOPE)
        mutant=copy.deepcopy(real)
        mutant['knowledge_overlay'][0]['source_claim_ids']=['V5C0018']
        original_json=bridge._json
        def replace_one(path):
            if Path(path)==ROOT/SCOPE:return mutant
            return original_json(path)
        with patch.object(bridge,'_json',side_effect=replace_one):
            with self.assertRaises(ApprovalGateError):
                bridge.load_catalog(ROOT)

    def test_unsupported_request_parameters_fail_closed(self):
        with self.assertRaises(bridge.BridgeError):
            bridge.retrieve(ROOT,'')
        with self.assertRaises(bridge.BridgeError):
            bridge.retrieve(ROOT,'연금',intent='certified_personal_recommendation')
        with self.assertRaises(bridge.BridgeError):
            bridge.retrieve(ROOT,'연금',limit=20)

    def test_live_advisory_answer_includes_official_context_but_not_fact_approval(self):
        out=p3.answer(ROOT,'ISA 만기 연금계좌 전환 세액공제는 어떻게 되나요?')
        self.assertIn('first40_education_retrieval',out)
        side=out['first40_education_retrieval']
        self.assertTrue(any(x['knowledge_id'].endswith('ISA_MATURITY_TO_PENSION') for x in side['items']))
        self.assertIn('독립 승인 전',out['answer_text'])
        self.assertIn('공식 출처 추출본',out['answer_text'])
        self.assertEqual(side['independent_legal_fact_approval_count'],0)
        self.assertTrue(all(not f.startswith('V5-001-40-') for f in out['fact_ids']))
        self.assertFalse(out['current_law_fully_verified_in_this_run'])
        self.assertFalse(out['direct_order_or_personal_recommendation_approved'])

    def test_live_personal_trade_answer_does_not_include_claim_overlay(self):
        out=p3.answer(ROOT,'내 계좌에서 연금 ISA 전량 매도해 줘')
        self.assertEqual(out['first40_education_retrieval']['items'],[])
        self.assertTrue(out['personal_order_detected'])
        self.assertFalse(out['direct_order_or_personal_recommendation_approved'])

    def test_real_snapshots_are_not_claimed_as_official_digital_signatures(self):
        rows=bridge.retrieve(ROOT,'국민연금 연기연금 7.2%')['items']
        self.assertTrue(rows)
        for x in rows:
            for d in x['official_extraction_evidence']:
                self.assertIn('NOT_GOVERNMENT_SIGNED',d['source_kind'])
                self.assertEqual(d['observed_as_of'],'2026-11-06')


if __name__=='__main__':unittest.main()
