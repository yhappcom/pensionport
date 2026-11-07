"""Fourth research overlay: 21 primary-rule case checks and 8 uncertain SRT numbers.

These are ChatGPT WEB-TOOL-VISIBLE citations. They are NOT authenticated raw
HTTP captures, independent legal opinions, or investment advice approvals.
Original source and prior four ledgers remain append-only and immutable.
"""
from __future__ import annotations
import json, re
from pathlib import Path
from urllib.parse import urlsplit
from datetime import datetime
from .engine import sha256, canonical, require, _private_dir, _exclusive_json, _read_json
from .third_pass import FocusedReview64

SCHEMA='IRE_V5_2026_RULE_RECHECK_V1'
EVENT='IRE_V5_2026_RULE_RECHECK_EVENT_V1'
E_STATUS={'GENERAL_RULE_SUPPORTED_SCOPE_OPEN','PARTIAL_RULE_MORE_EVIDENCE','HISTORICAL_RULE_CURRENT_VERSION_OPEN'}
N_STATUS={'AUDIO_OR_INDEPENDENT_TRANSCRIPT_REQUIRED'}
DOMAINS=('nts.go.kr','nps.or.kr','law.go.kr','kofia.or.kr','krx.co.kr')

def _allowed(url):
 try:
  u=urlsplit(url)
  return u.scheme=='https' and bool(u.hostname) and not (u.username or u.password) and any(u.hostname==d or u.hostname.endswith('.'+d) for d in DOMAINS)
 except ValueError:return False

