#!/usr/bin/env python3
"""V2.2 candidate discovery via auditable typed financial propositions.

Frozen historical V2/V2.1 are imported read-only; this engine is additive.
This is a recall-oriented candidate *retriever*, never an entailment judge,
source fact-checker, merger, investment adviser, or knowledge approver.

New #15/#16 failures are development cases; #17+ must remain unseen until
the V2.2 source and diagnostics have been frozen in Git.
"""
import re
from functools import lru_cache
from v5_candidate_engine_v21 import retrieve as frozen_v21_retrieve

VERSION="2.2.0"

# Distinguish proposition dimensions rather than equating product labels.
# These ontology concepts intentionally describe a financial question for
# human review; no authoritative finance facts are inferred by matching them.
CONCEPTS={
 "history_vs_future":r"과거.{0,12}(?:수익|성과|회복)|미래.{0,12}(?:보장|보증)|역사적.{0,12}(?:수익|낙폭)|장기.{0,14}(?:수익|침체|횡보|회복)|실제.{0,9}(?:수익|보유)|손실.{0,5}확률|수익.{0,5}보장|원금 회복",
 "return_measure":r"평균.{0,5}수익|연평균|실현수익|보유기간.{0,5}수익|수익률|총수익|성과|배당 재투자|복리|배당재투자|연\s*7\s*%|분배율",
 "backtest_model":r"백테스트|지수.{0,12}(?:성과|수익률)|1972.{0,8}2022|월별 수익률|역사적.{0,9}최대낙폭|모형.{0,12}수익|가상.{0,9}수익|성과표",
 "return_provenance":r"실제 ETF|실제.{0,9}보유|실현수익|기대.{0,7}수익|세금|비용|추적오차|환율.{0,4}차이|시작.종료시점|배당 재투자|수익률.*가정",
 "long_horizon":r"장기|오래 보유|5.10년|10년|20년|25년|보유기간|침체|회복기간|수익률.{0,6}기간|시장 사이클",
 "drawdown":r"폭락|대폭락|급락|낙폭|하락장|장기.{0,4}침체|장기.{0,4}횡보|회복기간|원금 회복|평가손실|손실 자산",
 "volatility":r"변동성|가격 변동|표준편차|낙폭|위험률|가격위험|상관",
 "investor_behavior":r"조기매도|급히 파|급락장|하락장에서.{0,10}매도|감정적 거래|매도하지|앱을 삭제|보유를 포기|시세 확인|정기 리밸런싱|리밸런싱|매수.{0,8}매도",
 "liquidity_buffer":r"현금유동성|현금성|파킹형|분할투자|분할매수|필수지출|지출 분리|여유자금",
 "asset_allocation":r"자산배분|자산군|채권.{0,8}금|금.{0,8}채권|주식.{0,12}채권|비중|리스크 패리티|포트폴리오|분산투자|위험 기여도|구성 실험",
 "portfolio_weights":r"\d+\s*[%％].{0,10}(?:금|채권|주식|원자재)|\d+\s*:\s*\d+|6\s*[:：]\s*4|리스크 패리티|위험 기여도|원금 비중|구성 비율|중간 구성|주식.{0,8}금|주식.{0,12}채권",
 "multiasset_exposure":r"미국주식|주식|장기국채|국채|(?<![가-힣])금(?![가-힣])|원자재|채권|자산군|달러|현금성|일본주식",
 "macro_regime":r"올웨더|거시환경|경기.{0,8}물가|성장률|인플레이션|경제환경|경제상황|경기 국면|경기.물가",
 "risk_management":r"위험 관리|위험관리|위험수준|분산|손실|포트폴리오.{0,12}위험|심리적 안정|안정적|안정성|주식.{0,8}위험|주가 변동",
 "risk_correlation":r"상관|동반 하락|비상관|분산 효과|서로 다른.{0,5}자산|종목.{0,7}겹|중복|편입종목",
 "security_overlap":r"겹치|중복|같은 종목|종목 비중|섹터|단일 종목|상위 시총|편입종목",
 "concentration":r"집중|한 자산군|단일 시장|단일 종목|단일 섹터|상위 시총|겹치|중복|종목 수",
 "security_vs_asset":r"ETF|자산군|주식|채권|금|종목|섹터|시장|기업",
 "etf_product":r"ETF|상장지수|펀드|SCHD|나스닥100|S&P\s*500|미국배당다우존스",
 "etf_index_rules":r"지수.{0,9}(?:구성|편입|선별|추종|방법론)|S&P\s*500|배당다우존스|배당기업|시가총액|재무 지표|100개|500개|선도 기업|패시브",
 "entry_lot":r"만원대|만원|1주|한 주|매수 가능|매수접근|거래단위|ETF 가격|개별 ETF 가격|소액",
 "dividend_cashflow":r"배당|분배|월배당|커버드콜",
 "dividend_frequency":r"분기|월 분배|월분배|매달.{0,5}분배|월별 지급|월배당|매월.{0,5}(?:배당|분배)",
 "dividend_sustainability":r"안정적|안정성|지속성|감소|중단|비보장|지급액|원금.{0,8}잠식|원금.{0,8}보장|세전|배당수익|분배금.{0,5}보장",
 "dividend_reinvest":r"배당.{0,8}재투자|배당금.{0,6}(?:재투자|축적)|현금배당 재투자|배당재투자|배당금으로|배당주.{0,7}정기매수",
 "periodic_invest":r"정기매수|적립식|정액 적립|신규 저축|정기.{0,5}투자|재투자",
 "pension_lump":r"퇴직금.{0,12}(?:목돈|분할|정기)|퇴직.{0,5}목돈|과거 월급|3년 분할|일정 기간 거치",
 "retirement_income":r"은퇴.{0,10}현금흐름|연금.{0,10}현금흐름|국민연금|월 생활비|월.{0,5}수령|매달.{0,8}현금흐름|매월.{0,8}현금흐름",
 "tax_route":r"과세|세금|국내.{0,9}과세|현지.{0,9}과세|일본.{0,9}상장|원엔|달러엔|엔화|환전",
 "product_access":r"ETF.{0,12}(?:가격|1주|만원)|소액|만원대|1주|한 주|거래단위|허용상품|매수 가능",
 "product_diversification":r"ETF.{0,12}(?:다수|분산|집중|종목)|단일.{0,8}ETF|분산 효과|다수 종목|테마.{0,5}ETF",
 "investor_principle":r"투자.{0,5}원칙|자산배분|장기투자|저비용|분산투자|투자 교육|위험 관리",
 "retirement_sustainability":r"은퇴기|지속 가능한 현금흐름|현금흐름.{0,8}위험|일확천금",
 "income_projection":r"월\s*[\d,]+\s*만원|연\s*6\s*%|월분배|월배당|지급액|세전.{0,7}분배",
 "index_us_exposure":r"미국.{0,12}(?:주가지수|지수|대형주)|S&P\s*500|미국지수",
 "fx_execution":r"엔화로.{0,18}(?:ETF|주식)|원화로.{0,18}(?:ETF|엔화)|환전.{0,12}(?:매수|후)|방법\s*[1-5]",
}
RX={k:re.compile(v,re.I) for k,v in CONCEPTS.items()}
@lru_cache(maxsize=16384)
def concepts(text):
    return frozenset(k for k,v in RX.items() if v.search(text))

