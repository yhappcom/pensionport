#!/usr/bin/env python3
"""V3.2 general financial-event enrichment after *failed* V3.1 first use.

Scope: ETF microstructure, pension lifecycle, portfolio downside controls,
government savings deposits and rate/period distinctions. The V3.1 engine,
its frozen first-use gold and failures remain unchanged.

Tags are *not* verification of financial truth. This is an explanatory
human-review-retrieval lens; financial relations never auto-approve.
"""
import re
from collections import Counter
from v30_verified_core import guard,CLAIM_RE,VERDICTS
from v30_semantic_v31 import pair_review,derive_facets,normalized_text_words

# These concepts are classes of financial events, not fitted claim IDs or
# frozen gold labels. Priority: product and metric identity precedes a
# lexical coincidence of interest rates, ages or dollar amounts.
V32_EXTRA_PATTERNS={
 "ETF_ASSETS_UNDER_MANAGEMENT":r"순자산|ETF.{0,24}규모|규모.{0,24}ETF",
 "ETF_MARKET_LIQUIDITY":r"거래량|호가|매수.{0,10}매도.{0,14}차이",
 "ETF_PRICE_NAV_DISCOUNT":r"괴리율|NAV.{0,24}(?:시장.?가격|거래가격)|(?:시장.?가격|거래가격).{0,24}NAV",
 "ETF_TRACKING_ERROR":r"추적오차|ETF.{0,16}지수.*수익률.*차이|지수.{0,12}ETF.*수익률.*차이",
 "ETF_EXPENSE_RATIO":r"운용보수|ETF.{0,35}보수|보수.{0,30}ETF|보수율",
 "ETF_INDEX_METHOD":r"패시브|액티브|TR\s*지수|PR\s*지수|지수.*재투자",
 "ETF_DISTRIBUTION_MECHANISM":r"ETF.*분배|분배금|분배락|배당금.*ETF",
 "PENSION_LATE_START":r"55세.{0,50}연금|연금.{0,40}55세|늦지.*연금",
 "PENSION_ACCOUNT_LIFECYCLE":r"연금저축|연금계좌|IRP|퇴직연금|연금.*운용",
 "PORTFOLIO_LOSS_BUFFER":r"비상자금|안전자금|위험자산.*분리|분산계좌|분산투자|전체 손실.*제한|고위험.{0,14}분산",
 "EQUITY_LONG_HORIZON_RISK":r"지수.{0,12}장기|장기투자|장기분산|급등주.*장기|기업 퇴출",
 "YOUTH_POLICY_SAVINGS_PROGRAM":r"청년미래적금|청년.*(?:적금|우대형|기여금)|정부.*(?:기여금|지원율)",
 "YOUTH_SAVINGS_GOVERNMENT_MATCH":r"기여금|정부.{0,22}(?:6%|12%|지원)|우대형.*12%|일반형.*6%",
 "YOUTH_SAVINGS_BANK_INTEREST":r"은행금리|기본금리|우대.{0,18}(?:금리|포인트)|금리.{0,8}이자",
 "MONTHLY_SAVINGS_CONTRIBUTION_SCHEDULE":r"월.{0,15}만원.{0,20}(?:납입|적금)|36개월.{0,20}(?:원금|납입)|납입원금|적금.{0,12}3년",
 "YOUTH_SAVINGS_ELIGIBILITY":r"가구.?중위소득|총급여.{0,18}기여금|청년미래적금.*가입|재직.{0,18}우대형",
 "PENSION_SAVINGS_CONTRIBUTION_LIMITS":r"(?:IRP|ISA|연금계좌|연금저축).{0,45}(?:납입|한도|연.{0,7}만원)|부부.{0,24}계좌",
 "HOUSING_DOWNSIZE_CASH":r"주택.{0,28}(?:축소|다운사이징|현금화)|다운사이징",
 "INSURANCE_CONTRACT_REDEMPTION":r"보험.{0,26}(?:해약|해지|보증|환급)|(?:해약|해지).*보험",
}
EXTRA={name:re.compile(pattern,re.I) for name,pattern in V32_EXTRA_PATTERNS.items()}
# Explicit scope conflict: matching on generic "interest" must never imply
# that a central-bank policy announcement is a product's investable yield.
NONINTERCHANGEABLE={
 frozenset(("ETF_PRICE_NAV_DISCOUNT","ETF_TRACKING_ERROR")),
 frozenset(("ETF_DISTRIBUTION_MECHANISM","ETF_TRACKING_ERROR")),
 frozenset(("PENSION_SAVINGS_CONTRIBUTION_LIMITS","YOUTH_SAVINGS_ELIGIBILITY")),
 frozenset(("YOUTH_SAVINGS_GOVERNMENT_MATCH","ETF_DISTRIBUTION_MECHANISM")),
 frozenset(("YOUTH_SAVINGS_BANK_INTEREST","ETF_EXPENSE_RATIO")),
}

