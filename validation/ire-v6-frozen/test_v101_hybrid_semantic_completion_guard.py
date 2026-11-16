"""Synthetic-only V101 source-first + original-cue full-context negative tests.

This fixture fabricates cue text and financing context; none is user SRT.
"""
from __future__ import annotations
from dataclasses import dataclass
import copy,unittest
from v101_hybrid_semantic_completion_guard import (
 SCOPE,EXPECTED_GAPS,EXPECTED_SPLITS,FALSE_FLAGS,STATUS,GAP_STATUS,
 SOURCE_ARCHIVE_SHA,V98_ARCHIVE_SHA,sha,digest,verify_v101)

@dataclass
class Cue:
 index:int
 start_ms:int
 end_ms:int
 text:str

MEANING='이것은 원본 자막이 아니라 합성시험으로 구성한 임의의 투자 사례에 대한 문맥 설명입니다.'
CAUTION='실제 금융규정이나 소득·보유상품 정보가 없으므로 개인 매매나 법적 사실을 인증하지 않습니다.'

class SyntheticV101(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.allcues={};cls.regs={};cls.selected=[];cls.routes=[];cls.readings=[];cls.gaps=[];cls.splits=[]
  cls.prior=set();cls.priorcues=set();cls.priorwins=set()
  for vid,w,no,firstid,lastid,priorities in SCOPE:
   start=(int(w[1:])-1)*40+1;end=start+39
   # Full video fixture is synthetic, with unique text and monotonically valid time.
   full=[Cue(i,i*1000,i*1000+400,f'가상의 금융 자막 {vid} {w} {i}번 조건 및 장기 금융 투자 발화')
         for i in range(1,end+3)]
   cls.allcues[vid]=full
   win_gaps={i for v,wi,i in EXPECTED_GAPS if (v,wi)==(vid,w)}
   assigned=[i for i in range(start,end+1) if i not in win_gaps]
   ids=[f'C{i:05d}' for i in range(firstid,lastid+1)]
   buckets=[[] for _ in ids]
   for j,i in enumerate(assigned):buckets[j%len(ids)].append(i)
   # Prefix fixture deliberately groups scattered cue indices: verifier checks
   # source identity and complete cue coverage, not contiguity of synthetic text.
   cls.regs[vid]={w:[]};bycue={}
   for cid,ix in zip(ids,buckets):
    p={'claim_id':cid,'cue_indices':ix,
       'source_text_sha256':sha(' | '.join(full[i-1].text for i in ix))}
    cls.regs[vid][w].append(p)
    for i in ix:bycue[i]=cid
    cls.readings.append({'video_id':vid,'window_id':w,'parent_id':cid,
      'cue_indices':ix,'parent_sha256':p['source_text_sha256'],'status':STATUS,
      'semantic_kind':'OPINION','speaker_meaning_private':MEANING,
      'reviewer_scope_caution_private':CAUTION,**{f:False for f in FALSE_FLAGS}})
   for j,i in enumerate(range(start,end+1)):
    cue=full[i-1];context=[{'cue_index':q,'text_private':full[q-1].text}
               for q in range(max(1,i-2),min(len(full),i+2)+1)]
    cls.selected.append({'video_id':vid,'window_id':w,'cue_index':i,
      'start_ms':cue.start_ms,'end_ms':cue.end_ms,'source_text_private':cue.text,
      'cue_sha256':sha(cue.text),'context_private':context,'context_sha256':digest(context)})
    priority=j<priorities
    cls.routes.append({'video_id':vid,'window_id':w,'cue_index':i,
      'cue_sha256':sha(cue.text),'route':('PRIORITY_' if priority else 'BASELINE_')+
         ('UNASSIGNED_PENDING' if i in win_gaps else 'PARENT_PENDING'),
      'parent_id':bycue.get(i),'review_completed':False,
      'independent_gold':False,'fact_approved':False,'personalized_advice_approved':False})
   for i in sorted(win_gaps):
    cls.gaps.append({'video_id':vid,'window_id':w,'cue_index':i,
     'cue_sha256':sha(full[i-1].text),'status':GAP_STATUS,'speech_act':'ASSENT',
     'reason_private':'가상의 자막 조각으로 원문 금융 사실의 독립적 인증을 수행하지 않았습니다.',
     'negative_gold':False,'nonclaim_independently_proven':False,
     **{f:False for f in FALSE_FLAGS}})
   for v,wi,cid in sorted(EXPECTED_SPLITS):
    if (v,wi)!=(vid,w):continue
    p=next(p for p in cls.regs[vid][w] if p['claim_id']==cid)
    ix=p['cue_indices'];half=len(ix)//2
    if len(ix)<2:raise AssertionError('Fixture synthetic split parent has insufficient cues')
    parts=[{'cue_indices':segment,'meaning_private':'가상 부모 발화의 일부에 해당하는 잠정 주제 구간입니다.',
            'independent_fact_approved':False,'negative_gold':False} for segment in (ix[:half],ix[half:])]
    cls.splits.append({'video_id':vid,'window_id':w,'parent_id':cid,
     'status':'PROVISIONAL_WITHIN_PARENT_SEGMENTATION_NOT_ATOMIC_GOLD',
     'provisional_parts':parts,**{f:False for f in FALSE_FLAGS}})

 def check(self,**changes):
  args={'selected_cues':self.selected,'original_cues_by_video':self.allcues,
   'registry_by_video':self.regs,'v98_routes':self.routes,'readings':self.readings,
   'gaps':self.gaps,'split_rows':self.splits,
   'prior_shadow_parent_keys':self.prior,
   'prior_v96_cue_keys':self.priorcues,'prior_v97_windows':self.priorwins,
   'owner_archive_sha':SOURCE_ARCHIVE_SHA,
   'previous_private_archive_sha':V98_ARCHIVE_SHA}
  args.update(changes)
  return verify_v101(**args)

 def expect_bad(self,**changes):
  with self.assertRaises(ValueError):self.check(**changes)
 def test_all_240_81_7_10_133_107(self):
  r=self.check();self.assertEqual((r['source_bound_cues_context_reviewed_chat'],
    r['source_bound_parent_draft_readings_chat'],r['source_bound_gap_speech_acts_chat'],
    r['provisional_parent_subclaim_segmentations_chat']), (240,81,7,10))
  self.assertEqual((r['prioritized_cues_processed_chat'],r['fallback_cues_processed_chat']), (133,107))
  self.assertEqual(r['zero_risk_windows_context_reviewed'],2)
  self.assertFalse(r['independent_gold']);self.assertFalse(r['p0_go'])
 def test_drop_source(self):self.expect_bad(selected_cues=self.selected[:-1])
 def test_duplicate_source(self):
  x=copy.deepcopy(self.selected);x[-1]=copy.deepcopy(x[0]);self.expect_bad(selected_cues=x)
 def test_corrupt_text(self):
  x=copy.deepcopy(self.selected);x[0]['source_text_private']='위조';self.expect_bad(selected_cues=x)
 def test_corrupt_cue_digest(self):
  x=copy.deepcopy(self.selected);x[0]['cue_sha256']='0'*64;self.expect_bad(selected_cues=x)
 def test_corrupt_time(self):
  x=copy.deepcopy(self.selected);x[0]['start_ms']+=1;self.expect_bad(selected_cues=x)
 def test_corrupt_context_text(self):
  x=copy.deepcopy(self.selected);x[0]['context_private'][0]['text_private']='위조';self.expect_bad(selected_cues=x)
 def test_corrupt_context_digest(self):
  x=copy.deepcopy(self.selected);x[0]['context_sha256']='f'*64;self.expect_bad(selected_cues=x)
 def test_prior_v97_duplicate_window(self):
  self.expect_bad(prior_v97_windows={(SCOPE[0][0],SCOPE[0][1])})
 def test_prior_v96_duplicate_cue(self):
  v,w=SCOPE[0][:2];self.expect_bad(prior_v96_cue_keys={(v,self.selected[0]['cue_index'])})
 def test_prior_parent_duplicate(self):
  v,w=SCOPE[0][:2];self.expect_bad(prior_shadow_parent_keys={(v,w,'C00137')})
 def test_drop_v98_route(self):self.expect_bad(v98_routes=self.routes[:-1])
 def test_route_sha_corruption(self):
  x=copy.deepcopy(self.routes);x[0]['cue_sha256']='0'*64;self.expect_bad(v98_routes=x)
 def test_route_faked_completed(self):
  x=copy.deepcopy(self.routes);x[0]['review_completed']=True;self.expect_bad(v98_routes=x)
 def test_route_faked_approved(self):
  x=copy.deepcopy(self.routes);x[0]['fact_approved']=True;self.expect_bad(v98_routes=x)
 def test_route_drops_fallback_cue(self):
  x=copy.deepcopy(self.routes);i=next(i for i,v in enumerate(x) if v['route'].startswith('BASELINE_'));x.pop(i)
  self.expect_bad(v98_routes=x)
 def test_route_fake_risk_count(self):
  x=copy.deepcopy(self.routes);i=next(i for i,v in enumerate(x) if v['route'].startswith('BASELINE_'))
  x[i]['route']=x[i]['route'].replace('BASELINE_','PRIORITY_');self.expect_bad(v98_routes=x)
 def test_parent_count_missing(self):self.expect_bad(readings=self.readings[:-1])
 def test_parent_duplicate_reading(self):
  x=copy.deepcopy(self.readings);x[-1]=copy.deepcopy(x[0]);self.expect_bad(readings=x)
 def test_parent_hash_bad(self):
  x=copy.deepcopy(self.readings);x[0]['parent_sha256']='0'*64;self.expect_bad(readings=x)
 def test_parent_reason_missing(self):
  x=copy.deepcopy(self.readings);x[0]['speaker_meaning_private']='...';self.expect_bad(readings=x)
 def test_parent_fake_gold(self):
  x=copy.deepcopy(self.readings);x[0]['independent_gold']=True;self.expect_bad(readings=x)
 def test_parent_fake_current_law(self):
  x=copy.deepcopy(self.readings);x[0]['current_law_certified']=True;self.expect_bad(readings=x)
 def test_gap_missing(self):self.expect_bad(gaps=self.gaps[:-1])
 def test_gap_fake_negative_gold(self):
  x=copy.deepcopy(self.gaps);x[0]['negative_gold']=True;self.expect_bad(gaps=x)
 def test_gap_forced_approval(self):
  x=copy.deepcopy(self.gaps);x[0]['financial_fact_approved']=True;self.expect_bad(gaps=x)
 def test_split_missing(self):self.expect_bad(split_rows=self.splits[:-1])
 def test_split_overlap(self):
  x=copy.deepcopy(self.splits);x[0]['provisional_parts'][1]['cue_indices']=x[0]['provisional_parts'][0]['cue_indices']
  self.expect_bad(split_rows=x)
 def test_split_source_incomplete(self):
  x=copy.deepcopy(self.splits);x[0]['provisional_parts'][1]['cue_indices']=[];self.expect_bad(split_rows=x)
 def test_split_false_gold(self):
  x=copy.deepcopy(self.splits);x[0]['provisional_parts'][0]['independent_fact_approved']=True;self.expect_bad(split_rows=x)
 def test_wrong_owner_archive(self):self.expect_bad(owner_archive_sha='0'*64)
 def test_wrong_private_v98_archive(self):self.expect_bad(previous_private_archive_sha='0'*64)
 def test_missing_selected_zero_signal_window(self):
  x=[c for c in self.selected if not (c['video_id']=='6VEfKF7BzZU' and c['window_id']=='W00029')]
  self.expect_bad(selected_cues=x)
 def test_prior_flags_type(self):self.expect_bad(prior_v96_cue_keys=[])
 def test_crosswindow_parent_ref(self):
  x=copy.deepcopy(self.regs);vid,w=SCOPE[0][:2];x[vid][w][0]['cue_indices']=[1];self.expect_bad(registry_by_video=x)

if __name__=='__main__':unittest.main()