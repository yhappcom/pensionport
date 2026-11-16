"""V33: lossless all-cue provisional *utterance* draft registry for private SRTs.

Never conflate an utterance with a semantically atomic financial claim.
This module creates source-anchored, UNRESOLVED candidate units in every
V32 window; the ChatGPT host must split and classify them further, check
current official sources, and adjudicate prior knowledge before research use.
No subtitles, quotes, or candidate text appear in public receipts.
"""
from __future__ import annotations

import hashlib
import re
from collections import Counter

from .atomic_exchange import NUMBER, audit_host_atomic_exchange
from .codec import json_digest, sha256
from .errors import InvalidInput
from .semantic_risk import CONDITION, EXCEPTION, audit_semantic_risks
from .source import verify_source, parse_srt

_CLOSING = re.compile(r'[.!?。？！][\s\"\']*$')
_FILLER = re.compile(r'^(?:>>\s*)?(?:네|예|응|어|아|음|그죠|그렇죠|맞아요|하하|아하|그렇군요|음|웃음|감사합니다|안녕하세요)[.?!\s\[\]]*$')
_SPEAKER = re.compile(r'^\s*>>\s*')
_REVIEW_HIGH = re.compile(r'(?:연금|퇴직|IRP|ISA|ETF|추납|세액|비과세|원천징수|과세|중도인출|국민연금|보험료|배당|원금|수익률|금리|대출|세금|증여|상속|분산|주식|채권|투자|매도|매수|계좌)',re.I)


def _draft_spans(cues, first, last, *, max_cues=7):
    """Source-respecting ASR utterance spans, not an entailment parser."""
    if type(max_cues) is not int or not 2 <= max_cues <= 12:
        raise InvalidInput('V33_PROVISIONAL_SEGMENT_LIMIT_INVALID')
    spans=[]
    current=[]
    def flush():
        nonlocal current
        if current:
            spans.append(current)
            current=[]
    for i in range(first,last+1):
        c=cues[i-1]
        text=c.text.strip()
        if _SPEAKER.search(text) and current:
            flush()
        if _FILLER.fullmatch(text) and len(text)<16:
            flush()
            spans.append([i])
            continue
        current.append(i)
        combined=' '.join(cues[j-1].text for j in current)
        # A literal punctuation mark often marks sentence end; ASR breaks
        # sentence across cues and rarely fully preserves punctuation.
        if ((len(combined)>=5 and _CLOSING.search(text)) or
            len(current)>=max_cues or len(combined)>1450):
            flush()
    flush()
    return spans


def draft_full_original_utterance_exchange_v33(source, *, max_cues=7):
    """Actual full-video V6 exchange with all cues explicitly dispositioned.

    `proposition` is an ASR utterance COPY. It may have zero, one or several
    atomic claims. Nothing in this output is allowed as a verified fact.
    """
    if source.scope_first_cue != 1 or source.scope_last_cue != len(source.cues):
        raise InvalidInput('V33_FULL_SOURCE_REQUIRED')
    by_cue={i:[] for i in range(1,len(source.cues)+1)}
    atoms=[]
    counts=Counter()
    for wid,first,last in source.primary_windows:
        spans=_draft_spans(source.cues,first,last,max_cues=max_cues)
        for indices in spans:
            texts=[source.cues[i-1].text for i in indices]
            entire=' '.join(texts).strip()
            # All source fragments still have a disposition. Short purely
            # conversational acknowledgement is not an atom proposal.
            if (len(entire)<5 or (_FILLER.fullmatch(entire) and len(entire)<16)):
                counts['no_atom_conversational_cues']+=len(indices)
                continue
            valid=[i for i in indices if len(source.cues[i-1].text.strip())>=2]
            if not valid:
                counts['no_atom_conversational_cues']+=len(indices)
                continue
            cid=f'C{len(atoms)+1:05d}'
            # Encode literal original utterance only, with no inferred words.
            # In particular DO NOT assign speaker, entailment, legal effect.
            prop=' | '.join(source.cues[i-1].text for i in valid).strip()
            refs=[{'cue_index':i,'quote':source.cues[i-1].text} for i in valid]
            numeric=[{'cue_index':i,'token':t}
                     for i in valid for t in NUMBER.findall(source.cues[i-1].text)]
            conditions=sorted(i for i in valid if CONDITION.search(source.cues[i-1].text))
            exceptions=sorted(i for i in valid if EXCEPTION.search(source.cues[i-1].text))
            kind='QUESTION' if ('?' in prop or '？' in prop) else 'OPINION'
            atom={
                'claim_id':cid,'owner_window_id':wid,
                'proposition':prop[:3000],
                'kind':kind,
                'stance':'UNRESOLVED','speaker':'UNKNOWN',
                'source_refs':refs,'context_cue_indices':valid,
                'condition_cue_indices':conditions,
                'exception_cue_indices':exceptions,
                'numeric_references':numeric,
                'as_of':None,
            }
            atoms.append(atom)
            for i in valid:
                by_cue[i].append(cid)
            counts['draft_utterance_candidates']+=1
            counts['draft_numeric_references']+=len(numeric)
            if _REVIEW_HIGH.search(prop):
                counts['finance_keyword_utterances']+=1
            if kind=='QUESTION':
                counts['question_utterances']+=1
            if len(indices)>1:
                counts['multi_cue_utterances']+=1
            # Fragmentary ASR is potentially multi-claim even in one span.
            if prop.count('.')+prop.count('?')>=2:
                counts['possibly_multi_sentence_utterances']+=1
    disp=[]
    for i,c in enumerate(source.cues,1):
        ids=sorted(by_cue[i])
        status='CANDIDATES' if ids else 'NO_ATOM'
        disp.append({'cue_index':i,'cue_text_sha256':sha256(c.text.encode('utf-8')),
                     'disposition':status,'claim_ids':ids,
                     'numeric_tokens':NUMBER.findall(c.text),
                     'note':'PROVISIONAL_ASR_UTTERANCE_NOT_SEMANTICALLY_ATOMIC'
                            if ids else 'CONVERSATION_ACK_OR_SHORT_NONCLAIM_FRAGMENT'})
    return ({'schema':'IRE_V6_HOST_ATOMIC_EXCHANGE_V1',
             'video_id':source.video_id,'source_sha256':source.source_sha256,
             'manifest_sha256':source.manifest_sha256,
             'cue_dispositions':disp,'atoms':atoms},dict(counts))


