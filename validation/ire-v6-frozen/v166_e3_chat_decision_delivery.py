"""V166 E3 — ChatGPT decision delivery across frozen V123 and V127/V128.

No model/API invocation and NO new approval authority. The only judgments
are pre-authored CHATGPT_IN_CHAT private evidence records, replayed by the
exact frozen V123 gate. A REJECT must never be reported as an ordinary HOLD.
"""
from __future__ import annotations

from contextlib import closing
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
from v123_chat_final_gate import assess_chat_final_gate
from v128_host_continuous_video import run_all_video_scopes_in_chat

SCHEMA = "IRE_V166_E3_SOURCE_BOUND_CHAT_DECISION_DELIVERY_V1"
RUN_SCHEMA = "IRE_V166_E3_PARENT_DECISION_TRANSPORT_V1"
NATIVE = {
    "CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY": "PASS_RESEARCH_CANDIDATES_ONLY",
    "CHAT_FINAL_HOLD_OPEN": "HOLD_UNRELEASED",
    "CHAT_FINAL_REJECTED": "REJECTED",
}
ATOM = {
    "ACCEPT_FOR_RESEARCH": "ACCEPT_RESEARCH_CANDIDATE_ONLY",
    "OPEN": "OPEN_UNRELEASED",
    "REJECT": "REJECTED",
    "EXCLUDE_FROM_RESEARCH": "QUARANTINED_NOT_RESEARCH_KNOWLEDGE",
}
CHECKPOINT = {
    "PASS_RESEARCH_CANDIDATES_ONLY": "PASS",
    "HOLD_UNRELEASED": "HOLD",
    "REJECTED": "REJECT",
}


def _assert(ok, code):
    if not ok:
        raise InvalidInput("V166_E3_DECISION_" + code)


def replay_chat_decision_envelope(case):
    """Source-replay one actual ChatGPT review with the unmodified V123 gate.

    The output is metadata/decision custody, not formal financial fact
    verification and not a new standalone research release receipt.
    """
    _assert(type(case) is dict, "CASE_REQUIRED")
    must = {
        "source", "exchange", "host_receipt", "chat_review",
        "source_store", "official_evidence_bodies",
    }
    _assert(must.issubset(case), "CASE_FIELDS_REQUIRED")
    source = case["source"]
    exchange = case["exchange"]
    review = case["chat_review"]
    _assert(type(review) is dict and
            review.get("review_executor") == "CHATGPT_IN_CHAT",
            "FINAL_CHAT_REVIEW_REQUIRED")
    native = assess_chat_final_gate(
        source, exchange,
        host_receipt=case["host_receipt"],
        chat_review=review,
        store=case["source_store"],
        official_evidence_bodies=case["official_evidence_bodies"])
    _assert(native["status"] in NATIVE, "NOT_A_COMPLETE_NATIVE_REVIEW")
    _assert(native["chat_final_review_digest_sha256"] == json_digest(review),
            "NATIVE_REVIEW_DIGEST_CHANGED")
    atoms = {a["claim_id"]:a for a in exchange["atoms"]}
    verdicts = review["atom_verdicts"]
    _assert(len(atoms) == len(exchange["atoms"]) == len(verdicts),
            "ATOM_CENSUS")
    q = review.get("quarantine")
    reason = {r["claim_id"]:r["reason_code"]
              for r in q["atom_rows"]} if q is not None else {}
    decisions=[]
    for v in verdicts:
        cid=v["claim_id"]
        _assert(cid in atoms and v["status"] in ATOM, "UNKNOWN_ATOM_DECISION")
        disposition=ATOM[v["status"]]
        _assert((disposition=="QUARANTINED_NOT_RESEARCH_KNOWLEDGE") ==
                (cid in reason), "QUARANTINE_REASON_MISSING_OR_INJECTED")
        decisions.append({
            "claim_id":cid,
            "atom_sha256":v["atom_sha256"],
            "review_note_sha256":v["private_review_note_sha256"],
            "disposition":disposition,
            "reason_code":reason.get(cid),
            "quarantine_not_fact_approval":cid in reason,
        })
    _assert(len({x["claim_id"] for x in decisions}) == len(decisions),
            "DUPLICATE_ATOM")
    accepted=sum(x["disposition"]=="ACCEPT_RESEARCH_CANDIDATE_ONLY" for x in decisions)
    open_count=sum(x["disposition"]=="OPEN_UNRELEASED" for x in decisions)
    reject_count=sum(x["disposition"]=="REJECTED" for x in decisions)
    quarantined=sum(x["disposition"]=="QUARANTINED_NOT_RESEARCH_KNOWLEDGE"
                    for x in decisions)
    _assert((accepted,open_count,reject_count)==(
        native["atoms_accepted"],native["atoms_open"],native["atoms_rejected"]),
        "NATIVE_DISPOSITION_COUNTS_DIVERGED")
    _assert(quarantined==native.get("atoms_excluded",0)
            and sorted(reason)==native.get("quarantined_claim_ids",[]),
            "NATIVE_QUARANTINE_CENSUS_DIVERGED")
    status=NATIVE[native["status"]]
    _assert((status=="REJECTED")==(reject_count>0), "REJECT_PRIORITY_LOST")
    _assert(native["research_candidate_export_allowed"] ==
            (status=="PASS_RESEARCH_CANDIDATES_ONLY"),
            "EXTERNAL_RELEASE_STATUS_DIVERGED")
    _assert(status!="PASS_RESEARCH_CANDIDATES_ONLY" or
            (open_count==0 and reject_count==0 and native["finance_open"]==0
             and native["high_risk_open"]==0), "OPEN_CANNOT_BE_PASSED")
    return {
        "schema":SCHEMA,
        "source_sha256":native["source_sha256"],
        "manifest_sha256":native["manifest_sha256"],
        "host_event_sha256":case["host_receipt"]["event_sha256"],
        "host_bundle_sha256":case["host_receipt"]["bundle_sha256"],
        "native_gate_status":native["status"],
        "decision":status,
        "expected_checkpoint_decision":CHECKPOINT[status],
        "chat_review_sha256":native["chat_final_review_digest_sha256"],
        "native_gate_receipt_sha256":json_digest(native),
        "atom_decisions":decisions,
        "atom_census":len(decisions),
        "accepted_research_candidates":accepted,
        "open_atoms_blocked":open_count,
        "rejected_atoms":reject_count,
        "quarantined_source_only_atoms":quarantined,
        "finance_open":native["finance_open"],
        "high_risk_open_legacy":native["high_risk_open"],
        "risk_counter_independent_false_negative_proof":False,
        "research_candidate_export_allowed":native["research_candidate_export_allowed"],
        "formal_financial_fact_approved":False,
        "personal_investment_advice_authorized":False,
        "p0_go":False,
    }


