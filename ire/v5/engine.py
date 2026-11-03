"""IRE V5 research transactions under a ChatGPT chat-host control plane.

This module NEVER initiates model inference or network search; the active ChatGPT
conversation does those tasks and submits independent source-grounded results.
The module verifies immutable inputs, coverage, evidence/relationship review
obligations, and report sealing.  No synthetic answers or automatic fact approvals.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json
import os
import re
import secrets

SOURCE_MANIFEST_SCHEMA = "IRE_V5_SOURCE_PLAN_V1"
MODEL_SCHEMA = "IRE_V5_MODEL_WINDOW_V1"
EVIDENCE_SCHEMA = "IRE_V5_EVIDENCE_CASE_V1"
RELATION_SCHEMA = "IRE_V5_PRIOR_RELATION_V1"
EVENT_SCHEMA = "IRE_V5_EVENT_V1"
RECEIPT_SCHEMA = "IRE_V5_CLOSURE_V1"
VALID_KINDS = {"QUESTION", "PERSONAL_CASE", "RULE", "HYPOTHETICAL", "OPINION", "RECOMMENDATION", "MATH"}
EVIDENCE_STATUS = {"OFFICIAL_CANDIDATE_APPLICABILITY_OPEN", "OPEN_PERSONAL_DATA", "OPEN_ASSUMPTION", "OPEN_SOURCE", "NOT_REQUIRED_WITH_REASON", "FACT_VERIFIED_IN_SCOPE"}
RELATION_STATUS = {"SAME_SCOPE_PENDING", "EXTENDS_SCOPE_PENDING", "DIFFERENT_SCOPE", "CONFLICT_CANDIDATE", "NO_RELEVANT_PRIOR_WITH_SEARCH", "OPEN_RELATION"}

class RunError(ValueError):
    pass


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RunError(reason)


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _private_dir(path: Path) -> Path:
    path = path.expanduser().resolve()
    if path.exists():
        require(path.is_dir(), "STORE_NOT_DIRECTORY")
        require(path.stat().st_mode & 0o077 == 0, "STORE_DIRECTORY_NOT_PRIVATE")
    else:
        path.mkdir(parents=True, mode=0o700)
    return path


def _exclusive_json(path: Path, value: Any) -> None:
    encoded = canonical(value)
    require(len(encoded) < 4_000_000, "RECEIPT_OVERSIZED")
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(encoded)
        f.flush()
        os.fsync(f.fileno())


def _read_json(path: Path) -> dict:
    v = json.loads(path.read_text("utf-8"))
    require(type(v) is dict, "RECEIPT_NOT_OBJECT")
    return v


@dataclass(frozen=True)
class Cue:
    index: int
    text: str
    start_ms: int
    end_ms: int


def cues_from_srt(raw: bytes) -> dict[int, Cue]:
    """Independent SRT decoder; no V3 import or external libraries."""
    decoded = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    out = {}
    pattern = re.compile(r"^(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})$")
    def ms(x: str) -> int:
        m = pattern.fullmatch(x)
        require(m is not None, "SRT_BAD_TIME")
        hh,mm,ss,frac=map(int,m.groups())
        require(mm<60 and ss<60, "SRT_BAD_TIME_UNIT")
        return ((hh*60+mm)*60+ss)*1000+frac
    for block in re.split(r"\n\s*\n",decoded.strip()):
        lines=block.split("\n")
        require(len(lines)>=3 and lines[0].strip().isdigit(),"SRT_BAD_BLOCK")
        n=int(lines[0].strip())
        times=lines[1].split(" --> ")
        require(len(times)==2,"SRT_BAD_TIME_ARROW")
        start,end=ms(times[0].strip()),ms(times[1].strip())
        require(n==len(out)+1 and start<=end,"SRT_CUE_ORDER_OR_TIME")
        content=" ".join(x.strip() for x in lines[2:] if x.strip())
        require(bool(content),"SRT_EMPTY_CUE")
        out[n]=Cue(n,content,start,end)
    require(bool(out),"SRT_NO_CUES")
    return out


class ResearchRun:
    """Append-only event-chain research ledger, partitioned from all prior engines.

    Manifest supplies source hash, V3-origin exact window boundaries and scope;
    its full 81-window ownership is rechecked. The run only needs semantic
    evidence for the requested 3-window pilot, then can scale without changing
    the data structures. 
    """
    def __init__(self, source_srt: bytes, manifest: dict, store: str | Path):
        self.source = source_srt
        self.cues = cues_from_srt(source_srt)
        self.manifest = manifest
        self.root = _private_dir(Path(store))
        self.events = _private_dir(self.root/"events")
        self._verify_manifest()
        metadata={"schema":"IRE_V5_RUN_LOCK_V1",
                  "video_id":manifest["video_id"],
                  "source_sha256":sha256(source_srt),
                  "source_cues":len(self.cues),
                  "source_window_count":len(manifest["windows"]),
                  "active_window_ids":manifest["active_window_ids"],
                  "manifest_sha256":sha256(canonical(manifest)),
                  "prior_baseline_git_blob_sha":manifest["prior_baseline_git_blob_sha"],
                  "user_request_count_declared":1,
                  "host_model_call_origin":"CHATGPT_CURRENT_CONVERSATION_UNVERIFIED"}
        self.lock=metadata
        file=self.root/"run_lock.json"
        if file.exists():
            require(_read_json(file)==metadata,"RUN_SOURCE_OR_SCOPE_CHANGED")
        else:
            _exclusive_json(file,metadata)
        self.replay()

    def _verify_manifest(self) -> None:
        m=self.manifest
        require(type(m) is dict and m.get("schema")==SOURCE_MANIFEST_SCHEMA,
                "MANIFEST_INVALID")
        require(m.get("source_sha256")==sha256(self.source) and
                m.get("source_cues")==len(self.cues),"MANIFEST_SOURCE_MISMATCH")
        require(type(m.get("video_id")) is str and
                re.fullmatch(r"[A-Za-z0-9_-]{11}",m["video_id"]) and
                type(m.get("planner_version")) is str and
                type(m.get("prior_baseline_git_blob_sha")) is str and
                bool(re.fullmatch(r"[0-9a-f]{40}",m["prior_baseline_git_blob_sha"])),"MANIFEST_IDENTITY_INCOMPLETE")
        windows=m.get("windows",[])
        require(type(windows) is list and len(windows)>0,"MANIFEST_WINDOWS_MISSING")
        owners=[];seen=set();self.windows={}
        for w in windows:
            wid=w.get("window_id")
            ids=w.get("primary_cue_ids")
            require(type(wid) is str and re.fullmatch(r"W\d{5}",wid) and wid not in seen,
                    "MANIFEST_DUPLICATE_OR_BAD_WINDOW")
            seen.add(wid)
            require(type(ids) is list and bool(ids) and
                    all(type(i) is int and i in self.cues for i in ids) and
                    ids==list(range(ids[0],ids[-1]+1)),"MANIFEST_BAD_PRIMARY_CUES")
            text=" ".join(self.cues[i].text for i in ids)
            require(w.get("primary_text_sha256")==sha256(text.encode("utf-8")),
                    "MANIFEST_WINDOW_SOURCE_HASH_MISMATCH")
            owners.extend(ids)
            self.windows[wid]=w
        require(owners==list(self.cues),"MANIFEST_NOT_FULL_PRIMARY_CUE_CENSUS")
        active=m.get("active_window_ids")
        require(type(active) is list and bool(active) and len(active)==len(set(active))
                and all(w in self.windows for w in active),"MANIFEST_ACTIVE_SCOPE_INVALID")
        self.active=active

    def packet(self, wid: str) -> dict:
        require(wid in self.active,"WINDOW_OUT_OF_ACTIVE_SCOPE")
        w=self.windows[wid]
        payload={"schema":"IRE_V5_SOURCE_PACKET_V1", "video_id":self.manifest["video_id"],
                 "window_id":wid,"source_sha256":sha256(self.source),
                 "primary_text_sha256":w["primary_text_sha256"],
                 "cues":[{"cue_index":i,"text":self.cues[i].text}
                         for i in w["primary_cue_ids"]]}
        return {**payload,"packet_sha256":sha256(canonical(payload))}

    def replay(self) -> dict:
        """Verifies content-addressed immutable sequential events and every transition."""
        self.model={};self.evidence={};self.relations={};self.closure=None
        files=sorted(self.events.glob("*.json"))
        expected_prev="0"*64
        for seq,path in enumerate(files,1):
            body=_read_json(path)
            require(body.get("schema")==EVENT_SCHEMA and
                    body.get("sequence")==seq and body.get("prev_event_sha256")==expected_prev,
                    "EVENT_CHAIN_SEQ_OR_PREV_INVALID")
            event_sha=body.get("event_sha256")
            require(type(event_sha) is str and
                    event_sha==sha256(canonical({k:v for k,v in body.items() if k!="event_sha256"}))
                    and path.name==f"{seq:06d}_{event_sha}.json", "EVENT_CONTENT_OR_FILENAME_TAMPERED")
            self._apply(body["type"],body["payload"])
            expected_prev=event_sha
        self.head=expected_prev
        self.seq=len(files)
        return self.status()

    def _apply(self, kind: str, item: dict) -> None:
        require(self.closure is None,"RUN_ALREADY_CLOSED")
        if kind=="BATCH_ACCEPT":
            # One signed/content-addressed event can contain many source-linked
            # model/evidence/prior review actions. Reject nested batches and
            # closures. Validation of EVERY subevent precedes any disk write.
            require(type(item) is dict and
                    item.get("schema")=="IRE_V5_ACTION_BUNDLE_V1" and
                    type(item.get("actions")) is list and
                    1 <= len(item["actions"]) <= 500,
                    "BATCH_ACTION_BUNDLE_INVALID")
            for action in item["actions"]:
                require(type(action) is dict and
                        set(action)=={"type","payload"} and
                        action["type"] in {"MODEL_ANALYSIS", "EVIDENCE_REVIEW",
                                           "PRIOR_RELATION_REVIEW"},
                        "BATCH_ACTION_TYPE_NOT_ALLOWED")
                self._apply(action["type"], action["payload"])
            return
        if kind=="MODEL_ANALYSIS":
            wid=item.get("window_id") if type(item) is dict else None
            require(wid not in self.model,"MODEL_WINDOW_ALREADY_ACCEPTED")
            self._validate_model(item)
            self.model[wid]=item
        elif kind=="EVIDENCE_REVIEW":
            self._validate_evidence(item)
            cid=item["claim_id"]
            require(cid not in self.evidence,"EVIDENCE_REVIEW_ALREADY_FINALIZED")
            self.evidence[cid]=item
        elif kind=="PRIOR_RELATION_REVIEW":
            self._validate_relation(item)
            cid=item["claim_id"]
            require(cid not in self.relations,"RELATION_REVIEW_ALREADY_FINALIZED")
            self.relations[cid]=item
        elif kind=="RESEARCH_CLOSURE":
            require(item==self._closure_body(),"CLOSURE_CHANGED_OR_INCOMPLETE")
            self.closure=item
        else:
            raise RunError("UNKNOWN_EVENT_TYPE")

    def append(self, kind: str, item: dict) -> dict:
        # preflight against live actual state before writing.
        self.replay()
        old=(self.model.copy(),self.evidence.copy(),self.relations.copy(),self.closure)
        try:
            self._apply(kind,item)
        except Exception:
            self.model,self.evidence,self.relations,self.closure=old
            raise
        body={"schema":EVENT_SCHEMA,"sequence":self.seq+1,
              "prev_event_sha256":self.head,"type":kind,"payload":item}
        digest=sha256(canonical(body));body["event_sha256"]=digest
        name=f"{self.seq+1:06d}_{digest}.json"
        _exclusive_json(self.events/name,body)
        self.replay()
        return {"event_type":kind,"sequence":self.seq,"event_sha256":digest,
                "status":self.status()}

    def next_task(self) -> dict:
        """Deterministic HOST task router, not a model inference implementation.

        The active ChatGPT conversation must author the decisions and use tools.
        No Python API can invoke the model.  This single-turn controller always
        selects the next unmet obligation from the authenticated live ledger.
        """
        self.replay()
        if self.closure is not None:
            result={"phase":"DONE", "receipt_chain_head":self.head}
        else:
            result=None
            for wid in self.active:
                if wid not in self.model:
                    result={"phase":"MODEL_ANALYSIS_REQUIRED", "window_id":wid,
                            "packet":self.packet(wid)}
                    break
                for claim in self.model[wid]["claims"]:
                    cid=claim["claim_id"]
                    if cid not in self.evidence:
                        result={"phase":"OFFICIAL_EVIDENCE_REVIEW_REQUIRED",
                                "window_id":wid,"claim_id":cid,
                                "proposition":claim["proposition"],
                                "requires_external_verification":claim["requires_external_verification"]}
                        break
                    if cid not in self.relations:
                        result={"phase":"PRIOR_KNOWLEDGE_REVIEW_REQUIRED",
                                "window_id":wid,"claim_id":cid,
                                "proposition":claim["proposition"],
                                "prior_baseline_git_blob_sha":self.manifest["prior_baseline_git_blob_sha"]}
                        break
                if result is not None:break
            if result is None:
                if self._closure_body()["blockers"]:
                    result={"phase":"BLOCKED_AUDIT_REVIEW", "blockers":self._closure_body()["blockers"]}
                else:
                    result={"phase":"SEAL_RESEARCH_REPORT_REQUIRED",
                            "source_window_scope":len(self.active),
                            "total_claims":len(self._claims()),
                            "open_evidence_cases":self._closure_body()["open_or_unverified_evidence_cases"]}
        return {**result,"task_sha256":sha256(canonical(result)),
                "user_continue_requested":False}

    def _claims(self)->dict:
        return {c["claim_id"]:c for w in self.model.values() for c in w["claims"]}

    def _validate_model(self, item: dict)->None:
        require(type(item) is dict and item.get("schema")==MODEL_SCHEMA,
                "MODEL_SCHEMA_INVALID")
        wid=item.get("window_id")
        require(wid in self.active,"MODEL_WINDOW_OUT_OF_SCOPE")
        p=self.packet(wid)
        require(item.get("packet_sha256")==p["packet_sha256"],"MODEL_SOURCE_PACKET_CHANGED")
        require(item.get("claimed_author")=="CURRENT_CHATGPT_CONVERSATION" and
                item.get("independent_human_verified") is False,
                "MODEL_ORIGIN_OR_INDEPENDENCE_MISSTATED")
        claims=item.get("claims");states=item.get("cue_dispositions")
        require(type(claims) is list and type(states) is list,"MODEL_CLAIMS_MISSING")
        all_existing=set(self._claims())
        ref_by_cue={i:set() for i in self.windows[wid]["primary_cue_ids"]}
        seen=set()
        for c in claims:
            cid=c.get("claim_id")
            require(type(cid) is str and re.fullmatch(r"V5C[0-9]{4}",cid) and
                    cid not in seen and cid not in all_existing,"MODEL_CLAIM_ID_INVALID")
            seen.add(cid)
            require(type(c.get("proposition")) is str and len(c["proposition"].strip())>=8 and
                    c.get("kind") in VALID_KINDS and
                    type(c.get("requires_external_verification")) is bool and
                    c.get("fact_verified") is False and
                    c.get("advisory_approved") is False,
                    "MODEL_CLAIM_UNREVIEWED_ONLY")
            refs=c.get("source_refs")
            require(type(refs) is list and bool(refs),"MODEL_CLAIM_WITHOUT_SOURCE")
            for ref in refs:
                i=ref.get("cue_index")
                quote=ref.get("quote")
                require(type(i) is int and i in ref_by_cue and
                        type(quote) is str and len(quote.strip())>=2 and
                        quote in self.cues[i].text,"MODEL_HALO_OR_FABRICATED_QUOTE")
                ref_by_cue[i].add(cid)
        ids=self.windows[wid]["primary_cue_ids"]
        require(len(states)==len(ids),"MODEL_CUE_CENSUS_MISSING")
        for i,row in zip(ids,states):
            require(type(row) is dict and row.get("cue_index")==i,
                    "MODEL_CUE_ORDER_CHANGED")
            st=row.get("status")
            require(st in {"LINKED","NONCLAIM","UNRESOLVED"},"MODEL_CUE_STATUS_INVALID")
            linked=row.get("claim_ids")
            require(type(linked) is list and len(linked)==len(set(linked)) and
                    set(linked)==ref_by_cue[i],"MODEL_CUE_REVERSE_LINK_INVALID")
            if st=="LINKED":
                require(bool(linked),"MODEL_EMPTY_LINKED_CUE")
            else:
                require(not linked and type(row.get("reason")) is str and
                        len(row["reason"].strip())>=6,"MODEL_NONCLAIM_WITHOUT_REASON")

    def _validate_evidence(self,item):
        require(type(item) is dict and item.get("schema")==EVIDENCE_SCHEMA,
                "EVIDENCE_SCHEMA_INVALID")
        claim=self._claims().get(item.get("claim_id"))
        require(claim is not None,"EVIDENCE_CLAIM_NOT_ANALYZED")
        require(item.get("status") in EVIDENCE_STATUS and
                type(item.get("investigation_summary")) is str and
                len(item["investigation_summary"].strip())>=12,
                "EVIDENCE_INVALID_DECISION")
        if claim["requires_external_verification"]:
            require(item["status"]!="NOT_REQUIRED_WITH_REASON" and
                    type(item.get("search_query")) is str and item["search_query"].strip(),
                    "EVIDENCE_MANDATORY_SEARCH_MISSING")
        if item["status"]=="FACT_VERIFIED_IN_SCOPE":
            # A boolean self-attestation is not independently signed proof.
            # This kernel may collect a candidate dossier but cannot confer approval.
            raise RunError("FACT_APPROVAL_REQUIRES_INDEPENDENT_VERIFIER_NOT_THIS_HOST")
        require(item.get("financial_truth_approved") is False and
                type(item.get("open_reason")) is str and len(item["open_reason"].strip())>=9,
                "EVIDENCE_OPEN_REASON_REQUIRED")
        if self.manifest.get("p0c_policy") == "STRICT_P0C_V1":
            from .p0c import validate_strict_evidence
            validate_strict_evidence(item,claim)

    def _validate_relation(self,item):
        require(type(item) is dict and item.get("schema")==RELATION_SCHEMA and
                item.get("claim_id") in self._claims(),"RELATION_CLAIM_NOT_ANALYZED")
        require(item.get("prior_baseline_git_blob_sha")==self.manifest["prior_baseline_git_blob_sha"],
                "RELATION_PRIOR_BASELINE_DRIFT")
        require(item.get("status") in RELATION_STATUS and
                type(item.get("review_notes")) is str and
                len(item["review_notes"].strip())>=12 and
                item.get("automerge") is False and
                item.get("financial_truth_approved") is False,
                "RELATION_NOT_REVIEWED_OR_UNSAFE_MERGE")
        require(type(item.get("search_terms")) is list and bool(item["search_terms"]),
                "RELATION_SEARCH_NOT_DOCUMENTED")
        require(item.get("prior_claim_ids") is not None and
                type(item["prior_claim_ids"]) is list,"RELATION_PRIOR_CANDIDATES_UNSPECIFIED")
        if self.manifest.get("p0c_policy") == "STRICT_P0C_V1":
            from .p0c import validate_strict_relation
            validate_strict_relation(item,self.manifest["prior_baseline_git_blob_sha"])

    def _closure_body(self)->dict:
        cid_map=self._claims()
        missing_windows=[w for w in self.active if w not in self.model]
        missing_evidence=sorted(set(cid_map)-set(self.evidence))
        missing_relations=sorted(set(cid_map)-set(self.relations))
        # There can be unresolved semantic cues but every one must have a recorded cause.
        unresolved=sum(c["status"]=="UNRESOLVED" for w in self.model.values()
                       for c in w["cue_dispositions"])
        blocking=[]
        if missing_windows:blocking.append("MODEL_WINDOWS_NOT_COMPLETE")
        if missing_evidence:blocking.append("CLAIM_EVIDENCE_NOT_INVESTIGATED")
        if missing_relations:blocking.append("PRIOR_RELATIONS_NOT_REVIEWED")
        if unresolved:blocking.append("HIGH_SIGNAL_SEMANTIC_UNRESOLVED")
        provisional=sum(1 for e in self.evidence.values()
                        if e["status"]!="FACT_VERIFIED_IN_SCOPE")
        return {"schema":RECEIPT_SCHEMA,
                "video_id":self.manifest["video_id"],
                "source_sha256":sha256(self.source),
                "manifest_sha256":self.lock["manifest_sha256"],
                "scope_windows":len(self.active),
                "submitted_windows":len(self.model),
                "unprocessed_windows":missing_windows,
                "claims":len(cid_map),
                "evidence_cases_reviewed":len(self.evidence),
                "open_or_unverified_evidence_cases":provisional,
                "relation_cases_reviewed":len(self.relations),
                "unresolved_cues":unresolved,
                "blockers":blocking,
                "research_status":"RESEARCH_REPORT_COMPLETE_WITH_OPEN_ITEMS" if not blocking else "INCOMPLETE",
                "approved_financial_facts":0,
                "advisory_release_status":"BLOCKED_NO_INDEPENDENT_APPROVAL",
                "host_execution_origin":"ONE_CHAT_REQUEST_REPORTED_NOT_INDEPENDENTLY_ATTESTED",
                "external_model_api_calls":0}

    def close(self)->dict:
        body=self._closure_body()
        require(not body["blockers"],"RESEARCH_CANNOT_CLOSE:"+",".join(body["blockers"]))
        self.append("RESEARCH_CLOSURE",body)
        # Derived display fields do not alter the pre-existing immutable event.
        return self.status()

    def status(self)->dict:
        # Never confuse a bounded pilot with a full video run. These fields
        # are computed outside the event content so older sealed receipts replay.
        full_scope=(len(self.active)==len(self.windows))
        d=self.closure.copy() if self.closure is not None else self._closure_body()
        return {**d,"sealed":self.closure is not None,
                "receipt_count":self.seq,
                "event_chain_head_sha256":getattr(self,"head","0"*64),
                "video_windows_total":len(self.windows),
                "scope_kind":"FULL_VIDEO" if full_scope else "PILOT_WINDOW_SCOPE",
                "full_video_source_scope_sealed":bool(self.closure is not None and full_scope),
                "p0_one_command_full_research_go":False}
