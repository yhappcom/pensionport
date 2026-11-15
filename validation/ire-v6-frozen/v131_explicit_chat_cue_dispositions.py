"""V131 source-first, explicit cue-by-cue ChatGPT disposition audit.

A deterministic *negative control*, not a semantic model or accuracy proof.
No SRT text is persisted; no model/verdict is generated or assumed.
An all-cue packet is a precondition for, never a replacement of, V123.
"""
from __future__ import annotations

import re
from ire.v6.codec import sha256, json_digest
from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.claim_census import FINANCIAL, QUALIFIER, MULTI_CLAIM

ROLES=frozenset({"ASSERTION","CONTINUATION","CONDITION","EXCEPTION",
                 "REBUTTAL","QUOTE","CONTEXT","QUESTION","OPEN"})
ASSERTION_ROLES=frozenset({"ASSERTION","CONTINUATION","CONDITION","EXCEPTION","REBUTTAL","QUOTE"})
LINK_ROLES=frozenset({"CONTINUATION","CONDITION","EXCEPTION","REBUTTAL"})
SHA=re.compile(r"[0-9a-f]{64}\Z")
ATOM=re.compile(r"[A-Z][A-Z0-9_-]{1,63}\Z")


def _stop(reason):
    raise QualityNotProven("V131_CUE_REVIEW_"+reason)


def make_source_review_queue(source):
    """Zero auto-approval: hashes plus risk hints only, from owner-pinned source."""
    items=[]
    for i in range(source.scope_first_cue, source.scope_last_cue+1):
        cue=source.cues[i-1]
        items.append({"cue_index":i,"cue_text_sha256":sha256(cue.text.encode("utf-8")),
                      "financial_lexical_hint":bool(FINANCIAL.search(cue.text)),
                      "qualifier_lexical_hint":bool(QUALIFIER.search(cue.text)),
                      "multi_atom_lexical_hint":bool(MULTI_CLAIM.search(cue.text)),
                      "review_state":"REVIEW_REQUIRED"})
    return {"schema":"IRE_V131_SOURCE_FIRST_CUE_REVIEW_QUEUE_V1",
            "video_id":source.video_id,"source_sha256":source.source_sha256,
            "manifest_sha256":source.manifest_sha256,
            "scope_first_cue":source.scope_first_cue,
            "scope_last_cue":source.scope_last_cue,
            "total_cues":len(items),
            "financial_hint_cues":sum(x["financial_lexical_hint"] for x in items),
            "qualifier_hint_cues":sum(x["qualifier_lexical_hint"] for x in items),
            "multi_atom_hint_cues":sum(x["multi_atom_lexical_hint"] for x in items),
            "cue_queue_sha256":json_digest(items),"items":items,
            "all_claims_exhausted":False,"v123_final_approved":False,"p0_go":False}


