"""Shared V166 E1 contract adapter: attested speech-only -> V123 source-pinned quarantine.

This performs no semantic classification or evidence approval. It *only* encodes
an explicit, source/atom/cue/quote-bound ChatGPT attestation into the existing
V123 quarantine ledger. Frozen V123/V126/V127/V128 must independently replay.
"""
from __future__ import annotations

import copy

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import VerifiedSource

ROW_SCHEMA = "IRE_V164_SOURCE_SPEECH_ACT_V1"
OUTPUT_SCHEMA = "IRE_V166_TYPED_SOURCE_ONLY_NATIVE_QUARANTINE_DRAFT_V1"
Q_SCHEMA = "IRE_V123_SOURCE_PINNED_QUARANTINE_V1"
TYPES = {
    "RISK_QUESTION_ONLY": {"HYPOTHETICAL", "QUESTION"},
    "BOOK_TO_INVESTMENT_META_PROPOSAL_ONLY": {"OPINION"},
    "CONDITIONAL_PAYOFF_HYPOTHESIS_ONLY": {"OPINION", "HYPOTHETICAL"},
    "PERSONAL_READING_IMPRESSION_ONLY": {"OPINION"},
    "INVESTMENT_CONVICTION_QUESTION_ONLY": {"QUESTION"},
}
REQUIRED_ROW_KEYS = {
    "schema", "claim_id", "atom_sha256", "source_sha256", "source_cue_indices",
    "source_context_sha256", "speech_type", "verbatim_anchor_cue_index",
    "verbatim_anchor", "source_speaker_identity", "chat_meaning_analysis",
    "chat_meaning_analysis_sha256", "conditions_checked", "exceptions_checked",
    "numeric_checked", "counterexample_checked", "speaker_stance_checked",
    "financial_factual_truth_certified", "strategy_effectiveness_verified",
    "individual_investment_advice_approved", "independent_gold_certified",
    "external_source_audio_authenticated", "research_knowledge_export_allowed",
    "source_only_attribution", "disclosure_restriction",
}
FALSE_FLAGS = {
    "financial_factual_truth_certified", "strategy_effectiveness_verified",
    "individual_investment_advice_approved", "independent_gold_certified",
    "external_source_audio_authenticated", "research_knowledge_export_allowed",
}
TRUE_FLAGS = {
    "conditions_checked", "exceptions_checked", "numeric_checked",
    "counterexample_checked", "speaker_stance_checked",
}


def _require(ok, code):
    if not ok:
        raise InvalidInput("V166_SHARED_SOURCE_ONLY_" + code)


