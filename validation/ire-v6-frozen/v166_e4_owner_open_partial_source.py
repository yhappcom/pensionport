"""V166 E4 OPEN source-first partial evidence: three distinct B0001 risks.

An officially sourced *part* of a video claim NEVER certifies the speaker's
complete claim, ASR/audio, historical inference, named anthology or finance
advice. The native V123 OPEN status stays OPEN. The published E4 parent stays
HOLD. This is reusable as an immutable reviewer-preflight package, not a
new V123 verdict writer.

The Berkshire company index is first party for its own online archive and
its own book announcement; a reproduced 1957 Buffett partnership letter on a
third-party website is NOT authenticated as the physical original. Korean
bibliographies attest printed author/title, NOT what a YouTube speaker said.
"""
from __future__ import annotations

import re
from ire.v6.codec import sha256,json_digest
from ire.v6.errors import InvalidInput,QualityNotProven
from ire.v6.source import VerifiedSource

SCHEMA="IRE_V166_E4_OWNER_OPEN_PARTIAL_SOURCE_FIRST_V1"
OPEN_CLAIMS={
    "C00002":{
        "kind":"FACT","stance":"AFFIRMED",
        "supported":"ORIGINAL_ENGLISH_PUBLISHER_TITLE_AUTHOR_ONLY",
        "missing":(
            "SPEAKER_ORIGINAL_AUDIO_AUTHOR_PRONUNCIATION_NOT_VERIFIED",
            "KOREAN_TRANSLATION_RECORD_SECONDARY_NOT_ORIGINAL_PUBLISHER_ATTESTATION",
            "KOREAN_ASR_PROPER_NAME_NOT_LITERAL_PUBLISHER_SPELLING",
        ),
        "role":"ORIGINAL_PUBLISHER_AND_KOREAN_BIBLIOGRAPHIC_LISTING",
    },
    "C00009":{
        "kind":"OPINION","stance":"AFFIRMED",
        "supported":"BERKSHIRE_OFFICIAL_LETTERS_ONLINE_INDEX_AND_1965_2024_BOOK",
        "missing":(
            "PARTICULAR_BOOK_OR_ANTHOLOGY_NOT_IDENTIFIED",
            "BOOK_COVERS_ONLY_AFTER_CAPITAL_WAS_LARGE_NOT_ESTABLISHED",
            "UNIVERSAL_ALL_COLLECTIONS_CLAIM_NOT_PROVEN",
        ),
        "role":"BERKSHIRE_ISSUER_LETTER_CATALOGUE",
    },
    "C00010":{
        "kind":"OPINION","stance":"UNRESOLVED",
        "supported":"THIRD_PARTY_REPRINT_OF_1957_PARTNERSHIP_LETTER_CONTEXT_ONLY",
        "missing":(
            "ISSUER_AUTHENTICATED_1957_ORIGINAL_LETTER_ABSENT",
            "AGGRESSIVE_STRATEGY_CHARACTERIZATION_DISPUTED",
            "SPEAKER_QUESTION_RESPONSE_BOUNDARY_UNRESOLVED",
            "HIGH_RETURN_INTENT_NOT_EQUALS_REALIZED_RETURN",
        ),
        "role":"UNAUTHENTICATED_1957_SECONDARY_REPRODUCTION",
    },
}
ROLE_WORDS={
    "C00002":("The Dhandho Investor","Mohnish Pabrai"),
    "C00009":("shareholder letters","1977","1965","2024"),
    "C00010":("1957 letter","undervalued securities","work-outs"),
}
SRC_KEYWORDS={
    "C00002":("투자를 어떻게","바브라"),
    "C00009":("주주서한","커진"),
    "C00010":("파트너십","공격적"),
}
BODY_LIMIT=3*1024*1024


def _require(ok,reason):
    if not ok:
        raise InvalidInput("V166_E4_OWNER_OPEN_"+reason)


def _safe_text(body):
    _require(type(body) is bytes and 100<=len(body)<=BODY_LIMIT,
             "PRIMARY_BODY_REQUIRED")
    return re.sub(r"\s+"," ",body.decode("utf-8",errors="replace"))


