"""V123 final ChatGPT review gate for NEW V6 research candidate release.

Untrusted engine CI, structural host-batch events, same-model internal scores,
and bare SHA assertions cannot authorize a new research claim. A chat review
has to cover the complete owner-pinned scope and every source-backed atom.

PASS below means ONLY "ChatGPT reviewed, eligible for non-personal research
candidate indexing". It NEVER certifies legal truth, human-independent
precision/recall, Master/P4 merge, P0 GO or personalized investment advice.

This module does not invoke an LLM. Review rows are prepared by ChatGPT in the
conversation and held privately. Public receipts carry only metadata/digests.
"""
from __future__ import annotations

from datetime import date
import re

from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.claim_census import FINANCIAL
from ire.v6.codec import json_digest, require_hash, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.source import VerifiedSource

SCHEMA = "IRE_V6_CHAT_FINAL_REVIEW_V123"
RECEIPT_SCHEMA = "IRE_V6_CHAT_FINAL_GATE_RECEIPT_V123"
REVIEW_STATUSES = {"ACCEPT_FOR_RESEARCH", "REJECT", "OPEN"}
FINANCE_STATUSES = {"NOT_APPLICABLE", "PRIMARY_BODY_AND_DATE_CHAT_CHECKED", "OPEN"}
CUE_STATUSES = {"REVIEWED", "OPEN"}
BLINDNESS = {"PRIOR_EXPOSED", "BLIND_NOT_ESTABLISHED", "SOURCE_FIRST_WITH_LOCKED_PREDICTION"}


def _check(ok: bool, name: str) -> None:
    if not ok:
        raise InvalidInput("V123_" + name)


def _pin(v, name):
    return require_hash(v, "V123_" + name)


def _date(v, name):
    _check(type(v) is str, name)
    try:
        d = date.fromisoformat(v)
    except ValueError as e:
        raise InvalidInput("V123_" + name) from e
    _check(d.isoformat() == v, name)
    return d


def _is_finance(atom, source):
    # Conservative lexical floor. ChatGPT can additionally flag a claim as
    # finance-sensitive; it may not downgrade this automatic minimum.
    indices = set(atom["context_cue_indices"])
    text = atom["proposition"] + " " + " ".join(source.cues[i-1].text for i in sorted(indices))
    return bool(FINANCIAL.search(text))


def _stage_receipt(source, atom_audit, host, store):
    if host is None:
        return False
    _check(type(host) is dict and host.get("schema") == "IRE_V6_HOST_BATCH_RECEIPT_V1", "HOST_RECEIPT_SCHEMA")
    _check(host.get("atomic_batch_committed") is True and host.get("is_current") is True,
           "HOST_BATCH_NOT_COMMITTED_OR_CURRENT")
    _check(host.get("research_complete") is False and host.get("p0_go") is False and
           host.get("semantic_truth_certified") is False and
           host.get("human_semantic_review_pending") is True, "HOST_FALSE_QUALITY_APPROVAL")
    frontier = host.get("source_first_semantic_frontier_pin")
    risk = host.get("source_semantic_risk_pin")
    _check(type(frontier) is dict and type(risk) is dict and
           frontier.get("original_source_sha256") == source.source_sha256 and
           risk.get("original_source_sha256") == source.source_sha256 and
           frontier.get("manifest_sha256") == source.manifest_sha256 and
           risk.get("manifest_sha256") == source.manifest_sha256,
           "HOST_SCOPE_OR_SOURCE_DRIFT")
    _pin(host.get("bundle_sha256"), "HOST_BUNDLE")
    _pin(host.get("event_sha256"), "HOST_EVENT")
    _check(type(host.get("scope_id")) is str and bool(host["scope_id"]), "HOST_SCOPE")
    if store is None:
        return False
    _check(callable(getattr(store, "snapshot", None)), "HOST_STORE_SNAPSHOT_REQUIRED")
    snap = store.snapshot(host["scope_id"])
    _check(type(snap) is dict and
           snap.get("ledger_head_sha256") == host["event_sha256"] and
           type(snap.get("progress")) is dict and
           snap["progress"].get("model_windows_recorded") ==
               host.get("source_and_proof_model_windows") and
           snap["progress"].get("current_revision_structural_proof_records") ==
               host.get("source_and_proof_model_windows"),
           "HOST_STORE_STALE_OR_PROOF_NOT_COMMITTED")
    _check(frontier.get("review_case_count", -1) >= 0 and
           frontier.get("review_case_census_sha256") is not None and
           type(frontier.get("review_case_count")) is int, "HOST_FRONTIER_UNVERIFIED")
    _pin(frontier["review_case_census_sha256"], "HOST_FRONTIER")
    return True


