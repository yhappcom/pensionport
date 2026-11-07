"""Fail-closed P0 incremental source-integrity gate for the real one-turn path.

This gate replays committed redacted batch structure and content hashes; it
NEVER independently rereads private SRT bytes, performs model inference,
establishes semantic completeness, or approves financial advice. Future
batches are registered in a versioned manifest, not hard-coded by video.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zlib

from .validation.p0_generic_source_review_gate import validate_source_review

SCHEMA = "IRE_V5_P0_INCREMENTAL_QUALITY_MANIFEST_V1"
MANIFEST = Path("ire/v5/validation/p0_incremental_quality_manifest.json")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_WINDOW = re.compile(r"W[0-9]{5}\Z")


class IncrementalQualityError(ValueError):
    pass


def _require(ok: bool, code: str) -> None:
    if not ok:
        raise IncrementalQualityError(code)


def _decode_bundle(path: Path) -> dict:
    encoded = path.read_text("ascii").strip()
    packed = base64.b64decode(encoded, validate=True)
    unpack = zlib.decompressobj()
    raw = unpack.decompress(packed, 1_000_000)
    _require(unpack.eof and not unpack.unused_data and not unpack.unconsumed_tail,
             "BUNDLE_COMPRESSION_OR_SIZE_INVALID")
    value = json.loads(raw)
    _require(type(value) is dict, "BUNDLE_NOT_OBJECT")
    return value, hashlib.sha256(raw).hexdigest()


def verify(root: Path, manifest_path: Path | None = None) -> dict:
    root = Path(root).resolve()
    manifest_path = root / MANIFEST if manifest_path is None else Path(manifest_path)
    manifest = json.loads(manifest_path.read_text("utf-8"))
    _require(type(manifest) is dict and manifest.get("schema") == SCHEMA, "MANIFEST_SCHEMA")
    _require(manifest.get("p0_go") is False and
             manifest.get("independent_recall_certified") is False and
             manifest.get("formal_researchrun_submitted") is False, "MANIFEST_FALSE_GO")
    batches = manifest.get("batches")
    _require(type(batches) is list and bool(batches), "EMPTY_BATCH_REGISTRY")
    seen_batches: set[str] = set()
    seen_claims: dict[str, set[str]] = {}
    previous: dict[str, tuple[str, int, str, str]] = {}
    counts = {"batches": 0, "windows": 0, "cues": 0, "provisional_claims": 0}
    pointers = {}
    for entry in batches:
        _require(type(entry) is dict and type(entry.get("batch_id")) is str and
                 bool(entry["batch_id"]) and entry["batch_id"] not in seen_batches,
                 "DUPLICATE_OR_MISSING_BATCH_ID")
        seen_batches.add(entry["batch_id"])
        rel = entry.get("path")
        _require(type(rel) is str and rel.startswith("ire/v5/validation/") and
                 rel.endswith(".json.zlib.b64") and
                 all(piece not in ("", ".", "..") for piece in PurePosixPath(rel).parts),
                 "BUNDLE_PATH_INVALID")
        source_file = (root / rel).resolve()
        _require(source_file.is_relative_to(root / "ire/v5/validation") and
                 source_file.is_file(), "BUNDLE_FILE_MISSING_OR_ESCAPED")
        for name in ("payload_sha256", "archive_sha256", "source_sha256"):
            _require(type(entry.get(name)) is str and _SHA.fullmatch(entry[name]) is not None,
                     "BATCH_HASH_INVALID")
        record, digest = _decode_bundle(source_file)
        _require(digest == entry["payload_sha256"], "BUNDLE_PAYLOAD_HASH_DRIFT")
        _require(record.get("source_sha256") == entry["source_sha256"] and
                 record.get("archive_sha256") == entry["archive_sha256"] and
                 record.get("video_id") == entry.get("video_id"), "SOURCE_IDENTITY_DRIFT")
        result = validate_source_review(record)
        _require(result["window_count"] == entry.get("expected_windows") and
                 result["cue_count"] == entry.get("expected_cues") and
                 result["provisional_claims"] == entry.get("expected_claims"),
                 "REVIEW_CENSUS_DRIFT")
        _require(record["windows"][0]["window_id"] == entry.get("first_window") and
                 record["first_cue"] == entry.get("first_cue") and
                 result["next_window"] == entry.get("next_window"), "BATCH_POINTER_DRIFT")
        video = entry["video_id"]
        if video in previous:
            next_window, next_cue, previous_source, previous_archive = previous[video]
            _require(entry["first_window"] == next_window and
                     entry["first_cue"] == next_cue, "CROSS_BATCH_GAP_OR_OVERLAP")
            _require(entry["source_sha256"] == previous_source and
                     entry["archive_sha256"] == previous_archive, "CROSS_BATCH_SOURCE_DRIFT")
        claims = seen_claims.setdefault(video, set())
        new_claims = {c["candidate_id"] for c in record["candidates"]}
        _require(not (claims & new_claims), "CROSS_BATCH_CLAIM_ID_DUPLICATE")
        claims.update(new_claims)
        previous[video] = (result["next_window"], record["last_cue"] + 1,
                           entry["source_sha256"], entry["archive_sha256"])
        pointers[video] = result["next_window"]
        counts["batches"] += 1
        counts["windows"] += result["window_count"]
        counts["cues"] += result["cue_count"]
        counts["provisional_claims"] += result["provisional_claims"]
    return {"schema": "IRE_V5_P0_INCREMENTAL_QUALITY_GATE_V1", **counts,
            "next_windows_by_video": pointers,
            "source_derivative_integrity_checked": True,
            "private_original_replayed": False,
            "semantic_completeness_certified": False,
            "independent_recall_certified": False,
            "p0_go": False}
