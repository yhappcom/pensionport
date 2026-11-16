"""V83 public-source-safe auxiliary link audit for V33's 104 uncovered cue fragments.

This module NEVER equates cue coverage with atomic-claim recall or financial truth.
It accepts original cues privately but publishes hash-only counts and synthetic tests.
No official 1,603 candidate ID, 130 source window, or prior review is modified.
"""
from __future__ import annotations
from bisect import bisect_left
from collections import Counter
from dataclasses import asdict
from typing import Mapping
import hashlib

from v77_private_v33_replay import sha, digest

SCHEMA='IRE_V6_V83_FIRST5_104_UNCOVERED_CUES_AUXILIARY_CONTEXT_ONLY_V1'
STATUS='AUXILIARY_CONTEXT_NOT_V33_CANDIDATE'
UNTRIAGED='CONTEXT_UNADJUDICATED_NOT_NEGATIVE_GOLD'
REVIEWED='CHAT_CONTEXT_ALERT_REVIEW_NOT_INDEPENDENT_GOLD'
FALSE_FLAGS=('fact_approved','independent_gold','personal_action_approved','official_parent_merged','v75_membership_verified')
# Hand-screened source-fragment anchors; cues and their exact wording remain private.
# The label is a *risk of misconstrual*, not a determination that the utterance is true.
PRIORITY_ALERTS={
 (1,129):'DURATION_SCOPE_FRAGMENT',
 (1,582):'QUESTION_FORCE_FRAGMENT',
 (2,155):'NEGATION_POLARITY_FRAGMENT',
 (2,316):'LIQUIDITY_SCOPE_FRAGMENT',
 (2,901):'COMPARATIVE_QUESTION_FRAGMENT',
 (3,133):'AMOUNT_UNIT_FRAGMENT',
 (4,334):'HOLD_ACTION_FRAGMENT',
 (4,342):'FUTURE_TIME_SCOPE_FRAGMENT',
 (5,398):'QUESTION_FORCE_FRAGMENT',
 (5,961):'PREFERENCE_DIRECTION_FRAGMENT',
}

def require(p,code):
    if not p:raise ValueError('V83_'+code)

def _entry_index(registry,cues_by_video,video_id):
    require(video_id in registry and video_id in cues_by_video,'VIDEO_NOT_FOUND')
    cues=cues_by_video[video_id]
    m={}
    for wid,rows in registry[video_id].items():
        for r in rows:
            cid=r['claim_id']
            for i in r['cue_indices']:
                require(isinstance(i,int) and 1<=i<=len(cues),'CANDIDATE_CUE_RANGE_INVALID')
                require(i not in m,'CANDIDATE_CUE_OVERLAP')
                m[i]=(wid,cid,r['source_text_sha256'])
    return m

def auxiliary_expected(cues_by_video,registry,video_pins):
    """Generate source-anchored 104 non-candidate gap descriptors, no semantic label."""
    out=[]
    for video_no,video_id,*_ in video_pins:
        cc=cues_by_video[video_id];m=_entry_index(registry,cues_by_video,video_id)
        assigned=sorted(m)
        require(assigned,'VIDEO_HAS_NO_CANDIDATES')
        for c in cc:
            i=c.index
            if i in m:continue
            at=bisect_left(assigned,i)
            left=assigned[at-1] if at else None
            right=assigned[at] if at<len(assigned) else None
            require(left is not None or right is not None,'GAP_WITHOUT_ANY_PARENT_CONTEXT')
            def anchor(n):
                if n is None:return None
                wid,cid,claim_sha=m[n]
                return {'window_id':wid,'claim_id':cid,'claim_sha256':claim_sha,'nearest_cue_index':n,'cue_distance':abs(n-i)}
            neighbors=[{'cue_index':n,'start_ms':cc[n-1].start_ms,
                'end_ms':cc[n-1].end_ms,'text_private':cc[n-1].text}
                for n in range(max(1,i-2),min(len(cc),i+2)+1)]
            out.append({
                'schema':SCHEMA,'video_no':video_no,'video_id':video_id,
                'cue_index':i,'start_ms':c.start_ms,'end_ms':c.end_ms,
                'cue_text_private':c.text,'cue_text_sha256':sha(c.text.encode('utf-8')),
                'adjacent_cues_private':neighbors,
                'left_existing_candidate':anchor(left),
                'right_existing_candidate':anchor(right),
                'source_status':STATUS,'context_status':UNTRIAGED,
                'risk_type':None,'context_interpretation_private':None,'reviewer_caution_private':None,
                **{flag:False for flag in FALSE_FLAGS},
            })
    return out

