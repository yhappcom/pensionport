"""V166 E4 strict primary-evidence approval for research-candidate release ONLY.

Frozen V123 checks body SHA/dates/flags, but cannot authenticate the origin of
an arbitrary supplied 'government' byte sequence. E4 re-fetches authenticated
HTTPS bytes from narrowly allowlisted official sources, verifies exact source
body SHA, effective interval, text scope and explicit ChatGPT applicability.
This is NOT a legal opinion, independent semantic gold or personal advice.
"""
from __future__ import annotations

from datetime import date
import re
import ssl
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from v166_e3_chat_decision_delivery import (
    replay_chat_decision_envelope, run_full_video_with_e3_decisions)

SCHEMA = "IRE_V166_E4_TRUSTED_PRIMARY_EVIDENCE_APPLICATION_V1"
RECEIPT = "IRE_V166_E4_VERIFIED_RESEARCH_CANDIDATE_GATE_V1"
OFFICIAL_ISSUERS = {
    "www.law.go.kr":"MOLEG",
    "law.go.kr":"MOLEG",
    "www.nts.go.kr":"NTS",
    "nts.go.kr":"NTS",
    "www.fsc.go.kr":"FSC",
    "fsc.go.kr":"FSC",
    "www.fss.or.kr":"FSS",
    "fss.or.kr":"FSS",
}
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
ROW_KEYS = {
    "claim_id","official_url","issuer_code","body_sha256",
    "effective_from","effective_until","original_claim_cue_index",
    "original_claim_quote","primary_scope_excerpt",
    "chat_primary_scope_note","chat_primary_scope_note_sha256",
    "primary_claim_support_mode",
    "chat_scope_conditions_reviewed",
    "chat_exceptions_reviewed",
    "chat_source_asof_reviewed",
    "general_education_only",
    "personal_applicability_confirmed",
    "formal_financial_truth_certified",
}


def _require(ok, reason):
    if not ok:
        raise InvalidInput("V166_E4_"+reason)


def _date(x, label):
    _require(type(x) is str, label)
    try:
        d=date.fromisoformat(x)
    except (ValueError,TypeError) as exc:
        raise InvalidInput("V166_E4_"+label) from exc
    _require(d.isoformat()==x,label)
    return d


def _canonical_official_url(url):
    _require(type(url) is str and 10<=len(url)<=1400, "OFFICIAL_URL")
    p=urlsplit(url)
    _require(p.scheme=="https" and p.hostname in OFFICIAL_ISSUERS
             and p.username is None and p.password is None
             and p.port in (None,443) and not p.fragment
             and (p.path or p.query), "UNTRUSTED_PRIMARY_HOST")
    # Never allow subdomains by substring ("fsc.go.kr.attacker.tld"),
    # plain HTTP, untrusted ports, or redirects to another origin.
    return p.hostname


def _fetch_approved_primary_https(url):
    """Only genuine HTTPS origin fetch: no user-controlled bytes are trusted.

    Tests monkeypatch this transport explicitly with *synthetic* authority
    fixtures. Such tests prove control flow, not real official provenance.
    """
    _canonical_official_url(url)
    request=Request(url,headers={
        "User-Agent":"IRE-V166-E4-primary-review/1.0",
        "Accept":"text/html,text/plain,application/xhtml+xml,application/pdf",
        "Accept-Encoding":"identity",
    })
    ctx=ssl.create_default_context()
    with urlopen(request,timeout=18,context=ctx) as response:
        target=response.geturl()
        _require(_canonical_official_url(target)==_canonical_official_url(url)
                 and urlsplit(target).netloc==urlsplit(url).netloc,
                 "UNTRUSTED_PRIMARY_REDIRECT")
        _require(response.status==200, "OFFICIAL_HTTP_NOT_200")
        body=response.read(4*1024*1024+1)
    _require(type(body) is bytes and 60<=len(body)<=4*1024*1024,
             "OFFICIAL_BODY_LENGTH")
    return body


