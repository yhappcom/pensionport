"""V127.1 private resumable, digest-only child ChatGPT checkpoint.

The actual chat host must prepare candidate semantics; this coordinator does
not generate them or call a model. A checkpoint is NOT a parent research GO.
Source transcript is held in process memory, never committed into checkpoint.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from ire.v6.codec import ZERO_SHA, canonical, json_digest
from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.full_video_segments import propose_full_video_segments
from ire.v6.trust import verify_owner_inventory
from ire.v6.prior_knowledge import audit_prior_candidates
from v123_chat_final_gate import assess_chat_final_gate
from v127_full_video_chat_completion import assess_full_video_chat_assembly

HEX = re.compile(r"[a-f0-9]{64}\Z")


def _stop(reason):
    raise QualityNotProven("V1271_"+reason)


class PrivateFullVideoCheckpoint:
    """Append-only checkpoint; independently pinned external DB HEAD still needed."""
    def __init__(self, path, *, raw, parent_manifest, parent_inventory,
                 expected_parent_inventory_sha256, max_cues):
        self.path=Path(path)
        if self.path.suffix not in (".db", ".sqlite") or not self.path.parent.is_dir():
            raise InvalidInput("V1271_PRIVATE_CHECKPOINT_PATH_REQUIRED")
        self.raw=raw
        self.parent_manifest=parent_manifest
        self.parent_inventory=parent_inventory
        self.owner_pin=expected_parent_inventory_sha256
        self.max_cues=max_cues
        self.parent=verify_owner_inventory(raw,parent_manifest,parent_inventory,
                      expected_inventory_sha256=expected_parent_inventory_sha256).source
        self.plan=propose_full_video_segments(raw,parent_manifest,parent_inventory,
                       expected_inventory_sha256=expected_parent_inventory_sha256,
                       max_cues=max_cues)
        self.child_manifests=([s["child_manifest"] for s in self.plan["segments"]]
                              if self.plan["segmentation_needed"] else [parent_manifest])
        self.child_ids=[f"B{i:04d}" for i in range(1,len(self.child_manifests)+1)]
        self.plan_pin=json_digest({"parent_source_sha256":self.parent.source_sha256,
                         "parent_manifest_sha256":self.parent.manifest_sha256,
                         "parent_owner_inventory_sha256":self.owner_pin,
                         "max_cues":max_cues,
                         "child_manifest_sha256s":[json_digest(m) for m in self.child_manifests]})
        con=self._connect()
        try:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS checkpoint_meta(
                   name TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS checkpoint_events(
                   seq INTEGER PRIMARY KEY, event_json TEXT NOT NULL,
                   event_sha256 TEXT NOT NULL);
            """)
            con.execute("BEGIN IMMEDIATE")
            meta=con.execute("SELECT value FROM checkpoint_meta WHERE name='plan_sha256'").fetchone()
            if meta is None:
                con.execute("INSERT INTO checkpoint_meta VALUES(?,?)",("plan_sha256",self.plan_pin))
            elif meta[0]!=self.plan_pin:
                _stop("PARENT_PLAN_OR_SOURCE_PIN_CHANGED")
            con.commit()
            self._audit(con)
        finally:
            con.close()

    def _connect(self):
        con=sqlite3.connect(str(self.path),timeout=10)
        con.execute("PRAGMA busy_timeout=10000")
        return con

    def _audit(self,con):
        row=con.execute("SELECT value FROM checkpoint_meta WHERE name='plan_sha256'").fetchone()
        if row is None or row[0]!=self.plan_pin:
            _stop("META_PLAN_PIN_DRIFT")
        prev=ZERO_SHA
        latest={}
        for expected_seq,(seq,body,digest) in enumerate(
                con.execute("SELECT seq,event_json,event_sha256 FROM checkpoint_events ORDER BY seq"),1):
            try:
                frame=json.loads(body)
                if (type(frame) is not dict or set(frame)!={
                    "seq","segment_id","manifest_sha256","host_event_sha256",
                    "host_bundle_sha256","chat_review_sha256","gate_receipt_sha256",
                    "decision","prev_sha256"
                } or seq!=expected_seq):
                    _stop("CHECKPOINT_FRAME_SCHEMA_OR_SEQUENCE")
            except (TypeError,ValueError):
                _stop("CHECKPOINT_FRAME_JSON_INVALID")
            segment=frame["segment_id"]
            if segment not in self.child_ids:
                _stop("SEGMENT_NOT_IN_PARENT_PLAN")
            if (frame["manifest_sha256"] != json_digest(self.child_manifests[self.child_ids.index(segment)]) or
                    frame["prev_sha256"]!=prev or json_digest(frame)!=digest or
                    frame["seq"]!=seq or frame["decision"] not in ("PASS","HOLD","REJECT") or
                    not all(type(frame[k]) is str and HEX.fullmatch(frame[k]) for k in (
                        "host_event_sha256","host_bundle_sha256","chat_review_sha256","gate_receipt_sha256"))):
                _stop("CHECKPOINT_PROOF_CHAIN_OR_SHA_DRIFT")
            if segment in latest and latest[segment]["decision"]=="PASS":
                _stop("COMMITTED_PASS_CANNOT_BE_SILENTLY_REVISED")
            latest[segment]=frame
            prev=digest
        return prev,latest

    def progress(self, *, externally_pinned_checkpoint_head=None):
        con=self._connect()
        try:
            head,latest=self._audit(con)
        finally:
            con.close()
        if externally_pinned_checkpoint_head is not None and head!=externally_pinned_checkpoint_head:
            _stop("EXTERNAL_CHECKPOINT_HEAD_DRIFT")
        done=[x for x in self.child_ids if x in latest and latest[x]["decision"]=="PASS"]
        held=[x for x in self.child_ids if x in latest and latest[x]["decision"]!="PASS"]
        missing=[x for x in self.child_ids if x not in latest]
        return {"schema":"IRE_V1271_RESUMABLE_PARENT_CUE_CHECKPOINT_V1",
                "parent_source_sha256":self.parent.source_sha256,
                "parent_plan_sha256":self.plan_pin,
                "checkpoint_head_sha256":head,
                "expected_child_scopes":len(self.child_ids),
                "passed_child_scopes":len(done),"held_child_scopes":len(held),
                "missing_child_scopes":len(missing),
                "next_segment_id":next((x for x in self.child_ids if x not in done),None),
                "ready_for_full_parent_replay":len(done)==len(self.child_ids),
                "engine_research_complete":False,"p0_go":False}

    def record(self, segment_id, case, *, expected_checkpoint_head,
               allow_hold_revision=False):
        """Replay one child owner source+V6+ChatGPT evidence, then append SHA only."""
        if segment_id not in self.child_ids or type(case) is not dict:
            raise InvalidInput("V1271_CHILD_SEGMENT_SCHEMA")
        index=self.child_ids.index(segment_id)
        manifest=self.child_manifests[index]
        if case.get("manifest")!=manifest:
            _stop("CHILD_MANIFEST_NOT_IN_PARENT_PLAN")
        pinned=verify_owner_inventory(self.raw,manifest,case["inventory_bytes"],
                    expected_inventory_sha256=case["expected_inventory_sha256"])
        if pinned.source.attestation()!=case["source"].attestation():
            _stop("CHILD_SOURCE_ATTESTATION_DRIFT")
        gate=assess_chat_final_gate(
            pinned.source,case["exchange"],host_receipt=case["host_receipt"],
            chat_review=case["chat_review"],store=case["source_store"],
            official_evidence_bodies=case["official_evidence_bodies"])
        audit_prior_candidates(pinned.source,case["exchange"],case["prior_knowledge"])
        decision=("PASS" if gate["status"]=="CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY"
                  else "REJECT" if gate["status"]=="CHAT_FINAL_REJECTED" else "HOLD")
        review=case["chat_review"]
        review_sha=(json_digest(review) if review is not None else ZERO_SHA)
        fields={"segment_id":segment_id,"manifest_sha256":json_digest(manifest),
                "host_event_sha256":case["host_receipt"]["event_sha256"],
                "host_bundle_sha256":case["host_receipt"]["bundle_sha256"],
                "chat_review_sha256":review_sha,
                "gate_receipt_sha256":json_digest(gate),"decision":decision}
        con=self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            head,latest=self._audit(con)
            previous=latest.get(segment_id)
            if previous is not None and all(previous[k]==fields[k] for k in fields):
                return {"status":"IDEMPOTENT_CHILD_CHECKPOINT_REPLAY",
                        "checkpoint_head_sha256":head,"segment_id":segment_id,
                        "idempotent":True,"p0_go":False}
            if head!=expected_checkpoint_head:
                _stop("CHECKPOINT_EXPECTED_HEAD_CHANGED")
            if previous is not None and not (allow_hold_revision and previous["decision"]!="PASS"):
                _stop("REVIEW_REVISION_NOT_EXPLICIT_OR_ALREADY_PASSED")
            seq=con.execute("SELECT COUNT(*) FROM checkpoint_events").fetchone()[0]+1
            frame={"seq":seq,"prev_sha256":head,**fields}
            digest=json_digest(frame)
            con.execute("INSERT INTO checkpoint_events VALUES(?,?,?)",
                        (seq,canonical(frame).decode("utf-8"),digest))
            con.commit()
            return {"status":"CHILD_CHAT_CHECKPOINT_"+decision,
                    "checkpoint_head_sha256":digest,"segment_id":segment_id,
                    "idempotent":False,"research_candidate_published":False,"p0_go":False}
        finally:
            con.close()

    def assemble(self, child_runs, seam_reviews, *, expected_checkpoint_head):
        """Require every child digest to match saved record and full V127 replay.

        This remains parent STAGING even when all children pass; no knowledge write.
        """
        con=self._connect()
        try:
            head,latest=self._audit(con)
        finally:
            con.close()
        if head!=expected_checkpoint_head:
            _stop("ASSEMBLY_CHECKPOINT_HEAD_CHANGED")
        if type(child_runs) is not list or len(child_runs)!=len(self.child_ids):
            _stop("ASSEMBLY_CHILD_RUN_CENSUS")
        if any(x not in latest or latest[x]["decision"]!="PASS" for x in self.child_ids):
            _stop("ASSEMBLY_CHILD_REVIEW_STILL_OPEN")
        for i,(segment,case) in enumerate(zip(self.child_ids,child_runs)):
            row=latest[segment]
            if (case.get("manifest")!=self.child_manifests[i] or
                    row["host_event_sha256"]!=case["host_receipt"]["event_sha256"] or
                    row["host_bundle_sha256"]!=case["host_receipt"]["bundle_sha256"] or
                    row["chat_review_sha256"]!=json_digest(case["chat_review"])):
                _stop("ASSEMBLY_CHILD_EVIDENCE_CHANGED")
        audited=assess_full_video_chat_assembly(
            self.raw,self.parent_manifest,self.parent_inventory,
            expected_parent_inventory_sha256=self.owner_pin,
            max_cues=self.max_cues,child_runs=child_runs,seam_reviews=seam_reviews)
        if audited["status"]!="ALL_CHILD_CHATS_REVIEWED_STAGING_NOT_PUBLISHED":
            _stop("ASSEMBLY_CHAT_FINAL_HOLD")
        return {"schema":"IRE_V1271_REPLAYED_PARENT_RESTART_RECEIPT_V1",
                "status":"ALL_CHILDREN_REPLAYED_STAGING_ONLY_NOT_PUBLISHED",
                "checkpoint_head_sha256":head,
                "source_sha256":self.parent.source_sha256,
                "parent_replay_sha256":json_digest(audited),
                "original_parent_cues":audited["total_parent_cues"],
                "child_segments_replayed":len(child_runs),
                "whole_video_research_complete":False,
                "new_knowledge_export_allowed":False,"p0_go":False}