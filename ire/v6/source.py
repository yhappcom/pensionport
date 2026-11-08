"""V6-2 private-original replay: verify actual bytes, cues and window ownership.

Hash syntax is never treated as replay evidence. The caller must pin the
expected source and manifest digests independently from the bytes supplied.
All raw text remains in memory; event payloads contain hashes/counts only.
"""
from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from dataclasses import dataclass

from .codec import WINDOW, VIDEO, json_digest, require_hash, require_identifier, sha256
from .errors import InvalidInput

SRT_CLOCK = re.compile(r"(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})\Z")
SRT_ARROW = re.compile(r"\s*-->\s*")
MAX_SOURCE_SIZE = 32 * 1024 * 1024
MAX_CUE_CENSUS_BYTES = 128 * 1024 * 1024


@dataclass(frozen=True)
class Cue:
    index: int
    start_ms: int
    end_ms: int
    text: str


def _clock(value: str) -> int:
    match = SRT_CLOCK.fullmatch(value.strip())
    if match is None:
        raise InvalidInput("SRT_CLOCK_INVALID")
    hh, mm, ss, ms = map(int, match.groups())
    if mm >= 60 or ss >= 60:
        raise InvalidInput("SRT_CLOCK_UNIT_INVALID")
    return ((hh * 60 + mm) * 60 + ss) * 1000 + ms


def parse_srt(raw: bytes) -> tuple[Cue, ...]:
    if type(raw) is not bytes or not raw or len(raw) > MAX_SOURCE_SIZE:
        raise InvalidInput("SRT_BYTES_REQUIRED_WITHIN_LIMIT")
    try:
        data = raw.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise InvalidInput("SRT_UTF8_INVALID") from exc
    blocks = re.split(r"\n\s*\n", data.replace("\r\n", "\n").replace("\r", "\n").strip())
    cues: list[Cue] = []
    previous_start = -1
    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 3 or not lines[0].strip().isdecimal():
            raise InvalidInput("SRT_BLOCK_INVALID")
        idx = int(lines[0].strip())
        if idx != len(cues) + 1:
            raise InvalidInput("SRT_CUE_INDEX_NOT_CONTIGUOUS")
        times = SRT_ARROW.split(lines[1].strip())
        if len(times) != 2:
            raise InvalidInput("SRT_TIME_ARROW_INVALID")
        start, end = (_clock(t) for t in times)
        if end < start:
            raise InvalidInput("SRT_END_BEFORE_START")
        if start < previous_start:
            raise InvalidInput("SRT_NON_MONOTONIC_START")
        text = " ".join(t.strip() for t in lines[2:] if t.strip())
        if not text:
            raise InvalidInput("SRT_EMPTY_CUE")
        cues.append(Cue(idx, start, end, text))
        previous_start = start
    if not cues:
        raise InvalidInput("SRT_NO_CUES")
    return tuple(cues)


@dataclass(frozen=True)
class VerifiedSource:
    video_id: str
    source_sha256: str
    manifest_sha256: str
    cue_census_sha256: str
    cues: tuple[Cue, ...]
    scope_first_cue: int
    scope_last_cue: int
    primary_windows: tuple[tuple[str, int, int], ...]

    def attestation(self) -> dict:
        return {
            "video_id": self.video_id,
            "source_sha256": self.source_sha256,
            "manifest_sha256": self.manifest_sha256,
            "cue_census_sha256": self.cue_census_sha256,
            "cue_count": len(self.cues),
            "scope_first_cue": self.scope_first_cue,
            "scope_last_cue": self.scope_last_cue,
            "window_count": len(self.primary_windows),
        }

    def owner(self, cue_index: int) -> str | None:
        for wid, first, last in self.primary_windows:
            if first <= cue_index <= last:
                return wid
        return None


