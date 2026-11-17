"""E4 typed non-statutory authority: source-only vs publisher vs company.

Must run AFTER frozen native V123 PASS and a full source/atom/pinned E4
type-inventory audit. Classifying a risk-screened opinion is not legal truth.
Unsupported historical book contents, author theory and private partnership
claims HOLD rather than obtaining a fake tax-law approval.
"""
from __future__ import annotations

from urllib.parse import urlsplit
from ire.v6.codec import sha256,json_digest
from ire.v6.errors import InvalidInput,QualityNotProven
from v166_e4_bibliographic_primary import (
    WILEY_ORIGINAL,_validate_publisher_url,
    audit_original_publisher_book_metadata,fetch_wiley_publisher_bytes)
from v166_e4_corporate_historical_primary import (
    URL as BERKSHIRE_ORIGINAL,
    _validate_url as validate_berkshire_url,
    fetch_official_berkshire_letters_index)
from v166_e4_typed_authority import CLASS_TO_KIND
from v166_e4_wiley_author_chapter import (
    CHAPTER_URL,fetch_wiley_original_chapter_pdf,audit_author_original_chapter)

SCHEMA="IRE_V166_E4_TYPED_NONSTATUTORY_PRIMARY_V1"
ROW_KEYS={
    "claim_id","evidence_class","authority_route","source_quote_sha256",
    "chat_meaning_note","chat_meaning_note_sha256",
    "primary_url","primary_body_sha256","verification_mode",
    "original_speaker_audio_verified","formal_financial_fact_certified",
    "personal_advice_approved",
}
WILEY_APPROVED_CHAPTER_SHA256="870be11899036a19351d1ce8644f833748e9b9618d67233d6a0c162144397024"
NOTE_MIN=90
NO_PUBLISH={
    "HISTORICAL_PARTNERSHIP_CLAIM",
    "THIRD_PARTY_LETTER_ANTHOLOGY_SCOPE",
    "UNRESOLVED_CONTEXT",
}
SOURCE_ONLY={
    "INVESTMENT_STRATEGY_OPINION",
    "PERSONAL_SUBJECTIVE_OPINION",
    "HYPOTHETICAL_OR_QUESTION",
}
BOOK_TITLE_CUES=("단도","Dhandho","댄도")
YEAR_ROLES=("1977","1965","2024")


def _need(ok,reason):
    if not ok:
        raise InvalidInput("V166_E4_TYPED_PRIMARY_"+reason)


def _hold(reason):
    raise QualityNotProven("V166_E4_TYPED_PRIMARY_"+reason)


