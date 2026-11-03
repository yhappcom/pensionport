"""Fail-closed read-only prior-knowledge join, never financial truth approval."""
import copy
import unittest
from ire.v4_prior_knowledge_join import validate_index,candidate_crosswalk

SHA="a"*40
PATH="knowledge/national-pension.md"
INDEX={
  "schema":"IRE_V4_LEGACY_READ_ONLY_CANDIDATE_INDEX_V1",
  "source_files":[{"path":PATH,"git_blob_sha":SHA,"line_count":2}],
  "unique_principle_count":1,
  "import_into_ire_incremental_knowledge":False,
  "automatic_merge":False,"approved_financial_facts":0,
  "items":[{"legacy_claim_id":"GOMHEE-C66",
    "candidate_text":"국민연금과 연금저축을 노후현금흐름의 서로 다른 계좌로 활용한다.",
    "state":"READ_ONLY_LEGACY_PRINCIPLE_NOT_FINANCIAL_FACT_VERIFIED",
    "sources":[{"path":PATH,"line":1,"git_blob_sha":SHA}]}]
}
DRAFT={
 "schema":"IRE_V4_P0_ADAPTIVE_PROVISIONAL_V1","original_sha256":"c"*64,
 "windows":[{"window_id":"W00001","claims":[{
     "claim_id":"P0C1","proposition":"국민연금과 연금저축을 함께 활용한다.",
     "frame":{"product":"국민연금","financial_event":"연금저축"},
     "source_refs":[{"cue_index":1,"quote":"국민연금"}],
     "annotation_status":"UNREVIEWED"
 }]}]
}

class LegacyJoinTests(unittest.TestCase):
 def run_join(self,d=DRAFT,index=INDEX,blobs=None):
  return candidate_crosswalk(d,index,blobs or {PATH:SHA})
 def test_strong_candidate_not_approval(self):
  r=self.run_join()
  self.assertEqual(len(r["relation_candidates"]),1)
  self.assertEqual(r["relation_decisions_approved"],0)
  self.assertFalse(r["relation_candidates"][0]["same_claim_proven"])
  self.assertFalse(r["legacy_imported_into_new_ire"])
 def test_wrong_pin(self):
  with self.assertRaises(ValueError):
   self.run_join(blobs={PATH:"b"*40})
 def test_unverified_cannot_be_promoted(self):
  x=copy.deepcopy(INDEX);x["approved_financial_facts"]=1
  with self.assertRaises(ValueError):self.run_join(index=x)
 def test_conflicting_legacy_id(self):
  x=copy.deepcopy(INDEX);x["items"].append(x["items"][0]);x["unique_principle_count"]=2
  with self.assertRaises(ValueError):self.run_join(index=x)
 def test_draft_must_be_unreviewed(self):
  x=copy.deepcopy(DRAFT);x["windows"][0]["claims"][0]["annotation_status"]="APPROVED"
  with self.assertRaises(ValueError):self.run_join(d=x)
 def test_single_concept_is_weak_and_not_relation(self):
  x=copy.deepcopy(DRAFT);x["windows"][0]["claims"][0]["frame"]={}
  x["windows"][0]["claims"][0]["proposition"]="국민연금 수령이 개시된다."
  r=self.run_join(d=x)
  self.assertEqual(len(r["relation_candidates"]),0)
  self.assertEqual(r["weak_single_concept_matches"],1)
 def test_unrelated_is_no_match(self):
  x=copy.deepcopy(DRAFT);x["windows"][0]["claims"][0]["frame"]={}
  x["windows"][0]["claims"][0]["proposition"]="교통 안전벨트 착용법"
  r=self.run_join(d=x)
  self.assertEqual(len(r["relation_candidates"]),0)
  self.assertEqual(r["weak_single_concept_matches"],0)

if __name__=="__main__":
 unittest.main()
