"""P0 third-pass 64-case ledger. NEVER independently certifies financial truth.

Locks source, original ledger, first-pass risk ledger, second-pass historical relation
ledger, source wording and official-primary-page *excerpts* into immutable events.
Official page text is cited by URL but has not been network-origin attested here.
"""
from __future__ import annotations
import json,re
from pathlib import Path
from datetime import datetime
from urllib.parse import urlsplit
from .engine import ResearchRun, _private_dir, _exclusive_json, _read_json, canonical, sha256, require
from .incremental import IncrementalAudit
from .second_pass import RelationSecondPass

SCHEMA='IRE_V5_64_FOCUSED_THIRD_PASS_V1'
EVENT='IRE_V5_64_FOCUSED_EVENT_V1'
B_STATUS={'BOUNDARY_CONTEXT_RECONSTRUCTED_LIMITED','BOUNDARY_MATERIAL_SCOPE_OPEN','BOUNDARY_ASR_OR_AMOUNT_OPEN'}
E_STATUS={'PRIMARY_RULE_TEXT_FOUND_APPLICABILITY_OPEN','PRIMARY_SOURCE_INSUFFICIENT_SCOPE_OPEN'}
N_STATUS={'AUDIO_TRANSCRIPT_REQUIRED'}
VALID={'B':B_STATUS,'E':E_STATUS,'N':N_STATUS}
URL_DOMAINS=('nps.or.kr','nts.go.kr','law.go.kr','krx.co.kr','kofia.or.kr')

def _official_url(url):
 p=urlsplit(url)
 return p.scheme=='https' and bool(p.hostname) and not p.username and not p.password and any(p.hostname==x or p.hostname.endswith('.'+x) for x in URL_DOMAINS)

def make_issue_ids(audit:IncrementalAudit):
 return tuple(sorted(k for k,v in audit.reviews.items() if v['decision'] in {
  'CONDITION_SPANS_WINDOWS_OPEN','SOURCE_TRANSCRIPTION_OPEN','ASR_NUMERIC_OPEN',
  'OFFICIAL_CANDIDATE_SCOPE_OPEN','OFFICIAL_SEARCH_OPEN','PERSONAL_APPLICABILITY_OPEN','EFFECTIVE_DATE_OPEN'}))

