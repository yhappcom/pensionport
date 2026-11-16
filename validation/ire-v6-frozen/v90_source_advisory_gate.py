"""V90: source-bound #7 ISA/NPS/REIT high-risk provisional review and P3 no-promotion guard.
All real SRT and human-in-chat meaning is owner-private. Synthetic-only CI does not
measure financial fact precision or certify personal investment recommendations.
"""
from __future__ import annotations
import hashlib,json
from collections import Counter
from v87_targeted_source_guard import expected_parent_source
from v89_isa_source_guard import ISA_SCOPE, ISA_AUTHORITIES
VIDEO_ID='4CQ4FjGT2gA'
OWNER_SHA='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
PRIOR_ARCHIVES={
84:'b8fa34d4f36a790608aa4e7f6662caf14567fee9c8eedef68000d1e1b3df9e2d',
85:'0c87078e870bb88536667cc5a60a68eaeff71914740c9571242dc988caaa584d',
86:'82b35be0c691aa832102255ac324e73a815c37259228370ff1c91cb53ca2e71d',
87:'ff028b1c51f2429980fca26a1ddf0f607ed7d2a198b1a53fc7597a9928eb58b4',
88:'770c55af94d4d041092ce4df89ff27d64cfc7681b62d5e9542a4c6a92a870d50',
89:'fee2fe3ba9d44aa2c42917482086d625b0020005df9fa45d91c82e71d33e70ce',
}
EXPECTED={
'W00022':('C00340','C00341','C00343','C00344'),
'W00114':('C01521','C01524','C01525','C01528'),
'W00119':('C01576','C01577','C01579','C01581'),
'W00142':('C01830','C01832','C01836','C01838'),
'W00145':('C01869','C01871','C01873','C01874'),
'W00146':('C01877','C01882','C01883','C01884'),
'W00159':('C02036','C02040','C02041','C02046'),
'W00161':('C02061','C02064','C02066','C02070'),
'W00167':('C02129','C02132','C02133','C02138'),
'W00175':('C02214','C02215','C02219','C02220'),
'W00234':('C02969','C02970','C02971','C02973'),
'W00235':('C02975','C02977','C02978','C02982'),
}
SOURCE_COUNT=10728
WINDOW_COUNT=269
STATUS='SOURCE_BOUND_CHAT_SHADOW_NOT_INDEPENDENT_GOLD'
FALSE_FLAGS=('fact_approved','independent_gold','official_parent_merged','personal_action_approved',
             'v75_membership_verified','financial_fact_certified','independent_precision_recall_certified',
             'personalized_advice_approved','full_window_semantics_certified','audio_verified',
             'law_current_verified')
KINDS={'DESCRIPTIVE_FINANCE','HISTORICAL_CASE','OPINION','HYPOTHESIS','QUESTION_NOT_FACT',
       'CONDITIONAL_ADVICE','REPORTED_NUMERIC','ASR_UNCERTAIN'}
ASOF='2026-11-13'
AUTHORITIES={
'LAW_ISA':'https://law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1024341967',
'KB_ISA':'https://blog.kbsec.com/isa/%EB%B9%84%EA%B3%BC%EC%84%B8%ED%95%9C%EB%8F%84-%EC%86%90%EC%9D%B5%ED%86%B5%EC%82%B0/',
'NPS_CREDIT':'https://m.nps.or.kr/pnsinfo/ntpsklg/getOHAF0095M0.do?menuId=MN24001131',
'NPS_TOPUP':'https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0095M0.do',
'ETF_RISK':'https://www.mynamuh.com/WMDoc.action?viewPage=%2FstockGuide%2FlocalMarket%2FetfIntro.jsp',
}
# Policy categories are risk routing only; they do not compute tax or trade orders.
ROUTING={
('DIRECT_DOMESTIC_LISTED_SHARE','REALIZED_TRADING_GAIN'):'NON_TAXABLE_GAIN_EXCLUDED',
('DIRECT_DOMESTIC_LISTED_SHARE','NET_REALIZED_TRADING_LOSS'):'POTENTIALLY_NETTABLE_IF_ELIGIBLE',
('DOMESTIC_EQUITY_FUND_ETF','EXEMPT_EQUITY_TRADING_LOSS'):'NON_TAXABLE_COMPONENT_EXCLUDED',
('FUND_OR_ETF','TAXABLE_BASIS_LOSS'):'POTENTIALLY_NETTABLE_BY_TAX_BASIS',
('ISA','CALENDAR_YEAR_ACCUMULATION'):'NEEDS_ACCOUNT_OPEN_DATE_AND_CONTRIBUTIONS',
('ISA','PENSION_MATURITY_TRANSFER'):'NEEDS_MATURITY_60_DAY_CUSTODY',
('NPS','UNEMPLOYMENT_CREDIT'):'NEEDS_AGE_PRIOR_PAYMENTS_INCOME_PROPERTY',
('NPS','RETROACTIVE_CONTRIBUTIONS'):'NEEDS_APPLICATION_PERIOD_AND_RATE_ASOF',
('BOND_MATURITY_ETF','PRINCIPAL_GUARANTEE'):'NOT_PRINCIPAL_GUARANTEED',
('REIT','HIGH_DISTRIBUTION_YIELD'):'NOT_GUARANTEED_DISTRIBUTION_OR_TOTAL_RETURN',
('PORTFOLIO','AVERAGING_DOWN_PROFIT'):'REQUIRE_CASHFLOW_LEDGER',
}

def fail(code):raise ValueError('V90_'+code)
def ensure(v,code):
    if not v:fail(code)
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
def digest(x):return sha(canonical(x))
def risk_route(asset_kind,component):
    ensure(type(asset_kind) is str and type(component) is str,'ROUTE_TYPE')
    return ROUTING.get((asset_kind,component),'MANUAL_REVIEW_REQUIRED')
