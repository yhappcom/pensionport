import sys,unittest,copy,json,pathlib,hashlib
from v97_paired_source_guard import source_first_paired_check,check_public_receipt,WINDOWS,SOURCE_ARCHIVE,sha

class TestV97(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.source=[];cls.parents=[];cls.flags=[];cls.issues=[]
  for v,w,pr,fg in WINDOWS:
   first=(int(w[1:])-1)*40+1
   texts={i:f'Original-style synthetic fragment {i} in {w}' for i in range(first,first+40)}
   for i,t in texts.items():cls.source.append({'video_id':v,'window_id':w,'cue_index':i,'text_private':t,'cue_sha256':sha(t)})
   for j in range(pr):
    ids=list(range(first+j,first+j+1))
    cls.parents.append({'video_id':v,'window_id':w,'claim_id':f'C{j+1:05}',
        'cue_indices':ids,'source_text_sha256':sha(' | '.join(texts[i] for i in ids))})
   for j in range(fg):
    i=first+j
    cls.flags.append({'video_id':v,'window_id':w,'cue_index':i,'kind':'QUALIFIER_REVIEW','cue_sha256':sha(texts[i])})
  for j in range(20):
   v,w,_,_=WINDOWS[j%4];a=(int(w[1:])-1)*40+1+15+(j//4)
   t=next(x for x in cls.source if x['video_id']==v and x['cue_index']==a)
   cls.issues.append({'video_id':v,'window_id':w,'first_cue':a,'last_cue':a,
     'source_span_sha256':sha(t['cue_sha256']),'independent_gold':False,
     'actual_error_certified':False,'note_private':'This is only a synthetic single-model review hypothesis.'})
 def runcheck(self,source=None,parents=None,flags=None,issues=None,prior=None):
  return source_first_paired_check(self.source if source is None else source,
    self.parents if parents is None else parents,self.flags if flags is None else flags,
    self.issues if issues is None else issues,original_archive_sha=SOURCE_ARCHIVE,
    prior_windows=set() if prior is None else prior)
 def test_complete(self):
  r=self.runcheck();self.assertEqual(r['cues'],200);self.assertEqual(r['parents'],77)
  self.assertEqual(r['alerts'],21);self.assertFalse(r['can_replace_full_source_review'])
 def test_positive_internal_issue_alert_overlap(self):
  x=copy.deepcopy(self.issues)
  v,w,_,_=WINDOWS[0]; a=(int(w[1:])-1)*40+1
  matching=next(r for r in self.source if r['video_id']==v and r['cue_index']==a)
  x[0]={'video_id':v,'window_id':w,'first_cue':a,'last_cue':a,
      'source_span_sha256':sha(matching['cue_sha256']),
      'independent_gold':False,'actual_error_certified':False,
      'note_private':'Synthetic source-first scope caution, never independent truth.'}
  r=self.runcheck(issues=x)
  self.assertEqual(r['internal_issue_spans_with_alert'],1)
 def test_source_missing(self):
  with self.assertRaises(ValueError):self.runcheck(source=self.source[:-1])
 def test_source_spoof(self):
  x=copy.deepcopy(self.source);x[0]['text_private']='tampered';
  with self.assertRaises(ValueError):self.runcheck(source=x)
 def test_source_duplicate(self):
  x=copy.deepcopy(self.source);x[0]=copy.deepcopy(x[1]);
  with self.assertRaises(ValueError):self.runcheck(source=x)
 def test_prior_reviewed_window(self):
  with self.assertRaises(ValueError):self.runcheck(prior={(WINDOWS[0][0],WINDOWS[0][1])})
 def test_parent_missing(self):
  with self.assertRaises(ValueError):self.runcheck(parents=self.parents[:-1])
 def test_parent_duplicate(self):
  x=copy.deepcopy(self.parents);x[0]=copy.deepcopy(x[1]);
  with self.assertRaises(ValueError):self.runcheck(parents=x)
 def test_parent_sha_change(self):
  x=copy.deepcopy(self.parents);x[0]['source_text_sha256']='0'*64
  with self.assertRaises(ValueError):self.runcheck(parents=x)
 def test_parent_cross_window(self):
  x=copy.deepcopy(self.parents);x[0]['cue_indices']=[1]
  with self.assertRaises(ValueError):self.runcheck(parents=x)
 def test_flag_missing(self):
  with self.assertRaises(ValueError):self.runcheck(flags=self.flags[:-1])
 def test_flag_sha_fake(self):
  x=copy.deepcopy(self.flags);x[0]['cue_sha256']='0'*64
  with self.assertRaises(ValueError):self.runcheck(flags=x)
 def test_duplicate_flag(self):
  x=copy.deepcopy(self.flags);x[0]=copy.deepcopy(x[1]);
  with self.assertRaises(ValueError):self.runcheck(flags=x)
 def test_issue_missing(self):
  with self.assertRaises(ValueError):self.runcheck(issues=self.issues[:-1])
 def test_fake_gold(self):
  x=copy.deepcopy(self.issues);x[0]['independent_gold']=True
  with self.assertRaises(ValueError):self.runcheck(issues=x)
 def test_issue_source_sha(self):
  x=copy.deepcopy(self.issues);x[0]['source_span_sha256']='0'*64
  with self.assertRaises(ValueError):self.runcheck(issues=x)
 def test_issue_short_note(self):
  x=copy.deepcopy(self.issues);x[0]['note_private']='bad'
  with self.assertRaises(ValueError):self.runcheck(issues=x)
 def test_wrong_owner_zip(self):
  with self.assertRaises(ValueError):source_first_paired_check(self.source,self.parents,self.flags,self.issues,original_archive_sha='f'*64,prior_windows=set())
 def test_public_receipt(self):
  s={'v91_baseline_commit':'732efc8c2dffcd64828de5188168a694f0133ce6','v96_comparison_commit':'6825d90fefcea3645dbad60e3c2051d3f41475b4','owner_archive_sha256':SOURCE_ARCHIVE,'independent_gold':False,'p0_go':False}
  r={'gold_independent':False,'source_archive_sha256':SOURCE_ARCHIVE,'p0_go':False,'original_cues':200,'v91_provisional_draft_parents':77,'v96_cue_risk_signal_events':21,'internal_source_first_issue_spans_not_gold':20,'v96_internal_issue_spans_any_alert':12,'v96_internal_issue_spans_no_alert':8,'certified_financial_precision':None,'certified_financial_recall':None,'model_semantic_token_time_measured':False,'human_review_time_measured':False,'v96_unique_cues_within_7_neighbor_envelopes':145}
  self.assertTrue(check_public_receipt(r,s)['structure_checked'])
  bad=copy.deepcopy(r);bad['certified_financial_recall']=1
  with self.assertRaises(ValueError):check_public_receipt(bad,s)
if __name__=='__main__': unittest.main()