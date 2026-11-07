"""P0 regression: context, multi-atom second pass and generic cohort."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from ire.v5.engine import ResearchRun, RunError
from ire.v5.p0_semantic_coverage import contextual_packet, audit_second_pass
from ire.v5.p0_generic_runner import GenericResearchCohort
from ire.v5.tests.test_engine import SRT, MAN, TEXT
from ire.v5.tests.test_batch import fixture_video


class P0SemanticTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.run = ResearchRun(SRT, copy.deepcopy(MAN), self.root / "private")

    def initial_model(self):
        p = self.run.packet("W00001")
        return {"schema": "IRE_V5_MODEL_WINDOW_V1", "window_id": "W00001",
                "claimed_author": "CURRENT_CHATGPT_CONVERSATION",
                "independent_human_verified": False,
                "packet_sha256": p["packet_sha256"],
                "claims": [
                    {"claim_id": "V5C0001", "kind": "RULE",
                     "proposition": "Hypothetical pension amount could differ by person.",
                     "requires_external_verification": True,
                     "fact_verified": False, "advisory_approved": False,
                     "source_refs": [{"cue_index": 1, "quote": TEXT[1]}]},
                    {"claim_id": "V5C0002", "kind": "RULE",
                     "proposition": "Pension assumptions are conditional and variable.",
                     "requires_external_verification": True,
                     "fact_verified": False, "advisory_approved": False,
                     "source_refs": [{"cue_index": 1, "quote": TEXT[1]}]},
                    {"claim_id": "V5C0003", "kind": "OPINION",
                     "proposition": "Income is uncertain in this hypothetical example.",
                     "requires_external_verification": False,
                     "fact_verified": False, "advisory_approved": False,
                     "source_refs": [{"cue_index": 2, "quote": TEXT[2]}]}],
                "cue_dispositions": [
                    {"cue_index": 1, "status": "LINKED",
                     "claim_ids": ["V5C0001", "V5C0002"], "reason": None},
                    {"cue_index": 2, "status": "LINKED",
                     "claim_ids": ["V5C0003"], "reason": None}]}

    def review(self):
        return {"schema": "IRE_V5_P0_SECOND_PASS_V1",
                "video_id": MAN["video_id"], "window_id": "W00001",
                "source_sha256": MAN["source_sha256"],
                "packet_sha256": self.run.packet("W00001")["packet_sha256"],
                "claimed_author": "CURRENT_CHATGPT_CONVERSATION",
                "independent_human_verified": False,
                "units": [
                    {"unit_id": "S0001", "cue_index": 1, "source_quote": TEXT[1],
                     "meaning": "First pension amount qualification statement.",
                     "decision": "CLAIM", "claim_ids": ["V5C0001"]},
                    {"unit_id": "S0002", "cue_index": 1, "source_quote": TEXT[1],
                     "meaning": "Second distinct pension assumption statement.",
                     "decision": "CLAIM", "claim_ids": ["V5C0002"]},
                    {"unit_id": "S0003", "cue_index": 2, "source_quote": TEXT[2],
                     "meaning": "Income may remain uncertain in this scenario.",
                     "decision": "CLAIM", "claim_ids": ["V5C0003"]}]}

    def test_packet_halo_does_not_mutate_legacy_source_or_citation_hash(self):
        legacy = self.run.packet("W00001")
        p = contextual_packet(self.run, "W00001", halo_cues=2)
        self.assertEqual(p["primary_packet"], legacy)
        self.assertEqual(p["original_model_packet_sha256"], legacy["packet_sha256"])
        self.assertEqual([x["cue_index"] for x in p["after"]], [3, 4])
        self.assertEqual(p["context_only_cue_ids"], [3, 4])
        self.assertEqual(contextual_packet(self.run, "W00001"), p)
        with self.assertRaisesRegex(RunError, "P0_CONTEXT_HALO_BUDGET_INVALID"):
            contextual_packet(self.run, "W00001", halo_cues=100)

    def test_two_distinct_atomic_units_on_one_cue_reconciled_but_not_certified(self):
        self.run.append("MODEL_ANALYSIS", self.initial_model())
        result = audit_second_pass(self.run, "W00001", self.review())
        self.assertTrue(result["source_review_reconciled"])
        self.assertEqual(result["review_units"], 3)
        self.assertEqual(result["reconfirmed_initial_claims"], 3)
        self.assertFalse(result["independent_atomic_recall_certified"])

    def test_missing_additional_semantic_claim_never_passes(self):
        self.run.append("MODEL_ANALYSIS", self.initial_model())
        review = self.review()
        review["units"].append({
            "unit_id": "S0004", "cue_index": 1, "source_quote": TEXT[1],
            "meaning": "New material atomic proposition missing from first analysis.",
            "decision": "MISSING_CLAIM", "claim_ids": []})
        result = audit_second_pass(self.run, "W00001", review)
        self.assertFalse(result["source_review_reconciled"])
        self.assertIn("UNRESOLVED_OR_MISSING_ATOMIC_UNITS",
                      [x["reason"] for x in result["review_gaps"]])

    def test_unreviewed_cue_and_replaced_source_are_rejected_or_blocked(self):
        self.run.append("MODEL_ANALYSIS", self.initial_model())
        review = self.review()
        review["units"] = review["units"][:2]
        self.assertFalse(audit_second_pass(self.run, "W00001", review)
                         ["source_review_reconciled"])
        review = self.review()
        review["units"][0]["source_quote"] = "fabricated quote"
        with self.assertRaisesRegex(RunError, "P0_SECOND_PASS_UNIT_OR_QUOTE_INVALID"):
            audit_second_pass(self.run, "W00001", review)

    def test_secondary_review_requires_actual_host_model_record(self):
        with self.assertRaisesRegex(RunError, "P0_SECOND_PASS_REQUIRES_REAL_MODEL_ANALYSIS"):
            audit_second_pass(self.run, "W00001", self.review())


class P0GenericRunnerTests(unittest.TestCase):
    def test_unseen_one_video_reopen_and_context_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = fixture_video(1)
            cohort = GenericResearchCohort([
                {"video_id": row["manifest"]["video_id"],
                 "source": row["source"],
                 "prior_baseline_git_blob_sha": "a" * 40}], Path(tmp) / "private")
            state = cohort.status()
            self.assertEqual(state["video_count"], 1)
            self.assertEqual(state["source_windows_with_model"], 0)
            task = cohort.next_required_task()["tasks"][0]
            self.assertEqual(task["task"]["phase"], "MODEL_ANALYSIS_REQUIRED")
            packet = cohort.next_source_tasks(max_windows=2)["items"][0]
            self.assertIn("primary_packet", packet["contextual_packet"])
            restored = GenericResearchCohort.reopen(Path(tmp) / "private")
            self.assertEqual(state, restored.status())
            self.assertFalse(restored.status()["llm_or_web_executed_by_this_module"])

    def test_duplicate_video_and_original_tamper_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = fixture_video(2)
            one = {"video_id": row["manifest"]["video_id"],
                   "source": row["source"],
                   "prior_baseline_git_blob_sha": "a" * 40}
            with self.assertRaisesRegex(RunError, "P0_GENERIC_VIDEO_ID_DUPLICATE"):
                GenericResearchCohort([one, one], Path(tmp) / "dup")
            src = Path(tmp) / "ok"
            GenericResearchCohort([one], src)
            (src / one["video_id"] / "original.srt").write_bytes(b"tamper")
            with self.assertRaises(RunError):
                GenericResearchCohort.reopen(src)


if __name__ == "__main__":
    unittest.main()
