"""Fail-closed 2026-11-06 original cue/case/finance review of #1 W00021..W00040.

Ordinary GitHub CI checks redacted source provenance, arithmetical examples,
immutable private chain fingerprints and no advice promotion. Private source
and all actual events are replayed only when both source ZIP and private-root
are provided explicitly; CI must not claim private replay from public hashes.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,re,zipfile
from pathlib import Path
from urllib.parse import urlparse
from .first_five_phase1_second_ten_gate import verify as verify_second
from .first_five_phase1_cue_gate import Phase1ReviewError,VIDEO_IDS,ZIP_SHA

BASE=Path('ire/v5/validation')
PATH=BASE/'first_five_phase1_video1_21_40_cue_review_20261106.json'
COMPACT=BASE/'v5_first_five_video_01_window_review_20261106.json'
PREVIOUS=BASE/'first_five_phase1_video1_11_20_cue_review_20261106.json'
NON={29:set(range(502,512)),30:{512,513}}
KNOWN_MISLINKED_IDS={'V5C0020','V5C0022','V5C0026','V5C0027','V5C0034'}
SOURCE_SHA='2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f'


def ensure(ok,reason):
    if not ok:raise Phase1ReviewError(reason)


def monthly_future_value(monthly:int,months:int,rate:float=.07/12)->int:
    return round(monthly*((1+rate)**months-1)/rate)


def verify(root:Path,replace:dict|None=None,source_zip:Path|None=None,
           private_root:Path|None=None)->dict:
    root=Path(root)
    prior=verify_second(root)
    data=replace if replace is not None else json.loads((root/PATH).read_text('utf-8'))
    old=json.loads((root/PREVIOUS).read_text('utf-8'))
    compact=json.loads((root/COMPACT).read_text('utf-8'))
    ensure(data.get('schema')=='IRE_V5_PHASE1_FIRST_FIVE_VIDEO1_W21_W40_SOURCE_CUE_GATE_V1'
           and data.get('as_of')=='2026-11-06'
           and data.get('original_zip_sha256')==ZIP_SHA
           and data.get('source_video_id')==VIDEO_IDS[0]
           and data.get('source_review')=='VIDEO_1_WINDOWS_21_TO_40_350_TO_709_INCLUSIVE',
           'THIRD_TWENTY_BAD_SOURCE_SCOPE')
    ensure(data.get('prior_video1_event_head_sha256')==old['private_actual_replay_status_summary'][0]['event_chain_head_sha256']
           and data.get('source_video_sha256')==SOURCE_SHA
           and data.get('previous_original_event_files_preserved') is True
           and re.fullmatch(r'[0-9a-f]{64}',data.get('new_video1_event_head_sha256','')) is not None
           and data.get('prior_video1_event_head_sha256')!=data['new_video1_event_head_sha256'],
           'THIRD_TWENTY_PRIOR_EVENT_HISTORY_MUST_SURVIVE')
    expected_values={
        'previous_20_reviewed_windows':20,'new_reviewed_windows':20,
        'current_total_reviewed_windows':40,'original_source_cues_in_this_batch':360,
        'previous_five_video_unresolved_cue_count':4578,
        'newly_dispositioned_unresolved_cues_in_this_batch':342,
        'current_five_video_unresolved_cue_count':4236,
        'new_event_count_added_to_video1':2,'current_video1_event_receipts':5,
        'video1_claim_count_after':123,'all_five_claim_count_after':314,
        'all_five_model_windows_created_in_private':288,
        'all_five_model_evidence_relation_reviewed_windows':40,
        'all_five_evidence_case_count':314,'all_five_relation_case_count':314,
        'public_control_plane_processed_windows_unchanged':5,
        'official_personal_finance_fact_approved':0}
    for key,value in expected_values.items():
        ensure(data.get(key)==value,'THIRD_TWENTY_PUBLIC_PROGRESS_DRIFT_'+key)
    ensure(data.get('retired_old_claim_ids')==[
        'V5C0019','V5C0020','V5C0021','V5C0022','V5C0025',
        'V5C0026','V5C0027','V5C0029','V5C0032','V5C0034',
        'V5C0035','V5C0037'] and
        data.get('private_original_zip_reopened_in_source_research') is True and
        data.get('source_archive_private_replayed_by_ci') is False and
        data.get('full_original_atomic_claim_recall_proven') is False and
        data.get('all_five_ResearchRun_CLOSURE_issued') is False and
        data.get('B04_legacy_merge_approved') is False and
        data.get('investment_advice_authorized') is False and
        data.get('release')=='SOURCE_CUE_FINANCE_SAFETY_REVIEW_ONLY_NO_GO',
        'THIRD_TWENTY_UNJUSTIFIED_CERTIFICATION')
    rows=data.get('original_window_reviews',[])
    index={w['window_id']:w for w in compact['records']}
    ensure(type(rows) is list and len(rows)==20,'THIRD_TWENTY_WINDOWS_MISSING')
    seen=set();cue_ids=[];claimids=[];linked_count=0;non_count=0
    for n,row in enumerate(rows,21):
        wid=f'W{n:05d}';origin=index[wid]
        ensure(row.get('window_id')==wid
              and row.get('video_id')==VIDEO_IDS[0]
              and row.get('first_cue')==origin['first_cue']
              and row.get('last_cue')==origin['last_cue']
              and row.get('window_sha256')==origin['primary_text_sha256']
              and row.get('full_external_fact_certified') is False
              and row.get('legacy_merge_approved') is False,
              'THIRD_TWENTY_SOURCE_WINDOW_OR_HASH_CHANGED')
        ids=list(range(row['first_cue'],row['last_cue']+1));cue_ids.extend(ids)
        claims=row.get('claims',[]); dispositions=row.get('cue_dispositions',[])
        ensure(type(claims) is list and len(claims)>0
               and type(dispositions) is list and len(dispositions)==len(ids),
               'THIRD_TWENTY_SOURCE_CUE_DISPOSITION_GAP')
        reverse={i:set() for i in ids}
        for c in claims:
            cid=c.get('claim_id')
            ensure(type(cid) is str and re.fullmatch(r'V5C\d{4}',cid) is not None
                   and cid not in seen and cid not in KNOWN_MISLINKED_IDS
                   and c.get('kind') in {'RULE','MATH','PERSONAL_CASE','QUESTION','OPINION','HYPOTHETICAL','RECOMMENDATION'}
                   and type(c.get('paraphrase')) is str and len(c['paraphrase'])>16
                   and c.get('financial_fact_approved') is False and c.get('automerge') is False
                   and c.get('legacy_relation_status')=='EXTENDS_SCOPE_PENDING'
                   and c.get('evidence_status') in {'OPEN_ASSUMPTION','OFFICIAL_CANDIDATE_APPLICABILITY_OPEN'}
                   and type(c.get('external_verification_required')) is bool
                   and type(c.get('rule_scope_token')) is str and len(c['rule_scope_token'])>4
                   and not set(c).intersection({'quote','source_refs','source_text','transcript','raw_srt'}),
                   'THIRD_TWENTY_CLAIM_UNANCHORED_OR_UNSAFE_APPROVAL')
            seen.add(cid);claimids.append(cid)
            legacy=c.get('legacy_claim_candidates',[])
            ensure(type(legacy) is list and all(isinstance(z,str) and re.fullmatch(r'GOMHEE-C\d{2,3}',z) for z in legacy),
                  'THIRD_TWENTY_LEGACY_CANDIDATE_BAD')
            urls=c.get('official_evidence_url_candidates',[])
            ensure(type(urls) is list and all(isinstance(u,str) and urlparse(u).scheme=='https'
                   and urlparse(u).netloc in {'www.law.go.kr','law.go.kr','www.nts.go.kr','nts.go.kr'} for u in urls),
                   'THIRD_TWENTY_UNTRUSTED_FINANCE_SOURCE')
            ensure((not urls) or c['evidence_status']=='OFFICIAL_CANDIDATE_APPLICABILITY_OPEN',
                   'THIRD_TWENTY_OFFICIAL_REFERENCE_IS_NOT_FACT_APPROVAL')
            these=c.get('cue_ids',[])
            ensure(type(these) is list and len(these)>0 and len(these)==len(set(these)),
                   'THIRD_TWENTY_NO_ATOMIC_CUES')
            for cue in these:
                ensure(type(cue) is int and cue in reverse and cid not in reverse[cue],
                       'THIRD_TWENTY_CLAIM_CUE_NOT_IN_OWN_WINDOW')
                reverse[cue].add(cid)
        for i,disp in zip(ids,dispositions):
            ensure(type(disp) is dict and disp.get('cue_index')==i
                   and type(disp.get('claim_ids')) is list
                   and set(disp['claim_ids'])==reverse[i],
                   'THIRD_TWENTY_DISPOSITION_REVERSE_CLAIM_MISMATCH')
            if reverse[i]:
                ensure(disp.get('status')=='LINKED' and i not in NON.get(n,set()),
                       'THIRD_TWENTY_MISLABELED_FINANCIAL_CUE')
                linked_count+=1
            else:
                ensure(disp.get('status')=='NONCLAIM' and i in NON.get(n,set())
                      and type(disp.get('reason')) is str and len(disp['reason'])>=18,
                       'THIRD_TWENTY_UNREVIEWED_SOURCE_SILENT_NONCLAIM')
                non_count+=1
        ensure({i for i in ids if not reverse[i]}==NON.get(n,set()),
               'THIRD_TWENTY_NONCLAIM_WHITELIST_REQUIRED')
    ensure(cue_ids==list(range(350,710)) and linked_count==348 and non_count==12
           and data.get('original_source_cues_dispositions')=={'LINKED':348,'NONCLAIM':12}
           and len(claimids)==len(set(claimids))==41,
           'THIRD_TWENTY_CUE_CENSUS_AND_CLAIMS_BAD')
    ensure(sorted(data.get('new_atomic_claim_ids',[]))==sorted(set(claimids)-{
       'V5C0018','V5C0023','V5C0240','V5C0241','V5C0024',
       'V5C0028','V5C0030','V5C0031','V5C0033','V5C0036'}),
       'THIRD_TWENTY_NEW_CLAIM_ID_OR_RETAINED_HISTORY_DRIFT')
    maths=data.get('financial_numeric_recheck',{})
    formulas={
      'pension_500k_monthly_20y_7pct_krw':monthly_future_value(500000,240),
      'irp_250k_monthly_20y_7pct_krw':monthly_future_value(250000,240),
      'non_deduct_750k_monthly_20y_7pct_krw':monthly_future_value(750000,240),
      'pension_500k_monthly_20y_principal_krw':500000*240,
      'irp_250k_monthly_20y_principal_krw':250000*240,
      'non_deduct_750k_monthly_20y_principal_krw':750000*240,
      'monthly_pension_1200000_annual_krw':1200000*12,
      'isa_100million_four_maturities_hypothetical_krw':100000000*4,
      'gross_10billion_15p4percent_after_tax_krw':round(10_000_000_000*(1-.154)),
      'gross_10billion_16p5percent_after_tax_krw':round(10_000_000_000*(1-.165)),
      'gross_10billion_15p4_vs_16p5_tax_gap_krw':round(10_000_000_000*(.165-.154)),
      'all_are_hypothetical_not_guaranteed':True}
    ensure(maths==formulas,'THIRD_TWENTY_INDEPENDENT_ARITHMETIC_MISMATCH')
    risk=data.get('critical_risk_flags',[])
    ensure(type(risk) is list and len(risk)>=7
           and any('16.5%' in s and '15.4%' in s for s in risk)
           and any('ISA' in s for s in risk)
           and any('1,500' in s for s in risk),
           'THIRD_TWENTY_CRITICAL_RISK_NOT_CARRIED_FORWARD')
    status=data.get('private_actual_replay_status_summary',[])
    ensure(type(status) is list and len(status)==5 and
           [r.get('video_id') for r in status]==list(VIDEO_IDS) and
           [r.get('claims') for r in status]==[123,72,41,36,42] and
           [r.get('unresolved_cues') for r in status]==[463,1283,751,729,1010] and
           [r.get('windows_model_evidence_relation_reviewed') for r in status]==[40,0,0,0,0] and
           [r.get('receipt_count') for r in status]==[5,1,1,1,1] and
           all(r.get('sealed') is False and r.get('approved_financial_facts')==0
               and r.get('claims')==r.get('evidence_cases_reviewed')==r.get('relation_cases_reviewed') for r in status),
           'THIRD_TWENTY_PRIVATE_RUN_NOT_FAITHFUL')
    ensure(status[0]['event_chain_head_sha256']==data['new_video1_event_head_sha256'],
           'THIRD_TWENTY_CHAIN_HEAD_MISMATCH')
    private=False
    if source_zip is not None or private_root is not None:
        ensure(source_zip is not None and private_root is not None,
               'THIRD_TWENTY_SOURCE_AND_PRIVATE_CHAIN_REQUIRED_TOGETHER')
        from .engine import ResearchRun
        source_zip=Path(source_zip);private_root=Path(private_root)
        ensure(hashlib.sha256(source_zip.read_bytes()).hexdigest()==ZIP_SHA,
               'THIRD_TWENTY_PRIVATE_SOURCE_ARCHIVE_SHA_CHANGED')
        with zipfile.ZipFile(source_zip) as z:
            for vid,record in zip(VIDEO_IDS,status):
                d=private_root/'videos'/vid
                raw=z.read(f'1-70/youtube-transcript-{vid}.srt')
                ensure(raw==(d/'private_source.srt').read_bytes(),
                      'THIRD_TWENTY_PRIVATE_ORIGINAL_SOURCE_CHANGED')
                m=json.loads((d/'source_manifest.json').read_text('utf-8'))
                run=ResearchRun(raw,m,d)
                actual=run.status()
                for k in ('source_sha256','claims','unresolved_cues','event_chain_head_sha256',
                          'evidence_cases_reviewed','relation_cases_reviewed',
                          'windows_model_evidence_relation_reviewed','receipt_count','sealed','approved_financial_facts'):
                    ensure(actual[k]==record[k],'THIRD_TWENTY_ACTUAL_ENGINE_REPLAY_MISMATCH_'+k)
                if vid==VIDEO_IDS[0]:
                    for row in rows:
                        model=run.model[row['window_id']]
                        ensure(model['cue_dispositions']==row['cue_dispositions']
                            and [(x['claim_id'],x['kind'],x['proposition']) for x in model['claims']]
                              ==[(x['claim_id'],x['kind'],x['paraphrase']) for x in row['claims']]
                            and all([x['cue_index'] for x in c['source_refs']]==r['cue_ids']
                                   for c,r in zip(model['claims'],row['claims'])),
                            'THIRD_TWENTY_SOURCE_MODEL_REF_MISMATCH')
                    event_files=sorted((d/'events').glob('*.json'))
                    ensure(len(event_files)==5
                           and json.loads(event_files[2].read_text())['event_sha256']
                             ==data['prior_video1_event_head_sha256'],
                           'THIRD_TWENTY_APPEND_ONLY_PRIOR_CHAIN_NOT_PRESERVED')
        private=True
    return {'schema':'IRE_V5_PHASE1_40_WINDOWS_SOURCE_CUE_VERDICT_V1',
      'source_video1_reviewed_windows':40,'newly_reviewed_source_cues':360,
      'newly_dispositioned_unresolved_cues':342,'five_video_unresolved_cues_remaining':4236,
      'private_model_evidence_relation_windows':40,'private_claims_reviewed':314,
      'original_source_replayed_in_this_execution':private,
      'financial_fact_approval_count':0,'full_five_video_research_closure':'BLOCKED',
      'public_control_plane_status_unchanged':5}


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('.'))
    parser.add_argument('--source-zip',type=Path)
    parser.add_argument('--private-root',type=Path)
    args=parser.parse_args()
    print(json.dumps(verify(args.root,source_zip=args.source_zip,private_root=args.private_root),ensure_ascii=False,sort_keys=True))

if __name__=='__main__':main()
