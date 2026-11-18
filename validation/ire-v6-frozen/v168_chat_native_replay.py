"""V168: complete V167 in-chat proposal -> *native* frozen V123 review replay.

Only a chat-host supplied, explicit secondary native review may change an OPEN
atom. A V167 research *candidate* is not a V123 or E4 approval. All original
source+scope references, old review digests, risk counters and dispute state are
kept; negative and inconclusive proposals remain unreleased.

This module DOES NOT invoke an LLM. When a host cannot supply a new secondary
ChatGPT review, all affected native rows remain OPEN, and the real V123 gate is
replayed as HOLD. E4 is a separate independent authority, never inferred here.
"""
from __future__ import annotations
import copy
from datetime import date
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import VerifiedSource
from v123_chat_final_gate import assess_chat_final_gate
from v167_chat_research_loop import SCHEMA as DOCKET_SCHEMA, PROPOSAL_SCHEMA

SCHEMA = "IRE_V168_CHAT_PROPOSALS_TO_FROZEN_NATIVE_V123_V1"
NATIVE_FIELDS = {
    "claim_id", "atom_sha256", "status", "speaker_stance_checked",
    "conditions_exceptions_checked", "numeric_period_checked",
    "counterexample_checked", "high_risk", "financial_claim",
    "finance_evidence_status", "official_body_sha256",
    "official_effective_as_of", "financial_scope_checked",
    "private_review_note_sha256",
}
ROUTES = {
    "KEEP_OPEN": "OPEN",
    "CANDIDATE_NEEDS_NATIVE_REVIEW": "ACCEPT_FOR_RESEARCH",
    "REJECT_PROPOSAL": "REJECT",
    # Explicit typed source-only attestation is still required by V166.
    "QUARANTINE_PROPOSAL": "OPEN",
}


def _need(cond, code):
    if not cond:
        raise InvalidInput("V168_CHAT_NATIVE_" + code)


def _digest(obj):
    return json_digest(obj)


def _review_note(item, claim, proposal, decision):
    """Digest the *actual* host-authored secondary note, never a fake SHA."""
    _need(type(item) is dict and set(item) == {
        "claim_id", "atom_sha256", "proposal_decision_sha256",
        "source_sha256", "prior_review_sha256", "chat_review_note",
        "conditions_checked", "exceptions_checked", "numbers_checked",
        "counterarguments_checked", "speaker_stance_checked",
        "not_personal_advice", "not_legal_certification",
        "native_row",
    }, "SECONDARY_CHAT_SCHEMA")
    _need(item["claim_id"] == claim["claim_id"] and
          item["atom_sha256"] == claim["atom_sha256"] and
          item["proposal_decision_sha256"] == proposal["chat_decision_sha256"] and
          item["source_sha256"] == decision["owner_source_sha256"] and
          item["prior_review_sha256"] == claim["prior_review_sha256"],
          "SECONDARY_SOURCE_OR_REVIEW_PIN")
    _need(all(item[k] is True for k in (
        "conditions_checked", "exceptions_checked", "numbers_checked",
        "counterarguments_checked", "speaker_stance_checked",
        "not_personal_advice", "not_legal_certification")),
          "SECONDARY_MEANING_REVIEW_REQUIRED")
    note = item["chat_review_note"]
    _need(type(note) is str and len(note.strip()) >= 60,
          "SECONDARY_REASON_REQUIRED")
    return sha256(note.encode("utf-8"))


