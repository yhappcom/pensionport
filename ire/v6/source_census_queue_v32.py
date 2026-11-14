"""V32: all-original-cue registration and confidential ChatGPT review queue.

Fully enumerating cue hashes/windows is NOT equivalent to extracting all
atomic financial claims. Queue contents are source hashes and review states;
original captions must remain private to the chat host.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

from .codec import json_digest, sha256
from .errors import InvalidInput
from .private_original_pin_v28 import verify_private_original_archive
from .source import parse_srt, verify_source

_TOPIC = re.compile(r'ISA|IRP|ETF|연금|퇴직|세액|세금|투자|매수|매도|수익|소득|주식|분산|추납|자산|보험|금리|대출|계좌|배당|원금|월급|납입', re.I)
_CONDITION = re.compile(r'만약|경우|하면|다만|하지만|반면|그런데|예외|무조건|아니|없|못|않|단|한도|이후|이전')
_NUMBER = re.compile(r'(?<![0-9A-Za-z])\d[0-9,.]*(?:%|세|년|개월|원|만|억)?')


def make_full_source_review_queue_v32(raw: bytes, *, video_id: str,
                                      expected_srt_sha256: str,
                                      window_size: int = 40) -> dict:
    """Construct an EXACT original-cue census with all windows explicitly OPEN.

    The plan digest is generated *during this run*, not a prospective plan
    commitment. The SRT digest must already be independently pinned.
    """
    if type(window_size) is not int or not 10 <= window_size <= 80:
        raise InvalidInput('V32_WINDOW_SIZE_INVALID')
    if type(raw) is not bytes or sha256(raw) != expected_srt_sha256:
        raise InvalidInput('V32_ORIGINAL_SRT_PIN_MISMATCH')
    cues = parse_srt(raw)
    windows = []
    queue = []
    for k,start in enumerate(range(1,len(cues)+1,window_size),1):
        end=min(len(cues),start+window_size-1)
        group=cues[start-1:end]
        source_text=' '.join(c.text for c in group)
        source_topic_cues=sum(bool(_TOPIC.search(c.text)) for c in group)
        source_condition_cues=sum(bool(_CONDITION.search(c.text)) for c in group)
        literal_number_count=sum(len(_NUMBER.findall(c.text)) for c in group)
        source_digest=sha256(source_text.encode('utf-8'))
        windows.append({'window_id':f'W{k:05d}', 'first_cue':start,
                        'last_cue':end,'text_sha256':source_digest})
        queue.append({'window_id':f'W{k:05d}', 'cue_first':start,'cue_last':end,
                      'cue_count':len(group), 'window_source_sha256':source_digest,
                      'financial_keyword_cue_count_heuristic':source_topic_cues,
                      'qualifier_keyword_cue_count_heuristic':source_condition_cues,
                      'literal_numeric_token_count_heuristic':literal_number_count,
                      'status':'PENDING_CHAT_SEMANTIC_REVIEW',
                      'atom_count':None,'chat_review_receipt_sha256':None,
                      'priority':'REVIEW_EARLY' if (source_topic_cues or source_condition_cues) else 'REVIEW_STANDARD'})
    plan={'schema':'IRE_V6_SOURCE_PLAN_V1','video_id':video_id,
          'source_sha256':expected_srt_sha256,'cue_count':len(cues),
          'scope':{'mode':'FULL_VIDEO','first_cue':1,'last_cue':len(cues)},
          'windows':windows}
    verified=verify_source(raw,plan,expected_source_sha256=expected_srt_sha256,
                           expected_manifest_sha256=json_digest(plan))
    if (sum(row['cue_count'] for row in queue)!=len(cues) or
        any(r['status']!='PENDING_CHAT_SEMANTIC_REVIEW' for r in queue)):
        raise InvalidInput('V32_OPEN_QUEUE_CENSUS_INCOMPLETE')
    return {'schema':'IRE_V6_V32_FULL_CUE_OPEN_FINANCE_REVIEW_QUEUE',
            'video_id':video_id,'source_sha256':expected_srt_sha256,
            'original_cue_count':len(cues),'source_cue_census_sha256':verified.cue_census_sha256,
            'full_source_plan_sha256':json_digest(plan),
            'window_size':window_size,'window_count':len(windows),
            'queued_cue_count':sum(x['cue_count'] for x in queue),
            'reviewed_cue_count':0,'financial_meaning_atom_count':None,
            'source_plan_precommitted_before_this_run':False,
            'independent_precision_recall_measured':False,
            'source_wide_semantic_extraction_complete':False,
            'claim_to_law_applicability_review_complete':False,
            'all_windows_marked_pending':True,
            'review_queue_sha256':json_digest(queue),
            'windows':queue,
            'p0_go':False}


def verify_five_pinned_originals_and_queue_v32(zip_path: Path, *, archive_sha256: str,
                                                sources: list[dict], window_size=40):
    """Verify REAL ZIP/SRT bytes via V28 prior to building bounded queues.

    Public result is hashes and counts only; original text never leaves ZIP.
    """
    if type(sources) is not list or not 1<=len(sources)<=5:
        raise InvalidInput('V32_EXPECTED_SOURCE_LIST_REQUIRED')
    if len({x.get('video_id') for x in sources if type(x) is dict})!=len(sources):
        raise InvalidInput('V32_DUPLICATE_SOURCE_ID')
    if len({x.get('member_name') for x in sources if type(x) is dict})!=len(sources):
        raise InvalidInput('V32_DUPLICATE_ARCHIVE_MEMBER')
    path=Path(zip_path)
    public=[]
    with zipfile.ZipFile(path) as archive:
        for item in sources:
            if type(item) is not dict or set(item)!=set((
                'video_id','member_name','srt_sha256','cue_count')):
                raise InvalidInput('V32_SOURCE_MANIFEST_FIELDS_INVALID')
            v28=verify_private_original_archive(
                path,member_name=item['member_name'],expected_zip_sha256=archive_sha256,
                expected_srt_sha256=item['srt_sha256'],expected_video_id=item['video_id'],
                expected_cue_count=item['cue_count'])
            raw=archive.read(item['member_name'])
            row=make_full_source_review_queue_v32(raw,
                video_id=item['video_id'],expected_srt_sha256=item['srt_sha256'],
                window_size=window_size)
            if row['original_cue_count']!=v28['original_cue_count']:
                raise InvalidInput('V32_SOURCE_CUE_CONSENSUS_DRIFT')
            public.append(row)
    return {'schema':'IRE_V6_V32_PINNED_OWNER_ORIGINAL_FIVE_VIDEO_OPEN_WORKQUEUE',
            'archive_sha256':archive_sha256,'original_video_count':len(public),
            'original_cues_registered':sum(x['original_cue_count'] for x in public),
            'window_count':sum(x['window_count'] for x in public),
            'windows_reviewed_in_this_queue':0,
            'original_semantic_atom_recall_verified':False,
            'independent_financial_accuracy_certified':False,
            'p0_go':False,'videos':public}


def audit_contextual_allocation_v32(source, *, first_cue=173, last_cue=181,
                                    interpreted_unit='만원', reviewer='CHATGPT_CURRENT_TURN',
                                    reviewed_as_of='2026-11-10'):
    """Bound #2 conditional educational amount examples to original ASR cues.

    Some individual figures omit the suffix '만원' in ASR. Source-context
    inference must remain explicitly flagged NOT_VERBATIM_AUDIO_VERIFIED.
    """
    if (source.video_id!='6VEfKF7BzZU' or first_cue!=173 or last_cue!=181 or
        not source.scope_first_cue<=first_cue<=last_cue<=source.scope_last_cue or
        interpreted_unit!='만원' or reviewer!='CHATGPT_CURRENT_TURN' or
        type(reviewed_as_of) is not str):
        raise InvalidInput('V32_ALLOCATION_SCOPE_OR_REVIEW_INVALID')
    text=' '.join(source.cues[i-1].text for i in range(first_cue,last_cue+1))
    if not (re.search(r'50\s?만\s?원',text) and
        all(re.search(r'(?<!\d)'+n+r'(?!\d)',text) for n in ('10','40','100','80','20')) and
        'ISA' in text and ('연금' in text or '연금축' in text)):
        raise InvalidInput('V32_ALLOCATION_NUMERIC_OR_PRODUCT_SOURCE_NOT_GROUNDED')
    examples=[{'budget_krw':500000,'pension_savings_krw':100000,'isa_krw':400000},
              {'budget_krw':1000000,'pension_savings_krw':200000,'isa_krw':800000}]
    if not all(r['budget_krw']==r['pension_savings_krw']+r['isa_krw'] for r in examples):
        raise InvalidInput('V32_ALLOCATION_TOTAL_SUM_MISMATCH')
    summary={'schema':'IRE_V6_V32_CHAT_CONTEXT_NUMERIC_UNIT_INTERPRETATION',
             'video_id':source.video_id,'srt_sha256':source.source_sha256,
             'context_cue_first':first_cue,'context_cue_last':last_cue,
             'context_cue_sha256':sha256(text.encode('utf-8')),
             'reviewer':reviewer,'reviewed_as_of':reviewed_as_of,
             'interpreted_unit':'만원','examples':examples,
             'inference':'INFERRED_FROM_50_MAN_WON_AND_ADDITIVE_SPLIT',
             'numeric_addition_valid':True,
             'explicit_unit_repeated_for_each_number':False,
             'audio_transcript_independently_verified':False,
             'this_is_historical_illustration_not_personal_allocation':True,
             'personal_eligibility_or_tax_deduction_approved':False,
             'independent_financial_semantic_gold':False,
             'p0_go':False}
    summary['receipt_sha256']=json_digest(summary)
    return summary
