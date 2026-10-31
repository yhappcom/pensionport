#!/usr/bin/env python3
"""V3.0 <-> V5 preservation bridge, blocked research certificates and proposals.

This produces REVIEW-ONLY structures. A completed V5 research certificate
cannot be created from an automatic V3.0 work product; approved integration
must pass V5's existing source-provenance and human-review gates.
"""
import hashlib
import json
import re
from pathlib import Path

from v30_verified_core import guard,policy_gate,blob_sha,check_privacy,canonical

def _as_json_bytes(data):
    return (json.dumps(data,sort_keys=True,ensure_ascii=False,
                       indent=2)+"\n").encode("utf-8")

def blocked_v5_package(report,root):
    """Create in-memory blocked review/certificate, verify with original V5 gate."""
    from verify_v5_research_completion import verify
    root=Path(root)
    policy_gate(root)
    guard(isinstance(report,dict) and
          report.get("schema")=="V30_END_TO_END_RESEARCH_WORK_PRODUCT_V1" and
          report["research_status"]=="RESEARCH_BLOCKED" and
          1<=report["video_number"]<=20 and
          report["claims_processed"]==len(report["claim_results"])>0 and
          report["automatic_research_completion_certificates"]==0,
          "ONLY_REAL_BLOCKED_V30_WORK_PRODUCTS_MAY_BE_EXPORTED")
    from v30_verified_core import VERDICTS
    claims=[];obligations=[];blockers=[]
    for row in report["claim_results"]:
        cid=row["claim_id"]
        kinds=row["claim_types"]
        verdict=row["legacy_verdict"]
        guard(isinstance(cid,str) and
              cid.startswith(report["video_id"]+"-") and
              verdict in VERDICTS and
              row["evidence_analysis_status"]=="RESEARCH_BLOCKED",
              "INVALID_V30_BLOCKED_CLAIM")
        primary=(kinds[0] if len(kinds)==1 else
                 "STRATEGY_OR_PERFORMANCE" if "STRATEGY_OR_PERFORMANCE" in kinds else
                 "NUMERIC" if "NUMERIC" in kinds else
                 "LEGAL_OR_PRODUCT" if "LEGAL_OR_PRODUCT" in kinds
                 else "QUALITATIVE")
        claims.append({
            "id":cid,"material":True,
            "legacy_verdict":verdict,
            "positive_principle_allowed":False,
            "current_review":"BLOCKED",
            "independently_checked_this_turn":False,
            "v30_claim_types":kinds,
        })
        obligations.append({
            "claim_id":cid,"claim_type":primary,
            "material":True,"status":"BLOCKED",
            "applicability":"Research subject to original source and jurisdiction",
            "counterexample":"Not independently verified; possible exceptions",
            "decision_impact":"No investment or tax conclusion permitted",
            "primary_source_ids":[],"model_ids":[],"empirical_ids":[],
            "empirical_not_applicable_reason":(
                None if "STRATEGY_OR_PERFORMANCE" in kinds
                else "Not established from authenticated external evidence"),
        })
        blockers.append({
            "id":"V30-"+str(len(blockers)+1).zfill(3),
            "claim_ids":[cid],
            "missing_evidence":"; ".join(row["blockers"]) or
                               "Unverified independent source review",
            "decision_blocked":"Evidence-based conclusion and automatic integration",
            "reopen_when":"Verified source, model, empirical study, reviewer certificate",
        })
    review={
      "schema":"V30_BRIDGED_V5_BLOCKED_REVIEW_V1",
      "video_id":report["video_id"],"video_number":report["video_number"],
      "synthetic_example":False,
      "source":{
          "raw_srt_read_and_hash_verified_this_turn":(
               report["input_srt_sha256"] is not None),
          "full_cue_review_this_turn":(
               report["source_reviewer_authenticated"] is True),
          "source_cue_count":report["source_cue_count"],
          "srt_sha256":report["input_srt_sha256"],
          "original_bytes_persisted":False,
      },
      "claims":claims,
      "primary_sources":[],
      "models":[],
      "open_blockers":blockers,
      "one_turn_closeout":{"result":"EVIDENCE_BLOCKED"},
      "decision_logic":{"baseline_is_same_horizon_and_currency":False},
      "source_provenance_read_only":True,
    }
    digest=hashlib.sha256(_as_json_bytes(review)).hexdigest()
    cert={
      "schema":"RESEARCH_CERTIFICATE_V1",
      "video_id":report["video_id"],
      "video_number":report["video_number"],
      "review_sha256":digest,
      "uses_personal_data":False,
      "contains_private_srt":False,
      "preflight":{
           "expected_claim_count":len(claims),
           "classified_before_conclusions":True,
      },
      "obligations":obligations,
      "empirical_evidence":[],
      "domains":{key:{"status":"BLOCKED",
                      "reason":"V3.0 evidence/reviewer obligations not completed"}
                 for key in ("SOURCE_AND_CLAIMS","PRIMARY_EVIDENCE",
                             "QUANT_AND_EMPIRICAL","GENERAL_DECISION")},
      "blockers":blockers,
      "source_audits":{},
      "independent_audit":{
           "human_or_separately_appointed_reviewer":False,
           "source_and_method_checked":False,
           "limitations":"No independent verification certificate issued",
      },
      "release":{
         "status":"RESEARCH_BLOCKED","approved":False,
         "personal_advice":False,"trading":False,
      },
      "multi_type_obligation_companion":{
         row["claim_id"]:row["required_evidence_domains"]
         for row in report["claim_results"]
      }
    }
    policy=json.loads((root/"v5/policy/research_completion_gate_v1.json").read_text())
    status=verify(cert,review,policy,digest,root)
    guard(status=="RESEARCH_BLOCKED" and cert["release"]["approved"] is False,
          "V5_RESEARCH_COMPLETENESS_GATE_WAS_BYPASSED")
    check_privacy(review);check_privacy(cert)
    return {
        "schema":"V30_V5_BLOCKED_REVIEW_AND_CERTIFICATE_DRAFT_V1",
        "review":review,"certificate":cert,
        "review_bytes_sha256":digest,
        "verified_by_original_v5_gate":True,
        "certificates_automatically_approved":0,
        "knowledge_overlays_automatically_approved":0,
        "status":"RESEARCH_BLOCKED"
    }

