"""V126 private append-only incremental research knowledge store (NOT P0-GO).

Only the V123 real ChatGPT final review gate may authorize a batch. The
SQLite file contains PRIVATE source quotations; never commit it to GitHub.
A SHA event chain detects ordinary corruption, not malicious whole-file rewrite
without a separately held owner checkpoint. Advisory access is evidence-only.
"""
from __future__ import annotations

import json
import math
from collections import Counter
import re
import sqlite3
from contextlib import contextmanager, closing, ExitStack
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



# Lexical discovery only: Korean particles and character n-grams recover
# inflected and compound terms without a model, per-question ID list or API.
# Common corpus terms carry no discriminative weight. No synonym/semantic
# equivalence is asserted; the returned packet still needs ChatGPT review.
_QUERY_STOP = frozenset("화자는 화자 설명한다 설명하고 설명 소개한다 소개 권고한다 경고한다 무엇인가요 어떻게 무엇 어떤 되나요 있나요 같나요 하나요 인가요 나요 가요 되는 경우 있다고 있다 수 것 같은 대한 관련 그리고 따라 하는 한다 이다 되는지 있습니까 입니까 문의 알려주세요".split())
_QUERY_SUFFIX = ("으로부터", "에게서", "에서는", "으로는", "이라면", "한다면", "이면", "이라고", "으로", "에서", "에게", "까지", "부터", "보다", "처럼", "하고", "이며", "이나", "과", "와", "의", "이", "가", "은", "는", "을", "를", "도", "만", "에")
_QUERY_WORD = re.compile(r"[가-힣]+|[a-z]+|[0-9]+(?:\.[0-9]+)?%?")


def _discovery_features(text):
    features = {}
    for word in _QUERY_WORD.findall(text.casefold()):
        if word in _QUERY_STOP or len(word) < 2:
            continue
        if re.fullmatch(r"[가-힣]+", word):
            for suffix in _QUERY_SUFFIX:
                if word.endswith(suffix) and len(word)-len(suffix) >= 2:
                    word = word[:-len(suffix)]
                    break
            if word in _QUERY_STOP:
                continue
            features["w:"+word] = 20
            for n, weight in ((2, 10), (3, 13)):
                for i in range(len(word)-n+1):
                    features[str(n)+":"+word[i:i+n]] = weight
        else:
            features["w:"+word] = 20
    return features