def _holding(case, native, code, *, verified=0):
    return {
        "schema":RECEIPT,
        "status":"E4_HOLD_INELIGIBLE_APPROVAL",
        "reason_code":code,
        "source_sha256":case["source"].source_sha256,
        "native_chat_decision":native["decision"],
        "chat_review_sha256":native["chat_review_sha256"],
        "approved_research_candidate_claims":0,
        "official_primary_claims_replayed":verified,
        "research_export_authorized":False,
        "formal_financial_fact_approved":False,
        "personal_advice_approved":False,
        "independent_gold_certified":False,
        "p0_go":False,
    }


def assess_e4_primary_authority_gate(case, primary_manifest, *, now_as_of):
    """Pass precisely the eligible native V123 review and primary metadata.

    No external LLM is invoked. Accepted facts must match a freshly fetched,
    TLS-verified government source. An absent document or disputed meaning
    HOLDs the entire child, never changes an OPEN to ACCEPT.
    """
    native=replay_chat_decision_envelope(case)
    if native["decision"]!="PASS_RESEARCH_CANDIDATES_ONLY":
        return _holding(case,native,"NATIVE_CHAT_NOT_PASS")
    _date(now_as_of,"REVIEW_CUTOFF_DATE")
    if primary_manifest is None:
        return _holding(case,native,"PRIMARY_PROVENANCE_MISSING")
    _require(type(primary_manifest) is dict and set(primary_manifest)=={
        "schema","owner_source_sha256","host_event_sha256",
        "chat_review_sha256","review_as_of","rows",
        "private_chat_primary_applicability_note_sha256",
        "formal_financial_fact_approved",
        "personal_advice_approved",
        "independent_gold_certified",
    } and primary_manifest["schema"]==SCHEMA
             and primary_manifest["owner_source_sha256"]==case["source"].source_sha256
             and primary_manifest["host_event_sha256"]==case["host_receipt"]["event_sha256"]
             and primary_manifest["chat_review_sha256"]==native["chat_review_sha256"]
             and primary_manifest["review_as_of"]==case["chat_review"]["as_of"]
             and primary_manifest["formal_financial_fact_approved"] is False
             and primary_manifest["personal_advice_approved"] is False
             and primary_manifest["independent_gold_certified"] is False
             and type(primary_manifest["private_chat_primary_applicability_note_sha256"]) is str
             and SHA_RE.fullmatch(primary_manifest["private_chat_primary_applicability_note_sha256"]),
             "PRIMARY_REVIEW_MANIFEST_UNTRUSTED")
    as_of=_date(primary_manifest["review_as_of"],"PRIMARY_ASOF")
    _require(as_of<=_date(now_as_of,"CURRENT_ASOF"),
             "PRIMARY_REVIEW_IN_FUTURE")
    verdicts={v["claim_id"]:v for v in case["chat_review"]["atom_verdicts"]}
    atoms={a["claim_id"]:a for a in case["exchange"]["atoms"]}
    must_verify={
        cid for cid,v in verdicts.items()
        if v["status"]=="ACCEPT_FOR_RESEARCH"
        and (v["financial_claim"] is True or v["high_risk"] is True
             or atoms[cid]["kind"]=="FACT")
    }
    rows=primary_manifest.get("rows")
    _require(type(rows) is list and len(rows)==len(must_verify),
             "PRIMARY_FACTUAL_CENSUS")
    _require({r.get("claim_id") for r in rows if type(r) is dict}
             ==must_verify and len({r["claim_id"] for r in rows})==len(rows),
             "PRIMARY_FACTUAL_ATOM_IDS")
    accepted={a["claim_id"] for a in native["atom_decisions"]
              if a["disposition"]=="ACCEPT_RESEARCH_CANDIDATE_ONLY"}
    _require(accepted=={cid for cid,v in verdicts.items()
                          if v["status"]=="ACCEPT_FOR_RESEARCH"},
             "NATIVE_ACCEPTANCE_CHANGED")
    fetched=0
    for r in rows:
        _require(type(r) is dict and set(r)==ROW_KEYS, "PRIMARY_ROW_SCHEMA")
        cid=r["claim_id"]
        url=r["official_url"]
        origin=_canonical_official_url(url)
        _require(r["issuer_code"]==OFFICIAL_ISSUERS[origin],
                 "CLAIMED_PRIMARY_ISSUER_MISMATCH")
        v=verdicts[cid]
        _require(v["finance_evidence_status"]=="PRIMARY_BODY_AND_DATE_CHAT_CHECKED"
                 and v["financial_scope_checked"] is True
                 and type(v["official_body_sha256"]) is str
                 and SHA_RE.fullmatch(v["official_body_sha256"])
                 and r["body_sha256"]==v["official_body_sha256"],
                 "V123_ACCEPTED_PRIMARY_NOT_BYTE_VERIFIED")
        _require(_date(r["effective_from"],"EFFECTIVE_FROM")==
                 _date(v["official_effective_as_of"],"V123_EFFECTIVE_FROM"),
                 "EFFECTIVE_DATE_DIFFERS_FROM_V123")
        until=(None if r["effective_until"] is None else
               _date(r["effective_until"],"EFFECTIVE_UNTIL"))
        _require(r["effective_from"]<=primary_manifest["review_as_of"] and
                 (until is None or as_of<=until), "PRIMARY_NOT_APPLICABLE_ASOF")
        idx=r["original_claim_cue_index"]
        atom=atoms[cid]
        _require(type(idx) is int and idx in atom["context_cue_indices"]
                 and type(r["original_claim_quote"]) is str
                 and len(r["original_claim_quote"])>=5
                 and r["original_claim_quote"] in case["source"].cues[idx-1].text,
                 "CLAIM_CONTEXT_QUOTE_NOT_SOURCE_PINNED")
        note=r["chat_primary_scope_note"]
        _require(type(note) is str and len(note.strip())>=70
                 and sha256(note.encode("utf-8"))==r["chat_primary_scope_note_sha256"]
                 and r["chat_scope_conditions_reviewed"] is True
                 and r["chat_exceptions_reviewed"] is True
                 and r["chat_source_asof_reviewed"] is True
                 and r["general_education_only"] is True
                 and r["personal_applicability_confirmed"] is False
                 and r["formal_financial_truth_certified"] is False,
                 "PRIMARY_CHAT_APPLICABILITY_NOT_REVIEWED")
        # The body is re-fetched from the fixed allowlisted HTTPS origin.
        # No hash-only or caller-supplied bytes can attest a government source.
        try:
            fetched_bytes=_fetch_approved_primary_https(url)
        except (OSError,TimeoutError) as exc:
            raise QualityNotProven("V166_E4_PRIMARY_ORIGIN_FETCH_UNAVAILABLE") from exc
        if type(fetched_bytes) is not bytes or not (60<=len(fetched_bytes)<=4*1024*1024):
            raise InvalidInput("V166_E4_INVALID_FETCHED_PRIMARY_BODY")
        _require(sha256(fetched_bytes)==r["body_sha256"]
                 and case["official_evidence_bodies"].get(cid)==fetched_bytes,
                 "PRIMARY_ORIGINAL_BYTES_MISMATCH")
        # E4 conservative substantive linkage: for now an exact quotation
        # in the original official bytes is required. A real *paraphrase*
        # needs a separate ChatGPT entailment proof; a URL + arbitrary
        # excerpt cannot certify that the primary source supports this claim.
        _require(r["primary_claim_support_mode"]=="EXACT_PRIMARY_QUOTE"
                 and r["original_claim_quote"].encode("utf-8") in fetched_bytes,
                 "OFFICIAL_ORIGINAL_DOES_NOT_SUPPORT_CLAIM_QUOTE")
        excerpt=r["primary_scope_excerpt"]
        _require(type(excerpt) is str and len(excerpt.strip())>=15
                 and excerpt.encode("utf-8") in fetched_bytes,
                 "PRIMARY_SCOPE_EXCERPT_NOT_IN_ORIGINAL")
        fetched+=1
    return {
        "schema":RECEIPT,
        "status":"E4_PASS_RESEARCH_CANDIDATES_ONLY",
        "source_sha256":case["source"].source_sha256,
        "host_event_sha256":case["host_receipt"]["event_sha256"],
        "chat_review_sha256":native["chat_review_sha256"],
        "primary_manifest_sha256":json_digest(primary_manifest),
        "native_v123_status":native["native_gate_status"],
        "official_primary_claims_replayed":fetched,
        "approved_research_candidate_claims":len(accepted),
        "quarantined_source_only_atoms":native["quarantined_source_only_atoms"],
        "research_export_authorized":True,
        "formal_financial_fact_approved":False,
        "personal_advice_approved":False,
        "independent_gold_certified":False,
        "p0_go":False,
    }


