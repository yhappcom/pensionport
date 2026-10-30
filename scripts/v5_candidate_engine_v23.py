#!/usr/bin/env python3
"""V2.3 source-aware RETRIEVAL candidate development, never fact verification.

Uses frozen V2.2 guarded decisions as baseline; typed economic-role bridges
address diagnosed #17-18 retrieval failures. Source provenance is REQUIRED.
No source rewrites, semantic support predictions, adviser decisions or merges.
The #17/18 benchmark is now development data. #19+ remains unseen.
"""
import re
from functools import lru_cache

from v5_candidate_engine_v22_guarded import retrieve_claims as frozen_v22_guarded

VERSION="2.3.0"

# Low-entropy terms "ETF", "연금", "금", "만원" by themselves are NOT
# evidence of related propositions. These are composite economic attributes.
PATTERNS={
    "retirement_constraint":r"건강상|배우자.{0,10}은퇴|추가 납입.{0,9}(?:어렵|불가|없이)|재취업|완전 은퇴|퇴직.{0,8}생활비|지출 계획|지출능력",
    "retirement_planning":r"은퇴|퇴직|노후|연금|재취업|생활비",
    "retirement_capital":r"퇴직연금.{0,25}(?:억|자금)|개인연금.{0,25}(?:억|자금)|퇴직금|퇴직 목돈|초기 자금|연금.{0,8}초기",
    "retirement_strategy":r"자산배분|운용|거치|파킹형|분할.{0,4}투자|분할.{0,4}매수|현금흐름|지출|언제 쓸|연금수령",
    "retirement_cashflow":r"생활비|현금흐름|월.{0,6}수령|분배금|연금수령|지출",
    "retirement_target":r"(?:연\s*)?5\s*[~∼-]\s*7\s*%|10년.{0,15}(?:복리|수익률)|연.{0,8}투자 목표|연.{0,8}수익률|장기.{0,7}목표수익률",
    "retirement_account":r"퇴직연금|IRP|연금저축|연금계좌|개인연금",
    "multi_asset":r"자산배분|자산군|주식.{0,8}채권|채권.{0,8}금|리스크.?패리티|포트폴리오",
    "indexed_diversification":r"지수형.{0,7}펀드|KOSPI\s*200|코스피\s*200|지수.{0,9}(?:분산|대표기업)|다수.{0,9}(?:대형주|종목|기업)",
    "small_entry_general":r"만원으로.{0,12}투자|소액투자.{0,9}(?:시작|교육)|만원으로.{0,6}모든|만원.{0,8}(?:투자 방법|시작)",
    "small_lot":r"만원대|만원어치|1주|한 주|1좌|최소.{0,8}(?:매수|주문|거래)|소액.{0,5}(?:투자|매수)|만원으로",
    "investment_access":r"매수|투자|ETF|펀드|대표지수|적립식|정기.{0,4}매수|한 주|1주",
    "periodic_education":r"적립식|정기.{0,6}매수|대표지수 ETF|소액|초보|교육적|투자 공부",
    "group_controlled_fund":r"(?:계열사|계열 기업|기업집단|그룹).{0,10}펀드|(?:삼성|SK).{0,15}(?:계열|기업집단)|대기업.{0,10}전용 펀드",
    "equity_diversification":r"분산|집중|다수.{0,7}종목|섹터|업종|시장지수|산업|기업|주식|펀드",
    "equity_concentration":r"집중|한 기업|단일.{0,10}(?:종목|기업|업종|섹터)|특정.{0,6}(?:기업|자산|시장)|국가.{0,6}자산군|섹터|테마|인생주식|주식 위험",
    "bond_etf":r"(?:만기.{0,7}채권|채권.{0,8}ETF|국채.{0,6}ETF|채권 ETF)",
    "bond_maturity":r"채권.{0,15}만기|만기.{0,15}채권|만기매칭|초단기.{0,10}국채|듀레이션|금리 민감도",
    "fixed_income_risk":r"원금.{0,5}(?:회수|위험|손실)|금리.{0,8}(?:위험|민감도)|신용.{0,8}위험|채권|국채|만기|듀레이션",
    "fx_and_rate_learning":r"환율.{0,12}금리|금리.{0,12}환율|환율.{0,18}(?:학습|경험|변화)|금리.{0,18}(?:학습|경험|변화)",
    "fx_scope":r"환율|환전|엔화|달러|통화|환헤지|환노출|외환",
    "fx_risk_action":r"환율.{0,12}(?:예측|비중|위험)|스프레드|환전 비용|환전.{0,6}스프레드|환헤지|환노출|환율변동",
    "yield_learning":r"금리|채권|만기|듀레이션",
    "monthly_distribution_model":r"월\s*[\d,]+\s*만원|월배당|월분배|매달.{0,8}분배|월급처럼",
    "distribution_product":r"ETF.{0,15}분배|분배.{0,12}ETF|미국배당다우존스|분배금|월배당|월분배|배당주",
    "distribution_assumption":r"연\s*6\s*%|분배율|분배금|지급액|세전|월급처럼|안정적",
    "pension_income_tax":r"연\s*1,?500만원|1,?500만원.{0,12}과세|사적연금.{0,13}과세|연금소득.{0,13}과세",
    "contribution_limit":r"납입.{0,12}한도|연\s*1,?800만원|세액공제.{0,10}한도|연금저축.{0,8}600만원|퇴직연금.{0,7}900만원",
    "pension_deferral_bonus":r"연기연금|연기.{0,12}(?:0\.6|7\.2|36)|1개월 연기|1년\s*7\.2|5년\s*36",
}
RX={k:re.compile(v,re.IGNORECASE) for k,v in PATTERNS.items()}

