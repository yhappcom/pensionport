"""Incremental, source-linked IRE knowledge register and advisory retrieval.

This is an ADDITIVE private knowledge archive, not a truth engine.
A new ChatGPT chat-derived video is structurally verified against ORIGINAL SRT,
then joined to PREVIOUS NEW-IRE-ONLY results by global claim identity. Cross-video
similarities, apparent conflicts and time changes are review candidates only.

No imported old study gold, no automatically approved investment advice.
"""
from __future__ import annotations

from datetime import date
import json
import os
from pathlib import Path
import re

from .source import require,sha256,text_norm,VIDEO,DIGEST
from .claims import validate_annotations
from .checkpoint import safe_private_directory
from .retrieval import _features

SCHEMA="IRE_INCREMENTAL_KNOWLEDGE_V1"
MAX_ITEMS=100_000
MAX_RELATIONS=800_000
LIMIT_QUERY=30
REVIEW_PENDING="UNVERIFIED_REVIEW_REQUIRED"


def _bytes(value) -> bytes:
    return json.dumps(value,sort_keys=True,ensure_ascii=False,
                      separators=(",",":"),allow_nan=False).encode("utf-8")


def fingerprint(value) -> str:
    return sha256(_bytes(value))


def empty_knowledge() -> dict:
    return _seal({
        "schema":SCHEMA,
        "version":0,
        "parent_sha256":None,
        "source_register":[],
        "claims":[],
        "relation_candidates":[],
        "validation_scope":"NEW_IRE_ORIGINALS_ONLY",
        "old_research_knowledge_imported":False,
        "independent_human_gold_from_old_study":False,
        "automatic_financial_approvals":0,
        "release":"UNVERIFIED_KNOWLEDGE_NOT_FOR_AUTOMATED_ADVICE",
    })


def _seal(body: dict) -> dict:
    return {**body,"snapshot_sha256":fingerprint(body)}


