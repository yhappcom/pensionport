"""Fail-closed scoped 40-window financial-rule and educational retrieval gate.

Fifteen *narrow* official subfacts are linked to 20 original RULE claims.
It does not independently certify whole video claims, current legal advice, or
mutate the 116-item legacy knowledge base. CI cannot replay private source SRT.
Run `--private-root` only with the locally retained private original V5 chain.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
from urllib.parse import urlparse

LEDGER='ire/v5/validation/first_five_40_scoped_fact_knowledge_review_20261106.json'
NO_RELEASE={'entire_original_claims_certified':0,'formal_fact_approval_in_v5_engine':0,
            'formal_knowledge_B04_legacy_merge':False,'advice_release':'BLOCKED'}
VALID_STATUS={'OFFICIAL_NARROW_SUBFACT_VERIFIED','REGULATORY_COMPOSITE_OPEN',
              'NOT_APPROVED_AS_REGULATORY_FACT'}
BASELINE='data/claims.jsonl'
APPROVED_DOMAINS={'www.law.go.kr','law.go.kr','www.nts.go.kr','nts.go.kr',
                  'www.nps.or.kr','nps.or.kr','m.nps.or.kr'}

class SafetyError(ValueError):pass

def ensure(condition, message):
    if not condition: raise SafetyError(message)

def canonical(x):
    return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')

def sha256(x):return hashlib.sha256(x).hexdigest()

def load(root:Path):
    j=json.loads((root/LEDGER).read_text('utf-8'))
    ensure(j['schema']=='IRE_V5_VIDEO1_FIRST40_SCOPED_FINANCE_FACT_REVIEW_V1','BAD_SCHEMA')
    ensure(j['review_date']=='2026-11-06','REVIEW_DATE_CHANGED')
    ensure(j['source_zip_sha256']=='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd','ZIP_SHA_CHANGED')
    ensure(j['source_srt_sha256']=='2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f','SRT_SHA_CHANGED')
    ensure(j['video1_20to40_event_head_sha256']=='9f0685b2b1f8b95c2eefa7708e8ae1ad8d1bd567d40e84e1d6b2d04aed81874e','EVENT_HEAD_CHANGED')
    ensure(j['reviewed_window_ids']==[f'W{i:05d}' for i in range(1,41)],'WINDOW_SCOPE_CHANGED')
    for k,val in NO_RELEASE.items():ensure(j.get(k)==val,'UNSAFE_APPROVAL:'+k)
    ensure(j.get('official_source_snapshots_byte_pinned') is False,'SOURCE_SNAPSHOTS_INVENTED')
    official={x['source_id']:x for x in j['official_sources']}
    ensure(len(official)==len(j['official_sources'])==11,'OFFICIAL_SOURCE_DUPLICATE')
    for x in official.values():
        u=urlparse(x['url'])
        ensure(u.scheme=='https' and u.hostname in APPROVED_DOMAINS,'UNTRUSTED_AUTHORITY')
        ensure(x['accessed_at']=='2026-11-06' and
               x['observed_kind']=='WEB_VERIFIED_OFFICIAL_TEXT_NOT_IMMUTABLE_ARCHIVE',
               'UNPROVEN_OFFICIAL_SOURCE_STATUS')
        ensure(x['verified_summary'].strip() and x['section'].strip(),'AUTHORITY_SCOPE_MISSING')
    claims=j['claims'];claimids={x['claim_id']:x for x in claims}
    ensure(len(claims)==97 and len(claimids)==97,'CLAIM_97_CENSUS_FAILED')
    ensure(j['reviewed_claims_count']==97 and j['reviewed_rule_claims_count']==20,'REVIEW_COUNT_MISMATCH')
    ensure(sum(x['kind']=='RULE' for x in claims)==20,'RULE_20_CENSUS_FAILED')
    assure={'OFFICIAL_NARROW_SUBFACT_VERIFIED':15,'REGULATORY_COMPOSITE_OPEN':5,
            'NOT_APPROVED_AS_REGULATORY_FACT':77}
    for status,n in assure.items():
        ensure(sum(x['review_status']==status for x in claims)==n,'VERDICT_COUNT_DRIFT:'+status)
    ensure(j['narrow_official_subfacts_supported']==15 and j['unresolved_rule_composites']==5 and j['non_regulatory_claims_not_approved']==77,'SUMMARY_METRIC_DRIFT')
    for c in claims:
        ensure(c['review_status'] in VALID_STATUS and re.fullmatch(r'V5C\d{4}',c['claim_id']) is not None,
               'BAD_CLAIM_ID_OR_STATUS')
        ensure(c['window_id'] in j['reviewed_window_ids'],'CLAIM_OUT_OF_SCOPE')
        ensure(all(type(n) is int and n>=1 for n in c['source_cue_indices']) and c['source_cue_indices'],
               'SOURCE_CUE_REFS_MISSING')
        ensure(re.fullmatch(r'[0-9a-f]{64}',c['claim_payload_sha256']) is not None and
               re.fullmatch(r'[0-9a-f]{64}',c['source_cue_refs_sha256']) is not None,
               'SOURCE_PROVENANCE_HASH_MISSING')
        ensure(c['entire_video_claim_approved'] is False and c['personal_application_approved'] is False
               and c['v5_kernel_fact_verification_event_issued'] is False,'UNSAFE_WHOLE_CLAIM_PROMOTION')
        ensure(c['existing_relation_status'] in {'EXTENDS_SCOPE_PENDING','DIFFERENT_SCOPE','SAME_SCOPE_PENDING','NO_RELEVANT_PRIOR_WITH_SEARCH','OPEN_RELATION','CONFLICT_CANDIDATE'},'RELATION_STATUS_UNSUPPORTED')
        if c['review_status']=='OFFICIAL_NARROW_SUBFACT_VERIFIED':
            ensure(c['kind']=='RULE' and c['official_source_id'] in official and c['narrow_approved_subfact'],
                   'NARROW_FACT_MISSING_OFFICIAL_EVIDENCE')
        else:
            ensure(c['official_source_id'] is None and c['narrow_approved_subfact'] is None,
                   'UNREVIEWED_FACT_HAS_AUTHORITY')
            if c['review_status']=='REGULATORY_COMPOSITE_OPEN':
                ensure(c['kind']=='RULE','REGULATORY_OPEN_NOT_RULE')
            else:ensure(c['kind']!='RULE','RULE_MISSING_ADJUDICATION')
    # Verify that the legacy 116 claims really exist and remain sourced to their
    # original videos. Never add #1 provenance to C21/C42/C66 etc by assertion.
    rows=[json.loads(x) for x in (root/BASELINE).read_text('utf-8').splitlines() if x.strip()]
    prior={x['claim_id']:x for x in rows}
    ensure(len(rows)>=116 and len(prior)==len(rows),'LEGACY_BASELINE_MISSING_OR_DUPLICATED')
    nodes=j['knowledge_overlay']; nodeids=set()
    ensure(len(nodes)==9,'KNOWLEDGE_NODE_COUNT_CHANGED')
    for node in nodes:
        ensure(node['knowledge_id'] not in nodeids and node['knowledge_id'].startswith('V5-001-40-'),'NODE_ID_INVALID')
        nodeids.add(node['knowledge_id'])
        ensure(node['status']=='CURATED_EDUCATION_OVERLAY_ACTIVE_FOR_SCOPED_RETRIEVAL' and
               node['scope']=='GENERAL_EDUCATION_NARROW_OFFICIAL','NODE_SCOPE_UNSAFE')
        ensure(node['relationship_to_prior']=='EXTENDS_SCOPE_NOT_EXACT_DUPLICATE','MISREPRESENTED_DUPLICATE')
        ensure(node['personalized_advice_approved'] is False and node['legacy_master_mutated'] is False
               and node['formal_B04_merged'] is False,'UNAUTHORIZED_LEGACY_MERGE')
        ensure(node['source_claim_ids'] and node['prior_claim_ids'] and node['official_source_ids'],
               'NODE_PROVENANCE_MISSING')
        ensure(all(x in claimids and claimids[x]['review_status']=='OFFICIAL_NARROW_SUBFACT_VERIFIED'
                   for x in node['source_claim_ids']),'NODE_UNAPPROVED_VIDEO_CLAIM')
        ensure(all(x in official for x in node['official_source_ids']),'NODE_BAD_OFFICIAL_SOURCE')
        ensure(all(x in prior and 'sz5N9WJS310' not in prior[x]['supporting_videos']
                   for x in node['prior_claim_ids']),'PRIOR_SOURCE_PROVENANCE_FABRICATED')
        ensure(type(node['knowledge_text']) is str and len(node['knowledge_text'])>=35,'NODE_CONTENT_UNUSABLE')
    covered={cid for n in nodes for cid in n['source_claim_ids']}
    narrow={x['claim_id'] for x in claims if x['review_status']=='OFFICIAL_NARROW_SUBFACT_VERIFIED'}
    ensure(covered==narrow,'NARROW_RULE_NODE_COVERAGE_GAP')
    return j

def retrieval(query:str,record:dict):
    # Deterministic educational fact lookup, not generative personalized advice.
    ensure(type(query) is str and query.strip(),'EMPTY_QUERY')
    q=query.casefold().replace(',','').replace(' ','')
    matches=[]
    for node in record['knowledge_overlay']:
        if any(term.casefold().replace(',','').replace(' ','') in q for term in node['retrieval_terms']):
            matches.append({'knowledge_id':node['knowledge_id'],'education_text':node['knowledge_text'],
                            'official_source_urls':[s['url'] for s in record['official_sources'] if s['source_id'] in node['official_source_ids']],
                            'source_claim_ids':node['source_claim_ids'],
                            'provisional_relationship_to_legacy':node['prior_claim_ids'],
                            'not_personalized_tax_or_investment_advice':True})
    return {'matching_scoped_education_nodes':matches,'count':len(matches),
            'not_suitable_for_personalized_advice':True,'formal_B04_merge_complete':False}

def private_source_verify(record:dict,private_root:Path):
    # Only the locally retained source enables full quote/cue-hash replay.
    from ire.v5.engine import ResearchRun
    vid='sz5N9WJS310';p=private_root/'videos'/vid
    assert p.is_dir() and not p.is_symlink()
    r=ResearchRun((p/'private_source.srt').read_bytes(),json.loads((p/'source_manifest.json').read_text('utf-8')),p)
    assert r.status()['event_chain_head_sha256']==record['video1_20to40_event_head_sha256']
    assert r.status()['windows_model_evidence_relation_reviewed']==40
    for c in record['claims']:
        m=r.model[c['window_id']];src=next(x for x in m['claims'] if x['claim_id']==c['claim_id'])
        assert sha256(canonical(src))==c['claim_payload_sha256']
        assert sha256(canonical(src['source_refs']))==c['source_cue_refs_sha256']
        assert [x['cue_index'] for x in src['source_refs']]==c['source_cue_indices']
        for q in src['source_refs']:
            assert q['quote'] in r.cues[q['cue_index']].text
        assert c['claim_id'] in r.evidence and c['claim_id'] in r.relations
    assert not r.status()['sealed'] and r.status()['approved_financial_facts']==0
    return {'source_claims_directly_replayed':97,'source_windows_reviewed':40,
            'actual_private_ResearchRun_replay':True,'research_closure':'BLOCKED'}

def verify(root:Path, private_root:Path|None=None):
    j=load(root)
    x={'schema':'IRE_V5_VIDEO1_FIRST40_SCOPED_EDUCATION_GATE_V1',
       'original_40_windows_claims_reviewed':97,'raw_rule_claims_examined':20,
       'official_narrow_subfacts_education_only':15,'regulatory_composite_open':5,
       'not_regulatory_fact':77,'deduplicated_education_overlay_nodes':9,
       'official_sources_checked_in_chat_not_pinned':len(j['official_sources']),
       'formal_B04_master_claim_merge':False,'original_full_claims_approved':0,
       'source_1_to_40_private_replayed_by_ci':False,
       'financial_personal_advice_release':'NO_GO',
       'replay':private_source_verify(j,private_root) if private_root else None}
    return x

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--private-root',type=Path)
    p.add_argument('--query',type=str)
    a=p.parse_args();r=verify(a.root.resolve(),a.private_root)
    if a.query:r['retrieval_example']=retrieval(a.query,load(a.root.resolve()))
    print(json.dumps(r,ensure_ascii=False,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
