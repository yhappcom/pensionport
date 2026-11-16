"""V98 adversarial synthetic-only tests. No owner cue text or financial claims."""
import copy,unittest
from v98_hybrid_source_guard import SCOPE,hybrid_route,verify_hybrid_receipt,sha

# Only relative positions of synthetic alert fixtures are encoded; no real text.
ALERT_POS={
 'W00026':(4,10,21,35,39),'W00018':(9,11,23,32),
 'W00117':(6,7,12,18,23,29,31,32,40),'W00053':(7,8,20),
 'W00096':()}
GAP_POS={'W00026':(37,), 'W00018':(4,7,39),
         'W00117':(26,), 'W00053':(23,), 'W00096':(23,)}

class Fixture:
 def __init__(self):
  self.source=[];self.parents=[];self.alerts=[]
  for v,w,np,nf in SCOPE:
   first=(int(w[1:])-1)*40+1
   gaps={first+n-1 for n in GAP_POS[w]}
   ids=[i for i in range(first,first+40) if i not in gaps]
   assert len(ids)>=np
   # synthetic parents partition all assigned cues, no overlap
   batches=[[i] for i in ids[:np-1]]+[ids[np-1:]]
   pids={}
   for j,batch in enumerate(batches,1):
    cid=f'SYNTH_PARENT_{j:02}'
    for idx in batch:pids[idx]=cid
    self.parents.append({'video_id':v,'window_id':w,'claim_id':cid,
       'cue_indices':batch,'source_text_sha256':sha(' | '.join(self.text(w,k) for k in batch))})
   for k in range(first,first+40):
    t=self.text(w,k)
    self.source.append({'video_id':v,'window_id':w,'cue_index':k,
     'source_text_private':t,'source_sha256':sha(t),'start_ms':k*100,'end_ms':k*100+90,
     'parent_ids':[pids[k]] if k in pids else []})
   for off in ALERT_POS[w]:
    i=first+off-1
    self.alerts.append({'video_id':v,'window_id':w,'cue_index':i,
       'kind':'QUALIFIER_REVIEW','cue_sha256':sha(self.text(w,i))})
 @staticmethod
 def text(w,i):return f'SYNTHETIC_ONLY_{w}_{i}'
 def route(self,source=None,parents=None,alerts=None,**kwargs):
  return hybrid_route(self.source if source is None else source,
   self.parents if parents is None else parents,self.alerts if alerts is None else alerts,**kwargs)

