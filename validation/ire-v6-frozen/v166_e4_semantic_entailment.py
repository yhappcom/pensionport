"""V166 E4 source-to-primary semantic entailment, stricter than keyword match.

Only a ChatGPT-in-chat, source-pinned claim-by-claim meaning judgment can
authorize a spoken paraphrase. The proof binds original SRT bytes, V6 atom,
V123 final review, HTTPS original body, numeric units and conditional/exception
material. The verifier cannot independently understand meaning; disagreement,
an unquoted primary source, a changed number, or any unaudited condition
MUST HOLD. This is research-candidate eligibility, NOT legal advice/gold.
"""
from __future__ import annotations

import re

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput

SCHEMA="IRE_V166_E4_CHAT_PRIMARY_ENTAILMENT_SOURCE_PINNED_V1"
KEYS={
    "schema","review_executor","claim_id","atom_sha256",
    "source_sha256","host_event_sha256","chat_review_sha256",
    "official_body_sha256","source_quote_sha256",
    "source_context_cue_indices","source_context_digest_sha256",
    "primary_scope_excerpt_sha256","original_condition_cue_indices",
    "original_exception_cue_indices","official_condition_passages",
    "official_exception_passages","numeric_claim_mappings",
    "claim_stance","official_scope_stance",
    "applicability_as_of","official_effective_from",
    "reviewer_reasoning","reviewer_reasoning_sha256",
    "meaning_disagreements_adjudicated","reviewed_counterexamples",
    "reviewed_primary_conditions_and_exceptions",
    "reviewed_source_and_official_time_scope",
    "no_unresolved_material_mismatch","entailment_conclusion",
    "reviewer_not_speaker_quote","independent_gold_certified",
    "legal_truth_certified","personal_advice_approved",
}
NUMERIC={"cue_index","source_token","official_token","unit","period"}
STANCES={"AFFIRMED","CORRECTED","CONDITIONAL","HYPOTHETICAL","QUESTION"}
HEX=re.compile(r"^[0-9a-f]{64}$")
PERCENT=re.compile(r"^[0-9][\d,]*(?:\.\d+)?%$")
AMOUNT=re.compile(r"^[0-9][\d,]*(?:\.\d+)?$")


def _need(ok,code):
    if not ok:
        raise InvalidInput("V166_E4_ENTAILMENT_"+code)


def _context_sha(source,indices):
    return json_digest([
        {"cue_index":i,"cue_text_sha256":
            sha256(source.cues[i-1].text.encode("utf-8"))}
        for i in indices])


def _number_core(value):
    # A percent must remain a percent; a bare number must remain bare.
    # Different numbers, periods or units MUST NEVER be coerced into match.
    return value.replace(",","")


