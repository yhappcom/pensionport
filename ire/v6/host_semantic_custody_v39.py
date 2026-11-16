"""V39: replay V33 speech grouping and V37 digests on owner-private SRT.

The ChatGPT host supplies classifications, but this custody audit only
checks original-byte identity, candidate coverage, source scope and metadata.
Never certify entailment, finance fact truth, blind gold or P0 GO.
No raw speech or semantic review prose is returned in the public receipt.
"""
from __future__ import annotations

from collections import Counter
import re

from .codec import json_digest, sha256
from .errors import InvalidInput
from .provisional_full_source_v33 import _draft_spans, _FILLER
from .source import parse_srt
from .source_window_host_screen_v37 import _NUMBER as _V37_NUMBER

_HEX = re.compile(r'[0-9a-f]{64}\Z')
_WINDOW = re.compile(r'W\d{5}\Z')
_CLAIM = re.compile(r'C\d{5}\Z')
_LABELS = {'C': 'ASSERTION_CHAT_PROPOSAL', 'H': 'HYPOTHETICAL_OR_EXAMPLE',
           'Q': 'QUESTION', 'A': 'ANECDOTE', 'R': 'RECOMMENDATION',
           'D': 'OTHER_SPEAKER_OR_REPORTED_SPEECH',
           'U': 'UNCERTAIN_ASR_OR_PROVIDER_HISTORY', 'X': 'REBUTTAL',
           'F': 'FRAGMENT_NOT_STANDALONE', 'T': 'HISTORICAL_RATE_OR_PERIOD'}
_WINDOW_KEYS = {'video_id', 'window_id', 'cue_first', 'cue_last',
                'original_window_text_sha256', 'v33_candidate_list_sha256'}
_VIDEO_KEYS = {'video_id', 'original_srt_sha256', 'cue_count'}
_ROW_KEYS = {'video_id', 'window_id', 'claim_id', 'cue_indices',
             'source_excerpt', 'source_excerpt_sha256', 'semantic_notes',
             'original_audio_verified', 'issuer_terms_verified',
             'finance_fact_certified', 'independent_gold'}
_NOTE_KEYS = {'kind', 'meaning'}


def _v33_draft_registry(cues):
    """Rebuild complete-video V33 candidate IDs and V37 list digest inputs."""
    count = 0
    found = {}
    for window_no, first in enumerate(range(1, len(cues) + 1, 40), 1):
        last = min(first + 39, len(cues))
        rows = []
        for indices in _draft_spans(cues, first, last, max_cues=7):
            entire = ' '.join(cues[i - 1].text for i in indices).strip()
            if len(entire) < 5 or (_FILLER.fullmatch(entire) and len(entire) < 16):
                continue
            valid = [i for i in indices if len(cues[i - 1].text.strip()) >= 2]
            if not valid:
                continue
            count += 1
            proposal = ' | '.join(cues[i - 1].text for i in valid)
            rows.append({'claim_id': f'C{count:05d}',
                         'source_text_sha256': sha256(proposal.encode('utf-8')),
                         'cue_indices': valid,
                         'numeric_tokens': sum(len(_V37_NUMBER.findall(cues[i - 1].text))
                                               for i in valid)})
        found[f'W{window_no:05d}'] = rows
    return found


