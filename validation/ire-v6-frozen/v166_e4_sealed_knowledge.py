"""V166 E4 durable authorization SEAL for the trusted research namespace.

A same-file raw SQLite/legacy V126 writer cannot be physically prohibited by a
Python object's authorizer. Instead, no such writes qualify as E4-CERTIFIED
knowledge: every approved parent release seals the entire *logical* SQLite
content plus per-child E4 source/verdict receipts with an external HMAC key and
owner-pinned seal digest. External secret and owner pin MUST reside outside the
SQLite directory. Legacy writes and seal tampering invalidate certification.

This is an E4 research-candidate trust boundary, not legislation validation,
tamper-proof filesystem security, model evidence, or financial advice.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import tempfile
from pathlib import Path
from contextlib import contextmanager

from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from v166_e4_guarded_knowledge_store import E4GuardedKnowledgeStore
from v128_atomic_parent_knowledge import _replay_parent_publications

SCHEMA = "IRE_V166_E4_HMAC_SEALED_KNOWLEDGE_ROOT_V1"
HEX = frozenset("0123456789abcdef")


def _fail(code):
    raise QualityNotProven("V166_E4_CERTIFICATE_"+code)


def _key_ok(key):
    if type(key) is not bytes or len(key) < 32:
        raise InvalidInput("V166_E4_EXTERNAL_SIGNING_KEY_MIN_32_BYTES_REQUIRED")
    return key


def _pin_ok(value):
    return type(value) is str and len(value)==64 and set(value) <= HEX


class E4SealedKnowledgeStore(E4GuardedKnowledgeStore):
    def __init__(self, path, *, external_signing_key, prior_owner_pin=None):
        self._external_secret=_key_ok(external_signing_key)
        self._trusted_prior_owner_pin=prior_owner_pin
        if prior_owner_pin is not None and not _pin_ok(prior_owner_pin):
            raise InvalidInput("V166_E4_PRIOR_OWNER_PIN_INVALID")
        super().__init__(path)
        self._seal_path=Path(str(self.path)+".e4seal.json")
        self._last_owner_pin=None
        self._e4_start_snapshot=None

    def _logical_fingerprint(self):
        """V126 hash-chain AND V128 parent proofs replayed, no blind file SHA.

        Logical rows catch unauthorized V126 inserts even while WAL is open.
        """
        with self._session() as con:
            head,_=self._audit(con)
            existing=con.execute("SELECT name FROM sqlite_master "
                                 "WHERE type='table' AND name='parent_publications'").fetchone()
            parents=_replay_parent_publications(con,head) if existing else {}
            tables={}
            for table in ("knowledge","events","parent_publications"):
                if (con.execute("SELECT name FROM sqlite_master "
                                "WHERE type='table' AND name=?",(table,)).fetchone()):
                    rows=con.execute("SELECT * FROM "+table+" ORDER BY 1").fetchall()
                else:
                    rows=[]
                tables[table]=[list(row) for row in rows]
            return {"knowledge_head_sha256":head,
                    "parent_ids":sorted(parents),
                    "parent_count":len(parents),
                    "knowledge_count":len(tables["knowledge"]),
                    "events_count":len(tables["events"]),
                    "canonical_sqlite_rows_sha256":json_digest(tables)}

    def _read_seal(self):
        if not self._seal_path.is_file():
            _fail("MISSING_APPROVAL_SEAL")
        try:
            doc=json.loads(self._seal_path.read_text(encoding="utf-8"))
        except (OSError,ValueError,UnicodeError) as exc:
            raise QualityNotProven("V166_E4_CERTIFICATE_NOT_READABLE") from exc
        if (type(doc) is not dict or set(doc)!={"payload","signature"}
            or type(doc["payload"]) is not dict
            or doc["payload"].get("schema")!=SCHEMA
            or type(doc["signature"]) is not str):
            _fail("MALFORMED_SEAL")
        expected=hmac.new(self._external_secret,
                          canonical(doc["payload"]),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(doc["signature"],expected):
            _fail("INVALID_EXTERNAL_HMAC_SIGNATURE")
        return doc

    def verify_e4_certificate(self, *, externally_pinned_seal_sha256):
        """Trust requires an independent pin, never one copied from this DB."""
        if not _pin_ok(externally_pinned_seal_sha256):
            raise InvalidInput("V166_E4_OWNER_EXTERNAL_PIN_REQUIRED")
        doc=self._read_seal()
        if not hmac.compare_digest(sha256(canonical(doc)),
                                   externally_pinned_seal_sha256):
            _fail("EXTERNAL_OWNER_PIN_MISMATCH_OR_ROLLBACK")
        state=self._logical_fingerprint()
        payload=doc["payload"]
        if state!=payload.get("database_snapshot"):
            _fail("LEGACY_WRITE_OR_DATABASE_MUTATION_AFTER_APPROVAL")
        if (type(payload.get("approved_child_receipts")) is not list or
            len(payload["approved_child_receipts"])==0 or
            type(payload.get("child_ids")) is not list or
            len(payload["child_ids"])!=len(payload["approved_child_receipts"])):
            _fail("CHILD_APPROVAL_CENSUS_MISSING")
        if state["parent_count"]<1 or not state["knowledge_count"]:
            _fail("NO_APPROVED_PARENT_RELEASE")
        return {
            "schema":"IRE_V166_E4_CERTIFIED_RESEARCH_ROOT_AUDIT_V1",
            "source":"EXTERNALLY_PINNED_E4_RESEARCH_CANDIDATE_ONLY",
            "owner_pin_sha256":externally_pinned_seal_sha256,
            "knowledge_head_sha256":state["knowledge_head_sha256"],
            "knowledge_count":state["knowledge_count"],
            "parent_count":state["parent_count"],
            "approved_child_receipts_count":len(payload["approved_child_receipts"]),
            "all_original_sqlite_rows_unchanged":True,
            "source_finance_fact_legally_certified":False,
            "personal_investment_advice_approved":False,
            "p0_go":False,
        }

    @contextmanager
    def begin_e4_parent_approval(self, child_ids):
        # First publication must start from an empty DB; historical V126
        # content cannot be retroactively described as E4-approved.
        before=self._logical_fingerprint()
        if self._seal_path.exists():
            if self._trusted_prior_owner_pin is None:
                _fail("PREVIOUS_EXTERNAL_OWNER_PIN_REQUIRED")
            self.verify_e4_certificate(
                externally_pinned_seal_sha256=self._trusted_prior_owner_pin)
        elif any(before[c] for c in
                 ("knowledge_count","events_count","parent_count")):
            _fail("EXISTING_UNCERTIFIED_LEGACY_ROWS")
        self._e4_start_snapshot=before
        try:
            with super().begin_e4_parent_approval(child_ids):
                yield self
        finally:
            self._e4_start_snapshot=None

    def certify_completed_parent(self, *, child_ids, e3_downstream_result):
        """Called by the official E4 runner INSIDE an approved E4 scope."""
        scope=self._e4_context
        if (scope is None or list(scope["expected"])!=list(child_ids)
            or set(scope["approved"])!=set(child_ids)
            or type(e3_downstream_result) is not dict
            or e3_downstream_result.get("explicit_e3_status") !=
                "PUBLISHED_RESEARCH_CANDIDATES_ONLY"
            or e3_downstream_result.get("all_video_knowledge_published") is not True):
            _fail("NOT_ALL_CHILDREN_E4_V123_PARENT_APPROVED")
        state=self._logical_fingerprint()
        if state["parent_count"]==0 or state["knowledge_count"]==0:
            _fail("PARENT_SQLITE_PUBLICATION_NOT_DURABLE")
        receipts=[{"child_id":cid,**scope["approved"][cid]}
                  for cid in child_ids]
        if (self._trusted_prior_owner_pin is not None and
            self._e4_start_snapshot is not None and
            state==self._e4_start_snapshot):
            # The frozen V128 parent proof can be replayed idempotently.
            # Never rewrite a previously owner-pinned certificate merely
            # because a caller retried the same parent. In particular,
            # changing previous_owner_pin_sha256 in a new sidecar would
            # create a different untrusted pin for unchanged SQLite rows.
            existing=self._read_seal()["payload"]
            if (existing.get("database_snapshot")!=state or
                existing.get("child_ids")!=list(child_ids) or
                existing.get("approved_child_receipts")!=receipts or
                existing.get("e3_checkpoint_head_sha256")!=
                    e3_downstream_result["checkpoint_head_sha256"]):
                _fail("IDEMPOTENT_REPLAY_NOT_IDENTICAL_TO_OWNER_PINNED_APPROVAL")
            self.verify_e4_certificate(
                externally_pinned_seal_sha256=self._trusted_prior_owner_pin)
            self._last_owner_pin=self._trusted_prior_owner_pin
            return self._trusted_prior_owner_pin
        payload={
            "schema":SCHEMA,
            "database_snapshot":state,
            "child_ids":list(child_ids),
            "approved_child_receipts":receipts,
            "e3_checkpoint_head_sha256":e3_downstream_result["checkpoint_head_sha256"],
            "previous_owner_pin_sha256":self._trusted_prior_owner_pin,
            "research_candidate_only":True,
            "current_finance_legislation_certified":False,
            "independent_gold_certified":False,
            "personal_advice_approved":False,
            "p0_go":False,
        }
        doc={"payload":payload,
             "signature":hmac.new(self._external_secret,
                                  canonical(payload),hashlib.sha256).hexdigest()}
        out=canonical(doc)
        # The state is trusted ONLY with separately retained owner pin. Crash
        # between SQLite commit and this replace => no usable E4 certificate.
        fd,name=tempfile.mkstemp(prefix=".e4seal.",suffix=".tmp",
                                  dir=str(self._seal_path.parent))
        try:
            with os.fdopen(fd,"wb") as handle:
                handle.write(out)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name,self._seal_path)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        self._last_owner_pin=sha256(out)
        self.verify_e4_certificate(
            externally_pinned_seal_sha256=self._last_owner_pin)
        return self._last_owner_pin

    def quarantine_unsealed_parent(self, *,
                                   expected_unsealed_rows_sha256,
                                   private_quarantine_dir):
        """Explicit owner-controlled recovery of a FULL but unsealed SQLite parent.

        A crash after V128's atomic commit and before E4 sidecar replacement
        can leave *complete* research rows with NO valid release certificate.
        They must never be retroactively signed from the orphan database.
        Copy exact full SQLite bytes to a private forensic DB, verify the
        source and quarantine snapshots, then atomically clear the ACTIVE DB.

        This is not automatic on startup, is NOT recovery of E3/financial
        approval, and requires an independently retained original row digest.
        All failure branches preserve the original active database.
        """
        import sqlite3
        from stat import S_IMODE
        directory=Path(private_quarantine_dir)
        if (type(expected_unsealed_rows_sha256) is not str or
            not _pin_ok(expected_unsealed_rows_sha256)):
            raise InvalidInput("V166_E4_UNSEALED_ORPHAN_EXTERNAL_ROWS_PIN_REQUIRED")
        if (not directory.is_dir() or directory.is_symlink() or
            (S_IMODE(directory.stat().st_mode) & 0o077)!=0 or
            directory.resolve()==self.path.parent.resolve()):
            raise InvalidInput("V166_E4_PRIVATE_QUARANTINE_DIRECTORY_MODE_0700_REQUIRED")
        if self._seal_path.exists():
            _fail("SEALED_DATABASE_MUST_NOT_ENTER_ORPHAN_QUARANTINE")
        original=self._logical_fingerprint()
        if (original["canonical_sqlite_rows_sha256"]!=
                expected_unsealed_rows_sha256 or
            original["parent_count"]!=1 or
            original["knowledge_count"]==0 or
            original["knowledge_count"]!=original["events_count"]):
            _fail("FULL_UNSEALED_PARENT_OR_SOURCE_OWNER_PIN_REQUIRED")
        # A forensic copy is mandatory BEFORE the active database is reset.
        fd,name=tempfile.mkstemp(
            prefix=".unsealed-parent-forensic-",suffix=".db",
            dir=str(directory))
        os.close(fd)
        forensic=Path(name)
        try:
            from contextlib import closing
            with closing(sqlite3.connect(str(self.path),timeout=10)) as src:
                with closing(sqlite3.connect(str(forensic),timeout=10)) as dst:
                    src.backup(dst)
            os.chmod(forensic,0o600)
            archive=E4SealedKnowledgeStore(
                forensic,external_signing_key=self._external_secret)
            if archive._logical_fingerprint()!=original:
                _fail("FORENSIC_SQLITE_BACKUP_NOT_EXACT")
            with forensic.open("rb") as handle:
                os.fsync(handle.fileno())

            # SQLite BEGIN IMMEDIATE excludes competing database writers;
            # replay event + parent proofs and compare the pinned rows again
            # INSIDE the lock before atomically deleting any active tables.
            with sqlite3.connect(str(self.path),timeout=10) as con:
                con.execute("PRAGMA busy_timeout=10000")
                con.execute("BEGIN IMMEDIATE")
                if self._seal_path.exists():
                    _fail("APPROVAL_SEAL_APPEARED_DURING_QUARANTINE")
                head,_=self._audit(con)
                parents=_replay_parent_publications(con,head)
                tables={table:[list(row) for row in
                    con.execute("SELECT * FROM "+table+" ORDER BY 1").fetchall()]
                    for table in ("knowledge","events","parent_publications")}
                if (json_digest(tables)!=expected_unsealed_rows_sha256 or
                    head!=original["knowledge_head_sha256"] or
                    len(parents)!=1):
                    _fail("ACTIVE_DATABASE_CHANGED_AFTER_FORENSIC_COPY")
                for table in ("parent_publications","events","knowledge"):
                    con.execute("DELETE FROM "+table)
                clean_head,_=self._audit(con)
                _replay_parent_publications(con,clean_head)
                if clean_head!="0"*64:
                    _fail("ACTIVE_EMPTY_HEAD_NOT_RESTORED")
                con.commit()
            if (self._logical_fingerprint()["parent_count"]!=0 or
                self._logical_fingerprint()["knowledge_count"]!=0 or
                self._seal_path.exists()):
                _fail("ACTIVE_UNSEALED_ROWS_NOT_CLEARED")
            return {
                "schema":"IRE_V166_E4_UNSEALED_FULL_PARENT_QUARANTINE_V1",
                "status":"UNSEALED_FULL_PARENT_PRIVATELY_PRESERVED_ACTIVE_EMPTY",
                "original_orphan_rows_sha256":expected_unsealed_rows_sha256,
                "forensic_private_database_path":str(forensic),
                "forensic_database_byte_sha256":sha256(forensic.read_bytes()),
                "forensic_rows_sha256":original["canonical_sqlite_rows_sha256"],
                "quarantine_parent_count":1,
                "quarantine_knowledge_rows":original["knowledge_count"],
                "active_parent_count":0,"active_knowledge_rows":0,
                "e4_research_approved":False,"e5_knowledge_published":False,
                "financial_fact_certified":False,"personal_advice_approved":False,
            }
        except BaseException:
            # Protect the forensic copy after active cleanup has committed.
            # Deleting it on a post-commit verification exception would
            # irreversibly lose the original unsealed source evidence.
            try:
                active_still_original=(self._logical_fingerprint()==original)
            except Exception:
                active_still_original=False  # preserve forensic data on doubt
            if active_still_original and forensic.exists():
                forensic.unlink()
            raise

    def evidence_for_question(self, *args, **kwargs):
        _fail("RAW_V126_EVIDENCE_REQUIRES_E4_OWNER_PIN_AND_E2_CONTEXT")

    def certified_e2_source_separated_context(self, question, *,
                                              externally_pinned_seal_sha256,
                                              source, exchange, ledger,
                                              selected_knowledge_ids=None,
                                              discourse=None):
        """Owner-pinned E4 research evidence only; never unfiltered V126 atoms.

        Two certificate audits bracket the exact V126 internal read.
        The only returned language is E2 source-anchored quote / marked
        ChatGPT paraphrase / marked reviewer caution, never V6 proposition.
        Financial facts and personalized advice remain unapproved.
        """
        from v126_chat_approved_knowledge_store import PrivateKnowledgeStore
        from v166_e2_semantic_separation import source_separated_evidence_for_question
        first=self.verify_e4_certificate(
            externally_pinned_seal_sha256=externally_pinned_seal_sha256)
        host=self

        class _PinnedReadOnlyV126:
            def evidence_for_question(self, *args, **kwargs):
                return PrivateKnowledgeStore.evidence_for_question(
                    host,*args,**kwargs)

        packet=source_separated_evidence_for_question(
            _PinnedReadOnlyV126(),question,source=source,
            exchange=exchange,ledger=ledger,discourse=discourse,
            selected_knowledge_ids=selected_knowledge_ids)
        second=self.verify_e4_certificate(
            externally_pinned_seal_sha256=externally_pinned_seal_sha256)
        if (first["knowledge_head_sha256"]!=second["knowledge_head_sha256"]
            or first["owner_pin_sha256"]!=second["owner_pin_sha256"]):
            _fail("TRUSTED_RESEARCH_EVIDENCE_CHANGED_DURING_READ")
        return {
            **packet,
            "schema":"IRE_V166_E4_E2_CERTIFIED_RESEARCH_CONTEXT_V1",
            "e4_external_owner_pin_sha256":externally_pinned_seal_sha256,
            "e4_knowledge_head_sha256":second["knowledge_head_sha256"],
            "e4_db_rows_certified_twice":True,
            "original_legacy_v6_proposition_exposed":False,
            "research_candidates_only":True,
            "chatgpt_final_advice_review_required":True,
            "official_financial_law_must_be_rechecked":True,
            "personal_investment_advice_approved":False,
            "p0_go":False,
        }

    def audit_authorized_research(self, *, externally_pinned_seal_sha256):
        return self.verify_e4_certificate(
            externally_pinned_seal_sha256=externally_pinned_seal_sha256)
