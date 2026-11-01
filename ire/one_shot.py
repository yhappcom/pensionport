"""Independent one-command multi-video research attempt and private audit report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from .checkpoint import safe_private_directory
from .cli import private_file,write_new_private_report
from .orchestrator import (OrchestrationPolicy,execute_independent_research,
                           unavailable_original_report)
from .source import sha256,require,VIDEO,DIGEST


def items_from_options(options):
    if options.batch_manifest:
        require(not any((options.original_srt,options.video_id,options.source_sha256)),
                "MIXED_SINGLE_AND_BATCH_FORBIDDEN")
        data=json.loads(private_file(options.batch_manifest).read_text(encoding="utf-8"))
        require(type(data) is dict and set(data)=={"schema","videos"}
                and data["schema"]=="IRE_NEW_ORIGINAL_BATCH_V1",
                "BATCH_MANIFEST_SCHEMA_INVALID")
        items=data["videos"]
    else:
        require(all((options.original_srt,options.video_id,options.source_sha256)),
                "SINGLE_ORIGINAL_FIELDS_REQUIRED")
        items=[{"video_id":options.video_id,
                "original_srt_path":options.original_srt,
                "source_sha256":options.source_sha256}]
    require(type(items) is list and 1<=len(items)<=30,
            "BATCH_SIZE_INVALID")
    seen=set()
    for item in items:
        require(type(item) is dict and set(item)=={
            "video_id","original_srt_path","source_sha256"},
            "BATCH_VIDEO_SCHEMA_INVALID")
        require(type(item["video_id"]) is str and
                VIDEO.fullmatch(item["video_id"]) is not None and
                item["video_id"] not in seen,
                "BATCH_VIDEO_ID_INVALID_OR_DUPLICATE")
        seen.add(item["video_id"])
        require(type(item["original_srt_path"]) is str and
                bool(item["original_srt_path"]),
                "BATCH_ORIGINAL_SOURCE_PATH_INVALID")
        require(type(item["source_sha256"]) is str and
                DIGEST.fullmatch(item["source_sha256"]) is not None,
                "BATCH_SOURCE_SHA256_INVALID")
    return items


def next_path(folder: Path, stem: str) -> Path:
    for index in range(1,10000):
        p=folder/(stem+"__attempt_"+f"{index:04d}"+".json")
        if not p.exists():
            return p
    raise ValueError("EXHAUSTED_PRIVATE_REPORT_ATTEMPTS")


def execute_batch(items, output_dir, policy, semantic_request_fn=None,
                  official_response_fn=None, sleep_fn=None):
    """One invocation, one immutable report per video and one summary.

    Callback overrides are for integration tests, not exposed on production CLI.
    """
    root=safe_private_directory(output_dir)
    policy.validate()
    entries=[]
    for item in items:
        try:
            source=private_file(item["original_srt_path"]).read_bytes()
        except (OSError,ValueError,TypeError):
            report=unavailable_original_report(
                item["video_id"],item["source_sha256"],policy)
        else:
            # Source fingerprint mismatch is recorded as a per-item failure.
            report=execute_independent_research(
                source,item["video_id"],item["source_sha256"],policy,
                semantic_request_fn=semantic_request_fn,
                official_response_fn=official_response_fn,sleep_fn=sleep_fn)
        report_path=next_path(root,item["video_id"]+"_"+item["source_sha256"][:16])
        write_new_private_report(str(report_path),report)
        entries.append({
            "video_id":item["video_id"],
            "source_sha256":item["source_sha256"],
            "report_path":str(report_path),
            "run_fingerprint":report["run_fingerprint"],
            "execution_status":report["execution_status"],
            "research_status":report["research_status"],
            "source_cues":report["metrics"]["source_cue_count"],
            "proposed_atoms":report["metrics"]["proposed_financial_atoms"],
            "blockers":report["blockers"],
        })
    final={
        "schema":"IRE_ONE_SHOT_BATCH_SUMMARY_V1",
        "single_invocation_completed":True,
        "video_count":len(entries),
        "private_reports_written":len(entries),
        "entries":entries,
        "research_release":"BLOCKED",
        "independently_approved_claims":0,
        "historical_research_loaded":False,
        "historical_research_cited":False,
    }
    summary_path=next_path(root,"ire_batch_summary")
    write_new_private_report(str(summary_path),final)
    final["summary_path"]=str(summary_path)
    return final


def main():
    p=argparse.ArgumentParser(description="Single invocation independent research audit")
    p.add_argument("--batch-manifest")
    p.add_argument("--original-srt")
    p.add_argument("--video-id")
    p.add_argument("--source-sha256")
    p.add_argument("--private-output-dir",required=True)
    p.add_argument("--private-semantic-checkpoints")
    p.add_argument("--semantic-model")
    p.add_argument("--research-model")
    p.add_argument("--max-discovery-claims",type=int,default=30)
    p.add_argument("--max-model-attempts",type=int,default=3)
    p.add_argument("--max-retrieval-claims",type=int,default=4000)
    p.add_argument("--skip-web-discovery",action="store_true")
    options=p.parse_args()
    try:
        policy=OrchestrationPolicy(
            model=options.semantic_model,
            research_model=options.research_model,
            max_discovery_claims=options.max_discovery_claims,
            max_model_attempts=options.max_model_attempts,
            max_retrieval_claims=options.max_retrieval_claims,
            private_checkpoint_directory=options.private_semantic_checkpoints,
            enable_primary_discovery=not options.skip_web_discovery)
        outcome=execute_batch(items_from_options(options),
                              options.private_output_dir,policy)
    except (ValueError,TypeError,KeyError,OSError,UnicodeError) as exc:
        message=str(exc)
        code=message if re.fullmatch(r"[A-Z][A-Z0-9_]{3,90}",message) else "PRIVATE_INPUT_OR_EXECUTION_FAILED"
        print(json.dumps({"execution_status":"FAILED_CLOSED",
                          "error_code":code},sort_keys=True))
        return 3
    print(json.dumps({
        "schema":outcome["schema"],
        "single_invocation_completed":True,
        "video_count":outcome["video_count"],
        "private_reports_written":outcome["private_reports_written"],
        "final_research_release":"BLOCKED",
        "approved_financial_claims":0,
        "results":[{"video_id":x["video_id"],
                    "source_cues":x["source_cues"],
                    "unreviewed_atoms":x["proposed_atoms"],
                    "blockers":x["blockers"]} for x in outcome["entries"]],
        "private_summary_path":outcome["summary_path"]
    },ensure_ascii=False,sort_keys=True))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
