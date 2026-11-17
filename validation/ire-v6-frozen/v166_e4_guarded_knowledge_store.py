"""V166 E4 fail-closed official research knowledge store.

Enforces E4 approval at the durable V128 SQLite write boundary even if a
caller invokes historical V128/E3 code directly with the guarded store.
The ordinary legacy PrivateKnowledgeStore remains research-candidate only
and is NOT an E4-certified production store.

This is an application-level SQL authorizer, not tamper-proof against a
process deliberately opening the same SQLite file outside this class.
"""
from __future__ import annotations

from contextlib import contextmanager
import sqlite3

from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.codec import json_digest
from v126_chat_approved_knowledge_store import PrivateKnowledgeStore


class E4GuardedKnowledgeStore(PrivateKnowledgeStore):
    """Separate official route; no durable ADD without all E4 child passes."""

    def __init__(self, path):
        self._e4_context = None
        super().__init__(path)

    def _connect(self):
        con = super()._connect()
        def authorize(action, arg1, arg2, database, origin):
            # SQLite authorizer is evaluated for each newly prepared write.
            # Staged V128 child validation uses an isolated disposable base
            # class, but the FINAL durable COMMIT passes this protected store.
            if action in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE,
                          sqlite3.SQLITE_DELETE) and arg1 in {
                              "events", "knowledge", "parent_publications",
                          }:
                scope=self._e4_context
                if (scope is None or
                    set(scope["approved"]) != set(scope["expected"]) or
                    not all(x["status"] ==
                            "E4_PASS_RESEARCH_CANDIDATES_ONLY"
                            for x in scope["approved"].values())):
                    return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        con.set_authorizer(authorize)
        return con

    @contextmanager
    def begin_e4_parent_approval(self, child_ids):
        if (self._e4_context is not None or type(child_ids) not in (list,tuple)
            or not child_ids or len(set(child_ids)) != len(child_ids)):
            raise InvalidInput("V166_E4_PARENT_APPROVAL_SCOPE_INVALID")
        self._e4_context={"expected":tuple(child_ids),"approved":{}}
        try:
            yield self
        finally:
            self._e4_context=None

    def record_e4_validated_child(self, child_id, verified, case):
        scope=self._e4_context
        if scope is None or child_id not in scope["expected"] or child_id in scope["approved"]:
            raise InvalidInput("V166_E4_CHILD_APPROVAL_OUT_OF_SCOPE_OR_REPLAY")
        if (type(verified) is not dict or
            verified.get("schema") !=
                "IRE_V166_E4_VERIFIED_RESEARCH_CANDIDATE_GATE_V1" or
            verified.get("status")!="E4_PASS_RESEARCH_CANDIDATES_ONLY" or
            verified.get("research_export_authorized") is not True or
            verified.get("source_sha256")!=case["source"].source_sha256 or
            verified.get("host_event_sha256")!=case["host_receipt"]["event_sha256"] or
            verified.get("chat_review_sha256")!=json_digest(case["chat_review"]) or
            type(verified.get("typed_source_inventory_sha256")) is not str or
            len(verified["typed_source_inventory_sha256"])!=64 or
            type(verified.get("typed_nonlegal_manifest_sha256")) is not str or
            len(verified["typed_nonlegal_manifest_sha256"])!=64 or
            verified.get("native_v123_status") !=
                "CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY" or
            type(verified.get("primary_manifest_sha256")) is not str or
            len(verified["primary_manifest_sha256"])!=64 or
            type(verified.get("approved_research_candidate_claims")) is not int or
            verified["approved_research_candidate_claims"]<1 or
            verified.get("personal_advice_approved") is not False or
            verified.get("formal_financial_fact_approved") is not False):
            raise QualityNotProven("V166_E4_CHILD_UNVERIFIED_PRIMARY_RELEASE")
        scope["approved"][child_id]={
            "status":verified["status"],
            "host_event_sha256":verified["host_event_sha256"],
            "source_sha256":verified["source_sha256"],
            "primary_manifest_sha256":verified["primary_manifest_sha256"],
            "typed_source_inventory_sha256":verified["typed_source_inventory_sha256"],
            "typed_nonlegal_manifest_sha256":verified["typed_nonlegal_manifest_sha256"],
            "chat_review_sha256":verified["chat_review_sha256"],
        }
