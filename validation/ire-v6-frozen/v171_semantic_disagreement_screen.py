"""Whole-video source-first *suspicion* docket for mixed speech-act atom frames.

A lexical signal is not a semantic adjudication. It prioritizes current-chat
review of source-pinned FACT atoms that may contain speculation, recollection
or speaker opinion. No automatic change to status/kind/source, V123 or E4.
"""
from __future__ import annotations
import re
from v166_e4_full_video_readiness import audit_video_readiness,digest

SCHEMA='IRE_V171_SEMANTIC_TYPE_DISAGREEMENT_TRIAGE_V1'
HIGH=re.compile(r'의견|체감|주관적|기억상|추정|인상|느낌|개인적')
MEDIUM=re.compile(r'느껴|기억|생각|보이|같아요|것 같|듯해|한계가 있|가능성')


def screen_full_video(raw,cues,segments,*,expected_source_sha256):
    """Real source bytes and 13 complete original scopes are mandatory.

    Returns identifiers and source pins ONLY, no unpublished subtitle text.
    The flag is a prioritization signal, never a TP/FP accuracy estimate.
    """
    census=audit_video_readiness(raw,cues,segments,
                                 expected_source_sha256=expected_source_sha256)
    candidates=[]
    total_facts=0
    for segment in segments:
        review={v['claim_id']:v for v in segment['review']['atom_verdicts']}
        for atom in segment['exchange']['atoms']:
            if atom.get('kind')!='FACT':continue
            total_facts+=1
            ctx=' '.join(cues[idx] for idx in atom['context_cue_indices'])
            proposition=atom.get('proposition','')
            high=HIGH.search(proposition)
            medium=MEDIUM.search(ctx)
            if not (high or medium):continue
            verdict=review[atom['claim_id']]
            candidates.append({
                'segment_id':segment['segment_id'],
                'claim_id':atom['claim_id'],
                'atom_sha256':digest(atom),
                'prior_review_sha256':digest(segment['review']),
                'prior_status':verdict['status'],
                'original_source_context_cue_indices':atom['context_cue_indices'],
                'risk_tier':'HIGH_META_CONFLICT' if high else 'MEDIUM_SPEECH_CONTEXT',
                'source_only_lexical_signal_not_a_semantic_verdict':True,
                'chat_reviewer_must_adjudicate_before_atom_kind_change':True,
            })
    candidates.sort(key=lambda x:(x['risk_tier']!='HIGH_META_CONFLICT',x['segment_id'],x['claim_id']))
    core={
        'schema':SCHEMA,'owner_source_sha256':census['owner_source_sha256'],
        'original_segment_count':census['segment_count'],
        'original_atom_count':census['distinct_claim_count'],
        'fact_atom_count':total_facts,
        'flagged_for_meaning_review':len(candidates),
        'high_priority':sum(x['risk_tier']=='HIGH_META_CONFLICT' for x in candidates),
        'medium_priority':sum(x['risk_tier']=='MEDIUM_SPEECH_CONTEXT' for x in candidates),
        'items':candidates,'true_error_count':None,'semantic_precision_recall':None,
        'original_atom_kind_changed':False,'native_v123_status_changed':False,
        'formal_financial_truth_certified':False,
        'e4_approved':False,'e5_authorized':False,
        'knowledge_publication_authorized':False,
    }
    return {**core,'triage_sha256':digest(core)}