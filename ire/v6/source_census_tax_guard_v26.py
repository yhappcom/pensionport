"""V26: complete candidate-atom census before source-based answers, safer ISA arithmetic.

Additive entrypoint; V25 and prior files remain byte pinned and unmodified.
Host judgements are same-chat assertions, NOT independent completeness/precision.
No raw SRT publishing, personal tax/refund, orders, or provider authentication.
"""
from __future__ import annotations

import re
from pathlib import Path

from ire.v5.advisory_intent import classify as _classify_intent
from .advisory_decision_utility import _ACTION
from .atomic_exchange import audit_host_atomic_exchange
from .codec import sha256, json_digest
from .errors import InvalidInput
from .semantic_finance_decision_v25 import (
    _facet, _literal_date, _whole_krw, illustrative_isa_extra_base,
    evaluate_current_question_v25,
)

_EXECUTE = re.compile(
    r'(?:옮겨|보내|입금|이전|이체|인출|매수|매도|환매|송금|주문|해지|전환)'
    r'.{0,28}(?:해\s?줘|해\s?주세요|실행|처리|대신|신청해|진행해)'
    r'|(?:직접|지금|당장).{0,28}(?:이체해|전환해|옮겨줘|주문해|인출해)',
    re.I,
)
_DISPOSITIONS = frozenset({
    'SELECTED_RELEVANT', 'REVIEWED_OFF_TOPIC', 'PENDING_RELEVANT', 'UNDECIDABLE',
})


def audit_candidate_census(question: str, exchange: dict, selected_claim_ids: list,
                           candidate_dispositions: list, current_as_of: str) -> dict:
    """Every available original-bound atom receives a question-specific status.

    This closes the *known candidate* omission path, not the harder upstream
    omission of atoms never extracted from original cues.
    """
    if (type(question) is not str or not question.strip()
        or type(candidate_dispositions) is not list):
        raise InvalidInput('V26_CENSUS_INPUT_INVALID')
    atoms = {a['claim_id']:a for a in exchange['atoms']}
    selected = set(selected_claim_ids)
    ids = sorted(atoms)
    if (type(selected_claim_ids) is not list or len(selected) != len(selected_claim_ids)
        or not selected or not selected.issubset(atoms)):
        raise InvalidInput('V26_SELECTED_CLAIMS_INVALID')
    if len(candidate_dispositions) != len(ids):
        raise InvalidInput('V26_CENSUS_MISSING_CANDIDATE')
    actual_ids = [d.get('claim_id') if type(d) is dict else None
                  for d in candidate_dispositions]
    if actual_ids != ids:
        raise InvalidInput('V26_CENSUS_UNSORTED_DUPLICATE_OR_FOREIGN_CLAIM')
    question_sha = sha256(question.encode('utf-8'))
    for d in candidate_dispositions:
        a = atoms[d['claim_id']]
        if (type(d) is not dict or
            set(d) != {
                'claim_id','question_sha256','proposition_sha256','disposition',
                'reviewer','reviewed_as_of','context_checked','reason'}):
            raise InvalidInput('V26_CENSUS_SCHEMA_DRIFT')
        if (d['question_sha256']!=question_sha or
            d['proposition_sha256'] != sha256(a['proposition'].encode('utf-8')) or
            d['reviewer']!='CHATGPT_CURRENT_TURN' or
            d['reviewed_as_of']!=current_as_of or
            d['context_checked'] is not True):
            raise InvalidInput('V26_CENSUS_SOURCE_OR_DATE_NOT_VERIFIED')
        if d['disposition'] not in _DISPOSITIONS:
            raise InvalidInput('V26_CENSUS_UNKNOWN_DISPOSITION')
        if type(d['reason']) is not str or not 15<=len(d['reason'])<=500:
            raise InvalidInput('V26_CENSUS_REASON_REQUIRED')
        if d['claim_id'] in selected:
            if d['disposition']!='SELECTED_RELEVANT':
                raise InvalidInput('V26_SELECTED_CLAIM_CENSUS_CONTRADICTION')
        elif d['disposition']!='REVIEWED_OFF_TOPIC':
            raise InvalidInput('V26_RELEVANT_UNSELECTED_OR_UNKNOWN_PENDING')
    return {'candidate_atom_count':len(atoms),
            'selected_claim_count':len(selected),
            'reviewed_off_topic_count':len(atoms)-len(selected),
            'candidate_receipt_sha256':json_digest(candidate_dispositions),
            'all_extracted_atoms_accounted_for':True,
            'full_original_atom_recall_certified':False}


