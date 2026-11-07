"""Append-only second-pass reconciliation of V5 incremental OPEN relation risks.

This module certifies only whether two source-pinned *claim texts* contradict.
It cannot certify an official rule, numeric correctness, model recall, personal
applicability, or final investment-advisory approval. Original sealed V5 events
and the previous incremental event chain remain unchanged.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from datetime import datetime
import json,re
from ire.v5.engine import _private_dir, _exclusive_json, _read_json, canonical, sha256, require

SCHEMA='IRE_V5_SECOND_PASS_RELATION_V1'
EV_SCHEMA='IRE_V5_SECOND_PASS_EVENT_V1'
_KINDS={'EQUIVALENT_QUALIFICATION','CONSISTENT_WITH_DIFFERENT_SCOPE',
        'CORRECTION_ALREADY_PRESENT','TEMPORAL_SCOPE_NO_DIRECT_CONFLICT',
        'UNRESOLVED_SUBSTANTIVE_CONFLICT'}
_RELPREFIX='R-V5C'
_ID=re.compile(r'^R-V5C\d{4}$')

def timestamp(value):
    require(isinstance(value,str) and 'T' in value,'SECOND_PASS_TIME_REQUIRED')
    try: v=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as e: raise ValueError('SECOND_PASS_TIME_INVALID') from e
    require(v.tzinfo is not None,'SECOND_PASS_TIME_NOT_AWARE')

class RelationSecondPass:
    def __init__(self, audit, root:Path, prior_claims:dict, *, prior_blob_sha:str):
        self.audit=audit
        self.run=audit.run
        require(audit.seq>=1,'SECOND_PASS_ORIGINAL_AUDIT_REQUIRED')
        require(prior_blob_sha==self.run.manifest['prior_baseline_git_blob_sha'],
                'SECOND_PASS_WRONG_PRIOR_BLOB')
        self.prior_claims=prior_claims
        require(isinstance(prior_claims,dict) and all(isinstance(k,str) and isinstance(v,str)
                and len(v)>12 for k,v in prior_claims.items()),'SECOND_PASS_BAD_PRIOR_CLAIMS')
        self.eligible={k for k,x in audit.issues.items() if x['kind']=='R'
                       and audit.reviews[k]['decision']=='CONFLICT_OPEN'}
        require(self.eligible,'SECOND_PASS_NO_OPEN_CONFLICTS')
        self.root=_private_dir(Path(root))
        self.events=_private_dir(self.root/'events')
        self.lock={'schema':SCHEMA,'original_source_sha256':sha256(self.run.source),
                   'original_event_head_sha256':self.run.head,
                   'incremental_event_head_sha256':audit.head,
                   'prior_blob_sha256':prior_blob_sha,
                   'prior_claims_snapshot_sha256':sha256(canonical(prior_claims)),
                   'eligible_relation_issue_sha256':sha256(canonical(sorted(self.eligible)))}
        p=self.root/'second_pass_lock.json'
        if p.exists():require(_read_json(p)==self.lock,'SECOND_PASS_LOCK_DRIFT')
        else:_exclusive_json(p,self.lock)
        self.replay()

    def validate(self,row):
        require(isinstance(row,dict) and row.get('schema')==SCHEMA,'SECOND_PASS_SCHEMA_INVALID')
        issue_id=row.get('issue_id')
        require(isinstance(issue_id,str) and _ID.fullmatch(issue_id)
                and issue_id in self.eligible, 'SECOND_PASS_ISSUE_NOT_OPEN')
        issue=self.audit.issues[issue_id]
        require(row.get('issue_sha256')==sha256(canonical(issue)),
                'SECOND_PASS_ISSUE_HASH_CHANGED')
        target=issue['claim_id']
        actual=self.run._claims()[target]
        require(row.get('new_proposition')==actual['proposition'],
                'SECOND_PASS_SOURCE_PROPOSITION_CHANGED')
        refs=actual['source_refs']
        require(isinstance(refs,list) and refs and
                row.get('source_refs')==refs,
                'SECOND_PASS_SOURCE_REFERENCES_MISSING')
        for ref in refs:
            require(self.run.cues[ref['cue_index']].text.find(ref['quote'])>=0,
                    'SECOND_PASS_SOURCE_QUOTE_INCORRECT')
        prior_ids=issue['prior_claim_ids']
        require(isinstance(row.get('prior_claims'),list) and
                {x['claim_id'] for x in row['prior_claims']}==set(prior_ids)
                and len(row['prior_claims'])==len(prior_ids),'SECOND_PASS_PRIOR_IDS_MISSING')
        for r in row['prior_claims']:
            require(r['claim_id'] in self.prior_claims and
                    r.get('exact_prior_claim')==self.prior_claims[r['claim_id']],
                    'SECOND_PASS_PRIOR_TEXT_DRIFT')
        require(row.get('prior_blob_sha256')==self.lock['prior_blob_sha256'],
                'SECOND_PASS_PRIOR_BLOB_DRIFT')
        kind=row.get('relation_decision')
        require(kind in _KINDS,'SECOND_PASS_RELATION_DECISION_INVALID')
        require(isinstance(row.get('scope_explanation'),str)
                and len(row['scope_explanation'].strip())>=40,
                'SECOND_PASS_COMPARATIVE_EXPLANATION_TOO_SHORT')
        timestamp(row.get('reviewed_at'))
        require(row.get('independent_financial_approval') is False and
                row.get('financial_fact_approved') is False and
                row.get('personal_advice_approved') is False and
                row.get('old_claims_automatically_overwritten') is False,
                'SECOND_PASS_FALSE_TRUTH_OR_AUTOMERGE')
        require(row.get('source_truth_separately_unverified') is True,
                'SECOND_PASS_TRUTH_SCOPE_REQUIRED')
        return issue_id

    def submit(self, rows):
        require(isinstance(rows,list) and 1<=len(rows)<=64,'SECOND_PASS_BAD_BATCH')
        pending=set(self.rows)
        ids=[]
        for row in rows:
            issue_id=self.validate(row)
            require(issue_id not in pending,'SECOND_PASS_DUPLICATE_RELATION')
            pending.add(issue_id);ids.append(issue_id)
        body={'schema':EV_SCHEMA,'sequence':self.seq+1,'previous_event_sha256':self.head,
              'source_audit_sha256':self.audit.head,'rows':rows}
        body['event_sha256']=sha256(canonical(body))
        _exclusive_json(self.events/f"{self.seq+1:06d}_{body['event_sha256']}.json",body)
        self.replay()
        return self.status()

    def replay(self):
        rows={};head='0'*64
        files=sorted(self.events.glob('*.json'))
        for seq,f in enumerate(files,1):
            b=_read_json(f)
            require(b.get('schema')==EV_SCHEMA and b.get('sequence')==seq
                    and b.get('previous_event_sha256')==head
                    and b.get('source_audit_sha256')==self.audit.head,
                    'SECOND_PASS_CHAIN_INVALID')
            digest=b.get('event_sha256')
            require(isinstance(digest,str) and
                    digest==sha256(canonical({k:v for k,v in b.items() if k!='event_sha256'}))
                    and f.name==f'{seq:06d}_{digest}.json',
                    'SECOND_PASS_EVENT_TAMPERED')
            require(isinstance(b.get('rows'),list) and bool(b['rows']),
                    'SECOND_PASS_EMPTY_ROWS')
            for row in b['rows']:
                k=self.validate(row)
                require(k not in rows,'SECOND_PASS_REPLAY_DUPLICATE')
                rows[k]=row
            head=digest
        self.rows=rows;self.seq=len(files);self.head=head
        return self.status()

    def status(self):
        resolved=sum(x['relation_decision']!='UNRESOLVED_SUBSTANTIVE_CONFLICT'
                     for x in self.rows.values())
        # Crucially these are a subset of relationship-risk flags only; not
        # independent financial facts, legal review, or validated cue recall.
        from ire.v5.incremental import OPEN_DECISIONS
        unresolved_other=sum(1 for key in self.audit.issues if key not in self.eligible
                             and (key not in self.audit.reviews or
                                  self.audit.reviews[key]['decision'] in OPEN_DECISIONS))
        return {'schema':'IRE_V5_SECOND_PASS_RELATION_STATUS_V1',
                'eligible_relation_risks':len(self.eligible),
                'relationship_comparisons_rechecked':len(self.rows),
                'relationship_false_conflicts_reclassified':resolved,
                'remaining_relationship_risks':len(self.eligible)-resolved,
                'other_open_risks_unchanged':unresolved_other,
                'remaining_all_initial_open_risks':unresolved_other+len(self.eligible)-resolved,
                'original_event_head_sha256':self.run.head,
                'incremental_event_head_sha256':self.audit.head,
                'second_pass_event_count':self.seq,
                'second_pass_head_sha256':self.head,
                'all_source_cues_semantically_independently_audited':False,
                'official_financial_facts_independently_approved':0,
                'advisory_release_go':False}
