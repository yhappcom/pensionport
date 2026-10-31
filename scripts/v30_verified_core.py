#!/usr/bin/env python3
"""V3.0 strengthened trust boundary and source-ledger verification (stdlib only).

This module is not a reviewer: it validates provenance, structure, immutable
evidence bytes and authenticated reviewer attestations. It never generates a
human signature, infers a financial fact, or approves a trade.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

# Separate root-of-trust: immutable SOURCE SHA pins and mandatory policy values
# live in executable code, not in an editable contract's own hash manifest.
TRUST_PINS={
 "scripts/v5_candidate_engine_v23.py":"be73e778b7851ba440e40c85629f2f89b6da3648",
 "scripts/v30_integrated_research.py":"7924ad51058abc1129eef2ec91df97589b412f63",
 "v5/policy/research_completion_gate_v1.json":"de602c45572c047170c3fc81a7a16431305a5386",
 "v5/integration/integration_policy_v1.json":"09b7234523ed4f0ea339c59669450f43bd40e51f",
 "v5/integration/v23_first_use_019_020_results_v1.json":"00b6972368e782665156314c6a6d31ff5bf542da",
}
VID_RE=re.compile(r"^[A-Za-z0-9_-]{11}$")
CLAIM_RE=re.compile(r"^[A-Za-z0-9_-]{11}-(?:\d{2,3})$")
HASH_RE=re.compile(r"^[0-9a-f]{64}$")
TIMECODE_RE=re.compile(r"^(\d{2}):(\d{2}):(\d{2})[,.](\d{3})$")
VERDICTS=frozenset(("PRIMARY_CONFIRMED","QUALIFIED","HYPOTHETICAL",
                     "CONTRADICTED","SPEAKER_OPINION"))
CLAIM_TYPES=frozenset(("LEGAL_OR_PRODUCT","NUMERIC",
                       "STRATEGY_OR_PERFORMANCE","QUALITATIVE"))
ROLES=frozenset((
 "PENSION_INCOME_PAYOUT_TAX","PENSION_CONTRIBUTION_LIMIT",
 "PENSION_CONTRIBUTION_TAX_CREDIT","ISA_TRANSFER_TAX_CREDIT",
 "NATIONAL_PENSION_DEFER_BONUS","CIVIL_SERVICE_PENSION_CONTRIBUTION",
 "CIVIL_SERVICE_PENSION_BENEFIT","GIFT_TAX_ALLOWANCE",
 "BOND_DIRECT_MATURITY","BOND_ETF_MATURITY_RISK",
 "RETIREMENT_PENSION_CASHFLOW","RETIREMENT_INCOME_BRIDGE",
 "DIVIDEND_PAYOUT_MODEL","EQUITY_DIVERSIFICATION",
 "GROUP_CONCENTRATION","ETF_MINIMUM_TRADE_LOT",
 "CURRENCY_CONVERSION_COST","PORTFOLIO_ASSET_ALLOCATION",
 "MATHEMATICAL_COMPOUND_GROWTH","FINANCIAL_EDUCATION",
))
ACTIONS=frozenset(("CONTRIBUTE","DEPOSIT","WITHDRAW","TRANSFER","TRADE",
                   "COMPUTE","COMPARE","REBALANCE","DEFER","TAX","HOLD",
                   "DISTRIBUTE","EXPLAIN","PAY"))
RELATION_CODES=frozenset(("SAME_PROPOSITION_CANDIDATE",
 "QUALIFIES_SCOPE_CANDIDATE","CONTRADICTION_REVIEW",
 "CALCULATION_DEPENDENCY_REVIEW","SCOPE_DIFFERENT",
 "TOPIC_ONLY","UNRESOLVED_AMBIGUOUS"))
DATA_DOMAINS=frozenset(("SOURCE_AND_CLAIMS","PRIMARY_EVIDENCE",
                       "QUANT_AND_EMPIRICAL","GENERAL_DECISION"))
DANGEROUS_KEYWORDS=re.compile(r"(?i)(?:-----BEGIN (?:RSA |EC )?PRIVATE KEY-----|"
                             r"\b\d{6}[- ]?[1-4]\d{6}\b|"
                             r"(?<!\w)(?:account_number|owner_income|"
                             r"owner_portfolio|real_portfolio|personal_holdings)(?!\w))")

def guard(ok,reason):
    if not ok:raise ValueError(reason)

def blob_sha(path):
    b=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def canonical(obj):
    return json.dumps(obj,sort_keys=True,ensure_ascii=False,
                      separators=(",",":"),allow_nan=False).encode("utf-8")

def check_privacy(x):
    if isinstance(x,dict):
        for k,v in x.items():
            guard(not DANGEROUS_KEYWORDS.search(k),
                  "POSSIBLE_PRIVATE_FIELD")
            check_privacy(v)
    elif isinstance(x,list):
        for z in x:check_privacy(z)
    elif isinstance(x,str):
        guard(not DANGEROUS_KEYWORDS.search(x),
              "POSSIBLE_PRIVATE_DATA")
    return True

def policy_gate(root):
    """The V3.0 configuration cannot redefine its own protected files."""
    root=Path(root)
    for relative,expected in TRUST_PINS.items():
        path=root/relative
        guard(path.is_file() and blob_sha(path)==expected,
              "TRUSTED_PARENT_FILE_MODIFIED_"+relative)
    p=json.loads((root/"v30/contracts/integrated_engine_v1.json").read_text())
    e=json.loads((root/"v30/contracts/evaluation_protocol_v1.json").read_text())
    expected={k:v for k,v in TRUST_PINS.items()
              if k.startswith("v5/")}
    guard(p["schema"]=="V30_INTEGRATED_RESEARCH_ENGINE_CONTRACT_V1"
          and p["release_stage"]=="ARCHITECTURE_AND_EXECUTABLE_PILOT_ONLY"
          and p["frozen_existing_policy_files"]==expected
          and p["frozen_v23_engine_git_blob_sha"]==
              TRUST_PINS["scripts/v5_candidate_engine_v23.py"],
          "CONTRACT_TRUST_ROOT_WEAKENED")
    safety=p["hard_safety"]
    for flag in ("personal_investment_advice","trade_execution",
                 "automatic_knowledge_merge",
                 "automatic_research_completion_certificate"):
        guard(safety.get(flag) is False,"UNSAFE_CONTRACT_FLAG_"+flag)
    guard(safety["production_release"]=="BLOCKED"
          and safety["no_unseen_video_21_plus_read_during_bootstrap"] is True
          and p["source_of_truth"]["raw_user_srt_must_not_be_committed"] is True
          and p["relation_output"]["claim_truth_inferred_from_similarity"] is False
          and p["relation_output"]["always_review_only"] is True
          and p["evidence_obligations"]["research_is_complete_only_with_independently_audited_certificate"] is True,
          "CRITICAL_CONTRACT_INVARIANT_CHANGED")
    guard(e["schema"]=="V30_EVALUATION_PROTOCOL_V1"
          and e["development_videos_inclusive"]==[1,20]
          and e["protected_out_of_sample_videos_begin_at"]==21
          and e["bootstrap_may_read_new_video_21_plus"] is False
          and e["independent_blind_labelers_required_for_release"] is True
          and e["release_status"].startswith("BLOCKED")
          and e["targets"]["retrieval_recall"]>=0.95
          and e["targets"]["retrieval_precision"]>=0.85
          and e["targets"]["falsely_approved_knowledge_merges_max"]==0,
          "INDEPENDENT_EVALUATION_GATE_WEAKENED")
    return True

@dataclass(frozen=True)
class Cue:
    index:int
    start_ms:int
    end_ms:int
    text:str

def parse_srt(data,expected_sha,limit_bytes=16_000_000):
    """Load full actual subtitle bytes in memory. Never persist original text."""
    guard(isinstance(data,bytes) and 0<len(data)<=limit_bytes,
          "RAW_SRT_NOT_BYTES_OR_TOO_LARGE")
    guard(isinstance(expected_sha,str) and HASH_RE.fullmatch(expected_sha)
          and sha256(data)==expected_sha,"ORIGINAL_SRT_SHA256_MISMATCH")
    try:txt=data.decode("utf-8-sig")
    except UnicodeDecodeError as err:raise ValueError("SRT_UTF8_REQUIRED") from err
    blocks=re.split(r"\n\s*\n",txt.replace("\r\n","\n").strip())
    cues=[]
    for block in blocks:
        lines=block.split("\n")
        guard(len(lines)>=3 and lines[0].strip().isdigit(),
              "MALFORMED_SRT_CUE_INDEX_OR_TEXT")
        num=int(lines[0].strip())
        guard(num==len(cues)+1,"DUPLICATED_GAPPED_OR_OUT_OF_ORDER_CUE")
        span=lines[1].split("-->")
        guard(len(span)==2,"SRT_TIME_SPAN_MISSING")
        def millis(x):
            m=TIMECODE_RE.fullmatch(x.strip())
            guard(m is not None,"INVALID_SRT_TIMECODE")
            h,mn,s,ms=map(int,m.groups())
            guard(mn<60 and s<60,"INVALID_SRT_CLOCK_RANGE")
            return ((h*60+mn)*60+s)*1000+ms
        a,b=map(millis,span)
        guard(a<b and (not cues or a>=cues[-1].start_ms),
              "SRT_NEGATIVE_OR_REVERSED_TIME")
        line="\n".join(lines[2:]).strip()
        guard(bool(line),"SRT_EMPTY_CUE")
        cues.append(Cue(index=num,start_ms=a,end_ms=b,text=line))
    guard(bool(cues),"EMPTY_SRT")
    return tuple(cues)

def verify_ledger(cues,ledger,video_id,legacy_verdicts=None):
    """No subcue material statement may be omitted from reviewed coverage.

    A cue can hold several atomic statements, supplied explicitly in ledger.
    Review signatures are validated separately and do not prove semantic truth.
    """
    guard(isinstance(video_id,str) and VID_RE.fullmatch(video_id),
          "INVALID_VIDEO_ID")
    guard(isinstance(ledger,dict) and ledger.get("schema")=="V30_ATOMIC_LEDGER_V2",
          "FULL_ATOMIC_LEDGER_REQUIRED")
    cs=ledger.get("cues");statements=ledger.get("claims")
    guard(isinstance(cs,list) and len(cs)==len(cues)
          and isinstance(statements,list) and bool(statements),
          "ATOMIC_CUE_COVERAGE_DENOMINATOR_MISMATCH")
    known={}
    mapping={}
    for atom in statements:
        guard(isinstance(atom,dict),"ATOMIC_STATEMENT_INVALID")
        cid=atom.get("claim_id")
        guard(isinstance(cid,str) and CLAIM_RE.fullmatch(cid)
              and cid.startswith(video_id+"-") and cid not in known,
              "UNTRUSTED_OR_DUPLICATE_ORIGINAL_CLAIM_ID")
        ids=atom.get("cue_indices")
        quote=atom.get("quote")
        kinds=atom.get("claim_types")
        guard(isinstance(ids,list) and ids and
              all(type(k) is int and 1<=k<=len(cues) for k in ids)
              and ids==sorted(set(ids)),
              "ATOMIC_CLAIM_MISSING_OR_OUT_OF_RANGE_CUES")
        guard(isinstance(quote,str) and quote.strip() and
              any(quote.strip() in cues[i-1].text for i in ids),
              "ATOMIC_QUOTE_NOT_IN_ORIGINAL_SOURCE")
        guard(isinstance(kinds,list) and kinds and
              len(set(kinds))==len(kinds)
              and set(kinds)<=CLAIM_TYPES,
              "ATOMIC_MATERIAL_CLAIM_TYPES_INVALID")
        verdict=atom.get("legacy_verdict")
        guard(verdict in VERDICTS,"ATOMIC_VERDICT_INVALID")
        if legacy_verdicts is not None:
            guard(cid in legacy_verdicts and verdict==legacy_verdicts[cid],
                  "HISTORIC_VERDICT_SOURCE_SPOOFED")
        known[cid]=atom
        for i in ids:mapping.setdefault(i,set()).add(cid)
    for i,row in enumerate(cs,1):
        guard(type(row) is dict and row.get("cue_index")==i,
              "INCOMPLETE_SRT_CUE_ORDER")
        status=row.get("classification")
        guard(status in ("MATERIAL","NON_MATERIAL"),
              "UNCLASSIFIED_OR_UNREVIEWED_SRT_CUE")
        links=row.get("claim_ids")
        guard(isinstance(links,list) and len(links)==len(set(links))
              and set(links)<=set(known),
              "ATOMIC_CUE_LINK_TO_UNKNOWN_CLAIM")
        guard(set(links)==mapping.get(i,set()),
              "ATOMIC_CUE_CLAIM_REVERSE_LINK_MISMATCH")
        if status=="MATERIAL":
            guard(links,"MATERIAL_SRT_CUE_NOT_LINKED_TO_ATOMIC_CLAIM")
        else:
            guard(not links and isinstance(row.get("nonmaterial_reason"),str)
                  and len(row["nonmaterial_reason"])>=10,
                  "NONMATERIAL_CUE_NEEDS_JUSTIFIED_EXCLUSION")
    guard(all(atom.get("material") is True for atom in statements),
          "UNCLASSIFIED_MATERIAL_ATOMIC_STATEMENT")
    return {
        "schema":"V30_ATOMIC_COVERAGE_REPORT_V2",
        "original_cue_count":len(cues),
        "mapped_material_cues":sum(x["classification"]=="MATERIAL" for x in cs),
        "justified_nonmaterial_cues":sum(x["classification"]=="NON_MATERIAL" for x in cs),
        "individually_traced_atomic_claims":len(known),
        "missing_or_unmapped_cues":0,
        "source_material_statement_completeness_audited_by_human":False,
        "signature_validated_by_this_function":False,
    }

def decimal(x):
    guard(type(x) in (str,int,Decimal),"DECIMAL_INPUT_MUST_NOT_BE_FLOAT")
    try:v=Decimal(str(x))
    except InvalidOperation as err:raise ValueError("INVALID_DECIMAL") from err
    guard(v.is_finite(),"NONFINITE_DECIMAL")
    return v

def frame_check(frame,claim_types=()):
    guard(isinstance(frame,dict),"FINANCIAL_FRAME_REQUIRED")
    req=("subject_type","subject_id","action","object_type","object_id",
         "financial_role","jurisdiction","effective_date","conditions","units")
    for key in req:
        if key=="conditions":
            guard(isinstance(frame.get(key),dict) and frame[key],
                  "EXPLICIT_NONEMPTY_FINANCIAL_CONDITIONS_REQUIRED")
        else:
            guard(isinstance(frame.get(key),str) and frame[key].strip()
                  and frame[key]!="UNKNOWN",
                  "UNKNOWN_OR_MISSING_MATERIAL_FRAME_FIELD_"+key)
    guard(frame["action"] in ACTIONS and frame["financial_role"] in ROLES,
          "UNKNOWN_FINANCIAL_ROLE_OR_ACTION")
    try:
        actual=date.fromisoformat(frame["effective_date"])
    except ValueError as err:
        raise ValueError("INVALID_REAL_CALENDAR_DATE") from err
    guard(actual.isoformat()==frame["effective_date"] and
          re.fullmatch(r"[A-Z]{2}",frame["jurisdiction"]) is not None,
          "INVALID_DATE_FORMAT_OR_JURISDICTION")
    types=set(claim_types)
    guard(types<=CLAIM_TYPES,"UNRECOGNIZED_FINANCIAL_CLAIM_TYPE")
    if "NUMERIC" in types:
        guard("value" in frame and frame.get("units") not in ("", "UNKNOWN")
              and "period" in frame and bool(frame["period"]),
              "NUMERIC_CLAIM_MUST_HAVE_VALUE_PERIOD_AND_UNIT")
    if "value" in frame:
        decimal(frame["value"])
    check_privacy(frame)
    return frame

def evidence_requirements(claim_types):
    guard(isinstance(claim_types,list) and bool(claim_types)
          and len(set(claim_types))==len(claim_types)
          and set(claim_types)<=CLAIM_TYPES,"MULTILABEL_CLAIM_TYPE_REQUIRED")
    requirements={"ORIGINAL_SRT_AND_ATOMIC_COVERAGE",
                  "INDEPENDENT_REVIEW","COUNTEREXAMPLE_AND_SCOPE"}
    if set(claim_types)&{"LEGAL_OR_PRODUCT","QUALITATIVE","NUMERIC","STRATEGY_OR_PERFORMANCE"}:
        requirements.add("INDEPENDENT_PRIMARY_OR_DOMAIN_EVIDENCE")
    if set(claim_types)&{"NUMERIC","STRATEGY_OR_PERFORMANCE"}:
        requirements.add("REPRODUCED_NUMERIC_METHOD")
    if "STRATEGY_OR_PERFORMANCE" in claim_types:
        requirements.add("REPRODUCED_REAL_EMPIRICAL_STUDY")
    return sorted(requirements)

def typed_relation(left,right):
    """Typed candidate only, never a verdict about financial truth.

    Requires source-authenticated wrapper from the higher-level pipeline.
    """
    guard(all(isinstance(x,dict) and
              x.get("source_bound") is True and
              x.get("review_binding_checked") is True
              for x in (left,right)),"VERIFIED_SOURCE_AND_FRAME_REVIEW_REQUIRED")
    guard(left["claim_id"]!=right["claim_id"],"SELF_PAIR")
    fl=frame_check(left["frame"],left["claim_types"])
    fr=frame_check(right["frame"],right["claim_types"])
    status={left["legacy_verdict"],right["legacy_verdict"]}
    guard(status<=VERDICTS,"UNTRUSTED_VERDICT")
    risk=("CORRECTION_ONLY" if "CONTRADICTED" in status else
          "UNREPLICATED_HYPOTHETICAL_SOURCE" if "HYPOTHETICAL" in status else
          "HUMAN_REVIEW_ONLY")
    same_role=fl["financial_role"]==fr["financial_role"]
    essential=("subject_type","subject_id","object_type","object_id",
               "action","jurisdiction","effective_date","conditions","units")
    missing_val=("value" in fl)!=("value" in fr)
    keys_equal=all(fl[k]==fr[k] for k in essential)
    if not same_role:rel="SCOPE_DIFFERENT"
    elif missing_val:rel="UNRESOLVED_AMBIGUOUS"
    elif not keys_equal:rel="QUALIFIES_SCOPE_CANDIDATE"
    elif "value" in fl and decimal(fl["value"])!=decimal(fr["value"]):
        rel="CONTRADICTION_REVIEW"
    else:rel="SAME_PROPOSITION_CANDIDATE"
    return {
        "claim_ids":sorted((left["claim_id"],right["claim_id"])),
        "relationship_candidate":rel,"source_risk":risk,
        "automatic_merge_permitted":False,"approved_semantic_equivalence":False,
        "research_completion_certificate_permitted":False,
        "investment_instruction_permitted":False,
        "relation_is_human_review_only":True,
        "requires_independent_evidence":True,
    }

def verify_attestation(attestation,payload,role,authorities):
    """HMAC tests role-specific issuer keys supplied OUTSIDE the repository.

    Production identities need an external independent key registry; test
    fixture keys can never produce production research certification.
    """
    guard(isinstance(attestation,dict) and attestation.get("role")==role
          and isinstance(authorities,dict) and role in authorities,
          "INDEPENDENT_REVIEWER_CREDENTIAL_REQUIRED")
    a=authorities[role]
    guard(isinstance(a,dict) and a.get("reviewer_id")==attestation.get("reviewer_id")
          and isinstance(a.get("secret"),bytes) and len(a["secret"])>=32
          and a.get("test_fixture") is False,
          "PRODUCTION_REVIEWER_NOT_AUTHENTICATED")
    mac=hmac.new(a["secret"],canonical(payload),hashlib.sha256).hexdigest()
    guard(hmac.compare_digest(mac,str(attestation.get("mac",""))),
          "REVIEW_ATTESTATION_DIGEST_MISMATCH")
    return a["reviewer_id"]
