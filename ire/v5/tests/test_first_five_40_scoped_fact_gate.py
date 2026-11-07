"""Unit tests for scoped, fail-closed source and official-knowledge pilot."""
from __future__ import annotations
import copy,json,tempfile,unittest,os
from pathlib import Path
from ire.v5.first_five_40_scoped_fact_gate import load,retrieval,private_source_verify,SafetyError,LEDGER

SOURCE=Path(__file__).resolve().parents[1]/'validation'/'first_five_40_scoped_fact_knowledge_review_20261106.json'
BASE=Path(os.environ.get('PRIVATE_V5_FIRST40_SOURCE_ROOT', '/nonexistent-v5-source-root'))

class ScopedFirst40Tests(unittest.TestCase):
 def setUp(self):
  d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup)
  self.root=Path(d.name)
  p=self.root/LEDGER;p.parent.mkdir(parents=True);p.write_bytes(SOURCE.read_bytes())
  data=self.root/'data';data.mkdir()
  self.source=json.loads(SOURCE.read_text())
  known={x for n in self.source['knowledge_overlay'] for x in n['prior_claim_ids']}
  rows=[{'claim_id':f'GOMHEE-C{i:02d}','supporting_videos':['not-the-first-video']} for i in range(1,117)]
  assert known<={x['claim_id'] for x in rows}
  (data/'claims.jsonl').write_text('\n'.join(json.dumps(x) for x in rows)+'\n')
 def mutate(self,action):
  f=self.root/LEDGER;s=json.loads(f.read_text());action(s);f.write_text(json.dumps(s,ensure_ascii=False)+'\n')
 def test_97_claims_and_15_narrow_sourced_facts(self):
  x=load(self.root)
  self.assertEqual(len(x['claims']),97)
  self.assertEqual(len(x['knowledge_overlay']),9)
 def test_reject_fabricated_legal_domain(self):
  self.mutate(lambda x:x['official_sources'][0].update(url='https://fake.example/rule'))
  with self.assertRaisesRegex(SafetyError,'UNTRUSTED_AUTHORITY'):load(self.root)
 def test_reject_official_rule_promoted_to_whole_fact(self):
  self.mutate(lambda x:x['claims'][0].update(entire_video_claim_approved=True))
  with self.assertRaisesRegex(SafetyError,'UNSAFE_WHOLE_CLAIM_PROMOTION'):load(self.root)
 def test_reject_v5_approved_claim_without_engine_verifier(self):
  self.mutate(lambda x:x['claims'][0].update(v5_kernel_fact_verification_event_issued=True))
  with self.assertRaisesRegex(SafetyError,'UNSAFE_WHOLE_CLAIM_PROMOTION'):load(self.root)
 def test_no_v5_legacy_mutation(self):
  self.mutate(lambda x:x.update(formal_knowledge_B04_legacy_merge=True))
  with self.assertRaisesRegex(SafetyError,'UNSAFE_APPROVAL'):load(self.root)
 def test_false_same_scope_relation_is_blocked(self):
  self.mutate(lambda x:x['knowledge_overlay'][0].update(relationship_to_prior='SAME_SCOPE_VERIFIED'))
  with self.assertRaisesRegex(SafetyError,'MISREPRESENTED_DUPLICATE'):load(self.root)
 def test_invalid_video_claim_id_is_blocked(self):
  self.mutate(lambda x:x['knowledge_overlay'][0].update(source_claim_ids=['V5C9999']))
  with self.assertRaisesRegex(SafetyError,'NODE_UNAPPROVED_VIDEO_CLAIM'):load(self.root)
 def test_prior_provenance_cannot_be_falsified(self):
  p=self.root/'data/claims.jsonl';rows=[json.loads(x) for x in p.read_text().splitlines()]
  rows[65]['supporting_videos'].append('sz5N9WJS310');p.write_text('\n'.join(json.dumps(x) for x in rows))
  with self.assertRaisesRegex(SafetyError,'PRIOR_SOURCE_PROVENANCE_FABRICATED'):load(self.root)
 def test_retrieval_is_scoped_and_warns_personal(self):
  x=retrieval('ISA 만기시 연금계좌 전환 시 혜택은?',load(self.root))
  self.assertGreaterEqual(x['count'],1)
  self.assertTrue(x['not_suitable_for_personalized_advice'])
  self.assertFalse(x['formal_B04_merge_complete'])
  self.assertTrue(all(y['official_source_urls'] for y in x['matching_scoped_education_nodes']))
 def test_private_original_97_source_refs_hash_and_replay(self):
  if not BASE.is_dir(): self.skipTest('Private SRT/event chain deliberately absent in public CI')
  self.assertEqual(private_source_verify(load(self.root),BASE)['source_claims_directly_replayed'],97)
 def test_open_rule_cannot_be_promoted_with_missing_official_evidence(self):
  self.mutate(lambda x:next(c for c in x['claims'] if c['claim_id']=='V5C0266').update(review_status='OFFICIAL_NARROW_SUBFACT_VERIFIED'))
  with self.assertRaisesRegex(SafetyError,'VERDICT_COUNT_DRIFT'):load(self.root)

if __name__=='__main__':unittest.main()
