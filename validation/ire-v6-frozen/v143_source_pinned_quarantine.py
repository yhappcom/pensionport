"""V143 explicit, source-anchored ChatGPT quarantine of uncertain claims/cues.

Quarantine is not approval. Any accepted claim depending on an excluded cue
fails. A review without original audio can preserve unresolved audio exactly,
exclude those source cues and publish only unrelated *research candidates*.
This cannot certify original audio, independent recall, finance, or P0 GO.
"""
from __future__ import annotations
from ire.v6.claim_census import FINANCIAL, QUALIFIER, MULTI_CLAIM
from ire.v6.codec import json_digest, sha256, require_hash
from ire.v6.errors import InvalidInput

REASONS = frozenset({
    "AUDIO_UNVERIFIED", "AMBIGUOUS_MEANING", "FACT_CONTRADICTED",
    "FINANCE_APPLICABILITY_UNPROVEN", "CONTEXT_INSUFFICIENT",
    "NON_RESEARCH_CONTENT",
})

def _check(ok, code):
    if not ok:
        raise InvalidInput("V123_QUARANTINE_" + code)

def audit_explicit_quarantine(source, exchange, review, atoms):
    excluded_cues = {r["cue_index"] for r in review["source_cues"]
                     if r["status"] == "EXCLUDED_FROM_RESEARCH"}
    excluded_atoms = {r["claim_id"] for r in review["atom_verdicts"]
                      if r["status"] == "EXCLUDE_FROM_RESEARCH"}
    q = review.get("quarantine")
    if q is None:
        _check(not excluded_cues and not excluded_atoms, "LEDGER_REQUIRED")
        return None
    required = {"schema", "source_sha256", "manifest_sha256", "review_executor",
                "cue_rows", "atom_rows", "audio_unverified_cue_indices",
                "private_chat_quarantine_review_sha256"}
    _check(type(q) is dict and set(q) == required and
           q["schema"] == "IRE_V123_SOURCE_PINNED_QUARANTINE_V1" and
           q["source_sha256"] == source.source_sha256 and
           q["manifest_sha256"] == source.manifest_sha256 and
           q["review_executor"] == "CHATGPT_IN_CHAT" and
           type(q["cue_rows"]) is list and type(q["atom_rows"]) is list,
           "SCHEMA_OR_ORIGINAL_SOURCE")
    require_hash(q["private_chat_quarantine_review_sha256"], "V123_Q_PRIVATE_REVIEW")
    cue_map = {}
    for r in q["cue_rows"]:
        _check(type(r) is dict and set(r) == {
            "cue_index", "cue_text_sha256", "reason_code",
            "private_review_note_sha256", "source_first_context_checked"
        }, "CUE_SCHEMA")
        idx = r["cue_index"]
        _check(type(idx) is int and
               source.scope_first_cue <= idx <= source.scope_last_cue and
               idx not in cue_map and
               r["cue_text_sha256"] == sha256(source.cues[idx-1].text.encode("utf-8")) and
               r["reason_code"] in REASONS and
               r["source_first_context_checked"] is True, "CUE_UNVERIFIED")
        require_hash(r["private_review_note_sha256"], "V123_Q_CUE_NOTE")
        cue_map[idx] = r
    atom_map = {}
    for r in q["atom_rows"]:
        _check(type(r) is dict and set(r) == {
            "claim_id", "atom_sha256", "reason_code",
            "private_review_note_sha256", "context_dependencies_checked"
        }, "ATOM_SCHEMA")
        cid = r["claim_id"]
        _check(type(cid) is str and cid in atoms and cid not in atom_map and
               r["atom_sha256"] == json_digest(atoms[cid]) and
               r["reason_code"] in REASONS and
               r["context_dependencies_checked"] is True, "ATOM_UNVERIFIED")
        require_hash(r["private_review_note_sha256"], "V123_Q_ATOM_NOTE")
        atom_map[cid] = r
    _check(set(cue_map) == excluded_cues and set(atom_map) == excluded_atoms and
           bool(excluded_cues or excluded_atoms), "DISPOSITION_CENSUS")
    audio = q["audio_unverified_cue_indices"]
    _check(type(audio) is list and all(type(i) is int for i in audio) and
           audio == sorted(set(audio)) and set(audio) <= excluded_cues and
           len(audio) == review["unresolved_audio_visual"] and
           all(cue_map[idx]["reason_code"] in {
               "AUDIO_UNVERIFIED", "AMBIGUOUS_MEANING", "CONTEXT_INSUFFICIENT"}
               for idx in audio), "AUDIO_CASE_NOT_QUARANTINED")
    # Host-proposed unresolved/risky-unclaimed source cues cannot disappear
    # from the final review by changing an aggregate counter.
    mandatory = set()
    for row in exchange["cue_dispositions"]:
        idx = row["cue_index"]
        content = source.cues[idx-1].text
        risky = bool(FINANCIAL.search(content) or QUALIFIER.search(content) or
                     MULTI_CLAIM.search(content))
        if row["disposition"] == "UNRESOLVED" or (
            row["disposition"] == "NO_ATOM" and risky):
            mandatory.add(idx)
    _check(mandatory <= excluded_cues, "UNRESOLVED_HOST_CUE_NOT_EXCLUDED")
    # No excluded source cue is ever permitted in an accepted atom's
    # meaning/condition/exception/quote dependencies.
    for row in review["atom_verdicts"]:
        if row["status"] == "ACCEPT_FOR_RESEARCH":
            _check(not (excluded_cues & set(
                atoms[row["claim_id"]]["context_cue_indices"])),
                "ACCEPTED_CLAIM_DEPENDS_ON_EXCLUDED_CUE")
    for atom in exchange["atoms"]:
        if excluded_cues & set(atom["context_cue_indices"]):
            _check(atom["claim_id"] in excluded_atoms,
                   "DEPENDENT_ATOM_NOT_EXCLUDED")
    return {"atoms":len(excluded_atoms), "cues":len(excluded_cues),
            "audio_unverified":len(audio),
            "excluded_claim_ids":sorted(excluded_atoms),
            "quarantine_digest_sha256":json_digest(q)}
