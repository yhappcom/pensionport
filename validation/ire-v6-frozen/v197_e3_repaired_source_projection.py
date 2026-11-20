"""V197 read-only, fail-closed E3 view over frozen V194/V195 and V196 repair proposals.

This is a NON-APPROVED source-custody projection. It does NOT rewrite the previous
ChatGPT turn or turn proposed amendments into accepted finance knowledge. Exactly
all original 120 candidates and every high-risk flag remain visible to E3 reviewers.
Private user SRT, judgment texts, and the materialized JSON must never be in Git.
"""
from __future__ import annotations
import json,os,stat
from pathlib import Path
from collections import Counter
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v196_e3_second_review_repair import E3SecondReviewRepairOverlay,_sha,_canonical

VIEW_SCHEMA='IRE_V197_E3_SOURCE_REPAIR_PROPOSALS_UNAPPROVED_VIEW_V1'
RISK_SCHEMA='IRE_V197_CMA_ALL_HIGH_RISK_UNRESOLVED_REGISTER_V1'
CUSTODY_SCHEMA='IRE_V197_PRIVATE_MATERIALIZED_E3_VIEW_SEALED_V1'
RISK_REF_URL='https://law.kofia.or.kr/service/law/lawFullScreenContent.do?historySeq=1379&seq=285'
FLAGS=('independent_gold','finance_fact_approved','e3_approved','e4_approved','e5_published')
RISK_FAMILIES={
 'EXAGGERATED_SAFETY_OR_IGNORED_LOSS_RISK':'INVESTMENT_LOSS_OR_CREDIT_RISK',
 'UNIVERSAL_RATE_OR_SWITCH_ADVICE_UNSUPPORTED':'RATE_COMPARISON_OR_UNASSESSED_SWITCH',
 'HISTORICAL_DATE_OR_UNREAD_SCREEN_DATA':'HISTORICAL_SCREEN_DATA',
 'PRODUCT_TERMS_OR_PROVIDER_SCOPE_NOT_VERIFIED':'PRODUCT_PROVIDER_TERMS',
 'ILLUSTRATIVE_NOT_CURRENT_RETURN':'ILLUSTRATIVE_RETURN_NOT_CURRENT',
 'INVESTOR_APPLICABILITY_UNASSESSED':'PERSONAL_APPLICABILITY',
 'SOURCE_QUOTE_ONLY_NOT_FACT_CERTIFIED':'SOURCE_SPOKEN_NOT_CURRENT_FACT',
}

def _require(ok,code):
    if not ok:raise InvalidInput('V197_E3_'+code)

def _safe_source_quote(src,atom):
    # Original quote may straddle captions. The exact original *full* cue is
    # rederived here; never make provenance from a summarized proposition.
    i=atom['cue_index']
    _require(type(i)==int and i in src and type(src[i])==str and src[i].strip(),
             'MISSING_ORIGINAL_SOURCE_CUE')
    return src[i]

def _read_pinned(review,repair,expected_head):
    _require(isinstance(repair,E3SecondReviewRepairOverlay) and
             repair.reviewer is review,'REPAIR_REVIEWER_NOT_SAME_OBJECT')
    repair._original_pinned()
    a=review.status();b=repair.status()
    _require(a['source_sha256']==b['source_sha256'] and
             a['first_turn_frozen_owner_head_sha256']==b['first_turn_owner_head_sha256'] and
             a['review_head_sha256']==b['v195_second_review_head_sha256'] and
             b['repair_overlay_head_sha256']==expected_head,
             'STALE_SOURCE_OR_REVIEW_OR_REPAIR_HEAD')
    _require(a['second_turn_claims_reviewed']==120 and
             a['source_cue_count']==336 and len(review.atoms)==120 and
             len(review.cues)==336 and a['unreviewed_claims']==0 and
             b['proposed_corrections']==16 and
             b['original_quarantined_retained']==28 and
             b['original_open_cues_preserved']==14 and
             b['original_source_tasks_preserved']==34,
             'CURRENT_REAL_CMA_CENSUS_NOT_VERIFIED')
    _require(all(a.get(k) is False for k in ('independent_gold','e3_accuracy_certified',
             'v123_e4_authorized','e5_published','host_message_identity_verified')) and
             all(b.get(k) is False for k in ('independent_gold','accuracy_metrics_measured',
             'e3_approved','e4_approved','e5_published','host_user_turn_ids_verified')),
             'ILLEGAL_CLAIM_OF_QUALITY_OR_AUTHORITY')
    with review._db() as db: old_head,judgments,_=review._audit(db)
    with repair._db() as db: amend_head,amendments,_=repair._audit(db)
    _require(old_head==a['review_head_sha256'] and amend_head==expected_head and
             sorted(judgments)==list(range(1,121)) and len(amendments)==16,
             'AUDITED_LEDGER_VS_REPAIR_MISMATCH')
    return a,b,judgments,amendments

