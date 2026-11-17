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
        with super().begin_e4_parent_approval(child_ids):
            yield self

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

    def evidence_for_question(self, *args, **kwargs):
        _fail("RAW_V126_EVIDENCE_REQUIRES_E4_OWNER_PIN_AND_E2_CONTEXT")

    def audit_authorized_research(self, *, externally_pinned_seal_sha256):
        return self.verify_e4_certificate(
            externally_pinned_seal_sha256=externally_pinned_seal_sha256)
