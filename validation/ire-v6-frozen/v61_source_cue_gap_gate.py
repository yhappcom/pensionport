"""V61: SHA-bound source cue coverage control; NOT atomic/factual approval.

Operator supplies a contextual classification for every omitted original SRT cue.
The gate only checks original-byte binding, census and metadata. It does NOT
decide whether the classification is semantically correct or an independent gold.
Original transcript and free-text operator reasons remain private.
"""
from __future__ import annotations

import re
from collections import Counter

from ire.v6.codec import VIDEO, json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.host_semantic_custody_v39 import _v33_draft_registry
from ire.v6.source import parse_srt

_HEX = re.compile(r'[a-f0-9]{64}\Z')
_VIDEO_KEYS = {'video_id', 'original_srt_sha256', 'cue_count'}
_REVIEW_KEYS = {
    'video_id', 'cue_index', 'original_cue_text_sha256', 'status',
    'neighbor_cue_indices', 'context_reason', 'source_audio_verified',
    'independent_gold',
}
_STATUSES = {
    'BACKCHANNEL_CONTEXT', 'GREETING_OR_CLOSING', 'NONVERBAL_CUE',
    'CONTINUATION_CONTEXT', 'QUESTION_TAIL_CONTEXT',
    'NEGATION_TAIL_CONTEXT', 'NUMERIC_UNIT_TAIL_CONTEXT',
    'STANCE_CONTEXT', 'UNRESOLVED_CONTEXT',
}
_MATERIAL = {
    'CONTINUATION_CONTEXT', 'QUESTION_TAIL_CONTEXT',
    'NEGATION_TAIL_CONTEXT', 'NUMERIC_UNIT_TAIL_CONTEXT',
    'STANCE_CONTEXT', 'UNRESOLVED_CONTEXT',
}


