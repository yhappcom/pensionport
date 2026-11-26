"""V126 private append-only incremental research knowledge store (NOT P0-GO).

Only the V123 real ChatGPT final review gate may authorize a batch. The
SQLite file contains PRIVATE source quotations; never commit it to GitHub.
A SHA event chain detects ordinary corruption, not malicious whole-file rewrite
without a separately held owner checkpoint. Advisory access is evidence-only.
"""
from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from ire.v6.codec import canonical, json_digest, sha256, ZERO_SHA
from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.prior_knowledge import audit_prior_candidates
from v123_chat_final_gate import require_chat_final_release

RELATIONS = {"NEW", "SAME", "EXTENDS", "CONFLICT"}
PENDING = {"NEW": {"NOVEL_PENDING", "DISTINCT_PENDING"},
           "SAME": {"SAME_PENDING"}, "EXTENDS": {"EXTENDS_PENDING"},
           "CONFLICT": {"CONFLICT_PENDING"}}
SHA = re.compile(r"[a-f0-9]{64}\Z")
TOPIC = re.compile(r"[0-9A-Za-z가-힣]{2,}")


def _stop(code):
    raise QualityNotProven("V126_" + code)


def _digest(obj):
    return json_digest(obj)


class PrivateKnowledgeStore:
    """Private cumulative knowledge; frozen Master/P4 are read-only relations."""
    def __init__(self, path, *, parent_staging_only=False):
        self.path = Path(path)
        if type(parent_staging_only) is not bool:
            raise InvalidInput("V126_PARENT_STAGING_FLAG_INVALID")
        if parent_staging_only and (
            self.path.name != "staging.db" or
            not self.path.parent.name.startswith("v128_staging_")
        ):
            raise InvalidInput("V126_PARENT_STAGING_MUST_BE_DISPOSABLE_PRIVATE_PATH")
        self._parent_staging_only = parent_staging_only
        if self.path.suffix not in {".db", ".sqlite"}:
            raise InvalidInput("V126_PRIVATE_DB_FILE_REQUIRED")
        if not self.path.parent.is_dir():
            raise InvalidInput("V126_PRIVATE_DB_PARENT_REQUIRED")
        con = self._connect()
        try:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS knowledge(
                    knowledge_id TEXT PRIMARY KEY, entry_json TEXT NOT NULL,
                    entry_sha256 TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events(
                    seq INTEGER PRIMARY KEY, kind TEXT NOT NULL,
                    knowledge_id TEXT NOT NULL, record_sha256 TEXT NOT NULL,
                    prev_sha256 TEXT NOT NULL, event_sha256 TEXT NOT NULL);
            """)
        finally:
            con.close()

    def _connect(self):
        con = sqlite3.connect(str(self.path), timeout=10)
        con.execute("PRAGMA busy_timeout=10000")
        con.execute("PRAGMA foreign_keys=ON")
        return con

    @contextmanager
    def _session(self):
        con=self._connect()
        try:
            with con:
                yield con
        finally:
            con.close()

    @staticmethod
    def _audit(con):
        rows = con.execute("SELECT * FROM events ORDER BY seq").fetchall()
        entries = con.execute("SELECT knowledge_id,entry_json,entry_sha256 FROM knowledge").fetchall()
        indexed = {}
        for kid, raw, digest in entries:
            try:
                obj = json.loads(raw)
                if obj.get("knowledge_id") != kid or _digest(obj) != digest:
                    _stop("PRIVATE_KNOWLEDGE_ROW_DRIFT")
            except (ValueError, TypeError):
                _stop("PRIVATE_KNOWLEDGE_ROW_NOT_CANONICAL")
            indexed[kid] = (obj, digest)
        prev = ZERO_SHA
        state = {}
        for pos, (seq, kind, kid, record_sha, prior, event_sha) in enumerate(rows, 1):
            if seq != pos or prior != prev or kind not in {"ADD", "REVOKE"}:
                _stop("EVENT_SEQUENCE_OR_HEAD_DRIFT")
            frame = {"seq": seq, "kind": kind, "knowledge_id": kid,
                     "record_sha256": record_sha, "prev_sha256": prior}
            if event_sha != _digest(frame):
                _stop("EVENT_HASH_CHAIN_DRIFT")
            if kind == "ADD":
                if kid in state or kid not in indexed or indexed[kid][1] != record_sha:
                    _stop("ENTRY_EVENT_MISSING_OR_REWRITTEN")
                state[kid] = "ACTIVE"
            elif kid not in state or state[kid] == "REVOKED" or not SHA.fullmatch(record_sha):
                _stop("INVALID_REVOCATION_EVENT")
            else:
                state[kid] = "REVOKED"
            prev = event_sha
        if set(state) != set(indexed):
            _stop("ENTRY_NOT_IN_EVENT_LOG")
        return prev, state

    @staticmethod
    def _event(con, kind, kid, record_sha, prev):
        seq = con.execute("SELECT COUNT(*) FROM events").fetchone()[0] + 1
        frame = {"seq": seq, "kind": kind, "knowledge_id": kid,
                 "record_sha256": record_sha, "prev_sha256": prev}
        head = _digest(frame)
        con.execute("INSERT INTO events VALUES(?,?,?,?,?,?)",
                    (seq,kind,kid,record_sha,prev,head))
        return head

    def audit(self, *, externally_pinned_head=None):
        with self._session() as con:
            head, state = self._audit(con)
            # A knowledge event chain alone does not attest the separate V128
            # all-child parent ChatGPT publication receipt. Recheck it on
            # *every* knowledge audit; a changed parent proof must not be
            # silently treated as a still-approved research source.
            # Historical V126 *full-video* knowledge needs no V128 parent
            # table. A read-only audit/query must not create a new table.
            # V128 parent publication receipts are fully replayed whenever
            # that table actually exists.
            if con.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' "
                    "AND name='parent_publications'").fetchone():
                from v128_atomic_parent_knowledge import _replay_parent_publications
                _replay_parent_publications(con, head)
        if externally_pinned_head is not None and head != externally_pinned_head:
            _stop("EXTERNAL_HEAD_CHECKPOINT_DRIFT")
        return {"schema":"IRE_V126_PRIVATE_KNOWLEDGE_AUDIT_V1",
                "head_sha256":head,"active_claims":sum(v=="ACTIVE" for v in state.values()),
                "revoked_claims":sum(v=="REVOKED" for v in state.values()),
                "externally_anchored_checkpoint_verified":externally_pinned_head is not None,
                "independent_semantic_accuracy_certified":False,"p0_go":False}

    def add_chat_final_batch(self, source, exchange, prior_knowledge, *,
                             host_receipt, chat_review, source_store,
                             official_evidence_bodies, relation_decisions,
                             expected_knowledge_head,
                             original_host_batch_replay_args):
        """All-or-nothing exact ChatGPT-vetted candidate accumulation.

        Every claim must have one source-bound, explicit ChatGPT relationship
        decision in addition to V6's pending prior relation. Existing private
        knowledge can be referenced only by its exact immutable ID.
        """
        # The older per-child API may never publish a partial long-video
        # source scope directly. Only V128's disposable, private parent
        # staging clone may accept partial children pending whole-parent COMMIT.
        if (source.scope_first_cue != 1 or
                source.scope_last_cue != len(source.cues)) and not self._parent_staging_only:
            _stop("PARTIAL_SOURCE_REQUIRES_FULL_PARENT_ATOMIC_PUBLICATION")
        gate = require_chat_final_release(
            source, exchange, host_receipt=host_receipt, chat_review=chat_review,
            store=source_store, official_evidence_bodies=official_evidence_bodies)
        prior = audit_prior_candidates(source, exchange, prior_knowledge)
        # Bind the *same* original prior relation list to the real V6 batch
        # commitment, not merely to a separate, replaceable ChatGPT input.
        # The V6 idempotent replay returns the original bundle and event SHA
        # only if every model, source, owner pin and relation byte still match.
        replay = original_host_batch_replay_args
        base_keys = {"scope_id", "run_id", "expected_head", "raw", "manifest",
                     "inventory_bytes", "expected_inventory_sha256", "exchange",
                     "knowledge", "window_models", "window_reviews"}
        formal = host_receipt.get("formal_typed_transition_pin")
        if type(replay) is not dict:
            _stop("SOURCE_HOST_BATCH_REPLAY_INPUT_DRIFT")
        if formal is not None:
            if (set(replay) != base_keys | {"typed_predecessor", "formal_typed_transition"} or
                    replay["formal_typed_transition"] is not True or
                    replay["typed_predecessor"] != formal["predecessor_event_sha256"] or
                    replay["expected_head"] != formal["predecessor_event_sha256"]):
                _stop("SOURCE_HOST_BATCH_REPLAY_INPUT_DRIFT")
        elif set(replay) not in (base_keys, base_keys | {"quarantine_preflight"}):
            _stop("SOURCE_HOST_BATCH_REPLAY_INPUT_DRIFT")
        if (replay["knowledge"] != prior_knowledge or replay["exchange"] != exchange or
                replay["scope_id"] != host_receipt["scope_id"]):
            _stop("SOURCE_HOST_BATCH_REPLAY_INPUT_DRIFT")
        rechecked = source_store.submit_host_atomic_batch(**replay)
        if (rechecked["idempotent_replay"] is not True or
                rechecked["is_current"] is not True or
                rechecked["event_sha256"] != host_receipt["event_sha256"] or
                rechecked["bundle_sha256"] != host_receipt["bundle_sha256"] or
                rechecked.get("formal_typed_transition_pin") != formal):
            _stop("SOURCE_HOST_BUNDLE_NOT_EXACT_REPLAY")
        if gate["status"] != "CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY":
            _stop("CHAT_FINAL_NOT_PASSED")
        if type(expected_knowledge_head) is not str or not SHA.fullmatch(expected_knowledge_head):
            raise InvalidInput("V126_EXPECTED_HEAD_REQUIRED")
        atoms = {a["claim_id"]: a for a in exchange["atoms"]}
        pending = {}
        for row in prior_knowledge["relations"]:
            pending.setdefault(row["claim_id"], []).append(row)
        if (type(relation_decisions) is not list or
                len(relation_decisions) != len(atoms)):
            _stop("CHAT_RELATION_CENSUS_MISSING")
        decisions = {}
        for d in relation_decisions:
            if type(d) is not dict or set(d) != {
                "claim_id", "atom_sha256", "relation", "target_kind",
                "target_id", "private_chat_relation_review_sha256"
            }:
                _stop("CHAT_RELATION_SCHEMA_INVALID")
            cid = d["claim_id"]
            if (cid not in atoms or cid in decisions or d["atom_sha256"] != _digest(atoms[cid])
                    or d["relation"] not in RELATIONS or type(d["private_chat_relation_review_sha256"]) is not str
                    or not SHA.fullmatch(d["private_chat_relation_review_sha256"])):
                _stop("CHAT_RELATION_SOURCE_OR_DUPLICATE")
            decisions[cid] = d
        if set(decisions) != set(atoms):
            _stop("CHAT_RELATION_MISSING_ATOM")
        finance = {r["claim_id"]:r["financial_claim"] for r in chat_review["atom_verdicts"]}
        accepted_ids = {r["claim_id"] for r in chat_review["atom_verdicts"]
                        if r["status"] == "ACCEPT_FOR_RESEARCH"}
        excluded_ids = set(gate.get("quarantined_claim_ids", []))
        if accepted_ids != set(atoms) - excluded_ids:
            _stop("APPROVED_SUBSET_NOT_BOUND_TO_FINAL_CHAT_QUARANTINE")
        with self._session() as con:
            con.execute("BEGIN IMMEDIATE")
            head, statuses = self._audit(con)
            current = {x[0]:json.loads(x[1]) for x in con.execute(
                "SELECT knowledge_id,entry_json FROM knowledge")}
            entries = []
            for cid in sorted(accepted_ids):
                atom, decision = atoms[cid], decisions[cid]
                candidates = pending.get(cid, [])
                if len(candidates) != 1:
                    _stop("MULTI_PRIOR_RELATION_REQUIRES_EXPLICIT_RESOLUTION")
                d = decision
                kind, target = d["target_kind"], d["target_id"]
                relation = d["relation"]
                if relation == "NEW":
                    if (kind != "NONE" or target is not None or
                            candidates[0]["relationship"] not in PENDING[relation]):
                        _stop("NOVEL_RELATION_WITH_PRIOR_CONFLICT")
                    concept = None
                elif kind == "CUMULATIVE":
                    if (type(target) is not str or target not in current or
                            statuses[target] != "ACTIVE" or target in [e["knowledge_id"] for e in entries]):
                        _stop("CUMULATIVE_TARGET_MISSING_OR_REVOKED")
                    if candidates[0]["relationship"] not in PENDING["NEW"]:
                        _stop("LEGACY_CONFLICT_CANNOT_BE_IGNORED")
                    concept = current[target]["concept_id"] if relation == "SAME" else None
                elif kind in {"MASTER116", "P4_EDUCATION"}:
                    if (type(target) is not str or not any(
                         row["target_kind"] == kind and row["target_id"] == target and
                         row["relationship"] in PENDING[relation] for row in candidates)):
                        _stop("LEGACY_RELATION_TARGET_NOT_SOURCE_AUDITED")
                    concept = None  # no protected master/P4 mutation
                else:
                    _stop("RELATION_TARGET_INVALID")
                kid = _digest({"video_id":source.video_id,
                               "source_sha256":source.source_sha256,
                               "claim_id":cid,"atom_sha256":_digest(atom)})
                if concept is None:
                    concept = kid
                if relation != "SAME" and any(
                        obj["atom"]["proposition"].strip() == atom["proposition"].strip()
                        and obj["knowledge_id"] != kid for obj in current.values()):
                    _stop("SAME_TEXT_NEEDS_EQUIVALENCE_REVIEW")
                entry = {"schema":"IRE_V126_CHAT_VETTED_CANDIDATE_V1",
                         "knowledge_id":kid,"concept_id":concept,
                         "video_id":source.video_id,"source_sha256":source.source_sha256,
                         "manifest_sha256":source.manifest_sha256,
                         "host_event_sha256":host_receipt["event_sha256"],
                         "chat_review_sha256":gate["chat_final_review_digest_sha256"],
                         "claim_id":cid,"atom":atom,
                         "relation":relation,"target_kind":kind,"target_id":target,
                         "relation_review_sha256":d["private_chat_relation_review_sha256"],
                         "finance_current_law_review_required":bool(finance[cid]),
                         "research_candidate_only":True,
                         "personal_advice_approved":False}
                entries.append(entry)
            if not entries:
                if head != expected_knowledge_head:
                    _stop("NO_APPROVED_CHILD_HEAD_CHANGED")
                # No publication/event for a child with only explicit exclusions.
                # V128 can still commit other children in its final transaction.
                return {"status": "CHILD_ALL_CLAIMS_EXCLUDED_NO_KNOWLEDGE_WRITE",
                        "knowledge_head_sha256": head, "entries": 0,
                        "idempotent_replay": False, "p0_go": False}
            prior_complete = all(e["knowledge_id"] in current and
                                 current[e["knowledge_id"]] == e for e in entries)
            if prior_complete:
                return {"status":"IDEMPOTENT_V126_PRIVATE_RESEARCH_BATCH",
                        "knowledge_head_sha256":head,"entries":len(entries),
                        "idempotent_replay":True,"p0_go":False}
            if head != expected_knowledge_head:
                _stop("KNOWLEDGE_EXPECTED_HEAD_CHANGED")
            if any(e["knowledge_id"] in current for e in entries):
                _stop("PARTIAL_OR_CHANGED_BATCH_NOT_ALLOWED")
            for entry in entries:
                kid = entry["knowledge_id"]
                raw = canonical(entry).decode("utf-8")
                digest = _digest(entry)
                con.execute("INSERT INTO knowledge VALUES(?,?,?)",(kid,raw,digest))
                head = self._event(con,"ADD",kid,digest,head)
            con.commit()
            return {"schema":"IRE_V126_PRIVATE_APPEND_ONLY_CHAT_APPROVED_V1",
                    "status":"RESEARCH_CANDIDATES_STORED_NOT_FORMAL_FINANCIAL_FACTS",
                    "knowledge_head_sha256":head,"entries":len(entries),
                    "chat_final_gate_passed":True,"idempotent_replay":False,
                    "master116_p4_untouched":True,"financial_fact_formal_approval":0,
                    "personal_advice_approved":False,"p0_go":False}

    def revoke(self, knowledge_id, *, chat_review_sha256, expected_knowledge_head):
        """Tombstone without deleting immutable history or making user advice."""
        if self._parent_staging_only:
            _stop("UNPUBLISHED_PARENT_STAGING_CANNOT_REVOKE")
        if not all(type(x) is str and SHA.fullmatch(x or "")
                   for x in (knowledge_id,chat_review_sha256,expected_knowledge_head)):
            raise InvalidInput("V126_REVOCATION_REQUIRES_VALID_SHA_PINS")
        with self._session() as con:
            con.execute("BEGIN IMMEDIATE")
            head, states = self._audit(con)
            if head != expected_knowledge_head or states.get(knowledge_id) != "ACTIVE":
                _stop("REVOCATION_HEAD_OR_TARGET_DRIFT")
            # Review SHA must be separately generated by the ChatGPT final reviewer.
            head = self._event(con,"REVOKE",knowledge_id,chat_review_sha256,head)
            con.commit()
        return {"status":"PRIVATE_KNOWLEDGE_TOMBSTONED","head_sha256":head,
                "p0_go":False}

    def evidence_for_question(self, question, *, selected_knowledge_ids=None, max_items=12):
        """Private context for ChatGPT, NOT a generated financial recommendation.

        Lexical scores support discovery only. ChatGPT must independently
        check relevant sources, up-to-date primary law and current facts.
        """
        if self._parent_staging_only:
            _stop("UNPUBLISHED_PARENT_STAGING_NOT_QUERYABLE")
        if type(question) is not str or not question.strip() or len(question)>4000:
            raise InvalidInput("V126_QUESTION_REQUIRED")
        if type(max_items) is not int or not 1<=max_items<=30:
            raise InvalidInput("V126_QUERY_LIMIT_INVALID")
        if selected_knowledge_ids is not None and (
            type(selected_knowledge_ids) is not list or
            len(selected_knowledge_ids)>max_items or
            any(type(x) is not str or not SHA.fullmatch(x) for x in selected_knowledge_ids) or
            selected_knowledge_ids!=sorted(set(selected_knowledge_ids))):
            raise InvalidInput("V126_SELECTED_KNOWLEDGE_IDS_INVALID")
        with self._session() as con:
            head, statuses = self._audit(con)
            # Protect the advice-retrieval path from using rows whose parent
            # all-segment release receipt has been modified or detached from
            # its original V6 event-chain boundaries.
            # Historical V126 *full-video* knowledge needs no V128 parent
            # table. A read-only audit/query must not create a new table.
            # V128 parent publication receipts are fully replayed whenever
            # that table actually exists.
            if con.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' "
                    "AND name='parent_publications'").fetchone():
                from v128_atomic_parent_knowledge import _replay_parent_publications
                _replay_parent_publications(con, head)
            entries = [json.loads(v[0]) for v in con.execute("SELECT entry_json FROM knowledge")]
            # A newly detected cross-video conflict must quarantine the old
            # active target too. Review-only status never becomes auto approval.
            from v127_cumulative_knowledge_graph import inspect_cumulative_knowledge_graph
            graph = inspect_cumulative_knowledge_graph(entries, statuses)
        approved_for_lookup = set(graph["active_knowledge_ids"])
        active = {x["knowledge_id"]:x for x in entries
                  if x["knowledge_id"] in approved_for_lookup}
        if selected_knowledge_ids is not None:
            if not set(selected_knowledge_ids) <= active.keys():
                _stop("QUESTION_REFERENCES_UNVERIFIED_OR_QUARANTINED_KNOWLEDGE")
            found = [active[k] for k in selected_knowledge_ids]
        else:
            words = set(TOPIC.findall(question.casefold()))
            scored = [(len(words.intersection(set(TOPIC.findall(x["atom"]["proposition"].casefold())))),x)
                      for x in active.values()]
            found = [x for n,x in sorted(scored,key=lambda pair:(-pair[0],pair[1]["knowledge_id"]))
                     if n>0][:max_items]
        return {"schema":"IRE_V126_PRIVATE_CHAT_ADVISORY_EVIDENCE_PACKET_V1",
                "question_sha256":sha256(question.encode("utf-8")),
                "knowledge_head_sha256":head,
                "claims":found,"count":len(found),
                "financial_claims_requiring_current_primary_source":sum(
                    x["finance_current_law_review_required"] for x in found),
                "chat_question_relevance_not_independently_verified":True,
                "requires_live_official_source_recheck":True,
                "chatgpt_final_answer_review_required":True,
                "research_candidate_not_formal_financial_fact":True,
                "no_auto_personal_advice":True,"p0_go":False,
                "status":"HOST_CHAT_EVIDENCE_REVIEW_REQUIRED"}
