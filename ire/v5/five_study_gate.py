"""Validate source-based pilot research and proposed links to existing knowledge.

This gate validates provenance and honest research statuses, NOT the semantic
correctness of ChatGPT's analysis or independent approval of finance claims.
It optionally validates the full source ZIP when the private file is supplied.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import hashlib
import json
import re
import zipfile

STUDIES=("7p3p7TKcdqY","l0Q-2Ah-ba8","2bLy034D5LA",
         "z1oZOJ3_uIk","tDD5GzvDYq8")
RELATIONS={"SUPPORTS","EXTENDS","QUALIFIES","CHALLENGES","UNRELATED"}
SCHEMA="IRE_V5_FULL_SOURCE_STUDY_V1"
EVIDENCE_SCHEMA="IRE_V5_FIVE_SOURCE_EVIDENCE_REGISTRY_V1"

class StudyGateError(ValueError):
    pass

def require(ok,why):
    if not ok: raise StudyGateError(why)

def load(file):
    return json.loads(Path(file).read_text("utf-8"))

def verify(root:Path, private_zip:Path|None=None) -> dict:
    root=Path(root)
    corpus=load(root/"ire/v5/source_catalog/201-300.json")
    sources={x["video_id"]:x for x in corpus["files"]}
    refs=load(root/"ire/v5/studies/evidence_20261104.json")
    require(refs.get("schema")==EVIDENCE_SCHEMA and
            refs.get("no_automatic_financial_fact_approval") is True,
            "EVIDENCE_REGISTRY_INVALID")
    evidence={}
    for s in refs["sources"]:
        sid=s.get("id")
        require(sid not in evidence and type(sid) is str
                and str(s.get("url","")).startswith("https://")
                and s.get("source_bytes_archived") is False
                and s.get("independent_verifier") is False,
                "FALSE_OFFICIAL_SOURCE_ATTESTATION")
        evidence[sid]=s
    prior={json.loads(x)["claim_id"] for x in
           (root/"data/claims.jsonl").read_text("utf-8").splitlines() if x.strip()}
    core=load(root/"ire/v5/advisory_knowledge/core20_candidates_20261104.json")
    core_ids={x["claim_id"] for x in core["claims"]}
    ids=set()
    count=0
    sections_total=0
    relations={}
    open_statuses={}
    studied=[]
    for video_id in STUDIES:
        p=root/"ire/v5/studies"/(video_id+".json")
        record=load(p)
        require(record.get("schema")==SCHEMA and record.get("video_id")==video_id
                and record.get("review_date")=="2026-11-04"
                and record.get("source_archive")=="201-300.zip",
                "STUDY_ID_OR_SCHEMA_WRONG")
        source=sources.get(video_id)
        require(source is not None and
                record.get("source_sha256")==source["source_sha256"] and
                record.get("total_cues")==source["cue_count"] and
                record.get("roster_no")==source["roster_inventory_no"],
                "STUDY_ORIGINAL_SRT_MISMATCH")
        require(record.get("source_read_all_cues_in_active_chat") is True and
                record.get("each_cue_independently_claim_adjudicated") is False
                and record.get("overall_status")=="SOURCE_STUDIED_CLAIMS_PROVISIONAL"
                and record.get("advisory_go") is False
                and record.get("no_public_transcript_full_text") is True,
                "STUDY_FALSIFIED_COMPLETION_OR_APPROVAL")
        sections=record.get("source_sections")
        cursor=1
        for sec in sections:
            require(type(sec["first_cue"]) is int and
                    type(sec["last_cue"]) is int and
                    sec["first_cue"]==cursor and
                    sec["first_cue"]<=sec["last_cue"]<=record["total_cues"],
                    "STUDY_CUE_SECTION_GAP_OR_OVERLAP")
            cursor=sec["last_cue"]+1
            sections_total+=1
        require(cursor==record["total_cues"]+1,"STUDY_CUE_SECTION_INCOMPLETE")
        claim_rows=record.get("claims")
        require(type(claim_rows) is list and len(claim_rows)>=8,
                "STUDY_MISSING_FINANCE_CLAIMS")
        local_ids=set()
        for item in claim_rows:
            claim_id=item.get("claim_id")
            require(type(claim_id) is str and claim_id not in ids
                    and claim_id not in local_ids,"STUDY_CLAIM_ID_DUPLICATE")
            ids.add(claim_id);local_ids.add(claim_id)
            require(type(item.get("first_cue")) is int and
                    type(item.get("last_cue")) is int and
                    1<=item["first_cue"]<=item["last_cue"]<=record["total_cues"],
                    "STUDY_CLAIM_OUTSIDE_SRT_RANGE")
            require(item.get("relationship") in RELATIONS and
                    type(item.get("prior_claim_ids")) is list and
                    0<len(item["prior_claim_ids"]) and
                    set(item["prior_claim_ids"])<=prior and
                    set(item["prior_claim_ids"])<=core_ids,
                    "STUDY_UNKNOWN_OR_OUT_OF_SCOPE_LEGACY_CLAIM")
            require(type(item.get("proposition")) is str
                    and len(item["proposition"])>=20 and
                    type(item.get("scope_or_error")) is str
                    and len(item["scope_or_error"])>=20 and
                    type(item.get("review_status")) is str,
                    "STUDY_MEANING_OR_LIMITS_MISSING")
            citations=item.get("evidence_ids")
            require(type(citations) is list and
                    set(citations)<=set(evidence),"STUDY_UNKNOWN_WEB_EVIDENCE")
            require(item.get("independent_human_verified") is False and
                    item.get("advisory_approved") is False,
                    "STUDY_UNAPPROVED_CLAIM_ESCALATED")
            count+=1
            relations[item["relationship"]]=relations.get(item["relationship"],0)+1
            status=item["review_status"]
            open_statuses[status]=open_statuses.get(status,0)+1
        require(type(record.get("verification_open")) is list and
                len(record["verification_open"])>=4,"STUDY_OPEN_ITEMS_HIDDEN")
        studied.append(video_id)
    require(count==53 and len(ids)==53,"STUDY_EXPECTED_53_PROVISIONAL_CLAIMS")
    require(sections_total>=40,"STUDY_FULL_SOURCE_SECTIONS_MISSING")
    # This arithmetic is an explicit counterexample to unconditional DCA returns.
    example=load(root/"ire/v5/studies/tDD5GzvDYq8.json")["counterexample_arithmetic"]
    units=[example["monthly_investment_krw"]//p for p in example["prices_krw"]]
    require(units==example["purchased_units"]
            and sum(units)==example["total_units"]
            and sum(units)*example["average_cost_krw"]==example["total_paid_krw"]
            and sum(units)*example["last_price_krw"]==example["ending_value_krw"]
            and example["unrealized_loss_krw"]==example["total_paid_krw"]-example["ending_value_krw"]
            and abs(100*(example["ending_value_krw"]/example["total_paid_krw"]-1)-
                    example["return_pct"])<1e-10,"STUDY_DCA_COUNTEREXAMPLE_BAD_MATH")
    if private_zip is not None:
        with zipfile.ZipFile(private_zip) as archive:
            for video_id in STUDIES:
                paths=[n for n in archive.namelist() if
                       n.endswith("/youtube-transcript-"+video_id+".srt")
                       and "__MACOSX" not in n]
                require(len(paths)==1,"PRIVATE_ZIP_MEMBER_MISSING_OR_DUPLICATE")
                content=archive.read(paths[0])
                require(hashlib.sha256(content).hexdigest()==sources[video_id]["source_sha256"],
                        "PRIVATE_ZIP_SOURCE_BYTES_CHANGED")
    return {"schema":"IRE_V5_FIVE_SOURCE_STUDIES_GATE_V1",
            "full_transcripts_read_by_chat":len(studied),
            "total_source_cues":sum(sources[x]["cue_count"] for x in studied),
            "coverage_sections":sections_total,
            "provisional_claims":count,"provisional_relations":dict(sorted(relations.items())),
            "independently_verified_financial_facts":0,
            "independently_adjudicated_atomic_cues":0,
            "personalized_advisory_approved":False,
            "private_srt_bytes_verified_this_run":private_zip is not None,
            "release":"RESEARCH_COMPLETE_FOR_MAJOR_CLAIMS_NO_ADVISORY_APPROVAL"}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",type=Path,default=Path("."))
    ap.add_argument("--private-zip",type=Path)
    args=ap.parse_args()
    print(json.dumps(verify(args.root,args.private_zip),ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
