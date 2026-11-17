"""V166 E4 owner B0001 C00011: first-party Pabrai Partnership RULES only.

Issuer's own about page attests that its FUND STRUCTURE/RULES were modeled
after the 1950s Buffett Partnerships. It CANNOT prove replication of
security-selection strategy, investment returns, success causality, or the
video speaker's garbled proper name. This is contextual custody only;
native V123 verdicts and E4 whole-child HOLD never change here.
"""
from __future__ import annotations

import html
import re
import ssl
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.source import VerifiedSource

PABRAI_ABOUT_URL = "https://pabraifunds.com/about/"
SCHEMA = "IRE_V166_E4_PABRAI_OFFICIAL_PARTNERSHIP_STRUCTURE_CONTEXT_V1"
WHITESPACE=re.compile(r"\s+")
TAGS=re.compile(r"(?is)<(?:script|style)\b[^>]*>.*?</(?:script|style)\s*>|<[^>]*>")


def _fail(code):
    raise InvalidInput("V166_E4_PABRAI_OWNER_"+code)


def _validate_url(url):
    if type(url) is not str or url != PABRAI_ABOUT_URL:
        _fail("OFFICIAL_SOURCE_URL_NOT_PINNED")
    p=urlsplit(url)
    if (p.scheme!="https" or p.hostname!="pabraifunds.com"
        or p.username or p.password or p.port not in (None,443)
        or p.path!="/about/" or p.query or p.fragment):
        _fail("FIRST_PARTY_ORIGIN_INVALID")
    return p.hostname


def fetch_pabrai_fund_original_bytes(url=PABRAI_ABOUT_URL):
    _validate_url(url)
    request=Request(url,headers={
        "User-Agent":"V166-E4-owner-partnership-source/1.0",
        "Accept":"text/html","Accept-Encoding":"identity"})
    try:
        with urlopen(request,timeout=18,context=ssl.create_default_context()) as response:
            if response.status!=200 or response.geturl()!=url:
                raise QualityNotProven("V166_E4_PABRAI_OWNER_REDIRECT_OR_STATUS")
            body=response.read(2*1024*1024+1)
    except (OSError,TimeoutError) as exc:
        raise QualityNotProven("V166_E4_PABRAI_OWNER_FIRST_PARTY_HTTPS_UNAVAILABLE") from exc
    if type(body) is not bytes or not 400<=len(body)<=2*1024*1024:
        raise QualityNotProven("V166_E4_PABRAI_OWNER_FIRST_PARTY_BYTES_INVALID")
    return body


def audit_pabrai_fund_first_party_words(primary_body):
    """First-party evidence only for Pabrai FUND RULES copied from Buffett.

    Company self-report is not an independently audited return/causality fact.
    """
    if type(primary_body) is not bytes or not 400<=len(primary_body)<=2*1024*1024:
        _fail("ORIGINAL_FIRST_PARTY_BODY_REQUIRED")
    body=html.unescape(primary_body.decode("utf-8",errors="replace"))
    text=WHITESPACE.sub(" ",TAGS.sub(" ",body)).lower()
    # Dynamic website tokens can change the COMPLETE raw HTTPS body
    # without changing the issuer's specific fund-rules sentence.
    # Preserve BOTH hashes; stable excerpt hash never substitutes for the
    # original bytes in frozen V123 or owner-bound E4 certificate.
    scope=re.search(
        r"the pabrai investment funds\\s*\\(pif\\)\\s*were inspired by the original\\s+"
        r"1950s buffett partnerships\\s+and are a close replica of the original\\s+"
        r"buffett partnership rules",text)
    if not scope:
        raise QualityNotProven("V166_E4_PABRAI_OWNER_ORIGINAL_STRUCTURE_WORDING_ABSENT")
    return {
        "schema":"IRE_V166_E4_PABRAI_FUND_ISSUER_RULES_ONLY_V1",
        "normalised_issuer_claim_sha256":sha256(scope.group(0).encode("utf-8")),
        "normalised_issuer_claim_not_raw_body_substitute":True,
        "raw_body_sha256_may_change_between_https_fetches":True,
        "first_party_url":PABRAI_ABOUT_URL,
        "raw_body_sha256":sha256(primary_body),
        "fund_management_rules_based_on_buffett_claimed_by_issuer":True,
        "actual_investment_performance_independently_audited":False,
        "causal_success_proven":False,
        "personalized_investment_advice_approved":False,
    }


def audit_first_party_buffett_partnership_structure(
    source,atom,v123_verdict,primary_body,*,original_cue_indices=None
):
    if (not isinstance(source,VerifiedSource) or type(atom) is not dict
        or type(v123_verdict) is not dict or type(primary_body) is not bytes
        or not 400<=len(primary_body)<=2*1024*1024):
        _fail("ORIGINAL_VIDEO_ATOM_OR_PRIMARY_BYTES")
    if (atom.get("claim_id")!="C00011"
        or v123_verdict.get("claim_id")!="C00011"
        or atom.get("kind")!="FACT" or atom.get("stance")!="UNRESOLVED"
        or v123_verdict.get("atom_sha256")!=json_digest(atom)
        or v123_verdict.get("status")!="ACCEPT_FOR_RESEARCH"):
        _fail("C00011_OR_FROZEN_V123_VERDICT_CHANGED")
    refs=atom.get("source_refs")
    if type(refs) is not list or len(refs)<3:
        _fail("VIDEO_SOURCE_REFS_INCOMPLETE")
    indices=[r["cue_index"] for r in refs]
    if original_cue_indices is not None and indices!=original_cue_indices:
        _fail("ORIGINAL_VIDEO_CUE_CENSUS_CHANGED")
    if not all(
        type(r) is dict and
        type(r.get("cue_index")) is int and
        1<=r["cue_index"]<=len(source.cues) and
        type(r.get("quote")) is str and
        r["quote"] in source.cues[r["cue_index"]-1].text
        for r in refs
    ):
        _fail("ORIGINAL_VIDEO_QUOTES_NOT_BYTE_PINNED")
    joined=" ".join(r["quote"] for r in refs)
    if not ("버핏 파트너십" in joined and
            "비즈니스 모델" in joined and
            "벤치마킹" in joined and
            "성공" in joined):
        _fail("C00011_WHOLE_SOURCE_MEANING_NOT_PINNED")
    issuer=audit_pabrai_fund_first_party_words(primary_body)
    return {
        "schema":SCHEMA,
        "claim_id":"C00011",
        "source_sha256":source.source_sha256,
        "atom_sha256":json_digest(atom),
        "source_quote_cue_indices":indices,
        "source_quote_digest_sha256":json_digest(refs),
        "frozen_v123_status_before":v123_verdict["status"],
        "frozen_v123_status_after":v123_verdict["status"],
        "first_party_source_url":PABRAI_ABOUT_URL,
        "first_party_original_body_sha256":issuer["raw_body_sha256"],
        "fund_operator_self_description_original":True,
        "fund_rules_modeled_on_1950s_buffett_partnerships":True,
        "investment_stock_selection_same_as_buffett_verified":False,
        "investment_success_causality_independently_verified":False,
        "investment_returns_or_risk_verified":False,
        "narrator_author_name_audio_authenticated":False,
        "whole_video_chat_final_pass":False,
        "research_knowledge_release_authorized":False,
        "personal_advice_approved":False,
        "p0_go":False,
    }
