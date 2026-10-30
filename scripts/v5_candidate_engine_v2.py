#!/usr/bin/env python3
"""V2: deterministic, inspectable claim-level relation candidate retrieval.

Purpose: find pairs requiring semantic/financial review. It DOES NOT assign
SUPPORT/QUALIFY, verify tax law, or approve/promote investment knowledge.
The V2 ontology is intentionally small and broad; ambiguity is flagged.
Designed against diagnostic misses in #1-#12, not a validated universal model.
"""
import re
from functools import lru_cache

# Facets represent different aspects of a proposition; product mention alone
# must not be regarded as a verified relationship.
FACETS={
 "isa":r"ISA",
 "isa_benefit":r"서민형.{0,16}비과세|일반형.{0,16}비과세|의무기간.{0,12}재가입|ISA.{0,20}만기|비과세.{0,14}재가입",
 "private_pension":r"연금저축|연금계좌|연금보험|연금수령|IRP|퇴직연금",
 "national_pension":r"국민연금|추납|연기연금",
 "child":r"자녀|미성년|출생|태어난|갓 태어난",
 "child_finance":r"자녀.{0,22}(?:계좌|증여|투자|적립|주식)|미성년.{0,20}(?:투자|연금|증여)|(?:증여|주식).{0,15}자녀",
 "gift":r"증여|증여세|유기정기금",
 "periodic_buy":r"적립식|정기.{0,7}매수|분할.{0,8}(?:투자|매수)|정액 적립|월별 정기",
 "liquidity":r"CMA|파킹형|보통예금|현금성|유동성|단기 현금",
 "equity_index":r"S&P\s*500|KOSPI\s*200|나스닥|대표지수|주가지수|미국지수|해외지수|지수\s*추종|미국 대형주|패시브|추종지수|지수\s*구성|지수\s*편입|시가총액",
 "equity_index_method":r"시가총액|방법론|편입|가중치|구성기업|추종지수|선도 기업|패시브|액티브",
 "etf":r"ETF",
 "equity_risk":r"자산배분|분산|주식.{0,8}집중|집중투자|위험수준|투자위험|환율위험|위험.{0,6}분산",
 "market_risk":r"손실|위험|추적오차|보장하지|보증이 아니|과거.{0,9}성과|미래.{0,8}보증",
 "etf_cost":r"보수|추적오차|괴리|거래비용|거래가격|기초자산|투자설명서|상장|계좌.{0,8}매수|허용상품",
 "fx":r"엔화|원엔|달러엔|환율|환전|환헤지|환노출|외국.{0,5}원천세",
 "fx_hedge":r"환헤지|환노출|원엔|달러엔|환율위험|환율.{0,8}차이",
 "tax":r"과세|세액공제|소득공제|연말정산|비과세|세금|공제",
 "pension_tax":r"연금.{0,12}(?:세금|과세|공제|이연)|(?:세금|과세|공제|이연).{0,12}연금|미공제|과세제외",
 "retire":r"퇴직|은퇴|노후|노년",
 "cashflow":r"현금흐름|생활비|연금.{0,6}수령|퇴직급여|퇴직금|지출능력|수급",
 "life_goal":r"노후.{0,15}(?:꿈|목표|하고 싶은|준비의 목적)|은퇴 후.{0,35}(?:여행|주택|박물관|목표)|은퇴생활.{0,12}목표",
 "life_interest":r"취미|마라톤|박물관|책방|기부|테마여행|음악 활동|건강.{0,8}독립",
 "risk_discipline":r"매도|고점|저점|손실 자산|투자 포인트|투자 논리|감정.{0,8}거래",
 "performance_story":r"개인 사례|개인.{0,8}성공|구독자.{0,18}(?:자산|수입|사례)|성공 회고|자산 규모가 증가",
 "return_quality":r"과거.{0,12}성과|미래.{0,8}보증|추적오차|세후수익|투자수익률|운용수익",
 "account_limit":r"계좌개설|개설|가능.{0,4}계좌|허용상품|매수 가능|거래단위|1주|주당|가격",
 "insurance_contract":r"보험|해약|해지|보증이율|최저보증|환급금",
 "payout":r"월분배|분배금|분배형|세전 분배|월.{0,4}만원.{0,8}분배",
 "tax_principal":r"과세제외|공제.{0,8}원금|미공제|비과세 인출|장기간 세금 없이|전액.{0,8}세금 없이",
 "tax_education":r"연말정산|세액공제|소득공제",
 "benefit_timing":r"수령 시점|언제 쓸 돈|즉시 수령|연기 후|퇴직급여 수령|퇴직금.{0,8}언제",
 "yen":r"엔화|원엔|달러엔|엔투자",
 "fx_timing":r"바닥|저점|더 약세|약세.{0,5}이어|분할매수|환율.{0,8}예측",
 "yen_route":r"(?:방법\s*[1-5]|다섯 경로)|엔화.{0,18}(?:매수|구매|주식)|원화로.{0,15}엔화",
 "lifecycle":r"생애주기|은퇴 시점|은퇴 가정|장기 납입|적립식 투자|TDF",
 "asset_mix":r"주식.{0,6}채권|채권.{0,6}금|자산배분|ETF.{0,8}(?:금|채권)|분산투자",
}
FACET_PATTERNS={name:re.compile(expr,re.IGNORECASE) for name,expr in FACETS.items()}

