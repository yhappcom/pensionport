"""Private-original byte replay for P0 claim anchors, with hostile synthetic SRTs.

CI never contains the owner's 1-70.zip. All synthetic tests are public and
prove that syntactically valid but false hashes/times cannot pass the private
execution path. The default one-turn pipeline reports source replay=NOT DONE.
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

from ire.v5.p0_claim_ownership_gate import (
    ClaimOwnershipError,
    validate_claim_ownership,
    verify_private_source,
)
from ire.v5 import one_turn_run

SHA = lambda b: hashlib.sha256(b).hexdigest()
ROOT = Path(__file__).resolve().parents[3]
VIDEO = "abcdefghijk"
TEXTS = ("first statement", "second conditional statement",
         "third multiple hypothesis", "fourth answer")
SRT = "\n\n".join(
    f"{i}\n00:00:{i:02d},000 --> 00:00:{i:02d},800\n{t}"
    for i, t in enumerate(TEXTS, 1)
).encode("utf-8")


def claim(cid: str, cue: int, window: str, *, context=None) -> dict:
    first, last = context or (cue, cue)
    return {
        "candidate_id": cid,
        "window_id": window,
        "original_window_id": window,
        "anchor_cue": cue,
        "anchor_cue_sha256": SHA(TEXTS[cue - 1].encode("utf-8")),
        "anchor_start_time": f"00:00:{cue:02d},000",
        "context_first_cue": first,
        "context_last_cue": last,
        "cross_window_context_open": first <= 2 < last,
        "summary": f"Semantic provisional claim {cid} sourced from cue {cue}",
        "correction_status": "UNCHANGED",
        "evidence_status": "OPEN",
        "prior_relation_status": "OPEN",
        "fact_approved": False,
    }


def window(number: int, first: int, last: int) -> dict:
    return {
        "window_id": f"W{number:05d}",
        "first_cue": first,
        "last_cue": last,
        "window_text_sha256": SHA(
            " ".join(TEXTS[i - 1] for i in range(first, last + 1)).encode("utf-8")
        ),
    }


def record(archive_sha: str, *, windows=None, claims=None, video=VIDEO) -> dict:
    windows = windows if windows is not None else [window(1, 1, 2), window(2, 3, 4)]
    claims = claims if claims is not None else [
        claim("C1", 2, "W00001", context=(2, 3)),
        claim("C2", 2, "W00001"),
        claim("C3", 3, "W00002"),
    ]
    return {
        "schema": "IRE_V5_P0_CLAIM_OWNERSHIP_RECONCILIATION_V1",
        "video_id": video,
        "archive_sha256": archive_sha,
        "source_sha256": SHA(SRT),
        "source_cues_total": 4,
        "source_window_first": windows[0]["window_id"],
        "source_window_last": windows[-1]["window_id"],
        "windows": windows,
        "claims": claims,
        "legacy_claim_count": len(claims),
        "legacy_owner_errors_expected": 0,
        "first_unread_window": f"W{int(windows[-1]['window_id'][1:]) + 1:05d}",
        "formal_queue_pointer": windows[0]["window_id"],
        "p0_complete": False,
        "independent_gold_available": False,
        "formal_second_pass_registry_generated": False,
        "finance_facts_approved": 0,
    }


class PrivateOriginalCueReplayTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.zip = self.root / "original.zip"
        self.registry = self.root / "registry.json"
        self._archive({"pilot/youtube-transcript-abcdefghijk.srt": SRT})
        self.docs = [record(SHA(self.zip.read_bytes()))]
        self._write_docs()

    def _archive(self, contents):
        with zipfile.ZipFile(self.zip, "w", zipfile.ZIP_DEFLATED) as z:
            for filename, raw in contents.items():
                z.writestr(filename, raw)

    def _write_docs(self):
        entries = []
        for i, d in enumerate(self.docs):
            rel = Path(f"ire/v5/validation/private_test_{i}.json")
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            raw = json.dumps(d, sort_keys=True).encode("utf-8")
            p.write_bytes(raw)
            entries.append({"path": str(rel), "record_sha256": SHA(raw)})
        self.registry.write_text(json.dumps({
            "schema": "IRE_V5_P0_CLAIM_OWNERSHIP_REGISTRY_V1",
            "p0_go": False,
            "entries": entries,
        }), encoding="utf-8")

    def check(self):
        return verify_private_source(self.root, self.zip, self.registry)

    def test_exact_source_byte_replay(self):
        out = self.check()
        self.assertTrue(out["source_original_bytes_replayed"])
        self.assertEqual(out["validated_window_hashes"], 2)
        self.assertEqual(out["validated_claim_anchor_hashes_and_times"], 3)
        self.assertEqual(out["unique_claim_anchor_cues"], 2)
        self.assertFalse(out["independent_blind_recall_proven"])
        self.assertFalse(out["p0_go"])

    def test_repeated_cue_can_support_two_distinct_atomic_claims(self):
        self.assertEqual(self.check()["validated_claim_anchor_hashes_and_times"], 3)
        self.assertEqual(self.check()["unique_claim_anchor_cues"], 2)

    def test_syntactically_valid_wrong_cue_digest_is_caught(self):
        self.docs[0]["claims"][0]["anchor_cue_sha256"] = "a" * 64
        self._write_docs()
        with self.assertRaisesRegex(ClaimOwnershipError,
                                    "PRIVATE_ANCHOR_CUE_SHA256_MISMATCH"):
            self.check()

    def test_syntactically_valid_wrong_source_timestamp_is_caught(self):
        self.docs[0]["claims"][0]["anchor_start_time"] = "00:00:09,000"
        self._write_docs()
        with self.assertRaisesRegex(ClaimOwnershipError,
                                    "PRIVATE_ANCHOR_START_TIME_MISMATCH"):
            self.check()

    def test_wrong_window_content_digest_is_caught(self):
        self.docs[0]["windows"][0]["window_text_sha256"] = "b" * 64
        self._write_docs()
        with self.assertRaisesRegex(ClaimOwnershipError,
                                    "PRIVATE_WINDOW_CONTENT_SHA256_MISMATCH"):
            self.check()

    def test_wrong_total_cue_count_is_caught(self):
        self.docs[0]["source_cues_total"] = 5
        self._write_docs()
        with self.assertRaisesRegex(ClaimOwnershipError,
                                    "PRIVATE_SRT_CUE_CENSUS_DRIFT"):
            self.check()

    def test_changed_zip_original_is_caught_with_correct_archive_digest(self):
        altered = SRT.replace(b"third multiple hypothesis", b"third altered hypothesis")
        self._archive({"pilot/youtube-transcript-abcdefghijk.srt": altered})
        self.docs[0]["archive_sha256"] = SHA(self.zip.read_bytes())
        self._write_docs()
        with self.assertRaisesRegex(ClaimOwnershipError, "PRIVATE_SRT_SHA256_MISMATCH"):
            self.check()

    def test_wrong_original_archive_sha_is_caught(self):
        self.docs[0]["archive_sha256"] = "c" * 64
        self._write_docs()
        with self.assertRaisesRegex(ClaimOwnershipError,
                                    "PRIVATE_ARCHIVE_SHA256_MISMATCH"):
            self.check()

    def test_missing_original_srt_member_is_caught(self):
        self._archive({"pilot/other.srt": SRT})
        self.docs[0]["archive_sha256"] = SHA(self.zip.read_bytes())
        self._write_docs()
        with self.assertRaisesRegex(ClaimOwnershipError,
                                    "PRIVATE_SRT_MEMBER_MISSING_OR_AMBIGUOUS"):
            self.check()

    def test_ambiguous_original_srt_member_is_caught(self):
        self._archive({
            "first/youtube-transcript-abcdefghijk.srt": SRT,
            "second/youtube-transcript-abcdefghijk.srt": SRT,
        })
        self.docs[0]["archive_sha256"] = SHA(self.zip.read_bytes())
        self._write_docs()
        with self.assertRaisesRegex(ClaimOwnershipError,
                                    "PRIVATE_SRT_MEMBER_MISSING_OR_AMBIGUOUS"):
            self.check()

    def test_unregistered_file_mutation_is_caught_before_replay(self):
        self.docs[0]["claims"][0]["anchor_cue_sha256"] = "c" * 64
        path = self.root / "ire/v5/validation/private_test_0.json"
        path.write_text(json.dumps(self.docs[0]))
        with self.assertRaisesRegex(ClaimOwnershipError,
                                    "OWNERSHIP_RECORD_HASH_DRIFT"):
            self.check()

    def test_sequential_batches_same_video_are_replayed(self):
        archive_sha = SHA(self.zip.read_bytes())
        self.docs = [
            record(archive_sha, windows=[window(1, 1, 2)],
                   claims=[claim("C1", 2, "W00001")]),
            record(archive_sha, windows=[window(2, 3, 4)],
                   claims=[claim("C2", 3, "W00002")]),
        ]
        self._write_docs()
        result = self.check()
        self.assertEqual(result["validated_research_batches"], 2)
        self.assertEqual(result["validated_window_hashes"], 2)
        self.assertEqual(result["validated_claim_anchor_hashes_and_times"], 2)

    def test_second_batch_source_sha_drift_even_with_cache_is_caught(self):
        archive_sha = SHA(self.zip.read_bytes())
        self.docs = [
            record(archive_sha, windows=[window(1, 1, 2)],
                   claims=[claim("C1", 2, "W00001")]),
            record(archive_sha, windows=[window(2, 3, 4)],
                   claims=[claim("C2", 3, "W00002")]),
        ]
        self.docs[1]["source_sha256"] = "d" * 64
        self._write_docs()
        with self.assertRaisesRegex(ClaimOwnershipError,
                                    "PRIVATE_BATCH_SOURCE_SHA256_DRIFT"):
            self.check()

    def test_cross_window_context_is_not_semantically_approved(self):
        out = self.check()
        self.assertFalse(out["context_semantic_completeness_proven"])
        self.assertEqual(out["context_cue_references_structurally_reviewed"], 4)

    def test_one_turn_private_source_replay_failure_stops_before_receipt(self):
        with patch.object(one_turn_run, "verify_p0_private_source",
                          side_effect=ClaimOwnershipError("INJECTED_PRIVATE_REPLAY_FAIL")) as verify:
            printed = io.StringIO()
            with redirect_stdout(printed), self.assertRaisesRegex(
                    ClaimOwnershipError, "INJECTED_PRIVATE_REPLAY_FAIL"):
                one_turn_run.run(ROOT, private_zip=self.zip)
            verify.assert_called_once()
            self.assertNotIn("ONE_TURN_RESEARCH_RECEIPT ", printed.getvalue())


if __name__ == "__main__":
    unittest.main()
