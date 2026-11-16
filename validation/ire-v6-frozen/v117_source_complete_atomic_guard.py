"""V117 private-owner full-source atomic-claim graph and evidence gate.

Requires actual privately supplied full SRT and a ChatGPT-curated proposal graph;
validates source hashes, complete parent ownership, cue/claim/evidence links,
conditions and rebuttal graph, without asserting independent semantic recall.
No private speech, source or claims enter the returned public receipt.
No network, model APIs, automatic fiscal approval, or knowledge mutation.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from time import perf_counter_ns
from urllib.parse import urlsplit
from v115_full_video_bridge import parse_exact_srt, sha as source_sha

_SHA=re.compile(r'[0-9a-f]{64}\Z')
_VIDEO=re.compile(r'[A-Za-z0-9_-]{11}\Z')
_PARENT=re.compile(r'P\d{3,6}\Z')
_ATOM=re.compile(r'A\d{3,6}\Z')
_KINDS={'FACT_CANDIDATE','HYPOTHESIS','QUESTION','RECOMMENDATION','OPINION','ANALOGY','EXCEPTION'}
_STANCES={'AFFIRMED','CONDITIONAL','CORRECTED','HYPOTHETICAL','REBUTTAL','QUOTED','NEGATED'}
_RISKS={'LOW','MEDIUM','HIGH','CRITICAL'}
_ALLOWED_RELATIONS={
'SAME_PREMISE_DIFFERENT_SCOPE','TOPIC_ELABORATION','DISTINCT_CAUSAL_MECHANISMS',
'REPHRASE_MISSING_CONJUNCTION','TEMPORAL_CONDITION',
'OBSERVED_STATS_VS_REGULATORY_TRIGGER','ASSET_TYPE_EXCEPTION',
'REPEATED_REDEMPTION_MECHANISM','ANALOGY_TO_ASSERTION',
'REFUTABLE_PRICE_EQUIVALENCE','MARKET_PRICE_VS_REDEMPTION_VALUE',
'EXPLICIT_NOT_PRINCIPAL','CONTINGENT_MARKET_LOSS','LOSS_REALIZATION',
'TAX_CONDITION_SEPARATE','HYPOTHETICAL_QUESTION_RESPONSE',
'CUSTODY_MECHANISM','CUSTODIAN_SEPARATION',
'HYPOTHETICAL_ALTERNATIVE_BRANCH','BRANCH_VS_BLANKET_ASSURANCE',
'RISK_CONTRADICTION','BLANKET_NO_RISK','MARKET_LOSS_VS_SYSTEM_LOSS',
'DERIVATIVE_EXCEPTION_INSUFFICIENT','EXCEPTION_VS_RECOMMENDATION'}
_PR= {'MASTER116':frozenset({'GOMHEE-C17','GOMHEE-C24','GOMHEE-C34'}),
      'P4_22':frozenset({'EDU-ETF-NAV-TRACKING','EDU-ETF-TOTAL-COST-DECISION'})}
_MASTER='ab5af7eea02e65d5e36174546a2a94f4cc642d92'
_P4='bfb446ffb1dd40caa1ed03088d088c9a1ba7490f'
_OFFICIAL_HOSTS=('krx.co.kr','fsc.go.kr','law.go.kr','fss.or.kr','nts.go.kr',
                'nabo.go.kr','samsungfund.com','kcmi.re.kr','easylaw.go.kr')
# Two categories deliberately cannot be mistaken for legislative primary body:
_EVIDENCE_CLASSES={'EXCHANGE_RULE','REGULATOR','ACTUAL_LAW','GOV_EDUCATION',
                   'PUBLIC_BUDGET','RESEARCH_EXPLANATION','ISSUER_DISCLOSURE'}
_REQUIRED_FLAGS={
'v75_gold_404_recovered':False,'historical_full_dedup_complete':False,
'any_financial_fact_approved':False,'any_personal_advice_approved':False,
'speaker_audio_verified':False,'original_video_verified':False,
'independent_gold':False,'recall':None,'precision':None,'p0_go':False}

class V117SourceProofError(ValueError):pass

def _check(ok, label):
    if not ok:raise V117SourceProofError('V117_'+label)

def digest(data):
    return source_sha(json.dumps(data,ensure_ascii=False,sort_keys=True,
                  separators=(',',':'),allow_nan=False))

def _unique_indices(value,n,*,empty=False):
    return (type(value) is list and (bool(value) or empty) and
            all(type(v) is int and 1<=v<=n for v in value) and
            value==sorted(set(value)))

def _official_url(url):
    _check(type(url) is str and len(url)<=1200,'OFFICIAL_URL_TYPE')
    try:u=urlsplit(url)
    except ValueError as e:raise V117SourceProofError('V117_OFFICIAL_URL_PARSE') from e
    _check(u.scheme=='https' and u.hostname and u.username is None and
           u.password is None and u.port is None and not u.fragment,
           'OFFICIAL_URL_NOT_TRUSTED')
    _check(any(u.hostname==h or u.hostname.endswith('.'+h)
               for h in _OFFICIAL_HOSTS),'OFFICIAL_URL_HOST')
    return url

def audit_private_original(*,raw_srt,graph,expected_srt_sha256,
                           expected_archive_sha256,checked_date='2026-11-14'):
    """No semantic GOLD. Original-source and claim/evidence graph integrity only."""
    ts=perf_counter_ns()
    _check(type(graph) is dict and graph.get('schema')==
           'V117_PRIVATE_REAL_SOURCE_ATOMIC_GRAPH_V1','GRAPH_SCHEMA')
    _check(type(expected_srt_sha256) is str and _SHA.fullmatch(expected_srt_sha256),
           'EXPECTED_SOURCE_PIN')
    _check(type(expected_archive_sha256) is str and _SHA.fullmatch(expected_archive_sha256),
           'EXPECTED_ARCHIVE_PIN')
    _check(graph.get('srt_sha256')==source_sha(raw_srt)==expected_srt_sha256,
           'ORIGINAL_SOURCE_DRIFT')
    _check(graph.get('zip_sha256')==expected_archive_sha256,'ORIGINAL_ARCHIVE_PIN')
    _check(type(graph.get('video_id')) is str and _VIDEO.fullmatch(graph['video_id']),
           'VIDEO_ID_INVALID')
    for flag,val in _REQUIRED_FLAGS.items():
        _check(flag in graph and graph[flag] is val,'UNPROVEN_'+flag.upper())
    _check(graph.get('legacy_master_git_blob_sha1')==_MASTER and
           graph.get('legacy_p4_git_blob_sha1')==_P4,'PREVIOUS_KNOWLEDGE_BLOB_DRIFT')
    cues=parse_exact_srt(raw_srt); n=len(cues)
    _check(n==graph.get('source_cues'),'CUE_COUNT_DRIFT')
    by={c['cue_index']:c for c in cues}
    _check(graph.get('cue_hashes')==[
        {'cue_index':c['cue_index'],'sha256':c['cue_sha256']} for c in cues],
        'ALL_CUE_ORIGINAL_HASH_DRIFT')
    t_source=perf_counter_ns()-ts
    t_semantic=perf_counter_ns()
    parent_map={};p_cues=[]
    for p in graph.get('parents',[]):
        _check(type(p) is dict,'PARENT_OBJECT_REQUIRED')
        pid=p.get('parent_id')
        _check(type(pid) is str and _PARENT.fullmatch(pid) and pid not in parent_map,
               'PARENT_ID_INVALID_OR_DUPLICATE')
        lo,hi=p.get('first_cue'),p.get('last_cue')
        _check(type(lo) is int and type(hi) is int and 1<=lo<=hi<=n,'PARENT_RANGE')
        inds=list(range(lo,hi+1));p_cues+=inds
        _check(p.get('cue_indices')==inds and type(p.get('speech_act')) is str and
               p.get('speaker')=='NARRATOR_PRESUMED_UNVERIFIED' and
               p.get('scope_source_verified') is True,'PARENT_SCOPE_OR_SPEAKER')
        _check(p.get('source_text_sha256')==source_sha(' '.join(by[j]['text'] for j in inds)),
               'PARENT_PRIVATE_TEXT_CHANGED')
        parent_map[pid]=p
    _check(bool(parent_map) and p_cues==list(range(1,n+1)),'SOURCE_PARENT_GAP_OR_OVERLAP')
    amap={};all_atomic_cues=set();high_ids=set();risk_dist={}
    for atom in graph.get('atoms',[]):
        _check(type(atom) is dict,'ATOM_OBJECT_REQUIRED')
        aid=atom.get('atom_id')
        _check(type(aid) is str and _ATOM.fullmatch(aid) and aid not in amap,
               'ATOM_ID_DUPLICATE_OR_INVALID')
        idx=atom.get('cue_indices')
        _check(_unique_indices(idx,n),'ATOM_SOURCE_REF_NOT_SORTED')
        _check(atom.get('cue_sha256')==[by[j]['cue_sha256'] for j in idx],
               'ATOM_ORIGINAL_CUE_DRIFT')
        _check(atom.get('source_span_sha256')==source_sha(''.join(by[j]['cue_sha256'] for j in idx)),
               'ATOM_SPAN_DIGEST_DRIFT')
        actual_parents=[p['parent_id'] for p in graph['parents']
                        if set(p['cue_indices']).intersection(idx)]
        _check(atom.get('related_parents')==actual_parents,'ATOM_PARENT_LINK_CHANGED')
        _check(type(atom.get('proposition_private')) is str and
               8<=len(atom['proposition_private'].strip())<=800,
               'ATOM_SEMANTIC_TEXT_REQUIRED')
        _check(atom.get('speech_act') in _KINDS and atom.get('stance') in _STANCES and
               atom.get('risk') in _RISKS,'ATOM_SPEECH_ROLE_UNKNOWN')
        _check(type(atom.get('evidence_key')) is str and atom.get('evidence_key'),
               'ATOM_EVIDENCE_REF_MISSING')
        _check(atom.get('speaker')=='NARRATOR_PRESUMED_UNVERIFIED',
               'SPEAKER_AUDIO_UNVERIFIED')
        for f in ('independent_gold','source_truth_certified','official_evidence_verified',
                  'financial_fact_approved','personal_advice_approved'):
            _check(atom.get(f) is False,'ATOM_UNEARNED_'+f.upper())
        amap[aid]=atom;all_atomic_cues.update(idx)
        risk_dist[atom['risk']]=risk_dist.get(atom['risk'],0)+1
        if atom['risk'] in ('HIGH','CRITICAL'):high_ids.add(aid)
    _check(bool(amap),'NO_ATOMS_PRESENT')
    # Not all cues must be claims. The 100% claim is only about parent cue ownership.
    edges=set();cross_parents=0
    for e in graph.get('cross_parent_links',[]):
        _check(type(e) is dict and set(e)=={'from_atom','to_atom','relation'},
               'EDGE_FIELDS')
        a,b,t=e['from_atom'],e['to_atom'],e['relation']
        _check(a in amap and b in amap and a!=b and t in _ALLOWED_RELATIONS,
               'EDGE_INVALID_OR_UNRECOGNIZED')
        _check((a,b,t) not in edges,'DUPLICATED_EDGE')
        edges.add((a,b,t))
        if set(amap[a]['related_parents'])!=set(amap[b]['related_parents']):
            cross_parents+=1
    if any(a['speech_act']=='EXCEPTION' for a in amap.values()):
        _check(any('EXCEPTION' in t for _,_,t in edges),
               'SPEAKER_EXCEPTION_LOST_FROM_GRAPH')
    obligations=set();watch_high=0
    for w in graph.get('watch_source_obligations',[]):
        _check(type(w) is dict and set(w)=={'first_cue','last_cue','risk_label','must_high_risk'},
               'WATCH_FIELDS')
        lo,hi=w['first_cue'],w['last_cue'];label=w['risk_label']
        _check(type(lo) is int and type(hi) is int and 1<=lo<=hi<=n and
               type(label) is str and 5<=len(label)<=60,'WATCH_SPAN_INVALID')
        _check(label not in obligations,'WATCH_REUSED')
        obligations.add(label)
        matched=[a for a in amap.values() if set(a['cue_indices']) & set(range(lo,hi+1))]
        _check(len(matched)>0,'WATCH_NOT_REVIEWED')
        _check(any(a['evidence_key']!='NONE' for a in matched),
               'WATCH_FINANCE_EVIDENCE_MISSING')
        _check(type(w['must_high_risk']) is bool, 'WATCH_RISK_FLAG_INVALID')
        if w['must_high_risk']:
            _check(any(a['risk'] in ('HIGH','CRITICAL') for a in matched),
                   'WATCH_HIGH_RISK_NOT_DECLARED')
            watch_high+=1
    _check(bool(obligations),'NO_SOURCE_HIGH_RISK_WATCH')
    t_semantic=perf_counter_ns()-t_semantic
    t_finance=perf_counter_ns()
    seen=set();url_count=set();status_count={}
    for f in graph.get('financial_docket',[]):
        _check(type(f) is dict,'EVIDENCE_ROW_OBJECT_REQUIRED')
        aid=f.get('atom_id')
        _check(aid in amap and aid not in seen and amap[aid]['evidence_key']!='NONE',
               'EVIDENCE_MISSING_DUPLICATED_OR_CONTEXT_ONLY')
        _check(f.get('cue_indices')==amap[aid]['cue_indices'] and
               f.get('as_of')==checked_date,'EVIDENCE_SOURCE_OR_DATE_DRIFT')
        refs=f.get('issuer_reference_urls')
        _check(type(refs) is list and bool(refs) and len(refs)<=12,
               'EVIDENCE_OFFICIAL_REFERENCE_MISSING')
        _check(f.get('evidence_status')=='OPEN_PRIMARY_BODY_AND_APPLICABILITY' and
               f.get('rule_effective_date_verified') is False and
               f.get('official_source_body_pinned_sha256') is None and
               f.get('personal_account_scope_verified') is False and
               f.get('approved') is False,'FALSE_REGULATORY_OR_PERSONAL_APPROVAL')
        _check(f.get('has_counterevidence_candidate') ==
               (amap[aid]['risk'] in ('CRITICAL','HIGH')),
               'FINANCE_RISK_COUNTEREVIDENCE_LINK_DRIFT')
        for x in refs:
            _check(type(x) is dict and set(x)=={'issuer_category','url'} and
                   x['issuer_category'] in _EVIDENCE_CLASSES,'EVIDENCE_ISSUER_CLASS')
            url_count.add(_official_url(x['url']))
        seen.add(aid)
        status_count[f['evidence_status']]=status_count.get(f['evidence_status'],0)+1
    _check(seen=={aid for aid,a in amap.items() if a['evidence_key']!='NONE'},
           'ATOMIC_FINANCE_CENSUS_NOT_EXHAUSTIVE')
    _check(high_ids<=seen,'HIGH_RISK_WITHOUT_EVIDENCE')
    t_finance=perf_counter_ns()-t_finance
    t_prior=perf_counter_ns()
    priors=set()
    for p in graph.get('prior_relations',[]):
        _check(type(p) is dict and set(p)=={
               'atom_id','namespace','prior_id','relation','dedup_verified'},
               'PRIOR_FIELDS')
        _check(p['atom_id'] in amap and p['namespace'] in _PR and
               p['prior_id'] in _PR[p['namespace']] and
               p['relation']=='RELATED_ONLY_PENDING' and p['dedup_verified'] is False,
               'PRIOR_FALSE_EQUIVALENCE_OR_UNKNOWN_ID')
        rel=(p['atom_id'],p['namespace'],p['prior_id'])
        _check(rel not in priors,'DUPLICATED_PRIOR_RELATION')
        priors.add(rel)
    t_prior=perf_counter_ns()-t_prior
    return {'schema':'V117_ORIGINAL_173_SOURCE_ATOMIC_FINANCE_CUSTODY_NO_GOLD_V1',
            'video_id':graph['video_id'],'srt_sha256':expected_srt_sha256,
            'original_archive_sha256':expected_archive_sha256,
            'all_parent_cues':len(p_cues),'original_cues':n,
            'parent_clusters':len(parent_map),'atomic_proposals':len(amap),
            'atomic_source_cues_union':len(all_atomic_cues),
            'cross_atom_relationships':len(edges),'cross_parent_relationships':cross_parents,
            'source_risk_obligations':len(obligations),'source_risk_obligations_reviewed':len(obligations),'source_high_risk_obligations':watch_high,
            'high_risk_candidates':len(high_ids),'official_pending_rows':len(seen),
            'unique_official_research_links':len(url_count),
            'read_only_prior_candidates':len(priors),'knowledge_merge_count':0,
            'source_cue_count_unaccounted':n-len(p_cues),
            'source_semantic_digest_sha256':digest(graph['atoms']),
            'source_evidence_digest_sha256':digest(graph['financial_docket']),
            'source_prior_digest_sha256':digest(graph['prior_relations']),
            'source_graph_digest_sha256':digest(graph),
            'source_parse_and_hash_wall_ns':t_source,
            'semantic_graph_audit_wall_ns':t_semantic,
            'official_docket_audit_wall_ns':t_finance,
            'read_only_prior_audit_wall_ns':t_prior,
            'official_primary_body_sha_verified':False,
            'financial_fact_approved':0,
            'model_semantic_wall_ns':None,
            'official_search_wall_ns':None,
            'open_resolution_wall_ns':None,
            'independent_gold':False,'precision':None,'recall':None,
            'high_risk_recall':None,'research_complete':False,'p0_go':False}

def guard_public_v117_receipt(receipt):
    """Exact public digest/census guard for V117, not semantic recall proof."""
    _check(type(receipt) is dict and receipt.get('schema')==
           'V117_PUBLIC_173_CUE_SOURCE_CUSTODY_AND_NO_GOLD_V1',
           'PUBLIC_SCHEMA')
    expected={'video_id':'Yb_5prWaqhk',
              'original_archive_sha256':'00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd',
              'srt_sha256':'19ce2a37a37079dc0a6ea4dde3d031bdc2b7bb990f0506fd1e0610442dbf0145',
              'original_cues':173,'all_parent_cues':173,'parent_clusters':19,
              'atomic_proposals':46,'atomic_source_cues_union':169,
              'cross_atom_relationships':26,'cross_parent_relationships':14,
              'source_risk_obligations':10,'source_risk_obligations_reviewed':10,
              'source_high_risk_obligations':7,'high_risk_candidates':17,
              'official_pending_rows':41,'open_finance_evidence_rows':41,
              'read_only_prior_candidates':6,'knowledge_merge_count':0,
              'source_cue_count_unaccounted':0,'five_stage_checkpoint_count':5,
              'checkpoint_reentry_idempotent':True,
              'source_graph_digest_sha256':'d9eaf6b3f483c633a9d1c85df43f936d3e6a67bc4390abfceae3561a8ca512c8',
              'official_primary_body_sha_verified':False,
              'finance_fact_approved':0,'personal_advice_approved':False,
              'model_call_automated':False,'original_audio_verified':False,
              'original_screen_verified':False,
              'historical_v75_404_recovered':False,
              'original_owner_source_published':False,
              'owner_source_check_date':'2026-11-14',
              'model_semantic_wall_ns':None,'official_search_wall_ns':None,
              'open_resolution_wall_ns':None,'independent_gold':False,
              'precision':None,'recall':None,'high_risk_recall':None,
              'research_complete':False,'p0_go':False}
    for k,value in expected.items():
        _check(k in receipt and receipt[k] is value if value is None or type(value) is bool
               else receipt.get(k)==value,'PUBLIC_EXPECTED_'+k.upper())
    for key in ('source_semantic_digest_sha256','source_evidence_digest_sha256',
                'source_prior_digest_sha256','checkpoint_sha256'):
        _check(type(receipt.get(key)) is str and _SHA.fullmatch(receipt[key]),
               'PUBLIC_HASH_'+key.upper())
    t=receipt.get('source_structure_stage_wall_ns')
    _check(type(t) is dict and set(t)=={'source_parse_and_hash_wall_ns',
           'semantic_graph_audit_wall_ns','official_docket_audit_wall_ns',
           'read_only_prior_audit_wall_ns'} and
           all(type(v) is int and v>=0 for v in t.values()),
           'PUBLIC_STAGE_TIMINGS')
    return {'public_receipt_matched_source_sha_and_counts':True,
            'structural_custody_pass':True,'independent_accuracy_no_score':True,
            'full_research_complete':False,'p0_go':False}
