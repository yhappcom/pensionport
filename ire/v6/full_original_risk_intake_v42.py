"""V42: complete original source-window replay and *lexical* risk prioritization.

Never confuse this deterministic source safety triage with a complete
ChatGPT semantic reading, verified financial atom, or independent gold.
Only returns source fingerprints, numeric counters and priority metadata;
owner SRT bytes stay private. No external model API is used.
"""
from __future__ import annotations

import io
import re
import zipfile
from collections import Counter

from .codec import json_digest, sha256
from .errors import InvalidInput
from .host_semantic_custody_v39 import _v33_draft_registry
from .source import parse_srt
from .source_window_host_screen_v37 import _NUMBER

_TOPIC_RE = {
    'pension_tax': re.compile(r'ISA|IRP|연금|세액공제|소득공제|종합과세|인출|연기연금|추납|퇴직|공제|과세|1,500만|1500만',re.I),
    'broker_product': re.compile(r'CMA|MMW|RP형|발행어음|예금자|증권사|공과금|이체|자동납부|단기채|계좌|수수료|보장',re.I),
    'return_risk': re.compile(r'수익률|배당|주가|이자|원금|손실|복리|금리|폭락|하락|수익|이익|투자|장기|매도|리밸런싱',re.I),
    'personal_advice': re.compile(r'추천|절대|꼭|반드시|무조건|투자하|갈아타|바꾸|하십시오|해야|좋습니다|언제 팔|손절',re.I),
    'uncertainty': re.compile(r'가정|예를|예시|아마|정확|모르|경우|만약|수도|가능|확정|다는 건|일반적|조심',re.I),
    'financial_numbers': re.compile(r'\d[\d,.]*(?:%|원|만|억|배|세|개월|년|퍼센트)',re.I),
    'question': re.compile(r'\?|왜|어떻게|얼마|언제|뭘|무엇|인가요|습니까|할까요',re.I),
}
_WEIGHTS = {'pension_tax':7,'broker_product':6,'return_risk':4,
            'personal_advice':4,'uncertainty':2,'financial_numbers':3,'question':1}
_ALLOWED_SOURCE_KEYS = {'video_no','video_id','original_srt_sha256','cue_count'}
_V37_KEYS = {'video_no','video_id','window_id','cue_first','cue_last',
             'provisional_utterances','source_window_text_sha256','v37_candidate_list_sha256'}