def validate_source_gap_custody(cues_by_video,registry,video_pins,rows,*,
                                expected_count=104,alerts=PRIORITY_ALERTS,
                                expected_prior_parents=130):
    require(type(rows) is list and len(rows)==expected_count,'GAP_COUNT_OR_TYPE_DRIFT')
    require(type(alerts) is dict,'ALERTS_SCHEMA_INVALID')
    require(type(expected_prior_parents) is int and expected_prior_parents>=0,'PRIOR_COUNT_INVALID')
    baseline=auxiliary_expected(cues_by_video,registry,video_pins)
    require(len(baseline)==expected_count,'SOURCE_GAP_EXPECTATION_DRIFT')
    indexed={(r['video_id'],r['cue_index']):r for r in baseline}
    require(len(indexed)==expected_count,'BASELINE_DUPLICATE_GAP')
    got={};aggregated=[];priority=[];pervideo=Counter();leftonly=0;rightonly=0
    for row in rows:
        require(type(row) is dict,'GAP_ROW_NOT_DICT')
        k=(row.get('video_id'),row.get('cue_index'))
        require(k not in got,'DUPLICATE_GAP_ROW')
        require(k in indexed,'NON_GAP_OR_FOREIGN_CUE')
        got[k]=row
        expect=indexed[k]
        for key in ('schema','video_no','video_id','cue_index','start_ms','end_ms',
                    'cue_text_private','cue_text_sha256','adjacent_cues_private',
                    'left_existing_candidate','right_existing_candidate','source_status'):
            require(type(row.get(key)) is type(expect[key]) and row.get(key)==expect[key],
                    'SOURCE_OR_NEIGHBOR_CONTEXT_DRIFT_'+key.upper())
        require(all(row.get(f) is False for f in FALSE_FLAGS),'FALSE_FINANCIAL_OR_GOLD_PROMOTION')
        label=alerts.get((row['video_no'],row['cue_index']))
        if label is None:
            require(row.get('risk_type') is None and row.get('context_status')==UNTRIAGED
                    and row.get('context_interpretation_private') is None
                    and row.get('reviewer_caution_private') is None,
                    'UNREVIEWED_CONTEXT_MUST_STAY_UNADJUDICATED')
        else:
            require(row.get('risk_type')==label and row.get('context_status')==REVIEWED,
                    'MANUAL_ALERT_LABEL_MISMATCH')
            require(isinstance(row.get('context_interpretation_private'),str)
                    and len(row['context_interpretation_private'])>=12,
                    'MISSING_MANUAL_INTERPRETATION')
            require(isinstance(row.get('reviewer_caution_private'),str)
                    and len(row['reviewer_caution_private'])>=12,
                    'MISSING_MANUAL_CAUTION')
            priority.append({'video_no':row['video_no'],'cue_index':row['cue_index'],
                             'risk_type':label,'cue_sha256':row['cue_text_sha256'],
                             'interpretation_sha256':sha(row['context_interpretation_private'].encode()),
                             'caution_sha256':sha(row['reviewer_caution_private'].encode())})
        pervideo[row['video_no']]+=1
        if row['left_existing_candidate'] is None:leftonly+=1
        if row['right_existing_candidate'] is None:rightonly+=1
        aggregated.append({'video_no':row['video_no'],'video_id':row['video_id'],
          'cue_index':row['cue_index'],'cue_sha256':row['cue_text_sha256'],
          'neighbor_cues_sha256':digest(row['adjacent_cues_private']),
          'left_candidate_sha256':digest(row['left_existing_candidate']),
          'right_candidate_sha256':digest(row['right_existing_candidate']),
          'risk_type':row['risk_type'],'review_status':row['context_status']})
    require(set(got)==set(indexed),'MISSING_EXPECTED_GAP_ROW')
    require(len(priority)==len(alerts),'PRIORITY_ALERT_CENSUS_DRIFT')
    aggregated.sort(key=lambda a:(a['video_no'],a['cue_index']))
    priority.sort(key=lambda a:(a['video_no'],a['cue_index']))
    return {'schema':'IRE_V6_V83_104_GAPS_SOURCE_BOUND_AUXILIARY_SHA_ONLY_RECEIPT_V1',
        'total_cues_first_five':sum(len(cues_by_video[vid]) for _,vid,*_ in video_pins),
        'original_v33_candidate_count_immutable':sum(len(a) for vid in registry for a in registry[vid].values()),
        'original_v33_unassigned_cues':len(rows),
        'auxiliary_context_links_verified':len(rows),
        'high_priority_contextual_alerts':len(priority),
        'other_gaps_unadjudicated_as_standalone_claims':len(rows)-len(priority),
        'gap_cues_by_video':dict(sorted(pervideo.items())),
        'no_left_context_at_video_start':leftonly,
        'no_right_context_at_video_end':rightonly,
        'source_gap_auxiliary_custody_sha256':digest(aggregated),
        'priority_alert_manifest_sha256':digest(priority),
        'prior_130_shadow_parents_source_verified':expected_prior_parents,
        'new_v33_candidates_approved':0,
        'financial_facts_approved':0,'atomic_claim_recall_certified':False,
        'independent_gold':False,'v75_historic_membership_verified':False,
        'official_v75_completed_increment':0,
        'v75_total_pending_unchanged':887,
        'personal_advice_approved':False,'p0_go':False,
        'private_source_or_context_published':False}