"""V34: check complete source-first ChatGPT risk triage and two OPEN financial claims.

Non-API host workflow: ChatGPT reads private original cues and external/current
primary pages; the engine verifies cited case/cue/atom/master identity.  Distinct
from full source claim recall, blind semantic gold and personal advice approval.
"""
from __future__ import annotations

from datetime import date
from urllib.parse import urlsplit

from .codec import json_digest, sha256
from .errors import InvalidInput
from .semantic_risk import audit_semantic_risks
from .atomic_exchange import audit_host_atomic_exchange
from .chat_review_custody_v33 import audit_source_bound_chat_reviews_v33

_RISK_CLASSES = frozenset({
    'CROSS_CUE_DISCOURSE_ONLY',
    'QUOTED_QUESTION_OR_SPEAKER_OPEN',
    'ASR_OR_SPEAKER_UNCERTAINTY_OPEN',
    'FINANCIAL_TAX_OR_LEGAL_SCOPE_OPEN',
    'INVESTMENT_CONDITION_OR_FORECAST_OPEN',
    'INVESTMENT_EDUCATION_OVERGENERALIZATION_OPEN',
})
_CLOSED_CLASS = 'CROSS_CUE_DISCOURSE_ONLY'
_DECISIONS = {
    'V3-IRP_ONE_MAN_WITHDRAWAL_START': 'PROVIDER_AND_CONTRIBUTION_TYPE_CONDITIONAL',
    'V5-EMPLOYER_SUPPLIER_STOCK_ADVOCACY': 'PUBLIC_INFORMATION_AND_DIVERSIFICATION_BOUNDARY',
}
_ALLOWED_PRIMARY = frozenset({'law.go.kr', 'www.law.go.kr',
    'consumer.kiwoom.com','file.shinhansec.com','file.truefriend.com',
    'moel.go.kr','www.moel.go.kr','www.investor.gov'})


