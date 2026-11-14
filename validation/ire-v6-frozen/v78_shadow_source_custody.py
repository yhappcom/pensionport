"""V78 private ChatGPT shadow annotations: source/meaning boundary, NOT P0 approval.

Original SRT and annotated source phrases are supplied by owner at runtime and
never appear in the public SHA receipt. Does not infer V75 queue membership.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
import re
from pathlib import Path
from v77_private_v33_replay import audit, digest, sha

SCHEMA = 'IRE_V6_V78_FIRST5_UNRECONCILED_PRIVATE_SHADOW_MEANING_V1'
ACTS = {
    'QUESTION', 'REPORTED_QUESTION', 'HYPOTHETICAL', 'NUMERIC_HYPOTHETICAL',
    'SPEAKER_ADVICE_NOT_GENERAL_RULE', 'SPEAKER_OPINION', 'SPEAKER_EXPLANATION_UNVERIFIED',
    'SPEAKER_ASSERTION_UNVERIFIED', 'SPEAKER_INFERENCE', 'ASR_CONTEXT_OPEN',
    'CONDITIONAL', 'HISTORICAL_UNVERIFIED', 'RHETORICAL_QUESTION',
    'PERSONAL_ANECDOTE'
}
SAFE_FLAGS = ('fact_approved','independent_gold','personal_action_approved','v75_membership_verified','official_parent_merged')
ROW_FIELDS = {
    'schema','video_no','video_id','window_id','claim_id','cue_indices',
    'start_ms','end_ms','source_excerpt_private','source_excerpt_sha256','neighbor_cues_private',
    'speaker_units','reviewer_guard','source_status','semantic_method', *SAFE_FLAGS,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError('V78_' + message)


def validate_rows(cuesbyvid: dict, registry: dict, rows: list, *,
                  expected_count: int = 20, enforce_four_per_video: bool = True) -> dict:
    require(type(rows) is list and len(rows) == expected_count and expected_count >= 1,
            'SHADOW_REVIEW_COUNT_MISMATCH')
    indexed = {}
    vid_to_no = {}
    for no, (vid, cues) in enumerate(cuesbyvid.items(), 1):
        vid_to_no[vid] = no
        for wid, cs in registry[vid].items():
            for c in cs:
                k = (vid, wid, c['claim_id'])
                require(k not in indexed, 'DUPLICATE_ORIGINAL_REGISTRY_KEY')
                indexed[k] = c
    require(bool(indexed), 'ORIGINAL_REGISTRY_REQUIRED')
    keys = set()
    per_video = Counter()
    acts = Counter()
    safe_meta = []
    for r in rows:
        require(type(r) is dict and set(r) == ROW_FIELDS, 'ROW_SCHEMA_MISMATCH')
        k = r['video_id'], r['window_id'], r['claim_id']
        require(k in indexed, 'FOREIGN_ORIGINAL_PARENT')
        require(k not in keys, 'DUPLICATE_SHADOW_PARENT')
        keys.add(k)
        require(r['schema'] == SCHEMA, 'ROW_SCHEMA_INVALID')
        require(r['video_no'] == vid_to_no[r['video_id']], 'VIDEO_OWNERSHIP_MISMATCH')
        require(r['source_status'] == 'SHADOW_UNRECONCILED_V75', 'FALSE_COMPLETION_STATUS')
        require(r['semantic_method'] == 'CHAT_CONTEXT_INTERPRETATION_NOT_GOLD', 'FALSE_SEMANTIC_GOLD')
        require(all(r[k] is False for k in SAFE_FLAGS), 'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
        original = indexed[k]
        require(r['cue_indices'] == original['cue_indices'], 'ORIGINAL_CUE_INDEX_DRIFT')
        cues = cuesbyvid[r['video_id']]
        indices = r['cue_indices']
        require(type(indices) is list and bool(indices), 'EMPTY_ORIGINAL_CUE')
        excerpt = ' | '.join(cues[i-1].text for i in indices)
        require(r['source_excerpt_private'] == excerpt and
                r['source_excerpt_sha256'] == original['source_text_sha256'] == sha(excerpt.encode('utf-8')),
                'SOURCE_EXCERPT_OR_DIGEST_DRIFT')
        require(r['start_ms'] == cues[indices[0]-1].start_ms and
                r['end_ms'] == cues[indices[-1]-1].end_ms, 'TIME_FRAME_DRIFT')
        first, last = max(1, indices[0]-2), min(len(cues),indices[-1]+2)
        neighborhood = [{'cue_index':i,'start_ms':cues[i-1].start_ms,
                         'end_ms':cues[i-1].end_ms,'text_private':cues[i-1].text}
                        for i in range(first,last+1)]
        require(r['neighbor_cues_private'] == neighborhood, 'NEIGHBOR_OR_TIME_DRIFT')
        require(type(r['speaker_units']) is list and 1 <= len(r['speaker_units']) <= 4,
                'SPEAKER_UNITS_REQUIRED')
        for u in r['speaker_units']:
            require(type(u) is dict and set(u) == {'act','interpretation'} and
                    u['act'] in ACTS and type(u['interpretation']) is str and
                    12 <= len(u['interpretation']) <= 1200, 'SPEAKER_UNIT_INVALID')
            acts[u['act']] += 1
        require(type(r['reviewer_guard']) is str and 20 <= len(r['reviewer_guard']) <= 1800,
                'REVIEWER_GUARD_REQUIRED')
        per_video[r['video_no']] += 1
        safe_meta.append({
            'video_no':r['video_no'], 'video_id':r['video_id'],
            'window_id':r['window_id'], 'parent_id':r['claim_id'],
            'source_excerpt_sha256':r['source_excerpt_sha256'],
            'neighbor_sha256':digest(neighborhood),
            'interpretations_count':len(r['speaker_units']),
            'speaker_unit_digest_sha256':digest(r['speaker_units']),
            'reviewer_guard_sha256':sha(r['reviewer_guard'].encode('utf-8')),
            'official_reviewed':False,'unreconciled_v75':True,
        })
    if enforce_four_per_video:
        require(dict(per_video) == {1:4,2:4,3:4,4:4,5:4}, 'FOUR_PER_VIDEO_REQUIRED')
    safe_meta.sort(key=lambda x:(x['video_no'],x['window_id'],x['parent_id']))
    return {
        'schema':'IRE_V6_V78_PRIVATE_SHADOW_SOURCE_CUSTODY_SHA_ONLY_V1',
        'shadow_parents':len(rows),
        'shadow_speaker_or_nonclaim_interpretations':sum(acts.values()),
        'reviewer_risk_guards':len(rows),
        'shadow_parents_by_video':dict(sorted(per_video.items())),
        'speech_act_counts':dict(sorted(acts.items())),
        'source_and_review_custody_digest_sha256':digest(safe_meta),
        'private_source_text_published':False,
        'v75_298_queue_membership_verified':False,
        'may_overlap_v75_reviews':True,
        'new_official_unique_parent_reviews':0,
        'original_v75_context_pending':298,
        'original_total_pending':887,
        'financial_fact_truth_independently_certified':False,
        'personal_advice_approved':False,
        'p0_go':False,
    }


def audit_zip(source_zip: Path, private_annotation_json: Path) -> dict:
    corpus, reg, cues = audit(source_zip)
    require(corpus['v42_cohort_digest_matches'], 'V42_SOURCE_COHORT_SHA_DRIFT')
    rows = json.loads(private_annotation_json.read_text(encoding='utf-8'))
    return validate_rows(cues,reg,rows)