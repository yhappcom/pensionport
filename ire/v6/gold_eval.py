"""Source-first atomic gold evaluation, conservatively fail-closed on trust.

This component can measure *semantic atom* precision/recall against a complete,
independently attested, frozen two-reviewer gold ledger. It cannot create gold
truth or independently verify a human/ChatGPT reviewer's mental isolation.
No private SRT or gold claims are retained in public receipts.
"""
from __future__ import annotations

import base64
import json
import math
from datetime import datetime

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

from .codec import canonical, json_digest, sha256
from .errors import InvalidInput
from .source import parse_srt
from .numeric_provenance import audit_numeric_reference_boundaries
from .gold_traceability import verify_gold_cue_trace
from .assessment_plan import source_prediction_fields

MATCH_FIELDS = (
    "source_quote_and_entailment",
    "claim_kind",
    "speaker_and_stance",
    "negation_and_rebuttal",
    "conditions",
    "exceptions",
    "numeric_value_and_unit",
    "temporal_scope",
    "hypothetical_or_actual_scope",
)
CLAIM_KINDS = {"FACT", "OPINION", "QUESTION", "HYPOTHETICAL", "RECOMMENDATION", "CALCULATION", "MATH"}
CUE_REVIEW_STATUSES = {"REVIEWED_ATOM", "NO_ATOM", "OPEN_UNCERTAIN"}


def _invalid(reason):
    raise InvalidInput("P205_" + reason)


def _base_report(plan, source_sha, prediction_sha, cue_count, candidate_count, *, problem):
    return {
        "schema": "IRE_V6_P205_ATOMIC_GOLD_MEASUREMENT_V1",
        "original_source_sha256": source_sha,
        "original_prediction_sha256": prediction_sha,
        "planned_cue_count": cue_count,
        "frozen_prediction_atom_count": candidate_count,
        "assessment_scope": "ORIGINAL_SOURCE_FIRST_ATOMIC_CLAIM_NOT_CUE_LABELS",
        "status": problem,
        "independent_gold_verified": False,
        "blindness_host_attested": False,
        "independent_precision": None,
        "independent_recall": None,
        "independent_high_risk_false_negative_count": None,
        "diagnostic_precision": None,
        "diagnostic_recall": None,
        "diagnostic_high_risk_fn": None,
        "tp": None, "fp": None, "fn": None,
        "gold_atom_count": None,
        "source_cue_rows_reviewed_count": None,
        "attestation_signatures_verified":False,
        "thresholds_met_on_supplied_data":False,
        "e2_full_accuracy_pass": False,
        "e3_e4_e5_knowledge_approved": False,
        "personalized_advice_authorized": False,
        "ready_for_p0_2_06": False,
        "reason_not_a_truth_or_advice_certification":
            "Models and self-labelled cue coverage cannot certify atomic recall. "
            "A reviewer could still miss claims, role reversals or negations.",
    }


def _iso(value, name):
    if type(value) is not str:
        _invalid(name + "_ISO_REQUIRED")
    try:
        iso = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _invalid(name + "_ISO_INVALID")
    if iso.tzinfo is None:
        _invalid(name + "_UTC_OFFSET_REQUIRED")
    return iso