class FocusedReview64:
 def __init__(self,audit:IncrementalAudit,relation:RelationSecondPass,root:Path):
  require(audit.run.head==relation.run.head and audit.head==relation.audit.head,'THIRD_PASS_CHAIN_FORK')
  self.audit,self.rel,self.run=audit,relation,audit.run
  self.ids=make_issue_ids(audit)
  require(len(self.ids)==64 and {k:sum(audit.issues[i]['kind']==k for i in self.ids) for k in ('B','E','N')}=={'B':35,'E':21,'N':8},'THIRD_PASS_TARGETS_NOT_35_21_8')
  self.root=_private_dir(Path(root));self.events=_private_dir(self.root/'events')
  self.lock={'schema':SCHEMA,'source_sha256':sha256(self.run.source),'base_head':self.run.head,
   'audit_head':audit.head,'relation_head':relation.head,'case_ids_sha256':sha256(canonical(self.ids)),
   'case_issue_hashes_sha256':sha256(canonical({k:sha256(canonical(audit.issues[k])) for k in self.ids}))}
  f=self.root/'lock.json'
  if f.exists():require(_read_json(f)==self.lock,'THIRD_PASS_LOCK_MISMATCH')
  else:_exclusive_json(f,self.lock)
  self.replay()
 def validate_row(self,row):
  require(type(row) is dict and row.get('schema')==SCHEMA and row.get('issue_id') in self.ids,'THIRD_PASS_UNKNOWN_CASE')
  issue=self.audit.issues[row['issue_id']];kind=issue['kind']
  require(row.get('kind')==kind and row.get('decision') in VALID[kind],'THIRD_PASS_BAD_DISPOSITION')
  require(row.get('issue_sha256')==sha256(canonical(issue)) and
   row.get('prior_review_sha256')==sha256(canonical(self.audit.reviews[row['issue_id']])), 'THIRD_PASS_SOURCE_OR_PRIOR_REVIEW_CHANGED')
  require(row.get('financial_fact_independently_approved') is False and row.get('investment_advice_approved') is False
   and row.get('old_events_rewritten') is False, 'THIRD_PASS_FALSE_APPROVAL')
  require(isinstance(row.get('explanation'),str) and len(row['explanation'].strip())>=55,'THIRD_PASS_MEANING_UNREVIEWED')
  require(row.get('reviewer')=='CURRENT_CHATGPT_CONVERSATION','THIRD_PASS_REVIEWER_UNKNOWN')
  try:date=datetime.fromisoformat(row.get('reviewed_at','').replace('Z','+00:00'))
  except (ValueError,TypeError):raise ValueError('THIRD_PASS_REVIEW_TIME')
  require(date.tzinfo is not None,'THIRD_PASS_REVIEW_TIME_NOT_AWARE')
  if kind=='B':
   require(row.get('left_cue')==issue['left_cue'] and row.get('right_cue')==issue['right_cue'] and
    row.get('left_quote')==issue['left_quote'] and row.get('right_quote')==issue['right_quote'], 'THIRD_PASS_BOUNDARY_QUOTE_CHANGED')
   require(row.get('context')==issue['context'],'THIRD_PASS_CONTEXT_UNVERIFIED')
   ids=row.get('related_claim_ids')
   require(type(ids) is list and bool(ids) and all(cid in self.run._claims() for cid in ids),'THIRD_PASS_BOUNDARY_CLAIM_REQUIRED')
   i=issue['left_cue'];require(any(abs(ref['cue_index']-i)<=7 for cid in ids for ref in self.run._claims()[cid]['source_refs']),'THIRD_PASS_BOUNDARY_CLAIM_DISTANCE')
  if kind=='N':
   require(row.get('cue_index')==issue['cue_index'] and row.get('exact_quote')==issue['quote'] and
    row.get('context')==issue['context'] and row.get('independent_audio_checked') is False,'THIRD_PASS_NUMERIC_NOT_AUDIO_VERIFIED')
  if kind=='E':
   require(row.get('claim_id')==issue['claim_id'] and row.get('proposition')==issue['proposition']
    and row.get('personal_or_effective_scope_approved') is False,'THIRD_PASS_EVIDENCE_APPLICABILITY_NOT_ATTESTED')
   if row['decision']=='PRIMARY_RULE_TEXT_FOUND_APPLICABILITY_OPEN':
    ev=row.get('evidence')
    require(type(ev) is dict and _official_url(ev.get('official_url','')) and
      isinstance(ev.get('exact_excerpt'),str) and len(ev['exact_excerpt'])>=12 and
      isinstance(ev.get('source_type'),str) and ev['source_type']=='WEB_TOOL_VISIBLE_PRIMARY_EXCERPT' and
      ev.get('network_origin_independently_attested') is False and
      isinstance(ev.get('date_and_scope_limit'),str) and len(ev['date_and_scope_limit'])>=20, 'THIRD_PASS_OFFICIAL_EVIDENCE_INCOMPLETE')
    require(row.get('evidence_sha256')==sha256(canonical(ev)), 'THIRD_PASS_EVIDENCE_HASH_DRIFT')
   else:
    require(row.get('evidence') is None,'THIRD_PASS_INSUFFICIENT_EVIDENCE_MUST_NOT_ATTACH_RULE')
  return row['issue_id']
 def replay(self):
  rows={};head='0'*64
  for n,p in enumerate(sorted(self.events.glob('*.json')),1):
   ev=_read_json(p)
   require(ev.get('schema')==EVENT and ev.get('sequence')==n and ev.get('previous_sha256')==head
    and ev.get('lock_sha256')==sha256(canonical(self.lock)), 'THIRD_PASS_EVENT_CHAIN_FORK')
   digest=ev.get('event_sha256');require(digest==sha256(canonical({k:v for k,v in ev.items() if k!='event_sha256'})) and
       p.name==f'{n:06d}_{digest}.json','THIRD_PASS_EVENT_TAMPERED')
   require(type(ev.get('rows')) is list,'THIRD_PASS_NO_ROWS')
   for row in ev['rows']:
    k=self.validate_row(row);require(k not in rows,'THIRD_PASS_DUPLICATE');rows[k]=row
   head=digest
  self.rows=rows;self.seq=len(sorted(self.events.glob('*.json')));self.head=head
  return self.status()
 def submit(self,rows):
  require(type(rows) is list and 1<=len(rows)<=64,'THIRD_PASS_INVALID_BATCH')
  seen=set(self.rows)
  for row in rows:
   key=self.validate_row(row);require(key not in seen,'THIRD_PASS_DUPLICATE');seen.add(key)
  body={'schema':EVENT,'sequence':self.seq+1,'previous_sha256':self.head,
        'lock_sha256':sha256(canonical(self.lock)),'rows':rows}
  body['event_sha256']=sha256(canonical(body))
  _exclusive_json(self.events/f"{self.seq+1:06d}_{body['event_sha256']}.json",body)
  return self.replay()
 def status(self):
  counts={kind:{s:sum(row['decision']==s for row in self.rows.values()) for s in VALID[kind]} for kind in ('B','E','N')}
  stitched=counts['B']['BOUNDARY_CONTEXT_RECONSTRUCTED_LIMITED']
  return {'schema':'IRE_V5_64_FOCUSED_STATUS_V1','target_cases':64,'reviewed':len(self.rows),
          'reviewed_boundary':sum(row['kind']=='B' for row in self.rows.values()),
          'reviewed_numeric':sum(row['kind']=='N' for row in self.rows.values()),
          'reviewed_official':sum(row['kind']=='E' for row in self.rows.values()),
          'decision_counts':counts,'boundary_context_reconstructed_limited':stitched,
          'remaining_initial_112_risks':112-stitched,
          'remaining_high_priority_64_risks':64-stitched,
          'source_chain_head':self.run.head,'audit_chain_head':self.audit.head,
          'relation_chain_head':self.rel.head,'third_pass_head':getattr(self,'head','0'*64),
          'official_financial_facts_independently_approved':0,'advisory_go':False,
          'official_effective_date_and_individual_scope_open':True,
          'numeric_asr_needs_audio':True}
