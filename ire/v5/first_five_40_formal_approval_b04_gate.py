"""Strict first-40 rule-disposition and B04 scoped-education integration gate.

The first five previously OPEN rule composites receive a terminal research
*disposition*, never certification of their original claims. Six B04 C66/C78
scoped education graph references are accepted in a new append-only sidecar.
The historical master, primary citations and V5 kernel are untouched.

Without independent official bytes and a distinct verifier's authenticated
attestation, this gate must NOT issue FACT_VERIFIED_IN_SCOPE, B04 master merge,
or personalized advisory approval. All indicators are fail-closed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

RESOLVED=Path('ire/v5/validation/first_five_40_open5_resolution_20261106.json')
B04=Path('ire/v5/legacy_consolidation/B04_FIRST40_SCOPED_EDUCATION_EDGES_20261106.json')
OLD=Path('ire/v5/validation/first_five_40_scoped_fact_knowledge_review_20261106.json')
BASELINE=Path('data/claims.jsonl')
MASTER_BLOB_SHA='ab5af7eea02e65d5e36174546a2a94f4cc642d92'
SOURCE_EVENT_SHA='9f0685b2b1f8b95c2eefa7708e8ae1ad8d1bd567d40e84e1d6b2d04aed81874e'
SOURCE_ZIP_SHA='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
SOURCE_SRT_SHA='2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f'
EXPECTED_STATUS={
  'V5C0266':('W00006','SCOPED_LEGAL_FACT_WITH_2026_EXCEPTION'),
  'V5C0267':('W00006','PERSONAL_TAX_OUTCOME_NOT_PROVEN'),
  'V5C0287':('W00014','TAX_WITHHOLDING_VS_FILING_CLARIFIED'),
  'V5C0405':('W00023','EFFECTIVE_RATE_OVERGENERALIZATION_REJECTED'),
  'V5C0430':('W00026','PROGRESSIVE_BRACKETS_SCOPE_CONFIRMED')}
AUTH_KEYS={'NTS_RATE2026','LAW_129','NPS_TAX_FAQ','LAW_40','LAW_14','LAW_55','NTS_TAXBRACKET'}
_ALLOWED={'www.nts.go.kr','nts.go.kr','www.nps.or.kr','nps.or.kr','law.go.kr','www.law.go.kr'}
_SHA64=re.compile(r'^[0-9a-f]{64}$')

class FormalGateError(ValueError):pass

def need(ok:bool,code:str):
 if not ok:raise FormalGateError(code)

def canonical(x):
 return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')

def sha256(x:bytes):return hashlib.sha256(x).hexdigest()

def git_blob_sha(b:bytes):
 return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

def verify_bundle(old:dict,resolution:dict,b04:dict,prior:list[dict]) -> dict:
 """Pure verifier; production wrapper verifies the actual master file and old gate."""
 need(old['schema']=='IRE_V5_VIDEO1_FIRST40_SCOPED_FINANCE_FACT_REVIEW_V1','FIRST40_BAD_OLD_LEDGER')
 need(old['reviewed_claims_count']==97 and old['reviewed_rule_claims_count']==20
      and old['unresolved_rule_composites']==5 and len(old['claims'])==97,'FIRST40_SCOPE_DRIFT')
 need(old['video1_20to40_event_head_sha256']==SOURCE_EVENT_SHA
      and old['source_srt_sha256']==SOURCE_SRT_SHA,'SOURCE_EVENT_DRIFT')
 need(resolution.get('schema')=='IRE_V5_VIDEO1_FIRST40_FIVE_OPEN_RULE_TERMINAL_REVIEW_V1'
      and resolution.get('as_of')=='2026-11-06'
      and resolution.get('source_zip_sha256')==SOURCE_ZIP_SHA
      and resolution.get('source_srt_sha256')==SOURCE_SRT_SHA
      and resolution.get('video_id')==old['video_id']=='sz5N9WJS310'
      and resolution.get('source_event_chain_head_sha256')==SOURCE_EVENT_SHA
      and resolution.get('prior_master_git_blob_sha')==MASTER_BLOB_SHA,
      'RULE_RESOLUTION_IDENTITY_DRIFT')
 need(resolution.get('authority_text_byte_snapshots_pinned') is False
      and resolution.get('formal_2026_current_law_certification_from_signature') is False
      and resolution.get('full_rule_claims_newly_certified')==0
      and resolution.get('finance_personal_advice_release')=='BLOCKED'
      and resolution.get('existing_97_source_claims_modified') is False,
      'FALSE_FINANCIAL_FACT_APPROVAL')
 auth=resolution.get('authorities')
 need(type(auth) is dict and set(auth)==AUTH_KEYS,'RULE_AUTHORITY_SET_CHANGED')
 for sid,u in auth.items():
  parsed=urlparse(u.get('url',''))
  need(parsed.scheme=='https' and parsed.hostname in _ALLOWED,'NONOFFICIAL_AUTHORITY')
  need(u.get('observed_date')=='2026-11-06'
       and u.get('source_kind')=='WEB_OBSERVED_AUTHORITY_PARAPHRASE_NOT_OFFICIAL_BYTE_SNAPSHOT',
       'AUTHORITY_CLAIMS_UNPROVEN_SNAPSHOT')
  need(len(u.get('evidence',''))>=35 and len(u.get('section',''))>=8
       and _SHA64.fullmatch(u.get('paraphrase_sha256','')) is not None
       and u['paraphrase_sha256']==sha256(u['evidence'].encode()),
       'AUTHORITY_PARAPHRASE_TAMPERED')
  need(re.fullmatch(r'2026-\d\d-\d\d|GUIDANCE_REVIEWED_2026-11-06',u.get('effective_date','')) is not None,
       'AUTHORITY_EFFECTIVE_SCOPE_MISSING')
 need(auth['NTS_RATE2026']['effective_date']=='2026-01-01'
      and '2026' in auth['NTS_RATE2026']['evidence']
      and '종신' in auth['NTS_RATE2026']['evidence'],
      'PENSION_2026_RATE_CHANGE_OMITTED')
 old_by_id={c['claim_id']:c for c in old['claims']}
 need(len(old_by_id)==97,'FIRST40_DUPLICATE_CLAIMS')
 reviews=resolution.get('open_five_review_outcomes')
 need(type(reviews) is list and len(reviews)==5
      and {c.get('claim_id') for c in reviews}==set(EXPECTED_STATUS),
      'RULE_FIVE_TERMINAL_CENSUS_MISSING')
 for row in reviews:
  cid=row['claim_id'];src=old_by_id[cid];win,st=EXPECTED_STATUS[cid]
  need(src['review_status']=='REGULATORY_COMPOSITE_OPEN'
       and src['kind']=='RULE' and row.get('window_id')==win
       and row.get('final_review_disposition')==st,'OPEN_FIVE_WHOLE_CLAIM_UNSAFELY_APPROVED')
  need(row.get('original_claim_payload_sha256')==src['claim_payload_sha256']
       and row.get('original_source_refs_sha256')==src['source_cue_refs_sha256']
       and row.get('source_cue_indices')==src['source_cue_indices'],
       'SPEAKER_ORIGINAL_SOURCE_LINK_TAMPERED')
  need(row.get('legacy_prior_ids')==src['existing_prior_candidates'],'B04_ORIGINAL_PRIOR_CANDIDATES_CHANGED')
  need(row.get('terminal_review') is True
       and row.get('claim_specific_correction_recommended') is True
       and row.get('full_video_speaker_claim_certified') is False
       and row.get('v5_kernel_FACT_VERIFIED_IN_SCOPE_event_issued') is False
       and row.get('person_specific_tax_advice_approved') is False,
       'UNAUTHORIZED_KERNEL_APPROVAL')
  need(len(row.get('blocked_inference',''))>=25
       and len(row.get('legally_supported_narrow_scope',''))>=25
       and row.get('review_date')=='2026-11-06'
       and row.get('reviewer_origin')=='ACTIVE_CHAT_HOST_SOURCE_SCOPED_NOT_INDEPENDENT_EXPERT',
       'RULE_NO_LIMITED_DISPOSITION')
  official_ids=row.get('official_authority_ids')
  need(type(official_ids) is list and len(official_ids)>=2
       and len(official_ids)==len(set(official_ids))
       and all(x in AUTH_KEYS for x in official_ids),'RULE_MISSING_DIRECT_OFFICIAL_SCOPE')
 need(resolution['unresolved_5_review_dispositions_remaining']==0
      and resolution['official_narrow_education_explanations_available']==5,
      'RULE_RESOLUTION_COUNT_MISMATCH')
 need(b04.get('schema')=='IRE_V5_B04_C61_C80_FIRST40_SCOPED_RELATION_DECISION_V1'
      and b04.get('as_of')=='2026-11-06'
      and b04.get('baseline_git_blob_sha')==MASTER_BLOB_SHA
      and b04.get('source_video_id')=='sz5N9WJS310'
      and b04.get('source_video_event_head_sha256')==SOURCE_EVENT_SHA
      and b04.get('B04_existing_master_claim_id_range')==['GOMHEE-C61','GOMHEE-C80']
      and b04.get('B04_specific_existing_targets')==['GOMHEE-C66','GOMHEE-C78'],
      'B04_BASELINE_OR_SCOPE_UNVERIFIED')
 need(b04.get('B04_legacy_master_rewritten') is False
      and b04.get('legacy_supporting_videos_modified') is False
      and b04.get('actual_direct_personal_investment_advice_approval') is False
      and b04.get('B04_formal_master_fact_merge_completed') is False
      and b04.get('strict_relation_policy')=='EDUCATIONAL_LINK_ACCEPTED_ONLY_WITH_PRESERVED_BASELINE_AND_NO_EXACT_EQUIVALENCE',
      'B04_MASTER_PROMOTED_WITHOUT_FACT_VERIFICATION')
 overlay={n['knowledge_id']:n for n in old['knowledge_overlay']}
 need(len(overlay)==len(old['knowledge_overlay'])==9
      and b04.get('related_first40_overlay_nodes')==9,
      'B04_LOST_OVERLAY_PROVENANCE')
 prior_by_id={p['claim_id']:p for p in prior}
 need(len(prior_by_id)==len(prior)==116,'B04_BASELINE_CLAIMS_UNAVAILABLE')
 all_prior_ids={f'GOMHEE-C{i:02d}' if i<100 else f'GOMHEE-C{i}' for i in range(1,117)}
 need(set(prior_by_id)==all_prior_ids,'B04_MASTER_116_IDS_CHANGED')
 expected=[];cross=[]
 for node in old['knowledge_overlay']:
  for pid in node['prior_claim_ids']:
   p=prior_by_id.get(pid)
   need(p is not None and 'sz5N9WJS310' not in p.get('supporting_videos',[]),'B04_HISTORICAL_VIDEO_PROVENANCE_FABRICATED')
   entry=(pid,node['knowledge_id'],tuple(node['source_claim_ids']),tuple(node['official_source_ids']))
   (expected if pid in {'GOMHEE-C66','GOMHEE-C78'} else cross).append(entry)
 edges=b04.get('B04_scoped_education_edges')
 outside=b04.get('cross_batch_edges_not_promoted_here')
 need(type(edges) is list and len(edges)==6 and type(outside) is list and len(outside)==9
      and b04.get('B04_authorized_scoped_education_edges_count')==6,
      'B04_EDGES_COUNT_OR_PARTITION_INVALID')
 for rows,expected_keys,scope in ((edges,expected,'SCOPED_EDUCATION_EDGE_ACCEPTED_NOT_LEGACY_MASTER_MERGED'),
                                  (outside,cross,'OUT_OF_B04_CROSS_BATCH_REVIEW_ONLY')):
  actual=[]
  for e in rows:
   pid=e.get('prior_claim_id');n=overlay.get(e.get('knowledge_id'))
   need(n is not None and pid in n['prior_claim_ids'],'B04_EDGE_FABRICATED')
   need(e.get('video1_claim_ids')==n['source_claim_ids']
        and e.get('official_source_ids')==n['official_source_ids']
        and e.get('source_video_id')=='sz5N9WJS310'
        and e.get('link_status')==scope
        and e.get('equality_decision')=='EXTENDS_SCOPE_NOT_EXACT_DUPLICATE'
        and e.get('personal_advice_release') is False
        and e.get('historical_supporting_videos_unchanged') is True,
        'B04_UNSAFE_SEMANTIC_OR_FACT_MERGE')
   actual.append((pid,n['knowledge_id'],tuple(e['video1_claim_ids']),tuple(e['official_source_ids'])))
  need(sorted(actual)==sorted(expected_keys) and len(actual)==len(set(actual)),
       'B04_CROSS_BATCH_MISSING_OR_DUPLICATE_EDGE')
 return {'schema':'IRE_V5_FIRST40_OPEN5_FINAL_DISPOSITION_B04_SAFE_LINK_GATE_V1',
         'five_composite_reviews_terminal':len(reviews),
         'open5_review_tasks_remaining':0,
         'full_five_original_claims_approved':0,
         'official_2026_scope_records':len(auth),
         'b04_scope_accepted_education_edges':len(edges),
         'outside_b04_links_unmerged':len(outside),
         'existing_master_116_originals_mutated':0,
         'formal_B04_master_fact_merge_approved':False,
         'v5_kernel_official_financial_facts_approved':0,
         'unverified_official_source_bytes_pretended_pinned':False,
         'personal_advice_release':'NO_GO',
         'private_replay':None}

def authorize_formal_financial_fact(attestation:dict | None) -> dict:
 """Deliberately non-self-authorizing until a separate trusted verifier ships.

 The chat host and GitHub CI are not signing authorities for official-source
 byte snapshots. A user-provided flag, checksum or claimed verifier identity is
 never enough for FACT_VERIFIED_IN_SCOPE. Reject all such attempts for now.
 """
 if not isinstance(attestation,dict):
  return {'authorized':False,'reason':'NO_AUTHENTICATED_INDEPENDENT_VERIFIER'}
 if attestation.get('raw_official_source_bytes_verified') is not True:
  return {'authorized':False,'reason':'NO_OFFICIAL_SOURCE_BYTE_SNAPSHOT'}
 if attestation.get('verifier_credential_registry_match') is not True:
  return {'authorized':False,'reason':'NO_AUTHENTICATED_INDEPENDENT_VERIFIER'}
 # No trusted signed-verifier registry exists. Never treat self-attestation
 # as an external signature; only a separate independently reviewed release
 # may introduce such a registry and its cryptographic verification.
 return {'authorized':False,'reason':'TRUSTED_VERIFIER_REGISTRY_NOT_IMPLEMENTED'}

def verify(root:Path,private_root:Path|None=None) -> dict:
 root=Path(root).resolve()
 from ire.v5.first_five_40_scoped_fact_gate import load as old_load,private_source_verify
 old=old_load(root)
 resolution=json.loads((root/RESOLVED).read_text('utf-8'))
 b04=json.loads((root/B04).read_text('utf-8'))
 blob=(root/BASELINE).read_bytes()
 need(git_blob_sha(blob)==MASTER_BLOB_SHA,'B04_MASTER_GIT_BLOB_CHANGED')
 prior=[json.loads(line) for line in blob.decode('utf-8').splitlines() if line.strip()]
 # Resolve exact ledger byte digest without trusting a self-asserted source hash.
 need(resolution.get('previous_scoped_review_sha256')==sha256((root/OLD).read_bytes()),
      'B04_OLD_REVIEW_HASH_CHANGED')
 summary=verify_bundle(old,resolution,b04,prior)
 if private_root is not None:
  check=private_source_verify(old,Path(private_root))
  need(check['source_claims_directly_replayed']==97 and check['source_windows_reviewed']==40,
       'PRIVATE_97_CLAIM_REPLAY_FAILED')
  summary['private_replay']=check
 return summary

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'))
 p.add_argument('--private-root',type=Path)
 a=p.parse_args();print(json.dumps(verify(a.root,a.private_root),ensure_ascii=False,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