def _both(a,b,k):return k in a and k in b
def _cross(a,b,x,y):return (x in a and y in b) or (x in b and y in a)

def retrieve(a_text,b_text,legacy_signals=None,left_verdict=None,right_verdict=None):
    """(candidate: bool, evidence: dict). Always REVIEW ONLY.

    Inherited scope blockers can never be defeated by a newly detected bridge.
    No historical source status or external finance fact is altered.
    """
    base,prior=frozen_v21_retrieve(
        a_text,b_text,legacy_signals,left_verdict,right_verdict)
    fa,fb=concepts(a_text),concepts(b_text)
    shared=fa&fb
    edges=[]
    veto=[]

    # A high-level investment risk term cannot transform loan rollover or
    # a monthly bank-account budget into the same proposition as asset risk.
    if ((re.search(r"연금담보대출|상환.재대출",a_text) and
         re.search(r"섹터|시총기업|분산|자산군",b_text) and
         "대출" not in b_text) or
        (re.search(r"연금담보대출|상환.재대출",b_text) and
         re.search(r"섹터|시총기업|분산|자산군",a_text) and
         "대출" not in a_text)):
        veto.append("collateral_loan_vs_underlying_asset_concentration")
    if ((re.search(r"청년 저축|ISA.{0,16}연금저축",a_text) and
         re.search(r"자산군|주식.채권|특정 자산",b_text) and
         "자산군" not in a_text) or
        (re.search(r"청년 저축|ISA.{0,16}연금저축",b_text) and
         re.search(r"자산군|주식.채권|특정 자산",a_text) and
         "자산군" not in b_text)):
        veto.append("household_account_budget_vs_market_asset_allocation")

    # Distinguish cash-flow RECEIPTS from allocation of earned wages;
    # distinguish a statutory pension timing/arithmetic example from
    # reinvestment of equity dividends.
    if ((re.search(r"청년 저축|월\s*100만원.{0,45}ISA",a_text) and
         "dividend_cashflow" in fb and "dividend_cashflow" not in fa) or
        (re.search(r"청년 저축|월\s*100만원.{0,45}ISA",b_text) and
         "dividend_cashflow" in fa and "dividend_cashflow" not in fb)):
        veto.append("wage_contribution_budget_vs_dividend_income")
    if ((re.search(r"국민연금.{0,40}(?:월\s*30만원|7년|복리)",a_text) and
         "dividend_reinvest" in fb and "dividend_cashflow" not in fa) or
        (re.search(r"국민연금.{0,40}(?:월\s*30만원|7년|복리)",b_text) and
         "dividend_reinvest" in fa and "dividend_cashflow" not in fb)):
        veto.append("national_pension_numeric_example_vs_equity_dividend_reinvestment")

    # A deterministic monthly-contribution compound-interest arithmetic
    # correction is not itself an equity-dividend-reinvestment claim.
    def fixed_contribution_arithmetic(t):
        return bool(re.search(r"월\s*[\d,]+\s*만원",t) and
                    re.search(r"\d+년",t) and
                    re.search(r"연\s*\d+\s*%",t) and
                    re.search(r"불일치|오류|잘못|계산",t) and
                    "배당" not in t and "분배" not in t)
    if ((fixed_contribution_arithmetic(a_text) and
         "dividend_reinvest" in fb) or
        (fixed_contribution_arithmetic(b_text) and
         "dividend_reinvest" in fa)):
        veto.append("fixed_monthly_contribution_arithmetic_vs_dividend_reinvestment")

    # Typed scope boundaries: same ETF or same recurring-buy words do not
    # imply the same economic action, eligibility, accounting or exposure.
    if _cross(fa,fb,"dividend_reinvest","pension_lump") and (
        "pension_lump" in fa or "pension_lump" in fb):
        veto.append("dividend_recycling_vs_retirement_lump_sum_scheduling")
    if (_cross(fa,fb,"etf_index_rules","tax_route") and
        (("엔화" in a_text or "환전" in a_text or "엔화" in b_text or "환전" in b_text)) and
        ("etf_index_rules" in fa or "etf_index_rules" in fb) and
        not ("etf_index_rules" in shared) and not (
          "index_us_exposure" in fa and "index_us_exposure" in fb and
          "ETF" in a_text.upper() and "ETF" in b_text.upper() and
          "지수" in a_text and "지수" in b_text)):
        veto.append("index_constituent_selection_vs_fx_execution_routes")
    if (_cross(fa,fb,"dividend_frequency","tax_route") and
        ("일본" in a_text+b_text or "엔화" in a_text+b_text) and
        not ("dividend_frequency" in shared)):
        veto.append("distribution_cadence_vs_foreign_tax_jurisdiction")
    if (_cross(fa,fb,"return_measure","pension_lump") and
        ("dividend_reinvest" in fa or "dividend_reinvest" in fb)
        and "pension_lump" in fa|fb):
        veto.append("dividend_return_compounding_vs_cash_lump_plan")

    # Avoid claim-identity shortcuts; bridges must have financial proposition
    # cues on both sides, often in different levels of an economic hierarchy.
    if _cross(fa,fb,"long_horizon","history_vs_future") and (
        "history_vs_future" in shared or "drawdown" in fa|fb):
        edges.append("horizon_and_past_results_are_conditional")
    if _both(fa,fb,"drawdown") and (
        "volatility" in fa|fb or "long_horizon" in fa|fb):
        edges.append("drawdown_recovery_vs_investment_time")
    if _cross(fa,fb,"drawdown","volatility") and (
        "risk_management" in fa|fb or "long_horizon" in fa|fb):
        edges.append("price_drawdown_vs_broader_investment_risk")
    if _cross(fa,fb,"return_measure","long_horizon") and (
        "history_vs_future" in fa|fb and "return_measure" in fa|fb):
        edges.append("historical_average_vs_hypothetical_growth_model")
    if _both(fa,fb,"return_measure") and (
        ("backtest_model" in fa|fb and "return_provenance" in fa|fb) or
        ("history_vs_future" in fa|fb and
         ("backtest_model" in fa|fb or "long_horizon" in fa|fb))):
        edges.append("average_historical_vs_realized_performance")
    if _cross(fa,fb,"return_measure","dividend_reinvest") and (
        "backtest_model" in fa|fb or "long_horizon" in fa|fb):
        edges.append("return_measurement_vs_reinvested_cash")
    if _cross(fa,fb,"backtest_model","dividend_reinvest") and (
        "return_measure" in fa|fb):
        edges.append("backtest_reinvestment_assumptions_vs_cash_reinvestment")
    if _both(fa,fb,"return_measure") and "long_horizon" in fa|fb and (
        "return_provenance" in (fa|fb)):
        edges.append("investor_holding_period_vs_compound_assumptions")
    if _both(fa,fb,"investor_behavior") and (
        "drawdown" in fa|fb or "long_horizon" in fa|fb):
        edges.append("panic_sell_vs_recovery_timing")
    if _cross(fa,fb,"drawdown","investor_behavior") and (
        "long_horizon" in fa|fb or "liquidity_buffer" in fa|fb):
        edges.append("severe_market_drawdowns_vs_holding_behavior")
    if _cross(fa,fb,"drawdown","liquidity_buffer") and (
        "long_horizon" in fa|fb):
        edges.append("bear_market_liquidity_and_staged_entry")

    # Macro risk explanations can inform asset-allocation principles even
    # when the speaker omits the literal term 'portfolio'.
    if (_cross(fa,fb,"macro_regime","investor_principle") and
        "위험" in a_text+b_text and
        "자산배분" in a_text+b_text):
        edges.append("all_weather_risk_objective_vs_allocation_education")
    if _cross(fa,fb,"macro_regime","investor_principle") and (
        "risk_management" in fa|fb and
        ("asset_allocation" in (fa|fb) or "investor_principle" in shared)):
        edges.append("all_weather_macro_risk_vs_general_diversification_principles")
    if _cross(fa,fb,"macro_regime","retirement_sustainability") and (
        "risk_management" in shared):
        edges.append("all_weather_risk_stability_vs_retiree_drawdown_survivability")
    if (_both(fa,fb,"risk_management") and
        "macro_regime" in (fa|fb) and "etf_product" in (fa|fb)):
        edges.append("all_weather_vs_single_equity_etf_stability_assumptions")
    if (_both(fa,fb,"multiasset_exposure") and
        "macro_regime" in (fa|fb) and
        ("현금성" in a_text+b_text or "엔화" in a_text+b_text) and
        ("주식" in a_text and "주식" in b_text)):
        edges.append("currency_cash_vs_equity_risk_role")

    # Macro/risk-parity and asset-allocation are connected at asset-class
    # exposure level, not because "growth" predicts next period's returns.
    if _cross(fa,fb,"macro_regime","asset_allocation") and (
        "multiasset_exposure" in (fa|fb) and
        ("asset_allocation" in shared or "risk_management" in fa|fb)):
        edges.append("growth_inflation_regime_vs_allocation")
    if _both(fa,fb,"asset_allocation") and (
        "portfolio_weights" in fa|fb or
        "macro_regime" in fa|fb or
        "risk_management" in fa|fb):
        edges.append("multiasset_portfolio_construction")
    if _both(fa,fb,"portfolio_weights") and (
        "multiasset_exposure" in fa and "multiasset_exposure" in fb):
        edges.append("portfolio_weight_comparative_allocation")
    if _cross(fa,fb,"portfolio_weights","asset_allocation") and (
        "multiasset_exposure" in fa and "multiasset_exposure" in fb):
        edges.append("different_weight_schemes_same_asset_mixture")
    if _cross(fa,fb,"multiasset_exposure","risk_management") and (
        "asset_allocation" in fa|fb and
        ("security_vs_asset" in shared or "asset_allocation" in shared)):
        edges.append("asset_class_risk_roles")
    if _both(fa,fb,"volatility") and (
        "risk_management" in fa|fb or "asset_allocation" in fa|fb):
        edges.append("reported_volatility_vs_investment_risk")
    if _cross(fa,fb,"risk_correlation","risk_management") and (
        "asset_allocation" in fa|fb or "security_overlap" in fa|fb):
        edges.append("correlation_asset_vs_security_level")
    if _both(fa,fb,"risk_management") and (
        "asset_allocation" in fa|fb and
        ("macro_regime" in fa|fb or "risk_correlation" in fa|fb)):
        edges.append("diversification_residual_risk")
    if _cross(fa,fb,"risk_management","retirement_income") and (
        "asset_allocation" in fa|fb):
        edges.append("portfolio_survivability_vs_retirement_income")
    if _cross(fa,fb,"asset_allocation","security_overlap") and (
        "security_vs_asset" in shared):
        edges.append("asset_class_diversification_vs_index_overlap")

    # Dividend-investing cashflows are not guaranteed; month/quarter payment
    # cadence is not return, nor the tax route for Japanese exchange products.
    if _both(fa,fb,"dividend_cashflow") and (
        "retirement_income" in fa|fb or
        "dividend_frequency" in fa|fb or
        "dividend_sustainability" in fa|fb or
        "dividend_reinvest" in fa|fb):
        edges.append("dividend_funding_vs_payment_sustainability")
    if _cross(fa,fb,"dividend_cashflow","income_projection") and (
        "dividend_sustainability" in fa|fb and
        re.search(r"월\s*\d+\s*만원|세전|지급액",a_text+b_text)):
        edges.append("dividend_income_vs_hypothetical_monthly_payment")
    if _cross(fa,fb,"dividend_cashflow","retirement_income") and (
        "dividend_sustainability" in fa|fb or
        "dividend_frequency" in fa|fb):
        edges.append("dividend_etf_income_vs_retirement_spending")
    if _cross(fa,fb,"dividend_cashflow","dividend_sustainability") and (
        "return_measure" in fa|fb or "dividend_frequency" in fa|fb):
        edges.append("dividend_payout_not_guaranteed")
    if _both(fa,fb,"dividend_reinvest") and (
        "return_measure" in fa|fb or "periodic_invest" in fa|fb):
        edges.append("reinvested_distributions_accumulation")
    if _cross(fa,fb,"dividend_reinvest","periodic_invest") and (
        "dividend_cashflow" in fa|fb and "pension_lump" not in fa|fb):
        edges.append("dividend_recycling_vs_new_contributions")
    if _cross(fa,fb,"dividend_reinvest","return_measure") and (
        "long_horizon" in fa|fb):
        edges.append("dividend_reinvestment_compounding_vs_return_assumption")
    if (_both(fa,fb,"dividend_frequency") and
        "dividend_cashflow" in (fa|fb)):
        edges.append("monthly_vs_quarterly_distribution_cadence")
    if _cross(fa,fb,"dividend_frequency","dividend_cashflow") and (
        "dividend_sustainability" in fa|fb):
        edges.append("payout_frequency_vs_income_stability")

    # ETF access, index methodologies, concentration and overlap
    if _both(fa,fb,"etf_index_rules") and (
        "etf_product" in shared or "security_vs_asset" in shared):
        edges.append("equity_index_construction_comparison")
    if _cross(fa,fb,"etf_index_rules","etf_product") and (
        "etf_index_rules" in fa|fb and "etf_product" in shared):
        edges.append("index_rule_vs_etf_vehicle")
    if _both(fa,fb,"product_access") and "etf_product" in shared:
        edges.append("etf_unit_lot_price_access")
    if _cross(fa,fb,"entry_lot","product_access") and "etf_product" in shared:
        edges.append("etf_minimum_unit_vs_price_affordability")
    if _cross(fa,fb,"product_diversification","risk_management") and (
        "etf_product" in shared):
        edges.append("etf_affordability_does_not_remove_equity_risk")
    if _both(fa,fb,"security_overlap") and (
        "risk_management" in fa|fb or "etf_product" in fa|fb):
        edges.append("stock_sector_overlap_concentration")
    if _cross(fa,fb,"security_overlap","risk_management") and (
        "concentration" in fa|fb):
        edges.append("index_constituent_overlap_vs_concentration")
    if _cross(fa,fb,"product_diversification","asset_allocation") and (
        "etf_product" in fa|fb):
        edges.append("equity_etfs_internal_vs_multiasset_diversification")

    # A new bridge cannot defeat old hard scope blockers from either version.
    inherited=sorted(set(prior.get("inherited_v2_scope_blocks",[]) +
                         prior.get("v21_scope_blocks",[])))
    found=bool(base or edges) and not (veto or inherited)
    d=dict(prior)
    d.update({
        "engine_version":VERSION,
        "v22_concepts_left":sorted(fa),
        "v22_concepts_right":sorted(fb),
        "v22_bridges":sorted(set(edges)),
        "v22_scope_blocks":sorted(set(veto)),
        "inherited_v21_v2_scope_blocks":inherited,
        "v22_base_v21_candidate":bool(base),
        "review_only":True,
        "correction_only":left_verdict=="CONTRADICTED" or
                          right_verdict=="CONTRADICTED",
        "semantic_relation_prediction":None,
        "automatic_knowledge_approval":False,
        "candidate_is_evidence_of_claim_truth":False,
    })
    return found,d
