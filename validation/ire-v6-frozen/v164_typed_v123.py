"""V164 — additive typed V123 ChatGPT final-semantics contract.

Does NOT mutate historical byte-frozen V123. It binds a tightly scoped ChatGPT
speech-act review to owner-original source bytes, original V6 host and native
V123 HOLD. Its source-only speech acts may be used for *research audit only*,
not factual investment knowledge, V128 publication or personalized advice.

Full typed research PASS is fail-closed until all factual/financial cases have
primary evidence, each high-risk omission is reconciled, and final disagreements
are resolved. In particular, a 0 count alone cannot certify completeness.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import VerifiedSource
from v123_chat_final_gate import assess_chat_final_gate

SCHEMA = "IRE_V164_CHAT_TYPED_SOURCE_SEMANTIC_REVIEW_V1"
ROW_SCHEMA = "IRE_V164_SOURCE_SPEECH_ACT_V1"
RECEIPT_SCHEMA = "IRE_V164_TYPED_FINAL_MEANING_PRECHECK_V1"

SPEECH_TYPES = frozenset({
    "RISK_QUESTION_ONLY",
    "BOOK_TO_INVESTMENT_META_PROPOSAL_ONLY",
    "CONDITIONAL_PAYOFF_HYPOTHESIS_ONLY",
    "PERSONAL_READING_IMPRESSION_ONLY",
    "INVESTMENT_CONVICTION_QUESTION_ONLY",
})

# This frozen pilot is intentionally specific to source-reviewed atoms. A
# generic word heuristic must never convert an actionable claim to nonfactual.
B0001_EXPECTED = {
    "C00001": ("HYPOTHETICAL", "RISK_QUESTION_ONLY"),
    "C00003": ("OPINION", "BOOK_TO_INVESTMENT_META_PROPOSAL_ONLY"),
    "C00277": ("OPINION", "CONDITIONAL_PAYOFF_HYPOTHESIS_ONLY"),
    "C00285": ("OPINION", "PERSONAL_READING_IMPRESSION_ONLY"),
    "C00293": ("QUESTION", "INVESTMENT_CONVICTION_QUESTION_ONLY"),
}


def _ensure(value: bool, code: str) -> None:
    if not value:
        raise InvalidInput("V164_TYPED_" + code)


def _cue_pin(source: VerifiedSource, indices: list[int]) -> str:
    return json_digest([
        {"cue_index": i, "cue_text_sha256": sha256(source.cues[i - 1].text.encode("utf-8"))}
        for i in indices
    ])


def audit_typed_speech_row(source: VerifiedSource, atom: dict, legacy_row: dict,
                           row: dict, reviewed_cues: dict[int, str]) -> dict:
    """Prove a non-factual *attributed speech act* is in the actual private SRT.

    An OPINION or HYPOTHETICAL here never means its investment effectiveness
    was independently verified. A conditional hypothesis remains unresolved as
    a strategy recommendation; the question remains a question, not an answer.
    """
    needed = {
        "schema", "claim_id", "atom_sha256", "source_sha256", "source_cue_indices",
        "source_context_sha256", "speech_type", "verbatim_anchor_cue_index",
        "verbatim_anchor", "source_speaker_identity", "chat_meaning_analysis",
        "chat_meaning_analysis_sha256", "conditions_checked", "exceptions_checked",
        "numeric_checked", "counterexample_checked", "speaker_stance_checked",
        "financial_factual_truth_certified", "strategy_effectiveness_verified",
        "individual_investment_advice_approved", "independent_gold_certified",
        "external_source_audio_authenticated", "research_knowledge_export_allowed",
        "source_only_attribution", "disclosure_restriction",
    }
    _ensure(type(row) is dict and set(row) == needed, "ROW_SCHEMA")
    _ensure(row["schema"] == ROW_SCHEMA and row["claim_id"] == atom["claim_id"],
            "SCHEMA_OR_CLAIM")
    cid = atom["claim_id"]
    _ensure(cid in B0001_EXPECTED, "PILOT_SOURCE_REVIEW_REQUIRED")
    expected_kind, expected_type = B0001_EXPECTED[cid]
    _ensure(atom["kind"] == expected_kind and row["speech_type"] == expected_type
            and row["speech_type"] in SPEECH_TYPES, "SEMANTIC_KIND_MISMATCH")
    _ensure(row["source_sha256"] == source.source_sha256 and
            row["atom_sha256"] == json_digest(atom), "SOURCE_OR_ATOM_DRIFT")
    indices = sorted(set(atom["context_cue_indices"]))
    _ensure(indices and row["source_cue_indices"] == indices and
            all(type(i) is int and source.scope_first_cue <= i <= source.scope_last_cue
                for i in indices), "CONTEXT_CUES_NOT_EXACT")
    _ensure(row["source_context_sha256"] == _cue_pin(source, indices) and
            all(reviewed_cues.get(i) == "REVIEWED" for i in indices),
            "SOURCE_UNREVIEWED_OR_TAMPERED")
    idx = row["verbatim_anchor_cue_index"]
    _ensure(type(idx) is int and idx in indices and
            type(row["verbatim_anchor"]) is str and
            5 <= len(row["verbatim_anchor"]) <= 200 and
            row["verbatim_anchor"] in source.cues[idx - 1].text,
            "VERBATIM_ANCHOR_NOT_IN_ORIGINAL")
    # Do not attribute private subtitle speech to a named individual without
    # independent speaker proof. Engine input speaker is UNKNOWN.
    _ensure(atom["speaker"] == "UNKNOWN" and
            row["source_speaker_identity"] == "UNKNOWN_NOT_AUDIO_AUTHENTICATED",
            "SPEAKER_IDENTITY_UNPROVEN")
    _ensure(legacy_row["claim_id"] == cid and
            legacy_row["atom_sha256"] == json_digest(atom) and
            legacy_row["status"] == "OPEN" and legacy_row["financial_claim"] is True and
            legacy_row["high_risk"] is True and
            legacy_row["finance_evidence_status"] == "OPEN",
            "DO_NOT_RECLASSIFY_NATIVE_FACT_OR_ACCEPTED_ATOM")
    for k in ("conditions_checked", "exceptions_checked", "numeric_checked",
              "counterexample_checked", "speaker_stance_checked"):
        _ensure(row[k] is True, "UNREVIEWED_" + k.upper())
    for k in ("financial_factual_truth_certified", "strategy_effectiveness_verified",
              "individual_investment_advice_approved", "independent_gold_certified",
              "external_source_audio_authenticated", "research_knowledge_export_allowed"):
        _ensure(row[k] is False, "FALSE_FACT_OR_ADVICE_CERTIFICATE_" + k.upper())
    _ensure(row["source_only_attribution"] is True and
            row["disclosure_restriction"] ==
            "ORIGINAL_VIDEO_SPEECH_ONLY_NOT_FINANCIAL_TRUTH_OR_ADVICE",
            "MUST_RESTRICT_SOURCE_ONLY")
    note = row["chat_meaning_analysis"]
    _ensure(type(note) is str and len(note) >= 45 and
            row["chat_meaning_analysis_sha256"] == sha256(note.encode("utf-8")),
            "CHAT_MEANING_TEXT_NOT_BYTES_PINNED")
    # Strictly preserve the original numeric/conditional content rather than
    # inventing a financial statistic, guarantee or personal suitability.
    _ensure(row["speech_type"] not in {
        "RISK_QUESTION_ONLY", "INVESTMENT_CONVICTION_QUESTION_ONLY"
    } or ("질문" in note and "답변" in note), "QUESTION_NOT_DISTINGUISHED_FROM_ANSWER")
    _ensure(row["speech_type"] != "CONDITIONAL_PAYOFF_HYPOTHESIS_ONLY" or
            ("조건" in note and "보장" in note), "HYPOTHESIS_WITHOUT_RISK_LIMIT")
    _ensure(row["speech_type"] != "BOOK_TO_INVESTMENT_META_PROPOSAL_ONLY" or
            ("제안" in note and "적합" in note), "PROPOSAL_WITHOUT_SUITABILITY_LIMIT")
    return {
        "claim_id": cid, "source_context_sha256": row["source_context_sha256"],
        "speech_type": row["speech_type"], "source_speech_act_attested": True,
        "financial_fact_verified": False, "investment_recommendation_approved": False,
        "research_knowledge_export_allowed": False,
    }


def assess_typed_chat_final_v164(source: VerifiedSource, exchange: dict, *,
                                 host_receipt: dict, store,
                                 legacy_chat_review: dict,
                                 official_evidence_bodies: dict[str, bytes],
                                 typed_rows: list[dict],
                                 risk_reconciliation: dict | None = None,
                                 disagreement_resolution: dict | None = None) -> dict:
    """Run actual untouched native V123, then assess typed semantic exceptions.

    A precheck is NOT a replacement V123 export gate; typed full PASS remains
    impossible with three unverified historical facts or 12 high-risk omissions.
    """
    _ensure(isinstance(source, VerifiedSource), "VERIFIED_OWNER_SOURCE_REQUIRED")
    atomic = audit_host_atomic_exchange(source, exchange)
    native = assess_chat_final_gate(
        source, exchange, host_receipt=host_receipt,
        chat_review=legacy_chat_review, store=store,
        official_evidence_bodies=official_evidence_bodies,
    )
    _ensure(type(typed_rows) is list, "TYPED_ROWS_REQUIRED")
    _ensure(source.scope_first_cue == 1 and source.scope_last_cue == 120
            and len(exchange["atoms"]) == 16, "PILOT_SCOPE_MUST_BE_EXACT_B0001")
    atoms = {a["claim_id"]: a for a in exchange["atoms"]}
    original = {r["claim_id"]: r for r in legacy_chat_review["atom_verdicts"]}
    _ensure(set(atoms) == set(original), "ORIGINAL_V123_ATOM_CENSUS")
    cue_reviewed = {r["cue_index"]: r["status"] for r in legacy_chat_review["source_cues"]}
    seen = set()
    proof_rows = []
    for row in typed_rows:
        _ensure(type(row) is dict and row.get("claim_id") in atoms,
                "UNKNOWN_TYPED_CLAIM")
        cid = row["claim_id"]
        _ensure(cid not in seen, "DUPLICATE_TYPED_CLAIM")
        seen.add(cid)
        proof_rows.append(audit_typed_speech_row(
            source, atoms[cid], original[cid], row, cue_reviewed))
    _ensure(seen == set(B0001_EXPECTED), "REQUIRED_FIVE_SPEECH_ACTS_MISSING")
    factual_pending = sorted(cid for cid, r in original.items()
                             if r["status"] == "OPEN" and cid not in seen)
    external_required = {"C00002", "C00009", "C00010"}
    _ensure(set(factual_pending).issubset(external_required),
            "UNEXPECTED_EXTERNAL_OPEN_CANNOT_DISAPPEAR")
    _ensure(all(original[cid]["status"] == "ACCEPT_FOR_RESEARCH"
                for cid in external_required - set(factual_pending)),
            "EXTERNAL_FACT_NOT_ACTUALLY_NATIVE_V123_ACCEPTED")
    _ensure(native["status"] == "CHAT_FINAL_HOLD_OPEN" and
            native["atoms_accepted"] == 10 - len(factual_pending) and
            native["atoms_open"] == 5 + len(factual_pending) and
            native["finance_open"] >= 5 and
            not native["research_candidate_export_allowed"],
            "NATIVE_V123_MUST_REMAIN_HOLD_AND_COUNTS_EXACT")
    # A typed source review is not a risk-resolution gold dataset. Never
    # silently zero these controls; disagreement flag stays as originally set.
    omissions = legacy_chat_review["unresolved_high_risk_omissions"]
    disputes_resolved = legacy_chat_review["disagreements_adjudicated"]
    _ensure(type(omissions) is int and omissions >= 0 and
            type(disputes_resolved) is bool, "ORIGINAL_QUALITY_FLAGS_REQUIRED")
    # A self-authored zero in the old count is insufficient: the 12 originally
    # unresolved risk-review cases need auditable, source-anchored case notes.
    reconciled_cases = False
    if risk_reconciliation is not None:
        _ensure(type(risk_reconciliation) is dict and
                set(risk_reconciliation) == {
                   "schema", "source_sha256", "baseline_unresolved_count",
                   "cases", "all_original_risks_reconciled", "independent_gold_certified",
                } and
                risk_reconciliation["schema"] == "IRE_V164_RISK_12_SOURCE_RECONCILIATION_V1" and
                risk_reconciliation["source_sha256"] == source.source_sha256 and
                risk_reconciliation["baseline_unresolved_count"] == 12 and
                risk_reconciliation["independent_gold_certified"] is False and
                type(risk_reconciliation["cases"]) is list and
                len(risk_reconciliation["cases"]) == 12,
                "RISK_CASE_LEDGER_STRUCTURE_OR_CENSUS")
        checked = set()
        for rr in risk_reconciliation["cases"]:
            _ensure(type(rr) is dict and set(rr) == {
                "risk_case_id", "cue_index", "cue_text_sha256",
                "chat_reconciliation_note", "chat_reconciliation_note_sha256",
                "source_context_risk_checked", "harmful_finance_claim_not_factually_certified",
            }, "RISK_CASE_ROW_STRUCTURE")
            idx = rr["cue_index"]
            _ensure(type(idx) is int and source.scope_first_cue <= idx <= source.scope_last_cue and
                    type(rr["risk_case_id"]) is str and len(rr["risk_case_id"]) >= 4 and
                    rr["risk_case_id"] not in checked and
                    rr["cue_text_sha256"] == sha256(source.cues[idx - 1].text.encode("utf-8")) and
                    type(rr["chat_reconciliation_note"]) is str and
                    len(rr["chat_reconciliation_note"]) >= 40 and
                    rr["chat_reconciliation_note_sha256"] == sha256(
                      rr["chat_reconciliation_note"].encode("utf-8")) and
                    rr["source_context_risk_checked"] is True and
                    rr["harmful_finance_claim_not_factually_certified"] is True,
                    "RISK_CASE_NOT_SOURCE_VERIFIED")
            checked.add(rr["risk_case_id"])
        reconciled_cases = (risk_reconciliation["all_original_risks_reconciled"] is True and
                            omissions == 0)
    conflicts_resolved_with_ledger = False
    if disagreement_resolution is not None:
        _ensure(type(disagreement_resolution) is dict and
                set(disagreement_resolution) == {
                  "schema", "source_sha256", "chat_review_note", "chat_review_note_sha256",
                  "all_conflicts_resolved", "not_external_independent_gold",
                } and disagreement_resolution["schema"] ==
                "IRE_V164_CONFLICT_RESOLUTION_SOURCE_REVIEW_V1" and
                disagreement_resolution["source_sha256"] == source.source_sha256 and
                type(disagreement_resolution["chat_review_note"]) is str and
                len(disagreement_resolution["chat_review_note"]) >= 40 and
                disagreement_resolution["chat_review_note_sha256"] == sha256(
                    disagreement_resolution["chat_review_note"].encode("utf-8")) and
                disagreement_resolution["not_external_independent_gold"] is True,
                "CONFLICT_RESOLUTION_NOT_SOURCE_PINNED")
        conflicts_resolved_with_ledger = (
            disagreement_resolution["all_conflicts_resolved"] is True and
            disputes_resolved is True)
    typed_scope_ready = (
        not factual_pending and omissions == 0 and reconciled_cases and
        disputes_resolved and conflicts_resolved_with_ledger and
        legacy_chat_review["source_first_pass_completed"] is True and
        legacy_chat_review["counterexample_pass_completed"] is True and
        native["cues_reviewed"] == 120 and
        native.get("atoms_excluded") == 1 and
        native["atoms_accepted"] == 10 and native["atoms_open"] == 5 and
        all(cue_reviewed.get(i) == "REVIEWED" for i in range(1,121))
    )
    return {
        "schema": RECEIPT_SCHEMA,
        "source_sha256": source.source_sha256,
        "manifest_sha256": source.manifest_sha256,
        "host_event_sha256": host_receipt["event_sha256"],
        "owner_120_cues_reviewed": native["cues_reviewed"],
        "owner_16_atoms_verified": len(atoms),
        "native_v123_status_unchanged": native["status"],
        "native_v123_accepted_research_candidates": native["atoms_accepted"],
        "source_speech_act_only_typed_reviewed": len(proof_rows),
        "source_speech_act_only_claim_ids": sorted(seen),
        "objective_historical_claims_unverified": factual_pending,
        "native_v123_open_unchanged": native["atoms_open"],
        "native_v123_finance_open_unchanged": native["finance_open"],
        "native_v123_excluded": native.get("atoms_excluded", 0),
        "unresolved_high_risk_omissions": omissions,
        "disagreements_adjudicated": disputes_resolved,
        "risk_12_case_source_reconciliation_complete": reconciled_cases,
        "conflicts_source_reconciled": conflicts_resolved_with_ledger,
        "typed_full_scope_semantic_pass": typed_scope_ready,
        "typed_final_knowledge_release_authorized": False,
        "v128_parent_publication_authorized": False,
        "personalized_investment_advice_approved": False,
        "independent_gold_accuracy_certified": False,
        "source_only_claims_proof_sha256": json_digest(proof_rows),
        "typed_review_digest_sha256": json_digest(typed_rows),
        "p0e_go": False,
        "status": ("V164_B0001_TYPED_NONPERSONAL_RESEARCH_CUSTODY_READY_V128_STILL_BLOCKED"
                   if typed_scope_ready else
                   "V164_B0001_5_SOURCE_SPEECH_ATTESTED_EXTERNAL_OR_RISK_HOLD"),
    }
