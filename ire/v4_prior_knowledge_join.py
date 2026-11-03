"""V4 prior-knowledge bridge: read-only candidate retrieval across canonical and new IRE.
This must not import or fact-approve legacy claims. No external model API.
"""
from __future__ import annotations
import json
import re
from .source import require, sha256
from .v3_semantic_candidates import financial_concepts

INDEX_SCHEMA="IRE_V4_LEGACY_READ_ONLY_CANDIDATE_INDEX_V1"
CROSSWALK_SCHEMA="IRE_V4_LEGACY_CANDIDATE_CROSSWALK_V1"
BLOB=re.compile(r"^[0-9a-f]{40}$")
CLAIM=re.compile(r"^GOMHEE-C[0-9]+$")


def _canonical(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,
                      separators=(",",":"),allow_nan=False).encode("utf-8")


def validate_index(index,expected_source_blobs):
    """Requires caller-pinned Git blob IDs; identity alone is not a fact review."""
    require(type(index) is dict and index.get("schema")==INDEX_SCHEMA and
            type(index.get("items")) is list and
            type(index.get("source_files")) is list,
            "V4_LEGACY_INDEX_INVALID")
    require(index.get("import_into_ire_incremental_knowledge") is False and
            index.get("automatic_merge") is False and
            index.get("approved_financial_facts")==0,
            "V4_LEGACY_SILENT_PROMOTION_DENIED")
    require(type(expected_source_blobs) is dict and expected_source_blobs,
            "V4_LEGACY_BLOB_PIN_REQUIRED")
    pinned={}
    for src in index["source_files"]:
        require(type(src) is dict and type(src.get("path")) is str and
                type(src.get("git_blob_sha")) is str and
                BLOB.fullmatch(src["git_blob_sha"]) and
                src["path"] not in pinned,
                "V4_LEGACY_SOURCE_INVALID")
        pinned[src["path"]]=src["git_blob_sha"]
    require(pinned==expected_source_blobs,"V4_LEGACY_SOURCE_BLOB_CHANGED")
    seen=set()
    for item in index["items"]:
        cid=item.get("legacy_claim_id","")
        require(type(cid) is str and CLAIM.fullmatch(cid) and cid not in seen,
                "V4_LEGACY_ID_INVALID")
        seen.add(cid)
        require(type(item.get("candidate_text")) is str and
                8<=len(item["candidate_text"])<=3500 and
                item.get("state")=="READ_ONLY_LEGACY_PRINCIPLE_NOT_FINANCIAL_FACT_VERIFIED" and
                type(item.get("sources")) is list and bool(item["sources"]),
                "V4_LEGACY_PRINCIPLE_NOT_REVIEW_SAFE")
        for source in item["sources"]:
            require(type(source) is dict and
                    pinned.get(source.get("path"))==source.get("git_blob_sha") and
                    type(source.get("line")) is int and source["line"]>0,
                    "V4_LEGACY_PRINCIPLE_SOURCE_DRIFT")
    require(index.get("unique_principle_count")==len(index["items"]),
            "V4_LEGACY_PRINCIPLE_CENSUS")
    return True


def candidate_crosswalk(draft,index,expected_source_blobs,top_k=3):
    """High-specificity concept candidate discovery, NEVER SAME/CONFLICT judgment."""
    validate_index(index,expected_source_blobs)
    require(type(draft) is dict and
            draft.get("schema")=="IRE_V4_P0_ADAPTIVE_PROVISIONAL_V1" and
            type(draft.get("windows")) is list,
            "V4_LEGACY_SOURCE_BOUND_DRAFT_REQUIRED")
    require(type(top_k) is int and 1<=top_k<=12,"V4_LEGACY_TOP_K")
    prior=[(p,financial_concepts(p["candidate_text"])) for p in index["items"]]
    hits=[];seen=set()
    for w in draft["windows"]:
        wid=w.get("window_id")
        require(type(wid) is str and re.fullmatch(r"W\d{5}",wid),
                "V4_LEGACY_WINDOW_INVALID")
        for c in w["claims"]:
            cid=c.get("claim_id")
            require(type(cid) is str and cid not in seen and
                    c.get("annotation_status")=="UNREVIEWED" and
                    bool(c.get("source_refs")),
                    "V4_LEGACY_CLAIM_NOT_PROVISIONAL_SOURCE_LINKED")
            seen.add(cid)
            f=c.get("frame") or {}
            text=" ".join((str(c.get("proposition") or ""),
                str(f.get("product") or ""),str(f.get("financial_event") or "")))
            concepts=financial_concepts(text)
            matches=[]
            for old,old_concepts in prior:
                common=sorted(concepts & old_concepts)
                if common:matches.append((len(common),old["legacy_claim_id"],old,common))
            matches.sort(key=lambda x:(-x[0],x[1]))
            for overlap,oldid,old,common in matches[:top_k]:
                hits.append({
                    "new_claim_id":cid,"new_window_id":wid,
                    "legacy_claim_id":oldid,
                    "legacy_source_paths":sorted({s["path"] for s in old["sources"]}),
                    "matching_controlled_concepts":common,
                    "retrieval_overlap_signal_count":overlap,
                    "relation":"UNDECIDED_REQUIRES_SCOPE_TIME_CAUSAL_REVIEW",
                    "same_claim_proven":False,
                    "independent_relation_verified":False,
                    "prior_financial_truth_certified":False})
    body={
        "schema":CROSSWALK_SCHEMA,
        "source_sha256":draft.get("original_sha256"),
        "prior_baseline_ref":index.get("baseline_ref"),
        "prior_index_sha256":sha256(_canonical(index)),
        "prior_source_blobs":expected_source_blobs,
        "provisional_claim_count":len(seen),
        "legacy_principle_count":len(index["items"]),
        "relation_candidates":hits,
        "relation_decisions_approved":0,
        "legacy_imported_into_new_ire":False,
        "financial_facts_approved":0}
    return {**body,"crosswalk_sha256":sha256(_canonical(body))}
