"""One-request, ACID all-or-nothing host-origin model+source-proof batch.

ChatGPT host supplies *already generated* atomic candidates and prior relation
proposals. This module never calls an external LLM or asserts semantic recall.
No model/proof events survive a failed batch; replay is deterministic and
idempotent by run identifier and exact evidence digests.
"""
from __future__ import annotations

import json
from copy import deepcopy

from .chat_revision import compile_chat_atom_revision

from .atomic_exchange import _digest_rows, audit_host_atomic_exchange
from .codec import WINDOW, IDENT, json_digest, require_hash, require_identifier
from .errors import (ConcurrentHeadChanged, DomainConflict, IdempotencyConflict,
                     InvalidInput, LedgerCorrupted, QualityNotProven)
from .prior_knowledge import audit_prior_candidates
from .proof import audit_model_anchors
from .semantic_frontier import source_first_semantic_frontier
from .semantic_risk import audit_semantic_risks
from .host_quarantine_preflight import audit_host_quarantine_preflight, TYPED_STAGING_RECEIPT, audit_typed_staging_successor
from .state_machine import reduce_event
from .trust import verify_owner_inventory

MARKER_SCHEMA = "IRE_V6_HOST_BATCH_COMMIT_MARKER_V3"


def _compile_revision_record(source, inputs):
    """Rebuild the exact unapproved proposal from reviewer inputs."""
    if type(inputs) is not dict or set(inputs) != {"before", "edits", "cue_reviews"}:
        raise InvalidInput("HOST_CHAT_REVISION_INPUT_SCHEMA")
    if type(inputs["cue_reviews"]) is not list:
        raise InvalidInput("HOST_CHAT_REVISION_CUE_REVIEWS_REQUIRED")
    result = compile_chat_atom_revision(
        source, inputs["before"], edits=inputs["edits"],
        cue_reviews=inputs["cue_reviews"])
    record = {"schema":"IRE_V6_PRIVATE_CHAT_REVISION_RECORD_V1",
              "inputs":deepcopy(inputs),
              "result":deepcopy(result)}
    # Existing canonical event limits still apply. No truncation or silent
    # dropping of reasons/quotes when a large batch exceeds the limit.
    json_digest(record)
    return record


def read_host_chat_revision(store, *, scope_id, run_id, raw, manifest,
                            inventory_bytes, expected_inventory_sha256):
    """Private read of a committed unapproved revision, with source replay.

    This is not evidence of an independent reviewer or financial truth.
    The read never writes a new model or advances a research gate.
    """
    scope_id = require_identifier(scope_id, name="SCOPE_ID")
    run_id = require_identifier(run_id, IDENT, "HOST_RUN_ID")
    if len(run_id)>48:
        raise InvalidInput("HOST_RUN_ID_TOO_LONG")
    con = store._connection()
    try:
        con.execute("BEGIN")
        state, _, head = store._replay(con, scope_id)
        owner, att = state["owner_pin"], state["source_attestation"]
        if owner is None or att is None:
            raise DomainConflict("HOST_BATCH_PINNED_SOURCE_REQUIRED")
        pinned = verify_owner_inventory(
            raw, manifest, inventory_bytes,
            expected_inventory_sha256=expected_inventory_sha256)
        source = pinned.source
        if (pinned.attestation()!={k:v for k,v in owner.items() if k!="event_sha256"}
            or source.attestation()!={k:v for k,v in att.items() if k!="event_sha256"}):
            raise DomainConflict("HOST_BATCH_SOURCE_PIN_LEDGER_DRIFT")
        row = con.execute("SELECT * FROM events WHERE scope_id=? AND command_id=?",
                          (scope_id,run_id+"_seal")).fetchone()
        if row is None:
            raise InvalidInput("HOST_CHAT_REVISION_NOT_FOUND")
        event = json.loads(row["event_json"])
        marker = event.get("payload",{}).get("review",{})
        if (event.get("type")!="REVIEW_PROPOSED" or marker.get("schema")!=MARKER_SCHEMA
            or marker.get("source_sha256")!=source.source_sha256
            or "private_chat_revision" not in marker):
            raise InvalidInput("HOST_CHAT_REVISION_NOT_FOUND")
        record = marker["private_chat_revision"]
        if (type(record) is not dict or
            marker.get("private_chat_revision_sha256")!=json_digest(record)):
            raise LedgerCorrupted("HOST_CHAT_REVISION_RECORD_DIGEST_DRIFT")
        rebuilt = _compile_revision_record(source,record.get("inputs"))
        if rebuilt != record:
            raise LedgerCorrupted("HOST_CHAT_REVISION_REPLAY_DRIFT")
        result = rebuilt["result"]
        windows = [wid for wid,_,_ in source.primary_windows]
        sequence = row["sequence"]-2*len(windows)
        for wid in windows:
            for suffix,kind,field,expected in (
                ("model","MODEL_RECORDED","model",result["window_models"][wid]),
                ("proof","STRUCTURAL_PROOF_RECORDED","review",result["window_reviews"][wid])):
                entry = con.execute(
                    "SELECT * FROM events WHERE scope_id=? AND sequence=?",
                    (scope_id,sequence)).fetchone()
                if entry is None or entry["command_id"]!=run_id+"_"+suffix+"_"+wid:
                    raise LedgerCorrupted("HOST_CHAT_REVISION_MODEL_CHAIN_MISSING")
                body = json.loads(entry["event_json"])
                if (body["type"]!=kind or body["payload"].get("window_id")!=wid
                    or body["payload"].get(field)!=expected):
                    raise LedgerCorrupted("HOST_CHAT_REVISION_MODEL_CHAIN_DRIFT")
                sequence += 1
        con.execute("COMMIT")
        return {"schema":"IRE_V6_PRIVATE_CHAT_REVISION_READ_V1",
                "event_sha256":row["event_sha256"],"is_current":head==row["event_sha256"],
                "private_chat_revision_sha256":json_digest(record),
                "record":record,"research_complete":False,"p0_go":False}
    finally:
        con.close()


