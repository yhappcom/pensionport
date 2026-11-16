"""V140 deterministic CURRENT-law educational scope sanity checks (not legal advice).

Public law.go.kr excerpts have been examined in this chat as of 2026-11-16,
not independently authenticated original issuer bytes. This function cannot
approve individual eligibility, account status, orders, or personal tax advice.
"""
from __future__ import annotations

VALID_DATE='2026-11-16'
ISA_EFFECTIVE='2026-09-18'
PENSION_EFFECTIVE='2026-07-01'

class ScopeError(ValueError): pass

def current_rule_preflight(case):
    if type(case)!=dict or case.get('as_of')!=VALID_DATE:
        raise ScopeError('V140_AS_OF_MISMATCH_OR_MISSING')
    kind=case.get('kind')
    if kind=='ISA':
        # Assessment of this qualification must itself be supplied by a
        # verified source and personal facts. Never infer from salary alone.
        qualifier=case.get('statutory_400man_condition_verified')
        if qualifier is True:
            bound=4_000_000
            status='CONDITIONAL_400MAN_SCOPE_NOT_PERSONALLY_APPROVED'
        elif qualifier is False and case.get('statutory_general_case_verified') is True:
            bound=2_000_000
            status='CONDITIONAL_GENERAL_200MAN_SCOPE_NOT_PERSONALLY_APPROVED'
        else:
            bound=None
            status='OPEN_NO_VERIFIED_ELIGIBILITY_AND_ACCOUNT_TERMS'
        return {'kind':kind,'law':'조세특례제한법 제91조의18',
                'effective_as_of':ISA_EFFECTIVE,'statutory_exemption_cap_won':bound,
                'status':status,'account_terms_verified':False,
                'personal_tax_or_investment_advice_approved':False,'p0_go':False}
    if kind=='PENSION':
        # Tax-credit ceiling (not contribution ceiling), statutory general
        # comparison only. Requires taxability, earned income and exclusions.
        pension_max=6_000_000
        combined_max=9_000_000
        eligible_band=case.get('income_threshold_15_percent_verified')
        pct=15 if eligible_band is True else 12 if eligible_band is False else None
        return {'kind':kind,'law':'소득세법 제59조의3',
                'effective_as_of':PENSION_EFFECTIVE,'pension_savings_max_credit_base_won':pension_max,
                'combined_account_max_credit_base_won':combined_max,
                'statutory_credit_rate_percent':pct,
                'status':'CONDITIONAL_GENERAL_CREDIT_BASE_NO_PERSONAL_APPROVAL' if pct is not None else 'OPEN_INCOME_CLASSIFICATION_UNVERIFIED',
                'contribution_eligibility_verified':False,
                'personal_tax_or_investment_advice_approved':False,'p0_go':False}
    raise ScopeError('V140_UNSUPPORTED_REGULATORY_SCENARIO')

def advisory_route_acceptance(*, source_v123_passed, parent_knowledge_published,
                              real_operational_db_attested, original_issuer_bytes_sha_verified,
                              effective_law_and_issuer_scope_verified,
                              v5_v23_live_current_law_run_executed,
                              actual_user_facts_verified):
    # No flags from an unauthenticated JSON object can substitute a true V123
    # receipt, V128 publication, or actual source-backed end-to-end answer.
    pending=[name for name,v in locals().items() if v is not True]
    return {'status':'BLOCKED_MISSING_REAL_ACCEPTANCE_PROOF' if pending else 'READY_FOR_MANUAL_HOST_REVIEW_NO_AUTOMATIC_APPROVAL',
            'unproven_gates':pending,'full_real_e2e_certified':False,
            'personal_order_enabled':False,'p0_go':False}