@lru_cache(maxsize=16384)
def typed_facets(text):
    return frozenset(k for k,p in RX.items() if p.search(text))

def _both(a,b,k):
    return k in a and k in b

def _cross(a,b,x,y):
    return (x in a and y in b) or (x in b and y in a)

def _pure_pension_income_tax(f,t):
    return ("pension_income_tax" in f and
            "contribution_limit" not in f and
            not re.search(r"세액공제.{0,6}(?:납입|한도)",t))

def _pure_contribution_limit(f,t):
    return ("contribution_limit" in f and
            "pension_income_tax" not in f and
            bool(re.search(r"납입|세액공제",t)))

def retrieve_claims(left,right,legacy_signals=None):
    """Return (human_review_candidate, evidence trace), never auto approval.

    The frozen V2.2 *guarded* adapter validates claim IDs, original video
    metadata and verification status. Current claim data MUST have been read
    from independently source-hash-checked study records by the caller.
    """
    prior,info=frozen_v22_guarded(left,right,legacy_signals)
    a=left["text"];b=right["text"]
    fa,fb=typed_facets(a),typed_facets(b)
    union=fa|fb;common=fa&fb
    bridges=[]
    veto=[]

    # A pension INCOME tax threshold is not an annual CONTRIBUTION ceiling.
    if ((_pure_pension_income_tax(fa,a) and
         _pure_contribution_limit(fb,b)) or
        (_pure_pension_income_tax(fb,b) and
         _pure_contribution_limit(fa,a))):
        veto.append("pension_payout_tax_threshold_vs_account_contribution_limit")
    # Deferring national pension benefit to gain a statutory BONUS is
    # neither the private pension tax exemption nor the personal portfolio rate.
    if ((_pure_pension_income_tax(fa,a) and
         "pension_deferral_bonus" in fb and
         "pension_deferral_bonus" not in fa) or
        (_pure_pension_income_tax(fb,b) and
         "pension_deferral_bonus" in fa and
         "pension_deferral_bonus" not in fb)):
        veto.append("private_pension_tax_treatment_vs_national_pension_deferral_bonus")

    # A household retrospective/hypothetical financial situation and a
    # general plan may deserve comparison, not evidence of personal identity.
    if (_cross(fa,fb,"retirement_constraint","retirement_strategy") and
        _both(fa,fb,"retirement_planning") and
        ("retirement_cashflow" in union or "retirement_constraint" in common)):
        bridges.append("retirement_income_constraints_vs_spending_and_withdrawal_plan")
    if (_cross(fa,fb,"retirement_constraint","retirement_cashflow") and
        _both(fa,fb,"retirement_planning")):
        bridges.append("retirement_case_constraints_vs_general_cashflow")
    if (_both(fa,fb,"retirement_capital") and
        "retirement_strategy" in union and
        _both(fa,fb,"retirement_planning")):
        bridges.append("retirement_initial_capital_vs_lump_sum_investment_plan")
    if (_both(fa,fb,"retirement_target") and
        "retirement_account" in union and
        _both(fa,fb,"retirement_planning")):
        bridges.append("retirement_return_assumption_vs_account_accumulation_plan")

    # Beginner's money threshold is a transaction minimum/market price
    # question, not an annual pension limit or a hypothetical savings budget.
    if (_cross(fa,fb,"small_entry_general","small_lot") and
        "investment_access" in common):
        bridges.append("small_ticket_investing_vs_minimum_trade_lot")
    if (_cross(fa,fb,"small_entry_general","periodic_education") and
        "investment_access" in common):
        bridges.append("small_ticket_access_vs_index_savings_education")

    # A conglomerate-controlled fund can hold several industries yet retain
    # a shared controller/counterparty risk: compare to equity concentration,
    # never infer the two instruments are fungible.
    if (_cross(fa,fb,"group_controlled_fund","equity_concentration") and
        "equity_diversification" in common):
        bridges.append("conglomerate_fund_multiple_sectors_vs_controller_concentration")
    if (_cross(fa,fb,"group_controlled_fund","equity_diversification") and
        "equity_concentration" in union):
        bridges.append("corporate_group_holdings_vs_equity_diversification")

    # Bond duration and legal maturity are separate for direct bonds and
    # ETFs; candidate discovery invites a prospectus-level risk check.
    if (_both(fa,fb,"bond_maturity") and
        "fixed_income_risk" in common):
        bridges.append("individual_bond_maturity_vs_maturity_target_etf")
    if (_cross(fa,fb,"bond_etf","bond_maturity") and
        "fixed_income_risk" in common):
        bridges.append("bond_etf_duration_vs_held_to_maturity_bond")

    # FX learning includes foreign exchange spread, hedge, timing/risk.
    # Learning about interest-rate risk must not be equated with a statutory
    # pension increase rate, ordinary dividend yield or savings rate.
    if (_cross(fa,fb,"fx_and_rate_learning","fx_scope") and
        "fx_risk_action" in union):
        bridges.append("fx_risk_education_vs_currency_conversion_cost")
    if (_cross(fa,fb,"fx_and_rate_learning","yield_learning") and
        "bond_maturity" in union):
        bridges.append("interest_rate_learning_vs_bond_duration_risk")

    # A KRW 2.2m hypothetical monthly ETF payout and a small-lot income
    # ETF are financially comparable only on payability/variable amount.
    if (_both(fa,fb,"distribution_product") and
        "monthly_distribution_model" in common and
        "distribution_assumption" in union):
        bridges.append("monthly_etf_payout_assumption_vs_small_lot_income_etf")
    if (_cross(fa,fb,"multi_asset","indexed_diversification") and
        "retirement_target" in union and
        "retirement_planning" in union):
        bridges.append("retirement_asset_allocation_vs_index_fund_security_diversification")

    # Enforce historical V2/V2.1/V2.2 negative scopes, not just V2.2 bool.
    inherited=list(info.get("inherited_v21_v2_scope_blocks",[]))
    v22_blocks=list(info.get("v22_scope_blocks",[]))
    blocked=bool(veto or inherited or v22_blocks)
    candidate=bool(prior or bridges) and not blocked

    detail=dict(info)
    detail.update({
        "engine_version":VERSION,
        "v23_typed_left":sorted(fa),
        "v23_typed_right":sorted(fb),
        "v23_bridges":sorted(set(bridges)),
        "v23_scope_blocks":sorted(set(veto)),
        "v23_inherited_scope_blocks":sorted(set(inherited+v22_blocks)),
        "v23_inherited_v22_candidate":bool(prior),
        "review_only":True,
        "automatic_knowledge_approval":False,
        "automatic_merge_permitted":False,
        "semantic_relation_prediction":None,
        "candidate_is_evidence_of_claim_truth":False,
        "source_provenance_required":True,
        "independent_primary_or_numeric_verification_reperformed":False,
        "research_completion_certificate_permitted":False,
        "investment_trade_instruction_permitted":False,
    })
    return candidate,detail