def validate_knowledge(snapshot: dict) -> None:
    require(type(snapshot) is dict and
            set(snapshot)=={
                "schema","version","parent_sha256","source_register","claims",
                "relation_candidates","validation_scope",
                "old_research_knowledge_imported",
                "independent_human_gold_from_old_study",
                "automatic_financial_approvals","release","snapshot_sha256"
            } and snapshot["schema"]==SCHEMA,
            "KNOWLEDGE_SNAPSHOT_SCHEMA_INVALID")
    digest=snapshot["snapshot_sha256"]
    base={k:v for k,v in snapshot.items() if k!="snapshot_sha256"}
    require(type(digest) is str and DIGEST.fullmatch(digest) and
            fingerprint(base)==digest,"KNOWLEDGE_SNAPSHOT_TAMPERED")
    require(type(snapshot["version"]) is int and snapshot["version"]>=0
            and (snapshot["parent_sha256"] is None or
                 DIGEST.fullmatch(snapshot["parent_sha256"])),
            "KNOWLEDGE_VERSION_CHAIN_INVALID")
    require(snapshot["validation_scope"]=="NEW_IRE_ORIGINALS_ONLY"
            and snapshot["old_research_knowledge_imported"] is False
            and snapshot["independent_human_gold_from_old_study"] is False
            and snapshot["automatic_financial_approvals"]==0
            and snapshot["release"]==
                "UNVERIFIED_KNOWLEDGE_NOT_FOR_AUTOMATED_ADVICE",
            "KNOWLEDGE_LEGACY_IMPORT_OR_APPROVAL_FORBIDDEN")
    sources=snapshot["source_register"]
    claims=snapshot["claims"]
    relations=snapshot["relation_candidates"]
    require(type(sources) is list and type(claims) is list and
            type(relations) is list and
            len(claims)<=MAX_ITEMS and len(relations)<=MAX_RELATIONS,
            "KNOWLEDGE_ITEM_LIMIT_INVALID")
    require(snapshot["version"]==len(sources),
            "KNOWLEDGE_INCREMENTAL_SOURCE_VERSION_MISMATCH")
    source_ids=set()
    for source in sources:
        require(type(source) is dict and set(source)=={
            "video_id","source_sha256","origin_report_sha256",
            "unresolved_source_cues","cues","claim_count"
        } and type(source["video_id"]) is str and
                VIDEO.fullmatch(source["video_id"]) and
                type(source["source_sha256"]) is str and
                DIGEST.fullmatch(source["source_sha256"]) and
                type(source["origin_report_sha256"]) is str and
                DIGEST.fullmatch(source["origin_report_sha256"]),
                "KNOWLEDGE_ORIGINAL_SOURCE_INVALID")
        require(type(source["unresolved_source_cues"]) is int and
                source["unresolved_source_cues"]>=0 and
                type(source["cues"]) is int and source["cues"]>0 and
                source["unresolved_source_cues"]<=source["cues"] and
                type(source["claim_count"]) is int and
                source["claim_count"]>=0,
                "KNOWLEDGE_SOURCE_COUNTS_INVALID")
        key=(source["video_id"],source["source_sha256"])
        require(key not in source_ids,"KNOWLEDGE_SOURCE_ID_DUPLICATE")
        source_ids.add(key)
    ids=set()
    count_by_source={}
    for c in claims:
        require(type(c) is dict and set(c)=={
            "global_claim_id","video_id","source_sha256","original_claim_id",
            "proposition","claim_types","frame","source_refs",
            "knowledge_status","review_stage","evidence_status",
        } and type(c["global_claim_id"]) is str and
                re.fullmatch(r"K[0-9a-f]{24}",c["global_claim_id"]),
                "KNOWLEDGE_CLAIM_SCHEMA_INVALID")
        uid=c["global_claim_id"]
        require(uid not in ids,"KNOWLEDGE_GLOBAL_ID_COLLISION")
        ids.add(uid)
        key=(c["video_id"],c["source_sha256"])
        require(key in source_ids,"KNOWLEDGE_CLAIM_UNREGISTERED_ORIGINAL")
        require(c["knowledge_status"]==REVIEW_PENDING and
                c["review_stage"]=="NEW_IRE_CLAIM_UNREVIEWED" and
                c["evidence_status"]=="INDEPENDENT_SOURCE_NOT_CERTIFIED",
                "KNOWLEDGE_SILENT_FACT_APPROVAL_DENIED")
        require(uid==_global_id(c["video_id"],c["source_sha256"],
                                c["original_claim_id"]),
                "KNOWLEDGE_CLAIM_ID_SOURCE_MISMATCH")
        count_by_source[key]=count_by_source.get(key,0)+1
    for source in sources:
        key=source["video_id"],source["source_sha256"]
        require(count_by_source.get(key,0)==source["claim_count"],
                "KNOWLEDGE_CLAIM_CENSUS_CHANGED")
    relation_ids=set()
    for relation in relations:
        require(type(relation) is dict and set(relation)=={
            "relation_id","old_claim_id","new_claim_id","candidate_type",
            "overlap_score","review_status"} and
            relation["old_claim_id"] in ids and
            relation["new_claim_id"] in ids and
            relation["old_claim_id"]!=relation["new_claim_id"] and
            relation["review_status"]=="PENDING_SEPARATE_ADJUDICATION",
            "KNOWLEDGE_RELATION_NOT_SOURCE_LINKED")
        require(relation["relation_id"] not in relation_ids,
                "KNOWLEDGE_DUPLICATED_RELATION_ID")
        relation_ids.add(relation["relation_id"])


def _global_id(video_id: str,digest: str,claim_id: str) -> str:
    return "K"+sha256((video_id+"|"+digest+"|"+claim_id).encode("utf-8"))[:24]


def _tokens(text: str) -> set[str]:
    return _features(text)[0]


