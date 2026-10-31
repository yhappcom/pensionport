#!/usr/bin/env python3
"""V3.3 source-census atomic financial semantics *proposal* extractor.

Consumes the actual SRT bytes and an independently reviewed atomic cue ledger.
Can ingest an externally generated, model-version-pinned typed proposal, but
NEVER silently fills unrecognized event/roles. All automatic outputs remain
unreviewed. Neither text similarity nor keywords can self-issue a gold label.
"""
from __future__ import annotations
from datetime import date
import json
import re
from pathlib import Path

from v30_verified_core import (
  parse_srt,verify_ledger,guard,sha256,canonical,HASH_RE,VID_RE,VERDICTS
)
from v30_semantic_frame_v33 import (
  SCHEMA,validate_financial_frame,frame_proposal_summary
)

PERCENT=re.compile(r"(?<![\w])(-?\d+(?:\.\d+)?)\s*%")
AMOUNT=re.compile(r"(?<![\w])(\d+(?:,\d{3})*(?:\.\d+)?)\s*(원|만원|억원)\b")
YEAR=re.compile(r"(?<!\d)(20\d\d)-(\d\d)-(\d\d)(?!\d)")
NUMBER=re.compile(r"(?<![\w])\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|원|만원|억원)")
INFERABLE_TYPES=frozenset((
 "subject","object","action","event_kind","modality",
 "jurisdiction","effective_date","conditions","measurement"
))

def number_proposal(text):
    """Read typed literal only. NO automatic rate-base assertions."""
    p=PERCENT.search(text)
    if p:
        return {"measure_type":"PERCENT_RATE",
                "value":p.group(1),"unit":"PERCENT",
                "period":"UNRESOLVED","rate_basis":"UNRESOLVED"}
    a=AMOUNT.search(text)
    if a:
        return {"measure_type":"CURRENCY_AMOUNT",
                "value":a.group(1).replace(",",""),
                "unit":a.group(2),"period":"UNRESOLVED",
                "rate_basis":"NOT_APPLICABLE"}
    return {"measure_type":"NONE","value":None,"unit":"NOT_APPLICABLE",
            "period":"NOT_APPLICABLE","rate_basis":"NOT_APPLICABLE"}

def tentative_date(text):
    m=YEAR.search(text)
    if m:
        s=m.group(0)
        try:
            if date.fromisoformat(s).isoformat()==s:return s
        except ValueError:pass
    return "UNRESOLVED"

def make_proposal(atom,video_id,raw_sha,source_class="REAL_ORIGINAL",
                  extractor_annotation=None,extractor_sha=None):
    """External model proposal must be bound to exact source atom hash."""
    guard(type(atom) is dict and
          isinstance(atom.get("claim_id"),str)
          and atom["claim_id"].startswith(video_id+"-") and
          atom.get("legacy_verdict") in VERDICTS,
          "EXTRACTOR_ATOM_MUST_BE_IN_VERIFIED_SOURCE_LEDGER")
    quote=atom["quote"]
    text=atom.get("claim_text",quote)
    guard(isinstance(text,str) and len(text)>=5,
          "EXTRACTOR_NEEDS_EXACT_SOURCE_QUOTE_OR_CLAIM_TEXT")
    cond={"population":"UNRESOLVED",
          "exception":"UNRESOLVED","trigger":"UNRESOLVED"}
    unresolved={"kind":"OTHER","canonical_id":"UNRESOLVED:"+atom["claim_id"]}
    frame={
        "schema":SCHEMA,
        "claim_id":atom["claim_id"],
        "source_video_id":video_id,
        "source_srt_sha256":raw_sha,
        "claim_text":text,
        "claim_text_sha256":sha256(text.encode("utf-8")),
        "cue_indices":atom["cue_indices"],
        "source_quote":quote,
        "subject":dict(unresolved),"object":dict(unresolved),
        "action":"OTHER","event_kind":"FINANCIAL_OTHER",
        "modality":"UNRESOLVED","jurisdiction":"UNRESOLVED",
        "effective_date":tentative_date(text),
        "conditions":cond,
        "measurement":number_proposal(text),
        "legacy_verdict":atom["legacy_verdict"],
        "evidence_state":("CORRECTION_ONLY" if
          atom["legacy_verdict"]=="CONTRADICTED" else "NOT_RESEARCHED"),
        "annotation_origin":("EXTERNAL_EXTRACTOR" if
                             extractor_annotation is not None
                             else "MANUAL_REVIEWER"),
        "annotation_review_status":"PROPOSED",
        "source_class":source_class,
    }
    if extractor_annotation is not None:
        guard(type(extractor_annotation) is dict
              and extractor_annotation.get("schema")==
                "V33_PINNED_MODEL_SEMANTIC_PROPOSAL_V1"
              and extractor_annotation.get("claim_id")==atom["claim_id"]
              and extractor_annotation.get("claim_text_sha256")==
                    frame["claim_text_sha256"]
              and extractor_annotation.get("source_srt_sha256")==raw_sha
              and type(extractor_sha) is str and HASH_RE.fullmatch(extractor_sha)
              and extractor_annotation.get("extractor_model_sha256")==extractor_sha
              and type(extractor_annotation.get("typed_fields")) is dict
              and set(extractor_annotation["typed_fields"])<=INFERABLE_TYPES,
              "MODEL_EXTRACTION_MUST_BE_PINNED_TO_EXACT_SOURCE_AND_FIELD_SCHEMA")
        frame.update(extractor_annotation["typed_fields"])
        # EXTERNAL_EXTRACTOR cannot self-report a human review.
        frame["annotation_review_status"]="PROPOSED"
    validate_financial_frame(frame)
    return frame

