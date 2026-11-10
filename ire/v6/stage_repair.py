"""Audit explicit chat-only atom splits and source-linked risk dispositions.

This preserves all heuristic alerts. It cannot independently verify meaning,
financial facts, reviewer identity, or blind gold. No raw transcript in receipt.
"""
from __future__ import annotations

from .atomic_exchange import audit_host_atomic_exchange
from .codec import canonical, json_digest, sha256
from .errors import InvalidInput
from .semantic_risk import audit_semantic_risks


def audit_chat_atom_splits(source, before, after, split_records, added_claim_ids):
    """Reject silent revision and unjustified atom splits (structure only)."""
    base = audit_host_atomic_exchange(source, before)
    new = audit_host_atomic_exchange(source, after)
    if (before['video_id'] != after['video_id'] or
            before['source_sha256'] != after['source_sha256'] or
            before['manifest_sha256'] != after['manifest_sha256']):
        raise InvalidInput('CHAT_SPLIT_SOURCE_CHANGED')
    if (type(split_records) is not list or not split_records or
            type(added_claim_ids) is not list or
            added_claim_ids != sorted(set(added_claim_ids))):
        raise InvalidInput('CHAT_SPLIT_PLAN_INVALID')
    old = {a['claim_id']: a for a in before['atoms']}
    latest = {a['claim_id']: a for a in after['atoms']}
    retired, introduced = set(), set(added_claim_ids)
    for item in split_records:
        if (type(item) is not dict or set(item) != {'old_claim_id', 'new_claim_ids'} or
                type(item['new_claim_ids']) is not list or
                len(item['new_claim_ids']) < 2 or
                item['new_claim_ids'] != sorted(set(item['new_claim_ids']))):
            raise InvalidInput('CHAT_SPLIT_RECORD_INVALID')
        prior_id = item['old_claim_id']
        child_ids = item['new_claim_ids']
        if (prior_id not in old or prior_id in retired or prior_id in latest or
                any(cid in old or cid not in latest or cid in introduced
                    for cid in child_ids)):
            raise InvalidInput('CHAT_SPLIT_RETIRED_OR_CHILD_ID_DRIFT')
        retired.add(prior_id)
        introduced.update(child_ids)
        prior = old[prior_id]
        prior_anchors = {r['cue_index'] for r in prior['source_refs']}
        prior_context = set(prior['context_cue_indices'])
        anchors = set()
        propositions = set()
        for cid in child_ids:
            child = latest[cid]
            child_anchors = {r['cue_index'] for r in child['source_refs']}
            if (not child_anchors.issubset(prior_anchors) or
                    not set(child['context_cue_indices']).issubset(prior_context)):
                raise InvalidInput('CHAT_SPLIT_CHILD_ESCAPED_SOURCE_SCOPE')
            anchors.update(child_anchors)
            propositions.add(' '.join(child['proposition'].casefold().split()))
        if anchors != prior_anchors or len(propositions) != len(child_ids):
            raise InvalidInput('CHAT_SPLIT_ORIGINAL_ANCHORS_LOST_OR_DUPLICATED')
    if set(old) - set(latest) != retired:
        raise InvalidInput('CHAT_SPLIT_UNDECLARED_DELETION')
    if set(latest) - set(old) != introduced or introduced & set(old):
        raise InvalidInput('CHAT_SPLIT_UNDECLARED_ADDITION')
    for cid in set(old) & set(latest):
        if canonical(old[cid]) != canonical(latest[cid]):
            raise InvalidInput('CHAT_SPLIT_SILENT_OLD_CLAIM_REWRITE')
    return {
        'schema': 'IRE_V6_CHAT_ATOM_SPLIT_AUDIT_V1',
        'source_sha256': source.source_sha256,
        'before_candidate_digest': base['atom_candidate_digest'],
        'after_candidate_digest': new['atom_candidate_digest'],
        'split_records_digest': json_digest(split_records),
        'split_count': len(split_records),
        'retired_candidate_count': len(retired),
        'split_child_count': len(introduced) - len(added_claim_ids),
        'additional_missed_atom_count': len(added_claim_ids),
        'before_candidate_count': len(old), 'after_candidate_count': len(latest),
        'source_meaning_independently_verified': False,
        'chat_internal_score_is_blind_gold': False,
        'research_complete': False, 'p0_go': False,
    }


