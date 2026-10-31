#!/usr/bin/env python3
"""Non-mutating V3.0 red-team audit of the frozen bootstrap implementation.

Expected positive results below REPRODUCE limitations and design weaknesses,
not pass the V3.0 production engine. This script does not access #21+ source
claim content, external accounts, private originals or actual holdings.
"""
import argparse
import copy
import json
import shutil
import tempfile
from pathlib import Path

from v30_integrated_research import (
    ROOT, CONTRACT, EVAL, valid_approved_source, compare_explicit_frames,
    validate_frame, finance_model, obligatory_evidence, git_blob_sha,
)

V30_ORIGINAL_ENGINE_SHA="7924ad51058abc1129eef2ec91df97589b412f63"
AUDIT_SCHEMA="V30_DEEP_SECURITY_SEMANTICS_AUDIT_20261031_V1"

def need(ok,reason):
    if not ok:
        raise ValueError("RED_TEAM_EXPECTATION_NOT_REPRODUCED: "+reason)

def frame(role="PENSION_INCOME_PAYOUT_TAX",action="WITHDRAW",value=None,
          effective_date="2026-01-01"):
    x={
        "subject_type":"PENSION_ACCOUNT",
        "subject_id":"SYNTHETIC_NONPERSONAL",
        "action":action,
        "object_type":"TAX_RULE",
        "object_id":"SYNTHETIC_THRESHOLD",
        "financial_role":role,
        "jurisdiction":"KR",
        "effective_date":effective_date,
        "conditions":{"tax_event":"PRIVATE_PENSION_PAYOUT"},
        "units":"KRW",
    }
    if value is not None:x["value"]=value
    return x

def claim(id,form,status="QUALIFIED"):
    return {"claim_id":id,"frame":form,"legacy_verdict":status}

