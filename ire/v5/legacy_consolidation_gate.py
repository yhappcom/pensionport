"""Fail-closed V5 reconciliation of the legacy-claims inventory and first 20.

This validates provenance and knowledge-graph lineage; it does NOT certify
previous video summaries or regulatory truth. External original-source
search and meaning adjudication belong in the active chat when needed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT_DIR = Path("ire/v5/legacy_consolidation")
MASTER = ROOT_DIR / "master_index_20261105.json"
B01 = ROOT_DIR / "batch_B01_C001_C020_20261105.json"


class LegacyConsolidationError(ValueError):
    pass


def must(ok: bool, code: str):
    if not ok:
        raise LegacyConsolidationError(code)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def verify(root: Path, master: dict | None = None, batch: dict | None = None) -> dict:
    root = Path(root)
    master = load_json(root / MASTER) if master is None else master
    batch = load_json(root / B01) if batch is None else batch
    claim_path = root / "data/claims.jsonl"
    video_path = root / "data/videos.jsonl"
    graph_path = root / "ire/v5/advisory_knowledge/integrated_education13_20261104.json"
    claims = load_jsonl(claim_path)
    videos = load_jsonl(video_path)
    graph = load_json(graph_path)
    must(len(claims) == 116 and len(videos) == 157
         and len(graph["nodes"]) == 13, "LEGACY_SOURCE_COUNTS_CHANGED")
    source_sha = {
        "legacy": git_blob_sha(claim_path.read_bytes()),
        "video": git_blob_sha(video_path.read_bytes()),
        "graph": git_blob_sha(graph_path.read_bytes()),
    }
    must(master.get("source_blob_shas") == source_sha
         and batch.get("source_legacy_blob_sha") == source_sha["legacy"]
         and batch.get("source_video_index_blob_sha") == source_sha["video"]
         and batch.get("source_education_graph_blob_sha") == source_sha["graph"],
         "LEGACY_SOURCE_SNAPSHOT_CHANGED_REASSESS")
    must(master.get("schema") == "IRE_V5_LEGACY_SOURCE_CONSOLIDATION_MASTER_V1"
         and master.get("as_of") == batch.get("as_of") == "2026-11-05"
         and master.get("requires_active_chat_web_evidence_review_for_new_financial_fact_approval") is True
         and master.get("main_branch_unchanged") is True
         and master.get("summary", {}).get("fact_approvals_from_metadata_index") == 0
         and master["summary"].get("previous_research_records_mutated") == 0,
         "LEGACY_MASTER_FALSE_FACT_OR_UNSAFE_STATE")
    vmap = {v["video_id"]: v for v in videos}
    must(len(vmap) == len(videos), "LEGACY_DUPLICATE_CANONICAL_VIDEO_IDS")
    ids = [x["claim_id"] for x in claims]
    must(len(ids) == len(set(ids)) and ids ==
         [f"GOMHEE-C{i:02d}" if i < 100 else f"GOMHEE-C{i}"
          for i in range(1, 117)], "LEGACY_CLAIM_ID_SEQUENCE_CHANGED")
    direct = {cid: [] for cid in ids}
    available = set()
    for n in graph["nodes"]:
        kid = n["knowledge_id"]
        must(kid not in available, "LEGACY_DUPLICATE_V5_EDUCATION_NODE")
        available.add(kid)
        for cid in n["existing_core_claim_ids"]:
            must(cid in direct, "LEGACY_GRAPH_ORPHAN_CLAIM")
            direct[cid].append(kid)
    index = master.get("claims", [])
    must(len(index) == 116, "LEGACY_INVENTORY_INCOMPLETE")
    batches = master.get("batches", [])
    must(len(batches) == 6, "LEGACY_BATCH_COUNT_INVALID")
    assigned = []
    for k, b in enumerate(batches, 1):
        want = [x["claim_id"] for x in claims[(k-1)*20:k*20]]
        must(b.get("batch_id") == f"B{k:02d}"
             and b.get("count") == len(want)
             and b.get("claim_ids") == want
             and b.get("range") == [want[0], want[-1]]
             and b.get("state") ==
                 ("METADATA_AND_SOURCE_DOCUMENT_TRIAGE_COMPLETED" if k == 1
                  else "PENDING_DETAILED_RECONCILIATION")
             and b.get("artifact") ==
                 (str(B01) if k == 1 else None),
             "LEGACY_PARTITION_OR_COMPLETION_MISMATCH")
        assigned.extend(want)
    must(assigned == ids, "LEGACY_BATCH_COVERAGE_GAP")
    for i, (row, claim) in enumerate(zip(index, claims)):
        must(row.get("claim_id") == claim["claim_id"]
             and row.get("original_topic") == claim["topic"]
             and row.get("legacy_confidence") == claim["confidence"]
             and row.get("legacy_status") == claim["status"]
             and row.get("video_ids") == claim["supporting_videos"]
             and all(id in vmap for id in row["video_ids"])
             and row.get("canonical_video_links_complete") is True
             and row.get("direct_v5_core_reference_ids") == direct[claim["claim_id"]]
             and row.get("assigned_batch_id") == f"B{i//20+1:02d}"
             and row.get("fact_acceptance_this_index") == "NOT_REASSESSED_METADATA_ONLY",
             "LEGACY_INDEX_UNTRACED_OR_OVERPROMOTED_CLAIM")
    summary = master["summary"]
    must(summary.get("legacy_claims") == len(claims)
         and summary.get("metadata_videos") == len(videos)
         and summary.get("integrated_education_topics") == len(available)
         and summary.get("legacy_claims_with_missing_video_ids") == 0
         and summary.get("all_legacy_video_refs") ==
             sum(len(x["supporting_videos"]) for x in claims)
         and summary.get("distinct_video_ids_referenced_from_legacy_claims") ==
             len({id for c in claims for id in c["supporting_videos"]})
         and summary.get("core_claims_with_existing_v5_graph_reference") ==
             sum(bool(x) for x in direct.values())
         and summary.get("existing_v5_core_edges") ==
             sum(map(len, direct.values())),
         "LEGACY_MASTER_SUMMARY_NOT_REPRODUCIBLE")
    must(batch.get("schema") == "IRE_V5_LEGACY_CONSOLIDATION_BATCH_V1"
         and batch.get("batch_id") == "B01"
         and batch.get("claim_range") == ["GOMHEE-C01", "GOMHEE-C20"]
         and batch.get("original_ledger_preserved") is True
         and batch.get("unverified_fact_promotion_prohibited") is True
         and batch.get("basis") ==
             "METADATA_AND_LEGACY_STUDY_DOCUMENT_RECONCILIATION_NOT_FRESH_REGULATORY_FACT_CHECK",
         "LEGACY_BATCH_PRETENDS_FACT_APPROVAL")
    reviewed = batch.get("records", [])
    must(len(reviewed) == 20, "LEGACY_FIRST_BATCH_NOT_20")
    source_count = 0
    doc_count = 0
    content_review_count = 0
    class_counts: Counter[str] = Counter()
    source_ids = set()
    linked_count = 0
    linked_edges = 0
    for claim, row in zip(claims[:20], reviewed):
        cid = claim["claim_id"]
        must(row.get("claim_id") == cid and
             row.get("original_statement") == claim["claim"]
             and row.get("original_topic") == claim["topic"]
             and row.get("legacy_status") == claim["status"]
             and row.get("legacy_confidence") == claim["confidence"]
             and type(row.get("interpretation_and_exceptions")) is str
             and len(row["interpretation_and_exceptions"]) >= 35,
             "LEGACY_RESEARCH_STATEMENT_OR_MEANING_LOST")
        must(row.get("chat_evidence_fact_approved_this_batch") is False
             and row.get("personal_investment_advice_approved") is False
             and row.get("original_srt_full_cue_coverage_reverified_this_batch") is False
             and row.get("official_rule_current_source_verified_this_batch") is False,
             "LEGACY_METADATA_MISREPORTED_AS_FACT_VERIFIED")
        group = row.get("research_triage")
        must(group in {"STRATEGY_CONTEXT_ONLY",
                       "GENERAL_EDUCATION_LINK_CANDIDATE",
                       "TIME_SENSITIVE_EVIDENCE_RECHECK",
                       "SOURCE_LIMITED_NOT_FACT_APPROVED"},
             "LEGACY_TRIAGE_LABEL_UNKNOWN")
        class_counts[group] += 1
        vids = row.get("source_videos", [])
        must([x.get("video_id") for x in vids] == claim["supporting_videos"],
             "LEGACY_SUPPORTING_VIDEO_ID_CHANGED")
        source_count += len(vids)
        source_ids.update(x["video_id"] for x in vids)
        checked_paths = []
        for v in vids:
            metadata = vmap[v["video_id"]]
            must(v.get("canonical_sequence") == metadata["sequence"]
                 and v.get("verification_status") == metadata.get("verification_status")
                 and v.get("analysis_status") == metadata.get("analysis_status"),
                 "LEGACY_CANONICAL_VIDEO_STATUS_CONTRADICTS_INDEX")
            docs = v.get("video_document_paths", [])
            must(isinstance(docs, list) and len(docs) >= 1
                 and len(docs) == len(set(docs)),
                 "LEGACY_VIDEO_DOCUMENT_NOT_MAPPED")
            for doc in docs:
                must(doc.startswith("videos/") and v["video_id"] in Path(doc).name
                     and (root / doc).is_file(),
                     "LEGACY_VIDEO_DOCUMENT_NOT_FOUND")
            doc_count += len(docs)
            if v.get("document_read_in_this_batch") is True:
                checked_paths.extend(docs)
        must(row.get("reviewed_primary_or_secondary_study_documents") == checked_paths,
             "LEGACY_SOURCE_STUDY_DOC_REVIEW_CLAIM_INCONSISTENT")
        content_review_count += bool(checked_paths)
        actual_links = [x["knowledge_id"]
                        for x in row.get("existing_v5_graph_core_references", [])]
        must(actual_links == direct[cid]
             and all(x.get("relation") ==
                     "EXISTING_V5_GRAPH_CORE_REFERENCE_NOT_A_NEW_EVIDENCE_APPROVAL"
                     for x in row["existing_v5_graph_core_references"]),
             "LEGACY_EXISTING_V5_EDUCATION_GRAPH_LINK_INACCURATE")
        linked_count += bool(actual_links)
        linked_edges += len(actual_links)
        thematic = row.get("integrated_knowledge_links", [])
        must(len(thematic) == len({x["knowledge_id"] for x in thematic})
             and all(x.get("knowledge_id") in available and x.get("relation") ==
                     "TOPICALLY_RELATED_NOT_SAME_FACT_AND_NOT_NEW_APPROVAL"
                     for x in thematic), "LEGACY_THEMATIC_LINK_FALSELY_APPROVED")
        relationships = row.get("legacy_relation_candidates", [])
        must(all(x.get("claim_id") in ids and x.get("claim_id") != cid
                 and x.get("relation") ==
                     "POTENTIAL_OVERLAP_OR_EXTENSION_REQUIRES_SEMANTIC_REVIEW"
                 for x in relationships), "LEGACY_CROSSCLAIM_RELATION_UNSAFE")
    stats = batch.get("stats", {})
    must(stats.get("claims") == len(reviewed) == 20
         and stats.get("video_links") == source_count
         and stats.get("distinct_video_ids") == len(source_ids)
         and stats.get("video_links_not_in_canonical_index") == 0
         and stats.get("source_document_paths_mapped") == doc_count
         and stats.get("claims_with_supplemental_study_docs_read") == content_review_count
         and stats.get("triage_counts") == dict(class_counts)
         and stats.get("existing_v5_graph_core_linked_claims") == linked_count
         and stats.get("existing_v5_graph_core_reference_edges") == linked_edges
         and stats.get("new_fact_approvals") == 0
         and stats.get("new_personalized_advice_approvals") == 0
         and stats.get("legacy_claims_modified") == 0,
         "LEGACY_BATCH_SUMMARY_INCONSISTENT")
    special = {r["claim_id"]: r for r in reviewed}
    for id in ("GOMHEE-C07", "GOMHEE-C08", "GOMHEE-C13",
               "GOMHEE-C15", "GOMHEE-C17"):
        must(special[id]["research_triage"] == "TIME_SENSITIVE_EVIDENCE_RECHECK",
             "LEGACY_TIME_SENSITIVE_FINANCIAL_LAW_WAS_AUTOPROMOTED")
    for id in ("GOMHEE-C11", "GOMHEE-C14", "GOMHEE-C18",
               "GOMHEE-C19", "GOMHEE-C20"):
        must(special[id]["research_triage"] == "SOURCE_LIMITED_NOT_FACT_APPROVED",
             "LEGACY_UNVERIFIED_SOURCE_GOT_PROMOTED")
    return {
        "schema": "IRE_V5_LEGACY_CONSOLIDATION_GATE_V1",
        "master_claims_indexed": len(index),
        "all_canonical_video_links_found": True,
        "preexisting_v5_education_node_core_claims": summary[
            "core_claims_with_existing_v5_graph_reference"],
        "preexisting_v5_education_node_core_edges": summary[
            "existing_v5_core_edges"],
        "first_batch": "B01",
        "first_batch_claims_integrated": len(reviewed),
        "first_batch_video_links_checked": source_count,
        "first_batch_source_doc_paths_mapped": doc_count,
        "first_batch_preexisting_core_links": linked_edges,
        "remaining_batches_not_claimed_complete": 5,
        "existing_approved_facts_retracted_or_changed": 0,
        "new_claims_independently_verified_by_script": 0,
        "new_personalized_advice_approvals": 0,
        "outcome": "SOURCE_AND_CONCEPT_RECONCILIATION_CLOSED_FACT_APPROVAL_SEPARATE",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    args = p.parse_args()
    print(json.dumps(verify(args.root), sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
