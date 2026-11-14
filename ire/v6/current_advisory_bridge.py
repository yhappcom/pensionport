"""V23 safe read-only adapter: execute actual V5 P3, then V22 current-law gate.

The original V5 result is not trusted as current law: old 2026-11-05 authority
snapshots are never copied into the CURRENT-law answer. The current-law gate
runs source-first with official evidence and active in-chat judgments only.
This additive V6 entrypoint is the REQUIRED current-law route on the V6 branch;
existing V5 entrypoints stay unchanged and are not globally monkey-patched.
No network calls, order execution, authority attestation or approval.
"""
from __future__ import annotations

from pathlib import Path

from ire.v5.advisory_answer_pipeline import answer as _v5_p3_answer
from .atomic_exchange import audit_host_atomic_exchange
from .codec import sha256, json_digest
from .current_law_reassessment import audit_current_law_reassessment
from .errors import InvalidInput

_CONTRA='CURRENT_RULE_CONTRADICTS_SOURCE'
_SCOPE='CURRENT_RULE_SCOPE_MISSING'
_CONDITIONAL='CURRENT_GENERAL_RULE_CONSISTENT_CONDITIONAL'
_UNKNOWN='CURRENT_FACT_OR_APPLICABILITY_UNKNOWN'
_NONREG='NOT_A_REGULATORY_CLAIM'


