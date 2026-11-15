"""V128: all-or-nothing private multi-child research candidate publication.

A synchronous ChatGPT host, not this Python module, must prepare EVERY child
atomic exchange, V6 host batch, V123 ChatGPT review, source evidence and final
parent/seam semantic decision. Synthetic tests cannot certify those judgments.

All child V126 inserts are first replayed against a disposable copy of the
private knowledge DB. If and only if the complete V127/V1271 parent assembly,
ChatGPT parent release and all V126 child passes succeed, all staged new
entries, event-chain rows and one parent publication receipt are committed in
ONE SQLite transaction to the durable private knowledge DB. No V5/Master/P4
mutation, financial fact approval, new-video analysis or portfolio access.
"""
from __future__ import annotations

import json
import re
import sqlite3
import tempfile
from pathlib import Path

from ire.v6.codec import ZERO_SHA, canonical, json_digest
from ire.v6.errors import InvalidInput, QualityNotProven
from v126_chat_approved_knowledge_store import PrivateKnowledgeStore
from v127_cumulative_knowledge_graph import inspect_cumulative_knowledge_graph

HEX = re.compile(r"[0-9a-f]{64}\Z")
PARENT_RELEASE_SCHEMA = "IRE_V128_CHATGPT_WHOLE_VIDEO_RELEASE_V1"
PROOF_SCHEMA = "IRE_V128_PRIVATE_PARENT_PUBLICATION_V1"


def _stop(code):
    raise QualityNotProven("V128_" + code)


def _hash(value):
    return json_digest(value)


def _validate_release(release, assembly, checkpoint_head, seams, packets):
    """Check source-pinned parent-level CHATGPT decision, never self-generate it."""
    allowed = {"schema", "review_executor", "parent_source_sha256",
               "parent_replay_sha256", "checkpoint_head_sha256",
               "child_chat_review_digest_sha256", "seams_digest_sha256",
               "relation_decisions_digest_sha256", "whole_parent_source_first_reviewed",
               "condition_exception_rebuttal_seams_reviewed", "prior_knowledge_conflicts_resolved",
               "unresolved_high_risk_semantic_omissions", "unresolved_cross_segment_cases",
               "private_chat_parent_review_sha256", "financial_fact_auto_approved",
               "personal_advice_auto_approved"}
    if type(release) is not dict or set(release) != allowed:
        _stop("PARENT_CHAT_RELEASE_SCHEMA")
    cases = [p["case"] for p in packets]
    references = [{"host_event_sha256":c["host_receipt"]["event_sha256"],
                   "host_bundle_sha256":c["host_receipt"]["bundle_sha256"],
                   "chat_review_sha256":_hash(c["chat_review"])} for c in cases]
    decisions = [p["relation_decisions"] for p in packets]
    expected = {
        "schema": PARENT_RELEASE_SCHEMA, "review_executor":"CHATGPT_IN_CHAT",
        "parent_source_sha256":assembly["source_sha256"],
        "parent_replay_sha256":assembly["parent_replay_sha256"],
        "checkpoint_head_sha256":checkpoint_head,
        "child_chat_review_digest_sha256":_hash(references),
        "seams_digest_sha256":_hash(seams),
        "relation_decisions_digest_sha256":_hash(decisions),
        "whole_parent_source_first_reviewed":True,
        "condition_exception_rebuttal_seams_reviewed":True,
        "prior_knowledge_conflicts_resolved":True,
        "unresolved_high_risk_semantic_omissions":0,
        "unresolved_cross_segment_cases":0,
        "financial_fact_auto_approved":False,
        "personal_advice_auto_approved":False,
    }
    for key, value in expected.items():
        if type(release.get(key)) is not type(value) or release.get(key) != value:
            _stop("PARENT_CHAT_RELEASE_NOT_SOURCE_BOUND_" + key.upper())
    private_note = release["private_chat_parent_review_sha256"]
    if type(private_note) is not str or not HEX.fullmatch(private_note):
        _stop("PARENT_CHAT_PRIVATE_EVIDENCE_NOT_PINNED")
    return _hash(release)