class E4ApprovalBlocked(QualityNotProven):
    """E4 held or rejected a child, so V128 must not publish the parent."""


def run_e4_guarded_parent(checkpoint, knowledge_store, *, review_or_load_child,
                          review_seams, review_parent, primary_manifest_for_child,
                          expected_knowledge_head, now_as_of):
    """Run E4 before each E3→V128 child; any bad primary prevents publication.

    No permission to skip the E3 path or 'fix' rejected ChatGPT evidence.
    """
    _require(callable(primary_manifest_for_child), "PRIMARY_MANIFEST_CALLBACK")
    guarded=[]
    def checked_child(segment_id,manifest,stage,original_raw):
        packet=review_or_load_child(segment_id,manifest,stage,original_raw)
        _require(type(packet) is dict and type(packet.get("case")) is dict,
                 "CHILD_PACKET")
        verified=assess_e4_primary_authority_gate(
            packet["case"],primary_manifest_for_child(segment_id,packet["case"]),
            now_as_of=now_as_of)
        guarded.append({"segment_id":segment_id,"e4_status":verified["status"],
                        "reason_code":verified.get("reason_code"),
                        "source_sha256":verified["source_sha256"]})
        if verified["status"]!="E4_PASS_RESEARCH_CANDIDATES_ONLY":
            raise E4ApprovalBlocked("V166_E4_CHILD_PRIMARY_NOT_APPROVED")
        return packet
    try:
        downstream=run_full_video_with_e3_decisions(
            checkpoint,knowledge_store,
            review_or_load_child=checked_child,
            review_seams=review_seams,review_parent=review_parent,
            expected_knowledge_head=expected_knowledge_head)
    except E4ApprovalBlocked:
        return {"schema":"IRE_V166_E4_PARENT_APPROVAL_V1",
                "status":"E4_HOLD_UNVERIFIED_CHILD",
                "child_preflights":guarded,
                "all_video_knowledge_published":False,
                "research_export_authorized":False,
                "financial_fact_formally_approved":False,
                "personal_advice_approved":False,
                "p0_go":False}
    _require(downstream["explicit_e3_status"]=="PUBLISHED_RESEARCH_CANDIDATES_ONLY"
             and downstream["all_video_knowledge_published"] is True,
             "E3_PARENT_NOT_RESEARCH_RELEASED")
    return {"schema":"IRE_V166_E4_PARENT_APPROVAL_V1",
            "status":"E4_PARENT_RESEARCH_CANDIDATES_PUBLISHED",
            "child_preflights":guarded,
            "e3_parent_status":downstream["explicit_e3_status"],
            "all_video_knowledge_published":True,
            "research_export_authorized":True,
            "financial_fact_formally_approved":False,
            "personal_advice_approved":False,
            "p0_go":False}
