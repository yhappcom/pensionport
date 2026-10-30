#!/usr/bin/env python3
"""#001 research work-driver: reuses real V3/V4/V5 provenance and scoped public evidence.
Does not ingest private SRT, assert all 42 atomic text is checked, or certify empirics.
Produce an actionable deterministic research queue. GitHub CI replays numeric probes.
"""
import argparse
import copy
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ATOMIC="v5/research_progress/v5_001_atomic_evidence_worklist_20261030.json"
MODELS="v5/research_progress/v5_001_models_20261030.json"
V3="data/analysis_events/sz5N9WJS310.json"
GOLD="data/synthesis/investment_knowledge_v4/reviews/v4_001_gold_pilot_manifest_20261029.json"
SIGNOFF="data/synthesis/investment_knowledge_v4/reviews/v4_001_final_srt_review_signoff_20261029.json"
V5="v5/retrofit/v5_001_sz5N9WJS310_bounded_closeout.json"
VIDEO="sz5N9WJS310"
SRC_IDS={"NPS_TOPUP","NPS_DELAY","NTS_PENSION","LAW_PENSION_ORDER",
         "LAW_PENSION_ELIGIBILITY","LAW_ISA","SEC_DISTRIBUTION"}
PREF={"NPS_TOPUP":"nps.or.kr","NPS_DELAY":"nps.or.kr","NTS_PENSION":"nts.go.kr",
      "LAW_PENSION_ORDER":"law.go.kr","LAW_PENSION_ELIGIBILITY":"law.go.kr",
      "LAW_ISA":"law.go.kr","SEC_DISTRIBUTION":"investor.gov"}
CODES={"MONTHLY_SAVINGS_EFFECTIVE","PENSION_DEFERRAL_STATIC","PENSION_BASIS_CEILING",
       "TOPUP_NOMINAL_RECOVERY","DISTRIBUTION_NAV_IDENTITY"}
REQUIRED_MODEL_LINKS={
"V5_001_SAVINGS_EFFECTIVE_ANNUAL":{"sz5N9WJS310-02","sz5N9WJS310-06"},
"V5_001_NPS_FIVE_YEAR_DEFERRAL_BREAK_EVEN":{"sz5N9WJS310-07","sz5N9WJS310-08"},
"V5_001_TAX_EXCLUDED_BASIS_BOUND":{"sz5N9WJS310-13","sz5N9WJS310-14",
                                    "sz5N9WJS310-15","sz5N9WJS310-16"},
"V5_001_TOPUP_SIMPLE_RECOVERY":{"sz5N9WJS310-01","sz5N9WJS310-03"},
"V5_001_DISTRIBUTION_NAV_NEUTRAL":{"sz5N9WJS310-02","sz5N9WJS310-15"}
}

def need(value, note):
    if not value: raise ValueError(note)

def read(p): return json.loads(p.read_text(encoding="utf-8"))

def must_str(d,k):need(type(d.get(k)) is str and bool(d[k].strip()),"empty "+k)

def independent_math(t, a):
    if t=="MONTHLY_SAVINGS_EFFECTIVE":
        principal=a["monthly"]; n=a["months"]; annual=a["annual_effective"]
        need(principal>=0 and type(n)==int and 1<=n<=1200 and annual>-1,
             "monthly savings assumptions invalid")
        r=(1+annual)**(1/12)-1
        balance=0.0
        for _ in range(n):
            balance=balance*(1+r)+principal
        return balance
    if t=="PENSION_DEFERRAL_STATIC":
        base=a["base_monthly"];months=a["months_deferred"];rate=a["rate_per_month"]
        need(base>0 and type(months)==int and 1<=months<=60 and 0<rate<=.01,
             "deferral domain")
        uplift=months*rate
        return {"delayed_monthly":base*(1+uplift),
                "foregone_months_equivalent":months,
                "catch_up_months_after_restart":months/uplift}
    if t=="PENSION_BASIS_CEILING":
        m=a["monthly_contribution"];n=a["contribution_months"]
        transfers=a["isa_transfers"]; each=a["isa_each"];w=a["withdrawal_monthly"]
        valuation=a["total_valuation"]
        need(m>0 and type(n)==int and type(transfers)==int
             and n>0 and transfers>=0 and each>=0 and w>0 and valuation>=0,
             "pension basis domain")
        possible=m*n+transfers*each
        return {"possible_basis_upper_bound":possible,
                "valuation_excess":valuation-possible,
                "basis_only_months":math.floor(possible/w),
                "claimed_16_year_months":192,
                "withdraw_16y":w*192,
                "basis_shortfall_for_16y":max(0,w*192-possible)}
    if t=="TOPUP_NOMINAL_RECOVERY":
        need(a["topup_amount"]>0 and a["incremental_monthly"]>0,"nominal recovery domain")
        return {"undiscounted_months_after_benefit_start":
                a["topup_amount"]/a["incremental_monthly"]}
    if t=="DISTRIBUTION_NAV_IDENTITY":
        nav=a["nav_before"];dist=a["distribution"]
        need(nav>=0 and 0<=dist<=nav,"distribution domain")
        return {"nav_after":nav-dist,"combined_nav_plus_cash":nav}
    raise ValueError("unapproved model "+str(t))

