"""Adversarial P0 incremental quality-path tests: synthetic fixtures plus a frozen real derivative."""
import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zlib

from ire.v5.p0_incremental_source_gate import verify, IncrementalQualityError
from ire.v5.validation.p0_generic_source_review_gate import (
    ResearchCoverageError, validate_source_review,
)

H = lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest()


def fixture(first_window=25, first_cue=432, claim_id="A25"):
    wid = f"W{first_window:05d}"
    return {
        "video_id": "AeCOMNl11v4",
        "archive_sha256": H("archive"),
        "source_sha256": H("source"),
        "first_cue": first_cue,
        "last_cue": first_cue + 1,
        "reviewed_windows": 1,
        "reviewed_cues": 2,
        "next_window": f"W{first_window + 1:05d}",
        "research_complete": False,
        "p0_go": False,
        "p1_merge": False,
        "windows": [{
            "window_id": wid, "first_cue": first_cue, "last_cue": first_cue + 1,
            "cue_count": 2,
            "disposition": "SOURCE_READ_CANDIDATES_PROVISIONAL",
            "primary_text_sha256": H("cue-pair"),
            "cue_sha256": [
                {"cue": first_cue, "sha256": H("cue-first")},
                {"cue": first_cue + 1, "sha256": H("cue-second")},
            ]
        }],
        "candidates": [{
            "candidate_id": claim_id, "window_id": wid,
            "cue": first_cue, "cue_sha256": H("cue-first"),
            "truth_approved": False, "prior_relation": "OPEN_REQUIRES_REVIEW"
        }]
    }


def prepare(root, records):
    root = Path(root)
    batches = []
    for i, data in enumerate(records):
        rel = f"ire/v5/validation/fixture_{i}.json.zlib.b64"
        file = root / rel
        file.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(data, sort_keys=True).encode("utf-8")
        file.write_text(base64.b64encode(zlib.compress(raw)).decode("ascii"))
        batches.append({
            "batch_id": f"fixture-{i}", "path": rel,
            "payload_sha256": hashlib.sha256(raw).hexdigest(),
            "archive_sha256": data["archive_sha256"],
            "source_sha256": data["source_sha256"],
            "video_id": data["video_id"],
            "first_window": data["windows"][0]["window_id"],
            "first_cue": data["first_cue"],
            "expected_windows": 1, "expected_cues": 2, "expected_claims": len(data["candidates"]),
            "next_window": data["next_window"],
        })
    manifest = {
        "schema": "IRE_V5_P0_INCREMENTAL_QUALITY_MANIFEST_V1",
        "p0_go": False, "independent_recall_certified": False,
        "formal_researchrun_submitted": False, "batches": batches
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest))
    return path, manifest


