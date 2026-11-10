"""V37: source-bound audit of CHAT first-pass 130-window risk screening.

The host actually reads all original windows, but a one-record-per-window
risk summary is NOT claim-level atomization or independent gold. This module
verifies source bytes, exhaustive candidate references, no-atom behavior,
and the completeness/immutability of the host's coarse screening docket.

No original speech, source excerpt, host prose or secret is emitted to public
receipts. Never convert screening status into semantic accuracy certification.
"""
from __future__ import annotations

import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from .codec import json_digest, sha256
from .errors import InvalidInput
from .source import parse_srt

_NUMBER = re.compile(r'(?<![0-9A-Za-z])\d[0-9,.]*(?:%|세|년|개월|원|만|억)?')
_HIGH = re.compile(r'(?:연금|퇴직|IRP|ISA|ETF|추납|세액|비과세|원천징수|과세|중도인출|국민연금|보험료|배당|원금|수익률|금리|대출|세금|증여|상속|분산|주식|채권|투자|매도|매수|계좌)', re.I)
_REQUIRED_NOTE={'video_no','window_no','themes','financial_risks','source_speech_roles',
                'current_evidence','evidence_state','full_atomic_claims_certified'}
_REQUIRED_CANDIDATE={'video_id','video_no','claim_id','window_id','cues','source_text',
                     'source_text_sha256','risk_tax','risk_market','qualifier','numeric_tokens',
                     'review_priority','question_mark'}
_OPEN_EXPERT='NOT_MEASURED_NO_INDEPENDENT_GOLD'


