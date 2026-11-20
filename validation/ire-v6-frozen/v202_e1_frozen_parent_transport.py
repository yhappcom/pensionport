"""V202 E1: source-pinned V176 chat journal -> frozen V128 parent pipeline.

This module is transport ONLY. The host provides actual native V6 child cases
and independent ChatGPT verdict callbacks. It never manufactures official bytes,
review decisions, source-only quarantines, or authorization.
"""
from __future__ import annotations

from collections import Counter

from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.codec import sha256
from v176_chat_engine_loop import EngineChatSession
from v128_host_continuous_video import run_all_video_scopes_in_chat

SCHEMA = "IRE_V202_E1_FROZEN_V176_TO_V128_TRANSPORT_V1"


def _need(ok, reason):
    if not ok:
        raise InvalidInput("V202_E1_" + reason)


def _fingerprint(atom):
    # Deliberately do NOT rely on claim IDs, which may be scoped per child.
    # Do not use fuzzy matching or an unchecked numerical claim conversion.
    refs = atom.get("source_refs")
    _need(type(refs) is list and len(refs) == 1,
          "MULTI_SOURCE_ATOM_REQUIRES_EXPLICIT_RECONCILIATION")
    ref = refs[0]
    return (atom.get("proposition"), atom.get("kind"),
            ref.get("cue_index"), ref.get("quote"))


def run_source_pinned_parent(
    engine: EngineChatSession,
    checkpoint,
    knowledge_store,
    *,
    expected_owner_head: str,
    expected_knowledge_head: str,
    review_or_load_child,
    review_seams,
    review_parent,
):
    """Execute *existing* V123/V127/V128/V126 on exactly V176-reviewed atoms.

    Refuse to treat V176 provenance as E3 approval. If the host does not provide
    fully compatible independently reviewed V6 child cases, return error
    before any private knowledge publication; V128 itself owns ACID commit.
    """
    _need(type(engine) is EngineChatSession,
          "ACTUAL_V176_ENGINE_REQUIRED")
    _need(type(expected_owner_head) is str and
          engine.progress()["checkpoint_head_sha256"] == expected_owner_head,
          "FROZEN_OWNER_HEAD_MISMATCH")
    _need(checkpoint.raw == engine.raw,
          "PARENT_SOURCE_BYTES_DIFFER_FROM_V176")
    _need(type(review_or_load_child) is not type(None) and
          all(callable(x) for x in
              (review_or_load_child, review_seams, review_parent)),
          "ACTUAL_HOST_CALLBACKS_REQUIRED")

    staged, report = engine.compile_native_v6_stage()
    _need(report["checkpoint_head_sha256"] == expected_owner_head and
          report["source_sha256"] == sha256(checkpoint.raw),
          "STAGED_REVIEW_SOURCE_DRIFT")
    _need(engine.progress()["source_first_review_complete"] and
          report["pending_original_cues"] == 0 and
          not report["unsupported_claim_cues"],
          "V176_SOURCE_REVIEW_INCOMPLETE")

    expected_atoms = Counter(_fingerprint(a) for a in staged["atoms"])
    expected_rows = {
        row["cue_index"]: row["disposition"]
        for row in staged["cue_dispositions"]}
    _need(len(expected_rows) == len(engine.source.cues),
          "V176_CUE_CENSUS_INCOMPLETE")
    consumed = Counter()
    seen_cues = set()

    def pinned_child(segment_id, manifest, stage, original_raw):
        _need(original_raw == engine.raw,
              "CHILD_SOURCE_BYTES_DRIFT")
        packet = review_or_load_child(segment_id, manifest, stage, original_raw)
        _need(type(packet) is dict and "case" in packet and
              type(packet["case"]) is dict, "CHILD_CASE_NOT_SUPPLIED")
        case = packet["case"]
        ex = case.get("exchange")
        src = case.get("source")
        _need(type(ex) is dict and src is not None and
              src.source_sha256 == engine.source.source_sha256 and
              ex.get("source_sha256") == engine.source.source_sha256 and
              ex.get("manifest_sha256") == src.manifest_sha256 and
              ex.get("video_id") == engine.source.video_id,
              "CHILD_NATIVE_SOURCE_OR_MANIFEST_DRIFT")
        _need(type(ex.get("cue_dispositions")) is list and
              type(ex.get("atoms")) is list,
              "CHILD_CUE_OR_ATOM_MISSING")
        for row in ex["cue_dispositions"]:
            idx = row["cue_index"]
            _need(idx not in seen_cues and
                  expected_rows.get(idx) == row["disposition"] and
                  row["cue_text_sha256"] ==
                  sha256(engine.source.cues[idx-1].text.encode("utf-8")),
                  "CHILD_CUE_DISPOSITION_OR_SOURCE_MISMATCH")
            seen_cues.add(idx)
        for atom in ex["atoms"]:
            key = _fingerprint(atom)
            consumed[key] += 1
            _need(consumed[key] <= expected_atoms[key],
                  "UNREVIEWED_CHILD_ATOM_INJECTED")
        return packet

    def pinned_seams(cp, cases):
        _need(len(seen_cues) == len(expected_rows) and
              consumed == expected_atoms,
              "CHILD_ATOM_CENSUS_DIFFERS_FROM_V176")
        return review_seams(cp, cases)

    result = run_all_video_scopes_in_chat(
        checkpoint, knowledge_store,
        review_or_load_child=pinned_child,
        review_seams=pinned_seams,
        review_parent=review_parent,
        expected_knowledge_head=expected_knowledge_head)
    # A HOLD path may return before the final cross-child seam callback.
    # V128 guarantees parent ACID commit cannot happen on that path.
    if result.get("all_video_knowledge_published"):
        _need(len(seen_cues) == len(expected_rows) and
              consumed == expected_atoms,
              "PUBLISHED_UNDER_INCOMPLETE_SOURCE_REVIEW")
    return {
        "schema": SCHEMA,
        "owner_source_sha256": engine.source.source_sha256,
        "owner_review_head_sha256": expected_owner_head,
        "native_parent_result": result,
        "native_parent_status": result["status"],
        "native_knowledge_published": bool(
            result.get("all_video_knowledge_published", False)),
        "e1_transport_only": True,
        "e2_semantic_correctness_certified": False,
        "e3_two_turn_final_review_certified": False,
        "e4_real_financial_approval_certified": False,
        "e5_real_13_child_knowledge_certified": False,
    }
