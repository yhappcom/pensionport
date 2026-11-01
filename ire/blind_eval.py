"""Blind, source-pinned financial proposition performance evaluation.

Blind gold must be made independently from new original SRT by two external
reviewers, adjudicated by a third, and cryptographically frozen BEFORE seeing
the IRE predictions. This evaluator validates formal evidence and computes
strict confusion counts ONLY from a separately adjudicated alignment.

A file saying 'reviewed' is NOT proof that actual human reviewers existed.
No historical research or prior claim corpus may be used as gold.
"""
from __future__ import annotations

import hashlib
import json
import math
import re

from .source import parse_srt,require,sha256,text_norm
from .claims import MODALITIES

GOLD_ID=re.compile(r"^G[0-9]{5,8}$")
PRED_ID=re.compile(r"^C[0-9]{5,8}$")
VERDICTS=frozenset({"EXACT","PARTIAL","INCORRECT"})
FRAME_FIELDS=frozenset({
    "subject","product","financial_event","action","object",
    "jurisdiction","effective_date","conditions","exceptions",
    "measurements","modality"
})
FIELD_VERDICTS=frozenset({"CORRECT","INCORRECT","UNDETERMINED"})


def _canonical(value: dict) -> bytes:
    return json.dumps(value,ensure_ascii=False,sort_keys=True,
                      separators=(",",":"),allow_nan=False).encode("utf-8")


def digest_json(value: dict) -> str:
    return sha256(_canonical(value))


def _reviewer(record: dict):
    require(type(record) is dict and set(record)=={
        "reviewer_id","independent_from_model_attestation",
        "source_first_review_sha256"},
        "GOLD_REVIEWER_SCHEMA_INVALID")
    require(type(record["reviewer_id"]) is str
            and re.fullmatch(r"[A-Za-z0-9_-]{3,48}",record["reviewer_id"])
            and record["independent_from_model_attestation"] is True
            and type(record["source_first_review_sha256"]) is str
            and re.fullmatch(r"[0-9a-f]{64}",
                             record["source_first_review_sha256"]),
            "GOLD_REVIEWER_SOURCE_FIRST_ATTESTATION_MISSING")


def validate_blind_gold(raw: bytes,source_sha: str,
                        video_id: str,gold: dict) -> dict:
    cues=parse_srt(raw,source_sha)
    require(type(gold) is dict and set(gold)=={
        "schema","video_id","source_sha256","reviewers",
        "adjudicator_id","claims","source_only_adjudication"},
        "GOLD_SCHEMA_INVALID")
    require(gold["schema"]=="IRE_BLIND_GOLD_V1"
            and gold["source_sha256"]==source_sha
            and gold["video_id"]==video_id
            and gold["source_only_adjudication"] is True,
            "GOLD_SOURCE_IDENTITY_OR_BLINDNESS_INVALID")
    reviewers=gold["reviewers"]
    require(type(reviewers) is list and len(reviewers)==2,
            "GOLD_REQUIRES_TWO_SEPARATE_REVIEWERS")
    for entry in reviewers:
        _reviewer(entry)
    ids={r["reviewer_id"] for r in reviewers}
    require(len(ids)==2 and
            gold["adjudicator_id"] not in ids and
            type(gold["adjudicator_id"]) is str and
            re.fullmatch(r"[A-Za-z0-9_-]{3,48}",
                         gold["adjudicator_id"]),
            "GOLD_ADJUDICATOR_NOT_ROLE_SEPARATED")
    claims=gold["claims"]
    require(type(claims) is list and len(claims)<=100000,
            "GOLD_ATOM_COUNT_INVALID")
    seen=set()
    for claim in claims:
        require(type(claim) is dict and set(claim)=={
            "gold_id","proposition","source_refs","financial_frame",
            "financial_importance"},
            "GOLD_ATOM_SCHEMA_INVALID")
        gid=claim["gold_id"]
        require(type(gid) is str and GOLD_ID.fullmatch(gid)
                and gid not in seen,"GOLD_ATOM_ID_INVALID_OR_DUPLICATE")
        seen.add(gid)
        require(type(claim["proposition"]) is str and
                5<=len(claim["proposition"])<=10000,
                "GOLD_PROPOSITION_INVALID")
        require(claim["financial_importance"] in (
            "CRITICAL","STANDARD"),"GOLD_IMPORTANCE_INVALID")
        refs=claim["source_refs"]
        require(type(refs) is list and 1<=len(refs)<=80,
                "GOLD_QUOTE_CENSUS_INVALID")
        indices=[]
        for ref in refs:
            require(type(ref) is dict and set(ref)=={
                "cue_index","quote"},"GOLD_QUOTE_SCHEMA_INVALID")
            index=ref["cue_index"]
            require(type(index) is int and 1<=index<=len(cues),
                    "GOLD_INVALID_SOURCE_CUE")
            quote=ref["quote"]
            require(type(quote) is str and len(quote)>=2 and
                    text_norm(quote) in text_norm(cues[index-1].text),
                    "GOLD_UNTRACEABLE_OR_INVENTED_ORIGINAL_QUOTE")
            indices.append(index)
        require(indices==sorted(set(indices)),
                "GOLD_CUE_IDS_NOT_ORDERED_UNIQUE")
        frame=claim["financial_frame"]
        require(type(frame) is dict and set(frame)==FRAME_FIELDS,
                "GOLD_FINANCIAL_FRAME_SCHEMA_INVALID")
        require(frame["modality"] in MODALITIES,
                "GOLD_FINANCIAL_MODALITY_INVALID")
    return {
        "schema":"IRE_GOLD_FORMAL_AUDIT_V1",
        "source_sha256":source_sha,
        "source_cues":len(cues),
        "gold_atomic_claim_count":len(claims),
        "gold_critical_claim_count":sum(
            x["financial_importance"]=="CRITICAL" for x in claims),
        "sealed_gold_sha256":digest_json(gold),
        "source_citations_formally_valid":True,
        "human_reviewer_identity_independently_verified":False,
        "reviewer_blindness_independently_verified":False,
        "financial_gold_completeness_independently_verified":False,
    }


