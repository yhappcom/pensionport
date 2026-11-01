#!/usr/bin/env python3
"""Source-first independent research command line (private artifacts only)."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from .source import sha256, source_record, require
from .claims import validate_annotations
from .retrieval import related_proposals
from .research import pending_research
from .semantics import InferenceConfig, interpret_original

REPOSITORY=Path(__file__).resolve().parents[1]


def run(raw: bytes, digest: str, video_id: str,
        annotation: dict | None = None) -> dict:
    # Source analysis does not depend on previous studies/claim ledgers.
    source=source_record(raw,video_id,digest)
    if annotation is None:
        return {
            "schema":"IRE_INDEPENDENT_RESEARCH_REPORT_V1",
            "source":source,
            "annotation_result":None,
            "relation_result":None,
            "research_worklist":None,
            "automatically_inferred_financial_claims":0,
            "approved_claims":0,
            "previous_research_cited":False,
            "source_only_analysis":True,
            "production_release":"BLOCKED_NEEDS_NEW_FINANCIAL_SEMANTIC_ANNOTATIONS"
        }
    validation=validate_annotations(raw,digest,video_id,annotation)
    relations=related_proposals(annotation,top_k=10,audit_count=8)
    worklist=pending_research(annotation)
    return {
        "schema":"IRE_INDEPENDENT_RESEARCH_REPORT_V1",
        "source":source,
        "annotation_result":validation,
        "relation_result":relations,
        "research_worklist":worklist,
        "approved_claims":0,
        "previous_research_cited":False,
        "source_only_analysis":False,
        "production_release":"BLOCKED_PENDING_SOURCE_MEANING_AND_EVIDENCE_REVIEW"
    }


def private_file(path: str, read_required: bool = True) -> Path:
    p=Path(path).expanduser().resolve()
    require(not p.is_relative_to(REPOSITORY),
            "PRIVATE_FILE_MUST_NOT_BE_STORED_INSIDE_GIT_REPOSITORY")
    if read_required:
        require(p.is_file(), "INPUT_FILE_NOT_FOUND")
    return p


def write_new_private_report(path: str, data: dict) -> None:
    destination=private_file(path,read_required=False)
    require(not destination.exists(), "PRIVATE_REPORT_OVERWRITE_FORBIDDEN")
    destination.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as file:
            json.dump(data,file,ensure_ascii=False,indent=2,allow_nan=False)
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def main() -> None:
    ap=argparse.ArgumentParser(description="Independent research, no legacy studies")
    ap.add_argument("--original-srt",required=True)
    ap.add_argument("--source-sha256",required=True)
    ap.add_argument("--video-id",required=True)
    ap.add_argument("--private-report",required=True)
    ap.add_argument("--private-annotations")
    ap.add_argument("--private-semantic-checkpoints",
                    help="Private resume directory outside repository")
    ap.add_argument("--semantic-model",
                    help="Execute live model inference; requires OPENAI_API_KEY")
    args=ap.parse_args()
    source=private_file(args.original_srt)
    destination=private_file(args.private_report,read_required=False)
    require(not destination.exists(), "PRIVATE_REPORT_OVERWRITE_FORBIDDEN")
    require(not (args.semantic_model and args.private_annotations),
            "SEMANTIC_MODEL_AND_EXTERNAL_ANNOTATIONS_MUTUALLY_EXCLUSIVE")
    require(not args.private_semantic_checkpoints or args.semantic_model,
            "CHECKPOINTS_REQUIRE_SEMANTIC_MODEL")
    original=source.read_bytes()
    annotation=None
    if args.private_annotations:
        annotation=json.loads(private_file(
            args.private_annotations).read_text(encoding="utf-8"))
    semantic=None
    if args.semantic_model:
        require(sha256(original)==args.source_sha256,"SOURCE_SHA256_MISMATCH")
        semantic=interpret_original(original,args.video_id,
                                    InferenceConfig(model=args.semantic_model),
                                    private_checkpoint_directory=args.private_semantic_checkpoints)
        annotation=semantic["annotation_manifest"]
    result=run(original,args.source_sha256,args.video_id,annotation)
    if semantic is not None:
        result["private_semantic_annotation_manifest"]=semantic["annotation_manifest"]
        result["semantic_execution"]={
            "schema":semantic["schema"],
            "inference_mode":semantic["inference_mode"],
            "model_name":semantic["model_name"],
            "completed_window_count":semantic["completed_window_count"],
            "previously_cached_window_count":semantic["previously_cached_window_count"],
            "window_count":semantic["window_count"],
            "validated_annotated_claims":semantic["validation"]["proposed_atomic_claims"],
            "research_complete":False
        }
    write_new_private_report(args.private_report,result)
    # Do not print original subtitles, model output, claim text or personal data.
    preview={
        "schema":result["schema"],
        "source_sha256":result["source"]["source_sha256"],
        "cue_count":result["source"]["cue_count"],
        "context_windows":len(result["source"]["windows"]),
        "proposed_claims":(
            result["annotation_result"]["proposed_atomic_claims"]
            if result["annotation_result"] is not None else 0),
        "all_claims_unreviewed":True,
        "research_complete":False,
        "private_report_written":True,
        "production_release":result["production_release"],
        "inference_executed":"semantic_execution" in result
    }
    print(json.dumps(preview,sort_keys=True))


if __name__=="__main__":
    try:
        main()
    except (ValueError,TypeError,KeyError,OSError) as exc:
        # Always report error codes, never leak transcript/annotation fields.
        print(json.dumps({"gate":"FAIL","error":str(exc)},sort_keys=True))
        raise SystemExit(1)
