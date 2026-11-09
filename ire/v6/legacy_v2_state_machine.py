# HISTORICAL V2 REDUCER FOR READ-ONLY EVENT DIGEST VERIFICATION ONLY.
# NEVER IMPORT THIS INTO LIVE V6 EXECUTION OR USE ITS OLD RESEARCH_COMPLETE.
"""Pure V6 reducer. No I/O, global variables, timestamps or model calls.

These transitions store unverified input only. They NEVER assert SOURCE_VERIFIED,
SECOND_PASS_VERIFIED, FINANCIAL_FACT_APPROVED or RESEARCH_CLOSED.
"""
from __future__ import annotations

from copy import deepcopy

from .codec import WINDOW, json_digest, require_hash, require_identifier
from .errors import DomainConflict, InvalidInput


def empty_state() -> dict:
    return {"schema": "IRE_V6_STATE_V4", "source": None,
            "source_attestation": None, "owner_pin": None, "structural_proofs": {},
            "finance_candidate_reviews": {},
            "blind_plan": None, "blind_measurement": None, "terminal_audits": [],
            "models": {}, "reviews": {},
            "source_original_bytes_verified": False,
            "independent_semantic_recall_measured": False,
            "research_report_closed": False,
            "engine_quality_certified": False}


def reduce_event(state: dict, kind: str, payload: dict, event_hash: str) -> dict:
    if type(payload) is not dict:
        raise InvalidInput("EVENT_PAYLOAD_MUST_BE_OBJECT")
    next_state = deepcopy(state)
    if kind == "SCOPE_DECLARED":
        if set(payload) != {"video_id", "source_sha256", "manifest_sha256"}:
            raise InvalidInput("SCOPE_DECLARATION_SCHEMA_INVALID")
        if next_state["source"] is not None:
            raise DomainConflict("SOURCE_ALREADY_DECLARED")
        next_state["source"] = deepcopy(payload)
    elif kind == "SOURCE_ATTESTED":
        if set(payload) != {"video_id", "source_sha256", "manifest_sha256",
                            "cue_census_sha256", "cue_count", "scope_first_cue",
                            "scope_last_cue", "window_count"}:
            raise InvalidInput("SOURCE_ATTESTATION_SCHEMA_INVALID")
        if next_state["source"] is None or next_state["source_attestation"] is not None:
            raise DomainConflict("SOURCE_ATTESTATION_ALREADY_SET_OR_SOURCE_ABSENT")
        if any(payload[k] != next_state["source"][k]
               for k in ("video_id", "source_sha256", "manifest_sha256")):
            raise DomainConflict("SOURCE_ATTESTATION_IDENTITY_MISMATCH")
        for k in ("cue_count", "scope_first_cue", "scope_last_cue", "window_count"):
            if type(payload[k]) is not int or payload[k] <= 0:
                raise InvalidInput("SOURCE_ATTESTATION_COUNT_INVALID")
        require_hash(payload["cue_census_sha256"], "CUE_CENSUS_HASH")
        if payload["scope_first_cue"] > payload["scope_last_cue"] or payload["scope_last_cue"] > payload["cue_count"]:
            raise InvalidInput("SOURCE_ATTESTATION_SCOPE_INVALID")
        next_state["source_attestation"] = {**deepcopy(payload), "event_sha256": event_hash}
    elif kind == "STRUCTURAL_PROOF_RECORDED":
        if set(payload) != {"window_id", "source_attestation_event_sha256",
                            "model_revision_event_sha256", "model_sha256",
                            "review", "audit"}:
            raise InvalidInput("STRUCTURAL_PROOF_SCHEMA_INVALID")
        window_id = require_identifier(payload["window_id"], WINDOW, "WINDOW_ID")
        attested = next_state["source_attestation"]
        if attested is None or payload["source_attestation_event_sha256"] != attested["event_sha256"]:
            raise DomainConflict("STRUCTURAL_PROOF_SOURCE_ATTESTATION_STALE")
        model = next_state["models"].get(window_id)
        if model is None or model["revision_event_sha256"] != payload["model_revision_event_sha256"]:
            raise DomainConflict("STRUCTURAL_PROOF_MODEL_REVISION_STALE")
        if model["model_sha256"] != payload["model_sha256"]:
            raise DomainConflict("STRUCTURAL_PROOF_MODEL_DIGEST_MISMATCH")
        if type(payload["review"]) is not dict or type(payload["audit"]) is not dict:
            raise InvalidInput("STRUCTURAL_PROOF_MISSING_INPUT_OR_AUDIT")
        if payload["audit"].get("review_sha256") != json_digest(payload["review"]) or \
           payload["audit"].get("model_sha256") != model["model_sha256"] or \
           payload["audit"].get("source_sha256") != attested["source_sha256"] or \
           payload["audit"].get("cue_census_sha256") != attested["cue_census_sha256"] or \
           payload["audit"].get("manifest_sha256") != attested["manifest_sha256"] or \
           payload["audit"].get("window_id") != window_id or \
           payload["audit"].get("structural_source_links_checked") is not True or \
           payload["audit"].get("semantic_completeness_verified") is not False or \
           payload["audit"].get("independent_gold_verified") is not False or \
           payload["audit"].get("p0_go") is not False:
            raise InvalidInput("STRUCTURAL_PROOF_AUDIT_UNTRUSTWORTHY")
        next_state["research_report_closed"]=False
        next_state["structural_proofs"][window_id] = {
            "model_revision_event_sha256": model["revision_event_sha256"],
            "proof_event_sha256": event_hash,
            "audit_sha256": json_digest(payload["audit"]),
            "status": "SOURCE_ANCHOR_RECORDED_REPLAY_REQUIRED",
        }
    elif kind == "OWNER_PIN_RECORDED":
        if set(payload) != {"schema", "video_id", "source_sha256",
                            "manifest_sha256", "cue_census_sha256",
                            "inventory_sha256", "inventory_video_count",
                            "owner_identity_verified", "operator_held_inventory_digest_matched",
                            "private_source_replayed_this_call"} or \
           payload["schema"] != "IRE_V6_OWNER_SOURCE_ANCHOR_V1":
            raise InvalidInput("OWNER_PIN_EVENT_SCHEMA_INVALID")
        att = next_state["source_attestation"]
        if att is None or next_state["owner_pin"] is not None:
            raise DomainConflict("OWNER_PIN_DUPLICATE_OR_SOURCE_NOT_ATTESTED")
        if any(payload[k] != att[k] for k in (
                "video_id", "source_sha256", "manifest_sha256", "cue_census_sha256")):
            raise DomainConflict("OWNER_PIN_SOURCE_NOT_EQUAL_TO_ATTESTATION")
        require_hash(payload["inventory_sha256"], "OWNER_INVENTORY_SHA256")
        if (type(payload["inventory_video_count"]) is not int or
            not 1 <= payload["inventory_video_count"] <= 2000 or
            payload["owner_identity_verified"] is not False or
            payload["operator_held_inventory_digest_matched"] is not True or
            payload["private_source_replayed_this_call"] is not True):
            raise InvalidInput("OWNER_PIN_ASSERTIONS_INVALID")
        next_state["owner_pin"] = {**deepcopy(payload), "event_sha256": event_hash}
    elif kind == "FINANCE_CANDIDATE_RECORDED":
        if set(payload) != {"window_id", "model_revision_event_sha256",
                            "structural_proof_event_sha256", "owner_pin_event_sha256",
                            "official_audit", "relation_audit"}:
            raise InvalidInput("FINANCE_CANDIDATE_EVENT_SCHEMA_INVALID")
        wid = require_identifier(payload["window_id"], WINDOW, "WINDOW_ID")
        model = next_state["models"].get(wid)
        proof = next_state["structural_proofs"].get(wid)
        owner = next_state["owner_pin"]
        if (model is None or proof is None or owner is None or
            model["revision_event_sha256"] != payload["model_revision_event_sha256"] or
            proof["model_revision_event_sha256"] != model["revision_event_sha256"] or
            proof["proof_event_sha256"] != payload["structural_proof_event_sha256"] or
            owner["event_sha256"] != payload["owner_pin_event_sha256"]):
            raise DomainConflict("FINANCE_CANDIDATE_DEPENDENCY_STALE")
        official, relation = payload["official_audit"], payload["relation_audit"]
        if (type(official) is not dict or type(relation) is not dict or
            official.get("schema") != "IRE_V6_OFFICIAL_CANDIDATE_AUDIT_V1" or
            relation.get("schema") != "IRE_V6_PRIOR_RELATION_AUDIT_V1" or
            official.get("claim_id") != relation.get("claim_id") or
            official.get("finance_fact_approved") is not False or
            relation.get("finance_fact_approved") is not False or
            official.get("claim_semantically_supported") is not False or
            relation.get("semantic_relation_verified") is not False or
            official.get("captured_document_bytes_verified") is not True or
            relation.get("baseline_entry_membership_verified") is not True):
            raise InvalidInput("FINANCE_CANDIDATE_FALSE_AUTHORITY")
        key = wid + ":" + official["claim_id"]
        next_state["research_report_closed"]=False
        next_state["finance_candidate_reviews"][key] = {
            "model_revision_event_sha256": model["revision_event_sha256"],
            "finance_event_sha256": event_hash,
            "official_audit_sha256": json_digest(official),
            "relation_audit_sha256": json_digest(relation),
            "status": "STRUCTURAL_FINANCE_CANDIDATE_ONLY",
        }
    elif kind == "BLIND_PLAN_FROZEN":
        if set(payload)!={"plan", "plan_sha256", "owner_pin_event_sha256"} or \
           type(payload["plan"]) is not dict:
            raise InvalidInput("BLIND_PLAN_EVENT_SHAPE_INVALID")
        if next_state["blind_plan"] is not None or next_state["models"]:
            raise DomainConflict("BLIND_PLAN_MUST_PRECEDE_ALL_PREDICTIONS")
        owner = next_state["owner_pin"]
        if owner is None or payload["owner_pin_event_sha256"]!=owner["event_sha256"]:
            raise DomainConflict("BLIND_PLAN_REQUIRES_OWNER_PIN")
        if json_digest(payload["plan"])!=payload["plan_sha256"]:
            raise InvalidInput("BLIND_PLAN_DIGEST_MISMATCH")
        if (payload["plan"].get("source_sha256")!=owner["source_sha256"] or
            payload["plan"].get("manifest_sha256")!=owner["manifest_sha256"]):
            raise DomainConflict("BLIND_PLAN_OWNER_SOURCE_DRIFT")
        next_state["blind_plan"]={"plan":deepcopy(payload["plan"]),
                                  "plan_sha256":payload["plan_sha256"],
                                  "event_sha256":event_hash}
    elif kind == "BLIND_MEASUREMENT_RECORDED":
        if set(payload)!={"plan_event_sha256", "revision_set_sha256", "metrics",
                           "gold", "predictions", "alignment"}:
            raise InvalidInput("BLIND_MEASUREMENT_EVENT_SHAPE_INVALID")
        plan=next_state["blind_plan"]
        if plan is None or payload["plan_event_sha256"]!=plan["event_sha256"]:
            raise DomainConflict("BLIND_MEASUREMENT_PLAN_MISSING_OR_STALE")
        if type(payload["metrics"]) is not dict or \
           payload["metrics"].get("schema")!="IRE_V6_BLIND_ARITHMETIC_V1":
            raise InvalidInput("BLIND_MEASUREMENT_METRICS_INVALID")
        for field in ("gold", "predictions", "alignment"):
            if type(payload[field]) is not dict:
                raise InvalidInput("BLIND_MEASUREMENT_INPUT_INVALID")
            if payload["metrics"].get({"gold":"gold_sha256", "predictions":"predictions_sha256", "alignment":"alignment_sha256"}[field])!=json_digest(payload[field]):
                raise InvalidInput("BLIND_MEASUREMENT_INPUT_DIGEST_MISMATCH")
        if payload["metrics"].get("plan_sha256")!=plan["plan_sha256"] or \
           payload["metrics"].get("semantic_accuracy_certified") is not False or \
           payload["metrics"].get("engine_quality_certified") is not False or \
           payload["metrics"].get("actual_reviewer_identity_verified") is not False or \
           payload["metrics"].get("actual_blindness_independently_verified") is not False:
            raise InvalidInput("BLIND_MEASUREMENT_FALSE_CERTIFICATION")
        ids=sorted(next_state["models"])
        revisions=json_digest([{"window_id":wid,"revision_event_sha256":
                      next_state["models"][wid]["revision_event_sha256"]} for wid in ids])
        if revisions!=payload["revision_set_sha256"]:
            raise DomainConflict("BLIND_MEASUREMENT_MODEL_REVISION_DRIFT")
        next_state["blind_measurement"]={
            "event_sha256":event_hash, "plan_event_sha256":plan["event_sha256"],
            "revision_set_sha256":revisions, "metrics_sha256":json_digest(payload["metrics"]),
            "semantic_accuracy_certified":False}
    elif kind == "TERMINAL_OFFICIAL_COMPLETION_RECORDED":
        if (set(payload)!={"schema","base_head_sha256","base_state_sha256",
                           "private_input_sha256","report"} or
            payload["schema"]!="IRE_V6_OFFICIAL_TERMINAL_EVENT_V2" or
            type(payload["report"]) is not dict):
            raise InvalidInput("OFFICIAL_TERMINAL_EVENT_SCHEMA_INVALID")
        require_hash(payload["base_head_sha256"],"OFFICIAL_TERMINAL_BASE_HEAD")
        require_hash(payload["private_input_sha256"],"OFFICIAL_TERMINAL_INPUT_SHA")
        report=payload["report"]
        from .official_completion import LAW_RULE_ID, LAW_SOURCE_SHA256
        revisions=json_digest([
            {"window_id":wid,"revision_event_sha256":item["revision_event_sha256"]}
            for wid,item in sorted(state["models"].items())])
        if (payload["base_state_sha256"]!=json_digest(state) or
            state["research_report_closed"] is not False or
            report.get("schema")!="IRE_V6_OFFICIAL_SCOPE_TERMINAL_REPORT_V2" or
            report.get("source_sha256")!=state["source"]["source_sha256"] or
            report.get("manifest_sha256")!=state["source"]["manifest_sha256"] or
            report.get("rule_id")!=LAW_RULE_ID or
            report.get("official_document_sha256")!=LAW_SOURCE_SHA256 or
            report.get("model_revision_set_sha256")!=revisions or
            report.get("window_count")!=len(state["models"]) or
            type(report.get("officially_verified_fact_count")) is not int or
            report["officially_verified_fact_count"]<1 or
            report.get("scope_fully_modelled") is not True or
            report.get("all_registered_factual_assertions_verified") is not True or
            report.get("historical_official_source_bytes_verified") is not True or
            report.get("independent_human_review_required") is not False or
            report.get("general_semantic_recall_certified") is not False or
            report.get("legacy116_semantic_merge_approved") is not False or
            report.get("outcome")!="OFFICIAL_SOURCE_SCOPED_COMPLETE" or
            report.get("research_complete") is not True or
            report.get("engine_quality_certified") is not False or
            report.get("p0_go") is not False):
            raise InvalidInput("OFFICIAL_TERMINAL_UNAUTHORIZED_COMPLETION")
        next_state["terminal_audits"].append({
            "event_sha256":event_hash,
            "base_head_sha256":payload["base_head_sha256"],
            "base_state_sha256":payload["base_state_sha256"],
            "report_sha256":json_digest(report),
            "outcome":"OFFICIAL_SOURCE_SCOPED_COMPLETE"})
        next_state["research_report_closed"]=True
    elif kind == "TERMINAL_AUDIT_RECORDED":
        if set(payload)!={"schema", "base_head_sha256", "base_state_sha256", "private_input_sha256", "report"} or \
           payload["schema"]!="IRE_V6_TERMINAL_AUDIT_EVENT_V1" or \
           type(payload["report"]) is not dict:
            raise InvalidInput("TERMINAL_AUDIT_EVENT_INVALID")
        require_hash(payload["private_input_sha256"],"TERMINAL_AUDIT_INPUT_COMMITMENT")
        report=payload["report"]
        if payload["base_state_sha256"]!=json_digest(state) or \
           report.get("schema")!="IRE_V6_TERMINAL_AUDIT_REPORT_V1" or \
           report.get("outcome")!="TERMINAL_BLOCKED" or \
           report.get("research_complete") is not False or \
           report.get("engine_quality_certified") is not False or \
           report.get("p0_go") is not False or \
           report.get("official_fact_semantics_verified") is not False or \
           report.get("independent_gold_review_verified") is not False or \
           report.get("independent_source_owner_authenticated") is not False or \
           type(report.get("blockers")) is not list or \
           not report["blockers"]:
            raise InvalidInput("TERMINAL_AUDIT_FALSE_COMPLETION")
        next_state["terminal_audits"].append({
            "event_sha256":event_hash,
            "base_head_sha256":payload["base_head_sha256"],
            "base_state_sha256":payload["base_state_sha256"],
            "report_sha256":json_digest(report),
            "outcome":"TERMINAL_BLOCKED"})
    elif kind == "MODEL_RECORDED":
        if set(payload) != {"window_id", "model"}:
            raise InvalidInput("MODEL_EVENT_SCHEMA_INVALID")
        window_id = require_identifier(payload["window_id"], WINDOW, "WINDOW_ID")
        model = payload["model"]
        if type(model) is not dict or not model:
            raise InvalidInput("MODEL_PAYLOAD_REQUIRED")
        if next_state["source"] is None:
            raise DomainConflict("SOURCE_NOT_DECLARED")
        previous = next_state["models"].get(window_id)
        next_state["research_report_closed"]=False
        next_state["models"][window_id] = {
            "revision": 1 if previous is None else previous["revision"] + 1,
            "revision_event_sha256": event_hash,
            "model_sha256": json_digest(model),
        }
    elif kind == "REVIEW_PROPOSED":
        if set(payload) != {"window_id", "model_revision_event_sha256", "review"}:
            raise InvalidInput("REVIEW_EVENT_SCHEMA_INVALID")
        wid = require_identifier(payload["window_id"], WINDOW, "WINDOW_ID")
        revision_hash = require_hash(payload["model_revision_event_sha256"],
                                     "MODEL_REVISION_EVENT_HASH")
        review = payload["review"]
        if type(review) is not dict or not review:
            raise InvalidInput("REVIEW_INPUT_REQUIRED")
        model = next_state["models"].get(wid)
        if model is None or model["revision_event_sha256"] != revision_hash:
            raise DomainConflict("REVIEW_STALE_OR_UNKNOWN_MODEL_REVISION")
        next_state["reviews"].setdefault(wid, []).append({
            "review_event_sha256": event_hash,
            "model_revision_event_sha256": revision_hash,
            "review_sha256": json_digest(review),
            "status": "UNVERIFIED_PROPOSAL",
        })
    else:
        # No arbitrary closure or proof-verification event is accepted by V6-1.
        raise DomainConflict("EVENT_TYPE_NOT_ENABLED:" + str(kind))
    return next_state


