"""Synthetic V25 guards; same-chat labels are NOT blind human gold."""
from __future__ import annotations

import copy
import unittest
from unittest.mock import patch
from pathlib import Path

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.semantic_finance_decision_v25 import (
    _audit_relevance, illustrative_isa_extra_base, evaluate_current_question_v25)
from ire.v6.tests.test_advisory_decision_utility import CurrentDecisionUtilityTests


class V25SemanticFinanceTests(unittest.TestCase):
    def setUp(self):
        older=CurrentDecisionUtilityTests('test_actual_style_irp_and_etf_question_leads_with_decision')
        older.setUp()
        self.old=older
        self.q=older.q
        self.selected=['C00001','C00002']
        self.decisions=self._relevance(self.q,self.selected)
        self.isa={
            'kind':'ISA_TRANSFER','isa_expiry_date':'2026-10-01',
            'pension_deposit_date':'2026-10-30',
            'isa_balance_at_expiry_krw':40000000,
            'pension_deposit_from_isa_krw':30000000,
            'prior_transfers_from_same_isa_krw':0,
            'previously_used_extra_base_krw':0,
        }
        self.evidence=[self._rule('NTS_ISA_60D',
            'ISA 만기일로부터 60일 이내에 연금계좌에 납입한 자금을 해당 제도의 전환액으로 취급한다.'),
            self._rule('NTS_ISA_EXTRA',
            'ISA 만기 연금계좌 전환금액의 10%에 해당하는 금액을 최대 300만원의 추가 세액공제 대상 납입한도로 한다.')]
        self.law={'reviewed_as_of':'2026-11-10','reviewer':'CHATGPT_CURRENT_TURN',
                  'scope':'CURRENT_GENERAL_RULE_ONLY','transfer_days':60,
                  'extra_base_rate_bps':1000,'max_extra_base_krw':3000000,
                  'rule_ids':['NTS_ISA_60D','NTS_ISA_EXTRA'],
                  'excerpt_sha256':[r['excerpt_sha256'] for r in self.evidence]}

    def _rule(self,rid,excerpt):
        return {'rule_id':rid,
            'source_url':'https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7885',
            'effective_from':'2026-01-01','effective_to':None,'retrieved_on':'2026-11-10',
            'excerpt':excerpt,'excerpt_sha256':sha256(excerpt.encode('utf-8')),
            'document_body_sha256':None,
            'scope_note':'현행 일반 법령 설명이며 납세자별 적용성과 실제 결정세액은 미확인이다.'}

    def _relevance(self,q,selected):
        facets=['IRP_WITHDRAWAL' if cid=='C00001' else 'ETF_TAX' for cid in selected]
        atoms={a['claim_id']:a for a in self.old.exchange['atoms']}
        return [{'claim_id':cid,'question_sha256':sha256(q.encode()),
                 'proposition_sha256':sha256(atoms[cid]['proposition'].encode()),
                 'relation':'COUNTERPOINT','facet':facet,
                 'reviewer':'CHATGPT_CURRENT_TURN','reviewed_as_of':'2026-11-10',
                 'source_attribution_checked':True,'stance_checked':True,
                 'conditions_and_exceptions_checked':True,'numeric_scope_checked':True,
                 'reason':'영상 발언이 현재 질문의 세부 논점을 직접 다루므로 대조 설명이 필요하다.'}
                for cid,facet in zip(selected,facets)]

    def _audit(self,q=None,selected=None,decisions=None):
        return _audit_relevance(q or self.q,self.old.exchange,selected or self.selected,
            self.decisions if decisions is None else decisions,'2026-11-10')

    def _base(self,scenario=None,law=None,evidence=None):
        return illustrative_isa_extra_base(self.isa if scenario is None else scenario,
            current_as_of='2026-11-10',
            primary_evidence=self.evidence if evidence is None else evidence,
            law_review=self.law if law is None else law)

    def test_dual_subjects_cited_individually_and_real_v24_route_invoked(self):
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer',side_effect=self.old._p3) as p3:
            out=evaluate_current_question_v25(self.old.root,self.q,
                source=self.old.source,exchange=self.old.exchange,
                current_as_of='2026-11-10',primary_evidence=self.old.evidence,
                chat_decisions=self.old.decisions,selected_claim_ids=self.selected,
                relevance_decisions=self.decisions)
        p3.assert_called_once()
        self.assertEqual(out['semantic_relevance_review']['question_facets'],
                         ['ETF_TAX','IRP_WITHDRAWAL'])
        self.assertFalse(out['p0_go'])
        self.assertFalse(out['independent_question_to_claim_entailment_verified'])
        self.assertIn('법정 중도인출 사유',out['answer_text'])

    def test_same_product_but_different_financial_facet_blocked(self):
        # Previously V24 would accept this claim just because IRP occurs in both.
        q='IRP 은퇴 후 수령액과 월 생활비는 어느 정도인가요?'
        d=self._relevance(q,['C00001'])
        with self.assertRaisesRegex(InvalidInput,'SAME_TOPIC_DIFFERENT_QUESTION_FACET'):
            self._audit(q,['C00001'],d)

    def test_composite_question_missing_etf_claim_fail_closed(self):
        d=self._relevance(self.q,['C00001'])
        with self.assertRaisesRegex(InvalidInput,'UNCOVERED_QUESTION_FACETS'):
            self._audit(self.q,['C00001'],d)

    def test_missing_one_review_receipt_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'CENSUS_MISMATCH'):
            self._audit(decisions=self.decisions[:1])

    def test_forged_question_digest_rejected(self):
        d=copy.deepcopy(self.decisions); d[0]['question_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'PROVENANCE_OR_ASOF_MISMATCH'):
            self._audit(decisions=d)

    def test_irrelevant_same_topic_claim_rejected(self):
        d=copy.deepcopy(self.decisions); d[0]['relation']='IRRELEVANT'
        with self.assertRaisesRegex(InvalidInput,'UNRELATED_OR_UNCERTAIN'):
            self._audit(decisions=d)

    def test_missing_exception_review_rejected(self):
        d=copy.deepcopy(self.decisions); d[1]['conditions_and_exceptions_checked']=False
        with self.assertRaisesRegex(InvalidInput,'REVIEW_INCOMPLETE'):
            self._audit(decisions=d)

    def test_duplicate_relevance_claim_rejected(self):
        d=copy.deepcopy(self.decisions); d[1]=copy.deepcopy(d[0])
        with self.assertRaisesRegex(InvalidInput,'UNKNOWN_OR_DUPLICATE'):
            self._audit(decisions=d)

    def test_no_arbitrary_general_question_semantic_approval(self):
        q='오늘 투자해도 되나요?'
        with self.assertRaisesRegex(InvalidInput,'UNSUPPORTED_QUESTION_SEMANTIC_FACET'):
            self._audit(q,decisions=self._relevance(q,self.selected))

    def test_isa_extra_base_not_a_refund_or_tax_credit(self):
        out=self._base()
        self.assertEqual(out['illustrative_extra_deduction_base_krw'],3000000)
        self.assertIsNone(out['actual_credit_krw'])
        self.assertIsNone(out['actual_refund_krw'])
        self.assertFalse(out['personal_eligibility_verified'])

    def test_isa_60_day_expiry_and_date_boundary(self):
        s=copy.deepcopy(self.isa)
        s['isa_expiry_date']='2026-08-01'
        s['pension_deposit_date']='2026-10-01'
        self.assertEqual(self._base(s)['illustrative_extra_deduction_base_krw'],0)
        s['pension_deposit_date']='2026-08-01'
        self.assertEqual(self._base(s)['days_after_expiry'],0)

    def test_isa_cross_tax_year_defers_instead_of_resetting_credit_cap(self):
        s=copy.deepcopy(self.isa)
        s['isa_expiry_date']='2025-12-15'
        s['pension_deposit_date']='2026-01-05'
        self.assertEqual(self._base(s)['status'],'CROSS_TAX_YEAR_DEFER')
        self.assertIsNone(self._base(s)['illustrative_extra_deduction_base_krw'])

    def test_isa_paid_more_than_expiry_balance_rejected(self):
        s=copy.deepcopy(self.isa);s['pension_deposit_from_isa_krw']=50000000
        with self.assertRaisesRegex(InvalidInput,'EXCEEDS_EXPIRY_BALANCE'):
            self._base(s)

    def test_isa_prior_used_base_reduces_remaining_cap(self):
        s=copy.deepcopy(self.isa)
        s['previously_used_extra_base_krw']=2000000
        s['prior_transfers_from_same_isa_krw']=5000000
        self.assertEqual(self._base(s)['illustrative_extra_deduction_base_krw'],1000000)

    def test_isa_stale_official_excerpt_fails(self):
        e=copy.deepcopy(self.evidence);e[0]['retrieved_on']='2026-07-01'
        with self.assertRaisesRegex(InvalidInput,'LAW_OUT_OF_DATE'):
            self._base(evidence=e)

    def test_isa_forged_rule_hash_fails(self):
        l=copy.deepcopy(self.law);l['excerpt_sha256'][0]='0'*64
        with self.assertRaisesRegex(InvalidInput,'EXCERPT_PIN_MISMATCH'):
            self._base(law=l)

    def test_isa_without_two_distinct_official_rules_fails(self):
        l=copy.deepcopy(self.law);l['rule_ids']=['NTS_ISA_60D','NTS_ISA_60D']
        with self.assertRaisesRegex(InvalidInput,'TWO_DISTINCT_PRIMARY_RULES'):
            self._base(law=l)

    def test_isa_wrong_legal_cap_rejected(self):
        l=copy.deepcopy(self.law);l['max_extra_base_krw']=5000000
        with self.assertRaisesRegex(InvalidInput,'LEGAL_TERMS_NOT_REVIEWED'):
            self._base(law=l)


if __name__=='__main__':
    unittest.main()
