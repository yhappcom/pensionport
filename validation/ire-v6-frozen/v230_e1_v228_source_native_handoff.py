"""V230: source-native E1 seam for a genuine V228 frozen private ETF source.

A NEW V6 source custody is not a recovered V176 journal. This module takes the
actual frozen V228 source and existing unapproved native V6 draft as inputs,
verifies their custody, and offers an optional REAL V6 host-only transaction.
It never invokes V123/V127/V128/V126 or manufactures ChatGPT turn-2 review.
Private material must never be written to a public Git repository.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ire.v6 import TransactionStore
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.prior_knowledge import audit_prior_candidates
from ire.v6.trust import verify_owner_inventory
from v176_chat_engine_loop import make_original_plan
from v203_e1_v176_origin_native_host_bridge import _native_models
from v228_v193_actual_two_turn_runtime_gate import verify_turn1_frozen, canonical as v228_canonical

SCHEMA = "IRE_V230_E1_V228_SOURCE_NATIVE_ORIGIN_HANDOFF_V1"
SECOND_SCHEMA = "IRE_V228_TWO_DISTINCT_USER_MESSAGE_E3_REVIEW_HOLD_RECEIPT_V1"


def require(ok: Any, reason: str) -> None:
    if not ok:
        raise InvalidInput("V230_E1_" + reason)


def read_v228_source_native(*, private_zip: Path,
                            externally_pinned_zip_sha256: str,
                            externally_pinned_manifest_sha256: str,
                            externally_pinned_first_head_sha256: str,
                            externally_pinned_source_sha256: str) -> dict:
    """Verify real frozen owner bytes. Returned source/exchange remain PRIVATE.

    The new V6 inventory is created from authenticated frozen source bytes;
    it DOES NOT constitute a V176 owner review or an owner identity signature.
    Its SHA must be independently pinned for any subsequent host transaction.
    """
    frozen = verify_turn1_frozen(
        private_zip=private_zip,
        externally_pinned_zip_sha256=externally_pinned_zip_sha256,
        externally_pinned_manifest_sha256=externally_pinned_manifest_sha256,
        externally_pinned_first_head_sha256=externally_pinned_first_head_sha256,
        externally_pinned_source_sha256=externally_pinned_source_sha256)
    require(frozen["phase"] == "AWAIT_SEPARATE_USER_VERIFICATION_COMMAND",
            "ACTUAL_FROZEN_FIRST_TURN_REQUIRED")
    raw = frozen["content"]["source.srt"]
    exchange = json.loads(frozen["content"]["native.json"])
    source, manifest = make_original_plan(
        raw, exchange["video_id"],
        expected_source_sha256=externally_pinned_source_sha256,
        window_size=frozen["manifest"]["window_size"])
    verified = audit_host_atomic_exchange(source, exchange)
    require(exchange["source_sha256"] == externally_pinned_source_sha256
            and exchange["manifest_sha256"] == source.manifest_sha256
            and verified["proposed_atomic_claims"] ==
            frozen["audit"]["unapproved_native_atoms"],
            "FROZEN_EXCHANGE_REINTERPRETED")
    inventory = {
        "schema": "IRE_V6_OWNER_INVENTORY_V1",
        "entries": [{
            "video_id": source.video_id,
            "source_sha256": source.source_sha256,
            "manifest_sha256": source.manifest_sha256,
            "cue_census_sha256": source.cue_census_sha256,
        }]
    }
    inventory_bytes = canonical(inventory)
    registry_pin = sha256(inventory_bytes)
    verify_owner_inventory(raw, manifest, inventory_bytes,
                           expected_inventory_sha256=registry_pin)
    models, reviews = _native_models(source, exchange)
    require(set(models) == {w for w, _, _ in source.primary_windows}
            and all(m["claims"] for m in models.values())
            and all(r["independent_gold_verified"] is False for r in reviews.values()),
            "EMPTY_OR_FALSELY_APPROVED_NATIVE_WINDOW")
    return {
        "schema": SCHEMA,
        "source": source, "source_raw": raw, "manifest": manifest,
        "exchange": exchange, "inventory_bytes": inventory_bytes,
        "inventory_sha256": registry_pin,
        "native_sha256": sha256(frozen["content"]["native.json"]),
        "frozen_zip_sha256": externally_pinned_zip_sha256,
        "frozen_turn1_head_sha256": externally_pinned_first_head_sha256,
        "source_sha256": source.source_sha256,
        "cue_count": frozen["audit"]["original_cues"],
        "unapproved_atoms": verified["proposed_atomic_claims"],
        "models": models, "reviews": reviews,
        "status": "V228_REAL_SOURCE_NATIVE_INPUT_PREPARED_NOT_YET_APPROVED",
        "recovered_v176_owner_journal": False,
        "turn2_chatgpt_review_verified": False,
        "e1_full_approval_store_path_proven": False,
        "e2_gold_approved": False,
        "e3_final_approved": False,
        "e4_authorized": False,
        "e5_published": 0,
    }


def safe_preflight_summary(origin: dict) -> dict:
    """Public-safe metadata only. Never include raw, models, exchange, source."""
    require(origin.get("schema") == SCHEMA, "ORIGIN_TYPE")
    return {k: origin[k] for k in (
        "schema", "source_sha256", "frozen_zip_sha256",
        "frozen_turn1_head_sha256", "inventory_sha256", "native_sha256",
        "cue_count", "unapproved_atoms", "status",
        "recovered_v176_owner_journal", "turn2_chatgpt_review_verified",
        "e1_full_approval_store_path_proven", "e2_gold_approved",
        "e3_final_approved", "e4_authorized", "e5_published"
    )}


def check_v228_real_turn2_receipt(origin: dict, second_receipt: dict) -> dict:
    """Check V228's ACTUAL emitted field names, not V229's mismatched keys.

    This validates record shape and pins; manually claimed USER IDs still are
    NOT cryptographically attested. No approval is granted by this function.
    """
    require(type(second_receipt) is dict and
            second_receipt.get("schema") == SECOND_SCHEMA,
            "ACTUAL_V228_SECOND_RECEIPT_SCHEMA_REQUIRED")
    review = second_receipt.get("turn2_review")
    require(type(review) is dict and
            review.get("phase") == "CHATGPT_FINAL_SEMANTIC_VERIFICATION" and
            review.get("turn1_frozen_head_sha256") ==
            origin["frozen_turn1_head_sha256"] and
            review.get("source_sha256") == origin["source_sha256"] and
            second_receipt.get("source_sha256") == origin["source_sha256"] and
            second_receipt.get("first_frozen_head_sha256") ==
            origin["frozen_turn1_head_sha256"] and
            second_receipt.get("second_review_head_sha256") ==
            sha256(v228_canonical(review)), "SECOND_RECEIPT_BINDING_OR_HASH")
    rows = review.get("source_only_review_rows")
    atoms = review.get("atom_adjudication_rows")
    require(type(rows) is list and len(rows) == origin["cue_count"] and
            type(atoms) is list and len(atoms) == origin["unapproved_atoms"] and
            {x.get("claim_id") for x in atoms if type(x) is dict} ==
            {a["claim_id"] for a in origin["exchange"]["atoms"]} and
            [x.get("cue_index") for x in rows if type(x) is dict] ==
            list(range(1, origin["cue_count"] + 1)), "TURN2_SOURCE_ATOM_CENSUS")
    require(review.get("e3_final_approved") is False and
            review.get("e4_approved") is False and
            review.get("e5_published") is False and
            second_receipt.get("e3_formal_approved") is False and
            second_receipt.get("e4_authorized") is False and
            second_receipt.get("e5_published") is False and
            review.get("host_user_turn_proven_by_cryptographic_id") is False,
            "SECOND_RECEIPT_FALSE_APPROVAL_OR_HOST_PROVENANCE")
    return {
        "status": "MANUAL_TURN2_RECORD_SHAPE_VALID_E3_STILL_HOLD",
        "turn2_host_cryptographically_proven": False,
        "e3_final_approved": False, "e4_authorized": False,
        "e5_published": 0
    }


def stage_unapproved_v228_native_host(*, origin: dict,
                                     native_store: TransactionStore,
                                     scope_id: str, run_id: str,
                                     externally_pinned_inventory_sha256: str,
                                     prior_knowledge: dict,
                                     explicit_private_host_stage: bool = False) -> dict:
    """Optional REAL V6 model/proof/host transaction from original V228 bytes.

    Stores only V6 source/model/host custody, never V123 approval or V126/128
    knowledge. All protected prior-knowledge bytes and pending relations must
    be supplied and audited. A failure may leave source-only metadata events
    in the private staging DB; it never writes approved knowledge.
    """
    require(explicit_private_host_stage is True, "EXPLICIT_STAGING_PERMISSION")
    require(type(origin) is dict and origin.get("schema") == SCHEMA and
            type(native_store) is TransactionStore and
            type(prior_knowledge) is dict, "PRIVATE_V6_INPUT_REQUIRED")
    require(externally_pinned_inventory_sha256 == origin["inventory_sha256"],
            "EXTERNALLY_PINNED_REGISTRY_MISMATCH")
    source, manifest = origin["source"], origin["manifest"]
    raw, exchange = origin["source_raw"], origin["exchange"]
    require(sha256(raw) == origin["source_sha256"] and
            audit_host_atomic_exchange(source, exchange)["proposed_atomic_claims"] ==
            origin["unapproved_atoms"], "SOURCE_NATIVE_DRIFT")
    verify_owner_inventory(raw, manifest, origin["inventory_bytes"],
                           expected_inventory_sha256=externally_pinned_inventory_sha256)
    audit_prior_candidates(source, exchange, prior_knowledge)
    # No synthetic ChatGPT approval callback, and no knowledge store here.
    first = native_store.create_scope(
        scope_id=scope_id, video_id=source.video_id,
        source_sha256=source.source_sha256,
        manifest_sha256=source.manifest_sha256,
        command_id="v230_v228_source_native_new_scope")
    second = native_store.attest_source(
        scope_id=scope_id, command_id="v230_v228_original_source",
        expected_head=first["event_sha256"], raw=raw, manifest=manifest)
    third = native_store.attest_owner_inventory(
        scope_id=scope_id, command_id="v230_v228_native_inventory",
        expected_head=second["event_sha256"], raw=raw, manifest=manifest,
        inventory_bytes=origin["inventory_bytes"],
        expected_inventory_sha256=externally_pinned_inventory_sha256)
    host = native_store.submit_host_atomic_batch(
        scope_id=scope_id, run_id=run_id, expected_head=third["event_sha256"],
        raw=raw, manifest=manifest, inventory_bytes=origin["inventory_bytes"],
        expected_inventory_sha256=externally_pinned_inventory_sha256,
        exchange=exchange, knowledge=prior_knowledge,
        window_models=origin["models"], window_reviews=origin["reviews"])
    require(host["atomic_batch_committed"] is True and
            host["semantic_truth_certified"] is False and
            native_store.snapshot(scope_id)["ledger_head_sha256"] ==
            host["event_sha256"], "NATIVE_HOST_TRANSACTION_NOT_VERIFIED")
    return {
        "schema": SCHEMA,
        "status": "V228_ACTUAL_SOURCE_NATIVE_V6_HOST_STAGED_UNAPPROVED",
        "source_sha256": source.source_sha256,
        "frozen_turn1_head_sha256": origin["frozen_turn1_head_sha256"],
        "new_v6_host_event_sha256": host["event_sha256"],
        "new_v6_owner_inventory_sha256": externally_pinned_inventory_sha256,
        "unapproved_atoms": origin["unapproved_atoms"],
        "recovered_v176_owner_journal": False,
        "e1_full_approval_store_path_proven": False,
        "e3_final_approved": False, "e4_authorized": False, "e5_published": 0,
    }
