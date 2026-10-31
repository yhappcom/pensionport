#!/usr/bin/env python3
"""V3.3 independently reviewable atomic financial semantic frames.

Takes ORIGINAL SRT bytes and a separately produced atomic claim plus typed
annotation; verifies provenance, numeric scope, event/action/subject and
attestation. Never guesses missing financial roles from keywords and never
promotes relation similarity to financial truth. This is *not* a model of
independent human reviewers, and signatures alone cannot establish identity.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import hashlib
import hmac
import re
import secrets

from v30_verified_core import (
    parse_srt,verify_ledger,sha256,canonical,guard,CLAIM_RE,HASH_RE,VERDICTS,decimal,
    verify_attestation,
)

SCHEMA="V33_ATOMIC_FINANCIAL_SEMANTIC_FRAME_V1"
TYPES=frozenset((
 "ACCOUNT","FUND","ETF","STOCK","BOND","INSURANCE","DEPOSIT",
 "INDEX","CURRENCY","GOVERNMENT","INVESTOR","FINANCIAL_INSTITUTION",
 "PORTFOLIO","TRANSACTION","CASHFLOW","MARKET","OTHER"
))
EVENTS=frozenset((
 "PRODUCT_STRUCTURE","ACCOUNT_ELIGIBILITY","ACCOUNT_CONTRIBUTION",
 "ACCOUNT_WITHDRAWAL","TAX_CONTRIBUTION","TAX_WITHDRAWAL",
 "GOVERNMENT_MATCH","DISTRIBUTION","FUND_PRICE_VS_NAV",
 "INDEX_TRACKING","COST_FEE","MARKET_POLICY_RATE","PRODUCT_YIELD",
 "MATURITY_REPAYMENT","PERFORMANCE_MODEL","PORTFOLIO_ALLOCATION",
 "MARKET_TRADING_HALTS","TRADING_METHOD","INVESTMENT_BEHAVIOR",
 "MARKET_EVENT","FINANCIAL_OTHER"
))
ACTIONS=frozenset((
 "DEFINE","REQUIRE","QUALIFY","CONTRIBUTE","WITHDRAW","TAX",
 "PAY","DISTRIBUTE","TRACK","COMPARE","VALUE","CHARGE",
 "TRADE","HALT","MATURE","REPAY","CALCULATE","ALLOCATE",
 "REBALANCE","FORECAST","ADVISE","OBSERVE","OTHER"
))
MODALITY=frozenset((
 "ASSERTED","CONDITIONAL","HYPOTHETICAL","NEGATED",
 "OPINION","UNRESOLVED"
))
MEASURE_TYPES=frozenset((
 "NONE","CURRENCY_AMOUNT","PERCENT_RATE","INDEX_POINTS",
 "DURATION","SHARE_COUNT","RATIO","OTHER"
))
RATE_BASES=frozenset((
 "NOT_APPLICABLE","EFFECTIVE_ANNUAL","NOMINAL_ANNUAL",
 "CENTRAL_BANK_POLICY_RATE","PRODUCT_PROMISED_YIELD",
 "EXPECTED_RETURN","COST_PERCENTAGE","GOVERNMENT_MATCH_RATE",
 "REGULATORY_TAX_RATE","UNRESOLVED"
))
SOURCE_CLASSES=frozenset(("REAL_ORIGINAL","SYNTHETIC_FIXTURE"))
REVIEW_STATUS=frozenset(("PROPOSED","STRUCTURE_REVIEWED"))
NEW_SOURCE_VERDICT="ORIGINAL_UNEVALUATED"
ALL_VERDICTS=VERDICTS|{NEW_SOURCE_VERDICT}
_SEAL=secrets.token_bytes(32)

def validate_entity(value):
    guard(type(value) is dict and set(value)=={"kind","canonical_id"}
          and value["kind"] in TYPES
          and isinstance(value["canonical_id"],str)
          and 2<=len(value["canonical_id"])<=160
          and not any(ord(ch)<32 for ch in value["canonical_id"]),
          "ENTITY_TYPE_CANONICAL_ID_REQUIRED")
    return True

def validate_measurement(m):
    guard(type(m) is dict and set(m)=={
        "measure_type","value","unit","period","rate_basis"},
        "EXPLICIT_COMPLETE_MEASUREMENT_FRAME_REQUIRED")
    guard(m["measure_type"] in MEASURE_TYPES and
          m["rate_basis"] in RATE_BASES and
          isinstance(m["unit"],str) and bool(m["unit"]) and
          isinstance(m["period"],str) and bool(m["period"]),
          "INVALID_FINANCIAL_RATE_UNIT_OR_PERIOD")
    if m["measure_type"]=="NONE":
        guard(m["value"] is None and m["rate_basis"]=="NOT_APPLICABLE" and
              m["unit"]=="NOT_APPLICABLE" and
              m["period"]=="NOT_APPLICABLE",
              "NONE_MEASURE_CANNOT_CARRY_PSEUDO_NUMBER")
    else:
        guard(m["value"] is not None,"NUMERIC_MEASURE_MUST_HAVE_VALUE")
        decimal(m["value"])
    if m["measure_type"]=="PERCENT_RATE":
        guard(m["rate_basis"] not in ("NOT_APPLICABLE",)
              and m["unit"]=="PERCENT",
              "RATE_CANNOT_DROP_DENOMINATOR_OR_FINANCIAL_BASIS")
    elif m["measure_type"]!="NONE":
        guard(m["rate_basis"]=="NOT_APPLICABLE",
              "NON_RATE_MUST_NOT_CARRY_RATE_BASIS")
    return True

def validate_financial_frame(frame):
    guard(type(frame) is dict and frame.get("schema")==SCHEMA,
          "V33_FRAME_SCHEMA_REQUIRED")
    required={
      "schema","claim_id","source_video_id","source_srt_sha256",
      "source_atomic_ledger_sha256",
      "claim_text","claim_text_sha256","cue_indices","source_quote",
      "subject","object","action","event_kind","modality",
      "jurisdiction","effective_date","conditions","measurement",
      "legacy_verdict","evidence_state","annotation_origin",
      "annotation_review_status","source_class"
    }
    guard(set(frame)==required,"FRAME_FIELDS_MISSING_EXTRA_OR_SPOOFED")
    cid=frame["claim_id"];vid=frame["source_video_id"]
    guard(isinstance(cid,str) and CLAIM_RE.fullmatch(cid)
          and isinstance(vid,str) and cid.startswith(vid+"-"),
          "FRAME_CLAIM_NOT_BOUND_TO_SOURCE_VIDEO")
    guard(type(frame["source_srt_sha256"]) is str and
          HASH_RE.fullmatch(frame["source_srt_sha256"]) and
          type(frame["source_atomic_ledger_sha256"]) is str and
          HASH_RE.fullmatch(frame["source_atomic_ledger_sha256"]) and
          isinstance(frame["claim_text"],str)
          and 5<=len(frame["claim_text"])<=5000 and
          frame["claim_text_sha256"]==
             sha256(frame["claim_text"].encode("utf-8")) and
          isinstance(frame["source_quote"],str)
          and 4<=len(frame["source_quote"])<=5000,
          "FRAME_SOURCE_TEXT_OR_DIGEST_INVALID")
    indices=frame["cue_indices"]
    guard(type(indices) is list and indices and len(indices)<=100
          and all(type(i) is int and i>0 for i in indices)
          and indices==sorted(set(indices)),
          "SOURCE_CUE_MAPPING_MUST_BE_UNIQUE_ORDERED_AND_NONEMPTY")
    validate_entity(frame["subject"]);validate_entity(frame["object"])
    guard(frame["action"] in ACTIONS and frame["event_kind"] in EVENTS
          and frame["modality"] in MODALITY and
          frame["source_class"] in SOURCE_CLASSES
          and frame["legacy_verdict"] in ALL_VERDICTS,
          "FINANCIAL_EVENT_ACTION_MODES_OR_VERDICT_INVALID")
    d=frame["effective_date"]
    guard(d=="UNRESOLVED" or (
          isinstance(d,str) and
          re.fullmatch(r"\d{4}-\d{2}-\d{2}",d) is not None
          and date.fromisoformat(d).isoformat()==d),
          "FINANCIAL_EFFECTIVE_DATE_INVALID")
    guard(frame["jurisdiction"]=="UNRESOLVED" or
          (isinstance(frame["jurisdiction"],str) and
           re.fullmatch(r"[A-Z]{2}",frame["jurisdiction"])),
          "INVALID_JURISDICTION_OR_UNRESOLVED_FLAG")
    conditions=frame["conditions"]
    guard(type(conditions) is dict and
          set(conditions)=={"population","exception","trigger"} and
          all(isinstance(v,str) and bool(v) and len(v)<=3000
              for v in conditions.values()),
          "FINANCIAL_POPULATION_EXCEPTION_TRIGGER_ARE_REQUIRED")
    validate_measurement(frame["measurement"])
    guard(frame["evidence_state"] in (
            "NOT_RESEARCHED","OPEN","CORRECTION_ONLY",
            "PRIMARY_EVIDENCE_PENDING","HUMAN_REVIEW_REQUIRED")
          and frame["annotation_origin"] in (
            "EXTERNAL_EXTRACTOR","MANUAL_REVIEWER","TEST_FIXTURE")
          and frame["annotation_review_status"] in REVIEW_STATUS,
          "NO_SELF_DECLARED_EVIDENCE_COMPLETION_FROM_SEMANTIC_FRAME")
    if frame["source_class"]=="REAL_ORIGINAL":
        guard(frame["annotation_origin"]!="TEST_FIXTURE",
              "SYNTHETIC_ANNOTATOR_CANNOT_APPROVE_REAL_SOURCE")
    if frame["legacy_verdict"]=="CONTRADICTED":
        guard(frame["evidence_state"]=="CORRECTION_ONLY",
              "REFUTED_HISTORICAL_CLAIM_CANNOT_BE_POSITIVELY_PROMOTED")
    if frame["legacy_verdict"]==NEW_SOURCE_VERDICT:
        guard(frame["evidence_state"]=="NOT_RESEARCHED",
              "NEW_FINANCIAL_CLAIM_CANNOT_HAVE_HISTORICAL_APPROVED_VERDICT")
    return True

def validate_atomic_ledger_for_v33(cues,ledger,video_id):
    """Read-only structural V3 ledger check with a *new-source* sentinel.

    Only for verification: substitute SPEAKER_OPINION in a temporary copy
    because V3.0's frozen ledger checker predates ORIGINAL_UNEVALUATED.
    Never persist the substituted verdict or claim it was original speech.
    """
    import copy
    guard(type(ledger) is dict and
          ledger.get("schema")=="V30_ATOMIC_LEDGER_V2",
          "FULL_ORIGINAL_ATOMIC_LEDGER_REQUIRED")
    tmp=copy.deepcopy(ledger)
    for atom in tmp["claims"]:
        if atom.get("legacy_verdict")==NEW_SOURCE_VERDICT:
            atom["legacy_verdict"]="SPEAKER_OPINION"
    report=verify_ledger(cues,tmp,video_id)
    return report

def check_actual_cue_provenance(frame,raw_srt,reviewed_ledger=None):
    """Exact original bytes + complete original atomic ledger and quote."""
    validate_financial_frame(frame)
    cues=parse_srt(raw_srt,frame["source_srt_sha256"])
    guard(type(reviewed_ledger) is dict
          and sha256(canonical(reviewed_ledger))==
              frame["source_atomic_ledger_sha256"],
          "ATOMIC_FRAME_UNBOUND_TO_COMPLETE_ORIGINAL_LEDGER")
    coverage=validate_atomic_ledger_for_v33(
        cues,reviewed_ledger,frame["source_video_id"])
    atoms={a["claim_id"]:a for a in reviewed_ledger["claims"]}
    guard(frame["claim_id"] in atoms,
          "SOURCE_FRAME_REFERENCES_NONEXISTENT_ATOMIC_LEDGER_CLAIM")
    atom=atoms[frame["claim_id"]]
    guard(atom["cue_indices"]==frame["cue_indices"]
          and atom["quote"]==frame["source_quote"]
          and atom.get("claim_text",atom["quote"])==frame["claim_text"]
          and atom["legacy_verdict"]==frame["legacy_verdict"],
          "SOURCE_FRAME_CONTENT_DOES_NOT_MATCH_ATOMIC_LEDGER")
    guard(all(i<=len(cues) for i in frame["cue_indices"]),
          "FINANCIAL_ATOM_CUE_OUTSIDE_ORIGINAL")
    text="\n".join(cues[i-1].text for i in frame["cue_indices"])
    guard(frame["source_quote"].strip() in text,
          "FINANCIAL_ATOM_QUOTE_NOT_IN_ACTUAL_SRT")
    guard(coverage["missing_or_unmapped_cues"]==0,
          "ORIGINAL_SOURCE_CUE_CENSUS_INCOMPLETE")
    return {
       "schema":"V33_ORIGINAL_SOURCE_ATOMIC_CUE_PROVENANCE_V1",
       "claim_id":frame["claim_id"],
       "source_video_id":frame["source_video_id"],
       "source_srt_sha256":frame["source_srt_sha256"],
       "source_atomic_ledger_sha256":frame["source_atomic_ledger_sha256"],
       "claim_text_sha256":frame["claim_text_sha256"],
       "frame_sha256":sha256(canonical(frame)),
       "cue_indices":frame["cue_indices"],
       "full_cues_parsed":len(cues),
       "original_quote_present":True,
       "financial_semantics_truth_automatically_verified":False,
    }

@dataclass(frozen=True)
class BoundSemanticFrame:
    """Non-serializable authority: claim+frame reviewed in this process."""
    claim_id:str
    frame_digest:str
    source_srt_sha256:str
    legacy_verdict:str
    semantic_frame:dict
    source_reviewer_id:str
    semantic_reviewer_id:str
    _seal:str

def verify_independent_frame(frame,raw_srt,source_attestation,
                             semantic_attestation,authorities,
                             reviewed_ledger=None):
    proof=check_actual_cue_provenance(frame,raw_srt,reviewed_ledger)
    guard(frame["annotation_review_status"]=="STRUCTURE_REVIEWED",
          "SUGGESTED_UNREVIEWED_SEMANTICS_NOT_SEARCH_AUTHORITY")
    guard(type(authorities) is dict and
          "source_reviewer" in authorities and
          "semantic_reviewer" in authorities,
          "DISTINCT_EXTERNAL_SOURCE_AND_SEMANTIC_REVIEW_ROLES_REQUIRED")
    source_payload={
        "video_id":frame["source_video_id"],
        "srt_sha256":frame["source_srt_sha256"],
        "atomic_ledger_sha256":frame["source_atomic_ledger_sha256"],
        "claim_id":frame["claim_id"],
        "claim_text_sha256":frame["claim_text_sha256"],
        "cue_indices":frame["cue_indices"],
        "quote_sha256":sha256(frame["source_quote"].encode("utf-8")),
    }
    source_id=verify_attestation(
        source_attestation,source_payload,"source_reviewer",authorities)
    semantic_payload={
        "frame_sha256":proof["frame_sha256"],
        "source_payload_sha256":sha256(canonical(source_payload)),
        "review_scope":"FINANCIAL_STRUCTURE_NOT_FINANCIAL_TRUTH",
    }
    semantic_id=verify_attestation(
        semantic_attestation,semantic_payload,
        "semantic_reviewer",authorities)
    guard(source_id!=semantic_id,
          "SOURCE_AND_SEMANTIC_REVIEWER_MUST_BE_DIFFERENT_PERSON")
    fields={
        "claim_id":frame["claim_id"],
        "frame_digest":proof["frame_sha256"],
        "source_srt_sha256":frame["source_srt_sha256"],
        "legacy_verdict":frame["legacy_verdict"],
        "semantic_frame":frame,
        "source_reviewer_id":source_id,
        "semantic_reviewer_id":semantic_id,
    }
    seal=hmac.new(_SEAL,canonical(fields),hashlib.sha256).hexdigest()
    return BoundSemanticFrame(**fields,_seal=seal)

def verified_frame(bound):
    guard(isinstance(bound,BoundSemanticFrame),
          "UNVERIFIED_DICTIONARY_CANNOT_IMPERSONATE_REVIEWED_FRAME")
    f={k:getattr(bound,k) for k in (
        "claim_id","frame_digest","source_srt_sha256",
        "legacy_verdict","semantic_frame",
        "source_reviewer_id","semantic_reviewer_id")}
    expected=hmac.new(_SEAL,canonical(f),hashlib.sha256).hexdigest()
    guard(hmac.compare_digest(expected,bound._seal)
          and bound.frame_digest==sha256(canonical(bound.semantic_frame)),
          "TAMPERED_BOUND_FINANCIAL_SEMANTIC_FRAME")
    return bound.semantic_frame

def semantic_relation_for_review(a,b):
    """Provenance-checked, *candidate-only* financial semantic comparison."""
    left=verified_frame(a);right=verified_frame(b)
    guard(left["claim_id"]!=right["claim_id"],
          "SAME_FINANCIAL_ATOM_CANNOT_BE_A_RELATION")
    risk=("CORRECTION_ONLY" if "CONTRADICTED" in
          (left["legacy_verdict"],right["legacy_verdict"]) else
          "UNVERIFIED_NEW_SOURCE_ONLY" if NEW_SOURCE_VERDICT in
          (left["legacy_verdict"],right["legacy_verdict"]) else
          "UNREPLICATED_HYPOTHETICAL_SOURCE" if "HYPOTHETICAL" in
          (left["legacy_verdict"],right["legacy_verdict"]) else
          "HUMAN_REVIEW_ONLY")
    event_same=left["event_kind"]==right["event_kind"]
    action_same=left["action"]==right["action"]
    subject_same=left["subject"]==right["subject"]
    object_same=left["object"]==right["object"]
    different_rate_basis=(left["measurement"]["measure_type"]=="PERCENT_RATE"
         and right["measurement"]["measure_type"]=="PERCENT_RATE"
         and left["measurement"]["rate_basis"]!=
             right["measurement"]["rate_basis"])
    if different_rate_basis:
        relationship="FINANCIAL_RATE_BASIS_SCOPE_DIFFERENT"
    elif event_same and action_same and subject_same and object_same:
        relationship="SAME_FINANCIAL_EVENT_REVIEW_CANDIDATE"
    elif event_same and (subject_same or object_same):
        relationship="QUALIFIES_FINANCIAL_EVENT_REVIEW_CANDIDATE"
    elif left["subject"]==right["subject"] or left["object"]==right["object"]:
        relationship="SHARED_ENTITY_BROAD_AUDIT_ONLY"
    else:
        relationship="UNRESOLVED_BROAD_NONCANDIDATE_AUDIT"
    # Explicit auditable denominators and "unknown" cannot become false
    # proof of no relation. Even different typed events may interact.
    return {
      "schema":"V33_SOURCE_BOUND_TYPED_RELATION_CANDIDATE_V1",
      "claims":sorted((left["claim_id"],right["claim_id"])),
      "event_kind_equal":event_same,"action_equal":action_same,
      "subject_equal":subject_same,"object_equal":object_same,
      "rate_convention_mismatch":different_rate_basis,
      "relation_candidate":relationship,
      "relationship_evidence":None,
      "human_review_required":True,
      "noncandidate_may_hide_relevant_dependency":True,
      "source_risk":risk,
      "independent_external_reviewer_identity_proven_by_code":False,
      "financial_fact_truth_verified":False,
      "automatic_knowledge_merge":False,
      "research_completion_certificate":False,
      "investment_instruction_permitted":False,
    }

def frame_proposal_summary(frame,raw_srt,reviewed_ledger=None):
    """Unreviewed proposal returns blockers, never a knowledge candidate."""
    proof=check_actual_cue_provenance(frame,raw_srt,reviewed_ledger)
    return {
      "schema":"V33_FINANCIAL_FRAME_PROPOSAL_GATE_V1",
      "source_claim_sha256":proof["claim_text_sha256"],
      "frame_sha256":proof["frame_sha256"],
      "source_sha256":proof["source_srt_sha256"],
      "cue_count":proof["full_cues_parsed"],
      "financial_event_kind":frame["event_kind"],
      "event_identity_independently_reviewed":False,
      "human_source_review_required":True,
      "human_semantic_review_required":True,
      "evidence_and_numeric_study_required":True,
      "state":"RESEARCH_BLOCKED",
      "candidate_knowledge_approval":False,
    }
