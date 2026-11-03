import copy
import unittest
from ire.v5_app.batch_worker import reduce_five_video_commands, ControlError

VIDS=[f"V5TEST{i:05d}" for i in range(1,6)]
START={"schema":"IRE_V5_APP_FIVE_VIDEO_COMMAND_V1",
 "job_id":"v5-five-batch-001","sequence":1,"operation":"OPEN",
 "videos":[{"video_id":id,"source_cues":100,"windows_total":10,
   "source_sha256":"a"*64,"prior_git_blob_sha":"b"*40} for id in VIDS]}
CHECK={"schema":"IRE_V5_APP_FIVE_VIDEO_COMMAND_V1",
 "job_id":"v5-five-batch-001","sequence":2,"operation":"CHECKPOINT",
 "progress":[{"video_id":id,"processed_windows":1,"claims":1,
     "evidence_reviews":1,"relation_reviews":1,"event_receipts":1,
     "event_chain_sha256":"c"*64} for id in VIDS]}
class FivePublicAppTests(unittest.TestCase):
 def test_five_video_job_has_five_hints_without_false_approval(self):
  x=reduce_five_video_commands([START,CHECK])
  self.assertEqual(x["windows_processed_reported"],5)
  self.assertEqual(x["windows_remaining_reported"],45)
  self.assertEqual(len(x["next_source_window_hints"]),5)
  self.assertFalse(x["single_chat_turn_five_video_research_proven"])
  self.assertFalse(x["claim_review_and_official_scope_independently_attested"])
 def test_duplicate_video_rejected(self):
  x=copy.deepcopy(START);x["videos"][1]["video_id"]=x["videos"][0]["video_id"]
  with self.assertRaises(ControlError):reduce_five_video_commands([x])
 def test_undecided_source_census_no_artificial_completion(self):
  x=copy.deepcopy(CHECK)
  for p in x["progress"]:
   p["processed_windows"]=10
  y=reduce_five_video_commands([START,x])
  self.assertEqual(y["windows_remaining_reported"],0)
  self.assertFalse(y["all_five_videos_research_complete"])
 def test_monotonic_rewind_rejected(self):
  x=copy.deepcopy(CHECK);x["sequence"]=3;x["progress"][0]["processed_windows"]=0
  with self.assertRaises(ControlError):reduce_five_video_commands([START,CHECK,x])
 def test_progress_unknown_video(self):
  x=copy.deepcopy(CHECK);x["progress"][1]["video_id"]="UNKNOWN_123"
  with self.assertRaises(ControlError):reduce_five_video_commands([START,x])
 def test_four_videos_supported(self):
  x=copy.deepcopy(START);x["videos"]=x["videos"][:4]
  y=reduce_five_video_commands([x])
  self.assertEqual(y["video_count"],4)
if __name__=="__main__":unittest.main()
