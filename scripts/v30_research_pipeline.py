#!/usr/bin/env python3
"""V3.0 complete STAGE ROUTER: original SRT -> coverage -> evidence ->
quant/empirical -> hybrid relation review -> independent gate -> V5 preview.

This is executable offline with user-supplied source/evidence packages. It
never manufactures primary sources, actual empirical observations, an
independent human review, V5 completion certification or a knowledge merge.
"""
import argparse
import copy
import json
import os
import re
from pathlib import Path

from v30_verified_core import (
    guard,policy_gate,parse_srt,verify_ledger,sha256,canonical,
    check_privacy,frame_check,evidence_requirements,verify_attestation,
    VERDICTS,ROLES,bind_reviewed_claim,relation_for_bound_claims,
)
from v30_evidence_services import (
    review_primary_evidence,math_reproduce,empirical_reproduce,
)
from v30_hybrid_search import make_index,search

STAGES=("SOURCE_PROVENANCE","ATOMIC_COVERAGE","CLAIM_FRAME_AND_OBLIGATIONS",
        "PRIMARY_EVIDENCE","QUANT_AND_EMPIRICAL","RELATION_CANDIDATES",
        "INDEPENDENT_REVIEW","COMPLETION_AND_APPEND_ONLY_INTEGRATION")
ALLOWED_ROSTERS=frozenset(range(1,21))
DEV_RESEARCH_STATUS=("RESEARCH_BLOCKED","REVIEW_ELIGIBLE_PENDING_V5_CERTIFICATE")
PRIVATE_OUTPUT_FIELDS=frozenset(("raw_srt","source_text","full_quote",
                                 "personal_holdings","owner_portfolio"))
CONTROLS={
 "automatic_research_complete":False,
 "automatic_knowledge_merge":False,
 "automatic_trade":False,
 "research_requires_v5_certificate":True,
}

def summary_blockers(reason,claim_id=None):
    return {"code":reason,"claim_id":claim_id,"reopen_with":"ACTUAL_INDEPENDENT_VERIFIABLE_SOURCE_AND_HUMAN_REVIEW"}

def scan_source_state(root,manifest,raw_srt,ledger,authorities=None):
    """Use exactly supplied bytes and independently approved full cue map.

    Caller may not persuade this function to use a historical metadata SHA
    alone; it must supply *the actual source bytes*.
    """
    policy_gate(root)
    guard(type(manifest) is dict and
          manifest.get("schema")=="V30_FULL_SOURCE_MANIFEST_V1",
          "VERIFIABLE_SOURCE_MANIFEST_REQUIRED")
    video_id=manifest.get("video_id")
    number=manifest.get("video_number")
    guard(type(number) is int and number in ALLOWED_ROSTERS and
          isinstance(video_id,str) and
          re.fullmatch(r"[A-Za-z0-9_-]{11}",video_id),
          "POST20_UNSEEN_SOURCE_NOT_AUTHORIZED_FOR_DEVELOPMENT")
    expected=manifest.get("srt_sha256")
    cues=parse_srt(raw_srt,expected)
    guard(len(cues)==manifest.get("original_cue_count"),
          "ORIGINAL_CUE_COUNT_MISMATCH")
    legacy=manifest.get("legacy_verdicts")
    guard(legacy is None or isinstance(legacy,dict),
          "SOURCE_VERDICT_PROVENANCE_INVALID")
    coverage=verify_ledger(cues,ledger,video_id,legacy)
    binding={
        "video_id":video_id,"video_number":number,
        "srt_sha256":expected,"cue_count":len(cues),
        "ledger_sha256":sha256(canonical(ledger)),
    }
    review=False
    review_identity=None
    if manifest.get("source_review_attestation") and authorities:
        review_identity=verify_attestation(
            manifest["source_review_attestation"],binding,
            "source_reviewer",authorities)
        review=True
    return {
      "binding":binding,"coverage":coverage,"source_reviewer_authenticated":review,
      "source_reviewer_id":review_identity,
      "source_digest_checked_from_actual_bytes":True,
      "original_bytes_saved_in_public_report":False,
      "verified_cues":cues,
    }

