"""Pre-registered, source-pinned relation retrieval benchmark (V3 P0-D).

This computes recall@K/precision@K from a separate supplied source-first
adjudication and compares lexical-only vs financial-alias candidate ranking.
It cannot independently establish the claimed reviewers' identities, blind
procedure or completeness. Its results must NEVER be a release certificate.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import re

from .cli import private_file
from .checkpoint import safe_private_directory
from .knowledge import validate_knowledge, _overlap_score
from .retrieval import _features
from .source import require, sha256, text_norm

SCHEMA="IRE_V3_RELATION_BLIND_GOLD_V1"
TOP_K=(1,3,5,10)
RELATIONS=frozenset({"RESTATEMENT","CONTRADICTION","SCOPE_CHANGE",
                      "TEMPORAL_CHANGE","NUMERIC_VARIANT","COMPLEMENT"})


def _bytes(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,
                      separators=(",",":"),allow_nan=False).encode("utf-8")


def _strict_quote(claim,quote):
    require(type(quote) is str and len(quote)>=2 and
            any(text_norm(quote) in text_norm(x["quote"])
                for x in claim["source_refs"]),
            "V3_RELATION_GOLD_UNCITED_QUOTE")


def validate_relation_gold(knowledge,gold):
    validate_knowledge(knowledge)
    require(type(gold) is dict and set(gold)=={
        "schema","knowledge_snapshot_sha256","source_first_only",
        "predictions_unseen_during_gold","reviewers","adjudicator_id",
        "gold_sealed_at_utc","complete_candidate_universe_attested","queries"
    } and gold["schema"]==SCHEMA and
            gold["knowledge_snapshot_sha256"]==knowledge["snapshot_sha256"] and
            gold["source_first_only"] is True and
            gold["predictions_unseen_during_gold"] is True and
            gold["complete_candidate_universe_attested"] is True,
            "V3_RELATION_GOLD_CONTRACT_INVALID")
    reviewers=gold["reviewers"]
    require(type(reviewers) is list and len(reviewers)==2 and
            all(type(r) is dict and set(r)=={
                "reviewer_id","source_only_review_sha256",
                "independent_from_model_attestation"} and
                type(r["reviewer_id"]) is str and
                re.fullmatch(r"[A-Za-z0-9_-]{3,48}",r["reviewer_id"]) and
                re.fullmatch(r"[0-9a-f]{64}",r["source_only_review_sha256"]) and
                r["independent_from_model_attestation"] is True
                for r in reviewers), "V3_RELATION_GOLD_REVIEWERS_INVALID")
    rid={r["reviewer_id"] for r in reviewers}
    require(len(rid)==2 and type(gold["adjudicator_id"]) is str and
            re.fullmatch(r"[A-Za-z0-9_-]{3,48}",gold["adjudicator_id"]) and
            gold["adjudicator_id"] not in rid,
            "V3_RELATION_GOLD_ADJUDICATOR_NOT_SEPARATE")
    try:
        stamp=datetime.fromisoformat(gold["gold_sealed_at_utc"].replace("Z","+00:00"))
        require(stamp.tzinfo is not None and stamp.utcoffset().total_seconds()==0,
                "V3_RELATION_GOLD_SEAL_TIME_INVALID")
    except (ValueError,TypeError,AttributeError):
        raise ValueError("V3_RELATION_GOLD_SEAL_TIME_INVALID") from None
    claims={x["global_claim_id"]:x for x in knowledge["claims"]}
    source_order={x["video_id"]:i for i,x in enumerate(knowledge["source_register"])}
    seen=set()
    queries=gold["queries"]
    require(type(queries) is list and 1<=len(queries)<=10000,
            "V3_RELATION_GOLD_QUERY_COUNT_INVALID")
    for row in queries:
        require(type(row) is dict and set(row)=={
            "new_claim_id","new_source_quote","relevant_old_claims"
        } and row["new_claim_id"] in claims and
                row["new_claim_id"] not in seen and
                type(row["relevant_old_claims"]) is list,
                "V3_RELATION_GOLD_QUERY_INVALID")
        seen.add(row["new_claim_id"])
        new=claims[row["new_claim_id"]]
        _strict_quote(new,row["new_source_quote"])
        present=set()
        for old in row["relevant_old_claims"]:
            require(type(old) is dict and set(old)=={
                "old_claim_id","old_source_quote","relation_type"
            } and old["old_claim_id"] in claims and
                    old["old_claim_id"] not in present and
                    old["relation_type"] in RELATIONS,
                    "V3_RELATION_GOLD_PAIR_INVALID")
            item=claims[old["old_claim_id"]]
            require(source_order[item["video_id"]] <
                    source_order[new["video_id"]],
                    "V3_RELATION_GOLD_PAIR_NOT_PRIOR_VIDEO")
            _strict_quote(item,old["old_source_quote"])
            present.add(old["old_claim_id"])
    return {"query_count":len(queries),
            "positive_pair_count":sum(len(q["relevant_old_claims"]) for q in queries),
            "gold_sha256":sha256(_bytes(gold)),
            "human_reviewer_identity_independently_verified":False,
            "gold_blindness_independently_verified":False,
            "complete_universe_independently_verified":False}


def _baseline_overlap(a,b):
    ta=_features(a["proposition"])[0]
    tb=_features(b["proposition"])[0]
    score=len(ta&tb)/len(ta|tb) if ta|tb else 0.0
    for field,weight in (("product",0.65),("financial_event",0.7),
                         ("action",0.2),("object",0.2)):
        l=a["frame"].get(field);r=b["frame"].get(field)
        if (isinstance(l,str) and isinstance(r,str) and l and r and
                text_norm(l).lower()==text_norm(r).lower()):
            score+=weight
    return round(score,5)


def _rank(query,previous,with_semantics):
    scorer=_overlap_score if with_semantics else _baseline_overlap
    return [old["global_claim_id"] for old in sorted(
        previous,key=lambda old:(-scorer(query,old),old["global_claim_id"]))]


def evaluate_relation_retrieval(knowledge,gold):
    audit=validate_relation_gold(knowledge,gold)
    claims={x["global_claim_id"]:x for x in knowledge["claims"]}
    order={x["video_id"]:i for i,x in enumerate(knowledge["source_register"])}
    totals={mode:{k:{"hits":0,"relevant":0,"returned":0}
                  for k in TOP_K} for mode in ("lexical_baseline","financial_alias")}
    by_query=[]
    for question in gold["queries"]:
        new=claims[question["new_claim_id"]]
        previous=[c for c in knowledge["claims"]
                  if order[c["video_id"]]<order[new["video_id"]]]
        expected={p["old_claim_id"] for p in question["relevant_old_claims"]}
        outcome={"query_id":new["global_claim_id"],"relevant_count":len(expected)}
        for mode,semantics in (("lexical_baseline",False),("financial_alias",True)):
            ranked=_rank(new,previous,semantics)
            outcome[mode]={}
            for k in TOP_K:
                at=ranked[:k]
                hits=len(set(at)&expected)
                totals[mode][k]["hits"]+=hits
                totals[mode][k]["relevant"]+=len(expected)
                totals[mode][k]["returned"]+=len(at)
                outcome[mode][str(k)]={"hits":hits,"retrieved":len(at)}
        by_query.append(outcome)
    results={}
    for mode,cases in totals.items():
        results[mode]={}
        for k,counts in cases.items():
            results[mode][str(k)]={
                "recall_at_k":round(counts["hits"]/counts["relevant"],6)
                    if counts["relevant"] else None,
                "precision_at_k":round(counts["hits"]/counts["returned"],6)
                    if counts["returned"] else None,
                **counts}
    return {"schema":"IRE_V3_RELATION_RETRIEVAL_EVALUATION_V1",**audit,
            "knowledge_snapshot_sha256":knowledge["snapshot_sha256"],
            "results":results,"queries":by_query,
            "gold_is_new_source_only":True,
            "certified_real_world_recall":False,
            "independent_validation_of_reviewer_attestations":False,
            "release_gate_approved":False}


def main():
    import argparse
    from .knowledge import read_private_snapshot
    parser=argparse.ArgumentParser(description="Blind-relation candidate retrieval benchmark")
    parser.add_argument("operation",choices=["evaluate"])
    parser.add_argument("--private-knowledge-snapshot",required=True)
    parser.add_argument("--private-gold",required=True)
    parser.add_argument("--private-report-dir",required=True)
    args=parser.parse_args()
    try:
        knowledge=read_private_snapshot(args.private_knowledge_snapshot)
        gold=json.loads(private_file(args.private_gold).read_text(encoding="utf-8"))
        report=evaluate_relation_retrieval(knowledge,gold)
        encoded=_bytes(report)
        digest=sha256(encoded)
        root=safe_private_directory(args.private_report_dir)
        path=root/("ire_relation_eval_"+digest[:24]+".json")
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        try:
            with os.fdopen(fd,"wb") as stream:
                stream.write(encoded);stream.flush();os.fsync(stream.fileno())
        except Exception:
            path.unlink(missing_ok=True)
            raise
        print(json.dumps({"schema":report["schema"],
                          "query_count":report["query_count"],
                          "gold_sha256":report["gold_sha256"],
                          "report_sha256":digest,
                          "private_report_path":str(path),
                          "certified_real_world_recall":False},sort_keys=True))
        return 2
    except (ValueError,KeyError,TypeError,UnicodeError,OSError):
        print(json.dumps({"schema":"IRE_V3_RELATION_EVAL_ERROR",
                          "status":"FAILED_CLOSED"}))
        return 3


if __name__=="__main__":
    raise SystemExit(main())