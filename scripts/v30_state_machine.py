#!/usr/bin/env python3
"""Append-only V3.0 research state journal. No out-of-order completeness.

This keeps execution diagnostic progress distinct from permission to proceed.
A report can say an arithmetic calculation ran, yet its research workflow
cannot advance past a blocked source/official fact stage.
"""
from dataclasses import dataclass
from v30_verified_core import sha256,canonical,guard

WORKFLOW_STAGES=(
 "SOURCE_PROVENANCE","ATOMIC_COVERAGE","CLAIM_FRAME_AND_OBLIGATIONS",
 "PRIMARY_EVIDENCE","QUANT_AND_EMPIRICAL","RELATION_CANDIDATES",
 "INDEPENDENT_REVIEW","COMPLETION_AND_APPEND_ONLY_INTEGRATION"
)
PROOF_DOMAINS={
 "SOURCE_PROVENANCE":"ORIGINAL_SOURCE_HASH_AND_REVIEW_ATTESTATION",
 "ATOMIC_COVERAGE":"FULL_CUE_ATOMIC_LEDGER_AND_REVIEW",
 "CLAIM_FRAME_AND_OBLIGATIONS":"MULTILABEL_FINANCIAL_FRAME_OR_BLOCKER",
 "PRIMARY_EVIDENCE":"INDEPENDENT_OFFICIAL_PRIMARY_CLAIM_PROOFS",
 "QUANT_AND_EMPIRICAL":"INDEPENDENT_MODEL_OR_JUSTIFIED_AUDITED_WAIVER",
 "RELATION_CANDIDATES":"TYPED_REVIEW_QUEUE_AND_NONCANDIDATE_AUDIT",
 "INDEPENDENT_REVIEW":"DISTINCT_HUMAN_OR_DELEGATED_REVIEWER_CREDENTIAL",
 "COMPLETION_AND_APPEND_ONLY_INTEGRATION":"ACTUAL_APPROVED_V5_COMPLETION_CERTIFICATE",
}

@dataclass(frozen=True)
class StageEvent:
    sequence:int
    stage:str
    status:str
    proof_ids:tuple
    reason:str
    previous_digest:str
    digest:str

class ResearchState:
    def __init__(self,video_id,source_sha):
        guard(type(video_id) is str and type(source_sha) is str
              and len(source_sha)==64,
              "CANONICAL_VIDEO_AND_SOURCE_IDENTITY_REQUIRED")
        self.video_id=video_id
        self.source_sha=source_sha
        self.events=[]
    def _last_digest(self):
        return self.events[-1].digest if self.events else "GENESIS"
    def append(self,stage,status,proof_ids=(),reason="",v5_approved=False):
        guard(stage in WORKFLOW_STAGES and status in ("PASSED","BLOCKED")
              and isinstance(proof_ids,(list,tuple))
              and len(set(proof_ids))==len(proof_ids)
              and isinstance(reason,str),"UNSAFE_RESEARCH_STAGE_EVENT")
        required_index=len(self.events)
        guard(required_index<len(WORKFLOW_STAGES)
              and stage==WORKFLOW_STAGES[required_index],
              "RESEARCH_STAGE_OUT_OF_ORDER_OR_DUPLICATE")
        if self.events:
            guard(self.events[-1].status=="PASSED",
                  "PREVIOUS_RESEARCH_STAGE_BLOCKED")
        if status=="PASSED":
            guard(bool(proof_ids)
                  and all(isinstance(p,str) and len(p)>=10 for p in proof_ids),
                  "STAGE_PASSED_WITHOUT_AUTHENTICATED_EVIDENCE_REFERENCES")
            if stage=="COMPLETION_AND_APPEND_ONLY_INTEGRATION":
                guard(v5_approved is True,
                      "V5_COMPLETION_AND_REVIEW_CANNOT_BE_SELF_CERTIFIED")
        else:
            guard(reason and len(reason)>=10,
                  "BLOCKED_STAGE_MUST_NAME_CONCRETE_EVIDENCE_DEFECT")
        payload={
           "video_id":self.video_id,"source_sha":self.source_sha,
           "sequence":required_index+1,
           "stage":stage,"status":status,"proof_ids":list(proof_ids),
           "reason":reason,"previous_digest":self._last_digest(),
        }
        event=StageEvent(
            sequence=payload["sequence"],stage=stage,status=status,
            proof_ids=tuple(proof_ids),reason=reason,
            previous_digest=payload["previous_digest"],
            digest=sha256(canonical(payload)),
        )
        self.events.append(event)
        return event
    def preview(self):
        # No stages are automatically completed by missing evidence.
        status=("RESEARCH_BLOCKED" if self.events and
                self.events[-1].status=="BLOCKED" else
                "RESEARCH_COMPLETE" if len(self.events)==len(WORKFLOW_STAGES)
                and all(e.status=="PASSED" for e in self.events)
                else "RESEARCH_PENDING")
        return {
          "schema":"V30_APPEND_ONLY_EXECUTION_JOURNAL_V1",
          "video_id":self.video_id,"source_sha256":self.source_sha,
          "status":status,
          "completed_stages":sum(e.status=="PASSED" for e in self.events),
          "last_digest":self._last_digest(),
          "events":[{key:getattr(e,key) for key in
                     ("sequence","stage","status","proof_ids",
                      "reason","previous_digest","digest")}
                    for e in self.events],
          "certificate_generated_by_state_machine":False,
          "historical_claims_overwritten":0,
        }