def _isa_preflight(question: str, scenario, *, current_as_of: str):
    if type(scenario) is not dict or scenario.get('kind')!='ISA_TRANSFER':
        raise InvalidInput('V26_ISA_SCENARIO_REQUIRED')
    try:
        old_intent = _classify_intent(question)
    except (TypeError, ValueError, KeyError) as exc:
        raise InvalidInput('V26_QUESTION_INTENT_UNAVAILABLE') from exc
    if (old_intent.get('order_execution_requested') or _ACTION.search(question)
        or _EXECUTE.search(question)):
        raise InvalidInput('V26_ACTION_ATTACHED_ISA_MATH_REFUSED')
    # Explicitly exclude any unnoticed input fields that could silently change
    # the scope of a real transfer calculation. No bool-as-int or float money.
    required = {
        'kind','isa_expiry_date','pension_deposit_date',
        'isa_balance_at_expiry_krw','pension_deposit_from_isa_krw',
        'prior_transfers_from_same_isa_krw','previously_used_extra_base_krw',
    }
    if set(scenario)!=required:
        raise InvalidInput('V26_ISA_INPUT_FIELDS_DRIFT')
    expiry=_literal_date(scenario['isa_expiry_date'],'expiry')
    deposit=_literal_date(scenario['pension_deposit_date'],'deposit')
    current=_literal_date(current_as_of,'current_as_of')
    if expiry>deposit or deposit>current:
        raise InvalidInput('V26_ISA_DATE_ORDER_INVALID')
    for key in ('isa_balance_at_expiry_krw','pension_deposit_from_isa_krw',
                'prior_transfers_from_same_isa_krw'):
        _whole_krw(scenario[key],key)
    _whole_krw(scenario['previously_used_extra_base_krw'],
               'previously_used_extra_base_krw',max_value=3000000)
    if (scenario['pension_deposit_from_isa_krw']
        + scenario['prior_transfers_from_same_isa_krw']
        > scenario['isa_balance_at_expiry_krw']):
        raise InvalidInput('V26_ISA_DEPOSIT_EXCEEDS_EXPIRY_BALANCE')
    if 'ISA_TRANSFER' not in _facet(question):
        raise InvalidInput('V26_ISA_QUESTION_FACET_MISSING')
    return expiry,deposit


def _linked_current_law(isa_law_review, chat_decisions, selected_claim_ids):
    if type(isa_law_review) is not dict or type(chat_decisions) is not list:
        raise InvalidInput('V26_CURRENT_ISA_RULE_REVIEW_MISSING')
    ids = isa_law_review.get('rule_ids')
    if type(ids) is not list or len(ids)!=2 or len(set(ids))!=2:
        raise InvalidInput('V26_CURRENT_ISA_TWO_RULES_REQUIRED')
    selected=set(selected_claim_ids)
    linked=set()
    for d in chat_decisions:
        if d.get('claim_id') in selected:
            if d.get('classification') in (
                'CURRENT_GENERAL_RULE_CONSISTENT_CONDITIONAL',
                'CURRENT_RULE_SCOPE_MISSING','CURRENT_RULE_CONTRADICTS_SOURCE',
            ):
                linked.update(d.get('rule_ids',[]))
    if not set(ids).issubset(linked):
        raise InvalidInput('V26_ISA_RULES_NOT_SUPPORTED_BY_SELECTED_CURRENT_REVIEW')