def _validate_provenance(plan, *, gold_sha, alignment_sha, provenance):
    """Independent reviewer and neutral host signed blind provenance.

    The trusted keys MUST have been pinned in the immutable preregistration
    before review. A self-submitted signature without preregistered keys does
    not establish blindness. The current ETF250 plan has no such keys.
    """
    trusted = plan.get("trusted_attestation_public_keys", {})
    if type(trusted) is not dict or set(trusted) != {"reviewer_one", "reviewer_two", "neutral_host"}:
        return False, "HOLD_NO_PREREGISTERED_INDEPENDENT_REVIEWER_TRUST_KEYS"
    if type(provenance) is not dict:
        return False, "HOLD_NO_AUTHENTICATED_BLINDNESS_PROVENANCE"
    if set(provenance) != {"schema", "plan_sha256", "gold_sha256", "alignment_sha256", "source_sha256",
                           "prediction_sha256", "review_session_ids", "gold_frozen_at", "aligned_at",
                           "gold_rater_disagreement_reconciled", "signatures"}:
        return False, "HOLD_BLIND_ATTESTATION_SCHEMA_INVALID"
    if provenance.get("schema") != "IRE_P205_BLIND_TRUST_ATTESTATION_V1":
        return False, "HOLD_UNKNOWN_BLIND_ATTESTATION_SCHEMA"
    session_ids=provenance.get("review_session_ids")
    if (type(session_ids) is not list or len(session_ids) != 2 or
        any(type(x) is not str or len(x) < 12 for x in session_ids) or
        len(set(session_ids)) != 2):
        return False, "HOLD_REVIEW_SESSION_ISOLATION_UNPROVEN"
    if provenance.get("gold_rater_disagreement_reconciled") is not True:
        return False, "HOLD_GOLD_DISAGREEMENT_UNRESOLVED"
    try:
        time_gold=_iso(provenance.get("gold_frozen_at"),"GOLD_LOCK")
        time_aligned=_iso(provenance.get("aligned_at"),"ALIGNMENT_LOCK")
    except InvalidInput:
        return False, "HOLD_GOLD_ALIGNMENT_FREEZE_TIME_INVALID"
    if time_gold >= time_aligned:
        return False, "HOLD_GOLD_NOT_LOCKED_BEFORE_ALIGNMENT"
    if provenance.get("gold_sha256") != gold_sha or provenance.get("alignment_sha256") != alignment_sha:
        return False, "HOLD_GOLD_OR_ALIGNMENT_DIGEST_NOT_LOCKED"
    if provenance.get("plan_sha256") != json_digest({k:v for k,v in plan.items() if k != "plan_runtime"}):
        return False, "HOLD_PREREGISTRATION_PLAN_CHANGED"
    if provenance.get("source_sha256") != plan["source"]["original_srt_sha256"]:
        return False, "HOLD_REVIEW_SOURCE_CHANGED"
    if provenance.get("prediction_sha256") != source_prediction_fields(plan)[2]:
        return False, "HOLD_PREDICTION_CHANGED"
    if type(provenance.get("signatures")) is not dict or set(provenance["signatures"]) != set(trusted):
        return False, "HOLD_INDEPENDENT_SIGNED_PROVENANCE_MISSING"
    body={k:v for k,v in provenance.items() if k!="signatures"}
    raw=canonical(body)
    try:
        for role in ("reviewer_one", "reviewer_two", "neutral_host"):
            pub=base64.b64decode(trusted[role], validate=True)
            sig=base64.b64decode(provenance["signatures"][role], validate=True)
            if len(pub)!=32 or len(sig)!=64:
                return False, "HOLD_UNTRUSTED_REVIEWER_KEY_LENGTH"
            Ed25519PublicKey.from_public_bytes(pub).verify(sig,raw)
        if len({trusted[k] for k in trusted}) != 3:
            return False, "HOLD_DUPLICATE_REVIEWER_OR_HOST_KEY"
    except (ValueError,TypeError,InvalidSignature):
        return False, "HOLD_REVIEWER_OR_HOST_SIGNATURE_INVALID"
    return True, "BLIND_REVIEWERS_AND_HOST_SIGNATURES_PASS"


