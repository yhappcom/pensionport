#!/usr/bin/env python3
"""V3.0 integrated research prototype: deterministic and adversarial checks.

Includes development-only #19/#20 historic source records, never video #21+.
This test proves structured fail-closed behavior, not independent fact truth.
"""
import argparse
import copy
import json
from decimal import Decimal
from pathlib import Path

from v30_integrated_research import (
    ROOT, valid_approved_source, check_historical_registry,
    load_development_video, plan_unverified_video, obligatory_evidence,
    compare_explicit_frames, finance_model, validate_frame, risk_for_status,
    require,
)

def must_reject(fn, reason):
    try:fn()
    except (ValueError,TypeError,KeyError):
        return
    raise ValueError("ADVERSARIAL_INPUT_WAS_ACCEPTED: "+reason)

def frame(role,action="WITHDRAW",value=None,conditions=None):
    out={
        "subject_type":"PENSION_ACCOUNT",
        "subject_id":"EXAMPLE_PRIVATE_ACCOUNT",
        "action":action,
        "object_type":"TAX_OR_FINANCIAL_CONDITION",
        "object_id":"EXAMPLE_AMOUNT",
        "financial_role":role,
        "jurisdiction":"KR",
        "effective_date":"2026-01-01",
        "conditions":conditions if conditions is not None else {
           "source_of_funds":"PRIVATE_AFTER_TAX_PENSION",
           "tax_event":"ANNUAL_PAYOUT",
        },
        "units":"KRW",
    }
    if value is not None:out["value"]=value
    return out

def item(id,form,status="QUALIFIED"):
    return {"claim_id":id,"frame":form,"legacy_verdict":status}

