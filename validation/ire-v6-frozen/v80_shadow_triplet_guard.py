"""V80 public-safe source-bound audit of 30 new host shadow rows vs V78/V79.

No owner SRT, quoted speech, subjective annotations, or personal investor data
belongs in public Git. A successful audit is not finance fact certification,
external human gold, V75 queue reconciliation, or P0 authorization.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json,zipfile
from v77_private_v33_replay import sha,digest,audit
from v78_shadow_source_custody import validate_rows,SCHEMA as OLD_SCHEMA
from v79_shadow_delta_guard import validate_delta,SCHEMA as V79_SCHEMA

SCHEMA='IRE_V6_V80_FIRST5_UNRECONCILED_SHADOW_MEANING_V1'
V78_BUNDLE_SHA='76d8834f8bd4e8f3af2812948aeff5e15d0779b3eb87392d1a10d72d7ec24c98'
V78_RECORD_SHA='866dc5376d54fd01098d900fb0182fe8c5a3597dbabc50b1a5bb9011859b1628'
V78_RECORD='V78_PRIVATE_20_SHADOW_SOURCE_MEANING_DO_NOT_UPLOAD_GITHUB.json'
V79_BUNDLE_SHA='7bbdfe7387cf987d92011c14c9df2f410675d38bd6fd33d7b37cad1ce6d2ded1'
V79_RECORD_SHA='5d1253711af94f96bcef2b9e388a6e59b117f4dcb65b6b9c96cd975f3fc4ab9f'
V79_RECORD='V79_PRIVATE_20_SHADOW_SOURCE_MEANING_DO_NOT_UPLOAD_GITHUB.json'


def require(ok,message):
    if not ok:raise ValueError('V80_'+message)


def load_pinned_private_rows(bundle, bundle_sha, record_name, record_sha):
    b=Path(bundle).read_bytes()
    require(sha(b)==bundle_sha,'PRIOR_BUNDLE_BYTES_CHANGED')
    with zipfile.ZipFile(bundle) as z:
        names=z.namelist()
        require(z.testzip() is None,'PRIOR_BUNDLE_ZIP_CRC_ERROR')
        require(len(names)==len(set(names)) and names.count(record_name)==1,
                'PRIOR_BUNDLE_DUPLICATE_OR_MISSING_RECORD')
        # Prevent archive members that could become unsafe if someone later extracts.
        for info in z.infolist():
            n=info.filename
            require(n and not n.startswith(('/', '\\')) and '\\' not in n and
                    '..' not in n.split('/') and not any(p=='' for p in n.split('/')),
                    'PRIOR_BUNDLE_UNSAFE_PATH')
            require(((info.external_attr>>16)&0o170000)!=0o120000,'PRIOR_BUNDLE_SYMLINK')
        record=z.read(record_name)
    require(sha(record)==record_sha,'PRIOR_RECORD_HASH_MISMATCH')
    rows=json.loads(record.decode('utf-8'))
    require(isinstance(rows,list),'PRIOR_RECORD_LIST_REQUIRED')
    return rows


def key(row):
    return row['video_id'],row['window_id'],row['claim_id']


def validate_triplet(cues,registry,v78,v79,new,*,n78=20,n79=20,n80=30,
                     enforce_video_counts=True):
    """All 3 real source cohorts verified against exact V33 parent IDs and cue bytes."""
    require(type(v78) is list and type(v79) is list and type(new) is list,
            'RECORD_LISTS_REQUIRED')
    prior=validate_delta(cues,registry,v78,v79,prev_count=n78,new_count=n79,
                         enforce_four_per_video=enforce_video_counts)
    require(len(new)==n80 and n80>0,'NEW_SHADOW_COUNT_MISMATCH')
    require(all(isinstance(r,dict) and r.get('schema')==SCHEMA for r in new),
            'V80_SCHEMA_REQUIRED')
    adapted=[]
    for row in new:
        copied=deepcopy(row)
        copied['schema']=OLD_SCHEMA
        adapted.append(copied)
    rec=validate_rows(cues,registry,adapted,expected_count=n80,enforce_four_per_video=False)
    if enforce_video_counts:
        require(rec['shadow_parents_by_video']=={1:6,2:6,3:6,4:6,5:6},
                'SIX_PER_VIDEO_REQUIRED')
    keys78=set(map(key,v78));keys79=set(map(key,v79));keys80=set(map(key,new))
    require(len(keys78)==len(v78) and len(keys79)==len(v79) and len(keys80)==len(new),
            'VERSION_INTERNAL_DUPLICATE')
    require(not (keys78&keys79 or keys78&keys80 or keys79&keys80),
            'CROSS_VERSION_DUPLICATE_PARENT')
    require(all(r['source_status']=='SHADOW_UNRECONCILED_V75' for r in new),
            'V75_FALSE_LINEAGE_COMPLETION')
    unique=keys78|keys79|keys80
    meta=[{'video_id':r['video_id'],'window_id':r['window_id'],'claim_id':r['claim_id'],
           'source_sha256':r['source_excerpt_sha256'],
           'units_sha256':digest(r['speaker_units']),
           'guard_sha256':sha(r['reviewer_guard'].encode('utf-8')),
           'stage':r['schema']}
          for r in v78+v79+new]
    meta.sort(key=lambda a:(a['video_id'],a['window_id'],a['claim_id']))
    return {
        'schema':'IRE_V6_V80_V78_V79_V80_THREE_STAGE_OWNER_SOURCE_SHADOW_TRIPLET_SHA_ONLY_V1',
        'source_cohort_v33_count':1603,
        'source_cohort_original_40cue_windows':130,
        'v78_source_bound_parents':len(v78),
        'v79_source_bound_parents':len(v79),
        'v80_new_source_bound_parents':len(new),
        'three_stage_distinct_source_parents':len(unique),
        'three_stage_duplicate_source_parents':len(v78)+len(v79)+len(new)-len(unique),
        'v78_interpretations':prior['v78_previous_interpretations'],
        'v79_interpretations':prior['v79_new_interpretations'],
        'v80_new_interpretations':rec['shadow_speaker_or_nonclaim_interpretations'],
        'three_stage_interpretations':prior['v78_v79_joint_interpretations']+
                                     rec['shadow_speaker_or_nonclaim_interpretations'],
        'v80_reviewer_guards':len(new),
        'v80_source_custody_sha256':rec['source_and_review_custody_digest_sha256'],
        'three_stage_source_and_review_sha256':digest(meta),
        'source_first_review_only':True,
        'v75_private_298_queue_recovered':False,
        'v75_official_404_history_membership_verified':False,
        'v75_official_parent_count_increment':0,
        'v75_context_risk_pending_unchanged':298,
        'v75_other_p2_pending_unchanged':501,
        'v75_p1_pending_unchanged':88,
        'v75_total_pending_unchanged':887,
        'historical_v40_108_event_bytes_recovered':False,
        'independent_gold':False,
        'independent_finance_fact_accuracy_certified':False,
        'personal_advice_approved':False,
        'p0_go':False,
        'private_srt_or_annotation_published':False,
    }


def private_replay(original_srt_zip,v78_private_zip,v79_private_zip,new_json):
    census,registry,cues=audit(original_srt_zip)
    require(census['v42_cohort_digest_matches'] and census['total_v33_candidates']==1603
            and census['total_windows']==130,'V77_SOURCE_COHORT_MISMATCH')
    a=load_pinned_private_rows(v78_private_zip,V78_BUNDLE_SHA,V78_RECORD,V78_RECORD_SHA)
    b=load_pinned_private_rows(v79_private_zip,V79_BUNDLE_SHA,V79_RECORD,V79_RECORD_SHA)
    c=json.loads(Path(new_json).read_text(encoding='utf-8'))
    return validate_triplet(cues,registry,a,b,c)