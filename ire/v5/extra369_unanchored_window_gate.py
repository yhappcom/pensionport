"""V5 original #6/#8/#9 unanchored-window risk review, 97/78/13.

This deliberately checks what the older 36 selected claims DID NOT cover. In
optional --source-zip mode, replay all private original 3,123 cues and 175
source windows, deduce 78 source-window anchor gaps, and independently score
the 13 highest-priority uncovered windows. Without the ZIP, CI can validate
only the reviewed immutable metadata and reject approval inflation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

from .extra_video6_8_9_source_gate import (
    EXPECTED as SOURCES,
    SHA_ARCHIVE,
    audit as audit_previous,
    load as load_previous,
    rollup,
)
from .first_five_window_review_gate import source_windows
from .first_five_remnant_221_gate import cue_txt

LEDGER=Path("ire/v5/validation/extra369_175window_78gap_13risk_review_20261107.json")
LEDGER_PIN="8cf2a8f709208e0af511169b9057dc0228bfb5dd"
EVIDENCE_HOSTS={"www.law.go.kr"}
NUMBERS={6:(45,28,17,2),8:(59,30,29,4),9:(71,39,32,7)}
DETECTORS={
    "tax":r"세금|세액|비과세|과세|공제|증여|환급|연금|신고|양도|상속",
    "numeric":r"\d+\s*(?:원|만|억|%|프로|퍼센트|년)",
    "product":r"ETF|ETN|펀드|주식|채권|금리|환율|ISA|IRP|헤지|환전|주택",
    "advice":r"무조건|반드시|안전|하면|해야|필수|좋아|추천|이득|수익",
}

class UnanchoredWindowError(ValueError):
    pass

def need(valid, code):
    if not valid:
        raise UnanchoredWindowError(code)

def gitblob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def score(text):
    return sum(len(re.findall(pattern,text,re.I))
               for pattern in DETECTORS.values())

def load(root):
    blob=(Path(root)/LEDGER).read_bytes()
    need(gitblob(blob)==LEDGER_PIN,"EXTRA_GAP_REVIEWED_JSON_CHANGED")
    return json.loads(blob)

def audit(root:Path,source_zip:Path|None=None):
    root=Path(root)
    p=audit_previous(root)
    d=load(root)
    need(d.get("schema")==
          "IRE_V5_EXTRA369_ALL175_WINDOWS_UNLINKED_78_13_PRIORITY_ADJUDICATION_V1"
         and d.get("as_of")=="2026-11-07"
         and d.get("original_zip_sha256")==SHA_ARCHIVE
         and d.get("derived_from_ledger")==
             "extra_video6_8_9_3123cue_36_atomic_scope_20261107.json"
         and d.get("all_original_cues")==3123
         and d.get("all_original_windows")==175
         and d.get("previous_selected_claim_ranges")==36
         and d.get("windows_overlapping_at_least_one_existing_claim")==97
         and d.get("windows_without_direct_claim_span")==78
         and d.get("priority_unlinked_windows_selected")==13
         and d.get("remaining_unlinked_windows_not_prioritized")==65
         and d.get("signals_do_not_prove_missing_claims") is True
         and d.get("source_scoped_candidate_ledger_may_have_other_semantic_equivalents") is True
         and d.get("full_atomic_claim_recall_certified") is False
         and d.get("original_audio_verified") is False
         and d.get("all_101_to_791_dup_source_archives_available") is False
         and d.get("prior_116_master_unchanged") is True
         and d.get("prior_29_p4_education_nodes_unchanged") is True
         and d.get("formal_new_claim_approvals")==0
         and d.get("strict_graph_edges_approved")==0
         and d.get("private_raw_srt_uploaded_to_github") is False
         and d.get("release")==
           "CUE_WINDOW_GAP_TRIAGE_13_SCOPED_RISK_REVIEWS_NOT_ALL_ATOMIC_CLAIMS",
         "EXTRA_GAP_UNEARNED_RESEARCH_APPROVAL")
    need(p["original_source_cues"]==3123
         and p["original_planner_windows"]==175
         and p["scoped_source_claim_candidates"]==36
         and not p["independent_complete_atomic_recall_certified"],
         "EXTRA_GAP_PREVIOUS_SOURCE_OR_RESEARCH_CHANGED")
    prior=load_previous(root)
    candidate_ids={c["claim_id"] for c in prior["claim_candidates"]}
    prior_spans={n:[] for n in NUMBERS}
    for c in prior["claim_candidates"]:
        prior_spans[c["video_number"]].append((c["start_cue"],c["end_cue"]))
    by_video=d.get("by_video")
    need(type(by_video) is list and len(by_video)==3,
         "EXTRA_GAP_MISSING_PER_VIDEO_COUNTS")
    for item in by_video:
        n=item.get("video_no")
        need(type(n) is int and n in NUMBERS
             and tuple(item[k] for k in (
                 "source_windows","selected_claim_overlapping_windows",
                 "unlinked_windows","priority_unlinked"))==NUMBERS[n],
             "EXTRA_GAP_WINDOW_COVERAGE_COUNT_CHANGED")
    official=d.get("official_context",{})
    need(type(official) is dict and set(official)=={"KOREA_GIFT53_2026"},
         "EXTRA_GAP_OFFICIAL_SCOPE_CHANGED")
    for key,ctx in official.items():
        url=urlsplit(ctx.get("url",""))
        need(url.scheme=="https" and url.hostname in EVIDENCE_HOSTS
             and ctx.get("effective_date")=="2026-01-02"
             and ctx.get("full_tax_application_approved") is False
             and len(ctx.get("limited_scope",""))>=30,
             "EXTRA_GAP_STATUTORY_2026_SCOPE_UNSUPPORTED")
    reviews=d.get("priority_reviews")
    need(type(reviews) is list and len(reviews)==13
         and len({x.get("review_id") for x in reviews})==13
         and len({(x.get("video_no"),x.get("source_window_id"))
                  for x in reviews})==13,
         "EXTRA_GAP_THIRTEEN_REVIEW_WINDOWS_MISSING")
    priority_counts=Counter()
    for idx,item in enumerate(reviews,1):
        n=item.get("video_no")
        lo=item.get("first_cue");hi=item.get("last_cue")
        if type(n) is int and n in NUMBERS:
            priority_counts[n]+=1
        need(item.get("review_id")==f"V5-GAP-{idx:02d}"
             and type(n) is int and n in NUMBERS
             and re.fullmatch(r"W\d{5}",str(item.get("source_window_id","")))
             and type(lo) is int and type(hi) is int
             and lo>=1 and lo<=hi<=SOURCES[n][1]
             and re.fullmatch("[0-9a-f]{64}",
                              str(item.get("original_window_text_sha256","")))
             and type(item.get("lexical_risk_score")) is int
             and item["lexical_risk_score"]>=5
             and len(item.get("scoped_interpretation",""))>=45
             and len(item.get("risk_code",""))>=12
             and item.get("direct_claim_anchor_preexisting") is False
             and item.get("strict_semantic_newness_certified") is False
             and item.get("formal_financial_fact_approved") is False
             and item.get("personal_trade_approved") is False
             and len(item.get("user_query_triggers",[]))>=1
             and all(len(x)>=5 for x in item["user_query_triggers"])
             and all(x in candidate_ids for x in
                     item.get("contextually_related_36_claim_ids",[]))
             and all(x in official for x in item.get("official_source_ids",[]))
             and all(hi<a or lo>b for a,b in prior_spans[n]),
             "EXTRA_GAP_SOURCE_CUE_OR_EQUIVALENCE_FALSE")
    need(priority_counts=={6:2,8:4,9:7},
         "EXTRA_GAP_PRIORITY_COUNTS_INVALID")
    # Explicit new scope that the original 36 candidates could not anchor.
    gift=next(x for x in reviews if x["risk_code"]==
              "UNCLE_AUNT_NEPHEW_OTHER_KIN_GIFT_10M")
    need(gift["video_no"]==6
         and gift["source_window_id"]=="W00043"
         and gift["official_source_ids"]==["KOREA_GIFT53_2026"]
         and "10년" in gift["scoped_interpretation"]
         and "1,000만원" in gift["scoped_interpretation"],
         "EXTRA_GAP_OTHER_RELATIVE_GIFT_10Y_APPLICATION_BAD")

    # Only when the owner-private original source is actually given does this
    # receipt certify independent 175-window source-body and 13-score replay.
    private_replay=False
    if source_zip is not None:
        path=Path(source_zip)
        need(path.is_file(),"EXTRA_GAP_ORIGINAL_ZIP_MISSING")
        need(sha(path.read_bytes())==SHA_ARCHIVE,
             "EXTRA_GAP_ORIGINAL_ARCHIVE_CHANGED")
        observed=[]
        with zipfile.ZipFile(path) as z:
            per_video_windows={}
            for n,(vid,expect_cues,expect_windows,srt_sha,roll) in SOURCES.items():
                name=f"1-100/youtube-transcript-{vid}.srt"
                need(z.namelist().count(name)==1,
                     "EXTRA_GAP_PRIVATE_SRT_NOT_UNIQUE")
                raw=z.read(name)
                cue_bodies=cue_txt(raw)
                w=source_windows(raw)
                need(sha(raw)==srt_sha and len(cue_bodies)==expect_cues
                     and len(w)==expect_windows and rollup(w)==roll,
                     "EXTRA_GAP_PRIVATE_175_WINDOW_REPLAY_CHANGED")
                per_video_windows[n]={x["window_id"]:x for x in w}
                linked=[x for x in w if any(
                    a<=x["last_cue"] and b>=x["first_cue"]
                    for a,b in prior_spans[n])]
                unlinked=[x for x in w if x not in linked]
                scored=[]
                for wrow in unlinked:
                    a,b=wrow["first_cue"],wrow["last_cue"]
                    plain=" ".join(cue_bodies[a-1:b])
                    s=score(plain)
                    if s>=5:
                        scored.append((wrow["window_id"],a,b,
                                       wrow["primary_text_sha256"],s))
                observed.append((n,len(w),len(linked),len(unlinked),len(scored)))
                expected={(x["source_window_id"],x["first_cue"],x["last_cue"],
                           x["original_window_text_sha256"],
                           x["lexical_risk_score"]) for x in reviews
                          if x["video_no"]==n}
                need(set(scored)==expected,
                     "EXTRA_GAP_PRIVATE_THIRTEEN_PRIORITY_SCORES_CHANGED")
            need(observed==[(6,45,28,17,2),(8,59,30,29,4),
                            (9,71,39,32,7)],
                 "EXTRA_GAP_PRIVATE_78_COVERAGE_REPLAY_CHANGED")
        private_replay=True
    return {
       "schema":"IRE_V5_EXTRA369_UNANCHORED_WINDOW_RISK_REPLAY_RECEIPT_V1",
       "source_cues":3123,"source_windows":175,
       "selected_earlier_claim_candidates":36,
       "windows_directly_anchored_by_prior36":97,
       "windows_not_directly_anchored_by_prior36":78,
       "unlinked_high_signal_windows_reviewed":13,
       "lower_signal_or_context_unlinked_windows_still_open":65,
       "new_narrow_scoped_2026_gift_kinship_issue_detected":True,
       "private_owner_zip_replayed_in_this_process":private_replay,
       "private_source_windows_replayed_this_process":175 if private_replay else 0,
       "strict_new_claim_recall_certified":False,
       "independent_blind_semantic_evaluator_done":False,
       "new_formal_financial_fact_approvals":0,
       "master_116_and_education29_unchanged":True,
       "new_B04_graph_relations_approved":0,
       "personal_financial_action_approved":False,
       "release":"UNANCHORED_WINDOW_GAP_RISK_TRIAGE_PARTIAL_REVIEW_ONLY",
    }

def retrieve(root:Path,question:str,*,limit:int=3):
    need(type(question) is str and question.strip()
         and type(limit) is int and 1<=limit<=13,
         "EXTRA_GAP_BAD_QUERY")
    audit(root)
    q=re.sub(r"\s+","",question.casefold())
    matched=[]
    for x in load(root)["priority_reviews"]:
        if any(re.sub(r"\s+","",term.casefold()) in q
               for term in x["user_query_triggers"]):
            matched.append({
                "review_id":x["review_id"],
                "video_no":x["video_no"],
                "source_window_id":x["source_window_id"],
                "cue_range":[x["first_cue"],x["last_cue"]],
                "scope_caveat":x["scoped_interpretation"],
                "classification":x["status"],
                "related_prior_36":x["contextually_related_36_claim_ids"],
                "strict_newness_certified":False,
                "official_law_fact_finalized":False,
                "personal_action_approved":False})
    return {"schema":"IRE_V5_EXTRA369_MISSING_WINDOW_SOURCE_CAUTION_V1",
            "items":matched[:limit],"match_count":len(matched[:limit]),
            "strict_financial_advice_approved":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--source-zip",type=Path)
    p.add_argument("--question")
    a=p.parse_args()
    d=retrieve(a.root,a.question) if a.question else audit(a.root,a.source_zip)
    print(json.dumps(d,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    main()