def review_chat_risk_cases(source, before, after, decisions):
    """Resolve ownership of *alerts*, not semantic truth or official law.

    Every original alert must be explicitly marked; unaltered cross-clause
    heuristic alerts stay in the raw V14 docket, with an attached chat-only
    explanation and a source-anchored related atom.
    """
    original = audit_semantic_risks(source, before)
    revised = audit_semantic_risks(source, after)
    if (before['source_sha256'] != after['source_sha256'] or
            before['manifest_sha256'] != after['manifest_sha256'] or
            before['video_id'] != after['video_id']):
        raise InvalidInput('CHAT_RISK_SOURCE_CHANGED')
    if type(decisions) is not list or len(decisions) != original['review_case_count']:
        raise InvalidInput('CHAT_RISK_INCOMPLETE_DECISIONS')
    lookup = {c['case_sha256']: c for c in original['review_cases']}
    after_lookup = {c['case_sha256']: c for c in revised['review_cases']}
    revised_atoms = {a['claim_id']: a for a in after['atoms']}
    resolved, scoped, open_case, seen = 0, 0, 0, set()
    remodeled_exception, remodeled_polarity, scoped_same_cue = 0, 0, 0
    for item in decisions:
        if (type(item) is not dict or set(item) != {
                'case_sha256', 'source_cue_sha256', 'decision', 'linked_claim_id',
                'reason'}):
            raise InvalidInput('CHAT_RISK_DECISION_SCHEMA_INVALID')
        cid = item['case_sha256']
        if cid not in lookup or cid in seen:
            raise InvalidInput('CHAT_RISK_UNKNOWN_OR_DUPLICATE_CASE')
        seen.add(cid)
        case = lookup[cid]
        index = case['cue_index']
        if (item['source_cue_sha256'] != sha256(source.cues[index-1].text.encode()) or
                type(item['reason']) is not str or
                not 12 <= len(item['reason'].strip()) <= 500):
            raise InvalidInput('CHAT_RISK_CUE_OR_RATIONALE_UNTRUSTED')
        kind, link = item['decision'], item['linked_claim_id']
        if kind == 'REMODELED_CONDITION':
            if (case['reason'] != 'UNMAPPED_CONDITION_IN_MODEL_CONTEXT' or
                    cid in after_lookup or link != case['claim_id'] or
                    link not in revised_atoms or
                    index not in revised_atoms[link]['condition_cue_indices']):
                raise InvalidInput('CHAT_RISK_CONDITION_NOT_REPAIRED')
            resolved += 1
        elif kind == 'REMODELED_EXCEPTION':
            if (case['reason'] != 'UNMAPPED_EXCEPTION_IN_MODEL_CONTEXT' or
                    cid in after_lookup or link != case['claim_id'] or
                    link not in revised_atoms or
                    index not in revised_atoms[link]['exception_cue_indices']):
                raise InvalidInput('CHAT_RISK_EXCEPTION_NOT_REPAIRED')
            resolved += 1
            remodeled_exception += 1
        elif kind == 'REMODELED_POLARITY':
            if (case['reason'] != 'SOURCE_NEGATION_POLARITY_REVIEW' or
                    cid in after_lookup or link != case['claim_id'] or
                    link not in revised_atoms or
                    revised_atoms[link]['stance'] not in {
                        'NEGATED', 'CORRECTED', 'QUOTED', 'UNRESOLVED'} or
                    index not in {r['cue_index'] for r in revised_atoms[link]['source_refs']}):
                raise InvalidInput('CHAT_RISK_POLARITY_NOT_REPAIRED')
            resolved += 1
            remodeled_polarity += 1
        elif kind == 'CROSS_CLAUSE_CONTEXT':
            if (cid not in after_lookup or link == case['claim_id'] or
                    link not in revised_atoms or
                    index not in {r['cue_index'] for r in
                                  revised_atoms[link]['source_refs']}):
                raise InvalidInput('CHAT_RISK_CROSS_CLAUSE_EVIDENCE_MISSING')
            target = revised_atoms[link]
            if case['reason'] == 'UNMAPPED_CONDITION_IN_MODEL_CONTEXT':
                if (index not in target['condition_cue_indices'] or
                        target['stance'] != 'CONDITIONAL'):
                    raise InvalidInput('CHAT_RISK_UNMAPPED_CONDITION_CARRIER_MISSING')
            elif case['reason'] == 'NEARBY_CORRECTION_NOT_IN_CONTEXT':
                if target['stance'] not in {'NEGATED', 'CORRECTED', 'UNRESOLVED'}:
                    raise InvalidInput('CHAT_RISK_NEIGHBOR_NEGATION_CARRIER_MISSING')
            else:
                raise InvalidInput('CHAT_RISK_CROSS_CLAUSE_REASON_INVALID')
            scoped += 1
        elif kind == 'SAME_CUE_DISTINCT_CLAUSES':
            # A source cue can contain two sentences with different stances.
            # Both verbatim quotes must be *separate, nonoverlapping spans* of
            # that same independently pinned original cue. Keep the raw alert.
            if (case['reason'] != 'CONFLICTING_STANCES_ON_SAME_SOURCE_CUE' or
                    cid not in after_lookup or case['claim_id'] is not None or
                    link not in revised_atoms):
                raise InvalidInput('CHAT_RISK_SAME_CUE_CONFLICT_NOT_GROUNDED')
            refs_here = [(atom['claim_id'], atom['stance'], r['quote'])
                         for atom in after['atoms'] for r in atom['source_refs']
                         if r['cue_index'] == index]
            if len(refs_here) != 2 or link not in {r[0] for r in refs_here}:
                raise InvalidInput('CHAT_RISK_SAME_CUE_TWO_CLAIMS_REQUIRED')
            stances = {r[1] for r in refs_here}
            if 'AFFIRMED' not in stances or not stances.intersection({'NEGATED', 'CORRECTED'}):
                raise InvalidInput('CHAT_RISK_SAME_CUE_OPPOSITE_STANCES_REQUIRED')
            raw = source.cues[index-1].text
            offsets = []
            for _, _, quote in refs_here:
                start = raw.find(quote)
                if start < 0 or raw.find(quote, start + 1) >= 0 or quote == raw:
                    raise InvalidInput('CHAT_RISK_SAME_CUE_UNIQUE_SPAN_REQUIRED')
                offsets.append((start,start + len(quote)))
            if not (offsets[0][1] <= offsets[1][0] or
                    offsets[1][1] <= offsets[0][0]):
                raise InvalidInput('CHAT_RISK_SAME_CUE_SPANS_OVERLAP')
            scoped += 1
            scoped_same_cue += 1
        elif kind == 'OPEN':
            if cid not in after_lookup:
                raise InvalidInput('CHAT_RISK_OPEN_BUT_ALREADY_DISAPPEARED')
            open_case += 1
        else:
            raise InvalidInput('CHAT_RISK_DECISION_UNKNOWN')
    unassessed_new = set(after_lookup) - set(lookup)
    return {
        'schema': 'IRE_V6_CHAT_SEMANTIC_CASE_REVIEW_V1',
        'source_sha256': source.source_sha256,
        'before_candidate_digest': original['atom_candidate_digest'],
        'after_candidate_digest': revised['atom_candidate_digest'],
        'before_case_census_sha256': original['case_census_sha256'],
        'after_case_census_sha256': revised['case_census_sha256'],
        'decision_digest': json_digest(decisions),
        'original_alert_count': len(lookup),
        'directly_remodeled_alerts': resolved,
        'remodeled_exception_alerts': remodeled_exception,
        'remodeled_polarity_alerts': remodeled_polarity,
        'same_cue_distinct_clause_alerts_raw_still_present': scoped_same_cue,
        'cross_clause_scoped_alerts_raw_still_present': scoped,
        'declared_open_alerts': open_case,
        'unreviewed_new_alerts': len(unassessed_new),
        'outstanding_chat_triage_count': open_case + len(unassessed_new),
        'raw_post_review_alert_count': revised['review_case_count'],
        'source_meaning_independently_verified': False,
        'chat_only_classification_not_financial_truth': True,
        'reviewer_identity_independently_verified': False,
        'research_complete': False, 'p0_go': False,
    }
