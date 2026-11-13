"""V91 synthetic/owner-side full V33-parent census for five original #7 windows.

All 55 V33 parents must be individually reviewed, and every uncaptured cue
must receive a provisional speech-act disposition. This is *not* a claim
completeness, independent gold, tax-rule approval or personalized-advice gate.
No raw owner subtitle may be committed to the public repository.
"""
from __future__ import annotations
import hashlib, json
from collections import Counter
from v87_targeted_source_guard import expected_parent_source

VIDEO_ID='4CQ4FjGT2gA'
SOURCE_CUE_COUNT=10728
SOURCE_WINDOW_COUNT=269
PREVIOUS_PARENT_COUNT=205
PREVIOUS_WINDOW_COUNT=65
EXPECTED={
 'W00076':tuple(f'C{x:05d}' for x in range(1078,1091)),
 'W00102':tuple(f'C{x:05d}' for x in range(1395,1405)),
 'W00153':tuple(f'C{x:05d}' for x in range(1955,1968)),
 'W00218':tuple(f'C{x:05d}' for x in range(2800,2809)),
 'W00231':tuple(f'C{x:05d}' for x in range(2938,2948)),
}
EXPECTED_PARENT_TOTAL=55
EXPECTED_GAP={( 'W00231',9239)}
KINDS={'DESCRIPTIVE_FINANCE','HISTORICAL_CASE','OPINION','HYPOTHESIS',
       'QUESTION_NOT_FACT','CONDITIONAL_ADVICE','REPORTED_NUMERIC','ASR_UNCERTAIN'}
FALSE_FLAGS=('fact_approved','independent_gold','official_parent_merged','personal_action_approved',
             'v75_membership_verified','financial_fact_certified','independent_precision_recall_certified',
             'personalized_advice_approved','full_window_semantics_certified','audio_verified',
             'law_current_verified')
STATUS='V91_COMPLETE_DRAFT_PARENT_SET_CHAT_SHADOW_NOT_GOLD'
GAP_STATUS='V91_UNASSIGNED_CUE_SPEECHACT_SHADOW_NOT_NEGATIVE_GOLD'

