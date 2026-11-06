"""Fail-closed #1-#5 221-remnant *candidate* ledger and source-window gate.

All original source windows are accounted for. This is NOT an independently
certified atom-by-atom statement recall, official-law snapshot, investment
advice approval or formal knowledge merge. In --source-zip mode, verify the
private original source bytes, including each candidate's anchor cue hash.
"""
from __future__ import annotations
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse
import zipfile
from .first_five_window_review_gate import source_windows
from .first_five_atomic_claim_gate import load as load_prior

P=Path('ire/v5/validation')
LEDGER=P/'first_five_remnant_221_source_claim_candidates_20261106.json'
SOURCES=P/'first_five_remnant_official_source_register_20261106.json'
RELATION=P/'first_five_remnant_duplicate_conflict_register_20261106.json'
RESOLUTION=P/'first_five_remnant_canonical_concepts_20261106.json'
CHALLENGES=P/'first_five_remnant_omission_challenges_20261106.json'
V=('sz5N9WJS310','6VEfKF7BzZU','OiDTNstaSpM','aNfGrcO6WPI','qtluAViPpsQ')
W=(67,76,44,43,58)
RAW_ZIP='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
ALLOWED_HOSTS={'m.nps.or.kr','www.nps.or.kr','nts.go.kr','d.nts.go.kr',
               'regulation.krx.co.kr','nabo.go.kr','www.knbank.co.kr','blog.kbsec.com',
               'open.krx.co.kr','www.moel.go.kr','www.samsungpop.com',
               'www.hf.go.kr','www.investor.gov'}
NO_CLAIM={'USER_QUESTION','NON_FINANCIAL_CONTEXT','EXPERIENCE_OR_UNVERIFIED_HISTORY'}
KINDS={'CONDITIONAL_STRATEGY_OPINION','HYPOTHETICAL_FINANCIAL_MODEL',
       'TAX_OR_PENSION_RULE','PRODUCT_TERMS_OR_RISK','TIME_SENSITIVE_MACRO_DATA'}
class RemainderReviewError(ValueError):pass
def require(ok:bool,label:str)->None:
 if not ok:raise RemainderReviewError(label)
def read(root:Path,p:Path)->dict:
 return json.loads((Path(root)/p).read_text('utf-8'))
def cue_txt(blob:bytes):
 s=blob.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n').strip()
 arr=[]
 for block in re.split(r'\n\s*\n',s):
  lines=block.split('\n')
  require(len(lines)>=3 and lines[0].strip().isdigit(),'REM221_BAD_PRIVATE_CUE')
  n=int(lines[0]);require(n==len(arr)+1,'REM221_PRIVATE_CUE_SEQUENCE')
  body=' '.join(x.strip() for x in lines[2:] if x.strip())
  arr.append(body)
 return arr

