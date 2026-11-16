"""V108 same-model double-read source audit: NOT independent gold/accuracy.

This public code processes injected private source rows; it never embeds SRT text.
V105 external reviewer 160-cue cohort remains separately sealed.
"""
from __future__ import annotations
from hashlib import sha256
from collections import Counter,defaultdict
import json,re

SCHEMA='V108_SAME_CHAT_TWO_PASS_CHANGE_LEDGER_NO_GOLD_V1'
SRC_SHA='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
VALID_STANCES={'HYPOTHESIS','NONCLAIM','QUESTION','OPEN_ASR','CONDITION','OPINION','ANALOGY','EDUCATIONAL_CLAIM','HISTORICAL_CLAIM','ANECDOTE','NUMERIC_CONDITION_OPEN','SOURCE_AUDIO_OPEN','ACCOUNT_TRANSFER_SCOPE_OPEN','NUMERIC_DISTRIBUTION_OPEN','CONDITIONAL_ADVICE_OPEN','REFERENT_AUDIO_OPEN','PRODUCT_STRUCTURE_OPEN','DISTRIBUTION_REINVESTMENT_OPEN','CMA_PRODUCT_RISK_OPEN','QUOTED_QUESTION_NOT_BUY_ADVICE','HISTORICAL_RANK_OPEN','MULTI_ENTITY_HISTORY_OPEN','THREE_TRANSACTION_SPLIT_OPEN','PAYMENT_PROCESS_CONDITION_OPEN','NET_BENEFIT_VS_PENALTY_OPEN','HYPERBOLE_NOT_LAW','CROSS_WINDOW_OPEN'}
def require(v,why):
 if not v:raise ValueError('V108_'+why)
def sha(x):return sha256(x if isinstance(x,bytes) else x.encode('utf-8')).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(x):return sha(canonical(x))