def assess_open_partial_claim(source,atom,v123_verdict,*,original_body,
                              review_note,review_note_sha256,
                              evidence_source_role,body_origin_verified,
                              own_audio_authenticated=False):
    """Fail closed: source identity + original byte quotes + frozen OPEN.

    The body is already acquired externally. body_origin_verified can be
    True only if an independent TLS/archived-raw-byte provenance receipt
    exists; it is NOT inferred from URL or this function.
    """
    _require(isinstance(source,VerifiedSource)
             and type(atom) is dict and type(v123_verdict) is dict,
             "NATIVE_OWNER_SOURCE_AND_ATOM_REQUIRED")
    cid=atom.get("claim_id")
    _require(cid in OPEN_CLAIMS,"CLAIM_NOT_IN_B0001_OPEN_RESEARCH_SET")
    spec=OPEN_CLAIMS[cid]
    _require(atom.get("kind")==spec["kind"]
             and atom.get("stance")==spec["stance"]
             and v123_verdict.get("claim_id")==cid
             and v123_verdict.get("status")=="OPEN"
             and v123_verdict.get("atom_sha256")==json_digest(atom),
             "NATIVE_V123_OPEN_OR_ATOM_TYPE_CHANGED")
    refs=atom.get("source_refs")
    _require(type(refs) is list and len(refs)>=3
             and all(
                 type(r) is dict and set(r)=={"cue_index","quote"}
                 and type(r["cue_index"]) is int
                 and 1<=r["cue_index"]<=len(source.cues)
                 and r["cue_index"] in atom["context_cue_indices"]
                 and type(r["quote"]) is str and len(r["quote"])>=5
                 and r["quote"] in source.cues[r["cue_index"]-1].text
                 for r in refs)
             and len({r["cue_index"] for r in refs})==len(refs),
             "DIRECT_SOURCE_CUE_MISSING_OR_CROSS_ATOM")
    quotes=" ".join(r["quote"] for r in refs)
    _require(all(s in quotes for s in SRC_KEYWORDS[cid]),
             "OPEN_FULL_CLAIM_CONTEXT_INCOMPLETE")
    _require(evidence_source_role==spec["role"]
             and body_origin_verified is True
             and own_audio_authenticated is False,
             "ORIGIN_AUDIO_OR_SOURCE_ROLE_UNPROVEN")
    _require(type(review_note) is str and len(review_note)>=120
             and type(review_note_sha256) is str
             and sha256(review_note.encode("utf-8"))==review_note_sha256,
             "INDEPENDENT_CHAT_NOTE_NOT_PINNED")
    body_text=_safe_text(original_body).lower()
    _require(all(s.lower() in body_text for s in ROLE_WORDS[cid]),
             "ISSUER_TEXT_ONLY_PARTIAL_NOT_SUPPORTED")
    return {
        "schema":SCHEMA,"claim_id":cid,
        "owner_original_sha256":source.source_sha256,
        "atom_sha256":json_digest(atom),
        "native_v123_status_before":"OPEN",
        "native_v123_status_after":"OPEN",
        "original_direct_refs_sha256":json_digest(refs),
        "direct_source_quote_count":len(refs),
        "original_primary_body_sha256":sha256(original_body),
        "caller_declared_source_role":evidence_source_role,
        "caller_asserts_prior_origin_verification":True,
        "transport_origin_independently_verified_by_this_function":False,
        "review_note_sha256":review_note_sha256,
        "limited_supported_subclaim":spec["supported"],
        "still_unproven_components":list(spec["missing"]),
        "whole_original_claim_supported":False,
        "first_party_primary_for_all_subclaims":False,
        "speaker_audio_authenticated":False,
        "chatgpt_final_new_approval_written":False,
        "research_knowledge_release_authorized":False,
        "personal_advice_approved":False,
        "p0_go":False,
    }


def audit_partial_open_video_census(source,exchange,review,receipts):
    """A preflight report of 3 OPEN claims, never a new 'pass' decision."""
    _require(isinstance(source,VerifiedSource)
             and type(exchange) is dict and type(review) is dict
             and type(receipts) is list,"COMPLETE_EVIDENCE_SCHEMA")
    atoms={a["claim_id"]:a for a in exchange["atoms"]}
    verdicts={v["claim_id"]:v for v in review["atom_verdicts"]}
    _require(len(receipts)==len(OPEN_CLAIMS)
             and all(type(r) is dict and r.get("claim_id") in OPEN_CLAIMS
                     for r in receipts)
             and {r["claim_id"] for r in receipts}==set(OPEN_CLAIMS)
             and len({r["claim_id"] for r in receipts})==len(receipts)
             and set(OPEN_CLAIMS).issubset(atoms)
             and set(OPEN_CLAIMS).issubset(verdicts)
             and all(
                 r.get("schema")==SCHEMA and
                 r.get("native_v123_status_after")=="OPEN" and
                 r.get("whole_original_claim_supported") is False and
                 r.get("research_knowledge_release_authorized") is False and
                 r.get("owner_original_sha256")==source.source_sha256 and
                 r.get("atom_sha256")==json_digest(atoms[r["claim_id"]]) and
                 verdicts[r["claim_id"]]["status"]=="OPEN"
                 for r in receipts),
             "MISSING_OPEN_EVIDENCE_OR_V123_STATUS_ESCALATION")
    return {
        "schema":"IRE_V166_E4_OWNER_OPEN_PREPUBLICATION_HOLD_CENSUS_V1",
        "source_sha256":source.source_sha256,
        "review_sha256":json_digest(review),
        "partial_evidence_receipts_sha256":json_digest(receipts),
        "still_open_claim_ids":sorted(OPEN_CLAIMS),
        "n_open_unapproved":len(OPEN_CLAIMS),
        "original_v123_review_modified":False,
        "real_owner_parent_release_allowed":False,
        "e4_status":"FAIL_ACTUAL_OWNER_PARENT_STILL_HOLD",
        "e5_authorized":False,
        "personal_advice_approved":False,
    }
