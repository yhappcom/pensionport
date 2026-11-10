"""V31 ChatGPT-led finance evidence contract; deterministic engine is the auditor.

Flow (no external LLM API):
  private original -> source-bound host packet -> ChatGPT judges meaning and
  current official evidence -> deterministic completeness/provenance gates ->
  actual V27/V5 read-only education answer -> hash-only custody receipt.

No reviewer self-description, signed hash, same-chat verdict, or successful
software unit test grants INDEPENDENT semantic accuracy certification. Existing
V22-V30 are retained without modification.
"""
from __future__ import annotations

from pathlib import Path

from .atomic_exchange import audit_host_atomic_exchange
from .codec import json_digest, sha256
from .current_law_reassessment import audit_current_law_reassessment, _rules
from .errors import InvalidInput
from .private_replay_receipt_v29 import audit_elided_pension_basis_v29
from .semantic_risk import audit_semantic_risks
from .source_census_tax_guard_v26 import audit_candidate_census, _EXECUTE
from .source_facet_audit_v27 import (audit_source_facet_residuals,
                                     evaluate_current_question_v27)
from .source_quality_audit_v30 import _all_numeric_occurrences
from .advisory_decision_utility import _ACTION
from .temporal_finance_gate import _day

_MEANINGS = frozenset({
    'SUPPORTED_WITH_CONTEXT', 'SOURCE_SCOPE_OVERSTATED',
    'SOURCE_INCORRECT_CURRENT', 'QUESTION_OR_QUOTATION_ONLY', 'UNRESOLVED',
})
_RELATIONS = frozenset({
    'UNREVIEWED', 'NO_MATCH_FOUND_CHAT_ONLY', 'POSSIBLE_RELATION_PENDING',
    'SUPPORTS_PRIOR_CHAT_ONLY', 'REFINES_PRIOR_CHAT_ONLY',
    'CONFLICTS_PRIOR_CHAT_ONLY',
})
_PRIOR_WITH_ANCHOR = frozenset({
    'SUPPORTS_PRIOR_CHAT_ONLY', 'REFINES_PRIOR_CHAT_ONLY',
    'CONFLICTS_PRIOR_CHAT_ONLY',
})
_LAW_CONTRADICTS = 'CURRENT_RULE_CONTRADICTS_SOURCE'
_LAW_SCOPE = 'CURRENT_RULE_SCOPE_MISSING'
_LAW_CONDITIONAL = 'CURRENT_GENERAL_RULE_CONSISTENT_CONDITIONAL'
_LAW_UNKNOWN = 'CURRENT_FACT_OR_APPLICABILITY_UNKNOWN'
_LAW_NONREG = 'NOT_A_REGULATORY_CLAIM'


