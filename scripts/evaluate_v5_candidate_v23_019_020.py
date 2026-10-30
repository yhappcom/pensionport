#!/usr/bin/env python3
"""Frozen V2.3 FIRST USE on #19/#20: preregistered 125 analyst cases.

Diagnostic labels were committed before evaluating V2.3 on #19+#20.
They are NOT independently blinded or probability-sampled gold labels.
Historical 344 V2.3 development cases are never mixed with first-use scores.
"""
import argparse
import itertools
import json
from collections import Counter
from pathlib import Path

from evaluate_v5_001_010_synthesis import read,need,git_blob_sha
from evaluate_v5_candidate_v23 import (
    source_contract_v23,
    evaluate as v23_dev,
)
from v5_candidate_engine_v23 import retrieve_claims as v23_retrieve
from v5_candidate_engine_v22_guarded import retrieve_claims as v22_retrieve
from verify_v5_knowledge_integration import (
    load_legacy_claim_index,
    verified_verdict_reconciliations,
)

ROOT=Path(__file__).resolve().parents[1]
BENCH="v5/integration/benchmark_019_020_v23_first_use_v1.json"
FROZEN="v5/integration/v23_development_001_018_v1.json"
ORIGINAL_18="v5/integration/v22_first_use_017_018_results_v1.json"
SNAPSHOT="v5/integration/v23_first_use_019_020_results_v1.json"
EXPECTED_BENCH_SHA="37abfcff9e6fa60341abf1a201e463693c02f29f"
V23_SHA="be73e778b7851ba440e40c85629f2f89b6da3648"
V23_EVAL_SHA="c4fe1df36c8dc8ed59003a1d1ad23c27f959bb5c"
V22_SHA="c0608b316c446c8391d68e9fc25d6173ceba971a"
ORIGINAL_17_18_RESULT_SHA="95da7fc873734a91f6c9f18340925f18e2a53de3"
CLAIM_VIDEOS={19:"zi9x_q2fYoc",20:"inLlZgtS7qs"}
EVENT_BLOBS={
 "zi9x_q2fYoc":"8fbb48dbff06389f69223fdcbdc94241b960d3e4",
 "inLlZgtS7qs":"2f4970972f3dc8a9144c001f4e1a8c3a18e553fa",
}
SRT_HASHES={
 "zi9x_q2fYoc":"e7284caf3d5cee58a202ad29e88a39c57973d5f181dda018f47852a9f23200f3",
 "inLlZgtS7qs":"c563107dd5479eba7b36e3b7ead388ed74d8ef5bb2c4207e616396749c9d5b77",
}
CUES={"zi9x_q2fYoc":1134,"inLlZgtS7qs":31}
CLAIM_COUNTS={"zi9x_q2fYoc":12,"inLlZgtS7qs":6}
NEW_REFUTED={"zi9x_q2fYoc-12"}
LABELS={"QUALIFY","CORRECTION_REVIEW","TOPIC_ONLY"}
VERDICTS={"PRIMARY_CONFIRMED","QUALIFIED","CONTRADICTED",
          "HYPOTHETICAL","SPEAKER_OPINION"}
GROUPS={"NEW19":60,"NEW20":40,"CROSS19-20":25}

