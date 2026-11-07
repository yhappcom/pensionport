"""V5 incremental re-verification overlay: source-bound risks and shared official documents.

Sealed V5 receipts are immutable. The overlay audits forced source boundaries,
quantitative nonclaim cues, previous official candidates and potential conflicts.
A shared official snapshot reduces redundant searches, but the *applicability* of
that snapshot must be reviewed for every atomic claim. No network provenance,
independent financial truth or advice approval is automatically conferred.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import re

from .engine import ResearchRun, _private_dir, _exclusive_json, _read_json, canonical, sha256, require
from .p0c import _host as _official_host

AUDIT_SCHEMA = "IRE_V5_INCREMENTAL_AUDIT_V1"
DOC_SCHEMA = "IRE_V5_SHARED_OFFICIAL_DOC_V1"
REVIEW_SCHEMA = "IRE_V5_RISK_REVIEW_V1"
_EVENT = "IRE_V5_INCREMENTAL_AUDIT_EVENT_V1"
NUMERIC = re.compile(r"[0-9０-９]")
_SHA = re.compile(r"[0-9a-f]{64}")
_CLAIM = re.compile(r"V5C\d{4}")
_ID = re.compile(r"(?:B-W\d{5}|N-\d{5}|E-V5C\d{4}|R-V5C\d{4})")
DECISIONS = {
    "B": {"CONTINUITY_REVIEWED", "CONDITION_SPANS_WINDOWS_OPEN", "SOURCE_TRANSCRIPTION_OPEN"},
    "N": {"NONFINANCIAL_NUMERIC", "EXISTING_CLAIM_FRAGMENT", "PERSONAL_SCENARIO_OPEN", "NEW_ATOM_REQUIRED", "ASR_NUMERIC_OPEN"},
    "E": {"OFFICIAL_CANDIDATE_SCOPE_OPEN", "PERSONAL_APPLICABILITY_OPEN", "EFFECTIVE_DATE_OPEN", "OFFICIAL_SEARCH_OPEN"},
    "R": {"CONFLICT_OPEN", "DIFFERENT_SCOPE_PENDING", "PRIOR_MATCH_PENDING"},
}
OPEN_DECISIONS = {
    "CONDITION_SPANS_WINDOWS_OPEN", "SOURCE_TRANSCRIPTION_OPEN", "PERSONAL_SCENARIO_OPEN",
    "NEW_ATOM_REQUIRED", "ASR_NUMERIC_OPEN", "PERSONAL_APPLICABILITY_OPEN",
    "EFFECTIVE_DATE_OPEN", "OFFICIAL_SEARCH_OPEN", "CONFLICT_OPEN", "DIFFERENT_SCOPE_PENDING",
    "PRIOR_MATCH_PENDING", "OFFICIAL_CANDIDATE_SCOPE_OPEN",
}


def _timestamp(value: str) -> None:
    require(type(value) is str and "T" in value, "AUDIT_TIMESTAMP_REQUIRED")
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as e:
        raise ValueError("AUDIT_TIMESTAMP_INVALID") from e
    require(d.tzinfo is not None, "AUDIT_TIMESTAMP_AWARE_REQUIRED")


def _evidence_id(item: dict) -> str:
    return "D-" + sha256(canonical({"url":item["url"], "content_sha256":item["content_sha256"]}))[:24]


class IncrementalAudit:
    def __init__(self, run: ResearchRun, store: str | Path):
        require(run.closure is not None and run.status()["full_video_source_scope_sealed"],
                "AUDIT_REQUIRES_FULL_SOURCE_SEAL")
        self.run = run
        self.root = _private_dir(Path(store))
        self.events_dir = _private_dir(self.root / "events")
        self.issues = self._build_issues()
        lock = {"schema":AUDIT_SCHEMA, "source_sha256":sha256(run.source),
                "manifest_sha256":run.lock["manifest_sha256"],
                "base_chain_sha256":run.head,"base_claim_count":len(run._claims()),
                "base_window_count":len(run.active),
                "issues_sha256":sha256(canonical(self.issues))}
        self.lock=lock
        p = self.root / "audit_lock.json"
        if p.exists():
            require(_read_json(p)==lock, "AUDIT_LOCK_OR_SOURCE_DRIFT")
        else:
            _exclusive_json(p,lock)
        self.replay()

    def _build_issues(self) -> dict[str,dict]:
        issues = {}
        cues = self.run.cues
        for w in self.run.manifest["windows"]:
            if not w.get("continuation_boundary_review_required"):
                continue
            # Planner's flag describes a forced split AFTER the marked window,
            # not at its first cue. Lock the right interpretation here.
            i=w["primary_cue_ids"][-1]
            require(i<len(cues),"AUDIT_BAD_CONTINUATION_LAST_WINDOW")
            issues[f"B-{w['window_id']}"]={
                "kind":"B","window_id":w["window_id"],"left_cue":i,"right_cue":i+1,
                "left_quote":cues[i].text,"right_quote":cues[i+1].text,
                "context":[{"cue_index":k,"text":cues[k].text}
                           for k in range(max(1,i-2),min(len(cues),i+3)+1)]}
        for wid,model in self.run.model.items():
            for row in model["cue_dispositions"]:
                i=row["cue_index"]
                if row["status"]!="NONCLAIM" or not NUMERIC.search(cues[i].text):
                    continue
                issues[f"N-{i:05d}"]={
                    "kind":"N","window_id":wid,"cue_index":i,
                    "quote":cues[i].text,
                    "context":[{"cue_index":k,"text":cues[k].text}
                               for k in range(max(1,i-2), min(len(cues),i+2)+1)]}
        for cid,e in self.run.evidence.items():
            if e["status"]=="OFFICIAL_CANDIDATE_APPLICABILITY_OPEN":
                issues[f"E-{cid}"]={"kind":"E","claim_id":cid,
                     "proposition":self.run._claims()[cid]["proposition"],
                     "initial_evidence_status":e["status"]}
        for cid,r in self.run.relations.items():
            if r["status"]=="CONFLICT_CANDIDATE":
                issues[f"R-{cid}"]={"kind":"R","claim_id":cid,
                    "proposition":self.run._claims()[cid]["proposition"],
                    "prior_claim_ids":r["prior_claim_ids"],
                    "prior_blob_sha256":self.run.manifest["prior_baseline_git_blob_sha"]}
        require(all(_ID.fullmatch(x) for x in issues),"AUDIT_ISSUE_ID_INVALID")
        return dict(sorted(issues.items()))

    def replay(self) -> dict:
        self.documents:dict[str,dict]={}
        self.reviews:dict[str,dict]={}
        head="0"*64
        files=sorted(self.events_dir.glob("*.json"))
        for seq,p in enumerate(files,1):
            ev=_read_json(p)
            require(ev.get("schema")==_EVENT and ev.get("sequence")==seq and
                    ev.get("prev_sha256")==head,"AUDIT_EVENT_SEQUENCE_INVALID")
            got=ev.get("event_sha256")
            require(type(got) is str and got==sha256(canonical({k:v for k,v in ev.items() if k!="event_sha256"})) and
                    p.name==f"{seq:06d}_{got}.json","AUDIT_EVENT_TAMPERED")
            self._validate_payload(ev["payload"],commit=True)
            head=got
        self.seq=len(files);self.head=head
        return self.status()

    def _validate_document(self, d:dict) -> str:
        require(type(d) is dict and d.get("schema")==DOC_SCHEMA and
                type(d.get("issuer")) is str and len(d["issuer"].strip())>=3 and
                type(d.get("url")) is str and _official_host(d["url"]),
                "AUDIT_OFFICIAL_DOCUMENT_IDENTITY_INVALID")
        _timestamp(d.get("observed_at"))
        body=d.get("captured_text")
        require(type(body) is str and 60<=len(body.encode("utf-8"))<=400000 and
                d.get("content_sha256")==sha256(body.encode("utf-8")),
                "AUDIT_OFFICIAL_CAPTURE_DIGEST_INVALID")
        require(d.get("network_origin_independently_attested") is False and
                d.get("financial_fact_approved") is False,
                "AUDIT_DOCUMENT_UNSUPPORTED_APPROVAL")
        require(type(d.get("retrieval_note")) is str and len(d["retrieval_note"].strip())>=16 and
                type(d.get("effective_date_note")) is str and len(d["effective_date_note"].strip())>=12,
                "AUDIT_OFFICIAL_SOURCE_SCOPE_NOT_REVIEWED")
        require(d.get("doc_id")==_evidence_id(d),"AUDIT_DOCUMENT_CONTENT_ADDRESS_INVALID")
        return d["doc_id"]

    def _validate_review(self, review:dict, documents:dict) -> str:
        require(type(review) is dict and review.get("schema")==REVIEW_SCHEMA,
                "AUDIT_REVIEW_SCHEMA_INVALID")
        issue=review.get("issue_id")
        require(type(issue) is str and issue in self.issues,"AUDIT_UNKNOWN_RISK_ISSUE")
        kind=self.issues[issue]["kind"]
        require(review.get("decision") in DECISIONS[kind] and
                type(review.get("rationale")) is str and len(review["rationale"].strip())>=18 and
                review.get("reviewer")=="CURRENT_CHATGPT_CONVERSATION" and
                review.get("independent_approval") is False and
                review.get("financial_fact_approved") is False,
                "AUDIT_UNSUPPORTED_REVIEW_DECISION")
        require(review.get("issue_sha256")==sha256(canonical(self.issues[issue])),
                "AUDIT_REVIEW_SOURCE_DRIFT")
        related=review.get("related_claim_ids")
        require(type(related) is list and len(related)==len(set(related)) and
                all(type(cid) is str and cid in self.run._claims() for cid in related),
                "AUDIT_CLAIM_RELATION_INVALID")
        source=self.issues[issue]
        if kind=="B":
            require(review.get("left_quote")==source["left_quote"] and
                    review.get("right_quote")==source["right_quote"],
                    "AUDIT_BOUNDARY_EXACT_CUES_MISSING")
        elif kind=="N":
            require(review.get("exact_quote")==source["quote"],
                    "AUDIT_NUMERIC_CUE_QUOTE_INVALID")
            if review["decision"]=="EXISTING_CLAIM_FRAGMENT":
                require(bool(related),"AUDIT_FRAGMENT_WITHOUT_CLAIM")
                owned={ref["cue_index"] for cid in related for ref in self.run._claims()[cid]["source_refs"]}
                require(any(abs(source["cue_index"]-k)<=3 for k in owned),
                        "AUDIT_FRAGMENT_CLAIM_TOO_DISTANT")
        elif kind=="E":
            doc_id=review.get("official_doc_id")
            if review["decision"]!="OFFICIAL_SEARCH_OPEN":
                require(type(doc_id) is str and doc_id in documents,
                        "AUDIT_EVIDENCE_DOCUMENT_REQUIRED")
                excerpt=review.get("exact_official_excerpt")
                require(type(excerpt) is str and len(excerpt.strip())>=12 and
                        excerpt in documents[doc_id]["captured_text"],
                        "AUDIT_OFFICIAL_EXCERPT_NOT_IN_SOURCE")
            else:
                require(doc_id is None and
                        type(review.get("search_outcome")) is str and
                        len(review["search_outcome"].strip())>=12,
                        "AUDIT_EVIDENCE_SEARCH_REASON_MISSING")
            require(type(review.get("applicability_limitation")) is str and
                    len(review["applicability_limitation"].strip())>=12 and
                    type(review.get("effective_date_check")) is str and
                    len(review["effective_date_check"].strip())>=12,
                    "AUDIT_EVIDENCE_CLAIM_APPLICABILITY_MISSING")
        elif kind=="R":
            require(review.get("prior_baseline_git_blob_sha")==source["prior_blob_sha256"] and
                    type(review.get("compared_prior_claim_ids")) is list and
                    set(review["compared_prior_claim_ids"])==set(source["prior_claim_ids"]) and
                    type(review.get("scope_difference_note")) is str and
                    len(review["scope_difference_note"].strip())>=16,
                    "AUDIT_PRIOR_COMPARISON_INCOMPLETE")
        return issue

    def _validate_payload(self,payload:dict,*,commit:bool) -> None:
        require(type(payload) is dict and payload.get("schema")=="IRE_V5_INCREMENTAL_BATCH_V1" and
                type(payload.get("documents")) is list and
                type(payload.get("reviews")) is list and
                bool(payload["documents"] or payload["reviews"]) and
                len(payload["documents"])+len(payload["reviews"])<=120,
                "AUDIT_BATCH_INVALID")
        docs=dict(self.documents);reviews=dict(self.reviews)
        for d in payload["documents"]:
            doc_id=self._validate_document(d)
            require(doc_id not in docs,"AUDIT_DUPLICATE_DOCUMENT")
            docs[doc_id]=d
        for rev in payload["reviews"]:
            issue=self._validate_review(rev,docs)
            require(issue not in reviews,"AUDIT_DUPLICATE_RISK_REVIEW")
            reviews[issue]=rev
        if commit:
            self.documents=docs;self.reviews=reviews

    def submit(self,*,documents:list[dict]|None=None,reviews:list[dict]|None=None) ->dict:
        payload={"schema":"IRE_V5_INCREMENTAL_BATCH_V1", "documents":documents or [],
                 "reviews":reviews or []}
        self._validate_payload(payload,commit=False)
        body={"schema":_EVENT,"sequence":self.seq+1,
              "prev_sha256":self.head,"payload":payload}
        h=sha256(canonical(body));body["event_sha256"]=h
        _exclusive_json(self.events_dir/f"{self.seq+1:06d}_{h}.json",body)
        self.replay()
        return self.status()

    def outstanding(self,*,limit:int=35,after:str|None=None) -> dict:
        require(type(limit) is int and 1<=limit<=150,"AUDIT_PACKET_LIMIT_INVALID")
        pending=[key for key in self.issues if key not in self.reviews]
        if after is not None:
            require(after in self.issues,"AUDIT_BAD_CURSOR")
            pending=[key for key in pending if key>after]
        results=[{"issue_id":key,"issue_sha256":sha256(canonical(self.issues[key])),
                  **self.issues[key]} for key in pending[:limit]]
        return {"schema":"IRE_V5_INCREMENTAL_REVIEW_PACKET_V1", "video_id":self.run.manifest["video_id"],
                "total_risks":len(self.issues),"remaining_risks":len(self.issues)-len(self.reviews),
                "next_cursor":results[-1]["issue_id"] if results else None,
                "issues":results}

    def status(self)->dict:
        total=Counter(case["kind"] for case in self.issues.values())
        reviewed=Counter(self.issues[i]["kind"] for i in self.reviews)
        residual=sorted(k for k,v in self.reviews.items() if v["decision"] in OPEN_DECISIONS)
        return {"schema":"IRE_V5_INCREMENTAL_AUDIT_STATUS_V1",
                "video_id":self.run.manifest["video_id"],
                "original_source_cues":len(self.run.cues),
                "base_source_scope_sealed":self.run.status()["full_video_source_scope_sealed"],
                "base_claims":len(self.run._claims()),"original_event_head":self.run.head,
                "issue_counts":dict(total),"reviewed_counts":dict(reviewed),
                "issues_total":len(self.issues),"issues_reviewed":len(self.reviews),
                "issues_unreviewed":len(self.issues)-len(self.reviews),
                "unresolved_after_review":len(residual),
                "registered_official_document_candidates":len(self.documents),
                "official_document_reuse_links":sum(bool(v.get("official_doc_id")) for v in self.reviews.values()),
                "incremental_event_count":getattr(self,"seq",0),
                "incremental_head_sha256":getattr(self,"head","0"*64),
                "research_audit_complete_with_declared_open":len(self.reviews)==len(self.issues),
                "official_network_origin_independently_verified":False,
                "independently_approved_financial_facts":0,
                "personal_investment_advice_approved":False,
                "one_turn_five_video_research_go":False,
                "release_verdict":"NO_GO_INDEPENDENT_FACT_AND_SEMANTIC_AUDIT"}


def make_document(*,issuer:str,url:str,captured_text:str,observed_at:str,
                  retrieval_note:str,effective_date_note:str)->dict:
    doc={"schema":DOC_SCHEMA,"issuer":issuer,"url":url,
         "captured_text":captured_text,"content_sha256":sha256(captured_text.encode("utf-8")),
         "observed_at":observed_at,"retrieval_note":retrieval_note,
         "effective_date_note":effective_date_note,
         "network_origin_independently_attested":False,
         "financial_fact_approved":False}
    doc["doc_id"]=_evidence_id(doc)
    return doc
