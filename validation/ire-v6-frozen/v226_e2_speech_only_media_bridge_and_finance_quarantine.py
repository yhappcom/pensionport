"""Source-first media speech recovery without visual/factual certification.

Reusable validation layer for original SRT -> frozen native V6 -> all cue
review -> E3 preview. Reviewer decisions are NOT independent gold or E4 grants.
All original source/user claim text stays in owner-private inputs, not this code.
"""
from __future__ import annotations
import json
from collections import Counter
from copy import deepcopy
from hashlib import sha256 as stdsha
from ire.v6.errors import InvalidInput
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from v176_chat_engine_loop import make_original_plan

MEDIA_SCHEMA="IRE_V226_MEDIA_SPEECH_TO_V6_NATIVE_UNAPPROVED_V1"
QUARANTINE_SCHEMA="IRE_V226_E3_FINANCE_CONTRADICTION_AND_UNRESOLVED_TERM_QUARANTINE_V1"


def require(ok, why):
    if not ok:
        raise InvalidInput("V226_"+why)


def hash_bytes(b):
    require(type(b) is bytes,"INPUT_NOT_BYTES")
    return stdsha(b).hexdigest()


def strict_json(blob, why):
    try: 
        d=json.loads(blob.decode('utf-8'))
    except (UnicodeError,ValueError,TypeError) as exc:
        raise InvalidInput('V226_JSON_'+why+'_INVALID') from exc
    require(type(d) is dict,why+'_NOT_OBJECT')
    return d


