"""Proof-of-custody guard for V103 locked same-host risk audit; NEVER independent gold."""
from __future__ import annotations
import hashlib,json

def sha(x):return hashlib.sha256(x.encode('utf-8') if isinstance(x,str) else x).hexdigest()
def digest(x):return sha(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False))
def require(c,why):
 if not c: raise ValueError('V103_EVAL_'+why)

def audit_holdout(*,locked,forecast,cue_rows,parent_rows,observations,observed_risks):
 require(type(locked)==dict and type(forecast)==dict,'INPUT_TYPE')
 scopes={(s['video_id'],s['window_id']):s for s in locked['selected']};require(len(scopes)==5,'LOCKED_SCOPE')
 require(type(cue_rows)==list and len(cue_rows)==200,'SOURCE_200')
 require(type(parent_rows)==list and len(parent_rows)==57,'PARENT_57')
 require(type(observations)==list and len(observations)>0,'SOURCE_ANNOTATIONS')
 bycue={};group={}
 for row in cue_rows:
  key=(row.get('video_id'),row.get('window_id'))
  idx=row.get('cue_index')
  require(key in scopes and type(idx) is int,'SOURCE_KEY')
  s=scopes[key];require(s['first_cue']<=idx<=s['last_cue'],'SOURCE_RANGE')
  require(type(row.get('source_text_private')) is str,'SOURCE_TEXT')
  require(row.get('cue_sha256')==sha(row['source_text_private']),'SOURCE_SHA')
  k=(key[0],idx);require(k not in bycue,'DUPLICATE_SOURCE');bycue[k]=row
  group.setdefault(key,[]).append(row)
 require(len(group)==5 and all(len(v)==40 for v in group.values()),'CENSUS_40')
 for key,rs in group.items():
  s=scopes[key];order=sorted(rs,key=lambda x:x['cue_index'])
  require([r['cue_index'] for r in order]==list(range(s['first_cue'],s['last_cue']+1)),'SOURCE_GAP')
  require(sha(' '.join(r['source_text_private'] for r in order))==s['source_window_sha256'],'WINDOW_SHA')
 pseen=set()
 for p in parent_rows:
  key=(p.get('video_id'),p.get('window_id'));cid=p.get('claim_id');ids=p.get('cue_indices')
  require(key in scopes and isinstance(cid,str) and isinstance(ids,list) and ids,'PARENT')
  require((key,cid) not in pseen,'DUPLICATE_PARENT');pseen.add((key,cid))
  require(all((key[0],i) in bycue for i in ids),'PARENT_SOURCE')
  require(sha(' | '.join(bycue[(key[0],i)]['source_text_private'] for i in ids))==p.get('source_text_sha256'),'PARENT_SHA')
 for key,s in scopes.items():
  require(sum(p['video_id']==key[0] and p['window_id']==key[1] for p in parent_rows)==s['draft_parent_count'],'PARENT_CENSUS')
 fseen={};baseline=[];new=[]
 for f in forecast.values():
  key=(f['video_id'],f['window_id']);require(key in scopes and key not in fseen,'FORECAST_SCOPE');fseen[key]=True
  require(f['source_sha256']==scopes[key]['source_window_sha256'],'FORECAST_SHA')
  for label,arr,collector in [('v93',f['v93_flags'],baseline),('v103',f['v103_flags'],new)]:
   for a in arr:
    k=(key[0],a['cue_index']);require(k in bycue and a['cue_sha256']==bycue[k]['cue_sha256'],'FORECAST_CUE_SHA')
    require(a.get('independent_fact_approved') in (None,False) and a.get('automated_true_error_certified') in (None,False),'FAKE_FORECAST_APPROVAL')
    collector.append({"video_id":f["video_id"],**a})
 require(len(fseen)==5,'FORECAST_MISSING')
 seen=set();iscore=[]
 for row in observations:
  key=(row.get('video_id'),row.get('window_id'))
  first=row.get('first_cue');last=row.get('last_cue')
  require(key in scopes and type(first) is int and type(last) is int and first<=last,'OBS_SCOPE')
  x=(key,first,last);require(x not in seen,'OBS_DUP');seen.add(x)
  require(all((key[0],i) in bycue for i in range(first,last+1)),'OBS_SOURCE_GAP')
  crypt=sha(''.join(bycue[(key[0],i)]['cue_sha256'] for i in range(first,last+1)))
  require(row.get('source_span_sha256')==crypt,'OBS_SOURCE_SHA')
  require(type(row.get('note_private')) is str and len(row['note_private'])>=20,'OBS_NOTE')
  require(type(row.get('needed_evidence_private')) is str and len(row['needed_evidence_private'])>=10,'OBS_EVIDENCE')
  for flag in ['independent_gold','actual_finance_error_certified','personal_advice_approved','p0_go']:
   require(row.get(flag) is False,'FALSE_APPROVAL_'+flag)
  def anyhit(arr):return any(a['video_id']==key[0] and first<=a['cue_index']<=last for a in arr)
  iscore.append({'key':key,'first':first,'last':last,'old_hit':anyhit(baseline),'new_hit':anyhit(new)})
 old=sum(z['old_hit'] for z in iscore);extended=sum(z['new_hit'] for z in iscore);union=sum(z['old_hit'] or z['new_hit'] for z in iscore)
 require(len(baseline)==observed_risks['v93_events'] and len(new)==observed_risks['v103_events'],'PREDICTION_CENSUS')
 require(union>=max(old,extended),'OVERLAP_MONOTONIC')
 return {'schema':'V103_SAME_HOST_SOURCE_PINNED_HOLDOUT_MEASUREMENT_NOT_INDEPENDENT_GOLD_V1','original_cues_reviewed_internal':len(cue_rows),
    'v33_draft_parents_source_checked':len(parent_rows),'review_windows':len(scopes),'same_host_issue_spans_not_gold':len(observations),
    'v93_alert_events':len(baseline),'v103_alert_events':len(new),
    'v93_internal_issue_spans_directly_flagged':old,'v103_internal_issue_spans_directly_flagged':extended,
    'v93_v103_union_internal_issue_spans_directly_flagged':union,'internal_issue_spans_without_either_signal':len(observations)-union,
    'source_receipt_sha256':digest(sorted((r['video_id'],r['cue_index'],r['cue_sha256']) for r in cue_rows)),
    'annotation_digest_sha256':digest(sorted((r['video_id'],r['window_id'],r['first_cue'],r['last_cue'],r['source_span_sha256'],sha(r['note_private'])) for r in observations)),
    'blind_independent_gold':False,'precision':None,'recall':None,'high_risk_recall':None,'p0_go':False,
    'full_source_semantic_recall_certified':False,'formal_finance_approval_count':0}