import copy,json,unittest
from pathlib import Path
from ire.v5.first_five_private_event_gate import verify,EventIndexError
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'ire/v5/validation/first_five_private_event_pointer_20261106.json'

class SourceAndPrivateReceiptSafety(unittest.TestCase):
 def setUp(self):self.idx=json.loads(DATA.read_text('utf8'))
 def test_valid_public_pointer_is_not_source_approval(self):
  r=verify(ROOT);self.assertEqual(r['research_closure'],'BLOCKED')
  self.assertEqual(r['provisional_model_windows_private_only'],288)
  self.assertEqual(r['unresolved_cues'],4908)
  self.assertFalse(r['real_v5_engine_replay_of_private_events_by_ci'])
  self.assertTrue(r['actual_v5_engine_private_replay_host_attested'])
 def test_forbid_forged_full_research_completion(self):
  z=copy.deepcopy(self.idx);z['all_original_288_windows_final_research_complete']=True
  with self.assertRaises(EventIndexError):verify(ROOT,z)
 def test_forbid_counting_old_public_model_drafts_as_288_receipts(self):
  z=copy.deepcopy(self.idx);z['original_public_batch_processed_windows']=288
  with self.assertRaises(EventIndexError):verify(ROOT,z)
 def test_forbid_empty_events_or_tampered_source_pointer(self):
  z=copy.deepcopy(self.idx);z['videos'][0]['event_chain_head_sha256']='f'
  with self.assertRaises(EventIndexError):verify(ROOT,z)
 def test_forbid_claims_of_private_source_replay_in_ci(self):
  z=copy.deepcopy(self.idx);z['source_bytes_reopened_by_github_ci']=True
  with self.assertRaises(EventIndexError):verify(ROOT,z)
 def test_forbid_false_engine_sha_in_pointer(self):
  z=copy.deepcopy(self.idx);z['exact_ResearchRun_source_sha256']='missing'
  with self.assertRaises(EventIndexError):verify(ROOT,z)
 def test_forbid_claiming_github_ci_reopened_private_source(self):
  z=copy.deepcopy(self.idx);z['source_bytes_reopened_by_github_ci']=True
  with self.assertRaises(EventIndexError):verify(ROOT,z)
 def test_no_financial_fact_auto_approval(self):
  z=copy.deepcopy(self.idx);z['all_financial_facts_independently_approved']=True
  with self.assertRaises(EventIndexError):verify(ROOT,z)
if __name__=='__main__':unittest.main()