def verify_media_and_quarantine(source, old, new, source_media, bridge, old_census,
                                new_census, finance, quarantine, old_e3, new_e3,
                                relations, internal_metric):
    """All semantic decisions retained as unapproved hypotheses, fail closed.

    No semantic or legal correctness is inferred from this structural audit.
    """
    require(type(bridge) is dict and bridge.get('schema')==MEDIA_SCHEMA,'MEDIA_SCHEMA')
    require(bridge.get('original_media_evidence_resolved') is False and
            bridge.get('e2_gold_pass') is False and bridge.get('financial_facts_approved') is False,'MEDIA_NOT_HOLD')
    source_sha=source.source_sha256
    require(old.get('source_sha256')==new.get('source_sha256')==bridge.get('source_sha256')==source_sha,'SOURCE_CHANGED')
    for x in [old,new]:
        audit_host_atomic_exchange(source,x)
    old_atoms=old['atoms'];new_atoms=new['atoms'];oldids={r['claim_id'] for r in old_atoms};newmap={r['claim_id']:r for r in new_atoms}
    require(len(oldids)==len(old_atoms) and len(newmap)==len(new_atoms),'DUPLICATE_ATOM')
    require(all(newmap.get(a['claim_id'])==a for a in old_atoms),'SURVIVING_ATOMS_CHANGED')
    require(type(source_media) is dict and type(source_media.get('unapproved_speech_claims')) is list,'OLD_MEDIA_INVALID')
    old_media={x['id']:x for x in source_media['unapproved_speech_claims']}
    rows=bridge.get('rows');require(type(rows) is list and len(rows)<=100,'BRIDGE_ROWS')
    require(len(new_atoms)==len(old_atoms)+len(rows),'SPEECH_ATOM_COUNT')
    require(len(rows)==bridge.get('prior_legacy_media_claims_unapproved')==bridge.get('new_unapproved_native_draft_claims'),'BRIDGE_COUNTS')
    require(set(newmap)-oldids=={r['new_unapproved_native_claim_id'] for r in rows},'NEW_CLAIMS_NOT_BRIDGE')
    seen_media=set();all_media_cues=set();added_ref_cues=set();
    for r in rows:
        require(type(r) is dict,'BRIDGE_ROW_INVALID')
        legacy=r.get('legacy_source_only_speech_id');cid=r.get('new_unapproved_native_claim_id')
        require(type(legacy) is str and legacy in old_media and legacy not in seen_media,'BRIDGE_OLD_ID')
        seen_media.add(legacy)
        require(type(cid) is str and cid in newmap and cid not in oldids,'BRIDGE_NEW_ID')
        atom=newmap[cid]
        require(atom['proposition']==r.get('proposition_text_as_spoken_not_visual_fact'),'BRIDGE_PROPOSITION_DRIFT')
        require(atom['kind']=='HYPOTHETICAL' and atom['stance']=='UNRESOLVED' and
            atom['speaker']=='UNKNOWN' and atom['as_of'] is None,'MEDIA_AUTHORITY_FORGED')
        require(r.get('audio_visual_verified') is False and r.get('financial_truth_approved') is False and
            r.get('independent_gold_verified') is False and r.get('e3_approved') is False and
            r.get('release_gate')=='HOLD_MEDIA_SOURCE_ONLY','MEDIA_FALSE_APPROVAL')
        refs=atom['source_refs'];indices=[x['cue_index'] for x in refs]
        require(indices==r.get('source_quote_cue_ids') and indices==sorted(set(indices)),'SOURCE_REFERENCE_DRIFT')
        origin=old_media[legacy]
        require(type(origin.get('source_refs')) is list and origin['source_refs'],'LEGACY_MEDIA_SOURCE_EMPTY')
        old_src=set()
        for q in origin['source_refs']:
            require(type(q) is dict and type(q.get('cue_index')) is int,'LEGACY_MEDIA_REF_SCHEMA')
            idx=q['cue_index'];require(1<=idx<=len(source.cues),'LEGACY_MEDIA_CUE_RANGE')
            actual=source.cues[idx-1].text
            require(q.get('quote')==actual,'LEGACY_MEDIA_QUOTE_DRIFT')
            if 'source_text_sha256' in q:
                require(q['source_text_sha256']==stdsha(actual.encode('utf-8')).hexdigest(),
                        'LEGACY_MEDIA_REF_SHA_DRIFT')
            old_src.add(idx)
        require(set(indices).issubset(old_src) and
                r.get('all_original_speech_span')==sorted(old_src),'MEDIA_SOURCE_SPAN_MISSING')
        all_media_cues.update(old_src)
        for x in refs:
            idx=x['cue_index'];require(type(idx) is int and 1<=idx<=len(source.cues),'REF_INDEX')
            require(x['quote']==source.cues[idx-1].text,'QUOTE_NOT_FULL_SOURCE')
            require(old['cue_dispositions'][idx-1]['disposition']=='UNRESOLVED','OLD_MEDIA_NOT_UNRESOLVED')
            nr=new['cue_dispositions'][idx-1]
            require(nr['disposition']=='CANDIDATES' and nr['claim_ids']==[cid],'MEDIA_CUE_NOT_ANCHORED')
            added_ref_cues.add(idx)
        require(atom['owner_window_id']==source.owner(indices[0]),'OWNER_WINDOW_CHANGED')
        require(set(indices).issubset(set(atom['context_cue_indices'])),'CONTEXT_DROPPED')
        require(atom['numeric_references']==[] and atom['exception_cue_indices']==[],'INVENTED_NUMERIC_EXCEPTION')
        require(len(r.get('missing_evidence',''))>=12 and type(r.get('media_relation_ids_for_followup')) is list,'REVIEW_MISSING')
    require(seen_media==set(old_media),'OLD_MEDIA_CLAIMS_DROPPED')
    require(all_media_cues==set(bridge.get('original_media_cue_ids',[])),'MEDIA_CUE_CENSUS_LOST')
    for oldrow,newrow in zip(old['cue_dispositions'],new['cue_dispositions']):
        idx=oldrow['cue_index'];require(idx==newrow['cue_index'],'CUE_ORDER_DRIFT')
        if idx not in added_ref_cues:
            require(oldrow==newrow,'UNRELATED_CUE_MUTATED')
        else:
            require({k:v for k,v in oldrow.items() if k not in {'note','disposition','claim_ids'}}==
                    {k:v for k,v in newrow.items() if k not in {'note','disposition','claim_ids'}},'MEDIA_NUMBER_MUTATED')
    require(new_census.get('original_source_sha256')==old_census.get('original_source_sha256')==source_sha,'CENSUS_SOURCE_CHANGED')
    require(type(new_census.get('rows')) is list and len(new_census['rows'])==len(source.cues),'CENSUS_GAP')
    require(all(new_census['rows'][i-1]['original_audio_or_screen_review_required'] for i in all_media_cues),'MEDIA_FLAG_REMOVED')
    require(all(new_census['rows'][i-1]['classification'] in
        {'MEDIA_SPEECH_SOURCE_ANCHORED_BUT_VISUAL_HOLD','MEDIA_SPEECH_CONTEXT_STILL_VISUAL_HOLD'} for i in all_media_cues),'MEDIA_QUARANTINE_DROPPED')
    for o,n in zip(old_census['rows'],new_census['rows']):
        if o['cue_index'] not in all_media_cues:
            require(o==n,'OTHER_CUE_CENSUS_MODIFIED')
        else:
            if o['cue_index'] in added_ref_cues:
                require(n['source_anchor_claim_ids']==new['cue_dispositions'][o['cue_index']-1]['claim_ids'],'CENSUS_REF_MISMATCH')
    require(new_census.get('classification_counts')==dict(Counter(x['classification'] for x in new_census['rows'])),'CENSUS_COUNTS_DRIFT')
    require(set(new_census.get('media_evidence_cues_still_quarantined',[]))==all_media_cues,'STILL_MEDIA_REVIEW_MISSING')
    require(new_census.get('independent_gold_available') is False and new_census.get('financial_fact_approved') is False,'CENSUS_GOLD_FORGED')
    # All explicitly contradicted and terminology-unresolved claims stay unavailable for knowledge.
    require(quarantine.get('schema')==QUARANTINE_SCHEMA,'FINANCE_QUARANTINE_SCHEMA')
    require(quarantine.get('financial_facts_approved')==0 and quarantine.get('independent_gold_verified') is False,'FINANCE_QUARANTINE_AUTHORITY')
    status_by_id={r['claim_id']:r['status'] for r in finance['rows']}
    qrows=quarantine.get('rows');require(type(qrows) is list and len(qrows)<=10000,'QUARANTINE_ROWS')
    require(quarantine.get('original_financial_false_or_overbroad_atoms')==sum(q.get('disposition')=='QUARANTINE_FINANCIAL_CONCEPT_CONTRADICTION' for q in qrows) and
            quarantine.get('tracking_terminology_unresolved_atoms')==sum(q.get('disposition')=='HOLD_TRACKING_TERMINOLOGY_ORIGINAL_AUDIO_REQUIRED' for q in qrows),'FINANCE_QUARANTINE_COUNTS')
    require(len(set(r.get('claim_id') for r in qrows))==len(qrows),'QUARANTINE_DUPLICATES')
    for q in qrows:
        cid=q.get('claim_id');require(cid in oldids and cid in status_by_id,'QUARANTINE_CLAIM_MISSING')
        require(q.get('native_proposition_spoken_verbatim')==newmap[cid]['proposition'],'QUARANTINE_SPOKEN_CHANGED')
        if q.get('disposition')=='QUARANTINE_FINANCIAL_CONCEPT_CONTRADICTION':
            require(status_by_id[cid]=='SPOKEN_CLAIM_CONTRADICTED_OR_TOO_BROAD','WRONG_CONTRADICTION_CLASS')
        else:
            require(q.get('disposition')=='HOLD_TRACKING_TERMINOLOGY_ORIGINAL_AUDIO_REQUIRED' and
                    status_by_id[cid]=='TERMINOLOGY_NOT_RESOLVED','WRONG_TERMINOLOGY_CLASS')
        require(q.get('original_speaker_claim_retained_for_audit') is True and
                q.get('correction_is_not_source_atom') is True,'SPOKEN_REPLACED_BY_CORRECTION')
        require(all(q.get(k) is False for k in ['financial_fact_approved','e3_final_approved','e4_approved','e5_published','official_primary_regulation_bytes_verified']),'FINANCE_FALSE_APPROVAL')
    require(set(status_by_id)>=set(q['claim_id'] for q in qrows),'FINANCE_NOT_IN_OFFICIAL_REVIEW')
    # E3 task must carry every prior claim and all restored dependency IDs.
    require(type(new_e3.get('task_rows')) is list and len(new_e3['task_rows'])==len(new_atoms),'E3_TASK_COUNT')
    old_tasks={t['claim_id']:t for t in old_e3['task_rows']}
    new_tasks={t['claim_id']:t for t in new_e3['task_rows']}
    require(len(old_tasks)==len(old_e3['task_rows']) and len(new_tasks)==len(new_atoms),'E3_DUPLICATE')
    require(set(new_tasks)==set(newmap),'E3_CLAIM_ID_CLOSURE')
    require(new_e3.get('source_sha256')==source_sha and
            new_e3.get('source_claim_tasks')==len(new_atoms) and
            new_e3.get('v225_full_relation_count')==len(relations.get('rows',[])) and
            new_e3.get('v225_full_legacy_candidate_endpoints_preserved') is True,'E3_HISTORY_LOST')
    for cid,o in old_tasks.items():
        n=new_tasks[cid]
        for k,v in o.items():require(n.get(k)==v,'OLD_E3_CONTENT_MUTATED')
        require(n.get('v226_independent_gold_verified') is False and n.get('v226_financial_facts_approved') is False,'E3_GOLD_FORGED')
    for r in rows:
        t=new_tasks[r['new_unapproved_native_claim_id']]
        require(t['primary_cue_ids']==r['source_quote_cue_ids'] and
                set(t['v225_relation_candidate_ids'])==set(r['media_relation_ids_for_followup']),'E3_MEDIA_LINK_MISSING')
        require(t['v226_e3_financial_release_disposition']=='HOLD_MEDIA_UNVERIFIED' and
                t['e3_final_approved'] is False and t['financial_fact_approved'] is False,'E3_MEDIA_APPROVED')
    for q in qrows:
        expect='QUARANTINE_CONTRADICTED' if q['disposition'].startswith('QUARANTINE') else 'HOLD_TRACKING_TERMINOLOGY'
        require(new_tasks[q['claim_id']].get('v226_e3_financial_release_disposition')==expect,'QUARANTINE_NOT_IN_E3')
    require(new_e3['globally_unassigned_original_media_quarantines']==old_e3['globally_unassigned_original_media_quarantines'],'GLOBAL_MEDIA_RELATION_LOST')
    require(new_e3['v225_full_relation_rows_sha256']==old_e3['v225_full_relation_rows_sha256'],'GRAPH_DIGEST_CHANGED')
    require(type(relations.get('rows')) is list and
            len(relations['rows'])==old_e3.get('v225_full_relation_count'),'GRAPH_NOT_PRESERVED')
    require(all(t.get('financial_fact_approved') is False and t.get('v226_financial_facts_approved') is False for t in new_e3['task_rows']),'KNOWLEDGE_RELEASE_BYPASS')
    require(all(new_e3.get(k) is False for k in ['e3_final_approved','e4_approved','e5_published','external_independent_gold_provided']),'E3_PROMOTION_BYPASS')
    if 'before_draft_native_claims' in internal_metric:
        require(internal_metric['before_draft_native_claims']==len(old_atoms) and
                internal_metric.get('after_draft_native_claims')==len(new_atoms) and
                internal_metric.get('source_only_media_speech_candidates_missing_before')==len(rows) and
                internal_metric.get('source_only_media_speech_candidates_missing_after')==0,
                'INTERNAL_CANDIDATE_COUNT_FALSE')
    require(internal_metric.get('not_an_independent_semantic_recall_measurement') is True and
            internal_metric.get('certified_gold_precision') is None and
            internal_metric.get('certified_gold_recall') is None and
            internal_metric.get('certified_high_risk_false_negatives') is None and
            internal_metric.get('e2_final_pass') is False,'FAKE_GOLD_MEASUREMENT')
    a=audit_host_atomic_exchange(source,new)
    return {'schema':'IRE_V226_E2_MEDIA_SPEECH_AND_FINANCE_QUARANTINE_REPLAY_RECEIPT_V1',
      'original_srt_source_sha256':source_sha,'original_cues_replayed':len(source.cues),
      'previous_native_atoms':len(old_atoms),'unapproved_native_atoms_after':len(new_atoms),
      'media_speech_cue_refs_now_native':len(added_ref_cues),'media_original_cues_hold':len(all_media_cues),
      'new_media_speech_atoms':len(rows),'source_cues_with_native':a['cues_with_candidates'],
      'unresolved_cue_count':a['unresolved_cues'],'suspicious_no_atom_cues':a['suspicious_no_atom_cues'],
      'financial_contradictions_quarantined':quarantine['original_financial_false_or_overbroad_atoms'],
      'tracking_terms_unresolved_held':quarantine['tracking_terminology_unresolved_atoms'],
      'full_legacy_relations_retained':len(relations['rows']),
      'independent_gold_recall_measured':False,'external_visual_or_audio_verified':False,
      'e3_e4_e5_authorized':False,'knowledge_published':0,
      'status':'REAL_SOURCE_FROZEN_V6_CUSTODY_PASS_E2_GOLD_HOLD'}


