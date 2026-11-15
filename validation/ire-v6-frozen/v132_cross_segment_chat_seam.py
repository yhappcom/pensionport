"""V132 explicit cross-child ChatGPT source-cue seam adjudication.

Validates a *supplied* ChatGPT review, never invents it. This is a single
source-cue discourse correction, NOT V123 final approval or historical proof.
Only immutable cue/source hashes are accepted as external join anchors.
"""
from __future__ import annotations
import re
from ire.v6.codec import sha256, json_digest
from ire.v6.errors import QualityNotProven
from v131_explicit_chat_cue_dispositions import audit_explicit_chat_dispositions

_SHA = re.compile(r"[0-9a-f]{64}\Z")


def _block(code):
    raise QualityNotProven("V132_SEAM_" + code)


def audit_explicit_cross_segment_question(left, right, previous, revised, seam):
    """Resolve one segment-end open only as speculative source discourse.

    The preceding cue-level review and entire source remain immutable. Only
    the last cue's explicit context-role disposition can change from OPEN to
    REVIEWED. Other unresolved cues remain OPEN; no finance/claim approval.
    """
    if (left.video_id != right.video_id or
        left.source_sha256 != right.source_sha256 or
        left.scope_last_cue + 1 != right.scope_first_cue or
        left.scope_first_cue < 1):
        _block("SOURCE_OR_CHILD_SCOPE_DISJOINT")
    old = audit_explicit_chat_dispositions(left, previous)
    if old["status"] != "HOLD_OPEN_CUE_DISPOSITIONS":
        _block("ORIGINAL_MUST_BE_EXPLICIT_OPEN")
    end = left.scope_last_cue
    old_rows = previous["cue_rows"]
    new_rows = revised.get("cue_rows") if type(revised) is dict else None
    if type(new_rows) is not list or len(new_rows) != len(old_rows):
        _block("REVIEW_REVISION_MISSING")
    old_end = old_rows[-1]
    new_end = new_rows[-1]
    if old_end["cue_index"] != end or old_end["role"] != "OPEN" or old_end["review_state"] != "OPEN":
        _block("PREVIOUS_BOUNDARY_NOT_OPEN")
    if ({k: v for k, v in previous.items() if k != "cue_rows"} !=
        {k: v for k, v in revised.items() if k != "cue_rows"} or
        old_rows[:-1] != new_rows[:-1]):
        _block("OTHER_CUE_OR_ATOM_REWRITTEN")
    if type(new_end) is not dict:
        _block("UNJUSTIFIED_BOUNDARY_ROLE_REVISION")
    expected = dict(old_end)
    expected.update({"role": "CONTEXT", "review_state": "REVIEWED",
                     "atom_ids": [], "rationale": new_end.get("rationale")})
    if (type(new_end) is not dict or new_end != expected or not isinstance(new_end["rationale"], str) or
        len(new_end["rationale"].strip()) < 35):
        _block("UNJUSTIFIED_BOUNDARY_ROLE_REVISION")
    new_audit = audit_explicit_chat_dispositions(left, revised)
    if (old["unresolved_open_cues"] - new_audit["unresolved_open_cues"] != 1 or
        new_audit["unresolved_open_cues"] == 0):
        _block("UNREVIEWED_OPEN_CUES_SILENTLY_CLOSED")
    last = min(end + 5, right.scope_last_cue)
    cue_indices = list(range(end, last + 1))
    if len(cue_indices) < 3:
        _block("INSUFFICIENT_FOLLOWUP_CUES")
    expected_sha = [sha256(left.cues[i-1].text.encode("utf-8")) for i in cue_indices]
    required = {"schema", "reviewer", "video_id", "parent_source_sha256",
                "left_manifest_sha256", "right_manifest_sha256",
                "cue_indices", "cue_text_sha256", "discourse_kind",
                "semantic_interpretation", "source_based_counterexample",
                "literal_spoken_question_confirmed", "financial_success_fact_verified",
                "independent_audio_speaker_verified", "chat_private_review_sha256"}
    if type(seam) is not dict or set(seam) != required:
        _block("CHAT_SEAM_REVIEW_SCHEMA")
    if (seam["schema"] != "IRE_V132_CHAT_BOUNDARY_QUESTION_DISPOSITION_V1" or
        seam["reviewer"] != "CHATGPT_IN_CHAT" or
        seam["video_id"] != left.video_id or
        seam["parent_source_sha256"] != left.source_sha256 or
        seam["left_manifest_sha256"] != left.manifest_sha256 or
        seam["right_manifest_sha256"] != right.manifest_sha256 or
        seam["cue_indices"] != cue_indices or
        seam["cue_text_sha256"] != expected_sha or
        seam["discourse_kind"] != "SPECULATIVE_QUESTION_NOT_ESTABLISHED_RETURN" or
        seam["literal_spoken_question_confirmed"] is not True or
        seam["financial_success_fact_verified"] is not False or
        seam["independent_audio_speaker_verified"] is not False):
        _block("BOUNDARY_SOURCE_OR_MEANING_CONTRADICTION")
    if not any("?" in right.cues[i-1].text for i in cue_indices[1:]):
        _block("QUESTION_NOT_IN_FOLLOWUP_SOURCE")
    for key in ("semantic_interpretation", "source_based_counterexample"):
        if type(seam[key]) is not str or len(seam[key].strip()) < 30:
            _block("CHAT_MEANING_AND_COUNTEREXAMPLE_MISSING")
    evidence_sha=sha256((seam["semantic_interpretation"] + "\n" +
                         seam["source_based_counterexample"]).encode("utf-8"))
    if (seam["chat_private_review_sha256"] != evidence_sha or
        not _SHA.fullmatch(seam["chat_private_review_sha256"])):
        _block("PRIVATE_CHAT_EVIDENCE_HASH_DRIFT")
    return {
        "schema": "IRE_V132_CROSS_SEGMENT_CHAT_SEAM_AUDIT_V1",
        "video_id": left.video_id, "parent_source_sha256": left.source_sha256,
        "cue_indices": cue_indices, "source_cues_replayed": len(cue_indices),
        "seam_review_sha256": json_digest(seam),
        "revised_left_packet_sha256": json_digest(revised),
        "original_unresolved_open_cues": old["unresolved_open_cues"],
        "remaining_unresolved_open_cues": new_audit["unresolved_open_cues"],
        "status": "QUESTION_SEAM_CONTEXT_RESOLVED_V123_STILL_HOLD",
        "historical_followers_success_claim_accepted": False,
        "independent_audio_speaker_attribution_verified": False,
        "full_atomic_claims_exhausted": False,
        "v123_chat_final_passed": False,
        "knowledge_export_authorized": False, "p0_go": False,
    }
