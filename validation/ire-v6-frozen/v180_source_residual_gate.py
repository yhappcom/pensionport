"""V180 source-only residual review gate: never equate context links with recall.

Frozen V6 flags risky NO_ATOM; this secondary add-on enumerates all flags,
separates source-context-linked vs orphan cues and demands actual in-chat
per-cue meaning dispositions. Neither model-authorship nor independent gold is
cryptographically authenticated. No native V123/E4/E5 write exists here.
"""
from __future__ import annotations
import copy
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.claim_census import FINANCIAL, QUALIFIER, MULTI_CLAIM
from v176_chat_engine_loop import EngineChatSession

SCHEMA="IRE_V180_SOURCE_RISK_RECHECK_QUEUE_V1"
RESULT="IRE_V180_SOURCE_RISK_RECHECK_UNRELEASED_V1"
CHOICES={"SOURCE_ONLY_DISCOURSE","CONTEXT_ONLY_PROPOSAL",
         "MISSED_ATOM_REVISIT_REQUIRED","UNRESOLVED_MEDIA_OR_SOURCE"}

def _need(ok,code):
    if not ok:raise InvalidInput("V180_RISK_RECHECK_"+code)

def prepare_source_risk_recheck(engine: EngineChatSession):
    _need(isinstance(engine,EngineChatSession),"NATIVE_OWNER_ENGINE_REQUIRED")
    exchange,summary=engine.compile_native_v6_stage()
    active={a['claim_id']:a for a in exchange['atoms']}
    items=[]
    for row in exchange['cue_dispositions']:
        i=row['cue_index']
        if row['disposition']!='NO_ATOM':continue
        text=engine.source.cues[i-1].text
        triggers=[name for name,regex in (
            ('FINANCIAL',FINANCIAL),('QUALIFIER',QUALIFIER),
            ('MULTI_CLAIM',MULTI_CLAIM)) if regex.search(text)]
        if not triggers:continue
        parents=sorted(cid for cid,atom in active.items() if
                       i in atom['context_cue_indices'])
        items.append({'cue_index':i,'source_cue_sha256':row['cue_text_sha256'],
                      'source_text':text,'risk_triggers':triggers,
                      'parent_context_claim_ids':parents,
                      'parent_atom_sha256':{cid:json_digest(active[cid]) for cid in parents},
                      'requires_actual_chat_semantic_review':True,
                      'grounded_parent_context_does_not_prove_recall':True})
    native=summary['native_v6_audit']
    _need(len(items)==native['suspicious_no_atom_cues'],"FROZEN_NO_ATOM_CENSUS_DRIFT")
    core={'schema':SCHEMA,'owner_source_sha256':engine.source.source_sha256,
          'native_manifest_sha256':engine.source.manifest_sha256,
          'prior_journal_head_sha256':summary['checkpoint_head_sha256'],
          'native_frozen_cue_disposition_sha256':native['cue_disposition_digest'],
          'native_frozen_atom_candidate_sha256':native['atom_candidate_digest'],
          'original_source_cue_count':len(engine.source.cues),
          'risk_cue_count':len(items),
          'context_linked_count':sum(bool(t['parent_context_claim_ids']) for t in items),
          'context_orphan_count':sum(not t['parent_context_claim_ids'] for t in items),
          'items':items,'independent_recall_gold_exists':False,
          'auto_closed_or_accepted':False,'e4_approved':False,'e5_published':False}
    return {**core,'challenge_sha256':json_digest(core)}

def assess_chat_risk_responses(engine: EngineChatSession,challenge:dict,responses:list):
    """Validate partial actual ChatGPT dispositions; missing remains *OPEN*.

    No response is generated here. `CONTEXT_ONLY_PROPOSAL` requires a pinned
    parent and source quote; `SOURCE_ONLY_DISCOURSE` is reserved for orphan
    agenda/filler, with a substantive explanation. The reviewer cannot claim
    model identity, official finance fact or E4 approval via a data field.
    """
    _need(type(challenge) is dict and challenge.get('schema')==SCHEMA and
          challenge.get('challenge_sha256')==json_digest({k:v for k,v in
                                                    challenge.items() if k!='challenge_sha256'}),
          "CHALLENGE_TAMPERED")
    fresh=prepare_source_risk_recheck(engine)
    _need(challenge==fresh,"STALE_OR_FORGED_CHALLENGE")
    _need(type(responses) is list and len(responses)<=len(challenge['items']),
          "RESPONSE_LIST")
    tasks={r['cue_index']:r for r in challenge['items']}
    seen={};out=[]
    for r in responses:
        required={'cue_index','source_cue_sha256','source_quote','decision',
                  'linked_parent_claim_ids','meaning_reason',
                  'conditions_and_exceptions_checked','independent_gold_certified',
                  'finance_truth_certified','model_identity_cryptographically_attested',
                  'e4_or_e5_authorized'}
        _need(type(r) is dict and set(r)==required,"CHAT_RESPONSE_FIELDS")
        idx=r['cue_index']
        _need(type(idx) is int and idx in tasks and idx not in seen,"UNKNOWN_OR_DUPLICATE")
        t=tasks[idx]
        _need(r['source_cue_sha256']==t['source_cue_sha256'] and
              type(r['source_quote']) is str and len(r['source_quote'].strip())>=3 and
              ' '.join(r['source_quote'].split()) in ' '.join(t['source_text'].split()) and
              r['decision'] in CHOICES and
              type(r['linked_parent_claim_ids']) is list and
              r['linked_parent_claim_ids']==sorted(set(r['linked_parent_claim_ids'])) and
              set(r['linked_parent_claim_ids'])<=set(t['parent_context_claim_ids']) and
              type(r['meaning_reason']) is str and len(r['meaning_reason'].strip())>=40 and
              r['conditions_and_exceptions_checked'] is True and
              all(r[k] is False for k in ('independent_gold_certified',
                   'finance_truth_certified','model_identity_cryptographically_attested',
                   'e4_or_e5_authorized')),
              "SOURCE_SEMANTIC_OR_AUTHORITY_REQUIRED")
        _need(r['decision']!='CONTEXT_ONLY_PROPOSAL' or
              bool(r['linked_parent_claim_ids']),"PARENT_REQUIRED")
        _need(r['decision']!='SOURCE_ONLY_DISCOURSE' or
              not t['parent_context_claim_ids'],"DISCOURSE_ONLY_FOR_ORPHAN")
        seen[idx]=r
        out.append(copy.deepcopy(r))
    core={'schema':RESULT,'owner_source_sha256':challenge['owner_source_sha256'],
          'challenge_sha256':challenge['challenge_sha256'],
          'prior_journal_head_sha256':challenge['prior_journal_head_sha256'],
          'risk_cue_count':len(tasks),'responses_reviewed':len(out),
          'unreviewed_risk_cues':len(tasks)-len(out),
          'parent_context_only_not_gold':True,
          'context_only_proposals':sum(r['decision']=='CONTEXT_ONLY_PROPOSAL' for r in out),
          'confirmed_source_only_discourse':sum(r['decision']=='SOURCE_ONLY_DISCOURSE' for r in out),
          'missed_atom_needing_revisit':sum(r['decision']=='MISSED_ATOM_REVISIT_REQUIRED' for r in out),
          'media_blocked':sum(r['decision']=='UNRESOLVED_MEDIA_OR_SOURCE' for r in out),
          'responses':out,'all_meaning_approved':False,
          'independent_recall_gold_exists':False,'v123_approved':False,
          'e4_approved':False,'e5_published':False}
    return {**core,'receipt_sha256':json_digest(core)}