"""V201 E1 only: native source-to-ledger bridge.

Connect a real V176 original-source/ChatGPT journal to the frozen V6
TransactionStore owner/source attestation and atomic candidate audit.
It does NOT invoke E2 adjudication, E3 final approval, E4, or E5.
A connected unapproved read path is not an E1 end-to-end PASS.
"""
from __future__ import annotations

from ire.v6 import TransactionStore
from ire.v6.trust import verify_owner_inventory
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession

SCHEMA = "IRE_V201_E1_PRIVATE_NATIVE_SOURCE_BRIDGE_V1"


def _need(ok, code):
    if not ok:
        raise InvalidInput("V201_E1_" + code)


def bridge_v176_to_v6(
    engine: EngineChatSession,
    ledger: TransactionStore,
    *,
    scope_id: str,
    inventory_bytes: bytes,
    expected_inventory_sha256: str,
    expected_owner_head: str,
    new_scope: bool = False,
):
    """Bridge actual audit objects only, without self-authorizing approval.

    Caller must retain the owner head independently and the inventory SHA
    externally. For new_scope, the target scope must not already exist.
    For resumes, ONLY a previously source+owner-attested V6 scope is valid.
    Both SQLite journals remain PRIVATE. No transcript bytes are returned.
    """
    _need(type(engine) is EngineChatSession and type(ledger) is TransactionStore,
          "ACTUAL_V176_AND_V6_INSTANCES_REQUIRED")
    _need(type(new_scope) is bool, "EXPLICIT_NEW_SCOPE_FLAG_REQUIRED")
    progress = engine.progress()
    _need(type(expected_owner_head) is str and
          progress["checkpoint_head_sha256"] == expected_owner_head,
          "EXTERNAL_OWNER_HEAD_DRIFT")
    exchange, staged = engine.compile_native_v6_stage()
    _need(exchange["source_sha256"] == progress["source_sha256"] ==
          staged["source_sha256"], "SOURCE_DIGEST_DRIFT")
    _need(staged["checkpoint_head_sha256"] == expected_owner_head,
          "STAGED_OWNER_HEAD_DRIFT")
    _need(staged["native_v6_audit"] is not None and
          staged["final_approval"] is False, "NATIVE_AUDIT_NOT_PROVEN")

    # Recheck external inventory bytes BEFORE any V6 writes. This does not
    # prove the identity of the owner or the independent origin of the pin.
    verified = verify_owner_inventory(
        engine.raw, engine.manifest, inventory_bytes,
        expected_inventory_sha256=expected_inventory_sha256)
    _need(verified.source.source_sha256 == progress["source_sha256"],
          "OWNER_SOURCE_SCOPE_DRIFT")

    if new_scope:
        # V6 create_scope is deliberately idempotent for identical command IDs.
        # The E1 operator explicitly requesting a *new* session must NOT
        # silently replay or reuse an already existing scope.
        try:
            ledger.snapshot(scope_id)
        except InvalidInput as exc:
            if "SCOPE_UNKNOWN" not in str(exc):
                raise
        else:
            raise InvalidInput("V201_E1_NEW_SCOPE_ALREADY_EXISTS")
        created = ledger.create_scope(
            scope_id=scope_id,
            video_id=engine.source.video_id,
            source_sha256=progress["source_sha256"],
            manifest_sha256=engine.source.manifest_sha256,
            command_id="v201_e1_new_scope")
        attested = ledger.attest_source(
            scope_id=scope_id, command_id="v201_e1_attest_source",
            expected_head=created["event_sha256"],
            raw=engine.raw, manifest=engine.manifest)
        ledger.attest_owner_inventory(
            scope_id=scope_id, command_id="v201_e1_attest_inventory",
            expected_head=attested["event_sha256"],
            raw=engine.raw, manifest=engine.manifest,
            inventory_bytes=inventory_bytes,
            expected_inventory_sha256=expected_inventory_sha256)
    else:
        # The original native transaction store will fail closed if the
        # scope or trusted owner/source attestation is absent.
        state = ledger.snapshot(scope_id)["state"]
        _need(state["source"]["source_sha256"] == progress["source_sha256"] and
              state["source"]["manifest_sha256"] == engine.source.manifest_sha256,
              "NATIVE_SCOPE_SOURCE_OR_MANIFEST_MISMATCH")

    native = ledger.snapshot_with_atomic_exchange(
        scope_id=scope_id,
        raw=engine.raw,
        manifest=engine.manifest,
        inventory_bytes=inventory_bytes,
        expected_inventory_sha256=expected_inventory_sha256,
        exchange=exchange)
    _need(native["source_original_bytes_verified_this_call"] is True and
          native["financial_facts_approved"] is False and
          native["research_complete"] is False and
          native["p0_go"] is False, "NATIVE_SNAPSHOT_AUTHORITY_ESCALATION")
    n = native["atomic_audit"]
    _need(type(n) is dict and "schema" in n, "NATIVE_ATOMIC_REPORT_MISSING")

    return {
        "schema": SCHEMA,
        "scope_id": scope_id,
        "source_sha256": progress["source_sha256"],
        "owner_head_sha256": expected_owner_head,
        "native_v6_head_sha256": native["ledger_head_sha256"],
        "source_cue_total": progress["cue_total"],
        "source_cue_reviewed": progress["cue_reviewed"],
        "source_first_review_complete": progress["source_first_review_complete"],
        "native_atomic_audit_schema": n["schema"],
        "native_read_snapshot_replayed": True,
        "owner_identity_cryptographically_attested": False,
        "e1_status": "HOLD_APPROVAL_AND_STORAGE_PATH_NOT_CONNECTED",
        "e2_status": "NOT_ENTERED",
        "e3_status": "NOT_ENTERED",
        "e4_status": "NOT_ENTERED",
        "e5_status": "NOT_ENTERED",
        "all_stages_passed": False,
        "knowledge_published": 0,
    }
