#!/usr/bin/env python3
"""Real video #001 regression probe for V5 research completion.

Unlike synthetic fixtures this reads immutable prior V3/V4/V5 research JSON
from the repository and compares every historical claim and provenance scope.
It NEVER reads or republishes private SRT or client financial information.
Passing confirms fail-closed governance on this pilot, not factual completion.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PILOT="v5/pilots/v5_001_sz5N9WJS310_completion_probe.json"
POLICY="v5/policy/research_completion_gate_v1.json"
STATUS="v5/research_completion_001_010.json"
TYPES={"LEGAL_OR_PRODUCT","NUMERIC","STRATEGY_OR_PERFORMANCE","QUALITATIVE"}
DOMAINS={"SOURCE_AND_CLAIMS","PRIMARY_EVIDENCE","QUANT_AND_EMPIRICAL","GENERAL_DECISION"}
KNOWN_BAD={"sz5N9WJS310-06","sz5N9WJS310-15"}
VIDEO="sz5N9WJS310"

def need(ok,msg):
    if not ok: raise ValueError(msg)

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def git_blob_sha(path):
    b=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def verify(p,v3,gold,signoff,v5,policy,status,root):
    need(p["schema"]=="V5_REAL_VIDEO_COMPLETENESS_PILOT_001_1.0"
         and p["real_source_record_not_fixture"] is True,"not a real pilot")
    need(p["video_number"]==1 and p["video_id"]==VIDEO
         and v3["video_id"]==gold["video_id"]==signoff["video_id"]==v5["video_id"]==VIDEO,
         "video identity incorrect")
    need(policy["schema"]=="RESEARCH_COMPLETENESS_V1" and
         set(policy["four_domains"])==DOMAINS and policy["private_data_allowed"] is False
         and policy["historical_001_010_certified"] is False,"policy weakened")
    need(status["certified_count"]==0
         and next(x for x in status["videos"] if x["video_number"]==1)["status"]=="NOT_CERTIFIED",
         "historical #1 falsely certified")

    for name,path in p["source_paths"].items():
        need(name in ("v3","v4_gold","v4_signoff","v5_closeout"),"unrecognized provenance source")
        need(path.startswith(("data/analysis_events/","data/synthesis/investment_knowledge_v4/reviews/","v5/retrofit/")),
             "unapproved provenance directory")
        file=(root/path)
        need(file.is_file() and git_blob_sha(file)==p["legacy_git_blob_shas"][name],
             "source content changed: "+name)
    need(set(p["source_paths"])==set(p["legacy_git_blob_shas"])==
         {"v3","v4_gold","v4_signoff","v5_closeout"},"missing pinned legacy evidence")
    need(p["source_paths"]["v3"]=="data/analysis_events/"+VIDEO+".json",
         "V3 source misattributed")
    need(p["source_paths"]["v5_closeout"]=="v5/retrofit/v5_001_"+VIDEO+"_bounded_closeout.json",
         "V5 source misattributed")

    old_claims=v3["core_claims"]
    old_map={x["claim_id"]:x for x in old_claims}
    v5_claims=v5["claim_coverage"]["claims"]
    v5_map={x["id"]:x for x in v5_claims}
    p_claims=p["claims"]
    probe_map={x["claim_id"]:x for x in p_claims}
    gold_overlays={x["claim_id"] for x in gold["claim_overlays"]}
    need(len(old_claims)==len(old_map)==len(v5_claims)==len(v5_map)==
         len(p_claims)==len(probe_map)==23,"23 claims not individually represented")
    need(set(old_map)==set(v5_map)==set(probe_map)==gold_overlays,
         "claims missing or artificial IDs inserted")
    need(v5["claim_coverage"]["expected_legacy_claim_count"]==23
         and signoff["based_on"]["legacy_claims_matched"]==23,
         "historical claim denominator altered")

    s=p["source_boundaries"]
    hash_expected="2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f"
    need(s["historical_private_srt_sha256"]==hash_expected==
         v5["source"]["source_sha256"]==gold["source_srt_sha256"]==
         signoff["based_on"]["original_srt_sha256"],
         "private SRT historical digest mismatch")
    need(s["historical_srt_cues"]==v5["source"]["cue_count"]==
         gold["confirmed"]["srt_cues"]==signoff["based_on"]["source_srt_cues"]==1195,
         "1195 source cues changed")
    need(s["private_raw_srt_in_repository"] is False
         and s["independent_raw_srt_rehashed_in_this_pilot"] is False,
         "unearned original source rehash / privacy error")
    need(s["complete_audio_and_frame_verification"] is False
         and gold["source_integrity"]["original_audio_and_frames_verified"] is False
         and signoff["full_audio_video_verified"] is False,
         "unearned media verification")
    need(s["full_semantic_review_in_v5"] is False
         and v5["source"]["full_human_semantic_review_completed"] is False
         and v5["source"]["all_cues_manually_understood"] is False,
         "partial source review promoted to full")
    need(s["v5_selected_source_contexts"]==v5["source"]["source_cue_contexts_read"]==3,
         "selected source contexts miscounted")

    q=p["denominator"]
    need(q["v3_core_claim_ids"]==23
         and q["v4_atomic_financial_statements"]==gold["confirmed"]["atomic_facts_audited"]==
         signoff["based_on"]["atomic_financial_statements_screened"]==42,
         "42 atomic claims invisibly reduced to 23")
    need(q["v4_all_42_atomic_statements_independently_fact_verified"] is False
         and signoff["qa"]["all_42_statements_independently_fact_verified"] is False,
         "atomic statements unearned completion")
    need(q["new_completed_independent_claims_certified"]==0,
         "pilot cannot mint new independent claim approvals")
    need(q["v5_legacy_external_open"]==len(v5["external_blockers"])==3,
         "legacy OPEN denominator changed")
    need({x["id"] for x in v5["external_blockers"]}==
         set(p["historical_open_unmapped_ids"]) and
         len(p["historical_open_unmapped_ids"])==3,
         "unmapped historical OPEN cannot be silently resolved")

    source_ids={x["ref_id"] for x in v5["primary_checks"]}
    checks={x["ref_id"]:x for x in v5["primary_checks"]}
    need(len(source_ids)==len(v5["primary_checks"])==3,
         "independent official sources scope overstated")
    need(len(p["official_source_scope"])==3 and
         {x["id"] for x in p["official_source_scope"]}==source_ids,
         "primary source metadata mismatch")
    for entry in p["official_source_scope"]:
        original=checks[entry["id"]]
        need(entry["scope_claim_ids"]==original["supported_claim_ids"]
             and entry["source_read_in_existing_v5"]==original["actual_page_read_this_turn"],
             "source-to-claim support fabricated")

    model=v5["decision_model"]
    need(model["id"]=="V5_CLOSEOUT_001" and model["type"]=="MONTHLY_SAVINGS"
         and model["synthetic_only"] is True and len(model["scenarios"])==2,
         "V5 numerical coverage overclaimed")
    need(len(p["verified_numerical_models_from_existing_v5"])==1,"numeric model count incorrect")
    model_info=p["verified_numerical_models_from_existing_v5"][0]
    need(model_info["id"]==model["id"] and model_info["tested_scenario_count"]==2
         and model_info["linked_claim_ids"]==[VIDEO+"-06"]
         and model_info["status"]=="SYNTHETIC_ARITHMETIC_ONLY",
         "hypothetical math improperly reused for other claims")
    arithmetic={}
    for case in model["scenarios"]:
        name=case["label"]
        amount, annual_rate, months=case["inputs"]
        need(amount==300000 and annual_rate==0.07
             and months=={"BASE":120,"ADVERSE":84}[name],
             "savings model was silently changed")
        rate=(1+annual_rate)**(1/12)-1
        accumulated=0.0
        for _ in range(months):
            accumulated=accumulated*(1+rate)+amount
        need(math.isclose(accumulated,case["expected"],rel_tol=1e-10,abs_tol=0.01),
             "independent month-by-month arithmetic differs")
        arithmetic[name]=round(accumulated)
    need(set(arithmetic)=={"BASE","ADVERSE"} and
         arithmetic["BASE"]>arithmetic["ADVERSE"],
         "scenario completeness")

    direct_context=0
    for cid in sorted(old_map):
        a,b,x=old_map[cid],v5_map[cid],probe_map[cid]
        need(x["timecode"]==a["timecode"]==b["timecode"]
             and x["historic_verdict"]==a["verification"]==b["verdict"],
             "historical per-claim verdict/time changed: "+cid)
        types=x["claim_type_obligations"]
        need(isinstance(types,list) and len(types)==len(set(types))
             and types and set(types)<=TYPES,
             "claim missing preflight methods: "+cid)
        need(type(x["v5_direct_context_reexamined"]) is bool
             and x["v5_direct_context_reexamined"]==b["srt_context_read_this_turn"],
             "prior full-source review exaggerated: "+cid)
        direct_context+=x["v5_direct_context_reexamined"]
        need(x["v5_primary_scope_refs"]==b["primary_scope_refs"]
             and set(x["v5_primary_scope_refs"])<=source_ids,
             "primary evidence false promotion: "+cid)
        for src_id in x["v5_primary_scope_refs"]:
            need(cid in checks[src_id]["supported_claim_ids"],
                 "missing primary reverse link: "+cid)
        need(x["v5_quantitative_model_refs"]==
             ([model["id"]] if cid==VIDEO+"-06" else []),
             "model invented for unmodeled claim: "+cid)
        need(x["v5_strategy_empirical_dataset_ids"]==[],
             "no real-world strategy research has been performed in V5")
        need(x["pilot_outcome"]==
             ("CORRECTION_QUARANTINED" if cid in KNOWN_BAD
              else "EVIDENCE_LIMITED"),
             "unearned positive research promotion: "+cid)
        need(x["positive_advice_permitted"] is False,
             "unqualified investment principle: "+cid)
    need(direct_context==3,"V5 actual direct source contexts != 3")
    need(p["correction_quarantine_claim_ids"]==sorted(KNOWN_BAD) and
         {x["claim_id"] for x in p_claims
          if x["historic_verdict"]=="CONTRADICTED"}==KNOWN_BAD and
         set(v5["cross_video"]["blocked_legacy_claim_ids"])==KNOWN_BAD,
         "two known contradictions wrongly reinstated")
    need({"NUMERIC"}<=set(probe_map[VIDEO+"-06"]["claim_type_obligations"])
         and {"NUMERIC","LEGAL_OR_PRODUCT"}<=set(
             probe_map[VIDEO+"-15"]["claim_type_obligations"]),
         "known math/tax contradiction undertested")

    blocks=p["current_pilot_unresolved"]
    need(len(blocks)>=4 and len({x["id"] for x in blocks})==len(blocks),
         "real pilot requires explicit material blockers")
    for b in blocks:
        need(b["claim_ids"] and set(b["claim_ids"])<=set(old_map),
             "unmapped blocker: "+b["id"])
        need(all(b.get(k) for k in ("missing_evidence","decision_blocked","reopen_when")),
             "unactionable blocker: "+b["id"])
    need({x["id"] for x in blocks}>=
         {"P001-SOURCE","P001-CLAIM","P001-MATH","P001-EMPIRICAL"},
         "real research gaps cannot be bypassed")
    need(set(p["research_domains"])==DOMAINS and
         all(v=="BLOCKED" for v in p["research_domains"].values()),
         "incomplete pilot falsely passed a research domain")
    need(p["result"]=="RESEARCH_BLOCKED"
         and p["certified_complete"] is False
         and p["personal_advice_approved"] is False
         and p["historical_research_preserved"] is True,
         "false completion or unauthorized advice")
    return {"video":1,"real_v3_claims":len(old_map),
            "v4_atomic_statements":q["v4_atomic_financial_statements"],
            "v5_direct_source_contexts":direct_context,
            "bounded_primary_sources":len(source_ids),
            "material_blockers":len(blocks),
            "legacy_external_open_unmapped":q["v5_legacy_external_open"],
            "known_contradictions_quarantined":len(KNOWN_BAD),
            "reproduced_synthetic_savings_krw":arithmetic,
            "completion":"RESEARCH_BLOCKED",
            "independent_real_media_or_empirical_truth_verified_in_this_pilot":False}

def load_repository(root):
    p=read(root/PILOT)
    docs={k:read(root/path) for k,path in p["source_paths"].items()}
    policy=read(root/POLICY)
    status=read(root/STATUS)
    return p,docs,policy,status

def validate_repo(root):
    p,d,policy,status=load_repository(root)
    return verify(p,d["v3"],d["v4_gold"],d["v4_signoff"],d["v5_closeout"],
                  policy,status,root)

def regression_tests(root):
    p,d,policy,status=load_repository(root)
    def rejects(pilot,docs=d,pol=policy,st=status):
        try:
            verify(pilot,docs["v3"],docs["v4_gold"],docs["v4_signoff"],
                   docs["v5_closeout"],pol,st,root)
        except (ValueError,KeyError,TypeError,IndexError):
            return
        raise ValueError("real #1 tampering was not blocked")
    trials=[]
    a=copy.deepcopy(p);a["claims"].pop();trials.append(a)
    a=copy.deepcopy(p);a["claims"][5]["historic_verdict"]="PRIMARY_CONFIRMED";trials.append(a)
    a=copy.deepcopy(p);a["claims"][5]["positive_advice_permitted"]=True;trials.append(a)
    a=copy.deepcopy(p);a["claims"][14]["pilot_outcome"]="EVIDENCE_LIMITED";trials.append(a)
    a=copy.deepcopy(p);a["denominator"]["v4_atomic_financial_statements"]=23;trials.append(a)
    a=copy.deepcopy(p);a["source_boundaries"]["full_semantic_review_in_v5"]=True;trials.append(a)
    a=copy.deepcopy(p);a["source_boundaries"]["independent_raw_srt_rehashed_in_this_pilot"]=True;trials.append(a)
    a=copy.deepcopy(p);a["denominator"]["v5_legacy_external_open"]=0;trials.append(a)
    a=copy.deepcopy(p);a["official_source_scope"].pop();trials.append(a)
    a=copy.deepcopy(p);a["verified_numerical_models_from_existing_v5"][0]["linked_claim_ids"]=[VIDEO+"-15"];trials.append(a)
    a=copy.deepcopy(p);a["result"]="RESEARCH_COMPLETE";trials.append(a)
    a=copy.deepcopy(p);a["current_pilot_unresolved"]=[];trials.append(a)
    a=copy.deepcopy(p);a["legacy_git_blob_shas"]["v3"]="0"*40;trials.append(a)
    a=copy.deepcopy(p);a["claims"][0]["v5_strategy_empirical_dataset_ids"]=["FAKE-BACKTEST"];trials.append(a)
    a=copy.deepcopy(p);a["research_domains"]["PRIMARY_EVIDENCE"]="PASS";trials.append(a)
    a=copy.deepcopy(p);a["claims"][12]["v5_primary_scope_refs"]=["NPS"];trials.append(a)
    a=copy.deepcopy(p);a["claims"][14]["claim_type_obligations"]=["QUALITATIVE"];trials.append(a)
    a=copy.deepcopy(p);a["denominator"]["v4_all_42_atomic_statements_independently_fact_verified"]=True;trials.append(a)
    for a in trials:rejects(a)
    # Also reject tampering with immutable legacy V5 in-memory.
    modified=copy.deepcopy(d)
    modified["v5_closeout"]["source"]["cue_count"]=1194
    rejects(p,modified)
    modified=copy.deepcopy(d)
    modified["v4_signoff"]["qa"]["all_42_statements_independently_fact_verified"]=True
    rejects(p,modified)
    return {"real_video_001_passed_fail_closed_probe":True,
            "negative_mutations_rejected":len(trials)+2,
            "claims_reconciled":23,"atomic_denominator_preserved":42,
            "pilot_approved_complete":False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    root=args.root.resolve()
    result={"pilot":validate_repo(root)}
    if args.self_test:result["regression"]=regression_tests(root)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    try:main()
    except (ValueError,KeyError,TypeError,OSError,IndexError,OverflowError) as e:
        print(json.dumps({"pilot":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