def audit_40_original_contrast_docket_v34(sources, exchanges, review_rows, *, as_of):
    """Complete inventory of V33 *lexical* alerts with exact original cue hashes.

    Classifying an alert as cross-cue discourse closes only that heuristic
    triage item. It does not bless the historical investment proposition.
    """
    try: date.fromisoformat(as_of)
    except (TypeError, ValueError) as exc:
        raise InvalidInput('V34_REVIEW_DATE_INVALID') from exc
    if not isinstance(sources, dict) or not isinstance(exchanges, dict) or set(sources)!=set(exchanges):
        raise InvalidInput('V34_SOURCE_CANDIDATE_MAP_INVALID')
    if not isinstance(review_rows, list):
        raise InvalidInput('V34_REVIEW_ROWS_NOT_A_LIST')
    cases={}; risks_by_video={}
    for video_id,src in sources.items():
        audit_host_atomic_exchange(src,exchanges[video_id])
        alert=audit_semantic_risks(src,exchanges[video_id])
        risks_by_video[video_id]=alert
        for risk in alert['review_cases']:
            key=(video_id,risk['case_sha256'])
            if risk['reason']!='NEARBY_CORRECTION_NOT_IN_CONTEXT':
                raise InvalidInput('V34_UNEXPECTED_RISK_CATEGORY')
            cases[key]=risk
    if len(cases)!=40 or len(review_rows)!=len(cases):
        raise InvalidInput('V34_ORIGINAL_40_CASE_CENSUS_REQUIRED')
    seen=set();compact=[];total_open=0;closed=0
    for row in review_rows:
        required={'video_id','case_sha256','case_cue_index','case_cue_sha256',
                  'draft_claim_id','draft_claim_frame_sha256',
                  'contrast_carrier_claim_id','carrier_claim_frame_sha256',
                  'context_cue_indices','context_cue_sha256',
                  'classification','chat_reason','reviewer','as_of'}
        if type(row) is not dict or set(row)!=required:
            raise InvalidInput('V34_RISK_ROW_SCHEMA_INVALID')
        key=(row['video_id'],row['case_sha256'])
        if key not in cases or key in seen:
            raise InvalidInput('V34_RISK_CASE_MISSING_DUPLICATE_OR_FOREIGN')
        seen.add(key)
        risk=cases[key];src=sources[key[0]];ex=exchanges[key[0]]
        idx=risk['cue_index']
        context=list(range(max(1,idx-2),min(len(src.cues),idx+3)+1))
        if (type(row['case_cue_index']) is not int or row['case_cue_index']!=idx or
            row['case_cue_sha256']!=sha256(src.cues[idx-1].text.encode('utf8')) or
            row['draft_claim_id']!=risk['claim_id'] or
            row['context_cue_indices']!=context or
            row['context_cue_sha256']!=[sha256(src.cues[i-1].text.encode('utf8')) for i in context]):
            raise InvalidInput('V34_RISK_ORIGINAL_CUE_OR_CONTEXT_CHANGED')
        draft_atom=next((x for x in ex['atoms'] if x['claim_id']==risk['claim_id']),None)
        if draft_atom is None or row['draft_claim_frame_sha256']!=json_digest(draft_atom):
            raise InvalidInput('V34_RISK_DRAFT_ATOM_HASH_CHANGED')
        carrier=row['contrast_carrier_claim_id']
        atom=next((x for x in ex['atoms'] if x['claim_id']==carrier),None)
        if (atom is None or row['carrier_claim_frame_sha256']!=json_digest(atom) or
            carrier==risk['claim_id'] or not any(
            r['cue_index']==idx for r in atom['source_refs'])):
            raise InvalidInput('V34_RISK_CONTRAST_CARRIER_NOT_SOURCE_PINNED')
        if (row['classification'] not in _RISK_CLASSES or
            type(row['chat_reason']) is not str or not 30<=len(row['chat_reason'].strip())<=800 or
            row['reviewer']!='CHATGPT_CURRENT_TURN' or row['as_of']!=as_of):
            raise InvalidInput('V34_HOST_RISK_MEANING_REVIEW_INVALID')
        is_open=row['classification']!=_CLOSED_CLASS
        total_open+=int(is_open);closed+=int(not is_open)
        compact.append({'video_id':key[0], 'case_sha256':key[1],
                        'source_cue_sha256':row['case_cue_sha256'],
                        'draft_claim_id':risk['claim_id'],
                        'context_carrier':carrier,
                        'draft_claim_frame_sha256':json_digest(draft_atom),
                        'carrier_claim_frame_sha256':json_digest(atom),
                        'source_context_sha256':json_digest([{'cue_index':i,'sha256':s}
                             for i,s in zip(context,row['context_cue_sha256'])]),
                        'classification':row['classification'],
                        'reason_sha256':sha256(row['chat_reason'].encode('utf8')),
                        'financial_meaning_truth_approved':False})
    if seen!=set(cases):
        raise InvalidInput('V34_ORIGINAL_ALERT_UNREVIEWED')
    compact.sort(key=lambda r:(r['video_id'],r['case_sha256']))
    out={'schema':'IRE_V6_V34_ORIGINAL_40_SOURCE_FIRST_CHAT_RISK_TRIAGE',
         'original_alerts':len(cases),'reviewed_alerts':len(compact),
         'discourse_only_heuristic_alerts':closed,
         'financial_or_asr_semantic_review_still_open':total_open,
         'original_risk_docket_digest':json_digest({k:risks_by_video[k]['case_census_sha256'] for k in sorted(risks_by_video)}),
         'source_first_review_sha256':json_digest(compact),
         'review_rows':compact,'original_raw_heuristic_flags_kept':True,
         'all_1603_utterances_atomically_split':False,
         'full_video_semantic_accuracy_certified':False,
         'independent_gold_available':False,'knowledge_merge_approved':False,
         'personal_tax_or_order_approved':False,'p0_go':False}
    out['receipt_sha256']=json_digest(out)
    return out


