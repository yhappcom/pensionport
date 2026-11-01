"""New synthetic official-document tests; no previous investment study claims."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from unittest.mock import patch

from ire.evidence import (
    issuer_for,independently_fetch_candidate,select_evidence_excerpt,
    MAX_DOCUMENT_BYTES,_check_public_dns)
from ire.evidence_audit import compare_to_fetched_evidence,OUT_SCHEMA
from ire.orchestrator import OrchestrationPolicy,execute_independent_research
from test_engine import synthetic_srt,annotations,VID
from test_semantics import synthetic_reply
from test_orchestrator import mock_official


TEST_URL="https://www.bok.or.kr/portal/mock-explicit-example"
# Synthetic document deliberately uses invented terms; not an official quote.
TEST_TEXT=("이 자료는 모의 시험용으로 만든 합성 설명입니다. "
           "가상 상품 A의 비용은 계약 조건에 따라 달라질 수 있습니다. "
           "연간 수수료 0.3%는 예시로 제시되었습니다. "
           "실제 적용 조건과 시점은 별도 확인해야 합니다. ")
RAW_DOCUMENT=("<html><head><style>숨김 지시</style></head>"
              "<body><article>"+TEST_TEXT*4+
              "</article><script>injected instruction</script></body></html>"
              ).encode("utf-8")


def fake_reader(url):
    return RAW_DOCUMENT,"text/html; charset=utf-8",url


def judgment(claim,quote="가상 상품 A의 비용은 계약 조건에 따라 달라질 수 있습니다.",
             verdict="SUPPORTS",time_relation="UNRESOLVED"):
    return {
        "claim_id":claim["claim_id"],
        "verdict":verdict,
        "evidence_quote":quote,
        "jurisdiction_relation":"UNRESOLVED",
        "effective_date_relation":time_relation,
        "condition_relation":"MATCH",
        "exception_relation":"NOT_SPECIFIED",
        "number_relation":"NOT_SPECIFIED",
        "explanation":"합성 문서와 원문 조건을 비교했으나 효력 시점은 미해결입니다."
    }


class IndependentEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.raw,self.digest=synthetic_srt()
        self.a=annotations(self.digest)
        self.claim=self.a["claims"][0]

    def test_issuer_safety_and_special_market(self):
        self.assertEqual(issuer_for(TEST_URL),"BANK_OF_KOREA")
        self.assertEqual(issuer_for("https://www.krx.co.kr/example"),"KOREA_EXCHANGE")
        self.assertIsNone(issuer_for("http://www.bok.or.kr/"))
        self.assertIsNone(issuer_for("https://bok.or.kr.evil.example/"))
        self.assertIsNone(issuer_for("https://127.0.0.1/"))
        self.assertIsNone(issuer_for("https://localhost/"))
        self.assertIsNone(issuer_for("https://www.bok.or.kr:8080/"))
        self.assertIsNone(issuer_for("https://user:secret@www.bok.or.kr/"))
        self.assertIsNone(issuer_for("https://random-unverified.or.kr/"))

    def test_document_body_hash_html_text_and_context_are_recomputed(self):
        document=independently_fetch_candidate(
            TEST_URL,read_fn=fake_reader,fetched_at="2026-11-01T00:00:00Z")
        self.assertEqual(document["raw_byte_size"],len(RAW_DOCUMENT))
        self.assertIn("가상 상품 A의 비용",document["visible_text"])
        self.assertNotIn("injected instruction",document["visible_text"])
        self.assertNotIn("숨김 지시",document["visible_text"])
        self.assertEqual(document["raw_sha256"],__import__("hashlib").sha256(
            RAW_DOCUMENT).hexdigest())
        self.assertFalse(document["independent_financial_fact_approved"])
        excerpt=select_evidence_excerpt(document,self.claim)
        self.assertIn("계약 조건",excerpt["excerpt"])

    def test_fetch_rejects_redirect_unsupported_mime_and_oversize(self):
        def redirect(url):
            return RAW_DOCUMENT,"text/html","https://attacker.example/phishing"
        with self.assertRaisesRegex(ValueError,"EVIDENCE_FETCH_REDIRECT_OR_MIME_INVALID"):
            independently_fetch_candidate(TEST_URL,read_fn=redirect)
        def pdf(url):
            return b"%PDF-1.4"+b"x"*30,"application/pdf",url
        with self.assertRaisesRegex(ValueError,"EVIDENCE_UNSUPPORTED_DOCUMENT_MIME"):
            independently_fetch_candidate(TEST_URL,read_fn=pdf)
        def too_big(url):
            return b"x"*(MAX_DOCUMENT_BYTES+1),"text/plain",url
        with self.assertRaisesRegex(ValueError,"EVIDENCE_SOURCE_BYTES_INVALID_OR_OVERSIZE"):
            independently_fetch_candidate(TEST_URL,read_fn=too_big)

    def test_evidence_comparison_exact_quote_and_scoped_unknown(self):
        document=independently_fetch_candidate(TEST_URL,read_fn=fake_reader)
        result=compare_to_fetched_evidence(
            self.claim,document,model="synthetic-mock",
            model_fn=lambda packet:judgment(packet["claim"]))
        self.assertEqual(result["model_verdict"],"SUPPORTS")
        self.assertEqual(result["assessment_label"],
                         "PROVISIONAL_SUPPORT_WITH_UNRESOLVED_SCOPE")
        self.assertTrue(result["exact_quote_verified_against_fetched_text"])
        self.assertFalse(result["financial_claim_fact_approved"])
        self.assertEqual(result["inference_mode"],"SYNTHETIC_INJECTED_MOCK")

    def test_contradiction_needs_real_quote(self):
        doc=independently_fetch_candidate(TEST_URL,read_fn=fake_reader)
        r=compare_to_fetched_evidence(self.claim,doc,"synthetic-mock",
            model_fn=lambda packet:judgment(packet["claim"],
                 quote="연간 수수료 0.3%는 예시로 제시되었습니다.",
                 verdict="CONTRADICTS",time_relation="CONFLICT"))
        self.assertEqual(r["assessment_label"],
                         "POSSIBLE_CONTRADICTION_REQUIRES_REVIEW")
        self.assertFalse(r["financial_claim_fact_approved"])

    def test_hallucinated_primary_quote_fails_hard(self):
        doc=independently_fetch_candidate(TEST_URL,read_fn=fake_reader)
        with self.assertRaisesRegex(ValueError,"EVIDENCE_AUDIT_FABRICATED_PRIMARY_QUOTE"):
            compare_to_fetched_evidence(self.claim,doc,"synthetic-mock",
                model_fn=lambda packet:judgment(packet["claim"],
                    quote="모든 금융투자는 국가가 원금을 보장합니다."))
        with self.assertRaisesRegex(ValueError,"EVIDENCE_AUDIT_NEEDS_EXACT_PRIMARY_QUOTE"):
            compare_to_fetched_evidence(self.claim,doc,"synthetic-mock",
                model_fn=lambda packet:judgment(packet["claim"],quote=""))

    def test_official_evidence_live_model_requires_key(self):
        doc=independently_fetch_candidate(TEST_URL,read_fn=fake_reader)
        with self.assertRaisesRegex(ValueError,"EVIDENCE_AUDIT_API_KEY_MISSING"):
            compare_to_fetched_evidence(self.claim,doc,"configured-model",
                api_key="")

    def test_combined_financial_semantics_and_primary_evidence(self):
        def fake_issuer_search(claim):
            out=mock_official(claim)
            return out
        policy=OrchestrationPolicy(model="synthetic-mock",
                                   max_evidence_documents=5)
        result=execute_independent_research(
            self.raw,VID,self.digest,policy,
            semantic_request_fn=lambda _:synthetic_reply(self.a),
            official_response_fn=fake_issuer_search,
            evidence_read_fn=fake_reader,
            evidence_model_fn=lambda packet:judgment(packet["claim"]))
        self.assertEqual(result["metrics"]["proposed_financial_atoms"],2)
        self.assertEqual(result["metrics"]["real_document_text_fetches"],0)
        self.assertEqual(result["metrics"]["scoped_evidence_audits"],2)
        self.assertEqual(result["stages"][4]["status"],
                         "PROVISIONAL_SCOPED_AUDITS_NOT_APPROVED")
        self.assertTrue(result["private_details"]["evidence_scope_audits"][0][
            "exact_quote_verified_against_fetched_text"])
        self.assertEqual(result["approved_claims"],0)
        self.assertFalse(result["factual_truth_certified"])

    def test_partial_evidence_fetch_failure_does_not_invent_success(self):
        calls=[]
        def fail_second(url):
            calls.append(url)
            if len(calls)==2:raise ValueError("EVIDENCE_DOCUMENT_DECODE_FAILED")
            return fake_reader(url)
        policy=OrchestrationPolicy(model="synthetic-mock")
        result=execute_independent_research(
            self.raw,VID,self.digest,policy,
            semantic_request_fn=lambda _:synthetic_reply(self.a),
            official_response_fn=mock_official,
            evidence_read_fn=fail_second,
            evidence_model_fn=lambda packet:judgment(packet["claim"]))
        self.assertEqual(result["metrics"]["scoped_evidence_audits"],1)
        self.assertIn("PRIMARY_DOCUMENT_DOWNLOAD_OR_AUDIT_FAILURES",result["blockers"])
        self.assertEqual(len(result["private_details"]["evidence_download_failures"]),1)
        self.assertEqual(result["approved_claims"],0)

    def test_fetch_fail_closed_on_dns_private_target(self):
        with patch("socket.getaddrinfo",return_value=[
            (2,1,6,"",("127.0.0.1",443))
        ]):
            with self.assertRaisesRegex(ValueError,
                                         "EVIDENCE_PRIVATE_OR_RESERVED_NETWORK_DENIED"):
                _check_public_dns(TEST_URL)

    def test_strict_audit_json_schema_expected_fields(self):
        self.assertEqual(OUT_SCHEMA["additionalProperties"],False)
        self.assertEqual(set(OUT_SCHEMA["required"]),set(OUT_SCHEMA["properties"]))
        self.assertEqual(OUT_SCHEMA["properties"]["verdict"]["type"],"string")


    def test_private_primary_bytes_snapshot_rejects_mutation(self):
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            folder=str(Path(tmp)/"source_bytes")
            doc=independently_fetch_candidate(
                TEST_URL,read_fn=fake_reader,private_evidence_dir=folder)
            where=Path(doc["private_immutable_source_snapshot"])
            self.assertTrue(where.is_file())
            self.assertEqual(where.read_bytes(),RAW_DOCUMENT)
            self.assertEqual(where.stat().st_mode & 0o077,0)
            same=independently_fetch_candidate(
                TEST_URL,read_fn=fake_reader,private_evidence_dir=folder)
            self.assertEqual(doc["raw_sha256"],same["raw_sha256"])
            where.write_bytes(b"bad changed document")
            with self.assertRaisesRegex(ValueError,
                                        "EVIDENCE_PRIVATE_SNAPSHOT_HASH_CHANGED"):
                independently_fetch_candidate(
                    TEST_URL,read_fn=fake_reader,private_evidence_dir=folder)



    def test_real_http_redirect_layer_blocks_cross_issuer_before_follow(self):
        import io
        from email.message import Message
        from unittest.mock import patch
        from urllib.error import HTTPError
        from ire.evidence import _restricted_get
        response_headers=Message()
        response_headers["Location"]="https://attacker.example/fake"
        moved=HTTPError(TEST_URL,302,"Found",response_headers,io.BytesIO())
        calls=[]
        class FakeOpener:
            def open(self,req,timeout):
                calls.append(req.full_url)
                raise moved
        with patch("urllib.request.build_opener",return_value=FakeOpener()), \
             patch("ire.evidence._check_public_dns",return_value=None):
            with self.assertRaisesRegex(ValueError,
                                         "EVIDENCE_REDIRECT_CROSS_ISSUER_DENIED"):
                _restricted_get(TEST_URL)
        self.assertEqual(calls,[TEST_URL])

    def test_real_http_redirect_layer_accepts_same_issuer_https(self):
        import io
        from email.message import Message
        from unittest.mock import patch
        from urllib.error import HTTPError
        from ire.evidence import _restricted_get
        target="https://www.bok.or.kr/portal/mock-final"
        hdr=Message();hdr["Location"]=target
        moved=HTTPError(TEST_URL,302,"Found",hdr,io.BytesIO())
        calls=[]
        class MockLiveResponse:
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def geturl(self):return target
            def read(self,cap):return RAW_DOCUMENT
            @property
            def headers(self):
                h=Message();h["Content-Type"]="text/html;charset=utf-8"
                return h
        class FakeOpener:
            def open(self,req,timeout):
                calls.append(req.full_url)
                if req.full_url==TEST_URL:raise moved
                return MockLiveResponse()
        with patch("urllib.request.build_opener",return_value=FakeOpener()), \
             patch("ire.evidence._check_public_dns",return_value=None):
            raw,mime,final=_restricted_get(TEST_URL)
        self.assertEqual(calls,[TEST_URL,target])
        self.assertEqual(raw,RAW_DOCUMENT)
        self.assertEqual(final,target)



    def test_bounded_primary_research_is_fair_across_claims(self):
        first="https://www.bok.or.kr/portal/example"
        second="https://www.bis.org/mock-other"
        third="https://www.krx.co.kr/example"
        def search(claim):
            urls=([first,second] if claim["claim_id"]=="C00001"
                  else [third])
            return {"status":"completed","output":[
                {"type":"web_search_call","status":"completed"},
                {"type":"message","content":[{"type":"output_text",
                   "annotations":[{"type":"url_citation","url":url}
                                  for url in urls]}]}]}
        seen=[]
        def reader(url):
            seen.append(url)
            return fake_reader(url)
        result=execute_independent_research(
            self.raw,VID,self.digest,
            OrchestrationPolicy(model="mock-research",max_evidence_documents=2),
            semantic_request_fn=lambda _:synthetic_reply(self.a),
            official_response_fn=search,
            evidence_read_fn=reader,
            evidence_model_fn=lambda packet:judgment(packet["claim"]))
        ids=[record["claim_id"] for record in
             result["private_details"]["evidence_scope_audits"]]
        self.assertEqual(ids,["C00001","C00002"])
        self.assertEqual(result["metrics"]["scoped_evidence_audits"],2)
        self.assertIn("PRIMARY_DOCUMENT_BUDGET_INCOMPLETE",result["blockers"])
        self.assertEqual(result["approved_claims"],0)



if __name__=="__main__":
    unittest.main()