def self_test(root):
    config,protocol=valid_approved_source(root)
    baseline=check_historical_registry(root)
    require(baseline=={
        "historical_claims":4120,"historical_videos":253,
        "topic_families":39,"historical_71_public_proxy_id_count":13,
        "source_verdict_reconciliation_overlays":1,
        "original_claims_modified":0,"meaning_automatically_approved":False,
    },"LEGACY_KNOWLEDGE_CENSUS_DIFFERED")
    result={}
    for n,expected in ((19,12),(20,6)):
        v=load_development_video(root,n)
        w=plan_unverified_video(root,n)
        require(v["number"]==w["video_number"]==n
                and w["source_claim_count"]==expected
                and w["blocked_claim_count"]==expected
                and w["research_status"]=="RESEARCH_BLOCKED"
                and not w["full_atomic_coverage_complete"]
                and w["real_research_complete_certificates"]==0
                and w["authorized_knowledge_merges"]==0
                and w["material_claim_count_confirmed_by_full_srt"] is None
                and all(x["source_cue_range"] is None
                        and x["research_status"]=="BLOCKED"
                        and x["frame_status"]=="MISSING_STRUCTURED_FRAME"
                        and not x["full_material_atomic_coverage_revalidated"]
                        and not x["primary_source_actual_text_read_this_run"]
                        and not x["quant_arithmetic_checked_this_run"]
                        and not x["empirical_reproduced_this_run"]
                        for x in w["claim_worklist"]),
                "HISTORICAL_MATERIAL_CLAIMS_FALSELY_CERTIFIED_OR_OVERLOOKED")
        result[n]={"historical_claims_read":expected,
                   "blocked_claims":w["blocked_claim_count"],
                   "original_cues_not_independently_reviewed_this_run":
                       w["historical_srt_cues"]}
    n19=plan_unverified_video(root,19)
    require({x["claim_id"] for x in n19["claim_worklist"]
             if x["source_risk"]=="CORRECTION_ONLY"}==
            {"zi9x_q2fYoc-12"},
            "NEW_V19_CONTRADICTED_CLAIM_PROMOTED")
    n20=plan_unverified_video(root,20)
    require(not any(x["source_risk"]=="CORRECTION_ONLY"
                    for x in n20["claim_worklist"]),
            "FALSE_20_CONTRADICTION")
    for unsupported in (0,1,18,21,22,791,999,"19",True,-1):
        must_reject(lambda x=unsupported:load_development_video(root,x),
                    "must not open a new video or spoof the roster")
    for bad in ("TRUE","PROVEN",None,"",[]):
        must_reject(lambda x=bad:risk_for_status(x,"QUALIFIED"),
                    "legacy source verdict spoof")
    require(risk_for_status("CONTRADICTED","QUALIFIED")=="CORRECTION_ONLY"
            and risk_for_status("HYPOTHETICAL","QUALIFIED")=="UNREPLICATED_HYPOTHETICAL"
            and risk_for_status("PRIMARY_CONFIRMED","QUALIFIED")=="HUMAN_REVIEW_ONLY",
            "HISTORICAL_SOURCE_SAFETY_POLICY")
    require("CLAIM_CLASSIFICATION_REQUIRED" in obligatory_evidence("UNCLASSIFIED")
            and "REAL_WORLD_EMPIRICAL_REQUIRED" in
                obligatory_evidence("STRATEGY_OR_PERFORMANCE"),
            "MATERIAL_EMPIRICAL_OR_UNCLASSIFIED_RESEARCH_WAIVER")
    must_reject(lambda:obligatory_evidence("STRATEGY_NON_EMPIRICAL"),
                "strategy evidence bypass")

    a=item("DEMO0000001-01",frame("PENSION_INCOME_PAYOUT_TAX",value="15000000"))
    a2=item("DEMO0000001-02",frame("PENSION_INCOME_PAYOUT_TAX",value="15000000"))
    ab=item("DEMO0000001-03",frame("PENSION_INCOME_PAYOUT_TAX",value="18000000"))
    diff_role=item("DEMO0000002-01",frame("PENSION_CONTRIBUTION_LIMIT",
                                      action="DEPOSIT",value="18000000"))
    diff_rule=item("DEMO0000002-02",frame("PENSION_INCOME_PAYOUT_TAX",
                                      conditions={"tax_event":"DEFERRED_EARLY_PAYOUT"}))
    diff_time=item("DEMO0000002-03",frame("PENSION_INCOME_PAYOUT_TAX"))
    diff_time["frame"]["effective_date"]="2024-01-01"
    unknown=item("DEMO0000002-04",frame("PENSION_INCOME_PAYOUT_TAX"))
    unknown["frame"]["effective_date"]="UNKNOWN"
    family=item("DEMO0000002-05",frame("ISA_TRANSFER_TAX_CREDIT"))
    family2=item("DEMO0000002-06",frame("PENSION_CONTRIBUTION_TAX_CREDIT"))
    errors=item("DEMO0000002-07",frame("PENSION_INCOME_PAYOUT_TAX"),"CONTRADICTED")
    diverse={"same":(a,a2,"SAME_PROPOSITION_CANDIDATE"),
             "tax_rule_vs_deposit":(a,diff_role,"SCOPE_DIFFERENT"),
             "same_scope_different_numeric":(a,ab,"CONTRADICTION_REVIEW"),
             "tax_condition_exception":(a,diff_rule,"QUALIFIES_SCOPE_CANDIDATE"),
             "older_effective_date":(a,diff_time,"QUALIFIES_SCOPE_CANDIDATE"),
             "unknown_effective_date":(a,unknown,"UNRESOLVED_AMBIGUOUS"),
             "related_financial_roles":(family,family2,"QUALIFIES_SCOPE_CANDIDATE"),
             "refuted_not_positive":(a,errors,"SAME_PROPOSITION_CANDIDATE")}
    for title,(left,right,expected_relation) in diverse.items():
        r=compare_explicit_frames(left,right)
        rev=compare_explicit_frames(right,left)
        require(r["relationship_candidate"]==expected_relation
                and r["relationship_candidate"]==rev["relationship_candidate"]
                and r["source_risk"]==rev["source_risk"]
                and r["claimed_semantic_truth"] is None
                and not r["automatically_approved"]
                and not r["automatic_knowledge_merge_permitted"]
                and not r["research_completion_certificate_permitted"]
                and not r["investment_trade_instruction_permitted"]
                and r["review_only"] is True,
                "FALSE_SEMANTIC_TRUTH_INFERENCE_OR_SCOPE_ERROR_"+title)
        if title=="refuted_not_positive":
            require(r["source_risk"]=="CORRECTION_ONLY",
                    "CONTRADICTED_PROMOTED_AS_POSITIVE")
    for invalid in (
        {}, {"effective_date":None},
        {"conditions":None},
        {"financial_role":"AUTO_INFERRED"},
        {"jurisdiction":""},
        {"subject_id":None},
    ):
        broken=frame("PENSION_INCOME_PAYOUT_TAX")
        broken.update(invalid)
        if invalid:
            must_reject(lambda x=broken:validate_frame(x),
                        "frame must require typed auditable source")
    must_reject(lambda:compare_explicit_frames(a,a),
                "self-pair must not be scored")
    must_reject(lambda:compare_explicit_frames(
        item("DEMO0000001-02",frame("PENSION_INCOME_PAYOUT_TAX"),"TRUE"),a),
        "no fake verified status")
    must_reject(lambda:compare_explicit_frames(
        item("DEMO0000001-03",{}),a),
        "no missing financial role")
    must_reject(lambda:compare_explicit_frames(
        item("DEMO0000001-03",frame("PENSION_INCOME_PAYOUT_TAX",
            conditions=[])),a),
        "no non-dict typed conditions")

    # Historic #19 mathematical red flag tested as *assumption-bound arithmetic*.
    fv=finance_model("MONTHLY_SAVINGS_FUTURE_VALUE",
                     "600000","0.04",300)
    payout=finance_model("MONTHLY_AMORTIZING_PAYOUT",
                         "308470000","0.04",360)
    require(abs(Decimal(fv["amount"])-Decimal("308477728"))<Decimal("5")
            and abs(Decimal(payout["amount"])-Decimal("1472683"))<Decimal("5")
            and Decimal(payout["amount"])<Decimal("2130000")
            and not payout["contractual_rate_or_payout_verified"]
            and not payout["independent_source_and_economic_assumptions_approved"],
            "ASSUMPTION_BOUND_PENSION_FV_ANNUITY_CALCULATION")
    zero=finance_model("MONTHLY_AMORTIZING_PAYOUT","12000","0",12)
    zerofv=finance_model("MONTHLY_SAVINGS_FUTURE_VALUE","1000","0",12)
    require(zero["amount"]=="1000.00" and zerofv["amount"]=="12000.00",
            "ZERO_INTEREST_LIMIT_CASE")
    for args in (
        ("MONTHLY_SAVINGS_FUTURE_VALUE",-1,0.04,12),
        ("MONTHLY_SAVINGS_FUTURE_VALUE","nan",0.04,12),
        ("MONTHLY_SAVINGS_FUTURE_VALUE","100","3",12),
        ("MONTHLY_SAVINGS_FUTURE_VALUE","100",0.04,False),
        ("MONTHLY_SAVINGS_FUTURE_VALUE","100",0.04,0),
        ("MONTHLY_SAVINGS_FUTURE_VALUE","100",0.04,1201),
        ("UNKNOWN_FINANCIAL_MODEL","100",0.04,12),
    ):
        must_reject(lambda x=args:finance_model(*x),
                    "unsafe assumptions or inconsistent monthly periods")

    return {
        "schema":"V30_BOOTSTRAP_DEVELOPMENT_SELF_TEST_V1",
        "source_legacy_verified":baseline,
        "historical_dev_video_worklists":result,
        "typed_semantic_scenario_count":len(diverse),
        "typed_semantic_scenarios_pass":len(diverse),
        "bad_or_unseen_video_inputs_rejected":9,
        "math_models_reproduced":4,
        "math_adversarial_rejections":7,
        "automatic_knowledge_approvals":0,
        "independent_fact_validation_claimed":False,
        "historical_source_status_overwritten":False,
        "unseen_video_21_plus_loaded":False,
        "research_complete_certificates_generated":0,
        "production_ready":False
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    args=p.parse_args()
    try:
        print(json.dumps(self_test(args.root.resolve()),ensure_ascii=False,
                         sort_keys=True))
    except (ValueError,TypeError,KeyError,OSError) as err:
        print(json.dumps({"gate":"FAIL","error":str(err)},ensure_ascii=False))
        raise SystemExit(1)