def _relation_type(a: dict,b: dict) -> str:
    left,right=a["frame"],b["frame"]
    if (left["modality"]!=right["modality"]
        and ("NEGATION" in (left["modality"],right["modality"]))):
        return "POSSIBLE_NEGATION_CONFLICT"
    if (left["effective_date"] and right["effective_date"] and
            left["effective_date"]!=right["effective_date"]):
        return "POSSIBLE_TEMPORAL_RULE_CHANGE"
    if left["jurisdiction"]!=right["jurisdiction"]:
        return "POSSIBLE_JURISDICTION_SCOPE_CHANGE"
    if (left["conditions"]!=right["conditions"] or
            left["exceptions"]!=right["exceptions"]):
        return "POSSIBLE_CONDITION_OR_EXCEPTION_COMPLEMENT"
    if left["measurements"]!=right["measurements"]:
        return "POSSIBLE_NUMERIC_VARIATION"
    return "POSSIBLE_RESTATEMENT_OR_SUPPORT"


def _overlap_score(a: dict,b: dict) -> float:
    av,bv=a["frame"],b["frame"]
    words1=_tokens(a["proposition"])
    words2=_tokens(b["proposition"])
    lexical=len(words1 & words2)/len(words1 | words2) if words1 | words2 else 0.0
    result=lexical
    for field,weight in (("product",0.65),("financial_event",0.7),
                         ("action",0.2),("object",0.2)):
        if av[field] is not None and bv[field] is not None and (
                text_norm(av[field]).lower()==text_norm(bv[field]).lower()):
            result+=weight
    return round(result,5)


def _cross_video_candidates(new_claims:list,old_claims:list,
                            top_k:int=8) -> list[dict]:
    """Rank *possible* cross-video relations, never label them as true."""
    require(type(top_k) is int and 1<=top_k<=40,
            "KNOWLEDGE_RETRIEVAL_BUDGET_INVALID")
    candidates=[]
    for new in new_claims:
        ranked=[]
        for old in old_claims:
            if new["source_sha256"]==old["source_sha256"]:
                continue
            score=_overlap_score(new,old)
            if score>=0.5:
                ranked.append((score,old))
        for score,old in sorted(ranked,
            key=lambda item:(-item[0],item[1]["global_claim_id"]))[:top_k]:
            old_id,new_id=old["global_claim_id"],new["global_claim_id"]
            candidates.append({
                "relation_id":"R"+sha256(
                    (old_id+"|"+new_id).encode("utf-8"))[:24],
                "old_claim_id":old_id,
                "new_claim_id":new_id,
                "candidate_type":_relation_type(old,new),
                "overlap_score":score,
                "review_status":"PENDING_SEPARATE_ADJUDICATION"
            })
    return candidates


def ingest_new_video(previous:dict,original_raw:bytes,
                     new_report:dict,top_k:int=8) -> dict:
    """Incremental update, no rewriting or silent integration of old entries."""
    validate_knowledge(previous)
    require(type(new_report) is dict and
            new_report.get("schema")=="IRE_CHAT_RESEARCH_PACKAGE_V1" and
            new_report.get("all_primary_windows_submitted") is True and
            new_report.get("actual_model_api_calls")==0 and
            new_report.get("semantic_origin")==
                "CURRENT_CHAT_CONVERSATION_UNVERIFIED" and
            new_report.get("financial_facts_approved")==0,
            "KNOWLEDGE_REQUIRES_COMPLETE_NEW_CHAT_SOURCE_REPORT")
    proposed=new_report.get("annotations")
    require(type(proposed) is dict,"KNOWLEDGE_NEW_PROPOSALS_MISSING")
    vid=new_report.get("video_id")
    digest=new_report.get("source_sha256")
    require(vid==proposed.get("video_id") and
            digest==proposed.get("source_sha256") and
            sha256(original_raw)==digest,
            "KNOWLEDGE_ORIGINAL_SHA_MISMATCH")
    audit=validate_annotations(original_raw,digest,vid,proposed)
    for old in previous["source_register"]:
        require(old["source_sha256"]!=digest,
                "KNOWLEDGE_REUSED_ORIGINAL_BYTES_NO_DOUBLECOUNT")
        require(old["video_id"]!=vid,
                "KNOWLEDGE_SOURCE_VIDEO_ID_ALREADY_REGISTERED")
    old_claims=previous["claims"]
    fresh=[]
    for claim in proposed["claims"]:
        fresh.append({
            "global_claim_id":_global_id(vid,digest,claim["claim_id"]),
            "video_id":vid,"source_sha256":digest,
            "original_claim_id":claim["claim_id"],
            "proposition":claim["proposition"],
            "claim_types":claim["claim_types"],
            "frame":claim["frame"],
            "source_refs":claim["source_refs"],
            "knowledge_status":REVIEW_PENDING,
            "review_stage":"NEW_IRE_CLAIM_UNREVIEWED",
            "evidence_status":"INDEPENDENT_SOURCE_NOT_CERTIFIED"
        })
    require(len(old_claims)+len(fresh)<=MAX_ITEMS,
            "KNOWLEDGE_ITEM_BUDGET_EXCEEDED")
    rels=_cross_video_candidates(fresh,old_claims,top_k)
    source={
        "video_id":vid,"source_sha256":digest,
        "origin_report_sha256":fingerprint(new_report),
        "unresolved_source_cues":audit["unresolved_cues"],
        "cues":audit["source_cues"],
        "claim_count":len(fresh)
    }
    body={k:v for k,v in previous.items() if k!="snapshot_sha256"}
    body.update({
        "version":previous["version"]+1,
        "parent_sha256":previous["snapshot_sha256"],
        "source_register":previous["source_register"]+[source],
        "claims":old_claims+fresh,
        "relation_candidates":previous["relation_candidates"]+rels,
    })
    output=_seal(body)
    validate_knowledge(output)
    return output


