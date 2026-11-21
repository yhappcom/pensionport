"""E2 semantic convergence: exact-source claim-level, multi-axis review & honest gates.

Operational use: pass frozen SRT, before/after native candidate frames,
source-first host review, 11 coarse contradictions, every atom's text-act review,
financial risk ledger, cue census and 32 discourse relations. This makes the
meaning pass measurable and repeatable without pretending an external gold set
or authentic audiovisual evidence exists. No private source text is emitted.

Unlike version-specific check-only guards, the entrypoint returns *domain-level*
release conditions, an actionable bounded unresolved queue and a safe handoff.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict

from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import make_original_plan

SCHEMA="IRE_V223_E2_MULTIACT_ONE_PASS_CONVERGENCE_RECEIPT_V1"
NAMES={"source","before_native","after_native","source_units","mismatch",
       "review","patch","before_finance","after_finance","before_census",
       "after_census","relation_graph"}
ROLE_ALLOWED={
"EVALUATIVE_JUDGMENT","TIME_BOUND_UNVERIFIED_DATA","FINANCIAL_DEFINITION",
"SCOPE_LIMITED_DEFINITION","ILLUSTRATIVE_ANALOGY","INVESTMENT_SELECTION_RULE",
"MECHANISM_DESCRIPTION","HISTORICAL_OR_EMPIRICAL_GENERALIZATION",
"EXPLICIT_COUNTEREXAMPLE_OR_LIMITATION","CONDITIONAL_INVESTMENT_SELECTION_RULE",
"CONDITIONAL_CAUSAL_EXPLANATION","TRADING_MECHANISM_DESCRIPTION",
"EXPLICIT_LIQUIDITY_EXCEPTION","CONDITIONAL_MECHANISM_DESCRIPTION",
"OVERGENERALIZED_FINANCIAL_DEFINITION","SIMPLIFIED_FINANCIAL_DEFINITION",
"FINANCIAL_CALCULATION_DEFINITION","AMBIGUOUS_FINANCIAL_DEFINITION",
"HYPOTHETICAL_FINANCIAL_EXAMPLE","FINANCIAL_CAUSAL_EXPLANATION",
"CONDITIONAL_COST_ARGUMENT","TIME_DEPENDENT_CLAIM","EMPIRICAL_BEHAVIORAL_CLAIM",
"ILLUSTRATIVE_ASR_UNCERTAIN_EXAMPLE","FICTIONAL_SCOPE_DECLARATION",
"FICTIONAL_PRODUCT_ATTRIBUTE","FICTIONAL_NUMERIC_ATTRIBUTE",
"EVALUATIVE_GENERALIZATION","HYPOTHETICAL_NUMERIC_EXAMPLE",
"HYPOTHETICAL_DERIVATION","FICTIONAL_DERIVATION",
"FINANCIAL_MECHANISM_DESCRIPTION",
}
SCOPES={"HYPOTHETICAL_OR_FICTIONAL","EDUCATIONAL_NORMATIVE",
        "EDUCATIONAL_SOURCE_ASSERTION","EDUCATIONAL_SOURCE_CONDITIONAL",
        "EDUCATIONAL_SOURCE_EVALUATION","HISTORICALLY_TIME_BOUND"}
TEXT_STANCES={"HYPOTHETICAL_TEXT_ONLY","RECOMMENDED_TEXT_ONLY",
              "NEGATED_TEXT_ONLY","CONDITIONAL_TEXT_ONLY",
              "EVALUATED_TEXT_ONLY","ASSERTED_TEXT_ONLY"}
SOURCE_STATUSES={"SOURCE_CONTENT_NOT_FINANCIAL_TRUTH_AND_ASR_OR_SCOPE_HOLD",
                 "SOURCE_CONTENT_NOT_FINANCIAL_TRUTH_WITH_REVIEW_RISK",
                 "SOURCE_CONTENT_REVIEWED_NOT_INDEPENDENT_GOLD"}


def need(predicate,code):
    if not predicate:
        raise InvalidInput("V223_E2_"+code)


def load_pinned_documents(raw_inputs, expected_hashes):
    """All 12 documents must be byte pinned, exactly typed and within bounded size.

    Having both an expected digest and a self-declared approved flag is never a
    substitute for independent semantic provenance; we keep the flags false.
    """
    need(type(raw_inputs) is dict and type(expected_hashes) is dict and
         set(raw_inputs)==set(expected_hashes)==NAMES,"INPUT_CONTRACT")
    docs={}
    for k in sorted(NAMES):
        raw=raw_inputs[k];digest=expected_hashes[k]
        need(type(raw) is bytes and len(raw)<=2_000_000 and
             type(digest) is str and re.fullmatch("[0-9a-f]{64}",digest) is not None and
             sha256(raw)==digest,"BYTE_PIN_"+k.upper())
        if k=="source":docs[k]=raw;continue
        try:
            obj=json.loads(raw.decode("utf-8"))
        except (ValueError,UnicodeError,TypeError) as exc:
            raise InvalidInput("V223_E2_INVALID_JSON_"+k.upper()) from exc
        need(type(obj) is dict,"JSON_OBJECT_"+k.upper())
        docs[k]=obj
    return docs


def inspect_native_kind_changes(before,after,patch,source):
    need(type(before.get("atoms")) is list and type(after.get("atoms")) is list and
         len(before["atoms"])==len(after["atoms"]),"NATIVE_COUNT_CHANGED")
    p={a['claim_id']:a for a in before['atoms']};n={a['claim_id']:a for a in after['atoms']}
    need(len(p)==len(n)==len(before['atoms']) and set(p)==set(n) and
         before['cue_dispositions']==after['cue_dispositions'] and
         {k:v for k,v in before.items() if k!='atoms'}==
         {k:v for k,v in after.items() if k!='atoms'},"NATIVE_SOURCE_OR_ID_CHANGED")
    changes={}
    for cid in sorted(p):
        x=dict(p[cid]);y=dict(n[cid]);k0=x.pop('kind');k1=y.pop('kind')
        need(x==y,"NATIVE_CLAIM_UNREVIEWED_MUTATION")
        if k0!=k1:
            changes[cid]=(k0,k1)
    need(type(patch.get('changes')) is list and
         patch.get('changed_count')==len(patch['changes'])==len(changes) and
         patch.get('original_atom_count')==len(p) and
         patch.get('corrected_atom_count')==len(n) and
         patch.get('preserved_claims_and_context') is True and
         patch.get('financial_truth_approved') is False and
         patch.get('independent_gold_verified') is False and
         patch.get('e2_final_pass') is False,
         "KIND_CHANGE_EVENT_INCOMPLETE")
    seen=set()
    for change in patch['changes']:
        need(type(change) is dict and type(change.get('claim_id')) is str and
             change['claim_id'] in changes and change['claim_id'] not in seen,
             "KIND_CHANGE_UNDOCUMENTED")
        cid=change['claim_id'];seen.add(cid)
        i=change.get('cue_index')
        need(change.get('before_kind')==changes[cid][0] and
             change.get('after_kind')==changes[cid][1] and
             type(change.get('reason')) is str and len(change['reason'])>30 and
             type(i) is int and 1<=i<=len(source.cues) and
             i in [r['cue_index'] for r in n[cid]['source_refs']] and
             change.get('cue_quote')==source.cues[i-1].text and
             change.get('cue_quote_sha256')==sha256(source.cues[i-1].text.encode()) and
             change.get('original_sound_evidence_verified') is False and
             change.get('financial_truth_approved') is False,
             "KIND_CHANGE_SOURCE_NOT_GROUNDED")
    need(seen==set(changes),"KIND_CHANGE_MISSING")
    return changes


def inspect_source_units(docket,source):
    need(docket.get('source_sha256')==source.source_sha256 and
         docket.get('not_a_blind_gold_dataset') is True and
         docket.get('author_was_exposed_to_prior_engine_project_context') is True and
         docket.get('e2_final_pass') is False and
         type(docket.get('claims')) is list and 1<=len(docket['claims'])<=1000,
         "SOURCE_UNIT_GOLD_OR_SCHEMA")
    unit_lookup={};cue_cover=set()
    for u in docket['claims']:
        need(type(u) is dict and type(u.get('source_only_id')) is str and
             u['source_only_id'] not in unit_lookup and
             type(u.get('cue_start')) is int and type(u.get('cue_end')) is int and
             1<=u['cue_start']<=u['cue_end']<=len(source.cues) and
             type(u.get('source_refs')) is list and
             len(u['source_refs'])==u['cue_end']-u['cue_start']+1,
             "SOURCE_UNIT_RANGE")
        for i,ref in enumerate(u['source_refs'],u['cue_start']):
            need(ref.get('cue_index')==i and
                 ref.get('quote')==source.cues[i-1].text and
                 ref.get('source_text_sha256')==sha256(source.cues[i-1].text.encode()),
                 "SOURCE_UNIT_QUOTE_OR_HASH")
            cue_cover.add(i)
        unit_lookup[u['source_only_id']]=u
    need(cue_cover==set(range(1,len(source.cues)+1)),"SOURCE_UNIT_COVERAGE")
    return unit_lookup


def inspect_source_multiact_review(review,mismatch,source,source_units,after,
                                   before_finance,after_finance,changes):
    atoms={a['claim_id']:a for a in after['atoms']}
    mismatch_rows=mismatch.get('rows')
    need(type(mismatch_rows) is list and len(mismatch_rows)<=len(atoms) and
         mismatch.get('coarse_kind_mismatch_count')==len(mismatch_rows) and
         mismatch.get('confirmed_new_kind_errors')==0 and
         mismatch.get('not_a_blind_gold') is True,
         "MISMATCH_DOCKET_UNTRUSTED")
    md={r['claim_id']:r for r in mismatch_rows}
    need(len(md)==len(mismatch_rows) and set(md)<=set(atoms),"MISMATCH_CLAIMS")
    need(type(review.get('rows')) is list and
         len(review['rows'])==len(atoms) and
         review.get('schema')=='IRE_V223_E2_SOURCE_CLAIM_DUAL_AXIS_HOST_REVIEW_V1' and
         review.get('source_sha256')==source.source_sha256 and
         review.get('source_claims_reviewed')==len(atoms) and
         review.get('discourse_kind_disagreements_reexamined')==len(md) and
         review.get('remaining_coarse_conflicts')==0 and
         review.get('source_roles_resolved_from_coarse_span')==len(md)-len(changes) and
         review.get('native_kind_corrections')==len(changes) and
         review.get('source_review_has_seen_prior_engine') is True and
         review.get('independent_gold_supplied') is False and
         review.get('speaker_audio_available') is False and
         review.get('original_video_screen_available') is False and
         review.get('financial_truth_approved')==0 and
         review.get('e2_final_pass') is False and
         review.get('e3_e4_e5_authorized') is False and
         review.get('knowledge_published')==0,
         "REVIEW_FALSE_GOLD_OR_INCOMPLETE")
    need(type(after_finance.get('atoms')) is list and type(before_finance.get('atoms')) is list,
         "FINANCE_ROWS_INVALID")
    pfin={r['claim_id']:r for r in before_finance['atoms']};fin={r['claim_id']:r for r in after_finance['atoms']}
    need(len(pfin)==len(fin)==len(atoms) and set(pfin)==set(fin)==set(atoms),
         "FINANCE_ATOM_LOSS")
    seen=set();counts=Counter()
    for r in review['rows']:
        cid=r.get('claim_id');need(type(cid) is str and cid in atoms and cid not in seen,
                                 "REVIEW_MISSING_OR_DUPLICATE_ATOM");seen.add(cid)
        atom=atoms[cid]
        cue_ids=[x['cue_index'] for x in atom['source_refs']]
        source_unit_ids=sorted({uid for uid,u in source_units.items()
                                if any(u['cue_start']<=i<=u['cue_end'] for i in cue_ids)})
        need(r.get('reviewed_legacy_kind')==atom['kind'] and
             r.get('source_primary_cues')==cue_ids and
             r.get('source_primary_exact_quote')==[source.cues[i-1].text for i in cue_ids] and
             r.get('source_primary_quote_sha256')==[
                 sha256(source.cues[i-1].text.encode()) for i in cue_ids] and
             r.get('source_unit_ids_for_primary')==source_unit_ids and
             r.get('textual_discourse_role') in ROLE_ALLOWED and
             r.get('epistemic_scope') in SCOPES and
             r.get('textual_stance_candidate') in TEXT_STANCES and
             r.get('source_support_status') in SOURCE_STATUSES and
             type(r.get('review_explanation')) is str and len(r['review_explanation'])>=15 and
             r.get('source_risk_tags')==fin[cid]['risk_tags'] and
             r.get('original_native_stance')==atom['stance']=='UNRESOLVED' and
             r.get('original_native_speaker')==atom['speaker']=='UNKNOWN' and
             r.get('speaker_audio_verified') is False and
             r.get('financial_truth_verified') is False and
             r.get('independent_gold_verified') is False and
             r.get('atom_e2_approved') is False,
             "CLAIM_SOURCE_ROLE_OR_FALSE_CERTIFICATION")
        # The base native kind is *not* the full speech act. Fictional numeric
        # facts must never be reinterpreted as actual market observations.
        if fin[cid]['risk_tags']:
            need(r['source_support_status']!='SOURCE_CONTENT_REVIEWED_NOT_INDEPENDENT_GOLD',
                 'RISK_REVIEW_NOT_QUARANTINED')
        if atom['kind']=='HYPOTHETICAL':
            need(r['epistemic_scope']=='HYPOTHETICAL_OR_FICTIONAL' and
                 r['textual_stance_candidate']=='HYPOTHETICAL_TEXT_ONLY',
                 "HYPOTHETICAL_SCOPE_LOST")
        if atom['kind']=='RECOMMENDATION':
            need(r['epistemic_scope']=='EDUCATIONAL_NORMATIVE' and
                 r['textual_stance_candidate']=='RECOMMENDED_TEXT_ONLY',
                 "RECOMMENDATION_ACT_LOST")
        if cid in md:
            resolution=r.get('source_kind_mismatch_resolution')
            need(resolution in {'COMPOUND_SPAN_ROLE_DIFFERENCE','LEGACY_KIND_CORRECTED'} and
                 (resolution=='LEGACY_KIND_CORRECTED')==(cid in changes) and
                 md[cid]['native_kind']==r['original_legacy_kind'] and
                 md[cid]['source_primary'][0]['cue_index']==cue_ids[0] and
                 type(md[cid]['source_unit_ids']) is list and
                 len(md[cid]['source_unit_ids'])>=1 and
                 any(x in r['source_unit_ids_for_primary'] for x in md[cid]['source_unit_ids']) and
                 all(u in source_units and any(source_units[u]['cue_start']<=i<=
                     source_units[u]['cue_end'] for i in atom['context_cue_indices'])
                     for u in md[cid]['source_unit_ids']),
                 "MISMATCH_NOT_ADJUDICATED")
            counts[resolution]+=1
        else:
            need(r.get('source_kind_mismatch_resolution')=='NO_PREVIOUS_COARSE_KIND_DIFFERENCE' and
                 r.get('original_legacy_kind')==r.get('reviewed_legacy_kind'),
                 "UNREVIEWED_KIND_CHANGE")
        if r['epistemic_scope']=='HYPOTHETICAL_OR_FICTIONAL':
            counts['hypothetical_or_fictional']+=1
        counts['reviewed_atoms']+=1
    need(seen==set(atoms) and counts['LEGACY_KIND_CORRECTED']==len(changes) and
         counts['COMPOUND_SPAN_ROLE_DIFFERENCE']==len(md)-len(changes),
         "MULTIACT_CENSUS_INCOMPLETE")
    return dict(counts)


def inspect_finance_and_census(before_finance,after_finance,
                               before_census,after_census,after,source,changes):
    n={a['claim_id']:a for a in after['atoms']}
    b={r['claim_id']:r for r in before_finance['atoms']};a={r['claim_id']:r for r in after_finance['atoms']}
    need(set(a)==set(b)==set(n) and
         len(a)==len(after_finance['atoms']) and
         after_finance['all_atoms_reviewed_source_claims']==len(n) and
         after_finance.get('external_independent_gold') is False and
         after_finance.get('e2_final_pass') is False and
         after_finance.get('knowledge_publication_authorized') is False,
         "FINANCE_CENSUS_OR_FALSE_GOLD")
    added=[]
    for cid in n:
        x,y=b[cid],a[cid]
        same_except_kind_and_tags={k:v for k,v in y.items() if k not in ('kind','risk_tags','risk_review_status')}
        old_except_kind_and_tags={k:v for k,v in x.items() if k not in ('kind','risk_tags','risk_review_status')}
        need(same_except_kind_and_tags==old_except_kind_and_tags and
             y['kind']==n[cid]['kind'] and x['kind']==(changes[cid][0] if cid in changes else n[cid]['kind']) and
             set(y['risk_tags'])>=set(x['risk_tags']) and
             len(set(y['risk_tags']))==len(y['risk_tags']) and
             y['risk_review_status']==('HOLD_REQUIRES_OFFICIAL_OR_MEDIA_REVIEW' if y['risk_tags'] else
                                       'SOURCE_ANCHORED_BUT_NOT_INDEPENDENT_GOLD') and
             y['speaker_verified'] is False and y['stance_confirmed'] is False and
             y['financial_truth_certified'] is False and y['claim_approved'] is False,
             "FINANCE_RISK_LOST_OR_SOURCE_MUTATED")
        if set(y['risk_tags'])>set(x['risk_tags']):
            need(cid in changes and changes[cid][1]=='FACT',"FINANCE_NEW_RISK_WITHOUT_FACT_CHANGED")
            added.append(cid)
    need(after_finance['risk_tagged_atom_count']==sum(bool(r['risk_tags']) for r in a.values()) and
         after_finance['risk_tag_types']==sorted({t for r in a.values() for t in r['risk_tags']}),
         "FINANCE_RISK_SUMMARY_FALSE")
    old=before_census['rows'];new=after_census['rows']
    need(len(old)==len(new)==len(source.cues) and old==new and
         after_census['classification_counts']==before_census['classification_counts'] and
         after_census['audio_screen_flagged_cue_count']==before_census['audio_screen_flagged_cue_count'] and
         after_census['distinct_primary_claim_ids']==len(n) and
         after_census['independent_gold_available'] is False and
         after_census['e2_final_pass'] is False,
         "CUE_CLASS_DRIFT")
    for idx,c in enumerate(new,1):
        need(c['cue_index']==idx and c['source_quote']==source.cues[idx-1].text and
             c['cue_text_sha256']==sha256(source.cues[idx-1].text.encode()) and
             c['financial_fact_approved'] is False and
             c['independent_omission_review_complete'] is False,
             "CUE_ORIGINAL_SOURCE_OR_FALSE_GOLD")
    return added


def inspect_prior_relations(graph,source,after):
    rows=graph.get('rows');atoms={a['claim_id'] for a in after['atoms']}
    need(graph.get('schema')=='IRE_V218_E2_PRIVATE_CROSS_ATOM_REVIEW_BRIDGE_V1' and
         graph.get('source_sha256')==source.source_sha256 and
         type(rows) is list, "GRAPH_SCHEMA")
    need(type(rows) is list and graph.get('total_original_relations')==len(rows) and
         graph.get('source_sha256')==source.source_sha256 and
         graph.get('independent_gold_available') is False and
         graph.get('financial_fact_approved') in (None,False) and
         graph.get('e2_final_pass') is False,
         "GRAPH_SOURCE_OR_GOLD")
    seen=set();states=Counter()
    for r in rows:
        rid=r.get('relation_id');need(type(rid) is str and rid not in seen,"GRAPH_DUPLICATE")
        seen.add(rid)
        for field in ('source_cue','target_cue'):
            idx=r.get(field);need(type(idx) is int and 1<=idx<=len(source.cues),"GRAPH_CUE_INVALID")
        for k in ('source_atom_id','target_atom_id'):
            need(r.get(k) is None or r[k] in atoms,"GRAPH_DANGLING_CLAIM")
        for k in ('is_external_gold','speaker_audio_verified','video_frame_verified',
                  'financial_fact_approved','final_semantic_approval','knowledge_publication_authorized'):
            need(r.get(k) is False,"GRAPH_FALSE_APPROVAL")
        need(r.get('review_state') in {'INTRA_ATOM_UNAPPROVED','LINKED_UNAPPROVED',
                                      'QUARANTINE_VISUAL_UNVERIFIED'},
             'GRAPH_UNREVIEWED_STATE')
        states[r['review_state']]+=1
    need(states['LINKED_UNAPPROVED']==graph.get('cross_atom_edges_reviewed') and
         states['INTRA_ATOM_UNAPPROVED']==graph.get('intra_atom_context_reviewed') and
         states['QUARANTINE_VISUAL_UNVERIFIED']==graph.get('visual_quarantines_reviewed'),
         'GRAPH_RELATION_CENSUS_DRIFT')
    return dict(states)


def run_e2_convergence(raw_inputs,expected_hashes,*,window_size=20):
    """One-call, private original replay and typed semantic audit. No LLM call.

    A model/ChatGPT host must produce the claim-by-claim review packet. Pure
    software can verify source bytes, monotone risk custody and review coverage
    but cannot certify whether the host actually understood Korean nuance.
    """
    d=load_pinned_documents(raw_inputs,expected_hashes)
    need(type(window_size) is int and 1<=window_size<=100,"WINDOW_SIZE")
    source,_=make_original_plan(d['source'],d['after_native']['video_id'],
          expected_source_sha256=expected_hashes['source'],window_size=window_size)
    before=audit_host_atomic_exchange(source,d['before_native'])
    after=audit_host_atomic_exchange(source,d['after_native'])
    # Verify all cross-file hashes, never trust a hash written inside its own JSON.
    named={"previous_native_sha256":"before_native","reviewed_native_sha256":"after_native",
           "source_first_review_sha256":"source_units","previous_coarse_mismatch_sha256":"mismatch",
           "financial_risk_sha256":"after_finance","source_cue_census_sha256":"after_census"}
    for attr,key in named.items():
        need(d['review'].get(attr)==expected_hashes[key],"REVIEW_ATTACHMENT_SHA_"+attr)
    need(d['patch'].get('before_native_sha256')==expected_hashes['before_native'] and
         d['patch'].get('after_native_sha256')==expected_hashes['after_native'] and
         d['patch'].get('previous_kind_mismatch_sha256')==expected_hashes['mismatch'] and
         d['patch'].get('review_sha256')==expected_hashes['review'] and
         d['patch'].get('source_sha256')==source.source_sha256,
         "PATCH_ATTACHMENT_SHA")
    for name in ('before_finance','after_finance'):
        pin='before_native' if name=='before_finance' else 'after_native'
        need(d[name].get('native_exchange_sha256')==expected_hashes[pin] and
             d[name].get('source_sha256')==source.source_sha256,
             "FINANCE_NATIVE_OR_SOURCE_DRIFT")
    for name in ('before_census','after_census'):
        pin='before_native' if name=='before_census' else 'after_native'
        need(d[name].get('native_exchange_sha256')==expected_hashes[pin] and
             d[name].get('original_source_sha256')==source.source_sha256,
             "CENSUS_NATIVE_OR_SOURCE_DRIFT")
    change=inspect_native_kind_changes(d['before_native'],d['after_native'],d['patch'],source)
    units=inspect_source_units(d['source_units'],source)
    roles=inspect_source_multiact_review(d['review'],d['mismatch'],source,units,d['after_native'],
                                         d['before_finance'],d['after_finance'],change)
    added=inspect_finance_and_census(d['before_finance'],d['after_finance'],d['before_census'],
                                     d['after_census'],d['after_native'],source,change)
    relations=inspect_prior_relations(d['relation_graph'],source,d['after_native'])
    counts=Counter(x['classification'] for x in d['after_census']['rows'])
    risks=d['after_finance']['risk_tagged_atom_count']
    return {
     'schema':SCHEMA,'source_sha256':source.source_sha256,
     'original_cues':len(source.cues),'native_atoms_after':len(d['after_native']['atoms']),
     'native_atoms_before':len(d['before_native']['atoms']),
     'source_claim_level_roles_reviewed':roles['reviewed_atoms'],
     'previous_coarse_unit_kind_disagreements':len(d['mismatch']['rows']),
     'coarse_multi_act_roles_distinguished':roles.get('COMPOUND_SPAN_ROLE_DIFFERENCE',0),
     'real_native_kind_corrections':roles['LEGACY_KIND_CORRECTED'],
     'coarse_role_conflicts_remaining_in_review_docket':0,
     'hypothetical_or_fictional_atoms_not_recast_as_market_facts':roles.get('hypothetical_or_fictional',0),
     'actual_financial_risk_tagged_atoms':risks,
     'newly_flagged_financial_risk_claim_ids':sorted(added),
     'source_cue_classes':dict(counts),
     'original_av_or_media_risk_cues':d['after_census']['audio_screen_flagged_cue_count'],
     'original_32_relation_review_states':relations,
     'frozen_original_v6_atom_digest':after['atom_candidate_digest'],
     'original_unchanged_text_quote_integrity':True,
     'speaker_original_audio_verified':False,
     'financial_facts_verified':False,
     'independent_blind_gold_certified':False,
     'precision_recall_real_video_measured':False,
     'historic_owner_sqlite_recovered':False,
     'e2_text_level_internal_multiact_review_completed':True,
     'e2_final_semantic_accuracy_pass':False,
     'e3_e4_e5_authorized':False,'knowledge_published':0,
     'result':'SOURCE_CLAIM_MULTIACT_CONVERGED_ORIGINAL_VIDEO_REPLAY_PASS_INDEPENDENT_GOLD_AV_FINANCE_HOLD'
    }


def require_certified_e2_for_approval(receipt):
    need(type(receipt) is dict and receipt.get('schema')==SCHEMA,'NOT_PROOF_RECEIPT')
    # This packet is *by construction* a source-first internal ChatGPT review.
    # Later independent-gold and regulatory certifiers must issue separate,
    # validated proof objects, never flip one boolean in this receipt.
    raise InvalidInput('V223_E2_INDEPENDENT_GOLD_AND_E3_E4_NOT_VERIFIED')


def prepare_chatgpt_e3_semantic_review_packet(raw_inputs,expected_hashes,
                                               convergence_receipt,*,window_size=20):
    """E3 *review intake* despite E2 HOLD, not E3 approval or E5 publication.

    This breaks the former deadlock where source semantics were required before
    ChatGPT could even receive the exact context needed to resolve them.
    Owner-private original quotes and claim text MUST NOT enter public CI/logs.
    """
    expected=run_e2_convergence(raw_inputs,expected_hashes,window_size=window_size)
    need(type(convergence_receipt) is dict and convergence_receipt==expected,
         'CHAT_REVIEW_PREVIEW_REQUIRES_ORIGINAL_REPLAY')
    docs=load_pinned_documents(raw_inputs,expected_hashes)
    source,_=make_original_plan(docs['source'],docs['after_native']['video_id'],
        expected_source_sha256=expected_hashes['source'],window_size=window_size)
    reviews={x['claim_id']:x for x in docs['review']['rows']}
    risk={x['claim_id']:x for x in docs['after_finance']['atoms']}
    relations=docs['relation_graph']['rows']
    all_media_quarantines=[]
    for e in relations:
        if e['review_state']=='QUARANTINE_VISUAL_UNVERIFIED':
            all_media_quarantines.append({
               'relation_id':e['relation_id'],
               'source_cue':e['source_cue'],
               'source_quote':source.cues[e['source_cue']-1].text,
               'target_cue':e['target_cue'],
               'target_quote':source.cues[e['target_cue']-1].text,
               'evidence_required':'ORIGINAL_VIDEO_OR_AUDIO',
               'financial_facts_approved':False,
            })
    tasks=[]
    for atom in docs['after_native']['atoms']:
        cid=atom['claim_id'];r=reviews[cid]
        # All source text is taken only from the pinned owner's SRT.
        indices=atom['context_cue_indices']
        context=[{'cue_index':i,'quote':source.cues[i-1].text,
                  'quote_sha256':sha256(source.cues[i-1].text.encode())} for i in indices]
        attached=[{'relation_id':e['relation_id'],'type':e['relation_type'],
                   'source_atom_id':e['source_atom_id'],
                   'target_atom_id':e['target_atom_id'],
                   'source_cue':e['source_cue'],
                   'source_quote':source.cues[e['source_cue']-1].text,
                   'target_cue':e['target_cue'],
                   'target_quote':source.cues[e['target_cue']-1].text,
                   'relation_is_unapproved':True}
                  for e in relations if cid in (e['source_atom_id'],e['target_atom_id'])]
        tasks.append({
            'claim_id':cid,'proposition':atom['proposition'],
            'old_native_kind':r['original_legacy_kind'],
            'corrected_kind':atom['kind'],
            'text_discourse_role':r['textual_discourse_role'],
            'textual_stance_provisional':r['textual_stance_candidate'],
            'source_context':context,
            'inter_atom_discourse_dependencies':attached,
            'primary_cue_ids':[q['cue_index'] for q in atom['source_refs']],
            'condition_cue_indices':atom['condition_cue_indices'],
            'exception_cue_indices':atom['exception_cue_indices'],
            'source_text_is_not_audio_verified':True,
            'risk_tags':risk[cid]['risk_tags'],
            'source_review_only_not_independent_gold':True,
            'question_for_chatgpt':'원문 지지/반박·화자/입장·가상/시점·숫자단위·조건예외·현재 공식 금융근거 판정',
            'disposition_required':'TEXT_SUPPORT_ONLY_OR_HOLD_OR_QUARANTINE',
            'financial_fact_approved':False,
        })
    need(len(tasks)==expected['native_atoms_after'], 'E3_REVIEW_PACKET_CLAIM_LOSS')
    return {
      'schema':'IRE_V223_CHATGPT_OWNER_PRIVATE_E3_PRE_REVIEW_INTAKE_V1',
      'source_sha256':expected_hashes['source'],
      'native_sha256':expected_hashes['after_native'],
      'semantic_convergence_atom_digest':expected['frozen_original_v6_atom_digest'],
      'original_cues':len(source.cues),
      'source_claim_tasks':len(tasks),
      'text_level_internal_review_complete':True,
      'chatgpt_e3_semantic_review_can_start_while_e2_gold_hold':True,
      'external_independent_gold_provided':False,
      'source_audio_video_verified':False,
      'tasks_are_not_approved':True,
      'preserved_inter_atom_and_intra_atom_relations':len(relations)-len(all_media_quarantines),
      'globally_unassigned_original_media_quarantines':all_media_quarantines,
      'e3_final_approved':False,'e4_approved':False,'e5_published':False,
      'task_rows':tasks,
    }