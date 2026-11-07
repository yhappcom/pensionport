"""Batch API regression: bounded source packets and atomic model submission."""
import json
from urllib.error import HTTPError
from ire.v5_app.tests.test_server import AppServerTests
from ire.v5.tests.test_engine import V5ContractTests, SRT, MAN
from ire.v5.engine import ResearchRun

class BatchAPIRegression(AppServerTests):
    def test_source_bundle_and_single_batch_receipt(self):
        packet=json.load(self.request("/v1/next-bundle"))
        self.assertEqual(len(packet["packets"]),3)
        self.assertTrue(packet["requires_live_chat_interpretation"])
        self.r=ResearchRun(SRT,MAN,self.app.root)
        actions=[{"type":"MODEL_ANALYSIS",
                  "payload":V5ContractTests.model(self,i)} for i in (1,2,3)]
        request={"event_type":"BATCH_ACCEPT",
                 "payload":{"schema":"IRE_V5_ACTION_BUNDLE_V1","actions":actions},
                 "expected_chain_head":packet["expected_chain_head"],
                 "expected_task_sha256":packet["expected_task_sha256"]}
        result=json.load(self.request("/v1/receipt",request))
        self.assertEqual(result["receipt_sequence"],1)
        self.assertEqual(result["next_phase"],"OFFICIAL_EVIDENCE_REVIEW_REQUIRED")
        self.assertEqual(self.app.state()["research"]["submitted_windows"],3)
        self.assertEqual(self.app.state()["research"]["approved_financial_facts"],0)
        with self.assertRaises(HTTPError) as err:
            self.request("/v1/receipt",request)
        self.assertEqual(err.exception.code,409)
