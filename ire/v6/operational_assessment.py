"""Owner-approved operational E2 policy; distinct from independent L4 certification.

This scores a frozen first-turn prediction against a second-turn internal
reference. It does not create financial truth or approve any research output.
"""
from __future__ import annotations
import json
from .assessment_plan import validate_campaign,timestamp,EXPOSED_SOURCE_SHA256,EXPOSED_VIDEO_IDS
from .atomic_exchange import audit_host_atomic_exchange
from .codec import json_digest,sha256,require_hash
from .errors import InvalidInput
from .gold_eval import evaluate_atomic_gold
from .source import verify_source
from .trust import verify_owner_inventory

POLICY_ID="IRE_P205_OPERATIONAL_V1_20261124"
DOMAINS=frozenset(("ETF","PENSION","ASSET_ALLOCATION"))


def _need(condition,code):
    if not condition:
        raise InvalidInput("OPERATIONAL_"+code)


def _reason(value):
    return type(value) is str and len(value.strip())>=8


def _hash(value):
    return require_hash(value,"OPERATIONAL_EVIDENCE_SHA")


def evaluate_operational_trial(plan, original, prediction, *, manifest, inventory_bytes,
                               expected_inventory_sha256, reference, alignment, review):
    """Full source and 1:1 internal-reference replay; not an independence claim.

    The review's user references, times and notes are manual chat records,
    not host-authenticated. Public closeout separately binds a preregistered
    cohort, actual private replay and CI evidence. No supplied metrics accepted.
    """
    validate_campaign(plan)
    _need(plan["purpose"]=="HOLDOUT","FRESH_SOURCE_REQUIRED")
    _need(plan["source"]["video_id"] not in EXPOSED_VIDEO_IDS and
          plan["source"]["original_srt_sha256"] not in EXPOSED_SOURCE_SHA256,
          "EXPOSED_SOURCE")
    fields={"schema","policy_id","cohort_sha256","domain","selection_sha256",
            "turn1_user_ref","turn2_user_ref","prediction_frozen_at","turn2_at",
            "reference_frozen_at","aligned_at","reference_sha256","alignment_sha256",
            "alignment_reasons","unmatched_reasons","high_risk_reviews"}
    _need(type(review) is dict and set(review)==fields and
          review["schema"]=="IRE_P205_INTERNAL_TWO_TURN_REVIEW_V1" and
          review["policy_id"]==POLICY_ID and review["domain"] in DOMAINS,
          "REVIEW_SCHEMA")
    for k in ("cohort_sha256","selection_sha256","reference_sha256","alignment_sha256"):
        _hash(review[k])
    a,b=review["turn1_user_ref"],review["turn2_user_ref"]
    _need(_reason(a) and _reason(b) and a!=b,"DISTINCT_USER_TURNS")
    _need(timestamp(plan["registered_at"])<=timestamp(review["prediction_frozen_at"])<
          timestamp(review["turn2_at"])<=timestamp(review["reference_frozen_at"])<
          timestamp(review["aligned_at"]),"FREEZE_ORDER")
    _need(review["reference_sha256"]==json_digest(reference) and
          review["alignment_sha256"]==json_digest(alignment),"REFERENCE_ALIGNMENT_DRIFT")
    pinned=verify_owner_inventory(original,manifest,inventory_bytes,
                    expected_inventory_sha256=expected_inventory_sha256)
    source=pinned.source
    _need(source.video_id==plan["source"]["video_id"] and
          source.source_sha256==plan["source"]["original_srt_sha256"] and
          source.scope_first_cue==1 and source.scope_last_cue==len(source.cues),
          "FULL_SOURCE_IDENTITY")
    try:
        native=json.loads(prediction)
    except (ValueError,TypeError,UnicodeError) as exc:
        raise InvalidInput("OPERATIONAL_PREDICTION_JSON") from exc
    audit=audit_host_atomic_exchange(source,native)
    diagnostic=evaluate_atomic_gold(plan,original,prediction,gold=reference,alignment=alignment)
    tp,fp,fn=(diagnostic[k] for k in ("tp","fp","fn"))
    _need(all(type(x) is int for x in (tp,fp,fn)),"INCOMPLETE_INTERNAL_REFERENCE")
    _need(diagnostic["source_cue_rows_reviewed_count"]==len(source.cues),
          "REFERENCE_CUE_CENSUS")
    pairs=alignment["pairs"]
    expected_pair_keys={x["gold_id"]+":"+x["claim_id"] for x in pairs}
    reasons=review["alignment_reasons"]
    _need(type(reasons) is dict and set(reasons)==expected_pair_keys and
          all(_reason(x) for x in reasons.values()),"PAIR_REASONS_INCOMPLETE")
    unmatched=review["unmatched_reasons"]
    expected_unmatched={"reference:"+x for x in alignment["unmatched_gold_ids"]}|{
                        "prediction:"+x for x in alignment["unmatched_prediction_ids"]}
    _need(type(unmatched) is dict and set(unmatched)==expected_unmatched and
          all(_reason(x) for x in unmatched.values()),"UNMATCHED_REASONS_INCOMPLETE")
    high_ids={x["gold_id"] for x in reference["atomic_gold_claims"] if x["risk"]=="HIGH"}
    risk=review["high_risk_reviews"]
    _need(bool(high_ids) and type(risk) is dict and set(risk)==high_ids,
          "NONVACUOUS_HIGH_RISK_CENSUS")
    for row in risk.values():
        _need(type(row) is dict and set(row)=={"disposition","reason","evidence_sha256"} and
              row["disposition"] in ("OFFICIAL_SOURCE_REVIEW_PENDING_E4","QUARANTINE_PENDING_E3")
              and _reason(row["reason"]),"HIGH_RISK_DISPOSITION")
        _hash(row["evidence_sha256"])
    high=diagnostic["diagnostic_high_risk_fn"]
    numeric=diagnostic["prediction_numeric_source_boundary_warnings"]
    # An exact pair is a ChatGPT judgment, not mechanically proven equivalence.
    # Numeric/condition/exception mismatches are critical even if low risk.
    critical=sum(not all(p["match_dimensions"][k] for k in
                      p["match_dimensions"] if k in ("numbers_units","conditions","exceptions",
                      "numeric_evidence","numeric_scope","numeric_unit","numeric_values",
                      "condition_scope","exception_scope")) for p in pairs)
    # All non-exact pairs still count as FP and FN in the common evaluator.
    met=bool(tp+fp and tp+fn and tp*10000>=9500*(tp+fp) and
             tp*10000>=9800*(tp+fn) and high==0 and numeric==0 and critical==0)
    return {"schema":"IRE_P205_INTERNAL_OPERATIONAL_TRIAL_V1","policy_id":POLICY_ID,
            "campaign_id":plan["campaign_id"],"engine_commit_sha":plan["engine_commit_sha"],
            "domain":review["domain"],"cohort_sha256":review["cohort_sha256"],
            "selection_sha256":review["selection_sha256"],"plan_sha256":json_digest(plan),
            "source_sha256":source.source_sha256,"video_id":source.video_id,
            "prediction_sha256":sha256(prediction),"reference_sha256":json_digest(reference),
            "alignment_sha256":json_digest(alignment),"review_sha256":json_digest(review),
            "source_cues":len(source.cues),"reviewed_cues":diagnostic["source_cue_rows_reviewed_count"],
            "prediction_atoms":tp+fp,"reference_atoms":tp+fn,"tp":tp,"fp":fp,"fn":fn,
            "high_risk_reference_atoms":len(high_ids),"high_risk_fn":high,
            "numeric_boundary_warnings":numeric,"critical_pair_mismatches":critical,
            "first_turn_unresolved_cues":audit["unresolved_cues"],
            "internal_thresholds_met":met,"evidence_level":"L2",
            "independent_gold_verified":False,"independent_precision":None,
            "independent_recall":None,"independent_high_risk_fn":None,
            "host_turn_authentication_verified":False,"research_publication_authorized":False,
            "personalized_advice_authorized":False,
            "status":"INTERNAL_TRIAL_THRESHOLDS_MET" if met else "HOLD"}
