"""V19: same-source-cue opposite stances may belong to distinct quoted clauses."""
import copy
import unittest
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.stage_repair import review_chat_risk_cases
from ire.v6.semantic_risk import audit_semantic_risks
from ire.v6.tests.test_stage_repair import fixture,atom,exchange

class SameCueClauseReviewTests(unittest.TestCase):
    def setUp(self):
        self.src=fixture([
            '자금 부족의 원인이 소득만은 아니라는 설명입니다.',
            '있습니다. 따라서 가계부를 확인하세요.'
        ])
        self.a=atom(self.src,'C00001',[1,2],[1,2],
                    '소득 부족만이 문제가 아니라고 설명한다.',stance='NEGATED')
        self.b=atom(self.src,'C00002',[2],[2],
                    '가계부 기록을 권유한다.',stance='AFFIRMED')
        self.before=exchange(self.src,[self.a,self.b])
        docket=audit_semantic_risks(self.src,self.before)
        self.assertEqual(docket['cases_by_reason']['CONFLICTING_STANCES_ON_SAME_SOURCE_CUE'],1)
        self.c=next(x for x in docket['review_cases']
                    if x['reason']=='CONFLICTING_STANCES_ON_SAME_SOURCE_CUE')
        self.decision=[{'case_sha256':self.c['case_sha256'],
                        'source_cue_sha256':sha256(self.src.cues[1].text.encode()),
                        'decision':'SAME_CUE_DISTINCT_CLAUSES',
                        'linked_claim_id':'C00001',
                        'reason':'한 자막 구간에 연속된 서로 다른 문장의 부정과 권유가 명시된다.'}]
    def _refined(self):
        after=copy.deepcopy(self.before)
        after['atoms'][0]['source_refs'][1]['quote']='있습니다.'
        after['atoms'][1]['source_refs'][0]['quote']='따라서 가계부를 확인하세요.'
        return after
    def test_distinct_substring_spans_reviewed_raw_risk_retained(self):
        after=self._refined()
        r=review_chat_risk_cases(self.src,self.before,after,self.decision)
        self.assertEqual(r['same_cue_distinct_clause_alerts_raw_still_present'],1)
        self.assertEqual(r['raw_post_review_alert_count'],1)
        self.assertEqual(r['outstanding_chat_triage_count'],0)
        self.assertFalse(r['source_meaning_independently_verified'])
        self.assertFalse(r['p0_go'])
    def test_full_quote_or_overlapping_quote_cannot_close_case(self):
        for variant in ['both-full','overlap']:
            sample=self._refined()
            if variant=='both-full':
                sample=self.before
            else:
                sample['atoms'][0]['source_refs'][1]['quote']='있습니다. 따라서'
                sample['atoms'][1]['source_refs'][0]['quote']='따라서 가계부를 확인하세요.'
            with self.subTest(variant=variant),self.assertRaises(InvalidInput):
                review_chat_risk_cases(self.src,self.before,sample,self.decision)
    def test_claim_id_or_case_digest_forgery_rejected(self):
        for variant in ['target','case_sha','cue_sha']:
            review=copy.deepcopy(self.decision)
            if variant=='target':review[0]['linked_claim_id']='C00999'
            elif variant=='case_sha':review[0]['case_sha256']='0'*64
            else:review[0]['source_cue_sha256']='0'*64
            with self.subTest(variant=variant),self.assertRaises(InvalidInput):
                review_chat_risk_cases(self.src,self.before,self._refined(),review)

if __name__=='__main__':unittest.main()
