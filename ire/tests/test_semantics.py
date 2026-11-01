"""Tests of real semantic runner integration via a clearly labeled injected mock.

They never claim an external model actually interpreted a real video.
"""
import copy
import unittest
from ire.semantics import (
    InferenceConfig,interpret_original,assemble_window,
    _extract_response_text,PROMPT_VERSION)
from ire.source import source_record,sha256
from test_engine import VID,synthetic_srt,annotations


def synthetic_reply(annotation):
    return {
        "claims":[{
            "proposition":c["proposition"],
            "claim_types":c["claim_types"],
            "frame":copy.deepcopy(c["frame"]),
            "source_refs":copy.deepcopy(c["source_refs"])
        } for c in annotation["claims"]],
        "cue_dispositions":[
            {"cue_index":c["cue_index"],"status":c["status"],
             "reason":c["reason"]}
            for c in annotation["cue_dispositions"]]
    }


class SemanticInferenceTests(unittest.TestCase):
    def setUp(self):
        self.raw,self.digest=synthetic_srt()
        self.cfg=InferenceConfig(model="development-mock-01")

    def test_source_only_multicue_interpretation(self):
        annotated=annotations(self.digest)
        observed=[]
        def simulated_model(payload):
            observed.append(payload)
            return synthetic_reply(annotated)
        result=interpret_original(self.raw,VID,self.cfg,simulated_model)
        self.assertEqual(result["inference_mode"],"SYNTHETIC_INJECTED_MOCK")
        self.assertEqual(result["window_count"],1)
        self.assertEqual(result["validation"]["proposed_atomic_claims"],2)
        self.assertFalse(result["independent_human_gold_review"])
        self.assertEqual(observed[0]["primary_cues"][0]["text"],"상품 비용은")
        self.assertNotIn("historic",str(observed).lower())
        self.assertEqual(observed[0]["task"],PROMPT_VERSION)
        first=result["annotation_manifest"]["claims"][0]
        self.assertEqual([x["cue_index"] for x in first["source_refs"]],[1,2])
        self.assertEqual(result["approved_claims"],0)

    def test_missing_api_credentials_fail_closed(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,"SEMANTIC_API_KEY_UNAVAILABLE"):
                interpret_original(self.raw,VID,self.cfg)

    def test_llm_hallucination_rejected(self):
        annotated=annotations(self.digest)
        reply=synthetic_reply(annotated)
        reply["claims"][1]["source_refs"][0]["quote"]="실제로 보장되는 50% 수익률"
        with self.assertRaisesRegex(ValueError,"UNTRACEABLE_QUOTED_SOURCE"):
            interpret_original(self.raw,VID,self.cfg,lambda _:reply)

    def test_response_cue_omission_rejected(self):
        annotated=annotations(self.digest)
        reply=synthetic_reply(annotated)
        reply["cue_dispositions"].pop()
        with self.assertRaisesRegex(ValueError,"SEMANTIC_WINDOW_OUTPUT_CENSUS_INVALID"):
            interpret_original(self.raw,VID,self.cfg,lambda _:reply)

    def test_invalid_private_source_or_scope_rejected(self):
        annotated=annotations(self.digest)
        reply=synthetic_reply(annotated)
        reply["claims"][0]["source_refs"][0]["cue_index"]=95
        with self.assertRaisesRegex(ValueError,"CLAIM_SOURCE_OUTSIDE_PRIMARY_CUES"):
            interpret_original(self.raw,VID,self.cfg,lambda _:reply)

    def test_model_output_does_not_approve_truth(self):
        a=annotations(self.digest)
        reply=synthetic_reply(a)
        reply["claims"][0]["annotation_status"]="APPROVED"
        with self.assertRaisesRegex(ValueError,"SEMANTIC_CLAIM_OUTPUT_SCHEMA_MISMATCH"):
            interpret_original(self.raw,VID,self.cfg,lambda _:reply)

    def test_bounded_request_and_secure_endpoint(self):
        with self.assertRaisesRegex(ValueError,"SEMANTIC_API_ALLOWLIST_VIOLATION"):
            InferenceConfig(model="development-mock-01",api_url=
                "https://evil.example/v1/responses").validate()
        with self.assertRaisesRegex(ValueError,"SEMANTIC_WINDOW_BUDGET_EXCEEDED"):
            interpret_original(self.raw,VID,self.cfg,lambda _:None,max_total_windows=0)

    def test_remote_response_output_must_be_single_json(self):
        self.assertEqual(
            _extract_response_text({
                "status":"completed",
                "output":[{"type":"reasoning","summary":[]},
                          {"type":"message","content":[
                              {"type":"output_text","text":"{}"}]}]
            }),"{}")
        with self.assertRaisesRegex(ValueError,"SEMANTIC_RESPONSE_NOT_COMPLETED"):
            _extract_response_text({"status":"incomplete","output":[]})

    def test_oversized_source_fails(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_SHA256_MISMATCH"):
            interpret_original(self.raw+b"fabrication",VID,self.cfg,lambda _:None) if False else __import__("ire.source",fromlist=["parse_srt"]).parse_srt(self.raw+b"x",self.digest)


    def test_actual_http_client_request_contract_offline(self):
        import json
        from unittest.mock import patch
        from ire.semantics import openai_responses_request
        class MockResponse:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,max_bytes):
                return json.dumps({
                    "status":"completed",
                    "output":[{"type":"message","content":[
                        {"type":"output_text","text":
                         '{"claims":[],"cue_dispositions":[]}'}]}]
                }).encode()
        captured={}
        def no_network(request,timeout):
            captured["url"]=request.full_url
            captured["auth"]=request.get_header("Authorization")
            captured["payload"]=json.loads(request.data)
            return MockResponse()
        with patch("urllib.request.urlopen",side_effect=no_network):
            result=openai_responses_request(self.cfg,
                {"video_id":VID,"primary_cues":[]}, "development-placeholder-only")
        self.assertEqual(result["claims"],[])
        self.assertEqual(captured["url"],"https://api.openai.com/v1/responses")
        self.assertEqual(captured["auth"],"Bearer development-placeholder-only")
        self.assertFalse(captured["payload"]["store"])
        self.assertEqual(captured["payload"]["text"]["format"]["type"],"json_schema")
        self.assertTrue(captured["payload"]["text"]["format"]["strict"])
        self.assertEqual(set(captured["payload"]["text"]["format"]["schema"]["required"]),{"claims","cue_dispositions"})
        self.assertNotIn("development-placeholder-only",json.dumps(captured["payload"]))

    def test_actual_http_client_fails_on_incomplete_output_offline(self):
        import json
        from unittest.mock import patch
        from ire.semantics import openai_responses_request
        class MockResponse:
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self,max_bytes):
                return b'{"status":"incomplete","output":[]}'
        with patch("urllib.request.urlopen",return_value=MockResponse()):
            with self.assertRaisesRegex(ValueError,"SEMANTIC_RESPONSE_INVALID_JSON"):
                openai_responses_request(self.cfg,{"primary_cues":[]}, "test-placeholder")


if __name__=="__main__":
    unittest.main()