def audit_full_original_provisional_v33(source,exchange,*,expected_window_count=None):
    """Fail closed on unverifiable source or leaked semantic-complete flag."""
    structural=audit_host_atomic_exchange(source,exchange)
    risks=audit_semantic_risks(source,exchange)
    if expected_window_count is not None and len(source.primary_windows)!=expected_window_count:
        raise InvalidInput('V33_WHOLE_SOURCE_WINDOW_COUNT_DRIFT')
    if structural['original_scoped_cues_enumerated']!=len(source.cues):
        raise InvalidInput('V33_ORIGINAL_CUE_CENSUS_GAP')
    if structural['unresolved_cues']:
        raise InvalidInput('V33_EXCHANGE_DISPOSITIONS_UNRESOLVED')
    if structural['suspicious_no_atom_cues'] or any(
        row['numeric_tokens'] for row in exchange['cue_dispositions']
        if row['disposition']=='NO_ATOM'
    ):
        raise InvalidInput('V33_RISKY_OR_NUMERIC_NO_ATOM_REQUIRES_REVIEW')
    for row in exchange['atoms']:
        if row['stance']!='UNRESOLVED' or row['speaker']!='UNKNOWN':
            raise InvalidInput('V33_DRAFT_CANNOT_PRETEND_REVIEWED_FACT')
    # Has no semantic correctness guarantee: content may be multiple claims.
    bywin=Counter(a['owner_window_id'] for a in exchange['atoms'])
    bycue=sum(1 for d in exchange['cue_dispositions'] if d['disposition']=='CANDIDATES')
    windowrows=[]
    for wid,first,last in source.primary_windows:
        windowrows.append({'window_id':wid,'first_cue':first,'last_cue':last,
                           'cue_count':last-first+1,
                           'provisional_utterance_candidates':bywin[wid],
                           'status':'REQUIRES_CHAT_ATOMIC_SPLIT_AND_EVIDENCE_REVIEW'})
    return {
       'schema':'IRE_V6_V33_PROVISIONAL_UTTERANCE_DRAFT_HASH_ONLY',
       'video_id':source.video_id,'source_sha256':source.source_sha256,
       'manifest_sha256':source.manifest_sha256,
       'cue_census_sha256':source.cue_census_sha256,
       'original_cue_count':len(source.cues),
       'source_windows_registered':len(source.primary_windows),
       'cue_dispositions_audited':structural['original_scoped_cues_enumerated'],
       'cues_with_draft_utterance_candidates':bycue,
       'cues_marked_no_candidate':len(source.cues)-bycue,
       'heuristic_risky_no_atom_cues':structural['suspicious_no_atom_cues'],
       'provisional_utterance_candidates':len(exchange['atoms']),
       'full_utterance_draft_digest':structural['atom_candidate_digest'],
       'cue_disposition_digest':structural['cue_disposition_digest'],
       'semantic_risk_alerts_pending':risks['review_case_count'],
       'semantic_risk_docket_sha256':risks['case_census_sha256'],
       'all_original_utterances_semantically_atomic':False,
       'chat_meaning_review_completed':False,
       'complete_original_claim_recall_certified':False,
       'independent_gold_precision_recall_measured':False,
       'current_financial_law_corroborated':False,
       'approved_master_116_knowledge_merge':False,
       'p0_go':False,
       'window_review_queue':windowrows,
    }
