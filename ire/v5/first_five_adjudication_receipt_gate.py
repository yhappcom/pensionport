"""V5 source-authored classification/equivalence milestone, NOT a research closure.

ChatGPT-authored SRT interpretations cannot substitute for IRE_V5_EVENT_V1
MODEL_ANALYSIS+EVIDENCE_REVIEW+PRIOR_RELATION_REVIEW event-chain receipts.
An optional *private* original archive rechecks exactly thirteen challenged
source windows and twenty-one mapped cue anchors. Never writes original text.
"""
from __future__ import annotations
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse
import zipfile

P=Path('ire/v5/validation')
OLD=P/'first_five_remnant_omission_challenges_20261106.json'
A=P/'first_five_13_omission_adjudication_20261106.json'
E=P/'first_five_305_claim_equivalence_20261106.json'
L=P/'first_five_13_official_scope_20261106.json'
R=P/'first_five_rule_applicability_41_20261106.json'
NEW=P/'first_five_remnant_221_source_claim_candidates_20261106.json'
PREV=P/'first_five_atomic_20261106.json'
CLUSTERS=P/'first_five_remnant_duplicate_conflict_register_20261106.json'
BATCH=Path('ire/v5_app/batch_states/v5-gomhee-001-005-batch.json')
IDS=('sz5N9WJS310','6VEfKF7BzZU','OiDTNstaSpM','aNfGrcO6WPI','qtluAViPpsQ')
RAW_ZIP='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
SAFE_TYPES={'QUESTION_WITH_PERSONAL_NUMERIC_PREMISE','QUESTION_WITH_TAX_RULE_PREMISE',
 'QUESTION_AND_CONDITIONAL_ISA_CONTRACT_PREMISE','HISTORICAL_MARKET_MECHANISM_DESCRIPTION',
 'FINANCIAL_ECONOMIC_EXPLANATION_NOT_NONFINANCIAL','HISTORICAL_RETROSPECTIVE_WITH_CAUSAL_HALO',
 'EMPLOYER_BANK_CONTRACT_BARGAINING_HYPOTHESIS','RETIREMENT_OPINION_WITH_CONDITIONS',
 'UNVERIFIED_EMPIRICAL_CYCLE_GENERALIZATION','PERSONAL_RECOVERY_ANECDOTE_NOT_FORECAST',
 'HISTORICAL_CORPORATE_ACTION_WITH_VERIFIED_SUBCLAIMS',
 'HISTORICAL_DEFENSE_ACQUISITION_WITH_UNVERIFIED_MOTIVE',
 'PUBLIC_EMPLOYMENT_SIGNAL_WITH_INSIDER_INFO_GUARD'}
KNOWN_FALSE={'DIVIDEND_NEW_MONEY':{'FV5-A050','FV5-A051'},
             'EMPLOYER_SECTOR_RISK':{'FV5-A062'},
             'SOCIAL_BEGINNER_SAVE':{'FV5-A061'}}

class ResearchReceiptBlocked(ValueError):pass

def check(ok:bool,reason:str)->None:
    if not ok:raise ResearchReceiptBlocked(reason)

def load(root:Path,path:Path)->dict:
    x=json.loads((root/path).read_text('utf-8'))
    check(type(x) is dict,'RECEIPT_JSON_NOT_OBJECT')
    return x

def digest(x)->str:
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,
          separators=(',',':')).encode('utf8')).hexdigest()

def _bytes_private_source(source_zip:Path,cases:list[dict])->dict:
    check(source_zip.exists() and hashlib.sha256(source_zip.read_bytes()).hexdigest()==RAW_ZIP,
          'RECEIPT_PRIVATE_ARCHIVE_SHA_MISMATCH')
    from .first_five_window_review_gate import source_windows
    out={}
    with zipfile.ZipFile(source_zip) as z:
        for n,vid in enumerate(IDS,1):
            filename=f'1-70/youtube-transcript-{vid}.srt'
            check(filename in z.namelist(),'RECEIPT_SOURCE_ORIGINAL_VIDEO_MISSING')
            raw=z.read(filename)
            planned=source_windows(raw)
            lines=raw.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n').strip()
            cues={}
            for block in re.split(r'\n\s*\n',lines):
                row=block.splitlines()
                check(len(row)>=3 and row[0].strip().isdigit(),
                      'RECEIPT_BAD_ORIGINAL_CUE')
                cue_id=int(row[0].strip())
                check(cue_id==len(cues)+1,'RECEIPT_BAD_CUE_ORDER')
                cues[cue_id]=' '.join(s.strip() for s in row[2:] if s.strip())
            selected=[q for q in cases if q['video_number']==n]
            for q in selected:
                wid=int(q['window_id'][1:])
                check(1<=wid<=len(planned),'RECEIPT_WINDOW_OUT_OF_RANGE')
                w=planned[wid-1]
                check(w['primary_text_sha256']==q['source_window_sha256'] and
                 w['first_cue']==q['first_cue'] and w['last_cue']==q['last_cue'],
                 'RECEIPT_ORIGINAL_WINDOW_DIGEST_MISMATCH')
                for atom in q['propositions']:
                    i=atom['anchor_cue']
                    check(hashlib.sha256(cues[i].encode('utf-8')).hexdigest()==
                     atom['anchor_cue_sha256'],'RECEIPT_ORIGINAL_ANCHOR_TAMPERED')
                out[q['case_id']]=len(q['propositions'])
    check(len(out)==13 and sum(out.values())==21,'RECEIPT_ORIGINAL_NOT_13_21')
    return {'verified_windows':len(out),'verified_cue_anchors':sum(out.values()),
            'private_original_reopened':True}

