#!/usr/bin/env python3
"""V3.1 typed-financial retrieval sidecar (V3.0/V2.3 remain immutable).

Two separate outputs:
  * broad_recall: audit queue, not a relatedness judgment;
  * typed_review: candidate only after interpretable financial-event overlap.

All extracted tags are PROVISIONAL lexical features, never independently
verified economic claim metadata. Unknown evidence remains BLOCKED.
"""
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from v30_verified_core import guard,VERDICTS,CLAIM_RE,sha256,canonical

# General financial event definitions, not identifiers of historical labels.
# Keep concrete legal bases and flows separate to prevent homonym collisions.
PATTERNS={
 "NATIONAL_PENSION_DEFERRAL":r"연기연금|국민연금.*연기|연기.*국민연금|연금수령.*연기",
 "NATIONAL_PENSION_BUYBACK":r"추납|추후납부",
 "PENSION_WITHDRAWAL_TAX":r"연금소득|과세제외|연금.*인출|사적연금.*과세|연금.*과세재원|연금.*세금|과세.*원금|연금수령한도|과세제외.*인출",
 "PENSION_CONTRIBUTION_CREDIT":r"세액공제|연금저축.*적립|연금저축.*납입|IRP.*납입|연금계좌.*적립",
 "ISA_ACCOUNT_RULE":r"\bISA\b|중개형 ISA|개인종합자산관리계좌",
 "ISA_MATURITY":r"\bISA\b.{0,18}(?:만기|의무기간|해지|재가입)|(?:만기|의무기간|해지).{0,18}\bISA\b",
 "BOND_MATURITY":r"(?:채권|국채).{0,25}(?:만기|원금|상환)|(?:만기|상환).{0,18}(?:채권|국채)",
 "CENTRAL_BANK_POLICY_RATE":r"한국은행.*기준금리|기준금리.*한국은행|통화정책.*금리|중앙은행.*금리",
 "SHORT_TERM_CASH_PARKING":r"파킹형|파킹 ETF|CMA|단기자금|단기 현금|유동성 관리",
 "FINANCIAL_DEPOSIT_PROTECTION":r"예금자보호|원금보장|발행어음|RP형|MMW형",
 "DIVIDEND_AND_DISTRIBUTION":r"분배금|분배율|월분배|배당|커버드콜",
 "INSURANCE_CONTRACT":r"연금저축보험|보험.*(?:계약|해지|해약|보증)|(?:해지|해약).*보험|최저보증이율",
 "RETIREMENT_CASHFLOW":r"은퇴.*(?:생활비|현금흐름|연금|수급)|퇴직.*(?:생활비|현금흐름|연금)|연금.*(?:생활비|현금흐름)|은퇴자.*(?:분배|현금)|노후.*생활비",
 "RETIREMENT_LUMP_SUM_ALLOCATION":r"퇴직금.*(?:분할|투자|파킹|운용)|퇴직.*목돈|분할투자.*퇴직",
 "ETF_ACCUMULATION":r"ETF.*(?:적립|정기|분할)|(?:적립식|정기적).{0,20}(?:ETF|지수)|(?:ETF|지수).*분할투자",
 "EQUITY_SINGLE_COMPANY":r"주식|개별주|반도체.*(?:기업|대형주)|(?:회사|기업).*종목|종목.*(?:기업|투자|매수)",
 "EQUITY_LOSS_DECISION":r"손실.*(?:매도|종목|계좌|투자|주식)|(?:매도|고점|저점).*종목|감정적.*거래|매수.*가설|매도.*판단|투자 포인트",
 "INVESTMENT_RISK_ALLOCATION":r"자산배분|리밸런싱|포트폴리오|패시브|액티브|위험.*(?:분산|관리)",
 "YOUTH_FINANCIAL_ACCOUNTS":r"사회초년생|취업.*(?:계좌|재무)|신입.*재무|청년.*(?:저축|계좌)|목적별.*계좌",
 "HOUSEHOLD_SPENDING":r"생활비.*(?:지출|소비|예산)|지출.*(?:관리|조정|항목|계획|통제)|소비.*(?:관리|조정|통제|지출)|신용카드|할부|과소비|월급.*(?:지출|저축|소비)|첫.{0,6}개월.*월급",
 "HOUSING_DOWNSIZE":r"다운사이징|주택.*(?:축소|매각|현금화)",
 "GOLD_SPOT_ACCOUNT":r"금현물|금 현물|금 거래소|KRX 금",
 "LABOUR_TAX_REPORTING":r"연말정산|근로소득.*(?:소득공제|세액공제)",
 "TARGET_DATE_FUND":r"\bTDF\b|타깃데이트|타겟데이트",
 "FOREX":r"환율|환전|외화|엔화|달러.*환차익",
 "COMPOUND_SAVINGS_MODEL":r"복리.*(?:적립|운용)|(?:연|실효).{0,6}\d+(?:\.\d+)?%.*(?:적립|복리)|적립.{0,15}년.*(?:수익|만원)",
}
COMPILED={k:re.compile(p,re.I) for k,p in PATTERNS.items()}
# A broad umbrella ('pension', 'tax', 'percent', 'maturity') is never an
# automatically sufficient link. These are deliberately concrete events.
INCOMPATIBLE=frozenset({
 frozenset(("ISA_MATURITY","BOND_MATURITY")),
 frozenset(("CENTRAL_BANK_POLICY_RATE","DIVIDEND_AND_DISTRIBUTION")),
 frozenset(("CENTRAL_BANK_POLICY_RATE","SHORT_TERM_CASH_PARKING")),
 frozenset(("PENSION_WITHDRAWAL_TAX","PENSION_CONTRIBUTION_CREDIT")),
 frozenset(("LABOUR_TAX_REPORTING","GOLD_SPOT_ACCOUNT")),
 frozenset(("YOUTH_FINANCIAL_ACCOUNTS","RETIREMENT_LUMP_SUM_ALLOCATION")),
})
GUARD_SPEC="V31_FINANCIAL_EVENT_TYPES_V1"
def derive_facets(text):
    guard(isinstance(text,str) and 0<len(text.strip())<=16000,
          "NONEMPTY_FINANCIAL_CLAIM_TEXT_REQUIRED")
    tags={k for k,r in COMPILED.items() if r.search(text)}
    # Rule-level priority means a withdrawal tax phrase mentioning past tax
    # credits does not become a contribution-tax-candidate automatically.
    if "PENSION_WITHDRAWAL_TAX" in tags and "PENSION_CONTRIBUTION_CREDIT" in tags:
        if re.search(r"세액공제\s*받은|공제받지\s*않은|공제받은\s*원금",text):
            tags.discard("PENSION_CONTRIBUTION_CREDIT")
    if "CENTRAL_BANK_POLICY_RATE" in tags:
        tags.discard("SHORT_TERM_CASH_PARKING")
    return frozenset(sorted(tags))

