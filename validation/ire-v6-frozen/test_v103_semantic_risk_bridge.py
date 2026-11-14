import unittest,copy
from dataclasses import dataclass
from v103_semantic_risk_bridge import contextual_signal_events,score_internal_overlap
PIN='a'*64
@dataclass
class C:
 index:int
 start_ms:int
 end_ms:int
 text:str
class T(unittest.TestCase):
 def setup(self,arr):return [C(i,100*i,100*i+10,t) for i,t in enumerate(arr,1)]
 def runq(self,arr):return contextual_signal_events(self.setup(arr),video_id='synthetic',source_zip_sha256=PIN,expected_source_zip_sha256=PIN)
 def test_loan(self):
  x=self.runq(['그런데 빚을 갚고 다시 빌렸어요']);self.assertIn('LOAN_BALANCE_REVIEW',[y['kind'] for y in x['risk_events']])
 def test_cashflow(self):
  x=self.runq(['자산이 1억 늘었어요','연금계좌에 돈을 넣었습니다']);self.assertIn('CASHFLOW_CAUSALITY_REVIEW',[y['kind'] for y in x['risk_events']])
 def test_absolute_scope(self):
  x=self.runq(['연금은 무조건 안전하고 확정수익입니다']);self.assertIn('GUARANTEE_SCOPE_REVIEW',[y['kind'] for y in x['risk_events']])
 def test_date_amount(self):
  x=self.runq(['작년 투자수익이 1억원 늘었어요']);self.assertIn('AMOUNT_TIME_REVIEW',[y['kind'] for y in x['risk_events']])
 def test_correction(self):
  x=self.runq(['아니요, 주식은 그게 아니라']);self.assertIn('SPEAKER_CORRECTION_REVIEW',[y['kind'] for y in x['risk_events']])
 def test_plain_chat(self):self.assertEqual(self.runq(['안녕하세요','좋은 아침이에요'])['risk_event_count'],0)
 def test_false_go(self):
  x=self.runq(['대출금 1000만원을 갚았습니다']);self.assertFalse(x['p0_go']);self.assertIsNone(x['certified_recall'])
 def test_owner_mismatch(self):
  with self.assertRaises(ValueError):contextual_signal_events(self.setup(['연금']),video_id='X',source_zip_sha256='b'*64,expected_source_zip_sha256=PIN)
 def test_source_noncontiguous(self):
  c=self.setup(['빚']);c[0].index=2
  with self.assertRaises(ValueError):contextual_signal_events(c,video_id='X',source_zip_sha256=PIN,expected_source_zip_sha256=PIN)
 def test_source_time(self):
  c=self.setup(['빚']);c[0].end_ms=0
  with self.assertRaises(ValueError):contextual_signal_events(c,video_id='X',source_zip_sha256=PIN,expected_source_zip_sha256=PIN)
 def test_duplicate_and_order(self):
  x=self.runq(['금 1000만원을 팔았습니다','대출 받아서 투자했어요']);self.assertEqual(len(x['risk_events']),len({(q['cue_index'],q['kind']) for q in x['risk_events']}))
 def test_no_false_gold_with_internal_spans(self):
  with self.assertRaises(ValueError):score_internal_overlap(internal_spans=[{'video_id':'x','first_cue':1,'last_cue':1,'independent_gold':True,'actual_error_certified':False}],baseline_alerts=[],new_events=[],source_by_index={('x',1):'h'})
 def test_internal_counts_not_recall(self):
  src={('x',1):'h',('x',2):'h'}
  spans=[{'video_id':'x','first_cue':1,'last_cue':2,'independent_gold':False,'actual_error_certified':False}]
  x=score_internal_overlap(internal_spans=spans,baseline_alerts=[],new_events=[{'video_id':'x','cue_index':2}],source_by_index=src)
  self.assertEqual(x['v93_v103_union_direct_overlap'],1);self.assertIsNone(x['certified_financial_recall'])
 def test_cannot_reclassify_risk_signal_as_truth(self):
  x=self.runq(['연금은 보장됩니다'])
  self.assertTrue(all(y['automated_true_error_certified'] is False for y in x['risk_events']))
if __name__=='__main__':unittest.main()