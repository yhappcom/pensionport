"""Only per-window provenance/disposition coverage, not research quality approval."""
import copy
import json
import unittest
from pathlib import Path
from ire.v5 import first_five_window_review_gate as g
ROOT=Path(__file__).resolve().parents[3]
class FirstFiveWindowReviewTests(unittest.TestCase):
 def test_exact_full_window_meaning_census_still_not_full_facts(self):
  o=g.verify(ROOT)
  self.assertEqual(o['source_windows_with_chat_authored_meaning'],288)
  self.assertEqual(o['video_cue_count'],5129)
  self.assertEqual(o['previous_public_v5_engine_event_windows_still_only'],5)
  self.assertFalse(o['independently_measured_atomic_claim_recall'])
  self.assertFalse(o['full_research_release_go'])
 def data(self):
  return json.loads((ROOT/g.PREFIX/'v5_first_five_video_01_window_review_20261106.json').read_text('utf-8'))
 def test_omission_fails_closed(self):
  d=self.data(); d['records'].pop(14)
  with self.assertRaisesRegex(g.WindowReviewError,'UNPROCESSED_WINDOWS'):
   g.verify(ROOT,replacement=d)
 def test_fabricated_source_span_fails_closed(self):
  d=self.data();d['records'][1]['last_cue']+=1
  with self.assertRaisesRegex(g.WindowReviewError,'CUE_COVERAGE_GAP'):
   g.verify(ROOT,replacement=d)
 def test_false_promotion_rejected(self):
  d=self.data(); d['records'][1]['personal_action_approved']=True
  with self.assertRaisesRegex(g.WindowReviewError,'UNEARNED_ADVISORY'):
   g.verify(ROOT,replacement=d)
 def test_false_full_research_rejected(self):
  d=self.data(); d['current_law_fact_research_completed']=True
  with self.assertRaisesRegex(g.WindowReviewError,'FALSE_FINANCIAL_CERTIFICATION'):
   g.verify(ROOT,replacement=d)
 def test_missing_critical_limit_rejected(self):
  d=self.data(); d['critical_applicability_scopes'][d['records'][0]['domain']]='a'
  with self.assertRaisesRegex(g.WindowReviewError,'MISSING_MEANING_LIMITS'):
   g.verify(ROOT,replacement=d)
if __name__=='__main__':unittest.main()