def audit_full_original_risk_intake_v42(archive_bytes, *,
        expected_archive_sha256, sources, independently_pinned_v37_rows,
        expected_v37_cohort_sha256, previous_deep_window_keys=()):
    """Replay complete original owner cohort against independent V37 SHA pins.

    The caller MUST provide a separately frozen V37 cohort SHA and each video
    SRT SHA. Previously deep-reviewed window keys carry over as prior status,
    not as new ChatGPT semantics certified by this triage.
    """
    if (type(archive_bytes) is not bytes or not archive_bytes or
        type(expected_archive_sha256) is not str or
        type(expected_v37_cohort_sha256) is not str or
        type(sources) is not list or not sources or
        type(independently_pinned_v37_rows) is not list or not independently_pinned_v37_rows):
        raise InvalidInput('V42_OWNER_SOURCE_AND_INDEPENDENT_V37_PINS_REQUIRED')
    if sha256(archive_bytes)!=expected_archive_sha256:
        raise InvalidInput('V42_OWNER_ARCHIVE_SHA_PIN_MISMATCH')
    pinned_list=[];pins={};cue_census=0
    for s in sources:
        if (type(s) is not dict or set(s)!=_ALLOWED_SOURCE_KEYS or
            type(s['video_no']) is not int or type(s['video_id']) is not str or
            type(s['cue_count']) is not int or s['cue_count']<1 or
            s['video_id'] in pins or any(x['video_no']==s['video_no'] for x in pinned_list)):
            raise InvalidInput('V42_ORIGINAL_SRT_INVENTORY_SCHEMA_OR_DUPLICATE')
        pins[s['video_id']]=s
        pinned_list.append(s)
    if type(previous_deep_window_keys) not in (set,tuple,list):
        raise InvalidInput('V42_PRIOR_DEEP_KEY_TYPE_INVALID')
    known_previous=set()
    for k in previous_deep_window_keys:
        if (type(k) is not tuple or len(k)!=2 or type(k[0]) is not int or
            type(k[1]) is not str or not re.fullmatch(r'W\d{5}',k[1]) or
            k in known_previous):
            raise InvalidInput('V42_PREVIOUS_DEEP_KEY_DUPLICATE_OR_INVALID')
        known_previous.add(k)
    expected={};cohort=[]
    for w in independently_pinned_v37_rows:
        if (type(w) is not dict or set(w)!=_V37_KEYS or
            type(w['video_no']) is not int or type(w['video_id']) is not str or
            type(w['window_id']) is not str or not re.fullmatch(r'W\d{5}',w['window_id']) or
            (w['video_id'],w['window_id']) in expected):
            raise InvalidInput('V42_INDEPENDENT_V37_ROW_INVALID_OR_DUPLICATE')
        expected[(w['video_id'],w['window_id'])]=w
        cohort.append([w['video_no'],w['window_id'],w['source_window_text_sha256'],
                       w['v37_candidate_list_sha256']])
    if json_digest(cohort)!=expected_v37_cohort_sha256:
        raise InvalidInput('V42_INDEPENDENT_V37_COHORT_HASH_DRIFT')
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as z:
            if z.testzip() is not None:
                raise InvalidInput('V42_OWNER_ZIP_BAD_CRC')
            membernames=set(z.namelist())
            if len(membernames)!=len(z.namelist()):
                raise InvalidInput('V42_DUPLICATE_ZIP_ENTRY')
            actual=[]; summary=[]
            for s in pinned_list:
                vid=s['video_id']
                member=f'1-100/youtube-transcript-{vid}.srt'
                if member not in membernames:
                    raise InvalidInput('V42_OWNER_SRT_MISSING')
                raw=z.read(member)
                if sha256(raw)!=s['original_srt_sha256']:
                    raise InvalidInput('V42_OWNER_SRT_SHA_PIN_DRIFT')
                cues=parse_srt(raw)
                if len(cues)!=s['cue_count']:
                    raise InvalidInput('V42_OWNER_CUE_CENSUS_CHANGED')
                drafts=_v33_draft_registry(cues)
                count=0
                for wn,(wid,cands) in enumerate(drafts.items(),1):
                    start=(wn-1)*40+1
                    stop=min(wn*40,len(cues))
                    window_text=' '.join(c.text for c in cues[start-1:stop])
                    pin=expected.get((vid,wid))
                    if (pin is None or pin['video_no']!=s['video_no'] or
                        pin['cue_first']!=start or pin['cue_last']!=stop or
                        pin['provisional_utterances']!=len(cands) or
                        pin['source_window_text_sha256']!=sha256(window_text.encode('utf8')) or
                        pin['v37_candidate_list_sha256']!=json_digest(cands)):
                        raise InvalidInput('V42_ORIGINAL_WINDOW_OR_V33_CANDIDATE_PIN_MISMATCH')
                    counts={k:sum(1 for c in cues[start-1:stop] if pat.search(c.text))
                            for k,pat in _TOPIC_RE.items()}
                    sample_count=sum(any(_TOPIC_RE[k].search(' '.join(cues[i-1].text
                              for i in d['cue_indices'])) for k in ('pension_tax','broker_product','return_risk'))
                              for d in cands)
                    pri=sum(_WEIGHTS[k]*n for k,n in counts.items())
                    already=(s['video_no'],wid) in known_previous
                    actual.append({'video_no':s['video_no'],'video_id':vid,'window_id':wid,
                        'cue_first':start,'cue_last':stop,
                        'original_window_sha256':pin['source_window_text_sha256'],
                        'v33_candidate_list_sha256':pin['v37_candidate_list_sha256'],
                        'provisional_utterances':len(cands),'keyword_match_cues_by_theme':counts,
                        'heuristic_finance_keyword_candidates':sample_count,
                        'numeric_token_occurrences':sum(len(_NUMBER.findall(c.text))
                                                         for c in cues[start-1:stop]),
                        'lexical_priority_score_noncertified':pri,
                        'previously_deep_reviewed':already,
                        'source_first_triage_completed':True,
                        'actual_claim_meaning_truth_certified':False})
                    count+=len(cands)
                summary.append({'video_no':s['video_no'],'video_id':vid,
                    'original_srt_sha256':s['original_srt_sha256'],'original_cues':len(cues),
                    'windows':len(drafts),'provisional_speech_candidates':count})
                cue_census+=len(cues)
    except (zipfile.BadZipFile, EOFError) as e:
        raise InvalidInput('V42_OWNER_ARCHIVE_CORRUPT') from e
    if {(x['video_id'],x['window_id']) for x in actual} != set(expected):
        raise InvalidInput('V42_INCOMPLETE_OR_EXTRA_V37_COHORT')
    if not known_previous.issubset({(x['video_no'],x['window_id']) for x in actual}):
        raise InvalidInput('V42_UNKNOWN_PRIOR_DEEP_REVIEW_WINDOW')
    if len(actual)!=len(expected):
        raise InvalidInput('V42_WINDOW_CENSUS_DRIFT')
    remaining=[r for r in actual if not r['previously_deep_reviewed']]
    remaining.sort(key=lambda r:(-r['lexical_priority_score_noncertified'],r['video_no'],r['window_id']))
    n_candidates=sum(s['provisional_speech_candidates'] for s in summary)
    out={'schema':'IRE_V6_V42_COMPLETE_OWNER_SOURCE_RISK_TRIAGE_NOT_FINANCIAL_TRUTH',
        'archive_sha256':expected_archive_sha256,
        'independently_pinned_v37_cohort_sha256':expected_v37_cohort_sha256,
        'actual_source_videos':len(summary),'actual_original_cues':cue_census,
        'actual_original_windows':len(actual),
        'v33_provisional_utterance_candidates':n_candidates,
        'prior_deep_reviewed_windows':len(known_previous),
        'not_yet_deep_reviewed_windows':len(remaining),
        'not_yet_deep_reviewed_provisional_utterances':sum(r['provisional_utterances'] for r in remaining),
        'inventory':summary,'ranked_windows':remaining,
        'raw_owner_srt_or_claim_prose_in_public_receipt':False,
        'lexical_risk_rank_is_independent_semantic_truth':False,
        'all_utterances_atomically_split':False,
        'human_gold_supplied':False,'independent_precision_recall_measured':False,
        'historical_eight_audio_issuer_cases_closed':False,
        'current_user_personal_tax_trade_authorized':False,'p0_go':False}
    out['receipt_sha256']=json_digest(out)
    return out
