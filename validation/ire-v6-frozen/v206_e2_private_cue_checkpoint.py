"""Private E2 ChatGPT semantic-census checkpoint (no knowledge publication).

E2 source and ChatGPT review text remain PRIVATE in SQLite. Public GitHub
stores code and synthetic tests only, never owner's raw SRT, review payload,
financial fact approvals or personally identifying source material.

The store cannot resolve semantic disagreements or launch model API tasks.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import stat

from ire.v6.codec import ZERO_SHA, canonical, json_digest
from ire.v6.errors import InvalidInput
from v206_e2_full_cue_semantic_census import (
    PLAN,ANSWER,audit_e2_cue_answer)

SCHEMA="IRE_V206_E2_PRIVATE_CUE_CHECKPOINT_V1"


def must(ok,why):
    if not ok:
        raise InvalidInput("V206_E2_PRIVATE_"+why)


class PrivateE2CensusCheckpoint:
    def __init__(self,path,owner,*,expected_owner_head):
        self.path=Path(path)
        self.owner=owner
        self.owner_head=expected_owner_head
        must(self.path.suffix in {".db",".sqlite"} and
             self.path.parent.is_dir() and
             not self.path.is_symlink(),
             "PRIVATE_EXISTING_FOLDER_SQLITE_PATH_REQUIRED")
        if not self.path.exists():
            fd=os.open(str(self.path),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            os.close(fd)
        must(self.path.is_file() and
             stat.S_IMODE(self.path.stat().st_mode)&0o077==0,
             "PRIVATE_FILE_PERMISSIONS_REQUIRED")
        self.identity={
            "schema":SCHEMA,
            "owner_head_sha256":expected_owner_head,
            "source_sha256":owner.source.source_sha256,
            "manifest_sha256":owner.source.manifest_sha256,
            "cue_total":len(owner.source.cues),
        }
        self._check_owner()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""CREATE TABLE IF NOT EXISTS e2_identity(
                singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                identity_json TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS e2_events(
                seq INTEGER PRIMARY KEY,
                prev_sha256 TEXT NOT NULL,
                event_sha256 TEXT NOT NULL,
                event_json TEXT NOT NULL)""")
            old=db.execute("SELECT identity_json FROM e2_identity WHERE singleton=1").fetchone()
            if old is None:
                db.execute("INSERT INTO e2_identity VALUES(1,?)",
                           (canonical(self.identity).decode("utf-8"),))
            else:
                must(old[0]==canonical(self.identity).decode("utf-8"),
                     "OWNER_SCOPE_OR_HEAD_CHANGED_ON_RESUME")
            db.commit()
            self._audit(db)

    def _connect(self):
        db=sqlite3.connect(str(self.path),timeout=20,isolation_level=None)
        db.execute("PRAGMA busy_timeout=20000")
        return db

    def _check_owner(self):
        must(self.owner.progress()["checkpoint_head_sha256"]==self.owner_head,
             "ORIGINAL_OWNER_JOURNAL_CHANGED")

    def _audit(self,db):
        meta=db.execute("SELECT identity_json FROM e2_identity WHERE singleton=1").fetchone()
        must(meta is not None and
             meta[0]==canonical(self.identity).decode("utf-8"),
             "PRIVATE_META_SOURCE_DRIFT")
        prev=ZERO_SHA
        covered={}
        saved={}
        for expected_seq,record in enumerate(db.execute(
                "SELECT seq,prev_sha256,event_sha256,event_json FROM e2_events ORDER BY seq"),1):
            seq,prior,digest,body=record
            must(seq==expected_seq and prior==prev,
                 "PRIVATE_SEQUENCE_OR_PREVIOUS_HEAD_DRIFT")
            try:
                event=json.loads(body)
            except (TypeError,ValueError) as error:
                raise InvalidInput("V206_E2_PRIVATE_EVENT_JSON_INVALID") from error
            must(type(event) is dict and
                 set(event)=={
                     "schema","seq","prev_sha256","source_sha256",
                     "owner_head_sha256","start_cue","end_cue",
                     "challenge","answer","audit_status"} and
                 event["schema"]==SCHEMA and
                 event["seq"]==seq and
                 event["prev_sha256"]==prev and
                 event["source_sha256"]==self.identity["source_sha256"] and
                 event["owner_head_sha256"]==self.owner_head and
                 json_digest(event)==digest and
                 canonical(event).decode("utf-8")==body,
                 "PRIVATE_EVENT_HASH_OR_SCHEMA_DRIFT")
            ch=event["challenge"]
            answer=event["answer"]
            first,last=event["start_cue"],event["end_cue"]
            must(type(ch) is dict and type(answer) is dict and
                 ch.get("schema")==PLAN and answer.get("schema")==ANSWER and
                 ch.get("challenge_sha256")==answer.get("challenge_sha256") and
                 ch.get("owner_head_sha256")==self.owner_head and
                 ch.get("source_sha256")==self.identity["source_sha256"] and
                 ch.get("start_cue")==first and ch.get("end_cue")==last and
                 type(first) is int and type(last) is int and
                 1<=first<=last<=self.identity["cue_total"],
                 "PRIVATE_EVENT_CUE_SCOPE_DRIFT")
            for cue in range(first,last+1):
                must(cue not in covered,"PRIVATE_ORIGINAL_CUE_DOUBLE_REVIEW")
                covered[cue]=digest
            saved[first]=(digest,event)
            prev=digest
        return prev,covered,saved

    def progress(self):
        self._check_owner()
        with self._connect() as db:
            head,covered,saved=self._audit(db)
        missing=[cue for cue in range(1,self.identity["cue_total"]+1)
                 if cue not in covered]
        statuses=[item["audit_status"] for _,item in saved.values()]
        return {
            "schema":"IRE_V206_E2_PRIVATE_CUE_PROGRESS_V1",
            "owner_head_sha256":self.owner_head,
            "source_sha256":self.identity["source_sha256"],
            "private_e2_head_sha256":head,
            "original_cue_total":self.identity["cue_total"],
            "original_cues_checkpointed":len(covered),
            "original_cues_remaining":len(missing),
            "next_cue_index":missing[0] if missing else None,
            "semantic_hold_batches":sum(x.startswith("HOLD_") for x in statuses),
            "source_cue_census_recorded":not missing,
            "independent_gold_semantics_verified":False,
            "e2_pass":False,
            "e3_e4_e5_authorized":False,
        }

    def record(self,challenge,answer,*,expected_private_head):
        self._check_owner()
        # The SOURCE challenge is reconstructed against a LIVE V176 journal,
        # so hashes copied from fabricated packets are never trusted.
        audited=audit_e2_cue_answer(
            self.owner,challenge,answer,expected_owner_head=self.owner_head)
        event_keys={"schema":SCHEMA,"source_sha256":self.identity["source_sha256"],
                    "owner_head_sha256":self.owner_head,
                    "start_cue":challenge["start_cue"],
                    "end_cue":challenge["end_cue"],
                    "challenge":challenge,"answer":answer,
                    "audit_status":audited["status"]}
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            head,covered,saved=self._audit(db)
            first,last=challenge["start_cue"],challenge["end_cue"]
            for _,previous in saved.values():
                if (previous["start_cue"]==first and previous["end_cue"]==last and
                    previous["challenge"]==challenge and
                    previous["answer"]==answer):
                    db.rollback()
                    return {"status":"IDEMPOTENT_E2_CUE_REVIEW_REPLAY",
                            "private_head_sha256":head,
                            "audited_status":audited["status"],
                            "e2_pass":False}
            must(head==expected_private_head,"PRIVATE_EXPECTED_HEAD_STALE")
            must(not any(i in covered for i in range(first,last+1)),
                 "PRIVATE_CUE_ALREADY_REVIEWED_NO_SILENT_REVISION")
            self._check_owner()
            seq=len(saved)+1
            event={**event_keys,"seq":seq,"prev_sha256":head}
            digest=json_digest(event)
            db.execute("INSERT INTO e2_events VALUES(?,?,?,?)",(
                seq,head,digest,canonical(event).decode("utf-8")))
            db.commit()
            return {
                "status":"E2_CUE_REVIEW_CHECKPOINTED_NOT_FINANCIALLY_APPROVED",
                "private_head_sha256":digest,
                "audited_status":audited["status"],
                "original_cues_committed":last-first+1,
                "e2_pass":False,
                "e3_e4_e5_authorized":False}
