"""V101 source-first completion *of 240-cue CHAT review*, not independent recall.

Public software guard. Run with owner-private SRT, V98 pending routes and manually
written contextual readings ONLY on the owner's system. No real speech or personal
advice is committed to GitHub. Synthetic tests check invariants and fail-closed.
"""
from __future__ import annotations
import hashlib,json,re
from collections import Counter

SOURCE_ARCHIVE_SHA='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
V98_ARCHIVE_SHA='e55d58b931cde6261fb76c79c7df011256a565f6e08ce5236894aa077c4edabd'
V98_HEAD_SHA='40469bbfada2fd47ebac6579f1d8a1896b056e5b'
V97_HEAD_SHA='c57f0611d809e6c9cc9d2446835184b73d3f6bde'
SCOPE=(
 ('sz5N9WJS310','W00012',1,137,147,26),
 ('6VEfKF7BzZU','W00029',2,368,383,0),
 ('OiDTNstaSpM','W00017',3,190,201,37),
 ('aNfGrcO6WPI','W00005',4,60,71,40),
 ('qtluAViPpsQ','W00016',5,211,226,30),
 ('4CQ4FjGT2gA','W00024',7,359,372,0),
)
EXPECTED_GAPS={('6VEfKF7BzZU','W00029',1143),('OiDTNstaSpM','W00017',663),
 ('OiDTNstaSpM','W00017',676),('aNfGrcO6WPI','W00005',178),
 ('qtluAViPpsQ','W00016',631),('qtluAViPpsQ','W00016',632),
 ('4CQ4FjGT2gA','W00024',931)}
EXPECTED_SPLITS={
 ('sz5N9WJS310','W00012','C00138'),('sz5N9WJS310','W00012','C00143'),
 ('6VEfKF7BzZU','W00029','C00374'),('OiDTNstaSpM','W00017','C00193'),
 ('aNfGrcO6WPI','W00005','C00062'),('aNfGrcO6WPI','W00005','C00067'),
 ('qtluAViPpsQ','W00016','C00218'),('qtluAViPpsQ','W00016','C00219'),
 ('4CQ4FjGT2gA','W00024','C00366'),('4CQ4FjGT2gA','W00024','C00372')}
ROUTES={'PRIORITY_PARENT_PENDING','BASELINE_PARENT_PENDING','PRIORITY_UNASSIGNED_PENDING','BASELINE_UNASSIGNED_PENDING'}
SPEECH={'ASSENT','INTERJECTION','LAUGHTER'}
STATUS='V101_SOURCE_CONTEXT_CHAT_REVIEWED_SHADOW_NOT_INDEPENDENT_GOLD'
GAP_STATUS='V101_GAP_SPEECH_ACT_CHAT_REVIEWED_NOT_NEGATIVE_GOLD'
FALSE_FLAGS=('independent_gold','financial_fact_approved','personal_trade_approved',
 'p0_go','formal_parent_merged','full_atomic_recall_certified','current_law_certified',
 'v75_historical_membership_verified','audio_verified')
SEMANTIC_KINDS={
 'ASR_UNCERTAIN','TAX_SCOPE_RISK','DISCOURSE_FRAGMENT','RHETORICAL_QUESTION',
 'CONDITIONAL_OPINION','HYPOTHETICAL_EXAMPLE','OPINION','RHETORICAL_ECHO',
 'QUESTION','PROVISIONAL_ADVICE','QUESTION_ECHO','SPECULATIVE_OPINION',
 'FINANCIAL_GENERALIZATION','OPINION_CONTEXT','GENERAL_RECOMMENDATION',
 'OPINION_FRAGMENT','DISCOURSE_ASSENT','RISK_STATEMENT','PROCESS_INSTRUCTION',
 'HISTORICAL_ACCOUNT','PERSONAL_ANECDOTE','PERSONAL_PREFERENCE','LIFECYCLE_OPINION',
 'OPINION_ANECTODAL','HISTORICAL_UNCERTAIN','HISTORICAL_OBSERVATION',
 'CONDITIONAL_ADVICE','HIGH_RISK_ADVICE','HISTORICAL_CASE_FRAGMENT',
 'ELIGIBILITY_FRAGMENT','FRAGMENT','HYPOTHETICAL_RETURN','BENEFIT_SCOPE_RISK',
 'HIGH_RISK_ANALOGY','HISTORICAL_NUMERIC_OPEN','NUMERIC_ECHO','HISTORICAL_OPINION',
 'PERSONAL_ANECDOTE','REPORTED_ADVICE','GENERAL_ADVICE','QUESTION_FRAGMENT'}