def facets_v32(text):
    tags=set(derive_facets(text))
    tags.update(name for name,rx in EXTRA.items() if rx.search(text))
    return frozenset(tags)

def pair_review_v32(left,right):
    original=pair_review(left,right)
    tags_a=facets_v32(left["text"]);tags_b=facets_v32(right["text"])
    overlap=sorted(tags_a & tags_b)
    other=[]
    for kinds in NONINTERCHANGEABLE:
        a,b=tuple(kinds)
        if ((a in tags_a and b in tags_b) or
            (b in tags_a and a in tags_b)):
            if not overlap:other.append("+".join(sorted(kinds)))
    conflicts=sorted(set(original["conflicting_cross_scope_types"]+other))
    typed=bool(overlap) and not conflicts
    return {
        "schema":"V32_ENRICHED_TYPED_FINANCIAL_REVIEW_V1",
        "left":left["claim_id"],"right":right["claim_id"],
        "typed_review_candidate":typed,
        "baseline_v31_candidate":original["typed_review_candidate"],
        "matching_financial_event_tags":overlap,
        "cross_scope_conflicts":conflicts,
        "financial_event_annotations_source":"UNREVIEWED_RULE_BASED_PROVISIONAL",
        "legacy_verdict_source_risk":original["source_risk"],
        "source_identity_certified_by_this_function":False,
        "financial_fact_independently_verified":False,
        "automatic_relation_approval":False,
        "automatic_knowledge_merge":False,
        "research_completion_certificate_approved":False,
        "personalized_financial_advice":False,
    }

def review_queue_v32(query,corpus,limit=10):
    """Explanatory typed list; never silently drop unknowns from broad audit."""
    guard(type(query) is dict and type(corpus) in (list,tuple)
          and type(limit) is int and 1<=limit<=100 and
          len(corpus)<=6000,"V32_REVIEW_INPUT_NOT_BOUNDED")
    ranked=[]
    qwords=normalized_text_words(query["text"])
    for cand in corpus:
        if cand["claim_id"]==query["claim_id"]:continue
        out=pair_review_v32(query,cand)
        cwords=normalized_text_words(cand["text"])
        score=10*len(out["matching_financial_event_tags"])+(
            len(qwords&cwords)/max(1,len(qwords|cwords)))
        ranked.append((out["typed_review_candidate"],score,
                       cand["claim_id"],out))
    ranked.sort(key=lambda x:(-int(x[0]),-x[1],x[2]))
    typed=[r for r in ranked if r[0]]
    return {
       "schema":"V32_TYPED_AND_BROAD_SEPARATE_QUEUE_V1",
       "typed_review_candidates":[{
           "claim_id":r[2],
           "shared_event_tags":r[3]["matching_financial_event_tags"],
           "source_risk":r[3]["legacy_verdict_source_risk"],
           "autoapprove":False} for r in typed[:limit]],
       "broad_audit_candidates":[r[2] for r in ranked[:limit]],
       "unknown_event_census":sum(not facets_v32(r["text"]) for r in corpus),
       "all_corpus_claims_accounted_for":len(corpus),
       "unreturned_pairs_may_be_related":True,
       "automatic_knowledge_merge":False,
    }
