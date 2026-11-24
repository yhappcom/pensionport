"""Separate graded engine assessment from per-video research authority.

L3 is recorded manual source-only cross-review, NOT authenticated isolation.
No grade publishes knowledge or alters the sequential checklist.
"""
from __future__ import annotations
from .assessment_plan import validate_campaign, timestamp, THRESHOLDS
from .codec import json_digest, sha256
from .errors import InvalidInput
from .gold_eval import evaluate_atomic_gold, _original_quote_valid
from .gold_release import evaluate_production_gold
from .gold_traceability import verify_gold_cue_trace
from .review_consensus import verify_two_review_consensus_lineage
from .source import parse_srt


def _manual_cross_review(plan, original, gold, alignment, evidence, transcripts):
    if (type(evidence) is not dict or set(evidence)!={"submissions","consensus","alignment_lock"}
        or type(transcripts) is not list or len(transcripts)!=2
        or any(type(x) is not bytes or not x for x in transcripts)
        or transcripts[0]==transcripts[1]):
        raise InvalidInput("ASSESSMENT_MANUAL_REVIEW_EVIDENCE_INVALID")
    rows=evidence["submissions"]
    if type(rows) is not list or len(rows)!=2:
        raise InvalidInput("ASSESSMENT_TWO_REVIEW_EXPORTS_REQUIRED")
    cues=parse_srt(original)
    roles={};sessions=set();ends=[];digests={}
    for row,transcript in zip(rows,transcripts):
        if type(row) is not dict or set(row)!={"role","session_id","packet_sha256",
                "transcript_sha256","predictions_reported_exposed","began_at",
                "submitted_at","draft_gold"}:
            raise InvalidInput("ASSESSMENT_MANUAL_SUBMISSION_SCHEMA")
        role=row["role"]; session=row["session_id"]
        if (role not in ("reviewer_one","reviewer_two") or role in roles or
            type(session) is not str or len(session)<12 or session in sessions or
            row["packet_sha256"]!=plan["source_only_packet_sha256"] or
            row["transcript_sha256"]!=sha256(transcript) or
            row["predictions_reported_exposed"] is not False):
            raise InvalidInput("ASSESSMENT_MANUAL_SESSION_OR_PACKET_DRIFT")
        start,end=timestamp(row["began_at"]),timestamp(row["submitted_at"])
        if not timestamp(plan["registered_at"])<=start<end:
            raise InvalidInput("ASSESSMENT_MANUAL_REVIEW_ORDER")
        draft=row["draft_gold"]
        if (type(draft) is not dict or set(draft)!={"schema","source_srt_sha256",
                "reviewed_cues","atomic_gold_claims"} or
            draft["schema"]!="IRE_P205_PRIVATE_GOLD_ATOMIC_REVIEW_V1" or
            draft["source_srt_sha256"]!=sha256(original)):
            raise InvalidInput("ASSESSMENT_MANUAL_DRAFT_SCHEMA")
        trace=verify_gold_cue_trace(cues,draft)
        if trace["cue_open_uncertain"] or not trace["gold_atom_count"] or any(
            not _original_quote_valid(cues,ref)
            for atom in draft["atomic_gold_claims"] for ref in atom["source_refs"]):
            raise InvalidInput("ASSESSMENT_MANUAL_DRAFT_INCOMPLETE")
        roles[role]=draft; sessions.add(session); ends.append(end)
        digests[role]=json_digest(row)
    consensus=evidence["consensus"]; lock=evidence["alignment_lock"]
    if (type(consensus) is not dict or consensus.get("reviewer_submission_sha256")!=digests
        or consensus.get("gold_sha256")!=json_digest(gold)):
        raise InvalidInput("ASSESSMENT_MANUAL_CONSENSUS_DRIFT")
    freeze=timestamp(consensus.get("gold_frozen_at"))
    if (type(lock) is not dict or set(lock)!={"gold_sha256","alignment_sha256","aligned_at"}
        or lock["gold_sha256"]!=json_digest(gold)
        or lock["alignment_sha256"]!=json_digest(alignment)
        or not max(ends)<freeze<timestamp(lock["aligned_at"])):
        raise InvalidInput("ASSESSMENT_MANUAL_FREEZE_ORDER")
    verify_two_review_consensus_lineage(roles,gold,consensus)


def assess_campaign(plan, original, prediction, *, gold=None, alignment=None,
                    manual_evidence=None, transcripts=None, production_evidence=None):
    """Calculate evidence level, never accept caller-provided scores or grades."""
    validate_campaign(plan)
    diagnostic=evaluate_atomic_gold(plan,original,prediction,gold=gold,alignment=alignment)
    level="L1"
    tp,fp,fn=(diagnostic[k] for k in ("tp","fp","fn"))
    complete=all(type(v) is int for v in (tp,fp,fn))
    high=diagnostic["diagnostic_high_risk_fn"]
    meets=False
    if complete:
        level="L2"
        meets=bool(tp+fp and tp+fn and tp*10000>=9500*(tp+fp)
                   and tp*10000>=9800*(tp+fn) and high==0
                   and diagnostic["prediction_numeric_source_provenance_complete"])
    if manual_evidence is not None or transcripts is not None:
        if not complete:
            raise InvalidInput("ASSESSMENT_MANUAL_REVIEW_REQUIRES_COMPLETE_ALIGNMENT")
        _manual_cross_review(plan,original,gold,alignment,manual_evidence,transcripts)
        level="L3"
    production=None
    if production_evidence is not None:
        if (type(production_evidence) is not dict or set(production_evidence)!={
                "registry","reviewer_submissions","consensus","alignment_receipt"}):
            raise InvalidInput("ASSESSMENT_PRODUCTION_INPUT_SCHEMA")
        production=evaluate_production_gold(plan,original,prediction,gold=gold,
                          alignment=alignment,**production_evidence)
        if production["independent_gold_verified"]:
            level="L4"
    eligible=bool(level=="L4" and plan["purpose"]=="HOLDOUT"
                  and production["ready_for_p0_2_06"] and meets)
    return {"schema":"IRE_V6_GRADED_ATOMIC_ASSESSMENT_V1",
            "campaign_id":plan["campaign_id"],"plan_sha256":json_digest(plan),
            "engine_commit_sha":plan["engine_commit_sha"],"purpose":plan["purpose"],
            "evidence_level":level,"tp":tp,"fp":fp,"fn":fn,
            "diagnostic_high_risk_fn":high,"diagnostic_thresholds_met":meets,
            "independent_gold_verified":level=="L4",
            "independent_metrics_available":level=="L4",
            "manual_isolation_authenticated":False,
            "ready_for_p0_2_06":eligible,
            "research_publication_authorized":False,
            "personalized_advice_authorized":False,
            "status":"ASSESSMENT_THRESHOLDS_PASS_REVIEW_REQUIRED" if eligible else "HOLD"}