def audit_e4_claim_entailment(case, original_row, fetched_body):
    _need(type(case) is dict and type(original_row) is dict and
          type(fetched_body) is bytes,"INPUT_NOT_SOURCE_BOUND")
    proof=original_row.get("chat_entailment_proof")
    _need(type(proof) is dict and set(proof)==KEYS and
          proof["schema"]==SCHEMA and
          proof["review_executor"]=="CHATGPT_IN_CHAT",
          "NO_CHAT_FINAL_SEMANTIC_PROOF")
    cid=original_row.get("claim_id")
    atoms={a["claim_id"]:a for a in case["exchange"]["atoms"]}
    _need(cid in atoms and proof["claim_id"]==cid,"CLAIM_ID")
    a=atoms[cid]
    review=case["chat_review"]
    _need(proof["atom_sha256"]==json_digest(a) and
          proof["source_sha256"]==case["source"].source_sha256 and
          proof["host_event_sha256"]==case["host_receipt"]["event_sha256"] and
          proof["chat_review_sha256"]==json_digest(review) and
          proof["official_body_sha256"]==sha256(fetched_body),
          "CLAIM_SOURCE_REVIEW_ORIGINAL_HASH_MISMATCH")
    _need(proof["source_quote_sha256"]==
          sha256(original_row["original_claim_quote"].encode("utf-8")) and
          proof["primary_scope_excerpt_sha256"]==
          sha256(original_row["primary_scope_excerpt"].encode("utf-8")),
          "CLAIM_OR_PRIMARY_QUOTE_CHANGED")
    contexts=a["context_cue_indices"]
    _need(proof["source_context_cue_indices"]==contexts and
          proof["source_context_digest_sha256"]==
          _context_sha(case["source"],contexts) and
          proof["original_condition_cue_indices"]==a["condition_cue_indices"] and
          proof["original_exception_cue_indices"]==a["exception_cue_indices"],
          "SOURCE_CONDITION_EXCEPTION_LOST")
    # Every official condition/exception in the reviewed proof must be an
    # actual quote of issuer bytes, never a generated ChatGPT paraphrase.
    for key,source_indices in (
        ("official_condition_passages",a["condition_cue_indices"]),
        ("official_exception_passages",a["exception_cue_indices"])):
        passages=proof[key]
        _need(type(passages) is list and
              (not source_indices or len(passages)>0) and
              len(passages)==len(set(passages)) and
              all(type(v) is str and len(v)>=5 and
                  v.encode("utf-8") in fetched_body for v in passages),
              "UNPROVEN_OFFICIAL_CONDITION_OR_EXCEPTION")
    _need(proof["claim_stance"]==a["stance"] and
          proof["official_scope_stance"] in STANCES,
          "CLAIM_STANCE_CHANGE_OR_UNKNOWN_OFFICIAL_SCOPE")
    # A corrected, conditional, hypothetical or question statement cannot
    # magically become an unconditional legal promise.
    if a["stance"]!="AFFIRMED":
        _need(proof["official_scope_stance"]==a["stance"],
              "QUALIFIED_OR_QUESTION_REBRANDED_AS_FACT")
    _need(proof["applicability_as_of"]==review["as_of"] and
          proof["official_effective_from"]==original_row["effective_from"],
          "TIME_APPLICATION_CHANGED")
    numbers=a["numeric_references"]
    mappings=proof["numeric_claim_mappings"]
    _need(type(mappings) is list and
          len(mappings)==len(numbers),"NUMERIC_CENSUS")
    neednum={(x["cue_index"],x["token"]) for x in numbers}
    gotnum=set()
    for m in mappings:
        _need(type(m) is dict and set(m)==NUMERIC and
              type(m["cue_index"]) is int and
              (m["cue_index"],m["source_token"]) in neednum and
              (m["cue_index"],m["source_token"]) not in gotnum,
              "NUMERIC_CUE_TOKEN_NOT_IN_ORIGINAL")
        gotnum.add((m["cue_index"],m["source_token"]))
        st=m["source_token"]
        ot=m["official_token"]
        _need(type(st) is str and type(ot) is str and
              st in case["source"].cues[m["cue_index"]-1].text and
              ot.encode("utf-8") in fetched_body and
              (PERCENT.fullmatch(st) and PERCENT.fullmatch(ot) or
               AMOUNT.fullmatch(st) and AMOUNT.fullmatch(ot)) and
              _number_core(st)==_number_core(ot) and
              m["unit"]==("PERCENT" if st.endswith("%")
                         else "RAW_NUMBER_UNIT_NOT_AUTHENTICATED") and
              type(m["period"]) is str,
              "NUMERIC_RATE_AMOUNT_UNIT_OR_PERIOD_NOT_EQUIVALENT")
        original_cue_text=case["source"].cues[m["cue_index"]-1].text
        explicit_years=set(re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)",
                                      original_cue_text))
        if explicit_years:
            _need(m["period"] in {"SOURCE_YEAR:"+y for y in explicit_years}
                  and m["period"].split(":",1)[1].encode("utf-8") in fetched_body,
                  "NUMERIC_PERIOD_NOT_SOURCE_AND_PRIMARY_PINNED")
        else:
            _need(m["period"]=="PERIOD_NOT_EXPRESSED_IN_SOURCE",
                  "NUMERIC_PERIOD_FABRICATED_FROM_OFFICIAL_DATE")
    _need(gotnum==neednum,"NUMERIC_REFERENCE_OMITTED")
    note=proof["reviewer_reasoning"]
    _need(type(note) is str and len(note)>=120 and
          proof["reviewer_reasoning_sha256"]==sha256(note.encode("utf-8")) and
          proof["meaning_disagreements_adjudicated"] is True and
          proof["reviewed_counterexamples"] is True and
          proof["reviewed_primary_conditions_and_exceptions"] is True and
          proof["reviewed_source_and_official_time_scope"] is True and
          proof["no_unresolved_material_mismatch"] is True and
          proof["entailment_conclusion"]=="SUPPORTED_ONLY_WITH_EXACT_QUALIFIERS" and
          proof["reviewer_not_speaker_quote"] is True and
          proof["independent_gold_certified"] is False and
          proof["legal_truth_certified"] is False and
          proof["personal_advice_approved"] is False,
          "CHAT_ENTAILMENT_MISSING_OR_FALSE_APPROVAL")
    return {
        "schema":"IRE_V166_E4_ENTAILMENT_CUSTODY_RECEIPT_V1",
        "source_sha256":proof["source_sha256"],
        "claim_id":cid,
        "atom_sha256":proof["atom_sha256"],
        "chat_review_sha256":proof["chat_review_sha256"],
        "primary_body_sha256":proof["official_body_sha256"],
        "entailment_proof_sha256":json_digest(proof),
        "numeric_claim_mappings_verified":len(mappings),
        "source_condition_cues_preserved":len(a["condition_cue_indices"]),
        "source_exception_cues_preserved":len(a["exception_cue_indices"]),
        "semantic_review_kind":"CHATGPT_IN_CHAT_NOT_BLIND_GOLD",
        "research_only_candidate_eligible":True,
        "legal_financial_fact_certified":False,
        "personal_advice_approved":False,
        "p0_go":False,
    }