def require(ok,why):
 if not ok: raise ValueError('V101_'+why)
def sha(x):return hashlib.sha256(x.encode('utf-8') if isinstance(x,str) else x).hexdigest()
def digest(x):return sha(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False))
def source_expectation(selected_cues):
 return { (r['video_id'],r['window_id'],r['cue_index']):r for r in selected_cues }

def verify_v101(selected_cues,original_cues_by_video,registry_by_video,v98_routes,
                readings,gaps,split_rows,*,prior_shadow_parent_keys,
                prior_v96_cue_keys,prior_v97_windows,owner_archive_sha,
                previous_private_archive_sha):
 require(owner_archive_sha==SOURCE_ARCHIVE_SHA,'SOURCE_ARCHIVE_MISMATCH')
 require(previous_private_archive_sha==V98_ARCHIVE_SHA,'V98_ARCHIVE_MISMATCH')
 require(type(selected_cues) is list and len(selected_cues)==240,'SOURCE_240')
 require(type(v98_routes) is list and len(v98_routes)==240,'ROUTE_240')
 require(type(readings) is list and len(readings)==81,'PARENTS_81')
 require(type(gaps) is list and len(gaps)==7,'GAPS_7')
 require(type(split_rows) is list and len(split_rows)==10,'SPLITS_10')
 require(all(type(s) is set for s in (prior_shadow_parent_keys,prior_v96_cue_keys,prior_v97_windows)),'PRIOR_TYPE')
 scopes={(v,w):(no,first,last,priority) for v,w,no,first,last,priority in SCOPE}
 require(len(scopes)==6,'SCOPE_COLLISION')
 source={};by_win=Counter();last_time={};src_receipts=[]
 for r in selected_cues:
  require(type(r) is dict,'SOURCE_ROW_TYPE')
  v,w,i=r.get('video_id'),r.get('window_id'),r.get('cue_index')
  require((v,w) in scopes and type(i) is int,'SOURCE_KEY')
  start=(int(w[1:])-1)*40+1;require(start<=i<start+40,'SOURCE_BOUNDARY')
  key=(v,w,i);require(key not in source,'SOURCE_DUPLICATE')
  require((v,w) not in prior_v97_windows,'PRIOR_V97_WINDOW_OVERLAP')
  require((v,i) not in prior_v96_cue_keys,'PRIOR_V96_CUE_OVERLAP')
  source_cues=original_cues_by_video.get(v)
  require(type(source_cues) is list and i<=len(source_cues),'ORIGINAL_VIDEO_MISSING')
  c=source_cues[i-1]
  require((c.index,c.start_ms,c.end_ms,c.text)==
          (i,r.get('start_ms'),r.get('end_ms'),r.get('source_text_private')),'SOURCE_CUE_MUTATED')
  require(r.get('cue_sha256')==sha(c.text),'SOURCE_SHA')
  require(r.get('context_private')==[
   {'cue_index':j,'text_private':source_cues[j-1].text}
   for j in range(max(1,i-2),min(len(source_cues),i+2)+1)],'CONTEXT_CHANGED')
  require(r.get('context_sha256')==digest(r['context_private']),'CONTEXT_SHA')
  source[key]=r;by_win[(v,w)]+=1;src_receipts.append([*key,r['cue_sha256'],r['context_sha256']])
 require(set(by_win)==set(scopes) and all(x==40 for x in by_win.values()),'WINDOW_INCOMPLETE')
 routes={};rbywin=Counter();priority=Counter();priorities=0
 for row in v98_routes:
  require(type(row) is dict,'ROUTE_TYPE')
  k=(row.get('video_id'),row.get('window_id'),row.get('cue_index'))
  require(k in source and k not in routes,'ROUTE_DUP_OR_OUTSIDE')
  require(row.get('cue_sha256')==source[k]['cue_sha256'],'ROUTE_SHA_MISMATCH')
  require(row.get('route') in ROUTES,'ROUTE_ENUM')
  require(row.get('review_completed') is False and row.get('independent_gold') is False,'V98_PRETEND_COMPLETION')
  require(row.get('fact_approved') is False and row.get('personalized_advice_approved') is False,'V98_PRETEND_APPROVAL')
  routes[k]=row;rbywin[k[:2]]+=1
  if row['route'].startswith('PRIORITY_'):priority[k[:2]]+=1;priorities+=1
 require(len(routes)==240 and all(rbywin[k]==40 for k in scopes),'ROUTE_MISSING')
 require(all(priority[(v,w)]==q for (v,w),(no,a,b,q) in scopes.items()),'PRIORITY_PIN')
 parent_refs={};parents={};pbywin=Counter();parent_receipts=[]
 for v,w,no,start_id,last_id,priority_cue_count in SCOPE:
  rows=registry_by_video.get(v,{}).get(w)
  require(type(rows) is list and len(rows)==last_id-start_id+1,'V33_PARENT_CENSUS')
  ids={r['claim_id'] for r in rows}
  require(ids=={f'C{i:05d}' for i in range(start_id,last_id+1)},'V33_PARENT_IDS')
  for p in rows:
   key=(v,w,p['claim_id']);require(key not in prior_shadow_parent_keys,'PRIOR_SHADOW_DUPLICATE')
   indices=p['cue_indices'];require(indices and len(indices)==len(set(indices)),'PARENT_CUE_DUP')
   require(all((v,w,i) in source for i in indices),'PARENT_CROSS_WINDOW')
   text=' | '.join(source[(v,w,i)]['source_text_private'] for i in indices)
   require(sha(text)==p.get('source_text_sha256'),'PARENT_TEXT_SHA')
   parents[key]=p;pbywin[(v,w)]+=1
   for i in indices:
    ck=(v,w,i);require(ck not in parent_refs,'PARENT_CUE_OVERLAP');parent_refs[ck]=p['claim_id']
 for k,r in routes.items():
  require(r.get('parent_id')==parent_refs.get(k),'ROUTE_PARENT_MISMATCH')
  require(('UNASSIGNED' in r['route'])==(k not in parent_refs),'ROUTE_UNASSIGNED_DRIFT')
 actual_gaps=set(source)-set(parent_refs)
 require(actual_gaps==EXPECTED_GAPS,'GAP_CENSUS_DRIFT')
 records={};meaning=Counter()
 for a in readings:
  require(type(a) is dict,'PARENT_READING_TYPE')
  key=(a.get('video_id'),a.get('window_id'),a.get('parent_id'))
  require(key in parents and key not in records,'REVIEW_PARENT_MISSING_OR_DUP')
  p=parents[key]
  require(a.get('cue_indices')==p['cue_indices'],'READING_CUE_LIST')
  require(a.get('parent_sha256')==p['source_text_sha256'],'READING_PARENT_SHA')
  require(a.get('status')==STATUS,'READING_STATE')
  require(a.get('semantic_kind') in SEMANTIC_KINDS,'READING_SEMANTIC_KIND')
  for f in ('speaker_meaning_private','reviewer_scope_caution_private'):
   require(type(a.get(f)) is str and len(a[f])>=30,'UNREAD_MEANING_'+f)
  for f in FALSE_FLAGS:require(a.get(f) is False,'FALSE_APPROVAL_'+f)
  meaning[a['semantic_kind']]+=1
  records[key]=a
  parent_receipts.append([*key,a['parent_sha256'],a['semantic_kind'],
    sha(a['speaker_meaning_private']),sha(a['reviewer_scope_caution_private'])])
 require(len(records)==81,'MISSING_PARENT_READING')
 checked_gaps=set();gap_receipts=[]
 for g in gaps:
  require(type(g) is dict,'GAP_REVIEW_TYPE')
  key=(g.get('video_id'),g.get('window_id'),g.get('cue_index'))
  require(key in actual_gaps and key not in checked_gaps,'GAP_REVIEW_DUP_OR_EXTRA')
  checked_gaps.add(key)
  require(g.get('cue_sha256')==source[key]['cue_sha256'],'GAP_SHA_CHANGED')
  require(g.get('status')==GAP_STATUS and g.get('speech_act') in SPEECH,'GAP_STATUS_OR_KIND')
  require(type(g.get('reason_private')) is str and len(g['reason_private'])>=35,'GAP_REASON_EMPTY')
  for f in FALSE_FLAGS:require(g.get(f) is False,'GAP_FALSE_APPROVAL_'+f)
  require(g.get('negative_gold') is False and g.get('nonclaim_independently_proven') is False,'GAP_FAKE_NEGATIVE_GOLD')
  gap_receipts.append([*key,g['cue_sha256'],g['speech_act'],sha(g['reason_private'])])
 require(checked_gaps==EXPECTED_GAPS,'GAPS_NOT_REVIEWED')
 splits={};split_receipts=[]
 for sp in split_rows:
  require(type(sp) is dict,'SPLIT_ROW_TYPE')
  key=(sp.get('video_id'),sp.get('window_id'),sp.get('parent_id'))
  require(key in EXPECTED_SPLITS and key not in splits and key in parents,'SPLIT_EXTRA_OR_DUP')
  parts=sp.get('provisional_parts');require(type(parts) is list and len(parts)==2,'SPLIT_PARTS_NOT_TWO')
  parent_indices=parents[key]['cue_indices'];seen=set();part_hash=[]
  for part in parts:
   ix=part.get('cue_indices');require(type(ix) is list and ix and len(ix)==len(set(ix)),'SPLIT_CUE_LIST')
   require(set(ix)<=set(parent_indices) and not seen.intersection(ix),'SPLIT_OVERLAP_OUTSIDE')
   seen.update(ix)
   require(type(part.get('meaning_private')) is str and len(part['meaning_private'])>=12,'SPLIT_MEANING_EMPTY')
   require(part.get('independent_fact_approved') is False and part.get('negative_gold') is False,'SPLIT_FALSE_GOLD')
   part_hash.append([ix,sha(part['meaning_private'])])
  require(seen==set(parent_indices),'SPLIT_PARENT_NOT_COVERED')
  require(sp.get('status')=='PROVISIONAL_WITHIN_PARENT_SEGMENTATION_NOT_ATOMIC_GOLD','SPLIT_STATUS')
  for f in FALSE_FLAGS:require(sp.get(f) is False,'SPLIT_FALSE_APPROVAL_'+f)
  splits[key]=sp;split_receipts.append([*key,part_hash])
 require(set(splits)==EXPECTED_SPLITS,'SPLITS_MISSING')
 original_cues=len(source);parent_cues=len(parent_refs)
 require(original_cues==240 and parent_cues==233 and len(actual_gaps)==7,'FINAL_CUE_CENSUS')
 require(priorities==133 and 240-priorities==107,'PRIORITY_TOTAL')
 return {
  'schema':'V101_6_SOURCE_WINDOWS_240_CUES_81_DRAFT_PARENTS_7_GAPS_10_SPLITS_CHAT_SHADOW_V1',
  'source_bound_cues_context_reviewed_chat':240,
  'source_bound_parent_draft_readings_chat':81,
  'source_bound_gap_speech_acts_chat':7,
  'provisional_parent_subclaim_segmentations_chat':10,
  'provisional_segments':20,
  'parent_assigned_cues_context_accounted':233,
  'selected_windows':len(scopes),
  'prioritized_cues_processed_chat':priorities,
  'fallback_cues_processed_chat':original_cues-priorities,
  'zero_risk_windows_context_reviewed':sum(q==0 for _,_,_,_,_,q in SCOPE),
  'semantic_kind_counts':dict(sorted(meaning.items())),
  'source_receipt_sha256':digest(sorted(src_receipts)),
  'parent_meaning_receipt_sha256':digest(sorted(parent_receipts)),
  'gap_meaning_receipt_sha256':digest(sorted(gap_receipts)),
  'split_meaning_receipt_sha256':digest(sorted(split_receipts)),
  'prior_v98_pending_mutated':False,
  'v75_historical_lineage_recovered':False,
  'first_five_official_pending_unchanged':887,
  'video7_audio_open_unchanged':3,
  'independent_gold':False,
  'financial_fact_approved':False,
  'official_knowledge_merge':False,
  'full_source_atomic_claim_recall_certified':False,
  'human_or_model_semantic_duration_measured':False,
  'personalized_advice_approved':False,
  'p0_go':False}