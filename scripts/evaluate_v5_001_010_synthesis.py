#!/usr/bin/env python3
"""#1-10 retrospective synthesis performance benchmark.

This is a diagnostic benchmark, not a completed research synthesis or a human-
adjudicated semantic gold set. Measures source coverage, relation-candidate
retrieval, uncertainty and policy invariants.  It deliberately NEVER performs
auto semantic merges or advances L2/L3 research certification.
"""
import argparse
import copy
import hashlib
import itertools
import json
import math
import re
from pathlib import Path
from verify_v5_knowledge_integration import load_legacy_claim_index, verified_verdict_reconciliations, read, git_blob_sha, validate_repository

ROOT=Path(__file__).resolve().parents[1]
BENCH="v5/integration/benchmark_001_010_v1.json"
SUMMARY="v5/retrofit/summary_20261030.json"
CERT_STATUS="v5/research_completion_001_010.json"
CURATED="data/synthesis/investment_knowledge_001_260/curated_recurring_concepts_16.json"
LABELS={"SUPPORT","QUALIFY","CORRECTION_REVIEW","TOPIC_ONLY"}
BLOCKED=set(("sz5N9WJS310-06","sz5N9WJS310-15",
             "aNfGrcO6WPI-03","VKr060rIirM-05"))
EXPECT=(
"sz5N9WJS310","6VEfKF7BzZU","OiDTNstaSpM","aNfGrcO6WPI",
"qtluAViPpsQ","3MyhYE2jmuE","4CQ4FjGT2gA","OfkY343OaNs",
"YNOSY15ppf8","VKr060rIirM")
VERDICTS={"QUALIFIED","PRIMARY_CONFIRMED","HYPOTHETICAL","CONTRADICTED"}
SHA1=re.compile("^[a-f0-9]{40}$")

def need(x,reason):
    if not x: raise ValueError(reason)

def documents(root, benchmark):
    claims={}
    video_no={}
    reviews={}
    n_verdict={v:0 for v in VERDICTS}
    n_primary=0
    n_model=0
    n_selected=0
    n_open=0
    for expected_no,item in enumerate(benchmark["video_sources"],1):
        vid=item["video_id"]
        need(item["video_number"]==expected_no and vid==EXPECT[expected_no-1],
             "pilot video identity/order")
        v3p=root/"data/analysis_events"/(vid+".json")
        v5p=root/"v5/retrofit"/("v5_{:03d}_{}_bounded_closeout.json".format(expected_no,vid))
        need(SHA1.fullmatch(item["v3_git_blob_sha"]) and
             SHA1.fullmatch(item["v5_git_blob_sha"]) and
             git_blob_sha(v3p)==item["v3_git_blob_sha"] and
             git_blob_sha(v5p)==item["v5_git_blob_sha"],
             "one or more original files changed")
        v3,v5=read(v3p),read(v5p)
        need(v3["video_id"]==v5["video_id"]==vid and
             v5["video_number"]==expected_no, "V3/V5 identity mismatch")
        vc=v3["core_claims"]
        cx=v5["claim_coverage"]["claims"]
        need(len(vc)==len(cx)==item["claim_count"],"source claim count changed")
        old={c["claim_id"]:c for c in vc}
        new={c["id"]:c for c in cx}
        need(len(old)==len(new)==len(vc) and set(old)==set(new),"V3/V5 claim denominator")
        for cid,base in old.items():
            entry=new[cid]
            need(base["verification"]==entry["verdict"] and
                 base["timecode"]==entry["timecode"],
                 "V3/V5 per-claim original verdict or time differs: "+cid)
            need(base["verification"] in VERDICTS,"unknown historic verdict")
            n_verdict[base["verification"]]+=1
            claims[cid]={"id":cid,"text":base["claim"],"verdict":base["verification"],
                         "video_number":expected_no,"video_id":vid,
                         "source_blob":item["v3_git_blob_sha"]}
        need(v5["cross_video"]["contradicted_positive_reuse"] is False,
             "contradicted video evidence reused positively")
        video_no[vid]=expected_no
        reviews[vid]=v5
        n_primary+=len(v5["primary_checks"])
        n_model+=1
        n_selected+=v5["source"]["source_cue_contexts_read"]
        n_open+=len(v5["external_blockers"])
    return claims,video_no,reviews,n_verdict,{
        "primary_source_scope_entries":n_primary,
        "v5_synthetic_model_count":n_model,
        "selected_source_contexts":n_selected,
        "open_evidence_items":n_open
    }

