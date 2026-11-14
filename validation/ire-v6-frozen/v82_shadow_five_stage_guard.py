"""Public-safe V82 source identity and fifth-generation shadow research custody.

This validates the private original SRT byte provenance and reviewed parent
lineage without publishing source text. This NEVER certifies semantic truth,
independent blind gold, V75 membership, historical V40 or personal advice.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json

from v77_private_v33_replay import audit, sha, digest
from v78_shadow_source_custody import validate_rows, SCHEMA as V78_SCHEMA
from v80_shadow_triplet_guard import load_pinned_private_rows, V78_BUNDLE_SHA, V78_RECORD, V78_RECORD_SHA, V79_BUNDLE_SHA, V79_RECORD, V79_RECORD_SHA
from v81_shadow_quad_guard import (validate_quad, V80_BUNDLE_SHA,V80_RECORD,V80_RECORD_SHA,SCHEMA as V81_SCHEMA)

SCHEMA='IRE_V6_V82_FIRST5_UNRECONCILED_SHADOW_MEANING_V1'
V81_BUNDLE_SHA='22f9327ad164ae4c03ac4c3b59a2e83a19c1d0e633ee9f5b73f6f55922515110'
V81_RECORD_SHA='5a50611d6c1b243187ac8362569762d995011d98c57b034a46a19fc1cbc19a54'
V81_RECORD='V81_PRIVATE_FIRST5_30_REAL_SOURCE_MEANING_NOT_PUBLIC.json'
EXPECTED_BY_VIDEO={1:8,2:6,3:6,4:5,5:5}
FLAGS=('fact_approved','independent_gold','personal_action_approved','v75_membership_verified','official_parent_merged')

def require(v, code):
    if not v: raise ValueError('V82_'+code)

def key(row):
    return row['video_id'],row['window_id'],row['claim_id']

def validate_five(cues,registry,v78,v79,v80,v81,v82,*,counts=(20,20,30,30,30),enforce_video_counts=True):
    """Validate all 5 ledgers, exact parent provenance, no cross-ledger duplication.

    All old private reviews are independently pinned in private_replay; the
    pure function below enables negative synthetic tests without source leaks.
    """
    require(type(counts) is tuple and len(counts)==5 and all(type(n) is int and n>0 for n in counts),'COUNTS_REQUIRED')
    generations=[v78,v79,v80,v81,v82]
    require(all(type(rows) is list for rows in generations),'FIVE_RECORD_LISTS_REQUIRED')
    prior=validate_quad(cues,registry,v78,v79,v80,v81,counts=counts[:4],enforce_video_counts=enforce_video_counts)
    require(len(v82)==counts[4],'NEW_PARENT_COUNT_DRIFT')
    require(all(type(x) is dict and x.get('schema')==SCHEMA for x in v82),'NEW_SCHEMA_DRIFT')
    adapted=[]
    for row in v82:
        c=deepcopy(row)
        c['schema']=V78_SCHEMA
        adapted.append(c)
    checked=validate_rows(cues,registry,adapted,expected_count=counts[4],enforce_four_per_video=False)
    if enforce_video_counts:
        require(checked['shadow_parents_by_video']==EXPECTED_BY_VIDEO,'VIDEO_CENSUS_DRIFT')
    sets=[]
    for rows in generations:
        keys=set(map(key,rows))
        require(len(keys)==len(rows),'INTRA_GENERATION_DUPLICATE')
        require(all(row.get('source_status')=='SHADOW_UNRECONCILED_V75' and
                    row.get('semantic_method')=='CHAT_CONTEXT_INTERPRETATION_NOT_GOLD' and
                    all(row.get(flag) is False for flag in FLAGS)
                    for row in rows),'FALSE_GOLD_OR_RESEARCH_APPROVAL')
        sets.append(keys)
    union=set().union(*sets)
    require(len(union)==sum(map(len,generations)),'CROSS_GENERATION_SOURCE_ID_COLLISION')
    meta=[{'stage':stage,'video_id':r['video_id'],'window_id':r['window_id'],
           'claim_id':r['claim_id'],'source_sha256':r['source_excerpt_sha256'],
           'units_sha256':digest(r['speaker_units']),
           'reviewer_guard_sha256':sha(r['reviewer_guard'].encode('utf-8'))}
          for stage,rows in zip((78,79,80,81,82),generations) for r in rows]
    meta.sort(key=lambda r:(r['video_id'],r['window_id'],r['claim_id']))
    n_new=checked['shadow_speaker_or_nonclaim_interpretations']
    return {
       'schema':'IRE_V6_V82_FIRST5_130_SOURCE_BOUND_245_INTERPRETATIONS_SHA_ONLY_V1',
       'actual_first_five_source_cues':5129,
       'original_40cue_windows':130,
       'source_provisional_speech_candidates':1603,
       'stage_parent_counts':{str(ver):len(rows) for ver,rows in zip((78,79,80,81,82),generations)},
       'stage_interpretations':{'78':prior['v78_semantic_or_nonclaim_units'],
            '79':prior['v79_semantic_or_nonclaim_units'],
            '80':prior['v80_semantic_or_nonclaim_units'],
            '81':prior['v81_semantic_or_nonclaim_units'],'82':n_new},
       'five_stage_unique_parent_reviews':len(union),
       'five_stage_source_parent_collisions':sum(map(len,generations))-len(union),
       'five_stage_meaning_or_nonclaim_units':prior['four_stage_semantic_or_nonclaim_units']+n_new,
       'v82_by_video':checked['shadow_parents_by_video'],
       'v82_source_custody_sha256':checked['source_and_review_custody_digest_sha256'],
       'five_stage_source_review_sha256':digest(meta),
       'v82_speech_act_counts':checked['speech_act_counts'],
       'v75_private_298_queue_bytes_recovered':False,
       'v75_original_404_parent_membership_verified':False,
       'official_v75_parent_count_increment':0,
       'v75_p2_context_escalated_pending_unchanged':298,
       'v75_p2_other_pending_unchanged':501,
       'v75_p1_complex_pending_unchanged':88,
       'v75_total_pending_unchanged':887,
       'historical_v40_108_canonical_events_recovered':False,
       'independent_gold':False,
       'financial_fact_truth_certified':False,
       'personal_advice_approved':False,
       'p0_go':False,
       'private_srt_or_annotation_published':False,
    }

def private_replay(source_zip,v78_zip,v79_zip,v80_zip,v81_zip,v82_json):
    census,registry,cues=audit(source_zip)
    require(census['v42_cohort_digest_matches'] and census['total_v33_candidates']==1603 and
            census['total_windows']==130 and census['source_cues_without_candidate']==104,'SOURCE_COHORT_DRIFT')
    records=[load_pinned_private_rows(p,h,n,rh) for p,h,n,rh in [
        (v78_zip,V78_BUNDLE_SHA,V78_RECORD,V78_RECORD_SHA),
        (v79_zip,V79_BUNDLE_SHA,V79_RECORD,V79_RECORD_SHA),
        (v80_zip,V80_BUNDLE_SHA,V80_RECORD,V80_RECORD_SHA),
        (v81_zip,V81_BUNDLE_SHA,V81_RECORD,V81_RECORD_SHA)]]
    records.append(json.loads(Path(v82_json).read_text(encoding='utf-8')))
    return validate_five(cues,registry,*records)