"""V5 source-only adaptive planner tests; no model semantics inferred."""
import unittest
from ire.v5.engine import cues_from_srt, RunError
from ire.v5.planner import prepare_full_video_manifest
from ire.v5.tests.test_batch import fixture_video

class PlanningTests(unittest.TestCase):
 def test_covers_all_cues_and_full_scope(self):
  raw=fixture_video(1)["source"]
  plan=prepare_full_video_manifest(raw,"V5TEST00001","a"*40,min_cues=2,max_cues=3)
  self.assertEqual(sum(len(w["primary_cue_ids"]) for w in plan["windows"]),4)
  self.assertEqual(plan["active_window_ids"],[w["window_id"] for w in plan["windows"]])
 def test_hashes_stable_across_runs(self):
  raw=fixture_video(2)["source"]
  p=prepare_full_video_manifest(raw,"V5TEST00002","a"*40)
  q=prepare_full_video_manifest(raw,"V5TEST00002","a"*40)
  self.assertEqual(p,q)
 def test_reject_bad_config(self):
  raw=fixture_video(3)["source"]
  with self.assertRaisesRegex(RunError,"V5_SOURCE_PLANNER_CONFIGURATION_INVALID"):
   prepare_full_video_manifest(raw,"V5TEST00003","a"*40,max_cues=1)
if __name__=="__main__":unittest.main()