def assess_chat_final_gate(source: VerifiedSource, exchange: dict, *,
                           host_receipt: dict | None, chat_review: dict | None,
                           store=None, official_evidence_bodies=None) -> dict:
    """Replay real V6 atomic source audit; return safe HOLD or research-only PASS.

    The verifier structurally replays supplied evidence; it cannot establish
    that ChatGPT's semantic judgments or a source-body SHA are factually true.
    """
    _check(isinstance(source, VerifiedSource), "OWNER_VERIFIED_SOURCE_REQUIRED")
    atomic = audit_host_atomic_exchange(source, exchange)
    _check(atomic["every_cue_has_explicit_disposition"] is True, "ATOMIC_CUE_GAP")
    if not _stage_receipt(source, atomic, host_receipt, store):
        return _result(source, atomic, status="HOLD_MISSING_V6_HOST_BATCH_OR_STORE", reviewed=0,
                       accepted=0, rejected=0, opened=len(exchange["atoms"]),
                       missing_cues=source.scope_last_cue-source.scope_first_cue+1,
                       finance_open=0, risk_open=0, digest=None)
    if chat_review is None:
        return _result(source, atomic, status="HOLD_MISSING_CHAT_FINAL_REVIEW", reviewed=0,
                       accepted=0, rejected=0, opened=len(exchange["atoms"]),
                       missing_cues=source.scope_last_cue-source.scope_first_cue+1,
                       finance_open=0, risk_open=0, digest=None)
    _check(type(chat_review) is dict and set(chat_review) == {
        "schema", "review_executor", "as_of", "source_sha256", "manifest_sha256",
        "host_event_sha256", "host_bundle_sha256", "atom_candidate_digest",
        "cue_disposition_digest", "blindness", "source_first_pass_completed",
        "counterexample_pass_completed", "disagreements_adjudicated",
        "source_cues", "atom_verdicts", "unresolved_high_risk_omissions",
        "unresolved_audio_visual", "external_independent_certified",
        "personalized_advice_approved", "p0_go", "review_private_evidence_sha256",
    }, "CHAT_REVIEW_SCHEMA")
    _check(chat_review["schema"] == SCHEMA and
           chat_review["review_executor"] == "CHATGPT_IN_CHAT" and
           chat_review["source_sha256"] == source.source_sha256 and
           chat_review["manifest_sha256"] == source.manifest_sha256 and
           chat_review["host_event_sha256"] == host_receipt["event_sha256"] and
           chat_review["host_bundle_sha256"] == host_receipt["bundle_sha256"] and
           chat_review["atom_candidate_digest"] == atomic["atom_candidate_digest"] and
           chat_review["cue_disposition_digest"] == atomic["cue_disposition_digest"],
           "CHAT_REVIEW_WRONG_FROZEN_SOURCE_OR_HOST")
    _date(chat_review["as_of"], "REVIEW_DATE")
    _pin(chat_review["review_private_evidence_sha256"], "REVIEW_PRIVATE_EVIDENCE")
    _check(chat_review["blindness"] in BLINDNESS and
           all(chat_review[k] is False for k in
               ("external_independent_certified", "personalized_advice_approved", "p0_go")),
           "FALSE_INDEPENDENT_OR_PERSONAL_APPROVAL")
    _check(all(type(chat_review[k]) is bool for k in
               ("source_first_pass_completed", "counterexample_pass_completed",
                "disagreements_adjudicated")), "CHAT_PASS_FLAGS_INVALID")
    hrf = chat_review["unresolved_high_risk_omissions"]
    av = chat_review["unresolved_audio_visual"]
    _check(type(hrf) is int and 0 <= hrf <= 100000 and
           type(av) is int and 0 <= av <= 100000, "OPEN_COUNTS_INVALID")

    # Verify actual owner-private primary-source bodies, not just source SHA
    # strings. A missing body is an OPEN, never a self-certified finance PASS.
    if official_evidence_bodies is None:
        official_evidence_bodies = {}
    _check(type(official_evidence_bodies) is dict and
           all(type(k) is str and type(v) is bytes and 0 < len(v) <= 8*1024*1024
               for k,v in official_evidence_bodies.items()), "OFFICIAL_BODY_BYTES_INPUT")
    cues = chat_review["source_cues"]
    _check(type(cues) is list and len(cues) == source.scope_last_cue-source.scope_first_cue+1,
           "CHAT_CUE_CENSUS")
    missing_cues = 0
    for i, row in enumerate(cues, source.scope_first_cue):
        _check(type(row) is dict and set(row) == {
            "cue_index", "cue_text_sha256", "status", "review_note_sha256"
        } and type(row["cue_index"]) is int and row["cue_index"] == i and
            row["cue_text_sha256"] == sha256(source.cues[i-1].text.encode("utf-8")) and
            row["status"] in CUE_STATUSES, "CHAT_CUE_SOURCE_OR_ORDER_DRIFT")
        _pin(row["review_note_sha256"], "CUE_REVIEW_NOTE")
        missing_cues += int(row["status"] == "OPEN")

    atoms = {a["claim_id"]:a for a in exchange["atoms"]}
    rows = chat_review["atom_verdicts"]
    _check(type(rows) is list and len(rows) == len(atoms), "CHAT_ATOM_CENSUS")
    seen = set()
    accepted = rejected = opened = finance_open = risk_open = 0
    _check(set(official_evidence_bodies).issubset(atoms), "OFFICIAL_BODY_UNKNOWN_CLAIM")
    for row in rows:
        _check(type(row) is dict and set(row) == {
            "claim_id", "atom_sha256", "status", "speaker_stance_checked",
            "conditions_exceptions_checked", "numeric_period_checked",
            "counterexample_checked", "high_risk", "financial_claim",
            "finance_evidence_status", "official_body_sha256",
            "official_effective_as_of", "financial_scope_checked",
            "private_review_note_sha256",
        }, "CHAT_ATOM_ROW_SCHEMA")
        cid = row["claim_id"]
        _check(type(cid) is str and cid in atoms and cid not in seen and
               row["atom_sha256"] == json_digest(atoms[cid]), "CHAT_ATOM_SOURCE_OR_DUPLICATE")
        seen.add(cid)
        _pin(row["private_review_note_sha256"], "ATOM_REVIEW_NOTE")
        _check(row["status"] in REVIEW_STATUSES and
               all(type(row[k]) is bool for k in (
                   "speaker_stance_checked", "conditions_exceptions_checked",
                   "numeric_period_checked", "counterexample_checked",
                   "high_risk", "financial_claim", "financial_scope_checked")),
               "CHAT_ATOM_STATUS_OR_BOOL")
        _check(row["finance_evidence_status"] in FINANCE_STATUSES,
               "CHAT_FINANCE_STATUS")
        _check(not _is_finance(atoms[cid], source) or row["financial_claim"],
               "FINANCE_CLASSIFICATION_DOWNGRADE")
        if row["financial_claim"]:
            _check(row["finance_evidence_status"] != "NOT_APPLICABLE", "FINANCE_NOT_APPLICABLE")
        else:
            _check(row["finance_evidence_status"] == "NOT_APPLICABLE", "NONFINANCE_STATUS")
        body_replayed = False
        if row["finance_evidence_status"] == "PRIMARY_BODY_AND_DATE_CHAT_CHECKED":
            _pin(row["official_body_sha256"], "OFFICIAL_BODY")
            original_body = official_evidence_bodies.get(cid)
            if original_body is not None:
                _check(sha256(original_body) == row["official_body_sha256"],
                       "OFFICIAL_BODY_BYTES_MISMATCH")
                body_replayed = True
            _check(_date(row["official_effective_as_of"], "OFFICIAL_EFFECTIVE_DATE")
                   <= _date(chat_review["as_of"], "REVIEW_ASOF"),
                   "FUTURE_EFFECTIVE_LAW")
            _check(row["financial_scope_checked"], "FINANCE_SCOPE_NOT_CHECKED")
        else:
            _check(row["official_body_sha256"] is None and
                   row["official_effective_as_of"] is None and
                   row["financial_scope_checked"] is False,
                   "FINANCE_EVIDENCE_FAKED_OR_INCONSISTENT")
        accepted += int(row["status"] == "ACCEPT_FOR_RESEARCH")
        rejected += int(row["status"] == "REJECT")
        opened += int(row["status"] == "OPEN")
        finance_open += int(row["financial_claim"] and
                            (row["finance_evidence_status"] != "PRIMARY_BODY_AND_DATE_CHAT_CHECKED"
                             or not body_replayed))
        risk_open += int(row["high_risk"] and (
            row["status"] != "ACCEPT_FOR_RESEARCH" or
            row["financial_claim"] and
            (row["finance_evidence_status"] != "PRIMARY_BODY_AND_DATE_CHAT_CHECKED"
             or not body_replayed)))
        if row["status"] == "ACCEPT_FOR_RESEARCH":
            _check(all(row[k] for k in ("speaker_stance_checked", "conditions_exceptions_checked",
                                         "numeric_period_checked", "counterexample_checked")),
                   "UNVERIFIED_SEMANTIC_ACCEPTANCE")
    _check(seen == set(atoms), "CHAT_ATOM_MISSING")
    all_pass = (accepted == len(atoms) and not rejected and not opened and
                not missing_cues and not finance_open and not risk_open and
                not hrf and not av and
                chat_review["source_first_pass_completed"] and
                chat_review["counterexample_pass_completed"] and
                chat_review["disagreements_adjudicated"] and
                not atomic["unresolved_cues"] and not atomic["suspicious_no_atom_cues"])
    final_status = ("CHAT_FINAL_REJECTED" if rejected else
                    "CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY" if all_pass else
                    "CHAT_FINAL_HOLD_OPEN")
    return _result(source, atomic,
                   status=final_status,
                   reviewed=len(cues)-missing_cues, accepted=accepted, rejected=rejected,
                   opened=opened, missing_cues=missing_cues, finance_open=finance_open,
                   risk_open=risk_open+hrf, digest=json_digest(chat_review))


