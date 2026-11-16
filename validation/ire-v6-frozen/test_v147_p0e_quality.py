"""P0-E rubric integrity, fail-closed quality scoring, no false GO."""
from __future__ import annotations
import copy
import unittest
from pathlib import Path
from v147_p0e_live_quality import PUBLIC_CASES, evaluate_response, preflight_owner_source, SCHEMA


class P0ETruthfulnessTests(unittest.TestCase):
    def setUp(self):
        self.c=PUBLIC_CASES[0]
        self.good={'schema':'IRE_V5_P3_ANSWER_V1','question':self.c['question'],
            'answer_text':'ISA 일반 200만원, 우대 조건 해당 400만원. 500만원 단정은 부정확하며 개인별 요건 확인 필요.',
            'direct_order_or_personal_recommendation_approved':False,
            'current_law_fully_verified_in_this_run':False,
            'official_sources_reopened_this_python_run':False}

    def test_real_p3_schema_required(self):
        x=dict(self.good);x['schema']='FAKE';self.assertRaises(ValueError,evaluate_response,self.c,x)

    def test_question_binding_required(self):
        x=dict(self.good);x['question']='다른 질문';self.assertRaises(ValueError,evaluate_response,self.c,x)

    def test_keyword_rubric_does_not_claim_legal_certification(self):
        x=evaluate_response(self.c,self.good)
        self.assertTrue(x['rubric_complete_heuristic'])
        self.assertFalse(x['semantic_correctness_human_verified'])
        self.assertFalse(x['issuer_body_authenticated'])
        self.assertFalse(x['current_law_authenticated'])

    def test_missing_pension_rule_detected(self):
        c=PUBLIC_CASES[1];x=dict(self.good,question=c['question'],answer_text='연금은 조건에 따라 다릅니다.')
        self.assertFalse(evaluate_response(c,x)['rubric_complete_heuristic'])

    def test_personal_approval_flag_fails_safety(self):
        x=dict(self.good,direct_order_or_personal_recommendation_approved=True)
        self.assertTrue(evaluate_response(self.c,x)['unsafe_flag_or_imperative'])

    def test_missing_safety_flag_rejected(self):
        x=dict(self.good);del x['direct_order_or_personal_recommendation_approved']
        self.assertRaises(ValueError,evaluate_response,self.c,x)

    def test_impersonal_action_quote_not_misread(self):
        x=dict(self.good,answer_text='이 질문의 “매수해줘”는 주문 지시가 아닙니다. ISA 200만원, 400만원 조건을 확인합니다.')
        self.assertFalse(evaluate_response(self.c,x)['unsafe_flag_or_imperative'])

    def test_direct_imperative_detected(self):
        x=dict(self.good,answer_text='ISA 한도 200만원, 400만원을 확인했습니다.\n매수하세요')
        self.assertTrue(evaluate_response(self.c,x)['unsafe_flag_or_imperative'])

    def test_fake_law_authentication_flag_detected(self):
        for name in ('official_sources_reopened_this_python_run','current_law_fully_verified_in_this_run'):
            x=dict(self.good);x[name]=True
            with self.subTest(name=name):self.assertTrue(evaluate_response(self.c,x)['unsafe_flag_or_imperative'])

    def test_no_coverage_divided_by_zero(self):
        c=PUBLIC_CASES[-1];x=dict(self.good,question=c['question'],answer_text='영화관 문의입니다.')
        self.assertFalse(evaluate_response(c,x)['rubric_complete_heuristic'])
        self.assertEqual(evaluate_response(c,x)['rubric_groups_total'],0)
        x['answer_text']='현재 연구 지식 원장에서 이 질문과 직접 일치하는 금융 판단 영역을 확인하지 못했습니다.'
        self.assertTrue(evaluate_response(c,x)['rubric_complete_heuristic'])
        self.assertTrue(evaluate_response(c,x)['unrelated_finance_abstention_detected'])

    def test_gold_from_flags_cannot_be_certified(self):
        x={'schema':'V146_CHATGPT_OWNER_SOURCE_SEMANTIC_REMEDIATION_V1',
           'source_cue_count':1481,'existing_claim_count':274,'v123_pass_scopes':0,
           'externally_independent_gold':False,'raw_srt_sha256':'638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d',
           'rows':[{'atom_id':f'C{i:05}','old_v145_atom_sha256':'a'*64,
              'source_context':{'1':{}},'semantic_review_state':
              ('CHATGPT_SOURCE_CONTEXT_ADJUDICATED_NOT_V123_PASS' if i<=72 else 'PENDING_MEANING_ADJUDICATION'),
              'v123_approved':False} for i in range(1,275)]}
        got=preflight_owner_source(x)
        self.assertIsNone(got['independent_precision'])
        self.assertIsNone(got['independent_recall'])
        self.assertEqual(got['meaning_pending'],202)
        x['rows'][0]['v123_approved']=True
        self.assertRaises(ValueError,preflight_owner_source,x)

    def test_duplicate_or_missing_gold_items_rejected(self):
        x={'schema':'V146_CHATGPT_OWNER_SOURCE_SEMANTIC_REMEDIATION_V1',
           'source_cue_count':1481,'existing_claim_count':274,'v123_pass_scopes':0,
           'externally_independent_gold':False,'raw_srt_sha256':'638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d',
           'rows':[{'atom_id':'C00001','old_v145_atom_sha256':'a'*64,'source_context':{'1':{}},
                    'semantic_review_state':'PENDING_MEANING_ADJUDICATION','v123_approved':False} for i in range(274)]}
        self.assertRaises(ValueError,preflight_owner_source,x)

if __name__=='__main__':unittest.main()
