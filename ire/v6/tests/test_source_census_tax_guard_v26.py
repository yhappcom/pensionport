"""V26 additive safety regression fixtures; NO external blind human gold."""
from __future__ import annotations

import copy
import unittest
from unittest.mock import patch
from pathlib import Path

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.source_census_tax_guard_v26 import (
    audit_candidate_census, evaluate_current_question_v26)


class SourceCensusTaxGuardV26Tests(unittest.TestCase):
    def setUp(self):
        # Import fixtures lazily. Top-level TestCase imports silently duplicate
        # the previous V24/V25 discovery count.
        from ire.v6.tests.test_advisory_decision_utility import CurrentDecisionUtilityTests
        from ire.v6.tests.test_semantic_finance_decision_v25 import V25SemanticFinanceTests
        from ire.v6.tests.test_stage_repair import fixture, atom, exchange
        self.v24 = CurrentDecisionUtilityTests(
            'test_actual_style_irp_and_etf_question_leads_with_decision')
        self.v24.setUp()
        self.v25 = V25SemanticFinanceTests(
            'test_dual_subjects_cited_individually_and_real_v24_route_invoked')
        self.v25.setUp()
        self.fixture=fixture;self.atom=atom;self.exchange_fn=exchange
        self.q=self.v24.q
        self.selected=['C00001','C00002']
        self.rel=self.v25._relevance(self.q,self.selected)
        self.census=self._census(
            self.q,self.v24.exchange,self.selected)

    def _census(self,question,ex,selected):
        selected=set(selected)
        return [{
            'claim_id':a['claim_id'],
            'question_sha256':sha256(question.encode()),
            'proposition_sha256':sha256(a['proposition'].encode()),
            'disposition':'SELECTED_RELEVANT' if a['claim_id'] in selected
                          else 'REVIEWED_OFF_TOPIC',
            'reviewer':'CHATGPT_CURRENT_TURN','reviewed_as_of':'2026-11-10',
            'context_checked':True,
            'reason':'발언의 전후 의미와 질문에 필요한 논점 및 예외를 구분하여 검토하였다.'
        } for a in ex['atoms']]

    def _args(self):
        return dict(root=self.v24.root,question=self.q,
            source=self.v24.source,exchange=self.v24.exchange,
            current_as_of='2026-11-10',
            primary_evidence=self.v24.evidence,
            chat_decisions=self.v24.decisions,
            selected_claim_ids=self.selected,
            relevance_decisions=self.rel,
            candidate_dispositions=self.census)

    def _call(self, args):
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer',
                   side_effect=self.v24._p3) as p3:
            result=evaluate_current_question_v26(**args)
            p3.assert_called_once()
            return result

    def _isa_args(self):
        source=self.fixture([
            'ISA 만기자금을 60일 안에 연금계좌로 이전하면 전환금액의 10%는 300만원 한도 내에서 추가 세액공제 대상 납입한도에 해당한다.'
        ])
        ex=self.exchange_fn(source,[self.atom(source,'C00001',[1],[1],
            'ISA 만기자금의 60일 내 연금계좌 이전에 세액공제 대상 추가 납입한도 규정이 존재한다.')])
        ex['atoms'][0]['condition_cue_indices']=[1]
        q='ISA 만기자금을 연금계좌로 이전할 때 세액공제 대상 추가 납입한도는?'
        rule1={
            'rule_id':'NTS_ISA_60D',
            'source_url':'https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7885',
            'effective_from':'2026-01-01','effective_to':None,
            'retrieved_on':'2026-11-10',
            'excerpt':'ISA 계좌 만기일 기준 잔액을 연금계좌로 60일 이내 납입할 수 있다.',
            'document_body_sha256':None,
            'scope_note':'금융기관 거래 내역 및 개인 공제 조건은 확인되지 않았으므로 일반 규정 발췌만 사용한다.'}
        rule2={
            'rule_id':'NTS_ISA_EXTRA',
            'source_url':'https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875',
            'effective_from':'2026-01-01','effective_to':None,
            'retrieved_on':'2026-11-10',
            'excerpt':'ISA 만기 전환금액의 10%, 300만원 한도로 세액공제 대상 추가 납입한도를 확대한다.',
            'document_body_sha256':None,
            'scope_note':'실제 공제율과 결정세액 및 이미 사용된 추가 한도는 개인별 사실 확인이 필요하다.'}
        for rule in (rule1,rule2):
            rule['excerpt_sha256']=sha256(rule['excerpt'].encode())
        evidence=[rule1,rule2]
        d=[{'claim_id':'C00001',
            'proposition_sha256':sha256(ex['atoms'][0]['proposition'].encode()),
            'classification':'CURRENT_GENERAL_RULE_CONSISTENT_CONDITIONAL',
            'rule_ids':['NTS_ISA_60D','NTS_ISA_EXTRA'],
            'reason':'현재 법령상의 ISA 연금 전환 일반 규정과 일치할 수 있으나 개인 조건을 확인해야 한다.',
            'missing_conditions':['가입자 소득 및 결정세액','납입 내역'],
            'reviewer':'CHATGPT_CURRENT_TURN','reviewed_as_of':'2026-11-10'}]
        relevance=[{
            'claim_id':'C00001','question_sha256':sha256(q.encode()),
            'proposition_sha256':sha256(ex['atoms'][0]['proposition'].encode()),
            'relation':'DIRECT','facet':'ISA_TRANSFER',
            'reviewer':'CHATGPT_CURRENT_TURN','reviewed_as_of':'2026-11-10',
            'source_attribution_checked':True,'stance_checked':True,
            'conditions_and_exceptions_checked':True,'numeric_scope_checked':True,
            'reason':'해당 ISA 만기 전환과 연금계좌 납입한도의 적용 요건을 직접 다룬 주장이다.'}]
        law={'reviewed_as_of':'2026-11-10','reviewer':'CHATGPT_CURRENT_TURN',
            'scope':'CURRENT_GENERAL_RULE_ONLY','transfer_days':60,
            'extra_base_rate_bps':1000,'max_extra_base_krw':3000000,
            'rule_ids':['NTS_ISA_60D','NTS_ISA_EXTRA'],
            'excerpt_sha256':[rule1['excerpt_sha256'],rule2['excerpt_sha256']]}
        scenario={
            'kind':'ISA_TRANSFER','isa_expiry_date':'2026-10-01',
            'pension_deposit_date':'2026-10-30',
            'isa_balance_at_expiry_krw':40000000,
            'pension_deposit_from_isa_krw':30000000,
            'prior_transfers_from_same_isa_krw':0,
            'previously_used_extra_base_krw':0}
        return dict(root=self.v24.root,question=q,source=source,exchange=ex,
            current_as_of='2026-11-10',primary_evidence=evidence,
            chat_decisions=d,selected_claim_ids=['C00001'],
            relevance_decisions=relevance,
            candidate_dispositions=self._census(q,ex,['C00001']),
            scenario=scenario,isa_law_review=law)

    def test_full_selected_and_off_topic_census_then_real_v24_pipeline(self):
        a=self._args()
        o=self._call(a)
        self.assertEqual(o['source_candidate_census']['candidate_atom_count'],3)
        self.assertEqual(o['source_candidate_census']['selected_claim_count'],2)
        self.assertEqual(o['source_candidate_census']['reviewed_off_topic_count'],1)
        self.assertFalse(o['full_original_atomic_recall_certified'])
        self.assertFalse(o['p0_go'])

    def test_unselected_relevant_atom_forces_open_before_v5(self):
        a=self._args(); a['candidate_dispositions']=copy.deepcopy(a['candidate_dispositions'])
        a['candidate_dispositions'][-1]['disposition']='PENDING_RELEVANT'
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer') as p3:
            with self.assertRaisesRegex(InvalidInput,'UNSELECTED_OR_UNKNOWN_PENDING'):
                evaluate_current_question_v26(**a)
        p3.assert_not_called()

    def test_unknown_nonselected_facet_forces_open(self):
        a=self._args();a['candidate_dispositions']=copy.deepcopy(a['candidate_dispositions'])
        a['candidate_dispositions'][-1]['disposition']='UNDECIDABLE'
        with self.assertRaisesRegex(InvalidInput,'UNSELECTED_OR_UNKNOWN_PENDING'):
            evaluate_current_question_v26(**a)

    def test_missing_atom_census_blocked(self):
        a=self._args();a['candidate_dispositions']=a['candidate_dispositions'][:-1]
        with self.assertRaisesRegex(InvalidInput,'MISSING_CANDIDATE'):
            evaluate_current_question_v26(**a)

    def test_selected_claim_marked_offtopic_blocked(self):
        a=self._args();a['candidate_dispositions']=copy.deepcopy(a['candidate_dispositions'])
        a['candidate_dispositions'][0]['disposition']='REVIEWED_OFF_TOPIC'
        with self.assertRaisesRegex(InvalidInput,'SELECTED_CLAIM_CENSUS_CONTRADICTION'):
            evaluate_current_question_v26(**a)

    def test_tampered_question_sha_blocked(self):
        a=self._args();a['candidate_dispositions']=copy.deepcopy(a['candidate_dispositions'])
        a['candidate_dispositions'][0]['question_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'SOURCE_OR_DATE_NOT_VERIFIED'):
            evaluate_current_question_v26(**a)

    def test_duplicate_census_row_blocked(self):
        a=self._args();a['candidate_dispositions']=copy.deepcopy(a['candidate_dispositions'])
        a['candidate_dispositions'][2]=copy.deepcopy(a['candidate_dispositions'][0])
        with self.assertRaisesRegex(InvalidInput,'UNSORTED_DUPLICATE'):
            evaluate_current_question_v26(**a)

    def test_action_with_isatransfer_numeric_guard_blocks_before_v5(self):
        a=self._isa_args()
        a['question']='ISA 만기자금 3천만원을 연금계좌로 옮겨줘'
        a['candidate_dispositions']=self._census(
            a['question'],a['exchange'],a['selected_claim_ids'])
        with patch('ire.v6.semantic_finance_decision_v25.evaluate_current_question') as p3:
            with self.assertRaisesRegex(InvalidInput,'ACTION_ATTACHED_ISA_MATH_REFUSED'):
                evaluate_current_question_v26(**a)
        p3.assert_not_called()

    def test_action_with_isatransfer_please_blocked(self):
        a=self._isa_args()
        a['question']='ISA 계좌에서 연금계좌로 이체해주세요'
        a['candidate_dispositions']=self._census(
            a['question'],a['exchange'],a['selected_claim_ids'])
        with self.assertRaisesRegex(InvalidInput,'ACTION_ATTACHED_ISA_MATH_REFUSED'):
            evaluate_current_question_v26(**a)

    def test_clean_first_transfer_illustrative_nominal_base_only(self):
        a=self._isa_args()
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer',
                   side_effect=self.v24._p3) as p3, \
             patch('ire.v6.advisory_decision_utility._v5_p2_compare') as p2:
            out=evaluate_current_question_v26(**a)
        p3.assert_called_once()
        p2.assert_not_called()
        v=out['isa_extra_deduction_base_illustration']
        self.assertEqual(v['illustrative_extra_deduction_base_krw'],3000000)
        self.assertIsNone(v['actual_credit_krw'])
        self.assertIsNone(v['actual_refund_krw'])
        self.assertIsNone(out['actual_isa_tax_credit_or_refund'])
        self.assertIn('대상 납입한도',out['answer_text'])

    def test_prior_transfer_even_with_zero_claimed_base_is_deferred(self):
        a=self._isa_args()
        a['scenario']['prior_transfers_from_same_isa_krw']=5000000
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer',
                   side_effect=self.v24._p3):
            out=evaluate_current_question_v26(**a)
        v=out['isa_extra_deduction_base_illustration']
        self.assertEqual(v['status'],'PRIOR_TRANSFER_OR_CAP_CUSTODY_OPEN')
        self.assertIsNone(v['illustrative_extra_deduction_base_krw'])

    def test_previous_credit_base_used_without_transfer_history_is_deferred(self):
        a=self._isa_args()
        a['scenario']['previously_used_extra_base_krw']=1000000
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer',
                   side_effect=self.v24._p3):
            out=evaluate_current_question_v26(**a)
        self.assertEqual(out['isa_extra_deduction_base_illustration']['status'],
                         'PRIOR_TRANSFER_OR_CAP_CUSTODY_OPEN')

    def test_cross_tax_year_defers_but_retains_current_law_review(self):
        a=self._isa_args()
        a['scenario']['isa_expiry_date']='2025-12-15'
        a['scenario']['pension_deposit_date']='2026-01-05'
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer',
                   side_effect=self.v24._p3):
            out=evaluate_current_question_v26(**a)
        self.assertEqual(out['isa_extra_deduction_base_illustration']['status'],
                         'CROSS_TAX_YEAR_DEFER')

    def test_isa_unverified_general_terms_defers(self):
        a=self._isa_args();a['isa_law_review']=None
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer',
                   side_effect=self.v24._p3):
            out=evaluate_current_question_v26(**a)
        self.assertEqual(out['isa_extra_deduction_base_illustration']['status'],
                         'CURRENT_ISA_LEGAL_TERMS_NOT_REVIEWED')

    def test_invalid_isa_balance_before_v5(self):
        a=self._isa_args()
        a['scenario']['pension_deposit_from_isa_krw']=45000000
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer') as p3:
            with self.assertRaisesRegex(InvalidInput,'EXCEEDS_EXPIRY_BALANCE'):
                evaluate_current_question_v26(**a)
        p3.assert_not_called()

    def test_isa_without_selected_rule_citation_fails_before_v5(self):
        a=self._isa_args();a['chat_decisions'][0]['rule_ids']=['NTS_ISA_EXTRA']
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer') as p3:
            with self.assertRaisesRegex(InvalidInput,'RULES_NOT_SUPPORTED'):
                evaluate_current_question_v26(**a)
        p3.assert_not_called()

    def test_bad_isa_fields_rejected_early(self):
        a=self._isa_args();a['scenario']['unpriced_refund_krw']=900000
        with self.assertRaisesRegex(InvalidInput,'ISA_INPUT_FIELDS_DRIFT'):
            evaluate_current_question_v26(**a)

    def test_bool_as_krw_rejected(self):
        a=self._isa_args();a['scenario']['prior_transfers_from_same_isa_krw']=True
        with self.assertRaisesRegex(InvalidInput,'INVALID_AMOUNT'):
            evaluate_current_question_v26(**a)


if __name__=='__main__':
    unittest.main()