def prepare_private_chat_packet_v31(source, exchange, *, current_as_of,
                                    primary_evidence=None, start_index=0,
                                    max_claims=25):
    """Private-only chunked packet for the ChatGPT host, NEVER for public GitHub.

    Original exact quotes and official excerpts belong only in an authorized
    chat context. Empty evidence means *research it*; absence is not proof.
    """
    audit = audit_host_atomic_exchange(source, exchange)
    asof = _day(current_as_of, 'V31_CURRENT_ASOF').isoformat()
    if (type(start_index) is not int or type(max_claims) is not int or
        not 0 <= start_index < len(exchange['atoms']) or not 1 <= max_claims <= 25):
        raise InvalidInput('V31_PRIVATE_PACKET_SLICE_INVALID')
    if primary_evidence is None:
        primary_evidence = []
    if type(primary_evidence) is not list:
        raise InvalidInput('V31_EVIDENCE_FORMAT_INVALID')
    rules = _rules(_day(asof, 'V31_CURRENT_ASOF'), primary_evidence) if primary_evidence else {}
    subset = exchange['atoms'][start_index:start_index+max_claims]
    packet = {
        'schema': 'IRE_V6_V31_PRIVATE_CHAT_FINANCE_REVIEW_PACKET',
        'video_id': source.video_id,
        'source_sha256': source.source_sha256,
        'manifest_sha256': source.manifest_sha256,
        'atom_candidate_digest': audit['atom_candidate_digest'],
        'current_as_of': asof,
        'start_index': start_index,
        'original_candidate_count': len(exchange['atoms']),
        'original_claims': [{
            'claim_id': a['claim_id'],
            'claim_frame_sha256': json_digest(a),
            'kind': a['kind'], 'stance': a['stance'], 'speaker': a['speaker'],
            'proposition': a['proposition'],
            'original_cues': [{'cue_index': r['cue_index'], 'quote': r['quote']}
                              for r in a['source_refs']],
            'condition_cue_indices': a['condition_cue_indices'],
            'exception_cue_indices': a['exception_cue_indices'],
            'numeric_references': a['numeric_references'],
        } for a in subset],
        'known_official_evidence': [{
            'rule_id': e['rule_id'], 'source_url': e['source_url'],
            'effective_from': e['effective_from'], 'effective_to': e['effective_to'],
            'current_rule_status': rules[e['rule_id']]['status'],
            'excerpt': e['excerpt'], 'scope_note': e['scope_note'],
        } for e in primary_evidence],
        'next_start_index': (start_index+len(subset)
                             if start_index+len(subset)<len(exchange['atoms']) else None),
        'host_instructions': (
            'Analyze every original claim, speaker, modality, negation, condition, '
            'exception, numeric unit and cross-cue context. Look up currently '
            'effective official Korean financial regulations using ChatGPT search; '
            'record exact source URL, retrieval date, effective date and missing '
            'conditions. Compare approved prior knowledge by actual claim identity, '
            'not topical similarity. Unknown -> unresolved. Return review decisions '
            'for deterministic validation. Do not claim independent blind gold.'
        ),
        'private_not_for_github': True,
        'api_model_call_performed': False,
        'independent_evaluation': False,
        'p0_go': False,
    }
    packet['packet_sha256'] = json_digest(packet)
    return packet


def _review_list(reviews, known, asof, *, relation=False):
    if type(reviews) is not list or len(reviews)>len(known):
        raise InvalidInput('V31_HOST_REVIEW_LIST_INVALID')
    out={}
    required = ({'claim_id','claim_frame_sha256','relation','master_claim_id',
                 'master_atom_sha256','reason','reviewer','reviewed_as_of'} if relation else
                {'claim_id','claim_frame_sha256','source_cue_sha256',
                 'source_kind','source_stance','source_speaker',
                 'reviewed_condition_cue_indices','reviewed_exception_cue_indices',
                 'numeric_scope_checked','meaning_verdict',
                 'reason','reviewer','reviewed_as_of'})
    for row in reviews:
        if type(row) is not dict or set(row)!=required:
            raise InvalidInput('V31_HOST_REVIEW_SCHEMA_INVALID')
        cid=row['claim_id']
        if cid not in known or cid in out:
            raise InvalidInput('V31_HOST_REVIEW_DUPLICATE_OR_FOREIGN_ATOM')
        atom=known[cid]
        if (row['claim_frame_sha256']!=json_digest({k:v for k,v in atom.items() if k!='_verified_source_cue_texts'}) or
            row['reviewer']!='CHATGPT_CURRENT_TURN' or
            row['reviewed_as_of']!=asof or
            type(row['reason']) is not str or
            not 20<=len(row['reason'].strip())<=900):
            raise InvalidInput('V31_HOST_REVIEW_HASH_DATE_OR_RATIONALE_DRIFT')
        if relation:
            cls=row['relation']
            if cls not in _RELATIONS:
                raise InvalidInput('V31_PRIOR_KNOWLEDGE_RELATION_INVALID')
            mid,msha=row['master_claim_id'],row['master_atom_sha256']
            if cls in _PRIOR_WITH_ANCHOR:
                if (type(mid) is not str or len(mid)>120 or
                    type(msha) is not str or len(msha)!=64 or
                    any(c not in '0123456789abcdef' for c in msha)):
                    raise InvalidInput('V31_PRIOR_KNOWLEDGE_ANCHOR_REQUIRED')
            elif mid is not None or msha is not None:
                raise InvalidInput('V31_UNANCHORED_PRIOR_KNOWLEDGE_MISMATCH')
        else:
            cls=row['meaning_verdict']
            if cls not in _MEANINGS:
                raise InvalidInput('V31_MEANING_VERDICT_UNKNOWN')
            expected_cues=[sha256(source_text.encode('utf-8')) for source_text
                           in (atom['_verified_source_cue_texts'])]
            # The source text is inserted into a local scratch copy; never
            # mutate original atom frames or persist the scratch dict.
            if (row['source_cue_sha256']!=expected_cues or
                row['source_kind']!=atom['kind'] or
                row['source_stance']!=atom['stance'] or
                row['source_speaker']!=atom['speaker'] or
                row['reviewed_condition_cue_indices']!=atom['condition_cue_indices'] or
                row['reviewed_exception_cue_indices']!=atom['exception_cue_indices'] or
                type(row['numeric_scope_checked']) is not bool):
                raise InvalidInput('V31_MEANING_SOURCE_CONTEXT_OR_NUMERIC_DRIFT')
            if atom['kind']=='QUESTION' and cls not in ('QUESTION_OR_QUOTATION_ONLY','UNRESOLVED'):
                raise InvalidInput('V31_QUESTION_CANNOT_BECOME_FACT')
            if atom['stance']=='QUOTED' and cls not in ('QUESTION_OR_QUOTATION_ONLY','UNRESOLVED'):
                raise InvalidInput('V31_QUOTED_SOURCE_CANNOT_BECOME_FACT')
        out[cid]=row
    return out