def answer_with_current_law(root: Path, question: str, *, source, exchange,
                            current_as_of: str, primary_evidence: list,
                            chat_decisions: list, selected_claim_ids: list,
                            scenario: dict | None = None) -> dict:
    """Call the real V5 P3 answer generator but publish only V22-screened text.

    The existing P3 answer is calculated and its SHA returned as lineage. It
    NEVER becomes current-law proof. A relevant original atom cannot disappear,
    and absent/unverified official facts cannot become approved user advice.
    """
    if type(question) is not str or not question.strip() or len(question)>4000:
        raise InvalidInput('V23_QUESTION_REQUIRED')
    audit_host_atomic_exchange(source,exchange)
    if (type(selected_claim_ids) is not list or not selected_claim_ids or
        len(selected_claim_ids)>50 or any(type(x) is not str for x in selected_claim_ids) or
        selected_claim_ids!=sorted(set(selected_claim_ids))):
        raise InvalidInput('V23_SELECTED_ATOMS_BAD_CENSUS')
    atom_ids={x['claim_id'] for x in exchange['atoms']}
    if not set(selected_claim_ids)<=atom_ids:
        raise InvalidInput('V23_FOREIGN_ATOM_ID')

    assessment=audit_current_law_reassessment(
        source,exchange,current_as_of=current_as_of,
        primary_evidence=primary_evidence,chat_decisions=chat_decisions)
    by_id={x['claim_id']:x for x in assessment['claim_review']}
    reviewed={x['claim_id']:x for x in chat_decisions}
    selected=[by_id[x] for x in selected_claim_ids]
    open_ids=[x['claim_id'] for x in selected if x['status'] in (
        'CHATGPT_REVIEW_REQUIRED','OPEN_CHAT_OR_SOURCE_APPLICABILITY')]
    verified_current_rules=assessment['official_references']

    # The actual V5 P3 function *must* run; this is not a mock retrieval.
    # Its dated text is intentionally NOT carried forward, avoiding stale-law
    # assertions being shown as the current answer.
    p3=_v5_p3_answer(Path(root),question,scenario)
    if (type(p3) is not dict or p3.get('schema')!='IRE_V5_P3_ANSWER_V1' or
        type(p3.get('answer_text')) is not str or
        p3.get('direct_order_or_personal_recommendation_approved') is not False):
        raise InvalidInput('V23_V5_P3_ANSWER_UNSAFE_OR_INVALID')
    if p3.get('question')!=question:
        raise InvalidInput('V23_V5_QUESTION_DRIFT')

    classes={x['classification'] for x in selected}
    if _CONTRA in classes:
        lead='현재 법령과 충돌하는 과거 영상의 단정이 있어 그대로 적용하면 안 됩니다.'
    elif _SCOPE in classes:
        lead='과거 영상의 설명에는 현재 제도의 적용 조건 또는 예외가 누락돼 있습니다.'
    elif open_ids:
        lead='현재 법령·사실 근거 또는 개인별 적용 조건이 충분하지 않아 판단을 보류합니다.'
    elif _CONDITIONAL in classes:
        lead='현재 일반 규정과 조건부로 부합하지만 개인별 적용을 확정할 수 없습니다.'
    else:
        lead='해당 영상 주장은 오늘의 법령 사실 단정과 구분하여 검토해야 합니다.'

    parts=[lead,
           f'기준일: {current_as_of}. 영상 게시일이 아니라 오늘의 시행 규정을 대조합니다.',
           '기존 V5 판단 영역은 참조했지만 과거 스냅샷의 법률 문구를 현행 근거로 그대로 전달하지 않습니다.']
    matched_urls=set()
    for row in selected:
        cid=row['claim_id']; cls=row['classification']
        if row['status']=='CHATGPT_REVIEW_REQUIRED':
            parts.append(f'- {cid}: 현행 법령과의 채팅 검토 미실시. 현재 결론에 사용하지 않습니다.')
            continue
        d=reviewed[cid]
        if cls==_UNKNOWN:
            parts.append(f'- {cid}: 사실 또는 개인 적용성 확인 보류. {d["reason"]}')
            continue
        if cls==_NONREG:
            parts.append(f'- {cid}: 세법 사실 단정이 아닌 교육·투자 의견. {d["reason"]}')
            continue
        urls=[]
        for rid in row['rule_ids']:
            ref=verified_current_rules[rid]
            if ref['status']!='EFFECTIVE_ON_CURRENT_ASOF_CHAT_PRIMARY_EXCERPT_ONLY':
                raise InvalidInput('V23_NONCURRENT_REFERENCE_IN_USER_ANSWER')
            urls.append(ref['url']); matched_urls.add(ref['url'])
        if not urls:
            raise InvalidInput('V23_LEGAL_VERDICT_WITHOUT_CURRENT_RULE')
        state={_CONTRA:'현행 일반 규정과 충돌 가능',
               _SCOPE:'적용 범위 누락',_CONDITIONAL:'조건부 일치'}[cls]
        suffix=(' 필요한 확인: '+', '.join(d['missing_conditions'])+'.') if d['missing_conditions'] else ''
        parts.append(f'- {cid} ({state}): {d["reason"]}{suffix} 공식 근거: '+ ' / '.join(urls))
    parts.append('위 비교는 공개 공식자료 발췌문과 ChatGPT의 내부 의미 판정입니다. '
                 '원문 발급기관 서명·개인 상황·실제 거래일을 인증한 법률 자문이나 '
                 '개인 투자 적합성 승인이 아닙니다. 실행·주문·송금은 하지 않습니다.')

    return {
        'schema':'IRE_V6_V5_P3_CURRENT_LAW_ANSWER_BRIDGE_V23',
        'answer_text':'\n'.join(parts),
        'current_as_of':current_as_of,
        'source_video_id':source.video_id,
        'source_sha256':source.source_sha256,
        'selected_claim_ids':selected_claim_ids,
        'selected_claim_count':len(selected),
        'selected_unresolved_claim_ids':open_ids,
        'reviewed_current_rule_claim_count':sum(x['classification'] in
            (_CONTRA,_SCOPE,_CONDITIONAL) for x in selected),
        'official_context_urls':sorted(matched_urls),
        'v5_p3_executed':True,
        'v5_p3_original_schema':p3['schema'],
        'v5_p3_legacy_answer_sha256':sha256(p3['answer_text'].encode('utf-8')),
        'v5_p3_origin_fact_ids':list(p3.get('fact_ids',[])),
        'v5_p3_domain_candidates':list(p3.get('domain_candidates',[])),
        'v5_p3_legacy_text_rendered_as_current_law':False,
        'current_law_reassessment_sha256':json_digest(assessment),
        'current_law_reviewed_claim_count':assessment['chat_reviewed_claims'],
        'current_law_all_claim_count':assessment['count_claims'],
        'question_to_claim_relevance_independently_verified':False,
        'official_primary_body_authenticity_verified':False,
        'independent_human_gold_verified':False,
        'personal_account_eligibility_or_tax_approved':False,
        'direct_order_or_personal_recommendation_approved':False,
        'p0_go':False,
        'status':'V5_EXECUTED_V22_CHAT_REVIEW_ONLY_NO_FINANCE_APPROVAL'
    }
