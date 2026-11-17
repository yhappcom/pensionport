"""Synthetic V162 original-first semantic routing and evidence custody checks."""
from __future__ import annotations
import copy,unittest
from ire.v6.codec import sha256,json_digest
from ire.v6.errors import InvalidInput
from ire.v6.source import verify_source
from ire.v6.tests.test_source_and_proof import make_srt, make_manifest
from v162_meaning_routed_evidence import (adjudicate_finance_ticket,
 audit_evidence_page_match,SCHEMA,_cue_pin)

class V162SourceFirstRoutingTests(unittest.TestCase):
 def setUp(self):
  raw=make_srt(['월배당 수익률을 정합니다.','세금을 없다고 가정합니다.','매출 300억을 예를 들면.'])
  man=make_manifest(raw,cut=3)
  self.source=verify_source(raw,man,expected_source_sha256=sha256(raw),expected_manifest_sha256=json_digest(man))
  self.atom={'claim_id':'C00001','kind':'HYPOTHETICAL','stance':'CONDITIONAL',
   'context_cue_indices':[1,2,3],'proposition':'원문 숫자를 가정한 산술 예시',
   'numeric_references':[]}
  self.row={'claim_id':'C00001','atom_sha256':json_digest(self.atom),
   'status':'OPEN','financial_claim':True}
  self.prior={'claim_id':'C00001','atom_sha256':json_digest(self.atom),
   'original_source_sha256':self.source.source_sha256,
   'manifest_sha256':self.source.manifest_sha256,
   'source_context_sha256':_cue_pin(self.source,[1,2,3]),
   'evidence_work_queue':'CURRENT_LAW_EFFECTIVE_SCOPE',
   'original_verdict_remains':'OPEN','finance_evidence_approved':False}
  self.review={'schema':SCHEMA,'claim_id':'C00001','atom_sha256':json_digest(self.atom),
   'original_source_sha256':self.source.source_sha256,
   'source_context_sha256':_cue_pin(self.source,[1,2,3]),
   'source_cue_indices':[1,2,3],
   'old_evidence_work_queue':'CURRENT_LAW_EFFECTIVE_SCOPE',
   'discourse_type':'HYPOTHETICAL_NUMERIC',
   'new_evidence_work_queue':'NUMERIC_ASSUMPTION_OR_EXTERNAL_FACT',
   'review_executor':'CHATGPT_IN_CHAT','review_as_of':'2026-11-17',
   'private_review_note_sha256':sha256(b'fictional source-first review'),
   'evidence_limitations':'가정적 숫자를 사용한 설명이며 사실 성과와 세법 적용은 미검증 상태로 남는다.',
   'financial_fact_approved':False,'personal_advice_approved':False,
   'primary_body_bytes_authenticated':False,'p0_go':False}

 def run_route(self,review=True):
  return adjudicate_finance_ticket(self.source,self.atom,self.row,self.prior,
                                  self.review if review else None)

 def test_01_no_chat_review_preserves_original_route(self):
  x=self.run_route(False)
  self.assertEqual(x['evidence_work_queue'],'CURRENT_LAW_EFFECTIVE_SCOPE')
  self.assertFalse(x['route_changed'])
  self.assertFalse(x['v123_final_release_allowed'])

 def test_02_chat_checked_hypothetical_corrected_not_finance_approved(self):
  x=self.run_route(True)
  self.assertEqual(x['evidence_work_queue'],'NUMERIC_ASSUMPTION_OR_EXTERNAL_FACT')
  self.assertTrue(x['source_first_chat_adjudicated'])
  self.assertFalse(x['research_candidate_approved'])

 def test_03_stale_original_cue_pin_is_rejected(self):
  self.prior['source_context_sha256']='0'*64
  with self.assertRaises(InvalidInput):self.run_route(True)

 def test_04_forged_chat_quote_pin_is_rejected(self):
  self.review['source_context_sha256']='f'*64
  with self.assertRaises(InvalidInput):self.run_route(True)

 def test_05_forged_finance_fact_approval_rejected(self):
  self.review['financial_fact_approved']=True
  with self.assertRaises(InvalidInput):self.run_route(True)

 def test_06_false_current_law_semantics_rejected(self):
  self.review['discourse_type']='REAL_CURRENT_LAW_CLAIM'
  self.review['new_evidence_work_queue']='CURRENT_LAW_EFFECTIVE_SCOPE'
  with self.assertRaises(InvalidInput):self.run_route(True)

 def test_07_unsupported_kind_for_hypothetical_rejected(self):
  self.atom['kind']='FACT'
  self.row['atom_sha256']=json_digest(self.atom)
  self.prior['atom_sha256']=json_digest(self.atom)
  self.review['atom_sha256']=json_digest(self.atom)
  with self.assertRaises(InvalidInput):self.run_route(True)

 def test_08_external_evidence_wrong_hostname_rejected(self):
  m={'claim_id':'C00001','atom_sha256':json_digest(self.atom),
     'source_sha256':self.source.source_sha256,
     'source_context_sha256':_cue_pin(self.source,[1,2,3]),
     'review_executor':'CHATGPT_IN_CHAT',
     'match_scope':'BIBLIOGRAPHIC_ONLY',
     'source_url':'https://www.wiley-vch.de.attacker.example/forged',
     'support_description':'가상의 출처를 사실로 오인하여 무조건적인 금융 사실 승인을 시도함.',
     'original_http_response_bytes_sha256':None,
     'original_http_response_bytes_archived':False,
     'v123_official_body_verified':False,
     'finance_fact_approved':False,'v123_final_approval':False,
     'knowledge_publish_allowed':False}
  with self.assertRaises(InvalidInput):
   audit_evidence_page_match(self.source,self.atom,
                             original_finance_open_row=self.row,match=m)

 def test_09_evidence_page_cannot_claim_raw_http_bytes(self):
  m={'claim_id':'C00001','atom_sha256':json_digest(self.atom),
     'source_sha256':self.source.source_sha256,
     'source_context_sha256':_cue_pin(self.source,[1,2,3]),
     'review_executor':'CHATGPT_IN_CHAT','match_scope':'BIBLIOGRAPHIC_ONLY',
     'source_url':'https://www.wiley-vch.de/en/book',
     'support_description':'출판사 서지에는 가상의 도서명과 저자를 소개하는 항목이 있음.',
     'original_http_response_bytes_sha256':sha256(b'FAKE'),
     'original_http_response_bytes_archived':False,
     'v123_official_body_verified':False,
     'finance_fact_approved':False,'v123_final_approval':False,
     'knowledge_publish_allowed':False}
  with self.assertRaises(InvalidInput):
   audit_evidence_page_match(self.source,self.atom,
                             original_finance_open_row=self.row,match=m)

 def test_10_hypothetical_cannot_upgrade_to_actual_issuer_fact(self):
  self.review['discourse_type']='COMPANY_HISTORICAL_FACT'
  self.review['new_evidence_work_queue']='CORPORATE_ISSUER_FACT'
  with self.assertRaises(InvalidInput):self.run_route(True)

if __name__=='__main__':unittest.main()