def audit_chat_evidence_v31(source, exchange, *, current_as_of,
                            primary_evidence, regulatory_decisions,
                            meaning_reviews, prior_knowledge_reviews):
    """Public-safe, source-first audit; chat judges finance, engine only verifies.

    A missing review means an OPEN queue. A complete same-chat review may be
    reused for *general education* only, never auto-inserted as approved 116
    knowledge or passed off as independent accuracy certification.
    """
    audit=audit_host_atomic_exchange(source,exchange)
    asof=_day(current_as_of,'V31_CURRENT_ASOF').isoformat()
    if audit['unresolved_cues'] or audit['suspicious_no_atom_cues']:
        raise InvalidInput('V31_ORIGINAL_SOURCE_CUE_FRONTIER_UNRESOLVED')
    if any(type(x) is not dict for x in exchange['atoms']):
        raise InvalidInput('V31_SOURCE_ATOM_MALFORMED')
    known={x['claim_id']:x for x in exchange['atoms']}
    # Use local deep-copy-free, separate transient dicts so the existing
    # canonical atom frames and source SHA commitments are never modified.
    scratch={}
    for cid,a in known.items():
        scratch[cid]={**a,'_verified_source_cue_texts':[
            source.cues[r['cue_index']-1].text for r in a['source_refs']]}
    semantic=_review_list(meaning_reviews,scratch,asof)
    prior=_review_list(prior_knowledge_reviews,known,asof,relation=True)
    legal=audit_current_law_reassessment(
        source,exchange,current_as_of=asof,
        primary_evidence=primary_evidence,chat_decisions=regulatory_decisions)
    law={r['claim_id']:r for r in legal['claim_review']}
    risks=audit_semantic_risks(source,exchange)
    nums=_all_numeric_occurrences(source,exchange)
    missing_numbers=[r for r in nums if not r['linked_claim_ids']]
    records=[]
    for cid in sorted(known):
        m=semantic.get(cid)
        lr=law[cid]
        prior_review=prior.get(cid)
        label='CHAT_REVIEW_REQUIRED'
        if (m is not None and lr['status'] not in
                ('CHATGPT_REVIEW_REQUIRED','OPEN_CHAT_OR_SOURCE_APPLICABILITY') and
            prior_review is not None and
            prior_review['relation'] not in ('UNREVIEWED','POSSIBLE_RELATION_PENDING') and
            m['meaning_verdict']!='UNRESOLVED' and
            (m['numeric_scope_checked'] or not known[cid]['numeric_references'])):
            cls=lr['classification']
            meaning=m['meaning_verdict']
            if cls==_LAW_CONTRADICTS and meaning not in (
                    'SOURCE_INCORRECT_CURRENT','SOURCE_SCOPE_OVERSTATED'):
                raise InvalidInput('V31_CURRENT_LAW_HOST_MEANING_CONTRADICTION')
            if cls==_LAW_SCOPE and meaning not in (
                    'SOURCE_SCOPE_OVERSTATED','SOURCE_INCORRECT_CURRENT'):
                raise InvalidInput('V31_SOURCE_SCOPE_MISSING_MEANING_NOT_ACKNOWLEDGED')
            if cls==_LAW_CONDITIONAL and meaning=='SOURCE_INCORRECT_CURRENT':
                raise InvalidInput('V31_CURRENT_LAW_CONSISTENCY_CONFLICT')
            if meaning=='QUESTION_OR_QUOTATION_ONLY':
                label='QUESTION_OR_QUOTE_NOT_VERIFIED_FACT'
            elif cls in (_LAW_CONTRADICTS,_LAW_SCOPE) or meaning in (
                    'SOURCE_INCORRECT_CURRENT','SOURCE_SCOPE_OVERSTATED'):
                label='CHAT_REVIEWED_CORRECTION_ONLY'
            else:
                label='CHAT_REVIEWED_GENERAL_EDUCATION'
        records.append({
            'claim_id':cid,
            'claim_frame_sha256':json_digest(known[cid]),
            'meaning_status':label,
            'current_law_status':lr['status'],
            'prior_relation_status':(prior_review['relation'] if prior_review else 'UNREVIEWED'),
            'reviewed_source_cue_count':len(known[cid]['source_refs']),
            'direct_fact_reuse_allowed':label=='CHAT_REVIEWED_GENERAL_EDUCATION',
            'corrective_education_only':label=='CHAT_REVIEWED_CORRECTION_ONLY',
            'independent_gold_verified':False,
        })
    source_pending=(bool(risks['review_case_count']) or bool(missing_numbers))
    if source_pending:
        for r in records:
            if r['meaning_status'] in ('CHAT_REVIEWED_GENERAL_EDUCATION',
                                      'CHAT_REVIEWED_CORRECTION_ONLY'):
                r['meaning_status']='SOURCE_RISK_OR_NUMERIC_LINK_PENDING'
                r['direct_fact_reuse_allowed']=False
                r['corrective_education_only']=False
    ready=sum(r['meaning_status'] in (
        'CHAT_REVIEWED_GENERAL_EDUCATION','CHAT_REVIEWED_CORRECTION_ONLY')
              for r in records)
    pending=sorted(r['claim_id'] for r in records if r['meaning_status'] not in
        ('CHAT_REVIEWED_GENERAL_EDUCATION','CHAT_REVIEWED_CORRECTION_ONLY',
         'QUESTION_OR_QUOTE_NOT_VERIFIED_FACT'))
    all_reviewed=(len(semantic)==len(known) and
                  len(prior)==len(known) and
                  len(regulatory_decisions)==len(known))
    state=('CHAT_EVIDENCE_REVIEWED_EDUCATIONAL_ONLY'
           if all_reviewed and not pending and not source_pending
           else 'PENDING_CHAT_EVIDENCE_OR_SOURCE_REPAIR')
    # Hash-only, non-sensitive audit. Never embed user/source/official text.
    receipt={
        'schema':'IRE_V6_V31_HOST_EVIDENCE_HASH_ONLY_REVIEW',
        'video_id':source.video_id,'source_sha256':source.source_sha256,
        'manifest_sha256':source.manifest_sha256,
        'candidate_digest':audit['atom_candidate_digest'],
        'current_as_of':asof,'candidate_claim_count':len(known),
        'host_meaning_review_count':len(semantic),
        'host_regulatory_review_count':len(regulatory_decisions),
        'host_knowledge_relation_review_count':len(prior),
        'source_risk_cases':risks['review_case_count'],
        'source_numeric_token_occurrences':len(nums),
        'unlinked_numeric_occurrences':len(missing_numbers),
        'chat_reviewed_education_or_correction_count':ready,
        'pending_candidate_ids':pending,
        'claim_review_rows':records,
        'host_meaning_input_sha256':json_digest(meaning_reviews),
        'host_regulatory_input_sha256':json_digest(regulatory_decisions),
        'host_prior_relation_input_sha256':json_digest(prior_knowledge_reviews),
        'source_risk_docket_sha256':risks['case_census_sha256'],
        'numeric_source_census_sha256':json_digest(nums),
        'current_law_review_sha256':legal['review_sha256'],
        'current_law_basis':'CURRENT_ASOF_CHAT_INSPECTED_NOT_PUBLISHER_AUTHENTICATED',
        'operational_research_ready':state=='CHAT_EVIDENCE_REVIEWED_EDUCATIONAL_ONLY',
        'automatic_master_116_knowledge_merge':False,
        'independent_human_accuracy_certified':False,
        'independent_gold_precision_recall_measured':False,
        'user_specific_tax_or_order_approved':False,'p0_go':False,
        'status':state,
    }
    receipt['receipt_sha256']=json_digest(receipt)
    return receipt


