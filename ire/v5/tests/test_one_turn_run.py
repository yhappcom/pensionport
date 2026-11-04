"""One-turn engine issues a research receipt only after all checks pass."""
import contextlib
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from ire.v5 import one_turn_run

ROOT=Path(__file__).resolve().parents[3]

class SingleRequestOrchestratorTests(unittest.TestCase):
    def test_real_one_turn_all_gates_emit_terminal_receipt(self):
        output=io.StringIO()
        with patch.object(one_turn_run,"preflight_run",return_value=0) as p, \
             contextlib.redirect_stdout(output):
            rc=one_turn_run.run(ROOT)
        self.assertEqual(rc,0)
        p.assert_called_once()
        row=output.getvalue().split("ONE_TURN_RESEARCH_RECEIPT ",1)[1]
        payload=json.loads(row)
        self.assertTrue(payload["one_request_research_complete"])
        self.assertFalse(payload["repeat_user_progress_command_required"])
        self.assertEqual(payload["claims"]["claims_without_disposition"],0)
        self.assertFalse(payload["formal_personal_investment_advice_authorized"])
        self.assertFalse(payload["independent_human_blind_evaluation_completed"])

    def test_no_receipt_on_preflight_error(self):
        output=io.StringIO()
        with patch.object(one_turn_run,"preflight_run",return_value=9), \
             contextlib.redirect_stdout(output):
            rc=one_turn_run.run(ROOT)
        self.assertEqual(rc,9)
        self.assertNotIn("ONE_TURN_RESEARCH_RECEIPT {",output.getvalue())
        self.assertIn("NOT_ISSUED",output.getvalue())

    def test_no_external_api_calls_or_fake_blind_approval(self):
        import inspect
        source=inspect.getsource(one_turn_run)
        self.assertNotIn("openai.com/v1",source)
        self.assertIn("ACTIVE_CHAT_HOST_MUST_SUPPLY",source)
        self.assertIn('"formal_personal_investment_advice_authorized":False',source)

if __name__=="__main__":
    unittest.main()
