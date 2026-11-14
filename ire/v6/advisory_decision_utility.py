"""V24: source-constrained CURRENT-law decisions with transparent P2 maths.

The V23 bridge genuinely executes the legacy V5 P3 baseline. This additive
entrypoint adds question/claim relevance checks, direct decision-support text,
and verified non-law numerical comparisons. It NEVER publishes legacy P3's old
legal answer, authorizes an order, or certifies personal taxation or gold.
"""
from __future__ import annotations

import math
import re
import json
from pathlib import Path

from ire.v5.advisory_decision import compare as _v5_p2_compare
from ire.v5.advisory_intent import classify as _classify_intent
from .current_advisory_bridge import answer_with_current_law
from .errors import InvalidInput
from .codec import sha256

_TOPIC = {
    'IRP': (r'(?i)IRP|개인형\s*퇴직연금',r'(?i)IRP|개인형\s*퇴직연금'),
    'ETF': (r'(?i)ETF|상장지수펀드',r'(?i)ETF|상장지수펀드'),
    'ISA': (r'(?i)ISA|개인종합자산관리계좌',r'(?i)ISA|개인종합자산관리계좌'),
    'GIFT': (r'증여',r'증여'),
}
_ACTION = re.compile(r'(?:인출|이체|송금|매수|매도|팔아|주문|환매).{0,18}(?:해줘|해주세요|실행|처리|대신|시켜줘)')
_SAFE_KINDS = frozenset({'RETIREMENT_GAP','ETF_TOTAL_RETURN','ALLOCATION_DRIFT'})


def _finite(value, name):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise InvalidInput('V24_NONFINITE_OR_INVALID_MATH_'+name)
    return float(value)


def _close(got, expected, name):
    got=_finite(got,name)
    if not math.isclose(got,expected,rel_tol=1e-10,abs_tol=0.00001):
        raise InvalidInput('V24_MATH_RECOMPUTE_MISMATCH_'+name)
    return got


def _validate_calculation(comparison, scenario, question):
    if (type(comparison) is not dict or comparison.get('schema')!='IRE_V5_P2_CONDITIONAL_COMPARISON_V1' or
        comparison.get('question')!=question or comparison.get('kind')!=scenario.get('kind') or
        comparison.get('recommendation_status')!='TRADEOFF_ONLY_NOT_PERSONAL_ACTION' or
        comparison.get('personalized_trade_authorized') is not False or
        comparison.get('future_returns_guaranteed') is not False or
        comparison.get('default_win_or_trade_instruction') is not None):
        raise InvalidInput('V24_P2_OUTPUT_NOT_SAFE')
    rows=comparison.get('results')
    options=scenario.get('options')
    if (type(options) is not list or type(rows) is not list or len(rows)!=len(options) or
        not 1<=len(rows)<=5 or type(comparison.get('required_unpriced_factors')) is not list):
        raise InvalidInput('V24_P2_RESULT_COUNT_INVALID')
    result_lines=[]
    for o,r in zip(options,rows):
        if r.get('option_id')!=o.get('id') or not isinstance(o.get('id'),str):
            raise InvalidInput('V24_P2_OPTION_DRIFT')
        oid=o['id']
        kind=scenario['kind']
        if kind=='RETIREMENT_GAP':
            pension=_finite(scenario.get('monthly_pension_krw'),'pension')
            other=_finite(scenario.get('other_monthly_income_krw'),'income')
            expense=_finite(o.get('monthly_expense_krw'),'expense')
            gap=max(0.0,expense-pension-other)
            _close(r.get('monthly_unfunded_spending_krw'),gap,'monthly_gap')
            _close(r.get('annual_unfunded_spending_krw'),gap*12,'annual_gap')
            if r.get('retirement_capital_required') is not None:
                raise InvalidInput('V24_UNVERIFIED_RETIREMENT_CAPITAL_INFERRED')
            result_lines.append(f'대안 {oid}: 월 부족 현금흐름 {gap:,.0f}원, 연간 {gap*12:,.0f}원. 필요 투자원금은 아직 계산할 수 없습니다.')
        elif kind=='ETF_TOTAL_RETURN':
            entry=_finite(o.get('initial_value_krw'),'initial')
            ending=_finite(o.get('ending_market_value_krw'),'ending')
            dist=_finite(o.get('cash_distributions_krw'),'distributions')
            fees=_finite(o.get('separately_paid_fees_krw'),'outside_fees')
            if entry<=0:
                raise InvalidInput('V24_INVALID_INITIAL_VALUE')
            gain=ending+dist-fees-entry
            rate=gain/entry*100
            _close(r.get('net_total_return_krw_pre_tax'),gain,'etf_pretax_gain')
            _close(r.get('net_total_return_pct_pre_tax'),rate,'etf_pretax_pct')
            if r.get('cash_distribution_not_guaranteed_profit') is not True:
                raise InvalidInput('V24_DISTRIBUTION_NOT_PROFIT_SAFETY_FLAG_MISSING')
            result_lines.append(f'대안 {oid}: 입력 가정 기준 세전 총손익 {gain:,.0f}원, 세전 총수익률 {rate:.2f}%. 분배금만을 확정수익으로 해석할 수 없습니다.')
        elif kind=='ALLOCATION_DRIFT':
            target=_finite(scenario.get('target_equity_pct'),'target')
            current=_finite(o.get('current_equity_pct'),'current')
            if not (0<=current<=100 and 0<=target<=100):
                raise InvalidInput('V24_INVALID_PORTFOLIO_WEIGHT')
            drift=current-target
            _close(r.get('equity_weight_drift_percentage_points'),drift,'weight_drift')
            if r.get('trade_size_krw') is not None:
                raise InvalidInput('V24_UNAUTHORIZED_TRADE_SIZE')
            result_lines.append(f'대안 {oid}: 현재와 목표 주식비중 차이 {drift:+.2f}%포인트. 매수·매도 수량은 결정하지 않습니다.')
        else:
            raise InvalidInput('V24_NONSAFE_CALC_KIND')
    factors=comparison['required_unpriced_factors']
    if not factors or any(type(f) is not str or not 2<=len(f)<=200 for f in factors):
        raise InvalidInput('V24_MISSING_UNPRICED_FACTORS')
    return result_lines,factors