def approx(x,y):
    if isinstance(x,dict):
        need(isinstance(y,dict) and set(x)==set(y),"model output keys")
        for k,v in x.items():approx(v,y[k])
    else:
        need(type(x) in (int,float) and type(y) in (int,float) and
             math.isclose(x,y,rel_tol=1e-9,abs_tol=0.005),"model calculation differs")

def inspect(atomic,model,v3,gold,signoff,v5):
    need(atomic["schema"]=="V5_001_ATOMIC_EVIDENCE_WORKLIST_V1" and
         model["schema"]=="V5_001_RESEARCH_EXECUTABLE_MODELS_V1",
         "study record schema")
    need(atomic["video_id"]==model["video_id"]==v3["video_id"]==
         gold["video_id"]==signoff["video_id"]==v5["video_id"]==VIDEO,
         "provenance: video identity")
    need(atomic["source"]["private_atomic_artifact_loaded_this_cycle"] is False
         and atomic["source"]["atomic_wording_available_in_public_repo"] is False
         and atomic["release_status"]=="RESEARCH_BLOCKED",
         "unearned assertion that raw 42-atom transcript was loaded")
    need(atomic["source"]["private_original_srt_sha256"]==
         gold["source_srt_sha256"]==v5["source"]["source_sha256"],
         "original SHA provenance")
    need(atomic["atomic_count"]==42 and atomic["core_claim_count"]==23 and
         gold["confirmed"]["atomic_facts_audited"]==42 and
         signoff["based_on"]["atomic_financial_statements_screened"]==42,
         "atomic denominator")
    claims={c["claim_id"] for c in v3["core_claims"]}
    need(len(claims)==23,"V3 claim denominator")
    principals={p["principle_id"]:p for p in gold["principles"]}
    need(len(principals)==12,"12 V4 principles")
    signoff_backlinks={}
    for k,v in signoff["principle_provenance"].items():
        p="V4-001-"+k
        need(p in principals,"unrecognized K group")
        for atom in v["audit_atomic_ids"]:
            signoff_backlinks.setdefault(atom,[]).append(p)
    need(set(signoff_backlinks)=={"A"+str(n).zfill(2) for n in range(1,43)},
         "atomic ID A01-A42 coverage incomplete")
    atoms=atomic["atomic"]
    need(len(atoms)==42 and len({u["atomic_id"] for u in atoms})==42,
         "42 unique atoms missing")
    catalog={s["id"]:s for s in atomic["official_source_catalog"]}
    need(set(catalog)==SRC_IDS and len(atomic["official_source_catalog"])==7,
         "dated official evidence inventory incomplete")
    for sid,s in catalog.items():
        need(s["url"].startswith("https://") and PREF[sid] in s["url"].split("/")[2],
             "wrong official source origin")
        need(s["certifies_full_claim"] is False and
             s["independent_full_claim_approval"] is False and
             s["support_type"]=="NARROW_SCOPE_FACT_ONLY",
             "overstated official source conclusion")
        need(s["actual_section_read_on"]=="2026-10-30" and s["live_read_recorded_on"]=="2026-10-30",
             "dated source read not recorded")
        for key in ("section","excerpt","scope_note","scope"):
            must_str(s,key)
        need(set(s["claim_ids"])<=claims and s["claim_ids"],
             "source not connected to real V3 claim")
    source_use=set()
    for u in atoms:
        aid=u["atomic_id"]
        need(sorted(u["principle_ids"])==sorted(signoff_backlinks[aid]),
             "historical atomic K provenance tampered: "+aid)
        expected=set().union(*(set(principals[k]["legacy_claim_ids"])
                              for k in u["principle_ids"]))
        need(set(u["candidate_core_claim_ids"])==expected and
             u["candidate_core_claim_ids"],"atomic claim candidate provenance invented "+aid)
        need(set(u["candidate_core_claim_ids"])<=claims,
             "atomic linked to unknown V3 claim")
        need(u["source_provenance"]=="V4_SIGNOFF_ATOMIC_ID_TO_PRINCIPLE_ONLY"
             and u["status"]=="BLOCKED_ATOMIC_EVIDENCE_GRANULARITY"
             and u["exact_atomic_wording_verified_in_this_cycle"] is False
             and u["source_cue_range_verified_in_this_cycle"] is False
             and u["may_upgrade_to_complete"] is False,
             "historical atomic source silently upgraded "+aid)
        need(set(u["official_source_ids"])<=SRC_IDS and
             set(u["quantitative_model_ids"])==set() and
             u["empirical_dataset_ids"]==[],"fake atomic-level proof "+aid)
        need("candidate" in u["next_action"] or "exact" in u["next_action"],
             "missing reopening instruction "+aid)
        source_use.update(u["official_source_ids"])
    need(source_use==SRC_IDS-{"NTS_PENSION"} or
         source_use==SRC_IDS, "inconsistent group-to-public source mappings")
    need(model["all_models_hypothetical_and_non_empirical"] is True and
         model["empirical_dataset_records"]==[] and
         model["research_use"]=="BOUNDED_MECHANICAL_FACT_CHECK_ONLY",
         "synthetic research mislabeled empirical")
    ms=model["models"];need(len(ms)==model["model_count"]==len(CODES)==5
                          and len({x["id"] for x in ms})==5,"model inventory mismatch")
    need({x["id"] for x in ms}==set(REQUIRED_MODEL_LINKS),"expected five explicit models")
    s_count=0
    for x in ms:
        need(x["type"] in CODES and x["empirical"] is False,
             "unapproved empirical model")
        need(set(x["claim_ids"])==REQUIRED_MODEL_LINKS[x["id"]],
             "numeric proof incorrectly claimed for unrelated core IDs")
        must_str(x,"assumptions");must_str(x,"source_pedigree")
        need(isinstance(x["scenarios"],list) and x["scenarios"],"scenario missing")
        for sc in x["scenarios"]:
            calculated=independent_math(x["type"],sc["inputs"])
            approx(calculated,sc["expected"])
            s_count+=1
    need(model["scenarios"]==s_count==6,"number of scenarios incorrect")
    known={x["claim_id"] for x in v3["core_claims"]
           if x["verification"]=="CONTRADICTED"}
    need(known=={"sz5N9WJS310-06","sz5N9WJS310-15"},
         "historical contradiction set altered")
    return { "atomic_count":42, "core_claim_count":23, "principle_groups":12,
             "bounded_public_evidence":7, "dated_official_source_scopes":7,
             "reproduced_models":5, "reproduced_scenarios":6,
             "actual_empirical_datasets":0,
             "new_atomic_claims_fully_verified":0,
             "corrections_preserved":2,
             "study_status":"RESEARCH_BLOCKED"}

