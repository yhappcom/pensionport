"""V89 #7 source-custody, 2026 ISA category split, and no-false-P0 guard.

Public synthetic-testable module. Source SRT and all human-in-chat semantic
annotations remain in owner-private ZIP, never in GitHub or Actions.
2026 ISA classifications are scoped financial-law research, not a tax return.
"""
from __future__ import annotations
import hashlib,json
from collections import Counter
from v87_targeted_source_guard import expected_parent_source

VIDEO_ID='4CQ4FjGT2gA'
OWNER_SHA='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
PRIOR_ARCHIVE_PINS={
 84:'b8fa34d4f36a790608aa4e7f6662caf14567fee9c8eedef68000d1e1b3df9e2d',
 85:'0c87078e870bb88536667cc5a60a68eaeff71914740c9571242dc988caaa584d',
 86:'82b35be0c691aa832102255ac324e73a815c37259228370ff1c91cb53ca2e71d',
 87:'ff028b1c51f2429980fca26a1ddf0f607ed7d2a198b1a53fc7597a9928eb58b4',
 88:'770c55af94d4d041092ce4df89ff27d64cfc7681b62d5e9542a4c6a92a870d50',
}
EXPECTED={
 'W00012':('C00168','C00176','C00177','C00182'),
 'W00028':('C00421','C00423','C00426','C00433'),
 'W00069':('C00996','C00997','C00999','C01007'),
 'W00077':('C01093','C01095','C01096','C01097'),
 'W00109':('C01472','C01473','C01475','C01477'),
 'W00165':('C02106','C02109','C02110','C02116'),
 'W00171':('C02171','C02172','C02173','C02177'),
 'W00172':('C02181','C02184','C02186','C02192'),
 'W00203':('C02611','C02615','C02618','C02625'),
 'W00216':('C02773','C02776','C02778','C02781'),
 'W00220':('C02824','C02825','C02829','C02836'),
 'W00232':('C02949','C02951','C02952','C02953'),
}
SCHEMA='V89_VIDEO7_12_SOURCE_WINDOWS_48_CHAT_SHADOW_NOT_GOLD_V1'
FALSE_FLAGS=('fact_approved','independent_gold','official_parent_merged','personal_action_approved',
             'v75_membership_verified','financial_fact_certified','independent_precision_recall_certified',
             'personalized_advice_approved','full_window_semantics_certified','audio_verified','law_current_verified')
SEMANTIC_KINDS={'DESCRIPTIVE_FINANCE','HISTORICAL_CASE','OPINION','HYPOTHESIS',
                'QUESTION_NOT_FACT','CONDITIONAL_ADVICE','REPORTED_NUMERIC','ASR_UNCERTAIN'}
STATUS='SOURCE_BOUND_CHAT_SHADOW_NOT_INDEPENDENT_GOLD'
ISA_SCOPE_ASOF='2026-11-13'
ISA_SCOPE={
 ('DIRECT_DOMESTIC_LISTED_SHARE','REALIZED_TRADING_GAIN'):'NON_TAXABLE_GAIN_EXCLUDED',
 ('DIRECT_DOMESTIC_LISTED_SHARE','NET_REALIZED_TRADING_LOSS'):'POTENTIALLY_NETTABLE_IF_ELIGIBLE',
 ('DOMESTIC_EQUITY_FUND_ETF','EXEMPT_EQUITY_TRADING_LOSS'):'NON_TAXABLE_COMPONENT_EXCLUDED',
 ('FUND_OR_ETF','TAXABLE_BASIS_LOSS'):'POTENTIALLY_NETTABLE_BY_TAX_BASIS',
}
ISA_AUTHORITIES={
 'NABO_20260430':'https://nabo.go.kr/board/file/down.do?fid=33319223',
 'LAW_20260918':'https://law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1024341967',
 'SHINHAN_2026':'https://open.shinhansec.com/mobilealpha/html/FP/SB5491T01.html',
 'IBK_CURRENT':'https://www.ibks.com/fundproduct/isa/isa_02.jsp',
 'SAMSUNG_SCOPE':'https://www.samsungpop.com/mbw/finance/isa.do?cmd=guide',
}

def require(cond,reason):
    if not cond:raise ValueError('V89_'+reason)
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
def digest(obj):return sha(canonical(obj))
def scope_isa(asset_kind,component):
    """Fail-closed classification; NOT a personalized tax calculation."""
    return ISA_SCOPE.get((asset_kind,component),'MANUAL_REVIEW_REQUIRED')
def guard_nonapproval(row):
    require(row.get('status')==STATUS,'FALSE_SHADOW_STATUS')
    for key in FALSE_FLAGS:require(row.get(key) is False,'FALSE_FINANCIAL_APPROVAL_'+key)
    require(row.get('semantic_kind') in SEMANTIC_KINDS,'SEMANTIC_CATEGORY')
    require(type(row.get('risk_domain')) is str and len(row['risk_domain'])>=8,'NO_RISK_DOMAIN')
    for key in ('speaker_meaning_private','scope_caution_private'):
        require(type(row.get(key)) is str and len(row[key])>=40,'MISSING_SOURCE_MEANING_'+key)

