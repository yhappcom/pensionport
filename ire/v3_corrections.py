"""V3 append-only correction overlays for financial claim meaning.

Original source-tied V2/V3 checkpoint bytes stay immutable. A current-chat
analyst may submit a revised full window answer, sealed to the original checkpoint,
source packet, parent answer and all earlier corrections. Such a submission is
not independent human review and does not approve underlying financial facts.
"""
from __future__ import annotations

from datetime import date
import json
import os
import re
from pathlib import Path

from .source import require, sha256, DIGEST
from .semantics import verify_window_before_caching
from .v3_semantic_audit import window_semantic_audit

SCHEMA = "IRE_V3_CHAT_CORRECTION_V1"
SUBMISSION_SCHEMA = "IRE_V3_CHAT_CORRECTION_SUBMISSION_V1"
REASONS = frozenset({
    "UNSUPPORTED_UNIT", "UNCITED_PRODUCT_SCOPE", "FALSE_NUMERIC_PRECISION",
    "MISATTRIBUTED_SPEAKER", "UNCITED_CONDITION_OR_EXCEPTION",
    "NONCLAIM_MISCLASSIFICATION", "INCOMPLETE_ATOMIC_CLAIM",
    "OTHER_SOURCE_MEANING_CORRECTION",
})


def _serialized(body):
    return json.dumps(body, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _folder(session, create: bool) -> Path:
    root = session.folder / "corrections"
    if root.exists():
        require(root.is_dir() and root.stat().st_mode & 0o077 == 0,
                "V3_CORRECTION_DIRECTORY_NOT_PRIVATE")
    elif create:
        root.mkdir(mode=0o700)
    return root


def _revision_files(session, window_id):
    root = _folder(session, False)
    if not root.exists():
        return []
    result = sorted(root.glob(window_id + "_rev*.json"))
    require(len(result) < 100, "V3_CORRECTION_REVISION_LIMIT_EXCEEDED")
    return result


def effective_reply(session, window_id: str, original: dict) -> dict:
    """Read and verify the entire immutable revision chain, or fail closed."""
    file = session.answers / (window_id + ".json")
    require(file.exists(), "V3_CORRECTION_REQUIRES_BASE_CHECKPOINT")
    base_digest = sha256(file.read_bytes())
    packet = session.packet(window_id)
    expected_prior = sha256(_serialized(original))
    result = original
    for revision, path in enumerate(_revision_files(session, window_id), 1):
        match = re.fullmatch(r"W\d{5}_rev(\d{4})_[0-9a-f]{16}\.json", path.name)
        require(match is not None and int(match.group(1)) == revision,
                "V3_CORRECTION_REVISION_CHAIN_BROKEN")
        entry = json.loads(path.read_text(encoding="utf-8"))
        require(type(entry) is dict and set(entry) == {"receipt_sha256", "body"},
                "V3_CORRECTION_RECEIPT_SCHEMA_INVALID")
        body = entry["body"]
        require(type(body) is dict and set(body) == {
            "schema", "revision", "video_id", "session_id", "window_id",
            "source_sha256", "packet_sha256", "base_checkpoint_sha256",
            "prior_answer_sha256", "corrected_answer_sha256", "corrected_answer",
            "reason_codes", "affected_claim_ordinals", "review_note",
            "reviewed_as_of", "reviewer_mode", "independent_human_reviewer",
            "financial_truth_approved",
        } and body["schema"] == SCHEMA and body["revision"] == revision and
                body["video_id"] == session.video_id and
                body["session_id"] == session.session_id and
                body["window_id"] == window_id and
                body["source_sha256"] == session.digest and
                body["packet_sha256"] == packet["packet_sha256"] and
                body["base_checkpoint_sha256"] == base_digest and
                body["prior_answer_sha256"] == expected_prior and
                body["reviewer_mode"] == "CURRENT_CHATGPT_CONVERSATION" and
                body["independent_human_reviewer"] is False and
                body["financial_truth_approved"] is False,
                "V3_CORRECTION_IDENTITY_OR_PARENT_MISMATCH")
        require(entry["receipt_sha256"] == sha256(_serialized(body)) and
                path.name.endswith(entry["receipt_sha256"][:16] + ".json") and
                body["corrected_answer_sha256"] ==
                    sha256(_serialized(body["corrected_answer"])),
                "V3_CORRECTION_HASH_OR_NAME_MISMATCH")
        require(type(body["reason_codes"]) is list and
                1 <= len(body["reason_codes"]) <= 10 and
                set(body["reason_codes"]) <= REASONS and
                len(set(body["reason_codes"])) == len(body["reason_codes"]) and
                type(body["affected_claim_ordinals"]) is list and
                bool(body["affected_claim_ordinals"]) and
                all(type(n) is int and n >= 1 for n in body["affected_claim_ordinals"]) and
                len(set(body["affected_claim_ordinals"])) ==
                    len(body["affected_claim_ordinals"]) and
                type(body["review_note"]) is str and
                16 <= len(body["review_note"]) <= 4000 and
                type(body["reviewed_as_of"]) is str and
                date.fromisoformat(body["reviewed_as_of"]).isoformat() ==
                    body["reviewed_as_of"],
                "V3_CORRECTION_REVIEW_MANIFEST_INVALID")
        corrected = body["corrected_answer"]
        require(type(corrected) is dict and corrected != result,
                "V3_CORRECTION_MUST_CHANGE_PREVIOUS_ANSWER")
        verify_window_before_caching(session.original, session.digest,
                                     session._window(window_id), corrected)
        audit = window_semantic_audit(packet, corrected)
        require(not audit["critical"],
                "V3_CORRECTION_REINTRODUCED_CRITICAL_OMISSION")
        result = corrected
        expected_prior = body["corrected_answer_sha256"]
    return result


def submit_correction(session, submission: dict) -> dict:
    """Validate the complete new effective answer BEFORE any file write."""
    require(type(submission) is dict and set(submission) == {
        "schema", "video_id", "session_id", "window_id", "packet_sha256",
        "prior_answer_sha256", "reason_codes", "affected_claim_ordinals",
        "review_note", "reviewed_as_of", "corrected_answer",
    } and submission.get("schema") == SUBMISSION_SCHEMA and
            submission.get("video_id") == session.video_id and
            submission.get("session_id") == session.session_id and
            type(submission.get("window_id")) is str and
            re.fullmatch(r"W\d{5}", submission["window_id"]) and
            submission.get("packet_sha256") ==
                session.packet(submission["window_id"])["packet_sha256"],
            "V3_CORRECTION_SUBMISSION_IDENTITY_INVALID")
    window_id = submission["window_id"]
    before = session._answer(window_id)
    require(before is not None,
            "V3_CORRECTION_TARGET_NOT_YET_SUBMITTED")
    prior_sha = sha256(_serialized(before))
    require(prior_sha == submission["prior_answer_sha256"],
            "V3_CORRECTION_STALE_PRIOR_ANSWER")
    corrected = submission["corrected_answer"]
    require(type(corrected) is dict and corrected != before,
            "V3_CORRECTION_EMPTY_REVISION")
    verify_window_before_caching(session.original, session.digest,
                                 session._window(window_id), corrected)
    audit = window_semantic_audit(session.packet(window_id), corrected)
    require(not audit["critical"],
            "V3_CORRECTION_REINTRODUCED_CRITICAL_OMISSION")
    reasons = submission["reason_codes"]
    ordinals = submission["affected_claim_ordinals"]
    note = submission["review_note"]
    as_of = submission["reviewed_as_of"]
    require(type(reasons) is list and 1 <= len(reasons) <= 10 and
            set(reasons) <= REASONS and len(set(reasons)) == len(reasons) and
            type(ordinals) is list and bool(ordinals) and
            len(set(ordinals)) == len(ordinals) and
            all(type(n) is int and 1 <= n <= len(before["claims"])
                for n in ordinals) and
            type(note) is str and 16 <= len(note) <= 4000 and
            type(as_of) is str and date.fromisoformat(as_of).isoformat() == as_of,
            "V3_CORRECTION_REVIEW_MANIFEST_INVALID")
    revision = len(_revision_files(session, window_id)) + 1
    base = session.answers / (window_id + ".json")
    body = {
        "schema": SCHEMA,
        "revision": revision,
        "video_id": session.video_id,
        "session_id": session.session_id,
        "window_id": window_id,
        "source_sha256": session.digest,
        "packet_sha256": submission["packet_sha256"],
        "base_checkpoint_sha256": sha256(base.read_bytes()),
        "prior_answer_sha256": prior_sha,
        "corrected_answer_sha256": sha256(_serialized(corrected)),
        "corrected_answer": corrected,
        "reason_codes": reasons,
        "affected_claim_ordinals": ordinals,
        "review_note": note,
        "reviewed_as_of": as_of,
        "reviewer_mode": "CURRENT_CHATGPT_CONVERSATION",
        "independent_human_reviewer": False,
        "financial_truth_approved": False,
    }
    digest = sha256(_serialized(body))
    receipt = {"receipt_sha256": digest, "body": body}
    path = _folder(session, True) / (
        f"{window_id}_rev{revision:04d}_" + digest[:16] + ".json")
    encoded = _serialized(receipt)
    fd = os.open(path, os.O_WRONLY | os.O_EXCL | os.O_CREAT, 0o600)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(encoded)
            out.flush()
            os.fsync(out.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    require(effective_reply(session, window_id,
                            session._answer_original(window_id)) == corrected,
            "V3_CORRECTION_PERSISTENCE_READBACK_FAILED")
    return {
        "schema": "IRE_V3_CHAT_CORRECTION_RECEIPT_V1",
        "video_id": session.video_id,
        "window_id": window_id,
        "revision": revision,
        "receipt_sha256": digest,
        "base_checkpoint_preserved": True,
        "corrected_answer_is_model_provisional": True,
        "finance_truth_approved": False,
    }