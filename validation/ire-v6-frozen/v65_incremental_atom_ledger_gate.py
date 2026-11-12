"""V65 cumulative additive P0 SHA-only custody/reconciliation and provenance namespace.

Does not read original SRT or certify ChatGPT meaning/financial truth. The
private owner replay must validate source bytes and excerpt spans first.
"""
from __future__ import annotations
import hashlib,json,re
from collections import Counter

VID=re.compile(r'[a-zA-Z0-9_-]{11}\Z')
WID=re.compile(r'W[0-9]{5}\Z')
CID=re.compile(r'C[0-9]{5}\Z')
HEX=re.compile(r'[0-9a-f]{64}\Z')
ALLOWED={'P0_SCOPED_FINANCE','P1_COMPLEX_OR_INVESTMENT','P2_GENERAL_OR_CONTEXT'}
ORIGINS={'V61_1','V62','V63','V64','V65'}
class LedgerInvalid(ValueError):pass

def _digest(x):
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,
         separators=(',',':')).encode()).hexdigest()

def audit_atomic_ledger(source_census,review_rows):
    if type(source_census) is not list or type(review_rows) is not list or not source_census:
        raise LedgerInvalid('SOURCE_REVIEW_ROWS_REQUIRED')
    by_src={}
    for s in source_census:
        if type(s) is not dict or set(s)!={'video_id','window_id','parent_id','source_sha256','triage_bucket'}:
            raise LedgerInvalid('SOURCE_SCHEMA_BAD')
        vid,wid,pid,h,b=(s[k] for k in ('video_id','window_id','parent_id','source_sha256','triage_bucket'))
        if not all(type(v) is str for v in (vid,wid,pid,h,b)) or not VID.fullmatch(vid) or not WID.fullmatch(wid) or not CID.fullmatch(pid) or not HEX.fullmatch(h) or b not in ALLOWED:
            raise LedgerInvalid('SOURCE_VALUE_BAD')
        key=(vid,wid,pid)
        if key in by_src:raise LedgerInvalid('SOURCE_PARENT_DUPLICATE')
        by_src[key]=s
    done=set();kids=set();bare_video={};reviewed_by_origin=Counter();public=[]
    for row in review_rows:
        if type(row) is not dict or set(row)!={'video_id','window_id','parent_id','parent_source_sha256','review_origin','semantic_units'}:
            raise LedgerInvalid('REVIEW_SCHEMA_BAD')
        vid,wid,pid,h,origin=(row[k] for k in ('video_id','window_id','parent_id','parent_source_sha256','review_origin'))
        key=(vid,wid,pid)
        if key in done or key not in by_src or by_src[key]['source_sha256']!=h:
            raise LedgerInvalid('REVIEW_SOURCE_IDENTITY_DUPLICATE_OR_DRIFT')
        if origin not in ORIGINS or type(row['semantic_units']) is not list or not row['semantic_units']:
            raise LedgerInvalid('UNAPPROVED_REVIEW_OR_EMPTY_UNITS')
        done.add(key);reviewed_by_origin[origin]+=1
        for unit in row['semantic_units']:
            if type(unit) is not dict or set(unit)!={'unit_id','parent_source_sha256','financial_truth_approved','independent_gold'}:
                raise LedgerInvalid('CHILD_SCHEMA_BAD')
            uid,childsha,approved,gold=(unit[k] for k in ('unit_id','parent_source_sha256','financial_truth_approved','independent_gold'))
            if type(uid) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{6,90}',uid):
                raise LedgerInvalid('CHILD_ID_BAD')
            if childsha!=h or approved is not False or gold is not False:
                raise LedgerInvalid('FALSE_FINANCIAL_TRUTH_OR_GOLD_OR_SOURCE_DRIFT')
            composite=(*key,uid)
            if composite in kids:raise LedgerInvalid('QUALIFIED_CHILD_ID_DUPLICATE')
            kids.add(composite)
            bare_video.setdefault(uid,set()).add(vid)
            public.append({'video_id':vid,'window_id':wid,'parent_id':pid,'child_id':uid,'source_sha256':h})
    pending=Counter(by_src[k]['triage_bucket'] for k in by_src if k not in done)
    public.sort(key=lambda r:(r['video_id'],r['window_id'],r['parent_id'],r['child_id']))
    # Id only, no original transcript, raw meaning text, risk memo or tax conclusions.
    return {'schema':'IRE_V6_V65_SOURCE_CENSUS_AND_UNIQUE_VIDEO_WINDOW_PARENT_CHILD_SHA_ONLY',
            'source_provisional_parent_count':len(by_src),
            'source_grounded_parent_review_count':len(done),
            'unreviewed_source_parent_count':len(by_src)-len(done),
            'source_grounded_child_semantic_unit_count':len(kids),
            'reviewed_parent_by_version':dict(sorted(reviewed_by_origin.items())),
            'pending_by_lexical_bucket':dict(sorted(pending.items())),
            'legacy_unqualified_child_ids_reused_cross_video':sum(len(v)>1 for v in bare_video.values()),
            'qualified_child_duplicates':0,'qualified_ledger_sha256':_digest(public),
            'original_srt_raw_bytes_verification_external_to_this_gate':True,
            'independent_human_gold_certified':False,'true_precision_recall_measured':False,
            'financial_facts_personal_advice_approved':False,'p0_go':False}
