"""V166 E2: source-vs-reviewer semantic layer and factual-dependency contract.

A source-bound ChatGPT authored ledger, NOT automatic text classification,
not proof of factual accuracy, and not a V123/V128 release token.
"""
from __future__ import annotations

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import VerifiedSource

SCHEMA = "IRE_V166_E2_SOURCE_REVIEW_SEPARATION_V1"
SPEECH_TYPES = {
    "QUESTION_ONLY","HYPOTHETICAL_RISK_QUESTION","PERSONAL_OPINION",
    "META_PROPOSAL","CONDITIONAL_PAYOFF_HYPOTHESIS","BOOK_TITLE_FACT",
    "BIBLIOGRAPHIC_FACT","HISTORICAL_OR_ETYMOL_FACT",
    "QUOTED_SOURCE_PRINCIPLE","MIXED_OPINION_WITH_FACTUAL_DEPENDENCY",
    "SPECULATIVE_UNVERIFIED_FACT","PERSONAL_READING_IMPRESSION",
    "FINANCIAL_ASSERTION",
}
NUMERIC_ROLES = {
    "ASR_NUMERIC_AMBIGUITY", "REPORTED_QUANTITY_UNVERIFIED",
    "FINANCIAL_QUANTITY_UNVERIFIED", "VERIFIED_QUANTITY_WITH_PRIMARY",
    "NONFINANCIAL_CONTEXT_NUMBER",
}
FACTUAL_REQUIRED_TYPES = {
    "BOOK_TITLE_FACT","BIBLIOGRAPHIC_FACT","HISTORICAL_OR_ETYMOL_FACT",
    "MIXED_OPINION_WITH_FACTUAL_DEPENDENCY","SPECULATIVE_UNVERIFIED_FACT",
    "FINANCIAL_ASSERTION",
}
FACT_STATUS = {"OPEN_PRIMARY_REQUIRED","SOURCE_SPEECH_ONLY_NOT_VERIFIED",
               "PRIMARY_VERIFIED_SEPARATELY"}
ROW_KEYS = {
    "claim_id","atom_sha256","source_speech_type","source_context_cue_indices",
    "source_context_sha256","verbatim_cue_index","verbatim_excerpt",
    "source_speaker_identity","original_condition_cue_indices",
    "original_exception_cue_indices","source_speech_summary",
    "reviewer_caution_note","reviewer_note_sha256",
    "reviewer_caution_not_original_speaker_quote",
    "fact_dependencies","numeric_token_roles",
    "chat_source_reviewed","investment_effectiveness_certified",
    "personal_advice_approved","independent_gold_certified",
}
FACT_KEYS = {"cue_index","verbatim_excerpt","status","reviewer_note_sha256"}
NUMBER_KEYS = {"cue_index","token","role"}


def _need(value, code):
    if not value:
        raise InvalidInput("V166_E2_"+code)