def pair_review(a,b):
    """Review relevance, not truth/entailment/support. Provisional ontology."""
    for r in (a,b):
        guard(type(r) is dict and r.get("legacy_verdict") in VERDICTS
              and isinstance(r.get("claim_id"),str)
              and CLAIM_RE.fullmatch(r["claim_id"]) and
              isinstance(r.get("text"),str) and r["text"].strip(),
              "SOURCE_CLAIM_REQUIRED_FOR_TYPED_RETRIEVAL")
    guard(a["claim_id"]!=b["claim_id"],"CANNOT_RETRIEVE_SELF_PAIR")
    ta=derive_facets(a["text"]);tb=derive_facets(b["text"])
    shared=sorted(ta&tb)
    pair_risk=("CORRECTION_ONLY"
               if "CONTRADICTED" in (a["legacy_verdict"],b["legacy_verdict"])
               else "UNREPLICATED_HYPOTHETICAL_SOURCE"
               if "HYPOTHETICAL" in (a["legacy_verdict"],b["legacy_verdict"])
               else "HUMAN_REVIEW_ONLY")
    # Distinct financial flows are intentionally not the same proposition;
    # reviewers may still discover cross-domain dependencies in broad audit.
    blocked=[]
    for kind in INCOMPATIBLE:
        left,right=tuple(kind)
        if (left in ta and right in tb) or (right in ta and left in tb):
            if not shared:
                blocked.append("+".join(sorted(kind)))
    typed=bool(shared) and not blocked
    return {
      "schema":"V31_TYPED_REVIEW_PAIR_V1",
      "left_claim_id":a["claim_id"],"right_claim_id":b["claim_id"],
      "financial_facets_left":sorted(ta),"financial_facets_right":sorted(tb),
      "shared_financial_events":shared,
      "conflicting_cross_scope_types":sorted(blocked),
      "typed_review_candidate":typed,
      "provisional_source_role_only":True,
      "source_risk":pair_risk,
      "relation":"REVIEW_CANDIDATE_NOT_FACT",
      "approved_semantic_relation":False,
      "automatic_knowledge_merge":False,
      "research_completion_certificate_permitted":False,
      "personal_investment_advice_permitted":False,
    }

