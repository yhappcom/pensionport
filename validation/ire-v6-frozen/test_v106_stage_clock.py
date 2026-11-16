import sys,unittest
sys.path.insert(0,__file__.rsplit('/',1)[0])
from v106_stage_clock import stage_measured_callable,external_stage_bookend,full_workflow_feasibility
class TestV106(unittest.TestCase):
 def test_measured(self):
  x=stage_measured_callable('MULTICUE_CANDIDATE_GRAPH',lambda: [1,2],repetitions=4);self.assertEqual(x['repetitions'],4);self.assertFalse(x['chat_model_time_measured'])
 def test_missing_semantic(self):
  self.assertEqual(external_stage_bookend('MODEL_CONTEXT_SEMANTIC_REVIEW')['status'],'UNMEASURED')
 def test_reject_uninstrumented(self):
  with self.assertRaises(ValueError):stage_measured_callable('MODEL_CONTEXT_SEMANTIC_REVIEW',lambda:None)
 def test_bounded_elapsed(self):
  x=external_stage_bookend('OFFICIAL_REFERENCE_RETRIEVAL',start_utc='2026-11-14T00:00:00+00:00',end_utc='2026-11-14T00:01:00+00:00',observer='SHELL_BOUNDARY_OBSERVER',includes_tool_wait=True);self.assertEqual(x['elapsed_wall_seconds'],60);self.assertIsNone(x['model_inference_latency_seconds'])
 def test_negative_elapsed(self):
  with self.assertRaises(ValueError):external_stage_bookend('OFFICIAL_REFERENCE_RETRIEVAL',start_utc='2026-11-14T00:02:00Z',end_utc='2026-11-14T00:01:00Z',observer='SHELL_BOUNDARY_OBSERVER')
 def test_bad_observer(self):
  with self.assertRaises(ValueError):external_stage_bookend('OPEN_CASE_RESOLUTION',start_utc='2026-11-14T00:00:00Z',end_utc='2026-11-14T00:01:00Z',observer='MADE_UP')
 def test_no_total_claim(self):
  x=full_workflow_feasibility([stage_measured_callable('SOURCE_IO_PARSE',lambda:1,repetitions=3)],source_cues=15857,video_count=6)
  self.assertIsNone(x['full_end_to_end_duration_seconds']);self.assertIsNone(x['verified_791_video_completion_forecast'])
 def test_dup_stage(self):
  z=stage_measured_callable('SOURCE_IO_PARSE',lambda:1,repetitions=3)
  with self.assertRaises(ValueError):full_workflow_feasibility([z,z],source_cues=20,video_count=1)
 def test_nondeterministic(self):
  ct=[0]
  def f():ct[0]+=1;return ct[0]
  with self.assertRaises(ValueError):stage_measured_callable('SOURCE_IO_PARSE',f,repetitions=3)
if __name__=='__main__':unittest.main()