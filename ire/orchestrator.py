"""Single-invocation, fail-closed independent research orchestration.

The controller runs source -> semantics -> traceability -> primary discovery ->
quantitative obligations -> relation candidates -> review gate -> private report.
A completed *execution* can have BLOCKED research. No approval, knowledge merge,
financial factual claim, or historical research citation can be emitted here.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
import time
from typing import Callable

from .source import require,sha256,source_record
from .semantics import InferenceConfig,interpret_original,semantic_contract_sha256
from .claims import validate_annotations
from .research import pending_research
from .retrieval import related_proposals
from .primary import discover_official_candidates,screen_discovery_response
from .evidence import independently_fetch_candidate
from .evidence_audit import compare_to_fetched_evidence


STAGE_ORDER=(
    "SOURCE_INTEGRITY",
    "FINANCIAL_SEMANTICS",
    "ATOMIC_TRACEABILITY",
    "INDEPENDENT_PRIMARY_DISCOVERY",
    "PRIMARY_DOCUMENT_VERIFICATION",
    "QUANTITATIVE_OBLIGATIONS",
    "WITHIN_SOURCE_RELATIONS",
    "INDEPENDENT_REVIEW_GATE",
    "FINAL_PRIVATE_REPORT",
)
RETRYABLE_MODEL_ERRORS=(
    "SEMANTIC_API_HTTP_ERROR_429",
    "SEMANTIC_API_HTTP_ERROR_500",
    "SEMANTIC_API_HTTP_ERROR_502",
    "SEMANTIC_API_HTTP_ERROR_503",
    "SEMANTIC_API_HTTP_ERROR_504",
    "SEMANTIC_API_UNAVAILABLE",
)


@dataclass(frozen=True)
class OrchestrationPolicy:
    model: str | None = None
    private_checkpoint_directory: str | None = None
    max_model_attempts: int = 3
    max_discovery_claims: int = 30
    max_retrieval_claims: int = 4000
    max_evidence_documents: int = 8
    private_evidence_dir: str | None = None
    research_model: str | None = None
    # Real primary discovery requires OPENAI_API_KEY and may incur tool costs.
    enable_primary_discovery: bool = True

    def validate(self):
        require(type(self.max_model_attempts) is int and
                1<=self.max_model_attempts<=5,"INVALID_ORCHESTRATOR_RETRIES")
        require(type(self.max_discovery_claims) is int and
                0<=self.max_discovery_claims<=500,
                "INVALID_ORCHESTRATOR_DISCOVERY_LIMIT")
        require(type(self.max_retrieval_claims) is int and
                1<=self.max_retrieval_claims<=20000,
                "INVALID_ORCHESTRATOR_RETRIEVAL_LIMIT")
        require(type(self.max_evidence_documents) is int and
                0<=self.max_evidence_documents<=80,
                "INVALID_ORCHESTRATOR_EVIDENCE_BUDGET")
        require(type(self.enable_primary_discovery) is bool,
                "INVALID_OFFICIAL_DISCOVERY_SWITCH")
        if self.model is not None:
            InferenceConfig(model=self.model).validate()
        if self.research_model is not None:
            InferenceConfig(model=self.research_model).validate()


def _stage(name: str, status: str, **metadata) -> dict:
    require(name in STAGE_ORDER,"INVALID_STAGE")
    return {"stage":name,"status":status,**metadata}


def _safe_error(exc: Exception) -> str:
    reason=str(exc)
    # Never put transcript, upstream HTTP bodies, or model output into logs.
    if re.fullmatch(r"[A-Z][A-Z0-9_]{3,90}",reason):
        return reason
    return "UNEXPECTED_STAGE_FAILURE"


def _fingerprint(video_id: str, digest: str, policy: OrchestrationPolicy) -> str:
    raw={
        "schema":"IRE_ONESHOT_FINGERPRINT_V1",
        "video_id":video_id,"source_sha256":digest,
        "model":policy.model,
        "semantic_contract_sha256":semantic_contract_sha256(),
        "research_model":policy.research_model,
        "max_discovery_claims":policy.max_discovery_claims,
        "max_retrieval_claims":policy.max_retrieval_claims,
        "max_evidence_documents":policy.max_evidence_documents,
        "evidence_snapshot_enabled":policy.private_evidence_dir is not None,
        "enable_primary_discovery":policy.enable_primary_discovery,
        "engine":"IRE_ONE_SHOT_20261101_V1",
    }
    return sha256(json.dumps(raw,sort_keys=True).encode("utf-8"))


def _finalize(video_id: str, digest: str, policy: OrchestrationPolicy,
              stages: list[dict], blockers: list[str], details: dict) -> dict:
    occurred={x["stage"] for x in stages}
    # Every possible stage gets a final record, even if prerequisites blocked.
    for stage in STAGE_ORDER:
        if stage not in occurred:
            stages.append(_stage(stage,"SKIPPED_UPSTREAM_BLOCKED"))
    stages.sort(key=lambda x:STAGE_ORDER.index(x["stage"]))
    blockers=sorted(set(blockers))
    return {
        "schema":"IRE_ONE_SHOT_RESEARCH_REPORT_V1",
        "run_fingerprint":_fingerprint(video_id,digest,policy),
        "video_id":video_id,
        "source_sha256":digest,
        "single_invocation_execution_finished":True,
        "stages":stages,
        "execution_status":"COMPLETED_WITH_BLOCKERS",
        "research_status":"BLOCKED",
        "blockers":blockers,
        "metrics":{
            "source_cue_count":details.get("source_cue_count"),
            "discourse_windows":details.get("discourse_windows"),
            "proposed_financial_atoms":details.get("proposed_financial_atoms"),
            "independently_reviewed_claims":0,
            "independently_verified_financial_claims":0,
            "official_claim_approvals":0,
            "official_search_candidates":details.get("official_search_candidates"),
            "real_document_text_fetches":details.get("real_document_text_fetches"),
            "scoped_evidence_audits":details.get("scoped_evidence_audits"),
            "retrieval_candidate_queries":details.get("retrieval_candidate_queries"),
            "measured_real_precision":None,
            "measured_real_recall":None
        },
        "private_details":details,
        "previous_research_data_loaded":False,
        "previous_research_results_cited":False,
        "factual_truth_certified":False,
        "approved_claims":0,
        "automatic_knowledge_merge":False,
        "external_independent_human_reviewer_attested":False,
        "financial_research_release":"BLOCKED"
    }


def execute_independent_research(
    raw: bytes, video_id: str, original_sha: str,
    policy: OrchestrationPolicy,
    semantic_request_fn: Callable[[dict],dict] | None = None,
    official_response_fn: Callable[[dict],dict] | None = None,
    evidence_read_fn=None,
    evidence_model_fn=None,
    sleep_fn: Callable[[int],None] | None = None,
) -> dict:
    """One call does all eligible work; always produces a terminal audit report.

    Injected callbacks are explicitly TEST-ONLY. A test callback cannot
    upgrade any financial claim or impersonate external human review.
    """
    policy.validate()
    stages=[]
    blockers=[]
    details={
        "source_cue_count":None,
        "discourse_windows":None,
        "proposed_financial_atoms":None,
        "official_search_candidates":None,
        "retrieval_candidate_queries":None,
        "claim_worklist":None,
        "source_validation":None,
        "semantic_validation":None,
        "relation_candidates":None,
        "official_source_candidates":None,
        "evidence_scope_audits":None,
        "fetched_primary_source_manifests":None,
        "evidence_download_failures":None,
        "real_document_text_fetches":None,
        "scoped_evidence_audits":None,
        "numeric_research_obligations":None,
        "semantic_generation_origin":"NOT_EXECUTED",
    }
    # Fail closed on original-byte mismatch, before considering external calls.
    try:
        source=source_record(raw,video_id,original_sha)
        details["source_cue_count"]=source["cue_count"]
        details["discourse_windows"]=len(source["windows"])
        details["source_validation"]={
            "source_sha256":original_sha,
            "total_cues":source["cue_count"],
            "discourse_windows":len(source["windows"]),
            "every_cue_mapped":source["all_source_cues_assigned"],
            "audio_verified":False,
        }
        stages.append(_stage("SOURCE_INTEGRITY","PASSED",
                              cue_count=source["cue_count"],
                              window_count=len(source["windows"])))
    except (ValueError,TypeError,KeyError) as exc:
        error=_safe_error(exc)
        blockers.append(error)
        stages.append(_stage("SOURCE_INTEGRITY","FAILED_CLOSED",
                             error_code=error))
        stages.append(_stage("FINAL_PRIVATE_REPORT","COMPLETED_BLOCKED"))
        return _finalize(video_id,original_sha,policy,stages,blockers,details)

    if policy.model is None:
        blockers.append("SEMANTIC_MODEL_NOT_CONFIGURED")
        stages.append(_stage("FINANCIAL_SEMANTICS","BLOCKED",
                             reason="SEMANTIC_MODEL_NOT_CONFIGURED"))
        stages.append(_stage("FINAL_PRIVATE_REPORT","COMPLETED_BLOCKED"))
        return _finalize(video_id,original_sha,policy,stages,blockers,details)

    inference=None
    last_error=None
    for attempt in range(policy.max_model_attempts):
        try:
            inference=interpret_original(
                raw,video_id,InferenceConfig(model=policy.model),
                request_fn=semantic_request_fn,
                private_checkpoint_directory=policy.private_checkpoint_directory,
            )
            last_error=None
            break
        except (ValueError,TypeError,KeyError,OSError) as exc:
            last_error=_safe_error(exc)
            if last_error not in RETRYABLE_MODEL_ERRORS or (
                    attempt+1==policy.max_model_attempts):
                break
            if sleep_fn is None:
                time.sleep(min(2**attempt,4))
            else:
                sleep_fn(min(2**attempt,4))
    if inference is None:
        blockers.append(last_error or "SEMANTIC_EXECUTION_FAILED")
        stages.append(_stage("FINANCIAL_SEMANTICS","BLOCKED",
                             error_code=last_error or "SEMANTIC_EXECUTION_FAILED",
                             attempts=attempt+1))
        stages.append(_stage("FINAL_PRIVATE_REPORT","COMPLETED_BLOCKED"))
        return _finalize(video_id,original_sha,policy,stages,blockers,details)

    manifest=inference["annotation_manifest"]
    details["semantic_generation_origin"]=inference["inference_mode"]
    details["proposed_financial_atoms"]=len(manifest["claims"])
    # All model claims are only unreviewed proposals.
    details["provisional_claim_manifest"]=manifest
    stages.append(_stage("FINANCIAL_SEMANTICS","PROPOSALS_GENERATED_UNVERIFIED",
                          model_calls_completed=inference["completed_window_count"],
                          model_calls_reused_from_private_cache=inference[
                              "previously_cached_window_count"],
                          inference_mode=inference["inference_mode"]))
    try:
        validated=validate_annotations(raw,original_sha,video_id,manifest)
        details["semantic_validation"]=validated
        stages.append(_stage("ATOMIC_TRACEABILITY","STRUCTURAL_VALIDATION_PASSED",
                             original_cues=validated["source_cues"],
                             unreviewed_proposals=validated["proposed_atomic_claims"],
                             unresolved_cues=validated["unresolved_cues"]))
        if validated["unresolved_cues"]:
            blockers.append("UNRESOLVED_SOURCE_CUES_PRESENT")
    except (ValueError,TypeError,KeyError) as exc:
        error=_safe_error(exc)
        blockers.append(error)
        stages.append(_stage("ATOMIC_TRACEABILITY","FAILED_CLOSED",
                             error_code=error))
        stages.append(_stage("FINAL_PRIVATE_REPORT","COMPLETED_BLOCKED"))
        return _finalize(video_id,original_sha,policy,stages,blockers,details)

    # Evidence discovery searches must not be confused with source verification.
    candidates=[]
    if not policy.enable_primary_discovery:
        stages.append(_stage("INDEPENDENT_PRIMARY_DISCOVERY","DISABLED",
                             reason="EXPLICIT_DISCOVERY_OPT_OUT"))
        blockers.append("INDEPENDENT_OFFICIAL_EVIDENCE_NOT_RESEARCHED")
    elif len(manifest["claims"])>policy.max_discovery_claims:
        stages.append(_stage("INDEPENDENT_PRIMARY_DISCOVERY","BLOCKED_BUDGET",
                             claims=len(manifest["claims"]),
                             limit=policy.max_discovery_claims))
        blockers.append("RESEARCH_CLAIM_BUDGET_EXCEEDED")
    elif not manifest["claims"]:
        stages.append(_stage("INDEPENDENT_PRIMARY_DISCOVERY","NO_CLAIMS",
                             candidate_count=0))
        blockers.append("NO_FINANCIAL_ATOMS_INDEPENDENTLY_VALIDATED")
    elif official_response_fn is None and not os.environ.get("OPENAI_API_KEY"):
        stages.append(_stage("INDEPENDENT_PRIMARY_DISCOVERY","BLOCKED",
                             reason="OFFICIAL_WEB_SEARCH_API_KEY_MISSING"))
        blockers.append("OFFICIAL_WEB_SEARCH_API_KEY_MISSING")
    else:
        search_error=None
        for claim in manifest["claims"]:
            try:
                if official_response_fn:
                    response=official_response_fn(claim)
                    screened=screen_discovery_response(response,claim["claim_id"])
                else:
                    screened=discover_official_candidates(
                        claim,policy.research_model or policy.model,
                        os.environ["OPENAI_API_KEY"])
                candidates.append(screened)
            except (ValueError,TypeError,KeyError,OSError) as exc:
                search_error=_safe_error(exc)
                break
        if search_error:
            stages.append(_stage("INDEPENDENT_PRIMARY_DISCOVERY","BLOCKED_PARTIAL",
                                 researched_claim_count=len(candidates),
                                 error_code=search_error))
            blockers.append(search_error)
        else:
            stages.append(_stage("INDEPENDENT_PRIMARY_DISCOVERY",
                                 "CANDIDATES_ONLY_NOT_VERIFIED",
                                 researched_claim_count=len(candidates),
                                 verified_official_evidence=0))
        blockers.append("OFFICIAL_CITATIONS_NOT_INDEPENDENTLY_VERIFIED")
    details["official_source_candidates"]=candidates
    details["official_search_candidates"]=sum(
        e["candidate_count"] for e in candidates)

    # Primary evidence must be independently downloaded and compared with the
    # NEW claim. A web-search citation alone can never count as verification.
    verified_texts=[]
    audited=[]
    fetch_failures=[]
    evidence_budget=policy.max_evidence_documents
    detail_claims={c["claim_id"]:c for c in manifest["claims"]}
    # Round-robin source candidates across claims, so the first claim cannot
    # monopolise a limited official evidence budget.
    discovered_urls=[]
    maximum=max((len(entry["official_domain_candidate_urls"])
                 for entry in candidates),default=0)
    for rank in range(maximum):
        for entry in candidates:
            urls=entry["official_domain_candidate_urls"]
            if rank<len(urls):
                discovered_urls.append((entry["claim_id"],urls[rank]))
    if not policy.enable_primary_discovery:
        stages.append(_stage("PRIMARY_DOCUMENT_VERIFICATION","SKIPPED_DISCOVERY_DISABLED"))
    elif not discovered_urls:
        stages.append(_stage("PRIMARY_DOCUMENT_VERIFICATION","BLOCKED_NO_CANDIDATE_DOCUMENTS"))
        blockers.append("NO_PRIMARY_DOCUMENT_BODY_VERIFIED")
    elif evidence_budget==0:
        stages.append(_stage("PRIMARY_DOCUMENT_VERIFICATION","BLOCKED_EVIDENCE_BUDGET_ZERO"))
        blockers.append("PRIMARY_EVIDENCE_BUDGET_ZERO")
    elif official_response_fn is not None and evidence_read_fn is None:
        # Never turn a test-injected fake search result into a real network GET.
        stages.append(_stage("PRIMARY_DOCUMENT_VERIFICATION",
                             "BLOCKED_TEST_DISCOVERY_WITHOUT_READER"))
        blockers.append("MOCK_DISCOVERY_EVIDENCE_FETCH_NOT_EXECUTED")
    elif evidence_model_fn is None and not os.environ.get("OPENAI_API_KEY"):
        stages.append(_stage("PRIMARY_DOCUMENT_VERIFICATION","BLOCKED_MODEL_KEY_MISSING"))
        blockers.append("EVIDENCE_AUDIT_API_KEY_MISSING")
    else:
        for claim_id,url in discovered_urls[:evidence_budget]:
            claim=detail_claims.get(claim_id)
            if claim is None:
                fetch_failures.append({
                    "claim_id":claim_id,"url":url,
                    "error_code":"EVIDENCE_CLAIM_ID_NOT_IN_NEW_LEDGER"})
                continue
            try:
                document=independently_fetch_candidate(
                    url,read_fn=evidence_read_fn,
                    private_evidence_dir=policy.private_evidence_dir)
                verified_texts.append({
                    "claim_id":claim_id,
                    "url":document["canonical_url"],
                    "document_sha256":document["raw_sha256"],
                    "text_sha256":document["visible_text_sha256"],
                    "bytes":document["raw_byte_size"],
                    "retrieved_at_utc":document["retrieved_at_utc"],
                    "inference_test_reader":document["source_read_mode"]==
                         "INJECTED_SYNTHETIC_READER",
                    "issuer_domain_candidate":document["issuer_domain_category"],
                    "truncated":document["extracted_text_truncated"],
                    "private_snapshot_path":document["private_immutable_source_snapshot"]
                })
                audit=compare_to_fetched_evidence(
                    claim,document,policy.research_model or policy.model,
                    api_key=os.environ.get("OPENAI_API_KEY",""),
                    model_fn=evidence_model_fn)
                audited.append(audit)
            except (ValueError,TypeError,KeyError,OSError) as exc:
                fetch_failures.append({
                    "claim_id":claim_id,"url":url,
                    "error_code":_safe_error(exc)})
        details["evidence_scope_audits"]=audited
        details["evidence_download_failures"]=fetch_failures
        if audited:
            stages.append(_stage("PRIMARY_DOCUMENT_VERIFICATION",
                                 "PROVISIONAL_SCOPED_AUDITS_NOT_APPROVED",
                                 downloaded_text_documents=len(verified_texts),
                                 scope_model_audits=len(audited),
                                 retrieval_failures=len(fetch_failures),
                                 documents_not_attempted=max(
                                     0,len(discovered_urls)-evidence_budget)))
        else:
            stages.append(_stage("PRIMARY_DOCUMENT_VERIFICATION",
                                 "BLOCKED_NO_AUDIT_COMPLETED",
                                 downloaded_text_documents=len(verified_texts),
                                 scope_model_audits=0,
                                 retrieval_failures=len(fetch_failures)))
        blockers.append("OFFICIAL_DOCUMENT_COMPARISON_NOT_HUMAN_CERTIFIED")
        if fetch_failures:
            blockers.append("PRIMARY_DOCUMENT_DOWNLOAD_OR_AUDIT_FAILURES")
        if len(discovered_urls)>evidence_budget:
            blockers.append("PRIMARY_DOCUMENT_BUDGET_INCOMPLETE")
    details["fetched_primary_source_manifests"]=verified_texts
    details["real_document_text_fetches"]=sum(
        not item["inference_test_reader"] for item in verified_texts)
    details["scoped_evidence_audits"]=len(audited)
    if details["evidence_scope_audits"] is None:
        details["evidence_scope_audits"]=[]
    if details["evidence_download_failures"] is None:
        details["evidence_download_failures"]=[]
    # No human reviewer has independently validated this financial fact.
    # Even 'SUPPORTS' is only an evidence review candidate.

    try:
        worklist=pending_research(manifest)
        details["claim_worklist"]=worklist
        numeric=[
            {"claim_id":claim["claim_id"],
             "required_checks":[t for t in row["obligations"] if
                 t=="INDEPENDENT_DECIMAL_FORMULA_INPUT_AND_UNITS"],
             "verified_calculation_count":0,
             "status":"REQUIRES_INDEPENDENT_CALCULATION"}
            for claim,row in zip(manifest["claims"],worklist["claims"])
            if "INDEPENDENT_DECIMAL_FORMULA_INPUT_AND_UNITS"
                in row["obligations"]
        ]
        details["numeric_research_obligations"]=numeric
        stages.append(_stage("QUANTITATIVE_OBLIGATIONS",
                             "WORKLIST_BUILT_UNVERIFIED",
                             numeric_claims_needing_check=len(numeric)))
    except (ValueError,TypeError,KeyError) as exc:
        error=_safe_error(exc)
        blockers.append(error)
        stages.append(_stage("QUANTITATIVE_OBLIGATIONS","FAILED_CLOSED",
                             error_code=error))

    if len(manifest["claims"])>policy.max_retrieval_claims:
        stages.append(_stage("WITHIN_SOURCE_RELATIONS","BLOCKED_BUDGET",
                             claim_count=len(manifest["claims"]),
                             max_claims=policy.max_retrieval_claims))
        blockers.append("RETRIEVAL_CLAIM_BUDGET_EXCEEDED")
    else:
        try:
            related=related_proposals(manifest,top_k=10,audit_count=8)
            details["relation_candidates"]=related
            details["retrieval_candidate_queries"]=len(related["queries"])
            stages.append(_stage("WITHIN_SOURCE_RELATIONS",
                                 "CANDIDATES_ONLY_NOT_VERIFIED",
                                 query_count=len(related["queries"])))
        except (ValueError,TypeError,KeyError) as exc:
            error=_safe_error(exc)
            blockers.append(error)
            stages.append(_stage("WITHIN_SOURCE_RELATIONS","FAILED_CLOSED",
                                 error_code=error))
    stages.append(_stage("INDEPENDENT_REVIEW_GATE","BLOCKED",
                         reason="TWO_INDEPENDENT_BLIND_REVIEWERS_NOT_ATTESTED"))
    blockers.append("TWO_INDEPENDENT_BLIND_REVIEWERS_NOT_ATTESTED")
    stages.append(_stage("FINAL_PRIVATE_REPORT","COMPLETED_BLOCKED",
                         research_approvals=0,auto_merges=0))
    return _finalize(video_id,original_sha,policy,stages,blockers,details)


def unavailable_original_report(video_id: str, original_sha: str,
                                policy: OrchestrationPolicy) -> dict:
    """Persist source-file failures instead of losing a whole batch."""
    policy.validate()
    stages=[
        _stage("SOURCE_INTEGRITY","FAILED_CLOSED",
               error_code="ORIGINAL_SOURCE_UNAVAILABLE"),
        _stage("FINAL_PRIVATE_REPORT","COMPLETED_BLOCKED")
    ]
    return _finalize(video_id,original_sha,policy,stages,
                     ["ORIGINAL_SOURCE_UNAVAILABLE"],{})
