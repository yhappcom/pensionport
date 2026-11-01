"""V2 post-seal legacy study DIFFERENCE REVIEW, never source gold or fact import.

Old research claims must NOT influence new original interpretation. After
new IRE sources and claims are frozen, a separately supplied legacy registry
can be compared for potential missed topics and changed interpretations.
No legacy proposition or text appears in the returned advisory knowledge.
"""
from __future__ import annotations
import json
import re

from .source import require,sha256,VIDEO
from .knowledge import validate_knowledge
from .retrieval import _features

MAX_LEGACY=300_000

def _similarity(left:str,right:str) -> float:
    wa,ca=_features(left)
    wb,cb=_features(right)
    words=len(wa&wb)/len(wa|wb) if wa|wb else 0.0
    parts=len(ca&cb)/len(ca|cb) if ca|cb else 0.0
    return round(0.65*words+0.35*parts,5)


def post_seal_legacy_delta(new_ire_knowledge:dict,
                           legacy_manifest:dict, top_k:int=5) -> dict:
    """Only public-style IDs and hashes leave this segregated comparison.

    Actual historical claim values may appear ONLY in this tool's private
    input, not in the new IRE knowledge ledger or blind gold.
    """
    validate_knowledge(new_ire_knowledge)
    require(new_ire_knowledge["version"]>=1,
            "LEGACY_COMPARISON_REQUIRES_FROZEN_NEW_IRE_WORK")
    require(type(legacy_manifest) is dict and
            set(legacy_manifest)=={"schema","claims"} and
            legacy_manifest["schema"]=="IRE_LEGACY_QUARANTINED_CLAIMS_V1"
            and type(legacy_manifest["claims"]) is list and
            len(legacy_manifest["claims"])<=MAX_LEGACY,
            "LEGACY_QUARANTINE_SCHEMA_INVALID")
    require(type(top_k) is int and 1<=top_k<=15,
            "LEGACY_COMPARISON_TOPK_INVALID")
    sources={x["video_id"] for x in new_ire_knowledge["source_register"]}
    by_video={}
    for c in new_ire_knowledge["claims"]:
        by_video.setdefault(c["video_id"],[]).append(c)
    used=set()
    rows=[]
    covered_new=set()
    legacy_only=0
    for item in legacy_manifest["claims"]:
        require(type(item) is dict and set(item)=={
            "legacy_claim_id","video_id","claim_text","historical_status"
        },"LEGACY_ENTRY_SCHEMA_INVALID")
        legacy_id=item["legacy_claim_id"]
        video=item["video_id"]
        assertion=item["claim_text"]
        require(type(legacy_id) is str and
                re.fullmatch(r"[A-Za-z0-9_-]{1,100}",legacy_id)
                and legacy_id not in used,
                "LEGACY_ENTRY_ID_DUPLICATED_OR_INVALID")
        used.add(legacy_id)
        require(type(video) is str and VIDEO.fullmatch(video)
                and type(assertion) is str and
                5<=len(assertion)<=10000 and
                item["historical_status"]=="LEGACY_NOT_GOLD_UNVERIFIED",
                "LEGACY_UNTRUSTED_STUDY_INPUT_INVALID")
        assert_digest=sha256(assertion.encode("utf-8"))
        if video not in sources:
            rows.append({
                "legacy_claim_id":legacy_id,"original_video_id":video,
                "legacy_assertion_sha256":assert_digest,
                "comparison_status":"NEW_ORIGINAL_NOT_YET_STUDIED",
                "new_ire_candidate_claim_ids":[],
                "historical_claim_text_copied_to_new_knowledge":False
            })
            continue
        scored=sorted((
            (_similarity(assertion,c["proposition"]),c["global_claim_id"])
            for c in by_video.get(video,[])),
            key=lambda x:(-x[0],x[1]))
        matches=[(score,identifier) for score,identifier in scored[:top_k]
                 if score>=0.3]
        if not matches:
            legacy_only+=1
        covered_new.update(x[1] for x in matches)
        rows.append({
            "legacy_claim_id":legacy_id,
            "original_video_id":video,
            "legacy_assertion_sha256":assert_digest,
            "comparison_status":(
                "POST_SEAL_SIMILARITY_REVIEW_ONLY" if matches
                else "POSSIBLE_NEW_IRE_OMISSION_REQUIRES_SOURCE_RECHECK"),
            "new_ire_candidate_claim_ids":[
                {"global_claim_id":ident,"rank":i+1,"lexical_score":score}
                for i,(score,ident) in enumerate(matches)],
            "historical_claim_text_copied_to_new_knowledge":False
        })
    missing_new=[c["global_claim_id"] for c in new_ire_knowledge["claims"]
                 if c["global_claim_id"] not in covered_new]
    return {
        "schema":"IRE_V2_POST_SEAL_LEGACY_DELTA_V1",
        "new_ire_knowledge_snapshot_sha256":
            new_ire_knowledge["snapshot_sha256"],
        "new_originals_sealed_before_legacy_comparison":True,
        "legacy_claims_reviewed":len(rows),
        "legacy_only_cues_for_recheck":legacy_only,
        "new_ire_claims_without_legacy_match":len(missing_new),
        "new_ire_missing_legacy_match_ids":missing_new,
        "legacy_difference_queue":rows,
        "legacy_claims_imported_as_fact_or_gold":0,
        "new_ire_knowledge_modified":False,
        "claim_recall_against_independent_gold":None,
        "historical_comparison_eligible_for_advisory_without_recheck":False
    }


def main() -> int:
    import argparse
    from .cli import private_file,write_new_private_report
    from .knowledge import read_private_snapshot
    parser=argparse.ArgumentParser(description="Post-seal legacy difference queue; never reuse historical claims as new IRE facts")
    parser.add_argument("--private-new-knowledge",required=True)
    parser.add_argument("--private-legacy-manifest",required=True)
    parser.add_argument("--private-difference-report",required=True)
    args=parser.parse_args()
    try:
        current=read_private_snapshot(args.private_new_knowledge)
        old=json.loads(
            private_file(args.private_legacy_manifest).read_text(encoding="utf-8"))
        report=post_seal_legacy_delta(current,old)
        write_new_private_report(args.private_difference_report,report)
    except (ValueError,TypeError,KeyError,OSError,UnicodeError):
        print(json.dumps({"schema":"IRE_V2_LEGACY_DELTA_ERROR",
                          "status":"FAILED_CLOSED"}))
        return 3
    print(json.dumps({
        "schema":report["schema"],
        "comparison_queue_count":report["legacy_claims_reviewed"],
        "possible_omissions_for_source_recheck":report[
            "legacy_only_cues_for_recheck"],
        "imported_historical_fact_count":0,
        "knowledge_modified":False
    },ensure_ascii=False))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