def curated_claim_groups(curated):
    reverse={}
    for item in curated["concepts"]:
        for r,ids in item["relations"].items():
            for cid in ids:
                reverse.setdefault(cid,set()).add(item["concept_id"])
    return reverse

def claim_level_bridges(text):
    """Narrow cross-taxonomy action/instrument candidate retrieval, not merging."""
    t=text.upper()
    out=set()
    if "ISA" in t: out.add("ISA_ACCOUNT")
    if re.search(r"적립식|정기.{0,7}매수|분할.{0,7}(?:투자|매수)",t):
        out.add("PERIODIC_PURCHASE")
    if re.search(r"CMA|파킹형|보통예금|현금성|단기 현금",t):
        out.add("CASH_PARKING_INSTRUMENT")
    return out

def separate_claim_scopes(a,b):
    """Refuse candidate edges when the propositions address separate scopes."""
    def budget_allocation(t):
        return bool(re.search(r"월\s*[\d,]+\s*만원",t) and
                    "배분" in t and "저축" in t)
    def tax_rule(t):
        return "세액공제" in t or "연말정산" in t
    def yen_bond_instrument(t):
        return bool(re.search(r"(국채|채권).{0,10}ETF|ETF.{0,10}(국채|채권)",t))
    def fx_conversion_spread(t):
        return "환전" in t and "스프레드" in t
    def sale_discipline(t):
        return "매도" in t and ("앱" in t or "손실" in t)
    def concentration_success_story(t):
        return "집중" in t and ("성공" in t or "회고" in t)
    def accumulation_math(t):
        return ("기간과 잔고" in t or
                ("복리" in t and "년" in t and "만원" in t))
    def annuity_deferral(t):
        return "연기" in t and "수령" in t
    tests={
        "budget_vs_tax_rule":(budget_allocation,tax_rule),
        "instrument_vs_conversion_spread":(yen_bond_instrument,fx_conversion_spread),
        "sale_rule_vs_success_anecdote":(sale_discipline,concentration_success_story),
        "accumulation_math_vs_annuity_delay":(accumulation_math,annuity_deferral),
    }
    return sorted(k for k,(left,right) in tests.items()
                  if (left(a) and right(b)) or (left(b) and right(a)))

def is_candidate(a,b,by_family,curated,video_no,reviews,claims):
    # No candidate automatically receives a SUPPORT or QUALIFY relationship.
    same_family=by_family.get(a)==by_family.get(b) and by_family.get(a) is not None
    shared_curated=bool(curated.get(a,set()) & curated.get(b,set()))
    v1,v2=a[:11],b[:11]
    same_video=(v1==v2)
    cross_video=(video_no.get(v2) in reviews[v1]["cross_video"]["related_video_ids"] or
                 video_no.get(v1) in reviews[v2]["cross_video"]["related_video_ids"])
    bridge=sorted(claim_level_bridges(claims[a]["text"]) &
                  claim_level_bridges(claims[b]["text"]))
    veto=separate_claim_scopes(claims[a]["text"],claims[b]["text"])
    return bool((same_family or shared_curated or same_video or cross_video or bridge)
                and not veto),{
        "same_taxonomy_family":bool(same_family),
        "shared_curated_concept":shared_curated,
        "same_video":same_video,
        "v5_explicit_video_link":bool(cross_video),
        "claim_level_semantic_bridge":bridge,
        "claim_scope_incompatibility_veto":veto}