def verify(root:Path, source_zip:Path|None=None,replacement:dict|None=None)->dict:
 root=Path(root)
 d=read(root,LEDGER) if replacement is None else replacement
 require(d.get('schema')=='IRE_V5_FIRST_FIVE_REMAINDER_221_SOURCE_COVERED_CANDIDATES_V1'
  and d.get('as_of')=='2026-11-06'
  and d.get('original_zip_sha256')==RAW_ZIP
  and d.get('source_window_coverage_completed') is True
  and d.get('source_window_coverage_is_not_atomic_statement_recall') is True
  and d.get('full_original_atomic_recall_certified') is False
  and d.get('formal_financial_fact_approvals')==0
  and d.get('personal_investment_actions_approved')==0
  and d.get('legacy_B04_final_knowledge_merge_approved') is False
  and d.get('original_audio_verified') is False
  and d.get('private_original_srt_committed_to_git') is False
  and d.get('prior_claims_preserved')==68
  and d.get('prior_windows_preserved')==67
  and d.get('previous_public_engine_completed_windows_unchanged')==5
  and d.get('previous_public_engine_remaining_windows_unchanged')==283,
   'REM221_UNEARNED_RESEARCH_COMPLETION_OR_APPROVAL')
 p=load_prior(root)
 src=read(root,SOURCES)
 official=src.get('sources',[])
 require(src.get('schema')=='IRE_V5_FIRST_FIVE_OFFICIAL_CONTEXT_REGISTER_V1'
         and src.get('verified_current_law_for_all_221') is False
         and src.get('source_urls_are_context_not_claim_wide_approval') is True
         and len(official)==19,'REM221_OFFICIAL_CONTEXT_NOT_FROZEN')
 lookup={x['source_id']:x for x in official}
 require(len(lookup)==len(official),'REM221_DUPLICATE_OFFICIAL_CONTEXT_ID')
 for name,x in lookup.items():
  u=urlparse(x.get('url',''))
  require(u.scheme=='https' and u.hostname in ALLOWED_HOSTS
    and x.get('checked_date')=='2026-11-06'
    and x.get('financial_fact_approval_for_advice') is False
    and x.get('source_bytes_snapshotted_into_git') is False
    and len(x.get('verified_narrow_scope',''))>=20,
    'REM221_FAKE_OFFICIAL_CONTEXT_'+name)
 source={}
 counts=collections.Counter()
 for n in range(1,6):
  data=read(root,P/f'v5_first_five_video_{n:02d}_window_review_20261106.json')
  require(len(data['records'])==W[n-1],'REM221_PREVIOUS_CENSUS_CHANGED')
  for row in data['records']:
   source[(n,row['window_id'])]=row
 old_keys={(x['video_number'],x['window_id']) for x in p}
 require(len(old_keys)==67,'REM221_PRIOR_68_SOURCE_SET_CHANGED')
 windows=d.get('source_boundaries',[]);claims=d.get('candidate_assertions',[])
 require(type(windows) is list and len(windows)==221 and
         type(claims) is list and len(claims)==237,'REM221_MISSING_SOURCE_WINDOW_OR_CANDIDATES')
 keys=set();ids=set();links=collections.defaultdict(list)
 for row in windows:
  n=row.get('video_number');wid=row.get('window_id');k=(n,wid)
  require(type(n) is int and 1<=n<=5 and k in source and k not in keys and
          k not in old_keys and row.get('video_id')==V[n-1],
          'REM221_DUPLICATED_OR_WRONG_VIDEO_WINDOW')
  keys.add(k);counts[n]+=1
  prev=source[k]
  require(row.get('first_cue')==prev['first_cue'] and
          row.get('last_cue')==prev['last_cue'] and
          row.get('window_sha256')==prev['primary_text_sha256'] and
          row.get('window_start_ms')==prev['start_ms'] and
          row.get('window_end_ms')==prev['end_ms'] and
          row.get('source_cue_count')==prev['last_cue']-prev['first_cue']+1 and
          row.get('previous_semantic_summary') is None and
          row.get('previous_source_semantic_summary')==prev['semantic_summary'] and
          row.get('previous_meaning_type')==prev['meaning_type'] and
          row.get('domain')==prev['domain'] and
          row.get('source_text_private_not_published') is True,
          'REM221_SOURCE_CUE_WINDOW_DIGEST_OR_SUMMARY_CHANGED')
  require(row.get('adjudication_state')=='SECOND_PASS_CANDIDATES_NOT_FULL_ATOMIC_RECALL_PROVEN'
     and row.get('source_window_readable_meaning_exists') is True
     and row.get('historical_verbatim_audio_reviewed') is False
     and row.get('current_financial_fact_approved') is False
     and row.get('personal_investment_action_approved') is False,
     'REM221_FALSE_BOUNDED_REVIEW_STATUS')
  ty=row['previous_meaning_type']; cids=row.get('claim_candidate_ids',[])
  require(type(cids) is list and len(cids)==len(set(cids)), 'REM221_DUPLICATE_WINDOW_CLAIM_IDS')
  if ty in NO_CLAIM:
   require(not cids and isinstance(row.get('no_financial_assertion_reason'),str),
           'REM221_UNREVIEWED_QUESTION_CONTEXT')
  else:
   require(ty in KINDS and len(cids)>=1 and row.get('no_financial_assertion_reason') is None,
           'REM221_MISSING_ACTIVE_WINDOW_CLAIM')
  for z in cids:links[z].append(k)
 require(counts==collections.Counter({1:51,2:63,3:32,4:30,5:45})
         and len(keys | old_keys)==288 and
         len(keys & old_keys)==0,
         'REM221_288_WINDOWS_NOT_EXHAUSTIVELY_PARTITIONED')
 for i,row in enumerate(claims,1):
  c=row.get('id');k=(row.get('video_number'),row.get('window_id'))
  require(c==f'FV5-R{i:04d}' and c not in ids and k in keys
          and links.get(c)==[k] and row.get('video_id')==V[k[0]-1],
          'REM221_FABRICATED_OR_DUPLICATED_ATOMIC_CANDIDATE')
  ids.add(c)
  base=source[k]
  require(row.get('first_cue')==base['first_cue'] and
          row.get('last_cue')==base['last_cue'] and
          row.get('original_window_sha256')==base['primary_text_sha256'] and
          type(row.get('anchor_cue_number')) is int and
          row['first_cue']<=row['anchor_cue_number']<=row['last_cue'] and
          bool(re.fullmatch('[0-9a-f]{64}',str(row.get('anchor_cue_sha256')))),
          'REM221_ATOMIC_SOURCE_TEXT_ANCHOR_CHANGED')
  require(row.get('statement_origin') in ('FROM_PREVIOUS_MANUAL_WINDOW_SUMMARY',
       'INTERPRETIVE_RISK_SUPPLEMENT_NOT_VERBATIM')
       and len(row.get('statement',''))>=14
       and len(row.get('critical_scope_and_exceptions',''))>=20
       and row.get('official_document_supports_entire_statement') is False
       and row.get('current_rule_applicability_checked') is False
       and row.get('official_fact_approval') is False
       and row.get('strict_duplicate_certified') is False
       and row.get('remove_as_duplicate_from_candidate_registry') is False
       and row.get('B04_direct_claim_semantic_relation_approved') is False
       and row.get('anchor_cue_semantic_accuracy_independently_adjudicated') is False
       and row.get('verified_by_independent_blind_reviewer') is False
       and row.get('advisory_action_permitted') is False,
       'REM221_FALSE_CLAIM_CERTIFICATION_OR_RISK')
  ol=row.get('official_source_candidates',[])
  require(type(ol) is list and all(x in lookup for x in ol),
          'REM221_UNVERIFIED_OFFICIAL_SOURCE_POINTER')
  historic={3:'GOMHEE-C64',4:'GOMHEE-C63',5:'GOMHEE-C62'}.get(k[0])
  require(row.get('legacy_B04_direct_video_claim')==historic
          and row.get('B04_direct_claim_semantic_relation_approved') is False,
          'REM221_WRONG_OR_AUTO_APPROVED_B04_LINK')
  if row.get('known_unsafe_generalization_code'):
   require(len(row.get('contradiction_or_scope_risk',''))>20,
          'REM221_UNEXPLAINED_CONFLICT')
 rel=read(root,RELATION)
 require(rel.get('schema')=='IRE_V5_FIVE_ORIGINAL_221_RELATION_DEDUP_OPEN_V1'
         and rel.get('strict_duplicate_groups_certified')==0
         and rel.get('semantic_conflicts_formally_resolved')==0
         and rel.get('all_116_core_claims_mutated') is False
         and rel.get('deduped_facts_promoted_for_advice')==0
         and len(rel.get('unsafe_generalizations',[]))==30
         and len(rel.get('potential_topic_overlap_groups',[]))==22,
         'REM221_FALSE_DUPLICATE_CONFLICT_RESOLUTION')
 catalog_ids={x['id'] for x in p}
 for g in rel['potential_topic_overlap_groups']:
  require(g.get('merge_decision')=='HOLD_PENDING_CLAIM_LEVEL_SEMANTIC_EQUIVALENCE_REVIEW'
   and g.get('source_claims_retained') is True
   and all(x in ids for x in g['new_candidate_claim_ids'])
   and all(x in catalog_ids for x in g['prior_68_candidate_ids']),
   'REM221_DUPLICATE_GROUP_PROMOTED_OR_BAD_REF')
 resolution=read(root,RESOLUTION)
 require(resolution.get('schema')=='IRE_V5_FIRST_FIVE_221_CONCEPT_CANONICALIZATION_V1'
   and resolution.get('formal_B04_knowledge_merge_approved') is False
   and resolution.get('claim_level_duplicate_subclaims_approved_removed') is None
   and resolution.get('strict_semantic_duplicate_subclaims_approved_removed')==0
   and len(resolution.get('canonical_educational_scopes',[]))==22
   and len(resolution.get('B04_source_meaning_relationships_for_qualified_principles',[]))==62
   and len(resolution.get('narrow_financial_or_product_context_crosschecks',[]))==16
   and resolution.get('personal_advice_release') is False,
   'REM221_FALSE_CANONICAL_KNOWLEDGE_APPROVAL')
 valid_rels={'SUPPORTS_CONDITIONAL_PRINCIPLE','QUALIFIES_OR_CHALLENGES_UNSAFE_EXTENSION'}
 for q in resolution['B04_source_meaning_relationships_for_qualified_principles']:
  key=(q['video_number'],q['window_id'])
  require(key in keys and q['video_number'] in (3,4,5) and
   q['legacy_claim_id']=={3:'GOMHEE-C64',4:'GOMHEE-C63',5:'GOMHEE-C62'}[q['video_number']] and
   q['provisional_source_relationship'] in valid_rels and
   q['B04_formal_merge_approval'] is False and
   q['official_regulation_confirmation'] is False,
   'REM221_WRONG_B04_MEANING_REVIEW')
 for z in resolution['narrow_financial_or_product_context_crosschecks']:
  require((z['video_number'],z['window_id']) in keys and
          all(i in lookup for i in z['official_context_ids']) and
          z['advice_or_account_action_approval'] is False and
          z['exact_verbatim_video_fact_reviewed_by_independent_audio'] is False,
          'REM221_BAD_OFFICIAL_CONTEXT_SAFETY')
 challenge=read(root,CHALLENGES)
 require(challenge.get('schema')=='IRE_V5_FIRST_FIVE_SECOND_PASS_OMISSION_CHALLENGE_V1'
       and challenge.get('flagged_records')==len(challenge.get('rows',[]))==13
       and challenge.get('full_recall_proven') is False
       and challenge.get('source_claims_silently_discarded') is False
       and challenge.get('claims_approved_after_challenge')==0,
       'REM221_OMISSION_CHALLENGE_SUPPRESSED')
 for z in challenge['rows']:
  k=(z['video_number'],z['window_id'])
  require(k in keys and z['source_window_sha256']==source[k]['primary_text_sha256']
          and len(z['meaning_review_required'])>=30
          and z['resolution_state']=='OPEN_PROMOTABLE_ONLY_AFTER_INDEPENDENT_FACT_OR_CONTEXT_REVIEW'
          and z['historical_assertion_not_financial_rule_approved'] is True,
          'REM221_OMISSION_CHALLENGE_UNSAFE')
 source_validation={'original_private_zip_reopened_in_this_execution':False,
                    'original_221_window_hashes_matching':None,
                    'original_237_anchor_hashes_matching':None}
 if source_zip is not None:
  source_zip=Path(source_zip)
  require(source_zip.is_file() and hashlib.sha256(source_zip.read_bytes()).hexdigest()==RAW_ZIP,
          'REM221_PRIVATE_ZIP_SHA_MISMATCH')
  num_windows=0;num_claims=0
  with zipfile.ZipFile(source_zip) as z:
   for n,vid in enumerate(V,1):
    raw=z.read(f'1-70/youtube-transcript-{vid}.srt')
    sw=source_windows(raw);cues=cue_txt(raw)
    require(len(sw)==W[n-1],'REM221_ORIGINAL_WINDOW_PLAN_CHANGED')
    for row in windows:
     if row['video_number']!=n:continue
     actual=sw[int(row['window_id'][1:])-1]
     require(row['first_cue']==actual['first_cue']
             and row['last_cue']==actual['last_cue']
             and row['window_sha256']==actual['primary_text_sha256'],
             'REM221_PRIVATE_WINDOW_HASH_MISMATCH')
     num_windows+=1
    for row in claims:
     if row['video_number']!=n:continue
     actual=cues[row['anchor_cue_number']-1]
     require(hashlib.sha256(actual.encode()).hexdigest()==row['anchor_cue_sha256'],
             'REM221_PRIVATE_ANCHOR_CUE_HASH_MISMATCH_'+row['id'])
     num_claims+=1
  source_validation={'original_private_zip_reopened_in_this_execution':True,
                     'original_221_window_hashes_matching':num_windows,
                     'original_237_anchor_hashes_matching':num_claims}
 stats=d.get('statistics',{})
 require(stats.get('new_remnant_window_records')==221 and
    stats.get('new_remnant_assertion_candidates')==237 and
    stats.get('new_remnant_windows_with_assertions')==162 and
    stats.get('no_claim_context_and_question_windows')==59 and
    stats.get('independent_atomic_recall_certified') is False,
    'REM221_STATISTICS_STATUS_CHANGED')
 return {'schema':'IRE_V5_FIRST_FIVE_221_PROVISIONAL_SOURCE_GATE_V1',
  'old_68_claims_untouched':True,'old_claim_windows':67,
  'additional_source_windows_reviewed':221,
  'total_source_windows_structurally_covered':288,
  'new_interpretive_candidate_statements':237,
  'historical_question_nonfinancial_windows_marked':59,
  'new_active_financial_windows':162,
  'narrow_official_context_cases':16,
  'additional_omission_challenges_open':13,
  'concept_clusters_with_provisional_canonical_scopes':22,
  'high_risk_scope_flags_not_forced_conflicts':30,
  'B04_source_meaning_relations_not_formal_merge':62,
  'independent_100pct_atomic_recall_proven':False,
  'all_current_law_facts_verified':False,
  'full_financial_knowledge_approval':False,
  'trading_actions_approved':0,
  'previous_public_processed_windows_unchanged':5,
  'previous_public_unprocessed_windows_unchanged':283,
  **source_validation}

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--root',type=Path,default=Path('.'))
 ap.add_argument('--source-zip',type=Path)
 a=ap.parse_args()
 print(json.dumps(verify(a.root,a.source_zip),ensure_ascii=False,sort_keys=True))
if __name__=='__main__': main()