def advisory_research_context(snapshot:dict,question:str,as_of:str,
                              jurisdiction:str|None=None,
                              investor_profile:dict|None=None,
                              top_k:int=8) -> dict:
    """Research context, not financial advice or an asserted truth answer."""
    validate_knowledge(snapshot)
    require(type(question) is str and 5<=len(question)<=2000,
            "ADVISORY_QUESTION_INVALID")
    require(type(as_of) is str and
            date.fromisoformat(as_of).isoformat()==as_of,
            "ADVISORY_AS_OF_DATE_INVALID")
    require(jurisdiction is None or
            (type(jurisdiction) is str and 1<=len(jurisdiction)<=128),
            "ADVISORY_JURISDICTION_INVALID")
    require(investor_profile is None or (
                type(investor_profile) is dict
                and set(investor_profile)<={
                    "investment_horizon_years","risk_tolerance",
                    "tax_residency","account_type","liquidity_needs"}
            ),"ADVISORY_PROFILE_SCHEMA_INVALID")
    require(type(top_k) is int and 1<=top_k<=LIMIT_QUERY,
            "ADVISORY_QUERY_BUDGET_INVALID")
    query_terms=_tokens(question)
    hits=[]
    for claim in snapshot["claims"]:
        text=claim["proposition"]
        frame=claim["frame"]
        score=len(_tokens(text)&query_terms)
        for item in ("product","financial_event","action"):
            val=frame.get(item)
            if val:
                score+=2*len(_tokens(val)&query_terms)
        if score<=0:
            continue
        matched_scope=(jurisdiction is None or
                        frame.get("jurisdiction") in (jurisdiction,None))
        if not matched_scope:
            continue
        hits.append((score,claim))
    hits.sort(key=lambda x:(-x[0],x[1]["global_claim_id"]))
    top=[]
    known={c["global_claim_id"] for _,c in hits[:top_k]}
    for score,claim in hits[:top_k]:
        top.append({
            "global_claim_id":claim["global_claim_id"],
            "original_video_id":claim["video_id"],
            "original_source_sha256":claim["source_sha256"],
            "source_refs":claim["source_refs"],
            "proposition_as_spoken_not_proven":claim["proposition"],
            "frame":claim["frame"],
            "topic_retrieval_score":score,
            "claim_not_independently_factual_verified":True,
            "advisory_basis_approved":False
        })
    open_relations=[x for x in snapshot["relation_candidates"]
                    if x["old_claim_id"] in known or x["new_claim_id"] in known]
    return {
        "schema":"IRE_ADVISORY_EVIDENCE_CONTEXT_V1",
        "question":question,
        "as_of":as_of,
        "jurisdiction":jurisdiction,
        "investor_profile_supplied":investor_profile is not None,
        "snapshot_sha256":snapshot["snapshot_sha256"],
        "knowledge_source_video_count":len(snapshot["source_register"]),
        "knowledge_claim_count":len(snapshot["claims"]),
        "unverified_relevant_claims":top,
        "possible_cross_video_conflicts_or_updates":open_relations[:50],
        "independent_verified_citable_claim_count":0,
        "actionable_recommendations":[],
        "fresh_official_source_reverification_required":True,
        "investor_suitability_reconfirmation_required":True,
        "advisory_output_status":"RESEARCH_CONTEXT_ONLY_NOT_ACTIONABLE_ADVICE",
        "no_previous_research_gold_imported":True,
    }