def _review_links(claim_id,source,documents,models,empirical,authorities):
    evidence=[]
    issues=[]
    for data in documents:
        doc=data.get("metadata");body=data.get("bytes")
        guard(isinstance(doc,dict),"OFFICIAL_EVIDENCE_PACKET_INVALID")
        if claim_id not in doc.get("claim_ids",[]):continue
        try:r=review_primary_evidence(source,doc,body,authorities)
        except (ValueError,KeyError,TypeError) as exc:
            issues.append("PRIMARY_"+str(exc))
            continue
        evidence.append(r)
    if not any(e["legal_applicability_independently_audited"] for e in evidence):
        issues.append("OFFICIAL_PRIMARY_SOURCE_SCOPE_AND_AUTHENTICITY_UNAUDITED")
    numeric=[]
    for data in models:
        if claim_id not in data.get("claim_ids",[]):continue
        try:r=math_reproduce(data)
        except (ValueError,KeyError,TypeError) as exc:
            issues.append("NUMERIC_"+str(exc));continue
        r["model_id"]=data.get("model_id")
        r["source_assumptions_independently_reviewed"]=False
        if data.get("audit") and authorities:
            payload={"model_id":data["model_id"],"claim_id":claim_id,
                     "formula_value":r["formula_value"],
                     "model_assumptions_sha256":sha256(canonical({
                         k:v for k,v in data.items()
                         if k not in ("audit","claim_ids")
                     }))}
            try:
                r["independent_auditor_id"]=verify_attestation(
                    data["audit"],payload,"numeric_auditor",authorities)
                r["source_assumptions_independently_reviewed"]=True
            except (ValueError,KeyError,TypeError) as exc:
                issues.append("NUMERIC_ATTESTATION_"+str(exc))
        numeric.append(r)
    studies=[]
    for data in empirical:
        m=data.get("metadata",{})
        if claim_id not in m.get("claim_ids",[]):continue
        try:r=empirical_reproduce(data["bytes"],m)
        except (ValueError,KeyError,TypeError) as exc:
            issues.append("EMPIRICAL_"+str(exc));continue
        r["study_id"]=m.get("study_id")
        r["independent_dataset_and_method_review"]=False
        if m.get("audit") and authorities:
            payload={"study_id":m["study_id"],"claim_id":claim_id,
                     "dataset_sha256":r["source_data_sha256"],
                     "empirical_summary_sha256":sha256(canonical({
                        k:v for k,v in r.items()
                        if k not in ("independent_dataset_and_method_review",)
                     }))}
            try:
                r["independent_auditor_id"]=verify_attestation(
                    m["audit"],payload,"empirical_auditor",authorities)
                r["independent_dataset_and_method_review"]=True
            except (ValueError,KeyError,TypeError) as exc:
                issues.append("EMPIRICAL_ATTESTATION_"+str(exc))
        studies.append(r)
    return evidence,numeric,studies,issues

