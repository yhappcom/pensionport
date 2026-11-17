"""V166 E1: compile FIVE source-attested B0001 speech acts into native V123 quarantine.

This is an auditable adapter, NOT a new meaning reviewer or an approval shortcut.
It preserves immutable V123, preserves undecided objective facts and risk flags,
and never overwrites owner evidence. V123/V126/V128 must still decide release.
"""
from __future__ import annotations

import copy

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from v164_typed_v123 import B0001_EXPECTED, audit_typed_speech_row
from v166_shared_source_only_native_contract import compile_attested_source_only_quarantine

SCHEMA = "IRE_V166_B0001_TYPED_TO_NATIVE_QUARANTINE_DRAFT_V1"
QUARANTINE_SCHEMA = "IRE_V123_SOURCE_PINNED_QUARANTINE_V1"


def _need(ok: bool, why: str) -> None:
    if not ok:
        raise InvalidInput("V166_SOURCE_ONLY_COMPILER_" + why)


def compile_b0001_source_only_to_native_review(
    source, exchange, legacy_chat_review, typed_rows, *,
    final_chat_quarantine_note: str,
) -> dict:
    """Preserve source-only meaning without exporting questions as investment facts.

    The result is a DRAFT ChatGPT review for an actual further V123 replay.
    It cannot set disagreements, high-risk omissions or outside evidence to PASS.
    """
    _need(source.scope_first_cue == 1 and source.scope_last_cue == 120
          and len(exchange.get("atoms", [])) == 16, "PILOT_SCOPE")
    _need(type(legacy_chat_review) is dict and
          legacy_chat_review.get("source_sha256") == source.source_sha256 and
          legacy_chat_review.get("manifest_sha256") == source.manifest_sha256 and
          legacy_chat_review.get("review_executor") == "CHATGPT_IN_CHAT",
          "ORIGINAL_REVIEW_SOURCE_OR_EXECUTOR")
    _need(type(final_chat_quarantine_note) is str
          and len(final_chat_quarantine_note.strip()) >= 60
          and ("원문" in final_chat_quarantine_note or
               "source-only" in final_chat_quarantine_note.lower()),
          "NEW_CHAT_QUARANTINE_NOTE_REQUIRED")
    atoms = {a["claim_id"]: a for a in exchange["atoms"]}
    before = {r["claim_id"]: r for r in legacy_chat_review.get("atom_verdicts", [])}
    _need(len(atoms) == len(exchange["atoms"]) == len(before) == 16
          and set(atoms) == set(before), "ATOM_CENSUS")
    cues = legacy_chat_review.get("source_cues")
    _need(type(cues) is list and len(cues) == 120
          and [r["cue_index"] for r in cues] == list(range(1, 121)), "CUE_CENSUS")
    statuses = {r["cue_index"]: r["status"] for r in cues}
    _need(type(typed_rows) is list and len(typed_rows) == 5, "TYPED_ROW_CENSUS")
    validated = []
    for row in typed_rows:
        cid = row.get("claim_id") if type(row) is dict else None
        _need(cid in B0001_EXPECTED and cid not in validated, "TYPED_ROW_UNEXPECTED")
        audit_typed_speech_row(source, atoms[cid], before[cid], row, statuses)
        validated.append(cid)
    _need(set(validated) == set(B0001_EXPECTED), "TYPED_MISSING")
    for cid in ("C00002", "C00009", "C00010"):
        _need(before[cid]["status"] in {"OPEN", "ACCEPT_FOR_RESEARCH"},
              "FACTUAL_CLAIM_CANNOT_BE_AUTO_EXCLUDED")
    # The B0001-specific V164 meaning audit above is mandatory. Reuse the
    # same strict source-only -> native V123 converter that is exercised by
    # full V127/V128 synthetic parent publication in E1 tests.
    shared = compile_attested_source_only_quarantine(
        source, exchange, legacy_chat_review, typed_rows,
        final_chat_quarantine_note=final_chat_quarantine_note)
    draft = shared["compiled_chat_review"]
    _need(all(before[cid]["status"] ==
              next(r for r in draft["atom_verdicts"] if r["claim_id"] == cid)["status"]
              for cid in ("C00002", "C00009", "C00010")),
          "HISTORICAL_FACT_AUTO_RECLASSIFIED")
    return {
        "schema": SCHEMA,
        "source_sha256": source.source_sha256,
        "input_review_sha256": json_digest(legacy_chat_review),
        "typed_rows_sha256": json_digest(typed_rows),
        "source_only_quarantined_ids": sorted(validated),
        "compiled_chat_review_sha256": json_digest(draft),
        "compiled_chat_review": draft,
        "native_v123_must_be_reassessed": True,
        "financial_factual_truth_certified": False,
        "personal_advice_approved": False,
        "release_authorized_by_compiler": False,
        "p0_go": False,
    }
