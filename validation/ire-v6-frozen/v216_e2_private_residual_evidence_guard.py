"""V216 E2 source-only residual-risk audit; never certifies financial truth.

Inputs are owner-private original-byte-backed V6 candidate and 250-cue coverage.
No private text is returned or committed to GitHub. Detects a semantic
evidence leak where a primary atom uses a visual/audio-unverified cue even
after the parent chart claim was quarantined. Does not auto-merge or approve.
"""
from __future__ import annotations

import json

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput

SCHEMA = "IRE_V216_E2_PRIVATE_SOURCE_RESIDUAL_RISK_AUDIT_V1"


def need(ok, code):
    if not ok:
        raise InvalidInput("V216_E2_" + code)


def _pin(raw, obj, digest, label):
    need(type(raw) is bytes and type(obj) is dict and
         type(digest) is str and len(digest) == 64,
         label + "_INPUT_SCHEMA")
    try:
        recovered = json.loads(raw)
    except (ValueError, TypeError, UnicodeError) as exc:
        raise InvalidInput("V216_E2_" + label + "_JSON_UNREADABLE") from exc
    need(recovered == obj and sha256(raw) == digest,
         label + "_ORIGINAL_BYTES_OR_HASH_CHANGED")


def audit_private_unapproved_evidence_risks(
    exchange, exchange_bytes, coverage, coverage_bytes, *,
    expected_exchange_sha256, expected_coverage_sha256,
):
    """Recheck source custody and return only non-sensitive HOLD metadata.

    A flagged cue may reflect either an ASR ambiguity OR a missing visual.
    Neither can be automatically classified as audio-confirmed or visually
    confirmed. A reviewer must separate standalone text from chart claims.
    """
    _pin(exchange_bytes, exchange, expected_exchange_sha256, "NATIVE")
    _pin(coverage_bytes, coverage, expected_coverage_sha256, "COVERAGE")
    need(type(exchange.get("source_sha256")) is str and
         exchange["source_sha256"] == coverage.get("source_sha256") and
         coverage.get("new_native_v6_exchange_sha256") ==
         expected_exchange_sha256, "SOURCE_AND_NATIVE_CUSTODY")
    atoms = exchange.get("atoms")
    dispositions = exchange.get("cue_dispositions")
    cues = coverage.get("cues")
    need(type(atoms) is list and type(dispositions) is list and
         type(cues) is list and 1 <= len(cues) <= 1000 and
         len(dispositions) == len(cues) and 1 <= len(atoms) <= 512 and
         coverage.get("full_original_cue_count") == len(cues),
         "BOUNDED_CUE_AND_NATIVE_CENSUS")
    need(coverage.get("original_audio_and_screen_not_available") is True and
         coverage.get("independent_gold_certified") is False and
         coverage.get("e2_final_pass") is False,
         "UNJUSTIFIED_EXTERNAL_GOLD_OR_AUDIO_APPROVAL")

    by_cue = {}
    observed_primary = {}
    flagged = set()
    for index, (cue, disp) in enumerate(zip(cues, dispositions), 1):
        need(type(cue) is dict and type(disp) is dict and
             cue.get("cue_index") == index and
             disp.get("cue_index") == index and
             type(cue.get("original_text")) is str and
             type(cue.get("cue_text_sha256")) is str and
             sha256(cue["original_text"].encode("utf-8")) ==
             cue["cue_text_sha256"] == disp.get("cue_text_sha256"),
             "CUE_POSITION_OR_TEXT_HASH_CHANGED")
        primary = cue.get("native_unapproved_primary_claim_ids")
        context = cue.get("native_unapproved_context_claim_ids")
        disp_ids = disp.get("claim_ids")
        need(type(primary) is list and type(context) is list and
             type(disp_ids) is list and
             all(type(x) is str for x in primary + context + disp_ids) and
             len(primary) == len(set(primary)) and
             len(context) == len(set(context)) and
             len(disp_ids) == len(set(disp_ids)) and
             sorted(primary) == sorted(disp_ids) and
             type(cue.get("needs_original_audio_or_screen")) is bool,
             "CUE_NATIVE_PRIMARY_OR_RISK_FLAGS")
        by_cue[index] = cue
        observed_primary[index] = set(primary)
        if cue["needs_original_audio_or_screen"]:
            flagged.add(index)

    by_atom = {}
    anchored = {}
    for atom in atoms:
        need(type(atom) is dict and type(atom.get("claim_id")) is str and
             atom["claim_id"] not in by_atom and
             atom.get("speaker") == "UNKNOWN" and
             atom.get("stance") == "UNRESOLVED" and
             type(atom.get("source_refs")) is list and
             bool(atom["source_refs"]) and
             type(atom.get("context_cue_indices")) is list,
             "NATIVE_ATOM_UNAPPROVED_AND_STRUCTURAL")
        cid = atom["claim_id"]
        by_atom[cid] = atom
        anchored[cid] = set()
        for ref in atom["source_refs"]:
            need(type(ref) is dict and
                 type(ref.get("cue_index")) is int and
                 ref["cue_index"] in by_cue and
                 type(ref.get("quote")) is str and
                 len(ref["quote"].strip()) >= 2 and
                 ref["quote"] in by_cue[ref["cue_index"]]["original_text"],
                 "PRIMARY_SOURCE_QUOTE_UNGROUNDED")
            i = ref["cue_index"]
            need(cid in observed_primary[i],
                 "PRIMARY_CLAIM_DISPOSITION_DRIFT")
            anchored[cid].add(i)
        for i in atom["context_cue_indices"]:
            need(type(i) is int and i in by_cue and
                 cid in by_cue[i]["native_unapproved_context_claim_ids"],
                 "CONTEXT_CLAIM_DISPOSITION_DRIFT")

    expected_primary = {i:set() for i in by_cue}
    for cid, indices in anchored.items():
        for i in indices:
            expected_primary[i].add(cid)
    need(expected_primary == observed_primary,
         "PRIMARY_ORPHAN_OR_DUPLICATE")
    for cue in cues:
        for cid in cue["native_unapproved_context_claim_ids"]:
            need(cid in by_atom and
                 cue["cue_index"] in by_atom[cid]["context_cue_indices"],
                 "CONTEXT_ORPHAN")
    unsafe_anchors = sorted(cid for cid, indices in anchored.items()
                            if indices & flagged)
    context_attention = sorted(a["claim_id"] for a in atoms if
        set(a["context_cue_indices"]) & flagged)
    return {
        "schema": SCHEMA,
        "source_sha256": exchange["source_sha256"],
        "native_exchange_sha256": expected_exchange_sha256,
        "coverage_original_bytes_sha256": expected_coverage_sha256,
        "cue_count": len(cues),
        "candidate_count": len(atoms),
        "source_flags_need_audio_or_screen_cue_count": len(flagged),
        "flagged_primary_atom_ids": unsafe_anchors,
        "flagged_context_atom_ids": context_attention,
        "flagged_primary_atom_count": len(unsafe_anchors),
        "automatic_visual_or_audio_promotion": False,
        "automatic_semantic_merge": False,
        "historical_owner_cross_equivalence_complete": False,
        "independent_gold_measured": False,
        "native_structure_reapproved_by_this_audit": False,
        "e2_final_pass": False,
        "e3_e4_e5_authorized": False,
        "knowledge_published": False,
        "status": "HOLD_SOURCE_EVIDENCE_AND_GOLD",
    }
