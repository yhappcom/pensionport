"""V116 source-bound private semantic challenges and finance/prior review gates.

WARNING: these gates establish that a host-supplied analysis is linked to real
original subtitles; they cannot autonomously generate or certify ALL claims.
All source transcripts and proposed text remain owner-private. Public receipts
include no quotation, individual investment advice, or private original text.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from time import perf_counter_ns
from urllib.parse import urlsplit

from v115_full_video_bridge import (audit_private_review, parse_exact_srt,
                                    sha as source_sha, UnsafeResearchStage,
                                    resume_prepared_five_stage_run)

HEX = re.compile(r'[0-9a-f]{64}\Z')
ISSUE = re.compile(r'V116_C[0-9]{3}\Z')
PART = re.compile(r'V116_C[0-9]{3}_P[0-9]{2}\Z')
VIDEO = re.compile(r'[A-Za-z0-9_-]{11}\Z')
ALLOWED_CHALLENGES = {
    'COMPOUND_ATOM','CROSS_CUE_QUALIFIER','SPEAKER_SELF_CONTRAST',
    'CURRENT_LAW_EXCEPTION','NONPAYMENT_POLICY','NUMERIC_OR_PRICE_SCOPE',
    'SCREEN_SOURCE_REQUIRED','RECORD_DATE_ASSUMPTION','PRIOR_KNOWLEDGE_BOUNDARY',
}
PART_KINDS = {
    'SPEAKER_ASSERTION','SPEAKER_QUESTION','SPEAKER_EXAMPLE',
    'SPEAKER_QUALIFIER','SPEAKER_CONTRAST','REVIEWER_COUNTEREVIDENCE',
    'REVIEWER_EXCEPTION','REVIEWER_APPLICABILITY_LIMIT',
}
REVIEW_STATUSES={'INTERNAL_ANALYSIS_OPEN','ORIGINAL_AUDIO_OPEN','SCREEN_EVIDENCE_OPEN'}
RISK={'LOW','CONTEXTUAL','HIGH','CRITICAL'}
PREVIEW_STATUS={'TOPIC_RELATED_PENDING','POSSIBLE_CONFLICT_PENDING',
                'EQUIVALENCE_UNDETERMINED'}
EVIDENCE_STATE={'GOVERNMENT_INDEXED_LAW_LIVE_BODY_UNAVAILABLE',
                'ISSUER_NOTICE_SEARCH_INDEX_ONLY','ISSUER_NOTICE_LIVE_TEXT_VERIFIED',
                'KRX_INDEXED_GUIDANCE_ONLY','NO_DOCUMENT_SOURCE_OPEN'}
OFFICIAL_DOMAINS=('law.go.kr','krx.co.kr','nts.go.kr','fss.or.kr','fsc.go.kr',
                  'plusetf.co.kr','riseetf.co.kr')
LEGACY_MASTER_BLOB='ab5af7eea02e65d5e36174546a2a94f4cc642d92'
P4_EDU22_BLOB='bfb446ffb1dd40caa1ed03088d088c9a1ba7490f'
# Five actual existing prior identities were read from the protected V5 sources.
# This narrow allowlist is only a topic-preview guard, not full 116-row replay.
PINNED_PRIOR_IDS={
 'MASTER116':frozenset({'GOMHEE-C17','GOMHEE-C24','GOMHEE-C34'}),
 'P4_EDUCATION22':frozenset({'EDU-ETF-NAV-TRACKING',
                              'EDU-ETF-TOTAL-COST-DECISION'}),
}


def fail(ok,reason):
    if not ok:raise UnsafeResearchStage('V116_'+reason)


def digest(x):
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,
                 separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()


def sorted_unique_indices(v,max_i):
    return (type(v) is list and len(v)>0 and all(type(i) is int and
            1<=i<=max_i for i in v) and v==sorted(set(v)))


def verify_original_challenges(*,srt_raw,base_ledger,base_docket,challenges,
                               expected_srt_sha256,owner_zip_sha256):
    """Source replay + exact challenge/facet lineage, without fake semantic recall."""
    start=perf_counter_ns()
    owner=audit_private_review(raw_srt=srt_raw,ledger=base_ledger,
             docket=base_docket,expected_srt_sha256=expected_srt_sha256,
             expected_zip_sha256=owner_zip_sha256,private_zip_sha256=owner_zip_sha256)
    cues=parse_exact_srt(srt_raw)
    n=len(cues);bycue={c['cue_index']:c for c in cues}
    fail(type(challenges) is dict and set(challenges)=={
         'schema','video_id','original_srt_sha256','source_v115_atom_digest_sha256',
         'independent_gold','all_claims_certified','p0_go','cases'},'CHALLENGE_SCHEMA')
    fail(challenges['schema']=='V116_OWNER_SEMANTIC_SPLIT_AND_CONTEXT_CHALLENGES_V1' and
         challenges['video_id']==base_ledger['source_video_id'] and
         challenges['original_srt_sha256']==expected_srt_sha256 and
         challenges['source_v115_atom_digest_sha256']==digest(base_ledger['atom_proposals']),
         'CHALLENGE_SOURCE_OR_BASE_DRIFT')
    for flag in ('independent_gold','all_claims_certified','p0_go'):
        fail(challenges[flag] is False,'FALSE_SEMANTIC_COMPLETION_'+flag)
    cases=challenges['cases']
    fail(type(cases) is list and cases and len(cases)<=160,'CHALLENGE_CASES')
    baseline={u['unit_id']:u for u in base_ledger['atom_proposals']}
    seen_cases=set();seen_parts=set(); covered=set(); roles={};per_type={}
    high_cases=0;part_count=0; cross_source_count=0
    for case in cases:
        fail(type(case) is dict and set(case)=={
            'case_id','review_kind','source_cue_indices','source_cue_sha256',
            'baseline_unit_ids','provisional_parts','risk','review_status',
            'source_context_reason','source_resolution','human_blind_independent',
            'financial_truth_approved','has_per_cue_original_replay'},'CHALLENGE_CASE_FIELDS')
        cid=case['case_id']; pos=case['source_cue_indices']
        fail(type(cid) is str and ISSUE.fullmatch(cid) and cid not in seen_cases,
             'CHALLENGE_CASE_DUPLICATE')
        seen_cases.add(cid)
        fail(case['review_kind'] in ALLOWED_CHALLENGES and
             sorted_unique_indices(pos,n),'CHALLENGE_SCOPE_OR_KIND')
        fail([bycue[i]['cue_sha256'] for i in pos]==case['source_cue_sha256'],
             'CHALLENGE_SOURCE_CUE_SHA_DRIFT')
        linked=case['baseline_unit_ids']
        fail(type(linked) is list and linked and linked==sorted(set(linked)) and
             set(linked)<=set(baseline),'CHALLENGE_ORIGINAL_ATOM_REF_INVALID')
        union=set(i for uid in linked for i in baseline[uid]['cue_indices'])
        fail(set(pos)<=union,'CHALLENGE_REBOUND_ORIGINAL_UNITS')
        fail(case['risk'] in RISK and case['review_status'] in REVIEW_STATUSES and
             case['source_resolution']=='OPEN_NOT_INDEPENDENT_GOLD' and
             case['human_blind_independent'] is False and
             case['financial_truth_approved'] is False and
             case['has_per_cue_original_replay'] is True,'CHALLENGE_UNEARNED_APPROVAL')
        fail(type(case['source_context_reason']) is str and
             20<=len(case['source_context_reason'].strip())<=1700,
             'CHALLENGE_CONTEXT_EXPLANATION')
        parts=case['provisional_parts']
        fail(type(parts) is list and 2<=len(parts)<=10,'CHALLENGE_PART_SPLIT_REQUIRED')
        roles[cid]=set(); part_source=set()
        for p in parts:
            fail(type(p) is dict and set(p)=={
                 'part_id','kind','cue_indices','cue_sha256','meaning_private',
                 'origin','approval_state','current_law_scope_confirmed'},
                 'CHALLENGE_PART_FIELDS')
            pid=p['part_id']; links=p['cue_indices']
            fail(type(pid) is str and PART.fullmatch(pid) and pid.startswith(cid+'_')
                 and pid not in seen_parts,'CHALLENGE_PART_ID')
            seen_parts.add(pid)
            fail(p['kind'] in PART_KINDS and sorted_unique_indices(links,n)
                 and set(links)<=set(pos),'CHALLENGE_PART_SOURCE_CUES')
            fail([bycue[i]['cue_sha256'] for i in links]==p['cue_sha256'],
                 'CHALLENGE_PART_EXACT_SOURCE_HASH')
            fail(type(p['meaning_private']) is str and
                 12<=len(p['meaning_private'].strip())<=1600,'CHALLENGE_MISSING_MEANING')
            fail(p['origin'] in ('SRT_SPEAKER_PROPOSAL','CHAT_REVIEWER_QUALIFICATION') and
                 p['approval_state']=='HOST_PROPOSED_OPEN' and
                 p['current_law_scope_confirmed'] is False,
                 'CHALLENGE_PART_FALSE_GO')
            fail((p['kind'].startswith('SPEAKER_') and p['origin']=='SRT_SPEAKER_PROPOSAL')
                 or (p['kind'].startswith('REVIEWER_') and
                     p['origin']=='CHAT_REVIEWER_QUALIFICATION'),
                 'REVIEWER_CORRECTION_MISATTRIBUTED_TO_SPEAKER')
            roles[cid].add(p['kind']);part_source.update(links);part_count+=1
        fail(set(pos)==part_source,'CHALLENGE_UNCOVERED_SOURCE_POSITION')
        if case['review_kind']=='CURRENT_LAW_EXCEPTION':
            fail('REVIEWER_EXCEPTION' in roles[cid] and
                 'SPEAKER_ASSERTION' in roles[cid], 'CHALLENGE_MISSING_LAW_COUNTEREVIDENCE')
        if case['review_kind']=='SCREEN_SOURCE_REQUIRED':
            fail(case['review_status']=='SCREEN_EVIDENCE_OPEN',
                 'SCREEN_CASE_MUST_STAY_OPEN')
        if case['risk'] in ('HIGH','CRITICAL'):high_cases+=1
        covered.update(pos);cross_source_count+=int(len(linked)>1)
        per_type[case['review_kind']]=per_type.get(case['review_kind'],0)+1
    fail(any(k.startswith('REVIEWER') for row in roles.values() for k in row),
         'REVIEWER_CORRECTIONS_MISSING')
    # Includes all underlying source positions in the independently preserved V115
    # 152-cue baseline. This does not assert all original semantic propositions.
    return {'schema':'V116_PRIVATE_REAL_SRT_CHALLENGE_AUDIT_PUBLIC_SHA_ONLY',
            'source_video_id':challenges['video_id'],
            'original_srt_sha256':expected_srt_sha256,
            'baseline_source_cues':owner['original_cues'],
            'baseline_cues_unaccounted':owner['source_cues_unaccounted'],
            'challenge_cases':len(cases),'provisional_atomic_facets':part_count,
            'challenged_unique_cue_positions':len(covered),
            'multi_parent_context_challenges':cross_source_count,
            'high_or_critical_cases':high_cases,
            'challenge_kinds':dict(sorted(per_type.items())),
            'source_challenge_digest_sha256':digest(challenges),
            'original_audio_confirmed':False,
            'gold_certified':False,'semantic_recall':None,
            'financial_fact_approved':0,'p0_go':False,
            'code_audit_wall_ns':perf_counter_ns()-start}


def _validate_official_url(url):
    fail(type(url) is str and len(url)<=1500,'EVIDENCE_URL_INVALID')
    try:
        u=urlsplit(url)
        valid = (u.scheme=='https' and bool(u.hostname) and
                 u.username is None and u.password is None and
                 u.fragment=='' and u.port is None)
    except ValueError:
        valid=False
    fail(valid and any(u.hostname.lower()==host or
             u.hostname.lower().endswith('.'+host) for host in OFFICIAL_DOMAINS),
         'UNTRUSTED_OFFICIAL_OR_ISSUER_HOST')
    return url


def audit_current_regulatory_evidence(*,challenge_doc,official_record,
                                     baseline_finance_docket):
    """Versioned law and issuer evidence-pointer review; no live-body claim."""
    t0=perf_counter_ns()
    fail(type(official_record) is dict and set(official_record)=={
      'schema','as_of','law_article_id','legal_effective_date',
      'tax_change_applies_from','old_claim_universal_tr_elimination',
      'domestic_equity_tr_exception_exists',
      'live_law_site_status','original_law_html_sha256',
      'official_body_bytes_verified','independent_finance_gold',
      'financial_facts_approved','personal_advice_approved',
      'asof_source_pointers','per_challenge_outcomes'},'FINANCE_SCHEMA')
    fail(official_record['schema']=='V116_INDEXED_LAW_PLUS_ISSUER_POINTERS_NO_RAW_BODY_V1',
         'FINANCE_SCHEMA_VERSION')
    fail(official_record['as_of']=='2026-11-14' and
         official_record['law_article_id']=='소득세법 시행령 제26조의2' and
         official_record['legal_effective_date']=='2026-10-01' and
         official_record['tax_change_applies_from']=='2025-07-01',
         'FINANCE_EFFECTIVE_DATE_OR_ARTICLE')
    fail(official_record['old_claim_universal_tr_elimination'] is False and
         official_record['domestic_equity_tr_exception_exists'] is True,
         'FINANCE_RULE_MISGENERALIZED')
    fail(official_record['live_law_site_status']=='MAINTENANCE_HTML_ON_2026_11_14' and
         official_record['original_law_html_sha256'] is None and
         official_record['official_body_bytes_verified'] is False,
         'LIVE_ORIGINAL_LAW_BODY_FALSE_VERIFIED')
    fail(official_record['independent_finance_gold'] is False and
         official_record['financial_facts_approved']==0 and
         official_record['personal_advice_approved'] is False,
         'FINANCE_FALSE_APPROVAL')
    citations=official_record['asof_source_pointers'];fail(type(citations) is list and len(citations)>=3,
                                                         'FINANCE_OFFICIAL_POINTERS_REQUIRED')
    roles={};types={}
    for citation in citations:
        fail(type(citation) is dict and set(citation)=={
          'source_id','kind','url','observed_date','index_date',
          'evidence_state','raw_source_body_sha256'},'FINANCE_SOURCE_POINTER_FIELDS')
        fail(type(citation['source_id']) is str and citation['source_id'] not in roles,
             'FINANCE_SOURCE_ID_DUPLICATE')
        fail(citation['kind'] in ('CURRENT_STATUTE','ISSUER_NOTICE','EXCHANGE_GUIDANCE') and
             citation['evidence_state'] in EVIDENCE_STATE and
             citation['observed_date']=='2026-11-14' and
             citation['raw_source_body_sha256'] is None,
             'FINANCE_POINTER_CLAIMS_LIVE_BODY')
        if citation['kind']=='CURRENT_STATUTE':
            fail(citation['evidence_state']==
                 'GOVERNMENT_INDEXED_LAW_LIVE_BODY_UNAVAILABLE',
                 'FINANCE_STATUTE_LIVE_OR_NOT_PINNED')
        _validate_official_url(citation['url'])
        roles[citation['source_id']]=citation
        types[citation['kind']]=types.get(citation['kind'],0)+1
    fail(types.get('CURRENT_STATUTE',0)>=1 and types.get('ISSUER_NOTICE',0)>=2,
         'FINANCE_LAW_AND_TWO_ISSUERS_REQUIRED')
    cases={c['case_id']:c for c in challenge_doc['cases']}
    outcomes=official_record['per_challenge_outcomes']
    fail(type(outcomes) is list and len(outcomes)==len(cases),'FINANCE_ALL_CHALLENGES_REQUIRE_DISPOSITION')
    seen=set();linked=0
    for item in outcomes:
        fail(type(item) is dict and set(item)=={
          'case_id','related_v115_unit_ids','evidence_source_ids','evidence_state',
          'scope_open','original_audio_or_visual_open','verified_financial_claim',
          'reviewer_status','as_of'},'FINANCE_CHALLENGE_OUTCOME_FIELDS')
        cid=item['case_id']
        fail(cid in cases and cid not in seen,'FINANCE_CHALLENGE_UNKNOWN_OR_DUP')
        seen.add(cid)
        fail(item['related_v115_unit_ids']==cases[cid]['baseline_unit_ids'],
             'FINANCE_REBINDING_TO_OTHER_SEMANTICS')
        srcids=item['evidence_source_ids']
        fail(type(srcids) is list and srcids==sorted(set(srcids)) and
             set(srcids)<=set(roles),'FINANCE_UNKNOWN_SOURCE_ID')
        fail(item['evidence_state'] in EVIDENCE_STATE and
             item['scope_open'] is True and
             item['verified_financial_claim'] is False and
             item['reviewer_status']=='OPEN_NOT_FOR_ADVICE' and
             item['as_of']=='2026-11-14','FINANCE_UNEARNED_STATUS')
        if cases[cid]['review_kind']=='CURRENT_LAW_EXCEPTION':
            fail(any(roles[s]['kind']=='CURRENT_STATUTE' for s in srcids) and
                 any(roles[s]['kind']=='ISSUER_NOTICE' for s in srcids),
                 'FINANCE_LAW_CLAIM_NEEDS_STATUTE_AND_ISSUER')
        if cases[cid]['review_kind']=='SCREEN_SOURCE_REQUIRED':
            fail(item['original_audio_or_visual_open'] is True,
                 'FINANCE_SCREEN_MUST_REMAIN_OPEN')
        linked+=bool(srcids)
    fail(len(baseline_finance_docket)==26 and
         all(row['approved'] is False for row in baseline_finance_docket),
         'V115_FINANCE_DOCKET_DRIFT')
    return {'schema':'V116_FINANCE_REVIEW_ONLY_CURRENT_SCOPE_SHA_V1',
            'original_v115_fact_candidate_rows':len(baseline_finance_docket),
            'challenged_cases_with_open_disposition':len(outcomes),
            'cases_linked_to_source_pointers':linked,
            'reviewed_source_pointer_count':len(roles),
            'current_law_effective_date':official_record['legal_effective_date'],
            'rule_change_income_effective_date':official_record['tax_change_applies_from'],
            'law_original_html_pinned':False,
            'original_audio_video_verified':False,
            'new_fact_approvals':0,'independent_gold':False,'p0_go':False,
            'evidence_pointer_digest_sha256':digest(official_record),
            'code_audit_wall_ns':perf_counter_ns()-t0}


def audit_readonly_prior_preview(*,challenge_doc,prior_review):
    """Source-to-legacy candidate IDs with pinned Git blob identities; no merges."""
    t0=perf_counter_ns()
    fail(type(prior_review) is dict and set(prior_review)=={
      'schema','source_video_id','master116_git_blob_sha1','p4_22_git_blob_sha1',
      'historical_v75_identity_recovered','full_history_dedup_completed',
      'master_or_p4_modified','knowledge_merges','candidate_relations'},
      'PRIOR_PREVIEW_FIELDS')
    fail(prior_review['schema']=='V116_P1_READONLY_TOPIC_RELATION_PREVIEW_V1' and
         prior_review['source_video_id']==challenge_doc['video_id'] and
         prior_review['master116_git_blob_sha1']==LEGACY_MASTER_BLOB and
         prior_review['p4_22_git_blob_sha1']==P4_EDU22_BLOB,
         'PRIOR_SOURCE_BLOB_PIN_MISMATCH')
    fail(prior_review['historical_v75_identity_recovered'] is False and
         prior_review['full_history_dedup_completed'] is False and
         prior_review['master_or_p4_modified'] is False and
         prior_review['knowledge_merges']==0,'PRIOR_FALSE_RECONCILIATION_OR_APPROVAL')
    cases={c['case_id']:c for c in challenge_doc['cases']}
    relations=prior_review['candidate_relations'];fail(type(relations) is list and len(relations)<=120,
                                                     'PRIOR_RELATION_LIST')
    keys=set(); ns={}
    for row in relations:
        fail(type(row) is dict and set(row)=={
          'challenge_case_id','source_unit_id','prior_namespace','prior_id',
          'relation','reason_private','independently_verified_equivalence',
          'ready_for_merge'},'PRIOR_RELATION_SCHEMA')
        case=cases.get(row['challenge_case_id'])
        fail(case is not None and row['source_unit_id'] in case['baseline_unit_ids'],
             'PRIOR_RELATION_SOURCE_NOT_GROUNDED')
        fail(row['prior_namespace'] in ('MASTER116','P4_EDUCATION22') and
             type(row['prior_id']) is str and row['prior_id'] and
             row['relation'] in PREVIEW_STATUS and
             type(row['reason_private']) is str and len(row['reason_private'])>=16,
             'PRIOR_RELATION_INVALID')
        fail(row['prior_id'] in PINNED_PRIOR_IDS[row['prior_namespace']],
             'PRIOR_ID_NOT_IN_READONLY_ACTUAL_SUBSET')
        fail(row['independently_verified_equivalence'] is False and
             row['ready_for_merge'] is False,'PRIOR_UNEARNED_EQUALITY_OR_MERGE')
        key=(row['challenge_case_id'],row['source_unit_id'],row['prior_namespace'],row['prior_id'])
        fail(key not in keys,'PRIOR_RELATION_DUPLICATE')
        keys.add(key);ns[row['prior_namespace']]=ns.get(row['prior_namespace'],0)+1
    return {'schema':'V116_P1_RELATION_PREVIEW_SHA_ONLY_V1',
            'candidate_relations':len(relations),'namespace_counts':ns,
            'master116_and_p4_reused_read_only':True,
            'v75_full_404_identity_recovered':False,
            'historical_dedup_certified':False,'knowledge_merge_count':0,
            'independent_gold':False,'p0_go':False,
            'candidate_preview_digest_sha256':digest(prior_review),
            'code_audit_wall_ns':perf_counter_ns()-t0}


def measure_bounded_review_steps(*,srt_raw,base_ledger,base_docket,
                                 challenge_doc,official_record,prior_review,
                                 expected_srt_sha256,owner_zip_sha256):
    """Runs linked PRIVATE evidence checks, keeps model/web durations NULL.

    This DOES NOT operate the ChatGPT host or live external lookup. It records
    only the four explicitly executed local operations and their durations.
    """
    t0=perf_counter_ns()
    source=verify_original_challenges(srt_raw=srt_raw,base_ledger=base_ledger,
       base_docket=base_docket,challenges=challenge_doc,
       expected_srt_sha256=expected_srt_sha256,owner_zip_sha256=owner_zip_sha256)
    finance=audit_current_regulatory_evidence(challenge_doc=challenge_doc,
       official_record=official_record,baseline_finance_docket=base_docket)
    prior=audit_readonly_prior_preview(challenge_doc=challenge_doc,prior_review=prior_review)
    return {'schema':'V116_REAL_HOST_PREPARED_NO_MODEL_CALL_LOCAL_STAGE_TIME_V1',
            'source':source,'finance':finance,'prior':prior,
            'elapsed_local_checks_wall_ns':perf_counter_ns()-t0,
            'model_semantic_inference_wall_ns':None,
            'official_live_lookup_wall_ns':None,
            'audio_visual_open_resolution_wall_ns':None,
            'independent_gold_adjudication_wall_ns':None,
            'model_called_in_software':False,
            'all_atomic_claims_certified':False,'p0_go':False}


def guard_public_v116_receipt(receipt):
    """Prohibit inflating real private V116 audit counts or guessing model speed.

    Numeric timing is host-observed local code time only. Independent accuracy,
    live law body SHA, archived V75 IDs and knowledge approvals stay unavailable.
    """
    fail(type(receipt) is dict,'PUBLIC_RECEIPT_INVALID')
    pin={
      'schema':'V116_ACTUAL_OWNER_PRIVATE_152CUE_16_CHALLENGE_FIVE_STAGE_NO_GOLD_V1',
      'as_of':'2026-11-14','source_video_id':'7RRWNL0V6As',
      'original_archive_sha256':'00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd',
      'original_srt_sha256':'4515d3446c4874d3a376d86b1dd46ab89446e992911b0d42b52aa0df5ffb3c83',
      'baseline_cue_count':152,'baseline_cues_unaccounted':0,
      'challenge_cases':16,'supplemental_chat_provisional_facets':36,
      'challenged_unique_cue_positions':135,'cross_parent_challenge_cases':9,
      'high_critical_challenge_cases':11,'v115_original_finance_docket_rows':26,
      'challenge_cases_with_finance_status':16,'law_issuer_source_pointers':4,
      'law_2026_10_01_indexed_asof_2026_11_14':True,
      'law_2026_11_14_live_maintenance_page_observed':True,
      'law_raw_live_body_sha256':None,
      'domestic_equity_tr_exception_retained':True,
      'prior_readonly_topic_relations':11,'v75_404_parent_ids_recovered':False,
      'historical_full_overlap_certified':False,'knowledge_merges':0,
      'checkpoint_stages':5,'checkpoint_replay_new_events':0,
      'partial_run_recovery_new_events':3,'checkpoint_tampering_rejected':True,
      'model_calls_automated':False,'full_semantic_claim_recall_certified':False,
      'independent_gold':False,'precision':None,'recall':None,'high_risk_recall':None,
      'official_original_html_pinned':False,'new_financial_fact_approvals':0,
      'p0_go':False,
    }
    for key,value in pin.items():
        fail(key in receipt and type(receipt[key]) is type(value) and
             receipt[key]==value,'PUBLIC_RECEIPT_DRIFT_'+key.upper())
    digests=('owner_private_challenge_digest_sha256',
             'owner_private_regulatory_pointer_digest_sha256',
             'owner_private_prior_docket_digest_sha256',
             'checkpoint_final_head_sha256')
    for key in digests:
        fail(type(receipt.get(key)) is str and HEX.fullmatch(receipt[key]),
             'PUBLIC_PRIVATE_DIGEST_REQUIRED_'+key.upper())
    times=receipt.get('measured_local_stage_wall_ns')
    expected_code=('source_original_replay_and_semantic_challenge_audit_ns',
       'official_pointer_scope_audit_ns','historical_readonly_candidate_audit_ns',
       'full_local_validation_ns')
    expected_null=('chat_model_semantic_inference_ns','law_site_live_fetch_ns',
       'original_audio_video_resolution_ns','independent_gold_decision_ns')
    fail(type(times) is dict and set(times)==set(expected_code)|set(expected_null),
         'PUBLIC_TIMING_FIELDS')
    for key in expected_code:
        fail(type(times[key]) is int and times[key]>0,'PUBLIC_CODE_TIMING_INVALID')
    for key in expected_null:
        fail(times[key] is None,'PUBLIC_UNMEASURED_AS_MEASURED')
    return {'real_source_challenge_receipt_consistent':True,
            'model_semantic_inference_measured':False,
            'gold_precision_recall_measured':False,'p0_go':False}
