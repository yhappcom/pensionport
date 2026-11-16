"""V150 negative official-byte/V23 controls; synthetic source, no owner GO."""
from __future__ import annotations
import copy,hashlib, tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from v150_real_issuer_v23_bridge import evidence_from_exact_live_bytes,synthetic_current_question,ASOF
from ire.v6.errors import InvalidInput
from v149_official_https_body import SPECS,audit_original_bytes


def mock_bytes(rule):
    s=SPECS[rule];y,m,d=map(int,s['effective'].split('-'))
    return (f'<html><body>{s["law"]} [시행 {y}. {m}. {d}.] '+s['article']+' '.join(s['terms'])+' 이 원문은 인증을 위한 시험 데이터로, 실제 법제처 응답이 아닙니다.</body></html>').encode('utf-8')

class V150LiveLawBridgeContracts(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.receipts=[]
        for rule,spec in SPECS.items():
            raw=mock_bytes(rule)
            (self.root/(rule+'.original_http_body.bin')).write_bytes(raw)
            receipt=audit_original_bytes(rule,raw,requested_url=spec['url'],final_url=spec['url'],captured_on=ASOF,as_of=ASOF)
            receipt.update(tls_session_executed_by_this_function=True,
                status='HTTPS_TRANSPORT_RAW_BODY_CAPTURED_SCOPE_REVIEW_STILL_REQUIRED')
            self.receipts.append(receipt)

    def test_01_literal_rehash_and_evidence_sha_bound(self):
        rules=evidence_from_exact_live_bytes(self.root,self.receipts)
        self.assertEqual(len(rules),2)
        for e in rules:
            original=(self.root/(e['rule_id']+'.original_http_body.bin')).read_bytes()
            self.assertEqual(e['document_body_sha256'],hashlib.sha256(original).hexdigest())
            self.assertEqual(e['retrieved_on'],ASOF)

    def test_02_modified_raw_bytes_rejected(self):
        p=self.root/'ISA_91_18.original_http_body.bin'
        p.write_bytes(p.read_bytes()+b'secret tamper')
        with self.assertRaises(ValueError):evidence_from_exact_live_bytes(self.root,self.receipts)

    def test_03_synthetic_or_missing_tls_not_authorized(self):
        receipts=copy.deepcopy(self.receipts)
        receipts[0]['tls_session_executed_by_this_function']=False
        with self.assertRaisesRegex(ValueError,'LIVE_ORIGIN'):
            evidence_from_exact_live_bytes(self.root,receipts)

    def test_04_forged_institutional_html_url_not_accepted(self):
        receipts=copy.deepcopy(self.receipts);receipts[0]['final_https_url']='https://evil.example/'
        with self.assertRaises(ValueError):evidence_from_exact_live_bytes(self.root,receipts)

    def test_05_missing_a_rule_blocks_completeness(self):
        with self.assertRaisesRegex(ValueError,'OFFICIAL_SOURCE_CENSUS'):
            evidence_from_exact_live_bytes(self.root,self.receipts[:1])

    def test_06_current_source_is_synthetic_not_owner(self):
        source,exchange,decisions=synthetic_current_question()
        self.assertEqual(len(exchange['atoms']),2)
        self.assertEqual(len(decisions),2)
        self.assertNotEqual(source.source_sha256,'638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d')
        self.assertTrue(all(d['classification']=='CURRENT_RULE_CONTRADICTS_SOURCE' for d in decisions))

    def test_07_semantic_chat_claim_source_hash_mutation_fails_v22(self):
        from ire.v6.current_law_reassessment import audit_current_law_reassessment
        source,ex,dec=synthetic_current_question()
        ev=evidence_from_exact_live_bytes(self.root,self.receipts)
        dec[0]['proposition_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'PROPOSITION_DRIFT'):
            audit_current_law_reassessment(source,ex,current_as_of=ASOF,primary_evidence=ev,chat_decisions=dec)

    def test_08_future_rule_not_misrepresented_as_current(self):
        from ire.v6.current_law_reassessment import audit_current_law_reassessment
        source,ex,dec=synthetic_current_question();ev=evidence_from_exact_live_bytes(self.root,self.receipts)
        ev[0]['effective_from']='2027-11-16'
        with self.assertRaisesRegex(InvalidInput,'RULE_NOT_CURRENT'):
            audit_current_law_reassessment(source,ex,current_as_of=ASOF,primary_evidence=ev,chat_decisions=dec)

if __name__=='__main__':unittest.main()
