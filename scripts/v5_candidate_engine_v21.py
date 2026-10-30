#!/usr/bin/env python3
"""V2.1 investment-claim retrieval: typed propositions and guarded bridges.

Extends the frozen V2 engine without mutating it. Candidate discovery is NOT
financial fact-checking, semantic entailment, or authorization to merge claims.
The independent next-video validation set must not be inspected to tune V2.1.
"""
import re
from functools import lru_cache

from v5_candidate_engine_v2 import retrieve as frozen_v2_retrieve

VERSION="2.1.0"

TAGS={
    # Keep constructs separate: accumulated contribution principal is not
    # an annual taxable pension-distribution ceiling.
    "account_contribution":r"납입한도|연\s*1,800만원|연\s*2,000만원|누적\s*1억원|매년.{0,12}저축",
    "pension_distribution_tax":r"연금소득.{0,12}과세|연금수령.{0,8}과세|연\s*1,500만원|인출.{0,8}과세|과세기준",
    "retirement_account":r"연금저축|연금계좌|퇴직연금|IRP|ISA",
    "retirement_plan":r"은퇴재원|노후준비|은퇴 준비|퇴직.{0,12}현금흐름|은퇴.{0,12}계획|50세부터|55세",
    "retirement_cashflow":r"현금흐름|생활비|수령액|수급|월분배|월배당|분배형|분배금|세후.{0,5}분배",
    "pension_timing":r"연기.{0,5}연금|수령시점|수령 시점|재투자|5년 연기|즉시 수령|언제 쓸 돈",
    "numeric_projection":r"복리|연\s*7\s*%|1\.07\^|1\.07|수익률.{0,10}10년|7\.18\s*%|기간과 잔고|원금.{0,15}만원",
    "numeric_error":r"잘못|불일치|오류|단정은|성립하지|부정확|비보장|보장하지",
    "future_duration":r"10년|12년|5년|3년|7년|장기|만기|35년|수익률|지속",
    "distribution":r"분배|월배당|배당 전환|커버드콜|인출|월.{0,5}만원",
    "distribution_guarantee":r"원금.{0,10}(?:잠식|보장)|지속성|세전|비과세|세금 없이|수익.{0,8}보장|지급액",
    "financial_risk":r"변동성|위험|손실|분산|집중|자산배분|리밸런싱|원금 회복|보장.{0,8}않|보증.{0,8}아니",
    "risk_types":r"가격 변동|영구 손실|신용|유동성|집중|물가 위험|위험수준|자산군",
    "diversification":r"분산|자산배분|주식.{0,8}채권|채권.{0,8}금|섹터.{0,6}집중|단일.{0,8}종목",
    "concentrated":r"집중|한 기업|단일 섹터|인생주식|집중 매수|종목.{0,5}비중",
    "long_horizon":r"장기투자|장기 투자|장기.{0,6}수익|3년.{0,8}짧|시장 사이클|오랫동안",
    "guarantee_limit":r"보장.{0,8}않|보증.{0,8}아니|원금.{0,8}회복|과거.{0,10}성과|수익.{0,8}보장|지속성",
    "discipline":r"투자원칙|매도|앱을 삭제|시세 확인|감정적|투자 포인트|리밸런싱|고점|저점",
    "periodic_rebalance":r"정기 리밸런싱|리밸런싱|매일 시세|주기.{0,5}관리|자산배분",
    "etf":r"ETF|펀드|패시브|액티브",
    "etf_fee":r"보수|운용비용|총비용|거래비용|추적오차|괴리|실현 수익.{0,8}낮",
    "etf_due_diligence":r"투자설명서|기초자산|거래가격|보수|비용|지수.{0,8}확인|ETF.{0,10}비교",
    "fund_management_method":r"전문가가 임의로|운용자 재량|패시브.{0,10}액티브|지수 규칙",
    "portfolio_allocation":r"자산배분|분산투자|위험수준|채권.{0,8}금|주식.{0,8}채권|비중.{0,8}조절",
    "story":r"사례|구독자|회고|역사|경험|고점",
    "investment_principle":r"장기투자|자산배분|저비용|위험 관리|위험관리|지속 가능한|원칙",
}
RX={k:re.compile(v,re.IGNORECASE) for k,v in TAGS.items()}
PERCENT7=re.compile(r"(?<!\d)(?:연\s*)?7\s*%|1\.07(?:\^10)?")
PERCENT6=re.compile(r"(?<!\d)(?:연\s*)?6\s*%")
LARGE_WON=re.compile(r"(?:\d[\d,]*)\s*억|(?:\d[\d,]*)\s*만원")

@lru_cache(maxsize=16384)
def proposition_facets(s):
    return frozenset(k for k,p in RX.items() if p.search(s))

def _cross(la,ra,k1,k2):
    return (k1 in la and k2 in ra) or (k1 in ra and k2 in la)

