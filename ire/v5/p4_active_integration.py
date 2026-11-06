"""P4 production retrieval for a materialized 13+9 scoped education graph.

This is a real, read-only integration into the P3 answer path. It does not
purport to certify P3 W00041..W00067 without original SRT and atomic receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from .first_five_40_retrieval_bridge import load_catalog as validated_first40
from .integrated_education_gate import verify as verify_legacy13
from .phase1_to_phase4_progress import audit as audit_p3_progress

MANIFEST = Path("ire/v5/advisory_knowledge/p4_integrated_scoped_education22_20261106.json")
LEGACY = Path("ire/v5/advisory_knowledge/integrated_education13_20261104.json")
SCOPED = Path("ire/v5/validation/first_five_40_scoped_fact_knowledge_review_20261106.json")
COMPACT = Path("ire/v5/validation/v5_first_five_video_01_window_review_20261106.json")
MASTER = Path("data/claims.jsonl")
SOURCE_PATHS = (LEGACY, SCOPED, COMPACT, MASTER)
RELATIONS = (
    ("V5-001-40-PRIVATE_PENSION_1500_TAX",
     "EDU-KR-PRIVATE-PENSION-1500-2026-01",
     "TOPIC_OVERLAP_NOT_EXACT_EQUIVALENCE"),
    ("V5-001-40-ISA_MATURITY_TO_PENSION",
     "EDU-KR-ISA-TO-PENSION-2026-01",
     "TOPIC_OVERLAP_NOT_EXACT_EQUIVALENCE"),
    ("V5-001-40-PENSION_BASIS_PROVENANCE",
     "EDU-PENSION-DEFERRED-TAX",
     "SPECIFIC_DETAIL_EXTENDS_PRIOR_EDUCATION"),
    ("V5-001-40-DEEMED_PENSION_WITHDRAWAL_ORDER",
     "EDU-PENSION-DEFERRED-TAX",
     "SPECIFIC_DETAIL_EXTENDS_PRIOR_EDUCATION"),
    ("V5-001-40-DIVIDEND_2000_VS_PENSION_1500",
     "EDU-KR-PRIVATE-PENSION-1500-2026-01",
     "DISTINCT_THRESHOLD_DO_NOT_CONFLATE"),
)


class P4IntegrationError(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise P4IntegrationError(code)


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\\0" + raw).hexdigest()


def load(root: Path, *, manifest_override: dict | None = None,
         source_zip: Path | None = None) -> dict:
    root = Path(root)
    manifest = read(root / MANIFEST) if manifest_override is None else manifest_override
    require(manifest.get("schema") == "IRE_V5_P4_MATERIALIZED_SCOPED_EDUCATION22_V1"
            and manifest.get("as_of") == "2026-11-06"
            and manifest.get("legacy_master_claim_count") == 116
            and manifest.get("active_education_nodes") == 22
            and manifest.get("provisional_prior13_nodes") == 13
            and manifest.get("scoped_first40_nodes") == 9
            and manifest.get("official_extracts_replayed_by_source_gate") == 15
            and manifest.get("p3_pending_window_count") == 27
            and manifest.get("P3_formal_claim_approvals") == 0
            and manifest.get("B04_formal_master_merges") == 0
            and manifest.get("source_original_zip_replayed_now") is False
            and manifest.get("original_w41_67_atomic_recall_verified") is False
            and manifest.get("personal_trade_recommendations_authorized") is False
            and manifest.get("release_level") ==
                "GENERAL_EDUCATION_RETRIEVAL_ONLY_NOT_NEW_P3_FACT_CERTIFICATION",
            "P4_FALSE_RELEASE_OR_BAD_MANIFEST")
    actual_pins = {str(p): blob_sha((root / p).read_bytes()) for p in SOURCE_PATHS}
    require(manifest.get("lineage_git_blob_sha1") == actual_pins,
            "P4_SOURCE_BYTES_CHANGED_NO_REVIEW")

    legacy_status = verify_legacy13(root)
    first40 = validated_first40(root)
    progress = audit_p3_progress(root, source_zip=source_zip)
    require(legacy_status["knowledge_concepts"] == 13 and len(first40) == 9,
            "P4_PRIOR_EDUCATION_SOURCE_GATES_FAILED")
    require(progress["P1_public_private_receipt_reconciliation"]
                    ["public_formal_processed_windows"] == 5
            and progress["P1_public_private_receipt_reconciliation"]
                    ["historical_private_reviewed_windows"] == 40
            and progress["P3_video1_next_batch"]["windows_queued"] == 27
            and progress["P3_video1_next_batch"]["formal_source_fact_approval"] is False,
            "P4_PRIVATE_RESEARCH_NOT_READY_FOR_PROMOTION")

    old = read(root / LEGACY)
    narrow = read(root / SCOPED)
    compact = read(root / COMPACT)
    by_old = {n["knowledge_id"]: n for n in old["nodes"]}
    by_new = {n["knowledge_id"]: n for n in narrow["knowledge_overlay"]}
    items = manifest.get("nodes")
    require(type(items) is list and len(items) == 22
            and len({n.get("knowledge_id") for n in items}) == 22
            and {n.get("knowledge_id") for n in items} ==
                    set(by_old) | set(by_new),
            "P4_MISSING_DUPLICATE_OR_INVENTED_KNOWLEDGE")

    for node in items:
        key = node["knowledge_id"]
        require(isinstance(node.get("terms"), list)
                and len(node["terms"]) >= 1
                and len(node["terms"]) == len(set(node["terms"]))
                and all(type(x) is str and len(x.strip()) >= 2 for x in node["terms"]),
                "P4_INVALID_RETRIEVAL_TERMS")
        if key in by_old:
            prior = by_old[key]
            require(node.get("namespace") == "PRIOR_13"
                    and node.get("source_claim_ids") == prior["original_source_claims"]
                    and node.get("prior_claim_ids") == prior["existing_core_claim_ids"]
                    and node.get("authority_ids") == prior["authority_ids"]
                    and node.get("statement") == prior["safe_general_statement"]
                    and node.get("scope_and_exceptions") ==
                        prior["critical_scope_and_exceptions"]
                    and node.get("status") ==
                        "EXISTING_PROVISIONAL_EDUCATION_NOT_CURRENT_LAW_APPROVAL",
                    "P4_LEGACY_NODE_SILENTLY_MUTATED")
        else:
            source = by_new[key]
            require(node.get("namespace") == "FIRST40_SCOPED_9"
                    and node.get("source_claim_ids") == source["source_claim_ids"]
                    and node.get("prior_claim_ids") == source["prior_claim_ids"]
                    and node.get("authority_ids") == source["official_source_ids"]
                    and node.get("statement") == source["knowledge_text"]
                    and node.get("terms") == source["retrieval_terms"]
                    and node.get("status") ==
                        "SCOPED_EDUCATION_OFFLINE_OFFICIAL_EXTRACT_REPLAYED",
                    "P4_FIRST40_NODE_SILENTLY_MUTATED")
    edges = manifest.get("cross_namespace_education_edges")
    require(type(edges) is list and len(edges) == len(RELATIONS),
            "P4_RELATIONS_CHANGED")
    expected_edges = [
        {"from": fr, "to": to, "relation": relation,
         "status": "EDUCATIONAL_RELATION_ONLY_NO_FORMAL_MASTER_MERGE"}
        for fr, to, relation in RELATIONS
    ]
    require(edges == expected_edges, "P4_ILLEGAL_EQUIVALENCE_OR_MERGE")

    pending = manifest.get("p3_pending_windows")
    queue = compact["records"][40:]
    require(type(pending) is list and len(pending) == len(queue) == 27,
            "P4_MISSING_P3_QUARANTINE")
    for actual, parent in zip(pending, queue):
        require(actual.get("window_id") == parent["window_id"]
                and actual.get("first_cue") == parent["first_cue"]
                and actual.get("last_cue") == parent["last_cue"]
                and actual.get("source_sha256") == parent["primary_text_sha256"]
                and actual.get("domain") == parent["domain"]
                and actual.get("meaning_type") == parent["meaning_type"]
                and actual.get("risk_review_codes") == parent["risk_review_codes"]
                and actual.get("source_original_replayed_in_current_turn") is False
                and actual.get("financial_fact_verified") is False
                and actual.get("formal_claim_approved") is False
                and actual.get("knowledge_node_created") is False
                and actual.get("status") == "P3_PENDING_SOURCE_BYTE_AND_ATOMIC_FACT_REVIEW",
                "P4_UNVERIFIED_P3_PROMOTION_OR_LOST_CUE")
    require(pending[0]["window_id"] == "W00041"
            and pending[-1]["window_id"] == "W00067",
            "P4_WRONG_P3_WINDOW_BATCH")
    return {
        "schema": "IRE_V5_P4_ACTIVE_SCOPED_EDUCATION_GRAPH_V1",
        "nodes": items,
        "cross_namespace_edges": edges,
        "quarantined_p3_window_count": 27,
        "active_education_node_count": 22,
        "legacy_claims_preserved": 116,
        "official_content_replay_snapshots": 15,
        "original_source_replayed_this_execution":
            progress["P3_video1_next_batch"]["replay_verified"],
        "p3_verified_atomic_claims": 0,
        "formal_master_merges": 0,
        "approved_personal_trades": 0,
        "release": "ACTIVE_EDUCATION_RETRIEVAL_ONLY",
    }


def _normalize(s: str) -> str:
    return re.sub(r"\\s+|[,，]", "", s.casefold())


def retrieve(root: Path, question: str, *, intent: str = "general_education",
             limit: int = 5) -> dict:
    require(isinstance(question, str) and bool(question.strip()),
            "P4_EMPTY_QUESTION")
    require(intent in {"general_education", "personal_decision_support",
                       "order_execution", "guaranteed_return"},
            "P4_UNKNOWN_INTENT")
    require(type(limit) is int and 1 <= limit <= 22, "P4_BAD_LIMIT")
    graph = load(root)
    if intent in {"order_execution", "guaranteed_return"}:
        return {"schema": "IRE_V5_P4_INTEGRATED_RETRIEVAL_V1",
                "match_count": 0, "items": [],
                "decision": "BLOCKED_ACTION_OR_GUARANTEE",
                "P3_promoted_fact_count": 0, "master_modified": False,
                "personal_trading_approved": False}
    q = _normalize(question)
    scored = []
    for node in graph["nodes"]:
        matches = [t for t in node["terms"] if _normalize(t) in q]
        if matches:
            score = sum(len(_normalize(t)) + 1 for t in matches)
            scored.append((score, node))
    scored.sort(key=lambda p: (-p[0], p[1]["knowledge_id"]))
    selected = []
    for _, item in scored[:limit]:
        selected.append({k: v for k, v in item.items() if k != "terms"})
    return {"schema": "IRE_V5_P4_INTEGRATED_RETRIEVAL_V1",
            "match_count": len(selected), "items": selected,
            "decision": "SCOPED_EDUCATION_ONLY" if selected else "NO_MATCH",
            "P3_promoted_fact_count": 0, "master_modified": False,
            "personal_trading_approved": False}


def audit(root: Path) -> dict:
    graph = load(root)
    queries = [
        ("ISA 만기자금 연금전환 60일",
         {"EDU-KR-ISA-TO-PENSION-2026-01",
          "V5-001-40-ISA_MATURITY_TO_PENSION"}),
        ("사적연금 1,500만원 분리과세",
         {"EDU-KR-PRIVATE-PENSION-1500-2026-01",
          "V5-001-40-PRIVATE_PENSION_1500_TAX"}),
        ("ETF 괴리율과 추적오차", {"EDU-ETF-NAV-TRACKING"}),
    ]
    for query, expected in queries:
        rows = retrieve(root, query, limit=22)["items"]
        require(expected <= {r["knowledge_id"] for r in rows},
                "P4_COMBINED_RETRIEVAL_MISSING_RELEVANT_NODES")
        require(all("P3_PENDING" not in x["status"] for x in rows),
                "P4_P3_PENDING_ENTERED_RETRIEVAL")
    blocked = retrieve(root, "내 계좌에서 전량 매도해줘",
                       intent="order_execution")
    empty = retrieve(root, "영화관 주차권 안내")
    require(blocked["match_count"] == 0 and empty["match_count"] == 0,
            "P4_UNSAFE_OR_IRRELEVANT_MATCH")
    return {
        "schema": "IRE_V5_P4_RUNTIME_INTEGRATION_AUDIT_V1",
        "integrated_education_nodes": graph["active_education_node_count"],
        "legacy_education_nodes": 13,
        "source_scoped_first40_nodes": 9,
        "cross_namespace_edges": len(graph["cross_namespace_edges"]),
        "quarantined_unconfirmed_p3_windows": graph["quarantined_p3_window_count"],
        "official_snapshots_replayed": graph["official_content_replay_snapshots"],
        "actual_integrated_queries_verified": len(queries),
        "legacy_master_116_changed": False,
        "P3_new_approved_facts": 0,
        "formal_master_merges": 0,
        "personal_order_approved": False,
        "integration_mode": "LIVE_READONLY_EDUCATION_INDEX",
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--question")
    p.add_argument("--intent", default="general_education")
    args = p.parse_args()
    r = retrieve(args.root, args.question, intent=args.intent) if args.question else audit(args.root)
    print(json.dumps(r, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
