"""V35 source-first scoped split/audit for previously open V34 finance-risk alerts.

No semantic gold: the ChatGPT host judges original speech.  The V6 engine only
attests exact source/cue/atom/master hash identities and fail-closed status
accounting. Private reviewer reasons and raw excerpts never enter public receipts.
"""
from __future__ import annotations

import re
from datetime import date
from .atomic_exchange import audit_host_atomic_exchange, NUMBER
from .codec import json_digest, sha256
from .errors import InvalidInput
from .chat_risk_reassessment_v34 import audit_40_original_contrast_docket_v34

RESOLVED = 'CHAT_SOURCE_MEANING_RESOLVED_EDUCATION_ONLY'
OPEN = 'ORIGINAL_ASR_OR_FINANCIAL_SCOPE_STILL_OPEN'
_RELATIONS={'SUPPORTS_PRIOR_CHAT_ONLY','REFINES_PRIOR_CHAT_ONLY',
            'CONFLICTS_PRIOR_CHAT_ONLY','POTENTIAL_PRIOR_LINK_OPEN'}


def audit_source_first_remaining_37_v35(sources, baseline_exchanges, v34_rows,
                                        scoped_replays, host_case_reviews,
                                        master116, *, as_of, expected_master116_rows_digest):
    """Audit *all* 37 V34 pending alerts against freshly replayed original cues.

    Scoped replays: each (source,exchange) represents a complete V6 source-plan
    scope around one distinct hinge; surrounding cues remain UNRESOLVED. Review
    reason and proposition text stay private. No atom count equals gold recall.
    """
    try: date.fromisoformat(as_of)
    except (ValueError, TypeError) as e: raise InvalidInput('V35_ASOF_INVALID') from e
    baseline=audit_40_original_contrast_docket_v34(sources,baseline_exchanges,
                                                   v34_rows,as_of=as_of)
    pending={(r['video_id'],r['case_sha256']):r for r in v34_rows if
             r['classification']!='CROSS_CUE_DISCOURSE_ONLY'}
    if (len(pending)!=baseline['financial_or_asr_semantic_review_still_open'] or
        len(pending)!=37 or not isinstance(master116,list) or len(master116)!=116):
        raise InvalidInput('V35_EXACT_PRIOR_COHORT_OR_MASTER_REQUIRED')
    if (type(expected_master116_rows_digest) is not str or
        not re.fullmatch(r'[0-9a-f]{64}',expected_master116_rows_digest) or
        json_digest(master116)!=expected_master116_rows_digest):
        raise InvalidInput('V35_MASTER116_ROWS_PIN_MISMATCH')
    by_master={m['claim_id']:m for m in master116}
    if len(by_master)!=116:
        raise InvalidInput('V35_MASTER_IDS_DUPLICATED')
    if type(scoped_replays) is not list or type(host_case_reviews) is not list:
        raise InvalidInput('V35_REPLAY_OR_REVIEW_SCHEMA_INVALID')
    clusters={}; all_cases=set(); child_ids_seen=set(); child_count=0; numeric_count=0
    for bundle in scoped_replays:
        if type(bundle) is not dict or set(bundle)!= {'video_id','hinge_cue','source','exchange','case_sha256_list'}:
            raise InvalidInput('V35_REPLAY_BUNDLE_SCHEMA_INVALID')
        vid=bundle['video_id']; idx=bundle['hinge_cue']; scoped=bundle['source']
        k=(vid,idx)
        if (vid not in sources or k in clusters or type(idx) is not int or
            type(bundle['case_sha256_list']) is not list or not bundle['case_sha256_list']):
            raise InvalidInput('V35_HINGE_VIDEO_OR_GROUP_DUPLICATE')
        full=sources[vid]
        if (scoped.video_id!=vid or scoped.source_sha256!=full.source_sha256 or
            scoped.cue_census_sha256!=full.cue_census_sha256 or
            not (scoped.scope_first_cue<=idx<=scoped.scope_last_cue) or
            scoped.scope_last_cue-scoped.scope_first_cue+1>120):
            raise InvalidInput('V35_SCOPE_OR_ORIGINAL_SOURCE_MISMATCH')
        wanted={(v,h) for h in bundle['case_sha256_list'] for v in [vid]}
        actual={(v,h) for (v,h),r in pending.items() if r['case_cue_index']==idx and v==vid}
        if wanted!=actual or wanted.intersection(all_cases):
            raise InvalidInput('V35_RISK_TO_HINGE_LINEAGE_LOST')
        all_cases.update(wanted)
        audit=audit_host_atomic_exchange(scoped,bundle['exchange'])
        atoms=bundle['exchange']['atoms']
        if not 2<=len(atoms)<=6 or audit['proposed_atomic_claims']!=len(atoms) or any(
                a['stance']!='UNRESOLVED' or a['as_of'] is not None for a in atoms):
            raise InvalidInput('V35_UNCERTIFIED_PROPOSAL_MUST_REMAIN_UNRESOLVED')
        child_ids={a['claim_id'] for a in atoms}
        if child_ids_seen.intersection(child_ids):
            raise InvalidInput('V35_DUPLICATE_CHILD_ID_ACROSS_SCOPED_REPLAYS')
        child_ids_seen.update(child_ids)
        if not any(idx in [r['cue_index'] for r in a['source_refs']] for a in atoms):
            raise InvalidInput('V35_HINGE_QUOTE_ANCHOR_MISSING')
        # A bounded chunk still contains unresolved source material.  It must
        # NEVER silently become a fully verified original-video study.
        if audit['unresolved_cues']<1:
            raise InvalidInput('V35_SCOPED_MATERIAL_FALSLY_COMPLETE')
        # Only numeric tokens occurring on the reviewed child-frame refs are
        # required to remain anchored; surrounding unrelated cues are open.
        cited={r['cue_index'] for a in atoms for r in a['source_refs']}
        for n in cited:
            for token in NUMBER.findall(scoped.cues[n-1].text):
                if not any(i['cue_index']==n and i['token']==token
                           for a in atoms for i in a['numeric_references']):
                    raise InvalidInput('V35_REVIEWED_CUE_NUMERIC_TOKEN_DROPPED')
                numeric_count+=1
        clusters[k]={
            'video_id':vid,'hinge_cue_index':idx,
            'source_sha256':full.source_sha256,
            'scope_first':scoped.scope_first_cue,'scope_last':scoped.scope_last_cue,
            'manifest_sha256':scoped.manifest_sha256,
            'child_count':len(atoms),
            'candidate_sha256':audit['atom_candidate_digest'],
            'source_cues_left_unresolved':audit['unresolved_cues'],
            'child_claims':[{
                'claim_id':a['claim_id'],
                'claim_sha256':json_digest(a),
                'role':a['kind'],
                'cue_indices':[r['cue_index'] for r in a['source_refs']],
                'cue_sha256':[sha256(scoped.cues[r['cue_index']-1].text.encode())
                              for r in a['source_refs']],
                'financial_fact_approved':False} for a in atoms],
            'case_keys':wanted,
        }
        child_count+=len(atoms)
    if all_cases!=set(pending):
        raise InvalidInput('V35_ORIGINAL_OPEN_ALERT_MISSING')
    if len(host_case_reviews)!=len(pending):
        raise InvalidInput('V35_ALL37_CHAT_DECISIONS_REQUIRED')
    seen=set(); public=[]; n_resolved=0; n_open=0; n_prior_open=0
    required={'video_id','case_sha256','hinge_cue_index','scoped_candidate_sha256',
              'original_draft_atom_sha256','source_meaning_status',
              'bounded_semantic_explanation','remaining_limit','master_claim_id',
              'master_row_sha256','prior_knowledge_relation','official_evidence',
              'reviewer','as_of'}
    for review in host_case_reviews:
        if type(review) is not dict or set(review)!=required:
            raise InvalidInput('V35_CHAT_CASE_SCHEMA_INVALID')
        key=(review['video_id'],review['case_sha256'])
        if key not in pending or key in seen:
            raise InvalidInput('V35_CHAT_CASE_MISSING_OR_DUPLICATE')
        seen.add(key); old=pending[key];g=clusters.get((key[0],review['hinge_cue_index']))
        if (g is None or key not in g['case_keys'] or
            review['original_draft_atom_sha256']!=old['draft_claim_frame_sha256'] or
            review['scoped_candidate_sha256']!=g['candidate_sha256']):
            raise InvalidInput('V35_CHAT_CASE_OR_CHILD_LINEAGE_DRIFT')
        state=review['source_meaning_status']
        if (state not in (RESOLVED,OPEN) or
            type(review['bounded_semantic_explanation']) is not str or
            len(review['bounded_semantic_explanation'].strip())<50 or
            type(review['remaining_limit']) is not str or
            len(review['remaining_limit'].strip())<30 or
            review['reviewer']!='CHATGPT_CURRENT_TURN' or review['as_of']!=as_of):
            raise InvalidInput('V35_CHAT_MEANING_OR_STATUS_INVALID')
        m=by_master.get(review['master_claim_id'])
        if (not m or review['master_row_sha256']!=json_digest(m) or
            review['prior_knowledge_relation'] not in _RELATIONS):
            raise InvalidInput('V35_PRIOR116_RELATION_NOT_SOURCE_BOUND')
        evidence=review['official_evidence']
        if type(evidence) is not list or len(evidence)>4:
            raise InvalidInput('V35_PRIMARY_EVIDENCE_SCHEMA_INVALID')
        for e in evidence:
            if (type(e) is not dict or set(e)!={'url','retrieved_on','scope','independent_issuer_body_verified'} or
                type(e['url']) is not str or not e['url'].startswith('https://') or
                type(e['scope']) is not str or len(e['scope'])<25 or
                e['retrieved_on']!=as_of or e['independent_issuer_body_verified'] is not False):
                raise InvalidInput('V35_PRIMARY_EVIDENCE_SCOPE_OR_PROVENANCE_INVALID')
            # URL alone is NOT independently authenticated publisher body.
        if (old['classification']=='FINANCIAL_TAX_OR_LEGAL_SCOPE_OPEN' and state==RESOLVED
                and not evidence and any(a['role'] not in ('OPINION','QUESTION') for a in g['child_claims'])):
            raise InvalidInput('V35_LEGAL_CURRENT_SCOPE_WITHOUT_PRIMARY_EVIDENCE')
        if old['classification']=='ASR_OR_SPEAKER_UNCERTAINTY_OPEN' and state==RESOLVED:
            raise InvalidInput('V35_UNVERIFIED_ASR_MUST_REMAIN_OPEN')
        n_resolved+=state==RESOLVED;n_open+=state==OPEN
        n_prior_open+=state==RESOLVED and review['prior_knowledge_relation']=='POTENTIAL_PRIOR_LINK_OPEN'
        public.append({
            'video_id':key[0], 'original_case_sha256':key[1],
            'source_hinge_cue_index':old['case_cue_index'],
            'child_candidate_digest':g['candidate_sha256'],
            'child_count':g['child_count'],
            'old_claim_frame_sha256':old['draft_claim_frame_sha256'],
            'status':state,
            'source_context_meaning_review_sha256':sha256(review['bounded_semantic_explanation'].encode()),
            'remaining_limit_sha256':sha256(review['remaining_limit'].encode()),
            'master_claim_id':review['master_claim_id'],
            'master_row_sha256':review['master_row_sha256'],
            'prior_relation':review['prior_knowledge_relation'],
            'combined_source_and_prior_review_status':(
                'ORIGINAL_ASR_OR_FINANCIAL_SCOPE_STILL_OPEN' if state==OPEN else
                'PRIOR_RELATION_REVIEW_REQUIRED' if review['prior_knowledge_relation']=='POTENTIAL_PRIOR_LINK_OPEN'
                else 'CHAT_FIRSTPASS_EDUCATIONAL_CONTEXT_REVIEWED_NOT_GOLD'),
            'official_evidence':[
                {'url':x['url'],'scope_sha256':sha256(x['scope'].encode()),
                 'issuer_body_independently_verified':False} for x in evidence],
            'financial_fact_truth_certified':False,
            'personal_tax_or_trade_approved':False,
        })
    if seen!=set(pending) or n_resolved+n_open!=37:
        raise InvalidInput('V35_COHORT_CONSERVATION_FAILED')
    public.sort(key=lambda x:(x['video_id'],x['source_hinge_cue_index'],x['original_case_sha256']))
    pub_clusters=[]
    for k,g in sorted(clusters.items()):
        pub_clusters.append({field:value for field,value in g.items() if field!='case_keys'})
    out={
        'schema':'IRE_V6_V35_37_REAL_ORIGINAL_SOURCE_SPLIT_FINANCE_EVIDENCE_AND_PRIOR116_CUSTODY',
        'as_of':as_of,'v34_original_open_cases':37,
        'reviewed_source_case_count':len(public),
        'unique_source_hinge_count':len(clusters),
        'new_provisional_child_claim_frames':child_count,
        'reviewed_cited_numeric_occurrences':numeric_count,
        'chat_source_meaning_resolved_education_only':n_resolved,
        'risk_cases_retained_open_after_chat_review':n_open,
        'additional_prior_relation_pending_among_source_resolved':n_prior_open,
        'still_open_including_prior_relation':n_open+n_prior_open,
        'source_meaning_and_prior_relation_chat_reviewed':n_resolved-n_prior_open,
        'original_v34_risk_receipt_sha256':baseline['receipt_sha256'],
        'master116_count':len(by_master),
        'master116_rows_digest':expected_master116_rows_digest,
        'source_split_clusters':pub_clusters,'per_alert_reviews':public,
        'original_private_text_published':False,
        'full_source_1603_candidate_atomization_complete':False,
        'all_130_original_windows_semantically_complete':False,
        'independent_gold_precision_recall_measured':False,
        'official_issuer_document_body_independently_authenticated':False,
        'master116_auto_merge_approved':False,
        'personal_tax_or_trade_approved':False,
        'p0_go':False,
    }
    out['receipt_sha256']=json_digest(out)
    return out