def check_one_parent(row,cues,regs):
    require(row.get('video_no')==7 and row.get('video_id')==VIDEO_ID,'UNEXPECTED_VIDEO')
    wid,cid=row.get('window_id'),row.get('claim_id')
    require(wid in EXPECTED and cid in EXPECTED[wid],'UNEXPECTED_PARENT')
    src=expected_parent_source(cues,regs,(wid,cid))
    for key in ('window_id','claim_id','cue_indices','start_ms','end_ms','source_excerpt_private',
                'adjacent_cues_private','source_sha256','adjacent_context_sha256'):
        require(row.get(key)==src[key],'SOURCE_CUSTODY_'+key)
    require(sha(row['source_excerpt_private'].encode('utf-8'))==row['source_sha256'],'FORGED_PARENT_DIGEST')
    require(digest(row['adjacent_cues_private'])==row['adjacent_context_sha256'],'FORGED_CONTEXT_DIGEST')
    guard_nonapproval(row)
    return digest([wid,cid,row['source_sha256'],row['semantic_kind'],
                   sha(row['speaker_meaning_private'].encode('utf-8')),
                   sha(row['scope_caution_private'].encode('utf-8'))])

def verify_source_screens(selected,all269,cues,regs):
    require(type(selected) is list and len(selected)==12,'SELECTED_WINDOW_12_CENSUS')
    require(type(all269) is list and len(all269)==269,'V86_269_SCREEN_REQUIRED')
    sm={x['window_id']:x for x in all269}
    require(len(sm)==269 and set(x['window_id'] for x in selected)==set(EXPECTED),'SCREEN_KEY_DRIFT')
    for r in selected:
        w=r['window_id'];require(w in sm and r==sm[w],'V86_WINDOW_SCREEN_CHANGED')
        require(r['video_id']==VIDEO_ID and r['video_no']==7,'SCREEN_VIDEO')
        require(r['manual_reviewed_all_parents'] is False,'FALSE_FULL_WINDOW_GO')
        require(r['fact_approved'] is False and r['independent_gold'] is False and r['personal_action_approved'] is False,'SCREEN_FALSE_GO')
        win=int(w[1:]);fst=(win-1)*40+1;last=min(win*40,len(cues))
        require(r['first_cue']==fst and r['last_cue']==last,'SCREEN_CUE_BOUNDS')
        require(r['draft_parent_count']==len(regs[w]),'SCREEN_DRAFT_COUNT')
        text=' '.join(cues[i-1].text for i in range(fst,last+1))
        require(r['source_window_sha256']==sha(text.encode('utf-8')),'SCREEN_RAW_SHA')
    return digest(selected)

def verify_batch(rows,cues,regs,prior,selected,all269):
    require(type(rows) is list and len(rows)==48,'FORTY_EIGHT_PARENT_REVIEWS_REQUIRED')
    require(type(prior) is set and len(prior)==109,'V88_PRIOR109_REQUIRED')
    require(len({w for w,c in prior})==41,'V88_PRIOR41_WINDOWS_REQUIRED')
    targets={(w,c) for w,cs in EXPECTED.items() for c in cs}
    require(len(targets)==48 and len(EXPECTED)==12,'TARGET_MAP_CHANGED')
    require(not ({w for w,c in prior} & set(EXPECTED)),'REVIEWED_WINDOW_REUSED')
    verify_source_screens(selected,all269,cues,regs)
    seen=set();hashed=[];counts=Counter()
    for row in rows:
        k=(row.get('window_id'),row.get('claim_id'))
        require(k in targets and k not in seen and k not in prior,'DUPLICATE_OR_UNKNOWN_PARENT')
        seen.add(k);counts[k[0]]+=1
        hashed.append(check_one_parent(row,cues,regs))
    require(seen==targets and all(counts[w]==4 for w in EXPECTED),'INCOMPLETE_PER_WINDOW_REVIEW')
    require(len(prior|seen)==157 and len({w for w,c in (prior|seen)})==53,'CUMULATIVE_157_53_DRIFT')
    return {'new_manual_parent_reads':48,'new_source_windows_with_manual_samples':12,
            'cumulative_video7_shadow_parents':157,'cumulative_video7_window_samples':53,
            'video7_windows_without_manual_parent':216,
            'new_parent_evidence_sha256':digest(sorted(hashed)),
            'v75_historical_membership_verified':False,
            'official_new_parent_approvals':0,'precision_recall_certified':False,
            'financial_fact_certified':False,'personal_advice_approved':False,'p0_go':False}

def no_false_go_disposition():
    return {'official_unreviewed_first5_887_unchanged':887,
            'v75_roster_unavailable':True,'independent_gold_unavailable':True,
            'financial_source_fact_approval':False,'personalized_advice_approval':False,
            'audio_three_unresolved':3,'all_269_video7_windows_meaning_reviewed':False,'p0_go':False}