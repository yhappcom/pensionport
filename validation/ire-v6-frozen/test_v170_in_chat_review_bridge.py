"""V170 synthetic protocol tests against actual V167/V169 journal, not model calls."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from test_v167_chat_research_loop import fixture, evidence, reviewer
from v166_e4_full_video_readiness import h
from v167_chat_research_loop import prepare_open_docket
from v169_chat_research_journal import ChatReviewJournal
from v170_in_chat_review_bridge import prepare_chat_batch, ingest_chat_responses


class V170LiveChatReviewContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        raw, cues, segments = fixture()
        self.docket = prepare_open_docket(raw, cues, segments,
            expected_source_sha256=h(raw), as_of="2026-11-19")
        self.path = Path(self.tmp.name) / "private-review.sqlite"
        self.journal = ChatReviewJournal(self.path, self.docket)

    def packet(self, limit=1, with_evidence=False):
        tasks = self.journal.next_tasks(limit)
        self.evidences = {task["claim_id"]:
            evidence(task) if with_evidence else [] for task in tasks}
        return prepare_chat_batch(self.journal,
            evidence_by_claim=self.evidences, limit=limit)

    def answers(self, packet, decision="KEEP_OPEN"):
        return [reviewer(request, decision) for request in packet["requests"]]

    def ingest(self, packet, responses=None):
        return ingest_chat_responses(self.journal, prepared_batch=packet,
            evidence_by_claim=self.evidences,
            chat_responses=self.answers(packet) if responses is None else responses)

    def test_01_one_in_chat_review_persists_only_unreleased(self):
        packet = self.packet()
        self.assertEqual(len(packet["requests"]), 1)
        self.assertTrue(packet["requests"][0]["task"]["source_context"])
        saved = self.ingest(packet)
        self.assertEqual((saved["processed_count"], saved["remaining_count"]), (1, 1))
        self.assertFalse(saved["e4_approved"])
        self.assertFalse(saved["knowledge_publication_authorized"])

    def test_02_restart_second_request_has_new_pinned_cursor(self):
        batch1 = self.packet()
        self.ingest(batch1)
        restart = ChatReviewJournal(self.path, self.docket)
        task = restart.next_tasks(limit=1)[0]
        ev = {task["claim_id"]: []}
        batch2 = prepare_chat_batch(restart, evidence_by_claim=ev, limit=1)
        self.assertNotEqual(batch1["batch_sha256"], batch2["batch_sha256"])
        answer = [reviewer(batch2["requests"][0], "KEEP_OPEN")]
        result = ingest_chat_responses(restart, prepared_batch=batch2,
            evidence_by_claim=ev, chat_responses=answer)
        self.assertEqual(result["processed_count"], 2)
        self.assertEqual(restart.status()["remaining_count"], 0)

    def test_03_duplicate_batch_replay_blocked_no_extra_write(self):
        packet = self.packet()
        self.ingest(packet)
        with self.assertRaisesRegex(ValueError, "STALE_OR_CHANGED_REVIEW_CONTEXT"):
            self.ingest(packet)
        self.assertEqual(self.journal.status()["processed_count"], 1)

    def test_04_fake_request_sha_rejected(self):
        packet = self.packet()
        bad = self.answers(packet)
        bad[0]["request_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "CHAT_DECISION_PIN_MISMATCH"):
            self.ingest(packet, bad)
        self.assertEqual(self.journal.status()["processed_count"], 0)

    def test_05_fake_chat_identity_claim_rejected(self):
        packet = self.packet()
        bad = self.answers(packet)
        bad[0]["chat_reviewer_identity_attested"] = True
        with self.assertRaisesRegex(ValueError, "CHAT_SEMANTIC_OR_AUTHORITY_NOT_SAFE"):
            self.ingest(packet, bad)
        self.assertEqual(self.journal.status()["processed_count"], 0)

    def test_06_batch_metadata_tamper_rejected(self):
        packet = self.packet()
        packet["requests"][0]["task"]["source_context"][0]["text"] = "fabricated"
        with self.assertRaisesRegex(ValueError, "REVIEW_BATCH_TAMPERED"):
            self.ingest(packet)

    def test_07_change_evidence_body_between_prep_and_ingest(self):
        packet = self.packet(with_evidence=True)
        altered = copy.deepcopy(self.evidences)
        claim = next(iter(altered))
        altered[claim][0]["body"] += b" unverified addition"
        with self.assertRaisesRegex(ValueError, "STALE_OR_CHANGED_REVIEW_CONTEXT"):
            ingest_chat_responses(self.journal, prepared_batch=packet,
                evidence_by_claim=altered,
                chat_responses=self.answers(packet))
        self.assertEqual(self.journal.status()["processed_count"], 0)

    def test_08_missing_or_extra_evidence_map_blocked(self):
        with self.assertRaisesRegex(ValueError, "EVIDENCE_EXACT_TASK_CENSUS"):
            prepare_chat_batch(self.journal, evidence_by_claim={}, limit=1)
        with self.assertRaisesRegex(ValueError, "EVIDENCE_EXACT_TASK_CENSUS"):
            prepare_chat_batch(self.journal, evidence_by_claim={"C99999":[]}, limit=1)

    def test_09_missing_answer_or_duplicate_answer_blocked(self):
        packet = self.packet(limit=2)
        answers = self.answers(packet)
        for variant in (answers[:1], [answers[0], answers[0]]):
            with self.subTest(length=len(variant)), self.assertRaisesRegex(
                ValueError, "ANSWER_ORDER_OR_CENSUS_MISMATCH"):
                self.ingest(packet, variant)
        self.assertEqual(self.journal.status()["processed_count"], 0)

    def test_10_batch_second_bad_answer_rolls_back_both(self):
        packet = self.packet(limit=2)
        answers = self.answers(packet)
        answers[1]["conditions_checked"] = False
        with self.assertRaisesRegex(ValueError, "CHAT_SEMANTIC_OR_AUTHORITY_NOT_SAFE"):
            self.ingest(packet, answers)
        self.assertEqual(self.journal.status()["processed_count"], 0)

    def test_11_candidate_with_evidence_is_not_approval(self):
        packet = self.packet(with_evidence=True)
        saved = self.ingest(packet, self.answers(packet, "CANDIDATE_NEEDS_NATIVE_REVIEW"))
        p = self.journal.export_unreleased_proposals()
        self.assertEqual(p["candidate_proposals"], 1)
        self.assertFalse(saved["e4_approved"])
        self.assertFalse(p["native_v123_status_changed"])
        self.assertFalse(p["knowledge_publication_authorized"])

    def test_12_candidate_without_evidence_blocked(self):
        packet = self.packet()
        with self.assertRaisesRegex(ValueError, "CANDIDATE_WITHOUT_SOURCE"):
            self.ingest(packet, self.answers(packet, "CANDIDATE_NEEDS_NATIVE_REVIEW"))
        self.assertEqual(self.journal.status()["processed_count"], 0)

    def test_13_unauthenticated_provenance_never_became_primary(self):
        packet = self.packet(with_evidence=True)
        req = packet["requests"][0]
        self.assertTrue(req["source_provenance_and_statutory_scope_not_yet_authenticated"])
        self.assertFalse(req["evidence"][0]["provenance_authenticated"])
        self.assertFalse(req["evidence"][0]["finance_rule_applicability_verified"])

    def test_14_no_review_tasks_cannot_ingest(self):
        packet = self.packet(limit=2)
        self.ingest(packet)
        empty = prepare_chat_batch(self.journal, evidence_by_claim={}, limit=2)
        self.assertEqual(empty["requests"], [])
        with self.assertRaisesRegex(ValueError, "NO_REVIEW_TASKS_TO_INGEST"):
            ingest_chat_responses(self.journal, prepared_batch=empty,
                evidence_by_claim={}, chat_responses=[])

    def test_15_source_root_mismatch_resume_rejected(self):
        packet = self.packet()
        packet["root_docket_sha256"] = "1" * 64
        from v166_e4_full_video_readiness import digest
        packet["batch_sha256"] = digest({k:v for k,v in packet.items() if k!="batch_sha256"})
        with self.assertRaisesRegex(ValueError, "STALE_OR_CHANGED_REVIEW_CONTEXT"):
            self.ingest(packet)
        self.assertEqual(self.journal.status()["processed_count"], 0)


if __name__ == "__main__":
    unittest.main()