"""V230 E1 regressions: synthetic V228 origin, no fake V176 and no publication."""
from __future__ import annotations

import copy
import tempfile
import test_v202_e1_v176_native_positive_path as v202_fixture
import unittest
from pathlib import Path

from ire.v6 import TransactionStore
from ire.v6.codec import sha256
from ire.v6.claim_census import FINANCIAL, QUALIFIER, MULTI_CLAIM
from ire.v6.errors import InvalidInput
from ire.v6.trust import verify_owner_inventory
from test_v227_e2_source_semantic_reconciliation import synthetic
from test_v228_v193_actual_two_turn_runtime_gate import make_input, pins
from v228_v193_actual_two_turn_runtime_gate import (
    freeze_turn1_private, canonical as v228_canonical)
from v230_e1_v228_source_native_handoff import (
    SECOND_SCHEMA, read_v228_source_native, safe_preflight_summary,
    check_v228_real_turn2_receipt, stage_unapproved_v228_native_host)


class TestV230RealSourceNativeBoundary(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        docs, *_ = synthetic()
        self.freeze = freeze_turn1_private(**make_input(docs, self.root))
        self.pins = pins(self.freeze, self.root / "first.zip")
        self.origin = read_v228_source_native(**self.pins)

    def review_receipt(self):
        origin = self.origin
        cues = []
        for i, cue in enumerate(origin["source"].cues, 1):
            cues.append({
                "cue_index": i,
                "quote": cue.text,
                "quote_sha256": sha256(cue.text.encode("utf8")),
                "disposition": "QUESTION",
                "review_reason": "SYNTHETIC source cue assessment only",
                "is_independent_blind_gold": False,
                "financial_fact_approved": False,
            })
        atoms = [{
            "claim_id": a["claim_id"],
            "disposition": "HOLD",
            "source_grounded_reason": "SYNTHETIC unapproved atom held",
            "e3_final_approved": False,
            "financial_fact_approved": False,
            "independent_gold_certified": False,
        } for a in origin["exchange"]["atoms"]]
        review = {
            "phase": "CHATGPT_FINAL_SEMANTIC_VERIFICATION",
            "source_sha256": origin["source_sha256"],
            "turn1_frozen_head_sha256": origin["frozen_turn1_head_sha256"],
            "second_user_ref_manual": "user:synthetic-turn2-not-host-attested",
            "source_only_review_rows": cues,
            "atom_adjudication_rows": atoms,
            "review_complete_as_internal_not_blind_gold": True,
            "host_user_turn_proven_by_cryptographic_id": False,
            "e3_final_approved": False, "e4_approved": False,
            "e5_published": False,
        }
        return {
            "schema": SECOND_SCHEMA,
            "source_sha256": origin["source_sha256"],
            "first_frozen_head_sha256": origin["frozen_turn1_head_sha256"],
            "second_review_head_sha256": sha256(v228_canonical(review)),
            "turn1_manual_message_ref": origin["turn1_manual_user_ref"],
            "turn2_manual_message_ref": review["second_user_ref_manual"],
            "turn2_review": review,
            "e3_formal_approved": False,
            "e4_authorized": False,
            "e5_published": False,
            "independent_blind_gold_certified": False,
        }

    def test_01_genuine_v228_source_is_native_v6_input_not_v176(self):
        x = self.origin
        self.assertEqual(x["cue_count"], 8)
        self.assertEqual(x["unapproved_atoms"], 3)
        self.assertFalse(x["recovered_v176_owner_journal"])
        self.assertEqual(x["status"],
                         "V228_REAL_SOURCE_NATIVE_INPUT_PREPARED_NOT_YET_APPROVED")
        self.assertFalse(x["e1_full_approval_store_path_proven"])

    def test_02_new_inventory_is_valid_private_v6_source_pin(self):
        x = self.origin
        anchor = verify_owner_inventory(
            x["source_raw"], x["manifest"], x["inventory_bytes"],
            expected_inventory_sha256=x["inventory_sha256"])
        self.assertEqual(anchor.source.source_sha256, x["source_sha256"])
        self.assertFalse(anchor.attestation()["owner_identity_verified"])

    def test_03_public_receipt_does_not_export_owner_bytes_or_atoms(self):
        x = safe_preflight_summary(self.origin)
        self.assertNotIn("source_raw", x)
        self.assertNotIn("source", x)
        self.assertNotIn("exchange", x)
        self.assertNotIn("models", x)
        self.assertNotIn("inventory_bytes", x)
        self.assertEqual(x["e5_published"], 0)

    def test_04_first_turn_digest_tampering_rejected(self):
        with self.assertRaises(InvalidInput):
            read_v228_source_native(**dict(
                self.pins, externally_pinned_zip_sha256="0"*64))

    def test_05_first_head_tampering_rejected(self):
        with self.assertRaises(InvalidInput):
            read_v228_source_native(**dict(
                self.pins, externally_pinned_first_head_sha256="0"*64))

    def test_06_no_automatic_host_stage(self):
        store = TransactionStore(self.root / "stage" / "source.db")
        with self.assertRaisesRegex(InvalidInput, "EXPLICIT_STAGING_PERMISSION"):
            stage_unapproved_v228_native_host(
                origin=self.origin, native_store=store,
                scope_id="v230_scope", run_id="v230_trial",
                externally_pinned_inventory_sha256=self.origin["inventory_sha256"],
                prior_knowledge={})
        with self.assertRaisesRegex(InvalidInput, "SCOPE_UNKNOWN"):
            store.snapshot("v230_scope")

    def test_07_wrong_inventory_pin_precedes_any_db_write(self):
        store = TransactionStore(self.root / "stage" / "source.db")
        with self.assertRaisesRegex(InvalidInput, "EXTERNALLY_PINNED_REGISTRY_MISMATCH"):
            stage_unapproved_v228_native_host(
                origin=self.origin, native_store=store,
                scope_id="v230_scope", run_id="v230_trial",
                externally_pinned_inventory_sha256="0"*64,
                prior_knowledge={}, explicit_private_host_stage=True)
        with self.assertRaisesRegex(InvalidInput, "SCOPE_UNKNOWN"):
            store.snapshot("v230_scope")

    def test_08_missing_protected_prior_relations_fail_before_db_write(self):
        store = TransactionStore(self.root / "stage" / "source.db")
        with self.assertRaisesRegex(InvalidInput, "PRIOR_RELATION_INPUT_SCHEMA"):
            stage_unapproved_v228_native_host(
                origin=self.origin, native_store=store,
                scope_id="v230_scope", run_id="v230_trial",
                externally_pinned_inventory_sha256=self.origin["inventory_sha256"],
                prior_knowledge={}, explicit_private_host_stage=True)
        with self.assertRaisesRegex(InvalidInput, "SCOPE_UNKNOWN"):
            store.snapshot("v230_scope")

    def test_09_v228_real_second_turn_field_names_are_supported(self):
        result = check_v228_real_turn2_receipt(self.origin, self.review_receipt())
        self.assertEqual(result["status"],
                         "MANUAL_TURN2_RECORD_SHAPE_VALID_E3_STILL_HOLD")
        self.assertFalse(result["turn2_host_cryptographically_proven"])
        self.assertEqual(result["e5_published"], 0)

    def test_10_v229_legacy_mismatched_head_key_cannot_bypass(self):
        bad = self.review_receipt()
        bad["owner_first_turn_head_sha256"] = bad.pop("first_frozen_head_sha256")
        with self.assertRaisesRegex(InvalidInput, "SECOND_RECEIPT_BINDING_OR_HASH"):
            check_v228_real_turn2_receipt(self.origin, bad)

    def test_11_v228_turn2_cue_quote_forgery_fails(self):
        bad = self.review_receipt()
        bad["turn2_review"]["source_only_review_rows"][0]["quote"] = "FAKE"
        bad["second_review_head_sha256"] = sha256(v228_canonical(bad["turn2_review"]))
        with self.assertRaisesRegex(InvalidInput, "SECOND_RECEIPT_SOURCE_MEANING_ROW"):
            check_v228_real_turn2_receipt(self.origin, bad)

    def test_12_v228_turn2_claim_coverage_missing_fails(self):
        bad = self.review_receipt()
        bad["turn2_review"]["atom_adjudication_rows"].pop()
        bad["second_review_head_sha256"] = sha256(v228_canonical(bad["turn2_review"]))
        with self.assertRaisesRegex(InvalidInput, "TURN2_SOURCE_ATOM_CENSUS"):
            check_v228_real_turn2_receipt(self.origin, bad)

    def test_13_same_manual_user_ref_cannot_be_second_turn(self):
        bad = self.review_receipt()
        bad["turn2_manual_message_ref"] = self.origin["turn1_manual_user_ref"]
        bad["turn2_review"]["second_user_ref_manual"] = bad["turn2_manual_message_ref"]
        bad["second_review_head_sha256"] = sha256(v228_canonical(bad["turn2_review"]))
        with self.assertRaisesRegex(InvalidInput, "SECOND_RECEIPT_DISTINCT_MANUAL_REF_REQUIRED"):
            check_v228_real_turn2_receipt(self.origin, bad)

    def test_14_claimed_e3_approval_is_rejected(self):
        bad = self.review_receipt()
        bad["e3_formal_approved"] = True
        with self.assertRaisesRegex(InvalidInput, "SECOND_RECEIPT_FALSE_APPROVAL"):
            check_v228_real_turn2_receipt(self.origin, bad)

    def test_15_bad_host_type_may_not_replace_real_v6_store(self):
        with self.assertRaisesRegex(InvalidInput, "PRIVATE_V6_INPUT_REQUIRED"):
            stage_unapproved_v228_native_host(
                origin=self.origin, native_store=object(),
                scope_id="v230_scope", run_id="v230_trial",
                externally_pinned_inventory_sha256=self.origin["inventory_sha256"],
                prior_knowledge={}, explicit_private_host_stage=True)


    def test_16_real_v6_host_only_structural_synthetic_positive(self):
        # The native inputs are from fresh V228 freeze, NOT the V176 test owner.
        # Protected legacy bytes come from the V202 fixture, and all current
        # 8-cue atomic relations are explicitly OPEN/novel, not approved.
        fx = v202_fixture.TestV202SameInputE1Route(
            "test_01_preseeded_native_v166_cannot_impersonate_v176_verdict")
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        previous = fx.fx.fx.packets[0]["case"]["prior_knowledge"]
        pending = copy.deepcopy(previous)
        pending["relations"] = [{
            "claim_id": a["claim_id"],
            "candidate_source_sha256": self.origin["source_sha256"],
            "target_kind": "NONE",
            "target_id": None,
            "target_content_sha256": None,
            "relationship": "NOVEL_PENDING",
            "rationale": "SYNTHETIC novel relation remains unapproved",
            "independent_semantic_review_verified": False,
            "personalized_action_approved": False,
        } for a in self.origin["exchange"]["atoms"]]
        # Synthetic fixture ONLY: explicitly authored source-first ChatGPT
        # quarantine attestation, not constructed by the production bridge.
        mandatory = []
        for row in self.origin["exchange"]["cue_dispositions"]:
            idx = row["cue_index"]
            cue = self.origin["source"].cues[idx-1].text
            risky = bool(FINANCIAL.search(cue) or QUALIFIER.search(cue) or
                         MULTI_CLAIM.search(cue))
            if row["disposition"] == "UNRESOLVED" or (
                    row["disposition"] == "NO_ATOM" and risky):
                mandatory.append(idx)
        prequarantine = {
            "schema": "IRE_V6_HOST_SOURCE_PREQUARANTINE_V145",
            "source_sha256": self.origin["source_sha256"],
            "manifest_sha256": self.origin["source"].manifest_sha256,
            "review_executor": "CHATGPT_IN_CHAT",
            "private_review_sha256": sha256(b"SYNTHETIC explicit cue review"),
            "cue_rows": [{
                "cue_index": idx,
                "cue_text_sha256": sha256(
                    self.origin["source"].cues[idx-1].text.encode("utf8")),
                "reason_code": "OTHER_SOURCE_FIRST_RISK",
                "private_chat_cue_review_sha256": sha256(
                    f"SYNTHETIC risk cue {idx}".encode()),
                "source_first_context_reviewed": True,
            } for idx in mandatory],
            "audio_authenticity_verified": False,
            "semantic_claims_independently_verified": False,
            "p0_go": False,
        }
        stage = TransactionStore(self.root / "new_source" / "v230.db")
        out = stage_unapproved_v228_native_host(
            origin=self.origin,
            native_store=stage,
            scope_id="v230_real_native_source_scope",
            run_id="v230_unapproved_synthetic_trial",
            externally_pinned_inventory_sha256=self.origin["inventory_sha256"],
            prior_knowledge=pending,
            source_prequarantine=prequarantine,
            explicit_private_host_stage=True)
        self.assertEqual(out["status"],
                         "V228_ACTUAL_SOURCE_NATIVE_V6_HOST_STAGED_UNAPPROVED")
        self.assertEqual(stage.snapshot("v230_real_native_source_scope")[
            "ledger_head_sha256"], out["new_v6_host_event_sha256"])
        self.assertFalse(out["recovered_v176_owner_journal"])
        self.assertFalse(out["e1_full_approval_store_path_proven"])
        self.assertFalse(out["e3_final_approved"])
        self.assertEqual(out["e5_published"], 0)


if __name__ == "__main__":
    unittest.main()