def evaluate_current_question_v26(root: Path, question: str, *, source, exchange,
                                  current_as_of: str, primary_evidence: list,
                                  chat_decisions: list, selected_claim_ids: list,
                                  relevance_decisions: list,
                                  candidate_dispositions: list,
                                  scenario: dict | None = None,
                                  isa_law_review: dict | None = None) -> dict:
    """Strict gate before any actual V5 P3 / P2 call through V25."""
    audit_host_atomic_exchange(source,exchange)
    census=audit_candidate_census(question,exchange,selected_claim_ids,
                                  candidate_dispositions,current_as_of)
    is_isa = type(scenario) is dict and scenario.get('kind')=='ISA_TRANSFER'
    if isa_law_review is not None and not is_isa:
        raise InvalidInput('V26_ISA_REVIEW_WITHOUT_ISA_SCENARIO')
    if is_isa:
        expiry,deposit=_isa_preflight(question,scenario,current_as_of=current_as_of)
        # With prior partial transfers there is no independent evidence of the
        # cumulative applied *extra deduction base*; abstain rather than trusting
        # an unverified used-amount field or double counting earlier tranches.
        prior = scenario['prior_transfers_from_same_isa_krw']
        used = scenario['previously_used_extra_base_krw']
        open_reason = (
            'PRIOR_TRANSFER_OR_CAP_CUSTODY_OPEN' if prior or used else
            'CROSS_TAX_YEAR_DEFER' if expiry.year!=deposit.year else
            None
        )
        if isa_law_review is not None:
            _linked_current_law(isa_law_review,chat_decisions,selected_claim_ids)
    else:
        open_reason=None

    # Never allow V25 itself to append an ISA figure; V26 alone controls
    # audited arithmetic. No legacy V5 ISA P2 scenario is invoked.
    actual_scenario = None if is_isa else scenario
    base = evaluate_current_question_v25(
        root,question,source=source,exchange=exchange,current_as_of=current_as_of,
        primary_evidence=primary_evidence,chat_decisions=chat_decisions,
        selected_claim_ids=selected_claim_ids,relevance_decisions=relevance_decisions,
        scenario=actual_scenario,isa_law_review=None,
    )
    if (base.get('p0_go') is not False or
        base.get('independent_question_to_claim_entailment_verified') is not False or
        base.get('personal_trade_or_tax_approval') is not False):
        raise InvalidInput('V26_INHERITED_APPROVAL_UNSAFE')
    illustration=None
    lines=[base['answer_text']]
    if is_isa:
        if isa_law_review is None:
            open_reason='CURRENT_ISA_LEGAL_TERMS_NOT_REVIEWED'
        elif base.get('selected_unresolved_claim_ids'):
            open_reason='SELECTED_CURRENT_LAW_CLAIMS_UNRESOLVED'
        if open_reason is not None:
            illustration={'status':open_reason,
                'illustrative_extra_deduction_base_krw':None,
                'actual_credit_krw':None,'actual_refund_krw':None,
                'personal_eligibility_verified':False}
            lines.append(
                'ISA 전환 추가 공제 대상 납입한도 산술은 과거 이전 내역, 과세연도, '
                '현행 근거 또는 개인별 적용 조건이 미확정되어 보류합니다.')
        else:
            illustration=illustrative_isa_extra_base(
                scenario,current_as_of=current_as_of,
                primary_evidence=primary_evidence,law_review=isa_law_review,
            )
            if illustration['status']!='SAME_YEAR_ILLUSTRATIVE_BASE_ONLY':
                raise InvalidInput('V26_UNEXPECTED_LEGACY_ISA_CALC_STATUS')
            lines.append(
                '검증되지 않은 사용자 가정과 현행 일반규정 발췌문 기준, '
                'ISA 추가 세액공제 **대상 납입한도**의 산술 예시: '
                f'{illustration["illustrative_extra_deduction_base_krw"]:,}원. '
                '이는 실제 세액공제액 또는 환급액이 아니며 납세자별 결론은 보류합니다.')
    return {**base,
            'schema':'IRE_V6_V26_CENSUS_AND_ISA_ACTION_GUARD',
            'answer_text':'\n'.join(lines),
            'source_candidate_census':census,
            'isa_extra_deduction_base_illustration':illustration,
            'isa_tax_calculation_quarantined_pending_current_evidence':True,
            'actual_isa_tax_credit_or_refund':None,
            'current_source_semantic_completeness_independently_verified':False,
            'full_original_atomic_recall_certified':False,
            'personal_trade_or_tax_approval':False,
            'p0_go':False,
            'status':'V26_CENSUS_COMPLETE_FOR_SUPPLIED_ATOMS_NO_PERSONAL_APPROVAL'}
