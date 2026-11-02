"""Source-only, deterministic V3 warning triage for private research sessions.

Find *candidate* source cue locations for current-checkpoint semantic review
warnings. This is a review index, NOT a correction, gold label, or certificate:
no warning is auto-dismissed and no original/answer checkpoint is edited.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

from .checkpoint import safe_private_directory
from .cli import private_file
from .source import require, sha256, text_norm
from .v3_orchestrator import ChatBatchQueue
from .v3_semantic_audit import (window_semantic_audit, PERIODICITY,
                                PRODUCT_TERMS)

SCHEMA = "IRE_V3_PRIVATE_SEMANTIC_WARNING_TRIAGE_V1"


def _canon(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _match(code, text):
    if code.startswith("UNSUPPORTED_SPECIFIC_PRODUCT_"):
        product = code.split("UNSUPPORTED_SPECIFIC_PRODUCT_",1)[1]
        return any(re.search(alias, text, re.I)
                   for alias in PRODUCT_TERMS.get(product, ()))
    if code.startswith("UNSUPPORTED_") and code.endswith("_SOURCE_UNIT"):
        unit = code.removeprefix("UNSUPPORTED_").removesuffix("_SOURCE_UNIT")
        return PERIODICITY.get(unit, re.compile(r"(?!x)x")).search(text) is not None
    return False


def _locate_source(session, packet, warning):
    code = warning["code"]
    if not code.startswith("UNSUPPORTED_"):
        return "OPEN_NONLEXICAL_REVIEW", [], []
    primary = packet["primary_cues"]
    start = primary[0]["cue_index"]
    # A source cue is primary to exactly one context window; do not
    # automatically turn nearby cue data into citation for this claim.
    primary_ids = [x["cue_index"] for x in primary
                   if _match(code,x["text"])]
    if primary_ids:
        return "PRIMARY_WINDOW_CUE_AVAILABLE_REQUOTE_REQUIRED", primary_ids, []
    before = [c for c in session.cues
              if start - 100 <= c.index < start]
    before_ids = [c.index for c in before if _match(code,c.text)]
    if before_ids:
        return "PRIOR_SOURCE_CONTEXT_ONLY_REVIEW_REQUIRED", [], before_ids[-8:]
    return "NO_DIRECT_SOURCE_TERM_WITHIN_100_CUES_REVIEW_REQUIRED", [], []


def build_warning_triage(queue):
    require(type(queue).__name__ == "ChatBatchQueue" and
            type(queue.sessions) is list,
            "V3_TRIAGE_SOURCE_QUEUE_REQUIRED")
    rows = []
    for session in queue.sessions:
        for window in session.windows:
            answer = session._answer(window["window_id"])
            if answer is None:
                continue
            packet = session.packet(window["window_id"])
            audit = window_semantic_audit(packet, answer)
            for warning in audit["warnings"]:
                where, primary, prior = _locate_source(session,packet,warning)
                ordinal = warning.get("claim_ordinal")
                cited = (answer["claims"][ordinal-1]["source_refs"]
                         if ordinal is not None else [])
                ref = {
                    "video_id":session.video_id,
                    "original_sha256":session.digest,
                    "session_id":session.session_id,
                    "window_id":window["window_id"],
                    "packet_sha256":packet["packet_sha256"],
                    "claim_ordinal":ordinal,
                    "cue_index":warning.get("cue_index"),
                    "code":warning["code"],
                    "review_route":where,
                    "primary_candidate_cue_indices":primary,
                    "prior_context_candidate_cue_indices":prior,
                    "source_quote_sha256":sha256(_canon(cited)),
                    "human_or_external_gold_verified":False,
                    "warning_dismissed":False,
                    "needs_claim_specific_review":True,
                }
                ref["warning_id"] = sha256(_canon(ref))[:28]
                rows.append(ref)
    rows.sort(key=lambda x:(x["video_id"],x["window_id"],
                            x["claim_ordinal"] or 0,x["code"]))
    source_status = queue.status()
    summary = {}
    for row in rows:
        summary[row["review_route"]] = summary.get(row["review_route"],0)+1
    body = {
        "schema":SCHEMA,
        "source_batch_sha256":source_status["batch_fingerprint"],
        "original_cue_count":source_status["total_cues"],
        "accepted_window_count":source_status["accepted_windows"],
        "unprocessed_window_count":source_status["remaining_windows"],
        "warning_count":len(rows),
        "still_require_semantic_review":len(rows),
        "human_verified_resolutions":0,
        "classification_counts":summary,
        "warnings":rows,
        "model_self_review_not_independent_gold":True,
        "ready_for_financial_fact_approval":False,
    }
    return {**body,"report_sha256":sha256(_canon(body))}


def save_warning_triage(report,directory):
    require(type(report) is dict and report.get("schema")==SCHEMA and
            sha256(_canon({k:v for k,v in report.items()
                           if k!="report_sha256"})) == report.get("report_sha256"),
            "V3_TRIAGE_REPORT_INVALID")
    root = safe_private_directory(directory)
    target = root/("ire_v3_warning_triage_"+report["report_sha256"][:24]+".json")
    fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        with os.fdopen(fd,"wb") as handle:
            handle.write(_canon(report));handle.flush();os.fsync(handle.fileno())
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return str(target)


def main():
    ap=argparse.ArgumentParser(description="Source-cue review triage, no auto approval")
    ap.add_argument("operation",choices=["inspect"])
    ap.add_argument("--private-manifest",required=True)
    ap.add_argument("--private-report-dir",required=True)
    args=ap.parse_args()
    try:
        batch=json.loads(private_file(args.private_manifest).read_text(encoding="utf-8"))
        report=build_warning_triage(ChatBatchQueue(batch))
        saved=save_warning_triage(report,args.private_report_dir)
        print(json.dumps({"schema":SCHEMA,"warning_count":report["warning_count"],
                          "still_require_semantic_review":report["still_require_semantic_review"],
                          "classification_counts":report["classification_counts"],
                          "report_sha256":report["report_sha256"],
                          "private_path":saved,"financial_facts_approved":0},sort_keys=True))
        return 0
    except (ValueError, KeyError, TypeError, OSError, UnicodeError):
        print(json.dumps({"schema":"IRE_V3_WARNING_TRIAGE_ERROR","status":"FAILED_CLOSED"}))
        return 3


if __name__=="__main__":raise SystemExit(main())