from __future__ import annotations
import copy, json, tempfile, unittest
from pathlib import Path
from ire.v5_app.worker import load_job, reduce_commands, parse_command, ControlError, emit_state

OPEN = {
 "schema": "IRE_V5_APP_PUBLIC_COMMAND_V1", "job_id": "v5-video-001-research",
 "sequence": 1, "operation": "OPEN", "video_id": "sz5N9WJS310",
 "source_cues": 1195, "total_windows": 81,
 "source_sha256": "2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f",
}
PROGRESS = {
 "schema": "IRE_V5_APP_PUBLIC_COMMAND_V1", "job_id": "v5-video-001-research",
 "sequence": 2, "operation": "CHECKPOINT", "reported_windows": 3,
 "reported_claims": 5, "reported_evidence_reviews": 5,
 "reported_relation_reviews": 5, "reported_event_receipts": 13,
 "encrypted_checkpoint_sha256": "9a5b4262740749118990a58fd049b0961eee79d5aee4b133a76b884b957183b8",
 "receipt_chain_sha256": "37018c1d2358ee6c48aeb4d98b27053591b3b270b996f9c679bae424241bffa3",
}

class PublicControlTests(unittest.TestCase):
 def test_prior_real_3_window_report_appears_as_pending(self):
  s=reduce_commands([OPEN,PROGRESS]);self.assertEqual(s['remaining_windows_reported'],78)
  self.assertEqual(s['next_expected_window_hint'],'W00004')
  self.assertFalse(s['full_video_completed_and_verified'])
  self.assertFalse(s['private_receipt_chain_verified_by_github'])
  self.assertFalse(s['official_evidence_independently_approved_by_github'])
  self.assertFalse(s['financial_advice_approved'])
 def test_no_progress_does_not_claim_research(self):
  s=reduce_commands([OPEN]);self.assertEqual(s['remaining_windows_reported'],81)
  self.assertEqual(s['next_expected_window_hint'],'W00001')
 def test_public_data_allow_list_blocks_private_text(self):
  x=copy.deepcopy(PROGRESS);x['original_subtitle_text']='PRIVATE CONTENT'
  with self.assertRaisesRegex(ControlError,'EXACT_FIELD_SET'):parse_command(x)
 def test_public_data_allow_list_blocks_secret(self):
  x=copy.deepcopy(OPEN);x['recovery_secret']='SECRET'
  with self.assertRaisesRegex(ControlError,'EXACT_FIELD_SET'):parse_command(x)
 def test_monotonic_windows(self):
  x=copy.deepcopy(PROGRESS);x['sequence']=3;x['reported_windows']=2
  with self.assertRaisesRegex(ControlError,'CHECKPOINT_WINDOW_COUNT_DRIFT'):
   reduce_commands([OPEN,PROGRESS,x])
 def test_overcount_rejected(self):
  x=copy.deepcopy(PROGRESS);x['reported_windows']=82
  with self.assertRaisesRegex(ControlError,'CHECKPOINT_WINDOW_COUNT_DRIFT'):
   reduce_commands([OPEN,x])
 def test_missing_sequence_rejected(self):
  x=copy.deepcopy(PROGRESS);x['sequence']=3
  with self.assertRaisesRegex(ControlError,'MISSING_OR_REORDERED_SEQUENCE'):
   reduce_commands([OPEN,x])
 def test_claims_less_than_evidence_rejected(self):
  x=copy.deepcopy(PROGRESS);x['reported_claims']=1
  with self.assertRaisesRegex(ControlError,'REVIEWS_EXCEED_CLAIM_COUNT'):
   reduce_commands([OPEN,x])
 def test_not_permitted_auto_approval(self):
  x=copy.deepcopy(PROGRESS);x['financial_facts_approved']=10
  with self.assertRaisesRegex(ControlError,'EXACT_FIELD_SET'):
   reduce_commands([OPEN,x])
 def test_zero_or_bad_sha(self):
  x=copy.deepcopy(PROGRESS);x['encrypted_checkpoint_sha256']='abc'
  with self.assertRaisesRegex(ControlError,'ENCRYPTED_CHECKPOINT_SHA256_INVALID'):
   reduce_commands([OPEN,x])
 def test_file_io_accurate_and_no_private_fields(self):
  with tempfile.TemporaryDirectory() as folder:
   job=Path(folder)/'v5-video-001-research';job.mkdir()
   for n,x in enumerate([OPEN,PROGRESS],1):
    (job/f'{n:06d}.json').write_text(json.dumps(x))
   s=load_job(job)
   state=Path(folder)/'states'/f'{job.name}.json'
   emit_state(state,s)
   stored=json.loads(state.read_text())
   self.assertEqual(stored['last_sequence'],2)
   self.assertNotIn('PRIVATE',state.read_text())
   self.assertNotIn('recovery_secret',state.read_text())
 def test_no_hidden_files_in_public_job_dir(self):
  with tempfile.TemporaryDirectory() as folder:
   job=Path(folder)/'v5-video-001-research';job.mkdir()
   (job/'000001.json').write_text(json.dumps(OPEN))
   (job/'private.srt').write_text('HIDDEN')
   with self.assertRaisesRegex(ControlError,'CONTROL_JOB_FILES_INVALID'):
    load_job(job)

if __name__=='__main__': unittest.main()
