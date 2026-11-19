"""V174: owner-source-pinned fresh in-chat research -> UNRELEASED native V6 exchange.

This bridge takes *fresh original SRT*, source-first ChatGPT review and cue census.
No historical atom exchange, V123 review, E4 authority, or knowledge DB is read.
Uses the actual frozen ``ire.v6.source.verify_source`` and
``ire.v6.atomic_exchange.audit_host_atomic_exchange`` in the same process.

A V6 *structural* PASS is NEVER a semantic/financial/parent E4 approval.
Unanchored cues, missing speaker identity, and unverified conditions remain OPEN.
Source-tied reexpressions must be explicitly supplied; no silent rewriting.
Owner raw source and the returned packets must stay private.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
import math
import re

from ire.v6.atomic_exchange import NUMBER, audit_host_atomic_exchange
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import parse_srt, verify_source

SCHEMA = "IRE_V174_FRESH_OWNER_NATIVE_V6_STRUCTURAL_DRAFT_NOT_APPROVED_V1"
FRESH_ID = re.compile(r"FRESH-(\d{4,8})\Z")
ALLOWED_KINDS = {"FACT", "HYPOTHETICAL", "QUESTION", "OPINION", "RECOMMENDATION", "MATH"}


def _require(condition, reason):
    if not condition:
        raise InvalidInput("V174_FRESH_BRIDGE_" + reason)


def _normalized_numeric(value):
    return re.sub(r"\s+", "", value)


def _digits_missing(proposition, source, first, last):
    seen = {_normalized_numeric(tok)
            for index in range(first, last+1)
            for tok in NUMBER.findall(source.cues[index-1].text)}
    return [tok for tok in NUMBER.findall(proposition)
            if _normalized_numeric(tok) not in seen]


def compile_fresh_native_v6(raw, fresh_review, full_cue_census, *,
                             owner_pinned_source_sha256, expected_video_id,
                             expected_scope_count, scope_width=120,
                             reviewed_source_reexpressions=None):
    """Compile and **actually run frozen native V6** against each new child.

    All source and text pins must match. Model judgments are *not* inferred
    from source or reexpressions. No V123 review/host transaction is minted.
    `reviewed_source_reexpressions`: explicit, private owner-source-pinned
    correction records with `original_claim_sha256`, `new_proposition`,
    `reason`, and optionally `corrected_source_ref`. Each correction will be
    marked as requiring a new in-chat secondary meaning review.
    """
    _require(type(raw) is bytes and type(owner_pinned_source_sha256) is str
             and sha256(raw)==owner_pinned_source_sha256, "SOURCE_SHA_NOT_OWNER_PINNED")
    _require(type(fresh_review) is dict and type(full_cue_census) is dict,
             "FRESH_INPUTS_REQUIRED")
    _require(type(expected_video_id) is str and len(expected_video_id)==11,
             "VIDEO_PIN_REQUIRED")
    _require(type(expected_scope_count) is int and expected_scope_count>=1
             and type(scope_width) is int and scope_width>=1, "SCOPE_CENSUS_REQUIRED")
    reviews=fresh_review.get("fresh_manual_claims")
    scope_rows=fresh_review.get("scope_census")
    meta=fresh_review.get("metadata",{})
    cue_rows=full_cue_census.get("cues")
    _require(type(reviews) is list and len(reviews)>=1
             and type(scope_rows) is list and type(cue_rows) is list,
             "FRESH_REVIEW_AND_ALL_CUES_REQUIRED")
    source_cues=parse_srt(raw)
    cue_count=len(source_cues)
    _require(cue_count==len(cue_rows) and len(scope_rows)==expected_scope_count
             and math.ceil(cue_count/scope_width)==expected_scope_count,
             "COMPLETE_VIDEO_SCOPE_CENSUS")
    _require(meta.get("source_cue_count")==cue_count and
             meta.get("source_bytes")==len(raw) and
             meta.get("video_id")==expected_video_id and
             meta.get("original_source_sha256")==owner_pinned_source_sha256 and
             meta.get("previous_research_consumed") is False and
             meta.get("manual_source_anchored_claim_count")==len(reviews) and
             meta.get("scope_count")==expected_scope_count and
             meta.get("native_v123_final_gate_replayed") is False and
             meta.get("actual_e4_status")=="HOLD" and
             meta.get("e5_authorized") is False,
             "NOT_A_NEW_UNAPPROVED_OWNER_INPUT")
    _require(full_cue_census.get("source_sha256")==owner_pinned_source_sha256,
             "CUE_CENSUS_SOURCE_DRIFT")
    reviewed_source_reexpressions=deepcopy(reviewed_source_reexpressions or {})
    _require(type(reviewed_source_reexpressions) is dict,
             "UNTRUSTED_SOURCE_REEXPRESSIONS")
    original_claims={}
    for row in reviews:
        cid=row.get("id") if type(row) is dict else None
        _require(type(cid) is str and FRESH_ID.fullmatch(cid)
                 and cid not in original_claims, "DUPLICATE_OR_BAD_RESEARCH_CLAIM")
        original_claims[cid]=row
    _require(len(reviews)==len(original_claims)
             and set(reviewed_source_reexpressions) <= set(original_claims),
             "CORRECTION_WITHOUT_ORIGINAL")
    # Fresh source-first complete *cue* census is a necessary (not sufficient)
    # condition. It is not independent semantic recall, and the V6 review
    # will not promote generic context links to source_refs.
    prelim_counts=Counter()
    context_counts=Counter()
    for pos,row in enumerate(cue_rows,1):
        _require(type(row) is dict and row.get("cue_index")==pos
                 and row.get("cue_sha256")==sha256(source_cues[pos-1].text.encode()),
                 "FRESH_CUE_INDEX_OR_SHA_DRIFT")
        status=row.get("cue_source_first_disposition")
        _require(type(status) is str and bool(status),"MISSING_CUE_DISPOSITION")
        prelim_counts[status]+=1
        context_ids=row.get("new_manual_review_context_claim_ids")
        _require(type(context_ids) is list and
                 len(context_ids)==len(set(context_ids)), "BAD_CUE_CONTEXT_IDS")
        for cid in context_ids:
            _require(cid in original_claims,"UNKNOWN_CUE_CONTEXT_CLAIM")
            span=original_claims[cid]["source_cue_span"]
            _require(span["first"]<=pos<=span["last"],"CONTEXT_SPAN_DRIFT")
            context_counts[cid]+=1
    _require(set(context_counts)==set(original_claims),"UNLINKED_FRESH_MEANING_UNIT")

    # A source reexpression is *always* separately flagged and unapproved;
    # verify the original immutable record and the original cue bytes.
    matched=[]; blocked=[]; corrections=[]; anchors=defaultdict(list)
    for original in reviews:
        row=deepcopy(original)
        cid=row["id"]
        x=reviewed_source_reexpressions.get(cid)
        if x is not None:
            _require(type(x) is dict and set(x) in (
                {"original_claim_sha256","source_sha256","new_proposition","reason"},
                {"original_claim_sha256","source_sha256","new_proposition","reason","corrected_source_ref"})
                and x["original_claim_sha256"]==json_digest(original)
                and x["source_sha256"]==owner_pinned_source_sha256
                and type(x["new_proposition"]) is str
                and x["reason"] in {
                    "SOURCE_NUMERIC_NOTATION_RECONCILED_IN_CHAT",
                    "ONE_CHAR_CUE_REANCHORED_IN_CHAT",
                }, "SOURCE_REEXPRESSION_UNATTESTED_OR_CHANGED")
            row["claim"]=x["new_proposition"]
            if "corrected_source_ref" in x:
                row["source_ref"]=deepcopy(x["corrected_source_ref"])
            corrections.append({"fresh_id":cid,"original_claim_sha256":x["original_claim_sha256"],
                                "new_proposition_sha256":sha256(row["claim"].encode()),
                                "reason":x["reason"],"requires_secondary_chat_meaning_review":True})
        match=FRESH_ID.fullmatch(cid)
        native_id=f"C{int(match.group(1)):05d}"
        span=row.get("source_cue_span")
        ref=row.get("source_ref")
        _require(type(span) is dict and type(ref) is dict,
                 "SOURCE_SPAN_AND_ORIGINAL_REF_REQUIRED")
        first,last=span["first"],span["last"]
        at=ref["cue_index"]
        _require(type(first) is int and type(last) is int and
                 1<=first<=at<=last<=cue_count and
                 (first-1)//scope_width==(last-1)//scope_width and
                 row["segment_id"]==f"B{(at-1)//scope_width+1:04d}",
                 "SEGMENT_OR_CROSS_BORDER_CLAIM")
        quote=ref["quote"]
        _require(type(quote) is str and bool(quote.strip())
                 and quote in source_cues[at-1].text
                 and ref["original_cue_sha256"]==sha256(source_cues[at-1].text.encode()),
                 "ORIGINAL_CUE_QUOTE_HASH_OR_CONTEXT_DRIFT")
        _require(type(row["conditions_exceptions_and_limitations"]) is str
                 and bool(row["conditions_exceptions_and_limitations"].strip()),
                 "ORIGINAL_CONDITION_WARNING_NOT_PRESERVED")
        miss=_digits_missing(row["claim"],_PseudoSource(source_cues),first,last)
        if len(quote.strip())<2 or miss:
            blocked.append({"fresh_id":cid,"native_id":native_id,
                            "reason":"V6_SOURCE_REF_TOO_SHORT" if len(quote.strip())<2
                              else "V6_NUMERIC_TOKENS_NOT_IN_CONTEXT",
                            "unanchored_number_tokens":miss,
                            "high_risk":row["high_risk"]})
            continue
        matched.append((row,native_id))
        anchors[at].append(native_id)

    native_children=[]; crosswalk=[]
    for index in range(1,expected_scope_count+1):
        sid=f"B{index:04d}"
        first=(index-1)*scope_width+1
        last=min(index*scope_width,cue_count)
        info=scope_rows[index-1]
        _require(info["segment_id"]==sid and
                 info["first_cue"]==first and info["last_cue"]==last,
                 "FRESH_CHILD_SEGMENT_PLAN_CHANGED")
        window_id=f"W{index:05d}"
        manifest={
            "schema":"IRE_V6_SOURCE_PLAN_V1", "video_id":expected_video_id,
            "source_sha256":owner_pinned_source_sha256, "cue_count":cue_count,
            "scope":{"mode":"PARTIAL","first_cue":first,"last_cue":last},
            "windows":[{"window_id":window_id,"first_cue":first,"last_cue":last,
                "text_sha256":sha256(" ".join(source_cues[i-1].text
                    for i in range(first,last+1)).encode())}],
        }
        # Native source checks both full original bytes and this exact child
        # plan; passing a different SRT or any out-of-scope cue is refused.
        source=verify_source(raw,manifest,
                  expected_source_sha256=owner_pinned_source_sha256,
                  expected_manifest_sha256=json_digest(manifest))
        dispositions=[]
        for i in range(first,last+1):
            anchor_ids=sorted(anchors[i])
            text=source_cues[i-1].text
            dispositions.append({"cue_index":i,"cue_text_sha256":sha256(text.encode()),
                "disposition":"CANDIDATES" if anchor_ids else "UNRESOLVED",
                "claim_ids":anchor_ids,"numeric_tokens":NUMBER.findall(text),
                "note":"" if anchor_ids else "문맥 연결 또는 비주장 예비 분류만 완료. 원자 전수 판정은 OPEN"})
        atoms=[]
        for row,native_id in matched:
            anchor=row["source_ref"]["cue_index"]
            if not first<=anchor<=last:continue
            a=row["source_cue_span"]
            context=list(range(a["first"],a["last"]+1))
            numeric_refs=[{"cue_index":idx,"token":token} for idx in context
                          for token in NUMBER.findall(source_cues[idx-1].text)]
            _require(len(numeric_refs)<=80,"NUMERIC_CONTEXT_TOO_LARGE")
            source_kind=row["speech_act_kind"]
            kind=source_kind if source_kind in ALLOWED_KINDS else "FACT"
            atom={"claim_id":native_id,"owner_window_id":window_id,
                  "proposition":row["claim"],"kind":kind,"stance":"UNRESOLVED",
                  "speaker":"UNKNOWN", "source_refs":[{
                      "cue_index":anchor,"quote":row["source_ref"]["quote"]}],
                  "context_cue_indices":context,"condition_cue_indices":[],
                  "exception_cue_indices":[], "numeric_references":numeric_refs,"as_of":None}
            atoms.append(atom)
            crosswalk.append({"fresh_id":row["id"],"native_id":native_id,
               "original_speech_act_kind":source_kind,
               "original_speaker_stance":row["speaker_stance"],
               "condition_exception_caution":row["conditions_exceptions_and_limitations"],
               "high_risk":row["high_risk"],
               "source_semantic_status":row["chat_semantic_status"],
               "requires_in_chat_native_v123_review":True,
               "source_reexpression_requires_independent_meaning_review":row["id"] in reviewed_source_reexpressions,
               "v123_review_status":"OPEN","e4_authorized":False})
        exchange={"schema":"IRE_V6_HOST_ATOMIC_EXCHANGE_V1",
            "video_id":expected_video_id,"source_sha256":owner_pinned_source_sha256,
            "manifest_sha256":json_digest(manifest),
            "cue_dispositions":dispositions,"atoms":atoms}
        # Actual frozen V6 source and atomic-exchange validators.
        native_audit=audit_host_atomic_exchange(source,exchange)
        _require(native_audit["status"]=="HOST_ATOM_EXCHANGE_STRUCTURAL_REVIEW_ONLY"
                 and native_audit["research_complete"] is False
                 and native_audit["all_atomic_claims_exhausted"] is False,
                 "FROZEN_NATIVE_AUDIT_MUST_NOT_CERTIFY_MEANING")
        native_children.append({"segment_id":sid,"manifest":manifest,
            "exchange":exchange,"native_v6_structural_audit":native_audit})
    _require(len(native_children)==expected_scope_count and
             sum(len(x["exchange"]["atoms"]) for x in native_children)==len(matched),
             "ALL_NATIVE_CHILD_CLAIMS_NOT_RECONCILED")
    anchored_cues=sum(d["disposition"]=="CANDIDATES" for child in native_children
                      for d in child["exchange"]["cue_dispositions"])
    native_open=sum(d["disposition"]=="UNRESOLVED" for child in native_children
                    for d in child["exchange"]["cue_dispositions"])
    _require(anchored_cues+native_open==cue_count,"NATIVE_FULL_CUE_CENSUS")
    summary={"schema":SCHEMA,"video_id":expected_video_id,
        "owner_source_sha256":owner_pinned_source_sha256,
        "source_cue_count":cue_count,"scopes_native_structurally_checked":len(native_children),
        "fresh_meaning_units":len(reviews),"native_v6_candidate_atoms":len(matched),
        "v6_unconverted_meaning_units":len(blocked),
        "source_reexpressions_pending_secondary_review":len(corrections),
        "original_fresh_high_risk_count":sum(x["high_risk"] for x in reviews),
        "native_high_risk_candidate_count":sum(x[0]["high_risk"] for x in matched),
        "cues_with_direct_claim_quote":anchored_cues,"cues_still_v6_unresolved":native_open,
        "v6_semantic_recall_proven":False,"v6_speaker_stance_confirmed":False,
        "v6_conditions_exceptions_confirmed":False,
        "native_v123_chat_approval":False,"native_e4_approved_children":0,
        "e5_authorized":False,"research_knowledge_published":False}
    return {"summary":summary,"native_children_private":native_children,
        "unconverted_private":blocked,"source_reexpressions_private":corrections,
        "source_semantic_crosswalk_private":crosswalk}


class _PseudoSource:
    def __init__(self,cues):self.cues=cues