@lru_cache(maxsize=16384)
def facets(text):
    return frozenset(k for k,p in FACET_PATTERNS.items() if p.search(text))

def explanatory_blocks(a,b,fa,fb):
    """Different proposition scopes that must not be merged by broad topic."""
    veto=[]
    def cross(x,y,u,v):return (x in u and y in v) or (y in u and x in v)
    # Personal aspirations / nonfinancial anecdotes are not proof of financial
    # instruments, returns, taxation or early-retirement economic decisions.
    if cross("life_interest","cashflow",fa,fb):
        interest=a if "life_interest" in fa else b
        if not ("life_goal" in facets(interest) and re.search(r"단독주택|주거|생활비",interest)):
            veto.append("lifestyle_aspiration_vs_cashflow_fact")
    if cross("life_interest","market_risk",fa,fb) or cross("life_interest","equity_risk",fa,fb):
        if not (("child_finance" in fa) or ("child_finance" in fb)):
            veto.append("lifestyle_vs_investment_risk")
    if ("life_goal" in fa and "life_goal" not in fb and re.search(r"FIRE|조기은퇴",b)) or (
        "life_goal" in fb and "life_goal" not in fa and re.search(r"FIRE|조기은퇴",a)):
        veto.append("retirement_aspiration_vs_fire_career")
    if cross("gift","pension_tax",fa,fb) and not ("child_finance" in fa and "child_finance" in fb):
        veto.append("gift_tax_vs_pension_tax")
    if cross("performance_story","return_quality",fa,fb):
        if ("equity_index" in fa or "equity_index" in fb) and not ("equity_index" in fa and "equity_index" in fb):
            veto.append("individual_anecdote_vs_index_returns")
    if ("life_goal" in fa and "cashflow" not in fa and "cashflow" not in fb) or (
        "life_goal" in fb and "cashflow" not in fa and "cashflow" not in fb):
        # Goal vs different lifestyle preference, without financial planning.
        if ("life_interest" in fa or "life_interest" in fb):
            veto.append("different_lifestyle_aspirations")
    # Budget choices, account tax rules and active investment gains do not
    # establish one another. Preserve explicit source-level explanations.
    def budget(x):return bool(re.search(r"월\s*[\d,]+\s*만원",x) and "배분" in x and "저축" in x)
    if (budget(a) and "tax" in fb and "tax" not in fa) or (budget(b) and "tax" in fa and "tax" not in fb):
        veto.append("budget_allocation_vs_tax_rule")
    if (("periodic_buy" in fa and "retire" in fb and "cashflow" in fb and "child_finance" in fa)
        or ("periodic_buy" in fb and "retire" in fa and "cashflow" in fa and "child_finance" in fb)):
        veto.append("child_accumulation_vs_retiree_lump_sum")
    if (("private_pension" in fa and re.search(r"보험.{0,6}보증|보증이율|오래된 보험",a) and "child_finance" in fb)
        or ("private_pension" in fb and re.search(r"보험.{0,6}보증|보증이율|오래된 보험",b) and "child_finance" in fa)):
        veto.append("historic_insurance_contract_vs_minor_savings")
    # Minor account strategies are not the same proposition as a general
    # first-salary hypothetical budget allocation.
    if (("child_finance" in fa and re.search(r"월\\s*100만원|청년 저축",b))
        or ("child_finance" in fb and re.search(r"월\\s*100만원|청년 저축",a))):
        veto.append("minor_retirement_account_vs_first_salary_budget")
    # Index construction methodology and the mechanics of portfolio
    # allocation address different propositions even if both mention equities.
    if (("equity_index_method" in fa and "equity_risk" not in fa
         and not re.search(r"패시브|액티브",a)
         and "asset_mix" in fb and "equity_index_method" not in fb
         and "equity_index" not in fb)
        or ("equity_index_method" in fb and "equity_risk" not in fb
         and not re.search(r"패시브|액티브",b)
         and "asset_mix" in fa and "equity_index_method" not in fa
         and "equity_index" not in fa)):
        veto.append("index_constituents_vs_multiasset_allocation")
    if ("etf" in fa and "etf" in fb and
        ("fx" in fa) != ("fx" in fb) and
        ("etf_cost" in fa) != ("etf_cost" in fb)):
        # Keep scope-distinct cost/FX edges eligible only if an index/asset
        # exposure bridge below is supported.
        pass
    # Specific negative scopes documented in the earlier #1-#10 baseline:
    def bond_etf(t):return bool(re.search(r"(국채|채권).{0,10}ETF|ETF.{0,10}(국채|채권)",t))
    def spread(t):return "환전" in t and "스프레드" in t
    if bond_etf(a) and spread(b) or bond_etf(b) and spread(a):
        veto.append("bond_etf_vs_conversion_spread")
    if (("risk_discipline" in fa and "performance_story" in fb and "risk_discipline" not in fb)
        or ("risk_discipline" in fb and "performance_story" in fa and "risk_discipline" not in fa)):
        veto.append("sale_discipline_vs_success_anecdote")
    if (("national_pension" in fa and "national_pension" not in fb and "복리" in b and "기간과 잔고" in b)
        or ("national_pension" in fb and "national_pension" not in fa and "복리" in a and "기간과 잔고" in a)):
        veto.append("accumulation_arithmetic_vs_pension_deferral")
    return sorted(set(veto))

