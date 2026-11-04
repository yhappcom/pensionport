"""Fail-closed one-video incremental source + official-law + knowledge reconciliation.

This module is reusable for future videos. Each video study supplies its own
manifest, original cue spans, legal comparisons and legacy/education links.
The active ChatGPT turn must do actual semantic analysis and official browsing.
Passing this gate proves coverage, source lineage, temporal warnings and safe
non-promotion; it does NOT prove that official URLs are content-hashed, that
ASR is acoustically accurate or that a human independently certified advice.

CI intentionally has no private SRT. With --private-zip it rechecks every
source window byte-for-byte against the privately supplied original archive.
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

STUDY="ire/v5/new_video_studies/C7KctGzg-K0_20261105.json"
VIDEO_RE=re.compile(r"[A-Za-z0-9_-]{11}\Z")
SHA_RE=re.compile(r"[0-9a-f]{64}\Z")
RECONCILIATION={
    "EDU-KR-STOCK-TRANSACTION-TAX-2026-CANDIDATE",
    "EDU-KR-HIGH-DIVIDEND-2026-CANDIDATE",
    "EDU-KR-STOCK-MAJOR-SHAREHOLDER-2026-CANDIDATE",
}
SAFE_KINDS={
    "PUBLISHED_PROPOSAL","ENACTED_LAW","GOVERNMENT_POLICY_DECISION",
    "TAX_ADMIN_NOTICE","TAX_ADMIN_GUIDANCE","EFFECTIVE_POLICY_GUIDANCE",
    "GOVERNMENT_2026_DRAFT","GOVERNMENT_EFFECTIVE_SUMMARY",
    "EXECUTED_BROKER_NOTICE",
}
CLAIM_STATUS={
    "HISTORICAL_DRAFT_FRAME","SUPERSEDED_DRAFT_MATERIAL_CHANGE",
    "UNVERIFIED_STATISTIC_BLOCKED","ENACTED_WITH_PERSONAL_TAX_CONDITIONS",
    "ENACTED_WITH_AMOUNT_LIMIT_CORRECTION",
    "ENACTED_CONDITIONAL_WITH_FRESH_PROPOSAL_WATCH",
    "ENACTED_CORPORATE_TAX_GENERAL",
    "ENACTED_MARKET_SEGMENTED_WITH_ASR_WARNING",
    "ETF_TRANSACTION_TAX_SCOPE_HOLD","DRAFT_REVERSED_BY_GOVERNMENT",
    "ENACTED_FINANCIAL_SECTOR_TAX_WITH_FORECAST_HOLD",
}
class IncrementalReviewError(ValueError):
    pass

def demand(ok, code):
    if not ok: raise IncrementalReviewError(code)

def read(path):
    return json.loads(Path(path).read_text("utf-8"))

def parse_srt(source):
    text=source.decode("utf-8-sig").replace("\r\n","\n").replace("\r","\n")
    cues={}
    for block in re.split(r"\n\s*\n",text.strip()):
        lines=block.splitlines()
        demand(len(lines)>=3 and lines[0].strip().isdigit(),
               "SOURCE_BAD_CUE")
        cue=int(lines[0].strip())
        demand(cue==len(cues)+1 and " --> " in lines[1],
               "SOURCE_CUES_NOT_CONTIGUOUS")
        cues[cue]={"cue":cue,"time":lines[1].strip(),
                   "text":" ".join(lines[2:])}
    return cues

def verify(root:Path, review:dict|None=None, private_zip:Path|None=None):
    root=Path(root)
    study=review if review is not None else read(root/STUDY)
    v=study.get("video",{})
    vid=v.get("video_id")
    demand(study.get("schema")=="IRE_V5_NEW_VIDEO_FULL_SOURCE_AND_TEMPORAL_CHECK_V1"
           and study.get("research_run_date")=="2026-11-05"
           and isinstance(vid,str) and VIDEO_RE.fullmatch(vid)
           and v.get("roster_no")==231 and vid=="C7KctGzg-K0",
           "NEW_VIDEO_SCHEMA_OR_ROSTER_WRONG")
    demand(v.get("private_original_bytes_read_in_chat") is True
           and v.get("private_original_bytes_available_to_github_ci") is False
           and v.get("existing_legacy_research_before_this_study") is False,
           "NEW_VIDEO_FALSE_SOURCE_OR_LEGACY_PROVENANCE")
    cat=read(root/"ire/v5/source_catalog/201-300.json")
    source=[x for x in cat["files"] if x["video_id"]==vid]
    demand(len(source)==1 and source[0]["roster_inventory_no"]==231
           and source[0]["roster_video_type"]=="Long-form"
           and source[0]["source_sha256"]==v.get("original_srt_sha256")
           and SHA_RE.fullmatch(str(v.get("original_srt_sha256","")))
           and source[0]["cue_count"]==v.get("original_cue_count")==214
           and source[0]["end_ms"]==v.get("original_duration_end_ms"),
           "NEW_VIDEO_CENSUS_SOURCE_MISMATCH")
    demand(SHA_RE.fullmatch(str(v.get("original_zip_sha256","")))
           and v.get("original_archive")=="201-300.zip"
           and not (root/"ire/v5/studies"/(vid+".json")).exists(),
           "NEW_VIDEO_NOT_GENUINELY_UNSTUDIED")
    graph=read(root/"ire/v5/advisory_knowledge/integrated_education13_20261104.json")
    legacy=read(root/"ire/v5/advisory_knowledge/provisional_integrated_20_plus_5_20261104.json")
    g_ids={x["knowledge_id"] for x in graph["nodes"]}
    core_ids={x["claim_id"] for x in legacy["nodes"]}
    demand(len(g_ids)==graph["total_education_topics"]==13
           and len(core_ids)==20
           and study["reconciled_against_prior"].get("baseline_education_concepts")==13
           and study["reconciled_against_prior"].get("baseline_core_video_claim_nodes")==20
           and study["reconciled_against_prior"].get("unchanged_canonical_claims_116") is True
           and study["reconciled_against_prior"].get("unchanged_education_13") is True
           and study["reconciled_against_prior"].get("auto_education_approval_count")==0,
           "NEW_VIDEO_SILENT_LEGACY_OR_KNOWLEDGE_PROMOTION")
    final=study.get("approvals",{})
    demand(final=={
        "personalized_financial_advice":False,
        "human_blind_independent_review":False,
        "original_audio_authentication":False,
        "current_financial_fact_certification":False,
    },"NEW_VIDEO_FALSE_APPROVAL")
    auth={}
    for ref in study.get("authoritative_sources",[]):
        rid=ref["id"]
        domain=urlparse(ref.get("url",""))
        demand(rid not in auth and domain.scheme=="https" and domain.hostname
               and ref.get("kind") in SAFE_KINDS
               and ref.get("source_is_independent_of_youtube") is True
               and ref.get("original_document_bytes_sealed") is False
               and ref.get("externally_human_reviewed") is False,
               "NEW_VIDEO_UNTRUSTED_AUTHORITY")
        if ref.get("published_on"):
            demand(date.fromisoformat(ref["published_on"])<=date(2026,11,5),
                   "NEW_VIDEO_FUTURE_AUTHORITY")
        auth[rid]=ref
    demand(len(auth)>=13,"NEW_VIDEO_TOO_FEW_INDEPENDENT_PUBLIC_DOCUMENTS")
    cover=study.get("coverage_segments",[])
    demand(len(cover)>=len(study.get("research_claims",[])),
           "NEW_VIDEO_NOT_FULLY_SEGMENTED")
    pos=1
    for chunk in cover:
        a,b=chunk["start"],chunk["end"]
        demand(type(a) is int and type(b) is int
               and a==pos and b>=a and b<=214
               and isinstance(chunk.get("kind"),str)
               and len(chunk["kind"])>=4,"NEW_VIDEO_MISSING_CUE_COVERAGE")
        pos=b+1
    demand(pos==215,"NEW_VIDEO_TAIL_CUES_NOT_ANALYZED")
    cases=study.get("research_claims")
    demand(type(cases) is list and len(cases)==13,
           "NEW_VIDEO_MAIN_CLAIMS_COUNT_BAD")
    labels=set()
    relations=[]
    new_candidates=[]
    for claim in cases:
        cid=claim["claim_id"]
        demand(re.fullmatch(r"C231-\d{2}",cid)
               and cid not in labels and claim.get("video_id")==vid,
               "NEW_VIDEO_CLAIM_IDS_OR_SOURCE_WRONG")
        labels.add(cid)
        a,b=claim["cue_start"],claim["cue_end"]
        demand(type(a) is int and type(b) is int and 1<=a<=b<=214
               and any(x["start"]==a and x["end"]==b for x in cover)
               and SHA_RE.fullmatch(str(claim.get("source_cue_span_sha256","")))
               and re.fullmatch(r"\d\d:\d\d:\d\d,\d{3}",
                                str(claim.get("first_cue_time","")))
               and re.fullmatch(r"\d\d:\d\d:\d\d,\d{3}",
                                str(claim.get("last_cue_time",""))),
               "NEW_VIDEO_ATOMIC_SOURCE_CUE_ANCHOR_INVALID")
        demand(claim.get("verified_as_of")=="2026-11-05"
               and isinstance(claim.get("source_paraphrase"),str)
               and len(claim["source_paraphrase"])>=25
               and isinstance(claim.get("authoritative_comparison"),str)
               and len(claim["authoritative_comparison"])>=55
               and claim.get("disposition") in CLAIM_STATUS,
               "NEW_VIDEO_MISSING_INDEPENDENT_COMPARISON")
        refids=claim.get("authority_ids")
        demand(type(refids) is list and refids
               and len(set(refids))==len(refids)
               and set(refids)<=set(auth),
               "NEW_VIDEO_INVENTED_OR_MISSING_AUTHORITY")
        demand(set(claim.get("existing_core_claim_ids",[]))<=core_ids,
               "NEW_VIDEO_INVENTED_LEGACY_CLAIM")
        demand(claim.get("financial_fact_certified") is False
               and claim.get("personal_investment_advice_approved") is False
               and claim.get("external_human_blind_approved") is False
               and claim.get("original_audio_verified") is False,
               "NEW_VIDEO_UNVERIFIED_TAX_ADVICE_PROMOTED")
        relation=claim.get("reconciliation_link")
        if relation is not None:
            demand(relation["target_id"] in core_ids|g_ids
                   and relation["relation"] in {
                       "SUPPORTS_PROPOSAL_LAW_SEPARATION",
                       "CHALLENGES_OUTDATED_PROPOSAL",
                       "QUALIFIES_MARKET_TRADING_COST_NOT_ETF_TAX_APPROVAL",
                       "QUALIFIES_TAX_COMPONENT_SCOPE_NOT_AUTO_APPROVAL",
                       "CHALLENGES_ABORTED_TAX_PROPOSAL",
                   },"NEW_VIDEO_INVALID_OLD_KNOWLEDGE_RELATION")
            relations.append((cid,relation["target_id"],relation["relation"]))
        candidate=claim.get("new_provisional_concept_id")
        if candidate is not None:
            demand(candidate in RECONCILIATION
                   and candidate not in g_ids
                   and candidate not in new_candidates,
                   "NEW_VIDEO_UNREVIEWED_FACT_MERGED_AS_APPROVED")
            new_candidates.append(candidate)
    demand(labels=={f"C231-{i:02d}" for i in range(1,14)},
           "NEW_VIDEO_SOURCE_CLAIM_GAPS")
    check_by_id={x["claim_id"]:x for x in cases}
    dividend=check_by_id["C231-02"]
    major=check_by_id["C231-12"]
    tax=check_by_id["C231-10"]
    coverage=check_by_id["C231-03"]
    def contains(id,*tokens):
        return all(token in check_by_id[id]["authoritative_comparison"] for token in tokens)
    demand(dividend["disposition"]=="SUPERSEDED_DRAFT_MATERIAL_CHANGE"
           and contains("C231-02","20%","25%","10%","30%","2026")
           and set(dividend["authority_ids"])>={"M25","L26DIV","N26DIV"},
           "NEW_VIDEO_2025_DIVIDEND_PROPOSAL_FALSELY_CURRENT")
    demand(major["disposition"]=="DRAFT_REVERSED_BY_GOVERNMENT"
           and contains("C231-12","2025-09-15","50억원")
           and set(major["authority_ids"])>={"G25MAJOR","N26MAJOR"},
           "NEW_VIDEO_10B_WAS_NOT_ENACTED")
    demand(tax["disposition"]=="ENACTED_MARKET_SEGMENTED_WITH_ASR_WARNING"
           and contains("C231-10","0.05%","0.15%","0.20%")
           and coverage["disposition"]=="UNVERIFIED_STATISTIC_BLOCKED"
           and check_by_id["C231-11"]["disposition"]=="ETF_TRANSACTION_TAX_SCOPE_HOLD",
           "NEW_VIDEO_UNSAFE_TRADE_TAX_OR_UNVERIFIED_ESTIMATE")
    demand(contains("C231-07","300만원","전액")
           and contains("C231-08","2026","1200만원")
           and contains("C231-13","1조원","1%"),
           "NEW_VIDEO_TAX_EXCEPTIONS_LOST")
    summary=study.get("reconciled_against_prior",{})
    demand(len(relations)==summary.get("existing_relation_count")==5
           and set(new_candidates)==RECONCILIATION
           and summary.get("new_provisional_concept_count")==3
           and summary.get("new_provisional_concept_ids")==new_candidates
           and summary.get("relations")==[
               {"claim_id":c,"target_id":target,"relation":rel}
               for c,target,rel in relations],
           "NEW_VIDEO_RECONCILIATION_NOT_REPRODUCIBLE")
    demand(study.get("counts",{}).get("whole_source_cues_covered")==214
           and study["counts"].get("claim_windows")==13
           and study["counts"].get("superseded_or_reversed")==2
           and study["counts"].get("unverified_estimate")==1
           and study["counts"].get("pending_etf_scope")==1,
           "NEW_VIDEO_RUN_SUMMARY_UNTRUSTWORTHY")
    span_rechecks=0
    if private_zip:
        raw=Path(private_zip).read_bytes()
        demand(hashlib.sha256(raw).hexdigest()==v["original_zip_sha256"],
               "NEW_VIDEO_PRIVATE_ARCHIVE_TAMPERED")
        with zipfile.ZipFile(private_zip) as z:
            paths=[n for n in z.namelist()
                   if n.endswith(f"youtube-transcript-{vid}.srt")
                   and not n.startswith("__MACOSX") and "/._" not in n]
            demand(len(paths)==1,"NEW_VIDEO_PRIVATE_SRT_NOT_FOUND")
            file=z.read(paths[0])
        demand(hashlib.sha256(file).hexdigest()==v["original_srt_sha256"],
               "NEW_VIDEO_PRIVATE_SRT_CONTENT_TAMPERED")
        cues=parse_srt(file)
        demand(len(cues)==214,"NEW_VIDEO_PRIVATE_CUE_COUNT_CHANGED")
        for x in cases:
            span=[cues[n] for n in range(x["cue_start"],x["cue_end"]+1)]
            text=json.dumps(span,ensure_ascii=False,sort_keys=True,
                            separators=(",",":")).encode("utf-8")
            digest=hashlib.sha256(text).hexdigest()
            demand(digest==x["source_cue_span_sha256"]
                   and span[0]["time"].split(" --> ")[0]==x["first_cue_time"]
                   and span[-1]["time"].split(" --> ")[-1]==x["last_cue_time"],
                   "NEW_VIDEO_ORIGINAL_SRT_SPAN_HASH_MISMATCH")
            span_rechecks+=1
    return {
       "schema":"IRE_V5_NEW_VIDEO_SINGLE_REQUEST_GATE_RESULT_V1",
       "video_id":vid,"roster_no":v["roster_no"],
       "source_cues_full_video_covered":214,
       "source_claims_extracted_and_checked":len(labels),
       "verified_separate_public_source_references":len(auth),
       "old_core_or_education_context_links":len(relations),
       "new_knowledge_provisional_only":len(new_candidates),
       "superseded_draft_and_reversed_policy_detected":2,
       "unverifiable_13pct_estimate_blocked":True,
       "all_private_original_cue_windows_byte_verified_now":span_rechecks,
       "original_full_video_source_available_in_ci":False,
       "existing_13_education_topics_untouched":True,
       "independent_human_blind_review_completed":False,
       "personalized_investment_advice_approved":False,
       "verdict":"NEW_UNSEEN_VIDEO_RESEARCH_RECONCILED_WITH_NO_UNVERIFIED_PROMOTION",
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=Path("."))
    parser.add_argument("--private-zip",type=Path)
    a=parser.parse_args()
    print(json.dumps(verify(a.root,private_zip=a.private_zip),
                     ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    main()