def audit_typed_nonstatutory_research(case,inventory,manifest,*,as_of):
    """Every native accepted non-statutory atom must have a proven route.

    'No statutory primary claims' is NEVER proof that facts need no source.
    No primary source row may be recycled to support a different atom.
    """
    source=case["source"]
    atoms={x["claim_id"]:x for x in case["exchange"]["atoms"]}
    review=case["chat_review"]
    verdicts={v["claim_id"]:v for v in review["atom_verdicts"]}
    route_by_id={r["claim_id"]:r for r in inventory["rows"]}
    accepted={k for k,v in verdicts.items() if v["status"]=="ACCEPT_FOR_RESEARCH"}
    candidates={cid for cid in accepted if
                route_by_id[cid]["evidence_class"]!="STATUTORY_FINANCIAL_RULE"}
    _need(type(manifest) is dict and set(manifest)=={
        "schema","source_sha256","chat_review_sha256","type_inventory_sha256",
        "as_of","rows","formal_financial_fact_certified",
        "personal_advice_approved",
    } and manifest["schema"]==SCHEMA
          and manifest["source_sha256"]==source.source_sha256
          and manifest["chat_review_sha256"]==json_digest(review)
          and manifest["type_inventory_sha256"]==json_digest(inventory)
          and manifest["as_of"]==as_of
          and manifest["formal_financial_fact_certified"] is False
          and manifest["personal_advice_approved"] is False,
          "SOURCE_TYPE_MANIFEST_REVIEW_PIN")
    rows=manifest["rows"]
    _need(type(rows) is list and len(rows)==len(candidates) and
          all(type(r) is dict and set(r)==ROW_KEYS for r in rows),
          "ALL_ACCEPTED_NONLEGAL_CLAIMS_NEED_EVIDENCE")
    keyed={r["claim_id"]:r for r in rows}
    _need(len(keyed)==len(rows) and set(keyed)==candidates,
          "NONLEGAL_ACCEPTANCE_CENSUS_OR_DUPLICATE")
    proofs=0
    source_only=0
    book=0
    company=0
    original_chapter=0
    author_strategy=0
    for cid in sorted(candidates):
        row=keyed[cid]
        typed=route_by_id[cid]
        atom=atoms[cid]
        cat=typed["evidence_class"]
        _need(cat==row["evidence_class"] and
              row["authority_route"]==typed["authority_route"] and
              row["source_quote_sha256"]==typed["original_cue_quote_sha256"] and
              row["original_speaker_audio_verified"] is False and
              row["formal_financial_fact_certified"] is False and
              row["personal_advice_approved"] is False,
              "CLAIM_SPECIFIC_SOURCE_TYPE_OR_SCOPE")
        note=row["chat_meaning_note"]
        _need(type(note) is str and len(note)>=NOTE_MIN
              and sha256(note.encode("utf-8"))==row["chat_meaning_note_sha256"],
              "CHAT_ORIGINAL_MEANING_NOTE")
        if cat in NO_PUBLISH:
            _hold("UNSUPPORTED_PRIMARY_KIND_"+cat)
        if cat in SOURCE_ONLY:
            _need(row["verification_mode"]=="SOURCE_ONLY_SPEAKER_ATTRIBUTION" and
                  row["primary_url"] is None and
                  row["primary_body_sha256"] is None,
                  "OPINION_OR_QUESTION_MUST_NOT_BORROW_FINANCIAL_PRIMARY")
            if cat=="HYPOTHETICAL_OR_QUESTION":
                _need(atom["kind"] in ("QUESTION","HYPOTHETICAL") and
                      atom["stance"] in ("QUESTION","HYPOTHETICAL"),
                      "QUESTION_STANCE_NOT_PROVEN")
            else:
                _need(atom["kind"]=="OPINION" and
                      atom["stance"] in ("AFFIRMED","CONDITIONAL","HYPOTHETICAL"),
                      "OPINION_NOT_THE_SPEAKERS_STANCE")
                # Numeric strategies, statutory claims disguised as opinion,
                # and empirical guarantees require actual primary evidence.
                _need(not atom["numeric_references"],
                      "NUMERIC_INVESTMENT_OPINION_CANNOT_BYPASS_PRIMARY")
                # A statute, taxation condition or returns guarantee remains
                # a factual matter even when someone labels its V6 kind OPINION.
                _need(not any(term in typed["original_cue_quote"] for term in (
                    "세금","세율","공제","비과세","납입한도",
                    "연금저축","원금보장","수익률","보장됩니다")),
                      "OBJECTIVE_FINANCIAL_RULE_REBRANDED_AS_OPINION")
            source_only+=1
        elif cat=="PUBLISHER_BOOK_BIBLIOGRAPHY":
            _need(row["verification_mode"]=="PUBLISHER_ORIGINAL_ENGLISH_TITLE" and
                  row["primary_url"]==WILEY_ORIGINAL and
                  _validate_publisher_url(row["primary_url"])=="www.wiley.com" and
                  atom["kind"]=="FACT" and
                  any(q in typed["original_cue_quote"] for q in BOOK_TITLE_CUES),
                  "PUBLISHER_TITLE_AND_VIDEO_QUOTE_NOT_BOUND")
            body=fetch_wiley_publisher_bytes(row["primary_url"])
            pub=audit_original_publisher_book_metadata(
                body,original_owner_source_sha256=source.source_sha256)
            _need(pub["official_original_body_sha256"]==row["primary_body_sha256"]
                  and case["official_evidence_bodies"].get(cid)==body and
                  verdicts[cid]["official_body_sha256"]==sha256(body),
                  "BOOK_PUBLISHER_BYTES_NOT_FROZEN_V123_PINNED")
            # Only title, never a speaker's ASR pronunciation of author
            # or attributed investment outcomes.
            book+=1
        elif cat=="LINGUISTIC_ETYMLOGY":
            # This confirms the ORIGINAL BOOK AUTHOR'S use of Gujarati.
            # It does NOT independently prove the etymology through an
            # authoritative Gujarati linguistic dictionary.
            quotes=" ".join(r["quote"] for r in atom["source_refs"])
            _need(row["verification_mode"]==
                  "WILEY_BOOK_AUTHOR_GUJARATI_DESCRIPTION_NOT_DICTIONARY"
                  and row["primary_url"]==CHAPTER_URL
                  and atom["kind"]=="FACT"
                  and "단도" in quotes and "구자라트" in quotes,
                  "GUJARATI_AUTHOR_WORD_ASSERTION_NOT_SOURCE_BOUND")
            chapter=fetch_wiley_original_chapter_pdf(row["primary_url"])
            _need(sha256(chapter)==WILEY_APPROVED_CHAPTER_SHA256,
                  "WILEY_ORIGINAL_CHAPTER_SNAPSHOT_DIGEST_DRIFT")
            receipt=audit_author_original_chapter(
                chapter,owner_source_sha256=source.source_sha256)
            _need(receipt["official_original_pdf_body_sha256"]==
                  row["primary_body_sha256"] and
                  verdicts[cid]["official_body_sha256"]==sha256(chapter)
                  and case["official_evidence_bodies"].get(cid)==chapter,
                  "GUJARATI_WILEY_ORIGINAL_PDF_NOT_V123_PINNED")
            original_chapter+=1
        elif cat=="BOOK_ORIGINAL_AUTHOR_PRINCIPLE":
            # The HTML is already pinned by original V123, but author's
            # loss/return asymmetric principle is supported by a separate
            # ORIGINAL Wiley chapter PDF, including its no-guarantee caveat.
            quotes=" ".join(r["quote"] for r in atom["source_refs"])
            _need(row["verification_mode"]==
                  "WILEY_BOOK_AUTHOR_ASYMMETRIC_RISK_NOT_GUARANTEED"
                  and row["primary_url"]==WILEY_ORIGINAL
                  and atom["kind"]=="OPINION"
                  and atom["stance"]=="QUOTED"
                  and "손실" in quotes and "수익" in quotes and
                  "보장" in note and "위험" in note,
                  "WILEY_AUTHOR_PRINCIPLE_NOT_ORIGINAL_SCOPE")
            first=fetch_wiley_publisher_bytes(row["primary_url"])
            _need(sha256(first)==row["primary_body_sha256"]==
                  verdicts[cid]["official_body_sha256"] and
                  case["official_evidence_bodies"].get(cid)==first,
                  "AUTHOR_BOOK_HTML_NOT_FROZEN_V123_PINNED")
            chapter=fetch_wiley_original_chapter_pdf(CHAPTER_URL)
            _need(sha256(chapter)==WILEY_APPROVED_CHAPTER_SHA256,
                  "WILEY_ORIGINAL_CHAPTER_SNAPSHOT_DIGEST_DRIFT")
            chapter_scope=audit_author_original_chapter(
                chapter,owner_source_sha256=source.source_sha256)
            _need(chapter_scope["original_author_also_discusses_nonzero_loss_risk"]
                  and chapter_scope["real_world_loss_or_return_limits_certified"] is False,
                  "ASYMMETRIC_RISK_FACT_FALSE_GUARANTEE")
            author_strategy+=1
        elif cat=="HISTORICAL_CORPORATE_FACT":
            _need(row["verification_mode"]=="BERKSHIRE_ARCHIVE_START_YEAR_1977" and
                  row["primary_url"]==BERKSHIRE_ORIGINAL and
                  validate_berkshire_url(row["primary_url"]) in (
                    "www.berkshirehathaway.com","berkshirehathaway.com") and
                  atom["kind"]=="FACT" and
                  "1977" in typed["original_cue_quote"] and
                  ("주주서한" in typed["original_cue_quote"] or
                   "서한" in typed["original_cue_quote"]),
                  "COMPANY_HISTORICAL_FACT_TOO_BROAD_FOR_ARCHIVE")
            body=fetch_official_berkshire_letters_index(row["primary_url"])
            _need(all(y.encode("ascii") in body for y in YEAR_ROLES)
                  and row["primary_body_sha256"]==sha256(body)
                  and case["official_evidence_bodies"].get(cid)==body
                  and verdicts[cid]["official_body_sha256"]==sha256(body),
                  "COMPANY_YEAR_FACT_NOT_ACTUAL_ORIGINAL")
            company+=1
        else:
            _hold("PRIMARY_EVIDENCE_CLASS_NOT_SUPPORTED_"+cat)
        proofs+=1
    return {
        "schema":"IRE_V166_E4_NONSTATUTORY_TYPED_PROOF_V1",
        "source_sha256":source.source_sha256,
        "chat_review_sha256":json_digest(review),
        "type_inventory_sha256":json_digest(inventory),
        "type_manifest_sha256":json_digest(manifest),
        "nonstatutory_accepted_claims":len(candidates),
        "nonstatutory_primary_checked":proofs,
        "source_only_speaker_statements":source_only,
        "original_publisher_book_titles":book,
        "original_company_chronology_claims":company,
        "original_author_chapter_word_descriptions":original_chapter,
        "original_author_asymmetric_risk_descriptions":author_strategy,
        "financial_truth_certified":False,
        "personal_advice_approved":False,
        "p0_go":False,
    }
