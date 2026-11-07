"""Public GitHub control-plane projection of 64-case focused V5 source audit.

Only hashed summary counters leave private model+SRT environment. Public status
is **not** independent government evidence or financial/semantic truth approval.
"""
from __future__ import annotations
import json,argparse
from pathlib import Path
from .worker import check,emit_state,SHA256,VIDEO,ID
SCHEMA='IRE_V5_64_PUBLIC_CHECKPOINT_V1'
REQ={'schema','job_id','video_id','source_sha256','original_event_head','incremental_event_head',
     'relation_event_head','focused_event_head','encrypted_archive_sha256','reviewed_total',
     'reviewed_boundary','reviewed_numeric','reviewed_official','boundary_context_reconstructed',
     'material_boundary_open','asr_boundary_open','numeric_audio_open','official_scope_open',
     'personal_cases_open','remaining_open','independently_approved_financial_facts',
     'personalized_advice_approved'}

def project(item):
    check(type(item) is dict and set(item)==REQ,'FOCUSED_PUBLIC_EXACT_FIELDS')
    check(item['schema']==SCHEMA and type(item['job_id']) is str and ID.fullmatch(item['job_id'])
          and type(item['video_id']) is str and VIDEO.fullmatch(item['video_id']), 'FOCUSED_PUBLIC_ID_INVALID')
    for k in ('source_sha256','original_event_head','incremental_event_head','relation_event_head',
              'focused_event_head','encrypted_archive_sha256'):
        check(type(item[k]) is str and SHA256.fullmatch(item[k]),'FOCUSED_PUBLIC_SHA_INVALID')
    for k in ('reviewed_total','reviewed_boundary','reviewed_numeric','reviewed_official',
              'boundary_context_reconstructed','material_boundary_open','asr_boundary_open',
              'numeric_audio_open','official_scope_open','personal_cases_open','remaining_open'):
        check(type(item[k]) is int and item[k]>=0,'FOCUSED_PUBLIC_COUNT_INVALID')
    check(item['reviewed_total']==64 and item['reviewed_boundary']==35 and
          item['reviewed_numeric']==8 and item['reviewed_official']==21 and
          item['boundary_context_reconstructed']+item['material_boundary_open']+
          item['asr_boundary_open']==35 and item['numeric_audio_open']==8 and
          item['official_scope_open']==21 and item['personal_cases_open']==48 and
          item['remaining_open']==112-item['boundary_context_reconstructed'],
          'FOCUSED_PUBLIC_COUNTERS_INCONSISTENT')
    check(item['independently_approved_financial_facts']==0 and
          item['personalized_advice_approved'] is False,'FOCUSED_PUBLIC_FALSE_APPROVAL')
    return {'schema':'IRE_V5_64_PUBLIC_STATUS_V1',
            'video_id':item['video_id'],'job_id':item['job_id'],
            'source_sha256_reported':item['source_sha256'],
            'four_ledger_heads_reported':{k:item[k] for k in ('original_event_head','incremental_event_head',
                                       'relation_event_head','focused_event_head')},
            'encrypted_archive_sha256_reported':item['encrypted_archive_sha256'],
            'risks_reviewed_reported':64,'boundary_context_reconstructed_limited_reported':item['boundary_context_reconstructed'],
            'boundary_material_open_reported':item['material_boundary_open'],
            'boundary_asr_open_reported':item['asr_boundary_open'],
            'numeric_audio_open_reported':item['numeric_audio_open'],
            'official_applicability_open_reported':item['official_scope_open'],
            'personal_scenarios_open_reported':item['personal_cases_open'],
            'remaining_risks_reported':item['remaining_open'],
            'private_source_verified_by_github':False,
            'financial_facts_independently_approved':0,'investment_advice_approved':False,
            'release_verdict':'NO_GO','next_action':'INDEPENDENT_ASR_LEGAL_AND_PERSONAL_APPLICABILITY_AUDIT'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--requests',required=True);p.add_argument('--states',required=True)
    args=p.parse_args();root=Path(args.requests);out=Path(args.states)
    check(root.is_dir() and not root.is_symlink(),'FOCUSED_PUBLIC_REQUEST_FOLDER')
    count=0
    for job in sorted(root.iterdir()):
        check(job.is_dir() and not job.is_symlink() and ID.fullmatch(job.name),'FOCUSED_PUBLIC_BAD_JOB')
        ls=sorted(job.iterdir());check(len(ls)==1 and ls[0].name=='000001.json' and ls[0].stat().st_size<12000
                                   and not ls[0].is_symlink(),'FOCUSED_PUBLIC_FILES_INVALID')
        data=json.loads(ls[0].read_text('utf-8'));check(data.get('job_id')==job.name,'FOCUSED_PUBLIC_WRONG_JOB')
        state=project(data);emit_state(out/(job.name+'.json'),state)
        print(json.dumps({'job_id':job.name,'remaining_risks_reported':state['remaining_risks_reported'],
                          'full_financial_approval':False},sort_keys=True))
        count+=1
    check(count>0,'FOCUSED_PUBLIC_NO_REQUESTS')
    return 0
if __name__=='__main__':raise SystemExit(main())
