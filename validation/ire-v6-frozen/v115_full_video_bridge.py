"""V115 full-video owner-private cue and meaning lineage gate (no model API).

Verifies real original source bytes supplied by owner, complete parent partition,
all-cue meaning disposition and source-pinned review propositions. Separately
links every factual candidate to a pending official-evidence row, never certifies
semantic correctness, claim recall, personal suitability or financial truth.

For ChatGPT-native research, a host supplies *already reviewed* annotations.
The stage runner can resume through prepared stages in one invocation, but cannot
secretly invoke ChatGPT or other models. Private text never enters the public
receipt or SQLite stage journal.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from time import perf_counter_ns
from urllib.parse import urlsplit

from ire.v6.research_pipeline_v114 import V114ResearchJournal, STAGES, ZERO, UnsafeResearchStage

SRT = re.compile(r'\n\s*\n')
_CLOCK = re.compile(r'(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})\Z')
_SHA = re.compile(r'[0-9a-f]{64}\Z')
_VIDEO = re.compile(r'[0-9A-Za-z_-]{11}\Z')
_NO = object()
_ROLES = {'CONTEXT','QUESTION','EXPLANATION','INFERENCE','CONTRAST',
          'GENERALIZATION','DEFINITION','MECHANISM','HOW_TO','SCREEN_EXAMPLE',
          'CONDITIONAL','COMPARISON','ADVICE','OUTRO'}
_STANCES={'AFFIRMED','QUESTION','CONDITIONAL','RECOMMENDATION','QUOTED_VISUAL',
          'OUTRO','CONTEXT_ONLY','CORRECTED','NEGATED','REBUTTAL','QUOTED'}
_RISKS={'CONTEXT_ONLY','LOW','CONTEXTUAL','QUALIFY','HIGH','CRITICAL'}

def _fail(predicate, code):
    if not predicate:
        raise UnsafeResearchStage('V115_'+code)

def sha(data):
    return hashlib.sha256(data if isinstance(data,bytes) else data.encode('utf-8')).hexdigest()

def digest(value):
    return sha(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False))

def clock(t):
    m=_CLOCK.fullmatch(t.strip())
    _fail(m is not None, 'CLOCK_INVALID')
    h,mi,s,ms=map(int,m.groups())
    _fail(mi<60 and s<60,'CLOCK_OUT_OF_RANGE')
    return ((h*60+mi)*60+s)*1000+ms

def parse_exact_srt(raw):
    _fail(type(raw) is bytes and 0<len(raw)<=32*1024*1024,'ORIGINAL_SRT_REQUIRED')
    try:
        text=raw.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise UnsafeResearchStage('V115_SRT_UTF8_INVALID') from exc
    text=text.replace('\r\n','\n').replace('\r','\n').strip()
    cues=[]
    for n,block in enumerate(SRT.split(text),1):
        lines=block.split('\n')
        _fail(len(lines)>=3 and lines[0].strip().isdigit() and int(lines[0])==n,
              'SOURCE_INDEX_GAP')
        times=re.split(r'\s*-->\s*',lines[1])
        _fail(len(times)==2,'TIMECODE_ARROW')
        first,last=map(clock,times)
        _fail(first<=last and (not cues or first>=cues[-1]['start_ms']),
              'NONMONOTONE_TIMECODE')
        source=' '.join(p.strip() for p in lines[2:] if p.strip())
        _fail(bool(source),'SOURCE_TEXT_EMPTY')
        cues.append({'cue_index':n,'cue_sha256':sha(source),
                     'start_ms':first,'end_ms':last,'text':source})
    return cues

def _sorted_unique_ints(indices, allowed):
    return (type(indices) is list and bool(indices) and
            all(type(x) is int and x in allowed for x in indices) and
            indices==sorted(set(indices)))

def audit_private_review(*,raw_srt,ledger,docket,expected_srt_sha256,
                         expected_zip_sha256=None,private_zip_sha256=None):
    """Actual private-source crosswalk; outputs only hashes/counts.

    All risk/open judgments are same-chat provisional and not independent gold.
    Never create a public file with `ledger`, `docket`, or original transcript.
    """
    t0=perf_counter_ns()
    _fail(type(ledger) is dict and type(docket) is list,'PRIVATE_LEDGER_REQUIRED')
    _fail(type(expected_srt_sha256) is str and _SHA.fullmatch(expected_srt_sha256),
          'SRT_SHA_PIN_REQUIRED')
    _fail(sha(raw_srt)==expected_srt_sha256==ledger.get('source_sha256'),
          'OWNER_SOURCE_MISMATCH')
    if expected_zip_sha256 is not None:
        _fail(type(private_zip_sha256) is str and private_zip_sha256==expected_zip_sha256==
              ledger.get('source_original_zip_sha256'),'OWNER_ARCHIVE_PIN_MISMATCH')
    _fail(type(ledger.get('source_video_id')) is str and
          _VIDEO.fullmatch(ledger['source_video_id']),'VIDEO_ID_INVALID')
    cues=parse_exact_srt(raw_srt)
    n=len(cues)
    _fail(n==ledger.get('source_cues'),'SOURCE_CUE_COUNT_DRIFT')
    byidx={x['cue_index']:x for x in cues}
    _fail([{'cue_index':x['cue_index'],'sha256':x['cue_sha256']} for x in cues]
          ==ledger.get('source_cue_hashes'),'PRIVATE_SOURCE_CUE_DIGEST_DRIFT')
    for flag in ('original_audio_verified','original_video_screen_verified',
                 'independent_gold','semantics_complete_certified','p0_go'):
        _fail(ledger.get(flag) is False,'FALSE_SOURCE_RESEARCH_APPROVAL')
    _fail(ledger.get('precision') is None and ledger.get('recall') is None,
          'FALSE_INDEPENDENT_ACCURACY')
    parents=ledger.get('parents')
    units=ledger.get('atom_proposals')
    _fail(type(parents) is list and len(parents)>0 and
          type(units) is list and len(units)>0, 'MISSING_PARENT_OR_PROPOSITIONS')
    covered=[]
    pids=set()
    for p in parents:
        _fail(type(p) is dict,'PARENT_FIELDS')
        pid=p.get('parent_id')
        _fail(type(pid) is str and pid and pid not in pids,'DUPLICATE_PARENT')
        pids.add(pid)
        start,end=p.get('first_cue'),p.get('last_cue')
        _fail(type(start) is int and type(end) is int and 1<=start<=end<=n,
              'PARENT_SPAN_OUT_OF_RANGE')
        arr=list(range(start,end+1))
        _fail(p.get('cue_indices')==arr and p.get('speech_act') in _ROLES,
              'PARENT_OWNERSHIP_DRIFT')
        _fail(p.get('speaker')=='NARRATOR_PRESUMED_NOT_AUDIO_VERIFIED' and
              p.get('source_meaning_claims_verified_independently') is False,
              'PARENT_SPEAKER_CERTIFIED_WITHOUT_AUDIO')
        _fail(p.get('source_text_sha256')==sha(' '.join(byidx[i]['text'] for i in arr)),
              'PARENT_ORIGINAL_TEXT_HASH_MISMATCH')
        covered.extend(arr)
    _fail(covered==list(range(1,n+1)),'PARENT_SOURCE_CENSUS_NOT_EXHAUSTIVE')
    all_unit_cues=set(); unit_map={};risk_count=0
    for u in units:
        _fail(type(u) is dict,'UNIT_FIELDS_INVALID')
        uid=u.get('unit_id')
        _fail(type(uid) is str and uid and uid not in unit_map,'DUPLICATE_UNIT')
        arr=u.get('cue_indices')
        _fail(_sorted_unique_ints(arr,byidx),'UNIT_SOURCE_REFS_INVALID')
        _fail([byidx[i]['cue_sha256'] for i in arr] == u.get('cue_sha256'),
              'UNIT_SOURCE_SHA_MISMATCH')
        _fail(u.get('source_span_digest')==sha(''.join(byidx[i]['cue_sha256'] for i in arr)),
              'UNIT_SPAN_HASH_MISMATCH')
        _fail(u.get('speaker_stance') in _STANCES and u.get('risk_level') in _RISKS,
              'UNIT_UNKNOWN_STANCE_OR_RISK')
        _fail(type(u.get('owner_private_paraphrase')) is str and
              bool(u.get('owner_private_paraphrase').strip()),'UNIT_EMPTY_SEMANTIC_REVIEW')
        _fail(u.get('origin')=='SINGLE_CHAT_REVIEW_OF_REAL_ORIGINAL_SRT' and
              u.get('speaker_audio_confirmed') is False and
              u.get('independent_gold') is False and
              u.get('financial_fact_approved') is False and
              u.get('knowledge_merge_approved') is False,'UNIT_UNEARNED_CERTIFICATION')
        if u['risk_level'] in ('HIGH','CRITICAL'):
            risk_count+=1
        all_unit_cues.update(arr)
        unit_map[uid]=u
    _fail(all_unit_cues==set(byidx),'CLAIM_OR_CONTEXT_DISPOSITION_GAP')
    present=set(); status_count={'COUNTEREVIDENCE_OPEN':0,'GENERAL_SCOPE_OPEN':0}
    source_candidates={uid:u for uid,u in unit_map.items() if u.get('official_check_group')}
    _fail(len(docket)==len(source_candidates),'OFFICIAL_FACT_REVIEW_DOCKET_CENSUS')
    official_urls=set()
    for row in docket:
        _fail(type(row) is dict and type(row.get('unit_id')) is str,'DOCKET_ROW_FIELDS')
        uid=row['unit_id']
        _fail(uid in source_candidates and uid not in present,'DUPLICATE_OR_ABSENT_UNIT_DOCKET')
        present.add(uid)
        src=source_candidates[uid]
        _fail(row.get('source_cue_indices')==src['cue_indices'],
              'DOCKET_SOURCE_CUE_REBIND')
        urls=row.get('official_reference_urls')
        _fail(type(urls) is list and len(urls)<=12,'OFFICIAL_URL_LIST')
        for url in urls:
            _fail(type(url) is str and len(url)<1500,'OFFICIAL_URL_TYPE')
            u=urlsplit(url)
            _fail(u.scheme=='https' and u.hostname and u.username is None and
                  u.password is None and u.port is None and not u.fragment,
                  'OFFICIAL_URL_UNSAFE')
            # Regulated domains only; fund issuer notice is evidence of a
            # published issuer position, not legislation or a government source.
            _fail(any(u.hostname==host or u.hostname.endswith('.'+host) for host in (
                'krx.co.kr','law.go.kr','nts.go.kr','fss.or.kr','fsc.go.kr',
                'plusetf.co.kr','riseetf.co.kr')),'OFFICIAL_URL_HOST_NOT_ALLOWED')
            official_urls.add(url)
        _fail(row.get('checked_date')==('2026-11-14' if urls else None),
              'REFERENCE_DATE_DRIFT')
        _fail(row.get('status') in status_count, 'UNKNOWN_CASE_STATUS')
        if not urls:
            _fail(row.get('must_verify_product_screens') is True,
                  'EMPTY_EVIDENCE_NOT_EXPLICITLY_OPEN')
        _fail(row.get('official_body_content_hash_verified') is False and
              row.get('personal_applicability_verified') is False and
              row.get('approved') is False,
              'DOCKET_FACT_AUTO_APPROVED')
        status_count[row['status']]+=1
    _fail(present==set(source_candidates),'DOCKET_MISSING_OR_WRONG_UNITS')
    _fail(ledger.get('source_windows')==(n+39)//40,'PRIMARY_40CUE_WINDOWS')
    public={
        'schema':'V115_REAL_OWNER_PRIVATE_FULL_VIDEO_CUE_AND_FACT_CROSSWALK_V1',
        'video_id':ledger['source_video_id'],
        'source_srt_sha256':expected_srt_sha256,
        'original_cues':n,'source_windows':ledger['source_windows'],
        'discourse_clusters':len(parents),'same_chat_semantic_units':len(units),
        'all_source_cues_accounted':len(all_unit_cues),
        'source_cues_unaccounted':n-len(all_unit_cues),
        'pending_finance_docket_rows':len(docket),
        'higher_risk_units_pending':risk_count,
        'distinct_official_and_issuer_urls':len(official_urls),
        'without_original_screen_or_audio':True,
        'independent_gold':False,'precision':None,'recall':None,
        'approved_financial_facts':0,'p0_go':False,
        'internal_review_correctness_independently_certified':False,
        'source_private_claim_digest_sha256':digest(units),
        'source_private_docket_digest_sha256':digest(docket),
        'parse_check_wall_ns':perf_counter_ns()-t0,
    }
    return public

def resume_prepared_five_stage_run(db_path, project_id, payloads):
    """Continue prepared host-reviewed evidence through all bounded stages.

    Exact source/payload digest agreement required for every previously committed
    checkpoint. This runs the Python stages without re-entering ChatGPT; it does
    NOT drive ChatGPT inference, web lookup, independent gold, or personal advice.
    """
    _fail(type(payloads) is dict and set(payloads)==set(STAGES),
          'FIVE_STAGE_PAYLOAD_SET_REQUIRED')
    journal=V114ResearchJournal(db_path)
    snap=journal.snapshot(project_id)
    # Guard against source confusion even if the DB had a valid prior chain.
    if snap['completed_stages']:
        with journal._connect() as db:
            rows=db.execute('SELECT stage,payload_json,run_id,prev_hash,event_hash FROM events '
                            'WHERE project_id=? ORDER BY ordinal',(project_id,)).fetchall()
        for row in rows:
            name=row['stage']
            _fail(json.loads(row['payload_json'])==payloads[name],
                  'CHECKPOINT_REVIEW_CHANGED_WITHOUT_NEW_VERSION')
    out=[]
    for stage in STAGES:
        snap=journal.snapshot(project_id)
        if snap['ready_for_next'] is None:
            break
        if STAGES.index(stage)<snap['completed_stages']:
            continue
        _fail(snap['ready_for_next']==stage,'NONSEQUENTIAL_STAGE_SCHEDULE')
        resp=journal.submit(project_id=project_id,run_id=f'{project_id}_{stage}',
                            expected_head=snap['head_sha256'],stage=stage,
                            payload=payloads[stage])
        out.append({'stage':stage,'new_head_sha256':resp['new_head_sha256']})
    complete=journal.snapshot(project_id)
    _fail(complete['completed_stages']==5,'FIVE_STAGE_CHAIN_INCOMPLETE')
    return {'project_id':project_id,'five_stages_recorded':complete['completed_stages'],
            'newly_recorded_stages':len(out),'restarted_from_snapshot':len(out)<5,
            'head_sha256':complete['head_sha256'],
            'model_inference_automated':False,'independent_gold':False,
            'research_complete':False,'p0_go':False}

def assert_public_replay_receipt(receipt):
    """Guard the V115 real private pilot's PUBLIC summary, not its hidden SRT."""
    _fail(type(receipt) is dict and receipt.get('schema')==
          'V115_ACTUAL_SINGLE_CHAT_152_CUES_5_STAGE_NO_GOLD', 'PUBLIC_RECEIPT_SCHEMA')
    expected={
      'video_id':'7RRWNL0V6As',
      'source_original_zip_sha256':'00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd',
      'source_srt_sha256':'4515d3446c4874d3a376d86b1dd46ab89446e992911b0d42b52aa0df5ffb3c83',
      'original_cue_count':152, 'source_cue_coverage':152,'source_cues_without_unit_link':0,
      'window_count':4,'chat_reviewed_discourse_clusters':20,
      'chat_provisional_semantic_units':29,'finance_education_docket_rows':26,
      'high_critical_unit_open_flags':11,'official_reference_url_count':6,
      'five_stage_checkpoint_count':5,'checkpoint_idempotent_replay':True,
      'model_call_automated':False,'new_knowledge_approved':0,
      'independent_gold':False,'precision':None,'recall':None,'high_risk_recall':None,
      'tr_total_elimination_claim_mentions':2,'tr_domestic_equity_exception_types':1,
      'original_audio_verified':False,'original_screen_verified':False,
      'all_atomic_claims_certified':False,'full_historical_dedup_complete':False,
      'v75_404_identity_recovered':False,'research_complete':False,'p0_go':False,
    }
    for k,v in expected.items():
        _fail(receipt.get(k,_NO)==v,'PUBLIC_BASELINE_DRIFT_'+k.upper())
    for k in ('private_atom_digest_sha256','private_finance_docket_sha256',
              'five_stage_journal_head_sha256'):
        _fail(type(receipt.get(k)) is str and _SHA.fullmatch(receipt[k]) is not None,
              'PUBLIC_DIGEST_REQUIRED_'+k.upper())
    times=receipt.get('local_structure_stage_wall_ns')
    _fail(type(times) is dict and set(times)=={
        'source_parse_and_hash','source_semantic_ledger_construction',
        'finance_reference_docket_construction'},'PUBLIC_STAGE_TIMING_SCHEMA')
    _fail(all(type(v) is int and v>=0 for v in times.values()),
          'PUBLIC_STRUCTURE_RUNTIME')
    for unmeasured in ('model_semantic_wall_ns','official_search_wall_ns',
                       'open_resolution_wall_ns'):
        _fail(receipt.get(unmeasured) is None,'PUBLIC_FALSE_MEASURED_'+unmeasured.upper())
    return {'public_cue_review_pilot_receipt_consistent':True,
            'independent_gold':False,'full_research_complete':False,
            'v75_recovered':False,'p0_go':False}