def run(root):
    valid_approved_source(root)
    need(git_blob_sha(root/"scripts/v30_integrated_research.py")==
         V30_ORIGINAL_ENGINE_SHA,
         "audit cannot be silently applied to a different V3.0 engine version")
    reproduced=[]

    # P0: the supposedly protected source manifest is itself supplied by an
    # editable contract. An empty manifest skips source-policy hash checks.
    with tempfile.TemporaryDirectory(prefix="v30_readonly_redteam_") as d:
        q=Path(d)
        (q/"scripts").mkdir(parents=True)
        (q/"v30/contracts").mkdir(parents=True)
        shutil.copyfile(root/"scripts/v5_candidate_engine_v23.py",
                        q/"scripts/v5_candidate_engine_v23.py")
        cfg=json.loads((root/CONTRACT).read_text(encoding="utf-8"))
        eval_doc=json.loads((root/EVAL).read_text(encoding="utf-8"))
        original_protected=sorted(cfg["frozen_existing_policy_files"])
        need(len(original_protected)>=3,"expected protected source entries")
        cfg["frozen_existing_policy_files"]={}
        # Deliberately flip safety claims that validator does not assert.
        cfg["hard_safety"]["automatic_research_completion_certificate"]=True
        cfg["relation_output"]["claim_truth_inferred_from_similarity"]=True
        cfg["source_of_truth"]["raw_user_srt_must_not_be_committed"]=False
        eval_doc["targets"]["retrieval_recall"]=0.01
        (q/CONTRACT).write_text(json.dumps(cfg,ensure_ascii=False),encoding="utf-8")
        (q/EVAL).write_text(json.dumps(eval_doc,ensure_ascii=False),encoding="utf-8")
        mutated,mut_eval=valid_approved_source(q)
        need(mutated["frozen_existing_policy_files"]=={} and
             mutated["hard_safety"]["automatic_research_completion_certificate"] is True
             and mutated["relation_output"]["claim_truth_inferred_from_similarity"] is True
             and mutated["source_of_truth"]["raw_user_srt_must_not_be_committed"] is False
             and mut_eval["targets"]["retrieval_recall"]==0.01,
             "critical invariant edits should pass current vulnerable validator")
    reproduced.append({
        "id":"AUD-01","severity":"P0_ARCHITECTURE_GATE",
        "issue":"MUTABLE_PROTECTED_FILE_MANIFEST_AND_UNCHECKED_POLICY_INVARIANTS",
        "outcome":"REPRODUCED_ACCEPTED_WEAKENED_POLICY_IN_TEMP_ROOT",
        "protected_paths_bypassed_count":len(original_protected),
        "note":"No repository policy file was modified; temporary synthetic copy only.",
    })

    # P0 pre-production: assertion IDs and legacy verdicts are not verified
    # against original claim files in the low-level pure comparison function.
    x=claim("FABRICATEDA1-01",frame(value="15000000"),"PRIMARY_CONFIRMED")
    y=claim("FABRICATEDB2-02",frame(value="15000000"),"PRIMARY_CONFIRMED")
    out=compare_explicit_frames(x,y)
    need(out["relationship_candidate"]=="SAME_PROPOSITION_CANDIDATE"
         and out["source_provenance_independently_verified_by_this_function"] is False
         and not out["automatically_approved"]
         and not out["automatic_knowledge_merge_permitted"],
         "unbound synthetic claim IDs can produce a relation candidate")
    reproduced.append({
        "id":"AUD-02","severity":"P0_IF_PROMOTED_TO_PUBLIC_OR_APPROVAL_API",
        "issue":"RELATION_FRAME_PROVENANCE_AND_REVIEWER_UNAUTHENTICATED",
        "outcome":"REPRODUCED_CANDIDATE_FROM_NONEXISTENT_CLAIM_IDS",
        "mitigation_already_present":"automatic approval and knowledge merge remain forbidden"
    })

    # P1 same economic number differing only in lexical Decimal representation.
    n1=claim("FABRICATEDA1-03",frame(value="15000000"))
    n2=claim("FABRICATEDB2-04",frame(value="15000000.00"))
    different_format=compare_explicit_frames(n1,n2)
    need(different_format["relationship_candidate"]=="CONTRADICTION_REVIEW",
         "mathematically equal values fail lexical comparison")
    reproduced.append({
        "id":"AUD-03","severity":"P1_SEMANTIC_CORRECTNESS",
        "issue":"NUMERIC_LEXICAL_INEQUALITY_FALSE_CONTRADICTION",
        "outcome":"REPRODUCED_CONTRADICTION_CANDIDATE_FOR_SAME_DECIMAL_VALUE",
        "example_values":["15000000","15000000.00"]
    })

    # P1 frame omission is not detected for same-like propositions.
    missing=claim("FABRICATEDB2-05",frame())
    om=compare_explicit_frames(n1,missing)
    need(om["relationship_candidate"]=="SAME_PROPOSITION_CANDIDATE",
         "missing numeric value leaves misleading equivalent proposition label")
    reproduced.append({
        "id":"AUD-04","severity":"P1_SEMANTIC_CORRECTNESS",
        "issue":"MISSING_NUMERIC_PAYLOAD_DID_NOT_PREVENT_SAME_PROPOSITION",
        "outcome":"REPRODUCED_SAME_PROPOSITION_CANDIDATE_WITH_ONE_VALUE_ABSENT"
    })

    # P1 bogus financial roles and impossible calendar dates are syntactically valid.
    invalid_financial_role=frame(role="MADE_UP_FINANCIAL_ROLE_999")
    invalid_effective_date=frame(effective_date="2026-99-99")
    need(validate_frame(invalid_financial_role)==invalid_financial_role
         and validate_frame(invalid_effective_date)==invalid_effective_date,
         "invalid role taxonomy and impossible date should be rejected, but are not")
    reproduced.append({
        "id":"AUD-05","severity":"P1_CONTRACT_VALIDATION",
        "issue":"ROLE_NOT_ENUMERATED_AND_DATE_NOT_CALENDAR_VALIDATED",
        "outcome":"REPRODUCED_ACCEPTED_MADE_UP_ROLE_AND_IMPOSSIBLE_DATE"
    })

    # P1 action inequality does not mathematically prove dependency.
    a=claim("FABRICATEDA1-06",frame(action="WITHDRAW"))
    b=claim("FABRICATEDB2-07",frame(action="OPEN_ACCOUNT"))
    dep=compare_explicit_frames(a,b)
    need(dep["relationship_candidate"]=="CALCULATION_DEPENDENCY_REVIEW",
         "action mismatch is incorrectly treated as mathematical dependency candidate")
    reproduced.append({
        "id":"AUD-06","severity":"P1_SEMANTIC_CORRECTNESS",
        "issue":"DIFFERENT_ACTIONS_LABELLED_CALCULATION_DEPENDENCY",
        "outcome":"REPRODUCED_CALCULATION_DEPENDENCY_WITHOUT_FORMULA_OR_GRAPH"
    })

    # P1 single-label choice can waive numeric requirement if legal claim
    # contains a material amount. No actual claim classification is done.
    legal=obligatory_evidence("LEGAL_OR_PRODUCT")
    numeric=obligatory_evidence("NUMERIC")
    need("QUANT_AND_EMPIRICAL" not in legal
         and "QUANT_AND_EMPIRICAL" in numeric,
         "claim-class-dependent obligations can omit finance math checks")
    reproduced.append({
        "id":"AUD-07","severity":"P1_OBLIGATION_CLASSIFICATION",
        "issue":"SINGLE_CLAIM_TYPE_CAN_OMIT_NUMERIC_OBLIGATION",
        "outcome":"REPRODUCED_NUMERIC_REQUIREMENT_ABSENT_FROM_LEGAL_ONLY_CLASS"
    })

    # P1 #21+ source metadata already exists in the 253-video historic registry.
    # Do NOT load or list individual #21+ records in the red-team audit.
    from verify_v5_knowledge_integration import load_legacy_claim_index
    import inspect
    fntext=inspect.getsource(__import__("v30_integrated_research").legacy_topic_prefilter)
    need("primary_concept_id" in fntext and
         'x["roster_no"]' not in fntext and
         'r["roster_no"] <= 20' not in fntext,
         "topic filter lacks a roster embargo")
    # Historic census already statically established by existing V3.0 tests;
    # this audit does not visit individual post-20 claim IDs.
    reproduced.append({
        "id":"AUD-08","severity":"P1_DATA_LEAKAGE_EVALUATION",
        "issue":"TOPIC_PREFILTER_LACKS_POST20_EMBARGO_FOR_HISTORICAL_INDEX",
        "outcome":"CONFIRMED_BY_SOURCE_PATH_NO_POST20_ROSTER_FILTER",
        "new_video_content_read_for_this_probe":False,
        "note":"Contrast no raw #21+ SRT with historic post-20 claim metadata exposure."
    })

    # P1 existing CI excludes content scan for .json/.md and allows edits to
    # scripts/data not on V3.0 workflow path triggers.
    yml=(root/".github/workflows/v30-integrated-research-gate.yml").read_text(encoding="utf-8")
    need('git ls-files -- ' in yml and "v30/**" in yml and
         "scripts/v30_integrated_research.py" in yml and
         "file type" in yml and "pii" not in yml.lower(),
         "existing CI only validates file-path types and selected source files")
    reproduced.append({
        "id":"AUD-09","severity":"P1_PRIVACY_AND_IMMUTABILITY",
        "issue":"CI_FILE_EXTENSION_CHECK_NOT_CONTENT_PRIVACY_OR_ALL_LEGACY_DIFF_GATE",
        "outcome":"CONFIRMED_BY_WORKFLOW_SOURCE_REVIEW",
        "note":"No personal or private data was written to repository in this audit."
    })

    # P0 for final system: bootstrap has no dynamic source/evidence runner.
    src=(root/"scripts/v30_integrated_research.py").read_text(encoding="utf-8")
    require_tokens=[
        'phase":"BOOTSTRAP_DEVELOPMENT_FIXTURE_NOT_FULL_VIDEO_RESEARCH"',
        '"research_status":"RESEARCH_BLOCKED"',
        '"full_atomic_coverage_complete":False',
        '"primary_source_actual_text_read_this_run":False',
        '"empirical_reproduced_this_run":False',
    ]
    need(all(s in src for s in require_tokens),
         "worklist remains intentionally blocked, not a research completion engine")
    reproduced.append({
        "id":"AUD-10","severity":"P0_FUNCTIONAL_COMPLETENESS",
        "issue":"ORCHESTRATION_MISSING_WORKLIST_ONLY",
        "outcome":"CONFIRMED_IMPLEMENTATION_RETURNS_ONLY_BLOCKED_OBLIGATION_PLAN",
        "automatic_research_certificates":0
    })

    # Historical fixes that do work as designed: V2.3 hash bound and
    # disabled merging, corrected source risk; arithmetic remains conditional.
    p=finance_model("MONTHLY_AMORTIZING_PAYOUT","308470000","0.04",360)
    need(p["contractual_rate_or_payout_verified"] is False
         and p["independent_source_and_economic_assumptions_approved"] is False,
         "hypothetical arithmetic cannot be promoted to contractual evidence")
    return {
        "schema":AUDIT_SCHEMA,
        "audit_kind":"READ_ONLY_CODE_AND_SYNTHETIC_COUNTEREXAMPLE",
        "engine_git_blob_sha":V30_ORIGINAL_ENGINE_SHA,
        "findings_count":len(reproduced),
        "findings":reproduced,
        "existing_safety_retained":{
            "v23_source_sha_enforced":True,
            "candidate_auto_merge_still_disabled":True,
            "source_hash_checked_19_20_dev":True,
            "quant_contractual_truth_not_inferred":True,
            "production_release_blocked":True,
        },
        "conclusion":"V30_BOOTSTRAP_TEST_PASS_NOT_FINAL_RESEARCH_ENGINE_READY",
        "production_ready":False,
        "engine_files_modified_in_this_audit":False,
        "real_unseen_21_plus_claims_examined":False
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    args=p.parse_args()
    try:
        print(json.dumps(run(args.root.resolve()),ensure_ascii=False,sort_keys=True))
    except (KeyError,ValueError,TypeError,OSError) as exc:
        print(json.dumps({"audit":"FAIL","error":str(exc)},ensure_ascii=False))
        raise SystemExit(1)
