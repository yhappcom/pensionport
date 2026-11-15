"""V123 supported P1 candidate preview: a mandatory ChatGPT-last gate.

The older audit_prior_candidates is an internal consistency checker and does
not publish new knowledge. This read-only preview is the supported outward
research candidate interface: software PASS without chat review is insufficient.
"""
from __future__ import annotations

from .chat_final_gate import require_chat_final_release
from .codec import json_digest
from .prior_knowledge import audit_prior_candidates


def preview_chat_validated_candidates(source, exchange, knowledge, *,
                                      host_receipt, chat_review, store):
    gate = require_chat_final_release(
        source, exchange, host_receipt=host_receipt, chat_review=chat_review, store=store)
    prior = audit_prior_candidates(source, exchange, knowledge)
    return {
        "schema": "IRE_V6_CHAT_FINAL_P1_READONLY_PREVIEW_V123",
        "status": "CHAT_REVIEWED_RESEARCH_CANDIDATES_READONLY",
        "source_sha256": gate["source_sha256"],
        "candidate_digest_sha256": gate["atom_candidate_digest"],
        "chat_review_sha256": gate["chat_final_review_digest_sha256"],
        "candidate_count": gate["atoms_accepted"],
        "existing_knowledge_reconciliation": "PENDING_READONLY",
        "prior_knowledge_audit_sha256": json_digest(prior),
        "master_p4_merged": False,
        "financial_fact_approved": 0,
        "personal_advice_approved": False,
        "p0_go": False,
    }
