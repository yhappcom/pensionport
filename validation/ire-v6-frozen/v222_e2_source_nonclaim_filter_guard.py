"""V222: source-first negative-claim review, with retained provenance and gold HOLD.

One synthetic PASS cannot claim gold recall. The real release gate still requires
an independent source/gold assessment and eventual E3/E4 approval.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from v176_chat_engine_loop import make_original_plan

SCHEMA='IRE_V222_SOURCE_FIRST_EXPLICIT_NONCLAIM_FILTER_RECEIPT_V1'


def need(x,reason):
    if not x:
        raise InvalidInput('V222_'+reason)


def audit_source_first_nonclaim_filter(raw_srt, old_native,old_bytes,new_native,new_bytes,
        source_docket,source_bytes, negative_review,review_bytes,
        relation_graph,graph_bytes,*,expected_hashes,window_size=20):
    """Fail closed on *every* input and any unreviewed candidate suppression.

    Source-first nonclaim decisions are host-review artifacts, NOT independent gold.
    A `NO_ATOM` candidate remains a suspicious cue for later missed-claim auditing.
    """
    data={"source":raw_srt,"old_native":old_bytes,"new_native":new_bytes,
          "source_docket":source_bytes,"negative_review":review_bytes,"relation_graph":graph_bytes}
    need(type(expected_hashes) is dict and set(expected_hashes)==set(data),'EXPECTED_HASH_FIELDS')
    for key,value in data.items():
        h=expected_hashes[key]
        need(type(value) is bytes and type(h) is str and re.fullmatch(r'[0-9a-f]{64}',h)
             and sha256(value)==h,'PINNED_'+key.upper()+'_BYTES_CHANGED')
    typed={"old_native":old_native,"new_native":new_native,"source_docket":source_docket,
           "negative_review":negative_review,"relation_graph":relation_graph}
    for key,obj in typed.items():
        need(type(obj) is dict,'SCHEMA_'+key.upper())
        try:parsed=json.loads(data[key])
        except (UnicodeError,ValueError,TypeError) as err:
            raise InvalidInput('V222_INVALID_JSON_'+key.upper()) from err
        need(parsed==obj,'INPUT_OBJECT_BYTES_MISMATCH_'+key.upper())
    need(type(window_size) is int and 1<=window_size<=1000,'BAD_WINDOW_SIZE')
    need(type(new_native.get('video_id')) is str,'BAD_VIDEO_ID')
    source,_=make_original_plan(raw_srt,new_native['video_id'],
          expected_source_sha256=expected_hashes['source'],window_size=window_size)
    prior=audit_host_atomic_exchange(source,old_native)
    after=audit_host_atomic_exchange(source,new_native)
    need(type(source_docket.get('claims')) is list and
         source_docket.get('source_sha256')==source.source_sha256 and
         source_docket.get('video_id')==source.video_id and
         source_docket.get('original_cues_covered')==len(source.cues) and
         source_docket.get('not_a_blind_gold_dataset') is True and
         source_docket.get('source_internal_review_not_independent_gold') is True and
         source_docket.get('author_was_exposed_to_prior_engine_project_context') is True and
         source_docket.get('financial_facts_approved') is False and
         source_docket.get('e2_final_pass') is False,
         'SOURCE_DOCKET_NOT_INDEPENDENT_OR_CHANGED')
    lookup={};covered=set()
    for u in source_docket['claims']:
        need(type(u) is dict and type(u.get('source_only_id')) is str and
             u['source_only_id'] not in lookup and type(u.get('cue_start')) is int and
             type(u.get('cue_end')) is int and 1<=u['cue_start']<=u['cue_end']<=len(source.cues)
             and type(u.get('source_refs')) is list and
             len(u['source_refs'])==u['cue_end']-u['cue_start']+1,
             'SOURCE_UNITS_MALFORMED_OR_DUPLICATE')
        for cue_idx,ref in enumerate(u['source_refs'],start=u['cue_start']):
            orig=source.cues[cue_idx-1].text
            need(type(ref) is dict and ref.get('cue_index')==cue_idx and
                 ref.get('quote')==orig and ref.get('source_text_sha256')==sha256(orig.encode('utf-8')),
                 'SOURCE_UNIT_QUOTE_AND_SHA_MISMATCH')
            covered.add(cue_idx)
        lookup[u['source_only_id']]=u
    need(covered==set(range(1,len(source.cues)+1)),'SOURCE_UNIT_CUE_COVERAGE_GAP')
    need(relation_graph.get('schema')=='IRE_V218_E2_SOURCE_PINNED_UNAPPROVED_DEPENDENCY_GRAPH_V1' and
         type(relation_graph.get('cross_atom_edges')) is list and
         type(relation_graph.get('same_atom_relations')) is list and
         type(relation_graph.get('evidence_quarantines')) is list and
         relation_graph.get('source_sha256')==source.source_sha256 and
         relation_graph.get('source_relation_lineage_complete') is True and
         relation_graph.get('unreviewed_relations')==0 and
         relation_graph.get('same_source_quoted_semantic_gold_independent') is False and
         relation_graph.get('speaker_audio_verified') is False and
         relation_graph.get('video_screen_verified') is False and
         relation_graph.get('financial_facts_approved') is False and
         relation_graph.get('e2_final_pass') is False and
         type(relation_graph.get('relations_total')) is int and
         relation_graph['relations_total'] ==
             len(relation_graph['cross_atom_edges'])+len(relation_graph['same_atom_relations'])+
             len(relation_graph['evidence_quarantines']) and
         relation_graph.get('cross_atom_linked_unapproved') == len(relation_graph['cross_atom_edges']) and
         relation_graph.get('same_atom_context_unapproved') == len(relation_graph['same_atom_relations']) and
         relation_graph.get('audio_video_quarantined') == len(relation_graph['evidence_quarantines']),
         'GRAPH_SOURCE_OR_FALSE_APPROVAL_OR_CENSUS')
    need(negative_review.get('schema')==
         'IRE_V222_PRIVATE_ETF_SOURCE_FIRST_NONCLAIM_NEGATIVE_ADJUDICATION_V1' and
         negative_review.get('video_id')==source.video_id and
         negative_review.get('source_sha256')==source.source_sha256 and
         negative_review.get('old_native_sha256')==expected_hashes['old_native'] and
         negative_review.get('new_native_sha256')==expected_hashes['new_native'] and
         negative_review.get('source_docket_sha256')==expected_hashes['source_docket'] and
         negative_review.get('prior_cross_atom_graph_sha256')==expected_hashes['relation_graph'] and
         negative_review.get('review_context')==
           'SAME_CHATGPT_INTERNAL_SOURCE_FIRST_AFTER_PRIOR_ENGINE_EXPOSURE_NOT_INDEPENDENT_GOLD'
         and negative_review.get('independent_gold_certified') is False and
         negative_review.get('claim_omission_gold_certified') is False and
         negative_review.get('financial_facts_approved') is False and
         negative_review.get('e2_final_pass') is False and
         negative_review.get('e3_e4_e5_authorized') is False and
         negative_review.get('knowledge_published') is False,
         'NEGATIVE_REVIEW_INVALID_OR_FALSE_GOLD')
    decisions=negative_review.get('decisions')
    need(type(decisions) is list and 1<=len(decisions)<=50 and
         negative_review.get('rejected_native_claim_count')==len(decisions),
         'NEGATIVE_REVIEW_CENSUS')
    older={a['claim_id']:a for a in old_native['atoms']};newer={a['claim_id']:a for a in new_native['atoms']}
    need(len(older)==len(old_native['atoms']) and len(newer)==len(new_native['atoms']) and
         len(older)>=len(decisions) and
         negative_review.get('native_before')==len(older) and
         negative_review.get('native_after')==len(newer),
         'NATIVE_ATOM_COUNTS_CHANGED')
    removed=set(older)-set(newer)
    need(len(removed)==len(decisions) and all(older[cid]==newer[cid] for cid in newer) and
         negative_review.get('other_native_atoms_modified') is False and
         negative_review.get('other_discourse_edges_modified') is False,
         'UNAPPROVED_NATIVE_ATOM_LOSS_OR_MUTATION')
    need(all(a['speaker']=='UNKNOWN' and a['stance']=='UNRESOLVED' for a in newer.values()),
         'FALSE_SPEAKER_OR_STANCE_CERTIFICATION')
    graph_refs={v for e in relation_graph['cross_atom_edges'] for k,v in e.items()
                if k in ('from_atom_id','to_atom_id')}
    for e in relation_graph['same_atom_relations']:
        if type(e) is dict:
            for k in ('from_atom_id','to_atom_id','atom_id'):
                if type(e.get(k)) is str:graph_refs.add(e[k])
    need(not (removed & graph_refs),'REMOVED_ATOM_HAS_LIVE_DISCOURSE_EDGE')
    changed_rows={}
    for before,got in zip(old_native['cue_dispositions'],new_native['cue_dispositions']):
        if before!=got:
            need(type(before) is dict and type(got) is dict and
                 before.get('cue_index')==got.get('cue_index'), 'CUE_DISPOSITION_REORDERED')
            changed_rows[before['cue_index']]=(before,got)
    need(len(changed_rows)>=len(removed),'MISSING_CUE_DISPOSITION_CLEANUP')
    seen=set();allowed_changed=set()
    for d in decisions:
        need(type(d) is dict and type(d.get('claim_id')) is str and
             d['claim_id'] in removed and d['claim_id'] not in seen and
             type(d.get('source_only_id')) is str and d['source_only_id'] in lookup and
             d.get('rejection_code')=='NARRATIVE_INTRODUCTION_NOT_FINANCIAL_RECOMMENDATION' and
             type(d.get('reason')) is str and len(d['reason'].strip())>=15 and
             d.get('speaker_audio_verified') is False and
             d.get('financial_truth_approved') is False and
             d.get('independent_gold_verified') is False,
             'UNSUPPORTED_NONCLAIM_REJECTION')
        cid=d['claim_id'];seen.add(cid);u=lookup[d['source_only_id']];a=older[cid]
        need(u.get('discourse_kind')=='NARRATIVE_NONCLAIM' and
             u.get('source_review_status')=='CHATGPT_SOURCE_FIRST_INTERNAL_NOT_BLIND_GOLD' and
             u.get('speaker_verified') is False and u.get('truth_certified') is False and
             d.get('source_cue_start')==u['cue_start'] and
             d.get('source_cue_end')==u['cue_end'] and
             d.get('previous_claim')==a and
             a.get('kind')=='RECOMMENDATION' and
             set(x['cue_index'] for x in a['source_refs']).issubset(
               set(range(u['cue_start'],u['cue_end']+1))) and
             set(a['context_cue_indices']).issubset(
               set(range(u['cue_start'],u['cue_end']+1))),
             'FINANCIAL_CLAIM_NOT_A_PURE_INTRODUCTION')
        quotes=d.get('source_cues')
        need(type(quotes) is list and len(quotes)==u['cue_end']-u['cue_start']+1,
             'REJECTION_SOURCE_QUOTES_MISSING')
        for i,r in enumerate(quotes,start=u['cue_start']):
            text=source.cues[i-1].text
            need(type(r) is dict and r.get('cue_index')==i and r.get('quote')==text and
                 r.get('sha256')==sha256(text.encode('utf-8')),
                 'REJECTION_SOURCE_QUOTE_CHANGED')
        for ref in a['source_refs']:
            i=ref['cue_index'];allowed_changed.add(i)
            need(i in changed_rows,'REJECTED_CANDIDATE_CUE_STILL_PRESENT')
            before,got=changed_rows[i]
            need(d.get('previous_cue_disposition')==before and
                 d.get('corrected_cue_disposition')==got and
                 cid in before['claim_ids'] and cid not in got['claim_ids'] and
                 got['claim_ids']==[c for c in before['claim_ids'] if c!=cid] and
                 got['disposition']==('CANDIDATES' if got['claim_ids'] else 'NO_ATOM') and
                 {k:before[k] for k in ('cue_index','cue_text_sha256','numeric_tokens')}==
                 {k:got[k] for k in ('cue_index','cue_text_sha256','numeric_tokens')} and
                 len(got['note'].strip())>=8,
                 'UNAUTHORIZED_NONCLAIM_CUE_REWRITE')
    need(seen==removed and set(changed_rows)==allowed_changed,'UNREVIEWED_CUE_DISPOSITION_CHANGE')
    return {"schema":SCHEMA,"original_source_sha256":source.source_sha256,
            "source_cues_exact":len(source.cues),"source_only_units":len(lookup),
            "previous_native_atom_count":prior['proposed_atomic_claims'],
            "corrected_native_atom_count":after['proposed_atomic_claims'],
            "reviewed_nonclaim_removed_count":len(removed),
            "removed_atom_ids":sorted(removed),
            "previous_primary_cues":prior['cues_with_candidates'],
            "corrected_primary_cues":after['cues_with_candidates'],
            "corrected_unresolved_cues":after['unresolved_cues'],
            "suspicious_noatom_cues_kept_for_further_review":after['suspicious_no_atom_cues'],
            "previous_atom_digest":prior['atom_candidate_digest'],
            "corrected_atom_digest":after['atom_candidate_digest'],
            "known_graph_edges_changed":0,
            "speaker_verified":False,"financial_facts_approved":False,
            "independent_gold_certified":False,"precision_recall_computed":False,
            "e2_final_pass":False,"e3_e4_e5_authorized":False,
            "knowledge_published":False,
            "status":"PASS_EXACT_SOURCE_NONCLAIM_REJECTION_HOLD_INDEPENDENT_GOLD"}


def require_approved_e2_disposition(receipt):
    need(type(receipt) is dict and receipt.get('schema')==SCHEMA,
         'NOT_A_V222_SOURCE_REVIEW_RECEIPT')
    # No gold claims or audio/video ground truth can be created by this sidecar.
    raise InvalidInput('V222_E2_GOLD_SPEAKER_AND_FINANCIAL_EVIDENCE_NOT_VERIFIED')


def audit_postfilter_native_risk_and_cue_census(raw_srt,native,native_bytes,
        finance,finance_bytes,census,census_bytes,*,expected_hashes,window_size=20):
    """Bind 250 cue dispositions and 65 atom risk rows to the *same* native SHA.

    Re-anchoring/suppression must not quietly leave the prior version's finance
    or cue ledger in place. Flags remain human/model annotations, not gold.
    """
    data={'source':raw_srt,'native':native_bytes,'finance':finance_bytes,'census':census_bytes}
    need(type(expected_hashes) is dict and set(expected_hashes)==set(data),'SIDECAR_EXPECTED_HASH_FIELDS')
    for k,v in data.items():
        h=expected_hashes[k]
        need(type(v) is bytes and type(h) is str and re.fullmatch(r'[0-9a-f]{64}',h)
             and sha256(v)==h,'SIDECAR_'+k.upper()+'_SHA_CHANGED')
    for k,obj in [('native',native),('finance',finance),('census',census)]:
        need(type(obj) is dict,'SIDECAR_'+k.upper()+'_SCHEMA')
        try:d=json.loads(data[k])
        except (UnicodeError,ValueError,TypeError) as exc:
            raise InvalidInput('V222_SIDECAR_JSON_'+k.upper()) from exc
        need(d==obj,'SIDECAR_'+k.upper()+'_OBJECT_CHANGED')
    need(type(window_size) is int and 1<=window_size<=1000 and
         type(native.get('video_id')) is str,'SIDECAR_SOURCE_PLAN')
    source,_=make_original_plan(raw_srt,native['video_id'],
         expected_source_sha256=expected_hashes['source'],window_size=window_size)
    native_receipt=audit_host_atomic_exchange(source,native)
    need(finance.get('schema')=='IRE_V219_PRIVATE_ALL_66_ATOMS_SEMANTIC_FINANCE_REVIEW_V1' and
         census.get('schema')=='IRE_V219_PRIVATE_SOURCE_FIRST_250_CUE_REVIEW_V1' and
         finance.get('source_sha256')==source.source_sha256 and
         census.get('original_source_sha256')==source.source_sha256 and
         finance.get('native_exchange_sha256')==expected_hashes['native'] and
         census.get('native_exchange_sha256')==expected_hashes['native'] and
         finance.get('original_audio_screen_available') is False and
         finance.get('human_independent_gold_available') is False and
         finance.get('external_independent_gold') is False and
         finance.get('e2_final_pass') is False and
         finance.get('knowledge_publication_authorized') is False and
         census.get('original_audio_screen_available') is False and
         census.get('independent_gold_available') is False and
         census.get('financial_fact_approved') is False and
         census.get('speaker_verified') is False and
         census.get('e2_final_pass') is False,
         'SIDECAR_CUSTODY_OR_FALSE_APPROVAL')
    atom_map={a['claim_id']:a for a in native['atoms']}
    finrows=finance.get('atoms')
    need(type(finrows) is list and len(finrows)==len(atom_map) and
         finance.get('all_atoms_reviewed_source_claims')==len(finrows),
         'SIDECAR_FINANCE_ATOM_CENSUS')
    present=set();risk=0;tag_types=set()
    for row in finrows:
        need(type(row) is dict and type(row.get('claim_id')) is str and
             row['claim_id'] in atom_map and row['claim_id'] not in present,
             'SIDECAR_FINANCE_ATOM_ID_MISSING_OR_DUPLICATE')
        cid=row['claim_id'];present.add(cid);a=atom_map[cid]
        refs=a['source_refs']
        tags=row.get('risk_tags')
        need(row.get('kind')==a['kind'] and
             row.get('primary_cue_ids')==[r['cue_index'] for r in refs] and
             row.get('primary_original_text_sha256')==[
                 sha256(source.cues[r['cue_index']-1].text.encode('utf-8')) for r in refs] and
             row.get('context_cue_indices')==a['context_cue_indices'] and
             row.get('numeric_source_token_cue_pairs')==[
                 {'cue_index':t['cue_index'],'source_token':t['token']} for t in a['numeric_references']] and
             type(tags) is list and len(set(tags))==len(tags) and
             all(type(t) is str and len(t)>2 for t in tags) and
             row.get('risk_review_status')==('HOLD_REQUIRES_OFFICIAL_OR_MEDIA_REVIEW' if tags
                                               else 'SOURCE_ANCHORED_BUT_NOT_INDEPENDENT_GOLD') and
             row.get('speaker_verified') is False and
             row.get('stance_confirmed') is False and
             row.get('financial_truth_certified') is False and
             row.get('semantically_gold_verified') is False and
             row.get('claim_approved') is False,
             'SIDECAR_FINANCE_RISK_SOURCE_OR_FALSE_GOLD')
        tag_types.update(tags);risk+=int(bool(tags))
    need(present==set(atom_map) and finance.get('risk_tagged_atom_count')==risk and
         finance.get('risk_tag_types')==sorted(tag_types),
         'SIDECAR_FINANCE_RISK_COUNT_DRIFT')
    bycue={i:[] for i in range(1,len(source.cues)+1)}
    ctx={i:[] for i in range(1,len(source.cues)+1)}
    for a in native['atoms']:
        for r in a['source_refs']:bycue[r['cue_index']].append(a['claim_id'])
        for i in a['context_cue_indices']:ctx[i].append(a['claim_id'])
    rows=census.get('rows')
    need(type(rows) is list and len(rows)==len(source.cues) and
         census.get('cue_count')==len(rows) and
         census.get('distinct_primary_claim_ids')==len(atom_map),
         'SIDECAR_CUE_CENSUS_INCOMPLETE')
    counts=Counter();flag=0
    for i,row in enumerate(rows,1):
        q=source.cues[i-1].text
        need(type(row) is dict and row.get('cue_index')==i and
             row.get('source_quote')==q and
             row.get('cue_text_sha256')==sha256(q.encode('utf-8')) and
             row.get('source_anchor_claim_ids')==sorted(bycue[i]) and
             row.get('context_claim_ids')==sorted(ctx[i]) and
             row.get('independent_omission_review_complete') is False and
             row.get('classification_is_chatgpt_source_review_not_external_gold') is True and
             row.get('financial_fact_approved') is False and
             row.get('e2_final_pass') is False,
             'SIDECAR_CUE_SOURCE_OR_ID_MISMATCH')
        kind=row.get('classification')
        if kind=='MEDIA_DEPENDENT_UNMAPPED_QUARANTINE':
            need(not bycue[i] and row.get('original_audio_or_screen_review_required') is True,
                 'SIDECAR_MEDIA_UNRESOLVED_WAS_SILENCED')
        else:
            correct=('SOURCE_ANCHORED_NATIVE_UNAPPROVED' if bycue[i] else
                     'SOURCE_CONTEXT_ONLY_UNAPPROVED' if ctx[i] else
                     'DISCOURSE_OR_NONCLAIM_PROVISIONAL')
            need(kind==correct,'SIDECAR_CUE_CLASSIFICATION_DRIFT')
        if native['cue_dispositions'][i-1]['disposition']=='NO_ATOM':
            need(not bycue[i] and kind in (
                'DISCOURSE_OR_NONCLAIM_PROVISIONAL','SOURCE_CONTEXT_ONLY_UNAPPROVED'),
                'SIDECAR_NONCLAIM_FALSE_APPROVAL')
        counts[kind]+=1
        flag+=int(row.get('original_audio_or_screen_review_required') is True)
    need(census.get('classification_counts')==dict(counts) and
         census.get('audio_screen_flagged_cue_count')==flag,
         'SIDECAR_CUE_CLASS_COUNT_OR_MEDIA_FLAG_DRIFT')
    return {'schema':'IRE_V222_POSTFILTER_SOURCE_RISK_CUE_CUSTODY_RECEIPT_V1',
        'source_sha256':source.source_sha256,'native_sha256':expected_hashes['native'],
        'cues_checked':len(source.cues),'native_atoms_checked':len(atom_map),
        'finance_risk_tagged_atoms':risk,'cues_by_classification':dict(counts),
        'audio_or_screen_risk_cues':flag,
        'suspicious_noatom_cues':native_receipt['suspicious_no_atom_cues'],
        'independent_gold_certified':False,'finance_truth_approved':False,
        'e2_final_pass':False,'e3_e4_e5_authorized':False,'knowledge_published':False,
        'status':'PASS_NEW_NATIVE_AND_SOURCE_SIDECARS_SYNCHRONIZED_GOLD_HOLD'}