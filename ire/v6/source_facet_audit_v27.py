"""V27: conservative source-risk and omitted-same-facet gate over V26.

Structural negative controls only; question-to-claim entailment remains same-chat.
Historical V26/V25 source and original source data are not modified or exposed.
"""
from __future__ import annotations

from .atomic_exchange import audit_host_atomic_exchange
from .codec import json_digest
from .errors import InvalidInput
from .semantic_finance_decision_v25 import _facet
from .source_census_tax_guard_v26 import (
    audit_candidate_census, evaluate_current_question_v26,
)

def audit_source_facet_residuals(source, exchange, question, selected_claim_ids,
                                 candidate_dispositions, *, current_as_of):
    """Stop obvious omissions BEFORE V26 invokes V5 P3/P2.

    Every already-extracted same-facet atom must be selected. This is a
    deliberate fail-closed overapproximation; 'off-topic' is not a waiver.
    A relevant source cue joined across two neighboring subtitle boundaries
    must have at least one selected source anchor in that context neighborhood.
    """
    atomic = audit_host_atomic_exchange(source,exchange)
    if atomic['unresolved_cues']:
        raise InvalidInput('V27_UNRESOLVED_SOURCE_CUES')
    if atomic['suspicious_no_atom_cues']:
        raise InvalidInput('V27_FINANCIAL_OR_CONDITIONAL_CUE_UNEXTRACTED')
    census = audit_candidate_census(question,exchange,selected_claim_ids,
                                    candidate_dispositions,current_as_of)
    facets = _facet(question)
    if not facets:
        raise InvalidInput('V27_NO_SUPPORTED_FINANCE_FACET')
    selected = set(selected_claim_ids)
    same_facet_unselected = sorted(
        a['claim_id'] for a in exchange['atoms']
        if a['claim_id'] not in selected and
        (_facet(a['proposition']) & facets)
    )
    if same_facet_unselected:
        raise InvalidInput('V27_UNSELECTED_SAME_FACET_SOURCE_CLAIMS')
    selected_source_refs = {
        r['cue_index'] for a in exchange['atoms']
        if a['claim_id'] in selected
        for r in a['source_refs']
    }
    first, last = source.scope_first_cue,source.scope_last_cue
    # Split Korean ASR terms across consecutive cues can conceal topic terms
    # from one-cue lexical scanning. Inspect a local +/-1 cue neighborhood.
    # Only count neighborhoods with a financial facet under the actual question.
    risky_windows = 0
    for idx in range(first,last+1):
        lo, hi = max(first,idx-1),min(last,idx+1)
        segment = ' '.join(source.cues[j-1].text for j in range(lo,hi+1))
        if not (facets & _facet(segment)):
            continue
        risky_windows += 1
        if not any(j in selected_source_refs for j in range(lo,hi+1)):
            raise InvalidInput('V27_RELEVANT_SOURCE_SPAN_HAS_NO_SELECTED_ANCHOR')
    return {
        'schema':'IRE_V6_V27_QUESTION_SOURCE_RESIDUAL_AUDIT',
        'all_original_scoped_cues':atomic['original_scoped_cues_enumerated'],
        'already_extracted_candidates':atomic['proposed_atomic_claims'],
        'selected_candidates':len(selected),
        'suspicious_no_atom_cues':atomic['suspicious_no_atom_cues'],
        'unresolved_cues':atomic['unresolved_cues'],
        'same_facet_unselected_candidates':0,
        'question_related_source_windows':risky_windows,
        'v26_candidate_receipt_sha256':census['candidate_receipt_sha256'],
        'review_receipt_sha256':json_digest({
            'question':question,
            'source_sha256':source.source_sha256,
            'question_facets':sorted(facets),
            'selected_claim_ids':sorted(selected),
            'atomic_candidate_digest':atomic['atom_candidate_digest'],
            'candidate_receipt_sha256':census['candidate_receipt_sha256'],
        }),
        'same_chat_semantic_truth_only':True,
        'independent_human_gold_verified':False,
        'all_real_original_atoms_extracted':False,
        'personal_financial_advice_approved':False,
        'p0_go':False,
    }

def evaluate_current_question_v27(root,question,*,source,exchange,current_as_of,
                                  primary_evidence,chat_decisions,selected_claim_ids,
                                  relevance_decisions,candidate_dispositions,
                                  scenario=None,isa_law_review=None):
    prior = audit_source_facet_residuals(
        source,exchange,question,selected_claim_ids,candidate_dispositions,
        current_as_of=current_as_of)
    base=evaluate_current_question_v26(
        root,question,source=source,exchange=exchange,
        current_as_of=current_as_of,primary_evidence=primary_evidence,
        chat_decisions=chat_decisions,selected_claim_ids=selected_claim_ids,
        relevance_decisions=relevance_decisions,
        candidate_dispositions=candidate_dispositions,
        scenario=scenario,isa_law_review=isa_law_review)
    if base.get('p0_go') is not False or base.get('personal_trade_or_tax_approval') is not False:
        raise InvalidInput('V27_FALSE_QUALITY_APPROVAL')
    return {**base,
            'schema':'IRE_V6_V27_SOURCE_FACET_AUDITED_DECISION',
            'source_facet_audit':prior,
            'source_semantic_recall_independently_verified':False,
            'personal_trade_or_tax_approval':False,
            'p0_go':False,
            'status':'V27_SOURCE_FACET_NEGATIVE_CONTROLS_ONLY_P0_NO_GO'}
