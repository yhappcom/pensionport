"""GitHub-side public risk-counter projection, not an official audit attestation.

GitHub never needs the private original SRT, captured government excerpts,
model judgments, encrypted backup secret or personal financial information.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from .worker import check,ControlError,emit_state,ID,VIDEO,SHA256

SCHEMA='IRE_V5_APP_INCREMENTAL_PUBLIC_REPORT_V1'
KEYS={"schema","job_id","video_id","source_sha256","source_event_head_sha256",
      "audit_event_head_sha256","encrypted_checkpoint_sha256",
      "issues_total","issues_reviewed","issues_unresolved","issue_counts",
      "reviewed_counts","official_document_candidates","official_candidate_links",
      "independently_approved_financial_facts","personal_investment_advice_approved"}
KINDS={"B","E","N","R"}


def project_public_report(item:dict)->dict:
    check(type(item) is dict and set(item)==KEYS,'AUDIT_PUBLIC_EXACT_FIELDS_REQUIRED')
    check(item.get('schema')==SCHEMA and type(item.get('job_id')) is str and
          ID.fullmatch(item['job_id']) is not None and type(item.get('video_id')) is str and
          VIDEO.fullmatch(item['video_id']) is not None,'AUDIT_PUBLIC_ID_INVALID')
    for k in ('source_sha256','source_event_head_sha256','audit_event_head_sha256',
              'encrypted_checkpoint_sha256'):
        check(type(item.get(k)) is str and SHA256.fullmatch(item[k]) is not None,
              'AUDIT_PUBLIC_DIGEST_MISSING')
    for k in ('issues_total','issues_reviewed','issues_unresolved',
              'official_document_candidates','official_candidate_links'):
        check(type(item.get(k)) is int and item[k]>=0,'AUDIT_PUBLIC_COUNT_INVALID')
    check(type(item.get('issue_counts')) is dict and
          type(item.get('reviewed_counts')) is dict and
          set(item['issue_counts'])==KINDS and
          set(item['reviewed_counts'])==KINDS,
          'AUDIT_PUBLIC_KINDS_INVALID')
    for k in KINDS:
        v,done=item['issue_counts'][k],item['reviewed_counts'][k]
        check(type(v) is int and type(done) is int and 0<=done<=v,
              'AUDIT_PUBLIC_REVIEW_COUNT_INVALID')
    check(item['issues_total']==sum(item['issue_counts'].values()) and
          item['issues_reviewed']==sum(item['reviewed_counts'].values()) and
          0<=item['issues_unresolved']<=item['issues_reviewed'] and
          item['official_candidate_links']<=item['issues_reviewed'],
          'AUDIT_PUBLIC_TOTAL_INCONSISTENT')
    check(item.get('independently_approved_financial_facts')==0 and
          item.get('personal_investment_advice_approved') is False,
          'AUDIT_PUBLIC_FALSE_TRUTH_PROMOTION')
    pending=item['issues_total']-item['issues_reviewed']
    return {'schema':'IRE_V5_APP_INCREMENTAL_PUBLIC_STATUS_V1',
        'job_id':item['job_id'],'video_id':item['video_id'],
        'source_sha256_reported':item['source_sha256'],
        'source_event_head_sha256_reported':item['source_event_head_sha256'],
        'audit_event_head_sha256_reported':item['audit_event_head_sha256'],
        'encrypted_checkpoint_sha256_reported':item['encrypted_checkpoint_sha256'],
        'risk_cases_total_reported':item['issues_total'],
        'risk_cases_screened_reported':item['issues_reviewed'],
        'risk_cases_not_screened_reported':pending,
        'risk_cases_still_open_reported':item['issues_unresolved'],
        'risk_issue_counts_reported':item['issue_counts'],
        'risk_screened_by_type_reported':item['reviewed_counts'],
        'shared_official_documents_reported':item['official_document_candidates'],
        'claim_source_links_reported':item['official_candidate_links'],
        'next_action':('CHATGPT_SCREEN_OPEN_RISKS' if pending else
                       'INDEPENDENT_FINANCIAL_AND_SOURCE_SCOPE_REVIEW_REQUIRED'),
        'private_risk_cases_available_to_github':False,
        'public_counters_independently_attested':False,
        'official_financial_facts_approved':False,
        'investment_advice_approved':False,
        'one_turn_four_five_video_complete':False,
        'final_release_verdict':'NO_GO'}


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--requests',required=True)
    p.add_argument('--states',required=True)
    opt=p.parse_args()
    inp=Path(opt.requests);out=Path(opt.states)
    check(inp.is_dir() and not inp.is_symlink(),'AUDIT_PUBLIC_REQUEST_ROOT_MISSING')
    checked=0
    for folder in sorted(inp.iterdir()):
        check(folder.is_dir() and not folder.is_symlink() and ID.fullmatch(folder.name) is not None,
              'AUDIT_PUBLIC_BAD_JOB_DIR')
        files=sorted(folder.iterdir())
        check(len(files)==1 and files[0].name=='000001.json' and not files[0].is_symlink() and
              files[0].stat().st_size<=12000,'AUDIT_PUBLIC_REQUEST_FILE_INVALID')
        data=json.loads(files[0].read_text('utf-8'))
        check(data.get('job_id')==folder.name,'AUDIT_PUBLIC_JOB_MISMATCH')
        state=project_public_report(data)
        emit_state(out/(folder.name+'.json'),state)
        print(json.dumps({'job_id':folder.name,'risk_pending':state['risk_cases_not_screened_reported'],
                          'open_remaining':state['risk_cases_still_open_reported'],
                          'no_financial_approval':True},sort_keys=True))
        checked+=1
    check(checked>0,'AUDIT_PUBLIC_NO_JOB')
    return 0

if __name__=='__main__':raise SystemExit(main())
