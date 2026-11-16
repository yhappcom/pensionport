"""V79: validate an owner-private V78 -> V79 disjoint shadow research delta.

Never infer V75 queue membership, independent accuracy, tax correctness, or P0 GO.
Public output contains only hashes/counts; actual notes and SRT stay owner-private.
"""
from __future__ import annotations
from copy import deepcopy
import json
import zipfile
from pathlib import Path
from v77_private_v33_replay import audit, sha, digest
from v78_shadow_source_custody import validate_rows, SCHEMA as V78_SCHEMA

SCHEMA = 'IRE_V6_V79_FIRST5_UNRECONCILED_SHADOW_MEANING_V1'
V78_BUNDLE_SHA = '76d8834f8bd4e8f3af2812948aeff5e15d0779b3eb87392d1a10d72d7ec24c98'
V78_RECORD_SHA = '866dc5376d54fd01098d900fb0182fe8c5a3597dbabc50b1a5bb9011859b1628'
V78_RECORD_FILENAME='V78_PRIVATE_20_SHADOW_SOURCE_MEANING_DO_NOT_UPLOAD_GITHUB.json'


def require(ok: bool, msg: str) -> None:
    if not ok: raise ValueError('V79_' + msg)


def source_key(r: dict):
    return (r['video_id'], r['window_id'], r['claim_id'])


def validate_delta(cuesbyvid, registry, previous_rows, new_rows, *,
                   prev_count=20, new_count=20, enforce_four_per_video=True):
    """Source-authenticated review provenance and exact V78/V79 non-overlap only."""
    require(type(previous_rows) is list and type(new_rows) is list, 'TWO_PRIVATE_RECORD_LISTS_REQUIRED')
    prev_receipt=validate_rows(cuesbyvid,registry,previous_rows,expected_count=prev_count,
                               enforce_four_per_video=enforce_four_per_video)
    require(all(type(r) is dict and r.get('schema')==SCHEMA for r in new_rows),'V79_NEW_SHADOW_SCHEMA_REQUIRED')
    # Reuse the already tested V78 source-only custody; this conversion occurs
    # in-memory and does NOT change any genuine V79 source row or approval flag.
    adapted=[]
    for r in new_rows:
        copy=deepcopy(r)
        copy['schema']=V78_SCHEMA
        adapted.append(copy)
    new_receipt=validate_rows(cuesbyvid,registry,adapted,expected_count=new_count,
                              enforce_four_per_video=enforce_four_per_video)
    old_keys={source_key(r) for r in previous_rows}
    new_keys={source_key(r) for r in new_rows}
    require(len(old_keys)==len(previous_rows) and len(new_keys)==len(new_rows), 'DUPLICATE_ORIGINAL_SOURCE_KEY')
    require(not (old_keys & new_keys), 'DUPLICATE_V78_V79_PARENT_SOURCE_KEY')
    require(all(r['source_status']=='SHADOW_UNRECONCILED_V75' for r in new_rows),'V75_MEMBERSHIP_NOT_RECONCILED')
    meta=[{'video_id':r['video_id'],'window_id':r['window_id'],'claim_id':r['claim_id'],
           'excerpt_sha256':r['source_excerpt_sha256'],'review_sha256':digest(r['speaker_units']),
           'guard_sha256':sha(r['reviewer_guard'].encode('utf-8'))} for r in previous_rows+new_rows]
    meta.sort(key=lambda a:(a['video_id'],a['window_id'],a['claim_id']))
    return {
        'schema':'IRE_V6_V79_OWNER_PRIVATE_V78_V79_UNRECONCILED_SHADOW_DELTA_SHA_ONLY_V1',
        'v78_previous_parents_source_authenticated':len(previous_rows),
        'v79_new_parents_source_authenticated':len(new_rows),
        'v78_v79_joint_distinct_source_parents':len(old_keys|new_keys),
        'v78_v79_overlap':len(old_keys&new_keys),
        'v78_previous_interpretations':prev_receipt['shadow_speaker_or_nonclaim_interpretations'],
        'v79_new_interpretations':new_receipt['shadow_speaker_or_nonclaim_interpretations'],
        'v78_v79_joint_interpretations':prev_receipt['shadow_speaker_or_nonclaim_interpretations']+new_receipt['shadow_speaker_or_nonclaim_interpretations'],
        'v79_reviewer_guards':len(new_rows),
        'v78_v79_joint_review_source_and_annotation_sha256':digest(meta),
        'v78_custody_digest_sha256':prev_receipt['source_and_review_custody_digest_sha256'],
        'v79_custody_digest_sha256':new_receipt['source_and_review_custody_digest_sha256'],
        'v75_private_queue_recovered':False,
        'v75_membership_verified':False,
        'v75_official_parent_count_increment':0,
        'v75_remaining_context_risk':298,
        'v75_other_p2_pending':501,
        'v75_p1_pending':88,
        'v75_total_remaining_unchanged':887,
        'historical_v40_event_chain_recovered':False,
        'independent_gold':False,
        'financial_truth_certified':False,
        'personal_advice_approved':False,
        'p0_go':False,
        'raw_private_source_or_annotation_published':False,
    }


def read_v78_anchor(v78_private_zip: Path, *, expected_zip_sha=V78_BUNDLE_SHA,
                    expected_records_sha=V78_RECORD_SHA):
    raw=Path(v78_private_zip).read_bytes()
    require(sha(raw)==expected_zip_sha,'V78_PREVIOUS_BUNDLE_SHA_MISMATCH')
    with zipfile.ZipFile(v78_private_zip) as z:
        require(z.testzip() is None,'V78_PRIVATE_ZIP_CORRUPT')
        names=z.namelist()
        require(len(names)==len(set(names)) and names.count(V78_RECORD_FILENAME)==1,'V78_RECORD_MISSING_OR_DUPLICATE')
        data=z.read(V78_RECORD_FILENAME)
    require(sha(data)==expected_records_sha,'V78_PREVIOUS_RECORD_SHA_MISMATCH')
    return json.loads(data.decode('utf-8'))


def private_replay(source_zip, v78_private_zip, v79_current_json):
    source, reg, cues=audit(source_zip)
    require(source['v42_cohort_digest_matches'] and source['total_v33_candidates']==1603 and
            source['total_windows']==130,'V77_V42_ORIGINAL_COHORT_FAILED')
    prev=read_v78_anchor(v78_private_zip)
    new=json.loads(Path(v79_current_json).read_text(encoding='utf-8'))
    return validate_delta(cues,reg,prev,new)