def save_private_snapshot(snapshot:dict,directory:str) -> str:
    """Append-only immutable versioned snapshots. Never write under Git repo."""
    validate_knowledge(snapshot)
    root=safe_private_directory(directory)
    target=root/("ire_knowledge_v"+str(snapshot["version"]).zfill(6)+
                 "_"+snapshot["snapshot_sha256"][:16]+".json")
    require(not target.exists(),"KNOWLEDGE_SNAPSHOT_OVERWRITE_FORBIDDEN")
    raw=_bytes(snapshot)
    fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        with os.fdopen(fd,"wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return str(target)


def read_private_snapshot(path:str) -> dict:
    from .cli import private_file
    data=json.loads(private_file(path).read_text(encoding="utf-8"))
    validate_knowledge(data)
    return data


def main() -> int:
    import argparse
    from .cli import private_file
    parser=argparse.ArgumentParser(description="Incremental new-IRE investment knowledge and guarded advisory context; no external model API")
    parser.add_argument("operation",choices=["init","ingest","advisory"])
    parser.add_argument("--private-directory",required=True)
    parser.add_argument("--prior-snapshot")
    parser.add_argument("--original-srt")
    parser.add_argument("--chat-final-report")
    parser.add_argument("--question")
    parser.add_argument("--as-of")
    parser.add_argument("--jurisdiction")
    args=parser.parse_args()
    try:
        if args.operation=="init":
            require(not args.prior_snapshot and
                    not args.original_srt and not args.chat_final_report,
                    "KNOWLEDGE_INIT_UNEXPECTED_INPUT")
            state=empty_knowledge()
            path=save_private_snapshot(state,args.private_directory)
            result={"version":0,"snapshot_path":path,"source_count":0,
                    "relation_candidate_count":0,"approved_financial_facts":0}
        elif args.operation=="ingest":
            require(bool(args.prior_snapshot and args.original_srt and
                         args.chat_final_report),
                    "KNOWLEDGE_INGEST_FIELDS_REQUIRED")
            previous=read_private_snapshot(args.prior_snapshot)
            report=json.loads(private_file(
                args.chat_final_report).read_text(encoding="utf-8"))
            raw=private_file(args.original_srt).read_bytes()
            next_state=ingest_new_video(previous,raw,report)
            path=save_private_snapshot(next_state,args.private_directory)
            result={
                "version":next_state["version"],
                "snapshot_path":path,
                "source_count":len(next_state["source_register"]),
                "claim_count":len(next_state["claims"]),
                "cross_video_relation_candidates":len(
                    next_state["relation_candidates"]),
                "automatically_approved_financial_facts":0,
            }
        else:
            require(bool(args.prior_snapshot and args.question and
                         args.as_of),"ADVISORY_INPUTS_REQUIRED")
            state=read_private_snapshot(args.prior_snapshot)
            result=advisory_research_context(
                state,args.question,args.as_of,args.jurisdiction)
            # This is preliminary source-linked research context only.
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 0 if args.operation=="init" else 2
    except (ValueError,KeyError,OSError,TypeError,UnicodeError):
        print(json.dumps({"schema":"IRE_KNOWLEDGE_ERROR_V1",
                          "status":"FAILED_CLOSED"}))
        return 3


if __name__=="__main__":
    raise SystemExit(main())
