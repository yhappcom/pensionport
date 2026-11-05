"""Bounded QA of original #1~#5 SRT vs research/advice knowledge.

No external LLM API or personal-order execution. The 25 ChatGPT-reviewed
risk cases are explicitly a high-risk selected (NOT blind or recall measured)
sample. Optional private ZIP reproduces each source span SHA256; CI can only
check the recorded ledger, source IDs, audit classification and fail-closed
research state without access to private source bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urlparse

from .first_five_source_readiness_gate import inspect_source_zip

FILE=Path("ire/v5/validation/first_five_original_qa_25_20261105.json")
MANIFEST=Path("ire/v5/validation/first_five_source_manifest_20261105.json")
PUBLIC_STATE=Path("ire/v5_app/batch_states/v5-gomhee-001-005-batch.json")
MASTER=Path("ire/v5/legacy_consolidation/master_index_20261105.json")
ROUTES=Path("ire/v5/advisory_integration/decision_routes_20261105.json")

class ResearchQualityError(ValueError):
    pass

def require(value:bool, code:str)->None:
    if not value:
        raise ResearchQualityError(code)

def read(root:Path,path:Path)->dict:
    return json.loads((Path(root)/path).read_text("utf-8"))

def _case_digest(data:bytes,first:int,last:int)->str:
    text=data.decode("utf-8-sig").replace("\r\n","\n").replace("\r","\n").strip()
    blocks=re.split(r"\n[ \t]*\n",text)
    # SRT timestamps and cue numbering have already been byte reverified by
    # inspect_source_zip; this routine derives a safe hash without publishing.
    cues=[]
    for i in range(first,last+1):
        lines=[z.strip() for z in blocks[i-1].split("\n") if z.strip()]
        require(len(lines)>=3 and int(lines[0])==i,
                "QA_ORIGINAL_CUE_NUMBER_CHANGED")
        cues.append(str(i)+"|"+" ".join(lines[2:]).strip())
    return hashlib.sha256("\n".join(cues).encode("utf-8")).hexdigest()

def verify(root:Path, source_zip:Path|None=None,
           ledger:dict|None=None)->dict:
    root=Path(root)
    q=read(root,FILE) if ledger is None else ledger
    m=read(root,MANIFEST)
    p=read(root,PUBLIC_STATE)
    master=read(root,MASTER)
    clauses=(root/"data/claims.jsonl").read_text("utf-8").splitlines()
    claims=[json.loads(x) for x in clauses if x.strip()]
    routes=read(root,ROUTES)
    need_ids=[f"F{i:02d}" for i in range(1,26)]
    expected_vids=[x["video_id"] for x in m["videos"]]
    require(
        q.get("schema")=="IRE_V5_FIRST_FIVE_ORIGINAL_QA_V1"
        and q.get("date")=="2026-11-05"
        and q.get("source_archive")=="1-70.zip"
        and q.get("source_zip_sha256")==
           "00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd"
        and q.get("original_srt_verified_files")==5
        and q.get("original_srt_total_cues")==5129
        and q.get("original_srt_structural_cues_verified")==5129
        and q.get("previous_public_batches_total_windows")==288
        and q.get("previous_public_batches_processed_windows")==5
        and q.get("previous_public_batches_unreviewed_windows")==283
        and q.get("focused_cases")==q.get("focused_qa_case_count")==25
        and q.get("focused_span_reviewed_is_corpus_complete") is False
        and q.get("focused_distinct_cues_touched")==892
        and q.get("source_span_hash_algorithm")==
            "SHA256_UTF8_JOIN_NEWLINE_OF_CUE_NUMBER_PIPE_STRIPPED_TEXT"
        and q.get("financial_fact_approvals_created")==0
        and q.get("personalized_advice_approvals_created")==0
        and q.get("research_full_quality_approved") is False
        and q.get("next_five_video_expansion_authorized") is False
        and q.get("independent_human_evaluator_used") is False
        and q.get("full_video_semantic_recall_measured") is False
        and q.get("advisory60_path_contains_C62_C64") is False
        and q.get("prior_B04_pending") is True
        and q.get("core_60_claim_pilot_video_source_directly_connected")==0
        and q.get("quality_verdict")==
           "NO_GO_FULL_RESEARCH_QUALITY_25_SOURCE_ANCHORED_RISKS_AND_MISSING_INTEGRATION",
        "QA_FALSE_CORPUS_COMPLETION_OR_SOURCE_PROVENANCE")
    require(p["windows_total_reported"]==288
            and p["windows_processed_reported"]==5
            and p["windows_remaining_reported"]==283
            and p["all_five_videos_research_complete"] is False,
            "QA_PUBLIC_BATCH_ALREADY_CHANGED")
    require(master["batches"][3]["batch_id"]=="B04"
            and master["batches"][3]["state"]=="PENDING_DETAILED_RECONCILIATION"
            and master["summary"]["legacy_claims_detailed_triaged"]==60,
            "QA_CORE_RESEARCH_PROGRESS_CHANGED")
    route_text=json.dumps(routes,ensure_ascii=False)
    require(not any(x in route_text for x in ("GOMHEE-C62","GOMHEE-C63","GOMHEE-C64")),
            "QA_PILOT_LEGACY_CLAIMS_ALREADY_ROUTE_BOUND")
    expected_claims={}
    for id in expected_vids:
        expected_claims[id]=sorted(x["claim_id"] for x in claims
                                 if id in x.get("supporting_videos",[]))
    require([expected_claims[x] for x in expected_vids]==[
            [],[],["GOMHEE-C64"],["GOMHEE-C63"],["GOMHEE-C62"]],
            "QA_OLD_LEDGER_VIDEO_DIRECT_LINK_DIFFERENT")
    catalog=q.get("official_evidence_catalog",[])
    lookup={x["id"]:x for x in catalog}
    require(len(catalog)==len(lookup)==6
            and all(x.get("live_web_checked_in_active_chat") is True
                    and x.get("source_issuer_independent_of_video_creator") is True
                    and x.get("current_rule_application_to_person_approved") is False
                    and len(x.get("limited_verified_scope",""))>=14
                    and urlparse(x.get("url","")).scheme=="https"
                    and urlparse(x["url"]).hostname for x in catalog),
            "QA_OFFICIAL_PROVENANCE_UNVERIFIED_OR_FAKED")
    cases=q.get("cases",[])
    require(len(cases)==25
            and [x.get("id") for x in cases]==need_ids,
            "QA_REVIEW_CASE_COUNT_OR_ORDER")
    summary={}
    covered=set()
    actual_linked={}
    for x in cases:
        index=x.get("video_number")
        require(type(index)==int and 1<=index<=5
                and x.get("video_id")==expected_vids[index-1]
                and type(x.get("first_cue"))==int
                and type(x.get("last_cue"))==int
                and 1<=x["first_cue"]<=x["last_cue"]<=m["videos"][index-1]["expected_cues"],
                "QA_CASE_SOURCE_ID_OR_SPAN_MISMATCH")
        require(re.fullmatch("[0-9a-f]{64}",str(x.get("original_normalized_span_sha256","")))
                and x.get("source_original_fidelity_spot_reviewed") is True
                and x.get("personal_advice_approved") is False
                and x.get("official_financial_fact_automatically_approved") is False
                and x.get("release_state")=="FOCUSED_QA_RISK_RECORDED_NOT_FACT_PROMOTED"
                and x.get("severity") in ("CRITICAL","HIGH","MEDIUM")
                and len(x.get("observed_risk_or_claim",""))>=10
                and len(x.get("safe_advisory_restriction",""))>=22,
                "QA_UNANCHORED_OR_AUTO_APPROVED_FINANCIAL_CLAIM")
        require(x.get("official_crosscheck_id") is None
                or x["official_crosscheck_id"] in lookup,
                "QA_UNKNOWN_OR_FABRICATED_OFFICIAL_SOURCE")
        expected=expected_claims[x["video_id"]]
        if index<=2:
            require(x.get("legacy_claim_id") is None,
                    "QA_FALSE_DIRECT_CORE_LINK")
        else:
            require(x.get("legacy_claim_id") in expected,
                    "QA_WRONG_LEGACY_VIDEO_CLAIM")
        covered.update((index,n) for n in range(x["first_cue"],x["last_cue"]+1))
        summary[index]=summary.get(index,0)+1
    require(sorted(summary.items())==[(1,5),(2,5),(3,5),(4,5),(5,5)]
            and len(covered)==892
            and q.get("critical_risk_cases")==
               sum(x["severity"]=="CRITICAL" for x in cases)
            and q.get("critical_risk_cases")==6,
            "QA_CASE_DISTRIBUTION_OR_COUNT_MISMATCH")
    if source_zip is None:
        raw={"private_archive_reopened_in_this_gate":False,
             "private_25_span_hashes_byte_rechecked_in_this_gate":False,
             "private_25_span_hashes_matching":None}
    else:
        raw_path=Path(source_zip)
        require(raw_path.is_file(),"QA_PRIVATE_ARCHIVE_ABSENT")
        require(hashlib.sha256(raw_path.read_bytes()).hexdigest()==q["source_zip_sha256"],
                "QA_PRIVATE_ARCHIVE_SHA256_MISMATCH")
        proof=inspect_source_zip(raw_path,m["videos"])
        require(proof["all_five_original_srt_byte_integrity_verified"],
                "QA_PRIVATE_FIVE_SOURCE_REVERIFY_FAILED")
        n=0
        with zipfile.ZipFile(raw_path) as z:
            for x in cases:
                sid=x["video_id"]
                found=[y for y in z.namelist() if y.endswith("/youtube-transcript-"+sid+".srt")
                       or y=="youtube-transcript-"+sid+".srt"]
                require(len(found)==1,"QA_PRIVATE_SRT_NOT_UNIQUE")
                if _case_digest(z.read(found[0]),x["first_cue"],x["last_cue"])!=x["original_normalized_span_sha256"]:
                    raise ResearchQualityError("QA_PRIVATE_SOURCE_SPAN_MISMATCH_"+x["id"])
                n+=1
        raw={"private_archive_reopened_in_this_gate":True,
             "private_25_span_hashes_byte_rechecked_in_this_gate":True,
             "private_25_span_hashes_matching":n}
    return {
        "schema":"IRE_V5_FIVE_SOURCE_QUALITY_GATE_V1",
        "all_original_srt_integrity_previously_attested":True,
        "prior_original_cues_count":5129,
        "focused_qa_source_cases":25,
        "focused_qa_unique_source_cues":892,
        "critical_risk_cases_not_released":6,
        "pilot_video_legacy_claims_outside_60_claim_route":3,
        "pilot_video_ids_not_in_116_claim_ledger":2,
        "full_raw_semantic_video_coverage_tested":False,
        "source_passed_not_equal_knowledge_passed":True,
        "published_research_windows_processed":5,
        "published_research_windows_remaining":283,
        "new_approved_financial_facts":0,
        "personal_advice_release":False,
        "full_research_quality_go":False,
        "next_five_video_expansion_go":False,
        "research_quality_verdict":"NO_GO",
        **raw
    }

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--source-zip",type=Path)
    a=p.parse_args()
    print(json.dumps(verify(a.root,source_zip=a.source_zip),
                     ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    main()
