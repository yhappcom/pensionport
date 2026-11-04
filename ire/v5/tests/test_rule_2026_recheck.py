"""Source-locked synthetic 29-case recheck safety regressions."""
from __future__ import annotations
import unittest,json,tempfile
from pathlib import Path
from types import SimpleNamespace
from ire.v5.engine import sha256,canonical
from ire.v5.rule_2026_audit import RuleRecheck29,SCHEMA,_allowed

class CheckRuleReaudit(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.issue={}
  self.rows={}
  for i in range(1,22):
   k=f'E-V5C{i:04d}';self.issue[k]={'kind':'E','claim_id':f'V5C{i:04d}','proposition':f'CASE {i} legal scope pending'}
   self.rows[k]={'issue_id':k,'decision':'PRIMARY_RULE_TEXT_FOUND_APPLICABILITY_OPEN'}
  for i in range(1,9):
   k=f'N-{i:05d}';self.issue[k]={'kind':'N','cue_index':i,'quote':f'bad numeric cue {i}', 'context':[{'cue_index':i,'text':f'bad numeric cue {i}'}]}
   self.rows[k]={'issue_id':k,'decision':'AUDIO_TRANSCRIPT_REQUIRED'}
  r=SimpleNamespace(source=b'untrusted original source stub',head='a'*64)
  a=SimpleNamespace(issues=self.issue,head='b'*64)
  rel=SimpleNamespace(head='c'*64)
  prior=SimpleNamespace(run=r,audit=a,rel=rel,head='d'*64,rows=self.rows,ids=tuple(self.issue))
  self.check=RuleRecheck29(prior,Path(self.tmp.name)/'overlay')
 def make(self,k):
  iss=self.issue[k]
  x={'schema':SCHEMA,'issue_id':k,'kind':iss['kind'],
     'source_issue_sha256':sha256(canonical(iss)),'prior_row_sha256':sha256(canonical(self.rows[k])),
     'financial_fact_independently_approved':False,'personal_applicability_approved':False,
     'advice_approved':False,'reviewer':'CURRENT_CHATGPT_CONVERSATION','observed_at':'2026-11-04T01:00:00+00:00',
     'reason':'This independent check is limited to official-rule wording and does not attest personal applicability or original audio.'}
  if iss['kind']=='E':
   quote='연금계좌에서 일부 금액이 인출되는 경우에는 법령 순서대로 인출되는 것으로 본다.'
   x.update({'claim_id':iss['claim_id'],'proposition':iss['proposition'], 'decision':'GENERAL_RULE_SUPPORTED_SCOPE_OPEN',
       'source_reference':{'official_url':'https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1029964673',
       'visible_excerpt':quote,'visible_excerpt_sha256':sha256(quote.encode('utf-8')),
       'source_transport':'CHAT_WEB_TOOL_VISIBLE_NOT_RAW_HTTP',
       'effective_date_scope':'As of 2026-11-04, individual taxpayer facts and effective-date check remain unverified.'}})
  else:
   x.update({'cue_index':iss['cue_index'],'exact_srt_quote':iss['quote'],
       'surrounding_original_cues':iss['context'],
       'decision':'AUDIO_OR_INDEPENDENT_TRANSCRIPT_REQUIRED',
       'independent_audio_checked':False,'audio_correction':None})
  return x
 def test_29_cues_all_locked_replay(self):
  self.check.append([self.make(k) for k in self.check.ids])
  s=self.check.replay()
  self.assertEqual((s['cases_reviewed'],s['official_cases_reviewed'],s['asr_cases_reviewed']),(29,21,8))
  self.assertEqual(s['independent_financial_facts_approved'],0)
 def test_false_financial_approval_rejected(self):
  x=self.make('E-V5C0001');x['financial_fact_independently_approved']=True
  with self.assertRaisesRegex(Exception,'RULE_RECHECK_FAKE_APPROVAL'):self.check.append([x])
 def test_fake_issuer_and_hash_rejected(self):
  self.assertFalse(_allowed('https://fake.nts.go.kr.evil.example/ref'))
  x=self.make('E-V5C0001');x['source_reference']['official_url']='https://fake.nts.go.kr.evil.example/ref'
  with self.assertRaisesRegex(Exception,'RULE_RECHECK_OFFICIAL_SOURCE_INVALID'):self.check.append([x])
  x=self.make('E-V5C0001');x['source_reference']['visible_excerpt_sha256']='c'*64
  with self.assertRaisesRegex(Exception,'RULE_RECHECK_EXCERPT_INVALID'):self.check.append([x])
 def test_unverified_audio_not_corrected(self):
  x=self.make('N-00001');x['audio_correction']='100만원'
  with self.assertRaisesRegex(Exception,'RULE_RECHECK_ASR_NO_AUDIO_PROOF'):self.check.append([x])
 def test_event_tamper_detected(self):
  self.check.append([self.make('E-V5C0001')]);p=next(self.check.events.glob('*.json'))
  obj=json.loads(p.read_text());obj['rows'][0]['reason']='falsely changed in place';p.write_text(json.dumps(obj))
  with self.assertRaisesRegex(Exception,'RULE_RECHECK_TAMPERED'):self.check.replay()
 def test_source_or_prior_drift_rejected(self):
  x=self.make('E-V5C0001');x['source_issue_sha256']='b'*64
  with self.assertRaisesRegex(Exception,'RULE_RECHECK_SOURCE_DRIFT'):self.check.append([x])
  x=self.make('E-V5C0001');x['prior_row_sha256']='b'*64
  with self.assertRaisesRegex(Exception,'RULE_RECHECK_PRIOR_DRIFT'):self.check.append([x])
if __name__=='__main__':unittest.main()
