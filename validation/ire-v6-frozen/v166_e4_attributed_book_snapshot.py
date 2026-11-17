"""Source-pinned book attribution, not proof of empirical returns or truth.

The pilot registry contains only hashes of explicit in-chat judgments for
real atoms. An unregistered or changed atom/review cannot borrow an approved
chapter or statement. The old publisher snapshot is never silently replaced
by a dynamic response. Full V123, E4, and parent V128 remain mandatory.
"""
import html
import io
import json
import re
from pathlib import Path
from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.source import VerifiedSource

MODE = "WILEY_ATTRIBUTED_BOOK_TEXT_PINNED_V1"
REGISTRY_SHA = "4d668093f93f995e8f487deacb890a292a605bed0f08a5b4dfdf0cd47427fd85"
HTML_SHA = "0b444a35f1f3d6a4355188c4dcfd0d7327c00ba73e75e4c6c0cccb1379525bd2"
PDF_SHA = "870be11899036a19351d1ce8644f833748e9b9618d67233d6a0c162144397024"
HTML_URL = ("https://www.wiley.com/en-us/"
            "The%2BDhandho%2BInvestor%3A%2BThe%2BLow%2BRisk%2BValue%2BMethod"
            "%2Bto%2BHigh%2BReturns-p-9780470043899")
PDF_URL = "https://catalogimages.wiley.com/images/db/pdf/9780470043899.excerpt.pdf"
# Printed page numbers of the pinned first chapter, not assertions that the
# modeled transactions or historical counts are independently true.
PDF_PAGES = {
    "RISK_REWARD": (2, 12), "PATEL_CASE": (1, 2, 6, 12),
    "HISTORICAL_POPULATION": (1,), "PATEL_SUBGROUP": (1,),
    "HISTORICAL_MOTEL_SHARE": (1, 13), "REFUGEE_BACKGROUND": (1, 3, 4, 6),
    "DISTRESSED_MOTELS": (5, 6), "FINANCED_EXAMPLE": (6, 8),
    "FAMILY_LABOR": (7,), "SELF_OPERATED_TASKS": (7,),
    "CASH_LABOR_COST": (7,), "MODEL_OCCUPANCY": (7,),
    "MODEL_EXPANSION": (12, 13), "DISTRESSED_COST_MODEL": (6, 7, 8, 10, 12),
    "LOSS_AND_UPSIDE_MODEL": (9, 10, 11, 12),
}
HEADINGS = {
    "EXISTING": "invest in existing businesses",
    "SIMPLE": "invest in simple businesses",
    "DISTRESSED": "invest in distressed businesses in distressed industries",
    "MOATS": "invest in businesses with durable moats",
    "LOW_RISK_UNCERTAINTY": "invest in low-risk, high-uncertainty businesses",
    "COPYCATS": "invest in the copycats rather than the innovators",
}
OTHER_FRAMEWORK = ("few bets, big bets, infrequent bets", "fixate on arbitrage", "margin of safety")


def need(ok, reason):
    if not ok:
        raise InvalidInput("V166_E4_BOOK_SCOPE_" + reason)


def load_registry():
    body = Path(__file__).with_name("V166_E4_BOOK_ATTRIBUTED_SCOPE_PINS.json").read_bytes()
    need(sha256(body) == REGISTRY_SHA, "REGISTRY_PIN")
    reg = json.loads(body)
    need(reg.get("schema") == "IRE_V166_BOOK_ATTRIBUTION_PILOT_PIN_V1"
         and len(reg.get("rows", {})) == 23, "PILOT_CENSUS")
    return reg


def body_scope(body, key, *, archive):
    need(type(body) is bytes and 150 < len(body) <= 3 * 1024 * 1024, "PRIMARY_BYTES")
    if key in PDF_PAGES:
        need(sha256(body) == PDF_SHA and body.startswith(b"%PDF-"), "CHAPTER_SNAPSHOT_PIN")
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(body))
        evidence = []
        for n in PDF_PAGES[key]:
            text = reader.pages[n-1].extract_text() or ""
            need(len(text) > 100, "PDF_PAGE_EXTRACTION")
            evidence.append({"printed_page": n, "text_sha256": sha256(text.encode())})
        return {"format": "chapter", "source_url": PDF_URL, "page_text_hashes": evidence}
    need(key in HEADINGS or key in {"NINE_FRAMEWORK_TOPICS", "STOCK_MARKET_APPLICATION"}, "UNKNOWN_SCOPE")
    if archive:
        need(sha256(body) == HTML_SHA, "PUBLISHER_ARCHIVED_SNAPSHOT_PIN")
    source = body.decode("utf-8", errors="strict")
    text = html.unescape(re.sub(r"(?is)<[^>]+>", " ", source)).lower()
    text = re.sub(r"\s+", " ", text)
    need("the dhandho investor" in text and "mohnish pabrai" in text
         and "9780470043899" in re.sub(r"\D", "", source), "WRONG_BOOK")
    anchors = (HEADINGS[key],) if key in HEADINGS else (
        tuple(HEADINGS.values()) + OTHER_FRAMEWORK if key == "NINE_FRAMEWORK_TOPICS"
        else ("capital allocation framework", "stock market"))
    if not all(a in text for a in anchors):
        raise QualityNotProven("V166_E4_BOOK_SCOPE_NARROW_PUBLISHER_PASSAGE_MISSING")
    return {"format": "html", "source_url": HTML_URL, "scope_marker_digest": json_digest(list(anchors))}


