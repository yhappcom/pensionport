"""V231: bind ACTUAL V228 manual turn-2 source review to V145 private V6 escrow.

This strengthens the V230 E1 seam: a 64-character hash alone is not proof of
a real ChatGPT source review. Verify the private note's *bytes*, every source
cue review reason, and each independently hashed V145 escrow row before ANY
host transaction. This never certifies real host message IDs, blind gold,
financial truth, E3 final approval, E4 authorization, or E5 publication.
"""
from __future__ import annotations

from typing import Any

from ire.v6.claim_census import FINANCIAL, QUALIFIER, MULTI_CLAIM
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.host_quarantine_preflight import audit_host_quarantine_preflight
from v228_v193_actual_two_turn_runtime_gate import canonical as v228_canonical
from v230_e1_v228_source_native_handoff import (
    SCHEMA, check_v228_real_turn2_receipt, require,
    stage_unapproved_v228_native_host,
)

NOTE_SCHEMA = "IRE_V231_CHATGPT_SECOND_TURN_SOURCE_FIRST_REVIEW_NOTE_V1"


def _mandatory(source, exchange):
    indices = []
    for row in exchange["cue_dispositions"]:
        i = row["cue_index"]
        body = source.cues[i-1].text
        risky = bool(FINANCIAL.search(body) or QUALIFIER.search(body)
                     or MULTI_CLAIM.search(body))
        if row["disposition"] == "UNRESOLVED" or (
                row["disposition"] == "NO_ATOM" and risky):
            indices.append(i)
    return indices


def verify_real_turn2_private_custody(
        *, origin: dict, second_receipt: dict,
        private_source_note: dict, prequarantine: dict,
        externally_pinned_receipt_sha256: str,
        externally_pinned_source_note_sha256: str,
        externally_pinned_prequarantine_sha256: str) -> dict:
    """Fail closed on wrong private receipts and disconnected source-cue proofs.

    Pins must be held separately from these mutable objects. Passed message
    references are only manual claims; their user/turn identity is untrusted.
    """
    require(origin.get("schema") == SCHEMA, "ORIGIN_TYPE")
    require(type(second_receipt) is dict
            and sha256(v228_canonical(second_receipt))
            == externally_pinned_receipt_sha256, "SECOND_RECEIPT_BYTE_PIN")
    check_v228_real_turn2_receipt(origin, second_receipt)
    require(type(private_source_note) is dict
            and sha256(v228_canonical(private_source_note))
            == externally_pinned_source_note_sha256, "PRIVATE_NOTE_BYTE_PIN")
    require(type(prequarantine) is dict
            and sha256(v228_canonical(prequarantine))
            == externally_pinned_prequarantine_sha256,
            "PREQUARANTINE_BYTE_PIN")
    note = private_source_note
    require(set(note) == {
        "schema", "source_sha256", "turn1_first_head_sha256",
        "turn2_review_sha256", "review_executor", "cue_rows",
        "independent_gold", "financial_fact_approved",
        "e3_formal_approved", "host_two_turns_crypto_verified"
    } and note["schema"] == NOTE_SCHEMA
            and note["source_sha256"] == origin["source_sha256"]
            and note["turn1_first_head_sha256"]
            == origin["frozen_turn1_head_sha256"]
            and note["turn2_review_sha256"]
            == second_receipt["second_review_head_sha256"]
            and note["review_executor"] == "CHATGPT_IN_CHAT"
            and note["independent_gold"] is False
            and note["financial_fact_approved"] is False
            and note["e3_formal_approved"] is False
            and note["host_two_turns_crypto_verified"] is False
            and type(note["cue_rows"]) is list,
            "PRIVATE_NOTE_SOURCE_OR_AUTHORITY")

    source, exchange = origin["source"], origin["exchange"]
    review_rows = second_receipt["turn2_review"]["source_only_review_rows"]
    mandatory = _mandatory(source, exchange)
    actual = note["cue_rows"]
    require(len(mandatory) == len(actual), "PRIVATE_NOTE_CENSUS")
    escrow_rows = prequarantine.get("cue_rows")
    require(type(escrow_rows) is list and len(escrow_rows) == len(mandatory)
            and prequarantine.get("private_review_sha256")
            == externally_pinned_source_note_sha256,
            "PREQUARANTINE_NOTE_BINDING")
    for idx, note_row, escrow_row in zip(mandatory, actual, escrow_rows):
        review_row = review_rows[idx-1]
        require(type(note_row) is dict and set(note_row) == {
            "cue_index", "quote_sha256", "review_disposition",
            "source_grounded_review_reason"
        } and note_row["cue_index"] == idx
                and note_row["quote_sha256"] == review_row["quote_sha256"]
                and note_row["review_disposition"] == review_row["disposition"]
                and note_row["source_grounded_review_reason"]
                == review_row["review_reason"],
                "PRIVATE_NOTE_CUE_MEANING_OR_QUOTE_DRIFT")
        require(type(escrow_row) is dict
                and escrow_row.get("cue_index") == idx
                and escrow_row.get("private_chat_cue_review_sha256")
                == sha256(v228_canonical(note_row)),
                "PREQUARANTINE_CUE_NOTE_NOT_MATCHED")
    escrow = audit_host_quarantine_preflight(
        source, exchange, prequarantine)
    require(escrow is not None and
            escrow["unresolved_original_cue_count"] == len(mandatory),
            "QUARANTINE_ACTUAL_SOURCE_CENSUS")
    return {
        "schema": "IRE_V231_E1_REAL_TURN2_TO_HOST_CUSTODY_V1",
        "status": "REAL_SOURCE_TURN2_NOTE_BINDED_E3_E4_E5_HOLD",
        "source_sha256": origin["source_sha256"],
        "second_receipt_sha256": externally_pinned_receipt_sha256,
        "second_review_head_sha256":
            second_receipt["second_review_head_sha256"],
        "private_source_note_sha256": externally_pinned_source_note_sha256,
        "prequarantine_sha256": externally_pinned_prequarantine_sha256,
        "unapproved_source_cues_escrowed": len(mandatory),
        "unapproved_atoms": origin["unapproved_atoms"],
        "host_user_turns_cryptographically_proven": False,
        "e1_full_approval_store_path_proven": False,
        "e3_final_approved": False,
        "e4_authorized": False, "e5_published": 0,
    }


