"""IRE V3 P0-P2 research lifecycle gate: no silent promotion to advice.

At any point a ChatGPT conversation can ask for a deterministic snapshot of
what is structurally complete, what is empirically unverified and which next
operation is permitted. CI tests and self-attestations cannot unlock legal or
financial advice. The report contains counts/hashes only, not private quotes.
"""
from __future__ import annotations

import json
import os

from .v3_orchestrator import ChatBatchQueue
from .knowledge import validate_knowledge
from .v2_evidence import validate_evidence_ledger
from .v3_relation_review import validate_relation_reviews
from .checkpoint import safe_private_directory
from .cli import private_file
from .source import require,sha256


def completion_gate(queue,knowledge=None,evidence=None,relations=None,
                    relation_evaluation=None,advisory_dossier=None,
                    advisory_evaluation=None):
    require(type(queue).__name__=="ChatBatchQueue" and
            callable(getattr(queue,"status",None)) and
            callable(getattr(queue,"audit_semantic_coverage",None)) and
            type(getattr(queue,"sessions",None)) is list,
            "V3_COMPLETION_QUEUE_REQUIRED")
    status=queue.status()
    semantic=queue.audit_semantic_coverage()
    source_complete=status["remaining_windows"]==0 and status["full_semantic_analysis_submitted"]
    unresolved_cues=0
    for session in queue.sessions:
        for window in session.windows:
            answer=session._answer(window["window_id"])
            if answer is not None:
                unresolved_cues+=sum(r["status"]=="UNRESOLVED" for r in
                                     answer["cue_dispositions"])
    quality = semantic["cross_window_claim_quality"]
    source_gate=(source_complete and unresolved_cues==0 and
                 semantic["critical_count"]==0 and quality["risk_count"]==0)
    if knowledge is not None:
        validate_knowledge(knowledge)
    batch_registered=(knowledge is not None and all(
        any(row["video_id"]==src.video_id and
            row["source_sha256"]==src.digest and
            row["cues"]==len(src.cues)
            for row in knowledge["source_register"])
        for src in queue.sessions))
    if evidence is not None:
        require(knowledge is not None,"V3_COMPLETION_EVIDENCE_WITHOUT_KNOWLEDGE")
        validate_evidence_ledger(evidence,knowledge)
    if relations is not None:
        require(knowledge is not None,"V3_COMPLETION_RELATIONS_WITHOUT_KNOWLEDGE")
        relation_status=validate_relation_reviews(relations,knowledge)
    else:
        relation_status=None
    if relation_evaluation is not None:
        require(type(relation_evaluation) is dict and
                relation_evaluation.get("schema")==
                    "IRE_V3_RELATION_RETRIEVAL_EVALUATION_V1" and
                relation_evaluation.get("knowledge_snapshot_sha256")==
                    (knowledge or {}).get("snapshot_sha256") and
                relation_evaluation.get("certified_real_world_recall") is False,
                "V3_COMPLETION_RELATION_EVAL_INVALID")
    if advisory_dossier is not None:
        require(type(advisory_dossier) is dict and
                advisory_dossier.get("schema")==
                    "IRE_V3_ADVISORY_EVIDENCE_DOSSIER_V1" and
                advisory_dossier.get("knowledge_snapshot_sha256")==
                    (knowledge or {}).get("snapshot_sha256") and
                advisory_dossier.get("evidence_snapshot_sha256")==
                    (evidence or {}).get("snapshot_sha256") and
                advisory_dossier.get("individualized_advice_released") is False,
                "V3_COMPLETION_ADVISORY_DOSSIER_INVALID")
    if advisory_evaluation is not None:
        require(type(advisory_evaluation) is dict and
                advisory_evaluation.get("schema")==
                    "IRE_V3_ADVISORY_SAFETY_EVALUATION_V1" and
                advisory_evaluation.get("knowledge_snapshot_sha256")==
                    (knowledge or {}).get("snapshot_sha256") and
                advisory_evaluation.get("actual_investment_advice_quality_certified") is False and
                advisory_evaluation.get("release_approved") is False,
                "V3_COMPLETION_ADVISORY_EVALUATION_INVALID")
    live_evidence=sum(a["actual_network_fetch"] is True
                      for a in evidence["assessments"]) if evidence else 0
    unresolved=[]
    if not source_complete:
        unresolved.append("P0_ALL_ORIGINAL_SEMANTIC_WINDOWS_NOT_SUBMITTED")
    if semantic["critical_count"]:
        unresolved.append("P0_SEMANTIC_HIGH_SIGNAL_OMISSIONS")
    if unresolved_cues:
        unresolved.append("P0_UNRESOLVED_PRIMARY_SOURCE_CUES")
    if semantic["warning_count"]:
        unresolved.append("P0_SEMANTIC_BOUNDARY_OR_COMPOUND_REVIEW")
    if quality["material_unresolved_causal_count"]:
        unresolved.append("P0_UNSEPARATED_FINANCIAL_CAUSAL_BASIS")
    if quality["regulatory_missing_unit_count"]:
        unresolved.append("P0_REGULATORY_NUMERIC_UNIT_NOT_SOURCE_ESTABLISHED")
    if knowledge is None:
        unresolved.append("P1_NEW_IRE_CUMULATIVE_KNOWLEDGE_NOT_FINALIZED")
    elif not batch_registered:
        unresolved.append("P1_BATCH_ORIGINALS_NOT_IN_CUMULATIVE_KNOWLEDGE")
    if live_evidence==0:
        unresolved.append("P0C_NO_INDEPENDENTLY_FETCHED_OFFICIAL_DOCUMENT_EVENTS")
    if relation_status is None:
        unresolved.append("P1_RELATION_REVIEW_LEDGER_MISSING")
    elif relation_status["pending_count"]:
        unresolved.append("P1_CROSS_VIDEO_RELATIONS_PENDING_REVIEW")
    if relation_evaluation is None:
        unresolved.append("P0D_RELATION_BLIND_EVALUATION_MISSING")
    # A supplied synthetic or self-attested gold result is not external proof.
    unresolved.append("P0D_INDEPENDENT_REVIEWER_IDENTITIES_AND_GOLD_UNVERIFIED")
    if advisory_dossier is None:
        unresolved.append("P2_QUESTION_SPECIFIC_ADVISORY_DOSSIER_MISSING")
    else:
        unresolved.extend(advisory_dossier["unresolved_advisory_requirements"])
    if advisory_evaluation is None:
        unresolved.append("P2_BLIND_ADVISORY_SAFETY_SCENARIOS_MISSING")
    else:
        if (advisory_evaluation["unsafe_recommendation_releases"] or
            advisory_evaluation["required_blocker_misses"] or
            advisory_evaluation["false_verified_claim_assertions"] or
            advisory_evaluation["official_freshness_gate_errors"]):
            unresolved.append("P2_ADVISORY_BENCHMARK_SAFETY_VIOLATIONS")
    unresolved.append("P2_REAL_WORLD_FINANCIAL_AND_SUITABILITY_APPROVAL_ABSENT")
    next_action=("FINISH_SOURCE_WINDOWS" if not source_complete else
                 "RESOLVE_UNRESOLVED_SOURCE_CUES" if unresolved_cues else
                 "RESOLVE_SEMANTIC_QUALITY_WARNINGS" if
                    semantic["critical_count"] or semantic["warning_count"] or
                    quality["risk_count"] else
                 "INTEGRATE_NEW_IRE_KNOWLEDGE" if not batch_registered else
                 "FETCH_AND_SCOPE_CHECK_OFFICIAL_PRIMARY_SOURCES" if
                    live_evidence==0 else
                 "REVIEW_CROSS_VIDEO_RELATIONS" if
                    relation_status is None or relation_status["pending_count"] else
                 "OBTAIN_INDEPENDENT_BLIND_GOLD_AND_ADVISORY_EVALUATION")
    return {
        "schema":"IRE_V3_P0_P2_COMPLETION_GATE_V1",
        "source_manifest_sha256":status["batch_fingerprint"],
        "video_count":status["source_count"],
        "original_source_cue_count":status["total_cues"],
        "total_windows":status["total_windows"],
        "submitted_windows":status["accepted_windows"],
        "remaining_windows":status["remaining_windows"],
        "source_semantic_census_complete":source_gate,
        "unresolved_source_cues":unresolved_cues,
        "current_batch_in_cumulative_knowledge":batch_registered,
        "semantic_high_signal_omission_count":semantic["critical_count"],
        "semantic_boundary_or_compound_warning_count":semantic["warning_count"],
        "cross_window_financial_causal_review_count":quality["material_unresolved_causal_count"],
        "regulatory_unknown_numeric_unit_count":quality["regulatory_missing_unit_count"],
        "cross_window_claim_quality_report_sha256":quality["report_sha256"],
        "knowledge_snapshot_sha256":knowledge["snapshot_sha256"] if knowledge else None,
        "evidence_snapshot_sha256":evidence["snapshot_sha256"] if evidence else None,
        "live_official_document_assessments":live_evidence,
        "relation_review_snapshot_sha256":relations["snapshot_sha256"] if relations else None,
        "relation_review_pending":relation_status["pending_count"] if relation_status else None,
        "blind_eval_formal_result_available":relation_evaluation is not None,
        "advisory_safety_eval_formal_result_available":advisory_evaluation is not None,
        "real_independent_human_gold_certified":False,
        "real_advisory_suitability_approved":False,
        "next_operation":next_action,
        "blockers":sorted(set(unresolved)),
        "financial_facts_independently_approved":0,
        "financial_advice_released":False,
        "research_release_status":"BLOCKED_INCOMPLETE" if not source_gate else
                                  "STRUCTURAL_SOURCE_COMPLETE_EVIDENCE_PENDING",
        "investor_advisory_release_status":"BLOCKED_NO_INDEPENDENT_APPROVAL",
        "model_api_calls":0,
    }