def audit_book_attribution_snapshot(source, atom, verdict, note_text, body, row):
    """Check archived proof and actual reviewer decision; never grant release."""
    need(isinstance(source, VerifiedSource) and type(note_text) is str, "OWNER_SOURCE")
    note = json.loads(note_text)
    nh = sha256(note_text.encode("utf-8"))
    need(type(note) is dict and canonical(note).decode() == note_text, "CANONICAL_CHAT_NOTE")
    cid = atom["claim_id"]
    reg = load_registry()
    key = note.get("primary_scope_key")
    need(source.source_sha256 == reg["source_sha256"]
         and reg["rows"].get(cid) == [json_digest(atom), nh, key], "UNREGISTERED_OR_CHANGED_REVIEW")
    need(verdict.get("claim_id") == cid and verdict.get("status") == "ACCEPT_FOR_RESEARCH"
         and verdict.get("atom_sha256") == json_digest(atom)
         and verdict.get("private_review_note_sha256") == nh
         and atom["kind"] == "OPINION" and atom["stance"] == "QUOTED", "NATIVE_AUTHOR_QUOTE_REVIEW")
    need(note.get("schema") == "V166_E4_P0_CHATGPT_ACTUAL_REVIEW_REVISION_V1"
         and note.get("claim_id") == cid and note.get("atom_sha256") == json_digest(atom)
         and note.get("source_sha256") == source.source_sha256
         and note.get("decision") == "ACCEPT_FOR_RESEARCH"
         and note.get("scope") == "ATTRIBUTED_ORIGINAL_BOOK_TEXT_ONLY_NOT_EMPIRICAL_TRUE_OR_ADVICE"
         and all(note.get(f) is False for f in ("formal_investment_truth_certified", "personal_advice_approved", "actual_speaker_audio_verified")), "REVIEW_SCOPE")
    indices = sorted(set(atom["context_cue_indices"]))
    refs = atom["source_refs"]
    need(indices and all(source.scope_first_cue <= i <= source.scope_last_cue for i in indices)
         and note.get("original_cue_indices") == atom["context_cue_indices"]
         and note.get("source_context_sha256") == json_digest([
             {"cue_index": i, "original_cue_text_sha256": sha256(source.cues[i-1].text.encode())} for i in indices])
         and note.get("source_refs_sha256") == json_digest(refs)
         and refs and all(r["cue_index"] in indices and r["quote"] and r["quote"] in source.cues[r["cue_index"]-1].text for r in refs), "DIRECT_SOURCE_CONTEXT")
    need(row.get("verification_mode") == MODE and row.get("claim_id") == cid
         and row.get("primary_body_sha256") == note.get("primary_body_sha256") == sha256(body)
         and row.get("chat_meaning_note_sha256") == nh
         and row.get("source_quote_sha256") in {sha256(r["quote"].encode()) for r in refs}, "MANIFEST_SOURCE_OR_BODY_PIN")
    need(verdict.get("financial_claim") is note.get("financial_claim")
         and (not verdict["financial_claim"] or (verdict.get("official_body_sha256") == sha256(body)
              and verdict.get("finance_evidence_status") == "PRIMARY_BODY_AND_DATE_CHAT_CHECKED")), "V123_PRIMARY_PIN")
    scope = body_scope(body, key, archive=True)
    need(note.get("primary_kind") == scope["format"]
         and note.get("primary_url") == row.get("primary_url") == scope["source_url"], "PRIMARY_SCOPE_ORIGIN")
    return {"claim_id": cid, "scope_key": key, "review_note_sha256": nh,
            "archived_primary_sha256": sha256(body), "primary_scope": scope,
            "investment_effectiveness_certified": False, "research_release_authorized": False}


def verify_live_book_attribution(proof, live_body):
    """Caller: canonical E4 fetch from fixed issuer URL. Keep both byte hashes."""
    live_scope = body_scope(live_body, proof["scope_key"], archive=False)
    need(live_scope == proof["primary_scope"], "LIVE_SCOPE_CHANGED")
    return dict(proof, live_primary_sha256=sha256(live_body),
                historical_bytes_replaced=False, live_scope_replayed=True)
