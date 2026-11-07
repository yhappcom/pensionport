"""Independent-authority versus original-SRT audit for selected V5 financial claims.

Primary checks: source IDs and optional original private ZIP cue hashes,
independently published authority references and their effective/publication
dates, conservative educational-release labels and non-promotion.
Passing code cannot substitute for an independent human/blind reviewer.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

DIR="ire/v5/advisory_knowledge/verification_20261104"
PASSES={"EVIDENCE_SUPPORTED_EDUCATIONAL_SCOPE"}
OTHER={"HOLD_CONTEXT","BLOCK_UNSAFE_PROJECTION",
       "DATED_POLICY_WATCH","GENERAL_PRINCIPLE_SCOPE_ONLY"}
ALLOWED=PASSES|OTHER
HOSTS={"law.go.kr","www.law.go.kr","www.kebhana.com",
       "www.nts.go.kr","nts.go.kr","i.nts.go.kr","taxlaw.nts.go.kr",
       "www.moel.go.kr","www.investor.gov","syndication.finra.org"}
RULE_KINDS={"STATUTE","ENACTED_DECREE"}

class IndependentAuthorityGateError(ValueError):
    pass

def demand(value,code):
    if not value: raise IndependentAuthorityGateError(code)

def load(p):
    return json.loads(Path(p).read_text("utf-8"))

def source_cues(raw:bytes):
    """Match SRT's contiguous cue indexes, time and full multiline text."""
    text=raw.decode("utf-8-sig").replace("\r\n","\n").replace("\r","\n")
    cues={}
    for block in re.split(r"\n\s*\n",text.strip()):
        parts=block.splitlines()
        demand(len(parts)>=3 and parts[0].strip().isdigit(),"SRT_BAD_CUE_BLOCK")
        n=int(parts[0].strip())
        demand(n not in cues and n==len(cues)+1,"SRT_CUES_NOT_CONTIGUOUS")
        demand(" --> " in parts[1],"SRT_BAD_TIMECODE")
        cues[n]={"cue":n,"time":parts[1].strip(),"text":" ".join(parts[2:])}
    return cues

