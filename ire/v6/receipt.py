"""V6-5 single-snapshot terminal *audit* (BLOCKED, never research GO).

The authoritative SQLite write transaction is held by TransactionStore. This
module reads only data visible at that transaction version, replays every
current proof against private bytes, and checks candidate metadata again.
Missing candidate replay inputs abort issuance; absent analysis is an explicit
BLOCKED reason. Audit issuance is NOT research closure or factual approval.
"""
from __future__ import annotations

import json
from .codec import json_digest
from .errors import DomainConflict, InvalidInput, LedgerCorrupted
from .trust import verify_owner_inventory
from .proof import audit_model_anchors
from .finance import audit_official_candidate, audit_prior_relation


def _payload(con, scope_id, event_sha256, kind):
    row=con.execute("SELECT event_json FROM events WHERE scope_id=? AND event_sha256=?",
                    (scope_id, event_sha256)).fetchone()
    if row is None:
        raise LedgerCorrupted("RECEIPT_DEPENDENCY_EVENT_MISSING")
    event=json.loads(row["event_json"])
    if event["type"]!=kind:
        raise LedgerCorrupted("RECEIPT_DEPENDENCY_KIND_MISMATCH")
    return event["payload"]


def audit_receipt_inputs(con, scope_id, state, *, raw, manifest, inventory_bytes,
                         expected_inventory_sha256, finance_inputs):
    if type(finance_inputs) is not dict:
        raise InvalidInput("AUDIT_FINANCE_INPUTS_INVALID")
    att=state["source_attestation"]
    owner=state["owner_pin"]
    if att is None or owner is None:
        raise DomainConflict("AUDIT_OWNER_PIN_AND_SOURCE_REQUIRED")
    anchored=verify_owner_inventory(raw,manifest,inventory_bytes,
                                     expected_inventory_sha256=expected_inventory_sha256)
    src=anchored.source
    if (anchored.attestation()!={k:v for k,v in owner.items() if k!="event_sha256"} or
        src.attestation()!={k:v for k,v in att.items() if k!="event_sha256"}):
        raise DomainConflict("AUDIT_PRIVATE_SOURCE_OR_OWNER_REPLAY_DRIFT")
    windows=[w for w,_,_ in src.primary_windows]
    models=state["models"]
    proofs=state["structural_proofs"]
    finance=state["finance_candidate_reviews"]
    missing_models=[w for w in windows if w not in models]
    missing_proofs=[]
    missing_finance=[]
    date_not_applicable=[]
    verified_proof=[]
    verified_finance=[]
    model_cache={}
    for wid in windows:
        current=models.get(wid)
        if not current:
            continue
        m=_payload(con,scope_id,current["revision_event_sha256"],"MODEL_RECORDED")["model"]
        model_cache[wid]=m
        proof=proofs.get(wid)
        if proof is None or proof["model_revision_event_sha256"]!=current["revision_event_sha256"]:
            missing_proofs.append(wid)
            continue
        p=_payload(con,scope_id,proof["proof_event_sha256"],"STRUCTURAL_PROOF_RECORDED")
        checked=audit_model_anchors(src,wid,m,p["review"])
        if checked!=p["audit"] or json_digest(checked)!=proof["audit_sha256"]:
            raise LedgerCorrupted("AUDIT_STRUCTURAL_PROOF_REPLAY_MISMATCH")
        verified_proof.append({"window_id":wid,"proof_event_sha256":proof["proof_event_sha256"]})
    current_finance=set()
    for key,item in sorted(finance.items()):
        wid,_,cid=key.partition(":")
        model=models.get(wid)
        if not model or item["model_revision_event_sha256"]!=model["revision_event_sha256"]:
            continue # Historical evidence is never current.
        current_finance.add(key)
        if wid not in model_cache or wid in missing_proofs:
            raise DomainConflict("AUDIT_CURRENT_FINANCE_WITHOUT_CURRENT_PROOF")
        supplied=finance_inputs.get(key)
        if type(supplied) is not dict or set(supplied)!={
            "official_document_raw","official_proposal","expected_official_sha256",
            "as_of","prior_baseline","prior_relation","expected_baseline_sha256"}:
            raise InvalidInput("AUDIT_CURRENT_FINANCE_REPLAY_INPUT_MISSING:"+key)
        official=audit_official_candidate(supplied["official_document_raw"],
                                supplied["official_proposal"],
                                expected_document_sha256=supplied["expected_official_sha256"],
                                as_of=supplied["as_of"])
        relation=audit_prior_relation(supplied["prior_baseline"],supplied["prior_relation"],
                              expected_baseline_sha256=supplied["expected_baseline_sha256"])
        prior=_payload(con,scope_id,item["finance_event_sha256"],"FINANCE_CANDIDATE_RECORDED")
        if (prior["official_audit"]!=official or prior["relation_audit"]!=relation or
            official["claim_id"]!=cid or relation["claim_id"]!=cid or
            prior["model_revision_event_sha256"]!=model["revision_event_sha256"]):
            raise DomainConflict("AUDIT_FINANCE_CANDIDATE_REPLAY_DRIFT")
        if official["effective_at_as_of"] is not True:
            date_not_applicable.append(key)
        verified_finance.append({"key":key,"finance_event_sha256":item["finance_event_sha256"]})
    if set(finance_inputs)!=current_finance:
        raise InvalidInput("AUDIT_FINANCE_INPUT_SCOPE_MISMATCH")
    for wid,m in model_cache.items():
        for c in m.get("claims",[]):
            if wid+":"+c.get("claim_id","") not in current_finance:
                missing_finance.append(wid+":"+c.get("claim_id", ""))
    measurement=state["blind_measurement"]
    current_revisions=json_digest([{"window_id":wid,
                             "revision_event_sha256":models[wid]["revision_event_sha256"]}
                             for wid in windows if wid in models])
    current_eval=(measurement is not None and
                  measurement["revision_set_sha256"]==current_revisions)
    if current_eval:
        from .evaluation import measure_blind
        plan=state["blind_plan"]
        if plan is None:
            raise LedgerCorrupted("AUDIT_MEASUREMENT_WITHOUT_FROZEN_PLAN")
        record=_payload(con,scope_id,measurement["event_sha256"],
                        "BLIND_MEASUREMENT_RECORDED")
        recalculated=measure_blind(raw,manifest,plan["plan"],
                                   record["gold"],record["predictions"],
                                   record["alignment"])
        if (recalculated!=record["metrics"] or
            json_digest(recalculated)!=measurement["metrics_sha256"]):
            raise LedgerCorrupted("AUDIT_BLIND_ARITHMETIC_REPLAY_MISMATCH")
    blockers=["OWNER_IDENTITY_NOT_INDEPENDENTLY_VERIFIED",
              "FINANCIAL_ENTAILMENT_NOT_VERIFIED","GOLD_REVIEWER_INDEPENDENCE_NOT_VERIFIED"]
    if missing_models:blockers.append("MODEL_WINDOWS_MISSING")
    if missing_proofs:blockers.append("STRUCTURAL_PROOFS_MISSING")
    if missing_finance:blockers.append("FINANCE_CANDIDATES_MISSING")
    if date_not_applicable:blockers.append("OFFICIAL_EVIDENCE_DATE_NOT_APPLICABLE")
    if not current_eval:blockers.append("INDEPENDENT_GOLDSET_MEASUREMENT_NOT_CURRENT")
    if len(verified_finance)!=len(current_finance):
        raise LedgerCorrupted("AUDIT_FINANCE_REPLAY_CENSUS_MISMATCH")
    return {"schema":"IRE_V6_TERMINAL_AUDIT_REPORT_V1",
            "source_sha256":src.source_sha256,"manifest_sha256":src.manifest_sha256,
            "inventory_sha256":anchored.inventory_sha256,"cue_census_sha256":src.cue_census_sha256,
            "scope_windows":len(windows),"models_current":len(model_cache),
            "proofs_replayed":len(verified_proof),"finance_candidates_replayed":len(verified_finance),
            "proof_set_sha256":json_digest(verified_proof),
            "finance_set_sha256":json_digest(verified_finance),
            "revision_set_sha256":current_revisions,
            "blind_measurement_current":bool(current_eval),
            "source_bytes_replayed_in_this_transaction":True,
            "independent_source_owner_authenticated":False,
            "official_fact_semantics_verified":False,
            "independent_gold_review_verified":False,
            "blockers":sorted(set(blockers)),
            "outcome":"TERMINAL_BLOCKED","research_complete":False,
            "engine_quality_certified":False,"p0_go":False}


