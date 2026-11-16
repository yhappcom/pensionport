"""V19 extra source-pinned review dispositions; synthetic only and no truth GO."""
import copy
import unittest
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.semantic_risk import audit_semantic_risks
from ire.v6.stage_repair import review_chat_risk_cases
from ire.v6.tests.test_stage_repair import fixture, atom, exchange


class RiskExtendedDecisionTests(unittest.TestCase):
    def _review(self, src, before, after, expected_reason, review_kind):
        risk=audit_semantic_risks(src,before)
        cases=[c for c in risk['review_cases'] if c['reason']==expected_reason]
        self.assertEqual(len(cases),1)
        case=cases[0]
        decision=[{'case_sha256':case['case_sha256'],
                   'source_cue_sha256':sha256(src.cues[case['cue_index']-1].text.encode()),
                   'decision':review_kind,'linked_claim_id':case['claim_id'],
                   'reason':'해당 원문 지시어와 주장 속성을 연결해 내부 검토했다.'}]
        self.assertEqual(risk['review_case_count'],1)
        result=review_chat_risk_cases(src,before,after,decision)
        self.assertEqual(result['directly_remodeled_alerts'],1)
        self.assertEqual(result['outstanding_chat_triage_count'],0)
        self.assertFalse(result['source_meaning_independently_verified'])
        self.assertFalse(result['p0_go'])
        return decision

    def test_exception_mapping_reduces_alert_without_truth_certificate(self):
        src=fixture(['다만, 특별한 출금 제한이 있습니다.'])
        a=atom(src,'C00001',[1],[1],
               '특별한 출금 예외를 설명한다.',stance='UNRESOLVED')
        before=exchange(src,[a]); revised=copy.deepcopy(a)
        revised['exception_cue_indices']=[1]
        after=exchange(src,[revised]);
        decision=self._review(src,before,after,
                              'UNMAPPED_EXCEPTION_IN_MODEL_CONTEXT','REMODELED_EXCEPTION')
        result=review_chat_risk_cases(src,before,after,decision)
        self.assertEqual(result['remodeled_exception_alerts'],1)
        for variant in ('wrong-id','missing-exception','changed-reason'):
            bad=copy.deepcopy(decision)
            modified=copy.deepcopy(after)
            if variant=='wrong-id':bad[0]['linked_claim_id']='C00002'
            elif variant=='missing-exception':
                modified=before
            else:bad[0]['decision']='REMODELED_POLARITY'
            with self.subTest(variant=variant),self.assertRaises(InvalidInput):
                review_chat_risk_cases(src,before,modified,bad)

    def test_polarity_mapping_requires_same_claim_and_new_stance(self):
        src=fixture(['소득 때문이 아니라 소비 패턴의 문제일 수도 있습니다.'])
        a=atom(src,'C00001',[1],[1],
               '소득 때문만의 문제는 아니다.',stance='CONDITIONAL',conds=[1])
        before=exchange(src,[a]); revised=copy.deepcopy(a)
        revised['stance']='NEGATED'
        after=exchange(src,[revised]);
        decision=self._review(src,before,after,
                              'SOURCE_NEGATION_POLARITY_REVIEW','REMODELED_POLARITY')
        self.assertEqual(review_chat_risk_cases(src,before,after,decision)
                         ['remodeled_polarity_alerts'],1)
        for variant in ('wrong-id','unfixed-stance','wrong-action'):
            bad=copy.deepcopy(decision);modified=after
            if variant=='wrong-id':bad[0]['linked_claim_id']='C00002'
            elif variant=='unfixed-stance':modified=before
            else:bad[0]['decision']='REMODELED_EXCEPTION'
            with self.subTest(variant=variant),self.assertRaises(InvalidInput):
                review_chat_risk_cases(src,before,modified,bad)

if __name__=='__main__':unittest.main()
