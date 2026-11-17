"""V166 E2: source-vs-reviewer semantic layer and factual-dependency contract.

A source-bound ChatGPT authored ledger, NOT automatic text classification,
not proof of factual accuracy, and not a V123/V128 release token.
"""
from __future__ import annotations

from ire.v6.codec import HEX64, json_digest, sha256
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
ALLOWED_ATOM_KINDS = {
    "QUESTION_ONLY":{"QUESTION"},
    "HYPOTHETICAL_RISK_QUESTION":{"QUESTION","HYPOTHETICAL"},
    "PERSONAL_OPINION":{"OPINION"},
    "META_PROPOSAL":{"OPINION"},
    "CONDITIONAL_PAYOFF_HYPOTHESIS":{"OPINION","HYPOTHETICAL"},
    "BOOK_TITLE_FACT":{"FACT"},
    "BIBLIOGRAPHIC_FACT":{"FACT"},
    "HISTORICAL_OR_ETYMOL_FACT":{"FACT"},
    "QUOTED_SOURCE_PRINCIPLE":{"OPINION","FACT"},
    "MIXED_OPINION_WITH_FACTUAL_DEPENDENCY":{"OPINION"},
    "SPECULATIVE_UNVERIFIED_FACT":{"OPINION","HYPOTHETICAL"},
    "PERSONAL_READING_IMPRESSION":{"OPINION"},
    "FINANCIAL_ASSERTION":{"FACT"},
}
NUMERIC_ROLES = {
    "ASR_NUMERIC_AMBIGUITY", "REPORTED_QUANTITY_UNVERIFIED",
    "FINANCIAL_QUANTITY_UNVERIFIED",
    "NONFINANCIAL_CONTEXT_NUMBER",
}
FACTUAL_REQUIRED_TYPES = {
    "BOOK_TITLE_FACT","BIBLIOGRAPHIC_FACT","HISTORICAL_OR_ETYMOL_FACT",
    "MIXED_OPINION_WITH_FACTUAL_DEPENDENCY","SPECULATIVE_UNVERIFIED_FACT",
    "FINANCIAL_ASSERTION","QUOTED_SOURCE_PRINCIPLE",
}
FACT_STATUS = {"OPEN_PRIMARY_REQUIRED","SOURCE_SPEECH_ONLY_NOT_VERIFIED"}
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
          HEX64.fullmatch(ledger["private_review_note_sha256"]) is not None,
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
              row["source_speech_type"] in SPEECH_TYPES and
              atom["kind"] in ALLOWED_ATOM_KINDS[row["source_speech_type"]],
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
                  dep["reviewer_note_sha256"] == row["reviewer_note_sha256"],
                  "FACTUAL_DEPENDENCY_SOURCE_OR_EVIDENCE")
            facts_open += 1
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


def build_e2_source_separated_context_packet(source, exchange, ledger):
    """Expose source speech and reviewer caution in non-interchangeable fields.

    The original V6 `proposition` may mix a speaker paraphrase with a
    reviewer financial caution. It is deliberately NEVER copied into the
    `source_verbatim_quote` field. A consumer can only attribute that field
    to the actual subtitle; all other narrative is clearly reviewer metadata.
    This is a NOT-PUBLISHED review-context packet, NOT a knowledge export.
    """
    checked = audit_e2_semantic_ledger(source, exchange, ledger)
    atoms = {a["claim_id"]: a for a in exchange["atoms"]}
    entries = []
    for row in ledger["rows"]:
        atom = atoms[row["claim_id"]]
        idx = row["verbatim_cue_index"]
        quote = row["verbatim_excerpt"]
        _need(quote in source.cues[idx - 1].text, "PACKET_SOURCE_QUOTE_DRIFT")
        entries.append({
            "claim_id": row["claim_id"],
            "atom_sha256": row["atom_sha256"],
            "speech_act": row["source_speech_type"],
            "source_verbatim_quote": quote,
            "source_quote_cue_index": idx,
            "source_quote_sha256": sha256(quote.encode("utf-8")),
            "speaker_identity": "UNKNOWN_NOT_AUDIO_AUTHENTICATED",
            "source_summary_role": "CHATGPT_PARAPHRASE_NOT_ORIGINAL_SPEAKER_QUOTE",
            "source_speech_paraphrase": row["source_speech_summary"],
            "reviewer_role": "CHATGPT_CAUTION_NOT_ORIGINAL_SPEAKER_QUOTE",
            "reviewer_caution": row["reviewer_caution_note"],
            "reviewer_caution_note_sha256": row["reviewer_note_sha256"],
            "original_context_cue_indices": row["source_context_cue_indices"],
            "original_condition_cue_indices": row["original_condition_cue_indices"],
            "original_exception_cue_indices": row["original_exception_cue_indices"],
            "unverified_fact_dependencies": [
                {"cue_index": dep["cue_index"],
                 "evidence_status": dep["status"],
                 "source_text_sha256": sha256(dep["verbatim_excerpt"].encode("utf-8"))}
                for dep in row["fact_dependencies"]],
            "source_numeric_token_roles": row["numeric_token_roles"],
            "legacy_v6_proposition_exported_as_speaker_quote": False,
            "released_financial_fact": False,
            "personal_advice_authorized": False,
        })
    return {
        "schema": "IRE_V166_E2_SOURCE_SEPARATED_REVIEW_CONTEXT_V1",
        "source_sha256": checked["source_sha256"],
        "semantic_review_ledger_sha256": checked["ledger_sha256"],
        "entry_census": len(entries),
        "entries": entries,
        "research_only_not_approved_for_investment_advice": True,
        "knowledge_publication_authorized": False,
        "final_chat_semantic_approval_authorized": False,
        "independent_gold_certified": False,
        "p0_go": False,
    }