class TestV98(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.f=Fixture();cls.ok=cls.f.route()
 def test_all_cues_routed_pending(self):
  d=self.ok;self.assertEqual(d['source_cue_count'],200);self.assertEqual(d['draft_parent_count'],77)
  self.assertEqual(d['priority_cues'],145);self.assertEqual(d['baseline_fallback_cues'],55)
  self.assertTrue(d['all_original_cues_routed']);self.assertFalse(d['all_original_cues_semantically_reviewed'])
 def test_parent_worklist_and_gap_count(self):
  self.assertEqual(len(self.ok['private_parent_worklist']),77)
  self.assertEqual(self.ok['unassigned_cues'],7)
  self.assertTrue(all(p['draft_parent_review_completed'] is False for p in self.ok['private_parent_worklist']))
 def test_zero_signal_window_fallback(self):
  xs=[x for x in self.ok['private_cue_routes'] if x['window_id']=='W00096']
  self.assertEqual(len(xs),40);self.assertTrue(all(x['route'].startswith('BASELINE_') for x in xs))
 def test_receipt(self):
  public={k:v for k,v in self.ok.items() if not k.startswith('private_')}
  self.assertTrue(verify_hybrid_receipt(public,self.ok))
 def test_private_leak_block(self):
  p={k:v for k,v in self.ok.items() if not k.startswith('private_')};p['private_source']='sensitive'
  with self.assertRaises(ValueError):verify_hybrid_receipt(p,self.ok)
 def test_fake_gold_block(self):
  p={k:v for k,v in self.ok.items() if not k.startswith('private_')};p['independent_gold']=True
  with self.assertRaises(ValueError):verify_hybrid_receipt(p,self.ok)
 def test_fake_reviewed_block(self):
  p={k:v for k,v in self.ok.items() if not k.startswith('private_')};p['review_completed_cues']=200
  with self.assertRaises(ValueError):verify_hybrid_receipt(p,self.ok)
 def test_priority_drift_receipt(self):
  p={k:v for k,v in self.ok.items() if not k.startswith('private_')};p['priority_cues']=200
  with self.assertRaises(ValueError):verify_hybrid_receipt(p,self.ok)
 def test_missing_cue(self):
  with self.assertRaises(ValueError):self.f.route(source=self.f.source[:-1])
 def test_duplicate_cue(self):
  rows=copy.deepcopy(self.f.source);rows[-1]=copy.deepcopy(rows[0])
  with self.assertRaises(ValueError):self.f.route(source=rows)
 def test_cue_text_spoof(self):
  rows=copy.deepcopy(self.f.source);rows[0]['source_text_private']='malicious rewrite'
  with self.assertRaises(ValueError):self.f.route(source=rows)
 def test_cue_time_corrupt(self):
  rows=copy.deepcopy(self.f.source);rows[0]['end_ms']=-10
  with self.assertRaises(ValueError):self.f.route(source=rows)
 def test_missing_parent(self):
  with self.assertRaises(ValueError):self.f.route(parents=self.f.parents[:-1])
 def test_duplicate_parent(self):
  rows=copy.deepcopy(self.f.parents);rows[-1]=copy.deepcopy(rows[0])
  with self.assertRaises(ValueError):self.f.route(parents=rows)
 def test_wrong_parent_span(self):
  rows=copy.deepcopy(self.f.parents);rows[0]['cue_indices']=[1]
  with self.assertRaises(ValueError):self.f.route(parents=rows)
 def test_parent_sha_mutation(self):
  rows=copy.deepcopy(self.f.parents);rows[0]['source_text_sha256']='f'*64
  with self.assertRaises(ValueError):self.f.route(parents=rows)
 def test_parent_overlap(self):
  rows=copy.deepcopy(self.f.parents);rows[1]['cue_indices']=[rows[0]['cue_indices'][0]]
  with self.assertRaises(ValueError):self.f.route(parents=rows)
 def test_unassigned_forged_parent(self):
  rows=copy.deepcopy(self.f.source);next(x for x in rows if x['window_id']=='W00026' and not x['parent_ids'])['parent_ids']=['FAKE']
  with self.assertRaises(ValueError):self.f.route(source=rows)
 def test_missing_alert(self):
  with self.assertRaises(ValueError):self.f.route(alerts=self.f.alerts[:-1])
 def test_duplicate_alert(self):
  rows=copy.deepcopy(self.f.alerts);rows[-1]=copy.deepcopy(rows[0])
  with self.assertRaises(ValueError):self.f.route(alerts=rows)
 def test_alert_text_sha_spoof(self):
  rows=copy.deepcopy(self.f.alerts);rows[0]['cue_sha256']='0'*64
  with self.assertRaises(ValueError):self.f.route(alerts=rows)
 def test_archive_mismatch(self):
  with self.assertRaises(ValueError):self.f.route(archive_sha='f'*64)
 def test_out_of_scope_alert(self):
  rows=copy.deepcopy(self.f.alerts);rows[0]['cue_index']=1
  with self.assertRaises(ValueError):self.f.route(alerts=rows)
 def test_invalid_radius(self):
  with self.assertRaises(ValueError):self.f.route(radius=0)
 def test_false_approval_receipt(self):
  p={k:v for k,v in self.ok.items() if not k.startswith('private_')};p['financial_fact_approved']=True
  with self.assertRaises(ValueError):verify_hybrid_receipt(p,self.ok)

if __name__=='__main__':unittest.main()