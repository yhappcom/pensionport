"""Exhaustive SOURCE-window partition; explicit inability to certify claim recall."""
import copy
import unittest
from pathlib import Path
from ire.v5 import first_five_remnant_221_gate as gate
ROOT=Path(__file__).resolve().parents[3]
class Test221RemainderGate(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d=gate.read(ROOT,gate.LEDGER)
 def test_288_windows_source_coverage_is_structural_not_semantic_recall(self):
  q=gate.verify(ROOT)
  self.assertEqual(q['total_source_windows_structurally_covered'],288)
  self.assertEqual(q['additional_source_windows_reviewed'],221)
  self.assertEqual(q['new_interpretive_candidate_statements'],237)
  self.assertEqual(q['historical_question_nonfinancial_windows_marked'],59)
  self.assertFalse(q['independent_100pct_atomic_recall_proven'])
  self.assertFalse(q['full_financial_knowledge_approval'])
 def test_window_removed_fails_closed(self):
  d=copy.deepcopy(self.d);d['source_boundaries'].pop()
  with self.assertRaisesRegex(gate.RemainderReviewError,'MISSING_SOURCE_WINDOW'):
   gate.verify(ROOT,replacement=d)
 def test_existing_68_window_doublecount_fails(self):
  d=copy.deepcopy(self.d);d['source_boundaries'][0]['window_id']='W00004'
  with self.assertRaisesRegex(gate.RemainderReviewError,'DUPLICATED_OR_WRONG_VIDEO_WINDOW'):
   gate.verify(ROOT,replacement=d)
 def test_original_digest_modified_fails(self):
  d=copy.deepcopy(self.d);d['source_boundaries'][0]['window_sha256']='0'*64
  with self.assertRaisesRegex(gate.RemainderReviewError,'SOURCE_CUE_WINDOW_DIGEST'):
   gate.verify(ROOT,replacement=d)
 def test_source_anchor_cannot_point_off_window(self):
  d=copy.deepcopy(self.d);d['candidate_assertions'][0]['anchor_cue_number']=0
  with self.assertRaisesRegex(gate.RemainderReviewError,'ATOMIC_SOURCE_TEXT_ANCHOR'):
   gate.verify(ROOT,replacement=d)
 def test_claim_fact_approval_cannot_be_promoted(self):
  d=copy.deepcopy(self.d);d['candidate_assertions'][0]['official_fact_approval']=True
  with self.assertRaisesRegex(gate.RemainderReviewError,'FALSE_CLAIM_CERTIFICATION'):
   gate.verify(ROOT,replacement=d)
 def test_legacy_direct_link_cannot_be_invented(self):
  d=copy.deepcopy(self.d);d['candidate_assertions'][0]['legacy_B04_direct_video_claim']='GOMHEE-C62'
  with self.assertRaisesRegex(gate.RemainderReviewError,'WRONG_OR_AUTO_APPROVED_B04'):
   gate.verify(ROOT,replacement=d)
 def test_mislabel_financial_window_as_question_fails(self):
  d=copy.deepcopy(self.d)
  k=next(x for x in d['source_boundaries'] if x['claim_candidate_ids'])
  k['claim_candidate_ids']=[]
  with self.assertRaisesRegex(gate.RemainderReviewError,'MISSING_ACTIVE_WINDOW_CLAIM'):
   gate.verify(ROOT,replacement=d)
 def test_no_raw_original_text_in_public_record(self):
  self.assertTrue(all('text' not in r for r in self.d['source_boundaries']))
  self.assertTrue(all('transcript' not in r and 'original_text' not in r
                      for r in self.d['candidate_assertions']))
 def test_false_total_certification_rejected(self):
  d=copy.deepcopy(self.d);d['full_original_atomic_recall_certified']=True
  with self.assertRaisesRegex(gate.RemainderReviewError,'UNEARNED_RESEARCH_COMPLETION'):
   gate.verify(ROOT,replacement=d)
if __name__=='__main__':unittest.main()
