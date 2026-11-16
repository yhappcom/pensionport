"""V141 public structural policy barrier: never misread cue census as P0 acceptance.

No private source or real V123 artifacts are available in public CI. This module
only rejects false promotions and checks required context dependencies; it cannot
issue V123 PASS, knowledge publication or personalized advice.
"""
from __future__ import annotations
from dataclasses import dataclass

EXPECTED_PARENT_SHA='638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d'
HIGH_RISK_PUBLIC = frozenset({
 'B7_SAMSUNG_DID_NOT_MAKE_HBM_FALSE',
 'B7_FIXED_FOUR_YEAR_CYCLE_EXAGGERATION',
 'B8_HBM_EXCLUSIVITY_OVERSTATEMENT',
 'B8_AI_MUST_STORE_ALL_USER_DATA_FALSE',
 'B10_DRAWDOWN_ALWAYS_LEADS_BIG_GAIN_FALSE',
 'B11_DIVIDEND_YIELD_EQUALS_MARGIN_FALSE',
 'B12_TECH_SUCCESS_NINETY_PERCENT_ASSUMPTION',
 'B12_WAIT_FOR_CONFIRMATION_ALWAYS_TOO_LATE_FALSE',
 'B13_FIVE_STOCKS_LIFE_CHANGING_GAIN_ADVOCACY',
 'B13_PERSONALITY_BASED_STOCK_CONCENTRATION_INVITATION',
})
MUST_CARRY_CONTEXT = {
 'B13_FIVE_STOCKS_LIFE_CHANGING_GAIN_ADVOCACY': ('B10_NONEXPERT_DIVERSIFY_EXCEPTION', 'B10_DRAWDOWN_ALWAYS_LEADS_BIG_GAIN_FALSE'),
 'B13_PERSONALITY_BASED_STOCK_CONCENTRATION_INVITATION': ('B10_NONEXPERT_DIVERSIFY_EXCEPTION',),
 'B10_CONCENTRATE_WHEN_ODDS_HIGH_PRINCIPLE': ('B10_NONEXPERT_DIVERSIFY_EXCEPTION',),
 'B11_DIVIDEND_YIELD_EQUALS_MARGIN_FALSE': ('B11_VALUE_100_PRICE_60_HYPOTHETICAL',),
 'B12_BUY_BEFORE_RESULT_HIGH_ODDS': ('B12_TECH_SUCCESS_NINETY_PERCENT_ASSUMPTION',),
 'B7_SAMSUNG_DID_NOT_MAKE_HBM_FALSE': ('B8_HBM_EXCLUSIVITY_OVERSTATEMENT',),
 'B7_FIXED_FOUR_YEAR_CYCLE_EXAGGERATION': ('B7_CYCLE_BREAK_RERATING_HYPOTHESIS',),
}

def audit_candidate_readonly(*, parent_source_sha256:str, candidate_claim_ids:list[str],
                             approved_v123_receipts:int=0, formal_knowledge_entries:int=0):
    """Scope-limited preliminary consumer gate; never an advisory approval."""
    if parent_source_sha256!=EXPECTED_PARENT_SHA:
        return {'status':'HOLD_SOURCE_IDENTITY_DRIFT','answer_release_allowed':False,'p0_go':False}
    if type(candidate_claim_ids) is not list or any(type(x) is not str for x in candidate_claim_ids):
        return {'status':'HOLD_INVALID_CANDIDATE_IDS','answer_release_allowed':False,'p0_go':False}
    chosen=set(candidate_claim_ids)
    missing={x: [y for y in req if y not in chosen] for x,req in MUST_CARRY_CONTEXT.items() if x in chosen}
    missing={x:v for x,v in missing.items() if v}
    if missing:
        return {'status':'HOLD_MISSING_MANDATORY_SEMANTIC_CONTEXT','missing_context':missing,
                'answer_release_allowed':False,'p0_go':False}
    if chosen & HIGH_RISK_PUBLIC:
        return {'status':'HOLD_HIGH_RISK_SOURCE_FACT_OR_ADVICE_UNAPPROVED',
                'high_risk_ids':sorted(chosen & HIGH_RISK_PUBLIC),
                'answer_release_allowed':False,'p0_go':False}
    # Even forged counts do not prove original signed V123 release/owner DB.
    if approved_v123_receipts!=0 or formal_knowledge_entries!=0:
        return {'status':'HOLD_UNVERIFIED_SELF_ATTESTED_APPROVAL_COUNTS',
                'answer_release_allowed':False,'p0_go':False}
    return {'status':'HOLD_NO_SIGNED_REAL_V123_AND_OWNER_DB_REPLAY',
            'answer_release_allowed':False,'p0_go':False}

def audit_census_not_final(metadata):
    """A public SHA receipt can prove neither semantic completeness nor GO."""
    if type(metadata) is not dict or metadata.get('parent_source_sha256')!=EXPECTED_PARENT_SHA:
        return {'status':'HOLD_SOURCE_UNTRUSTED','p0_go':False,'knowledge_export_allowed':False}
    if (metadata.get('reviewed_cue_count')!=1481 or metadata.get('segments_count')!=13 or
        metadata.get('new_cue_dispositions')!=761 or metadata.get('new_provisional_atom_occurrences')!=109):
        return {'status':'HOLD_CENSUS_INCONSISTENT','p0_go':False,'knowledge_export_allowed':False}
    return {'status':'SOURCE_CENSUS_COMPLETE_FINAL_SEMANTIC_QUALITY_UNPROVEN',
            'p0_go':False,'knowledge_export_allowed':False,
            'real_v123_pass':False,'personal_advice_approved':False}
