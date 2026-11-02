"""Pre-registered, source-only ORIGINAL SRT review task packets.

No model-generated claim, checkpoint answer, older study or ranking is copied
into the two independent review task packets. Two human reviewer assignments
and third adjudicator's actual materials are external inputs, NEVER inferred
from a fabricated reviewer_id or self-attestation. All source text stays private.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets

from .checkpoint import safe_private_directory
from .cli import private_file
from .source import require, sha256
from .v3_orchestrator import ChatBatchQueue

SCHEMA = "IRE_V3_SOURCE_FIRST_HUMAN_REVIEW_TASKS_V1"


def _serialize(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def plan_blind_review(queue, sample_per_video=3, private_seed=None):
    require(type(queue).__name__ == "ChatBatchQueue" and
            1 <= sample_per_video <= 20 and
            (private_seed is None or
             (type(private_seed) is str and len(private_seed) >= 32)),
            "V3_BLIND_SOURCE_PLAN_INPUT_INVALID")
    secret = private_seed or secrets.token_hex(24)
    tasks = []
    source_counts = []
    for session in queue.sessions:
        # Hold-out ONLY: do not claim new independent review is blind if the
        # model's provisional original analysis is already cached.
        unseen = [w for w in session.windows
                  if session._answer(w["window_id"]) is None]
        ranked = sorted(unseen,key=lambda w:sha256(
            (secret+"|"+session.digest+"|"+w["window_id"]).encode()))
        chosen = sorted(ranked[:sample_per_video],key=lambda w:w["window_id"])
        source_counts.append({"video_id":session.video_id,
                              "selected_unseen_windows":len(chosen),
                              "previously_analyzed_windows_excluded":
                                len(session.windows)-len(unseen)})
        for w in chosen:
            packet=session.packet(w["window_id"])
            cues = [{"cue_index":c["cue_index"],"start_ms":c["start_ms"],
                     "end_ms":c["end_ms"],"text":c["text"]}
                    for c in packet["primary_cues"]]
            context=[{"cue_index":c["cue_index"],"text":c["text"]}
                     for c in packet["left_context_cues"]+
                              packet["right_context_cues"]]
            core={"video_id":session.video_id,
                  "original_sha256":session.digest,
                  "window_id":w["window_id"],
                  "packet_sha256":packet["packet_sha256"],
                  "primary_cues":cues,
                  "neighbor_context_non_evidentiary":context}
            tasks.append({**core,"task_sha256":sha256(_serialize(core))})
    require(tasks, "V3_BLIND_NO_UNSEEN_SOURCE_WINDOWS")
    body={"schema":SCHEMA,
          "selection_pre_registered_before_independent_human_review":True,
          "model_answers_included":False,
          "prior_studies_or_relation_rankings_included":False,
          "source_only_sampling_seed_sha256":sha256(secret.encode()),
          "selected_source_count":len(source_counts),
          "task_count":len(tasks),
          "source_sampling":source_counts,
          "reviewer_task_slots":["REVIEWER_A","REVIEWER_B"],
          "adjudicator_not_assigned":True,
          "actual_human_gold_received":False,
          "reviewer_identity_verified":False,
          "financial_semantic_recall_certified":False,
          "instructions":(
            "Review primary cue text without model predictions. Distinguish "
            "source claim/no-claim/unresolved; list complete atomic claims, "
            "exact primary cue quote, finance product/action, numbers, units, "
            "conditions, negations, dates, exceptions. Reviewer A and B must "
            "work independently; third reviewer adjudicates disagreements. "
            "No result is certified until separate human records are supplied."),
          "tasks":tasks}
    return {**body,"plan_sha256":sha256(_serialize(body))}


def save_blind_review_plan(plan,directory):
    require(type(plan) is dict and plan.get("schema")==SCHEMA and
            sha256(_serialize({k:v for k,v in plan.items()
                               if k!="plan_sha256"}))==plan.get("plan_sha256")
            and plan["actual_human_gold_received"] is False and
            plan["financial_semantic_recall_certified"] is False,
            "V3_BLIND_PLAN_INTEGRITY_INVALID")
    root=safe_private_directory(directory)
    path=root/("ire_v3_source_only_blind_"+plan["plan_sha256"][:24]+".json")
    raw=_serialize(plan)
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        with os.fdopen(fd,"wb") as file:
            file.write(raw);file.flush();os.fsync(file.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return str(path)


def main():
    ap=argparse.ArgumentParser(description="Unseen original-source human-review packet generator")
    ap.add_argument("operation",choices=["prepare"])
    ap.add_argument("--private-manifest",required=True)
    ap.add_argument("--private-dir",required=True)
    ap.add_argument("--sample-per-video",type=int,default=3)
    args=ap.parse_args()
    try:
        manifest=json.loads(private_file(args.private_manifest).read_text(encoding="utf-8"))
        plan=plan_blind_review(ChatBatchQueue(manifest),args.sample_per_video)
        saved=save_blind_review_plan(plan,args.private_dir)
        print(json.dumps({"schema":SCHEMA,"plan_sha256":plan["plan_sha256"],
                          "tasks":plan["task_count"],
                          "source_count":plan["selected_source_count"],
                          "actual_human_gold_received":False,
                          "private_path":saved,"financial_facts_approved":0},sort_keys=True))
        return 0
    except (ValueError, KeyError, TypeError, OSError, UnicodeError):
        print(json.dumps({"schema":"IRE_V3_BLIND_SOURCE_ERROR","status":"FAILED_CLOSED"}))
        return 3


if __name__=="__main__":raise SystemExit(main())