def _wilson(success: int,denominator: int,z: float=1.95996398454):
    if denominator==0:
        return None
    p=success/denominator
    zz=z*z
    center=(p+zz/(2*denominator))/(1+zz/denominator)
    bound=z*math.sqrt((p*(1-p)+zz/(4*denominator))/
                      denominator)/(1+zz/denominator)
    return {"lower":round(max(0,center-bound),6),
            "upper":round(min(1,center+bound),6)}


def measure_blind_performance(
    raw: bytes,source_sha: str,video_id: str,
    gold: dict,predicted: dict,matching: dict
) -> dict:
    gold_audit=validate_blind_gold(raw,source_sha,video_id,gold)
    require(type(predicted) is dict and predicted.get("schema")=="IRE_PROPOSALS_V1"
            and predicted.get("source_sha256")==source_sha
            and predicted.get("video_id")==video_id
            and type(predicted.get("claims")) is list,
            "BLIND_EVAL_PREDICTION_IDENTITY_INVALID")
    # Import locally: preserve full upstream source-link and cue-census gate.
    from .claims import validate_annotations
    validate_annotations(raw,source_sha,video_id,predicted)
    require(type(matching) is dict and set(matching)=={
        "schema","video_id","source_sha256","sealed_gold_sha256",
        "prediction_manifest_sha256","alignment_reviewer_id",
        "model_results_hidden_during_gold_creation",
        "pairs","all_predictions_and_gold_compared"},
        "BLIND_ALIGNMENT_SCHEMA_INVALID")
    require(matching["schema"]=="IRE_BLIND_ALIGNMENT_V1"
            and matching["source_sha256"]==source_sha
            and matching["video_id"]==video_id
            and matching["sealed_gold_sha256"]==
                gold_audit["sealed_gold_sha256"]
            and matching["prediction_manifest_sha256"]==
                digest_json(predicted)
            and matching["model_results_hidden_during_gold_creation"] is True
            and matching["all_predictions_and_gold_compared"] is True,
            "BLIND_ALIGNMENT_HASH_OR_ATTESTATION_MISMATCH")
    reviewer=matching["alignment_reviewer_id"]
    ids={r["reviewer_id"] for r in gold["reviewers"]}
    require(type(reviewer) is str and
            re.fullmatch(r"[A-Za-z0-9_-]{3,48}",reviewer) and
            reviewer not in ids,
            "BLIND_ALIGNMENT_INDEPENDENT_REVIEWER_REQUIRED")
    pairs=matching["pairs"]
    require(type(pairs) is list,"BLIND_ALIGNMENT_PAIRS_INVALID")
    pred_ids={c["claim_id"] for c in predicted["claims"]}
    gold_ids={c["gold_id"] for c in gold["claims"]}
    require(len(pred_ids)==len(predicted["claims"])
            and len(gold_ids)==len(gold["claims"]),
            "BLIND_EVAL_DUPLICATE_ATOM_IDS")
    seen_pred=set();seen_gold=set();exact=[];partial=[]
    for pair in pairs:
        require(type(pair) is dict and set(pair)=={
            "predicted_claim_id","gold_id","semantic_verdict",
            "frame_field_verdicts"},
            "BLIND_PAIR_SCHEMA_INVALID")
        pid=pair["predicted_claim_id"]
        gid=pair["gold_id"]
        require(pid in pred_ids and gid in gold_ids
                and pid not in seen_pred and gid not in seen_gold,
                "BLIND_PAIR_INVALID_ID_OR_DOUBLE_MATCH")
        seen_pred.add(pid);seen_gold.add(gid)
        verdict=pair["semantic_verdict"]
        require(verdict in VERDICTS,"BLIND_PAIR_VERDICT_INVALID")
        fields=pair["frame_field_verdicts"]
        require(type(fields) is dict and set(fields)==FRAME_FIELDS
                and set(fields.values())<=FIELD_VERDICTS,
                "BLIND_FRAME_FIELD_VERDICTS_INVALID")
        if verdict=="EXACT":
            # Critical scope errors turn an apparent exact match into partial.
            require(all(fields[field]=="CORRECT" for field in (
                "financial_event","action","modality","conditions",
                "exceptions","measurements")),
                "BLIND_EXACT_ATOM_WITH_CORE_FRAME_ERROR")
            exact.append(pair)
        elif verdict=="PARTIAL":
            partial.append(pair)
    true_positives=len(exact)
    pred_n=len(pred_ids)
    gold_n=len(gold_ids)
    tp_ids={p["gold_id"] for p in exact}
    critical_gold={x["gold_id"] for x in gold["claims"]
                   if x["financial_importance"]=="CRITICAL"}
    c_tp=len(tp_ids & critical_gold)
    c_n=len(critical_gold)
    field_totals={}
    for field in sorted(FRAME_FIELDS):
        right=sum(p["frame_field_verdicts"][field]=="CORRECT"
                  for p in exact)
        known=sum(p["frame_field_verdicts"][field]!="UNDETERMINED"
                  for p in exact)
        field_totals[field]={
            "correct":right,"determinate":known,
            "accuracy":round(right/known,6) if known else None}
    return {
        "schema":"IRE_BLIND_MEASUREMENT_V1",
        "source_sha256":source_sha,
        "sealed_gold_sha256":gold_audit["sealed_gold_sha256"],
        "prediction_manifest_sha256":digest_json(predicted),
        "gold_atom_count":gold_n,
        "predicted_atom_count":pred_n,
        "strict_exact_matches":true_positives,
        "partial_related_pairs":len(partial),
        "unmatched_predictions_or_nonexact":pred_n-true_positives,
        "unmatched_gold_or_nonexact":gold_n-true_positives,
        "strict_precision":round(true_positives/pred_n,6) if pred_n else None,
        "strict_recall":round(true_positives/gold_n,6) if gold_n else None,
        "precision_wilson_95":_wilson(true_positives,pred_n),
        "recall_wilson_95":_wilson(true_positives,gold_n),
        "critical_gold_count":c_n,
        "critical_exact_matches":c_tp,
        "critical_recall":round(c_tp/c_n,6) if c_n else None,
        "exact_match_frame_accuracy":field_totals,
        "historical_research_gold_used":False,
        "formal_gold_and_alignment_hash_valid":True,
        "external_human_reviewer_identity_verified":False,
        "true_blind_independence_proven":False,
        "research_complete":False,
        "production_release":"BLOCKED_PENDING_EXTERNAL_BLIND_ATTESTATION"
    }