DISCOURSE_TYPES = {
    "QUESTION_REFINEMENT", "CONTRAST", "QUESTION_COMPARISON",
    "SPECULATION_VS_SOURCE_DESCRIPTION", "QUALIFIER", "REBUTTAL",
}


def audit_e2_cross_atom_discourse(source, exchange, ledger, discourse):
    """Keep rebuttal/contrast/qualification spanning DIFFERENT atoms.

    An original V6 exception list may be empty even when a neighboring
    speaker explicitly contrasts two sentences. This supplemental ChatGPT
    ledger makes those relationships source-auditable without fabricating
    original condition/exception cue indices or a financial-fact approval.
    """
    base = audit_e2_semantic_ledger(source, exchange, ledger)
    _need(type(discourse) is dict and set(discourse) == {
        "schema","source_sha256","review_executor","rows",
        "private_chat_review_sha256","financial_fact_auto_approved",
    } and discourse["schema"] == "IRE_V166_E2_CROSS_ATOM_DISCOURSE_V1"
        and discourse["source_sha256"] == source.source_sha256
        and discourse["review_executor"] == "CHATGPT_IN_CHAT"
        and discourse["financial_fact_auto_approved"] is False
        and type(discourse["private_chat_review_sha256"]) is str
        and HEX64.fullmatch(discourse["private_chat_review_sha256"])
        and type(discourse["rows"]) is list, "DISCOURSE_SCHEMA")
    atoms = {a["claim_id"]:a for a in exchange["atoms"]}
    required = {"left_claim_id","right_claim_id","relation_type",
                "source_cue_index","source_quote","source_cue_sha256",
                "chat_meaning_note","chat_meaning_note_sha256",
                "source_checked","financial_fact_verified"}
    seen = set()
    for item in discourse["rows"]:
        _need(type(item) is dict and set(item) == required, "DISCOURSE_ROW_SCHEMA")
        left,right = item["left_claim_id"],item["right_claim_id"]
        idx = item["source_cue_index"]
        key = (left,right,item["relation_type"],idx)
        _need(left in atoms and right in atoms and left != right
              and key not in seen and item["relation_type"] in DISCOURSE_TYPES,
              "DISCOURSE_ATOM_IDS_OR_TYPE")
        seen.add(key)
        union = set(atoms[left]["context_cue_indices"]) | set(
            atoms[right]["context_cue_indices"])
        _need(type(idx) is int and idx in union
              and type(item["source_quote"]) is str
              and len(item["source_quote"]) >= 5
              and item["source_quote"] in source.cues[idx-1].text
              and item["source_cue_sha256"] ==
                  sha256(source.cues[idx-1].text.encode("utf-8")),
              "DISCOURSE_ORIGINAL_CUE_NOT_BOUND")
        note = item["chat_meaning_note"]
        _need(type(note) is str and len(note) >= 30
              and sha256(note.encode("utf-8")) ==
                  item["chat_meaning_note_sha256"]
              and item["source_checked"] is True
              and item["financial_fact_verified"] is False,
              "DISCOURSE_UNVERIFIED_MEANING")
    return {
        "schema":"IRE_V166_E2_DISCOURSE_AUDIT_RECEIPT_V1",
        "source_sha256":source.source_sha256,
        "semantic_ledger_sha256":base["ledger_sha256"],
        "discourse_ledger_sha256":json_digest(discourse),
        "cross_atom_relations_verified":len(seen),
        "source_conditions_preserved":base["conditioned_atoms_accounted"],
        "source_exceptions_preserved":base["exception_atoms_accounted"],
        "new_exception_or_financial_fact_invented":False,
        "independent_semantic_gold_certified":False,
        "research_knowledge_release_authorized":False,
        "p0_go":False,
    }