def journal_from_report(report,root):
    """Monotone gate; independently recheck actual V5 certificate if provided."""
    guard(report.get("schema")=="V30_END_TO_END_RESEARCH_WORK_PRODUCT_V1",
          "ONLY_VERIFIED_RESEARCH_REPORTS_CAN_CREATE_GATES")
    state=ResearchState(report["video_id"],report["input_srt_sha256"])
    evidences={
        "SOURCE_PROVENANCE":["original_srt_sha256:"+report["input_srt_sha256"],
                              "source_reviewer_attestation_checked"],
        "ATOMIC_COVERAGE":["source_atomic_ledger_sha256:"+report["input_ledger_sha256"],
                           "all_source_cue_ranges_accounted_for"],
        "CLAIM_FRAME_AND_OBLIGATIONS":["multi_type_financial_frames_validated"],
        "PRIMARY_EVIDENCE":["contextual_official_source_evidence_reviewed"],
        "QUANT_AND_EMPIRICAL":["required_quant_and_empirical_results_reviewed"],
        "RELATION_CANDIDATES":["signed_claim_relation_queue_and_negative_audit"],
        "INDEPENDENT_REVIEW":["distinct_external_reviewer_signed_result"],
        "COMPLETION_AND_APPEND_ONLY_INTEGRATION":[],
    }
    for stage in WORKFLOW_STAGES:
        assessment=report["stages"].get(stage,"BLOCKED")
        if stage=="COMPLETION_AND_APPEND_ONLY_INTEGRATION":
            if (assessment=="PASSED_EXISTING_V5_CERTIFICATE" and
                report.get("v5_certificate_status")==
                  "V5_RESEARCH_COMPLETE_EXTERNALLY_VALIDATED" and
                report.get("v5_existing_certificate_paths")):
                from v30_research_pipeline import (
                    complete_with_preexisting_v5_certificate,)
                from v30_verified_core import sha256
                from pathlib import Path
                p=report["v5_existing_certificate_paths"]
                evidence=complete_with_preexisting_v5_certificate(
                    root,p["certificate_path"],p["review_path"])
                path=Path(root)/p["certificate_path"]
                digest=sha256(path.read_bytes())
                guard(evidence["existing_v5_certificate_verdict"]==
                      "RESEARCH_COMPLETE" and
                      digest==report["v5_external_certificate_sha256"],
                      "EXTERNAL_V5_CERTIFICATE_DIGEST_DRIFT")
                state.append(stage,"PASSED",
                             proof_ids=("actual_v5_cert_sha256:"+digest,),
                             v5_approved=True)
            else:
                state.append(stage,"BLOCKED",
                             reason="Actual V5 independently approved certificate is absent")
            break
        if assessment not in ("PASSED","REVIEW_ONLY"):
            state.append(stage,"BLOCKED",reason=(
                "Evidence or independent attestation absent for "+stage))
            break
        if stage=="RELATION_CANDIDATES" and assessment=="REVIEW_ONLY":
            state.append(stage,"BLOCKED",
                         reason="Candidate matches are not independently reviewed")
            break
        state.append(stage,"PASSED",proof_ids=evidences[stage])
    result=state.preview()
    if result["status"]=="RESEARCH_COMPLETE":
        guard(report.get("v5_certificate_status")==
              "V5_RESEARCH_COMPLETE_EXTERNALLY_VALIDATED" and
              report.get("automatic_research_completion_certificates")==0 and
              report.get("automatic_knowledge_approvals")==0,
              "V3_PIPELINE_CANNOT_SELF_ISSUE_RESEARCH_COMPLETE")
    return result
