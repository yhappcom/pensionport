#!/usr/bin/env python3
"""Adversarial isolated V3.3 semantic frame verification on synthetic SRT.

These tests are NOT financial research, new real-video recall, or independent
human review. The keys are ephemeral fixtures and do not certify identity.
"""
import copy
import hashlib
import hmac
import json
import secrets
from pathlib import Path

from v30_verified_core import sha256,canonical,policy_gate,parse_srt
from v30_semantic_extraction_v33 import (
    extract_from_original,make_proposal,number_proposal
)
from v30_semantic_frame_v33 import (
    check_actual_cue_provenance,frame_proposal_summary,
    verify_independent_frame,verified_frame,semantic_relation_for_review
)

ROOT=Path(__file__).resolve().parents[1]

def require(flag,reason):
    if not flag:raise ValueError(reason)
def must_reject(fn,code):
    try:fn()
    except (ValueError,TypeError,KeyError):return
    raise ValueError("V33_SECURITY_NEGATIVE_CASE_NOT_REJECTED_"+code)
def sample():
    vid="SYNTHV0033A"
    data=("1\n00:00:00,000 --> 00:00:02,000\n"
          "연금저축 계좌에 7% 세액공제율로 납입할 수 있다.\n\n"
          "2\n00:00:02,100 --> 00:00:05,000\n"
          "연금저축에서 적격 연금 인출 시 3% 세율이 적용될 수 있다.\n\n"
          "3\n00:00:05,100 --> 00:00:08,000\n"
          "증권사의 ETF 괴리율과 추적오차는 다른 금융 지표이다.\n").encode()
    digest=sha256(data)
    quotes=[
        "연금저축 계좌에 7% 세액공제율로 납입할 수 있다.",
        "연금저축에서 적격 연금 인출 시 3% 세율이 적용될 수 있다.",
        "증권사의 ETF 괴리율과 추적오차는 다른 금융 지표이다.",
    ]
    claims=[
        {"claim_id":f"{vid}-0{i+1}",
         "cue_indices":[i+1],
         "quote":quotes[i],
         "claim_types":["LEGAL_OR_PRODUCT","NUMERIC"]
                       if i<2 else ["QUALITATIVE"],
         "legacy_verdict":"QUALIFIED" if i!=2 else "CONTRADICTED",
         "material":True}
         for i in range(3)
    ]
    ledger={
        "schema":"V30_ATOMIC_LEDGER_V2",
        "cues":[
            {"cue_index":i+1,
             "classification":"MATERIAL",
             "claim_ids":[claims[i]["claim_id"]]}
             for i in range(3)
        ],
        "claims":claims,
    }
    manifest={
        "schema":"V33_ORIGINAL_SOURCE_CONTRACT_V1",
        "source_class":"SYNTHETIC_FIXTURE",
        "test_fixture":True,
        "video_number":901,
        "video_id":vid,
        "srt_sha256":digest,
        "cue_count":3,
    }
    return data,ledger,manifest

def reviewed(frame,event,action,subject_id,object_id):
    frame=copy.deepcopy(frame)
    frame["annotation_review_status"]="STRUCTURE_REVIEWED"
    frame["action"]=action
    frame["event_kind"]=event
    frame["subject"]={"kind":"ACCOUNT","canonical_id":subject_id}
    frame["object"]={"kind":"TRANSACTION","canonical_id":object_id}
    frame["modality"]="CONDITIONAL"
    frame["jurisdiction"]="KR"
    frame["effective_date"]="2026-10-31"
    frame["conditions"]={"population":"investors",
                         "exception":"source-specific, unresolved",
                         "trigger":"source condition review pending"}
    if frame["measurement"]["measure_type"]=="PERCENT_RATE":
        frame["measurement"]["rate_basis"]="REGULATORY_TAX_RATE"
        frame["measurement"]["period"]="2026-10"
    return frame

