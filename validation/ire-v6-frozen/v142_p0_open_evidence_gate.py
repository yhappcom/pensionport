"""V142 fail-closed evidence gate for original audio OPEN and high-risk claims.

Public metadata can establish only custody and the existence of blockers.
This module never makes a V123 decision or issues personal investment advice.
"""
from __future__ import annotations

PARENT_SHA='638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d'
SCHEMA='V142_PUBLIC_SOURCE_FIRST_OPEN_TRIAGE_SHA_ONLY_V1'
NEEDED={
 'source_original_cues':1481,
 'source_cues_replayed':1481,
 'provisional_atoms':274,
 'open_source_cues_original':88,
 'open_source_cues_remain_unverified_audio':88,
 'high_impact_open_cues_requiring_audio_and_fact_evidence':52,
 'context_classifiable_but_audio_unverified_open_cues':36,
 'high_impact_claim_adjudications':13,
 'v123_final_passed_segments':0,
 'final_approved_knowledge_atoms':0,
}
REQUIRED_FACT_CHECK={
 'B7_SAMSUNG_DID_NOT_MAKE_HBM_FALSE': 'B8_HBM_EXCLUSIVITY_OVERSTATEMENT',
 'B7_FIXED_FOUR_YEAR_CYCLE_EXAGGERATION':'B7_CYCLE_BREAK_RERATING_HYPOTHESIS',
 'B8_HBM_EXCLUSIVITY_OVERSTATEMENT':'B7_SAMSUNG_DID_NOT_MAKE_HBM_FALSE',
 'B8_AI_MUST_STORE_ALL_USER_DATA_FALSE':'B8_AI_PERSONALIZATION_PREVIOUS_HISTORY',
 'B10_CONCENTRATE_WHEN_ODDS_HIGH_PRINCIPLE':'B10_NONEXPERT_DIVERSIFY_EXCEPTION',
 'B10_DRAWDOWN_ALWAYS_LEADS_BIG_GAIN_FALSE':'B10_NONEXPERT_DIVERSIFY_EXCEPTION',
 'B11_CASH_RICH_CHEAP_DIVIDEND_STOCK':'B11_MARGIN_OF_SAFETY_DOWNSIDE_BUFFER',
 'B11_DIVIDEND_YIELD_EQUALS_MARGIN_FALSE':'B11_VALUE_100_PRICE_60_HYPOTHETICAL',
 'B12_TECH_SUCCESS_NINETY_PERCENT_ASSUMPTION':'B12_BUY_BEFORE_RESULT_HIGH_ODDS',
 'B12_BUY_BEFORE_RESULT_HIGH_ODDS':'B12_TECH_SUCCESS_NINETY_PERCENT_ASSUMPTION',
 'B12_WAIT_FOR_CONFIRMATION_ALWAYS_TOO_LATE_FALSE':'B12_TECH_SUCCESS_NINETY_PERCENT_ASSUMPTION',
 'B13_FIVE_STOCKS_LIFE_CHANGING_GAIN_ADVOCACY':'B10_NONEXPERT_DIVERSIFY_EXCEPTION',
 'B13_PERSONALITY_BASED_STOCK_CONCENTRATION_INVITATION':'B13_SPEAKER_USUALLY_RECOMMENDS_DIVERSIFY'
}

def audit_public_triage(metadata):
    """Reject false clearance or PASS; a valid receipt still stays HOLD."""
    if type(metadata) is not dict or metadata.get('schema')!=SCHEMA or metadata.get('source_sha256')!=PARENT_SHA:
        return {'status':'REJECT_WRONG_REAL_PARENT_OR_SCHEMA','p0_go':False,'knowledge_release_allowed':False}
    for key,expected in NEEDED.items():
        if type(metadata.get(key)) is not int or metadata[key]!=expected:
            return {'status':'REJECT_OPEN_OR_CUE_CENSUS_DRIFT_'+key.upper(), 'p0_go':False,'knowledge_release_allowed':False}
    if type(metadata.get('provisional_atom_references_replayed')) is not int or metadata['provisional_atom_references_replayed']!=1225:
        return {'status':'REJECT_ATOM_REFERENCES_DRIFT','p0_go':False,'knowledge_release_allowed':False}
    if metadata.get('derived_from_source_only_context_not_raw_audio') is not True:
        return {'status':'REJECT_FAKE_AUDIO_REVIEW_PROVENANCE','p0_go':False,'knowledge_release_allowed':False}
    # A true value from a metadata author is NOT an authenticated V123 review.
    if any(metadata.get(k) is not False for k in (
        'original_audio_in_attached_archives','independent_semantic_precision_verified',
        'all_13_v123_pass','research_publication_allowed','formal_finance_legal_fact_approval',
        'personal_portfolio_advisory_approved','p0_go')):
        return {'status':'REJECT_SELF_ATTESTED_APPROVAL_WITH_OPEN_SOURCE','p0_go':False,'knowledge_release_allowed':False}
    return {'status':'REAL_SOURCE_AND_88_OPEN_CENSUS_VERIFIED_REMAIN_HOLD',
            'provisional_atom_count':274,'audio_open_count':88,'p0_go':False,
            'knowledge_release_allowed':False,'personal_advice_approved':False}

def audit_high_risk_context(selected_atom_ids, *, requested_release=False):
    """Presence of context is necessary but is never sufficient for release."""
    if type(selected_atom_ids) is not list or any(type(x) is not str for x in selected_atom_ids):
        return {'status':'REJECT_BAD_CLAIM_IDS','p0_go':False,'release_allowed':False}
    chosen=set(selected_atom_ids)
    missing={a:b for a,b in REQUIRED_FACT_CHECK.items() if a in chosen and b not in chosen}
    if missing:
        return {'status':'HOLD_MISSING_SOURCE_BOUND_RISK_CONTEXT','missing_required_context':missing,
                'p0_go':False,'release_allowed':False}
    unresolved=chosen & set(REQUIRED_FACT_CHECK)
    if unresolved:
        return {'status':'HOLD_SOURCE_ONLY_HIGH_RISK_FACT_OR_ADVICE','high_risk_atoms':sorted(unresolved),
                'p0_go':False,'release_allowed':False}
    return {'status':'HOLD_NO_REAL_V123_SIGNED_PARENT_REPLAY',
            'p0_go':False,'release_allowed':False}
