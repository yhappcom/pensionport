"""Read-only V6 relation candidates bound to immutable master 116 + P4 22+7.

This provides legacy-content identity and a complete per-atom pending relation
ledger. It does NOT decide semantic equivalence, supersession, actual law,
or approve financial claims; approved V5/P4 files are never modified.
"""
from __future__ import annotations

import hashlib
import json
import re

from .atomic_exchange import audit_host_atomic_exchange
from .codec import canonical, require_hash, sha256
from .errors import InvalidInput

MASTER_BLOB = "ab5af7eea02e65d5e36174546a2a94f4cc642d92"
P4_22_BLOB = "bfb446ffb1dd40caa1ed03088d088c9a1ba7490f"
P4_7_BLOB = "b92573dbefb0f22d3a3a266685415c538b4f7a72"
RELATIONS = {"SAME_PENDING", "EXTENDS_PENDING", "CONFLICT_PENDING",
             "SUPERSEDED_PENDING", "DISTINCT_PENDING", "OPEN", "NOVEL_PENDING"}
CLAIM = re.compile(r"C[0-9]{5,8}\Z")


def _blob(raw, expected, name):
    if type(raw) is not bytes or not raw or len(raw) > 8 * 1024 * 1024:
        raise InvalidInput(name + "_BYTES_REQUIRED")
    digest=hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if digest != expected:
        raise InvalidInput(name + "_PROTECTED_GIT_BLOB_DRIFT")
    return raw.decode("utf-8-sig", errors="strict")


def _index_prior(master_raw, p4_22_raw, p4_7_raw):
    master=_blob(master_raw,MASTER_BLOB,"MASTER116")
    a=_blob(p4_22_raw,P4_22_BLOB,"P4_22")
    b=_blob(p4_7_raw,P4_7_BLOB,"P4_7")
    try:
        records=[json.loads(line) for line in master.splitlines() if line.strip()]
        p22=json.loads(a)
        p7=json.loads(b)
    except (ValueError,TypeError) as exc:
        raise InvalidInput("PRIOR_KNOWLEDGE_JSON_INVALID") from exc
    if len(records)!=116:
        raise InvalidInput("PRIOR_MASTER116_CARDINALITY_DRIFT")
    indexed={}
    for i,record in enumerate(records,1):
        cid=f"GOMHEE-C{i:02d}"
        if (type(record) is not dict or set(record)!={
            "claim_id","topic","claim","supporting_videos","status","confidence"
        } or record["claim_id"]!=cid or
            type(record["claim"]) is not str or len(record["claim"].strip())<5 or
            type(record["supporting_videos"]) is not list or
            not record["supporting_videos"]):
            raise InvalidInput("PRIOR_MASTER116_ROW_DRIFT")
        indexed[("MASTER116",cid)]=sha256(record["claim"].encode("utf-8"))
    if (p22.get("schema")!="IRE_V5_P4_MATERIALIZED_SCOPED_EDUCATION22_V1" or
        len(p22.get("nodes",[]))!=22 or
        p22.get("active_education_nodes")!=22 or
        p22.get("P3_formal_claim_approvals")!=0 or
        p22.get("B04_formal_master_merges")!=0 or
        p22.get("personal_trade_recommendations_authorized") is not False or
        p7.get("schema")!="IRE_V5_P4_P3_27_SOURCE_INCREMENTAL_EDUCATION29_V1" or
        len(p7.get("items",[]))!=7 or
        p7.get("combined_education_nodes")!=29 or
        p7.get("materialized_116_master_updated") is not False or
        p7.get("financial_law_facts_formally_approved")!=0 or
        p7.get("blind_independent_recall_certified") is not False):
        raise InvalidInput("PRIOR_P4_EDUCATION_STATUS_DRIFT")
    for item in p22["nodes"]:
        if (type(item) is not dict or type(item.get("knowledge_id")) is not str or
            type(item.get("statement")) is not str or
            ("P4_EDUCATION",item["knowledge_id"]) in indexed):
            raise InvalidInput("PRIOR_P4_NODE_INVALID")
        indexed[("P4_EDUCATION",item["knowledge_id"])]=sha256(item["statement"].encode())
    for item in p7["items"]:
        if (type(item) is not dict or type(item.get("knowledge_id")) is not str or
            type(item.get("safe_general_statement")) is not str or
            item.get("personalized_action_approved") is not False or
            item.get("formal_116_master_claim_merged") is not False or
            ("P4_EDUCATION",item["knowledge_id"]) in indexed):
            raise InvalidInput("PRIOR_P4_NEW_NODE_INVALID")
        indexed[("P4_EDUCATION",item["knowledge_id"])]=sha256(
            item["safe_general_statement"].encode())
    if len(indexed)!=145:
        raise InvalidInput("PRIOR_116_PLUS_29_IDENTITY_DRIFT")
    return indexed


