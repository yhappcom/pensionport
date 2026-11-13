"""V92 owner-side private lineage reconciliation gate (no approved merge).

Accepts explicit source-verified records, never infers first-five historical V75
identities from public totals and never promotes ChatGPT annotations to gold.
The public module contains no owner SRT or transcript excerpts.
"""
from collections import Counter
from hashlib import sha256
import json, re

COUNT_BY_VERSION={78:20,79:20,80:30,81:30,82:30,84:1,85:15,86:16,87:37,88:40,89:48,90:48,91:55}
SHA_RE=re.compile(r'^[0-9a-f]{64}$')

def digest(obj):
    return sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def require(ok,why):
    if not ok: raise ValueError('V92_'+why)

def verify_lineage(records,expected_source,*,v75_original=None,expected_older_ledger=None):
    """Source-custody gate, NOT semantic identity or official historical consolidation.

    expected_source: owner-verified dict[(video_id, window_id, claim_id)] ->
      {'cue_indices': [...], 'source_sha256': hex}. Caller must reconstruct
      this from the owner SRT and the frozen draft registry independently.
    """
    require(type(records) is list and type(expected_source) is dict,'TYPES')
    require(len(records)==390,'CENSUS_390')
    counts=Counter();keys=set();source_tuples=[]
    group_keys={'FIRST_FIVE':set(),'VIDEO7':set()}
    for row in records:
        require(type(row) is dict,'ROW_TYPE')
        v=row.get('version');vid=row.get('video_id');w=row.get('window_id');c=row.get('claim_id')
        require(type(v) is int and v in COUNT_BY_VERSION,'VERSION')
        require(type(w) is str and re.fullmatch(r'W\d{5}',w)!=None,'WINDOW')
        require(type(c) is str and re.fullmatch(r'C\d{5}',c)!=None,'CLAIM')
        group='FIRST_FIVE' if v<=82 else 'VIDEO7'
        require(row.get('cohort')==group,'COHORT')
        require(type(row.get('video_no')) is int and (row['video_no'] in range(1,6) if group=='FIRST_FIVE' else row['video_no']==7),'VIDEO_NO')
        require(vid in {'sz5N9WJS310','6VEfKF7BzZU','OiDTNstaSpM','aNfGrcO6WPI','qtluAViPpsQ'} if group=='FIRST_FIVE' else vid=='4CQ4FjGT2gA','VIDEO_ID')
        key=(vid,w,c)
        require(key not in keys,'DUPLICATE_SOURCE_CLAIM');keys.add(key);group_keys[group].add(key)
        source=expected_source.get(key)
        require(source is not None,'UNKNOWN_SOURCE_CLAIM')
        require(row.get('cue_indices')==source.get('cue_indices'),'CUE_INTEGRITY')
        require(row.get('source_sha256')==source.get('source_sha256') and SHA_RE.fullmatch(str(row.get('source_sha256')))!=None,'SOURCE_HASH')
        require(all(row.get(f) is False for f in ('fact_approved','independent_gold','personal_action_approved','official_parent_merged')),'ILLEGAL_PROMOTION')
        counts[v]+=1;source_tuples.append([v,*key,row['source_sha256']])
    require(dict(counts)==COUNT_BY_VERSION,'VERSION_CENSUS')
    require(len(group_keys['FIRST_FIVE'])==130 and len(group_keys['VIDEO7'])==260,'COHORT_CENSUS')
    require(len({k[1] for k in group_keys['VIDEO7']})==70,'VIDEO7_WINDOW_CENSUS')
    # Do not accept fabricated V75 membership as evidence. Full external audit is
    # a separate owner-side procedure requiring source bytes and *historical* IDs.
    historical_ready=bool(v75_original is not None and expected_older_ledger is not None)
    if historical_ready:
        require(type(v75_original) is dict and type(expected_older_ledger) is dict,'HISTORICAL_FORMAT')
        require(v75_original.get('trusted_historical_custody') is True and expected_older_ledger.get('trusted_historical_custody') is True,'HISTORICAL_NOT_AUTHENTICATED')
        # Never merge merely because these booleans are present: reconciliation
        # is outside this gate, which records only NOT_YET_ADJUDICATED.
    return {
        'schema':'V92_LINEAGE_CUSTODY_NO_OFFICIAL_MERGE_V1',
        'first_five_source_checked_shadow_parents':130,
        'video7_source_checked_shadow_parents':260,
        'unique_source_claims':390,
        'version_counts':{str(v):counts[v] for v in sorted(counts)},
        'source_receipt_sha256':digest(sorted(source_tuples)),
        'v75_recovery_state':'EXTERNAL_HISTORY_PRESENT_UNADJUDICATED' if historical_ready else 'V75_PRIVATE_404_IDENTITIES_UNAVAILABLE',
        'v75_parent_membership_verified':False,
        'first_five_pending_docket_unchanged':887,
        'new_approved_knowledge':0,
        'formal_history_merge':False,
        'source_semantic_recall_certified':False,
        'p0_go':False
    }