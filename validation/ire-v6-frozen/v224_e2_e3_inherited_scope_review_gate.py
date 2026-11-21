"""E2/E3 bridge: exact-byte original, reviewed cross-cue scope inheritance, 65-atom text-only ChatGPT dispositions.

This is a reusable FAIL-CLOSED source/custody validator. It cannot decide the
semantic truth of a financial claim; that decision is supplied by an accountable
ChatGPT review sidecar and remains unapproved until independent gold and
regulated evidence are verified. Owner-private content never belongs in CI.
"""
from __future__ import annotations
import json
from copy import deepcopy
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlparse

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from v176_chat_engine_loop import make_original_plan

SCHEMA = 'IRE_V224_REAL_SOURCE_INDEX_SCOPE_AND_CHATGPT_TEXT_REVIEW_CUSTODY_V1'
DOC_KEYS = frozenset({'source', 'old_native', 'new_native', 'scope',
                       'old_finance', 'new_finance', 'old_census', 'new_census',
                       'review', 'old_packet', 'new_packet'})
REVIEW_STATES = frozenset({'TEXT_SUPPORTED_AS_SPOKEN',
                           'SOURCE_SUPPORTED_AS_SPOKEN_WITH_MATERIAL_QUALIFICATION',
                           'TRANSCRIPT_ASR_OR_MISSING_REFERENCE_HOLD'})
FINANCE_STATES = frozenset({'FICTIONAL_EXAMPLE_NOT_OBSERVED_MARKET_DATA',
                            'CORRECTION_OR_LIMITATION_REQUIRED_BEFORE_FINANCIAL_USE',
                            'TEMPORAL_OR_EMPIRICAL_UNVERIFIED',
                            'NORMATIVE_OR_EVALUATIVE_NOT_OBJECTIVE_FACT',
                            'CONCEPT_CHECKED_NO_LEGAL_SNAPSHOT_APPROVAL',
                            'UNVERIFIED_VISUAL_ASR_OR_FICTIONAL_EVIDENCE'})
APPROVAL = ('financial_fact_approved', 'e3_final_approved', 'e4_approved', 'e5_published')


def check(value, code):
    if not value:
        raise InvalidInput('V224_'+code)


def _decoded(docs, hashes):
    check(type(docs) is dict and type(hashes) is dict and set(docs)==set(hashes)==DOC_KEYS,
          'EXACT_INPUT_SET')
    objects={}
    for k in DOC_KEYS:
        raw=docs[k];digest=hashes[k]
        check(type(raw) is bytes and type(digest) is str and len(digest)==64 and
              sha256(raw)==digest,'RAW_SHA_'+k)
        if k=='source':continue
        try:obj=json.loads(raw.decode('utf-8-sig',errors='strict'))
        except (ValueError,UnicodeDecodeError) as exc:raise InvalidInput('V224_JSON_'+k) from exc
        check(type(obj) is dict,'JSON_SCHEMA_'+k)
        objects[k]=obj
    return objects


def _cue(i,source):
    check(type(i) is int and 1<=i<=len(source.cues),'CUE_REFERENCE_OUTSIDE_SOURCE')
    return source.cues[i-1].text