def retrieve(a_text,b_text,legacy_signals=None,left_verdict=None,right_verdict=None):
    old,detail=frozen_v2_retrieve(a_text,b_text,legacy_signals,
                                  left_verdict,right_verdict)
    fa=proposition_facets(a_text);fb=proposition_facets(b_text)
    common=fa&fb
    bridges=[]
    blocks=[]

    # Scope controls are evaluated BEFORE both legacy and new positive edges.
    # A pension contribution ceiling and a pension-income taxation threshold
    # can coexist in the same retirement account without being the same rule.
    if _cross(fa,fb,"account_contribution","pension_distribution_tax"):
        def pure_contribution(t,tags):
            return ("account_contribution" in tags and
                    "pension_distribution_tax" not in tags and
                    "납입" in t)
        if pure_contribution(a_text,fa) or pure_contribution(b_text,fb):
            blocks.append("contribution_limit_vs_pension_income_tax_threshold")

    # Fund manager discretion versus cross-asset allocation is a distinct
    # axis. But the earlier #2 passive-vs-active discussion also expressly
    # proposed an allocation, so avoid vetoing that separate bridge.
    def pure_manager(t,tags):
        return ("fund_management_method" in tags and
                "portfolio_allocation" not in tags and
                ("전문가가 임의로" in t or "운용자 재량" in t))
    if ((pure_manager(a_text,fa) and "portfolio_allocation" in fb and
         "fund_management_method" not in fb) or
        (pure_manager(b_text,fb) and "portfolio_allocation" in fa and
         "fund_management_method" not in fa)):
        blocks.append("etf_manager_discretion_vs_multiasset_allocation")

    # Structural bridges are explanation codes, not relationship judgments.
    # Retirement planning objective <-> funding and retirement cashflows.
    if _cross(fa,fb,"retirement_plan","retirement_cashflow") and (
        "retirement_account" in fa or "retirement_account" in fb or
        "retirement_plan" in fa&fb):
        bridges.append("retirement_savings_to_decumulation_cashflow")

    # Numeric assumptions are only reviewed together when their model
    # dimensions overlap (annual contributions, compound return or payout).
    if ("numeric_projection" in common and
        ("future_duration" in common or bool(PERCENT7.search(a_text) and PERCENT7.search(b_text)))):
        bridges.append("compound_projection_shared_assumptions")
    if ("numeric_error" in common and
        "future_duration" in common and
        ("numeric_projection" in fa or "numeric_projection" in fb)):
        bridges.append("time_horizon_arithmetic_correction_review")
    if (PERCENT6.search(a_text) and PERCENT6.search(b_text) and
        "distribution" in fa and "distribution" in fb):
        bridges.append("six_percent_distribution_arithmetic")
    if ("distribution" in common and
        ("distribution_guarantee" in fa or "distribution_guarantee" in fb)):
        bridges.append("distribution_yield_vs_capital_sustainability")
    if ("distribution" in common and
        "retirement_cashflow" in (fa|fb) and
        "financial_risk" in (fa|fb)):
        bridges.append("drawdown_income_vs_risk")
    if ("distribution_guarantee" in fa and "distribution" in fb and
        "retirement_cashflow" in fb) or (
        "distribution_guarantee" in fb and "distribution" in fa and
        "retirement_cashflow" in fa):
        bridges.append("payout_guarantee_conditions")
    if ("pension_timing" in fa and "retirement_cashflow" in fb and
        "retirement_plan" in (fa|fb)) or (
        "pension_timing" in fb and "retirement_cashflow" in fa and
        "retirement_plan" in (fa|fb)):
        bridges.append("pension_claiming_time_vs_cashflow")

    # Risk is a family of semantically distinct scopes: only reviewed pairs
    # with identifiable risk types, asset allocation or discipline action.
    if ("financial_risk" in common and
        ("risk_types" in (fa|fb)) and
        ("portfolio_allocation" in (fa|fb) or
         "diversification" in (fa|fb))):
        bridges.append("risk_taxonomy_vs_portfolio_diversification")
    if ("financial_risk" in common and "diversification" in (fa|fb)
        and "concentrated" in (fa|fb)):
        bridges.append("single_name_concentration_vs_diversification")
    if ("concentrated" in fa and "diversification" in fb and
        "financial_risk" in (fa|fb)) or (
        "concentrated" in fb and "diversification" in fa and
        "financial_risk" in (fa|fb)):
        bridges.append("concentration_loss_exposure")
    if ("long_horizon" in fa and "guarantee_limit" in fb and
        "financial_risk" in (fa|fb)) or (
        "long_horizon" in fb and "guarantee_limit" in fa and
        "financial_risk" in (fa|fb)):
        bridges.append("investment_horizon_not_performance_guarantee")
    if ("discipline" in common and
        ("periodic_rebalance" in fa or "periodic_rebalance" in fb)):
        bridges.append("trade_discipline_vs_portfolio_rebalancing")
    if ("discipline" in fa and "guarantee_limit" in fb and
        "financial_risk" in (fa|fb)) or (
        "discipline" in fb and "guarantee_limit" in fa and
        "financial_risk" in (fa|fb)):
        bridges.append("hold_unconditionally_vs_drawdown_risk")
    if ("investment_principle" in fa and "financial_risk" in fb and
        "retirement_plan" in fb) or (
        "investment_principle" in fb and "financial_risk" in fa and
        "retirement_plan" in fa):
        bridges.append("allocation_risk_principle_for_retirement")
    if ("investment_principle" in common and
        "retirement_cashflow" in (fa|fb) and
        "financial_risk" in (fa|fb)):
        bridges.append("sustainable_cashflow_risk_principle")
    if ("etf" in common and
        ("etf_fee" in fa and "etf_due_diligence" in fb or
         "etf_fee" in fb and "etf_due_diligence" in fa)):
        bridges.append("etf_fee_vs_investor_cost_disclosure")

    # No positive "support" relation may be assigned here, even when the
    # source prose is the corrected explanation of a contradicted video quote.
    result=bool(old or bridges) and not blocks
    d=dict(detail)
    d.update({
       "engine_version":VERSION,"review_only":True,
       "correction_only":left_verdict=="CONTRADICTED" or
                         right_verdict=="CONTRADICTED",
       "v21_proposition_left":sorted(fa),
       "v21_proposition_right":sorted(fb),
       "v21_bridges":sorted(set(bridges)),
       "v21_scope_blocks":sorted(set(blocks)),
       "v21_raw_v2_candidate":bool(old),
       "automatic_knowledge_approval":False,
       "semantic_relation_prediction":None,
    })
    return result,d