def prepare(root):
    b=read(root/BENCH)
    need(git_blob_sha(root/BENCH)==EXPECTED_BENCH_SHA,
         "preregistered #19-20 diagnoses were edited after first-use freeze")
    frozen=read(root/FROZEN)
    need(frozen["schema"]=="V5_CANDIDATE_V23_FROZEN_RETROSPECTIVE_DEVELOPMENT_V1"
         and frozen["engine_git_blob_sha"]==V23_SHA
         and frozen["evaluator_git_blob_sha"]==V23_EVAL_SHA
         and frozen["new_unseen_videos_since_v23_freeze"]==0
         and frozen["next_unseen_validation_video_number"]==19
         and frozen["production_release"].startswith("BLOCKED"),
         "frozen V2.3 baseline pre-registration contract invalid")
    for p,sha in (
        ("scripts/v5_candidate_engine_v23.py",V23_SHA),
        ("scripts/evaluate_v5_candidate_v23.py",V23_EVAL_SHA),
        ("scripts/v5_candidate_engine_v22.py",V22_SHA),
        (ORIGINAL_18,ORIGINAL_17_18_RESULT_SHA),
    ):
        need(git_blob_sha(root/p)==sha,
             "immutable V2.3/V2.2 parent source or original first-use changed: "+p)
    need(b["schema"]=="V5_CANDIDATE_V23_FIRST_USE_019_020_PREREGISTERED_DIAGNOSTIC_V1"
         and b["frozen_engine_git_blob_sha"]==V23_SHA
         and b["frozen_evaluator_git_blob_sha"]==V23_EVAL_SHA
         and b["dev_snapshot"]==FROZEN
         and b["prior_video_count"]==18 and b["prior_claim_count"]==194
         and b["new_video_count"]==2 and b["new_claim_count"]==18
         and b["total_video_count"]==20 and b["total_claim_count"]==212
         and b["possible_pairs"]==22366
         and b["new_involving_pairs"]==3645
         and b["diagnostic_count"]==125 and len(b["tests"])==125
         and b["group_sizes"]==GROUPS
         and b["positive_expected"]==69 and b["negative_expected"]==56
         and len(b["new_video_sources"])==2
         and b["primary_audio_checked_during_this_test"] is False,
         "new-video preregistration metrics, labels or source policy changed")
    old,old_cases=source_contract_v23(root)
    need(len(old)==194 and len(old_cases)==344
         and frozen["development"]["total_confusion"]==
         {"TP":219,"FN":0,"FP":0,"TN":125}
         and frozen["universe"]["v23_candidate_pairs"]==2675,
         "frozen V2.3 344-case development baseline changed")
    claims=dict(old)
    idx=read(root/"data/subtitles/content_index_001_070.json")["items"]
    new_sources={x["number"]:x for x in b["new_video_sources"]}
    need(set(new_sources)=={19,20},"missing #19/20 provenance")
    for num,id in CLAIM_VIDEOS.items():
        x=new_sources[num];p=f"data/analysis_events/{id}.json"
        need(x["id"]==id and x["event_path"]==p and
             x["event_git_blob_sha"]==git_blob_sha(root/p)==EVENT_BLOBS[id] and
             x["registered_srt_sha256"]==SRT_HASHES[id]==idx[id]["subtitle_sha256"] and
             x["srt_cues"]==CUES[id]==idx[id]["cue_count"] and
             idx[id]["roster_no"]==num and
             x["claim_count"]==CLAIM_COUNTS[id],
             "new source event/SRT fingerprint/roster mismatch")
        src=read(root/p)
        need(src["video_id"]==id
             and src["approval"]=="APPROVED"
             and src["evidence_gate"]["source_checked"] is True
             and src["evidence_gate"]["source_fingerprint"]==SRT_HASHES[id]
             and len(src["core_claims"])==CLAIM_COUNTS[id]
             and {c["claim_id"] for c in src["core_claims"]
                  if c["verification"]=="CONTRADICTED"}==set(x["contradicted_claim_ids"])
             and (set(x["contradicted_claim_ids"])==NEW_REFUTED if num==19
                  else not x["contradicted_claim_ids"]),
             "new educational-source claim provenance/verification mismatch")
        for rec in src["core_claims"]:
            cid=rec["claim_id"]
            need(cid.startswith(id+"-") and cid not in claims and
                 rec["verification"] in VERDICTS and
                 rec["claim"] and rec["timecode"] and rec["source_precision"],
                 "new source claim lacks record, timecode, verdict or original ID")
            claims[cid]={
                "id":cid,"text":rec["claim"],
                "verdict":rec["verification"],
                "video_id":id,"video_number":num}
    need(len(claims)==212
         and {cid for cid,c in claims.items()
              if c["verdict"]=="CONTRADICTED"}==
             {cid for cid,c in old.items()
              if c["verdict"]=="CONTRADICTED"}|NEW_REFUTED,
         "source universe or original refutations changed")
    legacy,_,_=load_legacy_claim_index(root)
    verified_verdict_reconciliations(root,legacy)
    need(all(cid in legacy and
             legacy[cid]["video_id"]==c["video_id"] and
             legacy[cid]["original_verdict"]==c["verdict"]
             for cid,c in claims.items() if c["video_number"]>=19),
         "new study claims do not reconcile with original canonical ledger")
    names=set();pairs=set();groups=Counter()
    for t in b["tests"]:
        a_id,b_id=t["left"],t["right"]
        need(t["id"] not in names and
             (a_id,b_id) not in pairs and
             len(t["rationale"])>=15 and
             t["analyst_label"] in LABELS and
             t["independent_blinded_gold"] is False and
             t["automatic_approval"] is False and
             a_id in claims and b_id in claims and a_id!=b_id,
             "duplicate, invalid or falsely blinded registration")
        names.add(t["id"]);pairs.add((a_id,b_id))
        a,brow=claims[a_id],claims[b_id]
        if t["id"].startswith("NEW19-"):
            grp="NEW19"
            need(a["video_number"]==19 and brow["video_number"]<=18,
                 "NEW19 must compare genuinely new source with prior studies")
        elif t["id"].startswith("NEW20-"):
            grp="NEW20"
            need(a["video_number"]==20 and brow["video_number"]<=18,
                 "NEW20 must compare genuinely new source with prior studies")
        elif t["id"].startswith("CROSS19-20-"):
            grp="CROSS19-20"
            need(a["video_number"]>=19 and brow["video_number"]>=19,
                 "new-new comparisons must include only #19/#20")
        else:raise ValueError("UNKNOWN_PRE_REGISTERED_HOLDOUT_GROUP")
        groups[grp]+=1
        if t["analyst_label"]=="CORRECTION_REVIEW":
            need("CONTRADICTED" in (a["verdict"],brow["verdict"]),
                 "registered correction relation without historical refutation")
        if "CONTRADICTED" in (a["verdict"],brow["verdict"]):
            need(t["analyst_label"]!="QUALIFY",
                 "historically refuted statement promoted into positive support")
    need(dict(groups)==GROUPS,
         "new #19/20 and within-video diagnostic sampling was modified")
    return claims,b["tests"]