def audit_full_source_firstpass_v37(archive_path, *, archive_sha256, sources,
                                     candidate_registry, host_window_notes,
                                     externally_unverified_case_ids,
                                     expected_counts=None):
    """Cross-check actual owner ZIP/SRT, draft candidates and 130 chat notes.

    Input `sources` entries: video_no, video_id, original_srt_sha256, cue_count.
    `candidate_registry` contains raw quotes PRIVATE to this call only.
    Output safe to put on public GitHub: SHA, cue refs, counters and flags.
    Unless a separate human gold is genuinely present, evaluator is not run.
    """
    if (type(archive_sha256) is not str or type(sources) is not list or
        not sources or type(candidate_registry) is not list or
        type(host_window_notes) is not list or
        type(externally_unverified_case_ids) is not list):
        raise InvalidInput('V37_INPUT_SCHEMA_REQUIRED')
    if type(expected_counts) not in (type(None),dict):
        raise InvalidInput('V37_EXPECTED_COUNTS_INVALID')
    rawzip=Path(archive_path).read_bytes()
    if sha256(rawzip)!=archive_sha256:
        raise InvalidInput('V37_OWNER_ZIP_PIN_MISMATCH')
    vids=set(); actual={}
    for row in sources:
        if (type(row) is not dict or set(row)!={'video_no','video_id','original_srt_sha256','cue_count'} or
            type(row['video_no']) is not int or row['video_no']<1 or
            type(row['video_id']) is not str or row['video_id'] in vids or
            type(row['cue_count']) is not int or row['cue_count']<=0):
            raise InvalidInput('V37_SOURCE_INVENTORY_INVALID')
        vids.add(row['video_id'])
    with zipfile.ZipFile(archive_path) as z:
        for row in sources:
            member=f"1-70/youtube-transcript-{row['video_id']}.srt"
            try: raw=z.read(member)
            except KeyError as e: raise InvalidInput('V37_EXPECTED_OWNER_SRT_MISSING') from e
            if sha256(raw)!=row['original_srt_sha256']:
                raise InvalidInput('V37_OWNER_SRT_SHA_CHANGED')
            cues=parse_srt(raw)
            if len(cues)!=row['cue_count']:
                raise InvalidInput('V37_OWNER_CUE_COUNT_CHANGED')
            actual[row['video_id']]=cues
    numbers={r['video_id']:r['video_no'] for r in sources}
    if len(set(numbers.values()))!=len(sources):
        raise InvalidInput('V37_DUPLICATE_VIDEO_NUMBER')
    windows={}
    for row in sources:
        vid=row['video_id']; cues=actual[vid]; num=row['video_no']
        for wn,first in enumerate(range(1,len(cues)+1,40),1):
            last=min(len(cues),first+39);k=(vid,wn)
            windows[k]={'video_no':num,'first':first,'last':last,'cues':cues,
                        'source_sha':sha256(' '.join(c.text for c in cues[first-1:last]).encode())}
    notes={}
    for note in host_window_notes:
        if type(note) is not dict or set(note)!=_REQUIRED_NOTE:
            raise InvalidInput('V37_CHAT_WINDOW_NOTE_SCHEMA_INVALID')
        vid=next((v for v,n in numbers.items() if n==note['video_no']),None)
        k=(vid,note['window_no'])
        if k not in windows or k in notes:
            raise InvalidInput('V37_MISSING_OR_DUPLICATE_CHAT_WINDOW_NOTE')
        for tag in ('themes','financial_risks','source_speech_roles','current_evidence'):
            if (type(note[tag]) is not list or not note[tag] or
                any(type(q) is not str or len(q.strip())<2 for q in note[tag])):
                raise InvalidInput('V37_CHAT_NOTE_EMPTY_OR_WEAK')
        if (note['full_atomic_claims_certified'] is not False or
            not note['evidence_state'].startswith('CHAT_CONTEXT_REVIEWED')):
            raise InvalidInput('V37_FALSE_ATOMIC_COMPLETION_REVIEW_STATUS')
        notes[k]=note
    if set(notes)!=set(windows):
        raise InvalidInput('V37_130_SOURCE_WINDOWS_MISSING_CHAT_NOTE')
    candidates=defaultdict(list); by_cue=defaultdict(set)
    candidate_ids=set(); total_numbers=0
    for x in candidate_registry:
        if type(x) is not dict or set(x)!=_REQUIRED_CANDIDATE:
            raise InvalidInput('V37_SOURCE_DRAFT_CANDIDATE_SCHEMA_INVALID')
        vid=x['video_id'];num=x['video_no'];wname=x['window_id'];cid=x['claim_id']
        if (vid not in numbers or num!=numbers[vid] or type(cid) is not str or
            type(wname) is not str or not re.fullmatch(r'W\d{5}',wname)):
            raise InvalidInput('V37_FOREIGN_VIDEO_CLAIM_OR_WINDOW')
        k=(vid,int(wname[1:])); key=(vid,cid)
        if k not in windows or key in candidate_ids:
            raise InvalidInput('V37_DUPLICATE_OR_FOREIGN_CLAIM')
        candidate_ids.add(key)
        if type(x['cues']) is not list or not x['cues'] or x['cues']!=sorted(set(x['cues'])):
            raise InvalidInput('V37_CUE_REFERENCES_MISSING_OR_DUPLICATED')
        if any(type(i) is not int or i<windows[k]['first'] or i>windows[k]['last'] for i in x['cues']):
            raise InvalidInput('V37_CLAIM_CROSSES_SOURCE_WINDOW')
        expected_text=' | '.join(actual[vid][idx-1].text for idx in x['cues'])
        if x['source_text']!=expected_text or sha256(expected_text.encode())!=x['source_text_sha256']:
            raise InvalidInput('V37_SOURCE_DRAFT_TEXT_HASH_MISMATCH')
        literal_numbers=sum(len(_NUMBER.findall(actual[vid][idx-1].text)) for idx in x['cues'])
        if (x['numeric_tokens']!=literal_numbers or type(x['question_mark']) is not bool or
            x['question_mark']!=('?' in expected_text or '？' in expected_text)):
            raise InvalidInput('V37_NUMERIC_OR_QUESTION_SOURCE_SCOPE_MISMATCH')
        total_numbers+=literal_numbers
        candidates[k].append({'claim_id':cid,'source_text_sha256':x['source_text_sha256'],
                               'cue_indices':x['cues'],'numeric_tokens':literal_numbers})
        for cue in x['cues']:
            if cue in by_cue[vid]:
                raise InvalidInput('V37_ORIGINAL_CUE_DUPLICATE_UTTERANCE_OWNERSHIP')
            by_cue[vid].add(cue)
    review_rows=[]; source_unanchored=0; source_counts=[]
    for r in sources:
        vid=r['video_id']; cues=actual[vid]
        missing=set(range(1,len(cues)+1))-by_cue[vid]
        source_unanchored+=len(missing)
        for i in missing:
            raw=cues[i-1].text
            if _NUMBER.search(raw) or _HIGH.search(raw):
                raise InvalidInput('V37_NUMERIC_OR_HIGH_RISK_CUE_DROPPED_AS_FILLER')
        source_counts.append({'video_no':r['video_no'],'video_id':vid,'source_sha256':r['original_srt_sha256'],
                              'cue_count':len(cues),'window_count':sum(k[0]==vid for k in windows),
                              'candidate_utterance_count':sum(len(candidates[k]) for k in windows if k[0]==vid),
                              'short_no_candidate_cue_count':len(missing)})
    for k,w in sorted(windows.items(),key=lambda t:(numbers[t[0][0]],t[0][1])):
        note=notes[k]; atoms=candidates[k]
        if not atoms:
            raise InvalidInput('V37_WINDOW_WITHOUT_UTTERANCE_OR_REVIEW')
        review_rows.append({'video_no':w['video_no'],'video_id':k[0],
                            'window_id':f'W{k[1]:05d}','cue_first':w['first'],
                            'cue_last':w['last'],'original_window_text_sha256':w['source_sha'],
                            'provisional_utterance_count':len(atoms),
                            'draft_candidate_digest_sha256':json_digest(atoms),
                            'chat_window_firstpass_review_sha256':json_digest(note),
                            'chat_source_window_screening':'CHAT_SOURCE_CONTEXT_SCREENED_NOT_ATOMIC_GOLD',
                            'all_utterances_atomized_and_approved':False,
                            'financial_fact_semantically_approved':False})
    if (len(set(externally_unverified_case_ids))!=len(externally_unverified_case_ids) or
        any(type(x) is not str or not re.fullmatch('[0-9a-f]{64}',x) for x in externally_unverified_case_ids)):
        raise InvalidInput('V37_EXTERNAL_EVIDENCE_ID_SCHEMA_INVALID')
    totals={'source_video_count':len(actual),'original_cues':sum(len(v) for v in actual.values()),
            'source_windows':len(windows),'provisional_utterances':len(candidate_registry),
            'cues_with_provisional_utterance':sum(len(s) for s in by_cue.values()),
            'short_no_candidate_cues':source_unanchored,'literal_source_number_occurrences':total_numbers,
            'chat_firstpass_window_reviews':len(notes),
            'verified_external_audio_product_cases':0,
            'still_open_external_audio_product_case_ids':len(externally_unverified_case_ids)}
    if expected_counts is not None:
        for key,value in expected_counts.items():
            if key not in totals or totals[key]!=value:
                raise InvalidInput('V37_EXACT_PRIVATE_COHORT_CENSUS_DRIFT')
    # Public result has source provenance and note digests ONLY; no raw prose.
    receipt={'schema':'IRE_V6_V37_PRIVATE_OWNER_FULL_5_VIDEO_130_WINDOW_CHAT_FIRSTPASS_HASH_ONLY',
             'source_archive_sha256':archive_sha256,'totals':totals,
             'video_source_counts':source_counts,'window_review_rows':review_rows,
             'unverified_source_evidence_case_sha256':sorted(externally_unverified_case_ids),
             'host_window_review_prose_not_published':True,
             'actual_private_srt_cues_reopened_this_turn':True,
             'all_130_window_contexts_chat_firstpass_screened':True,
             'all_1603_drafts_source_hash_verified':True,
             'all_1603_utterances_semantically_atomized':False,
             'all_130_windows_financial_meaning_claims_certified':False,
             'official_issuer_product_terms_original_audio_verified':False,
             'independent_blind_gold_available':False,
             'precision_recall_true_tp_fp_fn_measured':False,
             'master116_auto_merge_approved':False,
             'personal_tax_or_trading_approved':False,'p0_go':False,
             'independent_financial_semantic_accuracy_status':_OPEN_EXPERT}
    receipt['receipt_sha256']=json_digest(receipt)
    return receipt