def research_run(root,manifest,raw_srt,ledger,
                 documents=(),models=(),empirical=(),search_bank=(),
                 authorities=None,independent_review=None):
    """Create a REAL, repeatable research **work product**, not an auto-cert."""
    root=Path(root)
    x=scan_source_state(root,manifest,raw_srt,ledger,authorities)
    binding=x["binding"]
    rows=[]
    index=make_index(list(search_bank)) if search_bank else ()
    for atom in ledger["claims"]:
        cid=atom["claim_id"]
        issues=[]
        types=atom["claim_types"]
        basis=evidence_requirements(types)
        try:
            frame=frame_check(atom.get("frame"),types)
            frame_ok=True
        except (ValueError,KeyError,TypeError) as err:
            frame_ok=False
            frame=None
            issues.append("FRAME_"+str(err))
        source={
          "claim_id":cid,"frame":frame if frame is not None else {},
          "claim_types":types,
          "legacy_verdict":atom["legacy_verdict"]}
        if not x["source_reviewer_authenticated"]:
            issues.append("FULL_ATOMIC_LEDGER_HAS_NO_EXTERNAL_SOURCE_REVIEW_ATTESTATION")
        if atom["legacy_verdict"]=="CONTRADICTED":
            issues.append("REFUTED_SOURCE_CORRECTION_ONLY")
        if atom["legacy_verdict"]=="HYPOTHETICAL":
            issues.append("HYPOTHETICAL_MODEL_NOT_VERIFIED_AS_REAL_WORLD_FACT")
        ev=[];quant=[];studies=[];link_issues=[]
        if frame_ok:
            ev,quant,studies,link_issues=_review_links(
                cid,source,documents,models,empirical,authorities)
            issues+=link_issues
        if "REPRODUCED_NUMERIC_METHOD" in basis:
            if not any(q["independent_methods_agree"] and
                       q["source_assumptions_independently_reviewed"] and
                       q["historical_asserted_value_matches_model"] is not False
                       for q in quant):
                issues.append("INDEPENDENT_NUMERIC_MODEL_OR_SOURCE_ASSUMPTIONS_MISSING")
        if "REPRODUCED_REAL_EMPIRICAL_STUDY" in basis:
            if not any(q["independent_dataset_and_method_review"]
                       for q in studies):
                issues.append("REAL_EMPIRICAL_REPRODUCTION_AND_REVIEW_MISSING")
        proposals=None
        if index:
            proposals=search({"claim_id":cid,"text":atom["quote"],
                              "financial_role":frame.get("financial_role")
                                  if frame_ok else None,
                              "topic_families":atom.get("topic_families",[])},
                             index,limit=min(10,len(index)),
                             audit_non_candidates=5)
        rows.append({
          "claim_id":cid,"legacy_verdict":atom["legacy_verdict"],
          "claim_types":types,"source_cue_indices":atom["cue_indices"],
          "source_origin_sha256":binding["srt_sha256"],
          "financial_frame_complete":frame_ok,
          "required_evidence_domains":basis,
          "primary_evidence":[{k:v for k,v in d.items()
                               if k in ("source_id","sha256","exact_quote_present",
                                        "legal_applicability_independently_audited",
                                        "evidence_status")} for d in ev],
          "quant_evidence":[{k:v for k,v in d.items()
                            if k in ("model_id","formula_value",
                                     "source_assumptions_independently_reviewed",
                                     "historical_asserted_value_matches_model")}
                            for d in quant],
          "empirical_evidence":[{k:v for k,v in d.items()
                                if k in ("study_id","source_data_sha256",
                                         "independent_dataset_and_method_review")}
                                for d in studies],
          "relations_review_queue":proposals,
          "source_risk":("CORRECTION_ONLY" if atom["legacy_verdict"]=="CONTRADICTED"
                         else "UNREPLICATED_HYPOTHETICAL_SOURCE"
                         if atom["legacy_verdict"]=="HYPOTHETICAL"
                         else "HUMAN_REVIEW_ONLY"),
          "blockers":sorted(set(issues)),
          "evidence_analysis_status":"READY_FOR_INDEPENDENT_REVIEW"
                                     if not issues else "RESEARCH_BLOCKED",
          "positively_approved_knowledge":False,
        })
    result_payload={
        "video_id":binding["video_id"],
        "srt_sha256":binding["srt_sha256"],
        "ledger_sha256":binding["ledger_sha256"],
        "claim_review_summary":[
            {"claim_id":r["claim_id"],"blockers":r["blockers"]}
            for r in rows
        ],
    }
    review_id=None
    if independent_review and authorities:
        if x["source_reviewer_authenticated"]:
            try:
                review_id=verify_attestation(
                    independent_review,result_payload,
                    "independent_reviewer",authorities)
                guard(review_id!=x["source_reviewer_id"],
                      "INDEPENDENT_REVIEWER_CANNOT_SELF_REVIEW")
            except (ValueError,KeyError,TypeError):
                review_id=None
    # A relation may be computed only from independently source-signed,
    # process-sealed claim objects. Typed relations remain review candidates.
    bound=[]
    if x["source_reviewer_authenticated"] and authorities:
        for atom in ledger["claims"]:
            try:
                bound.append(bind_reviewed_claim(
                    atom,binding,manifest["source_review_attestation"],authorities))
            except (ValueError,TypeError,KeyError):
                pass
    intra=[]
    for i,a in enumerate(bound):
        for b in bound[i+1:]:
            intra.append(relation_for_bound_claims(a,b))
    pending=sum(bool(r["blockers"]) for r in rows)
    reviewer_block=(None if review_id else
                    "INDEPENDENT_REVIEW_SIGNED_ATTESTATION_MISSING")
    state=("REVIEW_ELIGIBLE_PENDING_V5_CERTIFICATE"
           if pending==0 and review_id else "RESEARCH_BLOCKED")
    stages={}
    stages["SOURCE_PROVENANCE"]="PASSED" if x["source_reviewer_authenticated"] else "BLOCKED"
    stages["ATOMIC_COVERAGE"]="PASSED" if x["source_reviewer_authenticated"] else "BLOCKED"
    stages["CLAIM_FRAME_AND_OBLIGATIONS"]="PASSED" if all(
        r["financial_frame_complete"] for r in rows) else "BLOCKED"
    stages["PRIMARY_EVIDENCE"]="PASSED" if all(
        not any(b.startswith("OFFICIAL_") or b.startswith("PRIMARY_")
                for b in r["blockers"]) for r in rows) else "BLOCKED"
    stages["QUANT_AND_EMPIRICAL"]="PASSED" if all(
        not any(b.startswith("INDEPENDENT_NUMERIC_") or
                b.startswith("REAL_EMPIRICAL_") or
                b.startswith("NUMERIC_") or b.startswith("EMPIRICAL_")
                for b in r["blockers"]) for r in rows) else "BLOCKED"
    stages["RELATION_CANDIDATES"]="REVIEW_ONLY" if index else "BLOCKED"
    stages["INDEPENDENT_REVIEW"]="PASSED" if review_id else "BLOCKED"
    stages["COMPLETION_AND_APPEND_ONLY_INTEGRATION"]="BLOCKED_REQUIRES_V5_CERTIFICATE"
    result={
        "schema":"V30_END_TO_END_RESEARCH_WORK_PRODUCT_V1",
        "video_id":binding["video_id"],
        "video_number":binding["video_number"],
        "input_srt_sha256":binding["srt_sha256"],
        "input_ledger_sha256":binding["ledger_sha256"],
        "source_cue_count":binding["cue_count"],
        "atomic_coverage":x["coverage"],
        "source_reviewer_authenticated":x["source_reviewer_authenticated"],
        "claims_processed":len(rows),
        "claims_with_open_blockers":pending,
        "independent_review_authenticated":bool(review_id),
        "source_sealed_claim_count":len(bound),
        "intra_video_typed_relation_candidates":intra,
        "typed_relation_accuracy_independently_verified":False,
        "stages":stages,
        "claim_results":rows,
        "reviewer_blocker":reviewer_block,
        "research_status":state,
        "v5_certificate_status":"NOT_ISSUED",
        "automatic_knowledge_approvals":0,
        "automatic_research_completion_certificates":0,
        "automatic_personal_investment_advice":0,
        "trade_orders":0,
        "immutable_source_cues_persisted_publicly":False,
    }
    check_privacy(result)
    return result

