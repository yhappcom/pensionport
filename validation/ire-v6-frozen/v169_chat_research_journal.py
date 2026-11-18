"""V169 E4: crash-safe, source-pinned journal for an IN-CHAT researcher.

No model/API call and no autonomous source verification. The chat host passes its
own reviewer callback during the active turn. Results remain draft V167
proposals. Frozen V123, E4 authority, V128, and investment knowledge untouched.

Private SQLite may contain owner-source quotes and ChatGPT notes: keep locally
with restrictive file permissions, never commit it to GitHub.
"""
from __future__ import annotations

import copy
import json
from contextlib import closing
import os
import sqlite3
import stat
from pathlib import Path

from v166_e4_full_video_readiness import digest
from v167_chat_research_loop import (SCHEMA as DOCKET_SCHEMA,
    PROPOSAL_SCHEMA, execute_chat_review_round)

SCHEMA = "IRE_V169_SOURCE_PINNED_CHAT_CHECKPOINT_JOURNAL_V1"
ZERO = "0" * 64


def _need(ok, reason):
    if not ok:
        raise ValueError("V169_JOURNAL_" + reason)


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


class ChatReviewJournal:
    """Journal only V167 proposals against a prevalidated root docket.

    One durable step is one contiguous prefix of source-pinned work items.
    A failed callback, incomplete batch or SQL fault cannot advance progress.
    Each call starts with an independent read-through of all stored receipts.
    This enforces replay integrity; no cryptographic provenance of ChatGPT.
    """

    def __init__(self, db_path, docket):
        _need(type(docket) is dict and docket.get("schema") == DOCKET_SCHEMA,
              "SOURCE_DOCKET_REQUIRED")
        _need(docket.get("docket_sha256") == digest({
            k:v for k,v in docket.items() if k!="docket_sha256"}),
            "ROOT_DOCKET_TAMPERED")
        _need(docket.get("original_open_count") == len(docket.get("items", []))
              and len({x["claim_id"] for x in docket["items"]}) ==
              len(docket["items"]), "ROOT_OPEN_CENSUS")
        _need(docket.get("v123_status_changed") is False and
              docket.get("e4_approved") is False and
              docket.get("e5_authorized") is False,
              "ROOT_RELEASE_FALSIFIED")
        self.docket = copy.deepcopy(docket)
        self.path = str(db_path)
        target = Path(self.path)
        _need(target.parent.is_dir(), "PRIVATE_PARENT_REQUIRED")
        if target.exists():
            _need(target.is_file() and not target.is_symlink() and
                  stat.S_IMODE(target.stat().st_mode) & 0o077 == 0,
                  "UNSAFE_PRIVATE_DB_MODE")
        else:
            # No world-readable file before sqlite opens the path. An existing
            # symlink is also rejected by the check above.
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        with closing(self._connect()) as con:
            con.execute("PRAGMA journal_mode=DELETE")
            con.execute("PRAGMA synchronous=FULL")
            con.executescript("""
              CREATE TABLE IF NOT EXISTS meta(
                key TEXT PRIMARY KEY, value TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS receipts(
                seq INTEGER PRIMARY KEY, claim_id TEXT NOT NULL UNIQUE,
                task_sha TEXT NOT NULL, proposal_json TEXT NOT NULL,
                prior_head TEXT NOT NULL, head TEXT NOT NULL);
            """)
            initial = con.execute("SELECT value FROM meta WHERE key='docket' ").fetchone()
            if initial is None:
                con.execute("INSERT INTO meta VALUES('docket',?)",
                            (docket["docket_sha256"],))
                con.execute("INSERT INTO meta VALUES('source',?)",
                            (docket["owner_source_sha256"],))
                con.execute("INSERT INTO meta VALUES('schema',?)", (SCHEMA,))
            else:
                _need(initial[0]==docket["docket_sha256"] and
                      con.execute("SELECT value FROM meta WHERE key='source'").fetchone()[0]
                      ==docket["owner_source_sha256"] and
                      con.execute("SELECT value FROM meta WHERE key='schema'").fetchone()[0]
                      ==SCHEMA, "FROZEN_SOURCE_OR_DOCKET_VERSION_CHANGED")
            con.commit()
        self.status()  # Verify any pre-existing receipts before serving work.

    def _connect(self):
        con=sqlite3.connect(self.path, timeout=8)
        con.execute("PRAGMA busy_timeout=8000")
        return con

    def _read_and_verify(self, con):
        rows=con.execute("SELECT seq,claim_id,task_sha,proposal_json,prior_head,head "
                         "FROM receipts ORDER BY seq").fetchall()
        items=self.docket["items"]
        _need(len(rows)<=len(items),"OVERFULL_JOURNAL")
        head=ZERO
        proposals=[]
        for pos,(seq,cid,t_sha,pjson,previous,receipt_head) in enumerate(rows):
            task=items[pos]
            _need(type(seq) is int and seq==pos+1 and
                  cid==task["claim_id"] and t_sha==digest(task) and
                  previous==head,"ORDER_OR_TASK_OR_PREVIOUS_HEAD_CHANGED")
            try:
                value=json.loads(pjson)
            except (TypeError, ValueError) as exc:
                raise ValueError("V169_JOURNAL_BAD_PRIVATE_RECEIPT_JSON") from exc
            _need(type(value) is dict and
                  value.get("claim_id")==cid and
                  value.get("segment_id")==task["segment_id"] and
                  value.get("atom_sha256")==task["atom_sha256"] and
                  value.get("prior_review_sha256")==task["prior_review_sha256"] and
                  value.get("prior_status")=="OPEN" and
                  value.get("proposed_decision") in {
                      "KEEP_OPEN", "CANDIDATE_NEEDS_NATIVE_REVIEW",
                      "QUARANTINE_PROPOSAL", "REJECT_PROPOSAL"} and
                  value.get("applied_to_native_v123") is False and
                  value.get("approved_by_e4") is False and
                  value.get("knowledge_released") is False and
                  type(value.get("source_evidence")) is list,
                  "PROPOSAL_DRIFT_OR_RELEASE_FORGED")
            event={"seq":seq,"root_docket_sha256":self.docket["docket_sha256"],
                   "task_sha":t_sha,"proposal":value,"prior_head":previous}
            head=digest(event)
            _need(receipt_head==head,"CHAIN_HASH_MISMATCH")
            proposals.append(value)
        return proposals,head

    def status(self):
        with closing(self._connect()) as con:
            props,head=self._read_and_verify(con)
        n=len(props)
        return {"schema":SCHEMA,"root_docket_sha256":self.docket["docket_sha256"],
                "owner_source_sha256":self.docket["owner_source_sha256"],
                "original_open_count":self.docket["original_open_count"],
                "processed_count":n,"remaining_count":self.docket["original_open_count"]-n,
                "journal_head_sha256":head,
                "native_v123_replay_required":True,
                "e4_approved":False,"e5_authorized":False,
                "independent_accuracy_certified":False,
                "model_origin_cryptographically_authenticated":False}

    def next_tasks(self, limit=8):
        _need(type(limit) is int and 1<=limit<=100,"NEXT_LIMIT")
        n=self.status()["processed_count"]
        return copy.deepcopy(self.docket["items"][n:n+limit])

    def run_round(self, *, evidence_retriever, chat_reviewer, limit=8,
                  _failure_injector=None):
        """Calls real host-provided functions, commits complete batch atomically.

        The caller must be the active chat host with real model-produced notes.
        An automated 'KEEP_OPEN' test callback cannot prove semantic quality.
        """
        _need(type(limit) is int and 1<=limit<=100,"ROUND_LIMIT")
        with closing(self._connect()) as con:
            previous,head=self._read_and_verify(con)
        n=len(previous)
        if n==len(self.docket["items"]):
            return self.status()
        count=min(limit,len(self.docket["items"])-n)
        last=self.docket["items"][n-1]["claim_id"] if n else None
        round_receipt=execute_chat_review_round(self.docket,
             evidence_retriever=evidence_retriever,
             chat_reviewer=chat_reviewer, limit=count, start_after=last)
        selected=self.docket["items"][n:n+count]
        _need(round_receipt["proposals_created"]==count and
              [p["claim_id"] for p in round_receipt["proposals"]]==
                  [i["claim_id"] for i in selected] and
              round_receipt["docket_sha256"]==self.docket["docket_sha256"] and
              round_receipt["owner_source_sha256"]==self.docket["owner_source_sha256"] and
              round_receipt["knowledge_publication_authorized"] is False and
              round_receipt["e5_authorized"] is False, "ROUND_BOUNDARY_DRIFT")
        con=self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            now,pinned_head=self._read_and_verify(con)
            _need(len(now)==n and pinned_head==head,
                  "CONCURRENT_JOURNAL_ADVANCE")
            for j,(task,proposal) in enumerate(zip(selected,round_receipt["proposals"])):
                seq=n+j+1
                blob=_canonical(proposal)
                item_sha=digest(task)
                event={"seq":seq,"root_docket_sha256":self.docket["docket_sha256"],
                       "task_sha":item_sha,"proposal":proposal,"prior_head":head}
                new_head=digest(event)
                con.execute("INSERT INTO receipts VALUES(?,?,?,?,?,?)",
                            (seq,task["claim_id"],item_sha,blob,head,new_head))
                head=new_head
                if _failure_injector is not None:
                    _failure_injector(seq)
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()
        return self.status()

    def export_unreleased_proposals(self):
        """Make a V168-compatible cumulative V167 receipt, never an approval."""
        with closing(self._connect()) as con:
            props,head=self._read_and_verify(con)
        n=len(props)
        obj={"schema":PROPOSAL_SCHEMA,
             "owner_source_sha256":self.docket["owner_source_sha256"],
             "docket_sha256":self.docket["docket_sha256"],
             "original_open_count":self.docket["original_open_count"],
             "proposals_created":n,
             "unprocessed_open_count":len(self.docket["items"])-n,
             "candidate_proposals":sum(p["proposed_decision"]==
                 "CANDIDATE_NEEDS_NATIVE_REVIEW" for p in props),
             "proposed_quarantines":sum(p["proposed_decision"]==
                 "QUARANTINE_PROPOSAL" for p in props),
             "proposals":props,
             "review_executor_claimed_not_cryptographically_authenticated":True,
             "evidence_origin_not_authenticated_by_this_module":True,
             "native_v123_replay_required":True,
             "formal_e4_primary_and_scope_review_required":True,
             "native_v123_status_changed":False,
             "knowledge_publication_authorized":False,
             "e5_authorized":False}
        return {**obj,"proposal_receipt_sha256":digest(obj)}