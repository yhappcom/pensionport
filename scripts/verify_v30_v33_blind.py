#!/usr/bin/env python3
"""Adversarial V3.3 blind gold/retrieval scoring *synthetic fixture* only.

No external review identity, source audio, #261+ original SRT or real
blind recall has been supplied. Positive test of the integrity contract
does not satisfy its required real-world inputs.
"""
import copy
import hashlib
import hmac
import json
import secrets
from pathlib import Path

from v30_verified_core import policy_gate,canonical,sha256
from v30_semantic_extraction_v33 import extract_from_original
from v30_semantic_frame_v33 import (
 verify_independent_frame,check_actual_cue_provenance
)
from v30_blind_recall_v33 import (
 make_blind_census,blind_packet_digest,evaluate_blind,
 pending_real_unseen_gate
)
from verify_v30_v33_semantics import sample,reviewed

ROOT=Path(__file__).resolve().parents[1]

def req(cond,msg):
    if not cond:raise ValueError(msg)
def reject(fn,code):
    try:fn()
    except (ValueError,KeyError,TypeError):return
    raise ValueError("BLIND_HOLDOUT_GATE_ACCEPTED_FORGED_"+code)

def run(root=ROOT):
    policy_gate(root)
    data,ledger,manifest=sample()
    proposals=extract_from_original(data,manifest,ledger)["frames"]
    f=[
      reviewed(proposals[0],"TAX_CONTRIBUTION","CONTRIBUTE",
               "KR:PENSION_SAVINGS","PENSION_CONTRIBUTION"),
      reviewed(proposals[1],"TAX_WITHDRAWAL","WITHDRAW",
               "KR:PENSION_SAVINGS","PENSION_WITHDRAWAL"),
      reviewed(proposals[2],"INDEX_TRACKING","COMPARE",
               "KR:ETF_INDEX","TRACKING_ERROR"),
    ]
    keys={}
    for role in ("source_reviewer","semantic_reviewer",
                 "blind_gold_reviewer_a","blind_gold_reviewer_b"):
        keys[role]={
            "reviewer_id":"SYNTHETIC_"+role+"_ONLY",
            "secret":secrets.token_bytes(32),
            "test_fixture":False,
        }
    def sign(role,payload):
        x=keys[role]
        return {
         "role":role,"reviewer_id":x["reviewer_id"],
         "mac":hmac.new(x["secret"],canonical(payload),
                        hashlib.sha256).hexdigest()
        }
    def bind(frame):
        proof=check_actual_cue_provenance(frame,data)
        source_payload={
            "video_id":frame["source_video_id"],
            "srt_sha256":frame["source_srt_sha256"],
            "claim_id":frame["claim_id"],
            "claim_text_sha256":frame["claim_text_sha256"],
            "cue_indices":frame["cue_indices"],
            "quote_sha256":sha256(frame["source_quote"].encode("utf-8")),
        }
        sem_payload={
           "frame_sha256":proof["frame_sha256"],
           "source_payload_sha256":sha256(canonical(source_payload)),
           "review_scope":"FINANCIAL_STRUCTURE_NOT_FINANCIAL_TRUTH",
        }
        return verify_independent_frame(
            frame,data,sign("source_reviewer",source_payload),
            sign("semantic_reviewer",sem_payload),keys)
    bound=[bind(frame) for frame in f]
    roster={
        manifest["video_id"]:{
          "video_number":manifest["video_number"],
          "srt_sha256":manifest["srt_sha256"]
        }
    }
    packet=make_blind_census(
        bound,roster,"SYNTHETIC_UNIT_TEST_ONLY")
    digest=blind_packet_digest(packet)
    req(packet["total_pairs_in_census"]==3 and
        packet["number_of_claims"]==3 and
        all(c["model_prediction"] is None and
            c["expected_label"] is None for c in packet["cases"]),
        "BLIND_PACKET_MUST_NOT_REVEAL_MODEL_OUTPUT")
    source_ids=[f["claim_id"] for f in proposals]
    pairtruth={
       frozenset(source_ids[:2]):("RELATED","QUALIFIES_OR_EXCEPTS"),
       frozenset((source_ids[0],source_ids[2])):("UNRELATED","UNRELATED"),
       frozenset((source_ids[1],source_ids[2])):("UNRELATED","UNRELATED"),
    }
    label_list=[]
    for case in packet["cases"]:
        label,kind=pairtruth[frozenset((
            case["left_claim_id"],case["right_claim_id"]))]
        label_list.append({
          "case_id":case["case_id"],
          "label":label,
          "relation_type":kind,
          "reason":"Synthetic example for blind reviewer label integrity.",
          "stratum":case["stratum"],
        })
    def blind_review(role,labels):
        payload={
            "schema":"V33_SIGNED_BLIND_LABEL_SET_V1",
            "packet_sha256":digest,
            "labels_sha256":sha256(canonical(labels)),
            "blind_to_model_predictions":True,
            "did_not_develop_engine":True,
        }
        return {
            "schema":"V33_SIGNED_BLIND_LABEL_SET_V1",
            "packet_sha256":digest,
            "blind_to_model_predictions":True,
            "did_not_develop_engine":True,
            "reviewer_role":role,
            "labels":labels,
            "attestation":sign(role,payload),
        }
    a=blind_review("blind_gold_reviewer_a",label_list)
    second=copy.deepcopy(label_list)
    for x in second:x["reason"]="Second synthetic reviewer writes independently."
    b=blind_review("blind_gold_reviewer_b",second)
    gold={
        "schema":"V33_TWO_REVIEWER_SEALED_RELATION_GOLD_V1",
        "packet_sha256":digest,
        "engine_sha256":"a"*64,
        "engine_frozen_before_labeling":True,
        "reviewers_model_predictions_unseen":True,
        # Only simulated to test the HMAC gate, not real org evidence.
        "external_reviewer_organization_identity_verified":True,
        "reviewer_a":a,"reviewer_b":b,
    }
    predictions={
        "schema":"V33_FROZEN_ENGINE_CENSUS_PREDICTIONS_V1",
        "packet_sha256":digest,
        "engine_sha256":"a"*64,
        "index_sha256":packet["frozen_semantic_index_sha256"],
        "cases":[{"case_id":c["case_id"],
                  "candidate":pairtruth[frozenset((
                      c["left_claim_id"],c["right_claim_id"]))][0]=="RELATED"}
                 for c in packet["cases"]]
    }
    simulated_git={
        "chronologically_precommitted":True,
        "fixture_only_not_actual_git_provenance":True,
    }
    outcome=evaluate_blind(packet,gold,predictions,keys,simulated_git)
    req(outcome["overall"]["counts"]==
         {"TP":1,"FN":0,"FP":0,"TN":2} and
        not outcome["numeric_wilson_thresholds_met"] and
        not outcome["automatic_model_release"] and
        outcome["external_human_identity_verifiable_by_this_software"]
             is False and
        not outcome["source_real_unseen"],
        "HUMAN_FIXTURE_MUST_NOT_BECOME_REAL_RECALL_CERTIFICATE")
    forged=copy.deepcopy(predictions)
    forged["cases"]=forged["cases"][:-1]
    reject(lambda:evaluate_blind(packet,gold,forged,keys,simulated_git),
           "MISSING_NONCANDIDATE_GOLD_PAIR")
    forged=copy.deepcopy(gold)
    forged["reviewer_a"]["labels"][0]["label"]="UNRELATED"
    reject(lambda:evaluate_blind(packet,forged,predictions,keys,
                                 simulated_git),"GOLD_CHANGED_AFTER_SIGNED")
    forged=copy.deepcopy(gold)
    forged["reviewer_b"]["attestation"]=forged["reviewer_a"]["attestation"]
    reject(lambda:evaluate_blind(packet,forged,predictions,keys,
                                 simulated_git),"REVIEWER_ROLE_REPLAY")
    forged=copy.deepcopy(gold)
    forged["external_reviewer_organization_identity_verified"]=False
    reject(lambda:evaluate_blind(packet,forged,predictions,keys,
                                 simulated_git),"MISSING_EXTERNAL_AUTHORITY")
    forged=copy.deepcopy(gold)
    forged["engine_sha256"]="b"*64
    reject(lambda:evaluate_blind(packet,forged,predictions,keys,
                                 simulated_git),"ENGINE_CHANGED_AFTER_LABEL")
    forged=copy.deepcopy(packet)
    forged["cases"][0]["model_prediction"]=True
    reject(lambda:evaluate_blind(forged,gold,predictions,keys,
                                 simulated_git),"MODEL_LEAKAGE_IN_GOLD_PACKET")
    # Synthetic credential reuse cannot pass the real unexposed video gate.
    reject(lambda:make_blind_census(
             bound,roster,"REAL_UNSEEN_261_PLUS"),
           "SYNTHETIC_SOURCE_PASSED_AS_261_PLUS")
    missing=copy.deepcopy(packet)
    reject(lambda:evaluate_blind(packet,gold,predictions,keys,None),
           "NO_PRECOMMIT_ORDER")
    status=json.loads((root/"v30/holdout/v33_261_264_unseen_intake_v1.json").read_text())
    req(status["total_new_source_originals_verified"]==0 and
        status["external_blind_gold_commit_count"]==0 and
        all(x["source_srt_sha256"] is None for x in
            status["video_candidates"]),
        "MISSING_REAL_UNSEEN_SOURCE_STATUS_FALSIFIED")
    pending=pending_real_unseen_gate({
        "target_video_numbers":[261,262,263,264],
        "original_srt_sha_verified":0,
        "independent_semantic_reviews":0,
        "independent_blind_gold_committed":0,
        "frozen_engine_predictions":0,
    })
    req(pending["measured_recall"] is None and
        pending["measured_precision"] is None and
        pending["release_status"]==
        "BLOCKED_NO_AUTHENTICATED_REAL_UNSEEN_GOLD",
        "MISSING_GOLD_FALSELY_RECEIVED_100_PERCENT")
    return {
        "schema":"V33_BLIND_RECALL_ADVERSARIAL_PROTOCOL_TEST_V1",
        "test_mode":"SYNTHETIC_FIXTURE_ONLY_NOT_REAL_BLIND_HUMAN_REVIEW",
        "synthetic_source_claims":3,
        "full_pair_census":3,
        "dual_signed_synthetic_gold":True,
        "structural_mock_confusion_matrix":outcome["overall"]["counts"],
        "simulated_git_order_is_not_true_preregistration":True,
        "real_261_264_source_originals_verified":0,
        "real_external_independent_blind_gold":0,
        "real_blind_recall":None,
        "leakage_label_replay_missing_pair_and_no_original_blocked":True,
        "no_automatic_knowledge_merge":True,
        "status":"BLOCKED"
    }

if __name__=="__main__":
    try:print(json.dumps(run(),ensure_ascii=False,sort_keys=True))
    except (ValueError,TypeError,KeyError) as exc:
        print(json.dumps({"gate":"FAIL","error":str(exc)},ensure_ascii=False))
        raise SystemExit(1)
