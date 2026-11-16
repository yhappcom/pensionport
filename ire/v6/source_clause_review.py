"""Append-only source-span audit of a chat-resolved same-cue contrast risk.

A lexical cue flag may mention '하지만' even when it belongs to the next atom.
This routine verifies source-only clause ownership and never certifies meaning,
current financial law, independent review, or model recall. Retain raw V14 case.
"""
from __future__ import annotations

import copy
import re

from .atomic_exchange import audit_host_atomic_exchange
from .codec import canonical, json_digest, sha256
from .errors import InvalidInput
from .semantic_risk import audit_semantic_risks

_CONNECTOR = re.compile(r"(?:하지만|그러나|반면|그런데|그렇지만)(?:\s|$)")
_END = re.compile(r"[.!?。！？]$")


def review_same_cue_contrast(source, before: dict, after: dict, *,
                             case_sha256: str, contrasting_claim_id: str) -> dict:
    """Source-pin two disjoint clauses without changing the old claim meaning.

    The old case remains in the raw heuristic docket, and this separate
    receipt records a later *chat-only* interpretation of clause ownership.
    A source-anchored apparent contrast is not a valid legal/financial fact.
    """
    old_audit = audit_host_atomic_exchange(source, before)
    new_audit = audit_host_atomic_exchange(source, after)
    if (before['video_id'] != after['video_id'] or
            before['source_sha256'] != after['source_sha256'] or
            before['manifest_sha256'] != after['manifest_sha256']):
        raise InvalidInput('CONTRAST_SOURCE_OR_MANIFEST_CHANGED')
    old_risk = audit_semantic_risks(source, before)
    new_risk = audit_semantic_risks(source, after)
    if type(case_sha256) is not str or type(contrasting_claim_id) is not str:
        raise InvalidInput('CONTRAST_CASE_OR_CLAIM_TYPE_INVALID')
    found = [c for c in old_risk['review_cases']
             if c['case_sha256'] == case_sha256]
    if len(found) != 1 or found[0]['reason'] != 'SOURCE_NEGATION_POLARITY_REVIEW':
        raise InvalidInput('CONTRAST_OLD_POLARITY_CASE_MISSING')
    case = found[0]
    cue_index = case['cue_index']
    owner_claim = case['claim_id']
    if (not owner_claim or contrasting_claim_id == owner_claim or
            case_sha256 not in {x['case_sha256'] for x in new_risk['review_cases']}):
        raise InvalidInput('CONTRAST_OLD_RAW_CASE_MUST_REMAIN')
    old_atoms = {a['claim_id']: a for a in before['atoms']}
    new_atoms = {a['claim_id']: a for a in after['atoms']}
    if (set(old_atoms) != set(new_atoms) or owner_claim not in old_atoms or
            contrasting_claim_id not in old_atoms):
        raise InvalidInput('CONTRAST_ATOM_IDENTITY_CHANGED')
    touched = {owner_claim, contrasting_claim_id}
    for cid in old_atoms:
        if cid not in touched:
            if canonical(old_atoms[cid]) != canonical(new_atoms[cid]):
                raise InvalidInput('CONTRAST_UNRELATED_CLAIM_REWRITTEN')
            continue
        old_c = copy.deepcopy(old_atoms[cid])
        new_c = copy.deepcopy(new_atoms[cid])
        prev = old_c.pop('source_refs')
        curr = new_c.pop('source_refs')
        if canonical(old_c) != canonical(new_c):
            raise InvalidInput('CONTRAST_CLAIM_MEANING_CHANGED')
        if ([r['cue_index'] for r in prev] !=
                [r['cue_index'] for r in curr]):
            raise InvalidInput('CONTRAST_SOURCE_REF_IDS_CHANGED')
        for previous, revised in zip(prev, curr):
            if (previous['cue_index'] != cue_index and previous != revised):
                raise InvalidInput('CONTRAST_DIFFERENT_CUE_REWRITTEN')
    owners = [(a['claim_id'], next((r['quote'] for r in a['source_refs']
                                    if r['cue_index'] == cue_index), None))
              for a in after['atoms'] if any(r['cue_index'] == cue_index
                                            for r in a['source_refs'])]
    if len(owners) != 2 or {cid for cid, _ in owners} != touched:
        raise InvalidInput('CONTRAST_EXACTLY_TWO_CUE_OWNERS_REQUIRED')
    raw = source.cues[cue_index - 1].text
    first = dict(owners)[owner_claim]
    second = dict(owners)[contrasting_claim_id]
    if (not first or not second or len(first.strip()) < 4 or len(second.strip()) < 4 or
            raw.count(first) != 1 or raw.count(second) != 1 or
            not _END.search(first.rstrip()) or not _CONNECTOR.match(second.lstrip())):
        raise InvalidInput('CONTRAST_TWO_DIRECT_CLAUSE_QUOTES_REQUIRED')
    start_a = raw.find(first)
    start_b = raw.find(second)
    if (start_a < 0 or start_b <= start_a + len(first) - 1 or
            raw[:start_a].strip() or raw[start_a + len(first):start_b].strip() or
            raw[start_b + len(second):].strip()):
        raise InvalidInput('CONTRAST_SOURCE_SPANS_OVERLAP_OR_GAP')
    return {
        'schema': 'IRE_V6_CHAT_SOURCE_CONTRAST_REVIEW_V20',
        'source_sha256': source.source_sha256,
        'manifest_sha256': source.manifest_sha256,
        'original_risk_case_sha256': case_sha256,
        'cue_text_sha256': sha256(raw.encode('utf-8')),
        'old_prediction_sha256': old_audit['atom_candidate_digest'],
        'reviewed_prediction_sha256': new_audit['atom_candidate_digest'],
        'exact_source_clause_shas': [sha256(first.encode('utf-8')),
                                      sha256(second.encode('utf-8'))],
        'reviewed_related_atom_count': 2,
        'original_case_still_in_raw_docket': True,
        'chat_source_scope_review_complete': True,
        'independent_semantic_truth_verified': False,
        'real_gold_available': False,
        'finance_rule_applicability_approved': False,
        'original_cohort_recall_verified': False,
        'research_complete': False,
        'p0_go': False,
    }