def progress(state: dict) -> dict:
    models = state["models"]
    current_proposals = sum(
        1 for wid, rev in models.items()
        for proposal in state["reviews"].get(wid, [])
        if proposal["model_revision_event_sha256"] == rev["revision_event_sha256"]
    )
    current_proofs = sum(1 for wid, proof in state["structural_proofs"].items()
                         if wid in models and
                         proof["model_revision_event_sha256"] == models[wid]["revision_event_sha256"])
    current_finance = sum(1 for key, record in state["finance_candidate_reviews"].items()
                          if key.split(":")[0] in models and
                          record["model_revision_event_sha256"] ==
                          models[key.split(":")[0]]["revision_event_sha256"])
    return {
        "owner_inventory_pin_recorded": state["owner_pin"] is not None,
        "blind_plan_frozen_before_predictions": state["blind_plan"] is not None,
        "blind_measurement_recorded": state["blind_measurement"] is not None,
        "terminal_blocked_audit_count": sum(
            a["outcome"]=="TERMINAL_BLOCKED" for a in state["terminal_audits"]),
        "terminal_official_scope_count": sum(
            a["outcome"]=="OFFICIAL_SOURCE_SCOPED_COMPLETE"
            for a in state["terminal_audits"]),
        "current_revision_finance_candidate_reviews": current_finance,
        "financial_facts_approved": False,
        "source_pointer_declared": state["source"] is not None,
        "source_original_bytes_verified": False,
        "source_attestation_recorded": state["source_attestation"] is not None,
        "current_revision_structural_proof_records": current_proofs,
        "model_windows_recorded": len(models),
        "unverified_current_revision_review_proposals": current_proposals,
        "verified_proofs": 0,
        "research_report_closed": state["research_report_closed"],
        "independent_semantic_recall_measured": False,
        "engine_quality_certified": False,
        "p0_go": False,
    }
