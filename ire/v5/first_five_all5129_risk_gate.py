"""Repeatable original 5-SRT 5129-cue financial-risk *screen*, not full claim recall.

GitHub CI without private ZIP validates immutable, scoped pre-reviewed manifests.
--source-zip replays 5129 original cues, 288 V5 window hashes, six rule
detectors, and 22 independently reviewed source span SHA256 values. These
linguistic detectors do NOT certify 100% atomic-claim recall or legal accuracy.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

from .first_five_window_review_gate import source_windows
from .first_five_remnant_221_gate import cue_txt

CENSUS=Path("ire/v5/validation/first_five_all5129_cue_risk_census_20261106.json")
REVIEW=Path("ire/v5/validation/first_five_22_scope_financial_adjudication_20261106.json")
CENSUS_PIN="2398a7218196d541ba1f2f9e7aea0a2b029e66b8"
REVIEW_PIN="ac1d26ff0120d088096d38d299d3ec2fb8079ec4"
PRIVATE_ZIP_SHA="088869c583b2d3ed93d68e4dd5348b1f506877ea2bdc1d66466c199ec80e7716"
VIDEO_IDS=("sz5N9WJS310","6VEfKF7BzZU","OiDTNstaSpM","aNfGrcO6WPI","qtluAViPpsQ")
CUES=(1195,1347,785,758,1044)
WINDOWS=(67,76,44,43,58)
CLASSES=("PERCENT_NUMERIC","MONEY_NUMERIC","ACCOUNT_TAX_PENSION",
         "PRODUCT_OR_LEVERAGE","INSTRUCTION_CERTAINTY","MACRO_STAT")
PATTERNS={
 "PERCENT_NUMERIC":r"\d+(?:[.,]\d+)?\s*(?:%|퍼센트|프로)",
 "MONEY_NUMERIC":r"\d+(?:[.,]\d+)?\s*(?:억|만|천)\s*원",
 "ACCOUNT_TAX_PENSION":r"연금|[Ii][Rr][Pp]|[Ii][Ss][Aa]|[Cc][Mm][Aa]|과세|비과세|세액|소득공제|퇴직금",
 "PRODUCT_OR_LEVERAGE":r"예금자.?보호|파킹\s*[Ee][Tt][Ff]|주택.?연금|[Tt][Dd][Ff]|수수료|대출|빚|부채|배당|해지|보험",
 "INSTRUCTION_CERTAINTY":r"무조건|반드시|필수|절대|확실|보장|[01]00%|다\s*사세요|전부\s*사|사면\s*돼",
 "MACRO_STAT":r"[Gg][Dd][Pp]|경상.?수지|금리|성장률|환율|실업률|물가|인플레",
}
ALLOWED_HOSTS={"open.krx.co.kr","regulation.krx.co.kr","samsungpop.com",
               "nts.go.kr","eiec.kdi.re.kr","www.hf.go.kr",
               "www.index.go.kr","www.bok.or.kr","www.bccard.com"}
EXPECTED_STATUS={"CONDITIONAL_EDUCATION","NARROW_OFFICIAL_CONTEXT",
                 "HISTORICAL_PRODUCT_QUOTE_UNVERIFIED",
                 "PRODUCT_STRUCTURE_NEEDS_CURRENT_TERMS",
                 "NARROW_ACCOUNT_RULE_CONTEXT",
                 "PERSONAL_OPINION_NOT_PREDICTION",
                 "PRODUCT_PROCEDURE_OPEN",
                 "NARROW_REGULATOR_GUIDANCE",
                 "PORTFOLIO_AND_PRODUCT_RISK",
                 "CONTRACT_NEEDED",
                 "HYPOTHETICAL_NON_EQUIVALENT",
                 "NARROW_AGENCY_PRODUCT_FACT",
                 "ANECDOTAL_MARKET_OPINION",
                 "HYPOTHETICAL_NO_RECOVERY_PROMISE",
                 "OFFICIAL_MACRO_TABLE_OPEN",
                 "ORIGINAL_AUDIO_PENDING",
                 "CONDITIONAL_PERSONAL_ALLOCATION",
                 "TARGET_DATE_FUND_UNVERIFIED",
                 "CORRELATED_HUMAN_CAPITAL_RISK",
                 "TAX_YEAR_SCOPED_EDUCATION",
                 "CONDITIONAL_DEBT_RISK",
                 "ILLUSTRATIVE_NONREGULATORY"}
PRIOR_FILE=Path("ire/v5/validation/first_five_original_residual_15_scoped_adjudication_20261106.json")

class FullCueRiskError(ValueError):pass

def need(ok,code):
    if not ok:raise FullCueRiskError(code)

def digest(raw:bytes):
    return hashlib.sha256(raw).hexdigest()

def gitblob(raw:bytes):
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

def pinned_json(root:Path,path:Path,pin:str):
    raw=(root/path).read_bytes()
    need(gitblob(raw)==pin,"RISK5129_PINNED_INPUT_CHANGED_"+path.stem)
    return json.loads(raw)

def scan_cues(cues:list[str]):
    counts={}
    for name in CLASSES:
        counts[name]=sum(bool(re.search(PATTERNS[name],s,re.I)) for s in cues)
    flagged=sum(any(re.search(PATTERNS[name],s,re.I)
                    for name in CLASSES) for s in cues)
    return flagged,counts

def read_all(root:Path):
    c=pinned_json(root,CENSUS,CENSUS_PIN)
    r=pinned_json(root,REVIEW,REVIEW_PIN)
    return c,r

def audit(root:Path,source_zip:Path|None=None):
    root=Path(root)
    c,r=read_all(root)
    need(c.get("schema")=="IRE_V5_FIRST_FIVE_ALL_5129_CUE_SIGNAL_CENSUS_V1"
         and c.get("as_of")=="2026-11-06"
         and c.get("private_owner_zip_sha256")==PRIVATE_ZIP_SHA
         and c.get("original_private_raw_srt_committed_to_github") is False
         and c.get("all_cues_screened")==5129
         and c.get("all_windows_screened")==288
         and c.get("risk_lexical_cues_with_at_least_one_detector")==636
         and c.get("overlap_across_detectors_allowed") is True
         and c.get("regex_signals_not_independent_atomic_claim_count") is True
         and c.get("full_atomic_recall_certified") is False
         and c.get("blind_evaluator_reviewed") is False
         and c.get("new_formal_financial_fact_approvals")==0
         and c.get("original_srt_reopened_by_github_ci") is False
         and c.get("class_names")==list(CLASSES)
         and c.get("sources_are_private_and_not_shipped") is True,
         "RISK5129_FALSE_CERTIFICATION")
    need(r.get("schema")=="IRE_V5_FIRST_FIVE_22_FINANCIAL_RISK_SCOPE_ADJUDICATION_V1"
         and r.get("as_of")=="2026-11-06"
         and r.get("source_census_file")==CENSUS.name
         and r.get("reviewed_claim_groups")==22
         and r.get("semantics_from_private_original_srt") is True
         and r.get("independent_blind_recall_proven") is False
         and r.get("formal_B04_fact_promotions")==0
         and r.get("legacy_master_116_unchanged") is True
         and r.get("p4_education_nodes_29_unchanged") is True
         and r.get("original_audio_issues_unresolved") is True
         and r.get("official_context_is_not_full_statutory_proof") is True
         and r.get("stale_2015_isa_guidance_must_not_supersede_current_2026_rules") is True
         and r.get("release")==
           "PARTIAL_ORIGINAL_RISK_CLAIM_REVIEW_NOT_COMPLETE_FIVE_VIDEO_ATOMIC_RECALL",
         "RISK5129_FALSE_FORMAL_APPROVAL")
    rows=c.get("source_span_evidence",[])
    meanings=r.get("groups",[])
    need(type(rows) is list and len(rows)==22
         and type(meanings) is list and len(meanings)==22
         and len({x.get("review_id") for x in rows})==22
         and len({x.get("review_id") for x in meanings})==22,
         "RISK5129_UNMATCHED_RISK_GROUPS")
    official=r.get("official_context",{})
    need(type(official) is dict and len(official)==9,
         "RISK5129_OFFICIAL_SOURCE_NOT_SCOPED")
    for key,s in official.items():
        parsed=urlsplit(s.get("url",""))
        need(parsed.scheme=="https" and parsed.hostname in ALLOWED_HOSTS
             and not parsed.username and not parsed.password
             and s.get("not_legal_snapshot") is True
             and len(s.get("scope",""))>=25 and bool(s.get("source_date")),
             "RISK5129_OFFICIAL_SOURCE_INVALID_"+key)
    prev=json.loads((root/PRIOR_FILE).read_text("utf-8"))
    prior_ids={x["id"] for x in prev["items"]}
    vmeta=json.loads((root/"ire/v5/validation/first_five_source_manifest_20261105.json").read_text("utf-8"))
    videoinfo={x["sequence"]:x for x in vmeta["videos"]}
    source_windows_by_n={}
    video_stats=c.get("by_video")
    need(type(video_stats) is list and len(video_stats)==5,
         "RISK5129_NO_ALL_VIDEO_STATS")
    for n,v in enumerate(video_stats,1):
        exp=json.loads((root/"ire/v5/validation"/f"v5_first_five_video_{n:02d}_window_review_20261106.json").read_text("utf-8"))
        windows=exp["records"];source_windows_by_n[n]=windows
        need(v.get("video_number")==n and v.get("cues")==CUES[n-1]
             and v.get("windows")==WINDOWS[n-1]
             and type(v.get("detector_positive_cues")) is int
             and 0<=v["detector_positive_cues"]<=CUES[n-1]
             and set(v.get("class_positive_cues",{}))==set(CLASSES)
             and all(type(v["class_positive_cues"][k]) is int
                     and 0<=v["class_positive_cues"][k]<=CUES[n-1] for k in CLASSES)
             and videoinfo[n]["video_id"]==VIDEO_IDS[n-1],
             "RISK5129_288_WINDOW_OR_5129_CUE_METADATA_CHANGED")
    need(sum(v["detector_positive_cues"] for v in video_stats)==636,
         "RISK5129_FLAG_COUNTS_CHANGED")
    for i,(s,m) in enumerate(zip(rows,meanings),1):
        ident=f"FV5-3PASS-{i:03d}"
        n=s.get("video_number")
        lo=s.get("start_cue");hi=s.get("end_cue")
        need(s.get("review_id")==ident and m.get("review_id")==ident
             and type(n) is int and 2<=n<=5
             and s.get("video_id")==VIDEO_IDS[n-1]
             and type(lo) is int and type(hi) is int and 1<=lo<=hi<=CUES[n-1]
             and re.fullmatch("[0-9a-f]{64}",str(s.get("combined_cue_text_sha256","")))
             and s.get("actual_audio_rechecked") is False
             and s.get("individual_claim_recall_proven") is False,
             "RISK5129_SOURCE_SPAN_NOT_VERIFIED")
        overlap=[w["window_id"] for w in source_windows_by_n[n]
                 if w["first_cue"]<=hi and w["last_cue"]>=lo]
        need(s.get("window_ids")==overlap,
             "RISK5129_WINDOW_CUE_RELATION_CHANGED")
        need(m.get("status") in EXPECTED_STATUS
             and len(m.get("adjudicated_scope",""))>=55
             and type(m.get("query_phrases")) is list
             and 1<=len(m["query_phrases"])<=4
             and all(type(q) is str and len(q)>=5 for q in m["query_phrases"])
             and m.get("strict_atomic_equivalence_approved") is False
             and m.get("individual_financial_fact_approved") is False
             and m.get("investment_order_approved") is False
             and all(k in official for k in m.get("official_ref_ids",[]))
             and all(k in prior_ids for k in m.get("prior_review_ids",[])),
             "RISK5129_UNREVIEWED_FINANCIAL_SEMANTICS")
    source_replayed=False
    if source_zip is not None:
        p=Path(source_zip)
        need(p.is_file(),"RISK5129_PRIVATE_SOURCE_NOT_AVAILABLE")
        need(digest(p.read_bytes())==PRIVATE_ZIP_SHA,
             "RISK5129_PRIVATE_SOURCE_ARCHIVE_HASH_CHANGED")
        by_vid={}
        with zipfile.ZipFile(p) as z:
            for n,vid in enumerate(VIDEO_IDS,1):
                member=f"1-100/youtube-transcript-{vid}.srt"
                need(z.namelist().count(member)==1,
                     "RISK5129_PRIVATE_SRT_NOT_UNIQUE")
                blob=z.read(member)
                need(digest(blob)==videoinfo[n]["source_sha256"],
                     "RISK5129_PRIVATE_VIDEO_SRT_HASH_CHANGED")
                cue_strings=cue_txt(blob)
                need(len(cue_strings)==CUES[n-1],
                     "RISK5129_PRIVATE_CUE_COUNT_CHANGED")
                w=source_windows(blob)
                need(len(w)==WINDOWS[n-1] and all(
                    all(actual[k]==value for k,value in derived.items())
                    for actual,derived in zip(source_windows_by_n[n],w)),
                    "RISK5129_288_SOURCE_WINDOWS_CHANGED")
                flagged,counts=scan_cues(cue_strings)
                expected=video_stats[n-1]
                need(flagged==expected["detector_positive_cues"]
                     and counts==expected["class_positive_cues"],
                     "RISK5129_LEXICAL_636_REPLAY_MISMATCH")
                by_vid[n]=cue_strings
            for s in rows:
                clips=by_vid[s["video_number"]]
                snippet=" ".join(clips[s["start_cue"]-1:s["end_cue"]])
                need(digest(snippet.encode("utf-8"))==s["combined_cue_text_sha256"],
                     "RISK5129_ORIGINAL_22_SPAN_CONTENT_CHANGED")
        source_replayed=True
    return {
      "schema":"IRE_V5_FIRST_FIVE_5129_RISK_SCREEN_AND_22_SOURCE_SPANS_RECEIPT_V1",
      "source_cues_screened":5129,
      "source_windows_screened":288,
      "risk_flagged_source_cues":636,
      "reviewed_risk_claim_groups":22,
      "source_spans_private_reopened_this_process":source_replayed,
      "source_windows_replayed_from_original_in_this_process":288 if source_replayed else 0,
      "source_cues_replayed_from_original_in_this_process":5129 if source_replayed else 0,
      "source_span_hashes_replayed_from_original_in_this_process":22 if source_replayed else 0,
      "formal_financial_claim_approvals":0,
      "prior_master_116_untouched":True,
      "active_education_nodes_29_preserved":True,
      "full_atomic_claim_recall_independently_proven":False,
      "independent_personal_advice_grade_pass":False,
      "release":"SOURCE_SCREENED_RISK_GROUPS_ONLY_NO_COMPLETE_RESEARCH_APPROVAL",
    }

def retrieve(root:Path,question:str,*,limit:int=3):
    need(type(question) is str and question.strip() and type(limit) is int
         and 1<=limit<=22,"RISK5129_QUERY_INVALID")
    c,r=read_all(Path(root))
    # Also validates manifest material and prior-claim lineage rather than
    # reading unchecked and potentially forged caution strings.
    audit(Path(root))
    q=re.sub(r"\s+","",question.casefold())
    pairs={x["review_id"]:x for x in c["source_span_evidence"]}
    found=[]
    for m in r["groups"]:
        if any(re.sub(r"\s+","",phrase.casefold()) in q
               for phrase in m["query_phrases"]):
            s=pairs[m["review_id"]]
            found.append({
                "review_id":m["review_id"],
                "video_number":s["video_number"],
                "cue_range":[s["start_cue"],s["end_cue"]],
                "status":m["status"],
                "caution":m["adjudicated_scope"],
                "prior_related_ids":m["prior_review_ids"],
                "official_context_urls":[r["official_context"][k]["url"]
                                         for k in m["official_ref_ids"]],
                "new_verified_financial_law_fact":False,
            })
    return {"schema":"IRE_V5_ORIGINAL_5129_CUE_RISK_SCOPE_RETRIEVAL_V1",
            "items":found[:limit],"match_count":len(found[:limit]),
            "research_certification":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--source-zip",type=Path)
    p.add_argument("--question")
    a=p.parse_args()
    result=retrieve(a.root,a.question) if a.question is not None else audit(a.root,a.source_zip)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":main()