def compile_attested_source_only_quarantine(source, exchange, original_review,
                                            typed_rows, *, final_chat_quarantine_note):
    """Return a *draft* native V123 review, never a release or GO.

    The calling ChatGPT reviewer remains responsible for honest speech-type
    attribution and context. An explicit source-only proof is required per row.
    """
    _require(isinstance(source, VerifiedSource), "SOURCE_OBJECT")
    _require(type(exchange) is dict and type(exchange.get("atoms")) is list
             and type(original_review) is dict, "INPUT_SHAPE")
    _require(original_review.get("source_sha256") == source.source_sha256
             and original_review.get("manifest_sha256") == source.manifest_sha256
             and original_review.get("review_executor") == "CHATGPT_IN_CHAT", "REVIEW_SOURCE")
    _require(type(final_chat_quarantine_note) is str
             and len(final_chat_quarantine_note.strip()) >= 60
             and ("원문" in final_chat_quarantine_note
                  or "source-only" in final_chat_quarantine_note.lower()),
             "EXPLICIT_FINAL_REVIEW_NOTE")
    atoms = {a["claim_id"]:a for a in exchange["atoms"]}
    verdicts = original_review.get("atom_verdicts")
    _require(type(verdicts) is list and
             len(atoms) == len(exchange["atoms"]) == len(verdicts), "ATOM_CENSUS")
    original = {v["claim_id"]:v for v in verdicts}
    _require(len(original) == len(atoms) and set(original) == set(atoms), "VERDICT_CENSUS")
    cues = original_review.get("source_cues")
    _require(type(cues) is list and len(cues) == source.scope_last_cue-source.scope_first_cue+1,
             "CUE_CENSUS")
    cue_map = {r["cue_index"]:r for r in cues}
    _require(len(cue_map) == len(cues) and
             set(cue_map) == set(range(source.scope_first_cue,source.scope_last_cue+1)),
             "CUE_ORDER_CENSUS")
    _require(type(typed_rows) is list and 0 < len(typed_rows) <= len(atoms), "ROW_CENSUS")
    seen = set()
    for row in typed_rows:
        _require(type(row) is dict and set(row) == REQUIRED_ROW_KEYS
                 and row.get("schema") == ROW_SCHEMA, "ROW_SCHEMA")
        cid = row["claim_id"]
        _require(cid in atoms and cid not in seen, "ROW_ID_OR_DUPLICATE")
        seen.add(cid)
        atom, old = atoms[cid], original[cid]
        _require(row["source_sha256"] == source.source_sha256
                 and row["atom_sha256"] == json_digest(atom)
                 and old.get("atom_sha256") == json_digest(atom), "SOURCE_OR_ATOM_SHA")
        _require(row["speech_type"] in TYPES
                 and atom["kind"] in TYPES[row["speech_type"]]
                 and atom["speaker"] == "UNKNOWN"
                 and row["source_speaker_identity"] == "UNKNOWN_NOT_AUDIO_AUTHENTICATED",
                 "SPEECH_KIND_OR_SPEAKER")
        indices = sorted(set(atom["context_cue_indices"]))
        _require(indices and row["source_cue_indices"] == indices
                 and all(i in cue_map and cue_map[i]["status"] == "REVIEWED" for i in indices),
                 "CUE_SCOPE_OR_REVIEW")
        cue_hashes = [
            {"cue_index":idx,
             "cue_text_sha256":sha256(source.cues[idx-1].text.encode("utf-8"))}
            for idx in indices]
        _require(row["source_context_sha256"] == json_digest(cue_hashes),
                 "CUE_SOURCE_SHA")
        anchor = row["verbatim_anchor_cue_index"]
        _require(anchor in indices and type(row["verbatim_anchor"]) is str
                 and 5 <= len(row["verbatim_anchor"]) <= 200
                 and row["verbatim_anchor"] in source.cues[anchor-1].text,
                 "VERBATIM_MISMATCH")
        _require(old.get("status") == "OPEN" and old.get("financial_claim") is True
                 and old.get("high_risk") is True
                 and old.get("finance_evidence_status") == "OPEN",
                 "CANNOT_CONVERT_APPROVED_OR_OBJECTIVE_FACT")
        _require(all(row[k] is True for k in TRUE_FLAGS)
                 and all(row[k] is False for k in FALSE_FLAGS), "FALSE_FACT_OR_UNREVIEWED")
        _require(row["source_only_attribution"] is True
                 and row["disclosure_restriction"] ==
                     "ORIGINAL_VIDEO_SPEECH_ONLY_NOT_FINANCIAL_TRUTH_OR_ADVICE",
                 "MISSING_SOURCE_ONLY_LIMIT")
        note = row["chat_meaning_analysis"]
        _require(type(note) is str and len(note) >= 45
                 and row["chat_meaning_analysis_sha256"] ==
                     sha256(note.encode("utf-8")), "CHAT_NOTE_BYTES")
        _require(row["speech_type"] not in
                 {"RISK_QUESTION_ONLY", "INVESTMENT_CONVICTION_QUESTION_ONLY"}
                 or ("질문" in note and "답변" in note), "QUESTION_NOT_PRESERVED")
        _require(row["speech_type"] != "CONDITIONAL_PAYOFF_HYPOTHESIS_ONLY"
                 or ("조건" in note and "보장" in note),
                 "CONDITION_NOT_DISCLOSED")
        _require(row["speech_type"] != "BOOK_TO_INVESTMENT_META_PROPOSAL_ONLY"
                 or ("제안" in note and "적합" in note),
                 "SUITABILITY_NOT_DISCLOSED")
    result = copy.deepcopy(original_review)
    q = result.get("quarantine")
    prior_ids = {v["claim_id"] for v in result["atom_verdicts"]
                 if v["status"] == "EXCLUDE_FROM_RESEARCH"}
    if q is None:
        _require(not prior_ids, "EXCLUSION_LEDGER_MISSING")
        q = {"schema":Q_SCHEMA, "source_sha256":source.source_sha256,
             "manifest_sha256":source.manifest_sha256,
             "review_executor":"CHATGPT_IN_CHAT", "cue_rows":[],
             "atom_rows":[], "audio_unverified_cue_indices":[],
             "private_chat_quarantine_review_sha256":
                 sha256(final_chat_quarantine_note.encode("utf-8"))}
        result["quarantine"] = q
    _require(type(q) is dict and q.get("schema") == Q_SCHEMA
             and q.get("source_sha256") == source.source_sha256
             and q.get("manifest_sha256") == source.manifest_sha256
             and q.get("review_executor") == "CHATGPT_IN_CHAT"
             and type(q.get("cue_rows")) is list
             and type(q.get("atom_rows")) is list
             and type(q.get("audio_unverified_cue_indices")) is list,
             "Q_LEDGER_INVALID")
    _require({r["claim_id"] for r in q["atom_rows"]} == prior_ids
             and not (seen & prior_ids), "Q_CENSUS_OR_DUPLICATE")
    by_id = {r["claim_id"]:r for r in typed_rows}
    for verdict in result["atom_verdicts"]:
        cid = verdict["claim_id"]
        if cid not in by_id:
            continue
        verdict.update(status="EXCLUDE_FROM_RESEARCH",
                       finance_evidence_status="OPEN",
                       official_body_sha256=None,
                       official_effective_as_of=None,
                       financial_scope_checked=False)
        q["atom_rows"].append({
            "claim_id":cid, "atom_sha256":json_digest(atoms[cid]),
            "reason_code":"NON_RESEARCH_CONTENT",
            "private_review_note_sha256":by_id[cid]["chat_meaning_analysis_sha256"],
            "context_dependencies_checked":True})
    q["atom_rows"].sort(key=lambda x:x["claim_id"])
    q["private_chat_quarantine_review_sha256"] = sha256(
        final_chat_quarantine_note.encode("utf-8"))
    _require(result["unresolved_high_risk_omissions"] ==
             original_review["unresolved_high_risk_omissions"]
             and result["disagreements_adjudicated"] ==
                 original_review["disagreements_adjudicated"]
             and result["source_cues"] == original_review["source_cues"],
             "RISK_DISPUTES_OR_CUES_CHANGED")
    return {"schema":OUTPUT_SCHEMA,
            "source_sha256":source.source_sha256,
            "original_chat_review_sha256":json_digest(original_review),
            "typed_rows_sha256":json_digest(typed_rows),
            "source_only_quarantined_ids":sorted(seen),
            "compiled_chat_review":result,
            "compiled_chat_review_sha256":json_digest(result),
            "native_v123_must_be_reassessed":True,
            "release_authorized_by_compiler":False,
            "financial_fact_approved":False,
            "personal_advice_approved":False, "p0_go":False}
