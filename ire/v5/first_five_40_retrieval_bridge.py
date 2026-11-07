"""Read-only connection: first-40 original claims -> pinned laws -> V5 educational answers.

Replays official-site *markdown extracts* before retrieval. Never upgrades a source
snippet to an approved tax determination or changes the 116-claim master. The
independent two-signature knowledge approval gate remains separately required.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

from .first_five_40_official_replay_approval_gate import (
    MANIFEST, SCOPE, B04, PINS, verify as verify_official,
    ApprovalGateError, need,
)

# This is a reviewed *routing* map. Every value must exactly match official
# snapshots on the respective source claims in the locked 40-window manifest.
# Changing an educational node's legal support requires a code review.
REVIEWED_SOURCE_BINDINGS = {
    'V5-001-40-NPS_RETROACTIVE_ELIGIBILITY': ('NPS_RETRO',),
    'V5-001-40-NPS_CPI_VS_INVESTMENT': ('NPS_CPI',),
    'V5-001-40-NPS_PAYMENT': ('NPS_PAY',),
    'V5-001-40-NPS_DEFERRAL': ('NPS_DELAY',),
    'V5-001-40-PRIVATE_PENSION_1500_TAX': ('NTS_RATE2026','LAW_14'),
    'V5-001-40-DIVIDEND_2000_VS_PENSION_1500': ('LAW_FIN2000',),
    'V5-001-40-PENSION_BASIS_PROVENANCE': ('LAW_CREDIT','LAW_WITHDRAW'),
    'V5-001-40-ISA_MATURITY_TO_PENSION': ('NTS_CREDIT','LAW_CREDIT'),
    'V5-001-40-DEEMED_PENSION_WITHDRAWAL_ORDER': ('LAW_WITHDRAW',),
}
BLOCKED_PATTERNS = re.compile(
    r'내\s*(?:계좌|돈|IRP|ISA|연금).*?(?:주문|매수|매도|전량|팔아|처리해|옮겨줘|결정해)' 
    r'|(?:내게|저한테|나에게).*?(?:추천해|선택해|결정해)' 
    r'|(?:무조건|반드시).*?(?:수익|안전|보장)'
)

class BridgeError(ValueError):
    pass


def _json(path: Path):
    return json.loads(path.read_text('utf-8'))


def load_catalog(root: Path) -> list[dict]:
    root=Path(root).resolve()
    # Full 15/15 byte replay, source window scope, master unchanged, B04 6 edges,
    # and deny-by-default no-signed-review policy must all pass, every call.
    receipt=verify_official(root)
    need(receipt['official_source_extraction_snapshots_replayed']==15 and
         receipt['actual_dual_signed_legal_knowledge_approvals']==0 and
         receipt['formal_B04_master_merges']==0 and
         receipt['entire_original_claims_approved']==0,
         'BRIDGE_UNAUTHORIZED_OR_INCOMPLETE_APPROVAL_STATE')
    manifest=_json(root/MANIFEST)
    scope=_json(root/SCOPE)
    b04=_json(root/B04)
    claims={c['claim_id']:c for c in scope['claims']}
    snaps={s['authority_id']:s for s in manifest['snapshots']}
    overlays=scope['knowledge_overlay']
    need(len(overlays)==len(REVIEWED_SOURCE_BINDINGS)==9 and
         {n['knowledge_id'] for n in overlays}==set(REVIEWED_SOURCE_BINDINGS),
         'BRIDGE_EDUCATION_NODE_CENSUS_CHANGED')
    b04_edges={(x['knowledge_id'],x['prior_claim_id'])
               for x in b04['B04_scoped_education_edges']}
    nodes=[]
    for node in overlays:
        ident=node['knowledge_id']
        support=REVIEWED_SOURCE_BINDINGS[ident]
        refs=tuple(dict.fromkeys(s for claim_id in node['source_claim_ids']
                            for s in manifest['regulatory_claim_narrow_source_map'][claim_id]))
        need(set(refs)==set(support) and set(support)<=set(snaps)<=set(PINS),
             'BRIDGE_NODE_TO_PINNED_OFFICIAL_SOURCES_CHANGED')
        need(node['scope']=='GENERAL_EDUCATION_NARROW_OFFICIAL' and
             node['status']=='CURATED_EDUCATION_OVERLAY_ACTIVE_FOR_SCOPED_RETRIEVAL' and
             node['legacy_master_mutated'] is False and node['formal_B04_merged'] is False and
             node['personalized_advice_approved'] is False,
             'BRIDGE_UNAUTHORIZED_FACT_PROMOTION')
        for cid in node['source_claim_ids']:
            need(cid in claims and claims[cid]['review_status']=='OFFICIAL_NARROW_SUBFACT_VERIFIED' and
                 claims[cid]['entire_video_claim_approved'] is False,
                 'BRIDGE_INADMISSIBLE_SPEAKER_CLAIM')
        for pid in node['prior_claim_ids']:
            if pid in {'GOMHEE-C66','GOMHEE-C78'}:
                need((ident,pid) in b04_edges,'BRIDGE_B04_EDGE_NOT_ACCEPTED')
            else:
                need((ident,pid) not in b04_edges,'BRIDGE_OUTSIDE_B04_WRONGLY_MERGED')
        terms=node.get('retrieval_terms')
        need(isinstance(terms,list) and len(terms)>0 and
             len(terms)==len(set(terms)) and
             all(isinstance(t,str) and len(t.strip())>=2 for t in terms),
             'BRIDGE_UNSAFE_QUERY_TERMS')
        nodes.append({
            'knowledge_id':ident,
            'statement':node['knowledge_text'],
            'terms':terms,
            'source_video_id':node['origin_video_id'],
            'source_claim_ids':node['source_claim_ids'],
            'source_cue_ref_sha256':{cid:claims[cid]['source_cue_refs_sha256']
                                     for cid in node['source_claim_ids']},
            'prior_claim_ids':node['prior_claim_ids'],
            'official_extraction_evidence':[
                {'authority_id':sid,'official_url':snaps[sid]['official_url'],
                 'pinned_sha256':snaps[sid]['snapshot_sha256'],
                 'snapshot_path':snaps[sid]['snapshot_path'],
                 'observed_as_of':manifest['observed_as_of'],
                 'source_kind':'THIRD_PARTY_OFFICIAL_SITE_EXTRACT_NOT_GOVERNMENT_SIGNED'}
                for sid in support
            ],
            'source_content_replayed':True,
            'independent_knowledge_approved':False,
            'speaker_whole_claim_fact_approved':False,
            'formal_master_merged':False,
            'personal_advice_approved':False,
            'retrieval_status':'SCOPED_EDUCATION_CONTEXT_NOT_FORMALLY_APPROVED_FACT',
        })
    return sorted(nodes,key=lambda x:x['knowledge_id'])


def _normalize(text: str) -> str:
    return re.sub(r'\s+|[,，]', '', text.casefold())


def retrieve(root: Path, question: str, *, intent: str='general_education', limit: int=3) -> dict:
    if not isinstance(question,str) or not question.strip():
        raise BridgeError('BRIDGE_EMPTY_QUESTION')
    if intent not in {'general_education','personal_action','guaranteed_return'}:
        raise BridgeError('BRIDGE_UNKNOWN_INTENT')
    if type(limit) is not int or not 1<=limit<=9:
        raise BridgeError('BRIDGE_BAD_LIMIT')
    # Check legal provenance first; even denied requests cannot silently skip
    # a tampered source if the feature is present in an active repository.
    catalog=load_catalog(root)
    if intent!='general_education' or BLOCKED_PATTERNS.search(question):
        return {'schema':'IRE_V5_FIRST40_READONLY_EDUCATION_RETRIEVAL_V1',
                'match_count':0,'items':[],
                'decision':'BLOCKED_PERSONAL_ACTION_OR_GUARANTEED_RETURN',
                'independent_legal_fact_approval_count':0,
                'personal_advice_approved':False,'master_merged':False}
    q=_normalize(question)
    hits=[]
    for item in catalog:
        score=sum(len(_normalize(t))+2 for t in item['terms'] if _normalize(t) in q)
        if score>0:hits.append((score,item))
    hits.sort(key=lambda pair:(-pair[0],pair[1]['knowledge_id']))
    found=[{k:v for k,v in item.items() if k!='terms'} for score,item in hits[:limit]]
    return {'schema':'IRE_V5_FIRST40_READONLY_EDUCATION_RETRIEVAL_V1',
            'match_count':len(found),'items':found,
            'decision':'SCOPED_EDUCATION_CONTEXT_ONLY' if found else 'NO_MATCH',
            'independent_legal_fact_approval_count':0,
            'personal_advice_approved':False,'master_merged':False}


def audit(root:Path)->dict:
    catalog=load_catalog(root)
    examples=[
        ('국민연금 추납 119개월 조건','NPS_RETROACTIVE_ELIGIBILITY'),
        ('연금 지급일이 25일인가요','NPS_PAYMENT'),
        ('물가와 배당은 어떻게 다른가','NPS_CPI_VS_INVESTMENT'),
        ('연기연금 7.2% 가산율','NPS_DEFERRAL'),
        ('사적연금 1500만원 인출 상한','PRIVATE_PENSION_1500_TAX'),
        ('배당세 2000만원 세금','DIVIDEND_2000_VS_PENSION_1500'),
        ('비공제원금 세액공제 확인','PENSION_BASIS_PROVENANCE'),
        ('ISA 만기 전환 세액공제','ISA_MATURITY_TO_PENSION'),
        ('인출순서 과세제외 원금','DEEMED_PENSION_WITHDRAWAL_ORDER')]
    for query,expected in examples:
        result=retrieve(root,query,limit=9)
        if not any(r['knowledge_id'].endswith(expected) for r in result['items']):
            raise BridgeError('BRIDGE_MISSING_SCOPED_KNOWLEDGE:'+expected)
        if any(r['independent_knowledge_approved'] or r['personal_advice_approved'] for r in result['items']):
            raise BridgeError('BRIDGE_UNSIGNED_FACT_PROMOTED')
    unrelated=retrieve(root,'영화관 상영시간과 주차요금')
    if unrelated['match_count']!=0:
        raise BridgeError('BRIDGE_UNRELATED_QUESTION_FALSE_POSITIVE')
    personal=retrieve(root,'내 IRP 계좌의 돈을 전량 매도해 줘')
    if personal['match_count'] or personal['decision']!='BLOCKED_PERSONAL_ACTION_OR_GUARANTEED_RETURN':
        raise BridgeError('BRIDGE_PERSONAL_ACTION_NOT_BLOCKED')
    return {'schema':'IRE_V5_FIRST40_READONLY_ADVISORY_CONNECTION_AUDIT_V1',
            'source_windows':40,'source_claims':97,
            'education_candidates_connected':len(catalog),
            'official_source_snapshots_replayed':15,
            'sample_queries_verified':len(examples),
            'unrelated_query_returned_zero':True,
            'personal_action_blocked':True,
            'externally_signed_narrow_facts_approved':0,
            'original_full_claims_approved':0,
            'master_116_modified':False,
            'formal_b04_merge_approved':False,
            'release':'GENERAL_EDUCATION_RETRIEVAL_ONLY_NO_GO_PERSONAL_ADVICE'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--question')
    p.add_argument('--intent',default='general_education')
    a=p.parse_args()
    result=retrieve(a.root,a.question,intent=a.intent) if a.question else audit(a.root)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
