"""V5 P0: context-preserving packets and a source-anchored second semantic pass.

The second pass is authored by the active ChatGPT host, never inferred by this
module. Its deterministic checks reveal omissions and contradictions but cannot
certify perfect atomic-claim recall without an independent reference inventory.
Legacy MODEL_ANALYSIS packet hashes and immutable receipts remain unchanged.
"""
from __future__ import annotations

import re
from .engine import ResearchRun, require, sha256, canonical

CUE_CHALLENGE = re.compile(r"그리고|그러나|하지만|반면|또한|따라서|그런데|한편|instead|however|whereas", re.I)
DECISIONS = {"CLAIM", "NONCLAIM", "MISSING_CLAIM", "OPEN"}


def contextual_packet(run: ResearchRun, window_id: str, *, halo_cues: int = 2) -> dict:
    """Provide nearby source solely as context; it cannot own claim citations.

    The original packet and its packet_sha256 are nested, unchanged. This
    prevents older MODEL_ANALYSIS hashes and signed event chains from drifting.
    """
    require(type(halo_cues) is int and 0 <= halo_cues <= 8,
            "P0_CONTEXT_HALO_BUDGET_INVALID")
    primary = run.packet(window_id)
    windows = run.manifest["windows"]
    pos = next(i for i, w in enumerate(windows) if w["window_id"] == window_id)
    ids = windows[pos]["primary_cue_ids"]
    before = list(range(max(1, ids[0] - halo_cues), ids[0]))
    after = list(range(ids[-1] + 1, min(len(run.cues), ids[-1] + halo_cues) + 1))
    neighbors = ({"cue_index": i, "text": run.cues[i].text} for i in before + after)
    current_boundary = bool(windows[pos].get("continuation_boundary_review_required"))
    previous_boundary = bool(pos and windows[pos-1].get("continuation_boundary_review_required"))
    payload = {
        "schema": "IRE_V5_P0_CONTEXTUAL_PACKET_V1",
        "video_id": run.manifest["video_id"],
        "window_id": window_id,
        "primary_packet": primary,
        "before": [{"cue_index": i, "text": run.cues[i].text} for i in before],
        "after": [{"cue_index": i, "text": run.cues[i].text} for i in after],
        "boundary_review_required": current_boundary or previous_boundary,
        "context_only_cue_ids": before + after,
        "context_quotation_is_not_claim_source": True,
        "original_model_packet_sha256": primary["packet_sha256"],
    }
    return {**payload, "context_sha256": sha256(canonical(payload))}


def audit_second_pass(run: ResearchRun, window_id: str, review: dict) -> dict:
    """Cross-check second-pass semantic units against the initial model record.

    Every primary cue needs an explicit semantic-unit disposition; a cue may
    have many units. MISSING_CLAIM and OPEN are *discovered review obligations*
    and must never be treated as completed research. The model may have failed
    to recognize still more units; therefore even a clean audit is not gold recall.
    """
    primary = run.packet(window_id)
    run.replay()
    require(window_id in run.model, "P0_SECOND_PASS_REQUIRES_REAL_MODEL_ANALYSIS")
    require(type(review) is dict and
            review.get("schema") == "IRE_V5_P0_SECOND_PASS_V1" and
            review.get("video_id") == run.manifest["video_id"] and
            review.get("window_id") == window_id and
            review.get("source_sha256") == run.manifest["source_sha256"] and
            review.get("packet_sha256") == primary["packet_sha256"] and
            review.get("claimed_author") == "CURRENT_CHATGPT_CONVERSATION" and
            review.get("independent_human_verified") is False and
            type(review.get("units")) is list,
            "P0_SECOND_PASS_SOURCE_OR_ORIGIN_INVALID")
    model = run.model[window_id]
    primary_ids = set(run.windows[window_id]["primary_cue_ids"])
    model_claim_ids = {c["claim_id"] for c in model["claims"]}
    model_links = {row["cue_index"]: set(row["claim_ids"])
                   for row in model["cue_dispositions"]}
    mapped = set()
    covered = set()
    gaps = []
    open_units = []
    seen_ids = set()
    linked_by_cue = set()
    for unit in review["units"]:
        require(type(unit) is dict, "P0_SECOND_PASS_UNIT_INVALID")
        uid = unit.get("unit_id")
        idx = unit.get("cue_index")
        quote = unit.get("source_quote")
        meaning = unit.get("meaning")
        decision = unit.get("decision")
        ids = unit.get("claim_ids")
        require(type(uid) is str and re.fullmatch(r"S\d{4,}", uid) is not None and
                uid not in seen_ids and type(idx) is int and idx in primary_ids and
                type(quote) is str and len(quote.strip()) >= 2 and
                quote in run.cues[idx].text and
                type(meaning) is str and len(meaning.strip()) >= 8 and
                decision in DECISIONS and
                type(ids) is list and len(ids) == len(set(ids)) and
                all(type(cid) is str for cid in ids),
                "P0_SECOND_PASS_UNIT_OR_QUOTE_INVALID")
        seen_ids.add(uid)
        covered.add(idx)
        if decision == "CLAIM":
            require(bool(ids) and set(ids) <= model_claim_ids,
                    "P0_SECOND_PASS_CLAIM_UNKNOWN")
            if not set(ids) <= model_links[idx]:
                gaps.append({"unit_id": uid, "cue_index": idx,
                             "reason": "CLAIM_NOT_ANCHORED_TO_THIS_CUE"})
            mapped.update(ids)
            linked_by_cue.add(idx)
        else:
            require(not ids, "P0_SECOND_PASS_NONCLAIM_HAS_CLAIM_ID")
            if decision in {"MISSING_CLAIM", "OPEN"}:
                open_units.append({"unit_id": uid, "cue_index": idx,
                                   "reason": decision})
    uncovered = sorted(primary_ids - covered)
    unmapped = sorted(model_claim_ids - mapped)
    linked_without_second_pass = sorted(
        idx for idx in primary_ids if model_links[idx] and idx not in linked_by_cue
    )
    compound_challenges = sorted(idx for idx in primary_ids
        if CUE_CHALLENGE.search(run.cues[idx].text) and
        len(model_links[idx]) < 2)
    if uncovered:
        gaps.append({"reason": "CUES_WITHOUT_SECOND_PASS_UNITS",
                     "cue_indices": uncovered})
    if unmapped:
        gaps.append({"reason": "INITIAL_CLAIMS_NOT_RECONFIRMED",
                     "claim_ids": unmapped})
    if linked_without_second_pass:
        gaps.append({"reason": "LINKED_CUES_NOT_RECONFIRMED",
                     "cue_indices": linked_without_second_pass})
    if open_units:
        gaps.append({"reason": "UNRESOLVED_OR_MISSING_ATOMIC_UNITS",
                     "units": open_units})
    result = {
        "schema": "IRE_V5_P0_SECOND_PASS_RESULT_V1",
        "video_id": run.manifest["video_id"],
        "window_id": window_id,
        "source_sha256": run.manifest["source_sha256"],
        "model_packet_sha256": primary["packet_sha256"],
        "review_units": len(seen_ids),
        "primary_cues": len(primary_ids),
        "covered_cues": len(covered),
        "initial_claims": len(model_claim_ids),
        "reconfirmed_initial_claims": len(mapped),
        "review_gaps": gaps,
        "compound_clause_challenge_cues": compound_challenges,
        "source_review_reconciled": not gaps,
        "independent_atomic_recall_certified": False,
        "personal_investment_advice_approved": False,
    }
    return {**result, "result_sha256": sha256(canonical(result))}
