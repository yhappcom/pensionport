"""V111: source-pinned evidence dispositions of the 22 V110 OPEN speech units.

CLOSED_CONTEXT means only that a source-contiguous discourse fragment is
interpretable; it is neither an approval of financial facts nor blind gold.
Any unresolved account scope, missing video visual or missing audio is OPEN.
No original SRT prose belongs in public code or SHA-only receipts.
"""
from __future__ import annotations
from collections import Counter
from hashlib import sha256
import json,re

SOURCE_ZIP_SHA='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
STATUS_OPEN={'OPEN_AUDIO','OPEN_VISUAL','OPEN_ACCOUNT_VISUAL','OPEN_ACCOUNT_SCOPE'}
STATUS_SET={'CLOSED_CONTEXT'}|STATUS_OPEN
DEPS={'SOURCE_CONTEXT','AUDIO_ORIGINAL','SCREEN_OR_ACCOUNT_LEDGER','ACCOUNT_ORIGIN_AND_RECEIPT_TYPE'}
ALLOWED_EXTERNAL={'NTS_PRIVATE_PENSION_2026','SKHYNIX_HISTORY','BOOK_CATALOG'}
HEX=re.compile(r'^[0-9a-f]{64}$')

def canon(obj):return json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def sha(s):return sha256(s if isinstance(s,bytes) else s.encode('utf-8')).hexdigest()
def digest(obj):return sha(canon(obj))
def require(c,name):
 if not c:raise ValueError('V111_'+name)

