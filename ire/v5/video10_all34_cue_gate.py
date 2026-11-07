"""All 34 original cues from #10: 8 scoped semantic groups; no blind claim approval.

Optional --source-zip independently reopens all original SRT bytes and two
V5 planner windows, then validates each of eight disjoint cue-range SHA256s.
Default CI checks immutable reviewed artifact + old #10 caveat lineage only.
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

LEDGER=Path("ire/v5/validation/video10_all34_cue_scoped_atomic_review_20261106.json")
PRIOR=Path("ire/v5/validation/first_ten_original_crossvalidation_20261106.json")
PIN="c220b1a4d43dbc4ef7db60be99a2c1d2a19c2f99"
ZIP_SHA="088869c583b2d3ed93d68e4dd5348b1f506877ea2bdc1d66466c199ec80e7716"
VIDEO_SHA="1263d79eaf2f203b81e39231a05b884f6069bd9c3e4e3e20a213ad86cfdd2c95"
VIDEO_ID="VKr060rIirM"
WINDOWS=("646a1dc7b0aef5dfbe1cc1a02356112a31fb0ace9016574a1919b6304a02d9dd",
         "7617da6e2fef01b041cfc1148efea028ecabb8746f17a87e37e9048a03e8edaa")
EXPECTED=[
 (1,4,"QUESTION_NOT_A_STATUTORY_FACT"),
 (5,8,"UNIVERSAL_ACCOUNT_SUPERIORITY_REJECTED"),
 (9,12,"ORDINARY_TAX_SCOPE_OVERGENERALIZED"),
 (13,16,"CONDITIONAL_TAX_DEFERRAL"),
 (17,20,"NONDEDUCTED_BASIS_REQUIRES_PROOF"),
 (21,25,"PENSION_TAX_RATE_CONDITIONAL"),
 (26,31,"IRP_PARTIAL_WITHDRAWAL_NOT_ANYTIME"),
 (32,34,"CONCLUSION_REPEATS_SCOPED_OPINION"),
]
ALLOWED={"nts.go.kr","www.samsungpop.com","regulation.krx.co.kr","eiec.kdi.re.kr"}

class ShortVideoSourceError(ValueError): pass

def require(ok,code):
    if not ok:raise ShortVideoSourceError(code)

def sha(raw:bytes):
    return hashlib.sha256(raw).hexdigest()

def gitblob(raw:bytes):
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

def load(root:Path):
    raw=(Path(root)/LEDGER).read_bytes()
    require(gitblob(raw)==PIN,"SHORT10_REVIEWED_LEDGER_BLOB_CHANGED")
    return json.loads(raw)

def audit(root:Path,source_zip:Path|None=None):
    root=Path(root)
    d=load(root)
    require(d.get("schema")=="IRE_V5_EXTRA_VIDEO10_ALL_34_CUE_SOURCE_ATOMIC_GROUP_CENSUS_V1"
            and d.get("as_of")=="2026-11-06"
            and d.get("video_number")==10
            and d.get("video_id")==VIDEO_ID
            and d.get("source_srt_sha256")==VIDEO_SHA
            and d.get("source_archive_zip_sha256")==ZIP_SHA
            and d.get("original_srt_cue_count")==34
            and d.get("source_window_count")==2
            and d.get("source_window_sha256")==list(WINDOWS)
            and d.get("all_34_cues_assigned_one_disposition_group") is True
            and d.get("source_semantics_chat_host_reviewed") is True
            and d.get("independent_blind_atomic_recall_certified") is False
            and d.get("original_audio_independently_rechecked") is False
            and d.get("current_legal_rules_for_every_taxpayer_approved") is False
            and d.get("formal_financial_knowledge_nodes_approved")==0
            and d.get("prior_cv010_four_risk_cases_preserved") is True
            and d.get("compilation_video7_excluded_from_independent_blind_holdout") is True
            and d.get("prior_116_master_unchanged") is True
            and d.get("p4_29_education_nodes_unchanged") is True
            and d.get("release")==
            "ORIGINAL_34_CUE_8_SCOPED_GROUPS_RESEARCHED_NOT_INDEPENDENT_ATOMIC_CERTIFICATE",
            "SHORT10_UNEARNED_FINANCIAL_APPROVAL")
    official=d.get("official_context",{})
    require(type(official) is dict and len(official)==4,
            "SHORT10_OFFICIAL_CONTEXT_INCOMPLETE")
    for sid,context in official.items():
        u=urlsplit(context.get("url",""))
        require(u.scheme=="https" and u.hostname in ALLOWED
                and not u.username and not u.password
                and len(context.get("verified_scope",""))>=30
                and context.get("not_government_signed_snapshot") is True
                and bool(context.get("as_of")),
                "SHORT10_OFFICIAL_CONTEXT_UNRELIABLE_"+sid)
    prior=json.loads((root/PRIOR).read_text("utf-8"))
    prior_risks={x["case_id"] for x in prior["risk_challenges"]
                 if x["video_no"]==10}
    require(len(prior_risks)==4,"SHORT10_PRIOR_FOUR_RISKS_CHANGED")
    items=d.get("groups")
    require(type(items) is list and len(items)==8,
            "SHORT10_NOT_ALL_34_CUES_REVIEWED")
    previous=0
    for i,(row,exp) in enumerate(zip(items,EXPECTED),1):
        a,b,kind=exp
        require(row.get("group_id")==f"V10-C{i:02d}"
                and row.get("start_cue")==a
                and row.get("end_cue")==b
                and a==previous+1
                and row.get("disposition")==kind
                and re.fullmatch("[0-9a-f]{64}",str(row.get("combined_cue_sha256","")))
                and row.get("source_window_ids")==(
                    ["W00001"] if b<=18 else (["W00002"] if a>18 else ["W00001","W00002"]))
                and len(row.get("scoped_meaning",""))>=25
                and 1<=len(row.get("query_phrases",[]))<=4
                and all(len(t)>=5 for t in row["query_phrases"])
                and row.get("formal_tax_law_fact_approved") is False
                and row.get("unrestricted_partial_withdrawal_approved") is False
                and row.get("personalized_advice_trade_order_approved") is False
                and all(sid in official for sid in row.get("official_ids",[]))
                and all(rid in prior_risks for rid in row.get("prior_crossvideo_risk_ids",[])),
                "SHORT10_CUE_PROPOSITION_OR_PROVENANCE_INVALID")
        previous=b
    require(previous==34,"SHORT10_CUE_TRAILING_UNREVIEWED")
    private_replayed=False
    if source_zip is not None:
        p=Path(source_zip)
        require(p.is_file(),"SHORT10_PRIVATE_SOURCE_ZIP_MISSING")
        require(sha(p.read_bytes())==ZIP_SHA,"SHORT10_SOURCE_ARCHIVE_CHANGED")
        with zipfile.ZipFile(p) as z:
            name=f"1-100/youtube-transcript-{VIDEO_ID}.srt"
            require(z.namelist().count(name)==1,"SHORT10_ORIGINAL_SRT_NOT_UNIQUE")
            raw=z.read(name)
            require(sha(raw)==VIDEO_SHA,"SHORT10_ORIGINAL_BYTES_CHANGED")
            cues=cue_txt(raw);win=source_windows(raw)
            require(len(cues)==34 and len(win)==2 and
                    tuple(x["primary_text_sha256"] for x in win)==WINDOWS
                    and win[0]["first_cue"]==1 and win[0]["last_cue"]==18
                    and win[1]["first_cue"]==19 and win[1]["last_cue"]==34,
                    "SHORT10_WINDOWS_NOT_REPLAYED")
            for r in items:
                content=" ".join(cues[r["start_cue"]-1:r["end_cue"]])
                require(sha(content.encode())==r["combined_cue_sha256"],
                        "SHORT10_ORIGINAL_EIGHT_GROUP_HASH_CHANGED")
        private_replayed=True
    return {
      "schema":"IRE_V5_VIDEO10_ALL_34_SOURCE_CUES_SCOPED_GROUP_RECEIPT_V1",
      "original_video_number":10,
      "source_cues_dispositioned":34,
      "original_v5_source_windows":2,
      "source_cue_groups_researched":8,
      "prior_risk_cases_consistency_checked":4,
      "private_original_source_replayed_this_process":private_replayed,
      "private_original_cues_replayed_this_process":34 if private_replayed else 0,
      "new_final_financial_fact_approvals":0,
      "full_five_video_atomic_recall_certified":False,
      "extra_five_blind_holdout_grade_approved":False,
      "personal_account_withdrawal_action_approved":False,
      "release":"VIDEO10_SOURCE_CUE_DISPOSITIONED_EDUCATIONAL_SCOPE_NOT_PERSONAL_ADVICE",
    }

def retrieve(root:Path,question:str,*,limit:int=3):
    require(type(question) is str and bool(question.strip())
            and type(limit) is int and 1<=limit<=8,
            "SHORT10_QUERY_INVALID")
    audit(root)
    d=load(root)
    phrase=re.sub(r"\s+","",question.casefold())
    matched=[]
    for r in d["groups"]:
        if any(re.sub(r"\s+","",k.casefold()) in phrase
               for k in r["query_phrases"]):
            matched.append({
                "review_id":r["group_id"],
                "source_cues":[r["start_cue"],r["end_cue"]],
                "disposition":r["disposition"],
                "scope_caveat":r["scoped_meaning"],
                "related_prior_crossvideo_ids":r["prior_crossvideo_risk_ids"],
                "current_financial_fact_approved":False,
            })
    return {"schema":"IRE_V5_VIDEO10_SCOPED_RETRIEVAL_V1",
            "items":matched[:limit],
            "match_count":len(matched[:limit]),
            "personal_financial_action_allowed":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--source-zip",type=Path)
    p.add_argument("--question")
    a=p.parse_args()
    result=retrieve(a.root,a.question) if a.question is not None else audit(a.root,a.source_zip)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":main()