def source_separated_evidence_for_question(store, question, *,
                                            source, exchange, ledger,
                                            discourse=None,
                                            selected_knowledge_ids=None):
    """Read the REAL V126 active knowledge, then remove mixed propositions.

    V126's historically stored atom.proposition may include a reviewer
    caution alongside a speaker paraphrase. Never hand that string to an
    answer generator as a verbatim speaker claim. Reconstruct a distinct,
    source-checked quotation and a separate ChatGPT caution. This is a
    research-context *read*, never final financial advice or knowledge write.
    Mixed-video results without their matching E2 source/atom ledger FAIL
    closed rather than being silently reported as validated.
    """
    context = build_e2_source_separated_context_packet(source, exchange, ledger)
    inspected = None
    if discourse is not None:
        inspected = audit_e2_cross_atom_discourse(source, exchange, ledger, discourse)
    v126 = store.evidence_for_question(
        question, selected_knowledge_ids=selected_knowledge_ids)
    _need(type(v126) is dict and v126.get("schema") ==
          "IRE_V126_PRIVATE_CHAT_ADVISORY_EVIDENCE_PACKET_V1"
          and v126.get("status") == "HOST_CHAT_EVIDENCE_REVIEW_REQUIRED"
          and v126.get("no_auto_personal_advice") is True
          and v126.get("chatgpt_final_answer_review_required") is True
          and type(v126.get("claims")) is list,
          "V126_NOT_A_TRUSTED_EVIDENCE_PACKET")
    by_id = {r["claim_id"]:r for r in context["entries"]}
    result = []
    for entry in v126["claims"]:
        _need(type(entry) is dict and
              entry.get("source_sha256") == source.source_sha256
              and entry.get("claim_id") in by_id
              and entry.get("research_candidate_only") is True
              and entry.get("personal_advice_approved") is False
              and type(entry.get("atom")) is dict
              and entry["claim_id"] == entry["atom"].get("claim_id"),
              "V126_CLAIM_NOT_BOUND_TO_CURRENT_E2_SOURCE")
        row = by_id[entry["claim_id"]]
        _need(json_digest(entry["atom"]) == row["atom_sha256"],
              "V126_ATOM_AND_E2_MEANING_MISMATCH")
        # No `atom.proposition` or raw `atom` object appears in the output.
        # Only E2's original-text quote and separately labeled reviewer
        # paraphrase/caution are available to the later ChatGPT answer gate.
        result.append({
            "knowledge_id":entry["knowledge_id"],
            "claim_id":entry["claim_id"],
            "source_sha256":entry["source_sha256"],
            "host_event_sha256":entry["host_event_sha256"],
            "chat_review_sha256":entry["chat_review_sha256"],
            "source_verbatim_quote":row["source_verbatim_quote"],
            "source_quote_cue_index":row["source_quote_cue_index"],
            "source_quote_sha256":row["source_quote_sha256"],
            "source_summary_role":row["source_summary_role"],
            "speaker_paraphrase":row["source_speech_paraphrase"],
            "reviewer_role":row["reviewer_role"],
            "reviewer_caution":row["reviewer_caution"],
            "original_condition_cue_indices":row["original_condition_cue_indices"],
            "original_exception_cue_indices":row["original_exception_cue_indices"],
            "unverified_fact_dependencies":row["unverified_fact_dependencies"],
            "source_numeric_token_roles":row["source_numeric_token_roles"],
            "source_speech_type":row["speech_act"],
            "legacy_mixed_proposition_exposed_to_answer_generator":False,
            "current_primary_law_recheck_required":
                entry["finance_current_law_review_required"],
        })
    _need(v126["count"] == len(result), "V126_RETRIEVAL_CENSUS_DRIFT")
    return {
        "schema":"IRE_V166_E2_SOURCE_SEPARATED_V126_EVIDENCE_V1",
        "question_sha256":v126["question_sha256"],
        "source_sha256":source.source_sha256,
        "knowledge_head_sha256":v126["knowledge_head_sha256"],
        "semantic_ledger_sha256":context["semantic_review_ledger_sha256"],
        "discourse_ledger_sha256":(
            inspected["discourse_ledger_sha256"] if inspected else None),
        "count":len(result),
        "claims":result,
        "reviewed_financial_facts_authorized":False,
        "requires_live_official_source_recheck":True,
        "chatgpt_final_answer_review_required":True,
        "personalized_advice_auto_approved":False,
        "p0_go":False,
    }
