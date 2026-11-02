"""IRE V3 source-grounded, append-only cross-video relation review.

Candidate similarity is NOT semantic adjudication. Current-chat reasoning may
record a source-linked hypothesis; neither the ledger nor its reviewer flags
certify financial truth or independent human review. Previously recorded events
remain immutable and separately versioned when new videos arrive.
"""
from __future__ import annotations

from datetime import date
import json
import os
import re

from .checkpoint import safe_private_directory
from .cli import private_file
from .knowledge import validate_knowledge
from .source import require, sha256, text_norm, DIGEST

SCHEMA = "IRE_V3_RELATION_REVIEW_LEDGER_V1"
LABELS = frozenset({
    "RESTATEMENT", "ADDITIONAL_CONDITION", "POSSIBLE_CONTRADICTION",
    "TEMPORAL_CHANGE", "JURISDICTION_DIFFERENCE", "NUMERIC_DIFFERENCE",
    "RELATED_DISTINCT", "UNRELATED", "UNRESOLVED",
})


def _bytes(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(data):
    return sha256(_bytes(data))


def _sealed(body):
    return {**body, "snapshot_sha256": _digest(body)}


def empty_relation_reviews(knowledge):
    validate_knowledge(knowledge)
    return _sealed({
        "schema": SCHEMA,
        "knowledge_snapshot_sha256": knowledge["snapshot_sha256"],
        "version": 0,
        "parent_sha256": None,
        "reviews": [],
        "discovered_candidates": [],
        "reviewer_mode": "CURRENT_CHATGPT_CONVERSATION",
        "independent_human_truth_approved": False,
        "auto_merged_claims": 0,
    })


def _support_quote(claim, quote):
    require(type(quote) is str and 2 <= len(quote) <= 2000 and
            any(text_norm(quote) in text_norm(r["quote"])
                for r in claim["source_refs"]),
            "V3_RELATION_QUOTE_NOT_IN_CITED_ORIGINAL")


def validate_relation_reviews(ledger, knowledge):
    validate_knowledge(knowledge)
    require(type(ledger) is dict and set(ledger) == {
        "schema", "knowledge_snapshot_sha256", "version", "parent_sha256",
        "reviews", "discovered_candidates", "reviewer_mode", "independent_human_truth_approved",
        "auto_merged_claims", "snapshot_sha256"
    } and ledger["schema"] == SCHEMA and
            ledger["knowledge_snapshot_sha256"] == knowledge["snapshot_sha256"] and
            ledger["reviewer_mode"] == "CURRENT_CHATGPT_CONVERSATION" and
            ledger["independent_human_truth_approved"] is False and
            ledger["auto_merged_claims"] == 0 and
            type(ledger["version"]) is int and ledger["version"] >= 0 and
            type(ledger["reviews"]) is list and
            type(ledger["discovered_candidates"]) is list and
            len(ledger["reviews"]) + len(ledger["discovered_candidates"]) == ledger["version"] and
            (ledger["parent_sha256"] is None or
             (type(ledger["parent_sha256"]) is str and
              DIGEST.fullmatch(ledger["parent_sha256"]))) and
            _digest({k:v for k,v in ledger.items() if k != "snapshot_sha256"}) ==
                ledger["snapshot_sha256"], "V3_RELATION_LEDGER_INVALID")
    candidates = {r["relation_id"]:r for r in knowledge["relation_candidates"]}
    claims = {r["global_claim_id"]:r for r in knowledge["claims"]}
    order={x["video_id"]:i for i,x in enumerate(knowledge["source_register"])}
    for n, record in enumerate(ledger["discovered_candidates"],1):
        require(type(record) is dict and set(record)=={
            "relation_id","ordinal","old_claim_id","new_claim_id",
            "old_quote","new_quote","discovery_explanation",
            "reviewer_mode","independent_human_gold"} and
            record["ordinal"]==n and
            record["relation_id"] not in candidates and
            record["old_claim_id"] in claims and
            record["new_claim_id"] in claims and
            record["old_claim_id"]!=record["new_claim_id"] and
            record["reviewer_mode"]=="CURRENT_CHATGPT_CONVERSATION" and
            record["independent_human_gold"] is False and
            type(record["discovery_explanation"]) is str and
            20<=len(record["discovery_explanation"])<=4000 and
            record["relation_id"]=="R"+sha256((record["old_claim_id"]+"|"+
                            record["new_claim_id"]).encode("utf-8"))[:24] and
            order[claims[record["old_claim_id"]]["video_id"]]<
            order[claims[record["new_claim_id"]]["video_id"]],
            "V3_RELATION_DISCOVERY_EVENT_INVALID")
        _support_quote(claims[record["old_claim_id"]],record["old_quote"])
        _support_quote(claims[record["new_claim_id"]],record["new_quote"])
        candidates[record["relation_id"]]=record
    seen = set()
    for n, row in enumerate(ledger["reviews"], 1):
        require(type(row) is dict and set(row) == {
            "review_id", "ordinal", "relation_id", "old_claim_id",
            "new_claim_id", "old_quote", "new_quote", "relation_label",
            "source_first_explanation", "reviewed_as_of", "reviewer_mode",
            "independent_review_attested", "financial_truth_approved"
        }, "V3_RELATION_REVIEW_EVENT_SCHEMA_INVALID")
        rid = row["relation_id"]
        require(rid in candidates and rid not in seen and
                row["ordinal"] == n and
                row["old_claim_id"] == candidates[rid]["old_claim_id"] and
                row["new_claim_id"] == candidates[rid]["new_claim_id"] and
                row["relation_label"] in LABELS and
                type(row["source_first_explanation"]) is str and
                20 <= len(row["source_first_explanation"]) <= 4000 and
                type(row["reviewed_as_of"]) is str and
                date.fromisoformat(row["reviewed_as_of"]).isoformat() ==
                    row["reviewed_as_of"] and
                row["reviewer_mode"] == "CURRENT_CHATGPT_CONVERSATION" and
                row["independent_review_attested"] is False and
                row["financial_truth_approved"] is False,
                "V3_RELATION_REVIEW_UNSAFE_OR_UNREGISTERED")
        old,new = claims[row["old_claim_id"]],claims[row["new_claim_id"]]
        require(old["video_id"] != new["video_id"],
                "V3_RELATION_NOT_CROSS_VIDEO")
        _support_quote(old, row["old_quote"])
        _support_quote(new, row["new_quote"])
        body = {k:v for k,v in row.items() if k != "review_id"}
        require(row["review_id"] == "J" + _digest(body)[:24],
                "V3_RELATION_REVIEW_ID_TAMPERED")
        seen.add(rid)
    return {
        "candidate_count": len(candidates),
        "reviewed_count": len(seen),
        "discovered_candidate_count":len(ledger["discovered_candidates"]),
        "pending_count": len(candidates)-len(seen),
        "independent_human_verified_relations": 0,
    }


def discover_relation_candidate(ledger, knowledge, submission):
    """Register a missed source-backed pair without rewriting knowledge facts."""
    validate_relation_reviews(ledger, knowledge)
    require(type(submission) is dict and set(submission)=={
        "schema","old_claim_id","new_claim_id","old_quote","new_quote",
        "discovery_explanation"
    } and submission["schema"]=="IRE_V3_RELATION_DISCOVERY_SUBMISSION_V1",
            "V3_RELATION_DISCOVERY_SUBMISSION_INVALID")
    body={"ordinal":len(ledger["discovered_candidates"])+1,
          **{k:v for k,v in submission.items() if k!="schema"},
          "reviewer_mode":"CURRENT_CHATGPT_CONVERSATION",
          "independent_human_gold":False}
    body["relation_id"]="R"+sha256((body["old_claim_id"]+"|"+
                                    body["new_claim_id"]).encode("utf-8"))[:24]
    current={k:v for k,v in ledger.items() if k!="snapshot_sha256"}
    updated=_sealed({**current,"version":ledger["version"]+1,
                    "parent_sha256":ledger["snapshot_sha256"],
                    "discovered_candidates":ledger["discovered_candidates"]+[body]})
    validate_relation_reviews(updated,knowledge)
    return updated


def submit_relation_review(ledger, knowledge, submission):
    validate_relation_reviews(ledger, knowledge)
    require(type(submission) is dict and set(submission) == {
        "schema", "relation_id", "old_claim_id", "new_claim_id",
        "old_quote", "new_quote", "relation_label",
        "source_first_explanation", "reviewed_as_of"
    } and submission["schema"] == "IRE_V3_RELATION_REVIEW_SUBMISSION_V1",
            "V3_RELATION_SUBMISSION_INVALID")
    body = {
        "ordinal": len(ledger["reviews"]) + 1,
        **{k:v for k,v in submission.items() if k != "schema"},
        "reviewer_mode": "CURRENT_CHATGPT_CONVERSATION",
        "independent_review_attested": False,
        "financial_truth_approved": False,
    }
    event = {**body, "review_id": "J"+_digest(body)[:24]}
    current = {k:v for k,v in ledger.items() if k != "snapshot_sha256"}
    updated = _sealed({**current, "version": ledger["version"]+1,
                       "parent_sha256": ledger["snapshot_sha256"],
                       "reviews": ledger["reviews"] + [event]})
    validate_relation_reviews(updated, knowledge)
    return updated


def rebase_relation_reviews(ledger, old_knowledge, new_knowledge):
    """Carry forward exact old pair IDs only; do not relabel new pairs."""
    validate_relation_reviews(ledger, old_knowledge)
    validate_knowledge(new_knowledge)
    require(set(x["global_claim_id"] for x in old_knowledge["claims"]) <=
            set(x["global_claim_id"] for x in new_knowledge["claims"]),
            "V3_RELATION_REBASE_MISSING_SOURCE_CLAIM")
    old_pairs = {r["relation_id"]:r for r in old_knowledge["relation_candidates"]}
    next_pairs = {r["relation_id"]:r for r in new_knowledge["relation_candidates"]}
    require(all(rid in next_pairs and next_pairs[rid] == row
                for rid,row in old_pairs.items()),
            "V3_RELATION_REBASE_CHANGED_PRIOR_CANDIDATE")
    base = {k:v for k,v in ledger.items() if k != "snapshot_sha256"}
    updated = _sealed({**base,
        "knowledge_snapshot_sha256": new_knowledge["snapshot_sha256"],
        "parent_sha256": ledger["snapshot_sha256"]})
    validate_relation_reviews(updated, new_knowledge)
    return updated


def relation_review_context(ledger,knowledge,claim_ids):
    status=validate_relation_reviews(ledger,knowledge)
    relevant=set(claim_ids)
    candidates=[x for x in
                (knowledge["relation_candidates"]+ledger["discovered_candidates"])
                if x["old_claim_id"] in relevant or x["new_claim_id"] in relevant]
    reviews={x["relation_id"]:x for x in ledger["reviews"]}
    return {"schema":"IRE_V3_RELATION_CONTEXT_V1",**status,
        "relevant_candidate_count":len(candidates),
        "relevant_reviews":[reviews[x["relation_id"]] for x in candidates
                            if x["relation_id"] in reviews],
        "unreviewed_relation_ids":[x["relation_id"] for x in candidates
                                   if x["relation_id"] not in reviews],
        "semantic_adjudication_independent":False,
        "approved_integrated_facts":0}


def save_private_relation_reviews(ledger,knowledge,directory):
    validate_relation_reviews(ledger,knowledge)
    root=safe_private_directory(directory)
    target=root/("ire_relation_v"+str(ledger["version"]).zfill(6)+"_"+
                 ledger["snapshot_sha256"][:16]+".json")
    raw=_bytes(ledger)
    fd=os.open(target, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd,"wb") as stream:
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return str(target)


def main():
    import argparse
    from .knowledge import read_private_snapshot
    parser=argparse.ArgumentParser(description="Source-grounded relation candidates, not certified truth")
    parser.add_argument("operation",choices=["init","discover","assess","rebase","status"])
    parser.add_argument("--private-knowledge-snapshot",required=True)
    parser.add_argument("--private-ledger")
    parser.add_argument("--private-old-knowledge-snapshot")
    parser.add_argument("--private-review")
    parser.add_argument("--private-dir")
    args=parser.parse_args()
    try:
        knowledge=read_private_snapshot(args.private_knowledge_snapshot)
        if args.operation=="init":
            require(args.private_dir and not args.private_ledger,
                    "V3_RELATION_INIT_ARGS_INVALID")
            updated=empty_relation_reviews(knowledge)
        else:
            require(args.private_ledger,"V3_RELATION_LEDGER_REQUIRED")
            ledger=json.loads(private_file(args.private_ledger).read_text(encoding="utf-8"))
            if args.operation in ("assess","discover"):
                require(args.private_review and args.private_dir,
                        "V3_RELATION_ASSESS_ARGS_REQUIRED")
                submission=json.loads(private_file(args.private_review).read_text(encoding="utf-8"))
                updated=(submit_relation_review(ledger,knowledge,submission)
                         if args.operation=="assess" else
                         discover_relation_candidate(ledger,knowledge,submission))
            elif args.operation=="rebase":
                require(args.private_old_knowledge_snapshot and args.private_dir,
                        "V3_RELATION_REBASE_ARGS_REQUIRED")
                prior=read_private_snapshot(args.private_old_knowledge_snapshot)
                updated=rebase_relation_reviews(ledger,prior,knowledge)
            else:
                status=validate_relation_reviews(ledger,knowledge)
                print(json.dumps({"schema":SCHEMA,**status,
                                  "financial_facts_approved":0},sort_keys=True))
                return 2
        saved=save_private_relation_reviews(updated,knowledge,args.private_dir)
        status=validate_relation_reviews(updated,knowledge)
        print(json.dumps({"schema":SCHEMA,"snapshot_sha256":updated["snapshot_sha256"],
                          "private_path":saved,**status,
                          "financial_facts_approved":0},sort_keys=True))
        return 0 if args.operation=="init" else 2
    except (ValueError,KeyError,TypeError,UnicodeError,OSError):
        print(json.dumps({"schema":"IRE_V3_RELATION_ERROR","status":"FAILED_CLOSED"}))
        return 3


if __name__=="__main__":
    raise SystemExit(main())