def make_risk_register(review,judgments):
    """Source-pinned OPEN risk tasks, including all 28 quarantines AND 56 other holds.

    The references are only official *web-text lookup candidates*. No original
    issuer bytes, product terms or effective law dates are certified here.
    """
    records=[]
    for serial in range(1,len(review.atoms)+1):
        atom=review.atoms[serial-1];old=judgments[serial]
        if not atom['high_risk']:continue
        _require(old['first_turn_high_risk_flag'] is True and
                 old['e3_disposition'].startswith(('QUARANTINE','HOLD')),
                 'HIGH_RISK_HAS_NO_BLOCKING_VERDICT')
        issue=old['financial_problem']
        _require(issue in RISK_FAMILIES,'UNKNOWN_RISK_FAMILY')
        rationale=old['source_specific_rationale']
        _require(type(rationale)==str and len(rationale)>=25,'MISSING_PRIOR_SOURCE_RATIONALE')
        cue=_safe_source_quote(review.cues,atom)
        records.append({
          'serial':serial,'claim_sha256':_sha(atom),
          'prior_judgment_sha256':_sha(old),'cue_index':atom['cue_index'],
          'source_text_sha256':sha256(cue.encode('utf-8')),
          'source_quote':cue,'old_disposition':old['e3_disposition'],
          'risk_family':RISK_FAMILIES[issue],
          'source_specific_issue_from_second_turn':rationale,
          'risk_status':'OPEN_UNVERIFIED_BLOCK_FINANCIAL_USE',
          'official_public_web_text_candidate_url':RISK_REF_URL,
          'official_document_raw_bytes_verified':False,
          'product_specific_terms_verified':False,
          'currently_applicable_fact_verified':False,
          'e3_approved':False,'e4_approved':False,'e5_published':False})
    return {'schema':RISK_SCHEMA,'video_id':review.study['video_id'],
        'source_sha256':review.config['source_sha256'],
        'original_study_sha256':review.config['frozen_first_study_sha256'],
        'prior_review_head_sha256':review.status()['review_head_sha256'],
        'candidate_issuer_web_lookup_only':True,'risk_records':records,
        'independent_gold':False,'e3_approved':False,'e4_approved':False,'e5_published':False}

def validate_risk_register(review,judgments,risk):
    _require(type(risk)==dict and set(risk)=={
       'schema','video_id','source_sha256','original_study_sha256',
       'prior_review_head_sha256','candidate_issuer_web_lookup_only','risk_records',
       'independent_gold','e3_approved','e4_approved','e5_published'},
       'REGISTER_SCHEMA_OR_AUTHORITY_INVALID')
    _require(risk['schema']==RISK_SCHEMA and risk['video_id']==review.study['video_id'] and
       risk['source_sha256']==review.config['source_sha256'] and
       risk['original_study_sha256']==review.config['frozen_first_study_sha256'] and
       risk['prior_review_head_sha256']==review.status()['review_head_sha256'] and
       risk['candidate_issuer_web_lookup_only'] is True and
       all(risk[x] is False for x in ('independent_gold','e3_approved','e4_approved','e5_published')),
       'RISK_REGISTER_FALSE_SOURCE_OR_CERTIFICATION')
    correct=make_risk_register(review,judgments)
    _require(risk==correct,'RISK_84_SOURCE_CENSUS_OR_TAMPER')
    _require(len(risk['risk_records'])==84 and
       sum(r['old_disposition']=='QUARANTINE_UNSAFE_INVESTMENT_ADVICE' for r in risk['risk_records'])==28,
       'ALL_84_HIGH_RISK_AND_28_QUARANTINES_REQUIRED')
    return True

