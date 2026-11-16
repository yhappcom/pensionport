"""V23: actual V5 route protected by private V22 current-law assessment.

All results are synthetic source-bound process checks, NOT legal gold or
independent final answer accuracy. One full-root smoke runs the real V5 P3.
"""
from __future__ import annotations
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

from ire.v6.errors import InvalidInput
from ire.v6.current_advisory_bridge import answer_with_current_law
from ire.v6.tests import test_current_law_reassessment as _original


class CurrentAdvisoryBridgeTests(unittest.TestCase):
    def setUp(self):
        original=_original.CurrentLawReassessmentTests(methodName='test_current_law_after_video_publication_is_valid_for_current_advice')
        original.setUp()
        self.source=original.source
        self.exchange=original.ex
        self.evidence=original.evidence
        self.decisions=original.decisions
        self.args={
            'source':self.source,'exchange':self.exchange,
            'current_as_of':'2026-11-10','primary_evidence':self.evidence,
            'chat_decisions':self.decisions,
            'selected_claim_ids':['C00001','C00002','C00003']
        }
        self.question='오늘 현재 IRP 중도인출과 국내 ETF 세금은 모두 동일하나요?'
        self.old_p3={'schema':'IRE_V5_P3_ANSWER_V1','question':self.question,
            'answer_text':'2026-11-05 과거 스냅샷의 검증되지 않은 오래된 법규를 그대로 안내합니다.',
            'domain_candidates':['PENSION_TAX'],'fact_ids':['OLD_SNAPSHOT'],
            'direct_order_or_personal_recommendation_approved':False}

    def call(self,**changed):
        args=dict(self.args);args.update(changed)
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer',return_value=self.old_p3) as mocked:
            output=answer_with_current_law(Path('/unused'),self.question,**args)
            mocked.assert_called_once_with(Path('/unused'),self.question,None)
        return output

    def test_p3_actually_called_but_old_law_text_not_carried_forward(self):
        r=self.call()
        self.assertTrue(r['v5_p3_executed'])
        self.assertEqual(r['v5_p3_original_schema'],'IRE_V5_P3_ANSWER_V1')
        self.assertEqual(r['v5_p3_origin_fact_ids'],['OLD_SNAPSHOT'])
        self.assertIn('현재 법령과 충돌',r['answer_text'])
        self.assertIn('법정 사유',r['answer_text'])
        self.assertNotIn('2026-11-05 과거 스냅샷',r['answer_text'])
        self.assertFalse(r['v5_p3_legacy_text_rendered_as_current_law'])
        self.assertFalse(r['personal_account_eligibility_or_tax_approved'])
        self.assertFalse(r['p0_go'])

    def test_current_authority_urls_appear_in_user_answer(self):
        r=self.call()
        self.assertEqual(r['reviewed_current_rule_claim_count'],2)
        self.assertEqual(len(r['official_context_urls']),2)
        self.assertTrue(all(url in r['answer_text'] for url in r['official_context_urls']))

    def test_unreviewed_chat_atom_is_explicitly_blocked(self):
        r=self.call(chat_decisions=self.decisions[:1])
        self.assertEqual(r['selected_unresolved_claim_ids'],['C00002','C00003'])
        self.assertIn('검토 미실시',r['answer_text'])
        self.assertFalse(r['personal_account_eligibility_or_tax_approved'])

    def test_all_missing_chat_reviews_never_make_approval(self):
        r=self.call(chat_decisions=[])
        self.assertEqual(len(r['selected_unresolved_claim_ids']),3)
        self.assertEqual(r['reviewed_current_rule_claim_count'],0)
        self.assertFalse(r['p0_go'])
        self.assertNotIn('조건부 일치',r['answer_text'])

    def test_unknown_current_fact_must_be_open_and_no_url_required(self):
        d=copy.deepcopy(self.decisions)
        d[0]['classification']='CURRENT_FACT_OR_APPLICABILITY_UNKNOWN'
        d[0]['rule_ids']=[]
        d[0]['missing_conditions']=['개인 상황 확인']
        r=self.call(chat_decisions=d)
        self.assertIn('사실 또는 개인 적용성 확인 보류',r['answer_text'])
        self.assertIn('C00001',r['selected_unresolved_claim_ids'])

    def test_no_unqualified_legal_promotion(self):
        d=copy.deepcopy(self.decisions)
        d[0]['classification']='CURRENT_GENERAL_RULE_CONSISTENT_CONDITIONAL'
        d[0]['missing_conditions']=[]
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer',return_value=self.old_p3),self.assertRaisesRegex(InvalidInput,'UNCONDITIONAL'):
            answer_with_current_law(Path('.'),self.question,**(self.args|{'chat_decisions':d}))

    def test_bad_current_law_cannot_reach_v5_generation(self):
        bad=copy.deepcopy(self.evidence)
        bad[0]['effective_from']='2027-01-01'
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer') as mocked,self.assertRaisesRegex(InvalidInput,'REFERENCED_RULE_NOT_CURRENT'):
            answer_with_current_law(Path('.'),self.question,**(self.args|{'primary_evidence':bad}))
        mocked.assert_not_called()

    def test_foreign_duplicate_or_unsorted_source_claims_block(self):
        for ids in [['C99999'],['C00002','C00001'],['C00001','C00001'],[],['C00002',6]]:
            with self.subTest(ids=ids),patch('ire.v6.current_advisory_bridge._v5_p3_answer') as mocked,self.assertRaises(InvalidInput):
                answer_with_current_law(Path('.'),self.question,**(self.args|{'selected_claim_ids':ids}))
            mocked.assert_not_called()

    def test_unsafe_p3_order_approval_blocked(self):
        old=copy.deepcopy(self.old_p3);old['direct_order_or_personal_recommendation_approved']=True
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer',return_value=old),self.assertRaisesRegex(InvalidInput,'UNSAFE'):
            answer_with_current_law(Path('.'),self.question,**self.args)

    def test_wrong_p3_question_or_schema_blocked(self):
        for key,value in [('schema','IRE_V6_BAD'),('question','DIFFERENT')]:
            old=copy.deepcopy(self.old_p3);old[key]=value
            with self.subTest(key=key),patch('ire.v6.current_advisory_bridge._v5_p3_answer',return_value=old),self.assertRaises(InvalidInput):
                answer_with_current_law(Path('.'),self.question,**self.args)

    def test_source_claim_sha_drift_is_blocking(self):
        changed=copy.deepcopy(self.decisions)
        changed[0]['proposition_sha256']='0'*64
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer') as mocked,self.assertRaisesRegex(InvalidInput,'PROPOSITION_DRIFT'):
            answer_with_current_law(Path('.'),self.question,**(self.args|{'chat_decisions':changed}))
        mocked.assert_not_called()

    def test_current_as_of_changes_without_matching_host_review_blocked(self):
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer') as mocked,self.assertRaisesRegex(InvalidInput,'REVIEWER_DATE_INVALID'):
            answer_with_current_law(Path('.'),self.question,**(self.args|{'current_as_of':'2026-11-11'}))
        mocked.assert_not_called()

    def test_real_v5_p3_route_on_canonical_full_checkout(self):
        # Public CI runs from the full Git checkout. Local partial source-only
        # artifacts lack frozen master data; do not misreport a local pass.
        root=Path(__file__).resolve().parents[3]
        if not (root/'ire/v5/legacy_consolidation/master_index_20261105.json').is_file():
            self.skipTest('complete V5 source+master fixtures only in canonical repo')
        from ire.v5.advisory_answer_pipeline import answer as actual_p3
        v5=actual_p3(root,self.question)
        self.assertEqual(v5['schema'],'IRE_V5_P3_ANSWER_V1')
        self.assertEqual(v5['question'],self.question)
        response=answer_with_current_law(root,self.question,**self.args)
        self.assertTrue(response['v5_p3_executed'])
        self.assertEqual(response['v5_p3_legacy_answer_sha256'],
                         __import__('hashlib').sha256(v5['answer_text'].encode()).hexdigest())
        self.assertNotIn('2026-11-05 채팅 검토 기준',response['answer_text'])
        self.assertFalse(response['p0_go'])

if __name__=='__main__':unittest.main()
