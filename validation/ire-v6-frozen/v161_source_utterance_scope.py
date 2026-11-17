"""V161: narrow ChatGPT source-only speech record, never V123 research release.

A speech record means only that a particular attributed utterance appears in
the original SRT. It does NOT authenticate audio, book claims, market returns,
current regulation, individual investment suitability, or independent gold.
"""
from __future__ import annotations

import re
from ire.v6.codec import json_digest, sha256, require_hash
from ire.v6.atomic_exchange import NUMBER
from ire.v6.errors import InvalidInput

SCHEMA = "IRE_V123_SOURCE_ONLY_SPEECH_ACT_V161"
USE_SCOPE = "ATTRIBUTED_ORIGINAL_SPEECH_ONLY_NO_FACT_NO_ADVICE_NO_KNOWLEDGE"
ALLOWED_KINDS = frozenset({"OPINION", "QUESTION", "HYPOTHETICAL"})
FACT_OR_ADVICE = re.compile(
    r"매수|매도|추천|권유|투자하|주가|수익률|원금|보장|손실|세금|과세|연금|배당|시가총액|금리|대출|IRP|ISA|ETF|HBM|시장점유율", re.I)


def audit_source_utterance_only(source, atom, row, source_cue_rows):
    """Audit a SHA-bound ChatGPT source-only status, which stays non-exportable."""
    def need(valid, code):
        if not valid:
            raise InvalidInput("V161_SOURCE_ONLY_" + code)

    need(row.get("status") == "SOURCE_ATTESTED_ONLY", "WRONG_DISPOSITION")
    att = row.get("source_utterance_attestation")
    required = {
        "schema", "claim_id", "atom_sha256", "original_cue_indices",
        "source_context_sha256", "private_chat_note_sha256", "use_scope",
        "external_financial_fact_verified", "source_audio_authenticated",
        "independent_gold_certified", "personal_advice_approved",
    }
    need(type(att) is dict and set(att) == required and att.get("schema") == SCHEMA,
         "ATTESTATION_SCHEMA")
    need(att["claim_id"] == atom["claim_id"] and
         att["atom_sha256"] == json_digest(atom), "CLAIM_OR_ATOM_DRIFT")
    ids = sorted(set(atom["context_cue_indices"]))
    need(ids and type(att["original_cue_indices"]) is list and
         att["original_cue_indices"] == ids and
         all(source.scope_first_cue <= i <= source.scope_last_cue for i in ids),
         "ORIGINAL_SOURCE_CONTEXT_DRIFT")
    original = [{"cue_index": i,
                 "cue_text_sha256": sha256(source.cues[i-1].text.encode("utf-8"))}
                for i in ids]
    need(att["source_context_sha256"] == json_digest(original), "CONTEXT_SHA_DRIFT")
    need(row["private_review_note_sha256"] == att["private_chat_note_sha256"],
         "CHAT_NOTE_NOT_PINNED_TO_DISPOSITION")
    require_hash(att["private_chat_note_sha256"], "V161_SPEECH_ONLY_NOTE")
    need(att["use_scope"] == USE_SCOPE and
         all(att[k] is False for k in (
             "external_financial_fact_verified", "source_audio_authenticated",
             "independent_gold_certified", "personal_advice_approved")),
         "FALSE_FINANCIAL_OR_AUDIO_APPROVAL")
    need(atom["kind"] in ALLOWED_KINDS and
         row["financial_claim"] is True and
         row["high_risk"] is False and
         row["finance_evidence_status"] == "OPEN" and
         atom["numeric_references"] == [] and
         all(row[k] is True for k in (
             "speaker_stance_checked", "conditions_exceptions_checked",
             "numeric_period_checked", "counterexample_checked")),
         "RISK_OR_FACT_NOT_SOURCE_ONLY")
    combined = atom["proposition"] + " " + " ".join(source.cues[i-1].text for i in ids)
    need(not NUMBER.search(combined) and not FACT_OR_ADVICE.search(combined),
         "NUMERIC_OR_ACTIONABLE_FACT_MUST_HAVE_PRIMARY_EVIDENCE")
    cue_by_id = {cue["cue_index"]: cue["status"] for cue in source_cue_rows}
    need(all(cue_by_id.get(i) == "REVIEWED" for i in ids),
         "SOURCE_CUE_UNREVIEWED_OR_EXCLUDED")
    return {"claim_id": atom["claim_id"],
            "original_source_context_sha256": att["source_context_sha256"],
            "primary_financial_fact_verified": False,
            "research_candidate_export_allowed": False,
            "personalized_advice_approved": False}
