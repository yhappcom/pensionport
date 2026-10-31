#!/usr/bin/env python3
"""V3.0 SRT full-cue candidate extraction, privacy-preserving work drafting.

Deterministic extraction is *proposal generation only*. Neither silence nor
keyword absence can prove a nonmaterial passage. Every cue needs independent
review and material atomic statements need full quote/evidence linkage.
"""
import argparse
import json
import os
import re
from pathlib import Path
from v30_verified_core import parse_srt,sha256,guard

MATERIAL_TERMS=re.compile(
    r"(?:연금|투자|ETF|ISA|IRP|퇴직|공제회|주식|채권|환율|금리|세금|"
    r"세액공제|과세|증여|적립|월급|월배당|포트폴리오|수익|위험|"
    r"원금|배당|매수|매도|증권|이자|분배|환전|현금흐름|"
    r"[0-9][.,0-9]*\s*(?:%|원|만원|억원|년|개월))",
    re.IGNORECASE)
NUMERIC_TERMS=re.compile(r"(?:[0-9][.,0-9]*\s*(?:%|원|만원|억원|년|개월)|복리|이율|수익률|세율)")
LEGAL_TERMS=re.compile(r"법률|법령|제도|세금|과세|납입한도|세액공제|비과세|증여")
STRATEGY_TERMS=re.compile(r"포트폴리오|리밸런싱|자산배분|성과|백테스트|장기투자")
SPLIT=re.compile(r"(?<=[.!?。])(?=\s+[^\s])")

def split_statements(cue_text):
    chunks=[]
    for line in cue_text.splitlines():
        for segment in SPLIT.split(line):
            x=segment.strip()
            if x:chunks.append(x)
    return chunks

def propose_atomic_draft(cues,video_id):
    """Never generates an APPROVED atom or claims full statement coverage."""
    guard(isinstance(video_id,str) and re.fullmatch(r"[A-Za-z0-9_-]{11}",video_id),
          "VIDEO_ID_REQUIRED_FOR_ATOMIC_DRAFT")
    guard(cues and len(cues)<100_000,"UNSUPPORTED_CUE_DENOMINATOR")
    atoms=[];rows=[]
    likely_material=0;ambiguous=0
    for cue in cues:
        proposal_ids=[]
        segments=split_statements(cue.text)
        for phrase in segments:
            num=len(atoms)+1
            guard(num<=99999,"TOO_MANY_ATOMIC_STATEMENT_CANDIDATES")
            cid=f"{video_id}-A{num:05d}"
            signs={
                "NUMERIC":bool(NUMERIC_TERMS.search(phrase)),
                "LEGAL_OR_PRODUCT":bool(LEGAL_TERMS.search(phrase)),
                "STRATEGY_OR_PERFORMANCE":bool(STRATEGY_TERMS.search(phrase)),
            }
            classes=[kind for kind,flag in signs.items() if flag]
            if not classes:classes=["QUALITATIVE"]
            flag=bool(MATERIAL_TERMS.search(phrase))
            likely_material+=int(flag);ambiguous+=int(not flag)
            atoms.append({
                "proposed_atomic_id":cid,
                "cue_index":cue.index,
                "original_quote":phrase,
                "proposal_materiality":(
                    "LIKELY_MATERIAL_REVIEW_REQUIRED" if flag
                    else "AMBIGUOUS_REVIEW_REQUIRED"),
                "proposed_claim_types":classes,
                "source_quote_sha256":sha256(phrase.encode("utf-8")),
                "review_status":"UNREVIEWED",
                "evidence_status":"NOT_RESEARCHED",
            })
            proposal_ids.append(cid)
        rows.append({
            "cue_index":cue.index,
            "proposed_atomic_ids":proposal_ids,
            "review_status":"UNREVIEWED",
            "classification":"REVIEW_REQUIRED",
            "may_not_be_auto_excluded":True,
        })
    return {
       "schema":"V30_ATOMIC_EXTRACTION_PROPOSALS_V1",
       "video_id":video_id,
       "total_source_cues":len(cues),
       "cue_reviews_required":len(rows),
       "generated_atomic_proposals":len(atoms),
       "likely_material_proposals":likely_material,
       "ambiguous_proposals":ambiguous,
       "human_approved_claims":0,
       "completed_full_statement_coverage":False,
       "cues":rows,"proposals":atoms,
    }

def private_preview(args):
    src=Path(args.original_srt)
    b=src.read_bytes()
    cues=parse_srt(b,args.sha256)
    draft=propose_atomic_draft(cues,args.video_id)
    # Do not print raw quote/text in GitHub CI logs or response by default.
    summary={k:v for k,v in draft.items() if k not in ("cues","proposals")}
    summary["source_srt_sha256"]=sha256(b)
    if args.private_out:
        out=Path(args.private_out).resolve()
        repo=Path(args.root).resolve()
        guard(not out.is_relative_to(repo),
              "PRIVATE_SOURCE_ATOMIC_DRAFT_CANNOT_BE_COMMITTED")
        guard(not out.exists(),"DO_NOT_REPLACE_EXISTING_PRIVATE_DRAFT")
        out.parent.mkdir(parents=True,exist_ok=True)
        fd=os.open(str(out),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        try:
            with os.fdopen(fd,"w",encoding="utf-8") as f:
                json.dump(draft,f,ensure_ascii=False,indent=2)
        except Exception:
            if out.exists():out.unlink()
            raise
        summary["private_proposal_saved_outside_repo"]=True
    print(json.dumps(summary,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--original-srt",required=True)
    p.add_argument("--sha256",required=True)
    p.add_argument("--video-id",required=True)
    p.add_argument("--private-out")
    args=p.parse_args()
    try:private_preview(args)
    except (ValueError,OSError,TypeError) as e:
        print(json.dumps({"gate":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