def run(root=ROOT):
    policy_gate(root)
    data,ledger,manifest=sample()
    result=extract_from_original(data,manifest,ledger)
    require(result["number_of_proposed_frames"]==3 and
            result["source_cue_count"]==3 and
            result["unresolved_generic_events"]==3 and
            result["unresolved_rate_bases"]==2 and
            result["automatic_approval"] is False and
            result["research_completion"] is False,
            "V33_MUST_NOT_PROMOTE_GENERIC_ATOMIC_EXTRACTION")
    proposal=result["frames"][0]
    require(frame_proposal_summary(proposal,data,ledger)["state"]=="RESEARCH_BLOCKED",
            "UNREVIEWED_FINANCIAL_FRAMES_ARE_NEVER_COMPLETED")
    # Explicit external model pinning accepts only source-aligned fields.
    atom=ledger["claims"][0]
    digest="a"*64
    m={
        "schema":"V33_PINNED_MODEL_SEMANTIC_PROPOSAL_V1",
        "claim_id":atom["claim_id"],
        "claim_text_sha256":proposal["claim_text_sha256"],
        "source_srt_sha256":manifest["srt_sha256"],
        "extractor_model_sha256":digest,
        "typed_fields":{
            "event_kind":"TAX_CONTRIBUTION",
            "action":"CONTRIBUTE",
            "subject":{"kind":"ACCOUNT","canonical_id":"KR:PENSION_SAVINGS"},
            "object":{"kind":"TRANSACTION","canonical_id":"CONTRIBUTION"}
        }
    }
    derived=make_proposal(atom,manifest["video_id"],manifest["srt_sha256"],
                          source_class="SYNTHETIC_FIXTURE",
                          extractor_annotation=m,extractor_sha=digest,
                          ledger_sha256=sha256(canonical(ledger)))
    require(derived["event_kind"]=="TAX_CONTRIBUTION"
            and derived["annotation_review_status"]=="PROPOSED",
            "MODEL_CANNOT_SELF_APPROVE_FINANCIAL_MEANING")
    tampered=copy.deepcopy(m)
    tampered["claim_text_sha256"]="0"*64
    must_reject(lambda:make_proposal(atom,manifest["video_id"],
                manifest["srt_sha256"],extractor_annotation=tampered,
                extractor_sha=digest,
                ledger_sha256=sha256(canonical(ledger))),"EXTRACTOR_CLAIM_DIGEST")
    frames=[
        reviewed(result["frames"][0],"TAX_CONTRIBUTION","CONTRIBUTE",
                 "KR:PENSION_SAVINGS","DEPOSIT"),
        reviewed(result["frames"][1],"TAX_WITHDRAWAL","WITHDRAW",
                 "KR:PENSION_SAVINGS","WITHDRAWAL"),
        reviewed(result["frames"][2],"INDEX_TRACKING","COMPARE",
                 "KR:ETF_PRODUCT","TRACKING_ERROR"),
    ]
    # These are throwaway test keys; test_fixture flag in source output makes
    # them unusable as external-independent real-world research evidence.
    keys={
      "source_reviewer":{
          "reviewer_id":"SIMULATED_SOURCE_REVIEWER_ONLY",
          "secret":secrets.token_bytes(32),"test_fixture":False},
      "semantic_reviewer":{
          "reviewer_id":"SIMULATED_SEMANTIC_REVIEWER_ONLY",
          "secret":secrets.token_bytes(32),"test_fixture":False}
    }
    def signed(frame,authorities=keys,source_reviewer_id=None):
        proof=check_actual_cue_provenance(frame,data,ledger)
        source_payload={
            "video_id":frame["source_video_id"],
            "srt_sha256":frame["source_srt_sha256"],
            "atomic_ledger_sha256":frame["source_atomic_ledger_sha256"],
            "claim_id":frame["claim_id"],
            "claim_text_sha256":frame["claim_text_sha256"],
            "cue_indices":frame["cue_indices"],
            "quote_sha256":sha256(frame["source_quote"].encode()),
        }
        semantic_payload={
            "frame_sha256":proof["frame_sha256"],
            "source_payload_sha256":sha256(canonical(source_payload)),
            "review_scope":"FINANCIAL_STRUCTURE_NOT_FINANCIAL_TRUTH",
        }
        attestations={}
        for role,payload in (("source_reviewer",source_payload),
                             ("semantic_reviewer",semantic_payload)):
            key=authorities[role]
            attestations[role]={
                "role":role,"reviewer_id":key["reviewer_id"],
                "mac":hmac.new(key["secret"],canonical(payload),
                               hashlib.sha256).hexdigest(),
            }
        return verify_independent_frame(frame,data,attestations["source_reviewer"],
            attestations["semantic_reviewer"],authorities,
            reviewed_ledger=ledger)
    first=signed(frames[0]);second=signed(frames[1])
    require(verified_frame(first)["event_kind"]=="TAX_CONTRIBUTION",
            "VERIFIED_FRAME_MUST_BIND_EXACT_SEMANTICS")
    compare=semantic_relation_for_review(first,second)
    require(compare["relation_candidate"]==
               "SHARED_ENTITY_BROAD_AUDIT_ONLY" and
            compare["automatic_knowledge_merge"] is False and
            compare["human_review_required"] is True,
            "CONTRIBUTION_VS_WITHDRAWAL_NOT_EQUIVALENT")
    # Source identity, time, amount unit and rate convention are hard barriers.
    bad=copy.deepcopy(frames[0])
    bad["source_quote"]="does not exist in any original cue"
    must_reject(lambda:check_actual_cue_provenance(bad,data,ledger),"FORGED_SOURCE_QUOTE")
    bad=copy.deepcopy(frames[0])
    bad["source_srt_sha256"]="0"*64
    must_reject(lambda:check_actual_cue_provenance(bad,data,ledger),"WRONG_SOURCE_HASH")
    bad=copy.deepcopy(frames[0])
    bad["cue_indices"]=[5]
    must_reject(lambda:check_actual_cue_provenance(bad,data,ledger),"INVALID_CUE_NUMBER")
    bad=copy.deepcopy(frames[0])
    bad["measurement"]["rate_basis"]="NOT_APPLICABLE"
    must_reject(lambda:check_actual_cue_provenance(bad,data,ledger),"RATE_BASE_MISSING")
    bad=copy.deepcopy(frames[0])
    bad["effective_date"]="2026-02-30"
    must_reject(lambda:check_actual_cue_provenance(bad,data,ledger),"INVALID_CALENDAR_DAY")
    bad=copy.deepcopy(frames[0])
    bad["legacy_verdict"]="CONTRADICTED"
    must_reject(lambda:check_actual_cue_provenance(bad,data,ledger),"REFUTED_FALSE_APPROVAL")
    bad=copy.deepcopy(frames[0])
    bad["annotation_review_status"]="PROPOSED"
    must_reject(lambda:signed(bad),"UNREVIEWED_PROPOSAL_CANNOT_SIGN")
    must_reject(lambda:verified_frame(frames[0]),"BARE_DICT_CANNOT_SIGN")
    bad=copy.deepcopy(frames[0])
    bad["claim_text"]=bad["claim_text"]+" 위조"
    must_reject(lambda:check_actual_cue_provenance(bad,data,ledger),"CLAIM_DIGEST_DRIFT")
    double=copy.deepcopy(keys)
    double["semantic_reviewer"]["reviewer_id"]=double["source_reviewer"]["reviewer_id"]
    must_reject(lambda:signed(frames[0],double),"SAME_HUMAN_TWO_REVIEW_ROLES")
    tampered=copy.deepcopy(frames[0])
    tampered["measurement"]["rate_basis"]="EFFECTIVE_ANNUAL"
    # New content must have *new* valid semantic reviewer signature,
    # and cannot be silently edited after a BoundSemanticFrame is created.
    import dataclasses
    forged=dataclasses.replace(first,semantic_frame=tampered)
    must_reject(lambda:verified_frame(forged),"POST_SIGN_FRAME_MODIFIED")
    # Genuine signed structural approval still does not approve real facts.
    require(compare["financial_fact_truth_verified"] is False and
            compare["research_completion_certificate"] is False and
            compare["independent_external_reviewer_identity_proven_by_code"] is False,
            "STRUCTURAL_REVIEW_MUST_NOT_CLAIM_EVIDENCE_OR_HUMAN_IDENTITY")
    # Real #261 attempt cannot reuse fake synthetic provenance.
    forged_manifest=dict(manifest)
    forged_manifest.update({"source_class":"REAL_ORIGINAL",
                            "test_fixture":False,"video_number":261})
    must_reject(lambda:extract_from_original(data,forged_manifest,ledger),
                "FAKE_REAL_UNSEEN_SOURCE")
    return {
        "schema":"V33_INDEPENDENT_ATOMIC_SEMANTICS_ADVERSARIAL_TEST_V1",
        "synthetic_cue_count":3,
        "synthetic_atomic_claim_count":3,
        "verified_structural_review_test_fixture_only":2,
        "proposals_unresolved_as_blocked":True,
        "forged_quote_hash_cue_rate_date_status_and_reviewer_rejected":True,
        "separate_human_reviewer_identity_independently_proven":False,
        "real_original_261_plus_used_in_test":0,
        "external_real_financial_truth_proven":0,
        "automatic_knowledge_merges":0,
        "release_status":"BLOCKED",
    }

if __name__=="__main__":
    try:print(json.dumps(run(),sort_keys=True,ensure_ascii=False))
    except (ValueError,KeyError,TypeError) as exc:
        print(json.dumps({"gate":"FAIL","error":str(exc)},ensure_ascii=False))
        raise SystemExit(1)