def audit_cue_coverage_v61(original_srt_bytes, source_pins, excluded_cue_reviews):
    """Rebuild V33 and fail closed on any omitted, duplicated or altered gap review."""
    if (type(original_srt_bytes) is not dict or not original_srt_bytes or
            type(source_pins) is not list or not source_pins or
            type(excluded_cue_reviews) is not list):
        raise InvalidInput('V61_SOURCE_PINS_AND_EXCLUDED_REVIEWS_REQUIRED')
    if any(type(k) is not str or type(v) is not bytes
           for k, v in original_srt_bytes.items()):
        raise InvalidInput('V61_PRIVATE_SOURCE_BYTES_REQUIRED')

    cues_by_video = {}
    found = {}
    for p in source_pins:
        if (type(p) is not dict or set(p) != _VIDEO_KEYS or
                type(p['video_id']) is not str or
                VIDEO.fullmatch(p['video_id']) is None or
                p['video_id'] in cues_by_video or
                p['video_id'] not in original_srt_bytes or
                type(p['cue_count']) is not int or p['cue_count'] < 1 or
                type(p['original_srt_sha256']) is not str or
                not _HEX.fullmatch(p['original_srt_sha256'])):
            raise InvalidInput('V61_SOURCE_PIN_SCHEMA_DUPLICATE_OR_FOREIGN')
        vid = p['video_id']
        raw = original_srt_bytes[vid]
        if sha256(raw) != p['original_srt_sha256']:
            raise InvalidInput('V61_ORIGINAL_SOURCE_HASH_DRIFT')
        cues = parse_srt(raw)
        if len(cues) != p['cue_count']:
            raise InvalidInput('V61_CUE_CENSUS_DRIFT')
        registry = _v33_draft_registry(cues)
        owner = {}
        total = 0
        for wid, rows in registry.items():
            for proposal in rows:
                total += 1
                for idx in proposal['cue_indices']:
                    if idx in owner:
                        raise InvalidInput('V61_DUPLICATE_PROVISIONAL_CUE_OWNERSHIP')
                    owner[idx] = (wid, proposal['claim_id'])
        excluded = {x.index for x in cues} - set(owner)
        found[vid] = dict(cues=len(cues), windows=len(registry),
                          candidates=total, assigned=len(owner), gaps=excluded)
        cues_by_video[vid] = cues
    if set(cues_by_video) != set(original_srt_bytes):
        raise InvalidInput('V61_SOURCE_COHORT_INCOMPLETE')

    seen = set()
    decisions = Counter()
    public_dispositions = []
    for r in excluded_cue_reviews:
        if type(r) is not dict or set(r) != _REVIEW_KEYS:
            raise InvalidInput('V61_DISPOSITION_SCHEMA_INVALID')
        vid, idx = r['video_id'], r['cue_index']
        if (type(vid) is not str or vid not in found or
                type(idx) is not int or idx not in found[vid]['gaps'] or
                (vid, idx) in seen):
            raise InvalidInput('V61_DISPOSITION_NOT_UNIQUE_UNREFERENCED_CUE')
        if (type(r['original_cue_text_sha256']) is not str or
                r['original_cue_text_sha256'] !=
                sha256(cues_by_video[vid][idx - 1].text.encode('utf-8'))):
            raise InvalidInput('V61_DISPOSITION_CUE_TEXT_SHA_DRIFT')
        if (type(r['status']) is not str or r['status'] not in _STATUSES or
                type(r['context_reason']) is not str or
                not 12 <= len(r['context_reason'].strip()) <= 800):
            raise InvalidInput('V61_CONTEXT_DISPOSITION_REASON_REQUIRED')
        if (type(r['neighbor_cue_indices']) is not list or
                not 1 <= len(r['neighbor_cue_indices']) <= 4 or
                any(type(i) is not int or i < 1 or
                    i > len(cues_by_video[vid]) or i == idx or
                    abs(i - idx) > 3 for i in r['neighbor_cue_indices']) or
                len(set(r['neighbor_cue_indices'])) !=
                len(r['neighbor_cue_indices'])):
            raise InvalidInput('V61_ADJACENT_CONTEXT_CUE_REQUIRED')
        if (r['source_audio_verified'] is not False or
                r['independent_gold'] is not False):
            raise InvalidInput('V61_UNSUPPORTED_AUDIO_GOLD_CERTIFICATION')
        seen.add((vid, idx))
        decisions[r['status']] += 1
        public_dispositions.append({
            'video_id': vid, 'cue_index': idx,
            'original_cue_text_sha256': r['original_cue_text_sha256'],
            'status': r['status'],
            'neighbor_cue_indices': r['neighbor_cue_indices'],
            'context_reason_sha256': sha256(r['context_reason'].encode('utf-8')),
        })
    expected = {(vid, idx) for vid, x in found.items() for idx in x['gaps']}
    if seen != expected:
        raise InvalidInput('V61_UNREVIEWED_OR_OMITTED_CUE_CONTEXT')
    per_video = []
    for vid in sorted(found):
        f = found[vid]
        per_video.append({
            'video_id': vid, 'source_cues': f['cues'],
            'original_windows': f['windows'],
            'v33_candidates': f['candidates'],
            'cues_referenced_by_v33': f['assigned'],
            'cues_not_referenced_by_v33': len(f['gaps']),
            'chat_context_dispositions': sum(1 for v, k in seen if v == vid),
        })
    public_dispositions.sort(key=lambda x: (x['video_id'], x['cue_index']))
    totals = {k: sum(v[k] for v in per_video) for k in (
        'source_cues', 'original_windows', 'v33_candidates',
        'cues_referenced_by_v33', 'cues_not_referenced_by_v33',
        'chat_context_dispositions',
    )}
    result = {
        'schema': 'IRE_V6_V61_FULL_SOURCE_V33_CUE_GAP_HOST_CUSTODY_HASH_ONLY',
        'video_count': len(cues_by_video), 'totals': totals,
        'per_video': per_video,
        'chat_disposition_kinds': dict(sorted(decisions.items())),
        'potentially_material_tail_dispositions':
            sum(decisions[x] for x in _MATERIAL),
        'dispositions_source_link_sha256': json_digest(public_dispositions),
        'private_srt_or_host_reasons_in_receipt': False,
        'provisional_speech_equals_atomic_claim_count': False,
        'host_disposition_independently_certified': False,
        'cue_gap_review_proves_no_missing_atomic_claims': False,
        'all_1603_provisional_utterances_atomized': False,
        'independent_gold': False, 'p0_go': False,
    }
    result['receipt_sha256'] = json_digest(result)
    return result