def evaluate_chat_question_v31(root:Path, question:str, *, source,exchange,
                               current_as_of,primary_evidence,regulatory_decisions,
                               meaning_reviews,prior_knowledge_reviews,
                               selected_claim_ids,relevance_decisions,
                               candidate_dispositions,scenario=None,
                               isa_law_review=None):
    """Question route: CHAT evidence first, old V27->V5 P3 only after gates.

    This function does not itself verify owner ZIP bytes. Use V28/V29 local
    pinned-original replay to instantiate source; do not fabricate provenance.
    """
    if type(question) is not str or not question.strip():
        raise InvalidInput('V31_QUESTION_REQUIRED')
    if _ACTION.search(question) or _EXECUTE.search(question):
        raise InvalidInput('V31_PERSONAL_FINANCIAL_EXECUTION_NOT_SUPPORTED')
    vetted=audit_chat_evidence_v31(
        source,exchange,current_as_of=current_as_of,
        primary_evidence=primary_evidence,
        regulatory_decisions=regulatory_decisions,
        meaning_reviews=meaning_reviews,
        prior_knowledge_reviews=prior_knowledge_reviews)
    if (type(selected_claim_ids) is not list or not selected_claim_ids or
        selected_claim_ids!=sorted(set(selected_claim_ids))):
        raise InvalidInput('V31_SELECTED_CLAIMS_INVALID')
    rows={r['claim_id']:r for r in vetted['claim_review_rows']}
    if any(cid not in rows or rows[cid]['meaning_status'] not in
           ('CHAT_REVIEWED_GENERAL_EDUCATION','CHAT_REVIEWED_CORRECTION_ONLY')
           for cid in selected_claim_ids):
        raise InvalidInput('V31_SELECTED_CHAT_EVIDENCE_NOT_RESOLVED')
    audit_candidate_census(question,exchange,selected_claim_ids,
                           candidate_dispositions,current_as_of)
    audit_source_facet_residuals(source,exchange,question,selected_claim_ids,
                                 candidate_dispositions,current_as_of=current_as_of)
    audit_elided_pension_basis_v29(source,exchange,question,selected_claim_ids)
    # Old V27/V26/V25 -> real V5 P3 and current-law answer execution.
    answer=evaluate_current_question_v27(
        Path(root),question,source=source,exchange=exchange,
        current_as_of=current_as_of,primary_evidence=primary_evidence,
        chat_decisions=regulatory_decisions,
        selected_claim_ids=selected_claim_ids,
        relevance_decisions=relevance_decisions,
        candidate_dispositions=candidate_dispositions,
        scenario=scenario,isa_law_review=isa_law_review)
    if answer.get('p0_go') is not False or answer.get(
            'personal_trade_or_tax_approval') is not False:
        raise InvalidInput('V31_OLD_ANSWER_UNSAFE_APPROVAL')
    receipt={
        'schema':'IRE_V6_V31_CHAT_LED_QUESTION_HASH_RECEIPT',
        'host_evidence_receipt_sha256':vetted['receipt_sha256'],
        'question_sha256':sha256(question.encode('utf-8')),
        'selected_claim_ids':selected_claim_ids,
        'question_candidate_census_sha256':json_digest(candidate_dispositions),
        'question_relevance_review_sha256':json_digest(relevance_decisions),
        'current_as_of':current_as_of,
        'final_answer_sha256':sha256(answer['answer_text'].encode('utf-8')),
        'educational_answer_executed':True,
        'private_original_bytes_replayed_in_this_call':False,
        'original_source_semantic_recall_independently_proven':False,
        'master_knowledge_auto_approved':False,
        'personal_tax_or_trade_approved':False,'p0_go':False,
    }
    receipt['receipt_sha256']=json_digest(receipt)
    return {**answer,
            'schema':'IRE_V6_V31_CHAT_LED_FINANCE_EDUCATIONAL_ANSWER',
            'v31_host_evidence_receipt':vetted,
            'v31_hash_only_answer_receipt':receipt,
            'operational_education_only':True,
            'independent_financial_accuracy_certified':False,
            'p0_go':False,
            'status':'V31_CHAT_REVIEWED_EDUCATIONAL_ANSWER_NOT_INDEPENDENT_GOLD'}
