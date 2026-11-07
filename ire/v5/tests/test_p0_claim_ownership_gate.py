"""Negative replay of eight real legacy cue-owner defects and generic counterexamples.

The 26-claim record is a provisional redacted artifact, not a gold annotation.
No private subtitle bytes are required or fetched by CI.
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

from ire.v5.p0_claim_ownership_gate import (
    ClaimOwnershipError, validate_claim_ownership, verify,
)
from ire.v5 import one_turn_run


ROOT = Path(__file__).resolve().parents[3]
RECORD = ROOT / "ire/v5/validation/p0_video24_w37_w44_claim_ownership_reconciliation.json"


def sample():
    return json.loads(RECORD.read_text("utf-8"))


def indexed(d, cue):
    return next(c for c in d["claims"] if c["anchor_cue"] == cue)


class ClaimOwnershipGateTests(unittest.TestCase):

    def test_real_redacted_source_registry_passes(self):
        r = verify(ROOT)
        self.assertEqual((r["batches"], r["verified_provisional_claim_anchors"],
                          r["corrected_legacy_claim_owners"],
                          r["cross_window_context_open"]), (1, 26, 8, 3))
        self.assertFalse(r["private_srt_replayed_in_this_ci"])
        self.assertFalse(r["semantic_gold_recall_certified"])
        self.assertFalse(r["p0_go"])

    def test_all_eight_legacy_wrong_window_labels_fail_closed(self):
        d = sample()
        broken = [c for c in d["claims"] if
                  c["original_window_id"] != c["window_id"]]
        self.assertEqual({c["anchor_cue"] for c in broken},
                         {719, 729, 731, 734, 736, 747, 755, 772})
        for row in broken:
            with self.subTest(cue=row["anchor_cue"]):
                forged = deepcopy(d)
                target = indexed(forged, row["anchor_cue"])
                target["window_id"] = target["original_window_id"]
                with self.assertRaisesRegex(ClaimOwnershipError,
                                            "CLAIM_CUE_OUTSIDE_OWNED_WINDOW"):
                    validate_claim_ownership(forged)

    def test_effective_correction_cannot_be_silenced(self):
        d = sample()
        indexed(d, 729)["correction_status"] = "UNCHANGED"
        with self.assertRaisesRegex(ClaimOwnershipError,
                                    "ORIGINAL_OWNER_CORRECTION_UNACKNOWLEDGED"):
            validate_claim_ownership(d)

    def test_cross_window_halo_rejected_without_open_flag(self):
        d = sample()
        indexed(d, 772)["cross_window_context_open"] = False
        with self.assertRaisesRegex(ClaimOwnershipError,
                                    "CROSS_WINDOW_CONTEXT_NOT_FLAGGED"):
            validate_claim_ownership(d)

    def test_nonadjacent_claim_context_rejected(self):
        d = sample()
        indexed(d, 729)["context_last_cue"] = 790
        with self.assertRaisesRegex(ClaimOwnershipError,
                                    "CLAIM_CONTEXT_NOT_ADJACENT"):
            validate_claim_ownership(d)

    def test_unowned_context_span_rejected(self):
        d = sample()
        indexed(d, 659)["context_first_cue"] = 647
        with self.assertRaisesRegex(ClaimOwnershipError,
                                    "CLAIM_CONTEXT_CUE_MISSING"):
            validate_claim_ownership(d)

    def test_duplicate_claim_ids_rejected(self):
        d = sample()
        d["claims"][0]["candidate_id"] = d["claims"][1]["candidate_id"]
        with self.assertRaisesRegex(ClaimOwnershipError,
                                    "DUPLICATE_CANDIDATE_ID"):
            validate_claim_ownership(d)

    def test_distinct_atomic_claims_can_share_one_cue(self):
        d = sample()
        second = deepcopy(indexed(d, 695))
        second["candidate_id"] = "PR38-C027"
        second["summary"] = "Personal first cryptocurrency purchase separately from price trend"
        d["claims"].append(second)
        d["legacy_claim_count"] = 27
        self.assertEqual(validate_claim_ownership(d)
                         ["provisional_claims_structurally_checked"], 27)

    def test_cue_range_gap_and_overlap_fail_closed(self):
        for delta in (-1, 1):
            with self.subTest(delta=delta):
                d = sample()
                d["windows"][1]["first_cue"] += delta
                with self.assertRaisesRegex(ClaimOwnershipError,
                                            "WINDOW_CUE_GAP_OR_OVERLAP"):
                    validate_claim_ownership(d)

    def test_wrong_resume_pointer_rejected(self):
        d = sample()
        d["first_unread_window"] = "W00047"
        with self.assertRaisesRegex(ClaimOwnershipError, "NEXT_UNREAD_WINDOW_DRIFT"):
            validate_claim_ownership(d)

    def test_formal_queue_not_advanced_by_unsealed_notes(self):
        d = sample()
        d["formal_queue_pointer"] = "W00045"
        with self.assertRaisesRegex(ClaimOwnershipError, "FORMAL_POINTER"):
            validate_claim_ownership(d)

    def test_unsubstantiated_p0_approval_fails_closed(self):
        for field, value in [("p0_complete", True),
                             ("independent_gold_available", True),
                             ("finance_facts_approved", 1)]:
            with self.subTest(field=field):
                d = sample()
                d[field] = value
                with self.assertRaisesRegex(ClaimOwnershipError,
                                            "FALSE_P0_OR_FINANCIAL_APPROVAL"):
                    validate_claim_ownership(d)

    def test_changed_hash_or_timestamp_rejected(self):
        d = sample()
        indexed(d, 761)["anchor_cue_sha256"] = "INVALID"
        with self.assertRaisesRegex(ClaimOwnershipError, "CLAIM_CUE_HASH_INVALID"):
            validate_claim_ownership(d)
        d = sample()
        indexed(d, 761)["anchor_start_time"] = "not-a-time"
        with self.assertRaisesRegex(ClaimOwnershipError, "CLAIM_TIMESTAMP_INVALID"):
            validate_claim_ownership(d)

    def test_registration_hash_pin_rejects_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rel = Path("ire/v5/validation/p0_fixture.json")
            file = root / rel
            file.parent.mkdir(parents=True)
            payload = RECORD.read_bytes()
            file.write_bytes(payload)
            entry = {"path": str(rel), "record_sha256": hashlib.sha256(payload).hexdigest()}
            registry = {"schema": "IRE_V5_P0_CLAIM_OWNERSHIP_REGISTRY_V1",
                        "p0_go": False, "entries": [entry]}
            regfile = root / "registry.json"
            regfile.write_text(json.dumps(registry))
            self.assertEqual(verify(root, regfile)["batches"], 1)
            file.write_bytes(payload + b" ")
            with self.assertRaisesRegex(ClaimOwnershipError,
                                        "OWNERSHIP_RECORD_HASH_DRIFT"):
                verify(root, regfile)

    def test_multi_video_registry_supported_but_same_video_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            entries = []
            for i in range(2):
                data = sample()
                data["video_id"] = "abcdefghijk" if i else "AeCOMNl11v4"
                rel = Path(f"ire/v5/validation/batch_{i}.json")
                f = root / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                raw = json.dumps(data).encode("utf-8")
                f.write_bytes(raw)
                entries.append({"path": str(rel),
                                "record_sha256": hashlib.sha256(raw).hexdigest()})
            regfile = root / "registry.json"
            regfile.write_text(json.dumps({
                "schema": "IRE_V5_P0_CLAIM_OWNERSHIP_REGISTRY_V1",
                "p0_go": False, "entries": entries}))
            self.assertEqual(verify(root, regfile)["batches"], 2)
            data = sample()
            second_file = root / entries[1]["path"]
            raw = json.dumps(data).encode("utf-8")
            second_file.write_bytes(raw)
            entries[1]["record_sha256"] = hashlib.sha256(raw).hexdigest()
            regfile.write_text(json.dumps({
                "schema": "IRE_V5_P0_CLAIM_OWNERSHIP_REGISTRY_V1",
                "p0_go": False, "entries": entries}))
            with self.assertRaisesRegex(ClaimOwnershipError,
                                        "RESEARCH_CLAIM_ID_DUPLICATED_ACROSS_BATCHES"):
                verify(root, regfile)

    def test_one_turn_path_halts_before_terminal_receipt(self):
        capture = io.StringIO()
        with patch.object(one_turn_run, "preflight_run", return_value=0), \
             patch.object(one_turn_run, "verify_p0_incremental_source",
                          return_value={"p0_go": False}), \
             patch.object(one_turn_run, "verify_p0_claim_ownership",
                          side_effect=ClaimOwnershipError("INJECTED_BAD_OWNER")) as gate, \
             redirect_stdout(capture):
            with self.assertRaisesRegex(ClaimOwnershipError, "INJECTED_BAD_OWNER"):
                one_turn_run.run(ROOT)
            gate.assert_called_once()
        self.assertNotIn("ONE_TURN_RESEARCH_RECEIPT ", capture.getvalue())


if __name__ == "__main__":
    unittest.main()
