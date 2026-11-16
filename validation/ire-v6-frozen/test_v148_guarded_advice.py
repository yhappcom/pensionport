"""V148 educational path: real P3 lineage contract + source/safety adversarial checks.
The natural-language answers are not owner-video claims or external accuracy gold.
"""
import unittest
from pathlib import Path
from unittest.mock import patch
from ire.v6.guarded_question_advisory_v148 import explain, _route, AS_OF

ROOT=Path('.')

class V148GuardedAdvisoryTests(unittest.TestCase):
    def fake_p3(self,root,question,scenario=None):
        return {'schema':'IRE_V5_P3_ANSWER_V1','question':question,
            'answer_text':'2025년 오래된 법령 안내를 수정해야 합니다.',
            'direct_order_or_personal_recommendation_approved':False}

    def test_01_actual_v5_execution_contract(self):
        with patch('ire.v6.guarded_question_advisory_v148.p3_answer',side_effect=self.fake_p3) as spy:
            x=explain(ROOT,'8억원을 5% 수익률로 투자하면 월급 300만원을 세금 없이 평생 대체하나요?')
        self.assertEqual(spy.call_count,1)
        self.assertTrue(x['legacy_v5_p3_executed'])
        self.assertFalse(x['legacy_v5_p3_text_rendered_as_current_law'])
        self.assertNotIn('2025년 오래된 법령',x['answer_text'])
        self.assertFalse(x['p0_e_go'])
        for term in ('4,000만원','3,600만원','세전','손실'):
            self.assertIn(term,x['answer_text'])

    def test_02_v5_unsafe_answer_cannot_be_reused(self):
        def bad(root,question,scenario=None):
            x=self.fake_p3(root,question,scenario)
            x['direct_order_or_personal_recommendation_approved']=True
            return x
        with patch('ire.v6.guarded_question_advisory_v148.p3_answer',side_effect=bad):
            with self.assertRaisesRegex(ValueError,'UNSAFE'):
                explain(ROOT,'ISA 비과세 한도는 얼마인가요?')

    def test_03_isa_2026_web_excerpt_limited_not_certified(self):
        with patch('ire.v6.guarded_question_advisory_v148.p3_answer',side_effect=self.fake_p3):
            x=explain(ROOT,'2026년 ISA 계좌에서는 누구나 이자·배당수익 500만원까지 비과세인가?')
        self.assertIn('200만원',x['answer_text'])
        self.assertIn('400만원',x['answer_text'])
        self.assertIn('개인별',x['answer_text'])
        self.assertFalse(x['issuer_original_http_body_authenticated'])
        self.assertFalse(x['owner_approved_knowledge_db_attached'])
        self.assertFalse(x['direct_order_or_personal_recommendation_approved'])

    def test_04_future_rule_requires_refresh_and_does_not_reuse_old_numbers(self):
        with patch('ire.v6.guarded_question_advisory_v148.p3_answer',side_effect=self.fake_p3):
            x=explain(ROOT,'ISA 비과세 한도는 얼마인가요?',as_of='2027-01-01')
        self.assertEqual(x['matched_educational_route'],'ISA_RULE_NEEDS_REFRESH')
        self.assertNotIn('400만원',x['answer_text'])
        self.assertNotIn('200만원',x['answer_text'])

    def test_05_individual_order_never_performed_even_if_question_has_finance_terms(self):
        for question in ('내 계좌에 있는 주식 전부 팔아줘. 확신 있는 5개 종목으로 전액 매수해줘.',
                         '제 계좌 투자주식 바로 매도해주세요.'):
            with patch('ire.v6.guarded_question_advisory_v148.p3_answer',side_effect=self.fake_p3):
                x=explain(ROOT,question)
            self.assertEqual(x['matched_educational_route'],'ORDER_DENIED')
            self.assertFalse(x['automated_order_execution'])
            self.assertFalse(x['direct_order_or_personal_recommendation_approved'])

    def test_06_original_8_question_substantive_groups(self):
        from v147_p0e_live_quality import PUBLIC_CASES
        expected={'E01':'ISA_RULE_CONDITIONAL','E02':'PENSION_RULE_CONDITIONAL',
            'E03':'CONCENTRATION_RISK','E04':'HYPOTHETICAL_MATH',
            'E05':'DIVIDEND_NOT_MARGIN','E06':'DISTRESS_NOT_GUARANTEE',
            'E07':'SUCCESS_ODDS_UNVERIFIED','E08':'SEMICONDUCTOR_CYCLE_CONDITIONAL'}
        for case in PUBLIC_CASES[:8]:
            with self.subTest(case=case['id']):
                route,body,_=_route(case['question'],AS_OF)
                self.assertEqual(route,expected[case['id']])
                for group in case['required_groups']:
                    self.assertTrue(any(x.casefold() in body.casefold() for x in group), (case['id'],group))

    def test_07_preregistered_variant_examples(self):
        cases=[
          ('ISA 비과세 한도는 일반형과 서민형에서 어떻게 달라지나요?','ISA_RULE_CONDITIONAL'),
          ('IRP와 연금저축의 2026년 세액공제 한도와 합산 규칙?','PENSION_RULE_CONDITIONAL'),
          ('한 업종의 3개 주식에 몰아넣으면 확신 있어도 안전할까요?','CONCENTRATION_RISK'),
          ('10억원을 4% 수익률로 운용해 매월 250만원을 보장받을 수 있나요?','HYPOTHETICAL_MATH'),
          ('고배당주 투자면 기업가치가 떨어져도 원금은 안전한가?','DIVIDEND_NOT_MARGIN'),
          ('적자 기업을 3년 기다리면 본전 회복되나요?','DISTRESS_NOT_GUARANTEE'),
          ('회사 신기술 성공률 80%라고 하면 발표 전 매수해야 하나?','SUCCESS_ODDS_UNVERIFIED'),
          ('인공지능 붐으로 메모리 반도체 재고 사이클은 영원히 끝났나요?','SEMICONDUCTOR_CYCLE_CONDITIONAL'),
        ]
        for q,route in cases:
            with self.subTest(route=route):
                got,body,_=_route(q,AS_OF)
                self.assertEqual(got,route)
                self.assertGreater(len(body),50)

    def test_08_math_variants_are_calculated_not_a_fixed_8_5_template(self):
        q='10억원을 4% 수익률로 운용해 매월 250만원을 보장받을 수 있나요?'
        got,body,_=_route(q,AS_OF)
        self.assertEqual(got,'HYPOTHETICAL_MATH')
        self.assertIn('4,000만원',body)
        self.assertIn('3,000만원',body)
        self.assertNotIn('3,600만원',body)
        self.assertIn('연간',body)

    def test_09_irrelevant_and_unrecognized_finance_do_not_get_fake_authority(self):
        for q in ('내일 영화관 상영시간표 알려줘.', 'ISA 계좌는 어느 증권사에 있습니까?'):
            route,body,urls=_route(q,AS_OF)
            self.assertEqual(route,'NO_DIRECT_FINANCIAL_DOMAIN')
            self.assertFalse(urls)
            self.assertNotIn('200만원',body)

    def test_10_no_current_law_original_bytes_or_unverified_owner_promotion(self):
        with patch('ire.v6.guarded_question_advisory_v148.p3_answer',side_effect=self.fake_p3):
            x=explain(ROOT,'연금저축 900만원을 넣으면 전액 세액공제 되나요? IRP는 따로 900만원인가요?')
        for key in ('owner_approved_knowledge_db_attached','issuer_original_http_body_authenticated',
                    'v23_current_law_owner_e2e_executed','independently_adjudicated_answer_accuracy',
                    'personal_investor_eligibility_verified','p0_e_go','p0_go'):
            self.assertIs(x[key],False,key)

    def test_11_variant_questions_are_sha_sealed_before_actual_p3_probe(self):
        from v148_quality_probe import HOLDOUT_CASES, _sha
        self.assertEqual(_sha(HOLDOUT_CASES),
             '91b0355b749a2fdf2738fd0ff16ce98ac78442125d96e499c605a6e0ca5ddfda')

    def test_12_original_v147_rubric_sha_unchanged(self):
        from v148_quality_probe import _sha
        from v147_p0e_live_quality import PUBLIC_CASES
        self.assertEqual(_sha(PUBLIC_CASES),
             'c661be11f0c931b7abd1777e5abba9a7a9fa4fb62c55f487c476a4ecdfd61847')

    def test_13_invalid_dates_and_empty_questions_rejected(self):
        with patch('ire.v6.guarded_question_advisory_v148.p3_answer',side_effect=self.fake_p3):
            with self.assertRaises(ValueError):explain(ROOT,'')
            with self.assertRaises(ValueError):explain(ROOT,'ISA 비과세 한도?',as_of='2026-02-30')

if __name__=='__main__':unittest.main(verbosity=2)