def conf_metrics(c):
    def ratio(n,d):return round(n/d,6) if d else None
    return {"precision":ratio(c["TP"],c["TP"]+c["FP"]),
            "recall":ratio(c["TP"],c["TP"]+c["FN"]),
            "specificity":ratio(c["TN"],c["TN"]+c["FP"])}

def run(root,show_cases=False):
    claims,cases=prepare(root)
    groups={k:{j:0 for j in ("TP","FP","FN","TN")} for k in GROUPS}
    baseline={j:0 for j in ("TP","FP","FN","TN")}
    rows=[]
    for t in cases:
        a,b=claims[t["left"]],claims[t["right"]]
        got,why=v23_retrieve(a,b)
        old,oldwhy=v22_retrieve(a,b)
        positive=t["analyst_label"]!="TOPIC_ONLY"
        cell=("TP" if got else "FN") if positive else ("FP" if got else "TN")
        oldcell=("TP" if old else "FN") if positive else ("FP" if old else "TN")
        grp=("NEW19" if t["id"].startswith("NEW19-") else
             "NEW20" if t["id"].startswith("NEW20-") else "CROSS19-20")
        groups[grp][cell]+=1
        baseline[oldcell]+=1
        need(why["review_only"] is True and
             why["source_provenance_required"] is True and
             why["automatic_knowledge_approval"] is False and
             why["automatic_merge_permitted"] is False and
             why["candidate_is_evidence_of_claim_truth"] is False and
             why["semantic_relation_prediction"] is None and
             why["investment_trade_instruction_permitted"] is False and
             why["research_completion_certificate_permitted"] is False and
             why["correction_only"]==
                 ("CONTRADICTED" in (a["verdict"],b["verdict"])),
             "source-aware candidate was falsely upgraded")
        rows.append({
            "id":t["id"],"left":t["left"],"right":t["right"],
            "label":t["analyst_label"],"v23_candidate":bool(got),
            "v23_confusion":cell,"v22_candidate":bool(old),
            "v22_confusion":oldcell,
            "v23_bridges":why["v23_bridges"],
            "v23_scope_blocks":why["v23_scope_blocks"],
            "v22_scope_blocks":why["v23_inherited_scope_blocks"],
            "source_risk":why["source_risk"],
            "correction_only":why["correction_only"],
            "auto_merge":False
        })
    need({k:sum(v.values()) for k,v in groups.items()}==GROUPS,
         "first-use diagnostic groups incomplete")
    all_v23=new_v23=new_v22=new_possible=refuted_new=hypo_new=0
    bridge_counter=Counter();hubs=Counter();origins=Counter()
    for aid,bid in itertools.combinations(sorted(claims),2):
        a,b=claims[aid],claims[bid]
        hit,why=v23_retrieve(a,b)
        all_v23+=int(hit)
        if a["video_number"]>=19 or b["video_number"]>=19:
            new_possible+=1
            old,oldwhy=v22_retrieve(a,b)
            new_v23+=int(hit);new_v22+=int(old)
            if hit:
                bridge_counter.update(why["v23_bridges"])
                if a["video_number"]>=19:hubs[aid]+=1
                if b["video_number"]>=19:hubs[bid]+=1
                refuted_new+=int(why["source_risk"]=="CORRECTION_ONLY")
                hypo_new+=int(why["source_risk"]=="UNREPLICATED_HYPOTHETICAL_SOURCE")
                origins["inherited_v22" if old else "added_v23"]+=1
            elif old:origins["blocked_v22"]+=1
    need(new_possible==3645 and len(claims)*(len(claims)-1)//2==22366,
         "entire 212-claim/new-18-claim possible pair census drift")
    group_scores={k:{"confusion":v,**conf_metrics(v)}
                  for k,v in groups.items()}
    total={k:sum(v[k] for v in groups.values())
           for k in ("TP","FP","FN","TN")}
    return {
        "schema":"V5_CANDIDATE_V23_FIRST_USE_019_020_RESULT_V1",
        "assessment_kind":"FROZEN_FIRST_USE_NOT_BLINDED_OR_REPRESENTATIVE",
        "source_audio_and_frames_rechecked_in_this_run":False,
        "new_video_numbers":[19,20],
        "new_claim_count":18,
        "cumulative_videos":20,"cumulative_claims":212,
        "new_refuted_correction_only_claims":sorted(NEW_REFUTED),
        "development_baseline_1_to_18":{
            "cases":344,"confusion":{"TP":219,"FN":0,"FP":0,"TN":125},
            "classification":"IN_SAMPLE_RETROSPECTIVE_NOT_HOLDOUT"},
        "diagnostic":{
            "case_count":125,"confusion":total,**conf_metrics(total),
            "by_group":group_scores,
            "v22_same_new_pairs_confusion":baseline,
            "v22_same_new_pairs_metrics":conf_metrics(baseline),
            "independently_blinded":False,
            "probability_sampled":False,
            "population_generalizable":False,
        },
        "universe":{
            "all_possible_pairs":22366,
            "new_videos_involving_possible_pairs":new_possible,
            "v23_all_candidate_pairs":all_v23,
            "v23_new_involving_candidates":new_v23,
            "v22_new_involving_candidates":new_v22,
            "v23_new_source_refuted_candidates_correction_only":refuted_new,
            "v23_new_source_hypothetical_candidates_review_only":hypo_new,
            "candidate_origin_new_involving":dict(origins),
            "candidate_degree_new_claims":dict(sorted(hubs.items())),
            "top_new_anchors":bridge_counter.most_common(20),
        },
        "case_results":rows if show_cases else None,
        "errors":[z for z in rows if z["v23_confusion"] in ("FP","FN")],
        "automatic_knowledge_merges":0,
        "automatic_evidence_completion_certificates":0,
        "automatic_trade_advice":0,
        "release_gate":"BLOCKED_PENDING_INDEPENDENT_HUMAN_REVIEW_AND_OFFICIAL_FINANCIAL_SOURCE_COMPLETION",
    }

