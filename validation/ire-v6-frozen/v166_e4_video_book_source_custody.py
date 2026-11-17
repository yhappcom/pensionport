"""E4 first-party book bibliography facts in VIDEO, not financial law.

C00002 (video book title/author, V123 OPEN) and C00006 (English book
title, previously V123 ACCEPT research) are different claims. Publisher
metadata can support book title/author, never the broader original quote,
investment return or an unverified speaker's exact pronunciation.
"""
from __future__ import annotations

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.source import VerifiedSource
from v166_e4_bibliographic_primary import (
    WILEY_ORIGINAL,audit_original_publisher_book_metadata)

SCHEMA="IRE_V166_E4_OWNER_PUBLISHER_BIBLIOGRAPHIC_SOURCE_CUSTODY_V1"

def _fail(code):
    raise InvalidInput("V166_E4_BOOK_OWNER_"+code)


def assess_book_citation_against_primary(source, atom, v123_verdict, body, *,
                                         source_quote_cue_index, source_quote,
                                         chat_scope_note, chat_note_sha256,
                                         original_audio_authenticated=False):
    if not isinstance(source,VerifiedSource) or type(atom) is not dict or type(v123_verdict) is not dict:
        _fail("SOURCE_OR_ATOM_REQUIRED")
    cid=atom.get("claim_id")
    if (cid!=v123_verdict.get("claim_id") or
        atom.get("kind")!="FACT" or
        v123_verdict.get("atom_sha256")!=json_digest(atom) or
        cid not in ("C00002","C00006")):
        _fail("BOOK_ATOM_OR_V123_HASH_MISMATCH")
    if (type(source_quote_cue_index) is not int or
        source_quote_cue_index not in atom["context_cue_indices"] or
        type(source_quote) is not str or
        source_quote not in source.cues[source_quote_cue_index-1].text or
        not any(w in source_quote for w in
                ("투자를 어떻게","단도","Dhandho"))):
        _fail("BOOK_SOURCE_QUOTE_NOT_PINNED")
    if (type(chat_scope_note) is not str or len(chat_scope_note)<80 or
        type(chat_note_sha256) is not str or
        sha256(chat_scope_note.encode("utf-8"))!=chat_note_sha256 or
        original_audio_authenticated is not False):
        _fail("CHAT_BOOK_SEMANTIC_OR_AUDIO_UNVERIFIED")
    publisher=audit_original_publisher_book_metadata(
        body,original_owner_source_sha256=source.source_sha256)
    old=v123_verdict["status"]
    if old not in ("OPEN","ACCEPT_FOR_RESEARCH"):
        _fail("BOOK_CANNOT_CHANGE_REJECTED_OR_QUARANTINED")
    if old=="ACCEPT_FOR_RESEARCH" and (
        v123_verdict.get("official_body_sha256")!=sha256(body) or
        v123_verdict.get("finance_evidence_status")!=
            "PRIMARY_BODY_AND_DATE_CHAT_CHECKED"):
        _fail("EXISTING_ACCEPT_MUST_HAVE_SAME_PUBLISHER_RAW_BYTES")
    return {
        "schema":SCHEMA,
        "claim_id":cid,
        "source_sha256":source.source_sha256,
        "atom_sha256":json_digest(atom),
        "v123_original_status":old,
        "v123_status_after_check":old,
        "source_verbatim_quote_sha256":sha256(source_quote.encode("utf-8")),
        "source_cue_index":source_quote_cue_index,
        "chat_scope_note_sha256":chat_note_sha256,
        "publisher_original_body_sha256":publisher["official_original_body_sha256"],
        "publisher_original_url":WILEY_ORIGINAL,
        "supported_book_title":"The Dhandho Investor",
        "supported_original_author":"Mohnish Pabrai",
        "bibliographic_primary_support":True,
        "classification":("PUBLISHER_BOOK_FACT_CUSTODY_ONLY_NO_NEW_RELEASE"
                          if old=="ACCEPT_FOR_RESEARCH"
                          else "PARTIAL_PRIMARY_SUPPORT_NATIVE_V123_OPEN"),
        "source_speaker_audio_authenticated":False,
        "transcribed_korean_name_exactness_verified":False,
        "legal_financial_rule_approval":False,
        "risk_reward_claim_verified":False,
        "full_child_chat_final_pass":False,
        "financial_fact_autoapproved":False,
        "investment_advice_approved":False,
        "research_knowledge_release_authorized":False,
        "p0_go":False,
    }
