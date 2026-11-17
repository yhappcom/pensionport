"""V161 additive, proof-bound evidence-scope layer around IMMUTABLE V123.

Never change historical V123 release function/bytes. Source-only speech acts
remain OPEN in actual V123 and never become V126/V128 research candidates.
"""
from __future__ import annotations

from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
from v123_chat_final_gate import assess_chat_final_gate
from v161_source_utterance_scope import audit_source_utterance_only


def assess_source_only_overlay_then_v123(
    source, exchange, *, host_receipt, chat_review, store,
    official_evidence_bodies, source_only_reviews: list[dict],
):
    """Account for source-first subdecisions, without changing native V123.

    One attested speech act can reduce remaining semantic review *tasks*;
    this does NOT reduce native V123 OPEN, financial evidence obligations,
    or V128 release requirements. Only original V123 authorizes export.
    """
    audit_host_atomic_exchange(source, exchange)
    if type(source_only_reviews) is not list:
        raise InvalidInput("V161_SOURCE_ONLY_OVERLAY_LIST_REQUIRED")
    atoms = {a["claim_id"]: a for a in exchange["atoms"]}
    native = {r["claim_id"]: r for r in chat_review["atom_verdicts"]}
    if len(native) != len(exchange["atoms"]):
        raise InvalidInput("V161_SOURCE_ONLY_ATOM_CENSUS")
    seen = set()
    proofs = []
    for row in source_only_reviews:
        if type(row) is not dict:
            raise InvalidInput("V161_SOURCE_ONLY_ROW_INVALID")
        cid = row.get("claim_id")
        if (cid not in atoms or cid in seen or
            row.get("atom_sha256") != json_digest(atoms[cid])):
            raise InvalidInput("V161_SOURCE_ONLY_CLAIM_DUPLICATE_OR_DRIFT")
        if native[cid]["status"] != "OPEN" or native[cid]["financial_claim"] is not True:
            raise InvalidInput("V161_SOURCE_ONLY_MUST_BE_NATIVE_V123_OPEN")
        seen.add(cid)
        proof = audit_source_utterance_only(source, atoms[cid], row,
                                            chat_review["source_cues"])
        proofs.append(proof)
    native_result = assess_chat_final_gate(
        source, exchange, host_receipt=host_receipt, chat_review=chat_review,
        store=store, official_evidence_bodies=official_evidence_bodies)
    if native_result["status"] not in {"CHAT_FINAL_HOLD_OPEN", "CHAT_FINAL_REJECTED"} and proofs:
        raise InvalidInput("V161_SOURCE_ONLY_CANNOT_MUTATE_ALREADY_PASSED_V123")
    if native_result["atoms_open"] < len(proofs):
        raise InvalidInput("V161_OVERLAY_MORE_PROOFS_THAN_NATIVE_OPEN")
    return {
        "schema": "V161_ADDITIVE_SOURCE_ONLY_OVERLAY_ON_NATIVE_V123_V1",
        "original_source_sha256": source.source_sha256,
        "native_v123_receipt": native_result,
        "native_v123_final_status_unchanged": native_result["status"],
        "native_v123_atoms_open_unchanged": native_result["atoms_open"],
        "original_speech_only_claims_pinned": len(proofs),
        "original_speech_only_claim_ids": [p["claim_id"] for p in proofs],
        "source_first_semantic_tasks_remaining": native_result["atoms_open"] - len(proofs),
        "native_finance_fact_evidence_open_unchanged": native_result["finance_open"],
        "financial_fact_verified_by_overlay": False,
        "research_export_allowed": False if proofs else native_result["research_candidate_export_allowed"],
        "v126_v128_knowledge_publish_allowed": False if proofs else native_result["research_candidate_export_allowed"],
        "personalized_advice_approved": False,
        "independent_gold": False,
        "p0_go": False,
        "proof_digest_sha256": json_digest(proofs),
    }
