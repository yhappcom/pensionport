"""V127 source-linked cross-video knowledge dependency and conflict quarantine.

Graph structure is mechanically verified, NOT semantic equivalence or authority.
A ChatGPT conflict against existing knowledge must quarantine BOTH sides until
future adjudication. Revoked roots quarantine their SAME/EXTENDS descendants.
"""
from __future__ import annotations

from ire.v6.errors import QualityNotProven
from ire.v6.codec import sha256


def _stop(code):
    raise QualityNotProven("V127_GRAPH_" + code)


def inspect_cumulative_knowledge_graph(entries, statuses):
    """Pure graph audit for a checked V126 event-chain snapshot.

    A record alone does not authenticate the model's semantic relation labels.
    """
    if type(entries) is not list or type(statuses) is not dict:
        _stop("INPUT_SCHEMA")
    rows = {r.get("knowledge_id"):r for r in entries if type(r) is dict}
    if len(rows) != len(entries) or set(rows) != set(statuses):
        _stop("KNOWLEDGE_SNAPSHOT_CENSUS_DRIFT")
    reverse = {}
    conflicts = set()
    edges = {}
    for kid, record in rows.items():
        if (type(kid) is not str or len(kid)!=64 or
            record.get("schema") != "IRE_V126_CHAT_VETTED_CANDIDATE_V1" or
            record.get("research_candidate_only") is not True or
            record.get("personal_advice_approved") is not False or
            record.get("relation") not in {"NEW","SAME","EXTENDS","CONFLICT"} or
            record.get("target_kind") not in {"NONE","MASTER116","P4_EDUCATION","CUMULATIVE"}):
            _stop("ENTRY_UNSAFE_OR_SCHEMA_DRIFT")
        target = record.get("target_id")
        if record["target_kind"] == "CUMULATIVE":
            if type(target) is not str or target not in rows or target==kid:
                _stop("ORPHAN_OR_SELF_CUMULATIVE_TARGET")
            target_record=rows[target]
            if (record["relation"] == "SAME" and
                    record["concept_id"] != target_record["concept_id"]):
                _stop("SAME_CONCEPT_IDENTITY_INCONSISTENT")
            edges[kid]=target
            reverse.setdefault(target,set()).add(kid)
            if record["relation"] == "CONFLICT" and statuses[kid]=="ACTIVE":
                conflicts.add(kid)
                conflicts.add(target)
        else:
            if record["target_kind"] == "NONE" and target is not None:
                _stop("NON_TARGETED_RECORD_WITH_TARGET")
            if record["target_kind"] in {"MASTER116","P4_EDUCATION"} and not target:
                _stop("MISSING_PROTECTED_TARGET")
            if record["relation"] == "SAME" and record["target_kind"] == "NONE":
                _stop("UNSUPPORTED_UNTARGETED_SAME")
    # Iterative cycle detection: a 791-video corpus may exceed Python's
    # recursion limit even for a legitimate long SAME/EXTENDS dependency chain.
    visited=set()
    for kid in rows:
        if kid in visited:
            continue
        chain=set()
        cursor=kid
        while cursor not in visited:
            if cursor in chain:
                _stop("CUMULATIVE_CYCLE")
            chain.add(cursor)
            if cursor not in edges:
                break
            cursor=edges[cursor]
        visited.update(chain)
    blocked={kid for kid,s in statuses.items() if s!="ACTIVE"}
    blocked.update(conflicts)
    blocked.update(kid for kid,r in rows.items() if r["relation"]=="CONFLICT")
    # Revocation/conflict in a root invalidates dependent SAME/EXTENDS claims,
    # not merely the root.  A later ChatGPT supersession step must adjudicate.
    todo=list(blocked)
    while todo:
        parent=todo.pop()
        for child in reverse.get(parent,()):
            if child not in blocked:
                blocked.add(child)
                todo.append(child)
    active = set(rows)-blocked
    # Cross-source identical text with distinct concepts remains a semantic
    # review frontier; never auto-equivalent or publishable as settled advice.
    propositions={}
    for k in active:
        row=rows[k]
        proposition=row.get("atom",{}).get("proposition")
        if not isinstance(proposition,str) or not proposition.strip():
            _stop("MISSING_ATOMIC_PROPOSITION")
        propositions.setdefault(proposition.strip(),[]).append(k)
    duplicate_groups=[ids for ids in propositions.values()
                      if len({rows[k]["concept_id"] for k in ids})>1]
    unresolved_same_text=len(duplicate_groups)
    for ids in duplicate_groups:
        blocked.update(ids)
    todo=[c for ids in duplicate_groups for c in ids]
    while todo:
        parent=todo.pop()
        for child in reverse.get(parent,()):
            if child not in blocked:
                blocked.add(child); todo.append(child)
    active=set(rows)-blocked
    return {
        "schema":"IRE_V127_CUMULATIVE_KNOWLEDGE_CONFLICT_AUDIT_V1",
        "knowledge_rows":len(rows),
        "active_retrievable_rows":len(active),
        "quarantined_rows":len(blocked),
        "active_conflict_links":sum(
            r["relation"]=="CONFLICT" and statuses[k]=="ACTIVE"
            for k,r in rows.items()),
        "cumulative_relationship_edges":len(edges),
        "same_text_distinct_concept_frontiers":unresolved_same_text,
        "blocked_knowledge_ids":sorted(blocked),
        "active_knowledge_ids":sorted(active),
        "semantic_equivalence_independently_verified":False,
        "formal_finance_fact_approved":False,"p0_go":False,
        "status":"STRUCTURAL_GRAPH_AUDIT_NOT_SEMANTIC_APPROVAL"
    }


def audit_private_cumulative_knowledge_graph(store, *, externally_pinned_head=None):
    """Replay real private V126 SQLite SHA events, then inspect version graph."""
    with store._session() as con:
        head, statuses=store._audit(con)
        if externally_pinned_head is not None and externally_pinned_head != head:
            _stop("OWNER_CHECKPOINT_DRIFT")
        import json
        rows=[json.loads(x[0]) for x in con.execute("SELECT entry_json FROM knowledge")]
        graph=inspect_cumulative_knowledge_graph(rows,statuses)
    return {**graph,"current_knowledge_head_sha256":head,
            "external_checkpoint_compared":externally_pinned_head is not None}