def main() -> int:
    """Offline blind gold evaluation. Operates only on private input paths."""
    import argparse
    from .cli import private_file,write_new_private_report
    parser=argparse.ArgumentParser(description="Independent source-only blind claim evaluation")
    parser.add_argument("--original-srt",required=True)
    parser.add_argument("--source-sha256",required=True)
    parser.add_argument("--video-id",required=True)
    parser.add_argument("--private-blind-gold",required=True)
    parser.add_argument("--private-model-proposals",required=True)
    parser.add_argument("--private-adjudicated-matches",required=True)
    parser.add_argument("--private-report",required=True)
    args=parser.parse_args()
    try:
        raw=private_file(args.original_srt).read_bytes()
        gold=json.loads(private_file(args.private_blind_gold).read_text(encoding="utf-8"))
        proposed=json.loads(private_file(args.private_model_proposals).read_text(encoding="utf-8"))
        matched=json.loads(private_file(args.private_adjudicated_matches).read_text(encoding="utf-8"))
        result=measure_blind_performance(
            raw,args.source_sha256,args.video_id,gold,proposed,matched)
        write_new_private_report(args.private_report,result)
    except (ValueError,KeyError,TypeError,OSError,UnicodeError):
        # A private annotation or parse failure may contain user text: never
        # echo arbitrary exceptions or text from private assessment files.
        print(json.dumps({"gate":"FAILED_CLOSED",
                          "error_code":"BLIND_MEASUREMENT_INPUT_OR_VALIDATION_FAILED"}))
        return 3
    print(json.dumps({
        "schema":result["schema"],
        "gold_atom_count":result["gold_atom_count"],
        "predicted_atom_count":result["predicted_atom_count"],
        "strict_precision":result["strict_precision"],
        "strict_recall":result["strict_recall"],
        "critical_recall":result["critical_recall"],
        "production_release":result["production_release"],
        "independent_human_identity_proven":False,
        "private_result_saved":True
    },ensure_ascii=False,sort_keys=True))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