def construct_parent_release_review(checkpoint_head, assembly, seams, packets,
                                    *, private_chat_parent_review_sha256):
    """Produce an unsigned review TEMPLATE; the CHATGPT host must judge the booleans.

    This is not a certification function; never call this as a substitute for
    an actual source-first ChatGPT semantic review. Intended only for explicit
    host filling and synthetic fixtures.
    """
    cases=[p["case"] for p in packets]
    return {"schema":PARENT_RELEASE_SCHEMA,"review_executor":"CHATGPT_IN_CHAT",
            "parent_source_sha256":assembly["source_sha256"],
            "parent_replay_sha256":assembly["parent_replay_sha256"],
            "checkpoint_head_sha256":checkpoint_head,
            "child_chat_review_digest_sha256":_hash([{
                "host_event_sha256":c["host_receipt"]["event_sha256"],
                "host_bundle_sha256":c["host_receipt"]["bundle_sha256"],
                "chat_review_sha256":_hash(c["chat_review"])} for c in cases]),
            "seams_digest_sha256":_hash(seams),
            "relation_decisions_digest_sha256":_hash([p["relation_decisions"] for p in packets]),
            "whole_parent_source_first_reviewed":False,
            "condition_exception_rebuttal_seams_reviewed":False,
            "prior_knowledge_conflicts_resolved":False,
            "unresolved_high_risk_semantic_omissions":-1,
            "unresolved_cross_segment_cases":-1,
            "private_chat_parent_review_sha256":private_chat_parent_review_sha256,
            "financial_fact_auto_approved":False,
            "personal_advice_auto_approved":False}


def _parent_id(checkpoint):
    return _hash({"video_id":checkpoint.parent.video_id,
                  "source_sha256":checkpoint.parent.source_sha256,
                  "manifest_sha256":checkpoint.parent.manifest_sha256,
                  "owner_inventory_pin":checkpoint.owner_pin})


def _publication_table(con):
    con.execute("""CREATE TABLE IF NOT EXISTS parent_publications(
        parent_id TEXT PRIMARY KEY, proof_json TEXT NOT NULL,
        proof_sha256 TEXT NOT NULL, from_head_sha256 TEXT NOT NULL,
        to_head_sha256 TEXT NOT NULL, entry_count INTEGER NOT NULL)""")


def _replay_parent_publications(con, current_head):
    """Verify recorded parent publication hashes and original event boundaries."""
    _publication_table(con)
    rows=con.execute("SELECT parent_id,proof_json,proof_sha256,from_head_sha256,"
                     "to_head_sha256,entry_count FROM parent_publications").fetchall()
    events={r[0]:r[1] for r in con.execute("SELECT prev_sha256,event_sha256 FROM events")}
    for pid,raw,digest,from_head,to_head,count in rows:
        try:
            proof=json.loads(raw)
        except (ValueError,TypeError):
            _stop("PARENT_PROOF_JSON_INVALID")
        if (type(proof) is not dict or proof.get("schema")!=PROOF_SCHEMA or
            proof.get("parent_id")!=pid or proof.get("from_head_sha256")!=from_head or
            proof.get("to_head_sha256")!=to_head or proof.get("entry_count")!=count or
            _hash(proof)!=digest or not (isinstance(pid,str) and HEX.fullmatch(pid)) or
            not (isinstance(to_head,str) and HEX.fullmatch(to_head)) or
            not (isinstance(from_head,str) and HEX.fullmatch(from_head)) or
            type(count) is not int or count <= 0):
            _stop("PARENT_PROOF_HASH_OR_SCHEMA_DRIFT")
        cursor=from_head
        for _ in range(count):
            if cursor not in events:
                _stop("PARENT_EVENT_CHAIN_MISSING")
            cursor=events[cursor]
        if cursor!=to_head:
            _stop("PARENT_EVENT_CHAIN_NOT_CONTIGUOUS")
    return {r[0]:json.loads(r[1]) for r in rows}


