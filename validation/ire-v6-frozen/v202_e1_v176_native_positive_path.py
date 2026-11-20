"""V202 — E1 ONLY: connected V176 source review -> frozen V123/V127/V128/V126.

The caller (the active ChatGPT host) must supply every original authoring,
finance/evidence and final parent review artifact. This module DOES NOT invent
or certify semantic judgments. It refuses V128 candidate substitution before
native gate calls; it only proves an existing same-input path can be invoked.

E1 is structural architecture testing; this is NOT E2/E3/E4/E5 quality PASS.
"""
from __future__ import annotations

import sqlite3

from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
from ire.v6.source import VerifiedSource
from v176_chat_engine_loop import EngineChatSession
from v201_e1_native_source_bridge import bridge_v176_to_v6
from v166_e3_chat_decision_delivery import run_full_video_with_e3_decisions

SCHEMA = "IRE_V202_E1_V176_TO_FROZEN_V128_NATIVE_ROUTE_V1"


def _need(ok, code):
    if not ok:
        raise InvalidInput("V202_E1_" + code)


def run_connected_e1_route(
    owner: EngineChatSession, parent_native_store,
    checkpoint, knowledge_store, *,
    scope_id, inventory_bytes, expected_inventory_sha256,
    expected_owner_head, new_parent_scope,
    review_or_load_child, review_seams, review_parent,
    expected_knowledge_head,
):
    """Synchronous E1 transport of a *source-identical* ChatGPT review.

    - The source-only V176 decisions MUST cover the original unmodified SRT.
    - Native child cases MUST carry every and only the same proposed claims.
    - Native V123 and V128 revalidate the externally authored decisions.
    - Approval and atomic knowledge writing are performed by the frozen path,
      never by this bridge, and no approvals are manufactured.
    - Returns counts/hashes only. Private text stays in owner-held journals.
    """
    _need(type(owner) is EngineChatSession,
          "ACTUAL_SOURCE_JOURNAL_REQUIRED")
    _need(all(callable(x) for x in (review_or_load_child,
                                   review_seams, review_parent)),
          "EXPLICIT_CHAT_HOST_CALLBACKS_REQUIRED")
    progress = owner.progress()
    _need(progress["checkpoint_head_sha256"] == expected_owner_head,
          "EXTERNAL_OWNER_HEAD_CHANGED")
    _need(progress["source_first_review_complete"] is True and
          progress["cue_remaining"] == 0 and
          progress["unresolved_open_cues"] == 0,
          "OWNER_SOURCE_CENSUS_UNRESOLVED")

    exchange, staged = owner.compile_native_v6_stage()
    _need(staged["checkpoint_head_sha256"] == expected_owner_head,
          "OWNER_STAGE_NOT_FROZEN")
    _need(exchange["source_sha256"] == progress["source_sha256"],
          "OWNER_EXCHANGE_SOURCE_CHANGED")
    _need(checkpoint.raw == owner.raw and
          checkpoint.parent_manifest == owner.manifest,
          "V128_PARENT_SOURCE_OR_PLAN_SUBSTITUTED")

    # These are source-first ATOMS, not semantic approvals. E2 must separately
    # prove that native stance/speaker/qualifier projections are correct.
    candidate_map = {a["claim_id"]: a for a in exchange["atoms"]}
    _need(len(candidate_map) == len(exchange["atoms"]),
          "OWNER_ATOM_ID_COLLISION")
    by_cue = {r["cue_index"]: r for r in exchange["cue_dispositions"]}
    _need(len(by_cue) == progress["cue_total"],
          "OWNER_DISPOSITION_CENSUS_DRIFT")
    bound_ids = set()
    challenged_cues = set()

    def knowledge_counts():
        # E1 must support a non-empty knowledge database. Never confuse
        # existing approved entries with a new partial publication.
        with sqlite3.connect(knowledge_store.path) as con:
            names={r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            return {name:(con.execute(
                        "SELECT COUNT(*) FROM "+name).fetchone()[0]
                          if name in names else 0)
                    for name in ("knowledge","events","parent_publications")}

    previous_counts = knowledge_counts()

    def source_head_still_frozen():
        _need(owner.progress()["checkpoint_head_sha256"] ==
              expected_owner_head, "OWNER_HEAD_CHANGED_DURING_GATE")

    # The private V6 parent ledger is a separate real transaction store.
    # It is not the legacy V128 knowledge database. It only anchors source
    # provenance; the V128 pipeline runs frozen approvals and atomic writer.
    native_source = bridge_v176_to_v6(
        owner, parent_native_store,
        scope_id=scope_id,
        inventory_bytes=inventory_bytes,
        expected_inventory_sha256=expected_inventory_sha256,
        expected_owner_head=expected_owner_head,
        new_scope=new_parent_scope)
    _need(native_source["native_read_snapshot_replayed"] is True and
          native_source["knowledge_published"] == 0,
          "NATIVE_SOURCE_AUDIT_NOT_CLEAN")

    def source_bound_child(segment_id, child_manifest, stage, original_raw):
        source_head_still_frozen()
        _need(original_raw == owner.raw,
              "CHILD_ORIGINAL_BYTES_NOT_OWNER")
        child = review_or_load_child(
            segment_id, child_manifest, stage, original_raw)
        source_head_still_frozen()
        _need(type(child) is dict and type(child.get("case")) is dict,
              "CHILD_CASE_MISSING")
        case = child["case"]
        source = case.get("source")
        _need(isinstance(source, VerifiedSource) and
              source.source_sha256 == progress["source_sha256"] and
              case.get("manifest") == child_manifest and
              child_manifest.get("source_sha256") ==
                  progress["source_sha256"],
              "CHILD_MANIFEST_OR_SOURCE_CHANGED")
        child_ex = case.get("exchange")
        _need(type(child_ex) is dict and
              child_ex.get("source_sha256") == progress["source_sha256"] and
              child_ex.get("manifest_sha256") == json_digest(child_manifest) and
              type(child_ex.get("atoms")) is list and
              type(child_ex.get("cue_dispositions")) is list,
              "CHILD_EXCHANGE_NOT_BOUND_TO_SOURCE")
        start = child_manifest["scope"]["first_cue"]
        stop = child_manifest["scope"]["last_cue"]
        expected_cues = set(range(start, stop + 1))
        _need(not (challenged_cues & expected_cues),
              "CHILD_CUE_OVERLAP")
        native_rows = {x["cue_index"]:x for x in
                       child_ex["cue_dispositions"]}
        _need(len(native_rows) == len(expected_cues) and
              set(native_rows) == expected_cues,
              "CHILD_CUE_SCOPE_MISMATCH")
        for cue in expected_cues:
            parent_row, row = by_cue[cue], native_rows[cue]
            _need(row["cue_text_sha256"] ==
                  parent_row["cue_text_sha256"] and
                  row["numeric_tokens"] == parent_row["numeric_tokens"] and
                  row["claim_ids"] == parent_row["claim_ids"] and
                  row["disposition"] == parent_row["disposition"],
                  "CUE_DECISION_CHANGED_AT_NATIVE_GATE")
        child_ids = [a["claim_id"] for a in child_ex["atoms"]]
        _need(len(set(child_ids)) == len(child_ids) and
              not (bound_ids & set(child_ids)),
              "CHILD_DUPLICATE_ATOM")
        _need(set(child_ids) == {cid for cid,a in candidate_map.items()
                      if start <= a["source_refs"][0]["cue_index"] <= stop},
              "CHILD_ATOM_SET_SUBSTITUTED")
        for atom in child_ex["atoms"]:
            candidate = candidate_map[atom["claim_id"]]
            _need(atom["proposition"] == candidate["proposition"] and
                  atom["kind"] == candidate["kind"] and
                  atom["source_refs"] == candidate["source_refs"] and
                  atom["context_cue_indices"] ==
                      candidate["context_cue_indices"],
                  "CANDIDATE_MEANING_OR_PROVENANCE_SUBSTITUTED")
            # E1 is a transport contract: even if a later independent ChatGPT
            # reviewer could legitimately change an unresolved frame, the
            # V176 journal did NOT authorize that change. A V123 child cannot
            # invent stance, speaker, exceptions, dates, or financial numbers.
            # Future positive routes require a separately versioned,
            # owner-head-bound *explicit semantic change* handoff; matching
            # original words alone is never enough.
            frame_keys=("stance","speaker","condition_cue_indices",
                        "exception_cue_indices","numeric_references","as_of")
            _need(all(atom.get(k)==candidate.get(k) for k in frame_keys),
                  "SEMANTIC_FRAME_UNATTESTED")
            _need(atom["owner_window_id"] ==
                  source.owner(atom["source_refs"][0]["cue_index"]) and
                  candidate["owner_window_id"] ==
                  owner.source.owner(candidate["source_refs"][0]["cue_index"]),
                  "SOURCE_WINDOW_MAPPING_UNATTESTED")
            # Explicit source-first qualifier strings cannot simply disappear
            # when they are not native cue anchors. This check is intentionally
            # lexical/structural; real semantic entailment belongs to E2.
            for source_term in owner_quote_terms(owner, atom):
                anchors = atom["condition_cue_indices"] + atom["exception_cue_indices"]
                _need(any(source_term in owner.source.cues[i-1].text
                          for i in anchors),
                      "SOURCE_QUALIFIER_DROPPED")
        challenged_cues.update(expected_cues)
        bound_ids.update(child_ids)
        return child

    def checked_seams(parent, child_cases):
        source_head_still_frozen()
        review = review_seams(parent, child_cases)
        source_head_still_frozen()
        return review

    def checked_parent(parent, assembly, seams, packets):
        source_head_still_frozen()
        review = review_parent(parent, assembly, seams, packets)
        source_head_still_frozen()
        return review

    source_head_still_frozen()
    result = run_full_video_with_e3_decisions(
        checkpoint, knowledge_store,
        review_or_load_child=source_bound_child,
        review_seams=checked_seams,
        review_parent=checked_parent,
        expected_knowledge_head=expected_knowledge_head)
    published = result["all_video_knowledge_published"] is True
    if published:
        _need(challenged_cues == set(range(1, progress["cue_total"] + 1)) and
              bound_ids == set(candidate_map),
              "PARENT_DID_NOT_CONSUME_ALL_OWNER_CLAIMS")

    counts=knowledge_counts()
    deltas={name:counts[name]-previous_counts[name] for name in counts}
    if not published:
        _need(all(x==0 for x in deltas.values()),
              "HOLD_OR_REJECT_WROTE_PRIVATE_KNOWLEDGE")
    else:
        _need(deltas["knowledge"] > 0 and
              deltas["events"] == deltas["knowledge"] and
              deltas["parent_publications"] == 1 and
              result["explicit_e3_status"] ==
                  "PUBLISHED_RESEARCH_CANDIDATES_ONLY",
              "PUBLISH_RESULT_NOT_STORED_ATOMICALLY")
    return {
        "schema": SCHEMA,
        "source_sha256":progress["source_sha256"],
        "owner_head_sha256":expected_owner_head,
        "native_source_ledger_head_sha256":native_source["native_v6_head_sha256"],
        "checked_cues":len(challenged_cues),
        "checked_atoms":len(bound_ids),
        "native_v128_status":result["native_v128_status"],
        "legacy_v123_v127_v128_v126_invoked":True,
        "knowledge_sqlite_counts":counts,
        "knowledge_before_counts":previous_counts,
        "knowledge_added_counts":deltas,
        "same_input_synthetic_architecture_path":published,
        "e1_structural_route":("PASS_SYNTHETIC_ROUTE" if published else
                              "SAFE_HOLD_NO_PUBLICATION"),
        "e2_semantic_accuracy_verified":False,
        "e3_independent_gold_verified":False,
        "e4_finance_approval_verified":False,
        "e5_real_13_segment_pub_verified":False,
        "personal_advice_authorized":False,
    }


def owner_quote_terms(owner, native_atom):
    """Retrieve only source-first explicit qualifiers for the matched atom.

    Uses the actual original source-first journal rather than inferring
    conditions from the native V128 packets. The method is intentionally
    scoped to the original claim anchor cue and ordinal to avoid accidental
    mixing across different utterances.
    """
    with owner._connect() as con:
        _, reviewed = owner._audit(con)
    anchored = native_atom["source_refs"][0]["cue_index"]
    entry = reviewed[anchored][1]
    candidates = [
        c for c in entry["claims"]
        if c["proposition"] == native_atom["proposition"] and
           c["kind"] == native_atom["kind"] and
           c["quote"] == native_atom["source_refs"][0]["quote"]
    ]
    _need(len(candidates)==1, "QUALIFIER_SOURCE_CLAIM_NOT_UNIQUE")
    return candidates[0]["conditions"]+candidates[0]["exceptions"]
