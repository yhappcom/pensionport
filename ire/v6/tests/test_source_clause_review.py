"""V20 synthetic only: fail-closed disjoint-clause source contrast evidence."""
import copy
import unittest

from ire.v6.errors import InvalidInput
from ire.v6.semantic_risk import audit_semantic_risks
from ire.v6.source_clause_review import review_same_cue_contrast
from ire.v6.tests.test_stage_repair import fixture, atom, exchange


class SourceContrastTests(unittest.TestCase):
    def setUp(self):
        self.src = fixture([
            '분산투자 이야기입니다.',
            '한 종목에만 투자하면 그 종목 하락 시 전부 떨어집니다. 하지만 주식과 채권',
            '성격이 다른 자산을 나눠 담으면 변동성이 줄 수 있습니다.',
        ])
        a = atom(self.src, 'C00001', [2], [2],
                 '단일 종목 집중은 하락하면 전체 손실이 커질 수 있다.',
                 stance='CONDITIONAL', conds=[2])
        b = atom(self.src, 'C00002', [2, 3], [2, 3],
                 '주식과 채권을 나눠 보유하면 변동성이 줄 수 있다.',
                 stance='UNRESOLVED')
        self.before = exchange(self.src, [a, b])
        original = audit_semantic_risks(self.src, self.before)
        cases = [r for r in original['review_cases']
                 if r['reason'] == 'SOURCE_NEGATION_POLARITY_REVIEW'
                 and r['claim_id'] == 'C00001']
        self.assertEqual(len(cases), 1)
        self.case = cases[0]['case_sha256']
        self.after = copy.deepcopy(self.before)
        self.after['atoms'][0]['source_refs'][0]['quote'] = (
            '한 종목에만 투자하면 그 종목 하락 시 전부 떨어집니다.')
        self.after['atoms'][1]['source_refs'][0]['quote'] = '하지만 주식과 채권'

    def test_source_genuine_disjoint_clause_proves_chat_scope_only(self):
        r = review_same_cue_contrast(self.src, self.before, self.after,
                                    case_sha256=self.case,
                                    contrasting_claim_id='C00002')
        self.assertTrue(r['original_case_still_in_raw_docket'])
        self.assertTrue(r['chat_source_scope_review_complete'])
        self.assertFalse(r['independent_semantic_truth_verified'])
        self.assertFalse(r['finance_rule_applicability_approved'])
        self.assertFalse(r['p0_go'])

    def test_reject_overlap_quote_or_full_cue_claim(self):
        for changed in ('overlap','full'):
            x = copy.deepcopy(self.after)
            if changed == 'overlap':
                x['atoms'][0]['source_refs'][0]['quote'] = (
                    '한 종목에만 투자하면 그 종목 하락 시 전부 떨어집니다. 하지만')
            else:
                x['atoms'][0]['source_refs'][0]['quote'] = self.src.cues[1].text
            with self.subTest(changed=changed), self.assertRaises(InvalidInput):
                review_same_cue_contrast(self.src,self.before,x,
                                         case_sha256=self.case,
                                         contrasting_claim_id='C00002')

    def test_reject_wrong_case_or_carrier(self):
        for case, carrier in [('0'*64,'C00002'), (self.case,'C00001'),
                              (self.case,'C00999')]:
            with self.subTest(case=case,carrier=carrier),self.assertRaises(InvalidInput):
                review_same_cue_contrast(self.src,self.before,self.after,
                                         case_sha256=case,
                                         contrasting_claim_id=carrier)

    def test_reject_contrast_phrase_not_in_second_clause(self):
        x=copy.deepcopy(self.after)
        x['atoms'][1]['source_refs'][0]['quote']='주식과 채권'
        with self.assertRaises(InvalidInput):
            review_same_cue_contrast(self.src,self.before,x,
                                     case_sha256=self.case,contrasting_claim_id='C00002')

    def test_reject_silent_claim_meaning_change(self):
        x=copy.deepcopy(self.after)
        x['atoms'][0]['proposition']='한 종목은 무조건 상승한다.'
        with self.assertRaises(InvalidInput):
            review_same_cue_contrast(self.src,self.before,x,
                                     case_sha256=self.case,contrasting_claim_id='C00002')

    def test_reject_third_cue_owner_without_full_scoping(self):
        third = atom(self.src,'C00003',[2],[2],
                     '분산투자는 언제나 투자성과를 보장한다.',stance='UNRESOLVED')
        before=exchange(self.src,self.before['atoms']+[third])
        after=exchange(self.src,self.after['atoms']+[third])
        with self.assertRaises(InvalidInput):
            review_same_cue_contrast(self.src,before,after,
                                     case_sha256=self.case,contrasting_claim_id='C00002')

    def test_reject_cue_span_gap_even_if_each_quote_valid(self):
        x=copy.deepcopy(self.after)
        x['atoms'][0]['source_refs'][0]['quote']='그 종목 하락 시 전부 떨어집니다.'
        with self.assertRaises(InvalidInput):
            review_same_cue_contrast(self.src,self.before,x,
                                     case_sha256=self.case,contrasting_claim_id='C00002')


if __name__ == '__main__':
    unittest.main()
