"""Fail-closed IRE V5 first ten original-window cue adjudication audit.

Public CI checks only frozen redacted scope/metadata.  A private replay path
with the original ZIP and actual append-only event directory must be supplied
for byte-for-byte source and V5 ResearchRun verification. Neither grants any
financial-rule truth approval or final research closure.
"""
from __future__ import annotations
import argparse, hashlib, json, re, zipfile
from collections import Counter
from pathlib import Path

P=Path('ire/v5/validation')
F=P/'first_five_phase1_video1_10_windows_cue_review_20261106.json'
OLD=P/'v5_first_five_video_01_window_review_20261106.json'
ZIP_SHA='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
VIDEO_IDS=('sz5N9WJS310','6VEfKF7BzZU','OiDTNstaSpM','aNfGrcO6WPI','qtluAViPpsQ')
NONCLAIM={2:set(range(8,22)),5:{74},7:{113},9:{146,147}}
RETIRING={'V5C0003','V5C0005','V5C0007'}
class Phase1ReviewError(ValueError):pass

def check(ok,label):
    if not ok:raise Phase1ReviewError(label)

def verify(root:Path, override:dict|None=None, original_zip:Path|None=None,
           private_root:Path|None=None)->dict:
    root=Path(root)
    data=override if override is not None else json.loads((root/F).read_text('utf-8'))
    prior=json.loads((root/OLD).read_text('utf-8'))
    check(data.get('schema')=='IRE_V5_FIRST_FIVE_PHASE1_ORIGINAL_CUE_ADJUDICATION_V1'
      and data.get('date')=='2026-11-06'
      and data.get('original_zip_sha256')==ZIP_SHA
      and data.get('review_scope')=='ONLY_VIDEO_1_WINDOWS_1_TO_10_169_CUES'
      and data.get('public_redaction')=='NO_ORIGINAL_SRT_TEXT_NO_QUOTED_CUES_NO_PRIVATE_EVENT_PAYLOAD',
      'PHASE1_SOURCE_SCOPE_INVALID')
    check(data.get('manually_source_read_cues_in_this_batch')==169
      and data.get('reviewed_windows_in_this_batch')==10
      and data.get('previous_unresolved_cue_count_across_five_videos')==4908
      and data.get('updated_unresolved_cue_count_across_five_videos')==4749
      and data.get('unresolved_cues_closed_in_this_batch')==159
      and data.get('formal_model_evidence_relation_reviewed_windows_across_five_videos')==10
      and data.get('initial_private_v5_model_windows')==288
      and data.get('claim_scope_reviewed_in_video1_first_ten')==28,
      'PHASE1_CUE_TOTAL_OR_REVIEW_COUNT_MISMATCH')
    check(data.get('formal_five_video_research_closures_issued')==0
      and data.get('independently_verified_financial_facts_approved')==0
      and data.get('personal_portfolio_actions_approved')==0
      and data.get('prior_68_focused_claims_atomically_completed') is False
      and data.get('no_universal_recall_proven') is True
      and data.get('public_batch_processed_count_unchanged')==5
      and data.get('B04_legacy_merge_approved') is False
      and data.get('finance_education_full_release_go') is False
      and data.get('no_prior_claim_id_reassigned_to_different_meaning') is True,
      'PHASE1_FALSE_RESEARCH_OR_ADVISORY_APPROVAL')
    check(set(data.get('prior_claim_ids_retired_after_proposition_alignment',[]))==RETIRING,
      'PHASE1_PRIOR_CLAIM_ID_RETIREMENT_OMITTED')
    rows=data.get('source_window_reviews')
    check(type(rows) is list and len(rows)==10,'PHASE1_NOT_TEN_WINDOWS')
    old={r['window_id']:r for r in prior.get('records',[])}
    all_cues=[];all_claims=[];statuses=Counter()
    for j,row in enumerate(rows,1):
        wid=f'W{j:05d}';prior_row=old[wid]
        check(row.get('window_id')==wid and row.get('video_number')==1
              and row.get('video_id')==VIDEO_IDS[0]
              and row.get('first_cue')==prior_row['first_cue']
              and row.get('last_cue')==prior_row['last_cue']
              and row.get('window_sha256')==prior_row['primary_text_sha256'],
              'PHASE1_SOURCE_WINDOW_HASH_BOUNDARY_BAD')
        ids=list(range(row['first_cue'],row['last_cue']+1))
        all_cues.extend(ids)
        cs=row.get('claims');disp=row.get('cue_dispositions')
        check(type(cs) is list and type(disp) is list and len(disp)==len(ids),
              'PHASE1_CLAIM_OR_CUE_CENSUS_MISSING')
        linked={i:set() for i in ids}
        local=set()
        for c in cs:
            cid=c.get('claim_id')
            check(type(cid) is str and re.fullmatch(r'V5C\d{4}',cid) is not None
                  and cid not in local and cid not in RETIRING
                  and c.get('kind') in {'QUESTION','PERSONAL_CASE','RULE','HYPOTHETICAL','OPINION','RECOMMENDATION','MATH'}
                  and type(c.get('paraphrase')) is str and len(c['paraphrase'])>=8
                  and c.get('financial_fact_approved') is False
                  and type(c.get('cue_ids')) is list and bool(c['cue_ids']),
                  'PHASE1_CLAIM_HALO_OR_RETIRED_ID')
            local.add(cid);all_claims.append(cid)
            for cue in c['cue_ids']:
                check(type(cue) is int and cue in linked and cid not in linked[cue],
                      'PHASE1_INVALID_CLAIM_SOURCE_LINK')
                linked[cue].add(cid)
        for i,entry in zip(ids,disp):
            check(type(entry) is dict and entry.get('cue_index')==i
               and type(entry.get('claim_ids')) is list
               and set(entry['claim_ids'])==linked[i],
               'PHASE1_CUE_REVERSE_LINK_OR_ORDER')
            expected='LINKED' if linked[i] else 'NONCLAIM'
            check(entry.get('status')==expected,
               'PHASE1_NONCLAIM_UNREVIEWED_OR_LINKED_CUE')
            if expected=='NONCLAIM':
                check(i in NONCLAIM.get(j,set())
                  and type(entry.get('reason')) is str and len(entry['reason'])>=15,
                  'PHASE1_NONCLAIM_OUTSIDE_MANUAL_ADJUDICATION')
            else:
                check(i not in NONCLAIM.get(j,set()),'PHASE1_CUE_SOURCE_LINK_ON_NONCLAIM')
            statuses[expected]+=1
        check({i for i in ids if not linked[i]}==NONCLAIM.get(j,set()),
              'PHASE1_MANUAL_NONCLAIM_MAP_CHANGED')
        check(row.get('full_external_fact_certified') is False
          and row.get('B04_legacy_merge_approved') is False,
          'PHASE1_WINDOW_FALSE_FINANCIAL_PROMOTION')
        # No original speech or cue quote text is allowed in a public payload.
        check(all(not set(c).intersection({'source_refs','quote','source_text','raw_cues'})
                  for c in cs), 'PHASE1_PRIVATE_CUE_TEXT_LEAK')
    check(all_cues==list(range(1,170)) and len(all_claims)==len(set(all_claims))==28
      and statuses=={'LINKED':151,'NONCLAIM':18},
      'PHASE1_WINDOW_CUE_OR_CLAIM_RECALL_BAD')
    calc=data.get('arithmetic_rechecked',[])
    check(type(calc) is list and len(calc)==5,'PHASE1_MATH_CHECK_MISSING')
    expected=[round(18_000_000*(1.07**12)),200000,233333,266667,72]
    actual=[calc[0].get('amount_krw'),calc[1].get('amount_krw_month'),
            calc[2].get('amount_krw_month'),calc[3].get('amount_krw_month'),
            calc[4].get('simple_months')]
    check(actual==expected and all(x.get('not_guaranteed') is True for x in calc[:4])
      and calc[4].get('excludes_tax_discount_survival') is True,
      'PHASE1_MATH_OR_RISK_NOTE_INVALID')
    recorded=data.get('per_video_replayed_private_status',[])
    check(len(recorded)==5 and [v['video_id'] for v in recorded]==list(VIDEO_IDS),
          'PHASE1_PRIVATE_RUN_STATUS_MISSING')
    check([v['unresolved_cues'] for v in recorded]==[976,1283,751,729,1010]
       and [v['claims'] for v in recorded]==[85,72,41,36,42]
       and [v['evidence_cases_reviewed'] for v in recorded]==[85,72,41,36,42]
       and [v['relation_cases_reviewed'] for v in recorded]==[85,72,41,36,42]
       and [v['windows_model_evidence_relation_reviewed'] for v in recorded]==[10,0,0,0,0]
       and [v['receipt_count'] for v in recorded]==[2,1,1,1,1]
       and all(v.get('sealed') is False and v.get('approved_financial_facts')==0 for v in recorded),
       'PHASE1_PRIVATE_EVENT_HISTORY_INCONSISTENT')
    private_verified=False
    if original_zip is not None or private_root is not None:
        check(original_zip is not None and private_root is not None,
              'PHASE1_PRIVATE_REPLAY_NEEDS_SOURCE_AND_CHAIN')
        from .engine import ResearchRun
        original_zip=Path(original_zip);private_root=Path(private_root)
        check(hashlib.sha256(original_zip.read_bytes()).hexdigest()==ZIP_SHA,
              'PHASE1_WRONG_PRIVATE_ZIP')
        with zipfile.ZipFile(original_zip) as z:
            for vid,rec in zip(VIDEO_IDS,recorded):
                d=private_root/'videos'/vid
                source=z.read(f'1-70/youtube-transcript-{vid}.srt')
                check((d/'private_source.srt').read_bytes()==source,
                      'PHASE1_PRIVATE_SOURCE_BYTES_DRIFT')
                model=json.loads((d/'source_manifest.json').read_text('utf-8'))
                r=ResearchRun(source,model,d)
                status=r.status()
                for k in ('video_id','submitted_windows','claims','evidence_cases_reviewed',
                          'relation_cases_reviewed','unresolved_cues',
                          'windows_model_evidence_relation_reviewed','receipt_count',
                          'event_chain_head_sha256','sealed','approved_financial_facts'):
                    check(status[k]==rec[k], 'PHASE1_REPLAY_DISAGREES_'+k)
                if vid==VIDEO_IDS[0]:
                    for pub in rows:
                        m=r.model[pub['window_id']]
                        check(m['cue_dispositions']==pub['cue_dispositions'],
                              'PHASE1_PRIVATE_CUE_DECISION_NOT_REPLAYABLE')
                        check([(c['claim_id'],c['proposition']) for c in m['claims']]
                           ==[(c['claim_id'],c['paraphrase']) for c in pub['claims']],
                              'PHASE1_PRIVATE_CLAIM_TEXT_MISMATCH')
        private_verified=True
    return {'schema':'IRE_V5_FIRST_FIVE_PHASE1_GATE_V1',
       'original_video1_windows_source_reviewed':10,
       'original_video1_cues_dispositioned':169,
       'new_nonfinancial_reaction_cues_explicitly_adjudicated':18,
       'previously_unresolved_cues_newly_dispositioned':159,
       'all_five_video_unresolved_cues_remaining':4749,
       'actual_v5_original_source_private_replayed_this_run':private_verified,
       'actual_v5_private_model_evidence_relation_windows':10,
       'all_five_video_formal_research_closures':0,
       'original_68_unmapped_focused_claims_still_open':True,
       'financial_advisory_release':'NO_GO'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--source-zip',type=Path)
    p.add_argument('--private-root',type=Path)
    a=p.parse_args()
    print(json.dumps(verify(a.root,original_zip=a.source_zip,private_root=a.private_root),ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