def publish_parent_once(checkpoint, knowledge_store, packets, seam_reviews,
                        parent_chat_release, *, expected_checkpoint_head,
                        expected_knowledge_head, externally_pinned_knowledge_head=None):
    """Commit every approved child to the private V126 knowledge DB atomically.

    1. Exact V127.1 checkpoint and V127 all-child/seam replay.
    2. Separate, SHA-bound ChatGPT whole-parent release.
    3. Disposable V126 knowledge DB staging with all child batch validations.
    4. Cross-video graph/duplicate/CONFLICT fail-closed audit.
    5. **One** durable SQLite BEGIN IMMEDIATE publication of all new entries,
       events and parent proof; no partial publication on failure.
    """
    if type(packets) is not list or len(packets)!=len(checkpoint.child_ids):
        _stop("PARENT_CHILD_PACKET_CENSUS")
    if any(type(p) is not dict or set(p)!={"case", "relation_decisions", "original_host_batch_replay_args"}
           for p in packets):
        _stop("CHILD_PACKET_SCHEMA")
    if type(expected_checkpoint_head) is not str or not HEX.fullmatch(expected_checkpoint_head):
        raise InvalidInput("V128_CHECKPOINT_HEAD_REQUIRED")
    if type(expected_knowledge_head) is not str or not HEX.fullmatch(expected_knowledge_head):
        raise InvalidInput("V128_KNOWLEDGE_HEAD_REQUIRED")
    if not isinstance(knowledge_store,PrivateKnowledgeStore):
        raise InvalidInput("V128_PRIVATE_KNOWLEDGE_STORE_REQUIRED")
    cases=[p["case"] for p in packets]
    assembly=checkpoint.assemble(cases,seam_reviews,
        expected_checkpoint_head=expected_checkpoint_head)
    if assembly["status"]!="ALL_CHILDREN_REPLAYED_STAGING_ONLY_NOT_PUBLISHED":
        _stop("PARENT_REPLAY_NOT_PASSED")
    review_sha=_validate_release(parent_chat_release,assembly,expected_checkpoint_head,
                                 seam_reviews,packets)
    if any(d.get("relation")=="CONFLICT" for p in packets for d in p["relation_decisions"]):
        _stop("UNRESOLVED_PARENT_KNOWLEDGE_CONFLICT")
    if externally_pinned_knowledge_head is not None and externally_pinned_knowledge_head!=expected_knowledge_head:
        _stop("EXTERNAL_KNOWLEDGE_HEAD_NOT_CURRENT")
    pid=_parent_id(checkpoint)
    stable_request={
        "parent_id":pid,
        "checkpoint_head_sha256":expected_checkpoint_head,
        "parent_replay_sha256":assembly["parent_replay_sha256"],
        "parent_chat_release_sha256":review_sha,
        "seam_reviews_sha256":_hash(seam_reviews),
        "child_batches_sha256":_hash([{
            "host_event_sha256":p["case"]["host_receipt"]["event_sha256"],
            "host_bundle_sha256":p["case"]["host_receipt"]["bundle_sha256"],
            "chat_review_sha256":_hash(p["case"]["chat_review"]),
            "prior_relations_sha256":_hash(p["case"]["prior_knowledge"]["relations"]),
            "relation_decisions_sha256":_hash(p["relation_decisions"])} for p in packets]),
    }
    # A validated prior publication is idempotent; modifications require a
    # separately adjudicated retirement/revision process, not duplicate source.
    with knowledge_store._session() as con:
        current_head,_=knowledge_store._audit(con)
        published=_replay_parent_publications(con,current_head)
        existing=published.get(pid)
        if existing is not None:
            if existing.get("request")!=stable_request or existing.get("from_head_sha256")!=expected_knowledge_head:
                _stop("PARENT_ALREADY_PUBLISHED_WITH_DIFFERENT_PROOF")
            return {"schema":"IRE_V128_ATOMIC_PARENT_PUBLISH_RECEIPT_V1",
                    "status":"IDEMPOTENT_PARENT_KNOWLEDGE_COMMIT",
                    "parent_id":pid,"knowledge_head_sha256":current_head,
                    "entry_count":existing["entry_count"],"idempotent":True,
                    "all_child_chat_reviews_passed":True,
                    "research_candidates_only":True,"financial_fact_approved":0,
                    "p0_go":False}
        if current_head!=expected_knowledge_head:
            _stop("KNOWLEDGE_EXPECTED_HEAD_CHANGED")
        first_event_count=con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        with tempfile.TemporaryDirectory(prefix="v128_staging_",dir=str(knowledge_store.path.parent)) as temp:
            staging_path=Path(temp)/"staging.db"
            target=sqlite3.connect(str(staging_path))
            try:
                con.backup(target)  # read-consistent owner-private copy
            finally:
                target.close()
            staging=PrivateKnowledgeStore(staging_path,parent_staging_only=True)
            head=expected_knowledge_head
            # Exact V123 and frozen V6 source-to-relations replay occurs here.
            for packet in packets:
                case=packet["case"]
                result=staging.add_chat_final_batch(
                    case["source"],case["exchange"],case["prior_knowledge"],
                    host_receipt=case["host_receipt"],chat_review=case["chat_review"],
                    source_store=case["source_store"],
                    official_evidence_bodies=case["official_evidence_bodies"],
                    relation_decisions=packet["relation_decisions"],
                    expected_knowledge_head=head,
                    original_host_batch_replay_args=packet["original_host_batch_replay_args"])
                if result.get("idempotent_replay") is not False:
                    _stop("CHILD_ALREADY_IN_KNOWLEDGE_OUTSIDE_PARENT_BATCH")
                head=result["knowledge_head_sha256"]
            with staging._session() as staged_con:
                staging_head,staged_statuses=staging._audit(staged_con)
                if staging_head!=head:
                    _stop("STAGED_KNOWLEDGE_CHAIN_DRIFT")
                staged_entries=[json.loads(x[0]) for x in staged_con.execute(
                    "SELECT entry_json FROM knowledge")]
                graph=inspect_cumulative_knowledge_graph(staged_entries,staged_statuses)
                original_ids={x[0] for x in con.execute("SELECT knowledge_id FROM knowledge")}
                new_rows=staged_con.execute(
                    "SELECT knowledge_id,entry_json,entry_sha256 FROM knowledge"
                ).fetchall()
                new_rows=[x for x in new_rows if x[0] not in original_ids]
                new_ids={x[0] for x in new_rows}
                if graph["same_text_distinct_concept_frontiers"] or not new_ids or (
                        new_ids & set(graph["blocked_knowledge_ids"])):
                    _stop("PARENT_NEW_KNOWLEDGE_GRAPH_QUARANTINED")
                new_events=staged_con.execute(
                    "SELECT seq,kind,knowledge_id,record_sha256,prev_sha256,event_sha256 "
                    "FROM events WHERE seq>? ORDER BY seq",(first_event_count,)).fetchall()
                if (len(new_rows)!=len(new_events) or
                        set(x[2] for x in new_events)!=new_ids or
                        any(x[1]!="ADD" for x in new_events)):
                    _stop("STAGED_PARENT_EVENT_CENSUS_OR_CHAIN_INVALID")
                final_head=head
                # All validation is complete before touching durable private DB.
                # Acquire single-writer lock and re-check the *original* head.
                con.execute("BEGIN IMMEDIATE")
                live_head,_=knowledge_store._audit(con)
                _replay_parent_publications(con,live_head)
                if live_head!=expected_knowledge_head:
                    _stop("ATOMIC_PUBLICATION_CONCURRENT_HEAD_CHANGE")
                for kid,body,digest in new_rows:
                    con.execute("INSERT INTO knowledge VALUES(?,?,?)",(kid,body,digest))
                for event in new_events:
                    con.execute("INSERT INTO events VALUES(?,?,?,?,?,?)",event)
                applied_head, applied_states=knowledge_store._audit(con)
                if applied_head!=final_head or len(new_ids)!=len(new_rows):
                    _stop("ATOMIC_PARENT_WRITE_REPLAY_MISMATCH")
                proof={"schema":PROOF_SCHEMA,"parent_id":pid,
                       "request":stable_request,"from_head_sha256":expected_knowledge_head,
                       "to_head_sha256":applied_head,"entry_count":len(new_rows),
                       "child_segment_count":len(packets),"chat_release_sha256":review_sha,
                       "candidate_only_not_finance_fact":True,"p0_go":False}
                con.execute("INSERT INTO parent_publications VALUES(?,?,?,?,?,?)",
                            (pid,canonical(proof).decode("utf-8"),_hash(proof),
                             expected_knowledge_head,applied_head,len(new_rows)))
                _replay_parent_publications(con,applied_head)
                con.commit()
                return {"schema":"IRE_V128_ATOMIC_PARENT_PUBLISH_RECEIPT_V1",
                        "status":"WHOLE_PARENT_CHAT_REVIEWED_RESEARCH_KNOWLEDGE_COMMITTED",
                        "parent_id":pid,"checkpoint_head_sha256":expected_checkpoint_head,
                        "knowledge_head_sha256":applied_head,
                        "entry_count":len(new_rows),"child_segments":len(packets),
                        "parent_publication_proof_sha256":_hash(proof),
                        "all_child_chat_reviews_passed":True,
                        "idempotent":False,"research_candidates_only":True,
                        "financial_fact_approved":0,"personal_advice_approved":False,
                        "external_owner_attestation_certified":False,"p0_go":False}