"""V140: source-bound private review/roll-up guard, not a semantic or release engine.

This gate deliberately cannot produce a V123 PASS, a semantic gold score or a
parent publication receipt. It detects mutated owner source, missing high-risk
links and unqualified positive release states. It is safe to add to public CI
with synthetic data while keeping the real owner transcript private.
"""
from __future__ import annotations
from hashlib import sha256
from collections import Counter
import json
import re

BASE_SOURCE_SHA='638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d'
REQUIRED_REPAIRS=frozenset({'S01','S04','S07','S20','S25'})
REQUIRED_CONFLICT_LINKS={
 'B13_FIVE_STOCK_CONCENTRATION':{'B10_NONPROFESSIONAL_EXCEPTION','B10_LOSS_THEN_LARGE_GAIN'},
 'B13_PERSONALITY_CONCENTRATION':{'B10_NONPROFESSIONAL_EXCEPTION','B10_DIVERSIFICATION_RULE'},
 'B11_DIVIDEND_YIELD_IS_MARGIN':{'B11_MARGIN_OF_SAFETY','B11_MARGIN_FALLIBILITY'},
 'B12_TECH_SUCCESS_90_PERCENT':{'B11_RISK_UNCERTAINTY','B12_BUY_BEFORE_RESULT'},
 'B10_LOSS_THEN_LARGE_GAIN':{'B10_INITIAL_LOSS','B12_THESIS_WRONG_EXIT'}
}
CRITICAL_ID_SET={
 'B10_LOSS_THEN_LARGE_GAIN','B10_EXPERT_CONCENTRATION','B10_NONPROFESSIONAL_EXCEPTION',
 'B11_DIVIDEND_YIELD_IS_MARGIN','B12_TECH_SUCCESS_90_PERCENT','B12_BUY_BEFORE_RESULT',
 'B13_CONCENTRATION_WITHOUT_RESEARCH','B13_FIVE_STOCK_CONCENTRATION','B13_PERSONALITY_CONCENTRATION'
}
class SourceCustodyError(ValueError): pass

def _fail(code): raise SourceCustodyError('V140_P0_'+code)

def srt_cues(raw:bytes):
    """Exact owner bytes are required. Counts and cue order cannot be inferred from SHA-only metadata."""
    if not isinstance(raw,bytes) or sha256(raw).hexdigest()!=BASE_SOURCE_SHA:
        _fail('ORIGINAL_BYTES_CHANGED_OR_MISSING')
    try:txt=raw.decode('utf-8-sig')
    except UnicodeDecodeError:_fail('SRT_NOT_UTF8')
    out={}
    for chunk in re.split(r'\n\s*\n',txt.strip()):
        fields=chunk.strip().splitlines()
        if not fields or not fields[0].isdigit() or len(fields)<3 or '-->' not in fields[1]:
            _fail('INVALID_SRT_CUE')
        n=int(fields[0])
        if n in out:_fail('DUPLICATE_CUE')
        text=' '.join(x.strip() for x in fields[2:])
        out[n]=sha256(text.encode('utf-8')).hexdigest()
    if list(out)!=list(range(1,1482)):_fail('ORIGINAL_1481_CUE_CENSUS_INCOMPLETE')
    return out

