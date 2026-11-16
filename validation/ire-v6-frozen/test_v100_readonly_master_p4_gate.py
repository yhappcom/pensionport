"""V100 pure synthetic read-only integration denial and content pin tests."""
import copy,unittest
from v98_hybrid_source_guard import sha,digest
from v100_readonly_master_p4_gate import readonly_preview,MASTER_BLOB_SHA,P4_BLOB_SHA,MASTER_PATH,P4_PATH,ALLOW_NODES,ACTUAL_P4_NODE_IDS

class TestV100(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.master={'git_blob_sha':MASTER_BLOB_SHA,'path':MASTER_PATH,
   'claim_ids':[f'GOMHEE-C{i:02d}' for i in range(1,117)],
   'fact_approvals_from_metadata_index':0}
  nids=list(ACTUAL_P4_NODE_IDS)
  cls.p4={'git_blob_sha':P4_BLOB_SHA,'path':P4_PATH,'nodes':[
   {'knowledge_id':n,'status':('SCOPED_EDUCATION_OFFLINE_OFFICIAL_EXTRACT_REPLAYED' if n.startswith('V5-') else 'EXISTING_PROVISIONAL_EDUCATION_NOT_CURRENT_LAW_APPROVAL')} for n in nids],
   'P3_formal_claim_approvals':0,'B04_formal_master_merges':0}
  cls.entries=[{'video_id':'SYNTH_V','window_id':'W00001','first_cue':i+1,'last_cue':i+1,
    'source_span_sha256':sha(f'synthethic_span_{i}'),
    'related_education_ids':['EDU-DCA-DIVERSIFICATION'] if i in (2,9) else [],
    'relation':'RELATED_CANDIDATE_NOT_EQUIVALENT' if i in (2,9) else 'UNRESOLVED_NO_MATCH',
    **{k:False for k in ('fact_approved','auto_merge','personal_advice_approved',
                         'independent_gold','source_semantics_certified','legal_current_approved')}}
   for i in range(20)]
 def audit(self,entries=None,master=None,p4=None,before=None,after=None):
  ident=digest([MASTER_BLOB_SHA,P4_BLOB_SHA,self.master['claim_ids'],list(ACTUAL_P4_NODE_IDS)])
  before=ident if before is None else before
  after=ident if after is None else after
  return readonly_preview(self.entries if entries is None else entries,
    self.master if master is None else master,self.p4 if p4 is None else p4,
    source_sha='a'*64,approved_identity_before=before,approved_identity_after=after)
 def test_approved_116_22_unchanged(self):
  r=self.audit();self.assertEqual(r['legacy_claims_read_only'],116)
  self.assertEqual(r['p4_education_nodes_read_only'],22)
  self.assertEqual(r['related_education_candidates'],2)
  self.assertEqual(r['unresolved_no_match'],18)
  self.assertFalse(r['p0_go']);self.assertEqual(r['formal_knowledge_merges'],0)
 def test_source_digest_only(self):
  r=self.audit();self.assertEqual(len(r['candidate_source_receipt_sha256']),64)
  self.assertNotIn('private_source_text',r)
 def test_master_blob_change(self):
  m=copy.deepcopy(self.master);m['git_blob_sha']='f'*40
  with self.assertRaises(ValueError):self.audit(master=m)
 def test_p4_blob_change(self):
  p=copy.deepcopy(self.p4);p['git_blob_sha']='0'*40
  with self.assertRaises(ValueError):self.audit(p4=p)
 def test_master_count_wrong(self):
  m=copy.deepcopy(self.master);m['claim_ids']=m['claim_ids'][:-1]
  with self.assertRaises(ValueError):self.audit(master=m)
 def test_master_duplicate_id(self):
  m=copy.deepcopy(self.master);m['claim_ids'][0]=m['claim_ids'][1]
  with self.assertRaises(ValueError):self.audit(master=m)
 def test_p4_node_missing(self):
  p=copy.deepcopy(self.p4);p['nodes'].pop()
  with self.assertRaises(ValueError):self.audit(p4=p)
 def test_p4_node_duplicate(self):
  p=copy.deepcopy(self.p4);p['nodes'][0]=p['nodes'][1]
  with self.assertRaises(ValueError):self.audit(p4=p)
 def test_p4_not_approved_fact(self):
  p=copy.deepcopy(self.p4);p['nodes'][0]['status']='AUTOMATICALLY_CERTIFIED'
  with self.assertRaises(ValueError):self.audit(p4=p)
 def test_master_fact_approval(self):
  m=copy.deepcopy(self.master);m['fact_approvals_from_metadata_index']=1
  with self.assertRaises(ValueError):self.audit(master=m)
 def test_p4_fact_approval(self):
  p=copy.deepcopy(self.p4);p['P3_formal_claim_approvals']=1
  with self.assertRaises(ValueError):self.audit(p4=p)
 def test_knowledge_mutation(self):
  with self.assertRaises(ValueError):self.audit(after='CHANGED')
 def test_duplicate_issue(self):
  entries=copy.deepcopy(self.entries);entries[1]=entries[0]
  with self.assertRaises(ValueError):self.audit(entries=entries)
 def test_issue_missing(self):
  with self.assertRaises(ValueError):self.audit(entries=self.entries[:-1])
 def test_issue_wrong_source(self):
  entries=copy.deepcopy(self.entries);entries[0]['source_span_sha256']=None
  with self.assertRaises(ValueError):self.audit(entries=entries)
 def test_forbidden_unknown_knowledge(self):
  entries=copy.deepcopy(self.entries);entries[0]['related_education_ids']=['SYNTH_EDU_1']
  with self.assertRaises(ValueError):self.audit(entries=entries)
 def test_false_semantic_equivalence(self):
  entries=copy.deepcopy(self.entries);entries[0]['relation']='EQUIVALENT'
  with self.assertRaises(ValueError):self.audit(entries=entries)
 def test_false_personal_advice(self):
  entries=copy.deepcopy(self.entries);entries[0]['personal_advice_approved']=True
  with self.assertRaises(ValueError):self.audit(entries=entries)
 def test_false_p3_merge(self):
  entries=copy.deepcopy(self.entries);entries[0]['auto_merge']=True
  with self.assertRaises(ValueError):self.audit(entries=entries)

if __name__=='__main__':unittest.main()