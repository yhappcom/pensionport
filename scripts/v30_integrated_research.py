#!/usr/bin/env python3
"""V3.0 integrated investment research engine: executable *foundation*.

This is a fail-closed, nonpersonal research WORK PLANNER and typed-review
prototype. It does not retrieve new originals, certify external facts, infer
semantic frames from short text, approve an integration or place trades.

#1-20 may be DEVELOPMENT fixtures; NEVER read #21+ here before a preregistered
unseen evaluation. Frozen V1-V2.3 code/data and legacy V3/V4 claims are read-only.
"""
import argparse
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = "v30/contracts/integrated_engine_v1.json"
EVAL = "v30/contracts/evaluation_protocol_v1.json"
DEMO_SOURCES = {
    19: ("zi9x_q2fYoc",
         "8fbb48dbff06389f69223fdcbdc94241b960d3e4",
         "e7284caf3d5cee58a202ad29e88a39c57973d5f181dda018f47852a9f23200f3",
         1134, 12),
    20: ("inLlZgtS7qs",
         "2f4970972f3dc8a9144c001f4e1a8c3a18e553fa",
         "c563107dd5479eba7b36e3b7ead388ed74d8ef5bb2c4207e616396749c9d5b77",
         31, 6),
}
VID = re.compile(r"^[A-Za-z0-9_-]{11}$")
CID = re.compile(r"^[A-Za-z0-9_-]{11}-\d{2,3}$")
SHA1 = re.compile(r"^[a-f0-9]{40}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
STATUS = {"PRIMARY_CONFIRMED", "QUALIFIED", "HYPOTHETICAL",
          "CONTRADICTED", "SPEAKER_OPINION"}
TYPES = {"LEGAL_OR_PRODUCT", "NUMERIC", "STRATEGY_OR_PERFORMANCE",
         "QUALITATIVE", "UNCLASSIFIED"}
STAGES = ("SOURCE_PROVENANCE", "ATOMIC_COVERAGE", "CLAIM_FRAME_AND_OBLIGATIONS",
          "PRIMARY_EVIDENCE", "QUANT_AND_EMPIRICAL", "RELATION_CANDIDATES",
          "INDEPENDENT_REVIEW", "COMPLETION_AND_APPEND_ONLY_INTEGRATION")
FRAME_FIELDS = ("subject_type", "subject_id", "action", "object_type", "object_id",
                "financial_role", "jurisdiction", "effective_date", "conditions",
                "units")
# Explicit ontological relationship candidates; not a claim of fact truth.
RELATED_ROLES = {
    frozenset(("ISA_TRANSFER_TAX_CREDIT", "PENSION_CONTRIBUTION_TAX_CREDIT")),
    frozenset(("BOND_DIRECT_MATURITY", "BOND_ETF_MATURITY_RISK")),
    frozenset(("RETIREMENT_PENSION_CASHFLOW", "RETIREMENT_INCOME_BRIDGE")),
    frozenset(("DIVIDEND_PAYOUT_MODEL", "RETIREMENT_INCOME_BRIDGE")),
}
DISTINCT_ROLE_GROUPS = (
    {"PENSION_INCOME_PAYOUT_TAX", "PENSION_CONTRIBUTION_LIMIT",
     "PENSION_CONTRIBUTION_TAX_CREDIT", "ISA_TRANSFER_TAX_CREDIT",
     "NATIONAL_PENSION_DEFER_BONUS", "CIVIL_SERVICE_PENSION_CONTRIBUTION"},
    {"GIFT_TAX_ALLOWANCE", "PENSION_INCOME_PAYOUT_TAX",
     "ISA_TRANSFER_TAX_CREDIT"},
)

def require(test, message):
    if not test:
        raise ValueError(message)

def read(root, path):
    return json.loads((root / path).read_text(encoding="utf-8"))

def git_blob_sha(path):
    b = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()

def valid_approved_source(root):
    """Validate immutable *policy* provenance, not factual approval."""
    config = read(root, CONTRACT)
    protocol = read(root, EVAL)
    require(config["schema"]=="V30_INTEGRATED_RESEARCH_ENGINE_CONTRACT_V1"
            and config["release_stage"]=="ARCHITECTURE_AND_EXECUTABLE_PILOT_ONLY"
            and config["hard_safety"]["production_release"]=="BLOCKED"
            and config["hard_safety"]["automatic_knowledge_merge"] is False
            and config["hard_safety"]["personal_investment_advice"] is False
            and config["hard_safety"]["trade_execution"] is False
            and config["hard_safety"]["no_unseen_video_21_plus_read_during_bootstrap"] is True,
            "V30_RESEARCH_POLICY_WEAKENED")
    require(config["workflow_stages"]==list(STAGES),
            "V30_STAGE_CONTRACT_CHANGED")
    for p,sha in config["frozen_existing_policy_files"].items():
        require(SHA1.fullmatch(sha) and git_blob_sha(root/p)==sha,
                "HISTORICAL_POLICY_OR_FIRST_USE_RESULT_CHANGED: "+p)
    require(git_blob_sha(root/"scripts/v5_candidate_engine_v23.py") ==
            config["frozen_v23_engine_git_blob_sha"],
            "FROZEN_V23_CODE_ALTERED")
    require(protocol["schema"]=="V30_EVALUATION_PROTOCOL_V1"
            and protocol["development_videos_inclusive"]==[1,20]
            and protocol["protected_out_of_sample_videos_begin_at"]==21
            and protocol["bootstrap_may_read_new_video_21_plus"] is False
            and protocol["independent_blind_labelers_required_for_release"] is True
            and protocol["release_status"].startswith("BLOCKED"),
            "V30_UNSEEN_TEST_OR_RELEASE_CONTRACT_WEAKENED")
    return config, protocol

def check_historical_registry(root):
    """Verify exact 4,120 crosswalk and 39 topic families, never rewrite."""
    # V5's historic provenance reconciliation is itself the trusted loader.
    from verify_v5_knowledge_integration import (
        load_legacy_claim_index, verified_verdict_reconciliations,
    )
    legacy,parts,irregular = load_legacy_claim_index(root)
    verdicts = verified_verdict_reconciliations(root,legacy)
    family = read(root,"data/synthesis/investment_knowledge_001_260/concept_families.json")
    require(len(legacy)==4120 and len(family["concept_families"])==39
            and len({r["video_id"] for r in legacy.values()})==253
            and len(irregular)==13,
            "HISTORICAL_KNOWLEDGE_COUNT_OR_EXCEPTION_REGRESSED")
    return {
        "historical_claims":len(legacy),"historical_videos":253,
        "topic_families":len(family["concept_families"]),
        "historical_71_public_proxy_id_count":len(irregular),
        "source_verdict_reconciliation_overlays":len(verdicts),
        "original_claims_modified":0,"meaning_automatically_approved":False,
    }

def load_development_video(root, number):
    """Consume ONLY explicitly pinned historic #19/20 V3 development abstracts.

    This does not open private SRT, reread audio or assert atomic completeness.
    """
    require(type(number) is int and number in DEMO_SOURCES,
            "BOOTSTRAP_REJECTS_UNSEEN_OR_UNPINNED_VIDEO")
    video_id, expected_blob, srt_hash, cues, expected_n = DEMO_SOURCES[number]
    require(VID.fullmatch(video_id) and SHA1.fullmatch(expected_blob)
            and SHA256.fullmatch(srt_hash), "UNSAFE_HISTORIC_SOURCE_METADATA")
    p = root / "data" / "analysis_events" / (video_id+".json")
    require(git_blob_sha(p)==expected_blob,
            "HISTORICAL_SOURCE_GIT_BLOB_CHANGED")
    x=read(root,"data/analysis_events/"+video_id+".json")
    ix=read(root,"data/subtitles/content_index_001_070.json")["items"][video_id]
    require(ix["roster_no"]==number and ix["subtitle_sha256"]==srt_hash
            and ix["cue_count"]==cues
            and x["video_id"]==video_id and x["approval"]=="APPROVED"
            and x["evidence_gate"]["source_checked"] is True
            and x["evidence_gate"]["source_fingerprint"]==srt_hash
            and len(x["core_claims"])==expected_n,
            "HISTORICAL_V3_SOURCE_OR_SUBTITLE_REGISTRY_DIVERGED")
    claims={}
    for row in x["core_claims"]:
        cid=row["claim_id"]
        require(isinstance(cid,str) and CID.fullmatch(cid)
                and cid.startswith(video_id+"-") and cid not in claims
                and row["verification"] in STATUS
                and isinstance(row["claim"],str) and row["claim"].strip()
                and isinstance(row["timecode"],str) and row["timecode"]
                and isinstance(row["source_precision"],str)
                and row["source_precision"].strip(),
                "INVALID_HISTORIC_CLAIM_ID_TEXT_OR_PROVENANCE")
        claims[cid]={
            "claim_id":cid,"video_id":video_id,"video_number":number,
            "source_git_blob_sha":expected_blob,
            "historical_srt_sha256":srt_hash,
            "text":row["claim"],"legacy_verdict":row["verification"],
            "historical_timecode":row["timecode"],
            "historical_source_precision":row["source_precision"],
        }
    return {"video_id":video_id,"number":number,"cue_count":cues,
            "original_srt_sha256_history":srt_hash,
            "original_audio_reopened_this_run":False,
            "original_srt_bytes_reopened_this_run":False,
            "claims":list(claims.values())}

def obligatory_evidence(claim_type):
    """Required evidence categories; UNKNOWN blocks all waivers."""
    require(claim_type in TYPES,"INVALID_CLAIM_CLASS")
    x=["SOURCE_AND_CLAIMS", "PRIMARY_EVIDENCE", "GENERAL_DECISION"]
    if claim_type in ("NUMERIC", "STRATEGY_OR_PERFORMANCE","UNCLASSIFIED"):
        x.append("QUANT_AND_EMPIRICAL")
    if claim_type=="STRATEGY_OR_PERFORMANCE":
        x.append("REAL_WORLD_EMPIRICAL_REQUIRED")
    if claim_type=="UNCLASSIFIED":
        x.append("CLAIM_CLASSIFICATION_REQUIRED")
    return x

def plan_unverified_video(root, number):
    """Concrete, source-checked, per-claim worklist. Never a certificate."""
    contract, _ = valid_approved_source(root)
    video=load_development_video(root,number)
    obligations=[]
    for c in video["claims"]:
        risk=("CORRECTION_ONLY" if c["legacy_verdict"]=="CONTRADICTED"
              else "UNREPLICATED_HYPOTHETICAL" if c["legacy_verdict"]=="HYPOTHETICAL"
              else "HISTORICAL_EVIDENCE_UNREVERIFIED")
        obligations.append({
            "claim_id":c["claim_id"],
            "legacy_verdict":c["legacy_verdict"],
            "historical_timecode":c["historical_timecode"],
            "classification":"UNCLASSIFIED",
            "frame_status":"MISSING_STRUCTURED_FRAME",
            "source_cue_range":None,
            "full_material_atomic_coverage_revalidated":False,
            "requirements":obligatory_evidence("UNCLASSIFIED"),
            "evidence_ids":[],
            "primary_source_actual_text_read_this_run":False,
            "quant_arithmetic_checked_this_run":False,
            "empirical_reproduced_this_run":False,
            "source_risk":risk,
            "research_status":"BLOCKED",
            "blockers":[
                "FULL_ORIGINAL_SRT_ATOMIC_COVERAGE_AND_AUDIO_LIMITS_UNVERIFIED",
                "EXPLICIT_FINANCIAL_FRAME_AND_CLAIM_CLASSIFICATION_REQUIRED",
                "INDEPENDENT_PRIMARY_NUMERIC_OR_EMPIRICAL_EVIDENCE_UNVERIFIED",
                "INDEPENDENT_HUMAN_REVIEW_AND_CERTIFICATE_ABSENT",
            ],
        })
    return {
        "schema":"V30_SOURCE_BOUND_WORKLIST_V1",
        "phase":"BOOTSTRAP_DEVELOPMENT_FIXTURE_NOT_FULL_VIDEO_RESEARCH",
        "video_number":video["number"],
        "video_id":video["video_id"],
        "source_claim_count":len(video["claims"]),
        "historical_srt_cues":video["cue_count"],
        "historical_srt_sha256":video["original_srt_sha256_history"],
        "source_original_audio_reverified":False,
        "source_original_srt_bytes_reverified":False,
        "full_atomic_coverage_complete":False,
        "material_claim_count_confirmed_by_full_srt":None,
        "gate_per_stage":{k:("HISTORIC_SOURCE_REGISTRY_CHECKED" if k=="SOURCE_PROVENANCE"
                           else "BLOCKED_NOT_DONE") for k in STAGES},
        "claim_worklist":obligations,
        "blocked_claim_count":len(obligations),
        "real_research_complete_certificates":0,
        "authorized_knowledge_merges":0,
        "personal_advice_approved":False,
        "investment_trade_instruction_permitted":False,
        "research_status":"RESEARCH_BLOCKED",
    }

def validate_frame(frame):
    """Require explicit auditable financial-role annotation, never infer it."""
    require(isinstance(frame,dict) and set(FRAME_FIELDS)<=set(frame),
            "EXPLICIT_FINANCIAL_FRAME_REQUIRED")
    for key in FRAME_FIELDS:
        if key=="conditions":
            require(isinstance(frame[key],dict),"CONDITIONS_MUST_BE_EXPLICIT_MAPPING")
        else:
            require(isinstance(frame[key],str) and frame[key].strip(),
                    "MISSING_FINANCIAL_FRAME_FIELD_"+key)
    require(frame["financial_role"]!="AUTO_INFERRED",
            "UNVERIFIED_SEMANTIC_CLASSIFICATION")
    require(frame["effective_date"]=="UNKNOWN" or
            re.fullmatch(r"\d{4}-\d{2}-\d{2}",frame["effective_date"]),
            "INVALID_OR_MISSING_EFFECTIVE_DATE")
    return frame

def risk_for_status(left,right):
    v={left,right}
    require(v<=STATUS,"UNKNOWN_OR_MISSING_HISTORICAL_VERDICT")
    return ("CORRECTION_ONLY" if "CONTRADICTED" in v
            else "UNREPLICATED_HYPOTHETICAL" if "HYPOTHETICAL" in v
            else "HUMAN_REVIEW_ONLY")

def compare_explicit_frames(left,right):
    """Typed review triage: no automatic approval, no truth inference.

    INPUTS must originate from source-hash-checked records before the caller
    appends independently reviewed frames. No comparison against bare strings.
    """
    require(isinstance(left,dict) and isinstance(right,dict)
            and isinstance(left.get("claim_id"),str)
            and isinstance(right.get("claim_id"),str)
            and left["claim_id"]!=right["claim_id"],
            "PAIR_REQUIRES_TWO_DISTINCT_ORIGINAL_CLAIM_IDS")
    fa=validate_frame(left.get("frame"))
    fb=validate_frame(right.get("frame"))
    risk=risk_for_status(left.get("legacy_verdict"),right.get("legacy_verdict"))
    a,b=fa["financial_role"],fb["financial_role"]
    same_domain=(
        fa["subject_type"]==fb["subject_type"]
        and fa["subject_id"]==fb["subject_id"]
        and fa["object_type"]==fb["object_type"]
        and fa["object_id"]==fb["object_id"]
        and fa["jurisdiction"]==fb["jurisdiction"]
    )
    same_rules=(fa["effective_date"]==fb["effective_date"]
                and fa["conditions"]==fb["conditions"])
    essential=("subject_type","subject_id","object_type","object_id",
               "jurisdiction","effective_date")
    if a==b and any(fa[key]=="UNKNOWN" or fb[key]=="UNKNOWN"
                    for key in essential):
        relation="UNRESOLVED_AMBIGUOUS"
        why="MISSING_MATERIAL_SCOPE_OR_EFFECTIVE_DATE"
    elif a!=b:
        if frozenset((a,b)) in RELATED_ROLES:
            relation="QUALIFIES_SCOPE_CANDIDATE"
            why="EXPLICIT_ONTOLOGY_RELATED_DIFFERENT_FINANCIAL_ROLES"
        else:
            relation="SCOPE_DIFFERENT"
            why="DIFFERENT_FINANCIAL_ROLE_NO_EQUALITY_INFERENCE"
    elif fa["effective_date"]!=fb["effective_date"] and (
            "UNKNOWN" not in (fa["effective_date"],fb["effective_date"])):
        relation="QUALIFIES_SCOPE_CANDIDATE"
        why="DIFFERENT_STATUTORY_EFFECTIVE_DATES"
    elif not same_domain:
        relation="QUALIFIES_SCOPE_CANDIDATE"
        why="DIFFERENT_SUBJECT_OR_JURISDICTION_OR_PRODUCT"
    elif fa["action"]!=fb["action"]:
        relation="CALCULATION_DEPENDENCY_REVIEW"
        why="SAME_FINANCIAL_ROLE_DIFFERENT_ACTION"
    elif not same_rules:
        relation="QUALIFIES_SCOPE_CANDIDATE"
        why="SAME_FINANCIAL_ROLE_DIFFERENT_CONDITIONS_OR_UNKNOWN_DATE"
    elif fa["units"]!=fb["units"]:
        relation="UNRESOLVED_AMBIGUOUS"
        why="SAME_SCOPE_INCOMPATIBLE_QUANTITY_UNITS"
    elif fa.get("value") is not None and fb.get("value") is not None and (
            str(fa["value"]) != str(fb["value"])):
        relation="CONTRADICTION_REVIEW"
        why="SAME_SCOPE_DIFFERING_UNVERIFIED_NUMERIC_CLAIMS"
    else:
        relation="SAME_PROPOSITION_CANDIDATE"
        why="MATCHING_EXPLICIT_FRAME_SCOPE_NOT_EVIDENCE_OF_TRUTH"
    return {
        "schema":"V30_TYPED_RELATION_TRIAGE_V1",
        "claim_ids":[left["claim_id"],right["claim_id"]],
        "relationship_candidate":relation,
        "reason":why,"source_risk":risk,
        "financial_roles":[a,b],
        "explicit_frame_required":True,
        "review_only":True,
        "claimed_semantic_truth":None,
        "official_source_review_reperformed":False,
        "automatically_approved":False,
        "automatic_knowledge_merge_permitted":False,
        "research_completion_certificate_permitted":False,
        "investment_trade_instruction_permitted":False,
    }

def dec(value):
    require(isinstance(value,(str,int,Decimal)) and not isinstance(value,bool),
            "NUMERIC_INPUT_REQUIRES_EXACT_DECIMAL_OR_INTEGER")
    try:
        n=Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("INVALID_FINANCIAL_NUMERIC_INPUT") from exc
    require(n.is_finite(),"NONFINITE_FINANCIAL_INPUT")
    return n

def finance_model(kind,principal,annual_rate,months):
    """Deterministic **arithmetic only**, not contract-specific economics.

    annual_rate is a nominal annual *decimal*, with monthly rate annual/12;
    contributions are paid at *end* of each month; no tax, fees, inflation.
    """
    require(kind in ("MONTHLY_SAVINGS_FUTURE_VALUE","MONTHLY_AMORTIZING_PAYOUT"),
            "UNSUPPORTED_OR_UNVERIFIED_FINANCIAL_MODEL")
    require(type(months) is int and 1<=months<=1200,"INVALID_MONTHS")
    p,r=dec(principal),dec(annual_rate)
    require(p>=0 and r>=Decimal("-0.99") and r<=Decimal("1"),
            "UNSUPPORTED_PRINCIPAL_OR_NOMINAL_ANNUAL_RATE")
    with localcontext() as ctx:
        ctx.prec=40
        m=r/Decimal(12)
        if kind=="MONTHLY_SAVINGS_FUTURE_VALUE":
            amount=p*Decimal(months) if m==0 else p*(((1+m)**months-1)/m)
        else:
            amount=p/Decimal(months) if m==0 else p*m/(1-(1+m)**(-months))
        return {
            "kind":kind,"principal_or_contribution":str(p),
            "nominal_annual_rate":str(r),"monthly_periods":months,
            "timing":"END_OF_MONTH","monthly_rate_convention":"NOMINAL_DIVIDED_BY_12",
            "amount":str(amount.quantize(Decimal("0.01"))),
            "units":"SAME_CURRENCY_UNITS_AS_INPUT",
            "includes_fees_taxes_inflation":False,
            "contractual_rate_or_payout_verified":False,
            "independent_source_and_economic_assumptions_approved":False,
        }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--validate-baseline",action="store_true")
    p.add_argument("--plan-development-video",type=int)
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    root=args.root.resolve()
    valid_approved_source(root)
    out={
       "schema":"V30_BOOTSTRAP_RUN_V1",
       "architecture_contract_checked":True,
       "v23_frozen_and_unchanged":True,
       "unseen_video_21_plus_loaded":False,
       "production_release":"BLOCKED",
       "automatic_research_completion_certificates":0,
       "automatic_knowledge_merges":0,
    }
    if args.validate_baseline:out["legacy_registry"]=check_historical_registry(root)
    if args.plan_development_video is not None:
        out["worklist"]=plan_unverified_video(root,args.plan_development_video)
    if args.self_test:
        from verify_v30_integrated_research import self_test
        out["bootstrap_tests"]=self_test(root)
    print(json.dumps(out,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    try:main()
    except (ValueError,TypeError,KeyError,IndexError,OSError) as exc:
        print(json.dumps({"gate":"FAIL","error":str(exc)},ensure_ascii=False))
        raise SystemExit(1)