def normalized_text_words(text):
    return set(re.findall(r"[A-Za-z가-힣]{2,}",text.lower()))

def make_v31_index(records):
    guard(type(records) is list and records,"EXPLICIT_NONEMPTY_CORPUS_REQUIRED")
    out=[];seen=set()
    for r in records:
        guard(type(r) is dict and
              type(r.get("video_number")) is int and
              1<=r["video_number"]<=20 and
              r.get("claim_id") not in seen,
              "POST20_OR_DUPLICATE_DEVELOPMENT_CORPUS_BLOCKED")
        seen.add(r["claim_id"])
        # An optional fully audited role must not be silently overwritten by
        # heuristics. The derived facets are provisional search metadata.
        if r.get("financial_role") is not None:
            guard(r.get("financial_role_review_state")=="EXTERNALLY_REVIEWED",
                  "UNREVIEWED_FINANCIAL_ROLE_INJECTION_BLOCKED")
        item={k:r[k] for k in ("claim_id","video_number","text",
                               "legacy_verdict")}
        facets=derive_facets(item["text"])
        item["provisional_financial_facets"]=sorted(facets)
        item["facets_review_state"]="UNREVIEWED_RULE_BASED"
        item["financial_role"]=r.get("financial_role")
        pair_review(item,{**item,"claim_id":"REVIEWTEST1-99"}) if False else None
        guard(item["legacy_verdict"] in VERDICTS and
              CLAIM_RE.fullmatch(item["claim_id"]),
              "MALFORMED_HISTORY_CLAIM")
        out.append(item)
    return tuple(sorted(out,key=lambda x:x["claim_id"]))

def search_v31(query,corpus,top_k=10,noncandidate_audit=10):
    guard(type(query) is dict and query.get("claim_id") and
          type(corpus) in (list,tuple) and
          type(top_k) is int and 1<=top_k<=100,
          "V31_SEARCH_INPUT_INVALID")
    ranked=[]
    queryfac=derive_facets(query["text"])
    words=normalized_text_words(query["text"])
    for candidate in corpus:
        if candidate["claim_id"]==query["claim_id"]:continue
        out=pair_review(query,candidate)
        words2=normalized_text_words(candidate["text"])
        common=words&words2
        # Lexical evidence can rank within a type but cannot create the link.
        lexical=len(common)/max(1,len(words|words2))
        tagcount=len(out["shared_financial_events"])
        score=round(tagcount*10+lexical,6)
        ranked.append((int(out["typed_review_candidate"]),score,
                       candidate["claim_id"],out))
    ranked.sort(key=lambda x:(-x[0],-x[1],x[2]))
    typed=[x for x in ranked if x[0]]
    unknown=[x for x in ranked if not x[0]]
    # Broad queue retains unmatched candidates for human recall/noncandidate
    # audits. It is explicitly NOT counted as confirmed relevance.
    broad=(typed+unknown)[:top_k]
    typed_hits=typed[:top_k]
    rest=[x[2] for x in ranked if x[2] not in {e[2] for e in broad}]
    rest.sort(key=lambda cid:hashlib.sha256((query["claim_id"]+"|"+cid).encode()).hexdigest())
    def thin(x):return {
        "claim_id":x[2],"score":x[1],
        "shared_financial_events":x[3]["shared_financial_events"],
        "source_risk":x[3]["source_risk"],
        "typed_review_candidate":bool(x[0]),
        "automatically_approved":False}
    return {
       "schema":"V31_SEPARATED_BROAD_AND_TYPED_REVIEW_V1",
       "query_claim_id":query["claim_id"],
       "financial_role_annotation_coverage":sum(
            r.get("financial_role") is not None for r in corpus),
       "rule_based_facets_unreviewed":True,
       "broad_recall_queue":[thin(x) for x in broad],
       "typed_review_queue":[thin(x) for x in typed_hits],
       "noncandidate_audit_sample":rest[:noncandidate_audit],
       "all_pairs_financially_related_certified":False,
       "source_is_separate_from_semantic_similarity":True,
       "relation_auto_approval":False,
       "review_burden_unrestricted_broad_queue":len(broad),
       "review_burden_typed_queue":len(typed_hits),
       "development_input_max_video":20,
    }

def development_from_original_history(root,roster):
    """Read historical V3 claims, never #21+ or private SRT."""
    from v30_hybrid_search import build_development_history
    source=build_development_history(root,roster)
    items=[{k:r[k] for k in ("claim_id","video_number","text","legacy_verdict")}
           for r in source]
    return make_v31_index(items)