def audit_prior_candidates(source, exchange, inputs: dict) -> dict:
    if type(inputs) is not dict or set(inputs)!={
        "master116_bytes", "p4_22_bytes", "p4_7_bytes", "relations"
    }:
        raise InvalidInput("PRIOR_RELATION_INPUT_SCHEMA_INVALID")
    audit=audit_host_atomic_exchange(source,exchange)
    indexed=_index_prior(inputs["master116_bytes"],inputs["p4_22_bytes"],
                          inputs["p4_7_bytes"])
    relations=inputs["relations"]
    if type(relations) is not list or len(relations)>20000:
        raise InvalidInput("PRIOR_RELATION_CENSUS_INVALID")
    source_claims={atom["claim_id"] for atom in exchange["atoms"]}
    matched=set(); pairs=set()
    buckets={k:0 for k in sorted(RELATIONS)}
    for row in relations:
        if type(row) is not dict or set(row)!={
            "claim_id","candidate_source_sha256","target_kind","target_id",
            "target_content_sha256","relationship","rationale",
            "independent_semantic_review_verified","personalized_action_approved"
        }:
            raise InvalidInput("PRIOR_RELATION_ROW_SCHEMA_INVALID")
        cid=row["claim_id"]
        if (type(cid) is not str or not CLAIM.fullmatch(cid) or
            cid not in source_claims or
            row["candidate_source_sha256"]!=source.source_sha256 or
            row["relationship"] not in RELATIONS or
            row["independent_semantic_review_verified"] is not False or
            row["personalized_action_approved"] is not False or
            type(row["rationale"]) is not str or
            not 8<=len(row["rationale"].strip())<=1000):
            raise InvalidInput("PRIOR_RELATION_SELF_APPROVAL_OR_CANDIDATE_DRIFT")
        kind,target=row["target_kind"],row["target_id"]
        if row["relationship"]=="NOVEL_PENDING":
            if kind!="NONE" or target is not None or row["target_content_sha256"] is not None:
                raise InvalidInput("PRIOR_RELATION_NOVEL_TARGET_INVALID")
        elif kind not in ("MASTER116","P4_EDUCATION") or (
            kind,target) not in indexed or
            row["target_content_sha256"]!=indexed[(kind,target)]:
            raise InvalidInput("PRIOR_RELATION_TARGET_CONTENT_DRIFT")
        key=(cid,kind,target)
        if key in pairs:
            raise InvalidInput("PRIOR_RELATION_DUPLICATE")
        pairs.add(key)
        matched.add(cid)
        buckets[row["relationship"]]+=1
    if matched!=source_claims:
        raise InvalidInput("PRIOR_EVERY_HOST_ATOM_REQUIRES_RELATION_DISPOSITION")
    return {
        "schema":"IRE_V6_PRIOR116_P4_CANDIDATE_AUDIT_V1",
        "source_sha256":source.source_sha256,
        "source_atom_exchange_digest":audit["atom_candidate_digest"],
        "master116_git_blob_sha1":MASTER_BLOB,
        "p4_prior22_git_blob_sha1":P4_22_BLOB,
        "p4_new7_git_blob_sha1":P4_7_BLOB,
        "protected_master_claims_replayed":116,
        "p4_general_education_context_nodes_replayed":29,
        "host_candidate_atoms_accounted_for":len(matched),
        "pending_relation_count":len(relations),
        "relation_count_by_pending_class":buckets,
        "source_first_atomic_exhaustiveness_verified":False,
        "prior_semantic_relation_independently_verified":False,
        "knowledge_auto_merged":False,
        "master116_modified":False,
        "advisory_personal_action_approved":False,
        "engine_quality_certified":False,
        "p0_go":False,
        "status":"PRIOR_KNOWLEDGE_READONLY_CANDIDATES_AWAITING_SEMANTIC_REVIEW"
    }
