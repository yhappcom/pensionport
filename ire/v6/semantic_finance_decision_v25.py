"""V25: claim-by-claim chat relevance contract and conditional ISA cap arithmetic.

No external model/API, automatic meaning certification, personal tax credit, trade or
verified publisher signature. This additive wrapper preserves frozen V24 bytes.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from .advisory_decision_utility import evaluate_current_question
from .atomic_exchange import audit_host_atomic_exchange
from .codec import sha256, json_digest
from .current_law_reassessment import _rules
from .errors import InvalidInput
from .temporal_finance_gate import _day

_RELATIONS = frozenset({'DIRECT', 'NECESSARY_EXCEPTION', 'COUNTERPOINT'})
_MONEY_LIMIT = 10 ** 12


def _facet(text: str) -> set[str]:
    s = text.upper()
    result = set()
    if 'IRP' in s or '개인형퇴직연금' in text or '개인형 퇴직연금' in text:
        if re.search(r'중도|인출|해지', text):
            result.add('IRP_WITHDRAWAL')
        if re.search(r'은퇴|연금|생활비|현금흐름|수령', text):
            result.add('IRP_INCOME')
    if 'ETF' in s or '상장지수펀드' in text:
        if re.search(r'과세|세금|세율|15[.]4|매매차익|배당소득', text):
            result.add('ETF_TAX')
        if re.search(r'수익|가격|분배금|총손익|총수익', text):
            result.add('ETF_RETURN')
    if 'ISA' in s or '개인종합자산관리계좌' in text:
        if re.search(r'만기|전환|이전|이체|연금계좌|납입', text):
            result.add('ISA_TRANSFER')
    if re.search(r'연금저축', text) and re.search(r'비공제|과세제외|인출|원금', text):
        result.add('PENSION_EXCLUDED_BASIS')
    if re.search(r'증여', text) and re.search(r'과세|세금|세율|공제|과세표준', text):
        result.add('GIFT_TAX')
    return result


def _audit_relevance(question, exchange, selected_claim_ids, decisions, as_of):
    if type(decisions) is not list or len(decisions) != len(selected_claim_ids):
        raise InvalidInput('V25_RELEVANCE_CENSUS_MISMATCH')
    atoms = {a['claim_id']: a for a in exchange['atoms']}
    q_facet = _facet(question)
    if not q_facet:
        raise InvalidInput('V25_UNSUPPORTED_QUESTION_SEMANTIC_FACET')
    q_sha = sha256(question.encode('utf-8'))
    expected = set(selected_claim_ids)
    if len(expected) != len(selected_claim_ids) or not expected.issubset(atoms):
        raise InvalidInput('V25_SELECTED_ATOM_CENSUS_INVALID')
    ids, covered = [], set()
    for d in decisions:
        if type(d) is not dict:
            raise InvalidInput('V25_RELEVANCE_DECISION_MALFORMED')
        cid = d.get('claim_id')
        if cid not in expected or cid in ids:
            raise InvalidInput('V25_RELEVANCE_UNKNOWN_OR_DUPLICATE_CLAIM')
        a = atoms[cid]
        if (d.get('question_sha256') != q_sha or
            d.get('proposition_sha256') != sha256(a['proposition'].encode('utf-8')) or
            d.get('reviewed_as_of') != as_of or
            d.get('reviewer') != 'CHATGPT_CURRENT_TURN'):
            raise InvalidInput('V25_RELEVANCE_PROVENANCE_OR_ASOF_MISMATCH')
        if d.get('relation') not in _RELATIONS:
            raise InvalidInput('V25_UNRELATED_OR_UNCERTAIN_SOURCE_CLAIM')
        if any(d.get(flag) is not True for flag in
               ('source_attribution_checked', 'stance_checked',
                'conditions_and_exceptions_checked', 'numeric_scope_checked')):
            raise InvalidInput('V25_SEMANTIC_REVIEW_INCOMPLETE')
        reason = d.get('reason')
        if type(reason) is not str or not 15 <= len(reason) <= 500:
            raise InvalidInput('V25_RELEVANCE_EXPLANATION_REQUIRED')
        facet = d.get('facet')
        if facet not in q_facet or facet not in _facet(a['proposition']):
            raise InvalidInput('V25_SAME_TOPIC_DIFFERENT_QUESTION_FACET')
        covered.add(facet)
        ids.append(cid)
    if covered != q_facet:
        raise InvalidInput('V25_UNCOVERED_QUESTION_FACETS')
    return {'reviewed_claim_count':len(ids),
            'question_facets':sorted(covered),
            'review_receipt_sha256':json_digest(decisions)}


def _whole_krw(value, name, *, max_value=_MONEY_LIMIT):
    if type(value) is not int or value < 0 or value > max_value:
        raise InvalidInput('V25_INVALID_AMOUNT_'+name)
    return value


def _literal_date(value, name):
    if type(value) is not str or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise InvalidInput('V25_INVALID_DATE_'+name)
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise InvalidInput('V25_INVALID_DATE_'+name) from exc


def illustrative_isa_extra_base(scenario: dict, *, current_as_of: str,
                                 primary_evidence: list, law_review: dict) -> dict:
    """Only the nominal ADDITIONAL DEDUCTIBLE CONTRIBUTION BASE, never tax refund.

    Requires two source excerpts and an explicit same-chat legal-term receipt.
    Dates/amounts are unverified user assumptions. Cross-year/split-year cases
    are quarantined, rather than incorrectly resetting the 3m cumulative cap.
    """
    if type(scenario) is not dict or scenario.get('kind') != 'ISA_TRANSFER':
        raise InvalidInput('V25_ISA_SCENARIO_REQUIRED')
    as_of = _day(current_as_of, 'V25_ISA_CURRENT_ASOF')
    if (type(law_review) is not dict or law_review.get('reviewed_as_of') != current_as_of
        or law_review.get('reviewer') != 'CHATGPT_CURRENT_TURN'
        or law_review.get('scope') != 'CURRENT_GENERAL_RULE_ONLY'
        or law_review.get('transfer_days') != 60
        or law_review.get('extra_base_rate_bps') != 1000
        or law_review.get('max_extra_base_krw') != 3000000):
        raise InvalidInput('V25_ISA_LEGAL_TERMS_NOT_REVIEWED')
    ids = law_review.get('rule_ids')
    if (type(ids) is not list or len(ids) != 2 or
        any(type(x) is not str for x in ids) or len(set(ids)) != 2):
        raise InvalidInput('V25_ISA_TWO_DISTINCT_PRIMARY_RULES_REQUIRED')
    rules = _rules(as_of, primary_evidence)
    if any(rid not in rules or
           rules[rid]['status'] != 'EFFECTIVE_ON_CURRENT_ASOF_CHAT_PRIMARY_EXCERPT_ONLY'
           for rid in ids):
        raise InvalidInput('V25_ISA_LAW_OUT_OF_DATE_OR_UNSUPPORTED')
    raw = {e['rule_id']:e for e in primary_evidence}
    if not all(rid in raw for rid in ids):
        raise InvalidInput('V25_ISA_RULE_ID_UNKNOWN')
    excerpts = [raw[rid]['excerpt'] for rid in ids]
    if (not any('60일' in e or '60 일' in e for e in excerpts) or
        not any((('10%' in e or '100분의 10' in e) and
                 ('300만원' in e or '300만 원' in e or '3,000,000' in e))
                for e in excerpts)):
        raise InvalidInput('V25_ISA_OFFICIAL_EXCERPT_TERMS_NOT_SHOWN')
    if law_review.get('excerpt_sha256') != [raw[x]['excerpt_sha256'] for x in ids]:
        raise InvalidInput('V25_ISA_LEGAL_EXCERPT_PIN_MISMATCH')
    expired = _literal_date(scenario.get('isa_expiry_date'), 'expiry')
    deposited = _literal_date(scenario.get('pension_deposit_date'), 'deposit')
    if deposited > as_of or expired > deposited:
        raise InvalidInput('V25_ISA_DATE_SEQUENCE_INVALID')
    balance = _whole_krw(scenario.get('isa_balance_at_expiry_krw'), 'expiry_balance')
    transfer = _whole_krw(scenario.get('pension_deposit_from_isa_krw'), 'deposit')
    prior = _whole_krw(scenario.get('prior_transfers_from_same_isa_krw'), 'prior')
    used = _whole_krw(scenario.get('previously_used_extra_base_krw'), 'used', max_value=3000000)
    if transfer + prior > balance:
        raise InvalidInput('V25_ISA_DEPOSIT_EXCEEDS_EXPIRY_BALANCE')
    if expired.year != deposited.year:
        return {'status':'CROSS_TAX_YEAR_DEFER',
                'illustrative_extra_deduction_base_krw':None,
                'actual_credit_krw':None, 'actual_refund_krw':None,
                'personal_eligibility_verified':False}
    days = (deposited-expired).days
    estimated = min(transfer // 10, 3000000-used) if days <= 60 else 0
    return {'status':'SAME_YEAR_ILLUSTRATIVE_BASE_ONLY',
            'days_after_expiry':days,
            'illustrative_extra_deduction_base_krw':estimated,
            'actual_credit_krw':None, 'actual_refund_krw':None,
            'personal_eligibility_verified':False,
            'primary_rule_ids':ids}


def evaluate_current_question_v25(root: Path, question: str, *, source, exchange,
                                  current_as_of: str, primary_evidence: list,
                                  chat_decisions: list, selected_claim_ids: list,
                                  relevance_decisions: list,
                                  scenario: dict | None = None,
                                  isa_law_review: dict | None = None) -> dict:
    """Preflight source/citation relevance BEFORE invoking V5 P3/P2 via V24."""
    audit_host_atomic_exchange(source, exchange)
    relevance = _audit_relevance(question, exchange, selected_claim_ids,
                                 relevance_decisions, current_as_of)
    # V24 always quarantines personal ISA tax; V25 does not unquarantine it.
    base = evaluate_current_question(root, question, source=source, exchange=exchange,
        current_as_of=current_as_of, primary_evidence=primary_evidence,
        chat_decisions=chat_decisions, selected_claim_ids=selected_claim_ids,
        scenario=scenario)
    estimate = None
    if isa_law_review is not None:
        if (scenario is None or type(scenario) is not dict or
            scenario.get('kind') != 'ISA_TRANSFER' or
            'ISA_TRANSFER' not in relevance['question_facets'] or
            base['selected_unresolved_claim_ids']):
            raise InvalidInput('V25_ISA_UNSUPPORTED_OR_UNRESOLVED_QUESTION')
        cited_rules = {rid for d in chat_decisions
                       if d.get('claim_id') in selected_claim_ids
                       for rid in d.get('rule_ids', [])}
        if not set(isa_law_review.get('rule_ids', [])).issubset(cited_rules):
            raise InvalidInput('V25_ISA_TERMS_NOT_LINKED_TO_SELECTED_SOURCE_REVIEW')
        estimate = illustrative_isa_extra_base(scenario,current_as_of=current_as_of,
                    primary_evidence=primary_evidence,law_review=isa_law_review)
    text = base['answer_text']
    if estimate and estimate['status']=='SAME_YEAR_ILLUSTRATIVE_BASE_ONLY':
        text += ('\n입력 가정과 일반 규정에 따른 ISA 추가 세액공제 대상 납입한도 산술: '
                 f'{estimate["illustrative_extra_deduction_base_krw"]:,}원. '
                 '이는 세액공제액이나 환급액이 아니며 개인별 자격·과세연도·결정세액은 미검증입니다.')
    if estimate and estimate['status']=='CROSS_TAX_YEAR_DEFER':
        text += '\n과세연도에 걸친 ISA 이전은 이전 연도 사용 한도 확인 전까지 계산을 보류합니다.'
    return {**base, 'schema':'IRE_V6_CURRENT_FINANCE_SEMANTIC_GATE_V25',
            'answer_text':text,
            'semantic_relevance_review':relevance,
            'selected_claim_relevance_heuristic_only':True,
            'selected_claim_relevance_chat_review_only':True,
            'independent_question_to_claim_entailment_verified':False,
            'isa_extra_deduction_base_illustration':estimate,
            'isa_tax_calculation_quarantined_pending_current_evidence':True,
            'personal_trade_or_tax_approval':False,
            'independent_answer_truth_or_decision_usefulness_certified':False,
            'p0_go':False,
            'status':'V25_CHAT_RELEVANCE_AND_CONDITIONAL_ISA_BASE_NO_PERSONAL_TAX_APPROVAL'}
