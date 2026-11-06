"""Public and optional private V5 original-cue review for #1 windows 11-20.

This verifies 20 actual MODEL+EVIDENCE+RELATION reviewed source windows,
not the entire five-video finance claim recall or any financial fact approval.
"""
from __future__ import annotations
import argparse,hashlib,json,re,zipfile
from pathlib import Path
from .first_five_phase1_cue_gate import verify as verify_first,Phase1ReviewError,VIDEO_IDS,ZIP_SHA

P=Path('ire/v5/validation')
F=P/'first_five_phase1_video1_11_20_cue_review_20261106.json'
OLD=P/'v5_first_five_video_01_window_review_20261106.json'
NONCLAIM={12:set(range(190,195))|{202,203,204},19:{326,327},20:{343,344}}
RETIRED={'V5C0011','V5C0013'}

def ensure(ok,why):
    if not ok:raise Phase1ReviewError(why)

def verify(root:Path, replace:dict|None=None,original_zip:Path|None=None,
           private_root:Path|None=None)->dict:
    root=Path(root)
    prev=verify_first(root)
    data=replace if replace is not None else json.loads((root/F).read_text('utf-8'))
    original=json.loads((root/OLD).read_text('utf-8'))
    ensure(data.get('schema')=='IRE_V5_FIRST_FIVE_PHASE1_SECOND_TEN_CUE_AUDIT_V1'
      and data.get('as_of')=='2026-11-06'
      and data.get('original_zip_sha256')==ZIP_SHA
      and data.get('source_review')=='VIDEO_1_WINDOWS_11_TO_20_170_TO_349_INCLUSIVE',
      'PHASE1_SECOND_TEN_SCOPE_OR_ARCHIVE_MISMATCH')
    recorded_old=json.loads((root/P/'first_five_phase1_video1_10_windows_cue_review_20261106.json').read_text('utf-8'))
    ensure(data.get('first_ten_prior_event_head_sha256')==recorded_old['per_video_replayed_private_status'][0]['event_chain_head_sha256'],
           'PHASE1_SECOND_TEN_PRIOR_EVENT_NOT_PRESERVED')
    ensure(data.get('original_cues_in_this_batch')==180
      and data.get('newly_dispositioned_unresolved_cues_in_this_batch')==171
      and data.get('previous_five_video_unresolved_cue_count')==4749
      and data.get('current_five_video_unresolved_cue_count')==4578
      and data.get('total_five_video_windows_reviewed_model_evidence_relation')==20
      and data.get('total_video1_source_cues_reviewed_first_20')==349
      and data.get('five_video_model_windows_still_288')==288
      and data.get('original_public_batch_processed_windows_remain_5')==5
      and data.get('private_event_records_video1_now_3')==3
      and data.get('claim_count_video1_now_104')==104
      and data.get('claim_count_five_videos_now_295')==295,
      'PHASE1_SECOND_TEN_AGGREGATE_SOURCE_REVIEW_COUNT_CHANGED')
    ensure(data.get('retired_previous_scope_claim_ids')==sorted(RETIRED)
      and data.get('source_private_quote_text_uploaded_to_git') is False
      and data.get('full_original_atomic_recall_proven') is False
      and data.get('all_five_ResearchRun_CLOSURE_issued') is False
      and data.get('official_personal_finance_fact_approved')==0
      and data.get('B04_legacy_merge_approved') is False
      and data.get('investment_advice_authorized') is False
      and data.get('release')=='SOURCE_CUE_EVIDENCE_RELATION_REVIEW_PROGRESS_ONLY_NO_GO',
      'PHASE1_SECOND_TEN_FALSE_FINANCIAL_RELEASE')
    rows=data.get('source_window_reviews');prev_index={x['window_id']:x for x in original['records']}
    ensure(type(rows) is list and len(rows)==10,'PHASE1_SECOND_TEN_WINDOWS_MISSING')
    all_cues=[];allclaims=[];cnt_link=0;cnt_nonclaim=0
    for n,row in enumerate(rows,11):
        wid=f'W{n:05d}';o=prev_index[wid]
        ensure(row.get('window_id')==wid and row.get('video_number')==1
          and row.get('video_id')==VIDEO_IDS[0] and row.get('first_cue')==o['first_cue']
          and row.get('last_cue')==o['last_cue'] and row.get('window_sha256')==o['primary_text_sha256'],
          'PHASE1_SECOND_TEN_WINDOW_HASH_OR_POSITION_INVALID')
        ids=list(range(o['first_cue'],o['last_cue']+1));all_cues.extend(ids)
        claims=row.get('claims');disps=row.get('cue_dispositions')
        ensure(type(claims) is list and type(disps) is list and len(disps)==len(ids),
          'PHASE1_SECOND_TEN_CUE_DISPOSITIONS_MISSING')
        linked={i:set() for i in ids}
        for c in claims:
            id=c.get('claim_id')
            ensure(type(id) is str and re.fullmatch(r'V5C\d{4}',id) is not None
               and id not in RETIRED and c.get('financial_fact_approved') is False
               and type(c.get('paraphrase')) is str and len(c['paraphrase'])>=8
               and c.get('kind') in {'QUESTION','PERSONAL_CASE','RULE','HYPOTHETICAL','OPINION','RECOMMENDATION','MATH'}
               and type(c.get('cue_ids')) is list and len(c['cue_ids'])>0
               and not set(c).intersection({'source_refs','quote','source_text'}),
               'PHASE1_SECOND_TEN_CLAIM_RETIRED_OR_RAW_SOURCE')
            allclaims.append(id)
            for cue in c['cue_ids']:
                ensure(type(cue) is int and cue in linked and id not in linked[cue],
                  'PHASE1_SECOND_TEN_MISSING_ATOMIC_CUE_REF')
                linked[cue].add(id)
        for cue,d in zip(ids,disps):
            ensure(d.get('cue_index')==cue and type(d.get('claim_ids')) is list
                and set(d['claim_ids'])==linked[cue],
                'PHASE1_SECOND_TEN_REVERSE_CUE_MISMATCH')
            if linked[cue]:
                ensure(d.get('status')=='LINKED' and cue not in NONCLAIM.get(n,set()),
                    'PHASE1_SECOND_TEN_CUE_NOT_SOURCE_LINKED')
                cnt_link+=1
            else:
                ensure(d.get('status')=='NONCLAIM' and cue in NONCLAIM.get(n,set())
                  and type(d.get('reason')) is str and len(d['reason'])>=12,
                  'PHASE1_SECOND_TEN_UNREVIEWED_CUE_AUTO_NONCLAIM')
                cnt_nonclaim+=1
        ensure({cue for cue in ids if not linked[cue]}==NONCLAIM.get(n,set())
          and row.get('full_external_fact_certified') is False
          and row.get('legacy_merge_approved') is False,
          'PHASE1_SECOND_TEN_UNSAFE_WINDOW_PROMOTION')
    ensure(all_cues==list(range(170,350)) and len(allclaims)==len(set(allclaims))==28
           and cnt_link==168 and cnt_nonclaim==12,
           'PHASE1_SECOND_TEN_CUE_CENSUS_NOT_COMPLETE')
    math=data.get('arithmetic_recheck',[])
    monthly=lambda x,n,r=.07/12:round(x*((1+r)**n-1)/r)
    ensure(type(math) is list and len(math)==7,
          'PHASE1_SECOND_TEN_MATH_ITEMS_MISSING')
    expected=[monthly(300000,84),monthly(300000,120),
              round(monthly(300000,120)*.06/12),monthly(400000,60),
              monthly(408000,60),140000,408000]
    actual=[math[0].get('future_value_krw'),math[1].get('future_value_krw'),
      math[2].get('monthly_krw'),math[3].get('future_value_krw'),
      math[4].get('future_value_krw'),math[5].get('monthly_krw'),
      math[6].get('new_annual_increase_effect_monthly_krw')]
    ensure(actual==expected and all(a.get('not_guaranteed') is True for a in math),
      'PHASE1_SECOND_TEN_MATH_OR_RISK_FLAGS_FAILED')
    ensure('7 years' in data.get('source_period_discrepancy_not_audio_confirmed','')
      and '10 years' in data['source_period_discrepancy_not_audio_confirmed'],
      'PHASE1_SECOND_TEN_FALSE_ASR_CORRECTION')
    status=data.get('private_actual_replay_status_summary')
    ensure(type(status) is list and len(status)==5
       and [x['video_id'] for x in status]==list(VIDEO_IDS)
       and [x['unresolved_cues'] for x in status]==[805,1283,751,729,1010]
       and [x['claims'] for x in status]==[104,72,41,36,42]
       and [x['windows_model_evidence_relation_reviewed'] for x in status]==[20,0,0,0,0]
       and [x['receipt_count'] for x in status]==[3,1,1,1,1]
       and all(x['sealed'] is False and x['approved_financial_facts']==0
               and x['claims']==x['evidence_cases_reviewed']==x['relation_cases_reviewed']
               for x in status),
       'PHASE1_SECOND_TEN_PRIVATE_STATUS_SHOULD_REMAIN_PROVISIONAL')
    private=False
    if original_zip is not None or private_root is not None:
        ensure(original_zip is not None and private_root is not None,
               'PHASE1_SECOND_TEN_PRIVATE_REPLAY_REQUIRES_BOTH_INPUTS')
        from .engine import ResearchRun
        original_zip=Path(original_zip);private_root=Path(private_root)
        ensure(hashlib.sha256(original_zip.read_bytes()).hexdigest()==ZIP_SHA,
               'PHASE1_SECOND_TEN_WRONG_ARCHIVE')
        with zipfile.ZipFile(original_zip) as z:
            for vid,s in zip(VIDEO_IDS,status):
                d=private_root/'videos'/vid;src=z.read(f'1-70/youtube-transcript-{vid}.srt')
                ensure((d/'private_source.srt').read_bytes()==src,
                       'PHASE1_SECOND_TEN_PRIVATE_SOURCE_DRIFT')
                model=json.loads((d/'source_manifest.json').read_text('utf-8'))
                run=ResearchRun(src,model,d);now=run.status()
                for k in ('video_id','claims','evidence_cases_reviewed','relation_cases_reviewed',
                          'unresolved_cues','windows_model_evidence_relation_reviewed',
                          'receipt_count','event_chain_head_sha256','sealed','approved_financial_facts'):
                    ensure(now[k]==s[k],'PHASE1_SECOND_TEN_REAL_ENGINE_REPLAY_MISMATCH_'+k)
                if vid==VIDEO_IDS[0]:
                    for row in rows:
                        m=run.model[row['window_id']]
                        ensure(m['cue_dispositions']==row['cue_dispositions']
                          and [(x['claim_id'],x['proposition']) for x in m['claims']]
                              ==[(x['claim_id'],x['paraphrase']) for x in row['claims']],
                              'PHASE1_SECOND_TEN_CLAIM_OR_CUE_NOT_MATCHING_ORIGINAL')
        private=True
    return {'schema':'IRE_V5_FIRST_FIVE_PHASE1_FIRST_TWENTY_CUES_V1',
        'manually_reviewed_windows_video1':20,
        'source_cues_reviewed_video1':349,
        'five_video_new_unresolved_cues_remaining':4578,
        'second_ten_cues_newly_dispositioned':171,
        'all_five_engine_model_evidence_relation_reviewed_windows':20,
        'private_original_zip_replayed_in_this_run':private,
        'financial_rule_or_personal_advice_release':'NO_GO'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--source-zip',type=Path)
    p.add_argument('--private-root',type=Path)
    a=p.parse_args()
    print(json.dumps(verify(a.root,original_zip=a.source_zip,private_root=a.private_root),ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