def extract_from_original(raw_srt,source_manifest,ledger,
                          external_model_proposals=None,
                          model_sha256=None):
    guard(type(source_manifest) is dict and
          source_manifest.get("schema")=="V33_ORIGINAL_SOURCE_CONTRACT_V1"
          and source_manifest.get("source_class") in
              ("REAL_ORIGINAL","SYNTHETIC_FIXTURE")
          and type(source_manifest.get("video_number")) is int
          and 1<=source_manifest["video_number"]<=791
          and isinstance(source_manifest.get("video_id"),str)
          and VID_RE.fullmatch(source_manifest["video_id"])
          and isinstance(source_manifest.get("srt_sha256"),str)
          and HASH_RE.fullmatch(source_manifest["srt_sha256"]),
          "V33_ATOMIC_SOURCE_IDENTITY_REQUIRED")
    cues=parse_srt(raw_srt,source_manifest["srt_sha256"])
    guard(len(cues)==source_manifest.get("cue_count"),
          "V33_FULL_ORIGINAL_SRT_CUE_COUNT_CHANGED")
    if source_manifest["source_class"]=="REAL_ORIGINAL":
        # A real unseen source must be independently registered, not minted
        # by the same developer after seeing its engine predictions.
        guard(source_manifest.get("video_number",0)>=261
              and source_manifest.get("provenance_status")==
                  "INDEPENDENT_CUSTODIAN_ORIGINAL_SHA_PINNED"
              and source_manifest.get("historical_001_260_exposure_checked") is True
              and source_manifest.get("audio_or_captions_source_identity_verified")
                  is True,
              "REAL_UNSEEN_SOURCE_NOT_INDEPENDENTLY_REGISTERED")
    else:
        guard(source_manifest.get("test_fixture") is True,
              "TEST_FIXTURE_MUST_NOT_IMPERSONATE_REAL_ORIGINAL")
    coverage=verify_ledger(cues,ledger,source_manifest["video_id"])
    guard(len(ledger["claims"])>0,
          "NO_ATOMIC_FINANCIAL_CLAIMS_TO_EVALUATE")
    proposals=external_model_proposals or {}
    guard(type(proposals) is dict and
          set(proposals)==set(ledger["claims"][i]["claim_id"]
                               for i in range(len(ledger["claims"])))
          if external_model_proposals is not None else
          external_model_proposals is None,
          "MODEL_MUST_RETURN_ONE_PROPOSAL_PER_ATOMIC_LEDGER_CLAIM")
    frames=[]
    for atom in ledger["claims"]:
        proposed=make_proposal(
            atom,source_manifest["video_id"],
            source_manifest["srt_sha256"],
            source_class=source_manifest["source_class"],
            extractor_annotation=proposals.get(atom["claim_id"]),
            extractor_sha=model_sha256)
        frame_proposal_summary(proposed,raw_srt)
        frames.append(proposed)
    return {
      "schema":"V33_SOURCE_CENSUS_SEMANTIC_EXTRACTION_PROPOSALS_V1",
      "video_id":source_manifest["video_id"],
      "source_sha256":source_manifest["srt_sha256"],
      "source_cue_count":len(cues),
      "reviewed_atomic_ledger_sha256":sha256(canonical(ledger)),
      "full_cue_coverage_structural_check_passed":True,
      "fully_reviewed_real_world_semantics":False,
      "source_audio_human_verified_by_this_script":False,
      "origin_of_external_model_pinned":bool(model_sha256),
      "number_of_proposed_frames":len(frames),
      "unresolved_generic_events":sum(f["event_kind"]=="FINANCIAL_OTHER"
                                      for f in frames),
      "unresolved_rate_bases":sum(
            f["measurement"]["rate_basis"]=="UNRESOLVED"
            for f in frames),
      "source_class":source_manifest["source_class"],
      "automatic_approval":False,
      "research_completion":False,
      "blinded_human_labeling_supplied":False,
      "frames":frames,
    }

def export_private_frames(path,root,result):
    """Private raw quotes/claim text must never be committed to GitHub."""
    import os
    target=Path(path).resolve()
    guard(not target.is_relative_to(Path(root).resolve()) and
          not target.exists(),
          "PRIVATE_SEMANTIC_EXTRACTION_MUST_BE_OUTSIDE_PUBLIC_GIT")
    target.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(result,f,ensure_ascii=False,indent=2)
    except Exception:
        if target.exists():target.unlink()
        raise
    return {"saved_private":True,
            "source_sha256":result["source_sha256"],
            "frames":len(result["frames"]),
            "research_completed":False}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--original-srt",type=Path,required=True)
    p.add_argument("--source-manifest",type=Path,required=True)
    p.add_argument("--reviewed-atomic-ledger",type=Path,required=True)
    p.add_argument("--private-output",type=Path,required=True)
    p.add_argument("--external-model-proposals",type=Path)
    p.add_argument("--model-sha256")
    args=p.parse_args()
    try:
        manifest=json.loads(args.source_manifest.read_text(encoding="utf-8"))
        ledger=json.loads(args.reviewed_atomic_ledger.read_text(encoding="utf-8"))
        model=(json.loads(args.external_model_proposals.read_text(encoding="utf-8"))
               if args.external_model_proposals else None)
        x=extract_from_original(args.original_srt.read_bytes(),manifest,
                                ledger,model,args.model_sha256)
        print(json.dumps(export_private_frames(args.private_output,
              args.root,x),ensure_ascii=False))
    except (ValueError,TypeError,KeyError,OSError) as e:
        print(json.dumps({"gate":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
