"""Fail closed for #1-#5 private unsealed V5 packet hash pointer.
No private SRT or event bodies are inspected in GitHub CI. This gate is NOT
source-byte replay nor a closure/fact/advice release.
"""
from __future__ import annotations
import argparse,copy,json,re
from pathlib import Path

REL=Path('ire/v5/validation/first_five_private_event_pointer_20261106.json')
RULE=Path('ire/v5/validation/official_rule_scope_20261106.json')
PUBLIC=Path('ire/v5_app/batch_states/v5-gomhee-001-005-batch.json')
VIDS=('sz5N9WJS310','6VEfKF7BzZU','OiDTNstaSpM','aNfGrcO6WPI','qtluAViPpsQ')
WINDOWS=(67,76,44,43,58)
CUES=(1195,1347,785,758,1044)
SHA=re.compile(r'^[0-9a-f]{64}$')

class EventIndexError(ValueError):pass

def check(ok,why):
 if not ok:raise EventIndexError(why)

def verify(root:Path, replacement:dict|None=None)->dict:
 root=Path(root)
 idx=json.loads((root/REL).read_text('utf8')) if replacement is None else replacement
 laws=json.loads((root/RULE).read_text('utf8'))
 old=json.loads((root/PUBLIC).read_text('utf8'))
 check(idx.get('schema')=='IRE_V5_FIVE_PRIVATE_PROVISIONAL_EVENT_INDEX_V1' and idx.get('as_of')=='2026-11-06',
       'PRIVATE_EVENT_INDEX_SCHEMA_OR_DATE_INVALID')
 check(idx.get('original_public_batch_processed_windows')==5 and
       idx.get('original_public_batch_remaining_windows')==283 and
       old.get('windows_processed_reported')==5 and old.get('windows_remaining_reported')==283 and
       old.get('source_and_receipts_readable_by_github') is False,
       'PRIVATE_EVENT_FALSE_PUBLIC_COMPLETION')
 check(idx.get('new_private_PROVISIONAL_model_windows')==288 and
       idx.get('source_cues_total')==5129 and
       idx.get('private_source_anchor_claims_with_evidence_and_relation')==258 and
       idx.get('preexisting_68_span_only_claims_migration_blocked_without_atomic_cue_reference')==68 and
       idx.get('unresolved_cues_blocking_formal_closure')==4908 and
       idx.get('private_event_chain_files')==5,
       'PRIVATE_EVENT_COUNTERS_CHANGED')
 check(idx.get('owner_private_archive_not_committed_to_git') is True and
       idx.get('events_and_srt_stored_in_owner_private_bundle_only') is True and
       idx.get('source_bytes_reopened_by_github_ci') is False and
       idx.get('actual_repo_ResearchRun_replay_executed_in_this_turn') is False and
       idx.get('no_RESEARCH_CLOSURE_event_created') is True and
       idx.get('all_original_288_windows_final_research_complete') is False and
       idx.get('all_financial_facts_independently_approved') is False and
       idx.get('personal_advice_approved') is False and
       idx.get('formal_claim_approval_count')==0,
       'PRIVATE_EVENT_FALSE_RELEASE_CLAIM')
 check(type(idx.get('videos')) is list and len(idx['videos'])==5,
       'PRIVATE_EVENT_VIDEO_COUNT_CHANGED')
 for video,vid,w,c in zip(idx['videos'],VIDS,WINDOWS,CUES):
  check(video.get('video_id')==vid and video.get('window_count')==w and
        video.get('provisional_v5_model_subactions')==w and video.get('source_cues')==c and
        video.get('sealed_final_research_receipt') is False and
        video.get('legacy_public_window_count_not_changed') is True and
        SHA.fullmatch(str(video.get('event_chain_head_sha256'))) and
        SHA.fullmatch(str(video.get('original_srt_sha256'))),
        'PRIVATE_EVENT_VIDEO_SOURCE_OR_SEAL_MISMATCH')
 check(sum(x['provisional_evidence_and_relation_each'] for x in idx['videos'])==258 and
       sum(x['unresolved_cues'] for x in idx['videos'])==4908,
       'PRIVATE_EVENT_CLAIM_OR_CUE_SUM_MISMATCH')
 check(laws.get('schema')=='IRE_V5_FINANCIAL_RULE_41_OFFICIAL_SCOPE_REFRESH_V1' and
       len(laws.get('cases',[]))==41 and
       laws.get('prior_open_cases')==34 and
       laws.get('newly_scoped_from_prior_open')==34 and
       idx.get('new_34_narrow_official_framework_supported_not_personal')==laws.get('new_officially_scoped_case_frameworks')==23 and
       len(laws.get('official_registry',{}))==idx.get('source_authority_catalog_count') and
       laws.get('all_34_personal_applicability_established') is False and
       laws.get('any_personalized_trade_or_tax_recommendation_approved') is False and
       all(r.get('formal_independent_fact_signature') is None and
           r.get('automated_financial_fact_approval') is False and
           r.get('can_merge_legacy_B04_directly') is False for r in laws['cases']),
       'PRIVATE_EVENT_OFFICIAL_RULES_FALSLY_CERTIFIED')
 return {'schema':'IRE_V5_PRIVATE_SOURCE_EVENT_POINTER_CI_V1',
         'public_reference_matches':True,'private_original_bytes_reopened_by_ci':False,
         'real_v5_engine_replay_of_private_events_by_ci':False,
         'independently_source_anchored_claims_publicly_proven':False,
         'provisional_model_windows_private_only':288,
         'provisional_claim_review_actions_private_only':258,
         'unresolved_cues':4908,
         'new_34_rule_candidates_narrowly_scoped':34,
         'new_34_with_official_framework_narrow_support':23,
         'new_34_without_narrow_rule_certification':11,
         'research_closure':'BLOCKED','advisory_release':'NO_GO'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));a=p.parse_args()
 print(json.dumps(verify(a.root),ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
