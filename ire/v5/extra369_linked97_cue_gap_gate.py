"""Claim-linked source window residual-cue gate: 97 windows, 506 cue positions.

When --source-zip is supplied, reconstruct exact owner-private original
#6/#8/#9 cues, 175 planner windows, 36 selected source spans, and all
53 residual-window source hashes and 9 risk positions. Without original
bytes, CI validates the frozen, bounded research manifest only. Neither
mode proves complete atomic recall or authorizes financial tax advice.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

from .extra_video6_8_9_source_gate import (
    EXPECTED, SHA_ARCHIVE, load as load_36, rollup)
from .extra369_low65_source_gate import audit as audit_65
from .first_five_window_review_gate import source_windows
from .first_five_remnant_221_gate import cue_txt

LEDGER=Path("ire/v5/validation/extra369_97linked_506partial_9risk_20261107.json")
LEDGER_PIN="282808ec62ade5527a6065f11b6b2a459c18a471"
PATTERNS=(
 r"\d+(?:[.,]\d+)?\s*(?:%|퍼센트|프로)",
 r"\d+(?:[.,]\d+)?\s*(?:원|만|억|조|년|개월)",
 r"증여|세금|연금|과세|보험|IRP|ISA|수익|주식|ETF|투자|환율|엔화|환전|달러|배당",
 r"무조건|반드시|사세요|투자|해야|좋아|금리|불리|수수료|포트|위험|안전|마진|헤지|비과세",
)
PER_VIDEO={6:(807,45,28,504,369,135,16,2),
           8:(1039,59,30,540,387,153,15,2),
           9:(1277,71,39,702,484,218,22,5)}

class LinkedPartialCueError(ValueError):
    pass

def need(valid,code):
    if not valid:raise LinkedPartialCueError(code)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def blob_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

def read(root):
    blob=(Path(root)/LEDGER).read_bytes()
    need(blob_sha(blob)==LEDGER_PIN,"LINKED97_SOURCE_REVIEW_MANIFEST_CHANGED")
    return json.loads(blob)

def audit(root:Path,source_zip:Path|None=None):
    root=Path(root)
    prior=audit_65(root)
    d=read(root)
    need(d.get("schema")=="IRE_V5_EXTRA369_LINKED97_PARTIAL_506_SOURCE_CUE_RISK_CENSUS_V1"
         and d.get("as_of")=="2026-11-07"
         and d.get("source_zip_sha256")==SHA_ARCHIVE
         and d.get("source_claim_36")=="extra_video6_8_9_3123cue_36_atomic_scope_20261107.json"
         and d.get("source_low65")=="extra369_65_low_keyword_windows_meaning_review_20261107.json"
         and d.get("source_total_cues")==3123
         and d.get("source_total_windows")==175
         and d.get("source_claim_36_unique_covered_cues")==1240
         and d.get("unanchored_cues_anywhere")==1883
         and d.get("prior78_unlinked_windows_cues")==1377
         and d.get("prior97_linked_window_total_cues")==1746
         and d.get("prior97_linked_window_cues_with_selected_claim_anchor")==1240
         and d.get("remaining_unanchored_cues_inside97")==506
         and d.get("linked_windows_total")==97
         and d.get("linked_windows_with_residual_cues")==53
         and d.get("linked_windows_fully_covered_by_any_selected_claim_range")==44
         and d.get("lexical_score_gte5_window_count")==9
         and d.get("source_residual_53_window_proof_rollup_sha256")==
             "516a32340ff758d0297f858ea906fea2c2a24479a4b32696ef1b0b8fa7233b6f"
         and d.get("remaining_source_cue_positions_are_not_independent_atom_counts") is True
         and d.get("original_source_reopened_inside_github_ci") is False
         and d.get("independent_complete_claim_recall_proven") is False
         and d.get("prior_78_window_semantic_dispositions_preserved") is True
         and d.get("prior_13_high_risk_and_19_low_risk_cautions_preserved") is True
         and d.get("formal_B04_knowledge_promotions")==0
         and d.get("strict_existing_116_equivalence_approved")==0
         and d.get("existing_p4_29_untouched") is True
         and d.get("release")==
           "97_WINDOWS_PARTIAL_CUE_COVERAGE_AND_NINE_HIGH_SIGNAL_SCOPE_REVIEWS_NO_COMPLETE_ATOMIC_CLAIM_RECALL",
         "LINKED97_UNEARNED_ATOMIC_CLAIM_COMPLETENESS")
    need(prior["all_78_previously_unlinked_windows_triaged"]==78
         and prior["additional_low_keyword_financial_cautions"]==19
         and prior["remaining_atomic_completeness_gaps_in_97_linked_windows"]=="UNKNOWN",
         "LINKED97_PRIOR_78_MEANING_REVIEW_CHANGED")
    byvideo=d.get("by_video")
    need(type(byvideo) is list and len(byvideo)==3
         and [x.get("video_number") for x in byvideo]==[6,8,9],
         "LINKED97_SOURCE_VIDEOS_MISSING")
    for row in byvideo:
        n=row["video_number"]
        expected=PER_VIDEO[n]
        actual=tuple(row.get(k) for k in (
            "source_cues","source_windows","linked_windows",
            "linked_windows_total_cues","selected_claim_covered_cues",
            "residual_cues","partial_windows","high_signal_partial_windows"))
        need(actual==expected,
             "LINKED97_PER_VIDEO_CUE_WINDOW_COUNT_MISMATCH")
    ctx=d.get("official_context",{})
    need(type(ctx) is dict and set(ctx)=={"KOREA_PERIODIC_GIFT_REGULATION"},
         "LINKED97_PERIODIC_GIFT_LAW_SOURCE_NOT_LISTED")
    c=ctx["KOREA_PERIODIC_GIFT_REGULATION"]
    urls=c.get("urls",[])
    need(type(urls) is list and len(urls)==2
         and urlsplit(urls[0]).hostname=="law.go.kr"
         and urlsplit(urls[1]).hostname=="lawtrack.kr"
         and c.get("checked_date")=="2026-11-07"
         and len(c.get("scope",""))>=45
         and c.get("blanket_zero_tax_approved") is False,
         "LINKED97_GIFT_DISCOUNT_SCOPE_UNRELIABLE")
    risks=d.get("high_signal_cue_risk_reviews")
    need(type(risks) is list and len(risks)==9
         and len({(x.get("video_number"),x.get("source_window_id"))
                  for x in risks})==9,
         "LINKED97_NINE_HIGHSIGNAL_REVIEWS_MISSING")
    known={(6,"W00037"),(6,"W00039"),
           (8,"W00014"),(8,"W00055"),
           (9,"W00002"),(9,"W00018"),(9,"W00029"),
           (9,"W00036"),(9,"W00056")}
    need({(x.get("video_number"),x.get("source_window_id")) for x in risks}==known,
         "LINKED97_HIGH9_ORIGINAL_WINDOW_ID_CHANGED")
    for i,row in enumerate(risks,1):
        need(row.get("id")==f"V5-PART-{i:02d}"
             and type(row.get("start_residual_cue")) is int
             and type(row.get("end_residual_cue")) is int
             and row["start_residual_cue"]<=row["end_residual_cue"]
             and row.get("lexical_risk_score")>=5
             and row.get("residual_cue_count")>=1
             and re.fullmatch("[0-9a-f]{64}",str(row.get("residual_text_sha256","")))
             and len(row.get("risk_code",""))>=12
             and len(row.get("scoped_interpretation",""))>=45
             and len(row.get("question_triggers",[]))==2
             and all(len(q)>=5 for q in row["question_triggers"])
             and all(sid in ctx for sid in row.get("official_context_ids",[]))
             and row.get("independent_atomic_uniqueness_certified") is False
             and row.get("exact_current_legal_treatment_for_all_households_approved") is False
             and row.get("personal_trade_advice_approved") is False,
             "LINKED97_UNAPPROVED_PARTIAL_FINANCIAL_FACT")
    private_replayed=False
    if source_zip is not None:
        p=Path(source_zip)
        need(p.is_file(),"LINKED97_PRIVATE_ZIP_MISSING")
        need(sha(p.read_bytes())==SHA_ARCHIVE,"LINKED97_PRIVATE_ARCHIVE_CHANGED")
        old=load_36(root)
        span_by_video={n:[] for n in PER_VIDEO}
        for x in old["claim_candidates"]:
            span_by_video[x["video_number"]].append((x["start_cue"],x["end_cue"]))
        records=[]
        with zipfile.ZipFile(p) as z:
            for n,(vid,ncues,nwindows,srtsha,roll) in EXPECTED.items():
                member=f"1-100/youtube-transcript-{vid}.srt"
                need(z.namelist().count(member)==1,
                     "LINKED97_ORIGINAL_SRT_MISSING")
                raw=z.read(member)
                cues=cue_txt(raw);windows=source_windows(raw)
                need(sha(raw)==srtsha and len(cues)==ncues
                     and len(windows)==nwindows and rollup(windows)==roll,
                     "LINKED97_ORIGINAL_175_WINDOWS_CHANGED")
                covered=set(k for a,b in span_by_video[n] for k in range(a,b+1))
                for w in windows:
                    a,b=w["first_cue"],w["last_cue"]
                    if not any(u<=b and v>=a for u,v in span_by_video[n]):
                        continue
                    remain=[k for k in range(a,b+1) if k not in covered]
                    if not remain:
                        continue
                    value=" ".join(cues[k-1] for k in remain)
                    sc=sum(len(re.findall(pat,value,re.I)) for pat in PATTERNS)
                    records.append((n,w["window_id"],len(remain),sc,sha(value.encode())))
        packed="".join(f"{n}|{wid}|{cnt}|{sc}|{digest}\n"
                       for n,wid,cnt,sc,digest in records).encode()
        need(len(records)==53 and
             sha(packed)==d["source_residual_53_window_proof_rollup_sha256"],
             "LINKED97_PRIVATE_RESIDUAL_53_HASH_REPLAY_FAILED")
        high={(n,wid):(cnt,sc,digest) for n,wid,cnt,sc,digest in records if sc>=5}
        need(len(high)==9,"LINKED97_PRIVATE_HIGH9_NOT_REPLAYED")
        for row in risks:
            key=(row["video_number"],row["source_window_id"])
            need(high.get(key)==(row["residual_cue_count"],
                                 row["lexical_risk_score"],
                                 row["residual_text_sha256"]),
                 "LINKED97_PRIVATE_NINE_CUE_CONTENT_HASH_MISMATCH")
        private_replayed=True
    return {
       "schema":"IRE_V5_EXTRA369_LINKED97_506_PARTIAL_CUE_SOURCE_RECEIPT_V1",
       "source_total_cues":3123,
       "source_windows_total":175,
       "selected_source_claim_candidates":36,
       "already_meaning_reviewed_entirely_unlinked_windows":78,
       "claim_linked_windows":97,
       "selected_claim_span_cues":1240,
       "unanchored_cues_within_linked_windows":506,
       "linked_windows_containing_unanchored_cues":53,
       "linked_windows_with_no_cue_gap":44,
       "lexical_risk_high_windows_within_partial53":9,
       "actual_private_srt_replayed_in_this_process":private_replayed,
       "private_original_windows_replayed_in_this_process":175 if private_replayed else 0,
       "independently_blind_atom_recall_certified":False,
       "all_506_residual_cue_positions_are_missing_atomic_claims":False,
       "new_strict_formal_financial_claim_approvals":0,
       "existing_116_master_and_29_p4_unchanged":True,
       "release":"LINKED_WINDOW_SOURCE_CUE_COVERAGE_AUDIT_NOT_COMPLETE_ATOMIC_SEMANTIC_COVERAGE",
    }

def retrieve(root:Path,question:str,*,limit:int=3):
    need(type(question) is str and question.strip()
         and type(limit) is int and 1<=limit<=9,
         "LINKED97_QUERY_INVALID")
    audit(root)
    data=read(root)
    q=re.sub(r"\s+","",question.casefold())
    items=[]
    for r in data["high_signal_cue_risk_reviews"]:
        if any(re.sub(r"\s+","",x.casefold()) in q
               for x in r["question_triggers"]):
            items.append({
                "review_id":r["id"],
                "video_number":r["video_number"],
                "window_id":r["source_window_id"],
                "residual_cue_range":[r["start_residual_cue"],r["end_residual_cue"]],
                "scope_caveat":r["scoped_interpretation"],
                "status":"SOURCE_RESIDUAL_NOT_FORMALLY_APPROVED",
                "independent_full_atomic_claim_recall_proven":False,
                "personal_financial_order_authorized":False,
            })
    return {"schema":"IRE_V5_EXTRA369_LINKED97_RESIDUAL_CUE_RETRIEVAL_V1",
            "items":items[:limit],"match_count":min(len(items),limit),
            "formal_financial_fact_approvals":0}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--source-zip",type=Path)
    p.add_argument("--question")
    a=p.parse_args()
    r=retrieve(a.root,a.question) if a.question else audit(a.root,a.source_zip)
    print(json.dumps(r,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    main()