def _previous_typed_stage(con, scope_id, before_sequence):
    for row in con.execute("SELECT event_sha256,event_json FROM events WHERE scope_id=? AND sequence<? ORDER BY sequence DESC", (scope_id,before_sequence)):
        event=json.loads(row["event_json"])
        if event.get("type") != "REVIEW_PROPOSED":
            continue
        marker=event.get("payload",{}).get("review",{})
        if marker.get("schema") == MARKER_SCHEMA and "private_typed_staging_record" in marker:
            return row["event_sha256"], marker["private_typed_staging_record"]
    return None


def submit_host_atomic_batch(store, *, scope_id: str, run_id: str,
                             expected_head: str, raw: bytes, manifest: dict,
                             inventory_bytes: bytes,
                             expected_inventory_sha256: str,
                             exchange: dict, knowledge: dict,
                             window_models: dict, window_reviews: dict,
                             quarantine_preflight: dict | None = None,
                             chat_revision: dict | None = None,
                             typed_predecessor: str | None = None) -> dict:
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
            revision_record = None
            revision_pin = None
            if chat_revision is not None:
                revision_record = _compile_revision_record(source,chat_revision)
                compiled = revision_record["result"]
                if (compiled["exchange"]!=exchange or
                    compiled["window_models"]!=window_models or
                    compiled["window_reviews"]!=window_reviews):
                    raise InvalidInput("HOST_CHAT_REVISION_COMPILED_INPUT_MISMATCH")
                revision_pin = json_digest(revision_record)
            atom_audit=audit_host_atomic_exchange(source,exchange)
            prior_audit=audit_prior_candidates(source,exchange,knowledge)
            # The review frontier runs on this exact owner-pinned original
            # BEFORE any SQLite model/proof event can be committed. Only
            # bounded counts and digests enter the public-safe event marker.
            frontier=source_first_semantic_frontier(source,exchange)
            if (frontier["source_sha256"]!=source.source_sha256 or
                frontier["manifest_sha256"]!=source.manifest_sha256 or
                frontier["atom_candidate_digest"]!=atom_audit["atom_candidate_digest"] or
                frontier["cue_disposition_digest"]!=atom_audit["cue_disposition_digest"] or
                frontier["scoped_original_cues"]!=atom_audit["original_scoped_cues_enumerated"] or
                frontier["proposed_atomic_claims"]!=atom_audit["proposed_atomic_claims"] or
                frontier["review_case_count"]!=sum(frontier["review_cases_by_kind"].values()) or
                frontier["independent_review_performed"] is not False or
                frontier["p0_go"] is not False):
                raise LedgerCorrupted("HOST_BATCH_SEMANTIC_FRONTIER_INTEGRITY_DRIFT")
            frontier_pin={
                "schema":frontier["schema"],
                "original_source_sha256":source.source_sha256,
                "manifest_sha256":source.manifest_sha256,
                "review_case_census_sha256":frontier["review_case_census_sha256"],
                "review_case_count":frontier["review_case_count"],
                "review_cases_by_kind":frontier["review_cases_by_kind"],
                "human_semantic_review_pending":True,
                "independent_semantic_review_verified":False,
            }
            risk=audit_semantic_risks(source,exchange)
            if (risk["source_sha256"]!=source.source_sha256 or
                risk["manifest_sha256"]!=source.manifest_sha256 or
                risk["atom_candidate_digest"]!=atom_audit["atom_candidate_digest"] or
                risk["cue_disposition_digest"]!=atom_audit["cue_disposition_digest"] or
                risk["scoped_cue_count"]!=atom_audit["original_scoped_cues_enumerated"] or
                risk["model_claim_count"]!=atom_audit["proposed_atomic_claims"] or
                risk["review_case_count"]!=sum(risk["cases_by_reason"].values()) or
                risk["independent_human_review_complete"] is not False or
                risk["financial_law_as_of_verified"] is not False or
                risk["p0_go"] is not False):
                raise LedgerCorrupted("HOST_BATCH_SEMANTIC_RISK_AUDIT_DRIFT")
            risk_pin={
                "schema":risk["schema"],
                "original_source_sha256":source.source_sha256,
                "manifest_sha256":source.manifest_sha256,
                "case_census_sha256":risk["case_census_sha256"],
                "review_case_count":risk["review_case_count"],
                "cases_by_reason":risk["cases_by_reason"],
                "human_semantic_review_pending":True,
                "financial_law_as_of_verified":False,
                "semantic_entailment_independently_verified":False,
            }
            prequarantine_pin=audit_host_quarantine_preflight(
                source,exchange,quarantine_preflight)
            typed_staging_record = None
            if prequarantine_pin and prequarantine_pin["schema"] == TYPED_STAGING_RECEIPT:
                typed_staging_record = {"exchange": deepcopy(exchange),
                                        "ledger": deepcopy(quarantine_preflight)}
                json_digest(typed_staging_record)  # fail before writes if oversized
            # Receipt remains structural-only. Actual V123 must explicitly
            # quarantine every unresolved cue before any knowledge export.
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
                    type(model.get("claims")) is not list):
                    raise QualityNotProven("HOST_BATCH_WINDOW_MODEL_INVALID")
                if not model["claims"]:
                    # Zero-claim windows are legal only when the source-first
                    # exchange explicitly marks EVERY original cue NO_ATOM.
                    # UNRESOLVED/CANDIDATES in a blank window cannot silently
                    # pass as an empty model or shed a factual assertion.
                    window_cues={i for i in range(
                        source.scope_first_cue,source.scope_last_cue+1)
                        if source.owner(i)==wid}
                    rows=[r for r in exchange["cue_dispositions"]
                          if r["cue_index"] in window_cues]
                    if (not window_cues or len(rows)!=len(window_cues) or
                        any(r["disposition"]!="NO_ATOM" or r["claim_ids"]
                            for r in rows)):
                        raise QualityNotProven(
                            "HOST_BATCH_EMPTY_WINDOW_NOT_EXPLICITLY_NO_ATOM")
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
            commitment_fields={
                "base_head_sha256":expected_head,
                "source_sha256":source.source_sha256,
                "manifest_sha256":source.manifest_sha256,
                "atom_candidate_digest":atom_audit["atom_candidate_digest"],
                "cue_disposition_digest":atom_audit["cue_disposition_digest"],
                "source_first_semantic_frontier_pin":frontier_pin,
                "source_semantic_risk_pin":risk_pin,
                "prior_relation_digest":_digest_rows(knowledge["relations"]),
                "prior_master116_blob":prior_audit["master116_git_blob_sha1"],
                "prior_p4_22_blob":prior_audit["p4_prior22_git_blob_sha1"],
                "prior_p4_7_blob":prior_audit["p4_new7_git_blob_sha1"],
                "window_model_review_pins":pins,
            }
            if prequarantine_pin is not None:
                commitment_fields["host_source_prequarantine_pin"]=prequarantine_pin
            if revision_pin is not None:
                commitment_fields["private_chat_revision_sha256"]=revision_pin
            seal_id=run_id+"_seal"
            prior=con.execute(
                "SELECT * FROM events WHERE scope_id=? AND command_id=?",
                (scope_id,seal_id)).fetchone()
            # Use the actual earlier event in this same verified scope. For a
            # historical idempotent retry, inspect only the earlier prefix.
            # No new root or legacy host batch may overwrite a typed stage.
            limit = prior["sequence"] if prior is not None else seq + 1
            predecessor = _previous_typed_stage(con, scope_id, limit)
            successor_pin = None
            if predecessor is not None:
                previous_sha, previous_record = predecessor
                if (typed_staging_record is None or typed_predecessor != previous_sha
                        or expected_head != previous_sha):
                    raise InvalidInput("HOST_TYPED_SUCCESSOR_PREDECESSOR_REQUIRED")
                successor_pin = audit_typed_staging_successor(
                    source, previous_record, typed_staging_record, previous_sha)
                commitment_fields["typed_successor_pin"] = successor_pin
            elif typed_predecessor is not None:
                raise InvalidInput("HOST_TYPED_SUCCESSOR_PREDECESSOR_NOT_FOUND")
            commitment=json_digest(commitment_fields)
            if prior is not None:
                event=json.loads(prior["event_json"])
                review=event.get("payload",{}).get("review",{})
                if (event.get("type")!="REVIEW_PROPOSED" or
                    review.get("schema")!=MARKER_SCHEMA or
                    review.get("bundle_sha256")!=commitment or
                    review.get("original_expected_head")!=expected_head or
                    review.get("source_first_semantic_frontier_pin")!=frontier_pin or
                    review.get("source_semantic_risk_pin")!=risk_pin or
                    review.get("host_source_prequarantine_pin")!=prequarantine_pin or
                    review.get("private_typed_staging_record")!=typed_staging_record or
                    review.get("typed_successor_pin")!=successor_pin or
                    review.get("private_chat_revision_sha256")!=revision_pin or
                    review.get("private_chat_revision")!=revision_record or
                    review.get("semantic_truth_certified") is not False or
                    review.get("engine_quality_certified") is not False):
                    raise IdempotencyConflict("HOST_BATCH_RETRY_INPUT_CHANGED")
                receipt_fields={"schema":"IRE_V6_HOST_BATCH_RECEIPT_V1",
                        "scope_id":scope_id, "event_sha256":prior["event_sha256"],
                        "bundle_sha256":commitment,"idempotent_replay":True,
                        "is_current":head==prior["event_sha256"],
                        "atomic_batch_committed":True,
                        "source_and_proof_model_windows":len(windows),
                        "source_first_semantic_frontier_pin":frontier_pin,
                        "source_semantic_risk_pin":risk_pin,
                        "human_semantic_review_pending":True,
                        "semantic_truth_certified":False,
                        "independent_gold_recall_measured":False,
                        "research_complete":False,"p0_go":False}
                if prequarantine_pin is not None:
                    receipt_fields["host_source_prequarantine_pin"]=prequarantine_pin
                if revision_pin is not None:
                    receipt_fields["private_chat_revision_sha256"]=revision_pin
                if successor_pin is not None:
                    receipt_fields["typed_successor_pin"]=successor_pin
                return receipt_fields
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
                    "source_first_semantic_frontier_pin":frontier_pin,
                    "source_semantic_risk_pin":risk_pin,
                    "human_semantic_review_pending":True,
                    "semantic_truth_certified":False,
                    "engine_quality_certified":False}
            if prequarantine_pin is not None:
                marker["host_source_prequarantine_pin"]=prequarantine_pin
            if typed_staging_record is not None:
                marker["private_typed_staging_record"]=typed_staging_record
            if successor_pin is not None:
                marker["typed_successor_pin"]=successor_pin
            if revision_pin is not None:
                marker["private_chat_revision_sha256"]=revision_pin
                marker["private_chat_revision"]=revision_record
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
            receipt_fields={"schema":"IRE_V6_HOST_BATCH_RECEIPT_V1",
                    "scope_id":scope_id, "event_sha256":receipt["event_sha256"],
                    "bundle_sha256":commitment,"idempotent_replay":False,
                    "is_current":True,"atomic_batch_committed":True,
                    "source_and_proof_model_windows":len(windows),
                    "source_first_semantic_frontier_pin":frontier_pin,
                    "source_semantic_risk_pin":risk_pin,
                    "human_semantic_review_pending":True,
                    "semantic_truth_certified":False,
                    "independent_gold_recall_measured":False,
                    "research_complete":False,"p0_go":False}
            if prequarantine_pin is not None:
                receipt_fields["host_source_prequarantine_pin"]=prequarantine_pin
            if revision_pin is not None:
                receipt_fields["private_chat_revision_sha256"]=revision_pin
            if successor_pin is not None:
                receipt_fields["typed_successor_pin"]=successor_pin
            return receipt_fields
        return store._commit(con,work)
    finally:
        con.close()


