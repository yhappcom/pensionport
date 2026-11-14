"""V94 dated-financial-rule evidence routing: latest law vs historical utterance.
Not a legal fact oracle, official signed snapshot, or personal tax calculator.
A rule is used for *scope review* only after verifying date and applicable facts.
"""
from datetime import date
from urllib.parse import urlparse
import hashlib,json

OFFICIAL={'law.go.kr','www.law.go.kr','nts.go.kr','www.nts.go.kr','t.nts.go.kr','taxlaw.nts.go.kr','www.nps.or.kr','m.nps.or.kr','nps.or.kr','www.mohw.go.kr','mohw.go.kr'}

def require(cond,msg):
    if not cond:raise ValueError('V94_'+msg)
def check_date(x):
    require(type(x) is str,'DATE_TYPE')
    try:d=date.fromisoformat(x)
    except (ValueError,TypeError):raise ValueError('V94_INVALID_DATE')
    require(d.isoformat()==x,'DATE_CANONICAL');return d

def validate_rule(rule):
    require(type(rule) is dict,'RULE_TYPE')
    require(type(rule.get('rule_id')) is str and len(rule['rule_id'])>=4,'RULE_ID')
    url=rule.get('source_url');require(type(url) is str,'SOURCE_URL')
    p=urlparse(url)
    require(p.scheme=='https' and p.hostname in OFFICIAL and not p.username and not p.password,'OFFICIAL_SOURCE_REQUIRED')
    start=check_date(rule.get('effective_from'))
    end=check_date(rule['effective_to']) if rule.get('effective_to') else None
    if end is not None:require(start<=end,'INVALID_EFFECTIVE_INTERVAL')
    checked=check_date(rule['checked_at'])
    require(checked>=start or rule.get('source_status')=='FUTURE_ENACTED_NOT_IN_FORCE','CHECK_BEFORE_START')
    require(rule.get('source_status') in {'OFFICIAL_PAGE_CHECKED_SCOPE_ONLY','FUTURE_ENACTED_NOT_IN_FORCE','HISTORIC_STATUTE_SCOPE_ONLY'},'SOURCE_STATUS')
    require(type(rule.get('required_facts')) is list and rule['required_facts'] and all(type(x) is str and x for x in rule['required_facts']),'REQUIRED_FACTS')
    for fld in ('financial_fact_certified','personalized_advice_approved','independent_gold'):
        require(rule.get(fld) is False,'FALSE_PROMOTION')
    return start,end,checked

def route_claim_to_rule(claim,rule,*,today):
    """Distinct video utterance date, current answer date, and client specifics."""
    current=check_date(today)
    start,end,checked=validate_rule(rule)
    require(current>=checked,'FUTURE_SOURCE_CHECK')
    require(type(claim) is dict and claim.get('rule_id')==rule['rule_id'],'RULE_ID_MISMATCH')
    utter=check_date(claim['utterance_as_of']) if claim.get('utterance_as_of') else None
    if utter is not None:require(utter<=current,'FUTURE_UTTERANCE')
    facts=claim.get('client_facts')
    require(type(facts) is dict,'FACTS_TYPE')
    missing=[x for x in rule['required_facts'] if x not in facts or facts[x] is None]
    in_force=start<=current and (end is None or current<=end)
    source_fresh= (current-checked).days<=90
    if not in_force:decision='NOT_CURRENT_EFFECTIVE_RULE'
    elif not source_fresh:decision='STALE_OFFICIAL_SOURCE_RECHECK'
    elif missing:decision='CLIENT_APPLICABILITY_UNKNOWN'
    elif utter is None:decision='ORIGINAL_UTTERANCE_DATE_UNKNOWN'
    elif rule['source_status']!='OFFICIAL_PAGE_CHECKED_SCOPE_ONLY':decision='OFFICIAL_SNAPSHOT_REVIEW_REQUIRED'
    else:decision='CURRENT_SCOPE_REVIEW_ONLY'
    return {'rule_id':rule['rule_id'],'date_checked':today,'utterance_date_supplied':utter is not None,
        'client_required_facts_missing':missing,'rule_in_force_on_answer_date':in_force,
        'source_checked_recently':source_fresh,'decision':decision,
        'personal_advice_allowed':False,'tax_calculation_approved':False,
        'historical_claim_fact_certified':False,'independent_quality_certified':False}

def review_ledger(claims,rules,*,today):
    require(type(claims) is list and type(rules) is list,'LEDGER_TYPE')
    keys=set();decisions=[]
    for rule in rules:
        validate_rule(rule);require(rule['rule_id'] not in keys,'DUPLICATE_RULE');keys.add(rule['rule_id'])
    by_id={r['rule_id']:r for r in rules}
    for claim in claims:
        rule=by_id.get(claim.get('rule_id'))
        require(rule is not None,'RULE_MISSING')
        decisions.append(route_claim_to_rule(claim,rule,today=today))
    return {'schema':'V94_ASOF_FINANCIAL_SCOPE_ONLY_NO_APPROVAL_V1','claims_checked':len(decisions),
        'outcomes':{k:sum(x['decision']==k for x in decisions) for k in sorted(set(x['decision'] for x in decisions))},
        'all_personal_approvals_false':True,'new_financial_fact_approvals':0,'p0_go':False}