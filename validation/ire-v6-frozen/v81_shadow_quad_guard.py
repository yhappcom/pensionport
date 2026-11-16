"""V81 public-safe exact-source, four-generation V78-V81 review custody gate.

No owner text, notes, or personal investor data in this module or its public
receipts. This checks bytes, IDs, source spans, context and non-approval, NOT
semantic truth, historic V75 membership, independent gold, or P0 readiness.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
from v77_private_v33_replay import audit,sha,digest
from v78_shadow_source_custody import validate_rows,SCHEMA as V78_SCHEMA
from v80_shadow_triplet_guard import (validate_triplet,load_pinned_private_rows,
 V78_BUNDLE_SHA,V78_RECORD,V78_RECORD_SHA,V79_BUNDLE_SHA,V79_RECORD,V79_RECORD_SHA,
 SCHEMA as V80_SCHEMA)

SCHEMA='IRE_V6_V81_FIRST5_UNRECONCILED_SHADOW_MEANING_V1'
V80_BUNDLE_SHA='a7456404579000ebcc4a7426a9957ecd8b8466118667825d57fee46464e25760'
V80_RECORD_SHA='257f0f4e747dad3ff99f155d2c09de644e740ffa2a7661c0667daea5c03075f1'
V80_RECORD='V80_PRIVATE_FIRST5_30_REAL_SOURCE_SHADOW_MEANING_DO_NOT_UPLOAD_GITHUB.json'
EXPECTED_BY_VIDEO={1:8,2:6,3:6,4:5,5:5}
SAFE_FLAGS=('fact_approved','independent_gold','personal_action_approved',
            'v75_membership_verified','official_parent_merged')

def require(value,code):
    if not value:raise ValueError('V81_'+code)

def source_key(row):
    return row['video_id'],row['window_id'],row['claim_id']

def validate_quad(cues,registry,v78,v79,v80,v81,*,counts=(20,20,30,30),enforce_video_counts=True):
    """Recheck all 100 original V33 candidates against four independent private lineages."""
    require(type(counts) is tuple and len(counts)==4 and all(type(x) is int and x>0 for x in counts),
            'EXACT_FOUR_GENERATION_COUNTS_REQUIRED')
    require(all(type(x) is list for x in (v78,v79,v80,v81)),'FOUR_PRIVATE_RECORD_LISTS_REQUIRED')
    prior=validate_triplet(cues,registry,v78,v79,v80,n78=counts[0],n79=counts[1],n80=counts[2],enforce_video_counts=enforce_video_counts)
    require(len(v81)==counts[3],'NEW_PARENT_CENSUS_DRIFT')
    require(all(type(r) is dict and r.get('schema')==SCHEMA for r in v81),
            'NEW_SCHEMA_DRIFT')
    adapted=[]
    for r in v81:
        c=deepcopy(r)
        c['schema']=V78_SCHEMA
        adapted.append(c)
    checked=validate_rows(cues,registry,adapted,expected_count=counts[3],enforce_four_per_video=False)
    if enforce_video_counts:
        require(checked['shadow_parents_by_video']==EXPECTED_BY_VIDEO,'PER_VIDEO_PARENT_CENSUS_DRIFT')
    stage_rows=[v78,v79,v80,v81]
    sets=[]
    for version,rows in enumerate(stage_rows,78):
        keys=set(map(source_key,rows))
        require(len(keys)==len(rows),'INTERNAL_PARENT_DUPLICATE')
        # V78+V79+V80 were protected independently by previous gates;
        # still explicitly reject any automatic promotion from any of four ledgers.
        require(all(r.get('source_status')=='SHADOW_UNRECONCILED_V75' and
                r.get('semantic_method')=='CHAT_CONTEXT_INTERPRETATION_NOT_GOLD' and
                all(r.get(f) is False for f in SAFE_FLAGS) for r in rows),
                'FOUR_STAGE_FALSE_COMPLETION_OR_GOLD')
        sets.append(keys)
    union=set().union(*sets)
    require(len(union)==sum(map(len,stage_rows)),'CROSS_GENERATION_SOURCE_ID_COLLISION')
    meta=[]
    for stage,rows in zip((78,79,80,81),stage_rows):
        for r in rows:
            meta.append({'stage':stage,'video_id':r['video_id'],'window_id':r['window_id'],
                         'claim_id':r['claim_id'],'source_sha256':r['source_excerpt_sha256'],
                         'speaker_units_sha256':digest(r['speaker_units']),
                         'reviewer_guard_sha256':sha(r['reviewer_guard'].encode('utf-8'))})
    meta.sort(key=lambda r:(r['video_id'],r['window_id'],r['claim_id']))
    return {
        'schema':'IRE_V6_V81_FOUR_STAGE_FIRST5_PRIVATE_SOURCE_CUSTODY_SHA_ONLY_V1',
        'first_five_original_srt_cues':5129,
        'original_40_cue_windows':130,
        'v33_provisional_utterance_candidates':1603,
        'v78_source_parents':len(v78),'v79_source_parents':len(v79),
        'v80_source_parents':len(v80),'v81_source_parents':len(v81),
        'four_stage_source_parents_unique':len(union),
        'four_stage_source_parent_collisions':sum(map(len,stage_rows))-len(union),
        'v78_semantic_or_nonclaim_units':prior['v78_interpretations'],
        'v79_semantic_or_nonclaim_units':prior['v79_interpretations'],
        'v80_semantic_or_nonclaim_units':prior['v80_new_interpretations'],
        'v81_semantic_or_nonclaim_units':checked['shadow_speaker_or_nonclaim_interpretations'],
        'four_stage_semantic_or_nonclaim_units':prior['three_stage_interpretations']+checked['shadow_speaker_or_nonclaim_interpretations'],
        'v81_by_video':checked['shadow_parents_by_video'],
        'v81_source_custody_sha256':checked['source_and_review_custody_digest_sha256'],
        'four_stage_source_review_sha256':digest(meta),
        'v81_speech_act_counts':checked['speech_act_counts'],
        'v75_private_298_queue_bytes_recovered':False,
        'official_v75_404_parent_membership_verified':False,
        'new_official_unique_parent_reviews':0,
        'v75_p2_context_escalated_pending_unchanged':298,
        'v75_p2_other_pending_unchanged':501,
        'v75_p1_complex_pending_unchanged':88,
        'v75_total_pending_unchanged':887,
        'historical_v40_108_canonical_events_recovered':False,
        'financial_truth_certified':False,'independent_gold':False,
        'personal_advice_approved':False,'p0_go':False,
        'original_srt_and_private_notes_not_in_public_receipt':True,
    }

def private_replay(source_zip,v78_zip,v79_zip,v80_zip,v81_json):
    census,registry,cues=audit(source_zip)
    require(census['v42_cohort_digest_matches'] and census['total_v33_candidates']==1603 and
            census['total_windows']==130 and census['source_cues_without_candidate']==104,
            'V42_ORIGINAL_FULL_COHORT_DRIFT')
    old78=load_pinned_private_rows(v78_zip,V78_BUNDLE_SHA,V78_RECORD,V78_RECORD_SHA)
    old79=load_pinned_private_rows(v79_zip,V79_BUNDLE_SHA,V79_RECORD,V79_RECORD_SHA)
    old80=load_pinned_private_rows(v80_zip,V80_BUNDLE_SHA,V80_RECORD,V80_RECORD_SHA)
    new=json.loads(Path(v81_json).read_text(encoding='utf-8'))
    return validate_quad(cues,registry,old78,old79,old80,new)