def retrieve(a_text,b_text,legacy_signals=None,left_verdict=None,right_verdict=None):
    """Return only whether a pair deserves human semantic review plus explainability.

    legacy_signals are for diagnostics only: same-video/topic/old V5 video edge
    cannot by themselves create a candidate. No approval semantics are returned.
    """
    fa=facets(a_text);fb=facets(b_text)
    shared=fa&fb
    veto=explanatory_blocks(a_text,b_text,fa,fb)
    evidence=[]
    # Shared *concrete* instruments, tax regimes, investment actions or
    # reference index; 'retire'/'etf'/'tax' alone are intentionally too broad.
    concrete={
      "isa","national_pension","pension_tax","equity_index","fx_hedge",
      "benefit_timing",
      "insurance_contract","payout","tax_principal",
      "child_finance","risk_discipline","periodic_buy",
      "liquidity","equity_index_method","return_quality","account_limit",
    }
    strong=shared & concrete
    if strong:
        evidence.extend("direct:"+x for x in sorted(strong))
    if ("isa_benefit" in fa and "isa" in fb) or ("isa_benefit" in fb and "isa" in fa):
        evidence.append("isa_tax_benefit_vs_maturity_planning")
    if "fx_timing" in shared and "fx" in shared:
        evidence.append("fx_market_timing_uncertainty")
    if "tax_education" in fa and "tax" in fb and "private_pension" in fb:
        evidence.append("pension_tax_explanation_to_year_end_tax")
    if "tax_education" in fb and "tax" in fa and "private_pension" in fa:
        evidence.append("pension_tax_explanation_to_year_end_tax")
    if "etf" in shared and "account_limit" in fa and "periodic_buy" in fb:
        evidence.append("etf_minimum_lot_vs_accumulation")
    if "etf" in shared and "account_limit" in fb and "periodic_buy" in fa:
        evidence.append("etf_minimum_lot_vs_accumulation")
    if "retire" in shared and "cashflow" in fa and "benefit_timing" in fb:
        evidence.append("retirement_cashflow_vs_benefit_claim_timing")
    if "retire" in shared and "cashflow" in fb and "benefit_timing" in fa:
        evidence.append("retirement_cashflow_vs_benefit_claim_timing")
    if "lifecycle" in fa and "periodic_buy" in fb and "etf" in fb:
        evidence.append("lifecycle_fund_horizon_vs_periodic_investing")
    if "lifecycle" in fb and "periodic_buy" in fa and "etf" in fa:
        evidence.append("lifecycle_fund_horizon_vs_periodic_investing")
    if "yen" in shared and "fx_timing" in fa and "fx_timing" in fb:
        evidence.append("yen_market_timing_uncertainty")
    if "yen" in shared and "yen_route" in fa and "yen_route" in fb:
        evidence.append("yen_investment_implementation_routes")
    if "private_pension" in shared:
        if "tax" in fa and "tax" in fb: evidence.append("pension_account_tax_link")
        if "child_finance" in fa and ("child_finance" in fb or "retire" not in fb):
            evidence.append("minor_pension_account_scope")
        if "child_finance" in fb and ("child_finance" in fa or "retire" not in fa):
            evidence.append("minor_pension_account_scope")
    if "tax_principal" in fa and "tax" in fb and "payout" in fb:
        evidence.append("tax_exempt_principal_vs_distribution")
    if "tax_principal" in fb and "tax" in fa and "payout" in fa:
        evidence.append("tax_exempt_principal_vs_distribution")
    if "payout" in fa and "payout" in fb:
        evidence.append("distribution_income_vs_tax_scope")
    if "fx" in shared and ("etf" in shared or "fx_hedge" in fa or "fx_hedge" in fb):
        evidence.append("shared_currency_exposure")
    if "child_finance" in fa and "child_finance" in fb and (
        "gift" in fa or "gift" in fb or "etf" in fa or "etf" in fb):
        evidence.append("child_wealth_lifecycle_bridge")
    if "child_finance" in fa and "gift" in fb and "child" in fb and "tax" not in fb:
        evidence.append("child_contribution_vs_gift_funding")
    if "child_finance" in fb and "gift" in fa and "child" in fa and "tax" not in fa:
        evidence.append("child_contribution_vs_gift_funding")
    if "life_goal" in fa and "cashflow" in fb and "retire" in fb:
        evidence.append("retirement_goal_to_spending_plan")
    if "life_goal" in fb and "cashflow" in fa and "retire" in fa:
        evidence.append("retirement_goal_to_spending_plan")
    if "child_finance" in fa and "private_pension" in fa and "private_pension" in fb and "tax" not in fb:
        evidence.append("minor_vs_general_pension_savings")
    if "child_finance" in fb and "private_pension" in fb and "private_pension" in fa and "tax" not in fa:
        evidence.append("minor_vs_general_pension_savings")
    if "child_finance" in fa and "private_pension" in fa and "private_pension" in fb and "tax" in fb:
        evidence.append("minor_savings_vs_pension_tax_conditions")
    if "child_finance" in fb and "private_pension" in fb and "private_pension" in fa and "tax" in fa:
        evidence.append("minor_savings_vs_pension_tax_conditions")
    # S&P500 as a specific index is an index-family ETF even when another
    # speaker calls it '대표지수 ETF' or '미국주가지수 ETF'.
    if "equity_index" in fa and "etf" in fa and "etf" in fb and (
        "equity_index" in fb or re.search(r"대표지수|미국",b_text)):
        evidence.append("index_etf_same_asset_family")
    if "equity_index" in fb and "etf" in fb and "etf" in fa and (
        "equity_index" in fa or re.search(r"대표지수|미국",a_text)):
        evidence.append("index_etf_same_asset_family")
    if "equity_index" in fa and "equity_risk" in fb and "etf" in fb:
        evidence.append("index_exposure_vs_diversification")
    if "equity_index" in fb and "equity_risk" in fa and "etf" in fa:
        evidence.append("index_exposure_vs_diversification")
    if "equity_index" in fa and "equity_index_method" in fb:
        evidence.append("index_construction_vs_passive")
    if "equity_index" in fb and "equity_index_method" in fa:
        evidence.append("index_construction_vs_passive")
    if "equity_index_method" in fa and "equity_index_method" in fb:
        evidence.append("index_methodology_scope")
    if "equity_risk" in fa and "equity_risk" in fb and "etf" in shared:
        evidence.append("diversification_residual_risk")
    if "etf_cost" in fa and "etf" in fa and "etf" in fb and (
        "equity_index" in fb or "etf_cost" in fb):
        evidence.append("etf_vehicle_cost_and_scope")
    if "etf_cost" in fb and "etf" in fb and "etf" in fa and (
        "equity_index" in fa or "etf_cost" in fa):
        evidence.append("etf_vehicle_cost_and_scope")
    if "return_quality" in fa and "etf" in fa and "etf" in fb and (
        "tax" in fb or "equity_index" in fb or "fx_hedge" in fb):
        evidence.append("etf_return_vs_tax_fees_fx")
    if "return_quality" in fb and "etf" in fb and "etf" in fa and (
        "tax" in fa or "equity_index" in fa or "fx_hedge" in fa):
        evidence.append("etf_return_vs_tax_fees_fx")
    if "fx_hedge" in fa and "fx" in fb and ("etf" in fa or "etf" in fb):
        evidence.append("fx_asset_currency_conversion")
    if "fx_hedge" in fb and "fx" in fa and ("etf" in fa or "etf" in fb):
        evidence.append("fx_asset_currency_conversion")
    if "cashflow" in fa and "national_pension" in fb and "retire" in fb:
        evidence.append("national_pension_retirement_income")
    if "cashflow" in fb and "national_pension" in fa and "retire" in fa:
        evidence.append("national_pension_retirement_income")
    if "etf" in shared and "periodic_buy" in fa and "periodic_buy" in fb:
        evidence.append("same_etf_accumulation_action")
    if "asset_mix" in fa and "asset_mix" in fb:
        evidence.append("allocation_risk_context")
    # Very broad shared keyword contexts are never sufficient.
    # Guard against 'healthy retirement / future dreams' vs specific legal
    # claims where retirement is an incidental umbrella concept.
    if veto:
        return False,{
          "v2_version":"2.0.0","facets_left":sorted(fa),
          "facets_right":sorted(fb),"evidence":sorted(set(evidence)),
          "scope_blocks":veto,"review_only":True,
          "correction_only":left_verdict=="CONTRADICTED" or right_verdict=="CONTRADICTED",
          "legacy_was_candidate":bool(legacy_signals and any(legacy_signals.values()))
        }
    return bool(evidence),{
        "v2_version":"2.0.0","facets_left":sorted(fa),
        "facets_right":sorted(fb),"evidence":sorted(set(evidence)),
        "scope_blocks":[],"review_only":True,
        "correction_only":left_verdict=="CONTRADICTED" or right_verdict=="CONTRADICTED",
        "legacy_was_candidate":bool(legacy_signals and any(legacy_signals.values()))
    }
