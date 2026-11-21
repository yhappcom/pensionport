"""V225: preserve every historical candidate endpoint into a real E3 source review packet.

Earlier E3 reviews preserved 32 relation IDs but lost 22 candidate endpoint
occurrences across 17 relations by narrowing to one reviewed atom pair.
This guard retains both V217 candidate sets and V218 selected pairs, tagging
all additional candidates as text-only provisional rather than gold or approval.
Official KRX/FSC reference URLs are contextual, not certified regulation bytes.
"""
from __future__ import annotations
import json
from collections import Counter,defaultdict
from urllib.parse import urlparse
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from v176_chat_engine_loop import make_original_plan

SCHEMA='IRE_V225_E2_FULL_CANDIDATE_RELATION_CLOSURE_V1'
KEYS=frozenset({'srt','v217','v218','native','old_packet','graph','packet','official'})
REVIEW_STATUS=frozenset({'TEXT_RELATION_CANDIDATE_NOT_INDEPENDENT_GOLD',
 'CONTEXT_ONLY_PENDING_DETAIL','MEDIA_DEPENDENCY_UNVERIFIED'})
OFFICIAL_STATUS=frozenset({'CONCEPT_REFERENCE_SUPPORTED', 'SPOKEN_CLAIM_CONTRADICTED_OR_TOO_BROAD',
 'MATERIAL_LIMITATION_REQUIRED', 'TERMINOLOGY_NOT_RESOLVED', 'INVESTMENT_OPINION_NOT_FACT',
 'UNVERIFIED_SOURCE_OR_MARKET_HISTORY'})


def need(ok,code):
    if not ok:raise InvalidInput('V225_'+code)


def _parse(raw):
    try:
        value=json.loads(raw.decode('utf-8-sig',errors='strict'))
        need(type(value) is dict,'JSON_NOT_OBJECT')
        return value
    except (UnicodeDecodeError,ValueError,TypeError) as exc:
        raise InvalidInput('V225_BAD_JSON') from exc


def audit_v225_relation_closure(docs,expected_sha256,window_size=20):
    """Full fail-closed source-pinned review replay, without E2/E3/E4/E5 approvals."""
    try:
        return _audit(docs,expected_sha256,window_size)
    except InvalidInput:raise
    except (TypeError,KeyError,IndexError,ValueError,AttributeError,AssertionError,OverflowError) as exc:
        raise InvalidInput('V225_MALFORMED_INPUT') from exc


