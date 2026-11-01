"""Entire one-command orchestration: real integration surfaces, synthetic only.

A test passing does not imply the model understood a finance video or that
primary evidence, meaning, or independent review has been certified.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from ire.source import sha256
from ire.orchestrator import (STAGE_ORDER,OrchestrationPolicy,
                              execute_independent_research)
from ire.one_shot import execute_batch,items_from_options
from test_engine import VID,synthetic_srt,annotations
from test_semantics import synthetic_reply


def mock_official(claim):
    """The web tool ran and a cited official-domain URL was returned."""
    return {
        "status":"completed",
        "output":[
            {"type":"web_search_call","status":"completed"},
            {"type":"message","content":[{
                "type":"output_text","text":"Candidate site returned, not validated.",
                "annotations":[{
                    "type":"url_citation",
                    "url":"https://www.bok.or.kr/portal/main/main.do"
                },{
                    "type":"url_citation",
                    "url":"https://example.com/unverified"
                }]}]}
        ]
    }


class OrchestrationIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.raw,self.digest=synthetic_srt()
        self.a=annotations(self.digest)
        self.fn=lambda _:synthetic_reply(self.a)

    def test_one_invocation_no_model_finishes_with_blockers(self):
        result=execute_independent_research(self.raw,VID,self.digest,
                                            OrchestrationPolicy())
        self.assertTrue(result["single_invocation_execution_finished"])
        self.assertEqual([x["stage"] for x in result["stages"]],
                         list(STAGE_ORDER))
        self.assertEqual(result["stages"][0]["status"],"PASSED")
        self.assertEqual(result["stages"][1]["status"],"BLOCKED")
        self.assertIn("SEMANTIC_MODEL_NOT_CONFIGURED",result["blockers"])
        self.assertFalse(result["automatic_knowledge_merge"])
        self.assertEqual(result["approved_claims"],0)

    def test_model_missing_secret_gives_terminal_report(self):
        p=OrchestrationPolicy(model="some-verified-model")
        with patch.dict(os.environ,{},clear=True):
            r=execute_independent_research(self.raw,VID,self.digest,p)
        self.assertEqual(r["stages"][1]["status"],"BLOCKED")
        self.assertIn("SEMANTIC_API_KEY_UNAVAILABLE",r["blockers"])
        self.assertIsNone(r["metrics"]["proposed_financial_atoms"])

    def test_full_pipeline_with_mock_is_not_financial_approval(self):
        p=OrchestrationPolicy(model="mock-model")
        result=execute_independent_research(
            self.raw,VID,self.digest,p,
            semantic_request_fn=self.fn,
            official_response_fn=mock_official)
        self.assertEqual(len(result["stages"]),len(STAGE_ORDER))
        self.assertEqual(result["metrics"]["source_cue_count"],4)
        self.assertEqual(result["metrics"]["proposed_financial_atoms"],2)
        self.assertEqual(result["metrics"]["official_search_candidates"],2)
        self.assertEqual(result["metrics"]["retrieval_candidate_queries"],2)
        self.assertEqual(result["stages"][1]["status"],
                         "PROPOSALS_GENERATED_UNVERIFIED")
        self.assertEqual(result["stages"][3]["status"],
                         "CANDIDATES_ONLY_NOT_VERIFIED")
        self.assertEqual(result["stages"][4]["status"],
                         "WORKLIST_BUILT_UNVERIFIED")
        self.assertEqual(result["stages"][5]["status"],
                         "CANDIDATES_ONLY_NOT_VERIFIED")
        self.assertIn("TWO_INDEPENDENT_BLIND_REVIEWERS_NOT_ATTESTED",
                      result["blockers"])
        self.assertTrue(result["previous_research_results_cited"] is False)
        self.assertEqual(result["approved_claims"],0)
        self.assertFalse(result["factual_truth_certified"])
        self.assertFalse(result["private_details"]["official_source_candidates"][
            0]["document_text_independently_fetched"])

    def test_hallucinated_source_causes_final_block_not_approval(self):
        bad=synthetic_reply(self.a)
        bad["claims"][0]["source_refs"][0]["quote"]="보장되는 천 퍼센트"
        p=OrchestrationPolicy(model="mock")
        r=execute_independent_research(self.raw,VID,self.digest,p,
                                       semantic_request_fn=lambda _:bad)
        self.assertEqual(r["stages"][1]["status"],"BLOCKED")
        self.assertIn("UNTRACEABLE_QUOTED_SOURCE",r["blockers"])
        self.assertEqual(r["approved_claims"],0)
        self.assertEqual(r["stages"][-1]["status"],"COMPLETED_BLOCKED")

    def test_transient_model_error_retried_in_same_invocation(self):
        calls=[]
        def fail_once(data):
            calls.append(data["window_id"])
            if len(calls)==1:raise ValueError("SEMANTIC_API_UNAVAILABLE")
            return self.fn(data)
        pauses=[]
        p=OrchestrationPolicy(model="mock",max_model_attempts=2)
        r=execute_independent_research(
            self.raw,VID,self.digest,p,semantic_request_fn=fail_once,
            official_response_fn=mock_official,sleep_fn=pauses.append)
        self.assertEqual(len(calls),2)
        self.assertEqual(pauses,[1])
        self.assertEqual(r["metrics"]["proposed_financial_atoms"],2)

    def test_nontransient_failure_not_repeated(self):
        attempts=[]
        def invalid(data):
            attempts.append(1)
            raise ValueError("UNTRACEABLE_QUOTED_SOURCE")
        p=OrchestrationPolicy(model="mock",max_model_attempts=5)
        r=execute_independent_research(self.raw,VID,self.digest,p,
                                       semantic_request_fn=invalid)
        self.assertEqual(len(attempts),1)
        self.assertIn("UNTRACEABLE_QUOTED_SOURCE",r["blockers"])

    def test_official_budget_is_explicit_block(self):
        p=OrchestrationPolicy(model="mock",max_discovery_claims=1)
        r=execute_independent_research(
            self.raw,VID,self.digest,p,semantic_request_fn=self.fn,
            official_response_fn=mock_official)
        self.assertEqual(r["stages"][3]["status"],"BLOCKED_BUDGET")
        self.assertIn("RESEARCH_CLAIM_BUDGET_EXCEEDED",r["blockers"])
        self.assertEqual(r["metrics"]["official_search_candidates"],0)
        self.assertEqual(r["metrics"]["retrieval_candidate_queries"],2)

    def test_exact_source_hash_fails_closed(self):
        r=execute_independent_research(self.raw,VID,sha256(b"different"),
                                       OrchestrationPolicy())
        self.assertEqual(r["stages"][0]["status"],"FAILED_CLOSED")
        self.assertEqual(r["metrics"]["source_cue_count"],None)
        self.assertFalse(r["factual_truth_certified"])
        self.assertIn("SOURCE_SHA256_MISMATCH",r["blockers"])

    def test_single_source_batch_and_immutable_rerun(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            original=root/"new_original.srt"
            original.write_bytes(self.raw)
            out=root/"reports"
            inputs=[{"video_id":VID,"original_srt_path":str(original),
                     "source_sha256":self.digest}]
            policy=OrchestrationPolicy(model="mock")
            first=execute_batch(
                inputs,str(out),policy,
                semantic_request_fn=self.fn,official_response_fn=mock_official)
            second=execute_batch(
                inputs,str(out),policy,
                semantic_request_fn=self.fn,official_response_fn=mock_official)
            a,b=first["entries"][0]["report_path"],second["entries"][0]["report_path"]
            self.assertNotEqual(a,b)
            self.assertEqual(first["video_count"],1)
            self.assertEqual(second["video_count"],1)
            self.assertEqual(Path(a).stat().st_mode & 0o077,0)
            self.assertEqual(Path(b).stat().st_mode & 0o077,0)
            before=json.loads(Path(a).read_text())
            after=json.loads(Path(b).read_text())
            self.assertEqual(before["run_fingerprint"],after["run_fingerprint"])
            self.assertFalse(before["automatic_knowledge_merge"])
            self.assertEqual(first["private_reports_written"],1)
            self.assertEqual(first["research_release"],"BLOCKED")

    def test_cli_real_one_command_blocked_but_report_written(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            original=root/"original.srt"
            original.write_bytes(self.raw)
            output=root/"output"
            cmd=[sys.executable,"-m","ire.one_shot",
                 "--original-srt",str(original),
                 "--video-id",VID,
                 "--source-sha256",self.digest,
                 "--private-output-dir",str(output)]
            environment={k:v for k,v in os.environ.items()
                         if k!="OPENAI_API_KEY"}
            result=subprocess.run(cmd,check=False,capture_output=True,text=True,
                                  env=environment)
            self.assertEqual(result.returncode,2,result.stderr)
            public=json.loads(result.stdout)
            self.assertEqual(public["video_count"],1)
            self.assertEqual(public["approved_financial_claims"],0)
            self.assertIn("SEMANTIC_MODEL_NOT_CONFIGURED",
                          public["results"][0]["blockers"])
            self.assertNotIn("상품 비용은",result.stdout)
            summary=json.loads(Path(public["private_summary_path"]).read_text())
            self.assertEqual(len(summary["entries"]),1)
            report=json.loads(Path(summary["entries"][0]["report_path"]).read_text())
            self.assertTrue(report["single_invocation_execution_finished"])
            self.assertEqual(len(report["stages"]),8)


if __name__=="__main__":
    unittest.main()
