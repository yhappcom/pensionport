"""Two-phase literal ChatGPT answer transport -> real native V123 -> E4 HOLD.

All decisions here are SYNTHETIC and are fed as literal JSON through V170.
The frozen V123 implementation (not a mock) judges the resulting native row.
"""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from ire.v6.errors import InvalidInput
from test_v168_chat_native_replay import V168NativeBridgeTests, proposal_reviewer
from v168_chat_native_replay import compile_and_replay_native
from v169_chat_research_journal import ChatReviewJournal
from v170_in_chat_review_bridge import prepare_chat_batch, ingest_chat_responses
from v166_e4_primary_approval_gate import assess_e4_primary_authority_gate


class V170NativeReviewBoundaryTests(unittest.TestCase):
    def setUp(self):
        fx = V168NativeBridgeTests("test_01_no_changes_replayed_real_native_v123_hold")
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        self.fx = fx
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.journal = ChatReviewJournal(Path(self.tmp.name)/"private.sqlite", fx.docket)
        self.old_review = copy.deepcopy(fx.case["chat_review"])

    def run_host(self, decision, provide_evidence):
        task = self.journal.next_tasks(1)[0]
        evidence_map = {task["claim_id"]: self.fx.evidence(task) if provide_evidence else []}
        batch = prepare_chat_batch(self.journal, evidence_by_claim=evidence_map, limit=1)
        reply = [proposal_reviewer(batch["requests"][0], decision)]
        saved = ingest_chat_responses(self.journal, prepared_batch=batch,
            evidence_by_claim=evidence_map, chat_responses=reply)
        return saved, self.journal.export_unreleased_proposals()

    def test_01_literal_chat_open_to_native_v123_hold(self):
        saved, proposals = self.run_host("KEEP_OPEN", False)
        actual = compile_and_replay_native(self.fx.docket, proposals,
            cases_by_segment={"B0001": self.fx.case})
        native = actual["receipt"]["native_results"][0]
        self.assertEqual(native["native_status"], "CHAT_FINAL_HOLD_OPEN")
        self.assertEqual(actual["receipt"]["native_rows_changed"], 0)
        self.assertFalse(saved["knowledge_publication_authorized"])
        self.assertFalse(actual["receipt"]["e4_approved"])
        self.assertEqual(self.fx.case["chat_review"], self.old_review)

    def test_02_literal_chat_candidate_cannot_bypass_secondary_or_e4(self):
        saved, proposals = self.run_host("CANDIDATE_NEEDS_NATIVE_REVIEW", True)
        self.assertEqual(proposals["candidate_proposals"], 1)
        with self.assertRaisesRegex(InvalidInput, "SECONDARY_CHAT_REQUIRED"):
            compile_and_replay_native(self.fx.docket, proposals,
                cases_by_segment={"B0001": self.fx.case})
        secondary = {self.fx.claim: self.fx.secondary(proposals)}
        actual = compile_and_replay_native(self.fx.docket, proposals,
            cases_by_segment={"B0001": self.fx.case},
            secondary_chat_reviews=secondary)
        self.assertEqual(actual["receipt"]["native_results"][0]["native_status"],
                         "CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY")
        private_case = {**self.fx.case,
            "chat_review": actual["native_private_drafts"]["B0001"]["review"]}
        e4 = assess_e4_primary_authority_gate(private_case, None, now_as_of="2026-11-19")
        self.assertEqual(e4["status"], "E4_HOLD_INELIGIBLE_APPROVAL")
        self.assertFalse(saved["e4_approved"])
        self.assertFalse(actual["receipt"]["knowledge_publication_authorized"])
        self.assertEqual(self.fx.case["chat_review"], self.old_review)

    def test_03_literal_chat_reject_is_native_rejected_no_publication(self):
        saved, proposals = self.run_host("REJECT_PROPOSAL", False)
        secondary = {self.fx.claim: self.fx.secondary(proposals, "REJECT")}
        actual = compile_and_replay_native(self.fx.docket, proposals,
            cases_by_segment={"B0001": self.fx.case},
            secondary_chat_reviews=secondary)
        self.assertEqual(actual["receipt"]["native_results"][0]["native_status"],
                         "CHAT_FINAL_REJECTED")
        self.assertFalse(actual["receipt"]["all_native_scopes_pass"])
        self.assertFalse(saved["e5_authorized"])
        self.assertEqual(self.fx.case["chat_review"], self.old_review)


if __name__ == "__main__":
    unittest.main()