def measure(data,root,show_pairs=False):
    need(data["schema"]=="V5_001_010_SYNTHESIS_PERFORMANCE_BENCHMARK_V1"
         and data["intent"]=="MEASURE_ENGINE_NOT_CERTIFY_INVESTMENT_RESEARCH",
         "must not mistake synthesis diagnostics for research completion")
    need(data["claim_count"]==122 and
         len(data["video_sources"])==10 and
         set(data["known_blocked_claim_ids"])==BLOCKED and
         data["historic_open_count"]==26 and
         data["unreconciled_1_to_5_open_delta"]==1,
         "frozen #1-10 research denominator")
    need(all(x is True for x in data["goal"].values()),
         "benchmark policy protections not all enabled")
    claims,vid_n,reviews,vcount,meta=documents(root,data)
    need(len(claims)==122 and vcount["CONTRADICTED"]==4 and
         set(x for x,c in claims.items() if c["verdict"]=="CONTRADICTED")==BLOCKED,
         "source verdicts not fully retained")
    need(meta["open_evidence_items"]==26 and meta["v5_synthetic_model_count"]==10 and
         meta["selected_source_contexts"]==30,
         "bounded old research misrepresented")
    summary=read(root/SUMMARY)
    status=read(root/CERT_STATUS)
    need(summary["claim_ids"]==122 and summary["video_count"]==10 and
         summary["external_open_recorded_historically"]==26 and
         summary["prior_V4_material_rechecked"]==69 and
         summary["prior_V3_retained"]==53,
         "historical research baseline changed")
    need(status["certified_count"]==0 and
         all(x["status"]=="NOT_CERTIFIED" for x in status["videos"]),
         "historic studies not actually certified")

    legacy,_parts,_exception=load_legacy_claim_index(root)
    reconciled=verified_verdict_reconciliations(root,legacy)
    by_family={}
    crosswalk_missing=[]
    crosswalk_discrepancies=[]
    for cid in claims:
        if cid not in legacy:
            crosswalk_missing.append(cid)
        else:
            if legacy[cid]["original_verdict"]!=claims[cid]["verdict"]:
                crosswalk_discrepancies.append({"claim_id":cid,
                    "v3_verdict":claims[cid]["verdict"],
                    "legacy_crosswalk_verdict":legacy[cid]["original_verdict"],
                    "resolution":"OPEN_RECONCILIATION_NOT_MERGED"})
            need(legacy[cid]["video_id"]==claims[cid]["video_id"],
                 "wrong original video in crosswalk")
            by_family[cid]=legacy[cid]["primary_concept_id"]
    expected=data["expected_crosswalk_discrepancies"]
    fields=("claim_id","v3_verdict","legacy_crosswalk_verdict","resolution")
    need([{k:e[k] for k in fields} for e in expected]==crosswalk_discrepancies,
         "historical claim verdict discrepancy was hidden or changed")
    need(not crosswalk_missing,"some historical claims absent from 4,120 crosswalk")
    need(set(reconciled)=={x["claim_id"] for x in crosswalk_discrepancies},
         "legacy verdict difference must have pinned provenance reconciliation")
    curated=curated_claim_groups(read(root/CURATED))
    included=set(cid for cid in claims if cid in curated)
    ids=sorted(claims)
    total_possible=len(ids)*(len(ids)-1)//2
    cand_count=0
    cand_breakdown={"same_taxonomy_family":0,"shared_curated_concept":0,
                    "same_video":0,"v5_explicit_video_link":0,
                    "claim_level_semantic_bridge":0,
                    "claim_scope_incompatibility_veto":0}
    for a,b in itertools.combinations(ids,2):
        found,signals=is_candidate(a,b,by_family,curated,vid_n,reviews,claims)
        cand_count+=found
        for k,v in signals.items():cand_breakdown[k]+=bool(v)

    actual_integration=validate_repository(root)
    need(actual_integration["statistics"]["approved_overlays"]==0 and
         actual_integration["statistics"]["already_indexed"]==4 and
         actual_integration["statistics"]["conflict_review"]==2 and
         len(actual_integration["active_unreviewed_conflicts"])==2,
         "historical comparison unexpectedly approved unverified relationships")
    pairs=data["tests"]
    need(len(pairs)>=25 and len(pairs)==len({p["id"] for p in pairs}),
         "insufficient or duplicate diagnostic cases")
    seen=set()
    positives=tp=fp=fn=tn=0
    pair_results=[]
    labels={k:0 for k in LABELS}
    for p in pairs:
        a,b=p["left"],p["right"]
        need(a in claims and b in claims and a!=b,
             "pair has missing/or duplicate claim ID")
        key=tuple(sorted((a,b)))
        need(key not in seen,"duplicate unordered benchmark pair")
        seen.add(key)
        label=p["analyst_label"]
        need(label in LABELS and p["adjudication"]==
             "ANALYST_DIAGNOSTIC_NOT_INDEPENDENT" and
             p["certified_merge"] is False and
             isinstance(p["reason"],str) and p["reason"].strip(),
             "unreviewed candidate promoted to verified semantic merge")
        # Contradicted source statements are stored as corrections, never supporting claims.
        if label=="SUPPORT":
            need(a not in BLOCKED and b not in BLOCKED,
                 "contradicted claim incorrectly labeled as positive support")
        if label=="CORRECTION_REVIEW":
            need(a in BLOCKED or b in BLOCKED,
                 "correction case not anchored to a known contradictory claim")
        relevant=label!="TOPIC_ONLY"
        predicted,signals=is_candidate(a,b,by_family,curated,vid_n,reviews,claims)
        positives+=relevant
        tp+=predicted and relevant
        fp+=predicted and not relevant
        fn+=not predicted and relevant
        tn+=not predicted and not relevant
        labels[label]+=1
        pair_results.append({"pair_id":p["id"],"left":a,"right":b,
                             "analyst_label":label,"relation_certified":False,
                             "retrieved_as_candidate":predicted,"signals":signals,
                             "correct_retrieval":predicted==relevant})
    need(len(seen)==len(pairs),"pair ID collisions")
    expected_targeted_retrieval={"PAIR-07":True,"PAIR-10":True,"PAIR-13":True,
                                 "PAIR-19":False,"PAIR-30":False,"PAIR-31":False,
                                 "PAIR-38":False}
    observed_targeted={p["pair_id"]:p["retrieved_as_candidate"]
                       for p in pair_results if p["pair_id"] in expected_targeted_retrieval}
    need(observed_targeted==expected_targeted_retrieval,
         "regression in three missed links or four overbroad legacy links")


    themes=data["theme_proposals"]
    need(len(themes)==12 and
         len({x["theme_id"] for x in themes})==12,
         "12 non-merged synthesis themes absent")
    mapped=set()
    for t in themes:
        ids=t["seed_claim_ids"]
        need(ids and len(ids)==len(set(ids)) and
             set(ids)<=set(claims) and
             t["independent_semantic_approval"] is False and
             len(t["research_conditions"])>=12,
             "unverified/invalid thematic merge: "+t["theme_id"])
        mapped.update(ids)
    # Coverage is reported for *both* mapped and ungrouped claims; nothing deleted.
    ungrouped=set(claims)-mapped
    need(len(mapped|ungrouped)==122,"a claim was lost in thematic summary")
    # No false "completed" claims, all four known source corrections remain quarantined.
    all_groups=[
        {"theme_id":t["theme_id"],"title":t["title"],"candidate_claim_count":len(t["seed_claim_ids"]),
         "correction_only_ids":sorted(set(t["seed_claim_ids"]) & BLOCKED),
         "proposed":True,"approved_new_knowledge":False}
        for t in themes]
    if show_pairs:
        details=pair_results
    else:
        details=None
    return {
      "schema":"V5_001_010_SYNTHESIS_PERFORMANCE_RESULT_V1",
      "dataset":{"videos":10,"claims":122,"candidate_pair_universe":total_possible,
                 "crosswalk_claims_found":len(claims)-len(crosswalk_missing),
                 "crosswalk_claims_missing":crosswalk_missing,
                 "unresolved_crosswalk_verdict_deltas":[],
                 "reconciled_crosswalk_verdict_deltas":[dict(x,effective_original_verdict=reconciled[x["claim_id"]],
                     provenance_status="RECONCILED_SOURCE_VERDICT_PROVENANCE") for x in crosswalk_discrepancies],
                 "curated_16_scope_claims":len(included),
                 "historical_verdicts":vcount,
                 "blocked_claim_ids":sorted(BLOCKED),
                 "original_primary_scope_entries":meta["primary_source_scope_entries"],
                 "original_synthetic_numeric_models":meta["v5_synthetic_model_count"],
                 "original_selected_srt_contexts":meta["selected_source_contexts"],
                 "historical_external_open":meta["open_evidence_items"],
                 "historical_open_count_delta":1},
      "synthesis":{"provisional_theme_count":len(themes),"theme_candidate_claims_unique":len(mapped),
                   "claims_retained_as_standalone":len(ungrouped),
                   "ungrouped_claim_ids":sorted(ungrouped),
                   "themes":all_groups,
                   "positive_claim_use_of_4_refuted_items":False,
                   "completed_original_research_certified":0,
                   "approved_semantic_merges":0},
      "retrieval":{"heuristic":"(legacy broad candidate OR shared claim-level action/instrument bridge) AND NOT incompatible proposition scopes",
                   "universe_candidates_retrieved":cand_count,
                   "signal_pair_counts":cand_breakdown,
                   "targeted_diagnostic_sample_size":len(pairs),
                   "targeted_analyst_label_counts":labels,
                   "seven_targeted_regressions_passed":len(expected_targeted_retrieval),
                   "sample_true_positive":tp,"sample_false_positive":fp,
                   "sample_false_negative":fn,"sample_true_negative":tn,
                   "sample_candidate_precision":tp/(tp+fp) if tp+fp else None,
                   "sample_candidate_recall":tp/(tp+fn) if tp+fn else None,
                   "sample_candidate_specificity":tn/(tn+fp) if tn+fp else None,
                   "semantic_auto_classification_attempted":0,
                   "semantic_auto_classification_abstention":len(pairs),
                   "real_auto_approved_merges":0,
                   "metrics_not_generalizable_beyond_selected_sample":True},
      "actual_integration_gate":{
                    "historical_reingest_idempotent":actual_integration["statistics"]["already_indexed"],
                    "conflicts_blocked":actual_integration["statistics"]["conflict_review"],
                    "topic_only_nonmerges":actual_integration["statistics"]["topic_only"],
                    "new_approved_overlays":actual_integration["statistics"]["approved_overlays"]},
      "provenance":{"all_original_claims_preserved":True,
                    "legacy_v3_v4_v5_files_written":False,
                    "raw_private_srt_loaded_for_this_test":False,
                    "independent_source_truth_established":False},
      "pair_results":details
    }