def audit_explicit_chat_dispositions(source, packet, *, required_high_risk_spans=()):
    """Reject any unreviewed cue, fake link, missing risk review, unanchored atom.

    A structurally complete packet is still NOT a V123 PASS. Source ownership,
    semantic adequacy and accuracy must be reviewed separately by ChatGPT.
    """
    if (type(packet) is not dict or set(packet)!={
        "schema","source_sha256","manifest_sha256","reviewer","cue_rows","atoms"}
        or packet["schema"]!="IRE_V131_CHAT_EXPLICIT_CUE_DISPOSITIONS_V1"
        or packet["source_sha256"]!=source.source_sha256
        or packet["manifest_sha256"]!=source.manifest_sha256
        or packet["reviewer"]!="CHATGPT_IN_CHAT"):
        _stop("SOURCE_OR_CHAT_REVIEW_SCHEMA")
    rows=packet["cue_rows"]
    atoms=packet["atoms"]
    indices=range(source.scope_first_cue,source.scope_last_cue+1)
    if type(rows) is not list or len(rows)!=len(indices) or type(atoms) is not list:
        _stop("CUE_CENSUS_INCOMPLETE")
    if type(required_high_risk_spans) not in (tuple,list):
        _stop("HIGH_RISK_SPAN_SCHEMA")
    risks=set()
    for span in required_high_risk_spans:
        if (type(span) not in (tuple,list) or len(span)!=2 or
            any(type(x) is not int for x in span) or
            span[0]<source.scope_first_cue or span[1]>source.scope_last_cue or span[0]>span[1]):
            _stop("HIGH_RISK_SPAN_OUTSIDE_SOURCE")
        risks.update(range(span[0],span[1]+1))
    atoms_by_id={}
    for atom in atoms:
        if type(atom) is not dict or set(atom)!={"atom_id","proposition","source_cues","speech_act",
                    "context_constraints","chat_private_review_sha256"}:
            _stop("ATOM_SCHEMA")
        aid=atom["atom_id"]
        if (type(aid) is not str or not ATOM.fullmatch(aid) or aid in atoms_by_id or
            type(atom["proposition"]) is not str or len(atom["proposition"].strip())<5 or
            type(atom["source_cues"]) is not list or not atom["source_cues"] or
            atom["source_cues"]!=sorted(set(atom["source_cues"])) or
            any(type(c) is not int or c not in indices for c in atom["source_cues"]) or
            atom["speech_act"] not in ASSERTION_ROLES or
            type(atom["context_constraints"]) is not list or
            type(atom["chat_private_review_sha256"]) is not str or
            not SHA.fullmatch(atom["chat_private_review_sha256"])):
            _stop("ATOM_INVALID_OR_UNPINNED")
        atoms_by_id[aid]=atom
    if not atoms_by_id and any(FINANCIAL.search(source.cues[i-1].text) for i in indices):
        _stop("ZERO_CLAIMS_SUSPICIOUS_FINANCIAL_SOURCE")
    cue_seen={}
    linked={}
    open_count=0
    for expect,row in zip(indices,rows):
        cue=source.cues[expect-1]
        exact={"cue_index","cue_text_sha256","role","atom_ids","rationale","risk_checked","review_state"}
        if type(row) is not dict or set(row)!=exact:
            _stop("ROW_SCHEMA")
        role=row["role"]
        if (type(row["cue_index"]) is not int or row["cue_index"]!=expect or
            row["cue_text_sha256"]!=sha256(cue.text.encode("utf-8")) or
            role not in ROLES or type(row["atom_ids"]) is not list or
            row["atom_ids"]!=sorted(set(row["atom_ids"])) or
            any(a not in atoms_by_id for a in row["atom_ids"]) or
            type(row["rationale"]) is not str or len(row["rationale"].strip())<12 or
            type(row["risk_checked"]) is not bool or
            row["review_state"] not in {"REVIEWED","OPEN"}):
            _stop("CUE_INDEX_SHA_ROLE_OR_NOTE_INVALID")
        requires_anchor=role in ASSERTION_ROLES
        if (requires_anchor and not row["atom_ids"] or
            not requires_anchor and row["atom_ids"]):
            _stop("SPEECH_ACT_ANCHOR_INCONSISTENT")
        if (role=="OPEN") != (row["review_state"]=="OPEN"):
            _stop("OPEN_ROLE_REVIEW_INCONSISTENT")
        if role in LINK_ROLES:
            for aid in row["atom_ids"]:
                if min(atoms_by_id[aid]["source_cues"])>=expect:
                    _stop("CROSS_CUE_CONTEXT_PARENT_NOT_EARLIER")
        if any(x in cue.text for x in ("보장","언제나")) or expect in risks:
            if not row["risk_checked"]:
                _stop("HIGH_RISK_SOURCE_CUE_NOT_ADJUDICATED")
            if role in {"CONTEXT","QUESTION"} and len(row["rationale"].strip())<25:
                _stop("HIGH_RISK_EXCLUSION_NEEDS_EXPLICIT_REASON")
        if (FINANCIAL.search(cue.text) or QUALIFIER.search(cue.text) or
            MULTI_CLAIM.search(cue.text)) and not row["risk_checked"]:
            _stop("FINANCE_CONTEXT_OR_COMPOUND_NOT_REVIEWED")
        cue_seen[expect]=row
        linked[expect]=set(row["atom_ids"])
        open_count+=int(role=="OPEN")
    for aid,atom in atoms_by_id.items():
        used=[i for i in indices if aid in linked[i]]
        if used!=atom["source_cues"]:
            _stop("ATOM_PARENT_OR_CONTINUATION_ANCHOR_DRIFT")
    # Presence of explicit dispositions is NOT independent verification that
    # every spoken atom was correctly detected or that V123 finance is true.
    return {"schema":"IRE_V131_CUE_DISPOSITION_AUDIT_V1",
            "source_sha256":source.source_sha256,
            "manifest_sha256":source.manifest_sha256,
            "cue_rows_checked":len(rows),"declared_atoms":len(atoms),
            "unresolved_open_cues":open_count,
            "status":"HOLD_OPEN_CUE_DISPOSITIONS" if open_count else
                     "EXPLICIT_CUE_DISPOSITIONS_CHECKED_NOT_V123_APPROVED",
            "cue_dispositions_sha256":json_digest(rows),
            "all_atomic_claims_exhausted":False,
            "independent_recall_verified":False,
            "v123_chat_final_gate_passed":False,
            "owner_inventory_independently_signed":False,
            "knowledge_export_authorized":False,
            "p0_go":False}