def validate_two_pass(lock, blind_scope, cues, parents, first, revisions, gaps, *, owner_source_sha, forbidden_prior_windows):
 require(owner_source_sha==SRC_SHA and lock.get('source_zip_sha256')==SRC_SHA,'SOURCE_ARCHIVE')
 require(lock.get('schema')=='V108_INTERNAL_NONINDEPENDENT_TWO_PASS_SCOPE_LOCK_V1','LOCK_SCHEMA')
 require(lock.get('source_window_count')==4 and lock.get('source_cues')==160 and lock.get('labeling_not_started_at_lock') is True,'LOCK_CENSUS')
 require(lock.get('v105_external_private_packets_accessed') is False and lock.get('independent_gold') is False and lock.get('p0_go') is False,'LOCK_FALSE_GOLD')
 selected=lock['selected'];scopes={(x['video_id'],x['window_id']):x for x in selected}
 require(len(scopes)==4 and len({x['video_id'] for x in selected})==4,'LOCK_DISTINCT')
 require(type(forbidden_prior_windows)==set and not (set(scopes)&forbidden_prior_windows),'PRIOR_WINDOW_REUSED')
 require(blind_scope.get('source_zip_sha256')==SRC_SHA and blind_scope.get('cue_count') in (None,160),'BLIND_ARCHIVE')
 sealed={(x['video_id'],x['window_id']) for x in blind_scope['selected']}
 require(len(sealed)==4 and not (set(scopes)&sealed),'V105_SEALED_OVERLAP')
 require(type(cues)==list and len(cues)==160,'CUE_COUNT')
 bycue={};bywindow=defaultdict(list)
 for r in cues:
  k=(r.get('video_id'),r.get('window_id'));i=r.get('cue_index')
  require(k in scopes and type(i) is int and (k[0],i) not in bycue,'CUE_SCOPE_OR_REPEAT')
  require(type(r.get('text_private')) is str and r['text_private'],'CUE_TEXT')
  require(r.get('cue_sha256')==sha(r['text_private']),'CUE_SHA')
  require(type(r.get('start_ms')) is int and type(r.get('end_ms')) is int and r['start_ms']<=r['end_ms'],'CUE_TIME')
  bycue[(k[0],i)]=r;bywindow[k].append(r)
 for k,scope in scopes.items():
  rows=sorted(bywindow.get(k,[]),key=lambda x:x['cue_index'])
  require(len(rows)==40 and [x['cue_index'] for x in rows]==list(range(scope['first_cue'],scope['last_cue']+1)),'WINDOW_40_OR_INDEX')
  require(sha(' '.join(x['text_private'] for x in rows))==scope['source_window_sha256'],'WINDOW_SHA')
 require(len(parents)==63 and type(first)==list and len(first)==63,'PARENTS_63')
 parent_bykey={};assigned=set();parent_byclaim={}
 for p in parents:
  k=(p.get('video_id'),p.get('window_id'));cid=p.get('claim_id')
  require(k in scopes and type(cid) is str and re.fullmatch('C[0-9]{5}',cid),'PARENT_ID')
  full=(*k,cid);require(full not in parent_bykey and cid not in parent_byclaim,'PARENT_DUP')
  ids=p.get('cue_indices');require(type(ids) is list and bool(ids) and len(ids)==len(set(ids)),'PARENT_IDS')
  strings=[]
  for i in ids:
   require((k[0],i) in bycue and (k[0],i) not in assigned,'PARENT_OVERLAP_OR_MISSING')
   assigned.add((k[0],i));strings.append(bycue[(k[0],i)]['text_private'])
  require(p.get('source_text_sha256')==sha(' | '.join(strings)),'PARENT_SHA')
  parent_bykey[full]=p;parent_byclaim[cid]=p
 for k,s in scopes.items():require(sum(p['video_id']==k[0] and p['window_id']==k[1] for p in parents)==s['draft_parents'],'PARENT_CENSUS')
 actual_gap=set(bycue)-assigned
 require(type(gaps)==list and len(gaps)==len(actual_gap),'GAP_COUNT')
 seen_gaps=set()
 for g in gaps:
  k=(g['video_id'],g['cue_index']);require(k in actual_gap and k not in seen_gaps,'GAP_MISMATCH');seen_gaps.add(k)
  require(g.get('cue_sha256')==bycue[k]['cue_sha256'] and type(g.get('discourse_note_private')) is str and len(g['discourse_note_private'])>=10,'GAP_NOTE')
 require(seen_gaps==actual_gap,'UNCHECKED_GAP')
 fby={};st=Counter()
 for r in first:
  cid=r.get('claim_id');p=parent_byclaim.get(cid)
  require(p is not None and cid not in fby,'FIRST_DUP_OR_UNKNOWN')
  require(r.get('video_id')==p['video_id'] and r.get('window_id')==p['window_id'] and r.get('cue_indices')==p['cue_indices'],'FIRST_SOURCE_SCOPE')
  require(r.get('source_text_sha256')==p['source_text_sha256'],'FIRST_PARENT_SHA')
  require(r.get('stance') in VALID_STANCES,'FIRST_STANCE')
  require(all(type(r.get(k)) is str and len(r[k])>=10 for k in ('meaning_private','scope_limit_private')),'FIRST_CONTEXT')
  require(r.get('independent_gold') is False and r.get('fact_approved') is False,'FALSE_FIRST_APPROVAL')
  fby[cid]=r;st[r['stance']]+=1
 require(set(fby)==set(parent_byclaim),'FIRST_ALL_PARENTS')
 require(type(revisions)==list and len(revisions)==18,'REVISIONS_18')
 revised=set();newst=Counter(st)
 for r in revisions:
  cid=r.get('claim_id');require(cid in fby and cid not in revised,'REVISION_DUP_OR_UNKNOWN');revised.add(cid)
  require(r.get('pass_a_record_sha256')==digest(fby[cid]),'PASS_A_MUTATED')
  require(r.get('after_stance') in VALID_STANCES and r['after_stance']!=fby[cid]['stance'],'REVISION_NO_CHANGE')
  require(type(r.get('adversarial_reason_private')) is str and len(r['adversarial_reason_private'])>=24,'REVISION_REASON')
  require(r.get('independent_reviewer') is False and r.get('independent_gold') is False and r.get('certified_error') is False,'FALSE_REVISION_GOLD')
  newst[fby[cid]['stance']]-=1;newst[r['after_stance']]+=1
 return {'schema':SCHEMA,'source_cues':len(cues),'draft_parent_candidates':len(parents),'original_cues_without_parent':len(actual_gap),'pass_a_parent_notes':len(first),'pass_b_self_revision_candidates':len(revisions),'pass_a_unchanged_parent_notes':len(first)-len(revisions),'v105_external_cohort_overlap':0,
  'first_pass_stance_counts':dict(sorted(st.items())),'final_provisional_stance_counts':{k:v for k,v in sorted(newst.items()) if v},
  'source_cues_sha256':digest(sorted((r['video_id'],r['cue_index'],r['cue_sha256']) for r in cues)),
  'pass_a_notes_sha256':digest(sorted((r['claim_id'],digest(r)) for r in first)),
  'pass_b_revision_sha256':digest(sorted((r['claim_id'],digest(r)) for r in revisions)),
  'unassigned_cue_sha256':digest(sorted((r['video_id'],r['cue_index'],r['cue_sha256']) for r in gaps)),
  'same_chat_model_not_independent_review':True,'blind_external_reviewer_submissions_received':0,
  'independent_gold':False,'certified_precision':None,'certified_recall':None,'high_risk_recall':None,'full_financial_semantic_recall_certified':False,'p0_go':False,'new_approved_knowledge':0}