def _result(source, atomic, *, status, reviewed, accepted, rejected, opened,
            missing_cues, finance_open, risk_open, digest):
    return {
        "schema": RECEIPT_SCHEMA,
        "status": status,
        "source_sha256": source.source_sha256,
        "manifest_sha256": source.manifest_sha256,
        "original_scope_cues": atomic["original_scoped_cues_enumerated"],
        "atom_candidate_digest": atomic["atom_candidate_digest"],
        "chat_final_review_digest_sha256": digest,
        "cues_reviewed": reviewed,
        "cues_open": missing_cues,
        "atoms_accepted": accepted,
        "atoms_rejected": rejected,
        "atoms_open": opened,
        "finance_open": finance_open,
        "high_risk_open": risk_open,
        "research_candidate_export_allowed": status == "CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY",
        "formal_financial_fact_approved": 0,
        "master_p4_knowledge_auto_merged": False,
        "personalized_advice_approved": False,
        "external_independent_gold": False,
        "research_complete_791": False,
        "p0_go": False,
    }


def require_chat_final_release(source, exchange, *, host_receipt, chat_review, store, official_evidence_bodies) -> dict:
    """Fail-closed ONLY supported new V6 candidate-export entrypoint.

    A V6 host batch PASS without an explicit ChatGPT final review MUST NOT
    be used to export newly discovered research candidates.
    """
    decision = assess_chat_final_gate(source, exchange,
                                      host_receipt=host_receipt, chat_review=chat_review, store=store,
                                      official_evidence_bodies=official_evidence_bodies)
    if not decision["research_candidate_export_allowed"]:
        raise QualityNotProven("V123_CHAT_FINAL_REVIEW_REQUIRED_BEFORE_RESEARCH_EXPORT")
    return decision