def _rank_research_context(question, active, corrections, max_items):
    # Source quotes and rejected proposition are discovery text, not an
    # endorsement. Returned correction rows preserve their separate attribution.
    docs = [("SOURCE", row["knowledge_id"], row,
             row["atom"]["proposition"]+" "+" ".join(ref["quote"] for ref in row["atom"]["source_refs"]))
            for row in active.values()]
    docs += [("EXTERNAL", (row["batch_sha256"]+":" if "batch_sha256" in row else "")+row["claim_id"], row,
              row["external_statement"]+" "+row["original_atom"]["proposition"])
             for row in corrections]
    corpus = [(kind, key, row, _discovery_features(text)) for kind,key,row,text in docs]
    df = Counter(term for _,_,_,features in corpus for term in features)
    n = len(corpus)
    weights = {term: int(weight*1000*math.log1p((n+0.5)/(df[term]+0.5)))
               for term,weight in _discovery_features(question).items()
               if n and df[term]*100 < n*65}
    denominator = sum(weights.values())
    ranked = {"SOURCE": [], "EXTERNAL": []}
    if denominator:
        for kind,key,row,features in corpus:
            score = sum(weights[t] for t in features.keys() & weights.keys())*10000//denominator
            if score:
                ranked[kind].append((score,key,row))
    selected = {}
    diagnostics = {}
    for kind, rows in ranked.items():
        rows.sort(key=lambda item: (-item[0],item[1]))
        # A conservative absolute coverage floor and relative-to-category
        # cutoff; neither is a probability of correctness or semantic score.
        floor = max(800, rows[0][0]//4) if rows else 800
        hits = [x for x in rows if x[0]>=floor][:max_items]
        selected[kind] = [row for _,_,row in hits]
        diagnostics[kind] = [{"id":key,"lexical_score_basis_points":score} for score,key,_ in hits]
    return selected["SOURCE"], selected["EXTERNAL"], {
        "method":"CORPUS_WEIGHTED_KOREAN_LEXICAL_DISCOVERY_V1",
        "active_source_candidates_scanned":len(active),
        "external_correction_candidates_scanned":len(corrections),
        "max_items_per_category":max_items,"ranked":diagnostics,
        "automatic_id_selection":True,"semantic_relevance_certified":False,
        "requires_chat_relevance_review":True}


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
                             original_host_batch_replay_args, source_revision_extension=False):
        """All-or-nothing exact ChatGPT-vetted candidate accumulation.

        Every claim must have one source-bound, explicit ChatGPT relationship
        decision in addition to V6's pending prior relation. Existing private
        knowledge can be referenced only by its exact immutable ID.
        An explicit full-source native successor may add newly approved candidates
        while retaining every older active row byte-for-byte; never replace a row.
        """
        if type(source_revision_extension) is not bool:
            raise InvalidInput("V126_EXTENSION_FLAG_INVALID")
        if source_revision_extension and (self._parent_staging_only or
                source.scope_first_cue != 1 or source.scope_last_cue != len(source.cues) or
                type(host_receipt) is not dict or
                host_receipt.get("formal_typed_transition_pin") is not None):
            _stop("EXTENSION_ONLY_LEGACY_FULL_SOURCE_NATIVE")
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
        revision = host_receipt.get("private_chat_revision_sha256")
        if type(replay) is not dict:
            _stop("SOURCE_HOST_BATCH_REPLAY_INPUT_DRIFT")
        legacy_keys = (base_keys, base_keys | {"quarantine_preflight"})
        if formal is not None:
            if (revision is not None or set(replay) != base_keys | {"typed_predecessor", "formal_typed_transition"} or
                    replay["formal_typed_transition"] is not True or
                    replay["typed_predecessor"] != formal["predecessor_event_sha256"] or
                    replay["expected_head"] != formal["predecessor_event_sha256"]):
                _stop("SOURCE_HOST_BATCH_REPLAY_INPUT_DRIFT")
        elif revision is not None:
            # Follow the exact committed predecessor chain to its legacy root.
            # A later revision must not lose or invent an earlier "before".
            # Check every seal exists before calling the write-capable replay API.
            from ire.v6.store import TransactionStore
            from ire.v6.host_batch import read_host_chat_revision
            extras = {"chat_revision", "revision_predecessor_replay_args"}
            revision_keys = tuple(keys | extras for keys in legacy_keys)
            if (not isinstance(source_store, TransactionStore) or
                    type(revision) is not str or not SHA.fullmatch(revision) or
                    set(replay) not in revision_keys):
                _stop("SOURCE_HOST_REVISION_REPLAY_INPUT_DRIFT")
            chain = []
            node = replay
            event_sha = host_receipt["event_sha256"]
            seen = set()
            with closing(source_store._connection()) as native:
                native.execute("BEGIN")
                source_store._replay(native, replay["scope_id"])
                while True:
                    if (type(node) is not dict or type(node.get("run_id")) is not str or
                            node["run_id"] in seen):
                        _stop("SOURCE_HOST_REVISION_PREDECESSOR_INPUT_DRIFT")
                    seen.add(node["run_id"])
                    row = native.execute("SELECT event_sha256,event_json FROM events "
                        "WHERE scope_id=? AND command_id=?",
                        (replay["scope_id"], node["run_id"]+"_seal")).fetchone()
                    if row is None or row["event_sha256"] != event_sha:
                        _stop("SOURCE_HOST_REVISION_PREDECESSOR_NOT_EXACT_REPLAY")
                    marker = json.loads(row["event_json"]).get("payload", {}).get("review", {})
                    if ("formal_typed_transition_pin" in marker or
                            "private_typed_staging_record" in marker):
                        _stop("SOURCE_HOST_REVISION_PREDECESSOR_INPUT_DRIFT")
                    pin = marker.get("private_chat_revision_sha256")
                    if not chain and pin != revision:
                        _stop("SOURCE_HOST_REVISION_NOT_EXACT_REPLAY")
                    if pin is None:
                        if set(node) not in legacy_keys:
                            _stop("SOURCE_HOST_REVISION_PREDECESSOR_INPUT_DRIFT")
                        chain.append((node, event_sha, None))
                        break
                    if set(node) not in revision_keys:
                        _stop("SOURCE_HOST_REVISION_PREDECESSOR_INPUT_DRIFT")
                    change = node["chat_revision"]
                    predecessor = node["revision_predecessor_replay_args"]
                    if (type(predecessor) is not dict or
                            set(predecessor) not in (*legacy_keys, *revision_keys) or
                            type(change) is not dict or change.get("before") != predecessor["exchange"] or
                            any(predecessor[k] != node[k] for k in ("scope_id", "raw", "manifest",
                                "inventory_bytes", "expected_inventory_sha256"))):
                        _stop("SOURCE_HOST_REVISION_PREDECESSOR_INPUT_DRIFT")
                    chain.append(({k:v for k,v in node.items()
                        if k != "revision_predecessor_replay_args"}, event_sha, pin))
                    event_sha = node["expected_head"]
                    node = predecessor
            # All run IDs refer to immutable committed seals. No missing run
            # can create an event during these idempotent replay calls.
            for i, (args, event_sha, pin) in enumerate(chain):
                current = i == 0
                if pin is not None:
                    native_revision = read_host_chat_revision(source_store,
                        scope_id=args["scope_id"], run_id=args["run_id"], raw=args["raw"],
                        manifest=args["manifest"], inventory_bytes=args["inventory_bytes"],
                        expected_inventory_sha256=args["expected_inventory_sha256"])
                    if (native_revision.get("is_current") is not current or
                            native_revision.get("event_sha256") != event_sha or
                            native_revision.get("private_chat_revision_sha256") != pin or
                            native_revision["record"]["inputs"] != args["chat_revision"] or
                            native_revision["record"]["result"]["exchange"] != args["exchange"]):
                        _stop("SOURCE_HOST_REVISION_NOT_EXACT_REPLAY")
                if not current:
                    old = source_store.submit_host_atomic_batch(**args)
                    if (old.get("idempotent_replay") is not True or old.get("is_current") is not False or
                            old.get("event_sha256") != event_sha or
                            old.get("private_chat_revision_sha256") != pin):
                        _stop("SOURCE_HOST_REVISION_PREDECESSOR_NOT_EXACT_REPLAY")
            replay = chain[0][0]
        elif set(replay) not in legacy_keys:
            _stop("SOURCE_HOST_BATCH_REPLAY_INPUT_DRIFT")
        if (replay["knowledge"] != prior_knowledge or replay["exchange"] != exchange or
                replay["scope_id"] != host_receipt["scope_id"]):
            _stop("SOURCE_HOST_BATCH_REPLAY_INPUT_DRIFT")
        rechecked = source_store.submit_host_atomic_batch(**replay)
        if (rechecked["idempotent_replay"] is not True or
                rechecked["is_current"] is not True or
                rechecked["event_sha256"] != host_receipt["event_sha256"] or
                rechecked["bundle_sha256"] != host_receipt["bundle_sha256"] or
                rechecked.get("formal_typed_transition_pin") != formal or
                rechecked.get("private_chat_revision_sha256") != revision):
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
        with self._session() as con, ExitStack() as locks:
            con.execute("BEGIN IMMEDIATE")
            head, statuses = self._audit(con)
            current = {x[0]:json.loads(x[1]) for x in con.execute(
                "SELECT knowledge_id,entry_json FROM knowledge")}
            if revision is not None and not source_revision_extension:
                native = locks.enter_context(closing(source_store._connection()))
                native.execute("BEGIN IMMEDIATE")
                _, _, source_head = source_store._replay(native, replay["scope_id"])
                if source_head != host_receipt["event_sha256"]:
                    _stop("SOURCE_HOST_REVISION_HEAD_CHANGED")
            if source_revision_extension:
                # The original full-source candidate store only. Parent releases
                # have a separate atomic publication contract, never this path.
                if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                               "AND name='parent_publications'").fetchone():
                    _stop("EXTENSION_PARENT_PUBLICATION_STORE_FORBIDDEN")
                from ire.v6.store import TransactionStore
                from ire.v6.host_batch import MARKER_SCHEMA
                if not isinstance(source_store, TransactionStore):
                    _stop("EXTENSION_NATIVE_STORE_REQUIRED")
                # Hold source writer reservation across the knowledge commit;
                # avoid a concurrent source revision changing the approved head.
                native = locks.enter_context(closing(source_store._connection()))
                native.execute("BEGIN IMMEDIATE")
                _, _, source_head = source_store._replay(native, replay["scope_id"])
                if source_head != host_receipt["event_sha256"]:
                    _stop("EXTENSION_SOURCE_HEAD_CHANGED")
                seals = {}
                for row in native.execute("SELECT event_sha256,event_json,sequence FROM events "
                                          "WHERE scope_id=? ORDER BY sequence", (replay["scope_id"],)):
                    event = json.loads(row["event_json"])
                    marker = event.get("payload", {}).get("review", {})
                    if event.get("type") == "REVIEW_PROPOSED" and marker.get("schema") == MARKER_SCHEMA:
                        if (marker.get("source_sha256") != source.source_sha256 or
                                "private_typed_staging_record" in marker or
                                "formal_typed_transition_pin" in marker):
                            _stop("EXTENSION_UNSUPPORTED_SOURCE_HISTORY")
                        seals[row["event_sha256"]] = (row["sequence"], marker)
                predecessor = replay["expected_head"]
                if (predecessor not in seals or source_head not in seals or
                        seals[predecessor][0] >= seals[source_head][0] or
                        seals[source_head][1].get("original_expected_head") != predecessor or
                        seals[source_head][1].get("bundle_sha256") != host_receipt["bundle_sha256"]):
                    _stop("EXTENSION_PREDECESSOR_NOT_NATIVE_SEAL")
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
            if source_revision_extension:
                # A whole-source successor cannot drop, revise, re-activate or
                # change the relationship of an earlier accepted candidate.
                # A source-scoped revocation/replacement is a different operation.
                relevant = {kid: row for kid, row in current.items()
                            if row["video_id"] == source.video_id and
                            row["source_sha256"] == source.source_sha256}
                if not relevant or any(row["manifest_sha256"] != source.manifest_sha256
                                       for row in relevant.values()):
                    _stop("EXTENSION_PRIOR_SCOPE_MISSING_OR_CHANGED")
                proposed = {row["knowledge_id"]: row for row in entries}
                active_prior = {kid for kid in relevant if statuses[kid] == "ACTIVE"}
                if not active_prior or not active_prior <= proposed.keys():
                    _stop("EXTENSION_PRIOR_APPROVAL_DROPPED_OR_CHANGED")
                retained = []
                new_entries = []
                current_seal_matches = 0
                for entry in entries:
                    kid = entry["knowledge_id"]
                    if kid not in current:
                        if any(old["claim_id"] == entry["claim_id"] for old in relevant.values()):
                            _stop("EXTENSION_EXISTING_CLAIM_REPLACEMENT")
                        new_entries.append(entry)
                        continue
                    old = current[kid]
                    if kid not in relevant or statuses[kid] != "ACTIVE":
                        _stop("EXTENSION_PRIOR_ROW_INACTIVE_OR_FOREIGN")
                    prior_seal = old["host_event_sha256"]
                    if prior_seal == source_head:
                        if old != entry:
                            _stop("EXTENSION_CURRENT_ROW_DRIFT")
                        current_seal_matches += 1
                    else:
                        if (prior_seal not in seals or
                                seals[prior_seal][0] > seals[predecessor][0] or
                                {k:v for k,v in old.items() if k not in {"host_event_sha256", "chat_review_sha256"}} !=
                                {k:v for k,v in entry.items() if k not in {"host_event_sha256", "chat_review_sha256"}}):
                            _stop("EXTENSION_PRIOR_ROW_OR_LINEAGE_DRIFT")
                        retained.append(kid)
                if not retained:
                    _stop("EXTENSION_PRIOR_APPROVAL_REQUIRED")
                if not new_entries:
                    if not current_seal_matches:
                        _stop("EXTENSION_NO_NEW_CANDIDATES")
                    return {"status":"IDEMPOTENT_V126_PRIVATE_RESEARCH_BATCH",
                            "knowledge_head_sha256":head,"entries":current_seal_matches,
                            "retained_entries":len(retained),"idempotent_replay":True,"p0_go":False}
                if current_seal_matches:
                    _stop("EXTENSION_PARTIAL_CURRENT_BATCH")
                if head != expected_knowledge_head:
                    _stop("KNOWLEDGE_EXPECTED_HEAD_CHANGED")
                entries = new_entries
            else:
                retained = []
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
                    **({"source_revision_extension":True,"retained_entries":len(retained)}
                       if source_revision_extension else {}),
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

    @staticmethod
    def _correction_origin_rows(rows, origin):
        """Exact issuer-body linkage, not semantic or effective-date certification."""
        for row in rows:
            if not row["evidence"]:
                _stop("CORRECTION_EVIDENCE_REQUIRED")
            for link in row["evidence"]:
                entry = origin["bodies"].get(link["url"])
                if (entry is None or sha256(entry["body"]) != link["body_sha256"]
                        or link["quote"].encode("utf-8") not in entry["body"]):
                    _stop("CORRECTION_ORIGIN_QUOTE_OR_BODY_DRIFT")

    def save_external_correction_context(self, source, exchange, *, host_receipt,
            chat_review, source_store, official_evidence_bodies, origin_archive,
            corrections, expected_knowledge_head):
        """Persist explicitly attributed corrections as research context only.

        An excluded spoken claim remains excluded. An external-source correction
        is not a V123 atom, approved knowledge ADD, or E4/V128 publication.
        No implicit inclusion in ordinary retrieval or protected store subclasses.
        """
        if type(self) is not PrivateKnowledgeStore or self._parent_staging_only:
            _stop("CORRECTION_CONTEXT_RESEARCH_STORE_ONLY")
        from ire.v6.public_origin import replay_public_origin_archive
        gate = require_chat_final_release(source, exchange, host_receipt=host_receipt,
                    chat_review=chat_review, store=source_store,
                    official_evidence_bodies=official_evidence_bodies)
        origin = replay_public_origin_archive(**origin_archive)
        if origin["capture_date"] > chat_review["as_of"]:
            _stop("CORRECTION_CAPTURE_AFTER_REVIEW")
        atoms = {x["claim_id"]:x for x in exchange["atoms"]}
        excluded = set(gate["quarantined_claim_ids"]) & {v["claim_id"] for v in chat_review["atom_verdicts"] if v["status"] == "EXCLUDE_FROM_RESEARCH"}
        audio = set(chat_review.get("quarantine", {}).get("audio_unverified_cue_indices", []))
        if type(corrections) is not list or not 1 <= len(corrections) <= len(excluded):
            _stop("CORRECTION_CENSUS")
        rows, seen = [], set()
        for row in corrections:
            if (type(row) is not dict or set(row) != {"claim_id","atom_sha256",
                    "external_statement","scope_note","evidence"}):
                _stop("CORRECTION_ROW_SCHEMA")
            cid = row["claim_id"]
            if (cid not in excluded or cid in seen or row["atom_sha256"] != _digest(atoms[cid])
                    or audio.intersection(atoms[cid]["context_cue_indices"])):
                _stop("CORRECTION_EXCLUDED_ATOM_IDENTITY_OR_AUDIO")
            if any(type(row[k]) is not str or not 8 <= len(row[k].strip()) <= 3000
                   for k in ("external_statement","scope_note")):
                _stop("CORRECTION_STATEMENT_OR_SCOPE_REQUIRED")
            if type(row["evidence"]) is not list or not 1 <= len(row["evidence"]) <= 10:
                _stop("CORRECTION_EVIDENCE_REQUIRED")
            for link in row["evidence"]:
                if (type(link) is not dict or set(link) != {"url","body_sha256","quote","date_kind"}
                        or link["date_kind"] not in {"UNDATED_GUIDANCE_CAPTURE","DATED_CASE_DISCLOSURE","DATED_POLICY_ANNOUNCEMENT","DATED_LEGAL_TEXT"}
                        or type(link["quote"]) is not str or not 8 <= len(link["quote"].strip()) <= 500
                        or not isinstance(link["body_sha256"], str) or not SHA.fullmatch(link["body_sha256"])):
                    _stop("CORRECTION_EVIDENCE_SCHEMA")
            rows.append({**row,"original_atom":atoms[cid],"original_v123_status":"EXCLUDE_FROM_RESEARCH",
                         "external_not_speaker_quote":True,"formal_financial_fact_approved":False})
            seen.add(cid)
        rows.sort(key=lambda x:x["claim_id"])
        self._correction_origin_rows(rows,origin)
        record = {"schema":"IRE_V126_EXTERNAL_CORRECTION_CONTEXT_V1",
                  "source_sha256":source.source_sha256,"scope_id":host_receipt["scope_id"],
                  "source_head_sha256":host_receipt["event_sha256"],
                  "chat_review_sha256":gate["chat_final_review_digest_sha256"],
                  "as_of":chat_review["as_of"],"origin_archive_sha256":origin["archive_sha256"],
                  "origin_commit":origin["code_commit"],"origin_capture_date":origin["capture_date"],
                  "rows":rows,"research_context_only":True,"formal_financial_fact_approved":False}
        pin = _digest(record)
        with self._session() as con:
            con.execute("BEGIN IMMEDIATE")
            head,_ = self._audit(con)
            if head != expected_knowledge_head or not source_store.is_current(
                    scope_id=record["scope_id"],ledger_head_sha256=record["source_head_sha256"]):
                _stop("CORRECTION_SOURCE_OR_KNOWLEDGE_HEAD_DRIFT")
            con.execute("CREATE TABLE IF NOT EXISTS external_correction_context(batch_sha256 TEXT PRIMARY KEY, record_json TEXT NOT NULL, origin_archive BLOB NOT NULL)")
            prior = con.execute("SELECT record_json,origin_archive FROM external_correction_context WHERE batch_sha256=?",(pin,)).fetchone()
            payload = (canonical(record).decode("utf-8"),origin_archive["raw"])
            if prior is not None and prior != payload:
                _stop("CORRECTION_STORED_CONTEXT_DRIFT")
            if prior is None:
                con.execute("INSERT INTO external_correction_context VALUES(?,?,?)",(pin,*payload))
        return {"batch_sha256":pin,"research_corrections":len(rows),"idempotent_replay":prior is not None,
                "knowledge_head_sha256":head,"approved_knowledge_added":0,"formal_financial_fact_approved":False}

    def _external_correction_context(self, con, context):
        if (type(self) is not PrivateKnowledgeStore or self._parent_staging_only
                or type(context) is not dict or set(context) not in (
                    {"batch_sha256","source_store","claim_ids"}, {"batch_sha256","source_store"})):
            _stop("CORRECTION_CONTEXT_EXPLICIT_RESEARCH_ONLY")
        pin, ids = context["batch_sha256"], context.get("claim_ids")
        automatic = "claim_ids" not in context
        if (type(pin) is not str or not SHA.fullmatch(pin) or (not automatic and (
                type(ids) is not list or not ids or len(ids)>30
                or any(type(x) is not str for x in ids) or ids != sorted(set(ids))))):
            _stop("CORRECTION_CONTEXT_PIN_OR_SELECTION")
        if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='external_correction_context'").fetchone():
            _stop("CORRECTION_CONTEXT_NOT_FOUND")
        row = con.execute("SELECT record_json,origin_archive FROM external_correction_context WHERE batch_sha256=?",(pin,)).fetchone()
        if row is None:
            _stop("CORRECTION_CONTEXT_NOT_FOUND")
        try:
            record = json.loads(row[0])
        except (TypeError,ValueError):
            _stop("CORRECTION_STORED_CONTEXT_DRIFT")
        if _digest(record) != pin:
            _stop("CORRECTION_STORED_CONTEXT_DRIFT")
        if not context["source_store"].is_current(scope_id=record["scope_id"],ledger_head_sha256=record["source_head_sha256"]):
            _stop("CORRECTION_SOURCE_OR_KNOWLEDGE_HEAD_DRIFT")
        from ire.v6.public_origin import replay_public_origin_archive
        origin = replay_public_origin_archive(row[1], expected_archive_sha256=record["origin_archive_sha256"],
                                              expected_commit=record["origin_commit"])
        self._correction_origin_rows(record["rows"],origin)
        selected = {x["claim_id"]:x for x in record["rows"]}
        if automatic:
            ids = sorted(selected)
        if not set(ids) <= selected.keys():
            _stop("CORRECTION_CONTEXT_CLAIM_NOT_FOUND")
        return {"batch_sha256":pin,"source_sha256":record["source_sha256"],"source_head_sha256":record["source_head_sha256"],
                "as_of":record["as_of"],"origin_archive_sha256":record["origin_archive_sha256"],
                "origin_capture_date":record["origin_capture_date"],"rows":[selected[cid] for cid in ids],
                "research_context_only":True,"requires_live_primary_recheck":True,"formal_financial_fact_approved":False}

    def evidence_for_question(self, question, *, selected_knowledge_ids=None, max_items=12, correction_context=None, correction_contexts=None):
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
        # Explicit owner-pinned multi-source discovery, not automatic trust of
        # all stored batches. One current batch per original source, no silent
        # omission or selection of a superseded alternative.
        multi = correction_contexts is not None
        if multi:
            if (correction_context is not None or selected_knowledge_ids is not None
                    or type(correction_contexts) is not list
                    or not 1 <= len(correction_contexts) <= 30
                    or any(type(c) is not dict or set(c) != {"batch_sha256","source_store"}
                           or type(c["batch_sha256"]) is not str
                           or not SHA.fullmatch(c["batch_sha256"])
                           for c in correction_contexts)):
                raise InvalidInput("V126_MULTI_CONTEXT_EXPLICIT_PINS_ONLY")
            pins = [c["batch_sha256"] for c in correction_contexts]
            if len(set(pins)) != len(pins):
                raise InvalidInput("V126_MULTI_CONTEXT_DUPLICATE_BATCH")
        automatic_context = type(correction_context) is dict and "claim_ids" not in correction_context
        if automatic_context and selected_knowledge_ids is not None:
            raise InvalidInput("V126_AUTOMATIC_CONTEXT_CANNOT_MIX_MANUAL_IDS")
        with self._session() as con:
            if multi:
                con.execute("BEGIN")
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
            external = self._external_correction_context(con,correction_context) if correction_context is not None else None
            batches = []
            if multi:
                for ctx in sorted(correction_contexts, key=lambda c:c["batch_sha256"]):
                    batches.append(self._external_correction_context(con,ctx))
                if len({b["source_sha256"] for b in batches}) != len(batches):
                    _stop("MULTI_CONTEXT_MULTIPLE_BATCHES_PER_SOURCE")
        approved_for_lookup = set(graph["active_knowledge_ids"])
        active = {x["knowledge_id"]:x for x in entries
                  if x["knowledge_id"] in approved_for_lookup}
        diagnostics = None
        if multi:
            # Claim IDs are local to each source. Rank one combined corpus,
            # with qualified identities, and apply one global category cap.
            all_corrections = [{**r,"batch_sha256":b["batch_sha256"]}
                               for b in batches for r in b["rows"]]
            found, matched, diagnostics = _rank_research_context(question,active,all_corrections,max_items)
            matched_keys = {(r["batch_sha256"],r["claim_id"]) for r in matched}
            for b in batches:
                b["rows"] = [r for r in b["rows"] if (b["batch_sha256"],r["claim_id"]) in matched_keys]
            diagnostics.update(external_batches_scanned=len(batches),
                               external_identity="BATCH_SHA256_AND_CLAIM_ID")
        elif automatic_context:
            found, matched, diagnostics = _rank_research_context(question, active, external["rows"], max_items)
            external = {**external, "rows":matched}
        elif selected_knowledge_ids is not None:
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
                **({"external_correction_context":external} if external is not None else {}),
                **({"external_correction_contexts":batches} if multi else {}),
                **({"automatic_retrieval_diagnostics":diagnostics} if diagnostics is not None else {}),
                "financial_claims_requiring_current_primary_source":sum(
                    x["finance_current_law_review_required"] for x in found),
                "chat_question_relevance_not_independently_verified":True,
                "requires_live_official_source_recheck":True,
                "chatgpt_final_answer_review_required":True,
                "research_candidate_not_formal_financial_fact":True,
                "no_auto_personal_advice":True,"p0_go":False,
                "status":"HOST_CHAT_EVIDENCE_REVIEW_REQUIRED"}