def audit_e2_semantic_ledger(source, exchange, ledger):
    _need(isinstance(source,VerifiedSource), "OWNER_SOURCE_REQUIRED")
    _need(type(exchange) is dict and type(exchange.get("atoms")) is list
          and type(ledger) is dict and set(ledger) == {
              "schema","source_sha256","manifest_sha256",
              "review_executor","as_of","rows","private_review_note_sha256",
              "semantic_accuracy_independent_gold_certified","personal_advice_approved"
          }, "SCHEMA")
    _need(ledger["schema"] == SCHEMA and
          ledger["source_sha256"] == source.source_sha256 and
          ledger["manifest_sha256"] == source.manifest_sha256 and
          ledger["review_executor"] == "CHATGPT_IN_CHAT" and
          ledger["semantic_accuracy_independent_gold_certified"] is False and
          ledger["personal_advice_approved"] is False and
          type(ledger["private_review_note_sha256"]) is str and
          len(ledger["private_review_note_sha256"]) == 64,
          "REVIEW_OR_SOURCE_PIN")
    atoms = {a["claim_id"]:a for a in exchange["atoms"]}
    _need(len(atoms) == len(exchange["atoms"]) and
          type(ledger["rows"]) is list and len(ledger["rows"]) == len(atoms),
          "ATOM_CENSUS")
    seen = set()
    facts_open = 0
    ambiguous_numeric = 0
    conditions = 0
    exceptions = 0
    for row in ledger["rows"]:
        _need(type(row) is dict and set(row) == ROW_KEYS,
              "ROW_SCHEMA")
        cid = row["claim_id"]
        _need(cid in atoms and cid not in seen, "CLAIM_ID")
        seen.add(cid)
        atom = atoms[cid]
        _need(row["atom_sha256"] == json_digest(atom) and
              row["source_speech_type"] in SPEECH_TYPES,
              "ATOM_SHA_OR_SPEECH_TYPE")
        _need(row["source_speaker_identity"] == "UNKNOWN_NOT_AUDIO_AUTHENTICATED"
              and atom["speaker"] == "UNKNOWN", "UNVERIFIED_SPEAKER")
        indices = sorted(set(atom["context_cue_indices"]))
        _need(row["source_context_cue_indices"] == indices and
              all(source.scope_first_cue <= idx <= source.scope_last_cue
                  for idx in indices), "CONTEXT_LOSS")
        expected_cue_hash=json_digest([
            {"cue_index":idx,
             "cue_text_sha256":sha256(source.cues[idx-1].text.encode("utf-8"))}
             for idx in indices])
        _need(row["source_context_sha256"] == expected_cue_hash, "CONTEXT_SHA")
        idx = row["verbatim_cue_index"]
        _need(idx in indices and type(row["verbatim_excerpt"]) is str
              and 5 <= len(row["verbatim_excerpt"]) <= 200
              and row["verbatim_excerpt"] in source.cues[idx-1].text,
              "ORIGINAL_QUOTE_NOT_FOUND")
        _need(row["original_condition_cue_indices"] ==
                  atom["condition_cue_indices"] and
              row["original_exception_cue_indices"] ==
                  atom["exception_cue_indices"], "CONDITION_EXCEPTION_LOSS")
        _need(all(i in indices for i in row["original_condition_cue_indices"] +
                  row["original_exception_cue_indices"]), "CONDITION_OUTSIDE_SOURCE")
        conditions += int(bool(row["original_condition_cue_indices"]))
        exceptions += int(bool(row["original_exception_cue_indices"]))
        _need(type(row["source_speech_summary"]) is str
              and len(row["source_speech_summary"]) >= 20
              and type(row["reviewer_caution_note"]) is str
              and len(row["reviewer_caution_note"]) >= 20
              and row["reviewer_note_sha256"] ==
                  sha256(row["reviewer_caution_note"].encode("utf-8"))
              and row["reviewer_caution_not_original_speaker_quote"] is True
              and row["chat_source_reviewed"] is True
              and row["investment_effectiveness_certified"] is False
              and row["personal_advice_approved"] is False
              and row["independent_gold_certified"] is False,
              "REVIEWER_VS_SPEAKER_NOT_SEPARATED")
        facts = row["fact_dependencies"]
        _need(type(facts) is list and (
             bool(facts) if row["source_speech_type"] in FACTUAL_REQUIRED_TYPES
             else not facts), "FACT_DEPENDENCY_CENSUS")
        for dep in facts:
            _need(type(dep) is dict and set(dep) == FACT_KEYS and
                  dep["cue_index"] in indices and
                  type(dep["verbatim_excerpt"]) is str and
                  len(dep["verbatim_excerpt"]) >= 5 and
                  dep["verbatim_excerpt"] in
                      source.cues[dep["cue_index"]-1].text and
                  dep["status"] in FACT_STATUS and
                  type(dep["reviewer_note_sha256"]) is str and
                  len(dep["reviewer_note_sha256"])==64,
                  "FACTUAL_DEPENDENCY_SOURCE_OR_EVIDENCE")
            facts_open += int(dep["status"] != "PRIMARY_VERIFIED_SEPARATELY")
        nr = row["numeric_token_roles"]
        _need(type(nr) is list and len(nr)==len(atom["numeric_references"]),
              "NUMERIC_TOKEN_CENSUS")
        expected_nr={(r["cue_index"],r["token"]) for r in atom["numeric_references"]}
        actual_nr=set()
        for n in nr:
            _need(type(n) is dict and set(n)==NUMBER_KEYS and
                  n["role"] in NUMERIC_ROLES and
                  (n["cue_index"],n["token"]) in expected_nr and
                  (n["cue_index"],n["token"]) not in actual_nr,
                  "NUMERIC_TOKEN_ROLE_MISMATCH")
            actual_nr.add((n["cue_index"],n["token"]))
            ambiguous_numeric += int(n["role"]=="ASR_NUMERIC_AMBIGUITY")
        _need(actual_nr==expected_nr,"NUMERIC_ROLE_UNACCOUNTED")
    _need(seen == set(atoms),"MISSING_ATOM")
    return {
        "schema":"IRE_V166_E2_SEMANTIC_LAYER_AUDIT_RECEIPT_V1",
        "source_sha256":source.source_sha256,
        "checked_atom_count":len(atoms),
        "conditioned_atoms_accounted":conditions,
        "exception_atoms_accounted":exceptions,
        "unverified_embedded_factual_dependencies":facts_open,
        "ambiguous_asr_numeric_tokens":ambiguous_numeric,
        "reviewer_not_speaker_caveat_separated":True,
        "ledger_sha256":json_digest(ledger),
        "primary_fact_accuracy_certified":False,
        "independent_recall_certified":False,
        "release_authorized":False,
        "p0_go":False,
    }