def require(b,code):
 if not b:raise ValueError('V91_'+code)
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(obj):return sha(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def deny_promotion(row):
 require(type(row) is dict,'ROW_TYPE')
 for name in FALSE_FLAGS:require(row.get(name) is False,'FALSE_GO_'+name)
 require(row.get('semantic_kind') in KINDS,'INVALID_SEMANTIC_KIND')
 require(row.get('status')==STATUS,'ROW_STATUS')
 for name in ('speaker_meaning_private','scope_caution_private'):
  require(type(row.get(name)) is str and len(row[name])>=40,'MISSING_CONTEXT_'+name)
 require(type(row.get('risk_domain')) is str and len(row['risk_domain'])>=6,'NO_RISK_DOMAIN')
 return {'can_merge_master116':False,'can_promote_p3':False,'independent_gold':False}

def verify_parent(row,cues,regs):
 require(type(row) is dict,'ROW_INVALID')
 key=(row.get('window_id'),row.get('claim_id'))
 require(key[0] in EXPECTED and key[1] in EXPECTED[key[0]],'OUTSIDE_CENSUS')
 require(row.get('video_no')==7 and row.get('video_id')==VIDEO_ID,'VIDEO_MISMATCH')
 expected=expected_parent_source(cues,regs,key)
 for f in ('window_id','claim_id','cue_indices','start_ms','end_ms','source_excerpt_private','source_sha256',
           'adjacent_cues_private','adjacent_context_sha256'):
  require(row.get(f)==expected[f],'SOURCE_MUTATED_'+f)
 deny_promotion(row)
 return digest([*key,expected['source_sha256'],row['semantic_kind'],
                sha(row['speaker_meaning_private'].encode()),sha(row['scope_caution_private'].encode())])

def expected_unassigned(cues,regs):
 expected=[]
 for w in EXPECTED:
  start=(int(w[1:])-1)*40+1;end=min(int(w[1:])*40,len(cues))
  assigned={i for p in regs[w] for i in p['cue_indices']}
  expected.extend((w,i) for i in range(start,end+1) if i not in assigned)
 return set(expected)

def verify_gap(row,cues):
 require(type(row) is dict,'GAP_TYPE')
 key=(row.get('window_id'),row.get('cue_index'))
 require(key in EXPECTED_GAP,'GAP_OUTSIDE_CENSUS')
 require(row.get('video_no')==7 and row.get('video_id')==VIDEO_ID,'GAP_WRONG_VIDEO')
 cue=cues[key[1]-1]
 require(row.get('source_text_private')==cue.text,'GAP_SOURCE_TEXT')
 require(row.get('source_sha256')==sha(cue.text.encode()),'GAP_SOURCE_SHA')
 require(row.get('start_ms')==cue.start_ms and row.get('end_ms')==cue.end_ms,'GAP_TIME')
 require(row.get('status')==GAP_STATUS,'GAP_STATUS')
 require(row.get('speech_act')=='MINIMAL_RESPONSE','GAP_SPEECH_ACT')
 require(type(row.get('contextual_reason_private')) is str and len(row['contextual_reason_private'])>=40,'GAP_NO_REVIEW')
 for f in ('negative_gold','fact_approved','personal_action_approved','financial_fact_certified',
           'independent_gold','full_window_semantics_certified'):
  require(row.get(f) is False,'GAP_FALSE_APPROVAL_'+f)
 return digest([*key,row['source_sha256'],row['speech_act'],sha(row['contextual_reason_private'].encode())])

def verify_complete_draft_census(rows,gaps,selected_screens,all_screens,cues,regs,prior):
 require(len(cues)==SOURCE_CUE_COUNT and len(regs)==SOURCE_WINDOW_COUNT,'V7_SOURCE_COUNTS')
 require(type(all_screens) is list and len(all_screens)==SOURCE_WINDOW_COUNT,'SCREEN269')
 screens={x.get('window_id'):x for x in all_screens}
 require(len(screens)==SOURCE_WINDOW_COUNT,'DUPLICATE_SCREEN')
 require(type(prior) is set and len(prior)==PREVIOUS_PARENT_COUNT,'PRIOR_205')
 require(len({w for w,c in prior})==PREVIOUS_WINDOW_COUNT,'PRIOR_65_WINDOWS')
 expected_keys={(w,c) for w,claims in EXPECTED.items() for c in claims}
 require(len(expected_keys)==EXPECTED_PARENT_TOTAL,'INTERNAL_CENSUS')
 require(not {w for w,c in prior}.intersection(EXPECTED),'PRIOR_WINDOW_OVERLAP')
 require(type(selected_screens) is list and len(selected_screens)==len(EXPECTED),'SELECTED5')
 require({s.get('window_id') for s in selected_screens}==set(EXPECTED),'SCREEN_SET')
 for s in selected_screens:
  w=s['window_id'];require(s==screens[w],'SCREEN_CHANGED')
  first=(int(w[1:])-1)*40+1;last=min(int(w[1:])*40,len(cues))
  full=' '.join(cues[i-1].text for i in range(first,last+1))
  require((s['first_cue'],s['last_cue'])==(first,last),'SCREEN_BOUNDS')
  require(s['video_id']==VIDEO_ID and s['video_no']==7,'SCREEN_VIDEO')
  require(s['source_window_sha256']==sha(full.encode()),'SCREEN_SHA')
  require(s['draft_parent_count']==len(regs[w])==len(EXPECTED[w]),'PARENT_CENSUS_DRIFT')
  require(s.get('manual_reviewed_all_parents') is False,'ORIGINAL_SCREEN_FALSE_GO')
  for f in ('fact_approved','independent_gold','personal_action_approved'):
   require(s.get(f) is False,'SCREEN_FALSE_GO_'+f)
 require(type(rows) is list and len(rows)==EXPECTED_PARENT_TOTAL,'ROWS_55')
 seen=set();readings=[];by_window=Counter()
 for row in rows:
  key=(row.get('window_id'),row.get('claim_id'))
  require(key in expected_keys and key not in seen and key not in prior,'EXTRA_OR_DUPLICATE')
  seen.add(key);by_window[key[0]]+=1;readings.append(verify_parent(row,cues,regs))
 require(seen==expected_keys,'MISSING_PARENT')
 require(all(by_window[w]==len(EXPECTED[w]) for w in EXPECTED),'WINDOW_MISSING_PARENT')
 require(expected_unassigned(cues,regs)==EXPECTED_GAP,'UNKNOWN_UNASSIGNED_CUE')
 require(type(gaps) is list and len(gaps)==len(EXPECTED_GAP),'GAPS_MISSING')
 gap_keys={(r.get('window_id'),r.get('cue_index')) for r in gaps}
 require(gap_keys==EXPECTED_GAP,'GAP_SET_DRIFT')
 gap_receipts=[verify_gap(row,cues) for row in gaps]
 union=prior|seen
 require(len(union)==260 and len({w for w,c in union})==70,'CUMULATIVE_260_70')
 return {'whole_draft_parent_census_windows':5,'whole_draft_parent_census_parents':55,
         'private_cue_gap_speech_acts_reviewed':len(gaps),'new_window_ids':list(EXPECTED),
         'cumulative_source_bound_parents':260,'cumulative_sampled_windows':70,
         'video7_windows_without_parent_sample':199,
         'draft_parent_meaning_receipt_sha256':digest(sorted(readings)),
         'source_gap_receipt_sha256':digest(sorted(gap_receipts)),
         'all_draft_parents_in_5_windows_reviewed':True,
         'source_wide_atomic_claim_recall_certified':False,'independent_gold':False,
         'financial_fact_certified':False,'full_window_semantics_certified':False,
         'personalized_advice_approved':False,'p0_go':False}