def _audit(docs,hashes,window_size):
    need(type(docs) is dict and type(hashes) is dict and set(docs)==set(hashes)==KEYS,'EXACT_PINNED_DOCUMENT_SET')
    for k,raw in docs.items():
        need(type(raw) is bytes and type(hashes[k]) is str and len(hashes[k])==64 and sha256(raw)==hashes[k],'SHA_'+k)
    need(type(window_size) is int and 1<=window_size<=1000,'WINDOW_SIZE')
    d={k:_parse(docs[k]) for k in KEYS-{'srt'}}
    source,_=make_original_plan(docs['srt'],d['native']['video_id'],expected_source_sha256=hashes['srt'],window_size=window_size)
    audit=audit_host_atomic_exchange(source,d['native'])
    need(audit['source_sha256']==hashes['srt'],'NATIVE_SOURCE_INVALID')
    native={r['claim_id']:r for r in d['native']['atoms']}
    need(len(native)==len(d['native']['atoms']) and native,'DUPLICATE_NATIVE_CLAIMS')
    v217,v218,graph=d['v217'],d['v218'],d['graph']
    need(v217.get('source_sha256')==v218.get('source_sha256')==graph.get('source_sha256')==hashes['srt'] and
         graph.get('native_sha256')==hashes['native'] and
         graph.get('v217_original_relation_sha256')==hashes['v217'] and
         graph.get('v218_selected_relation_review_sha256')==hashes['v218'],
         'RELATION_OR_SOURCE_SNAPSHOT')
    original=v217.get('relation_rows');reviewed=v218.get('rows');rows=graph.get('rows')
    need(type(original) is list and type(reviewed) is list and type(rows) is list and
         1<=len(original)==len(reviewed)==len(rows)<=5000,'RELATION_COUNT_MISMATCH')
    oldmap={r['relation_id']:r for r in reviewed}
    oldorig={r['relation_id']:r for r in original}
    newmap={r['relation_id']:r for r in rows}
    need(len(oldmap)==len(newmap)==len(oldorig)==len(rows) and set(oldmap)==set(newmap)==set(oldorig),'RELATION_ID_DUPLICATE_OR_LOSS')
    statuses=Counter();unhandled=0;missing_before=0;mutated_relations=0
    claim_relation=defaultdict(list)
    for r in rows:
        rid=r['relation_id'];old=oldmap[rid];history=oldorig[rid]
        need(old.get('relation_id')==history.get('relation_id')==rid and
             old.get('source_cue')==history.get('source_cue')==r.get('source_cue') and
             old.get('target_cue')==history.get('target_cue')==r.get('target_cue') and
             old.get('relation_type')==history.get('relation_type')==r.get('relation_type') and
             r.get('historical_review_state')==old.get('review_state'),'RELATION_ORIGINAL_MISMATCH')
        src_i=history['source_cue'];tgt_i=history['target_cue']
        need(type(src_i) is int and type(tgt_i) is int and 1<=src_i<=len(source.cues) and 1<=tgt_i<=len(source.cues),'CUE_OUTSIDE_SOURCE')
        texts=[source.cues[i-1].text for i in (src_i,tgt_i)]
        need(r.get('source_quote')==texts[0] and r.get('target_quote')==texts[1] and
             r.get('source_quote_sha256')==sha256(texts[0].encode('utf-8')) and
             r.get('target_quote_sha256')==sha256(texts[1].encode('utf-8')),'SOURCE_QUOTE_CHANGED')
        cs=history['source_native_ids'];ct=history['target_native_ids']
        need(type(cs) is list and type(ct) is list and cs==sorted(set(cs)) and ct==sorted(set(ct)) and
             set(cs+ct)<=set(native),'UNRESOLVED_HISTORICAL_ENDPOINT')
        need(r.get('candidate_source_atom_ids')==cs and r.get('candidate_target_atom_ids')==ct,'CANDIDATE_ENDPOINT_LOSS')
        oldsrc=old.get('source_atom_id');oldtgt=old.get('target_atom_id')
        selecteds=[oldsrc] if oldsrc else [];selectedt=[oldtgt] if oldtgt else []
        need(set(selecteds)<=set(cs) and set(selectedt)<=set(ct),'SELECTED_NOT_HISTORICAL_CANDIDATE')
        extra_s=sorted(set(cs)-set(selecteds));extra_t=sorted(set(ct)-set(selectedt))
        need(r.get('v218_selected_source_atom_ids')==selecteds and
             r.get('v218_selected_target_atom_ids')==selectedt and
             r.get('extra_source_atom_ids')==extra_s and r.get('extra_target_atom_ids')==extra_t,'SELECTED_OR_EXTRA_ENDPOINT_DRIFT')
        extras=r.get('extra_endpoint_reviews');expected=[(p,cid) for p,ls in (('source',extra_s),('target',extra_t)) for cid in ls]
        need(type(extras) is list and len(extras)==len(expected),'EXTRA_ENDPOINT_REVIEW_COUNT')
        need([(q.get('position'),q.get('claim_id')) for q in extras]==expected,'EXTRA_ENDPOINT_REVIEW_MISSING')
        for q in extras:
            need(q.get('status') in REVIEW_STATUS and type(q.get('source_first_reason')) is str and len(q['source_first_reason'].strip())>=16 and
                 q.get('independent_gold_verified') is False and q.get('financial_fact_approved') is False,'EXTRA_ENDPOINT_FALSE_APPROVAL')
            statuses[q['status']]+=1
        unhandled+=len(expected);missing_before+=len(expected)
        need(r.get('any_semantic_financial_approval') is False and
             r.get('relation_is_independent_gold') is False and
             r.get('original_audio_or_video_verified') is False,'RELATION_FALSE_APPROVAL')
        if extras:mutated_relations+=1
        for cid in set(cs+ct):
            claim_relation[cid].append(rid)
    need(graph.get('schema')==SCHEMA and graph.get('original_relation_count')==len(rows) and
         graph.get('reviewed_v218_selected_relation_count')==len(rows) and
         graph.get('historical_candidate_endpoints_preserved') is True and
         graph.get('relation_rows_with_extra_endpoints')==mutated_relations and
         graph.get('extra_endpoint_occurrences_retained')==unhandled and
         graph.get('source_quote_byte_hash_verified') is True and
         graph.get('independent_gold_certified') is False and
         graph.get('financial_facts_approved') is False and
         graph.get('e2_final_pass') is False,'GRAPH_FALSE_CERTIFICATION_OR_COUNTER')
    oldp,newp=d['old_packet'],d['packet']
    need(oldp.get('native_sha256')==newp.get('native_sha256')==hashes['native'] and
         oldp.get('source_sha256')==newp.get('source_sha256')==hashes['srt'] and
         len(oldp.get('task_rows',[]))==len(newp.get('task_rows',[]))==len(native),'E3_ATOM_COUNT_OR_PIN')
    need(newp.get('v225_full_relation_rows_sha256')==hashes['graph'] and
         newp.get('v225_official_concept_refs_sha256')==hashes['official'] and
         newp.get('v225_full_relation_count')==len(rows) and
         newp.get('v225_full_legacy_candidate_endpoints_preserved') is True and
         newp.get('v225_independent_gold_certified') is False and
         newp.get('v225_e3_final_approved') is False and
         newp.get('e3_final_approved') is False and
         newp.get('e4_approved') is False and newp.get('e5_published') is False,'E3_PREAPPROVAL_ONLY')
    basefields=set(oldp)-{'task_rows'}
    need(all(newp.get(k)==oldp[k] for k in basefields),'E3_EXISTING_RELATION_OR_CLAIM_CHANGED')
    original_tasks={r['claim_id']:r for r in oldp['task_rows']};tasks={r['claim_id']:r for r in newp['task_rows']}
    need(set(tasks)==set(original_tasks)==set(native),'E3_ID_MISMATCH')
    for cid,t in tasks.items():
        old=original_tasks[cid]
        need(type(t) is dict and all(t.get(k)==v for k,v in old.items()),'E3_TASK_MUTATION')
        need(t.get('v225_relation_candidate_ids')==sorted(set(claim_relation.get(cid,[]))),'E3_RELATION_ENDPOINT_NOT_EXPOSED')
        need(t.get('financial_fact_approved') is False and t.get('e3_final_approved') is False,'E3_CLAIM_FALSE_APPROVAL')
    official=d['official']
    need(official.get('schema')=='IRE_V225_OFFICIAL_CONTEXT_PRIORITY_CONCEPT_MAP_V1' and
         official.get('source_sha256')==hashes['srt'] and
         official.get('native_sha256')==hashes['native'] and
         official.get('official_original_response_bytes_certified') is False and
         official.get('legal_effective_version_approved') is False and
         official.get('per_claim_financial_approval') is False and
         official.get('independent_gold_certified') is False,'OFFICIAL_FALSE_CERTIFICATION')
    entries=official.get('rows')
    need(type(entries) is list and entries and len(entries)<=len(native),'OFFICIAL_PRIORITY_LIST')
    seen=set()
    for row in entries:
        cid=row.get('claim_id')
        need(cid in native and cid not in seen and row.get('claim_text')==native[cid]['proposition'] and
             row.get('status') in OFFICIAL_STATUS and type(row.get('reason')) is str and len(row['reason'].strip())>=25,'OFFICIAL_CLAIM_INCORRECT')
        refs=row.get('official_reference_urls')
        need(type(refs) is list and len(refs)>=1 and len(refs)<=5 and len(refs)==len(set(refs)) and
             all(type(url) is str and urlparse(url).scheme=='https' and urlparse(url).hostname in
             {'www.krx.co.kr','m.krx.co.kr','regulation.krx.co.kr','www.fsc.go.kr','open.krx.co.kr','kind.krx.co.kr'}
             for url in refs),'OFFICIAL_URL_INVALID')
        need(row.get('source_audio_verified') is False and
             row.get('official_primary_regulation_bytes_verified') is False and
             row.get('financial_fact_approved') is False and row.get('e3_final_approved') is False,
             'OFFICIAL_ROW_UNAUTHORIZED_APPROVAL')
        seen.add(cid)
    need(official.get('rows_reviewed')==len(entries) and
         official.get('rule_time_conflict_requires_live_version_check') is True and
         type(official.get('time_conflict_note')) is str and
         len(official.get('time_conflict_note').strip())>=40,
         'OFFICIAL_CONFLICT_SUPPRESSED')
    return {'schema':'IRE_V225_REAL_SOURCE_FULL_GRAPH_AND_OFFICIAL_REFERENCE_AUDIT_HOLD_V1',
            'original_source_sha256':hashes['srt'],'verified_cues':len(source.cues),
            'verified_unapproved_native_atoms':len(native),'original_relations_retained':len(rows),
            'relations_that_lost_candidates_in_previous_packet':mutated_relations,
            'candidate_endpoint_occurrences_lost_before':missing_before,
            'candidate_endpoint_occurrences_lost_now':0,
            'extra_endpoint_review_status_counts':dict(sorted(statuses.items())),
            'official_claims_contextually_reviewed_not_approved':len(entries),
            'e3_tasks_with_full_candidate_relation_closure':len(tasks),
            'official_original_bytes_verified':False,'independent_gold_certified':False,
            'e2_final_pass':False,'e3_final_approved':False,'e4_authorized':False,
            'e5_published':0,'status':'FULL_ORIGINAL_RELATION_CANDIDATE_CUSTODY_PASS_GOLD_OFFICIAL_AV_HOLD'}