class IncrementalQualityPathTests(unittest.TestCase):
    def test_real_merged_batch_is_verified(self):
        root = Path(__file__).resolve().parents[3]
        r = verify(root)
        self.assertEqual((r["batches"], r["windows"], r["cues"],
                          r["provisional_claims"]), (1, 24, 431, 54))
        self.assertEqual(r["next_windows_by_video"]["AeCOMNl11v4"], "W00025")
        self.assertFalse(r["private_original_replayed"])
        self.assertFalse(r["p0_go"])

    def test_offset_window_25_is_accepted(self):
        r = validate_source_review(fixture())
        self.assertEqual(r["next_window"], "W00026")

    def test_offset_window_25_wrong_pointer_rejected(self):
        d = fixture()
        d["next_window"] = "W00002"
        with self.assertRaisesRegex(ResearchCoverageError, "RESUME_POINTER"):
            validate_source_review(d)

    def test_offset_window_gap_rejected(self):
        d = fixture()
        d["windows"][0]["window_id"] = "W00026"
        with self.assertRaisesRegex(ResearchCoverageError, "WINDOW_ORDER|FIRST|RESUME_POINTER"):
            validate_source_review(d)

    def test_single_batch_true_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            path, _ = prepare(temp, [fixture()])
            r = verify(Path(temp), path)
            self.assertEqual(r["next_windows_by_video"]["AeCOMNl11v4"], "W00026")

    def test_two_consecutive_offset_batches(self):
        with tempfile.TemporaryDirectory() as temp:
            path, _ = prepare(temp, [fixture(), fixture(26, 434, "A26")])
            self.assertEqual(verify(Path(temp), path)["batches"], 2)

    def test_cross_batch_window_or_cue_gap(self):
        for second in [fixture(27, 434, "A27"), fixture(26, 435, "A26")]:
            with self.subTest(second=second["next_window"]):
                with tempfile.TemporaryDirectory() as temp:
                    path, _ = prepare(temp, [fixture(), second])
                    with self.assertRaisesRegex(IncrementalQualityError, "CROSS_BATCH_GAP_OR_OVERLAP"):
                        verify(Path(temp), path)

    def test_duplicate_claim_id_across_batches(self):
        with tempfile.TemporaryDirectory() as temp:
            path, _ = prepare(temp, [fixture(), fixture(26, 434, "A25")])
            with self.assertRaisesRegex(IncrementalQualityError, "CROSS_BATCH_CLAIM_ID_DUPLICATE"):
                verify(Path(temp), path)

    def test_malicious_replaced_source(self):
        with tempfile.TemporaryDirectory() as temp:
            path, manifest = prepare(temp, [fixture()])
            manifest["batches"][0]["source_sha256"] = H("other-source")
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(IncrementalQualityError, "SOURCE_IDENTITY_DRIFT"):
                verify(Path(temp), path)

    def test_missing_or_corrupted_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            path, manifest = prepare(temp, [fixture()])
            file = Path(temp) / manifest["batches"][0]["path"]
            file.unlink()
            with self.assertRaisesRegex(IncrementalQualityError, "BUNDLE_FILE_MISSING"):
                verify(Path(temp), path)
        with tempfile.TemporaryDirectory() as temp:
            path, manifest = prepare(temp, [fixture()])
            file = Path(temp) / manifest["batches"][0]["path"]
            file.write_text(base64.b64encode(zlib.compress(b'{"forged":true}')).decode("ascii"))
            with self.assertRaisesRegex(IncrementalQualityError, "BUNDLE_PAYLOAD_HASH_DRIFT"):
                verify(Path(temp), path)

    def test_false_approval_and_raw_source_key_rejected(self):
        for key, value in [("p0_go", True), ("source_text", "private!")]:
            with self.subTest(key=key):
                d = fixture()
                d[key] = value
                with tempfile.TemporaryDirectory() as temp:
                    path, _ = prepare(temp, [d])
                    with self.assertRaises(ResearchCoverageError):
                        verify(Path(temp), path)

    def test_two_distinct_atomic_claims_on_same_cue(self):
        d = fixture()
        extra = dict(d["candidates"][0])
        extra["candidate_id"] = "A25B"
        d["candidates"].append(extra)
        self.assertEqual(validate_source_review(d)["provisional_claims"], 2)

    def test_empty_window_needs_explicit_disposition(self):
        d = fixture()
        d["candidates"] = []
        with self.assertRaisesRegex(ResearchCoverageError, "EMPTY_WINDOW_MISMATCH"):
            validate_source_review(d)
        d["windows"][0]["disposition"] = "SOURCE_READ_NO_FINANCIAL_ATOMIC_CLAIM"
        self.assertEqual(validate_source_review(d)["provisional_claims"], 0)

    def test_real_one_turn_entrypoint_aborts_on_gate_failure(self):
        from unittest.mock import patch
        from ire.v5 import one_turn_run
        with patch.object(one_turn_run, "preflight_run", return_value=0):
            with patch.object(one_turn_run, "verify_p0_incremental_source",
                              side_effect=IncrementalQualityError("PROBE_FAIL")) as check:
                with self.assertRaisesRegex(IncrementalQualityError, "PROBE_FAIL"):
                    one_turn_run.run(Path(__file__).resolve().parents[3])
                check.assert_called_once()

    def test_claim_provenance_cannot_be_edited(self):
        d = fixture()
        d["candidates"][0]["cue_sha256"] = H("fake-cue")
        with tempfile.TemporaryDirectory() as temp:
            path, _ = prepare(temp, [d])
            with self.assertRaisesRegex(ResearchCoverageError, "UNOWNED_CLAIM"):
                verify(Path(temp), path)


if __name__ == "__main__":
    unittest.main()