def audit_input_digest(raw, manifest, inventory_bytes, expected_inventory_sha256,
                       finance_inputs):
    """Privacy-safe commitment to the *request*, for idempotent audit retries."""
    from .codec import sha256, require_hash
    if type(raw) is not bytes or type(inventory_bytes) is not bytes or \
       type(finance_inputs) is not dict:
        raise InvalidInput("AUDIT_COMMITMENT_INPUT_INVALID")
    require_hash(expected_inventory_sha256,"AUDIT_INVENTORY_PIN")
    commits=[]
    for key,item in sorted(finance_inputs.items()):
        if type(key) is not str or type(item) is not dict or set(item)!={
            "official_document_raw","official_proposal","expected_official_sha256",
            "as_of","prior_baseline","prior_relation","expected_baseline_sha256"} or \
           type(item["official_document_raw"]) is not bytes:
            raise InvalidInput("AUDIT_COMMITMENT_FINANCE_INPUT_INVALID")
        commits.append({"key":key,"official_bytes_sha256":sha256(item["official_document_raw"]),
            "proposal_sha256":json_digest(item["official_proposal"]),
            "expected_official_sha256":item["expected_official_sha256"],
            "as_of":item["as_of"],"prior_baseline_sha256":json_digest(item["prior_baseline"]),
            "prior_relation_sha256":json_digest(item["prior_relation"]),
            "expected_baseline_sha256":item["expected_baseline_sha256"]})
    return json_digest({"source_sha256":sha256(raw),"manifest_sha256":json_digest(manifest),
        "inventory_bytes_sha256":sha256(inventory_bytes),
        "expected_inventory_sha256":expected_inventory_sha256,"finance":commits})