def v5_append_only_preview(root,event,source_claim_origin_sha):
    """Call original V5 gate to preview PENDING overlay; never autoapprove."""
    from verify_v5_knowledge_integration import (
        compare_and_integrate,read,git_blob_sha,
    )
    root=Path(root)
    policy_gate(root)
    guard(isinstance(event,dict) and
          event.get("review_state")=="PENDING_REVIEW" and
          event.get("certificate_path") is None and
          event.get("source_blob_sha")==source_claim_origin_sha and
          event.get("source_path","").startswith("data/analysis_events/") and
          git_blob_sha(root/event["source_path"])==source_claim_origin_sha,
          "UNVERIFIED_SOURCE_OR_AUTOMATIC_APPROVAL_ATTEMPTED")
    policy=read(root/"v5/integration/integration_policy_v1.json")
    seed=read(root/"data/synthesis/investment_knowledge_001_260/curated_recurring_concepts_16.json")
    preview=compare_and_integrate([event],seed,policy,root)
    guard(preview["approved_overlaid_relation_count"]==0 and
          not preview["automatic_semantic_merge_claimed"] and
          preview["original_claims_overwritten"]==0,
          "UNAUTHORIZED_V5_OVERLAY")
    return preview

def complete_with_preexisting_v5_certificate(root,certificate_path,review_path):
    """Validate actual existing V5 certificate via V5's original verifier.

    This does not mint an approval and cannot overrule the V5 research gate.
    """
    from verify_v5_research_completion import verify,digest,read
    root=Path(root)
    policy_gate(root)
    guard(re.fullmatch(r"v5/completion/v5_\d{3}_[A-Za-z0-9_-]{11}_certificate\.json",
                       certificate_path or "") is not None and
          re.fullmatch(r"v5/videos/v5_\d{3}_[A-Za-z0-9_-]{11}_advisory_review\.json",
                       review_path or "") is not None,
          "EXISTING_V5_CERTIFICATE_AND_REVIEW_PATHS_REQUIRED")
    c=root/certificate_path;v=root/review_path
    guard(c.is_file() and v.is_file(),"MISSING_EXISTING_V5_CERTIFICATE_BYTES")
    x=verify(read(c),read(v),
             read(root/"v5/policy/research_completion_gate_v1.json"),
             digest(v),root)
    return {
        "existing_v5_certificate_verdict":x,
        "source_v5_certificate_path":certificate_path,
        "automatically_generated_certificates":0,
        "automatic_knowledge_merge":False,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--manifest",type=Path)
    p.add_argument("--original-srt",type=Path)
    p.add_argument("--atomic-ledger",type=Path)
    p.add_argument("--evidence-package",type=Path)
    p.add_argument("--search-bank",type=Path)
    args=p.parse_args()
    root=args.root.resolve()
    policy_gate(root)
    if not (args.manifest and args.original_srt and args.atomic_ledger):
        print(json.dumps({
            "schema":"V30_END_TO_END_RUNNER_PREFLIGHT_V1",
            "status":"RESEARCH_BLOCKED",
            "missing":["--manifest","--original-srt","--atomic-ledger"],
            "policy_gate":"PASS",
            "current_work":"Runner ready for real supplied originals and separately audited evidence",
            "new_unseen_video_21_plus_opened":False,
            "release":"BLOCKED"
        },ensure_ascii=False))
        return
    manifest=json.loads(args.manifest.read_text())
    ledger=json.loads(args.atomic_ledger.read_text())
    evidence=(json.loads(args.evidence_package.read_text())
              if args.evidence_package else {})
    index=(json.loads(args.search_bank.read_text())
           if args.search_bank else [])
    def read_pack(arr):
        return [dict(x,bytes=Path(x["content_path"]).read_bytes())
                for x in arr]
    report=research_run(
        root,manifest,args.original_srt.read_bytes(),ledger,
        documents=read_pack(evidence.get("primary_sources",[])),
        empirical=[{"metadata":x,"bytes":Path(x["content_path"]).read_bytes()}
                   for x in evidence.get("empirical_studies",[])],
        models=evidence.get("math_models",[]),search_bank=index,
        authorities=None,independent_review=None)
    print(json.dumps(report,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    try:main()
    except (ValueError,KeyError,TypeError,IndexError,OSError) as err:
        print(json.dumps({"gate":"FAIL","error":str(err)},ensure_ascii=False))
        raise SystemExit(1)