def evaluate_current_question(root: Path, question: str, *, source, exchange,
                              current_as_of: str, primary_evidence: list,
                              chat_decisions: list, selected_claim_ids: list,
                              scenario: dict | None = None) -> dict:
    """Real V5 P3 -> V22 current ChatGPT law review -> decision-safe user answer.

    The source-relevance check is intentionally conservative, heuristic and
    NOT an independently established completeness/entailment model.
    """
    if type(question) is not str or len(question)>4000 or not question.strip():
        raise InvalidInput('V24_QUESTION_INVALID')
    selected={x['claim_id']:x for x in exchange['atoms'] if x['claim_id'] in selected_claim_ids}
    if len(selected)!=len(selected_claim_ids):
        raise InvalidInput('V24_SELECTION_UNKNOWN_OR_DUPLICATE')
    propositions=' '.join(x['proposition'] for x in selected.values())
    named=[]
    for topic,(qrx,prx) in _TOPIC.items():
        if re.search(qrx,question):
            named.append(topic)
            if not re.search(prx,propositions):
                raise InvalidInput('V24_QUESTION_TO_SOURCE_TOPIC_MISMATCH_'+topic)
    if not named and not re.search(r'연금|은퇴|투자|주식|배분|분산|세금',question):
        raise InvalidInput('V24_QUESTION_FINANCIAL_SCOPE_MISSING')
    intent=_classify_intent(question)
    requested_action=bool(intent['order_execution_requested'] or _ACTION.search(question))
    # Do not even ask legacy V5 to calculate tax benefits or transaction
    # scenarios when V24 will quarantine their outputs.
    v5_scenario=None if requested_action or (type(scenario) is dict and scenario.get('kind')=='ISA_TRANSFER') else scenario
    base=answer_with_current_law(root,question,source=source,exchange=exchange,
        current_as_of=current_as_of,primary_evidence=primary_evidence,
        chat_decisions=chat_decisions,selected_claim_ids=selected_claim_ids,
        scenario=v5_scenario)
    if base.get('v5_p3_executed') is not True or base.get('p0_go') is not False:
        raise InvalidInput('V24_MISSING_REAL_V5_OR_FALSE_QUALITY_APPROVAL')
    rows={r['claim_id']:r for r in chat_decisions}
    linked=[rows.get(cid) for cid in selected_claim_ids]
    direct=[]
    if requested_action:
        direct.append('계좌 매수·매도·인출·송금 주문을 대신 실행할 수 없습니다. 필요한 법적 요건과 거래 조건은 별도로 확인해야 합니다.')
    else:
        if 'IRP' in named and any(d is not None and d['classification']=='CURRENT_RULE_CONTRADICTS_SOURCE' for d in linked):
            direct.append('IRP 중도인출이 전혀 불가능하다는 설명은 맞지 않습니다. 현행 규정은 법정 중도인출 사유를 인정하며, 본인의 해당 사유·증빙과 실제 인출 가능 금액은 별도로 확인해야 합니다.')
        if 'ETF' in named and any(d is not None and d['classification']=='CURRENT_RULE_SCOPE_MISSING' for d in linked):
            direct.append('모든 ETF 매매차익에 동일하게 15.4% 세금이 부과되지는 않습니다. 국내주식형과 기타 ETF, 계좌 유형과 분배금 과세를 구분해야 합니다.')
        if re.search(r'연금저축',question) and any(
                d is not None and d['classification']=='CURRENT_RULE_SCOPE_MISSING'
                and ('연금저축' in selected[cid]['proposition'] or '과세제외' in selected[cid]['proposition'])
                for cid,d in zip(selected_claim_ids,linked)):
            direct.append('연금저축 비공제 납입금도 모든 자금을 언제나 세금이나 계좌 제약 없이 인출할 수 있다는 의미는 아닙니다. 실제 과세제외 인정금액·인출순서·과거 세액공제 사용내역과 계좌 약관을 확인해야 합니다.')
        if 'ISA' in named and any(d is not None and d['classification']=='CURRENT_GENERAL_RULE_CONSISTENT_CONDITIONAL' for d in linked):
            direct.append('ISA 만기자금의 연금계좌 납입 혜택은 만기 후 60일 이내 납입 여부와 세액공제 대상 납입한도 등 현행 조건을 확인해야 합니다. 개인별 실제 환급액은 확정할 수 없습니다.')
        if 'GIFT' in named and any(d is not None and d['classification']=='CURRENT_RULE_SCOPE_MISSING' for d in linked):
            direct.append('증여세 세율은 증여한 금액 전체에 단순 세율을 곱하는 방식이 아닙니다. 공제 후 과세표준과 누진세율 구간, 누진공제·특례 조건을 분리해 검토해야 합니다.')
    if not direct:
        direct.append('해당 질문은 현재 법령·원본 주장·입력 조건을 구분하여 검토해야 하며, 주어진 정보만으로 개인별 결론을 확정할 수 없습니다.')
    lead=' '.join(direct)
    lines=[lead]
    quantified=False
    quarantined_isa=False
    math_hash=None
    if scenario is not None and not requested_action:
        if type(scenario) is not dict:
            raise InvalidInput('V24_INVALID_SCENARIO')
        kind=scenario.get('kind')
        if kind in _SAFE_KINDS:
            # The arithmetic is independent of changing tax rules but all P2
            # calculations are rechecked against the exact user inputs.
            if kind=='RETIREMENT_GAP' and not re.search(r'연금|IRP|은퇴|생활비|현금흐름',question):
                raise InvalidInput('V24_RETIREMENT_SCENARIO_QUESTION_MISMATCH')
            if kind=='ETF_TOTAL_RETURN' and 'ETF' not in named:
                raise InvalidInput('V24_ETF_MATH_QUESTION_MISMATCH')
            if kind=='ALLOCATION_DRIFT' and not re.search(r'비중|배분|리밸런싱',question):
                raise InvalidInput('V24_WEIGHT_MATH_QUESTION_MISMATCH')
            p2=_v5_p2_compare(Path(root),question,scenario)
            summary,factors=_validate_calculation(p2,scenario,question)
            lines.extend(summary)
            lines.append('위 수치는 제시된 가정에 따른 산술 비교이며, 아직 반영하지 못한 조건: '+ '; '.join(factors)+'.')
            quantified=True
            try:
                math_hash=sha256(json.dumps(p2,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8'))
            except (ValueError,TypeError) as e:
                raise InvalidInput('V24_P2_NUMERIC_JSON_INVALID') from e
        elif kind=='ISA_TRANSFER':
            # V5's P2 2026-11-05 ISA tax scenario relies on archived P1 facts;
            # do NOT rebrand those figures as fresh without primary-law review
            # for the transfer timing, credit base AND taxpayer eligibility.
            lines.append('ISA 전환 세액공제 금액 계산은 만기일·실제 납입일·현행 세법·결정세액 및 다른 공제를 확인하기 전까지 보류합니다. 기존 V5의 세금 계산을 현행 확정혜택으로 전달하지 않습니다.')
            quarantined_isa=True
        else:
            raise InvalidInput('V24_UNSUPPORTED_SCENARIO_KIND')
    elif scenario is not None and requested_action:
        lines.append('주문 요청에 연결된 숫자 계산 또는 실행 지시도 제공하지 않습니다.')
    lines.append('현재 시행 규정과 원자 주장 대조 결과(공식자료 근거·조건·예외 및 미확정 항목):')
    lines.append(base['answer_text'])
    response='\n'.join(lines)
    if not response.startswith(lead) or not base['answer_text'] in response:
        raise InvalidInput('V24_ANSWER_CONSTRUCTION_INTEGRITY_FAIL')
    return {
        **base,
        'schema':'IRE_V6_CURRENT_LAW_DECISION_UTILITY_V24',
        'answer_text':response,
        'direct_lead':lead,
        'identified_question_topics':named,
        'selected_claim_relevance_heuristic_only':True,
        'current_legal_conditions_present':True,
        'question_specific_direct_answer':True,
        'historical_v5_legal_text_carried_forward':False,
        'has_validated_illustrative_math':quantified,
        'validated_p2_math_sha256':math_hash,
        'isa_tax_calculation_quarantined_pending_current_evidence':quarantined_isa,
        'trade_or_transfer_execution_allowed':False,
        'personal_trade_or_tax_approval':False,
        'independent_answer_truth_or_decision_usefulness_certified':False,
        'external_human_gold':False,
        'p0_go':False,
        'status':'V24_CURRENT_DECISION_SUPPORT_DEVELOPMENT_ONLY_NOT_PERSONAL_APPROVAL'
    }