def build_review_view(review,repair,*,expected_overlay_head,risk_register):
    a,b,old,amend=_read_pinned(review,repair,expected_overlay_head)
    validate_risk_register(review,old,risk_register)
    rows=[]
    for serial in range(1,121):
        atom=review.atoms[serial-1];prior=old[serial];patch=amend.get(serial)
        if patch:
            _require(patch['first_claim_sha256']==_sha(atom) and
              patch['prior_second_judgment_sha256']==_sha(prior),'WRONG_PATCH_SOURCE')
        reading=(patch['corrected_proposition'] if patch and patch['repair_kind'] in
                 ('SOURCE_REWRITE_PROPOSED','PRESERVE_QUARANTINE_SOURCE_REPHRASE') else None)
        # Crucial: even when textual proposal exists, the frozen first-turn text
        # is the historical record, NOT a new accepted fact or published atom.
        rows.append({
          'serial':serial,'original_claim_sha256':_sha(atom),
          'original_spoken_proposition':atom['proposition'],
          'original_kind':atom['kind'],'cue_index':atom['cue_index'],
          'source_text_sha256':sha256(_safe_source_quote(review.cues,atom).encode()),
          'frozen_second_judgment_sha256':_sha(prior),
          'frozen_second_disposition':prior['e3_disposition'],
          'first_turn_high_risk':atom['high_risk'],
          'old_quarantine_enforced':prior['e3_disposition']=='QUARANTINE_UNSAFE_INVESTMENT_ADVICE',
          'correction_kind':patch['repair_kind'] if patch else None,
          'source_fidelity_rewrite_proposal_only':reading,
          'proposed_nonatomic_exclusion_only':bool(patch and patch['repair_kind']=='REMOVE_NONATOMIC_PROPOSED'),
          'proposed_parent_relation_serial_only':patch['related_serial'] if patch and patch['repair_kind']=='PARENT_RELATION_REVIEW_REQUIRED' else None,
          'original_still_in_record':True,'removed_or_merged_as_fact':False,
          'risk_issue_still_open':bool(atom['high_risk']),
          'safe_for_financial_answers':False,
          'independent_gold':False,'finance_fact_approved':False,'e3_approved':False,
          'e4_approved':False,'e5_published':False})
    n=Counter(p['repair_kind'] for p in amend.values())
    _require(n==Counter({'SOURCE_REWRITE_PROPOSED':11,'PRESERVE_QUARANTINE_SOURCE_REPHRASE':1,
        'PARENT_RELATION_REVIEW_REQUIRED':2,'REMOVE_NONATOMIC_PROPOSED':2}),
        'PROPOSALS_SHOULD_REMAIN_16_AND_UNAPPROVED')
    qs=[r for r in rows if r['old_quarantine_enforced']]
    hr=[r for r in rows if r['first_turn_high_risk']]
    _require(len(rows)==120 and len(qs)==28 and len(hr)==84 and
      all(not x['safe_for_financial_answers'] for x in rows) and
      all(x['risk_issue_still_open'] for x in hr),'NO_PROVISIONAL_PROMOTION_OR_RISK_DROP')
    view={
      'schema':VIEW_SCHEMA,'video_id':a['video_id'],
      'source_sha256':a['source_sha256'],
      'frozen_first_head_sha256':a['first_turn_frozen_owner_head_sha256'],
      'frozen_second_head_sha256':a['review_head_sha256'],
      'frozen_v196_repair_head_sha256':expected_overlay_head,
      'frozen_original_candidates':120,'candidate_read_model_count':120,
      'v196_correction_proposals':16,'source_rewrite_proposals':12,
      'nonatomic_exclusion_proposals':2,'parent_link_review_proposals':2,
      'original_quarantines_enforced':28,
      'all_original_high_risk_blocked':84,
      'other_high_risk_hold_blocked':56,
      'all_high_risk_source_issues_open':84,
      'first_turn_open_cues_preserved':a['first_turn_open_cue_count'],
      'first_turn_unresolved_tasks_preserved':a['first_turn_unresolved_tasks_count'],
      'risk_register_sha256':_sha(risk_register),
      'records':rows,'official_evidence_bytes_verified':False,
      'independent_gold':False,'accuracy_metrics_measured':False,
      'e3_approved':False,'e4_approved':False,'e5_published':False,
      'decision':'E3_HOLD_REPAIR_PROPOSALS_PROJECTED_NO_FACT_APPROVAL'}
    return view

def seal_read_model(path,view):
    p=Path(path)
    _require(not p.is_symlink() and not p.exists(),'NO_OVERWRITE_OR_SYMLINK')
    _require(view.get('schema')==VIEW_SCHEMA and view.get('decision')==
             'E3_HOLD_REPAIR_PROPOSALS_PROJECTED_NO_FACT_APPROVAL' and
             all(view.get(x) is False for x in ('e3_approved','e4_approved','e5_published')),
             'INVALID_SOURCE_PROJECTION_FOR_SEAL')
    p.parent.mkdir(parents=True,exist_ok=True)
    payload={'schema':CUSTODY_SCHEMA,'view_sha256':_sha(view),'view':view}
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as f:f.write(_canonical(payload));f.flush();os.fsync(f.fileno())
    return _sha(payload)

def verify_seal(path,expected_view):
    p=Path(path)
    _require(p.is_file() and not p.is_symlink() and
             not (stat.S_IMODE(p.stat().st_mode)&0o077),'PRIVATE_SEAL_MISSING_OR_UNSAFE_PERMISSION')
    obj=json.loads(p.read_bytes())
    _require(obj.get('schema')==CUSTODY_SCHEMA and
             obj.get('view_sha256')==_sha(expected_view) and
             obj.get('view')==expected_view and
             p.read_bytes()==_canonical(obj),'PRIVATE_SEAL_TAMPER_OR_WRONG_INPUT')
    return _sha(obj)