class RuleRecheck29:
 def __init__(self,previous:FocusedReview64,path:Path):
  self.prior=previous
  self.ids=tuple(sorted(k for k in previous.ids if previous.audit.issues[k]['kind'] in ('E','N')))
  require(len(self.ids)==29 and sum(k.startswith('E-') for k in self.ids)==21 and sum(k.startswith('N-') for k in self.ids)==8,'RULE_RECHECK_TARGETS_INVALID')
  self.root=_private_dir(Path(path));self.events=_private_dir(self.root/'events')
  self.lock={'schema':SCHEMA,'source_sha256':sha256(previous.run.source),
   'base_event_head':previous.run.head,'first_audit_head':previous.audit.head,
   'historic_relation_head':previous.rel.head,'focused_third_head':previous.head,
   'issue_ids_sha256':sha256(canonical(self.ids)),
   'prior_rows_sha256':sha256(canonical({k:previous.rows[k] for k in self.ids}))}
  file=self.root/'lock.json'
  if file.exists():require(_read_json(file)==self.lock,'RULE_RECHECK_LOCK_DRIFT')
  else:_exclusive_json(file,self.lock)
  self.replay()

 def _validate(self,item):
  require(type(item) is dict and item.get('schema')==SCHEMA and item.get('issue_id') in self.ids,'RULE_RECHECK_CASE_UNKNOWN')
  issue=self.prior.audit.issues[item['issue_id']]
  require(item.get('kind')==issue['kind'] and item.get('prior_row_sha256')==sha256(canonical(self.prior.rows[item['issue_id']])), 'RULE_RECHECK_PRIOR_DRIFT')
  require(item.get('source_issue_sha256')==sha256(canonical(issue)), 'RULE_RECHECK_SOURCE_DRIFT')
  require(item.get('financial_fact_independently_approved') is False and item.get('personal_applicability_approved') is False and item.get('advice_approved') is False,'RULE_RECHECK_FAKE_APPROVAL')
  require(item.get('reviewer')=='CURRENT_CHATGPT_CONVERSATION' and isinstance(item.get('reason'),str) and len(item['reason'].strip())>=50,'RULE_RECHECK_MEANING_MISSING')
  try:dt=datetime.fromisoformat(item.get('observed_at','').replace('Z','+00:00'))
  except (TypeError,ValueError):raise ValueError('RULE_RECHECK_TIME_INVALID')
  require(dt.tzinfo is not None,'RULE_RECHECK_TIME_ZONE_REQUIRED')
  if issue['kind']=='E':
   require(item.get('decision') in E_STATUS and item.get('claim_id')==issue['claim_id'] and item.get('proposition')==issue['proposition'],'RULE_RECHECK_EVIDENCE_INVALID')
   ev=item.get('source_reference')
   require(type(ev) is dict and set(ev)=={'official_url','visible_excerpt','visible_excerpt_sha256','source_transport','effective_date_scope'} and _allowed(ev['official_url']), 'RULE_RECHECK_OFFICIAL_SOURCE_INVALID')
   require(isinstance(ev['visible_excerpt'],str) and len(ev['visible_excerpt'])>=15 and sha256(ev['visible_excerpt'].encode('utf-8'))==ev['visible_excerpt_sha256'] and ev['source_transport']=='CHAT_WEB_TOOL_VISIBLE_NOT_RAW_HTTP' and isinstance(ev['effective_date_scope'],str) and len(ev['effective_date_scope'])>=20,'RULE_RECHECK_EXCERPT_INVALID')
  else:
   require(item.get('decision') in N_STATUS and item.get('cue_index')==issue['cue_index'] and item.get('exact_srt_quote')==issue['quote'] and item.get('surrounding_original_cues')==issue['context'] and item.get('independent_audio_checked') is False and item.get('audio_correction') is None,'RULE_RECHECK_ASR_NO_AUDIO_PROOF')
  return item['issue_id']

 def replay(self):
  records={};head='0'*64;seq=0
  for p in sorted(self.events.glob('*.json')):
   ev=_read_json(p);seq+=1
   require(ev.get('schema')==EVENT and ev.get('sequence')==seq and ev.get('previous_sha256')==head and ev.get('lock_sha256')==sha256(canonical(self.lock)),'RULE_RECHECK_EVENT_FORK')
   val=ev.get('event_sha256');require(val==sha256(canonical({k:v for k,v in ev.items() if k!='event_sha256'})) and p.name==f'{seq:06d}_{val}.json','RULE_RECHECK_TAMPERED')
   require(isinstance(ev.get('rows'),list),'RULE_RECHECK_NO_ROWS')
   for item in ev['rows']:
    key=self._validate(item);require(key not in records,'RULE_RECHECK_DUPLICATE');records[key]=item
   head=val
  self.rows=records;self.seq=seq;self.head=head
  return self.status()

 def append(self,rows):
  require(type(rows) is list and 1<=len(rows)<=29,'RULE_RECHECK_BATCH_INVALID')
  ids=set(self.rows)
  for item in rows:
   key=self._validate(item);require(key not in ids,'RULE_RECHECK_DUPLICATE');ids.add(key)
  ev={'schema':EVENT,'sequence':self.seq+1,'previous_sha256':self.head,'lock_sha256':sha256(canonical(self.lock)),'rows':rows}
  ev['event_sha256']=sha256(canonical(ev))
  _exclusive_json(self.events/f"{self.seq+1:06d}_{ev['event_sha256']}.json",ev)
  return self.replay()

 def status(self):
  return {'schema':'IRE_V5_2026_RULE_RECHECK_STATUS_V1','cases_total':29,'cases_reviewed':len(self.rows),
    'official_cases_reviewed':sum(r['kind']=='E' for r in self.rows.values()),
    'asr_cases_reviewed':sum(r['kind']=='N' for r in self.rows.values()),
    'official_decisions':{k:sum(r['decision']==k for r in self.rows.values()) for k in sorted(E_STATUS)},
    'asr_needing_audio':sum(r['kind']=='N' for r in self.rows.values()),
    'original_92_still_open_for_independent_certification':92,
    'previous_four_chain_head':self.prior.head,'current_fifth_chain_head':self.head,
    'official_raw_http_independently_attested':False,'independent_financial_facts_approved':0,'advice_approved':False}
