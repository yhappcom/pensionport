"""Original media transcript reader and discourse context planner (stdlib only).

A discourse window is NOT an atomic financial claim. Semantic annotators read
overlapping left/right context, then produce source-linked propositions.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import re

TIME = re.compile(r"^(\d{2,}):([0-5]\d):([0-5]\d)[,.](\d{3})$")
VIDEO = re.compile(r"^[A-Za-z0-9_-]{11}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_norm(text: str) -> str:
    return " ".join(text.split())


@dataclass(frozen=True)
class Cue:
    index: int
    start_ms: int
    end_ms: int
    text: str


def _ms(part: str) -> int:
    found = TIME.fullmatch(part.strip())
    require(found is not None, "INVALID_SRT_TIMESTAMP")
    h, m, s, ms = map(int, found.groups())
    return (h * 3600 + m * 60 + s) * 1000 + ms


def parse_srt(raw: bytes, digest: str) -> tuple[Cue, ...]:
    require(isinstance(raw, bytes) and 0 < len(raw) <= 32_000_000,
            "INVALID_OR_OVERSIZE_SRT_BYTES")
    require(isinstance(digest, str) and DIGEST.fullmatch(digest) is not None
            and sha256(raw) == digest, "SOURCE_SHA256_MISMATCH")
    try:
        text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError as exc:
        raise ValueError("SOURCE_UTF8_REQUIRED") from exc
    blocks = re.split(r"\n\s*\n", text.strip())
    cues: list[Cue] = []
    for block in blocks:
        lines = block.strip().splitlines()
        require(len(lines) >= 3 and lines[0].strip().isdigit(),
                "MALFORMED_CUE")
        index = int(lines[0])
        require(index == len(cues) + 1, "CUE_NUMBER_GAP_OR_DUPLICATE")
        timing = lines[1].split("-->")
        require(len(timing) == 2, "CUE_TIMESPAN_MISSING")
        start, end = _ms(timing[0]), _ms(timing[1])
        require(start < end and
                (not cues or start >= cues[-1].start_ms),
                "INVALID_OR_OUT_OF_ORDER_TIME")
        body = text_norm(" ".join(lines[2:]))
        require(bool(body), "CUE_WITHOUT_TEXT")
        cues.append(Cue(index=index,start_ms=start,end_ms=end,text=body))
    require(bool(cues), "NO_CUES")
    return tuple(cues)


def discourse_windows(cues: tuple[Cue, ...], max_cues: int = 10,
                      max_chars: int = 850,
                      pause_ms: int = 1800) -> list[dict]:
    """Partition source cues once; supply adjacent context without reassigning IDs.

    The algorithm does not split a discourse unit into atomic propositions.
    Every cue occurs in exactly one primary window. Left/right halo cues
    provide context for sentence continuations across window boundaries.
    """
    require(cues and 2 <= max_cues <= 40 and 100 <= max_chars <= 5000
            and 0 <= pause_ms <= 10000, "INVALID_CONTEXT_WINDOW_CONFIG")
    groups: list[list[Cue]] = []
    current: list[Cue] = []
    current_length = 0
    for cue in cues:
        gap = max(0, cue.start_ms - current[-1].end_ms) if current else 0
        would_overflow = bool(current) and (
            len(current) >= max_cues or
            current_length + len(cue.text) + 1 > max_chars or
            gap > pause_ms)
        if would_overflow:
            groups.append(current)
            current = []
            current_length = 0
        current.append(cue)
        current_length += len(cue.text) + 1
    if current:
        groups.append(current)
    windows = []
    owned = []
    for pos, group in enumerate(groups):
        ids = [c.index for c in group]
        owned += ids
        previous = groups[pos-1][-2:] if pos else []
        following = groups[pos+1][:2] if pos+1 < len(groups) else []
        windows.append({
            "window_id":f"W{pos+1:05d}",
            "source_cue_ids":ids,
            "start_ms":group[0].start_ms,
            "end_ms":group[-1].end_ms,
            "source_text":" ".join(c.text for c in group),
            "source_text_sha256":sha256(
                " ".join(c.text for c in group).encode("utf-8")),
            "left_context_cue_ids":[c.index for c in previous],
            "left_context_text":" ".join(c.text for c in previous),
            "right_context_cue_ids":[c.index for c in following],
            "right_context_text":" ".join(c.text for c in following),
            "semantic_interpretation":"NOT_PERFORMED",
            "completeness":"CONTEXT_ONLY_NOT_AN_ATOM"
        })
    require(owned == [c.index for c in cues],
            "PRIMARY_DISCOURSE_WINDOW_DROPPED_CUES")
    return windows


def source_record(raw: bytes, video_id: str, digest: str) -> dict:
    require(isinstance(video_id, str) and VIDEO.fullmatch(video_id) is not None,
            "SOURCE_VIDEO_ID_INVALID")
    cues=parse_srt(raw,digest)
    windows=discourse_windows(cues)
    return {
        "schema":"IRE_SOURCE_CONTEXT_V1",
        "video_id":video_id,
        "source_sha256":digest,
        "cue_count":len(cues),
        "windows":windows,
        "all_source_cues_assigned":True,
        "audio_verified":False,
        "claims_extracted":False,
        "interpretation_status":"BLOCKED_NOT_YET_ANNOTATED",
    }