def audit(*,source_zip_bytes,previous_zip_bytes,previous_docket,previous_units,cues_full_by_video,decisions,evidence):
 """Return only source hashes, conservative counts and public-safe aggregate receipts."""
 require(type(source_zip_bytes) is bytes and sha(source_zip_bytes)==SOURCE_ZIP_SHA,'SOURCE_ZIP_DRIFT')
 require(type(previous_zip_bytes) is bytes and len(previous_zip_bytes)>50000,'PRIOR_ARCHIVE')
 require(type(previous_docket) is list and len(previous_docket)==22,'PRIOR_OPEN_22')
 require(type(previous_units) is dict and len(previous_units.get('parents',[]))==52,'PRIOR_52')
 require(type(cues_full_by_video) is dict and len(cues_full_by_video)>=4,'FULL_SOURCE')
 require(type(decisions) is dict and decisions.get('schema')=='V111_PRIVATE_22_EVIDENCE_DISPOSITIONS_NO_GOLD_V1','DISPOSITION_SCHEMA')
 require(decisions.get('source_archive_sha256')==SOURCE_ZIP_SHA,'DISPOSITION_SOURCE')
 require(decisions.get('prior_private_zip_sha256')==sha(previous_zip_bytes),'PRIOR_SHA')
 require(decisions.get('prior_open_docket_sha256')==digest(previous_docket),'PRIOR_DOCKET_SHA')
 require(type(decisions.get('rows')) is list and len(decisions['rows'])==22,'DISPOSITION_22')
 require(decisions.get('finance_fact_approved') is False and decisions.get('independent_gold') is False and decisions.get('p0_go') is False,'FALSE_GLOBAL_APPROVAL')
 prior={r['unit_id']:r for r in previous_docket}
 require(len(prior)==22,'PRIOR_UNIQUE')
 unit_map={}
 for p in previous_units['parents']:
  for u in p['units']:
   require(u['unit_id'] not in unit_map,'PARENT_UNIT_DUP')
   unit_map[u['unit_id']]=(p,u)
 require(set(prior)<=set(unit_map),'PRIOR_UNIT_MISSING')
 valid_external={x['evidence_id'] for x in evidence}
 require(valid_external==ALLOWED_EXTERNAL and len(evidence)==3,'EVIDENCE_CENSUS')
 for e in evidence:
  require(type(e.get('issuer')) is str and type(e.get('url')) is str and e['url'].startswith('https://'),'EVIDENCE_URI')
  require(e.get('current_personal_finance_application_certified') is False,'EVIDENCE_FALSE_APPROVAL')
  require(e.get('webpage_exact_byte_hash_saved') is False,'FALSE_WEB_SNAPSHOT')
 seen=set();states=Counter();source_covered=set();verified=[];audio=visual=acct=0
 for row in decisions['rows']:
  uid=row.get('unit_id');require(uid in prior and uid not in seen,'UNIT_DUP_MISSING_OR_EXTRA');seen.add(uid)
  base=prior[uid];parent,unit=unit_map[uid];vid=base['video_id'];indices=base['source_cue_indices']
  for k in ('video_id','window_id','draft_parent_id','role','source_cue_indices','source_cues_digest_sha256'):
   require(row.get(k)==base.get(k),'OLD_LINEAGE_DRIFT_'+k)
  require(parent['video_id']==vid and parent['draft_parent_id']==base['draft_parent_id'],'PARENT_LINK_DRIFT')
  require(unit['source_cue_indices']==indices and unit['source_cues_digest_sha256']==base['source_cues_digest_sha256'],'UNIT_SOURCE_DRIFT')
  cues=cues_full_by_video.get(vid);require(type(cues) is list and len(cues)>=max(indices),'VIDEO_SOURCE_MISSING')
  require([x.index for x in cues]==list(range(1,len(cues)+1)),'SOURCE_CUE_SEQUENCE')
  actual=sha(''.join(sha(cues[i-1].text) for i in indices))
  require(actual==base['source_cues_digest_sha256'],'CUE_TEXT_DRIFT')
  start,end=row.get('context_first_cue'),row.get('context_last_cue')
  require(type(start) is int and type(end) is int and max(1,min(indices)-25)<=start<=min(indices)
          and max(indices)<=end<=min(len(cues),max(indices)+25),'CONTEXT_SCOPE')
  require(end-start+1<=55,'CONTEXT_TOO_BROAD')
  ctx=[cues[i-1] for i in range(start,end+1)]
  require(row.get('context_sha256')==digest([[x.index,sha(x.text)] for x in ctx]),'CONTEXT_SHA_DRIFT')
  require(type(row.get('contextual_interpretation_private')) is str and len(row['contextual_interpretation_private'])>=30,'EMPTY_INTERPRETATION')
  require(type(row.get('remaining_limit_private')) is str and len(row['remaining_limit_private'])>=25,'EMPTY_LIMIT')
  status=row.get('status');require(status in STATUS_SET,'BAD_STATUS');states[status]+=1
  dep=row.get('next_evidence_dependency');require(dep in DEPS,'DEPENDENCY_TYPE')
  if status=='CLOSED_CONTEXT':
   require(dep=='SOURCE_CONTEXT' and row.get('contextual_meaning_resolved') is True,'CLOSED_WITH_UNRESOLVED_MEANING')
   require(row.get('further_audio_required_for_exact_transcript') is False,'CLOSED_AUDIO_FLAG')
   require(row.get('remaining_visual_or_account_data_required') is False,'CLOSED_VISUAL_FLAG')
   require(row.get('official_finance_rule_personalized') is False,'CLOSED_FINANCE_APPROVAL')
  else:
   require(row.get('contextual_meaning_resolved') is False,'FALSE_OPEN_MEANING_COMPLETE')
   require(bool(row['remaining_limit_private'].strip()),'OPEN_WITHOUT_LIMIT')
   if status=='OPEN_AUDIO':require(dep=='AUDIO_ORIGINAL' and row.get('further_audio_required_for_exact_transcript') is True,'OPEN_AUDIO_UNLABELED');audio+=1
   if status in ('OPEN_VISUAL','OPEN_ACCOUNT_VISUAL'):
    require(dep=='SCREEN_OR_ACCOUNT_LEDGER' and row.get('remaining_visual_or_account_data_required') is True,'OPEN_SCREEN_UNLABELED');visual+=1
   if status=='OPEN_ACCOUNT_SCOPE':
    require(dep=='ACCOUNT_ORIGIN_AND_RECEIPT_TYPE' and row.get('remaining_visual_or_account_data_required') is True,'OPEN_ACCOUNT_UNLABELED');acct+=1
  refids=row.get('external_evidence_ids');require(type(refids) is list and len(refids)==len(set(refids)) and set(refids)<=valid_external,'EXTERNAL_REF_INVALID')
  for fld in ('financial_rule_approved','personal_advice_approved','all_52_financial_claims_certified','independent_gold','p0_go'):
   require(row.get(fld) is False,'FALSE_APPROVAL_'+fld)
  verified.append([uid,status,vid,start,end,row['context_sha256'],refids,sha(row['contextual_interpretation_private']),sha(row['remaining_limit_private'])]);source_covered.update((vid,i) for i in indices)
 require(seen==set(prior),'PRIOR_OPEN_NOT_ALL_DISPOSED')
 require(states['CLOSED_CONTEXT']==10 and sum(states[s] for s in STATUS_OPEN)==12,'FROZEN_DISPOSITION_CENSUS')
 require(audio==7 and visual==4 and acct==1,'EVIDENCE_BACKLOG_CENSUS')
 require(len(source_covered)>0 and decisions.get('existing_v110_52_parent_85_units_modified') is False,'ORIGINAL_MUTATION')
 return {'schema':'V111_OPEN22_SOURCE_CONTEXT_EVIDENCE_AUDIT_SHA_ONLY_NO_GOLD_V1',
  'source_archive_sha256':SOURCE_ZIP_SHA,'v110_private_zip_sha256':sha(previous_zip_bytes),
  'original_open_units':len(prior),'context_resolved_units':states['CLOSED_CONTEXT'],
  'still_open_units':sum(states[s] for s in STATUS_OPEN),'open_audio':audio,'open_visual_or_screen':visual,
  'open_account_scope':acct,'external_source_references':len(evidence),
  'source_linked_disposition_digest_sha256':digest(sorted(verified)),
  'closed_context_does_not_certify_finance_facts':True,'all_financial_semantics_complete':False,
  'human_independent_gold':False,'certified_precision':None,'certified_recall':None,
  'personal_advice_approved':False,'p0_go':False,'master116_p4_formal_merge':False}

def compare_public_receipt(actual,published):
 require(type(published) is dict and actual==published,'PUBLIC_DIGEST_DRIFT')
 require(published['human_independent_gold'] is False and published['p0_go'] is False and published['certified_precision'] is None,'PUBLIC_FALSE_CERT')
 return True