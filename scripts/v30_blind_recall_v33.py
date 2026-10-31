#!/usr/bin/env python3
"""V3.3 genuine-source blind recall review protocol (stdlib only).

1. Full pair census from distinct, original-SRT-verified, double-reviewed
   atomic financial semantic frames. Reviewer packets contain NO predictions.
2. Two independent label sets, signatures and reconciliation; signed
   adjudication for disagreement; labels MUST be committed before predictions.
3. Frozen model/index hashes and Git chronological order checked prior to
   computing recall / precision with Wilson confidence intervals.
4. Real-world independent *identity* or reviewer blindness cannot be proven
   by local software; never auto-issue a release/research completion approval.

No #1-260 data can satisfy a REAL_UNEXPOSED source census.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from itertools import combinations
from pathlib import Path
import hashlib
import hmac
import json
import re
import subprocess

from v30_verified_core import (
 guard,sha256,canonical,HASH_RE,verify_attestation
)
from v30_semantic_frame_v33 import (
 BoundSemanticFrame,verified_frame
)
from v30_independent_evaluator import stats

PACKET_SCHEMA="V33_BLINDED_FULL_PAIR_CENSUS_V1"
GOLD_SCHEMA="V33_TWO_REVIEWER_SEALED_RELATION_GOLD_V1"
PRED_SCHEMA="V33_FROZEN_ENGINE_CENSUS_PREDICTIONS_V1"
KINDS=frozenset(("RELATED","UNRELATED","UNRESOLVED"))
RELATION_TYPES=frozenset((
 "SAME_FINANCIAL_EVENT","QUALIFIES_OR_EXCEPTS",
 "CONTRADICTS_OR_CORRECTS","CALCULATION_DEPENDENCY",
 "SHARED_CONCEPT_ONLY","UNRELATED","UNRESOLVED"
))

def make_blind_census(bound_frames,roster,cohort_kind,maximum=80):
    guard(type(bound_frames) is list and
          2<=len(bound_frames)<=maximum<=80 and
          cohort_kind in ("REAL_UNSEEN_261_PLUS",
                          "SYNTHETIC_UNIT_TEST_ONLY") and
          type(roster) is dict,
          "FULL_BLINDED_CENSUS_REQUIRES_BOUND_SOURCE_LIST")
    claims=[];ids=set()
    for b in bound_frames:
        guard(isinstance(b,BoundSemanticFrame),
              "BLIND_EVAL_CANNOT_USE_UNVERIFIED_SEMANTIC_FRAME")
        frame=verified_frame(b)
        vid=frame["source_video_id"]
        source=roster.get(vid)
        guard(type(source) is dict and
              frame["source_srt_sha256"]==source.get("srt_sha256")
              and frame["claim_id"] not in ids,
              "BLIND_COHORT_UNVERIFIED_SOURCE_OR_DUPLICATE_CLAIM")
        ids.add(frame["claim_id"])
        if cohort_kind=="REAL_UNSEEN_261_PLUS":
            guard(frame["source_class"]=="REAL_ORIGINAL" and
                  type(source.get("video_number")) is int and
                  261<=source["video_number"]<=791 and
                  source.get("verified_historical_project_nonexposure")
                    is True and
                  source.get("externally_approved_source_custody") is True,
                  "REAL_GOLD_SOURCE_NOT_GENUINELY_UNEXPOSED_OR_CUSTODIED")
        else:
            guard(frame["source_class"]=="SYNTHETIC_FIXTURE"
                  and source.get("video_number",0)>=800,
                  "FICTIONAL_GOLD_EXAMPLE_MUST_STAY_SYNTHETIC")
        claims.append({
            "claim_id":frame["claim_id"],
            "video_number":source["video_number"],
            "video_id":vid,
            "claim_text":frame["claim_text"],
            "claim_text_sha256":frame["claim_text_sha256"],
            "source_quote":frame["source_quote"],
            "cue_indices":frame["cue_indices"],
            "source_srt_sha256":frame["source_srt_sha256"],
            "frame_sha256":b.frame_digest,
            "source_reviewer_id":b.source_reviewer_id,
            "semantic_reviewer_id":b.semantic_reviewer_id,
            "modality":frame["modality"],
            "event_kind":frame["event_kind"],
            "verdict":frame["legacy_verdict"],
            "no_model_prediction_exposed":True,
        })
    claims.sort(key=lambda x:x["claim_id"])
    cases=[]
    for a,b in combinations(claims,2):
        pair_sha=sha256(canonical(sorted((a["claim_id"],b["claim_id"]))))
        cases.append({
           "case_id":"C"+pair_sha[:20],
           "left_claim_id":a["claim_id"],"right_claim_id":b["claim_id"],
           "source_claims":[a,b],
           "stratum":("SAME_VIDEO" if a["video_id"]==b["video_id"]
                      else "CROSS_VIDEO"),
           "expected_label":None,
           "model_prediction":None,
        })
    case_ids=[c["case_id"] for c in cases]
    guard(len(case_ids)==len(set(case_ids)),
          "BLINDED_PAIR_ID_COLLISION")
    index_digest=sha256(canonical([
         {"id":c["claim_id"],"frame_sha256":c["frame_sha256"]}
         for c in claims]))
    source_digest=sha256(canonical(sorted([
         (vid,meta["srt_sha256"],meta["video_number"])
         for vid,meta in roster.items()])))
    return {
       "schema":PACKET_SCHEMA,
       "cohort_kind":cohort_kind,
       "pair_sampling_method":"FULL_CENSUS",
       "source_cohort_sha256":source_digest,
       "frozen_semantic_index_sha256":index_digest,
       "number_of_claims":len(claims),
       "total_pairs_in_census":len(cases),
       "noncandidate_sample_may_not_replace_full_census":True,
       "label_review_packet_contains_no_model_output":True,
       "cases":cases,
       "automatic_knowledge_approval":False,
       "user_private_raw_quotes_must_remain_off_github":True,
    }

def blind_packet_digest(packet):
    guard(type(packet) is dict and packet.get("schema")==PACKET_SCHEMA
          and packet.get("pair_sampling_method")=="FULL_CENSUS"
          and packet.get("label_review_packet_contains_no_model_output") is True
          and type(packet.get("cases")) is list
          and len(packet["cases"])==packet.get("total_pairs_in_census"),
          "BLIND_PACKET_MUST_HAVE_FULL_CENSUS_AND_NO_MODEL_PREDICTIONS")
    for row in packet["cases"]:
        guard(row.get("expected_label") is None
              and row.get("model_prediction") is None,
              "MODEL_PREDICTIONS_OR_GOLD_LEAKED_INTO_BLIND_PACKET")
    return sha256(canonical(packet))

def verify_role_review(review,packet_sha,case_ids,role,authorities):
    guard(type(review) is dict
          and review.get("schema")=="V33_SIGNED_BLIND_LABEL_SET_V1"
          and review.get("packet_sha256")==packet_sha
          and review.get("blind_to_model_predictions") is True
          and review.get("did_not_develop_engine") is True
          and review.get("reviewer_role")==role,
          "BLIND_SEPARATE_REVIEW_REQUIRED")
    labels=review.get("labels")
    guard(type(labels) is list and len(labels)==len(case_ids)
          and len({x.get("case_id") for x in labels})==len(labels)
          and {x.get("case_id") for x in labels}==set(case_ids),
          "INDEPENDENT_REVIEW_MUST_LABEL_ALL_CENSUS_PAIRS")
    for label in labels:
        guard(type(label) is dict and
              set(label)=={"case_id","label","relation_type","reason","stratum"}
              and label["label"] in KINDS
              and label["relation_type"] in RELATION_TYPES
              and isinstance(label["reason"],str)
              and len(label["reason"].strip())>=10
              and label["stratum"] in ("SAME_VIDEO","CROSS_VIDEO"),
              "BLIND_LABEL_INCOMPLETE_OR_UNREVIEWED")
        guard((label["label"]=="RELATED")==
              (label["relation_type"] in (
                "SAME_FINANCIAL_EVENT","QUALIFIES_OR_EXCEPTS",
                "CONTRADICTS_OR_CORRECTS","CALCULATION_DEPENDENCY"))
              if label["label"]!="UNRESOLVED" else
              label["relation_type"]=="UNRESOLVED",
              "BLIND_LABEL_RELATION_KIND_CONFLICT")
    payload={
       "schema":review["schema"],
       "packet_sha256":packet_sha,
       "labels_sha256":sha256(canonical(labels)),
       "blind_to_model_predictions":True,
       "did_not_develop_engine":True,
    }
    rid=verify_attestation(review.get("attestation"),payload,role,authorities)
    return {x["case_id"]:x for x in labels},rid

def check_chronological_git_precommit(root,gold_file,prediction_file,
                                      freeze_file):
    """Actual repository commit ordering. Does NOT verify human blindness."""
    root=Path(root)
    def log_commit(path):
        p=subprocess.run(["git","log","-1","--format=%H","--",str(path)],
                         cwd=root,capture_output=True,text=True)
        guard(p.returncode==0 and
              re.fullmatch("[0-9a-f]{40}",p.stdout.strip()),
              "MISSING_GIT_SEALED_PRECOMMIT_FILE")
        return p.stdout.strip()
    pinned=[log_commit(x) for x in (freeze_file,gold_file,prediction_file)]
    guard(len(set(pinned))==3,
          "GOLD_MODEL_FREEZE_AND_PREDICTION_MUST_BE_SEPARATE_COMMITS")
    for left,right in zip(pinned,pinned[1:]):
        p=subprocess.run(["git","merge-base","--is-ancestor",left,right],
                         cwd=root,capture_output=True)
        guard(p.returncode==0,
              "BLIND_GOLD_WAS_NOT_PUBLISHED_BEFORE_MODEL_PREDICTION")
    return {
        "engine_freeze_commit":pinned[0],
        "gold_label_commit":pinned[1],
        "prediction_commit":pinned[2],
        "chronologically_precommitted":True,
        "reviewer_blindness_not_proven_by_git":True,
    }

def evaluate_blind(packet,gold,predictions,authorities,
                   verified_git_order=None):
    packet_sha=blind_packet_digest(packet)
    guard(type(gold) is dict and gold.get("schema")==GOLD_SCHEMA
          and gold.get("packet_sha256")==packet_sha
          and type(predictions) is dict and
          predictions.get("schema")==PRED_SCHEMA
          and predictions.get("packet_sha256")==packet_sha,
          "BLIND_EVAL_PACKET_GOLD_AND_PREDICTIONS_MUST_MATCH")
    guard(gold.get("engine_frozen_before_labeling") is True
          and gold.get("reviewers_model_predictions_unseen") is True
          and gold.get("external_reviewer_organization_identity_verified")
              is True
          and predictions.get("engine_sha256")==
              gold.get("engine_sha256")
          and predictions.get("index_sha256")==
              packet["frozen_semantic_index_sha256"],
          "BLIND_EVAL_CANNOT_SELF_CLAIM_EXTERNAL_REVIEWER_IDENTITY")
    # External identity verification is a custodian attestation, not a fact
    # proved by simply setting a JSON boolean. Always report that limitation.
    ids=[x["case_id"] for x in packet["cases"]]
    a,reviewer_a=verify_role_review(
        gold["reviewer_a"],packet_sha,ids,
        "blind_gold_reviewer_a",authorities)
    b,reviewer_b=verify_role_review(
        gold["reviewer_b"],packet_sha,ids,
        "blind_gold_reviewer_b",authorities)
    guard(reviewer_a!=reviewer_b and
          all(reviewer_a not in (c["source_reviewer_id"],
                 c["semantic_reviewer_id"]) and
              reviewer_b not in (c["source_reviewer_id"],
                 c["semantic_reviewer_id"])
              for row in packet["cases"] for c in row["source_claims"]),
          "NOT_INDEPENDENT_FROM_SOURCE_OR_SEMANTIC_ANNOTATOR")
    # Independent reviewers may write different explanations while agreeing
    # on labels; only disagreements in relation classification require a third
    # adjudicator. Both independently signed explanations remain in the audit.
    def decision(x):
        return (x["label"],x["relation_type"],x["stratum"])
    disputed={c for c in ids if decision(a[c])!=decision(b[c])}
    resolutions={}
    if disputed:
        review=gold.get("adjudicator")
        guard(review is not None,
              "BLIND_REVIEW_DISAGREEMENT_REQUIRES_THIRD_INDEPENDENT_ADJUDICATION")
        resolutions,adjudicator=verify_role_review(
            review,packet_sha,ids,"blind_gold_adjudicator",authorities)
        guard(adjudicator not in (reviewer_a,reviewer_b) and
              all(adjudicator not in (c["source_reviewer_id"],
                     c["semantic_reviewer_id"])
                  for row in packet["cases"] for c in row["source_claims"]),
              "ADJUDICATOR_MUST_BE_DISTINCT_FROM_ALL_PRIOR_REVIEWERS")
    final={}
    for i in ids:
        final[i]=(a[i] if i not in disputed else resolutions[i])
        guard(final[i]["label"]!="UNRESOLVED",
              "UNRESOLVED_LABEL_CANNOT_ENTER_FINAL_RECALL_DENOMINATOR")
    p=predictions.get("cases")
    guard(type(p) is list and len(p)==len(ids)
          and {r.get("case_id") for r in p}==set(ids)
          and len({r.get("case_id") for r in p})==len(ids)
          and all(type(r.get("candidate")) is bool and
                  set(r)=={"case_id","candidate"} for r in p),
          "EVALUATOR_MUST_SCORE_ALL_CANDIDATE_AND_NONCANDIDATE_PAIRS")
    guard(type(verified_git_order) is dict
          and verified_git_order.get("chronologically_precommitted") is True,
          "NO_GIT_ORDER_NO_BLIND_PERFORMANCE_CLAIM")
    pm={x["case_id"]:x["candidate"] for x in p}
    counts=Counter();by=defaultdict(Counter);errors=[]
    for row in packet["cases"]:
        case_id=row["case_id"]
        label=final[case_id]
        guard(label["stratum"]==row["stratum"],
              "SAMPLE_STRATUM_GOLD_SPOOFED")
        truth=label["label"]=="RELATED"
        selected=pm[case_id]
        cell=("TP" if truth else "FP") if selected else (
              "FN" if truth else "TN")
        counts[cell]+=1;by[row["stratum"]][cell]+=1
        if cell in ("FN","FP"):errors.append(case_id)
    overall=stats({k:counts[k] for k in ("TP","FN","FP","TN")})
    strata={s:stats({k:v[k] for k in ("TP","FN","FP","TN")})
            for s,v in sorted(by.items())}
    prec=overall["precision"];recall=overall["recall"]
    met=bool(prec and recall and
             prec["lower"]>=0.85 and recall["lower"]>=0.95)
    # An independently issued custodian identity/scope proof is required
    # outside this process; HMAC verifies possession only. Never auto-release.
    return {
       "schema":"V33_TWO_REVIEWER_FULL_CENSUS_RECALL_EVALUATION_V1",
       "packet_sha256":packet_sha,
       "case_count":len(ids),
       "sample_type":"FULL_CENSUS_OF_REGISTERED_COHORT",
       "source_real_unseen":packet["cohort_kind"]=="REAL_UNSEEN_261_PLUS",
       "separate_blind_reviewers_signed":True,
       "external_human_identity_verifiable_by_this_software":False,
       "blindness_from_prediction_not_cryptographically_proven":True,
       "git_chronology":verified_git_order,
       "overall":overall,
       "by_stratum":strata,
       "false_positive_and_negative_case_ids":errors,
       "numeric_wilson_thresholds_met":met,
       "automatic_model_release":False,
       "automatic_knowledge_merge":False,
       "automatic_research_complete":False,
    }

def pending_real_unseen_gate(source_status):
    """Do not fabricate a recall percentage from missing originals or labels."""
    guard(type(source_status) is dict,
          "MISSING_CUSTODIAN_SOURCE_STATUS")
    return {
        "schema":"V33_REAL_UNSEEN_RECALL_PRECONDITIONS_V1",
        "target_video_numbers":source_status.get("target_video_numbers",[]),
        "actual_original_srt_files_hash_verified":
          source_status.get("original_srt_sha_verified",0),
        "distinct_approved_source_and_semantic_reviews":
          source_status.get("independent_semantic_reviews",0),
        "blind_human_gold_sets_committed":
          source_status.get("independent_blind_gold_committed",0),
        "frozen_engine_prediction_sets":
          source_status.get("frozen_engine_predictions",0),
        "measured_recall":None,
        "measured_precision":None,
        "release_status":"BLOCKED_NO_AUTHENTICATED_REAL_UNSEEN_GOLD",
        "cannot_substitute_older_historical_001_260_for_unseen":True,
    }