def _audit(docs,hashes,window_size):
    objects=_decoded(docs,hashes)
    old,new=objects['old_native'],objects['new_native']
    check(type(window_size) is int and 1<=window_size<=1000,'WINDOW_SIZE')
    check(type(new.get('video_id')) is str and new.get('video_id')==old.get('video_id'),
          'OWNER_VIDEO_ID')
    source,_=make_original_plan(docs['source'],new['video_id'],
             expected_source_sha256=hashes['source'],window_size=window_size)
    prev=audit_host_atomic_exchange(source,old)
    nxt=audit_host_atomic_exchange(source,new)
    check(prev['proposed_atomic_claims']==nxt['proposed_atomic_claims'] and
          prev['source_sha256']==nxt['source_sha256'] and
          type(old.get('atoms')) is list and type(new.get('atoms')) is list,
          'NATIVE_ATOM_LOSS')
    check(type(objects['scope'].get('source_cue_indices')) is list and
          1<=len(objects['scope']['source_cue_indices'])<=50,
          'SCOPE_SOURCE_REQUIRED')
    scope=objects['scope'];indices=scope['source_cue_indices']
    check(indices==sorted(set(indices)) and
          scope.get('source_cue_quotes')==[_cue(i,source) for i in indices] and
          scope.get('source_cue_sha256')==[
              sha256(_cue(i,source).encode('utf-8')) for i in indices] and
          scope.get('original_source_sha256')==hashes['source'] and
          scope.get('video_id')==new['video_id'] and
          type(scope.get('source_first_semantic_explanation')) is str and
          len(scope['source_first_semantic_explanation'])>=30 and
          scope.get('scope_kind')=='APPLICABILITY_OF_SIX_QUALITATIVE_SELECTION_CRITERIA' and
          scope.get('scope_value')=='PASSIVE_INDEX_ETF_FOCUS_NOT_ALL_ETFS' and
          scope.get('reviewed_by')=='CHATGPT_SOURCE_TEXT_SEMANTIC_JUDGMENT_NOT_EXTERNAL_GOLD' and
          scope.get('inherited_source_scope_is_reviewer_judgment') is True and
          scope.get('original_audio_verified') is False and
          scope.get('independent_gold_verified') is False and
          scope.get('no_financial_knowledge_approved') is True,
          'SCOPE_SOURCE_OR_FALSE_CERTIFICATION')
    targets=scope.get('applicable_native_claim_ids')
    check(type(targets) is list and targets and targets==sorted(set(targets)) and
          len(targets)<=len(new['atoms']), 'SCOPE_TARGET_LIST')
    o={a['claim_id']:a for a in old['atoms']}
    n={a['claim_id']:a for a in new['atoms']}
    check(set(o)==set(n) and set(targets)<=set(n),'SOURCE_ATOM_SET_DRIFT')
    for cid in o:
        before,after=o[cid],n[cid]
        keys={'context_cue_indices','condition_cue_indices'}
        check({k:v for k,v in before.items() if k not in keys}==
              {k:v for k,v in after.items() if k not in keys},
              'UNREVIEWED_NATIVE_CHANGE')
        expected_context=sorted(set(before['context_cue_indices']+indices)) if cid in targets else before['context_cue_indices']
        expected_condition=sorted(set(before['condition_cue_indices']+indices)) if cid in targets else before['condition_cue_indices']
        check(after['context_cue_indices']==expected_context and
              after['condition_cue_indices']==expected_condition and
              after['speaker']=='UNKNOWN' and after['stance']=='UNRESOLVED',
              'DROPPED_SCOPE_OR_FORGED_SPEAKER')
    for tag,root_old,root_new in (
       ('FINANCE',objects['old_finance'],objects['new_finance']),
       ('CENSUS',objects['old_census'],objects['new_census'])):
        check(root_old.get('native_exchange_sha256')==hashes['old_native'] and
              root_new.get('native_exchange_sha256')==hashes['new_native'],
              tag+'_NATIVE_HASH_DRIFT')
    fprev=objects['old_finance'];fnext=objects['new_finance']
    check(type(fprev.get('atoms')) is list and type(fnext.get('atoms')) is list and
          len(fprev['atoms'])==len(fnext['atoms'])==len(n),
          'FINANCE_ATOM_COUNT')
    f0={r['claim_id']:r for r in fprev['atoms']}
    f1={r['claim_id']:r for r in fnext['atoms']}
    check(set(f0)==set(f1)==set(n),'FINANCE_ID_CENSUS')
    for cid in n:
        oldrow,newrow=f0[cid],f1[cid]
        check({k:v for k,v in oldrow.items() if k!='context_cue_indices'}==
              {k:v for k,v in newrow.items() if k!='context_cue_indices'} and
              newrow['context_cue_indices']==n[cid]['context_cue_indices'] and
              newrow['kind']==n[cid]['kind'] and
              newrow['primary_cue_ids']==[i['cue_index'] for i in n[cid]['source_refs']] and
              newrow['claim_approved'] is False and
              newrow['financial_truth_certified'] is False,
              'FINANCE_RISK_OR_SCOPE_DRIFT')
    check(fnext.get('risk_tagged_atom_count')==sum(bool(x['risk_tags']) for x in f1.values()) and
          fnext.get('risk_tagged_atom_count')==fprev.get('risk_tagged_atom_count') and
          fnext.get('e2_final_pass') is False,'FINANCE_TAGS_REVIEW_REMOVED')
    cprev=objects['old_census'];cnext=objects['new_census']
    check(type(cprev.get('rows')) is list and type(cnext.get('rows')) is list and
          len(cprev['rows'])==len(cnext['rows'])==len(source.cues),'CENSUS_ALL_CUES_REQUIRED')
    tally=Counter()
    for i,(oldrow,newrow) in enumerate(zip(cprev['rows'],cnext['rows']),start=1):
        check(type(oldrow) is dict and type(newrow) is dict and
              oldrow.get('cue_index')==newrow.get('cue_index')==i and
              oldrow.get('cue_text_sha256')==newrow.get('cue_text_sha256')==
                 sha256(_cue(i,source).encode('utf-8')) and
              oldrow.get('source_quote')==newrow.get('source_quote')==_cue(i,source),
              'CENSUS_ORIGINAL_QUOTE_CHANGED')
        oldid=sorted(a['claim_id'] for a in o.values() if i in [r['cue_index'] for r in a['source_refs']])
        newid=sorted(a['claim_id'] for a in n.values() if i in [r['cue_index'] for r in a['source_refs']])
        ctx=sorted(a['claim_id'] for a in n.values() if i in a['context_cue_indices'])
        check(oldid==newid and newrow.get('source_anchor_claim_ids')==newid and
              newrow.get('context_claim_ids')==ctx,'CENSUS_DROPPED_SOURCE_CONTEXT')
        status=('SOURCE_ANCHORED_NATIVE_UNAPPROVED' if newid else
                'SOURCE_CONTEXT_ONLY_UNAPPROVED' if ctx else oldrow.get('classification'))
        check(newrow.get('classification')==status and
              newrow.get('financial_fact_approved') is False and
              newrow.get('e2_final_pass') is False,
              'CENSUS_FALSE_CLASSIFICATION')
        fields={'source_anchor_claim_ids','context_claim_ids','classification','nonclaim_or_discourse_explanation'}
        check({k:v for k,v in oldrow.items() if k not in fields}==
              {k:v for k,v in newrow.items() if k not in fields} and
              (status=='DISCOURSE_OR_NONCLAIM_PROVISIONAL' or
               'nonclaim_or_discourse_explanation' not in newrow),
              'CENSUS_SILENT_RISK_LOSS')
        tally[status]+=1
    check(cnext.get('classification_counts')==dict(sorted(tally.items())) and
          cnext.get('distinct_primary_claim_ids')==len(n) and
          cnext.get('e2_final_pass') is False,'CENSUS_COUNT_DRIFT')
    review=objects['review'];scope_hash=hashes['scope']
    check(review.get('original_source_sha256')==hashes['source'] and
          review.get('prior_native_exchange_sha256')==hashes['old_native'] and
          review.get('corrected_native_exchange_sha256')==hashes['new_native'] and
          review.get('inherited_global_scope_review_sha256')==scope_hash and
          review.get('reviewer')=='CHATGPT_ORIGINAL_SOURCE_AND_V223_E3_PACKET_REVIEW_NOT_BLIND_GOLD' and
          review.get('source_seen_prior_model_outputs') is True and
          review.get('source_only_review_completed') is True and
          review.get('independent_external_truth_gold_available') is False and
          review.get('official_context_source_raw_bytes_not_verified') is True and
          review.get('speaker_audio_verified') is False and
          review.get('video_graphics_verified') is False and
          review.get('financial_knowledge_approved')==0 and
          review.get('e3_semantic_review_dispositions_recorded') is True and
          review.get('e3_final_approved') is False and
          review.get('e4_approved') is False and
          review.get('e5_published') is False,
          'REVIEW_FALSE_GOLD_OR_APPROVAL')
    sources=review.get('official_context_sources')
    check(type(sources) is dict and sources and len(sources)<=20 and
          all(type(k) is str and type(u) is str and
              urlparse(u).scheme=='https' and
              urlparse(u).hostname in {'m.krx.co.kr','www.krx.co.kr','www.soletf.com','www.fsc.go.kr'}
              for k,u in sources.items()),
          'OFFICIAL_CONTEXT_REF_INVALID')
    rows=review.get('rows')
    check(type(rows) is list and len(rows)==len(n)==review.get('manual_text_only_review_count')==review.get('claimed_atom_total'),
          'REVIEW_NOT_ALL_ATOMS')
    seen=set();notelist=set();states=Counter()
    for row in rows:
        check(type(row) is dict and type(row.get('claim_id')) is str and
              row['claim_id'] in n and row['claim_id'] not in seen,'REVIEW_DUPLICATE_OR_UNKNOWN')
        cid=row['claim_id'];seen.add(cid);a=n[cid]
        check(row.get('current_native_kind')==a['kind'] and
              row.get('existing_proposition')==a['proposition'] and
              row.get('source_primary_cue_indices')==[r['cue_index'] for r in a['source_refs']] and
              row.get('actual_source_quotes')==[r['quote'] for r in a['source_refs']] and
              row.get('actual_source_full_cue_quote_sha256')==[
                  sha256(_cue(r['cue_index'],source).encode('utf-8')) for r in a['source_refs']] and
              row.get('inherited_index_etf_scope_cue_indices')==(indices if cid in targets else []) and
              row.get('scope_inheritance_verified_from_source_text')==(cid in targets),
              'REVIEW_UNSUPPORTED_CLAIM_OR_SCOPE')
        context_indices=row.get('support_context_cue_indices')
        check(type(context_indices) is list and context_indices and
              context_indices==sorted(set(context_indices)) and
              row.get('support_context_quotes')==[_cue(i,source) for i in context_indices] and
              set(r['cue_index'] for r in a['source_refs'])<=set(context_indices),
              'REVIEW_PRIMARY_CONTEXT_TAMPER')
        note=row.get('review_explanation')
        check(type(note) is str and len(note.strip())>=30 and
              note not in notelist and
              row.get('review_disposition') in REVIEW_STATES and
              row.get('financial_evidence_disposition') in FINANCE_STATES and
              type(row.get('official_concept_context_ref_ids')) is list and
              set(row['official_concept_context_ref_ids'])<=set(sources),
              'REVIEW_NOTE_MISSING_OR_BOILERPLATE')
        notelist.add(note);states[row['review_disposition']]+=1
        check(row.get('speaker_attribution')=='PRESENTER_VOICE_INFERRED_FROM_CONTINUOUS_TRANSCRIPT_TEXT_ONLY' and
              row.get('speaker_audio_verified') is False and
              row.get('native_stance_still_unresolved') is True and
              row.get('independent_gold_adjudicated') is False and
              row.get('audio_video_evidence_verified') is False and
              row.get('chatgpt_text_only_meaning_review_complete') is True and
              all(row.get(key) is False for key in APPROVAL),
              'REVIEW_FALSE_SPEAKER_OR_FINANCIAL_APPROVAL')
        calculation=row.get('reviewer_proposed_numeric_derivation_not_source_quote')
        if calculation is not None:
            check(type(calculation) is dict and set(calculation)=={
                  'nav_won','market_won','price_minus_nav_won','discount_percent_approx'},
                  'DERIVED_NUMBER_SCHEMA')
            nav,price=Decimal(str(calculation['nav_won'])),Decimal(str(calculation['market_won']))
            check(nav>0 and price>0 and
                  price-nav==Decimal(str(calculation['price_minus_nav_won'])) and
                  (100*(price-nav)/nav).quantize(Decimal('0.0001'),rounding=ROUND_HALF_UP)==
                     Decimal(str(calculation['discount_percent_approx'])),
                  'DERIVED_MATH_INCORRECT')
    check(seen==set(n) and sum(states.values())==len(n),'REVIEW_INCOMPLETE')
    before_packet=objects['old_packet'];new_packet=objects['new_packet']
    check(before_packet.get('native_sha256')==hashes['old_native'] and
          new_packet.get('native_sha256')==hashes['new_native'] and
          new_packet.get('source_sha256')==hashes['source'] and
          new_packet.get('semantic_convergence_atom_digest')==nxt['atom_candidate_digest'] and
          new_packet.get('actual_chatgpt_review_completed_for_all_65_unapproved_claims') is True and
          new_packet.get('actual_chatgpt_review_sha256')==hashes['review'] and
          new_packet.get('global_index_only_scope_review_sha256')==scope_hash and
          new_packet.get('external_independent_gold_provided') is False and
          new_packet.get('source_audio_video_verified') is False and
          new_packet.get('tasks_are_not_approved') is True and
          new_packet.get('e3_final_approved') is False and
          new_packet.get('e4_approved') is False and
          new_packet.get('e5_published') is False and
          new_packet.get('financial_truth_corrected_before_knowledge_published') is False,
          'E3_PACKET_MUST_BE_UNAPPROVED')
    check(before_packet.get('globally_unassigned_original_media_quarantines')==
          new_packet.get('globally_unassigned_original_media_quarantines') and
          before_packet.get('preserved_inter_atom_and_intra_atom_relations')==
          new_packet.get('preserved_inter_atom_and_intra_atom_relations'),
          'E3_MEDIA_OR_DEPENDENCY_LOSS')
    oldtasks=before_packet.get('task_rows');newtasks=new_packet.get('task_rows')
    check(type(oldtasks) is list and type(newtasks) is list and len(oldtasks)==len(newtasks)==len(n),
          'E3_ATOM_COUNT')
    oldmap={r['claim_id']:r for r in oldtasks}
    newmap={r['claim_id']:r for r in newtasks}
    check(set(oldmap)==set(newmap)==set(n),'E3_REVIEW_ATOM_OMISSION')
    reviewmap={r['claim_id']:r for r in rows}
    for cid in n:
        oldtask,newtask=oldmap[cid],newmap[cid]
        changefields={'source_context','condition_cue_indices',
                      'inherited_index_etf_scope_cue_indices',
                      'actual_chatgpt_text_review_disposition','actual_financial_evidence_disposition',
                      'e3_final_approved'}
        check({k:v for k,v in oldtask.items() if k not in changefields}==
              {k:v for k,v in newtask.items() if k not in changefields},
              'E3_SILENT_TASK_REWRITE')
        ctxt=[{'cue_index':i,'quote':_cue(i,source),
               'quote_sha256':sha256(_cue(i,source).encode('utf-8'))}
              for i in n[cid]['context_cue_indices']]
        check(newtask.get('source_context')==ctxt and
              newtask.get('condition_cue_indices')==n[cid]['condition_cue_indices'] and
              newtask.get('inherited_index_etf_scope_cue_indices')==(indices if cid in targets else []) and
              newtask.get('actual_chatgpt_text_review_disposition')==reviewmap[cid]['review_disposition'] and
              newtask.get('actual_financial_evidence_disposition')==reviewmap[cid]['financial_evidence_disposition'] and
              newtask.get('e3_final_approved') is False,
              'E3_SCOPE_OR_SOURCE_CONTEXT_LOSS')
    return {'schema':SCHEMA,'actual_original_cues':len(source.cues),
            'original_srt_sha256':hashes['source'],'new_native_sha256':hashes['new_native'],
            'native_atom_digest':nxt['atom_candidate_digest'],
            'unapproved_native_atoms':len(n),'scope_source_cues':indices,
            'scope_inherited_atoms':len(targets),
            'text_only_claim_reviewed':len(rows),
            'text_review_dispositions':dict(sorted(states.items())),
            'financial_risk_atoms_preserved':fnext['risk_tagged_atom_count'],
            'original_250_cue_reconciled':sum(tally.values()),
            'census_counts':dict(sorted(tally.items())),
            'intra_and_cross_atom_discourse_relations_preserved':new_packet.get('preserved_inter_atom_and_intra_atom_relations'),
            'unverified_media_quarantines_preserved':len(new_packet.get('globally_unassigned_original_media_quarantines',[])),
            'actual_chatgpt_text_review_recorded':True,
            'independent_gold_or_audio_video_certified':False,
            'financial_facts_approved':0,'e3_final_approved':False,
            'e4_approved':False,'e5_knowledge_published':0,
            'e2_final_pass':False,
            'status':'SOURCE_SCOPE_AND_TEXT_REVIEW_CUSTODY_PASS_INDEPENDENT_GOLD_FINANCIAL_TRUTH_HOLD'}


def audit_exact_owner_source_and_review(docs,expected_sha256,window_size=20):
    """One complete source-pinned call; malformed inputs fail with InvalidInput, never unhandled runtime errors."""
    try:return _audit(docs,expected_sha256,window_size)
    except InvalidInput:raise
    except (KeyError,IndexError,ValueError,TypeError,ArithmeticError,AttributeError,AssertionError) as exc:
        raise InvalidInput('V224_MALFORMED_REVIEW_INPUT') from exc


def require_e3_final_or_e4_e5_authorization(receipt):
    """A text-source review is a useful research artifact but never an approval token."""
    check(type(receipt) is dict and receipt.get('schema')==SCHEMA,'NOT_A_REVIEW_RECEIPT')
    raise InvalidInput('V224_NO_INDEPENDENT_GOLD_MEDIA_FINANCIAL_APPROVAL')