"""Fail-closed atomic-claim source and B04 non-promotion tests."""
import copy
import unittest
from pathlib import Path
from ire.v5 import first_five_atomic_claim_gate as a

ROOT=Path(__file__).resolve().parents[3]

class AtomicFocusedReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.doc=a._read(ROOT,a.LEDGER)

 def test_complete_focused_claims_not_full_corpus(self):
  got=a.verify(ROOT)
  self.assertEqual(got['candidate_atomic_claims'],68)
  self.assertEqual(got['unique_windows_examined_for_claim_candidates'],67)
  self.assertEqual(got['remaining_windows_not_atomically_proven'],221)
  self.assertFalse(got['all_288_windows_atomic_recall_measured'])
  self.assertFalse(got['full_research_quality_go'])
  self.assertEqual(got['independent_arithmetic_checks'],8)
  self.assertFalse(got['B04_C62_C64_formally_merged'])

 def test_source_window_pointer_cannot_move(self):
  d=copy.deepcopy(self.doc);d['rows'][0]['first_cue']+=1
  with self.assertRaisesRegex(a.AtomicResearchError,'ORIGINAL_CUE_WINDOW'):
   a.load(ROOT,d)

 def test_current_tax_rule_cannot_be_traded(self):
  d=copy.deepcopy(self.doc);d['rows'][6]['financial_fact_approved_for_personal_advice']=True
  with self.assertRaisesRegex(a.AtomicResearchError,'TRADE_APPROVAL'):
   a.load(ROOT,d)

 def test_context_is_not_external_fact_approval(self):
  d=copy.deepcopy(self.doc);d['rows'][20]['evidence_state']='FACT_VERIFIED'
  with self.assertRaisesRegex(a.AtomicResearchError,'FALSE_FACT'):
   a.load(ROOT,d)

 def test_current_law_source_host_not_spoofed(self):
  d=copy.deepcopy(self.doc);d['official_sources'][0]['url']='https://nps.or.kr.attacker.example/true'
  with self.assertRaisesRegex(a.AtomicResearchError,'FALSE_OFFICIAL_SOURCE'):
   a.load(ROOT,d)

 def test_false_legacy_connection_blocked(self):
  d=copy.deepcopy(self.doc);d['rows'][0]['historic_legacy_claim_id']='GOMHEE-C62'
  with self.assertRaisesRegex(a.AtomicResearchError,'UNEARNED_LEGACY'):
   a.load(ROOT,d)

 def test_legacy_C62_stock_tips_not_matching_salary_claim(self):
  x=a.load(ROOT)
  r=next(z for z in x if z['id']=='FV5-A060')
  self.assertEqual(r['historic_legacy_claim_id'],'GOMHEE-C62')
  self.assertEqual(r['legacy_relation_state'],'C62_NOT_SAME')
  self.assertFalse(r['provisional_not_merged'] is False)

 def test_math_failure_not_suppressed(self):
  d=copy.deepcopy(self.doc);d['math_assertions'][3]['expected_rounded_krw']+=1000000
  with self.assertRaisesRegex(a.AtomicResearchError,'MATH_MISMATCH_M04'):
   a.load(ROOT,d)

 def test_high_risk_retrieval_is_source_scoped(self):
  idx=a.load(ROOT)
  h=a.retrieve(idx,'IRP 수수료')
  self.assertTrue(any(z['id']=='FV5-A035' for z in h))
  self.assertTrue(all(z['personalized_trade_action_approved'] is False for z in h))
  self.assertEqual(a.retrieve(idx,'내일 영화관 상영 일정'),[])

 def test_no_private_raw_cues_in_public_ledger(self):
  self.assertTrue(all('source_text' not in c and 'transcript' not in c for c in self.doc['rows']))

if __name__=='__main__':unittest.main()