def verify(root:Path, source_zip:Path|None=None, replacements:dict|None=None)->dict:
    root=Path(root)
    docs={p:load(root,p) for p in (OLD,A,E,L,R,NEW,PREV,CLUSTERS,BATCH)}
    for key,x in (replacements or {}).items():
        check(key in [str(k) for k in docs],'RECEIPT_UNKNOWN_REPLACEMENT')
        docs[Path(key)]=x
    old=docs[OLD]; a=docs[A];e=docs[E]; law=docs[L];rules=docs[R]
    new=docs[NEW];prev=docs[PREV]; cl=docs[CLUSTERS]; batch=docs[BATCH]
    check(old['schema']=='IRE_V5_FIRST_FIVE_SECOND_PASS_OMISSION_CHALLENGE_V1'
         and old['flagged_records']==13 and len(old['rows'])==13,
         'RECEIPT_ORIGINAL_CHALLENGE_CHANGED')
    check(a.get('schema')=='IRE_V5_FIRST_FIVE_13_OMISSION_ADJUDICATION_V1'
          and a.get('source_zip_sha256')==RAW_ZIP and a.get('prior_challenge_rows')==13
          and a.get('classification_closed_count')==13
          and a.get('formal_engine_events_created_from_this_public_ledger')==0
          and a.get('knowledge_auto_merge_approved') is False
          and a.get('independent_100pct_full_288_atomic_recall_established') is False
          and a.get('personalized_investment_decision_approved') is False,
          'RECEIPT_FORCED_FORMAL_OR_ADVICE_APPROVAL')
    known={(z['video_number'],z['window_id']):z for z in old['rows']}
    check(len(known)==13 and len(a['cases'])==13,
          'RECEIPT_CHALLENGE_OMITTED')
    passed=set(); proposition_ids=set();count=0
    for i,c in enumerate(a['cases'],1):
        key=c.get('video_number'),c.get('window_id')
        check(c.get('case_id')==f'FV5-O{i:02d}' and key in known
              and key not in passed and c.get('video_id')==IDS[c['video_number']-1],
              'RECEIPT_UNMATCHED_CHALLENGE')
        passed.add(key)
        previous=known[key]
        check(c['source_window_sha256']==previous['source_window_sha256']
              and c['prior_classification']==previous['prior_meaning_type']
              and c['challenge_code']==previous['challenge_code']
              and c['resolved_classification'] in SAFE_TYPES
              and c['classification_closed'] is True
              and c['source_semantic_review_completed'] is True
              and c['formal_ire_model_evidence_relation_event_migrated'] is False
              and c['financial_fact_personal_application_approved'] is False
              and c['incomplete_atomic_recall_for_full_corpus'] is True
              and c['video_audio_transcribed_independently'] is False
              and len(c['bounded_interpretation'])>=25
              and len(c['mandatory_limit'])>=30,
              'RECEIPT_UNEARNED_CLAIM_OR_SOURCE_STATUS')
        atoms=c['propositions']
        check(type(atoms) is list and c['adjudicated_proposition_count']==len(atoms)
               and 1<=len(atoms)<=3,'RECEIPT_NO_BOUNDED_ATOM')
        for j,z in enumerate(atoms,1):
            ident=z.get('id'); idx=z.get('anchor_cue')
            check(ident==f'FV5-O{i:02d}-{j:02d}'
             and ident not in proposition_ids and type(idx) is int
             and c['first_cue']<=idx<=c['last_cue']
             and bool(re.fullmatch('[0-9a-f]{64}',z.get('anchor_cue_sha256','')))
             and len(z.get('interpretation',''))>=14
             and z.get('current_personal_application_approved') is False
             and z.get('claim_truth_is_not_equivalent_to_source_quote') is True,
             'RECEIPT_ANCHOR_MISSING_OR_CLAIM_PROMOTED')
            proposition_ids.add(ident);count+=1
    check(passed==set(known) and count==21,
          'RECEIPT_13_CASES_NOT_EXHAUSTED')
    check(law.get('schema')=='IRE_V5_13_CASE_NARROW_AUTHORITY_SCOPE_V1'
      and law.get('source_scope_is_not_individualized_application') is True
      and law.get('all_other_221_and_68_financial_rule_claims_certified') is False
      and law.get('all_authority_uris_live_rechecked_in_ci') is False,
      'RECEIPT_ALL_LAW_FALSIFIED')
    authorities={}
    for x in law['authority_records']:
        id=x['id'];url=urlparse(x['url'])
        check(id not in authorities and url.scheme=='https'
          and url.hostname in {'www.nps.or.kr','m.nps.or.kr','nts.go.kr','www.nts.go.kr',
          'www.knbank.co.kr','www.moel.go.kr','www.kbfg.com','www.fsc.go.kr',
          'www.hanwha.com','law.go.kr','regulation.krx.co.kr'}
          and x['source_html_full_snapshot_archived'] is False
          and x['live_recheck_in_github_ci'] is False
          and x['personal_eligibility_verified'] is False
          and x['licenses_auto_advice'] is False,
          'RECEIPT_BAD_OFFICIAL_SOURCE_STATUS')
        authorities[id]=x
    check(len(authorities)==13 and all(ref in authorities for c in a['cases']
              for ref in c['official_reference_ids']),
          'RECEIPT_MISSING_OFFICIAL_SCOPE')
    check(e.get('schema')=='IRE_V5_305_CANDIDATE_SCOPE_EQUIVALENCE_ADJUDICATION_V1'
          and e['prior_candidate_count']==68 and e['new_candidate_count']==237
          and e['unique_candidate_count']==305 and e['cluster_count']==22
          and e['strict_proposition_level_equivalences_proven']==0
          and e['source_claims_deleted']==0
          and e['B04_formal_merge_approved'] is False
          and e['original_116_core_claims_changed'] is False
          and e['certified_full_atomic_recall'] is False,
          'RECEIPT_UNEARNED_EQUIVALENCE_OR_MERGE')
    catalog={c['id'] for c in prev['rows']}|{c['id'] for c in new['candidate_assertions']}
    check(len(catalog)==305 and len(e['candidate_dispositions'])==305,
          'RECEIPT_305_CANDIDATES_UNACCOUNTED_FOR')
    memberships=collections.defaultdict(list)
    groups={}
    for g in cl['potential_topic_overlap_groups']:
        groups[g['cluster_id']]=(set(g['prior_68_candidate_ids']),set(g['new_candidate_claim_ids']))
    check(len(groups)==22,'RECEIPT_PRIOR_CLUSTER_CHANGED')
    for x in e['clusters']:
        ident=x['cluster_id']
        check(ident in groups and len(x['manual_scope_rationale'])>30
             and x['proposition_level_identity_certified'] is False
             and x['new_financial_rule_approved'] is False
             and x['canonical_scope_does_not_override_historical_source'] is True
             and (set(x['related_prior_source_ids']),set(x['new_source_ids']))==groups[ident],
             'RECEIPT_CLUSTER_HALO_OR_UNSAFE_PROMOTION')
        for cid in x['new_source_ids']+x['related_prior_source_ids']:
            memberships[cid].append(ident)
    check(len(e['clusters'])==22,'RECEIPT_MISSING_CLUSTER')
    seen=set()
    for x in e['candidate_dispositions']:
        id=x['candidate_id']
        check(id in catalog and id not in seen
         and x['atomic_statement_equivalence_certified'] is False
         and x['source_record_deleted'] is False
         and x['financial_advice_approved'] is False
         and set(x['considered_clusters'])==set(memberships[id]),
         'RECEIPT_INVALID_CANDIDATE_DISPOSITION')
        seen.add(id)
    check(seen==catalog,'RECEIPT_NOT_ALL_CANDIDATES_ADJUDICATED')
    desired={(n,o,k) for k,(os,ns) in groups.items() for n in ns for o in os}
    actual=set();false=0
    for x in e['pair_edges']:
        t=(x['new_candidate_id'],x['previous_candidate_id'],x['cluster_id'])
        check(t in desired and t not in actual
         and x['same_atomic_claim_certified'] is False
         and x['can_delete_source_record'] is False
         and x['can_automerge_legacy'] is False,
         'RECEIPT_FALSE_DUPLICATE_CERTIFICATION')
        actual.add(t)
        flag=x['cluster_id'] in KNOWN_FALSE and x['previous_candidate_id'] in KNOWN_FALSE[x['cluster_id']]
        check(x['edge_type']==('FALSE_DIRECT_SEMANTIC_LINK_REJECTED' if flag else
              'TOPIC_OVERLAP_ONLY_NO_DIRECT_SUPPORT'),
              'RECEIPT_FALSE_PRIOR_EVIDENCE_REENABLED')
        false+=flag
    check(actual==desired and e['pairwise_topic_overlaps_examined']==len(actual)
          and len(actual)==359 and false==27,
          'RECEIPT_PAIRWISE_COVERAGE_CHANGED')
    check(rules.get('schema')=='IRE_V5_FIRST_FIVE_41_RULE_CANDIDATES_APPLICABILITY_V1'
          and rules['rule_candidates_examined']==41
          and rules['all_video_rules_verified'] is False
          and rules['all_law_reference_effective_dates_verified'] is False
          and rules['financial_fact_approved_for_personal_advice']==0
          and rules['official_pages_are_not_refetched_by_github_CI'] is True,
          'RECEIPT_MISSTATED_41_RULE_REVIEW')
    expected_rules={x['id'] for x in prev['rows'] if x['kind']=='RULE'} | {
        x['id'] for x in new['candidate_assertions'] if x['assertion_type']=='LAW_OR_TAX'}
    rule_ids=set();narrow=0
    for x in rules['rows']:
        cid=x['claim_id']
        check(cid in expected_rules and cid not in rule_ids
          and x['auto_advisory_approval'] is False
          and x['formal_fact_verifier_signature'] is None
          and all(i in authorities or i in {'BOK-RATE','KRX-GOLD'} for i in x['applied_authority_ids']),
          'RECEIPT_RULE_WITHOUT_TRUSTED_SCOPE')
        rule_ids.add(cid)
        narrow+=x['narrow_fact_status']=='NARROW_RULE_VERIFIED_NO_PERSONAL_APPLICATION'
    check(rule_ids==expected_rules and len(rule_ids)==41
       and narrow==rules['narrow_rule_confirmed_no_personal_application']==7
       and rules['still_open_or_not_in_scope']==34,
       'RECEIPT_RULE_CATEGORY_OR_SCOPE_COUNT')
    check(batch.get('schema')=='IRE_V5_APP_FIVE_VIDEO_PUBLIC_STATE_V1'
      and batch.get('windows_total_reported')==288
      and batch.get('windows_processed_reported')==5
      and batch.get('windows_remaining_reported')==283
      and batch.get('source_and_receipts_readable_by_github') is False
      and batch.get('all_five_videos_research_complete') is False
      and sum(v['event_receipts_reported'] for v in batch['videos'])==5,
      'RECEIPT_PUBLIC_STATUS_CHANGED_WITHOUT_REAL_EVENTS')
    private={'private_original_reopened':False,'verified_windows':None,'verified_cue_anchors':None}
    if source_zip is not None:
        private=_bytes_private_source(Path(source_zip),a['cases'])
    blockers=['NO_NEW_VERIFIED_IRE_V5_MODEL_EVIDENCE_RELATION_EVENT_CHAIN',
              'ORIGINAL_FIVE_PUBLIC_RECEIPTS_NOT_PUBLICLY_REPLAYABLE',
              'ATOM_BY_ATOM_RECALL_NOT_PROVEN_FOR_288_WINDOWS',
              '34_OF_41_RULE_CANDIDATES_STILL_OPEN_OR_PARTIAL',
              'NO_PERSONALIZED_ADVICE_APPROVAL']
    return {'schema':'IRE_V5_FIRST_FIVE_ADJUDICATION_RECEIPT_READINESS_V1',
     'source_classification_corrections_resolved':13,
     'source_anchor_propositions_adjudicated':21,
     'candidate_claims_scope_reviewed':305,
     'claim_topic_clusters_adjudicated':22,
     'pairwise_topic_edges_reviewed':359,
     'unsafe_false_direct_links_blocked':27,
     'rule_candidates_scoped':41,
     'narrow_rule_subfacts_checked_no_personal_approval':7,
     'rule_claims_remaining_open':34,
     'original_private_source':private,
     'formal_new_v5_engine_window_receipts':0,
     'public_v5_batch_processed_windows':5,
     'public_v5_batch_remaining_windows':283,
     'formal_288_window_research_closure_approved':False,
     'formal_knowledge_merge_approved':False,
     'financial_advice_release_approved':False,
     'receipt_promotion':'BLOCKED_REQUIRES_ACTUAL_PRIVATE_EVENT_CHAIN',
     'blocked_reasons':blockers,
     'source_dossier_manifest_sha256':digest({'cases':a['cases'],'pairs':e['pair_edges'],
           'rules':rules['rows']}),
     'host_assessed_and_ci_replayed_not_independently_human_blind_verified':True}

def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--source-zip',type=Path,default=None)
    a=p.parse_args()
    print(json.dumps(verify(a.root,a.source_zip),ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
