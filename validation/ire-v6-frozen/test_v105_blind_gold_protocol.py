import sys,unittest,copy
from dataclasses import dataclass
sys.path.insert(0,__file__.rsplit('/',1)[0])
from v105_blind_gold_protocol import lock_blind_cohort,prepare_external_review_forms,external_gold_gate,score_predictions,sha,digest
PIN='a'*64
@dataclass
class Cue:
 index:int
 start_ms:int
 end_ms:int
 text:str

def fixture():
 vids=['synthetic01','synthetic02','synthetic03','synthetic04'];c={};ws=[]
 for n,vid in enumerate(vids):
  c[vid]=[Cue(i,i*1000,i*1000+500,f'Synthetic independent evaluation text {vid} #{i}') for i in range(1,41)]
  ws.append({'video_id':vid,'window_id':'W00001','first_cue':1,'last_cue':40,'source_window_sha256':sha(' '.join(z.text for z in c[vid]))})
 lock={'schema':'V105_UNSEEN_OWNER_SOURCE_PRE_REVIEW_LOCK_V1','source_zip_sha256':PIN,'selected':ws,'cue_count':160,'independent_gold':False}
 return lock,c
class TestV105(unittest.TestCase):
 def pkt(self):
  lock,c=fixture();return lock,lock_blind_cohort(lock,c,source_archive_sha256=PIN,prior_windows=set())
 def test_lock(self):
  l,p=self.pkt();self.assertEqual(len(p['owner_private_cues']),160);self.assertFalse(p['independent_gold'])
 def test_blind_forms(self):
  l,p=self.pkt();q=prepare_external_review_forms(l,p);self.assertEqual(len(q),2);self.assertEqual(len(q[0]['cue_verdict_template']),160)
 def test_no_gold_no_reviewers(self):
  l,p=self.pkt();x=external_gold_gate(l,p);self.assertFalse(x['independent_gold']);self.assertIsNone(x['precision'])
 def test_no_gold_only_one(self):
  l,p=self.pkt();x=external_gold_gate(l,p,reviewer_a={});self.assertFalse(x['independent_gold'])
 def test_bad_source_hash(self):
  l,c=fixture();c['synthetic01'][0].text='tampered';
  with self.assertRaises(ValueError):lock_blind_cohort(l,c,source_archive_sha256=PIN,prior_windows=set())
 def test_prior_window_leak(self):
  l,c=fixture()
  with self.assertRaises(ValueError):lock_blind_cohort(l,c,source_archive_sha256=PIN,prior_windows={('synthetic01','W00001')})
 def test_wrong_archive(self):
  l,c=fixture()
  with self.assertRaises(ValueError):lock_blind_cohort(l,c,source_archive_sha256='b'*64,prior_windows=set())
 def test_duplicate_source(self):
  l,c=fixture();c['synthetic01'][0].index=2
  with self.assertRaises(ValueError):lock_blind_cohort(l,c,source_archive_sha256=PIN,prior_windows=set())
 def test_fake_gold(self):
  l,c=fixture();l['independent_gold']=True
  with self.assertRaises(ValueError):lock_blind_cohort(l,c,source_archive_sha256=PIN,prior_windows=set())
 def test_unverified_registry(self):
  l,p=self.pkt()
  with self.assertRaises(ValueError):external_gold_gate(l,p,{},{},{},trusted_registry={'verified_by_external_identity_authority':False})
 def test_score_blocked(self):
  l,p=self.pkt()
  with self.assertRaises(ValueError):score_predictions([],[],independent_gate_receipt={'independent_gold':False},equivalence_receipt={})
 def test_synthetic_distinct_prediction_ids_need_adjudicated_equivalence(self):
  gold=[{'atomic_id':'G-1','risk':'HIGH'},{'atomic_id':'G-2','risk':'LOW'}]
  pred=[{'atomic_id':'P-A'},{'atomic_id':'P-B'}]
  fake_gate={'independent_gold':True,'gold_locked':True,'gold_source_digest':digest(gold)}
  # Synthetic scoring arithmetic, NOT a real gold set or external reviewer.
  eq={'external_adjudication_verified':True,'gold_sha256':digest(gold),'prediction_sha256':digest(pred),
      'pairs':[{'gold_atomic_id':'G-1','predicted_atomic_id':'P-A','semantically_equivalent':True,
                'source_span_verified':True,'stance_preserved':True,'condition_exception_preserved':True,'adjudicator_attested':True}]}
  r=score_predictions(gold,pred,independent_gate_receipt=fake_gate,equivalence_receipt=eq)
  self.assertEqual((r['tp'],r['fp'],r['fn'],r['high_risk_fn']),(1,1,1,0))
 def test_reject_same_id_without_equivalence(self):
  gold=[{'atomic_id':'G-1','risk':'HIGH'}];pred=[{'atomic_id':'G-1'}]
  fake_gate={'independent_gold':True,'gold_locked':True,'gold_source_digest':digest(gold)}
  with self.assertRaises(ValueError):score_predictions(gold,pred,independent_gate_receipt=fake_gate,equivalence_receipt={})
 def test_two_same_id_blocked(self):
  l,p=self.pkt();z={'reviewer_id':'r','prediction_disclosed':False,'source_receipt_sha256':p['packet_sha256'],'externally_authenticated_signature_verified':True};a={**z,'adjudicator_id':'c'}
  with self.assertRaises(ValueError):external_gold_gate(l,p,z,z,a,trusted_registry={'verified_by_external_identity_authority':True,'verified_unique_people':['r','c']})
if __name__=='__main__':unittest.main()