def evaluate_atomic_gold(plan, original_srt: bytes, frozen_native: bytes,
                         *, gold=None, alignment=None, provenance=None):
    """Compute TP/FP/FN only on a fully enumerated, pairwise atom ledger.

    Any missing gold, ambiguous cue or unsigned reviewer makes the certified
    metrics **None** even when provisional diagnostic arithmetic is available.
    """
    expected_source,expected_cues,expected_prediction,expected_atoms=source_prediction_fields(plan)
    if type(original_srt) is not bytes or type(frozen_native) is not bytes:
        _invalid("SOURCE_AND_NATIVE_ORIGINAL_BYTES_REQUIRED")
    source_sha=sha256(original_srt)
    native_sha=sha256(frozen_native)
    if source_sha != expected_source:
        _invalid("SOURCE_SHA_DRIFT")
    if native_sha != expected_prediction:
        _invalid("PREDICTION_SHA_DRIFT")
    cue_rows=parse_srt(original_srt)
    if len(cue_rows) != expected_cues:
        _invalid("CUE_250_SOURCE_CENSUS_DRIFT")
    try:
        native=json.loads(frozen_native)
    except (ValueError,UnicodeDecodeError) as exc:
        raise InvalidInput("P205_PREDICTION_JSON_INVALID") from exc
    if type(native) is not dict or type(native.get("atoms")) is not list:
        _invalid("ORIGINAL_NATIVE_ATOMS_ABSENT")
    candidates=native["atoms"]
    if len(candidates) != expected_atoms:
        _invalid("PREDICTION_ATOM_CENSUS_DRIFT")
    pred={}
    for claim in candidates:
        if type(claim) is not dict or type(claim.get("claim_id")) is not str or claim["claim_id"] in pred:
            _invalid("NATIVE_DUPLICATE_OR_BAD_CLAIM")
        pred[claim["claim_id"]]=claim
        for ref in claim.get("source_refs", []):
            if not _original_quote_valid(cue_rows,ref):
                _invalid("NATIVE_PREDICTION_QUOTE_NOT_FROM_SOURCE")
    report=_base_report(plan,source_sha,native_sha,len(cue_rows),len(pred),
                        problem="HOLD_NO_INDEPENDENT_ATOMIC_GOLD")
    numeric_flags=audit_numeric_reference_boundaries(cue_rows,candidates)
    report["prediction_numeric_source_boundary_warnings"]=len(numeric_flags)
    report["prediction_numeric_source_boundary_affected_atoms"]=len(
        {flag["claim_id"] for flag in numeric_flags})
    report["prediction_numeric_source_provenance_complete"]=(len(numeric_flags)==0)
    # These are structural provenance warnings, not independent semantic gold.
    # Never convert an audit warning into an FP/FN count automatically.
    if gold is None or alignment is None:
        return report
    if type(gold) is not dict or gold.get("schema") != "IRE_P205_PRIVATE_GOLD_ATOMIC_REVIEW_V1":
        _invalid("GOLD_SCHEMA_INVALID")
    if gold.get("source_srt_sha256")!=source_sha:
        _invalid("GOLD_SOURCE_VERSION_DRIFT")
    goldcue=gold.get("reviewed_cues",[])
    if type(goldcue) is not list or len(goldcue) != len(cue_rows):
        return {**report,"status":"HOLD_INCOMPLETE_GOLD_CUE_CENSUS"}
    atoms=gold.get("atomic_gold_claims")
    if type(atoms) is not list or len(atoms)==0:
        return {**report,"status":"HOLD_GOLD_ATOMIC_CLAIMS_NOT_PROVIDED"}
    goldids={}
    for a in atoms:
        if type(a) is not dict or type(a.get("gold_id")) is not str or a["gold_id"] in goldids:
            _invalid("GOLD_DUPLICATE_ATOMIC_ID")
        if a.get("kind") not in CLAIM_KINDS or a.get("risk") not in {"HIGH","NORMAL"}:
            _invalid("GOLD_KIND_OR_RISK_INVALID")
        if type(a.get("source_refs")) is not list or not a["source_refs"]:
            _invalid("GOLD_ATOM_MUST_HAVE_SOURCE_REFERENCES")
        if any(not _original_quote_valid(cue_rows,ref) for ref in a["source_refs"]):
            _invalid("GOLD_SOURCE_QUOTE_NOT_VERBATIM")
        for key in ("proposition", "speaker_stance", "as_of", "high_risk_reason"):
            if not isinstance(a.get(key),str) or not a[key].strip():
                _invalid("GOLD_ATOM_MISSING_"+key.upper())
        for field in ("conditions", "exceptions", "numeric_evidence"):
            if type(a.get(field)) is not list:
                _invalid("GOLD_"+field.upper()+"_MUST_BE_LIST")
        goldids[a["gold_id"]]=a
    for i,row in enumerate(goldcue,1):
        if (type(row) is not dict or row.get("cue_index")!=i or
            row.get("source_quote_sha256")!=sha256(cue_rows[i-1].text.encode("utf8"))):
            _invalid("GOLD_CUE_ORDER_OR_HASH_CHANGED")
        if row.get("status") not in CUE_REVIEW_STATUSES or not isinstance(row.get("reason"),str) or not row["reason"].strip():
            _invalid("GOLD_CUE_DISPOSITION_WITHOUT_REASON")
    trace = verify_gold_cue_trace(cue_rows, gold)
    report["gold_traceability"] = trace
    if any(x["status"]=="OPEN_UNCERTAIN" for x in goldcue):
        return {**report,"status":"HOLD_UNRESOLVED_BLIND_GOLD_CUES",
                "gold_atom_count":len(goldids)}
    if alignment.get("schema")!="IRE_P205_ATOMIC_ALIGNMENT_V1" or type(alignment.get("pairs")) is not list:
        _invalid("ALIGNMENT_SCHEMA_INVALID")
    exact_g=set();exact_p=set();seen_g=set();seen_p=set()
    for pair in alignment["pairs"]:
        if type(pair) is not dict or set(pair)!={"gold_id","claim_id","match_dimensions"}:
            _invalid("ALIGNMENT_PAIR_SHAPE_INVALID")
        gid=pair["gold_id"];pid=pair["claim_id"]
        if gid not in goldids or pid not in pred:
            _invalid("ALIGNMENT_UNKNOWN_ATOM_ID")
        if gid in seen_g or pid in seen_p:
            _invalid("ALIGNMENT_DUPLICATE_SOURCE_OR_TARGET")
        seen_g.add(gid);seen_p.add(pid)
        dimensions=pair["match_dimensions"]
        if type(dimensions) is not dict or set(dimensions)!=set(MATCH_FIELDS) or any(type(v) is not bool for v in dimensions.values()):
            _invalid("ALIGNMENT_SEMANTIC_DIMENSIONS_INCOMPLETE")
        overlap=({x["cue_index"] for x in goldids[gid]["source_refs"]}
                 & {x["cue_index"] for x in pred[pid].get("source_refs",[])})
        exact=(all(dimensions.values()) and bool(overlap)
               and goldids[gid]["kind"]==pred[pid].get("kind"))
        if exact:
            exact_g.add(gid);exact_p.add(pid)
    if (type(alignment.get("unmatched_gold_ids")) is not list or
        set(alignment["unmatched_gold_ids"])!=set(goldids)-seen_g or
        type(alignment.get("unmatched_prediction_ids")) is not list or
        set(alignment["unmatched_prediction_ids"])!=set(pred)-seen_p or
        len(alignment["unmatched_gold_ids"])!=len(set(alignment["unmatched_gold_ids"])) or
        len(alignment["unmatched_prediction_ids"])!=len(set(alignment["unmatched_prediction_ids"]))):
        _invalid("ALIGNMENT_INCOMPLETE_OR_HIDDEN_UNMATCHED_ATOMS")
    tp=len(exact_g);fp=len(pred)-tp;fn=len(goldids)-tp
    highrisk_fn=sum(a["risk"]=="HIGH" and gid not in exact_g for gid,a in goldids.items())
    precision=tp/len(pred) if pred else None
    recall=tp/len(goldids)
    report.update({"tp":tp,"fp":fp,"fn":fn,
                   "gold_atom_count":len(goldids),
                   "diagnostic_precision":precision,
                   "diagnostic_recall":recall,
                   "diagnostic_high_risk_fn":highrisk_fn,
                   "source_cue_rows_reviewed_count":len(goldcue)})
    verified, message = _validate_provenance(plan,gold_sha=json_digest(gold),
                          alignment_sha=json_digest(alignment),provenance=provenance)
    if not verified:
        report["status"]=message
        return report
    # Even a valid signature means a trusted attestor asserted independence,
    # not that textual adjudications automatically become financial truth.
    report["attestation_signatures_verified"]=True
    report["blindness_host_attested"]=True
    # A data-supplied plan may use synthetic/generated keys. It is not itself
    # the repository's preregistered production trust anchor. The P205 public
    # checklist must independently accept the pinned real-source proof before
    # the following production-facing fields can ever be populated.
    production_gold_certified = False
    report["independent_gold_verified"] = production_gold_certified
    report["independent_precision"] = None
    report["independent_recall"] = None
    report["independent_high_risk_false_negative_count"] = None
    thresholds=plan["assessment"]["thresholds"]
    # Exact rational threshold arithmetic avoids floats in canonical signed JSON.
    if (type(thresholds.get("atomic_precision_min_bp")) is not int
            or type(thresholds.get("atomic_recall_min_bp")) is not int
            or type(thresholds.get("high_risk_false_negative_max")) is not int
            or not 0 <= thresholds["atomic_precision_min_bp"] <= 10000
            or not 0 <= thresholds["atomic_recall_min_bp"] <= 10000):
        _invalid("PREREGISTERED_INTEGER_THRESHOLD_CONTRACT_INVALID")
    met=(tp*10000 >= thresholds["atomic_precision_min_bp"]*len(pred)
         and tp*10000 >= thresholds["atomic_recall_min_bp"]*len(goldids)
         and highrisk_fn<=thresholds["high_risk_false_negative_max"])
    report["status"]=("HOLD_ATTESTED_DIAGNOSTIC_THRESHOLDS_MET_PRODUCTION_GOLD_UNVERIFIED"
                       if met else "HOLD_ATTESTED_DIAGNOSTIC_THRESHOLDS_MISSED")
    # E2 entire video/applicability, E3, E4, E5 remain distinct approvals.
    report["thresholds_met_on_supplied_data"]=bool(met)
    report["ready_for_p0_2_06"]=False
    return report


def _original_quote_valid(cues, ref):
    if type(ref) is not dict:
        return False
    idx=ref.get("cue_index");quote=ref.get("quote")
    if type(idx) is not int or not (1<=idx<=len(cues)) or not isinstance(quote,str):
        return False
    return bool(quote.strip()) and " ".join(quote.split()).casefold() in " ".join(cues[idx-1].text.split()).casefold()
