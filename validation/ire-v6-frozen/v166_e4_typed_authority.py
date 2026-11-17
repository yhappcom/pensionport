"""V166 E4 source-type attribution BEFORE choosing evidence authority.

Source-meaning statements, legal rules, historical citations, publisher
metadata, and strategy opinions cannot all pass one tax-law gate merely
because an older ChatGPT V123 row set financial_claim=True / high_risk=True.
This source-pinned typed inventory identifies the correct issuer for every
atom, but NEVER changes the frozen V123 review status or releases knowledge.

A ChatGPT typed classification is evidence-management metadata, NOT proof
of legal truth, a human blind gold set, or financial advice.
"""
from __future__ import annotations

from collections import Counter
from ire.v6.codec import sha256, json_digest
from ire.v6.errors import InvalidInput

SCHEMA="IRE_V166_E4_CHAT_TYPED_EVIDENCE_ROUTE_V1"
CLASS_TO_KIND={
    "STATUTORY_FINANCIAL_RULE":({"FACT"},"GOVERNMENT_LEGAL_PRIMARY"),
    "PUBLISHER_BOOK_BIBLIOGRAPHY":({"FACT"},"ORIGINAL_PUBLISHER_PRIMARY"),
    "BOOK_ORIGINAL_AUTHOR_PRINCIPLE":({"FACT","OPINION"},"AUTHOR_ORIGINAL_TEXT"),
    "HISTORICAL_CORPORATE_FACT":({"FACT","OPINION"},"COMPANY_ORIGINAL_ARCHIVE"),
    "HISTORICAL_PARTNERSHIP_CLAIM":({"FACT","OPINION"},"ORIGINAL_PARTNERSHIP_RECORD"),
    "LINGUISTIC_ETYMLOGY":({"FACT"},"ORIGINAL_LINGUISTIC_PRIMARY"),
    "INVESTMENT_STRATEGY_OPINION":({"OPINION"},"SOURCE_ONLY_UNVERIFIED_STRATEGY"),
    "PERSONAL_SUBJECTIVE_OPINION":({"OPINION"},"SOURCE_ONLY_NO_OBJECTIVE_TRUTH"),
    "HYPOTHETICAL_OR_QUESTION":({"QUESTION","HYPOTHETICAL"},
                                 "SOURCE_ONLY_NOT_AN_ANSWER"),
    "UNRESOLVED_CONTEXT":({"FACT","OPINION","QUESTION","HYPOTHETICAL"},
                          "NO_APPROVABLE_PRIMARY_YET"),
}
EXACT_FIELDS={
    "claim_id","atom_sha256","original_cue_index",
    "original_cue_quote","original_cue_quote_sha256",
    "evidence_class","authority_route","source_evidence_scope_note",
    "source_evidence_scope_note_sha256",
    "v123_original_status","unchanged_v123_review_note_sha256",
    "financial_claim_flag_only_screening_not_legal_proof",
    "reviewer_not_speaker_quote","primary_verification_complete",
    "independent_gold_certified","personal_advice_approved",
}
SCHEMA_FIELDS={
    "schema","source_sha256","manifest_sha256","chat_review_sha256",
    "review_executor","rows","private_reviewer_custody_sha256",
    "any_v123_status_changed","any_fact_autoapproved",
    "formal_current_law_certified","personal_advice_approved",
}
STATUSES={"OPEN","REJECT","ACCEPT_FOR_RESEARCH","EXCLUDE_FROM_RESEARCH"}


def _fail(reason):
    raise InvalidInput("V166_E4_SOURCE_TYPE_"+reason)


def _require(ok,reason):
    if not ok:
        _fail(reason)


