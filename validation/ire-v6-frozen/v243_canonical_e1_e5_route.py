"""V243 official E1→ChatGPT V123/E3→V166 E4→V128 E5 route.

No LLM API. The ChatGPT HOST must supply source-first callbacks and attest that
TWO distinct actual USER turns occurred. Caller-controlled manual turn refs
are NOT an attestation. With the existing V193 checker the only real outcome is
HOLD; do not bypass this by asking a model to certify itself.

The sole documented external research-publication interface is
run_canonical_research_route(). Legacy modules remain internal/history; no
standalone "publish" CLI is exported by this module. Python imports are not a
security boundary; a legacy direct-V126 write can physically modify SQLite but
cannot produce an externally pinned V166 E4 seal.
"""
from __future__ import annotations

from ire.v6.codec import ZERO_SHA
from ire.v6.errors import InvalidInput, QualityNotProven
from v193_e3_two_user_turn_contract import validate_manual_turn_receipt
from v166_e4_sealed_knowledge import E4SealedKnowledgeStore
from v166_e4_primary_approval_gate import run_e4_guarded_parent

SCHEMA = "IRE_V243_CANONICAL_E1_E5_RESEARCH_ROUTE_V1"
__all__ = ("run_canonical_research_route",)


def _hold(checkpoint, *, reason, manual):
    return {
        "schema": SCHEMA,
        "status": "HOLD_E3_HOST_TURN_PROVENANCE_NOT_VERIFIED",
        "reason_code": reason,
        "source_sha256": checkpoint.parent.source_sha256,
        "checkpoint_head_sha256": checkpoint.progress()["checkpoint_head_sha256"],
        "claimed_distinct_user_commands": manual["recorded_distinct_user_commands"],
        "trusted_host_two_user_turns_verified": False,
        "e4_invoked": False,
        "e5_invoked": False,
        "all_video_knowledge_published": False,
        "formal_financial_fact_approved": False,
        "personal_advice_approved": False,
        "p0_go": False,
    }


def run_canonical_research_route(
    checkpoint, knowledge_store, *,
    first_user_turn: dict, second_user_turn: dict | None,
    source_sha256: str, owner_freeze_sha256: str,
    expected_knowledge_head: str,
    review_or_load_child, review_seams, review_parent,
    primary_manifest_for_child, typed_inventory_for_child,
    typed_manifest_for_child, now_as_of: str,
) -> dict:
    """One *supported* executable API; fail closed before all E4/E5 writes.

    The only transport binding that could allow the approved E4 runner to
    execute is a trusted host-verified two-turn contract. Current V193 manual
    receipts explicitly do NOT prove host provenance, even when references
    are distinct. This function deliberately refuses publication until a
    real ChatGPT host attestation service replaces that verification boundary.

    A synthetic unit test can replace the verifier to exercise the wired
    V123→E4→V128 path. It is NEVER a live owner-approval certification.
    """
    if not isinstance(knowledge_store, E4SealedKnowledgeStore):
        raise InvalidInput("V243_E4_SEALED_KNOWLEDGE_STORE_REQUIRED")
    if not all(callable(fn) for fn in (
        review_or_load_child,review_seams,review_parent,
        primary_manifest_for_child,typed_inventory_for_child,typed_manifest_for_child
    )):
        raise InvalidInput("V243_MANDATORY_HOST_AND_PRIMARY_CALLBACKS")
    if (type(source_sha256) is not str or type(owner_freeze_sha256) is not str or
        type(expected_knowledge_head) is not str):
        raise InvalidInput("V243_SOURCE_AND_HEAD_PINS_REQUIRED")
    progress=checkpoint.progress(externally_pinned_checkpoint_head=owner_freeze_sha256)
    if (checkpoint.parent.source_sha256 != source_sha256 or
        progress["checkpoint_head_sha256"] != owner_freeze_sha256):
        raise QualityNotProven("V243_OWNER_SOURCE_OR_FREEZE_DRIFT")
    if (type(checkpoint.child_ids) is not list or not checkpoint.child_ids or
        len(set(checkpoint.child_ids))!=len(checkpoint.child_ids)):
        raise InvalidInput("V243_CHILD_CENSUS_INVALID")

    manual=validate_manual_turn_receipt(
        first=first_user_turn,second=second_user_turn,
        source_sha256=source_sha256,owner_head_sha256=owner_freeze_sha256,
        batch_count=len(checkpoint.child_ids),
        independent_gold_certified=False,
        e3_approved=False,v123_e4_approved=False,e5_published=False)
    if (manual.get("host_separate_turns_verified") is not True or
        manual.get("two_user_turns_proven") is not True):
        return _hold(checkpoint,
            reason="CALLER_MANUAL_REFS_ARE_NOT_TRUSTED_CHAT_HOST_EVENTS",
            manual=manual)
    # This branch MUST NOT become reachable via untrusted user/CLI flags.
    # Host attestation and actual separate user turns are an unresolved P101
    # release prerequisite. In CI only, the verifier is mock-replaced.
    outcome=run_e4_guarded_parent(
        checkpoint,knowledge_store,
        review_or_load_child=review_or_load_child,
        review_seams=review_seams,review_parent=review_parent,
        primary_manifest_for_child=primary_manifest_for_child,
        typed_inventory_for_child=typed_inventory_for_child,
        typed_manifest_for_child=typed_manifest_for_child,
        expected_knowledge_head=expected_knowledge_head,
        now_as_of=now_as_of)
    if outcome.get("schema")!="IRE_V166_E4_PARENT_APPROVAL_V1":
        raise QualityNotProven("V243_E4_ROUTE_RECEIPT_INVALID")
    approved=outcome.get("status")=="E4_PARENT_RESEARCH_CANDIDATES_PUBLISHED"
    if approved != (outcome.get("all_video_knowledge_published") is True):
        raise QualityNotProven("V243_E4_E5_STATUS_DIVERGENCE")
    if (outcome.get("formal_financial_fact_formally_approved") is True or
        outcome.get("financial_fact_formally_approved") is True or
        outcome.get("personal_advice_approved") is True or outcome.get("p0_go") is True):
        raise QualityNotProven("V243_FALSE_FINANCIAL_FACT_OR_ADVISORY_GO")
    return {
        "schema": SCHEMA,
        "status": ("SYNTHETIC_PATH_REPLAYED_RESEARCH_CANDIDATES_ONLY"
                   if approved else "HOLD_E4_PRIMARY_EVIDENCE"),
        "source_sha256": source_sha256,
        "checkpoint_head_sha256": checkpoint.progress()["checkpoint_head_sha256"],
        "claimed_distinct_user_commands":manual["recorded_distinct_user_commands"],
        "trusted_host_two_user_turns_verified": True,
        "e4_invoked": True,
        "e4_receipt": outcome,
        "e5_invoked": True,
        "all_video_knowledge_published": approved,
        "formal_financial_fact_approved": False,
        "personal_advice_approved": False,
        "p0_go": False,
    }