def run_full_video_with_e3_decisions(checkpoint, knowledge_store, *,
                                      review_or_load_child, review_seams,
                                      review_parent, expected_knowledge_head,
                                      externally_pinned_checkpoint_head=None,
                                      externally_pinned_knowledge_head=None):
    """One real V128 invocation, and an explicit E3 decision read-back.

    Preserves underlying V128 status. Adds an authenticated E3 user-facing
    subtype so a child REJECT cannot be mistaken for recoverable HOLD. Checks
    the V127.1 persisted review and gate digests, never trusts callback alone.
    """
    delivered={}
    order=[]
    def audited_child(segment_id, manifest, stage, original_raw):
        supplied=review_or_load_child(segment_id,manifest,stage,original_raw)
        _assert(type(supplied) is dict and type(supplied.get("case")) is dict,
                "CHILD_CALLBACK_REQUIRED")
        envelope=replay_chat_decision_envelope(supplied["case"])
        _assert(segment_id not in delivered,"DUPLICATE_SEGMENT")
        delivered[segment_id]=envelope
        order.append(segment_id)
        return supplied

    original=run_all_video_scopes_in_chat(
        checkpoint,knowledge_store,
        review_or_load_child=audited_child,
        review_seams=review_seams,
        review_parent=review_parent,
        expected_knowledge_head=expected_knowledge_head,
        externally_pinned_checkpoint_head=externally_pinned_checkpoint_head,
        externally_pinned_knowledge_head=externally_pinned_knowledge_head)
    with closing(checkpoint._connect()) as con:
        head,latest=checkpoint._audit(con)
    _assert(type(original) is dict and
            original.get("child_scopes_supplied")==len(order)
            and head==original["checkpoint_head_sha256"],
            "NATIVE_V128_HEAD_OR_CHILD_CENSUS")
    out=[]
    for segment_id in order:
        item=delivered[segment_id]
        persisted=latest.get(segment_id)
        _assert(persisted is not None and
                persisted["decision"]==item["expected_checkpoint_decision"] and
                persisted["chat_review_sha256"]==item["chat_review_sha256"] and
                persisted["gate_receipt_sha256"]==item["native_gate_receipt_sha256"] and
                persisted["host_event_sha256"]==item["host_event_sha256"] and
                persisted["host_bundle_sha256"]==item["host_bundle_sha256"],
                "CHECKPOINT_CHAT_DECISION_DIVERGED")
        out.append({"segment_id":segment_id,"decision":item["decision"],
                    "native_v123_gate":item["native_gate_status"],
                    "chat_review_sha256":item["chat_review_sha256"],
                    "v127_checkpoint_decision":persisted["decision"],
                    "checkpoint_gate_receipt_sha256":persisted["gate_receipt_sha256"],
                    "atoms":item["atom_decisions"],
                    "accepted":item["accepted_research_candidates"],
                    "open":item["open_atoms_blocked"],
                    "rejected":item["rejected_atoms"],
                    "quarantined":item["quarantined_source_only_atoms"]})
    rejected=[a for a in out if a["decision"]=="REJECTED"]
    held=[a for a in out if a["decision"]=="HOLD_UNRELEASED"]
    if rejected:
        classification="CHILD_REJECTED_FINAL_CHAT"
    elif held:
        classification="CHILD_HOLD_UNRELEASED"
    else:
        _assert(original["status"]=="WHOLE_VIDEO_RESEARCH_CANDIDATE_PUBLISHED_ATOMICALLY",
                "ALL_PASS_BUT_PARENT_NOT_PUBLISHED")
        classification="PUBLISHED_RESEARCH_CANDIDATES_ONLY"
    _assert(original.get("all_video_knowledge_published") is
            (classification=="PUBLISHED_RESEARCH_CANDIDATES_ONLY"),
            "UNAPPROVED_PARENT_RELEASE")
    return {
        "schema":RUN_SCHEMA,
        "native_v128_status":original["status"],
        "explicit_e3_status":classification,
        "checkpoint_head_sha256":head,
        "child_decisions":out,
        "child_scopes_reviewed":len(out),
        "all_video_knowledge_published":original["all_video_knowledge_published"],
        "research_candidate_only":True,
        "formal_financial_fact_approved":False,
        "personal_advice_approved":False,
        "p0_go":False,
    }