def check_real_private_source_review(raw, private_packet):
    cues=srt_cues(raw)
    p=private_packet
    if type(p)!=dict or p.get('schema')!='IRE_V140_PRIVATE_SOURCE_FIRST_RISK_AND_BLIND_REMEDIATION_V1' or p.get('source_sha256')!=BASE_SOURCE_SHA:
        _fail('REVIEW_PACKET_SOURCE_OR_SCHEMA')
    if p.get('reviewer')!='CHATGPT_IN_CHAT':_fail('REVIEWER_UNTRUSTED')
    if p.get('covered_legacy_cues')!=720 or p.get('new_cue_count_pending_complete_semantics')!=761 or p.get('prior_provisional_atom_occurrences')!=165:
        _fail('HISTORICAL_SCOPE_DRIFT')
    patches=p.get('p0_1_discrepancy_remediations')
    if type(patches)!=list or {d.get('blind_id') for d in patches if type(d)==dict}!=REQUIRED_REPAIRS or len(patches)!=len(REQUIRED_REPAIRS):
        _fail('BLIND_DISCREPANCY_UNRESOLVED')
    for d in patches:
        span=d.get('span')
        if type(span)!=list or len(span)!=2 or not all(type(k)==int for k in span) or not 1<=span[0]<=span[1]<=720:
            _fail('CORRECTION_SPAN_INVALID')
        if d.get('cue_sha256')!=[cues[n] for n in range(span[0],span[1]+1)]:
            _fail('CORRECTION_SOURCE_ANCHOR_CHANGED')
        if d.get('fully_adjudicated_independently') is not False or d.get('remediation_source_bound') is not True:
            _fail('FALSE_INDEPENDENT_ADJUDICATION')
        if not d.get('source_first_correction') or not d.get('conditions'):
            _fail('CORRECTION_LACKS_SEMANTIC_AND_CONDITIONS')
    risks=p.get('p0_2_source_selected_risk_cases')
    if type(risks)!=list or not risks:_fail('NO_LATE_SOURCE_REVIEW')
    ids=set()
    cnt=Counter()
    actual={}
    for row in risks:
        if type(row)!=dict:_fail('RISK_ROW_SCHEMA')
        aid=row.get('id');f=row.get('first_cue');l=row.get('last_cue')
        if not isinstance(aid,str) or aid in ids or type(f)!=int or type(l)!=int or not 721<=f<=l<=1481:
            _fail('RISK_ID_OR_SCOPE_INVALID')
        ids.add(aid)
        if row.get('cue_sha256')!=[cues[n] for n in range(f,l+1)]:_fail('RISK_SOURCE_ANCHOR_CHANGED')
        if not isinstance(row.get('source_read_proposition'),str) or len(row['source_read_proposition'])<14:
            _fail('NO_SOURCE_EXTRACTED_SEMANTICS')
        if not isinstance(row.get('reviewer_required_limitation'),str) or len(row['reviewer_required_limitation'])<15:
            _fail('NO_APPLICABILITY_LIMITATION')
        if row.get('source_first_chat_review')!='CHATGPT_IN_CHAT_SEGMENT_RISK_SELECTED' or row.get('full_cue_disposition_approved') is not False or row.get('financial_fact_approved') is not False:
            _fail('FALSE_COMPLETENESS_OR_FINANCE_APPROVAL')
        if row.get('risk_class') not in ('NONE','HIGH','CRITICAL','FACT_OPEN','INVESTMENT_EDUCATION','MARKET_UNVERIFIED','SOURCE_UNVERIFIED','EVIDENCE_OPEN','SURVIVORSHIP','RISK_OPEN'):
            _fail('RISK_CLASS_UNKNOWN')
        if row.get('source_cue_hash_digest')!=sha256(json.dumps(row['cue_sha256'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest():
            _fail('CUE_SPAN_DIGEST_CHANGED')
        cnt[row['risk_class']]+=1
        actual[aid]=row
    if not CRITICAL_ID_SET<=ids or any(actual[k]['risk_class']!='CRITICAL' for k in CRITICAL_ID_SET):
        _fail('HIGH_RISK_MISSING_OR_DOWNGRADED')
    if len(risks)!=p.get('p0_2_risk_case_count') or dict(cnt)!=p.get('p0_2_selected_risk_counts'):
        _fail('SELECTED_CASE_CENSUS_INVALID')
    if any(not any((row['first_cue']-1)//120+1==s for row in risks) for s in range(7,14)):
        _fail('SEGMENT_RISK_COVERAGE_MISSING')
    edges=p.get('p0_2_cross_claim_must_carry_links')
    if type(edges)!=list or len(edges)!=len({e.get('trigger') for e in edges if type(e)==dict}):
        _fail('DUPLICATE_CROSS_SCOPE_RELATION')
    found={}
    for e in edges:
        if type(e)!=dict or e.get('trigger') not in ids or not isinstance(e.get('must_read'),list) or not e['must_read'] or not set(e['must_read'])<=ids:
            _fail('BROKEN_MUST_CARRY_RESTRICTION')
        found[e['trigger']]=set(e['must_read'])
    for trigger,requires in REQUIRED_CONFLICT_LINKS.items():
        if not requires<=found.get(trigger,set()):_fail('MANDATORY_EXCEPTION_MISSING')
    declared_edges=p.get('p0_2_cross_claim_must_carry_links')
    if not isinstance(declared_edges,list) or len(edges)!=len(declared_edges):
        _fail('MUST_CARRY_CENSUS_INVALID')
    if any(p.get(k) is not False for k in ('p0_1_complete_720_atom_truth_adjudicated','p0_2_full_761_cue_role_review_done','p0_3_real_v5_p3_v23_original_e2e','p0_3_official_primary_issuer_bytes_authenticated')):
        _fail('UNPROVEN_COMPLETENESS_PROMOTED')
    if p.get('p0_2_13_child_v123_pass')!=0 or p.get('p0_2_integrated_knowledge_published')!=0:
        _fail('UNAUTHORIZED_V123_OR_KNOWLEDGE_PUBLISH')
    return {
        'status':'REAL_SOURCE_RISK_ANCHORS_VALIDATED_P0_STILL_HOLD',
        'verified_source_cues':len(cues),'reviewed_source_risk_cases':len(risks),
        'critical_items':cnt['CRITICAL'],'high_items':cnt['HIGH'],
        'source_anchored_blind_remediations':len(patches),
        'mandatory_cross_scope_links':len(edges),
        'full_atom_recall_certified':False,
        'full_761_cue_semantic_disposition_complete':False,
        'v123_passed_children':0,'formal_knowledge_export_allowed':False,'p0_go':False
    }

def audit_public_receipt(receipt):
    if type(receipt)!=dict or receipt.get('schema')!='IRE_V140_SOURCE_FIRST_RISK_REMEDIATION_PUBLIC_SHA_ONLY_V1' or receipt.get('source_sha256')!=BASE_SOURCE_SHA or receipt.get('parent_total_cues')!=1481:
        _fail('PUBLIC_RECEIPT_INVALID')
    if receipt.get('legacy_first_720_cues')!=720 or receipt.get('remaining_761_cues')!=761:
        _fail('PUBLIC_SOURCE_CENSUS_INVALID')
    if receipt.get('source_risk_cases_reviewed_selected',0)<=0 or receipt.get('source_anchored_remediation_cases')!=5 or receipt.get('cross_segment_must_carry_links',0)<len(REQUIRED_CONFLICT_LINKS):
        _fail('PUBLIC_REMEDIATION_CENSUS_INVALID')
    for k in ('full_720_independent_gold','true_tp_fp_fn_measured','high_risk_fn_zero_proven','all_remaining_761_cues_exhaustively_atom_dispositioned','knowledge_export_allowed','p0_3_issuer_original_bytes_authenticated','p0_3_real_approved_knowledge_advisory_e2e','p0_go'):
        if receipt.get(k) is not False:_fail('PUBLIC_FALSE_CERTIFICATION_'+k)
    if receipt.get('full_13_v123_final_passed')!=0 or receipt.get('knowledge_published_atoms')!=0:
        _fail('PUBLIC_FALSE_PUBLICATION')
    if not re.fullmatch('[0-9a-f]{64}',str(receipt.get('private_source_review_sha256',''))):
        _fail('PUBLIC_PRIVATE_PACKET_SHA_NOT_PINNED')
    return {'status':'PUBLIC_SHA_ONLY_NONPROMOTION_VERIFIED','p0_go':False,
            'private_original_replay_by_public_ci':False}
