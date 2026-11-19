"""Synthetic protocol checks only: NO model runs, NO real E4/V123 approval."""
import copy
import tempfile
import unittest
from pathlib import Path

from test_v167_chat_research_loop import fixture, evidence, reviewer
from v166_e4_full_video_readiness import h
from v167_chat_research_loop import prepare_open_docket
from v169_chat_research_journal import ChatReviewJournal
from v170_evidence_revisit import EvidenceRevisitJournal
from v171_in_chat_revisit_bridge import (prepare_revisit_chat_turn,
                                         commit_revisit_chat_turn)


class InChatRevisitTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        raw, cues, segments = fixture()
        docket = prepare_open_docket(raw, cues, segments,
                       expected_source_sha256=h(raw), as_of="2026-11-19")
        self.j = ChatReviewJournal(Path(self.t.name)/"private.sqlite", docket)
        self.j.run_round(evidence_retriever=lambda _: [],
             chat_reviewer=lambda q: reviewer(q, "KEEP_OPEN"), limit=2)
        self.r = EvidenceRevisitJournal(self.j)
        self.cid = docket["items"][0]["claim_id"]
        self.prepared = prepare_revisit_chat_turn(self.r, self.cid,
                                                   evidence_retriever=evidence)
        self.reply = reviewer(self.prepared.challenge["request"],
                              "CANDIDATE_NEEDS_NATIVE_REVIEW")

    def test_01_actual_two_step_uses_passed_response_only(self):
        self.assertFalse(self.prepared.challenge["python_called_any_model"])
        self.assertNotIn("body", self.prepared.challenge["request"]["evidence"][0])
        receipt = commit_revisit_chat_turn(self.r, self.prepared, self.reply)
        self.assertEqual(receipt["revisit_events_total"], 1)
        self.assertEqual(receipt["candidates_needing_native_review"], 1)
        self.assertFalse(receipt["knowledge_published"])
        self.assertFalse(receipt["native_v123_approved"])
        self.assertEqual(self.j.status()["processed_count"], 2)

    def test_02_missing_review_is_not_generated_by_python(self):
        with self.assertRaisesRegex(ValueError, "REVIEW_RESPONSE_WRONG_CLAIM"):
            commit_revisit_chat_turn(self.r, self.prepared, None)
        self.assertEqual(self.r.status()["revisit_events"], 0)

    def test_03_cannot_commit_same_prepared_revisit_twice(self):
        commit_revisit_chat_turn(self.r, self.prepared, self.reply)
        with self.assertRaisesRegex(ValueError, "NOT_STILL_OPEN|STALE_SOURCE"):
            commit_revisit_chat_turn(self.r, self.prepared, self.reply)
        self.assertEqual(self.r.status()["revisit_events"], 1)

    def test_04_hash_bound_raw_bytes_reject_substitution(self):
        prepared = copy.deepcopy(self.prepared)
        prepared.raw_evidence[0]["body"] = b"spoofed PDF original bytes"*8
        with self.assertRaisesRegex(ValueError, "REQUEST_OR_RAW_EVIDENCE_MUTATED|EVIDENCE_QUOTE_NOT_IN_BYTES"):
            commit_revisit_chat_turn(self.r, prepared, self.reply)
        self.assertEqual(self.r.status()["revisit_events"], 0)

    def test_05_request_bound_reviewer_no_wrong_claim_or_request(self):
        answer = copy.deepcopy(self.reply)
        answer["request_sha256"] = "f"*64
        with self.assertRaisesRegex(ValueError, "REVIEW_RESPONSE_WRONG_CLAIM"):
            commit_revisit_chat_turn(self.r, self.prepared, answer)
        self.assertEqual(self.r.status()["revisit_events"], 0)

    def test_06_no_false_model_or_e4_authentication(self):
        answer = copy.deepcopy(self.reply)
        answer["chat_reviewer_identity_attested"] = True
        with self.assertRaisesRegex(ValueError, "CHAT_SEMANTIC_OR_AUTHORITY_NOT_SAFE"):
            commit_revisit_chat_turn(self.r, self.prepared, answer)
        self.assertEqual(self.r.status()["revisit_events"], 0)

    def test_07_old_evidence_cannot_be_reused_after_keep_open(self):
        keep = reviewer(self.prepared.challenge["request"], "KEEP_OPEN")
        commit_revisit_chat_turn(self.r, self.prepared, keep)
        with self.assertRaisesRegex(ValueError, "NO_PREVIOUSLY_UNSEEN_EVIDENCE_BODY"):
            prepare_revisit_chat_turn(self.r, self.cid, evidence_retriever=evidence)
        self.assertEqual(self.r.status()["revisit_events"], 1)

    def test_08_tampered_challenge_fails_without_sqlite_write(self):
        prepared = copy.deepcopy(self.prepared)
        prepared.challenge["request"]["task"]["source_context"][0]["text"]="FAKE"
        with self.assertRaisesRegex(ValueError, "CHALLENGE_TAMPERED"):
            commit_revisit_chat_turn(self.r, prepared, self.reply)
        self.assertEqual(self.r.status()["revisit_events"], 0)

    def test_09_advance_first_pass_invalidates_prepared_request(self):
        # The synthetic docket has only 2 atoms, both already reviewed; force
        # an unrelated revisit head advance in the private DB.
        other = self.j.docket["items"][1]["claim_id"]
        self.r.run_revisit(other, evidence_retriever=evidence,
                           chat_reviewer=lambda q: reviewer(q,"KEEP_OPEN"))
        with self.assertRaisesRegex(ValueError, "STALE_SOURCE_OR_REVISIT_STATE"):
            commit_revisit_chat_turn(self.r, self.prepared, self.reply)
        self.assertEqual(self.r.status()["revisit_events"], 1)

    def test_10_prepared_secret_raw_bytes_never_in_public_challenge(self):
        import json
        self.assertNotIn("Synthetic evidence", json.dumps(self.prepared.challenge))
        self.assertIn("source_refs", self.prepared.challenge["request"]["task"])
        self.assertIn("source_context", self.prepared.challenge["request"]["task"])


if __name__ == "__main__": unittest.main()