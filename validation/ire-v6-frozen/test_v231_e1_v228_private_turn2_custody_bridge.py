"""V231 synthetic fixtures: private note bytes and every V145 escrow row bind."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from ire.v6 import TransactionStore
from ire.v6.claim_census import FINANCIAL, QUALIFIER, MULTI_CLAIM
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from test_v230_e1_v228_source_native_handoff import (
    TestV230RealSourceNativeBoundary,
)
from v228_v193_actual_two_turn_runtime_gate import canonical
from v231_e1_v228_private_turn2_custody_bridge import (
    verify_real_turn2_private_custody, stage_after_verified_private_turn2,
)


class TestV231Turn2ReviewCustody(unittest.TestCase):
    def setUp(self):
        base = TestV230RealSourceNativeBoundary(
            "test_01_genuine_v228_source_is_native_v6_input_not_v176")
        base.setUp()
        self.addCleanup(base.doCleanups)
        self.origin = base.origin
        self.receipt = base.review_receipt()
        self.synthetic_note = self._note()
        self.escrow = self._escrow()
        self.pins = self._pins()

    def _mandatory(self):
        source = self.origin["source"]
        out = []
        for r in self.origin["exchange"]["cue_dispositions"]:
            i = r["cue_index"]
            risky = bool(FINANCIAL.search(source.cues[i-1].text)
                         or QUALIFIER.search(source.cues[i-1].text)
                         or MULTI_CLAIM.search(source.cues[i-1].text))
            if r["disposition"] == "UNRESOLVED" or (
                    r["disposition"] == "NO_ATOM" and risky):
                out.append(i)
        return out

    def _note(self):
        rows = self.receipt["turn2_review"]["source_only_review_rows"]
        return {
            "schema": "IRE_V231_CHATGPT_SECOND_TURN_SOURCE_FIRST_REVIEW_NOTE_V1",
            "source_sha256": self.origin["source_sha256"],
            "turn1_first_head_sha256": self.origin[
                "frozen_turn1_head_sha256"],
            "turn2_review_sha256": self.receipt["second_review_head_sha256"],
            "review_executor": "CHATGPT_IN_CHAT",
            "cue_rows": [{
                "cue_index": idx,
                "quote_sha256": rows[idx-1]["quote_sha256"],
                "review_disposition": rows[idx-1]["disposition"],
                "source_grounded_review_reason": rows[idx-1]["review_reason"],
            } for idx in self._mandatory()],
            "independent_gold": False,
            "financial_fact_approved": False,
            "e3_formal_approved": False,
            "host_two_turns_crypto_verified": False,
        }

    def _escrow(self):
        src = self.origin["source"]
        return {
            "schema": "IRE_V6_HOST_SOURCE_PREQUARANTINE_V145",
            "source_sha256": self.origin["source_sha256"],
            "manifest_sha256": src.manifest_sha256,
            "review_executor": "CHATGPT_IN_CHAT",
            "private_review_sha256": sha256(canonical(self.synthetic_note)),
            "cue_rows": [{
                "cue_index": idx,
                "cue_text_sha256": sha256(src.cues[idx-1].text.encode("utf8")),
                "reason_code": "OTHER_SOURCE_FIRST_RISK",
                "private_chat_cue_review_sha256": sha256(canonical(note_row)),
                "source_first_context_reviewed": True,
            } for idx, note_row in zip(
                self._mandatory(), self.synthetic_note["cue_rows"])],
            "audio_authenticity_verified": False,
            "semantic_claims_independently_verified": False,
            "p0_go": False,
        }

    def _pins(self):
        return {
            "externally_pinned_receipt_sha256":
                sha256(canonical(self.receipt)),
            "externally_pinned_source_note_sha256":
                sha256(canonical(self.synthetic_note)),
            "externally_pinned_prequarantine_sha256":
                sha256(canonical(self.escrow)),
        }

    def verify(self, *, origin=None, receipt=None, note=None, escrow=None,
               pins=None):
        return verify_real_turn2_private_custody(
            origin=self.origin if origin is None else origin,
            second_receipt=self.receipt if receipt is None else receipt,
            private_source_note=self.synthetic_note if note is None else note,
            prequarantine=self.escrow if escrow is None else escrow,
            **(self.pins if pins is None else pins))

    def test_01_synthetic_internal_second_turn_and_quarantine_valid(self):
        result = self.verify()
        self.assertEqual(result["unapproved_atoms"], 3)
        self.assertEqual(result["unapproved_source_cues_escrowed"],
                         len(self._mandatory()))
        self.assertFalse(result["host_user_turns_cryptographically_proven"])
        self.assertFalse(result["e3_final_approved"])

    def test_02_receipt_wrong_pin_rejected_before_staging(self):
        with self.assertRaisesRegex(InvalidInput, "SECOND_RECEIPT_BYTE_PIN"):
            self.verify(pins=dict(self.pins,
                         externally_pinned_receipt_sha256="a"*64))

    def test_03_note_changed_with_same_count_rejected(self):
        note = copy.deepcopy(self.synthetic_note)
        note["cue_rows"][0]["source_grounded_review_reason"] += " fake"
        with self.assertRaisesRegex(InvalidInput, "PRIVATE_NOTE_BYTE_PIN"):
            self.verify(note=note)

    def test_04_note_changed_with_recomputed_pin_still_rejected(self):
        note = copy.deepcopy(self.synthetic_note)
        note["cue_rows"][0]["source_grounded_review_reason"] += " fake"
        pins = dict(self.pins,
                    externally_pinned_source_note_sha256=
                        sha256(canonical(note)))
        with self.assertRaisesRegex(InvalidInput,
                                    "PREQUARANTINE_NOTE_BINDING"):
            self.verify(note=note, pins=pins)

    def test_05_escrow_row_hash_wrong_even_when_all_pins_recomputed(self):
        escrow = copy.deepcopy(self.escrow)
        escrow["cue_rows"][0]["private_chat_cue_review_sha256"] = "a"*64
        pins = dict(self.pins,
                    externally_pinned_prequarantine_sha256=
                        sha256(canonical(escrow)))
        with self.assertRaisesRegex(InvalidInput,
                                    "PREQUARANTINE_CUE_NOTE_NOT_MATCHED"):
            self.verify(escrow=escrow, pins=pins)

    def test_06_one_unresolved_cue_missing_fails(self):
        note = copy.deepcopy(self.synthetic_note)
        note["cue_rows"].pop()
        pins = dict(self.pins,
                    externally_pinned_source_note_sha256=
                        sha256(canonical(note)))
        with self.assertRaisesRegex(InvalidInput,
                                    "PRIVATE_NOTE_CENSUS"):
            self.verify(note=note, pins=pins)

    def test_07_false_authority_in_private_note_rejected(self):
        note = copy.deepcopy(self.synthetic_note)
        note["e3_formal_approved"] = True
        escrow = copy.deepcopy(self.escrow)
        escrow["private_review_sha256"] = sha256(canonical(note))
        pins = dict(
            externally_pinned_receipt_sha256=self.pins[
                "externally_pinned_receipt_sha256"],
            externally_pinned_source_note_sha256=sha256(canonical(note)),
            externally_pinned_prequarantine_sha256=sha256(canonical(escrow)))
        with self.assertRaisesRegex(InvalidInput,
                                    "PRIVATE_NOTE_SOURCE_OR_AUTHORITY"):
            self.verify(note=note, escrow=escrow, pins=pins)

    def test_08_native_host_remains_blocked_without_prior_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            store = TransactionStore(Path(d)/"real.db")
            with self.assertRaisesRegex(InvalidInput,
                                        "PRIOR_RELATION_INPUT_SCHEMA"):
                stage_after_verified_private_turn2(
                    origin=self.origin, second_receipt=self.receipt,
                    private_source_note=self.synthetic_note,
                    prequarantine=self.escrow,
                    native_store=store, scope_id="v231_hold",
                    run_id="v231_trial",
                    externally_pinned_inventory_sha256=
                        self.origin["inventory_sha256"],
                    prior_knowledge={},
                    explicit_private_host_stage=True, **self.pins)
            with self.assertRaisesRegex(InvalidInput, "SCOPE_UNKNOWN"):
                store.snapshot("v231_hold")

    def test_09_no_implicit_stage_permission(self):
        with tempfile.TemporaryDirectory() as d:
            store = TransactionStore(Path(d)/"real.db")
            with self.assertRaisesRegex(InvalidInput,
                                        "EXPLICIT_STAGING_PERMISSION"):
                stage_after_verified_private_turn2(
                    origin=self.origin, second_receipt=self.receipt,
                    private_source_note=self.synthetic_note,
                    prequarantine=self.escrow,
                    native_store=store, scope_id="v231_no",
                    run_id="v231_trial",
                    externally_pinned_inventory_sha256=
                        self.origin["inventory_sha256"],
                    prior_knowledge={},
                    **self.pins)


if __name__ == "__main__":
    unittest.main()
