"""V24 user-style finance questions: NOT an independent human-blind gold set.

These tests are fixed authored financial question/answer checks, with synthetic
source-first V22 data. A separate full-repo smoke runs actual V5 P3 and P2.
"""
from __future__ import annotations

import copy
from pathlib import Path
import unittest
from unittest.mock import patch

from ire.v6.errors import InvalidInput
from ire.v6.tests import test_current_law_reassessment as _law_tests
from ire.v6.advisory_decision_utility import evaluate_current_question
from ire.v6.tests.test_stage_repair import fixture,atom,exchange
from ire.v6.codec import sha256


class CurrentDecisionUtilityTests(unittest.TestCase):
    def setUp(self):
        old=_law_tests.CurrentLawReassessmentTests('test_current_law_after_video_publication_is_valid_for_current_advice')
        old.setUp()
        self.source=old.source
        self.exchange=old.ex
        self.evidence=old.evidence
        self.decisions=old.decisions
        self.root=Path('/no-private-root')
        self.q='IRP 중도인출은 전혀 불가능하고, ETF 매매차익은 모두 15.4% 과세되나요?'

    def _args(self,question=None,selected=None,scenario=None,decisions=None,source=None,ex=None,evidence=None):
        return {'root':self.root,'question':question or self.q,
                'source':self.source if source is None else source,
                'exchange':self.exchange if ex is None else ex,
                'current_as_of':'2026-11-10',
                'primary_evidence':self.evidence if evidence is None else evidence,
                'chat_decisions':self.decisions if decisions is None else decisions,
                'selected_claim_ids':['C00001','C00002'] if selected is None else selected,
                'scenario':scenario}

    def _p3(self,root,question,scenario):
        return {'schema':'IRE_V5_P3_ANSWER_V1','question':question,
                'answer_text':'2026-11-05 채팅 검토 기준 과거 법률 스냅샷입니다.',
                'fact_ids':['OLD_20261105'],'domain_candidates':['PENSION_TAX'],
                'direct_order_or_personal_recommendation_approved':False}

    def _retirement(self):
        return {'kind':'RETIREMENT_GAP','monthly_pension_krw':1200000,
                'other_monthly_income_krw':300000,
                'options':[{'id':'A','monthly_expense_krw':3000000}]}

    def _returns(self):
        return {'kind':'ETF_TOTAL_RETURN',
                'options':[{'id':'A','initial_value_krw':10000000,
                            'ending_market_value_krw':11000000,
                            'cash_distributions_krw':200000,
                            'separately_paid_fees_krw':50000}]}

    def _math(self,root,question,scenario):
        if scenario['kind']=='RETIREMENT_GAP':
            return {'schema':'IRE_V5_P2_CONDITIONAL_COMPARISON_V1',
                    'question':question,'kind':scenario['kind'],
                    'recommendation_status':'TRADEOFF_ONLY_NOT_PERSONAL_ACTION',
                    'personalized_trade_authorized':False,'future_returns_guaranteed':False,
                    'default_win_or_trade_instruction':None,
                    'results':[{'option_id':'A','monthly_unfunded_spending_krw':1500000,
                                'annual_unfunded_spending_krw':18000000,
                                'retirement_capital_required':None}],
                    'required_unpriced_factors':['물가상승','의료지출']}
        if scenario['kind']=='ETF_TOTAL_RETURN':
            return {'schema':'IRE_V5_P2_CONDITIONAL_COMPARISON_V1',
                    'question':question,'kind':scenario['kind'],
                    'recommendation_status':'TRADEOFF_ONLY_NOT_PERSONAL_ACTION',
                    'personalized_trade_authorized':False,'future_returns_guaranteed':False,
                    'default_win_or_trade_instruction':None,
                    'results':[{'option_id':'A','net_total_return_krw_pre_tax':1150000,
                                'net_total_return_pct_pre_tax':11.5,
                                'cash_distribution_not_guaranteed_profit':True}],
                    'required_unpriced_factors':['ETF 유형별 세금','외부 비용']}
        raise AssertionError('Unknown scenario fixture')

    def call(self,**kw):
        args=self._args(**kw)
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer',side_effect=self._p3) as v5, \
             patch('ire.v6.advisory_decision_utility._v5_p2_compare',side_effect=self._math) as v5p2:
            result=evaluate_current_question(**args)
            v5.assert_called_once()
            if not args['scenario'] or args['scenario']['kind']=='ISA_TRANSFER' or '해줘' in args['question']:
                v5p2.assert_not_called()
            return result

    def test_actual_style_irp_and_etf_question_leads_with_decision(self):
        out=self.call()
        self.assertIn('법정 중도인출 사유',out['direct_lead'])
        self.assertIn('모든 ETF 매매차익',out['direct_lead'])
        self.assertEqual(out['identified_question_topics'],['IRP','ETF'])
        self.assertIn('regulation.krx.co.kr',out['answer_text'])
        self.assertNotIn('2026-11-05 채팅 검토 기준',out['answer_text'])
        self.assertTrue(out['question_specific_direct_answer'])
        self.assertFalse(out['p0_go'])

    def test_irp_legal_exception_is_not_absolute_prohibition(self):
        out=self.call(question='IRP 중도인출은 무조건 불가능한가요?',selected=['C00001'])
        self.assertIn('법정 중도인출 사유',out['direct_lead'])
        self.assertIn('law.go.kr',out['answer_text'])

    def test_etf_domestic_equity_scope_not_blanket_tax(self):
        out=self.call(question='국내주식형 ETF 매매차익도 모두 15.4% 과세되나요?',selected=['C00002'])
        self.assertIn('동일하게 15.4%',out['direct_lead'])
        self.assertIn('국내주식형과 기타 ETF',out['direct_lead'])

    def test_irp_source_cannot_be_falsely_used_for_isa(self):
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer') as mocked,self.assertRaisesRegex(InvalidInput,'TOPIC_MISMATCH_ISA'):
            evaluate_current_question(**self._args(question='ISA 만기자금을 연금계좌에 옮기면?',selected=['C00001']))
        mocked.assert_not_called()

    def test_investment_order_requests_explicitly_refused_no_math(self):
        q='내 IRP를 지금 모두 매도해줘'
        out=self.call(question=q,selected=['C00001'],scenario=self._retirement())
        self.assertIn('대신 실행할 수 없습니다',out['direct_lead'])
        self.assertFalse(out['trade_or_transfer_execution_allowed'])
        self.assertFalse(out['has_validated_illustrative_math'])

    def test_retirement_gap_question_includes_validated_actual_math(self):
        out=self.call(question='IRP에서 나올 연금을 고려할 때 은퇴 월 생활비 부족액은?',
                      selected=['C00001'],scenario=self._retirement())
        self.assertTrue(out['has_validated_illustrative_math'])
        self.assertIn('1,500,000원',out['answer_text'])
        self.assertIn('18,000,000원',out['answer_text'])
        self.assertIn('필요 투자원금은 아직 계산할 수 없습니다',out['answer_text'])
        self.assertIsNotNone(out['validated_p2_math_sha256'])

    def test_etf_total_return_separates_price_distribution_and_tax(self):
        out=self.call(question='ETF A의 가격과 분배금으로 세전 총수익을 계산해 주세요.',
                      selected=['C00002'],scenario=self._returns())
        self.assertTrue(out['has_validated_illustrative_math'])
        self.assertIn('1,150,000원',out['answer_text'])
        self.assertIn('11.50%',out['answer_text'])
        self.assertIn('ETF 유형별 세금',out['answer_text'])

    def test_dishonest_p2_net_gain_is_blocked(self):
        q='ETF A 세전 총수익을 계산해 주세요.'
        bad=self._math(None,q,self._returns())
        bad['results'][0]['net_total_return_krw_pre_tax']=99999999
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer',side_effect=self._p3), \
             patch('ire.v6.advisory_decision_utility._v5_p2_compare',return_value=bad), \
             self.assertRaisesRegex(InvalidInput,'MATH_RECOMPUTE_MISMATCH'):
            evaluate_current_question(**self._args(question=q,selected=['C00002'],scenario=self._returns()))

    def test_p2_false_trade_authorization_is_blocked(self):
        q='IRP 은퇴 생활비 월 부족액은?'
        bad=self._math(None,q,self._retirement())
        bad['personalized_trade_authorized']=True
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer',side_effect=self._p3), \
             patch('ire.v6.advisory_decision_utility._v5_p2_compare',return_value=bad), \
             self.assertRaisesRegex(InvalidInput,'P2_OUTPUT_NOT_SAFE'):
            evaluate_current_question(**self._args(question=q,selected=['C00001'],scenario=self._retirement()))

    def test_unknown_current_fact_stays_open(self):
        d=copy.deepcopy(self.decisions)
        d[0]['classification']='CURRENT_FACT_OR_APPLICABILITY_UNKNOWN'
        d[0]['rule_ids']=[]
        d[0]['missing_conditions']=['개인 조건 확인']
        out=self.call(question='IRP 중도인출은 무조건 가능한가요?',selected=['C00001'],decisions=d)
        self.assertEqual(out['selected_unresolved_claim_ids'],['C00001'])
        self.assertIn('확인 보류',out['answer_text'])
        self.assertFalse(out['personal_trade_or_tax_approval'])

    def test_unknown_question_without_financial_scope_rejected(self):
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer') as mocked,self.assertRaises(InvalidInput):
            evaluate_current_question(**self._args(question='오늘 영화 상영 시간은?',selected=['C00001']))
        mocked.assert_not_called()

    def test_asof_and_evidence_still_conserved(self):
        out=self.call()
        self.assertEqual(out['current_as_of'],'2026-11-10')
        self.assertFalse(out['official_primary_body_authenticity_verified'])
        self.assertFalse(out['independent_answer_truth_or_decision_usefulness_certified'])
        self.assertFalse(out['external_human_gold'])

    def test_current_isa_tax_scenario_is_quarantined_not_rebranded(self):
        source=fixture(['ISA 만기자금은 60일 이내 연금계좌로 전환해야 추가 세액공제 대상이다.'])
        ex=exchange(source,[atom(source,'C00001',[1],[1],
             'ISA 만기 자금을 60일 내 연금계좌에 이전해야 세액공제 한도 확대를 검토할 수 있다.')])
        ex['atoms'][0]['condition_cue_indices']=[1]
        rule={'rule_id':'NTS_ISA_60D','source_url':'https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7885',
              'effective_from':'2026-01-01','effective_to':None,'retrieved_on':'2026-11-10',
              'excerpt':'ISA 만기 후 60일 이내 연금계좌로 납입한 금액을 추가 납입으로 본다.',
              'scope_note':'계좌 만기일, 실제 납입일, 세액공제 적용 대상 조건은 별도 확인 필요함',
              'document_body_sha256':None}
        rule['excerpt_sha256']=sha256(rule['excerpt'].encode())
        statement=ex['atoms'][0]['proposition']
        d={'claim_id':'C00001','proposition_sha256':sha256(statement.encode()),
           'classification':'CURRENT_GENERAL_RULE_CONSISTENT_CONDITIONAL',
           'rule_ids':['NTS_ISA_60D'],'reason':'만기일 이후 60일 내 이전에 관한 일반 규정이며 개인 계좌 요건은 확인되지 않았다.',
           'missing_conditions':['가입자 소득 및 결정세액','실제 만기 및 이체일'],
           'reviewer':'CHATGPT_CURRENT_TURN','reviewed_as_of':'2026-11-10'}
        q='ISA 만기자금 연금계좌 이전 세액공제 혜택을 계산해 주세요.'
        isa={'kind':'ISA_TRANSFER','assumed_income_tax_credit_rate':0.15,
             'options':[{'id':'A','transfer_krw':30000000,'days_after_isa_expiry':30}]}
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer',side_effect=self._p3) as v5, \
             patch('ire.v6.advisory_decision_utility._v5_p2_compare') as p2:
            out=evaluate_current_question(**self._args(question=q,selected=['C00001'],scenario=isa,
                source=source,ex=ex,evidence=[rule],decisions=[d]))
            self.assertIsNone(v5.call_args.args[2])
            p2.assert_not_called()
        self.assertTrue(out['isa_tax_calculation_quarantined_pending_current_evidence'])
        self.assertIn('60일 이내',out['direct_lead'])
        self.assertIn('세액공제 금액 계산은',out['answer_text'])
        self.assertFalse(out['has_validated_illustrative_math'])

    def test_real_v5_and_p2_math_on_full_canonical_checkout(self):
        root=Path(__file__).resolve().parents[3]
        if not (root/'ire/v5/legacy_consolidation/master_index_20261105.json').is_file():
            self.skipTest('real V5 full root necessary; synthetic-only in partial private lab')
        q='IRP 연금을 고려해 은퇴 생활비 월 부족액을 계산해 주세요.'
        a=self._args(question=q,selected=['C00001'],scenario=self._retirement())
        a['root']=root
        out=evaluate_current_question(**a)
        self.assertTrue(out['v5_p3_executed'])
        self.assertTrue(out['has_validated_illustrative_math'])
        self.assertIn('1,500,000원',out['answer_text'])
        self.assertNotIn('2026-11-05 채팅 검토 기준',out['answer_text'])
        self.assertFalse(out['p0_go'])

if __name__=='__main__':unittest.main()
