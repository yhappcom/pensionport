"""Bounded #2-#5 source-ledger adjudication, preserving the first 305 candidates.

CI without the owner's private zip proves immutable manifest+prior lineage only;
--source-zip replays all 15 original SRT cue span hashes and whole four-video
byte provenance. It does not certify complete 288-window atomic claim recall.
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

LEDGER=Path("ire/v5/validation/first_five_original_residual_15_scoped_adjudication_20261106.json")
PRIOR68=Path("ire/v5/validation/first_five_atomic_20261106.json")
REMAINDER237=Path("ire/v5/validation/first_five_remnant_221_source_claim_candidates_20261106.json")
FIRSTFIVE_SOURCES=Path("ire/v5/validation/first_five_source_manifest_20261105.json")
PINNED_GIT_BLOB_SHA1="194f9fa93d567fac7a89796abb097d949de8bda4"
KNOWN_ARCHIVE_SHA="088869c583b2d3ed93d68e4dd5348b1f506877ea2bdc1d66466c199ec80e7716"
OLD_SHA="00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd"
HOSTS={"www.bok.or.kr","www.samsungpop.com","pension.kebhana.com",
       "file.shinhansec.com","syndication.finra.org","www.investor.gov"}
EXPECTED_VIDEO={2:"6VEfKF7BzZU",3:"OiDTNstaSpM",
                4:"aNfGrcO6WPI",5:"qtluAViPpsQ"}
ALLOWED_STATUSES={
 "STRATEGY_SCOPE_ONLY","NARROW_HISTORICAL_RATE_CORROBORATED_NOT_PRODUCT_RETURN",
 "OFFICIAL_SCOPE_CORRECTION_NOT_FORMAL_FACT_APPROVAL",
 "PRODUCT_HISTORICAL_UNCERTAIN","PRODUCT_TERMS_SCOPED_OFFICIAL_EXAMPLE",
 "OPEN_PRODUCT_PROCEDURE_NOT_APPROVED","OVERGENERALIZATION_QUARANTINED",
 "NEW_UNMATCHED_IN_68_237_SOURCE_ANCHOR_REGISTERS",
 "HYPOTHESIS_NOT_RETURN_GUARANTEE","ORIGINAL_AUDIO_REVIEW_REQUIRED",
 "PERSONAL_ALLOCATION_NOT_APPROVED","GENERAL_RISK_CAUTION_OFFICIAL_EDUCATION",
 "GENERAL_OPINION_ONLY",
}
TRIGGERS={
 "FV5-RES-001":("20대 CMA ISA 연금저축 3개","ISA 40 연금저축 10"),
 "FV5-RES-002":("2026년 9월 기준금리 3","CMA 20배 30배"),
 "FV5-RES-003":("기준금리 7일물 RP","7일물 RP가 기준금리"),
 "FV5-RES-004":("CMA 2.15~2.85","CMA 2.85%"),
 "FV5-RES-005":("IRP에 자산배분 ISA에 배당","연금저축에는 자산배분"),
 "FV5-RES-006":("증권사 IRP 수수료 0","IRP 수수료 무조건","모든 증권사 IRP 무료"),
 "FV5-RES-007":("IRP 1만원 연금개시","IRP 만원 수령","퇴직금 1만원 신청"),
 "FV5-RES-008":("파킹 ETF 3%","은행 IRP 수수료 전부"),
 "FV5-RES-009":("퇴직금 5~7%","퇴직 IRP 7% 수익"),
 "FV5-RES-010":("9% 배당주 손실 상쇄","3년 배당으로 손실 회복"),
 "FV5-RES-011":("89% 배당","배당률 89%"),
 "FV5-RES-012":("중국펀드 3년 회복","중국펀드 회복 가능성"),
 "FV5-RES-013":("신입 ISA 40 연금 10","신입 월급 100만원 저축"),
 "FV5-RES-014":("재직 회사 주식 매수","협력사 주식 매수","회사 주식 집중"),
 "FV5-RES-015":("50대 무조건 은퇴","40대 월급 가장 많이"),
}

class ResidualReviewError(ValueError): pass

def need(condition, code):
    if not condition:raise ResidualReviewError(code)

def sha256(raw):
    return hashlib.sha256(raw).hexdigest()

def gitblob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

def from_json(root:Path,path:Path):
    return json.loads((root/path).read_text("utf-8"))

def verify(root:Path, *, source_zip:Path|None=None,replacement:dict|None=None):
    root=Path(root)
    raw_manifest=(root/LEDGER).read_bytes()
    if replacement is None:
        need(gitblob(raw_manifest)==PINNED_GIT_BLOB_SHA1,
             "RES15_REVIEWED_MANIFEST_BLOB_CHANGED")
    d=json.loads(raw_manifest) if replacement is None else replacement
    need(d.get("schema")=="IRE_V5_FIRST_FIVE_ORIGINAL_RESIDUAL_15_SCOPED_ADJUDICATION_V1"
         and d.get("as_of")=="2026-11-06"
         and d.get("input_private_original_archive_sha256")==KNOWN_ARCHIVE_SHA
         and d.get("historical_archive_sha256_different")==OLD_SHA
         and d.get("source_video_ids")=={str(k):v for k,v in EXPECTED_VIDEO.items()}
         and d.get("reviewed_source_spans")==15
         and d.get("new_direct_source_anchor_gaps_found")==2
         and d.get("asr_caution_cases")==1
         and d.get("prior_focused_68_and_remnant_237_candidates_preserved") is True
         and d.get("previous_89_video1_source_review_preserved") is True
         and d.get("existing_p4_29_nodes_preserved") is True
         and d.get("formal_B04_merge_count")==0
         and d.get("unseen_full_288_atomic_recall_certified") is False
         and d.get("original_audio_ambiguities_resolved")==0
         and d.get("official_context_sources_are_scoped_not_government_signed") is True
         and d.get("GitHub_CI_source_zip_replayed") is False
         and d.get("release")=="SOURCE_SPAN_CUE_HASHES_ADJUDICATED_EDUCATIONAL_SCOPE_WITH_OPEN_RESIDUALS",
         "RES15_FALSE_SOURCE_OR_FACT_APPROVAL")
    official=d.get("official_context_sources")
    need(isinstance(official,dict) and len(official)==8,
         "RES15_OFFICIAL_SOURCE_CONTEXT_UNPINNED")
    for s in official.values():
        url=urlsplit(s.get("url",""))
        need(url.scheme=="https" and url.hostname in HOSTS
             and not url.username and not url.password
             and len(s.get("scope",""))>=25,
             "RES15_OFFICIAL_CONTEXT_HOST_OR_SCOPE_INVALID")
    prior=from_json(root,PRIOR68)
    b=from_json(root,REMAINDER237)
    need(len(prior["rows"])==68 and len(b["candidate_assertions"])==237,
         "RES15_HISTORIC_CANDIDATES_CHANGED")
    a_lookup={x["id"]:x for x in prior["rows"]}
    b_lookup={x["id"]:x for x in b["candidate_assertions"]}
    sc=from_json(root,FIRSTFIVE_SOURCES)
    lookup={v["sequence"]:v for v in sc["videos"]}
    windows={}
    for n in range(2,6):
        rows=from_json(root,Path("ire/v5/validation")/
                f"v5_first_five_video_{n:02d}_window_review_20261106.json")["records"]
        windows[n]=rows
        need(lookup[n]["video_id"]==EXPECTED_VIDEO[n],
             "RES15_VIDEO_ID_NOT_IN_ORIGINAL")
    items=d.get("items",[])
    need(len(items)==15 and len({x.get("id") for x in items})==15,
         "RES15_NOT_FIFTEEN_SCOPED_REVIEWS")
    need(set(TRIGGERS)=={x["id"] for x in items},
         "RES15_QUESTION_ROUTING_UNDOCUMENTED")
    matched=0
    unmatched=0
    asr=0
    source_claim_count=0
    for j,c in enumerate(items,1):
        n=c.get("video_number")
        lo=c.get("first_cue");hi=c.get("last_cue")
        ids=c.get("prior_candidate_ids",[])
        need(c.get("id")==f"FV5-RES-{j:03d}"
             and type(n) is int and n in EXPECTED_VIDEO
             and c.get("video_id")==EXPECTED_VIDEO[n]
             and type(lo) is int and type(hi) is int
             and 1<=lo<=hi<=lookup[n]["expected_cues"]
             and re.fullmatch("[0-9a-f]{64}",str(c.get("source_span_sha256","")))
             and c.get("review_status") in ALLOWED_STATUSES
             and len(c.get("adjudicated_scope",""))>=40
             and isinstance(c.get("official_source_ids"),list)
             and all(x in official for x in c["official_source_ids"])
             and c.get("content_author")==
                 "CHATGPT_IN_SAME_TURN_ORIGINAL_TEXT_REVIEW_NOT_BLIND"
             and c.get("independent_human_claim_recall_verified") is False
             and c.get("legal_fact_or_product_terms_formally_approved") is False
             and c.get("personal_investment_action_approved") is False
             and c.get("existing_candidate_deleted") is False,
             "RES15_BAD_CUE_BOUNDARY_OR_FORGED_APPROVAL")
        exp=[x["window_id"] for x in windows[n]
             if x["first_cue"]<=hi and x["last_cue"]>=lo]
        need(c.get("source_windows")==exp and len(exp)>=1,
             "RES15_WINDOW_SPAN_NOT_ORIGINAL")
        need(isinstance(ids,list) and len(ids)==len(set(ids)),
             "RES15_PRIOR_REFERENCE_DUPLICATED")
        for pid in ids:
            if pid.startswith("FV5-A"):
                priorrow=a_lookup.get(pid)
                need(priorrow is not None and priorrow["video_number"]==n
                     and priorrow["first_cue"]<=hi and
                     priorrow["last_cue"]>=lo,
                     "RES15_PRIOR_68_PROPOSITION_NOT_QUALIFIED")
            elif pid.startswith("FV5-R"):
                priorrow=b_lookup.get(pid)
                need(priorrow is not None and priorrow["video_number"]==n
                     and lo<=priorrow["anchor_cue_number"]<=hi,
                     "RES15_PRIOR_237_ANCHOR_NOT_QUALIFIED")
            else:
                raise ResidualReviewError("RES15_UNKNOWN_CANDIDATE_ID")
            source_claim_count+=1
        status=c.get("prior_relation")
        if ids:
            need(status=="TOPIC_OR_SCOPED_PROPOSITION_OVERLAP_NOT_ATOMIC_EQUIVALENCE_CLAIM",
                 "RES15_FALSE_EXACT_EQUIVALENCE")
            matched+=1
        else:
            need(status=="NO_DIRECT_SOURCE_ANCHOR_MATCH_IN_SELECTED_68_AND_237"
                 and c["review_status"]==
                      "NEW_UNMATCHED_IN_68_237_SOURCE_ANCHOR_REGISTERS",
                 "RES15_NEW_OMISSION_NOT_QUARANTINED")
            unmatched+=1
        asr+=c["review_status"]=="ORIGINAL_AUDIO_REVIEW_REQUIRED"
    need(matched==13 and unmatched==2 and asr==1,
         "RES15_SOURCE_ADJUDICATION_COUNTS_CHANGED")
    source_replayed=False
    if source_zip is not None:
        p=Path(source_zip)
        need(p.is_file(),"RES15_ORIGINAL_ZIP_MISSING")
        need(sha256(p.read_bytes())==KNOWN_ARCHIVE_SHA,
             "RES15_ORIGINAL_ARCHIVE_HASH_DIFFERENT")
        parsed={}
        with zipfile.ZipFile(p) as z:
            for n,vid in EXPECTED_VIDEO.items():
                name=f"1-100/youtube-transcript-{vid}.srt"
                need(z.namelist().count(name)==1,
                     "RES15_ORIGINAL_SRT_MEMBER_NOT_UNIQUE")
                blob=z.read(name)
                need(sha256(blob)==lookup[n]["source_sha256"],
                     "RES15_ORIGINAL_SRT_HASH_DIFFERENT")
                parsed[n]=cue_txt(blob)
            for c in items:
                arr=parsed[c["video_number"]]
                clip=" ".join(arr[c["first_cue"]-1:c["last_cue"]])
                need(sha256(clip.encode("utf-8"))==c["source_span_sha256"],
                     "RES15_CUE_SOURCE_SPAN_CHANGED")
        source_replayed=True
    return {"schema":"IRE_V5_FIRST_FIVE_15_RESIDUAL_SOURCE_ADJUDICATION_RECEIPT_V1",
            "reviewed_original_srt_spans":15,
            "previous_68_and_237_ledger_related_source_spans":matched,
            "new_direct_source_anchor_gaps_for_adjudication":unmatched,
            "source_audio_number_discrepancies_open":asr,
            "prior_candidate_links":source_claim_count,
            "private_owner_source_zip_replayed_in_this_process":source_replayed,
            "formal_financial_fact_promotions":0,
            "legacy_master_claim_mutations":0,
            "p4_prior_29_nodes_unchanged":True,
            "full_first_five_atomic_recall_independently_verified":False,
            "full_first_five_engine_research_closure":False,
            "personal_investment_actions_approved":False}

def retrieve(root:Path,question:str,*,limit:int=3):
    verify(root)
    need(type(question) is str and question.strip() and type(limit) is int
         and 1<=limit<=15,"RES15_QUERY_INVALID")
    q=re.sub(r"\s+","",question.casefold())
    ledger=from_json(Path(root),LEDGER)
    items=[]
    for row in ledger["items"]:
        if any(re.sub(r"\s+","",t.casefold()) in q
               for t in TRIGGERS[row["id"]]):
            items.append({"review_id":row["id"],
                "video_number":row["video_number"],
                "cue_range":[row["first_cue"],row["last_cue"]],
                "scope_caveat":row["adjudicated_scope"],
                "adjudication_state":row["review_status"],
                "source_window_ids":row["source_windows"],
                "prior_candidate_ids":row["prior_candidate_ids"],
                "official_context_urls":[ledger["official_context_sources"][s]["url"]
                                         for s in row["official_source_ids"]],
                "formal_financial_fact_approved":False})
    return {"schema":"IRE_V5_FIRST_FIVE_RESIDUAL_CAUTION_RETRIEVAL_V1",
            "match_count":len(items[:limit]),
            "items":items[:limit],"release":"SCOPED_SOURCE_REVIEW_NOT_FULL_ATOMIC_CERTIFICATION"}

def audit(root:Path):
    ans=verify(root)
    for case,q in [
        ("FV5-RES-006","증권사 IRP 수수료 0원인가요?"),
        ("FV5-RES-007","IRP 1만원 연금개시 의무인가요?"),
        ("FV5-RES-011","89% 배당률이 사실인가요?"),
        ("FV5-RES-014","재직 회사 주식 매수해도 되나요?"),
        ("FV5-RES-003","한국은행 기준금리 7일물 RP와 같나요?"),
    ]:
        found={v["review_id"] for v in retrieve(root,q)["items"]}
        need(case in found,"RES15_CAUTION_NOT_RETRIEVABLE")
    ans["live_scoped_question_probes_passed"]=5
    return ans

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--source-zip",type=Path)
    p.add_argument("--question")
    args=p.parse_args()
    out=retrieve(args.root,args.question) if args.question else (
        verify(args.root,source_zip=args.source_zip) if args.source_zip else audit(args.root))
    print(json.dumps(out,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":main()
