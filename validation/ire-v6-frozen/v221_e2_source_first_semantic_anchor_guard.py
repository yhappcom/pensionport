"""V221: exact-byte source-first primary evidence alignment, NOT independent gold.

A V6 atomic exchange can structurally PASS even when its primary quote is a
transition cue rather than the sentence substantiating a claim. This guard
compares a preserved source-only discourse docket to the old/new owner native
exchanges, and admits a *source-anchoring repair* only with an exact source cue,
owner window update, unchanged unapproved claim semantics, and a complete delta.
No original video/audio, speaker identity or independent accuracy is certified.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json
import re
from typing import Any

from ire.v6.errors import InvalidInput
from ire.v6.codec import sha256
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from v176_chat_engine_loop import make_original_plan

SCHEMA = "IRE_V221_REAL_ETF_SOURCE_FIRST_TO_NATIVE_PRIMARY_ANCHOR_CUSTODY_V1"


def need(test: Any, reason: str) -> None:
    if not test:
        raise InvalidInput("V221_" + reason)


def pin_bytes(raw: bytes, data: dict, digest: str, label: str):
    need(type(raw) is bytes and type(data) is dict and type(digest) is str and
         bool(re.fullmatch('[0-9a-f]{64}', digest)),label+"_TYPE")
    need(sha256(raw)==digest,label+"_BYTE_CHANGED")
    try:
        parsed=json.loads(raw)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise InvalidInput('V221_'+label+'_JSON_INVALID') from exc
    need(parsed==data,label+'_OBJECT_DIFFERS_FROM_PINNED_BYTES')


def audit_source_first_native_alignment(raw_srt: bytes, source_docket: dict, source_bytes: bytes,
        old_native: dict, old_bytes: bytes, new_native: dict, new_bytes: bytes,
        patch: dict, patch_bytes: bytes, crosswalk: dict, crosswalk_bytes: bytes,
        *, expected_hashes: dict, window_size: int = 20) -> dict:
    names={'source':raw_srt,'source_docket':source_bytes,'old_native':old_bytes,
           'new_native':new_bytes,'patch':patch_bytes,'crosswalk':crosswalk_bytes}
    need(type(expected_hashes) is dict and set(expected_hashes)==set(names), 'EXPECTED_SHA_FIELDS')
    for key,val in names.items():
        need(type(val) is bytes and type(expected_hashes[key]) is str and
             bool(re.fullmatch('[0-9a-f]{64}',expected_hashes[key])) and
             sha256(val)==expected_hashes[key],key.upper()+'_SOURCE_SHA_DRIFT')
    for key,content in [('source_docket',source_docket),('old_native',old_native),
                        ('new_native',new_native),('patch',patch),('crosswalk',crosswalk)]:
        pin_bytes(names[key],content,expected_hashes[key],key.upper())
    need(type(window_size) is int and 1<=window_size<=1000 and
         type(new_native.get('video_id')) is str, 'SOURCE_ID_OR_WINDOW_SIZE')
    source,_=make_original_plan(raw_srt,new_native['video_id'],
        expected_source_sha256=expected_hashes['source'],window_size=window_size)
    ro=audit_host_atomic_exchange(source,old_native)
    rn=audit_host_atomic_exchange(source,new_native)
    need(old_native['video_id']==new_native['video_id'] and
         ro['original_scoped_cues_enumerated']==rn['original_scoped_cues_enumerated'] and
         len(old_native['atoms'])==len(new_native['atoms']) and
         source_docket.get('schema')=='IRE_V221_REAL_ETF_250_SOURCE_FIRST_INTERNAL_DISCOURSE_ATOM_REVIEW_DRAFT_V1' and
         source_docket.get('video_id')==source.video_id and
         source_docket.get('source_sha256')==source.source_sha256 and
         source_docket.get('original_cues_covered')==len(source.cues) and
         source_docket.get('source_internal_review_not_independent_gold') is True and
         source_docket.get('author_was_exposed_to_prior_engine_project_context') is True and
         source_docket.get('not_a_blind_gold_dataset') is True and
         source_docket.get('financial_facts_approved') is False and
         source_docket.get('e2_final_pass') is False, 'SOURCE_DOCKET_IDENTITY_OR_FALSE_GOLD')
    units=source_docket.get('claims')
    need(type(units) is list and 1<=len(units)<=1000 and
         source_docket.get('source_first_dispositions')==len(units),
         'SOURCE_DOCKET_UNIT_COUNT')
    covered=set();unit_by_id={};kinds=Counter()
    for pos,u in enumerate(units,1):
        need(type(u) is dict and type(u.get('source_only_id')) is str and
             u['source_only_id']==f'SRC221-{pos:03d}' and
             type(u.get('cue_start')) is int and type(u.get('cue_end')) is int and
             1<=u['cue_start']<=u['cue_end']<=len(source.cues) and
             type(u.get('source_refs')) is list and
             len(u['source_refs'])==u['cue_end']-u['cue_start']+1 and
             type(u.get('proposition_from_original_unverified')) is str and
             len(u['proposition_from_original_unverified'].strip())>=4 and
             type(u.get('discourse_kind')) is str and
             type(u.get('risk_tags')) is list and
             u.get('source_review_status')=='CHATGPT_SOURCE_FIRST_INTERNAL_NOT_BLIND_GOLD' and
             u.get('speaker_verified') is False and
             u.get('truth_certified') is False and u.get('e2_pass') is False,
             'SOURCE_UNIT_SCHEMA_OR_FALSE_CERTIFICATION')
        for i,ref in enumerate(u['source_refs'],start=u['cue_start']):
            original=source.cues[i-1].text
            need(type(ref) is dict and ref.get('cue_index')==i and
                 ref.get('quote')==original and
                 ref.get('source_text_sha256')==sha256(original.encode('utf8')),
                 'SOURCE_UNIT_QUOTE_AND_CUE_CHANGED')
        covered.update(range(u['cue_start'],u['cue_end']+1))
        unit_by_id[u['source_only_id']]=u;kinds[u['discourse_kind']]+=1
    need(covered==set(range(1,len(source.cues)+1)) and
         kinds==Counter(source_docket.get('source_kinds',{})),
         'SOURCE_FIRST_FULL_CUE_COVERAGE_INCOMPLETE')
    allold={a['claim_id']:a for a in old_native['atoms']}
    allnew={a['claim_id']:a for a in new_native['atoms']}
    need(len(allold)==len(old_native['atoms']) and len(allnew)==len(new_native['atoms'])
         and set(allold)==set(allnew) and all(a.get('speaker')=='UNKNOWN' and
         a.get('stance')=='UNRESOLVED' for a in new_native['atoms']),
         'NATIVE_CLAIMS_CHANGED_OR_SPEAKER_PROMOTED')
    changes={}
    for cid,before in allold.items():
        after=allnew[cid]
        unchanged={k for k in before if before[k]!=after[k]}
        if not unchanged:continue
        need(unchanged.issubset({'source_refs','owner_window_id','context_cue_indices'}),
             'UNAUTHORIZED_NATIVE_MEANING_FIELD_CHANGED')
        need(type(before.get('source_refs')) is list and type(after.get('source_refs')) is list and
             len(before['source_refs'])==len(after['source_refs'])==1,
             'NATIVE_PRIMARY_REFS_COUNT_CHANGED')
        a=before['source_refs'][0]['cue_index'];b=after['source_refs'][0]['cue_index']
        need(a!=b and before['source_refs'][0]['quote']==source.cues[a-1].text and
             after['source_refs'][0]['quote']==source.cues[b-1].text and
             after['owner_window_id']==source.owner(b) and
             after['context_cue_indices']==sorted(set(before['context_cue_indices'])|{a,b}),
             'UNAUTHORIZED_PRIMARY_OWNER_OR_CONTEXT_DRIFT')
        changes[cid]=(a,b)
    need(type(patch.get('corrections')) is list and
         patch.get('schema')=='IRE_V221_PRIVATE_ETF_REAL_ATOM_SEMANTIC_PRIMARY_EVIDENCE_PATCH_V1' and
         patch.get('source_sha256')==expected_hashes['source'] and
         patch.get('previous_native_sha256')==expected_hashes['old_native'] and
         patch.get('corrected_native_sha256')==expected_hashes['new_native'] and
         patch.get('reviewed_primary_corrections')==len(changes)==len(patch['corrections']) and
         patch.get('native_atoms_after')==len(new_native['atoms']) and
         patch.get('speaker_verified') is False and
         patch.get('independent_gold') is False and
         patch.get('e2_pass') is False, 'PATCH_CUSTODY_OR_FALSE_APPROVAL')
    seen=set()
    for item in patch['corrections']:
        need(type(item) is dict and type(item.get('claim_id')) is str and
             item['claim_id'] in changes and item['claim_id'] not in seen,
             'PATCH_ROW_MISSING_OR_DUPLICATED')
        seen.add(item['claim_id']);a,b=changes[item['claim_id']]
        need(item.get('prior_primary_cue_index')==a and
             item.get('corrected_primary_cue_index')==b and
             item.get('prior_primary_quote')==source.cues[a-1].text and
             item.get('new_primary_quote')==source.cues[b-1].text and
             item.get('prior_primary_source_text_sha256')==sha256(source.cues[a-1].text.encode('utf8')) and
             item.get('new_primary_source_text_sha256')==sha256(source.cues[b-1].text.encode('utf8')) and
             item.get('prior_owner_window_id')==allold[item['claim_id']]['owner_window_id'] and
             item.get('corrected_owner_window_id')==allnew[item['claim_id']]['owner_window_id'] and
             item.get('proposition')==allnew[item['claim_id']]['proposition'] and
             item.get('financial_truth_approved') is False,
             'PATCH_ROW_SOURCE_OR_MEANING_MISMATCH')
    need(seen==set(changes), 'PATCH_CLAIM_NOT_FULLY_RECONCILED')
    need(crosswalk.get('schema')=='IRE_V221_ETF250_SOURCE_FIRST_TO_NATIVE_MEANING_ANCHOR_ALIGNMENT_INTERNAL_HOLD_V1' and
         crosswalk.get('source_sha256')==expected_hashes['source'] and
         crosswalk.get('source_first_review_sha256')==expected_hashes['source_docket'] and
         crosswalk.get('previous_native_sha256')==expected_hashes['old_native'] and
         crosswalk.get('corrected_native_sha256')==expected_hashes['new_native'] and
         crosswalk.get('crosswalk_review_uses_native_candidates') is True and
         crosswalk.get('independent_gold_certified') is False and
         crosswalk.get('precision_recall_measured') is False and
         crosswalk.get('financial_fact_approved') is False and
         crosswalk.get('e2_final_pass') is False,
         'CROSSWALK_SOURCE_OR_FALSE_GOLD')
    rows=crosswalk.get('rows')
    need(type(rows) is list and len(rows)==len(units) and
         crosswalk.get('source_units_reviewed')==len(rows),
         'CROSSWALK_ROW_INCOMPLETE')
    seen_native=set();old_good=set();new_good=set();media=[]
    for i,row in enumerate(rows):
        u=units[i]
        need(type(row) is dict and row.get('source_only_id')==u['source_only_id'] and
             row.get('from_cue')==u['cue_start'] and row.get('to_cue')==u['cue_end'] and
             row.get('source_only_unit_kind')==u['discourse_kind'] and
             type(row.get('matched_native_ids')) is list and
             row['matched_native_ids']==sorted(set(row['matched_native_ids'])) and
             all(type(c) is str and c in allnew for c in row['matched_native_ids']) and
             row.get('one_to_one_exact_semantic_equivalence_certified') is False and
             row.get('separate_blind_external_gold') is False and
             row.get('financial_fact_approved') is False,
             'CROSSWALK_INVALID_ROW_OR_FAKE_EQUIVALENCE')
        this=set(range(u['cue_start'],u['cue_end']+1));ids=row['matched_native_ids']
        before=sorted(cid for cid in ids if any(x['cue_index'] in this for x in allold[cid]['source_refs']))
        after=sorted(cid for cid in ids if any(x['cue_index'] in this for x in allnew[cid]['source_refs']))
        need(row.get('native_old_primary_in_source_unit')==before and
             row.get('native_new_primary_in_source_unit')==after,
             'CROSSWALK_PRIMARY_MISALIGNED_OR_SELF_REPORTED')
        state=row.get('source_first_review_disposition')
        if state=='UNAPPROVED_MEDIA_SPEECH_RETENTION_NOT_NATIVE':
            need(not ids and type(row.get('media_hold_packet_id')) is str and
                 row['media_hold_packet_id'] and u['discourse_kind']=='VISUAL_DEPENDENT_ASSERTION',
                 'MEDIA_SPEECH_SILENTLY_DROPPED_OR_PROMOTED')
            media.append(row['media_hold_packet_id'])
        elif state=='NATIVE_DISCOURSE_OVERLAP_NOT_EQUIVALENCE':need(bool(ids),'CLAIM_UNIT_WITHOUT_NATIVE')
        elif state=='SOURCE_TYPE_DISAGREEMENT_UNAPPROVED':
            need(bool(ids) and u['discourse_kind']=='NARRATIVE_NONCLAIM',
                 'SOURCE_TO_NATIVE_KIND_DISAGREEMENT_MUST_BE_EXPLICIT')
        elif state in ('NONCLAIM_OR_TRANSITION_PROVISIONAL','OPTIONAL_SOURCE_CONTEXT_OR_ANALOGY_REVIEW'):
            need(not ids and row.get('media_hold_packet_id') is None,'NONCLAIM_FALSE_NATIVE')
        else:need(False,'CROSSWALK_DISPOSITION_UNKNOWN')
        seen_native.update(ids);old_good.update(before);new_good.update(after)
    need(seen_native==set(allnew) and new_good==set(allnew) and
         crosswalk.get('native_claims_covered_by_any_source_unit')==len(seen_native) and
         crosswalk.get('old_native_primary_in_at_least_one_source_unit')==len(old_good) and
         crosswalk.get('new_native_primary_in_at_least_one_source_unit')==len(new_good) and
         len(media)==crosswalk.get('additional_unverified_screen_speech_claims') and
         len(media)==len(set(media)),
         'SOURCE_FIRST_CANDIDATE_COVERAGE_OR_MEDIA_CENSUS_DRIFT')
    return {'schema':SCHEMA,'source_sha256':expected_hashes['source'],
        'original_cues_source_pinned':len(source.cues),'source_first_meaning_units_reviewed':len(units),
        'old_native_anchors_in_corresponding_source_unit':len(old_good),
        'new_native_anchors_in_corresponding_source_unit':len(new_good),
        'native_provisional_claims':len(allnew),
        'primary_source_anchor_replacements':len(changes),
        'unapproved_visual_media_source_units_retained':len(media),
        'old_frozen_atom_digest':ro['atom_candidate_digest'],
        'new_frozen_atom_digest':rn['atom_candidate_digest'],
        'original_cues_with_any_native_candidate':rn['cues_with_candidates'],
        'unresolved_no_primary_cues':rn['unresolved_cues'],
        'one_to_one_exact_semantic_equivalence_certified':False,
        'source_first_review_externally_blind':False,
        'speaker_audio_certified':False,'financial_fact_truth_certified':False,
        'independent_precision_recall_measured':False,
        'owner_v176_history_verified':False,
        'e2_final_pass':False,'e3_e4_e5_authorized':False,'knowledge_published':False,
        'status':'PASS_SOURCE_PRIMARY_ANCHOR_CUSTODY_HOLD_INDEPENDENT_SEMANTIC_GOLD'}


def require_e2_release(evidence: dict):
    need(type(evidence) is dict and evidence.get('schema')==SCHEMA,
         'RECEIPT_REQUIRED')
    # No model-generated, provenance-only sidecar can attest independent gold.
    raise InvalidInput('V221_E2_INDEPENDENT_GOLD_AND_AUDIO_NOT_ESTABLISHED')