def adversarial(root):
    claims,tests=prepare(root)
    checked=0
    for t in tests:
        a,b=claims[t["left"]],claims[t["right"]]
        hit,why=v23_retrieve(a,b)
        rev,other=v23_retrieve(b,a)
        need(hit==rev and
             why["correction_only"]==other["correction_only"] and
             why["source_risk"]==other["source_risk"],
             "new #19/#20 pair order or source risk not symmetric")
        checked+=1
    x=next(c for c in claims.values() if c["video_number"]==19)
    y=next(c for c in claims.values() if c["video_number"]==20)
    bad=[
        dict(x,verdict=None),dict(x,verdict="TRUE"),
        dict(x,id="bad"),dict(x,video_id="INVALID"),
        dict(x,video_number=0),dict(x,video_number=True),
        dict(x,text=None),dict(x,text="")
    ]
    rejected=0
    for z in bad:
        try:v23_retrieve(z,y)
        except (ValueError,TypeError):rejected+=1
        else:raise ValueError("unsafe malformed source accepted")
    need(rejected==8 and checked==125,
         "incomplete provenance-adversarial test coverage")
    first=run(root)
    need(first==run(root),"full 22366-pair first-use replay nondeterministic")
    return {"source_metadata_mutations_rejected":rejected,
            "pair_order_symmetric_cases":checked,
            "full_22366_pair_double_replay_deterministic":True,
            "new_refuted_claim_count":1,
            "automatic_merges":0}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--show-cases",action="store_true")
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--assert-snapshot",action="store_true")
    args=p.parse_args()
    root=args.root.resolve()
    res=run(root,args.show_cases)
    if args.self_test:res["negative_tests"]=adversarial(root)
    if args.assert_snapshot:
        freeze=read(root/SNAPSHOT)
        for key in ("diagnostic","universe","development_baseline_1_to_18",
                    "new_refuted_correction_only_claims","release_gate"):
            need(freeze[key]==res[key],"frozen V2.3 first-use output changed: "+key)
        rows=res["case_results"] if args.show_cases else run(root,True)["case_results"]
        need(freeze["case_results"]==rows and
             freeze["automatic_knowledge_merges"]==0,
             "frozen 125 cases or auto-approval restriction changed")
    print(json.dumps(res,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    try:main()
    except (ValueError,TypeError,KeyError,IndexError,OSError) as exc:
        print(json.dumps({"gate":"FAIL","error":str(exc)},ensure_ascii=False))
        raise SystemExit(1)