def work_plan(atomic, model):
    """Deterministic actionable followup queue, grouped to avoid 42 repeated AI sessions."""
    catalog={x["id"]:x for x in atomic["official_source_catalog"]}
    work=[]
    for i in range(1,13):
        k=f"V4-001-K{i:02d}"
        units=[x for x in atomic["atomic"] if k in x["principle_ids"]]
        if any(x["status"]!="BLOCKED_ATOMIC_EVIDENCE_GRANULARITY" for x in units):
            continue  # only verified atomic evidence should remove this job
        reusable=sorted(set(s for x in units for s in x["official_source_ids"]))
        claims=sorted(set(c for x in units for c in x["candidate_core_claim_ids"]))
        work.append({"task_id":f"REOPEN-{k}",
                     "priority":"P0" if i in (3,4,5,7,11) else "P1",
                     "atomic_ids":sorted(x["atomic_id"] for x in units),
                     "related_core_claim_ids":claims,
                     "reusable_scoped_public_evidence":reusable,
                     "why_blocked":"Exact 42-item atomic statement artifact and cue-specific truth review not loaded; existing K-to-core mapping is only a candidate.",
                     "next_proof":"Read private original atomic audit or SRT; identify precise quote/cue, verify each atomic financial statement using its applicable independent evidence.",
                     "estimated_external_dependency":"PRIVATE_ATOMIC_PROVENANCE"})
    work.append({"task_id":"PUBLIC_LEGAL_EVIDENCE_SCOPE",
                 "priority":"P0",
                 "reusable_scoped_public_evidence":sorted(catalog),
                 "next_proof":"Check for every material legal claim its current paragraph, effective date, exceptions and match to exact atomic wording; do not infer a full-claim pass from a source URL.",
                 "why_blocked":"Seven scoped official references exist, but private atomic text and comprehensive per-claim application proof remain open."})
    work.append({"task_id":"COMPARATIVE_CASHFLOW_AND_TAX",
                 "priority":"P0",
                 "reproducible_models":[x["id"] for x in model["models"]],
                 "next_proof":"Extend toy calculations to NPS deferral versus immediate benefit over common horizons and pension source-class withdrawal with tax credit/eligibility rules and realistic sensitivities.",
                 "why_blocked":"Five reproducible hypothetical models do not establish tax-optimized real outcomes."})
    work.append({"task_id":"EMPIRICAL_AND_CONTRACT_EVIDENCE",
                 "priority":"P1",
                 "actual_dataset_count":len(model["empirical_dataset_records"]),
                 "next_proof":"Acquire lawful, documented market/ETF total-return and insurance product cost/guarantee series for claims of investment performance superiority; compare risk/fees and selection bias, or retain non-comparable claims as conditional.",
                 "why_blocked":"Zero genuine historical datasets; synthetic return assumptions are not backtests."})
    work.append({"task_id":"REAL_VIDEO_SOURCE_CONFLICT",
                 "priority":"P0",
                 "next_proof":"If the original disputed audio/frames are accessible, verify exact year-7/10-year and 16-year tax-free slide/voice statements; continue to quarantine known mathematical and legal overstatements.",
                 "why_blocked":"V4 signoff records unresolved frame and audio dependence."})
    return sorted(work,key=lambda x:(x["priority"],x["task_id"]))

