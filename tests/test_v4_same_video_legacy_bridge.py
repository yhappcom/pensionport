"""No historical approval can be inherited through source-cue overlap."""
import copy
import unittest
from ire.v4_same_video_legacy_bridge import same_video_cue_candidates

SHA="a"*64
PINS={"data/analysis_events/sz5N9WJS310.json":"b"*40,
      "data/synthesis/investment_knowledge_v4/reviews/x.json":"c"*40}
BASE={"schema":"IRE_V4_P0_LEGACY_VIDEO001_CUE_CROSSWALK_BASELINE_V1",
 "source_video_id":"sz5N9WJS310","source_sha256":SHA,
 "original_cue_count":1195,
 "pinned_git_blobs":[{"path":p,"git_blob_sha":s} for p,s in PINS.items()],
 "legacy_claims_count":1,
 "prior_approval_is_not_new_model_semantic_proof":True,
 "legacy_claims_are_not_independent_gold":True,
 "allow_auto_merge":False,"allow_auto_financial_approval":False,
 "claims":[{"legacy_claim_id":"sz5N9WJS310-06",
  "source_cue_range":[10,20],"historical_verification":"CONTRADICTED",
  "expected_personal_investment_approval":False}]}
DRAFT={"schema":"IRE_V4_P0_ADAPTIVE_PROVISIONAL_V1","original_sha256":SHA,
 "windows":[{"window_id":"W00001","claims":[{"claim_id":"P0C1",
     "annotation_status":"UNREVIEWED",
     "source_refs":[{"cue_index":15,"quote":"sample"}]}]}]}

class TestLegacyVideoCueJoin(unittest.TestCase):
 def call(self,d=DRAFT,b=BASE,p=PINS):
  return same_video_cue_candidates(d,b,SHA,p)
 def test_contradicted_history_requires_review(self):
  x=self.call()
  self.assertEqual(x["source_overlap_candidate_pairs"],1)
  self.assertTrue(x["pairs"][0]["prior_numeric_contradiction"])
  self.assertEqual(x["confirmed_relation_decisions"],0)
  self.assertFalse(x["pairs"][0]["identical_semantics_proven"])
 def test_old_sha_mismatch_blocked(self):
  b=copy.deepcopy(BASE);b["source_sha256"]="0"*64
  with self.assertRaises(ValueError):self.call(b=b)
 def test_git_blob_mismatch_blocked(self):
  with self.assertRaises(ValueError):self.call(p={**PINS,"data/analysis_events/sz5N9WJS310.json":"0"*40})
 def test_forbid_old_approval_inheritance(self):
  b=copy.deepcopy(BASE);b["allow_auto_financial_approval"]=True
  with self.assertRaises(ValueError):self.call(b=b)
 def test_draft_preapproved_rejected(self):
  d=copy.deepcopy(DRAFT);d["windows"][0]["claims"][0]["annotation_status"]="APPROVED"
  with self.assertRaises(ValueError):self.call(d=d)
 def test_unmatched_must_be_reported(self):
  d=copy.deepcopy(DRAFT);d["windows"][0]["claims"][0]["source_refs"][0]["cue_index"]=25
  x=self.call(d=d)
  self.assertEqual(x["new_claims_without_direct_prior_source_overlap"],1)
  self.assertEqual(x["source_overlap_candidate_pairs"],0)

if __name__=="__main__":
 unittest.main()