def shadow_advice_gate(row):
    """Never convert a shadow claim into evidence-backed personalized recommendations."""
    ensure(type(row) is dict,'ROW_TYPE')
    ensure(row.get('status')==STATUS,'STATUS')
    for field in FALSE_FLAGS:ensure(row.get(field) is False,'FALSE_GO_'+field)
    ensure(row.get('semantic_kind') in KINDS,'KIND')
    for field in ('speaker_meaning_private','scope_caution_private','risk_domain'):
        ensure(type(row.get(field)) is str and len(row[field])>=8,'MISSING_SEMANTICS_'+field)
    ensure(len(row['speaker_meaning_private'])>=40 and len(row['scope_caution_private'])>=40,'NO_CONTEXTUAL_JUDGEMENT')
    return {'can_promote_to_p3_advice':False,'can_merge_into_master116':False,'can_count_as_gold':False}

def check_review(row,cues,regs):
    ensure(type(row) is dict,'RECORD_TYPE')
    key=(row.get('window_id'),row.get('claim_id'))
    ensure(key[0] in EXPECTED and key[1] in EXPECTED[key[0]],'UNKNOWN_PARENT')
    ensure(row.get('video_no')==7 and row.get('video_id')==VIDEO_ID,'VIDEO')
    exp=expected_parent_source(cues,regs,key)
    for f in ('window_id','claim_id','cue_indices','start_ms','end_ms','source_excerpt_private',
              'source_sha256','adjacent_cues_private','adjacent_context_sha256'):
        ensure(row.get(f)==exp[f],'SOURCE_'+f)
    ensure(row['source_sha256']==sha(row['source_excerpt_private'].encode('utf-8')),'PARENT_SHA')
    ensure(row['adjacent_context_sha256']==digest(row['adjacent_cues_private']),'ADJACENT_SHA')
    shadow_advice_gate(row)
    return digest([key[0],key[1],row['source_sha256'],row['semantic_kind'],
                   sha(row['speaker_meaning_private'].encode('utf-8')),
                   sha(row['scope_caution_private'].encode('utf-8'))])

def check_screen(screen,all_screens,cues,regs):
    ensure(type(screen) is dict,'SCREEN_TYPE')
    ensure(len(cues)==SOURCE_COUNT and len(regs)==WINDOW_COUNT,'SOURCE_CENSUS')
    ensure(type(all_screens) is list and len(all_screens)==WINDOW_COUNT,'SCREEN_269')
    m={x['window_id']:x for x in all_screens};ensure(len(m)==WINDOW_COUNT,'SCREEN_UNIQUE')
    w=screen.get('window_id');ensure(w in EXPECTED and screen==m.get(w),'SCREEN_DRIFT')
    n=int(w[1:]);fst=(n-1)*40+1;last=min(n*40,len(cues))
    ensure(screen['video_id']==VIDEO_ID and screen['video_no']==7,'SCREEN_VIDEO')
    ensure(screen['first_cue']==fst and screen['last_cue']==last,'SCREEN_BOUNDS')
    ensure(screen['draft_parent_count']==len(regs[w]),'SCREEN_PARENTS')
    ensure(screen['source_window_sha256']==sha(' '.join(cues[i-1].text for i in range(fst,last+1)).encode('utf-8')),'SCREEN_SHA')
    for f in ('manual_reviewed_all_parents','fact_approved','independent_gold','personal_action_approved'):
        ensure(screen.get(f) is False,'SCREEN_FALSE_GO_'+f)
    return digest(screen)

def verify_batch(rows,selected_screens,all_screens,cues,regs,prior):
    ensure(type(rows) is list and len(rows)==48,'NEW_48_REQUIRED')
    ensure(type(selected_screens) is list and len(selected_screens)==12,'SCREEN_12_REQUIRED')
    ensure(type(prior) is set and len(prior)==157,'PRIOR_157_REQUIRED')
    prior_wins={w for w,c in prior};ensure(len(prior_wins)==53,'PRIOR_53_WINDOWS')
    expected={(w,c) for w,claims in EXPECTED.items() for c in claims}
    ensure(len(expected)==48,'EXPECTED_48')
    ensure(not (prior_wins & set(EXPECTED)),'PRIOR_WINDOW_REUSE')
    ensure({s.get('window_id') for s in selected_screens}==set(EXPECTED),'SELECTED_SCREEN_SCOPE')
    for screen in selected_screens:check_screen(screen,all_screens,cues,regs)
    seen=set();ds=[];counts=Counter()
    for row in rows:
        key=(row.get('window_id'),row.get('claim_id'))
        ensure(key in expected and key not in seen and key not in prior,'DUP_OR_EXTRA_PARENT')
        seen.add(key);counts[key[0]]+=1
        ds.append(check_review(row,cues,regs))
    ensure(seen==expected and all(counts[w]==4 for w in EXPECTED),'INCOMPLETE_WINDOW')
    union=prior|seen
    ensure(len(union)==205 and len({w for w,c in union})==65,'CUMULATIVE_205_65')
    return {'new_manual_parents':48,'new_sampled_windows':12,'prior_shadow_parents':157,
            'cumulative_shadow_parents':205,'cumulative_sampled_windows':65,
            'video7_windows_without_parent_sample':204,
            'new_review_evidence_sha256':digest(sorted(ds)),'p0_go':False,
            'full_window_semantics_certified':False,'independent_gold':False}

def no_false_p0():
    return {'v75_887_official_pending_unchanged':887,'v75_history_membership_verified':False,
            'audio_open_unchanged':3,'independent_precision_recall_certified':False,
            'financial_fact_certified':False,'master116_merged':False,
            'personalized_advice_approved':False,'p0_go':False}