def mutation_tests(a,m,v3,g,s,v5):
    tests=[]
    x=copy.deepcopy(a);x["atomic"].pop();tests.append((x,m))
    x=copy.deepcopy(a);x["atomic"][0]["status"]="VERIFIED";tests.append((x,m))
    x=copy.deepcopy(a);x["atomic"][0]["exact_atomic_wording_verified_in_this_cycle"]=True;tests.append((x,m))
    x=copy.deepcopy(a);x["atomic"][0]["candidate_core_claim_ids"]=[];tests.append((x,m))
    x=copy.deepcopy(a);x["atomic"][3]["principle_ids"]=["V4-001-K11"];tests.append((x,m))
    x=copy.deepcopy(a);x["official_source_catalog"][0]["certifies_full_claim"]=True;tests.append((x,m))
    x=copy.deepcopy(a);x["official_source_catalog"][0]["url"]="https://example.org/fake";tests.append((x,m))
    x=copy.deepcopy(a);x["official_source_catalog"][1]["claim_ids"]=["FAKE"];tests.append((x,m))
    x=copy.deepcopy(a);x["source"]["private_atomic_artifact_loaded_this_cycle"]=True;tests.append((x,m))
    x=copy.deepcopy(a);x["release_status"]="RESEARCH_COMPLETE";tests.append((x,m))
    x=copy.deepcopy(m);x["empirical_dataset_records"]=[{"fake":1}];tests.append((a,x))
    x=copy.deepcopy(m);x["models"][0]["scenarios"][0]["expected"]+=12345;tests.append((a,x))
    x=copy.deepcopy(m);x["models"][1]["scenarios"][0]["inputs"]["rate_per_month"]=0.07;tests.append((a,x))
    x=copy.deepcopy(m);x["models"][2]["claim_ids"]=["sz5N9WJS310-02"];tests.append((a,x))
    for i,(t,u) in enumerate(tests):
        try:inspect(t,u,v3,g,s,v5)
        except (ValueError,KeyError,TypeError,IndexError,ZeroDivisionError):
            continue
        raise ValueError("unsafe evidence mutation passed "+str(i))
    return len(tests)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--plan",action="store_true")
    args=p.parse_args()
    root=args.root.resolve()
    a,m,v3,g,s,v5=[read(root/path) for path in (ATOMIC,MODELS,V3,GOLD,SIGNOFF,V5)]
    result=inspect(a,m,v3,g,s,v5)
    work=work_plan(a,m)
    result["open_research_work_groups"]=len(work)
    result["source_reopen_groups"]=len([x for x in work if x["task_id"].startswith("REOPEN-")])
    result["workflow_finds_next_research_tasks"]=True
    if args.self_test:result["negative_mutations_rejected"]=mutation_tests(a,m,v3,g,s,v5)
    if args.plan:result["next_tasks"]=work
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":
    try:main()
    except (ValueError,KeyError,TypeError,IndexError,ZeroDivisionError,OSError,OverflowError) as e:
        print(json.dumps({"status":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
