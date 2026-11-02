"""IRE V2 ChatGPT-hosted batch study coordinator, NO model API.

Given 1..30 original SRTs and the chat's sealed per-cue answers, complete
all source checks and append one NEW-IRE cumulative knowledge snapshot.
It never calls the chat model. The ChatGPT host reads the plan/packets,
researches evidence and invokes the deterministic completion in the SAME
user request where tool time/context permits. Do not claim guaranteed
unlimited single-turn execution or financial fact certification.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path

from .source import require,source_record,parse_srt,sha256,VIDEO,DIGEST
from .cli import private_file
from .checkpoint import safe_private_directory
from .chat_bridge import ConversationResearchSession
from .semantics import assemble_window
from .claims import validate_annotations
from .knowledge import (
    empty_knowledge,ingest_new_video,validate_knowledge,
    save_private_snapshot,read_private_snapshot,provisional_concept_index,
    advisory_research_context)
from .v2_evidence import (
    empty_evidence_ledger,reconcile_ledger_with_updated_knowledge,
    validate_evidence_ledger,advisory_evidence_context)

VERSION="IRE_V2_BATCH_HOST_COORDINATOR"
MAX_SOURCE_BATCH=30
MAX_MANIFEST_SIZE=250_000


def _dump(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,
                      separators=(",",":"),allow_nan=False).encode("utf-8")


def _private_report(root:Path,name:str,data:dict) -> str:
    folder=safe_private_directory(str(root))
    raw=_dump(data)
    require(len(raw)<20_000_000,"V2_BATCH_REPORT_OVERSIZE")
    for counter in range(1,10000):
        path=folder/(name+"__"+str(counter).zfill(4)+".json")
        if not path.exists():
            fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            try:
                with os.fdopen(fd,"wb") as handle:
                    handle.write(raw);handle.flush();os.fsync(handle.fileno())
            except Exception:
                path.unlink(missing_ok=True)
                raise
            return str(path)
    raise ValueError("V2_BATCH_REPORT_VERSION_EXHAUSTED")


def inspect_manifest(manifest:dict) -> dict:
    require(type(manifest) is dict and set(manifest)=={
        "schema","videos","research_as_of"},
        "V2_BATCH_MANIFEST_SCHEMA_INVALID")
    require(manifest["schema"]=="IRE_V2_CHAT_BATCH_V1"
            and type(manifest["videos"]) is list
            and 1<=len(manifest["videos"])<=MAX_SOURCE_BATCH,
            "V2_BATCH_SOURCE_COUNT_INVALID")
    require(type(manifest["research_as_of"]) is str and
            date.fromisoformat(manifest["research_as_of"]).isoformat()
            ==manifest["research_as_of"],"V2_BATCH_ASOF_DATE_INVALID")
    ids=set();shas=set();text_hashes=set();items=[]
    for index,item in enumerate(manifest["videos"],1):
        required={"video_id","original_srt_path","source_sha256",
                  "private_chat_sessions_path"}
        require(type(item) is dict and
                required <= set(item) <= required | {"window_strategy"} and
                item.get("window_strategy","V2_COMPAT") in (
                    "V2_COMPAT","V3_ADAPTIVE"),
                "V2_BATCH_ITEM_SCHEMA_INVALID")
        vid=item["video_id"];digest=item["source_sha256"]
        require(type(vid) is str and VIDEO.fullmatch(vid) and
                type(digest) is str and DIGEST.fullmatch(digest),
                "V2_VIDEO_OR_SHA_INVALID")
        require(vid not in ids and digest not in shas,
                "V2_BATCH_DUPLICATE_SOURCE_OR_ID")
        ids.add(vid);shas.add(digest)
        raw=private_file(item["original_srt_path"]).read_bytes()
        require(sha256(raw)==digest,"V2_BATCH_ORIGINAL_SHA_MISMATCH")
        cues=parse_srt(raw,digest)
        text_sha=sha256(" ".join(c.text for c in cues).encode("utf-8"))
        require(text_sha not in text_hashes,
                "V2_BATCH_DUPLICATE_ORIGINAL_TEXT")
        text_hashes.add(text_sha)
        session=ConversationResearchSession(
            raw,vid,digest,item["private_chat_sessions_path"],
            window_strategy=item.get("window_strategy","V2_COMPAT"))
        state=session.status()
        items.append({
            "ordinal":index,
            "video_id":vid,
            "source_sha256":digest,
            "text_sha256":text_sha,
            "cues":state["original_cues"],
            "windows":state["total_windows"],
            "accepted_windows":state["accepted_windows"],
            "remaining_windows":state["remaining_windows"],
            "next_window_id":state["next_window_id"],
            "all_chat_windows_submitted":state["all_windows_accounted_for"],
            "session_id":state["session_id"],
            "window_strategy":item.get("window_strategy","V2_COMPAT"),
            "external_model_api_calls":0,
        })
    return {
        "schema":"IRE_V2_BATCH_READINESS_V1",
        "policy":VERSION,
        "research_as_of":manifest["research_as_of"],
        "batch_fingerprint":sha256(_dump({
            "schema":VERSION,
            "asof":manifest["research_as_of"],
            "sources":[[x["video_id"],x["source_sha256"],
                        x["session_id"]] for x in items]})),
        "requested_video_count":len(items),
        "total_cues":sum(x["cues"] for x in items),
        "total_windows":sum(x["windows"] for x in items),
        "accepted_windows":sum(x["accepted_windows"] for x in items),
        "remaining_windows":sum(x["remaining_windows"] for x in items),
        "all_source_windows_completed":all(
            x["all_chat_windows_submitted"] for x in items),
        "videos":items,
        "analysis_operator":"CURRENT_CHATGPT_CONVERSATION",
        "model_api_calls":0,
        "unattended_chat_model_invocation_available":False,
        "research_accuracy_certified":False,
    }


def finalize_batch(manifest:dict,
                   prior_knowledge:dict|None,
                   private_knowledge_dir:str,
                   private_audit_dir:str,
                   prior_evidence:dict|None=None,
                   private_evidence_dir:str|None=None) -> dict:
    """All-or-nothing 1..30 video knowledge update after sealed chat inputs.

    No knowledge commit occurs when even one source is not fully assessed,
    its final source ledger is corrupt, or it contains unresolved source cues.
    A durable, explicit blocked audit is created instead.
    """
    plan=inspect_manifest(manifest)
    current=prior_knowledge if prior_knowledge is not None else empty_knowledge()
    validate_knowledge(current)
    # Reject stale/forked caller state when a newer immutable snapshot exists.
    knowledge_root=safe_private_directory(private_knowledge_dir)
    existing=list(knowledge_root.glob("ire_knowledge_v*.json"))
    if existing:
        expected_name=("ire_knowledge_v"+str(current["version"]).zfill(6)+
                       "_"+current["snapshot_sha256"][:16]+".json")
        require(prior_knowledge is not None and any(
            p.name==expected_name for p in existing),
            "V2_BATCH_PRIOR_KNOWLEDGE_VERSION_NOT_CURRENT")
        require(not any(
            p.name.startswith("ire_knowledge_v") and
            p.name[15:21].isdigit() and
            int(p.name[15:21])>current["version"]
            for p in existing),
            "V2_BATCH_STALE_PRIOR_KNOWLEDGE_SNAPSHOT")
    if private_evidence_dir is not None:
        ev_root=safe_private_directory(private_evidence_dir)
        require(prior_evidence is not None or
                not list(ev_root.glob("ire_evidence_v*.json")),
                "V2_BATCH_PRIOR_EVIDENCE_SNAPSHOT_REQUIRED")
    base_current=current
    audit={
        "schema":"IRE_V2_STUDY_BATCH_AUDIT",
        "batch_fingerprint":plan["batch_fingerprint"],
        "research_as_of":manifest["research_as_of"],
        "requested_sources":plan["requested_video_count"],
        "cues_total":plan["total_cues"],
        "windows_total":plan["total_windows"],
        "windows_accounted_for":plan["accepted_windows"],
        "model_api_calls":0,
        "one_user_request_workflow_target":True,
        "guaranteed_unlimited_single_turn_execution":False,
        "legacy_study_claims_imported":False,
        "source_details":[],
        "unresolved_cues_total":0,
        "new_atomic_claims":0,
        "relation_candidates_added":0,
        "knowledge_previous_snapshot_sha256":current["snapshot_sha256"],
        "knowledge_next_snapshot_sha256":None,
        "private_knowledge_snapshot_path":None,
        "final_research_status":"INCOMPLETE_REQUIRES_RESUME",
        "scope_and_official_fact_accuracy_certified":False,
        "independent_human_blind_recall_measured":False,
        "financial_facts_automatically_approved":0,
        "financial_advice_released":False
    }
    if not plan["all_source_windows_completed"]:
        audit["source_details"]=[
            {"video_id":x["video_id"],
             "analysis_complete":x["all_chat_windows_submitted"],
             "pending_windows":x["remaining_windows"],
             "first_pending_window":x["next_window_id"]}
            for x in plan["videos"]]
        audit["blockers"]=["SOURCE_WINDOWS_NOT_ALL_ASSESSED"]
        audit["audit_path"]=_private_report(
            Path(private_audit_dir),"ire_v2_incomplete_batch",audit)
        return audit

    # V3_ADAPTIVE sources must never bypass the stricter V3 cross-window
    # quality gate by invoking the legacy V2 integration entrypoint directly.
    # Preserve V2_COMPAT historical behavior and existing sealed records.
    if any(x.get("window_strategy") == "V3_ADAPTIVE" for x in manifest["videos"]):
        from .v3_claim_quality import audit_claim_quality
        from .v3_orchestrator import ChatBatchQueue
        quality = audit_claim_quality(ChatBatchQueue(manifest))
        if quality["risk_count"]:
            audit["blockers"] = ["V3_ADAPTIVE_CROSS_WINDOW_CLAIM_QUALITY_PENDING"]
            audit["cross_window_quality_risk_count"] = quality["risk_count"]
            audit["cross_window_quality_report_sha256"] = quality["report_sha256"]
            audit["audit_path"] = _private_report(
                Path(private_audit_dir), "ire_v2_v3_quality_blocked", audit)
            return audit

    blockers=[]
    work=[]
    # Validate EVERY answer, report and original BEFORE any knowledge is written.
    for item in manifest["videos"]:
        raw=private_file(item["original_srt_path"]).read_bytes()
        session=ConversationResearchSession(
            raw,item["video_id"],item["source_sha256"],
            item["private_chat_sessions_path"],
            window_strategy=item.get("window_strategy","V2_COMPAT"))
        expected=assemble_window(
            raw,item["video_id"],item["source_sha256"],session.windows,
            [session._answer(w["window_id"]) for w in session.windows],
            "chatgpt-conversation-no-api")
        final_path=session.folder/"final_report.json"
        if final_path.exists():
            completed=json.loads(final_path.read_text(encoding="utf-8"))
            require(completed.get("schema")=="IRE_CHAT_RESEARCH_PACKAGE_V1"
                    and completed.get("source_sha256")==item["source_sha256"]
                    and completed.get("video_id")==item["video_id"]
                    and completed.get("annotations")==expected
                    and completed.get("all_primary_windows_submitted") is True
                    and completed.get("actual_model_api_calls")==0,
                    "V2_SEALED_CHAT_REPORT_CHANGED")
        else:
            # Session's only authorized finalization path performs the
            # same original-cue validation and writes immutable 0600 output.
            session.finalize()
            completed=json.loads(final_path.read_text(encoding="utf-8"))
        checked=validate_annotations(
            raw,item["source_sha256"],item["video_id"],expected)
        unresolved=checked["unresolved_cues"]
        audit["source_details"].append({
            "video_id":item["video_id"],
            "source_sha256":item["source_sha256"],
            "source_cues":checked["source_cues"],
            "provisional_claims":checked["proposed_atomic_claims"],
            "unresolved_cues":unresolved,
            "quote_trace_passed":True,
            "official_financial_facts_certified":0
        })
        audit["unresolved_cues_total"]+=unresolved
        audit["new_atomic_claims"]+=checked["proposed_atomic_claims"]
        if unresolved:
            blockers.append("SOURCE_MEANING_CUES_UNRESOLVED")
        work.append((raw,completed))
    if blockers:
        audit["blockers"]=sorted(set(blockers))
        audit["final_research_status"]="INCOMPLETE_REQUIRES_RESUME"
        audit["audit_path"]=_private_report(
            Path(private_audit_dir),"ire_v2_unresolved_batch",audit)
        return audit

    try:
        for raw,report in work:
            current=ingest_new_video(current,raw,report)
        # All v1 history and source citations remain append-only.
        topics=provisional_concept_index(current)
        audit["relation_candidates_added"]=(
            len(current["relation_candidates"])-
            len(base_current["relation_candidates"]))
        audit["knowledge_next_snapshot_sha256"]=current["snapshot_sha256"]
        audit["knowledge_source_count"]=len(current["source_register"])
        audit["cumulative_unverified_claims"]=len(current["claims"])
        audit["provisional_topic_clusters"]=len(topics)
        if prior_evidence is not None:
            validate_evidence_ledger(prior_evidence,base_current)
            rebased=reconcile_ledger_with_updated_knowledge(
                prior_evidence,base_current,current)
        else:
            rebased=empty_evidence_ledger(current)
        audit["evidence_snapshot_sha256"]=rebased["snapshot_sha256"]
        audit["evidence_assessment_count"]=len(rebased["assessments"])
        audit["current_chat_is_independent_human_reviewer"]=False
        audit["blockers"]=[
            "OFFICIAL_FACT_AND_TIME_SCOPE_VALIDATION_NOT_COMPLETE",
            "CROSS_VIDEO_CANDIDATES_REQUIRE_ADJUDICATION",
            "ADVISORY_FITNESS_REQUIRES_CURRENT_RESEARCH"
        ]
        audit["final_research_status"]="SOURCE_ANALYSIS_COMPLETE_EVIDENCE_PENDING"
        # Write the new snapshot only after all statements validated.
        target=save_private_snapshot(current,private_knowledge_dir)
        audit["private_knowledge_snapshot_path"]=target
        if private_evidence_dir is not None:
            from .v2_evidence import save_private_evidence
            audit["private_evidence_snapshot_path"]=save_private_evidence(
                rebased,current,private_evidence_dir)
        audit["audit_path"]=_private_report(
            Path(private_audit_dir),"ire_v2_integrated_batch",audit)
        return audit
    except (ValueError,TypeError,KeyError):
        # No lie about completion when integration/privilege checks fail.
        raise


def main() -> int:
    parser=argparse.ArgumentParser(
        description="ChatGPT-hosted multi-video research readiness and cumulative integration, no LLM API")
    parser.add_argument("operation",choices=["plan","finalize"])
    parser.add_argument("--private-manifest",required=True)
    parser.add_argument("--prior-knowledge-snapshot")
    parser.add_argument("--private-knowledge-dir")
    parser.add_argument("--private-audit-dir")
    parser.add_argument("--prior-evidence-snapshot")
    parser.add_argument("--private-evidence-dir")
    args=parser.parse_args()
    try:
        path=private_file(args.private_manifest)
        require(path.stat().st_size<=MAX_MANIFEST_SIZE,
                "V2_BATCH_MANIFEST_TOO_LARGE")
        manifest=json.loads(path.read_text(encoding="utf-8"))
        if args.operation=="plan":
            result=inspect_manifest(manifest)
            exit_code=0
        else:
            require(bool(args.private_knowledge_dir and args.private_audit_dir),
                    "V2_BATCH_PRIVATE_OUTPUT_DIRS_REQUIRED")
            knowledge_dir=safe_private_directory(args.private_knowledge_dir)
            previous=(read_private_snapshot(args.prior_knowledge_snapshot)
                      if args.prior_knowledge_snapshot else None)
            if previous is None:
                require(not list(knowledge_dir.glob("ire_knowledge_v*.json")),
                        "V2_BATCH_REFUSE_TO_RESET_EXISTING_KNOWLEDGE")
            if args.prior_evidence_snapshot:
                from .v2_evidence import validate_evidence_ledger
                prev_evid=json.loads(
                    private_file(args.prior_evidence_snapshot).read_text())
                validate_evidence_ledger(prev_evid,previous)
            else:
                prev_evid=None
            result=finalize_batch(
                manifest,previous,args.private_knowledge_dir,
                args.private_audit_dir,prev_evid,args.private_evidence_dir)
            exit_code=2
        # Private paths, source text and raw claims never enter stdout.
        public={k:v for k,v in result.items()
                if k not in {"source_details","videos",
                             "private_knowledge_snapshot_path",
                             "private_evidence_snapshot_path","audit_path"}}
        print(json.dumps(public,ensure_ascii=False,sort_keys=True))
        return exit_code
    except (ValueError,TypeError,KeyError,OSError,UnicodeError):
        print(json.dumps({"schema":"IRE_V2_BATCH_ERROR",
                          "status":"FAILED_CLOSED",
                          "error_code":"V2_BATCH_PRIVATE_INPUT_OR_AUDIT_INVALID"}))
        return 3


if __name__=="__main__":
    raise SystemExit(main())