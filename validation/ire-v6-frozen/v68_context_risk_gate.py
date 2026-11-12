"""V68: fail-closed source-bound risk escalation for Korean financial SRT.

Never equate lexical absence with non-financial semantics. This is a
review-queue guard, not an approved claim detector or independent gold.
Operates on PRIVATE SRT texts locally; public receipts contain SHA/counts only.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter


class SourceQualityError(ValueError):
    pass


FINANCIAL = re.compile(
    r"연금|추납|연기|세금|세액|과세|비과세|계좌|ISA|IRP|CMA|ETF|"
    r"수익|손실|배당|금리|이자|투자|주식|채권|상환|원금|공제|수령|납입|"
    r"평가|보험|환율|주택|만기", re.I,
)
MEASURE = re.compile(r"(?<!\d)\d+(?:[,.]\d+)?\s*(?:원|만|억|천|%|퍼센트|년|개월|만원|억원|배|주)", re.I)
STRONG = re.compile(
    r"추납|연금|ISA|IRP|세액|과세|비과세|"
    r"(?<!\d)\d+(?:[,.]\d+)?\s*(?:원|만원|억원|억|만|%|퍼센트)", re.I,
)
BUCKETS = {"P0_SCOPED_FINANCE", "P1_COMPLEX_OR_INVESTMENT", "P2_GENERAL_OR_CONTEXT"}


def _sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _jsha(obj):
    return _sha(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                           separators=(',', ':')))


def _key(row):
    return (row['video_id'], row['window_id'], row['claim_id'])


def risk_gate(source_census, pending_queue, cue_texts, *, expected_source=1603,
              expected_pending=1303, context_radius=2):
    """Check actual cue bytes and source ownership before escalating review.

    cue_texts: private mapping integer video_no -> sequence of original cue text.
    Returns (public_sha_only_receipt, PRIVATE_metadata_docket). Does not clear
    ANY still-unreviewed parent, regardless of its assigned P0/P1/P2 bucket.
    """
    if (type(source_census) is not list or type(pending_queue) is not list or
            type(cue_texts) is not dict or context_radius != 2 or
            type(expected_source) is not int or type(expected_pending) is not int):
        raise SourceQualityError('V68_EXACT_SOURCE_COHORT_REQUIRED')
    if len(source_census) != expected_source or len(pending_queue) != expected_pending:
        raise SourceQualityError('V68_INCOMPLETE_SOURCE_OR_PENDING_CENSUS')
    if not cue_texts or any(type(k) is not int or type(v) is not list or not v or
                           any(type(s) is not str for s in v)
                           for k, v in cue_texts.items()):
        raise SourceQualityError('V68_ORIGINAL_CUE_TEXT_REQUIRED')
    lookup = {}
    pvids = {}
    for row in source_census:
        if type(row) is not dict or not {
            'video_no', 'video_id', 'window_id', 'claim_id', 'cue_indices',
            'source_excerpt_private', 'source_excerpt_sha256', 'triage_bucket'
        }.issubset(row):
            raise SourceQualityError('V68_INVALID_SOURCE_ROW')
        n, indices, text = (row[k] for k in ('video_no', 'cue_indices', 'source_excerpt_private'))
        if (type(n) is not int or n not in cue_texts or
                type(indices) is not list or not indices or
                any(type(i) is not int or i < 1 or i > len(cue_texts[n]) for i in indices) or
                indices != sorted(set(indices)) or type(text) is not str or
                row['triage_bucket'] not in BUCKETS):
            raise SourceQualityError('V68_SOURCE_CUE_RANGE_INVALID')
        source = ' | '.join(cue_texts[n][i - 1] for i in indices)
        if source != text or _sha(source) != row['source_excerpt_sha256']:
            raise SourceQualityError('V68_SOURCE_EXCERPT_HASH_OR_TEXT_MISMATCH')
        key = _key(row)
        if key in lookup:
            raise SourceQualityError('V68_DUPLICATE_SOURCE_PARENT')
        if row['video_id'] in pvids and pvids[row['video_id']] != n:
            raise SourceQualityError('V68_VIDEO_ID_COLLISION')
        pvids[row['video_id']] = n
        lookup[key] = row
    if set(cue_texts) != {x['video_no'] for x in source_census}:
        raise SourceQualityError('V68_MISSING_OR_EXTRA_SOURCE_VIDEO')

    pending_keys = set()
    risk_docket = []
    counts = Counter()
    for row in pending_queue:
        if type(row) is not dict or not {
            'video_no', 'video_id', 'window_id', 'claim_id', 'cue_indices',
            'source_excerpt_private', 'source_excerpt_sha256', 'triage_bucket',
            'human_atomic_review_completed', 'independent_gold', 'approval_restricted'
        }.issubset(row):
            raise SourceQualityError('V68_PENDING_SOURCE_PROVENANCE_REQUIRED')
        key = _key(row)
        if key in pending_keys or key not in lookup:
            raise SourceQualityError('V68_FOREIGN_OR_DUPLICATE_PENDING_PARENT')
        original = lookup[key]
        for field in ('video_no', 'cue_indices', 'source_excerpt_private',
                      'source_excerpt_sha256', 'triage_bucket'):
            if row[field] != original[field]:
                raise SourceQualityError('V68_PENDING_SOURCE_OR_TRIAGE_DRIFT')
        if (row['human_atomic_review_completed'] is not False or
                row['independent_gold'] is not False or
                row['approval_restricted'] is not True):
            raise SourceQualityError('V68_UNVERIFIED_SOURCE_FRAUDULENTLY_APPROVED')
        pending_keys.add(key)
        n = row['video_no']
        indices = row['cue_indices']
        excerpt = row['source_excerpt_private']
        lower = max(1, min(indices) - context_radius)
        upper = min(len(cue_texts[n]), max(indices) + context_radius)
        vicinity = ' '.join(cue_texts[n][i - 1] for i in range(lower, upper + 1))
        direct = bool(FINANCIAL.search(excerpt) or MEASURE.search(excerpt))
        contextual = bool(FINANCIAL.search(vicinity) or MEASURE.search(vicinity))
        strong = bool(STRONG.search(excerpt))
        tier = ('DIRECT_ESCALATION' if direct else
                'CONTEXT_ONLY_ESCALATION' if contextual else 'PENDING_SOURCE_REVIEW')
        counts[row['triage_bucket'] + ':total'] += 1
        counts[row['triage_bucket'] + ':' + tier] += 1
        if strong:
            counts[row['triage_bucket'] + ':strong_direct'] += 1
        risk_docket.append({
            'video_no': n, 'video_id': row['video_id'], 'window_id': row['window_id'],
            'parent_id': row['claim_id'],
            'source_excerpt_sha256': row['source_excerpt_sha256'],
            'scope_within_cue_first': lower, 'scope_within_cue_last': upper,
            'context_sha256': _sha(vicinity),
            'priority_tier': tier,
            'strong_direct_signal': strong,
            'existing_triage_bucket': row['triage_bucket'],
            'approved_as_nonfinancial': False,
            'review_complete': False,
        })
    if len(pending_keys) != expected_pending:
        raise SourceQualityError('V68_MISSING_PENDING_PARENTS')
    risk_docket.sort(key=lambda x:(x['video_no'],x['window_id'],x['parent_id']))
    direct_p2 = counts['P2_GENERAL_OR_CONTEXT:DIRECT_ESCALATION']
    nearby_p2 = counts['P2_GENERAL_OR_CONTEXT:CONTEXT_ONLY_ESCALATION']
    p2_total = counts['P2_GENERAL_OR_CONTEXT:total']
    ret = {
        'schema': 'IRE_V6_V68_REAL_SOURCE_CONTEXT_QUALITY_FAIL_CLOSED_GUARD_SHA_ONLY',
        'source_provisional_parents': len(source_census),
        'source_parent_pending_review': len(pending_keys),
        'previous_reviewed_count_by_difference_not_independently_authenticated':
            len(source_census) - len(pending_keys),
        'p2_pending': p2_total,
        'p2_direct_financial_or_quantity_signal': direct_p2,
        'p2_additional_signal_only_within_2_original_cues': nearby_p2,
        'p2_total_context_escalated': direct_p2 + nearby_p2,
        'p2_remaining_without_keyword_signal_still_pending': p2_total-direct_p2-nearby_p2,
        'all_pending_claims_blocked_from_automatic_advice_use': True,
        'lexical_false_negatives_were_detected': nearby_p2 > 0,
        'finance_semantic_completeness_certified': False,
        'independent_gold': False,
        'actual_precision_recall_measured': False,
        'p0_go': False,
        'counts_by_prior_bucket_and_tier': dict(sorted(counts.items())),
        'parent_provenance_and_context_docket_sha256': _jsha(risk_docket),
        'no_private_source_text_in_public_receipt': True,
    }
    ret['receipt_sha256'] = _jsha(ret)
    return ret, risk_docket


def require_research_quality_for_advice(receipt):
    """No advisory promotion while original claims or independent gold unresolved."""
    if (type(receipt) is not dict or
            receipt.get('schema') !=
            'IRE_V6_V68_REAL_SOURCE_CONTEXT_QUALITY_FAIL_CLOSED_GUARD_SHA_ONLY'):
        raise SourceQualityError('V68_VERIFIED_PROVENANCE_RECEIPT_REQUIRED')
    raise SourceQualityError('V68_RESEARCH_NOT_INDEPENDENTLY_APPROVED_FOR_ADVICE')