def main():
    import argparse
    from .knowledge import read_private_snapshot
    parser=argparse.ArgumentParser(description="IRE V3 P0-P2 research completion gate")
    parser.add_argument("operation",choices=["audit"])
    parser.add_argument("--private-manifest",required=True)
    parser.add_argument("--private-knowledge-snapshot")
    parser.add_argument("--private-evidence-ledger")
    parser.add_argument("--private-relation-ledger")
    parser.add_argument("--private-relation-evaluation")
    parser.add_argument("--private-advisory-dossier")
    parser.add_argument("--private-advisory-evaluation")
    parser.add_argument("--private-report-dir",required=True)
    args=parser.parse_args()
    try:
        manifest=json.loads(private_file(args.private_manifest).read_text(encoding="utf-8"))
        queue=ChatBatchQueue(manifest)
        k=(read_private_snapshot(args.private_knowledge_snapshot)
           if args.private_knowledge_snapshot else None)
        def read(name):
            return json.loads(private_file(name).read_text(encoding="utf-8")) if name else None
        result=completion_gate(queue,k,read(args.private_evidence_ledger),
                               read(args.private_relation_ledger),
                               read(args.private_relation_evaluation),
                               read(args.private_advisory_dossier),
                               read(args.private_advisory_evaluation))
        encoded=json.dumps(result,ensure_ascii=False,sort_keys=True,
                           separators=(",",":"),allow_nan=False).encode("utf-8")
        digest=sha256(encoded)
        root=safe_private_directory(args.private_report_dir)
        file=root/("ire_v3_completion_"+digest[:24]+".json")
        fd=os.open(file,os.O_EXCL|os.O_CREAT|os.O_WRONLY,0o600)
        try:
            with os.fdopen(fd,"wb") as stream:
                stream.write(encoded);stream.flush();os.fsync(stream.fileno())
        except Exception:
            file.unlink(missing_ok=True)
            raise
        print(json.dumps({"schema":result["schema"],
                          "research_release_status":result["research_release_status"],
                          "next_operation":result["next_operation"],
                          "blockers":result["blockers"],
                          "submitted_windows":result["submitted_windows"],
                          "remaining_windows":result["remaining_windows"],
                          "report_sha256":digest,"private_report_path":str(file),
                          "financial_facts_independently_approved":0},sort_keys=True))
        return 2
    except (ValueError,KeyError,TypeError,UnicodeError,OSError):
        print(json.dumps({"schema":"IRE_V3_COMPLETION_ERROR","status":"FAILED_CLOSED"}))
        return 3


if __name__=="__main__":
    raise SystemExit(main())