def audit_two_open_original_claim_reassessments_v34(sources,exchanges,original_reviews,master116,
                                                    reassessments,*,as_of):
    """Append-only conditional reclassification of V33's two old OPEN rows.

    Enforces original review hashes, real master116 identity and authenticated
    original cue identity; the provider's current contractual policy itself is
    **not** automatically authenticated by this engine.
    """
    original=audit_source_bound_chat_reviews_v33(
        sources,exchanges,original_reviews,master116,current_as_of=as_of)
    previous={r['review_id']:r for r in original_reviews}
    if original['host_open_items']!=2 or type(reassessments) is not list or len(reassessments)!=2:
        raise InvalidInput('V34_TWO_ORIGINAL_OPEN_CLAIMS_REQUIRED')
    seen=set();outrows=[]
    for row in reassessments:
        required={'review_id','video_id','original_v33_review_sha256','source_cue_sha256',
                  'decision','new_meaning','source_scope_reason','prior_master_claim_id',
                  'prior_master_row_sha256','official_evidence',
                  'current_account_or_individual_applicability_verified',
                  'investment_recommendation_approved','reviewer','as_of'}
        if type(row) is not dict or set(row)!=required:
            raise InvalidInput('V34_OPEN_CLAIM_REASSESSMENT_SCHEMA_INVALID')
        rid=row['review_id']
        if rid not in _DECISIONS or rid in seen or row['decision']!=_DECISIONS[rid]:
            raise InvalidInput('V34_OPEN_REASSESSMENT_ID_OR_CLASS_INVALID')
        seen.add(rid)
        orig=previous.get(rid)
        if orig is None or row['video_id']!=orig['video_id'] or row['original_v33_review_sha256']!=json_digest(orig):
            raise InvalidInput('V34_ORIGINAL_OPEN_REVIEW_HASH_DRIFT')
        src=sources[orig['video_id']]
        expected=[sha256(src.cues[i-1].text.encode('utf8')) for i in orig['source_cue_indices']]
        if row['source_cue_sha256']!=expected:
            raise InvalidInput('V34_REASSESSED_ORIGINAL_SRT_MISMATCH')
        master=orig['knowledge_relation']['master_claim_id']
        match=next((x for x in master116 if x['claim_id']==master),None)
        if (not match or row['prior_master_claim_id']!=master or
            row['prior_master_row_sha256']!=json_digest(match)):
            raise InvalidInput('V34_MASTER116_TARGET_REWRITE_OR_FORGERY')
        if (type(row['new_meaning']) is not str or len(row['new_meaning'].strip())<80 or
            type(row['source_scope_reason']) is not str or len(row['source_scope_reason'].strip())<75 or
            row['current_account_or_individual_applicability_verified'] is not False or
            row['investment_recommendation_approved'] is not False or
            row['reviewer']!='CHATGPT_CURRENT_TURN' or row['as_of']!=as_of):
            raise InvalidInput('V34_CONDITIONAL_EDUCATIONAL_CLAIM_NOT_SUPPORTED')
        evidence=row['official_evidence']
        if type(evidence) is not list or len(evidence)<2:
            raise InvalidInput('V34_MULTIPLE_INDEPENDENT_SCOPE_SOURCES_REQUIRED')
        verified=[]
        for e in evidence:
            if type(e) is not dict or set(e)!={'url','source_type','published_or_effective_date',
                     'retrieved_on','scope_note','issuer_body_verified'}:
                raise InvalidInput('V34_EVIDENCE_ROW_SCHEMA_INVALID')
            try:
                u=urlsplit(e['url']);effective=date.fromisoformat(e['published_or_effective_date'])
                found=date.fromisoformat(e['retrieved_on'])
                on=date.fromisoformat(as_of)
            except (ValueError,TypeError) as exc:
                raise InvalidInput('V34_EVIDENCE_DATE_OR_URL_INVALID') from exc
            if (u.scheme!='https' or u.hostname not in _ALLOWED_PRIMARY or not u.path or
                effective>on or found>on or
                e['source_type'] not in ('STATUTE_CURRENT','FINANCIAL_INSTITUTION_POLICY','HISTORICAL_FINANCIAL_INSTITUTION_PDF','REGULATOR_FINANCIAL_EDUCATION') or
                type(e['scope_note']) is not str or len(e['scope_note'].strip())<45 or
                e['issuer_body_verified'] is not False):
                raise InvalidInput('V34_EVIDENCE_NOT_AUTHENTICATED_OR_DATE_WRONG')
            verified.append({'url_sha256':sha256(e['url'].encode()),
                'source_type':e['source_type'],
                'effective_or_publication_date':effective.isoformat(),
                'retrieved_on':found.isoformat(),
                'scope_sha256':sha256(e['scope_note'].encode()),
                'original_signed_issuer_full_body_authenticated':False})
        if rid=='V3-IRP_ONE_MAN_WITHDRAWAL_START':
            types={e['source_type'] for e in evidence}
            if not {'FINANCIAL_INSTITUTION_POLICY','HISTORICAL_FINANCIAL_INSTITUTION_PDF'}<=types:
                raise InvalidInput('V34_PROVIDER_CONTRAST_MISSING_HISTORICAL_LIMITATION')
        elif rid=='V5-EMPLOYER_SUPPLIER_STOCK_ADVOCACY':
            if 'STATUTE_CURRENT' not in {e['source_type'] for e in evidence}:
                raise InvalidInput('V34_EMPLOYER_SECURITY_LAW_MISSING')
        outrows.append({'review_id':rid,'source_original_sha256':src.source_sha256,
            'original_review_sha256':json_digest(orig),
            'reassessed_meaning_sha256':sha256(row['new_meaning'].encode()),
            'reassessed_rationale_sha256':sha256(row['source_scope_reason'].encode()),
            'prior_master_claim_id':master,
            'prior_master_sha256':json_digest(match),
            'decision':row['decision'],
            'supporting_evidence':verified,
            'case_scope_reviewed_conditional_education_only':True,
            'actual_account_financial_provider_policy_current_verified':False,
            'company_specific_MNPI_status_verified':False,
            'historical_claim_reuse_as_unconditional_fact':False,
            'existing_knowledge_auto_merge':False})
    if seen!=set(_DECISIONS):
        raise InvalidInput('V34_TWO_ORIGINAL_OPEN_UNACCOUNTED')
    outrows.sort(key=lambda x:x['review_id'])
    result={'schema':'IRE_V6_V34_TWO_OPEN_HISTORICAL_CLAIMS_CHAT_CONDITIONAL_REASSESSMENT',
      'prior_v33_host_review_sha256':original['receipt_sha256'],
      'original_open_claim_count':2,'conditional_scope_reclassified_count':2,
      'unverified_current_individual_or_provider_cases':2,
      'reassessments':outrows,'original_review_rows_immutable':True,
      'not_a_current_personal_investment_or_tax_advice':True,
      'not_independent_human_financial_gold':True,
      'all_1603_candidate_claims_semantically_reviewed':False,
      'master116_or_p4_auto_merge':False,'p0_go':False}
    result['receipt_sha256']=json_digest(result)
    return result