def verify(root:Path,private_zip:Path|None=None):
    root=Path(root);folder=root/DIR
    spans=load(folder/"source_spans.json")
    authors=load(folder/"external_authorities.json")
    adjud=load(folder/"adjudications.json")
    requiredate=date(2026,11,4)
    demand(spans.get("schema")=="IRE_V5_ORIGINAL_CUE_SPAN_ATTESTATION_V1"
           and spans.get("source_original_available_to_ci") is False
           and spans.get("span_count")==10,"SOURCE_SPAN_SCOPE_INVALID")
    demand(authors.get("schema")=="IRE_V5_EXTERNAL_AUTHORITY_REFERENCE_V1"
           and authors.get("external_human_blind_grading") is False
           and authors.get("nonblind_assessment_author")=="CHATGPT_SINGLE_CONVERSATION",
           "INDEPENDENT_REVIEW_FABRICATED")
    demand(adjud.get("schema")=="IRE_V5_SOURCE_AUTHORITY_ADJUDICATION_V1"
           and adjud.get("formal_financial_advice_approved") is False
           and adjud.get("blind_human_review_completed") is False
           and adjud.get("evaluator_independent_of_prior_chatgpt") is False
           and adjud.get("unreviewed_provisional_study_claims")==44,
           "BLIND_REVIEW_OR_ADVICE_APPROVAL_FABRICATED")
    catalog=load(root/"ire/v5/source_catalog/201-300.json")
    originals={x["video_id"]:x for x in catalog["files"]}
    reviews={}
    for p in (root/"ire/v5/studies").glob("*.json"):
        if p.name=="evidence_20261104.json": continue
        v=load(p)
        reviews[v["video_id"]]=v
    legacy={json.loads(s)["claim_id"] for s in
            (root/"data/claims.jsonl").read_text("utf-8").splitlines() if s.strip()}
    primary={}
    for entry in authors["sources"]:
        eid=entry["id"]
        demand(eid not in primary and len(eid)>5,"DUPLICATE_AUTHORITY_ID")
        u=urlparse(entry.get("url",""))
        demand(u.scheme=="https" and u.hostname in HOSTS,"AUTHORITY_HOST_NOT_APPROVED")
        demand(entry.get("independent_of_video_source") is True
               and entry.get("independent_external_human_rating") is False
               and entry.get("immutable_source_bytes_archived") is False,
               "EXTERNAL_REFERENCE_ATTESTATION_FALSE")
        if entry.get("published_on"):
            demand(date.fromisoformat(entry["published_on"])<=requiredate,
                   "FUTURE_AUTHORITY_PUBLICATION")
        if entry.get("legal_effective_from"):
            demand(entry["kind"] in RULE_KINDS and
                   date.fromisoformat(entry["legal_effective_from"])<=requiredate,
                   "LAW_EFFECTIVE_DATE_FUTURE_OR_NONLAW")
        primary[eid]=entry
    demand(len(primary)==authors["source_count"]>=10,"AUTHORITY_REFERENCE_COUNT_INVALID")
    source_map={s["id"]:s for s in spans["rows"]}
    demand(len(source_map)==len(spans["rows"])==10,"SOURCE_SPAN_IDS_INVALID")
    span_by_file={}
    if private_zip is not None:
        source_zip=Path(private_zip).read_bytes()
        demand(hashlib.sha256(source_zip).hexdigest()==spans["source_zip_sha256"],
               "SOURCE_ZIP_SHA_MISMATCH")
        with zipfile.ZipFile(private_zip) as bundle:
            for vid in {s["video_id"] for s in spans["rows"]}:
                matches=[x for x in bundle.namelist() if
                         x.endswith("youtube-transcript-"+vid+".srt")
                         and "__MACOSX/" not in x and "/._" not in x]
                demand(len(matches)==1,"PRIVATE_SRT_MEMBER_MISSING")
                raw=bundle.read(matches[0])
                demand(hashlib.sha256(raw).hexdigest()==originals[vid]["source_sha256"],
                       "PRIVATE_SRT_FILE_SHA_CHANGED")
                span_by_file[vid]=source_cues(raw)
    for sid,entry in source_map.items():
        vid=entry["video_id"]
        demand(vid in reviews and vid in originals,
               "ORIGINAL_VIDEO_ID_UNKNOWN")
        v=reviews[vid]
        demand(v["source_sha256"]==originals[vid]["source_sha256"]
               and v["total_cues"]==originals[vid]["cue_count"],
               "STUDY_SOURCE_ID_MISMATCH")
        lo,hi=entry["first_cue"],entry["last_cue"]
        demand(type(lo) is int and type(hi) is int
               and 1<=lo<=hi<=v["total_cues"]
               and entry["cue_count"]==hi-lo+1
               and re.fullmatch("[0-9a-f]{64}",entry["cue_span_sha256"]),
               "CUE_ANCHOR_MALFORMED")
        claim={c["claim_id"] for c in v["claims"]}
        demand(entry["source_study_claim_id"] in claim,
               "CUE_ANCHOR_NOT_LINKED_TO_STUDY_CLAIM")
        if private_zip is not None:
            values=span_by_file[vid]
            chunks=[values[x] for x in range(lo,hi+1)]
            calc=hashlib.sha256(json.dumps(chunks,ensure_ascii=False,
                   sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()
            demand(calc==entry["cue_span_sha256"],
                   "SOURCE_CUE_CONTENT_CHANGED")
            demand(chunks[0]["time"].split(" --> ")[0]==entry["first_time"] and
                   chunks[-1]["time"].split(" --> ")[-1]==entry["last_time"],
                   "SOURCE_CUE_TIMECODE_CHANGED")
    count=Counter()
    unique=set()
    auditids=set()
    for row in adjud["rows"]:
        aid=row["audit_id"]
        demand(aid in source_map and aid not in auditids,"ADJUDICATION_NOT_IN_SOURCE_AUDIT")
        auditids.add(aid)
        anchor=source_map[aid]
        vid=anchor["video_id"]
        claim=next(x for x in reviews[vid]["claims"] if x["claim_id"]==anchor["source_study_claim_id"])
        demand(row["source_study_claim_id"]==claim["claim_id"] and
               row["legacy_claim_ids"]==claim["prior_claim_ids"] and
               set(row["legacy_claim_ids"])<=legacy,
               "ADJUDICATION_DIFFERENT_VIDEO_OR_LEGACY_CLAIM")
        refs=row["authority_ids"]
        demand(len(refs)>0 and len(set(refs))==len(refs)
               and set(refs)<=set(primary),
               "ADJUDICATION_UNGROUNDED_AUTHORITY_REF")
        status=row["disposition"]
        demand(status in ALLOWED,"ADJUDICATION_STATUS_UNRECOGNIZED")
        demand(row.get("independently_human_blind_approved") is False
               and row.get("personalized_advice_approved") is False,
               "ADJUDICATION_PERSONAL_ADVICE_MISAPPROVED")
        demand(len(row["verified_safe_summary"])>=40
               and len(row["source_paraphrase"])>=20
               and len(row["critical_limit"])>=30
               and row["checked_as_of"]=="2026-11-04",
               "CRITICAL_SCOPE_OR_ASOF_MISSING")
        if row["legal_effective_from"]:
            effect=date.fromisoformat(row["legal_effective_from"])
            demand(effect<=requiredate and
                   any(primary[k]["kind"] in RULE_KINDS or
                       primary[k]["kind"]=="MINISTRY_PRESS_RELEASE" for k in refs),
                   "EFFECTIVE_DATE_UNSUPPORTED")
        if status=="DATED_POLICY_WATCH":
            demand(any(primary[k]["kind"]=="MINISTRY_PRESS_RELEASE" for k in refs),
                   "PROPOSED_IRP_LAW_MISLABELED")
        if status=="GENERAL_PRINCIPLE_SCOPE_ONLY":
            demand(any(primary[k]["kind"]=="REGULATOR_INVESTOR_GUIDE" for k in refs),
                   "FOREIGN_ETF_GUIDANCE_AS_KOREAN_LAW")
        count[status]+=1
        unique.add(row["source_study_claim_id"])
    demand(auditids==set(source_map),"SOURCE_WINDOW_MISSING_ADJUDICATION")
    demand(len(unique)==9 and adjud["unique_study_claims_scoped"]==9
           and sum(count.values())==10,"FOCUSED_CASE_COUNTS_WRONG")
    demand(count["EVIDENCE_SUPPORTED_EDUCATIONAL_SCOPE"]==5 and
           count["BLOCK_UNSAFE_PROJECTION"]==2 and
           count["HOLD_CONTEXT"]==1 and
           count["DATED_POLICY_WATCH"]==1 and
           count["GENERAL_PRINCIPLE_SCOPE_ONLY"]==1,
           "RELEASE_DISTRIBUTION_NOT_REPRODUCIBLE")
    return {"schema":"IRE_V5_EXTERNAL_AUTHORITY_RECHECK_RESULT_V1",
            "source_windows_checked":10,
            "unique_new_study_claims_scoped":len(unique),
            "new_study_claims_still_unassessed":44,
            "separately_authored_reference_sources":len(primary),
            "educational_fact_candidates":count["EVIDENCE_SUPPORTED_EDUCATIONAL_SCOPE"],
            "conditional_education_only":count["GENERAL_PRINCIPLE_SCOPE_ONLY"],
            "dated_rule_monitor":count["DATED_POLICY_WATCH"],
            "held_or_blocked":count["HOLD_CONTEXT"]+count["BLOCK_UNSAFE_PROJECTION"],
            "private_srt_bytes_reverified_during_this_run":private_zip is not None,
            "independent_blind_human_evaluation_completed":False,
            "formal_financial_advice_go":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--private-zip",type=Path)
    a=p.parse_args()
    print(json.dumps(verify(a.root,a.private_zip),ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