def audit_host_semantic_custody_v39(original_srt_bytes, source_pins,
                                    window_pins, host_rows):
    """Fail closed on omitted/forged candidate reviews, but never grade meaning.

    original_srt_bytes is ephemeral private {video_id: bytes}. source_pins
    are independently precommitted SHA+cue totals. window_pins are independently
    pinned V37 window SHA and V33 candidate-list digest. Host original text
    and review reasons stay in private process memory; only hashes are emitted.
    Selected-window review does not imply all-video atomic completion.
    """
    if (type(original_srt_bytes) is not dict or not original_srt_bytes or
        type(source_pins) is not list or not source_pins or
        type(window_pins) is not list or not window_pins or
        type(host_rows) is not list or not host_rows):
        raise InvalidInput('V39_PRIVATE_SOURCE_AND_HOST_REVIEWS_REQUIRED')
    if any(type(k) is not str or type(v) is not bytes
           for k, v in original_srt_bytes.items()):
        raise InvalidInput('V39_PRIVATE_ORIGINAL_SRT_BYTES_REQUIRED')
    if len(source_pins) != len(original_srt_bytes):
        raise InvalidInput('V39_SOURCE_COHORT_CENSUS_MISMATCH')
    sources = {}
    registry = {}
    for p in source_pins:
        if (type(p) is not dict or set(p) != _VIDEO_KEYS or
            type(p['video_id']) is not str or p['video_id'] in sources or
            p['video_id'] not in original_srt_bytes or
            type(p['original_srt_sha256']) is not str or
            not _HEX.fullmatch(p['original_srt_sha256']) or
            type(p['cue_count']) is not int or p['cue_count'] <= 0):
            raise InvalidInput('V39_VIDEO_PIN_SCHEMA_OR_DUPLICATE')
        raw = original_srt_bytes[p['video_id']]
        if sha256(raw) != p['original_srt_sha256']:
            raise InvalidInput('V39_ORIGINAL_SRT_SHA_DRIFT')
        cues = parse_srt(raw)
        if len(cues) != p['cue_count']:
            raise InvalidInput('V39_ORIGINAL_CUE_CENSUS_DRIFT')
        sources[p['video_id']] = cues
        registry[p['video_id']] = _v33_draft_registry(cues)
    if set(sources) != set(original_srt_bytes):
        raise InvalidInput('V39_PINNED_SOURCE_VIDEO_SET_DRIFT')

    selected = {}
    candidates = {}
    for w in window_pins:
        if type(w) is not dict or set(w) != _WINDOW_KEYS:
            raise InvalidInput('V39_WINDOW_PIN_SCHEMA_INVALID')
        vid, wid = w['video_id'], w['window_id']
        if (vid not in sources or type(wid) is not str or
            not _WINDOW.fullmatch(wid) or (vid, wid) in selected or
            wid not in registry[vid]):
            raise InvalidInput('V39_WINDOW_PIN_DUPLICATE_OR_FOREIGN')
        first = (int(wid[1:]) - 1) * 40 + 1
        last = min(first + 39, len(sources[vid]))
        if (type(w['cue_first']) is not int or type(w['cue_last']) is not int or
            (w['cue_first'], w['cue_last']) != (first, last)):
            raise InvalidInput('V39_WINDOW_CUE_SCOPE_DRIFT')
        raw_window = ' '.join(c.text for c in sources[vid][first - 1:last])
        draft = registry[vid][wid]
        if (w['original_window_text_sha256'] != sha256(raw_window.encode('utf-8')) or
            w['v33_candidate_list_sha256'] != json_digest(draft)):
            raise InvalidInput('V39_V37_SOURCE_OR_V33_CANDIDATE_DIGEST_DRIFT')
        if not draft:
            raise InvalidInput('V39_WINDOW_NO_CANDIDATES')
        selected[(vid, wid)] = (first, last)
        for c in draft:
            candidates[(vid, wid, c['claim_id'])] = c

    reviewed = set()
    safe_rows = []
    totals = Counter()
    for row in host_rows:
        if type(row) is not dict or set(row) != _ROW_KEYS:
            raise InvalidInput('V39_HOST_REVIEW_SCHEMA_INVALID')
        vid, wid, cid = row['video_id'], row['window_id'], row['claim_id']
        if (type(cid) is not str or not _CLAIM.fullmatch(cid) or
            (vid, wid, cid) not in candidates):
            raise InvalidInput('V39_HOST_REVIEW_UNKNOWN_CANDIDATE')
        key = (vid, wid, cid)
        if key in reviewed:
            raise InvalidInput('V39_HOST_REVIEW_DUPLICATE_CANDIDATE')
        reviewed.add(key)
        draft = candidates[key]
        if row['cue_indices'] != draft['cue_indices']:
            raise InvalidInput('V39_HOST_CUE_REFERENCES_NOT_ORIGINAL_DRAFT')
        source_prose = ' | '.join(sources[vid][i - 1].text for i in draft['cue_indices'])
        if (type(row['source_excerpt']) is not str or
            row['source_excerpt'] != source_prose or
            row['source_excerpt_sha256'] != draft['source_text_sha256']):
            raise InvalidInput('V39_HOST_EXCERPT_NOT_ORIGINAL_BYTES')
        if any(row[flag] is not False for flag in (
                'original_audio_verified', 'issuer_terms_verified',
                'finance_fact_certified', 'independent_gold')):
            raise InvalidInput('V39_UNSUPPORTED_FACT_AUDIO_GOLD_CERTIFICATION')
        notes = row['semantic_notes']
        if type(notes) is not list or not 1 <= len(notes) <= 16:
            raise InvalidInput('V39_HOST_SEMANTIC_NOTES_REQUIRED')
        seen_notes = set()
        labels = Counter()
        public_note_rows = []
        for note in notes:
            if type(note) is not dict or set(note) != _NOTE_KEYS:
                raise InvalidInput('V39_HOST_SEMANTIC_NOTE_SCHEMA_INVALID')
            kind, meaning = note['kind'], note['meaning']
            if (type(kind) is not str or kind not in _LABELS or
                type(meaning) is not str or not 5 <= len(meaning.strip()) <= 1500):
                raise InvalidInput('V39_HOST_SEMANTIC_KIND_OR_REASON_INVALID')
            digest = sha256(meaning.encode('utf-8'))
            if (kind, digest) in seen_notes:
                raise InvalidInput('V39_DUPLICATE_MEANING_UNIT')
            seen_notes.add((kind, digest))
            labels[kind] += 1
            public_note_rows.append({'kind': kind, 'meaning_sha256': digest})
        if labels['F'] and len(notes) != 1:
            raise InvalidInput('V39_FRAGMENT_CANNOT_BE_CERTIFIED_MULTI_CLAIM')
        totals['host_reviewed_candidates'] += 1
        totals['chat_review_items'] += len(notes)
        totals['context_only_fragments'] += int(bool(labels['F']))
        totals['numeric_source_candidates'] += int(draft['numeric_tokens'] > 0)
        safe_rows.append({'video_id': vid, 'window_id': wid, 'claim_id': cid,
                          'cue_indices': draft['cue_indices'],
                          'source_text_sha256': draft['source_text_sha256'],
                          'numeric_original_token_count': draft['numeric_tokens'],
                          'chat_label_kinds': sorted(labels),
                          'chat_meaning_note_hashes': public_note_rows,
                          'financial_fact_independently_certified': False})
    if set(candidates) != reviewed:
        raise InvalidInput('V39_HOST_REVIEWS_MISSING_CANDIDATE')
    safe_rows.sort(key=lambda x: (x['video_id'], x['window_id'], x['claim_id']))
    receipt = {'schema': 'IRE_V6_V39_PRIVATE_ORIGINAL_CHAT_SEMANTIC_CUSTODY_HASH_ONLY',
               'original_video_count': len(sources),
               'selected_original_window_count': len(selected),
               'selected_original_cues': sum(last-first+1 for first,last in selected.values()),
               'exact_v33_candidates_source_pinned': len(candidates),
               'host_reviewed_candidates': totals['host_reviewed_candidates'],
               'chat_review_items_including_questions': totals['chat_review_items'],
               'context_only_fragments': totals['context_only_fragments'],
               'source_numeric_candidates': totals['numeric_source_candidates'],
               'selected_window_pins': sorted(window_pins, key=lambda x:(x['video_id'],x['window_id'])),
               'host_review_hash_rows': safe_rows,
               'private_original_source_or_review_text_in_receipt': False,
               'whole_130_windows_semantically_complete': False,
               'reviewer_independence_verified': False,
               'true_precision_recall_measured': False,
               'historical_audio_issuer_terms_verified': False,
               'financial_fact_truth_certified': False,
               'master_knowledge_auto_merge': False,
               'personal_finance_advice_approved': False,
               'p0_go': False}
    receipt['receipt_sha256'] = json_digest(receipt)
    return receipt
