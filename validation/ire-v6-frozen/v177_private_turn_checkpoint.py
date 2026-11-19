"""V177: fail-closed, private, two-turn transfer for V176 actual ChatGPT research.

No LLM API and no semantic decisions are generated here. The private ZIP
contains ORIGINAL owner SRT, original-source-pinned SQLite backup and the exact
next V176 challenge. It is NOT encrypted and must NOT be published on GitHub.

External expected source SHA, previous SQLite head and reviewed count are
mandatory on *both* export and restore. They prevent accidental silent resets
but cannot provide cryptographic author authentication against a malicious
party that also controls the external expected pins.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import stat
import tempfile
import zipfile
from pathlib import Path

from v176_chat_engine_loop import EngineChatSession

SCHEMA = "IRE_V177_PRIVATE_TWO_TURN_RECOVERY_V1"
FILES = {"owner.srt", "review.sqlite", "next_challenge.json", "manifest.json"}
MAX_SOURCE = 32 * 1024 * 1024
MAX_DB = 128 * 1024 * 1024
MAX_CHALLENGE = 512 * 1024
MAX_MANIFEST = 32 * 1024


def _need(ok, code):
    if not ok:
        raise ValueError("V177_TWO_TURN_" + code)


def _sha(blob):
    return hashlib.sha256(blob).hexdigest()


def _canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _check_pin(sha, label):
    _need(type(sha) is str and len(sha) == 64 and
          all(c in "0123456789abcdef" for c in sha), label + "_SHA256_REQUIRED")


def _regular_file(path, code):
    p = Path(path)
    _need(p.is_file() and not p.is_symlink(), code + "_MISSING_OR_SYMLINK")
    return p


def _existing_private_db(path):
    p = _regular_file(path, "EXISTING_JOURNAL")
    _need(stat.S_IMODE(p.stat().st_mode) & 0o077 == 0,
          "INSECURE_DB_MODE")
    _need(p.stat().st_size > 0, "EMPTY_DB_NOT_RESUMABLE")
    # sqlite mode=ro refuses to manufacture an empty DB even when misconfigured.
    uri = p.resolve().as_uri() + "?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as con:
            result = con.execute("PRAGMA integrity_check").fetchone()
            _need(result is not None and result[0] == "ok",
                  "SQLITE_INTEGRITY_FAILURE")
            cfg = con.execute("SELECT v FROM config WHERE k='owner'").fetchone()
            _need(cfg is not None, "MISSING_OWNER_CONFIG")
    except sqlite3.DatabaseError as exc:
        raise ValueError("V177_TWO_TURN_SQLITE_NOT_VALID") from exc
    return p


def _assert_expected(session, *, expected_source_sha256, expected_head_sha256,
                     expected_reviewed, expected_total=None):
    p = session.progress()  # V176 verifies every event and owner-source cue pin.
    _need(p["source_sha256"] == expected_source_sha256,
          "OWNER_SOURCE_SHA_MISMATCH")
    _need(p["checkpoint_head_sha256"] == expected_head_sha256,
          "JOURNAL_HEAD_MISMATCH_DO_NOT_RESET")
    _need(p["cue_reviewed"] == expected_reviewed,
          "REVIEWED_COUNT_MISMATCH_DO_NOT_RESET")
    if expected_total is not None:
        _need(p["cue_total"] == expected_total, "SOURCE_CUE_CENSUS_MISMATCH")
    _need(not p["v123_pass_claimed"] and not p["e4_pass_claimed"] and
          p["e5_knowledge_written"] is False, "FALSE_NATIVE_APPROVAL")
    return p


def _make_session(db_path, raw, video_id, *, source_sha, window_size,
                  expected_windows):
    return EngineChatSession(db_path, raw, video_id,
        owner_source_sha256=source_sha, window_size=window_size,
        expected_window_count=expected_windows)


def _copy_sqlite_backup(source_path, dest_path):
    # A live V176 journal can advance during this backup. We re-open and
    # validate the SNAPSHOT against the externally expected checkpoint head.
    with sqlite3.connect(source_path) as src:
        with sqlite3.connect(dest_path) as dst:
            src.backup(dst)
    os.chmod(dest_path, 0o600)


def export_private_two_turn_bundle(*, srt_path, db_path, video_id,
        source_sha256, expected_head_sha256, expected_reviewed,
        output_zip, window_size=120, expected_windows=13,
        limit=20, context_radius=8):
    """Export last *proven* state; never initialize a missing journal.

    Returns only safe hash/count metadata, not original cue texts or judgments.
    """
    _check_pin(source_sha256, "OWNER")
    _check_pin(expected_head_sha256, "EXPECTED_JOURNAL")
    _need(type(expected_reviewed) is int and expected_reviewed >= 1,
          "POSITIVE_PREVIOUS_PROGRESS_REQUIRED")
    _need(type(video_id) is str and bool(video_id), "VIDEO_ID_REQUIRED")
    srt = _regular_file(srt_path, "ORIGINAL_SRT")
    db = _existing_private_db(db_path)  # BEFORE calling session's auto-create init
    _need(db.resolve() != srt.resolve(), "SRT_JOURNAL_PATH_COLLISION")
    raw = srt.read_bytes()
    _need(0 < len(raw) <= MAX_SOURCE and _sha(raw) == source_sha256,
          "ORIGINAL_OWNER_BYTES_WRONG")
    session = _make_session(db, raw, video_id, source_sha=source_sha256,
                            window_size=window_size, expected_windows=expected_windows)
    p = _assert_expected(session, expected_source_sha256=source_sha256,
        expected_head_sha256=expected_head_sha256,
        expected_reviewed=expected_reviewed)
    _need(p["cue_remaining"] > 0, "NOT_A_PENDING_FIRST_PASS")
    out = Path(output_zip)
    _need(not out.exists(), "NO_OVERWRITE_EXISTING_BUNDLE")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="v177backup_") as tmp:
        snapshot_path = Path(tmp) / "snapshot.sqlite"
        _copy_sqlite_backup(str(db), str(snapshot_path))
        _need(snapshot_path.stat().st_size <= MAX_DB,
              "PRIVATE_JOURNAL_EXCEEDS_BUNDLE_LIMIT")
        snap_engine = _make_session(snapshot_path, raw, video_id,
            source_sha=source_sha256, window_size=window_size,
            expected_windows=expected_windows)
        _assert_expected(snap_engine, expected_source_sha256=source_sha256,
            expected_head_sha256=expected_head_sha256,
            expected_reviewed=expected_reviewed,
            expected_total=p["cue_total"])
        challenge = snap_engine.prepare(limit=limit,
            context_radius=context_radius, source_first_only=True)
        _need(challenge["type"] == "CLASSIFY_SOURCE_CUES" and
              challenge["checkpoint_head_sha256"] == expected_head_sha256 and
              len(challenge["target_cues"]) > 0,
              "NO_REVIEWABLE_PERSISTENT_CHALLENGE")
        snapshot = snapshot_path.read_bytes()
        challenge_bytes = _canon(challenge)
        _need(len(challenge_bytes) <= MAX_CHALLENGE,
              "CHALLENGE_EXCEEDS_PRIVATE_LIMIT")
        manifest = {
          "schema": SCHEMA,
          "video_id": video_id,
          "source_sha256": source_sha256,
          "source_byte_count": len(raw),
          "source_cue_count": p["cue_total"],
          "journal_sha256": _sha(snapshot),
          "journal_byte_count": len(snapshot),
          "journal_head_sha256": expected_head_sha256,
          "previously_reviewed_cues": expected_reviewed,
          "challenge_sha256": _sha(challenge_bytes),
          "challenge_request_sha256": challenge["challenge_sha256"],
          "target_cue_indices": [r["cue_index"] for r in challenge["target_cues"]],
          "window_size": window_size,
          "expected_windows": expected_windows,
          "request_limit": limit,
          "context_radius": context_radius,
          "source_first_only": True,
          "private_unencrypted_archive": True,
          "model_decision_in_archive": False,
          "native_v123_approved": False,
          "e4_approved": False,
          "e5_authorized": False,
        }
        manifest_bytes = _canon(manifest)
        _need(len(manifest_bytes) <= MAX_MANIFEST, "MANIFEST_TOO_LARGE")
        fd = os.open(str(out), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            with os.fdopen(fd, "wb") as dest:
                with zipfile.ZipFile(dest, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
                    z.writestr("owner.srt", raw)
                    z.writestr("review.sqlite", snapshot)
                    z.writestr("next_challenge.json", challenge_bytes)
                    z.writestr("manifest.json", manifest_bytes)
        except BaseException:
            out.unlink(missing_ok=True)
            raise
    _need(stat.S_IMODE(out.stat().st_mode) == 0o600,
          "ARCHIVE_MODE_UNSAFE")
    return {
        "schema": SCHEMA,
        "source_sha256": source_sha256,
        "checkpoint_head_sha256": expected_head_sha256,
        "cue_reviewed": expected_reviewed,
        "cue_remaining": p["cue_remaining"],
        "next_cue_start": manifest["target_cue_indices"][0],
        "next_cue_end": manifest["target_cue_indices"][-1],
        "archive_sha256": _sha(out.read_bytes()),
        "manifest_sha256": _sha(manifest_bytes),
        "native_v123_approved": False,
        "e4_approved": False,
        "e5_authorized": False,
    }


def _read_archive(bundle):
    zpath = _regular_file(bundle, "PRIVATE_BUNDLE")
    _need(zpath.stat().st_size <= MAX_DB + MAX_SOURCE + MAX_CHALLENGE + 4*MAX_MANIFEST,
          "BUNDLE_OVERSIZED")
    with zipfile.ZipFile(zpath, "r") as z:
        infos = z.infolist()
        _need(len(infos) == len(FILES) and
              {i.filename for i in infos} == FILES and
              all(not (stat.S_IFMT(i.external_attr >> 16) == stat.S_IFLNK)
                      for i in infos), "BUNDLE_ENTRIES_UNSAFE")
        caps = {"owner.srt": MAX_SOURCE, "review.sqlite": MAX_DB,
                "next_challenge.json": MAX_CHALLENGE,
                "manifest.json": MAX_MANIFEST}
        _need(all(0 < i.file_size <= caps[i.filename] for i in infos),
              "BUNDLE_MEMBER_UNBOUNDED")
        content = {n: z.read(n) for n in FILES}
    try:
        manifest = json.loads(content["manifest.json"])
        challenge = json.loads(content["next_challenge.json"])
    except (TypeError, ValueError) as exc:
        raise ValueError("V177_TWO_TURN_BAD_CHALLENGE_OR_MANIFEST") from exc
    _need(type(manifest) is dict and manifest.get("schema") == SCHEMA and
          type(challenge) is dict and
          content["manifest.json"] == _canon(manifest) and
          content["next_challenge.json"] == _canon(challenge),
          "MANIFEST_OR_CHALLENGE_NOT_CANONICAL")
    _need(_sha(content["owner.srt"]) == manifest.get("source_sha256") and
          len(content["owner.srt"]) == manifest.get("source_byte_count") and
          _sha(content["review.sqlite"]) == manifest.get("journal_sha256") and
          len(content["review.sqlite"]) == manifest.get("journal_byte_count") and
          _sha(content["next_challenge.json"]) == manifest.get("challenge_sha256"),
          "ARCHIVE_INNER_BYTE_HASH_DRIFT")
    _need(challenge.get("challenge_sha256") == manifest["challenge_request_sha256"] and
          challenge.get("checkpoint_head_sha256") == manifest["journal_head_sha256"] and
          [r["cue_index"] for r in challenge["target_cues"]] ==
          manifest["target_cue_indices"] and
          manifest["source_first_only"] is True and
          manifest["private_unencrypted_archive"] is True and
          manifest["model_decision_in_archive"] is False and
          all(manifest[k] is False for k in (
              "native_v123_approved", "e4_approved", "e5_authorized")),
          "MALFORMED_OR_FALSE_APPROVAL_MANIFEST")
    return content, manifest, challenge


def restore_private_two_turn_bundle(*, input_zip, output_dir,
        expected_source_sha256, expected_head_sha256, expected_reviewed,
        expected_video_id):
    """Verify external pins, restore owner-private snapshot, reconstruct next task.

    Restoration never overwrites existing state; a bad archive leaves no valid
    restored state. The verified challenge is returned to the active chat for
    real semantic review, not automatically answered by the Python engine.
    """
    _check_pin(expected_source_sha256, "OWNER")
    _check_pin(expected_head_sha256, "EXPECTED_JOURNAL")
    _need(type(expected_reviewed) is int and expected_reviewed >= 1,
          "POSITIVE_PREVIOUS_PROGRESS_REQUIRED")
    content, manifest, challenge = _read_archive(input_zip)
    _need((manifest["source_sha256"], manifest["journal_head_sha256"],
           manifest["previously_reviewed_cues"], manifest["video_id"]) ==
          (expected_source_sha256, expected_head_sha256,
           expected_reviewed, expected_video_id),
          "EXTERNAL_OWNER_HEAD_PROGRESS_PIN_MISMATCH")
    out = Path(output_dir)
    _need(not out.exists(), "RESTORE_DESTINATION_MUST_BE_NEW")
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    try:
        for name, entry in (("original.srt", "owner.srt"),
                            ("owner.sqlite", "review.sqlite"),
                            ("next_challenge.json", "next_challenge.json")):
            p = out / name
            fd = os.open(str(p), os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(content[entry])
        _existing_private_db(out / "owner.sqlite")
        engine = _make_session(out / "owner.sqlite", content["owner.srt"],
            expected_video_id, source_sha=expected_source_sha256,
            window_size=manifest["window_size"],
            expected_windows=manifest["expected_windows"])
        p = _assert_expected(engine,
            expected_source_sha256=expected_source_sha256,
            expected_head_sha256=expected_head_sha256,
            expected_reviewed=expected_reviewed,
            expected_total=manifest["source_cue_count"])
        fresh = engine.prepare(limit=manifest["request_limit"],
            context_radius=manifest["context_radius"],
            source_first_only=True)
        _need(fresh == challenge, "PENDING_CHALLENGE_NOT_REISSUABLE")
    except BaseException:
        for file in (out / "original.srt", out / "owner.sqlite",
                     out / "next_challenge.json"):
            file.unlink(missing_ok=True)
        out.rmdir()
        raise
    return {"schema": SCHEMA,
            "source_sha256": expected_source_sha256,
            "checkpoint_head_sha256": expected_head_sha256,
            "previously_reviewed_cues": p["cue_reviewed"],
            "remaining_cues": p["cue_remaining"],
            "pending_challenge_sha256": challenge["challenge_sha256"],
            "next_cue_indices": [r["cue_index"] for r in challenge["target_cues"]],
            "restore_dir": str(out),
            "ready_for_actual_chat_review": True,
            "model_review_performed_by_restore": False,
            "native_v123_approved": False,
            "e4_approved": False,
            "e5_authorized": False}


def main(argv=None):
    p = argparse.ArgumentParser(description="V177 actual two-turn owner-private restore, never reset to zero")
    q = p.add_subparsers(dest="action", required=True)
    a = q.add_parser("export")
    a.add_argument("--srt", required=True)
    a.add_argument("--db", required=True)
    a.add_argument("--sha", required=True)
    a.add_argument("--video-id", required=True)
    a.add_argument("--head", required=True)
    a.add_argument("--reviewed", required=True, type=int)
    a.add_argument("--zip", required=True)
    a.add_argument("--window-size", type=int, default=120)
    a.add_argument("--windows", type=int, default=13)
    a.add_argument("--limit", type=int, default=20)
    a.add_argument("--radius", type=int, default=8)
    b = q.add_parser("restore")
    b.add_argument("--zip", required=True)
    b.add_argument("--out-dir", required=True)
    b.add_argument("--sha", required=True)
    b.add_argument("--video-id", required=True)
    b.add_argument("--head", required=True)
    b.add_argument("--reviewed", required=True, type=int)
    args = p.parse_args(argv)
    if args.action == "export":
        value = export_private_two_turn_bundle(
            srt_path=args.srt, db_path=args.db, video_id=args.video_id,
            source_sha256=args.sha, expected_head_sha256=args.head,
            expected_reviewed=args.reviewed, output_zip=args.zip,
            window_size=args.window_size, expected_windows=args.windows,
            limit=args.limit, context_radius=args.radius)
    else:
        value = restore_private_two_turn_bundle(
            input_zip=args.zip, output_dir=args.out_dir,
            expected_source_sha256=args.sha,
            expected_head_sha256=args.head,
            expected_reviewed=args.reviewed,
            expected_video_id=args.video_id)
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())