def pending_knowledge_proposal(root,source_id,source_claim_id,concept_id,
                               relation="TOPIC_ONLY"):
    """Generate pending overlay through original V5 integration preview."""
    from v30_research_pipeline import v5_append_only_preview
    root=Path(root)
    policy_gate(root)
    guard(isinstance(source_id,str) and
          re.fullmatch(r"[A-Za-z0-9_-]{11}",source_id) and
          source_claim_id.startswith(source_id+"-"),
          "PROPOSAL_REQUIRES_ACTUAL_SOURCE_CLAIM_ID")
    source_path="data/analysis_events/"+source_id+".json"
    p=root/source_path
    guard(p.is_file(),"UNREGISTERED_HISTORICAL_SOURCE_FOR_PROPOSAL")
    sha=blob_sha(p)
    token=hashlib.sha256((source_claim_id+"|"+concept_id+"|"+relation).encode()).hexdigest()
    proposal={
       "event_id":"V5-COMP-"+str(int(token[:12],16)%900000+100000),
       "source_path":source_path,
       "source_blob_sha":sha,
       "source_claim_id":source_claim_id,
       "target_concept_id":concept_id,
       "relation":relation,
       "review_state":"PENDING_REVIEW",
       "assessment":"V3.0 source-traced comparison candidate, not approved evidence",
       "evidence_refs":[],"evidence_blob_shas":{},
       "blocked_reason":"Independent material evidence and V5 RESEARCH_COMPLETE not yet certified",
       "reopen_trigger":"External independent review and valid V5 research completion",
       "supersedes_claim_id":None,"certificate_path":None,
    }
    guard(relation in ("TOPIC_ONLY","SUPPORTS_UNDER_CONDITIONS",
                       "QUALIFIES_SCOPE","CONTRADICTS","CORRECTION_ONLY"),
          "UNAPPROVED_CONCEPT_MIGRATION_NOT_ALLOWED")
    view=v5_append_only_preview(root,proposal,sha)
    guard(view["approved_overlaid_relation_count"]==0,
          "PENDING_OVERLAY_MUST_NOT_BE_IMPORTED")
    return {
      "schema":"V30_V5_APPEND_ONLY_PENDING_BRIDGE_V1",
      "event":proposal,
      "preview":view,
      "existing_legacy_events_modified":0,
      "automatic_merge":False,
      "approved":False,
    }
