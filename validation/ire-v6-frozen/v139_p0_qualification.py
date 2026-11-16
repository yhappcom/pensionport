"""V139 evidence-aware qualification and fail-closed P0 preflight.
This module NEVER approves or publishes financial knowledge; V123/V128 retain authority.
All precision/recall measurements require a genuine complete adjudicated goldset.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from collections import Counter

EXPECTED_CUE_COUNT=1481
EXPECTED_CHILDREN=13
LAST_CUE_COUNT=41

class EvidenceError(ValueError): pass


def score_atoms(*, gold=None, predicted=None, expected_cues=720, source_sha256=None):
    """Use exact adjudicated same-granularity identity sets.

    Abstain on missing complete independent gold; no selected-sample projection.
    Only certified source-aware one-to-one adjudication can produce TP/FP/FN.
    """
    hold={'status':'UNMEASURABLE_NO_COMPLETE_INDEPENDENT_GOLD', 'tp':None,'fp':None,
          'fn':None,'precision':None,'recall':None,'high_risk_fn':None,'p0_1_pass':False}
    if not isinstance(gold,dict) or not isinstance(predicted,dict):return hold
    must=('complete','external_independent','source_sha256','covered_cue_count','unit_schema','unit_ids','high_risk_unit_ids')
    if any(k not in gold for k in must):return hold
    if not gold['complete'] or not gold['external_independent']:return hold
    if gold['source_sha256']!=source_sha256 or predicted.get('source_sha256')!=source_sha256:return hold
    if gold['covered_cue_count']!=expected_cues or predicted.get('covered_cue_count')!=expected_cues:return hold
    if gold['unit_schema']!='ADJUDICATED_ATOMIC_PROPOSITION_V1' or predicted.get('unit_schema')!=gold['unit_schema']:return hold
    g=gold['unit_ids'];p=predicted.get('unit_ids')
    h=gold['high_risk_unit_ids']
    if not all(isinstance(x,list) and all(isinstance(k,str) and k for k in x) and len(set(x))==len(x) for x in (g,p,h)):
        return hold
    if not set(h)<=set(g):return hold
    tp=len(set(g)&set(p));fp=len(set(p)-set(g));fn=len(set(g)-set(p))
    precision=tp/(tp+fp) if tp+fp else 0.0
    recall=tp/(tp+fn) if tp+fn else 0.0
    high_risk_fn=len(set(h)-set(p))
    return {'status':'ADJUDICATED_GOLD_MEASURED','tp':tp,'fp':fp,'fn':fn,
            'precision':precision,'recall':recall,'high_risk_fn':high_risk_fn,
            'p0_1_pass':precision>=0.95 and recall>=0.98 and high_risk_fn==0}


def parent_preflight(children, *, actual_source_sha256, parent_review_receipt=None,
                     owner_db_attested=False, portfolio_connected=False):
    """Diagnostic only: never substitute for V128 ACID publication or V123 ChatGPT gate."""
    issues=[]
    if not isinstance(children,list) or len(children)!=EXPECTED_CHILDREN:
        issues.append('THIRTEEN_CHILDREN_REQUIRED')
    else:
        expected=1
        for i, child in enumerate(children,1):
            if not isinstance(child,dict) or child.get('segment_id')!=f'B{i:04d}':
                issues.append(f'CHILD_ID_{i}_MISMATCH');continue
            last=min(i*120,EXPECTED_CUE_COUNT)
            if child.get('first_cue')!=expected or child.get('last_cue')!=last:
                issues.append(f'CHILD_SCOPE_{i}_INVALID')
            if child.get('source_sha256')!=actual_source_sha256:
                issues.append(f'CHILD_SOURCE_{i}_MISMATCH')
            if child.get('v123_status')!='PASS':
                issues.append(f'CHILD_{i}_NOT_V123_PASS')
            if child.get('unresolved_cases')!=0:
                issues.append(f'CHILD_{i}_OPEN_OR_NOT_CONFIRMED')
            if not child.get('v123_receipt_sha256'):
                issues.append(f'CHILD_{i}_ACTUAL_RECEIPT_MISSING')
            expected=last+1
    if not isinstance(parent_review_receipt,dict) or parent_review_receipt.get('chat_validated_whole_parent') is not True:
        issues.append('PARENT_CHAT_FINAL_REVIEW_MISSING')
    if not owner_db_attested:issues.append('OWNER_DB_NOT_ATTESTED')
    # Even a zero-issue diagnostic is not an authorization; only V128 actual transaction can authorize.
    return {'status':'HOLD' if issues else 'READY_FOR_REAL_V128_TRANSACTION_REPLAY_NOT_PUBLISHED',
            'issues':issues,'diagnostic_ready':not issues,'publication_authorized':False,
            'formal_knowledge_published':0,'portfolio_connected':portfolio_connected and False,
            'p0_go':False}


def advisory_preflight(*, source_final_passed=False, knowledge_head_attested=False,
                       original_issuer_bytes_recalculated=False,
                       effective_date_checked=False, applicability_checked=False,
                       actual_v5_current_law_answer_executed=False,
                       investor_specific_facts_verified=False):
    checks={'SOURCE_V123_NOT_PASSED':source_final_passed,
            'APPROVED_KNOWLEDGE_HEAD_UNATTESTED':knowledge_head_attested,
            'OFFICIAL_ORIGINAL_BODY_NOT_REPLAYED':original_issuer_bytes_recalculated,
            'CURRENT_EFFECTIVE_DATE_NOT_CHECKED':effective_date_checked,
            'REGULATORY_AND_PERSONAL_SCOPE_UNCHECKED':applicability_checked,
            'V5_V23_REAL_E2E_NOT_EXECUTED':actual_v5_current_law_answer_executed,
            'INVESTOR_FACTS_NOT_VERIFIED':investor_specific_facts_verified}
    incomplete=[k for k,v in checks.items() if v is not True]
    return {'status':'HOLD' if incomplete else 'READY_FOR_SEPARATE_REAL_USER_ACCEPTANCE',
            'missing_gates':incomplete,
            'real_personal_advice_approved':False, 'personal_order_enabled':False,'p0_go':False}