def audit_v226_original_kit(blobs:dict,expected_hashes:dict):
    required={'srt','old_native','new_native','old_media','media_bridge','old_census',
              'new_census','official21','finance_quarantine','old_e3','new_e3','relations32','coverage_metric'}
    require(type(blobs) is dict and set(blobs)==required,'KIT_MANIFEST')
    require(type(expected_hashes) is dict and set(expected_hashes)==required,'KIT_HASH_MANIFEST')
    for k in sorted(required):
        require(hash_bytes(blobs[k])==expected_hashes[k],k.upper()+'_BYTE_HASH_DRIFT')
    old_metadata=strict_json(blobs['old_native'],'OLD_NATIVE')
    video_id=old_metadata.get('video_id')
    require(type(video_id) is str and len(video_id)>=3,'VIDEO_ID_MISSING')
    source,plan=make_original_plan(blobs['srt'],video_id=video_id,window_size=20,
                     expected_source_sha256=expected_hashes['srt'])
    docs={k:strict_json(blobs[k],k.upper()) for k in required-{'srt'}}
    require(docs['media_bridge'].get('prior_native_sha256')==expected_hashes['old_native'],'OLD_NATIVE_HASH')
    require(docs['media_bridge'].get('new_native_sha256')==expected_hashes['new_native'],'NEW_NATIVE_HASH')
    require(docs['finance_quarantine'].get('new_native_sha256')==expected_hashes['new_native'],'QUARANTINE_NATIVE_HASH')
    require(docs['new_census'].get('native_exchange_sha256')==expected_hashes['new_native'],'CENSUS_NATIVE_HASH')
    require(docs['new_e3'].get('native_sha256')==expected_hashes['new_native'],'E3_NATIVE_HASH')
    require(docs['new_e3'].get('v226_media_to_native_review_sha256')==expected_hashes['media_bridge'],'E3_MEDIA_HASH')
    require(docs['new_e3'].get('v226_financial_contradiction_quarantine_sha256')==expected_hashes['finance_quarantine'],'E3_QUARANTINE_HASH')
    receipt=verify_media_and_quarantine(source,docs['old_native'],docs['new_native'],
           docs['old_media'],docs['media_bridge'],docs['old_census'],docs['new_census'],
           docs['official21'],docs['finance_quarantine'],docs['old_e3'],docs['new_e3'],
           docs['relations32'],docs['coverage_metric'])
    receipt['pinned_input_hashes']=dict(sorted(expected_hashes.items()))
    return receipt