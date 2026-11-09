"""One-request, ACID all-or-nothing host-origin model+source-proof batch.

ChatGPT host supplies *already generated* atomic candidates and prior relation
proposals. This module never calls an external LLM or asserts semantic recall.
No model/proof events survive a failed batch; replay is deterministic and
idempotent by run identifier and exact evidence digests.
"""
from __future__ import annotations

import json

from .atomic_exchange import _digest_rows, audit_host_atomic_exchange
from .codec import WINDOW, IDENT, json_digest, require_hash, require_identifier
from .errors import (ConcurrentHeadChanged, DomainConflict, IdempotencyConflict,
                     InvalidInput, LedgerCorrupted, QualityNotProven)
from .prior_knowledge import audit_prior_candidates
from .proof import audit_model_anchors
from .state_machine import reduce_event
from .trust import verify_owner_inventory

MARKER_SCHEMA = "IRE_V6_HOST_BATCH_COMMIT_MARKER_V1"


def submit_host_atomic_batch(store, *, scope_id: str, run_id: str,
                             expected_head: str, raw: bytes, manifest: dict,
                             inventory_bytes: bytes,
                             expected_inventory_sha256: str,
                             exchange: dict, knowledge: dict,
                             window_models: dict, window_reviews: dict) -> dict:
    """Commit a complete, source-bound host batch or no events at all.

    Requires current operator-pinned source and complete non-empty models
    for every planned window. Empty claim windows remain unsupported by
    the V6 atomic MODEL_RECORDED contract and correctly fail closed.
    """
    scope_id = require_identifier(scope_id, name="SCOPE_ID")
    run_id = require_identifier(run_id, IDENT,"HOST_RUN_ID")
    if len(run_id)>48:
        raise InvalidInput("HOST_RUN_ID_TOO_LONG")
    expected_head = require_hash(expected_head,"EXPECTED_HEAD")
    if type(window_models) is not dict or type(window_reviews) is not dict:
        raise InvalidInput("HOST_BATCH_MODEL_MAPS_REQUIRED")
    con = store._connection()
    try:
        def work():
            state,seq,head = store._replay(con,scope_id)
            owner,att=state["owner_pin"],state["source_attestation"]
            if owner is None or att is None:
                raise DomainConflict("HOST_BATCH_PINNED_SOURCE_REQUIRED")
            pinned=verify_owner_inventory(
                raw,manifest,inventory_bytes,
                expected_inventory_sha256=expected_inventory_sha256)
            source=pinned.source
            if (pinned.attestation()!={k:v for k,v in owner.items()
                                         if k!="event_sha256"} or
                source.attestation()!={k:v for k,v in att.items()
                                          if k!="event_sha256"}):
                raise DomainConflict("HOST_BATCH_SOURCE_PIN_LEDGER_DRIFT")
            atom_audit=audit_host_atomic_exchange(source,exchange)
            prior_audit=audit_prior_candidates(source,exchange,knowledge)
            if (atom_audit["unresolved_cues"] or
                atom_audit["suspicious_no_atom_cues"]):
                raise QualityNotProven("HOST_BATCH_UNRESOLVED_SOURCE_RESIDUALS")
            windows=[wid for wid,_,_ in source.primary_windows]
            if set(window_models)!=set(windows) or set(window_reviews)!=set(windows):
                raise InvalidInput("HOST_BATCH_ALL_PLANNED_WINDOWS_REQUIRED")
            atomic_claims={a["claim_id"]:a for a in exchange["atoms"]}
            model_claim_ids=set()
            audits={}
            pins=[]
            for wid in windows:
                model,review=window_models[wid],window_reviews[wid]
                if (type(model) is not dict or
                    model.get("schema")!="IRE_V6_ATOMIC_MODEL_V1" or
                    type(model.get("claims")) is not list or
                    not model["claims"]):
                    raise QualityNotProven("HOST_BATCH_EMPTY_WINDOW_MODEL_UNSUPPORTED")
                audit=audit_model_anchors(source,wid,model,review)
                audits[wid]=audit
                for claim in model["claims"]:
                    cid=claim["claim_id"]
                    atom=atomic_claims.get(cid)
                    if (cid in model_claim_ids or atom is None or
                        atom["owner_window_id"]!=wid or
                        any(claim[k]!=atom[k] for k in (
                            "claim_id","owner_window_id","proposition","kind","source_refs"))):
                        raise InvalidInput("HOST_BATCH_ATOM_MODEL_INCONSISTENT")
                    model_claim_ids.add(cid)
                pins.append({"window_id":wid,"model_sha256":json_digest(model),
                             "review_sha256":json_digest(review),
                             "structural_audit_sha256":json_digest(audit)})
            if model_claim_ids!=set(atomic_claims):
                raise InvalidInput("HOST_BATCH_MISSING_HOST_ATOMS")
            commitment=json_digest({
                "base_head_sha256":expected_head,
                "source_sha256":source.source_sha256,
                "manifest_sha256":source.manifest_sha256,
                "atom_candidate_digest":atom_audit["atom_candidate_digest"],
                "cue_disposition_digest":atom_audit["cue_disposition_digest"],
                "prior_relation_digest":_digest_rows(knowledge["relations"]),
                "prior_master116_blob":prior_audit["master116_git_blob_sha1"],
                "prior_p4_22_blob":prior_audit["p4_prior22_git_blob_sha1"],
                "prior_p4_7_blob":prior_audit["p4_new7_git_blob_sha1"],
                "window_model_review_pins":pins,
            })
            seal_id=run_id+"_seal"
            prior=con.execute(
                "SELECT * FROM events WHERE scope_id=? AND command_id=?",
                (scope_id,seal_id)).fetchone()
            if prior is not None:
                event=json.loads(prior["event_json"])
                review=event.get("payload",{}).get("review",{})
                if (event.get("type")!="REVIEW_PROPOSED" or
                    review.get("schema")!=MARKER_SCHEMA or
                    review.get("bundle_sha256")!=commitment or
                    review.get("original_expected_head")!=expected_head):
                    raise IdempotencyConflict("HOST_BATCH_RETRY_INPUT_CHANGED")
                return {"schema":"IRE_V6_HOST_BATCH_RECEIPT_V1",
                        "scope_id":scope_id, "event_sha256":prior["event_sha256"],
                        "bundle_sha256":commitment,"idempotent_replay":True,
                        "is_current":head==prior["event_sha256"],
                        "atomic_batch_committed":True,
                        "source_and_proof_model_windows":len(windows),
                        "semantic_truth_certified":False,
                        "independent_gold_recall_measured":False,
                        "research_complete":False,"p0_go":False}
            for wid in windows:
                for suffix in ("model","proof"):
                    command=run_id+"_"+suffix+"_"+wid
                    if con.execute(
                        "SELECT 1 FROM events WHERE scope_id=? AND command_id=?",
                        (scope_id,command)).fetchone():
                        raise LedgerCorrupted("HOST_BATCH_PARTIAL_PRIOR_PUBLICATION")
            if head!=expected_head:
                raise ConcurrentHeadChanged("HOST_BATCH_EXPECTED_HEAD_STALE")
            for wid in windows:
                model,review=window_models[wid],window_reviews[wid]
                mp={"window_id":wid,"model":model}
                result=store._write_event(
                    con,scope_id=scope_id,seq=seq+1,prev=head,
                    command_id=run_id+"_model_"+wid,
                    kind="MODEL_RECORDED",payload=mp,state=state)
                state=reduce_event(state,"MODEL_RECORDED",mp,result["event_sha256"])
                head,seq=result["event_sha256"],result["sequence"]
                revision=state["models"][wid]
                pp={"window_id":wid,
                    "source_attestation_event_sha256":att["event_sha256"],
                    "model_revision_event_sha256":revision["revision_event_sha256"],
                    "model_sha256":revision["model_sha256"],
                    "review":review,"audit":audits[wid]}
                proof_result=store._write_event(
                    con,scope_id=scope_id,seq=seq+1,prev=head,
                    command_id=run_id+"_proof_"+wid,
                    kind="STRUCTURAL_PROOF_RECORDED",payload=pp,state=state)
                state=reduce_event(state,"STRUCTURAL_PROOF_RECORDED",pp,
                                   proof_result["event_sha256"])
                head,seq=proof_result["event_sha256"],proof_result["sequence"]
            last=windows[-1]
            marker={"schema":MARKER_SCHEMA,"bundle_sha256":commitment,
                    "original_expected_head":expected_head,
                    "source_sha256":source.source_sha256,
                    "host_cue_count":atom_audit["original_scoped_cues_enumerated"],
                    "model_windows":len(windows),
                    "knowledge_master_claims":116,
                    "knowledge_p4_nodes":29,
                    "semantic_truth_certified":False,
                    "engine_quality_certified":False}
            payload={"window_id":last,
                     "model_revision_event_sha256":state["models"][last]["revision_event_sha256"],
                     "review":marker}
            receipt=store._write_event(con,scope_id=scope_id,seq=seq+1,prev=head,
                                       command_id=seal_id,
                                       kind="REVIEW_PROPOSED",payload=payload,state=state)
            after,final_seq,final_head=store._replay(con,scope_id)
            if (final_head!=receipt["event_sha256"] or final_seq!=receipt["sequence"]
                or after["research_report_closed"] is not False or
                json_digest(after)!=receipt["state_sha256"]):
                raise LedgerCorrupted("HOST_BATCH_POST_WRITE_REPLAY_MISMATCH")
            return {"schema":"IRE_V6_HOST_BATCH_RECEIPT_V1",
                    "scope_id":scope_id, "event_sha256":receipt["event_sha256"],
                    "bundle_sha256":commitment,"idempotent_replay":False,
                    "is_current":True,"atomic_batch_committed":True,
                    "source_and_proof_model_windows":len(windows),
                    "semantic_truth_certified":False,
                    "independent_gold_recall_measured":False,
                    "research_complete":False,"p0_go":False}
        return store._commit(con,work)
    finally:
        con.close()
