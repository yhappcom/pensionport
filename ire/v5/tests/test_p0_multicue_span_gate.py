"""Adversarial cross-window multi-cue proof, provenance and one-turn tests.

Only synthetic private SRT bytes are used in CI. Real P0 spans are verified
structurally; no private transcript is committed or construed as gold labels.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from ire.v5 import one_turn_run
from ire.v5.p0_multicue_span_gate import (
    MultiCueSpanError, validate_multicue_record, verify, verify_private,
)

ROOT = Path(__file__).resolve().parents[3]
REAL_OWNER = ROOT / "ire/v5/validation/p0_video24_w37_w44_claim_ownership_reconciliation.json"
REAL_SPAN = ROOT / "ire/v5/validation/p0_video24_w37_w44_multicue_context.json"
SRT_TEXT = ("1\n00:00:01,000 --> 00:00:01,900\nDecision case\n\n"
            "2\n00:00:02,000 --> 00:00:02,900\nSplit purchase\n\n"
            "3\n00:00:03,000 --> 00:00:03,900\nOnly if sufficient cash\n\n"
            "4\n00:00:04,000 --> 00:00:04,900\nRisk caveat preserved").encode()
CUES = ("Decision case", "Split purchase", "Only if sufficient cash", "Risk caveat preserved")
SHA = lambda b: hashlib.sha256(b).hexdigest()


def synthetic_owner(archive_sha):
    video = "abcdefghijk"
    return {
        "schema": "IRE_V5_P0_CLAIM_OWNERSHIP_RECONCILIATION_V1",
        "video_id": video, "archive_sha256": archive_sha,
        "source_sha256": SHA(SRT_TEXT), "source_cues_total": 4,
        "source_window_first": "W00001", "source_window_last": "W00002",
        "windows": [
            {"window_id": "W00001", "first_cue": 1, "last_cue": 2,
             "window_text_sha256": SHA(" ".join(CUES[:2]).encode())},
            {"window_id": "W00002", "first_cue": 3, "last_cue": 4,
             "window_text_sha256": SHA(" ".join(CUES[2:]).encode())},
        ],
        "claims": [{
            "candidate_id": "C0001", "window_id": "W00001",
            "original_window_id": "W00001", "anchor_cue": 2,
            "anchor_cue_sha256": SHA(CUES[1].encode()),
            "anchor_start_time": "00:00:02,000",
            "context_first_cue": 2, "context_last_cue": 4,
            "cross_window_context_open": True,
            "summary": "Staged purchase conditional on maintained liquidity",
            "correction_status": "UNCHANGED", "evidence_status": "OPEN",
            "prior_relation_status": "OPEN", "fact_approved": False,
        }],
        "legacy_claim_count": 1, "legacy_owner_errors_expected": 0,
        "first_unread_window": "W00003", "formal_queue_pointer": "W00001",
        "p0_complete": False, "independent_gold_available": False,
        "formal_second_pass_registry_generated": False, "finance_facts_approved": 0,
    }


def synthetic_span(owner, owner_sha):
    entries = []
    for n, role, note in [
        (2, "ACTION", "States staged allocation in market episode"),
        (3, "QUALIFIER", "Explicit condition attached to allocation"),
        (4, "RISK_CONDITION", "States risk reserve concern for the decision"),
    ]:
        entries.append({
            "cue_index": n, "cue_sha256": SHA(CUES[n-1].encode()),
            "start_time": f"00:00:{n:02d},000",
            "roles": [role], "role_note": note,
        })
    return {
        "schema": "IRE_V5_P0_MULTICUE_CONTEXT_V1",
        "video_id": owner["video_id"], "source_sha256": owner["source_sha256"],
        "archive_sha256": owner["archive_sha256"],
        "owner_record_path": "ire/v5/validation/synthetic_owner.json",
        "owner_record_sha256": owner_sha,
        "source_bytes_replayed_by_public_ci": False,
        "independent_recall_certified": False, "p0_go": False,
        "cases": [{
            "candidate_id": "C0001", "window_id": "W00001", "anchor_cue": 2,
            "first_cue": 2, "last_cue": 4,
            "required_roles": ["ACTION", "QUALIFIER"],
            "cue_coverage": entries,
            "status": "OPEN_SECOND_PASS_REQUIRED",
            "independent_blind_reviewed": False,
            "material_semantics_certified": False,
            "financial_fact_approved": False,
        }]
    }


class MultiCueSpanQualityTests(unittest.TestCase):
    def setUp(self):
        self.owner = json.loads(REAL_OWNER.read_text("utf-8"))
        self.span = json.loads(REAL_SPAN.read_text("utf-8"))

    def test_real_3_spans_cover_15_cues_and_are_not_semantically_approved(self):
        result = verify(ROOT)
        self.assertEqual((result["claims_with_complete_declared_context_census"],
                          result["cue_roles_reviewed_structurally"]), (3, 15))
        self.assertFalse(result["private_original_spans_replayed"])
        self.assertFalse(result["independent_semantic_recall_proven"])
        self.assertFalse(result["p0_go"])

    def test_omit_adjacent_qualifier_cue_fails(self):
        doc = deepcopy(self.span)
        doc["cases"][0]["cue_coverage"].pop(2)
        with self.assertRaisesRegex(MultiCueSpanError,
                                    "MULTICUE_MISSING_OR_DUPLICATED_CONTEXT_CUE"):
            validate_multicue_record(doc, self.owner)

    def test_reorder_or_duplicate_source_cue_fails(self):
        for mutation in ("swap", "duplicate"):
            with self.subTest(mutation=mutation):
                doc = deepcopy(self.span)
                rows = doc["cases"][1]["cue_coverage"]
                if mutation == "swap":
                    rows[2], rows[3] = rows[3], rows[2]
                else:
                    rows[3] = deepcopy(rows[2])
                with self.assertRaisesRegex(MultiCueSpanError,
                                            "MULTICUE_MISSING_OR_DUPLICATED_CONTEXT_CUE"):
                    validate_multicue_record(doc, self.owner)

    def test_missing_leverage_amount_and_total_amount_roles_fail(self):
        for n in (773, 774):
            with self.subTest(cue=n):
                doc = deepcopy(self.span)
                for row in doc["cases"][2]["cue_coverage"]:
                    if row["cue_index"] == n:
                        row["roles"] = ["CONTEXT"]
                with self.assertRaisesRegex(MultiCueSpanError,
                                            "MULTICUE_REQUIRED_MATERIAL_SLOT_MISSING"):
                    validate_multicue_record(doc, self.owner)

    def test_crossing_span_with_only_context_on_next_window_fails(self):
        doc = deepcopy(self.span)
        for row in doc["cases"][0]["cue_coverage"]:
            if row["cue_index"] >= 720:
                row["roles"] = ["CONTEXT"]
        with self.assertRaisesRegex(MultiCueSpanError,
                                    "MULTICUE_ADJACENT_MATERIAL_NOT_REVIEWED"):
            validate_multicue_record(doc, self.owner)

    def test_omitted_entire_cross_window_case_fails(self):
        doc = deepcopy(self.span)
        doc["cases"].pop()
        with self.assertRaisesRegex(MultiCueSpanError,
                                    "MULTICUE_UNREGISTERED_CROSS_WINDOW_CLAIM"):
            validate_multicue_record(doc, self.owner)

    def test_try_to_shrink_context_span_fails_against_pinned_owner(self):
        doc = deepcopy(self.span)
        doc["cases"][2]["last_cue"] = 772
        doc["cases"][2]["cue_coverage"] = doc["cases"][2]["cue_coverage"][:1]
        with self.assertRaisesRegex(MultiCueSpanError,
                                    "MULTICUE_CROSS_WINDOW_SPAN_DRIFT"):
            validate_multicue_record(doc, self.owner)

    def test_false_semantic_or_fact_approval_fails(self):
        for key in ("independent_blind_reviewed", "material_semantics_certified",
                    "financial_fact_approved"):
            with self.subTest(key=key):
                doc = deepcopy(self.span)
                doc["cases"][0][key] = True
                with self.assertRaisesRegex(MultiCueSpanError,
                                            "MULTICUE_UNSUPPORTED_SEMANTIC_CLOSURE"):
                    validate_multicue_record(doc, self.owner)

    def test_same_cue_multiple_independent_claims_still_allowed_in_owner(self):
        # The canonical owner gate already permits two different candidate IDs
        # to cite the same cue. Multicue record does not erase that property.
        from ire.v5.p0_claim_ownership_gate import validate_claim_ownership
        owner = deepcopy(self.owner)
        c = deepcopy(owner["claims"][0])
        c["candidate_id"] = "SECOND_DISTINCT_ATOM"
        owner["claims"].append(c)
        owner["legacy_claim_count"] += 1
        self.assertEqual(validate_claim_ownership(owner)
                         ["provisional_claims_structurally_checked"], 27)

    def test_forged_anchor_hash_mismatches_owner(self):
        doc = deepcopy(self.span)
        doc["cases"][0]["cue_coverage"][0]["cue_sha256"] = "e"*64
        with self.assertRaisesRegex(MultiCueSpanError, "MULTICUE_ANCHOR_SOURCE_DRIFT"):
            validate_multicue_record(doc, self.owner)

    def test_same_session_role_labels_never_count_as_independent_gold(self):
        result = validate_multicue_record(self.span, self.owner)
        self.assertFalse(result["semantic_role_labels_independently_verified"])
        self.assertFalse(result["p0_go"])

    def test_one_turn_gate_failure_prevents_receipt(self):
        out = io.StringIO()
        with patch.object(one_turn_run, "preflight_run", return_value=0), \
             patch.object(one_turn_run, "verify_p0_incremental_source",
                          return_value={"p0_go": False}), \
             patch.object(one_turn_run, "verify_p0_claim_ownership",
                          return_value={"p0_go": False}), \
             patch.object(one_turn_run, "verify_p0_multicue_spans",
                          side_effect=MultiCueSpanError("INJECTED_MULTICUE_GAP")), \
             redirect_stdout(out):
            with self.assertRaisesRegex(MultiCueSpanError, "INJECTED_MULTICUE_GAP"):
                one_turn_run.run(ROOT)
        self.assertNotIn("ONE_TURN_RESEARCH_RECEIPT ", out.getvalue())


class MultiCueSyntheticPrivateReplayTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root = Path(self.dir.name)
        self.zip = self.root / "private.zip"
        with zipfile.ZipFile(self.zip, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("pilot/youtube-transcript-abcdefghijk.srt", SRT_TEXT)
        self.owner = synthetic_owner(SHA(self.zip.read_bytes()))
        self._write()

    def _write(self):
        validation = self.root / "ire/v5/validation"
        validation.mkdir(parents=True, exist_ok=True)
        owner_raw = (json.dumps(self.owner, sort_keys=True)+"\n").encode()
        (validation/"synthetic_owner.json").write_bytes(owner_raw)
        owner_sha = SHA(owner_raw)
        self.span = getattr(self, "span", None) or synthetic_span(self.owner, owner_sha)
        self.span["owner_record_sha256"] = owner_sha
        span_raw = (json.dumps(self.span, sort_keys=True)+"\n").encode()
        (validation/"synthetic_span.json").write_bytes(span_raw)
        (validation/"p0_claim_ownership_registry.json").write_text(json.dumps({
            "schema": "IRE_V5_P0_CLAIM_OWNERSHIP_REGISTRY_V1",
            "p0_go": False,
            "entries": [{
                "path": "ire/v5/validation/synthetic_owner.json",
                "record_sha256": owner_sha,
            }],
        }))
        (validation/"p0_multicue_context_registry.json").write_text(json.dumps({
            "schema": "IRE_V5_P0_MULTICUE_CONTEXT_REGISTRY_V1",
            "p0_go": False,
            "entries": [{
                "path": "ire/v5/validation/synthetic_span.json",
                "record_sha256": SHA(span_raw),
            }]
        }))

    def test_all_three_original_cross_window_cues_replay(self):
        result = verify_private(self.root, self.zip)
        self.assertEqual(result["original_private_cues_replayed"], 3)
        self.assertTrue(result["source_original_bytes_replayed"])
        self.assertFalse(result["independent_semantic_completeness_proven"])

    def test_context_cue_digest_forged_but_well_formed_fails(self):
        self.span["cases"][0]["cue_coverage"][1]["cue_sha256"] = "f"*64
        self._write()
        self.assertEqual(verify(self.root)["cue_roles_reviewed_structurally"], 3)
        with self.assertRaisesRegex(MultiCueSpanError,
                                    "MULTICUE_PRIVATE_CUE_DIGEST_MISMATCH"):
            verify_private(self.root, self.zip)

    def test_context_cue_timestamp_forged_but_well_formed_fails(self):
        self.span["cases"][0]["cue_coverage"][1]["start_time"] = "00:00:09,000"
        self._write()
        with self.assertRaisesRegex(MultiCueSpanError,
                                    "MULTICUE_PRIVATE_CUE_TIMESTAMP_MISMATCH"):
            verify_private(self.root, self.zip)

    def test_unregistered_changed_source_artifact_fails(self):
        path = self.root / "ire/v5/validation/synthetic_span.json"
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(MultiCueSpanError,
                                    "MULTICUE_RECORD_HASH_DRIFT"):
            verify(self.root)

    def test_private_one_turn_fail_closed_before_terminal_receipt(self):
        # Private optional path is checked before the public pipeline emits.
        out = io.StringIO()
        with patch.object(one_turn_run, "verify_p0_private_source",
                          return_value={"source_original_bytes_replayed": True}), \
             patch.object(one_turn_run, "verify_p0_private_multicue_spans",
                          side_effect=MultiCueSpanError("FORGED_CONTEXT_CUE")), \
             redirect_stdout(out):
            with self.assertRaisesRegex(MultiCueSpanError, "FORGED_CONTEXT_CUE"):
                one_turn_run.run(ROOT, private_zip=self.zip)
        self.assertNotIn("ONE_TURN_RESEARCH_RECEIPT ", out.getvalue())


if __name__ == "__main__":
    unittest.main()