def audit_chat_firstpass_atomic_window_v34(full_source, full_draft_exchange,
                                            scoped_source, scoped_chat_exchange,
                                            source_to_draft_links):
    """Pin a ChatGPT-authored narrower first-pass claim frame to old ASR units.

    This is a *source-bound splitting progress receipt*, not a statement that
    clauses are truly atomic, legally right or independently reviewed.  Every
    old anchor in the selected scope must be represented in the new scope.
    """
    old=audit_host_atomic_exchange(full_source,full_draft_exchange)
    new=audit_host_atomic_exchange(scoped_source,scoped_chat_exchange)
    if (full_source.source_sha256!=scoped_source.source_sha256 or
        full_source.video_id!=scoped_source.video_id or
        scoped_source.scope_first_cue<1 or
        scoped_source.scope_last_cue>len(full_source.cues) or
        scoped_source.scope_last_cue-scoped_source.scope_first_cue+1>100):
        raise InvalidInput('V34_CHAT_ATOMIC_SCOPED_SOURCE_NOT_VALID')
    first,last=scoped_source.scope_first_cue,scoped_source.scope_last_cue
    old_cues={d['cue_index'] for d in full_draft_exchange['cue_dispositions']
              if first<=d['cue_index']<=last and d['claim_ids']}
    new_cues={d['cue_index'] for d in scoped_chat_exchange['cue_dispositions']
              if d['claim_ids']}
    unquotable=old_cues-new_cues
    # V6 source refs require a >=2-character original quote.  A one-character
    # ASR fragment must be preserved as an explicitly disclosed source-context
    # cue; it cannot be forged into a two-character quote.
    for i in unquotable:
        if (len(scoped_source.cues[i-1].text.strip())>=2 or
            not any(i in a['context_cue_indices'] for a in scoped_chat_exchange['atoms'])):
            raise InvalidInput('V34_SPLIT_OLD_CUE_ANCHORS_NOT_PRESERVED')
    unquoted=set(range(first,last+1))-new_cues
    for i in unquoted:
        if (len(scoped_source.cues[i-1].text.strip())>=2 or
            not any(i in a['context_cue_indices'] for a in scoped_chat_exchange['atoms'])):
            raise InvalidInput('V34_SPLIT_UNQUOTED_ORIGINAL_CUE_NOT_ACCOUNTED')
    if new['unresolved_cues'] or new['suspicious_no_atom_cues']:
        raise InvalidInput('V34_SPLIT_OLD_CUE_ANCHORS_NOT_PRESERVED')
    old_cover={d['cue_index']:set(d['claim_ids']) for d in
               full_draft_exchange['cue_dispositions'] if first<=d['cue_index']<=last}
    new_atoms={a['claim_id']:a for a in scoped_chat_exchange['atoms']}
    if (type(source_to_draft_links) is not list or
        len(source_to_draft_links)!=len(new_atoms)):
        raise InvalidInput('V34_SPLIT_ALL_NEW_ROWS_REVIEW_REQUIRED')
    seen=set();lines=[];old_ids=set(a['claim_id'] for a in full_draft_exchange['atoms'])
    for row in source_to_draft_links:
        if type(row) is not dict or set(row)!={'claim_id','old_provisional_ids',
                        'new_claim_frame_sha256','chat_scope_note','reviewer'}:
            raise InvalidInput('V34_SPLIT_MAPPING_SCHEMA_INVALID')
        cid=row['claim_id'];atom=new_atoms.get(cid)
        if cid in seen or atom is None or cid in old_ids:
            raise InvalidInput('V34_SPLIT_CHILD_ID_NOT_NEW_UNIQUE')
        seen.add(cid)
        old_candidates=sorted(set().union(*(old_cover[r['cue_index']]
                                           for r in atom['source_refs'])))
        if (row['old_provisional_ids']!=old_candidates or
            row['new_claim_frame_sha256']!=json_digest(atom) or
            row['reviewer']!='CHATGPT_CURRENT_TURN' or
            type(row['chat_scope_note']) is not str or
            not 30<=len(row['chat_scope_note'].strip())<=350):
            raise InvalidInput('V34_SPLIT_SOURCE_PROVISIONAL_PARENT_DRIFT')
        lines.append({'new_claim_id':cid,
                      'new_atom_sha256':json_digest(atom),
                      'original_cue_anchor_indices':[x['cue_index'] for x in atom['source_refs']],
                      'old_provisional_ids':old_candidates,
                      'host_context_reason_sha256':sha256(row['chat_scope_note'].encode()),
                      'independent_atomic_meaning_proven':False})
    if seen!=set(new_atoms):
        raise InvalidInput('V34_SPLIT_CHAT_REVIEW_INCOMPLETE')
    from .atomic_exchange import NUMBER
    missing_numeric=[];total_numeric=0
    for i in range(first,last+1):
        for token in NUMBER.findall(scoped_source.cues[i-1].text):
            total_numeric+=1
            if not any(x['cue_index']==i and x['token']==token
                       for a in scoped_chat_exchange['atoms'] for x in a['numeric_references']):
                missing_numeric.append(i)
    if missing_numeric:
        raise InvalidInput('V34_SPLIT_ORIGINAL_NUMERIC_SCOPE_NOT_LINKED')
    lines.sort(key=lambda r:r['new_claim_id'])
    result={'schema':'IRE_V6_V34_REAL_ORIGINAL_HOST_FIRSTPASS_SPLIT_HASH_ONLY',
      'video_id':full_source.video_id,'original_source_sha256':full_source.source_sha256,
      'source_cue_first':first,'source_cue_last':last,
      'source_cue_count':last-first+1,
      'former_v33_utterance_count':len({x for i in old_cues for x in old_cover[i]}),
      'new_host_firstpass_candidate_count':len(new_atoms),
      'source_cues_with_v33_anchors_preserved':len(old_cues),
      'new_source_cues_with_host_frames':len(new_cues),
      'unquotable_single_character_original_cues_in_context':len(unquotable),
      'other_single_character_original_cues_context_only':len(unquoted),
      'source_literal_numeric_occurrences':total_numeric,
      'numeric_occurrences_structurally_cited':total_numeric,
      'old_draft_digest':old['atom_candidate_digest'],
      'new_host_frame_digest':new['atom_candidate_digest'],
      'new_host_claims':lines,
      'host_did_not_independently_verify_atomic_exhaustiveness':True,
      'independent_semantic_gold_available':False,
      'historical_financial_claims_verified_as_current':False,
      'original_full_video_research_completed':False,
      'master116_knowledge_merged':False,'p0_go':False}
    result['receipt_sha256']=json_digest(result)
    return result