def stage_after_verified_private_turn2(
        *, origin: dict, second_receipt: dict,
        private_source_note: dict, prequarantine: dict,
        externally_pinned_receipt_sha256: str,
        externally_pinned_source_note_sha256: str,
        externally_pinned_prequarantine_sha256: str,
        native_store: Any, scope_id: str, run_id: str,
        externally_pinned_inventory_sha256: str,
        prior_knowledge: dict,
        explicit_private_host_stage: bool = False) -> dict:
    """V231 checked input followed by V230's real V6 host-only writer.

    No unconditional E1 PASS: original protected prior116+29 bytes and
    pending decisions remain mandatory, and ALL output is unapproved.
    """
    require(explicit_private_host_stage is True,
            "EXPLICIT_STAGING_PERMISSION")
    proof = verify_real_turn2_private_custody(
        origin=origin, second_receipt=second_receipt,
        private_source_note=private_source_note,
        prequarantine=prequarantine,
        externally_pinned_receipt_sha256=externally_pinned_receipt_sha256,
        externally_pinned_source_note_sha256=
            externally_pinned_source_note_sha256,
        externally_pinned_prequarantine_sha256=
            externally_pinned_prequarantine_sha256)
    result = stage_unapproved_v228_native_host(
        origin=origin, native_store=native_store,
        scope_id=scope_id, run_id=run_id,
        externally_pinned_inventory_sha256=
            externally_pinned_inventory_sha256,
        prior_knowledge=prior_knowledge,
        source_prequarantine=prequarantine,
        explicit_private_host_stage=True)
    result["turn2_private_review_head_sha256"] = (
        proof["second_review_head_sha256"])
    result["v231_source_review_custody_verified"] = True
    return result
