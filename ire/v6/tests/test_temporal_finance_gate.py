"""V21 synthetic-only: date offsets, anti-retroactivity, cashflow frequency & scope."""
import copy
import unittest
from ire.v6.errors import InvalidInput
from ire.v6.temporal_finance_gate import (
    publication_temporal_rule_gate,audit_rate_frequency,
    flag_legal_scope_overgeneralization)

class TemporalFinanceGateTests(unittest.TestCase):
    def setUp(self):
        self.args={
          'video_id':'VKr060rIirM','source_sha256':'a'*64,
          'youtube_url':'https://www.youtube.com/watch?v=VKr060rIirM',
          'date_published':'2026-09-16T18:00:26-07:00','roster_date':'2026-09-16',
          'law_versions':[{'rule_id':'PENSION_DECR_2026_10','effective_from':'2026-10-01',
             'effective_to':None,'law_body_sha256':None},
            {'rule_id':'PENSION_DECR_2026_07','effective_from':'2026-07-01',
             'effective_to':'2026-10-01','law_body_sha256':None}]}
    def test_kst_crosses_to_next_day_and_roster_keeps_native_day(self):
        r=publication_temporal_rule_gate(**self.args)
        self.assertEqual(r['published_kst'],'2026-09-17T10:00:26+09:00')
        self.assertTrue(r['roster_matches_native_offset_calendar_date'])
        self.assertFalse(r['recording_time_independently_known'])
        self.assertFalse(r['p0_go'])
    def test_future_october_decree_cannot_approve_september_video(self):
        r=publication_temporal_rule_gate(**self.args)
        self.assertEqual(r['rule_assessments'][0]['temporal_status'],
                         'FUTURE_RULE_NOT_VALID_AT_PUBLICATION')
        self.assertEqual(r['rule_assessments'][1]['temporal_status'],
                         'DATE_POTENTIALLY_COMPATIBLE_UNPINNED_PRIMARY_BYTES')
    def test_primary_sha_does_not_prove_recording_or_personal_applicability(self):
        a=copy.deepcopy(self.args)
        a['law_versions'][1]['law_body_sha256']='f'*64
        r=publication_temporal_rule_gate(**a)
        self.assertEqual(r['rule_assessments'][1]['temporal_status'],
                         'DATE_COMPATIBLE_PINNED_BODY_RECORDING_TIME_UNKNOWN')
        self.assertFalse(r['rule_assessments'][1]['applied_to_speaker_or_individual'])
    def test_reject_wrong_youtube_video_id(self):
        a=copy.deepcopy(self.args);a['youtube_url']='https://www.youtube.com/watch?v=yDt8Ki7d_Yk'
        with self.assertRaises(InvalidInput):publication_temporal_rule_gate(**a)
    def test_reject_timezone_free_publish_date(self):
        a=copy.deepcopy(self.args);a['date_published']='2026-09-16T18:00:26'
        with self.assertRaises(InvalidInput):publication_temporal_rule_gate(**a)
    def test_reject_bad_rule_real_calendar(self):
        a=copy.deepcopy(self.args);a['law_versions'][0]['effective_from']='2026-02-30'
        with self.assertRaises(InvalidInput):publication_temporal_rule_gate(**a)
    def test_reject_duplicate_rule_and_invalid_end(self):
        a=copy.deepcopy(self.args);a['law_versions'][1]['rule_id']=a['law_versions'][0]['rule_id']
        with self.assertRaises(InvalidInput):publication_temporal_rule_gate(**a)
        a=copy.deepcopy(self.args);a['law_versions'][1]['effective_to']='2026-07-01'
        with self.assertRaises(InvalidInput):publication_temporal_rule_gate(**a)
    def test_superceded_rule_fails_closed(self):
        a=copy.deepcopy(self.args);a['law_versions'][1]['effective_to']='2026-08-01'
        self.assertEqual(publication_temporal_rule_gate(**a)['rule_assessments'][1]['temporal_status'],
                         'SUPERSEDED_RULE_NOT_VALID_AT_PUBLICATION')
    def test_yield_wording_monthly_rate_contradicts_stated_cashflow(self):
        r=audit_rate_frequency(principal_won=240000000,yield_percent='6',
             claimed_rate_period='MONTH',expected_monthly_payout_won=1200000)
        self.assertEqual(r['reported_payout_matches_rate_period'],'YEAR')
        self.assertTrue(r['period_conflict'])
        self.assertEqual(r['status'],'RATE_PERIOD_CONTRADICTION_REVIEW')
        self.assertFalse(r['monthly_dividend_guaranteed'])
    def test_annual_rate_explains_but_does_not_guarantee_cashflow(self):
        r=audit_rate_frequency(principal_won=200000000,yield_percent='6',
             claimed_rate_period='YEAR',expected_monthly_payout_won=1000000)
        self.assertFalse(r['period_conflict'])
        self.assertFalse(r['financial_factual_truth_approved'])
    def test_reject_silent_float_or_invalid_rate_or_wrong_monthly_amount(self):
        with self.assertRaises(InvalidInput):
            audit_rate_frequency(principal_won=2e8,yield_percent='6',claimed_rate_period='YEAR',expected_monthly_payout_won=1000000)
        with self.assertRaises(InvalidInput):
            audit_rate_frequency(principal_won=200000000,yield_percent='120',claimed_rate_period='YEAR',expected_monthly_payout_won=1000000)
        with self.assertRaises(InvalidInput):
            audit_rate_frequency(principal_won=200000000,yield_percent='6',claimed_rate_period='WEEK',expected_monthly_payout_won=1000000)
    def test_blanket_etf_gain_tax_is_a_review_not_approved_fact(self):
        r=flag_legal_scope_overgeneralization('일반계좌 ETF 매매수익은 15.4% 세금입니다.')
        self.assertEqual(r['review_flags'],['ETF_GAINS_TAX_TYPE_SCOPE_MISSING'])
        self.assertFalse(r['official_law_applicability_approved'])
    def test_etf_scope_exception_does_not_trigger_blanket_alarm(self):
        r=flag_legal_scope_overgeneralization('국내주식형 ETF 매매차익 비과세 예외가 있고 기타 ETF 15.4% 과세가 가능합니다.')
        self.assertEqual(r['review_flags'],[])
        self.assertFalse(r['source_meaning_independently_verified'])
    def test_irp_absolute_withdrawal_requires_exception_review(self):
        r=flag_legal_scope_overgeneralization('IRP는 중도인출 자체가 아예 안 돼요.')
        self.assertEqual(r['review_flags'],['IRP_MIDTERM_WITHDRAWAL_LEGAL_EXCEPTIONS_MISSING'])
    def test_irp_scoped_statement_not_auto_approved(self):
        r=flag_legal_scope_overgeneralization('IRP 중도인출은 제한되며 법정 사유와 예외가 있습니다.')
        self.assertEqual(r['review_flags'],[])
        self.assertFalse(r['p0_go'])

if __name__=='__main__':unittest.main()