def audit_e4_source_type_inventory(source,exchange,chat_review,inventory):
    _require(type(inventory) is dict and set(inventory)==SCHEMA_FIELDS,
             "INVENTORY_SCHEMA")
    _require(inventory["schema"]==SCHEMA and
             inventory["review_executor"]=="CHATGPT_IN_CHAT" and
             inventory["source_sha256"]==source.source_sha256 and
             inventory["manifest_sha256"]==source.manifest_sha256 and
             inventory["chat_review_sha256"]==json_digest(chat_review) and
             inventory["any_v123_status_changed"] is False and
             inventory["any_fact_autoapproved"] is False and
             inventory["formal_current_law_certified"] is False and
             inventory["personal_advice_approved"] is False and
             type(inventory["private_reviewer_custody_sha256"]) is str and
             len(inventory["private_reviewer_custody_sha256"])==64,
             "REVIEW_PIN_OR_FALSE_APPROVAL")
    atoms={a["claim_id"]:a for a in exchange["atoms"]}
    verdicts={v["claim_id"]:v for v in chat_review["atom_verdicts"]}
    _require(len(atoms)==len(exchange["atoms"]) and
             len(verdicts)==len(chat_review["atom_verdicts"]) and
             set(atoms)==set(verdicts) and
             type(inventory["rows"]) is list and
             len(inventory["rows"])==len(atoms),
             "ATOMIC_REVIEW_CENSUS")
    seen=set()
    classes=Counter()
    attention=[]
    for item in inventory["rows"]:
        _require(type(item) is dict and set(item)==EXACT_FIELDS,
                 "TYPE_ROW_SCHEMA")
        cid=item["claim_id"]
        _require(cid in atoms and cid not in seen,
                 "UNKNOWN_OR_DUPLICATE_ATOM")
        seen.add(cid)
        atom=atoms[cid]
        verdict=verdicts[cid]
        cat=item["evidence_class"]
        _require(cat in CLASS_TO_KIND,"UNRECOGNIZED_PRIMARY_AUTHORITY")
        kinds,authority=CLASS_TO_KIND[cat]
        _require(atom["kind"] in kinds and
                 item["authority_route"]==authority,
                 "ATOMIC_KIND_OR_PRIMARY_AUTHORITY_MISMATCH")
        _require(item["atom_sha256"]==json_digest(atom) and
                 item["v123_original_status"]==verdict["status"] and
                 item["unchanged_v123_review_note_sha256"]==
                     verdict["private_review_note_sha256"] and
                 verdict["status"] in STATUSES,
                 "V123_VERDICT_OR_ATOM_CHANGED")
        idx=item["original_cue_index"]
        src_refs={x["cue_index"] for x in atom["source_refs"]}
        quote=item["original_cue_quote"]
        _require(type(idx) is int and idx in src_refs and
                 type(quote) is str and len(quote)>=5 and
                 quote in source.cues[idx-1].text and
                 item["original_cue_quote_sha256"]==
                     sha256(quote.encode("utf-8")),
                 "SOURCE_FIRST_CUE_OR_VERBATIM_QUOTE")
        note=item["source_evidence_scope_note"]
        _require(type(note) is str and len(note)>=50 and
                 item["source_evidence_scope_note_sha256"]==
                     sha256(note.encode("utf-8")) and
                 item["financial_claim_flag_only_screening_not_legal_proof"] is True
                 and item["reviewer_not_speaker_quote"] is True
                 and item["independent_gold_certified"] is False
                 and item["personal_advice_approved"] is False,
                 "SOURCE_MEANING_OR_REVIEWER_CAUTION_NOT_SEPARATED")
        # Type inventory never makes any primary assertion VERIFIED.
        # Link exact HTTPS bytes + meaning before changing a separate
        # V123 revision, not here.
        _require(item["primary_verification_complete"] is False,
                 "CLASSIFICATION_NOT_PRIMARY_VERIFICATION")
        # High risk and generic 'financial_claim' in frozen V123 are
        # screening flags. A question/opinion/book citation is not a
        # current statute solely because of those flags.
        if ((verdict["financial_claim"] or verdict["high_risk"]) and
                cat!="STATUTORY_FINANCIAL_RULE"):
            attention.append(cid)
        classes[cat]+=1
    _require(seen==set(atoms),"MISSING_REVIEWED_ATOM")
    return {
        "schema":"IRE_V166_E4_EVIDENCE_AUTHORITY_SCOPE_AUDIT_V1",
        "source_sha256":source.source_sha256,
        "atom_census":len(atoms),
        "source_type_inventory_sha256":json_digest(inventory),
        "evidence_class_counts":dict(sorted(classes.items())),
        "actual_statutory_rule_atom_count":classes["STATUTORY_FINANCIAL_RULE"],
        "nonstatutory_financial_or_highrisk_screening_count":len(attention),
        "legacy_highrisk_flag_cannot_prove_statutory_authority":True,
        "all_v123_verdicts_unchanged":True,
        "actual_primary_fact_verification_completed":False,
        "final_chat_approval_granted":False,
        "formal_current_law_certified":False,
        "research_knowledge_release_authorized":False,
        "personal_advice_approved":False,
        "p0_go":False,
    }
