"""V122 adapter: V121 host-reviewed split -> real IRE V6 atomic exchange input.

Only checks source/representation. Meaning still supplied by ChatGPT; there is
no model API, financial fact approval, independent gold, or release permission.
This module is safe to import by core V6 hosts without mutating frozen kernels.
"""
from __future__ import annotations
import hashlib
import json
import re

from v121_source_atomic_repair_guard import apply_host_reviewed_atomic_patch, sha

class UnsafeV122(ValueError):
    pass

def need(ok, code):
    if not ok:
        raise UnsafeV122('V122_'+code)

def digest(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()

def _idx(xs, maximum, label):
    need(type(xs) is list and xs==sorted(set(xs)) and
         all(type(x) is int and 1<=x<=maximum for x in xs),label)


def build_v6_host_exchange(*, raw_srt, verified_source, proposals, operations,
                           host_frames, context_extensions=None):
    """Prepare an exchange consumable by existing V6 submit_host_atomic_batch.

    Host frames are *reviewer-supplied*, never inferred; no front-end approval.
    Source-literal context extensions are recorded as provenance, not claims.
    The returned exchange is *source-bound* and is audited by the actual V6
    audit_host_atomic_exchange before it can be passed to the existing host batch.
    """
    from ire.v6.atomic_exchange import NUMBER, audit_host_atomic_exchange
    from ire.v6.codec import sha256
    from ire.v6.source import parse_srt

    need(type(raw_srt) is bytes and sha(raw_srt)==verified_source.source_sha256,'PINNED_SOURCE')
    cues=parse_srt(raw_srt)
    need(len(cues)==len(verified_source.cues),'SOURCE_CENSUS')
    need(verified_source.scope_first_cue==1 and
         verified_source.scope_last_cue==len(cues),'FULL_VIDEO_SCOPE_REQUIRED')
    need(type(proposals) is list and type(operations) is list,'PROPOSALS_REQUIRED')
    need(type(host_frames) is dict and bool(host_frames),'HOST_FRAMES_REQUIRED')
    extensions=context_extensions if context_extensions is not None else {}
    need(type(extensions) is dict,'EXTENSIONS_SCHEMA')
    base=[]
    for p in proposals:
        need(type(p) is dict and set(p)=={'id','cue_indices','source_sha256','speaker_assertion'},'BASE_PROPOSAL_FIELDS')
        base.append(p)
    patched=apply_host_reviewed_atomic_patch(raw_srt,base,operations)
    candidates=patched['candidates']
    ids={x['id'] for x in candidates}
    need(set(host_frames)==ids,'FRAME_CENSUS_MUST_MATCH_PRECOMMIT')
    need(set(extensions).issubset(ids),'UNKNOWN_EXTENSION_ID')
    source_by_id={x['id']:x for x in candidates}
    atoms=[]
    used={i:[] for i in range(1,len(cues)+1)}
    extended=[]
    for num, candidate in enumerate(candidates,1):
        key=candidate['id']
        frame=host_frames[key]
        need(type(frame) is dict and set(frame)=={
            'kind','stance','speaker','context_cue_indices',
            'condition_cue_indices','exception_cue_indices','as_of'},'FRAME_FIELDS')
        required=candidate['cue_indices']
        ex=extensions.get(key,[])
        _idx(ex,len(cues),'EXTENDED_INDICES')
        need(all(x not in required and
                 (min(required)-1<=x<=max(required)+1) for x in ex),
             'EXTENSION_MUST_BE_ADJACENT_CONTEXT')
        indices=sorted(set(required)|set(ex))
        _idx(indices,len(cues),'ATOM_INDICES')
        ctx=frame['context_cue_indices']
        cond=frame['condition_cue_indices']
        except_=frame['exception_cue_indices']
        for items,label in [(ctx,'FRAME_CONTEXT'),(cond,'FRAME_COND'),(except_,'FRAME_EXCEPTION')]:
            _idx(items,len(cues),label)
        need(set(indices).issubset(ctx) and set(cond+except_).issubset(ctx),'FRAME_CONTEXT_GAP')
        need(all(min(indices)-2<=i<=max(indices)+2 for i in ctx),'CONTEXT_UNBOUNDED')
        need(frame['as_of'] is None or bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}',frame['as_of'])),'AS_OF')
        # Preserve reviewer's qualification outside V6's *speaker* proposition.
        # V6 atom quote must literally occur in owner SRT; no search inference.
        refs=[{'cue_index':i,'quote':cues[i-1].text} for i in indices]
        claim_id=f'C{num:05}'
        for i in indices:used[i].append(claim_id)
        numbers=[]
        for t in NUMBER.findall(candidate['speaker_assertion']):
            match=next(({'cue_index':i,'token':t} for i in ctx if
                        t in NUMBER.findall(cues[i-1].text)),None)
            need(match is not None,'NUMBER_NOT_IN_OWNER_CUES')
            if match not in numbers:numbers.append(match)
        atoms.append({
            'claim_id':claim_id,'owner_window_id':verified_source.owner(indices[0]),
            'proposition':candidate['speaker_assertion'],
            'kind':frame['kind'],'stance':frame['stance'],'speaker':frame['speaker'],
            'source_refs':refs,'context_cue_indices':ctx,
            'condition_cue_indices':cond,'exception_cue_indices':except_,
            'numeric_references':numbers,'as_of':frame['as_of']})
        if ex:
            extended.append({'candidate_id':key,'extra_cue_indices':ex,
                             'reason':'CONTEXT_SUPPORT_ONLY_NOT_NEW_CLAIM'})
    note='Source context / no separate atomic assertion; ChatGPT review required'
    records=[]
    for c in cues:
        present=sorted(used[c.index])
        records.append({'cue_index':c.index,
                        'cue_text_sha256':sha256(c.text.encode('utf-8')),
                        'disposition':'CANDIDATES' if present else 'NO_ATOM',
                        'claim_ids':present,
                        'numeric_tokens':NUMBER.findall(c.text),
                        'note':'Source-anchored host claim candidates' if present else note})
    exchange={'schema':'IRE_V6_HOST_ATOMIC_EXCHANGE_V1',
              'video_id':verified_source.video_id,
              'source_sha256':verified_source.source_sha256,
              'manifest_sha256':verified_source.manifest_sha256,
              'cue_dispositions':records,'atoms':atoms}
    audit=audit_host_atomic_exchange(verified_source,exchange)
    return {'schema':'V122_REFINED_EXCHANGE_BRIDGE_RECEIPT_V1',
            'exchange':exchange,
            'audit':audit,
            'host_proposals':len(base),'source_bound_refined_candidates':len(candidates),
            'extension_docket':extended,
            'input_patch_digest_sha256':digest({'proposals':base,'operations':operations}),
            'refinement_source_sha256':patched['source_sha256'],
            'finance_fact_approved':False,'independent_gold':False,'p0_go':False,
            'automatically_invoked_chatgpt':False}


def submit_v122_refined_host_batch(store, *, raw_srt, manifest, inventory_bytes,
                                   expected_inventory_sha256, proposals, operations,
                                   host_frames, knowledge, window_models, window_reviews,
                                   scope_id, run_id, expected_head, context_extensions=None):
    """Real V6 host_batch entrypoint. Fail closed on any bridge/core audit issue.

    Caller must first create/attest pinned owner inventory and provide the
    complete window proof/review maps. This function does not bypass those gates.
    """
    from ire.v6.trust import verify_owner_inventory
    from ire.v6.host_batch import submit_host_atomic_batch
    pinned=verify_owner_inventory(raw_srt,manifest,inventory_bytes,
                                  expected_inventory_sha256=expected_inventory_sha256)
    bridge=build_v6_host_exchange(raw_srt=raw_srt,
        verified_source=pinned.source,proposals=proposals,operations=operations,
        host_frames=host_frames,context_extensions=context_extensions)
    from ire.v6.errors import QualityNotProven
    if (bridge['audit']['unresolved_cues'] or bridge['audit']['suspicious_no_atom_cues']):
        raise QualityNotProven('V122_INCOMPLETE_REFINED_SOURCE_REVIEW')
    return submit_host_atomic_batch(store,scope_id=scope_id,run_id=run_id,
        expected_head=expected_head,raw=raw_srt,manifest=manifest,
        inventory_bytes=inventory_bytes,expected_inventory_sha256=expected_inventory_sha256,
        exchange=bridge['exchange'],knowledge=knowledge,
        window_models=window_models,window_reviews=window_reviews)