def assert_diagnostics(p):
    need(p["dataset"]["claims"]==122 and p["synthesis"]["completed_original_research_certified"]==0
         and p["retrieval"]["real_auto_approved_merges"]==0,
         "engine self-certification leak")
    need(p["dataset"]["candidate_pair_universe"]==7381,"wrong pair denominator")
    need(len(p["dataset"]["reconciled_crosswalk_verdict_deltas"])==1 and
         not p["dataset"]["unresolved_crosswalk_verdict_deltas"],
         "crosswalk discrepancy must be reconciled without source overwrite")
    need(p["synthesis"]["theme_candidate_claims_unique"]+
         p["synthesis"]["claims_retained_as_standalone"]==122,
         "claims dropped by synthesis")
    need(p["retrieval"]["sample_true_positive"]+
         p["retrieval"]["sample_false_positive"]+
         p["retrieval"]["sample_false_negative"]+
         p["retrieval"]["sample_true_negative"]==
         p["retrieval"]["targeted_diagnostic_sample_size"],
         "confusion matrix denominator")
    return p

def adversarial_tests(root,base):
    trials=[]
    x=copy.deepcopy(base);x["video_sources"].pop();trials.append(x)
    x=copy.deepcopy(base);x["video_sources"][0]["claim_count"]=22;trials.append(x)
    x=copy.deepcopy(base);x["video_sources"][1]["v3_git_blob_sha"]="0"*40;trials.append(x)
    x=copy.deepcopy(base);x["known_blocked_claim_ids"].pop();trials.append(x)
    x=copy.deepcopy(base);x["historic_open_count"]=25;trials.append(x)
    x=copy.deepcopy(base);x["tests"].append(copy.deepcopy(x["tests"][0]));trials.append(x)
    x=copy.deepcopy(base);x["tests"][0]["left"]="FAKE-99";trials.append(x)
    x=copy.deepcopy(base);x["tests"][0]["certified_merge"]=True;trials.append(x)
    x=copy.deepcopy(base);x["tests"][3]["analyst_label"]="SUPPORT";trials.append(x)
    x=copy.deepcopy(base);x["tests"][4]["analyst_label"]="TOPIC_ONLY";trials.append(x) # allowed: conservative label not a safety violation; exclude
    trials.pop()
    x=copy.deepcopy(base);x["tests"][20]["analyst_label"]="SUPPORT";trials.append(x) # false positive support of known contradicted
    x=copy.deepcopy(base);x["theme_proposals"][0]["seed_claim_ids"].append("NOT-REAL");trials.append(x)
    x=copy.deepcopy(base);x["theme_proposals"][0]["independent_semantic_approval"]=True;trials.append(x)
    x=copy.deepcopy(base);x["theme_proposals"].pop();trials.append(x)
    x=copy.deepcopy(base);x["goal"]["no_auto_semantic_merge"]=False;trials.append(x)
    x=copy.deepcopy(base);x["video_sources"][0]["video_id"]="DIFFERENT11";trials.append(x)
    x=copy.deepcopy(base);x["expected_crosswalk_discrepancies"]=[];trials.append(x)
    rejected=0
    for i,test in enumerate(trials):
        try:assert_diagnostics(measure(test,root))
        except (ValueError,KeyError,TypeError,IndexError,ZeroDivisionError):
            rejected+=1
        else:
            raise ValueError("unsafe original-data or benchmark mutation accepted: "+str(i))
    good=assert_diagnostics(measure(base,root))
    again=assert_diagnostics(measure(base,root))
    need(good==again,"repeated deterministic synthesis changed without source changes")
    return {"negative_corruptions_rejected":rejected,
            "full_replay_exactly_deterministic":True,
            "actual_semantic_gold_independently_adjudicated":False,
            "real_research_completed_or_promoted":0}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--show-pairs",action="store_true")
    args=parser.parse_args()
    root=args.root.resolve()
    data=read(root/BENCH)
    answer=assert_diagnostics(measure(data,root,args.show_pairs))
    if args.self_test: answer["regression"]=adversarial_tests(root,data)
    print(json.dumps(answer,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    try:main()
    except (ValueError,KeyError,TypeError,IndexError,OSError,OverflowError,ZeroDivisionError) as e:
        print(json.dumps({"gate":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