def compile_and_replay_native(docket, proposals, *, cases_by_segment,
                              secondary_chat_reviews=None):
    """Reconcile *all* native children and replay V123 without releasing any.

    cases_by_segment is a live-native case map containing VerifiedSource,
    exchange, chat_review, host_receipt, source_store and original evidence.
    The original review/case objects are never mutated. A secondary review
    must be supplied to enact a CANDIDATE or REJECT; mere proposal is not
    enough. QUARANTINE proposals stay OPEN until the V166 typed compiler.

    The native gate executes once per supplied segment; no V128 writes.
    Approval authority is explicitly *not* forwarded from V123 to E4/E5.
    """
    _need(type(docket) is dict and docket.get("schema") == DOCKET_SCHEMA and
          docket.get("docket_sha256") == _digest({k:v for k,v in docket.items()
                                                  if k != "docket_sha256"}),
          "DOCKET_TAMPER_OR_SCHEMA")
    _need(type(proposals) is dict and proposals.get("schema") == PROPOSAL_SCHEMA and
          proposals.get("proposal_receipt_sha256") == _digest({
              k:v for k,v in proposals.items() if k != "proposal_receipt_sha256"}),
          "PROPOSAL_RECEIPT_TAMPER")
    _need(proposals.get("owner_source_sha256") == docket["owner_source_sha256"]
          and proposals.get("docket_sha256") == docket["docket_sha256"]
          and proposals.get("original_open_count") == docket["original_open_count"]
          and proposals.get("proposals_created") == len(proposals.get("proposals", []))
          and proposals.get("unprocessed_open_count") ==
              docket["original_open_count"] - proposals["proposals_created"]
          and proposals.get("e5_authorized") is False
          and proposals.get("knowledge_publication_authorized") is False,
          "RESEARCH_PROPOSALS_NOT_UNRELEASED")
    _need(type(cases_by_segment) is dict and len(cases_by_segment) ==
          docket["original_segment_count"] and
          type(secondary_chat_reviews) in (type(None), dict),
          "ALL_NATIVE_CASES_REQUIRED")
    secondary_chat_reviews = secondary_chat_reviews or {}
    _need(type(docket.get("items")) is list and len(docket["items"]) ==
          docket["original_open_count"] and
          len({r["claim_id"] for r in docket["items"]}) == len(docket["items"]),
          "DOCKET_CENSUS")
    tasks = {r["claim_id"]:r for r in docket["items"]}
    all_proposals = proposals["proposals"]
    _need(type(all_proposals) is list and len({r["claim_id"] for r in all_proposals}) ==
          len(all_proposals) and {r["claim_id"] for r in all_proposals} <= set(tasks),
          "DUPLICATE_OR_UNKNOWN_PROPOSAL")
    selected = {}
    for p in all_proposals:
        task = tasks[p["claim_id"]]
        _need(p["segment_id"] == task["segment_id"] and
              p["atom_sha256"] == task["atom_sha256"] and
              p["prior_status"] == "OPEN" and
              p["prior_review_sha256"] == task["prior_review_sha256"] and
              p["proposed_decision"] in ROUTES and
              p["applied_to_native_v123"] is False and
              p["approved_by_e4"] is False and
              p["knowledge_released"] is False,
              "PROPOSAL_NOT_SOURCE_PINNED_OR_RELEASED")
        selected[p["claim_id"]] = p
    _need(set(secondary_chat_reviews).issubset(selected),
          "SECONDARY_REVIEW_UNKNOWN_PROPOSAL")

    native_results, compiled, updated, pending = [], {}, [], []
    touched = set()
    for sid, case in sorted(cases_by_segment.items()):
        _need(type(case) is dict and {
            "source", "exchange", "chat_review", "host_receipt",
            "source_store", "official_evidence_bodies"} <= set(case),
              "NATIVE_CASE_INCOMPLETE")
        source, exchange, review = case["source"], case["exchange"], case["chat_review"]
        _need(isinstance(source, VerifiedSource) and
              source.source_sha256 == docket["owner_source_sha256"] and
              type(exchange) is dict and type(review) is dict and
              review["source_sha256"] == source.source_sha256 and
              review["manifest_sha256"] == source.manifest_sha256 and
              case["host_receipt"]["event_sha256"] == review["host_event_sha256"] and
              case["host_receipt"]["bundle_sha256"] == review["host_bundle_sha256"] and
              case["official_evidence_bodies"] is not None,
              "NATIVE_SOURCE_OR_HOST_MISMATCH")
        atoms = {a["claim_id"]:a for a in exchange["atoms"]}
        existing = {v["claim_id"]:v for v in review["atom_verdicts"]}
        _need(len(atoms) == len(exchange["atoms"]) == len(existing) ==
              len(review["atom_verdicts"]) and set(atoms) == set(existing),
              "NATIVE_CLAIM_CENSUS")
        draft = copy.deepcopy(review)
        by_id = {r["claim_id"]:r for r in draft["atom_verdicts"]}
        sid_tasks = [t for t in docket["items"] if t["segment_id"] == sid]
        for task in sid_tasks:
            cid = task["claim_id"]
            _need(cid in atoms and cid in existing and existing[cid]["status"] == "OPEN" and
                  task["atom_sha256"] == _digest(atoms[cid]) and
                  task["prior_review_sha256"] == _digest(review) and
                  task["high_risk"] is existing[cid]["high_risk"] and
                  task["source_refs"] == atoms[cid]["source_refs"] and
                  task["condition_cue_indices"] == atoms[cid]["condition_cue_indices"] and
                  task["exception_cue_indices"] == atoms[cid]["exception_cue_indices"] and
                  task["numeric_references"] == atoms[cid]["numeric_references"] and
                  task["source_context"] == [{"cue_index": i,
                    "text": source.cues[i-1].text} for i in atoms[cid]["context_cue_indices"]],
                  "NATIVE_OPEN_ATOM_OR_CONTEXT_DRIFT")
            touched.add(cid)
            p = selected.get(cid)
            if p is None or p["proposed_decision"] in ("KEEP_OPEN", "QUARANTINE_PROPOSAL"):
                if p is not None and p["proposed_decision"] == "QUARANTINE_PROPOSAL":
                    pending.append({"claim_id":cid,"reason":"TYPED_V166_QUARANTINE_COMPILER_REQUIRED"})
                continue
            _need(cid in secondary_chat_reviews, "SECONDARY_CHAT_REQUIRED_FOR_CHANGE")
            secondary = secondary_chat_reviews[cid]
            note_hash = _review_note(secondary, task, p, docket)
            row = secondary["native_row"]
            _need(type(row) is dict and set(row) == NATIVE_FIELDS and
                  row["claim_id"] == cid and row["atom_sha256"] == _digest(atoms[cid]) and
                  row["status"] == ROUTES[p["proposed_decision"]] and
                  row["high_risk"] is existing[cid]["high_risk"] and
                  row["financial_claim"] is existing[cid]["financial_claim"] and
                  row["private_review_note_sha256"] == note_hash and
                  all(row[k] is True for k in ("speaker_stance_checked",
                    "conditions_exceptions_checked", "numeric_period_checked", "counterexample_checked")),
                  "SECONDARY_NATIVE_ROW_UNTRUSTED")
            if row["status"] == "ACCEPT_FOR_RESEARCH":
                # The V123 gate additionally verifies these bytes against
                # the frozen source. E4 must independently refetch origin.
                _need(type(p["source_evidence"]) is list and p["source_evidence"],
                      "CANDIDATE_SOURCE_MISSING")
                if row["financial_claim"]:
                    body = case["official_evidence_bodies"].get(cid)
                    _need(type(body) is bytes and
                          row["finance_evidence_status"] == "PRIMARY_BODY_AND_DATE_CHAT_CHECKED" and
                          row["official_body_sha256"] == sha256(body) and
                          row["official_body_sha256"] in {
                              e["body_sha256"] for e in p["source_evidence"]} and
                          type(row["official_effective_as_of"]) is str and
                          date.fromisoformat(row["official_effective_as_of"]) <=
                              date.fromisoformat(review["as_of"]) and
                          row["financial_scope_checked"] is True,
                          "FINANCIAL_CANDIDATE_NOT_ORIGINAL_BYTES_AND_DATE")
                else:
                    _need(row["finance_evidence_status"] == "NOT_APPLICABLE" and
                          row["official_body_sha256"] is None and
                          row["official_effective_as_of"] is None and
                          row["financial_scope_checked"] is False,
                          "NONFINANCIAL_SOURCE_ROUTE_INVALID")
            # Native V123 continues to verify every V6 cue, high-risk and
            # finance status. A REJECT does not license candidate publication.
            by_id[cid] = copy.deepcopy(row)
            updated.append({"segment_id":sid,"claim_id":cid,
                            "new_native_status":row["status"],
                            "secondary_chat_note_sha256":note_hash})
        draft["atom_verdicts"] = [by_id[r["claim_id"]] for r in review["atom_verdicts"]]
        # Never clear these fields by math; only the final reviewer with an
        # independently recorded original omission/reconciliation docket can.
        _need(draft["disagreements_adjudicated"] == review["disagreements_adjudicated"] and
              draft["unresolved_high_risk_omissions"] == review["unresolved_high_risk_omissions"] and
              draft["source_cues"] == review["source_cues"],
              "LEGACY_RISK_CUES_OR_DISPUTES_CHANGED")
        native = assess_chat_final_gate(source,exchange,
            host_receipt=case["host_receipt"],chat_review=draft,
            store=case["source_store"],
            official_evidence_bodies=case["official_evidence_bodies"])
        _need(native["status"] in {
            "CHAT_FINAL_HOLD_OPEN", "CHAT_FINAL_REJECTED",
            "CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY"}, "NATIVE_INDETERMINATE")
        compiled[sid] = {"native_review_sha256":_digest(draft),
            "previous_review_sha256":_digest(review),
            "review":draft,
            "native_v123_result":native}
        native_results.append({"segment_id":sid,
            "native_status":native["status"],
            "native_review_sha256":_digest(draft),
            "native_open_count":native["atoms_open"],
            "native_research_candidates":native["atoms_accepted"],
            "native_export_flag_not_e4_authority":native["research_candidate_export_allowed"]})
    _need(sum(len(c["exchange"]["atoms"]) for c in cases_by_segment.values()) ==
          docket["original_atom_count"] and
          {t["segment_id"] for t in docket["items"]} <= set(cases_by_segment),
          "SCOPE_OR_ORIGINAL_ATOM_CENSUS")
    _need(touched == set(tasks), "UNHANDLED_NATIVE_OPEN_TASKS")
    # Native PASS is NOT an E4 pass; no V126/V128 call is made here.
    result = {"schema":SCHEMA,
        "owner_source_sha256":docket["owner_source_sha256"],
        "docket_sha256":docket["docket_sha256"],
        "proposal_receipt_sha256":proposals["proposal_receipt_sha256"],
        "original_open_count":docket["original_open_count"],
        "proposals_considered":len(selected),
        "native_rows_changed":len(updated),
        "native_review_updates":updated,
        "quarantine_type_review_pending":pending,
        "native_results":native_results,
        "all_native_scopes_pass":all(x["native_status"] ==
             "CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY" for x in native_results),
        "model_identity_independently_authenticated":False,
        "official_issuer_origin_authenticated_by_this_bridge":False,
        "e4_approved":False,"e5_authorized":False,
        "knowledge_publication_authorized":False,
        "original_reviews_mutated":False}
    return {"receipt":{**result,"receipt_sha256":_digest(result)},
            "native_private_drafts":compiled}