def read_host_typed_staging(store, *, scope_id, run_id, raw, manifest,
                            inventory_bytes, expected_inventory_sha256):
    """Read a current private staging seal and replay typed/source custody.

    No approval transition is permitted. A stale seal is not a current input.
    """
    scope_id = require_identifier(scope_id, name="SCOPE_ID")
    run_id = require_identifier(run_id, IDENT, "HOST_RUN_ID")
    con = store._connection()
    try:
        con.execute("BEGIN")
        state, seq, head = store._replay(con, scope_id)
        pinned = verify_owner_inventory(raw, manifest, inventory_bytes,
                    expected_inventory_sha256=expected_inventory_sha256)
        source = pinned.source
        owner, att = state["owner_pin"], state["source_attestation"]
        if (owner is None or att is None or
            pinned.attestation() != {k:v for k,v in owner.items() if k!="event_sha256"} or
            source.attestation() != {k:v for k,v in att.items() if k!="event_sha256"}):
            raise DomainConflict("HOST_TYPED_STAGING_SOURCE_PIN_DRIFT")
        row = con.execute("SELECT * FROM events WHERE scope_id=? AND command_id=?",
                          (scope_id, run_id+"_seal")).fetchone()
        if row is None or row["event_sha256"] != head:
            raise DomainConflict("HOST_TYPED_STAGING_MISSING_OR_STALE")
        event = json.loads(row["event_json"])
        marker = event.get("payload", {}).get("review", {})
        record = marker.get("private_typed_staging_record")
        if (event.get("type") != "REVIEW_PROPOSED" or marker.get("schema") != MARKER_SCHEMA or
            type(record) is not dict or set(record) != {"exchange", "ledger"}):
            raise InvalidInput("HOST_TYPED_STAGING_RECORD_MISSING")
        receipt = audit_host_quarantine_preflight(source, record["exchange"], record["ledger"])
        if (not receipt or receipt["schema"] != TYPED_STAGING_RECEIPT or
            receipt != marker.get("host_source_prequarantine_pin")):
            raise LedgerCorrupted("HOST_TYPED_STAGING_RECEIPT_DRIFT")
        predecessor = _previous_typed_stage(con, scope_id, row["sequence"])
        if predecessor is not None:
            if audit_typed_staging_successor(source, predecessor[1], record,
                    predecessor[0]) != marker.get("typed_successor_pin"):
                raise LedgerCorrupted("HOST_TYPED_SUCCESSOR_PIN_DRIFT")
        elif "typed_successor_pin" in marker:
            raise LedgerCorrupted("HOST_TYPED_SUCCESSOR_PIN_WITHOUT_PREDECESSOR")
        # Bind the native projection to all current committed model revisions.
        indexed = {a["claim_id"]: a for a in record["exchange"]["atoms"]}
        seen = set()
        for wid, _, _ in source.primary_windows:
            entry = con.execute("SELECT event_json FROM events WHERE scope_id=? AND command_id=?",
                                (scope_id, run_id+"_model_"+wid)).fetchone()
            if entry is None:
                raise LedgerCorrupted("HOST_TYPED_STAGING_MODEL_MISSING")
            model_event = json.loads(entry["event_json"])
            model = model_event["payload"]["model"]
            if (model_event["type"] != "MODEL_RECORDED" or
                model_event["payload"]["window_id"] != wid or
                json_digest(model) != state["models"][wid]["model_sha256"]):
                raise LedgerCorrupted("HOST_TYPED_STAGING_MODEL_DRIFT")
            for claim in model["claims"]:
                cid = claim["claim_id"]
                atom = indexed.get(cid)
                if (cid in seen or atom is None or any(claim[k] != atom[k] for k in
                    ("claim_id", "owner_window_id", "proposition", "kind", "source_refs"))):
                    raise LedgerCorrupted("HOST_TYPED_STAGING_CLAIM_DRIFT")
                seen.add(cid)
        if seen != set(indexed):
            raise LedgerCorrupted("HOST_TYPED_STAGING_CLAIM_CENSUS")
        con.execute("COMMIT")
        return {"schema":"IRE_V6_PRIVATE_TYPED_STAGING_READ_V1", "event_sha256":head,
                "sequence":seq, "receipt":receipt, "record":record,
                "research_complete":False, "p0_go":False}
    finally:
        con.close()