def cue_census_digest(cues: tuple[Cue, ...]) -> str:
    """Hash the exact canonical cue list without the *event* payload size limit.

    Inputs originate from a <=32-MiB SRT. Do not hold the fully encoded cue
    list in memory; each small row is encoded deterministically and streamed
    into SHA256, preserving the existing canonical digest for old sources.
    This digest is not an event payload and is never stored as raw source text.
    """
    digest = hashlib.sha256()
    digest.update(b"[")
    encoded_length = 2
    for pos, cue in enumerate(cues):
        row = {"index": cue.index, "start_ms": cue.start_ms,
               "end_ms": cue.end_ms, "text": cue.text}
        raw = json.dumps(row, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
        encoded_length += len(raw) + (1 if pos else 0)
        if encoded_length > MAX_CUE_CENSUS_BYTES:
            raise InvalidInput("CUE_CENSUS_DIGEST_INPUT_TOO_LARGE")
        if pos:
            digest.update(b",")
        digest.update(raw)
    digest.update(b"]")
    return digest.hexdigest()


def verify_source(raw: bytes, manifest: dict, *,
                  expected_source_sha256: str,
                  expected_manifest_sha256: str) -> VerifiedSource:
    """No I/O. Pin source+plan to an external trust boundary, never self-pinned."""
    expected_source_sha256 = require_hash(expected_source_sha256, "PINNED_SOURCE")
    expected_manifest_sha256 = require_hash(expected_manifest_sha256, "PINNED_MANIFEST")
    # Take a detached plan snapshot before hashing/checking. Caller mutation
    # after validation must not change the attested source plan.
    if type(manifest) is not dict:
        raise InvalidInput("SOURCE_MANIFEST_SCHEMA_INVALID")
    manifest = deepcopy(manifest)
    if set(manifest) != {
        "schema", "video_id", "source_sha256", "cue_count", "scope", "windows"
    } or manifest["schema"] != "IRE_V6_SOURCE_PLAN_V1":
        raise InvalidInput("SOURCE_MANIFEST_SCHEMA_INVALID")
    video_id = require_identifier(manifest["video_id"], VIDEO, "VIDEO_ID")
    source_hash = sha256(raw) if type(raw) is bytes else ""
    manifest_hash = json_digest(manifest)
    if (source_hash != expected_source_sha256 or
        manifest["source_sha256"] != expected_source_sha256 or
        manifest_hash != expected_manifest_sha256):
        raise InvalidInput("PINNED_SOURCE_OR_PLAN_BYTES_MISMATCH")
    cues = parse_srt(raw)
    if type(manifest["cue_count"]) is not int or manifest["cue_count"] != len(cues):
        raise InvalidInput("SOURCE_CUE_CENSUS_MISMATCH")
    scope = manifest["scope"]
    if type(scope) is not dict or set(scope) != {"mode", "first_cue", "last_cue"}:
        raise InvalidInput("SOURCE_SCOPE_SCHEMA_INVALID")
    first, last = scope["first_cue"], scope["last_cue"]
    if (type(first) is not int or type(last) is not int or
        not 1 <= first <= last <= len(cues) or
        scope["mode"] not in ("FULL_VIDEO", "PARTIAL") or
        (scope["mode"] == "FULL_VIDEO" and (first != 1 or last != len(cues)))):
        raise InvalidInput("SOURCE_SCOPE_RANGE_INVALID")
    windows = manifest["windows"]
    if type(windows) is not list or not windows or len(windows) > len(cues):
        raise InvalidInput("SOURCE_WINDOWS_INVALID")
    next_cue, previous_window_no = first, None
    for window in windows:
        if type(window) is not dict or set(window) != {
            "window_id", "first_cue", "last_cue", "text_sha256"
        }:
            raise InvalidInput("WINDOW_PLAN_SCHEMA_INVALID")
        wid = require_identifier(window["window_id"], WINDOW, "WINDOW_ID")
        number = int(wid[1:])
        begin, finish = window["first_cue"], window["last_cue"]
        if (previous_window_no is not None and number != previous_window_no + 1):
            raise InvalidInput("WINDOW_ID_NONCONTIGUOUS")
        if (type(begin) is not int or type(finish) is not int or
            begin != next_cue or not begin <= finish <= last):
            raise InvalidInput("WINDOW_PRIMARY_OWNER_GAP_OR_OVERLAP")
        expected_text = sha256(" ".join(cues[i-1].text for i in range(begin, finish+1))
                               .encode("utf-8"))
        if require_hash(window["text_sha256"], "WINDOW_TEXT_SHA256") != expected_text:
            raise InvalidInput("WINDOW_SOURCE_TEXT_MISMATCH")
        previous_window_no, next_cue = number, finish+1
    if next_cue != last + 1:
        raise InvalidInput("WINDOW_SCOPE_COVERAGE_INCOMPLETE")
    census = cue_census_digest(cues)
    ownership = tuple((w["window_id"], w["first_cue"], w["last_cue"])
                      for w in windows)
    return VerifiedSource(video_id, source_hash, manifest_hash, census, cues,
                          first, last, ownership)
