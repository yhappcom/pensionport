"""V63 public-safe, additive, no-API lineage key namespace gate.

Input contains only source identity hashes, not transcript texts. Legacy unqualified
child IDs can legitimately repeat across DIFFERENT videos; canonical keys cannot.
This gate tests provenance identity, NOT ChatGPT semantic completeness or truth.
"""
from __future__ import annotations
import hashlib,json,re

VIDEO_ID=re.compile(r'^[A-Za-z0-9_-]{11}$')
WINDOW_ID=re.compile(r'^W[0-9]{5}$')
PARENT_ID=re.compile(r'^C[0-9]{5}$')
HEX=re.compile(r'^[a-f0-9]{64}$')

class LineageIdentityError(ValueError):pass

def audit_lineage(rows):
    if type(rows) is not list or not rows:raise LineageIdentityError('ROWS_REQUIRED')
    parents=set();qualified=set();bare_to_videos={};safe=[];num_units=0
    for r in rows:
        if type(r) is not dict or set(r)!={'video_id','window_id','parent_id','parent_source_sha256','review_origin','semantic_units'}:
            raise LineageIdentityError('EXACT_SOURCE_IDENTITY_KEYS_REQUIRED')
        v,w,p,h,o=r['video_id'],r['window_id'],r['parent_id'],r['parent_source_sha256'],r['review_origin']
        if not all(type(t) is str for t in (v,w,p,h,o)) or not VIDEO_ID.fullmatch(v) or not WINDOW_ID.fullmatch(w) or not PARENT_ID.fullmatch(p) or not HEX.fullmatch(h) or o not in ('V61_1','V62','V63'):
            raise LineageIdentityError('INVALID_SOURCE_IDENTITY')
        parent_key=(v,w,p)
        if parent_key in parents:raise LineageIdentityError('DUPLICATE_SOURCE_PARENT')
        parents.add(parent_key)
        children=r['semantic_units']
        if type(children) is not list or not children:raise LineageIdentityError('EMPTY_CHILDREN')
        for child in children:
            if type(child) is not dict or set(child)!={'unit_id','parent_source_sha256','financial_truth_approved','independent_gold'}:
                raise LineageIdentityError('CHILD_SCHEMA_ERROR')
            u,ch,fa,gi=(child[k] for k in ('unit_id','parent_source_sha256','financial_truth_approved','independent_gold'))
            if type(u) is not str or not 6 <= len(u) <= 90 or not re.fullmatch(r'[A-Za-z0-9_-]+',u):raise LineageIdentityError('UNSAFE_UNIT_ID')
            if ch!=h:raise LineageIdentityError('CHILD_SOURCE_SHA_DRIFT')
            if fa is not False or gi is not False:raise LineageIdentityError('FALSE_FINANCE_OR_GOLD_APPROVAL')
            key=(v,w,p,u)
            if key in qualified:raise LineageIdentityError('DUPLICATE_QUALIFIED_CHILD_KEY')
            qualified.add(key);num_units+=1
            bare_to_videos.setdefault(u,set()).add(v)
            safe.append({'video_id':v,'window_id':w,'parent_id':p,'parent_source_sha256':h,'legacy_child_id':u})
    safe.sort(key=lambda r:(r['video_id'],r['window_id'],r['parent_id'],r['legacy_child_id']))
    canonical=json.dumps(safe,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    return {'schema':'IRE_V6_V63_FEDERATED_ORIGINAL_VIDEO_WINDOW_PARENT_CHILD_NAMESPACE_SHA_ONLY',
            'parents':len(parents),'children':num_units,
            'unqualified_child_ids_reused_across_distinct_videos':sum(len(s)>1 for s in bare_to_videos.values()),
            'qualified_child_key_duplicates':0,
            'canonical_identity_sha256':hashlib.sha256(canonical).hexdigest(),
            'no_source_text_in_receipt':True,
            'source_byte_verification_executed_by_this_gate':False,
            'semantic_accuracy_or_human_gold_proved':False,
            'p0_go':False}
